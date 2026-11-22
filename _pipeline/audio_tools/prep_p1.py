# prep_p1.py - Part 1 (redesign) cue sheet, audio mix, lip-sync envelope and word-timed captions. 24 fps.
# Source line timings come from pocketsphinx alignment of the CURRENT milo.mp3 (see cues_milo.txt / words_p1.json).
# The old cues.py used timings from an older milo.mp3 (spoken "KNOCK. KNOCK. KNOCK.", separate closet.mp3) - retired.
# Usage: python3 prep_p1.py [repo_root]   -> writes /home/claude/talk/{env_p1.json, part1_audio.wav, captions_p1.ass}
import numpy as np, subprocess, json, os, sys

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AUD = REPO + "/series/bloxbury/audio script/"
SFXD = REPO + "/sound effects/"
OUT = "/home/claude/talk/"
os.makedirs(OUT, exist_ok=True)
FPS, SR = 24, 48000
WORDS = json.load(open(REPO + "/_pipeline/data/words_p1.json"))

# ---- voice cues: (file, src_start, src_end, dest_start, caption, style, effect)   style "w" white / "r" red
VOICE = [
    ("milo", 0.10, 2.40, 0.30, "Never open the door after 3 A.M.", "r", None),
    ("milo", 2.94, 4.66, 2.75, "We moved to Bloxbury on a Tuesday.", "w", None),
    ("milo", 4.80, 7.06, 4.75, "By Wednesday, I knew something was wrong.", "w", None),
    ("milo", 7.26, 8.58, 7.35, "Mum said she'd be home late.", "w", None),
    ("milo", 8.70, 9.66, 9.00, "She always was.", "w", None),
    ("milo", 9.93, 11.30, 10.35, "...I never actually saw her.", "w", None),
    ("milo", 11.50, 14.05, 12.20, "The girl next door, Rae, didn't even say hello.", "w", None),
    ("rae", 0.00, 0.56, 15.00, "New kid?", "w", None),
    ("rae", 0.88, 1.58, 15.95, "One rule.", "w", None),
    ("rae", 1.88, 3.46, 17.00, "Three knocks after 3 A.M...", "w", None),
    ("rae", 3.76, 4.74, 18.95, "you don't answer.", "w", None),
    ("rae", 5.08, 5.54, 20.35, "EVER.", "r", None),
    ("milo", 14.58, 16.64, 21.60, "I thought she was joking. She wasn't.", "w", None),
    ("rae", 5.90, 6.70, 24.00, "I keep a list.", "w", None),
    ("rae", 6.92, 7.81, 25.10, "Of who's LEFT.", "w", None),
    ("milo", 16.82, 17.58, 26.60, "...Who's left?", "w", None),
    ("milo", 17.84, 20.30, 28.00, "That afternoon, everyone boarded up their windows.", "w", None),
    ("milo", 20.40, 22.14, 30.90, "And the Mayor's house had no door.", "w", None),
    ("milo", 22.26, 24.78, 33.60, "At 2:57, every light in Bloxbury...", "w", None),
    ("milo", 24.92, 25.66, 36.50, "went OFF.", "w", None),
    ("milo", 25.84, 26.68, 38.30, "Except mine.", "r", None),
    ("milo", 26.88, 27.66, 40.60, "3 A.M.", "r", None),
    ("milo", 28.66, 29.58, 45.90, "I checked the window.", "w", None),
    ("milo", 29.76, 30.64, 47.50, "Nobody was there.", "w", None),
    ("milo", 30.76, 32.12, 48.90, "Then it went quiet.", "w", None),
    ("milo", 32.28, 33.60, 52.20, "Then the knocking came again.", "w", None),
    ("milo", 33.80, 35.24, 55.50, "From INSIDE my closet.", "r", None),
    ("milo", 35.36, 36.54, 57.60, "And a voice whispered...", "w", None),
    ("milo", 36.94, 37.76, 59.90, "Milo...", "r", "echo"),
    ("milo", 37.80, 38.66, 61.00, "let me OUT.", "r", "echo"),
    ("milo", 38.86, 40.12, 62.90, "It knew my name.", "r", None),
    ("outro", 0.00, 6.34, 65.25, None, "w", None),     # captions from the outro word list below
]
OUTRO0 = 65.0                       # outro shot starts here (same layout as test2 shot A: LEAD 0.25, 6.75 s)
TOTAL = OUTRO0 + 6.75

