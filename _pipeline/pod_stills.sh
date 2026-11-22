#!/bin/sh
# pod_stills.sh - render an ASSET SHEET (or any stills script) on the pod's GPU at FINAL quality (Joel 22:25):
# 1080x1920-class stills (SCALE=2 of the sheet's 540x960 base), 32 samples, OptiX, cinematic look. Then a labelled
# contact sheet (/workspace/stills/contact.jpg, for Claude via base64) and stills.zip (Joel's download link).
# Usage: sh pod_stills.sh part3_assets.py [SHOTS=all] [SCALE=2]
S=$1; SH=${2:-all}; SC=${3:-2}; OUT=/workspace/stills; mkdir -p $OUT
echo "stage=rendering" > /workspace/stills_status
CUDA_VISIBLE_DEVICES=0 ENGINE=GPU SAMPLES=32 SCALE=$SC SHOTS=$SH OUT=$OUT \
  /workspace/blender/blender -b --python /home/claude/bloxbury-blender/$S > /workspace/stills.log 2>&1
PY=$(ls /workspace/blender/5.3/python/bin/python3* | head -1)
$PY - <<'PYEOF'
import glob, os
from PIL import Image, ImageDraw, ImageFont
fs = sorted(glob.glob("/workspace/stills/*.png")); T = 300
ims = []
for f in fs:
    im = Image.open(f).convert("RGB"); im.thumbnail((T, int(T * 1.9))); ims.append((os.path.basename(f)[:-4], im))
cols = 6; rows = (len(ims) + cols - 1) // cols; W = cols * (T + 10) + 10; H = rows * (int(T * 1.9) + 40) + 10
sheet = Image.new("RGB", (W, H), (18, 18, 22)); d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype("/workspace/bloxbury/assets/fonts/Poppins-Bold.ttf", 16)
except Exception: f = ImageFont.load_default()
for i, (n, im) in enumerate(ims):
    x = 10 + (i % cols) * (T + 10); y = 10 + (i // cols) * (int(T * 1.9) + 40)
    sheet.paste(im, (x, y)); d.text((x, y + im.size[1] + 6), n, font=f, fill=(230, 230, 230))
sheet.save("/workspace/stills/contact.jpg", quality=80)
PYEOF
cd /workspace && rm -f stills.zip && $PY -c "import shutil; shutil.make_archive('/workspace/stills', 'zip', '/workspace/stills')"
grep -c Saved /workspace/stills.log > /dev/null && echo "stage=done" > /workspace/stills_status || echo "stage=failed" > /workspace/stills_status
cat /workspace/stills_status
