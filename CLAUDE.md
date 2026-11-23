# Joel's Roblox Shorts Studio (core)
Pipeline for Roblox-style animated Shorts in any genre: Blender 5.3 Python, shared engine + approved asset library, free low-res tests here, paid final renders on RunPod. This file is the core every thread needs. Genre rules are marked.

## Read only what the task needs (usage, Joel 23 Nov)
- Always: this file + `stories/<story>/STORY.md` for the ONE story you are on. Never read other stories.
- New story or spin-off: `stories/README.md` (how-to + template).
- Writing: `_pipeline/STORY_DIRECTION.md`; new voice: `_pipeline/VOICE_DESIGN.md`.
- Building scenes: `_pipeline/ENGINE.md`, `_pipeline/CAMERA.md`, `_pipeline/LIGHTING.md`; casting/assets: `_studio_library/README.md`.
- Pods: `_pipeline/RUNPOD.md`. Read source files only for the functions you touch.

## Start of every chat
1. `add_repo Joel52412/bloxbury (push)`, `git clone --depth 1 https://github.com/Joel52412/bloxbury /home/claude/bloxbury && sh /home/claude/bloxbury/_pipeline/restore.sh` (fills `/home/claude/{bloxbury-blender,studio_library/engine,talk,tools}` with every story's scripts + audio data, installs bpy).
2. After any change: commit + `git -c push.negotiate=true push`; laptop `C:\Users\frimp\Downloads\robloxshorts` is a git clone of `main`: after each merge update it with a git bundle (`_pipeline/LAPTOP.md`), not file copies. Laptop `device_bash` has ffmpeg.

## End of every chat (Joel 16:21)
Update the story's STORY.md Status (and Studio status below if shared things changed), condense any .md you touched (rules + current state only, no history), push, copy to the laptop, update the Project doc.

## Folders (repo and laptop identical)
```
_pipeline/        shared: scripts/ (rig2, cinema, director), audio_tools/ (mix.py kit, align, split, captions, visemes),
                  pod_*.sh, make_*.sh, playbooks (*.md)
_studio_library/  engine/ (library + scene_kit.py), manifest.json, approval_sheets/, README.md (catalogue)
_tools/           Render Monitor, library_audit.py, sets_audit.py, motion_audit.py, scene_fingerprint.py
assets/           music/ sfx/ fonts/ (shared)  voice_clones/ inspo/ (laptop)
stories/<story>/  STORY.md, scripts/ (<id>.py scenes, <id>_assets.py), audio/ (prep_<id>.py), data/<id>/,
                  partN/ (script, voice/<who>_<id>.mp3), exports/ (laptop), youtube/
```
- Part ids are unique across ALL stories (restore copies everything flat): Bloxbury `p1..pN`, a new story picks a 2-3 letter tag (`gb1`, `gb2`...). Scene/prep file names carry the id.
- Joel's files go straight to their place (music, sfx keep ElevenLabs names + all variants, voice → `stories/<story>/partN/voice`).
- Lean: no demo/test/preview files left behind (send them in chat). Mixes are stored only as FLAC (`*.wav` gitignored). Delete frames once an export is checked.

## Episode workflow (one part or a one-off)
1. **Story:** research, beat sheet + script → `stories/<story>/partN/`. Joel tweaks.
2. **Voices:** paste-ready ElevenLabs blocks, one per voice: one line per paragraph, [emotion] tags, no numbers; main character narrates. Request ALL the part's SFX now.
3. **Audio:** `align_full.py` (faster-whisper `small.en` mapped onto the script words; `ALIGN=sphinx` fallback), `split_lines.py`, scan every line for gaps >40 ms inside words and clicks (fix via `REPAIR` or ask for a regen), then `prep_<id>.py` on `mix.Mix` (cue/voice/sfx/silence/music/finish): loudnorm −16 LUFS / −2 dBTP, music ~20 dB under voices and ducked ~7 dB under speech, word-timed captions, lip-sync env with viseme codes.
4. **Audio animatic** (`make_animatic.py`, dark frame) → Joel judges pacing. Once the scene builds, `make_storyboard.py N` (each shot's first→last still cross-faded on the real mix + captions, ~10 s) replaces it and the stills sheet.
5. **Asset sheet** `<id>_assets.py` for every new character/set/prop (detail bar), low-res checks here, then final-quality stills on a pod (`pod_stills.sh`, 1× Secure 4090, ~$0.10) only after Joel OKs.
6. **After OK:** save to the library (cards, propsN.py, manifest, studio.py), switch the asset script to library versions.
7. **Scene** `<id>.py` on the scene kit: build here until `check_faces` + `check_shots` pass; animate only with `motion.py` + `mocap.py` (walks/runs `mo_walk`, natural actions `mo_clip`); storyboard animatic (`make_storyboard.py N`) → Joel. Then `check_motion` OK and **motion clips** of the 4-6 busiest moments (216×384, SAMPLES=4, batches <15 min) → Joel. Then **motion preview (hard gate):** whole part FREE here: `preview_local.py partN.py` (216×384 CPU, SAMPLES=4; one call = one ~12-min resumable batch, `--all` in the background runs them all, joins with mix + captions and runs motion_audit; Part 3 = 2023 frames in 30 min) → Joel watches with sound and says yes → final GPU render. `_tools/motion_audit.py` on preview AND final (with `shots_<id>.json`): fix every POP/JUDDER/FREEZE.
8. **TikTok:** `TIKTOK=1 prep_<id>.py`, copy `<stem>_tiktok.flac` to `data/<id>/` (pods make the cut via `tiktok_audio`), or by hand `make_tiktok.sh <part.mp4> <tiktok.flac> <out.mp4>` (94% picture with black borders).
9. Audit assets used; push anything new to the library.

## Hard rules
- **Library:** save only Joel-verified assets; ask before bulk saves; "full asset sheet" = show everything.
- **Look:** R6 characters, classic head, Roblox-makeable only. No glitch clipping (feet through floor, mug through face); unavoidable contact is fine. Hats get under-hat hair.
- **Hair:** dark skin never blonde/very light; white/grey only for older characters. Banned: downloaded .obj hair, faces A–E and M1, hair H1, H5, H6, H7.
- **Casting:** recurring characters have fixed cards (in their story); extras are random library mixes; monsters made fresh, saved only if approved.
- **Animation (Joel: "no AI-slop", "too much salt ruins the dish"):** subtle life, small overshoot, no tremble. Nothing snaps mid-shot or sits dead still; paths don't clip buildings; bottoms ON seats; props move with hands; quick actions are quick (5 frames + overshoot). Fluid Roblox-fight style (anticipation, overshoot, settle, motion blur, idle), never stop-motion. Faces match meaning and pitch. `look()` x>0 = head UP. Lip-sync from the speech (`rig2.lipsync` viseme codes), `check_lipsync(RIGS)` OK. **Narration = voiceover: mouth does not move**; lip-sync only for in-scene dialogue or to-camera.
- **Motion standards:** each channel keyed every frame OR on sparse Bezier keys, never mixed; every beat starts/ends at zero speed and blends (`motion._beat`); cross-fade, never pop, things that move in; no camera dead still >0.5 s; expressions ramp 4 frames; `check_motion` OK before any preview.
- **Camera (CAMERA.md):** 9:16, key details in the centre column; shots via `cine()`/`insert()`, never raw coords for characters; dolly not zoom; max one push per scene, moves ≤25% size change, eased, land ~80% then settle; vary size/move between cuts; inserts land ON the detail; `check_framing` passes. Zooms ending on nothing or cropped faces = fail.
- **Detail bar:** nothing ships as a plain block: 3+ readable sub-details per new asset; pictures/screens use generated images; cheap only (bevelled boxes, shared mats, emission, no glass/volumes, ≤5% render cost).
- **Sets:** dress what the camera sees (`props4.py`); max one practical light per room.
- **QA:** check_faces, check_shots (deliberate cases in `allow=`), shot stills reviewed, black/blank frame check after GPU render.
- **24 fps. Captions:** `captions.write_ass()`: bold yellow Poppins, ONE word at a time with a pop, y=66%; red = monster/fake, white = off-screen.
- **Length (Joel 23 Nov):** every video ~1 minute, max 1:10.
- **Hook:** frame 0 lit and readable; voice by 0.3 s with a strange claim a new viewer gets; something visibly wrong by ~3.5 s; cuts every 1.5–2 s for the first 6 s; recaps after the hook.
- **Story:** studio-grade first drafts; new open question every 8–10 s; pattern breaks; 1–2 rewatch details; last line loops to first; end on a choice question. (Horror: dread over loud stings, max one earned startle.)
- **SFX:** never synthesise real-world sounds; request ElevenLabs SFX from Joel (key-first prompt, duration, influence); level by RMS (files arrive ~−48 dB).
- **Ad-safe (horror):** creepy not gory; nothing graphic in the first 7 s or the thumbnail.
- **TikTok:** copyrighted music spans ≤55 s first-to-last (else muted); YouTube keeps the full mix.

## Rendering (details: `_pipeline/RUNPOD.md`)
- **Here (free):** low-res tests, stills, motion clips, storyboard and the whole-part motion preview, in batches under 15 min each. Final quality → RunPod. (Laptop: ASUS Vivobook, AMD integrated, no NVIDIA: no laptop renders.)
- **RunPod:** asset sheets, final (1080×1920, 32 samples, OptiX, `lookdev.cinematic_look()` grade). Before any pod: give $/hr, time and total cost per option (fastest in stock first, incl. 2×/3× GPUs); Joel must OK. Tell Joel when a render starts (pod ID, links, ETA, cost). Only delete pods made in this chat. Never print keys or tokens.

## Studio status (23 Nov)
- Parts 1-3 of BLOXBURY delivered. On main: motion fixes, speech-driven lip-sync + `talk_face`, shared scene kit + audio kit, pod hardening (watchdog, x264 export, auto TikTok + motion audit, FLAC mixes).
- Stories folder split (lean core + one folder per story) in review.
- Previews free (23 Nov): `preview_local.py` + `make_storyboard.py`. Laptop folder is a git clone of main (set up 23 Nov).
- TODO: GHCR render image private (use runpod/pytorch).
