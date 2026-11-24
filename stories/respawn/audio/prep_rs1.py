# prep_rs1.py - RESPAWN Part 1 "Checkpoint" cue sheet + SFX on the shared audio kit (mix.py). 24 fps.
# Usage: python3 prep_rs1.py [repo]  (TIKTOK=1, NOMUSIC=1) -> OUT_DIR/{env_rs1.json, rs1_audio.wav/.flac, captions_rs1.ass}
# No speed-up or pitch shift (j 24 Nov). Music: Numbers piano, quieter than Part 3 (0.13 vs 0.20), pauses through mutes.
import os, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from mix import Mix, load, fade
import numpy as np

# (who, line-text prefix, gap_before, mode N/D/C/O, style w/r, fx, scene-starting-here or None)
CUES = [
    ("theo", "That's the fourth", 0.25, "N", "w", None, "hook_respawn"),
    ("bramble", "Mind yourself", 0.15, "D", "w", None, None),
    ("theo", "Same apple", 0.30, "N", "w", None, "apple_cuts"),
    ("theo", "Three hours ago", 0.35, "N", "w", None, "bedroom"),
    ("theo", "Server called", 0.30, "N", "w", None, "server_list"),
    ("theo", "I clicked join", 0.30, "N", "w", None, "click"),
    ("theo", "And the game", 1.00, "N", "w", None, "arrival"),
    ("theo", "The first time round", 0.50, "N", "w", None, "wren_vault"),
    ("wren", "Oi!", 0.25, "D", "w", None, None),
    ("theo", "Wren. Lamplighter", 0.30, "N", "w", None, "rooftop"),
    ("wren", "If it's not back", 0.40, "D", "w", None, "warning"),
    ("theo", "The dark? Like", 0.35, "D", "w", None, None),
    ("wren", "No. The dark.", 0.50, "D", "w", None, None),
    ("theo", "We followed", 1.10, "N", "w", None, "chase_sunset"),
    ("theo", "Then the last bell", 2.60, "N", "w", None, "alley"),
    ("bramble", "Mind yourself", 3.80, "D", "w", None, "respawn_2"),
    ("theo", "So I tried again", 0.40, "N", "w", None, None),
    ("theo", "Second time", 0.40, "N", "w", None, "stairs"),
    ("theo", "Third time", 1.20, "N", "w", None, "cellar"),
    ("theo", "And every time", 1.30, "N", "w", None, "back_to_wren"),
    ("wren", "Sorry... have we met", 0.40, "D", "w", None, None),
    ("theo", "She didn't remember", 0.80, "N", "w", None, "alone"),
    ("theo", "So the fourth time", 0.50, "N", "w", None, "grab"),
    ("theo", "Wren. Listen.", 0.30, "D", "w", None, "two_shot"),
    ("theo", "Everything stopped", 1.60, "N", "w", None, "freeze"),
    ("hand", "Not. Yours", 1.80, "O", "r", None, "hand"),
    ("theo", "I died before", 1.70, "N", "w", None, "black"),
    ("theo", "But that's not", 0.90, "N", "w", None, "respawn_3"),
    ("theo", "This time... the apple", 0.40, "N", "w", None, "apple_glove"),
    ("ashby", "Welcome back", 0.90, "O", "w", None, "smile"),
    ("theo", "Nobody here knows", 0.60, "N", "w", None, "theo_face"),
    ("theo", "Would you have told", 0.90, "N", "w", None, "wren_look"),
    ("theo", "And that... was only", 0.80, "N", "w", None, "ring_loop"),
]
m = Mix(REPO, "rs1", story="respawn", voices=("theo", "wren", "bramble", "ashby", "hand"))
for c in CUES: m.cue(*c)
k = m.marks
TOTAL = round(k["And that... was only"][1] + 0.15 + 2.75, 2)   # the last sting plays out in full


def raw(name, at, db, a=0, b=None, fi=0.01, fo=0.2):
    """j's own files (no ElevenLabs variant number), levelled by RMS."""
    s = load(m.sfxd + name, a, b); s *= 10 ** (db / 20) / (np.sqrt((s ** 2).mean()) + 1e-9); m.put(fade(s, fi, fo), at)

