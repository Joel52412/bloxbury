#!/bin/bash
# Joins finished vertical parts (Bloxbury_Part1.mp4, Part2...) into one 16:9 YouTube video with blurred sides.
# Usage: put the finished part .mp4 files (with audio) in this folder, then: bash make_youtube.sh
cd "$(dirname "$0")"
ls Bloxbury_Part*.mp4 | sort -V | sed "s/.*/file '&'/" > parts.txt
ffmpeg -y -f concat -safe 0 -i parts.txt -filter_complex "[0:v]split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=40,eq=brightness=-0.08[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p" -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k Bloxbury_Full_YouTube.mp4
