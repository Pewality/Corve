# AUTOMATIC DRAWING MACHINE for Thumby (MicroPython)
#
# A pen plotter that never gets tired. Twelve "machines", each one a
# mathematical rule, draw themselves on the 72x40 screen. Every drawing
# has a seed number, so a good one can be recreated.
#
#   LEFT / RIGHT : choose machine (AUTO = machine picks itself)
#   UP / DOWN    : drawing speed
#   A            : new drawing (new seed)
#   B            : pause / resume
#
# Install: copy this file to /Games/DrawingMachine/DrawingMachine.py

import thumby
import math
import random
import time

W = 72
H = 40
CX = 35.5
CY = 19.5
PI = math.pi
TAU = 2 * math.pi

disp = thumby.display
disp.setFPS(30)

# shadow copy of the screen, so overlays (toasts) can be erased again
cv = bytearray(W * H)
sym = 0   # 0 none, 1 mirror left/right, 2 mirror up/down, 3 both


# ---------------------------------------------------------------- drawing
def put(x, y, v):
    cv[y * W + x] = v
    disp.setPixel(x, y, v)


def plot1(x, y):
    if 0 <= x < W and 0 <= y < H:
        put(x, y, 1)


def px(x, y):
    plot1(x, y)
    if sym & 1:
        plot1(W - 1 - x, y)
    if sym & 2:
        plot1(x, H - 1 - y)
    if sym == 3:
        plot1(W - 1 - x, H - 1 - y)


