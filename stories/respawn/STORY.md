# RESPAWN (dark fantasy death-loop, 4-part series)
Inspired by the Re:Zero death-loop idea, with our own characters, world and plot. Theo joins an empty Roblox server called Lanternfall at 3 AM and wakes up inside it. Every time he dies, he respawns at the same apple stall at noon. Nobody remembers but him, and if he tries to tell anyone, time freezes and a black hand closes around his chest.

## Format (j 24 Nov)
4 parts of 1:30 to 2:00 (overrides the ~1 min rule for this series). Each part opens on a 2-3 s hook and ends on a cliffhanger plus a choice question. British voices. Speed-ups j chose (24 Nov): (1) three approval stops only: script → storyboard (with sound) → motion preview → final; no audio animatic, motion clips or pod asset stills. (4) The respawn moment is rendered once and reused every loop. Scripts, voices and SFX go part by part.

## Look + cast
- **Cards (new):** THEO (lead/narrator, teen, hoodie, out of place in a medieval world), WREN (lamplighter's apprentice: satchel, lighting pole, braid), ASHBY (butler: white gloves, grey hair, kind face), BRAMBLE (apple merchant, apron). LILY (Ashby's daughter, Part 3-4, mostly heard). THE HAND (black, smoke-edged arm, only in time-freeze).
- **World:** new `@world("lanternfall")`. Sets: market square + apple stall (checkpoint), back alley, rooftops, Vale Manor (gate, servant bedroom, hall, locked room). Palette: warm lantern amber by day; cold blue night; time-freeze = desaturated + pure black hand.
- **Signature:** red Roblox respawn ring + respawn sound + apple drop. Rendered once, reused every loop.
- **Music:** `assets/music/Numbers_piano.mp3` (j 24 Nov), quieter than usual: ~24 dB under voices, ducked under speech; cuts out with all sound at the time freeze. Re:Zero stings: return-by-death on every respawn, the witch OST under the Hand.

## Files
`scripts/rsN.py`, `audio/prep_rsN.py`, `data/rsN/`, `partN/` (script, voice), `exports/` (laptop). Id tag: `rs`. 

## Parts
- **Part 1 "Checkpoint"** (~1:45): script v1 in `part1/script_rs1.md`.
- **Part 2 "The Manor"** (plan): Theo keeps Wren out of the alley; she gets him a servant job at Vale Manor, where the lantern's trail leads. Ashby (white gloves) is kind. Theo dies in his bed every night. Cliff: his own name scratched into the wall 12 times, in his handwriting, above "DON'T DRINK THE TEA". Ashby knocks with a tray.
- **Part 3 "The Butler"** (plan): the tea kills a plant. A locked room holds the unlit Sun Lantern and 40 years of identical calendars. Ashby stole the sun so dawn never comes for his dying daughter Lily. Cliff: "You've died here before, haven't you? So have I."
- **Part 4 "Sunrise"** (plan): two loopers can talk through the freeze. Theo stops running (the choice he always made) and talks Ashby round; Wren lights the lantern; dawn, day 4. Final: a red ring flickers under Wren: "That's the first time I've died today." 

## Status (24 Nov)
- Part 1 audio mix v3 APPROVED 24 Nov (114 s, `audio/prep_rs1.py`, data/rs1). Stair_crack SFX still missing (gap after "The stairs gave way").
- Part 1 built: world `scripts/rs_world.py` (@world lanternfall: square, apple stall, alley, inn stairs, cellar, bedroom, respawn ring, the hand), cards `scripts/rs_cast.py` (Theo, Wren, Bramble, Ashby, Thief, `lf_extra`), scene `scripts/rs1.py` (52 cuts; FACE/LIPSYNC/SHOT/FRAMING OK). Ashby shows only gloves, shoes and a smile in Part 1.
- Storyboard approved 24 Nov; j skipped the free preview. Final rendered 24 Nov on 3× Secure 4090 split (pod_range, ~1 h, ~$3.10): `RESPAWN_Part1.mp4` + `_TikTok.mp4` in project files respawn/exports (laptop: stories\respawn\exports). Render cache accepted (master: project files respawn/render_cache/rs1_master.mp4 → laptop stories\respawn\render_cache).
- Motion audit on the final: 5 pops (1026 lamps out, 2043-44 the hand, 2393-94 smile), 8 judder runs (ring 20-34 / 1200-1214 / 2700-2715, 55-69, 1255-1269, 2149-2163, 2418-2432, 2581-2595). Fix via render_cache patch if j wants. Stair_crack SFX still missing.
- Next: j's notes on the final; Part 2 script.
