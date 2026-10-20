# TinyCraft - 3D voxel sandbox for the Thumby (MicroPython)
#
# Copy ALL THREE files into /Games/TinyCraft/ on the Thumby:
#     TinyCraft.py   (this file: game loop, HUD, menus)
#     tc_render.py   (voxel raycaster)
#     tc_world.py    (world, physics, items, mobs, saving)
#
# CONTROLS
#   Up / Down ............ walk forward / back
#   Left / Right ......... turn (hold to turn faster)
#   Walk into a ledge .... you hop up automatically
#   Hold A ............... mine / attack what the crosshair points at
#   B .................... place the selected block (hold = repeat)
#   Up + B ............... jump
#   Hold A + Up/Down ..... look up / down
#   Hold A + Left/Right .. choose block
#   A + B ................ menu (craft, bag, detail, help, save)
# Night brings slimes: mine them (hold A) before they hurt you.
# The game autosaves every 45 s and continues your world next time.

import sys
for _p in ("/Games/TinyCraft", "/Games/TinyCraft/"):
    if _p not in sys.path:
        sys.path.append(_p)

import time, gc
import thumby
from tc_world import *
from tc_render import *

OVERCLOCK = False        # True = run the RP2040 at 250 MHz (faster, unofficial)
if OVERCLOCK:
    import machine
    machine.freq(250000000)

DAY_MS = 360000
MODES = ("SMART", "SHARP", "FAST")

# ---------------------------------------------------------------------- HUD
DIG_ROWS = ("111101101101111", "010110010010111", "111001111100111",
            "111001111001111", "101101111001001", "111100111001111",
            "111100111101111", "111001001001001", "111101111101111",
            "111101111001111")
DIG = []
for _d in DIG_ROWS:
    _cols = []
    for _c in range(3):
        _v = 0
        for _r in range(5):
            if _d[_r * 3 + _c] == "1":
                _v |= 1 << _r
        _cols.append(_v)
    DIG.append(_cols)

ICONL = (0, 9, 5, 7, 5, 6, 11, 9, 6, 7, 3, 0, 0, 0, 0, 8, 0)

def draw_num(buf, x, n):
    for ch in str(n):
        g = DIG[ord(ch) - 48]
        for c in range(3):
            buf[288 + x + c] |= g[c] << 2
        x += 4

def hud(buf, selid, hp):
    for x in range(72):
        buf[288 + x] &= 1
    items = hot()
    n = len(items)
    if n:
        si = items.index(selid) if selid in items else 0
        start = 0
        if n > 5:
            start = max(0, min(si - 2, n - 5))
        for k in range(min(5, n - start)):
            it = items[start + k]
            x0 = k * 8
            lvl = ICONL[it]
            for c in range(5):
                col = 0
                for r in range(5):
                    if lvl > BAYER[(c & 3) | ((r & 3) << 2)]:
                        col |= 1 << r
                buf[288 + x0 + 1 + c] |= col << 2
            if it == selid:
                for c in range(7):
                    buf[288 + x0 + c] |= 0x82
                buf[288 + x0] |= 0xFE
                buf[288 + x0 + 6] |= 0xFE
        if selid in items:
            draw_num(buf, 41, INV[selid])
    for i in range(20):
        buf[288 + 51 + i] |= 0x38 if i < hp else 0x10
    for cx, cy in ((36, 20), (35, 20), (37, 20), (36, 19), (36, 21)):   # crosshair (XOR)
        buf[cx + (cy >> 3) * 72] ^= 1 << (cy & 7)

# ---------------------------------------------------------------- UI helpers
def text(s, x, y):
    thumby.display.drawText(s, x, y, 1)

def wait_release():
    while (thumby.buttonA.pressed() or thumby.buttonB.pressed() or
           thumby.buttonU.pressed() or thumby.buttonD.pressed()):
        time.sleep_ms(10)

def draw_list(lines, cur, info):
    thumby.display.fill(0)
    n = len(lines)
    start = max(0, min(cur - 1, n - 4)) if n > 4 else 0
    for k in range(min(4, n - start)):
        i = start + k
        text(("> " if i == cur else "  ") + lines[i], 0, k * 8)
    text(info, 0, 33)
    thumby.display.update()

def bag_screen(kills):
    lines = ["Kills " + str(kills)]
    for i in range(1, 17):
        if INV[i]:
            lines.append(NAMES[i] + " " + str(INV[i]))
    cur = 0
    pu = pd = True
    while True:
        draw_list(lines, cur, "B: back")
        u = thumby.buttonU.pressed()
        d = thumby.buttonD.pressed()
        if u and not pu and cur > 0:
            cur -= 1
        if d and not pd and cur < len(lines) - 1:
            cur += 1
        pu = u
        pd = d
        if thumby.buttonB.pressed():
            wait_release()
            return

