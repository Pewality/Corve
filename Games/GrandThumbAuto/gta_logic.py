# gta_logic.py - Grand Thumb Auto code (stored in small pieces; main.py loads it). Do not edit.
#@@game
import math, random, time
PI = math.pi
sin = math.sin
cos = math.cos
sqrt = math.sqrt
atan2 = math.atan2
DX = (1, 0, -1, 0)
DY = (0, 1, 0, -1)
LANE = (1.5, 0.5, 0.5, 1.5)
CLEN = (1.1, 0.9, 1.35, 1.15, 1.1, 1.15, 1.8, 2.3, 1.15, 1.5)
CWID = (0.52, 0.48, 0.6, 0.54, 0.52, 0.56, 0.66, 0.7, 0.56, 0.66)
CHT = (0.42, 0.4, 0.6, 0.44, 0.46, 0.34, 0.75, 0.8, 0.36, 0.65)
TOP = (0.3, 0.27, 0.24, 0.32, 0.28, 0.35, 0.2, 0.17, 0.36, 0.26)
CVM = (0.09, 0.08, 0.07, 0.1, 0.1, 0.13, 0.06, 0.05, 0.1, 0.07)
COPV = (0, 0, 0, 0.21, 0, 0, 0, 0, 0.26, 0.18)
CKINDS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 3)
PS = (0.03, 0.03, 0.028, 0.026, 0.04, 0.07, 0.022, 0.024)
WN = ('PISTOL', 'SMG', 'SHOTGUN')
WL = ('P', 'S', 'H')
WR = (10.0, 9.0, 5.5)
WC = (9, 3, 22)
WP = (0, 150, 100)
WA = ((6, 15), (20, 30), (6, 24))
QUAL = (('LOW', 26, 8, 16), ('NORM', 40, 12, 19), ('HIGH', 68, 17, 24))
MAXPED = 46
MAXCAR = 13
NAMES = ('DINER', 'BANK', 'GAS', 'SHOP', 'BAR', 'MALL', 'PIZZA', 'CLINIC')
STREETS = ('ELM', 'OAK', 'MAIN', 'PINE', 'MAPLE', 'CEDAR', 'LAKE', 'HILL', 'PARK', 'KING', 'RIVER', 'BAY', 'SUN', 'ROSE', 'FORD', 'NOVA')
px = 2.5
py = 6.5
ang = -PI / 2
pcar = None
cars = []
peds = []
cash = 0
heat = 0
msg = ''
msgt = 0
mdl = 0
hint = ''
tick = 0
rkey = None
robbed = set()
hp = 3
gun = False
ENTER2 = 1.44
dead = 0
inap = False
dmsg = ''
CRASHV = 0.2667
#@
wpn = 0
owned = [True, False, False]
ammo = [12, 0, 0]
qual = 1
fcool = 0
flash = 0
hitf = 0
copd = 9999.0
n_steal = 0
n_rob = 0
n_kill = 0
n_jack = 0
camx = 0.0
camy = 0.0
camth = 0.0
hel = []
ph = None
pz = 0.0
pvz = 0.0
chute = False
fall = 0
def say(t, n=70):
    global msg, msgt, mdl
    msg = t
    msgt = 60
    mdl = time.ticks_add(time.ticks_ms(), 2000)
def crime(h, t):
    global heat
    if heat < h:
        heat = h
    say(t, 60)
