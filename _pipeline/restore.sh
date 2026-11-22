#!/bin/sh
# Restores the Bloxbury pipeline into a fresh Claude cloud workspace.
# Usage (in the new chat): stage the robloxshorts folder files, then:  sh /mnt/user-data/uploads/robloxshorts/_pipeline/restore.sh
U="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
H=/home/claude
mkdir -p $H/bloxbury-blender $H/studio_library/engine $H/audio $H/talk $H/cloud $H/tools
cp $U/_studio_library/engine/*.py $H/studio_library/engine/
cp $U/_pipeline/scripts/bloxbury_part1.py $U/_pipeline/scripts/talktest.py $U/_pipeline/scripts/test2.py $H/bloxbury-blender/
cp $U/_pipeline/scripts/cloud_render.py $U/_pipeline/scripts/render_cloud.sh $H/cloud/ 2>/dev/null
cp $U/_pipeline/audio_tools/cues.py $U/_pipeline/audio_tools/mix.py $H/audio/
cp $U/_pipeline/audio_tools/prep2.py $U/_pipeline/data/*.json $U/_pipeline/data/*.wav $H/talk/
A="$U/series/bloxbury/audio script"
cp "$A/milo.mp3" "$A/rae.mp3" "$A/outro.mp3" $H/audio/ 2>/dev/null
cp "$A/milo knocking closet.mp3" $H/audio/closet.mp3 2>/dev/null
cp $U/_tools/render_monitor.py $H/tools/ 2>/dev/null
pip install --break-system-packages -q bpy pocketsphinx pillow numpy 2>/dev/null || true
echo "restored into $H"; ls $H/bloxbury-blender $H/studio_library/engine
