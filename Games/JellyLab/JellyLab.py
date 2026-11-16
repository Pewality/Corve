# JELLY LAB - a jelly physics simulator for the Thumby (MicroPython)
#
#   D-PAD   move the hand
#   A       hold to grab the jelly and stretch it, let go to fling it
#   A + B   (tap B while holding A) nail that spot down - a PIN.
#           Pin one side, grab the other and stretch it between the nails
#   B       open / close the menu: material, gravity, shape, view,
#           sound, shake, unpin, reset
#
# The jelly is a ring of 16 point masses plus a centre point, joined by
# 56 springs, with an air-pressure term that keeps its volume (it bulges
# when squashed and thins when stretched). All integer fixed-point
# (1/256 px), so almost no garbage and no MemoryError.

import thumby
import gc
from math import sqrt, sin, cos, pi

disp = thumby.display
disp.setFPS(30)
_fr = disp.drawFilledRectangle
_ln = disp.drawLine
_tx = disp.drawText
_px = disp.setPixel

N = 16            # ring points
C = 16            # centre point
NN = 17
WX0 = 512         # world box in 1/256 px (2..69 x 2..37)
WX1 = 17664
WY0 = 512
WY1 = 9472
MAXV = 1100

MATS = (("SLIME", 5, 44, 3, 1), ("JELLO", 11, 14, 2, 2),
        ("WOBBLY", 8, 5, 2, 3), ("RUBBER", 20, 34, 1, 2),
        ("BOUNCY", 17, 4, 1, 4))      # name, stiff, damp, bounce, friction
GRAVS = (("EARTH", 36), ("MOON", 9), ("ZERO", 0), ("FLIP", -36))
SHAPES = ("BLOB", "SQUARE", "STAR", "HEART", "NOODLE")
VIEWS = ("SOLID", "XRAY", "GHOST")
GLOSS = ((9, 10, 11), (9, 10, 11), None, (13, 14, 15), None)

# ------------------------------------------------------------------ state
RX = [0] * NN
RY = [0] * NN
SP = []
px = [0] * NN
py = [0] * NN
vx = [0] * NN
vy = [0] * NN
gm = bytearray(NN)        # 0 free, 1 held by the hand, 2 pinned
ox = [0] * NN             # offset from hand while held
oy = [0] * NN
pnx = [0] * NN            # pin targets
pny = [0] * NN
xs = [0] * 168            # scanline crossings (4 per row)
cn = bytearray(42)
SX = [0] * NN
SY = [0] * NN

KM = 16
CM = 14
BS = 2
FS = 2
GV = 36
mat = 1
grv = 0
shp = 0
vw = 0
snd_on = True
A0 = 1
RD = 1
AR = 1
CX = CY = 0
BX0 = BX1 = BY0 = BY1 = 0
IMP = IMX = IMY = 0
gany = False
grab = False
seed = 1234


def rnd():
    global seed
    seed = (seed * 75 + 74) % 65537
    return seed


# ------------------------------------------------------------------ helpers
def snd(f, d):
    if snd_on:
        try:
            thumby.audio.play(f, d)
        except Exception:
            pass


def fr(x, y, w, h, c):
    if x < 0:
        w += x
        x = 0
    if x + w > 72:
        w = 72 - x
    if y < 0:
        h += y
        y = 0
    if y + h > 40:
        h = 40 - y
    if w > 0 and h > 0:
        _fr(x, y, w, h, c)


def dot(x, y, c):
    if 0 <= x < 72 and 0 <= y < 40:
        _px(x, y, c)


def tx(s, x, y, c=1):
    if x < 0:
        x = (73 - len(s) * 6) // 2
    _tx(s, x, y, c)


