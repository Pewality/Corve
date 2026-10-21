# DELVER - top-down roguelike dungeon crawler for the Thumby (MicroPython)
#
# Install: put this file at  /Games/Delver/Delver.py  on the Thumby
# (or paste it into the Thumby Code Editor at code.thumby.us and hit Run).
#
# Controls
#   D-PAD     : move (8 directions) - you face the way you walk
#   A (hold)  : sword slash. Slashing an ARROW REFLECTS it back at enemies!
#   B         : dash roll (invincible while rolling)
#   DOWN      : (title screen) sound on/off
#
# Clear every room, walk out the right door. Every 5th room is a BOSS.
# Altar rooms let you choose 1 of 2 permanent upgrades.

import math
import random
import thumby

D = thumby.display
D.setFPS(30)

W = 72
H = 40

SL, BA, AR, CH, BO = 0, 1, 2, 3, 4
RAD = (3.0, 2.5, 3.0, 3.5, 6.0)
HPS = (2, 1, 2, 3, 16)

# ---------------------------------------------------------------- save / sound
try:
    thumby.saveData.setName("Delver")
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


# ---------------------------------------------------------------- draw helpers
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
    while n < 300:
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


def norm(dx, dy):
    d = math.sqrt(dx * dx + dy * dy)
    if d < 0.001:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


