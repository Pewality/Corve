# ROADSTER AIR - Tesla Roadster on compressed-air jets.  Thumby / MicroPython
# A (hold): 4 lift jets ON, release: OFF.   B (hold): rear rocket booster.
# UP/DOWN: forward/back on the ground, TILT nose down/up in the air (no button needed)
# LEFT/RIGHT: steer (front-wheel jets).  Land slower than 12 m/s (43 km/h) or you crash!
# SKYSCRAPERS: touch a wall slowly and the car's suction turns on by itself. On a wall the
# arrows drive UP/DOWN/LEFT/RIGHT, A jumps off, the roof is a landing place. Hit one fast = crash.
# The air tank refills by itself.   LEFT+RIGHT held 0.5s: pause menu.
import thumby, math, time, gc
from array import array
try:
    from random import random as rnd
except ImportError:
    _sd = [7]
    def rnd():
        _sd[0] = (_sd[0] * 75 + 74) % 65537
        return _sd[0] / 65537
D = thumby.display
D.setFPS(30)
dl = D.drawLine; dp = D.setPixel; tx = D.drawText
sin = math.sin; cos = math.cos; sqrt = math.sqrt; atan2 = math.atan2; asin = math.asin; floor = math.floor
FX = 52.0; CX = 36; CY = 21           # CY below the middle = more sky, so tall buildings show

# car in cm (x right, y up, z forward): 12 body points + 4 wheel posts
_B = ((-75,30,210),(75,30,210),(-95,55,120),(95,55,120),(-85,110,-10),(85,110,-10),(-85,100,-90),
      (85,100,-90),(-80,65,-210),(80,65,-210),(-95,20,120),(95,20,120))
VT = tuple((p[0] * .01, p[1] * .01, p[2] * .01) for p in _B) + tuple(
    (x * .01, y, z * .01) for x, z in ((-100,125),(100,125),(-100,-115),(100,-115)) for y in (0.7, 0.0))
EP = ((0,1),(0,2),(1,3),(2,3),(2,4),(3,5),(4,5),(4,6),(5,7),(6,7),(6,8),(7,9),(8,9),(2,10),(3,11),
      (10,11),(10,8),(11,9),(0,10),(1,11),(12,13),(14,15),(16,17),(18,19))
PX = [0] * 20; PY = [0] * 20
SX = (-1.0, 1.0, -1.0, 1.0)  # jets: front-left, front-right, rear-left, rear-right
SZ = (1.0, 1.0, -1.0, -1.0)
STAR = []
for _i in range(20):
    while True:
        _v = (rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1)
        _m = _v[0] * _v[0] + _v[1] * _v[1] + _v[2] * _v[2]
        if 0.1 < _m < 1.0:
            break
    STAR.append((_v[0] / sqrt(_m), _v[1] / sqrt(_m), _v[2] / sqrt(_m)))
WORLD = ((9.8, 1.0), (3.7, 0.2), (1.6, 0.0), (0.0, 0.0))  # gravity, air density
OPT = (("MODE", ("FREE", "RINGS", "PADS")), ("WORLD", ("EARTH", "MARS", "MOON", "SPACE")),
       ("PARTS", ("LOW", "MED", "HIGH")), ("CAM", ("CHASE", "FAR", "UNDER")),
       ("SOUND", ("OFF", "ON")), ("FPS", ("HIDE", "SHOW")), ("TILT", ("AUTO", "FREE")), ("GRID", ("OFF", "ON")), ("CITY", ("LOW", "MED", "HIGH")))
CFG = [0, 0, 1, 0, 1, 0, 0, 1, 1]
NOPT = 9
FNX = (1.0, -1.0, 0.0, 0.0)      # wall normals: +x, -x, +z, -z face of a building
FNZ = (0.0, 0.0, 1.0, -1.0)
CD = (1, 2, 3)                   # city density (cells out of 10 that hold a building)
PR = (thumby.buttonU.pressed, thumby.buttonD.pressed, thumby.buttonL.pressed,
      thumby.buttonR.pressed, thumby.buttonA.pressed, thumby.buttonB.pressed)


def keys():
    return PR[0]() + 2 * PR[1]() + 4 * PR[2]() + 8 * PR[3]() + 16 * PR[4]() + 32 * PR[5]()


def beep(f, ms):
    if CFG[4]:
        try: thumby.audio.play(f, ms)
        except Exception: pass


def hs(v=None):
    try:
        s = thumby.saveData
        s.setName("RoadsterAir")
        if v is None:
            return int(s.getItem("hs")) if s.hasItem("hs") else 0
        s.setItem("hs", v); s.save()
    except Exception:
        pass
    return 0


def pyl(i, j):
    # procedural skyscraper in the 60 m cell (i, j): (x, z, height, half-width x, half-width z) or None
    a = (i * 1103 + j * 2713 + 11) & 1023
    if a % 10 >= CD[CFG[8]]:
        return None
    b = ((((i * 197 + 13) & 1023) * ((j * 311 + 17) & 1023) >> 4) ^ a) & 255
    return (i * 60 + 22 + (a & 15), j * 60 + 22 + ((a >> 4) & 15), 28.0 + ((a ^ b) & 63) * 1.3, 7.0 + (b & 3) * 2.0, 7.0 + ((b >> 2) & 3) * 2.0)


def rot(ax, ay, az, bx, by, bz, t):
    c = cos(t); s = sin(t)
    return (ax * c + bx * s, ay * c + by * s, az * c + bz * s, bx * c - ax * s, by * c - ay * s, bz * c - az * s)


def drawcar(dx, dy, dz, R, U, F, br=0.0):
    r0, r1, r2 = R; u0, u1, u2 = U; f0, f1, f2 = F
    k = 0
    for a, b, c in VT:
        z = dz + a * r2 + b * u2 + c * f2
        s = FX / (z if z > 0.3 else 0.3)
        PX[k] = int(CX + (dx + a * r0 + b * u0 + c * f0) * s)
        PY[k] = int(CY - (dy + a * r1 + b * u1 + c * f1) * s)
        k += 1
    for p, q in EP:
        if br == 0.0 or rnd() > br: dl(PX[p], PY[p], PX[q], PY[q], 1)       # br: share of edges broken off (wreck)