HIGHLIGHT = {"NEVER", "ALWAYS", "RAE", "EVER", "LEFT", "OFF", "MINE", "NOBODY", "INSIDE", "CLOSET", "NAME", "DOOR",
             "FOLLOW", "LIKE", "PART", "2!", "OUT", "QUIET"}

# ---- sound effects: (file, dest, max_len, vol, fade_in, fade_out, filter)
SFX = [
    ("three_heavy_door_kno_#2", 0.00, 1.6, 0.75, 0, 0.3, None),        # hook knocks under the title line
    ("low_horror_drone_#1", 0.0, 2.8, 0.18, 0.2, 0.8, None),
    ("Sharp,_rhythmic_hamm_#1", 27.8, 3.3, 0.55, 0.0, 0.5, None),      # hammer hits at +0.26/1.22/2.20 (swings synced)
    ("low_horror_drone_#2", 33.2, 17.2, 0.20, 2.0, 1.2, "loop"),       # night bed, stops for the silence
    ("buzzing_street_lamp__#1", 36.45, 0.9, 0.9, 0, 0.2, None),        # lights clunk off on "went off"
    ("clock_ticking_#2", 39.4, 1.6, 0.6, 0.1, 0.2, None),
    ("a_sharp_horror_sting_#4", 40.55, 1.6, 0.5, 0, 0.5, None),        # small hit on "3 AM"
    ("buzzing_street_lamp__#2", 41.6, 1.7, 0.9, 0.05, 0.3, None),      # lamps die
    ("three_heavy_door_kno_#4", 42.9, 2.0, 0.95, 0, 0.3, None),        # front door knocks (onsets 43.41/43.70/43.97/44.25)
    ("three_heavy_door_kno_#1", 53.4, 1.9, 0.9, 0, 0.3, "muffled"),    # from inside the closet (onsets 53.69/53.99/54.26/54.53)
    ("low_horror_drone_#3", 53.4, 9.0, 0.32, 0.8, 0.3, None),
    ("creaking_wooden_door_#3", 57.4, 3.0, 2.0, 0, 0.5, None),
    ("a_sharp_horror_sting_#2", 61.30, 1.3, 1.0, 0, 0.3, None),        # JUMP SCARE: door ripped open, the lunge
    ("a_sharp_horror_sting_#1", 62.35, 2.0, 0.55, 0, 0.3, None),       # hard cut to black
    ("low_horror_drone_#4", 49.7, 2.2, 0.35, 0.3, 0.6, None),          # the silhouette in the window
    ("a_sharp_horror_sting_#3", 71.05, 1.5, 0.45, 0, 0.5, None),       # "don't open the door"
]


def load(path, a=0, b=None, filt=None):
    af = ["-af", filt] if filt else []
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(a)] + (["-t", str(b - a)] if b else []) + ["-i", path] + af + \
          ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768


N = int(round(TOTAL * FPS)) + 1
mix = np.zeros(int((TOTAL + 2) * SR), np.float32)
vox = np.zeros_like(mix)
spk = {"milo": np.zeros_like(mix), "rae": np.zeros_like(mix)}
FILE = {"milo": "milo.mp3", "rae": "rae.mp3", "outro": "outro.mp3"}


def put(buf, sig, t):
    i = int(t * SR); n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n]


for f, a, b, d, cap, st, fx in VOICE:
    filt = "aecho=0.8:0.7:180|360:0.35|0.2,volume=1.1" if fx == "echo" else None
    sig = load(AUD + FILE[f], a, b, filt)
    k = int(0.012 * SR); sig[:k] *= np.linspace(0, 1, k); sig[-k:] *= np.linspace(1, 0, k)
    put(mix, sig, d); put(vox, sig, d); put(spk["rae" if f == "rae" else "milo"], sig, d)

sfx_files = {os.path.splitext(x)[0].rsplit("-", 1)[0]: x for x in os.listdir(SFXD)}
for key, d, ln, vol, fi, fo, filt in SFX:
    path = SFXD + sfx_files[key]
    ff = "lowpass=f=650,volume=1.6" if filt == "muffled" else None
    sig = load(path, 0, None, ff)
    if filt == "loop":
        while len(sig) < ln * SR: sig = np.concatenate([sig, sig])
    sig = sig[:int(ln * SR)] * vol
    if fi: k = int(fi * SR); sig[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * SR); sig[-k:] *= np.linspace(1, 0, k)
    put(mix, sig, d)

