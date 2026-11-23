# prep_p3.py - Part 3 "Don't Say It": cue sheet, pacing, mix, lip-sync envelopes, captions. 24 fps.
# Lines from _pipeline/data/p3/lines_*.json (align_full + split_lines; milo 12/13 + mum "Bug?" fixed by hand from the
# energy envelope, scan for in-word gaps/clicks clean 22 Nov). "Which Milo..." regenerated (pitch cracks) -> milo_p3_fix.mp3. Cues are SEQUENTIAL: dest = previous line end + gap.
# Usage: python3 prep_p3.py [repo]  (TIKTOK=1 -> music span <=55 s)  -> OUT_DIR/{env_p3.json, part3_audio.wav+.flac, captions_p3.ass}
import numpy as np, subprocess, json, os, sys, wave, re
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from music_bed import music_bed
from captions import write_ass
AUD = REPO + "/series/bloxbury/part3/voice/"; SFXD = REPO + "/assets/sfx/"; D = REPO + "/_pipeline/data/p3/"
OUT = os.environ.get("OUT_DIR", "/home/claude/talk/"); os.makedirs(OUT, exist_ok=True)
FPS, SR = 24, 48000
L = {k: json.load(open(D + f"lines_{k}.json")) for k in ("milo", "rae", "mum")}
FILE = {k: f"{k}_p3.mp3" for k in L}

def ln(who, text):
    for o in L[who]:
        if o["text"].lower().startswith(text.lower()): return o
    raise KeyError((who, text))

# (who, prefix, gap_before, mode, style, fx, scene-starting-here or None)
#  mode N narration / D dialogue (lip-sync) / C to camera / O off-screen.  style w / r.  fx None/door/closet/fake/phone
CUES = [
    ("milo", "I haven't", 0.10, "N", "w", None, "hook_bed"),        # frame 0: Milo lit, hand over mouth
    ("milo", "Because", 0.30, "N", "w", None, "door_feet"),         # 'something wrong' (shadow feet) by ~3.4 s
    ("mum", "Bug?", 1.30, "O", "r", "door", None),                  # soft knocks in the gap
    ("milo", "Last night", 0.55, "N", "w", None, "milo_close"),
    ("milo", "Then it heard", 0.20, "N", "r", None, None),
    ("mum", "Don't say", 0.70, "O", "w", "closet", "closet_crack"),
    ("mum", "Not one", 0.35, "O", "w", "closet", None),
    ("milo", "Mum had", 0.60, "N", "w", None, "rules_drawing"),
    ("milo", "Brush", 0.30, "N", "w", None, None),
    ("milo", "Lock", 0.25, "N", "w", None, None),
    ("milo", "And never", 0.35, "N", "r", None, None),
    ("mum", "Bug... if", 1.00, "O", "r", "fake_door", "door_ask"),  # MUSIC OUT
    ("mum", "tell me", 0.25, "O", "r", "fake_door", None),
    ("milo", "It wasn't", 0.70, "N", "w", None, "milo_push"),
    ("milo", "It was learning", 0.30, "N", "r", None, None),
    ("milo", "So I didn't", 0.60, "N", "w", None, "note"),
    ("milo", "I wrote", 0.25, "N", "w", None, None),                 # then pencil, slide in, wait, slide back, note insert
    ("milo", "I didn't make", 6.00, "N", "w", None, "escape"),       # window, roof, run
    ("rae", "Milo?", 3.80, "D", "w", None, "rae_door"),              # run + door unlock in the gap
    ("rae", "You just", 0.45, "D", "w", None, None),
    ("rae", "You said", 0.65, "D", "w", None, None),
    ("rae", "Lighthouse", 0.70, "D", "r", None, None),
    ("milo", "I never said", 0.80, "N", "w", None, "milo_realise"),
    ("milo", "I only wrote", 0.35, "N", "w", None, None),
    ("milo", "And I gave", 0.45, "N", "r", None, None),
    ("milo", "Most of you", 0.70, "N", "w", None, None),
    ("milo", "So did I", 0.40, "N", "w", None, None),
    ("milo", "Rae, it's me", 1.90, "O", "r", "phone", "phone"),      # silence, buzz, answer click
    ("milo", "Don't let", 0.40, "O", "r", "phone", None),
]
OUTRO = [("milo", "One of us is on the porch", 0.0, "C", "w", None, "outro"),
         ("milo", "One of us is on the phone", 0.30, "C", "w", None, None),
         ("milo", "Which Milo", 0.45, "C", "w", None, None)]
BLACK_AFTER, BLACK_LEN, TAIL = 0.45, 0.70, 1.20

def load(path, a=0, b=None, filt=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(a)] + (["-t", str(b - a)] if b else []) + ["-i", path] + \
          (["-af", filt] if filt else []) + ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768

FX = {None: None, "door": "lowpass=f=3200,volume=1.05", "fake_door": "lowpass=f=3200,volume=1.05",
      "closet": "lowpass=f=3800,volume=1.25",
      "phone": "highpass=f=320,lowpass=f=3400,acompressor=threshold=0.1:ratio=4,volume=1.1"}

