# mix.py - the shared audio kit. A prep_pN.py = cue sheet + SFX list; loading, level matching, voice FX, pacing,
# music bed + ducking, loudness, lip-sync envelopes, env_pN.json and captions all live here (any series).
#
#   from mix import Mix
#   m = Mix(REPO, "p4", series="bloxbury", voices=("milo", "rae", "mum"))   # lines from _pipeline/data/p4/lines_<who>.json
#   for c in CUES: m.cue(*c)                     # (who, prefix, gap_before, mode, style, fx, scene) - sequential pacing
#   m.voice("mum", "Bug?", at=69.6, mode="O", style="w", fx="door")        # or an absolute dest time
#   m.sfx("Phone_buzz", 1, 0.0, 2.5, db=-30, at=m.marks["So did I"][1] + 0.35)  # Joel's ElevenLabs SFX, level by RMS
#   m.silence(black_cut, outro0); m.music(part=4, mutes=MUTES, duck=True)
#   m.finish(total, black_cut=..., outro0=..., scenes=..., mutes=MUTES)  # mix -> loudnorm wav, env_p4.json, captions_p4.ass
#
# Modes: N narration (no mouth) / D in-scene dialogue (lip-sync) / C to camera (lip-sync) / O off-screen (no mouth).
# Styles: caption colour w / r.  FX: see FX below (door/fake_door/phone/fake also get the "too perfect" double).
# Env: OUT_DIR (default /home/claude/talk/), TIKTOK=1 (music span <=55 s: pass tiktok mutes), NOMUSIC=1 (voices + SFX only).
import numpy as np, subprocess, json, os, re, wave, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from music_bed import music_bed
from captions import write_ass
from visemes import viseme_tracks

FPS, SR = 24, 48000
FX = {None: None,
      "fake": "volume=1.0",                                                 # fake Mum: double added in voice()
      "downstairs": "highpass=f=180,lowpass=f=2300,aecho=0.8:0.6:45|90:0.25|0.12,volume=0.75",
      "closet": "lowpass=f=3800,volume=1.25",
      "door": "lowpass=f=3200,volume=1.05",
      "fake_door": "lowpass=f=3200,volume=1.05",
      "phone": "highpass=f=320,lowpass=f=3400,acompressor=threshold=0.1:ratio=4,volume=1.1",
      "echo": "aecho=0.8:0.7:180|360:0.35|0.2,volume=1.1"}
DOUBLED = ("fake", "door", "fake_door", "phone")


# ================================================================== primitives
def load(path, a=0, b=None, filt=None, sr=SR):
    """Mono float32 samples of path from a to b seconds, through an optional ffmpeg filter."""
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(a)] + (["-t", str(b - a)] if b else []) + ["-i", path] + \
          (["-af", filt] if filt else []) + ["-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768


def put(buf, sig, at, sr=SR):
    i = int(at * sr); n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n]


def fade(sig, fi, fo, sr=SR):
    if fi: k = int(fi * sr); sig[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * sr); sig[-k:] *= np.linspace(1, 0, k)
    return sig


def fake_double(sig, sr=SR):
    """'Slightly too perfect': a faint copy a hair lower in pitch, 22 ms late -> uncanny but still the same voice."""
    low = np.interp(np.arange(0, len(sig), 1.012), np.arange(len(sig)), sig).astype(np.float32)
    d = int(0.022 * sr); out = sig.copy(); n = min(len(low), len(out) - d); out[d:d + n] += low[:n] * 0.22
    return out


def active_db(path, sr=SR):
    """Level of the speech in a file (20 ms windows above -45 dB): voices are matched on this, keeping their dynamics."""
    x = load(path, sr=sr); k = int(0.02 * sr); n = len(x) // k
    r = np.sqrt((x[:n * k].reshape(n, k) ** 2).mean(1)); r = r[r > 10 ** (-45 / 20)]
    return 20 * np.log10(np.sqrt((r ** 2).mean()))


