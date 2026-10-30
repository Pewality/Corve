# ======================================================================
#  TURBO DRIFT  -  a 2.5D pseudo-3D arcade racer for the Thumby
#
#  D-PAD L/R : steer (the road pushes you outward in curves!)
#  B or UP   : jump (hop over cars and barriers for bonus points)
#  A (hold)  : NITRO - go faster and SMASH through traffic
#
#  Grab coins (they refill nitro), hit boost pads for free nitro,
#  and survive as the stages get faster and the roads get twistier.
#  Every stage changes the scenery and flips day/night.
#
#  Install: copy this file to  /Games/TurboDrift/TurboDrift.py
# ======================================================================
import math
import random
import thumby

d = thumby.display
d.setFPS(30)
sin = math.sin
rnd = random.random
rint = random.randint

HOR = 12            # horizon row
RH = 28             # rows from horizon to the bottom (HOR + RH = 40)
CAMW = 32.0         # road half-width (px) at the bottom of the screen
PY = 36             # row the player's car sits on
LANES = (-0.67, 0.0, 0.67)
NAMES = ("NIGHT HWY", "DESERT", "MOON WOODS", "SKYLINE")

INK = 1
PAPER = 0

# ---------------------------------------------------------------- save data
hi = 0
try:
    thumby.saveData.setName("TurboDrift")
    if thumby.saveData.hasItem("hi"):
        hi = int(thumby.saveData.getItem("hi"))
except Exception:
    pass


def save_hi():
    try:
        thumby.saveData.setItem("hi", hi)
        thumby.saveData.save()
    except Exception:
        pass


def beep(f, ms):
    try:
        thumby.audio.play(f, ms)
    except Exception:
        pass


# ------------------------------------------------------------ draw helpers
def rect(x, y, w, h, c):
    x = int(x); y = int(y); w = int(w); h = int(h)
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    if x + w > 72:
        w = 72 - x
    if y + h > 40:
        h = 40 - y
    if w > 0 and h > 0:
        d.drawFilledRectangle(x, y, w, h, c)


def hline(x1, x2, y, c):
    x1 = int(x1)
    x2 = int(x2)
    rect(x1, y, x2 - x1 + 1, 1, c)


def pixel(x, y, c):
    x = int(x)
    y = int(y)
    if 0 <= x < 72 and 0 <= y < 40:
        d.setPixel(x, y, c)


def panel(x, y, w, h):
    rect(x, y, w, h, PAPER)
    d.drawRectangle(x, y, w, h, INK)


def text_c(s, y):
    d.drawText(s, (72 - (len(s) * 6 - 1)) // 2, y, INK)


# ------------------------------------------------------------- static data
WR = [0.0] * 41      # world depth of each screen row (1/scale)
HW = [0.0] * 41      # road half-width in pixels of each screen row
OFF = [0.0] * 41     # horizontal curve offset of each screen row
for _y in range(HOR + 1, 41):
    WR[_y] = RH / (_y - HOR)
    HW[_y] = (_y - HOR) / RH * CAMW

stars = [(rint(0, 71), rint(1, 9)) for _ in range(14)]
MTN = []
for _i in range(96):
    _m = int(2.2 + 1.6 * sin(_i * 6.2832 * 3 / 96) + 1.0 * sin(_i * 6.2832 * 7 / 96 + 1.0))
    MTN.append(max(0, min(4, _m)))
SUN = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if dx * dx + dy * dy <= 9]
HEART = ((0, 0), (1, 0), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
         (1, 2), (2, 2), (3, 2), (2, 3))

# ------------------------------------------------------------- game state
objs = []     # [Z, lane, kind, flag]   kind: 0 car 1 coin 2 pad 3 barrier
parts = []    # [x, y, vx, vy, life]
dist = plat = cam = speed = nitro = bg = nextZ = jh = jv = 0.0
padT = hearts = invul = flash = banner = jcool = bonus = score = 0
stage = lastStage = 0
air = boosting = newbest = False
t = 0


