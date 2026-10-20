# fs_ui.py - HUD, map screen, end screen
import math
import time
import thumby
from fs_cfg import *
from fs_gfx import clip_line
from fs_world import find_settlements

sin = math.sin
cos = math.cos
disp = thumby.display


def draw_hud(py, v, thr, sink, on_ground, on_rwy, cockpit):
    if cockpit:
        disp.setPixel(36, 20, 1)
        disp.setPixel(33, 20, 1)
        disp.setPixel(39, 20, 1)
        disp.setPixel(36, 17, 1)
    disp.drawText(str(int(py)), 0, 0, 1)
    disp.drawText(str(int(v)), 0, 33, 1)
    n = int(thr * 25)
    disp.drawLine(71, 39, 71, 39 - n, 1)
    disp.drawLine(70, 39, 70, 39 - n, 1)
    if on_ground:
        disp.drawText("RWY" if on_rwy else "GND", 54, 0, 1)
    elif py < 60 and sink > SINK_LIMIT:
        disp.drawText("SINK", 24, 0, 1)


def toast(msg):
    disp.drawText(msg, 36 - len(msg) * 3, 16, 1)


def mpix(x, y):
    if 0 <= x < 72 and 0 <= y < 40:
        disp.setPixel(x, y, 1)


def show_map(px, pz, h):
    while thumby.buttonA.pressed() or thumby.buttonB.pressed():
        time.sleep_ms(20)
    sets = find_settlements(px - 2400, px + 2400, pz - 2400, pz + 2400)
    nc = 99999.0
    nt = 99999.0
    for kind, cx, cz, hs in sets:
        d = math.sqrt((cx - px) ** 2 + (cz - pz) ** 2)
        if kind == 0:
            if d < nc:
                nc = d
        elif d < nt:
            nt = d
    sh = sin(h)
    ch = cos(h)
    zi = 1
    pu = False
    pd = False
    while not (thumby.buttonA.pressed() and thumby.buttonB.pressed()):
        u = thumby.buttonU.pressed()
        d_ = thumby.buttonD.pressed()
        if u and not pu and zi < 2:
            zi += 1
        if d_ and not pd and zi > 0:
            zi -= 1
        pu = u
        pd = d_
        s = MAP_SCALES[zi]
        disp.fill(0)
        for kind, cx, cz, hs in sets:
            mx = int(36 + (cx - px) / s)
            my = int(20 - (cz - pz) / s)
            if kind == 0:  # city = filled square
                for i in range(3):
                    for j in range(3):
                        mpix(mx - 1 + i, my - 1 + j)
            else:          # town = hollow square
                for i in range(3):
                    for j in range(3):
                        if i != 1 or j != 1:
                            mpix(mx - 1 + i, my - 1 + j)
        c = clip_line(36 + (0 - px) / s, 20 - (-60 - pz) / s,
                      36 + (0 - px) / s, 20 - (60 - pz) / s)
        if c:
            disp.drawLine(c[0], c[1], c[2], c[3], 1)
        tx = int(36 + sh * 5)
        ty = int(20 - ch * 5)
        lx = int(36 + sin(h + 2.6) * 4)
        ly = int(20 - cos(h + 2.6) * 4)
        rx = int(36 + sin(h - 2.6) * 4)
        ry = int(20 - cos(h - 2.6) * 4)
        disp.drawLine(tx, ty, lx, ly, 1)
        disp.drawLine(tx, ty, rx, ry, 1)
        disp.drawLine(lx, ly, rx, ry, 1)
        disp.drawText("N", 66, 0, 1)
        disp.drawText("x" + str(s), 0, 0, 1)
        ct = "C" + (str(int(nc)) if nc < 9999 else "-")
        tt = "T" + (str(int(nt)) if nt < 9999 else "-")
        disp.drawText(ct, 0, 33, 1)
        disp.drawText(tt, 72 - 6 * len(tt), 33, 1)
        disp.update()
    while thumby.buttonA.pressed() or thumby.buttonB.pressed():
        time.sleep_ms(20)


def end_screen(msg):
    disp.fill(0)
    disp.drawText(msg, 36 - len(msg) * 3, 12, 1)
    disp.drawText("A:again", 15, 26, 1)
    disp.update()
    while thumby.buttonA.pressed():
        time.sleep_ms(20)
    while not thumby.buttonA.pressed():
        time.sleep_ms(20)