def repair(sig, a0, ops, sr=SR):
    """In-take glitch fixes in SOURCE seconds: ("fadein", t, len) and ("cut", t0, t1) with a 3 ms crossfade; a cut is
    padded back with silence at the end so everything after stays in sync with the rendered lip-sync."""
    for op in ops:
        if op[0] == "fadein":
            i = int((op[1] - a0) * sr); k = int(op[2] * sr); sig[i:i + k] *= np.linspace(0, 1, k)
    for op in ops:
        if op[0] == "cut":
            i, j = int((op[1] - a0) * sr), int((op[2] - a0) * sr); x = int(0.003 * sr)
            head, tail = sig[:i + x].copy(), sig[j:].copy()
            head[-x:] = head[-x:] * np.linspace(1, 0, x) + tail[:x] * np.linspace(0, 1, x)
            sig = np.concatenate([head, tail[x:], np.zeros(j - i, np.float32)])
    return sig


def duck_curve(v, depth_db=-7.0, att=0.04, rel=0.45, sr=SR):
    """Gain curve that dips the music ~7 dB while anyone speaks (40 ms attack, 450 ms release)."""
    k = int(0.01 * sr); n = len(v) // k
    lvl = np.sqrt((v[:n * k].reshape(n, k) ** 2).mean(1)); on = (lvl > 10 ** (-42 / 20)).astype(np.float32)
    g = np.ones(n, np.float32); cur = 1.0; lo = 10 ** (depth_db / 20)
    for i in range(n):
        tgt = lo if on[i] else 1.0; c = 0.01 / (att if tgt < cur else rel); cur += (tgt - cur) * min(1, c); g[i] = cur
    return np.repeat(g, k).tolist() + [1.0] * (len(v) - n * k)


def envelope(sig, nf, fps=FPS, sr=SR):
    """Per-frame loudness + spectral centroid: drives rig2 lip-sync (open/close) and mouth shape."""
    rms, cen = [], []
    for f in range(nf):
        a = int(f / fps * sr); b = int((f + 1) / fps * sr); seg = sig[a:b]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0; rms.append(r)
        if len(seg) and r > 1e-4:
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / sr)
            cen.append(float((sp * fr).sum() / (sp.sum() + 1e-9)))
        else: cen.append(0.0)
    return rms, cen


def write_wav(path, x, sr=SR):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes())


def loudnorm(src, dst, lufs=-16, tp=-2, sr=SR):
    """Two-pass EBU R128 loudnorm (linear, so silences stay silent). Joel 21:54: -16 LUFS / -2 dBTP."""
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    mj = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af",
                    f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
                    f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']}:linear=true", "-ar", str(sr), dst], check=True)


def sfx_path(sfxd, key, var=None):
    """Joel's ElevenLabs files keep their names: 'Phone_buzz,_a_mobile_#1-1795....mp3'. key = name prefix (case-free),
    var = variant number; var=None -> key is the exact name before the '-<id>' suffix."""
    names = sorted(os.listdir(sfxd))
    if var is None:
        return sfxd + {os.path.splitext(x)[0].rsplit("-", 1)[0]: x for x in names}[key]
    return sfxd + next(x for x in names if x.lower().startswith(key.lower()) and re.search(r"[_#]%s-\d+\." % var, x))


