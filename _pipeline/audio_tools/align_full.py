# align_full.py - word timings for a voice file against its script text (captions, lip-sync, line splits).
# faster-whisper (word_timestamps) transcribes, then the transcript is mapped onto the SCRIPT words (difflib):
# matched words take Whisper's times, misheard runs are spread over their span by letter count, missing words are
# interpolated between neighbours; starts/ends sitting in silence snap to the voice (snap_to_voice). Output tokens are always exactly norm(script), so split_lines.py's checks hold.
# Falls back to pocketsphinx forced alignment if faster-whisper or its model can't load (ALIGN=sphinx forces it).
# Env: WHISPER_MODEL (default small.en; medium.en = better, ~3x slower), WHISPER_DEVICE (cpu | cuda).
# Usage: python3 align_full.py <voice.mp3> <script.txt> <words.json>      -> [[word, start_s, end_s], ...]
import difflib, json, os, re, subprocess, sys


def norm(t): return re.sub(r"[^a-z' ]", " ", t.lower().replace("…", " ")).split()


def _spread(words, a, b):
    """Place words evenly by letter count over [a, b]."""
    tot = sum(len(w) for w in words) or 1; t = a; out = []
    for w in words:
        dt = (b - a) * len(w) / tot; out.append((t, t + dt)); t += dt
    return out


def map_to_script(ref, hyp):
    """ref: script tokens. hyp: [(token, start, end)] from the recogniser. -> [(ref token, start, end)]."""
    T = [None] * len(ref)
    sm = difflib.SequenceMatcher(a=ref, b=[h[0] for h in hyp], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): T[i1 + k] = (hyp[j1 + k][1], hyp[j1 + k][2])
        elif tag == "replace" and i2 - i1 == j2 - j1:             # misheard word for word ("mom" for "mum")
            for k in range(i2 - i1): T[i1 + k] = (hyp[j1 + k][1], hyp[j1 + k][2])
        elif tag == "replace":                                    # misheard run: keep its time span, spread the words
            for k, se in enumerate(_spread(ref[i1:i2], hyp[j1][1], hyp[j2 - 1][2])): T[i1 + k] = se
    i = 0
    while i < len(ref):                                           # words the recogniser skipped: interpolate
        if T[i] is not None: i += 1; continue
        j = i
        while j < len(ref) and T[j] is None: j += 1
        a = T[i - 1][1] if i else 0.0
        b = T[j][0] if j < len(ref) else a + 0.3 * (j - i)
        for k, se in enumerate(_spread(ref[i:j], a, max(b, a + 0.04 * (j - i)))): T[i + k] = se
        i = j
    out, last = [], 0.0
    for w, (s, e) in zip(ref, T):                                 # monotonic, every word >= 30 ms
        s = max(s, last); e = max(e, s + 0.03); last = e
        out.append((w, round(s, 3), round(e, 3)))
    return out


def _whisper(path, text):
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")              # plain https download (the Xet CAS host is often blocked)
    from faster_whisper import WhisperModel
    m = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device=os.environ.get("WHISPER_DEVICE", "cpu"),
                     compute_type="int8")
    import numpy as np                                            # decode with ffmpeg (PyAV versions break faster-whisper)
    pcm = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le",
                                        "-"], capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(pcm, language="en", word_timestamps=True, beam_size=5, vad_filter=False,
                           condition_on_previous_text=False, initial_prompt=" ".join(text.split()[:150]))
    hyp = []
    for s in segs:
        for w in s.words:
            toks = norm(w.word)
            for tok, (a, b) in zip(toks, _spread(toks, w.start, w.end)): hyp.append((tok, a, b))
    return hyp


def snap_to_voice(path, words, look=0.4, gap=4):
    """Whisper smears word edges across pauses: a start can sit in the silence (or in the previous word's tail) before
    the word, an end in the silence after it. If the first `look` s of a word hold a pause (>= `gap` x 10 ms below the
    voice threshold), the word starts after that pause; if its last `look` s hold one, it ends at that pause."""
    import numpy as np
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le",
                                      "-"], capture_output=True, check=True).stdout, np.int16) / 32768
    n = len(x) // 160; e = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
    quiet = e < max(np.percentile(e, 10) + 18, e.max() - 42)
    def runs(a, b):                                               # silent runs [i, j) inside frames a..b
        out, k = [], a
        while k < b:
            if quiet[k]:
                m = k
                while m < b and quiet[m]: m += 1
                if m - k >= gap or k == a or m == b: out.append((k, m))
                k = m
            else: k += 1
        return out
    res = []
    for w, s, t in words:
        a, b = int(s * 100), min(int(t * 100), n)
        r = [q for q in runs(a, min(b, a + int(look * 100))) if q[1] < b]
        if r: a = r[-1][1]                                        # start after the last pause near the start
        r = [q for q in runs(max(a + 3, b - int(look * 100)), b)]
        if r: b = max(a + 3, r[0][0] + 2)                         # end at the first pause near the end (+20 ms tail)
        res.append((w, round(a / 100, 3), round(b / 100, 3)))
    return res


def _sphinx(path, text):
    from pocketsphinx import Decoder
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    d = Decoder(samprate=16000, bestpath=False)
    d.add_word("bloxbury", "B L AA K S B ER IY", True); d.add_word("hummed", "HH AH M D", True)
    d.set_align_text(" ".join(norm(text))); d.start_utt(); d.process_raw(raw, full_utt=True); d.end_utt()
    return [(re.sub(r"\(\d\)", "", x.word), x.start_frame / 100, (x.end_frame + 1) / 100) for x in d.seg()
            if x.word not in ("<s>", "</s>", "<sil>")]


def align(path, text):
    ref = norm(text); hyp = None
    if os.environ.get("ALIGN", "whisper") != "sphinx":
        try: hyp = snap_to_voice(path, _whisper(path, text))
        except Exception as ex: print("faster-whisper unavailable (%s): pocketsphinx fallback" % str(ex)[:120], file=sys.stderr)
    if hyp is None: hyp = _sphinx(path, text)
    out = map_to_script(ref, hyp)
    hit = sum(m.size for m in difflib.SequenceMatcher(a=ref, b=[h[0] for h in hyp], autojunk=False).get_matching_blocks())
    print("matched %d/%d script words" % (hit, len(ref)), file=sys.stderr)
    return out


if __name__ == "__main__":
    out = align(sys.argv[1], open(sys.argv[2]).read()); json.dump(out, open(sys.argv[3], "w"))
    print(" ".join(f"{w}@{s}" for w, s, e in out))