def help_screen():
    pages = (
        ("-- MOVE --", "Up/Dn: walk", "Lt/Rt: turn", "Up+B: jump", "(auto-hops!)"),
        ("- BLOCKS -", "Hold A: mine", "B: place", "Mine a tree", "to get Wood"),
        ("- A + DPAD -", "A held +", "Up/Dn: look", "Lt/Rt: item", ""),
        ("- NIGHT -", "Slimes come", "out at night", "Hold A on one", "to kill it"),
        ("-- MENU --", "Press A + B", "Craft Planks", "then Pickaxe", "Saves by itself"),
    )
    for pg in pages:
        thumby.display.fill(0)
        for i in range(5):
            text(pg[i], 0, i * 8)
        text(">", 66, 32)
        thumby.display.update()
        wait_release()
        while True:
            if thumby.buttonA.pressed():
                break
            if thumby.buttonB.pressed():
                wait_release()
                return
            time.sleep_ms(20)
        wait_release()

def menu(state):
    entries = []
    for r in RECIPES:
        entries.append(r[0])
    entries += ["Bag", "Detail", "Help", "Save", "Resume"]
    cur = 0
    wait_release()
    pu = pd = pa = False
    while True:
        e = entries[cur]
        info = ""
        if cur < len(RECIPES):
            r = RECIPES[cur]
            if r[2] in (WPICK, SPICK, SWORD) and INV[r[2]]:
                info = "Owned"
            elif can_craft(r):
                info = r[4] + " OK"
            else:
                info = "Need " + r[4]
        elif e == "Detail":
            info = "A: " + MODES[state['mode']]
        elif e == "Save":
            info = "A: save game"
        elif e == "Help":
            info = "A: controls"
        elif e == "Bag":
            info = "A: open"
        else:
            info = "A: back"
        draw_list(entries, cur, info)
        u = thumby.buttonU.pressed()
        d = thumby.buttonD.pressed()
        a = thumby.buttonA.pressed()
        if u and not pu and cur > 0:
            cur -= 1
        if d and not pd and cur < len(entries) - 1:
            cur += 1
        if a and not pa:
            if cur < len(RECIPES):
                if can_craft(RECIPES[cur]):
                    craft(RECIPES[cur])
            elif e == "Bag":
                bag_screen(state['kills'])
            elif e == "Help":
                help_screen()
            elif e == "Detail":
                state['mode'] = (state['mode'] + 1) % 3
            elif e == "Save":
                state['msg'] = save_game(state['yaw'], state['pitch'], state['hp'], state['tod'])
                wait_release()
                return
            else:
                wait_release()
                return
        pu = u
        pd = d
        pa = a
        if thumby.buttonB.pressed():
            wait_release()
            return

def title(can_load):
    thumby.display.fill(0)
    text("TINYCRAFT", 9, 4)
    if can_load:
        text("A: Continue", 0, 20)
        text("B: New world", 0, 30)
    else:
        text("A: New world", 0, 24)
    thumby.display.update()
    wait_release()
    while True:
        if thumby.buttonA.pressed():
            wait_release()
            return can_load
        if can_load and thumby.buttonB.pressed():
            wait_release()
            return False
        time.sleep_ms(20)

def banner(s1, s2=""):
    thumby.display.fill(0)
    text(s1, 0, 10)
    text(s2, 0, 22)
    thumby.display.update()

def get_buffer():
    try:
        return thumby.display.display.buffer, False
    except Exception:
        return bytearray(360), True

def ambient(tod):
    p = tod // 88
    if p < 2400:
        return 16
    if p < 2900:
        return 16 - ((p - 2400) * 10) // 500
    if p < 3500:
        return 6
    return 6 + ((p - 3500) * 10) // 600

def cycle_item(selid, step):
    items = hot()
    if not items:
        return 0
    if selid in items:
        return items[(items.index(selid) + step) % len(items)]
    return items[0]

def top_text(buf, s):
    for x in range(72):
        buf[x] = 0
    text(s, 0, 0)

