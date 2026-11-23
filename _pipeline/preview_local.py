# preview_local.py - FREE motion preview (replaces the paid pod preview, 23 Nov): the whole part at 216x384,
# CPU Cycles SAMPLES=4, in batches under 15 min, then joined with the mix + captions and checked by motion_audit.
# Usage:  python3 preview_local.py partN.py            render ONE batch (~12 min) of the frames still missing, then exit
#         python3 preview_local.py partN.py --all      keep going batch after batch (each its own process), then join
#         python3 preview_local.py partN.py --join     only join + audit what is there
# Env: RX RY SAMPLES (216/384/4), BUDGET seconds per batch (720), OUT frames dir (/home/claude/talk/preview_pN).
# Resumable: a killed batch only loses the frame it was on. Measured 23 Nov here: ~1.1 s/frame (Part 3 = ~37 min, 3 batches).
import json, os, re, subprocess, sys, time
SCRIPT = sys.argv[1]; N = re.search(r"(\d+)", os.path.basename(SCRIPT)).group(1)
TALK = os.environ.get("OUT_DIR", "/home/claude/talk/"); HERE = os.path.dirname(os.path.abspath(__file__))
SCR_DIR = os.environ.get("SCR", "/home/claude/bloxbury-blender/")
OUT = os.environ.get("OUT", f"{TALK}preview_p{N}"); os.makedirs(OUT, exist_ok=True)
RX, RY, SAMPLES = os.environ.get("RX", "216"), os.environ.get("RY", "384"), os.environ.get("SAMPLES", "4")
BUDGET = float(os.environ.get("BUDGET", 720))
env = json.load(open(f"{TALK}env_p{N}.json")); NF = int(env.get("nf") or round(env["total"] * 24))
STATE = f"{OUT}/state.json"
st = json.load(open(STATE)) if os.path.exists(STATE) else {"spf": 1.5, "setup": 25, "batches": []}


def missing():
    out = []
    for f in range(1, NF + 1):
        p = f"{OUT}/{f:04d}.png"
        if not os.path.exists(p) or os.path.getsize(p) == 0:       # 0 bytes = placeholder of a killed frame
            if os.path.exists(p): os.remove(p)
            out.append(f)
    return out


def batch():
    m = missing()
    if not m: return False
    fs = m[0]; n = max(12, int((BUDGET - st["setup"]) / st["spf"]))
    fe = min(NF, fs + n - 1)
    t0 = time.time()
    envv = dict(os.environ, RENDER="1", OUT=OUT, RX=RX, RY=RY, SAMPLES=SAMPLES, FS=str(fs), FE=str(fe))
    envv.pop("FRAMES", None)
    try:
        r = subprocess.run([sys.executable, SCR_DIR + os.path.basename(SCRIPT)], env=envv, cwd=SCR_DIR,
                           capture_output=True, text=True, timeout=BUDGET + 150)
        log = r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        log = (e.stdout or b"").decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        print("batch hit the time limit; frames so far are kept")
    dt = time.time() - t0
    done = [f for f in range(fs, fe + 1) if os.path.exists(f"{OUT}/{f:04d}.png") and os.path.getsize(f"{OUT}/{f:04d}.png") > 0]
    if not done:
        print(log[-3000:]); raise SystemExit("no frames rendered - see log above")
    # setup = wall time before the first frame landed; spf from the rest
    first = min(os.path.getmtime(f"{OUT}/{f:04d}.png") for f in done)
    setup = max(5, first - t0 - 1); spf = max(0.2, (dt - setup) / max(1, len(done)))
    st.update(spf=round(0.5 * st["spf"] + 0.5 * spf, 3) if st["batches"] else round(spf, 3), setup=round(setup, 1))
    st["batches"].append([fs, fe, len(done), round(dt)]); json.dump(st, open(STATE, "w"))
    left = len(missing())
    print(f"BATCH {fs}-{fe}: {len(done)} frames in {dt / 60:.1f} min ({spf:.2f} s/frame). "
          f"{left} frames left, ~{left * st['spf'] / 60:.0f} min, {-(-left // max(1, int((BUDGET - st['setup']) / st['spf'])))} batches")
    return left > 0


def join():
    if missing(): raise SystemExit(f"{len(missing())} frames still missing - run more batches first")
    mp4 = f"{TALK}Part{N}_preview.mp4"
    subprocess.run(["sh", f"{HERE}/make_part.sh", OUT, mp4, f"{TALK}part{N}_audio.wav", f"{TALK}captions_p{N}.ass"], check=True)
    shots = f"{TALK}shots_p{N}.json"
    a = [sys.executable, os.path.abspath(f"{HERE}/../_tools/motion_audit.py"), mp4] + ([shots] if os.path.exists(shots) else [])
    print(subprocess.run(a, capture_output=True, text=True).stdout)
    print("PREVIEW", mp4)


if "--join" in sys.argv: join()
elif "--all" in sys.argv:
    while batch(): pass
    join()
elif not batch(): join()
