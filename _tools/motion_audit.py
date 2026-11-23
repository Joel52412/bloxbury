# motion_audit.py - frame-by-frame smoothness check of a finished export (23 Nov, Part 3 judder).
# Usage: python3 motion_audit.py <video.mp4> [shots.json]     (shots.json = {"shots": [[name, f0, f1], ...]} from partN.py)
# Diffs EVERY consecutive frame (caption band masked) and reports:
#   POP     a single-frame jump (> 2.5x the local motion, not on a cut)
#   JUDDER  a 3-frame stutter pattern (lag-3 autocorrelation > 0.55 over 14 frames): keys on mixed frame grids
#   FREEZE  8+ identical frames (a dead hold reads as a paused video)
import sys, json, subprocess
import numpy as np

W, H = 216, 384
video = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
mask = np.ones((H, W), bool); mask[int(H * 0.61):int(H * 0.72), :] = False          # captions sit at y=66%
d = np.array([np.abs(a[i + 1] - a[i])[mask].mean() for i in range(len(a) - 1)])
if len(sys.argv) > 2:
    cuts = [s[1] - 1 for s in json.load(open(sys.argv[2]))["shots"]]
else:
    cuts = [i + 1 for i in range(len(d)) if d[i] > 12]
iscut = lambda i: any(abs(i + 1 - c) <= 1 for c in cuts)
ts = lambda f: "%d:%05.2f" % (f // 24 // 60, (f / 24) % 60)
pad = np.pad(d, 4, mode="edge"); med = np.array([np.median(pad[i:i + 9]) for i in range(len(d))])
pops = [i for i in range(len(d)) if not iscut(i) and d[i] > 2.5 * med[i] + 0.8]
x = d - np.convolve(d, np.ones(7) / 7, "same"); runs = []
for s in range(len(d) - 14):
    w = x[s:s + 14]
    if any(iscut(k) for k in range(s, s + 14)) or d[s:s + 14].mean() < 0.25: continue
    if np.corrcoef(w[:-3], w[3:])[0, 1] > 0.55 and np.corrcoef(w[:-1], w[1:])[0, 1] < 0:
        if runs and s <= runs[-1][1] + 3: runs[-1][1] = s + 14
        else: runs.append([s, s + 14])
frz = []; s = None
for i in range(len(d)):
    if d[i] < 0.06 and a[i].mean() > 8: s = i if s is None else s
    else:
        if s is not None and i - s >= 8: frz.append((s, i))
        s = None
for i in pops: print("POP    %s  frame %d" % (ts(i + 1), i + 2))
for s, e in runs: print("JUDDER %s-%s  frames %d-%d" % (ts(s), ts(e), s + 1, e + 1))
for s, e in frz: print("FREEZE %s-%s  %d frames" % (ts(s), ts(e), e - s))
print("MOTION AUDIT", "OK" if not (pops or runs or frz) else "%d pops, %d judder runs, %d freezes" % (len(pops), len(runs), len(frz)))
