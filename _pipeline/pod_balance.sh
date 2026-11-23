#!/bin/sh
# Work-sharing: when a GPU's Blender exits while frames are still missing, start a helper Blender on that GPU over the
# whole range: placeholders make it skip every frame already done or in progress. Helpers inherit RX/RY/SAMPLES (and
# QUALITY, LOOK, PLAYBLAST...) from pod_render.sh, so a 540x960 preview never turns into 1080p helpers.
# Stale placeholders of dead Blenders are cleared by pod_watchdog.sh; this loop runs until every frame is a real file.
# A GPU whose helpers keep dying (MAXHELP, default 8) gets no more: the watchdog then stops the pod instead of looping.
# Usage: nohup sh pod_balance.sh part2.py 1921 /workspace/frames > /workspace/balance.log 2>&1 &
S=$1; N=$2; OUT=${3:-/workspace/frames}; G=$(nvidia-smi -L | wc -l); MAXHELP=${MAXHELP:-8}
while true; do
  # frames not finished yet (missing or 0-byte placeholder); 0 = done
  left=$(python3 -c "import os,sys;d=sys.argv[1];print(sum(1 for f in range(1,int(sys.argv[2])+1) if not (os.path.exists(d+'/%04d.png'%f) and os.path.getsize(d+'/%04d.png'%f)>0)))" $OUT $N)
  [ "$left" -eq 0 ] && echo "$(date +%T) every frame is done" && break
  i=0
  while [ $i -lt $G ]; do
    busy=0
    for p in $(pgrep -f "blender/blender -b"); do
      tr '\0' '\n' < /proc/$p/environ 2>/dev/null | grep -qx "CUDA_VISIBLE_DEVICES=$i" && busy=1
    done
    k=$(ls /workspace/render_gpu${i}_h*.log 2>/dev/null | wc -l)
    if [ $busy -eq 0 ] && [ $k -lt $MAXHELP ]; then
      echo "$(date +%T) GPU $i idle with $left frames left -> helper $k (${RX:-1080}x${RY:-1920}, ${SAMPLES:-32} samples)"
      CUDA_VISIBLE_DEVICES=$i ENGINE=GPU RENDER=1 RX=${RX:-1080} RY=${RY:-1920} SAMPLES=${SAMPLES:-32} OUT=$OUT FS=1 FE=$N \
        nohup /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/render_gpu${i}_h$k.log 2>&1 &
    fi
    i=$((i+1))
  done
  sleep 15
done
