# prep_hm1.py - HEIGHT MOG: The Trenchcoat Mayor cue sheet on the shared audio kit (mix.py). 24 fps.
# Voices are the sped-up/pitched copies (voice_fx.py: kai +3 kid, mayor/guys +1, tempo 1.13 to land at 1:07) in part1/voice/fx/:
#   python3 _pipeline/audio_tools/voice_fx.py stories/heightmog/part1/voice kai:3:kid mayor:1 guys:1 --id hm1 --tempo 1.13.
# Usage: python3 prep_hm1.py [repo]  (TIKTOK=1, NOMUSIC=1) -> OUT_DIR/{env_hm1.json, hm1_audio.wav/.flac, captions_hm1.ass}
import os, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from mix import Mix

# (who, line-text prefix, gap_before, mode N/D/C/O, style w/r, fx, scene-starting-here or None)
CUES = [
    ("kai", "In this town, the taller", 0.25, "N", "w", None, "hook_mayor_stage"),
    ("kai", "Six foot", 0.10, "N", "w", None, "tall_car"),
    ("kai", "Five foot", 0.10, "N", "w", None, "bus"),
    ("kai", "Me? Four", 0.10, "N", "w", None, "behind_bus"),
    ("kai", "And our mayor", 0.15, "N", "w", None, "mayor_glide"),
    ("mayor", "Taxes... doubled", 0.15, "D", "w", None, "mayor_close"),
    ("kai", "But something", 0.15, "N", "w", None, "kai_squint"),
    ("kai", "He never sits", 0.15, "N", "w", None, "dinner"),
    ("kai", "He never bends", 0.10, "N", "w", None, "pen_drop"),
    ("kai", "Once, a dog", 0.15, "N", "w", None, "dog_sniff"),
    ("guys", "Ah... ah", 0.05, "O", "w", None, None),
    ("kai", "And his coat", 0.15, "N", "w", None, "six_shoes"),
    ("kai", "Then I heard", 0.15, "N", "w", None, "backstage"),
    ("mayor", "Stop moving", 0.15, "D", "w", None, None),
    ("guys", "Your knee is in my ear.", 0.10, "O", "w", None, None),
    ("guys", "I'm hungry", 0.10, "O", "w", None, None),
    ("kai", "So at his big", 0.15, "N", "w", None, "speech_crawl"),
    ("mayor", "Citizens", 0.15, "D", "w", None, "podium"),
    ("kai", "One tickle", 0.05, "N", "w", None, "tickle"),
    ("guys", "Hehe", 0.10, "O", "w", None, "sway"),
    ("mayor", "...Please", 2.20, "D", "w", None, "reveal"),      # gap = wobble/rip/thud (1.2 s) + silence + gasp
    ("kai", "They were shorter", 0.30, "N", "w", None, "two_shot"),
    ("kai", "I could've", 0.15, "N", "w", None, None),
    ("kai", "Taxes... cancelled", 0.30, "D", "w", None, "coat_ten_feet"),
    ("kai", "Turns out", 0.15, "N", "w", None, "strut"),
    ("kai", "Every Tuesday", 0.15, "N", "w", None, "calendar"),
    ("guys", "It's not Tuesday", 0.10, "O", "w", None, None),
    ("guys", "Your knee is in my ear!", 0.15, "O", "w", None, "eight_shoes"),
    ("kai", "Would you", 0.30, "N", "w", None, "hat_tip"),
    ("kai", "Because in this town", 0.15, "N", "w", None, "loop_opening"),
]
m = Mix(REPO, "hm1", story="heightmog", voices=("kai", "mayor", "guys"),
        voice_dir=REPO + "/stories/heightmog/part1/voice/fx/")
for c in CUES: m.cue(*c)
k = m.marks
TOPPLE = k["Hehe"][1] + 0.1                       # coat goes over: music hard-drops here
MUTES = [(TOPPLE, k["Taxes... cancelled"][0])]    # back in when Kai takes the top
# SFX (Joel's ElevenLabs files, add when they arrive in assets/sfx/):
# m.sfx("Crowd_groan", 1, 0, 2.0, -34, at=k["Taxes... doubled"][1] + 0.05)
# m.sfx("Bus_leave", 1, 0, 3.0, -36, at=k["Me? Four"][0])
# m.sfx("Pen_drop", 1, 0, 1.0, -34, at=k["He never bends"][0] + 0.3)
# m.sfx("Dog_sniff", 1, 0, 2.0, -36, at=k["Once, a dog"][0] + 0.4)
# m.sfx("Shoe_shuffle", 1, 0, 2.0, -36, at=k["And his coat"][0] + 0.5)
# m.sfx("Mic_tap", 1, 0, 1.0, -34, at=k["Citizens"][0] - 0.6)
# m.sfx("Coat_topple", 1, 0, 3.0, -28, at=TOPPLE)
# m.sfx("Crowd_gasp", 1, 0, 2.0, -32, at=TOPPLE + 1.3)
# m.sfx("Crowd_cheer", 1, 0, 3.0, -32, at=k["Taxes... cancelled"][1] + 0.05)
TOTAL = round(m.t + 0.3, 2)
m.music({"file": "assets/music/Numbers_piano.mp3", "vol": 0.2, "fade_in": 0.0, "fade_out": 0.4, "pause": True},
        MUTES, duck=True, low_trim=True)
m.check_overlaps()
m.finish(TOTAL, mutes=MUTES)
