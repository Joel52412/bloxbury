# Bloxbury render image: RunPod's PyTorch base (already cached on most RunPod hosts, so pulls are fast)
# + everything pod_setup.sh used to install on every pod: Blender 5.3, its libs, ffmpeg, fonts, pillow/numpy.
# Built by .github/workflows/render-image.yml -> ghcr.io/joel52412/bloxbury-render:5.3
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
      wget xz-utils ffmpeg libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 \
      libgl1 libegl1 fonts-dejavu-core git \
 && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /tmp/blender.tar.xz https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz \
 && mkdir -p /opt/blender && tar -xf /tmp/blender.tar.xz -C /opt/blender --strip-components=1 && rm /tmp/blender.tar.xz \
 && PY=$(ls /opt/blender/5.3/python/bin/python3* | head -1) && $PY -m ensurepip >/dev/null 2>&1; \
    PY=$(ls /opt/blender/5.3/python/bin/python3* | head -1) && $PY -m pip install -q --no-cache-dir pillow numpy \
 && /opt/blender/blender -v | head -1
ENV BLOXBURY_IMAGE=5.3
