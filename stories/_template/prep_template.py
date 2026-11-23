# prep_<tag>1.py - <TITLE> cue sheet + SFX on the shared audio kit (mix.py). 24 fps.
# Usage: python3 prep_<tag>1.py [repo]  (TIKTOK=1, NOMUSIC=1) -> OUT_DIR/{env_<tag>1.json, <tag>1_audio.wav, captions_<tag>1.ass}
import os, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from mix import Mix

# (who, line-text prefix, gap_before, mode N/D/C/O, style w/r, fx, scene-starting-here or None)
CUES = [
    ("<lead>", "<first words>", 0.25, "N", "w", None, "hook"),
]
m = Mix(REPO, "<tag>1", story="<name>", voices=("<lead>",))
for c in CUES: m.cue(*c)
k = m.marks
# m.sfx("<ElevenLabs name>", 1, 0.0, 2.0, -36, at=k["<prefix>"][1] + 0.3)
TOTAL = m.t + 1.0
m.music({"file": "assets/music/<file>", "vol": 0.2, "fade_in": 0.0, "fade_out": 1.0}, [], duck=True, low_trim=True)
m.finish(TOTAL)
