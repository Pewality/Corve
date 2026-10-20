# tc_render.py - TinyCraft voxel raycaster (fixed point, @micropython.viper)
import math, array
import micropython
from micropython import const
from tc_world import (GRASS, DIRT, STONE, LOG, LEAVES, SAND, PLANKS, COBBLE,
                      COAL_ORE, BEDROCK, MOB, BRICK)

COLB = const(24)         # per-column ray vectors in P
ROWB = const(240)        # per-row ray vectors in P
TOPT = const(16)         # top/bottom face textures in T (17 blocks x 16)
SIDET = const(288)       # side face textures in T

BAYER = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)
P = array.array('i', [0] * 360)
T = bytearray(560)
SIN = [int(round(256 * math.sin(2 * math.pi * i / 256))) for i in range(256)]

def build_tables():
    for i in range(16):
        T[i] = BAYER[i]
    rs = [4242]

    def rnd(n):
        rs[0] = (rs[0] * 75 + 74) % 65537
        return rs[0] % n

    # block: (top base, top noise, side base, side noise)
    spec = {
        GRASS: (9, 1, 5, 1), DIRT: (5, 1, 5, 1), STONE: (7, 1, 7, 1),
        LOG: (6, 1, 4, 1), LEAVES: (6, 2, 6, 2), SAND: (11, 1, 11, 1),
        PLANKS: (9, 0, 9, 0), COBBLE: (6, 2, 6, 2), COAL_ORE: (7, 1, 7, 1),
        BEDROCK: (3, 2, 3, 2), MOB: (13, 0, 12, 0), BRICK: (8, 0, 8, 0),
    }
    for b in spec:
        tb, tn, sb, sn = spec[b]
        for v in range(4):
            for u in range(4):
                k = u | (v << 2)
                tt = tb + (rnd(2 * tn + 1) - tn if tn else 0)
                ss = sb + (rnd(2 * sn + 1) - sn if sn else 0)
                if b == GRASS:
                    if v == 3:
                        ss = 9 + rnd(3) - 1
                    elif v == 2 and rnd(2):
                        ss = 8
                elif b == LOG:
                    if u in (1, 2) and v in (1, 2):
                        tt = 7
                    else:
                        tt = 4
                    ss = 5 if (u & 1) else 3
                elif b == PLANKS:
                    tt = 9 if (v & 1) == 0 else 7
                    ss = tt
                elif b == COAL_ORE:
                    if rnd(5) < 2:
                        tt = 2
                        ss = 2
                elif b == BRICK:
                    mortar = (v == 0) or (((u + (v >> 1) * 2) & 3) == 0)
                    tt = 4 if mortar else 9
                    ss = tt
                elif b == MOB:
                    if v == 2 and (u == 1 or u == 2):
                        ss = 1                      # eyes
                    elif v == 1 and (u == 1 or u == 2):
                        ss = 4                      # mouth
                    elif v == 0:
                        ss = 9
                T[TOPT + b * 16 + k] = max(0, min(16, tt))
                T[SIDET + b * 16 + k] = max(0, min(16, ss))

@micropython.viper
def trace(world: ptr8, P: ptr32) -> int:
    # ray direction in P[11..13]; writes hit cell/t/face to P[14..18]; returns block id
    px = int(P[0])
    py = int(P[1])
    pz = int(P[2])
    maxt = int(P[8])
    dx = int(P[11])
    dy = int(P[12])
    dz = int(P[13])
    sx = 1
    ax = dx
    if dx < 0:
        sx = 0 - 1
        ax = 0 - dx
    if ax < 1:
        ax = 1
    sy = 1
    ay = dy
    if dy < 0:
        sy = 0 - 1
        ay = 0 - dy
    if ay < 1:
        ay = 1
    sz = 1
    az = dz
    if dz < 0:
        sz = 0 - 1
        az = 0 - dz
    if az < 1:
        az = 1
    tdx = 1048576 // ax
    tdy = 1048576 // ay
    tdz = 1048576 // az
    fx = px & 255
    fy = py & 255
    fz = pz & 255
    tmx = (tdx * fx) >> 8
    if sx > 0:
        tmx = (tdx * (256 - fx)) >> 8
    tmy = (tdy * fy) >> 8
    if sy > 0:
        tmy = (tdy * (256 - fy)) >> 8
    tmz = (tdz * fz) >> 8
    if sz > 0:
        tmz = (tdz * (256 - fz)) >> 8
    x = px >> 8
    y = py >> 8
    z = pz >> 8
    t = 0
    face = 0
    hit = 0
    n = 30
    while n > 0:
        n -= 1
        if tmx < tmy:
            if tmx < tmz:
                x += sx
                t = tmx
                tmx += tdx
                face = 0
            else:
                z += sz
                t = tmz
                tmz += tdz
                face = 2
        else:
            if tmy < tmz:
                y += sy
                t = tmy
                tmy += tdy
                face = 1
            else:
                z += sz
                t = tmz
                tmz += tdz
                face = 2
        if t > maxt:
            break
        if ((x | y) >> 5) != 0:
            break
        if (z >> 4) != 0:
            break
        b = int(world[x + (y << 5) + (z << 10)])
        if b != 0:
            hit = b
            break
    P[14] = x
    P[15] = y
    P[16] = z
    P[17] = t
    P[18] = face
    return hit

