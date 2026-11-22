# Bloxbury Studio: pipeline map
Joel makes Roblox-style animated horror Shorts. The series is **BLOXBURY: The 3AM Knock**, made in **Blender 5.3 Python** and rendered on **RunPod**. It's a studio workflow: a reusable asset library plus scripted scenes.

## Start of every chat
1. **Restore from GitHub** (private repo `Joel52412/bloxbury`, mirrors `robloxshorts` minus frames, .blend, .mp4, inspo, voice clones):
   `add_repo Joel52412/bloxbury (push)`, then `git clone --depth 1 https://github.com/Joel52412/bloxbury /home/claude/bloxbury && sh /home/claude/bloxbury/_pipeline/restore.sh`.
   `restore.sh` takes the repo root (default: its parent folder) and rebuilds `/home/claude/{bloxbury-blender,studio_library/engine,audio,talk,cloud}` and pip-installs bpy.
2. **After changing anything:** commit and push to the repo (`git -c push.negotiate=true push`), and copy changed files into `C:\Users\frimp\Downloads\robloxshorts` too if the folder is connected (device_commit_files).
3. **Laptop folder** is only needed for frames, .blend files or new audio Joel adds. Folders connect per chat: if Joel has said OK, `device_request_folder_access` on `C:\Users\frimp\Downloads\robloxshorts` works; otherwise ask him to use **+ → Add folder**. New audio Joel drops in the folder must be pushed to the repo.
4. **New stories** go in `series/<story>/` beside `series/bloxbury/`, sharing the engine and library.

## Hard rules
- **Library:**
  - Save only assets Joel has verified.
  - Ask before bulk saves.
  - "Full asset sheet" means show everything.
- **Look:**
  - R6 Roblox characters, classic head, only designs makeable in Roblox.
  - **No clipping.** Hats get under-hat hair.
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
- **QA before sending anything:**
  - `check_faces` passes: one mouth every frame, no closed eyes right before a cut.
  - A full low-res preview is reviewed frame by frame on contact sheets.
  - After the GPU render, automated checks for black or blank frames.
- **24 fps** (20% cheaper than 30).
- **Captions:**
  - Small, lower-middle, clear of faces.
  - Word-timed with pocketsphinx alignment.
- **Directing:** punch-ins on key words, slow push-ins for tension, hard cuts, follow the action.
- **Voiceover scripts:**
  - Paste-ready blocks for ElevenLabs.
  - One line per paragraph, [emotion] tags, no numbers.
  - One block per voice; the main character narrates.

## RunPod
- **Before you create:** state the price first, and Joel must OK pod creation (the auto-check can block it). When offering cards, give each option's **hourly price, total time and total cost**, and always include **multi-GPU options** (2×, 3×).
- **Pod ownership:** only delete pods made in this chat, and never print the API key or the GitHub token.
- **Card choice:** episodes go on **3× Community RTX 4090** ($0.34/hr each, about 58p per episode). Tests use 1–2×. Community stock often runs out (and `get-capacity` can be stale). Secure 4090 is $0.89/hr. `allowedCudaVersions` goes inside `gpu`.
- **Speed (Test 2 scene, 1080×1920, 32 samples):** about 5.3 s per frame per 4090.
- **Render settings:** 32 samples, OptiX denoise. Test each GPU with a `FRAMES=` still first, then check every frame.
- **Create body:** image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, disk 30, port 8888/http, startJupyter, and `env: {"GITHUB_RO": "{{ RUNPOD_SECRET_GITHUB_RO }}"}` **at create time**. Changing env later with update-pod restarts the container, wipes it and drops Jupyter's password. If that happens, restart Jupyter by hand with your own token.
- **Getting the code onto the pod (no more base64 chunks):**
  - Token: `T=$(tr '\0' '\n' < /proc/1/environ | sed -n 's/^GITHUB_RO=//p')`.
  - Clone: `git clone --depth 1 https://x-access-token:$T@github.com/Joel52412/bloxbury.git /workspace/bloxbury`.
  - Then `nohup sh /workspace/bloxbury/_pipeline/pod_setup.sh > setup.log &`. It installs apt packages and Blender 5.3 (note: no `-q` on `ensurepip`), and lays files out under `/home/claude`.
  - RunPod secret `GITHUB_RO` (id `we7rf4p3y8`) holds Joel's fine-grained token "robloxrepo" for this repo. It's currently over-scoped (read+write); a read-only one is a todo.
