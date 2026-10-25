# gta_play.py - Grand Thumb Auto code (stored in small pieces; main.py loads it). Do not edit.
#@@game
import math
mode = 1
camang = ang
cx = 0.0
cy = 0.0
horv = 21
HFW = 4
HFH = 5
HT = (0.47, 0.5, 0.47, 0.46, 0.34, 0.47, 0.5, 0.46)
WD = (0.32, 0.3, 0.32, 0.36, 0.26, 0.32, 0.34, 0.42)
BARW = (0, 0, 0, 0.34, 0, 0, 0, 0, 0.42, 0.52)
def toggle():
    global mode
    mode ^= 1
    say('1ST PERSON' if mode == 0 else '3RD PERSON', 30)
def camera():
    global camang, cx, cy, horv
    z16 = int(pz * 16)
    up = min(z16 * 3 >> 4, 36)
    if mode == 0:
        camang = ang
        k = 0.12 if pcar else (0.5 if ph else 0.0)
        cx = px + cos(ang) * k
        cy = py + sin(ang) * k
        horv = 21 - up
        return (horv, 7 + z16)
    df = (ang - camang + PI) % (2 * PI) - PI
    camang += df * 0.22
    dist = 1.4 + CLEN[pcar[7]] * 0.9 if pcar else (3.2 if ph else 1.7)
    ca = cos(camang)
    sa = sin(camang)
    if z16 < 16:
        while dist > 0.35 and solid(px - ca * dist, py - sa * dist):
            dist -= 0.2
    cx = px - ca * dist
    cy = py - sa * dist
    horv = 17 - up
    return (horv, 14 + z16)
#@
def _cars(L, hor, ey, lim, ct, st):
    tk = tick
    for c in cars:
        if c is pcar and mode == 0:
            continue
        dx = c[0] - cx
        if dx > lim or dx < -lim:
            continue
        dy = c[1] - cy
        if dy > lim or dy < -lim:
            continue
        dep = dx * ct + dy * st
        if dep < 0.3 or dep > lim:
            continue
        sxc = 35.5 + (dy * ct - dx * st) * FOC / dep
        if sxc < -40 or sxc > 112:
            continue
        dd = sqrt(dx * dx + dy * dy) + 0.001
        fx = cos(c[2])
        fy = sin(c[2])
        dot = (dx * fx + dy * fy) / dd
        cr = (dx * fy - dy * fx) / dd
        k = c[7]
        wd = CWID[k]
        flip = 0
        if dot > 0.72:
            nm = '%dr' % k
            wid = wd
        elif dot < -0.72:
            nm = '%df' % k
            wid = wd
        else:
            nm = '%ds' % k
            wid = wd + (CLEN[k] - wd) * abs(cr)
            if cr < 0:
                flip = 1
        kk = FOC / dep
        yb = hor + ey * kk
        hp = int(CHT[k] * kk)
        L.append((dep, nm, sxc, yb, int(wid * kk), hp, flip, c[10]))
        if c[4] == 3 and BARW[k]:
            L.append((dep - 0.02, 'b0' if tk >> 2 & 1 else 'b1', sxc, yb - hp + 1, int(BARW[k] * kk), max(2, int(0.1 * kk)), 0, 1))
#@
def _peds(L, hor, ey, ct, st):
    tk = tick
    for p in peds:
        dx = p[0] - cx
        if dx > 21 or dx < -21:
            continue
        dy = p[1] - cy
        if dy > 21 or dy < -21:
            continue
        dep = dx * ct + dy * st
        if dep < 0.3 or dep > 20:
            continue
        sxc = 35.5 + (dy * ct - dx * st) * FOC / dep
        if sxc < -10 or sxc > 82:
            continue
        kk = FOC / dep
        yb = hor + ey * kk
        t = p[6]
        if p[5]:
            L.append((dep, 'p%d0' % t, sxc, yb, int(0.5 * kk), max(1, int(0.12 * kk)), 0, p[9]))
        else:
            fr = 0
            if p[2] or p[3]:
                fr = (tk >> (2 if t == 5 else 3)) + int(p[0] * 3) & 1
            L.append((dep, 'th' if p[7] else 'p%d%d' % (t, fr), sxc, yb, int((WD[t] + 0.04 * p[7]) * kk), int(HT[t] * kk), 0, p[9]))
    if mode == 1 and pcar is None and ph is None:
        dx = px - cx
        dy = py - cy
        dep = dx * ct + dy * st
        kk = FOC / dep
        sxc = 35.5 + (dy * ct - dx * st) * kk
        yb = hor + (ey - pz) * kk
        L.append((dep, 'me', sxc, yb, int(0.34 * kk), int(0.5 * kk), 0, 1))
        if chute:
            L.append((dep - 0.02, 'pc', sxc, yb - int(0.46 * kk), int(1.1 * kk), int(0.55 * kk), 0, 1))
