# SINGULARITY - throw real 3D shapes into a black hole you can tune (Thumby)
#
# What's new in this version
#
#  SHAPES  (B cycles them, a spinning preview shows while you aim)
#    ROCK     wireframe cube
#    CRYSTAL  octahedron
#    PLANET   ringed planet (heavy - big gravitational slingshots)
#    NEEDLE   long thin spear (the most dramatic to watch get stretched)
#    STAR     spinning 5-pointed star with a twinkling core. The heaviest
#             thing you can throw: huge pull on everything around it, sheds
#             lots of debris as it is torn apart, and makes the hole grow most.
#
#  PHYSICS
#    * TIDAL STRETCHING: as a shape falls in it is stretched along the line to
#      the hole and squeezed sideways (spaghettification). Past the Roche
#      limit it glows (bold lines), shrinks and sheds debris into the disc.
#    * TRUE GRAVITATIONAL LENSING: anything BEHIND the hole is bent around it
#      (an Einstein ring). The far side of the disc forms the big arc over the
#      top, and shapes / stars sweeping behind the hole trace the ring.
#    * TIME DILATION + REDSHIFT: things near the horizon spin slower, fade
#      and flicker out as they are swallowed instead of just vanishing.
#    * FRAME DRAGGING (Lense-Thirring): the spinning hole twists the space
#      around it, so tilted orbits precess near the hole.
#    * GR precession + innermost stable orbit (orbits make rosettes, then plunge)
#    * MUTUAL GRAVITY: thrown shapes attract each other. If two collide they
#      MERGE (momentum conserved, mass adds up, size grows).
#    * RAM-PRESSURE DRAG: shapes plunging through the gas disc lose speed, so
#      they can get captured into orbit.
#    * Adaptive sub-stepping: shapes near the hole are integrated 2x finer.
#    * GRAVITATIONAL WAVES: swallows and mergers send ripples through space.
#    * Heavier hole = stronger gravity, bigger horizon, bigger lens.
#
#  BLACK HOLE MENU  (HOLD B for half a second)
#    UP/DOWN picks a setting, LEFT/RIGHT changes it (hold to repeat), the
#    scene keeps running behind the menu so you see the change live.
#    B or A closes it.
#      GRAVITY  pull strength            SIZE   starting mass / horizon size
#      SPIN     frame dragging           DISC   accretion disc radius
#      GAS      drag in the disc         JETS   jet power (0 = off)
#      LENS     light bending            GROW   how much it grows when fed
#      STARS    number of orbiting stars RESET  (A) back to defaults + fresh scene
#
#  CONTROLS
#    LEFT/RIGHT/UP/DOWN : spin / tilt camera
#    HOLD A             : aim (d-pad moves the reticle) and charge
#    RELEASE A          : throw   (weak charge = captured orbit, strong = flyby)
#    TAP B              : change shape (ROCK > CRYSTAL > PLANET > NEEDLE > STAR)
#    HOLD B             : black hole menu
#
# Install: copy to /Games/Singularity/Singularity.py on the Thumby.
# The game measures its own speed and automatically drops orbiting stars if
# it ever runs slow, so it should keep a steady frame rate.

import math
import random
import time
import thumby

thumby.display.setFPS(30)
disp = thumby.display

try:
    _tick = time.ticks_ms
    _diff = time.ticks_diff
except AttributeError:
    def _tick():
        return int(time.time() * 1000)

    def _diff(a, b):
        return a - b

# ---------------- tuning ----------------
N = 14            # max orbiting stars / debris (the STARS setting picks how many)
NJ = 8            # jet particles
NT = 3            # max shapes in flight
RN = 3            # max gravitational-wave ripples
GM = 0.0006       # black hole gravity
KGR = 0.02        # relativistic precession strength (0 = plain Newton)
KLT = 0.00015     # frame dragging strength
EPS = 0.004       # gravity softening
DT = 0.5          # physics step (2 per frame -> 1 time unit per frame)
RT = 0.40         # tidal (Roche) radius
HOR = 0.1414      # horizon radius
TLR = 5           # shape trail length
FOCAL = 56.0
CAM0 = 3.5
CX0 = 36
CY0 = 20
TWO_PI = 6.2831853

# ---------------- shapes ----------------
CUBE_V = ((-.8, -.8, -.8), (.8, -.8, -.8), (.8, .8, -.8), (-.8, .8, -.8),
          (-.8, -.8, .8), (.8, -.8, .8), (.8, .8, .8), (-.8, .8, .8))
CUBE_E = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
          (0, 4), (1, 5), (2, 6), (3, 7))

OCT_V = ((1.15, 0, 0), (-1.15, 0, 0), (0, 1.15, 0), (0, -1.15, 0),
         (0, 0, 1.15), (0, 0, -1.15))
OCT_E = ((0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5),
         (2, 4), (2, 5), (3, 4), (3, 5))

_pv = [(.7, 0, 0), (-.7, 0, 0), (0, .7, 0), (0, -.7, 0), (0, 0, .7), (0, 0, -.7)]
_pe = list(OCT_E)
for _k in range(6):
    _a = _k * TWO_PI / 6
    _pv.append((1.7 * math.cos(_a), 0.0, 1.7 * math.sin(_a)))
    _pe.append((6 + _k, 6 + (_k + 1) % 6))
PLN_V = tuple(_pv)
PLN_E = tuple(_pe)

NDL_V = ((0, 0, 2.2), (0, 0, -2.2), (.55, 0, 0), (-.55, 0, 0), (0, .55, 0), (0, -.55, 0))
NDL_E = ((0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5),
         (2, 4), (4, 3), (3, 5), (5, 2))

# 5-pointed star: 10 rim points (even = sharp tips, odd = inner notches) in the
# x/y plane, plus a raised point front and back so it reads as a solid 3D star.
# Tip 0 points up on the screen (screen y grows downwards).
_sv = []
_se = []
for _k in range(10):
    _a = _k * TWO_PI / 10 - 1.5707963
    if (_k & 1) == 0:
        _r = 1.3
    else:
        _r = 0.55
    _sv.append((_r * math.cos(_a), _r * math.sin(_a), 0.0))
    _se.append((_k, (_k + 1) % 10))
