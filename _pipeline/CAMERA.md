# Bloxbury camera playbook (Joel 23 Nov 01:10: "the camera just zooms in every time")
Research: Fincher (motivated moves), Spielberg (oners and blocking), Kubrick (one-point, Steadicam, stare), Ari Aster/Pogorzelski (dollhouse wides, swivel instead of reverse shot), Flanagan (negative space, hidden figures), It Follows (wide pans, POV push), Arcane/Spider-Verse (live-action imperfection in CG), Hitchcock's rule.

## Rules
1. **Motivated first (Fincher).** The camera moves when a character or object moves: same direction, same speed, and it stops when they stop. With nobody moving, the camera holds. An unmotivated move is spent on a story beat (a realisation, a reveal), never as filler.
2. **Size = importance (Hitchcock).** Frame each shot by what matters at that moment: the hand, the gap, the eyes. Save CU/ECU for key lines; a CU on every line flattens them all.
3. **Every scene gets one geography wide** (Aster dollhouse, Kubrick one-point) before or after its close-ups, so the viewer knows where the door, the closet and the window are. A static wide with empty space reads as "anything could come from there" (Flanagan, It Follows).
4. **Max one push-in per scene**, on its key beat (the POV push to the door, the realisation). In a row of shots, never two pushes back to back. Check the `SAME` rule and count the pushes.
5. **Vary three things between cuts:** size (wide/medium/close), angle (eye level, high, low, floor, top-down, dutch) and move (static, push, pull, arc, truck, follow, crane, rack).
6. **Angle carries meaning.** High (+20 to 35°) = small, trapped, watched. Top-down (60 to 80°) = fate, dollhouse. Low (−10 to −20°) = threat, the door, fake Mum/Milo. Floor level = the gap and the feet. Dutch 4 to 8° roll = something is wrong (the impostor, the phone). Never dutch a safe beat.
7. **Lens = distance to danger.** 24 to 30 mm wide = space and isolation (small sets). 40 to 50 = neutral. 60 to 85 long = compression and voyeurism ("someone is watching": through a door crack or a window).
8. **Swivel instead of reverse shot (Aster).** When a character turns to look, arc the camera with their head (`arc`) instead of cutting to a reverse. Withholding what they see keeps the tension.
9. **Imperfection (Arcane).** Panic shots (the run, the phone) get a small handheld float (`handheld(name, 0.004)`); calm shots get only `breathe()`. Never shake except the one big hit.
10. **Vertical frame:** use depth (z-axis): foreground occluders (door frame, bedpost) and something in the background; eyes in the upper third; headroom above as dread space; centre only for the stare to camera.
11. **The stare (Kubrick):** talking to the viewer = straight-on, centred, static, eyes to the lens.
12. **Rack focus** is a cut without a cut: a static frame that pulls focus from the foreground (Milo) to the background (the door) when the threat matters.
13. **Inserts:** land ON the detail (paper, gap, phone). Follow the moving object (the pencil, the paper sliding).

## Moves (`cinema.py` `cine(move=...)`)
| move | what | when |
|---|---|---|
| static | locked off | dread, the stare, geography wides, listening |
| hold | 3% creep | a line landing, near-static life |
| push | dolly in ≤25% | ONE realisation per scene, the POV push |
| pull | dolly out | reveal, isolation, the end of a beat |
| arc | orbit 15 to 35° at constant size | a head turn, swivel reveal, dialogue with energy |
| truck | lateral slide with parallax | past a foreground occluder; motivated by a walk |
| follow | tracks a moving subject (lag + settle) | runs, walks, a hand writing |
| crane | big height change (tilt 20°+) | top-down to eye level, rising above someone |
| rise / sink | small height change | looking up at a threat, a small lift |
| drift | slow orbit 6 to 8° | dialogue shots that need life |
| rack | static, focus pulls A→B | the threat in the background |

Every move eases in, lands at ~80% and settles (see `motion.py` timing). Fixed lens within a shot. `check_framing` must pass (OFF/CROP/DRIFT/SAME).

## Grade (`lookdev.cinematic_look`, see LIGHTING.md)
- Warm practicals against cool night: the light sources tell the temperature (Die Hard, Deakins). Graded as cool **shadows only**, so skin and the deepest blacks stay neutral. Tinted blacks look like an Instagram filter.
- Contrast from a real black, never a crushed one: print-film look (AgX Medium High Contrast), bloom on practicals, a little red halation round hot highlights, vignette.
- Palette by beat. Milo's room: cold moon plus warm night light. Yard: sodium orange against blue. Rae's house: warm tungsten (false safety). The 3AM clock: a red accent only.
