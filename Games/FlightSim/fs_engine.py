# fs_engine.py - 3D engine for the Thumby flight sim (keep next to FlightSim.py).
# Python decides WHAT to draw; the three viper functions below (fixed-point maths)
# do all the per-vertex work and draw straight into the display buffer.
import math
import gc
import thumby
import micropython
from array import array

gc.collect()           # defragment before the engine allocates anything
S = 8                  # fixed-point scale: 1 world unit = 8
Q = 16384              # matrix fixed point (Q14)
CELL = 120             # terrain cell (mountains / radio towers)
REGION = 600           # settlement region (towns / cities)
GRID = 60
CACHE_R = 450          # world generation radius (units)
RESEED = 50            # rebuild when you move this far from the cache centre
DRAW_R, MID_R, NEAR_R, ROAD_R = 380, 220, 100, 330    # draw distances (units)
K_MTN, K_LAT, K_SKY, K_MID, K_HOUSE, K_ROAD = 0, 1, 2, 3, 4, 5
CORN = ((-1, -1), (1, -1), (1, 1), (-1, 1))

sin = math.sin
cos = math.cos
disp = thumby.display
prm = array('i', [0] * 32)   # renderer parameters (matrices, offsets, colour...)
CAP = 160                    # small segment queue (2.5 KB): the Thumby has little free RAM
PTS = array('i', [0] * (4 * CAP))
prm[19] = CAP
BUF = None                   # display buffer (direct mode)
MODE = 1                     # 0 = draw into the display buffer, 1 = fallback via thumby.drawLine
objs = []                    # [kind,oxs,ozs,w,hh,seed,blk,nfar,nmid,nall,colw,cullm]
cache_x = 1.0e9
cache_z = 1.0e9
_gen = None
_cxs = _cys = _czs = 0
_mf = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
_mq = (Q, 0, 0, 0, Q, 0, 0, 0, Q)

# ---- the renderer: project() -> clip() -> draw()  (prm: 0-8 vertex matrix, 20-28
# translation matrix, 12 colour, 13 y-offset, 15-17 origin minus camera, 18 count, 19 cap)
@micropython.viper
def project(seg: ptr16, n: int, prm: ptr32, pts: ptr32):
    # (matrix entries are re-read from prm instead of held in locals, to keep
    #  the number of native-function locals small)
    tx = (int(prm[20]) * int(prm[15]) + int(prm[21]) * int(prm[16]) + int(prm[22]) * int(prm[17])) >> 14
    ty = (int(prm[23]) * int(prm[15]) + int(prm[24]) * int(prm[16]) + int(prm[25]) * int(prm[17])) >> 14
    tz = (int(prm[26]) * int(prm[15]) + int(prm[27]) * int(prm[16]) + int(prm[28]) * int(prm[17])) >> 14
    yoff = int(prm[13])
    cnt = int(prm[18])
    cap = int(prm[19])
    i = 0
    k = 0
    while k < n:
        if cnt >= cap:
            break
        ax = (int(seg[i]) ^ 32768) - 32768
        ay = (int(seg[i + 1]) ^ 32768) - 32768
        az = (int(seg[i + 2]) ^ 32768) - 32768
        bx = (int(seg[i + 3]) ^ 32768) - 32768
        by = (int(seg[i + 4]) ^ 32768) - 32768
        bz = (int(seg[i + 5]) ^ 32768) - 32768
        i += 6
        k += 1
        x0 = ((int(prm[0]) * ax + int(prm[1]) * ay + int(prm[2]) * az) >> 14) + tx
        y0 = ((int(prm[3]) * ax + int(prm[4]) * ay + int(prm[5]) * az) >> 14) + ty
        z0 = ((int(prm[6]) * ax + int(prm[7]) * ay + int(prm[8]) * az) >> 14) + tz
        x1 = ((int(prm[0]) * bx + int(prm[1]) * by + int(prm[2]) * bz) >> 14) + tx
        y1 = ((int(prm[3]) * bx + int(prm[4]) * by + int(prm[5]) * bz) >> 14) + ty
        z1 = ((int(prm[6]) * bx + int(prm[7]) * by + int(prm[8]) * bz) >> 14) + tz
        if z0 < 12:
            if z1 < 12:
                continue
            x0 = x0 + (x1 - x0) * (12 - z0) // (z1 - z0)
            y0 = y0 + (y1 - y0) * (12 - z0) // (z1 - z0)
            z0 = 12
        elif z1 < 12:
            x1 = x1 + (x0 - x1) * (12 - z1) // (z0 - z1)
            y1 = y1 + (y0 - y1) * (12 - z1) // (z0 - z1)
            z1 = 12
        ax = cnt * 4
        pts[ax] = 36 + (x0 * 34) // z0
        pts[ax + 1] = 20 - (y0 * 34) // z0 + yoff
        pts[ax + 2] = 36 + (x1 * 34) // z1
        pts[ax + 3] = 20 - (y1 * 34) // z1 + yoff
        cnt += 1
    prm[18] = cnt

