# Bloxbury Studio: pipeline map
Joel makes Roblox-style animated horror Shorts. The series is **BLOXBURY: The 3AM Knock**, made in **Blender 5.3 Python** and rendered on **RunPod**. It's a studio workflow: a reusable asset library plus scripted scenes.

## Start of every chat
1. **Restore from GitHub** (private repo `Joel52412/bloxbury`, mirrors `robloxshorts` minus frames, .blend, .mp4, inspo, voice clones):
   `add_repo Joel52412/bloxbury (push)`, then `git clone --depth 1 https://github.com/Joel52412/bloxbury /home/claude/bloxbury && sh /home/claude/bloxbury/_pipeline/restore.sh`.
   `restore.sh` takes the repo root (default: its parent folder) and rebuilds `/home/claude/{bloxbury-blender,studio_library/engine,talk,tools}` and pip-installs bpy.
2. **After changing anything:** commit and push to the repo (`git -c push.negotiate=true push`), and copy changed files into `C:\Users\frimp\Downloads\robloxshorts` too if the folder is connected (device_commit_files).
3. **Laptop folder** is only needed for frames, .blend files or new audio Joel adds. Folders connect per chat: if Joel has said OK, `device_request_folder_access` on `C:\Users\frimp\Downloads\robloxshorts` works; otherwise ask him to use **+ → Add folder**. New audio Joel drops in the folder must be pushed to the repo.
4. **New stories** go in `series/<story>/` beside `series/bloxbury/`, sharing the engine and library.

