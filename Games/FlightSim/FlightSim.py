# Thumby Flight Sim - plane, jet + helicopter, 30 FPS wireframe 3D, MicroPython
# Files (keep together, e.g. /Games/FlightSim/): FlightSim.py (game) | fs_engine.py (3D engine)
# | fs_menu.py (title/menu/help, loaded only while in the menu)
# MODES: FREE | RINGS (8 hoops, timed) | LAND (runway score).  OPTIONS: FUEL, ASSIST, WIND
# PLANE/JET  L/R bank, D nose up, U nose down, A/B throttle
# HELI       L/R turn, U forward, D back, A climb, B descend (let go = hover)
# A+B switch aircraft (plane > jet > heli)   L+R view   U+D map/pause (A/B zoom, L+R quit)
import sys
for _p in ("/Games/FlightSim", ""):
    if _p not in sys.path:
        sys.path.append(_p)
import time
import math
import gc
import random
import thumby
gc.collect()
try:
    import fs_engine as E
    from fs_engine import find_settlements
except Exception as _ex:      # e.g. firmware without viper: say so instead of crashing silently
    print("fs_engine failed to load:", _ex)
    thumby.display.fill(0)
    thumby.display.drawText("ENGINE", 18, 8, 1)
    thumby.display.drawText("ERROR", 21, 18, 1)
    thumby.display.update()
    while True:
        time.sleep_ms(1000)

FPS = 30
LOD_MIN = 0.45               # adaptive detail never drops below 45% draw distance
CHASE_D, CHASE_H, EYE, HELI_EYE = 14.0, 4.0, 2.0, 1.2
LAND_V, SINK, TAKEOFF_V = 75, 18, 50                     # plane landing limits / take-off speed
HELI_V, HELI_REV, HELI_CLIMB, HELI_LAND_V, HELI_SINK = 45, 12, 20, 18, 10
LK = (1.4, 1.0, 0.75)        # landing tolerance for EASY / NORMAL / HARD
WK = (0.6, 1.0, 1.4)         # wind strength for EASY / NORMAL / HARD
RINGS_N = 8
MAP_SCALES = (10, 24, 56)

sin, cos, atan2 = math.sin, math.cos, math.atan2
disp = thumby.display
disp.setFPS(FPS)
_snd = True

def beep(f, ms):
    if _snd:
        try:
            thumby.audio.play(f, ms)
        except Exception:
            pass

def rnd():
    return random.getrandbits(16) / 65536.0

# ---------------- saved settings + records ----------------
def load_saved():
    """-> (settings, records); records = [best rings time plane/heli/jet, best landing, flights, landed, crashed]"""
    cfg, rec = [0, 0, 0, 0, 1, 0, 0, 0, 0], [0] * 7
    try:
        sd = thumby.saveData
        sd.setName("FlightSim")
        if sd.hasItem("cfg"):
            c = sd.getItem("cfg")
            c = c[:5] + c[6:] if len(c) == 8 else c           # oldest save had a PITCH option
            c = c[:6] + [0, 0] + c[6:] if len(c) == 7 else c   # ...and no FUEL / ASSIST
            if len(c) == 9:
                cfg = c
                cfg[0] = cfg[0] if cfg[0] < 3 else 0           # the TOUR mode was removed
        if sd.hasItem("rec"):
            r = sd.getItem("rec")
            r = [r[0], r[1], 0, r[2], 0, 0, 0] if len(r) == 3 else ([r[0], r[1], r[2]] + r[6:] if len(r) == 10 else r)
            rec = r if len(r) == 7 else rec
    except Exception:
        pass
    return cfg, rec

def save_saved(cfg, rec):
    try:
        sd = thumby.saveData
        sd.setName("FlightSim")
        sd.setItem("cfg", cfg)
        sd.setItem("rec", rec)
        sd.save()
    except Exception:
        pass

# ---------------- HUD / cockpit / map ----------------
def draw_cockpit(heli, fc):
    dl = disp.drawLine
    for x, y in ((36, 20), (33, 20), (39, 20), (36, 17)):
        disp.setPixel(x, y, 1)
    if heli:  # bubble frame + blurred rotor along the top
        for q in ((0, 24, 6, 33), (6, 33, 14, 39), (71, 24, 65, 33), (65, 33, 57, 39)):
            dl(q[0], q[1], q[2], q[3], 1)
        for x in range(14 + (fc & 1) * 2, 58, 4):
            disp.setPixel(x, 0, 1)
    else:     # nose cone
        for q in ((24, 39, 31, 34), (31, 34, 41, 34), (41, 34, 48, 39)):
            dl(q[0], q[1], q[2], q[3], 1)

