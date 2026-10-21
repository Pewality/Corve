# HYPERLANE - pseudo-3D space-lane runner for the Thumby (MicroPython)
#
# Install: put this file at  /Games/Hyperlane/Hyperlane.py  on the Thumby
# (or paste it into the Thumby Code Editor at code.thumby.us and hit Run).
#
# Controls
#   LEFT / RIGHT : steer
#   A (hold)     : auto-fire laser (blocked by pillars!)
#   B            : DASH - hold a direction. Ghost through pillars, smash rocks/drones
#   DOWN (title) : sound on/off

import math
import random
import thumby

D = thumby.display
D.setFPS(30)

W = 72
H = 40
CX = 36
HOR = 12            # horizon row
PY = 34             # ground row at depth 1 (where the ship flies)
K = 28.0            # horizontal projection scale
GND = 22.0          # PY - HOR
EDGE = 1.15         # road half-width (world units)
ZF = 9.0            # spawn depth
CURVE_PX = 22.0
DASH_CD = 55
HW = (0.26, 0.28, 0.28, 0.28, 0.28)   # collision half-widths per entity type

# entity types: 0 rock, 1 pillar, 2 coin, 3 shield, 4 drone

# ---------------------------------------------------------------- save / sound
try:
    thumby.saveData.setName("Hyperlane")
except Exception:
    pass


def load_hi():
    try:
        if thumby.saveData.hasItem("hi"):
            return int(thumby.saveData.getItem("hi"))
    except Exception:
        pass
    return 0


def save_hi(v):
    try:
        thumby.saveData.setItem("hi", v)
        thumby.saveData.save()
    except Exception:
        pass


sound = True


def beep(f, ms=40):
    if not sound:
        return
    try:
        thumby.audio.play(int(f), int(ms))
    except Exception:
        pass


# ---------------------------------------------------------------- drawing helpers
ox = 0
oy = 0


def pix(x, y, c=1):
    x = int(x) + ox
    y = int(y) + oy
    if 0 <= x < W and 0 <= y < H:
        D.setPixel(x, y, c)


def frect(x, y, w, h, c=1):
    x = int(x) + ox
    y = int(y) + oy
    w = int(w)
    h = int(h)
    if w <= 0 or h <= 0:
        return
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    if x + w > W:
        w = W - x
    if y + h > H:
        h = H - y
    if w > 0 and h > 0:
        D.drawFilledRectangle(x, y, w, h, c)


