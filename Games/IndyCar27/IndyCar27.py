# IndyCar '27  -  Thumby (MicroPython) racer, 72x40, 30 FPS
#
# CONTROLS (while driving)
#   A = throttle    B = brake    LEFT/RIGHT = steer
#   UP = switch camera (cockpit <-> chase cam), any time
#   DOWN (tap)  = request pit stop (you pit next time you cross the line)
#   DOWN (hold) = pause menu
import thumby
import random
import framebuf
from math import sin, cos, sqrt

D = thumby.display
D.setFPS(30)
dt = 1.0 / 30

bU = thumby.buttonU
bD = thumby.buttonD
bL = thumby.buttonL
bR = thumby.buttonR
bA = thumby.buttonA
bB = thumby.buttonB

# ---------------------------------------------------------------- helpers
snd = True

def rnd(a, b):
    return a + (b - a) * random.random()

def clamp(x, a, b):
    return a if x < a else (b if x > b else x)

def beep(f, ms):
    if snd:
        try:
            thumby.audio.play(int(f), ms)
        except:
            pass

def eng(f):
    """engine note: refreshed every 3 frames"""
    if snd and fr % 3 == 0:
        try:
            thumby.audio.play(int(f), 110)
        except:
            pass

def tx(s, x, y, c=1):
    D.drawText(s, int(x), int(y), c)

