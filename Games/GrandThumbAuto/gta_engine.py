# gta_engine.py - Grand Thumb Auto code (stored in small pieces; main.py loads it). Do not edit.
#@@art
CARS = (('0r', 10, 8, '0,3,10,3,4 1,1,8,2,4 2,0,6,1,4 2,1,6,2,2 0,4,1,1,2 9,4,1,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('0f', 10, 8, '=0r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('0s', 22, 8, '0,3,22,3,4 4,1,13,2,4 6,0,9,1,4 5,1,5,2,2 11,1,5,2,2 21,3,1,1,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('1r', 10, 8, '0,3,10,3,4 2,0,6,3,4 3,1,4,1,2 0,4,1,1,2 9,4,1,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('1f', 10, 8, '=1r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('1s', 22, 8, '1,3,20,3,4 5,0,12,3,4 6,1,5,2,2 12,1,4,2,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('2r', 10, 8, '0,0,10,6,4 1,1,8,2,2 5,3,1,3,2 0,5,10,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('2f', 10, 8, '=2r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('2s', 22, 8, '0,1,22,5,4 15,1,6,2,2 2,1,3,2,2 7,1,3,2,2 14,1,1,5,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('3r', 10, 8, '0,3,10,3,3 0,3,10,1,1 1,1,8,2,1 2,0,6,1,1 2,1,6,2,2 0,5,10,1,1 1,6,2,2,2 7,6,2,2,2', 1), ('3f', 10, 8, '=3r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('3s', 22, 8, '0,3,22,3,3 0,3,22,1,1 4,1,13,2,1 6,0,9,1,1 5,1,5,2,2 11,1,5,2,2 9,4,4,1,1 0,5,22,1,1 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('4r', 10, 9, '3,0,4,1,1 0,4,10,3,4 1,2,8,2,4 2,1,6,1,4 2,2,6,2,2 0,5,10,1,4 0,5,1,1,2 2,5,1,1,2 4,5,1,1,2 6,5,1,1,2 8,5,1,1,2 1,7,2,2,2 7,7,2,2,2', 1), ('4f', 10, 9, '=4r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('4s', 22, 9, '0,4,22,3,4 4,2,13,2,4 6,1,9,1,4 5,2,5,2,2 11,2,5,2,2 9,0,4,1,1 0,5,2,1,2 4,5,2,1,2 8,5,2,1,2 12,5,2,1,2 16,5,2,1,2 20,5,2,1,2 3,6,4,3,2 15,6,4,3,2 4,7,1,1,1 16,7,1,1,1', 1))
#@
CARS2 = (('5r', 10, 8, '0,3,10,3,4 3,1,4,1,4 2,2,6,1,2 0,2,2,1,4 8,2,2,1,4 0,3,10,1,4 0,6,3,2,2 7,6,3,2,2', 1), ('5f', 10, 8, '=5r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('5s', 22, 8, '0,4,22,2,4 2,3,16,1,4 6,3,12,1,4 8,2,7,1,4 9,2,5,1,2 21,4,1,1,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('6r', 10, 8, '0,0,10,6,4 5,0,1,6,2 0,5,10,1,2 1,2,3,1,2 6,2,3,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('6f', 10, 8, '=6r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('6s', 22, 8, '0,0,15,6,4 15,2,7,4,4 17,2,3,2,2 7,0,1,6,2 2,2,3,1,2 9,2,3,1,2 2,5,4,3,2 9,5,4,3,2 17,5,4,3,2', 1), ('7r', 10, 8, '0,0,10,6,4 1,1,8,2,2 0,4,1,1,2 9,4,1,1,2 4,4,2,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('7f', 10, 8, '=7r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('7s', 22, 8, '0,0,22,6,4 1,1,4,2,2 6,1,4,2,2 11,1,4,2,2 16,1,4,2,2 20,1,2,3,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1), ('8r', 10, 8, '3,1,4,1,1 1,2,8,1,1 3,2,4,1,2 0,3,10,3,3 0,4,10,1,1 0,2,1,1,1 9,2,1,1,1 0,6,3,2,2 7,6,3,2,2', 1), ('8f', 10, 8, '=8r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('8s', 22, 8, '0,4,22,2,3 0,4,22,1,1 2,3,16,1,1 6,3,12,1,1 8,2,7,1,1 9,2,5,1,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1 9,5,3,1,1', 1), ('9r', 10, 8, '0,0,10,6,3 0,0,10,1,1 2,1,6,1,2 0,3,10,1,1 1,5,8,1,2 1,6,2,2,2 7,6,2,2,2', 1), ('9f', 10, 8, '=9r 3,4,4,1,2 0,3,1,1,1 9,3,1,1,1', 1), ('9s', 22, 8, '0,0,22,6,3 0,0,22,1,1 0,3,22,1,1 14,1,6,1,2 2,1,10,1,2 3,5,4,3,2 15,5,4,3,2 4,6,1,1,1 16,6,1,1,1', 1))
#@
PEOPLE = (('p00', 6, 14, '2,0,2,3,1 1,3,4,5,4 0,3,1,4,3 5,3,1,4,3 1,8,2,6,1 3,8,2,6,1', 1), ('p10', 6, 14, '2,0,2,3,1 1,3,4,5,1 2,3,1,4,2 0,3,1,4,3 5,3,1,4,3 1,8,2,6,3 3,8,2,6,3', 1), ('p20', 6, 14, '1,0,4,3,1 2,1,2,1,2 1,3,4,5,4 2,6,2,1,2 0,3,1,4,4 5,3,1,4,4 1,8,2,6,3 3,8,2,6,3', 1), ('p30', 6, 14, '2,0,2,3,1 1,3,4,3,4 0,6,6,3,4 2,9,1,5,1 3,9,1,5,1', 1), ('p40', 6, 14, '1,0,4,4,1 1,4,4,4,4 0,4,1,3,3 5,4,1,3,3 1,8,2,6,1 3,8,2,6,1', 1), ('p50', 6, 14, '2,0,2,3,1 1,3,4,4,4 0,4,1,2,1 5,3,1,2,1 0,7,2,7,1 4,7,2,7,1', 1), ('p60', 6, 14, '0,0,6,1,1 2,1,2,2,1 1,3,4,5,4 2,5,2,2,2 0,3,1,4,3 5,3,1,4,3 1,8,2,6,1 3,8,2,6,1', 1), ('p70', 6, 14, '2,0,2,3,1 0,3,6,6,4 1,9,2,5,1 3,9,2,5,1', 1), ('p01', 6, 14, '2,0,2,3,1 1,3,4,5,4 0,3,1,4,3 5,3,1,4,3 2,8,1,6,1 3,8,1,6,1', 1), ('p11', 6, 14, '2,0,2,3,1 1,3,4,5,1 2,3,1,4,2 0,3,1,4,3 5,3,1,4,3 2,8,1,6,3 3,8,1,6,3', 1), ('p21', 6, 14, '1,0,4,3,1 2,1,2,1,2 1,3,4,5,4 2,6,2,1,2 0,3,1,4,4 5,3,1,4,4 2,8,1,6,3 3,8,1,6,3', 1), ('p31', 6, 14, '2,0,2,3,1 1,3,4,3,4 0,6,6,3,4 1,9,1,5,1 4,9,1,5,1', 1), ('p41', 6, 14, '1,0,4,4,1 1,4,4,4,4 0,4,1,3,3 5,4,1,3,3 2,8,1,6,1 3,8,1,6,1', 1), ('p51', 6, 14, '2,0,2,3,1 1,3,4,4,4 0,4,1,2,1 5,3,1,2,1 2,7,2,7,1 3,8,1,6,1', 1), ('p61', 6, 14, '0,0,6,1,1 2,1,2,2,1 1,3,4,5,4 2,5,2,2,2 0,3,1,4,3 5,3,1,4,3 2,8,1,6,1 3,8,1,6,1', 1), ('p71', 6, 14, '2,0,2,3,1 0,3,6,6,4 2,9,2,5,1 3,9,1,5,1', 1), ('me', 6, 14, '2,0,2,3,1 1,3,4,5,1 0,3,1,4,3 5,3,1,4,3 1,8,2,6,1 3,8,2,6,1', 1), ('th', 6, 14, '1,0,4,3,1 1,1,4,1,2 0,3,6,5,1 0,3,1,3,1 5,3,1,3,1 1,8,2,6,1 3,8,2,6,1', 1))
#@
PROPS = (('b0', 8, 2, '0,0,4,2,1', 0), ('b1', 8, 2, '4,0,4,2,1', 0), ('lamp', 5, 14, '1,0,3,3,1 2,3,1,11,1', 0), ('red', 5, 14, '1,0,3,4,1 2,4,1,10,1', 0), ('grn', 5, 14, '1,0,3,4,1 2,1,1,2,2 2,4,1,10,1', 0))
def build(mk, a):
    done = {}
    for key in ('CARS', 'CARS2', 'PEOPLE', 'PROPS'):
        S = a.pop(key)
        for n, w, h, o, ol in S:
            ops = []
            for t in o.split():
                if t[0] == '=':
                    ops.extend(done[t[1:]])
                else:
                    ops.append(tuple((int(v) for v in t.split(','))))
            if n[-1] == 'r':
                done[n] = ops
            mk(n, w, h, ops, ol)
        S = None
        import gc
        gc.collect()
#@@game
import math, struct
import micropython
from micropython import const
FOC = const(43)
O_HK = const(64)
O_ZB = const(96)
O_CO = const(168)
O_CF = const(240)
O_IC = const(312)
O_D8 = const(384)
O_RC = const(448)
O_RS = const(520)
O_SIN = const(600)
O_DDX = const(860)
B_BAY = const(4480)
B_TEX = const(4496)
B_LV = const(7056)
B_THR = const(7072)
RAMSZ = 7080
maxd = 24 * 4096
floord = 26 * 4096
ram = bytearray(RAMSZ)
fb = bytearray(360)
SPR = bytearray(3700)
mp = bytearray(4096)
@micropython.viper
def rays(ram):
    P = ptr32(ram)
    x = 0
    while x < 72:
        a = P[2] + P[O_CO + x] & 1023
        i = a & 255
        if a & 256:
            i = 256 - i
        s = P[O_SIN + i]
        if a & 512:
            s = 0 - s
        b = a + 256 & 1023
        j = b & 255
        if b & 256:
            j = 256 - j
        c = P[O_SIN + j]
        if b & 512:
            c = 0 - c
        P[O_RC + x] = c
        P[O_RS + x] = s
        x += 1
#@
@micropython.viper
def sky(ram, fb):
    P = ptr32(ram)
    R8 = ptr8(ram)
    F = ptr8(fb)
    i = 0
    while i < 360:
        F[i] = 0
        i += 1
    hor = P[3]
    ye = hor
    if ye > 40:
        ye = 40
    x = 0
    while x < 72:
        a = P[2] + P[O_CO + x] & 1023
        y = 0
        while y < ye:
            lv = 9 - (hor - y)
            on = 0
            if lv > 0:
                if R8[B_BAY + ((y & 3) << 2) + (x & 3)] < lv:
                    on = 1
            elif a * 7 + y * 13 & 127 == 5:
                on = 1
            if on:
                idx = x + (y >> 3) * 72
                F[idx] = F[idx] | 1 << (y & 7)
            y += 1
        x += 1
#@
@micropython.viper
def floora(ram, mp, fb, y: int):
    P = ptr32(ram)
    R8 = ptr8(ram)
    M = ptr8(mp)
    F = ptr8(fb)
    d12 = P[4] * P[O_D8 + y - P[3]] >> 8
    far = 0
    if d12 > 45000:
        far = 1
    bb = B_BAY + ((y & 3) << 2)
    x = 0
    while x < 72:
        t = d12 * P[O_IC + x] >> 12
        fx = P[0] + (t * P[O_RC + x] >> 12)
        fy = P[1] + (t * P[O_RS + x] >> 12)
        m = M[(fy >> 12 & 63) << 6 | fx >> 12 & 63]
        if m < 128:
            lv = R8[B_LV + (m & 15)] >> far
            if lv:
                if R8[bb + (x & 3)] < lv:
                    idx = x + (y >> 3) * 72
                    F[idx] = F[idx] | 1 << (y & 7)
        x += 1
#@
@micropython.viper
def floorb(ram, mp, fb, y: int):
    P = ptr32(ram)
    M = ptr8(mp)
    F = ptr8(fb)
    d12 = P[4] * P[O_D8 + y - P[3]] >> 8
    thr = 200 + (d12 >> 7)
    x = 0
    while x < 72:
        t = d12 * P[O_IC + x] >> 12
        fx = P[0] + (t * P[O_RC + x] >> 12)
        fy = P[1] + (t * P[O_RS + x] >> 12)
        m = M[(fy >> 12 & 63) << 6 | fx >> 12 & 63]
        k = m & 15
        on = 0
        if m < 128:
            if k == 5:
                if fx & 4095 < thr:
                    if fy >> 11 & 1 == 0:
                        on = 1
            elif k == 6:
                if fy & 4095 < thr:
                    if fx >> 11 & 1 == 0:
                        on = 1
            elif k == 8:
                if fx >> 9 & 1 == 0:
                    on = 1
            elif k == 9:
                if fy >> 9 & 1 == 0:
                    on = 1
        if on:
            idx = x + (y >> 3) * 72
            F[idx] = F[idx] | 1 << (y & 7)
        x += 1
#@
@micropython.viper
def dinit(ram, x: int):
    P = ptr32(ram)
    a = P[2] + P[O_CO + x] & 1023
    f = a & 511
    if f > 256:
        f = 512 - f
    ddx = P[O_DDX + f]
    g = a + 768 & 511
    if g > 256:
        g = 512 - g
    ddy = P[O_DDX + g]
    fxp = P[0] & 4095
    fyp = P[1] & 4095
    sdx = (4096 - fxp) * ddx >> 12
    sdy = (4096 - fyp) * ddy >> 12
    sx = 1
    sy = 1
    if P[O_RC + x] < 0:
        sx = -1
        sdx = fxp * ddx >> 12
    if P[O_RS + x] < 0:
        sy = -1
        sdy = fyp * ddy >> 12
    P[52] = P[0] >> 12
    P[53] = P[1] >> 12
    P[54] = sdx
    P[55] = sdy
    P[56] = ddx
    P[57] = ddy
    P[58] = sx
    P[59] = sy
    P[28] = 40
    P[29] = 1
    P[40] = 0
    P[O_ZB + x] = P[7]
#@
@micropython.viper
def wset(ram):
    P = ptr32(ram)
    R8 = ptr8(ram)
    perp = P[38]
    m = P[37]
    h = m & 31
    bank = m >> 5 & 3
    if bank == 3:
        bank = 3 + (h & 1)
    wc = P[0] + (P[33] * P[O_RC + P[32]] >> 12)
    if P[36] == 0:
        wc = P[1] + (P[33] * P[O_RS + P[32]] >> 12)
    vs = perp * P[8] >> 12
    lod = 0
    if perp > 36000:
        lod = 1
    lvm = 2
    if P[36] == 0:
        lvm = 4
    if lod:
        lvm = lvm >> 2
    ed = 0
    if P[39]:
        if P[30]:
            ed = 1
    P[44] = wc >> 8 & 15
    P[45] = P[6] * 256 + (P[3] - P[41]) * vs
    P[46] = vs
    P[47] = B_TEX + ((bank << 1) + lod << 8)
    P[48] = R8[B_THR + bank]
    P[49] = lvm
    P[50] = P[34] * 37 + P[35] * 91 & 255
    P[51] = ed
#@
@micropython.viper
def wpix(ram, fb):
    P = ptr32(ram)
    R8 = ptr8(ram)
    F = ptr8(fb)
    x = P[32]
    perp = P[38]
    ui = P[44]
    v8 = P[45]
    vs = P[46]
    tb = P[47]
    thr = P[48]
    lvm = P[49]
    lc = P[50]
    ed = P[51]
    top = P[43]
    y1 = P[42]
    y = P[41]
    while y < y1:
        tv = R8[tb + ((v8 >> 8 & 15) << 4) + ui]
        on = 0
        if tv == 1:
            if lc + (v8 >> 12) * 53 + (ui >> 2) * 29 & 7 < thr:
                on = 1
                if perp > 50000:
                    if x + y & 1:
                        on = 0
        elif tv == 2:
            on = 1
        elif R8[B_BAY + ((y & 3) << 2) + (x & 3)] < lvm:
            on = 1
        if y == top:
            on = 1
        if ed:
            on = 1
        idx = x + (y >> 3) * 72
        bit = 1 << (y & 7)
        if on:
            F[idx] = F[idx] | bit
        else:
            F[idx] = F[idx] & 255 - bit
        v8 -= vs
        y += 1
#@
@micropython.viper
def seg2(ram, fb):
    P = ptr32(ram)
    pi = P[38] >> 6
    if pi < 16:
        pi = 16
    rc = 262144 // pi
    hor = P[3]
    top = hor - (P[O_HK + (P[37] & 31)] * rc >> 16)
    bot = hor + (P[4] * rc >> 16)
    occ = P[28]
    y0 = top
    if y0 < 0:
        y0 = 0
    y1 = bot
    if y1 > occ:
        y1 = occ
    if y0 < y1:
        P[41] = y0
        P[42] = y1
        P[43] = top
        wset(ram)
        wpix(ram, fb)
    if top < occ:
        P[28] = top
        if top <= 0:
            P[28] = 0
            P[40] = 1
@micropython.viper
def seg(ram, fb):
    P = ptr32(ram)
    h = P[37] & 31
    perp = P[33] * P[O_CF + P[32]] >> 12
    if perp > P[7]:
        P[40] = 1
        return
    P[38] = perp
    P[39] = P[29]
    if P[29]:
        P[O_ZB + P[32]] = perp
        P[29] = 0
        edge = 0
        if P[36] != P[11]:
            edge = 1
        if P[12] == P[7]:
            edge = 1
        if h != P[13]:
            edge = 1
        if P[32] == 0:
            edge = 0
        P[30] = edge
        P[11] = P[36]
        P[12] = perp
        P[13] = h
    seg2(ram, fb)
#@
@micropython.viper
def wcol(ram, mp, fb, x: int):
    P = ptr32(ram)
    M = ptr8(mp)
    dinit(ram, x)
    mx = P[52]
    my = P[53]
    sdx = P[54]
    sdy = P[55]
    ddx = P[56]
    ddy = P[57]
    sx = P[58]
    sy = P[59]
    side = 0
    steps = 0
    while steps < 44:
        t = sdy
        if sdx < sdy:
            t = sdx
            sdx += ddx
            mx += sx
            side = 0
        else:
            sdy += ddy
            my += sy
            side = 1
        steps += 1
        if t > P[9]:
            break
        m = M[(my & 63) << 6 | mx & 63]
        if m > 127:
            P[32] = x
            P[33] = t
            P[34] = mx
            P[35] = my
            P[36] = side
            P[37] = m
            seg(ram, fb)
            if P[40]:
                break
    if P[29]:
        P[11] = 9
        P[12] = P[7]
        P[13] = 0
@micropython.viper
def walls(ram, mp, fb):
    x = 0
    while x < 72:
        wcol(ram, mp, fb, x)
        x += 1
#@
@micropython.viper
def spcol(ram, fb, bm):
    P = ptr32(ram)
    F = ptr8(fb)
    B = ptr8(bm)
    col = P[27]
    tw = P[20]
    u = P[14]
    if P[23]:
        u = tw - 1 - u
    y0 = P[17]
    ys = y0
    if ys < 0:
        ys = 0
    ye = y0 + P[19]
    if ye > 40:
        ye = 40
    vstep = P[26]
    v16 = (ys - y0) * vstep
    base = P[24] + u
    y = ys
    while y < ye:
        pi = base + (v16 >> 16) * tw
        tv = B[pi >> 1] >> ((pi & 1) << 2) & 15
        if tv:
            on = 0
            if tv == 1:
                on = 1
            elif tv == 3:
                if col + y & 1 == 0:
                    on = 1
            elif tv == 4:
                if P[31]:
                    on = 1
                elif col + y & 1 == 0:
                    on = 1
            idx = col + (y >> 3) * 72
            bit = 1 << (y & 7)
            if on:
                F[idx] = F[idx] | bit
            else:
                F[idx] = F[idx] & 255 - bit
        v16 += vstep
        y += 1
#@
@micropython.viper
def sprite(ram, fb, bm):
    P = ptr32(ram)
    x0 = P[16]
    xs = x0
    if xs < 0:
        xs = 0
    xe = x0 + P[18]
    if xe > 72:
        xe = 72
    if xs >= xe:
        return
    if P[17] >= 40:
        return
    if P[17] + P[19] <= 0:
        return
    col = xs
    u16 = (xs - x0) * P[25]
    while col < xe:
        if P[22] < P[O_ZB + col]:
            P[27] = col
            P[14] = u16 >> 16
            spcol(ram, fb, bm)
        u16 += P[25]
        col += 1
_sp = 0
SD = {}
_eye = -1
_pk = struct.pack_into
#@
def mk(name, w, h, ops, ol=True):
    b = bytearray(w * h)
    for x, y, ww, hh, v in ops:
        for yy in range(y, y + hh):
            for xx in range(x, x + ww):
                b[yy * w + xx] = v
    if ol:
        w2 = w + 2
        o = bytearray(w2 * (h + 2))
        for yy in range(h):
            for xx in range(w):
                v = b[yy * w + xx]
                if v:
                    o[(yy + 1) * w2 + xx + 1] = v
        for yy in range(h + 2):
            for xx in range(w2):
                if not o[yy * w2 + xx]:
                    for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx = xx + ax
                        ny = yy + ay
                        if 0 <= nx < w2 and 0 <= ny < h + 2 and o[ny * w2 + nx] and (o[ny * w2 + nx] != 2):
                            o[yy * w2 + xx] = 2
                            break
        b = o
        w += 2
        h += 2
    global _sp
    SD[name] = _sp << 13 | (1 if ol else 0) << 12 | w << 6 | h
    p = _sp
    for v in b:
        if v:
            SPR[p >> 1] |= v << ((p & 1) << 2)
        p += 1
    _sp = p
#@
def _tabs():
    tau = 2 * math.pi
    for i in range(257):
        _pk('<i', ram, (O_SIN + i) * 4, int(round(math.sin(tau * i / 1024) * 4096)))
        c = math.cos(tau * i / 1024)
        v = 131072 if c < 1 / 32 else min(131072, int(4096 / c))
        _pk('<i', ram, (O_DDX + i) * 4, v)
    for n in range(1, 64):
        _pk('<i', ram, (O_D8 + n) * 4, 65536 // n)
    for x in range(72):
        ph = math.atan((x + 0.5 - 36) / FOC)
        _pk('<i', ram, (O_CO + x) * 4, int(round(ph * 1024 / tau)))
        _pk('<i', ram, (O_CF + x) * 4, int(round(math.cos(ph) * 4096)))
        _pk('<i', ram, (O_IC + x) * 4, int(round(4096 / math.cos(ph))))
    ram[B_BAY:B_BAY + 16] = bytes((0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5))
    ram[B_LV:B_LV + 16] = bytes((0, 6, 2, 9, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    ram[B_THR:B_THR + 8] = bytes((3, 4, 6, 2, 3, 0, 0, 0))
#@
def _texel(bank, lod, vi, ui):
    if bank == 0:
        if lod == 0:
            return 1 if 5 <= vi <= 10 and (3 <= ui <= 5 or 10 <= ui <= 12) else 0
        return 1 if 4 <= vi <= 11 and 1 <= ui <= 14 else 0
    if bank == 1:
        return 1 if 4 <= vi <= 11 and (lod or ui & 3 != 0) else 0
    if bank == 2:
        if 2 <= vi <= 8 and 2 <= ui <= 13:
            return 1
        return 2 if 11 <= vi <= 13 and 4 <= ui <= 11 else 0
    if bank == 3:
        if lod == 0:
            if ui & 3 == 0:
                return 2
            return 1 if 11 <= vi <= 12 and 5 <= ui <= 10 else 0
        return 2 if ui & 7 == 0 else 0
    if lod == 0:
        return 2 if ui * 7 + vi * 13 + ui * vi & 7 < 3 else 0
    return 2 if ui + vi & 3 == 0 else 0
def _tex():
    for bank in range(5):
        for lod in range(2):
            b = B_TEX + (bank * 2 + lod << 8)
            for vi in range(16):
                for ui in range(16):
                    ram[b + vi * 16 + ui] = _texel(bank, lod, vi, ui)
def _art(mk):
    a = {}
    load('art', a)
    a['build'](mk, a)
def build():
    global _tabs, _texel, _tex, mk, build, _art
    _tabs()
    _tex()
    _art(mk)
    _tabs = _texel = _tex = mk = build = _art = None
    import gc
    gc.collect()
#@
def set_dist(tiles):
    global maxd, floord
    maxd = tiles * 4096
    floord = (tiles + 2) * 4096
def setup(px, py, hd, hor, eye16):
    global _eye
    _pk('<11i', ram, 0, int(px * 4096), int(py * 4096), hd & 1023, hor, eye16 * FOC, 0, eye16, maxd, 4096 // FOC, maxd * 5 // 4, floord)
    _pk('<3i', ram, 44, 9, 0, 0)
    if eye16 != _eye:
        _eye = eye16
        _pk('<32i', ram, O_HK * 4, *[(h * 8 - eye16) * FOC for h in range(32)])
def render(mp, px, py, hd, hor, eye16):
    setup(px, py, hd, hor, eye16)
    rays(ram)
    sky(ram, fb)
    n = 1
    while eye16 * FOC * (65536 // n) >> 8 >= floord:
        n += 1
    y = hor + n
    if y < 1:
        y = 1
    while y < 40:
        floora(ram, mp, fb, y)
        floorb(ram, mp, fb, y)
        y += 1
    walls(ram, mp, fb)
def put(name, dep, sxc, ybot, wpx, hpx, flip, tint=1):
    v = SD[name]
    off = v >> 13
    ol = v >> 12 & 1
    tw = v >> 6 & 63
    th = v & 63
    if ol:
        wpx = wpx * tw // (tw - 2)
        hpx = hpx * th // (th - 2)
        ybot += hpx // th
    if wpx < 1:
        wpx = 1
    if hpx < 1:
        hpx = 1
    _pk('<11i', ram, 64, int(sxc - wpx / 2), int(ybot - hpx), wpx, hpx, tw, th, int(dep * 4096), flip, off, (tw << 16) // wpx, (th << 16) // hpx)
    _pk('<i', ram, 124, tint)
    sprite(ram, fb, SPR)
build()
OX = 0
OY = 0
#@
have = [None] * 16
tk = 0
def H(x, y, s):
    n = x * 1619 + y * 31337 + s * 6971 + 1013 & 32767
    n = (n ^ n >> 7) * 9301 + 49297 & 32767
    n = (n ^ n >> 5) * 14071 + 12345 & 32767
    return n ^ n >> 3
def density(X, Y):
    rx = X + 2 >> 2
    ry = Y + 2 >> 2
    r = H(rx, ry, 1) % 100
    if rx == 0 and ry == 0:
        return 4
    if r < 55:
        return 4
    if r < 80:
        return 2
    if r < 90:
        return 1
    return 3
def light(mx, my, ax):
    p = (tk + H(mx + OX, my + OY, 3) % 300 + 150 * ax) % 300
    if p < 120:
        return 0
    if p < 135:
        return 1
    return 2
def box(img, x, y, w, d, hg, mat):
    row = bytes([128 | mat << 5 | hg]) * w
    for r in range(y, y + d):
        img[r * 16 + x:r * 16 + x + w] = row
def tree(img, x, y):
    img[y * 16 + x] = 128 | 96 | 5
def scatter(img, X, Y, n, s0):
    for i in range(n):
        x = 3 + H(X, Y, s0 + i) % 12
        y = 3 + H(X, Y, s0 + 20 + i) % 12
        if img[y * 16 + x] < 128:
            tree(img, x, y)
#@
def base(img, g):
    img[:] = bytes([g]) * 256
    s = bytes([1]) * 14
    img[2 * 16 + 2:2 * 16 + 16] = s
    img[15 * 16 + 2:15 * 16 + 16] = s
    for r in range(3, 15):
        img[r * 16 + 2] = 1
        img[r * 16 + 15] = 1
    img[0:16] = bytes(16)
    img[16:32] = bytes([0, 0]) + bytes([6]) * 14
    for r in range(2, 16):
        img[r * 16] = 0
        img[r * 16 + 1] = 5
    for r in (2, 15):
        img[r * 16] = 8
        img[r * 16 + 1] = 8
    for c in (2, 15):
        img[c] = 9
        img[16 + c] = 9
#@
def _downtown(img, X, Y, h):
    base(img, 3)
    a = 10 + (h >> 4) % 16
    mt = h >> 8 & 1
    m = h % 8
    if m == 0:
        box(img, 3, 3, 12, 12, 4, 2)
        box(img, 5, 5, 8, 8, a, 1)
        box(img, 7, 7, 4, 4, a + 4, 0)
    elif m == 1:
        box(img, 3, 3, 5, 12, a, mt)
        box(img, 10, 3, 5, 12, a - 4, mt ^ 1)
    elif m == 2:
        for i in range(4):
            box(img, 3 + 7 * (i & 1), 3 + 7 * (i >> 1), 5, 5, 6 + H(X, Y, 10 + i) % 18, mt ^ i & 1)
    elif m == 3:
        box(img, 3, 3, 12, 12, 6, 0)
        box(img, 5, 5, 8, 8, 12, 1)
        box(img, 7, 7, 4, 4, a + 6, 1)
    elif m == 4:
        box(img, 3, 3, 12, 3, a - 2, 0)
        box(img, 3, 12, 12, 3, a - 2, 0)
        box(img, 3, 6, 3, 6, a, 1)
        box(img, 12, 6, 3, 6, a, 1)
        tree(img, 8, 8)
    elif m == 5:
        box(img, 7, 7, 4, 4, 2, 0)
        for p in ((4, 4), (13, 4), (4, 13), (13, 13), (4, 8), (13, 9)):
            tree(img, p[0], p[1])
    elif m == 6:
        box(img, 3, 3, 12, 4, a, 1)
        box(img, 3, 11, 12, 4, a - 2, 1)
        box(img, 8, 7, 2, 4, 6, 0)
    else:
        box(img, 3, 3, 12, 12, a + 4, 1)
#@
def _shops(img, X, Y, h):
    base(img, 4)
    m = h % 4
    if m == 0:
        for i in range(3):
            box(img, 3 + 4 * i, 3, 4, 5, 3 + H(X, Y, 10 + i) % 3, 2)
            box(img, 3 + 4 * i, 10, 4, 5, 3 + H(X, Y, 14 + i) % 3, 2)
    elif m == 1:
        box(img, 3, 3, 12, 7, 4, 2)
        box(img, 7, 12, 2, 2, 2, 2)
        scatter(img, X, Y, 3, 60)
    elif m == 2:
        box(img, 11, 3, 4, 4, 3, 2)
        for p in ((4, 6), (7, 6), (4, 9), (7, 9)):
            box(img, p[0], p[1], 1, 1, 2, 0)
    else:
        box(img, 3, 3, 12, 4, 3, 2)
        box(img, 3, 11, 12, 4, 4, 2)
def _housing(img, X, Y, h):
    base(img, 2)
    m = h % 3
    if m == 0:
        for i in range(4):
            box(img, 4 + 6 * (i & 1) + H(X, Y, 20 + i) % 2, 4 + 6 * (i >> 1), 4, 4, 2 + H(X, Y, 30 + i) % 2, 0)
        scatter(img, X, Y, 5, 70)
    elif m == 1:
        q = 8 + (h >> 4) % 6
        box(img, 3, 3, 12, 3, q, 0)
        box(img, 3, 12, 12, 3, q, 0)
        box(img, 3, 6, 3, 6, q, 0)
        box(img, 12, 6, 3, 6, q, 0)
        tree(img, 8, 8)
        tree(img, 9, 9)
    else:
        q = 6 + (h >> 4) % 8
        box(img, 3, 3, 12, 4, q, 0)
        box(img, 3, 9, 12, 5, q - 2, 0)
        scatter(img, X, Y, 3, 75)
#@
def _industrial(img, X, Y, h):
    base(img, 4)
    box(img, 3, 3, 12, 6, 4 + 2 * (h % 2), 3)
    box(img, 3, 10, 7, 5, 4, 3)
    box(img, 11, 10, 3, 3, 8, 3)
    box(img, 14, 14, 1, 1, 18, 3)
def _park(img, X, Y, h):
    base(img, 2)
    if h % 5 == 0:
        base(img, 4)
        box(img, 3, 3, 12, 12, 8, 0)
    else:
        for i in range(3, 15):
            img[8 * 16 + i] = 1
            img[9 * 16 + i] = 1
            img[i * 16 + 8] = 1
            img[i * 16 + 9] = 1
        scatter(img, X, Y, 22, 80)
def gen(mx, my):
    X = mx + OX
    Y = my + OY
    rx = X + 2 >> 2
    ry = Y + 2 >> 2
    r = H(rx, ry, 1) % 100
    if rx == 0 and ry == 0:
        r = 10 if X + Y & 1 else 40
    h = H(X, Y, 2)
    img = bytearray(256)
    if r < 32:
        _downtown(img, X, Y, h)
    elif r < 55:
        _shops(img, X, Y, h)
    elif r < 80:
        _housing(img, X, Y, h)
    elif r < 90:
        _industrial(img, X, Y, h)
    else:
        _park(img, X, Y, h)
    ox = (mx & 3) * 16
    oy = (my & 3) * 16
    for q in range(16):
        o = (oy + q) * 64 + ox
        mp[o:o + 16] = img[q * 16:q * 16 + 16]
_key = None
_pend = False
#@
def sync(px, py, budget=1):
    global _key, _pend
    mx = int(px // 16)
    my = int(py // 16)
    x0 = mx - 2 if px - mx * 16 < 8 else mx - 1
    y0 = my - 2 if py - my * 16 < 8 else my - 1
    if (x0, y0, OX, OY) == _key and (not _pend):
        return
    _key = (x0, y0, OX, OY)
    need = []
    for j in range(4):
        for i in range(4):
            gx = x0 + i
            gy = y0 + j
            s = (gy & 3) * 4 + (gx & 3)
            if have[s] != (gx, gy):
                need.append(((gx * 16 + 8 - px) ** 2 + (gy * 16 + 8 - py) ** 2, gx, gy, s))
    _pend = len(need) > budget
    if need:
        need.sort()
        for n in need[:budget]:
            gen(n[1], n[2])
            have[n[3]] = (n[1], n[2])
def rebase(px, py):
    global OX, OY
    sx = int(px // 64) * 64 if abs(px) > 3000 else 0
    sy = int(py // 64) * 64 if abs(py) > 3000 else 0
    if sx or sy:
        OX += sx // 16
        OY += sy // 16
        for i in range(16):
            if have[i]:
                have[i] = (have[i][0] - sx // 16, have[i][1] - sy // 16)
    return (sx, sy)
