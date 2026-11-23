#!/bin/sh
# make_tiktok.sh - TikTok version of a finished part (Joel, 22 Nov 15:25):
#  * swaps in the TikTok audio mix (prep_pN.py with TIKTOK=1: copyrighted music under 1 minute)
#  * shrinks the picture to SCALE (default 0.94) on a black 1080x1920 frame, so TikTok doesn't zoom/crop it
# Usage: sh make_tiktok.sh <in.mp4> <tiktok.wav> <out.mp4> [scale]
GRAIN=0 . "$(dirname "$0")/encode.sh"
IN=$1; AU=$2; OUT=$3; S=${4:-0.94}
ffmpeg -y -loglevel error -i "$IN" -i "$AU" -map 0:v -map 1:a \
  -vf "scale=trunc(1080*$S/2)*2:trunc(1920*$S/2)*2:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1" \
  $X264 -c:a aac -b:a 192k -shortest "$OUT" && echo "TIKTOK OK $OUT"