HEART = ((1, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (2, 3))
HEART_E = ((1, 0), (3, 0), (0, 1), (4, 1), (1, 2), (3, 2), (2, 3))


def heart(x, y, full):
    x = int(x)
    y = int(y)
    for dx, dy in (HEART if full else HEART_E):
        px_ = x + dx + ox
        py_ = y + dy + oy
        if 0 <= px_ < W and 0 <= py_ < H:
            D.setPixel(px_, py_, 1)


ICONS = (
    (".X.X.", "XXXXX", "XXXXX", ".XXX.", "..X.."),   # +max hp
    ("....X", "...X.", "X.X..", ".X...", "X.X.."),   # power
    ("..X..", ".XXX.", "X.X.X", "..X..", "..X.."),   # swift
    (".XXX.", "X...X", "X...X", "X...X", ".XXX."),   # wide
    ("...XX", "..XX.", ".XXXX", "..XX.", ".XX.."),   # dash
    ("..X..", "..X..", "XXXXX", "..X..", "..X.."),   # heal
)
NAMES = ("+MAX HP", "POWER UP", "SWIFT", "WIDE SLASH", "FAST DASH", "FULL HEAL")


def icon(k, x, y):
    g = ICONS[k]
    for j in range(5):
        row = g[j]
        for i in range(5):
            if row[i] == "X":
                pix(x + i, y + j)


# ---------------------------------------------------------------- state
state = 0           # 0 title, 1 play, 2 game over
hi = load_hi()
new_hi = False
frame = 0

px = 7.0
py = 25.0
fx = 1.0
fy = 0.0
hp = 3
maxhp = 3
pdmg = 1
pspeed = 1.1
reach = 0
moving = False
dash_t = 0
dash_cd = 0
dash_cd_max = 42
ddx = 1.0
ddy = 0.0
att_t = 0
att_cd = 0
inv = 0
pkx = 0.0
pky = 0.0
freeze = 0
shake = 0
dead_t = -1
score = 0
r = 0
room_type = 0       # 0 normal, 1 altar, 2 boss
cleared = False
reward = False
banner_t = 0
banner_s = ""

enemies = []
bullets = []
pickups = []
altars = []
pillars = []
parts = []
trail = []

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


# ---------------------------------------------------------------- collision
def blocked(x, y, hw, fly=False, pl=False):
    if y - hw < 10 or y + hw > 38 or x - hw < 2:
        return True
    if x + hw > 70:
        if not (pl and cleared and y - hw >= 19 and y + hw <= 31 and x < 77):
            return True
    if not fly:
        for p in pillars:
            if x + hw > p[0] and x - hw < p[0] + p[2] and y + hw > p[1] and y - hw < p[1] + p[3]:
                return True
    return False


def pmove(dx, dy):
    global px, py
    nx = px + dx
    if not blocked(nx, py, 2.5, False, True):
        px = nx
    ny = py + dy
    if not blocked(px, ny, 2.5, False, True):
        py = ny


def emove(e, dx, dy):
    rr = RAD[e[0]]
    fly = e[0] == BA
    ok = True
    nx = e[1] + dx
    if not blocked(nx, e[2], rr, fly):
        e[1] = nx
    else:
        ok = False
    ny = e[2] + dy
    if not blocked(e[1], ny, rr, fly):
        e[2] = ny
    else:
        ok = False
    return ok


# ---------------------------------------------------------------- effects
def burst(x, y, n):
    for i in range(n):
        if len(parts) > 40:
            break
        a = random.random() * 6.283
        s = random.random() * 1.8 + 0.3
        parts.append([x, y, math.cos(a) * s, math.sin(a) * s, random.randint(6, 14)])


def banner(s, t=40):
    global banner_s, banner_t
    banner_s = s
    banner_t = t


# ---------------------------------------------------------------- rooms
def add_enemy(t, x, y):
    h = HPS[t]
    if t == BO:
        h = 16 + 4 * (r // 5)
    elif t != BA:
        h += r // 8
    enemies.append([t, x, y, h, 0.0, 0.0, 0, 0, 0, 20 + random.randint(0, 20), 0.0, 0.0, h])


def place_ok(x, y, hw):
    return not blocked(x, y, hw)


def add_altars():
    pool = [0, 1, 2, 3, 4, 5]
    if maxhp >= 6:
        pool.remove(0)
    k1 = pool.pop(random.randint(0, len(pool) - 1))
    k2 = pool.pop(random.randint(0, len(pool) - 1))
    altars.append([k1, 46, 19])
    altars.append([k2, 46, 31])


def gen_room():
    global r, room_type, cleared, reward, px, py
    r += 1
    del enemies[:]
    del bullets[:]
    del pickups[:]
    del altars[:]
    del pillars[:]
    del trail[:]
    cleared = False
    reward = False
    px = 7.0
    py = 25.0
    if r % 5 == 0:
        room_type = 2
        add_enemy(BO, 54.0, 24.0)
        banner("BOSS!", 50)
        beep(200, 200)
        return
    if r % 5 == 3:
        room_type = 1
        add_altars()
        banner("CHOOSE ONE", 50)
        return
    room_type = 0
    banner("ROOM " + str(r), 35)
    if r > 1:
        for i in range(random.randint(0, 3)):
            for tries in range(12):
                w = 6
                x = random.randint(16, 54)
                y = random.randint(12, 30)
                ok = True
                for p in pillars:
                    if abs(p[0] - x) < 10 and abs(p[1] - y) < 10:
                        ok = False
                if ok:
                    pillars.append([x, y, w, w])
                    break
    budget = 2 + r // 2
    if budget > 9:
        budget = 9
    n = 0
    while budget > 0 and n < 7:
        opts = [SL]
        if r >= 2:
            opts.append(BA)
        if r >= 4:
            opts.append(AR)
        if r >= 6:
            opts.append(CH)
        t = opts[random.randint(0, len(opts) - 1)]
        cost = 2 if (t == AR or t == CH) else 1
        if cost > budget:
            t = SL
            cost = 1
        for tries in range(20):
            x = random.randint(26, 64)
            y = random.randint(14, 34)
            if place_ok(x, y, 5):
                add_enemy(t, float(x), float(y))
                break
        budget -= cost
        n += 1


def reset():
    global px, py, fx, fy, hp, maxhp, pdmg, pspeed, reach, dash_t, dash_cd, dash_cd_max
    global att_t, att_cd, inv, pkx, pky, freeze, shake, dead_t, score, r, new_hi, frame
    px = 7.0
    py = 25.0
    fx = 1.0
    fy = 0.0
    hp = 3
    maxhp = 3
    pdmg = 1
    pspeed = 1.1
    reach = 0
    dash_t = 0
    dash_cd = 0
    dash_cd_max = 42
    att_t = 0
    att_cd = 0
    inv = 0
    pkx = 0.0
    pky = 0.0
    freeze = 0
    shake = 0
    dead_t = -1
    score = 0
    r = 0
    new_hi = False
    frame = 0
    del parts[:]
    gen_room()


def apply_up(k):
    global maxhp, hp, pdmg, pspeed, reach, dash_cd_max
    if k == 0:
        maxhp = min(6, maxhp + 1)
        hp = min(maxhp, hp + 1)
    elif k == 1:
        pdmg += 1
    elif k == 2:
        pspeed += 0.15
    elif k == 3:
        reach += 2
    elif k == 4:
        dash_cd_max = max(16, dash_cd_max - 10)
    else:
        hp = maxhp


# ---------------------------------------------------------------- combat
def hurt(sx, sy):
    global hp, inv, shake, freeze, pkx, pky, dead_t
    if inv > 0 or dash_t > 0 or dead_t >= 0:
        return
    hp -= 1
    inv = 50
    shake = 6
    freeze = 4
    ux, uy, d = norm(px - sx, py - sy)
    if d < 0.01:
        ux = 1.0
    pkx = ux * 3.2
    pky = uy * 3.2
    burst(px, py, 6)
    beep(160, 100)
    if hp <= 0:
        dead_t = 50
        burst(px, py, 26)
        beep(110, 250)


def do_slash():
    global freeze
    rr = 8 + reach
    hit = False
    for e in enemies:
        if e[9] > 0:
            continue
        ux, uy, d = norm(e[1] - px, e[2] - py)
        if d < rr + RAD[e[0]] and (ux * fx + uy * fy) > 0.3:
            dmg = pdmg
            if (e[0] == CH or e[0] == BO) and e[7] == 3:
                dmg += 1
            e[3] -= dmg
            e[8] = 6
            kb = 1.2 if e[0] == BO else 3.6
            e[4] = ux * kb
            e[5] = uy * kb
            hit = True
    for b in bullets:
        if b[4] == 0:
            ux, uy, d = norm(b[0] - px, b[1] - py)
            if d < rr + 2 and (ux * fx + uy * fy) > 0.2:
                b[4] = 1
                b[2] = fx * 1.7
                b[3] = fy * 1.7
                hit = True
                beep(1300, 30)
    if hit:
        freeze = 2
        beep(700, 30)
    else:
        beep(350, 20)


def kill_enemy(e):
    global score, shake
    t = e[0]
    score += 25 if t == BO else 10
    burst(e[1], e[2], 14 if t == BO else 8)
    beep(500, 60)
    if t == BO:
        shake = 12
        pickups.append([0, e[1], e[2]])
        return
    roll = random.random()
    if roll < (0.2 if hp < maxhp else 0.06):
        pickups.append([0, e[1], e[2]])
    elif roll < 0.55:
        pickups.append([1, e[1], e[2]])


def upd_enemy(e):
    global shake
    t = e[0]
    if e[9] > 0:
        e[9] -= 1
        return
    if e[8] > 0:
        e[8] -= 1
    if abs(e[4]) > 0.15 or abs(e[5]) > 0.15:
        emove(e, e[4], e[5])
        e[4] *= 0.72
        e[5] *= 0.72
    ux, uy, d = norm(px - e[1], py - e[2])
    e[6] += 1
    if t == SL:
        if (e[6] // 14) % 2 == 0:
            s = 0.32 + 0.015 * min(r, 16)
            emove(e, ux * s, uy * s)
    elif t == BA:
        e[7] -= 1
        if e[7] <= 0:
            e[7] = random.randint(18, 36)
            a = math.atan2(uy, ux) + random.uniform(-1.4, 1.4)
            e[10] = math.cos(a)
            e[11] = math.sin(a)
        if not emove(e, e[10] * 0.85, e[11] * 0.85):
            e[7] = 0
    elif t == AR:
        if e[10] == 0:
            e[10] = 1.0 if random.random() < 0.5 else -1.0
        if d < 22:
            emove(e, -ux * 0.3, -uy * 0.3)
        elif d > 34:
            emove(e, ux * 0.3, uy * 0.3)
        else:
            if not emove(e, -uy * 0.25 * e[10], ux * 0.25 * e[10]):
                e[10] = -e[10]
        if e[6] >= 95:
            e[6] = random.randint(0, 20)
            bullets.append([e[1], e[2], ux * 1.1, uy * 1.1, 0])
            beep(260, 25)
    elif t == CH:
        st = e[7]
        if st == 0:
            emove(e, ux * 0.3, uy * 0.3)
            if e[6] > 55:
                e[7] = 1
                e[6] = 0
        elif st == 1:
            if e[6] >= 22:
                e[10] = ux
                e[11] = uy
                e[7] = 2
                e[6] = 0
        elif st == 2:
            ok = emove(e, e[10] * 2.3, e[11] * 2.3)
            if (not ok) or e[6] > 26:
                if not ok:
                    shake = 4
                e[7] = 3
                e[6] = 0
        else:
            if e[6] > 40:
                e[7] = 0
                e[6] = 0
    else:
        st = e[7]
        enraged = e[3] * 2 < e[12]
        if st == 0:
            s = 0.5 if enraged else 0.35
            emove(e, ux * s, uy * s)
            if e[6] > (55 if enraged else 70):
                e[6] = 0
                e[7] = 1 if random.random() < 0.55 else 4
        elif st == 1:
            if e[6] >= 26:
                e[10] = ux
                e[11] = uy
                e[7] = 2
                e[6] = 0
        elif st == 2:
            ok = emove(e, e[10] * 2.4, e[11] * 2.4)
            if (not ok) or e[6] > 34:
                if not ok:
                    shake = 7
                e[7] = 3
                e[6] = 0
        elif st == 3:
            if e[6] > 30:
                e[7] = 0
                e[6] = 0
        else:
            if e[6] == 1 or e[6] == 16:
                n = 12 if enraged else 8
                off = 0.0 if e[6] == 1 else 3.1416 / n
                for i in range(n):
                    a = off + 6.2832 * i / n
                    bullets.append([e[1], e[2], math.cos(a), math.sin(a), 0])
                beep(220, 40)
            if e[6] > 34:
                e[7] = 0
                e[6] = 0


# ---------------------------------------------------------------- update
def update():
    global px, py, fx, fy, moving, dash_t, dash_cd, ddx, ddy, att_t, att_cd, inv, pkx, pky
    global shake, freeze, dead_t, score, cleared, reward, banner_t, hp, state, hi, new_hi

    if dead_t >= 0:
        kp = []
        for p in parts:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.9
            p[3] *= 0.9
            p[4] -= 1
            if p[4] > 0:
                kp.append(p)
        parts[:] = kp
        if dead_t > 0:
            dead_t -= 1
            if dead_t == 0:
                state = 2
                if score > hi:
                    hi = score
                    new_hi = True
                    save_hi(hi)
        return

    # ---- input / movement
    dx = 0.0
    dy = 0.0
    if thumby.buttonL.pressed():
        dx -= 1.0
    if thumby.buttonR.pressed():
        dx += 1.0
    if thumby.buttonU.pressed():
        dy -= 1.0
    if thumby.buttonD.pressed():
        dy += 1.0
    ux, uy, d = norm(dx, dy)
    moving = d > 0
    if moving:
        fx = ux
        fy = uy

    if dash_t > 0:
        dash_t -= 1
        pmove(ddx * 3.0, ddy * 3.0)
        trail.append((px, py))
        if len(trail) > 4:
            trail.pop(0)
    else:
        if trail:
            trail.pop(0)
        if moving:
            pmove(ux * pspeed, uy * pspeed)
        if b_edge and dash_cd <= 0:
            dash_t = 7
            dash_cd = dash_cd_max
            if moving:
                ddx = ux
                ddy = uy
            else:
                ddx = fx
                ddy = fy
            beep(260, 50)
    if dash_cd > 0 and dash_t <= 0:
        dash_cd -= 1

    if abs(pkx) > 0.2 or abs(pky) > 0.2:
        pmove(pkx, pky)
        pkx *= 0.7
        pky *= 0.7

    # ---- attack
    if att_t > 0:
        att_t -= 1
    if att_cd > 0:
        att_cd -= 1
    if a_hold and att_cd <= 0 and dash_t <= 0:
        att_t = 6
        att_cd = 15
        do_slash()

    if inv > 0:
        inv -= 1

    # ---- enemies
    for e in enemies:
        upd_enemy(e)
    alive = []
    for e in enemies:
        if e[3] <= 0:
            kill_enemy(e)
        else:
            alive.append(e)
    enemies[:] = alive
    for e in enemies:
        if e[9] > 0:
            continue
        if (e[0] == CH or e[0] == BO) and e[7] == 3:
            continue
        ex = e[1] - px
        ey = e[2] - py
        if ex * ex + ey * ey < (RAD[e[0]] + 2.5) * (RAD[e[0]] + 2.5):
            hurt(e[1], e[2])

    # ---- bullets
    kb = []
    for b in bullets:
        b[0] += b[2]
        b[1] += b[3]
        if b[0] < 2 or b[0] > 70 or b[1] < 10 or b[1] > 38:
            continue
        gone = False
        for p in pillars:
            if p[0] <= b[0] <= p[0] + p[2] and p[1] <= b[1] <= p[1] + p[3]:
                gone = True
        if gone:
            continue
        if b[4] == 0:
            ex = b[0] - px
            ey = b[1] - py
            if ex * ex + ey * ey < 12:
                if dash_t > 0 or inv > 0:
                    kb.append(b)
                    continue
                hurt(b[0], b[1])
                continue
        else:
            for e in enemies:
                if e[9] > 0:
                    continue
                ex = b[0] - e[1]
                ey = b[1] - e[2]
                rr = RAD[e[0]] + 1.5
                if ex * ex + ey * ey < rr * rr:
                    e[3] -= 1
                    e[8] = 4
                    gone = True
                    burst(b[0], b[1], 3)
                    beep(800, 20)
                    break
            if gone:
                continue
        kb.append(b)
    bullets[:] = kb

    # ---- pickups
    kp = []
    for p in pickups:
        ex = p[1] - px
        ey = p[2] - py
        if ex * ex + ey * ey < 28:
            if p[0] == 0:
                if hp < maxhp:
                    hp += 1
                else:
                    score += 5
                beep(900, 60)
            else:
                score += 10
                beep(1200, 30)
        else:
            kp.append(p)
    pickups[:] = kp

    # ---- altars
    if altars:
        for a in altars:
            ex = a[1] - px
            ey = a[2] - py
            if ex * ex + ey * ey < 49:
                apply_up(a[0])
                banner(NAMES[a[0]], 45)
                beep(1000, 150)
                del altars[:]
                cleared = True
                score += 25
                break

    # ---- room clear
    if room_type == 0 and not cleared and not enemies:
        cleared = True
        score += 25
        banner("CLEAR!", 30)
        beep(800, 120)
    if room_type == 2 and not enemies and not reward:
        reward = True
        add_altars()
        banner("CHOOSE ONE", 50)

    # ---- exit
    if cleared and px > 73:
        gen_room()

    # ---- particles
    kp = []
    for p in parts:
        p[0] += p[2]
        p[1] += p[3]
        p[2] *= 0.9
        p[3] *= 0.9
        p[4] -= 1
        if p[4] > 0:
            kp.append(p)
    parts[:] = kp


# ---------------------------------------------------------------- drawing
def draw_player(x, y, fxx, fyy, mv, at, show=True):
    x = int(x)
    y = int(y)
    af = math.atan2(fyy, fxx)
    if show:
        frect(x - 1, y - 3, 3, 2)
        frect(x - 2, y - 1, 5, 3)
        leg = (frame // 4) % 2 if mv else 0
        pix(x - 1 + leg, y + 2)
        pix(x + 1 - leg, y + 2)
        ex = 1 if fxx > 0.3 else (-1 if fxx < -0.3 else 0)
        pix(x + ex, y - 2, 0)
    rr = 8 + reach
    if at > 0:
        a = -1.0 + 2.0 * (6 - at) / 5.0
        aa = af + a
        line(x + math.cos(aa) * 3, y + math.sin(aa) * 3, x + math.cos(aa) * rr, y + math.sin(aa) * rr)
        for k in (1, 2, 3):
            ab = aa - 0.35 * k
            pix(x + math.cos(ab) * rr, y + math.sin(ab) * rr)
    elif show:
        line(x + fxx * 3, y + fyy * 3, x + fxx * 6, y + fyy * 6)


def draw_slime(x, y, squash):
    x = int(x)
    y = int(y)
    frect(x - 2, y - 2 + squash, 5, 1)
    frect(x - 3, y - 1 + squash, 7, 4 - squash)
    pix(x - 1, y - 1 + squash, 0)
    pix(x + 1, y - 1 + squash, 0)


def draw_enemy(e):
    t = e[0]
    x = int(e[1])
    y = int(e[2])
    if e[9] > 0:
        if (frame // 2) % 2 == 0:
            pix(x, y)
            pix(x - 1, y)
            pix(x + 1, y)
            pix(x, y - 1)
            pix(x, y + 1)
        return
    rr = int(RAD[t])
    if e[8] > 0:
        frect(x - rr, y - rr, 2 * rr + 1, 2 * rr + 1)
        return
    if t == SL:
        draw_slime(x, y, (e[6] // 14) % 2)
    elif t == BA:
        frect(x - 1, y - 1, 3, 2)
        if (frame // 3) % 2 == 0:
            line(x - 1, y - 1, x - 4, y - 3)
            line(x + 1, y - 1, x + 4, y - 3)
        else:
            line(x - 1, y, x - 4, y + 1)
            line(x + 1, y, x + 4, y + 1)
    elif t == AR:
        frect(x - 2, y - 3, 5, 6)
        frect(x - 1, y - 2, 3, 2, 0)
        pix(x, y - 1)
        ux, uy, d = norm(px - e[1], py - e[2])
        pix(x + (3 if ux > 0 else -3), y - 1)
        pix(x + (3 if ux > 0 else -3), y)
        pix(x + (3 if ux > 0 else -3), y + 1)
        if e[6] > 75:
            for k in range(1, 6):
                pix(x + ux * k * 3, y + uy * k * 3)
    elif t == CH:
        st = e[7]
        if st == 1 and (frame // 2) % 2 == 0:
            frect(x - 3, y - 2, 7, 5, 0)
            line(x - 3, y - 2, x + 3, y - 2)
            line(x - 3, y + 2, x + 3, y + 2)
        else:
            frect(x - 3, y - 2, 7, 5)
            pix(x - 4, y - 3)
            pix(x + 4, y - 3)
            pix(x - 1, y - 1, 0)
            pix(x + 1, y - 1, 0)
        if st == 3:
            pix(x - 2 + (frame // 4) % 5, y - 5)
    else:
        st = e[7]
        if st == 1 and (frame // 2) % 2 == 0:
            frect(x - 6, y - 6, 13, 12, 0)
            line(x - 6, y - 6, x + 6, y - 6)
            line(x - 6, y + 5, x + 6, y + 5)
            line(x - 6, y - 6, x - 6, y + 5)
            line(x + 6, y - 6, x + 6, y + 5)
        else:
            frect(x - 6, y - 6, 13, 12)
            frect(x - 4, y - 3, 3, 3, 0)
            frect(x + 2, y - 3, 3, 3, 0)
            line(x - 3, y + 3, x + 3, y + 3, 0)
            pix(x - 1, y + 4, 0)
            pix(x + 1, y + 4, 0)
        if st == 3:
            for k in range(3):
                pix(x - 4 + k * 4 + (frame // 4) % 3, y - 8)


def draw_field():
    for xx in range(6, 70, 8):
        for yy in range(14, 38, 8):
            pix(xx, yy)
    frect(0, 8, 72, 2)
    frect(0, 38, 72, 2)
    frect(0, 8, 2, 32)
    if cleared:
        frect(70, 8, 2, 11)
        frect(70, 31, 2, 9)
        if (frame // 8) % 2 == 0:
            line(64, 22, 67, 25)
            line(67, 25, 64, 28)
    else:
        frect(70, 8, 2, 32)
    for p in pillars:
        frect(p[0], p[1], p[2], p[3])
        pix(p[0] + 2, p[1] + 2, 0)
        pix(p[0] + 3, p[1] + 3, 0)
    for a in altars:
        frect(a[1] - 4, a[2] + 3, 9, 2)
        icon(a[0], a[1] - 2, a[2] - 2)
        if (frame // 6) % 2 == 0:
            pix(a[1] - 5, a[2] - 4)
            pix(a[1] + 5, a[2] - 4)
    for p in pickups:
        bob = int(math.sin(frame * 0.2 + p[1]) * 1.2)
        if p[0] == 0:
            heart(p[1] - 2, p[2] - 2 + bob, True)
        else:
            x = int(p[1])
            y = int(p[2]) + bob
            pix(x, y - 1)
            pix(x - 1, y)
            pix(x + 1, y)
            pix(x, y + 1)
            if (frame // 5) % 2 == 0:
                pix(x, y)


def draw_hud():
    for i in range(maxhp):
        heart(1 + i * 6, 1, i < hp)
    boss = None
    for e in enemies:
        if e[0] == BO:
            boss = e
    if boss is not None:
        D.drawRectangle(38, 1, 32, 4, 1)
        w = int(30 * boss[3] / boss[12])
        if w > 0:
            D.drawFilledRectangle(39, 2, w, 2, 1)
    else:
        s = "R" + str(r)
        D.drawText(s, W - 6 * len(s) - 1, 0, 1)
    if dash_cd > 0:
        ln = int(W * (1.0 - dash_cd / dash_cd_max))
    else:
        ln = W
    if ln > 0:
        D.drawLine(0, 7, ln - 1, 7, 1)
    for a in altars:
        ex = a[1] - px
        ey = a[2] - py
        if ex * ex + ey * ey < 400:
            D.drawFilledRectangle(0, 0, W, 7, 0)
            text_c(NAMES[a[0]], 0)
    if banner_t > 0:
        D.drawFilledRectangle(0, 17, W, 9, 0)
        text_c(banner_s, 18)


def draw_play():
    global ox, oy, banner_t, shake
    if shake > 0:
        ox = random.randint(-1, 1)
        oy = random.randint(-1, 1)
        shake -= 1
    else:
        ox = 0
        oy = 0
    draw_field()
    for tp in trail:
        pix(tp[0], tp[1])
    for e in enemies:
        draw_enemy(e)
    for b in bullets:
        x = int(b[0])
        y = int(b[1])
        if b[4] == 0:
            frect(x - 1, y - 1, 2, 2)
        else:
            pix(x, y)
            pix(x - 1, y)
            pix(x + 1, y)
            pix(x, y - 1)
            pix(x, y + 1)
    if dead_t < 0:
        show = not (inv > 0 and (frame // 2) % 2 == 0)
        draw_player(px, py, fx, fy, moving, att_t, show)
    for p in parts:
        pix(p[0], p[1])
    ox = 0
    oy = 0
    draw_hud()
    if banner_t > 0:
        banner_t -= 1


# ---------------------------------------------------------------- screens
def title():
    global state, sound, frame
    frame += 1
    for y in range(0, 27, 6):
        line(0, y, W - 1, y)
        off = 0 if (y // 6) % 2 == 0 else 6
        for x in range(off, W, 12):
            line(x, y, x, y + 5)
    frect(0, 27, W, 13, 0)
    line(0, 27, W - 1, 27)
    for tx in (3, 68):
        frect(tx, 14, 1, 4)
        pix(tx, 11 + random.randint(0, 1))
        pix(tx - 1, 12 + random.randint(0, 1))
        pix(tx + 1, 12 + random.randint(0, 1))
        pix(tx, 12)
        pix(tx, 13)
    frect(8, 3, 56, 22, 0)
    D.drawRectangle(8, 3, 56, 22, 1)
    D.drawText("DELVER", 18, 6, 1)
    D.drawText("DELVER", 19, 6, 1)
    ph = (frame // 40) % 3
    if ph == 0:
        text_c("A:PLAY", 15)
    elif ph == 1:
        text_c("BEST " + str(hi), 15)
    else:
        text_c("D:SND ON" if sound else "D:SND OFF", 15)
    t = frame % 120
    sx = max(28, 70 - 0.6 * t)
    at = 0
    if 70 <= t < 76:
        at = 6 - (t - 70)
    if t < 76:
        draw_slime(sx, 34, (frame // 10) % 2)
    elif t < 90:
        k = t - 76
        line(28 - k, 34 - k, 28 + k, 34 + k)
        line(28 + k, 34 - k, 28 - k, 34 + k)
    draw_player(14, 34, 1.0, 0.0, False, at, True)
    if dn_edge:
        sound = not sound
        beep(800, 40)
    if a_edge:
        reset()
        state = 1
        beep(900, 60)


def gameover():
    global state, frame, over_t
    frame += 1
    over_t += 1
    for y in range(0, 40, 6):
        line(0, y, W - 1, y)
    frect(4, 1, 64, 38, 0)
    D.drawRectangle(4, 1, 64, 38, 1)
    text_c("YOU DIED", 4)
    text_c("ROOM " + str(r), 12)
    text_c("SCORE " + str(score), 20)
    ph = (frame // 40) % 3
    if ph == 0:
        text_c("NEW BEST!" if new_hi else "BEST " + str(hi), 28)
    elif ph == 1:
        text_c("A:RETRY", 28)
    else:
        text_c("B:MENU", 28)
    if over_t > 25:
        if a_edge:
            reset()
            state = 1
            beep(900, 60)
        elif b_edge:
            state = 0


over_t = 0


def play():
    global frame, freeze, over_t
    frame += 1
    if freeze > 0:
        freeze -= 1
    else:
        update()
    over_t = 0
    draw_play()


# ---------------------------------------------------------------- main loop
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
