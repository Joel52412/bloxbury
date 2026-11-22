# prep_p2.py - Part 2 "She Came Home": cue sheet, pacing, audio mix, lip-sync envelopes and word-timed captions. 24 fps.
# Line cuts come from split_lines.py / pocketsphinx (data in _pipeline/data/p2/lines_*.json). ElevenLabs leaves digital
# silence between lines, so every cut sits in silence. Pacing is set here (dest times), not in the recordings.
# Usage: python3 prep_p2.py [repo_root]  -> /home/claude/talk/{env_p2.json, part2_audio.wav, captions_p2.ass}
import numpy as np, subprocess, json, os, sys, wave
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from music_bed import music_bed
AUD = REPO + "/series/bloxbury/part2/voice/"
SFXD = REPO + "/assets/sfx/"
OUT = os.environ.get("OUT_DIR", "/home/claude/talk/"); os.makedirs(OUT, exist_ok=True)
FPS, SR = 24, 48000
D = REPO + "/_pipeline/data/p2/"
L = {k: json.load(open(D + f"lines_{k}.json")) for k in ("milo", "rae", "mum")}
FILE = {"milo": "milo_p2.mp3", "rae": "rae_p2.mp3", "mum": "mum_p2.mp3"}

def ln(who, text):
    for o in L[who]:
        if o["text"].lower().startswith(text.lower()): return o
    raise KeyError((who, text))

# ---- cue sheet: (who, line-text prefix, dest_start, mode, style, fx)
#  mode: N narration (no mouth) / D in-scene dialogue (lip-sync) / C to camera (lip-sync) / O off-screen (no mouth)
#  style: caption colour "w" white / "r" red.   fx: None / fake (too-perfect double) / downstairs / closet / door
CUES = [
    # 0 bridge 0.00-1.25: Part 1's final lunge (dark) -> black -> match cut grin->smile at 1.25
    # 1 sunny kitchen
    ("milo", "My mum finally", 1.30, "N", "w", None),
    ("milo", "I wish", 4.15, "N", "r", None),
    ("mum", "Morning", 5.60, "D", "w", "fake"),
    # 2 the wrong detail (pattern break)
    ("milo", "She made", 7.00, "N", "w", None),
    ("milo", "She hummed", 9.00, "N", "w", None),
    ("milo", "She hugged", 11.00, "N", "w", None),
    ("milo", "And she called", 14.20, "N", "w", None),
    ("milo", "Mum never", 16.30, "N", "r", None),
    # 3 Rae's porch
    ("milo", "My mum's back", 18.80, "D", "w", None),
    ("rae", "Did she knock", 21.50, "D", "w", None),
    ("milo", "No... she had", 23.40, "D", "w", None),
    ("rae", "Then it doesn't", 25.50, "D", "w", None),
    ("rae", "Milo...", 28.60, "D", "w", None),
    ("rae", "your mum was", 30.00, "D", "r", None),
    ("rae", "Three weeks", 33.30, "D", "r", None),
    # 4 next question
    ("milo", "So who's", 35.10, "D", "w", None),
    ("rae", "Check a mirror", 37.00, "D", "w", None),
    ("rae", "Mirrors don't", 38.20, "D", "w", None),
    # 5 hallway mirror, night
    ("milo", "It looked like", 40.30, "N", "w", None),
    ("milo", "Then Mum stopped", 42.20, "N", "w", None),
    ("milo", "Her reflection", 44.60, "N", "r", None),           # music cut at 44.30; reflection turns 46.2-47.6
    ("mum", "Milo...", 47.80, "D", "w", "fake"),
    ("mum", "who told you", 49.00, "D", "r", "fake"),
    # 6 bedroom
    ("milo", "I locked", 52.00, "N", "w", None),
    ("mum", "Milo! Dinner", 53.40, "O", "w", "downstairs"),
    ("milo", "Then a voice", 56.80, "N", "w", None),              # music out 56.6 -> outro
    ("mum", "Bug...", 59.60, "O", "w", "closet"),
    ("mum", "don't go", 60.70, "O", "w", "closet"),
    ("mum", "I heard", 62.40, "O", "r", "closet"),
    ("milo", "Mum?", 64.30, "D", "w", None),
    # 7 the door: footsteps 65.2-67.5, soft knocks 67.9/68.45/69.0
    ("mum", "Bug?", 69.60, "O", "w", "door"),
    ("mum", "Who are you", 70.70, "O", "r", "door"),             # hard cut to black 72.40
    # 8 outro to camera
    ("milo", "Two mums", 73.25, "C", "w", None),
    ("milo", "Which one", 75.20, "C", "w", None),
    ("milo", "Comment below", 76.90, "C", "w", None),
]
BLACK_CUT = 72.40
OUTRO0 = 73.00
TOTAL = 80.00
MUTES = [(0.0, 1.25), (44.30, 51.60), (56.60, OUTRO0)]
# TikTok only authorises copyrighted music for under 1 minute (first to last second it's heard). TIKTOK=1 keeps the
# music off after the bedroom dropout (no return in the outro), so it spans 1.25-56.6 s = 55 s. Mix only; lip-sync env unchanged.
TIKTOK = bool(os.environ.get("TIKTOK"))
MUSIC_MUTES = MUTES[:-1] + [(56.60, TOTAL)] if TIKTOK else MUTES
SCENES = [("bridge", 0.0, 1.25), ("kitchen", 1.25, 18.4), ("porch", 18.4, 39.9), ("mirror", 39.9, 51.7),
          ("bedroom", 51.7, BLACK_CUT), ("black", BLACK_CUT, OUTRO0), ("outro", OUTRO0, TOTAL)]