def jets(dx, dy, dz, R, U, F, T, sl, sr, bo):
    # air plumes: 4 under the wheels, 2 sideways at the front wheels, rocket at the rear
    def ln(a, b, c, a2, b2, c2):
        z = dz + a * R[2] + b * U[2] + c * F[2]
        z2 = dz + a2 * R[2] + b2 * U[2] + c2 * F[2]
        if z > 0.3 and z2 > 0.3:
            dl(int(CX + (dx + a * R[0] + b * U[0] + c * F[0]) * FX / z), int(CY - (dy + a * R[1] + b * U[1] + c * F[1]) * FX / z),
               int(CX + (dx + a2 * R[0] + b2 * U[0] + c2 * F[0]) * FX / z2), int(CY - (dy + a2 * R[1] + b2 * U[1] + c2 * F[1]) * FX / z2), 1)
    for j in range(4):
        if T[j] > 0.04:
            ln(SX[j] * 0.9, 0.22, SZ[j] * 1.2, SX[j] * 0.9, 0.22 - 0.4 - T[j] * 2.0 * (0.75 + rnd() * 0.5), SZ[j] * 1.2)
    if sl > 0.1: ln(-1.05, 0.35, 1.25, -1.3 - sl * 1.4 * (0.7 + rnd() * 0.6), 0.35, 1.25)
    if sr > 0.1: ln(1.05, 0.35, 1.25, 1.3 + sr * 1.4 * (0.7 + rnd() * 0.6), 0.35, 1.25)
    if bo:
        h = 2.0 + rnd() * 2.0
        ln(0.0, 0.45, -2.1, 0.0, 0.45, -2.1 - h)
        ln(0.0, 0.45, -2.1, 0.35, 0.5, -2.1 - h * 0.6)
        ln(0.0, 0.45, -2.1, -0.35, 0.5, -2.1 - h * 0.6)


def menu(resume):
    old = CFG[:3] + CFG[8:]
    n_it = NOPT + (2 if resume else 1)
    sel = off = 0
    prev = keys()
    while True:
        k = keys(); n = k & ~prev; prev = k
        if n & 1: sel = (sel - 1) % n_it
        if n & 2: sel = (sel + 1) % n_it
        if 0 < sel <= NOPT and n & 28:
            o = OPT[sel - 1][1]
            CFG[sel - 1] = (CFG[sel - 1] + (len(o) - 1 if n & 4 else 1)) % len(o)
        if n & 32 or (n & 16 and sel == 0): break
        if n & 16 and sel == NOPT + 1: return 2
        off = min(max(off, sel - 3), sel)
        D.fill(0)
        for r in range(4):
            i = off + r
            if i >= n_it: break
            s = ("RESUME" if resume else "GO!") if i == 0 else ("QUIT" if i == NOPT + 1 else OPT[i - 1][0] + " " + OPT[i - 1][1][CFG[i - 1]])
            tx((">" if i == sel else " ") + s, 0, 2 + r * 10, 1)
        D.update()
    return 1 if old != CFG[:3] + CFG[8:] else 0


def title():
    t = 0.0
    prev = keys()
    T4 = [0.5] * 4
    while True:
        k = keys(); n = k & ~prev; prev = k
        if n & 16: return
        if n & 32:
            menu(False); prev = keys()
        t += 0.04
        D.fill(0)
        for i in range(-3, 4): dl(36 + i * 3, 29, 36 + i * 20, 40, 1)
        for j in range(4):
            y = 29 + int(11 * (((j + t * 0.8) % 4) / 4.0) ** 2)
            dl(0, y, 71, y, 1)
        ca = cos(t * 0.9); sa = sin(t * 0.9)
        R = (ca, -sa * 0.296, -sa * 0.955); U = (0.0, 0.955, -0.296); F = (sa, ca * 0.296, ca * 0.955)
        drawcar(0.0, -1.6, 7.0, R, U, F)
        jets(0.0, -1.6, 7.0, R, U, F, T4, 0.0, 0.0, False)
        D.drawFilledRectangle(0, 32, 72, 8, 0); tx("A PLAY B OPT", 0, 33, 1)
        D.drawFilledRectangle(6, 0, 60, 8, 0); tx("ROADSTER AIR", 0, 0, 1)
        D.update()


def gameover(score):
    best = hs()
    nb = score > best
    if nb: hs(score); best = score
    prev = keys(); t = 0
    while True:
        k = keys(); n = k & ~prev; prev = k
        if n & 16: return True
        if n & 32: return False
        t += 1
        D.fill(0)
        tx("TIME UP", 15, 2, 1); tx("SCORE " + str(score), 0, 13, 1); tx("BEST " + str(best), 0, 22, 1)
        if nb and (t & 8): tx("NEW!", 48, 22, 1)
        tx("A:GO  B:MENU", 0, 32, 1)
        D.update()


