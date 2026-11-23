# library_audit.py - FULL ASSET SHEET: renders every library prop/card alone (front view: VY=1) -> OUT/*.png.
# Run: OUT=/tmp/audit VY=1 python3 _tools/library_audit.py ; ONLY=name1,name2 for a subset; then audit_sheet.py OUT sheet.jpg 8
# Add every NEW library builder to the add(...) list so the audit always covers the whole library.
import os, math, bpy
from mathutils import Vector
os.chdir("/home/claude/bloxbury/_pipeline/scripts")
exec(open("/home/claude/studio_library/engine/scene_kit.py").read())      # Part 2's world + engine + library, via the kit
boot("p2", world="bloxbury", patches=BLOX_LOW_WINDOWS); load("recurring", "props2", "props3")
exec(open(LIB + "props4.py").read())
OUT = os.environ.get("OUT", "/tmp/audit"); os.makedirs(OUT, exist_ok=True)
ONLY = os.environ.get("ONLY", "")
s = bpy.context.scene
ITEMS = []                    # (name, root or bbox objects, kind)
G = [0]


def slot():
    i = G[0]; G[0] += 1
    return Vector((3000 + (i % 8) * 80, 3000 + (i // 8) * 80, 0))


def add(name, fn):
    if ONLY and not any(k in name for k in ONLY.split(",")): return
    loc = slot(); before = set(bpy.data.objects)
    fn(loc)
    allnew = [o for o in bpy.data.objects if o not in before]
    for o in allnew:                                  # builders that ignore loc (cards, monster) sit at the origin
        if o.parent is None and o.location.length < 30 and (o.location - loc).length > 30:
            o.location = o.location + loc
    new = [o for o in allnew if o.type == "MESH"]
    ITEMS.append((name, loc, new))


def holder(loc):
    return root_of("Hold", loc)


add("car civilian", lambda L: car("CarC", "civilian", loc=L))
add("car police", lambda L: car("CarP", "police", loc=L))
add("car taxi", lambda L: car("CarT", "taxi", loc=L))
add("bed", lambda L: bed("Bed", loc=L))
add("sofa", lambda L: sofa("Sofa", loc=L))
add("armchair", lambda L: armchair("Arm", loc=L))
add("dining set", lambda L: dining_set("Din", loc=L))
add("desk setup", lambda L: desk_setup("Desk", loc=L))
add("wardrobe", lambda L: wardrobe("Ward", loc=L))
add("bookshelf", lambda L: bookshelf("Book", loc=L))
add("tv unit", lambda L: tv_unit("TV", loc=L))
add("fridge", lambda L: fridge("Fridge", loc=L))
add("kitchen", lambda L: kitchen("Kit", loc=L))
add("floor lamp", lambda L: floor_lamp("Lamp", loc=L))
add("door", lambda L: door("Door", loc=L))
add("laptop", lambda L: laptop("Lap", loc=L))
add("plant", lambda L: plant("Plant", loc=L))
add("wall clock", lambda L: wall_clock("Clk", loc=L + Vector((0, 0, 2)))
)
add("wheelie bin", lambda L: wheelie_bin("Bin", loc=L))
add("hammer", lambda L: p2_hammer(holder(L + Vector((0, 0, 1)))))
add("crate", lambda L: p2_crate(L))
add("notebook", lambda L: p2_notebook(holder(L + Vector((0, 0, 1)))))
add("newspaper", lambda L: p2_newspaper("News", holder(L + Vector((0, 0, 1)))))
add("mug", lambda L: p2_mug(holder(L + Vector((0, 0, 1)))))
add("cafe table", lambda L: p2_cafe_table(L))
add("round bin", lambda L: p2_round_bin(L))
add("toaster", lambda L: p3_toaster(L))
add("props4 wall kit", lambda L: (picture("AP", L + Vector((-3, 0, 0)), (0, -1, 0), 3.5), switch("AS", L + Vector((-0.8, 0, 0)), (0, -1, 0), 3.0),
                                  outlet("AO", L + Vector((-0.8, 0, 0)), (0, -1, 0)), sconce("AC", L + Vector((1.2, 0, 0)), (0, -1, 0), z=4.0),
                                  calendar("ACal", L + Vector((3.6, 0, 0)), (0, -1, 0), z=3.6)))
add("props4 shelf+coats", lambda L: (shelf_books("ASh", L + Vector((-2.6, 0, 0)), (0, -1, 0), 4.5), coat_hooks("ACo", L + Vector((2.6, 0, 0)), (0, -1, 0), z=5.0)))
add("props4 radiator+clutter", lambda L: (radiator("ARad", L + Vector((-2.5, 0, 0)), (0, -1, 0)), floor_clutter("ACl", L + Vector((2.5, -2, 0)))))
add("knocker", lambda L: make_knocker("KnA"))
for nm, fn in (("card MILO", make_milo), ("card RAE", make_rae), ("card MAYOR", make_mayor), ("card DAN", make_dan),
               ("card NEIGHBOUR", make_neighbour), ("card MUM", make_mum)):
    def _mk(L, fn=fn):
        fn()
    add(nm, _mk)

# floor + neutral studio light under everything
fl = rb("AuditFloor", (2000, 2000, 0.2), Vector((3300, 3300, -0.1)), pmat("AuditFloorM", (200, 200, 205), rough=0.8), None, r=0.0)
sun = bpy.data.lights.new("AuditSun", "SUN"); sun.energy = 3.0; sun.angle = 0.2
so = bpy.data.objects.new("AuditSun", sun); s.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(30))
w = s.world; w.use_nodes = True
bg = [n for n in w.node_tree.nodes if n.type == "BACKGROUND"]
for n in bg: n.inputs[0].default_value = (0.55, 0.6, 0.7, 1); n.inputs[1].default_value = 0.8
cam = bpy.data.objects.new("ACam", bpy.data.cameras.new("ACam")); s.collection.objects.link(cam); s.camera = cam
cam.data.lens = 40; cam.data.sensor_width = 36
s.render.engine = "CYCLES"; s.cycles.samples = int(os.environ.get("SAMPLES", 16)); s.cycles.use_denoising = True
s.render.resolution_x = s.render.resolution_y = int(os.environ.get("RES", 320))
for o in bpy.data.objects: o.animation_data_clear()
s.frame_set(1); bpy.context.view_layer.update()
for name, loc, objs in ITEMS:
    pts = [o.matrix_world @ Vector(c) for o in objs if not o.hide_render for c in o.bound_box]
    pts = [p for p in pts if (p - loc).length < 40]
    if not pts: print("EMPTY", name); continue
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (mn + mx) / 2; r = max((mx - mn).length / 2, 0.6)
    d = r / math.tan(math.atan(18 / 40)) * 1.15
    dirn = Vector((0.55, float(os.environ.get("VY", "-1")), 0.5)).normalized()
    cam.location = c + dirn * d; cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = "%s/%s.png" % (OUT, name.replace(" ", "_")); bpy.ops.render.render(write_still=True)
print("AUDIT DONE", len(ITEMS))