- **Multi-GPU:** `sh /workspace/bloxbury/_pipeline/pod_render.sh test2.py <NF> /workspace/frames` runs one Blender per GPU (`CUDA_VISIBLE_DEVICES`, `FS`/`FE` split). Logs go to `render_gpuN.log`.
- **Download:** **always give Joel the full download link** with the token in it: `https://<pod>-8888.proxy.runpod.net/files/workspace/<file>?token=<jupyter token>`. If Jupyter shows a login page, he pastes the token there. Delete the pod after he confirms.
- **Long jobs:** use `nohup`; `exec-pod` calls max out at 25 s.
- **Render monitor:** write `/workspace/render_job.json` (`name`, `group`, `total`, `frame_start`, `frame_end`, `cost_per_hr`, `pod_started` = the pod's createdAt, which shows spend) and give Joel the pod id and Jupyter token.

## Engine
- **Load order:** the `bloxbury_part1.py` prefix (up to `# Milo starts at the fence`), then charlib, stylelab, hair2, hair3, faces2, garments, garments2, hair4, faces3, faces4, props (and studio for the registry).
- **Registry:** `studio.py`, with `CAST` tags F1–F6, B1–B6, C1–C24, K1–K12 and `studio_character(tag)`.
- **Approved assets:**
  - **Faces:** M2, shine at 70% opacity, 12 emotions, plus `faces4.RARE` (14 faces).
  - **Hair:** H2, H3, H4, H8; M1–M6; X1–X6.
  - **Outfits:** O1–O4, plus role, kids and teen outfits.
  - **Props batch 1:** cars, house furniture, kitchen, door, laptop, plant, clock, bin.
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
- **Keep it ad-safe:** creepy, not gory, and nothing graphic in the first 7 seconds or the thumbnail.

## Status (22 Nov, updated 09:00)
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
- **Part 1 v2 (22 Nov), the redesign. Built, previewed, full render running.**
  - **Files:** `_pipeline/scripts/part1_v2.py` (scene, 1723 frames, 71.75 s), `rig2.py` (the test2 rig, face and Milo card, shared), `monster.py` (THE KNOCKER). Audio: `_pipeline/audio_tools/prep_p1.py` writes `talk/{env_p1.json, part1_audio.wav, captions_p1.ass}` (copies are in `_pipeline/data`). Assemble with `sh _pipeline/make_part1.sh <frames> <out.mp4>`; it burns in the ASS captions.
  - **Cue sheet rebuilt** from pocketsphinx word alignment of the current `milo.mp3` (`_pipeline/data/words_p1.json`, made by `align_lines.py`). The old `cues.py` used an older recording and is retired. Spoken knocks are gone (knock SFX instead), the `closet.mp3` duplicates are gone, and the hammer SFX is synced to the swings. Fixed a clipped "closet" (the line now ends at 35.24 s), plus "I thought…" and "Nobody was there". **Check every cut point's loudness** (a 20 ms RMS check) before mixing.
  - **Cast cards (new, recurring, pending Joel's sign-off):** Rae (purple hoodie, black X5 braids, dark jeans, lilac trainers, red notebook), the Mayor (dark suit, red tie, grey X1, glasses). The neighbour is a builder extra (hi-vis, hard hat). New props: hammer, crate, notebook, and the "WHO'S LEFT" list page (ends "Rae / Milo?").
  - **THE KNOCKER (Joel approved the look 22 Nov):** about 10.5–12 studs, starved and hunched, smooth spline-tube limbs (not blocky), arms past the knees, long pale claws, tilted skull, black sockets with pinpoint white eyes (emission 40), a red cheek-to-cheek grin of thin teeth. **Joel: keep him in the dark** so the eyes pop, with only a cool rim light for his silhouette and a faint red underglow. Beats: a silhouette outside the window behind Milo on "Then it went quiet" (49.7–51.7 s); eyes in the closet crack on "Milo..."; the door is ripped open with a lunge at the lens on "OUT" (61.32 s, jump-scare sting); hard cut to black.
  - **Blocking helpers:** `place()` plus `hold_cuts()` (the last pose holds until the cut, then snaps) and `flush_mouths()` (mouth events are sorted, so no double mouths). Milo's house windows are lowered to sill 4 / top 8 so he can look out.
  - **RunPod lessons (22 Nov):** two Community 4090 hosts on CUDA 13.0 had broken GPUs (`cuInit: Unknown error`; torch reports `cuda.is_available()` False), so **check torch CUDA in the first minute and delete if it's broken**. Secure 4090 (CUDA 13.2) worked. Part 1 full res runs at about **1.5 s per frame per 4090** (much faster than the Test 2 estimate). Previews get from pod to Claude by pushing contact sheets to a temporary `preview-part1-v2` branch (Claude's workspace can't reach the Jupyter proxy).
- **Later:** the auto-pipeline (story prompt in, everything generated, Joel just renders); library batches (outdoor/vehicles, then sets, then an animation move library).

## Joel's tools
`_tools/Render Monitor.bat` watches `series/` and RunPod pods, showing a progress bar, time left and finish time for each render.
