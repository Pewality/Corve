# ThumbyUtil - pocket toolbox for the Thumby. Install: /Games/ThumbyUtil/ThumbyUtil.py
# Sys info, Files (read-only), Button test, Stopwatch, Countdown, Tally, Dice,
# Reaction, Pixel ruler (px + mm), Critters (AI sim), Brightness, Reboot
import gc, os, time, machine, random
import thumby as t

d = t.display
d.setFPS(30)
T = d.drawText
A, B = t.buttonA, t.buttonB
Y = (9, 17, 25, 33)  # body text rows under the 8px header
PX, PY = 0.128, 0.13  # mm per pixel (0.42" 72x40 OLED datasheet pitch; edit to calibrate)


class R:  # button with auto-repeat
    def __init__(s, b):
        s.b = b
        s.n = 0

    def __call__(s):
        if s.b.pressed():
            s.n += 1
            return s.n == 1 or (s.n > 10 and s.n % 3 == 0)
        s.n = 0
        return False


Up, Dn, Lf, Rt = R(t.buttonU), R(t.buttonD), R(t.buttonL), R(t.buttonR)


def fmt(n):
    return "%.1fM" % (n / 1048576) if n >= 1048576 else "%dK" % (n >> 10) if n >= 1024 else "%dB" % n


def hdr(s, ar=0):
    d.fill(0)
    d.drawFilledRectangle(0, 0, 72, 8, 1)
    T(s, (72 - 6 * len(s)) // 2, 0, 0)
    if ar:
        T("<", 1, 0, 0)
        T(">", 65, 0, 0)


def lst(title, rows, sel, top, hl=1):  # scrolling list, returns new top
    top = sel if sel < top else sel - 3 if sel > top + 3 else top
    hdr(title[:12])
    n = len(rows)
    for i in range(min(4, n - top)):
        if hl and top + i == sel:
            d.drawFilledRectangle(0, Y[i] - 1, 69, 9, 1)
        T(rows[top + i][:11], 2 if hl else 0, Y[i], 0 if hl and top + i == sel else 1)
    if n > 4:
        h = max(3, 128 // n)
        d.drawFilledRectangle(70, 8 + (32 - h) * top // (n - 4), 2, h, 1)
    return top


def beep(f, ms):
    try:
        t.audio.play(f, ms)
    except Exception:
        pass


def sysinfo():
    p = 0
    m = ""
    while not B.justPressed():
        p = (p + Rt() - Lf()) % 3
        f, u = gc.mem_free(), gc.mem_alloc()
        if p == 0 and A.justPressed():
            gc.collect()
            m = " +" + fmt(max(0, gc.mem_free() - f))
        if p == 0:
            r, h = (("Free", fmt(f)), ("Used", fmt(u)), ("Total", fmt(f + u))), "A:GC" + m
        elif p == 1:
            s = os.statvfs("/")
            n, fr = s[0] * s[2], s[0] * s[3]
            r, h = (("Total", fmt(n)), ("Used", fmt(n - fr)), ("Free", fmt(fr))), "%d%% used" % (100 * (n - fr) // n)
        else:
            v = machine.ADC(4).read_u16() * 3.3 / 65535
            s = time.ticks_ms() // 1000
            r, h = (("CPU", "%dMHz" % (machine.freq() // 1000000)),
                    ("Temp", "%.1fC" % (27 - (v - 0.706) / 0.001721)),
                    ("Up", "%d:%02d:%02d" % (s // 3600, s // 60 % 60, s % 60))), ""
        hdr(("RAM", "FLASH", "SYSTEM")[p], 1)
        for i, (k, v) in enumerate(r):
            T("%-5s%7s" % (k, v), 0, Y[i], 1)
        T(h, 0, Y[3], 1)
        d.update()


def ls(p):
    e = [(x[0], x[1] == 0x4000, x[3] if len(x) > 3 else 0) for x in os.ilistdir(p)]
    e.sort(key=lambda x: (not x[1], x[0].lower()))
    return e


def view(path, name, size):  # read-only text viewer (first 2 KB)
    with open(path, "rb") as f:
        raw = f.read(2048)
    s = "".join(chr(b) if 31 < b < 127 else "\n" if b == 10 else " " if b == 9 else "" if b == 13 else "." for b in raw)
    rows = []
    for ln in s.split("\n"):
        rows += [ln[i:i + 11] for i in range(0, len(ln), 11)] or [""]
    rows.append("[%s]" % fmt(size) + (" cut" if size > 2048 else ""))
    top = 0
    while not (B.justPressed() or Lf()):
        top = max(0, min(len(rows) - 4, top + Dn() - Up()))
        lst(name[:12], rows, top, top, 0)
        d.update()


def files():
    p = "/"
    e = ls(p)
    s = top = 0
    while True:
        up = p != "/"
        rows = ([".."] if up else []) + [n + "/" if k else n for n, k, _ in e] or ["(empty)"]
        s = min(s, len(rows) - 1)
        top = lst(p.split("/")[-1] or "/", rows, s, top)
        d.update()
        s = (s + Dn() - Up()) % len(rows)
        back = B.justPressed() or Lf()
        if A.justPressed() or Rt():
            i = s - up
            if up and s == 0:
                back = 1
            elif 0 <= i < len(e):
                n, k, z = e[i]
                if k:
                    p = ("" if p == "/" else p) + "/" + n
                    e = ls(p)
                    s = top = 0
                else:
                    view(("" if p == "/" else p) + "/" + n, n, z)
        if back:
            if p == "/":
                return
            p = p[:p.rfind("/")] or "/"
            e = ls(p)
            s = top = 0


def btns():  # hold A+B to exit
    bx = (("U", t.buttonU, 14, 10), ("D", t.buttonD, 14, 28), ("L", t.buttonL, 5, 19),
          ("R", t.buttonR, 23, 19), ("B", B, 44, 24), ("A", A, 58, 16))
    n = 0
    while n < 30:
        d.fill(0)
        for c, b, x, y in bx:
            p = b.pressed()
            (d.drawFilledRectangle if p else d.drawRectangle)(x, y, 9, 9, 1)
            T(c, x + 2, y + 1, 1 - p)
        n = n + 1 if A.pressed() and B.pressed() else 0
        d.drawFilledRectangle(0, 38, 72 * n // 30, 2, 1)
        T("hold A+B", 12, 0, 1)
        d.update()


def tm(ms):
    return "%02d:%02d.%02d" % (ms // 60000, ms // 1000 % 60, ms // 10 % 100)


def stopw():
    run = base = st = 0
    laps = []
    while not B.justPressed():
        now = time.ticks_ms()
        el = base + (time.ticks_diff(now, st) if run else 0)
        if A.justPressed():
            base, st, run = (el, st, 0) if run else (base, now, 1)
        if Up() and run:
            laps.append(el)
        if Rt() and not run:
            base, laps = 0, []
        hdr("STOPWATCH")
        T(tm(el), 12, Y[0], 1)
        for k in (2, 1):
            if len(laps) >= k:
                T("L%d %s" % (len(laps) - k + 1, tm(laps[-k])), 3, Y[3 - k], 1)
        T("A:stop U:lap" if run else "A:go R:clear", 0, Y[3], 1)
        d.update()


def countdn():  # U/D +-10s, L/R +-1min, A start/pause
    pre = rem = 60000
    run = ring = end = last = 0
    while not B.justPressed():
        now = time.ticks_ms()
        if run:
            rem = time.ticks_diff(end, now)
            if rem <= 0:
                rem, run, ring = 0, 0, 1
        a = A.justPressed()
        if not (run or ring):
            o = rem
            rem = max(0, min(5999000, rem + 10000 * (Up() - Dn()) + 60000 * (Rt() - Lf())))
            pre = rem if rem != o else pre
        if a:
            if ring:
                ring, rem = 0, pre
            elif run:
                run = 0
            elif rem:
                run, end = 1, time.ticks_add(now, rem)
        if ring:
            k = now // 300
            if k != last and k & 1:
                beep(1000, 150)
            last = k
            c = 1 - (k & 1)
            d.fill(k & 1)
            T("TIME UP!", 12, 12, c)
            T("A:again", 0, 26, c)
            T("B:exit", 0, 33, c)
        else:
            s = (rem + 999) // 1000
            hdr("COUNTDOWN")
            T("%02d:%02d" % (s // 60, s % 60), 21, 14, 1)
            if run:
                d.drawRectangle(0, 25, 72, 4, 1)
                d.drawFilledRectangle(0, 25, 72 * rem // pre, 4, 1)
            T("A:pause" if run else "A:go U/D/L/R", 0, Y[3], 1)
        d.update()


def tally():  # A/U +1, D -1, hold L to reset
    n = z = 0
    while not B.justPressed():
        n = max(0, min(99999, n + ((A.justPressed() or Up()) - Dn())))
        z = z + 1 if t.buttonL.pressed() else 0
        n = 0 if z > 30 else n
        s = str(n)
        hdr("TALLY")
        T(s, (72 - 6 * len(s)) // 2, 13, 1)
        d.drawFilledRectangle(0, 22, 72 * min(z, 30) // 30, 2, 1)
        T("A/U:+1 D:-1", 0, Y[2], 1)
        T("L hold:reset", 0, Y[3], 1)
        d.update()


def dice():  # L/R die, U/D count, A roll
    sd = (4, 6, 8, 10, 12, 20, 100)
    i = q = 1
    x = []
    while not B.justPressed():
        i = (i + Rt() - Lf()) % 7
        q = max(1, min(3, q + Up() - Dn()))
        if A.justPressed():
            random.seed(time.ticks_us())
            x = [random.randint(1, sd[i]) for _ in range(q)]
        hdr("DICE A:ROLL")
        T("L/R: d%d" % sd[i], 0, Y[0], 1)
        T("U/D: x%d" % q, 0, Y[1], 1)
        T(" ".join(map(str, x)), 0, Y[2], 1)
        if len(x) > 1:
            T("= %d" % sum(x), 0, Y[3], 1)
        d.update()


def react():  # A to start, then press A the moment the screen flashes
    s = best = 0  # 0 idle, 1 waiting, 2 go
    msg = "Press A"
    while not B.justPressed():
        now = time.ticks_ms()
        if s == 1 and time.ticks_diff(now, t0) >= wait:
            s, t0, msg = 2, now, "GO!"
            beep(1500, 80)
        if A.justPressed():
            if s == 0:
                random.seed(now)
                wait, t0, s, msg = random.randint(1000, 4000), now, 1, "Wait..."
            elif s == 1:
                s, msg = 0, "Too soon!"
            else:
                ms = time.ticks_diff(now, t0)
                best = min(best, ms) if best else ms
                s, msg = 0, "%d ms" % ms
        c = 1 - (s >> 1)  # white screen + black text during GO
        d.fill(s >> 1)
        T("REACTION", 12, 0, c)
        T(msg, 36 - 3 * len(msg), 14, c)
        T("A:go B:exit", 0, 25, c)
        if best:
            T("Best %d ms" % best, 0, 33, c)
        d.update()


def ruler():
    # Two crosshairs; D-pad moves the big one, A switches which one is active.
    # Distances are centre-to-centre: pixels * pitch (PX wide, PY tall).
    # Tick marks along the top/left edges are real 1 mm steps (5 mm = long tick).
    P = [[8, 10], [48, 28]]
    k = 0
    while not B.justPressed():
        k ^= A.justPressed()
        p = P[k]
        p[0] = max(0, min(71, p[0] + Rt() - Lf()))
        p[1] = max(0, min(39, p[1] + Dn() - Up()))
        (x1, y1), (x2, y2) = P
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        d.fill(0)
        for i in range(10):
            x, y = int(i / PX), int(i / PY)
            d.drawLine(x, 0, x, 4 if i % 5 == 0 else 2, 1)
            if y < 40:
                d.drawLine(0, y, 4 if i % 5 == 0 else 2, y, 1)
        oy = 0 if y1 + y2 > 40 else 23  # keep the readout away from the points
        d.drawFilledRectangle(0, oy, 72, 17, 0)
        T("dx%d dy%d" % (dx, dy), 0, oy + 1, 1)
        T("%.0fpx %.2fmm" % ((dx * dx + dy * dy) ** .5, ((dx * PX) ** 2 + (dy * PY) ** 2) ** .5), 0, oy + 9, 1)
        d.drawLine(x1, y1, x2, y2, 1)
        for i, (x, y) in enumerate(P):
            r = 3 if i == k else 1
            d.drawLine(max(0, x - r), y, min(71, x + r), y, 1)
            d.drawLine(x, max(0, y - r), x, min(39, y + r), 1)
        d.update()


def critters():
    # Tiny AI sim. Critters (2px) flee the predator (box), else chase the nearest food
    # they can see, else wander. Fed critters split, starving ones die and the predator
    # hunts then rests (filled box). D-pad moves the cursor, A drops food, B exits.
    rnd = random.random
    cl = lambda v, hi: max(0, min(hi, v))
    d2 = lambda a, b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2  # squared distance

    def aim(a, b, sp):  # velocity of speed sp pointing from a towards b
        dx, dy = b[0] - a[0], b[1] - a[1]
        k = sp / ((dx * dx + dy * dy) ** .5 or 1)
        return dx * k, dy * k

    def rv(sp):  # random direction
        return aim((0, 0), (rnd() - .5, rnd() - .5), sp)

    random.seed(time.ticks_us())
    C = [[rnd() * 70, rnd() * 38, 0, 0, 10] for _ in range(6)]  # x, y, vx, vy, energy
    F = []  # food pellets [x, y]
    P = [60.0, 30.0, 0, 0]  # predator x, y, vx, vy
    cx, cy, f, rest = 36, 20, 0, 0
    while not B.justPressed():
        f += 1
        cx, cy = cl(cx + Rt() - Lf(), 71), cl(cy + Dn() - Up(), 39)
        if A.justPressed():
            F += [[cl(cx + random.randint(-3, 3), 71), cl(cy + random.randint(-3, 3), 39)] for _ in range(3)]
        if f % 15 == 0 and len(F) < 14:
            F.append([random.randint(1, 70), random.randint(1, 38)])
        if len(C) < 2:  # migrants arrive so the world is never empty
            C.append([rnd() * 70, 0, 0, 0, 10])
        for c in C[:]:
            fd = min(F, key=lambda q: d2(q, c)) if F else 0
            if d2(P, c) < 150:  # predator close -> run away
                c[2], c[3] = aim(P, c, .9)
            elif fd and d2(fd, c) < 600:  # food in sight -> go eat it
                c[2], c[3] = aim(c, fd, .6)
                if d2(fd, c) < 4:
                    F.remove(fd)
                    c[4] += 8
            elif rnd() < .05:  # nothing to do -> wander
                c[2], c[3] = rv(.3)
            for i, hi in ((0, 70), (1, 38)):  # move and bounce off the walls
                c[i] += c[i + 2]
                if not 0 < c[i] < hi:
                    c[i] = cl(c[i], hi)
                    c[i + 2] = -c[i + 2]
            c[4] -= .02  # hunger
            if c[4] > 16 and len(C) < 16:  # well fed -> split in two
                c[4] /= 2
                C.append([c[0], c[1], -c[2], -c[3], c[4]])
            elif c[4] <= 0:
                C.remove(c)
        rest = max(0, rest - 1)
        q = min(C, key=lambda c: d2(P, c)) if C and not rest else 0
        if q and d2(P, q) < 900:  # hunt the nearest critter within ~30px
            P[2], P[3] = aim(P, q, .7)
            if d2(P, q) < 9:
                C.remove(q)
                P[2] = P[3] = 0
                rest = 90  # full belly: rest for 3 s
        elif f % 30 == 0:
            P[2], P[3] = rv(.25)
        for i, hi in ((0, 66), (1, 34)):
            P[i] += P[i + 2]
            if not 0 < P[i] < hi:
                P[i] = cl(P[i], hi)
                P[i + 2] = -P[i + 2]
        d.fill(0)
        for q in F:
            d.setPixel(int(q[0]), int(q[1]), 1)
        for c in C:
            if c[4] > 3 or f & 4:  # starving critters blink
                d.drawFilledRectangle(int(c[0]), int(c[1]), 2, 2, 1)
        (d.drawFilledRectangle if rest else d.drawRectangle)(int(P[0]), int(P[1]), 5, 5, 1)
        if f & 8:  # blinking cursor
            d.drawLine(max(0, cx - 2), cy, min(71, cx + 2), cy, 1)
            d.drawLine(cx, max(0, cy - 2), cx, min(39, cy + 2), 1)
        T("pop%d" % len(C) + (" A:feed" if f < 90 else ""), 0, 33, 1)
        d.update()


def bright():  # L/R adjust, A/B done
    v = 127
    while not (A.justPressed() or B.justPressed()):
        v = max(0, min(127, v + 5 * (Rt() - Lf())))
        d.brightness(v)
        hdr("BRIGHTNESS")
        d.drawRectangle(5, 16, 62, 8, 1)
        d.drawFilledRectangle(6, 17, 60 * v // 127, 6, 1)
        T("%d%%" % (v * 100 // 127), 24, 28, 1)
        d.update()


def reboot():  # hold A ~1.5 s to confirm
    n = ok = 0
    while not B.justPressed():
        p = A.pressed()
        ok = ok or not p
        n = n + 1 if p and ok else 0
        if n > 44:
            machine.reset()
        hdr("REBOOT?")
        T("Hold A=yes", 0, Y[0], 1)
        d.drawRectangle(0, 25, 72, 6, 1)
        d.drawFilledRectangle(0, 25, 72 * n // 45, 6, 1)
        d.update()


TOOLS = (("Sys info", sysinfo), ("Files", files), ("Button test", btns),
         ("Stopwatch", stopw), ("Countdown", countdn), ("Tally", tally),
         ("Dice", dice), ("Reaction", react), ("Pixel ruler", ruler),
         ("Critters", critters), ("Brightness", bright), ("Reboot", reboot))


def main():
    names = [x[0] for x in TOOLS]
    s = top = 0
    while True:
        top = lst("THUMBY UTIL", names, s, top)
        d.update()
        s = (s + Dn() - Up()) % len(TOOLS)
        if A.justPressed():
            TOOLS[s][1]()
            gc.collect()


main()
