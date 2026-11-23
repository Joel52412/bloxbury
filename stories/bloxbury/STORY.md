# BLOXBURY: The 3AM Knock (horror series)
Milo, a kid in Bloxbury, hears knocks at 3AM. Something that copies people (the Knocker) is replacing the town one by one. Rae keeps the WHO'S LEFT list.

## Look + cast
- **The Knocker:** tall, starved, black sockets with pinpoint white eyes, red thin-tooth grin; always kept in the dark with a cool rim light. Fakes are "too perfect" (red captions, fake/door voice FX).
- **Cards:** MILO (lead + narrator, `rig2.make_milo`), RAE, MUM / RealMum (`make_mum("RealMum")`), MAYOR, DAN, NEIGHBOUR (`recurring.py`).
- **World:** `boot("pN", world="bloxbury", patches=BLOX_LOW_WINDOWS [+ BLOX_SIDE_WINDOW])`: town + Milo's house from `scripts/bloxbury_part1.py`. Sets: Milo's room, kitchen, hallway (mirror), hollow closet. Night lighting: `scripts/part3_assets.py`.
- **Music:** "Numbers" (instrumental loop, `assets/music`, Part 2 at 35%; piano cover in Part 3 at 20%, pauses during mutes). Config in `music_bed.PART_MUSIC`.

## Files
`scripts/` (part1_v2.py, part2.py, part3.py, *_assets.py, world), `audio/prep_p1..3.py`, `data/p1..p3/` (env, captions, mix, line cuts), `partN/` (script.md, voice), `youtube/make_youtube.sh`, `exports/` (laptop). Part ids `p1..pN`.

## Parts
- **Part 1** (71.75 s): knocks at 3AM; the Knocker is in his closet; lunge at the lens on "OUT", cut to black.
- **Part 2 "She Came Home"** (80 s, 1921 frames): Mum is back making pancakes but calls him "Milo" (she never does). Rae: Mum was crossed off three weeks ago; "mirrors don't lie". The hallway mirror's twin keeps smiling. Real Mum whispers from the closet "I heard it too"; fake Mum knocks: "Who are you talking to?" Outro: "Two mums. One door. Which one would you open?"
- **Part 3 "Don't Say It"**: Mum's rules; the fake learns words he says, so Milo writes LIGHTHOUSE; escapes over the roof to Rae, who says "Lighthouse"; he never said it. Rae's phone buzzes: Milo's own voice, "Rae, it's me. Don't let him in." Outro: "Which Milo would you let in?"

## Status (23 Nov)
- Parts 1-3 delivered (Part 3 v2 motion fixes in code; Joel chose no re-render). Part 2 keeps its old loudness lip flap (`visemes=False`).
- **NEXT:** Part 4. Open threads: where is real Mum? who has Milo's voice?
