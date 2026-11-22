# BANK ROBBER GETAWAY 3D - endless isometric police chase for the Thumby (72x40)
# CAR (auto-gas): L/R steer, A drift (release a long drift = BOOST), B/DOWN brake, UP bail out
# FOOT: D-pad run, B sprint, A carjack the nearest car. Heat never stops rising: cops flank and box you in,
# set roadblocks, roads dead-end at barricades. 3 lives. Grab $ bags and hearts.
import gc, random, thumby
from math import sin, cos, atan2, sqrt, pi
disp = thumby.display
disp.setFPS(30)
try: disp.setFont("/lib/font3x5.bin", 3, 5, 1)
except: pass
W, H, K, K2, KZ, P, RW, NV = 72, 40, 0.8, 0.4, 0.36, 40, 14, 14
TYPES = (("SEDAN", 2.7, .10, .60, .19, 10, 3, 1.5, 1), ("SPORT", 3.6, .14, .50, .18, 7, 3, 1.3, .8), ("TRUCK", 2.2, .07, .70, .14, 18, 4, 2, 2),
 ("MUSCLE", 3.2, .125, .45, .19, 9, 3.2, 1.6, 1.2), ("COP", 2.5, .09, .55, .17, 4, 3, 1.5, 1), ("SWAT", 2.2, .07, .60, .15, 10, 4, 2, 2.2),
 ("FBI", 3.2, .115, .50, .19, 6, 3.2, 1.5, 1), ("HELI", 2.9, 0, 0, 0, 99, 3, 3, 1), ("MAN", 1, 0, 0, 0, 6, 1, .8, .3))
COP, SWAT, FBI, HELI, MAN = 4, 5, 6, 7, 8
CD = ((4, 7, 1), (3, 5.5, 1), (7, 10, 1), (4, 6.5, 1), (4, 7, 3), (7, 9.5, 2), (4, 7, 1))
LV = (0, 15, 35, 60, 90, 130, 180)
MSG = ("", "COPS!", "MORE COPS!", "SWAT TEAM!", "FBI!", "HELICOPTER!", "ARMY!", "TOTAL WAR!")
class G: pass
g = G()
enemies, civs, parts, pick = [], [], [], []
_c, _v, SP = {}, {}, {}
hi, CX, CY = 0, 0.0, 0.0
class Car:
 def __init__(s, t, x, y, a):
  s.t, s.ang, s.hp, s.x, s.y, s.sx, s.sy = t, a, float(TYPES[t][5]), x, y, x, y
  s.vx = s.vy = s.spd = s.base = s.spin = s.off = 0.0
  s.mode = s.dx = s.dy = s.boost = s.stuck = s.rev = 0
  s.sm = 1.0
  s.id = random.getrandbits(4)
def sfx(f, d=40):
 try: thumby.audio.play(f, d)
 except: pass
def px(x, y, c):
 if 0 <= x < W and 0 <= y < H: disp.setPixel(x, y, c)
def frect(x, y, w, h, c):
 x1, y1, x, y = min(x + w, W), min(y + h, H), max(x, 0), max(y, 0)
 if x1 > x and y1 > y: disp.drawFilledRectangle(x, y, x1 - x, y1 - y, c)
