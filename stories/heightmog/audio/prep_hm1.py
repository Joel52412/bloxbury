# prep_hm1.py - HEIGHT MOG: The Trenchcoat Mayor cue sheet on the shared audio kit (mix.py). 24 fps.
# Voices are the sped-up/pitched copies (voice_fx.py: kai +1.5, mayor/guys +0.5 (Joel: +3 kid sounded weird), tempo 1.075 (Joel), 1:09.9) in part1/voice/fx/:
#   python3 _pipeline/audio_tools/voice_fx.py stories/heightmog/part1/voice kai:1.5 mayor:0.5 guys:0.5 --id hm1 --tempo 1.075.
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
    ("mayor", "...Please", 1.90, "D", "w", None, "reveal"),      # gap = wobble/rip/thud (1.2 s) + silence + gasp
    ("kai", "They were shorter", 0.25, "N", "w", None, "two_shot"),
    ("kai", "I could've", 0.15, "N", "w", None, None),
    ("kai", "Taxes... cancelled", 0.30, "D", "w", None, "coat_ten_feet"),
    ("kai", "Turns out", 0.15, "N", "w", None, "strut"),
    ("kai", "Every Tuesday", 0.15, "N", "w", None, "calendar"),
    ("guys", "It's not Tuesday", 0.10, "O", "w", None, None),
    ("guys", "Your knee is in my ear!", 0.15, "O", "w", None, "eight_shoes"),
    ("kai", "Would you", 0.25, "N", "w", None, "hat_tip"),
    ("kai", "Because in this town", 0.15, "N", "w", None, "loop_opening"),
]
m = Mix(REPO, "hm1", story="heightmog", voices=("kai", "mayor", "guys"),
        voice_dir=REPO + "/stories/heightmog/part1/voice/fx/")
for c in CUES: m.cue(*c)
k = m.marks
TOPPLE = k["Hehe"][1] + 0.1                       # giggle ends, coat goes over
THUD = TOPPLE + 0.6                               # Coat_topple #1 thuds land here; music hard-drops on the hit
MUTES = [(THUD, k["Taxes... cancelled"][0])]      # back in when Kai takes the top
# SFX: Joel's ElevenLabs files in assets/sfx (picked + edited 23 Nov; all trims/EQ live here, files untouched)
HP = "highpass=f=110"                              # crowds: cut rumble so they sit under the voices
m.sfx("Crowd_groan", 2, 0.30, 2.60, -36, fo=0.6, filt=HP, at=k["Taxes... doubled"][1] + 0.05)
m.sfx("Bus_leave", 1, 3.00, 6.00, -38, fi=0.08, fo=0.8, at=k["Me? Four"][0] + 0.1)     # door hiss + pull-away only
m.sfx("Pen_drop", 3, 0.82, 1.90, -40, fi=0.005, fo=0.3, filt="lowpass=f=9000", at=k["He never bends"][0] + 0.25)
m.sfx("Dog_sniff", 1, 0.10, 2.40, -37, fo=0.4, at=k["Once, a dog"][0] + 0.5)
m.sfx("Shoe_shuffle", 4, 0.30, 2.30, -37, fo=0.5, filt="lowpass=f=8000", at=k["And his coat"][0] + 0.6)
m.sfx("Mic_tap", 4, 0.36, 0.85, -38, fi=0.005, fo=0.1, at=k["Citizens"][0] - 0.6)       # two taps
m.sfx("Coat_topple", 1, 2.18, 4.10, -30, fi=0.15, fo=0.5, filt="alimiter=limit=0.7", at=THUD - 0.6)  # rustle under the giggle -> thuds
m.sfx("Crowd_gasp", 1, 0.15, 1.40, -31, fo=0.5, filt=HP, at=THUD + 0.15)
m.sfx("Crowd_cheer", 3, 0.10, 3.00, -36, fo=0.9, filt=HP, at=k["Taxes... cancelled"][1] + 0.05)
TOTAL = round(m.t + 0.3, 2)
m.music({"file": "assets/music/Numbers_piano.mp3", "vol": 0.2, "fade_in": 0.0, "fade_out": 0.4, "pause": True},
        MUTES, duck=True, low_trim=True)
m.check_overlaps()
m.finish(TOTAL, mutes=MUTES)
