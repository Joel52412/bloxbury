"""Shared caption writer (Joel 22 Nov 21:26, from the viral plane video).
Big bold yellow, ONE word at a time, popped in, thick black outline, lower-middle (y=66%: under faces, which sit in the
upper third). Red = monster/fake lines (style 'r'), white = off-screen voices (mode 'O'). Font ships in assets/fonts.
Usage: write_ass(caps, path, black_cut=None)   caps = [{"text", "style", "mode", "words": [(w, t0, t1), ...]}, ...]
"""
FONT, SIZE, Y = "Poppins", 104, 1270
COL = {"W": "&H0000E6FF", "R": "&H003C3CFF", "I": "&H00FFFFFF"}      # ASS colours are &HBBGGRR


def _ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(caps, path, black_cut=None, hold=0.6):
    head = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
            "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
    for k, c in COL.items():
        head.append(f"Style: {k},{FONT},{SIZE},{c},{c},&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,9,4,5,60,60,0,1")
    head += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    words = []                                       # flatten to (word, t0, style)
    for c in caps:
        sty = "R" if c.get("style") == "r" else ("I" if c.get("mode") == "O" else "W")
        toks = c["text"].split(); ws = c["words"]
        if not ws: continue
        tt = [ws[min(j, len(ws) - 1)][1] for j in range(len(toks))]
        for j, tok in enumerate(toks):
            words.append((tok.strip('"'), tt[j], ws[min(j, len(ws) - 1)][2], sty))
    ev = []
    for i, (w, a, e, sty) in enumerate(words):
        b = min(e + hold, words[i + 1][1]) if i + 1 < len(words) else e + hold
        b = max(b, a + 0.12)
        if black_cut and a < black_cut <= b: b = black_cut
        pop = "{\\pos(540,%d)\\fscx118\\fscy118\\t(0,90,\\fscx100\\fscy100)}" % Y
        ev.append(f"Dialogue: 0,{_ts(a - 0.03)},{_ts(b)},{sty},,0,0,0,,{pop}{w}")
    open(path, "w").write("\n".join(head + ev) + "\n")
    return len(ev)
