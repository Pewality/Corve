# PINBALL for the Thumby (MicroPython) - Pin Blast table + physics
# Put in /Games/Pinball/Pinball.py  -  hold the Thumby SIDEWAYS (screen is drawn rotated 90 deg)
import thumby
import math
import random
import gc

sqrt = math.sqrt
cos = math.cos
sin = math.sin

ROT = 1      # 0 = turn Thumby clockwise (D-pad on top), 1 = counter-clockwise (D-pad at bottom)
SND = 1
BALLS = 3            # always exactly three tries
FPS = 30
DEFHS = (("ACE", 3000), ("BOB", 2000), ("CAT", 1200), ("DOT", 800), ("EVE", 400))
SCORES = [[e[0], e[1]] for e in DEFHS]

# ---- Pin Blast table (portrait coords u across, v down) ----
HT = 72.0
GRAV = 0.105
VMAX = 4.4
R = 1.5
OX = 3
# walls: (u1, v1, u2, v2, bounce, kick, one-way gate)
WALLS = (
    (0.5, 52, 0.5, 18, 0.35, 0, 0), (0.5, 18, 3, 10, 0.35, 0, 0), (3, 10, 9, 5, 0.35, 0, 0),
    (9, 5, 15, 2.5, 0.35, 0, 0), (15, 2.5, 21, 3.5, 0.35, 0, 0), (21, 3.5, 26, 6, 0.35, 0, 0),
    (26, 6, 30, 10, 0.35, 0, 0), (30, 10, 34, 17, 0.35, 0, 0), (34, 17, 34, 70, 0.3, 0, 0),
    (29.5, 22, 29.5, 68, 0.3, 0, 0), (29.5, 68, 34, 68, 0.1, 0, 0),
    (0.5, 52, 5.5, 60, 0.3, 0, 0), (29.5, 50, 24.5, 60, 0.3, 0, 0),
    (4.5, 43, 9, 52, 0.5, 2.6, 0), (25.5, 43, 21, 52, 0.5, 2.6, 0),
    (34, 18.5, 29.5, 22, 0.3, 0, 1),
)
LAYOUTS = (
    ((10, 27, 3.0), (20, 27, 3.0), (15, 36, 3.0), (15, 18, 2.5)),
    ((8, 22, 3.0), (22, 22, 3.0), (15, 29, 3.5), (10, 38, 2.5), (20, 38, 2.5)),
    ((15, 21, 4.0), (7, 32, 2.5), (23, 32, 2.5), (15, 40, 2.5), (9, 15, 2.0), (21, 15, 2.0)),
)
TARGETS = ((8, 12), (15, 9.5), (22, 12))
FL = 7.0
PIV = ((6.0, 60.0), (24.0, 60.0))
REST = (0.49, 3.1416 - 0.49)
ACT = (-0.45, 3.1416 + 0.45)
LANE = 31.75

# ---- screen buffers (72x40, drawn rotated) ----
SBUF = bytearray(360)
FB = bytearray(360)
ZERO = bytes(360)
DST = FB

def pset(x, y):
    if x < 0 or x > 39 or y < 0 or y > 71:
        return
    if ROT:
        dx = 71 - y
        dy = x
    else:
        dx = y
        dy = 39 - x
    DST[dx + (dy >> 3) * 72] |= 1 << (dy & 7)

def pclr(x, y):
    if x < 0 or x > 39 or y < 0 or y > 71:
        return
    if ROT:
        dx = 71 - y
        dy = x
    else:
        dx = y
        dy = 39 - x
    DST[dx + (dy >> 3) * 72] &= 255 ^ (1 << (dy & 7))

def line(x0, y0, x1, y1):
    x0 = int(x0 + 0.5)
    y0 = int(y0 + 0.5)
    x1 = int(x1 + 0.5)
    y1 = int(y1 + 0.5)
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    e = dx + dy
    while True:
        pset(x0, y0)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x0 += sx
        if e2 <= dx:
            e += dx
            y0 += sy

