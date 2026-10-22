# HOPPY ROAD - endless road-crossing hopper for the Thumby (single file)
# Save as /Games/HoppyRoad/HoppyRoad.py
#
# A or UP = hop forward   LEFT/RIGHT = hop sideways   B or DOWN = hop back
# Hold a button to keep hopping.  DOWN on title = sound on/off
# Dodge cars, ride logs across rivers, watch for TRAINS (lights flash first!)
# and don't dawdle - the eagle comes for slowpokes.  How far can you get?
import math, random, thumby
D = thumby.display
D.setFPS(30)
W = 72
H = 40
HOP = 6
try:
    thumby.saveData.setName("HoppyRoad")
except Exception:
    pass


def beep(f, ms=30):
    if snd:
        try:
            thumby.audio.play(int(f), int(ms))
        except Exception:
            pass


def pix(x, y, c=1):
    x = int(x)
    y = int(y)
    if 0 <= x < W and 0 <= y < H:
        D.setPixel(x, y, c)


def fr(x, y, w, h, c=1):
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
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


def txt(s, x, y):
    fr(x - 1, y, 6 * len(s) + 1, 7, 0)
    D.drawText(s, x, y, 1)


def txtc(s, y):
    txt(s, (W - 6 * len(s)) // 2, y)


snd = True
hi = 0
try:
    if thumby.saveData.hasItem("hi"):
        hi = int(thumby.saveData.getItem("hi"))
except Exception:
    pass

# ------------------------------------------------------------ world
# lane: [type, dir, speed, period, objs, a, b, c]
# types: 0 grass(a=tree cols,b=coin col) 1 road 2 river 3 rail(a=state,b=timer,c=train x)
lanes = {}
gen_top = -1
prev_t = 0
run = 0
ldir = 1
tt = 0.0


def make(t, n, m):
    d = ldir
    if t == 0:
        trees = []
        if n > 1:
            for i in range(random.randint(0, 3)):
                c = random.randint(0, 8)
                if c not in trees:
                    trees.append(c)
        coin = -1
        if random.random() < 0.3:
            c = random.randint(0, 8)
            if c not in trees:
                coin = c
        return [0, d, 0, 0, [], trees, coin, 0]
    if t == 1:
        q = random.random()
        if q < 0.5:
            w = 10
            sp = random.uniform(0.5, 1.0)
            gap = random.randint(24, 40)
        elif q < 0.8:
            w = 16
            sp = random.uniform(0.4, 0.8)
            gap = random.randint(26, 40)
        else:
            w = 6
            sp = random.uniform(1.4, 2.0)
            gap = random.randint(30, 46)
        sp *= m
        seg = w + gap
        k = max(2, -(-80 // seg))
        return [1, d, sp, k * seg, [(i * seg + random.randint(0, 6), w) for i in range(k)], 0, 0, 0]
    if t == 2:
        w = random.randint(16, 24)
        seg = w + random.randint(6, 11)
        k = max(3, -(-80 // seg))
        sp = min(1.1, random.uniform(0.3, 0.7) * m)
        return [2, d, sp, k * seg, [(i * seg, w) for i in range(k)], 0, 0, 0]
    return [3, d, 0, 0, [], 0, random.randint(40, 160), -120.0]


def gen_to(r):
    global gen_top, prev_t, run, ldir
    while gen_top < r:
        gen_top += 1
        n = gen_top
        m = 1 + min(1.0, n / 90.0)
        t = 0
        if n >= 3:
            wt = [3, 5, 0, 0]
            if n > 7:
                wt[2] = 2 + min(2, (n - 7) // 10)
            if n > 10:
                wt[3] = 1 + min(1, (n - 10) // 25)
            if prev_t == 0 and run >= 3:
                wt[0] = 0
            if prev_t != 0 and run >= 3:
                wt = [1, 0, 0, 0]
            roll = random.randint(1, sum(wt))
            for i in range(4):
                roll -= wt[i]
                if roll <= 0:
                    t = i
                    break
        if t == prev_t:
            run += 1
        else:
            run = 1
            prev_t = t
        ldir = -ldir
        lanes[n] = make(t, n, m)


def opos(l, b):
    return (b + l[1] * l[2] * tt) % l[3]


def upd_rail(l):
    if l[5] == 0:
        l[6] -= 1
        if l[6] <= 0:
            l[5] = 1
            l[6] = 45
    elif l[5] == 1:
        l[6] -= 1
        if l[6] % 15 == 0:
            beep(1100, 40)
        if l[6] <= 0:
            l[5] = 2
            l[7] = -112.0 if l[1] > 0 else W + 4.0
            beep(200, 150)
    else:
        l[7] += l[1] * 6
        if l[7] > W + 6 or l[7] < -120:
            l[5] = 0
            l[6] = random.randint(80, 200)


# ------------------------------------------------------------ state
state = 0
frame = 0
prow = 1
frow = 1
px = 36.0
fx = 36.0
tx = 36.0
hop_t = 0
face = 0
want = None
hold = 0
cam = 0.0
max_row = 1
bonus = 0
idle = 0
dead_t = -1
cause = 0
over_t = 0
new_hi = False
near_cd = 0
pops = []
parts = []
pf = pl = pr = pb = False


def new_game():
    global state, gen_top, prev_t, run, ldir, tt, prow, frow, px, fx, tx, hop_t, want, cam, max_row
    global bonus, idle, dead_t, new_hi, frame, hold
    lanes.clear()
    del pops[:]
    del parts[:]
    gen_top = -1
    prev_t = 0
    run = 0
    ldir = 1
    tt = 0.0
    prow = frow = 1
    px = fx = tx = 36.0
    hop_t = 0
    want = None
    cam = 0.0
    max_row = 1
    bonus = 0
    idle = 0
    dead_t = -1
    new_hi = False
    frame = 0
    hold = 0
    gen_to(12)
    state = 1


def die(c):
    global dead_t, cause
    if dead_t >= 0:
        return
    dead_t = 45
    cause = c
    beep((120, 200, 150, 400)[c], 250)
    for i in range(14):
        a = random.random() * 6.28
        s = random.random() * 1.6
        parts.append([px, 24, math.cos(a) * s, math.sin(a) * s - 0.5, random.randint(8, 18)])


def on_log(l, x):
    for b, w in l[4]:
        p = opos(l, b)
        if (p <= x <= p + w) or (p - l[3] <= x <= p - l[3] + w):
            return True
    return False


def hop(dc, dr):
    global hop_t, frow, prow, fx, tx, face, hold
    r1 = prow + dr
    if r1 < int(cam):
        return
    gen_to(r1 + 8)
    l = lanes[r1]
    x1 = px + dc * 8
    if l[0] != 2:
        col = int(x1 // 8)
        if col < 0 or col > 8:
            return
        x1 = col * 8 + 4
        if l[0] == 0 and col in l[5]:
            beep(150, 30)
            return
    elif x1 < 3 or x1 > 69:
        return
    frow = prow
    prow = r1
    fx = px
    tx = x1
    hop_t = 1
    face = dc
    beep(500 + 20 * min(max_row, 20), 20)


def update():
    global tt, px, hop_t, want, hold, cam, max_row, bonus, idle, dead_t, state, hi, new_hi, over_t, near_cd
    global pf, pl, pr, pb
    f = thumby.buttonU.pressed() or thumby.buttonA.pressed()
    lf = thumby.buttonL.pressed()
    rt = thumby.buttonR.pressed()
    bk = thumby.buttonD.pressed() or thumby.buttonB.pressed()
    ef = f and not pf
    el = lf and not pl
    er = rt and not pr
    eb = bk and not pb
    pf, pl, pr, pb = f, lf, rt, bk
    hold = hold + 1 if (f or lf or rt or bk) else 0
    tt += 1
    for r in range(int(cam) - 1, int(cam) + 7):
        if r in lanes and lanes[r][0] == 3:
            upd_rail(lanes[r])
    for p in pops:
        p[2] -= 0.5
        p[3] -= 1
    pops[:] = [p for p in pops if p[3] > 0]
    for p in parts:
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.1
        p[4] -= 1
    parts[:] = [p for p in parts if p[4] > 0]
    if dead_t >= 0:
        dead_t -= 1
        if dead_t == 0:
            state = 2
            over_t = 0
            s = max_row - 1 + bonus
            if s > hi:
                hi = s
                new_hi = True
                try:
                    thumby.saveData.setItem("hi", hi)
                    thumby.saveData.save()
                except Exception:
                    pass
        return
    # input
    d = None
    if ef:
        d = (0, 1)
    elif el:
        d = (-1, 0)
    elif er:
        d = (1, 0)
    elif eb:
        d = (0, -1)
    elif hold > 12:
        d = (0, 1) if f else ((-1, 0) if lf else ((1, 0) if rt else ((0, -1) if bk else None)))
    if hop_t > 0:
        if d is not None and (ef or el or er or eb):
            want = d
        hop_t += 1
        p = hop_t / HOP
        px = fx + (tx - fx) * min(1.0, p)
        if hop_t > HOP:
            hop_t = 0
            px = tx
            l = lanes[prow]
            if l[0] == 2 and not on_log(l, px):
                die(1)
            if l[0] == 0 and l[6] == int(px // 8):
                l[6] = -1
                bonus += 3
                pops.append(["+3", px - 5, 20, 20])
                beep(1300, 60)
            if prow > max_row:
                max_row = prow
                idle = 0
            if want is not None:
                hop(want[0], want[1])
                want = None
    elif d is not None:
        hop(d[0], d[1])
    # riding logs
    if hop_t == 0 and dead_t < 0:
        l = lanes[prow]
        if l[0] == 2:
            px += l[1] * l[2]
            if px < 2 or px > 70 or not on_log(l, px):
                die(1)
    # camera / idle
    tg = prow - 1
    if tg > cam:
        cam += (tg - cam) * 0.2
    idle += 1
    if idle == 150:
        beep(900, 100)
    if idle >= 210:
        die(3)
    # collisions
    r = frow if (hop_t > 0 and hop_t < HOP // 2) else prow
    l = lanes[r]
    if l[0] == 1:
        hit = False
        near = False
        for b, w in l[4]:
            p = opos(l, b)
            for xx in (p, p - l[3]):
                if xx < px + 3 and xx + w > px - 3:
                    hit = True
                elif xx < px + 6 and xx + w > px - 6:
                    near = True
        if hit:
            die(0)
        elif near and near_cd <= 0:
            near_cd = 25
            bonus += 1
            pops.append(["+1", px - 5, 20, 14])
            beep(1500, 20)
    elif l[0] == 3 and l[5] == 2:
        if l[7] < px + 3 and l[7] + 112 > px - 3:
            die(2)
    if near_cd > 0:
        near_cd -= 1


# ------------------------------------------------------------ drawing
def car(x, sy, w, d):
    x = int(x)
    if w == 10:
        fr(x, sy + 3, 10, 4)
        fr(x + 2, sy + 1, 6, 2)
        pix(x + 3, sy + 2, 0)
        pix(x + 6, sy + 2, 0)
        pix(x + 2, sy + 6, 0)
        pix(x + 7, sy + 6, 0)
        pix(x + (10 if d > 0 else -1), sy + 4)
    elif w == 16:
        cx = x + 10 if d > 0 else x
        fr(x + (0 if d > 0 else 6), sy + 2, 10, 5)
        fr(cx, sy + 1, 6, 6)
        pix(cx + (4 if d > 0 else 1), sy + 2, 0)
        pix(x + 2, sy + 4, 0)
        pix(x + 5, sy + 4, 0)
        pix(x + 12, sy + 7, 0)
    else:
        fr(x + 1, sy + 3, 4, 2)
        pix(x, sy + 5)
        pix(x + 5, sy + 5)
        pix(x + (5 if d > 0 else 0), sy + 2)


def lane_bg(l, r, sy):
    t = l[0]
    if t == 0:
        for i in range(5):
            pix((r * 37 + i * 17) % W, sy + (r * 13 + i * 5) % 8)
        for c in l[5]:
            x = c * 8
            fr(x + 1, sy, 6, 5)
            pix(x + 1, sy, 0)
            pix(x + 6, sy, 0)
            fr(x + 3, sy + 5, 2, 3)
            pix(x + 3, sy + 1, 0)
        if l[6] >= 0:
            x = l[6] * 8 + 4
            pix(x, sy + 2)
            pix(x - 1, sy + 3)
            pix(x + 1, sy + 3)
            pix(x, sy + 4)
            if (frame // 6) % 2 == 0:
                pix(x, sy + 3)
    elif t == 1:
        for x in range(0, W, 8):
            fr(x + 1, sy + 3, 4, 1)
    elif t == 2:
        for x in range(0, W, 6):
            pix(x + (frame // 8) % 3, sy + 1 + ((x // 6) % 2) * 5)
    else:
        fr(0, sy + 2, W, 1)
        fr(0, sy + 5, W, 1)
        for x in range(0, W, 6):
            pix(x, sy + 3)
            pix(x, sy + 4)
        if l[5] == 1 and (frame // 4) % 2 == 0:
            fr(2, sy, 3, 2)
            fr(W - 5, sy, 3, 2)


def lane_obj(l, sy):
    t = l[0]
    if t == 1:
        for b, w in l[4]:
            p = opos(l, b)
            car(p, sy, w, l[1])
            car(p - l[3], sy, w, l[1])
    elif t == 2:
        for b, w in l[4]:
            p = opos(l, b)
            for xx in (p, p - l[3]):
                xx = int(xx)
                fr(xx, sy + 2, w, 5)
                pix(xx, sy + 2, 0)
                pix(xx + w - 1, sy + 2, 0)
                pix(xx, sy + 6, 0)
                pix(xx + w - 1, sy + 6, 0)
                for k in range(3, w - 2, 5):
                    pix(xx + k, sy + 4, 0)
                    pix(xx + k + 1, sy + 4, 0)
    elif t == 3 and l[5] == 2:
        x = int(l[7])
        fr(x, sy + 1, 112, 6)
        for k in range(4, 112, 7):
            pix(x + k, sy + 3, 0)
            pix(x + k + 1, sy + 3, 0)
        fr(x + (108 if l[1] > 0 else 0), sy + 2, 4, 2, 0)


def chicken(x, y, d):
    x = int(x)
    y = int(y)
    fr(x - 2, y - 4, 5, 4)
    fr(x - 1, y - 6, 3, 2)
    pix(x, y - 7)
    pix(x + d * 2, y - 5)
    pix(x + d, y - 5, 0)
    pix(x - 1, y)
    pix(x + 1, y)


def draw_world(c):
    for r in range(int(c) - 1, int(c) + 6):
        if r not in lanes:
            continue
        sy = int(round(32 - (r - c) * 8))
        l = lanes[r]
        lane_bg(l, r, sy)
        lane_obj(l, sy)


def draw_play():
    draw_world(cam)
    rf = frow + (prow - frow) * min(1.0, hop_t / HOP) if hop_t > 0 else prow
    sy = int(round(32 - (rf - cam) * 8))
    arc = int(math.sin(min(1.0, hop_t / HOP) * 3.1416) * 5) if hop_t > 0 else 0
    if dead_t < 0:
        if idle > 150 and (frame // 4) % 2 == 0:
            txt("!", int(px) - 2, 0)
        if idle > 185:
            ey = int((idle - 185) * 1.3) - 8
            fr(px - 8, ey, 17, 2)
            fr(px - 3, ey + 2, 7, 3)
        chicken(px, sy + 7 - arc, face)
    elif cause == 0:
        fr(px - 3, sy + 6, 7, 2)
    elif cause == 1:
        for k in range(3):
            D.drawRectangle(int(max(0, min(W - 3, px - 2 - k * 2 - (45 - dead_t) // 6))), sy + 4 + k, 4 + k * 4, 1, 1)
    for p in parts:
        pix(p[0], p[1])
    for p in pops:
        D.drawText(p[0], int(max(0, min(W - 6 * len(p[0]), p[1]))), int(max(0, min(33, p[2]))), 1)
    txt(str(max_row - 1 + bonus), 1, 0)
    if frame < 90:
        txtc(("A:HOP FORWARD", "L/R SIDEWAYS")[(frame // 45) % 2][:12], 33)


# ------------------------------------------------------------ screens
def title():
    global frame, snd, tt
    frame += 1
    tt += 1
    draw_world(4.0)
    t = frame % 30
    chicken(36 + int(math.sin(frame * 0.06) * 18), 31 - int(math.sin(t / 30.0 * 3.1416) * 5), 0)
    fr(2, 0, 68, 18, 0)
    D.drawRectangle(2, 0, 68, 18, 1)
    D.drawText("HOPPY ROAD", 5, 2, 1)
    D.drawText("HOPPY ROAD", 6, 2, 1)
    ph = (frame // 40) % 3
    s = ("A:PLAY", "BEST " + str(hi), "D:SND ON" if snd else "D:SND OFF")[ph]
    D.drawText(s, (W - 6 * len(s)) // 2, 10, 1)


def gameover():
    global frame
    draw_world(cam)
    fr(5, 3, 62, 34, 0)
    D.drawRectangle(5, 3, 62, 34, 1)
    s = ("SPLAT!", "SPLASH!", "TRAIN!", "EAGLE!")[cause]
    D.drawText(s, (W - 6 * len(s)) // 2, 6, 1)
    s = "SCORE " + str(max_row - 1 + bonus)
    D.drawText(s, (W - 6 * len(s)) // 2, 15, 1)
    s = "NEW BEST!" if (new_hi and frame % 20 < 12) else "BEST " + str(hi)
    D.drawText(s, (W - 6 * len(s)) // 2, 23, 1)
    if frame % 40 < 28:
        D.drawText("A:RETRY", 15, 30, 1)


gen_to(14)
ap = bp = dp = False
while True:
    D.fill(0)
    a = thumby.buttonA.pressed()
    b = thumby.buttonB.pressed()
    dn = thumby.buttonD.pressed()
    if state == 0:
        title()
        if dn and not dp:
            snd = not snd
            beep(800, 40)
        if a and not ap:
            new_game()
            pf = True
            beep(900, 60)
    elif state == 1:
        frame += 1
        update()
        draw_play()
    else:
        frame += 1
        over_t += 1
        gameover()
        if over_t > 20:
            if a and not ap:
                new_game()
                pf = True
            elif b and not bp:
                state = 0
    ap = a
    bp = b
    dp = dn
    D.update()
