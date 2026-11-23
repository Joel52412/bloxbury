#!/bin/sh
# Join split-render segments (seg_a.mp4 seg_b.mp4 ... in order) + audio + captions -> final mp4 (runs on the laptop).
# Usage: sh join_segments.sh <out.mp4> <audio.wav> <captions.ass> seg_a.mp4 seg_b.mp4 ...
. "$(dirname "$0")/encode.sh"
O=$1; AU=$2; CA=$3; shift 3
L=$(mktemp); for f in "$@"; do echo "file '$(readlink -f "$f")'" >> $L; done
D=$(cd "$(dirname "$0")/.." && pwd)
ffmpeg -y -loglevel error -f concat -safe 0 -i $L -i $AU -vf "${GRAIN_VF}ass=$CA:fontsdir=$D/assets/fonts,format=yuv420p" \
  $X264 -c:a aac -b:a 192k -shortest "$O" && echo "WROTE $O"
