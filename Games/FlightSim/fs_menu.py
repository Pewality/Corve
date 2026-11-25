# fs_menu.py - title screen, menu, help and records. Loaded by FlightSim.py only
# while the menu is showing, then unloaded so it uses no RAM during play.
import math
import time
import thumby

disp = thumby.display
sin, cos = math.sin, math.cos

ROWS = (("MODE", ("FREE", "RINGS", "LAND")), ("FLY", ("PLANE", "HELI", "JET")),
        ("AT", ("AIR", "RUNWAY", "CITY")), ("VIEW", ("CHASE", "1ST")),
        ("LVL", ("EASY", "NORMAL", "HARD")), ("WIND", ("OFF", "ON")),
        ("FUEL", ("OFF", "ON")), ("ASSIST", ("OFF", "ON")), ("SOUND", ("ON", "OFF")))
NOPT = len(ROWS)
ITEMS = NOPT + 3          # START + options + HELP + BEST

# title-screen wireframes: (vertices, edges)
PLANE = (((0, 0, 5), (-4.5, 0, -3), (4.5, 0, -3), (0, 0, -2.2), (0, 2.6, -3.4), (0, 0.9, 2)),
         ((0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (0, 5), (5, 3)))
HELI = (((0, -0.2, 3), (-1, 0, 0.4), (1, 0, 0.4), (0, 1, -0.6), (0, 0.5, -6.5), (0, 2, -7),
         (-4.5, 2, -0.4), (4.5, 2, -0.4), (0, 2, -4.9), (0, 2, 4.1), (-1.2, -1.5, 2),
         (-1.2, -1.5, -1.4), (1.2, -1.5, 2), (1.2, -1.5, -1.4)),
        ((0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (1, 10), (2, 12)))

HELP = (("PLANE / JET", "L/R  BANK", "D UP U DOWN", "A/B THROTTLE"),
        ("-- HELI --", "L/R  TURN", "U FWD D BACK", "A UP B DOWN"),
        ("-- ANY --", "A+B  SWITCH", "L+R  VIEW", "U+D  MAP"),
        ("-- MAP --", "A/B  ZOOM", "L+R  MENU", "U+D  RESUME"),
        ("-- MODES --", "RINGS: HOOPS", "LAND: RUNWAY"),
        ("-- FUEL --", "LAND AT RWY", "OR HELIPAD", "STOP: REFUEL"),
        ("-- ASSIST --", "AUTO LEVEL", "AUTO FLARE", "EASIER LAND"))

def _btn():
    return (thumby.buttonA.pressed(), thumby.buttonB.pressed(), thumby.buttonU.pressed(),
            thumby.buttonD.pressed(), thumby.buttonL.pressed(), thumby.buttonR.pressed())

def _wait():
    while any(_btn()):
        time.sleep_ms(15)

def _wire(model, ang, cx, cy, scale):
    V, E = model
    ca, sa, ct, st = cos(ang), sin(ang), cos(0.35), sin(0.35)
    pts = []
    for x, y, z in V:
        z1 = -x * sa + z * ca
        k = scale / (y * st + z1 * ct + 14)
        pts.append((int(cx + (x * ca + z * sa) * k), int(cy - (y * ct - z1 * st) * k)))
    for a, b in E:
        disp.drawLine(pts[a][0], pts[a][1], pts[b][0], pts[b][1], 1)

def title():
    """Spinning wireframe + 'press A'."""
    _wait()
    f = 0
    while not thumby.buttonA.pressed():
        disp.fill(0)
        disp.drawText("FLIGHT SIM", 6, 0, 1)
        disp.drawText("FLIGHT SIM", 7, 0, 1)
        _wire(HELI if (f // 100) & 1 else PLANE, f * 0.07, 36, 19, 52)
        if (f >> 3) & 1:
            disp.drawText("PRESS A", 15, 32, 1)
        disp.update()
        f += 1
    _wait()

def _pages(pages):
    """Read-only screens: Left/Right flips pages, A or B closes."""
    _wait()
    pg = 0
    pl = pr = False
    while True:
        disp.fill(0)
        for i, t in enumerate(pages[pg]):
            disp.drawText(t, 0, i * 9, 1)
        disp.update()
        a, b, u, d, l, r = _btn()
        if a or b:
            _wait()
            return
        pg = max(0, min(len(pages) - 1, pg + (r and not pr) - (l and not pl)))
        pl, pr = l, r
        time.sleep_ms(30)

def _help():
    _pages(HELP)

def _best(rec):
    f = lambda t: "%.1f" % t if t else "--"
    c = lambda n: str(min(n, 9999))
    _pages([("-- RINGS --", "PLANE " + f(rec[0]), "HELI  " + f(rec[1]), "JET   " + f(rec[2])),
            ("-- LAND --", "BEST " + (str(rec[3]) if rec[3] else "--")),
            ("-- STATS --", "FLIGHTS " + c(rec[4]), "LANDED  " + c(rec[5]), "CRASHED " + c(rec[6]))])

def _row(i, cfg):
    if i == 0:
        return "START"
    if i <= NOPT:
        return ROWS[i - 1][0] + ":" + ROWS[i - 1][1][cfg[i - 1]]
    return "HELP" if i == NOPT + 1 else "BEST"

def run(cfg, rec, show_title):
    """Show the menu; returns the (modified) settings list when START is chosen."""
    cfg = list(cfg)
    if show_title:
        title()
    _wait()
    sel = 0
    pu = pd = pl = pr = pa = True
    while True:
        a, b, u, d, l, r = _btn()
        sel = (sel + (d and not pd) - (u and not pu)) % ITEMS
        if 1 <= sel <= NOPT:                          # Left/Right (or A) change the option
            n = len(ROWS[sel - 1][1])
            cfg[sel - 1] = (cfg[sel - 1] + (r and not pr) - (l and not pl) + (a and not pa)) % n
        elif a and not pa:
            if sel == 0:
                _wait()
                return cfg
            _help() if sel == NOPT + 1 else _best(rec)
        pu, pd, pl, pr, pa = u, d, l, r, a
        top = max(0, min(ITEMS - 4, sel - 1))
        disp.fill(0)
        for k in range(4):
            if top + k == sel:
                disp.drawText(">", 0, 1 + k * 10, 1)
            disp.drawText(_row(top + k, cfg), 7, 1 + k * 10, 1)
        y0 = 1 + sel * 35 // (ITEMS - 1)
        disp.drawLine(71, y0, 71, y0 + 2, 1)           # scroll marker
        disp.update()
        time.sleep_ms(20)
