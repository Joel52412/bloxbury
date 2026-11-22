#!/usr/bin/env python3
# pod_progress.py - runs ON THE POD next to a render. Every 2 s it writes /workspace/render_progress.json (a few hundred
# bytes) so the Render Monitor on Joel's laptop reads one tiny file instead of listing the whole frames folder.
# Usage: nohup python3 pod_progress.py /workspace/frames 1921 "1-641,642-1282,1283-1921" > /dev/null 2>&1 &
import json, os, sys, time
from collections import deque
d, total = sys.argv[1], int(sys.argv[2])
ranges = [tuple(map(int, r.split("-"))) for r in (sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else [f"1-{total}"])]
OUT = os.environ.get("PROGRESS_OUT", "/workspace/render_progress.json")
hist = deque(maxlen=400)              # (time, frames done) ~ 13 min at 2 s
ghist = {}                            # per-GPU history: GPUs run side by side, so the SLOWEST one decides the finish
started = time.time()
while True:
    nums, newest = [], 0.0
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.endswith(".png"):
                    st = e.stat()
                    if st.st_size > 0:                       # 0-byte = Blender placeholder for a frame in progress
                        try: nums.append(int(e.name[:-4]))
                        except ValueError: pass
                        newest = max(newest, st.st_mtime)
    except FileNotFoundError:
        pass
    now = time.time(); done = len(nums); hist.append((now, done))
    def rate(win):                                           # frames per second over the last `win` seconds
        old = next(((t, n) for t, n in hist if now - t <= win), hist[0])
        return (done - old[1]) / (now - old[0]) if now > old[0] and done > old[1] else None
    per_gpu, etas = [], []
    for i, (a, b) in enumerate(ranges):
        gd = sum(1 for n in nums if a <= n <= b); h = ghist.setdefault(i, deque(maxlen=400)); h.append((now, gd))
        old = next(((t, n) for t, n in h if now - t <= 90), h[0])
        fps = (gd - old[1]) / (now - old[0]) if now > old[0] and gd > old[1] else None
        left = (b - a + 1) - gd
        eta = 0 if left <= 0 else (left / fps if fps else None)
        etas.append(eta)
        per_gpu.append({"gpu": i, "fs": a, "fe": b, "total": b - a + 1, "done": gd, "fps": fps, "eta_s": eta})
    eta_s = max(etas) if etas and all(e is not None for e in etas) else None
    info = {"done": done, "total": total, "updated": now, "newest_frame_time": newest or None, "started_watch": started,
            "fps_60s": rate(60), "fps_180s": rate(180), "eta_s": eta_s, "per_gpu": per_gpu, "finished": done >= total}
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f: json.dump(info, f)
    os.replace(tmp, OUT)                                     # atomic: the monitor never reads half a file
    if done >= total:
        break
    time.sleep(2)
