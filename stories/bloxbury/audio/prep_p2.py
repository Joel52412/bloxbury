# prep_p2.py - Part 2 "She Came Home": cue sheet + sound design on the shared audio kit (mix.py). 24 fps.
# Line cuts come from split_lines.py / pocketsphinx (data in stories/bloxbury/data/p2/lines_*.json). ElevenLabs leaves digital
# silence between lines, so every cut sits in silence. Pacing is set here (dest times), not in the recordings.
# Usage: python3 prep_p2.py [repo_root]  (TIKTOK=1)  -> OUT_DIR/{env_p2.json, part2_audio.wav, captions_p2.ass}
import numpy as np, os, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from mix import Mix, load, fade, SR

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


# ElevenLabs glitches inside a take (Joel 15:41: "a bug in Milo speaking near the end"): in milo_p2.mp3 "depends"
# had a 70 ms dropout mid-word (33.458-33.528 s): cut it with a 3 ms crossfade (source seconds).
REPAIR = {("milo", "Comment below"): [("cut", 33.458, 33.528)]}

m = Mix(REPO, "p2", voices=("milo", "rae", "mum"))
for who, pre, d, mode, st, fx in CUES:
    m.voice(who, pre, at=d, mode=mode, style=st, fx=fx, fix=REPAIR.get((who, pre)))
m.check_overlaps()                  # no two lines on top of each other
rng = np.random.default_rng(7)

# ---- sound design (no loud stings; silence does the work)
# bridge: Part 1's lunge under a low swell, then dead silence on black
m.put(fade(load(m.file("low_horror_drone_#3"), 0, 0.85) * 0.45, 0.05, 0.12), 0.0)
# kitchen: Joel's ElevenLabs "pan_sizzle" only under the opening (Joel 13:15 / 15:25 / 15:40: faint, ~20 dB under voices;
# better silent than fake). Variant 1 hisses from the first frame: skip the attack. Level set by RMS (files arrive ~-48 dB).
SIZZLE_VAR = os.environ.get("SIZZLE_VAR", "1")
SIZZLE_DB = float(os.environ.get("SIZZLE_DB", -46))
try:
    sz = load(m.file("pan_sizzle", SIZZLE_VAR), 0.5, 6.25)
    sz *= 10 ** (SIZZLE_DB / 20) / (np.sqrt((sz ** 2).mean()) + 1e-9)
    m.put(fade(sz, 0.3, 1.4), 1.25)
except StopIteration:
    print("NO SIZZLE SFX: ask Joel for pan_sizzle (prompt in VOICE_DESIGN.md -> SFX requests)")
# hallway at night: clock ticking, which stops dead with the music at 44.30
m.put(fade(load(m.file("clock_ticking_#1"), 0, 4.4) * 0.35, 0.3, 0.02), 39.9)
# reflection turns in silence; only a faint low swell as the head turns (46.2-47.6)
m.put(fade(load(m.file("low_horror_drone_#2"), 0, 1.8) * 0.18, 0.8, 0.6), 46.0)
# closet: tiny creak as the crack widens and the hand shows (63.9)
m.put(fade(load(m.file("creaking_wooden_door_#2"), 0, 1.1, "lowpass=f=3000") * 0.30, 0.05, 0.4), 63.85)
# footsteps on the stairs, slowing, then stopping outside the door (pre-rule synth thuds, kept as shipped)
t = 65.2
for i, gap in enumerate([0.52, 0.55, 0.58, 0.64, 0.72, 0.0]):
    k = int(0.16 * SR); thud = rng.standard_normal(k).astype(np.float32)
    thud = np.convolve(thud, np.ones(40) / 40, "same") * np.exp(-np.arange(k) / (0.035 * SR)) * (0.55 + 0.08 * i)
    m.put(thud, t); t += gap
# three soft knocks: Part 1's front-door knock (#4), its first three knocks (onsets 0.53/0.84/1.09), quieter, muffled
kn = load(m.file("three_heavy_door_kno_#4"), 0.45, 1.33, "lowpass=f=2400")   # stops before its 4th knock (1.37)
m.put(fade(kn * 0.55, 0.01, 0.12), 67.82)                     # knocks land at ~67.90 / 68.21 / 68.46
m.silence(BLACK_CUT, OUTRO0)          # hard cut to black: everything stops
m.music(2, MUSIC_MUTES)
m.silence(BLACK_CUT, OUTRO0)
# TikTok/Shorts loudness for Part 2: -14 LUFS / -1.5 dBTP (Part 3+ use the -16 / -2 default)
m.finish(TOTAL, black_cut=BLACK_CUT, outro0=OUTRO0, scenes=SCENES, mutes=MUTES, lufs=-14, tp=-1.5,
         visemes=False)        # delivered with the loudness flap; True = speech-driven mouths on a re-render
