#!/bin/sh
# Restores the Bloxbury pipeline into a fresh Claude cloud workspace.
# Usage: sh <repo>/_pipeline/restore.sh [repo_root]
U="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
H=/home/claude
[ -e $H/bloxbury ] || ln -s "$U" $H/bloxbury        # props6 fonts expect the repo at /home/claude/bloxbury
mkdir -p $H/bloxbury-blender $H/studio_library/engine $H/talk $H/tools
cp $U/_studio_library/engine/*.py $H/studio_library/engine/
cp $U/_pipeline/scripts/*.py $H/bloxbury-blender/                   # shared: rig2, cinema, director
for st in $U/stories/*/; do                                          # every story: scene scripts + audio data (flat)
  [ -d "$st/scripts" ] && cp "$st"scripts/*.py $H/bloxbury-blender/
  for d in "$st"data/*/; do [ -d "$d" ] && cp "$d"* $H/talk/; done   # env_<id>.json, captions_<id>.ass, <stem>_audio.flac
done
cp $U/_tools/render_monitor.py $H/tools/ 2>/dev/null
pip install --break-system-packages -q bpy faster-whisper pocketsphinx pillow numpy 2>/dev/null || true
(apt-get install -y -q libegl1 libgl1 >/dev/null 2>&1 || (apt-get update -q >/dev/null 2>&1 && apt-get install -y -q libegl1 libgl1 >/dev/null 2>&1)) || true   # bpy renders abort without libEGL
echo "restored into $H"; ls $H/bloxbury-blender $H/studio_library/engine
