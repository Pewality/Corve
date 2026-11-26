# BLOCADE for the Thumby  (simple edition)
#
# You are the SOLID square. The CPU is the HOLLOW square.
# Get to the far side first (you go UP, the CPU goes DOWN).
# Each turn do ONE thing: step, or drop a wall to slow the CPU.
#
# Install: copy to /Games/Blocade/Blocade.py on your Thumby
#          (or paste into the Thumby Code Editor and press Run).
#
#   Your turn : D-pad = step      A = build a wall
#   Wall mode : D-pad = aim       A = put it down
#               B = turn it (flat <-> upright), B again = back
#   Title     : Left/Right = level, A = play, B = help

import thumby
import time
import random
import gc

N = 5                      # 5 x 5 board
NN = 25
M = 4                      # wall slots per row / column (N - 1)
WALLS0 = 4                 # walls each
CELL = 5
PITCH = 7                  # 5px cell + 2px gap (walls live in the gap)
OY = 3                     # board top offset on screen
DELTA = (-N, 1, N, -1)     # up, right, down, left
LEVELS = ("EASY", "NORMAL", "HARD", "EXPERT")
KROOT = 8
KMID = 4
WALLW = 14

OPEN = bytearray(NN * 4)   # OPEN[cell*4 + dir] = 1 if that step is allowed
HW = bytearray(M * M)      # flat walls:    HW[r*M + c] sits under row r, covers columns c, c+1
VW = bytearray(M * M)      # upright walls: VW[r*M + c] sits right of column c, covers rows r, r+1
pos = [0, 0]               # 0 = you (bottom, going up), 1 = CPU (top, going down)
walls = [0, 0]
T_END = 0
TIMED = False


# --------------------------------------------------------------- rules ----

def reset():
    for i in range(NN):
        r = i // N
        c = i % N
        OPEN[i * 4] = 1 if r > 0 else 0
        OPEN[i * 4 + 1] = 1 if c < N - 1 else 0
        OPEN[i * 4 + 2] = 1 if r < N - 1 else 0
        OPEN[i * 4 + 3] = 1 if c > 0 else 0
    for i in range(M * M):
        HW[i] = 0
        VW[i] = 0
    pos[0] = (N - 1) * N + N // 2
    pos[1] = N // 2
    walls[0] = WALLS0
    walls[1] = WALLS0


def set_wall(ori, r, c, on):
    # ori 0 = flat (blocks up/down steps), ori 1 = upright (blocks left/right steps)
    v = 1 - on
    a = r * N + c
    if ori == 0:
        HW[r * M + c] = on
        OPEN[a * 4 + 2] = v
        OPEN[(a + 1) * 4 + 2] = v
        OPEN[(a + N) * 4] = v
        OPEN[(a + N + 1) * 4] = v
    else:
        VW[r * M + c] = on
        OPEN[a * 4 + 1] = v
        OPEN[(a + N) * 4 + 1] = v
        OPEN[(a + 1) * 4 + 3] = v
        OPEN[(a + N + 1) * 4 + 3] = v


def geom_ok(ori, r, c):
    i = r * M + c
    if HW[i] or VW[i]:             # same spot, or crossing
        return False
    if ori == 0:
        if c > 0 and HW[i - 1]:
            return False
        if c < M - 1 and HW[i + 1]:
            return False
    else:
        if r > 0 and VW[i - M]:
            return False
        if r < M - 1 and VW[i + M]:
            return False
    return True


def step_target(p, d):
    # where a step in direction d lands (jumps over the other pawn), or -1
    me = pos[p]
    if not OPEN[me * 4 + d]:
        return -1
    n = me + DELTA[d]
    if n == pos[1 - p]:
        if OPEN[n * 4 + d]:
            return n + DELTA[d]
        return -1
    return n


def pawn_moves(p):
    out = []
    for d in range(4):
        t = step_target(p, d)
        if t >= 0:
            out.append(t)
    return out