## Folder map (Joel, 22 Nov 15:40): the laptop folder and the repo use the same layout
```
robloxshorts/
  CLAUDE.md  README.md          this map + rules
  _pipeline/                    code: scripts/ (scenes), audio_tools/ (cue sheets), pod_*.sh, make_*.sh, data/ (env, captions, mixes per part)
  _studio_library/              engine/ (characters, props, sets), manifest.json, approval_sheets/
  _tools/                       Render Monitor
  assets/                       EVERYTHING REUSABLE Joel gives Claude
    music/                      source songs + approved loops (Numbers.mp3, Numbers_instrumental_loop.flac)
    sfx/                        ElevenLabs SFX, named by prompt key + variant (pan_sizzle #1/#4, knocks, drones...)
    voice_clones/               ElevenLabs voice samples (laptop only)
    inspo/                      reference videos (laptop only)
  series/<story>/
    partN/                      partN_script.md, voice/ (that part's recordings <voice>_pN.mp3), asset sheet
    exports/                    finished videos: Bloxbury_PartN.mp4 (YouTube master), _TikTok.mp4 (laptop only)
    youtube/                    make_youtube.sh (stitches exports/ into the compilation)
```
- **Intake rule:** every file Joel sends goes straight to its section: music → `assets/music/`, sound effects → `assets/sfx/` (keep ElevenLabs' names, all variants), voice recordings → `series/<story>/partN/voice/`, voice samples → `assets/voice_clones/`, reference clips → `assets/inspo/`. Push the repo copy and put the laptop copy in the same place.
- **Keep it lean:** no demo/listen files, test clips, previews, check images or duplicate formats left behind. Anything Claude makes only for Joel to hear or look at is sent in chat, not saved in the folder. Mixes live once in `_pipeline/data/pN/`; TikTok mixes are regenerated (`TIKTOK=1`), not stored. Delete a part's frames once its export is checked.

## Episode workflow (Joel, 22 Nov; Part 2 run approved as "the flow" 13:27), required for every new part
1. **Story:** read `_pipeline/STORY_DIRECTION.md`, research what's needed, write the beat sheet + script (`series/<story>/partN/partN_script.md`). Joel tweaks.
2. **Voices:** ElevenLabs blocks per voice; any NEW speaking character gets a Voice Design prompt + preview text + guidance (`_pipeline/VOICE_DESIGN.md`).
3. **Recordings in → audio first:** save as `series/<story>/partN/voice/<voice>_pN.mp3`; force-align (`audio_tools/align_full.py`), split into lines (`split_lines.py`, cuts in ElevenLabs' digital silence, check each cut), then `prep_pN.py` = the cue sheet: pacing (Claude directs it, Joel allows edits), voice level matching, voice FX, music bed + dropouts, sound design, loudnorm −14 LUFS, captions, per-speaker lip-sync env with line modes N/D/C/O.
4. **Audio animatic:** render the full audio over a dark frame with captions + scene labels + timecode; send it so Joel can judge pacing. Fix his sound notes straight away.
5. **Full asset sheet:** `partN_assets.py` (rendered here in the workspace: quick) builds every new character/set/prop (new sets in the air at z=400, studio cyc for character cards, `only()` to hide the rest), renders stills, composes one sheet with captions + a NEW / ALREADY APPROVED panel. Review every still yourself first (contact sheet) and fix clipping/composition before sending. **No pod is created until Joel OKs it.**
6. **After the OK:** save the approved assets to the library straight away (cards in `recurring.py`, props/sets in a `propsN.py` batch, `manifest.json`, `studio.py`), switch the asset script to the library versions and re-check a few stills.
7. **Scene (no low-res preview since 22 Nov 15:05):** `partN.py` from the previous part's scene script. Build it here (about 10 s) until `check_faces` AND `check_shots` (`_pipeline/scripts/director.py`) both pass. Then render one still per shot here (mid-frame, 216×384, about 3 s each) into a shot contact sheet, review it, and send it to Joel. Then Joel's OK on the price (hourly, total time, total cost, incl. 2×/3×), then the GPU render. The pod checks frames, assembles the video, the Render Monitor downloads it into `series/<story>/exports/`, and the pod deletes itself (see RunPod → Auto-finish).
8. **When finished:** audit every asset used and push anything not yet in the library.

## Hard rules
- **Library:**
  - Save only assets Joel has verified.
  - Ask before bulk saves.
  - "Full asset sheet" means show everything.
- **Look:**
  - R6 Roblox characters, classic head, only designs makeable in Roblox.
  - **No glitch clipping (Joel 13:33):** props or bodies passing through things they shouldn't (a toaster through a table, feet through a floor, a mug through a face). Contact clipping that can't be avoided is fine: hugs, fist bumps, tools in hands. Hats get under-hat hair.
- **Hair colour:**
  - Dark skin never gets blonde or very light hair.
  - White or grey hair only for older characters.
  - Keep "a" (light) and "b" (dark) versions of B4, C19, K11.
- **Banned:**
  - The downloaded .obj hair.
  - Faces A–E and M1.
  - Hair H1, H5, H6, H7.
- **Casting:**
  - Recurring characters get fixed cards.
  - Extras are random library mixes.
  - Unique monsters are made fresh and saved only if approved.
- **Animation:**
  - Fluid like Roblox fight animations: anticipation, overshoot and settle, snappy timing, **smear frames**, motion blur, idle motion. Never stop-motion.
  - Faces match the line's **meaning and voice pitch**.
  - Anime lip-sync (current method approved).
  - Sparkle eyes: a subtle twinkle only, never flicker.
  - **Narration is voiceover (Joel, 22 Nov):** when a character narrates to the viewer, their mouth does **not** move. Lip-sync only for in-scene dialogue (talking to another character) or when the character looks straight into the camera and talks to us (e.g. the outro). Narrating characters keep a resting mouth and act with their face and body only.
- **Camera (Joel, 22 Nov):** keep camera moves **calm and fluid**, like other channels' videos. Use slow, eased push-ins and gentle drifts. Keep shake to rare, small jolts on the biggest hits (the jump scare). No big lens or position swings inside a shot, and no punchy multi-key shakes on ordinary lines.
- **QA before sending anything:**
  - `check_faces` passes: one mouth every frame, no closed eyes right before a cut.
  - `check_shots` passes: no camera inside a mesh, nothing between the lens and the aim point, nothing covering the lens. Intentional cases (the lunge at the lens) go in `allow=`. It caught Part 2's B3 push-in ending inside Milo's hair (fixed in `part2.py`).
  - A per-shot stills contact sheet (rendered here) is reviewed before the GPU render. The low-res pod preview is retired.
  - After the GPU render, automated checks for black or blank frames.
- **24 fps** (20% cheaper than 30).
- **Captions:**
  - Small, lower-middle, clear of faces.
  - Word-timed with pocketsphinx alignment.
- **Directing:** punch-ins on key words, slow push-ins for tension, hard cuts, follow the action.
- **Story and scares (Joel, 22 Nov): studio-grade, never generic.** Joel wants every first draft at full quality, not slop.
  - **Retention:** hook with picture and line together in the first 1–3 s. Open a new question every ~8–10 s before closing the last one. Use pattern breaks (three normal things, then one wrong one). Pay off earlier parts' mysteries so returning viewers are rewarded.
  - **Familiar made wrong:** retell a story people half-know (urban legends, viral creepypastas) in the Roblox format. A familiar person, room or voice that is slightly off beats any monster.
  - **No cliché loud-sting jump scares.** Use silence and audio dropouts, misdirection (the scare is somewhere other than where the camera points), delayed reflections, things in plain sight, quiet lines that land like a hit, and the music cutting out. Keep at most one real startle per part, and earn it.
  - **Full reasoning and method:** `_pipeline/STORY_DIRECTION.md` (research, beat-sheet method, scare toolkit). Read it before writing any part.
  - **Rewatch bait:** hide one or two background details (e.g. a 4-frame reflection) that reward a second watch. Make the last line flow into the first so TikTok loops cleanly. End with a choice question for comments.
- **Voice design (Joel, 22 Nov):** every new speaking character gets an ElevenLabs Voice Design prompt, preview text and settings from Claude. Formula and cast list: `_pipeline/VOICE_DESIGN.md` (Mum is there).
- **Sound effects (Joel, 22 Nov 15:25):** never fake real-world sounds with synthesised noise. For any SFX not in `assets/sfx/`, send Joel an ElevenLabs Sound Effects request (prompt starting with the file key, duration, prompt influence): format and request list in `_pipeline/VOICE_DESIGN.md` → SFX requests. Ask for all of a part's SFX in one go, at the audio step.
- **Voiceover scripts:**
  - Paste-ready blocks for ElevenLabs.
  - One line per paragraph, [emotion] tags, no numbers.
  - One block per voice; the main character narrates.

## Where things render (Joel, 22 Nov 14:03)
- **In Claude's workspace:**
  - Asset-sheet stills, test stills and quick generations (a handful of frames). Measured: about 6–7 min for a full 10-still sheet, free.
  - A new pod would take 12–15 min for the same job, because setup alone is 8–12 min.
- **On RunPod GPUs (they're there to save time):**
  - Only the full-res final (the low-res preview was retired 22 Nov 15:05; per-shot stills + `check_shots` here replace it).
- **One pod per episode:** setup (under 1 min with the ready-made image) → full-res render (1080×1920, 32 samples) → the pod checks frames and assembles the video itself → the Render Monitor downloads it → the pod deletes itself. The price rule below still applies before creating it.

## RunPod
- **Before you create:** state the price first, and Joel must OK pod creation (the auto-check can block it). When offering cards, give each option's **hourly price, total time and total cost**, and always include **multi-GPU options** (2×, 3×).
- **Pod ownership:** only delete pods made in this chat, and never print the API key or the GitHub token.
- **CUDA rule (22 Nov, a 3rd broken Community 4090 on CUDA 13.0, pod eyntfwr3g1c478, deleted after 1 min):** always create with `allowedCudaVersions: ["13.2"]`. A Community 4090 on any other CUDA version has failed every time. If 13.2 has no stock, offer Secure or another card; don't drop the filter.
- **Card choice:** episodes go on **3× Community RTX 4090** ($0.34/hr each, about 58p per episode). Tests use 1–2×. Community stock often runs out (and `get-capacity` can be stale). Secure 4090 is $0.89/hr. `allowedCudaVersions` goes inside `gpu`.
- **Speed (Test 2 scene, 1080×1920, 32 samples):** about 5.3 s per frame per 4090.
- **Render settings:** 32 samples, OptiX denoise, `QUALITY=fast` (19% quicker, looks the same). Test each GPU with a `FRAMES=` still first, then check every frame.
- **Ready-made image (22 Nov 14:44):** `ghcr.io/joel52412/bloxbury-render:5.3` is RunPod's PyTorch base plus Blender 5.3 at `/opt/blender`, its libs, ffmpeg, fonts and pillow/numpy.
  - Built by GitHub Actions (`.github/workflows/render-image.yml`, from `docker/render.Dockerfile`), about 12 min. It rebuilds whenever the Dockerfile changes.
  - With it, `pod_setup.sh` skips installing (it links `/opt/blender`), so setup drops from about 10 min to under a minute. That makes 4–6 GPUs worth it.
  - The GHCR package must be **Public** for RunPod to pull it without credentials (Joel sets it once in GitHub → Packages → bloxbury-render → Package settings). It holds no code or secrets.
  - Fallback if the pull fails: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, which does the full install.
- **Create body:** image `ghcr.io/joel52412/bloxbury-render:5.3` (fallback `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`), disk 30, port 8888/http, startJupyter, and `env: {"GITHUB_RO": "{{ RUNPOD_SECRET_GITHUB_RO }}"}` **at create time**. Changing env later with update-pod restarts the container, wipes it and drops Jupyter's password. If that happens, restart Jupyter by hand with your own token.
- **Getting the code onto the pod (no more base64 chunks):**
  - Token: `T=$(tr '\0' '\n' < /proc/1/environ | sed -n 's/^GITHUB_RO=//p')`.
  - Clone: `git clone --depth 1 https://x-access-token:$T@github.com/Joel52412/bloxbury.git /workspace/bloxbury`.
  - Then `nohup sh /workspace/bloxbury/_pipeline/pod_setup.sh > setup.log &`. It installs apt packages and Blender 5.3 (note: no `-q` on `ensurepip`), and lays files out under `/home/claude`.
  - RunPod secret `GITHUB_RO` (id `we7rf4p3y8`) holds Joel's fine-grained token "robloxrepo" for this repo. **Read-only since 22 Nov 15:02** (Joel set Contents to Read-only), so pods can clone and pull but NEVER push.
- **Multi-GPU (22 Nov 14:30): one shared frame queue.** `sh /workspace/bloxbury/_pipeline/pod_render.sh partN.py <NF> /workspace/frames` starts one Blender per GPU, every one over the WHOLE range (FS=1, FE=N). Blender placeholders make each GPU claim the next free frame, so a slow GPU never holds the finish back.
  - It also starts `pod_progress.py`, which writes the tiny `/workspace/render_progress.json` every 2 s: done/total, fps over the last 90 s, ETA, and per-GPU frames from the `render_gpuN*.log` "Saved:" lines.
  - It also starts `pod_balance.sh`, which restarts a helper on any GPU that goes idle while unclaimed frames remain.
  - Part 2 found the problem: with the old static split, GPU 0 (kitchen frames) ran at 0.27 fps against 0.40 on GPU 2.
- **Auto-finish (22 Nov 15:20):** `pod_render.sh` also starts `pod_finish.sh`. When the last frame is done it runs `check_frames.py`, assembles with the generic `_pipeline/make_part.sh <frames> <out.mp4> <audio.wav> <captions.ass>`, and writes `/workspace/render_output.json` (stage rendering → checking → assembling → ready → received; or needs_claude / stopped_no_download).
  - The Render Monitor sees `ready`, downloads the video to `download_to` (relative to the robloxshorts folder, never overwriting: a clash gets a time suffix), checks the size, and writes `/workspace/received.json`. The pod then deletes itself with `runpodctl` (tries `pod delete`, `pod remove`, `remove pod`: verify which works on the next pod).
  - No download within 60 min: the pod STOPS itself (disk kept, almost free) and Claude takes over.
  - Frame check or assembly failure: stage `needs_claude`, the pod stays up.
  - Still **give Joel the full download link** with the token in it as a backup: `https://<pod>-8888.proxy.runpod.net/files/workspace/<file>?token=<jupyter token>`. If the monitor isn't running, delete the pod after he confirms.
- **Getting previews and stills from a pod to Claude (since 15:02 the token is read-only, so no more `preview-*` branches):**
  - Make a small contact-sheet JPG on the pod (under about 700 KB) and print it as base64 through `exec-pod`. stdout holds up to 1 MiB, so split bigger sheets into parts.
  - Decode it in the workspace and view it.
  - Joel can also open the Jupyter frames link.
  - Leftover branches `preview-part1-v2` and `preview-part2` can only be deleted by Joel on GitHub; the workspace proxy blocks branch deletes.
- **Long jobs:** use `nohup`; `exec-pod` calls max out at 25 s.
- **Tracking (Joel, 22 Nov 14:18):** the moment a render starts, send Joel the tracking block without being asked:
  - pod id, Jupyter token, and the Jupyter frames-folder link (`https://<pod>-8888.proxy.runpod.net/tree/workspace/frames?token=<token>`)
  - cards and price per hour, frames done/total, estimated finish time and estimated total cost
  - a reminder that `_tools/Render Monitor.bat` shows it live
- **Render Monitor (`_tools/render_monitor.py`, redesigned 22 Nov 14:30):**
  - Polls laptop folders every 2 s and pods every 5 s. On a pod it reads only `render_progress.json`; the full folder listing is a fallback, at most every 30 s, for older pods.
  - The ETA comes from the pod's live speed, so it updates when the render speeds up or slows down.
  - Each job is a card: progress bar, frames, time left, finish clock, speed, running time, cost (spent / estimated total) and per-GPU lanes.
  - Live window title, an "Open frames" button (Jupyter link), and a beep + bring-to-front when a render finishes.
- **Render monitor:** write `/workspace/render_job.json` BEFORE starting the render: `name`, `group`, `total`, `frame_start`, `frame_end`, `cost_per_hr`, `pod_started` (the pod's createdAt, which shows spend), plus for auto-finish `output` (e.g. `Bloxbury_Part3.mp4`), `audio` and `captions` (pod paths), `black` (deliberate black frame ranges for check_frames, e.g. `"1738-1752"`) and `download_to` (e.g. `series/bloxbury/exports/Bloxbury_Part3.mp4`). Give Joel the pod id and Jupyter token.
- **Spot / interruptible pods (checked 22 Nov):** about half price, but they can only be made through RunPod's GraphQL API (`podRentInterruptable`), which the MCP tools and REST v2 don't have, so Claude can't create them. `pod_render.sh` is resume-safe (it deletes 0-byte placeholders on start), so a manual spot pod (console + same image) could be restarted after an eviction. Not used by default.
- **Render quality (tested 22 Nov):** `director.render_quality(s, QUALITY)`, env `QUALITY=full|fast|turbo`. Same 32 samples + denoise; fast trims bounces (diffuse/glossy 2), adaptive threshold 0.04, no caustics: **19% faster, looks the same**. Turbo (1 bounce, 0.06): 36% faster, but corners and the bedroom go darker and flatter. Side-by-side: `_studio_library/approval_sheets/render_quality_test.png`. **Joel picked `fast` (22 Nov 15:23): it's the default in `part2.py` and every new part.**

## Engine
- **Load order:** the `bloxbury_part1.py` prefix (up to `# Milo starts at the fence`), then charlib, stylelab, hair2, hair3, faces2, garments, garments2, hair4, faces3, faces4, props (and studio for the registry).
- **Registry:** `studio.py`, with `CAST` tags F1–F6, B1–B6, C1–C24, K1–K12 and `studio_character(tag)`.
- **Approved assets:**
  - **Faces:** M2, shine at 70% opacity, 12 emotions, plus `faces4.RARE` (14 faces).
  - **Hair:** H2, H3, H4, H8; M1–M6; X1–X6.
  - **Outfits:** O1–O4, plus role, kids and teen outfits.
  - **Props batch 1:** cars, house furniture, kitchen, door, laptop, plant, clock, bin.
  - **Recurring cards (22 Nov):** MILO (`rig2.make_milo`); RAE, MAYOR, DAN and NEIGHBOUR are in `_studio_library/engine/recurring.py` (load it after the library).
  - **Props batch 2 (22 Nov), `_studio_library/engine/props2.py`:** hammer, crate, notebook, the WHO'S LEFT list insert, the BLOXBURY DAILY newspaper, the hollow mug, a café table, a round bin, and `p2_door_glow` (the signature red-orange closet glow).
  - **Sets:** BLOXBURY TOWN (the `bloxbury_part1.py` prefix plus the TREES–CAMERA section) and MILO'S ROOM (the hollow house interior, with the window patch in `part1_v2.py`).
  - **Monsters:** THE KNOCKER (`_studio_library/engine/monster.py`, `make_knocker(name, height)`).
- **Scene template: `test2.py`.** Reuse its parts:
  - **Rig:** `upgrade_rig(P)` adds Chest, HipL/R, Head, and hand grips that keep props level. `arm(P, side, frame, target | euler)`. The shoulder is at (±1.5, 0, 3.5) and the arm is 1.5 long.
  - **Face:** `build_face_v2(P)` with posed brows and eyes, a blink layer, smooth sparkles (yellow emissive `spark_star` glints) and mouth swaps. Helpers: `expr(rig, frame, EX preset)`, `blink`, `eyes_closed`, `sparkle`, `mouth`, `lipsync(styles calm / excited / whisper)`, `accents` (nods on stressed syllables).
  - **Motion:** a per-frame walk cycle; smears by scaling the shoulder Z to about 1.35 for 2 frames; motion blur at shutter 0.5 with **position START** (clean cuts); `cam_key` with `make_compatible` (no camera spins).
- **Audio:** `talk/prep2.py` builds `env2.json` (loudness and brightness per frame) and the mixed wav with synthesised foley. Order: prep2, then test2, then prep2 again.
- **Render commands:**
  - Preview: `RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 python3 test2.py` (about 1.5 s per frame).
  - Pod: `ENGINE=GPU RENDER=1 RX=1080 RY=1920 ./blender/blender -b --python test2.py`.
  - `FRAMES=a,b,c` renders stills only.
- **Held props:** check contact numerically (prop vs mouth/hand in head space, no clipping) before rendering. Cups must be hollow.
- **Blender 5.x:** use the `kf()` and `apply_interp()` helpers. Layered actions need `_fcurves()`. DOF is keyed on `cam.data`. Avoid coplanar faces.

## Platforms
- **Where things go:** parts go to TikTok and YouTube Shorts. YouTube also gets a 10–15 min compilation, made by `make_youtube.sh` in `series/bloxbury/youtube` (parts as `Bloxbury_PartN.mp4`, 16:9 with blurred sides).
- **Monetisation thresholds:** YouTube Partner Program needs 1,000 subs plus 4,000 watch hours (8,000 from 1 Feb 2027). TikTok rewards need videos over 1 minute.
- **TikTok music limit (22 Nov 15:24):** TikTok flagged Part 2's music bed (matched as two copyrighted tracks): copyrighted sound is only authorised for **under 1 minute**, measured first-to-last second it plays, or the post gets muted. Rule: in the TikTok mix the music must span **≤ 55 s** (no music returning in the outro). `prep_pN.py` with `TIKTOK=1` writes that mix (Part 2: music 1.25–56.6 s only); remux it onto the video (`ffmpeg -i video.mp4 -i tiktok.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k`). YouTube keeps the full mix. Or use a TikTok Unlimited Sounds Library track added in the app.
- **TikTok export (Joel, 22 Nov 15:25):** `sh _pipeline/make_tiktok.sh <part.mp4> <tiktok.wav> <Bloxbury_PartN_TikTok.mp4> [0.94]` swaps in the TikTok mix AND shrinks the picture to 94% on a black 1080×1920 frame, so TikTok doesn't zoom in (Joel was shrinking it by hand). Joel confirmed 16:05: keep the borders (TikTok's zoom crops them off, so the full picture shows). Every part gets both files: `Bloxbury_PartN.mp4` (YouTube) and `_TikTok.mp4`. Pod finish should make both once this is wired into `pod_finish.sh`.
- **Keep it ad-safe:** creepy, not gory, and nothing graphic in the first 7 seconds or the thumbnail.

## Status (22 Nov, updated 15:40)
- **GitHub repo set up** (22 Nov): `Joel52412/bloxbury`, restore tested from a clean clone.
  - Pods now `git clone` the repo with the `GITHUB_RO` secret (working since 22 Nov 00:30). No more base64 chunk uploads.
- **Mouth test v1:** approved the lip-sync and Rae's motion. Fixed since: Milo's flicker, and a face that vanished before a cut.
- **Test 2** (`test2.py`, 354 frames, 14.75 s), preview reviewed and fixed:
  - **Shot A:** Milo's outro acted to the line (curious, hype, lean-in, ominous), with the closet glow creeping in.
  - **Shot B:** Dan sips coffee, walks, grabs the *BLOXBURY DAILY: KNOCKING CONTINUES* newspaper, throws it into a bin, then a smug sip.
  - **v1 rendered 22 Nov 00:55** (2× Secure 4090, about 16 min). Joel: the animation is much better and Milo's speech movement is really good.
  - **Fixed after his notes (22 Nov):**
    - **Sip:** the mug was at eye height and clipping into the face. It's now `SIP=(0.2, 0.75, 3.7)` with a tilt of about 25°, found by a numeric search: rim on the mouth, mug in front of the face, no clipping.
    - **Mug is hollow:** open top, a solidified 0.045 wall, coffee lower inside.
    - **Sparkles:** now flat 4-point yellow emissive glints with a hot pale centre, not lit and casting no light. The old white tube/ball crosses looked like objects, and a transparent halo caused a gold rim on the eyes, so the halo is gone.
  - **Approved from stills (22 Nov 01:04):** Joel is happy with the fixes and doesn't need a v2 re-render. **Test 2 is closed**, and its fixes are the template for Part 1.
- **Part 1 v2 (22 Nov): APPROVED by Joel 09:26 and being uploaded.** Notes for next time are now hard rules: narration has no mouth movement, and camera moves are calmer. Rendered 09:17 (2× Secure 4090, about 30 min, about $1.10 for the render). Frame check OK. `Bloxbury_Part1.mp4` was assembled on pod `z2dypvk3747emh`. Joel downloaded it 09:21 and the pod was deleted (about 47 min, about $1.40). Captions are at MarginV 330 with outline 6 (clear of faces in close-ups). The render monitor now retries `render_job.json` and shows time running and time taken.
  - **Files:** `_pipeline/scripts/part1_v2.py` (scene, 1723 frames, 71.75 s), `rig2.py` (the test2 rig, face and Milo card, shared); the Knocker now lives in the library (`_studio_library/engine/monster.py`). Audio: `_pipeline/audio_tools/prep_p1.py` writes `talk/{env_p1.json, part1_audio.wav, captions_p1.ass}` (copies are in `_pipeline/data`). Assemble with `sh _pipeline/make_part.sh <frames> <out.mp4> <audio.wav> <captions.ass>`; it burns in the ASS captions.
  - **Cue sheet rebuilt** from pocketsphinx word alignment of the current `milo.mp3` (`_pipeline/data/words_p1.json`, made by `align_lines.py`). The old `cues.py` used an older recording and is retired. Spoken knocks are gone (knock SFX instead), the `closet.mp3` duplicates are gone, and the hammer SFX is synced to the swings. Fixed a clipped "closet" (the line now ends at 35.24 s), plus "I thought…" and "Nobody was there". **Check every cut point's loudness** (a 20 ms RMS check) before mixing.
  - **Cast cards (Joel approved 22 Nov 09:31, saved in `recurring.py`):** Rae (purple hoodie, black X5 braids, dark jeans, lilac trainers, red notebook), the Mayor (dark suit, red tie, grey X1, glasses). The neighbour is a builder extra (hi-vis, hard hat). New props: hammer, crate, notebook, and the "WHO'S LEFT" list page (ends "Rae / Milo?").
  - **THE KNOCKER (Joel approved the look 22 Nov):** about 10.5–12 studs, starved and hunched, smooth spline-tube limbs (not blocky), arms past the knees, long pale claws, tilted skull, black sockets with pinpoint white eyes (emission 40), a red cheek-to-cheek grin of thin teeth. **Joel: keep him in the dark** so the eyes pop, with only a cool rim light for his silhouette and a faint red underglow. Beats: a silhouette outside the window behind Milo on "Then it went quiet" (49.7–51.7 s); eyes in the closet crack on "Milo..."; the door is ripped open with a lunge at the lens on "OUT" (61.32 s, jump-scare sting); hard cut to black.
  - **Blocking helpers:** `place()` plus `hold_cuts()` (the last pose holds until the cut, then snaps) and `flush_mouths()` (mouth events are sorted, so no double mouths). Milo's house windows are lowered to sill 4 / top 8 so he can look out.
  - **RunPod lessons (22 Nov):** two Community 4090 hosts on CUDA 13.0 had broken GPUs (`cuInit: Unknown error`; torch reports `cuda.is_available()` False), so **check torch CUDA in the first minute and delete if it's broken**. Secure 4090 (CUDA 13.2) worked. Part 1 full res runs at about **1.5 s per frame per 4090** (much faster than the Test 2 estimate). Previews get from pod to Claude by pushing contact sheets to a temporary `preview-part1-v2` branch (Claude's workspace can't reach the Jupyter proxy).
- **Part 2 music (Joel, 22 Nov 12:00):** only the **instrumental** of "Numbers" (TEMPOREX), **looped for the whole of Part 2 at 35% volume** (Joel 12:26: 35%, loop APPROVED as good). Vocals were removed with UVR-MDX-NET-Inst_HQ_3 (model weights download from GitHub releases; dl.fbaipublicfiles/demucs is blocked) and cut into a seamless **10.2 s loop of just the intro, without the whistle** (Joel 12:23; the 25 s loop and the bar splices are retired): the intro's 4 bars at ~94 BPM, where bar 4 -> bar 1 is the song's own chord change, with bar 4's ring-out fading under bar 1 and a gentle level rider (only lifts, max +12 dB) so the volume stays even. **Music dropouts are allowed wherever they help a scene** (Joel 12:38): pass `mutes=[(t0, t1)]` to `music_bed` (40 ms cut out, 0.6 s fade back in). Stored as `assets/music/Numbers_instrumental_loop.flac` (FLAC, not MP3, so repeats are gapless). `_pipeline/audio_tools/music_bed.py` (`PART_MUSIC[2]`, vol 0.35, 1 s fade-out): in `prep_p2.py` add `mix += music_bed(REPO, TOTAL, SR, len(mix))` **before** the peak normalise, into `mix` only (never `vox`, so lip-sync is unaffected). At 0.35 the bed sits about 6 dB under the narration.
- **Part 2 script (22 Nov 12:37): "She Came Home", draft v2, Joel likes it.** Saved at `series/bloxbury/part2/part2_script.md` (beat sheet, open decisions, asset list). It retells the viral "I heard it too" story, and reveals that Part 1's closet voice was Milo's real mum. It opens with a bridge from Part 1's last image, match-cutting the Knocker's grin to fake Mum's smile. Waiting on Joel: Mum's voice, the music dropout at the mirror, fake Mum's tells, then the recordings.
- **Part 2 production (22 Nov 13:04–13:30):**
  - **Recordings:** Joel's ElevenLabs files are `series/bloxbury/part2/voice/{milo_p2,rae_p2,mum_p2}.mp3`. ElevenLabs leaves digital silence between lines, so each line is cut from pocketsphinx word alignment (`audio_tools/align_full.py`, `split_lines.py`; data in `_pipeline/data/p2/lines_*.json`). One fix: "Milo" (whispered) at 12.95–13.42 s.
  - **Audio:** `audio_tools/prep_p2.py` is the cue sheet and pacing (80 s, 1921 frames). It matches each voice's level (Mum −5.9 dB), adds a too-perfect double on fake Mum, and filters the downstairs, closet and door voices. Music dropouts: 0–1.25, 44.3–51.6, 56.6–73.0. Sound: the sizzle only runs 1.25–7.0 s (Joel: it was too loud and long); the clock stops with the music; the three soft knocks use Part 1's front-door knock #4, cut before its 4th knock (Joel: "use the other knock"). Hard black 72.4–73.0. Loudnorm to −14 LUFS. Outputs `talk/{env_p2.json, part2_audio.wav, captions_p2.ass}` (copies in `data/p2`). env has per-speaker rms/cen and line `mode` N/D/C/O (lip-sync only for D and C).
  - **Asset sheet** (`_pipeline/scripts/part2_assets.py`, about 4 min on CPU): `_studio_library/approval_sheets/Part2_asset_sheet.png`, sent 13:30, **waiting on Joel's OK**. It covers: the Mum card (Milo's skin tone, H4 brown hair, sage cardigan, jeans, tan flats, rounded-square gold bangle on her left wrist with no clipping); fake vs real Mum faces; the kitchen set; the toaster; the hallway with a real mirror; Rae's porch (town); the list with Mum crossed off first; the Knocker kept dark; and a hollow closet (the solid ClosetBox is swapped for a shell). New sets are built in the air at z=400 so the town hills stay out of frame.
  - **APPROVED by Joel 13:27 (all designs).** Saved to the library: `recurring.make_mum` (+ `p3_bangle`), `props3.py` (toaster, list, kitchen set, hallway set, hollow closet), manifest + studio.py updated; `part2_assets.py` now loads the library versions (rechecked).
  - **Scene `_pipeline/scripts/part2.py` (built 22 Nov 13:30–14:00, FACE CHECK OK, 33 shots).** It loads the library (recurring + props2 + props3), env_p2, and Part 1's camera/shot system. Key tricks:
    - **Mirror twin:** the fake Mum has `visible_glossy` off, so she has no reflection of her own. `ReflMum` is visible only in glossy rays, so the mirror shows the twin; it keeps smiling, then turns its head.
    - **Toaster ghost:** a Knocker visible only in glossy rays, for 4 frames at 9.95 s.
    - **Doorway:** light under the bedroom door with two foot shadows.
    - **Kitchen:** chairs hidden, a front wall added for reverse shots, and the hug is from behind (her face beside his).
    - **Lessons from this build:**
      - Part 1's `idle()` keys absolute z, so use `idle_here()`.
      - `place()`/`park()` moves the root immediately, so aim shots BEFORE parking anyone.
      - CU cameras use `ots()` so the camera never sits inside the other character's head.
      - Sockets (emission) are keyed with `key()`, not `kf()`.
  - **RENDERED 22 Nov 14:53** (Joel skipped the low-res preview this time).
    - Pod `ids55rvi5qzm1v`, 3× Secure A40 (EU-SE-1, CUDA 13.2), $1.77/hr. Pod created 14:13, render 14:16–14:50, about $1.20 at delivery.
    - Two Community 4090s were tried first: one had no stock at 13.2, and the 13.0 host was broken (deleted after 1 min).
    - Frame check OK (1921). `Bloxbury_Part2.mp4` (26 MB) was assembled on the pod (now `make_part.sh`).
    - Speed: about 3 s per frame per A40. GPU 0's kitchen frames ran slowest; work-sharing helpers took over on GPUs 1 and 2 at 14:47 and 14:48.
    - **DELIVERED 14:55:** Joel downloaded it. The pod was deleted (about 42 min, about $1.25 total). The `preview-part2` and old `preview-part1-v2` branches are still on GitHub (harmless). Asset audit: every asset used is already in the library (recurring + props2 + props3 + monster).
- **TikTok fixes (22 Nov 15:25–15:35): DONE.** Part 2 got TikTok's 1-minute copyright notice. `series/bloxbury/exports/Bloxbury_Part2_TikTok.mp4` (music only 1.25–56.6 s, picture at 94% on black, Joel's ElevenLabs sizzle `assets/sfx/Pan_sizzle_butter_a_1`, `SIZZLE_DB` −46 (Joel 15:40: −38 was too loud), about 20 dB under the voices). Remuxed on the laptop with device_bash (it has ffmpeg), no re-render. `Bloxbury_Part2.mp4` is still the YouTube master with the OLD sizzle: Joel doesn't need a YouTube version yet (parts get stitched later), so swap in `_pipeline/data/p2/part2_audio.wav` at stitch time (see `youtube/make_youtube.sh`).
- **Part 2 outro glitch (Joel 15:41):** `milo_p2.mp3` had a 70 ms dropout inside "depends" (source 33.458–33.528 s, an ElevenLabs artifact). `prep_p2.py` now has `REPAIR` (source-time cuts with a 3 ms crossfade, padded at the line end so later lip-sync stays in sync). **Rule: after splitting lines, scan every line for silent gaps >40 ms inside words and for clicks; fix with REPAIR or ask Joel to regenerate the line.**
- **Folder clean-up (22 Nov 15:40):** new layout (see Folder map), retired scripts removed (cues.py, mix.py, talktest.py, cloud_render.py, render_cloud.sh, make_part1.sh, make_part2.sh, old closet recording), demo/listen files and old previews deleted from the laptop. prep_p1 and prep_p2 rebuilt from the new paths bit-identical.
- **Streamlining (22 Nov 15:05–15:25, Joel's options 2–6):** low-res pod preview retired; `director.py` shot checker (`check_shots`) + per-shot stills here; auto-finish on the pod (`pod_finish.sh`, `make_part.sh`) + Render Monitor auto-download and pod self-delete (tested against a mock pod; the runpodctl delete command still needs confirming on a real pod); render-quality presets tested; Joel picked fast (19% quicker) at 15:23; spot pods can't be automated (GraphQL only). Fixed Part 2's B3 camera in `part2.py` (template for Part 3).
- **NEXT: Part 3** (new chat). Use the episode workflow above. Start from `part2.py` as the scene template, use the ready-made image and the shared-queue pod render. (Old note kept for reference: Part 2 started from `part1_v2.py` as the template: the town set, Milo's house interior, cast cards, the Knocker, `prep_p1.py` → copy as `prep_p2.py` for the new script audio. Apply the narration-mouth and calm-camera rules from the start. Every asset used in Part 1 and Test 2 is now in the library (audit 22 Nov 09:40): `recurring.py`, `props2.py`, `monster.py`, plus the sets.
- **Later:** the auto-pipeline (story prompt in, everything generated, Joel just renders); library batches (outdoor/vehicles, then sets, then an animation move library).

## Joel's tools
`_tools/Render Monitor.bat` watches `series/` and RunPod pods, showing a progress bar, time left and finish time for each render.
