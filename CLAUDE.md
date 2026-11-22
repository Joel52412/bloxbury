# Bloxbury Studio
Joel's Roblox-style horror Shorts, **BLOXBURY: The 3AM Knock**. Blender 5.3 Python, rendered on RunPod. Reusable asset library + scripted scenes.

## Start of every chat
1. `add_repo Joel52412/bloxbury (push)`, then `git clone --depth 1 https://github.com/Joel52412/bloxbury /home/claude/bloxbury && sh /home/claude/bloxbury/_pipeline/restore.sh` (fills `/home/claude/{bloxbury-blender,studio_library/engine,talk,tools}`, installs bpy).
2. After any change: commit + `git -c push.negotiate=true push`; copy changed files to `C:\Users\frimp\Downloads\robloxshorts` if connected (device_commit_files). Laptop `device_bash` has ffmpeg (remux there, no upload needed).

## End of every chat (Joel 16:21)
Update Status, then condense every .md (this file, `_pipeline/*.md`, scripts' notes): keep only rules and current state, cut history, duplicates and filler (fewer words = less usage). Push, copy to the laptop, update the Project doc.

## Folders (repo and laptop identical)
```
_pipeline/        scripts/ (scenes, director.py), audio_tools/ (prep_pN.py cue sheets), data/pN/ (env, captions, mix), pod_*.sh, make_*.sh
_studio_library/  engine/ (library .py), manifest.json, approval_sheets/
_tools/           Render Monitor, library_audit.py, sets_audit.py, audit_sheet.py
assets/           music/  sfx/  voice_clones/ (laptop)  inspo/ (laptop)
series/<story>/   partN/ (script, voice/<voice>_pN.mp3)  exports/ (mp4s, laptop)  youtube/make_youtube.sh
```
- Every file Joel sends goes straight to its section (music, sfx keep ElevenLabs names + all variants, voice → partN/voice).
- Lean: no demo/test/preview/check files left behind (send those in chat). TikTok mixes are regenerated, not stored. Delete frames once an export is checked.

## Episode workflow
1. **Story:** read `_pipeline/STORY_DIRECTION.md`, research, write beat sheet + script → `series/<story>/partN/partN_script.md`. Joel tweaks.
2. **Voices:** paste-ready ElevenLabs blocks, one per voice: one line per paragraph, [emotion] tags, no numbers; main character narrates. New speaking character → Voice Design prompt (`_pipeline/VOICE_DESIGN.md`). Request ALL the part's SFX now (same file).
3. **Audio:** align (`align_full.py`), split (`split_lines.py`), scan every line for gaps >40 ms inside words and clicks (fix via `REPAIR` in the cue sheet or ask for a regen), then `prep_pN.py`: pacing, level matching, voice FX, music bed + dropouts, SFX, loudnorm −14 LUFS, word-timed captions, lip-sync env (line modes N/D/C/O).
4. **Audio animatic** (dark frame + captions + scene labels + timecode) → Joel judges pacing.
5. **Asset sheet** `partN_assets.py`, rendered here (detail bar applies): every new character/set/prop (sets at z=400, studio cyc for cards), NEW vs APPROVED panel. Review stills first. No pod until Joel OKs.
6. **After OK:** save to library (`recurring.py` cards, `propsN.py`, manifest, studio.py), switch the asset script to library versions.
7. **Scene** `partN.py` from the previous part: build here (~10 s) until `check_faces` and `check_shots` pass; render one still per shot here (216×384) into a contact sheet → Joel. Then price OK → GPU render → pod auto-finish → Render Monitor downloads to `exports/` → pod deletes itself.
8. **TikTok:** `TIKTOK=1 prep_pN.py`, then `make_tiktok.sh <part.mp4> <tiktok.wav> <Bloxbury_PartN_TikTok.mp4>` (keeps 94% picture with black borders: TikTok's zoom crops them off. Joel 16:05).
9. Audit assets used; push anything not in the library.

## Hard rules
- **Library:** save only Joel-verified assets; ask before bulk saves; "full asset sheet" = show everything.
- **Look:** R6 characters, classic head, Roblox-makeable only. No glitch clipping (toaster through table, feet through floor, mug through face); unavoidable contact (hugs, tools in hands) is fine. Hats get under-hat hair.
- **Hair:** dark skin never blonde/very light; white/grey only for older characters; keep a/b versions of B4, C19, K11. Banned: downloaded .obj hair, faces A–E and M1, hair H1, H5, H6, H7.
- **Casting:** recurring characters have fixed cards; extras are random library mixes; monsters made fresh, saved only if approved.
- **Animation:** fluid Roblox-fight style (anticipation, overshoot, settle, smear frames, motion blur, idle motion), never stop-motion. Faces match meaning and pitch. Anime lip-sync. Sparkles twinkle subtly, never flicker. **Narration = voiceover: mouth does not move**; lip-sync only for in-scene dialogue or talking straight to camera (outro).
- **Camera:** calm, eased moves; shake only as a small jolt on the one big hit. Shots via `cinema.py` `cine()`/`insert()` (subject + size + move), never raw coords for character shots. Dolly, never zoom (fixed lens per shot); moves ≤25% size change, land at ~80% then settle; eyes upper third, looking room; vary size/move between cuts (hold, push, pull reveal, drift, sink); inserts land ON the key detail. `check_framing` (OFF/CROP/DRIFT/SAME) must pass. Joel 22 Nov: zooms that end on nothing / cropped faces = fail.
- **Detail bar (Joel 21:11):** nothing ships as a plain block. Every new asset gets 3+ readable sub-details at its shot size (trim/edges, a working part, a surface break, a story/life detail); pictures/screens/labels use generated images, never flat colour. Cheap only: bevelled boxes, shared materials, emission glows, no glass/volumes; measure render cost before/after (≤5%). Asset sheets: new assets + `_tools/library_audit.py` / `sets_audit.py` front-view renders, current vs new.
- **Sets:** dress what the camera sees (walls behind faces) with `props4.py` (two-tone walls, frames, shelves, coats, sconces, calendar/drawing rewatch bait). Cheap: boxes, shared mats, emission glows, max one practical light per room, no glass/volume (+~2% render time measured).
- **QA:** check_faces (one mouth every frame, no closed eyes before a cut); check_shots (no camera in a mesh, nothing blocking the aim point or lens; deliberate cases in `allow=`); shot stills sheet reviewed; after GPU render, black/blank frame check.
- **24 fps.** Captions small, lower-middle, clear of faces, word-timed (pocketsphinx).
- **Story:** studio-grade first drafts. Hook picture + line in 0–3 s; new open question every 8–10 s; pattern breaks; pay off earlier parts; retell half-known legends made wrong; no cliché loud stings (silence, dropouts, misdirection, reflections, quiet lines), max one earned startle; 1–2 rewatch details; last line loops to first; end on a choice question.
- **SFX:** never synthesise real-world sounds; request ElevenLabs SFX from Joel (key-first prompt, duration, influence). ElevenLabs files arrive ~−48 dB: set level by RMS in the cue sheet.
- **Ad-safe:** creepy not gory; nothing graphic in the first 7 s or the thumbnail.
- **TikTok:** copyrighted music must span ≤55 s first-to-last (else muted); YouTube keeps the full mix.

## Rendering
- **Here (free):** asset sheets, shot stills, tests. **RunPod:** only the full-res final (1080×1920, 32 samples, OptiX, `QUALITY=fast`).
- **Before creating a pod:** give hourly price, total time, total cost per option incl. 2×/3× GPUs; Joel must OK. Only delete pods made in this chat. Never print API keys or tokens.
- **Cards:** default 3× Community RTX 4090 ($0.34/hr each); Secure 4090 $0.89/hr; A40 Secure $0.59/hr. Always `allowedCudaVersions: ["13.2"]` (inside `gpu`): 13.0 Community 4090s were broken 3 times. Check torch CUDA in the first minute; delete if broken. Speeds: ~1.5 s/frame per 4090, ~3 s per A40.
- **Create body:** image `ghcr.io/joel52412/bloxbury-render:5.3` (Blender at /opt/blender; fallback `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`), disk 30, port 8888/http, startJupyter, `env: {"GITHUB_RO": "{{ RUNPOD_SECRET_GITHUB_RO }}"}` at create time (changing env later wipes the pod).
- **On the pod:** `T=$(tr '\0' '\n' < /proc/1/environ | sed -n 's/^GITHUB_RO=//p')`; `git clone --depth 1 https://x-access-token:$T@github.com/Joel52412/bloxbury.git /workspace/bloxbury`; `nohup sh /workspace/bloxbury/_pipeline/pod_setup.sh > setup.log &` (<1 min). Token is read-only: pods never push.
- **Render:** write `/workspace/render_job.json` first (`name, group, total, frame_start, frame_end, cost_per_hr, pod_started, output, audio, captions, black, download_to=series/bloxbury/exports/...`), then `sh /workspace/bloxbury/_pipeline/pod_render.sh partN.py <NF> /workspace/frames` (one shared frame queue across GPUs + progress file + balancer + auto-finish). `exec-pod` calls max 25 s: use nohup.
- **Auto-finish:** `pod_finish.sh` checks frames, assembles (`make_part.sh`), the Render Monitor downloads and writes `received.json`, the pod deletes itself (`runpodctl`: confirm which syntax works on the next pod). No download in 60 min → pod stops itself. Failure → stage `needs_claude`.
- **Tell Joel when a render starts:** pod id, Jupyter token, frames link `https://<pod>-8888.proxy.runpod.net/tree/workspace/frames?token=<token>`, cards + $/hr, frames, ETA, estimated cost, and the backup download link `.../files/workspace/<file>?token=<token>`. Render Monitor (`_tools/Render Monitor.bat`) shows it live.
- **Pod → Claude images:** small contact-sheet JPG printed as base64 via exec-pod (≤1 MiB stdout).
- Spot pods: GraphQL only, can't be created here.

## Engine
- Load order: `bloxbury_part1.py` prefix (to `# Milo starts at the fence`), charlib, stylelab, hair2, hair3, faces2, garments, garments2, hair4, faces3, faces4, props, studio, then recurring, props2, props3, props4, props5 (+ `detail_town(houses)` after the town), monster.
- Registry `studio.py`: CAST tags F1–F6, B1–B6, C1–C24, K1–K12, `studio_character(tag)`.
- Approved: faces M2 (+12 emotions, faces4.RARE); hair H2 H3 H4 H8, M1–M6, X1–X6; outfits O1–O4 + role/kids/teen; props batches 1–5 (4 = set dressing `dress_kitchen/hallway/bedroom` + wall/room pieces; 5 = town detail `detail_town`/`detail_house`; batch-2 props upgraded); sets Bloxbury Town, Milo's room, kitchen, hallway (mirror), hollow closet; cards MILO (`rig2.make_milo`), RAE, MAYOR, DAN, NEIGHBOUR, MUM (`recurring.py`); THE KNOCKER (`monster.make_knocker`).
- Scene template: `part2.py` (+ `rig2.py`: `upgrade_rig`, `arm`, `build_face_v2`, `expr`, `blink`, `lipsync`, `accents`; walk cycle; smears = shoulder Z ×1.35 for 2 frames; motion blur 0.5 position START; `cam_key` with make_compatible).
- Helpers/lessons: `place()` + `hold_cuts()` + `flush_mouths()`; use `idle_here()` (idle() keys absolute z); aim shots BEFORE parking characters; character shots via `cine()` (ots() is legacy); emission sockets keyed with `key()`; Blender 5 needs `kf()`, `apply_interp()`, `_fcurves()`; DOF keyed on `cam.data`; no coplanar faces; check held-prop contact numerically; cups hollow. Glossy-only objects (`visible_glossy`) for mirror/reflection tricks.
- `cinema.py` sets the 1080×1920 resolution before any maths (sensor fit uses the long side). Sizes = head fraction of frame height: ECU .40, CU .28, MCU .19, MS .12; small sets need short lenses (26–36) or the camera ends up in a wall.
- Stills: `RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 partN.py`.

## Series so far
- **Part 1** (71.75 s, `part1_v2.py`, `prep_p1.py`): Milo hears knocks at 3AM; the Knocker (tall, starved, black sockets with pinpoint white eyes, red thin-tooth grin; always kept in the dark with a cool rim light) is in his closet; lunge at the lens on "OUT", cut to black. Rae keeps the WHO'S LEFT list.
- **Part 2 "She Came Home"** (80 s, 1921 frames, `part2.py`, `prep_p2.py`, script in `series/bloxbury/part2/`): Mum is back making pancakes but calls him "Milo" (she never does). Rae: Mum was crossed off the list three weeks ago; "mirrors don't lie". The hallway mirror's twin keeps smiling and turns. Real Mum whispers from the closet "I heard it too"; fake Mum knocks: "Who are you talking to?" Outro: "Two mums. One door. Which one would you open?" Music: Numbers instrumental loop (`assets/music`), 35%.

## Status (22 Nov 21:15)
- Part 1 and Part 2 delivered. `exports/Bloxbury_Part2_TikTok.mp4` final; YouTube master needs `_pipeline/data/p2/part2_audio.wav` swapped in when stitching.
- Approved today: `cinema.py` camera grammar; `props4.py` set dressing; `props5.py` town detail + batch-2 prop upgrades (sheet `approval_sheets/Library_detail_pass.jpg`). `part2.py` uses all of it (all checks pass); Part 2 NOT re-rendered — Joel to decide (~1921 frames, 3× 4090 ≈ 16 min).
- TODO: wire `make_tiktok.sh` into `pod_finish.sh`.
- **NEXT: Part 3** (template `part2.py`: cine shots, props4 dressing, props5 town, detail bar for every new asset).
