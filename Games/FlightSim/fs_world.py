# fs_world.py - random world generation, collision, and 3D scenery drawing
import math
from fs_cfg import *
from fs_gfx import line3, dot3
import fs_gfx as G

sin = math.sin
cos = math.cos

objs = []            # (kind, x, z, halfwidth, height, seed) - nearest first
roads = []           # (x0, z0, x1, z1)
cache_x = 1.0e9      # centre of the generated area (forces first build)
cache_z = 1.0e9
_gen = None


# ---------------- generation ----------------
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


def build_settlement(kind, cx, cz, hs, o, rd):
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
                o.append((K_SKY if hh >= 62 else K_MID,
                          cx + (i - 1.5) * 32, cz + (j - 1) * 32, w, hh, s))
        rd.append((cx, cz - 60, cx, cz + 60))
        rd.append((cx - 70, cz + 16, cx + 70, cz + 16))
    else:  # town: scattered houses
        for i in range(3):
            for j in range(3):
                s = (s * 25173 + 13849) & 0xFFFF
                if s % 10 > 6:
                    continue
                s = (s * 25173 + 13849) & 0xFFFF
                o.append((K_HOUSE,
                          cx + (i - 1) * 24 + (s % 7) - 3,
                          cz + (j - 1) * 24 + ((s >> 4) % 7) - 3,
                          4 + s % 3, 5 + (s >> 3) % 4, s))
        rd.append((cx - 12, cz - 40, cx - 12, cz + 40))
        rd.append((cx - 40, cz + 12, cx + 40, cz + 12))


def regen_gen(px, pz):
    """Builds the world around (px, pz) a little at a time (yields between
    steps) so there is never a big frame hitch. Swaps in when finished."""
    global objs, roads, cache_x, cache_z
    no = []
    nr = []
    R = CACHE_R
    sets = find_settlements(px - R - 120, px + R + 120, pz - R - 120, pz + R + 120)
    for kind, cx, cz, hs in sets:
        build_settlement(kind, cx, cz, hs, no, nr)
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
                no.append((K_LAT, ox, oz, 5 + (hs >> 5) % 3, 60 + (hs >> 9) % 50, hs))
            else:
                no.append((K_MTN, ox, oz, 14 + (hs >> 5) % 18, 30 + (hs >> 9) % 80, hs))
        yield
    no.sort(key=lambda o: (o[1] - px) ** 2 + (o[2] - pz) ** 2)  # nearest first
    objs = no
    roads = nr
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


def hit(px, py, pz):
    for k, x, z, w, hh, s in objs:
        dx = abs(px - x)
        dz = abs(pz - z)
        if dx > w + 2 or dz > w + 2:
            continue
        if k == K_MTN:
            if py < hh * (1 - max(dx, dz) / (w + 2)):
                return True
        elif k == K_LAT:
            f = py / hh
            if f < 1.15 and max(dx, dz) < w * (1 - 0.75 * min(f, 1)) + 1.5:
                return True
        elif py < hh:
            return True
    return False


# ---------------- 3D scenery ----------------
def box(tf, x, z, w, y0, y1, ground, rings):
    """Wireframe box. Returns the 4 top corners (for roofs)."""
    a = tf(x - w, y1, z - w)
    b = tf(x + w, y1, z - w)
    c = tf(x + w, y1, z + w)
    d = tf(x - w, y1, z + w)
    e = tf(x - w, y0, z - w)
    f = tf(x + w, y0, z - w)
    g = tf(x + w, y0, z + w)
    i = tf(x - w, y0, z + w)
    line3(a, b)
    line3(b, c)
    line3(c, d)
    line3(d, a)
    line3(a, e)
    line3(b, f)
    line3(c, g)
    line3(d, i)
    if ground:
        line3(e, f)
        line3(f, g)
        line3(g, i)
        line3(i, e)
    for n in range(1, rings + 1):  # floor lines
        y = y0 + (y1 - y0) * n / (rings + 1)
        p0 = tf(x - w, y, z - w)
        p1 = tf(x + w, y, z - w)
        p2 = tf(x + w, y, z + w)
        p3 = tf(x - w, y, z + w)
        line3(p0, p1)
        line3(p1, p2)
        line3(p2, p3)
        line3(p3, p0)
    return (a, b, c, d)


def skyscraper(tf, x, z, w, hh, d2, fc):
    h1 = hh * 0.72
    if d2 > MID_D2:
        line3(tf(x - w, 0, z - w), tf(x - w, h1, z - w))
        line3(tf(x + w, 0, z + w), tf(x + w, h1, z + w))
        line3(tf(x, h1, z), tf(x, hh * 1.1, z))
        return
    near = d2 < NEAR_D2
    box(tf, x, z, w, 0, h1, near, 3 if near else 0)
    box(tf, x, z, w * 0.6, h1, hh, True, 1 if near else 0)
    top = tf(x, hh * 1.2, z)
    line3(tf(x, hh, z), top)
    if (fc >> 2) & 1:
        dot3(top)