_sv.append((0.0, 0.0, 0.5))
_sv.append((0.0, 0.0, -0.5))
for _k in range(0, 10, 2):
    _se.append((10, _k))
    _se.append((11, _k))
STR_V = tuple(_sv)
STR_E = tuple(_se)

SHAPES = ((CUBE_V, CUBE_E), (OCT_V, OCT_E), (PLN_V, PLN_E), (NDL_V, NDL_E),
          (STR_V, STR_E))
NSH = 5           # number of shapes
STAR_T = 4        # index of the star shape

T_NAME = ("ROCK", "CRYSTAL", "PLANET", "NEEDLE", "STAR")
T_SZ = (0.21, 0.19, 0.17, 0.15, 0.19)                  # world size of one shape unit
T_GM = (0.00014, 0.00022, 0.0007, 0.00008, 0.0009)     # gravity of the shape
T_MASS = (8, 8, 14, 6, 18)                             # debris pieces it can shed
T_GROW = (0.08, 0.10, 0.22, 0.05, 0.28)                # how much the hole grows when it eats it
T_SPD = (0.026, 0.030, 0.022, 0.034, 0.024)            # throw speed
T_WA = (0.13, 0.10, 0.07, 0.16, 0.09)                  # spin rate
T_WB = (0.17, 0.12, 0.0, 0.21, 0.0)                    # tumble rate

# ---------------- stars / debris ----------------
PX = [0.0] * N
PY = [0.0] * N
PZ = [0.0] * N
VX = [0.0] * N
VY = [0.0] * N
VZ = [0.0] * N
PRX = [-999] * N
PRY = [-999] * N
HOT = [False] * N


# live black-hole settings (changed from the menu, see apply_settings)
gravm = 1.0       # gravity multiplier
gfloor = 0.0      # extra starting mass
spinm = 1.0       # frame dragging multiplier
discm = 1.0       # accretion disc size multiplier
gasm = 1.0        # gas drag multiplier
jetm = 1.0        # jet power multiplier
lensm = 1.0       # lensing multiplier
growm = 1.0       # growth-when-fed multiplier
star_cap = 8      # orbiting stars wanted
DRAGS = 0.99978   # drag factors derived from gasm
DRAGYS = 0.99978 * 0.9994
ram = 0.992
gsc = 1.0


def spawn(i, rmin, rmax):
    r = random.uniform(rmin, rmax)
    a = random.uniform(0.0, TWO_PI)
    ca = math.cos(a)
    sa = math.sin(a)
    PX[i] = r * ca
    PZ[i] = r * sa
    PY[i] = random.uniform(-0.06, 0.06) * (0.4 + r)
    v = math.sqrt(GM * gravm * gsc / r) * random.uniform(0.84, 1.02)
    VX[i] = -sa * v
    VZ[i] = ca * v
    VY[i] = random.uniform(-0.002, 0.002)
    PRX[i] = -999


nact = 8
for i in range(nact):
    spawn(i, 0.5, 1.5)

# ---------------- thrown shapes ----------------
QON = [False] * NT
QX = [0.0] * NT
QY = [0.0] * NT
QZ = [0.0] * NT
QVX = [0.0] * NT
QVY = [0.0] * NT
QVZ = [0.0] * NT
QT = [0] * NT
QG = [0.0] * NT
QM = [1] * NT
QM0 = [1] * NT
QL = [0] * NT
QH = [0] * NT
QA = [0.0] * NT
QB = [0.0] * NT
QWA = [0.1] * NT
QWB = [0.1] * NT
QSZ = [1.0] * NT
QTX = [[-999] * TLR for _ in range(NT)]
QTY = [[-999] * TLR for _ in range(NT)]

# ---------------- gravitational-wave ripples ----------------
RPR = [-1.0] * RN
RPX = [0.0] * RN
RPY = [0.0] * RN
RPZ = [0.0] * RN

# ---------------- jets ----------------
JY = [random.uniform(0.0, 1.5) for _ in range(NJ)]
JA = [random.uniform(0.0, TWO_PI) for _ in range(NJ)]
JS = [1 if k & 1 else -1 for k in range(NJ)]

# ---------------- background stars ----------------
BX = []
BY = []
BZ = []
for _ in range(12):
    a = random.uniform(0.0, TWO_PI)
    b = random.uniform(-1.0, 1.0)
    r = math.sqrt(1.0 - b * b)
    BX.append(r * math.cos(a))
    BY.append(b)
    BZ.append(r * math.sin(a))


def make_ring(n):
    xs = []
    zs = []
    for k in range(n):
        a = k * TWO_PI / n
        xs.append(math.cos(a))
        zs.append(math.sin(a))
    return xs, zs


RINGS = []
for rad, n, spin in ((0.26, 22, 1.9), (0.38, 32, 1.3), (0.52, 44, 0.9), (0.68, 58, 0.6)):
    xs, zs = make_ring(n)
    RINGS.append((rad, n, spin, xs, zs))

# cached screen-space points of the disc (rebuilt only when the view changes).
# FL / NL[ring][phase] = list of (x, y) offsets to draw for that dash phase,
# so drawing the disc is just a plain loop of setPixel calls.
FL = [None] * 4     # far side (lensed over the hole)
NL = [None] * 4     # near side (in front of the hole)
SHR = []            # shadow rectangles (dy, half-width, height)
PHR = []            # photon ring points
RSP = tuple(r[2] * 3.0 for r in RINGS)   # dash speed of each ring
lc_p = -9.0
lc_c = -9.0
lc_g = -9.0
lc_f = -99

HC, HS = make_ring(24)   # photon ring (screen space)
RC, RS = make_ring(16)   # ripple ring (world space)
BURST_C = [math.cos(k * 0.7853982) for k in range(8)]
BURST_S = [math.sin(k * 0.7853982) for k in range(8)]

# ---------------- state ----------------
yaw = 0.0
pitch = 0.5
cam = CAM0
cx = CX0
cy = CY0
cyw = 1.0
syw = 0.0
cp = 1.0
sp = 0.0
E4 = 90.0          # (2 * Einstein radius in pixels)^2 / ... see lens()
gsc = 1.0

