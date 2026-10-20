# =====================================================================
#  FLYBRAIN  -  a tiny automatic fruit fly for the TinyCircuits Thumby
#  MicroPython.  Copy this folder to  /Games/FlyBrain/  on the Thumby.
#
#  96 spiking neurons (leaky integrate-and-fire, integer maths) wired like
#  a simplified fly circuit.  Nobody drives the fly: smell, eyes, bumps and
#  hunger go in, spikes flow through the network, and the motor neurons
#  decide where the legs go.  It wanders, sniffs out food, avoids walls and
#  obstacles, eats, gets full, and rests.
#
#  CONTROLS
#    A        cycle view: top view -> 3D chase cam -> fly eyes -> brain
#    B (hold) fast-forward
#    UP/DOWN  zoom (top view)
#    LEFT     drop a food pellet in front of the fly (poke it!)
# =====================================================================
import thumby
import math, random, time
from math import sin, cos, sqrt, atan2, floor

# ---------------------------------------------------------------- brain
NG = 16            # groups (cell types)
NPG = 6            # neurons per group
N = NG * NPG       # 96 neurons

(SL, SR, EL, ER, HUN, BMP, ATL, ATR,
 AVL, AVR, EXL, EXR, SLP, FWD, ML, MR) = range(16)

# (from group, to group, weight, synapses per target neuron)
WIRING = (
    # smell -> attraction, with left/right cross inhibition
    (SL, ATL, 230, 3), (SR, ATR, 230, 3),
    (SL, ATR, -200, 3), (SR, ATL, -200, 3),
    (HUN, ATL, 250, 3), (HUN, ATR, 250, 3),
    # attraction steers toward the odor and drives walking
    (ATL, MR, 500, 3), (ATR, ML, 500, 3),
    (ATL, ML, -250, 2), (ATR, MR, -250, 2),
    (ATL, FWD, 200, 3), (ATR, FWD, 200, 3),
    (ATL, EXL, -200, 3), (ATL, EXR, -200, 3),
    (ATR, EXL, -200, 3), (ATR, EXR, -200, 3),
    # eyes -> avoidance, steers away
    (EL, AVL, 450, 3), (ER, AVR, 450, 3),
    (AVL, ML, 600, 3), (AVR, MR, 600, 3),
    (AVL, MR, -500, 3), (AVR, ML, -500, 3),
    (AVL, AVR, -120, 2), (AVR, AVL, -120, 2),
    (BMP, AVL, 450, 3), (BMP, AVR, 450, 3),
    # spontaneous exploring
    (EXL, MR, 400, 3), (EXR, ML, 400, 3),
    (EXL, FWD, 150, 3), (EXR, FWD, 150, 3),
    # walking
    (FWD, ML, 350, 3), (FWD, MR, 350, 3),
    # rest circuit: fed fly sleeps; hunger / smell / danger wake it
    (SLP, FWD, -400, 4), (SLP, ML, -350, 3), (SLP, MR, -350, 3),
    (HUN, SLP, -400, 3), (ATL, SLP, -300, 3), (ATR, SLP, -300, 3),
    (AVL, SLP, -300, 3), (AVR, SLP, -300, 3), (BMP, SLP, -400, 3),
)

