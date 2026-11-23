# HEIGHT MOG: The Trenchcoat Mayor (comedy, one-off)
In this town, the taller you are, the more power you get. Kai (4 ft 1) notices the 9-foot mayor never sits, never bends and has six shoes. He tickles him mid-speech, the mayor topples: three short guys in a trenchcoat. Kai doesn't expose them. He climbs on top.

## Look + cast
- **Cards (new, need asset sheets):** KAI (lead/narrator, small kid), MAYOR STACK (three short guys; top one has mustache + top hat), long trenchcoat that hides them. Tall guy, average guy, aide, crowd: library extras.
- **Height = power:** R6 rigs scaled (Kai 1.0, short guys ~0.9, average 1.25, tall 1.5, stack ≈2.2).
- **World:** daytime, bright comedy palette. Sets: library town street/square; NEW stage + podium + flags, town dinner table, backstage curtain.
- **New props:** trenchcoat, mustache, top hat, podium + mic, bus, shiny car, pen.
- **Music:** `assets/music/Numbers_piano.mp3` (Joel 23 Nov), drop at the topple.

## Files
`part1/script_hm1.md` (beats + script), `part1/voices_hm1.md` (voice designs, paste-ready blocks, SFX list). Later: `scripts/hm1.py`, `audio/prep_hm1.py`, `data/hm1/`. Id tag: `hm`.

## Parts
- **Part 1 "The Trenchcoat Mayor"** (~64 s: min 1:01 for TikTok pay, max 1:10).

## Audio (approved, final)
- Voices `part1/voice/<who>_hm1.mp3` (Joel's takes); mix uses `part1/voice/fx/` made by `voice_fx.py part1/voice kai:1.5 mayor:0.5 guys:0.5 --id hm1 --tempo 1.075` (formants kept).
- Lines `data/hm1/lines_{kai,mayor,guys}.json` (Kai's "July" + "It's Tuesday" not recorded, dropped). Mix/env/captions `data/hm1/` (`hm1_audio.flac`, `env_hm1.json`: 24 scenes + lip-sync, `captions_hm1.ass`). Total 69.92 s.
- SFX picks (trims/EQ/levels in `audio/prep_hm1.py`): Crowd_groan #2, Bus_leave #1, Pen_drop #3, Dog_sniff #1, Shoe_shuffle #4, Mic_tap #4, Coat_topple #1 (music drops on its thud), Crowd_gasp #1, Crowd_cheer #3.

## Status (23 Nov)
- Script + audio approved by Joel 23 Nov. Branch `claude/project-thread-wfyx4a` (not merged, no PR).
- Next (fresh thread): asset sheet `scripts/hm1_assets.py` for Kai, the coat stack (3 short guys + trenchcoat, mustache, top hat), stage/podium/mic, bus, shiny car, dog, dinner table; then scene `hm1.py` on the 24 scenes in env_hm1.json.