@micropython.viper
def clip(pts: ptr32, cnt: int):
    k = 0
    while k < cnt:
        o = k * 4
        k += 1
        sx0 = int(pts[o])
        sy0 = int(pts[o + 1])
        sx1 = int(pts[o + 2])
        sy1 = int(pts[o + 3])
        res = 0
        it = 0
        while res == 0:
            c0 = 0
            if sx0 < 0:
                c0 = 1
            elif sx0 > 71:
                c0 = 2
            if sy0 < 0:
                c0 = c0 | 4
            elif sy0 > 39:
                c0 = c0 | 8
            c1 = 0
            if sx1 < 0:
                c1 = 1
            elif sx1 > 71:
                c1 = 2
            if sy1 < 0:
                c1 = c1 | 4
            elif sy1 > 39:
                c1 = c1 | 8
            if (c0 | c1) == 0:
                res = 1
            elif (c0 & c1) != 0:
                res = 2
            else:
                it += 1
                if it > 8:
                    res = 2
                elif c0 != 0:
                    if (c0 & 8) != 0:
                        sx0 = sx0 + (sx1 - sx0) * (39 - sy0) // (sy1 - sy0)
                        sy0 = 39
                    elif (c0 & 4) != 0:
                        sx0 = sx0 + (sx1 - sx0) * (0 - sy0) // (sy1 - sy0)
                        sy0 = 0
                    elif (c0 & 2) != 0:
                        sy0 = sy0 + (sy1 - sy0) * (71 - sx0) // (sx1 - sx0)
                        sx0 = 71
                    else:
                        sy0 = sy0 + (sy1 - sy0) * (0 - sx0) // (sx1 - sx0)
                        sx0 = 0
                else:
                    if (c1 & 8) != 0:
                        sx1 = sx1 + (sx0 - sx1) * (39 - sy1) // (sy0 - sy1)
                        sy1 = 39
                    elif (c1 & 4) != 0:
                        sx1 = sx1 + (sx0 - sx1) * (0 - sy1) // (sy0 - sy1)
                        sy1 = 0
                    elif (c1 & 2) != 0:
                        sy1 = sy1 + (sy0 - sy1) * (71 - sx1) // (sx0 - sx1)
                        sx1 = 71
                    else:
                        sy1 = sy1 + (sy0 - sy1) * (0 - sx1) // (sx0 - sx1)
                        sx1 = 0
        if res == 1:
            pts[o] = sx0
            pts[o + 1] = sy0
            pts[o + 2] = sx1
            pts[o + 3] = sy1
        else:
            pts[o] = 0 - 1000

@micropython.viper
def draw(buf: ptr8, pts: ptr32, cnt: int, prm: ptr32):
    color = int(prm[12])
    k = 0
    while k < cnt:
        o = k * 4
        k += 1
        x0 = int(pts[o])
        if x0 < 0:
            continue
        y0 = int(pts[o + 1])
        x1 = int(pts[o + 2])
        y1 = int(pts[o + 3])
        ddx = x1 - x0
        stx = 1
        if ddx < 0:
            ddx = 0 - ddx
            stx = 0 - 1
        ddy = y1 - y0
        sty = 1
        if ddy < 0:
            ddy = 0 - ddy
            sty = 0 - 1
        err = ddx - ddy
        while True:
            idx = x0 + (y0 >> 3) * 72
            bit = 1 << (y0 & 7)
            if color != 0:
                buf[idx] = buf[idx] | bit
            else:
                buf[idx] = buf[idx] & (255 ^ bit)
            if x0 == x1:
                if y0 == y1:
                    break
            e2 = err << 1
            if e2 > 0 - ddy:
                err -= ddy
                x0 += stx
            if e2 < ddx:
                err += ddx
                y0 += sty

# ====================== setup, queue, camera ======================
def _setup():
    global BUF, MODE
    gc.collect()
    try:                      # verify the display buffer layout before drawing into it
        b = disp.display.buffer
        disp.fill(0)
        disp.setPixel(10, 17, 1)
        disp.setPixel(71, 39, 1)
        if len(b) == 360 and b[154] == 2 and b[359] == 128 and sum(b) == 130:
            BUF = b
            MODE = 0
        disp.fill(0)
    except Exception:
        pass

