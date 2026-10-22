# NEON GRID - light-cycle duels for the Thumby (single file)
# Save as /Games/NeonGrid/NeonGrid.py
#
# D-PAD = steer (you can't reverse)   A (hold) = BOOST (uses energy)
# B (hold) = BRAKE for precise turns  DOWN on title = sound on/off
# Trap the rival cycles so they crash into walls or trails. Last one riding wins!
# Pickups:  hourglass = refill boost | shield = survive one crash (auto-swerve)
#           bomb = blast away nearby rivals and trails
import math, random, thumby
D = thumby.display
D.setFPS(30)
W = 72
H = 40
GW = 36
GH = 17
OY = 6
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)
try:
    thumby.saveData.setName("NeonGrid")
except Exception:
    pass
snd = True
hi = 0
try:
    if thumby.saveData.hasItem("hi"):
        hi = int(thumby.saveData.getItem("hi"))
except Exception:
    pass


def beep(f, ms=30):
    if snd:
        try:
            thumby.audio.play(int(f), int(ms))
        except Exception:
            pass


g = bytearray(GW * GH)
cyc = []
pk = []
parts = []
state = 0
frame = 0
rnd = 0
score = 0
tk = 0
par = 0
banner_t = 0
dead_t = -1
clear_t = 0
pk_t = 200
energy = 100.0
shield = False
pwant = 1
tc = 0
new_hi = False
over_t = 0
SPR = {"E": ("XXXX", ".XX.", ".XX.", "XXXX"), "S": ("XXXX", "X..X", "X..X", ".XX."),
       "B": (".XX.", "XXXX", "XXXX", ".XX.")}
TD = {"0": ("XXX", "X.X", "X.X", "X.X", "XXX"), "1": (".X.", "XX.", ".X.", ".X.", "XXX"),
      "2": ("XXX", "..X", "XXX", "X..", "XXX"), "3": ("XXX", "..X", "XXX", "..X", "XXX"),
      "4": ("X.X", "X.X", "XXX", "..X", "..X"), "5": ("XXX", "X..", "XXX", "..X", "XXX"),
      "6": ("XXX", "X..", "XXX", "X.X", "XXX"), "7": ("XXX", "..X", "..X", ".X.", ".X."),
      "8": ("XXX", "X.X", "XXX", "X.X", "XXX"), "9": ("XXX", "X.X", "XXX", "..X", "XXX"),
      "R": ("XX.", "X.X", "XX.", "X.X", "X.X")}


def tiny(s, x, y):
    for ch in s:
        gl = TD.get(ch)
        if gl:
            for j in range(5):
                for i in range(3):
                    if gl[j][i] == "X":
                        D.setPixel(x + i, y + j, 1)
        x += 4


def cell(cx, cy):
    v = g[cy * GW + cx]
    x = cx * 2
    y = OY + cy * 2
    D.drawFilledRectangle(x, y, 2, 2, 1 if v else 0)
    if v == 2:
        D.setPixel(x + 1, y + 1, 0)
    elif v == 3:
        D.setPixel(x, y, 0)
    elif v == 4:
        D.setPixel(x, y + 1, 0)


def spr(p, on):
    x = p[0] * 2 - 1
    y = OY + p[1] * 2 - 1
    s = SPR[p[2]]
    if on:
        for j in range(4):
            for i in range(4):
                if s[j][i] == "X" and 0 <= x + i < W and OY <= y + j < H:
                    D.setPixel(x + i, y + j, 1)
    else:
        for j in range(4):
            for i in range(4):
                if 0 <= x + i < W and OY <= y + j < H:
                    D.setPixel(x + i, y + j, 0)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                a = p[0] + dx
                b = p[1] + dy
                if 0 <= a < GW and 0 <= b < GH:
                    cell(a, b)