flash = 0
shake = 0
jet = 0.2
growth = 0.0
frame = 0
ring_a = 0.0
avg = 15.0
lite = False       # emergency low-detail mode (set automatically if slow)
BSX = [-999] * 12  # cached screen offsets of the background stars
BSY = [0] * 12
c10 = 0.0          # camera matrix entries (updated every frame)
c12 = 0.0
c20 = 0.0
c22 = 0.0

typ = 0
label_t = 0
aiming = False
charge = 0.0
ax = 0.0
ay = -4.0

# menu state
MENU = (("GRAVITY", 0, 10, 5), ("SIZE", 0, 10, 0), ("SPIN", 0, 10, 5),
        ("DISC", 0, 10, 5), ("GAS", 0, 10, 5), ("JETS", 0, 10, 5),
        ("LENS", 0, 10, 5), ("GROW", 0, 10, 5), ("STARS", 2, 14, 8),
        ("RESET", 0, 0, 0))
RESET_IDX = 9
LV = [m[3] for m in MENU]
menu_open = False
msel = 0
mrep = 0
bnow = False
bhold = 0
b_lock = False
a_lock = False


def c2w(xr, yr, zc):
    # camera space -> world space (inverse of the view transform)
    zr = zc * cp - yr * sp
    y = zc * sp + yr * cp
    x = xr * cyw - zr * syw
    z = xr * syw + zr * cyw
    return x, y, z


def lens(dx, dy, depth, e4):
    # Gravitational lensing of a point BEHIND the hole (screen offsets in px).
    # Primary image of a point source: d' = (d + sqrt(d^2 + 4E^2)) / 2
    d2 = dx * dx + dy * dy
    if d2 > 900.0:
        return dx, dy
    d = math.sqrt(d2) + 0.01
    k = (d + math.sqrt(d2 + e4)) / (2.0 * d)
    w = depth * 7.0
    if w < 1.0:
        k = 1.0 + (k - 1.0) * w
    return dx * k, dy * k


def feed(x):
    # the hole eats something: it grows (scaled by the GROW setting)
    global growth
    growth += x * growm
    if growth > 0.7:
        growth = 0.7


def apply_settings():
    global gravm, gfloor, spinm, discm, gasm, jetm, lensm, growm
    global star_cap, nact, lc_f, DRAGS, DRAGYS, ram
    gravm = 2.0 ** ((LV[0] - 5) * 0.25)     # 0.42x .. 2.4x
    gfloor = LV[1] * 0.07                    # up to +70% mass
    spinm = (LV[2] / 5.0) ** 2               # 0 .. 4x
    discm = 0.5 + LV[3] * 0.1                # 0.5x .. 1.5x
    gasm = (LV[4] / 5.0) ** 2                # 0 .. 4x
    jetm = LV[5] / 5.0
    lensm = LV[6] / 5.0
    growm = LV[7] / 5.0
    star_cap = LV[8]
    DRAGS = 1.0 - 0.00022 * gasm
    DRAGYS = DRAGS * (1.0 - 0.0006 * gasm)
    ram = 1.0 - 0.008 * gasm
    if nact > star_cap:
        nact = star_cap
    while nact < star_cap:
        spawn(nact, 1.1, 1.5)
        nact += 1
    lc_f = -99                               # re-project the disc


def change_setting(d):
    if msel == RESET_IDX:
        return
    v = LV[msel] + d
    if v < MENU[msel][1]:
        v = MENU[msel][1]
    if v > MENU[msel][2]:
        v = MENU[msel][2]
    if v != LV[msel]:
        LV[msel] = v
        apply_settings()


def reset_all():
    global growth, jet, flash, shake
    for i in range(len(MENU)):
        LV[i] = MENU[i][3]
    apply_settings()
    for k in range(NT):
        QON[k] = False
    for i in range(RN):
        RPR[i] = -1.0
    for i in range(nact):
        spawn(i, 0.5, 1.5)
    growth = 0.0
    jet = 0.2
    flash = 0
    shake = 0


def draw_menu():
    nm = MENU[msel][0]
    lo = MENU[msel][1]
    hi = MENU[msel][2]
    disp.drawFilledRectangle(0, 24, 72, 16, 0)
    disp.drawLine(0, 24, 71, 24, 1)
    for i in range(len(MENU)):
        tx = 4 + i * 7
        if i == msel:
            disp.drawFilledRectangle(tx - 1, 25, 3, 2, 1)
        else:
            disp.setPixel(tx, 25, 1)
    disp.drawText(nm, 3, 28, 1)
    if msel == RESET_IDX:
        disp.drawText("A:GO", 46, 28, 1)
    else:
        vs = str(LV[msel])
        disp.drawText(vs, 69 - 6 * len(vs), 28, 1)
        disp.drawRectangle(3, 36, 66, 3, 1)
        w = int(64 * (LV[msel] - lo) / (hi - lo))
        if w > 0:
            disp.drawFilledRectangle(4, 37, w, 1, 1)


def add_ripple(x, y, z):
    s = 0
    for i in range(RN):
        if RPR[i] < 0.0:
            s = i
            break
    RPR[s] = 0.15
    RPX[s] = x
    RPY[s] = y
    RPZ[s] = z


def throw():
    slot = 0
    best = -1
    for k in range(NT):
        if not QON[k]:
            slot = k
            break
        if QL[k] > best:
            best = QL[k]
            slot = k
    f0 = FOCAL / cam
    ox = 0.0
    oy = 0.42
    oz = 1.7 - cam
    dx = ax / f0 - ox
    dy = ay / f0 - oy
    dz = -oz
    d = math.sqrt(dx * dx + dy * dy + dz * dz)
    spd = T_SPD[typ] * (0.6 + 0.8 * charge) / d
    p = c2w(ox, oy, oz)
    v = c2w(dx * spd, dy * spd, dz * spd)
    QX[slot] = p[0]
    QY[slot] = p[1]
    QZ[slot] = p[2]
    QVX[slot] = v[0]
    QVY[slot] = v[1]
    QVZ[slot] = v[2]
    QT[slot] = typ
    QG[slot] = T_GM[typ]
    QM[slot] = T_MASS[typ]
    QM0[slot] = T_MASS[typ]
    QL[slot] = 0
    QH[slot] = 0
    QA[slot] = random.uniform(0.0, TWO_PI)
    if typ == 2:
        QB[slot] = 0.5                       # planet: ring tilted towards us
    elif typ == STAR_T:
        QB[slot] = random.uniform(-0.5, 0.5)  # star: spins like a coin, slight tilt
    else:
        QB[slot] = random.uniform(0.0, TWO_PI)
    QWA[slot] = T_WA[typ] * random.uniform(0.8, 1.2)
    QWB[slot] = T_WB[typ] * random.uniform(0.8, 1.2)
    QSZ[slot] = 1.0
    QON[slot] = True
    for j in range(TLR):
        QTX[slot][j] = -999
        QTY[slot][j] = -999


