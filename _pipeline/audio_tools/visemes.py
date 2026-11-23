# visemes.py - mouth shapes from the actual speech (story-agnostic). Same idea as Rhubarb Lip Sync, built on the
# pocketsphinx we already use for word timing (no extra binary): force-align each line's text to its audio at PHONE level,
# map phones to mouth codes, write one code per video frame.  rig2.lipsync() reads them (ENV["vis_all"] / ENV["vis"][who]).
#   codes: X rest  M closed (M B P)  T teeth-on-lip (F V)  U pucker (OO W R SH CH)  O round (AW OH)
#          A open (AH AA AY AE)  E spread (EE EH AY)  H half-open (every other consonant)
# Usage in a prep script:  from visemes import viseme_tracks
#   json[...].update(viseme_tracks([(who, text, t0, sig48k), ...], N, FPS, SR))
# CLI check: python3 visemes.py line.wav "the line text"   -> prints the per-frame codes at 24 fps
import re, subprocess, sys
import numpy as np

PH = {}
for _c, _ps in (("M", "M B P"), ("T", "F V"), ("U", "UW UH W R ER SH ZH CH JH"), ("O", "AO OW OY AW"),
                ("A", "AA AH AY AE"), ("E", "EH EY IY IH"), ("X", "SIL")):
    for _p in _ps.split(): PH[_p] = _c
WEIGHT = {"M": 2.6, "T": 1.6, "U": 1.2, "O": 1.25, "A": 1.25, "E": 1.2, "H": 1.0, "X": 0.6}   # closures must survive 24 fps
PAD, CMAX = 0.3, 0.12  # s of silence padded around each line; longest a consonant next to a vowel may last
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
GATE = 0.06            # line-end frames quieter than this x line peak are rest (aligners stretch the first/last phone over silence)


def _norm(t): return re.sub(r"[^a-z' ]", " ", t.lower().replace("…", " ")).split()


def _to16k(sig, sr):
    if sr == 16000: return sig
    if sr % 16000 == 0:
        k = sr // 16000; n = len(sig) // k
        return sig[:n * k].reshape(n, k).mean(1)          # box filter + decimate: fine for an aligner
    x = np.arange(0, len(sig), sr / 16000.0)
    return np.interp(x, np.arange(len(sig)), sig)


def phones(sig, sr, text):
    """[(phone, t0, t1)] seconds from the start of sig. Empty if the aligner fails."""
    from pocketsphinx import Decoder
    raw = (np.clip(_to16k(np.asarray(sig, np.float32), sr), -1, 1) * 32767).astype(np.int16).tobytes()
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    words = []
    for w in _norm(text):
        if d.lookup_word(w) is None:                        # unknown word: spell it with letter-ish phones (rare names)
            d.add_word(w, " ".join(_guess(w)), True)
        words.append(w)
    if not words: return []
    pad = b"\0\0" * int(PAD * 16000)                       # silence around the line: the aligner stops stretching phone 1
    try:
        d.set_align_text(" ".join(words)); d.start_utt(); d.process_raw(pad + raw + pad, full_utt=True); d.end_utt()
        d.set_alignment(); d.start_utt(); d.process_raw(pad + raw + pad, full_utt=True); d.end_utt()
        al = [[[p.name, p.start / 100.0 - PAD, (p.start + p.duration) / 100.0 - PAD] for p in w] for w in d.get_alignment()]
    except Exception:
        return []
    for w in al:                                            # vowels the aligner squeezed get time back from long consonants
        for i in range(len(w) - 1):
            a, b = w[i], w[i + 1]
            if a[0] not in VOWELS and b[0] in VOWELS and a[2] - a[1] > CMAX: a[2] = b[1] = a[1] + CMAX
            if a[0] in VOWELS and b[0] not in VOWELS and b[0] != "SIL" and b[2] - b[1] > CMAX: a[2] = b[1] = b[2] - CMAX
    return [tuple(p) for w in al for p in w]


_LET = {"a": "AE", "b": "B", "c": "K", "d": "D", "e": "EH", "f": "F", "g": "G", "h": "HH", "i": "IH", "j": "JH", "k": "K",
        "l": "L", "m": "M", "n": "N", "o": "AA", "p": "P", "q": "K", "r": "R", "s": "S", "t": "T", "u": "AH", "v": "V",
        "w": "W", "x": "K", "y": "Y", "z": "Z"}


def _guess(w):
    out = [_LET[c] for c in w if c in _LET]
    return out or ["AH"]


def frame_codes(ph, nfr, fps, start=0.0):
    """One code per video frame (frame i covers [start + i/fps, start + (i+1)/fps)), best weighted overlap."""
    out = []
    for i in range(nfr):
        a = start + i / fps; b = a + 1 / fps; best, score = "X", 0.0
        for p, s, e in ph:
            ov = min(b, e) - max(a, s)
            if ov <= 0: continue
            c = PH.get(p, "H"); sc = ov * WEIGHT[c]
            if sc > score: best, score = c, sc
        out.append(best)
    return out


def viseme_tracks(lines, nf, fps, sr):
    """lines: [(who, text, t0_seconds, signal)]. Returns {"vis": {who: codes}, "vis_all": codes} (one char per frame,
    index = frame - 1 like ENV rms). Frames outside any line are X."""
    tracks, merged = {}, ["X"] * nf
    for who, text, t0, sig in lines:
        tr = tracks.setdefault(who, ["X"] * nf)
        ph = phones(sig, sr, text)
        f0 = int(t0 * fps); f1 = min(nf, int((t0 + len(sig) / sr) * fps) + 1)
        if not ph: print("visemes: aligner failed on", repr(text)); continue
        codes = frame_codes(ph, f1 - f0, fps, start=f0 / fps - t0)
        # gate the stretched leading / trailing phone by loudness
        k = sr // fps; lv = []
        for i in range(f1 - f0):
            a = int((f0 + i) / fps * sr - t0 * sr); seg = sig[max(0, a):max(0, a + k)]
            lv.append(float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0)
        pk = max(lv) or 1.0; loud = [v > GATE * pk for v in lv]
        if any(loud):
            first = loud.index(True); last = len(loud) - 1 - loud[::-1].index(True)
            for i in range(len(codes)):
                if i < first or i > last: codes[i] = "X"
        for i, c in enumerate(codes):
            if c != "X": tr[f0 + i] = c; merged[f0 + i] = c
    return {"vis": {w: "".join(t) for w, t in tracks.items()}, "vis_all": "".join(merged)}


if __name__ == "__main__":
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", sys.argv[1], "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    s = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    ph = phones(s, 48000, sys.argv[2])
    print(" ".join(f"{p}@{a:.2f}" for p, a, b in ph))
    print(viseme_tracks([("x", sys.argv[2], 0.0, s)], int(len(s) / 48000 * 24) + 2, 24, 48000)["vis_all"])