_setup()

def _submit():
    """Clip + draw everything queued in PTS (one batch per colour)."""
    c = prm[18]
    if c:
        clip(PTS, c)
        if MODE:
            for i in range(0, c * 4, 4):
                if PTS[i] >= 0:
                    disp.drawLine(PTS[i], PTS[i + 1], PTS[i + 2], PTS[i + 3], prm[12])
        else:
            draw(BUF, PTS, c, prm)
        prm[18] = 0

def line2(x0, y0, x1, y1):
    """Clip + draw one screen-space line (map, horizon)."""
    _submit()
    for i, v in enumerate((x0, y0, x1, y1)):
        PTS[i] = max(-3000, min(3000, int(v)))
    prm[12] = 1
    prm[13] = 0
    prm[18] = 1
    _submit()

def _rot(h, p, r):
    """Model -> world rotation (9 numbers) for yaw h, pitch p, roll r."""
    ch, sh, cp, sp, cr, sr = cos(h), sin(h), cos(p), sin(p), cos(r), sin(r)
    return (ch * cr + sh * sp * sr, ch * sr - sh * sp * cr, sh * cp,
            -cp * sr, cp * cr, sp,
            -sh * cr + ch * sp * sr, -sh * sr - ch * sp * cr, ch * cp)

def _cammat():
    for i in range(9):
        prm[i] = _mq[i]

def _total(R):
    """prm[0..8] = camera matrix * model rotation R (local coords -> camera space)."""
    m = _mf
    for i in range(3):
        for j in range(3):
            prm[i * 3 + j] = int((m[i * 3] * R[j] + m[i * 3 + 1] * R[3 + j] + m[i * 3 + 2] * R[6 + j]) * Q)

def set_camera(cx, cy, cz, h, p, r):
    global _cxs, _cys, _czs, _mf, _mq
    R = _rot(h, p, r)            # the camera matrix is the transpose (inverse) of this
    _mf = (R[0], R[3], R[6], R[1], R[4], R[7], R[2], R[5], R[8])
    _mq = tuple(int(x * Q) for x in _mf)
    for i in range(9):
        prm[20 + i] = _mq[i]
    _cammat()
    prm[12] = 1
    prm[13] = 0
    prm[18] = 0
    _cxs = int(cx * S)
    _cys = int(cy * S)
    _czs = int(cz * S)

def _horizon(h):
    """The horizon is a line at infinity: project two far directions."""
    m = _mf
    pts = []
    for a in (h - 1.2, h + 1.2):
        dx, dz = sin(a), cos(a)
        pts.append([m[0] * dx + m[2] * dz, m[3] * dx + m[5] * dz, m[6] * dx + m[8] * dz])
    a, b = pts
    if a[2] < 0.3 and b[2] < 0.3:
        return
    for q, o in ((a, b), (b, a)):            # clip to the near plane
        if q[2] < 0.3:
            t = (0.3 - q[2]) / (o[2] - q[2])
            q[0] += (o[0] - q[0]) * t
            q[1] += (o[1] - q[1]) * t
            q[2] = 0.3
    line2(36 + a[0] * 34 / a[2], 20 - a[1] * 34 / a[2], 36 + b[0] * 34 / b[2], 20 - b[1] * 34 / b[2])

# ====================== world generation ======================
def hsh(a, b):
    n = ((a * 73856093) ^ (b * 19349663)) & 0x3FFFFFFF
    n ^= n >> 13
    n = (n * 1274126177) & 0x3FFFFFFF
    n ^= n >> 16
    return n