def shed(k):
    # tear a piece off shape k: recycle the outermost active star slot
    best = 0
    bd = -1.0
    for i in range(nact):
        d2 = PX[i] * PX[i] + PY[i] * PY[i] + PZ[i] * PZ[i]
        if d2 > bd:
            bd = d2
            best = i
    i = best
    PX[i] = QX[k] + random.uniform(-0.03, 0.03)
    PY[i] = QY[k] + random.uniform(-0.03, 0.03)
    PZ[i] = QZ[k] + random.uniform(-0.03, 0.03)
    VX[i] = QVX[k] * 0.95 + random.uniform(-0.006, 0.006)
    VY[i] = QVY[k] * 0.95 + random.uniform(-0.006, 0.006)
    VZ[i] = QVZ[k] * 0.95 + random.uniform(-0.006, 0.006)
    PRX[i] = -999


def build_rings():
    # The disc is circular, so its screen shape does not depend on the yaw.
    # Project it once, keep the pixel offsets, and only redo this when the
    # tilt / zoom / hole mass actually changes.
    global SHR, PHR
    for ri in range(4):
        rad, n, spin, xs, zs = RINGS[ri]
        R = rad * gsc * discm
        fl = [[], [], [], []]
        nl = [[], [], [], []]
        for k in range(n):
            xr = xs[k] * R
            zr = zs[k] * R
            f = FOCAL / (zr * cp + cam)
            px = xr * f
            py = -zr * sp * f
            far = zr > 0.0
            if far and px * px + py * py < 900.0:
                # far side of the disc is lensed up and over the hole
                px, py = lens(px, py, zr * cp, E4)
            x = int(px + 100.5) - 100
            y = int(py + 100.5) - 100
            if not (1 <= CX0 + x <= 70 and 1 <= CY0 + y <= 38):
                continue
            pt = (x, y)
            if far:
                dst = fl
            else:
                dst = nl
            if xr < 0.0:
                # approaching side (Doppler bright): visible in 3 of 4 dash phases
                q = (3 - k) & 3
                for p in range(4):
                    if p != q:
                        dst[p].append(pt)
            else:
                # receding side (dim): visible in 2 of 4 dash phases
                dst[(-k) & 3].append(pt)
                dst[(1 - k) & 3].append(pt)
        FL[ri] = fl
        NL[ri] = nl

    # round black shadow, merged into as few rectangles as possible
    sr = 0.62 * E0
    SHR = []
    prev = None
    for dy in range(-int(sr), int(sr) + 1):
        hw = int(math.sqrt(sr * sr - dy * dy) + 0.5)
        if prev is not None and prev[1] == hw:
            prev[2] += 1
        else:
            prev = [dy, hw, 1]
            SHR.append(prev)
    # thin bright photon ring around it
    pr = sr + 1.3
    PHR = []
    for k in range(24):
        PHR.append((int(HC[k] * pr + 100.5) - 100, int(HS[k] * pr + 100.5) - 100))


def draw_disc(far):
    if far:
        L = FL
    else:
        L = NL
    put = disp.setPixel
    for ri in range(4):
        for x, y in L[ri][int(ring_a * RSP[ri]) & 3]:
            put(cx + x, cy + y, 1)