def midrise(tf, x, z, w, hh, d2):
    if d2 > MID_D2:
        line3(tf(x, 0, z), tf(x, hh, z))
        return
    near = d2 < NEAR_D2
    box(tf, x, z, w, 0, hh, near, 2 if near else 0)


def house(tf, x, z, w, hh, d2):
    if d2 > HOUSE_D2:
        dot3(tf(x, hh + w * 0.6, z))
        return
    top = box(tf, x, z, w, 0, hh, d2 < NEAR_D2, 0)
    apex = tf(x, hh + w * 0.8, z)
    for c in top:
        line3(c, apex)


def lattice(tf, x, z, w, hh, d2, fc):
    wt = w * 0.25
    top = tf(x, hh * 1.15, z)
    if d2 > MID_D2:
        for sx, sz in CORN:
            line3(tf(x + sx * w, 0, z + sz * w), tf(x + sx * wt, hh, z + sz * wt))
    else:
        rings = []
        for f in (0.0, 0.5, 1.0):
            ww = w + (wt - w) * f
            y = hh * f
            rings.append([tf(x + sx * ww, y, z + sz * ww) for sx, sz in CORN])
        for ring in rings:
            for i in range(4):
                line3(ring[i], ring[(i + 1) & 3])
        for i in range(4):
            line3(rings[0][i], rings[2][i])
        if d2 < NEAR_D2:
            for sec in (0, 1):
                lo = rings[sec]
                up = rings[sec + 1]
                for i in range(4):
                    j = (i + 1) & 3
                    line3(lo[i], up[j])
                    line3(lo[j], up[i])
    line3(tf(x, hh, z), top)
    if (fc >> 2) & 1:
        dot3(top)


def mountain(tf, x, z, w, hh, s, d2):
    wz = w * (0.7 + 0.05 * ((s >> 6) & 7))
    ax = x + ((s & 7) - 3.5) * 0.1 * w
    az = z + (((s >> 3) & 7) - 3.5) * 0.1 * wz
    apex = tf(ax, hh, az)
    b = [tf(x + sx * w, 0, z + sz * wz) for sx, sz in CORN]
    for i in range(4):
        line3(b[i], b[(i + 1) & 3])
        line3(b[i], apex)
    if d2 < MID_D2:  # snow line
        sl = []
        for sx, sz in CORN:
            qx = x + sx * w
            qz = z + sz * wz
            sl.append(tf(qx + (ax - qx) * 0.62, hh * 0.62, qz + (az - qz) * 0.62))
        for i in range(4):
            line3(sl[i], sl[(i + 1) & 3])


def draw_world(tf, px, pz, h, fc, inv, gn, ck):
    """px,pz = camera position, h = heading, inv = 1/lod^2 (distance
    scaling), gn = grid half-size, ck = side-culling factor."""
    far = 4000
    line3(tf(px + sin(h - 1.2) * far, 0, pz + cos(h - 1.2) * far),
          tf(px + sin(h + 1.2) * far, 0, pz + cos(h + 1.2) * far))

    gx = int(px // GRID) * GRID
    gz = int(pz // GRID) * GRID
    ext = (gn + 1) * GRID
    for i in range(-gn, gn + 1):
        x = gx + i * GRID
        line3(tf(x, 0, gz - ext), tf(x, 0, gz + ext))
        z = gz + i * GRID
        line3(tf(gx - ext, 0, z), tf(gx + ext, 0, z))

    fx = sin(h)
    fz = cos(h)

    if px * px + pz * pz < 500 * 500:  # runway
        line3(tf(-6, 0, -60), tf(6, 0, -60))
        line3(tf(6, 0, -60), tf(6, 0, 60))
        line3(tf(6, 0, 60), tf(-6, 0, 60))
        line3(tf(-6, 0, 60), tf(-6, 0, -60))
        for z in range(-50, 51, 25):
            line3(tf(0, 0, z), tf(0, 0, z + 10))

    for x0, z0, x1, z1 in roads:
        mx = (x0 + x1) * 0.5 - px
        mz = (z0 + z1) * 0.5 - pz
        if (mx * mx + mz * mz) * inv < 330 * 330 and mx * fx + mz * fz > -60:
            line3(tf(x0, 0, z0), tf(x1, 0, z1))

    budget = LINE_BUDGET
    for k, x, z, w, hh, s in objs:
        if G.nlines > budget:
            break
        dx = x - px
        dz = z - pz
        d2 = (dx * dx + dz * dz) * inv
        if d2 > DRAW_R2:
            continue
        f = dx * fx + dz * fz
        side = dx * fz - dz * fx
        if side < 0:
            side = -side
        if side > f * ck + w * 2 + 8:   # outside the view cone (or behind)
            continue
        if k == K_MTN:
            mountain(tf, x, z, w, hh, s, d2)
        elif k == K_LAT:
            lattice(tf, x, z, w, hh, d2, fc)
        elif k == K_SKY:
            skyscraper(tf, x, z, w, hh, d2, fc)
        elif k == K_MID:
            midrise(tf, x, z, w, hh, d2)
        else:
            house(tf, x, z, w, hh, d2)
