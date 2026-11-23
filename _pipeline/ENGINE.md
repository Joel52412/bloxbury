# Engine notes (read when building scenes)

## Scene kit (`_studio_library/engine/scene_kit.py`)
A scene script = settings + beats:
```
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
boot("<id>", world="<world>", patches=...)     # world, engine, rig2 (+monster), env_<id>.json, timeline, helpers
load("recurring", "props2", ...)                # library batches
a, b = cast(a=(maker, "rest_flat"), ...)        # RIGS, CAST, park()
camera_rig(); load("cinema", "motion")
... beats: place/at, gesture/look/lean, say(...), cine(...)/insert(...), live(...) ...
finish_part(life=True, allow=(...), motion_chars={...}, quiet=(...))   # blinks, mouths, life, every check, render
```
- Fix shared helpers ONCE in the kit. Kit helpers beat same-name ones in world/asset files; cinema/motion/director beat the kit.
- **Worlds:** a base set is a `@world("name")` builder. A story with its own setting defines one in its scene script (after the kit exec, before `boot`) or, once reused, in the kit. Bloxbury's world is `bloxbury` (see its STORY.md).
- Asset load order inside the kit: charlib, stylelab, hair2, hair3, faces2, garments, garments2, hair4, faces3, faces4, props; then recurring, props2-6, lookdev, monster as needed.
- Before/after any kit or engine change: `_tools/scene_fingerprint.py` on every part (identical scene + checks).
- Stills: `RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 <id>.py` (from `/home/claude/bloxbury-blender`).

## Rig + motion
- `rig2.py`: `upgrade_rig`, `arm`, `build_face_v2`, `expr`, `blink`, `lipsync`, `accents`; walk cycle; smears = shoulder Z ×1.35 for 2 frames; motion blur 0.5 position START; `cam_key` with make_compatible.
- `motion.py` only: gesture/look/lean (wind-up + overshoot + settle), `run`, `sit_down`/`seated`, `life()` windows on every visible character, `bake_life()` at the end. `EXPR_RAMP` 4 frames; `accents` nods and `shake` jolts eased per frame; shake only as a small jolt on the one big hit.
- Lip-sync: `rig2.lipsync` reads env viseme codes (closed on M/B/P, teeth on F/V, 2-frame holds, mouth 1 frame ahead of the sound); loudness flap is only a fallback for envs without `vis_all`. Sparkles twinkle subtly, never flicker.
- Before calling a render smooth: diff consecutive frames of the export (3-frame autocorrelation, freezes, single-frame spikes) = `motion_audit.py`.

## Helpers / lessons
- `place()` + `hold_cuts()` + `flush_mouths()`; `idle_here()` (idle() keys absolute z); aim shots BEFORE parking characters; `ots()` is legacy.
- Emission sockets keyed with `key()`; Blender 5 needs `kf()`, `apply_interp()`, `_fcurves()`; DOF keyed on `cam.data`; no coplanar faces; check held-prop contact numerically; cups hollow; glossy-only objects (`visible_glossy`) for mirror tricks.
- `cinema.py` sets 1080×1920 before any maths. Sizes = head fraction of frame height: ECU .40, CU .28, MCU .19, MS .12; small sets need short lenses (26–36).
- Every shot: `lookdev.cinematic_look()` grade (+3% render) and LIGHTING.md (motivated short-side key, low fill, opposite-temperature rim, cookies, palette by beat).
