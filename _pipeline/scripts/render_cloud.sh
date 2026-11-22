#!/bin/bash
# Bloxbury cloud render. In the RunPod terminal, run:   bash render_cloud.sh
# Re-running it is safe: it skips the Blender download and any frames already done.
# If you see an "OptiX" error, run this instead:   BLOX_BACKEND=CUDA bash render_cloud.sh
set -e
cd "$(dirname "$0")"
BLEND="Bloxbury_Part1.blend"
BLENDER_URL="https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz"

if [ ! -f "$BLEND" ] || [ ! -f cloud_render.py ]; then
  echo "Upload $BLEND and cloud_render.py into this folder first."; exit 1
fi

echo "== 1/4  Installing Blender 5.3 (first run only)"
if [ ! -x blender/blender ]; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq wget xz-utils libx11-6 libxi6 libxxf86vm1 \
      libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 libgl1 libegl1 >/dev/null
  wget -q --show-progress -O blender.tar.xz "$BLENDER_URL"
  mkdir -p blender && tar -xf blender.tar.xz -C blender --strip-components=1 && rm blender.tar.xz
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

echo "== 2/4  Rendering all frames on the GPU (the long part)"
./blender/blender -b "$BLEND" --python cloud_render.py -- frames

echo "== 3/4  Building the final video with sound and captions"
./blender/blender -b "$BLEND" --python cloud_render.py -- video

echo "== 4/4  Done"
ls -lh Bloxbury_Part1_*.mp4
echo "Right-click the .mp4 in the file list on the left and choose Download."
echo "Then TERMINATE the pod in RunPod so billing stops."
