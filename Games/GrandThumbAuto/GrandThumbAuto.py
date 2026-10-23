# GrandThumbAuto - main.py  (needs gta_engine.py, gta_logic.py, gta_play.py in the same folder)
import sys
import gc
import thumby

d = thumby.display
d.setFPS(30)
try:
    d.setFont("/lib/font3x5.bin", 3, 5, 1)
    FW, FH = 4, 5
except Exception:
    FW, FH = 6, 7
FAST = hasattr(d, 'display') and hasattr(d.display, 'buffer')


FILES = ('gta_engine.py', 'gta_logic.py', 'gta_play.py')
LAST = ''


def load(sec, g):
    """run a section of the gta_*.py files in small pieces (compiling needs ~8x the source size in RAM)"""
    global LAST
    pre = 'from micropython import const\n'     # const names must be defined ONCE per compile unit
    for fn in (FILES if sec == 'game' else FILES[:1] if sec == 'art' else FILES[2:]):
        f = None
        for p in sys.path + ['/Games/GrandThumbAuto', '/']:
            try:
                f = open((p + '/' if p else '') + fn)
                break
            except OSError:
                pass
        if f is None:
            raise OSError('NO ' + fn)
        buf = []
        new = ''
        on = False
        for line in f:
            if line[:3] == '#@@':
                if on:
                    break
                on = line[3:].strip() == sec
            elif on:
                if line[:2] == '#@':
                    if buf:
                        LAST = fn[4:7] + ':' + buf[0][:18]
                        exec(pre + ''.join(buf), g)
                        pre += new
                        new = ''
                        buf = []
                        gc.collect()
                else:
                    buf.append(line)
                    if line[0] != ' ' and ' = const(' in line:
                        new += line
        if buf:
            LAST = fn[4:7] + ':' + buf[0][:18]
            exec(pre + ''.join(buf), g)
            pre += new
        f.close()
    gc.collect()


d.fill(0)
d.drawText("LOADING", (72 - 7 * FW) // 2, 16, 1)
d.update()
try:
    load('game', globals())
except Exception as e:                      # show the real error on screen
    try:
        sys.print_exception(e)
    except Exception:
        pass
    gc.collect()
    m = type(e).__name__ + " " + str(e) + " @" + LAST + " FREE" + str(gc.mem_free())
    n = 72 // FW
    while True:
        d.fill(0)
        for i in range(5):
            d.drawText(m[i * n:(i + 1) * n], 0, i * (FH + 2), 1)
        d.update()
main()