def reset():
    global dist, plat, cam, speed, nitro, padT, hearts, invul, jh, jv, air
    global jcool, bonus, bg, nextZ, stage, lastStage, flash, banner
    global boosting, score, newbest
    dist = 0.0
    plat = 0.0
    cam = 0.0
    speed = 0.12
    nitro = 30.0
    padT = 0
    hearts = 3
    invul = 0
    jh = 0.0
    jv = 0.0
    air = False
    jcool = 0
    bonus = 0
    bg = 0.0
    nextZ = 22.0
    stage = 0
    lastStage = 0
    flash = 0
    banner = 30
    boosting = False
    score = 0
    newbest = False
    del objs[:]
    del parts[:]


def hit(x, y):
    global hearts, invul, speed, flash
    hearts -= 1
    invul = 50
    speed = 0.05
    flash = 3
    burst(x, y, 14)
    beep(110, 250)


def burst(x, y, n):
    for _ in range(n):
        parts.append([x, y, (rnd() - 0.5) * 4.0, -rnd() * 3.0, 10 + rint(0, 8)])


def spawn(Z):
    """Drop a random pattern of stuff at world depth Z. Returns its length."""
    r = rnd()
    n = 0.0
    if r < 0.26:                                   # lone car
        objs.append([Z, LANES[rint(0, 2)], 0, 0])
    elif r < 0.44:                                 # wall of cars, coin in the gap
        g = rint(0, 2)
        for i in range(3):
            objs.append([Z, LANES[i], 1 if i == g else 0, 0])
    elif r < 0.60:                                 # coin line
        ln = (rnd() - 0.5) * 1.4
        for i in range(6):
            objs.append([Z + i * 0.9, ln, 1, 0])
        n = 5.0
    elif r < 0.70:                                 # coin snake
        for i in range(9):
            objs.append([Z + i * 0.8, 0.75 * sin(i * 0.75), 1, 0])
        n = 6.5
    elif r < 0.80:                                 # barrier - jump it!
        objs.append([Z, 0.0, 3, 0])
    elif r < 0.88:                                 # boost pad -> wall of cars to smash
        objs.append([Z, LANES[rint(0, 2)], 2, 0])
        for i in range(3):
            objs.append([Z + 3.5, LANES[i], 0, 0])
        n = 3.5
    elif r < 0.95:                                 # slalom with coins
        for i in range(4):
            a = 0 if i % 2 == 0 else 2
            objs.append([Z + i * 2.4, LANES[a], 0, 0])
            objs.append([Z + i * 2.4, LANES[2 - a], 1, 0])
        n = 7.2
    else:                                          # double barrier
        objs.append([Z, 0.0, 3, 0])
        objs.append([Z + 3.5, 0.0, 3, 0])
        n = 3.5
    objs.sort(key=lambda o: o[0])
    return n


def curve_at(z, amp):
    return amp * (0.7 * sin(z * 0.09) + 0.5 * sin(z * 0.031 + 2.0))


def build_road(amp):
    off = 0.0
    dd = 0.0
    OFF[40] = 0.0
    for y in range(39, HOR, -1):
        z = dist + WR[y]
        c = amp * (0.7 * sin(z * 0.09) + 0.5 * sin(z * 0.031 + 2.0))
        dd += c * 0.07
        off += dd
        OFF[y] = off


