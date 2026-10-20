import os
import time
import thumby

lines = []


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def size(path):
    try:
        return os.stat(path)[6]
    except OSError:
        return -1


# free flash space
try:
    st = os.statvfs("/")
    free_kb = st[0] * st[3] // 1024
    lines.append("FREE %dKB" % free_kb)
except Exception:
    lines.append("FREE ?")

# is the game where the launcher expects it?
path = "/Games/Sandbox/Sandbox.py"
if exists(path):
    lines.append("GAME OK %dKB" % (size(path) // 1024))
else:
    lines.append("NO GAME FILE")

# what is in /Games?
try:
    games = os.listdir("/Games")
    lines.append("GAMES %d" % len(games))
    for g in games[:6]:
        lines.append(g[:12])
except OSError:
    lines.append("NO /Games")

# what is inside /Games/Sandbox?
try:
    inner = os.listdir("/Games/Sandbox")
    lines.append("IN SANDBOX:")
    for f in inner[:4]:
        lines.append(f[:12])
except OSError:
    lines.append("NO SANDBOX DIR")

for ln in lines:
    print(ln)

top = 0
thumby.display.setFPS(30)
while True:
    thumby.display.fill(0)
    for i in range(5):
        k = top + i
        if k < len(lines):
            thumby.display.drawText(lines[k], 0, i * 8, 1)
    thumby.display.update()
    if thumby.buttonD.pressed() and top < len(lines) - 5:
        top += 1
        time.sleep_ms(120)
    if thumby.buttonU.pressed() and top > 0:
        top -= 1
        time.sleep_ms(120)