def play():
    gc.collect()
    mode, world, camm = CFG[0], CFG[1], CFG[3]
    if world == 3 and mode == 2: mode = 1         # no pads in space
    g, rho = WORLD[world]
    NA, NS = ((8, 10), (12, 16), (18, 24))[CFG[2]]     # ambient air dots, jet/dust particles
    A = array('f', [9999.0] * (NA * 3))
    S = array('f', [0.0] * (NS * 6)); SL = array('f', [0.0] * NS); SK = array('b', [0] * NS)
    T = [0.0] * 4
    RG = [0.0, 12.0 if world < 3 and mode == 1 else 0.0, 60.0, 0.0, 1.0]
    rsp = 0.0; pi = 0
    px = py = pz = vx = vy = vz = 0.0
    fx = 0.0; fy = 0.0; fz = 1.0
    ux = 0.0; uy = 1.0; uz = 0.0
    rx = 1.0; ry = 0.0; rz = 0.0
    wp = wr = wy = 0.0          # angular rates: nose-up, roll-right, yaw-right
    cj = 0.0                    # lift-jet valve (opens while A is held)
    sL = sR = 0.0
    bon = False
    tank = 100.0
    ng = 4 if world < 3 else 0
    gnd = world < 3
    if world == 3: vz = 8.0
    score = combo = 0
    since = 99.0; tleft = 45.0; air = 0.0
    msg = ""
    mt = crash_t = 0.0
    flash = 0
    kx = ky = kz = 0.0
    chx = 0.0; chz = 1.0
    cfx = 0.0; cfy = 0.0; cfz = 1.0
    ccx = 0.0; ccy = 4.0; ccz = -9.0
    crx = 1.0; crz = 0.0
    cux = 0.0; cuy = 1.0; cuz = 0.0
    sp = sa = wx = wz = tt = hold_t = agl = 0.0
    dtm = 0.033; yh = 0
    frame = ox = oy = rdist = lod = shk = 0
    wl = fc = 0                 # wl: suction-driving on a skyscraper wall, fc: which face (+x -x +z -z)
    bx = bz = hw_ = hd_ = bh = fh = lv = inv = pd = lastb = 0.0   # current building, roof height under the car, re-level / grace timers
    lfx = lfz = tux = tuy = tuz = tfx = tfy = tfz = 0.0
    bd = None
    acc = 0.0                   # pitch angle turned since take-off (flip counter)

    def spawn(kd, x, y, z, a, b, c_, lf):
        nonlocal pi
        j = pi * 6
        S[j] = x; S[j + 1] = y; S[j + 2] = z; S[j + 3] = a; S[j + 4] = b; S[j + 5] = c_
        SL[pi] = lf; SK[pi] = kd
        pi = pi + 1 if pi < NS - 1 else 0

    def cam(x, y, z):
        x -= ccx; y -= ccy; z -= ccz
        return (x * crx + z * crz, x * cux + y * cuy + z * cuz, x * cfx + y * cfy + z * cfz)

    def pr(x, y, z):
        a, b, d = cam(x, y, z)
        if d < 0.3: return None
        s = FX / d
        a = CX + ox + a * s; b = CY + oy - b * s
        return (int(a), int(b)) if -300 < a < 300 and -300 < b < 300 else None

    def seg(x0, y0, z0, x1, y1, z1):
        a0, b0, d0 = cam(x0, y0, z0)
        a1, b1, d1 = cam(x1, y1, z1)
        clip(a0, b0, d0, a1, b1, d1)

    def clip(a0, b0, d0, a1, b1, d1):
        # camera-space line clipped to the near plane and the screen, then drawn
        if d0 < 0.5:
            if d1 < 0.5: return
            t = (0.5 - d0) / (d1 - d0); a0 += (a1 - a0) * t; b0 += (b1 - b0) * t; d0 = 0.5
        elif d1 < 0.5:
            t = (0.5 - d1) / (d0 - d1); a1 += (a0 - a1) * t; b1 += (b0 - b1) * t; d1 = 0.5
        xa = CX + ox + a0 * FX / d0; ya = CY + oy - b0 * FX / d0
        xb = CX + ox + a1 * FX / d1; yb = CY + oy - b1 * FX / d1
        if (xa < 0 and xb < 0) or (xa > 71 and xb > 71) or (ya < 0 and yb < 0) or (ya > 39 and yb > 39): return
        if 0 <= xa <= 71 and 0 <= xb <= 71 and 0 <= ya <= 39 and 0 <= yb <= 39:
            dl(int(xa), int(ya), int(xb), int(yb), 1); return
        dx = xb - xa; dy = yb - ya
        u0 = 0.0; u1 = 1.0
        for p, q in ((-dx, xa), (dx, 71 - xa), (-dy, ya), (dy, 39 - ya)):
            if p == 0:
                if q < 0: return
            else:
                r = q / p
                if p < 0:
                    if r > u1: return
                    if r > u0: u0 = r
                else:
                    if r < u0: return
                    if r < u1: u1 = r
        dl(int(xa + dx * u0), int(ya + dy * u0), int(xa + dx * u1), int(ya + dy * u1), 1)

    def grid(Gs, n):
        # ground grid patch ahead of the car. Projection is linear, so each grid line's
        # contribution is computed once per axis and the endpoints are just sums
        i0 = floor((px + chx * Gs) / Gs) - n // 2
        j0 = floor((pz + chz * Gs) / Gs) - n // 2
        XL = []; ZL = []
        for i in range(n):
            v = (i0 + i) * Gs - ccx; w = (j0 + i) * Gs - ccz
            XL.append((v * crx, v * cux, v * cfx))
            ZL.append((w * crz, w * cuz - ccy * cuy, w * cfz - ccy * cfy))
        xa = XL[0]; xb = XL[n - 1]; za = ZL[0]; zb = ZL[n - 1]
        for i in range(n):
            x = XL[i]; z = ZL[i]
            clip(x[0] + za[0], x[1] + za[1], x[2] + za[2], x[0] + zb[0], x[1] + zb[1], x[2] + zb[2])
            clip(z[0] + xa[0], z[1] + xa[1], z[2] + xa[2], z[0] + xb[0], z[1] + xb[1], z[2] + xb[2])

    def bld(b):
        # skyscraper wireframe: 4 vertical edges + roof (+ footprint and floor lines when close).
        # Corners are projected once (the projection is linear)
        h = b[2]; ex = ccx - b[0]; ez = ccz - b[1]
        if ex * cfx + ez * cfz > 25.0: return                 # behind the camera
        nr = ex * ex + ez * ez
        if nr > (10000.0 if lod == 0 else 5000.0):
            seg(b[0], 0.0, b[1], b[0], h, b[1])             # far away: just a mast
            return
        hb = h * cuy; hd = h * cfy; yy = -ccy
        P = []
        for v, w in ((b[0] - b[3], b[1] - b[4]), (b[0] + b[3], b[1] - b[4]), (b[0] + b[3], b[1] + b[4]), (b[0] - b[3], b[1] + b[4])):
            v -= ccx; w -= ccz
            P.append((v * crx + w * crz, v * cux + yy * cuy + w * cuz, v * cfx + yy * cfy + w * cfz))
        dd = sqrt(nr); nr = nr < 3000.0 and lod == 0
        for i in range(4):
            p = P[i]; q = P[(i + 1) & 3]
            clip(p[0], p[1], p[2], p[0], p[1] + hb, p[2] + hd)
            clip(p[0], p[1] + hb, p[2] + hd, q[0], q[1] + hb, q[2] + hd)
            if nr: clip(p[0], p[1], p[2], q[0], q[1], q[2])
        if nr and dd < 45.0:                                # grid on the wall that faces us most
            m = (-ez - b[4], ex - b[3], ez - b[4], -ex - b[3])
            i = m.index(max(m)); p = P[i]; q = P[(i + 1) & 3]
            gy = max(4.0, dd * 0.3) if CFG[7] else 18.0       # floor lines, only up to the top of the screen
            y = gy; ym = min(h, 3.0 + dd * 0.45)
            while y < ym:
                clip(p[0], p[1] + y * cuy, p[2] + y * cfy, q[0], q[1] + y * cuy, q[2] + y * cfy)
                y += gy
            if CFG[7] and dd < 36.0:                        # window columns too
                for t in (0.33, 0.67):
                    a = p[0] + (q[0] - p[0]) * t; c_ = p[1] + (q[1] - p[1]) * t; e = p[2] + (q[2] - p[2]) * t
                    clip(a, c_, e, a, c_ + hb, e + hd)

    def newring():
        h = atan2(fx, fz) + (rnd() - 0.5) * 1.6
        d = 70.0 + rnd() * 55.0
        RG[0] = px + sin(h) * d
        RG[1] = py + (rnd() - 0.5) * 40.0 if world == 3 else 5.0 + rnd() * 28.0
        RG[2] = pz + cos(h) * d
        h += rnd() - 0.5
        RG[3] = sin(h); RG[4] = cos(h)
        if world < 3:
            a = pyl(floor(RG[0] / 60.0), floor(RG[2] / 60.0))
            if mode == 2:
                RG[1] = 0.0
                if a: RG[0] = a[0]; RG[2] = a[1]; RG[1] = a[2]          # pad on a skyscraper roof
            elif a and abs(RG[0] - a[0]) < a[3] + 10.0 and abs(RG[2] - a[1]) < a[4] + 10.0 and RG[1] < a[2] + 10.0:
                RG[1] = a[2] + 10.0                                      # ring floats above the roof

    if mode: newring()
    t0 = time.ticks_ms()
    while True:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, t0) / 1000.0
        t0 = now
        dtm += (dt - dtm) * 0.08
        lod = 0 if dtm < 0.042 else 1          # auto level-of-detail keeps it smooth
        dt = 0.05 if dt > 0.05 else (0.01 if dt < 0.01 else dt)
        frame += 1; tt += dt
        k = keys()
        if (k & 12) == 12:
            hold_t += dt
            if hold_t > 0.5:
                r = menu(True)
                if r == 1: return True
                if r == 2: return False
                camm = CFG[3]; hold_t = 0.0
                gc.collect(); t0 = time.ticks_ms()
                continue
        else:
            hold_t = 0.0
        if mt > 0: mt -= dt
        wx = 3.0 * sin(tt * 0.13) * rho; wz = 2.0 * cos(tt * 0.09) * rho
        boom = False

        pd = dt * 0.3 if crash_t > 0 else dt           # particles and the wreck run in slow motion
        if crash_t > 0:
            crash_t -= dt
            fx, fy, fz, ux, uy, uz = rot(fx, fy, fz, ux, uy, uz, wp * pd)      # the wreck tumbles
            ux, uy, uz, rx, ry, rz = rot(ux, uy, uz, rx, ry, rz, wr * pd)
            if crash_t <= 0:
                if mode and tleft <= 0: return gameover(score)
                fx = chx; fz = chz
                if world < 3:
                    py = 0.0; gnd = True; ng = 4
                    a = pyl(floor(px / 60.0), floor(pz / 60.0))
                    if a and abs(px - a[0]) < a[3] + 7.0 and abs(pz - a[1]) < a[4] + 7.0: px = 0.0; fx = 0.0; fz = 1.0      # wrecked at a building: restart on the road
                fy = 0.0; ux = 0.0; uy = 1.0; uz = 0.0
                rx = fz; ry = 0.0; rz = -fx
                vx = vy = vz = wp = wr = wy = cj = 0.0
                tank = 100.0; air = 0.0; wl = 0; lv = 0.0; inv = 1.5; acc = 0.0
                for i in range(NS): SL[i] = 0.0
        else:
            fwd = (k & 1) - ((k & 2) >> 1)
            yin = ((k & 8) >> 3) - ((k & 4) >> 2)
            kA = k & 16
            bon = (k & 32) != 0 and tank > 2.0
            tf = 1.0 if tank > 12.0 else 0.5 + tank * 0.04      # thrust sags as pressure drops
            hn = sqrt(fx * fx + fz * fz)
            hxn, hzn = (fx / hn, fz / hn) if hn > 0.01 else (0.0, 1.0)
            vf = vx * hxn + vz * hzn
            vrt = vx * hzn - vz * hxn

            if inv > 0.0: inv -= dt
            fh = 0.0; bd = None
            if world < 3:      # skyscraper in this cell? above its roof the roof is the floor
                bd = pyl(floor(px / 60.0), floor(pz / 60.0))
                if bd and abs(px - bd[0]) < bd[3] and abs(pz - bd[1]) < bd[4] and py >= bd[2] - 0.8: fh = bd[2]
            hgt = py - fh
            if wl:      # ---- suction driving: the arrows move the car along the wall, A jumps off
                st = 0.0; T[0] = T[1] = T[2] = T[3] = 0.0; sL = sR = cj = 0.0
                nx_ = FNX[fc]; nz_ = FNZ[fc]
                if kA:
                    wl = 0; vx += nx_ * 7.0; vz += nz_ * 7.0; vy += 2.0; inv = 0.8
                    lv = 0.7; lfx = nx_; lfz = nz_
                else:
                    ix = ((k & 8) >> 3) - ((k & 4) >> 2)
                    vm = 13.0 + (12.0 if bon else 0.0)
                    kk = min(1.0, 6.0 * dt)
                    vx += (-nz_ * ix * vm - vx) * kk; vy += (fwd * vm - vy) * kk; vz += (nx_ * ix * vm - vz) * kk
                    sp = sa = sqrt(vx * vx + vy * vy + vz * vz)
                    if sp > 1.0:
                        n = 1.0 / sp; tfx = vx * n; tfy = vy * n; tfz = vz * n
                    else:
                        tfx = fx; tfy = fy; tfz = fz
                    tux = nx_; tuy = 0.0; tuz = nz_
                    px += vx * dt; py += vy * dt; pz += vz * dt
                    kk = min(1.0, 15.0 * dt)           # the car sits on the wall plane
                    if fc == 0: px += (bx + hw_ - px) * kk
                    elif fc == 1: px += (bx - hw_ - px) * kk
                    elif fc == 2: pz += (bz + hd_ - pz) * kk
                    else: pz += (bz - hd_ - pz) * kk
                    q = fc
                    if fc < 2:                         # round a corner onto the next wall
                        if pz > bz + hd_: fc = 2; pz = bz + hd_
                        elif pz < bz - hd_: fc = 3; pz = bz - hd_
                    elif px > bx + hw_: fc = 0; px = bx + hw_
                    elif px < bx - hw_: fc = 1; px = bx - hw_
                    if fc != q:
                        d = vx * FNX[fc] + vz * FNZ[fc]
                        vx -= FNX[fc] * d; vz -= FNZ[fc] * d
                    if py > bh - 0.3:                  # over the top edge: onto the roof
                        wl = 0; py = bh; px -= nx_ * 2.0; pz -= nz_ * 2.0
                        vx = -nx_ * 5.0; vy = 0.0; vz = -nz_ * 5.0
                        lv = 0.5; lfx = -nx_; lfz = -nz_; inv = 1.0
                        if bx != lastb:
                            lastb = bx; pts = 50 + int(bh); score += pts; msg = "ROOF +" + str(pts); mt = 0.9; beep(1100, 80)
                    elif py < 0.5 and fwd < 0:         # down to the street: peel off the wall
                        wl = 0; py = 0.0; px += nx_ * 2.0; pz += nz_ * 2.0
                        vx = nx_ * 5.0; vy = 0.0; vz = nz_ * 5.0
                        lv = 0.5; lfx = nx_; lfz = nz_; inv = 1.0
                    elif py < 0.0: py = 0.0
            else:
                # lift jets: ON only while A is held (valve opens/closes in ~0.05 s)
                cj += ((1.0 if kA else 0.0) - cj) * (dt * 25.0 if dt < 0.04 else 1.0)
                if cj < 0.01: cj = 0.0
                T[0] = T[1] = T[2] = T[3] = 0.0
                st = 0.0
                pc = rc = 0.0
                if ng == 0 or kA:
                    # attitude thrusters work in the air with NO button held: UP = nose down, DOWN = nose up
                    if CFG[6] == 0 or (hgt < 3.0 and not fwd):      # AUTO: hold a tilt angle and level itself; FREE: you steer the rotation
                        th = asin(fy if -1.0 < fy < 1.0 else (1.0 if fy > 0 else -1.0))
                        tc = -0.6 * fwd if fwd else min(0.45, max(-0.45, 0.035 * vf))
                        pc = 26.0 * (tc - th) - 8.0 * wp
                    else:
                        pc = 8.0 * (-1.8 * fwd - wp)
                    pc = min(9.0, max(-9.0, pc))
                    rc = min(9.0, max(-9.0, 26.0 * (0.06 * wy * vf - 0.05 * vrt - atan2(-ry, uy)) - 8.0 * wr))
                    wp += pc * tf * dt; wr += rc * tf * dt
                if cj > 0:
                    for j in range(4):
                        T[j] = min(1.0, max(0.0, cj + 0.04 * (pc * SZ[j] - rc * SX[j]))) * tf
                        st += T[j]
                yc = min(1.0, max(-1.0, 3.0 * (1.7 * yin - wy)))     # front-wheel steering jets
                sL = yc * tf if yc > 0 else 0.0
                sR = -yc * tf if yc < 0 else 0.0

                # drag per body axis (slippery nose-first, flat underneath) + wind
                vax = vx - wx; vaz = vz - wz
                bf = vax * fx + vy * fy + vaz * fz
                bu = vax * ux + vy * uy + vaz * uz
                br = vax * rx + vy * ry + vaz * rz
                sa = sqrt(bf * bf + bu * bu + br * br)
                sp = sqrt(vx * vx + vy * vy + vz * vz)
                df = (24.0 if bon else 0.0) - (0.0022 * abs(bf) + 0.03) * bf * rho
                du = (0.012 * abs(bu) + 0.05) * bu * rho
                dr = (0.006 * abs(br) + 0.05) * br * rho
                a_up = 5.88 * st * (1.0 + (0.3 * (1.0 - hgt / 3.0) if world < 3 and hgt < 3.0 else 0.0))  # ground cushion
                a_sd = 4.0 * (sL - sR)
                vx += (ux * (a_up - du) + rx * (a_sd - dr) + fx * df) * dt
                vy += (uy * (a_up - du) + ry * (a_sd - dr) + fy * df - g) * dt
                vz += (uz * (a_up - du) + rz * (a_sd - dr) + fz * df) * dt
                if world == 3 and sp > 90.0:
                    kk = 90.0 / sp; vx *= kk; vy *= kk; vz *= kk
                kk = 0.8 + 0.02 * sa * rho
                wp -= wp * kk * dt; wr -= wr * kk * dt
                wy += (2.27 * (sL - sR) - 0.6 * kk * wy + 0.05 * rho * br) * dt

                if world < 3:      # wheels: four suspension springs on flat ground
                    vy0 = vy
                    ng = 0
                    if hgt < 2.2:
                        pa = ra = 0.0
                        for j in range(4):
                            ex = SX[j] * 0.95; ez = SZ[j] * 1.2
                            d = -(hgt + ex * ry + ez * fy)
                            if d > 0:
                                ng += 1
                                fw = min(90.0, max(0.0, 26.0 * min(d, 0.5) - (4.0 if vy < 0 else 7.0) * vy))
                                vy += fw * dt
                                ox_ = ex * rx + ez * fx; oz_ = ex * rz + ez * fz
                                pa -= (-oz_ * rx + ox_ * rz) * fw / 1.5
                                ra -= (-oz_ * fx + ox_ * fz) * fw / 0.9
                        wp += pa * dt; wr += ra * dt
                        if hgt + uy * 1.15 < 0 and inv <= 0.0: boom = True
                    if ng:
                        if (vy0 < -12.0 or uy < 0.6) and inv <= 0.0: boom = True      # too fast or too tilted = crash
                        gr = ng * 0.25
                        kk = min(1.0, 7.0 * gr * dt)
                        vx -= hzn * vrt * kk + hxn * vf * 0.12 * gr * dt
                        vz += hxn * vrt * kk - hzn * vf * 0.12 * gr * dt
                        if fwd > 0:
                            vx += hxn * 13.0 * gr * dt; vz += hzn * 13.0 * gr * dt
                        elif fwd < 0:                  # DOWN: brake, then reverse
                            dec = min(vf - 1.0, 20.0 * gr * dt) if vf > 1.0 else -8.0 * gr * dt
                            vx -= hxn * dec; vz -= hzn * dec
                        wy += (yin * 1.6 * vf / (abs(vf) + 5.0) - wy) * min(1.0, 8.0 * gr * dt)
                        kk = min(1.0, 3.0 * gr * dt)
                        wp -= wp * kk; wr -= wr * kk

                fx, fy, fz, ux, uy, uz = rot(fx, fy, fz, ux, uy, uz, wp * dt)
                ux, uy, uz, rx, ry, rz = rot(ux, uy, uz, rx, ry, rz, wr * dt)
                fx, fy, fz, rx, ry, rz = rot(fx, fy, fz, rx, ry, rz, wy * dt)
                n = 1.0 / sqrt(fx * fx + fy * fy + fz * fz)
                fx *= n; fy *= n; fz *= n
                rx = uy * fz - uz * fy; ry = uz * fx - ux * fz; rz = ux * fy - uy * fx
                n = 1.0 / sqrt(rx * rx + ry * ry + rz * rz)
                rx *= n; ry *= n; rz *= n
                ux = fy * rz - fz * ry; uy = fz * rx - fx * rz; uz = fx * ry - fy * rx
                px += vx * dt; py += vy * dt; pz += vz * dt
                if bd and py < bd[2] - 0.8:          # skyscraper walls: a slow touch turns the suction on, a fast one is a crash
                    ex_ = px - bd[0]; ez_ = pz - bd[1]
                    dxm = bd[3] + 1.2 - abs(ex_); dzm = bd[4] + 1.2 - abs(ez_)
                    if dxm > 0.0 and dzm > 0.0:
                        if dxm < dzm: q = 0 if ex_ > 0 else 1; pushd = dxm
                        else: q = 2 if ez_ > 0 else 3; pushd = dzm
                        nx_ = FNX[q]; nz_ = FNZ[q]
                        px += nx_ * pushd; pz += nz_ * pushd
                        vn = -(vx * nx_ + vz * nz_)
                        if vn > 0.0:
                            if vn > 20.0 and inv <= 0.0: boom = True
                            elif kA or vn < 0.5:                 # jets on / just brushing: bounce off and spin a little
                                vx += nx_ * vn * 1.3; vz += nz_ * vn * 1.3; wy += (rnd() - 0.5) * vn * 0.2
                            else:
                                wl = 1; fc = q; bx = bd[0]; bz = bd[1]; hw_ = bd[3]; hd_ = bd[4]; bh = bd[2]
                                vx += nx_ * vn; vz += nz_ * vn; ng = 0; wp = wr = wy = 0.0
                                msg = "SUCTION"; mt = 0.8; beep(500, 50)
            if lv > 0.0 and not wl:
                lv -= dt; tux = 0.0; tuy = 1.0; tuz = 0.0; tfx = lfx; tfy = 0.0; tfz = lfz
            if wl or lv > 0.0:                         # swing the car onto the wall / back onto its wheels
                kk = min(1.0, 10.0 * dt)
                ux += (tux - ux) * kk; uy += (tuy - uy) * kk; uz += (tuz - uz) * kk
                n = 1.0 / sqrt(ux * ux + uy * uy + uz * uz)
                ux *= n; uy *= n; uz *= n
                fx += (tfx - fx) * kk; fy += (tfy - fy) * kk; fz += (tfz - fz) * kk
                n = fx * ux + fy * uy + fz * uz
                fx -= ux * n; fy -= uy * n; fz -= uz * n
                n = sqrt(fx * fx + fy * fy + fz * fz)
                if n < 0.1:
                    fx = -uz; fy = 0.0; fz = ux; n = sqrt(fx * fx + fz * fz)
                    if n < 0.01: fx = 1.0; n = 1.0
                n = 1.0 / n
                fx *= n; fy *= n; fz *= n
                rx = uy * fz - uz * fy; ry = uz * fx - ux * fz; rz = ux * fy - uy * fx

            # compressed air tank, automatic refill (fast when parked)
            tank = min(100.0, max(0.0, tank + (10.0 + (14.0 if ng >= 3 or wl else 0.0) - 5.5 * st - 3.0 * (sL + sR) - (28.0 if bon else 0.0)) * dt))

            if boom:
                crash_t = 1.5; flash = 1; mt = 0.0
                kx = px; ky = py; kz = pz
                beep(110, 300)
                for i in range(NS):
                    a = rnd() * 6.283; m = 6.0 + rnd() * 14.0
                    spawn(3, px, py + 0.8, pz, vx * 0.5 + cos(a) * m, 4.0 + (rnd() * 2.0 - 0.4) * m * 0.7, vz * 0.5 + sin(a) * m, 0.5 + rnd() * 0.4)
                vx = vy = vz = 0.0
                wp = (rnd() - 0.5) * 9.0; wr = (rnd() - 0.5) * 9.0
                gnd = bon = False; wl = 0; lv = 0.0
                ng = 0; sL = sR = air = 0.0
                T[0] = T[1] = T[2] = T[3] = 0.0
                if mode: tleft -= 6.0
            else:
                if world < 3:
                    if ng > 0 and not gnd and air > 1.2:
                        pts = int(air * 6)
                        if vy0 < -8.0:
                            pts = 0; msg = "HARD LAND"; shk = 8; beep(200, 120)
                        else:
                            if vy0 > -4.0: pts += 25; msg = "SMOOTH +"
                            else: msg = "LAND +"
                            beep(900, 40)
                            if mode == 2 and abs(px - RG[0]) < 5.0 and abs(pz - RG[2]) < 5.0 and abs(py - RG[1]) < 2.5:
                                pts += 150; tleft = min(60.0, tleft + 15.0); msg = "PAD +"; newring(); beep(1200, 90)
                            msg += str(pts)
                        score += pts; mt = 0.7
                    gnd = ng > 0 or wl
                air = 0.0 if gnd else air + dt
                if gnd: acc = 0.0
                else:
                    acc += wp * dt
                    if acc > 5.8 or acc < -5.8:
                        acc = 0.0; score += 150; msg = "FLIP +150"; mt = 0.7; beep(1400, 60)
                # jet exhaust: every active jet, steering puffs, booster flame, wheel dust
                for j in range(4):
                    if T[j] > 0.05 and ((j + frame) & 1) == 0:
                        pw = 9.0 + 12.0 * T[j]
                        spawn(2, px + rx * SX[j] * 0.9 + fx * SZ[j] * 1.2 + ux * 0.2, py + ry * SX[j] * 0.9 + fy * SZ[j] * 1.2 + uy * 0.2,
                              pz + rz * SX[j] * 0.9 + fz * SZ[j] * 1.2 + uz * 0.2, vx - ux * pw + (rnd() - .5) * 4,
                              vy - uy * pw + (rnd() - .5) * 4, vz - uz * pw + (rnd() - .5) * 4, 0.35 + rnd() * 0.25)
                if (sL > 0.1 or sR > 0.1) and (frame & 1):
                    sd = -1.0 if sL > 0.1 else 1.0
                    spawn(2, px + rx * 1.05 * sd + fx * 1.25 + ux * 0.35, py + ry * 1.05 * sd + fy * 1.25 + uy * 0.35,
                          pz + rz * 1.05 * sd + fz * 1.25 + uz * 0.35, vx + rx * 14.0 * sd, vy + ry * 14.0 * sd, vz + rz * 14.0 * sd, 0.3)
                if bon:
                    spawn(2, px - fx * 2.2 + ux * 0.45, py - fy * 2.2 + uy * 0.45, pz - fz * 2.2 + uz * 0.45,
                          vx - fx * 30.0 + (rnd() - .5) * 5, vy - fy * 30.0 + (rnd() - .5) * 5, vz - fz * 30.0 + (rnd() - .5) * 5, 0.4 + rnd() * 0.3)
                if gnd and sp > 5.0 and (frame & 1) and not wl:
                    sd = 1.0 if rnd() < 0.5 else -1.0
                    spawn(3, px + rx * sd - fx * 1.15, 0.1, pz + rz * sd - fz * 1.15, vx * 0.3 + (rnd() - .5) * 3, 2.0 + rnd() * 3,
                          vz * 0.3 + (rnd() - .5) * 3, 0.5 + rnd() * 0.5)
                elif wl and sp > 3.0 and (frame & 1):          # sparks and dust off the suction wheels
                    sd = 1.0 if rnd() < 0.5 else -1.0
                    spawn(3, px + rx * sd - fx * 1.15, py + ry * sd - fy * 1.15, pz + rz * sd - fz * 1.15, ux * (1.0 + rnd() * 2.0) + (rnd() - .5) * 2,
                          (rnd() - .5) * 2 + 1.0, uz * (1.0 + rnd() * 2.0) + (rnd() - .5) * 2, 0.5 + rnd() * 0.4)
                if mode:
                    since += dt; tleft -= dt
                    dx = px - RG[0]; dy = py + 0.6 - RG[1]; dz = pz - RG[2]
                    s_ = dx * RG[3] + dz * RG[4]
                    if mode == 1 and rsp != 0.0 and rsp * s_ <= 0:
                        ax_ = dx - RG[3] * s_; az_ = dz - RG[4] * s_
                        if ax_ * ax_ + dy * dy + az_ * az_ < 100.0:
                            combo = combo + 1 if since < 9.0 else 0
                            pts = 100 + 25 * min(combo, 8)
                            score += pts; since = 0.0
                            tleft = min(45.0, tleft + 8.0)
                            msg = "RING +" + str(pts); mt = 0.6
                            beep(1000 + 80 * min(combo, 8), 70)
                            newring()
                            s_ = 0.0
                    rsp = s_
                    if tleft <= 0: return gameover(score)

        # camera follows the heading, not the roll/pitch of the car
        kk = min(1.0, dt * 5.0)
        hn = sqrt(fx * fx + fz * fz)
        if wl:                                  # on a wall the camera looks straight at it
            chx += (-FNX[fc] - chx) * kk; chz += (-FNZ[fc] - chz) * kk
        elif hn > 0.15 and crash_t <= 0:
            chx += (fx / hn - chx) * kk; chz += (fz / hn - chz) * kk
        n = 1.0 / sqrt(chx * chx + chz * chz)
        chx *= n; chz *= n
        tc_, dist = ((0.20, 9.0), (0.30, 15.0), (-0.2, 8.0))[camm]
        if crash_t > 0: dist += (3.3 - dist) * min(1.0, (1.5 - crash_t) * 2.4)       # the camera glides in on the wreck
        ct_ = cos(tc_); st_ = sin(tc_)
        cfx = chx * ct_; cfy = -st_; cfz = chz * ct_
        crx = chz; crz = -chx
        cux = chx * st_; cuy = ct_; cuz = chz * st_
        ccx = px - cfx * dist; ccy = max(py + 0.8 - cfy * dist, 1.0 if world < 3 else -9999.0); ccz = pz - cfz * dist
        yh = int(CY - FX * st_ / ct_)       # horizon row
        ox = oy = 0
        if shk > 0 and crash_t <= 0:
            shk -= 1
            ox = int(rnd() * 3) - 1; oy = int(rnd() * 3) - 1
        elif bon and crash_t <= 0 and (frame & 3) == 0: oy = 1      # booster: just a tiny 1-pixel tremble

        # ---------- render ----------
        if flash > 0:
            flash -= 1
            D.fill(1); D.update()
            continue
        D.fill(0)
        agl = py
        if world < 3 and 0 <= yh + oy < 40: dl(0, yh + oy, 71, yh + oy, 1)
        if world > 1:
            for sx_, sy_, sz_ in STAR:
                zv = sx_ * cfx + sy_ * cfy + sz_ * cfz
                if zv > 0.15 and (world == 3 or sy_ > 0.02):
                    s = FX / zv
                    xs = int(CX + ox + (sx_ * crx + sz_ * crz) * s); ys = int(CY + oy - (sx_ * cux + sy_ * cuy + sz_ * cuz) * s)
                    if 0 <= xs < 72 and 0 <= ys < 40: dp(xs, ys, 1)
        if world == 0:
            xc, yc, zc = cam(ccx + 45.0, ccy + 38.0, ccz + 81.0)
            if zc > 0.2:
                xs = int(CX + ox + xc * FX / zc); ys = int(CY + oy - yc * FX / zc)
                if 2 < xs < 69 and 2 < ys < 38:
                    dp(xs, ys, 1); dp(xs + 1, ys, 1); dp(xs - 1, ys, 1); dp(xs, ys + 1, 1); dp(xs, ys - 1, 1)
        if world < 3:      # ground grid (or speckles), towers, road
            Sg = 10.0 if agl < 12 else (20.0 if agl < 40 else (40.0 if agl < 110 else 0.0))
            if Sg and CFG[7] and not wl: grid(Sg, 5 - lod)
            elif Sg and not wl:
                ci = floor((ccx + cfx * Sg * 2.0) / Sg); cj_ = floor((ccz + cfz * Sg * 2.0) / Sg)
                for i in range(ci - 2, ci + 2):
                    for j in range(cj_ - 2, cj_ + 2):
                        a = (i * 1103 + j * 2713 + 11) & 1023
                        xs = (i + a * 0.000977) * Sg - ccx; zs = (j + ((a * 37 + i) & 1023) * 0.000977) * Sg - ccz
                        zv = xs * cfx - ccy * cfy + zs * cfz
                        if zv > 0.5:
                            xi = int(CX + ox + (xs * crx + zs * crz) * FX / zv); yi = int(CY + oy - (xs * cux - ccy * cuy + zs * cuz) * FX / zv)
                            if 0 <= xi < 72 and 0 <= yi < 40: dp(xi, yi, 1)
            ci = floor((ccx + cfx * 60.0) / 60.0); cj_ = floor((ccz + cfz * 60.0) / 60.0)
            for i in range(ci - 1, ci + 2):
                for j in range(cj_ - 1, cj_ + 2):
                    a = pyl(i, j)
                    if a: bld(a)
            if wl:       # floor lines on the wall we are driving on (they show how fast you climb)
                hl = hd_ if fc < 2 else hw_
                v0 = bx + FNX[fc] * hw_ + FNZ[fc] * hl - ccx; w0 = bz + FNZ[fc] * hd_ - FNX[fc] * hl - ccz
                v1 = bx + FNX[fc] * hw_ - FNZ[fc] * hl - ccx; w1 = bz + FNZ[fc] * hd_ + FNX[fc] * hl - ccz
                yy = -ccy
                a0 = v0 * crx + w0 * crz; b0 = v0 * cux + yy * cuy + w0 * cuz; d0 = v0 * cfx + yy * cfy + w0 * cfz
                a1 = v1 * crx + w1 * crz; b1 = v1 * cux + yy * cuy + w1 * cuz; d1 = v1 * cfx + yy * cfy + w1 * cfz
                for j in range(-2, 4):
                    y = (floor(py / 6.0) + j) * 6.0
                    if 0.0 < y < bh: clip(a0, b0 + y * cuy, d0 + y * cfy, a1, b1 + y * cuy, d1 + y * cfy)
                if CFG[7]:
                    for t in (0.25, 0.5, 0.75):
                        v0 = a0 + (a1 - a0) * t; v1 = b0 + (b1 - b0) * t; v2 = d0 + (d1 - d0) * t
                        clip(v0, v1, v2, v0, v1 + bh * cuy, v2 + bh * cfy)
            if agl < 70:
                seg(-5.8, 0.0, pz - 8.0, -5.8, 0.0, pz + 120.0)
                seg(5.8, 0.0, pz - 8.0, 5.8, 0.0, pz + 120.0)
                z0 = floor(pz / 16.0) * 16.0
                if not CFG[7]:
                    for q in range(4 - lod * 2): seg(0.0, 0.0, z0 + q * 16.0, 0.0, 0.0, z0 + q * 16.0 + 6.0)
        if mode:
            if mode == 1:
                a = None
                for q in range(9):
                    ang = q * 0.7854
                    nb = pr(RG[0] + RG[4] * cos(ang) * 9.0, RG[1] + sin(ang) * 9.0, RG[2] - RG[3] * cos(ang) * 9.0)
                    if a and nb: dl(a[0], a[1], nb[0], nb[1], 1)
                    a = nb
            else:       # landing pad: square on the ground + a beacon pole
                x = RG[0]; z = RG[2]; y = RG[1]
                seg(x - 5.0, y, z - 5.0, x + 5.0, y, z - 5.0); seg(x + 5.0, y, z - 5.0, x + 5.0, y, z + 5.0)
                seg(x + 5.0, y, z + 5.0, x - 5.0, y, z + 5.0); seg(x - 5.0, y, z + 5.0, x - 5.0, y, z - 5.0)
                seg(x, y, z, x, y + 40.0, z)
            xc, yc, zc = cam(RG[0], RG[1], RG[2])
            p = pr(RG[0], RG[1], RG[2])
            if not (p and 4 < p[0] < 67 and 4 < p[1] < 35):      # arrow at the screen edge points to the ring
                m = sqrt(xc * xc + yc * yc) + 0.001
                s_ = 1.0 if zc > 0.5 else -1.0
                xs = int(CX + s_ * xc / m * 30.0); ys = int(CY - s_ * yc / m * 15.0)
                dl(xs - 2, ys, xs + 2, ys, 1); dl(xs, ys - 2, xs, ys + 2, 1)
            rdist = int(sqrt(xc * xc + yc * yc + zc * zc))

        # air particles: ambient air pushed aside by the car
        if rho > 0.05 or world == 3:
            for i in range(0, (NA if lod == 0 else NA * 2 // 3) * 3, 3):
                x = A[i] - px; y = A[i + 1] - py; z = A[i + 2] - pz
                d2 = x * x + y * y + z * z
                if d2 > 1500.0:
                    al = rnd() * 30.0 - (6.0 if sp > 15 else 15.0); sd = (rnd() - 0.5) * 26.0; vt = (rnd() - 0.5) * 14.0 + 2.0
                    A[i] = px + fx * al + rx * sd + ux * vt; A[i + 1] = py + fy * al + ry * sd + uy * vt; A[i + 2] = pz + fz * al + rz * sd + uz * vt
                    continue
                if d2 < 30.0:
                    f2 = (sa + 6.0) * 2.2 * dt / ((d2 + 1.0) * (sqrt(d2) + 0.3))
                    A[i] += x * f2; A[i + 1] += y * f2; A[i + 2] += z * f2
                x = A[i] - ccx; y = A[i + 1] - ccy; z = A[i + 2] - ccz
                zv = x * cfx + y * cfy + z * cfz
                if 0.5 < zv < 90.0:
                    xs = int(CX + ox + (x * crx + z * crz) * FX / zv); ys = int(CY + oy - (x * cux + y * cuy + z * cuz) * FX / zv)
                    if 0 <= xs < 72 and 0 <= ys < 40:
                        if sa > 40.0 and zv < 60.0:
                            q = min(0.5, sa * 0.0025)
                            dl(xs, ys, xs + int((xs - CX) * q), ys + int((ys - CY) * q), 1)
                        else:
                            dp(xs, ys, 1)
        # jet exhaust, dust and debris
        for i in range(NS if lod == 0 else NS * 2 // 3):
            lf = SL[i]
            if lf <= 0: continue
            SL[i] = lf - pd
            j = i * 6
            a = S[j + 3]; b = S[j + 4]; c_ = S[j + 5]
            if SK[i] == 2:
                kk = 1.0 - pd * 1.2
                a *= kk; b *= kk; c_ *= kk
                if world < 3 and S[j + 1] < 0.0:       # blast hits the ground: dust splash
                    S[j + 1] = 0.05; SK[i] = 3; SL[i] = 0.5 + rnd() * 0.5
                    a = (rnd() - .5) * 16.0; c_ = (rnd() - .5) * 16.0; b = 1.5 + rnd() * 4.0
            else:
                kk = 1.0 - pd * 0.8
                a *= kk; c_ *= kk
                b = b * kk - g * pd
                if world < 3 and S[j + 1] < 0.0:
                    S[j + 1] = 0.0; b = -b * 0.4; a *= 0.7; c_ *= 0.7
            S[j + 3] = a; S[j + 4] = b; S[j + 5] = c_
            S[j] += a * pd; S[j + 1] += b * pd; S[j + 2] += c_ * pd
            x = S[j] - ccx; y = S[j + 1] - ccy; z = S[j + 2] - ccz
            zv = x * cfx + y * cfy + z * cfz
            if 0.5 < zv < 90.0:
                xs = int(CX + ox + (x * crx + z * crz) * FX / zv); ys = int(CY + oy - (x * cux + y * cuy + z * cuz) * FX / zv)
                if 0 <= xs < 72 and 0 <= ys < 40:
                    dp(xs, ys, 1)
                    if zv < 4.0 or SK[i] == 2:
                        dp(xs + 1, ys, 1); dp(xs, ys + 1, 1)
        # car
        dx, dy, dz = cam(px, py, pz)
        R = (rx * crx + rz * crz, rx * cux + ry * cuy + rz * cuz, rx * cfx + ry * cfy + rz * cfz)
        U = (ux * crx + uz * crz, ux * cux + uy * cuy + uz * cuz, ux * cfx + uy * cfy + uz * cfz)
        F = (fx * crx + fz * crz, fx * cux + fy * cuy + fz * cuz, fx * cfx + fy * cfy + fz * cfz)
        if crash_t <= 0:
            drawcar(dx, dy, dz, R, U, F)
            jets(dx, dy, dz, R, U, F, T, sL, sR, bon)
            if world < 3 and not wl:
                p = pr(px + rx * 1.3, fh, pz + rz * 1.3); q = pr(px - rx * 1.3, fh, pz - rz * 1.3)     # shadow bar
                if p and q: dl(p[0], p[1], q[0], q[1], 1)
                if agl - fh > 3.0:                                                                   # tether to the floor
                    p = pr(px, fh, pz)
                    if p: dl(p[0], p[1], int(CX + ox + dx * FX / dz), int(CY + oy - dy * FX / dz), 1)
        else:           # slow-motion wreck: the car breaks up, a fireball grows, the camera is right on it
            drawcar(dx, dy, dz, R, U, F, min(0.8, (1.5 - crash_t) * 0.8))
            if dz > 0.5 and crash_t > 0.5:
                rad = (1.5 - crash_t) * 3.2 * FX / dz
                for q in range(12):
                    dp(int(CX + dx * FX / dz + cos(q * 0.5236) * rad), int(CY - dy * FX / dz + sin(q * 0.5236) * rad * 0.7), 1)
                    dp(int(CX + dx * FX / dz + cos(q * 0.5236 + 0.26) * rad * 0.6), int(CY - dy * FX / dz + sin(q * 0.5236 + 0.26) * rad * 0.42), 1)
            if (frame & 4) and crash_t > 0.2: tx("CRASH", 21, 24, 1)
        # HUD
        tx(str(int(sp * 3.6)), 0, 0, 1)
        al = str(int(agl)) + "m"
        tx(al, 72 - 6 * len(al), 0, 1)
        if mt > 0: tx(msg, (72 - 6 * len(msg)) // 2, 10, 1)
        elif vy < -9.5 and agl < 45.0 and not gnd and (frame & 2): tx("PULL UP", 15, 10, 1)       # about to crash
        elif wl: tx("SUCTION", 15, 10, 1)
        elif tank < 15.0 and (frame & 4): tx("LOW AIR", 15, 10, 1)
        if not gnd and crash_t <= 0:                 # sink-rate gauge; the tick is the crash limit
            dl(71, 20, 71, 20 - int(max(-19.0, min(19.0, vy * 0.9))), 1); dp(70, 31, 1)
        tx(str(score), 0, 31, 1)
        if mode:
            ts = "T" + str(int(tleft)); tx(ts, 72 - 6 * len(ts), 31, 1)
            ds = str(rdist) + "m"; tx(ds, 36 - 3 * len(ds), 31, 1)
        if CFG[5]: tx(str(int(1.0 / dtm)), 30, 0, 1)
        if tank > 1.4: dl(0, 39, int(tank * 0.72), 39, 1)
        D.update()


while True:
    title()
    while play(): pass
