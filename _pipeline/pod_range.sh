#!/bin/sh
# SPLIT RENDER (Joel 23 Nov: no multi-GPU machines free): each single-GPU pod renders frames FS..FE and encodes a
# video-only segment (near-lossless intermediate); the segments are joined with audio + captions on the laptop (join_segments.sh).
# Usage: sh pod_range.sh part3.py 1 613 a
S=$1; FS=$2; FE=$3; TAG=$4; OUT=/workspace/frames; mkdir -p $OUT
echo "{\"stage\": \"rendering\", \"fs\": $FS, \"fe\": $FE}" > /workspace/render_output.json
nohup sh $(dirname "$0")/pod_watchdog.sh $OUT $FS $FE > /workspace/watchdog.log 2>&1 &   # hang/crash -> pod stops
CUDA_VISIBLE_DEVICES=0 ENGINE=GPU RENDER=1 RX=${RX:-1080} RY=${RY:-1920} SAMPLES=${SAMPLES:-32} OUT=$OUT FS=$FS FE=$FE \
  /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/render_gpu0.log 2>&1
n=$(ls $OUT/*.png 2>/dev/null | wc -l); want=$((FE - FS + 1))
ffmpeg -y -loglevel error -framerate 24 -start_number $FS -i $OUT/%04d.png -frames:v $want \
  -c:v libx264 -preset fast -crf 10 -pix_fmt yuv420p /workspace/seg_$TAG.mp4
st=ready; [ "$n" -lt "$want" ] && st=needs_claude
echo "{\"stage\": \"$st\", \"frames\": $n, \"want\": $want, \"file\": \"workspace/seg_$TAG.mp4\"}" > /workspace/render_output.json
