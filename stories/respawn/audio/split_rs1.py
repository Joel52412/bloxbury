# rs1: split each voice into lines + scan words for gaps >40 ms and clicks. Run from stories/respawn.
import json, os, sys, numpy as np
sys.path.insert(0, os.path.abspath("../../_pipeline/audio_tools"))
os.environ["AUD"] = "part1/voice/"
import split_lines as S
D = "data/rs1/"
for w in ("theo", "wren", "bramble", "ashby", "hand"):
    L = [l for l in open(D + f"script_{w}.txt").read().splitlines() if l.strip()]
    out = S.split(f"{w}_rs1.mp3", json.load(open(D + f"words_{w}.json")), L)
    json.dump(out, open(D + f"lines_{w}.json", "w"))
    e = S.env(f"{w}_rs1.mp3"); d = np.diff(e)
    for o in out:
        for wd, a, b in o["words"]:
            seg = e[int(a * 100):int(b * 100)]
            run = gap = 0
            for v in seg: run = run + 1 if v < -50 else 0; gap = max(gap, run)
            if gap * 10 > 40 and len(seg) > 8: print(f"GAP  {w} {wd} {a:.2f} {gap*10} ms")
        f0, f1 = int(o["a"] * 100), int(o["b"] * 100)
        for k in np.where(d[f0:f1] > 30)[0]: print(f"CLICK? {w} {(f0+k)/100:.2f} +{d[f0+k]:.0f} dB  '{o['text'][:30]}'")
    print(w, len(out), "lines", f"{out[0]['a']:.2f}-{out[-1]['b']:.2f}s")
