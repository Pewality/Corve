# tc_world.py - TinyCraft world, physics, items, mobs, save/load
import time, random, struct, os

# ---- block / item ids
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
LOG = 4
LEAVES = 5
SAND = 6
PLANKS = 7
COBBLE = 8
COAL_ORE = 9
BEDROCK = 10
COAL = 11      # item
WPICK = 12     # tool
SPICK = 13     # tool
MOB = 14       # slime (lives in the world array while alive)
BRICK = 15
SWORD = 16     # tool

NAMES = ("", "Grass", "Dirt", "Stone", "Wood", "Leaves", "Sand", "Planks",
         "Cobble", "CoalOre", "Bedrock", "Coal", "WoodPick", "StonePick",
         "Slime", "Brick", "Sword")
PLACEABLE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 15)

HW = 77          # player half width (256 units = 1 block)
PH = 450         # player height
EYE = 400        # eye height

SAVE_DIR = "/Saves/TinyCraft"
SAVE_FILE = "/Saves/TinyCraft/world.bin"
INV_SIZE = 24

world = bytearray(32 * 32 * 16)
hm = bytearray(32 * 32)
INV = bytearray(INV_SIZE)
pos = [0, 0, 0]
mobs = []

# ------------------------------------------------------------------ world
def solid(cx, cy, cz):
    if cz < 0:
        return True
    if cz > 15:
        return False
    if cx < 0 or cx > 31 or cy < 0 or cy > 31:
        return True
    return world[cx | (cy << 5) | (cz << 10)] != 0

def gen():
    random.seed(time.ticks_ms())
    ri = random.randint
    for i in range(len(world)):
        world[i] = 0
    g = [[ri(0, 255) for _ in range(9)] for _ in range(9)]
    for y in range(32):
        gy = y >> 2
        fy = y & 3
        for x in range(32):
            gx = x >> 2
            fx = x & 3
            a = g[gy][gx]
            b = g[gy][gx + 1]
            c = g[gy + 1][gx]
            d = g[gy + 1][gx + 1]
            top = a * (4 - fx) + b * fx
            bot = c * (4 - fx) + d * fx
            v = top * (4 - fy) + bot * fy
            h = 5 + (v * 6) // 4080
            hm[x | (y << 5)] = h
            sandy = h <= 6
            o = x | (y << 5)
            world[o] = BEDROCK
            for z in range(1, h + 1):
                if z == h:
                    b_ = SAND if sandy else GRASS
                elif z >= h - 3:
                    b_ = SAND if sandy else DIRT
                else:
                    b_ = STONE
                world[o | (z << 10)] = b_
    for n in range(7):                      # caves
        cx = ri(3, 28)
        cy = ri(3, 28)
        cz = ri(2, 5)
        for s in range(45):
            for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                x = cx + d[0]
                y = cy + d[1]
                z = cz + d[2]
                if 0 <= x < 32 and 0 <= y < 32 and z >= 1 and z <= hm[x | (y << 5)] - 2:
                    world[x | (y << 5) | (z << 10)] = AIR
            cx = max(2, min(29, cx + ri(-1, 1)))
            cy = max(2, min(29, cy + ri(-1, 1)))
            cz = max(2, min(7, cz + ri(-1, 1)))
    for n in range(110):                    # coal
        x = ri(0, 31)
        y = ri(0, 31)
        z = ri(1, 7)
        i = x | (y << 5) | (z << 10)
        if world[i] == STONE:
            world[i] = COAL_ORE
            if ri(0, 1) and x < 31 and world[i + 1] == STONE:
                world[i + 1] = COAL_ORE
    for n in range(26):                     # trees
        x = ri(3, 28)
        y = ri(3, 28)
        h = hm[x | (y << 5)]
        if h > 9 or world[x | (y << 5) | (h << 10)] != GRASS:
            continue
        for z in range(h + 1, h + 5):
            world[x | (y << 5) | (z << 10)] = LOG
        for z in range(h + 3, h + 6):
            r = 2 if z < h + 5 else 1
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if r == 2 and abs(dx) == 2 and abs(dy) == 2:
                        continue
                    i = (x + dx) | ((y + dy) << 5) | (z << 10)
                    if world[i] == AIR:
                        world[i] = LEAVES

def find_spawn():
    best = None
    for r in range(0, 12):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x = 16 + dx
                y = 16 + dy
                z = 15
                while z > 0 and world[x | (y << 5) | (z << 10)] == 0:
                    z -= 1
                if world[x | (y << 5) | (z << 10)] in (GRASS, SAND):
                    best = (x, y, z)
                    break
            if best:
                break
        if best:
            break
    if not best:
        best = (16, 16, 12)
    pos[0] = best[0] * 256 + 128
    pos[1] = best[1] * 256 + 128
    pos[2] = (best[2] + 1) * 256

