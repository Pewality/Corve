# Thumby Sandbox - falling sand toy. D-pad move, A paint, B tap = menu.
# Picker: hold B (shows while held) or press A+B to toggle it on/off.
# In the picker: up/down = LIQUIDS/SOLIDS/GASES/TOOLS, left/right = pick.
# Add reactions: react(a, b, new_a, new_b, mask)
import os
import time
import micropython
import thumby
from array import array
from random import getrandbits
W = 72
H = 40
N = W * H
EMPTY, SAND, WATER, WALL, FIRE, PLANT, OIL, STEAM, DIRT = 0, 1, 2, 3, 4, 5, 6, 7, 8
MUD, LAVA, STONE, GLASS, SALT, BRINE, ICE = 9, 10, 11, 12, 13, 14, 15
MOLTEN_GLASS, MUDSTONE, MOLTEN_DIRT = 16, 17, 18
ACID, SMOKE, METAL, RUST, GUNPOWDER = 19, 20, 21, 22, 23
SNOW, CLOUD, SEED, WOOD, CRYO = 24, 25, 26, 27, 28
MOLTEN_SALT, CAST_IRON, MOLTEN_IRON = 29, 30, 31
HEAT, COOL = 32, 33
MAXMAT = 31
NAMES = ("ERASE", "SAND", "WATER", "WALL", "FIRE", "PLANT", "OIL", "STEAM",
 "DIRT", "MUD", "LAVA", "STONE", "GLASS", "SALT", "BRINE", "ICE",
 "MOLTEN GLASS", "MUDSTONE", "MOLTEN DIRT", "ACID", "SMOKE", "METAL",
 "RUST", "GUNPOWDER", "SNOW", "CLOUD", "SEED", "WOOD", "CRYO",
 "MOLTEN SALT", "CAST IRON", "MOLTEN IRON", "HEAT", "COOL")
CAT_NAMES = ("LIQUIDS", "SOLIDS", "GASES", "TOOLS")
CAT_TABS = ("LIQ", "SOL", "GAS", "TOOL")
CATS = (
 (WATER, BRINE, ACID, OIL, CRYO, LAVA, MOLTEN_GLASS, MOLTEN_DIRT,
 MOLTEN_SALT, MOLTEN_IRON),
 (SAND, DIRT, MUD, MUDSTONE, SEED, SNOW, ICE, SALT, PLANT, WOOD, METAL,
 CAST_IRON, RUST, GUNPOWDER, WALL, STONE, GLASS),
 (STEAM, SMOKE, CLOUD, FIRE),
 (HEAT, COOL, EMPTY),
 )
SPEED_ACC = (1, 2, 4, 8, 16, 32, 64)
SPEED_NAMES = ("1/8x", "1/4x", "1/2x", "1x", "2x", "4x", "8x")
CURSOR_SPEEDS = ((12, 4, 1), (8, 2, 1), (6, 1, 1), (6, 1, 2))
CURSOR_NAMES = ("SLOW", "NORM", "FAST", "MAX")
SAVE_DIR = "/Saves/Sandbox"
D_OFF, K_OFF, S_OFF = 0, 32, 64
RA_OFF, RB_OFF, RP_OFF = 96, 1120, 2144
PAT_OFF, RND_OFF, TICK_OFF = 3168, 3680, 3936
HOT_OFF, HOTTO_OFF, COLD_OFF, COLDTO_OFF = 3937, 3969, 4001, 4033
TM_OFF = 4065
T = bytearray(TM_OFF + N + 32)
for _m, _d in ((OIL, 1), (WATER, 2), (BRINE, 3), (LAVA, 4),
 (SAND, 5), (DIRT, 5), (MUD, 5), (SALT, 5),
 (MOLTEN_GLASS, 4), (MOLTEN_DIRT, 4), (ACID, 3), (CRYO, 3),
 (RUST, 5), (GUNPOWDER, 5), (SNOW, 2), (SEED, 5),
 (METAL, 15), (WOOD, 15), (CAST_IRON, 15), (MOLTEN_SALT, 3),
 (MOLTEN_IRON, 6),
 (WALL, 15), (PLANT, 15), (STONE, 15), (GLASS, 15), (MUDSTONE, 15)):
 T[D_OFF + _m] = _d
for _m in (SAND, DIRT, MUD, SALT, RUST, GUNPOWDER, SNOW, SEED):
 T[K_OFF + _m] = 1
for _m in (WATER, OIL, LAVA, BRINE, MOLTEN_GLASS, MOLTEN_DIRT, ACID, CRYO,
 MOLTEN_SALT, MOLTEN_IRON):
 T[K_OFF + _m] = 2
for _m in (STEAM, SMOKE, CLOUD):
 T[K_OFF + _m] = 3