RBD = "re-zero-return-by-death.mp3"; WITCH = "re-zero-kara-hajimeru-isekai-seikatsu-ost-03_ORAmAM1.mp3"
# beds first, so a silence() placed later zeroes them too
alley0, freeze0 = k["Then the last bell"][0] - 2.2, k["Wren. Listen."][1]
m.sfx("Market_ambience", 1, 0, None, -44, fi=0.4, fo=0.8, at=k["And the game"][0] - 0.6)          # arrival -> sunset
m.sfx("Market_ambience", 2, 0, freeze0 - (k["Mind yourself"][0] - 0.3), -44, fi=0.6, fo=0.12, at=k["Mind yourself"][0] - 0.3)  # respawn 2 -> freeze
m.sfx("Alley_night_ambience", 1, 0, k["Mind yourself"][0] - alley0, -42, fi=1.0, fo=0.05, at=alley0)
# hook: respawn sting on frame 0, apple drop, three more drops on the cuts
raw(RBD, 0.0, -24)
h1 = k["That's the fourth"][1]
m.sfx("Apple_drop", 3, 0, 1.6, -30, at=h1 + 0.05)
for i, d in enumerate((0.15, 1.0, 1.85)): m.sfx("Apple_drop", 4 if i % 2 else 3, 0, 0.9, -32, at=k["Same apple"][0] + d)
# the server + the click + pulled in
m.sfx("Mouse_click", 1, 0, None, -30, at=k["I clicked join"][1] + 0.05)
m.sfx("Pulled_in_whoosh", 2, 0, None, -27, at=k["I clicked join"][1] + 0.25)
m.sfx("Rooftop_run", 1, 0, None, -36, at=k["Wren. Lamplighter"][0])
# last bell -> alley -> glove -> black -> respawn
m.sfx("Bell_toll", 1, 0, None, -28, fo=1.2, at=k["We followed"][1] + 0.35)
g = k["Then the last bell"][1] + 1.0
m.sfx("Close-mic_heavy_wool", 1, 0, 1.2, -32, at=g)
m.silence(g + 0.7, k["Mind yourself"][0] - 0.9, ramp=0.03)
raw(RBD, k["Mind yourself"][0] - 0.9, -26)
m.sfx("Apple_drop", 3, 0, 1.6, -31, at=k["Mind yourself"][1] + 0.05)
# loops 2 + 3: stairs (Stair_crack not delivered yet: gap left), cellar candle, quick respawns
s2 = k["Second time"][1]
m.silence(s2 + 0.05, s2 + 0.6, ramp=0.03); raw(RBD, s2 + 0.6, -30, b=1.4, fo=0.3)
c3 = k["Third time"][1]
m.sfx("Candle_out_a_single", 1, 0, None, -32, at=c3 - 0.35)
m.silence(c3 + 0.15, c3 + 0.7, ramp=0.03); raw(RBD, c3 + 0.7, -30, b=1.4, fo=0.3)
# the freeze: all sound stops, the witch under the Hand, the heartbeat, black
# (no silence() here: it would also zero every voice placed after the freeze; the market bed ends at freeze0 instead)
m.sfx("Time_freeze_every_s", 1, 0, None, -30, fi=0.005, at=freeze0)
raw(WITCH, k["Everything stopped"][0] - 0.6, -30, fi=0.6, fo=0.05, b=k["Not. Yours"][1] + 0.3 - (k["Everything stopped"][0] - 0.6))
m.sfx("Heartbeat_slow_a_de", 1, 0, None, -30, fi=0.3, fo=0.05, at=k["Everything stopped"][1] + 0.2)
black0 = k["Not. Yours"][1] + 0.3
m.silence(black0, k["I died before"][0] - 0.1, ramp=0.03)
# respawn 3: the apple rolls past, the glove picks it up
raw(RBD, k["But that's not"][0] - 0.8, -26)
m.sfx("Market_ambience", 3, 0, None, -48, fi=1.0, fo=1.0, at=k["But that's not"][0] - 0.5)
m.sfx("Apple_drop", 4, 0, 1.6, -31, at=k["This time... the apple"][0] + 0.2)
m.sfx("Glove_pickup_a_leat", 1, 0, None, -30, at=k["This time... the apple"][1] + 0.25)
raw(RBD, k["And that... was only"][1] + 0.15, -24)        # loops into the hook's sting

# music pauses through the alley/deaths and from the freeze to the end
MUTES = [(k["We followed"][1] - 0.6, k["And every time"][0] - 0.4), (freeze0, TOTAL)]
m.music({"file": "assets/music/Numbers_piano.mp3", "vol": 0.13, "fade_in": 0.0, "fade_out": 1.0, "pause": True, "mute_fo": (1.2, 0.04)},  # slow fade under the bell, sharp stop at the freeze (deliberate)
        MUTES, duck=True, low_trim=True)
m.check_overlaps()
m.finish(TOTAL, mutes=MUTES)
