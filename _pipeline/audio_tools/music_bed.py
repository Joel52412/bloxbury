# music_bed.py - looped background music bed for a part's mix.
# Joel (22 Nov): Part 2 uses ONLY the instrumental of "Numbers" (TEMPOREX), looped for the whole part at ~40% volume.
# The instrumental was split from backgorund music/Numbers.mp3 with UVR-MDX-NET-Inst_HQ_3 (vocals removed) and
# Joel (22 Nov 12:23): loop ONLY the intro, without the whistle (the pitch-slide whistle at ~19.8-20.6 s is not in it).
# The loop is the intro's 4 bars (0.07-10.28 s, ~94 BPM). Bar 5 has the same chords as bar 1, so bar 4 -> bar 1 is the
# song's own chord change. Bar 4's ring-out fades under bar 1's first hit over 150 ms, and a slow, circular level
# rider (0.15 s window, only lifts dips, max +12 dB) fills the thin end of bar 4, so every 0.25 s stays within about -15 to -25 dB.
# Stored as FLAC (Numbers_instrumental_loop.flac, 10.21 s) because MP3 padding would put tiny gaps between repeats.
#
# Usage inside a prep_pN.py, after voice + SFX are put into `mix` and BEFORE the peak normalise:
#     from music_bed import music_bed
#     mix += music_bed(REPO, TOTAL, SR, len(mix))
# Volume is a straight gain on the source track (0.40 = 40%), the same as a volume slider in an editor.
# It goes into `mix` only, never `vox`, so lip-sync envelopes are unaffected.
import numpy as np, subprocess

PART_MUSIC = {
    2: {"file": "backgorund music/Numbers_instrumental_loop.flac", "vol": 0.40, "fade_in": 0.0, "fade_out": 1.0},
}


def music_bed(repo, total, sr, n=None, part=2, vol=None, fade_in=None, fade_out=None, start=0.0):
    cfg = PART_MUSIC[part]
    vol = cfg["vol"] if vol is None else vol
    fi = cfg["fade_in"] if fade_in is None else fade_in
    fo = cfg["fade_out"] if fade_out is None else fade_out
    cmd = ["ffmpeg", "-loglevel", "error", "-i", repo + "/" + cfg["file"], "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    loop = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
    n = n or int(total * sr)
    reps = int(np.ceil(n / len(loop))) + 1
    bed = np.tile(loop, reps)[int(start * sr):][:n] * vol        # loop file is seamless, so plain tiling is clean
    end = int(total * sr)
    if fi: k = int(fi * sr); bed[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * sr); bed[max(0, end - k):end] *= np.linspace(1, 0, min(k, end))
    bed[end:] = 0
    return bed.astype(np.float32)
