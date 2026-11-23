#!/bin/sh
# pod_finish.sh - runs ON THE POD beside the render. When every frame is done: frame check, assemble, motion audit,
# TikTok cut, then wait for Joel's Render Monitor to download. The monitor writes /workspace/received.json once the
# file is safely on the laptop (size verified), and THEN the pod deletes itself. Nobody pays for an idle pod:
# no download in 60 min -> stop; any failure (needs_claude) -> 60 min for Claude to look, then stop.
# Reads /workspace/render_job.json: output (Bloxbury_Part3.mp4), audio, captions, black ("20-31 1739-1753"),
#   optional: shots (default newest /home/claude/talk/shots_p*.json), tiktok_audio (partN_tiktok.flac -> also makes
#   <output>_TikTok.mp4 with make_tiktok.sh; skipped when absent).
# Usage: nohup sh pod_finish.sh /workspace/frames <NF> > /workspace/finish.log 2>&1 &
F=${1:-/workspace/frames}; N=$2; J=/workspace/render_job.json; P=/workspace/render_progress.json; B=/workspace/bloxbury
get() { python3 -c "import json,sys;print(json.load(open('$J')).get(sys.argv[1],''))" "$1"; }
status() { python3 $B/_pipeline/pod_status.py "$@"; }
stop_pod() { runpodctl pod stop $RUNPOD_POD_ID 2>/dev/null || runpodctl stop pod $RUNPOD_POD_ID; }
fail() { status stage=needs_claude "error=$1"; echo "$(date +%T) $1 -> needs_claude; pod stops in 60 min"; sleep 3600
         status stage=stopped_needs_claude; stop_pod; exit 1; }
status stage=rendering
# 1. wait for the last frame (progress file says finished) and for every Blender to exit (pod_watchdog.sh stops the
#    pod if frames stop landing, so this wait can't run forever)
until python3 -c "import json,sys;sys.exit(0 if json.load(open('$P')).get('finished') else 1)" 2>/dev/null && ! pgrep -f "blender/blender -b" >/dev/null; do sleep 10; done
OUT=/workspace/$(get output); AU=$(get audio); CA=$(get captions); BL=$(get black); TA=$(get tiktok_audio); SH=$(get shots)
[ -z "$SH" ] && SH=$(ls -t /home/claude/talk/shots_p*.json 2>/dev/null | head -1)
status stage=checking
CHK=$(python3 $B/_pipeline/check_frames.py $F $N $BL 2>&1 | tail -1); echo "$CHK"
case "$CHK" in *"FRAME CHECK OK"*) status frame_check=OK ;; *) status "frame_check=$CHK"; fail "frame check failed" ;; esac
status stage=assembling
sh $B/_pipeline/make_part.sh $F $OUT $AU $CA || fail "make_part failed"
# video-only near-lossless master (no grain/captions): later story tweaks re-render only the changed frames and
# render_cache.py splices them into it. Joel keeps it in series/<story>/render_cache/<part>_master.mp4.
M="${OUT%.mp4}_master.mp4"
ffmpeg -y -loglevel error -framerate 24 -i $F/%04d.png -frames:v $N -c:v libx264 -preset fast -crf 10 -pix_fmt yuv420p $M &&
  status "master=workspace/$(basename $M)" master_size=$(stat -c %s $M) || status master=failed
# 2. motion audit (report only: the render is paid for; Claude reads it before calling the part done)
status stage=motion_audit
python3 $B/_tools/motion_audit.py $OUT $SH > /workspace/motion_audit.txt 2>&1
MA=$(tail -1 /workspace/motion_audit.txt); echo "$MA"; status "motion_audit=$MA"
# 3. TikTok cut (keeps the YouTube master as the main file)
if [ -n "$TA" ]; then
  status stage=tiktok; TT="${OUT%.mp4}_TikTok.mp4"
  sh $B/_pipeline/make_tiktok.sh $OUT $TA $TT && status "tiktok=workspace/$(basename $TT)" tiktok_size=$(stat -c %s $TT) || status tiktok=failed
fi
SZ=$(stat -c %s $OUT); status stage=ready "file=workspace/$(basename $OUT)" size=$SZ
echo "$(date +%T) ready: $OUT ($SZ bytes); waiting for the laptop to download it"
# 4. wait for the monitor's receipt (same size) -> delete this pod. No receipt in 60 min -> STOP (keeps the disk, ~free)
t=0
while [ $t -lt 3600 ]; do
  if [ -f /workspace/received.json ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('/workspace/received.json')).get('size')==$SZ else 1)"; then
    status stage=received; echo "$(date +%T) laptop has it -> deleting pod"
    sleep 3
    # runpodctl syntax changed between versions; try the new one first (pods carry a pod-scoped RUNPOD_API_KEY)
    runpodctl pod delete $RUNPOD_POD_ID 2>/dev/null || runpodctl pod remove $RUNPOD_POD_ID 2>/dev/null || runpodctl remove pod $RUNPOD_POD_ID && exit 0
    status stage=needs_claude; echo "runpodctl remove failed -> stopping instead"; stop_pod; exit 1
  fi
  sleep 5; t=$((t+5))
done
status stage=stopped_no_download; stop_pod
