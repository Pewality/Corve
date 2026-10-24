# ThumbyChat v4 - a tiny chatbot for the Thumby (MicroPython). ONE app file.
#
# Install on a real Thumby in /Games/ThumbyChat/ :
#   ThumbyChat.py  chatbrain.py  starters.py  chat.dat  ThumbyChat.bin
# Web emulator: tabs ThumbyChat.py  chatbrain.py  starters.py  chatdata.py
#
# Controls
#   Chat      : B = QUICK menu (sentence starters), A = type, UP/DOWN = scroll
#   Quick menu: UP/DOWN = move, A = pick, B = back
#   Picker    : appears when I ask you to choose. D-pad = move, A = pick, B = close
#   Keyboard  : QWERTY. D-pad = move, A = press key, B = backspace (B on empty = back)
#               bottom row: 12/ab = numbers/symbols, SPC, DEL, SEND
#
# If something goes wrong the error is shown on the screen (UP/DOWN scrolls)
# instead of the Thumby restarting.
import sys
import gc
sys.path.insert(0, "/Games/ThumbyChat")
import thumby


def show_error(e):
    try:
        sys.print_exception(e)
    except Exception:
        pass
    msg = "ERROR! " + repr(e)
    rows = [msg[i:i + 12] for i in range(0, min(len(msg), 240), 12)]
    top = 0
    while True:
        thumby.display.fill(0)
        for i in range(5):
            if top + i < len(rows):
                thumby.display.drawText(rows[top + i], 0, i * 8, 1)
        thumby.display.update()
        if thumby.buttonD.justPressed() and top < len(rows) - 5:
            top += 1
        if thumby.buttonU.justPressed() and top > 0:
            top -= 1


