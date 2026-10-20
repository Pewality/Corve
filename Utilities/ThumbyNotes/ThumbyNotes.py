# ThumbyNotes v3 - iPhone-Notes-style notes app for the original Thumby
#
# NOTES LIST
#   Up/Down : choose a note         A : open  (or "+ New note")
#   B       : delete the chosen note (A = yes, B = no)
#   Notes with checkboxes show their progress, e.g. 2/5
#
# READING A NOTE  (top bar:  < Notes ........ [EDIT])
#   Up/Down    : scroll          A : EDIT (open keyboard)      B : back to list
#   Left/Right : move cursor  -- or, on a checkbox line, TICK / UNTICK it
#
# KEYBOARD (QWERTY)
#   D-pad = pick key, A = press key, B = backspace
#   Bottom row:  [MODE] [space] [<-] [new line] [DONE]
#   MODE cycles:  abc -> 12 (numbers/symbols) -> :) (emoji/special) -> LS (lists + cursor tools)
#   The arrow-up key is SHIFT. First letter of a sentence is auto-capitalised.
#
# LS layer (lists + tools)
#   row 1:  [bullet] [1.] [checkbox] [tick/untick the line's checkbox]
#   row 2:  cursor  left / right / up / down
#   row 3:  HOME  END  CUT (delete the whole line)
#   Pressing new-line on a list item automatically starts the next item.
#   Pressing new-line on an EMPTY item ends the list.

import thumby
import os

thumby.display.setFPS(30)
thumby.display.setFont("/lib/font5x7.bin", 5, 7, 1)

BASE = "/Saves/ThumbyNotes"
COLS = 11          # characters per line
MAXLEN = 1500      # max characters per note

# ------------------------------------------------------------ special glyphs
# Stored in the note as control characters 14..31 and drawn as 5x7 pictures.
GLY = [
    (0, 0, 14, 14, 14, 0, 0),        # 0  bullet
    (0, 31, 17, 17, 17, 31, 0),      # 1  empty checkbox
    (0, 31, 27, 21, 27, 31, 0),      # 2  ticked checkbox (X in box)
    (0, 10, 31, 31, 14, 4, 0),       # 3  heart
    (4, 4, 31, 14, 10, 17, 0),       # 4  star
    (14, 31, 21, 31, 21, 27, 14),    # 5  smile
    (14, 31, 21, 31, 27, 21, 14),    # 6  sad
    (0, 1, 2, 20, 8, 0, 0),          # 7  tick
    (0, 17, 10, 4, 10, 17, 0),       # 8  cross
    (0, 4, 2, 31, 2, 4, 0),          # 9  arrow right
    (0, 4, 8, 31, 8, 4, 0),          # 10 arrow left
    (4, 14, 21, 4, 4, 4, 0),         # 11 arrow up
    (4, 4, 4, 21, 14, 4, 0),         # 12 arrow down
    (4, 21, 14, 31, 14, 21, 4),      # 13 sun
    (6, 12, 24, 24, 24, 12, 6),      # 14 moon
    (3, 6, 12, 31, 6, 12, 24),       # 15 lightning
    (6, 5, 4, 4, 12, 28, 8),         # 16 music note
    (4, 14, 31, 17, 17, 17, 31),     # 17 house
]
NG = len(GLY)
G0 = 14


def g(i):
    return chr(G0 + i)


BUL = g(0)
BOX = g(1)
BOXX = g(2)
MARKS = BUL + BOX + BOXX


def draw_glyph(i, x, y, c):
    d = thumby.display
    rows = GLY[i]
    for r in range(7):
        v = rows[r]
        if v:
            for col in range(5):
                if v & (16 >> col):
                    d.setPixel(x + col, y + r, c)


def draw_rich(s, x, y, c):
    # text with inline glyphs; every character is 6px wide
    d = thumby.display
    run = ""
    cx = x
    for ch in s:
        o = ord(ch)
        if G0 <= o < G0 + NG:
            if run:
                d.drawText(run, cx, y, c)
                cx += len(run) * 6
                run = ""
            draw_glyph(o - G0, cx, y, c)
            cx += 6
        else:
            run += ch
    if run:
        d.drawText(run, cx, y, c)