GRP = [i // NPG for i in range(N)]


class Brain:
    def __init__(self):
        self.v = [0] * N
        self.acc = [0] * N
        self.act = [0] * N          # recent-spike glow (for the display)
        self.spk = [0] * NG         # spikes this tick, per group
        self.rate = [0.0] * NG      # smoothed firing rate 0..1
        self.out = [[] for _ in range(N)]
        random.seed(7)              # same "genome" every boot
        gb = random.getrandbits
        for pre, post, w, k in WIRING:
            for j in range(NPG):
                tgt = post * NPG + j
                for _ in range(k):
                    src = pre * NPG + gb(8) % NPG
                    self.out[src].append((tgt, w * (85 + gb(5) % 31) // 100))
        try:
            random.seed(time.ticks_us())
        except Exception:
            pass

    def step(self, cur):
        v = self.v; acc = self.acc; act = self.act; spk = self.spk
        gb = random.getrandbits
        for g in range(NG):
            spk[g] = 0
        fired = []
        for i in range(N):
            g = GRP[i]
            x = v[i] - (v[i] >> 3) + acc[i] + cur[g] + gb(5) - 16
            acc[i] = 0
            a = act[i]
            if a:
                act[i] = a - 1
            if x >= 1000:
                x = 0
                fired.append(i)
                spk[g] += 1
                act[i] = 4
            elif x < -300:
                x = -300
            v[i] = x
        out = self.out
        for i in fired:
            for t, w in out[i]:
                acc[t] += w
        r = self.rate
        for g in range(NG):
            r[g] += (spk[g] / NPG - r[g]) * 0.25


# ---------------------------------------------------------------- world
WW = 480
WH = 280


def make_obstacles():
    random.seed(11)                 # same landscape every boot
    obs = []
    tries = 0
    while len(obs) < 18 and tries < 600:
        tries += 1
        r = 6 + random.getrandbits(4) % 10
        x = r + 14 + random.getrandbits(9) % (WW - 2 * r - 28)
        y = r + 14 + random.getrandbits(9) % (WH - 2 * r - 28)
        ok = True
        for a, b, c in obs:
            if (x - a) ** 2 + (y - b) ** 2 < (r + c + 18) ** 2:
                ok = False
        if ok:
            obs.append((x, y, r))
    return tuple(obs)


OBST = make_obstacles()
FOOD_R = 3.5
food = []
EYE_ANG = (-1.2, -0.8, -0.4, 0.4, 0.8, 1.2)
EYE_R = 30.0


def free_spot():
    while True:
        x = 10 + random.getrandbits(8) % (WW - 20)
        y = 10 + random.getrandbits(8) % (WH - 20)
        ok = True
        for cx, cy, r in OBST:
            if (cx - x) ** 2 + (cy - y) ** 2 < (r + 8) ** 2:
                ok = False
        if ok:
            return [x, y]


def cast(x, y, a, foods, obs):
    """distance and what a ray hits: 1 wall, 2 obstacle, 3 food"""
    dx = cos(a)
    dy = sin(a)
    best = 700.0
    kind = 0
    if dx > 0.0001:
        t = (WW - x) / dx
        if t < best:
            best = t; kind = 1
    elif dx < -0.0001:
        t = -x / dx
        if t < best:
            best = t; kind = 1
    if dy > 0.0001:
        t = (WH - y) / dy
        if t < best:
            best = t; kind = 1
    elif dy < -0.0001:
        t = -y / dy
        if t < best:
            best = t; kind = 1
    for cx, cy, r in obs:
        ox = cx - x
        oy = cy - y
        t = ox * dx + oy * dy
        if t > 0:
            p2 = ox * ox + oy * oy - t * t
            if p2 < r * r:
                t -= sqrt(r * r - p2)
                if t < best:
                    best = t; kind = 2
    if foods:
        rr = FOOD_R * FOOD_R
        for f in food:
            ox = f[0] - x
            oy = f[1] - y
            t = ox * dx + oy * dy
            if t > 0:
                p2 = ox * ox + oy * oy - t * t
                if p2 < rr:
                    t -= sqrt(rr - p2)
                    if t < best:
                        best = t; kind = 3
    return best, kind


# ---------------------------------------------------------------- fly
brain = Brain()
fx, fy = free_spot()
th = (random.getrandbits(8) / 256.0) * 6.28
spd = 0.0
energy = 650.0
wander = 0.0
bump = 0
eat_t = 0
eaten = 0
state = "WANDER"
cur = [0] * NG
wing = 0
tv = 0.0

for _ in range(8):
    food.append(free_spot())


def sim_tick():
    global fx, fy, th, spd, energy, wander, bump, eat_t, eaten, state, wing, tv
    r = random.getrandbits

    # --- smell: two antennae, each pointing a bit outward
    sl = 0.0
    sr = 0.0
    for f in food:
        dx = f[0] - fx
        dy = f[1] - fy
        d2 = dx * dx + dy * dy
        if d2 < 22500:
            c = 1.0 / (1.0 + d2 / 3600.0)
            a = atan2(dy, dx) - th
            u = cos(a + 0.7)
            if u > 0:
                sl += c * u
            u = cos(a - 0.7)
            if u > 0:
                sr += c * u
    # odor arrives in gusts, not a smooth gradient
    sl *= 0.7 + r(6) / 100.0
    sr *= 0.7 + r(6) / 100.0
    # --- eyes: proximity of obstacles / walls on each side
    pl = 0.0
    pr = 0.0
    near = [o for o in OBST if (o[0] - fx) ** 2 + (o[1] - fy) ** 2 < (o[2] + 40) ** 2]
    for k in range(6):
        d, kind = cast(fx, fy, th + EYE_ANG[k], False, near)
        if d < EYE_R:
            p = 1.0 - d / EYE_R
            if k < 3:
                if p > pl:
                    pl = p
            elif p > pr:
                pr = p
    # --- slow internal fluctuation (spontaneous activity) for exploring
    wander = wander * 0.96 + (r(8) / 128.0 - 1.0) * 0.25
    if wander > 1.0:
        wander = 1.0
    elif wander < -1.0:
        wander = -1.0
    # --- feed currents into the sensory / state neurons
    cur[SL] = int(min(sl, 1.0) * 450)
    cur[SR] = int(min(sr, 1.0) * 450)
    cur[EL] = int(pl * 420)
    cur[ER] = int(pr * 420)
    cur[BMP] = 300 if bump > 0 else 0
    if bump > 0:
        bump -= 1
    h = (800 - energy) * 0.45
    cur[HUN] = int(h) if h > 0 else 0
    s = (energy - 700) * 0.8
    cur[SLP] = int(s) if s > 0 else 0
    cur[EXL] = int(150 + 70 * wander)
    cur[EXR] = int(150 - 70 * wander)
    cur[FWD] = 100

    brain.step(cur)

    # --- motor neurons -> legs
    rate = brain.rate
    rl = rate[ML]
    rr = rate[MR]
    target = (rl + rr) * 3.0
    turn = (rl - rr) * 0.3
    if energy <= 0:
        target *= 0.6
    if eat_t > 0:
        eat_t -= 1
        target = 0.0
    spd += (target - spd) * 0.25
    tv += (turn - tv) * 0.4          # angular inertia
    th += tv
    wing += 1
    gait = spd * (1.0 + 0.3 * sin(wing * 0.9))   # tripod-gait wobble
    fx += cos(th) * gait
    fy += sin(th) * gait

    # --- collisions
    if fx < 3:
        fx = 3.0; bump = 6
    elif fx > WW - 3:
        fx = WW - 3.0; bump = 6
    if fy < 3:
        fy = 3.0; bump = 6
    elif fy > WH - 3:
        fy = WH - 3.0; bump = 6
    for cx, cy, rad in OBST:
        dx = fx - cx
        dy = fy - cy
        d2 = dx * dx + dy * dy
        m = rad + 3
        if d2 < m * m:
            d = sqrt(d2) + 0.001
            fx = cx + dx / d * m
            fy = cy + dy / d * m
            bump = 6

    # --- metabolism and eating
    energy -= 0.4 + spd * 0.12
    if energy < 0:
        energy = 0.0
    for f in food:
        dx = f[0] - fx
        dy = f[1] - fy
        if dx * dx + dy * dy < 36 and energy < 900:
            energy += 500
            if energy > 1000:
                energy = 1000.0
            nf = free_spot()
            f[0] = nf[0]
            f[1] = nf[1]
            eat_t = 25
            eaten += 1

    # --- label what the brain is doing (for the display only)
    if eat_t > 0:
        state = "EATING"
    elif rate[SLP] > 0.04 and spd < 0.2:
        state = "RESTING"
    elif rate[AVL] > 0.1 or rate[AVR] > 0.1:
        state = "AVOID"
    elif rate[ATL] > 0.05 or rate[ATR] > 0.05:
        state = "SNIFFING"
    elif energy < 450:
        state = "HUNGRY"
    else:
        state = "WANDER"


# ---------------------------------------------------------------- drawing
setpix = thumby.display.setPixel


def px(x, y):
    if 0 <= x < 72 and 0 <= y < 40:
        setpix(x, y, 1)


def hline(x0, x1, y):
    if 0 <= y < 40:
        if x0 > x1:
            x0, x1 = x1, x0
        for x in range(max(0, x0), min(71, x1) + 1):
            setpix(x, y, 1)


def vline(x, y0, y1):
    if 0 <= x < 72:
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(max(0, y0), min(39, y1) + 1):
            setpix(x, y, 1)


def line(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    n = int(max(abs(dx), abs(dy))) + 1
    for i in range(n + 1):
        px(floor(x0 + dx * i / n), floor(y0 + dy * i / n))


def circ(cx, cy, r):
    cx = floor(cx); cy = floor(cy); r = int(r)
    if cx + r < 0 or cx - r > 71 or cy + r < 0 or cy - r > 39:
        return
    if r < 1:
        px(cx, cy)
        return
    x = r; y = 0; e = 1 - r
    while x >= y:
        px(cx + x, cy + y); px(cx - x, cy + y)
        px(cx + x, cy - y); px(cx - x, cy - y)
        px(cx + y, cy + x); px(cx - y, cy + x)
        px(cx + y, cy - x); px(cx - y, cy - x)
        y += 1
        if e < 0:
            e += 2 * y + 1
        else:
            x -= 1
            e += 2 * (y - x) + 1


ZOOMS = (1.0, 0.5, 0.25, 0.125)
zoom_i = 1


def cam_axis(f, half, size):
    if half * 2 >= size:
        return size / 2.0
    if f < half:
        return half
    if f > size - half:
        return size - half
    return f


def draw_third(frame):
    z = ZOOMS[zoom_i]
    cx = cam_axis(fx, 36 / z, WW)
    cy = cam_axis(fy, 20 / z, WH)
    ox = 36 - cx * z
    oy = 20 - cy * z
    # arena border
    x0 = floor(ox); x1 = floor(ox + WW * z)
    y0 = floor(oy); y1 = floor(oy + WH * z)
    hline(x0, x1, y0); hline(x0, x1, y1)
    vline(x0, y0, y1); vline(x1, y0, y1)
    # obstacles
    for ocx, ocy, r in OBST:
        circ(ox + ocx * z, oy + ocy * z, r * z)
    # food
    for f in food:
        sx = floor(ox + f[0] * z)
        sy = floor(oy + f[1] * z)
        if z >= 0.5:
            px(sx, sy); px(sx + 1, sy); px(sx, sy + 1); px(sx + 1, sy + 1)
            if z >= 1.0 and (frame >> 3) & 1:
                px(sx - 1, sy - 1); px(sx + 2, sy - 1)
        else:
            px(sx, sy)
    # the fly
    sx = ox + fx * z
    sy = oy + fy * z
    ca = cos(th); sa = sin(th)
    L = 3.0 * max(z, 0.5) * 1.5
    if z >= 0.5:
        line(sx - ca * L, sy - sa * L, sx + ca * L, sy + sa * L)
        px(floor(sx + ca * (L + 1)), floor(sy + sa * (L + 1)))
        if spd > 0.3 and (wing & 1):
            wl = 3.0 * max(z, 0.5)
            px(floor(sx - sa * wl), floor(sy + ca * wl))
            px(floor(sx + sa * wl), floor(sy - ca * wl))
        elif spd <= 0.3 or not (wing & 1):
            px(floor(sx - sa * 2), floor(sy + ca * 2))
            px(floor(sx + sa * 2), floor(sy - ca * 2))
    else:
        px(floor(sx), floor(sy))
        px(floor(sx + ca * 1.5), floor(sy + sa * 1.5))
        if (frame >> 2) & 1:
            px(floor(sx) + 2, floor(sy) - 2)


def frect(x, y, w, h, c):
    x0 = max(0, x); x1 = min(72, x + w)
    y0 = max(0, y); y1 = min(40, y + h)
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            setpix(xx, yy, c)


def draw_chase(frame):
    """3D chase camera: perspective view from behind and above the fly"""
    ca = cos(th); sa = sin(th)
    camx = fx - ca * 28
    camy = fy - sa * 28
    CH = 14.0       # camera height
    F = 34.0        # focal length
    HOR = 14        # horizon row
    hline(0, 71, HOR)
    # ground dots: a lattice gives the feeling of motion
    gx0 = int(fx // 30) * 30
    gy0 = int(fy // 30) * 30
    for gx in range(gx0 - 180, gx0 + 211, 30):
        if gx < 0 or gx > WW:
            continue
        for gy in range(gy0 - 180, gy0 + 211, 30):
            if gy < 0 or gy > WH:
                continue
            dx = gx - camx; dy = gy - camy
            f = dx * ca + dy * sa
            if f > 6:
                px(floor(36 + (dy * ca - dx * sa) * F / f), floor(HOR + CH * F / f))
    # arena wall: fence posts
    for t in range(0, WW + 1, 24):
        for wy in (0, WH):
            dx = t - camx; dy = wy - camy
            f = dx * ca + dy * sa
            if 6 < f < 260:
                sx = floor(36 + (dy * ca - dx * sa) * F / f)
                if 0 <= sx < 72:
                    k = F / f
                    vline(sx, floor(HOR + (CH - 7) * k), floor(HOR + CH * k))
    for t in range(0, WH + 1, 24):
        for wx in (0, WW):
            dx = wx - camx; dy = t - camy
            f = dx * ca + dy * sa
            if 6 < f < 260:
                sx = floor(36 + (dy * ca - dx * sa) * F / f)
                if 0 <= sx < 72:
                    k = F / f
                    vline(sx, floor(HOR + (CH - 7) * k), floor(HOR + CH * k))
    # solid things, drawn far to near so near ones hide far ones
    items = []
    for o in OBST:
        dx = o[0] - camx; dy = o[1] - camy
        f = dx * ca + dy * sa
        if 10 < f < 230:
            items.append((f, 0, o, dy * ca - dx * sa))
    for fd in food:
        dx = fd[0] - camx; dy = fd[1] - camy
        f = dx * ca + dy * sa
        if 6 < f < 200:
            items.append((f, 1, fd, dy * ca - dx * sa))
    items.append((28.0, 2, None, 0.0))
    items.sort(key=lambda it: -it[0])
    for f, kind, o, r in items:
        k = F / f
        sx = 36 + r * k
        gy = HOR + CH * k
        if kind == 0:
            rad = o[2] * k
            if sx + rad < 0 or sx - rad > 71:
                continue
            hgt = 8 + o[2]
            ty = HOR + (CH - hgt) * k
            x0 = floor(sx - rad); x1 = floor(sx + rad)
            y0 = floor(ty); y1 = floor(gy)
            frect(x0, y0, x1 - x0 + 1, y1 - y0 + 1, 0)
            for yy in range(max(0, y0), min(40, y1 + 1)):
                for xx in range(max(0, x0 + 1), min(72, x1)):
                    if (xx + yy) & 3 == 0:
                        setpix(xx, yy, 1)
            vline(x0, y0, y1); vline(x1, y0, y1)
            e = max(1, int(rad * 0.3))
            hline(x0, x1, y0 - e // 2); hline(x0, x1, y0 + e // 2)
            hline(x0 + 1, x1 - 1, y1 + e // 2)
        elif kind == 1:
            fy2 = floor(HOR + (CH - 2.5) * k)
            s = max(1, int(3.5 * k))
            frect(floor(sx) - s // 2, fy2 - s // 2, s + 1, s + 1, 0)
            circ(sx, fy2, s)
            if (frame >> 3) & 1:
                px(floor(sx), fy2 - s - 2)
        else:
            w = max(3, int(4 * k))
            h = max(2, int(3 * k))
            sx = 36
            frect(floor(sx - w), floor(gy - h * 2), w * 2 + 1, h * 2 + 2, 0)
            frect(floor(sx - w // 2), floor(gy - h * 2) + 1, w, h * 2, 1)   # body
            px(floor(sx), floor(gy - h * 2) - 1)
            if spd > 0.3 and (wing & 1):
                for i in range(1, w + 1):
                    px(floor(sx - w // 2 - i), floor(gy - h * 2) - i // 2)
                    px(floor(sx + w // 2 + i), floor(gy - h * 2) - i // 2)
            else:
                px(floor(sx - w // 2 - 1), floor(gy - h) )
                px(floor(sx + w // 2 + 1), floor(gy - h))
            lg = floor(gy)
            if (wing >> 1) & 1:
                px(floor(sx - w // 2), lg); px(floor(sx + w // 2), lg - 1)
            else:
                px(floor(sx - w // 2), lg - 1); px(floor(sx + w // 2), lg)


FOV = 2.1
NRAY = 24


def draw_first():
    fpobs = [o for o in OBST if (o[0] - fx) ** 2 + (o[1] - fy) ** 2 < 62500]
    for x in range(0, 72, 4):
        px(x, 20)
    for i in range(NRAY):
        a = th + (i - (NRAY - 1) / 2.0) * FOV / NRAY
        d, kind = cast(fx, fy, a, True, fpobs)
        x0 = i * 3
        if kind == 3:
            h = int(220 / (d + 2))
            if h < 2:
                h = 2
            y0 = 20 - h // 2
            for yy in range(y0, y0 + h):
                if (yy + i) & 1:
                    setpix(x0, yy, 1); setpix(x0 + 1, yy, 1); setpix(x0 + 2, yy, 1)
        else:
            h = int(900 / (d + 10))
            if h < 1:
                h = 1
            if h > 40:
                h = 40
            if h < 1:
                h = 1
            y0 = 20 - h // 2
            if kind == 2:
                thumby.display.drawFilledRectangle(x0, y0, 3, h, 1)
            else:
                for yy in range(y0, y0 + h, 2):
                    setpix(x0, yy, 1); setpix(x0 + 1, yy, 1); setpix(x0 + 2, yy, 1)


raster = [0] * 72
head = 0
LABELS = ("SL", "SR", "EL", "ER", "HN", "BP", "AL", "AR",
          "VL", "VR", "XL", "XR", "SP", "FW", "ML", "MR")


def draw_brain():
    act = brain.act
    for g in range(NG):
        bx = (g % 8) * 9
        by = (g // 8) * 7
        for j in range(NPG):
            a = act[g * NPG + j]
            nx = bx + (j % 3) * 3
            ny = by + (j // 3) * 3
            if a >= 2:
                px(nx, ny); px(nx + 1, ny); px(nx, ny + 1); px(nx + 1, ny + 1)
            elif a == 1:
                px(nx, ny)
    thumby.display.drawText(state, 0, 15, 1)
    # energy gauge next to the label
    e = int(energy * 22 // 1000)
    hline(49, 71, 18)
    for y in range(16, 21):
        px(49, y)
    thumby.display.drawFilledRectangle(49, 16, e + 1, 5, 1)
    # scrolling spike raster (one row per cell type)
    for x in range(72):
        m = raster[(head + 1 + x) % 72]
        if m:
            for g in range(NG):
                if (m >> g) & 1:
                    setpix(x, 24 + g, 1)
    vline(0, 23, 23)


def gauge():
    n = int(energy * 72 // 1000)
    hline(0, n, 0)


# ---------------------------------------------------------------- main
thumby.display.setFPS(30)


def _btn(*names):
    # different Thumby firmware versions name the d-pad differently
    for n in names:
        if hasattr(thumby, n):
            return getattr(thumby, n)
    raise AttributeError(names[0])


btnA = _btn("buttonA")
btnB = _btn("buttonB")
btnU = _btn("dpadU", "buttonU")
btnD = _btn("dpadD", "buttonD")
btnL = _btn("dpadL", "buttonL")
view = 0
toast = 60
VIEW_NAMES = ("TOP VIEW", "3D CHASE", "FLY EYES", "BRAIN")
frame = 0
poke = 0

while True:
    t0 = time.ticks_ms()

    if btnA.justPressed():
        view = (view + 1) % 4
        toast = 45
    if btnU.justPressed() and zoom_i > 0:
        zoom_i -= 1
    if btnD.justPressed() and zoom_i < 3:
        zoom_i += 1
    if btnL.justPressed():
        food[poke % len(food)] = [
            min(WW - 8, max(8, fx + cos(th) * 35)),
            min(WH - 8, max(8, fy + sin(th) * 35))]
        poke += 1

    ticks = 4 if btnB.pressed() else 1
    mask = 0
    for _ in range(ticks):
        sim_tick()
        sp = brain.spk
        for g in range(NG):
            if sp[g]:
                mask |= 1 << g
    head = (head + 1) % 72
    raster[head] = mask

    thumby.display.fill(0)
    if view == 0:
        draw_third(frame)
        gauge()
    elif view == 1:
        draw_chase(frame)
        gauge()
    elif view == 2:
        draw_first()
        gauge()
    else:
        draw_brain()

    if toast > 0:
        toast -= 1
        thumby.display.drawFilledRectangle(0, 32, 72, 8, 0)
        thumby.display.drawText(VIEW_NAMES[view], 0, 33, 1)

    thumby.display.update()
    frame += 1
