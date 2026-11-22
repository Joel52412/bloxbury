#!/bin/sh
# pod_finish.sh - runs ON THE POD beside the render. When every frame is done it checks the frames, assembles the
# video, then waits for Joel's Render Monitor to download it. The monitor writes /workspace/received.json once the
# file is safely on the laptop (size verified), and THEN the pod deletes itself. Nobody pays for an idle pod.
# Reads /workspace/render_job.json: output (e.g. Bloxbury_Part3.mp4), audio, captions, black ("20-31 1739-1753").
# Usage: nohup sh pod_finish.sh /workspace/frames <NF> > /workspace/finish.log 2>&1 &
F=${1:-/workspace/frames}; N=$2; J=/workspace/render_job.json; P=/workspace/render_progress.json
get() { python3 -c "import json,sys;print(json.load(open('$J')).get(sys.argv[1],''))" "$1"; }
status() { python3 - "$@" <<'PY'
import json, sys, os, time
p = "/workspace/render_output.json"
d = json.load(open(p)) if os.path.exists(p) else {}
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); d[k] = int(v) if v.isdigit() else v
d["updated"] = time.time(); json.dump(d, open(p + ".tmp", "w")); os.replace(p + ".tmp", p)
PY
}
status stage=rendering
# 1. wait for the last frame (progress file says finished) and for every Blender to exit
until python3 -c "import json,sys;sys.exit(0 if json.load(open('$P')).get('finished') else 1)" 2>/dev/null && ! pgrep -f "blender/blender -b" >/dev/null; do sleep 10; done
OUT=/workspace/$(get output); AU=$(get audio); CA=$(get captions); BL=$(get black)
status stage=checking
CHK=$(python3 /workspace/bloxbury/_pipeline/check_frames.py $F $N $BL 2>&1 | tail -1); echo "$CHK"
case "$CHK" in *"FRAME CHECK OK"*) status frame_check=OK ;; *) status "frame_check=$CHK" stage=needs_claude; echo "frame check failed: Claude decides"; exit 1 ;; esac
status stage=assembling
sh /workspace/bloxbury/_pipeline/make_part.sh $F $OUT $AU $CA || { status stage=needs_claude; exit 1; }
SZ=$(stat -c %s $OUT); status stage=ready "file=workspace/$(basename $OUT)" size=$SZ
echo "$(date +%T) ready: $OUT ($SZ bytes); waiting for the laptop to download it"
# 2. wait for the monitor's receipt (same size) -> delete this pod. No receipt in 60 min -> STOP (keeps the disk, ~free)
t=0
while [ $t -lt 3600 ]; do
  if [ -f /workspace/received.json ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('/workspace/received.json')).get('size')==$SZ else 1)"; then
    status stage=received; echo "$(date +%T) laptop has it -> deleting pod"
    sleep 3
    # runpodctl syntax changed between versions; try the new one first (pods carry a pod-scoped RUNPOD_API_KEY)
    runpodctl pod delete $RUNPOD_POD_ID 2>/dev/null || runpodctl pod remove $RUNPOD_POD_ID 2>/dev/null || runpodctl remove pod $RUNPOD_POD_ID && exit 0
    status stage=needs_claude; echo "runpodctl remove failed"; exit 1
  fi
  sleep 5; t=$((t+5))
done
status stage=stopped_no_download; runpodctl pod stop $RUNPOD_POD_ID 2>/dev/null || runpodctl stop pod $RUNPOD_POD_ID