# --------------------------------------------------------------------- main
def main():
    build_tables()
    buf, fallback = get_buffer()
    thumby.display.setFPS(0)
    gc.collect()

    yaw = 0
    pitch = 0
    hp = 20
    tod = 0
    for i in range(INV_SIZE):
        INV[i] = 0
    cont = title(has_save())
    res = None
    if cont:
        banner("Loading", "world...")
        res = load_game()
    fresh = res is None
    if fresh:
        banner("Generating", "world...")
        for i in range(INV_SIZE):
            INV[i] = 0
        gen()
        find_spawn()
        sp = (pos[0], pos[1], pos[2])
    else:
        yaw, pitch, hp, tod = res
        keep = (pos[0], pos[1], pos[2])
        find_spawn()
        sp = (pos[0], pos[1], pos[2])
        pos[0], pos[1], pos[2] = keep
    mob_clear()
    if hp < 1:
        hp = 20
    if fresh:
        help_screen()

    state = {'mode': 0, 'yaw': 0, 'pitch': 0, 'hp': 20, 'tod': 0, 'msg': "", 'kills': 0}
    msg = ""
    msg_t = 0
    label = ""
    lab_t = 0
    last_tb = 0
    selid = cycle_item(0, 0)
    vz = 0
    peak = pos[2]
    regen = 0
    tt = 0
    mine_t = None
    mine_ms = 0
    pA = pB = pL = pR = False
    bacc = 0
    selt = 0
    dirty = False
    since_save = 0
    mob_t = 0
    hurt_cd = 0
    flash = False
    saved_pos = (pos[0], pos[1], pos[2])
    last = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, last)
        last = now
        if dt > 150:
            dt = 150
        if dt < 1:
            dt = 1
        tod = (tod + dt) % DAY_MS
        amb = ambient(tod)

        U = thumby.buttonU.pressed()
        D = thumby.buttonD.pressed()
        L = thumby.buttonL.pressed()
        R = thumby.buttonR.pressed()
        A = thumby.buttonA.pressed()
        B = thumby.buttonB.pressed()

        # --- A + B = menu
        if A and B and (not pA or not pB):
            state['yaw'] = yaw
            state['pitch'] = pitch
            state['hp'] = hp
            state['tod'] = tod
            state['msg'] = ""
            menu(state)
            if state['msg']:
                msg = state['msg']
                msg_t = 1500
                since_save = 0
                dirty = False
                saved_pos = (pos[0], pos[1], pos[2])
            else:
                dirty = True
            selid = cycle_item(selid, 0) if (selid and INV[selid]) else cycle_item(0, 0)
            last = time.ticks_ms()
            pA = pB = True
            pL = pR = False
            continue

        tool = A and (U or D or L or R)
        jump = False
        mv = 0
        turning = False
        if tool:
            tt = 0
            if U:
                pitch += dt * 7 // 10
            if D:
                pitch -= dt * 7 // 10
            if pitch > 760:
                pitch = 760
            if pitch < -760:
                pitch = -760
            if L or R:
                selt += dt
                if (L and not pL) or (R and not pR) or selt >= 300:
                    selt = 0
                    selid = cycle_item(selid, -1 if L else 1)
        else:
            selt = 0
            if not A:
                if U:
                    mv = 1
                if D:
                    mv = -1
                if B and U:
                    jump = True
            if L or R:
                turning = True
                tt += dt
                rate = (450 + min(tt, 500) * 2) * dt // 1000
                if L:
                    yaw += rate
                if R:
                    yaw -= rate
                yaw &= 4095
            else:
                tt = 0

        yi = (yaw >> 4) & 255
        # --- horizontal movement (+ auto-hop on ledges)
        hop = False
        if mv:
            dist = dt * 11 // 10
            c = SIN[(yi + 64) & 255]
            s_ = SIN[yi]
            dx = (c * dist) >> 8
            dy = (s_ * dist) >> 8
            if mv < 0:
                dx = -dx
                dy = -dy
            bx = move_axis(0, dx)
            by = move_axis(1, dy)
            if bx or by:
                hx = pos[0] + (0 if not bx else (110 if dx > 0 else -110))
                hy = pos[1] + (0 if not by else (110 if dy > 0 else -110))
                if not hits(hx, hy, pos[2] + 300):
                    hop = True
        # --- vertical movement (small sub-steps keep the jump strong at low fps)
        on_ground = hits(pos[0], pos[1], pos[2] - 1)
        if on_ground:
            peak = pos[2]
            if jump or hop:
                vz = 2500
        nsub = (dt + 39) // 40
        sub = dt // nsub
        for _ in range(nsub):
            vz -= 7168 * sub // 1000
            if vz < -6000:
                vz = -6000
            if move_axis(2, vz * sub // 1000):
                if vz < 0:
                    fall = (peak - pos[2]) >> 8
                    if fall > 3:
                        hp -= fall - 3
                        flash = True
                    peak = pos[2]
                vz = 0
            elif pos[2] > peak:
                peak = pos[2]
        regen += dt
        if regen >= 3500:
            regen = 0
            if 0 < hp < 20:
                hp += 1

        # --- mobs: spawn at night, chase, hurt, vanish at dawn
        mob_t += dt
        if hurt_cd > 0:
            hurt_cd -= dt
        if mob_t >= 450:
            mob_t = 0
            if amb < 10:
                if len(mobs) < 3 and (tod & 3) == 0:
                    mob_spawn(pos[0] >> 8, pos[1] >> 8)
            elif amb >= 15:
                mob_despawn_one()
            if mobs and mob_update() and hurt_cd <= 0:
                hp -= 2
                hurt_cd = 1000
                flash = True

        if hp <= 0:
            banner("YOU DIED", "")
            time.sleep_ms(1500)
            mob_clear()
            pos[0], pos[1], pos[2] = sp
            vz = 0
            hp = 20
            peak = pos[2]
            last = time.ticks_ms()
            continue

        # --- detail level: sharp when still, fast while moving
        moving = (mv != 0) or turning or tool or (not on_ground)
        mode = state['mode']
        ps = 1
        if mode == 2 or (mode == 0 and moving):
            ps = 2

        # --- view + target
        fx, fy, fz = setup_view(yaw, pitch, ps)
        tgt = pick(fx, fy, fz)
        tb = 0
        if tgt:
            P[3], P[4], P[5] = tgt[0]
            tb = world[tgt[0][0] | (tgt[0][1] << 5) | (tgt[0][2] << 10)]
        else:
            P[3] = -1
            P[4] = -1
            P[5] = -1
        if tb != last_tb:
            last_tb = tb
            if tb:
                label = NAMES[tb]
                lab_t = 800

        # --- mining / attacking (hold A, no d-pad)
        P[6] = 0
        if A and not tool and tgt and tgt[0][2] > 0:
            hc = tgt[0]
            b = world[hc[0] | (hc[1] << 5) | (hc[2] << 10)]
            need = break_time(b)
            if need > 0:
                if mine_t != hc:
                    mine_t = hc
                    mine_ms = 0
                mine_ms += dt
                if mine_ms >= need:
                    world[hc[0] | (hc[1] << 5) | (hc[2] << 10)] = 0
                    if b == MOB:
                        mob_kill(hc[0], hc[1], hc[2])
                        state['kills'] += 1
                        if hp < 20:
                            hp += 1
                        msg = "Slime down!"
                        msg_t = 800
                    else:
                        give(drop_of(b))
                        sand_fall(hc[0], hc[1], hc[2])
                    mine_t = None
                    mine_ms = 0
                    dirty = True
                    if selid == 0:
                        selid = cycle_item(0, 0)
                else:
                    P[6] = mine_ms * 8 // need
            else:
                mine_t = None
        else:
            mine_t = None
            mine_ms = 0

        # --- placing (press B; hold to repeat)
        fire = False
        if B:
            if not pB:
                bacc = 0
                fire = True
            else:
                bacc += dt
                if bacc >= 400:
                    bacc = 0
                    fire = True
        if fire and not A and not U and tgt and selid and INV[selid]:
            lx, ly, lz = tgt[1]
            if (0 <= lx < 32 and 0 <= ly < 32 and 0 <= lz < 16 and
                    world[lx | (ly << 5) | (lz << 10)] == 0 and
                    not cell_hits_player(lx, ly, lz)):
                world[lx | (ly << 5) | (lz << 10)] = selid
                INV[selid] -= 1
                dirty = True
                if selid == SAND:
                    sand_fall(lx, ly, lz - 1)
        if selid == 0 or not INV[selid]:
            selid = cycle_item(0, 0)

        rtick()

        # --- autosave
        since_save += dt
        if since_save >= 45000:
            since_save = 0
            moved = (abs(pos[0] - saved_pos[0]) > 768 or abs(pos[1] - saved_pos[1]) > 768)
            if dirty or moved:
                msg = save_game(yaw, pitch, hp, tod)
                msg_t = 900
                dirty = False
                saved_pos = (pos[0], pos[1], pos[2])

        # --- render
        P[0] = pos[0]
        P[1] = pos[1]
        P[2] = pos[2] + EYE
        P[7] = ps
        P[8] = 12 * 4096
        P[9] = amb
        P[10] = (amb - 4) // 4
        render(buf, world, P, T)
        hud(buf, selid, hp)
        if flash:
            flash = False
            for i in range(288):
                buf[i] ^= 0xFF
        if fallback:
            thumby.display.blit(buf, 0, 0, 72, 40, -1, 0, 0)
        if msg_t > 0:
            msg_t -= dt
            top_text(buf, msg)
        elif lab_t > 0 and last_tb:
            lab_t -= dt
            top_text(buf, label)
        thumby.display.update()

        pA = A
        pB = B
        pL = L
        pR = R

main()
