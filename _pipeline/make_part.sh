#!/bin/sh
# Assemble a part: frames (0001.png...) + mixed audio + word-timed captions -> mp4.
# Usage: sh make_part.sh <frames_dir> <out.mp4> <audio.wav> <captions.ass>
. "$(dirname "$0")/encode.sh"
F=${1:-/workspace/frames}; O=${2:-Bloxbury_Part.mp4}; AU=$3; CA=$4
# captions are authored at PlayRes 1080x1920: libass scales fonts AND \pos to any frame size (do not rewrite PlayRes)
ffmpeg -y -loglevel error -framerate 24 -i $F/%04d.png -i $AU -vf "${GRAIN_VF}ass=$CA:fontsdir=$(dirname $0)/../assets/fonts,format=yuv420p" \
  $X264 -c:a aac -b:a 192k -shortest "$O" && echo "WROTE $O"
