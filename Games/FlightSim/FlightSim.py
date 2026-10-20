# Thumby Flight Sim v3 - wireframe 3D, MicroPython
#
# Files (keep them all in the same folder, e.g. /Games/FlightSim/):
#   FlightSim.py  this file: the game loop and flight model
#   fs_cfg.py     all settings (speed, landing rules, view distance...)
#   fs_gfx.py     camera + fast line drawing
#   fs_world.py   random towns/cities/mountains/towers + collision
#   fs_plane.py   the plane model and its shadow (third-person view)
#   fs_ui.py      HUD, map screen, end screen
#
# Controls:
#   D-pad Left/Right : bank (turns the plane, auto-levels when released)
#   D-pad Down       : nose up      D-pad Up : nose down  [INVERT_PITCH]
#   A / B            : throttle up / down
#   A + B together   : open / close the MAP (Up/Down zooms)
#   Left + Right     : switch CHASE (3rd person) / COCKPIT view
#
# Land ANYWHERE with a gentle sink rate, wings level, not too fast
# (watch the SINK warning; the plane's shadow helps in chase view).
# On the ground: A = throttle, Left/Right = steer, pull back at 50+ to
# take off again. Mountains, towers and buildings are solid.

import sys
for _p in ("/Games/FlightSim", ""):
    if _p not in sys.path:
        sys.path.append(_p)

import time
import math
import thumby
from fs_cfg import *
import fs_gfx as G
import fs_world as W
from fs_gfx import make_view
from fs_plane import draw_plane
from fs_ui import draw_hud, show_map, end_screen, toast

sin = math.sin
cos = math.cos
disp = thumby.display
disp.setFPS(FPS)


def fly(px=0.0, py=80.0, pz=-320.0, h=0.0, p=0.0, v=70.0):
    r = 0.0
    thr = 0.5
    on_ground = False
    fc = 0
    chase = START_CHASE
    toast_t = 0
    prev_lr = False
    lod = 1.0
    W.regen_now(px, pz)
    last = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        raw = time.ticks_diff(now, last) / 1000
        last = now
        dt = 0.1 if raw > 0.1 else raw
        fc += 1

        # adaptive detail: slow frame -> draw less, fast frame -> draw more
        if raw > 1.2 / FPS:
            lod = lod - 0.04 if lod > LOD_MIN + 0.04 else LOD_MIN
        elif raw < 1.1 / FPS and lod < 1.0:
            lod += 0.01

        a = thumby.buttonA.pressed()
        b = thumby.buttonB.pressed()
        if a and b:
            show_map(px, pz, h)
            last = time.ticks_ms()
            continue
        l = thumby.buttonL.pressed()
        rt = thumby.buttonR.pressed()
        lr = l and rt
        if lr and not prev_lr:
            chase = not chase
            toast_t = 25
        prev_lr = lr

        pin = (1 if thumby.buttonD.pressed() else 0) - (1 if thumby.buttonU.pressed() else 0)
        if INVERT_PITCH:
            pin = -pin
        rin = (1 if rt else 0) - (1 if l else 0)
        thr += ((1 if a else 0) - (1 if b else 0)) * 0.6 * dt
        thr = 0.0 if thr < 0 else (1.0 if thr > 1 else thr)

        W.update(px, pz)

        sink = 0.0
        if on_ground:
            v += (110 * thr - v) * 0.9 * dt
            h += rin * 0.7 * dt * (0.25 + min(1.0, v / 30) * 0.75)
            p = 0.0
            r = 0.0
            py = 0.0
            if pin > 0 and v >= TAKEOFF_SPEED:
                on_ground = False
                p = 0.15
                py = 1.0
            px += sin(h) * v * dt
            pz += cos(h) * v * dt
        else:
            p += pin * 1.0 * dt
            r += (rin * 0.8 - r) * 3.0 * dt
            h += r * 1.3 * dt
            target = 35 + 70 * thr - sin(p) * 40
            v += (target - v) * 1.0 * dt
            if v < 40:  # stall
                p -= (40 - v) * 0.3 * dt
            p = -1.2 if p < -1.2 else (1.2 if p > 1.2 else p)
            cp = cos(p)
            px += sin(h) * cp * v * dt
            pz += cos(h) * cp * v * dt
            py += sin(p) * v * dt
            if py > 500:
                py = 500.0
            sink = -sin(p) * v
            if py <= 0:
                py = 0.0
                if (sink <= SINK_LIMIT and -0.35 < p < 0.35
                        and abs(r) < 0.3 and v < LAND_MAX_SPEED):
                    on_ground = True  # good landing, anywhere!
                    p = 0.0
                    r = 0.0
                    thr = 0.0
                else:
                    return "CRASH"

        if W.hit(px, py, pz):
            return "CRASH"

        # ---- draw ----
        disp.fill(0)
        G.reset_lines()
        inv = 1.0 / (lod * lod)
        gn = 3 if lod > 0.7 else 2
        ap = p if p > 0 else -p
        ck = 1.25 if ap < 0.55 else 3.0
        if chase:
            cx = px - sin(h) * CHASE_D
            cz = pz - cos(h) * CHASE_D
            cy = py + CHASE_H
            tf = make_view(cx, cy, cz, h, -0.20 + p * 0.35, r * 0.4)
            W.draw_world(tf, cx, cz, h, fc, inv, gn, ck)
            draw_plane(tf, px, py, pz, h, p, r)
        else:
            tf = make_view(px, py + EYE, pz, h, p, r)
            W.draw_world(tf, px, pz, h, fc, inv, gn, ck)
        draw_hud(py, v, thr, sink, on_ground, abs(px) < 8 and -62 < pz < 62, not chase)
        if toast_t > 0:
            toast_t -= 1
            toast("CHASE" if chase else "COCKPIT")
        if DEBUG:
            disp.drawText(str(G.nlines), 30, 33, 1)
        disp.update()


while True:
    end_screen(fly())