FONT = {
    ' ': (0, 0, 0, 0, 0), '0': (7, 5, 5, 5, 7), '1': (2, 6, 2, 2, 7), '2': (7, 1, 7, 4, 7),
    '3': (7, 1, 7, 1, 7), '4': (5, 5, 7, 1, 1), '5': (7, 4, 7, 1, 7), '6': (7, 4, 7, 5, 7),
    '7': (7, 1, 1, 1, 1), '8': (7, 5, 7, 5, 7), '9': (7, 5, 7, 1, 7), 'A': (2, 5, 7, 5, 5),
    'B': (6, 5, 6, 5, 6), 'C': (7, 4, 4, 4, 7), 'D': (6, 5, 5, 5, 6), 'E': (7, 4, 6, 4, 7),
    'F': (7, 4, 6, 4, 4), 'G': (7, 4, 5, 5, 7), 'H': (5, 5, 7, 5, 5), 'I': (7, 2, 2, 2, 7),
    'J': (1, 1, 1, 5, 7), 'K': (5, 5, 6, 5, 5), 'L': (4, 4, 4, 4, 7), 'M': (5, 7, 7, 5, 5),
    'N': (6, 5, 5, 5, 5), 'O': (2, 5, 5, 5, 2), 'P': (7, 5, 7, 4, 4), 'Q': (7, 5, 5, 7, 1),
    'R': (6, 5, 6, 5, 5), 'S': (3, 4, 2, 1, 6), 'T': (7, 2, 2, 2, 2), 'U': (5, 5, 5, 5, 7),
    'V': (5, 5, 5, 5, 2), 'W': (5, 5, 7, 7, 5), 'X': (5, 5, 2, 5, 5), 'Y': (5, 5, 2, 2, 2),
    'Z': (7, 1, 2, 4, 7), '!': (2, 2, 2, 0, 2), '-': (0, 0, 7, 0, 0), ':': (0, 2, 0, 2, 0),
    '.': (0, 0, 0, 0, 2), '/': (1, 1, 2, 4, 4), '>': (4, 2, 1, 2, 4), '+': (0, 2, 7, 2, 0),
}

def text(s, x, y, sc=1):
    for ch in s:
        g = FONT.get(ch)
        if g:
            for r in range(5):
                row = g[r]
                for c in range(3):
                    if row & (4 >> c):
                        if sc == 1:
                            pset(x + c, y + r)
                        else:
                            for i in range(sc):
                                for j in range(sc):
                                    pset(x + c * sc + i, y + r * sc + j)
        x += 4 * sc

def tw(s, sc=1):
    return 4 * sc * len(s) - sc