def stats():
    global AR, CX, CY, BX0, BX1, BY0, BY1
    sx = sy = ar = 0
    x0 = y0 = 1 << 29
    x1 = y1 = -(1 << 29)
    xp = px[N - 1] >> 4
    yp = py[N - 1] >> 4
    for i in range(N):
        x = px[i]
        y = py[i]
        sx += x
        sy += y
        xc = x >> 4
        yc = y >> 4
        ar += xp * yc - xc * yp
        xp = xc
        yp = yc
        if x < x0:
            x0 = x
        if x > x1:
            x1 = x
        if y < y0:
            y0 = y
        if y > y1:
            y1 = y
    AR = ar
    CX = sx // N
    CY = sy // N
    BX0 = x0
    BX1 = x1
    BY0 = y0
    BY1 = y1


# ------------------------------------------------------------------ shapes
def spring(a, b, k, c):
    dx = RX[b] - RX[a]
    dy = RY[b] - RY[a]
    SP.append((a, b, int(sqrt(dx * dx + dy * dy)), k, c))


def set_shape(s):
    global shp, A0, RD
    shp = s
    sx = sy = 0
    for i in range(N):
        a = 2 * pi * i / N
        ca = cos(a)
        sa = sin(a)
        if s == 0:
            x = ca * 2560
            y = sa * 2560
        elif s == 1:
            q = sqrt(sqrt(ca * ca * ca * ca + sa * sa * sa * sa))
            x = ca * 2200 / q
            y = sa * 2200 / q
        elif s == 2:
            r = (0.9 + 0.45 * cos(4 * a)) * 2300
            x = ca * r
            y = sa * r
        elif s == 3:
            x = 16 * sa * sa * sa * 158
            y = -(13 * ca - 5 * cos(2 * a) - 2 * cos(3 * a)
                  - cos(4 * a)) * 158
        else:
            x = ca * 4200
            y = sa * 820
        RX[i] = int(x)
        RY[i] = int(y)
        sx += RX[i]
        sy += RY[i]
    sx //= N
    sy //= N
    for i in range(N):
        RX[i] -= sx
        RY[i] -= sy
    RX[C] = 0
    RY[C] = 0
    del SP[:]
    for i in range(N):
        spring(i, (i + 1) % N, 16, 4)      # skin
        spring(i, (i + 2) % N, 12, 3)      # bending
        spring(i, C, 6, 1)                 # spokes
    for i in range(8):
        spring(i, i + 8, 8, 2)             # cross braces
    ar = 0
    x0 = y0 = 1 << 29
    x1 = y1 = -(1 << 29)
    xp = RX[N - 1] >> 4
    yp = RY[N - 1] >> 4
    for i in range(N):
        xc = RX[i] >> 4
        yc = RY[i] >> 4
        ar += xp * yc - xc * yp
        xp = xc
        yp = yc
        if RX[i] < x0:
            x0 = RX[i]
        if RX[i] > x1:
            x1 = RX[i]
        if RY[i] < y0:
            y0 = RY[i]
        if RY[i] > y1:
            y1 = RY[i]
    A0 = ar
    RD = max(x1 - x0, y1 - y0)
    gc.collect()


def apply_mat():
    global KM, CM, BS, FS
    m = MATS[mat]
    KM = m[1]
    CM = m[2]
    BS = m[3]
    FS = m[4]


def spawn(x, y):
    for i in range(NN):
        px[i] = (x << 8) + RX[i]
        py[i] = (y << 8) + RY[i]
        vx[i] = 0
        vy[i] = 0
        gm[i] = 0
    stats()


def reshape():
    # folded inside-out: snap back to a clean blob, keep the average speed
    mx = my = 0
    for i in range(N):
        mx += vx[i]
        my += vy[i]
    mx //= N
    my //= N
    for i in range(NN):
        px[i] = CX + RX[i]
        py[i] = CY + RY[i]
        vx[i] = mx
        vy[i] = my
    stats()