@micropython.viper
def shade(T: ptr8, P: ptr32, hit: int) -> int:
    px = int(P[0])
    py = int(P[1])
    pz = int(P[2])
    tgx = int(P[3])
    tgy = int(P[4])
    tgz = int(P[5])
    mprog = int(P[6])
    amb = int(P[9])
    dx = int(P[11])
    dy = int(P[12])
    dz = int(P[13])
    x = int(P[14])
    y = int(P[15])
    z = int(P[16])
    t = int(P[17])
    face = int(P[18])
    ua = 0
    va = 0
    if face == 0:
        ua = py + ((t * dy) >> 12)
        va = pz + ((t * dz) >> 12)
    elif face == 1:
        ua = px + ((t * dx) >> 12)
        va = pz + ((t * dz) >> 12)
    else:
        ua = px + ((t * dx) >> 12)
        va = py + ((t * dy) >> 12)
    u = (ua >> 6) & 3
    v = (va >> 6) & 3
    u16 = (ua >> 4) & 15
    v16 = (va >> 4) & 15
    tl = 0
    if face == 2:
        tl = int(T[TOPT + hit * 16 + (u | (v << 2))])
        if dz < 0:
            tl += 3
        else:
            tl -= 4
    else:
        tl = int(T[SIDET + hit * 16 + (u | (v << 2))])
        if face == 1:
            tl -= 3
    tl -= t >> 14
    if t < 24576:
        if u16 == 0:
            tl -= 3
        elif v16 == 0:
            tl -= 3
    if tl < 0:
        tl = 0
    tl = (tl * amb) >> 4
    if x == tgx:
        if y == tgy:
            if z == tgz:
                edge = 0
                if u16 == 0:
                    edge = 1
                if u16 == 15:
                    edge = 1
                if v16 == 0:
                    edge = 1
                if v16 == 15:
                    edge = 1
                if edge == 1:
                    if tl > 7:
                        tl = 0
                    else:
                        tl = 16
                elif mprog > 0:
                    if (((u * 5) ^ (v * 3) ^ face) & 7) < mprog:
                        tl = 1
    return tl

@micropython.viper
def put(buf: ptr8, T: ptr8, P: ptr32):
    ps = int(P[7])
    cx = int(P[19])
    cy = int(P[20])
    tl = int(P[21])
    if tl < 0:
        tl = 0
    if tl > 16:
        tl = 16
    for j in range(ps):
        yy = cy * ps + j
        for i in range(ps):
            xx = cx * ps + i
            if tl > int(T[(xx & 3) + ((yy & 3) << 2)]):
                k = xx + (yy >> 3) * 72
                buf[k] = buf[k] | (1 << (yy & 7))

@micropython.viper
def render(buf: ptr8, world: ptr8, P: ptr32, T: ptr8):
    ps = int(P[7])
    skyl = int(P[10])
    ncol = 72 // ps
    nrow = 40 // ps
    for i in range(360):
        buf[i] = 0
    for cx in range(ncol):
        ox = int(P[COLB + cx * 3])
        oy = int(P[COLB + cx * 3 + 1])
        oz = int(P[COLB + cx * 3 + 2])
        P[19] = cx
        for cy in range(nrow):
            dz = oz + int(P[ROWB + cy * 3 + 2])
            P[11] = ox + int(P[ROWB + cy * 3])
            P[12] = oy + int(P[ROWB + cy * 3 + 1])
            P[13] = dz
            hit = int(trace(world, P))
            tl = skyl - (dz >> 5)
            if hit != 0:
                tl = int(shade(T, P, hit))
            P[20] = cy
            P[21] = tl
            put(buf, T, P)

def setup_view(yaw, pitch, ps):
    yi = (yaw >> 4) & 255
    pi = (pitch >> 4) & 255
    sy = SIN[yi]
    cy = SIN[(yi + 64) & 255]
    sp = SIN[pi]
    cp = SIN[(pi + 64) & 255]
    fx = (cp * cy) >> 8
    fy = (cp * sy) >> 8
    fz = sp
    rx = sy
    ry = -cy
    ux = -((sp * cy) >> 8)
    uy = -((sp * sy) >> 8)
    uz = cp
    for i in range(72 // ps):
        a = (((2 * i + 1) * ps - 72) * 5) >> 1
        o = COLB + i * 3
        P[o] = fx + ((a * rx) >> 8)
        P[o + 1] = fy + ((a * ry) >> 8)
        P[o + 2] = fz
    for j in range(40 // ps):
        b = ((40 - (2 * j + 1) * ps) * 5) >> 1
        o = ROWB + j * 3
        P[o] = (b * ux) >> 8
        P[o + 1] = (b * uy) >> 8
        P[o + 2] = (b * uz) >> 8
    return fx, fy, fz
