#!/usr/bin/env python3
# pod_progress.py - runs ON THE POD next to a render. Every 2 s it writes /workspace/render_progress.json (a few hundred
# bytes) so the Render Monitor on Joel's laptop reads one tiny file instead of listing the whole frames folder.
# Per-GPU numbers come from each GPU's Blender logs (render_gpuN*.log "Saved:" lines), so they stay right when GPUs
# share one frame queue (pod_render.sh / pod_balance.sh). ETA = frames left / total speed over the last ~90 s.
# Usage: nohup python3 pod_progress.py /workspace/frames 1921 > /workspace/progress.log 2>&1 &
import glob, json, os, re, sys, time
from collections import deque
d, total = sys.argv[1], int(sys.argv[2])
OUT = os.environ.get("PROGRESS_OUT", "/workspace/render_progress.json")
hist = deque(maxlen=600); ghist = {}; started = time.time()


def rate(h, now, win=90):
    old = next(((t, n) for t, n in h if now - t <= win), h[0])
    return (h[-1][1] - old[1]) / (now - old[0]) if now > old[0] and h[-1][1] > old[1] else None


while True:
    done, newest = 0, 0.0
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.endswith(".png"):
                    st = e.stat()
                    if st.st_size > 0:                       # 0-byte = Blender placeholder for a frame in progress
                        done += 1; newest = max(newest, st.st_mtime)
    except FileNotFoundError:
        pass
    now = time.time(); hist.append((now, done))
    per_gpu = []
    for g in sorted({int(m.group(1)) for f in glob.glob("/workspace/render_gpu*.log") for m in [re.search(r"render_gpu(\d+)", f)] if m}):
        n = 0
        for f in glob.glob("/workspace/render_gpu%d*.log" % g):
            try: n += len(re.findall(r"Saved: '[^']*/\d{4}\.png'", open(f, errors="ignore").read()))   # frames only
            except OSError: pass
        h = ghist.setdefault(g, deque(maxlen=600)); h.append((now, n))
        per_gpu.append({"gpu": g, "done": n, "fps": rate(h, now)})
    fps = rate(hist, now)
    left = max(total - done, 0)
    info = {"done": done, "total": total, "updated": now, "newest_frame_time": newest or None, "started_watch": started,
            "fps_60s": fps, "eta_s": (0 if left == 0 else (left / fps if fps else None)), "per_gpu": per_gpu,
            "shared_queue": True, "finished": done >= total}
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f: json.dump(info, f)
    os.replace(tmp, OUT)                                     # atomic: the monitor never reads half a file
    if done >= total:
        break
    time.sleep(2)
