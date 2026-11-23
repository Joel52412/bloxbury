#!/bin/sh
# Restores the Bloxbury pipeline into a fresh Claude cloud workspace.
# Usage: sh <repo>/_pipeline/restore.sh [repo_root]
U="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
H=/home/claude
mkdir -p $H/bloxbury-blender $H/studio_library/engine $H/talk $H/tools
cp $U/_studio_library/engine/*.py $H/studio_library/engine/
cp $U/_pipeline/scripts/*.py $H/bloxbury-blender/
find $U/_pipeline/data -maxdepth 1 -type f -exec cp {} $H/talk/ \;
for d in $U/_pipeline/data/p*/; do [ -d "$d" ] && cp "$d"* $H/talk/; done    # env_pN.json, captions_pN.ass, partN_audio.flac
cp $U/_tools/render_monitor.py $H/tools/ 2>/dev/null
pip install --break-system-packages -q bpy faster-whisper pocketsphinx pillow numpy 2>/dev/null || true
echo "restored into $H"; ls $H/bloxbury-blender $H/studio_library/engine
