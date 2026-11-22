#!/bin/sh
# Assemble Part 1: frames (0001.png...) + mixed audio + word-timed captions -> mp4.
# Usage: sh make_part1.sh <frames_dir> <out.mp4>   (needs /home/claude/talk/{part1_audio.wav,captions_p1.ass} from prep_p1.py)
F=${1:-/workspace/frames}; O=${2:-Bloxbury_Part1.mp4}; T=/home/claude/talk
W=$(python3 -c "from PIL import Image;print(Image.open('$F/0001.png').size[0])")
SC=$(python3 -c "print(round($W/1080,4))")
sed "s/^PlayResX: 1080/PlayResX: $W/; s/^PlayResY: 1920/PlayResY: $(python3 -c "print(int($W*16/9))")/" $T/captions_p1.ass > /tmp/cap_scaled.ass
python3 - "$SC" <<'PY'
import sys,re
k=float(sys.argv[1]); p='/tmp/cap_scaled.ass'; s=open(p).read()
def fix(m):
    f=m.group(0).split(','); f[2]=str(max(8,round(int(f[2])*k))); f[16]=str(max(1,round(float(f[16])*k),)); f[21]=str(round(int(f[21])*k)); f[19]=str(round(int(f[19])*k)); f[20]=str(round(int(f[20])*k)); return ','.join(f)
s=re.sub(r'^Style: .*$',fix,s,flags=re.M); open(p,'w').write(s)
PY
ffmpeg -y -loglevel error -framerate 24 -i $F/%04d.png -i $T/part1_audio.wav -vf "ass=/tmp/cap_scaled.ass,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -shortest "$O" && echo "WROTE $O"
