# PIN BLAST - physics pinball for the Thumby (single file)
# Save as /Games/PinBlast/PinBlast.py
#
# The table is rotated so it fits the wide screen: gravity pulls LEFT, the
# flippers are on the left edge, and the plunger lane runs along the bottom.
#
# HOLD A = pull the plunger, release to launch (hold longer = harder)
# LEFT = flipper on the screen's top side     A or B or RIGHT = flipper on the bottom side
# UP = nudge the table (careful - too many nudges = TILT)    DOWN on title = sound
# Hit the 3 targets to raise the multiplier (x5 then a NEW TABLE!). Pop bumpers
# charge MULTIBALL. 3 balls. How high can you score?
import math, random, thumby
D = thumby.display
D.setFPS(30)
W = 72
H = 40
sqrt = math.sqrt
sin = math.sin
cos = math.cos
HT = 72.0
R = 1.5
G = 0.105
VMAX = 4.4
try:
    thumby.saveData.setName("PinBlast")
except Exception:
    pass
snd = True
hi = 0
try:
    if thumby.saveData.hasItem("hi"):
        hi = int(thumby.saveData.getItem("hi"))
except Exception:
    pass


def beep(f, ms=20):
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


def ln(a, b, c, d):
    a = int(a)
    b = int(b)
    c = int(c)
    d = int(d)
    if 0 <= a < W and 0 <= c < W and 0 <= b < H and 0 <= d < H:
        D.drawLine(a, b, c, d, 1)
        return
    n = max(abs(c - a), abs(d - b), 1)
    for i in range(n + 1):
        pix(a + (c - a) * i // n, b + (d - b) * i // n)


def S(u, v):
    return 71 - v, 5 + u


TD = {"0": ("XXX", "X.X", "X.X", "X.X", "XXX"), "1": (".X.", "XX.", ".X.", ".X.", "XXX"),
      "2": ("XXX", "..X", "XXX", "X..", "XXX"), "3": ("XXX", "..X", "XXX", "..X", "XXX"),
      "4": ("X.X", "X.X", "XXX", "..X", "..X"), "5": ("XXX", "X..", "XXX", "..X", "XXX"),
      "6": ("XXX", "X..", "XXX", "X.X", "XXX"), "7": ("XXX", "..X", "..X", ".X.", ".X."),
      "8": ("XXX", "X.X", "XXX", "X.X", "XXX"), "9": ("XXX", "X.X", "XXX", "..X", "XXX"),
      "x": ("...", "X.X", ".X.", "X.X", "...")}


def tiny(s, x, y):
    for ch in s:
        gl = TD.get(ch)
        if gl:
            for j in range(5):
                for i in range(3):
                    if gl[j][i] == "X":
                        pix(x + i, y + j)
        x += 4


# ------------------------------------------------------------ table (portrait coords u,v)
# walls: (u1, v1, u2, v2, bounce, kick)
WALLS = [
    (0.5, 52, 0.5, 18, 0.35, 0, 0), (0.5, 18, 3, 10, 0.35, 0, 0), (3, 10, 9, 5, 0.35, 0, 0),
    (9, 5, 15, 2.5, 0.35, 0, 0), (15, 2.5, 21, 3.5, 0.35, 0, 0), (21, 3.5, 26, 6, 0.35, 0, 0),
    (26, 6, 30, 10, 0.35, 0, 0), (30, 10, 34, 17, 0.35, 0, 0), (34, 17, 34, 70, 0.3, 0, 0),
    (29.5, 22, 29.5, 68, 0.3, 0, 0), (29.5, 68, 34, 68, 0.1, 0, 0),
    (0.5, 52, 5.5, 60, 0.3, 0, 0), (29.5, 50, 24.5, 60, 0.3, 0, 0),
    (4.5, 43, 9, 52, 0.5, 2.6, 0), (25.5, 43, 21, 52, 0.5, 2.6, 0),
    (34, 18.5, 29.5, 22, 0.3, 0, 1),
]
LAYOUTS = (
    ((10, 27, 3.0), (20, 27, 3.0), (15, 36, 3.0), (15, 18, 2.5)),
    ((8, 22, 3.0), (22, 22, 3.0), (15, 29, 3.5), (10, 38, 2.5), (20, 38, 2.5)),
    ((15, 21, 4.0), (7, 32, 2.5), (23, 32, 2.5), (15, 40, 2.5), (9, 15, 2.0), (21, 15, 2.0)),
)
TARGETS = ((8, 12), (15, 9.5), (22, 12))
FL = 7.0
PIV = ((6.0, 60.0), (24.0, 60.0))
REST = (0.49, 3.1416 - 0.49)
ACT = (-0.45, 3.1416 + 0.45)
LANE = 31.75

# ------------------------------------------------------------ state
state = 0
frame = 0
score = 0
balls_left = 3
mult = 1
layout = 0
mode = 0
charge = 0.0
balls = []
tg = [True, True, True]
fa = [REST[0], REST[1]]
fh = [0, 0]
fcool = [0, 0]
flash = {}
bcool = {}
idle_t = 0
tflash = 0
bump_hits = 0
save_t = 0
saved = False
nudges = 0
nudge_t = 0
tilt = False
banner_t = 0
banner_s = ""
next_extra = 20000
new_hi = False
over_t = 0
auto = False
parts = []


def banner(s, t=45):
    global banner_s, banner_t
    banner_s = s
    banner_t = t


def serve():
    global mode, charge, tilt, nudges, saved
    del balls[:]
    balls.append([LANE, 66.2, 0.0, 0.0, 0])
    mode = 0
    charge = 0.0
    tilt = False
    nudges = 0


def new_game():
    global state, score, balls_left, mult, layout, tg, bump_hits, save_t, next_extra, new_hi, frame, banner_t
    state = 1
    score = 0
    balls_left = 3
    mult = 1
    layout = 0
    tg = [True, True, True]
    bump_hits = 0
    save_t = 0
    next_extra = 25000
    new_hi = False
    frame = 0
    flash.clear()
    bcool.clear()
    del parts[:]
    serve()
    banner("HOLD A", 60)


def add_score(n):
    global score, balls_left, next_extra
    score += n * mult
    if score >= next_extra:
        next_extra += 25000
        if balls_left < 5:
            balls_left += 1
            banner("EXTRA BALL!", 40)
        else:
            score += 1000
        beep(1300, 150)


def hit_seg(b, ax, ay, bx, by, rad, e, kick):
    abx = bx - ax
    aby = by - ay
    t = ((b[0] - ax) * abx + (b[1] - ay) * aby) / (abx * abx + aby * aby)
    if t < 0:
        t = 0.0
    elif t > 1:
        t = 1.0
    cx = ax + abx * t
    cy = ay + aby * t
    dx = b[0] - cx
    dy = b[1] - cy
    d2 = dx * dx + dy * dy
    if d2 >= rad * rad:
        return 0.0
    d = sqrt(d2)
    if d < 1e-4:
        l = sqrt(abx * abx + aby * aby)
        nx = -aby / l
        ny = abx / l
    else:
        nx = dx / d
        ny = dy / d
    b[0] = cx + nx * rad
    b[1] = cy + ny * rad
    vn = b[2] * nx + b[3] * ny
    if vn < 0:
        b[2] -= (1 + e) * vn * nx
        b[3] -= (1 + e) * vn * ny
        if kick and -vn > 0.5:
            b[2] += nx * kick
            b[3] += ny * kick
        return -vn
    return 0.01


def hit_flip(b, i, ang, om):
    px, py = PIV[i]
    ex = px + cos(ang) * FL
    ey = py + sin(ang) * FL
    abx = ex - px
    aby = ey - py
    t = ((b[0] - px) * abx + (b[1] - py) * aby) / (FL * FL)
    if t < 0:
        t = 0.0
    elif t > 1:
        t = 1.0
    cx = px + abx * t
    cy = py + aby * t
    dx = b[0] - cx
    dy = b[1] - cy
    rad = R + 1.1
    d2 = dx * dx + dy * dy
    if d2 >= rad * rad:
        return 0.0
    d = sqrt(d2)
    if d < 1e-4:
        nx = -aby / FL
        ny = abx / FL
        if ny > 0:
            nx = -nx
            ny = -ny
    else:
        nx = dx / d
        ny = dy / d
        if abs(nx) < 0.08 and ny < 0:
            nx += 0.1 if i == 0 else -0.1
            l2 = sqrt(nx * nx + ny * ny)
            nx /= l2
            ny /= l2
    b[0] = cx + nx * rad
    b[1] = cy + ny * rad
    vfu = -om * (cy - py)
    vfv = om * (cx - px)
    vn = (b[2] - vfu) * nx + (b[3] - vfv) * ny
    if vn < 0:
        b[2] -= (1 + 0.4) * vn * nx
        b[3] -= (1 + 0.4) * vn * ny
        return -vn
    return 0.01


def physics(left, right):
    global score, tflash, bump_hits, tg, mult, layout, tilt, idle_t
    idle_t += 1
    gx = G + min(0.12, max(0, idle_t - 600) * 0.0004)
    old = (fa[0], fa[1])
    pr = (left, right)
    for i in range(2):
        if fcool[i] > 0:
            fcool[i] -= 1
        if pr[i]:
            if fh[i] == 0 and fcool[i] > 0:
                continue
            fh[i] += 1
        else:
            if fh[i] > 0:
                fcool[i] = 7
            fh[i] = 0
    want = (ACT[0] if left and not tilt and fh[0] < 100 else REST[0],
            ACT[1] if right and not tilt and fh[1] < 100 else REST[1])
    for i in range(2):
        d = want[i] - fa[i]
        sp = 0.32 if abs(want[i] - ACT[i]) < 0.01 else 0.2
        if abs(d) <= sp:
            fa[i] = want[i]
        else:
            fa[i] += sp if d > 0 else -sp
    n = 4
    oms = ((fa[0] - old[0]) / n, (fa[1] - old[1]) / n)
    bums = LAYOUTS[layout]
    for s in range(n):
        a0 = old[0] + (fa[0] - old[0]) * (s + 1) / n
        a1 = old[1] + (fa[1] - old[1]) * (s + 1) / n
        for b in balls:
            b[3] += gx / n
            b[0] += b[2] / n
            b[1] += b[3] / n
            for w in WALLS:
                if w[6] and b[3] < -0.6:
                    continue
                lo = min(w[0], w[2]) - 2.6
                hi_ = max(w[0], w[2]) + 2.6
                if lo < b[0] < hi_:
                    lo = min(w[1], w[3]) - 2.6
                    hi_ = max(w[1], w[3]) + 2.6
                    if lo < b[1] < hi_:
                        v = hit_seg(b, w[0], w[1], w[2], w[3], R, w[4], w[5])
                        if v > 0.5:
                            if w[5]:
                                add_score(5)
                                beep(500, 15)
                            elif v > 1.5:
                                beep(200, 10)
            if b[1] > 38:
                hit_flip(b, 0, a0, oms[0] * n)
                hit_flip(b, 1, a1, oms[1] * n)
            for k in range(len(bums)):
                bu = bums[k]
                dx = b[0] - bu[0]
                dy = b[1] - bu[1]
                rr = R + bu[2]
                if dx * dx + dy * dy < rr * rr:
                    d = sqrt(dx * dx + dy * dy)
                    if d < 1e-4:
                        dx = 1.0
                        d = 1.0
                    nx = dx / d
                    ny = dy / d
                    b[0] = bu[0] + nx * rr
                    b[1] = bu[1] + ny * rr
                    vn = b[2] * nx + b[3] * ny
                    if vn < 0:
                        b[2] -= 1.3 * vn * nx
                        b[3] -= 1.3 * vn * ny
                    if bcool.get(k, 0) <= 0:
                        vo = b[2] * nx + b[3] * ny
                        if vo < 1.45:
                            b[2] += nx * (1.45 - vo)
                            b[3] += ny * (1.45 - vo)
                        flash[k] = 6
                        bcool[k] = 5
                        idle_t = 0
                        add_score(10)
                        bump_hits += 1
                        beep(700 + (k % 3) * 120, 20)
            for k in range(3):
                if tg[k]:
                    dx = b[0] - TARGETS[k][0]
                    dy = b[1] - TARGETS[k][1]
                    rr = R + 1.7
                    if dx * dx + dy * dy < rr * rr:
                        d = sqrt(dx * dx + dy * dy)
                        if d < 1e-4:
                            dx = 1.0
                            d = 1.0
                        nx = dx / d
                        ny = dy / d
                        b[0] = TARGETS[k][0] + nx * rr
                        b[1] = TARGETS[k][1] + ny * rr
                        vn = b[2] * nx + b[3] * ny
                        if vn < 0:
                            b[2] -= 1.7 * vn * nx
                            b[3] -= 1.7 * vn * ny
                        tg[k] = False
                        idle_t = 0
                        add_score(100)
                        beep(1200, 40)
                        if not (tg[0] or tg[1] or tg[2]):
                            tg = [True, True, True]
                            mult += 1
                            if mult > 5:
                                mult = 1
                                layout = (layout + 1) % 3
                                add_score(1000)
                                banner("NEW TABLE!", 50)
                                beep(1500, 200)
                            else:
                                banner("BONUS x" + str(mult), 40)
                                beep(1400, 150)
            b[2] *= 0.9993
            b[3] *= 0.9993
            sp = sqrt(b[2] * b[2] + b[3] * b[3])
            if sp > VMAX:
                b[2] *= VMAX / sp
                b[3] *= VMAX / sp
    for b in balls:
        if b[2] * b[2] + b[3] * b[3] < 0.004:
            b[4] += 1
            if b[4] > 150:
                b[4] = 0
                b[2] += random.uniform(-0.9, 0.9)
                b[3] -= 0.9
                beep(200, 20)
        else:
            b[4] = 0
    for k in list(flash.keys()):
        flash[k] -= 1
        if flash[k] <= 0:
            del flash[k]
    for k in list(bcool.keys()):
        bcool[k] -= 1
        if bcool[k] <= 0:
            del bcool[k]


def lose_ball():
    global balls_left, mode, state, over_t, hi, new_hi, save_t, saved
    if save_t > 0 and not saved:
        saved = True
        serve()
        banner("BALL SAVED!", 45)
        beep(900, 100)
        return
    balls_left -= 1
    beep(120, 300)
    if balls_left <= 0:
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
    else:
        serve()
        saved = False
        banner("BALL " + str(4 - balls_left) if balls_left <= 3 else "NEXT BALL", 35)


def update(L, Rt, ah, ae, up_edge):
    global mode, charge, save_t, nudges, nudge_t, tilt, bump_hits, banner_t, saved
    if mode == 0:
        if ah:
            charge = min(1.0, charge + 0.025)
        elif charge > 0.05:
            b = balls[0]
            b[3] = -(2.85 + 2.15 * charge)
            b[2] = 0.0
            mode = 1
            save_t = 330
            saved = False
            beep(300 + int(charge * 600), 80)
            charge = 0.0
        else:
            charge = 0.0
        if mode == 0:
            return
    if save_t > 0:
        save_t -= 1
    if nudge_t > 0:
        nudge_t -= 1
    else:
        nudges = 0
    if up_edge and not tilt:
        nudges += 1
        nudge_t = 120
        for b in balls:
            b[3] -= 0.55
            b[2] += random.uniform(-0.3, 0.3)
        beep(150, 30)
        if nudges > 3:
            tilt = True
            banner("TILT!", 60)
            beep(100, 300)
    physics(L, Rt)
    # multiball
    if bump_hits >= 30 and len(balls) < 3:
        bump_hits = 0
        for i in range(2):
            balls.append([15.0 + i * 3, 8.0, random.uniform(-0.6, 0.6), 0.8, 0])
        banner("MULTIBALL!", 45)
        beep(1500, 200)
    for b in balls[:]:
        if b[1] > HT + 3:
            balls.remove(b)
    if len(balls) > 1:
        for b in balls:
            if b[0] > 30.0 and b[1] > 64 and b[2] * b[2] + b[3] * b[3] < 0.12:
                b[2] = 0.0
                b[3] = -(4.2 + random.random() * 0.8)
                beep(500, 40)
    if not balls:
        lose_ball()
    elif len(balls) == 1 and mode == 1:
        b = balls[0]
        if b[0] > 30.0 and b[1] > 64 and abs(b[3]) < 0.35:
            mode = 0
            charge = 0.0
            b[2] = 0.0
            b[3] = 0.0
            b[0] = LANE
            b[1] = 66.2


def draw_table():
    for w in WALLS:
        x1, y1 = S(w[0], w[1])
        x2, y2 = S(w[2], w[3])
        ln(x1, y1, x2, y2)
        if w[5]:
            ln(x1, y1 + (1 if y1 < 20 else -1), x2, y2 + (1 if y1 < 20 else -1))
    for k in range(len(LAYOUTS[layout])):
        bu = LAYOUTS[layout][k]
        x, y = S(bu[0], bu[1])
        r = bu[2]
        if k in flash:
            fr(x - r, y - r, 2 * r + 1, 2 * r + 1)
        else:
            for a in range(10):
                pix(x + cos(a * 0.628) * r, y + sin(a * 0.628) * r)
            pix(x, y)
    for k in range(3):
        x, y = S(TARGETS[k][0], TARGETS[k][1])
        if tg[k]:
            fr(x - 1, y - 1, 3, 3)
        else:
            pix(x, y)
    for i in range(2):
        px, py = PIV[i]
        ang = fa[i]
        x1, y1 = S(px, py)
        x2, y2 = S(px + cos(ang) * FL, py + sin(ang) * FL)
        ln(x1, y1, x2, y2)
        ln(x1, y1 + 1, x2, y2 + 1)
        ln(x1, y1 - 1, x2, y2 - 1)
    if mode == 0:
        x, y = S(LANE, 68.0 + charge * 4)
        fr(x - 1, y - 1, 1, 3)
        pix(x - 2, y)
        pix(x - 3, y)


def draw_play():
    D.fill(0)
    draw_table()
    for b in balls:
        x, y = S(b[0], b[1])
        pix(x, y)
        pix(x - 1, y)
        pix(x + 1, y)
        pix(x, y - 1)
        pix(x, y + 1)
    tiny(str(score), 1, 0)
    for i in range(min(balls_left, 5)):
        fr(40 + i * 4, 1, 2, 2)
    tiny("x" + str(mult), 62, 0)
    if tilt and frame % 8 < 4:
        D.drawText("TILT", 24, 17, 1)
    if banner_t > 0:
        bw = 6 * len(banner_s) + 4
        fr((W - bw) // 2, 16, bw, 9, 0)
        D.drawRectangle((W - bw) // 2, 16, bw, 9, 1)
        D.drawText(banner_s, (W - 6 * len(banner_s)) // 2, 17, 1)


def autoflip():
    L = Rt = False
    for b in balls:
        if b[1] > 50 and b[3] > -0.5:
            if b[0] < 15.5 and b[1] > 52:
                L = True
            if b[0] > 14.5 and b[1] > 52:
                Rt = True
    return L, Rt


def title():
    global frame, mode, charge, balls_left, banner_t
    frame += 1
    if not balls:
        serve()
        mode = 1
        balls[0][3] = -4.6
        balls[0][2] = random.uniform(-0.2, 0.2)
    L, Rt = autoflip()
    physics(L, Rt)
    for b in balls[:]:
        if b[1] > HT + 3:
            balls.remove(b)
        elif len(balls) == 1 and b[0] > 30.0 and b[1] > 64 and abs(b[3]) < 0.35:
            balls.remove(b)
    D.fill(0)
    draw_table()
    for b in balls:
        x, y = S(b[0], b[1])
        pix(x, y)
        pix(x - 1, y)
        pix(x + 1, y)
        pix(x, y - 1)
        pix(x, y + 1)
    fr(6, 12, 60, 17, 0)
    D.drawRectangle(6, 12, 60, 17, 1)
    D.drawText("PIN BLAST", 8, 14, 1)
    D.drawText("PIN BLAST", 9, 14, 1)
    ph = (frame // 40) % 4
    s = ("A:START", "BEST " + str(hi), "A:LAUNCH", "D:SND ON" if snd else "D:SND OFF")[ph]
    D.drawText(s, (W - 6 * len(s)) // 2, 21, 1)


def gameover():
    global frame
    frame += 1
    fr(6, 5, 60, 30, 0)
    D.drawRectangle(6, 5, 60, 30, 1)
    D.drawText("GAME OVER", 9, 8, 1)
    s = "SCORE " + str(score)
    D.drawText(s[:10], (W - 6 * len(s[:10])) // 2, 17, 1)
    s = "NEW BEST!" if (new_hi and frame % 20 < 12) else "BEST " + str(hi)
    D.drawText(s[:10], (W - 6 * len(s[:10])) // 2, 26, 1)


ap = bp = dp = up = False
serve()
while True:
    a = thumby.buttonA.pressed()
    b = thumby.buttonB.pressed()
    dn = thumby.buttonD.pressed()
    u = thumby.buttonU.pressed()
    l = thumby.buttonL.pressed()
    r_ = thumby.buttonR.pressed()
    ae = a and not ap
    be = b and not bp
    if state == 0:
        title()
        if dn and not dp:
            snd = not snd
            beep(800, 40)
        if ae:
            new_game()
            beep(900, 60)
    elif state == 1:
        frame += 1
        if banner_t > 0:
            banner_t -= 1
        rt = b or r_ or (a and mode == 1)
        update(l, rt, a and mode == 0, ae, u and not up)
        draw_play()
    else:
        over_t += 1
        gameover()
        if over_t > 25:
            if ae:
                new_game()
            elif be:
                state = 0
                del balls[:]
    ap = a
    bp = b
    dp = dn
    up = u
    D.update()
