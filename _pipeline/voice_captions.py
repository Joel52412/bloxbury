#!/usr/bin/env python3
"""
voice_captions.py: finish a story with one command (ported from the standalone Roblox Shorts Maker).
  script.txt -> ElevenLabs voices (cached) -> rendered shots IN ORDER, each fitted to its line
  -> one-word pop captions (studio style) -> 1080x1920 mp4 in <story>/output/

Usage (from the studio root):
  python _pipeline/voice_captions.py stories/<story>              real voices
  python _pipeline/voice_captions.py stories/<story> --no-tts     free silent timing preview
  python _pipeline/voice_captions.py stories/<story> --random     old mode: random cuts from assets/clips

Story folder:
  script.txt   one line = one beat:  speaker: text      (speaker picks a voice in config.json; default narrator)
               [shot: 03_kitchen] text   -> use the shot whose filename contains '03_kitchen'
               [shot: a, b] text         -> the line plays shots a then b, its time split evenly
               *word*  -> red caption (monster/fake);  # comment lines ignored
  shots/       rendered shots (mp4/mov/...), sorted by filename: shot 1 -> line 1, shot 2 -> line 2 ...
               Each shot plays from its first frame; trimmed if longer than the line, last frame held if shorter.
  output/ .cache/   made here (gitignored). .cache keeps fitted shots so only changed ones re-encode.

Needs Python 3.9+ and ffmpeg. Key: ELEVENLABS_API_KEY env var or config.json in the studio root (gitignored).
"""
import argparse, base64, hashlib, json, os, random, re, shutil, subprocess, sys, tempfile, urllib.request, urllib.error

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # studio root
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac")
W, H, FPS = 1080, 1920, 24  # studio standard: 9:16, 24 fps

STYLE_DEFAULTS = {  # CLAUDE.md captions: bold yellow Poppins, one word at a time with a pop, y=66%
    "font": "Poppins", "font_size": 110, "outline": 7, "caption_y": 0.66,
    "caption_colour": "&H00D7FF&", "highlight_colour": "&H3B3BFF&",  # ASS &HBBGGRR: yellow, red
    "words_per_caption": 1, "auto_highlight": 0.0,
}

# --------------------------------------------------------------------------- helpers

def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-2000:])
    return r.stdout

def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path])
    return float(out.strip())

def load_config():
    cfg = {}
    p = os.path.join(HERE, "config.json")
    if not os.path.exists(p):
        p = os.path.join(HERE, "config.example.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            cfg = json.load(f)
    key = os.environ.get("ELEVENLABS_API_KEY") or cfg.get("elevenlabs_api_key", "")
    cfg["elevenlabs_api_key"] = "" if key.startswith("PASTE") else key
    cfg["voices"] = {k: v for k, v in cfg.get("voices", {}).items() if v and not v.startswith("PASTE")}
    return cfg

def files_in(folder, exts):
    if not folder or not os.path.isdir(folder):
        return []
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts))

# --------------------------------------------------------------------------- script parsing

def parse_script(path):
    beats = []
    with open(path, encoding="utf-8-sig") as f:  # -sig: Notepad/PowerShell add a BOM
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            want = []
            m = re.match(r"^\[(?:shot|clip)s?:\s*(.+?)\]\s*(.*)$", line, re.I)
            if m:
                want = [w.strip().lower() for w in m.group(1).split(",") if w.strip()]
                line = m.group(2).strip()
                if not line:
                    continue
            speaker = "narrator"
            m = re.match(r"^([A-Za-z0-9_ ]{1,20}):\s+(.+)$", line)
            if m:
                speaker, line = m.group(1).strip().lower(), m.group(2).strip()
            beats.append({"speaker": speaker, "text": line, "want": want})
    if not beats:
        sys.exit(f"No lines found in {path}")
    return beats

# --------------------------------------------------------------------------- TTS