T[K_OFF + FIRE] = 4
for _m, _s in ((DIRT, 1), (MUD, 3), (OIL, 1), (LAVA, 3), (MOLTEN_GLASS, 7),
 (MOLTEN_DIRT, 3), (RUST, 1), (SNOW, 1), (MOLTEN_SALT, 1),
 (MOLTEN_IRON, 3)):
 T[S_OFF + _m] = _s
AMBIENT = 14
def deg(t):
 return t * 5 - 50
for _m, _at, _to in ((WATER, 30, STEAM), (BRINE, 30, STEAM), (ICE, 14, WATER),
 (OIL, 40, FIRE), (PLANT, 40, FIRE),
 (MUD, 30, MUDSTONE),
 (STONE, 220, LAVA),
 (SAND, 240, MOLTEN_GLASS), (GLASS, 240, MOLTEN_GLASS),
 (DIRT, 225, MOLTEN_DIRT), (MUDSTONE, 225, MOLTEN_DIRT),
 (SNOW, 12, WATER), (WOOD, 50, FIRE), (GUNPOWDER, 40, FIRE),
 (SEED, 40, FIRE), (CRYO, 8, SMOKE), (ACID, 30, SMOKE),
 (SALT, 180, MOLTEN_SALT),
 (METAL, 220, CAST_IRON),
 (CAST_IRON, 240, MOLTEN_IRON),
 (RUST, 225, MOLTEN_IRON)):
 T[HOT_OFF + _m] = _at
 T[HOTTO_OFF + _m] = _to
for _m, _at, _to in ((WATER, 10, ICE), (BRINE, 5, ICE), (LAVA, 120, STONE),
 (STEAM, 5, WATER),
 (MOLTEN_GLASS, 160, GLASS), (MOLTEN_DIRT, 150, DIRT),
 (MOLTEN_SALT, 120, SALT), (MOLTEN_IRON, 160, CAST_IRON)):
 T[COLD_OFF + _m] = _at
 T[COLDTO_OFF + _m] = _to
DEFT = {FIRE: 130, LAVA: 210, STEAM: 40, ICE: 0, MOLTEN_GLASS: 245,
 MOLTEN_DIRT: 235, SNOW: 0, CRYO: 0, SMOKE: 30, MOLTEN_SALT: 190,
 MOLTEN_IRON: 245}
AMB = bytes((AMBIENT,)) * N
T[TM_OFF:TM_OFF + N] = AMB
for _i in range(1024):
 T[RA_OFF + _i] = 255
 T[RB_OFF + _i] = 255
for _i in range(256):
 T[RND_OFF + _i] = getrandbits(8)
def react(a, b, ra=255, rb=255, mask=0):
 T[RA_OFF + a * 32 + b] = ra
 T[RB_OFF + a * 32 + b] = rb
 T[RP_OFF + a * 32 + b] = mask
FLAM_OFF = TM_OFF + N
for _i in range(32):
 T[FLAM_OFF + _i] = 255
for _m, _mk in ((PLANT, 1), (OIL, 1), (WOOD, 3), (GUNPOWDER, 0), (SEED, 1)):
 T[FLAM_OFF + _m] = _mk
react(DIRT, WATER, MUD, EMPTY, 7)
react(WATER, DIRT, EMPTY, MUD, 7)
react(SALT, WATER, EMPTY, BRINE, 3)
react(WATER, SALT, BRINE, EMPTY, 3)
react(FIRE, WATER, STEAM, 255, 0)
react(FIRE, BRINE, STEAM, 255, 0)
react(WATER, FIRE, STEAM, 255, 7)
react(BRINE, FIRE, SALT, 255, 7)
react(PLANT, LAVA, FIRE, 255, 0)
react(OIL, LAVA, FIRE, 255, 0)
react(MUD, FIRE, MUDSTONE, 255, 3)
react(MUD, LAVA, MUDSTONE, 255, 1)
react(LAVA, WATER, STONE, STEAM, 1)
react(WATER, LAVA, STEAM, STONE, 1)
react(LAVA, BRINE, STONE, STEAM, 1)
react(BRINE, LAVA, STEAM, STONE, 1)
react(LAVA, SAND, 255, GLASS, 7)
react(MOLTEN_IRON, WATER, CAST_IRON, STEAM, 1)
react(WATER, MOLTEN_IRON, STEAM, CAST_IRON, 1)
react(MOLTEN_IRON, BRINE, CAST_IRON, STEAM, 1)
react(BRINE, MOLTEN_IRON, STEAM, CAST_IRON, 1)
react(MOLTEN_IRON, ICE, CAST_IRON, STEAM, 0)
react(MOLTEN_IRON, SNOW, CAST_IRON, STEAM, 0)
react(CRYO, MOLTEN_IRON, SMOKE, CAST_IRON, 0)
react(MOLTEN_SALT, WATER, SALT, STEAM, 1)
react(WATER, MOLTEN_SALT, STEAM, SALT, 1)
react(MOLTEN_SALT, ICE, SALT, STEAM, 0)
react(CRYO, MOLTEN_SALT, SMOKE, SALT, 0)
for _m, _mk in ((PLANT, 0), (OIL, 0), (WOOD, 3), (GUNPOWDER, 0), (SEED, 0)):
 react(_m, MOLTEN_IRON, FIRE, 255, _mk)