def dmap(goal_row):
    # steps to the goal row from every cell (99 = cut off)
    d = [99] * NN
    fr = []
    b = goal_row * N
    for c in range(N):
        d[b + c] = 0
        fr.append(b + c)
    k = 0
    while fr:
        k += 1
        nx = []
        for cell in fr:
            b = cell << 2
            if OPEN[b]:
                n = cell - N
                if d[n] == 99:
                    d[n] = k
                    nx.append(n)
            if OPEN[b + 1]:
                n = cell + 1
                if d[n] == 99:
                    d[n] = k
                    nx.append(n)
            if OPEN[b + 2]:
                n = cell + N
                if d[n] == 99:
                    d[n] = k
                    nx.append(n)
            if OPEN[b + 3]:
                n = cell - 1
                if d[n] == 99:
                    d[n] = k
                    nx.append(n)
        fr = nx
    return d


def wall_valid(ori, r, c):
    if not geom_ok(ori, r, c):
        return False
    set_wall(ori, r, c, 1)
    ok = dmap(0)[pos[0]] < 99 and dmap(N - 1)[pos[1]] < 99
    set_wall(ori, r, c, 0)
    return ok


def apply(p, code):
    # code < 100: pawn to that cell.   code >= 100: wall = 100 + 100*ori + r*10 + c
    if code < 100:
        old = pos[p]
        pos[p] = code
        return old
    rc = code % 100
    set_wall(code // 100 - 1, rc // 10, rc % 10, 1)
    walls[p] -= 1
    return 0


def unapply(p, code, old):
    if code < 100:
        pos[p] = old
    else:
        rc = code % 100
        set_wall(code // 100 - 1, rc // 10, rc % 10, 0)
        walls[p] += 1


# ------------------------------------------------------------------ AI ----

def static(p, dm):
    q = 1 - p
    a = dm[p][pos[p]]
    b = dm[q][pos[q]]
    if a == 0:
        return 1000
    if b == 0:
        return -1000
    return (b - a) * 10 + (walls[p] - walls[q]) * WALLW


def sort_key(t):
    return t[0]


def _add(out, ori, r, c):
    if geom_ok(ori, r, c):
        code = 100 + ori * 100 + r * 10 + c
        if code not in out:
            out.append(code)


def cand_walls(p, dm):
    # walls that would cut across the other player's shortest route
    dq = dm[1 - p]
    cell = pos[1 - p]
    out = []
    steps = 0
    while dq[cell] > 0 and steps < 8:
        want = dq[cell] - 1
        dd = -1
        for d in range(4):
            if OPEN[cell * 4 + d] and dq[cell + DELTA[d]] == want:
                dd = d
                break
        if dd < 0:
            break
        r = cell // N
        c = cell % N
        if dd == 0 or dd == 2:
            rr = r - 1 if dd == 0 else r
            if c < M:
                _add(out, 0, rr, c)
            if c > 0:
                _add(out, 0, rr, c - 1)
        else:
            cc = c if dd == 1 else c - 1
            if r < M:
                _add(out, 1, r, cc)
            if r > 0:
                _add(out, 1, r - 1, cc)
        cell += DELTA[dd]
        steps += 1
    return out


def children(p, dm):
    # every move worth considering: (score for p, code, distance maps after)
    out = []
    old = pos[p]
    for t in pawn_moves(p):
        pos[p] = t
        out.append((static(p, dm), t, dm))
    pos[p] = old
    if walls[p] > 0:
        for code in cand_walls(p, dm):
            rc = code % 100
            ori = code // 100 - 1
            r = rc // 10
            c = rc % 10
            set_wall(ori, r, c, 1)
            n0 = dmap(0)
            n1 = dmap(N - 1)
            if n0[pos[0]] < 99 and n1[pos[1]] < 99:
                walls[p] -= 1
                ndm = (n0, n1)
                out.append((static(p, ndm), code, ndm))
                walls[p] += 1
            set_wall(ori, r, c, 0)
    return out


def negamax(p, dm, depth, alpha, beta):
    global TIMED
    if TIMED or time.ticks_diff(T_END, time.ticks_ms()) < 0:
        TIMED = True
        return 0
    ch = children(p, dm)
    if not ch:
        return static(p, dm)
    if depth <= 1:
        best = -5000
        for t in ch:
            if t[0] > best:
                best = t[0]
        return best
    ch.sort(key=sort_key, reverse=True)
    best = -5000
    n = 0
    for v, code, ndm in ch:
        if n >= KMID:
            break
        n += 1
        if v >= 900:
            return v
        old = apply(p, code)
        val = -negamax(1 - p, ndm, depth - 1, -beta, -alpha)
        unapply(p, code, old)
        if TIMED:
            return 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def pick(lst):
    return lst[random.randint(0, len(lst) - 1)]


def ai_think(p, lv):
    # returns a move code for player p at difficulty lv (0..3), or None
    global T_END, TIMED, WALLW
    WALLW = 6 if lv < 2 else 14
    dm = (dmap(0), dmap(N - 1))
    ch = children(p, dm)
    if not ch:
        return None
    ch.sort(key=sort_key, reverse=True)
    if ch[0][0] >= 900:
        return ch[0][1]

    if lv == 0:
        # EASY: walks the shortest way, sometimes stumbles, rarely walls
        moves = pawn_moves(p)
        r = random.randint(0, 99)
        if moves and r < 15:
            return pick(moves)
        if r < 35 and walls[p] > 0:
            ws = [t for t in ch if t[1] >= 100]
            if ws:
                return ws[0][1]
        if moves:
            dp = dm[p]
            best = min([dp[c] for c in moves])
            return pick([c for c in moves if dp[c] == best])
        return ch[0][1]

    if lv == 1:
        # NORMAL: best single move
        top = ch[0][0]
        return pick([t[1] for t in ch if t[0] >= top - 1])

    # HARD (2 moves ahead) / EXPERT (4 moves ahead), with a time limit
    T_END = time.ticks_add(time.ticks_ms(), 3000 if lv == 2 else 7000)
    TIMED = False
    best = -9999
    pool = []
    n = 0
    for v, code, ndm in ch:
        if n >= KROOT:
            break
        n += 1
        old = apply(p, code)
        val = -negamax(1 - p, ndm, 2 if lv == 2 else 4, -5000, -(best - 1))
        unapply(p, code, old)
        if TIMED:
            break
        if val > best:
            best = val
            pool = [code]
        elif val == best:
            pool.append(code)
    if not pool:
        return ch[0][1]
    return pick(pool)


# ------------------------------------------------------------- drawing ----

class G:
    pass


def ctext(s, y, c=1):
    thumby.display.drawText(s, (73 - len(s) * 6) // 2, y, c)


def cell_xy(t):
    return (t % N) * PITCH, OY + (t // N) * PITCH


def draw_player_row(y, solid, count, active):
    # icon (solid = you, hollow = CPU) + one little bar per wall left
    d = thumby.display
    fg = 1
    if active:
        d.drawFilledRectangle(35, y, 37, 7, 1)
        fg = 0
    if solid:
        d.drawFilledRectangle(37, y + 1, 5, 5, fg)
    else:
        d.drawRectangle(37, y + 1, 5, 5, fg)
    for i in range(count):
        d.drawFilledRectangle(45 + i * 7, y + 2, 5, 2, fg)


def draw_play(g, lines):
    d = thumby.display
    d.fill(0)
    blink = (g.frame // 4) & 1
    hide = g.flash_t > 0 and ((g.frame // 3) & 1) == 0
    mine = g.state == 2 and g.turn == 0

    # board: a dot in every empty square
    for t in range(NN):
        x, y = cell_xy(t)
        d.setPixel(x + 2, y + 2, 1)

    # walls
    for r in range(M):
        for c in range(M):
            i = r * M + c
            if HW[i] and not (hide and g.flash == (0, i)):
                d.drawFilledRectangle(c * PITCH, OY + r * PITCH + CELL, 12, 2, 1)
            if VW[i] and not (hide and g.flash == (1, i)):
                d.drawFilledRectangle(c * PITCH + CELL, OY + r * PITCH, 2, 12, 1)

    # where you can step (blinking)
    if mine and not g.wmode and blink:
        for t in pawn_moves(0):
            x, y = cell_xy(t)
            d.drawFilledRectangle(x + 1, y + 1, 3, 3, 1)

    # pawns
    x, y = cell_xy(pos[0])
    d.drawFilledRectangle(x, y, CELL, CELL, 1)
    if not (hide and g.flash_pawn):
        x, y = cell_xy(pos[1])
        d.drawFilledRectangle(x, y, CELL, CELL, 0)
        d.drawRectangle(x, y, CELL, CELL, 1)

    # wall being aimed
    if mine and g.wmode:
        if g.wori == 0:
            x = g.wc * PITCH
            y = OY + g.wr * PITCH + CELL
            w = 12
            h = 2
        else:
            x = g.wc * PITCH + CELL
            y = OY + g.wr * PITCH
            w = 2
            h = 12
        if g.wok:
            if blink:
                d.drawFilledRectangle(x, y, w, h, 1)
        else:
            for i in range(0, 12, 2):      # dashed = not allowed here
                if g.wori == 0:
                    d.setPixel(x + i, y, 1)
                    d.setPixel(x + i + 1, y + 1, 1)
                else:
                    d.setPixel(x, y + i, 1)
                    d.setPixel(x + 1, y + i + 1, 1)

    # side panel
    d.drawLine(34, 0, 34, 39, 1)
    draw_player_row(0, True, walls[0], g.state == 2 and g.turn == 0)
    draw_player_row(9, False, walls[1], g.state == 2 and g.turn == 1)
    for i in range(len(lines)):
        d.drawText(lines[i], 36, 17 + i * 8, 1)


HELP = (
    ("SOLID = YOU", "HOLLOW = CPU", "REACH THE", "FAR SIDE", "FIRST TO WIN"),
    ("EACH TURN:", "PAD = STEP", "OR A = WALL", "", "(SEE NEXT)"),
    ("WALL MODE:", "PAD = AIM", "A = PUT IT", "B = TURN IT", "B TWICE=BACK"),
    ("WALLS BLOCK", "2 SQUARES.", "NO FULL SEAL", "FACING CPU =", "AUTO JUMP"),
)


def draw_help(g):
    thumby.display.fill(0)
    lines = HELP[g.page]
    for i in range(5):
        thumby.display.drawText(lines[i], 0, i * 8, 1)


def draw_title(g):
    d = thumby.display
    d.fill(0)
    ctext("BLOCADE", 1)
    d.drawLine(15, 9, 56, 9, 1)
    ctext("< " + LEVELS[g.level] + " >", 15)
    ctext("A = PLAY", 25)
    ctext("B = HELP", 33)


def draw_result(g):
    d = thumby.display
    d.fill(0)
    ctext("YOU WIN!" if g.winner == 0 else "CPU WINS", 3)
    ctext("W:%d L:%d" % (g.wins, g.losses), 14)
    ctext("A:AGAIN", 25)
    ctext("B:MENU", 33)


# ----------------------------------------------------------- save data ----

def load_save(g):
    try:
        thumby.saveData.setName("Blocade")
        if thumby.saveData.hasItem("level"):
            g.level = int(thumby.saveData.getItem("level")) % 4
        if thumby.saveData.hasItem("wins"):
            g.wins = int(thumby.saveData.getItem("wins"))
        if thumby.saveData.hasItem("losses"):
            g.losses = int(thumby.saveData.getItem("losses"))
    except Exception:
        pass


def store_save(g):
    try:
        thumby.saveData.setItem("level", g.level)
        thumby.saveData.setItem("wins", g.wins)
        thumby.saveData.setItem("losses", g.losses)
        thumby.saveData.save()
    except Exception:
        pass


# ----------------------------------------------------------------- game ----

def start_game(g):
    reset()
    g.state = 2
    g.turn = 0
    g.winner = -1
    g.wmode = False
    g.wori = 0
    g.wr = 0
    g.wc = 0
    g.wok = False
    g.msg = None
    g.msg_t = 0
    g.note = None
    g.note_t = 0
    g.flash = None
    g.flash_pawn = False
    g.flash_t = 0
    g.over_t = 0


def say(g, *lines):
    g.msg = lines
    g.msg_t = 30


def human_turn(g, bu, br, bd, bl, ba, bb):
    if not g.wmode:
        if not pawn_moves(0) and walls[0] == 0:
            say(g, "NO", "MOVES")
            g.turn = 1
            return
        dirs = (bu, br, bd, bl)
        for d in range(4):
            if dirs[d]:
                t = step_target(0, d)
                if t >= 0:
                    pos[0] = t
                    g.note_t = 0
                    if t < N:
                        g.winner = 0
                    g.turn = 1
                else:
                    say(g, "CANT", "GO", "THERE")
                return
        if ba:
            if walls[0] == 0:
                say(g, "NO", "WALLS", "LEFT")
            else:
                g.wmode = True
                g.wori = 0
                g.note_t = 0
                g.wr = min(pos[1] // N, M - 1)      # starts right in front of the CPU
                g.wc = min(pos[1] % N, M - 1)
                g.wok = wall_valid(0, g.wr, g.wc)
        return

    # wall mode
    moved = False
    if bu and g.wr > 0:
        g.wr -= 1
        moved = True
    if bd and g.wr < M - 1:
        g.wr += 1
        moved = True
    if bl and g.wc > 0:
        g.wc -= 1
        moved = True
    if br and g.wc < M - 1:
        g.wc += 1
        moved = True
    if bb:
        if g.wori == 0:
            g.wori = 1              # turn it upright
            moved = True
        else:
            g.wmode = False         # second press = back out
            return
    if moved:
        g.wok = wall_valid(g.wori, g.wr, g.wc)
    if ba:
        if g.wok:
            apply(0, 100 + g.wori * 100 + g.wr * 10 + g.wc)
            g.wmode = False
            g.turn = 1
        else:
            say(g, "NOT", "HERE")


def status_lines(g):
    if g.state == 3:
        return ("YOU", "WIN!") if g.winner == 0 else ("CPU", "WINS")
    if g.msg_t > 0:
        return g.msg
    if g.turn == 1:
        return ("CPU", "THINKS")
    if g.wmode:
        return ("WALL", "A:PUT", "B:TURN" if g.wori == 0 else "B:BACK")
    if g.note_t > 0:
        return g.note
    return ("YOUR", "MOVE", "A:WALL")


def main():
    g = G()
    g.level = 1
    g.wins = 0
    g.losses = 0
    g.state = 0
    g.page = 0
    g.frame = 0
    g.turn = 0
    g.winner = -1
    g.wmode = False
    g.wori = 0
    g.wr = 0
    g.wc = 0
    g.wok = False
    g.msg = None
    g.msg_t = 0
    g.note = None
    g.note_t = 0
    g.flash = None
    g.flash_pawn = False
    g.flash_t = 0
    g.over_t = 0
    load_save(g)
    random.seed(time.ticks_us())
    reset()
    thumby.display.setFPS(30)

    while True:
        g.frame += 1
        bu = thumby.buttonU.justPressed()
        br = thumby.buttonR.justPressed()
        bd = thumby.buttonD.justPressed()
        bl = thumby.buttonL.justPressed()
        ba = thumby.buttonA.justPressed()
        bb = thumby.buttonB.justPressed()
        s = g.state

        if s == 0:
            if bl:
                g.level = (g.level - 1) % 4
            if br:
                g.level = (g.level + 1) % 4
            if bb:
                g.state = 1
                g.page = 0
            elif ba:
                store_save(g)
                start_game(g)
            else:
                draw_title(g)

        elif s == 1:
            if ba:
                g.page += 1
                if g.page >= len(HELP):
                    g.state = 0
            if bb:
                g.state = 0
            if g.state == 1:
                draw_help(g)

        elif s == 2:
            if g.msg_t > 0:
                g.msg_t -= 1
            if g.note_t > 0:
                g.note_t -= 1
            if g.flash_t > 0:
                g.flash_t -= 1
            if g.turn == 1:
                draw_play(g, status_lines(g))
                thumby.display.update()
                gc.collect()
                code = ai_think(1, g.level)
                g.flash = None
                g.flash_pawn = False
                if code is not None:
                    apply(1, code)
                    if code >= 100:
                        rc = code % 100
                        g.flash = (code // 100 - 1, (rc // 10) * M + rc % 10)
                        g.note = ("CPU", "WALLED")
                    else:
                        g.flash_pawn = True
                        g.note = ("CPU", "MOVED")
                    g.flash_t = 60
                    g.note_t = 60
                if pos[1] >= NN - N:
                    g.winner = 1
                g.turn = 0
                g.wmode = False
            else:
                human_turn(g, bu, br, bd, bl, ba, bb)
            if g.winner >= 0:
                g.state = 3
                g.over_t = 0
                g.flash_t = 0
                if g.winner == 0:
                    g.wins += 1
                else:
                    g.losses += 1
                store_save(g)
            draw_play(g, status_lines(g))

        elif s == 3:
            g.over_t += 1
            if g.over_t > 45 or ba or bb:
                g.state = 4
            draw_play(g, status_lines(g))

        else:
            if ba:
                start_game(g)
            elif bb:
                g.state = 0
            draw_result(g)

        thumby.display.update()


main()