def draw_throwable(k):
    t = QT[k]
    qx = QX[k]
    qy = QY[k]
    qz = QZ[k]
    r = math.sqrt(qx * qx + qy * qy + qz * qz) + 0.001

    # --- centre of the shape in camera space (also the trail anchor) ---
    xr0 = qx * cyw + qz * syw
    zr = qz * cyw - qx * syw
    yr0 = qy * cp - zr * sp
    zc0 = qy * sp + zr * cp
    zz = zc0 + cam
    h = (QH[k] + 1) % TLR
    QH[k] = h
    tx = QTX[k]
    ty = QTY[k]
    if zz < 0.5:
        tx[h] = -999
        return
    f = FOCAL / zz
    px = xr0 * f
    py = yr0 * f
    if zc0 > 0.0 and px * px + py * py < 900.0:
        px, py = lens(px, py, zc0, E4)
    sx = int(cx + px)
    sy = int(cy + py)
    tx[h] = sx
    ty[h] = sy

    # --- time dilation / redshift near the horizon ---
    tau2 = 1.0 - HOR * gsc / r
    if tau2 > 0.0:
        tau = math.sqrt(tau2)
    else:
        tau = 0.0
    QA[k] += QWA[k] * tau
    QB[k] += QWB[k] * tau

    # --- bold trail ---
    pxx = sx
    pyy = sy
    for j in range(1, TLR):
        idx = (h - j) % TLR
        bx = tx[idx]
        if bx < -500:
            break
        by = ty[idx]
        if abs(pxx - bx) + abs(pyy - by) < 14 and 0 <= pxx < 72 and 0 <= pyy < 39 and 0 <= bx < 72 and 0 <= by < 39:
            disp.drawLine(pxx, pyy, bx, by, 1)
            if j < 3:
                disp.drawLine(pxx, pyy + 1, bx, by + 1, 1)
        pxx = bx
        pyy = by

    # fade out (flicker) as it redshifts into the horizon
    if tau < 0.6 and (frame & 3) >= 1 + int(tau * 5.0):
        return

    # --- tidal stretch: long along the radial direction, squeezed across ---
    ux = qx / r
    uy = qy / r
    uz = qz / r
    q = RT * gsc / r
    S = 1.0 + 1.3 * q * q * q
    if S > 9.0:
        S = 9.0
    P = 1.0 / math.sqrt(S)
    b = S - P
    sz = T_SZ[t] * QSZ[k] * (0.4 + 0.6 * QM[k] / QM0[k])

    # One 3x3 matrix per shape:  L = Camera * (size * Stretch * Tumble).
    # Then every vertex costs just 9 multiplies.
    ca = math.cos(QA[k])
    sa = math.sin(QA[k])
    cb = math.cos(QB[k])
    sb = math.sin(QB[k])
    r00 = ca
    r02 = sa
    r10 = sb * sa
    r11 = cb
    r12 = -sb * ca
    r20 = -cb * sa
    r21 = sb
    r22 = cb * ca
    w0 = ux * r00 + uy * r10 + uz * r20
    w1 = uy * r11 + uz * r21
    w2 = ux * r02 + uy * r12 + uz * r22
    s_p = sz * P
    a_b = sz * b * ux
    b_b = sz * b * uy
    c_b = sz * b * uz
    m00 = s_p * r00 + a_b * w0
    m01 = a_b * w1
    m02 = s_p * r02 + a_b * w2
    m10 = s_p * r10 + b_b * w0
    m11 = s_p * r11 + b_b * w1
    m12 = s_p * r12 + b_b * w2
    m20 = s_p * r20 + c_b * w0
    m21 = s_p * r21 + c_b * w1
    m22 = s_p * r22 + c_b * w2
    l00 = cyw * m00 + syw * m20
    l01 = cyw * m01 + syw * m21
    l02 = cyw * m02 + syw * m22
    l10 = c10 * m00 + cp * m10 + c12 * m20
    l11 = c10 * m01 + cp * m11 + c12 * m21
    l12 = c10 * m02 + cp * m12 + c12 * m22
    l20 = c20 * m00 + sp * m10 + c22 * m20
    l21 = c20 * m01 + sp * m11 + c22 * m21
    l22 = c20 * m02 + sp * m12 + c22 * m22

    vs, es = SHAPES[t]
    pts = []
    minx = 999
    maxx = -999
    miny = 999
    maxy = -999
    for v in vs:
        x = v[0]
        y = v[1]
        z = v[2]
        zc = l20 * x + l21 * y + l22 * z + zc0
        zz = zc + cam
        if zz < 0.5:
            pts.append(None)
            continue
        f = FOCAL / zz
        px = (l00 * x + l01 * y + l02 * z + xr0) * f
        py = (l10 * x + l11 * y + l12 * z + yr0) * f
        if zc > 0.0 and px * px + py * py < 900.0:
            px, py = lens(px, py, zc, E4)
        sx = int(cx + px)
        sy = int(cy + py)
        pts.append((sx, sy))
        if sx < minx:
            minx = sx
        if sx > maxx:
            maxx = sx
        if sy < miny:
            miny = sy
        if sy > maxy:
            maxy = sy

    # black halo so the shape always stands out from the bright disc
    if maxx > -999 and maxx - minx < 40 and maxy - miny < 30:
        x0 = max(0, minx - 1)
        y0 = max(0, miny - 1)
        x1 = min(71, maxx + 1)
        y1 = min(39, maxy + 1)
        if x1 >= x0 and y1 >= y0:
            disp.drawFilledRectangle(x0, y0, x1 - x0 + 1, y1 - y0 + 1, 0)

    hot = S > 2.5      # tidally heated: draw bold
    for e in es:
        a = pts[e[0]]
        c = pts[e[1]]
        if a is None or c is None:
            continue
        if 0 <= a[0] < 71 and 0 <= a[1] < 40 and 0 <= c[0] < 71 and 0 <= c[1] < 40:
            disp.drawLine(a[0], a[1], c[0], c[1], 1)
            if hot:
                disp.drawLine(a[0] + 1, a[1], c[0] + 1, c[1], 1)

    # the star twinkles: a little sparkle on its glowing core
    if t == STAR_T:
        gx = tx[h]
        gy = ty[h]
        if 3 <= gx < 68 and 3 <= gy < 36:
            put = disp.setPixel
            put(gx - 1, gy, 1)
            put(gx + 1, gy, 1)
            put(gx, gy - 1, 1)
            put(gx, gy + 1, 1)
            if (frame >> 1) & 1:
                put(gx - 3, gy, 1)
                put(gx + 3, gy, 1)
                put(gx, gy - 3, 1)
                put(gx, gy + 3, 1)


def draw_preview(t, pcx, pcy, scale):
    # small spinning preview of the selected shape (orthographic)
    vs, es = SHAPES[t]
    a = frame * 0.15
    bb = 0.5 + frame * 0.09
    if t == 2:
        bb = 0.5
    elif t == STAR_T:
        bb = 0.25          # star just spins around its upright axis
    ca = math.cos(a)
    sa = math.sin(a)
    cb = math.cos(bb)
    sb = math.sin(bb)
    pts = []
    for v in vs:
        x1 = v[0] * ca + v[2] * sa
        z1 = v[2] * ca - v[0] * sa
        y2 = v[1] * cb - z1 * sb
        pts.append((int(pcx + x1 * scale), int(pcy + y2 * scale)))
    disp.drawFilledRectangle(0, 0, 19, 19, 0)
    for e in es:
        a_ = pts[e[0]]
        c_ = pts[e[1]]
        if 0 <= a_[0] < 72 and 0 <= a_[1] < 40 and 0 <= c_[0] < 72 and 0 <= c_[1] < 40:
            disp.drawLine(a_[0], a_[1], c_[0], c_[1], 1)