# ------------------------------------------------------------------ physics
def physics(cux, cuy):
    global IMP, IMX, IMY
    pxl = px
    pyl = py
    vxl = vx
    vyl = vy
    km = KM
    cm = CM
    g = GV

    if gany:
        for i in range(NN):
            m = gm[i]
            if m:
                if m == 1:
                    tx_ = cux + ox[i]
                    ty_ = cuy + oy[i]
                    k = 150
                else:
                    tx_ = pnx[i]
                    ty_ = pny[i]
                    k = 200
                vxl[i] += (((tx_ - pxl[i]) * k) >> 8) - (vxl[i] >> 1)
                vyl[i] += (((ty_ - pyl[i]) * k) >> 8) - (vyl[i] >> 1)

    for i in range(NN):
        vyl[i] += g

    for a, b, r0, k, c in SP:
        dx = pxl[b] - pxl[a]
        dy = pyl[b] - pyl[a]
        l = int(sqrt(dx * dx + dy * dy))
        if l < 1:
            l = 1
        rv = ((vxl[b] - vxl[a]) * dx + (vyl[b] - vyl[a]) * dy) // l
        f = ((l - r0) * k * km + rv * c * cm) >> 10
        fx = f * dx // l
        fy = f * dy // l
        vxl[a] += fx
        vyl[a] += fy
        vxl[b] -= fx
        vyl[b] -= fy

    # pressure: keeps the volume, so it bulges when squashed
    ar = AR
    if ar < (A0 >> 3):
        ar = A0 >> 3
    p = ((A0 - ar) << 8) // ar
    if p > 512:
        p = 512
    elif p < -256:
        p = -256
    if p:
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            ex = pxl[j] - pxl[i]
            ey = pyl[j] - pyl[i]
            fx = (ey * p) >> 11
            fy = -((ex * p) >> 11)
            vxl[i] += fx
            vyl[i] += fy
            vxl[j] += fx
            vyl[j] += fy

    bs = BS
    fs = FS
    ib = 0
    ix = iy = 0
    for i in range(NN):
        a = vxl[i]
        b = vyl[i]
        a -= a >> 6
        b -= b >> 6
        if a > MAXV:
            a = MAXV
        elif a < -MAXV:
            a = -MAXV
        if b > MAXV:
            b = MAXV
        elif b < -MAXV:
            b = -MAXV
        x = pxl[i] + a
        y = pyl[i] + b
        if x < WX0:
            x = WX0
            if a < -96:
                if -a > ib:
                    ib = -a
                    ix = x
                    iy = y
                a = -(a >> bs)
            else:
                a = 0
            b -= b >> fs
        elif x > WX1:
            x = WX1
            if a > 96:
                if a > ib:
                    ib = a
                    ix = x
                    iy = y
                a = -(a >> bs)
            else:
                a = 0
            b -= b >> fs
        if y < WY0:
            y = WY0
            if b < -96:
                if -b > ib:
                    ib = -b
                    ix = x
                    iy = y
                b = -(b >> bs)
            else:
                b = 0
            a -= a >> fs
        elif y > WY1:
            y = WY1
            if b > 96:
                if b > ib:
                    ib = b
                    ix = x
                    iy = y
                b = -(b >> bs)
            else:
                b = 0
            a -= a >> fs
        pxl[i] = x
        pyl[i] = y
        vxl[i] = a
        vyl[i] = b
    IMP = ib
    IMX = ix
    IMY = iy
    stats()
    if AR < (A0 >> 5):
        reshape()


def shake():
    for i in range(NN):
        vx[i] += rnd() % 1600 - 800
        vy[i] += rnd() % 1000 - 1100


# ------------------------------------------------------------------ scenery
bg = bytearray(360)       # static background, blitted once per frame


def bpx(x, y):
    bg[x + (y >> 3) * 72] |= 1 << (y & 7)


for _i in range(0, 72, 2):
    bpx(_i, 0)
for _i in range(0, 38, 2):
    bpx(0, _i)
    bpx(71, _i)
for _i in range(72):
    bpx(_i, 38)
    if _i & 1:
        bpx(_i, 39)
for _i in range(16):
    bpx(3 + rnd() % 66, 3 + rnd() % 32)

PN = 12
PX = [0] * PN
PY = [0] * PN
PVX = [0] * PN
PVY = [0] * PN
PL = [0] * PN