def solid(x, y):
    return mp[(int(y // 1) & 63) << 6 | int(x // 1) & 63] > 127
def blocked(x, y, r):
    return solid(x - r, y - r) or solid(x + r, y - r) or solid(x - r, y + r) or solid(x + r, y + r)
def car_blocked(x, y, a, c):
    k = c[7]
    hl = CLEN[k] / 2 - 0.05
    hw = CWID[k] / 2 - 0.03
    fx = cos(a)
    fy = sin(a)
    for l in (-hl, hl):
        for w in (-hw, hw):
            if solid(x + fx * l - fy * w, y + fy * l + fx * w):
                return True
    return False
def walk_ok(x, y):
    m = mp[(int(y // 1) & 63) << 6 | int(x // 1) & 63]
    return m < 128 and m & 15 in (1, 2, 3, 4, 8, 9)
def newcar(x, y, a, spd, ctl, dr, vm, k, tint=-1):
    if tint < 0:
        tint = 1 if k == 4 else random.getrandbits(1)
    c = [float(x), float(y), a, spd, ctl, dr, vm, k, 0, 0, tint, vm]
    cars.append(c)
    return c
#@
def spawn_car(ct, near=False):
    for _ in range(10):
        dd = random.getrandbits(2)
        r = 8 + random.getrandbits(4) if near else 18 + random.getrandbits(3)
        a = random.getrandbits(10) * 6.2832 / 1024
        sx = camx + cos(a) * r
        sy = camy + sin(a) * r
        if dd & 1:
            sx = int(sx // 16) * 16 + LANE[dd]
        else:
            sy = int(sy // 16) * 16 + LANE[dd]
        ok = abs(sx - px) > 3 or abs(sy - py) > 3
        for o in cars:
            if abs(o[0] - sx) < 3.8 and abs(o[1] - sy) < 3.8:
                ok = False
                break
        if ok:
            if ct == 3:
                if heat >= 450:
                    k = 8 + random.getrandbits(1)
                else:
                    k = 8 if random.getrandbits(2) == 0 else 3
                vm = COPV[k]
            else:
                k = CKINDS[random.getrandbits(5)]
                vm = CVM[k] + random.getrandbits(4) * 0.003
            newcar(sx, sy, dd * PI / 2, vm if near else 0.05, ct, dd, vm, k)
            return
#@
def spawn_ped(near=False):
    ct = cos(camth)
    st = sin(camth)
    for _ in range(10):
        r = 3 + random.getrandbits(3) if near else 5 + random.getrandbits(4)
        a = random.getrandbits(10) * 6.2832 / 1024
        sx = camx + cos(a) * r
        sy = camy + sin(a) * r
        s = (2.5, -0.5)[random.getrandbits(1)]
        if random.getrandbits(1):
            sx = int(sx // 16) * 16 + s
        else:
            sy = int(sy // 16) * 16 + s
        if not near:
            dx = sx - camx
            dy = sy - camy
            dep = dx * ct + dy * st
            if 0.5 < dep < 15 and abs(dy * ct - dx * st) < dep * 1.1:
                continue
        if walk_ok(sx, sy) and abs(sx - px) + abs(sy - py) > 1.5:
            if random.getrandbits(2) >= density(int(sx // 16) + OX, int(sy // 16) + OY):
                continue
            t = random.getrandbits(3)
            dd = random.getrandbits(2)
            peds.append([sx, sy, DX[dd] * PS[t], DY[dd] * PS[t], 30 + random.getrandbits(7), 0, t, 1 if random.getrandbits(5) == 0 else 0, 0, random.getrandbits(1)])
            return
#@
def spawn_parked():
    ct = cos(camth)
    st = sin(camth)
    for _ in range(8):
        r = 5 + random.getrandbits(4)
        a = random.getrandbits(10) * 6.2832 / 1024
        sx = camx + cos(a) * r
        sy = camy + sin(a) * r
        tx = int(sx // 1)
        ty = int(sy // 1)
        if mp[(ty & 63) << 6 | tx & 63] != 4 or mp[(ty & 63) << 6 | tx + 1 & 63] != 4:
            continue
        dx = sx - camx
        dy = sy - camy
        dep = dx * ct + dy * st
        if 0.5 < dep < 15 and abs(dy * ct - dx * st) < dep * 1.1:
            continue
        ok = abs(sx - px) + abs(sy - py) > 2.5
        for o in cars:
            if abs(o[0] - tx - 0.5) < 1.7 and abs(o[1] - ty - 0.5) < 1.7:
                ok = False
                break
        if ok:
            k = CKINDS[random.getrandbits(5)]
            newcar(tx + 0.5, ty + 0.5, random.getrandbits(2) * PI / 2, 0.0, 2, 0, 0.1, k)
            return
#@
def _tv(c, tv, dr, fx, fy):
    if fx:
        a = c[0]
        lat = c[1]
    else:
        a = c[1]
        lat = c[0]
    hl = CLEN[c[7]] * 0.5
    if c[8] >= 0:
        for o in cars:
            dx = o[0] - c[0]
            if dx > 4.8 or dx < -4.8:
                continue
            dy = o[1] - c[1]
            if dy > 4.8 or dy < -4.8 or o is c:
                continue
            ah = dx * fx + dy * fy
            gap = hl + CLEN[o[7]] * 0.5 + 0.3
            if 0 < ah < gap + 1.8 and abs(dy * fx - dx * fy) < 0.7:
                v = (ah - gap) * 0.07
                if v < tv:
                    tv = v
        if pcar is None and pz <= 0:
            dx = px - c[0]
            dy = py - c[1]
            ah = dx * fx + dy * fy
            if 0 < ah < hl + 2.0 and abs(dy * fx - dx * fy) < 0.6:
                v = (ah - hl - 0.2) * 0.07
                if v < tv:
                    tv = v
    if fx + fy > 0:
        k = int((a - 1.0) // 16) + 1
        dist = k * 16 + 1.0 - a
    else:
        k = int((a - 1.0) // 16)
        dist = a - (k * 16 + 1.0)
    sd = 1.45 + hl
    if sd < dist < sd + 5.0:
        lc = int(lat // 16)
        s = light(k, lc, 0) if fx else light(lc, k, 1)
        if s == 2 or (s == 1 and dist > sd + 1.8):
            v = (dist - sd) * 0.05
            if v < tv:
                tv = v
    return tv
#@
def _turn(c, dr, cop):
    r = random.getrandbits(7) % 100
    nd = dr
    if cop:
        tx = px - c[0]
        ty = py - c[1]
        bs = -9999
        for cand in (dr, dr + 1 & 3, dr + 3 & 3):
            sc = DX[cand] * tx + DY[cand] * ty
            if r < 12:
                sc = random.getrandbits(5)
            if sc > bs:
                bs = sc
                nd = cand
    elif r >= 55:
        nd = dr + 1 & 3 if r < 78 else dr + 3 & 3
    return nd
#@
def ai(c):
    dr = c[5]
    fx = DX[dr]
    fy = DY[dr]
    a = c[0] if fx else c[1]
    sg = fx + fy
    cop = c[4] == 3
    tv = c[6]
    if not cop and abs(c[0] - camx) < 28 and (abs(c[1] - camy) < 28):
        if tick + (id(c) >> 4) & 1:
            tv = c[11]
        else:
            tv = c[11] = _tv(c, tv, dr, fx, fy)
    if tv < 0:
        tv = 0
    if c[3] < tv:
        c[3] = min(tv, c[3] + 0.004)
    else:
        c[3] = max(tv, c[3] - 0.012)
    if tv == 0 and c[3] < 0.01:
        c[8] += 1
        if c[8] > 240:
            c[8] = -90
    elif c[8] > 0:
        c[8] = 0
    elif c[8] < 0:
        c[8] += 1
    na = a + sg * c[3]
    if c[9] > 0:
        c[9] -= 1
    elif (a - 1.0) // 16 != (na - 1.0) // 16:
        nd = _turn(c, dr, cop)
        if nd != dr:
            c[5] = nd
            c[9] = 30
    if fx:
        c[0] = na
    else:
        c[1] = na
    dr = c[5]
    if DX[dr]:
        dl = int(c[1] // 16) * 16 + LANE[dr] - c[1]
        c[1] += max(-0.03, min(0.03, dl))
    else:
        dl = int(c[0] // 16) * 16 + LANE[dr] - c[0]
        c[0] += max(-0.03, min(0.03, dl))
    diff = (dr * PI / 2 - c[2] + PI) % (2 * PI) - PI
    c[2] += max(-0.12, min(0.12, diff))
#@
def move_car(c):
    s = c[3]
    if s == 0:
        return
    a = c[2]
    nx = c[0] + cos(a) * s
    ny = c[1] + sin(a) * s
    if car_blocked(c[0], c[1], a, c):
        c[0] = nx
        c[1] = ny
        return
    hit = 0
    if car_blocked(nx, c[1], a, c):
        hit = 1
    else:
        c[0] = nx
    if car_blocked(c[0], ny, a, c):
        hit += 1
    else:
        c[1] = ny
    if hit:
        c[3] = s * (0.3 if hit > 1 else 0.85)
def can_walk(p, x, y):
    return walk_ok(x, y) or (p[7] and (not solid(x, y)))
def flee(p, dx, dy, v=0.09):
    if abs(dx) > abs(dy):
        p[2] = v if dx > 0 else -v
        p[3] = 0.0
    else:
        p[3] = v if dy > 0 else -v
        p[2] = 0.0
def hurt(p):
    global cash, hp
    g = cash // 4 if cash >= 8 else 0
    cash -= g
    hp -= 1
    p[8] = 220
    p[4] = 220
    flee(p, p[0] - px, p[1] - py, 0.07)
    say('MUGGED -$' + str(g) if g else 'THUG HIT YOU', 50)
    if hp <= 0:
        wasted('BEATEN DOWN')
def wasted(m):
    global dead, dmsg
    dead = 1
    dmsg = m
#@
def steal(p):
    global cash, n_steal
    g = 3 + random.getrandbits(5)
    if p[6] == 1 or p[6] == 7:
        g += 12
    cash += g
    n_steal += 1
    flee(p, p[0] - px, p[1] - py)
    p[4] = 90
    p[8] = 90
    if random.getrandbits(1):
        crime(240, 'STOLE $' + str(g))
    else:
        say('STOLE $' + str(g), 40)
def _pellets(cand, w, rng):
    hits = []
    sp = (0.0, 0.07, 0.3)[w]
    for _ in range(5 if w == 2 else 1):
        a = ang
        if sp:
            a += (random.getrandbits(8) - 128) / 128.0 * sp
        c = cos(a)
        s = sin(a)
        best = None
        bt = rng
        for p in cand:
            dx = p[0] - px
            dy = p[1] - py
            t = dx * c + dy * s
            if 0.2 < t < bt and abs(dy * c - dx * s) < 0.4:
                best = p
                bt = t
        if best is not None:
            d = 0.4
            while d < bt and (not solid(px + c * d, py + s * d)):
                d += 0.3
            if d >= bt:
                for h in hits:
                    if h is best:
                        break
                else:
                    hits.append(best)
    return hits
#@
def _shot_result(hits, cand):
    global hitf, cash, n_kill
    for p in cand:
        dx = p[0] - px
        dy = p[1] - py
        if dx * dx + dy * dy < 64:
            for h in hits:
                if h is p:
                    break
            else:
                flee(p, dx, dy, 0.08)
                p[4] = 50
                if not p[7]:
                    p[8] = 50
    for h in hits:
        h[5] = 1
        h[4] = 70
        hitf = 8
        n_kill += 1
        if h[7]:
            g = 8 + random.getrandbits(5)
            cash += g
            say('THUG DOWN +$' + str(g), 45)
        else:
            crime(520, 'SHOTS FIRED')
def fire():
    global fcool, flash
    if fcool > 0:
        return
    w = wpn
    if ammo[w] <= 0:
        say('NO AMMO', 25)
        fcool = 12
        return
    ammo[w] -= 1
    fcool = WC[w]
    flash = 3
    rng = WR[w]
    cand = []
    for p in peds:
        if not p[5]:
            dx = p[0] - px
            dy = p[1] - py
            if dx * dx + dy * dy < (rng + 0.6) * (rng + 0.6):
                cand.append(p)
    _shot_result(_pellets(cand, w, rng), cand)
#@
def upd_ped(p, k=1):
    p[4] -= k
    if p[5]:
        return
    if p[8] > 0:
        p[8] -= k
    elif p[7] and pcar is None and pz <= 0 and ph is None:
        dx = px - p[0]
        dy = py - p[1]
        dd = dx * dx + dy * dy
        if dd < 100:
            if dd < 1.0:
                hurt(p)
            else:
                s = 0.045 * k / sqrt(dd)
                nx = p[0] + dx * s
                ny = p[1] + dy * s
                if not solid(nx, p[1]):
                    p[0] = nx
                if not solid(p[0], ny):
                    p[1] = ny
            return
    if p[4] <= 0:
        r = random.getrandbits(4)
        if r < 3:
            p[2] = 0.0
            p[3] = 0.0
        elif r >= 10 or not (p[2] or p[3]):
            v = PS[p[6]]
            for _ in range(4):
                dd = random.getrandbits(2)
                if can_walk(p, p[0] + DX[dd] * 0.8, p[1] + DY[dd] * 0.8):
                    p[2] = DX[dd] * v
                    p[3] = DY[dd] * v
                    break
        p[4] = 40 + random.getrandbits(8)
    if p[2] or p[3]:
        nx = p[0] + p[2] * k
        ny = p[1] + p[3] * k
        if can_walk(p, nx, ny):
            p[0] = nx
            p[1] = ny
        else:
            p[2] = -p[2]
            p[3] = -p[3]
#@
def near_shop():
    tx = int(px // 1)
    ty = int(py // 1)
    for yy in range(ty - 1, ty + 2):
        for xx in range(tx - 1, tx + 2):
            m = mp[(yy & 63) << 6 | xx & 63]
            if m > 127 and m >> 5 & 3 == 2:
                gx = xx + OX * 16 >> 2
                gy = yy + OY * 16 >> 2
                if is_ap((xx >> 4) + OX, (yy >> 4) + OY):
                    return ((gx, gy), 'AIRPORT')
                return ((gx, gy), NAMES[H(gx, gy, 9) % 8])
    return (None, '')
def try_enter():
    global pcar, n_jack
    best = None
    bd = ENTER2
    for c in cars:
        if c[4] == 3:
            continue
        dx = c[0] - px
        dy = c[1] - py
        dd = dx * dx + dy * dy
        if dd < bd:
            bd = dd
            best = c
    if best is None:
        return False
    if best[4] == 0:
        n_jack += 1
        crime(420, 'CARJACK!')
    best[4] = 1
    best[3] = 0.0
    pcar = best
    return True
def exit_car():
    global pcar, px, py, ang
    c = pcar
    c[4] = 2
    c[3] = 0.0
    ang = c[2]
    px = c[0]
    py = c[1]
    for s in (1, -1):
        tx = c[0] - sin(c[2]) * 1.0 * s
        ty = c[1] + cos(c[2]) * 1.0 * s
        if not blocked(tx, ty, 0.25):
            px = tx
            py = ty
            break
    pcar = None
def calm_cops():
    for c in cars:
        if c[4] == 3:
            c[4] = 0
            c[6] = CVM[c[7]]
#@
def busted():
    global cash, heat, pcar
    cash = cash * 6 // 10
    heat = 0
    calm_cops()
    if pcar is not None:
        cars.remove(pcar)
        pcar = None
    say('BUSTED!', 90)
#@
def road_name():
    tx = int(px // 1)
    ty = int(py // 1)
    lx = tx & 15
    ly = ty & 15
    gx = tx >> 4
    gy = ty >> 4
    if lx < 2 and ly >= 2:
        return (('V', gx), STREETS[H(gx + OX, 0, 5) % 16] + ' AVE')
    if ly < 2 and lx >= 2:
        return (('H', gy), STREETS[H(0, gy + OY, 6) % 16] + ' ST')
    return (None, '')
def shift(sx, sy):
    global px, py, camx, camy
    px -= sx
    py -= sy
    camx -= sx
    camy -= sy
    for c in cars:
        c[0] -= sx
        c[1] -= sy
    for p in peds:
        p[0] -= sx
        p[1] -= sy
    for h in hel:
        h[0] -= sx
        h[1] -= sy
#@
def _foot_act(act, auto):
    global hint, cash, n_rob
    near = False
    for c in cars:
        if c[4] != 3 and (c[0] - px) ** 2 + (c[1] - py) ** 2 < ENTER2:
            near = True
            break
    nh = None
    if not near:
        for h in hel:
            if h[5] == 1 and (h[0] - px) ** 2 + (h[1] - py) ** 2 < 2.6:
                nh = h
                break
    sid, nm = near_shop()
    if near:
        hint = 'B:ENTER CAR'
        if act:
            try_enter()
    elif nh is not None:
        hint = 'B:FLY HELI'
        if act:
            enter_heli(nh)
    elif sid is not None:
        if sid in robbed:
            hint = nm + ' CLOSED'
        else:
            hint = 'B:ROB ' + nm
            if act:
                robbed.add(sid)
                n_rob += 1
                g = 25 + random.getrandbits(6)
                if gun:
                    g *= 2
                cash += g
                crime(600, 'ROBBED $' + str(g))
    elif gun:
        hint = 'B:FIRE'
        if act or (auto and wpn == 1):
            fire()
    else:
        tp = None
        bd = 2.6
        for p in peds:
            if not p[5]:
                dd = (p[0] - px) ** 2 + (p[1] - py) ** 2
                if dd < bd:
                    bd = dd
                    tp = p
        if tp is not None:
            hint = 'B:STEAL'
            if act:
                steal(tp)
#@
def _foot(bU, bD, bL, bR, act, auto):
    global ang, px, py
    if pz > 0:
        _air(bU, bD, bL, bR)
        return
    if bL:
        ang -= 0.07
    if bR:
        ang += 0.07
    mv = int(bU) - int(bD)
    if mv:
        s = 0.055 if mv > 0 else -0.03
        nx = px + cos(ang) * s
        ny = py + sin(ang) * s
        if not blocked(nx, py, 0.22):
            px = nx
        if not blocked(px, ny, 0.22):
            py = ny
    _foot_act(act, auto)
    for c in cars:
        if c[4] != 2 and abs(c[3]) > 0.04:
            dx = px - c[0]
            dy = py - c[1]
            if dx * dx + dy * dy < 0.5 + CLEN[c[7]] * 0.2:
                dl = sqrt(dx * dx + dy * dy) + 0.05
                px += dx / dl * 0.12
                py += dy / dl * 0.12
                say('OUCH!', 20)
#@
def _bump(c):
    k = c[7]
    fx = cos(c[2])
    fy = sin(c[2])
    for o in cars:
        if o is c:
            continue
        dx = c[0] - o[0]
        dy = c[1] - o[1]
        if abs(dx) < 3 and abs(dy) < 3:
            al = dx * fx + dy * fy
            la = -dx * fy + dy * fx
            if abs(al) < (CLEN[k] + CLEN[o[7]]) * 0.5 - 0.15 and abs(la) < (CWID[k] + CWID[o[7]]) * 0.5 + 0.12:
                dl = sqrt(dx * dx + dy * dy) + 0.01
                nx = c[0] + dx / dl * 0.08
                ny = c[1] + dy / dl * 0.08
                if not car_blocked(nx, ny, c[2], c):
                    c[0] = nx
                    c[1] = ny
                c[3] *= 0.85
                if o[4] != 2:
                    o[3] *= 0.5
def _runover(c):
    spd = c[3]
    for p in peds:
        if p[5]:
            continue
        dx = p[0] - px
        dy = p[1] - py
        if abs(dx) < 3 and abs(dy) < 3 and (abs(spd) > 0.08):
            dd = dx * dx + dy * dy
            if dd < 0.5 + CLEN[c[7]] * 0.2:
                p[5] = 1
                p[4] = 60
                crime(500, 'HIT AND RUN')
            elif dd < 5:
                flee(p, dx, dy, 0.12)
                p[4] = 15
#@
def _drive(bU, bD, bL, bR, bB, act):
    global ang, px, py, hint
    c = pcar
    top = TOP[c[7]]
    spd = c[3]
    if bU:
        spd += 0.006 * top / 0.3
    elif bD:
        spd -= 0.012 if spd > 0.01 else 0.004
    else:
        spd *= 0.985
    if bB and spd > 0.02:
        spd *= 0.93
    if spd > top:
        spd = top
    elif spd < -0.1:
        spd = -0.1
    st = int(bR) - int(bL)
    if st and abs(spd) > 0.004:
        rate = 0.06 * min(1.0, abs(spd) / 0.08) / (1.0 + 4.0 * abs(spd))
        if bB:
            rate *= 1.5
        na = c[2] + st * rate * (1 if spd > 0 else -1)
        if na > PI:
            na -= 2 * PI
        elif na < -PI:
            na += 2 * PI
        if not car_blocked(c[0], c[1], na, c):
            c[2] = na
    c[3] = spd
    move_car(c)
    _bump(c)
    if (spd > CRASHV or spd < -CRASHV) and abs(c[3]) < abs(spd) * 0.9:
        wasted('CRASH ' + str(int(abs(spd) * 483)) + 'KMH')
    px = c[0]
    py = c[1]
    ang = c[2]
    hint = 'B:EXIT' if abs(spd) < 0.02 else ''
    if act and abs(spd) < 0.02:
        exit_car()
    else:
        _runover(c)
#@
def _crowd():
    ncar = 0
    nparked = 0
    for c in cars:
        if c[4] == 0 or c[4] == 3:
            ai(c)
            if c[4] == 0:
                ncar += 1
        elif c[4] == 2:
            nparked += 1
    ev = tick & 1
    for p in peds:
        dx = p[0] - px
        dy = p[1] - py
        if -24 < dx < 24 and -24 < dy < 24:
            if -5 < dx < 5 and -5 < dy < 5:
                upd_ped(p)
            elif ev == id(p) >> 4 & 1:
                upd_ped(p, 2)
    if tick % 15 == 0:
        cars[:] = [c for c in cars if c is pcar or (abs(c[0] - camx) < (90 if c[4] == 2 else 45) and abs(c[1] - camy) < (90 if c[4] == 2 else 45))]
        peds[:] = [p for p in peds if abs(p[0] - camx) < 28 and abs(p[1] - camy) < 28 and (not p[5] or p[4] > 0)]
    if tick % 5 == 0:
        if ncar < MAXCAR:
            spawn_car(0)
        n = MAXPED - len(peds)
        if n > 0:
            for _ in range(4 if n > 4 else n):
                spawn_ped()
    if tick % 25 == 0 and nparked < 9:
        spawn_parked()
#@
def _law():
    global heat, copd
    copd = 9999.0
    if heat <= 0:
        return
    ncop = 0
    for c in cars:
        if c[4] == 3:
            ncop += 1
    if ncop < (1 if heat < 450 else 2) and tick % 20 == 0:
        spawn_car(3)
    for c in cars:
        if c[4] == 3:
            dx = c[0] - px
            dy = c[1] - py
            dd = dx * dx + dy * dy
            if dd < copd:
                copd = dd
            if dd < 1.7 and pz <= 0 and ph is None and (pcar is None or abs(pcar[3]) < 0.12):
                busted()
                return
    if copd > 400:
        heat -= 1
        if heat <= 0:
            heat = 0
            calm_cops()
            say('WANTED CLEARED', 60)
def update(bU, bD, bL, bR, bB, act, auto=False):
    global fcool, flash, hint, hitf, msgt, rkey, tick, tk, inap
    tick += 1
    tk = tick
    hint = ''
    if ph is not None:
        _fly(bU, bD, bL, bR, act)
    elif pcar is None:
        _foot(bU, bD, bL, bR, act, auto)
    else:
        _drive(bU, bD, bL, bR, bB, act)
    if fcool > 0:
        fcool -= 1
    if flash > 0:
        flash -= 1
    if hitf > 0:
        hitf -= 1
    _crowd()
    poll()
    _heli_tick()
    _law()
    k, nm = road_name()
    if k is not None and k != rkey:
        say(nm, 50)
    if k is not None:
        rkey = k
    ap = is_ap(int(px // 16) + OX, int(py // 16) + OY)
    if ap and not inap:
        say('AIRPORT', 70)
    inap = ap
    if msgt > 0:
        msgt -= 1
        if time.ticks_diff(time.ticks_ms(), mdl) >= 0:
            msgt = 0
#@
def _hgt(x, y):
    m = mp[(int(y // 1) & 63) << 6 | int(x // 1) & 63]
    return (m & 31) * 0.5 if m > 127 else 0.0
def _tz(x, y, a):
    t = 8.0
    for k in (0.0, 2.0, 4.0):
        z = _hgt(x + cos(a) * k, y + sin(a) * k) + 1.8
        if z > t:
            t = z
    return t
def upd_heli(h):
    h[6] -= 1
    if h[6] <= 0:
        h[6] = 90 + random.getrandbits(8)
        dx = camx - h[0]
        dy = camy - h[1]
        if dx * dx + dy * dy > 625:
            h[2] = atan2(dy, dx) + (random.getrandbits(5) - 16) * 0.04
        else:
            h[2] += (random.getrandbits(5) - 16) * 0.05
    if h[3] < 0.1:
        h[3] += 0.002
    h[0] += cos(h[2]) * h[3]
    h[1] += sin(h[2]) * h[3]
    h[4] += max(-0.05, min(0.05, _tz(h[0], h[1], h[2]) - h[4]))
#@
def spawn_heli():
    bx = int(camx // 16)
    by = int(camy // 16)
    for gy in range(by - 2, by + 3):
        for gx in range(bx - 2, bx + 3):
            if is_ap(gx + OX, gy + OY):
                hx = gx * 16 + 11.5
                hy = gy * 16 + 13.5
                if abs(hx - camx) > 36 or abs(hy - camy) > 36:
                    continue
                for h in hel:
                    if abs(h[0] - hx) < 2.5 and abs(h[1] - hy) < 2.5:
                        break
                else:
                    hel.append([hx, hy, 0.0, 0.0, 0.0, 1, 0])
                    return
def spawn_ambient():
    for h in hel:
        if h[5] == 0:
            return
    if random.getrandbits(2):
        return
    a = random.getrandbits(10) * 6.2832 / 1024
    hel.append([camx + cos(a) * 32, camy + sin(a) * 32, a + PI + (random.getrandbits(5) - 16) * 0.04, 0.1, 9.0, 0, 90])
def _heli_tick():
    for h in hel:
        if h[5] == 0:
            upd_heli(h)
    if tick % 15 == 0:
        hel[:] = [h for h in hel if h is ph or abs(h[0] - camx) < (90 if h[5] == 1 else 70) and abs(h[1] - camy) < (90 if h[5] == 1 else 70)]
    if tick % 40 == 0:
        spawn_heli()
    if tick % 60 == 0:
        spawn_ambient()
#@
def enter_heli(h):
    global ph, pz
    ph = h
    h[5] = 2
    h[3] = 0.0
    pz = h[4]
    say('TAKING OFF', 40)
#@
def start():
    newcar(1.5, 4.6, -PI / 2, 0.0, 2, 3, 0.1, 0, 1)
    newcar(0.5, 24.0, PI / 2, 0.0, 2, 1, 0.1, 2, 0)
    for _ in range(8):
        spawn_car(0, True)
    for _ in range(30):
        spawn_ped(True)
    say('GRAND THUMB AUTO', 80)
