# music_bed.py - looped background music bed for a part's mix.
# Joel (22 Nov): Part 2 uses ONLY the instrumental of "Numbers" (TEMPOREX), looped for the whole part at ~35% volume (was 40%).
# The instrumental was split from assets/music/Numbers.mp3 with UVR-MDX-NET-Inst_HQ_3 (vocals removed) and
# Joel (22 Nov 12:23): loop ONLY the intro, without the whistle (the pitch-slide whistle at ~19.8-20.6 s is not in it).
# The loop is the intro's 4 bars (0.07-10.28 s, ~94 BPM). Bar 5 has the same chords as bar 1, so bar 4 -> bar 1 is the
# song's own chord change. Bar 4's ring-out fades under bar 1's first hit over 150 ms, and a slow, circular level
# rider (0.15 s window, only lifts dips, max +12 dB) fills the thin end of bar 4, so every 0.25 s stays within about -15 to -25 dB.
# Stored as FLAC (Numbers_instrumental_loop.flac, 10.21 s) because MP3 padding would put tiny gaps between repeats.
#
# Usage inside a prep_pN.py, after voice + SFX are put into `mix` and BEFORE the peak normalise:
#     from music_bed import music_bed
#     mix += music_bed(REPO, TOTAL, SR, len(mix))
# Volume is a straight gain on the source track (0.35 = 35%), the same as a volume slider in an editor.
# It goes into `mix` only, never `vox`, so lip-sync envelopes are unaffected.
import numpy as np, subprocess

PART_MUSIC = {
    2: {"file": "assets/music/Numbers_instrumental_loop.flac", "vol": 0.35, "fade_in": 0.0, "fade_out": 1.0},
    # Part 3 (Joel 21:51): piano cover "numbers - temporex piano" (70.45 s, not a loop). pause=True: the song PAUSES
    # during mutes and carries on where it stopped, so 0-28 s + 44-73 s + outro use ~65 s of it and it never repeats.
    3: {"file": "assets/music/Numbers_piano.mp3", "vol": 0.20, "fade_in": 0.0, "fade_out": 1.0, "pause": True},
}


def music_bed(repo, total, sr, n=None, part=2, vol=None, fade_in=None, fade_out=None, start=0.0, mutes=()):
    # mutes: [(t0, t1), ...] seconds where the music drops out for a scene (Joel 12:38: cut it whenever it helps).
    # Cuts are hard-ish (40 ms) going out, so the silence lands, and fade back in over 0.6 s.
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
    if cfg.get("pause"):                                          # song pauses through mutes, resumes where it stopped
        song = loop[int(start * sr):] * vol; bed = np.zeros(n, np.float32); pos = 0; t = 0
        for a, b in list(mutes) + [(total, total)]:
            a, b = int(a * sr), int(b * sr); k = min(a - t, len(song) - pos)
            if k > 0:
                seg = song[pos:pos + k].copy(); ki = min(int(0.6 * sr), k)
                if t > 0: seg[:ki] *= np.linspace(0, 1, ki)
                ko = min(int(0.04 * sr), k)
                if a < end: seg[-ko:] *= np.linspace(1, 0, ko)
                bed[t:t + k] = seg; pos += k
            t = b
        if fo: k = int(fo * sr); bed[max(0, end - k):end] *= np.linspace(1, 0, min(k, end))
        bed[end:] = 0
        return bed.astype(np.float32)
    if fi: k = int(fi * sr); bed[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * sr); bed[max(0, end - k):end] *= np.linspace(1, 0, min(k, end))
    for t0, t1 in mutes:
        a, b = int(t0 * sr), int(t1 * sr); ko, ki = int(0.04 * sr), int(0.6 * sr)
        bed[a:a + ko] *= np.linspace(1, 0, len(bed[a:a + ko]))
        bed[a + ko:b] = 0
        bed[b:b + ki] *= np.linspace(0, 1, len(bed[b:b + ki]))
    bed[end:] = 0
    return bed.astype(np.float32)