def splat(x, y):
    n = 0
    for i in range(PN):
        if PL[i] == 0:
            PX[i] = x
            PY[i] = y
            PVX[i] = rnd() % 900 - 450 + ((x - CX) >> 3)
            PVY[i] = rnd() % 700 - 350 + ((y - CY) >> 3)
            PL[i] = 9 + rnd() % 8
            n += 1
            if n >= 7:
                break


def parts():
    for i in range(PN):
        if PL[i]:
            PL[i] -= 1
            PVY[i] += 26
            PX[i] += PVX[i]
            PY[i] += PVY[i]
            dot(PX[i] >> 8, PY[i] >> 8, 1)


# ------------------------------------------------------------------ drawing
def draw_jelly(tn):
    for i in range(NN):
        SX[i] = px[i] >> 8
        SY[i] = py[i] >> 8
    if vw == 0:
        lo = BY0 >> 8
        hi = (BY1 >> 8) + 1
        if lo < 0:
            lo = 0
        if hi > 40:
            hi = 40
        for y in range(lo, hi + 1):
            cn[y] = 0
        for i in range(N):
            j = i + 1
            if j == N:
                j = 0
            x0 = SX[i]
            y0 = SY[i]
            x1 = SX[j]
            y1 = SY[j]
            if y0 == y1:
                continue
            if y0 > y1:
                x0, x1 = x1, x0
                y0, y1 = y1, y0
            dx = x1 - x0
            dy = y1 - y0
            ya = y0 if y0 > 0 else 0
            yb = y1 if y1 < 40 else 40
            for y in range(ya, yb):
                c = cn[y]
                if c < 4:
                    xs[y * 4 + c] = x0 + ((y - y0) * dx) // dy
                    cn[y] = c + 1
        for y in range(lo, hi):
            c = cn[y]
            if c < 2:
                continue
            if tn == 2 and (y & 1):
                continue
            if tn == 1 and (y & 3) == 3:
                continue
            b = y * 4
            a0 = xs[b]
            a1 = xs[b + 1]
            if c >= 4:
                a2 = xs[b + 2]
                a3 = xs[b + 3]
                if a0 > a1:
                    a0, a1 = a1, a0
                if a2 > a3:
                    a2, a3 = a3, a2
                if a0 > a2:
                    a0, a2 = a2, a0
                if a1 > a3:
                    a1, a3 = a3, a1
                if a1 > a2:
                    a1, a2 = a2, a1
                fr(a0, y, a1 - a0 + 1, 1, 1)
                fr(a2, y, a3 - a2 + 1, 1, 1)
            else:
                if a0 > a1:
                    a0, a1 = a1, a0
                fr(a0, y, a1 - a0 + 1, 1, 1)
    for i in range(N):
        j = i + 1
        if j == N:
            j = 0
        _ln(SX[i], SY[i], SX[j], SY[j], 1)
    if vw == 1:
        mx = SX[C]
        my = SY[C]
        for i in range(0, N, 2):
            _ln(SX[i], SY[i], mx, my, 1)
        for i in range(8):
            _ln(SX[i], SY[i], SX[i + 8], SY[i + 8], 1)
        for i in range(NN):
            fr(SX[i] - 1, SY[i] - 1, 2, 2, 1)
    elif vw == 0 and tn < 2:
        gl = GLOSS[shp]
        if gl:
            mx = SX[C]
            my = SY[C]
            i = gl[0]
            x0 = SX[i] + ((mx - SX[i]) * 3 >> 4)
            y0 = SY[i] + ((my - SY[i]) * 3 >> 4)
            for i in gl[1:]:
                x1 = SX[i] + ((mx - SX[i]) * 3 >> 4)
                y1 = SY[i] + ((my - SY[i]) * 3 >> 4)
                _ln(x0, y0, x1, y1, 0)
                x0 = x1
                y0 = y1