def fake_double(sig):   # "slightly too perfect": faint lower copy 22 ms late
    low = np.interp(np.arange(0, len(sig), 1.012), np.arange(len(sig)), sig).astype(np.float32)
    d = int(0.022 * SR); out = sig.copy(); n = min(len(low), len(out) - d); out[d:d + n] += low[:n] * 0.22
    return out

def active_db(path):
    x = load(path); k = int(0.02 * SR); n = len(x) // k
    r = np.sqrt((x[:n * k].reshape(n, k) ** 2).mean(1)); r = r[r > 10 ** (-45 / 20)]
    return 20 * np.log10(np.sqrt((r ** 2).mean()))
REF = active_db(AUD + FILE["milo"])
GAIN = {w: 10 ** ((REF - active_db(AUD + f)) / 20) for w, f in FILE.items()}
print("voice gains dB", {w: round(20 * np.log10(g), 1) for w, g in GAIN.items()})

# ---- place voices sequentially
placed, t, scenes, marks = [], 0.0, [], {}
def place_line(who, pre, gap, mode, st, fx, scene):
    global t
    o = ln(who, pre); d = t + gap
    if scene: scenes.append([scene, round(d - min(gap, 0.35), 3)])
    f = o.get("file", FILE[who])                                    # regenerated single lines live in their own file
    g = GAIN[who] if f == FILE[who] else 10 ** ((REF - active_db(AUD + f)) / 20)
    sig = load(AUD + f, o["a"], o["b"], FX[fx]) * g
    if fx in ("door", "fake_door", "phone"): sig = fake_double(sig)
    k = int(0.01 * SR); sig[:k] *= np.linspace(0, 1, k); sig[-k:] *= np.linspace(1, 0, k)
    placed.append((who, o, d, mode, st, fx, sig)); marks[pre] = (d, d + len(sig) / SR); t = d + len(sig) / SR
for c in CUES: place_line(*c)
BLACK_CUT = round(t + BLACK_AFTER, 3); OUTRO0 = round(BLACK_CUT + BLACK_LEN, 3); t = OUTRO0
scenes.append(["black", BLACK_CUT])
for c in OUTRO: place_line(*c)
TOTAL = round(t + TAIL, 2)
SCENES = [(s, a, (scenes[i + 1][1] if i + 1 < len(scenes) else TOTAL)) for i, (s, a) in enumerate(scenes)]

N = int(round(TOTAL * FPS)) + 1
mix = np.zeros(int((TOTAL + 2) * SR), np.float32); vox = np.zeros_like(mix); spk = {k: np.zeros_like(mix) for k in L}
def put(buf, sig, at):
    i = int(at * SR); n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n]
for who, o, d, mode, st, fx, sig in placed: put(mix, sig, d); put(vox, sig, d); put(spk[who], sig, d)

# ---- SFX (Joel's ElevenLabs files; level set by RMS, files arrive ~-48 dB)
def sfx(key, var, a=0, b=None, db=-36, fi=0.02, fo=0.15, filt=None):
    f = next(SFXD + x for x in sorted(os.listdir(SFXD)) if x.lower().startswith(key.lower()) and re.search(r"#%s-\d+\." % var, x))
    s = load(f, a, b, filt); s *= 10 ** (db / 20) / (np.sqrt((s ** 2).mean()) + 1e-9)
    if fi: k = int(fi * SR); s[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * SR); s[-k:] *= np.linspace(1, 0, k)
    return s
m = marks
put(mix, sfx("Soft_knocks", 2, 1.05, 2.15, -30, filt="lowpass=f=2600"), m["Because"][1] + 0.25)          # three soft knocks before "Bug?"
put(mix, sfx("Pencil_writing", 2, 0.1, 1.7, -36), m["I wrote"][1] + 0.15)                                # writes LIGHTHOUSE
# Joel 21:57: the two slides overlapped each other and the window (sounded repeated). Now: short soft push in,
# ~0.9 s of silence, then a slower, different slide back, and 0.5 s of quiet on the note before the window.
put(mix, sfx("Paper_slide", 2, 0.6, 1.6, -39, fo=0.25), m["I wrote"][1] + 1.95)                         # pushed into the closet
put(mix, sfx("Paper_slide", 1, 0.9, 2.2, -36, fo=0.3), m["I wrote"][1] + 3.85)                          # ...slides back
put(mix, sfx("Window_open", 1, 0.8, 3.5, -34, fo=0.4), m["I didn't make"][0] - 0.6)
put(mix, sfx("Roof_steps", 1, 0.0, 2.6, -38, fi=0.2, fo=0.5), m["I didn't make"][0] + 1.6)
put(mix, sfx("Night_ambience", 2, 0.0, m["Rae, it's me"][0] - m["I didn't make"][0] + 0.5, -47, fi=0.6, fo=0.8), m["I didn't make"][0] - 0.2)
put(mix, sfx("Night_run", 3, 0.0, 3.2, -36, fi=0.3, fo=0.6), m["I didn't make"][1] + 0.2)
put(mix, sfx("Door_unlock", 2, 3.2, 5.6, -34), m["Milo?"][0] - 2.2)
put(mix, sfx("Phone_buzz", 1, 0.0, 2.5, -30), m["So did I"][1] + 0.35)                                   # the one startle: a buzz in silence
put(mix, sfx("Phone_click", 4, 1.1, 1.6, -38), m["Rae, it's me"][0] - 0.45)
put(mix, sfx("low_horror_drone_#2".split("#")[0], 2, 0, 3.0, -44, fi=1.0, fo=1.0), m["Bug... if"][0] - 0.2)  # faint swell under the ask
mix[int(BLACK_CUT * SR):int(OUTRO0 * SR)] = 0