def tts_elevenlabs(text, voice_id, cfg, out_mp3):
    """Returns list of (word, start, end) from ElevenLabs character timestamps. Cached in .tts_cache/."""
    spoken = text.replace("*", "")
    model = cfg.get("model_id", "eleven_multilingual_v2")
    settings = cfg.get("voice_settings", {"stability": 0.4, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True})
    cache_dir = os.path.join(HERE, ".tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    h = hashlib.sha1(json.dumps([spoken, voice_id, model, settings]).encode()).hexdigest()[:16]
    cache_json = os.path.join(cache_dir, h + ".json")
    if os.path.exists(cache_json):
        with open(cache_json, encoding="utf-8") as f:
            data = json.load(f)
    else:
        if not cfg["elevenlabs_api_key"]:
            sys.exit("No ElevenLabs key. Set ELEVENLABS_API_KEY or put it in config.json (or use --no-tts).")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128"
        body = json.dumps({"text": spoken, "model_id": model, "voice_settings": settings}).encode()
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "xi-api-key": cfg["elevenlabs_api_key"], "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs error {e.code}: {e.read().decode(errors='ignore')[:500]}")
        with open(cache_json, "w", encoding="utf-8") as f:
            json.dump(data, f)
    with open(out_mp3, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))
    al = data.get("normalized_alignment") or data["alignment"]
    return words_from_alignment(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])

def words_from_alignment(chars, starts, ends):
    words, cur, s, e = [], "", None, None
    for c, cs, ce in zip(chars, starts, ends):
        if c.isspace():
            if cur:
                words.append((cur, s, e))
            cur, s = "", None
            continue
        if s is None:
            s = cs
        cur += c
        e = ce
    if cur:
        words.append((cur, s, e))
    return words

def tts_silent(text, out_wav):
    """Preview mode: silent track with estimated word timings (~2.9 words/sec)."""
    ws = text.replace("*", "").split()
    t, words = 0.05, []
    for w in ws:
        d = 0.18 + 0.045 * len(w)
        words.append((w, t, t + d))
        t += d + 0.04
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{t + 0.05:.3f}", out_wav])
    return words

# --------------------------------------------------------------------------- captions (ASS)

def ass_time(t):
    t = max(0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"

def build_ass(caption_words, path, style):
    size, ypos = style["font_size"], int(H * style["caption_y"])
    base, hl = style["caption_colour"], style["highlight_colour"]
    prim = "&H00" + base.strip("&H")[-6:] if base.startswith("&H") else "&H00FFFFFF"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Cap,{style['font']},{size},{prim},{prim},&H00000000,&H96000000,1,0,0,0,100,100,1,0,1,{style['outline']},4,5,40,40,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    rnd = random.Random(7)  # fixed so captions don't change between renders
    n = style["words_per_caption"]
    groups = [caption_words[i:i + n] for i in range(0, len(caption_words), n)]
    for gi, g in enumerate(groups):
        start = g[0]["start"]
        end = groups[gi + 1][0]["start"] if gi + 1 < len(groups) and groups[gi + 1][0]["start"] - g[-1]["end"] < 0.6 else g[-1]["end"] + 0.25
        parts = []
        for j, w in enumerate(g):
            word = re.sub(r"[{}\\]", "", w["text"].upper())
            want = w["hl"] or (style["auto_highlight"] and j == len(g) - 1 and rnd.random() < style["auto_highlight"])
            parts.append("{\\c" + hl + "}" + word + "{\\c" + base + "}" if want else word)
        pop = "{\\pos(540,%d)\\fscx70\\fscy70\\t(0,70,\\fscx112\\fscy112)\\t(70,140,\\fscx100\\fscy100)}" % ypos
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def mark_highlights(raw_text, words):
    """Only *starred* words are highlighted (red = monster/fake, per CLAUDE.md)."""
    tokens = raw_text.split()
    out = []
    for i, (w, s, e) in enumerate(words):
        tok = tokens[i] if i < len(tokens) else w
        out.append({"text": w.replace("*", ""), "start": s, "end": e, "hl": "*" in tok})
    return out

# --------------------------------------------------------------------------- video

def fit_shot(src, start, seg_dur, out, cache_dir):
    """Cut seg_dur seconds from `start`, scaled/cropped to 1080x1920 @24fps; holds the last frame if the
    source is too short. Cached by source file + timing, so unchanged shots are never re-encoded."""
    st = os.stat(src)
    key = hashlib.sha1(f"{os.path.abspath(src)}|{st.st_size}|{st.st_mtime}|{start:.3f}|{seg_dur:.3f}|{W}x{H}@{FPS}".encode()).hexdigest()[:16]
    cached = os.path.join(cache_dir, key + ".mp4")
    if os.path.exists(cached):
        shutil.copyfile(cached, out)
        return False
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
          f"tpad=stop_mode=clone:stop_duration={seg_dur:.3f}")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", src, "-t", f"{seg_dur:.3f}",
         "-vf", vf, "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p", cached])
    shutil.copyfile(cached, out)
    return True

