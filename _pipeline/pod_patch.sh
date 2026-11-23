#!/bin/sh
# PATCH RENDER: render only the frames a story tweak changed (RANGES from `render_cache.py plan`), on every GPU of the
# pod from one shared queue, then pack them into one small video (frames in time order) + its frame list. Splice it
# into the cached master with `render_cache.py splice <part> --new patch_<part>.mp4` (laptop or Claude's workspace).
# Usage: sh pod_patch.sh part3.py "123-239,369-476" [/workspace/patch]      (RX/RY/SAMPLES/QUALITY as for pod_render.sh)
S=$1; RG=$2; OUT=${3:-/workspace/patch}; B=/workspace/bloxbury; mkdir -p $OUT
P=$(basename $S .py | sed 's/^part/p/')
find $OUT -name "*.png" -size 0 -delete 2>/dev/null           # resume-safe
LIST=$(python3 -c "
import sys
out=[]
for p in sys.argv[1].split(','):
    a,_,b=p.partition('-'); out+=range(int(a),int(b or a)+1)
print(' '.join(map(str,out)))" "$RG")
N=$(echo $LIST | wc -w); FS=$(echo $LIST | cut -d' ' -f1); FE=$(echo $LIST | awk '{print $NF}')
python3 $B/_pipeline/pod_status.py stage=rendering kind=patch frames=0 want=$N "ranges=$RG"
G=$(nvidia-smi -L | wc -l)
start() {   # $1 GPU, $2 log tag
  CUDA_VISIBLE_DEVICES=$1 ENGINE=GPU RENDER=1 RX=${RX:-1080} RY=${RY:-1920} SAMPLES=${SAMPLES:-32} OUT=$OUT RANGES="$RG" \
    nohup /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/patch_gpu$1$2.log 2>&1 &
}
i=0; while [ $i -lt $G ]; do start $i ""; i=$((i+1)); sleep 3; done
# hang/crash guard over the patch's span (stale placeholders re-queued, no new frame for 10 min -> pod stops)
nohup sh $B/_pipeline/pod_watchdog.sh $OUT $FS $FE > /workspace/watchdog.log 2>&1 &
left() { python3 -c "
import os,sys
d=sys.argv[1]; print(sum(1 for f in sys.argv[2:] if not (os.path.exists(d+'/%04d.png'%int(f)) and os.path.getsize(d+'/%04d.png'%int(f))>0)))" $OUT $LIST; }
k=0
while [ "$(left)" -gt 0 ]; do
  python3 $B/_pipeline/pod_status.py frames=$((N - $(left)))
  if ! pgrep -f "blender/blender -b" >/dev/null; then              # every Blender exited with frames left: restart
    k=$((k+1)); [ $k -gt 8 ] && { python3 $B/_pipeline/pod_status.py stage=needs_claude "error=patch render keeps dying"; exit 1; }
    find $OUT -name "*.png" -size 0 -delete; i=0; while [ $i -lt $G ]; do start $i "_h$k"; i=$((i+1)); done
  fi
  sleep 15
done
pkill -f pod_watchdog.sh
# pack: frames in time order -> near-lossless video-only patch + frame list
L=$(mktemp -d); j=0; for f in $LIST; do ln -s $OUT/$(printf %04d $f).png $L/$(printf %06d $j).png; j=$((j+1)); done
ffmpeg -y -loglevel error -framerate 24 -i $L/%06d.png -c:v libx264 -preset fast -crf 10 -pix_fmt yuv420p /workspace/patch_$P.mp4 &&
python3 -c "import json,sys;json.dump({'part':sys.argv[1],'ranges':sys.argv[2],'frames':[int(x) for x in sys.argv[3:]]},open('/workspace/patch_$P.json','w'))" $P "$RG" $LIST &&
python3 $B/_pipeline/pod_status.py stage=ready kind=patch frames=$N "file=workspace/patch_$P.mp4" "list=workspace/patch_$P.json" size=$(stat -c %s /workspace/patch_$P.mp4) ||
python3 $B/_pipeline/pod_status.py stage=needs_claude "error=patch encode failed"