# music: out from the door ask until the escape; out again for the phone; back for the outro (YouTube)
MUTES = [(m["Bug... if"][0] - 0.3, m["I didn't make"][0] - 0.8), (m["So did I"][1] + 0.1, OUTRO0)]
TIKTOK = bool(os.environ.get("TIKTOK"))
MUSIC_MUTES = MUTES[:-1] + [(m["So did I"][1] + 0.1, TOTAL)] if TIKTOK else MUTES
# NOMUSIC=1: voices + SFX only, for TikTok uploads where the song is added in-app from TikTok's own library (licensed path)
NOMUSIC = bool(os.environ.get("NOMUSIC"))
# Music sits well UNDER the voices (Joel 21:54: softer, "premium"): bed at 0.20, low end trimmed, and ducked a further
# ~7 dB while anyone speaks (40 ms attack, 450 ms release) so it swells only in the gaps between lines.
def duck_curve(v, depth_db=-7.0, att=0.04, rel=0.45):
    k = int(0.01 * SR); n = len(v) // k
    lvl = np.sqrt((v[:n * k].reshape(n, k) ** 2).mean(1)); on = (lvl > 10 ** (-42 / 20)).astype(np.float32)
    g = np.ones(n, np.float32); cur = 1.0; lo = 10 ** (depth_db / 20)
    for i in range(n):
        tgt = lo if on[i] else 1.0; c = 0.01 / (att if tgt < cur else rel); cur += (tgt - cur) * min(1, c); g[i] = cur
    return np.repeat(g, k).tolist() + [1.0] * (len(v) - n * k)
if not NOMUSIC:
    bed = music_bed(REPO, TOTAL, SR, len(mix), part=3, mutes=MUSIC_MUTES)
    bed = bed - np.convolve(bed, np.ones(64) / 64, "same") * 0.5     # gentle low trim
    mix += bed * np.array(duck_curve(vox), np.float32)
mix[int(BLACK_CUT * SR):int(OUTRO0 * SR)] = 0
mix = mix[:int(TOTAL * SR)]; mix = mix / max(np.abs(mix).max(), 1e-6) * 0.92
with wave.open(OUT + "part3_raw.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
mm = subprocess.run(["ffmpeg", "-hide_banner", "-i", OUT + "part3_raw.wav", "-af", "loudnorm=I=-16:TP=-2:LRA=11:print_format=json",
                     "-f", "null", "-"], capture_output=True, text=True).stderr
mj = json.loads(mm[mm.rindex("{"):mm.rindex("}") + 1])
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", OUT + "part3_raw.wav", "-af",
                f"loudnorm=I=-16:TP=-2:LRA=11:measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
                f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']}:linear=true", "-ar", str(SR),
                OUT + ("part3_nomusic.wav" if NOMUSIC else "part3_tiktok.wav" if TIKTOK else "part3_audio.wav")], check=True)
# the repo/pods keep the mix as lossless FLAC (half the size; *.wav is gitignored): copy partN_*.flac to _pipeline/data/pN/
_w = OUT + ("part3_nomusic.wav" if NOMUSIC else "part3_tiktok.wav" if TIKTOK else "part3_audio.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", _w, "-c:a", "flac", _w[:-4] + ".flac"], check=True)

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
caps = [{"who": who, "text": o["text"], "style": st, "mode": mode, "fx": fx, "t0": d, "t1": d + len(sig) / SR,
         "words": [(w, d + (s - o["a"]), d + (min(e, o["b"]) - o["a"])) for w, s, e in o["words"]]}
        for who, o, d, mode, st, fx, sig in placed]
json.dump({"fps": FPS, "total": TOTAL, "nf": N, "outro0": OUTRO0, "black_cut": BLACK_CUT, "scenes": SCENES, "mutes": MUTES,
           "rms": {k: v[0] for k, v in envs.items()}, "cen": {k: v[1] for k, v in envs.items()},
           "lines": caps, "lipsync_modes": ["D", "C"]}, open(OUT + "env_p3.json", "w"))
write_ass(caps, OUT + "captions_p3.ass", BLACK_CUT)
print("frames", N, "total", TOTAL, "black", BLACK_CUT, "lines", len(caps))
for s, a, b in SCENES: print(f"  {a:6.2f}-{b:6.2f} {s}")