def ctext(s, y, sc=1, cx=20):
    text(s, cx - tw(s, sc) // 2, y, sc)

def clear():
    try:
        FB[:] = ZERO
    except Exception:
        for i in range(360):
            FB[i] = 0

def copy_static():
    try:
        FB[:] = SBUF
    except Exception:
        for i in range(360):
            FB[i] = SBUF[i]

def present():
    thumby.display.blit(FB, 0, 0, 72, 40, -1, 0, 0)
    thumby.display.update()

def banner(s, y=34, cx=20):
    w = tw(s)
    x = cx - w // 2
    for i in range(x - 3, x + w + 3):
        for j in range(y - 3, y + 8):
            pclr(i, j)
    for i in range(x - 3, x + w + 3):
        pset(i, y - 3)
        pset(i, y + 7)
    for j in range(y - 3, y + 8):
        pset(x - 3, j)
        pset(x + w + 2, j)
    text(s, x, y)

# ---- input (user-oriented, whatever the rotation) ----
UL = 0
UR = 1
UU = 2
UD = 3
KA = 4
KB = 5
cur = [False] * 6
prv = [False] * 6

def poll():
    global cur, prv
    t = cur
    cur = prv
    prv = t
    if ROT:
        cur[0] = thumby.buttonU.pressed()
        cur[1] = thumby.buttonD.pressed()
        cur[2] = thumby.buttonR.pressed()
        cur[3] = thumby.buttonL.pressed()
    else:
        cur[0] = thumby.buttonD.pressed()
        cur[1] = thumby.buttonU.pressed()
        cur[2] = thumby.buttonL.pressed()
        cur[3] = thumby.buttonR.pressed()
    cur[4] = thumby.buttonA.pressed()
    cur[5] = thumby.buttonB.pressed()

def hit(i):
    return cur[i] and not prv[i]

def wait_release():
    for _ in range(60):
        poll()
        if not (cur[0] or cur[1] or cur[2] or cur[3] or cur[4] or cur[5]):
            break
        present()
    poll()
    poll()

def snd(f, d=40):
    if SND:
        try:
            thumby.audio.play(int(f), int(d))
        except Exception:
            pass

def rnd(a, b):
    return a + (b - a) * random.random()

# jingles: queue of (freq, frames) played one note at a time
JQ = []
jt = 0
MBJ = ((523, 2), (659, 2), (784, 2), (1047, 2), (784, 2), (1047, 2), (1319, 5))
WINJ = ((880, 2), (1175, 2), (1568, 4))
OVJ = ((400, 3), (300, 3), (200, 3), (120, 8))
MENUJ = ((330, 3), (392, 3), (523, 3), (494, 3), (392, 3), (330, 3), (440, 3), (523, 3), (659, 3), (587, 3), (523, 3), (440, 3), (392, 6))

def jingle(n):
    global jt
    del JQ[:]
    JQ.extend(n)
    jt = 0

def jtick():
    global jt
    if jt > 0:
        jt -= 1
    elif JQ:
        n = JQ.pop(0)
        snd(n[0], n[1] * 33)
        jt = n[1]

# ---- save data ----
def load_data():
    global ROT, SND, SCORES
    try:
        sd = thumby.saveData
        sd.setName("Pinball")
        if sd.hasItem("rot2"):
            ROT = int(sd.getItem("rot2"))
        if sd.hasItem("snd"):
            SND = int(sd.getItem("snd"))
        if sd.hasItem("hs2"):
            h = []
            for e in sd.getItem("hs2"):
                h.append([str(e[0])[:3], int(e[1])])
            if h:
                SCORES = h[:5]
    except Exception:
        pass

def save_data():
    try:
        sd = thumby.saveData
        sd.setItem("rot2", ROT)
        sd.setItem("snd", SND)
        sd.setItem("hs2", SCORES)
        sd.save()
    except Exception:
        pass

# ---- game state ----
balls = []          # each ball: [u, v, vu, vv, stuck]
tg = [True, True, True]
fa = [REST[0], REST[1]]
fh = [0, 0]
fcool = [0, 0]
flash = [0] * 6
bcool = [0] * 6
score = 0
balls_left = 3
ball_no = 1
mult = 1
layout = 0
mode = 0
charge = 0.0
idle_t = 0
bump_hits = 0
save_t = 0
saved = False
nudges = 0
nudge_t = 0
tilt = False
msg = ""
msg_t = 0

def set_msg(s):
    global msg, msg_t
    msg = s
    msg_t = 15          # half a second

# ---- static layer (walls + bumper rings) ----
def build_static():
    global DST
    DST = SBUF
    for i in range(360):
        SBUF[i] = 0
    for w in WALLS:
        line(w[0] + OX, w[1], w[2] + OX, w[3])
        if w[5]:
            o = 1 if w[0] < 15 else -1
            line(w[0] + OX + o, w[1], w[2] + OX + o, w[3])
    for bu in LAYOUTS[layout]:
        r = bu[2]
        n = int(r * 7.5) + 4
        for a in range(n):
            pset(int(bu[0] + OX + cos(a * 6.2832 / n) * r + 0.5), int(bu[1] + sin(a * 6.2832 / n) * r + 0.5))
        pset(int(bu[0] + OX), int(bu[1]))
    DST = FB

# ---- Pin Blast physics ----
def serve():
    global mode, charge, tilt, nudges
    del balls[:]
    balls.append([LANE, 66.2, 0.0, 0.0, 0])
    mode = 0
    charge = 0.0
    tilt = False
    nudges = 0

def new_game():
    global score, balls_left, ball_no, mult, layout, idle_t, bump_hits, save_t, saved
    global nudges, nudge_t, msg_t
    score = 0
    balls_left = BALLS
    ball_no = 1
    mult = 1
    layout = 0
    idle_t = 0
    bump_hits = 0
    save_t = 0
    saved = False
    nudges = 0
    nudge_t = 0
    msg_t = 0
    for k in range(3):
        tg[k] = True
    for k in range(6):
        flash[k] = 0
        bcool[k] = 0
    for i in (0, 1):
        fa[i] = REST[i]
        fh[i] = 0
        fcool[i] = 0
    del JQ[:]
    build_static()
    serve()
    set_msg("BALL 1")

def add_score(n):
    global score
    score += n * mult
    if score > 999999:
        score = 999999

def hit_seg(b, ax, ay, bx, by, rad, e, kick):
    abx = bx - ax
    aby = by - ay
    t = ((b[0] - ax) * abx + (b[1] - ay) * aby) / (abx * abx + aby * aby)
    if t < 0:
        t = 0.0
    elif t > 1:
        t = 1.0
    cx = ax + abx * t
    cy = ay + aby * t
    dx = b[0] - cx
    dy = b[1] - cy
    d2 = dx * dx + dy * dy
    if d2 >= rad * rad:
        return 0.0
    d = sqrt(d2)
    if d < 1e-4:
        l = sqrt(abx * abx + aby * aby)
        nx = -aby / l
        ny = abx / l
    else:
        nx = dx / d
        ny = dy / d
    b[0] = cx + nx * rad
    b[1] = cy + ny * rad
    vn = b[2] * nx + b[3] * ny
    if vn < 0:
        b[2] -= (1 + e) * vn * nx
        b[3] -= (1 + e) * vn * ny
        if kick and -vn > 0.5:
            b[2] += nx * kick
            b[3] += ny * kick
        return -vn
    return 0.01

def hit_flip(b, i, ang, om):
    px, py = PIV[i]
    ex = px + cos(ang) * FL
    ey = py + sin(ang) * FL
    abx = ex - px
    aby = ey - py
    t = ((b[0] - px) * abx + (b[1] - py) * aby) / (FL * FL)
    if t < 0:
        t = 0.0
    elif t > 1:
        t = 1.0
    cx = px + abx * t
    cy = py + aby * t
    dx = b[0] - cx
    dy = b[1] - cy
    rad = R + 1.1
    d2 = dx * dx + dy * dy
    if d2 >= rad * rad:
        return 0.0
    d = sqrt(d2)
    if d < 1e-4:
        nx = -aby / FL
        ny = abx / FL
        if ny > 0:
            nx = -nx
            ny = -ny
    else:
        nx = dx / d
        ny = dy / d
        if abs(nx) < 0.08 and ny < 0:
            nx += 0.1 if i == 0 else -0.1
            l2 = sqrt(nx * nx + ny * ny)
            nx /= l2
            ny /= l2
    b[0] = cx + nx * rad
    b[1] = cy + ny * rad
    vfu = -om * (cy - py)
    vfv = om * (cx - px)
    vn = (b[2] - vfu) * nx + (b[3] - vfv) * ny
    if vn < 0:
        b[2] -= (1 + 0.4) * vn * nx
        b[3] -= (1 + 0.4) * vn * ny
        return -vn
    return 0.01

def physics(left, right):
    global bump_hits, mult, layout, idle_t
    idle_t += 1
    gx = GRAV + min(0.12, max(0, idle_t - 600) * 0.0004)
    old0 = fa[0]
    old1 = fa[1]
    pr = (left, right)
    for i in range(2):
        if fcool[i] > 0:
            fcool[i] -= 1
        if pr[i]:
            if fh[i] == 0 and fcool[i] > 0:
                continue
            fh[i] += 1
        else:
            if fh[i] > 0:
                fcool[i] = 7
            fh[i] = 0
    want0 = ACT[0] if left and not tilt and fh[0] < 100 else REST[0]
    want1 = ACT[1] if right and not tilt and fh[1] < 100 else REST[1]
    wants = (want0, want1)
    for i in range(2):
        d = wants[i] - fa[i]
        sp = 0.32 if abs(wants[i] - ACT[i]) < 0.01 else 0.2
        if abs(d) <= sp:
            fa[i] = wants[i]
        else:
            fa[i] += sp if d > 0 else -sp
    n = 4
    om0 = (fa[0] - old0)
    om1 = (fa[1] - old1)
    bums = LAYOUTS[layout]
    for s in range(n):
        a0 = old0 + (fa[0] - old0) * (s + 1) / n
        a1 = old1 + (fa[1] - old1) * (s + 1) / n
        for b in balls:
            b[3] += gx / n
            b[0] += b[2] / n
            b[1] += b[3] / n
            for w in WALLS:
                if w[6] and b[3] < -0.6:
                    continue
                if min(w[0], w[2]) - 2.6 < b[0] < max(w[0], w[2]) + 2.6:
                    if min(w[1], w[3]) - 2.6 < b[1] < max(w[1], w[3]) + 2.6:
                        v = hit_seg(b, w[0], w[1], w[2], w[3], R, w[4], w[5])
                        if v > 0.5:
                            if w[5]:
                                add_score(5)
                                snd(500, 15)
                            elif v > 1.5:
                                snd(200, 10)
            if b[1] > 38:
                hit_flip(b, 0, a0, om0)
                hit_flip(b, 1, a1, om1)
            for k in range(len(bums)):
                bu = bums[k]
                dx = b[0] - bu[0]
                dy = b[1] - bu[1]
                rr = R + bu[2]
                if dx * dx + dy * dy < rr * rr:
                    d = sqrt(dx * dx + dy * dy)
                    if d < 1e-4:
                        dx = 1.0
                        d = 1.0
                    nx = dx / d
                    ny = dy / d
                    b[0] = bu[0] + nx * rr
                    b[1] = bu[1] + ny * rr
                    vn = b[2] * nx + b[3] * ny
                    if vn < 0:
                        b[2] -= 1.3 * vn * nx
                        b[3] -= 1.3 * vn * ny
                    if bcool[k] <= 0:
                        vo = b[2] * nx + b[3] * ny
                        if vo < 1.45:
                            b[2] += nx * (1.45 - vo)
                            b[3] += ny * (1.45 - vo)
                        flash[k] = 6
                        bcool[k] = 5
                        idle_t = 0
                        add_score(10)
                        bump_hits += 1
                        snd(700 + (k % 3) * 120, 20)
            for k in range(3):
                if tg[k]:
                    dx = b[0] - TARGETS[k][0]
                    dy = b[1] - TARGETS[k][1]
                    rr = R + 1.7
                    if dx * dx + dy * dy < rr * rr:
                        d = sqrt(dx * dx + dy * dy)
                        if d < 1e-4:
                            dx = 1.0
                            d = 1.0
                        nx = dx / d
                        ny = dy / d
                        b[0] = TARGETS[k][0] + nx * rr
                        b[1] = TARGETS[k][1] + ny * rr
                        vn = b[2] * nx + b[3] * ny
                        if vn < 0:
                            b[2] -= 1.7 * vn * nx
                            b[3] -= 1.7 * vn * ny
                        tg[k] = False
                        idle_t = 0
                        add_score(100)
                        snd(1200, 40)
                        if not (tg[0] or tg[1] or tg[2]):
                            tg[0] = tg[1] = tg[2] = True
                            mult += 1
                            if mult > 5:
                                mult = 1
                                layout = (layout + 1) % 3
                                for q in range(6):
                                    flash[q] = 0
                                    bcool[q] = 0
                                bums = LAYOUTS[layout]
                                build_static()
                                add_score(1000)
                                set_msg("NEW MAP!")
                                jingle(WINJ)
                            else:
                                set_msg("BONUS X" + str(mult))
                                jingle(WINJ)
            b[2] *= 0.9993
            b[3] *= 0.9993
            sp = sqrt(b[2] * b[2] + b[3] * b[3])
            if sp > VMAX:
                b[2] *= VMAX / sp
                b[3] *= VMAX / sp
    for b in balls:
        if b[2] * b[2] + b[3] * b[3] < 0.004:
            b[4] += 1
            if b[4] > 150:
                b[4] = 0
                b[2] += rnd(-0.9, 0.9)
                b[3] -= 0.9
                snd(200, 20)
        else:
            b[4] = 0
    for k in range(6):
        if flash[k] > 0:
            flash[k] -= 1
        if bcool[k] > 0:
            bcool[k] -= 1

def lose_ball():
    # returns True when the game is over
    global balls_left, saved, ball_no
    if save_t > 0 and not saved:
        saved = True
        serve()
        set_msg("SAVED!")
        snd(900, 100)
        return False
    balls_left -= 1
    snd(120, 300)
    if balls_left <= 0:
        return True
    ball_no += 1
    serve()
    saved = False
    set_msg("BALL " + str(ball_no))
    return False

def update(L, Rt, ah, up_edge):
    global mode, charge, save_t, saved, nudges, nudge_t, tilt, bump_hits
    if mode == 0:
        if ah:
            charge = min(1.0, charge + 0.025)
        elif charge > 0.05:
            b = balls[0]
            b[3] = -(2.85 + 2.15 * charge)
            b[2] = 0.0
            mode = 1
            save_t = 330
            saved = False
            snd(300 + int(charge * 600), 80)
            charge = 0.0
        else:
            charge = 0.0
        if mode == 0:
            return False
    if save_t > 0:
        save_t -= 1
    if nudge_t > 0:
        nudge_t -= 1
    else:
        nudges = 0
    if up_edge and not tilt:
        nudges += 1
        nudge_t = 120
        for b in balls:
            b[3] -= 0.55
            b[2] += rnd(-0.3, 0.3)
        snd(150, 30)
        if nudges > 3:
            tilt = True
            set_msg("TILT!")
            snd(100, 300)
    physics(L, Rt)
    # multiball
    if bump_hits >= 30 and len(balls) < 3:
        bump_hits = 0
        for i in range(2):
            balls.append([15.0 + i * 3, 8.0, rnd(-0.6, 0.6), 0.8, 0])
        set_msg("MULTI!")
        jingle(MBJ)
    i = 0
    while i < len(balls):
        if balls[i][1] > HT + 3:
            balls.pop(i)
        else:
            i += 1
    if len(balls) > 1:
        for b in balls:
            if b[0] > 30.0 and b[1] > 64 and b[2] * b[2] + b[3] * b[3] < 0.12:
                b[2] = 0.0
                b[3] = -(4.2 + random.random() * 0.8)
                snd(500, 40)
    if not balls:
        return lose_ball()
    if len(balls) == 1 and mode == 1:
        b = balls[0]
        if b[0] > 30.0 and b[1] > 64 and abs(b[3]) < 0.35:
            mode = 0
            charge = 0.0
            b[2] = 0.0
            b[3] = 0.0
            b[0] = LANE
            b[1] = 66.2
    return False

# ---- drawing the game ----
def draw_game(ft):
    copy_static()
    bums = LAYOUTS[layout]
    for k in range(len(bums)):
        if flash[k] > 0:
            bu = bums[k]
            cx = int(bu[0] + OX + 0.5)
            cy = int(bu[1] + 0.5)
            ri = int(bu[2] + 0.5)
            r2 = bu[2] * bu[2] + 0.6
            for i in range(-ri, ri + 1):
                for j in range(-ri, ri + 1):
                    if i * i + j * j <= r2:
                        pset(cx + i, cy + j)
    for k in range(3):
        x = int(TARGETS[k][0] + OX + 0.5)
        y = int(TARGETS[k][1])
        if tg[k]:
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    pset(x + i, y + j)
        else:
            pset(x, y)
    for i in (0, 1):
        px = PIV[i][0] + OX
        py = PIV[i][1]
        a = fa[i]
        tx = px + cos(a) * FL
        ty = py + sin(a) * FL
        line(px - 1, py, tx - 1, ty)
        line(px, py, tx, ty)
        line(px + 1, py, tx + 1, ty)
    if mode == 0:
        x = int(LANE + OX + 0.5)
        y = int(68.0 + charge * 4)
        pset(x - 1, y)
        pset(x, y)
        pset(x + 1, y)
        pset(x, y + 2)
        pset(x, y + 3)
    for b in balls:
        x = int(b[0] + OX + 0.5)
        y = int(b[1] + 0.5)
        pset(x, y)
        pset(x - 1, y)
        pset(x + 1, y)
        pset(x, y - 1)
        pset(x, y + 1)
    pset(3, 68)
    pset(2, 69)
    pset(3, 69)
    pset(4, 69)
    pset(3, 70)
    text(str(balls_left), 7, 67)
    text(str(score), 12, 67)
    text("X" + str(mult), 0, 0)
    if tilt and (ft & 8) < 4:
        text("TILT", 12, 44)
    if msg_t > 0:
        banner(msg)

# ---- screens ----
def menu():
    sel = 0
    t = 0
    wait_release()
    jingle(MENUJ)
    while True:
        poll()
        jtick()
        if not JQ and jt == 0:
            jingle(MENUJ)
        if hit(UU):
            sel = (sel - 1) % 4
            snd(500, 15)
        if hit(UD):
            sel = (sel + 1) % 4
            snd(500, 15)
        if hit(KA) or hit(UR):
            snd(800, 40)
            return sel
        clear()
        text("PIN", 9, 3, 2)
        text("BALL", 5, 15, 2)
        for k in (0, 1, 2):
            bxm = 20 + int(14 * sin(t * 0.11 + k * 2.1))
            bym = 27 + int(1.6 * sin(t * 0.43 + k))
            for o in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                pset(bxm + o[0], bym + o[1])
        items = ("PLAY", "SCORES", "OPTIONS", "HELP")
        for i in range(4):
            y = 33 + i * 8
            if i == sel:
                text(">", 1, y)
            text(items[i], 7, y)
        text("HI " + str(SCORES[0][1]), 2, 66)
        present()
        t += 1

def scores_screen():
    wait_release()
    while True:
        poll()
        if hit(KA) or hit(KB) or hit(UL):
            return
        clear()
        ctext("SCORES", 3)
        line(0, 10, 39, 10)
        for i in range(len(SCORES)):
            y = 14 + i * 9
            e = SCORES[i]
            text(str(i + 1), 0, y)
            text(e[0], 5, y)
            s = str(e[1])
            text(s, 40 - tw(s), y)
        ctext("A:BACK", 64)
        present()

HELP = (
    ("FLIPPERS", "DPAD L/R", "OR B / A", "", "LAUNCH:", "HOLD DOWN", "OR A / B", "", "UP: NUDGE", "DN: PAUSE"),
    ("SCORING", "", "BUMPER 10", "SLING 5", "TARGET 100", "", "3 TARGETS:", "BONUS X+1", "X5=NEW MAP", "", "3 TRIES"),
    ("MULTIBALL:", "30 BUMPER", "HITS GIVE", "3 BALLS", "", "SAVER:", "1ST 11 SEC", "", "TILT: DONT", "NUDGE 4X"),
)

def help_screen():
    wait_release()
    for pg in HELP:
        while True:
            poll()
            if hit(KA) or hit(UR):
                break
            if hit(KB):
                return
            clear()
            for i in range(len(pg)):
                text(pg[i], 0, 3 + i * 6)
            present()

def options():
    global ROT, SND, SCORES
    sel = 0
    sure = False
    wait_release()
    while True:
        poll()
        if hit(UU):
            sel = (sel - 1) % 4
            sure = False
        if hit(UD):
            sel = (sel + 1) % 4
            sure = False
        if hit(KB):
            break
        if hit(KA) or hit(UR) or hit(UL):
            if sel == 0:
                ROT = 1 - ROT
                build_static()
                wait_release()
            elif sel == 1:
                SND = 1 - SND
                snd(700, 40)
            elif sel == 2:
                if sure:
                    SCORES = [[e[0], e[1]] for e in DEFHS]
                    sure = False
                else:
                    sure = True
            else:
                break
        clear()
        ctext("OPTIONS", 3)
        line(0, 10, 39, 10)
        rows = ("ROT: CCW" if ROT else "ROT: CW", "SND: ON" if SND else "SND: OFF",
                "SURE?" if sure else "RESET HS", "BACK")
        for i in range(4):
            y = 15 + i * 8
            if i == sel:
                text(">", 0, y)
            text(rows[i], 5, y)
        ctext("B:EXIT", 64)
        present()
    save_data()

def pause():
    banner("PAUSED", 22, 20)
    text("A RESUME", 4, 34)
    text("B QUIT", 4, 42)
    while True:
        poll()
        if hit(KA) or hit(UD):
            wait_release()
            return True
        if hit(KB):
            return False
        present()

def enter_name():
    ltr = [0, 0, 0]
    pos = 0
    t = 0
    wait_release()
    while True:
        poll()
        if hit(UU):
            ltr[pos] = (ltr[pos] + 1) % 26
        if hit(UD):
            ltr[pos] = (ltr[pos] - 1) % 26
        if hit(UR) or hit(KA):
            pos += 1
            if pos == 3:
                return "".join([chr(65 + c) for c in ltr])
        if (hit(UL) or hit(KB)) and pos > 0:
            pos -= 1
        clear()
        ctext("NEW HIGH", 4)
        ctext("SCORE!", 12)
        for i in range(3):
            text(chr(65 + ltr[i]), 9 + i * 8, 30, 2)
        if (t >> 3) & 1:
            for i in range(6):
                pset(9 + pos * 8 + i, 42)
        ctext("UD: LETTER", 52)
        ctext("A: NEXT", 60)
        present()
        t += 1

def game_over():
    hi = score > 0 and (len(SCORES) < 5 or score > SCORES[-1][1])
    wait_release()
    jingle(OVJ)
    t = 0
    while True:
        poll()
        jtick()
        if t > 25 and (hit(KA) or hit(KB)):
            break
        clear()
        ctext("GAME", 4, 2)
        ctext("OVER", 16, 2)
        ctext("SCORE", 34)
        ctext(str(score), 42)
        if hi and (t >> 3) & 1:
            ctext("NEW HIGH!", 52)
        ctext("A:OK", 64)
        present()
        t += 1
    if hi:
        nm = enter_name()
        SCORES.append([nm, score])
        SCORES.sort(key=lambda e: e[1], reverse=True)
        del SCORES[5:]
        save_data()
        scores_screen()

# ---- main game ----
def play():
    global msg_t
    gc.collect()
    new_game()
    ft = 0
    wait_release()
    while True:
        poll()
        ft += 1
        lf = cur[UL] or cur[KB]
        rf = cur[UR] or cur[KA]
        ah = cur[UD] or cur[KA] or cur[KB]
        if mode == 1 and hit(UD):
            if not pause():
                return
        if update(lf, rf, ah, hit(UU)):
            break
        if msg_t > 0:
            msg_t -= 1
        jtick()
        draw_game(ft)
        present()
    game_over()

def main():
    gc.collect()
    thumby.display.setFPS(FPS)
    load_data()
    build_static()
    while True:
        c = menu()
        if c == 0:
            play()
        elif c == 1:
            scores_screen()
        elif c == 2:
            options()
        else:
            help_screen()

main()
