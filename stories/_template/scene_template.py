# <tag>1.py - <TITLE>. Built on the shared scene kit: this file is settings + beats (see _pipeline/ENGINE.md).
# Audio: audio/prep_<tag>1.py -> {env_<tag>1.json, <tag>1_audio.wav, captions_<tag>1.ass}
# Stills: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 <tag>1.py
import os
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
boot("<tag>1", world="bloxbury", lead="<lead>")        # or your own @world("<name>") registered above this line

load("recurring", "props2", "props3", "props4")         # library batches you need
lead, = cast(lead=(make_milo, "rest_flat"))             # cards: (maker, rest mouth)
camera_rig(); load("cinema", "motion")

# ---- beats (times from env scenes: SC["name"] = (t0, t1); FT(seconds) -> frame)
# place(...); cine("A hook", *SC["hook"], lead, size="MCU", move="push"); gesture/look/lean(...); live(lead, a, b, "calm")

finish_part(life=True, allow=(), motion_chars={"lead": lead})