def line(x0, y0, x1, y1, c=1):
    x0 = int(x0) + ox
    x1 = int(x1) + ox
    y0 = int(y0) + oy
    y1 = int(y1) + oy
    if 0 <= x0 < W and 0 <= x1 < W and 0 <= y0 < H and 0 <= y1 < H:
        D.drawLine(x0, y0, x1, y1, c)
        return
    if (x0 < 0 and x1 < 0) or (x0 >= W and x1 >= W) or (y0 < 0 and y1 < 0) or (y0 >= H and y1 >= H):
        return
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    n = 0
    while n < 400:
        n += 1
        if 0 <= x0 < W and 0 <= y0 < H:
            D.setPixel(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def text_c(s, y):
    D.drawText(s, (W - 6 * len(s)) // 2, y, 1)


HEART = ((1, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (2, 3))


def heart(x, y):
    for dx, dy in HEART:
        D.setPixel(x + dx, y + dy, 1)


# ---------------------------------------------------------------- perspective
curve = 0.0


def proj_x(x, d):
    u = 1.0 - 1.0 / d
    return CX + x * K / d + curve * CURVE_PX * u * u


def proj_y(d):
    return HOR + GND / d


# ---------------------------------------------------------------- game state
state = 0           # 0 title, 1 play, 2 game over
hi = load_hi()
new_hi = False
frame = 0
scroll = 0.0
stars = [[random.randint(0, W - 1), random.randint(0, HOR - 3)] for _ in range(16)]
SUN = []
for _dy in (0, 2, 4):
    SUN.append((_dy, int(math.sqrt(25 - _dy * _dy))))
EDGE_DS = (60.0, 20.0, 12.0, 8.0, 5.5, 4.0, 3.0, 2.3, 1.8, 1.4, 1.1, 0.9, 0.82)

px = 0.0
vx = 0.0
face = 1.0
spd = 0.05
curve_to = 0.0
curve_t = 120
score = 0
combo = 0
lives = 3
inv = 0
dash = 0
dash_dir = 1.0
dash_cd = 0
fire_cd = 0
laser = [0, 0, 0]
shake = 0
ents = []
parts = []
trail = []
dist = 0.0
next_spawn = 2.0
level = 1
lvl_t = 0
dead_t = -1
over_t = 0
first_spawn = True

a_prev = False
b_prev = False
dn_prev = False
a_hold = False
a_edge = False
b_edge = False
dn_edge = False


def read_buttons():
    global a_prev, b_prev, dn_prev, a_hold, a_edge, b_edge, dn_edge
    a_hold = thumby.buttonA.pressed()
    b_now = thumby.buttonB.pressed()
    dn_now = thumby.buttonD.pressed()
    a_edge = a_hold and not a_prev
    b_edge = b_now and not b_prev
    dn_edge = dn_now and not dn_prev
    a_prev = a_hold
    b_prev = b_now
    dn_prev = dn_now


def mult():
    return 1 + min(4, combo // 6)


def reset():
    global px, vx, face, spd, curve, curve_to, curve_t, frame, score, combo, lives
    global inv, dash, dash_dir, dash_cd, fire_cd, shake, dist, next_spawn
    global level, lvl_t, dead_t, new_hi, first_spawn, scroll
    px = 0.0
    vx = 0.0
    face = 1.0
    spd = 0.05
    curve = 0.0
    curve_to = 0.0
    curve_t = 120
    frame = 0
    scroll = 0.0
    score = 0
    combo = 0
    lives = 3
    inv = 0
    dash = 0
    dash_dir = 1.0
    dash_cd = 0
    fire_cd = 0
    shake = 0
    dist = 0.0
    next_spawn = 1.5
    level = 1
    lvl_t = 0
    dead_t = -1
    new_hi = False
    first_spawn = True
    laser[2] = 0
    del ents[:]
    del parts[:]
    del trail[:]


def burst(x, y, n):
    for i in range(n):
        if len(parts) > 40:
            break
        a = random.random() * 6.283
        s = random.random() * 1.6 + 0.3
        parts.append([x, y, math.cos(a) * s, math.sin(a) * s - 0.5, random.randint(6, 14)])


# ---------------------------------------------------------------- spawning
def spawn():
    global first_spawn
    if first_spawn:
        first_spawn = False
        for i in range(6):
            ents.append([2, 0.4 * math.sin(i * 0.8), ZF + i * 0.55, 1])
        return
    r = random.random()
    if r < 0.30:
        n = 1 + random.randint(0, min(2, level // 2))
        for i in range(n):
            ents.append([0, random.uniform(-0.85, 0.85), ZF + random.uniform(0, 0.8), 1])
    elif r < 0.55:
        g = random.uniform(-0.75, 0.75)
        thr = 0.3 if level < 6 else 0.22
        for i in range(-2, 3):
            x = i * 0.4
            if abs(x - g) > thr:
                ents.append([1, x, ZF, 1])
        if random.random() < 0.5:
            ents.append([2, g, ZF, 1])
            ents.append([2, g, ZF + 0.8, 1])
            ents.append([2, g, ZF + 1.6, 1])
    elif r < 0.80:
        cx = random.uniform(-0.5, 0.5)
        ph = random.uniform(0, 6)
        for i in range(6):
            x = cx + 0.45 * math.sin(ph + i * 0.7)
            x = max(-0.9, min(0.9, x))
            ents.append([2, x, ZF + i * 0.55, 1])
    elif r < 0.93 and level >= 2:
        n = 1
        if level >= 5:
            n = 2
        for i in range(n):
            ents.append([4, random.uniform(-0.8, 0.8), ZF + i * 1.0, 2])
    else:
        if lives < 3:
            ents.append([3, random.uniform(-0.7, 0.7), ZF, 1])
        else:
            for i in range(4):
                ents.append([2, -0.6 + i * 0.4, ZF + i * 0.4, 1])


# ---------------------------------------------------------------- actions
def hit():
    global lives, inv, shake, combo, dead_t
    lives -= 1
    combo = 0
    shake = 8
    burst(CX + px * K, 31, 14)
    beep(150, 120)
    if lives <= 0:
        dead_t = 45
        burst(CX + px * K, 31, 26)
    else:
        inv = 50


def fire():
    global score, combo
    best = None
    for e in ents:
        t = e[0]
        if t == 0 or t == 1 or t == 4:
            d = e[2]
            if d > 1.1 and d < ZF:
                hw = 0.3 if t == 1 else 0.26
                if abs(e[1] - px) < hw and (best is None or d < best[2]):
                    best = e
    beep(1500, 15)
    if best is None:
        laser[0] = proj_x(px, ZF)
        laser[1] = proj_y(ZF)
        laser[2] = 2
        return
    d = best[2]
    ex = proj_x(best[1], d)
    ey = proj_y(d) - 0.2 * K / d
    laser[0] = ex
    laser[1] = ey
    laser[2] = 2
    if best[0] == 1:
        burst(ex, ey, 2)
        return
    best[3] -= 1
    if best[3] <= 0:
        best[2] = -9.0
        combo += 1
        score += (25 if best[0] == 4 else 10) * mult()
        burst(ex, ey, 12)
        beep(500, 50)
    else:
        burst(ex, ey, 3)


# ---------------------------------------------------------------- entity drawing
def draw_ent(e):
    t = e[0]
    d = e[2]
    if d > 9.5 or d < 0.7:
        return
    s = 1.0 / d
    sx = proj_x(e[1], d)
    gy = proj_y(d)
    if t == 0:
        r = max(1, int(0.17 * K * s))
        frect(sx - r, gy - 2 * r, 2 * r + 1, 2 * r, 1)
        if r >= 3:
            pix(sx - r, gy - 2 * r, 0)
            pix(sx + r, gy - 2 * r, 0)
            pix(sx - r, gy - 1, 0)
            pix(sx + r, gy - 1, 0)
        if r >= 4:
            line(sx - 1, gy - 2 * r + 2, sx, gy - r, 0)
            line(sx, gy - r, sx + 2, gy - r + 2, 0)
    elif t == 1:
        w = max(2, int(0.42 * K * s))
        h = max(2, int(0.6 * K * s))
        x0 = int(sx - w / 2)
        frect(x0, gy - h, w, h, 1)
        if w >= 5:
            yy = gy - h + 2
            while yy < gy - 1:
                frect(x0 + 1, yy, w - 2, 1, 0)
                yy += 3
    elif t == 2:
        r = max(1, int(0.1 * K * s))
        rw = r if (frame // 4) % 2 == 0 else max(1, r - 1)
        cy = gy - int(0.3 * K * s) - r
        if r <= 1:
            pix(sx, cy)
        else:
            line(sx, cy - r, sx + rw, cy)
            line(sx + rw, cy, sx, cy + r)
            line(sx, cy + r, sx - rw, cy)
            line(sx - rw, cy, sx, cy - r)
            pix(sx, cy)
        pix(sx, gy)
    elif t == 3:
        r = max(2, int(0.14 * K * s))
        cy = gy - int(0.3 * K * s) - r
        if (frame // 3) % 4 != 0:
            frect(sx - r, cy - r, 2 * r + 1, 1)
            frect(sx - r, cy + r, 2 * r + 1, 1)
            frect(sx - r, cy - r, 1, 2 * r + 1)
            frect(sx + r, cy - r, 1, 2 * r + 1)
            line(sx - r // 2, cy, sx + r // 2, cy)
            line(sx, cy - r // 2, sx, cy + r // 2)
        pix(sx, gy)
    else:
        bw = max(2, int(0.2 * K * s))
        bh = max(1, int(0.12 * K * s))
        ws = int(0.3 * K * s) + 1
        bob = int(math.sin(frame * 0.3 + e[1] * 5) * s * 1.5)
        cy = gy - int(0.35 * K * s) + bob
        frect(sx - bw // 2, cy - bh // 2, bw, bh, 1)
        line(sx - bw // 2 - ws, cy - ws // 2, sx - bw // 2, cy)
        line(sx + bw // 2 + ws, cy - ws // 2, sx + bw // 2, cy)
        if bw >= 3 and (frame // 5) % 2 == 0:
            pix(sx, cy, 0)
        line(sx - bw // 2, gy, sx + bw // 2, gy)


def draw_ship(x, y, t):
    x = int(x)
    nose_y = y - 5
    lw_y = y + 2 - t
    rw_y = y + 2 + t
    line(x, nose_y, x - 5, lw_y)
    line(x, nose_y, x + 5, rw_y)
    line(x - 5, lw_y, x, y + 1)
    line(x + 5, rw_y, x, y + 1)
    frect(x - 1, y - 2, 3, 3, 1)
    pix(x, y - 1, 0)
    if frame & 1:
        line(x, y + 2, x, y + 4)
    else:
        pix(x, y + 2)


def draw_road():
    for i in range(len(stars)):
        s = stars[i]
        if (frame + i * 7) % 37 > 1:
            pix((s[0] - int(curve * 8)) % W, s[1])
    sunx = int(CX + curve * 22)
    for dy, hw in SUN:
        line(sunx - hw, HOR - 1 - dy, sunx + hw, HOR - 1 - dy)
    line(0, HOR, W - 1, HOR)
    plx = 0
    ply = 0
    prx = 0
    first = True
    for d in EDGE_DS:
        y = proj_y(d)
        xl = proj_x(-EDGE, d)
        xr = proj_x(EDGE, d)
        if not first:
            line(plx, ply, xl, y)
            line(prx, ply, xr, y)
        first = False
        plx = xl
        prx = xr
        ply = y
    fr = scroll % 1.0
    base = int(scroll)
    for i in range(9):
        d = i + 1 - fr
        if d < 0.82:
            continue
        y = proj_y(d)
        xl = proj_x(-EDGE, d)
        xr = proj_x(EDGE, d)
        if (base + i) % 2 == 0:
            line(xl, y, xr, y)
        ph = int(0.28 * K / d) + 1
        line(xl, y, xl, y - ph)
        line(xr, y, xr, y - ph)


# ---------------------------------------------------------------- states
def title():
    global state, sound, scroll, curve, frame
    frame += 1
    scroll += 0.06
    curve = 0.7 * math.sin(frame * 0.02)
    draw_road()
    frect(0, 0, W, 17, 0)
    line(0, 17, W - 1, 17)
    D.drawText("HYPERLANE", 9, 1, 1)
    D.drawText("HYPERLANE", 10, 1, 1)
    ph = (frame // 40) % 3
    if ph == 0:
        text_c("A:PLAY", 9)
    elif ph == 1:
        text_c("BEST " + str(hi), 9)
    else:
        text_c("D:SND ON" if sound else "D:SND OFF", 9)
    draw_ship(36, 32 + int(math.sin(frame * 0.1) * 1.5), 0)
    if dn_edge:
        sound = not sound
        beep(800, 40)
    if a_edge:
        reset()
        state = 1
        beep(900, 60)


def gameover():
    global state, scroll, curve, frame, over_t
    frame += 1
    over_t += 1
    scroll += 0.03
    curve = 0.5 * math.sin(frame * 0.02)
    draw_road()
    frect(4, 1, 64, 38, 0)
    D.drawRectangle(4, 1, 64, 38, 1)
    text_c("GAME OVER", 4)
    text_c("SCORE " + str(score), 13)
    if new_hi and (frame // 6) % 2 == 0:
        text_c("NEW BEST!", 22)
    elif not new_hi:
        text_c("BEST " + str(hi), 22)
    if (frame // 40) % 2 == 0:
        text_c("A:RETRY", 30)
    else:
        text_c("B:MENU", 30)
    if over_t > 25:
        if a_edge:
            reset()
            state = 1
            beep(900, 60)
        elif b_edge:
            state = 0


def play():
    global state, px, vx, face, spd, scroll, curve, curve_to, curve_t, frame, score, combo
    global inv, dash, dash_dir, dash_cd, fire_cd, shake, dist, next_spawn
    global level, lvl_t, dead_t, hi, new_hi, over_t, ox, oy

    frame += 1
    alive = dead_t < 0

    # level / speed ramp
    nl = 1 + frame // 450
    if nl > level:
        level = nl
        lvl_t = 50
        beep(1000, 100)
    target = min(0.12, 0.05 + 0.005 * level)
    if dash > 0:
        target += 0.05
    if not alive:
        target *= 0.25
    spd += (target - spd) * 0.2
    scroll += spd
    dist += spd

    # curve
    curve_t -= 1
    if curve_t <= 0:
        curve_t = random.randint(120, 260)
        curve_to = random.uniform(-1.0, 1.0) if level > 1 else random.uniform(-0.4, 0.4)
    curve += (curve_to - curve) * 0.02

    # player
    if alive:
        tx = 0.0
        if thumby.buttonL.pressed():
            tx -= 1.0
        if thumby.buttonR.pressed():
            tx += 1.0
        if tx != 0.0:
            face = tx
        if dash > 0:
            vx = dash_dir * 0.10
            dash -= 1
        else:
            vx += (tx * 0.08 - vx) * 0.35
            if dash_cd > 0:
                dash_cd -= 1
            elif b_edge:
                dash = 8
                dash_cd = DASH_CD
                if tx != 0.0:
                    dash_dir = tx
                else:
                    dash_dir = -1.0 if px > 0 else 1.0
                beep(300, 60)
        px += vx - curve * 0.01
        if px > 1.0:
            px = 1.0
        elif px < -1.0:
            px = -1.0
        if inv > 0:
            inv -= 1
        if fire_cd > 0:
            fire_cd -= 1
        if a_hold and fire_cd <= 0:
            fire()
            fire_cd = 6
        if dash > 0:
            trail.append(CX + px * K)
            if len(trail) > 5:
                trail.pop(0)
        elif trail:
            trail.pop(0)
        if frame % 15 == 0:
            score += mult()

    # spawning
    if alive and dist >= next_spawn:
        spawn()
        next_spawn = dist + max(2.0, 3.8 - 0.14 * level) * random.uniform(0.8, 1.3)

    # world update
    keep = []
    dr = min(0.02, 0.006 + 0.0008 * level)
    for e in ents:
        e[2] -= spd
        t = e[0]
        d = e[2]
        if d < 0.7:
            continue
        if t == 4 and d > 1.6:
            dx = px - e[1]
            if dx > dr:
                dx = dr
            elif dx < -dr:
                dx = -dr
            e[1] += dx
        if alive and 0.75 < d < 1.2 and abs(e[1] - px) < HW[t]:
            if t == 2:
                combo += 1
                score += 5 * mult()
                burst(CX + px * K, 30, 3)
                beep(700 + min(combo, 12) * 60, 30)
                continue
            elif t == 3:
                if lives < 3:
                    lives_up()
                else:
                    score += 50 * mult()
                beep(1200, 120)
                continue
            else:
                if dash > 0:
                    if t != 1:
                        combo += 1
                        score += (25 if t == 4 else 10) * mult()
                        burst(CX + px * K, 28, 10)
                        beep(450, 50)
                        continue
                elif inv > 0:
                    pass
                else:
                    hit()
                    continue
        keep.append(e)
    ents[:] = keep

    # particles
    kp = []
    for p in parts:
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.12
        p[4] -= 1
        if p[4] > 0:
            kp.append(p)
    parts[:] = kp

    # shake
    if shake > 0:
        ox = random.randint(-1, 1)
        oy = random.randint(-1, 1)
        shake -= 1
    else:
        ox = 0
        oy = 0

    # ---- draw
    draw_road()
    ents.sort(key=lambda q: -q[2])
    for e in ents:
        draw_ent(e)
    for p in parts:
        pix(p[0], p[1])
    sxp = CX + px * K
    if laser[2] > 0:
        line(sxp, 29, laser[0], laser[1])
        laser[2] -= 1
    if dead_t < 0 or dead_t > 40:
        if inv <= 0 or (frame // 2) % 2 == 0 or dash > 0:
            tilt = 1 if vx > 0.03 else (-1 if vx < -0.03 else 0)
            draw_ship(sxp, 33, tilt)
        for tx2 in trail:
            line(tx2 - 1, 33, tx2 + 1, 33)

    ox = 0
    oy = 0
    # HUD
    for i in range(lives):
        heart(1 + i * 6, 1)
    st = str(score)
    D.drawText(st, W - 6 * len(st) - 1, 1, 1)
    if mult() > 1:
        D.drawText("x" + str(mult()), 21, 1, 1)
    # dash meter
    if dash_cd > 0:
        ln = int(W * (1.0 - dash_cd / DASH_CD))
    else:
        ln = W
    if ln > 0:
        D.drawLine(0, 39, ln - 1, 39, 1)
    if frame < 110:
        text_c("A:FIRE", 14)
        text_c("B:DASH", 22)
    if lvl_t > 0:
        lvl_t -= 1
        if (lvl_t // 4) % 2 == 0:
            frect(8, 15, 56, 9, 0)
            text_c("SPEED UP!", 16)

    # death
    if dead_t > 0:
        dead_t -= 1
        if dead_t == 0:
            state = 2
            over_t = 0
            if score > hi:
                hi = score
                new_hi = True
                save_hi(hi)


def lives_up():
    global lives
    lives += 1


# ---------------------------------------------------------------- main loop
reset()
state = 0
while True:
    D.fill(0)
    read_buttons()
    if state == 0:
        title()
    elif state == 1:
        play()
    else:
        gameover()
    D.update()
