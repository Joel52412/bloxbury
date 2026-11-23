#!/bin/sh
# Run on a RunPod pod after cloning this repo to /workspace/bloxbury.
# Installs Blender 5.3 and lays the pipeline out at /home/claude like the Claude workspace.
set -e
R=/workspace/bloxbury; H=/home/claude; cd /workspace
if [ -x /opt/blender/blender ]; then
  # ready-made image (ghcr.io/joel52412/bloxbury-render): Blender + libs are already installed -> ~seconds
  ln -sfn /opt/blender /workspace/blender
else
timeout 90 apt-get update -qq || echo 'apt update timed out (slow mirror, 23 Nov EU-RO-1): using the image libs'
DEBIAN_FRONTEND=noninteractive timeout 180 apt-get install -y -qq wget xz-utils ffmpeg libx11-6 libxi6 libxxf86vm1 libxfixes3 \
  libxrender1 libxkbcommon0 libsm6 libice6 libgl1 libegl1 fonts-dejavu-core >/dev/null || true
# apt mirror dead? Blender only truly needs libEGL from the list: fetch the 4 glvnd debs over https (23 Nov fix)
if ! ldconfig -p | grep -q libEGL.so.1; then
  (cd /tmp && for p in libegl1 libglvnd0 libgl1 libglx0; do curl -sfO https://mirrors.edge.kernel.org/ubuntu/pool/main/libg/libglvnd/${p}_1.7.0-1build1_amd64.deb; done; dpkg -i --force-depends /tmp/lib*_1.7.0-1build1_amd64.deb >/dev/null 2>&1; ldconfig)
fi
if [ ! -x blender/blender ]; then
  wget -q -O blender.tar.xz https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz
  mkdir -p blender && tar -xf blender.tar.xz -C blender --strip-components=1 && rm blender.tar.xz
fi
PY=$(ls blender/5.3/python/bin/python3* | head -1)
$PY -m ensurepip >/dev/null 2>&1 || true      # note: no -q, Blender's ensurepip rejects it
$PY -m pip install -q pillow numpy
fi
mkdir -p $H/bloxbury-blender $H/studio_library/engine $H/talk $H/audio
cp $R/_studio_library/engine/*.py $H/studio_library/engine/
cp $R/_pipeline/scripts/*.py $H/bloxbury-blender/
for st in $R/stories/*/; do                                          # every story: scene scripts + env, captions, mix
  [ -d $st/scripts ] && cp $st/scripts/*.py $H/bloxbury-blender/
  for d in $st/data/*; do [ -d $d ] && cp $d/env_*.json $d/captions_*.ass $d/*_audio.flac $d/*_tiktok.flac $H/talk/ 2>/dev/null; done
done
./blender/blender -v | head -1
echo SETUP_OK