def face(cux, cuy, tn, hurt, blink):
    fc = 0 if vw == 0 else 1
    x = SX[C]
    y = SY[C]
    w = (BX1 - BX0) >> 8
    h = (BY1 - BY0) >> 8
    gap = w // 6
    if gap < 2:
        gap = 2
    elif gap > 5:
        gap = 5
    eh = 3 if h >= 12 else (2 if h >= 7 else 1)
    lx = ly = 0
    if cux > x + 6:
        lx = 1
    elif cux < x - 6:
        lx = -1
    if cuy > y + 6:
        ly = 1
    elif cuy < y - 6:
        ly = -1
    ey = y - (h >> 3) - 1
    if hurt:
        fr(x - gap - 2, ey + 1, 3, 1, fc)
        fr(x + gap, ey + 1, 3, 1, fc)
    elif blink:
        fr(x - gap - 1, ey + 1, 2, 1, fc)
        fr(x + gap, ey + 1, 2, 1, fc)
    else:
        if tn:
            eh += 1
        fr(x - gap - 1 + lx, ey + ly, 2, eh, fc)
        fr(x + gap + lx, ey + ly, 2, eh, fc)
    if h >= 9:
        my = y + (h >> 3) + 2
        if hurt:
            fr(x - 2, my + 1, 5, 1, fc)
        elif tn:
            fr(x - 1, my - 1, 3, 3, fc)
        else:
            dot(x - 2, my, fc)
            fr(x - 1, my + 1, 3, 1, fc)
            dot(x + 2, my, fc)


def cursor(cx, cy, held):
    if held:
        fr(cx - 2, cy - 2, 5, 5, 0)
        fr(cx - 1, cy - 1, 3, 3, 1)
    else:
        fr(cx - 2, cy - 1, 5, 3, 0)
        fr(cx - 1, cy - 2, 3, 5, 0)
        fr(cx - 1, cy, 3, 1, 1)
        fr(cx, cy - 1, 1, 3, 1)


# ------------------------------------------------------------------ hand
def do_grab(cx, cy):
    global grab, gany
    cux = cx << 8
    cuy = cy << 8
    n = 0
    best = 1 << 29
    bi = -1
    for i in range(NN):
        ddx = (px[i] - cux) >> 4
        ddy = (py[i] - cuy) >> 4
        d2 = ddx * ddx + ddy * ddy
        if d2 < 5184:
            gm[i] = 1
            ox[i] = px[i] - cux
            oy[i] = py[i] - cuy
            n += 1
        elif d2 < best:
            best = d2
            bi = i
    if n == 0 and bi >= 0 and best < 36864:
        gm[bi] = 1
        ox[bi] = px[bi] - cux
        oy[bi] = py[bi] - cuy
        n = 1
    grab = n > 0
    if grab:
        gany = True
        snd(700, 30)


def pin_held():
    global grab
    for i in range(NN):
        if gm[i] == 1:
            gm[i] = 2
            pnx[i] = px[i]
            pny[i] = py[i]
    grab = False
    snd(1000, 40)


def drop_held():
    global grab, gany
    gany = False
    for i in range(NN):
        if gm[i] == 1:
            gm[i] = 0
        elif gm[i]:
            gany = True
    grab = False


def unpin():
    global gany
    for i in range(NN):
        gm[i] = 0
    gany = False


# ------------------------------------------------------------------ menu
ITEMS = ("MATERIAL", "GRAVITY", "SHAPE", "VIEW", "SOUND", "SHAKE", "UNPIN",
         "RESET")


def value(i):
    if i == 0:
        return MATS[mat][0]
    if i == 1:
        return GRAVS[grv][0]
    if i == 2:
        return SHAPES[shp]
    if i == 3:
        return VIEWS[vw]
    if i == 4:
        return "ON" if snd_on else "OFF"
    return None


def change(i, ch):
    global mat, grv, GV, vw, snd_on
    if i == 0:
        mat = (mat + ch) % len(MATS)
        apply_mat()
    elif i == 1:
        grv = (grv + ch) % len(GRAVS)
        GV = GRAVS[grv][1]
    elif i == 2:
        unpin()
        set_shape((shp + ch) % len(SHAPES))
        spawn(36, 15)
    elif i == 3:
        vw = (vw + ch) % len(VIEWS)
    else:
        snd_on = not snd_on