def box(x, y, w, h): frect(x, y, w, 1, 1), frect(x, y + h - 1, w, 1, 1), frect(x, y, 1, h, 1), frect(x + w - 1, y, 1, h, 1)
def text_c(s, y): disp.drawText(s, (W - len(s) * 4 + 1) // 2, y, 1)
def sc(x, y): return (int(36 + ((x - CX) - (y - CY)) * K + .5), int(24 + ((x - CX) + (y - CY)) * K2 + .5))
def sfloor(v): return int(v // P)
def d2(a, x, y): return (a.x - x) ** 2 + (a.y - y) ** 2
def set_msg(s, t=45): g.msg, g.msgt = s, t
def tstr(f): return "%d:%02d" % (f // 1800, f // 30 % 60)
class Rnd:
 def __init__(s, x): s.s = (x & 0xFFFF) or 1
 def n(s, m):
  x = s.s; x ^= (x << 7) & 0xFFFF; x ^= x >> 9; x ^= (x << 8) & 0xFFFF; s.s = x
  return x % m
def make_var(v):
 n = Rnd(v * 2713 + 101).n; k = v % 7; B = []; a = B.append
 if k == 0:
  w, d = 10 + n(8), 10 + n(8); x, y, h = 1 + n(25 - w), 1 + n(25 - d), 20 + n(14)
  a((x, y, w, d, 0, h, 0))
  if n(2): a((x + w // 2, y + d // 2, 1, 1, h, h + 7, 4))
 elif k == 1:
  for i in range(3 + n(2)): a((2 + 3 * i, 2 + 3 * i, 22 - 6 * i, 22 - 6 * i, 7 * i, 7 * i + 7, 0))
 elif k == 2: a((1, 1, 9, 24, 0, 16 + n(16), 0)), a((16, 1, 9, 24, 0, 16 + n(16), 0))
 elif k == 3:
  for i in range(8 + n(4)): tx, ty = 3 + n(20), 3 + n(20); a((tx, ty, 1, 1, 0, 3, 4)); a((tx - 1, ty - 1, 3, 3, 3, 7, 3))
 elif k == 4:
  h = 8 + n(8)
  for r in range(4): y0 = 1 + 4 * r; a((y0 + 8, y0, 17 - y0, 4, 0, h + 3 * r, 0)); a((y0, y0 + 8, 4, 17 - y0, 0, h + 3 * r + n(3), 0))
  if n(2): B = [(x, 26 - y - d, w, d, z, t, s) for (x, y, w, d, z, t, s) in B]
 elif k == 5:
  B = [(9, 11, 8, 4, 0, 3, 4), (11, 9, 4, 8, 0, 3, 4), (10, 10, 6, 6, 0, 3, 4), (12, 12, 2, 2, 3, 12, 4)] + [(i, j, 5, 5, 0, 5 + n(5), 0) for i, j in ((1, 1), (20, 1), (1, 20), (20, 20))]
 else:
  for i in range(9): t = 1.75 + i * .52; a((int(13 + 9.5 * cos(t) - 2.5), int(13 + 9.5 * sin(t) - 2.5), 5, 5, 0, int(10 + 6 * sin(i * .39)), 0))
  a((12, 12, 2, 2, 0, 3, 4))
 return (B, [] if k == 3 else [b[:4] for b in B if b[4] == 0], 1 if k == 3 else (2 if k == 5 else 0))
def block(cx, cy):
 b = _c.get((cx, cy))
 if b is None:
  if len(_c) > 40: _c.clear()
  h = ((cx & 0xFFFF) * 9973) ^ ((cy & 0xFFFF) * 7919); h ^= h >> 11; h = (h & 0xFFFFFF) * 31 + 12345; h ^= h >> 9
  v, f = h % NV, (h >> 8) & 1
  if v not in _v: _v[v] = make_var(v)
  vr = _v[v]; bx, by = cx * P + RW, cy * P + RW
  b = (v, f, [(bx + r[1], by + r[0], r[3], r[2]) if f else (bx + r[0], by + r[1], r[2], r[3]) for r in vr[1]], vr[2],
 0 if abs(cx) <= 1 and abs(cy) <= 1 else (1 if (h >> 14) & 3 == 0 else 0) | (2 if (h >> 20) & 3 == 0 else 0))
  _c[(cx, cy)] = b
 return b
def solid(x, y):
 cx, cy = x // P, y // P; lx, ly = x - cx * P, y - cy * P
 if lx < RW: return 26 <= ly < 31 and (block(int(cx), int(cy))[4] & g.cm & 1) > 0
 if ly < RW: return 26 <= lx < 31 and (block(int(cx), int(cy))[4] & g.cm & 2) > 0
 for r in block(int(cx), int(cy))[2]:
  if r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]: return True
 return False
def in_park(x, y):
 cx, cy = x // P, y // P
 return x - cx * P >= RW and y - cy * P >= RW and block(int(cx), int(cy))[3] & 1
def clear(x, y, r):
 lx, ly = x % P, y % P
 return (lx - r >= 0 and lx + r < RW and (ly + r <= 26 or ly - r >= 31)) or (ly - r >= 0 and ly + r < RW and (lx + r <= 26 or lx - r >= 31))
def hit(x, y, r): return not clear(x, y, r) and (solid(x - r, y - r) or solid(x + r, y - r) or solid(x - r, y + r) or solid(x + r, y + r))
def drive(c, thr, brk, steer, hb):
 t = TYPES[c.t]; mx, ac = t[1] * c.sm, t[2] * c.sm
 if c.boost > 0: mx, ac = mx * 1.4, ac * 1.6
 ca, sa = cos(c.ang), sin(c.ang); fwd = c.vx * ca + c.vy * sa
 if steer:
  c.ang = (c.ang + steer * t[4] * min(abs(fwd), 1.0) * (1.5 if hb else 1) * (-1 if fwd < 0 else 1) + pi) % 6.2832 - pi
  ca, sa = cos(c.ang), sin(c.ang); fwd = c.vx * ca + c.vy * sa
 lat = c.vy * ca - c.vx * sa
 fwd = (fwd + ac) * (1 - ac / mx) if thr else fwd * .988
 if brk: fwd = fwd - .16 if fwd > .1 else max(fwd - ac * .6, -1.2)
 gp = t[3] * (.22 if hb else 1)
 if hb: fwd *= .985
 s2 = fwd * fwd + lat * lat; lat *= (1 - gp) * .99; r2 = s2 - lat * lat; af = abs(fwd)
 if r2 > af * af: fwd += (sqrt(r2) - af) * .7 * (1 if fwd >= 0 else -1)
 c.vx, c.vy = fwd * ca - lat * sa, fwd * sa + lat * ca
 return abs(lat) > .7 and s2 > 1.8
def move(c):
 r = TYPES[c.t][7] + .6; nx, ny = c.x + c.vx, c.y + c.vy
 if clear(nx, ny, r): c.x = c.sx = nx; c.y = c.sy = ny; return 0.0
 if hit(c.x, c.y, r): c.x, c.y, c.vx, c.vy = c.sx, c.sy, 0.0, 0.0; return 0.0
 c.sx, c.sy = c.x, c.y; imp = 0.0
 if hit(nx, c.y, r): imp, c.vx, c.vy = abs(c.vx), c.vx * -.2, c.vy * .85
 else: c.x = nx
 ny = c.y + c.vy
 if hit(c.x, ny, r): imp, c.vy, c.vx = max(imp, abs(c.vy)), c.vy * -.2, c.vx * .85
 else: c.y = ny
 return imp
def collide(a, b):
 if a.mode == 1 and b.mode == 1: return 0.0
 ta, tb = TYPES[a.t], TYPES[b.t]; rr = (ta[6] + ta[7] + tb[6] + tb[7]) * .5
 dx, dy = b.x - a.x, b.y - a.y; dd = dx * dx + dy * dy
 if dd >= rr * rr or dd < 1e-4: return 0.0
 d = sqrt(dd); nx, ny = dx / d, dy / d; ma, mb = ta[8], tb[8]; tot = ma + mb
 wa, wb = (0.0, 1.0) if a.mode == 1 else ((1.0, 0.0) if b.mode == 1 else (mb / tot, ma / tot))
 for c, w, sg in ((a, wa, -1), (b, wb, 1)):
  if w > 0 and not hit(c.x + sg * nx * (rr - d) * w, c.y + sg * ny * (rr - d) * w, TYPES[c.t][7] + .6): c.x, c.y = c.x + sg * nx * (rr - d) * w, c.y + sg * ny * (rr - d) * w
 s = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
 if s <= 0: return 0.0
 for c in (a, b):
  if c.mode == 1 and s > .15: c.mode, c.spin = 2, random.random() * .3 - .15
 j = 1.5 * s / (1 / ma + 1 / mb)
 if a.mode != 1: a.vx, a.vy = a.vx - j * nx / ma, a.vy - j * ny / ma
 if b.mode != 1: b.vx, b.vy = b.vx + j * nx / mb, b.vy + j * ny / mb
 if s > .8: a.hp, b.hp = a.hp - s * mb / tot * 1.6, b.hp - s * ma / tot * 1.6
 return s
def puff(x, y, vx, vy, life, vz=0.0, z=1.0):
 if len(parts) < 45: parts.append([x, y, z, vx, vy, vz, life])
def boom(x, y, n=10):
 for i in range(n): a, s = random.random() * 6.283, random.random() * 1.2 + .2; puff(x, y, cos(a) * s, sin(a) * s, random.randint(7, 16), random.random() * 1.1, 2.0)
def update_parts():
 for i in range(len(parts) - 1, -1, -1):
  q = parts[i]; q[0] += q[3]; q[1] += q[4]; q[2] = max(q[2] + q[5], 0.0); q[5] -= .06; q[3] *= .9; q[4] *= .9; q[6] -= 1
  if q[6] <= 0: del parts[i]
def newbuf(w, h): return bytearray(w * ((h + 7) >> 3))
def setpx(b, w, h, x, y):
 if 0 <= x < w and 0 <= y < h: b[(y >> 3) * w + x] |= 1 << (y & 7)
def vface(sil, det, w, h, x, y0, y1, pat):
 y0, y1 = max(y0, 0), min(y1, h)
 if x < 0 or x >= w or y1 <= y0: return
 for p in range(y0 >> 3, ((y1 - 1) >> 3) + 1):
  m = (1 << min(y1 - p * 8, 8)) - (1 << max(y0 - p * 8, 0)); i = p * w + x
  sil[i] |= m; det[i] = (det[i] & (255 - m)) | (m & pat)
def rast_box(sil, det, w, h, OX, OY, b):
 x0, y0, bw, bd, z0, z1, sty = b; X1, Y1 = x0 + bw, y0 + bd; zt, zb, e = z1 * KZ, z0 * KZ, 1 / K
 def side(s, base, c, lo, hi, sp, ph):
  t, bt = int(base - zt + .5), int(base - zb + .5)
  vface(sil, det, w, h, s, t, bt, sp)
  if sp == 0 and (int(c) & 3) == ph:
   for zw in range(z0 + 2, z1 - 1, 4): setpx(det, w, h, s, int(base - zw * KZ + .5))
  if z0 == 0: setpx(det, w, h, s, bt - 1)
  if c < lo + e or c >= hi - e:
   for y in range(t, bt): setpx(det, w, h, s, y)
 for s in range(int((x0 - Y1) * K + OX), int((X1 - y0) * K + OX) + 2):
  u = (s + .5 - OX) / K; q = 0 if s & 1 else 0x55; sp = 255 if sty == 4 else (q if sty == 3 else 0); x, y = u + Y1, X1 - u
  if x0 <= x < X1: side(s, (x + Y1) * K2 + OY, x, x0, X1, sp, 1)
  if y0 <= y < Y1: side(s, (X1 + y) * K2 + OY, y, y0, Y1, sp, 2)
  vmin, vmax = max(2 * x0 - u, 2 * y0 + u), min(2 * X1 - u, 2 * Y1 + u)
  if vmax > vmin:
   ya, yb = int(vmin * K2 - zt + OY + .5), int(vmax * K2 - zt + OY + .5)
   vface(sil, det, w, h, s, ya, yb, 255 if sty == 4 else q); setpx(det, w, h, s, ya); setpx(det, w, h, s, yb - 1)
def boxes_sprite(boxes, w, h, OX, OY):
 sil, det = newbuf(w, h), newbuf(w, h)
 for b in sorted(boxes, key=lambda b: (b[0] * 2 + b[2] + b[1] * 2 + b[3]) * 100 + b[4]): rast_box(sil, det, w, h, OX, OY, b)
 return (w, h, OX, OY, bytearray(255 - x for x in sil), det)
def bake_variant(v):
 boxes = _v.setdefault(v, make_var(v))[0]; OY = int(max(8, max(b[5] for b in boxes)) * KZ) + 2
 return boxes_sprite(boxes, 43, OY + 22, 21, OY)
def bake_barrier(o):
 w, d = (14, 5) if o == 0 else (5, 14); OX = int(d * K) + 1
 return boxes_sprite(((0, 0, w, d, 0, 5, 3), (1, 1, 2, 2, 5, 10, 4), (w - 3, d - 3, 2, 2, 5, 10, 4)), OX + int(w * K) + 3, 10 + int((w + d) * K2), OX, int(10 * KZ) + 2)
def bake_ground(kind):
 w, h = 65, 34; det = newbuf(w, h)
 def gp(lx, ly): setpx(det, w, h, int((lx - ly) * K + 32.5), int((lx + ly) * K2 + .5))
 for a in (16, 24, 32):
  for i in range(5): gp(7, a + i), gp(a + i, 7)
 for i in range(14, 40, 2): gp(i, 14), gp(14, i), gp(i, 39), gp(39, i)
 if kind & 1:
  for gx in range(18, 37, 4):
   for gy in range(18, 37, 4): gp(gx, gy)
 if kind & 2:
  for i in range(0, 24, 2): gp(27 + 9 * cos(i * .2618), 27 + 9 * sin(i * .2618))
 return (w, h, 32, 0, None, det)
def fillpoly(sil, det, w, h, pts, shade):
 n = len(pts); ys = [q[1] for q in pts]
 for y in range(int(min(ys)), int(max(ys)) + 1):
  yc = y + .5; xl, xr = 999.0, -999.0
  for i in range(n):
   a, b = pts[i], pts[(i + 1) % n]
   if (a[1] <= yc < b[1]) or (b[1] <= yc < a[1]):
    x = a[0] + (yc - a[1]) * (b[0] - a[0]) / (b[1] - a[1]); xl, xr = min(xl, x), max(xr, x)
  if xr < xl: continue
  lo = int(xl + .5)
  for x in range(lo, max(int(xr - .5), lo) + 1):
   if 0 <= x < w and 0 <= y < h:
    i, m = (y >> 3) * w + x, 1 << (y & 7); sil[i] |= m
    if shade == 2 or (shade == 1 and ((x + y) & 1)) or (shade == 3 and not (x & 1) and not (y & 1)): det[i] |= m
    else: det[i] &= 255 - m
def rbox(sil, det, w, h, PX, PY, ca, sa, xa, xb, ya, yb, z0, z1, side):
 C = ((xb, yb), (xb, ya), (xa, ya), (xa, yb)); N = ((1, 0), (0, -1), (-1, 0), (0, 1))
 def pj(c, z): X, Y = ca * c[0] - sa * c[1], sa * c[0] + ca * c[1]; return (PX + (X - Y) * K, PY + (X + Y) * K2 - z * KZ)
 for k in range(4):
  if N[k][0] * (ca + sa) + N[k][1] * (ca - sa) > 0:
   a, b = C[k], C[(k + 1) & 3]; fillpoly(sil, det, w, h, (pj(a, z0), pj(b, z0), pj(b, z1), pj(a, z1)), side)
 fillpoly(sil, det, w, h, [pj(c, z1) for c in C], 2)
def bake_car(t, ai, me):
 L, Wd = TYPES[t][6] * 1.3, TYPES[t][7] * 1.3; bz, cz, bs = CD[t]; bz, cz = bz * 1.4, cz * 1.4
 R = (L + Wd) * K; w = 2 * int(R + 2) + 1; PY = int(R * .5 + cz * KZ) + 2; h = PY + int(R * .5) + 3
 sil, det = newbuf(w, h), newbuf(w, h); ca, sa = cos(ai * .19635), sin(ai * .19635)
 rbox(sil, det, w, h, w // 2, PY, ca, sa, -L, L, -Wd, Wd, 0, bz, 2 if me else bs)
 rbox(sil, det, w, h, w // 2, PY, ca, sa, -.6 * L, .4 * L, -.8 * Wd, .8 * Wd, bz, cz, 0)
 return (w, h, w // 2, PY, bytearray(255 - x for x in sil), det)
def spr(kind, a, b=0, c=0):
 k = (kind << 12) | (a << 6) | (b << 1) | c
 if k not in SP:
  if len(SP) > 170:
   for q in list(SP):
    if q >> 12 == 2: del SP[q]
  SP[k] = (bake_variant, bake_ground, bake_car, bake_barrier)[kind](*((a, b, c) if kind == 2 else (a,)))
 return SP[k]
def spawn_civ(init):
 if len(civs) >= 12 + min(g.lvl, 5): return
 cx, cy, sg, p = g.camx, g.camy, random.choice((-1, 1)), g.p
 if random.getrandbits(1):
  e = random.getrandbits(1); y = sfloor(cy + random.randint(-45, 45)) * P + (10.5 if e else 3.5)
  x = cx + (random.randint(-60, 60) if init else random.randint(55, 85) * sg); dx, dy = (1 if e else -1), 0
 else:
  s = random.getrandbits(1); x = sfloor(cx + random.randint(-60, 60)) * P + (3.5 if s else 10.5)
  y = cy + (random.randint(-45, 45) if init else random.randint(50, 75) * sg); dx, dy = 0, (1 if s else -1)
 if (init and abs(x - p.x) < 22 and abs(y - p.y) < 22) or solid(x, y): return
 for c in civs + enemies:
  if abs(c.x - x) < 11 and abs(c.y - y) < 11: return
 r = random.randint(0, 99); c = Car(0 if r < 40 else (1 if r < 55 else (2 if r < 75 else 3)), x, y, atan2(dy, dx))
 c.mode, c.dx, c.dy = 1, dx, dy; c.spd = c.base = .7 + ((sfloor(y if dx else x) * 5 + dx + 2 * dy) & 7) * .1
 c.vx, c.vy = dx * c.spd, dy * c.spd; civs.append(c)
def spawn_enemy(t):
 p = g.p; a, d = random.random() * 6.2832, 78 + random.randint(0, 20); x, y = p.x + cos(a) * d, p.y + sin(a) * d
 if t != HELI: x = sfloor(x) * P + 7.0
 if (abs(x - g.camx) >= 64 or abs(y - g.camy) >= 64) and not solid(x, y):
  e = Car(t, x, y, atan2(p.y - y, p.x - x)); e.sm, e.hp = .9 + .045 * min(g.lvl, 12), e.hp * (1 + .08 * min(g.lvl, 12))
  enemies.append(e)
def spawn_pick():
 p = g.p; x, y = sfloor(p.x + p.vx * 15 + random.randint(-30, 30)) * P + 7.0, p.y + p.vy * 15 + random.randint(-40, 40)
 if d2(p, x, y) > 700 and not solid(x, y): pick.append([x, y, 1 if (g.lives < 3 or p.hp < TYPES[p.t][5] * .5) and random.getrandbits(2) == 0 else 0, 700])
def spawn_block():
 p = g.p
 if p.vx * p.vx + p.vy * p.vy < .6: return
 t, o = (COP, 3.4) if g.lvl < 5 else (SWAT, 4.2)
 if abs(p.vy) > abs(p.vx): x, y = round((p.x - 7) / P) * P + 7.0, p.y + (100 if p.vy > 0 else -100); cs = ((x - o, y, 0.0), (x + o, y, pi))
 else: x, y = p.x + (100 if p.vx > 0 else -100), round((p.y - 7) / P) * P + 7.0; cs = ((x, y - o, pi / 2), (x, y + o, -pi / 2))
 if any(solid(c[0], c[1]) for c in cs): return
 for c in cs: k = Car(t, c[0], c[1], c[2]); k.mode = 2; civs.append(k)
 set_msg("ROADBLOCK AHEAD!", 40)
def reset():
 gc.collect()
 for l in (enemies, civs, parts, pick): del l[:]
 g.p = Car(0, 7.0, 7.0, -pi / 2); g.onfoot = g.exiting = g.newbest = False
 g.entering = g.frame = g.shake = g.dtime = g.msgt = g.overt = g.inv = g.score = g.state = g.steals = g.cm = 0
 g.etar = g.near = None; g.camx = g.camy = 7.0; g.bonus = g.bust = g.step = 0.0; g.msg = g.reason = ""
 g.lvl, g.lives, g.up_prev, g.a_prev = 1, 3, True, True
def start():
 reset(); g.state, g.cm = 1, 3
 for i in range(6): spawn_civ(True)
 set_msg("BANK ROBBED! GO!", 70); sfx(900, 150)
def hurt(n):
 if not g.inv: g.p.hp -= n; g.shake = max(g.shake, min(int(n * 2) + 1, 6)); sfx(160, 70)
def exit_car():
 c = g.p; mx, my = c.x, c.y
 for sd in (4.5, -4.5):
  if not hit(c.x - sin(c.ang) * sd, c.y + cos(c.ang) * sd, 1.4): mx, my = c.x - sin(c.ang) * sd, c.y + cos(c.ang) * sd; break
 c.mode, c.spin = 2, 0.0; civs.append(c); g.p = m = Car(MAN, mx, my, c.ang); m.vx, m.vy = c.vx * .2, c.vy * .2
 g.onfoot, g.exiting, g.dtime = True, False, 0; set_msg("A = ENTER CAR", 70); sfx(500, 40)
def enter_car(c):
 civs.remove(c); c.mode, c.boost, c.spd = 0, 0, 0.0; g.p = c; g.onfoot, g.entering, g.etar = False, 0, None
 g.steals += 1; g.bonus += 25; g.bust = max(g.bust - 40, 0.0); set_msg(TYPES[c.t][0] + " STOLEN!", 40); sfx(600, 60)
def update_driving(p):
 B = thumby; hb = B.buttonA.pressed(); brk = B.buttonB.pressed() or B.buttonD.pressed() or g.exiting; up = B.buttonU.pressed()
 if up and not g.up_prev: g.exiting = not g.exiting; set_msg("STOPPING..." if g.exiting else "GO!", 30)
 g.up_prev = up
 dr = drive(p, not brk, brk, B.buttonR.pressed() - B.buttonL.pressed(), hb and not g.exiting)
 if in_park(p.x, p.y): p.vx, p.vy = p.vx * .93, p.vy * .93
 imp = move(p)
 if imp > 1.4: hurt((imp - 1.1) * .8); boom(p.x, p.y, 3)
 if dr:
  g.bonus += .34
  if g.frame & 1: puff(p.x - cos(p.ang) * 2.5, p.y - sin(p.ang) * 2.5, random.random() * .4 - .2, random.random() * .4 - .2, 9, .15, .5)
 if dr and hb: g.dtime += 1
 else:
  if g.dtime >= 20:
   p.boost = min(g.dtime, 70) // 2 + 10; g.bonus += g.dtime // 2; p.vx += cos(p.ang) * 1.2; p.vy += sin(p.ang) * 1.2; set_msg("DRIFT BOOST!", 30); sfx(900, 120)
  g.dtime = 0
 if p.boost > 0: p.boost -= 1; puff(p.x - cos(p.ang) * 3.5, p.y - sin(p.ang) * 3.5, 0.0, 0.0, 5, .1, 1.0)
 if p.hp < TYPES[p.t][5] * .4 and g.frame % 3 == 0: puff(p.x, p.y, random.random() * .3 - .15, random.random() * .3 - .15, 14, .5, 3.0)
 if g.exiting and p.vx * p.vx + p.vy * p.vy < .36: exit_car()
def update_man(m):
 B = thumby; ud, rl = B.buttonD.pressed() - B.buttonU.pressed(), B.buttonR.pressed() - B.buttonL.pressed(); a = B.buttonA.pressed()
 ae = a and not g.up_prev; g.up_prev = a; g.near, bd = None, 256
 for c in civs:
  dd = d2(c, m.x, m.y)
  if dd < bd: g.near, bd = c, dd
 if g.entering > 0:
  c = g.etar
  if c is None or c not in civs or d2(c, m.x, m.y) > 324: g.entering, g.etar = 0, None
  else:
   g.entering -= 1; m.vx = m.vy = 0.0
   if c.mode == 1: c.spd = 0.0
   if g.entering == 0: enter_car(c); return
 else:
  vx, vy = ud + rl, ud - rl; n = sqrt(vx * vx + vy * vy)
  if n > 0: sp = 1.8 if B.buttonB.pressed() else 1.1; m.vx, m.vy = vx / n * sp, vy / n * sp; m.ang = atan2(m.vy, m.vx); g.step += sp
  else: m.vx, m.vy = m.vx * .5, m.vy * .5
  if ae and g.near is not None: g.entering, g.etar = 10, g.near; set_msg("CARJACKING!", 12)
 move(m)
def update_enemy(e):
 p = g.p; mx = TYPES[e.t][1] * e.sm; heli = e.t == HELI
 dx, dy = p.x + (p.vx * 6 if heli else 0) - e.x, p.y + (p.vy * 6 if heli else 0) - e.y; dd = dx * dx + dy * dy
 if heli:
  d = sqrt(dd) + .01; e.vx, e.vy = (e.vx + dx / d * mx * .025) * .975, (e.vy + dy / d * mx * .025) * .975
  e.x += e.vx; e.y += e.vy; e.ang = atan2(e.vy, e.vx); return
 if dd > 6000:
  s = mx * .9 / sqrt(dd); e.vx, e.vy = dx * s, dy * s; e.x += e.vx; e.y += e.vy; e.ang = atan2(dy, dx)
  if dd < 7500 and solid(e.x, e.y):
   e.x = sfloor(e.x) * P + 7.0
   if solid(e.x, e.y): e.y += 8
  e.sx, e.sy = e.x, e.y; return
 lead = 6 if e.t == FBI else 3; tx, ty = p.x + p.vx * lead, p.y + p.vy * lead
 if g.lvl > 2 and not g.onfoot and dd > 256:
  n, r = sqrt(p.vx * p.vx + p.vy * p.vy) + .01, e.id & 3
  if r == 1: tx, ty = tx - p.vy / n * 11, ty + p.vx / n * 11
  elif r == 2: tx, ty = tx + p.vy / n * 11, ty - p.vx / n * 11
  elif r == 3: tx, ty = tx + p.vx / n * 26, ty + p.vy / n * 26
 ta = atan2(ty - e.y, tx - e.x)
 if (g.frame + e.id) & 3 == 0:
  e.off = 0.0
  if solid(e.x + cos(ta) * 12, e.y + sin(ta) * 12):
   e.off = 2.5
   for o in (.5, -.5, 1, -1, 1.6, -1.6):
    if not solid(e.x + cos(ta + o) * 12, e.y + sin(ta + o) * 12): e.off = o; break
 d = (ta + e.off - e.ang + pi) % 6.2832 - pi; steer = max(-1.0, min(1.0, d * 3))
 ca, sa = cos(e.ang), sin(e.ang); spd = e.vx * ca + e.vy * sa; thr, brk = True, False
 if solid(e.x + ca * 8, e.y + sa * 8):
  steer = steer or 1.0
  if spd > 1.4: thr, brk = False, spd > 2
 elif abs(d) > 1.2 and spd > 1.6: thr = False
 if abs(spd) < .2:
  e.stuck += 1
  if e.stuck > 30: e.rev, e.stuck, e.spin = 22, 0, e.spin + 1
 else: e.stuck = 0
 if e.rev > 0: e.rev, thr, brk, steer = e.rev - 1, False, True, -steer
 drive(e, thr, brk, steer, False); imp = move(e)
 if imp > 1: e.hp -= (imp - .7) * .8
def update_civs():
 p = g.p
 for c in civs:
  if c.mode == 1:
   if (g.frame + c.id) & 3 == 0 and solid(c.x + c.dx * 9, c.y + c.dy * 9):
    c.dx, c.dy = -c.dx, -c.dy; c.ang = atan2(c.dy, c.dx)
    if c.dx: c.y = 2 * sfloor(c.y) * P + 14 - c.y
    else: c.x = 2 * sfloor(c.x) * P + 14 - c.x
   t = 0.0 if g.onfoot and 0 < (p.x - c.x) * c.dx + (p.y - c.y) * c.dy < 26 and abs((p.y - c.y) * c.dx + (p.x - c.x) * c.dy) < 6 else c.base
   c.spd = min(t, c.spd + .03) if c.spd < t else max(t, c.spd - .1)
   c.vx, c.vy = c.dx * c.spd, c.dy * c.spd; c.x += c.vx; c.y += c.vy
  else: c.vx *= .95; c.vy *= .95; c.ang += c.spin; c.spin *= .92; move(c)
def collisions():
 p = g.p; near = [p] + [c for c in civs + enemies if c.t != HELI and abs(c.x - p.x) < 50 and abs(c.y - p.y) < 50]
 for i in range(len(near)):
  a = near[i]
  for b in near[i + 1:]:
   if abs(b.x - a.x) > 9 or abs(b.y - a.y) > 9: continue
   s = collide(a, b)
   if s > .8:
    boom((a.x + b.x) * .5, (a.y + b.y) * .5, 3)
    if a is p or b is p: g.shake = max(g.shake, min(int(s * 2), 6)); sfx(140, 60)
def cleanup():
 for e in enemies[:]:
  if e.hp <= 0: boom(e.x, e.y, 12); enemies.remove(e); g.bonus += 100; set_msg("COP WRECKED +$100", 30); sfx(220, 120)
 for c in civs[:]:
  if c.hp <= 0:
   if g.etar is c: g.etar, g.entering = None, 0
   boom(c.x, c.y, 12); civs.remove(c); sfx(200, 100)
 p = g.p
 for q in pick[:]:
  q[3] -= 1
  if q[3] <= 0: pick.remove(q)
  elif d2(p, q[0], q[1]) < 40:
   pick.remove(q); g.bonus += 10; sfx(1000, 80)
   if q[2]: g.lives = min(g.lives + 1, 3); p.hp = float(TYPES[p.t][5]); set_msg("+LIFE & REPAIRED!", 40)
   else: g.bonus += 250; set_msg("+$250 LOOT!", 40)
def manage_spawns():
 p, f = g.p, g.frame; sec = f // 30
 lvl = sum(1 for t in LV if sec >= t) + max(0, sec - 180) // 50
 if lvl > g.lvl: g.lvl = lvl; set_msg(MSG[lvl] if lvl < 8 else "HEAT %d!" % lvl, 70); sfx(1200, 200)
 if f % 15 == 0:
  if f > 60 and len(enemies) < 14:
   w = (min(1 + lvl, 7), min((lvl - 1) // 2, 3) if lvl > 2 else 0, min((lvl - 2) // 2, 3) if lvl > 3 else 0, 0 if lvl < 5 else (1 if lvl < 8 else 2))
   cnt = [0, 0, 0, 0]
   for e in enemies: cnt[e.t - 4] += 1
   for k in range(4):
    if cnt[k] < w[k]: spawn_enemy(4 + k); break
  for e in enemies[:]:
   if d2(e, p.x, p.y) > 22500 or e.spin > 5: enemies.remove(e)
  for c in civs[:]:
   if d2(c, g.camx, g.camy) > 19000 and c is not g.etar: civs.remove(c)
 if f % 8 == 0: spawn_civ(False)
 if f % 90 == 45 and len(pick) < 4: spawn_pick()
 if g.lvl > 2 and f % max(330 - 25 * g.lvl, 130) == 100: spawn_block()
 if f % 20 == 0 and enemies and d2(enemies[0], p.x, p.y) < 3600: sfx(700 + ((f // 20) & 1) * 250, 90)
def update_bust():
 p = g.p; inc, near = 0.0, 0
 for e in enemies:
  dd = d2(e, p.x, p.y)
  if e.t == HELI: inc += .2 if dd < 49 else 0
  elif dd < 196: near += 1
 slow = g.onfoot or p.vx * p.vx + p.vy * p.vy < 2.6
 if near >= 2 or (near and slow):
  inc += near * (.9 if slow else .5) * (.5 + .06 * min(g.lvl, 10))
  if near >= 2 and g.msgt == 0: set_msg("BOXED IN!", 20)
 g.bust = g.bust + inc if inc > 0 else max(g.bust - .8, 0.0)
def lose_life(why):
 global hi
 g.lives -= 1; p = g.p; boom(p.x, p.y, 15); sfx(100, 300)
 if g.lives <= 0:
  g.reason, g.newbest = why, g.score > hi
  if g.newbest:
   hi = g.score
   try: thumby.saveData.setItem("hi", hi); thumby.saveData.save()
   except: pass
  g.state, g.overt, g.shake = 2, 0, 8; return
 for e in enemies[:]:
  if d2(e, p.x, p.y) < 6400: enemies.remove(e)
 y = p.y
 while solid(sfloor(p.x) * P + 7.0, y): y += 6
 g.p = Car(random.choice((0, 0, 1, 3)), sfloor(p.x) * P + 7.0, y, -pi / 2); g.onfoot = g.exiting = False
 g.entering, g.etar, g.bust, g.inv, g.shake = 0, None, 0.0, 90, 6; set_msg("%d LIVES LEFT" % g.lives if g.lives > 1 else "LAST LIFE!", 70)
def play_step():
 g.frame += 1; p = g.p
 if g.frame in (80, 160) and not g.onfoot: set_msg(("A DRIFT  B BRAKE", "UP = BAIL OUT")[g.frame // 160], 60)
 if g.onfoot: update_man(p)
 else: update_driving(p)
 for e in enemies: update_enemy(e)
 update_civs(); hp0 = p.hp; collisions()
 if g.inv: p.hp = hp0
 cleanup(); update_parts(); manage_spawns()
 if g.inv: g.inv, g.bust = g.inv - 1, 0.0
 else: update_bust()
 g.msgt, g.shake = max(g.msgt - 1, 0), max(g.shake - 1, 0); p = g.p
 if p.hp <= 0 and not g.onfoot:
  boom(p.x, p.y, 14); sfx(120, 200); g.p = p = Car(MAN, p.x, p.y, p.ang); p.hp = 4.0
  g.onfoot, g.exiting, g.shake = True, False, 6; set_msg("WRECKED! RUN!", 70)
 g.camx += (p.x + p.vx * 9 - g.camx) * .18; g.camy += (p.y + p.vy * 9 - g.camy) * .18; g.score = g.frame // 3 + int(g.bonus)
 if p.hp <= 0: lose_life("KILLED!")
 elif g.bust >= 100: lose_life("BUSTED!")
def blit(s, x, y, f=0):
 if s[4] is not None: disp.blit(s[4], x, y, s[0], s[1], 1, f, 0)
 disp.blit(s[5], x, y, s[0], s[1], 0, f, 0)
def draw_man(x, y, mv):
 frect(x - 1, y - 6, 3, 7, 0)
 for q in ((0, -5), (-1, -4), (0, -4), (1, -4), (0, -3), (0, -2)): px(x + q[0], y + q[1], 1)
 if mv and (int(g.step) // 3) & 1: px(x - 1, y - 1, 1), px(x + 1, y, 1)
 elif mv: px(x + 1, y - 1, 1), px(x - 1, y, 1)
 else: px(x - 1, y, 1), px(x + 1, y, 1)
def ekey(x, y):
 cx, cy = x // P, y // P; lx, ly = x - cx * P, y - cy * P
 return int(cx + cy) * 10000 + int(lx + ly) + (2000 if lx >= RW and ly >= RW else 0)
def heart(x, y): px(x, y, 1), px(x + 2, y, 1), frect(x, y + 1, 3, 1, 1), px(x + 1, y + 2, 1)
def scene():
 cx0, cy0 = sfloor(CX), sfloor(CY); keys, objs = [], []; p, f = g.p, g.frame
 for cy in range(cy0 - 2, cy0 + 3):
  for cx in range(cx0 - 2, cx0 + 3):
   ix, iy = sc(cx * P, cy * P); b = block(cx, cy)
   if ix + 33 > 0 and ix - 32 < W and iy + 34 > 0 and iy < H: disp.blit(spr(1, b[3])[5], ix - 32, iy, 65, 34, 0, 0, 0)
   s = spr(0, b[0]); bx, by = ix - s[2], iy + 11 - s[3]
   if bx < W and bx + s[0] > 0 and by < H and by + s[1] > 0: keys.append((cx + cy) * 10000 + 1000); objs.append((0, s, bx, by, b[1]))
   for o in ((0, 1) if b[4] & g.cm else ()):
    if (b[4] & g.cm) >> o & 1:
     wx, wy = (cx * P, cy * P + 26) if o == 0 else (cx * P + 26, cy * P); sx, sy = sc(wx, wy); s = spr(3, o)
     if -20 < sx < 92 and -16 < sy < 56: keys.append(ekey(wx + (7 if o == 0 else 2.5), wy + (2.5 if o == 0 else 7))); objs.append((0, s, sx - s[2], sy - s[3], 0))
 ents = [(1, c, 0) for c in civs] + [(1, c, 0) for c in enemies if c.t != HELI]
 if not g.inv or (f >> 1) & 1: ents.append((2, p, 0) if g.onfoot else (1, p, 1))
 for o in ents:
  ob = o[1]; sx, sy = sc(ob.x, ob.y)
  if -16 < sx < 88 and -16 < sy < 58: keys.append(ekey(ob.x, ob.y) + (1 if ob is p else 0)); objs.append((o[0], ob, o[2], sx, sy))
 for i in sorted(range(len(keys)), key=lambda i: keys[i]):
  o = objs[i]
  if o[0] == 0: blit(o[1], o[2], o[3], o[4])
  elif o[0] == 2: draw_man(o[3], o[4], o[1].vx * o[1].vx + o[1].vy * o[1].vy > .04)
  else:
   c, t, sx, sy = o[1], o[1].t, o[3], o[4]; s = spr(2, t, int(c.ang * 5.093 + 64.5) & 31, o[2]); x0, y0 = sx - s[2], sy - s[3]
   for hx, hy in ((1, 0), (-1, 0), (0, 1), (0, -1)): disp.blit(s[4], x0 + hx, y0 + hy, s[0], s[1], 1, 0, 0)
   blit(s, x0, y0)
   if COP <= t <= FBI: zy = sy - int(CD[t][1] * KZ + .5); px(sx - 1, zy, (f // 4) & 1), px(sx + 1, zy, 1 - ((f // 4) & 1))
 for q in pick:
  if q[3] > 150 or (f >> 2) & 1:
   sx, sy = sc(q[0], q[1]); sy -= 6 + ((f >> 3) & 1); frect(sx - 2, sy - 2, 5, 5, 0)
   if q[2]: heart(sx - 1, sy - 1)
   else: px(sx, sy - 2, 1), frect(sx - 1, sy - 1, 3, 3, 1), px(sx, sy, 0)
 for c in enemies:
  sx, sy = sc(c.x, c.y)
  if c.t == HELI:
   px(sx - 2, sy, 1), px(sx + 2, sy, 1), px(sx, sy + 1, 1); hy = sy - 13; frect(sx - 2, hy - 2, 5, 4, 0)
   for r in (f * .9, f * .9 + 1.57): disp.drawLine(int(sx - cos(r) * 5), int(hy - sin(r) * 2.5), int(sx + cos(r) * 5), int(hy + sin(r) * 2.5), 1)
   frect(sx - 1, hy - 1, 3, 2, 1)
  if (f >> 2) & 1 and not (0 <= sx < W and 0 <= sy < H) and -50 < sx < 120 and -40 < sy < 80: px(min(max(sx, 0), W - 1), min(max(sy, 0), H - 1), 1)
 for q in parts:
  if q[6] > 4 or (q[6] & 1): sx, sy = sc(q[0], q[1]); px(sx, int(sy - q[2] * KZ), 1)
 n = g.near
 if g.onfoot and n is not None and (f // 5) & 1: sx, sy = sc(n.x, n.y); px(sx, sy - 10, 1), px(sx - 1, sy - 11, 1), px(sx + 1, sy - 11, 1)
def draw_hud():
 p = g.p; frac = max(0.0, min(1.0, p.hp / TYPES[p.t][5])); f = g.frame
 frect(0, 0, 24, 10, 0); box(0, 0, 22, 4); box(0, 5, 22, 4)
 if frac >= .3 or (f // 4) & 1: frect(1, 1, int(20 * frac), 2, 1)
 if g.bust < 60 or (f // 3) & 1: frect(1, 6, int(20 * g.bust / 100), 2, 1)
 frect(25, 0, g.lives * 4 + 1, 4, 0)
 for i in range(g.lives): heart(26 + i * 4, 0)
 for s, y in ((tstr(f), 0), ("$" + str(g.score), 35)): x = W - len(s) * 4; frect(x - 1, y - (y > 0), W - x + 1, 6, 0); disp.drawText(s, x, y, 1)
 hl = min(g.lvl, 9); frect(0, 35, hl * 4 + 2, 5, 0)
 for i in range(hl):
  if i < hl - 1 or g.msgt == 0 or (f // 3) & 1: frect(i * 4 + 1, 36, 3, 3, 1)
 if g.msgt > 0: x = (W - len(g.msg) * 4 + 1) // 2; frect(x - 2, 27, len(g.msg) * 4 + 3, 7, 0); disp.drawText(g.msg, x, 28, 1)
def draw_play():
 global CX, CY
 sh = (random.random() - .5) * 2 * (g.shake > 0); CX, CY = g.camx + sh, g.camy + sh; scene()
 if g.state == 1: draw_hud()
def title():
 global CX, CY
 g.frame += 1; f = g.frame; g.camy -= 1.5; CX, CY = 7.0, g.camy
 g.p, g.onfoot = Car(1, 7.0 + sin(f * .1) * 2.4, CY - 8, -pi / 2 + cos(f * .1) * .35), False; del enemies[:]
 for k in range(2): enemies.append(Car(COP, 7.0 + sin(f * .08 + k * 2.0) * 3, CY + 8 + k * 13, -pi / 2 + cos(f * .08 + k * 2.0) * .3))
 if f & 1: puff(g.p.x, g.p.y + 3, 0.0, .3, 10, .1, .5)
 update_parts(); scene(); frect(0, 0, W, 13, 0); frect(0, 29, W, 11, 0)
 text_c("BANK ROBBER", 1); text_c("GETAWAY 3D", 7); text_c("BEST $%d" % hi, 35)
 if (f // 15) & 1: text_c("A:START", 30)
def gameover():
 g.overt += 1; update_parts(); draw_play(); frect(4, 1, 64, 38, 0); box(4, 1, 64, 38)
 for s, y in (("GAME OVER", 3), (g.reason, 9), ("LOOT $%d" % g.score, 16), ("NEW BEST!" if g.newbest else "BEST $%d" % hi, 22), ("TIME " + tstr(g.frame), 28)): text_c(s, y)
 if g.overt > 30 and (g.overt // 12) & 1: text_c("A:RETRY", 34)
def main():
 global hi
 try:
  thumby.saveData.setName("EscapeRoadCity3D")
  if thumby.saveData.hasItem("hi"): hi = thumby.saveData.getItem("hi")
 except: pass
 reset()
 while True:
  disp.fill(0); a = thumby.buttonA.pressed(); ae = a and not g.a_prev; g.a_prev = a
  if g.state == 0: title(); ae and start()
  elif g.state == 1: play_step(); draw_play()
  else: gameover(); ae and g.overt > 30 and start()
  disp.update()
main()