def arrow(cx, cy, a, n):
    disp.drawLine(cx, cy, int(cx + sin(a) * n), int(cy - cos(a) * n), 1)
    disp.setPixel(cx, cy, 1)

def draw_hud(heli, py, gy, v, side, on_ground, tag, warn, clock):
    t = disp.drawText
    t(str(int(py - gy)), 0, 0, 1)            # height above ground / roof
    t(str(int(abs(v))), 0, 33, 1)
    if heli:                                  # vertical-speed bar from the centre
        disp.drawLine(71, 20, 71, 20 - int(side / HELI_CLIMB * 16), 1)
    else:                                     # throttle bar from the bottom
        for x in (70, 71):
            disp.drawLine(x, 39, x, 39 - int(side * 25), 1)
    if on_ground:
        t(tag, 54, 0, 1)
    elif clock:
        t(clock, 72 - 6 * len(clock), 0, 1)
    if warn:
        t(warn, 18, 0, 1)

def show_map(px, pz, h):
    """Pause + map: A/B zoom out/in, Up+Down resume, Left+Right quit. -> True to quit to the menu."""
    T = thumby
    keys = lambda: (T.buttonA.pressed(), T.buttonB.pressed(), T.buttonU.pressed(),
                    T.buttonD.pressed(), T.buttonL.pressed(), T.buttonR.pressed())
    while any(keys()):
        time.sleep_ms(20)
    sets = find_settlements(px - 2400, px + 2400, pz - 2400, pz + 2400)
    near = [99999, 99999]                    # nearest city / town
    for kind, cx, cz, hs in sets:
        near[kind] = min(near[kind], math.sqrt((cx - px) ** 2 + (cz - pz) ** 2))
    zi, pa, pb = 1, False, False
    while True:
        a, b, u, d, l, r = keys()
        if (u and d) or (l and r):
            break
        zi = max(0, min(2, zi + (a and not pa) - (b and not pb)))
        pa, pb = a, b
        s = MAP_SCALES[zi]
        disp.fill(0)
        for kind, cx, cz, hs in sets:        # city = filled square, town = hollow square
            mx, my = int(36 + (cx - px) / s), int(20 - (cz - pz) / s)
            for i in range(3):
                for j in range(3):
                    if (kind == 0 or i != 1 or j != 1) and 0 <= mx - 1 + i < 72 and 0 <= my - 1 + j < 40:
                        disp.setPixel(mx - 1 + i, my - 1 + j, 1)
        E.line2(36 - px / s, 20 + (pz + 60) / s, 36 - px / s, 20 + (pz - 60) / s)     # runway
        for q in ((0, 5, 2.6, 4), (0, 5, -2.6, 4), (2.6, 4, -2.6, 4)):                # your aircraft
            disp.drawLine(int(36 + sin(h + q[0]) * q[1]), int(20 - cos(h + q[0]) * q[1]),
                          int(36 + sin(h + q[2]) * q[3]), int(20 - cos(h + q[2]) * q[3]), 1)
        disp.drawText("N", 66, 0, 1)
        disp.drawText("x" + str(s), 0, 0, 1)
        for i, ch in enumerate("CT"):
            tx = ch + (str(int(near[i])) if near[i] < 9999 else "-")
            disp.drawText(tx, 0 if i == 0 else 72 - 6 * len(tx), 33, 1)
        disp.update()
    while any(keys()):
        time.sleep_ms(20)
    return l and r

