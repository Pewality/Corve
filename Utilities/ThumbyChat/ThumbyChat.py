# ThumbyChat - tiny chatbot for the Thumby (MicroPython)
# This small file just starts the app. If anything goes wrong it shows the
# error on the Thumby screen (D-pad UP/DOWN scrolls) instead of restarting.
#
# Put ALL of these in /Games/ThumbyChat/ on the Thumby:
#   ThumbyChat.py  chatapp.py  chatbrain.py  starters.py  chat.dat  ThumbyChat.bin
# (chatdata.py + chatdata2.py are only for the web emulator - not needed on the Thumby)
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


thumby.display.fill(0)
thumby.display.drawText("Loading...", 9, 16, 1)
thumby.display.update()

gc.collect()
try:
    import chatapp          # runs the whole app (never returns)
except Exception as e:
    show_error(e)