# ================================================================== the mix
class Mix:
    """Voices, SFX and music for one part. Everything is recorded as events and summed in order at finish()."""

    def __init__(self, repo, part, series="bloxbury", voices=("milo",), files=None, ref=None, out=None, fps=FPS, sr=SR,
                 voice_dir=None, data_dir=None, sfx_dir=None):
        n = part.lstrip("p")
        self.repo, self.part, self.fps, self.sr = repo, part, fps, sr
        self.aud = voice_dir or "%s/series/%s/part%s/voice/" % (repo, series, n)
        self.data = data_dir or "%s/_pipeline/data/%s/" % (repo, part)
        self.sfxd = sfx_dir or repo + "/assets/sfx/"
        self.out = out or os.environ.get("OUT_DIR", "/home/claude/talk/"); os.makedirs(self.out, exist_ok=True)
        self.voices = tuple(voices)
        self.L = {k: json.load(open(self.data + "lines_%s.json" % k)) for k in self.voices}
        self.files = files or {k: "%s_%s.mp3" % (k, part) for k in self.voices}
        self.ref = active_db(self.aud + self.files[ref or self.voices[0]], sr)          # every voice matched to the lead
        self.gain = {w: 10 ** ((self.ref - active_db(self.aud + f, sr)) / 20) for w, f in self.files.items()}
        print("voice gains dB", {w: round(20 * np.log10(g), 1) for w, g in self.gain.items()})
        self.placed, self.events, self.scenes, self.marks = [], [], [], {}
        self.t = 0.0                                                                     # end of the last placed line
        self.tiktok = bool(os.environ.get("TIKTOK")); self.nomusic = bool(os.environ.get("NOMUSIC"))

    def line(self, who, prefix):
        for o in self.L[who]:
            if o["text"].lower().startswith(prefix.lower()): return o
        raise KeyError((who, prefix))

    def voice(self, who, prefix, at=None, gap=None, mode="N", style="w", fx=None, scene=None, fix=None):
        """Place one line at `at` seconds, or `gap` after the previous line ends. scene: a scene starts here (its cut
        lands min(gap, 0.35) s before the line). fix: repair() ops for this take. Returns (t0, t1)."""
        o = self.line(who, prefix); d = at if at is not None else self.t + gap
        if scene: self.scenes.append([scene, round(d - min(gap or 0.0, 0.35), 3)])
        f = o.get("file", self.files[who])                                # regenerated single lines live in their own file
        g = self.gain[who] if f == self.files[who] else 10 ** ((self.ref - active_db(self.aud + f, self.sr)) / 20)
        sig = load(self.aud + f, o["a"], o["b"], FX[fx], self.sr) * g
        if fix: sig = repair(sig, o["a"], fix, self.sr)
        if fx in DOUBLED: sig = fake_double(sig, self.sr)
        k = int(0.01 * self.sr); sig[:k] *= np.linspace(0, 1, k); sig[-k:] *= np.linspace(1, 0, k)
        self.placed.append((who, o, d, mode, style, fx, sig)); self.events.append(("voice", sig, d, who))
        self.marks[prefix] = (d, d + len(sig) / self.sr); self.t = d + len(sig) / self.sr
        return self.marks[prefix]

    def cue(self, who, prefix, gap, mode, style, fx=None, scene=None):
        """Sequential cue-sheet row (Part 3+): dest = previous line end + gap."""
        return self.voice(who, prefix, gap=gap, mode=mode, style=style, fx=fx, scene=scene)

    def scene(self, name, t):
        self.scenes.append([name, t])

    def check_overlaps(self, tol=0.02):
        ends = sorted((d, d + len(sig) / self.sr, o["text"]) for who, o, d, m, s, f, sig in self.placed)
        for (a0, a1, t0), (b0, b1, t1) in zip(ends, ends[1:]):
            assert a1 <= b0 + tol, f"overlap: {t0} ({a1:.2f}) / {t1} ({b0:.2f})"

    def put(self, sig, at):
        self.events.append(("sfx", sig, at, None))

    def file(self, key, var=None):
        return sfx_path(self.sfxd, key, var)

    def sfx(self, key, var, a=0, b=None, db=-36, fi=0.02, fo=0.15, filt=None, at=0.0):
        """ElevenLabs SFX at a fixed RMS level (files arrive ~-48 dB, so level by RMS, not by gain)."""
        s = load(self.file(key, var), a, b, filt, self.sr); s *= 10 ** (db / 20) / (np.sqrt((s ** 2).mean()) + 1e-9)
        self.put(fade(s, fi, fo, self.sr), at)
        return s

    def silence(self, a, b):
        """Hard silence (cut to black): everything recorded so far is zeroed in [a, b)."""
        self.events.append(("silence", None, a, b))

    def music(self, part=None, mutes=(), duck=False, low_trim=False):
        """Music bed (music_bed.PART_MUSIC[part]) with dropouts; duck=True dips it under every voice placed so far."""
        if not self.nomusic: self.events.append(("music", part, tuple(mutes), (duck, low_trim)))

    # ------------------------------------------------------------------ build + write
    def build(self, total):
        sr = self.sr
        mix = np.zeros(int((total + 2) * sr), np.float32); vox = np.zeros_like(mix)
        spk = {k: np.zeros_like(mix) for k in self.voices}
        for kind, a, b, c in self.events:
            if kind == "voice": put(mix, a, b, sr); put(vox, a, b, sr); put(spk[c], a, b, sr)
            elif kind == "sfx": put(mix, a, b, sr)
            elif kind == "silence": mix[int(b * sr):int(c * sr)] = 0
            elif kind == "music":
                duck, low_trim = c
                bed = music_bed(self.repo, total, sr, len(mix), part=a or int(self.part.lstrip("p")), mutes=b)
                if low_trim: bed = bed - np.convolve(bed, np.ones(64) / 64, "same") * 0.5     # gentle low trim
                if duck: bed = bed * np.array(duck_curve(vox, sr=sr), np.float32)
                mix += bed
        return mix, vox, spk

    def finish(self, total, black_cut=None, outro0=None, scenes=None, mutes=(), lufs=-16, tp=-2, lipsync_modes=("D", "C"),
               visemes=True):
        """Mix down -> <part>_raw.wav -> loudnorm -> part<N>_audio.wav (TIKTOK: _tiktok, NOMUSIC: _nomusic),
        env_<part>.json (frames, scenes, mutes, per-voice lip-sync envelopes, word-timed lines, visemes.py mouth codes that
        rig2.lipsync reads; visemes=False keeps a delivered part's old loudness flap) and captions_<part>.ass."""
        sr, n = self.sr, self.part.lstrip("p"); nf = int(round(total * self.fps)) + 1
        mix, vox, spk = self.build(total)
        mix = mix[:int(total * sr)]; mix = mix / max(np.abs(mix).max(), 1e-6) * 0.92
        raw = self.out + "part%s_raw.wav" % n; write_wav(raw, mix, sr)
        loudnorm(raw, self.out + "part%s_%s.wav" % (n, "nomusic" if self.nomusic else "tiktok" if self.tiktok else "audio"), lufs, tp, sr)
        envs = {k: envelope(v, nf, self.fps, sr) for k, v in spk.items()}
        caps = [{"who": who, "text": o["text"], "style": st, "mode": mode, "fx": fx, "t0": d, "t1": d + len(sig) / sr,
                 "words": [(w, d + (s - o["a"]), d + (min(e, o["b"]) - o["a"])) for w, s, e in o["words"]]}
                for who, o, d, mode, st, fx, sig in self.placed]
        if scenes is None:
            sc = self.scenes; scenes = [(s, a, (sc[i + 1][1] if i + 1 < len(sc) else total)) for i, (s, a) in enumerate(sc)]
        json.dump({"fps": self.fps, "total": total, "nf": nf, "outro0": outro0, "black_cut": black_cut, "scenes": scenes,
                   "mutes": mutes, "rms": {k: v[0] for k, v in envs.items()}, "cen": {k: v[1] for k, v in envs.items()},
                   "lines": caps, "lipsync_modes": list(lipsync_modes),
                   **(viseme_tracks([(who, o["text"], d, sig) for who, o, d, mode, st, fx, sig in self.placed], nf, self.fps, sr)
                      if visemes else {})}, open(self.out + "env_%s.json" % self.part, "w"))
        write_ass(caps, self.out + "captions_%s.ass" % self.part, black_cut)
        print("frames", nf, "total", total, "black", black_cut, "lines", len(caps))
        for s, a, b in scenes: print(f"  {a:6.2f}-{b:6.2f} {s}")
        return caps