def plan_ordered(beats, shot_files):
    """Shot i -> line i (filename order). [shot: x] tags override; a line can take several shots."""
    plan, nxt = [], 0
    for i, b in enumerate(beats):
        picks = []
        for w in b["want"]:
            m = [s for s in shot_files if w in os.path.basename(s).lower()]
            if not m:
                sys.exit(f"Line {i + 1}: no shot in shots/ matches '{w}'")
            picks.append(m[0])
            nxt = shot_files.index(m[0]) + 1
        if not picks:
            if nxt >= len(shot_files):
                sys.exit(f"Line {i + 1} has no shot: shots/ has {len(shot_files)} files for {len(beats)} lines. "
                         "Add shots, tag lines with [shot: name], or use --random.")
            picks.append(shot_files[nxt])
            nxt += 1
        plan.append(picks)
    unused = [os.path.basename(s) for s in shot_files if not any(s in p for p in plan)]
    if unused:
        print(f"  ! unused shots: {', '.join(unused)}")
    return plan

def pick_random(clips, state, rng):
    if not state["bag"]:
        state["bag"] = clips[:]
        rng.shuffle(state["bag"])
    return state["bag"].pop()

# --------------------------------------------------------------------------- main render

def render(story_dir, args, cfg):
    name = os.path.basename(os.path.normpath(story_dir))
    beats = parse_script(os.path.join(story_dir, "script.txt"))
    shot_files = files_in(os.path.join(story_dir, "shots"), VIDEO_EXT)
    random_mode = args.random or not shot_files
    clips = files_in(args.clips, VIDEO_EXT) if random_mode else shot_files
    if random_mode and not args.random:
        print(f"  ! {story_dir}/shots is empty: falling back to random cuts from {args.clips}")
    if not clips:
        sys.exit(f"Put rendered shots in {story_dir}/shots (or clips in {args.clips} for --random)")
    plan = None if random_mode else plan_ordered(beats, shot_files)
    cache_dir = os.path.join(story_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    rng = random.Random(args.seed if args.seed is not None else name)
    voices = cfg.get("voices", {})
    style = {k: cfg.get(k, v) for k, v in STYLE_DEFAULTS.items()}
    if args.font:
        style["font"] = args.font
    if args.words:
        style["words_per_caption"] = args.words
    gap = cfg.get("gap_between_lines", 0.12)
    max_shot = cfg.get("max_shot_seconds", 2.6)

    work = tempfile.mkdtemp(prefix="vc_")
    print(f"\n== {name}: {len(beats)} lines, {'random clips' if random_mode else f'{len(shot_files)} shots in order'}")
    t, all_words, audio_parts, segs = 0.0, [], [], []
    for i, b in enumerate(beats):
        voice = voices.get(b["speaker"]) or voices.get("narrator")
        if args.no_tts:
            a = os.path.join(work, f"v{i}.wav")
            words = tts_silent(b["text"], a)
        else:
            if not voice:
                sys.exit(f"No voice id for speaker '{b['speaker']}' (or 'narrator') in config.json")
            a = os.path.join(work, f"v{i}.mp3")
            words = tts_elevenlabs(b["text"], voice, cfg, a)
        d = duration(a) + gap
        padded = os.path.join(work, f"p{i}.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", a, "-af", f"apad=whole_dur={d:.3f}", "-t", f"{d:.3f}",
             "-ar", "44100", "-ac", "2", padded])
        audio_parts.append(padded)
        for cw in mark_highlights(b["text"], words):
            cw["start"] += t
            cw["end"] += t
            all_words.append(cw)
        if random_mode:  # long lines -> several quick random cuts
            n = max(1, round(d / max_shot))
            segs += [{"dur": d / n, "src": None} for _ in range(n)]
            label = "random"
        else:
            segs += [{"dur": d / len(plan[i]), "src": s} for s in plan[i]]
            label = ", ".join(os.path.basename(s) for s in plan[i])
        print(f"  [{i + 1}/{len(beats)}] {b['speaker']}: {b['text'][:44]}  ({d:.1f}s) <- {label}")
        t += d

    with open(os.path.join(work, "a.txt"), "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in audio_parts)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "a.txt", "-c", "pcm_s16le", "voice.wav"], cwd=work)

    print("  fitting shots...")
    durs, state, seg_files, acc, fresh, held = {}, {"bag": []}, [], 0, 0, []
    for j, s in enumerate(segs):
        frames_end = round((acc + s["dur"]) * FPS)
        seg_d = (frames_end - round(acc * FPS)) / FPS  # frame-exact so picture stays on the voice
        acc += s["dur"]
        src = s["src"] or pick_random(clips, state, rng)
        if src not in durs:
            durs[src] = duration(src)
        if s["src"]:
            start = 0.0
            if durs[src] < seg_d - 1.0 / FPS:
                held.append(f"{os.path.basename(src)} +{seg_d - durs[src]:.1f}s")
        else:
            start = rng.uniform(0, max(0, durs[src] - seg_d - 0.1))
        out = os.path.join(work, f"s{j}.mp4")
        fresh += fit_shot(src, start, seg_d, out, cache_dir)
        seg_files.append(out)
    print(f"  {fresh} shots encoded, {len(segs) - fresh} reused from cache")
    if held:
        print(f"  last frame held: {'; '.join(held)}")
    with open(os.path.join(work, "v.txt"), "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in seg_files)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "v.txt", "-c", "copy", "video.mp4"], cwd=work)

    build_ass(all_words, os.path.join(work, "captions.ass"), style)
    fontsdir = os.path.join(HERE, "assets", "fonts")
    sub = "subtitles=captions.ass"
    if files_in(fontsdir, (".ttf", ".otf")):
        shutil.copytree(fontsdir, os.path.join(work, "fonts"), dirs_exist_ok=True)
        sub += ":fontsdir=fonts"

    final = os.path.abspath(os.path.join(args.out or os.path.join(story_dir, "output"), name + ".mp4"))
    os.makedirs(os.path.dirname(final), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "video.mp4", "-i", "voice.wav"]
    music = args.music if args.music and os.path.isfile(args.music) else None
    if music:  # studio: music only when named (assets/music holds copyrighted tracks)
        vol = cfg.get("music_volume", 0.1)
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[0:v]{sub}[v];[2:a]volume={vol}[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", f"[0:v]{sub}[v]", "-map", "[v]", "-map", "1:a"]
    cmd += ["-t", f"{t:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", args.preset, "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final]
    print("  rendering final video...")
    run(cmd, cwd=work)
    shutil.rmtree(work, ignore_errors=True)
    print(f"  done -> {final}  ({t:.1f}s)")
    return final


def main():
    ap = argparse.ArgumentParser(description="Voice + captions final step: script.txt + rendered shots -> 1080x1920 mp4.")
    ap.add_argument("story", help="a story folder (with script.txt), or a folder of stories to do all")
    ap.add_argument("--random", action="store_true", help="fallback: random cuts from --clips instead of shots/ in order")
    ap.add_argument("--clips", default=os.path.join(HERE, "assets", "clips"), help="clip library for --random")
    ap.add_argument("--music", help="a music file to mix under the voices (default: none)")
    ap.add_argument("--out", help="output folder (default: <story>/output)")
    ap.add_argument("--no-tts", action="store_true", help="silent preview, no ElevenLabs credits used")
    ap.add_argument("--words", type=int, help="words per caption (default 1)")
    ap.add_argument("--font", help="caption font (default Poppins, from assets/fonts)")
    ap.add_argument("--preset", default="veryfast", help="x264 preset: ultrafast = quickest, slow = smallest")
    ap.add_argument("--seed", type=int, help="fix the random clip choice (--random only)")
    args = ap.parse_args()
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found. Install it (winget install Gyan.FFmpeg) and reopen the terminal.")
    cfg = load_config()
    d = args.story
    if os.path.isfile(os.path.join(d, "script.txt")):
        stories = [d]
    else:
        stories = [os.path.join(d, x) for x in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, x, "script.txt"))]
    if not stories:
        sys.exit(f"No story folders with script.txt found in {d}")
    for s in stories:
        render(s, args, cfg)


if __name__ == "__main__":
    main()
