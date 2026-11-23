# prep_p3.py - Part 3 "Don't Say It": cue sheet + SFX on the shared audio kit (mix.py). 24 fps.
# Lines from _pipeline/data/p3/lines_*.json (align_full + split_lines; milo 12/13 + mum "Bug?" fixed by hand from the
# energy envelope, scan for in-word gaps/clicks clean 22 Nov). "Which Milo..." regenerated (pitch cracks) -> milo_p3_fix.mp3. Cues are SEQUENTIAL: dest = previous line end + gap.
# Usage: python3 prep_p3.py [repo]  (TIKTOK=1 -> music span <=55 s, NOMUSIC=1)  -> OUT_DIR/{env_p3.json, part3_audio.wav, captions_p3.ass}
import os, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, REPO + "/_pipeline/audio_tools")
from mix import Mix

# (who, prefix, gap_before, mode, style, fx, scene-starting-here or None)
#  mode N narration / D dialogue (lip-sync) / C to camera / O off-screen.  style w / r.  fx None/door/closet/fake/phone
CUES = [
    ("milo", "I haven't", 0.10, "N", "w", None, "hook_bed"),        # frame 0: Milo lit, hand over mouth
    ("milo", "Because", 0.30, "N", "w", None, "door_feet"),         # 'something wrong' (shadow feet) by ~3.4 s
    ("mum", "Bug?", 1.30, "O", "r", "door", None),                  # soft knocks in the gap
    ("milo", "Last night", 0.55, "N", "w", None, "milo_close"),
    ("milo", "Then it heard", 0.20, "N", "r", None, None),
    ("mum", "Don't say", 0.70, "O", "w", "closet", "closet_crack"),
    ("mum", "Not one", 0.35, "O", "w", "closet", None),
    ("milo", "Mum had", 0.60, "N", "w", None, "rules_drawing"),
    ("milo", "Brush", 0.30, "N", "w", None, None),
    ("milo", "Lock", 0.25, "N", "w", None, None),
    ("milo", "And never", 0.35, "N", "r", None, None),
    ("mum", "Bug... if", 1.00, "O", "r", "fake_door", "door_ask"),  # MUSIC OUT
    ("mum", "tell me", 0.25, "O", "r", "fake_door", None),
    ("milo", "It wasn't", 0.70, "N", "w", None, "milo_push"),
    ("milo", "It was learning", 0.30, "N", "r", None, None),
    ("milo", "So I didn't", 0.60, "N", "w", None, "note"),
    ("milo", "I wrote", 0.25, "N", "w", None, None),                 # then pencil, slide in, wait, slide back, note insert
    ("milo", "I didn't make", 6.00, "N", "w", None, "escape"),       # window, roof, run
    ("rae", "Milo?", 3.80, "D", "w", None, "rae_door"),              # run + door unlock in the gap
    ("rae", "You just", 0.45, "D", "w", None, None),
    ("rae", "You said", 0.65, "D", "w", None, None),
    ("rae", "Lighthouse", 0.70, "D", "r", None, None),
    ("milo", "I never said", 0.80, "N", "w", None, "milo_realise"),
    ("milo", "I only wrote", 0.35, "N", "w", None, None),
    ("milo", "And I gave", 0.45, "N", "r", None, None),
    ("milo", "Most of you", 0.70, "N", "w", None, None),
    ("milo", "So did I", 0.40, "N", "w", None, None),
    ("milo", "Rae, it's me", 1.90, "O", "r", "phone", "phone"),      # silence, buzz, answer click
    ("milo", "Don't let", 0.40, "O", "r", "phone", None),
]
OUTRO = [("milo", "One of us is on the porch", 0.0, "C", "w", None, "outro"),
         ("milo", "One of us is on the phone", 0.30, "C", "w", None, None),
         ("milo", "Which Milo", 0.45, "C", "w", None, None)]
BLACK_AFTER, BLACK_LEN, TAIL = 0.45, 0.70, 1.20

m = Mix(REPO, "p3", voices=("milo", "rae", "mum"))
for c in CUES: m.cue(*c)
BLACK_CUT = round(m.t + BLACK_AFTER, 3); OUTRO0 = round(BLACK_CUT + BLACK_LEN, 3); m.t = OUTRO0
m.scene("black", BLACK_CUT)
for c in OUTRO: m.cue(*c)
TOTAL = round(m.t + TAIL, 2)

# ---- SFX (Joel's ElevenLabs files; level set by RMS, files arrive ~-48 dB)
k = m.marks
m.sfx("Soft_knocks", 2, 1.05, 2.15, -30, filt="lowpass=f=2600", at=k["Because"][1] + 0.25)          # three soft knocks before "Bug?"
m.sfx("Pencil_writing", 2, 0.1, 1.7, -36, at=k["I wrote"][1] + 0.15)                                # writes LIGHTHOUSE
# Joel 21:57: the two slides overlapped each other and the window (sounded repeated). Now: short soft push in,
# ~0.9 s of silence, then a slower, different slide back, and 0.5 s of quiet on the note before the window.
m.sfx("Paper_slide", 2, 0.6, 1.6, -39, fo=0.25, at=k["I wrote"][1] + 1.95)                         # pushed into the closet
m.sfx("Paper_slide", 1, 0.9, 2.2, -36, fo=0.3, at=k["I wrote"][1] + 3.85)                          # ...slides back
m.sfx("Window_open", 1, 0.8, 3.5, -34, fo=0.4, at=k["I didn't make"][0] - 0.6)
m.sfx("Roof_steps", 1, 0.0, 2.6, -38, fi=0.2, fo=0.5, at=k["I didn't make"][0] + 1.6)
m.sfx("Night_ambience", 2, 0.0, k["Rae, it's me"][0] - k["I didn't make"][0] + 0.5, -47, fi=0.6, fo=0.8, at=k["I didn't make"][0] - 0.2)
m.sfx("Night_run", 3, 0.0, 3.2, -36, fi=0.3, fo=0.6, at=k["I didn't make"][1] + 0.2)
m.sfx("Door_unlock", 2, 3.2, 5.6, -34, at=k["Milo?"][0] - 2.2)
m.sfx("Phone_buzz", 1, 0.0, 2.5, -30, at=k["So did I"][1] + 0.35)                                   # the one startle: a buzz in silence
m.sfx("Phone_click", 4, 1.1, 1.6, -38, at=k["Rae, it's me"][0] - 0.45)
m.sfx("low_horror_drone_", 2, 0, 3.0, -44, fi=1.0, fo=1.0, at=k["Bug... if"][0] - 0.2)              # faint swell under the ask
m.silence(BLACK_CUT, OUTRO0)

# music: out from the door ask until the escape; out again for the phone; back for the outro (YouTube)
MUTES = [(k["Bug... if"][0] - 0.3, k["I didn't make"][0] - 0.8), (k["So did I"][1] + 0.1, OUTRO0)]
MUSIC_MUTES = MUTES[:-1] + [(k["So did I"][1] + 0.1, TOTAL)] if m.tiktok else MUTES
# Music sits well UNDER the voices (Joel 21:54: softer, "premium"): bed at 0.20, low end trimmed, ducked ~7 dB under speech
m.music(3, MUSIC_MUTES, duck=True, low_trim=True)
m.silence(BLACK_CUT, OUTRO0)
m.finish(TOTAL, black_cut=BLACK_CUT, outro0=OUTRO0, mutes=MUTES)
