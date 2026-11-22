#!/bin/sh
# Work-sharing: when a GPU's Blender finishes (its own frames done) while frames are still missing, start a helper
# Blender on that GPU over the whole range: placeholders make it skip every frame already done or in progress.
# Usage: nohup sh pod_balance.sh part2.py 1921 /workspace/frames > /workspace/balance.log 2>&1 &
S=$1; N=$2; OUT=${3:-/workspace/frames}; G=$(nvidia-smi -L | wc -l)
while true; do
  # frames nobody has claimed yet (no file, not even a 0-byte placeholder); 0 = everything is done or in progress
  left=$(python3 -c "import os,sys;d=sys.argv[1];print(sum(1 for f in range(1,int(sys.argv[2])+1) if not os.path.exists(d+'/%04d.png'%f)))" $OUT $N)
  [ "$left" -eq 0 ] && echo "$(date +%T) every frame is done or being rendered" && break
  i=0
  while [ $i -lt $G ]; do
    busy=0
    for p in $(pgrep -f "blender/blender -b"); do
      tr '\0' '\n' < /proc/$p/environ 2>/dev/null | grep -qx "CUDA_VISIBLE_DEVICES=$i" && busy=1
    done
    if [ $busy -eq 0 ]; then
      k=$(ls /workspace/render_gpu$i*.log 2>/dev/null | wc -l)
      echo "$(date +%T) GPU $i idle with $left frames left -> helper $k"
      CUDA_VISIBLE_DEVICES=$i ENGINE=GPU RENDER=1 RX=1080 RY=1920 OUT=$OUT FS=1 FE=$N \
        nohup /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/render_gpu${i}_h$k.log 2>&1 &
    fi
    i=$((i+1))
  done
  sleep 15
done
