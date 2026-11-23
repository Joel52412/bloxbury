#!/bin/sh
# pod_watchdog.sh - runs ON THE POD beside every render so a crash or hang can never bill forever.
#  * stale placeholders: a 0-byte frame older than STALE s (default 300) belongs to a Blender that died -> delete it,
#    so pod_balance.sh's helpers render that frame again (a live 1080p frame takes 2-6 s, a preview frame <1 s)
#  * no new finished frame for MAXIDLE s (default 600, counted from the watchdog's start until the first frame) ->
#    kill Blender, stage=stalled, STOP the pod (frames + disk kept, stop costs ~nothing). Claude restarts it.
# Exits once every frame FS..FE is a real file.
# Usage: nohup sh pod_watchdog.sh /workspace/frames 1 1921 > /workspace/watchdog.log 2>&1 &
OUT=${1:-/workspace/frames}; FS=$2; FE=$3; ST=$(dirname "$0")/pod_status.py
STALE=${STALE:-300}; MAXIDLE=${MAXIDLE:-600}; T0=$(date +%s)
while true; do
  R=$(python3 - "$OUT" "$FS" "$FE" "$STALE" "$T0" <<'PY'
import os, sys, time
d, fs, fe, stale, t0 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
now = time.time(); done = 0; newest = t0; dropped = []
for f in range(fs, fe + 1):
    p = "%s/%04d.png" % (d, f)
    try: st = os.stat(p)
    except FileNotFoundError: continue
    if st.st_size > 0: done += 1; newest = max(newest, st.st_mtime)
    elif now - st.st_mtime > stale:
        try: os.remove(p); dropped.append(f)
        except OSError: pass
if dropped: print("dropped stale placeholders", dropped[:20], file=sys.stderr)
print(done, fe - fs + 1, int(now - newest))
PY
)
  set -- $R; done=$1; want=$2; idle=$3
  [ "$done" -ge "$want" ] && echo "$(date +%T) all $want frames done, watchdog off" && exit 0
  if [ "$idle" -gt "$MAXIDLE" ]; then
    echo "$(date +%T) no new frame for ${idle}s ($done/$want done) -> stopping the pod"
    python3 $ST stage=stalled "frames=$done" "note=no new frame for ${idle}s: pod stopped, frames kept"
    pkill -f "blender/blender -b"; pkill -f pod_balance.sh; pkill -f pod_finish.sh
    [ -n "$RUNPOD_POD_ID" ] && { runpodctl pod stop $RUNPOD_POD_ID 2>/dev/null || runpodctl stop pod $RUNPOD_POD_ID; }
    exit 2
  fi
  sleep 30
done