def sand_fall(x, y, z):
    zz = z + 1
    while zz < 16 and world[x | (y << 5) | (zz << 10)] == SAND:
        lz = zz
        while lz > 0 and world[x | (y << 5) | ((lz - 1) << 10)] == 0:
            lz -= 1
        if lz != zz:
            world[x | (y << 5) | (zz << 10)] = 0
            world[x | (y << 5) | (lz << 10)] = SAND
        zz += 1

def rtick():
    ri = random.randint
    x = ri(0, 31)
    y = ri(0, 31)
    z = 15
    while z > 0 and world[x | (y << 5) | (z << 10)] == 0:
        z -= 1
    i = x | (y << 5) | (z << 10)
    b = world[i]
    above = world[i + 1024] if z < 15 else 0
    if b == DIRT and (above == 0 or above == MOB):
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < 32 and 0 <= ny < 32:
                for nz in (z - 1, z, z + 1):
                    if 0 <= nz < 16 and world[nx | (ny << 5) | (nz << 10)] == GRASS:
                        world[i] = GRASS
                        return
    elif b == GRASS and above != 0 and above != MOB:
        world[i] = DIRT

# ---------------------------------------------------------------- physics
def hits(x, y, z):
    x0 = (x - HW) >> 8
    x1 = (x + HW) >> 8
    y0 = (y - HW) >> 8
    y1 = (y + HW) >> 8
    z0 = z >> 8
    z1 = (z + PH - 1) >> 8
    for cx in range(x0, x1 + 1):
        for cy in range(y0, y1 + 1):
            for cz in range(z0, z1 + 1):
                if solid(cx, cy, cz):
                    return True
    return False

def move_axis(a, d):
    if d == 0:
        return False
    s = 1 if d > 0 else -1
    n = d * s
    while n > 0:
        st = n if n < 64 else 64
        base = pos[a]
        pos[a] = base + s * st
        if hits(pos[0], pos[1], pos[2]):
            lo = 0
            hi = st
            while hi - lo > 1:
                mid = (lo + hi) >> 1
                pos[a] = base + s * mid
                if hits(pos[0], pos[1], pos[2]):
                    hi = mid
                else:
                    lo = mid
            pos[a] = base + s * lo
            return True
        n -= st
    return False

def pick(fx, fy, fz):
    """March along the view. Returns (hit cell, previous cell) or None."""
    x = pos[0]
    y = pos[1]
    z = pos[2] + EYE
    lx = x >> 8
    ly = y >> 8
    lz = z >> 8
    sx = fx >> 3
    sy = fy >> 3
    sz = fz >> 3
    for _ in range(40):
        x += sx
        y += sy
        z += sz
        cx = x >> 8
        cy = y >> 8
        cz = z >> 8
        if cx != lx or cy != ly or cz != lz:
            if cx < 0 or cy < 0 or cx > 31 or cy > 31 or cz < 0:
                return None
            if cz < 16 and world[cx | (cy << 5) | (cz << 10)] != 0:
                return (cx, cy, cz), (lx, ly, lz)
            lx = cx
            ly = cy
            lz = cz
    return None

def cell_hits_player(cx, cy, cz):
    x0 = cx << 8
    y0 = cy << 8
    z0 = cz << 8
    return (pos[0] + HW > x0 and pos[0] - HW < x0 + 256 and
            pos[1] + HW > y0 and pos[1] - HW < y0 + 256 and
            pos[2] + PH > z0 and pos[2] < z0 + 256)

# ------------------------------------------------------------ items/mining
HARD = (0, 500, 450, 2600, 1100, 250, 400, 1000, 2600, 3000, 0, 0, 0, 0, 1200, 2600)

def tool_tier():
    if INV[SPICK]:
        return 2
    if INV[WPICK]:
        return 1
    return 0

def break_time(b):
    h = HARD[b]
    if b == MOB:
        return 400 if INV[SWORD] else 1200
    if b == STONE or b == COBBLE or b == COAL_ORE or b == BRICK:
        t = tool_tier()
        if t == 1:
            h = h * 35 // 100
        elif t == 2:
            h = h * 20 // 100
    return h

def drop_of(b):
    t = tool_tier()
    if b == STONE or b == COBBLE:
        return COBBLE if t else 0
    if b == BRICK:
        return BRICK if t else 0
    if b == COAL_ORE:
        return COAL if t else 0
    if b == GRASS:
        return DIRT
    if b == MOB:
        return 0
    return b

def give(it):
    if it and INV[it] < 99:
        INV[it] += 1

def hot():
    return [i for i in PLACEABLE if INV[i]]

RECIPES = (
    ("4 Planks", ((LOG, 1),), PLANKS, 4, "1 Wood"),
    ("Wood Pick", ((PLANKS, 4),), WPICK, 1, "4 Planks"),
    ("Stone Pick", ((COBBLE, 3), (PLANKS, 2)), SPICK, 1, "3Cob 2Plnk"),
    ("Sword", ((COBBLE, 2), (PLANKS, 1)), SWORD, 1, "2Cob 1Plnk"),
    ("4 Brick", ((COBBLE, 4),), BRICK, 4, "4 Cobble"),
)

