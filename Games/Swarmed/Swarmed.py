# SWARMED 2 - top-down survivor shooter for the Thumby
# D-PAD move (auto-fire) | A dash | B nova (when meter is full)
# Kill -> gems -> level up -> pick 1 of 3 of 26 upgrades.
# The stronger you get, the stronger they get (THREAT). Boss every minute.
# Install: /Games/Swarmed/Swarmed.py
import math, random, thumby

d = thumby.display
d.setFPS(30)
sin, cos, sqrt, atan2 = math.sin, math.cos, math.sqrt, math.atan2
rnd, rint = random.random, random.randint
CX, CY = 36, 23

hi = 0
try:
    thumby.saveData.setName("Swarmed")
    if thumby.saveData.hasItem("hi"):
        hi = int(thumby.saveData.getItem("hi"))
except Exception:
    pass


def beep(f, ms):
    try:
        thumby.audio.play(f, ms)
    except Exception:
        pass


def rect(x, y, w, h, c=1):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if x < 0: w += x; x = 0
    if y < 0: h += y; y = 0
    w = min(w, 72 - x); h = min(h, 40 - y)
    if w > 0 and h > 0:
        d.drawFilledRectangle(x, y, w, h, c)


def pixel(x, y, c=1):
    x, y = int(x), int(y)
    if 0 <= x < 72 and 0 <= y < 40:
        d.setPixel(x, y, c)


