# fs_plane.py - the plane model + ground shadow for third-person view
import math
from fs_cfg import FOCAL
from fs_gfx import line3, clip_line, _drawLine, CX, CY

sin = math.sin
cos = math.cos

# local coords: x right, y up, z forward
V = ((0, 0, 5),          # 0 nose
     (-4.5, 0, -3),      # 1 left wing tip
     (4.5, 0, -3),       # 2 right wing tip
     (0, 0, -2.2),       # 3 tail
     (0, 0.9, 2),        # 4 canopy front
     (0, 0.8, -0.6),     # 5 canopy back
     (0, 0.3, -1.2),     # 6 fin base front
     (0, 2.6, -3.4),     # 7 fin tip
     (0, 0.3, -3.0),     # 8 fin base back
     (-1.8, 0.1, -3.3),  # 9 left tailplane
     (1.8, 0.1, -3.3))   # 10 right tailplane
E = ((0, 1), (0, 2), (1, 3), (2, 3), (0, 3), (0, 4), (4, 5), (5, 3),
     (6, 7), (7, 8), (8, 9), (8, 10))


def draw_plane(tf, px, py, pz, h, p, r):
    ch, sh = cos(h), sin(h)
    cp, sp = cos(p), sin(p)
    cr, sr = cos(r), sin(r)
    cy = py + 1.0
    pts = []
    for lx, ly, lz in V:
        x1 = lx * cr + ly * sr
        y2 = -lx * sr + ly * cr
        dy = y2 * cp + lz * sp
        z1 = -y2 * sp + lz * cp
        pts.append((px + x1 * ch + z1 * sh, cy + dy, pz - x1 * sh + z1 * ch))
    cam = [tf(q[0], q[1], q[2]) for q in pts]
    if 1.5 < py < 45:  # shadow only when low: it's a landing aid
        sh_ = [tf(pts[i][0], 0, pts[i][2]) for i in (0, 1, 3, 2)]
        for i in range(4):
            line3(sh_[i], sh_[(i + 1) & 3])
    # project the 11 vertices once
    sp2 = []
    for x, y, z in cam:
        if z < 0.5:
            z = 0.5
        k = FOCAL / z
        sp2.append((CX + x * k, CY - y * k))
    # pass 1: thin black outline (clears the scenery behind the plane)
    for a, b in E:
        c = clip_line(sp2[a][0], sp2[a][1] - 1, sp2[b][0], sp2[b][1] - 1)
        if c:
            _drawLine(c[0], c[1], c[2], c[3], 0)
    # pass 2: white plane
    for a, b in E:
        c = clip_line(sp2[a][0], sp2[a][1], sp2[b][0], sp2[b][1])
        if c:
            _drawLine(c[0], c[1], c[2], c[3], 1)