def ctx(s, y, c=1):
    D.drawText(s, (73 - len(s) * 6) // 2, int(y), c)

def rc(x, y, w, h, c=1):
    D.drawFilledRectangle(int(x), int(y), int(w), int(h), c)

def ln(x0, y0, x1, y1, c=1):
    D.drawLine(int(x0), int(y0), int(x1), int(y1), c)

def rows(items, sel, y0=0, n=5, scroll=None):
    st = scroll if scroll is not None else (sel - n + 1 if sel >= n else 0)
    for i in range(n):
        j = st + i
        if j < 0 or j >= len(items):
            continue
        y = y0 + i * 8
        s = items[j][:12]
        if j == sel:
            rc(0, y, 72, 8, 1)
            tx(s, 1, y + 1, 0)
        else:
            tx(s, 1, y + 1, 1)

# ---------------------------------------------------------------- tracks
# (name, length label, speed factor, oval?, season laps, scenery theme, segments)
# segments = (length, curve)   curve > 0 = right,  < 0 = left
# Layouts follow the track maps (turn order / direction / straights).
TRACKS = (
    ("INDY ROAD", "2.44 MI", 1.0, 0, 6, 0,
     ((315, 0), (40, 1.6), (50, 0), (50, -1.0), (60, 1.0), (30, 0), (80, .8),
      (80, 0), (20, -.9), (20, .9), (400, 0), (40, -1.6), (75, 0), (40, 1.5),
      (35, 0), (40, -1.5), (80, 0), (40, 1.5), (90, 0), (140, .6), (100, 0),
      (40, 1.5), (45, 0), (60, -.9), (50, 0), (120, .7), (245, 0))),
    ("INDY 500", "2.50 MI", 1.35, 1, 10, 0,
     ((220, 0), (250, -.55), (190, 0), (250, -.55), (560, 0), (250, -.55),
      (190, 0), (250, -.55), (340, 0))),
    ("PORTLAND", "1.96 MI", 1.0, 0, 6, 1,
     ((210, 0), (40, .7), (40, -.8), (30, -.5), (200, 0), (70, 1.1), (60, .7),
      (20, 0), (70, -1.0), (60, 0), (60, 1.2), (30, 0), (280, 0), (330, .4),
      (40, .7), (30, 0), (70, 1.2), (80, 1.1), (304, 0))),
    ("ROAD AMERICA", "4.05 MI", 1.05, 0, 5, 2,
     ((410, 0), (60, 1.2), (280, 0), (60, 1.0), (250, 0), (150, .35), (290, 0),
      (60, -1.4), (170, 0), (50, -1.2), (130, 0), (50, .9), (245, 0), (45, -1.2),
      (60, .8), (200, .9), (157, 0), (30, .7), (30, -.7), (120, 0), (100, .4),
      (46, 0), (224, .35), (105, 1.0), (161, 0), (60, -.7), (196, 0), (60, 1.3),
      (423, 0))),
    ("LONG BEACH", "1.97 MI", 0.95, 0, 6, 3,
     ((260, 0), (55, 1.8), (100, 0), (55, 1.8), (130, 0), (60, -1.6), (70, 0),
      (60, 1.6), (170, 0), (70, -1.7), (80, 0), (70, -1.7), (90, 0), (110, 1.5),
      (260, 0), (60, -1.8), (100, 0), (60, 1.8), (110, 0))),
    ("MID-OHIO", "2.26 MI", 0.97, 0, 6, 4,
     ((190, 0), (70, -1.3), (60, 1.0), (70, -1.1), (110, 0), (60, 1.4), (90, -.9),
      (160, 0), (80, 1.2), (80, 0), (70, -1.5), (130, 0), (50, 1.5), (50, -1.5),
      (180, 0), (90, 1.1), (140, 0), (80, -1.3), (160, 0), (70, 1.0), (60, 0),
      (100, -1.0), (110, 0))),
    ("MILWAUKEE", "1.02 MI", 1.22, 1, 25, 5,
     ((75, 0), (280, -.7), (230, 0), (280, -.7), (170, 0))),
)
NTR = len(TRACKS)

BASE = 70.0
K = 240.0
PAN = 216
PANW = PAN + 72
HOR = 18
NR1 = 12          # road rows, cockpit view
NR3 = 19          # road rows, chase view
CB = 12.0         # chase camera distance behind the car
SPC = 28          # trackside object spacing
PITLIM = 30.0     # pit lane speed limit
ZN = 260          # pit lane starts this far before the line
ZX = 200          # ...and ends this far after it
NAMES = ("YOU", "ACE", "BLZ", "CRX", "DRT", "EVO", "FLY", "GTR", "HAW")
SK = (1.0, 0.99, 0.98, 0.97, 0.96, 0.95, 0.94, 0.93)
PTS = (25, 20, 16, 13, 10, 8, 6, 4, 2)
FUEL = (20, 40, 60, 80, 100)
SIDE = ((3, 2, 0), (1, 1, 0), (0, 1, 0), (5, 4, 5), (0, 0, 1), (3, 2, 4))

TR = TRACKS[0]
TL = 2000.0
tf = 1.0
ends2 = []
cv2 = []
prof = []
hd = [0.0, 0.0]
nprof = 1
ai0 = 40.0
PB = bytearray(PANW * 2)
PF = framebuf.FrameBuffer(PB, PANW, 16, framebuf.MONO_VLSB)

# ---------------------------------------------------------------- scenery panorama
_rs = [1]

def pr(a, b):
    _rs[0] = (_rs[0] * 1103515245 + 12345) & 0x3fffffff
    return a + (_rs[0] >> 8) % (b - a + 1)

def wrap3(fn, x, *a):
    for o in (-PAN, 0, PAN):
        fn(x + o, *a)

def f_sun(x):
    PF.fill_rect(x - 1, 5, 4, 4, 1)
    PF.fill_rect(x - 2, 6, 6, 2, 1)

def f_cloud(x, y):
    PF.hline(x, y, 8, 1)
    PF.hline(x + 2, y - 1, 4, 1)

def f_stand(x, w, h):
    PF.hline(x, 14 - h, w, 1)
    for r in range(0, h, 2):
        PF.hline(x, 15 - h + r, w, 1)
        for xx in range(x + (r & 2) // 2, x + w, 2):
            PF.pixel(xx, 16 - h + r, 1)
    PF.vline(x, 14 - h, h + 1, 1)
    PF.vline(x + w - 1, 14 - h, h + 1, 1)

def f_pagoda(x):
    PF.fill_rect(x, 12, 9, 3, 1)
    PF.fill_rect(x + 1, 9, 7, 3, 1)
    PF.fill_rect(x + 2, 6, 5, 3, 1)
    PF.vline(x + 4, 4, 2, 1)
    PF.pixel(x + 4, 13, 0)
    PF.pixel(x + 3, 10, 0)
    PF.pixel(x + 5, 10, 0)

def f_pylon(x):
    PF.fill_rect(x, 4, 3, 11, 1)
    for y in (6, 8, 10, 12):
        PF.pixel(x + 1, y, 0)

def f_tower(x):
    PF.vline(x + 1, 6, 9, 1)
    PF.fill_rect(x - 1, 5, 4, 2, 1)

def f_pine(x, h):
    for r in range(h):
        w = 1 + int(r * 1.3)
        PF.hline(x - w // 2, 16 - h + r, w, 1)

def f_round(x, w, h):
    PF.fill_rect(x + 1, 15 - h, w - 2, h - 3, 1)
    PF.fill_rect(x, 16 - h, w, h - 5, 1)
    PF.vline(x + w // 2, 12, 3, 1)

def f_sky(x, w, h):
    PF.fill_rect(x, 15 - h, w, h, 1)
    for y in range(16 - h, 14, 2):
        for xx in range(x + 1, x + w - 1, 2):
            PF.pixel(xx, y, 0)
    if h > 8:
        PF.vline(x + w // 2, 15 - h - 2, 2, 1)

def f_palm(x):
    PF.vline(x + 2, 8, 7, 1)
    PF.hline(x, 8, 5, 1)
    PF.pixel(x, 9, 1)
    PF.pixel(x + 4, 9, 1)
    PF.pixel(x + 2, 7, 1)

def f_wheel(x):
    cx = x + 6
    cy = 9
    for dx, dy in ((0, -5), (3, -4), (4, -3), (5, 0), (4, 3), (3, 4), (0, 5),
                   (-3, 4), (-4, 3), (-5, 0), (-4, -3), (-3, -4)):
        PF.pixel(cx + dx, cy + dy, 1)
    PF.line(cx - 5, cy, cx + 5, cy, 1)
    PF.line(cx, cy - 5, cx, cy + 5, 1)
    PF.line(cx - 3, cy - 3, cx + 3, cy + 3, 1)
    PF.line(cx - 3, cy + 3, cx + 3, cy - 3, 1)
    PF.line(cx, cy, cx - 3, 15, 1)
    PF.line(cx, cy, cx + 3, 15, 1)

def f_hood(x):
    PF.line(x + 22, 5, x, 15, 1)
    PF.line(x + 22, 5, x + 44, 15, 1)
    PF.line(x + 15, 9, x + 19, 8, 1)
    PF.line(x + 19, 8, x + 22, 10, 1)
    PF.line(x + 22, 10, x + 26, 8, 1)
    PF.line(x + 26, 8, x + 29, 9, 1)

def f_ship(x):
    PF.fill_rect(x, 12, 28, 3, 1)
    PF.fill_rect(x + 6, 9, 14, 3, 1)
    for k in (8, 12, 16):
        PF.fill_rect(x + k, 6, 2, 3, 1)

def f_barn(x):
    PF.fill_rect(x, 10, 11, 5, 1)
    PF.line(x - 1, 10, x + 5, 6, 1)
    PF.line(x + 11, 10, x + 5, 6, 1)
    PF.fill_rect(x + 4, 12, 3, 3, 0)

def build_pan(th):
    PF.fill(0)
    _rs[0] = 1234 + th * 977
    wrap3(f_sun, pr(20, 190))
    for _ in range(3):
        wrap3(f_cloud, pr(0, PAN - 8), pr(5, 7))
    if th == 2:                          # rolling hills (Road America)
        for xx in range(PANW):
            a = xx * 6.2832 / PAN
            h = 2 + int(1.4 * sin(3 * a) + 1.2 * sin(7 * a + 1) + 1.4)
            PF.vline(xx, 15 - h, h, 1)
    if th == 0:
        wrap3(f_pagoda, 30)
        wrap3(f_pylon, 120)
    elif th == 1:
        wrap3(f_hood, 100)
    elif th == 3:
        wrap3(f_wheel, 60)
        wrap3(f_ship, 150)
    elif th == 4:
        wrap3(f_barn, 90)
    elif th == 5:
        wrap3(f_wheel, 150)
    x = 0
    while x < PAN:
        gap = pr(2, 9)
        if th == 0:
            k = pr(0, 3)
            if k < 2:
                w = pr(26, 38)
                wrap3(f_stand, x, w, pr(5, 7))
            elif k == 2:
                w = 3
                wrap3(f_tower, x)
            else:
                w = 6
                wrap3(f_round, x, 6, pr(5, 7))
        elif th == 1:
            w = pr(6, 8)
            wrap3(f_pine, x + w // 2, pr(6, 11))
        elif th == 2:
            w = pr(6, 8)
            wrap3(f_round, x, w, pr(6, 9))
        elif th == 3:
            if pr(0, 3) == 0:
                w = 5
                wrap3(f_palm, x)
            else:
                w = pr(6, 9)
                wrap3(f_sky, x, w, pr(6, 11))
        elif th == 4:
            w = pr(6, 9)
            wrap3(f_round, x, w, pr(6, 9))
        else:
            if pr(0, 2) == 0:
                w = pr(30, 40)
                wrap3(f_stand, x, w, pr(5, 7))
            elif pr(0, 1) == 0:
                w = 3
                wrap3(f_tower, x)
            else:
                w = pr(8, 12)
                wrap3(f_sky, x, w, pr(4, 7))
        x += w + gap

def load_track(i):
    global TR, TL, tf, ends2, cv2, prof, nprof, ai0, hd
    TR = TRACKS[i]
    tf = TR[2]
    ends = []
    cv = []
    e = 0
    for a, c in TR[6]:
        e += a
        ends.append(e)
        cv.append(c)
    TL = float(e)
    ends2 = ends + [x + e for x in ends]
    cv2 = cv + cv
    nprof = int((e - 1) // 20) + 1
    coef = 0.1 if TR[3] else 0.3
    prof = []
    hd = [0.0]
    acc = 0.0
    k = 0
    for j in range(nprof):
        d = j * 20
        while ends[k] <= d:
            k += 1
        prof.append(1 - coef * min(1.0, abs(cv[k]) / 1.5))
        acc += cv[k] * 20 * 0.6
        hd.append(acc)
    tgt = round(acc / PAN) * PAN
    for j in range(nprof + 1):
        hd[j] += (tgt - acc) * j / nprof
    ai0 = 0.0
    for p in prof:
        ai0 += 20.0 / (BASE * tf * p)
    build_pan(TR[5])

# ---------------------------------------------------------------- state
S = 'title'
fr = 0
msel = 0
tsel = 0
nlap = 5
hsel = 0
mode = ''          # quick / single / season / practice
sess = ''          # prac / qual / race / free
tctx = 'pre'
tune = [3, 3, 1, 3]    # wing, gear, tire, fuel idx
trow = 0
anim = 0
svc_frames = 0
nlaps = 5
qgrid = None
qbest = None
ask = list(SK)
aiq = [60.0] * 8
srd = 0
spts = [0] * 9
res_order = []
rscroll = 0
fin_t = 0
iscroll = 0
fscroll = 0
cam3 = False
msg_t = 0
msg_s = ""
dhold = 0
dfired = False
svis = 0.0
rpm = 0.3
pitmode = False
pbox = 0.0
pit_pen = 0.0
pen_frames = 0
st_pt = 0.0
st_px = 0.0

# car / session
ptotal = 0.0
px = 0.0
v = 0.0
wear = 0.0
fuel = 100.0
dmg = 0.0
pitreq = False
lastidx = 0
lapstart = None
best = None
last = None
sess_t = None
paused = False
pmsel = 0
hit_cd = 0
startseq = False
sfr = 0
lo_delay = 30
tick = 0
pcur = 0.0
g_top = 70.0
g_acc = 26.0
g_grip = 1.0
g_wr = 1.0

# AI cars
nai = 8
at = [0.0] * 8
av = [0.0] * 8
alane = [0.0] * 8
alane0 = [0.0] * 8
aph = [0.0] * 8
alap = [0] * 8
ahold = [0] * 8
astops = []
XO = [0.0] * (NR3 + 2)

def car_params():
    global g_top, g_acc, g_grip, g_wr
    w, g, t, f = tune
    g_top = BASE * tf * (1.05 + 0.03 * (g - 3) - 0.032 * (w - 3))
    g_acc = 26.0 * (1.25 - 0.1 * g)
    g_grip = 0.75 + 0.09 * w + (0.14, 0.06, 0.0)[t]
    g_wr = (1.8, 1.0, 0.5)[t]

car_params()

# ---------------------------------------------------------------- events
def new_event(ti, laps, off=0.0):
    global nlaps, qgrid, qbest, ask, aiq
    load_track(ti)
    car_params()
    nlaps = laps
    qgrid = None
    qbest = None
    ask = [SK[c] * (1 + off) for c in range(8)]
    aiq = [ai0 / ask[c] * rnd(1.0, 1.03) + 1.5 for c in range(8)]

def season_event():
    global S, hsel
    new_event(srd, TRACKS[srd][4])
    hsel = 0
    S = 'hub'

def start_session(kind):
    global sess, tctx, trow, S
    sess = kind
    tctx = 'pre'
    trow = 0
    S = 'tune'

def grid_xy(slot):
    return -((slot // 2) + 1) * 9.0 - (slot % 2) * 4.5, (-0.45 if slot % 2 == 0 else 0.45)

def begin_drive(kind):
    global ptotal, px, v, wear, fuel, dmg, pitreq, lastidx, lapstart, best, last
    global sess_t, paused, hit_cd, startseq, sfr, lo_delay, tick, astops, nai
    ptotal = 0.0
    px = 0.0
    v = 0.0
    wear = 0.0
    fuel = float(FUEL[tune[3]])
    dmg = 0.0
    pitreq = False
    lastidx = 0
    lapstart = None
    best = None
    last = None
    paused = False
    hit_cd = 0
    tick = 0
    startseq = False
    sess_t = 9000 if kind in ('prac', 'qual') else None
    if kind == 'race':
        nai = 8
        gp = (qgrid - 1) if qgrid else 4 + random.randint(0, 4)
        order = sorted(range(8), key=lambda c: -(ask[c] * rnd(0.97, 1.03)))
        slot = 0
        for c in order:
            if slot == gp:
                slot += 1
            at[c], alane0[c] = grid_xy(slot)
            alane[c] = alane0[c]
            av[c] = 0.0
            aph[c] = rnd(0, 6)
            alap[c] = -1
            ahold[c] = 0
            slot += 1
        ptotal, px = grid_xy(gp)
        lastidx = -1
        startseq = True
        sfr = 0
        lo_delay = int(rnd(15, 60))
        if nlaps < 8:
            astops = []
        elif nlaps < 16:
            astops = [nlaps // 2]
        else:
            astops = [nlaps // 3, (2 * nlaps) // 3]
    else:
        nai = 3 if kind == 'qual' else 6
        astops = []
        for c in range(8):
            at[c] = (c + 1) * TL / (nai + 1) + rnd(-30, 30)
            alane0[c] = rnd(-0.6, 0.6)
            alane[c] = alane0[c]
            av[c] = 40.0
            aph[c] = rnd(0, 6)
            alap[c] = int(at[c] // TL)
            ahold[c] = 0

def service():
    global fuel, wear, dmg
    fuel = float(FUEL[tune[3]])
    wear = 0.0
    dmg = 0.0

def to_pit():
    global S, anim, pitreq, lapstart, pit_pen, pbox, ptotal, tctx, v
    spd = v
    pit_pen = 0.0
    if sess != 'race':
        ptotal = float(int(ptotal // TL)) * TL
        v = min(v, PITLIM)
    elif spd > PITLIM + 4:
        pit_pen = 2.0 + (spd - PITLIM) * 0.12
    pitreq = False
    lapstart = None
    pbox = float(int(ptotal // TL)) * TL + 45
    tctx = 'mid'
    anim = 0
    S = 'pitin'

def st_pitin():
    global anim, v, ptotal, px, S, trow, pitmode, svis, rpm
    pitmode = True
    if sess == 'race':
        ai_step()
    anim += 1
    rem = pbox - ptotal
    dpx = clamp(-1.25 - px, -1.6 * dt, 1.6 * dt)
    px += dpx
    vt = min(PITLIM, sqrt(20.0 * max(rem, 0.0)) + 1.5)
    v += clamp(vt - v, -60 * dt, 15 * dt)
    ptotal += v * dt
    svis += (clamp(dpx * 30, -1, 1) - svis) * 0.3
    rpm = 0.3 + 0.4 * v / PITLIM
    eng(70 + rpm * 400)
    draw_view(cam3)
    if not cam3:
        cockpit(svis, int(v * 2.3), rpm, "LIM" if (anim // 5) % 2 == 0 else None)
    band()
    ctx("PIT ENTRY" if anim < 50 else "TO THE BOX", 0)
    if rem <= 0.8 or anim > 260:
        v = 0.0
        pitmode = False
        trow = 0
        S = 'tune'

def finalize_qual():
    global qgrid, qbest
    if best is not None:
        if qbest is None or best < qbest:
            qbest = best
        qgrid = 1 + sum(1 for t in aiq if t < qbest)

def quit_session():
    global S
    if sess == 'qual':
        finalize_qual()
    S = 'menu' if sess == 'free' else 'hub'

def finish_race():
    global res_order, S, fin_t
    items = [(ptotal, 0)] + [(at[c], c + 1) for c in range(8)]
    items.sort(key=lambda t: -t[0])
    res_order = [t[1] for t in items]
    S = 'finish'
    fin_t = 0

def pos_now():
    n = 1
    for c in range(nai):
        if at[c] > ptotal:
            n += 1
    return n

# ---------------------------------------------------------------- AI
def ai_step():
    race = (sess == 'race')
    for c in range(nai):
        tt = at[c]
        idx = int(tt // TL)
        if idx != alap[c]:
            alap[c] = idx
            if idx in astops:
                ahold[c] = int(rnd(6, 9) * 30)
        if ahold[c] > 0:
            ahold[c] -= 1
            tv = 0.0
            tl = 0.95
        else:
            j = int((tt % TL) / 20)
            if j >= nprof:
                j = nprof - 1
            tv = BASE * tf * ask[c] * prof[j]
            if race:
                tv *= 1 - clamp((tt - ptotal) * 0.00015, -0.05, 0.05)
            else:
                tv *= 0.88
            tl = alane0[c] + 0.2 * sin(aph[c] + fr * 0.03)
            gap = (ptotal - tt + TL / 2) % TL - TL / 2
            if 0 < gap < 18 and abs(alane[c] - px) < 0.4:
                tl = clamp(alane[c] + (0.5 if alane[c] >= px else -0.5), -0.8, 0.8)
                if gap < 6 and abs(alane[c] - px) < 0.3:
                    tv = min(tv, max(v, 8.0))
        tl = clamp(tl, -0.95, 0.95)
        alane[c] += clamp(tl - alane[c], -0.9 * dt, 0.9 * dt)
        av[c] += clamp(tv - av[c], -60 * dt, 30 * dt)
        at[c] = tt + av[c] * dt

def collide():
    global v, dmg, px, hit_cd
    if hit_cd > 0:
        return
    for c in range(nai):
        rd = (at[c] - ptotal + TL / 2) % TL - TL / 2
        if -4 < rd < 5 and abs(alane[c] - px) < 0.3:
            if rd > 0:
                v = min(v, av[c] * 0.9)
            dmg = min(100.0, dmg + 2)
            hit_cd = 12
            px += 0.25 if px >= alane[c] else -0.25
            beep(150, 40)
            return

# ---------------------------------------------------------------- sprites
def car_sprite(x, yb, i, lv):
    """IndyCar seen from behind. i = row/scale, lv = livery 0..2"""
    w = int(i * 0.9) + 3
    h = int(i * 0.5) + 2
    x = int(x)
    yb = int(yb)
    x0 = x - w // 2
    wh = 1 + h // 10
    tw = 1 + w // 6
    th = (h * 2) // 3 + 1
    bw = max(1, w // 5)
    bx = x - bw // 2
    # rear wing + end plates
    rc(x0, yb - h, w, wh)
    rc(x0, yb - h, 1, 1 + h // 4)
    rc(x0 + w - 1, yb - h, 1, 1 + h // 4)
    # central body: gearbox / engine cover
    rc(bx, yb - h + wh, bw, h - wh)
    if h >= 7:
        rc(bx - 1, yb - h + wh + h // 4, bw + 2, 1 + h // 8)   # aeroscreen + helmet
    # axles + beam wing
    if w >= 9:
        rc(x0 + tw, yb - th // 2 - 1, w - 2 * tw, 1)
        rc(bx - 1, yb - 1, bw + 2, 1)
    # rear tyres
    rc(x0, yb - th, tw, th)
    rc(x0 + w - tw, yb - th, tw, th)
    if tw >= 3 and th >= 5:
        for yy in range(yb - th + 2, yb - 1, 3):
            rc(x0 + 1, yy, tw - 2, 1, 0)
            rc(x0 + w - tw + 1, yy, tw - 2, 1, 0)
    # livery
    if lv == 1 and bw >= 3 and h >= 8:
        rc(bx + 1, yb - h + wh + 2, bw - 2, h - wh - 3, 0)
    elif lv == 2 and h >= 6:
        rc(x, yb - h + wh + 1, 1, h - wh - 2, 0)
    if h >= 8:
        D.setPixel(x, yb - 1, 0)

def side_obj(kd, x, y, s):
    if kd == 0:       # tree
        rc(x - s, y - 2 * s - 1, 2 * s + 1, s + 1, 0)
        rc(x - s, y - 2 * s, 2 * s + 1, s + 1, 1)
        rc(x, y - s, 1, s, 1)
    elif kd == 1:     # pine
        ln(x, y - 3 * s, x - s, y - s)
        ln(x, y - 3 * s, x + s, y - s)
        ln(x - s, y - s, x + s, y - s)
        ln(x, y - s, x, y)
    elif kd == 2:     # light tower
        ln(x, y - 4 * s, x, y)
        rc(x - s, y - 4 * s, 2 * s + 1, s // 2 + 1)
    elif kd == 3:     # grandstand
        rc(x - 2 * s, y - s - 1, 4 * s + 1, s + 1, 0)
        rc(x - 2 * s, y - s, 4 * s + 1, s, 1)
        rc(x - 2 * s + 1, y - s // 2 - 1, 4 * s - 1, 1, 0)
    elif kd == 4:     # building
        rc(x - s, y - 4 * s, 2 * s + 1, 4 * s, 1)
        rc(x - s + 1, y - 3 * s, 1, 1, 0)
        rc(x + s - 1, y - 2 * s, 1, 1, 0)
    else:             # palm
        ln(x, y - 3 * s, x, y)
        ln(x - s, y - 3 * s + 1, x + s, y - 3 * s + 1)
        ln(x - s, y - 3 * s + 1, x - s, y - 3 * s + 2)
        ln(x + s, y - 3 * s + 1, x + s, y - 3 * s + 2)

# ---------------------------------------------------------------- drawing
def band():
    rc(0, 0, 72, 7, 0)
    ln(0, 7, 71, 7, 1)

def bar(x, w, f):
    D.drawRectangle(x, 1, w, 5, 1)
    rc(x + 1, 2, int((w - 2) * clamp(f, 0, 1)), 3, 1)

def cockpit(sv=0.0, spd=0, rpm_=0.0, lab=None):
    off = (fr // 2) & 1 if spd > 0 else 0
    # front tyres
    for x0 in (1, 60):
        rc(x0, 30, 11, 10, 1)
        rc(x0 + 1, 29, 9, 1, 1)
        for y in range(31 + off, 39, 2):
            ln(x0 + 1, y, x0 + 9, y, 0)
        rc(x0 + 4, 33, 3, 3, 0)
    # suspension arms
    ln(12, 33, 25, 35)
    ln(12, 37, 24, 38)
    ln(59, 33, 46, 35)
    ln(59, 37, 47, 38)
    # nose cone
    for y in range(30, 40):
        hw = 2 + ((y - 30) * 13) // 9
        ln(36 - hw, y, 36 + hw, y, 0)
    ln(34, 30, 21, 39)
    ln(38, 30, 51, 39)
    # front wing + end plates
    ln(14, 29, 58, 29)
    rc(13, 26, 2, 5)
    rc(57, 26, 2, 5)
    # steering wheel - rotates with your steering
    a = sv * 0.26
    c = cos(a)
    s_ = sin(a)
    for k in range(-12, 13):
        kk = k * 0.5
        ln(round(36 - 14 * c - kk * s_), round(36 - 14 * s_ + kk * c), round(36 + 14 * c - kk * s_), round(36 + 14 * s_ + kk * c), 0)
    for xx, yy, x2, y2 in ((-14, -6, 14, -6), (-14, 6, 14, 6), (-14, -6, -14, 6), (14, -6, 14, 6)):
        ln(round(36 + xx * c - yy * s_), round(36 + xx * s_ + yy * c), round(36 + x2 * c - y2 * s_), round(36 + x2 * s_ + y2 * c))
    for g in (15, 16, 17):
        for sg in (-1, 1):
            ln(round(36 + sg * g * c + 4 * s_), round(36 + sg * g * s_ - 4 * c), round(36 + sg * g * c - 5 * s_), round(36 + sg * g * s_ + 5 * c))
    for j in range(int(clamp(rpm_, 0, 1) * 6.99)):
        xx = -10 + j * 4
        ln(round(36 + xx * c + 8 * s_), round(36 + xx * s_ - 8 * c), round(36 + (xx + 2) * c + 8 * s_), round(36 + (xx + 2) * s_ - 8 * c))
    rc(26, 32, 20, 8, 0)
    tx(lab if lab else "%3d" % spd, 27, 33)

def draw_view(third=False):
    global pcur
    nr = NR3 if third else NR1
    cb = CB if third else 0.0
    pp = ptotal % TL
    pos = (ptotal - cb) % TL
    # scenery panorama (scrolls with the turns)
    j = int(pp / 20)
    if j >= nprof:
        j = nprof - 1
    ho = hd[j] + (hd[j + 1] - hd[j]) * ((pp - j * 20) / 20.0)
    x0 = int(ho) % PAN
    D.blit(PB[x0:x0 + 72] + PB[PANW + x0:PANW + x0 + 72], 0, HOR - 15, 72, 16, -1, 0, 0)
    D.drawLine(0, HOR, 71, HOR, 1)
    k = 0
    while ends2[k] <= pp:
        k += 1
    pcur = cv2[k]
    k = 0
    while ends2[k] <= pos:
        k += 1
    camx = px * 0.8 if third else px
    kinds = SIDE[TR[5]]
    nk = len(kinds)
    poi = int((pos + K / nr) / SPC)
    dx = 0.0
    xo = 0.0
    pl = 0
    pr = 0
    plx = -999
    pin = None
    zs = TL - ZN
    DR = D.drawFilledRectangle
    DL = D.drawLine
    for i in range(nr, 0, -1):
        d = pos + K / i
        while ends2[k] <= d:
            k += 1
        dx += cv2[k] * 0.17
        xo += dx
        XO[i] = xo
        y = HOR + i
        half = (24 * i) // 10
        cx = 36 + xo - camx * half
        l = int(cx - half)
        r = int(cx + half)
        band_ = int(d * 0.08) & 1
        if i < nr:
            DL(l, y, pl, y + 1, 1)
            DL(r, y, pr, y + 1, 1)
            if band_:
                DL(l + 1, y, pl + 1, y + 1, 1)
                DL(r - 1, y, pr - 1, y + 1, 1)
                if i > 2:
                    D.setPixel(l - 3 - i // 2, y, 1)
                    D.setPixel(r + 3 + i // 2, y, 1)
        pl = l
        pr = r
        if i > 1 and (int(d * 0.06) & 1):
            D.setPixel(int(cx), y, 1)
        dm = d % TL
        if dm < K / (i * i) * 1.2:
            DL(l, y, r, y, 1)
        # pit lane runs along the left of the start/finish straight
        inz = dm >= zs or dm <= ZX
        lxs = l
        if inz:
            lxs = l - (half * 6) // 10 - 1
            if plx != -999:
                DL(lxs, y, plx, y + 1, 1)
                if band_ and i > 2:
                    D.setPixel((l + lxs) // 2, y, 1)
            plx = lxs
        else:
            plx = -999
        if pin is not None and inz != pin and i >= 2:
            sx = lxs - 4 - i // 3
            s = 1 + i // 4
            rc(sx - s, y - 3 * s - 1, 2 * s + 3, 2 * s + 1, 1)
            rc(sx, y - 2 * s, 1 + (s > 1), 1, 0)
            ln(sx, y - s, sx, y)
        pin = inz
        oi = int(d / SPC)
        if oi != poi:
            poi = oi
            if i >= 3:
                s = 1 + i // 4
                gx = 2 + (oi % 3) * 2
                side_obj(4 if inz else kinds[oi % nk], lxs - gx - s, y, s)
                side_obj(kinds[(oi + 1) % nk], r + gx + s, y, s)
    # your pit box + crew
    if pitmode:
        rdb = (pbox - ptotal + TL / 2) % TL - TL / 2 + cb
        if 8 < rdb < K:
            i1 = int(K / rdb)
            i2 = int(K / (rdb + 16))
            a1 = i1 if i1 < nr else nr
            a2 = i2 if i2 < nr else nr
            y1 = HOR + i1
            y2 = HOR + i2
            xa1 = 36 + XO[a1] + (-1.04 - camx) * 2.4 * i1
            xb1 = 36 + XO[a1] + (-1.5 - camx) * 2.4 * i1
            xa2 = 36 + XO[a2] + (-1.04 - camx) * 2.4 * i2
            xb2 = 36 + XO[a2] + (-1.5 - camx) * 2.4 * i2
            ln(xa1, y1, xb1, y1)
            ln(xa2, y2, xb2, y2)
            ln(xa1, y1, xa2, y2)
            ln(xb1, y1, xb2, y2)
            for q in range(4):
                rk = rdb + 3 + q * 3.5
                ik = int(K / rk)
                if ik > 26:
                    continue
                ak = ik if ik < nr else nr
                xk = 36 + XO[ak] + (-1.62 - camx) * 2.4 * ik
                yk = HOR + ik
                sk = 1 + ik // 6
                rc(xk, yk - 3 * sk - 1, sk, sk, 1)
                rc(xk - sk // 2, yk - 2 * sk, sk + 1, 2 * sk, 1)
    # other cars (far first)
    vis = []
    for c in range(nai):
        rd = (at[c] - ptotal + TL / 2) % TL - TL / 2 + cb
        if rd < 8:
            continue
        i = int(K / rd)
        if i < 1:
            i = 1
        if i > (24 if third else 15):
            continue
        vis.append((i, c))
    vis.sort()
    for i, c in vis:
        ii = i if i < nr else nr
        x = 36 + XO[ii] + (alane[c] - camx) * 2.4 * i
        car_sprite(x, HOR + i, i, (c + 1) % 3)
    if third:
        x = 36 + clamp((px - camx) * 48, -24, 24)
        car_sprite(x, 39, 20, 2)

def pit_msg():
    """pit lane approach / warnings. returns text or None"""
    dl = TL - (ptotal % TL)
    if lastidx < 0 or dl > 520:
        return None
    if pitreq:
        if dl < ZN + 10:
            if v > PITLIM + 3:
                if fr % 10 == 0:
                    beep(330, 60)
                return "SLOW DOWN!" if (fr // 5) % 2 == 0 else ""
            return "PIT LANE"
        return "PIT IN %dM" % int(dl * 1.6)
    if sess == 'race' and fuel < 25 and nlaps - lastidx > 1 and (fr // 15) % 2 == 0:
        return "PIT? TAP DOWN"
    return None

def hud():
    band()
    if msg_t > 0:
        ctx(msg_s, 0)
        return
    pm = pit_msg()
    if pm is not None:
        ctx(pm, 0)
        return
    m = None
    if pitreq:
        m = "PIT NEXT LAP"
    elif fuel < 10:
        m = "LOW FUEL"
    elif dmg > 60:
        m = "HEAVY DAMAGE"
    if m and (fr // 30) % 2 == 1:
        ctx(m, 0)
        return
    if sess == 'race':
        tx("P%d L%d/%d" % (pos_now(), clamp(lastidx + 1, 1, nlaps), nlaps), 0, 0)
        tx("F", 43, 0)
        bar(49, 9, fuel / 100.0)
        tx("T", 60, 0)
        bar(65, 7, 1 - wear)
    else:
        b = ("B%.1f" % best) if best else "B--"
        if sess_t is None:
            tx("FREE L%d %s" % (lastidx + 1, b), 0, 0)
        else:
            sc = sess_t // 30
            tx("%s %d:%02d %s" % ('P' if sess == 'prac' else 'Q', sc // 60, sc % 60, b), 0, 0)

def wlabel():
    if pitreq and TL - (ptotal % TL) < ZN + 10 and v > PITLIM + 3 and (fr // 5) % 2 == 0:
        return "LIM"
    return None

def drive_draw():
    global svis
    st = (1 if bR.pressed() else 0) - (1 if bL.pressed() else 0)
    svis += (st - svis) * 0.3
    draw_view(cam3)
    if not cam3:
        cockpit(svis, int(v * 2.3), rpm, wlabel())
    if sess == 'race' and startseq:
        band()
        n = min(5, sfr // 30)
        for j in range(5):
            x = 10 + j * 11
            if j < n and sfr < 150 + lo_delay:
                rc(x, 1, 7, 5, 1)
            else:
                D.drawRectangle(x, 1, 7, 5, 1)
    elif sess == 'race' and sfr < 150 + lo_delay + 30:
        band()
        ctx("GO!", 0)
    else:
        hud()

def pause_menu():
    global paused, pmsel, pitreq, snd
    rc(8, 7, 56, 33, 0)
    D.drawRectangle(8, 7, 56, 33, 1)
    items = ("RESUME", "PIT", "SOUND ON" if snd else "SOUND OFF", "QUIT")
    for i in range(4):
        y = 8 + i * 8
        if i == pmsel:
            rc(9, y, 54, 8, 1)
            tx(items[i], 13, y + 1, 0)
        else:
            tx(items[i], 13, y + 1, 1)
    if bD.justPressed():
        pmsel = (pmsel + 1) % 4
    if bB.justPressed():
        paused = False
    if bA.justPressed():
        if pmsel == 0:
            paused = False
        elif pmsel == 1:
            paused = False
            if sess == 'race':
                pitreq = True
            else:
                to_pit()
        elif pmsel == 2:
            snd = not snd
        else:
            paused = False
            quit_session()

# ---------------------------------------------------------------- drive
def lap_event(idx):
    global lapstart, best, last, pitreq
    if sess == 'race':
        if idx >= nlaps:
            finish_race()
            return
        if idx >= 1 and pitreq:
            to_pit()
    else:
        if lapstart is not None:
            lt = (tick - lapstart) * dt
            last = lt
            if best is None or lt < best:
                best = lt
        lapstart = tick
        if pitreq:
            to_pit()

def drive_update():
    global v, px, ptotal, wear, fuel, dmg, hit_cd, tick, startseq, sfr, sess_t, S, lastidx, rpm
    if sess == 'race':
        if startseq:
            sfr += 1
            eng(90 + (sfr % 6) * 3)
            if sfr % 30 == 0 and sfr <= 150:
                beep(600, 100)
            if sfr >= 150 + lo_delay:
                startseq = False
                beep(1200, 300)
            return
        sfr += 1
    ai_step()
    tick += 1
    st = (1 if bR.pressed() else 0) - (1 if bL.pressed() else 0)
    thr = bA.pressed()
    top = g_top * (1 - 0.0003 * fuel) * (1 - 0.003 * dmg)
    if fuel <= 0:
        top *= 0.3
    if abs(px) > 1.0:
        top *= 0.45
    if v > top:
        v -= 35 * dt
    elif thr and fuel > 0:
        v += g_acc * (1 - 0.75 * v / top) * dt
    if not thr:
        v -= (3 + v * v * 0.0012) * dt
    if bB.pressed():
        v -= 55 * dt
    if v < 0:
        v = 0.0
    gr = v / g_top
    gear = min(6, 1 + int(gr * 6.0))
    fq = clamp(gr * 6.0 - (gear - 1), 0.0, 1.0)
    rpm = 0.3 + 0.7 * fq
    if not thr:
        rpm *= 0.8
    if v < 1:
        rpm = 0.25
    eng(70 + rpm * 400)
    vr = v / top
    if vr > 1.2:
        vr = 1.2
    grip = g_grip * (1 - 0.35 * wear) * (1 - 0.002 * dmg)
    eff = 1.5 * clamp(v / 15.0, 0, 1)
    sl = grip / (vr * 1.1 + 0.001)
    if sl > 1:
        sl = 1.0
    px += st * eff * sl * dt
    px -= pcur * vr * vr * (2.0 / grip) * dt
    if hit_cd > 0:
        hit_cd -= 1
    if px > 1.45 or px < -1.45:
        px = 1.45 if px > 0 else -1.45
        if hit_cd == 0:
            dmg = min(100.0, dmg + 4)
            v *= 0.7
            hit_cd = 15
            beep(120, 60)
    d = v * dt
    ptotal += d
    fuel -= d * 0.0043
    if fuel < 0:
        fuel = 0.0
    wear = min(1.0, wear + g_wr * dt * (0.0008 + 0.0035 * abs(st) * vr))
    collide()
    if sess_t is not None:
        sess_t -= 1
        if sess_t <= 0:
            if sess == 'qual':
                finalize_qual()
            S = 'summary'
            return
    idx = int(ptotal // TL)
    if idx != lastidx:
        lastidx = idx
        lap_event(idx)

def st_drive():
    global paused, pmsel, pitreq, cam3, msg_t, msg_s, dhold, dfired
    if msg_t > 0:
        msg_t -= 1
    if bU.justPressed():
        cam3 = not cam3
        msg_t = 40
        msg_s = "CHASE CAM" if cam3 else "COCKPIT"
        beep(500, 30)
    if paused:
        dhold = 0
        dfired = False
        drive_draw()
        pause_menu()
        return
    if bD.pressed():
        dhold += 1
        if dhold == 15 and not startseq:
            paused = True
            pmsel = 0
            dfired = True
    else:
        if 0 < dhold < 15 and not dfired and not startseq:
            pitreq = not pitreq
            beep(600, 40)
        dhold = 0
        dfired = False
    drive_update()
    if S != 'drive':
        return
    drive_draw()

# ---------------------------------------------------------------- tune / pit animations
def tune_go():
    global S, anim, tctx, svc_frames, pen_frames, st_pt, st_px, ptotal, px, v, pbox
    car_params()
    if tctx == 'pre':
        begin_drive(sess)
        st_pt = ptotal
        st_px = px
        ptotal = 45.0
        pbox = 45.0
        px = -1.25
        v = 0.0
        anim = 0
        S = 'pitout'
    elif sess == 'race':
        ff = max(0.0, FUEL[tune[3]] - fuel) / 100.0
        svc_frames = int((4.0 + ff * 3.0 + 2.5 + dmg * 0.04) * 30)
        pen_frames = int(pit_pen * 30)
        anim = 0
        S = 'pitbox'
    else:
        service()
        anim = 0
        S = 'pitout'

def st_tune():
    global trow
    if tctx == 'mid' and sess == 'race':
        ai_step()
    if bU.justPressed():
        trow = (trow - 1) % 5
    if bD.justPressed():
        trow = (trow + 1) % 5
    dv = (1 if bR.justPressed() else 0) - (1 if bL.justPressed() else 0)
    if dv and trow < 4:
        lim = (5, 5, 2, 4)[trow]
        lo = (1, 1, 0, 0)[trow]
        tune[trow] = int(clamp(tune[trow] + dv, lo, lim))
    if bA.justPressed():
        if trow < 4:
            trow = 4
        else:
            tune_go()
            return
    names = ("WING", "GEAR", "TIRE", "FUEL", "GO!")
    vals = (str(tune[0]), str(tune[1]), ("SOFT", "MED", "HARD")[tune[2]], "%d%%" % FUEL[tune[3]], "")
    for i in range(5):
        y = i * 8
        sel = (i == trow)
        c = 0 if sel else 1
        if sel:
            rc(0, y, 72, 8, 1)
        tx(names[i], 2, y + 1, c)
        if i < 4:
            tx(vals[i], 34, y + 1, c)
            if sel:
                tx("<", 26, y + 1, c)
                tx(">", 62, y + 1, c)
        else:
            tx("DMG%d%%" % int(dmg), 34, y + 1, c)

def st_pitout():
    global anim, S, v, px, tctx, ptotal, pitmode, svis, rpm
    pitmode = True
    if tctx == 'mid' and sess == 'race':
        ai_step()
    anim += 1
    a = anim
    if a <= 60:
        vt = PITLIM
        dpx = 0.0
    else:
        vt = PITLIM if (tctx == 'pre' and sess == 'race') else 46.0
        dpx = clamp(0.0 - px, -0.03, 0.03)
    px += dpx
    v += clamp(vt - v, -40 * dt, 16 * dt)
    ptotal += v * dt
    svis += (clamp(dpx * 40, -1, 1) - svis) * 0.3
    rpm = 0.3 + 0.5 * clamp(v / 46.0, 0, 1) + 0.1 * ((a // 3) & 1)
    eng(70 + rpm * 400)
    draw_view(cam3)
    if not cam3:
        cockpit(svis, int(v * 2.3), rpm, "LIM" if (a <= 60 and v > PITLIM - 2 and (a // 5) % 2 == 0) else None)
    band()
    if a < 40:
        ctx("PIT LIMITER", 0)
    elif a < 70:
        ctx("PIT EXIT", 0)
    elif (a // 5) % 2 == 0:
        ctx("GO GO GO!", 0)
    if a >= 105:
        pitmode = False
        if tctx == 'pre' and sess == 'race':
            ptotal = st_pt
            px = st_px
            v = 0.0
        elif tctx == 'pre':
            v = 40.0
        S = 'drive'
        tctx = 'run'
        beep(900, 80)

def human(x, y, w):
    x = int(x)
    rc(x, y, 2, 2, 1)
    rc(x - 1, y + 2, 4, 5, 1)
    if w:
        D.setPixel(x + 3 + ((fr // 3) & 1), y + 3, 1)

def st_pitbox():
    global anim, S, rpm
    ai_step()
    anim += 1
    t = anim - pen_frames
    hold = t < 0
    p = 0.0 if hold else t / float(svc_frames)
    lift = 2 if 0.14 < p < 0.8 else (1 if 0.1 < p <= 0.14 or 0.8 <= p < 0.84 else 0)
    hz = 17 + lift
    eng(80 + (fr % 4) * 4 + (60 if 0.86 < p < 0.92 else 0))
    ln(0, hz, 71, hz, 1)
    for bx in (2, 20, 44, 60):
        rc(bx, hz - 5, 10, 5, 1)
        rc(bx + 2, hz - 3, 3, 3, 0)
    cr = clamp(p / 0.12, 0, 1)
    work = 0.14 < p < 0.8
    o = lift
    # tyre crew (carry a new wheel in, swap, carry the old one away)
    human(-6 + 18 * cr, 19 + o, work)
    human(78 + (60 - 78) * cr, 19 + o, work)
    if work:
        wob = (fr // 2) & 1
        rc(12, 25 + o, 3, 4 - wob, 1)
        rc(57, 25 + o, 3, 4 - (1 - wob), 1)
        if fr % 2 == 0:
            D.setPixel(random.randint(2, 11), random.randint(24, 29), 1)
            D.setPixel(random.randint(60, 69), random.randint(24, 29), 1)
    elif 0.8 <= p < 0.9:
        rc(4, 24 + o, 3, 4, 1)
        rc(65, 24 + o, 3, 4, 1)
    # fuel rig
    human(78 + (66 - 78) * cr, 11 + o, work)
    if work:
        ln(66, 18 + o, 60, 27, 1)
        rc(62, 8 + o, 3, 1, 1)
    # screen cleaner
    if 0.3 < p < 0.6:
        wx = 26 + int(10 + 10 * sin(fr * 0.5))
        ln(wx, 9 + o, wx + 3, 13 + o)
    # lollipop / jack man at the nose
    if p < 0.88:
        rc(31, 13 + o, 11, 4, 1)
        rc(35, 14 + o, 3, 2, 0)
        rc(36, 17 + o, 1, 9, 1)
    cockpit(0.0, 0, 0.35 + 0.05 * ((fr // 2) & 1))
    band()
    if hold:
        if (anim // 6) % 2 == 0:
            ctx("SPEEDING +%dS" % int(pit_pen + 0.5), 0)
    else:
        tx("PIT %.1fs" % (t * dt), 0, 0)
        bar(50, 15, p)
        # release light: red -> green
        if p < 0.88:
            D.drawRectangle(67, 1, 5, 5, 1)
        else:
            rc(67, 1, 5, 5, 1)
    if anim >= pen_frames + svc_frames:
        service()
        anim = 0
        S = 'pitout'

# ---------------------------------------------------------------- results
def st_finish():
    global fin_t, v, ptotal, S, rscroll
    fin_t += 1
    v = max(0.0, v - 20 * dt)
    ptotal += v * dt
    ai_step()
    draw_view(cam3)
    if not cam3:
        cockpit(0.0, int(v * 2.3), v / g_top)
    band()
    if (fin_t // 5) % 2 == 0:
        ctx("FINISH!", 0)
    if fin_t > 100:
        if mode == 'season':
            for p, i in enumerate(res_order):
                spts[i] += PTS[p]
        rscroll = int(clamp(res_order.index(0) - 2, 0, 4))
        S = 'results'

def st_results():
    global rscroll, S, srd, fscroll
    lst = []
    for p, i in enumerate(res_order):
        s = "%d %s" % (p + 1, NAMES[i])
        if mode == 'season':
            s += " +%d" % PTS[p]
        lst.append(s)
    if bU.justPressed():
        rscroll = max(0, rscroll - 1)
    if bD.justPressed():
        rscroll = min(4, rscroll + 1)
    rows(lst, res_order.index(0), 0, 5, rscroll)
    if bA.justPressed():
        if mode == 'season':
            srd += 1
            if srd >= NTR:
                fscroll = 0
                S = 'final'
            else:
                season_event()
        else:
            S = 'menu'

def st_stand():
    global fscroll, S
    order = sorted(range(9), key=lambda i: -spts[i])
    lst = ["%d %s %d" % (r + 1, NAMES[i], spts[i]) for r, i in enumerate(order)]
    hi = order.index(0)
    if bU.justPressed():
        fscroll = max(0, fscroll - 1)
    if bD.justPressed():
        fscroll = min(5, fscroll + 1)
    if S == 'final':
        ctx("CHAMPION!" if hi == 0 else "P%d OVERALL" % (hi + 1), 0)
        rows(lst, hi, 8, 4, min(fscroll, 5))
        if bA.justPressed():
            S = 'menu'
    else:
        rows(lst, hi, 0, 5, min(fscroll, 4))
        if bA.justPressed() or bB.justPressed():
            S = 'hub'

def st_summary():
    global S
    ctx("QUALIFYING" if sess == 'qual' else "PRACTICE", 0)
    ctx(("BEST %.1fs" % best) if best else "NO LAP SET", 10)
    ctx("LAPS %d" % max(0, lastidx), 18)
    if sess == 'qual':
        ctx(("GRID P%d" % qgrid) if qgrid else "NO GRID", 26)
    if (fr // 15) % 2 == 0:
        ctx("A-OK", 33)
    if bA.justPressed():
        S = 'hub'

# ---------------------------------------------------------------- menus
def st_title():
    global S, msel
    ctx("IndyCar '27", 2)
    sc = (fr * 3) % 72
    # speed lines + ground
    for j in range(3):
        x = (fr * 3 + j * 24) % 72
        ln(x, 13 + j * 4, x + 6, 13 + j * 4, 1)
    for j in range(6):
        x = 72 - ((fr * 4 + j * 14) % 84)
        rc(x, 30, 6, 1, 1)
    # side-view IndyCar (nose to the right)
    rc(14, 14, 3, 9, 1)            # rear wing end plate
    rc(12, 13, 9, 2, 1)            # rear wing
    rc(18, 21, 40, 3, 1)           # tub
    rc(22, 18, 9, 3, 1)            # engine cover
    rc(31, 17, 2, 4, 1)            # airbox/aeroscreen post
    rc(32, 17, 9, 1, 1)            # aeroscreen
    rc(33, 18, 7, 3, 0)
    ln(41, 17, 45, 21)
    ln(58, 22, 66, 24)             # nose
    rc(63, 25, 7, 1, 1)            # front wing
    rc(68, 22, 1, 5, 1)            # front end plate
    for wx, wr in ((18, 4), (50, 3)):
        rc(wx, 22, wr * 2 + 3, wr * 2 + 3, 1)
        rc(wx + wr - 1, 24 + wr // 2, 3, 3, 0)
    if (fr // 15) % 2 == 0:
        ctx("A-start", 32)
    if bA.justPressed():
        beep(880, 60)
        msel = 0
        S = 'menu'

def hsel_reset():
    global hsel
    hsel = 0

def st_menu():
    global msel, S, mode, tune, tsel, nlap, srd, spts
    if bU.justPressed():
        msel = (msel - 1) % 5
    if bD.justPressed():
        msel = (msel + 1) % 5
    rows(("QUICK RACE", "SINGLE RACE", "SEASON", "PRACTICE", "INFO"), msel)
    if bA.justPressed():
        beep(700, 40)
        if msel == 0:
            mode = 'quick'
            ti = random.randint(0, NTR - 1)
            sl = TRACKS[ti][4]
            laps = random.randint(max(3, sl // 2), sl + 2)
            tune = [random.randint(1, 5), random.randint(1, 5), random.randint(0, 2), random.randint(2, 4)]
            new_event(ti, laps, rnd(-0.02, 0.02))
            hsel_reset()
            S = 'hub'
        elif msel == 1:
            mode = 'single'
            S = 'tracksel'
        elif msel == 2:
            mode = 'season'
            srd = 0
            spts = [0] * 9
            season_event()
        elif msel == 3:
            mode = 'practice'
            S = 'tracksel'
        else:
            S = 'info'

def st_tracksel():
    global tsel, S, nlap
    if bL.justPressed():
        tsel = (tsel - 1) % NTR
    if bR.justPressed():
        tsel = (tsel + 1) % NTR
    t = TRACKS[tsel]
    ctx("TRACK", 0)
    tx("<", 0, 11)
    tx(">", 66, 11)
    ctx(t[0], 11)
    ctx(t[1], 20)
    ctx("OVAL" if t[3] else "ROAD COURSE", 27)
    ctx("A:OK  B:BACK", 33)
    if bB.justPressed():
        S = 'menu'
    if bA.justPressed():
        if mode == 'single':
            nlap = t[4] + (2 if not t[3] else 0)
            S = 'lapsel'
        else:
            new_event(tsel, 0)
            start_session('free')

def st_lapsel():
    global nlap, S
    dv = (1 if bR.justPressed() else 0) - (1 if bL.justPressed() else 0)
    dv += 5 * ((1 if bU.justPressed() else 0) - (1 if bD.justPressed() else 0))
    nlap = int(clamp(nlap + dv, 1, 50))
    ctx(TRACKS[tsel][0], 0)
    ctx("LAPS", 11)
    ctx("< %d >" % nlap, 20)
    ctx("A:GO  B:BACK", 33)
    if bB.justPressed():
        S = 'tracksel'
    if bA.justPressed():
        new_event(tsel, nlap)
        start_session('race')

def st_hub():
    global hsel, S
    items = ["PRACTICE", "QUALIFY", "RACE"] + (["STANDINGS"] if mode == 'season' else []) + ["QUIT"]
    if hsel >= len(items):
        hsel = 0
    if bU.justPressed():
        hsel = (hsel - 1) % len(items)
    if bD.justPressed():
        hsel = (hsel + 1) % len(items)
    tx(TR[0][:12], 0, 0)
    pre = ("R%d " % (srd + 1)) if mode == 'season' else ""
    tx(("%s%dLAPS G%s" % (pre, nlaps, qgrid if qgrid else "-"))[:12], 0, 8)
    rows(items, hsel, 16, 3)
    if bA.justPressed():
        it = items[hsel]
        if it == "PRACTICE":
            start_session('prac')
        elif it == "QUALIFY":
            start_session('qual')
        elif it == "RACE":
            start_session('race')
        elif it == "STANDINGS":
            S = 'stand'
        else:
            S = 'menu'
    if bB.justPressed():
        S = 'menu'

INFO = (
    "INDYCAR '27", "CONTROLS:", "A  THROTTLE", "B  BRAKE", "L/R STEER",
    "UP CAMERA", "D = PIT STOP", "  LAP", "DOWN HOLD", "  = PAUSE", "",
    "PIT STOPS:", "TAP DOWN TO", "CALL A STOP.", "HUD SHOWS", "PIT IN 300M,", "BRAKE TO THE", "LIMIT OR GET", "A TIME", "PENALTY.", "", "SOUND: HOLD", "DOWN, PAUSE", "MENU TOGGLE", "",
    "TUNING:",
    "WING GRIP/V", "GEAR ACC/TOP", "TIRE GRIP/WR", "FUEL WEIGHT", "",
    "QUICK RACE:", "RANDOM TRACK", "LAPS, SETUP", "", "SINGLE RACE:",
    "PICK TRACK", "AND LAPS", "", "SEASON: 7", "TRACKS, MOST",
    "POINTS WINS", "", "PRACTICE:", "FREE RUN +", "TUNING", "", "QUICK/SEASON",
    "5 MIN PRAC", "5 MIN QUALI", "QUALI = GRID", "", "B: BACK",
)

def st_info():
    global iscroll, S
    if bU.justPressed():
        iscroll = max(0, iscroll - 1)
    if bD.justPressed():
        iscroll = min(len(INFO) - 5, iscroll + 1)
    rows(INFO, -1, 0, 5, iscroll)
    if bB.justPressed() or bA.justPressed():
        S = 'menu'

HANDLERS = {
    'title': st_title, 'menu': st_menu, 'tracksel': st_tracksel, 'lapsel': st_lapsel,
    'hub': st_hub, 'tune': st_tune, 'pitin': st_pitin, 'pitout': st_pitout, 'pitbox': st_pitbox,
    'drive': st_drive, 'finish': st_finish, 'results': st_results,
    'stand': st_stand, 'final': st_stand, 'summary': st_summary, 'info': st_info,
}

# ---------------------------------------------------------------- main loop
while True:
    D.fill(0)
    fr += 1
    HANDLERS[S]()
    D.update()
