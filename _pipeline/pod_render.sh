#!/bin/sh
# Split a scene render across every GPU on the pod, one Blender per GPU.
# Usage: sh pod_render.sh test2.py 354 /workspace/frames
S=$1; N=$2; OUT=${3:-/workspace/frames}; mkdir -p $OUT
G=$(nvidia-smi -L | wc -l); per=$(( (N + G - 1) / G ))
i=0
while [ $i -lt $G ]; do
  fs=$(( i*per + 1 )); fe=$(( (i+1)*per )); [ $fe -gt $N ] && fe=$N
  CUDA_VISIBLE_DEVICES=$i ENGINE=GPU RENDER=1 RX=1080 RY=1920 OUT=$OUT FS=$fs FE=$fe \
    nohup /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/render_gpu$i.log 2>&1 &
  echo "GPU $i: frames $fs-$fe"; i=$((i+1))
done
