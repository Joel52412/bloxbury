#!/bin/sh
# make_tiktok.sh - TikTok version of a finished part: same picture (no borders, no scaling - Joel 22 Nov 16:04),
# with the TikTok audio mix swapped in (prep_pN.py with TIKTOK=1: copyrighted music under 1 minute).
# Usage: sh make_tiktok.sh <in.mp4> <tiktok.wav> <out.mp4>
IN=$1; AU=$2; OUT=$3
ffmpeg -y -loglevel error -i "$IN" -i "$AU" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT" && echo "TIKTOK OK $OUT"
