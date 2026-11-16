# PerpetualDiamond.py  --  Thumby (MicroPython)
#
# Greyscale recreation of "The Perpetual Diamond" motion illusion
# (Oliver J. Flynn & Arthur G. Shapiro, i-Perception 2018; illusionscience.com)
#
# The shape NEVER moves. It is a fixed mid-grey shape wrapped in a very thin
# edge strip. The grey level of the strip and of the background both swing
# sinusoidally at 2 Hz. Strips that face the chosen direction run a quarter
# cycle (90 deg) AHEAD of the background, strips that face away run a quarter
# cycle BEHIND it. That phase difference alone makes the shape appear to drift
# continuously in the chosen direction.
#
# Controls
#   D-pad : choose the drift direction (up / down / left / right)
#   A     : next shape
#   B     : edge strip width, 1 px / 2 px
#
# Needs the thumbyGrayscale library (thumbyGrayscale.py next to this file or
# in /lib). If it is missing the game falls back to 1-bit black/white.

import time
import math

try:
    from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR
except ImportError:
    import thumby
    buttonA = thumby.buttonA
    buttonB = thumby.buttonB
    buttonU = thumby.buttonU
    buttonD = thumby.buttonD
    buttonL = thumby.buttonL
    buttonR = thumby.buttonR


def _pick_display():
    try:
        import thumbyGrayscale as g
        d = g.display
        lv = (getattr(d, "BLACK", 0), getattr(d, "DARKGRAY", 1),
              getattr(d, "LIGHTGRAY", 2), getattr(d, "WHITE", 3))
        try:
            d.enableGrayscale()
        except Exception:
            pass
        return d, lv, True
    except Exception:
        import thumby
        return thumby.display, (0, 0, 1, 1), False


display, LV, GRAY = _pick_display()
display.setFPS(60)

# ---------------------------------------------------------------- geometry
GR = 16                 # half size of the build grid
GW = 2 * GR + 1
CX = 36                 # shape centre on screen
CY = 18

# direction index: 0 up, 1 down, 2 left, 3 right  (screen y points down)
DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0))
DNAMES = ("UP", "DOWN", "LEFT", "RIGHT")


def _poly(pts):
    n = len(pts)

    def f(x, y):
        x += 0.013
        y += 0.017
        c = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y):
                if x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    c = not c
            j = i
        return c
    return f


def _star():
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 13.6 if k % 2 == 0 else 5.6
        pts.append((r * math.cos(a), r * math.sin(a) + 1.3))
    return _poly(pts)


def _hexagon():
    pts = []
    for k in range(6):
        a = k * math.pi / 3
        pts.append((13.4 * math.cos(a), 13.4 * math.sin(a)))
    return _poly(pts)


def f_diamond(x, y):
    return abs(x) + abs(y) <= 13


def f_square(x, y):
    return abs(x) <= 10 and abs(y) <= 10


def f_circle(x, y):
    return x * x + y * y <= 175


def f_cross(x, y):
    ax = abs(x)
    ay = abs(y)
    return (ax <= 4 and ay <= 12) or (ax <= 12 and ay <= 4)


def f_heart(x, y):
    u = x / 11.0
    v = -y / 11.0 + 0.1
    a = u * u + v * v - 1.0
    return a * a * a - u * u * v * v * v <= 0


def f_ring(x, y):
    r = x * x + y * y
    return 64 <= r <= 175


SHAPES = (
    ("DIAMOND", f_diamond),
    ("SQUARE", f_square),
    ("CIRCLE", f_circle),
    ("TRIANGLE", _poly(((0, -12.7), (13.2, 11.3), (-13.2, 11.3)))),
    ("HEXAGON", _hexagon()),
    ("STAR", _star()),
    ("CROSS", f_cross),
    ("HEART", f_heart),
    ("RING", f_ring),
)


