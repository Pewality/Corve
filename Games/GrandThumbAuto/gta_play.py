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
    if mode == 0:
        camang = ang
        k = 0.12 if pcar else 0.0
        cx = px + cos(ang) * k
        cy = py + sin(ang) * k
        horv = 21
        return (21, 7)
    df = (ang - camang + PI) % (2 * PI) - PI
    camang += df * 0.22
    dist = 1.4 + CLEN[pcar[7]] * 0.9 if pcar else 1.7
    ca = cos(camang)
    sa = sin(camang)
    while dist > 0.35 and solid(px - ca * dist, py - sa * dist):
        dist -= 0.2
    cx = px - ca * dist
    cy = py - sa * dist
    horv = 17
    return (17, 14)
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
    if mode == 1 and pcar is None:
        dx = px - cx
        dy = py - cy
        dep = dx * ct + dy * st
        kk = FOC / dep
        L.append((dep, 'me', 35.5 + (dy * ct - dx * st) * kk, hor + ey * kk, int(0.34 * kk), int(0.5 * kk), 0, 1))
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
    _props(P, hor, ey, ct, st)
    L.sort(key=lambda s: s[0])
    P.sort(key=lambda s: s[0])
    keep = L[:26] + P[:9]
    keep.sort(key=lambda s: -s[0])
    for s in keep:
        put(s[1], s[0], s[2], s[3], s[4], s[5], s[6], s[7])
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
def _hud_car(d):
    d.drawLine(0, 39, int(abs(pcar[3]) * 80), 39, 1)
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
    if gun and pcar is None:
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
import gc
def apply_quality():
    global MAXCAR, MAXPED
    q = QUAL[qual]
    MAXPED = q[1]
    MAXCAR = q[2]
    set_dist(q[3])

MNAMES = ('N', 'sel', 'top', 'page', 'note', 'nt', '_p', 'reset', 'labels', '_go', 'draw_map', 'draw_stats', 'step', 'cycle_weapon', 'buy_weapon', 'buy_ammo', 'heal', 'pay_cops', 'call_car')
def unmenu():
    g = globals()
    for n in MNAMES:
        g.pop(n, None)
    gc.collect()
def lowmem():
    global qual
    gc.collect()
    if qual:
        qual = 0
        apply_quality()
    del peds[12:]
    say('LOW RAM', 40)
#@
def show():
    if FAST:
        d.display.buffer[:] = fb
    else:
        d.blit(fb, 0, 0, 72, 40, -1, 0, 0)
def draw(hor, eye):
    render(mp, cx, cy, int(camang * 1024 / 6.2831853), hor, eye)
    sprites(hor, eye)
    show()
#@
def main():
    global camth, camx, camy
    try:
        load('intro', globals())
        title()
    except MemoryError:
        pass
    for n in ('G5', 'big', 'title'):
        globals().pop(n, None)
    gc.collect()
    apply_quality()
    start()
    sync(px, py, 16)
    pu = thumby.buttonU.pressed
    pd = thumby.buttonD.pressed
    pl = thumby.buttonL.pressed
    pr = thumby.buttonR.pressed
    pa = thumby.buttonA.pressed
    pb = thumby.buttonB.pressed
    aprev = bprev = True
    wa = wb = 0
    bh = 0
    lock = True
    menu_on = False
    while True:
        bA = pa()
        bB = pb()
        ae = bA and (not aprev)
        be = bB and (not bprev)
        aprev = bA
        bprev = bB
        bh = bh + 1 if bB else 0
        cam = act = False
        if lock:
            if not bA and (not bB):
                lock = False
        elif bA and bB and (ae or be):
            menu_on = not menu_on
            if menu_on:
                try:
                    load('menu', globals())
                    reset()
                except MemoryError:
                    menu_on = False
                    unmenu()
                    say('LOW RAM', 40)
            else:
                unmenu()
            lock = True
            wa = wb = 0
        else:
            if ae:
                wa = 3
            if be:
                wb = 3
            if wa:
                wa -= 1
                cam = wa == 0
            if wb:
                wb -= 1
                act = wb == 0
        if menu_on:
            wa = wb = 0
            if step(d, FW, FH, pu(), pd(), pl(), pr(), bA, bB, lock):
                menu_on = False
                unmenu()
                lock = True
            d.update()
            continue
        if cam:
            toggle()
        try:
            update(pu(), pd(), pl(), pr(), bB, act, bh > 4 and (not bA))
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
        except MemoryError:
            lowmem()
            continue
        d.update()
        if tick & 31 == 0:
            gc.collect()
#@@intro
G5 = {'G': (14, 17, 16, 23, 17, 17, 14), 'R': (30, 17, 17, 30, 20, 18, 17), 'A': (14, 17, 17, 31, 17, 17, 17), 'N': (17, 25, 25, 21, 19, 19, 17), 'D': (30, 17, 17, 17, 17, 17, 30), 'T': (31, 4, 4, 4, 4, 4, 4), 'H': (17, 17, 17, 31, 17, 17, 17), 'U': (17, 17, 17, 17, 17, 17, 14), 'M': (17, 27, 21, 21, 17, 17, 17), 'B': (30, 17, 17, 30, 17, 17, 30), 'O': (14, 17, 17, 17, 17, 17, 14)}
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
    pages = (('PAD  MOVE', 'A    VIEW', 'B    ACTION', 'A+B  MENU'), ('CAR   ENTER', 'SHOP  ROB', 'NPC   STEAL', 'GUN   FIRE'))
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
def reset():
    global sel, top, page, note, nt
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
def draw_map(d):
    d.drawFilledRectangle(0, 0, 72, 40, 0)
    tx0 = int(px // 1) - 36
    ty0 = int(py // 1) - 20
    m = mp
    for sy in range(40):
        row = (ty0 + sy & 63) << 6
        for sx in range(6, 64):
            t = m[row | tx0 + sx & 63]
            if t > 127:
                h = t & 31
                if h >= 12 or (h >= 5 and sx + sy & 1) or sx + sy & 3 == 0:
                    d.setPixel(sx, sy, 1)
            elif t & 15 == 2 and sx * 3 + sy & 7 == 0:
                d.setPixel(sx, sy, 1)
    blink = tick >> 2 & 1
    for c in cars:
        x = int(c[0] // 1) - tx0
        y = int(c[1] // 1) - ty0
        if 6 <= x < 63 and 0 <= y < 39 and (c[4] != 3 or blink):
            d.drawFilledRectangle(x, y, 2, 2, 1)
    for p in peds:
        x = int(p[0] // 1) - tx0
        y = int(p[1] // 1) - ty0
        if 6 <= x < 64 and 0 <= y < 40 and (not p[5]) and (blink or p[7]):
            d.setPixel(x, y, 1)
    x = 36
    y = 20
    d.drawFilledRectangle(x - 2, y - 2, 5, 5, 0)
    d.drawRectangle(x - 2, y - 2, 5, 5, 1)
    d.drawLine(x, y, x + int(math.cos(ang) * 5), y + int(math.sin(ang) * 5), 1)
    d.drawText('N', 67, 1, 1)
    d.drawRectangle(5, 0, 60, 40, 1)
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
        if page == 1:
            draw_map(d)
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