def find_settlements(x0, x1, z0, z1):
    """Random towns/cities. kind 0 = city, 1 = town."""
    out = []
    for rx in range(int(x0 // REGION), int(x1 // REGION) + 1):
        for rz in range(int(z0 // REGION), int(z1 // REGION) + 1):
            hs = hsh(rx, rz)
            k = hs % 10
            if k > 4:
                continue
            cx = rx * REGION + 100 + (hs >> 4) % (REGION - 200)
            cz = rz * REGION + 100 + (hs >> 12) % (REGION - 200)
            if cx * cx + cz * cz < 300 * 300:
                continue  # keep the start/runway area clear
            out.append((0 if k < 2 else 1, cx, cz, hs))
    return out

def _obj(kind, x, z, w, hh, s):
    return [kind, int(x * S), int(z * S), w, hh, s, None, 0, 0, 0,
            (w + 2) * S, (w * 2 + 8) * S * 16]

def _settlement(kind, cx, cz, hs, o):
    s = (hs & 0xFFFF) or 1
    if kind == 0:  # city: 4 x 3 blocks, tallest in the middle
        for i in range(4):
            for j in range(3):
                s = (s * 25173 + 13849) & 0xFFFF
                if s % 10 > 6:
                    continue
                s = (s * 25173 + 13849) & 0xFFFF
                c = abs(i - 1.5) + abs(j - 1)
                hh = 24 + s % 36 + int((3 - c) * 14)
                w = 6 + (s >> 4) % 5
                o.append(_obj(K_SKY if hh >= 62 else K_MID,
                              cx + (i - 1.5) * 32, cz + (j - 1) * 32, w, hh, s))
    else:  # town: scattered houses
        for i in range(3):
            for j in range(3):
                s = (s * 25173 + 13849) & 0xFFFF
                if s % 10 > 6:
                    continue
                s = (s * 25173 + 13849) & 0xFFFF
                o.append(_obj(K_HOUSE,
                              cx + (i - 1) * 24 + (s % 7) - 3,
                              cz + (j - 1) * 24 + ((s >> 4) % 7) - 3,
                              4 + s % 3, 5 + (s >> 3) % 4, s))
    r = _obj(K_ROAD, cx, cz, kind, 0, 0)   # roads: w field holds the kind
    r[10] = 0
    o.append(r)

def regen_gen(px, pz):
    """Builds the object list a little at a time (yields between steps) so
    there is never a big frame hitch. Swaps the new world in when done."""
    global objs, cache_x, cache_z
    no = []
    R = CACHE_R
    sets = find_settlements(px - R - 120, px + R + 120, pz - R - 120, pz + R + 120)
    for kind, cx, cz, hs in sets:
        _settlement(kind, cx, cz, hs, no)
        yield
    for cx in range(int((px - R) // CELL), int((px + R) // CELL) + 1):
        for cz in range(int((pz - R) // CELL), int((pz + R) // CELL) + 1):
            if -1 <= cx <= 0 and -1 <= cz <= 0:
                continue
            hs = hsh(cx + 5000, cz + 9000)
            k = hs % 9
            if k >= 3:
                continue
            ox = cx * CELL + 20 + (hs >> 3) % 80
            oz = cz * CELL + 20 + (hs >> 7) % 80
            near = False
            for st in sets:
                if abs(ox - st[1]) < 120 and abs(oz - st[2]) < 120:
                    near = True
                    break
            if near:
                continue
            if k == 2:
                no.append(_obj(K_LAT, ox, oz, 5 + (hs >> 5) % 3, 60 + (hs >> 9) % 50, hs))
            else:
                no.append(_obj(K_MTN, ox, oz, 14 + (hs >> 5) % 18, 30 + (hs >> 9) % 80, hs))
        yield
    pxs = int(px * S)
    pzs = int(pz * S)
    no.sort(key=lambda o: (o[1] - pxs) ** 2 + (o[2] - pzs) ** 2)  # nearest first
    objs = no
    cache_x = px
    cache_z = pz

def regen_now(px, pz):
    for _ in regen_gen(px, pz):
        pass

def update(px, pz):
    """Call once per frame: starts/advances background world generation."""
    global _gen
    if _gen is None:
        if abs(px - cache_x) > RESEED or abs(pz - cache_z) > RESEED:
            _gen = regen_gen(px, pz)
    if _gen is not None:
        try:
            next(_gen)
        except StopIteration:
            _gen = None
        except MemoryError:                  # low RAM: reclaim, restart the build later
            _gen = None
            gc.collect()

# ====================== segment blocks (built lazily, int16 local coords) ======================
def _ring(a, y, w, d):
    a.extend((-w, y, -d, w, y, -d, w, y, -d, w, y, d, w, y, d, -w, y, d, -w, y, d, -w, y, -d))

def _fin(a, nf, nm):
    return array('h', a), nf, nm, len(a) // 6      # (block, far count, mid count, all count)

def _b_sky(W, HH):
    H1, w2, a = HH * 72 // 100, W * 6 // 10, []
    a.extend((-W, 0, -W, -W, H1, -W, W, 0, W, W, H1, W, 0, HH, 0, 0, HH * 118 // 100, 0))
    _ring(a, H1, W, W)
    a.extend((W, 0, -W, W, H1, -W, -W, 0, W, -W, H1, W))
    _ring(a, H1, w2, w2)
    _ring(a, HH, w2, w2)
    for sx, sz in CORN:
        a.extend((sx * w2, H1, sz * w2, sx * w2, HH, sz * w2))
    nm = len(a) // 6
    for y in (0, H1 // 4, H1 // 2, H1 * 3 // 4):
        _ring(a, y, W, W)
    _ring(a, (H1 + HH) // 2, w2, w2)
    return _fin(a, 3, nm)

def _b_mid(W, HH):
    c, a = W * 55 // 100, []
    q = c // 2
    a.extend((-W, 0, -W, -W, HH, -W))
    _ring(a, HH, W, W)
    a.extend((W, 0, -W, W, HH, -W, W, 0, W, W, HH, W, -W, 0, W, -W, HH, W))
    _ring(a, HH, c, c)                       # helipad square
    nm = len(a) // 6
    for y in (0, HH // 3, HH * 2 // 3):
        _ring(a, y, W, W)
    a.extend((-q, HH, -q, -q, HH, q, q, HH, -q, q, HH, q, -q, HH, 0, q, HH, 0))   # the H
    return _fin(a, 1, nm)

def _b_house(W, HH):
    ya, a = HH + W * 8 // 10, [0, 0, 0, 0, 0, 0]
    a[1] = a[4] = ya                         # far: a single dot at the roof peak
    _ring(a, HH, W, W)
    for sx, sz in CORN:
        a.extend((sx * W, HH, sz * W, 0, ya, 0))
    nm = len(a) // 6
    for sx, sz in CORN:
        a.extend((sx * W, 0, sz * W, sx * W, HH, sz * W))
    _ring(a, 0, W, W)
    return _fin(a, 1, nm)

def _b_lat(W, HH):
    WT, a = W // 4, []
    WM = (W + WT) // 2
    for sx, sz in CORN:
        a.extend((sx * W, 0, sz * W, sx * WT, HH, sz * WT))
    _ring(a, 0, W, W)
    _ring(a, HH // 2, WM, WM)
    _ring(a, HH, WT, WT)
    a.extend((0, HH, 0, 0, HH * 115 // 100, 0))
    nm = len(a) // 6
    for (y0, w0, y1, w1) in ((0, W, HH // 2, WM), (HH // 2, WM, HH, WT)):      # X bracing
        for i in range(4):
            ix, iz = CORN[i]
            jx, jz = CORN[(i + 1) & 3]
            a.extend((ix * w0, y0, iz * w0, jx * w1, y1, jz * w1, jx * w0, y0, jz * w0, ix * w1, y1, iz * w1))
    return _fin(a, 4, nm)

def _b_mtn(W, HH, s):
    WZ = W * (14 + ((s >> 6) & 7)) // 20
    ax, az, a = ((s & 7) * 2 - 7) * W // 20, (((s >> 3) & 7) * 2 - 7) * WZ // 20, []
    _ring(a, 0, W, WZ)
    for sx, sz in CORN:
        a.extend((sx * W, 0, sz * WZ, ax, HH, az))
    nf = len(a) // 6
    pts = [((sx * W) + (ax - sx * W) * 62 // 100, HH * 62 // 100, (sz * WZ) + (az - sz * WZ) * 62 // 100) for sx, sz in CORN]
    for i in range(4):                       # snow line
        a.extend(pts[i] + pts[(i + 1) & 3])
    n = len(a) // 6
    return array('h', a), nf, n, n

def _b_road(kind):
    return array('h', ((0, 0, -60 * S, 0, 0, 60 * S, -70 * S, 0, 16 * S, 70 * S, 0, 16 * S) if kind == 0 else
                       (-12 * S, 0, -40 * S, -12 * S, 0, 40 * S, -40 * S, 0, 12 * S, 40 * S, 0, 12 * S))), 2, 2, 2

def _build(o):
    k, W, HH = o[0], o[3] * S, o[4] * S
    o[6], o[7], o[8], o[9] = (_b_mtn(W, HH, o[5]) if k == K_MTN else _b_lat(W, HH) if k == K_LAT else
                              _b_sky(W, HH) if k == K_SKY else _b_mid(W, HH) if k == K_MID else
                              _b_house(W, HH) if k == K_HOUSE else _b_road(o[3]))

def _grid_block():
    a = []
    ext = 4 * GRID * S
    for i in (0, 1, -1, 2, -2, 3, -3):
        x = i * GRID * S
        a.extend((x, 0, -ext, x, 0, ext, -ext, 0, x, ext, 0, x))
    return array('h', a)

def _runway_block():
    a = [-6 * S, 0, -60 * S, 6 * S, 0, -60 * S, 6 * S, 0, -60 * S, 6 * S, 0, 60 * S,
         6 * S, 0, 60 * S, -6 * S, 0, 60 * S, -6 * S, 0, 60 * S, -6 * S, 0, -60 * S]
    for z in range(-50, 51, 25):
        a.extend((0, 0, z * S, 0, 0, (z + 10) * S))
    return array('h', a)

GRIDB = _grid_block()
RWYB = _runway_block()

# ====================== collision ======================
def roof(px, pz):
    """Height of a landable flat roof (mid-rise helipad) under (px, pz), else 0."""
    pxs = int(px * S)
    pzs = int(pz * S)
    for o in objs:
        if o[0] == K_MID:
            c = o[3] * S - 4
            if abs(pxs - o[1]) < c and abs(pzs - o[2]) < c:
                return o[4]
    return 0.0

def hit(px, py, pz):
    pxs = int(px * S)
    pzs = int(pz * S)
    for o in objs:
        c = o[10]
        dx = pxs - o[1]
        if dx < 0:
            dx = -dx
        if dx > c:
            continue
        dz = pzs - o[2]
        if dz < 0:
            dz = -dz
        if dz > c:
            continue
        k = o[0]
        if k == K_ROAD:
            continue
        w = o[3]
        hh = o[4]
        if k == K_MTN:
            if py < hh * (1 - max(dx, dz) / c):
                return o
        elif k == K_LAT:
            f = py / hh
            if f < 1.15 and max(dx, dz) / S < w * (1 - 0.75 * min(f, 1)) + 1.5:
                return o
        elif py < hh - 0.05:
            return o
    return None

# ====================== world drawing ======================
def draw_world(h, gn, lod, ck):
    """Call set_camera() first. h = heading, gn = grid half-size (1-3),
    lod = detail 0.45..1, ck = view-cone width."""
    _horizon(h)
    p = prm
    cxs = _cxs
    cys = _cys
    czs = _czs
    gs = GRID * S
    p[15] = (cxs // gs) * gs - cxs
    p[16] = -cys
    p[17] = (czs // gs) * gs - czs
    project(GRIDB, 4 * gn + 2, p, PTS)
    if cxs * cxs + czs * czs < 4000 * 4000:      # runway
        p[15] = -cxs
        p[17] = -czs
        project(RWYB, 9, p, PTS)
    fxq = int(sin(h) * 1024)
    fzq = int(cos(h) * 1024)
    l2 = lod * lod * 64
    far2, mid2, near2, road2 = [int(r * r * l2) for r in (DRAW_R, MID_R, NEAR_R, ROAD_R)]
    ckq = int(ck * 16)
    built = 0
    for o in objs:
        dx = o[1] - cxs
        dz = o[2] - czs
        d2 = dx * dx + dz * dz
        if d2 > far2:
            continue
        f = (dx * fxq + dz * fzq) >> 10
        sd = (dx * fzq - dz * fxq) >> 10
        if sd < 0:
            sd = -sd
        if sd * 16 > f * ckq + o[11]:            # outside the view cone / behind
            continue
        if o[0] == K_ROAD and d2 > road2:
            continue
        if p[18] > CAP - 48:                     # queue nearly full: draw it now
            _submit()
        blk = o[6]
        if blk is None:
            if built >= 2:                       # spread block building over frames
                continue
            try:
                _build(o)
            except MemoryError:                  # low RAM: reclaim and retry next frame
                gc.collect()
                continue
            built += 1
            blk = o[6]
        p[15] = dx
        p[16] = -cys
        p[17] = dz
        project(blk, o[7] if d2 > mid2 else (o[9] if d2 < near2 else o[8]), p, PTS)
    _submit()

# ====================== aircraft models + rings ======================
# local coords: x right, y up, z forward
PV = ((0, 0, 5), (-4.5, 0, -3), (4.5, 0, -3), (0, 0, -2.2), (0, 0.9, 2),
      (0, 0.8, -0.6), (0, 0.3, -1.2), (0, 2.6, -3.4), (0, 0.3, -3.0),
      (-1.8, 0.1, -3.3), (1.8, 0.1, -3.3))
PE = ((0, 1), (0, 2), (1, 3), (2, 3), (0, 3), (0, 4), (4, 5), (5, 3),
      (6, 7), (7, 8), (8, 9), (8, 10))
PSH = (0, 1, 3, 2)                   # vertices that outline the ground shadow
HV = ((0, -0.2, 2.8), (0, 0.9, 1.6), (0, 1.1, -0.8), (0, 0.3, -1.4),
      (-1, 0, 0.4), (1, 0, 0.4), (0, -0.8, 0.4), (0, 0.7, -6.5),
      (0, 2.3, -7), (0, 2.0, -0.4),
      (-1.2, -1.5, 2.0), (-1.2, -1.5, -1.4), (1.2, -1.5, 2.0), (1.2, -1.5, -1.4))
HE = ((0, 1), (1, 2), (2, 3), (0, 4), (0, 5), (0, 6), (1, 4), (1, 5),
      (4, 6), (5, 6), (4, 3), (5, 3), (3, 7), (7, 8), (2, 9),
      (10, 11), (12, 13), (4, 10), (4, 11), (5, 12), (5, 13))
HSH = (10, 11, 13, 12)

JV = ((0, 0, 6.5), (-4, 0, -4), (4, 0, -4), (0, 0, -3.5), (0, 0.8, 2.5), (0, 0.7, -0.5),
      (-0.9, 0.2, -2.5), (-1.2, 2.4, -4.2), (0.9, 0.2, -2.5), (1.2, 2.4, -4.2),
      (-0.9, 0.2, -4), (0.9, 0.2, -4))
JE = ((0, 1), (0, 2), (1, 3), (2, 3), (0, 3), (0, 4), (4, 5), (5, 3),
      (6, 7), (7, 10), (8, 9), (9, 11))

def _model(V, E, extra):
    a = []
    for i, j in E:
        for k in (i, j):
            a.extend([round(c * S) for c in V[k]])
    a.extend([0] * (12 * extra))      # room for the spinning rotor blades
    return array('h', a)

PLANEB = _model(PV, PE, 0)
HELIB = _model(HV, HE, 2)
JETB = _model(JV, JE, 0)
JEDG = [JETB[i * 6:i * 6 + 6] for i in range(len(JE))]
PEDG = [PLANEB[i * 6:i * 6 + 6] for i in range(len(PE))]     # single edges (for wreckage)
HEDG = [HELIB[i * 6:i * 6 + 6] for i in range(len(HE))]

def draw_craft(heli, px, py, pz, h, p, r, fc, gy, jet=False):
    """The plane/jet/helicopter: thin black outline + white model, plus a ground shadow."""
    R = _rot(h, p, r)
    if 1.5 < py - gy < 45:                         # shadow: a landing aid
        V = HV if heli else (JV if jet else PV)
        q = [(int((R[0] * V[i][0] + R[1] * V[i][1] + R[2] * V[i][2]) * S),
              int((R[6] * V[i][0] + R[7] * V[i][1] + R[8] * V[i][2]) * S)) for i in (HSH if heli else PSH)]
        a = []
        for k in range(4):
            a.extend((q[k][0], 0, q[k][1], q[(k + 1) & 3][0], 0, q[(k + 1) & 3][1]))
        prm[15] = int(px * S) - _cxs
        prm[16] = int((gy + 0.05) * S) - _cys
        prm[17] = int(pz * S) - _czs
        project(array('h', a), 4, prm, PTS)
        _submit()
    _total(R)
    if heli:
        t = fc * 1.1
        c = int(cos(t) * 38)
        s = int(sin(t) * 38)
        for i, v in enumerate((c, 16, -3 + s, -c, 16, -3 - s, -s, 16, -3 + c, s, 16, -3 - c)):
            HELIB[len(HE) * 6 + i] = v             # spinning rotor blades
    blk = HELIB if heli else (JETB if jet else PLANEB)
    n = len(HE) + 2 if heli else len(JE if jet else PE)
    prm[15] = int(px * S) - _cxs
    prm[16] = int((py + (1.5 if heli else 1.0)) * S) - _cys
    prm[17] = int(pz * S) - _czs
    for col, yo in ((0, -1), (1, 0)):              # black outline first, then white
        prm[12] = col
        prm[13] = yo
        project(blk, n, prm, PTS)
        _submit()
    _cammat()

def _ring_blocks():
    """Two octagon rings (outer + inner) facing z (axis 0) or x (axis 1)."""
    out = []
    for axis in (0, 1):
        a = []
        for R in (14 * S, 10 * S):
            pts = [(int(cos(k * 0.7853982) * R), int(sin(k * 0.7853982) * R)) for k in range(8)]
            for k in range(8):
                u0, y0 = pts[k]
                u1, y1 = pts[(k + 1) & 7]
                a.extend((u0, y0, 0, u1, y1, 0) if axis == 0 else (0, y0, u0, 0, y1, u1))
        out.append(array('h', a))
    return out

RINGB = _ring_blocks()

def draw_ring(x, y, z, axis, target):
    """One ring; the current target gets a second (inner) octagon."""
    _submit()
    prm[15] = int(x * S) - _cxs
    prm[16] = int(y * S) - _cys
    prm[17] = int(z * S) - _czs
    project(RINGB[axis], 16 if target else 8, prm, PTS)
    _submit()

# ====================== crash effects (calm, slow motion) ======================
EXD = tuple((int(cos(k * 2.39996) * math.sqrt(1 - (1 - (k + 0.5) / 10) ** 2) * 256),
             int((1 - (k + 0.5) / 10) * 256),
             int(sin(k * 2.39996) * math.sqrt(1 - (1 - (k + 0.5) / 10) ** 2) * 256)) for k in range(20))

def draw_explosion(x, y, z, u, fc):
    """Gentle fireball + embers + rising smoke at (x,y,z); u = progress 0..1."""
    _submit()
    _cammat()
    prm[15] = int(x * S) - _cxs
    prm[16] = int(y * S) - _cys
    prm[17] = int(z * S) - _czs
    R = (2 + 11 * math.sqrt(u)) * S / 256
    a = []
    for k in range(10 if u < 0.5 else max(0, int(10 * (1.0 - (u - 0.5) / 0.7)))):   # fireball spikes, dying down
        d = EXD[k * 2]
        r1 = R * (0.6 + 0.08 * ((k * 7) % 5)) * (1.2 if fc & 1 else 1.0)
        r0 = r1 * 0.35 + R * 0.3 * u
        a.extend((int(d[0] * r0), int(d[1] * r0), int(d[2] * r0), int(d[0] * r1), int(d[1] * r1), int(d[2] * r1)))
    for k in range(6):                                                              # embers
        d = EXD[k * 3 + 1]
        rr = (4 + 16 * u) * S / 256 * (0.8 + 0.07 * k)
        x0, y0, z0 = int(d[0] * rr), int(d[1] * rr) - int(8 * u * u * S), int(d[2] * rr)
        a.extend((x0, y0, z0, x0 - int(d[0] * rr * 0.25), y0 - int(d[1] * rr * 0.25), z0 - int(d[2] * rr * 0.25)))
    for k in range(3):                                                              # smoke column
        bx = (k - 1) * 2 * S
        a.extend((bx, 0, 0, bx + int(sin(fc * 0.25 + k * 2) * S), int((3 + 14 * u) * S * (1 - 0.2 * k)), 0))
    blk = array('h', a)
    for col, yo in ((0, -1), (1, 0)):                                               # outline, then white
        prm[12] = col
        prm[13] = yo
        project(blk, len(a) // 6, prm, PTS)
        _submit()

def draw_wreck(heli, x, y, z, h, p, r, u, seed, jet=False):
    """The aircraft breaking apart, slowly: each edge drifts and tumbles on its
    own path and settles on the ground."""
    _submit()
    _total(_rot(h + u, p + 2 * u, r + 3 * u))
    edg = HEDG if heli else (JEDG if jet else PEDG)
    tt = u * 0.35
    for col, yo in ((0, -1), (1, 0)):
        prm[12] = col
        prm[13] = yo
        s = seed or 1
        for e in edg:
            s = (s * 25173 + 13849) & 0xFFFF
            prm[15] = int((x + ((s & 31) - 16) * tt) * S) - _cxs
            prm[16] = int(max(0.4, y + (((s >> 5) & 15) + 4) * tt - 14 * u * u) * S) - _cys
            prm[17] = int((z + (((s >> 9) & 31) - 16) * tt) * S) - _czs
            project(e, 1, prm, PTS)
        _submit()
    _cammat()

def damage(o, ix, iy, iz):
    """Break part of a solid object: knock out and bend the lines around the impact
    point (in the object's own scaled coords) and add jagged cracks."""
    if o[6] is None:
        _build(o)
    blk = o[6]
    out = []
    s = (o[5] & 0xFFFF) | 1
    for i in range(o[9]):
        c = [blk[i * 6 + k] for k in range(6)]
        mx, my, mz = (c[0] + c[3]) // 2 - ix, (c[1] + c[4]) // 2 - iy, (c[2] + c[5]) // 2 - iz
        if mx * mx + my * my + mz * mz < (18 * S) ** 2:
            s = (s * 25173 + 13849) & 0xFFFF
            if s % 3 == 0:
                continue                         # knocked out
            for k in range(3, 6):                # bent out of shape
                s = (s * 25173 + 13849) & 0xFFFF
                c[k] += (s % (6 * S)) - 3 * S
            c[1] = max(c[1], 0)
            c[4] = max(c[4], 0)
        out.extend(c)
    for k in range(6):                           # cracks
        s = (s * 25173 + 13849) & 0xFFFF
        out.extend((ix, iy, iz, ix + ((s & 31) - 16) * S // 2, iy + (((s >> 5) & 15) - 6) * S // 2,
                    iz + (((s >> 9) & 31) - 16) * S // 2))
    o[6] = array('h', out)
    o[7] = o[8] = o[9] = len(out) // 6