def build(fn, T):
    """Pre-compute everything that does not change from frame to frame."""
    m = bytearray(GW * GW)                      # 1 = inside the shape
    for y in range(GW):
        for x in range(GW):
            if fn(x - GR, y - GR):
                m[y * GW + x] = 1

    # edge strip = pixels just outside the shape (ring 1, plus ring 2 if T==2)
    ring = bytearray(GW * GW)
    for y in range(1, GW - 1):
        for x in range(1, GW - 1):
            i = y * GW + x
            if not m[i] and (m[i - 1] or m[i + 1] or m[i - GW] or m[i + GW]):
                ring[i] = 1
    if T >= 2:
        for y in range(1, GW - 1):
            for x in range(1, GW - 1):
                i = y * GW + x
                if not m[i] and not ring[i]:
                    if (ring[i - 1] == 1 or ring[i + 1] == 1 or
                            ring[i - GW] == 1 or ring[i + GW] == 1):
                        ring[i] = 2

    # interior: one run per row, plus the checker pixels that make it mid-grey
    runs = []
    dark = bytearray()
    for y in range(GW):
        x = 0
        while x < GW:
            if m[y * GW + x]:
                x0 = x
                while x < GW and m[y * GW + x]:
                    sx = CX + x - GR
                    sy = CY + y - GR
                    if (sx + sy) & 1:
                        dark.append(sx)
                        dark.append(sy)
                    x += 1
                runs.append((CX + x0 - GR, CY + y - GR, x - x0))
            else:
                x += 1

    # edge strip pixels, sorted by which way their outward normal points
    ahead = [bytearray() for _ in range(4)]
    behind = [bytearray() for _ in range(4)]
    for y in range(1, GW - 1):
        for x in range(1, GW - 1):
            if not ring[y * GW + x]:
                continue
            sx = 0
            sy = 0
            c = 0
            for yy in range(max(0, y - 3), min(GW, y + 4)):
                for xx in range(max(0, x - 3), min(GW, x + 4)):
                    if m[yy * GW + xx]:
                        sx += xx
                        sy += yy
                        c += 1
            if not c:
                continue
            nx = x - sx / c
            ny = y - sy / c
            ln = math.sqrt(nx * nx + ny * ny)
            if ln < 0.01:
                continue
            nx /= ln
            ny /= ln
            px = CX + x - GR
            py = CY + y - GR
            for d in range(4):
                s = nx * DIRS[d][0] + ny * DIRS[d][1]
                if s > 0.34:            # faces the drift direction -> leads
                    ahead[d].append(px)
                    ahead[d].append(py)
                elif s < -0.34:         # faces away -> lags
                    behind[d].append(px)
                    behind[d].append(py)
                # edges side-on to the drift stay in phase with the background
    return runs, dark, ahead, behind


# ------------------------------------------------------------------- game
def title():
    black = LV[0]
    white = LV[3]
    soft = LV[2]
    display.fill(black)
    lines = (("PERPETUAL", 0, white), ("DIAMOND", 7, white),
             ("DPAD:DIR", 16, soft), ("A:SHAPE", 24, soft), ("B:EDGE", 32, soft))
    for txt, y, col in lines:
        display.drawText(txt, (72 - 6 * len(txt)) // 2, y, col)
    display.update()
    # let go of anything held, then wait for A or B
    while buttonA.pressed() or buttonB.pressed():
        time.sleep_ms(10)
    while not (buttonA.pressed() or buttonB.pressed()):
        time.sleep_ms(10)


def run():
    title()

    shape = 0
    edge_w = 1
    direction = 0
    runs, dark, ahead, behind = build(SHAPES[shape][1], edge_w)

    msg = ""
    msg_until = 0
    pu = buttonU.pressed()
    pd = buttonD.pressed()
    pl = buttonL.pressed()
    pr = buttonR.pressed()
    pa = buttonA.pressed()
    pb = buttonB.pressed()

    rect = display.drawFilledRectangle
    sp = display.setPixel
    black = LV[0]
    white = LV[3]
    dkc = LV[1]
    ltc = LV[2]
    k = 2.0 * math.pi / 500.0           # 2 Hz  ->  500 ms period

    while True:
        ms = time.ticks_ms()

        cu = buttonU.pressed()
        cd = buttonD.pressed()
        cl = buttonL.pressed()
        cr = buttonR.pressed()
        ca = buttonA.pressed()
        cb = buttonB.pressed()
        say = None
        if cu and not pu:
            direction = 0
            say = "UP"
        elif cd and not pd:
            direction = 1
            say = "DOWN"
        elif cl and not pl:
            direction = 2
            say = "LEFT"
        elif cr and not pr:
            direction = 3
            say = "RIGHT"
        if ca and not pa:
            shape = (shape + 1) % len(SHAPES)
            runs, dark, ahead, behind = build(SHAPES[shape][1], edge_w)
            say = SHAPES[shape][0]
        if cb and not pb:
            edge_w = 3 - edge_w
            runs, dark, ahead, behind = build(SHAPES[shape][1], edge_w)
            say = "EDGE " + str(edge_w) + "PX"
        pu = cu
        pd = cd
        pl = cl
        pr = cr
        pa = ca
        pb = cb
        if say:
            msg = say
            msg_until = time.ticks_add(ms, 1200)

        # sinusoidal luminance, 4 grey levels:  bg = sin, lead = +90, lag = -90
        th = (ms % 500) * k
        s = math.sin(th)
        c = math.cos(th)
        col_bg = LV[int(2.0 + 1.5 * s)]
        col_lead = LV[int(2.0 + 1.5 * c)]
        col_lag = LV[int(2.0 - 1.5 * c)]

        display.fill(col_bg)

        for rx, ry, rw in runs:                 # static mid-grey interior
            rect(rx, ry, rw, 1, ltc)
        for i in range(0, len(dark), 2):
            sp(dark[i], dark[i + 1], dkc)

        a = ahead[direction]                    # thin edge strips
        for i in range(0, len(a), 2):
            sp(a[i], a[i + 1], col_lead)
        b = behind[direction]
        for i in range(0, len(b), 2):
            sp(b[i], b[i + 1], col_lag)

        if msg and time.ticks_diff(msg_until, ms) > 0:
            rect(0, 33, 72, 7, black)
            display.drawText(msg, (72 - 6 * len(msg)) // 2, 33, white)

        display.update()


run()