def round_rect(x, y, w, h):
    d = thumby.display
    d.drawFilledRectangle(x, y, w, h, 1)
    d.setPixel(x, y, 0)
    d.setPixel(x + w - 1, y, 0)
    d.setPixel(x, y + h - 1, 0)
    d.setPixel(x + w - 1, y + h - 1, 0)


# ------------------------------------------------------------ storage
def ensure_dir():
    for p in ("/Saves", BASE):
        try:
            os.mkdir(p)
        except OSError:
            pass


def path(i):
    return BASE + "/n" + str(i) + ".txt"


def note_ids():
    ids = []
    try:
        for f in os.listdir(BASE):
            if f.startswith("n") and f.endswith(".txt"):
                try:
                    ids.append(int(f[1:-4]))
                except ValueError:
                    pass
    except OSError:
        pass
    ids.sort()
    return ids


def load(i):
    try:
        with open(path(i)) as f:
            return f.read()
    except OSError:
        return ""


def info(i):
    # (title, total checkboxes, ticked checkboxes)
    s = load(i)
    first = ""
    for ln in s.split("\n"):
        ln = ln.strip()
        while ln and (ln[0] in MARKS or ln[0] == " "):
            ln = ln[1:]
        if ln:
            first = ln
            break
    if first == "":
        first = "Untitled"
    done = s.count(BOXX)
    return first, done + s.count(BOX), done


def commit(nid, text):
    # empty notes are removed instead of saved
    try:
        if text == "":
            os.remove(path(nid))
        else:
            with open(path(nid), "w") as f:
                f.write(text)
    except OSError:
        pass


def refresh():
    ids = note_ids()
    return ids, [info(i) for i in ids]


# ------------------------------------------------------------ input
hold = {}
prev = {}


def rep(name, b):
    if b.pressed():
        c = hold.get(name, 0) + 1
        hold[name] = c
        return c == 1 or (c > 10 and c % 3 == 0)
    hold[name] = 0
    return False


def edge(name, b):
    p = b.pressed()
    r = p and not prev.get(name, False)
    prev[name] = p
    return r


def poll():
    return (rep('u', thumby.buttonU), rep('d', thumby.buttonD),
            rep('l', thumby.buttonL), rep('r', thumby.buttonR),
            edge('a', thumby.buttonA), edge('b', thumby.buttonB),
            rep('b', thumby.buttonB))


# ------------------------------------------------------------ text layout
def wrap(t):
    lines = []
    s = 0
    n = len(t)
    while True:
        e = s
        while e < n and t[e] != "\n" and e - s < COLS:
            e += 1
        if e >= n:
            lines.append((s, e))
            break
        if t[e] == "\n" or t[e] == " ":
            lines.append((s, e))
            s = e + 1
            continue
        k = t.rfind(" ", s, e)
        if k > s:
            lines.append((s, k))
            s = k + 1
        else:
            lines.append((s, e))
            s = e
    return lines


def locate(lines, cur):
    for i in range(len(lines)):
        s, e = lines[i]
        if s <= cur <= e:
            if cur == e and i + 1 < len(lines) and lines[i + 1][0] == e:
                continue
            return i, cur - s
    return len(lines) - 1, 0


def autocap(t, cur):
    if cur == 0:
        return True
    p = t[cur - 1]
    if p == "\n":
        return True
    if p == " " and cur >= 2 and t[cur - 2] in ".!?" + MARKS:
        return True
    return False


# ------------------------------------------------------------ list tools
def marker(t, ls):
    # kind: 0 none, 1 bullet, 2 empty box, 3 ticked box, 4 number
    c = t[ls:ls + 1]
    if c == "":
        return 0, 0
    if t[ls + 1:ls + 2] == " ":
        if c == BUL:
            return 1, 2
        if c == BOX:
            return 2, 2
        if c == BOXX:
            return 3, 2
    j = ls
    n = len(t)
    while j < n and j - ls < 3 and t[j].isdigit():
        j += 1
    if j > ls and t[j:j + 2] == ". ":
        return 4, j - ls + 2
    return 0, 0