def can_craft(r):
    for it, n in r[1]:
        if INV[it] < n:
            return False
    if r[2] in (WPICK, SPICK, SWORD) and INV[r[2]]:
        return False
    return True

def craft(r):
    for it, n in r[1]:
        INV[it] -= n
    for _ in range(r[3]):
        give(r[2])

# ------------------------------------------------------------------- mobs
def mob_clear():
    for m in mobs:
        i = m[0] | (m[1] << 5) | (m[2] << 10)
        if world[i] == MOB:
            world[i] = 0
    while mobs:
        mobs.pop()

def mob_spawn(pcx, pcy):
    if len(mobs) >= 3:
        return
    ri = random.randint
    for _ in range(8):
        x = pcx + ri(-11, 11)
        y = pcy + ri(-11, 11)
        if x < 1 or y < 1 or x > 30 or y > 30:
            continue
        if abs(x - pcx) + abs(y - pcy) < 7:
            continue
        z = 15
        while z > 0 and world[x | (y << 5) | (z << 10)] == 0:
            z -= 1
        b = world[x | (y << 5) | (z << 10)]
        if z < 14 and b in (GRASS, SAND, DIRT, STONE):
            mobs.append([x, y, z + 1])
            world[x | (y << 5) | ((z + 1) << 10)] = MOB
            return

def mob_despawn_one():
    if mobs:
        m = mobs.pop()
        i = m[0] | (m[1] << 5) | (m[2] << 10)
        if world[i] == MOB:
            world[i] = 0

def mob_kill(cx, cy, cz):
    for m in mobs:
        if m[0] == cx and m[1] == cy and m[2] == cz:
            mobs.remove(m)
            return

def sgn(v):
    return 1 if v > 0 else (-1 if v < 0 else 0)

def mob_update():
    """Move every mob one cell toward the player. Returns how many touch the player."""
    pcx = pos[0] >> 8
    pcy = pos[1] >> 8
    pcz = pos[2] >> 8
    touching = 0
    for m in mobs:
        x, y, z = m[0], m[1], m[2]
        dxp = pcx - x
        dyp = pcy - y
        if abs(dxp) <= 1 and abs(dyp) <= 1 and pcz - 1 <= z <= pcz + 1:
            touching += 1
            continue
        if abs(dxp) >= abs(dyp):
            steps = ((sgn(dxp), 0), (0, sgn(dyp)))
        else:
            steps = ((0, sgn(dyp)), (sgn(dxp), 0))
        for sx, sy in steps:
            if sx == 0 and sy == 0:
                continue
            nx = x + sx
            ny = y + sy
            if nx < 0 or ny < 0 or nx > 31 or ny > 31:
                continue
            nz = z
            if world[nx | (ny << 5) | (z << 10)] != 0:
                if (z < 15 and world[nx | (ny << 5) | ((z + 1) << 10)] == 0 and
                        world[x | (y << 5) | ((z + 1) << 10)] == 0):
                    nz = z + 1
                else:
                    continue
            while nz > 1 and world[nx | (ny << 5) | ((nz - 1) << 10)] == 0:
                nz -= 1
            if cell_hits_player(nx, ny, nz):
                continue
            world[x | (y << 5) | (z << 10)] = 0
            world[nx | (ny << 5) | (nz << 10)] = MOB
            m[0], m[1], m[2] = nx, ny, nz
            break
    return touching

# -------------------------------------------------------------- save/load
def save_game(yaw, pitch, hp, tod):
    cells = []
    for m in mobs:                      # never save mobs into the terrain
        i = m[0] | (m[1] << 5) | (m[2] << 10)
        cells.append(i)
        world[i] = 0
    result = "Saved!"
    try:
        for d in ("/Saves", SAVE_DIR):
            try:
                os.mkdir(d)
            except OSError:
                pass
        f = open(SAVE_FILE, "wb")
        f.write(struct.pack("<7i", pos[0], pos[1], pos[2], yaw, pitch, hp, tod))
        f.write(INV)
        f.write(world)
        f.close()
    except Exception:
        result = "Save failed"
    for i in cells:
        world[i] = MOB
    return result

def has_save():
    try:
        return os.stat(SAVE_FILE)[6] == 28 + INV_SIZE + len(world)
    except OSError:
        return False

def load_game():
    try:
        if not has_save():
            return None
        f = open(SAVE_FILE, "rb")
        h = struct.unpack("<7i", f.read(28))
        f.readinto(INV)
        f.readinto(world)
        f.close()
        pos[0], pos[1], pos[2] = h[0], h[1], h[2]
        return h[3], h[4], h[5], h[6]
    except Exception:
        return None
