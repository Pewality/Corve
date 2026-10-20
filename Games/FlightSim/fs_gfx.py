# fs_gfx.py - camera, projection, clipped line drawing
import math
import thumby
from fs_cfg import FOCAL, NEAR

sin = math.sin
cos = math.cos
disp = thumby.display
_drawLine = disp.drawLine
CX = 36
CY = 20
nlines = 0          # lines drawn this frame (used for the line budget)


def reset_lines():
    global nlines
    nlines = 0


def clip_line(x0, y0, x1, y1):
    """Liang-Barsky clip to the 72x40 screen. Returns ints or None."""
    dx = x1 - x0
    dy = y1 - y0
    t0 = 0.0
    t1 = 1.0
    for p, q in ((-dx, x0), (dx, 71 - x0), (-dy, y0), (dy, 39 - y0)):
        if p == 0:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return None
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return None
                if r < t1:
                    t1 = r
    return (int(x0 + t0 * dx), int(y0 + t0 * dy),
            int(x0 + t1 * dx), int(y0 + t1 * dy))


def make_view(px, py, pz, h, p, r):
    """World -> camera transform (x right, y up, z forward) as one matrix."""
    ch, sh = cos(h), sin(h)
    cp, sp = cos(p), sin(p)
    cr, sr = cos(r), sin(r)
    m00 = cr * ch + sr * sp * sh
    m01 = -sr * cp
    m02 = -cr * sh + sr * sp * ch
    m10 = sr * ch - cr * sp * sh
    m11 = cr * cp
    m12 = -sr * sh - cr * sp * ch
    m20 = cp * sh
    m21 = sp
    m22 = cp * ch

    def tf(x, y, z):
        dx = x - px
        dy = y - py
        dz = z - pz
        return (m00 * dx + m01 * dy + m02 * dz,
                m10 * dx + m11 * dy + m12 * dz,
                m20 * dx + m21 * dy + m22 * dz)

    return tf


def line3(a, b):
    """Draw a camera-space line: near-plane clip, then fast screen test."""
    global nlines
    ax, ay, az = a
    bx, by, bz = b
    if az < NEAR:
        if bz < NEAR:
            return
        t = (NEAR - az) / (bz - az)
        ax += (bx - ax) * t
        ay += (by - ay) * t
        az = NEAR
    elif bz < NEAR:
        t = (NEAR - bz) / (az - bz)
        bx += (ax - bx) * t
        by += (ay - by) * t
        bz = NEAR
    k0 = FOCAL / az
    k1 = FOCAL / bz
    x0 = CX + ax * k0
    y0 = CY - ay * k0
    x1 = CX + bx * k1
    y1 = CY - by * k1
    if 0 <= x0 < 72 and 0 <= x1 < 72 and 0 <= y0 < 40 and 0 <= y1 < 40:
        nlines += 1                      # fully on screen: no clipping needed
        _drawLine(int(x0), int(y0), int(x1), int(y1), 1)
        return
    if ((x0 < 0 and x1 < 0) or (x0 > 71 and x1 > 71) or
            (y0 < 0 and y1 < 0) or (y0 > 39 and y1 > 39)):
        return                            # fully off screen: skip
    c = clip_line(x0, y0, x1, y1)
    if c:
        nlines += 1
        _drawLine(c[0], c[1], c[2], c[3], 1)


def dot3(pt):
    x, y, z = pt
    if z < NEAR:
        return
    k = FOCAL / z
    sx = int(CX + x * k)
    sy = int(CY - y * k)
    if 0 <= sx < 72 and 0 <= sy < 40:
        disp.setPixel(sx, sy, 1)