react(CAST_IRON, WATER, RUST, 255, 127)
react(CAST_IRON, BRINE, RUST, 255, 31)
react(SAND, LAVA, GLASS, 255, 7)
for _m, _mk in ((DIRT, 3), (SAND, 7), (PLANT, 1), (WOOD, 3), (METAL, 3),
 (RUST, 1), (STONE, 15), (MUDSTONE, 15), (MUD, 3), (SEED, 1),
 (SALT, 3), (ICE, 3), (CAST_IRON, 7)):
 react(ACID, _m, SMOKE, EMPTY, _mk)
react(ACID, WATER, WATER, 255, 15)
react(ACID, BRINE, BRINE, 255, 15)
react(METAL, WATER, RUST, 255, 63)
react(METAL, BRINE, RUST, 255, 15)
react(GUNPOWDER, LAVA, FIRE, 255, 0)
react(GUNPOWDER, WATER, MUD, EMPTY, 7)
react(WOOD, LAVA, FIRE, 255, 3)
react(SEED, MUD, PLANT, 255, 3)
react(SEED, LAVA, FIRE, 255, 0)
react(SNOW, SALT, WATER, 255, 3)
react(ICE, SALT, WATER, 255, 7)
react(SNOW, FIRE, WATER, 255, 0)
react(SNOW, LAVA, STEAM, 255, 0)
react(LAVA, ICE, STONE, STEAM, 0)
react(CLOUD, EMPTY, 255, WATER, 255)
react(SMOKE, EMPTY, EMPTY, 255, 255)
react(FIRE, EMPTY, SMOKE, 255, 31)
react(CRYO, WATER, 255, ICE, 1)
react(CRYO, BRINE, 255, ICE, 3)
react(CRYO, STEAM, 255, WATER, 0)
react(CRYO, FIRE, 255, EMPTY, 0)
react(CRYO, LAVA, SMOKE, STONE, 0)
react(PLANT, BRINE, EMPTY, 255, 63)
TILES = {
 SAND: "0111 1011 1101 1110",
 DIRT: "1100 0011 1100 0011",
 MUD: "1110 0111 1011 1101",
 WATER: "1010 0101 1010 0101",
 BRINE: "1010 0111 1010 1101",
 OIL: "1010 0000 1010 0000",
 SALT: "0100 0001 1000 0010",
 PLANT: "1010 1010 1010 1010",
 WALL: "1111 1111 1111 1111",
 STONE: "1111 1011 1111 1101",
 GLASS: "1000 0100 0010 0001",
 ICE: "1111 0101 1111 1010",
 MOLTEN_GLASS: "1110 1111 0111 1111",
 MUDSTONE: "1111 1010 1111 0101",
 MOLTEN_DIRT: "1111 1101 1111 1011",
 MOLTEN_SALT: "1011 1110 1101 0111",
 CAST_IRON: "1111 1101 1011 1111",
 MOLTEN_IRON: "2222 2222 2222 2222",
 ACID: "1001 0110 0110 1001",
 SMOKE: "2222 2222 2222 2222",
 METAL: "1111 1001 1001 1111",
 RUST: "1101 0111 1011 1110",
 GUNPOWDER: "1010 0100 1010 0001",
 SNOW: "1010 0000 0101 0000",
 CLOUD: "0110 1111 1111 0110",
 SEED: "0100 0000 0010 0000",
 WOOD: "1011 1011 1011 1011",
 CRYO: "1001 0000 0110 0000",
 FIRE: "2222 2222 2222 2222",
 LAVA: "2222 2222 2222 2222",
 STEAM: "2222 2222 2222 2222",
 }
for _m in TILES:
 _rows = TILES[_m].split(" ")
 for _j in range(4):
  for _i in range(4):
   T[PAT_OFF + _m * 16 + _j * 4 + _i] = int(_rows[_j][_i])
grid = bytearray(N)
ZERO = bytes(N)
st = array("I", [(time.ticks_us() | 1) & 0x3FFFFFFF, 0])
display = thumby.display
try:
 FB = display.display.buffer
 if len(FB) != (W * H) // 8:
  FB = None
except Exception:
 FB = None
