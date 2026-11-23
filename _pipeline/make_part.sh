#!/bin/sh
# Assemble a part: frames (0001.png...) + mixed audio + word-timed captions -> mp4.
# Usage: sh make_part.sh <frames_dir | video-only master.mp4> <out.mp4> <audio.wav> <captions.ass>
. "$(dirname "$0")/encode.sh"
F=${1:-/workspace/frames}; O=${2:-Bloxbury_Part.mp4}; AU=$3; CA=$4
if [ -f "$F" ]; then IN="-i $F"; P=$F; else IN="-framerate 24 -i $F/%04d.png"; P=$F/0001.png; fi    # render_cache.py splices give a master video
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 $P)
SC=$(python3 -c "print(round($W/1080,4))")
sed "s/^PlayResX: 1080/PlayResX: $W/; s/^PlayResY: 1920/PlayResY: $(python3 -c "print(int($W*16/9))")/" $CA > /tmp/cap_scaled.ass
python3 - "$SC" <<'PY'
import sys,re
k=float(sys.argv[1]); p='/tmp/cap_scaled.ass'; s=open(p).read()
def fix(m):
    f=m.group(0).split(','); f[2]=str(max(8,round(int(f[2])*k))); f[16]=str(max(1,round(float(f[16])*k),)); f[21]=str(round(int(f[21])*k)); f[19]=str(round(int(f[19])*k)); f[20]=str(round(int(f[20])*k)); return ','.join(f)
s=re.sub(r'^Style: .*$',fix,s,flags=re.M); open(p,'w').write(s)
PY
ffmpeg -y -loglevel error $IN -i $AU -vf "${GRAIN_VF}ass=/tmp/cap_scaled.ass:fontsdir=$(dirname $0)/../assets/fonts,format=yuv420p" \
  $X264 -c:a aac -b:a 192k -shortest "$O" && echo "WROTE $O"