def load(path, a=0, b=None, filt=None):
    af = ["-af", filt] if filt else []
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(a)] + (["-t", str(b - a)] if b else []) + ["-i", path] + af + \
          ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768

FX = {None: None,
      "fake": "volume=1.0",                                              # double added below
      "downstairs": "highpass=f=180,lowpass=f=2300,aecho=0.8:0.6:45|90:0.25|0.12,volume=0.75",
      "closet": "lowpass=f=3800,volume=1.25",
      "door": "lowpass=f=3200,volume=1.05"}

N = int(round(TOTAL * FPS)) + 1
mix = np.zeros(int((TOTAL + 2) * SR), np.float32)
vox = np.zeros_like(mix)
spk = {k: np.zeros_like(mix) for k in ("milo", "rae", "mum")}
rng = np.random.default_rng(7)

def put(buf, sig, t):
    i = int(t * SR); n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n]

def fake_double(sig):
    # "slightly too perfect": a faint copy a hair lower in pitch, 22 ms late -> uncanny but still her voice
    low = np.interp(np.arange(0, len(sig), 1.012), np.arange(len(sig)), sig).astype(np.float32)
    d = int(0.022 * SR); out = sig.copy(); n = min(len(low), len(out) - d); out[d:d + n] += low[:n] * 0.22
    return out

# per-voice gain: ElevenLabs renders each voice at a different level (Mum ~10 dB hotter than Milo). Match every
# file's active speech level to Milo's, keeping each performance's own dynamics (whispers stay quieter).
def active_db(path):
    x = load(path); k = int(0.02 * SR); n = len(x) // k
    r = np.sqrt((x[:n * k].reshape(n, k) ** 2).mean(1)); r = r[r > 10 ** (-45 / 20)]
    return 20 * np.log10(np.sqrt((r ** 2).mean()))
REF = active_db(AUD + FILE["milo"])
GAIN = {w: 10 ** ((REF - active_db(AUD + f)) / 20) for w, f in FILE.items()}
print("voice gains dB", {w: round(20 * np.log10(g), 1) for w, g in GAIN.items()})

placed = []
for who, pre, d, mode, st, fx in CUES:
    o = ln(who, pre)
    sig = load(AUD + FILE[who], o["a"], o["b"], FX[fx]) * GAIN[who]
    if fx in ("fake", "door"): sig = fake_double(sig) if fx == "fake" else fake_double(sig) * 1.0
    k = int(0.01 * SR); sig[:k] *= np.linspace(0, 1, k); sig[-k:] *= np.linspace(1, 0, k)
    put(mix, sig, d); put(vox, sig, d); put(spk[who], sig, d)
    placed.append((who, o, d, mode, st, fx, len(sig) / SR))