# --------------------------------------------------------------- rendering
def draw_sky():
    b = int(bg)
    for sx, sy in stars:
        pixel((sx - (b >> 3)) % 72, sy, INK)
    sunx = (70 - b // 4) % 100 - 14
    for dx, dy in SUN:
        pixel(sunx + dx, 9 + dy, INK)
    for x in range(72):
        m = MTN[(x + b) % 96]
        top = HOR - m
        if m > 0 and sunx - 4 <= x <= sunx + 4:
            rect(x, top, 1, m, PAPER)
        pixel(x, top, INK)


def draw_road():
    hline(0, 71, HOR, INK)
    for y in range(HOR + 1, 40):
        hw = HW[y]
        xc = 36 + OFF[y] - cam * hw
        L = int(xc - hw)
        R = int(xc + hw)
        band = 0
        if y > 18:
            band = int((WR[y] + dist) * 1.4) & 1
        if band:
            hline(0, L - 1, y, INK)
            hline(R + 1, 71, y, INK)
        else:
            ew = 1 + int(hw * 0.07)
            hline(L, L + ew - 1, y, INK)
            hline(R - ew + 1, R, y, INK)
            lw = 2 if hw > 16 else 1
            rect(xc - hw * 0.34, y, lw, 1, INK)
            rect(xc + hw * 0.34, y, lw, 1, INK)


def draw_scn(kind, x, y, h):
    if kind == 0:                                  # street lamp
        rect(x, y - h, 1, h, INK)
        if h >= 4:
            rect(x - h // 4, y - h, h // 4 + 1, 1, INK)
    elif kind == 1:                                # cactus
        rect(x, y - h, 1 + h // 6, h, INK)
        if h >= 5:
            rect(x - h // 4, y - h * 2 // 3, h // 4 + 1, 1, INK)
            rect(x - h // 4, y - h * 2 // 3 - h // 5, 1, h // 5 + 1, INK)
    elif kind == 2:                                # tree
        rect(x, y - h // 3, 1 + h // 8, h // 3 + 1, INK)
        rect(x - h // 4, y - h, h // 2 + 1 + h // 8, h * 2 // 3, INK)
    else:                                          # building
        bw = h // 2 + 2
        rect(x - bw // 2, y - h, bw, h, INK)
        if h >= 6:
            for wy in range(y - h + 2, y - 1, 3):
                rect(x - bw // 2 + 1, wy, 1, 1, PAPER)
                rect(x - bw // 2 + bw - 2, wy, 1, 1, PAPER)


def draw_scenery():
    kind = stage % 4
    first = (int(dist / 5.0) + 1) * 5
    for k in range(6, -1, -1):
        w = first + k * 5 - dist
        if w > 28.0 or w < 1.0:
            continue
        hw = CAMW / w
        y = int(HOR + RH / w)
        yy = y if y < 40 else 40
        h = int(13.0 / w) + 1
        base = 36 + OFF[yy] - cam * hw
        draw_scn(kind, int(base - 1.5 * hw), y, h)
        draw_scn(kind, int(base + 1.5 * hw), y, h)


def draw_car(x, yb, pw, me):
    """yb = first row BELOW the car."""
    if pw < 2:
        pw = 2
    ph = (pw * 3) // 5 + 1
    bx = x - pw // 2
    rh = ph * 2 // 5
    top = yb - ph
    rect(bx, top + rh, pw, ph - rh, INK)
    if pw >= 5:
        q = pw // 4
        rect(bx + q, top, pw - 2 * q, rh + 1, INK)
        if pw >= 7:
            rect(bx + q + 1, top + 1, pw - 2 * q - 2, max(1, rh - 1), PAPER)
    if pw >= 7:
        rect(bx + 1, top + rh + 1, 2, 1, PAPER)
        rect(bx + pw - 3, top + rh + 1, 2, 1, PAPER)
    if me:
        rect(bx - 1, yb - 2, 1, 2, INK)
        rect(bx + pw, yb - 2, 1, 2, INK)
        if boosting:
            fl = 1 + rint(0, 2)
            rect(bx + 1, yb, 2, fl, INK)
            rect(bx + pw - 3, yb, 2, fl, INK)


def draw_coin(x, y, hw):
    r = max(1, int(hw * 0.07))
    cy = y - r - 1 - int(hw * 0.08)
    if r < 2:
        rect(x, cy - 1, 1, 2, INK)
    elif (t // 4) & 1:
        rect(x - 1, cy - r, 3, 2 * r + 1, INK)
    else:
        rect(x - r + 1, cy - r, 2 * r - 1, 2 * r + 1, INK)
        rect(x - r, cy - r + 1, 2 * r + 1, 2 * r - 1, INK)
        if r >= 3:
            rect(x, cy - 1, 1, 3, PAPER)


def draw_pad(x, y, hw):
    pw = max(2, int(hw * 0.3))
    n = 1 + int(hw * 0.14)
    for r in range(n):
        half = (pw * (r + 1)) // n
        hline(x - half, x + half, y - (n - 1) + r, INK)
    if n >= 3:
        hline(x - 1, x + 1, y - 1, PAPER)


def draw_barrier(x, y, hw):
    bh = 2 + int(hw * 0.07)
    half = int(hw * 0.95)
    rect(x - half, y - bh, 2 * half + 1, bh, INK)
    if bh >= 3:
        i = x - half + 2
        while i < x + half - 1:
            rect(i, y - bh + 1, 1, bh - 2, PAPER)
            i += 4


def draw_objs():
    for i in range(len(objs) - 1, -1, -1):
        o = objs[i]
        if o[3] == 1:
            continue
        w = o[0] - dist
        if w > 28.0 or w < 0.7:
            continue
        hw = CAMW / w
        y = int(HOR + RH / w)
        yy = y if y < 40 else 40
        x = int(36 + OFF[yy] + (o[1] - cam) * hw)
        k = o[2]
        if k == 0:
            draw_car(x, y, int(0.36 * hw), False)
        elif k == 1:
            draw_coin(x, y, hw)
        elif k == 2:
            draw_pad(x, y, hw)
        else:
            draw_barrier(x, y, hw)


def draw_parts():
    for i in range(len(parts) - 1, -1, -1):
        p = parts[i]
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.3
        p[4] -= 1
        if p[4] <= 0:
            parts.pop(i)
        else:
            pixel(p[0], p[1], INK)


def draw_player():
    if invul > 0 and (invul // 3) % 2:
        return
    hw = HW[PY]
    x = int(36 + OFF[PY] + (plat - cam) * hw)
    if jh > 0:
        hline(x - 4, x + 4, 37, INK)
    draw_car(x, 37 - int(jh), int(0.36 * hw), True)


def render():
    global INK, PAPER
    INK = 1 if stage % 2 == 0 else 0
    if flash > 0:
        INK = 1 - INK
    PAPER = 1 - INK
    d.fill(PAPER)
    amp = min(0.6 + 0.1 * stage, 1.2)
    build_road(amp)
    draw_sky()
    draw_road()
    if boosting:
        for _ in range(5):
            sx = rint(0, 71)
            hline(sx, sx + 2 + rint(0, 4), rint(HOR + 3, 38), INK)
    draw_scenery()
    draw_objs()
    draw_parts()
    draw_player()


def draw_hud():
    rect(0, 0, 72, 7, PAPER)
    d.drawText("%05d" % score, 1, 0, INK)
    if not boosting or (t & 2):
        d.drawRectangle(32, 1, 20, 5, INK)
        rect(33, 2, int(nitro * 0.18), 3, INK)
    for i in range(3):
        if i < hearts:
            for hx, hy in HEART:
                pixel(54 + i * 6 + hx, 1 + hy, INK)


# ---------------------------------------------------------------- main loop
reset()
mode = 0          # 0 title, 1 playing, 2 game over
overT = 0
prevA = True      # ignore A if it's still held from the menu

while True:
    t += 1
    a = thumby.buttonA.pressed()
    b = thumby.buttonB.pressed()
    kl = thumby.buttonL.pressed()
    kr = thumby.buttonR.pressed()
    ku = thumby.buttonU.pressed()
    aEdge = a and not prevA
    prevA = a

    if mode == 0:
        # attract mode: the car cruises by itself behind the title
        dist += 0.14
        plat = 0.6 * sin(t * 0.025)
        cam = plat * 0.55
        bg += 0.25
        boosting = False
        if aEdge:
            reset()
            mode = 1

    elif mode == 1:
        stage = int(dist / 80)
        if stage != lastStage:
            lastStage = stage
            banner = 30
            beep(1200, 120)
        amp = min(0.6 + 0.1 * stage, 1.2)
        base = min(0.15 + 0.01 * stage, 0.24)

        # nitro
        boosting = padT > 0 or (a and nitro > 0)
        if padT > 0:
            padT -= 1
        elif boosting:
            nitro -= 1.0
        tgt = base + (0.11 if boosting else 0.0)
        if plat > 1.0 or plat < -1.0:
            tgt *= 0.6                          # grass slows you down
        speed += (tgt - speed) * 0.08

        # steering + centrifugal push in curves
        if kl:
            plat -= 0.07
        if kr:
            plat += 0.07
        cc = curve_at(dist + 1.2, amp)
        plat -= cc * speed * 0.18
        bg += cc * speed * 12.0
        sx = int(36 + OFF[PY] + (plat - cam) * HW[PY])
        if plat > 1.3 or plat < -1.3:           # slammed into the scenery
            plat = 1.0 if plat > 0 else -1.0
            if invul == 0:
                hit(sx, 30)
        cam += (plat * 0.55 - cam) * 0.2

        # jumping
        if jcool > 0:
            jcool -= 1
        if (b or ku) and not air and jcool == 0:
            air = True
            jv = 3.2
            beep(600, 40)
        if air:
            jh += jv
            jv -= 0.5
            if jh <= 0:
                jh = 0.0
                jv = 0.0
                air = False
                jcool = 15

        dist += speed

        # spawn traffic / coins
        while nextZ < dist + 27:
            n = spawn(nextZ)
            nextZ += n + max(3.0, 8.0 - stage * 0.5) * (0.6 + 0.8 * rnd())

        # collisions
        while objs and objs[0][0] - dist < 0.7:
            objs.pop(0)
        for o in objs:
            w = o[0] - dist
            if w > 1.45:
                break
            if w < 0.9 or o[3]:
                continue
            k = o[2]
            dx = abs(o[1] - plat)
            if k == 1:
                if dx < 0.42:
                    o[3] = 1
                    nitro = min(100.0, nitro + 6.0)
                    bonus += 10
                    beep(1900, 35)
            elif k == 2:
                if dx < 0.45:
                    o[3] = 1
                    padT = 75
                    beep(900, 120)
            elif k == 3 or dx < 0.34:
                if jh > 3.5:                    # hopped right over it
                    o[3] = 2
                    bonus += 15
                    nitro = min(100.0, nitro + 4.0)
                    beep(1400, 30)
                elif boosting:                  # nitro smash!
                    o[3] = 1
                    bonus += 25
                    burst(sx, 30, 10)
                    beep(260, 90)
                elif invul > 0:
                    o[3] = 3
                else:
                    o[3] = 1
                    hit(sx, 30)

        if invul > 0:
            invul -= 1
        if flash > 0:
            flash -= 1
        if banner > 0:
            banner -= 1
        score = int(dist * 5) + bonus

        if hearts <= 0:
            mode = 2
            overT = 0
            boosting = False
            newbest = score > hi
            if newbest:
                hi = score
                save_hi()

    else:
        overT += 1
        speed *= 0.95
        dist += speed
        if flash > 0:
            flash -= 1
        if aEdge and overT > 25:
            reset()
            mode = 1

    render()

    if mode == 1:
        draw_hud()
        if banner > 0 and flash == 0:
            panel(4, 13, 64, 19)
            text_c("STAGE %d" % (stage + 1), 15)
            text_c(NAMES[stage % 4], 23)
    elif mode == 0:
        panel(1, 3, 70, 34)
        text_c("TURBO DRIFT", 6)
        pg = (t // 70) % 3
        if pg == 0:
            if (t // 12) % 2 == 0:
                text_c("PRESS A", 17)
            text_c("BEST %d" % hi, 26)
        elif pg == 1:
            text_c("STEER L/R", 17)
            text_c("B/UP: JUMP", 26)
        else:
            text_c("A: NITRO", 17)
            text_c("SMASH CARS!", 26)
    else:
        draw_hud()
        panel(2, 5, 68, 30)
        text_c("CRASHED!", 8)
        text_c("%d PTS" % score, 17)
        if (t // 25) % 2 == 0:
            text_c("A: RETRY", 26)
        else:
            text_c("NEW BEST!" if newbest else "BEST %d" % hi, 26)

    d.update()
