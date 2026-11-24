# HEIGHT MOG: The Trenchcoat Mayor (comedy, one-off)
In this town, the taller you are, the more power you get. Kai (4 ft 1) notices the 9-foot mayor never sits, never bends and has six shoes. He tickles him mid-speech, the mayor topples: three short guys in a trenchcoat. Kai doesn't expose them. He climbs on top.

## Look + cast
- **Cards (approved 23 Nov, `scripts/hm1_cast.py`):** KAI (deep brown skin, mustard 4'1 tee, teal joggers, red backpack, kid scale), GUY TOP (ginger hair + mustache, purple suit, top hat), GUY MID (glasses, blue shirt, green vest), GUY BOT (pink tank, blue joggers, headband). `build_stack()` = the MAYOR: three guys inside `hm_coat` (6 shoes, outer pair backwards; `shoes=8` for the ending). Tall guy, average guy, aide, crowd: `random_extra` (seeds 28/11/7 in hm1_assets.py).
- **Height = power:** R6 rigs scaled (Kai 1.0, short guys ~0.9, average 1.25, tall 1.5, stack ≈2.2).
- **World (approved):** TALLTON = Bloxbury map + `props7.hm_town_makeover(houses)` (pastel houses, shops, town hall + clock, bunting), `hm_plaza((190,0))` + `hm_stage((210,0))` in front of the town hall (stage faces -X), backstage wing `hm_curtain` as a stand-alone set at (700,0,400), banquet `hm_banquet` at (120,30), bus `hm_bus`, shiny car `props.car`, dog `hm_dog`, pen `hm_pen`. Daytime: `set_day`, lamps off. Sheet: `_studio_library/approval_sheets/HeightMog_asset_sheet.jpg`; staging examples per shot in `scripts/hm1_assets.py`.
- **Music:** `assets/music/Numbers_piano.mp3` (Joel 23 Nov), drop at the topple.

## Files
`part1/script_hm1.md` (beats + script), `part1/voices_hm1.md` (voice designs, paste-ready blocks, SFX list). Later: `scripts/hm1.py`, `audio/prep_hm1.py`, `data/hm1/`. Id tag: `hm`.

## Parts
- **Part 1 "The Trenchcoat Mayor"** (~64 s: min 1:01 for TikTok pay, max 1:10).

## Audio (approved, final)
- Voices `part1/voice/<who>_hm1.mp3` (Joel's takes); mix uses `part1/voice/fx/` made by `voice_fx.py part1/voice kai:1.5 mayor:0.5 guys:0.5 --id hm1 --tempo 1.075` (formants kept).
- Lines `data/hm1/lines_{kai,mayor,guys}.json` (Kai's "July" + "It's Tuesday" not recorded, dropped). Mix/env/captions `data/hm1/` (`hm1_audio.flac`, `env_hm1.json`: 24 scenes + lip-sync, `captions_hm1.ass`). Total 69.92 s.
- SFX picks (trims/EQ/levels in `audio/prep_hm1.py`): Crowd_groan #2, Bus_leave #1, Pen_drop #3, Dog_sniff #1, Shoe_shuffle #4, Mic_tap #4, Coat_topple #1 (music drops on its thud), Crowd_gasp #1, Crowd_cheer #3.

## Status (24 Nov)
- Script + audio approved 23 Nov. Asset sheet v3 approved 23 Nov 23:57 (props7 saved to the library).
- Scene `scripts/hm1.py` built 24 Nov (branch `claude/project-thread-uujwb2`, on sn1fef): 24 env scenes / 29 cuts (dog_sniff, backstage, sway, calendar split), all checks OK (faces, lip-sync, shots, motion, framing). Hook: mayor beside the podium (`MAYOR_STAGE`), six-shoes insert low at the hem. Ending: coat 2 (`Stack2`, Kai rides on top, eight shoes, Kai's top hat); stack 1 parked. Storyboard sent to j; free motion preview `preview_local.py hm1.py --all`.
- Next: j's notes on storyboard + preview, then motion_audit fixes, then ask j before the paid final render.