#@
def _helis(L, hor, ey, ct, st):
    fr = str(tick >> 1 & 1)
    for h in hel:
        if h[5] == 2 and mode == 0:
            continue
        dx = h[0] - cx
        dy = h[1] - cy
        if dx > 40 or dx < -40 or dy > 40 or (dy < -40):
            continue
        dep = dx * ct + dy * st
        if dep < 0.3 or dep > 40:
            continue
        sxc = 35.5 + (dy * ct - dx * st) * FOC / dep
        if sxc < -40 or sxc > 112:
            continue
        dd = sqrt(dx * dx + dy * dy) + 0.001
        fx = cos(h[2])
        fy = sin(h[2])
        dot = (dx * fx + dy * fy) / dd
        cr = (dx * fy - dy * fx) / dd
        flip = 0
        wid = 0.5
        if dot > 0.72:
            nm = 'hr' + fr
        elif dot < -0.72:
            nm = 'hf' + fr
        else:
            nm = 'hs' + fr
            wid = 0.5 + 1.1 * abs(cr)
            if cr < 0:
                flip = 1
        kk = FOC / dep
        L.append((dep, nm, sxc, hor + (ey - h[4]) * kk, int(wid * kk), int(0.72 * kk), flip, 1))
#@
def _props(P, hor, ey, ct, st):
    tk = tick
    mxc = int(cx // 16)
    myc = int(cy // 16)
    for gy in range(myc - 1, myc + 2):
        for gx in range(mxc - 1, mxc + 2):
            ox = gx * 16
            oy = gy * 16
            if (ox + 8 - cx) * ct + (oy + 8 - cy) * st < -14:
                continue
            for i in range(8):
                if i < 4:
                    x = ox + (-0.5 if i & 1 else 2.5)
                    y = oy + (-0.5 if i & 2 else 2.5)
                else:
                    x = ox + (9.5, 9.5, 2.5, -0.5)[i - 4]
                    y = oy + (2.5, -0.5, 9.5, 9.5)[i - 4]
                dx = x - cx
                dy = y - cy
                if dx > 21 or dx < -21 or dy > 21 or (dy < -21):
                    continue
                dep = dx * ct + dy * st
                if dep < 0.4 or dep > 20:
                    continue
                kk = FOC / dep
                sxc = 35.5 + (dy * ct - dx * st) * kk
                if sxc < -6 or sxc > 78:
                    continue
                if i < 4:
                    s = light(gx, gy, 1 if i in (0, 3) else 0)
                    nm = 'grn' if s == 0 else 'red' if s == 2 else 'grn' if tk >> 2 & 1 else 'red'
                    hg = 1.3
                else:
                    nm = 'lamp'
                    hg = 1.5
                P.append((dep, nm, sxc, hor + ey * kk, int(0.22 * kk), int(hg * kk), 0, 1))
#@
def sprites(hor, eye16):
    th = int(camang * 1024 / (2 * PI)) & 1023
    th = th * 2 * PI / 1024
    ct = cos(th)
    st = sin(th)
    ey = eye16 / 16.0
    L = []
    P = []
    _cars(L, hor, ey, maxd / 4096.0, ct, st)
    _peds(L, hor, ey, ct, st)
    _helis(L, hor, ey, ct, st)
    _props(P, hor, ey, ct, st)
    poll()
    L.sort(key=lambda s: s[0])
    P.sort(key=lambda s: s[0])
    keep = L[:26] + P[:9]
    keep.sort(key=lambda s: -s[0])
    n = 0
    for s in keep:
        put(s[1], s[0], s[2], s[3], s[4], s[5], s[6], s[7])
        n += 1
        if n == 12 or n == 24:
            poll()
def cross(d, x, y):
    d.drawFilledRectangle(x - 5, y - 1, 11, 3, 0)
    d.drawFilledRectangle(x - 1, y - 5, 3, 11, 0)
    d.drawLine(x - 4, y, x - 2, y, 1)
    d.drawLine(x + 2, y, x + 4, y, 1)
    d.drawLine(x, y - 4, x, y - 2, 1)
    d.drawLine(x, y + 2, x, y + 4, 1)
#@
def gun_view(d):
    w = wpn
    if w == 0:
        d.drawFilledRectangle(42, 29, 22, 11, 0)
        d.drawFilledRectangle(44, 31, 16, 3, 1)
        d.drawFilledRectangle(44, 34, 5, 6, 1)
        d.drawLine(51, 32, 56, 32, 0)
        tip = 61
    elif w == 1:
        d.drawFilledRectangle(34, 28, 36, 12, 0)
        d.drawFilledRectangle(40, 31, 22, 3, 1)
        d.drawFilledRectangle(62, 32, 5, 1, 1)
        d.drawFilledRectangle(46, 34, 3, 6, 1)
        d.drawFilledRectangle(52, 34, 4, 5, 1)
        d.drawFilledRectangle(36, 32, 4, 3, 1)
        d.drawLine(44, 32, 58, 32, 0)
        tip = 68
    else:
        d.drawFilledRectangle(28, 28, 44, 12, 0)
        d.drawFilledRectangle(40, 31, 30, 2, 1)
        d.drawFilledRectangle(40, 33, 12, 3, 1)
        d.drawFilledRectangle(30, 34, 11, 4, 1)
        d.drawFilledRectangle(54, 33, 6, 2, 1)
        tip = 71
    if flash:
        d.drawLine(tip, 28, tip + 5, 34, 1)
        d.drawLine(tip, 34, tip + 5, 28, 1)
        d.drawLine(tip - 1, 31, tip + 6, 31, 1)
#@
def _hud_gun(d):
    s = WL[wpn] + str(ammo[wpn])
    w = len(s) * HFW + 1
    d.drawFilledRectangle(72 - w, HFH + 1, w, HFH + 1, 0)
    d.drawText(s, 72 - w + 1, HFH + 1, 1)
    cross(d, 36, horv)
    if hitf:
        d.drawLine(33, horv - 3, 39, horv + 3, 1)
        d.drawLine(33, horv + 3, 39, horv - 3, 1)
    if flash:
        d.drawLine(36, 31, 36, horv + 4, 1)
    if mode == 0:
        gun_view(d)
    elif flash:
        d.drawLine(38, 26, 42, 22, 1)
        d.drawLine(38, 22, 42, 26, 1)
def _hud_air(d):
    s = 'ALT ' + str(int(pz * 3)) + 'M'
    w = len(s) * HFW + 1
    d.drawFilledRectangle(72 - w, HFH + 1, w, HFH + 1, 0)
    d.drawText(s, 72 - w + 1, HFH + 1, 1)
    if ph is not None:
        s = str(int(abs(ph[3]) * 1000)) + 'KMH'
        w = len(s) * HFW + 1
        d.drawFilledRectangle(72 - w, 2 * HFH + 2, w, HFH + 1, 0)
        d.drawText(s, 72 - w + 1, 2 * HFH + 2, 1)
    elif chute and mode == 0:
        d.drawLine(6, 14, 18, 9, 1)
        d.drawLine(18, 9, 54, 9, 1)
        d.drawLine(54, 9, 66, 14, 1)
        d.drawLine(6, 14, 30, 30, 1)
        d.drawLine(66, 14, 42, 30, 1)
def _hud_car(d):
    d.drawLine(0, 39, int(abs(pcar[3]) * 80), 39, 1)
    s = str(int(abs(pcar[3]) * 483)) + 'KMH'
    w = len(s) * HFW + 1
    d.drawFilledRectangle(72 - w, HFH + 1, w, HFH + 1, 0)
    d.drawText(s, 72 - w + 1, HFH + 1, 1)
    if mode == 0:
        d.drawFilledRectangle(0, 36, 72, 4, 0)
        d.drawFilledRectangle(14, 34, 44, 2, 0)
        d.drawLine(0, 36, 14, 34, 1)
        d.drawLine(14, 34, 58, 34, 1)
        d.drawLine(58, 34, 72, 36, 1)
        d.drawLine(26, 38, 46, 38, 1)
#@
def hud(d, FW, FH):
    global HFW, HFH
    HFW = FW
    HFH = FH
    s = '$' + str(cash)
    d.drawFilledRectangle(0, 0, len(s) * FW + 1, FH + 1, 0)
    d.drawText(s, 1, 0, 1)
    d.drawFilledRectangle(0, FH + 1, 14, 4, 0)
    d.drawFilledRectangle(1, FH + 2, hp * 4, 2, 1)
    if heat > 0:
        n = 1 if heat < 450 else 2
        if not (n == 2 and tick >> 3 & 1):
            s = '*' * n
            w = len(s) * FW + 1
            d.drawFilledRectangle(72 - w, 0, w, FH + 1, 0)
            d.drawText(s, 72 - w + 1, 0, 1)
        if copd < 144:
            d.drawFilledRectangle(0 if tick >> 2 & 1 else 70, 14, 2, 10, 1)
    d.drawText('ESWN'[int((ang + PI / 4) % (2 * PI) / (PI / 2)) & 3], 34, 0, 1)
    if gun and pcar is None and ph is None and pz <= 0:
        _hud_gun(d)
    t = msg if msgt > 0 else hint
    if t:
        t = t[:70 // FW]
        w = len(t) * FW + 2
        x = (72 - w) // 2
        d.drawFilledRectangle(x, 40 - FH - 2, w, FH + 2, 0)
        d.drawText(t, x + 1, 40 - FH - 1, 1)
    if pcar is not None:
        _hud_car(d)
    elif ph is not None or pz > 0:
        _hud_air(d)
import gc, time
lmn = 0
def apply_quality():
    global MAXCAR, MAXPED
    q = QUAL[qual]
    MAXPED = q[1]
    MAXCAR = q[2]
    set_dist(q[3])

MNAMES = ('N', 'sel', 'top', 'page', 'note', 'nt', '_p', 'reset', 'labels', '_go', 'draw_map', 'draw_stats', 'step', 'cycle_weapon', 'buy_weapon', 'buy_ammo', 'heal', 'pay_cops', 'call_car', 'apt', 'mapd', 'mapc', 'mapv', 'find_ap', 'openmap', '_terrain', '_plane')
def unmenu():
    g = globals()
    for n in MNAMES:
        g.pop(n, None)
    gc.collect()
ANAMES = ('_unstick', '_air', '_fly')
def unair():
    g = globals()
    for n in ANAMES:
        g.pop(n, None)
    gc.collect()
def airfail():
    global ph, pz
    if ph is not None:
        ph[5] = 1
        ph[3] = 0.0
        ph[4] = 0.0
    ph = None
    pz = 0.0
    unair()
    say('LOW RAM', 40)
def lowmem():
    global qual, lmn
    gc.collect()
    lmn += 1
    if lmn > 20 and qual:
        qual = 0
        apply_quality()
        say('LOW RAM', 40)
#@
BTN = (thumby.buttonU.pressed, thumby.buttonD.pressed, thumby.buttonL.pressed, thumby.buttonR.pressed, thumby.buttonA.pressed, thumby.buttonB.pressed)
lat = 0
def poll():
    global lat
    m = 1
    for f in BTN:
        if f():
            lat |= m
        m <<= 1
def show():
    if FAST:
        d.display.buffer[:] = fb
    else:
        d.blit(fb, 0, 0, 72, 40, -1, 0, 0)
def draw(hor, eye):
    render(mp, cx, cy, int(camang * 1024 / 6.2831853), hor, eye)
    poll()
    sprites(hor, eye)
    poll()
    show()
    poll()
#@
def main():
    global camth, camx, camy, lat
    try:
        load('intro', globals())
        title()
    except MemoryError:
        pass
    for n in ('G5', 'big', 'title'):
        globals().pop(n, None)
    gc.collect()
    pre = []
    for n in ('menu', 'air', 'over'):
        try:
            load(n, globals())
            pre.append(n)
        except MemoryError:
            gc.collect()
    pm = 'menu' in pre
    pa = 'air' in pre
    po = 'over' in pre
    gc.collect()
    apply_quality()
    start()
    sync(px, py, 16)
    tms = time.ticks_ms
    tdf = time.ticks_diff
    t0 = tms()
    sa = sb = sl = time.ticks_add(t0, -100000)
    aprev = bprev = lprev = True
    wa = wb = 0
    bh = 0
    lock = True
    menu_on = False
    while True:
        poll()
        s = lat
        lat = 0
        now = tms()
        ft = tdf(now, t0)
        t0 = now
        w = ft + ft if ft > 50 else 100
        dl = 3 if ft < 60 else 2
        bu = s & 1
        bd = s >> 1 & 1
        bl = s >> 2 & 1
        br = s >> 3 & 1
        bA = s >> 4 & 1
        bB = s >> 5 & 1
        if bA:
            sa = now
        if bB:
            sb = now
        if bl:
            sl = now
        ae = bA and (not aprev)
        be = bB and (not bprev)
        le = bl and (not lprev)
        aprev = bA
        bprev = bB
        lprev = bl
        bh = bh + 1 if bB else 0
        cam = act = False
        if lock:
            if not bA and (not bB):
                lock = False
        elif (ae and (bB or tdf(now, sb) < w)) or (be and (bA or tdf(now, sa) < w)):
            menu_on = not menu_on
            if menu_on:
                try:
                    if not pm:
                        load('menu', globals())
                    reset()
                except MemoryError:
                    menu_on = False
                    if not pm:
                        unmenu()
            elif not pm:
                unmenu()
            lock = True
            wa = wb = 0
        elif (not menu_on) and ((ae and (bl or tdf(now, sl) < w)) or (le and (bA or tdf(now, sa) < w))):
            try:
                if not pm:
                    load('menu', globals())
                reset()
                openmap()
                menu_on = True
            except MemoryError:
                if not pm:
                    unmenu()
            lock = True
            wa = wb = 0
        else:
            if ae:
                wa = dl
            if be:
                wb = dl
            if wa:
                wa -= 1
                cam = wa == 0
            if wb:
                wb -= 1
                act = wb == 0
        if menu_on:
            wa = wb = 0
            if step(d, FW, FH, bu, bd, bl, br, bA, bB, lock):
                menu_on = False
                if not pm:
                    unmenu()
                lock = True
            d.update()
            continue
        if cam:
            toggle()
        want = ph is not None or pz > 0
        if (not pa) and want != ('_fly' in globals()):
            if want:
                try:
                    load('air', globals())
                except MemoryError:
                    airfail()
            else:
                unair()
        try:
            update(bu, bd, bl, br, bB, act, bh > 4 and (not bA))
            sx, sy = rebase(px, py)
            if sx or sy:
                shift(sx, sy)
            sync(px, py)
            hor, eye = camera()
            camx = cx
            camy = cy
            camth = camang
            draw(hor, eye)
            hud(d, FW, FH)
            poll()
        except MemoryError:
            lowmem()
            continue
        if dead:
            try:
                if not po:
                    load('over', globals())
                gameover()
                newgame()
            except MemoryError:
                lowmem()
                continue
            if not po:
                for n in ('gameover', 'newgame'):
                    globals().pop(n, None)
            gc.collect()
            sync(px, py, 16)
            lock = True
            wa = wb = 0
            continue
        d.update()
        if tick & 31 == 0:
            gc.collect()
#@@intro
G5 = {'G': (14, 17, 16, 23, 17, 17, 14), 'R': (30, 17, 17, 30, 20, 18, 17), 'A': (14, 17, 17, 31, 17, 17, 17), 'N': (17, 25, 25, 21, 19, 19, 17), 'D': (30, 17, 17, 17, 17, 17, 30), 'T': (31, 4, 4, 4, 4, 4, 4), 'H': (17, 17, 17, 31, 17, 17, 17), 'U': (17, 17, 17, 17, 17, 17, 14), 'M': (17, 27, 21, 21, 17, 17, 17), 'B': (30, 17, 17, 30, 17, 17, 30), 'O': (14, 17, 17, 17, 17, 17, 14), 'W': (17, 17, 17, 21, 21, 27, 17), 'S': (14, 17, 16, 14, 1, 17, 14), 'E': (31, 16, 16, 30, 16, 16, 31)}
def big(text, x, y, s):
    for ch in text:
        g = G5.get(ch)
        if g:
            for r in range(7):
                row = g[r]
                for q in range(5):
                    if row & 16 >> q:
                        if s == 1:
                            d.setPixel(x + q, y + r, 1)
                        else:
                            d.drawFilledRectangle(x + q * s, y + r * s, s, s, 1)
        x += 6 * s
#@
def title():
    n = 0
    hs = [2 + H(i, 3, 1) % 3 for i in range(12)]
    while True:
        d.fill(0)
        big('GRAND THUMB', 3, 3, 1)
        big('AUTO', 13, 13, 2)
        d.drawLine(3, 28, 68, 28, 1)
        if n >> 3 & 1:
            d.drawText('PRESS A', (72 - 7 * FW) // 2, 29, 1)
        for i in range(12):
            d.drawFilledRectangle(i * 6, 40 - hs[i], 5, hs[i], 1)
        d.drawFilledRectangle(n * 2 % 90 - 8, 38, 5, 2, 0)
        d.drawFilledRectangle(n * 2 % 90 - 7, 37, 3, 1, 1)
        d.update()
        n += 1
        if n > 8 and (thumby.buttonA.pressed() or thumby.buttonB.pressed()):
            break
    pages = (('PAD  MOVE', 'A    VIEW', 'B    ACTION', 'A+B  MENU'), ('CAR   ENTER', 'SHOP  ROB', 'NPC   STEAL', 'GUN   FIRE'), ('L+A   MAP', 'AIRPORT FLY', 'B  JUMP OUT', 'CHUTE SAFE'))
    pitch = FH + 3
    y0 = 2 if FH <= 5 else 1
    prev = True
    for pg in pages:
        n = 0
        while True:
            d.fill(0)
            for i in range(4):
                d.drawText(pg[i], 6, y0 + i * pitch, 1)
            d.drawRectangle(0, 0, 72, 40, 1)
            d.update()
            n += 1
            now = thumby.buttonA.pressed() or thumby.buttonB.pressed()
            if now and (not prev) and (n > 3):
                break
            prev = now
#@@menu
import math
N = 12
sel = 0
top = 0
page = 0
note = ''
nt = 0
_p = [False] * 6
apt = None
mapd = False
mapc = bytearray(360)
mapv = False
def find_ap():
    bx = int(px // 16)
    by = int(py // 16)
    best = None
    bd = 1e9
    for gy in range(by - 12, by + 13):
        for gx in range(bx - 12, bx + 13):
            if is_ap(gx + OX, gy + OY):
                x = gx * 16 + 11.5
                y = gy * 16 + 13.5
                dd = (x - px) ** 2 + (y - py) ** 2
                if dd < bd:
                    bd = dd
                    best = (x, y)
    return best
def openmap():
    global page, mapd
    page = 1
    mapd = True
def reset():
    global sel, top, page, note, nt, apt, mapd, mapv
    mapv = False
    apt = find_ap()
    mapd = False
    sel = 0
    top = 0
    page = 0
    note = ''
    nt = 0
    for i in range(6):
        _p[i] = True
def labels():
    w = wpn
    buy = 'ALL OWNED'
    for i in (1, 2):
        if not owned[i]:
            buy = WN[i] + ' $' + str(WP[i])
            break
    return ('GUN ON' if gun else 'GUN OFF', WN[w] + ' ' + str(ammo[w]), 'AMMO $' + str(WA[w][1]), buy, 'HEAL $25', 'CAR $60', 'COPS $' + str(40 if heat < 450 else 80) if heat > 0 else 'COPS --', 'MAP', 'STATS', 'VIEW ' + ('1ST' if mode == 0 else '3RD'), 'QUAL ' + QUAL[qual][0], 'CLOSE')
#@
def _go(i):
    global gun, msgt, note, nt, page, qual
    if i == 0:
        gun = not gun
        note = 'GUN READY' if gun else 'HOLSTERED'
    elif i == 1:
        note = cycle_weapon()
    elif i == 2:
        note = buy_ammo()
    elif i == 3:
        note = buy_weapon()
    elif i == 4:
        note = heal()
    elif i == 5:
        note = call_car()
    elif i == 6:
        note = pay_cops()
    elif i == 7:
        page = 1
        return False
    elif i == 8:
        page = 2
        return False
    elif i == 9:
        toggle()
        msgt = 0
        note = 'VIEW CHANGED'
    elif i == 10:
        qual = (qual + 1) % 3
        apply_quality()
        note = 'QUALITY ' + QUAL[qual][0]
    else:
        return True
    nt = 40
    return False
#@
def _terrain(d):
    tx0 = int(px // 1) - 36
    ty0 = int(py // 1) - 20
    m = mp
    bxl = [tx0 + sx >> 4 for sx in range(72)]
    okr = None
    for sy in range(40):
        ty = ty0 + sy
        if okr is None or ty & 15 == 0:
            by = ty >> 4
            okr = [have[(by & 3) * 4 + (bx & 3)] == (bx, by) for bx in bxl]
        row = (ty & 63) << 6
        for sx in range(72):
            if not okr[sx]:
                if sx + sy & 3 == 0:
                    d.setPixel(sx, sy, 1)
                continue
            t = m[row | tx0 + sx & 63]
            if t > 127:
                if (t & 31) >= 6 or sx + sy & 1:
                    d.setPixel(sx, sy, 1)
            elif t & 15 == 2:
                if sx & 1 and sy & 1:
                    d.setPixel(sx, sy, 1)
def _plane(d, x, y, c):
    d.drawLine(x, y - 3, x, y + 3, c)
    d.drawLine(x - 3, y, x + 3, y, c)
    d.drawLine(x - 1, y + 3, x + 1, y + 3, c)
    d.drawLine(x - 2, y + 1, x + 2, y + 1, c)
def draw_map(d, FW, FH):
    global mapv
    buf = d.display.buffer if FAST else None
    if buf is not None and mapv:
        buf[:] = mapc
    else:
        d.drawFilledRectangle(0, 0, 72, 40, 0)
        _terrain(d)
        if buf is not None:
            mapc[:] = buf
            mapv = True
    blink = tick >> 2 & 1
    tx0 = int(px // 1) - 36
    ty0 = int(py // 1) - 20
    for c in cars:
        x = int(c[0] // 1) - tx0
        y = int(c[1] // 1) - ty0
        if 1 <= x < 70 and 1 <= y < 38 and (c[4] != 3 or blink):
            d.drawFilledRectangle(x, y, 2, 2, 1)
    for q in peds:
        x = int(q[0] // 1) - tx0
        y = int(q[1] // 1) - ty0
        if 1 <= x < 71 and 1 <= y < 39 and (not q[5]) and (blink or q[7]):
            d.setPixel(x, y, 1)
    if apt:
        dx = apt[0] - px
        dy = apt[1] - py
        ax = 36 + int(dx)
        ay = 20 + int(dy)
        far = not (6 <= ax < 66 and 6 <= ay < 34)
        if far:
            t = 9999.0
            if dx > 0:
                t = 30.0 / dx
            elif dx < 0:
                t = 30.0 / -dx
            if dy > 0:
                t = min(t, 14.0 / dy)
            elif dy < 0:
                t = min(t, 14.0 / -dy)
            ax = 36 + int(dx * t)
            ay = 20 + int(dy * t)
        vx = ax - 36
        vy = ay - 20
        ln = math.sqrt(vx * vx + vy * vy) + 0.01
        for i in range(8, int(ln) - 5, 3):
            d.setPixel(36 + int(vx * i / ln), 20 + int(vy * i / ln), 1)
        on = tick >> 3 & 1
        d.drawFilledRectangle(ax - 5, ay - 5, 11, 11, 0)
        d.drawRectangle(ax - 5, ay - 5, 11, 11, 1)
        if on:
            d.drawFilledRectangle(ax - 4, ay - 4, 9, 9, 1)
        _plane(d, ax, ay, 1 - on)
        s = str(int(math.sqrt(dx * dx + dy * dy) * 3)) + 'M'
        d.drawFilledRectangle(1, 1, len(s) * FW + 2, FH + 2, 0)
        d.drawText(s, 2, 2, 1)
        d.drawFilledRectangle(1, 40 - FH - 3, 7 * FW + 2, FH + 2, 0)
        d.drawText('AIRPORT'[:68 // FW], 2, 40 - FH - 2, 1)
    else:
        d.drawFilledRectangle(1, 40 - FH - 3, 10 * FW + 2, FH + 2, 0)
        d.drawText('NO AIRPORT'[:68 // FW], 2, 40 - FH - 2, 1)
    d.drawFilledRectangle(36 - 4, 20 - 4, 9, 9, 0)
    tx = 36 + int(math.cos(ang) * 5)
    ty = 20 + int(math.sin(ang) * 5)
    ex = 36 + int(math.cos(ang + 2.5) * 3.5)
    ey = 20 + int(math.sin(ang + 2.5) * 3.5)
    fx = 36 + int(math.cos(ang - 2.5) * 3.5)
    fy = 20 + int(math.sin(ang - 2.5) * 3.5)
    d.drawLine(tx, ty, ex, ey, 1)
    d.drawLine(tx, ty, fx, fy, 1)
    d.drawLine(ex, ey, fx, fy, 1)
    d.drawFilledRectangle(65, 1, FW + 2, FH + 2, 0)
    d.drawText('N', 66, 2, 1)
    d.drawRectangle(0, 0, 72, 40, 1)
#@
def draw_stats(d, FW, FH):
    pitch = FH + 1
    s = tick // 30
    rows = ('TIME %d:%02d' % (s // 60, s % 60), 'RAM ' + str(gc.mem_free() // 1024) + 'K', 'STOLEN ' + str(n_steal), 'ROBBED ' + str(n_rob), 'KILLS ' + str(n_kill), 'JACKED ' + str(n_jack))
    d.drawFilledRectangle(0, 0, 72, 40, 0)
    d.drawRectangle(0, 0, 72, 40, 1)
    for i in range(min(6, 38 // pitch)):
        d.drawText(rows[i], 5, 2 + i * pitch, 1)
#@
def step(d, FW, FH, u, dn, l, r, a, b, lock):
    global sel, top, page, nt
    cur = (u, dn, l, r, a, b)
    ed = [cur[i] and (not _p[i]) for i in range(6)]
    for i in range(6):
        _p[i] = cur[i]
    close = False
    if nt > 0:
        nt -= 1
    if page:
        if not lock and (ed[2] or ed[3] or ed[4] or ed[5]):
            page = 0
            if mapd:
                return True
        if page == 1:
            draw_map(d, FW, FH)
        elif page == 2:
            draw_stats(d, FW, FH)
        return False
    if not lock:
        if ed[0]:
            sel = (sel - 1) % N
        if ed[1]:
            sel = (sel + 1) % N
        if ed[2] or ed[3] or ed[4] or ed[5]:
            close = _go(sel)
    pitch = FH + 2
    vis = 4 if FH <= 5 else 3
    if sel < top:
        top = sel
    if sel >= top + vis:
        top = sel - vis + 1
    mx = (68 - 10) // FW
    d.drawFilledRectangle(0, 0, 72, 40, 0)
    d.drawRectangle(0, 0, 72, 40, 1)
    d.drawText((note if nt > 0 else 'MENU $' + str(cash))[:mx], 4, 2, 1)
    d.drawLine(2, pitch + 1, 69, pitch + 1, 1)
    items = labels()
    for i in range(vis):
        j = top + i
        y = pitch + 3 + i * pitch
        if j == sel:
            d.drawText('>', 3, y, 1)
        d.drawText(items[j][:mx], 10, y, 1)
    if top > 0:
        d.drawLine(67, pitch + 4, 67, pitch + 4, 1)
        d.drawLine(66, pitch + 5, 68, pitch + 5, 1)
    if top + vis < N:
        d.drawLine(67, 37, 67, 37, 1)
        d.drawLine(66, 36, 68, 36, 1)
    return close
#@
def cycle_weapon():
    global wpn
    for _ in range(3):
        wpn = (wpn + 1) % 3
        if owned[wpn]:
            break
    return WN[wpn]
def buy_weapon():
    global cash, wpn
    for w in (1, 2):
        if not owned[w]:
            if cash < WP[w]:
                return 'NEED $' + str(WP[w])
            cash -= WP[w]
            owned[w] = True
            ammo[w] += WA[w][0]
            wpn = w
            return WN[w] + ' BOUGHT'
    return 'ALL OWNED'
def buy_ammo():
    global cash
    n, p = WA[wpn]
    if cash < p:
        return 'NEED $' + str(p)
    cash -= p
    ammo[wpn] += n
    return '+' + str(n) + ' AMMO'
def heal():
    global cash, hp
    if hp >= 3:
        return 'HP FULL'
    if cash < 25:
        return 'NEED $25'
    cash -= 25
    hp += 1
    return 'HP +1'
def pay_cops():
    global cash, heat
    if heat <= 0:
        return 'NOT WANTED'
    p = 40 if heat < 450 else 80
    if cash < p:
        return 'NEED $' + str(p)
    cash -= p
    heat = 0
    calm_cops()
    return 'COPS PAID'
#@
def call_car():
    global cash
    if cash < 60:
        return 'NEED $60'
    tx = int(px // 1)
    ty = int(py // 1)
    for r in range(1, 8):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx > -r and dx < r and (dy > -r) and (dy < r):
                    continue
                x = tx + dx
                y = ty + dy
                lx = x & 15
                ly = y & 15
                if mp[(y & 63) << 6 | x & 63] >= 128:
                    continue
                if lx < 2 and ly >= 2:
                    cx = (x >> 4) * 16 + (0.5 if lx == 0 else 1.5)
                    cy = y + 0.5
                    dd = 1 if lx == 0 else 3
                elif ly < 2 and lx >= 2:
                    cx = x + 0.5
                    cy = (y >> 4) * 16 + (0.5 if ly == 0 else 1.5)
                    dd = 2 if ly == 0 else 0
                else:
                    continue
                for o in cars:
                    if abs(o[0] - cx) < 1.8 and abs(o[1] - cy) < 1.8:
                        break
                else:
                    cash -= 60
                    newcar(cx, cy, dd * PI / 2, 0.0, 2, dd, 0.1, 5, 1)
                    return 'CAR READY'
    return 'NO ROAD NEAR'
#@@over
def gameover():
    global dead
    ok = True
    try:
        load('intro', globals())
    except MemoryError:
        ok = False
    buf = d.display.buffer if FAST else None
    bg = bytearray(buf) if FAST else None
    tn = {0: (180, 120), 5: (110, 160), 18: (60, 600)}
    cs = dmsg[:72 // FW]
    ms = ('$' + str(cash) + ' KEPT')[:72 // FW]
    for t in range(110):
        if t in tn:
            try:
                thumby.audio.play(tn[t][0], tn[t][1])
            except Exception:
                pass
        if FAST:
            sh = 0
            if t < 14 or (17 < t < 36 and (t - 18) % 3 == 0):
                am = 2 if t < 14 else 1
                sh = random.getrandbits(3) % (2 * am + 1) - am
            for pg in range(5):
                o = pg * 72
                if sh > 0:
                    buf[o:o + sh] = bytes(sh)
                    buf[o + sh:o + 72] = bg[o:o + 72 - sh]
                elif sh < 0:
                    buf[o:o + 72 + sh] = bg[o - sh:o + 72]
                    buf[o + 72 + sh:o + 72] = bytes(-sh)
                else:
                    buf[o:o + 72] = bg[o:o + 72]
            if t < 3:
                for i in range(360):
                    buf[i] ^= 255
            elif t >= 8:
                m0 = 170
                m1 = 85
                for i in range(360):
                    buf[i] &= m1 if i & 1 else m0
        bh = min(FH + 2, t // 2)
        if bh:
            d.drawFilledRectangle(0, 0, 72, bh, 0)
            d.drawFilledRectangle(0, 40 - bh, 72, bh, 0)
        if t >= 10:
            d.drawText(cs, (72 - len(cs) * FW) // 2, 1, 1)
            d.drawText(ms, (72 - len(ms) * FW) // 2, 40 - FH - 1, 1)
        h = min(18, max(0, (t - 12) * 3))
        if h:
            y0 = 20 - h // 2
            d.drawFilledRectangle(0, y0, 72, h, 0)
            d.drawLine(0, y0, 71, y0, 1)
            d.drawLine(0, y0 + h - 1, 71, y0 + h - 1, 1)
        n = min(6, (t - 18) // 3 + 1) if t >= 18 else 0
        if n:
            if ok:
                big('WASTED'[:n], 1, 13, 2)
            else:
                d.drawText('WASTED'[:n], 24, 17, 1)
        d.update()
    for n in ('G5', 'big', 'title'):
        globals().pop(n, None)
    dead = 0
    gc.collect()
#@
def newgame():
    global px, py, ang, pcar, heat, hp, gun, wpn, fcool, flash, hitf, copd, rkey, hint
    global camx, camy, camth, camang, n_steal, n_rob, n_kill, n_jack, OX, OY, _key, _pend, dead
    global ph, pz, pvz, chute, fall
    del cars[:]
    del hel[:]
    ph = None
    pz = pvz = 0.0
    chute = False
    fall = 0
    del peds[:]
    while robbed:
        robbed.pop()
    owned[:] = [True, False, False]
    ammo[:] = [12, 0, 0]
    have[:] = [None] * 16
    OX = 0
    OY = 0
    _key = None
    _pend = False
    px = 2.5
    py = 6.5
    ang = -PI / 2
    camang = ang
    camx = camy = camth = 0.0
    pcar = None
    heat = 0
    hp = 3
    gun = False
    wpn = 0
    fcool = flash = hitf = 0
    copd = 9999.0
    n_steal = n_rob = n_kill = n_jack = 0
    rkey = None
    hint = ''
    dead = 0
    start()
#@@air
def _unstick():
    global px, py
    tx = int(px // 1)
    ty = int(py // 1)
    for r in range(1, 5):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x = tx + dx + 0.5
                y = ty + dy + 0.5
                if not solid(x, y) and (not blocked(x, y, 0.25)):
                    px = x
                    py = y
                    return
#@
def _air(bU, bD, bL, bR):
    global pz, pvz, px, py, ang, chute, fall
    fall += 1
    if fall < 24:
        pvz = min(0.22, pvz + 0.012)
    else:
        if not chute:
            chute = True
            say('PARACHUTE!', 40)
        pvz += (0.05 - pvz) * 0.1
    pz -= pvz
    if bL:
        ang -= 0.05
    if bR:
        ang += 0.05
    if chute:
        s = 0.045 if bU else (-0.02 if bD else 0.0)
        if s:
            nx = px + cos(ang) * s
            ny = py + sin(ang) * s
            if pz >= _hgt(nx, py) or not solid(nx, py):
                px = nx
            if pz >= _hgt(px, ny) or not solid(px, ny):
                py = ny
    if solid(px, py) and pz < _hgt(px, py):
        _unstick()
    if pz <= 0:
        pz = 0.0
        pvz = 0.0
        fall = 0
        chute = False
        if solid(px, py):
            _unstick()
        say('SAFE LANDING', 60)
#@
def _fly(bU, bD, bL, bR, act):
    global ang, px, py, pz, hint, ph, chute, fall, pvz
    h = ph
    spd = h[3]
    if h[4] > 1.0:
        if bU:
            spd += 0.004
        elif bD:
            spd -= 0.006
        else:
            spd *= 0.985
        if spd > 0.15:
            spd = 0.15
        elif spd < -0.04:
            spd = -0.04
        h[2] += (int(bR) - int(bL)) * 0.045
    else:
        spd *= 0.9
    h[3] = spd
    h[0] += cos(h[2]) * spd
    h[1] += sin(h[2]) * spd
    h[4] += max(-0.06, min(0.05, _tz(h[0], h[1], h[2]) - h[4]))
    px = h[0]
    py = h[1]
    ang = h[2]
    pz = h[4]
    hint = 'B:JUMP' if pz > 1.2 else 'B:EXIT'
    if act:
        ph = None
        if pz > 1.2:
            h[5] = 0
            h[3] = 0.08
            h[6] = 60
            pvz = 0.0
            fall = 0
            chute = False
            say('JUMP!', 25)
        else:
            h[5] = 1
            h[3] = 0.0
            h[4] = 0.0
            pz = 0.0
            a = h[2] + 1.57
            px = h[0] + cos(a) * 1.4
            py = h[1] + sin(a) * 1.4
            if blocked(px, py, 0.25):
                px = h[0]
                py = h[1]