mix = mix[:int(TOTAL * SR)]
pk = np.abs(mix).max(); mix = mix / max(pk, 1e-6) * 0.92
pcm = (mix * 32767).astype(np.int16)
import wave
with wave.open(OUT + "part1_audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def envelope(sig):
    rms, cen = [], []
    for f in range(N):
        a = int(f / FPS * SR); b = int((f + 1) / FPS * SR); seg = sig[a:b]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
        rms.append(r)
        if len(seg) and r > 1e-4:
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / SR)
            cen.append(float((sp * fr).sum() / (sp.sum() + 1e-9)))
        else: cen.append(0.0)
    return rms, cen


rms, cen = envelope(vox)
env = {"fps": FPS, "total": TOTAL, "nf": N, "rms": rms, "cen": cen, "outro0": OUTRO0, "lead": 0.25,
       "lines": [{"who": ("rae" if f == "rae" else "milo"), "file": f, "a": a, "b": b, "t0": d, "t1": d + (b - a),
                  "text": cap, "style": st} for f, a, b, d, cap, st, fx in VOICE]}

# ---- word timings in video time (for captions and accents)
def words_for(f, a, b, d):
    out = []
    for L in WORDS[f]:
        for w, s, e in L["words"]:
            if a - 0.06 <= s < b: out.append((w, d + (s - a), d + (min(e, b) - a)))
    return out


caps = []
for f, a, b, d, cap, st, fx in VOICE:
    ws = words_for(f, a, b, d)
    if f == "outro":
        groups = [("Want to find out who was in my closet?", 0.0, 1.70, "w"), ("FOLLOW and LIKE for PART 2!", 1.85, 3.35, "w"),
                  ("...and whatever you do...", 3.5, 4.5, "w"), ("don't open the door.", 4.9, 6.0, "r")]
        for text, ga, gb, gst in groups:
            caps.append((text, gst, [x for x in ws if d + ga <= x[1] < d + gb]))
    else:
        caps.append((cap, st, ws))
env["captions"] = [{"text": t, "style": st, "words": w} for t, st, w in caps]
json.dump(env, open(OUT + "env_p1.json", "w"))


# ---- ASS subtitles: small, lower-middle, word-by-word highlight
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
       "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: W,DejaVu Sans,54,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,120,120,560,1",
       "Style: R,DejaVu Sans,54,&H003C3CFF,&H003C3CFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,120,120,560,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
YEL = "&H0030E0FF&"
for i, (text, st, ws) in enumerate(caps):
    toks = text.split()
    if not ws: continue
    t0 = ws[0][1] - 0.05
    nxt = caps[i + 1][2][0][1] - 0.05 if i + 1 < len(caps) and caps[i + 1][2] else t0 + 3
    t1 = min(ws[-1][2] + 0.6, nxt)
    # map tokens to word times (sphinx splits "3 A.M." into three/a/m, "2:57" into two/fifty/seven)
    times = [w[1] for w in ws]
    tt = []; j = 0
    for tok in toks:
        tt.append(times[min(j, len(times) - 1)])
        core = tok.strip(".,!?\"'").upper()
        if core in ("3", "2!"): j += 1
        elif core.startswith("A.M") or core == "A.M": j += 2
        elif core == "2:57": j += 3
        else: j += 1
    for k, tok in enumerate(toks):
        a = tt[k]; b = tt[k + 1] if k + 1 < len(toks) else t1
        if k == 0: a = t0
        parts = []
        for q, tk in enumerate(toks):
            core = tk.strip(".,!?\"'").upper()
            if q == k and st == "w": parts.append("{\\c" + YEL + "}" + tk + "{\\r}")
            elif q == k: parts.append("{\\fscx108\\fscy108}" + tk + "{\\r}")
            elif q > k: parts.append("{\\alpha&H60&}" + tk + "{\\r}")
            else: parts.append(tk)
        ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},{'R' if st == 'r' else 'W'},,0,0,0,,{' '.join(parts)}")
open(OUT + "captions_p1.ass", "w").write("\n".join(ass) + "\n")
print("frames", N, "total", TOTAL, "captions", len(caps))
