# chatbrain.py - the "thinking" part of ThumbyChat (no screen code here)
# Questions, small talk, games, calculator and tools. Data comes from chat.dat
# (real Thumby) or from chatdata.py (web emulator).
import time
import random
import math
import starters as S


class D:
    """Shared conversation state (the screen reads D.ask and D.clr)."""
    st = 0          # quiz, riddle, guess, rps, mq, kk1, kk2, pickn, choose, yn
    sd = ""
    sn = 0
    ss = 0
    used = []
    likes = []
    mem = {}
    clr = False     # screen: clear the chat
    ask = None      # screen: show a picker (tuple of options or ("#", lo, hi, start))
    glo = 1
    ghi = 100


# ---- data lives in chat.dat (plain text, read from flash only when needed).
# If chat.dat is not there (e.g. the web emulator, which only takes .py
# files) the same text is loaded from the built-in copy in chatdata.py.
DAT = None
DATA = None
IDX = {}


def _index():
    global DAT, DATA
    for p in ("/Games/ThumbyChat/chat.dat", "chat.dat"):
        try:
            f = open(p)
        except OSError:
            continue
        pos = 0
        while True:
            ln = f.readline()
            if not ln:
                break
            pos += len(ln)
            if ln[0] == "#":
                IDX[ln[1:].strip()] = pos
        f.close()
        DAT = p
        return
    # web emulator: tiny pieces from chatdata.py (+ chatdata2.py if memory allows)
    import gc
    gc.collect()
    import chatdata
    DATA = list(chatdata.S)
    gc.collect()
    for k in range(len(DATA)):
        nm = DATA[k][0]
        if nm in IDX:
            IDX[nm].append(k)
        else:
            IDX[nm] = [k]


def scan(name):
    """Read a section one line at a time (uses almost no RAM)."""
    if DATA is None:
        f = open(DAT)
        f.seek(IDX[name])
        while True:
            ln = f.readline()
            if not ln:
                break
            ln = ln.strip()
            if ln[:1] == "#":
                break
            if ln:
                yield ln
        f.close()
    else:
        for k in IDX.get(name, ()):
            for ln in DATA[k][1].split("\n"):
                ln = ln.strip()
                if ln:
                    yield ln


def lines_of(name):
    """All lines of a small section (jokes, facts ...)."""
    return list(scan(name))


_index()


def pick(seq):
    return seq[random.randint(0, len(seq) - 1)]

def fmt(x):
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e12:
            return str(int(x))
        x = round(x, 4)
    return str(x)

def nums(s):
    out = []
    cur = ""
    for ch in s + " ":
        if ch.isdigit() or (ch == "." and cur and "." not in cur):
            cur += ch
        else:
            if cur and cur != ".":
                try:
                    out.append(float(cur))
                except ValueError:
                    pass
            cur = ""
    return out

def score(keys, ws):
    m = 0
    for tok in keys.split(" "):
        if "+" in tok:
            ps = tok.split("+")
            for p in ps:
                if p not in ws:
                    break
            else:
                m += len(ps)
        elif tok in ws:
            m += 1
    return m

D.pick = pick
D.fmt = fmt
D.nums = nums
D.score = score
D.lines_of = lines_of
D.scan = scan


# ------------------------------------------------------------ games
def chk(low):
    for a in D.sd.split("/"):
        if a in low:
            return True
    return False


def qnext():
    Q = D.lines_of("QUIZ")
    while True:
        i = random.randint(0, len(Q) - 1)
        if i not in D.used:
            break
    D.used.append(i)
    q = Q[i].split("|")
    D.sd = q[1]
    return "Q%d: %s" % (D.sn, q[0])


def offer(msg, act):
    D.st = "yn"
    D.sd = act
    D.ask = ("yes", "no")
    return msg


def g_quiz():
    D.st = "quiz"
    D.sn = 1
    D.ss = 0
    del D.used[:]
    return "Quiz time! 5 questions. " + qnext()