def text_c(s, y, c=1):
    d.drawText(s, (73 - len(s) * 6) // 2, y, c)


def panel(x, y, w, h):
    rect(x, y, w, h, 0)
    d.drawRectangle(x, y, w, h, 1)


def ring(x, y, r, n, a0):
    for i in range(n):
        pixel(x + cos(a0 + i * 6.2832 / n) * r, y + sin(a0 + i * 6.2832 / n) * r)


# ---------------------------------------------------------------- sprites
class Spr:
    def __init__(s, rows):
        s.rows = rows.split("/")
        s.w, s.h, s.obj = len(s.rows[0]), len(s.rows), None
        s.bm = bytearray(sum((1 << y) if r[x] == "#" else 0 for y, r in enumerate(s.rows))
                         for x in range(s.w))


HERO = Spr(".###./#.#.#/#####/.###./.#.#.")
# per enemy type: list of animation frames (None = drawn by code)
SPR = ([Spr("#.#.#/.###./#####/.###./#.#.#")],
       [Spr("#...#/##.##/#####/.#.#./....."), Spr("...../#...#/#####/##.##/.#.#.")],
       [Spr("..###../.#####./#######/##.#.##/#######/.#####./.#...#.")],
       None,
       [Spr("..#../.###./#.#.#/.###./#...#")],
       [Spr("..###../.#####./##.#.##/#######/.##.##.")],
       [Spr("#.###.#/.#####./##.#.##/.#####./#.#.#.#")],
       [Spr("..#../.###./#####/#####/.###.")],
       [Spr(".###./#.#.#/#####/#####/#.#.#")])

SM = 3                      # sprite method: 1 blit, 2 Sprite objects, 3 pixels
for _m in (1, 2):
    try:
        if _m == 1:
            d.blit(HERO.bm, 0, 0, 5, 5, 0, 0, 0)
        else:
            d.drawSprite(thumby.Sprite(5, 5, HERO.bm, 0, 0, 0, 0, 0))
        SM = _m
        break
    except Exception:
        pass


def spr(S, x, y):
    x, y = int(x) - S.w // 2, int(y) - S.h // 2
    if SM == 1:
        d.blit(S.bm, x, y, S.w, S.h, 0, 0, 0)
    elif SM == 2:
        if S.obj is None:
            S.obj = thumby.Sprite(S.w, S.h, S.bm, x, y, 0, 0, 0)
        S.obj.x, S.obj.y = x, y
        d.drawSprite(S.obj)
    else:
        for j, r in enumerate(S.rows):
            for i in range(S.w):
                if r[i] == "#":
                    pixel(x + i, y + j)


# ------------------------------------------------------------------ data
CRAWL, BAT, BRUTE, BOSS, SPIT, SPLIT, CHARGE, BOMB, GHOST = range(9)
# per type: base hp, gems, bullet-hit size, contact size, speed, threat to appear, spawn weight
T = ((1, 1, 3.5, 4, .42, 0, 10), (1, 1, 3.5, 4, .8, 2, 6), (7, 3, 5, 5.5, .26, 11, 3),
     (0, 10, 7, 8, .22, 99, 0), (2, 2, 3.5, 4, .3, 5, 4), (4, 2, 4.5, 5, .34, 7, 4),
     (3, 3, 4.5, 5, .3, 9, 4), (2, 2, 3.5, 4, .8, 6, 4), (3, 3, 3.5, 4, .4, 8, 3))

(FIRE, DMG, MULTI, PIERCE, BLADE, MAGNET, SPEED, HEART, NGAIN, MED, RIC, EXPL, LIGHT,
 REAR, VAMP, AURA, LUCKY, GEMB, SHIELD, DRONE, DASHB, BIGN, FROST, THORN, LASER, PANIC) = range(26)
UPG = (("FIRE RATE", 5), ("DAMAGE", 10), ("MULTISHOT", 4), ("PIERCE", 4), ("SPIN BLADE", 5),
       ("MAGNET", 4), ("SPEED", 6), ("+1 HEART", 1), ("NOVA GAIN", 5), ("MEDKIT", 99),
       ("RICOCHET", 3), ("EXPLOSIVE", 3), ("LIGHTNING", 4), ("REAR GUN", 2), ("VAMPIRE", 3),
       ("FIRE AURA", 4), ("LUCKY HIT", 6), ("GEM BOOST", 4), ("SHIELD", 3), ("DRONE", 3),
       ("DASH BLADE", 3), ("BIG NOVA", 3), ("FROST SHOT", 3), ("THORNS", 3), ("LASER", 4),
       ("PANIC NOVA", 3))
U = [0] * len(UPG)

# pickups: heart, energy cell, gem magnet, bomb
ITEM = (((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)),
        ((0, 0), (2, 0), (0, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)))

enemies, bullets, ebul, gems, items, parts, bolts = [], [], [], [], [], [], []
opts = []
t = mode = overT = 0
camx = camy = 0.0


def recalc():
    globals().update({
        "firerate": max(5, int(16 * 0.8 ** U[FIRE])), "dmg": 1 + U[DMG], "shots": 1 + U[MULTI],
        "magnet": min(80.0, 16 * 1.5 ** U[MAGNET]), "pspd": 1 + .12 * U[SPEED],
        "pmax": 5 + U[HEART], "ngain": 4 + 2 * U[NGAIN], "crit": .08 * U[LUCKY],
        "gemx": 1 + .25 * U[GEMB], "dashcd": max(12, 40 - 9 * U[DASHB]),
        "novarad": 40 + 8 * U[BIGN]})


def reset():
    for i in range(len(U)):
        U[i] = 0
    for L in (enemies, bullets, ebul, gems, items, parts, bolts):
        del L[:]
    recalc()
    globals().update({
        "px": 0.0, "py": 0.0, "ldx": 1.0, "ldy": 0.0, "php": pmax, "invul": 0, "shake": 0,
        "xp": 0.0, "lvl": 1, "need": 6, "kills": 0, "bonus": 0, "firecd": 10, "charge": 0.0,
        "dashT": 0, "dashCD": 0, "ddx": 0.0, "ddy": 0.0, "bang": 0.0, "dang": 0.0, "spawnT": 20,
        "bossN": 0, "nextHorde": 25, "banner": "", "bantimer": 0, "novaR": 0, "shRdy": False,
        "shT": 0, "vcount": 0, "litT": 90, "lasT": 60, "auraT": 0, "dT": 30, "magT": 0, "ft": 0,
        "secs": 0, "thr": 0.0, "lastTier": 1, "score": 0, "newbest": False, "combo": 0, "comboT": 0})


# ---------------------------------------------------------------- helpers
def burst(x, y, n):
    if len(parts) < 40:
        for _ in range(n):
            parts.append([x, y, (rnd() - .5) * 3, (rnd() - .5) * 3, 6 + rint(0, 6)])


def say(s):
    global banner, bantimer
    banner, bantimer = s, 30


def nearest(x, y, r2, skip=()):
    best = None
    for e in enemies:
        if id(e) not in skip:
            u, v = e[0] - x, e[1] - y
            q = u * u + v * v
            if q < r2:
                r2, best = q, e
    return best


def near(e, x, y, pad):
    r = T[e[3]][2] + pad
    return abs(e[0] - x) < r and abs(e[1] - y) < r


def orb(i, n, a, r):
    a += i * 6.2832 / n
    return px + cos(a) * r, py + sin(a) * r


def fire(x, y, a, dm=0, life=22):
    bullets.append([x, y, cos(a) * 2.8, sin(a) * 2.8, life, 0 if dm else U[PIERCE], None,
                    0 if dm else U[RIC], dm or dmg])


def ebullet(x, y, a, s):
    if len(ebul) < 40:
        ebul.append([x, y, cos(a) * s, sin(a) * s, 70])


def blast(r, dm, kb):
    for e in enemies:
        u, v = e[0] - px, e[1] - py
        dd = sqrt(u * u + v * v) + .01
        if dd < r:
            e[2] -= dm
            e[4] = 4
            k = 2 if e[3] == BOSS else kb
            e[0] += u / dd * k
            e[1] += v / dd * k


def hurt(n):
    global php, invul, shake, shRdy, shT
    if shRdy:
        shRdy, shT, invul = False, 900 - 200 * (U[SHIELD] - 1), 30
        burst(px, py, 6)
        beep(800, 60)
        return
    php -= n
    invul, shake = 45, 6
    burst(px, py, 8)
    beep(150, 150)
    if U[PANIC]:
        blast(24 + 8 * U[PANIC], 2 + dmg, 8)


def mke(x, y, hp, k, sg):
    # x, y, hp, type, flash, blade-cooldown, strafe/boss-kind, timer, lockx, locky, maxhp, elite, slow
    return [x, y, hp, k, 0, 0, sg, 0, 0.0, 0.0, hp, 0, 0]


def kill(e):
    global kills, charge, php, bonus, vcount, combo, comboT
    k = e[3]
    kills += 1
    combo += 1
    comboT = 60
    bonus += combo // 4
    charge = min(100.0, charge + ngain)
    for _ in range(T[k][1] * (2 if e[11] else 1)):
        if len(gems) >= 80:
            gems.pop(0)
        gems.append([e[0] + rint(-4, 4), e[1] + rint(-4, 4)])
    burst(e[0], e[1], 18 if k == BOSS else 4)
    if k == SPLIT:
        for sg in (-1, 1):
            enemies.append(mke(e[0] + sg * 3, e[1], 1 + int(thr * .05), CRAWL, sg))
    n = 3 if k == BOSS else int(bool(e[11]) or rnd() < (.02 if k < 2 else .09))
    for _ in range(n):
        if len(items) < 12:
            items.append([e[0] + rint(-8, 8), e[1] + rint(-8, 8), (0, 0, 0, 1, 1, 2, 3)[rint(0, 6)]])
    if k == BOSS:
        bonus += 100
        php = min(pmax, php + 1)
        say("BOSS DOWN!")
        beep(500, 200)
    if U[VAMP]:
        vcount += 1
        if vcount >= 40 - 10 * U[VAMP]:
            vcount = 0
            php = min(pmax, php + 1)


def spawn_enemy():
    a = rnd() * 6.2832
    r = rnd() * sum(w[6] for w in T if thr >= w[5])
    k = 0
    for i, w in enumerate(T):
        if thr >= w[5]:
            r -= w[6]
            if r <= 0:
                k = i
                break
    hp = max(1, int(T[k][0] * (1 + thr * .12) + .5))
    el = thr >= 6 and rnd() < .05 + thr * .004          # elites: triple health, better drops
    e = mke(px + cos(a) * 46, py + sin(a) * 46, hp * 3 if el else hp, k, 1 if rnd() < .5 else -1)
    e[11] = int(el)
    e[7] = rint(0, 50) if k in (SPIT, CHARGE) else 0
    enemies.append(e)


def horde():
    say("HORDE!")
    n = min(28, 16 + int(thr / 2))
    for i in range(n):
        a = i * 6.2832 / n
        enemies.append(mke(px + cos(a) * 44, py + sin(a) * 44, max(1, int(1 + thr * .12 + .5)),
                           CRAWL, 1 if i & 1 else -1))


def boss():
    a = rnd() * 6.2832
    enemies.append(mke(px + cos(a) * 46, py + sin(a) * 46, int(30 + 20 * bossN + thr * 3),
                       BOSS, (bossN - 1) % 4))
    say("BOSS!")
    beep(200, 300)


def zap():
    x, y, used, r2 = px, py, [], 1600
    for _ in range(2 + U[LIGHT]):
        e = nearest(x, y, r2, used)
        if not e:
            break
        bolts.append([x, y, e[0], e[1], 4])
        e[2] -= 2 + dmg // 2
        e[4] = 3
        used.append(id(e))
        x, y, r2 = e[0], e[1], 900
    beep(1800, 20)


def lvlcheck():
    global xp, lvl, need, opts, sel, selDelay, mode
    if xp >= need:
        xp -= need
        lvl += 1
        need = int(5 + lvl * 3.5)
        pool = [i for i in range(len(UPG)) if U[i] < UPG[i][1]]
        opts = [pool.pop(rint(0, len(pool) - 1)) for _ in range(min(3, len(pool)))]
        sel, selDelay, mode = 0, 10, 2 if opts else 1
        beep(1500, 120)
    else:
        mode = 1


# --------------------------------------------------------------- rendering
def draw_boss(x, y, e):
    x, y, k = int(x), int(y), e[6]
    if e[4] > 0:
        rect(x - 5, y - 5, 11, 11)
        return
    if k == 0 and 80 <= e[7] < 100 and t & 2:
        return                                  # charger boss winding up
    rect(x - 4, y - 5, 9, 11)
    rect(x - 5, y - 4, 11, 9)
    rect(x - 3, y - 2, 2, 2, 0)
    rect(x + 2, y - 2, 2, 2, 0)
    rect(x - 2, y + 2, 5, 1, 0)
    if k == 1:
        rect(x - 3, y - 7, 7, 1)                # summoner: crown
    elif k == 2:
        rect(x - 7, y, 2, 2)                    # gunner: side cannons
        rect(x + 6, y, 2, 2)
    elif k == 3:
        rect(x - 1, y - 8, 3, 3)                # spiral boss: antenna
    pixel(x - 4, y - 6)
    pixel(x + 4, y - 6)
    rect(x - 5, y - 10, 11 * e[2] // e[10], 1)


def draw_world():
    ox, oy = camx, camy
    for g in gems:
        pixel(g[0] - ox, g[1] - oy)
        if (t + int(g[0])) & 4:
            pixel(g[0] - ox + 1, g[1] - oy)
    for it in items:
        if t & 8 or it[2] == 0:
            for hx, hy in ITEM[it[2]]:
                pixel(it[0] - ox - 1 + hx, it[1] - oy - 1 + hy)
    if U[AURA]:
        ring(px - ox, py - oy, 10 + 3 * U[AURA], 12, t * .12)
    for e in enemies:
        x, y, k = e[0] - ox, e[1] - oy, e[3]
        if not (-10 < x < 82 and -12 < y < 52):
            continue
        r = int(T[k][3]) - 1
        if k == BOSS:
            draw_boss(x, y, e)
        elif e[4] > 0:
            rect(x - r, y - r, 2 * r + 1, 2 * r + 1)
        elif k == GHOST and (ft // 24) & 1:
            d.drawRectangle(int(x) - 3, int(y) - 3, 7, 7, 1)    # phased out: can't be hit
        elif (k == CHARGE and 60 <= e[7] < 80 or k == BOMB and e[7]) and t & 2:
            pass                                                # winding up / fuse blink
        else:
            fr = SPR[k]
            spr(fr[(ft // 4) % len(fr)], x, y)
        if e[11]:
            rect(x - 1, y - r - 3, 3, 1)                        # elite mark
    if not (invul > 0 and (invul // 3) % 2):
        spr(HERO, px - ox, py - oy)
    if shRdy:
        ring(px - ox, py - oy, 7, 6, t * .15)
    for n, a, r in ((U[BLADE], bang, 9), (U[DRONE], dang, 14)):
        for i in range(n):
            x, y = orb(i, n, a, r)
            rect(x - ox - 1, y - oy - 1, 2, 2)
    for b in bullets:
        pixel(b[0] - ox, b[1] - oy)
        pixel(b[0] - ox - b[2] * .5, b[1] - oy - b[3] * .5)
    for b in ebul:
        rect(b[0] - ox - 1, b[1] - oy - 1, 2, 2)
    for i in range(len(bolts) - 1, -1, -1):
        b = bolts[i]
        b[4] -= 1
        if b[4] <= 0:
            bolts.pop(i)
        else:
            d.drawLine(int(b[0] - ox), int(b[1] - oy), int(b[2] - ox), int(b[3] - oy), 1)
    if novaR:
        ring(px - ox, py - oy, novaR * novarad / 13.0, 28, 0)
    for i in range(len(parts) - 1, -1, -1):
        p = parts[i]
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1
        if p[4] <= 0:
            parts.pop(i)
        else:
            pixel(p[0] - ox, p[1] - oy)


def draw_hud():
    rect(0, 0, 72, 7, 0)
    for i in range(pmax):
        for hx, hy in ITEM[0] if i < php else ((1, 1),):
            pixel(i * 4 + hx, 1 + hy)
    d.drawRectangle(26, 1, 10, 5, 1)
    rect(27, 2, 8 if charge >= 100 and t & 4 else int(charge * .08), 3)
    d.drawText("L%d" % lvl, 38, 0, 1)
    s = "%d" % secs
    d.drawText(s, 73 - len(s) * 6, 0, 1)
    rect(0, 39, 71 * xp / need, 1)
    if combo > 2:
        s = "x%d" % combo
        d.drawText(s, 73 - len(s) * 6, 31, 1)
    if bantimer > 0:
        panel(10, 14, 52, 11)
        text_c(banner, 16)


# ---------------------------------------------------------------- main loop
reset()
PB = [True] * 6

while True:
    t += 1
    B = [thumby.buttonA.pressed(), thumby.buttonB.pressed(), thumby.buttonL.pressed(),
         thumby.buttonR.pressed(), thumby.buttonU.pressed(), thumby.buttonD.pressed()]
    kl, kr, ku, kd = B[2:]
    eA, eB, _, _, eU, eD = [x and not y for x, y in zip(B, PB)]
    PB = B
    d.fill(0)

    if mode == 0:                                               # ---- title
        text_c("SWARMED 2", 1)
        text_c(("PRESS A", "D-PAD: MOVE", "A: DASH", "B: NOVA", "AUTO FIRE!")[(t // 60) % 5], 10)
        for i in range(8):
            r = 36 - ((t + i * 11) % 88) * .4
            if r > 6:
                spr(SPR[(0, 4, 5, 7)[i & 3]][0], 36 + cos(i * .785 + t * .01) * r * 1.5,
                    28 + sin(i * .785 + t * .01) * r * .6)
        for i in range(2):
            rect(36 + cos(t * .14 + i * 3.1416) * 9 - 1, 28 + sin(t * .14 + i * 3.1416) * 9 - 1, 2, 2)
        spr(HERO, 36, 28)
        d.drawText("BEST %d" % hi, 1, 34, 1)
        if eA:
            reset()
            mode = 1

    elif mode == 1:                                             # ---- play
        ft += 1
        secs = ft // 30
        thr = (lvl - 1) * 1.5 + secs / 45.0                     # THREAT: your power + time
        ms = 1 + min(thr, 30.0) * .015
        tn = sum(1 for w in T if w[6] and thr >= w[5])
        if tn > lastTier:
            lastTier = tn
            say("NEW FOES!")
            beep(300, 150)

        dx, dy = kr - kl, kd - ku
        if dx and dy:
            dx, dy = dx * .707, dy * .707
        if dx or dy:
            ldx, ldy = dx, dy
        dashCD = max(0, dashCD - 1)
        if eA and not dashCD:
            dashT, dashCD, ddx, ddy = 6, dashcd, ldx, ldy
            beep(700, 40)
        if dashT:
            dashT -= 1
            px += ddx * 3.2
            py += ddy * 3.2
            burst(px, py, 1)
            if U[DASHB]:
                for e in enemies:
                    if not e[5] and near(e, px, py, 2):
                        e[2] -= 2 * U[DASHB] + dmg // 2
                        e[4], e[5] = 3, 6
        else:
            px += dx * pspd
            py += dy * pspd
        if eB and charge >= 100:
            charge, novaR, shake = 0.0, 1, 8
            del ebul[:]
            blast(novarad, 3 + dmg + 2 * U[BIGN], 6)
            beep(220, 250)
        if novaR:
            novaR = novaR + 1 if novaR < 13 else 0

        firecd -= 1
        if firecd <= 0:
            e = nearest(px, py, 2500)
            if e:
                ag = atan2(e[1] - py, e[0] - px)
                for i in range(shots):
                    fire(px, py, ag + (i - (shots - 1) / 2) * .2)
                for i in range(U[REAR]):
                    fire(px, py, ag + 3.1416 + (i - (U[REAR] - 1) / 2) * .3)
                firecd = firerate

        if U[DRONE]:
            dang += .07
            dT -= 1
            for i in range(U[DRONE]):
                x, y = orb(i, U[DRONE], dang, 14)
                e = nearest(x, y, 2025) if dT <= 0 else None
                if e:
                    fire(x, y, atan2(e[1] - y, e[0] - x), max(1, dmg // 2), 18)
            if dT <= 0:
                dT = 40
        if U[LIGHT]:
            litT -= 1
            if litT <= 0 and enemies:
                litT = 150 - 20 * U[LIGHT]
                zap()
        if U[LASER]:
            lasT -= 1
            e = nearest(px, py, 3600) if lasT <= 0 else None
            if e:
                lasT = 120 - 15 * U[LASER]
                ag = atan2(e[1] - py, e[0] - px)
                c, s = cos(ag), sin(ag)
                bolts.append([px, py, px + c * 70, py + s * 70, 6])
                for o in enemies:
                    u, v = o[0] - px, o[1] - py
                    if 0 < u * c + v * s < 70 and abs(v * c - u * s) < T[o[3]][2] + 1:
                        o[2] -= 2 * dmg + U[LASER]
                        o[4] = 3
                beep(1200, 30)
        if U[AURA]:
            auraT -= 1
            if auraT <= 0:
                auraT, rr = 12, 10 + 3 * U[AURA]
                for e in enemies:
                    if abs(e[0] - px) < rr and abs(e[1] - py) < rr:
                        e[2] -= 1 + U[AURA] // 2
                        e[4] = 2

        spawnT -= 1
        if spawnT <= 0 and len(enemies) < min(44, int(12 + thr * 1.5)):
            spawn_enemy()
            spawnT = int(max(5, 38 - thr * 1.6) * (.7 + .6 * rnd()))
        if secs >= nextHorde:
            nextHorde += 45
            horde()
        if secs >= (bossN + 1) * 60:
            bossN += 1
            boss()

        for e in enemies:                                       # enemy AI
            ex, ey, k, sg = e[0], e[1], e[3], e[6]
            ux, uy = px - ex, py - ey
            dd = sqrt(ux * ux + uy * uy) + .001
            ux, uy = ux / dd, uy / dd
            sp = T[k][4] * ms * (.55 if e[12] else 1)
            mx, my = ux, uy
            if k in (CRAWL, BAT, BOMB, GHOST):                  # spiral in
                mx, my = ux * .94 - uy * .34 * sg, ux * .34 * sg + uy * .94
            if k == BAT:
                sp *= .25 + .75 * (.5 + .5 * sin(ft * .2 + ex))
            elif k == SPIT:                                     # keeps range and shoots
                if dd < 18:
                    mx, my = -ux, -uy
                elif dd < 28:
                    mx, my = -uy * sg, ux * sg
                e[7] += 1
                if e[7] >= max(45, 85 - int(thr * 2)) and dd < 50:
                    e[7] = 0
                    for o in (0,) if thr < 12 else (0, .3, -.3):
                        ebullet(ex, ey, atan2(py - ey, px - ex) + o, 1.2)
            elif k == CHARGE:                                   # wind up, then dash
                e[7] += 1
                if 60 <= e[7] < 80:
                    sp = 0
                    e[8], e[9] = ux, uy
                elif 80 <= e[7] < 100:
                    mx, my, sp = e[8], e[9], 2.2
                elif e[7] >= 100:
                    e[7] = 0
            elif k == BOMB:                                     # suicide bomber
                if dd < 14 and not e[7]:
                    e[7] = 1
                if e[7]:
                    sp = 0
                    e[7] += 1
                    if e[7] > 20:
                        burst(ex, ey, 14)
                        beep(180, 80)
                        e[2] = 0
                        if dd < 18 and not invul and not dashT:
                            hurt(1)
            elif k == BOSS:
                e[7] += 1
                c = e[7]
                if sg == 0:                                     # charger boss
                    if 80 <= c < 100:
                        sp = 0
                        e[8], e[9] = ux, uy
                    elif 100 <= c < 125:
                        mx, my, sp = e[8], e[9], 1.6
                    elif c >= 125:
                        e[7] = 0
                elif sg == 1 and c % 110 == 0 and len(enemies) < 46:     # summoner boss
                    say("MINIONS!")
                    for i in range(4):
                        enemies.append(mke(ex + cos(i * 1.5708) * 8, ey + sin(i * 1.5708) * 8,
                                           max(1, int(1 + thr * .12)), CRAWL, 1))
                elif sg == 2 and c % 90 == 0:                   # gunner boss: bullet ring
                    for i in range(8 + int(thr / 4)):
                        ebullet(ex, ey, i * 6.2832 / (8 + int(thr / 4)) + c * .01, 1.0)
                elif sg == 3 and c % 5 == 0:                    # spiral boss
                    ebullet(ex, ey, c * .35, 1.1)
            e[0], e[1] = ex + mx * sp, ey + my * sp
            e[4] = max(0, e[4] - 1)
            e[5] = max(0, e[5] - 1)
            e[12] = max(0, e[12] - 1)
            if dd < T[k][3]:
                if U[THORN] and not e[5]:
                    e[2] -= 1 + U[THORN]
                    e[4], e[5] = 3, 10
                if not invul and not dashT:
                    hurt(2 if thr >= 12 and k in (BRUTE, BOSS) else 1)

        for i in range(len(ebul) - 1, -1, -1):                  # enemy bullets
            b = ebul[i]
            b[0] += b[2]
            b[1] += b[3]
            b[4] -= 1
            if b[4] <= 0:
                ebul.pop(i)
            elif abs(b[0] - px) < 3 and abs(b[1] - py) < 3 and not invul and not dashT:
                ebul.pop(i)
                hurt(1)

        for i in range(len(bullets) - 1, -1, -1):               # player bullets
            b = bullets[i]
            b[0] += b[2]
            b[1] += b[3]
            b[4] -= 1
            if b[4] <= 0:
                bullets.pop(i)
                continue
            for e in enemies:
                if e is b[6] or (e[3] == GHOST and (ft // 24) & 1) or not near(e, b[0], b[1], 0):
                    continue
                dm = b[8]
                if crit and rnd() < crit:
                    dm *= 2
                    burst(e[0], e[1], 2)
                e[2] -= dm
                e[4] = 3
                e[0] += b[2] * .5
                e[1] += b[3] * .5
                e[12] = 30 + 15 * U[FROST] if U[FROST] else e[12]
                b[6] = e
                if U[EXPL]:
                    rr = 9 + 2 * U[EXPL]
                    for o in enemies:
                        if o is not e and abs(o[0] - e[0]) < rr and abs(o[1] - e[1]) < rr:
                            o[2] -= U[EXPL] + dmg // 3
                            o[4] = 3
                    burst(e[0], e[1], 3)
                b[5] -= 1
                if b[5] < 0:
                    o = nearest(b[0], b[1], 900, (id(e),)) if b[7] > 0 else None
                    if o:                                       # ricochet
                        ag = atan2(o[1] - b[1], o[0] - b[0])
                        b[2], b[3], b[5], b[7], b[4] = cos(ag) * 2.8, sin(ag) * 2.8, 0, b[7] - 1, max(b[4], 14)
                    else:
                        bullets.pop(i)
                    break

        if U[BLADE]:                                            # spinning blades
            bang += .14
            for i in range(U[BLADE]):
                x, y = orb(i, U[BLADE], bang, 9)
                for e in enemies:
                    if not e[5] and near(e, x, y, 1.5):
                        e[2] -= 1 + dmg // 2
                        e[4], e[5] = 3, 8

        for i in range(len(enemies) - 1, -1, -1):
            if enemies[i][2] <= 0:
                kill(enemies[i])
                enemies.pop(i)

        for i in range(len(gems) - 1, -1, -1):                  # gems
            g = gems[i]
            u, v = px - g[0], py - g[1]
            dd = u * u + v * v
            if magT or dd < magnet * magnet:
                dist = sqrt(dd) + .01
                g[0] += u / dist * 2.4
                g[1] += v / dist * 2.4
            if dd < 12:
                gems.pop(i)
                xp += gemx
        for i in range(len(items) - 1, -1, -1):                 # pickups
            it = items[i]
            u, v = px - it[0], py - it[1]
            dd = u * u + v * v
            if dd < 900:
                dist = sqrt(dd) + .01
                it[0] += u / dist * 1.5
                it[1] += v / dist * 1.5
            if dd < 25:
                items.pop(i)
                if it[2] == 0:
                    if php < pmax:
                        php += 1
                    else:
                        xp += 3
                elif it[2] == 1:
                    charge = min(100.0, charge + 40)
                elif it[2] == 2:
                    magT = 90
                else:
                    blast(80, 6 + dmg, 6)
                    novaR, shake = 1, 6
                beep(1400, 50)

        invul = max(0, invul - 1)
        shake = max(0, shake - 1)
        bantimer = max(0, bantimer - 1)
        magT = max(0, magT - 1)
        comboT = max(0, comboT - 1)
        if not comboT:
            combo = 0
        if U[SHIELD] and not shRdy:
            shT -= 1
            if shT <= 0:
                shRdy = True
                beep(1000, 50)

        if php <= 0:
            mode, overT = 3, 0
            score = secs * 5 + kills * 2 + bonus
            newbest = score > hi
            if newbest:
                hi = score
                try:
                    thumby.saveData.setItem("hi", hi)
                    thumby.saveData.save()
                except Exception:
                    pass
            beep(100, 400)
        elif xp >= need:
            lvlcheck()

        camx, camy = px - CX, py - CY
        if shake:
            camx += rint(-1, 1)
            camy += rint(-1, 1)
        draw_world()
        draw_hud()

    elif mode == 2:                                             # ---- level up
        selDelay = max(0, selDelay - 1)
        sel = max(0, min(len(opts) - 1, sel + eD - eU))
        if (eA or eB) and not selDelay:
            U[opts[sel]] += 1
            recalc()
            if opts[sel] == HEART:
                php += 1
            elif opts[sel] == MED:
                php = min(pmax, php + 2)
            elif opts[sel] == SHIELD and U[SHIELD] == 1:
                shRdy = True
            beep(1000, 60)
            lvlcheck()
        draw_world()
        draw_hud()
        panel(1, 1, 70, 38)
        text_c("LEVEL UP!", 4)
        for i in range(len(opts)):
            if i == sel:
                rect(4, 13 + i * 9, 64, 9)
            text_c(UPG[opts[i]][0], 14 + i * 9, 0 if i == sel else 1)

    else:                                                       # ---- game over
        overT += 1
        draw_world()
        panel(1, 1, 70, 38)
        text_c("GAME OVER", 4)
        text_c("TIME %ds" % secs, 13)
        text_c("%d KILLS" % kills, 21)
        text_c(("SCORE %d" % score, "NEW BEST!" if newbest else "BEST %d" % hi,
                "LEVEL %d" % lvl, "A: RETRY")[(t // 30) % 4], 30)
        if eA and overT > 25:
            reset()
            mode = 1

    d.update()