def stage(n, what):
    gc.collect()
    thumby.display.fill(0)
    thumby.display.drawText("Loading", 0, 0, 1)
    thumby.display.drawText("%d/3 %s" % (n, what), 0, 12, 1)
    try:
        thumby.display.drawText("RAM %dK" % (gc.mem_free() // 1024), 0, 24, 1)
    except Exception:
        pass
    thumby.display.update()


try:
    stage(1, "starters")
    import starters as S
    stage(2, "brain")
    import chatbrain as B
    D = B.D
    stage(3, "go!")
    gc.collect()

    W = 11          # characters per chat line


    def wrap(text):
        ws = []
        for w in text.split():
            while len(w) > W:
                ws.append(w[:W])
                w = w[W:]
            ws.append(w)
        res = []
        cur = ""
        for w in ws:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= W:
                cur += " " + w
            else:
                res.append(cur)
                cur = w
        if cur:
            res.append(cur)
        return res or [""]


    def draw_lines(view):
        n = len(view)
        for i in range(n):
            s, who = view[i]
            y = (5 - n + i) * 8
            if who:     # your message: inverted bubble on the right
                wpx = len(s) * 6 + 2
                x0 = 72 - wpx
                thumby.display.drawFilledRectangle(x0, y, wpx, 8, 1)
                thumby.display.drawText(s, x0 + 2, y + 1, 0)
            else:       # bot: text with a bar on the left
                thumby.display.drawLine(0, y, 0, y + 7, 1)
                thumby.display.drawText(s, 3, y + 1, 1)


    def title_bar(t):
        thumby.display.drawFilledRectangle(0, 0, 72, 8, 1)
        thumby.display.drawText(t[:11], 1, 1, 0)


    def draw_list(title, items, sel, top, tick):
        title_bar("%s %d/%d" % (title[:5], sel + 1, len(items)))
        for i in range(4):
            j = top + i
            if j >= len(items):
                break
            y = 8 + i * 8
            s = items[j]
            starter = s.endswith(" ") or s.endswith("#")
            if s.endswith("#"):
                s = s[:-1] + " "
            if starter:
                s = s.rstrip() + "_"
            if j == sel:
                thumby.display.drawFilledRectangle(0, y, 72, 8, 1)
                if len(s) > 11:
                    span = len(s) - 11 + 4
                    o = min((tick // 5) % span, len(s) - 11)
                    s = s[o:o + 11]
                thumby.display.drawText(s, 1, y + 1, 0)
            else:
                thumby.display.drawText(s[:11], 1, y + 1, 1)


    def keep_in_view(sel, top):
        if sel < top:
            return sel
        if sel > top + 3:
            return sel - 3
        return top


    PAGES = (
        ("qwertyuiop", "asdfghjkl'", "zxcvbnm,.?"),
        ("1234567890", "-+*/=()%:;", "!?.,'@#&_$"),
    )
    TOG = ("12", "ab")
    CMDX = (0, 12, 30, 48)
    CMDW = (12, 18, 18, 24)


    def cmd_from_col(c):
        x = 1 + c * 7 + 3
        for i in range(4):
            if x < CMDX[i] + CMDW[i]:
                return i
        return 3


    def col_from_cmd(i):
        return min(9, (CMDX[i] + CMDW[i] // 2) // 7)


    MAXLEN = 60


    # ------------------------------------------------------------- helpers
    lines = []          # (text, who)  who: 0 = bot, 1 = you


    def add(new):
        lines.extend(new)
        if len(lines) > 70:
            del lines[:len(lines) - 70]


    sf = 0              # first bot line being "typed out"
    shown = 0
    total = 0
    streaming = False
    off = 0             # chat scroll offset
    text = ""           # message being typed
    mode = 0            # 0 chat, 1 keyboard, 2 quick menu, 3 picker
    page = 0
    kr = 0
    kc = 0
    think = 0
    pending = ""
    pend_ask = None
    tick = 0

    # quick menu state
    slvl = 0            # 0 = groups, 1 = phrases
    csel = 0            # chosen group
    ssel = 0
    stop = 0
    CATS = tuple([g[0] for g in S.STARTERS])

    # picker state
    pk = None           # list of options, or None for a number range
    plo = 0
    phi = 0
    psel = 0
    ptop = 0


    def bot_say(msg):
        global sf, shown, total, streaming
        new = wrap(msg[:220])
        add([(s, 0) for s in new])
        sf = len(lines) - len(new)
        shown = 0
        total = 0
        for s in new:
            total += len(s) + 1
        streaming = True


    def send(s):
        global pending, mode, think, off
        pending = s
        add([(x, 1) for x in wrap(s)])
        mode = 0
        think = 12
        off = 0


    def open_picker(a):
        global mode, pk, plo, phi, psel, ptop
        mode = 3
        ptop = 0
        if a[0] == "#":
            pk = None
            plo = a[1]
            phi = a[2]
            psel = max(0, min(a[3] - plo, phi - plo))
            nr = (phi - plo) // 4 + 1
            ptop = min(max(0, psel // 4 - 1), max(0, nr - 4))
        else:
            pk = a
            psel = 0


    BTN = (thumby.buttonU, thumby.buttonD, thumby.buttonL, thumby.buttonR)
    hold = [0, 0, 0, 0]


    def step(i):
        """Button press with auto-repeat while held."""
        if BTN[i].pressed():
            hold[i] += 1
            return hold[i] == 1 or (hold[i] > 8 and hold[i] % 3 == 0)
        hold[i] = 0
        return False


    # -------------------------------------------------------------- splash
    thumby.display.setFPS(30)
    LOGO = None
    for p in ("/Games/ThumbyChat/ThumbyChat.bin", "ThumbyChat.bin"):
        try:
            f = open(p, "rb")
            LOGO = bytearray(f.read())
            f.close()
            break
        except OSError:
            pass
    if LOGO is None:
        try:
            import chatdata
            LOGO = bytearray(chatdata.LOGO)
        except Exception:
            LOGO = None

    if LOGO and len(LOGO) == 360:
        for i in range(70):
            thumby.display.fill(0)
            thumby.display.blit(LOGO, 0, 0, 72, 40, -1, 0, 0)
            rv = i * 3
            if rv < 72:
                thumby.display.drawFilledRectangle(rv, 0, 72 - rv, 40, 0)
                thumby.display.drawLine(rv, 0, rv, 39, 1)
            thumby.display.update()
            if thumby.buttonA.justPressed() or thumby.buttonB.justPressed():
                break
        LOGO = None
        gc.collect()

    # ---------------------------------------------------------------- main
    bot_say("Hi! I'm ThumbyGPT. Press B for quick replies or A to type!")

    while True:
        thumby.display.fill(0)
        tick += 1
        u = step(0)
        d = step(1)
        l = step(2)
        r = step(3)
        a = thumby.buttonA.justPressed()
        b = thumby.buttonB.justPressed()

        if mode == 0:
            # ---------------- chat screen ----------------
            if think:
                think -= 1
                if think == 0:
                    rep = B.reply(pending)
                    pend_ask = D.ask
                    D.ask = None
                    if D.clr:
                        D.clr = False
                        del lines[:]
                    bot_say(rep)
                    off = 0
                    gc.collect()
            elif streaming:
                shown += 2
                if shown >= total or a:
                    streaming = False
                    if pend_ask:
                        open_picker(pend_ask)
                        pend_ask = None
                off = 0
            else:
                if u and off < len(lines) - 5:
                    off += 1
                if d and off > 0:
                    off -= 1
                if a:
                    mode = 1
                    off = 0
                elif b:
                    mode = 2
                    slvl = 0
                    ssel = csel
                    stop = max(0, ssel - 3)

            src = lines
            if streaming:
                rem = shown
                part = []
                for item in lines[sf:]:
                    if rem <= 0:
                        break
                    part.append((item[0][:rem], item[1]))
                    rem -= len(item[0]) + 1
                src = lines[:sf] + part
            end = len(src) - off
            view = src[max(0, end - 5):end]
            if think:
                view = view[-4:] + [("." * (1 + (tick // 5) % 3), 0)]
            draw_lines(view)
            if off < len(src) - 5 and not think:
                thumby.display.setPixel(70, 0, 1)
                thumby.display.setPixel(69, 1, 1)
                thumby.display.setPixel(71, 1, 1)
            if off > 0:
                thumby.display.setPixel(69, 38, 1)
                thumby.display.setPixel(71, 38, 1)
                thumby.display.setPixel(70, 39, 1)

        elif mode == 1:
            # ---------------- keyboard screen ----------------
            if l or r:
                cols = 10 if kr < 3 else 4
                kc = (kc + (1 if r else -1)) % cols
            if u or d:
                nr = (kr + (1 if d else -1)) % 4
                if kr < 3 and nr == 3:
                    kc = cmd_from_col(kc)
                elif kr == 3 and nr < 3:
                    kc = col_from_cmd(kc)
                kr = nr
            if a:
                if kr < 3:
                    if len(text) < MAXLEN:
                        text += PAGES[page][kr][kc]
                elif kc == 0:
                    page = 1 - page
                elif kc == 1:
                    if len(text) < MAXLEN:
                        text += " "
                elif kc == 2:
                    text = text[:-1]
                elif text.strip():
                    s = text.strip()
                    text = ""
                    send(s)
            if b:
                if text:
                    text = text[:-1]
                else:
                    mode = 0

            if mode == 1:
                thumby.display.drawRectangle(0, 0, 72, 9, 1)
                cur = "_" if (tick // 8) % 2 else " "
                thumby.display.drawText(text[-10:] + cur, 2, 1, 1)
                pg = PAGES[page]
                for row in range(3):
                    y = 10 + row * 8
                    for c in range(10):
                        x = 1 + c * 7
                        if row == kr and c == kc:
                            thumby.display.drawFilledRectangle(x, y - 1, 7, 8, 1)
                            thumby.display.drawText(pg[row][c], x + 1, y, 0)
                        else:
                            thumby.display.drawText(pg[row][c], x + 1, y, 1)
                labels = (TOG[page], "SPC", "DEL", "SEND")
                for i in range(4):
                    if kr == 3 and kc == i:
                        thumby.display.drawFilledRectangle(CMDX[i], 32, CMDW[i], 8, 1)
                        thumby.display.drawText(labels[i], CMDX[i] + 1, 33, 0)
                    else:
                        thumby.display.drawText(labels[i], CMDX[i] + 1, 33, 1)

        elif mode == 2:
            # ---------------- quick menu (sentence starters) ----------------
            items = CATS if slvl == 0 else S.STARTERS[csel][1]
            if u:
                ssel = max(0, ssel - 1)
            if d:
                ssel = min(len(items) - 1, ssel + 1)
            stop = keep_in_view(ssel, stop)
            if a:
                if slvl == 0:
                    csel = ssel
                    slvl = 1
                    ssel = 0
                    stop = 0
                else:
                    s = items[ssel]
                    if s.endswith(" ") or s.endswith("#"):
                        page = 1 if s.endswith("#") else 0
                        text = s[:-1] if s.endswith("#") else s
                        kr = 0
                        kc = 0
                        mode = 1
                    else:
                        send(s)
            elif b:
                if slvl == 1:
                    slvl = 0
                    ssel = csel
                    stop = max(0, ssel - 3)
                else:
                    mode = 0
            if mode == 2:
                items = CATS if slvl == 0 else S.STARTERS[csel][1]
                draw_list("Quick" if slvl == 0 else CATS[csel], items, ssel, stop, tick)

        else:
            # ---------------- picker (when I ask you to choose) ----------------
            if pk is None:
                n = phi - plo + 1
                if l:
                    psel -= 1
                if r:
                    psel += 1
                if u:
                    psel -= 4
                if d:
                    psel += 4
                psel = max(0, min(n - 1, psel))
                ptop = keep_in_view(psel // 4, ptop)
            else:
                n = len(pk)
                if u:
                    psel -= 1
                if d:
                    psel += 1
                psel = max(0, min(n - 1, psel))
                ptop = keep_in_view(psel, ptop)
            if a:
                s = str(plo + psel) if pk is None else pk[psel]
                send(s)
            elif b:
                mode = 0
            if mode == 3:
                if pk is None:
                    title_bar("Pick %d-%d" % (plo, phi))
                    for row in range(4):
                        for col in range(4):
                            idx = (ptop + row) * 4 + col
                            if idx >= n:
                                break
                            s = str(plo + idx)
                            x = col * 18 + (18 - (len(s) * 6 - 1)) // 2
                            y = 8 + row * 8
                            if idx == psel:
                                thumby.display.drawFilledRectangle(col * 18, y, 18, 8, 1)
                                thumby.display.drawText(s, x, y + 1, 0)
                            else:
                                thumby.display.drawText(s, x, y + 1, 1)
                else:
                    draw_list("Pick", pk, psel, ptop, tick)

        thumby.display.update()

except Exception as e:
    show_error(e)
