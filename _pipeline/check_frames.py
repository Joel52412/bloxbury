# check_frames.py - after a GPU render: missing, empty, black or blank frames (outside intended black ranges).
# Usage: python check_frames.py <frames_dir> <nf> [black_from-black_to ...]   e.g. 1498-1561
import os, sys
from PIL import Image, ImageStat
d, nf = sys.argv[1], int(sys.argv[2])
ok_black = []
for r in sys.argv[3:]:
    a, b = r.split("-"); ok_black.append((int(a), int(b)))
bad = []
for f in range(1, nf + 1):
    p = os.path.join(d, "%04d.png" % f)
    if not os.path.exists(p) or os.path.getsize(p) < 1000:
        bad.append((f, "missing/empty")); continue
    try:
        im = Image.open(p).convert("L"); im.thumbnail((108, 192)); st = ImageStat.Stat(im)
    except Exception as e:
        bad.append((f, "unreadable")); continue
    mean, sd = st.mean[0], st.stddev[0]
    intended = any(a <= f <= b for a, b in ok_black)
    if mean < 4 and not intended: bad.append((f, "black %.1f" % mean))
    elif sd < 1.5 and not intended: bad.append((f, "blank sd %.2f" % sd))
print("FRAME CHECK", "OK" if not bad else bad[:40], "checked", nf)