def act(i):
    if i == 5:
        shake()
        snd(180, 100)
    elif i == 6:
        unpin()
    else:
        unpin()
        spawn(36, 15)


def draw_menu():
    fr(0, 0, 72, 18, 0)
    fr(0, 18, 72, 1, 1)
    tx(ITEMS[mi] + " " + str(mi + 1) + "/8", 0, 1)
    v = value(mi)
    if v is None:
        tx("A:GO", -1, 10)
    else:
        tx("<" + v + ">", -1, 10)


# ------------------------------------------------------------------ main
apply_mat()
GV = GRAVS[grv][1]
set_shape(0)
spawn(36, 12)

cx = 50
cy = 20
hold = 0
mo = False
mi = 0
frame = 0
hurt = 0
pa = pb = pu = pd = pl = pr = False
gc.collect()

while True:
    l = thumby.buttonL.pressed()
    r = thumby.buttonR.pressed()
    u = thumby.buttonU.pressed()
    d = thumby.buttonD.pressed()
    a = thumby.buttonA.pressed()
    b = thumby.buttonB.pressed()
    ea = a and not pa
    eb = b and not pb
    eu = u and not pu
    ed = d and not pd
    el = l and not pl
    er = r and not pr
    pa = a
    pb = b
    pu = u
    pd = d
    pl = l
    pr = r
    frame += 1

    if mo:
        if eb:
            mo = False
        else:
            if eu:
                mi = (mi - 1) % 8
                snd(900, 15)
            if ed:
                mi = (mi + 1) % 8
                snd(900, 15)
            ch = (1 if er else 0) - (1 if el else 0)
            if ea and mi < 5:
                ch = 1
            if ch and mi < 5:
                change(mi, ch)
                snd(1200, 20)
            if ea and mi >= 5:
                act(mi)
    else:
        dxm = (1 if r else 0) - (1 if l else 0)
        dym = (1 if d else 0) - (1 if u else 0)
        if dxm or dym:
            hold += 1
            sp = 1 if hold < 8 else (2 if hold < 16 else 3)
            cx += dxm * sp
            cy += dym * sp
            if cx < 1:
                cx = 1
            elif cx > 70:
                cx = 70
            if cy < 1:
                cy = 1
            elif cy > 37:
                cy = 37
        else:
            hold = 0
        if eb:
            if grab:
                pin_held()
            else:
                mo = True
        elif ea:
            do_grab(cx, cy)
        if grab and not a:
            if (max(BX1 - BX0, BY1 - BY0) * 100) // RD > 150:
                snd(260, 90)
            drop_held()

    physics(cx << 8, cy << 8)
    st = (max(BX1 - BX0, BY1 - BY0) * 100) // RD
    tn = 2 if st > 210 else (1 if st > 150 else 0)
    if IMP > 300:
        hurt = 7
        splat(IMX, IMY)
        snd(110 + (IMP >> 2), 40)
    elif hurt:
        hurt -= 1

    disp.fill(0)
    disp.blit(bg, 0, 0, 72, 40, -1, 0, 0)
    draw_jelly(tn)
    face(cx, cy, tn, hurt, (frame % 96) < 4)
    for i in range(NN):
        if gm[i] == 2:
            fr(SX[i] - 1, SY[i] - 1, 3, 3, 0)
            dot(SX[i], SY[i], 1)
    parts()
    if grab and st > 110:
        n = (st - 100) // 5
        fr(4, 2, 4 if n < 4 else (n if n < 62 else 62), 2, 1)
    if mo:
        draw_menu()
    else:
        cursor(cx, cy, grab)
        if frame < 160:
            fr(0, 0, 72, 18, 0)
        if frame < 80:
            tx("JELLY LAB", -1, 1)
            tx("A:GRAB B:OPT", 0, 9)
        elif frame < 160:
            tx("HOLD A,TAP B", 0, 1)
            tx("= PIN SPOT", -1, 9)
    disp.update()