while True:
    t0 = _tick()

    # ---------- input ----------
    bprev = bnow
    bnow = thumby.buttonB.pressed()
    if bnow:
        bhold += 1
    if menu_open:
        aiming = False
        was_aiming = False
        if bnow and not bprev:                 # B closes the menu
            menu_open = False
            b_lock = True
        if thumby.buttonU.justPressed():
            msel = (msel - 1) % len(MENU)
        if thumby.buttonD.justPressed():
            msel = (msel + 1) % len(MENU)
        dirn = 0
        if thumby.buttonL.pressed():
            dirn = -1
        elif thumby.buttonR.pressed():
            dirn = 1
        if dirn:
            mrep += 1
            if mrep == 1 or (mrep > 12 and mrep % 3 == 0):
                change_setting(dirn)
        else:
            mrep = 0
        if thumby.buttonA.justPressed():       # A closes (or resets)
            if msel == RESET_IDX:
                reset_all()
            menu_open = False
            a_lock = True
    else:
        was_aiming = aiming
        if not thumby.buttonA.pressed():
            a_lock = False
        aiming = thumby.buttonA.pressed() and not a_lock
        if aiming:
            if not was_aiming:
                charge = 0.0
            if charge < 1.0:
                charge += 0.025
            if thumby.buttonL.pressed() and ax > -30.0:
                ax -= 1.4
            if thumby.buttonR.pressed() and ax < 30.0:
                ax += 1.4
            if thumby.buttonU.pressed() and ay > -16.0:
                ay -= 1.0
            if thumby.buttonD.pressed() and ay < 16.0:
                ay += 1.0
        else:
            if thumby.buttonL.pressed():
                yaw -= 0.05
            if thumby.buttonR.pressed():
                yaw += 0.05
            if thumby.buttonU.pressed() and pitch < 1.3:
                pitch += 0.025
            if thumby.buttonD.pressed() and pitch > 0.08:
                pitch -= 0.025
        # B: tap = next shape, hold = open the menu
        if bnow and not aiming and bhold == 15 and not b_lock:
            menu_open = True
            b_lock = True
            mrep = 0
        if bprev and not bnow and bhold < 15 and not b_lock:
            typ = (typ + 1) % NSH
            label_t = 45
    if not bnow:
        bhold = 0
        b_lock = False

    frame += 1
    yaw += 0.011
    ring_a += 0.08
    cam = CAM0 + 0.5 * math.sin(frame * 0.0042)
    cam_pitch = pitch + 0.10 * math.sin(frame * 0.0107)
    cyw = math.cos(yaw)
    syw = math.sin(yaw)
    cp = math.cos(cam_pitch)
    sp = math.sin(cam_pitch)
    c10 = sp * syw
    c12 = -sp * cyw
    c20 = -cp * syw
    c22 = cp * cyw

    if was_aiming and not aiming:
        throw()

    cx = CX0
    cy = CY0
    if shake > 0:
        cx += random.randint(-1, 1)
        cy += random.randint(-1, 1)
        shake -= 1
    if label_t > 0:
        label_t -= 1

    if growth > 0.0:
        growth -= 0.0004
        if growth < 0.0:
            growth = 0.0
    gsc = 1.0 + min(0.7, growth + gfloor)
    swallow2 = 0.02 * gsc * gsc
    gme = GM * gravm * gsc
    if jet > 0.2:
        jet *= 0.985
    f0 = FOCAL / cam
    E0 = 0.30 * f0 * gsc        # size of the shadow / photon ring
    E = E0 * lensm              # strength of the light bending
    E4 = 4.0 * E * E

    # ---------- physics: stars (distant ones take one big step) ----------
    act = [k for k in range(NT) if QON[k]]
    dg2 = DRAGS * DRAGS
    dgy2 = DRAGYS * DRAGYS

    for i in range(nact):
        x = PX[i]
        y = PY[i]
        z = PZ[i]
        vx = VX[i]
        vy = VY[i]
        vz = VZ[i]
        if x * x + y * y + z * z > 0.3:
            steps = 1
            hh = 1.0
            dg = dg2
            dgy = dgy2
        else:
            steps = 2
            hh = 0.5
            dg = DRAGS
            dgy = DRAGYS
        for _ in range(steps):
            d2 = x * x + y * y + z * z + EPS
            r = math.sqrt(d2)
            f = -gme * hh / (d2 * r)
            if d2 < 0.8:
                # GR-like correction: precession + innermost stable orbit
                lx = y * vz - z * vy
                ly = z * vx - x * vz
                lz = x * vy - y * vx
                f -= KGR * hh * (lx * lx + ly * ly + lz * lz) / (d2 * d2 * r)
                # frame dragging: tilted orbits precess about the spin axis
                ph = KLT * spinm * hh / (d2 * r)
                c = 1.0 - 0.5 * ph * ph
                x, z = c * x - ph * z, c * z + ph * x
                vx, vz = c * vx - ph * vz, c * vz + ph * vx
            vx += x * f
            vy += y * f
            vz += z * f
            for k in act:
                dx = x - QX[k]
                dy = y - QY[k]
                dz = z - QZ[k]
                e2 = dx * dx + dy * dy + dz * dz + 0.012
                g = -QG[k] * hh / (e2 * math.sqrt(e2))
                vx += dx * g
                vy += dy * g
                vz += dz * g
            vx *= dg
            vy *= dgy
            vz *= dg
            x += vx * hh
            y += vy * hh
            z += vz * hh
        PX[i] = x
        PY[i] = y
        PZ[i] = z
        VX[i] = vx
        VY[i] = vy
        VZ[i] = vz

    # ---------- physics: thrown shapes (adaptive sub-steps) ----------
    for k in act:
        x = QX[k]
        y = QY[k]
        z = QZ[k]
        vx = QVX[k]
        vy = QVY[k]
        vz = QVZ[k]
        if x * x + y * y + z * z > 0.6:
            steps = 2
        else:
            steps = 4
        hh = 1.0 / steps
        for _ in range(steps):
            d2 = x * x + y * y + z * z + EPS
            r = math.sqrt(d2)
            f = -gme * hh / (d2 * r)
            if d2 < 0.8:
                lx = y * vz - z * vy
                ly = z * vx - x * vz
                lz = x * vy - y * vx
                f -= KGR * hh * (lx * lx + ly * ly + lz * lz) / (d2 * d2 * r)
                ph = KLT * spinm * hh / (d2 * r)
                c = 1.0 - 0.5 * ph * ph
                x, z = c * x - ph * z, c * z + ph * x
                vx, vz = c * vx - ph * vz, c * vz + ph * vx
            vx += x * f
            vy += y * f
            vz += z * f
            for j in act:
                if j != k:
                    dx = x - QX[j]
                    dy = y - QY[j]
                    dz = z - QZ[j]
                    e2 = dx * dx + dy * dy + dz * dz + 0.01
                    g = -QG[j] * hh / (e2 * math.sqrt(e2))
                    vx += dx * g
                    vy += dy * g
                    vz += dz * g
            x += vx * hh
            y += vy * hh
            z += vz * hh
        # ram pressure: plunging through the gas disc slows the shape down
        if -0.08 < y < 0.08 and x * x + z * z < 1.5:
            vx *= ram
            vy *= ram
            vz *= ram
        QX[k] = x
        QY[k] = y
        QZ[k] = z
        QVX[k] = vx
        QVY[k] = vy
        QVZ[k] = vz

    # ---------- mergers ----------
    for a in range(NT):
        if not QON[a]:
            continue
        for b in range(a + 1, NT):
            if not QON[b]:
                continue
            dx = QX[a] - QX[b]
            dy = QY[a] - QY[b]
            dz = QZ[a] - QZ[b]
            if dx * dx + dy * dy + dz * dz < 0.012:
                ma = QG[a]
                mb = QG[b]
                mt = ma + mb
                QVX[a] = (QVX[a] * ma + QVX[b] * mb) / mt
                QVY[a] = (QVY[a] * ma + QVY[b] * mb) / mt
                QVZ[a] = (QVZ[a] * ma + QVZ[b] * mb) / mt
                QX[a] = (QX[a] * ma + QX[b] * mb) / mt
                QY[a] = (QY[a] * ma + QY[b] * mb) / mt
                QZ[a] = (QZ[a] * ma + QZ[b] * mb) / mt
                if mb > ma:
                    QT[a] = QT[b]
                QG[a] = min(0.0014, mt * 0.95)   # some mass is radiated away
                QM[a] = min(24, QM[a] + QM[b])
                QM0[a] = min(24, QM0[a] + QM0[b])
                QSZ[a] = min(1.7, QSZ[a] + 0.3)
                QON[b] = False
                add_ripple(QX[a], QY[a], QZ[a])
                shake = 4
                flash = 6
    act = [k for k in range(NT) if QON[k]]

    # ---------- fates ----------
    for k in act:
        QL[k] += 1
        x = QX[k]
        y = QY[k]
        z = QZ[k]
        d2 = x * x + y * y + z * z
        r = math.sqrt(d2) + 0.001
        if d2 < swallow2 * 1.25:
            QON[k] = False
            flash = 10
            shake = 8
            jet = 1.0
            feed(T_GROW[QT[k]] * (0.4 + 0.6 * QM[k] / QM0[k]))
            add_ripple(0.0, 0.0, 0.0)
        else:
            q = RT * gsc / r
            if q * q * q > 1.5 and QM[k] > 0:
                # inside the Roche limit: torn apart into debris
                if QL[k] % 3 == 0:
                    shed(k)
                    QM[k] -= 1
                    if QM[k] <= 0:
                        QON[k] = False
                        flash = 6
                        jet += 0.3
                        if jet > 1.0:
                            jet = 1.0
                        feed(T_GROW[QT[k]] * 0.5)
            elif QL[k] > 60 and (d2 > 7.0 or QL[k] > 600):
                QON[k] = False

    for i in range(nact):
        d2 = PX[i] * PX[i] + PY[i] * PY[i] + PZ[i] * PZ[i]
        HOT[i] = d2 < 0.4
        if d2 < swallow2:
            flash = 7
            shake = 3
            jet += 0.35
            if jet > 1.0:
                jet = 1.0
            feed(0.04)
            spawn(i, 1.1, 1.5)
        elif d2 > 7.0:
            spawn(i, 1.1, 1.5)

    for i in range(RN):
        if RPR[i] >= 0.0:
            RPR[i] += 0.05
            if RPR[i] > 1.8:
                RPR[i] = -1.0

    # ---------- render ----------
    disp.fill(0)

    # distant stars (positions refreshed every other frame)
    if not lite:
        if frame & 1:
            for i in range(12):
                x = BX[i]
                y = BY[i]
                z = BZ[i]
                zr = z * cyw - x * syw
                if y * sp + zr * cp > 0.0:
                    ox = int((x * cyw + z * syw) * 46.0 + 100.5) - 100
                    oy = int((y * cp - zr * sp) * 46.0 + 100.5) - 100
                    if -34 <= ox <= 34 and -18 <= oy <= 18:
                        BSX[i] = ox
                        BSY[i] = oy
                        continue
                BSX[i] = -999
        put = disp.setPixel
        for i in range(12):
            if BSX[i] > -500 and (frame + i * 7) & 31 >= 3:
                put(cx + BSX[i], cy + BSY[i], 1)

    # gravitational-wave ripples
    for i in range(RN):
        R = RPR[i]
        if R < 0.0:
            continue
        for k in range(16):
            if R > 1.0 and (k & 1):
                continue
            wx = RPX[i] + RC[k] * R
            wy = RPY[i]
            wz = RPZ[i] + RS[k] * R
            xr = wx * cyw + wz * syw
            zr = wz * cyw - wx * syw
            yr = wy * cp - zr * sp
            zz = wy * sp + zr * cp + cam
            if zz > 0.6:
                f = FOCAL / zz
                px = int(cx + xr * f)
                py = int(cy + yr * f)
                if 0 <= px < 72 and 0 <= py < 40:
                    disp.setPixel(px, py, 1)

    # accretion disc: re-project the cached rings only when the view really changed
    since = frame - lc_f
    if since >= 24 or (since >= 2 and (abs(cam_pitch - lc_p) > 0.012 or
                                       abs(cam - lc_c) > 0.04 or
                                       abs(gsc - lc_g) > 0.02)):
        build_rings()
        lc_p = cam_pitch
        lc_c = cam
        lc_g = gsc
        lc_f = frame

    # far side of the disc (lensed over the top), drawn behind the hole
    draw_disc(True)

    # jets
    jj = jet * jetm
    if jj > 1.0:
        jj = 1.0
    if jetm > 0.0 and not lite:
        na = 2 + int(jj * (NJ - 2))
    else:
        na = 0
    for k in range(na):
        y = JY[k] + 0.03 + jj * 0.025
        if y > 1.6:
            y = 0.02
            JA[k] = random.uniform(0.0, TWO_PI)
        JY[k] = y
        a = JA[k] + y * 7.0
        r = 0.02 + 0.07 * y
        x = r * math.cos(a)
        z = r * math.sin(a)
        wy = JS[k] * y
        xr = x * cyw + z * syw
        zr = z * cyw - x * syw
        yr = wy * cp - zr * sp
        zz = wy * sp + zr * cp + cam
        if zz < 0.6:
            continue
        f = FOCAL / zz
        sx = int(cx + xr * f)
        sy = int(cy + yr * f)
        if 0 <= sx < 71 and 0 <= sy < 39:
            if y < 1.1 or (frame + k) & 1:
                disp.setPixel(sx, sy, 1)
                if jj > 0.6 and y < 0.7:
                    disp.setPixel(sx + 1, sy, 1)

    # black hole shadow (a round black disc) + thin bright photon ring
    for r_ in SHR:
        disp.drawFilledRectangle(cx - r_[1], cy + r_[0], 2 * r_[1] + 1, r_[2], 0)
    put = disp.setPixel
    for x, y in PHR:
        put(cx + x, cy + y, 1)

    # near side of the disc passes IN FRONT of the hole
    draw_disc(False)

    # orbiting stars (lensed when behind the hole)
    put = disp.setPixel
    for i in range(nact):
        x = PX[i]
        y = PY[i]
        z = PZ[i]
        xr = x * cyw + z * syw
        zr = z * cyw - x * syw
        yr = y * cp - zr * sp
        zc = y * sp + zr * cp
        zz = zc + cam
        if zz < 0.6:
            PRX[i] = -999
            continue
        f = FOCAL / zz
        px = xr * f
        py = yr * f
        if zc > 0.0 and px * px + py * py < 900.0:
            px, py = lens(px, py, zc, E4)
        sx = int(cx + px)
        sy = int(cy + py)
        qx = PRX[i]
        qy = PRY[i]
        PRX[i] = sx
        PRY[i] = sy
        if 0 <= sx < 71 and 0 <= sy < 39:
            if qx > -500 and not lite and 0 <= qx < 72 and 0 <= qy < 40:
                ddx = sx - qx
                ddy = sy - qy
                if ddx * ddx + ddy * ddy > 4:
                    if abs(ddx) + abs(ddy) < 10:
                        disp.drawLine(sx, sy, qx, qy, 1)
                else:
                    put(qx, qy, 1)
            if HOT[i] or f > 17.0:
                disp.drawFilledRectangle(sx, sy, 2, 2, 1)
            elif f < 14.0:
                if (frame + i) & 1:
                    put(sx, sy, 1)
            else:
                put(sx, sy, 1)

    # swallow flash
    if flash > 0:
        rr = 4 + (10 - flash) * 2
        for k in range(8):
            fx = cx + int(BURST_C[k] * rr)
            fy = cy + int(BURST_S[k] * rr * 0.6)
            if 0 <= fx < 72 and 0 <= fy < 40:
                disp.setPixel(fx, fy, 1)
        flash -= 1

    # thrown shapes: drawn last so they are always on top
    for k in act:
        if QON[k]:
            draw_throwable(k)

    # ---------- aiming UI ----------
    if aiming:
        tx_ = ax / f0
        ty_ = ay / f0
        ox = 0.0
        oy = 0.42
        oz = 1.7 - cam
        for s in range(1, 6):
            tt = s * 0.2
            gx = ox + (tx_ - ox) * tt
            gy = oy + (ty_ - oy) * tt
            gz = oz - oz * tt
            ff = FOCAL / (gz + cam)
            gpx = int(CX0 + gx * ff)
            gpy = int(CY0 + gy * ff)
            if 0 <= gpx < 72 and 0 <= gpy < 40 and (s + (frame >> 1)) & 1:
                disp.setPixel(gpx, gpy, 1)
        rx = int(CX0 + ax)
        ry = int(CY0 + ay)
        if (frame >> 2) & 1 or charge > 0.9:
            if 5 <= rx < 67 and 5 <= ry < 35:
                disp.drawLine(rx - 4, ry, rx - 2, ry, 1)
                disp.drawLine(rx + 2, ry, rx + 4, ry, 1)
                disp.drawLine(rx, ry - 4, rx, ry - 2, 1)
                disp.drawLine(rx, ry + 2, rx, ry + 4, 1)
                disp.setPixel(rx, ry, 1)
        disp.drawFilledRectangle(19, 34, 34, 6, 0)
        disp.drawRectangle(20, 35, 32, 4, 1)
        w = int(charge * 29)
        if w > 0:
            disp.drawFilledRectangle(21, 36, w, 2, 1)

    # shape preview + name
    if aiming or label_t > 0:
        draw_preview(typ, 9, 9, 3.6)
        nm = T_NAME[typ]
        wlab = len(nm) * 6
        lx0 = 36 - wlab // 2
        disp.drawFilledRectangle(lx0 - 1, 26, wlab + 1, 8, 0)
        disp.drawText(nm, lx0, 27, 1)

    if menu_open:
        draw_menu()

    # title + hints
    if frame < 70:
        disp.drawFilledRectangle(0, 0, 72, 20, 0)
        disp.drawText("SINGULARITY", 3, 2, 1)
        disp.drawText("BLACK HOLE", 6, 11, 1)
    elif frame < 240 and not menu_open:
        disp.drawFilledRectangle(0, 30, 72, 10, 0)
        if frame < 140:
            disp.drawText("HOLD A:AIM", 1, 32, 1)
        else:
            disp.drawText("HOLD B:MENU", 1, 32, 1)

    # ---------- self-tuning: keep the frame rate smooth ----------
    avg = avg * 0.85 + _diff(_tick(), t0) * 0.15
    if frame % 10 == 0:
        if avg > 30.0:
            # too slow: drop stars first, then switch to low-detail mode
            if nact > 3:
                nact -= 1
                if avg > 38.0 and nact > 3:
                    nact -= 1
            else:
                lite = True
        elif avg < 20.0:
            if lite:
                lite = False
            elif nact < star_cap:
                spawn(nact, 1.1, 1.5)
                nact += 1

    disp.update()
