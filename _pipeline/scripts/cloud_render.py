"""
Bloxbury cloud render (runs inside Blender on the RunPod machine).
  pass 1:  blender -b Bloxbury_Part1.blend --python cloud_render.py -- frames
  pass 2:  blender -b Bloxbury_Part1.blend --python cloud_render.py -- video
Pass 1 renders every frame on the GPU (Cycles + OptiX) into ./frames/, skipping
frames that already exist, so it can be re-run after any interruption.
Pass 2 joins the frames with the soundtrack and captions into the final MP4.
"""
import bpy
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["frames"]
MODE = args[0]
src = bpy.data.scenes["Scene"]
fin = bpy.data.scenes["FINAL"]

# Optional test range, e.g. BLOX_FRAMES=1-30
if os.environ.get("BLOX_FRAMES"):
    a, b = (int(x) for x in os.environ["BLOX_FRAMES"].split("-"))
    src.frame_start, src.frame_end = a, b


def setup_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    order = ("CUDA",) if os.environ.get("BLOX_BACKEND", "").upper() == "CUDA" else ("OPTIX", "CUDA")
    for backend in order:
        try:
            prefs.compute_device_type = backend
            try:
                prefs.refresh_devices()
            except AttributeError:
                prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == backend]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == backend
                print("GPU:", backend, [d.name for d in devs], flush=True)
                return backend
        except Exception as e:
            print("No", backend, "-", e, flush=True)
    print("WARNING: no NVIDIA GPU found, rendering on CPU (very slow).", flush=True)
    return None


if MODE == "frames":
    backend = setup_gpu()
    src.render.engine = "CYCLES"
    c = src.cycles
    c.device = "GPU" if backend else "CPU"
    c.samples = 96
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    try:
        c.denoiser = "OPTIX" if backend == "OPTIX" else "OPENIMAGEDENOISE"
    except Exception:
        pass
    for attr, val in (("max_bounces", 6), ("diffuse_bounces", 3), ("glossy_bounces", 3),
                      ("transmission_bounces", 6), ("volume_bounces", 0),
                      ("volume_step_rate", 4.0), ("volume_max_steps", 256)):
        try:
            setattr(c, attr, val)
        except Exception:
            pass
    src.render.use_persistent_data = True       # keep the scene loaded between frames
    src.render.resolution_percentage = int(os.environ.get("BLOX_RES", "100"))
    src.render.filepath = "//frames/"
    src.render.use_overwrite = False           # skip frames already rendered
    src.render.use_placeholder = True
    try:
        src.render.image_settings.media_type = "IMAGE"
    except Exception:
        pass
    src.render.image_settings.file_format = "PNG"
    print("Rendering frames %d-%d..." % (src.frame_start, src.frame_end), flush=True)
    bpy.ops.render.render(animation=True, scene="Scene")
    print("FRAMES DONE", flush=True)

elif MODE == "video":
    # same as the "STEP 2" script inside the .blend, then render FINAL to MP4
    exec(bpy.data.texts["STEP 2 - make the video.py"].as_string())
    fin.frame_start = 1
    fin.frame_end = int(os.environ.get("BLOX_LAST", fin.frame_end))
    fin.render.resolution_percentage = int(os.environ.get("BLOX_RES", "100"))
    fin.render.filepath = "//Bloxbury_Part1_"
    bpy.ops.render.render(animation=True, scene="FINAL")
    print("VIDEO DONE", flush=True)
