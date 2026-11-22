#!/bin/sh
# Run on a RunPod pod after cloning this repo to /workspace/bloxbury.
# Installs Blender 5.3 and lays the pipeline out at /home/claude like the Claude workspace.
set -e
R=/workspace/bloxbury; H=/home/claude; cd /workspace
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq wget xz-utils ffmpeg libx11-6 libxi6 libxxf86vm1 libxfixes3 \
  libxrender1 libxkbcommon0 libsm6 libice6 libgl1 libegl1 fonts-dejavu-core >/dev/null
if [ ! -x blender/blender ]; then
  wget -q -O blender.tar.xz https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz
  mkdir -p blender && tar -xf blender.tar.xz -C blender --strip-components=1 && rm blender.tar.xz
fi
PY=$(ls blender/5.3/python/bin/python3* | head -1)
$PY -m ensurepip >/dev/null 2>&1 || true      # note: no -q, Blender's ensurepip rejects it
$PY -m pip install -q pillow numpy
mkdir -p $H/bloxbury-blender $H/studio_library/engine $H/talk $H/audio
cp $R/_studio_library/engine/*.py $H/studio_library/engine/
cp $R/_pipeline/scripts/*.py $H/bloxbury-blender/
cp $R/_pipeline/audio_tools/prep2.py $H/talk/
find $R/_pipeline/data -maxdepth 1 -type f -exec cp {} $H/talk/ \;
[ -d $R/_pipeline/data/p2 ] && cp $R/_pipeline/data/p2/* $H/talk/       # Part 2: env_p2.json, captions_p2.ass, part2_audio.wav
./blender/blender -v | head -1
echo SETUP_OK
