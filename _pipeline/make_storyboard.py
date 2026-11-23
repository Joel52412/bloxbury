# make_storyboard.py N [out.mp4] - STORYBOARD ANIMATIC (replaces the dark-frame animatic, 23 Nov): the real shot
# stills on the real mix. Each shot shows its first frame and cross-fades to its last, so the planned camera move and
# the pose change read; shot name, timecode, "music out" markers and the word-timed captions sit on top.
# Needs shots_pN.json (written by every build of partN.py). Stills come from STILLS (default /home/claude/talk/
# preview_pN if frames are there); missing ones are rendered here at 216x384 SAMPLES=4 (~15 s + ~1 s per still).
# Before partN.py exists, use make_animatic.py (dark frame) for the first pacing pass. Send in chat; don't store it.
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
N = sys.argv[1]; T = os.environ.get("OUT_DIR", "/home/claude/talk/"); R = os.path.abspath(os.path.dirname(__file__) + "/..")
SCR = os.environ.get("SCR", "/home/claude/bloxbury-blender/")
out = sys.argv[2] if len(sys.argv) > 2 else f"/home/claude/Part{N}_storyboard.mp4"
W, H = 540, 960                                               # libass scales the 1080x1920 captions to this
e = json.load(open(f"{T}env_p{N}.json")); shots = json.load(open(f"{T}shots_p{N}.json"))["shots"]
AUDIO = next((f"{T}part{N}_audio.{x}" for x in ("wav", "flac") if os.path.exists(f"{T}part{N}_audio.{x}")), f"{T}part{N}_audio.flac")
NF = int(e.get("nf") or round(e["total"] * 24))
ST = os.environ.get("STILLS", f"{T}preview_p{N}")
os.makedirs(ST, exist_ok=True)
ends = [(max(f0, min(f1, f0 + 1)), max(f0, f1 - 1)) for _, f0, f1 in shots]      # skip the cut frame itself
need = sorted({f for ab in ends for f in ab if not os.path.exists(f"{ST}/{f:04d}.png") or not os.path.getsize(f"{ST}/{f:04d}.png")})
if need:
    print("rendering", len(need), "stills")
    subprocess.run([sys.executable, SCR + f"part{N}.py"], cwd=SCR, check=True, stdout=subprocess.DEVNULL,
                   env=dict(os.environ, RENDER="1", OUT=ST, RX="216", RY="384", SAMPLES=os.environ.get("SAMPLES", "4"),
                            FRAMES=",".join(map(str, need))))
font = ImageFont.truetype(R + "/assets/fonts/Poppins-Bold.ttf", 22)
img = {}
def still(f):
    if f not in img: img[f] = Image.open(f"{ST}/{f:04d}.png").convert("RGB").resize((W, H), Image.LANCZOS)
    return img[f]
dt = [f"drawtext=fontfile={R}/assets/fonts/Poppins-Bold.ttf:text='%{{pts\\:hms}}':x=(w-tw)/2:y=18:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.5"]
dt += [f"drawtext=fontfile={R}/assets/fonts/Poppins-Bold.ttf:text='music out':x=(w-tw)/2:y=96:fontsize=18:fontcolor=0xFF6666:enable='between(t,{a},{b})'" for a, b in e.get("mutes", [])]
vf = ",".join(dt) + f",ass={T}captions_p{N}.ass:fontsdir={R}/assets/fonts,format=yuv420p"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                       "-i", AUDIO, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                       "-c:a", "aac", "-b:a", "160k", "-shortest", out], stdin=subprocess.PIPE)
cur = 0
for (name, f0, f1), (a, b) in zip(shots, ends):
    A, B = still(a), still(b); n = max(1, f1 - f0 + 1)
    lab = Image.new("RGBA", (W, 40), (0, 0, 0, 120)); d = ImageDraw.Draw(lab)
    d.text((W // 2, 20), name[:44], font=font, fill=(235, 235, 235, 255), anchor="mm")
    for i in range(n):
        x = i / max(1, n - 1); k = x * x * (3 - 2 * x)          # eased cross-fade first -> last frame
        fr = Image.blend(A, B, k) if a != b else A.copy()
        fr.paste(lab, (0, 54), lab); ff.stdin.write(fr.tobytes()); cur += 1
while cur < NF: ff.stdin.write(fr.tobytes()); cur += 1        # hold the last shot to the end of the mix
ff.stdin.close(); ff.wait()
print("WROTE", out)
