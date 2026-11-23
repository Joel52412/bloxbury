#!/bin/bash
# Joins the finished vertical parts in ../exports (Bloxbury_Part1.mp4, Bloxbury_Part2.mp4, ... the YouTube masters,
# not the _TikTok versions) into one 16:9 YouTube video with blurred sides, written to ../exports.
# If a part's master is older than its latest mix, swap the audio first (e.g. Part 2's new sizzle:
#   ffmpeg -i Bloxbury_Part2.mp4 -i ../../../_pipeline/data/p2/part2_audio.flac -map 0:v -map 1:a -c:v copy -c:a aac ...).
# Usage: bash make_youtube.sh
GRAIN=0 . "$(dirname "$0")/../../../_pipeline/encode.sh"
cd "$(dirname "$0")/../exports"
ls Bloxbury_Part*.mp4 | grep -v _TikTok | sort -V | sed "s/.*/file '&'/" > /tmp/bloxbury_parts.txt
ffmpeg -y -f concat -safe 0 -i /tmp/bloxbury_parts.txt -filter_complex "[0:v]split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=40,eq=brightness=-0.08[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p" $X264 -c:a aac -b:a 192k Bloxbury_Full_YouTube.mp4