@micropython.viper
def _powder(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 tick = s[1]
 s[1] = tick + 1
 alt = tick & 1
 y = 38
 while y >= 0:
  base = y * 72
  xi = 0
  while xi < 72:
   if alt != 0:
    x = xi
   else:
    x = 71 - xi
   xi += 1
   i = base + x
   c = g[i]
   if T[32 + c] != 1:
    continue
   d = i + 72
   m = -1
   if T[c] > T[g[d]]:
    m = d
   else:
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    if ((r >> 2) & T[64 + c]) == 0:
     if (r & 1) != 0:
      dx = 1
     else:
      dx = -1
     nx = x + dx
     if nx >= 0 and nx < 72:
      if T[c] > T[g[d + dx]]:
       m = d + dx
   if m >= 0:
    t = g[m]
    g[m] = c
    g[i] = t
    a = T[4065 + m]
    T[4065 + m] = T[4065 + i]
    T[4065 + i] = a
  y -= 1
 s[0] = rs
@micropython.viper
def _liquid(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 alt = s[1] & 1
 y = 38
 while y >= 0:
  base = y * 72
  xi = 0
  while xi < 72:
   if alt != 0:
    x = 71 - xi
   else:
    x = xi
   xi += 1
   i = base + x
   c = g[i]
   if T[32 + c] != 2:
    continue
   d = i + 72
   m = -1
   if T[c] > T[g[d]]:
    m = d
   else:
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    if ((r >> 2) & T[64 + c]) == 0:
     if (r & 1) != 0:
      dx = 1
     else:
      dx = -1
     nx = x + dx
     if nx >= 0 and nx < 72:
      if T[c] > T[g[d + dx]]:
       m = d + dx
      elif T[g[i + dx]] == 0:
       m = i + dx
   if m >= 0:
    t = g[m]
    g[m] = c
    g[i] = t
    a = T[4065 + m]
    T[4065 + m] = T[4065 + i]
    T[4065 + i] = a
  y -= 1
 s[0] = rs
@micropython.viper
def _gas(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 y = 0
 while y < 40:
  base = y * 72
  x = 0
  while x < 72:
   i = base + x
   c = g[i]
   if T[32 + c] == 3:
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    m = -1
    if y > 0 and ((r >> 4) & 3) != 0:
     t = g[i - 72]
     if t == 0 or T[32 + t] == 2:
      m = i - 72
    if m < 0:
     if ((r >> 6) & 1) != 0:
      dx = 1
     else:
      dx = -1
     nx = x + dx
     if nx >= 0 and nx < 72 and g[i + dx] == 0:
      m = i + dx
    if m >= 0:
     t = g[m]
     g[m] = c
     g[i] = t
     a = T[4065 + m]
     T[4065 + m] = T[4065 + i]
     T[4065 + i] = a
   x += 1
  y += 1
 s[0] = rs
@micropython.viper
def _fire(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 y = 0
 while y < 40:
  base = y * 72
  x = 0
  while x < 72:
   i = base + x
   if g[i] == 4:
    T[4065 + i] = 130
    k = 0
    while k < 4:
     j = -1
     if k == 0:
      if y < 39:
       j = i + 72
     elif k == 1:
      if y > 0:
       j = i - 72
     elif k == 2:
      if x < 71:
       j = i + 1
     else:
      if x > 0:
       j = i - 1
     if j >= 0:
      f = T[6945 + g[j]]
      if f != 255:
       rs ^= rs << 13
       rs ^= (rs >> 17) & 0x7FFF
       rs ^= rs << 5
       if (rs & f) == 0:
        g[j] = 4
     k += 1
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    m = -1
    if (r & 15) == 0:
     g[i] = 0
    elif y > 0 and g[i - 72] == 0 and ((r >> 8) & 3) == 0:
     m = i - 72
    elif ((r >> 10) & 3) == 0:
     if ((r >> 9) & 1) != 0:
      dx = 1
     else:
      dx = -1
     nx = x + dx
     if nx >= 0 and nx < 72 and g[i + dx] == 0:
      m = i + dx
    if m >= 0:
     g[m] = 4
     g[i] = 0
     a = T[4065 + m]
     T[4065 + m] = T[4065 + i]
     T[4065 + i] = a
   x += 1
  y += 1
 s[0] = rs
@micropython.viper
def _react(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 y = 0
 while y < 40:
  base = y * 72
  x = 0
  while x < 72:
   i = base + x
   c = g[i]
   if c != 0:
    rep = 0
    while rep < 2:
     rep += 1
     rs ^= rs << 13
     rs ^= (rs >> 17) & 0x7FFF
     rs ^= rs << 5
     r = rs
     k = (r >> 3) & 3
     j = -1
     if k == 0 and y < 39:
      j = i + 72
     elif k == 1 and y > 0:
      j = i - 72
     elif k == 2 and x < 71:
      j = i + 1
     elif k == 3 and x > 0:
      j = i - 1
     if j >= 0:
      c = g[i]
      idx = c * 32 + g[j]
      ra = T[96 + idx]
      rb = T[1120 + idx]
      if ra != 255 or rb != 255:
       if ((r >> 5) & T[2144 + idx]) == 0:
        if ra != 255:
         g[i] = ra
        if rb != 255:
         g[j] = rb
   x += 1
  y += 1
 s[0] = rs
@micropython.viper
def _plant(g: ptr8, s: ptr32):
 rs = s[0]
 y = 0
 while y < 40:
  base = y * 72
  x = 0
  while x < 72:
   i = base + x
   if g[i] == 5:
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    if (r & 15) == 0:
     q = i
     h = 0
     while h < 9 and q < 2808 and g[q + 72] == 5:
      q += 72
      h += 1
     wet = 0
     if q < 2808:
      b = g[q + 72]
      if b == 9:
       wet = 1
      elif b == 8:
       p = q + 72
       if x > 0 and g[p - 1] == 2:
        wet = 1
       if x < 71 and g[p + 1] == 2:
        wet = 1
       if p < 2808 and g[p + 72] == 2:
        wet = 1
     if wet == 0:
      if x > 0 and g[q - 1] == 9:
       wet = 1
      if x < 71 and g[q + 1] == 9:
       wet = 1
     if wet != 0 and h < 6:
      k = (r >> 4) & 3
      if k < 2:
       if y > 0 and g[i - 72] == 0 and ((r >> 6) & 1) == 0:
        g[i - 72] = 5
      elif h >= 1 and ((r >> 6) & 3) == 0:
       if k == 2:
        if x < 71 and g[i + 1] == 0:
         g[i + 1] = 5
       else:
        if x > 0 and g[i - 1] == 0:
         g[i - 1] = 5
   x += 1
  y += 1
 s[0] = rs
@micropython.viper
def _heat(g: ptr8, s: ptr32, T: ptr8):
 rs = s[0]
 y = 0
 while y < 40:
  base = y * 72
  x = 0
  while x < 72:
   i = base + x
   if g[i] == 0:
    T[4065 + i] = 14
   else:
    rs ^= rs << 13
    rs ^= (rs >> 17) & 0x7FFF
    rs ^= rs << 5
    r = rs
    k = (r >> 3) & 3
    j = -1
    if k == 0 and y < 39:
     j = i + 72
    elif k == 1 and y > 0:
     j = i - 72
    elif k == 2 and x < 71:
     j = i + 1
    elif k == 3 and x > 0:
     j = i - 1
    if j >= 0:
     ti = T[4065 + i]
     if g[j] == 0:
      if ((r >> 8) & 3) == 0:
       d = ti - 14
       if d > 0:
        T[4065 + i] = ti - ((d + 63) >> 6)
       else:
        T[4065 + i] = ti + ((63 - d) >> 6)
     else:
      tj = T[4065 + j]
      if tj > ti + 2:
       dl = (tj - ti + 1) >> 2
       T[4065 + i] = ti + dl
       T[4065 + j] = tj - dl
      elif ti > tj + 2:
       dl = (ti - tj + 1) >> 2
       T[4065 + i] = ti - dl
       T[4065 + j] = tj + dl
   x += 1
  y += 1
 s[0] = rs
@micropython.viper
def _phase(g: ptr8, T: ptr8):
 i = 0
 while i < 2880:
  c = g[i]
  if c != 0:
   tm = T[4065 + i]
   h = T[3937 + c]
   if h != 0 and tm >= h:
    g[i] = T[3969 + c]
   elif tm < T[4001 + c]:
    g[i] = T[4033 + c]
  i += 1
def step(g, s):
 _powder(g, s, T)
 _liquid(g, s, T)
 _gas(g, s, T)
 _fire(g, s, T)
 _react(g, s, T)
 _plant(g, s)
 if s[1] & 1:
  _heat(g, s, T)
  _phase(g, T)
@micropython.viper
def render(g: ptr8, buf: ptr8, T: ptr8):
 t = T[3936]
 y = 0
 while y < 40:
  row = (y >> 3) * 72
  bit = 1 << (y & 7)
  yy = (y & 3) << 2
  x = 0
  while x < 72:
   c = g[y * 72 + x]
   if c != 0:
    on = T[3168 + c * 16 + yy + (x & 3)]
    if on == 2:
     rv = T[3680 + ((x * 29 + y * 61 + t * 97) & 255)]
     on = 0
     if c == 4 or c == 20:
      if (rv & 1) != 0:
       on = 1
     elif c == 10 or c == 31:
      if (rv & 7) != 0:
       on = 1
     elif (rv & 3) == 0:
      on = 1
    if on != 0:
     buf[row + x] = buf[row + x] | bit
   x += 1
  y += 1
def render_slow():
 px = display.setPixel
 for y in range(H):
  for x in range(W):
   if grid[y * W + x]:
    px(x, y, 1)
def draw_world(frame):
 display.fill(0)
 if FB is not None:
  T[TICK_OFF] = frame & 255
  render(grid, FB, T)
 else:
  render_slow()
def paint(cx, cy, r, mat):
 sparse = r > 0 and mat < HEAT and T[K_OFF + mat] != 0
 rr = r * r + 1
 for yy in range(cy - r, cy + r + 1):
  if yy < 0 or yy >= H:
   continue
  for xx in range(cx - r, cx + r + 1):
   if xx < 0 or xx >= W:
    continue
   dx = xx - cx
   dy = yy - cy
   if dx * dx + dy * dy > rr:
    continue
   if sparse and getrandbits(1):
    continue
   i = yy * W + xx
   if mat == HEAT:
    if grid[i]:
     T[TM_OFF + i] = min(255, T[TM_OFF + i] + 8)
   elif mat == COOL:
    if grid[i]:
     T[TM_OFF + i] = max(0, T[TM_OFF + i] - 8)
   elif mat == EMPTY:
    grid[i] = 0
    T[TM_OFF + i] = AMBIENT
   elif grid[i] == 0:
    grid[i] = mat
    T[TM_OFF + i] = DEFT.get(mat, AMBIENT)
def pset(x, y):
 if 0 <= x < W and 0 <= y < H:
  display.setPixel(x, y, 1)
def draw_cursor(cx, cy, r):
 if r == 0:
  pset(cx, cy)
  return
 x0, y0, x1, y1 = cx - r, cy - r, cx + r, cy + r
 for x in range(x0, x1 + 1):
  pset(x, y0)
  pset(x, y1)
 for y in range(y0 + 1, y1):
  pset(x0, y)
  pset(x1, y)
GLYPHS = {
 "A": "010101111101101", "B": "110101110101110", "C": "011100100100011",
 "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
 "G": "011100101101011", "H": "101101111101101", "I": "111010010010111",
 "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
 "M": "101111111101101", "N": "111101101101101", "O": "010101101101010",
 "P": "110101110100100", "Q": "010101101111011", "R": "110101110101101",
 "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
 "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
 "Y": "101101010010010", "Z": "111001010100111",
 "0": "111101101101111", "1": "010110010010111", "2": "110001010100111",
 "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
 "6": "011100111101111", "7": "111001010100100", "8": "111101111101111",
 "9": "111101111001110", "-": "000000111000000", "+": "000010111010000",
 }
def tiny_width(text):
 return len(text) * 4 - 1
def tiny_text(text, x, y, col=1):
 px = display.setPixel
 for ch in text:
  gl = GLYPHS.get(ch)
  if gl:
   for k in range(15):
    if gl[k] == "1":
     px(x + k % 3, y + k // 3, col)
  x += 4
def draw_swatch(x, y, s, m):
 if m == EMPTY:
  display.drawRectangle(x, y, s, s, 1)
  display.drawLine(x, y, x + s - 1, y + s - 1, 1)
  display.drawLine(x + s - 1, y, x, y + s - 1, 1)
  return
 display.drawRectangle(x, y, s, s, 1)
 if m == HEAT or m == COOL:
  mid = s // 2
  display.drawLine(x + 2, y + mid, x + s - 3, y + mid, 1)
  if m == HEAT:
   display.drawLine(x + mid, y + 2, x + mid, y + s - 3, 1)
  return
 px = display.setPixel
 for j in range(1, s - 1):
  for i in range(1, s - 1):
   v = T[PAT_OFF + m * 16 + ((j & 3) << 2) + (i & 3)]
   if v == 2:
    if m == LAVA or m == MOLTEN_IRON:
     v = 1 if getrandbits(3) else 0
    elif m == FIRE:
     v = getrandbits(1)
    else:
     v = 1 if getrandbits(2) == 0 else 0
   if v:
    px(x + i, y + j, 1)
def draw_palette(cat, p):
 items = CATS[cat]
 n = len(items)
 display.drawFilledRectangle(0, 8, W, 32, 0)
 display.drawLine(0, 8, W - 1, 8, 1)
 tx = 2
 for k in range(4):
  nm = CAT_TABS[k]
  w = tiny_width(nm)
  if k == cat:
   display.drawFilledRectangle(tx - 2, 10, w + 3, 7, 1)
   tiny_text(nm, tx, 11, 0)
  else:
   tiny_text(nm, tx, 11, 1)
  tx += w + 5
 name = NAMES[items[p]]
 display.drawText("<", 0, 17, 1)
 display.drawText(">", W - 6, 17, 1)
 if len(name) > 8:
  tiny_text(name, (W - tiny_width(name)) // 2, 18)
 else:
  display.drawText(name, (W - len(name) * 6) // 2, 17, 1)
 if n >= 5:
  draw_swatch(4, 27, 8, items[(p - 2) % n])
  draw_swatch(60, 27, 8, items[(p + 2) % n])
 if n >= 3:
  draw_swatch(17, 26, 10, items[(p - 1) % n])
  draw_swatch(45, 26, 10, items[(p + 1) % n])
 display.drawRectangle(29, 24, 14, 14, 1)
 draw_swatch(30, 25, 12, items[p])
def slot_path(slot):
 return SAVE_DIR + "/canvas%d.bin" % (slot + 1)
def save_canvas(slot):
 try:
  try:
   os.mkdir("/Saves")
  except OSError:
   pass
  try:
   os.mkdir(SAVE_DIR)
  except OSError:
   pass
  out = bytearray()
  prev = grid[0]
  n = 1
  for i in range(1, N):
   v = grid[i]
   if v == prev and n < 255:
    n += 1
   else:
    out.append(n)
    out.append(prev)
    prev = v
    n = 1
  out.append(n)
  out.append(prev)
  f = open(slot_path(slot), "wb")
  f.write(out)
  f.close()
  return "SAVED %d" % (slot + 1)
 except Exception:
  return "SAVE FAILED"
def load_canvas(slot):
 try:
  f = open(slot_path(slot), "rb")
  data = f.read()
  f.close()
  pos = 0
  tmp = bytearray(N)
  for k in range(0, len(data) - 1, 2):
   n = data[k]
   v = data[k + 1]
   if v > MAXMAT or pos + n > N:
    return "BAD FILE"
   if v:
    tmp[pos:pos + n] = bytes((v,)) * n
   pos += n
  grid[:] = tmp
  for i in range(N):
   T[TM_OFF + i] = DEFT.get(grid[i], AMBIENT)
  return "LOADED %d" % (slot + 1)
 except Exception:
  return "EMPTY SLOT"
def clear_canvas():
 grid[:] = ZERO
 T[TM_OFF:TM_OFF + N] = AMB
def fill_canvas(mat):
 if mat >= HEAT:
  return
 if mat == EMPTY:
  clear_canvas()
  return
 t = DEFT.get(mat, AMBIENT)
 for i in range(N):
  if grid[i] == 0:
   grid[i] = mat
   T[TM_OFF + i] = t
def border_canvas():
 for x in range(W):
  grid[x] = WALL
  grid[(H - 1) * W + x] = WALL
 for y in range(H):
  grid[y * W] = WALL
  grid[y * W + W - 1] = WALL
 for i in range(N):
  if grid[i] == WALL:
   T[TM_OFF + i] = AMBIENT
MENU_N = 13
def menu_label(k, cat, mat, brush_i, speed_i, curs_i, paused, slot):
 if k == 0:
  return "TYPE:" + CAT_NAMES[cat]
 if k == 1:
  return "MAT:" + NAMES[mat]
 if k == 2:
  s = brush_i * 2 + 1
  return "BRUSH:%dx%d" % (s, s)
 if k == 3:
  return "SPEED:" + SPEED_NAMES[speed_i]
 if k == 4:
  return "CURSOR:" + CURSOR_NAMES[curs_i]
 if k == 5:
  return "PAUSE:ON" if paused else "PAUSE:OFF"
 if k == 6:
  return "STEP"
 if k == 7:
  return "FILL"
 if k == 8:
  return "BORDER"
 if k == 9:
  return "CLEAR"
 if k == 10:
  return "SLOT:%d" % (slot + 1)
 if k == 11:
  return "SAVE"
 return "LOAD"
def draw_menu(sel, cat, mat, brush_i, speed_i, curs_i, paused, slot):
 display.fill(0)
 top = sel - 2
 if top < 0:
  top = 0
 if top > MENU_N - 5:
  top = MENU_N - 5
 for row in range(5):
  k = top + row
  y = row * 8
  label = menu_label(k, cat, mat, brush_i, speed_i, curs_i, paused, slot)
  col = 1
  if k == sel:
   display.drawFilledRectangle(0, y, 69, 8, 1)
   col = 0
  if len(label) > 11:
   tiny_text(label, 1, y + 2, col)
  else:
   display.drawText(label, 1, y + 1, col)
 bar_h = 40 * 5 // MENU_N
 bar_y = (40 - bar_h) * top // (MENU_N - 5)
 display.drawFilledRectangle(70, bar_y, 2, bar_h, 1)
def read_buttons():
 m = 0
 if thumby.buttonU.pressed():
  m |= 1
 if thumby.buttonD.pressed():
  m |= 2
 if thumby.buttonL.pressed():
  m |= 4
 if thumby.buttonR.pressed():
  m |= 8
 if thumby.buttonA.pressed():
  m |= 16
 if thumby.buttonB.pressed():
  m |= 32
 return m
def main():
 display.setFPS(30)
 cx, cy = W // 2, H // 2
 cat = 1
 pos = [0, 0, 0, 0]
 brush_i = 1
 speed_i = 3
 curs_i = 1
 slot = 0
 paused = False
 acc = 0
 menu = False
 sel = 0
 prev = 0
 held = 0
 b_hold = 0
 picked = False
 sticky = False
 a_block = False
 frame = 0
 msg = "TAP B:MENU"
 msg_t = 60
 while True:
  frame += 1
  mat = CATS[cat][pos[cat]]
  m = read_buttons()
  edge = m & ~prev
  rel = prev & ~m
  dm = m & 15
  if dm != (prev & 15):
   held = 0
  if dm:
   held += 1
  else:
   held = 0
  pulse_m = 0
  if held == 1 or (held > 8 and not (held & 1)):
   pulse_m = dm
  delay, every, stride = CURSOR_SPEEDS[curs_i]
  pulse_c = 0
  if held == 1 or (held > delay and (held - delay) % every == 0):
   pulse_c = dm
  prev = m
  if menu:
   if pulse_m & 1:
    sel = (sel - 1) % MENU_N
   if pulse_m & 2:
    sel = (sel + 1) % MENU_N
   dirx = 0
   if pulse_m & 4:
    dirx = -1
   if pulse_m & 8:
    dirx = 1
   act = edge & 16
   if sel == 0:
    if dirx:
     cat = (cat + dirx) % 4
    elif act:
     cat = (cat + 1) % 4
   elif sel == 1:
    n = len(CATS[cat])
    if dirx:
     pos[cat] = (pos[cat] + dirx) % n
    elif act:
     pos[cat] = (pos[cat] + 1) % n
   elif sel == 2:
    if dirx or act:
     brush_i = (brush_i + (dirx or 1)) % 4
   elif sel == 3:
    if dirx:
     speed_i = min(6, max(0, speed_i + dirx))
    elif act:
     speed_i = (speed_i + 1) % 7
   elif sel == 4:
    if dirx:
     curs_i = min(3, max(0, curs_i + dirx))
    elif act:
     curs_i = (curs_i + 1) % 4
   elif sel == 5:
    if (edge & 12) or act:
     paused = not paused
   elif sel == 10:
    if dirx:
     slot = min(2, max(0, slot + dirx))
    elif act:
     slot = (slot + 1) % 3
   elif act:
    menu = False
    if sel == 6:
     paused = True
     step(grid, st)
     msg, msg_t = "STEP", 20
    elif sel == 7:
     fill_canvas(CATS[cat][pos[cat]])
     msg, msg_t = "FILLED", 30
    elif sel == 8:
     border_canvas()
     msg, msg_t = "BORDER", 30
    elif sel == 9:
     clear_canvas()
     msg, msg_t = "CLEARED", 30
    elif sel == 11:
     msg, msg_t = save_canvas(slot), 40
    else:
     msg, msg_t = load_canvas(slot), 40
   if edge & 32:
    menu = False
    b_hold = -1
   if menu:
    draw_menu(sel, cat, CATS[cat][pos[cat]], brush_i, speed_i, curs_i, paused, slot)
    display.update()
    continue
  else:
   if (m & 48) == 48 and (edge & 48):
    sticky = not sticky
    picked = True
    a_block = True
   if m & 32:
    if b_hold >= 0:
     b_hold += 1
   else:
    if (rel & 32) and 0 < b_hold < 10 and not picked and not sticky:
     menu = True
    b_hold = 0
    picked = False
   if menu:
    draw_menu(sel, cat, CATS[cat][pos[cat]], brush_i, speed_i, curs_i, paused, slot)
    display.update()
    continue
   picker = sticky or b_hold >= 10
   if picker:
    picked = True
    if pulse_m & 1:
     cat = (cat - 1) % 4
    if pulse_m & 2:
     cat = (cat + 1) % 4
    n = len(CATS[cat])
    if pulse_m & 4:
     pos[cat] = (pos[cat] - 1) % n
    if pulse_m & 8:
     pos[cat] = (pos[cat] + 1) % n
    mat = CATS[cat][pos[cat]]
   else:
    if pulse_c & 1:
     cy = max(0, cy - stride)
    if pulse_c & 2:
     cy = min(H - 1, cy + stride)
    if pulse_c & 4:
     cx = max(0, cx - stride)
    if pulse_c & 8:
     cx = min(W - 1, cx + stride)
   if not (m & 16):
    a_block = False
   if (m & 16) and not a_block:
    paint(cx, cy, brush_i, mat)
   if not paused:
    acc += SPEED_ACC[speed_i]
    while acc >= 8:
     acc -= 8
     step(grid, st)
  draw_world(frame)
  if (frame >> 2) & 1:
   draw_cursor(cx, cy, brush_i)
  picker = sticky or b_hold >= 10
  if picker:
   draw_palette(cat, pos[cat])
  idx = cy * W + cx
  under = grid[idx]
  label = "AIR" if under == EMPTY else NAMES[under]
  label = "%s %dC" % (label, deg(T[TM_OFF + idx]))
  lw = tiny_width(label)
  if lw > W - 4:
   label = label.replace("MOLTEN ", "M.")
   lw = tiny_width(label)
  display.drawFilledRectangle(W - lw - 3, 0, lw + 3, 7, 0)
  tiny_text(label, W - lw - 1, 1)
  if paused:
   display.drawFilledRectangle(0, 0, 8, 8, 0)
   display.drawFilledRectangle(1, 1, 2, 6, 1)
   display.drawFilledRectangle(5, 1, 2, 6, 1)
  if msg_t:
   msg_t -= 1
   if not picker:
    display.drawFilledRectangle(0, H - 8, W, 8, 0)
    display.drawText(msg, 1, H - 7, 1)
  display.update()
main()