def line_start(t, cur):
    return t.rfind("\n", 0, cur) + 1


def set_marker(t, cur, newm):
    ls = line_start(t, cur)
    k, ln = marker(t, ls)
    t = t[:ls] + newm + t[ls + ln:]
    if cur >= ls + ln:
        cur = cur - ln + len(newm)
    else:
        cur = ls + len(newm)
    return t, cur


def tool_bullet(t, cur):
    k, ln = marker(t, line_start(t, cur))
    return set_marker(t, cur, "" if k == 1 else BUL + " ")


def tool_todo(t, cur):
    k, ln = marker(t, line_start(t, cur))
    return set_marker(t, cur, "" if k in (2, 3) else BOX + " ")


def tool_tick(t, cur):
    k, ln = marker(t, line_start(t, cur))
    if k == 2:
        return set_marker(t, cur, BOXX + " ")
    if k == 3:
        return set_marker(t, cur, BOX + " ")
    return t, cur


def tool_num(t, cur):
    ls = line_start(t, cur)
    k, ln = marker(t, ls)
    if k == 4:
        return set_marker(t, cur, "")
    n = 1
    if ls > 0:
        ps = t.rfind("\n", 0, ls - 1) + 1
        pk, pl = marker(t, ps)
        if pk == 4:
            n = int(t[ps:ps + pl - 2]) + 1
    return set_marker(t, cur, str(n) + ". ")


def tool_newline(t, cur):
    ls = line_start(t, cur)
    k, ln = marker(t, ls)
    ins = "\n"
    if k and cur >= ls + ln:
        le = t.find("\n", cur)
        if le < 0:
            le = len(t)
        if t[ls + ln:le] == "":
            return set_marker(t, cur, "")        # empty item ends the list
        if k == 1:
            ins += BUL + " "
        elif k in (2, 3):
            ins += BOX + " "
        else:
            ins += str(int(t[ls:ls + ln - 2]) + 1) + ". "
    if len(t) + len(ins) > MAXLEN:
        return t, cur
    return t[:cur] + ins + t[cur:], cur + len(ins)


def tool_cut(t, cur):
    ls = line_start(t, cur)
    le = t.find("\n", cur)
    if le < 0:
        le = len(t)
        if ls > 0:
            ls -= 1
    else:
        le += 1
    t = t[:ls] + t[le:]
    return t, min(ls, len(t))


# ------------------------------------------------------------ keyboard
def row(tokens, widths=None, x0=1):
    out = []
    x = x0
    for i in range(len(tokens)):
        w = widths[i] if widths else 7
        out.append((tokens[i], x, w))
        x += w
    return out


BOT = row(["MODE", "SP", "BS", "NL", "DONE"], [12, 14, 10, 10, 26], 0)


def letters(upper):
    def f(s):
        return [t.upper() if upper and t.isalpha() else t for t in s]
    return [row(f("qwertyuiop")),
            row(f("asdfghjkl'")),
            row(["SH"] + f("zxcvbnm") + [".", ","], [9] + [7] * 9, 0),
            BOT]


KB = [
    letters(False),                                       # 0 abc
    letters(True),                                        # 1 ABC (shift)
    [row(list("1234567890")),                             # 2 numbers/symbols
     row(list('-/:;()$&@"')),
     row(list(".,?!'#%*+=")),
     BOT],
    [row([g(3), g(4), g(5), g(6), g(7), g(8), g(13), g(14), g(15), g(16)]),   # 3 emoji
     row([g(17), g(9), g(10), g(11), g(12)] + list("~^|\\_")),
     row(list("[]{}<>`"), [10] * 7, 1),
     BOT],
    [row(["T_BUL", "T_NUM", "T_BOX", "T_TICK"], [18] * 4, 0),                 # 4 lists/tools
     row(["CL", "CR", "CU", "CD"], [18] * 4, 0),
     row(["HOME", "END", "CUT"], [24] * 3, 0),
     BOT],
]

