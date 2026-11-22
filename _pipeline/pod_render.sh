#!/bin/sh
# Render a scene on EVERY GPU of the pod from ONE shared frame queue (Blender placeholders: each GPU claims the next
# free frame), so a slow GPU never holds the finish back. pod_balance.sh restarts any GPU whose Blender exits early.
# Usage: sh pod_render.sh part2.py 1921 /workspace/frames
S=$1; N=$2; OUT=${3:-/workspace/frames}; mkdir -p $OUT
find $OUT -name "*.png" -size 0 -delete 2>/dev/null    # resume-safe: drop placeholders of frames cut off by a stop
G=$(nvidia-smi -L | wc -l); i=0
while [ $i -lt $G ]; do
  CUDA_VISIBLE_DEVICES=$i ENGINE=GPU RENDER=1 RX=1080 RY=1920 OUT=$OUT FS=1 FE=$N \
    nohup /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/render_gpu$i.log 2>&1 &
  echo "GPU $i: shared queue 1-$N"; i=$((i+1)); sleep 3          # stagger starts so they don't all claim frame 1
done
# tiny progress file for the laptop Render Monitor + keep every GPU busy until the last frame
nohup python3 /workspace/bloxbury/_pipeline/pod_progress.py $OUT $N > /workspace/progress.log 2>&1 &
nohup sh /workspace/bloxbury/_pipeline/pod_balance.sh $S $N $OUT > /workspace/balance.log 2>&1 &
# when every frame is done: frame check, assemble, wait for the laptop to download it, then the pod deletes itself
nohup sh /workspace/bloxbury/_pipeline/pod_finish.sh $OUT $N > /workspace/finish.log 2>&1 &