def end_screen(msg, st):
    """Result + stats. Returns True to fly again, False for the menu."""
    secs = int(st[0])
    disp.fill(0)
    disp.drawText(msg, 36 - len(msg) * 3, 0, 1)
    disp.drawText("TIME %d:%02d" % (secs // 60, secs % 60), 0, 11, 1)
    disp.drawText("DIST " + str(int(st[1])), 0, 20, 1)
    disp.drawText("A:GO", 0, 32, 1)
    disp.drawText("B:MENU", 36, 32, 1)
    disp.update()
    while thumby.buttonA.pressed() or thumby.buttonB.pressed():
        time.sleep_ms(20)
    while not (thumby.buttonA.pressed() or thumby.buttonB.pressed()):
        time.sleep_ms(20)
    return thumby.buttonA.pressed()

# ---------------- rings ----------------
def new_ring(x, y, z, a, heli):
    """Next ring ahead of (x,y,z) around heading a -> (x, y, z, axis, heading)"""
    a += (rnd() - 0.5) * 1.6
    d = (90 + rnd() * 60) if heli else (150 + rnd() * 90)
    lo, hi = (12, 70) if heli else (25, 130)
    return (x + sin(a) * d, min(hi, max(lo, y + (rnd() - 0.5) * 50)), z + cos(a) * d,
            0 if abs(cos(a)) > abs(sin(a)) else 1, a)

def ring_pass(r, ox, oy, oz, px, py, pz, rr):
    """Did the move (o)->(p) cross ring r's plane within radius rr?"""
    i = 2 if r[3] == 0 else 0                # axis 0 faces z, axis 1 faces x
    s0, s1 = (oz - r[2], pz - r[2]) if i == 2 else (ox - r[0], px - r[0])
    if s0 * s1 > 0 or s0 == s1:
        return False
    t = s0 / (s0 - s1)
    lat = (ox + (px - ox) * t - r[0]) if i == 2 else (oz + (pz - oz) * t - r[2])
    cy = oy + (py - oy) * t - r[1]
    return lat * lat + cy * cy <= rr * rr

# ---------------- crash: calm slow-motion ----------------
def crash_scene(heli, px, py, pz, h, p, r, v, vy, o, jet=False):
    """1.5 s of slow motion: small fireball, drifting wreckage, orbiting camera.
    A struck object (o) is left visibly broken."""
    gc.collect()
    if o:
        E.damage(o, int(px * 8) - o[1], int(min(py, o[4]) * 8), int(pz * 8) - o[2])
    k = (0.15 if o else 0.4) * 0.25                       # speed carried into the slow-mo wreck
    cp = cos(p)
    vx, vz, vyy = sin(h) * cp * v * k, cos(h) * cp * v * k, (vy if heli else sin(p) * v) * k
    gy0 = max(py, 0.0)
    seed = int(px * 7 + pz * 13) & 0xFFFF
    tc, fc, last = 0.0, 0, time.ticks_ms()
    while tc < 1.5:
        now = time.ticks_ms()
        tc += min(time.ticks_diff(now, last) / 1000, 0.1)
        last = now
        fc += 1
        u = tc / 1.5
        a, sh = h + 0.4 * tc, 0.3 * (1 - u)               # slow camera orbit, tiny fading shake
        E.set_camera(px - sin(a) * 24 + (rnd() - 0.5) * sh, gy0 + 9 + (rnd() - 0.5) * sh,
                     pz - cos(a) * 24 + (rnd() - 0.5) * sh, a, -0.35, 0)
        disp.fill(0)
        E.draw_world(a, 3, 0.8, 1.25)
        E.draw_wreck(heli, px + vx * tc, max(0.0, gy0 + vyy * tc - tc * tc) + 1.0, pz + vz * tc, h, p, r, u, seed, jet)
        E.draw_explosion(px, gy0 + 2.0, pz, u, fc)
        if fc == 1:                                       # sound: thud, metal crunch, fading rumble
            beep(70, 200)
        elif fc < 10:
            beep(150 + int(rnd() * 350), 35)
        elif fc % 3 == 0 and u < 0.8:
            beep(int((110 * (1 - u) + 50) * (0.7 + rnd() * 0.6)), 70)
        disp.update()

# ---------------- one run ----------------
def start(mode, sat, ac, at):
    """Starting state: x, y, z, heading, pitch, speed, on_ground"""
    x, y, z, h, gnd = 0.0, 80.0, -320.0, 0.0, False
    v = 0.0 if ac == 1 else (105.0 if ac == 2 else 70.0)
    if mode == 2:                           # LAND: high up, 450 units out, facing the runway
        a = rnd() * 6.283
        x, z, y = sin(a) * 450, cos(a) * 450, 110.0
        h = atan2(-x, -z)
    elif sat == 1:                          # on the runway, ready to take off
        x, y, z, v, gnd = 0.0, 0.0, -50.0, 0.0, True
    elif sat == 2:                          # near the closest city
        cs = [(cx * cx + cz * cz, cx, cz) for k, cx, cz, hs in find_settlements(-2400, 2400, -2400, 2400) if k == 0]
        if cs:
            c = min(cs)
            x, z, y = float(c[1]), float(c[2] - 280), 70.0
    p = 0.0
    if at:                                  # (x, y, z, heading, pitch, speed[, on_ground]) - for testing
        x, y, z, h, p, v = at[:6]
        gnd = len(at) > 6 and at[6]
    return x, y, z, h, p, (min(v, HELI_V) if ac == 1 else v), gnd

def fly(cfg, rec, at=None, fuel0=100.0):
    """Play one run. Returns (message, (seconds, distance))."""
    global _snd
    mode, ac, sat, view, lvl, wnd, fu, asst, snd = cfg      # ac: 0 plane, 1 heli, 2 jet
    _snd = snd == 0
    chase = view == 0
    lk, wscale = LK[lvl], WK[lvl]
    ring_r = 15.0 * math.sqrt(lk)
    px, py, pz, h, p, v, on_ground = start(mode, sat, ac, at)
    r, vy, thr, gy, lod, fuel = 0.0, 0.0, (0.0 if on_ground else 0.5), 0.0, 1.0, fuel0
    fc, tm, dist, rcount, msg, msg_t = 0, 0.0, 0.0, 0, "", 0
    prev_lr = prev_ab = False
    rings = []
    if mode == 1:
        r0 = new_ring(px, py, pz, h, ac == 1)
        rings = [r0, new_ring(r0[0], r0[1], r0[2], r0[4], ac == 1)]
    rec[4] += 1                                             # lifetime flights
    gc.collect()
    E.regen_now(px, pz)
    last = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        raw = time.ticks_diff(now, last) / 1000
        last = now
        dt = min(raw, 0.1)
        fc += 1
        tm += dt
        ox, oy, oz = px, py, pz
        if raw > 1.2 / FPS:                  # adaptive detail: slow frame -> draw less
            lod = max(LOD_MIN, lod - 0.04)
        elif raw < 1.1 / FPS and lod < 1.0:
            lod += 0.01

        a, b = thumby.buttonA.pressed(), thumby.buttonB.pressed()
        l, rt, u, d = thumby.buttonL.pressed(), thumby.buttonR.pressed(), thumby.buttonU.pressed(), thumby.buttonD.pressed()
        if u and d:                          # Up+Down: map / pause
            if show_map(px, pz, h):
                return "QUIT", (tm, dist)
            last = time.ticks_ms()
            continue
        if l and rt and not prev_lr:         # Left+Right: switch view
            chase = not chase
            msg, msg_t = ("CHASE" if chase else "1ST PERSON"), 25
        prev_lr = l and rt
        if a and b and not prev_ab:          # A+B: switch aircraft  plane > jet > heli > plane
            nac, jf = (2, 0, 1)[ac], (1.5 if ac == 2 else 1.0)
            if ac == 1 and on_ground and gy > 0:
                msg = "NO ROOM"
            elif ac == 1 and not on_ground and py < 10:
                msg = "TOO LOW"
            else:
                nj = 1.5 if nac == 2 else 1.0
                if nac == 1:
                    v = 0.0 if on_ground else min(v, HELI_V)
                elif ac == 1:
                    v, thr = (0.0, 0.0) if on_ground else (62.0 * nj, 0.6)
                else:
                    v *= nj / jf                                # plane <-> jet keeps your energy
                ac, vy, p, r = nac, 0.0, 0.0, 0.0
                msg = ("PLANE", "HELI", "JET")[ac]
                beep(500, 60)
            msg_t = 25
        prev_ab = a and b

        heli, jet = ac == 1, ac == 2
        jf = 1.5 if jet else 1.0                                # jet: faster, needs more speed to fly and land
        sink_lim, land_v, hsink, hland = SINK * lk, LAND_V * lk * jf, HELI_SINK * lk, HELI_LAND_V * lk
        pin = (1 if d else 0) - (1 if u else 0)             # +1 = pull back (plane nose up)
        rin = (1 if rt else 0) - (1 if l else 0)
        E.update(px, pz)
        if not heli:
            gy = 0.0
        if fc % 45 == 0:
            gc.collect()                     # a short planned pause instead of a surprise one
        sink, warn, touched, dead = 0.0, "", False, False
        dry = fu and fuel <= 0               # out of fuel

        if heli:
            # ================= HELICOPTER =================
            h += rin * 1.3 * dt
            if on_ground:
                v = vy = p = r = 0.0
                py = gy
                if a and not b and not dry:
                    on_ground, vy, py = False, 4.0, gy + 0.5
            else:
                fwd = -pin                                  # Up = forward
                v += ((fwd * HELI_V if fwd > 0 else fwd * HELI_REV) - v) * 1.2 * dt
                vy += ((-10 if dry else (HELI_CLIMB if a else 0) - (HELI_CLIMB if b else 0)) - vy) * 2.0 * dt
                if py - gy < 10 and vy < -8.0:
                    vy = -8.0                               # ground effect: holding B lands gently
                if asst and py - gy < 15:
                    v -= v * 3.0 * dt                       # assist: slow down near the ground
                p += (-0.3 * v / HELI_V - p) * 3.0 * dt
                r += (rin * 0.3 - r) * 3.0 * dt
                px += sin(h) * v * dt
                pz += cos(h) * v * dt
                py = min(500.0, py + vy * dt)
                gy = E.roof(px, pz) if py < 100 else 0.0    # helis can land on rooftop pads
                sink = -vy
                if py <= gy:
                    py = gy
                    if abs(v) < hland and vy >= -hsink:
                        on_ground = touched = True
                        v = vy = p = r = 0.0
                    else:
                        dead = True
                elif py - gy < 25 and abs(v) > hland:
                    warn = "FAST"
        else:
            # ================= PLANE / JET =================
            thr = 0.0 if dry else min(1.0, max(0.0, thr + ((1 if a else 0) - (1 if b else 0)) * 0.6 * dt))
            if on_ground:
                v += (110 * jf * thr - v) * 0.9 * dt
                h += rin * 0.7 * dt * (0.25 + min(1.0, v / 30) * 0.75)
                p = r = py = 0.0
                if pin > 0 and v >= TAKEOFF_V * jf:
                    on_ground, p, py = False, 0.15, 1.0
                px += sin(h) * v * dt
                pz += cos(h) * v * dt
            else:
                p = max(-1.2, min(1.2, p + pin * dt))
                if asst and pin == 0:                       # assist: self-level, gentle flare near the ground
                    p += ((-0.05 if py < 12 else 0.0) - p) * (1.5 if py < 12 else 0.6) * dt
                    if py < 15 and not dry:
                        thr += (0.2 - thr) * dt
                r += (rin * 0.8 - r) * 3.0 * dt
                h += r * 1.3 * dt
                v += ((35 + 70 * thr) * jf - sin(p) * 40 * jf - v) * dt
                if v < 40 * jf:                             # stall: nose drops
                    p = max(-1.2, p - (40 * jf - v) * 0.3 * dt)
                px += sin(h) * cos(p) * v * dt
                pz += cos(h) * cos(p) * v * dt
                py = min(500.0, py + sin(p) * v * dt)
                sink = -sin(p) * v
                if py <= 0:
                    py = 0.0
                    if sink <= sink_lim and -0.35 < p < 0.35 and abs(r) < 0.3 and v < land_v:
                        on_ground = touched = True          # good landing, anywhere!
                        p = r = thr = 0.0
                    else:
                        dead = True
                elif py < 60 and sink > sink_lim:
                    warn = "SINK"
                    if fc % 8 == 0:
                        beep(520, 40)

        if wnd and not on_ground:                           # wind + turbulence
            px += (7 * sin(tm * 0.11) + 3 * sin(tm * 0.37)) * wscale * dt
            pz += (7 * cos(tm * 0.07) + 3 * cos(tm * 0.29)) * wscale * dt
            r += (rnd() - 0.5) * 1.2 * wscale * dt
            if heli:
                vy += (rnd() - 0.5) * 6 * wscale * dt
            else:
                p += (rnd() - 0.5) * 0.5 * wscale * dt
        dist += abs(v) * dt

        if fu:                                              # fuel: burn in the air, refill on a runway/pad
            if not on_ground:
                fuel = max(0.0, fuel - (0.4 + 0.5 * (0.5 if heli else thr)) * jf * dt)
                if fuel <= 0 and not dry:
                    msg, msg_t = "ENGINE OUT", 40
                    beep(200, 200)
            elif abs(v) < 2 and fuel < 100 and (gy > 0 or (abs(px) < 8 and -62 < pz < 62)):
                fuel = min(100.0, fuel + 12 * dt)
                msg, msg_t = "REFUEL", 3
            if 0 < fuel < 15 and not warn:
                warn = "FUEL"
                if fc % 30 == 0:
                    beep(400, 60)

        ho = None if dead or py >= 130 else E.hit(px, py, pz)   # nothing is taller than 130
        if dead or ho:
            crash_scene(heli, px, py, pz, h, p, r, v, vy, ho, jet)
            return "CRASH", (tm, dist)

        if touched:
            beep(660, 120)
            rec[5] += 1                                     # lifetime landings
            q = sink / (hsink * 1.6 if heli else sink_lim)  # heli: scaled to its ground-effect cushion
            msg, msg_t = ("SMOOTH" if q < 0.25 else ("GOOD" if q < 0.6 else "HARD")), 40
            if mode == 2:                                   # LAND mode: score the landing
                if abs(px) < 8 and -62 < pz < 62:
                    score = max(10, 100 - int(0.8 * math.sqrt(px * px + pz * pz)) - int(1.2 * min(sink, 18)))
                    beep(1200, 250)
                    best = score > rec[3]
                    rec[3] = max(rec[3], score)
                    return ("BEST! " if best else "SCORE ") + str(score), (tm, dist)
                return "MISSED", (tm, dist)

        if mode == 1 and not on_ground and ring_pass(rings[0], ox, oy, oz, px, py, pz, ring_r):
            rcount += 1
            if rcount >= RINGS_N:
                beep(1200, 250)
                best = rec[ac] == 0 or tm < rec[ac]
                rec[ac] = tm if best else rec[ac]
                return ("BEST! " if best else "TIME ") + "%.1f" % tm, (tm, dist)
            beep(880, 80)
            q = rings[1]
            rings = [q, new_ring(q[0], q[1], q[2], q[4], heli)]

        # ---------------- draw ----------------
        disp.fill(0)
        if chase:
            E.set_camera(px - sin(h) * CHASE_D, py + CHASE_H, pz - cos(h) * CHASE_D, h, -0.2 + p * 0.35, r * 0.4)
        else:
            E.set_camera(px, py + (HELI_EYE if heli else EYE), pz, h, p, r)
        E.draw_world(h, 3 if lod > 0.7 else 2, lod, 1.25 if abs(p) < 0.55 else 3.0)
        for i, q in enumerate(rings):
            E.draw_ring(q[0], q[1], q[2], q[3], i == 0)
        if chase:
            E.draw_craft(heli, px, py, pz, h, p, r, fc, gy, jet)
        else:
            draw_cockpit(heli, fc)
        if heli:
            tag, side = ("PAD" if gy > 0 else "GND"), vy
        else:
            tag, side = ("RWY" if abs(px) < 8 and -62 < pz < 62 else "GND"), thr
        draw_hud(heli, py, gy, v, side, on_ground, tag, warn, ("%.1f" % tm) if mode == 1 else "")
        if mode == 1:                                       # pointer to the next ring / the runway
            tx, tz, lab = rings[0][0], rings[0][2], str(rcount) + "/" + str(RINGS_N)
        else:
            tx, tz, lab = 0, 0, (str(int(math.sqrt(px * px + pz * pz))) if mode == 2 else None)
        if lab:
            disp.drawText(lab, 20, 33, 1)
            arrow(52, 34, atan2(tx - px, tz - pz) - h, 5)
        if wnd:
            arrow(63, 34, atan2(7 * sin(tm * 0.11), 7 * cos(tm * 0.07)) - h, 4)
        if fu:                                              # fuel gauge down the left edge
            disp.drawLine(0, 30, 0, 30 - int(fuel / 5), 1)
            disp.setPixel(1, 10, 1)
        if msg_t > 0:
            msg_t -= 1
            disp.drawText(msg, 36 - len(msg) * 3, 16, 1)
        disp.update()

def run_menu(cfg, rec, first):
    """Load the menu, run it, unload it again to free RAM (falls back to saved settings)."""
    gc.collect()
    try:
        import fs_menu
        cfg = fs_menu.run(cfg, rec, first)
    except Exception as ex:
        print("menu unavailable:", ex)
    sys.modules.pop('fs_menu', None)
    gc.collect()
    return cfg

cfg, rec = load_saved()
menu = first = True
while True:
    if menu:
        cfg = run_menu(cfg, rec, first)
        first = False
        save_saved(cfg, rec)
    old = list(rec)
    msg, st = fly(cfg, rec)
    if msg == "CRASH":
        rec[6] += 1
    if rec != old:
        save_saved(cfg, rec)
    menu = True if msg == "QUIT" else not end_screen(msg, st)