NEXT = {0: 2, 2: 3, 3: 4, 4: 0}
MODE_LABEL = {0: "12", 2: ":)", 3: "LS", 4: "ab"}
ICONS = {"T_BUL": 0, "T_BOX": 1, "T_TICK": 2, "CL": 10, "CR": 9, "CU": 11, "CD": 12}
LABELS = {"T_NUM": "1.", "HOME": "HOME", "END": "END", "CUT": "CUT", "DONE": "DONE"}


def pick(rw, cx):
    for j in range(len(rw)):
        t, x, w = rw[j]
        if x <= cx < x + w:
            return j
    return 0 if cx < rw[0][1] else len(rw) - 1


def draw_key(tok, x, y, w, sel, label, caps):
    d = thumby.display
    c = 1
    if sel:
        round_rect(x, y, w, 8)
        c = 0
    cx = x + w // 2
    if len(tok) == 1:
        o = ord(tok)
        if G0 <= o < G0 + NG:
            draw_glyph(o - G0, x + (w - 5) // 2, y + 1, c)
        else:
            d.drawText(tok, x + (w - 5) // 2, y + 1, c)
    elif tok in ICONS:
        draw_glyph(ICONS[tok], x + (w - 5) // 2, y + 1, c)
    elif tok == "MODE" or tok in LABELS:
        s = label if tok == "MODE" else LABELS[tok]
        tw = len(s) * 6 - 1
        d.drawText(s, x + (w - tw) // 2, y + 1, c)
    elif tok == "SH":
        d.drawLine(cx, y + 1, cx, y + 6, c)
        d.drawLine(cx, y + 1, cx - 3, y + 4, c)
        d.drawLine(cx, y + 1, cx + 3, y + 4, c)
        if caps and not sel:
            d.drawRectangle(x, y, w, 8, 1)
    elif tok == "SP":
        d.drawLine(x + 3, y + 3, x + 3, y + 6, c)
        d.drawLine(x + 3, y + 6, x + w - 4, y + 6, c)
        d.drawLine(x + w - 4, y + 6, x + w - 4, y + 3, c)
    elif tok == "BS":
        d.drawLine(cx - 3, y + 4, cx + 3, y + 4, c)
        d.drawLine(cx - 3, y + 4, cx - 1, y + 2, c)
        d.drawLine(cx - 3, y + 4, cx - 1, y + 6, c)
    elif tok == "NL":
        d.drawLine(x + 7, y + 2, x + 7, y + 5, c)
        d.drawLine(x + 2, y + 5, x + 7, y + 5, c)
        d.drawLine(x + 2, y + 5, x + 4, y + 3, c)
        d.drawLine(x + 2, y + 5, x + 4, y + 7, c)


def draw_keyboard(idx, layer, kr, ki, caps):
    lab = MODE_LABEL[layer]
    for r in range(4):
        y = 8 + r * 8
        rw = KB[idx][r]
        for i in range(len(rw)):
            t, x, w = rw[i]
            draw_key(t, x, y, w, r == kr and i == ki, lab, caps)


# ------------------------------------------------------------ editor
def edit_note(nid, text, new):
    d = thumby.display
    cur = len(text)
    mode = 1 if new else 0          # 0 = reading, 1 = keyboard
    layer = 0
    shift = False
    kr = 1
    ki = 0
    top = 0
    dirty = False
    frame = 0
    lines = wrap(text)

    while True:
        frame += 1
        u, dn, l, r, a, b, brep = poll()
        cl, cc = locate(lines, cur)
        caps = (shift != autocap(text, cur))
        idx = 1 if (layer == 0 and caps) else layer
        kb = KB[idx]
        old = text

        if mode == 0:
            # ----- reading mode
            ls = line_start(text, cur)
            if u:
                if cl > 0:
                    s, e = lines[cl - 1]
                    cur = s + min(cc, e - s)
                else:
                    cur = 0
            elif dn:
                if cl < len(lines) - 1:
                    s, e = lines[cl + 1]
                    cur = s + min(cc, e - s)
                else:
                    cur = len(text)
            elif l or r:
                if marker(text, ls)[0] in (2, 3):
                    text, cur = tool_tick(text, cur)
                elif l:
                    cur = max(0, cur - 1)
                else:
                    cur = min(len(text), cur + 1)
            elif a:
                mode = 1
            elif b:
                if dirty or text != old:
                    commit(nid, text)
                return
        else:
            # ----- keyboard mode
            if u or dn:
                t, x, w = kb[kr][ki]
                kr = (kr + (-1 if u else 1)) % 4
                ki = pick(kb[kr], x + w // 2)
            elif l:
                ki = (ki - 1) % len(kb[kr])
            elif r:
                ki = (ki + 1) % len(kb[kr])
            elif brep:
                if cur > 0:
                    text = text[:cur - 1] + text[cur:]
                    cur -= 1
            elif a:
                tok = kb[kr][ki][0]
                room = len(text) < MAXLEN - 6
                if tok == "MODE":
                    t, x, w = kb[kr][ki]
                    layer = NEXT[layer]
                    shift = False
                    ki = pick(KB[layer][kr], x + w // 2)
                elif tok == "DONE":
                    mode = 0
                    if dirty:
                        commit(nid, text)
                        dirty = False
                elif tok == "SH":
                    shift = not shift
                elif tok == "BS":
                    if cur > 0:
                        text = text[:cur - 1] + text[cur:]
                        cur -= 1
                elif tok == "NL":
                    text, cur = tool_newline(text, cur)
                elif tok == "SP":
                    if room:
                        text = text[:cur] + " " + text[cur:]
                        cur += 1
                elif tok == "T_BUL":
                    if room:
                        text, cur = tool_bullet(text, cur)
                elif tok == "T_NUM":
                    if room:
                        text, cur = tool_num(text, cur)
                elif tok == "T_BOX":
                    if room:
                        text, cur = tool_todo(text, cur)
                elif tok == "T_TICK":
                    text, cur = tool_tick(text, cur)
                elif tok == "CL":
                    cur = max(0, cur - 1)
                elif tok == "CR":
                    cur = min(len(text), cur + 1)
                elif tok == "CU":
                    if cl > 0:
                        s, e = lines[cl - 1]
                        cur = s + min(cc, e - s)
                elif tok == "CD":
                    if cl < len(lines) - 1:
                        s, e = lines[cl + 1]
                        cur = s + min(cc, e - s)
                elif tok == "HOME":
                    cur = lines[cl][0]
                elif tok == "END":
                    cur = lines[cl][1]
                elif tok == "CUT":
                    text, cur = tool_cut(text, cur)
                else:
                    if room:
                        text = text[:cur] + tok + text[cur:]
                        cur += 1
                    shift = False

        if text != old:
            dirty = True
            lines = wrap(text)
        cl, cc = locate(lines, cur)

        # ----- scrolling
        rows = 4 if mode == 0 else 1
        maxtop = max(0, len(lines) - rows)
        if top > maxtop:
            top = maxtop
        if cl < top:
            top = cl
        if cl >= top + rows:
            top = cl - rows + 1

        # ----- draw
        d.fill(0)
        yb = 9 if mode == 0 else 0
        for rr in range(rows):
            i = top + rr
            if i >= len(lines):
                break
            s, e = lines[i]
            draw_rich(text[s:e], 1, yb + rr * 8, 1)

        if (frame // 12) % 2 == 0:
            cy = yb + (cl - top) * 8
            cx = cc * 6
            d.drawLine(cx, cy, cx, cy + 6, 1)

        if mode == 0:
            on_box = marker(text, line_start(text, cur))[0] in (2, 3)
            if on_box:
                d.drawText("<>:TICK", 0, 0, 1)
            else:
                d.drawLine(3, 0, 0, 3, 1)
                d.drawLine(0, 3, 3, 6, 1)
                d.drawText("Notes", 6, 0, 1)
            round_rect(44, 0, 28, 8)
            d.drawText("EDIT", 46, 1, 0)
            if len(lines) > rows:
                h = max(3, 31 * rows // len(lines))
                by = 9 + (31 - h) * top // (len(lines) - rows)
                d.drawLine(71, by, 71, by + h - 1, 1)
        else:
            d.drawLine(0, 7, 71, 7, 1)
            draw_keyboard(idx, layer, kr, ki, caps)

        d.update()


# ------------------------------------------------------------ front page
def splash():
    d = thumby.display
    for f in range(28):
        d.fill(0)
        d.drawRectangle(6, 5, 20, 28, 1)
        d.drawFilledRectangle(6, 5, 20, 5, 1)
        draw_glyph(1, 10, 13, 1)
        d.drawLine(18, 16, 23, 16, 1)
        draw_glyph(2, 10, 21, 1)
        d.drawLine(18, 24, 23, 24, 1)
        d.drawText("Notes", 32, 11, 1)
        d.drawLine(32, 21, 62, 21, 1)
        d.drawText("v3", 32, 25, 1)
        d.update()


def note_list():
    ids, infos = refresh()
    sel = 0
    top = 0
    confirm = False
    d = thumby.display

    while True:
        u, dn, l, r, a, b, brep = poll()
        n = len(ids) + 1

        if confirm:
            if a:
                try:
                    os.remove(path(ids[sel - 1]))
                except OSError:
                    pass
                ids, infos = refresh()
                n = len(ids) + 1
                sel = min(sel, n - 1)
                confirm = False
            elif b:
                confirm = False
        else:
            if u:
                sel = (sel - 1) % n
            if dn:
                sel = (sel + 1) % n
            if a:
                if sel == 0:
                    nid = (ids[-1] + 1) if ids else 1
                    edit_note(nid, "", True)
                else:
                    nid = ids[sel - 1]
                    edit_note(nid, load(nid), False)
                ids, infos = refresh()
                n = len(ids) + 1
                sel = (ids.index(nid) + 1) if nid in ids else 0
            elif b and sel > 0:
                confirm = True

        if sel < top:
            top = sel
        if sel >= top + 4:
            top = sel - 3

        d.fill(0)
        if confirm:
            d.drawRectangle(2, 2, 68, 36, 1)
            d.drawText("Delete?", 15, 5, 1)
            d.drawText(infos[sel - 1][0][:10], 6, 15, 1)
            d.drawText("A:Yes  B:No", 6, 27, 1)
        else:
            d.drawText("Notes", 1, 0, 1)
            if sel > 0:
                d.drawText("B:DEL", 42, 0, 1)
            else:
                cs = str(len(ids))
                d.drawText(cs, 70 - (len(cs) * 6 - 1), 0, 1)
            d.drawLine(0, 7, 71, 7, 1)

            for rr in range(4):
                i = top + rr
                if i >= n:
                    break
                y = 8 + rr * 8
                c = 1
                if i == sel:
                    round_rect(0, y, 70, 8)
                    c = 0
                if i == 0:
                    d.drawLine(2, y + 4, 6, y + 4, c)
                    d.drawLine(4, y + 2, 4, y + 6, c)
                    d.drawText("New note", 10, y + 1, c)
                else:
                    ttl, tot, dn_ = infos[i - 1]
                    room = 11
                    if tot:
                        badge = str(dn_) + "/" + str(tot)
                        bw = len(badge) * 6 - 1
                        d.drawText(badge, 68 - bw, y + 1, c)
                        room = (68 - bw - 4) // 6
                    draw_rich(ttl[:room], 2, y + 1, c)

            if n > 4:
                h = max(3, 32 * 4 // n)
                by = 8 + (32 - h) * top // (n - 4)
                d.drawLine(71, by, 71, by + h - 1, 1)

        d.update()


ensure_dir()
splash()
note_list()