def fl(v):
    return math.floor(v + 0.5)


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def line(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    if dx > 300 or dy < -300:
        return
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def clear_canvas():
    for i in range(W * H):
        cv[i] = 0
    disp.fill(0)


def restore():
    disp.fill(0)
    for i in range(W * H):
        if cv[i]:
            disp.setPixel(i % W, i // W, 1)


def center_text(s, y):
    disp.drawText(s, (W - (len(s) * 6 - 1)) // 2, y, 1)


# ---------------------------------------------------------------- machines
# Each machine is a generator: every `yield` is one small step of drawing.

def spirograph():
    # hypotrochoid: a wheel of radius r rolling inside a ring of radius R,
    # with the pen d units from the wheel's centre
    global sym
    sym = 0
    R = random.randint(5, 14)
    r = random.randint(2, R - 1)
    d = random.randint(2, R)
    k = (R - r) / r
    s = 19.0 / ((R - r) + d)
    T = TAU * r / gcd(R, r)
    n = int(T / 0.04) + 1
    ox = oy = 0
    for i in range(n + 1):
        t = T * i / n
        x = fl(CX + s * ((R - r) * math.cos(t) + d * math.cos(k * t)))
        y = fl(CY + s * ((R - r) * math.sin(t) - d * math.sin(k * t)))
        if i:
            line(ox, oy, x, y)
        ox = x
        oy = y
        yield


def lissajous():
    # x = sin(a t + phase), y = sin(b t)
    global sym
    sym = 0
    while True:
        a = random.randint(1, 7)
        b = random.randint(1, 7)
        if gcd(a, b) == 1 and a + b >= 3:
            break
    ph = random.uniform(0, PI)
    n = 600
    ox = oy = 0
    for i in range(n + 1):
        t = TAU * i / n
        x = fl(CX + 34 * math.sin(a * t + ph))
        y = fl(CY + 19 * math.sin(b * t))
        if i:
            line(ox, oy, x, y)
        ox = x
        oy = y
        yield


def rose():
    # polar rose: r = cos(k * theta) with k = p / q
    global sym
    sym = 0
    while True:
        p = random.randint(1, 9)
        q = random.randint(1, 4)
        g = gcd(p, q)
        p //= g
        q //= g
        if p != q:
            break
    n = 300 * q
    ox = oy = 0
    for i in range(n + 1):
        th = TAU * q * i / n
        rr = 19 * math.cos(p * th / q)
        x = fl(CX + rr * math.cos(th))
        y = fl(CY + rr * math.sin(th))
        if i:
            line(ox, oy, x, y)
        ox = x
        oy = y
        yield


ANGLES = (57, 72, 89, 91, 117, 121, 123, 135, 144, 150, 157, 161, 167)


def turtle():
    # forward L, turn by a fixed angle, make L a bit longer, repeat
    global sym
    sym = random.choice((0, 0, 1, 3))
    ang = random.choice(ANGLES) * PI / 180
    inc = random.choice((0.15, 0.25, 0.4, 0.6))
    x = CX
    y = CY
    h = random.uniform(0, TAU)
    L = 1.0
    while L < 45:
        nx = x + L * math.cos(h)
        ny = y + L * math.sin(h)
        line(fl(x), fl(y), fl(nx), fl(ny))
        x = nx
        y = ny
        h += ang
        L += inc
        yield


def harmonograph():
    # two damped pendulums per axis
    global sym
    sym = random.choice((0, 0, 3))
    while True:
        fi = [random.randint(1, 4) for i in range(4)]
        if fi[0] != fi[2] and fi[1] != fi[3] and fi[0] + fi[1] != fi[2] + fi[3]:
            break
    f = [v + random.uniform(-0.012, 0.012) for v in fi]
    ph = [random.uniform(0, TAU) for i in range(4)]
    dp = [random.uniform(0.02, 0.04) for i in range(4)]
    dt = 0.035
    n = int(110 / dt)
    ox = oy = 0
    for i in range(n):
        t = i * dt
        x = (17 * math.sin(f[0] * t + ph[0]) * math.exp(-dp[0] * t) +
             17 * math.sin(f[1] * t + ph[1]) * math.exp(-dp[1] * t))
        y = (9.5 * math.sin(f[2] * t + ph[2]) * math.exp(-dp[2] * t) +
             9.5 * math.sin(f[3] * t + ph[3]) * math.exp(-dp[3] * t))
        x = fl(CX + x)
        y = fl(CY + y)
        if i:
            line(ox, oy, x, y)
        ox = x
        oy = y
        yield


RULES = (30, 90, 110, 54, 60, 102, 150, 45, 22, 126, 18, 105, 73, 129)


def automaton():
    # elementary cellular automaton, one row per line, wraps at the edges
    global sym
    sym = 0
    rule = random.choice(RULES)
    row = [0] * W
    if random.randint(0, 2) == 0:
        for i in range(W):
            row[i] = random.randint(0, 1)
    else:
        row[W // 2] = 1
    for y in range(H):
        new = [0] * W
        for x in range(W):
            if row[x]:
                put(x, y, 1)
            idx = row[x - 1] * 4 + row[x] * 2 + row[(x + 1) % W]
            new[x] = (rule >> idx) & 1
            if x % 12 == 11:
                yield
        row = new


def chaos():
    # chaos game: jump part of the way to a random corner, again and again
    global sym
    sym = 0
    n = random.choice((3, 3, 5, 6))
    if n == 3:
        m = 0.5
        rad = 25.0
        yo = 6.25
    elif n == 5:
        m = 0.618
        rad = 19.0
        yo = 1.8
    else:
        m = 0.667
        rad = 19.0
        yo = 0.0
    vx = []
    vy = []
    for i in range(n):
        a = -PI / 2 + TAU * i / n
        vx.append(CX + rad * math.cos(a))
        vy.append(CY + yo + rad * math.sin(a))
    x = CX
    y = CY
    for i in range(8):
        v = random.randint(0, n - 1)
        x += (vx[v] - x) * m
        y += (vy[v] - y) * m
    for k in range(260):
        for j in range(10):
            v = random.randint(0, n - 1)
            x += (vx[v] - x) * m
            y += (vy[v] - y) * m
            px(fl(x), fl(y))
        yield


def fern():
    # Barnsley fern: four affine maps picked at random
    global sym
    sym = 0
    x = 0.0
    y = 0.0
    for k in range(300):
        for j in range(10):
            r = random.random()
            if r < 0.01:
                x, y = 0.0, 0.16 * y
            elif r < 0.86:
                x, y = 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
            elif r < 0.93:
                x, y = 0.2 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
            else:
                x, y = -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44
            px(fl(CX + (x - 0.24) * 5.0), fl(38.5 - y * 3.8))
        yield


def attractor():
    # Clifford attractor: x' = sin(a y) + c cos(a x), y' = sin(b x) + d cos(b y)
    global sym
    sym = random.choice((0, 0, 1, 2, 3))
    for tries in range(25):
        a = random.uniform(-2, 2)
        b = random.uniform(-2, 2)
        c = random.uniform(-2, 2)
        d = random.uniform(-2, 2)
        x = 0.1
        y = 0.1
        seen = set()
        x0 = y0 = 99.0
        x1 = y1 = -99.0
        for i in range(400):
            x, y = (math.sin(a * y) + c * math.cos(a * x),
                    math.sin(b * x) + d * math.cos(b * y))
            if i > 50:
                seen.add((int(x * 10), int(y * 10)))
                x0 = min(x0, x)
                x1 = max(x1, x)
                y0 = min(y0, y)
                y1 = max(y1, y)
        if len(seen) > 90 and x1 - x0 > 0.3 and y1 - y0 > 0.3:
            break
    else:
        a, b, c, d = -1.4, 1.6, 1.0, 0.7
        x0, x1, y0, y1 = -2.0, 2.0, -1.7, 1.7
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    sx = 34.0 / ((x1 - x0) / 2)
    sy = 18.5 / ((y1 - y0) / 2)
    x = 0.1
    y = 0.1
    for i in range(50):
        x, y = (math.sin(a * y) + c * math.cos(a * x),
                math.sin(b * x) + d * math.cos(b * y))
    for k in range(300):
        for j in range(12):
            x, y = (math.sin(a * y) + c * math.cos(a * x),
                    math.sin(b * x) + d * math.cos(b * y))
            px(fl(CX + (x - mx) * sx), fl(CY + (y - my) * sy))
        yield


def ant():
    # Langton's ant: white -> turn right, flip, step. black -> turn left, flip, step.
    global sym
    sym = 0
    g = bytearray(W * H)
    x = W // 2 + random.randint(-6, 6)
    y = H // 2 + random.randint(-4, 4)
    d = random.randint(0, 3)
    if random.randint(0, 1):
        for i in range(random.randint(20, 60)):
            gx = random.randrange(W)
            gy = random.randrange(H)
            g[gy * W + gx] = 1
            put(gx, gy, 1)
    DX = (0, 1, 0, -1)
    DY = (-1, 0, 1, 0)
    for k in range(1800):
        for j in range(10):
            i = y * W + x
            if g[i]:
                d = (d + 3) & 3
                g[i] = 0
                put(x, y, 0)
            else:
                d = (d + 1) & 3
                g[i] = 1
                put(x, y, 1)
            x = (x + DX[d]) % W
            y = (y + DY[d]) % H
        yield


def stringart():
    # times-table on an ellipse: join point i to point (i * k) mod n
    global sym
    sym = 0
    n = random.randint(24, 64)
    k = random.choice((2, 3, 4, 5, 6, 7, 8, 9, 11, 13))
    pts = []
    for i in range(n):
        a = TAU * i / n - PI / 2
        pts.append((fl(CX + 34 * math.cos(a)), fl(CY + 19 * math.sin(a))))
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i * k) % n]
        line(x0, y0, x1, y1)
        for j in range(8):
            yield


def kaleido():
    # a smoothly wandering pen, mirrored into a kaleidoscope
    global sym
    sym = random.choice((1, 3, 3))
    xm = W // 2 - 1
    ym = (H // 2 - 1) if sym == 3 else (H - 1)
    x = random.uniform(2, xm - 2)
    y = random.uniform(2, ym - 2)
    h = random.uniform(0, TAU)
    w = 0.0
    for i in range(900):
        w += random.uniform(-0.1, 0.1)
        w *= 0.96
        h += w
        nx = x + 1.6 * math.cos(h)
        ny = y + 1.6 * math.sin(h)
        if nx < 0 or nx > xm:
            h = PI - h
            nx = clamp(nx, 0, xm)
        if ny < 0 or ny > ym:
            h = -h
            ny = clamp(ny, 0, ym)
        line(fl(x), fl(y), fl(nx), fl(ny))
        x = nx
        y = ny
        yield


MACHINES = (
    ("SPIROGRAPH", spirograph),
    ("LISSAJOUS", lissajous),
    ("ROSE CURVE", rose),
    ("TURTLE", turtle),
    ("HARMONOGRAPH", harmonograph),
    ("AUTOMATON", automaton),
    ("CHAOS GAME", chaos),
    ("FERN IFS", fern),
    ("ATTRACTOR", attractor),
    ("LANGTON ANT", ant),
    ("STRING ART", stringart),
    ("KALEIDOSCOPE", kaleido),
)
N = len(MACHINES)
SPEEDS = (1, 2, 4, 8, 16, 32, 64)

# ---------------------------------------------------------------- state
gen = None
cur = -1
mode = 0          # 0 = AUTO, otherwise machine number + 1
speed = 3
paused = False
toast = 0
wait = 0
seed = 0


def pick_random(avoid):
    random.seed(time.ticks_ms())
    return (avoid + random.randint(1, N - 1)) % N


def begin(idx):
    global gen, cur, seed, paused, toast
    cur = idx
    paused = False
    toast = 0
    seed = time.ticks_ms() & 0xFFFF
    random.seed(seed)
    clear_canvas()
    name = MACHINES[idx][0]
    if mode == 0:
        center_text("AUTO", 6)
        center_text(name, 17)
        center_text("#" + str(seed), 28)
    else:
        center_text(name, 14)
        center_text("#" + str(seed), 25)
    for i in range(24):
        disp.update()
    clear_canvas()
    disp.update()
    gen = MACHINES[idx][1]()


def start_new():
    if mode == 0:
        begin(pick_random(cur))
    else:
        begin(mode - 1)


def show_toast(s, frames):
    global toast
    w = len(s) * 6 + 5
    x = (W - w) // 2
    disp.drawFilledRectangle(x, 28, w, 11, 0)
    disp.drawRectangle(x, 28, w, 11, 1)
    disp.drawText(s, x + 3, 30, 1)
    toast = frames


def any_pressed():
    return (thumby.buttonA.justPressed() or thumby.buttonB.justPressed() or
            thumby.buttonL.justPressed() or thumby.buttonR.justPressed() or
            thumby.buttonU.justPressed() or thumby.buttonD.justPressed())


def intro():
    while True:
        disp.fill(0)
        disp.drawRectangle(0, 0, W, H, 1)
        center_text("AUTOMATIC", 4)
        center_text("DRAWING", 13)
        center_text("MACHINE", 22)
        center_text("PRESS A", 31)
        disp.update()
        if thumby.buttonA.justPressed():
            break
    n = 0
    while n < 150:
        disp.fill(0)
        disp.drawText("L/R MODE", 10, 2, 1)
        disp.drawText("U/D SPEED", 10, 11, 1)
        disp.drawText("A  NEW", 10, 20, 1)
        disp.drawText("B  PAUSE", 10, 29, 1)
        disp.update()
        n += 1
        if any_pressed():
            break


def main():
    global mode, speed, paused, toast, gen, wait
    intro()
    start_new()
    while True:
        if thumby.buttonL.justPressed():
            mode = (mode - 1) % (N + 1)
            start_new()
        elif thumby.buttonR.justPressed():
            mode = (mode + 1) % (N + 1)
            start_new()
        elif thumby.buttonA.justPressed():
            start_new()

        if thumby.buttonB.justPressed():
            if paused:
                paused = False
                restore()
            else:
                paused = True
                show_toast("PAUSED", 0)

        if thumby.buttonU.justPressed() and not paused:
            speed = min(speed + 1, len(SPEEDS) - 1)
            show_toast("SPEED " + str(speed + 1), 18)
        if thumby.buttonD.justPressed() and not paused:
            speed = max(speed - 1, 0)
            show_toast("SPEED " + str(speed + 1), 18)

        if not paused:
            if toast > 0:
                toast -= 1
                if toast == 0:
                    restore()
            elif gen is not None:
                try:
                    for i in range(SPEEDS[speed]):
                        next(gen)
                except Exception:
                    gen = None
                    wait = 75
            else:
                wait -= 1
                if wait <= 0:
                    start_new()

        disp.update()


main()