# overlap check: no two lines on top of each other
ends = sorted((d, d + dur, o["text"]) for who, o, d, m, s, f, dur in placed)
for (a0, a1, t0), (b0, b1, t1) in zip(ends, ends[1:]):
    assert a1 <= b0 + 0.02, f"overlap: {t0} ({a1:.2f}) / {t1} ({b0:.2f})"

# ---- sound design (no loud stings; silence does the work)
def sfx(name):
    files = {os.path.splitext(x)[0].rsplit("-", 1)[0]: x for x in os.listdir(SFXD)}; return SFXD + files[name]

def env_fade(sig, fi, fo):
    if fi: k = int(fi * SR); sig[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * SR); sig[-k:] *= np.linspace(1, 0, k)
    return sig

# bridge: Part 1's lunge under a low swell, then dead silence on black
put(mix, env_fade(load(sfx("low_horror_drone_#3"), 0, 0.85) * 0.45, 0.05, 0.12), 0.0)
# kitchen: pan sizzle only under the opening (Joel 13:15: was too loud and ran too long, read as static).
# 1.25-7.0 s, ~8 dB quieter, softer top end, mostly crackle, faded out after "Morning, Milo!"
# Joel 15:25: the synth crackle didn't read as sizzling. Use his ElevenLabs SFX "pan_sizzle" (variant SIZZLE_VAR);
# until it's in "assets/sfx/" the kitchen opening has no sizzle at all (better silent than fake).
SIZZLE_VAR = os.environ.get("SIZZLE_VAR", "1")     # Joel sent #1 and #4 (15:31); #1 is steadier and starts at once
SIZZLE_DB = float(os.environ.get("SIZZLE_DB", -38))  # RMS before loudnorm: a bed under the voices, not "static"
try:
    import re as _re
    f = next(SFXD + x for x in sorted(os.listdir(SFXD))
             if x.lower().startswith("pan_sizzle") and _re.search(r"[_#]%s-\d+\." % SIZZLE_VAR, x))
    sz = load(f, 0.5, 6.25)                                   # variant 1 hisses from the first frame; skip the attack
    sz *= 10 ** (SIZZLE_DB / 20) / (np.sqrt((sz ** 2).mean()) + 1e-9)   # ElevenLabs files arrive ~-48 dB: set a fixed level
    put(mix, env_fade(sz, 0.3, 1.4), 1.25)
except StopIteration:
    print("NO SIZZLE SFX: ask Joel for pan_sizzle (prompt in VOICE_DESIGN.md -> SFX requests)")
# hallway at night: clock ticking, which stops dead with the music at 44.30
put(mix, env_fade(load(sfx("clock_ticking_#1"), 0, 4.4) * 0.35, 0.3, 0.02), 39.9)
# reflection turns in silence; only a faint low swell as the head turns (46.2-47.6)
put(mix, env_fade(load(sfx("low_horror_drone_#2"), 0, 1.8) * 0.18, 0.8, 0.6), 46.0)
# closet: tiny creak as the crack widens and the hand shows (63.9)
put(mix, env_fade(load(sfx("creaking_wooden_door_#2"), 0, 1.1, "lowpass=f=3000") * 0.30, 0.05, 0.4), 63.85)
# footsteps on the stairs, slowing, then stopping outside the door
t = 65.2
for i, gap in enumerate([0.52, 0.55, 0.58, 0.64, 0.72, 0.0]):
    k = int(0.16 * SR); thud = rng.standard_normal(k).astype(np.float32)
    thud = np.convolve(thud, np.ones(40) / 40, "same") * np.exp(-np.arange(k) / (0.035 * SR)) * (0.55 + 0.08 * i)
    put(mix, thud, t); t += gap
# three soft knocks (Joel 13:15: use the other knock). Part 1's front-door knock (#4), its first three knocks as
# performed (onsets 0.53/0.84/1.09), quieter and a little muffled: the series' signature knock, gentler this time.
kn = load(sfx("three_heavy_door_kno_#4"), 0.45, 1.33, "lowpass=f=2400")   # stops before its 4th knock (1.37)
put(mix, env_fade(kn * 0.55, 0.01, 0.12), 67.82)              # knocks land at ~67.90 / 68.21 / 68.46
# hard cut to black: everything stops
mix[int(BLACK_CUT * SR):int(OUTRO0 * SR)] = 0

