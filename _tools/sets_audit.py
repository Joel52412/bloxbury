# sets_audit.py - wide views of every set (town, Milo's room, kitchen, hallway) with dressing + town detail. OUT=/tmp/sets
import os, math, bpy
from mathutils import Vector as V
os.chdir("/home/claude/bloxbury/_pipeline/scripts")
exec(open("/home/claude/studio_library/engine/scene_kit.py").read())      # Part 2's world + engine + library, via the kit
boot("p2", world="bloxbury", patches=BLOX_LOW_WINDOWS); load("recurring", "props2", "props3")
exec(open(LIB + "props4.py").read())
KO = V((520, 0, 400)); p3_kitchen_set(KO); HO = V((560, 0, 400)); p3_hallway_set(HO)
dress_kitchen(KO); dress_hallway(HO); dress_bedroom(); p3_hollow_closet()
if os.environ.get("TOWN", "1") == "1": exec(open(LIB + "props5.py").read()); detail_town(houses)
s = bpy.context.scene; OUT = os.environ.get("OUT", "/tmp/sets"); os.makedirs(OUT, exist_ok=True)
set_day(0.0) if os.environ.get("DAY", "1") == "1" else set_night(0.0)
cam = bpy.data.objects.new("SC", bpy.data.cameras.new("SC")); s.collection.objects.link(cam); s.camera = cam; cam.data.sensor_width = 36
VIEWS = [("town_high", (95, 40, 45), (20, -30, 0), 24), ("town_street", (38, -8, 5.5), (60, -40, 4), 26),
         ("town_rae", (58, -14, 6), (48, -30, 4), 28), ("milo_room", (-9, -33, 9), (5, -46, 3), 20),
         ("kitchen", KO + V((10, -8.5, 7)), KO + V((-4, 6, 3)), 20), ("hallway", HO + V((3.5, -12.5, 6)), HO + V((-1, 10, 4)), 22)]
s.render.engine = "CYCLES"; s.cycles.samples = 16; s.cycles.use_denoising = True
s.render.resolution_x, s.render.resolution_y = 432, 768
for o in bpy.data.objects: o.animation_data_clear()
for n, p, t, l in VIEWS:
    cam.location = V(p); cam.rotation_euler = (V(t) - V(p)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = l
    s.render.filepath = "%s/%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