def redraw():
    D.fill(0)
    D.drawLine(0, 5, W - 1, 5, 1)
    for i in range(GW * GH):
        if g[i]:
            cell(i % GW, i // GW)
    for p in pk:
        spr(p, True)


def fc(x, y, d, n):
    c = 0
    for i in range(n):
        x += DX[d]
        y += DY[d]
        if x < 0 or y < 0 or x >= GW or y >= GH or g[y * GW + x]:
            break
        c += 1
    return c


def burst(x, y, n, s=1.6):
    for i in range(n):
        if len(parts) < 36:
            a = random.random() * 6.283
            v = random.random() * s + 0.3
            parts.append([x, y, math.cos(a) * v, math.sin(a) * v, random.randint(6, 14)])


def next_round():
    global rnd, tk, banner_t, energy, pwant, pk_t, dead_t, clear_t, par
    rnd += 1
    g[:] = bytearray(GW * GH)
    del cyc[:]
    del pk[:]
    del parts[:]
    cyc.append([3, 8, 1, 1, 1])
    n = min(3, 1 + (rnd - 1) // 2)
    st = ((32, 3, 3), (20, 0, 2), (20, 16, 0))
    for i in range(n):
        cyc.append([st[i][0], st[i][1], st[i][2], 1, 2 + i])
    for c in cyc:
        g[c[1] * GW + c[0]] = c[4]
    for i in range(min(10, rnd)):
        for t in range(10):
            x = random.randint(2, GW - 3)
            y = random.randint(1, GH - 2)
            ok = True
            for c in cyc:
                if abs(c[0] - x) < 5 and abs(c[1] - y) < 5:
                    ok = False
            if ok and not g[y * GW + x]:
                g[y * GW + x] = 5
                break
    pwant = 1
    energy = 100.0
    tk = 0
    par = 0
    pk_t = 150
    dead_t = -1
    clear_t = 0
    banner_t = 50
    redraw()
    D.drawFilledRectangle(14, 15, 44, 11, 0)
    D.drawRectangle(14, 15, 44, 11, 1)
    s = "ROUND " + str(rnd)
    D.drawText(s, (W - 6 * len(s)) // 2, 17, 1)


def new_game():
    global state, rnd, score, shield, new_hi, frame
    state = 1
    rnd = 0
    score = 0
    shield = False
    new_hi = False
    frame = 0
    next_round()


def die(c):
    global score, dead_t
    c[3] = 0
    n = 0
    for i in range(GW * GH):
        if g[i] == c[4]:
            g[i] = 0
            cell(i % GW, i // GW)
            n += 1
            if n % 4 == 0:
                burst(i % GW * 2 + 1, OY + i // GW * 2 + 1, 2, 1.2)
    if c[4] == 1:
        dead_t = 45
        burst(c[0] * 2 + 1, OY + c[1] * 2 + 1, 26, 2.2)
        beep(110, 300)
    else:
        score += 10
        burst(c[0] * 2 + 1, OY + c[1] * 2 + 1, 14, 2.0)
        beep(300, 120)


def blast():
    global score
    p = cyc[0]
    for c in cyc[1:]:
        if c[3] and abs(c[0] - p[0]) + abs(c[1] - p[1]) <= 7:
            die(c)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            if abs(dx) + abs(dy) <= 7:
                x = p[0] + dx
                y = p[1] + dy
                if 0 <= x < GW and 0 <= y < GH and g[y * GW + x] > 1:
                    g[y * GW + x] = 0
                    cell(x, y)
    for k in range(20):
        a = k * 0.314
        burst(p[0] * 2 + 1, OY + p[1] * 2 + 1, 1, 2.5)
    beep(150, 250)


def grab(p):
    global energy, shield
    for q in pk[:]:
        if q[0] == p[0] and q[1] == p[1]:
            pk.remove(q)
            if q[2] == "E":
                energy = 100.0
            elif q[2] == "S":
                shield = True
            else:
                blast()
            beep(1200, 120)


def advance(movers):
    global shield
    tl = []
    cnt = {}
    for c in movers:
        nx = c[0] + DX[c[2]]
        ny = c[1] + DY[c[2]]
        bl = nx < 0 or ny < 0 or nx >= GW or ny >= GH or g[ny * GW + nx] != 0
        if bl and c[4] == 1 and shield:
            for nd in ((c[2] + 1) & 3, (c[2] + 3) & 3):
                ax = c[0] + DX[nd]
                ay = c[1] + DY[nd]
                if 0 <= ax < GW and 0 <= ay < GH and not g[ay * GW + ax]:
                    c[2] = nd
                    nx = ax
                    ny = ay
                    bl = False
                    shield = False
                    beep(900, 150)
                    break
        tl.append([c, nx, ny, bl])
        if not bl:
            cnt[(nx, ny)] = cnt.get((nx, ny), 0) + 1
    for c, nx, ny, bl in tl:
        if bl or cnt[(nx, ny)] > 1:
            die(c)
        else:
            c[0] = nx
            c[1] = ny
            g[ny * GW + nx] = c[4]
            cell(nx, ny)
            if c[4] == 1:
                grab(c)


def ai(c):
    x = c[0]
    y = c[1]
    d = c[2]
    l = (d + 3) & 3
    r = (d + 1) & 3
    f = fc(x, y, d, 12)
    if f == 0 and random.random() < max(0.0, 0.35 - 0.04 * (rnd - 1)):
        return
    if f < 4 or random.random() < 0.05:
        fl = fc(x, y, l, 12)
        frr = fc(x, y, r, 12)
        if f < 4:
            if fl > frr:
                nd = l
            elif frr > fl:
                nd = r
            else:
                nd = l if random.random() < 0.5 else r
            if max(fl, frr) > f or f == 0:
                c[2] = nd
        elif max(fl, frr) > 5:
            c[2] = l if fl >= frr else r
    p = cyc[0]
    if p[3] and f >= 4 and random.random() < min(0.3, 0.01 + 0.03 * rnd):
        cand = []
        if p[0] > x:
            cand.append(1)
        elif p[0] < x:
            cand.append(3)
        if p[1] > y:
            cand.append(2)
        elif p[1] < y:
            cand.append(0)
        for nd in cand:
            if nd != ((c[2] + 2) & 3) and fc(x, y, nd, 6) >= 5:
                c[2] = nd
                break


def tick():
    global energy, par, clear_t, banner_t, score, tc
    p = cyc[0]
    mv = []
    tc += 1
    slow = rnd <= 2 and tc % 3 == 0 or (rnd <= 4 and tc % 6 == 0)
    for c in cyc[1:]:
        if c[3] and not slow:
            ai(c)
            mv.append(c)
    skip = False
    if thumby.buttonB.pressed():
        par ^= 1
        skip = par == 1
    if p[3] and not skip:
        p[2] = pwant
        mv.append(p)
    advance(mv)
    if p[3] and not skip and thumby.buttonA.pressed() and energy >= 5:
        energy -= 5
        advance([p])
        if frame % 6 == 0:
            beep(700, 15)
    elif energy < 100:
        energy += 0.7
    if p[3]:
        alive = False
        for c in cyc[1:]:
            if c[3]:
                alive = True
        if not alive and clear_t == 0:
            clear_t = 40
            score += 50
            beep(1400, 200)
            D.drawFilledRectangle(14, 15, 44, 11, 0)
            D.drawRectangle(14, 15, 44, 11, 1)
            D.drawText("CLEAR!", 18, 17, 1)


def play():
    global frame, tk, pwant, banner_t, dead_t, clear_t, pk_t, state, hi, new_hi, over_t, energy
    frame += 1
    p = cyc[0]
    d = p[2]
    if thumby.buttonU.pressed() and d != 2:
        pwant = 0
    elif thumby.buttonD.pressed() and d != 0:
        pwant = 2
    elif thumby.buttonL.pressed() and d != 1:
        pwant = 3
    elif thumby.buttonR.pressed() and d != 3:
        pwant = 1
    if banner_t > 0:
        banner_t -= 1
        if banner_t == 0:
            redraw()
    elif dead_t < 0 and clear_t == 0:
        tk += 1
        if tk >= (3 if rnd < 8 else 2):
            tk = 0
            tick()
        pk_t -= 1
        if pk_t <= 0:
            pk_t = random.randint(150, 300)
            if len(pk) < 2:
                for t in range(12):
                    x = random.randint(2, GW - 3)
                    y = random.randint(2, GH - 3)
                    if abs(x - p[0]) + abs(y - p[1]) > 6 and fc(x, y, 0, 2) == 2 and not g[y * GW + x]:
                        q = [x, y, random.choice("EESSB")]
                        pk.append(q)
                        spr(q, True)
                        break
    elif clear_t > 0:
        clear_t -= 1
        if clear_t == 0:
            next_round()
            return
    # particles
    kp = []
    for q in parts:
        cx = int(q[0] // 2)
        cy = int((q[1] - OY) // 2)
        if 0 <= cx < GW and 0 <= cy < GH:
            cell(cx, cy)
        q[0] += q[2]
        q[1] += q[3]
        q[4] -= 1
        if q[4] > 0:
            kp.append(q)
            if 0 <= q[0] < W and OY <= q[1] < H:
                D.setPixel(int(q[0]), int(q[1]), 1)
    parts[:] = kp
    if frame % 8 == 0:
        for q in pk:
            spr(q, (frame // 8) % 2 == 0)
    # heads blink
    for c in cyc:
        if c[3]:
            if (frame // 3) % 2 == 0 or c[4] != 1:
                cell(c[0], c[1])
            else:
                D.drawFilledRectangle(c[0] * 2, OY + c[1] * 2, 2, 2, 0)
                D.setPixel(c[0] * 2, OY + c[1] * 2, 1)
    # HUD
    D.drawFilledRectangle(0, 0, W, 5, 0)
    tiny(str(score), 0, 0)
    tiny("R" + str(rnd), 26, 0)
    if shield:
        D.drawFilledRectangle(40, 0, 4, 3, 1)
        D.setPixel(41, 3, 1)
        D.setPixel(42, 3, 1)
    D.drawFilledRectangle(48, 1, int(energy * 0.22) + 1, 3, 1)
    D.setPixel(47, 1, 1)
    D.setPixel(47, 3, 1)
    if dead_t > 0:
        dead_t -= 1
        if dead_t == 0:
            state = 2
            over_t = 0
            if score > hi:
                hi = score
                new_hi = True
                try:
                    thumby.saveData.setItem("hi", hi)
                    thumby.saveData.save()
                except Exception:
                    pass


def title():
    global frame
    frame += 1
    for k in range(0, 72, 8):
        for j in range(0, 40, 8):
            D.setPixel(k, j, 1)
    per = 2 * (62 + 28)
    for who in range(2):
        s = (frame * 1.6 + who * per / 2) % per
        for k in range(0, 40, 2):
            q = (s - k) % per
            if q < 62:
                x, y = 5 + q, 5
            elif q < 90:
                x, y = 67, 5 + (q - 62)
            elif q < 152:
                x, y = 67 - (q - 90), 33
            else:
                x, y = 5, 33 - (q - 152)
            D.setPixel(int(x), int(y), 1)
            if k < 6:
                D.setPixel(int(x) + 1, int(y), 1)
                D.setPixel(int(x), int(y) + 1, 1)
    D.drawFilledRectangle(5, 9, 62, 23, 0)
    D.drawRectangle(5, 9, 62, 23, 1)
    D.drawText("NEON GRID", 8, 12, 1)
    D.drawText("NEON GRID", 9, 12, 1)
    ph = (frame // 40) % 4
    s = ("A:START", "BEST " + str(hi), "A:BOOST", "D:SND ON" if snd else "D:SND OFF")[ph]
    D.drawText(s, (W - 6 * len(s)) // 2, 22, 1)


def gameover():
    global frame
    frame += 1
    D.drawFilledRectangle(8, 6, 56, 30, 0)
    D.drawRectangle(8, 6, 56, 30, 1)
    D.drawText("DEREZZED", 12, 9, 1)
    s = "SCORE " + str(score)
    D.drawText(s, (W - 6 * len(s)) // 2, 18, 1)
    s = "NEW BEST!" if (new_hi and frame % 20 < 12) else "BEST " + str(hi)
    D.drawText(s, (W - 6 * len(s)) // 2, 27, 1)


ap = dp = bp = False
while True:
    a = thumby.buttonA.pressed()
    b = thumby.buttonB.pressed()
    dn = thumby.buttonD.pressed()
    if state == 0:
        D.fill(0)
        title()
        if dn and not dp:
            snd = not snd
            beep(800, 40)
        if a and not ap:
            new_game()
            beep(900, 60)
    elif state == 1:
        play()
    else:
        over_t += 1
        gameover()
        if over_t > 25:
            if a and not ap:
                new_game()
            elif b and not bp:
                state = 0
    ap = a
    bp = b
    dp = dn
    D.update()