mix += music_bed(REPO, TOTAL, SR, len(mix), part=2, mutes=MUSIC_MUTES)
mix[int(BLACK_CUT * SR):int(OUTRO0 * SR)] = 0
mix = mix[:int(TOTAL * SR)]
pk = np.abs(mix).max(); mix = mix / max(pk, 1e-6) * 0.92
with wave.open(OUT + "part2_raw.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
# final loudness: TikTok/Shorts sit around -14 LUFS. Two-pass loudnorm with a -1.5 dBTP ceiling (silences stay silent).
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT + "part2_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
mj = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", OUT + "part2_raw.wav", "-af",
                f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
                f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']}:linear=true", "-ar", str(SR), OUT + "part2_audio.wav"], check=True)

def envelope(sig):
    rms, cen = [], []
    for f in range(N):
        a = int(f / FPS * SR); b = int((f + 1) / FPS * SR); seg = sig[a:b]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0; rms.append(r)
        if len(seg) and r > 1e-4:
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / SR)
            cen.append(float((sp * fr).sum() / (sp.sum() + 1e-9)))
        else: cen.append(0.0)
    return rms, cen

envs = {k: envelope(v) for k, v in spk.items()}
caps = []
for who, o, d, mode, st, fx, dur in placed:
    ws = [(w, d + (s - o["a"]), d + (min(e, o["b"]) - o["a"])) for w, s, e in o["words"]]
    caps.append({"who": who, "text": o["text"], "style": st, "mode": mode, "fx": fx, "t0": d, "t1": d + dur, "words": ws})
env = {"fps": FPS, "total": TOTAL, "nf": N, "outro0": OUTRO0, "black_cut": BLACK_CUT, "scenes": SCENES, "mutes": MUTES,
       "rms": {k: v[0] for k, v in envs.items()}, "cen": {k: v[1] for k, v in envs.items()},
       "lines": caps, "lipsync_modes": ["D", "C"]}
json.dump(env, open(OUT + "env_p2.json", "w"))

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
       "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: W,DejaVu Sans,54,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,120,120,330,1",
       "Style: R,DejaVu Sans,54,&H003C3CFF,&H003C3CFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,120,120,330,1",
       "Style: I,DejaVu Sans,50,&H00D8D8D8,&H00D8D8D8,&H00101010,&H80000000,-1,-1,0,0,100,100,0,0,1,6,2,2,120,120,330,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
YEL = "&H0030E0FF&"
for i, c in enumerate(caps):
    toks = c["text"].split(); ws = c["words"]
    if not ws: continue
    sty = "R" if c["style"] == "r" else ("I" if c["mode"] == "O" else "W")   # off-screen voices in grey italics
    t0 = ws[0][1] - 0.05
    nxt = caps[i + 1]["words"][0][1] - 0.05 if i + 1 < len(caps) else t0 + 3
    t1 = min(ws[-1][2] + 0.6, nxt)
    if t0 < BLACK_CUT <= t1: t1 = BLACK_CUT
    times = [w[1] for w in ws]
    tt = [times[min(j, len(times) - 1)] for j in range(len(toks))]
    for k, tok in enumerate(toks):
        a = t0 if k == 0 else tt[k]; b = tt[k + 1] if k + 1 < len(toks) else t1
        parts = []
        for q, tk in enumerate(toks):
            if q == k and sty == "W": parts.append("{\\c" + YEL + "}" + tk + "{\\r}")
            elif q == k: parts.append("{\\fscx108\\fscy108}" + tk + "{\\r" + sty + "}")
            elif q > k: parts.append("{\\alpha&H60&}" + tk + "{\\r" + sty + "}")
            else: parts.append(tk)
        ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},{sty},,0,0,0,,{' '.join(parts)}")
open(OUT + "captions_p2.ass", "w").write("\n".join(ass) + "\n")
print("frames", N, "total", TOTAL, "lines", len(caps))