def g_riddle():
    r = D.pick(D.lines_of("RIDDLES")).split("|")
    D.st = "riddle"
    D.sd = r[1]
    D.sn = 0
    return r[0] + " (say give up to skip)"


def g_guess():
    D.st = "guess"
    D.sd = random.randint(1, 100)
    D.sn = 0
    D.glo = 1
    D.ghi = 100
    D.ask = ("#", 1, 100, 50)
    return "I'm thinking of a number from 1 to 100. Guess!"


def g_rps():
    D.ask = ("rock", "paper", "scissors", "quit")
    D.st = "rps"
    D.sn = 0
    D.ss = 0
    return "Rock, paper or scissors? (say quit to stop)"


def mqnext():
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    op = D.pick("+-*")
    if op == "-" and b > a:
        a, b = b, a
    r = a + b if op == "+" else (a - b if op == "-" else a * b)
    D.sd = r
    return "M%d: %d %s %d = ?" % (D.sn, a, "x" if op == "*" else op, b)


def g_mq():
    D.st = "mq"
    D.sn = 1
    D.ss = 0
    return "Math time! 5 sums. " + mqnext()


def g_kk():
    D.st = "kk1"
    return "Who's there?"


def play(t, low, words, ws):
    giveup = ("skip" in ws or "idk" in ws or "pass" in ws or
              ("give" in ws and "up" in ws))
    if D.st == "quiz":
        ok = (not giveup) and chk(low)
        if ok:
            D.ss += 1
            m = "Correct!"
        else:
            m = "It's " + D.sd.split("/")[0] + "."
        if D.sn >= 5:
            D.st = 0
            return offer("%s Score: %d/5. %s Again?" % (m, D.ss, "Genius!" if D.ss >= 4 else "Nice try!"), "quiz")
        D.sn += 1
        return m + " " + qnext()
    if D.st == "riddle":
        if chk(low) and not giveup:
            return offer(D.pick(("Yes! Nailed it!", "Correct! Smart cookie!")) + " Another?", "riddle")
        D.sn += 1
        if giveup or D.sn >= 3:
            return offer("It was: " + D.sd.split("/")[0] + ". Another?", "riddle")
        return "Nope, try again!"
    if D.st == "guess":
        if giveup:
            return offer("It was %d. Play again?" % D.sd, "guess")
        n = D.nums(low)
        if not n:
            D.ask = ("#", D.glo, D.ghi, (D.glo + D.ghi) // 2)
            return "Pick a number from %d to %d." % (D.glo, D.ghi)
        g = int(n[0])
        D.sn += 1
        if g == D.sd:
            return offer("Yes! It was %d. You took %d tries! Again?" % (D.sd, D.sn), "guess")
        if g < D.sd:
            D.glo = max(D.glo, g + 1)
            msg = "Higher!"
        else:
            D.ghi = min(D.ghi, g - 1)
            msg = "Lower!"
        if D.glo > D.ghi:
            D.glo, D.ghi = 1, 100
        D.ask = ("#", D.glo, D.ghi, (D.glo + D.ghi) // 2)
        return "%s %d-%d" % (msg, D.glo, D.ghi)
    if D.st == "rps":
        M = {"rock": 0, "r": 0, "paper": 1, "p": 1, "scissors": 2,
             "scissor": 2, "s": 2}
        u = None
        for w in words:
            if w in M:
                u = M[w]
                break
        D.ask = ("rock", "paper", "scissors", "quit")
        if u is None:
            return "Rock, paper or scissors? (quit to stop)"
        b = random.randint(0, 2)
        N = ("rock", "paper", "scissors")
        d = (u - b) % 3
        if d == 1:
            D.ss += 1
            res = "You win!"
        elif d == 2:
            D.sn += 1
            res = "I win!"
        else:
            res = "Tie!"
        return "I chose %s. %s (%d-%d)" % (N[b], res, D.ss, D.sn)
    if D.st == "mq":
        n = D.nums(low)
        if n and int(n[0]) == D.sd:
            D.ss += 1
            m = "Right!"
        else:
            m = "It's %d." % D.sd
        if D.sn >= 5:
            D.st = 0
            return offer("%s Score: %d/5. %s Again?" % (m, D.ss, "Math whiz!" if D.ss >= 4 else "Keep going!"), "mathquiz")
        D.sn += 1
        return m + " " + mqnext()
    if D.st == "pickn":
        n = D.nums(low)
        if not n:
            D.st = 0
            return reply(t)
        g = int(n[0])
        D.st = 0
        if g == D.sd:
            return "You picked %d and so did I! Mind reader!" % g
        return "You picked %d. I picked %d. %s" % (g, D.sd, D.pick(("So close!", "Nice pick!", "Good one!")))
    if D.st == "choose":
        D.st = 0
        hit = False
        for noun, items in S.CHOOSE:
            if noun == D.sd:
                for it in items:
                    if it in low and len(words) <= 3:
                        hit = True
        if not hit:
            return reply(t)
        if D.sd in ("game", "topic", "mood"):
            return reply(t)
        v = t.strip()[:20]
        D.mem[D.sd] = v
        return D.pick(("%s! Great choice.", "Ooh, %s. Nice!", "%s it is!")) % v
    if D.st == "yn":
        D.st = 0
        if "no" in ws or "nope" in ws or "nah" in ws:
            return "Okay, no problem!"
        for w in ("yes", "yeah", "yep", "yup", "sure", "ok", "okay", "yea", "please"):
            if w in ws:
                return reply(D.sd)
        return reply(t)
    if D.st == "kk1":
        D.st = "kk2"
        return t.strip()[:14] + " who?"
    D.st = 0
    return D.pick(D.lines_of("KKEND"))





START = {"quiz": g_quiz, "riddle": g_riddle, "guess": g_guess, "rps": g_rps,
         "mq": g_mq, "kk": g_kk}


# ------------------------------------------------------------ tools
ALIAS = {"kilometers": "km", "kilometer": "km", "kilometres": "km",
         "miles": "mi", "mile": "mi", "kilos": "kg", "kilo": "kg",
         "kilograms": "kg", "kilogram": "kg", "pounds": "lb", "pound": "lb",
         "lbs": "lb", "meters": "m", "meter": "m", "metres": "m",
         "feet": "ft", "foot": "ft", "inches": "inch", "liters": "l",
         "liter": "l", "litres": "l", "gallons": "gal", "gallon": "gal",
         "celsius": "c", "fahrenheit": "f", "centimeters": "cm"}
UNITS = {"km": ("mi", 0.621371), "mi": ("km", 1.60934),
         "kg": ("lb", 2.20462), "lb": ("kg", 0.453592),
         "m": ("ft", 3.28084), "ft": ("m", 0.3048),
         "cm": ("inch", 0.393701), "inch": ("cm", 2.54),
         "l": ("gal", 0.264172), "gal": ("l", 3.78541),
         "c": ("F", 0), "f": ("C", 0)}


def roman(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
                 (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
                 (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


def tools(t, low, words, ws, qt):
    n = D.nums(low)
    if ("percent" in ws or "%" in low) and "of" in ws and len(n) >= 2:
        return "= " + D.fmt(n[0] * n[1] / 100)
    if ("sqrt" in ws or "root" in ws) and n:
        return "= " + D.fmt(math.sqrt(n[0]))
    if ("squared" in ws or "square" in ws) and n and "root" not in ws:
        return "= " + D.fmt(n[0] * n[0])
    if "factorial" in ws and n and 0 <= n[0] <= 20:
        f = 1
        for i in range(2, int(n[0]) + 1):
            f *= i
        return "%d! = %d" % (int(n[0]), f)
    if "prime" in ws and n and n[0] >= 2:
        v = int(n[0])
        i = 2
        while i * i <= v:
            if v % i == 0:
                return "%d is not prime (%d x %d)." % (v, i, v // i)
            i += 1
        return "%d is prime!" % v
    if ("fib" in ws or "fibonacci" in ws) and n and 1 <= n[0] <= 20:
        a, b = 0, 1
        out = []
        for i in range(int(n[0])):
            out.append(str(a))
            a, b = b, a + b
        return " ".join(out)
    if "binary" in ws and n and n[0] < 1e9:
        return "%d = %s in binary" % (int(n[0]), bin(int(n[0]))[2:])
    if ("hex" in ws or "hexadecimal" in ws) and n and n[0] < 1e9:
        return "%d = 0x%s" % (int(n[0]), hex(int(n[0]))[2:].upper())
    if "roman" in ws and n and 1 <= n[0] < 4000:
        return "%d = %s" % (int(n[0]), roman(int(n[0])))
    if "count" in ws and "to" in ws and n and 1 <= n[0] <= 30:
        return " ".join([str(i) for i in range(1, int(n[0]) + 1)])
    if n and ("to" in ws or "in" in ws or "convert" in ws):
        src = None
        for w in words:
            u = ALIAS.get(w, w)
            if u in UNITS:
                src = u
                break
        if src:
            if src == "c":
                r, unit = n[0] * 9 / 5 + 32, "F"
            elif src == "f":
                r, unit = (n[0] - 32) * 5 / 9, "C"
            else:
                unit, k = UNITS[src]
                r = n[0] * k
            return "%s %s = %s %s" % (D.fmt(n[0]), src, D.fmt(r), unit)
    # arithmetic
    e = low
    for a, b in ((" plus ", "+"), (" minus ", "-"), (" times ", "*"),
                 (" multiplied by ", "*"), (" divided by ", "/"),
                 (" over ", "/"), (" x ", "*")):
        e = e.replace(a, b)
    m = "".join([c for c in e if c in "0123456789+-*/.()"])
    if len(m) >= 3 and "**" not in m and "//" not in m:
        for o in "+-*/":
            if o in m[1:]:
                try:
                    return "= " + D.fmt(eval(m))
                except ZeroDivisionError:
                    return "Can't divide by zero!"
                except Exception:
                    break
                break
    return None


def fun(t, low, words, ws, qt):
    n = D.nums(low)
    if "morse" in ws:
        rest = low.split("morse", 1)[1]
        codes = D.lines_of("MORSE")[0].split(" ")
        out = []
        for c in rest:
            if "a" <= c <= "z":
                out.append(codes[ord(c) - 97])
            elif "0" <= c <= "9":
                out.append(codes[26 + ord(c) - 48])
            elif c == " " and out and out[-1] != "/":
                out.append("/")
        if out:
            return " ".join(out[:30])
        return "Try: morse sos"
    parts = t.strip().split(None, 1)
    if len(parts) > 1 and words[0] in ("reverse", "spell", "shout", "say", "repeat", "echo"):
        rest = parts[1][:30]
        k = words[0]
        if k == "reverse":
            return "".join(reversed(list(rest)))
        if k == "spell":
            return "-".join([c.upper() for c in rest if c != " "])
        if k == "shout":
            return rest.upper() + "!"
        return rest
    if "flip" in ws or "toss" in ws or ("coin" in ws and not qt):
        return D.pick(("Heads!", "Tails!"))
    for w in words:
        if len(w) > 1 and w[0] == "d" and w[1:].isdigit():
            s = int(w[1:])
            if 2 <= s <= 1000:
                return "d%d: %d" % (s, random.randint(1, s))
    if "dice" in ws or "roll" in ws:
        c = int(n[0]) if n and 1 <= n[0] <= 8 else 1
        rolls = [random.randint(1, 6) for i in range(c)]
        s = " ".join([str(x) for x in rolls])
        return "Rolled: " + s + ("  Total " + str(sum(rolls)) if c > 1 else "")
    if "random" in ws:
        if len(n) >= 2:
            a, b = int(n[0]), int(n[1])
            if a > b:
                a, b = b, a
            return "Random: %d" % random.randint(a, b)
        return "Random: %d" % random.randint(1, 100)
    cl = " ".join(words)
    if " or " in cl and len(words) <= 12:
        p = cl.split(" or ")
        if len(p) == 2:
            a = p[0].split()[-1] if p[0].split() else ""
            rb = [w for w in p[1].split() if w not in ("a", "an", "the")]
            if a and rb:
                return "I pick %s!" % D.pick((a, rb[0]))
    return None


# ------------------------------------------------------------ brain
try:
    random.seed(time.ticks_us())
    _ms = time.ticks_ms
except AttributeError:
    _ms = lambda: int(time.time() * 1000)
T0 = _ms()

name = ""

QT = {"why": "w", "what": "t", "whats": "t", "which": "t", "how": "h",
      "hows": "h", "who": "o", "whos": "o", "whom": "o", "whose": "o",
      "where": "r", "wheres": "r", "when": "r", "whens": "r"}

FUNW = ("morse", "reverse", "spell", "shout", "say", "repeat", "echo",
        "flip", "toss", "coin", "dice", "roll", "random")


def act(k):
    """Run an @action from the rules table."""
    if k in ("quiz", "riddle", "guess", "rps", "mq", "kk"):
        return START[k]()
    if k == "ball":
        return D.pick(D.lines_of("BALL"))
    if k == "menu":
        return D.lines_of("MENU")[0]
    if k == "clear":
        D.clr = True
        return "Chat cleared!"
    if k == "ram":
        try:
            import gc
            gc.collect()
            return "Free RAM: %d KB" % (gc.mem_free() // 1024)
        except Exception:
            return "Plenty of RAM for tiny me!"
    if k == "up":
        s = (_ms() - T0) // 1000
        return "I've been awake %dm %ds." % (s // 60, s % 60)
    return D.pick(D.lines_of(k))


def resolve(a):
    if a[0] == "@":
        return act(a[1:])
    a = a.replace("{n}", name or "friend")
    if "~yn:" in a:
        a, x = a.split("~yn:")
        return offer(a, x)
    return a


def reply(t):
    try:
        return _reply(t)
    except MemoryError:
        D.st = 0
        D.ask = None
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        return "Out of memory! Try something simpler."


def _reply(t):
    global name
    D.ask = None
    low = t.lower().replace("favourite", "favorite")
    clean = ""
    for ch in low:
        if ch == "'":
            continue
        clean += ch if (ch.isalpha() or ch.isdigit()) else " "
    words = clean.split()
    if not words:
        return "Say something!"
    ws = set(words)
    for w in words:
        if len(w) > 3 and w[-1] == "s":
            ws.add(w[:-1])
        if len(w) > 4 and w.endswith("ed"):
            ws.add(w[:-2])
            ws.add(w[:-1])
        if len(w) > 5 and w.endswith("ing"):
            ws.add(w[:-3])
            ws.add(w[:-3] + "e")

    if D.st:
        if "quit" in ws or "stop" in ws or "exit" in ws or "menu" in ws:
            D.st = 0
            return "Okay, back to chat!"
        return play(t, low, words, ws)

    qt = ""
    for w in words:
        if w in QT:
            qt = QT[w]
            break

    # ---- things I remember about you
    if "name" in ws and "my" in ws:
        if words[-1] in ("name", "my", "is", "now", "again"):
            return ("You're %s!" % name) if name else "You haven't told me yet."
        name = words[-1].capitalize()
        return "Nice to meet you, %s!" % name
    if "call" in ws and "me" in ws and words[-1] not in ("me", "call"):
        name = words[-1].capitalize()
        return "Okay, %s it is!" % name
    if "who" in ws and "am" in ws and "i" in ws:
        return ("You're %s!" % name) if name else "You're my favorite human!"
    if "favorite" in ws and "my" in ws:
        i = words.index("favorite")
        if len(words) > i + 1:
            k = words[i + 1]
            if "is" in words[i + 2:] and not qt:
                v = " ".join(words[words.index("is", i + 2) + 1:])
                if v:
                    D.mem[k] = v
                    return "Cool! Your favorite %s is %s." % (k, v)
            elif k in D.mem:
                return "Your favorite %s is %s!" % (k, D.mem[k])
            else:
                return "You haven't told me your favorite %s." % k
    if words[0] == "i" and len(words) > 2 and words[1] in ("like", "love", "enjoy"):
        v = " ".join(words[2:])
        if not v.startswith("you"):
            if v not in D.likes:
                D.likes.append(v)
                if len(D.likes) > 5:
                    del D.likes[0]
            return D.pick(("Nice! I'll remember you like %s.", "Cool! %s sounds fun.", "Great taste in %s!")) % v
    if qt == "t" and "do" in ws and "i" in ws and ("like" in ws or "love" in ws):
        return ("You like " + ", ".join(D.likes) + ".") if D.likes else "You haven't told me yet."

    # ---- "choose a number / color / animal ..." (shows a picker)
    if "choose" in ws or "pick" in ws or "select" in ws:
        n = D.nums(low)
        if "number" in ws:
            lo, hi = 1, 10
            if len(n) >= 2:
                lo, hi = int(n[0]), int(n[1])
            elif n:
                hi = int(n[0])
            elif "big" in ws or "large" in ws or "huge" in ws:
                hi = 100
            if lo > hi:
                lo, hi = hi, lo
            hi = min(hi, 999)
            lo = min(lo, hi - 1)
            D.st = "pickn"
            D.sd = random.randint(lo, hi)
            D.sn = lo
            D.ss = hi
            D.ask = ("#", lo, hi, lo)
            return "Pick a number from %d to %d!" % (lo, hi)
        for noun, items in S.CHOOSE:
            if noun in ws:
                D.st = "choose"
                D.sd = noun
                D.ask = items
                return "Choose a %s!" % noun
        if words[0] in ("choose", "pick", "select") and len(words) <= 2:
            return "Choose what? Try: choose a number, color, animal, food, game or topic."

    # ---- tools (math, converters, dice ...)
    r = None
    for ch in low:
        if ch.isdigit():
            r = tools(t, low, words, ws, qt)
            break
    if not r:
        hit = " or " in low
        for w in words:
            if w in FUNW or (w[0] == "d" and w[1:].isdigit()):
                hit = True
        if hit:
            r = fun(t, low, words, ws, qt)
    if r:
        return r

    if (words[0] in ("should", "will", "shall") and len(words) > 2 and
            t.strip().endswith("?")):
        return D.pick(D.lines_of("BALL"))

    # ---- rules vs knowledge base
    best = 0
    rule = None
    for e in D.scan("RULES"):
        p = e.split("|")
        s = D.score(p[0], ws) * 2
        if s > best:
            best = s
            rule = p
    kbs = 0
    kbp = None
    for e in D.scan("KB"):
        p = e.split("|", 2)
        m = D.score(p[1], ws)
        if not m:
            continue
        fit = p[0] == qt or p[0] == "x"
        if qt and not fit and m < 2:
            continue
        s = m * 2 + (1 if (fit or (not qt and p[0] == "t")) else 0)
        if s > kbs:
            kbs = s
            kbp = p
    if kbs > best:
        return kbp[2]
    if best > 0:
        return resolve(D.pick(rule[1:]))

    if t.strip().endswith("?") and words[0] in (
            "should", "will", "can", "could", "would", "do", "does", "is",
            "am", "are", "did", "shall", "may", "have", "has"):
        return D.pick(D.lines_of("BALL"))
    out = D.pick(D.lines_of("FB_" + (qt or "x")))
    if name and random.randint(0, 2) == 0:
        out = name + ", " + out[0].lower() + out[1:]
    return out
