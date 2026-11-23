"""
BLOXBURY — PART 1 "THE RULE"  (Blender scene builder, about 1:21 long)

HOW TO USE
  1. Put part1_audio.wav in the same folder as this script
     (robloxshorts\series\bloxbury).
  2. Open Blender (4.2 or newer). Go to the Scripting tab.
  3. Click "Open", choose this file, then click "Run Script" (the play button).
  4. Render > Render Animation (Ctrl+F12). Out comes the FINISHED video:
     1080x1920, about 1:28, with voiceover, sound effects and captions,
     saved next to this script as Bloxbury_Part1_....mp4

The script builds two scenes: "Scene" (the 3D town) and "FINAL" (3D render +
soundtrack + captions). FINAL is the one that renders. To look around the 3D
town, switch the scene selector (top right) back to "Scene".
Running the script again deletes everything and rebuilds it.
"""

import bpy
import math
import os
import random
from mathutils import Vector, Matrix, Quaternion

# ---------------------------------------------------------------- SETTINGS
FPS = 30
ENGINE = "EEVEE"          # "EEVEE" (fast) or "CYCLES" (slower, prettier)
SAMPLES = 32
PROJECT_DIR = r"C:\Users\frimp\Downloads\robloxshorts\series\bloxbury"
AUDIO_NAME = "part1_audio.wav"


def _project_dir():
    """Folder of this script if Blender knows it, else PROJECT_DIR, else home."""
    for t in bpy.data.texts:
        fp = bpy.path.abspath(t.filepath) if t.filepath else ""
        if fp.endswith(".py") and os.path.exists(os.path.join(os.path.dirname(fp), AUDIO_NAME)):
            return os.path.dirname(fp)
    if os.path.isdir(PROJECT_DIR):
        return PROJECT_DIR
    return os.path.expanduser("~")


OUT_DIR = _project_dir()
OUTPUT = os.path.join(OUT_DIR, "Bloxbury_Part1_")
AUDIO_FILE = os.path.join(OUT_DIR, AUDIO_NAME)
SHOW_CAPTIONS = False     # captions are added in CapCut from the voiceover (True = rough 3D captions)

# Optional: a folder holding knock.wav, hammer.wav, drone.wav, tick.wav,
# creak.wav, sting.wav, lightoff.wav. Leave "" to skip sound (timeline markers
# still show where every sound goes).
SOUND_DIR = ""

random.seed(7)


# Retime: the animation was laid out first, then stretched to fit the voiceover.
# Each (time, extra) inserts `extra` seconds at `time` (original timeline).
WARP = [(15.55, 1.6), (20.5, 0.6), (25.4, 0.6), (54.4, -1.0)]


class Frame(int):
    """An exact frame number (not warped again)."""


def warp(t):
    return t + sum(extra for at, extra in WARP if t >= at)


def F(t):
    """Seconds (original timeline) -> frame number in the final video."""
    if isinstance(t, Frame):
        return int(t)
    return int(round(warp(t) * FPS)) + 1


# The layout uses Roblox-style coordinates (Y up, 1 unit = 1 stud) so it
# matches the Roblox Studio kit. R() converts to Blender (Z up).
def R(x, y, z):
    return Vector((x, -z, y))


def RS(sx, sy, sz):
    return Vector((sx, sz, sy))


# ---------------------------------------------------------------- RESET
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights,
             bpy.data.cameras, bpy.data.actions, bpy.data.worlds):
    for block in list(coll):
        coll.remove(block)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

scene = bpy.data.scenes.get("Scene") or bpy.context.scene
try:
    bpy.context.window.scene = scene
except Exception:
    pass
if bpy.data.scenes.get("FINAL"):
    bpy.data.scenes.remove(bpy.data.scenes["FINAL"])
scene.timeline_markers.clear()
if scene.sequence_editor:
    scene.sequence_editor_clear()


def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


COL_TOWN = collection("Town")
COL_CHARS = collection("Characters")
COL_LIGHTS = collection("Lights")
COL_CAM = collection("Camera")


# ---------------------------------------------------------------- HELPERS
def set_interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


_KEY_LOG = []


def key(datablock, path, t, value=None, interp="CONSTANT", index=-1):
    """Insert a keyframe at time t (seconds). interp applies to the segment after it."""
    if value is not None:
        setattr(datablock, path, value)
    set_interp(interp)
    datablock.keyframe_insert(data_path=path, frame=F(t), index=index)
    try:
        full = datablock.path_from_id(path)
    except Exception:
        full = path
    _KEY_LOG.append((datablock.id_data, full, F(t), interp))


def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    out = []
    if getattr(act, "layers", None):
        for layer in act.layers:
            for strip in layer.strips:
                slot = getattr(ad, "action_slot", None)
                cb = strip.channelbag(slot) if slot else None
                if cb:
                    out += list(cb.fcurves)
    if not out:
        out = list(getattr(act, "fcurves", []))
    return out


def apply_interpolation():
    """Sets every keyframe's interpolation explicitly (works in all Blender versions)."""
    cache = {}
    for idb, path, frame, interp in _KEY_LOG:
        if idb not in cache:
            by_path = {}
            for fc in _fcurves(idb):
                by_path.setdefault(fc.data_path, []).append(fc)
            cache[idb] = by_path
        for fc in cache[idb].get(path, []):
            for kp in fc.keyframe_points:
                if int(round(kp.co.x)) == frame:
                    kp.interpolation = interp


def to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    return tuple(to_lin(c) for c in rgb)


def make_unit_cube():
    me = bpy.data.meshes.new("UnitCube")
    v = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], faces)
    me.update()
    me.materials.append(None)
    return me


def make_unit_cylinder(n=24):
    me = bpy.data.meshes.new("UnitCylinder")
    v = []
    for i in range(n):
        a = 2 * math.pi * i / n
        v += [(0.5 * math.cos(a), 0.5 * math.sin(a), -0.5), (0.5 * math.cos(a), 0.5 * math.sin(a), 0.5)]
    faces = [(2 * i, 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1, 2 * i + 1) for i in range(n)]
    faces.append(tuple(2 * i for i in reversed(range(n))))
    faces.append(tuple(2 * i + 1 for i in range(n)))
    me.from_pydata(v, [], faces)
    me.update()
    me.materials.append(None)
    return me


CUBE = make_unit_cube()
CYL = make_unit_cylinder()

_mats = {}


def set_blended(m):
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
            break
        except Exception:
            pass


def mat(name, rgb, emit=0.0, rough=0.6, alpha=1.0, metallic=0.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get("Principled BSDF")
    col = lin(rgb)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        set_blended(m)
    m.diffuse_color = (*col, 1)
    _mats[name] = m
    return m


def tex_mat(name, rgb, kind, rough=0.8):
    """Material with procedural texture: grass, asphalt, plaster, planks, slabs, siding, tiles."""
    if name in _mats:
        return _mats[name]
    m = mat(name, rgb, rough=rough)
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    col = lin(rgb)
    bump = nt.nodes.new("ShaderNodeBump")
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if kind in ("grass", "asphalt", "plaster"):
        sc, lo, hi, fine, bs = {"grass": (0.12, 0.72, 1.2, 9.0, 0.35), "asphalt": (0.5, 0.82, 1.12, 6.0, 0.2),
                                "plaster": (0.15, 0.93, 1.05, 3.0, 0.03)}[kind]
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = sc
        noise.inputs["Detail"].default_value = 6
        nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = lo
        mr.inputs["To Max"].default_value = hi
        nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Color"].default_value = (*col, 1)
        nt.links.new(mr.outputs["Result"], hsv.inputs["Value"])
        nt.links.new(hsv.outputs["Color"], b.inputs["Base Color"])
        n2 = nt.nodes.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = fine
        nt.links.new(geo.outputs["Position"], n2.inputs["Vector"])
        nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = bs
    else:
        scale, bw, rh, mortar, vertical = {"planks": (0.5, 3.0, 0.5, 0.03, False), "slabs": (0.25, 1.0, 1.0, 0.025, False),
                                           "siding": (0.7, 40.0, 0.55, 0.05, True), "tiles": (0.9, 0.7, 0.45, 0.06, False)}[kind]
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = scale
        br.inputs["Brick Width"].default_value = bw
        br.inputs["Row Height"].default_value = rh
        br.inputs["Mortar Size"].default_value = mortar
        br.inputs["Color1"].default_value = (*[c * 0.9 for c in col], 1)
        br.inputs["Color2"].default_value = (*[c * 1.08 for c in col], 1)
        br.inputs["Mortar"].default_value = (*[c * 0.55 for c in col], 1)
        if vertical:  # walls: use (x + y, z) so both wall directions get horizontal boards
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(geo.outputs["Position"], sep.inputs[0])
            add = nt.nodes.new("ShaderNodeMath")
            add.operation = "ADD"
            nt.links.new(sep.outputs["X"], add.inputs[0])
            nt.links.new(sep.outputs["Y"], add.inputs[1])
            comb = nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(add.outputs[0], comb.inputs["X"])
            nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
            nt.links.new(comb.outputs[0], br.inputs["Vector"])
        else:
            nt.links.new(geo.outputs["Position"], br.inputs["Vector"])
        nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = 0.25
    return m


def link(ob, col):
    col.objects.link(ob)
    return ob


def solid(name, mesh, size, loc, material, rot=(0, 0, 0), parent=None, col=COL_TOWN):
    ob = bpy.data.objects.new(name, mesh)
    link(ob, col)
    ob.scale = size
    ob.location = loc
    ob.rotation_euler = rot
    slot = ob.material_slots[0]
    slot.link = "OBJECT"
    slot.material = material
    if parent:
        ob.parent = parent
    return ob


def box(name, size, loc, material, **kw):
    return solid(name, CUBE, size, loc, material, **kw)


def cyl(name, size, loc, material, **kw):
    return solid(name, CYL, size, loc, material, **kw)


def empty(name, loc, col=COL_TOWN, parent=None):
    ob = bpy.data.objects.new(name, None)
    link(ob, col)
    ob.location = loc
    ob.empty_display_size = 2
    if parent:
        ob.parent = parent
    return ob


def load_font():
    for p in ("C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            try:
                return bpy.data.fonts.load(p, check_existing=True)
            except Exception:
                pass
    return None


FONT = load_font()


def text(name, body, size, material, wrap=None, extrude=0.0, offset=0.0, col=COL_TOWN):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.offset = offset
    if FONT:
        cu.font = FONT
    if wrap:
        cu.text_boxes[0].width = wrap
        cu.text_boxes[0].x = -wrap / 2
    ob = bpy.data.objects.new(name, cu)
    link(ob, col)
    ob.data.materials.append(material)
    return ob


def orient(ob, normal, right):
    """Turn a text object so it faces `normal` and reads along `right`."""
    n = Vector(normal).normalized()
    r = Vector(right).normalized()
    up = n.cross(r)
    m = Matrix((r, up, n)).transposed()
    ob.rotation_euler = m.to_euler()


def visible(ob, windows):
    """windows = [(t_on, t_off), ...]. Hidden outside the windows."""
    key(ob, "hide_render", 0, True)
    key(ob, "hide_viewport", 0, True)
    for on, off in windows:
        key(ob, "hide_render", on, False)
        key(ob, "hide_viewport", on, False)
        if off is not None:
            key(ob, "hide_render", off, True)
            key(ob, "hide_viewport", off, True)


def facing_yaw(pos, target):
    d = (target - pos)
    return math.atan2(-d.x, d.y)


# ---------------------------------------------------------------- COLOURS
C = dict(
    grass=(91, 154, 76), road=(52, 52, 58), pavement=(170, 170, 165), roof=(96, 62, 52),
    wood=(124, 84, 55), warm=(255, 210, 140), glass=(150, 190, 215), metal=(40, 40, 45),
    fog=(150, 150, 158), white=(245, 245, 245),
)
PALETTE = [(236, 224, 200), (170, 205, 230), (240, 190, 190), (200, 230, 190),
           (245, 225, 150), (210, 200, 235), (230, 230, 230)]

M_ROOF = tex_mat("Roof", C["roof"], "tiles")
M_WOOD = mat("Wood", C["wood"], rough=0.8)
M_METAL = mat("Metal", C["metal"], rough=0.4, metallic=0.6)
M_BLACK = mat("Black", (20, 20, 20))
M_WHITE = mat("White", C["white"], rough=0.3)

# One shared window material: glass by day, glowing at night (keyed later)
M_WINDOW = bpy.data.materials.new("Window")
try:
    M_WINDOW.use_nodes = True
except Exception:
    pass
_wb = M_WINDOW.node_tree.nodes.get("Principled BSDF")
_wb.inputs["Base Color"].default_value = (*lin(C["glass"]), 1)
_wb.inputs["Roughness"].default_value = 0.35
_wb.inputs["Emission Color"].default_value = (*lin(C["warm"]), 1)
_wb.inputs["Emission Strength"].default_value = 0.0

# ---------------------------------------------------------------- GROUND + ROAD
box("Ground", RS(560, 1, 320), R(0, -0.5, 0), tex_mat("Grass", (84, 156, 66), "grass", rough=0.95))
box("Road", RS(560, 0.2, 24), R(0, 0.1, 0), tex_mat("Road", C["road"], "asphalt", rough=0.85))
for z in (-14, 14):
    box("Pavement", RS(560, 0.4, 4), R(0, 0.2, z), tex_mat("Pavement", C["pavement"], "slabs"))
M_LINE = mat("RoadLine", (255, 255, 255))
for x in range(-270, 271, 12):
    box("RoadLine", RS(6, 0.05, 0.6), R(x, 0.22, 0), M_LINE)

# ---------------------------------------------------------------- HOUSES
HOUSE_LIGHTS = []
WINDOW_PARTS = []


def house_light(cx, cz, front_z, dirn):
    data = bpy.data.lights.new("WindowGlow", "POINT")
    data.energy = 0
    data.color = lin(C["warm"])
    data.shadow_soft_size = 2
    ob = bpy.data.objects.new("WindowGlow", data)
    link(ob, COL_LIGHTS)
    ob.location = R(cx, 9, front_z + dirn * 3)
    HOUSE_LIGHTS.append(data)


def solid_house(name, cx, cz, colour):
    dirn = -1 if cz > 0 else 1
    root = empty(name, R(cx, 0, cz))
    m_body = tex_mat("House_" + name, colour, "siding")
    box("Body", RS(24, 14, 20), R(0, 7, 0), m_body, parent=root)
    box("Roof", RS(26, 2, 22), R(0, 15, 0), M_ROOF, parent=root)
    box("Attic", RS(16, 4, 14), R(0, 18, 0), M_ROOF, parent=root)
    fz = dirn * 10
    box("Door", RS(5, 9, 0.4), R(0, 4.5, fz + dirn * 0.2), M_WOOD, parent=root)
    for ox in (-7, 7):
        WINDOW_PARTS.append(box("Window", RS(5, 4, 0.4), R(ox, 9, fz + dirn * 0.2), M_WINDOW, parent=root))
    house_light(cx, cz, cz + fz, dirn)
    return root


def milo_house(cx, cz, colour):
    """Hollow house with a filmable interior."""
    dirn = -1 if cz > 0 else 1
    W, H, D, T = 24, 14, 20, 1
    root = empty("MiloHouse", R(cx, 0, cz))
    m_wall = tex_mat("MiloWalls", colour, "plaster")
    box("Floor", RS(W, 0.4, D), R(0, 0.2, 0), tex_mat("Floorboards", (150, 110, 75), "planks", rough=0.6), parent=root)
    box("WallBack", RS(W, H, T), R(0, H / 2, -dirn * (D / 2 - T / 2)), m_wall, parent=root)
    box("WallLeft", RS(T, H, D), R(-W / 2 + T / 2, H / 2, 0), m_wall, parent=root)
    box("WallRight", RS(T, H, D), R(W / 2 - T / 2, H / 2, 0), m_wall, parent=root)
    fz = dirn * (D / 2 - T / 2)
    # Front wall either side of the door, with real window holes (4 wide, 4 tall, from y=7 to 11)
    for side in (-1, 1):
        cx_ = side * 7.25
        box("WallFront", RS(2.75, H, T), R(cx_ - 3.375, H / 2, fz), m_wall, parent=root)
        box("WallFront", RS(2.75, H, T), R(cx_ + 3.375, H / 2, fz), m_wall, parent=root)
        box("WallFront", RS(4, 7, T), R(cx_, 3.5, fz), m_wall, parent=root)
        box("WallFront", RS(4, H - 11, T), R(cx_, 11 + (H - 11) / 2, fz), m_wall, parent=root)
    box("WallFrontTop", RS(5, H - 9, T), R(0, 9 + (H - 9) / 2, fz), m_wall, parent=root)
    box("FrontDoor", RS(5, 9, 0.4), R(0, 4.5, fz), M_WOOD, parent=root)
    for ox in (-7.25, 7.25):
        WINDOW_PARTS.append(box("Window", RS(4, 4, 0.15), R(ox, 9, fz), M_WINDOW, parent=root))
    box("Ceiling", RS(W, 1, D), R(0, H + 0.5, 0), mat("Ceiling", (235, 235, 230)), parent=root)
    box("Roof", RS(W + 2, 2, D + 2), R(0, H + 2, 0), M_ROOF, parent=root)
    box("Attic", RS(16, 4, 14), R(0, H + 5, 0), M_ROOF, parent=root)
    box("Bed", RS(6, 2, 9), R(-7, 1.4, 3 * -dirn), mat("Bedsheet", (70, 90, 160), rough=0.9), parent=root)
    box("Pillow", RS(4.5, 0.8, 2), R(-7, 2.8, 6.5 * -dirn), M_WHITE, parent=root)
    closet_z = -dirn * (D / 2 - T - 1.5)
    box("ClosetBox", RS(6, 10, 3), R(7, 5, closet_z), mat("ClosetWood", (110, 75, 50), rough=0.8), parent=root)
    door_z = closet_z + dirn * 1.6
    # Closet door hinges on its +X edge
    hinge = empty("ClosetHinge", R(7 + 2.5, 4.9, door_z), parent=root)
    hinge.empty_display_size = 0.5
    box("ClosetDoor", RS(5, 9, 0.2), R(-2.5, 0, 0), mat("ClosetDoor", (140, 95, 60), rough=0.8), parent=hinge)
    handle = empty("ClosetHandle", R(-4.3, -0.4, dirn * 0.25), parent=hinge)
    handle.empty_display_size = 0.3
    box("HandleBar", RS(0.9, 0.3, 0.3), R(0.3, 0, 0), mat("Brass", (200, 180, 90), rough=0.3, metallic=0.8), parent=handle)
    # Wall clock
    clock = box("Clock", RS(0.2, 3, 4), R(-W / 2 + T + 0.1, 9, 0), M_BLACK, parent=root)
    return root, hinge, handle


houses = {}
for i, x in enumerate((-150, -100, -50, 100, 150)):
    houses["House_N%d" % (i + 1)] = solid_house("House_N%d" % (i + 1), x, 40, PALETTE[i])
houses["RaeHouse"] = solid_house("RaeHouse", 50, 40, (190, 170, 220))
for i, x in enumerate((-150, -100, -50, 0, 50, 100, 150)):
    houses["House_S%d" % (i + 1)] = solid_house("House_S%d" % (i + 1), x, -40, PALETTE[(i + 3) % len(PALETTE)])
MILO, CLOSET_HINGE, CLOSET_HANDLE = milo_house(0, 40, (225, 215, 195))
house_light(0, 40, 30.5, -1)

# Clock faces: two text objects, swapped at 3:00
M_RED_TEXT = mat("ClockRed", (255, 60, 60), emit=4)
CLOCK_TEXTS = {}
for label in ("2:59 AM", "3:00 AM"):
    t = text("Clock " + label, label, 0.9, M_RED_TEXT)
    t.location = R(-10.75, 9, 40)
    orient(t, (1, 0, 0), (0, 1, 0))
    CLOCK_TEXTS[label] = t

# Boarding planks (appear during the neighbour shot)
PLANKS = []
for i, ang in enumerate((14, -14)):
    PLANKS.append(box("BoardPlank%d" % (i + 1), RS(6.5, 0.8, 0.3), R(-57, 9, -29.4),
                      mat("Plank", (160, 120, 80), rough=0.8), rot=(0, -math.radians(ang), 0)))

# Fence between Milo and Rae
M_FENCE = mat("Fence", (245, 245, 240))
for z in range(24, 53, 2):
    box("Picket", RS(0.4, 4, 1.2), R(25, 2, z), M_FENCE)
for y in (1.5, 3.2):
    box("Rail", RS(0.3, 0.5, 28), R(25, y, 38), M_FENCE)

# The Mayor's mansion (no front door)
M_MARBLE = mat("Marble", (245, 245, 245), rough=0.25)
box("MansionBody", RS(40, 26, 52), R(245, 13, 0), M_MARBLE)
box("MansionRoof", RS(44, 3, 56), R(245, 27.5, 0), mat("MansionRoof", (60, 60, 70)))
for z in (-12, -4, 4, 12):
    cyl("Column", (2, 2, 24), R(223, 12, z), M_MARBLE)
M_DARKGLASS = mat("DarkGlass", (30, 30, 40), rough=0.05)
for y in (8, 18):
    for z in (-18, -8, 8, 18):
        box("MansionWindow", RS(0.4, 5, 4), R(224.9, y, z), M_DARKGLASS)

# Welcome sign
for ox in (-7, 7):
    box("SignPost", RS(0.8, 8, 0.8), R(-200 + ox, 4, -20), M_WOOD)
box("SignBoard", RS(18, 7, 0.6), R(-200, 7, -20), mat("SignBoard", (250, 245, 225)))
t = text("SignTitle", "Welcome to Bloxbury", 1.6, mat("SignGreen", (40, 90, 50)))
t.location = R(-200, 8.3, -19.6)
orient(t, (0, -1, 0), (1, 0, 0))
t = text("SignPopulation", "Population 47", 1.2, mat("SignGrey", (60, 60, 60)))
t.location = R(-200, 5.6, -19.6)
orient(t, (0, -1, 0), (1, 0, 0))

# Street lamps (each with its own material so they flicker independently)
LAMPS = []
for x in range(-250, 201, 50):
    for z in (-15, 15):
        s = 1 if z > 0 else -1
        box("LampPole", RS(0.8, 16, 0.8), R(x, 8, z), M_METAL)
        box("LampArm", RS(0.5, 0.5, 3), R(x, 15.8, z - s * 1.5), M_METAL)
        m = mat("Lamp_%d_%d" % (x, z), C["warm"], emit=12)
        head = box("StreetLamp", RS(2.4, 0.8, 2.4), R(x, 15.4, z - s * 3), m)
        ld = bpy.data.lights.new("LampLight", "SPOT")
        ld.energy = 20000
        ld.color = lin(C["warm"])
        ld.spot_size = math.radians(110)
        ld.shadow_soft_size = 1
        lo = bpy.data.objects.new("LampLight", ld)
        link(lo, COL_LIGHTS)
        lo.location = R(x, 14.8, z - s * 3)  # spot points down by default
        LAMPS.append((head, m, ld))

# Moving van (pivot on the road, drives along +X)
VAN = empty("MoveVan", R(-275, 0, -6))
box("VanBody", RS(14, 6, 7), R(0, 4.5, 0), M_WHITE, parent=VAN)
box("VanCab", RS(4, 4.5, 7), R(9, 3.75, 0), mat("VanRed", (200, 60, 50)), parent=VAN)
box("VanWindshield", RS(0.2, 2, 6), R(11.05, 4.5, 0), M_DARKGLASS, parent=VAN)
M_TYRE = mat("Tyre", (25, 25, 25), rough=0.9)
for ox in (-4.5, 7.5):
    for oz in (-3.6, 3.6):
        cyl("Wheel", (3, 3, 1.2), R(ox, 1.5, oz), M_TYRE, rot=(math.radians(90), 0, 0), parent=VAN)
vl = text("VanLabel", "BLOXBURY MOVERS\nReturn to: Bloxbury", 1.1, mat("VanText", (200, 60, 50)))
vl.parent = VAN
vl.location = R(0, 4.5, 3.56)
orient(vl, (0, -1, 0), (1, 0, 0))

# The Hollow (fog walls at the map edge)
M_FOG = mat("Hollow", C["fog"], alpha=0.8, rough=1)
box("Hollow_W", RS(6, 80, 340), R(-285, 40, 0), M_FOG)
box("Hollow_E", RS(6, 80, 340), R(285, 40, 0), M_FOG)
box("Hollow_N", RS(576, 80, 6), R(0, 40, 165), M_FOG)
box("Hollow_S", RS(576, 80, 6), R(0, 40, -165), M_FOG)


# ---------------------------------------------------------------- CHARACTERS
# Roblox R6 avatars: classic rounded-cylinder head, 1x1x2 limbs, 2x1x2 torso.
# Clothing is "printed" flat on the body like Roblox Shirts/Pants; hair, hats,
# the key necklace and held items are accessories/tools. Everything here could
# be made on a real Roblox avatar. Faces are original decal-style expressions
# that can be swapped during the animation with set_face().
import bmesh

_RBOX = {}


def rbox_mesh(size, r):
    k = tuple(round(v, 3) for v in size) + (round(r, 3),)
    if k in _RBOX:
        return _RBOX[k]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    r = min(r, min(size) * 0.45)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=3, affect="EDGES",
                    profile=0.5, clamp_overlap=True)
    me = bpy.data.meshes.new("RBox")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(None)
    _RBOX[k] = me
    return me


def make_sphere():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5)
    me = bpy.data.meshes.new("UnitSphere")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(None)
    return me


HEAD_R = 0.6   # classic head: 1.2 wide, 1.2 tall, rounded rims


def make_roblox_head():
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40,
                          radius1=HEAD_R, radius2=HEAD_R, depth=1.2)
    rim = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-4]
    bmesh.ops.bevel(bm, geom=rim, offset=0.26, segments=8, affect="EDGES", profile=0.5, clamp_overlap=True)
    me = bpy.data.meshes.new("RobloxHead")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = abs(p.normal.z) < 0.999
    me.materials.append(None)
    return me


SPHERE = make_sphere()
HEAD_MESH = make_roblox_head()


def rpart(name, size, loc, material, parent, r=0.04, rot=(0, 0, 0)):
    return solid(name, rbox_mesh(size, r), (1, 1, 1), loc, material, rot=rot, parent=parent, col=COL_CHARS)


def ball(name, size, loc, material, parent, rot=(0, 0, 0)):
    return solid(name, SPHERE, size, loc, material, rot=rot, parent=parent, col=COL_CHARS)


def disc(name, diam, thick, loc, material, parent, axis="Y"):
    rot = (math.radians(90), 0, 0) if axis == "Y" else (0, math.radians(90), 0)
    return solid(name, CYL, (diam, diam, thick), loc, material, rot=rot, parent=parent, col=COL_CHARS)


def tube(name, points, radius, material, parent):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS" if len(points) > 2 else "POLY")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1)
    if len(points) > 2:
        sp.use_endpoint_u = True
        sp.order_u = 3
    cu.materials.append(material)
    ob = bpy.data.objects.new(name, cu)
    link(ob, COL_CHARS)
    ob.parent = parent
    return ob


M_INK = mat("FaceInk", (20, 20, 24), rough=0.4)
M_EYEWHITE = mat("FaceWhite", (252, 252, 252), rough=0.4)
M_SHINE = mat("FaceShine", (255, 255, 255), emit=0.6)
M_TEAR = mat("FaceTear", (120, 195, 255), rough=0.2)
M_TONGUE = mat("FaceTongue", (225, 85, 95), rough=0.5)
M_BLUSH = mat("FaceBlush", (245, 140, 140), rough=0.8)
M_BRASS = mat("Brass", (214, 168, 64), rough=0.3, metallic=0.9)


# ---- face decals ------------------------------------------------------------
def surf_y(x):
    return math.sqrt(max(HEAD_R ** 2 - x * x, 0.0))


class Face:
    """Builds one expression as flat shapes hugging the front of the head."""

    def __init__(self, neck, name):
        self.neck, self.name, self.objs = neck, name, []

    def oval(self, x, z, w, h, m, lift=0.0):
        a = -math.asin(max(-0.99, min(0.99, x / HEAD_R)))
        ob = ball("F_" + self.name, (w, 0.035, h), Vector((x, surf_y(x) - 0.006 + lift, z + 0.6)), m, self.neck,
                  rot=(0, 0, a))
        self.objs.append(ob)

    def line(self, pts, m, r=0.028, lift=0.0):
        p3 = [(x, surf_y(x) + 0.004 + lift, z + 0.6) for x, z in pts]
        self.objs.append(tube("F_" + self.name, p3, r, m, self.neck))

    # building blocks
    def eyes(self, w=0.13, h=0.24, z=0.1, shine=True, dx=0.2):
        for sx in (-dx, dx):
            self.oval(sx, z, w, h, M_INK)
            if shine:
                self.oval(sx + w * 0.22, z + h * 0.28, w * 0.38, h * 0.28, M_SHINE, lift=0.008)

    def wide_eyes(self, w=0.2, h=0.28, z=0.12, pupil=0.06, look=0.0):
        for sx in (-0.2, 0.2):
            self.oval(sx, z, w, h, M_EYEWHITE)
            self.oval(sx + look, z, pupil, pupil * 1.3, M_INK, lift=0.008)


def expr_friendly(f, signature=True):
    f.eyes()
    if signature:  # Milo's lopsided smirk
        f.line([(-0.18, -0.15), (-0.08, -0.22), (0.06, -0.22), (0.16, -0.17), (0.23, -0.08)], M_INK)
    else:
        f.line([(-0.16, -0.16), (0, -0.23), (0.16, -0.16)], M_INK)


def expr_laugh(f):
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.08, 0.06), (sx, 0.14), (sx + 0.08, 0.06)], M_INK, r=0.032)
    f.oval(0, -0.2, 0.36, 0.22, M_INK)
    f.oval(0, -0.27, 0.18, 0.08, M_TONGUE, lift=0.008)
    f.oval(0, -0.12, 0.26, 0.05, M_EYEWHITE, lift=0.008)
    for sx in (-0.34, 0.34):
        f.oval(sx, -0.05, 0.14, 0.07, M_BLUSH, lift=0.002)


def expr_shocked(f):
    f.wide_eyes()
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.1, 0.3), (sx, 0.34), (sx + 0.1, 0.3)], M_INK)
    f.oval(0, -0.2, 0.12, 0.17, M_INK)


def expr_scared(f):
    f.wide_eyes(w=0.18, h=0.24, pupil=0.045, look=-0.03)
    f.line([(-0.3, 0.27), (-0.1, 0.34)], M_INK)
    f.line([(0.1, 0.34), (0.3, 0.27)], M_INK)
    f.line([(-0.18, -0.18), (-0.09, -0.14), (0, -0.18), (0.09, -0.14), (0.18, -0.18)], M_INK, r=0.024)
    f.oval(0.42, 0.25, 0.09, 0.15, M_TEAR, lift=0.004)


def expr_suspicious(f):
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.06, 0.13, 0.13, M_INK)
        f.line([(sx - 0.1, 0.13), (sx + 0.1, 0.13)], M_INK, r=0.03)
    f.line([(-0.3, 0.22), (-0.1, 0.2)], M_INK)
    f.line([(0.1, 0.28), (0.3, 0.33)], M_INK)
    f.line([(0.0, -0.18), (0.2, -0.15)], M_INK)


def expr_determined(f):
    f.eyes(h=0.22, z=0.08)
    f.line([(-0.3, 0.3), (-0.08, 0.22)], M_INK, r=0.034)
    f.line([(0.08, 0.22), (0.3, 0.3)], M_INK, r=0.034)
    f.line([(-0.15, -0.2), (0, -0.18), (0.15, -0.2)], M_INK)


def expr_sad(f):
    f.eyes(w=0.12, h=0.2, z=0.07)
    f.line([(-0.3, 0.24), (-0.1, 0.3)], M_INK)
    f.line([(0.1, 0.3), (0.3, 0.24)], M_INK)
    f.oval(0.23, -0.08, 0.07, 0.13, M_TEAR, lift=0.006)
    f.line([(-0.15, -0.24), (0, -0.17), (0.15, -0.24)], M_INK)


def expr_faceless(f):
    pass  # what the Hollow leaves behind


def expr_rae(f):
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.08, 0.13, 0.2, M_INK)
        f.oval(sx + 0.03, 0.13, 0.05, 0.06, M_SHINE, lift=0.008)
        f.line([(sx + (0.06 if sx > 0 else -0.06), 0.16), (sx + (0.12 if sx > 0 else -0.12), 0.21)], M_INK, r=0.02)
    f.line([(-0.3, 0.27), (-0.1, 0.27)], M_INK)
    f.line([(0.1, 0.29), (0.3, 0.33)], M_INK)   # one raised: sceptical
    f.line([(-0.12, -0.18), (0.12, -0.16)], M_INK)


def expr_mayor(f):
    f.eyes(w=0.12, h=0.18, z=0.12)
    f.line([(-0.3, 0.29), (-0.1, 0.31)], M_INK)
    f.line([(0.1, 0.31), (0.3, 0.29)], M_INK)
    f.oval(0, -0.16, 0.5, 0.15, M_EYEWHITE)
    f.line([(-0.26, -0.12), (-0.12, -0.2), (0.12, -0.2), (0.26, -0.12)], M_INK, r=0.022)
    f.line([(-0.24, -0.16), (0.24, -0.16)], M_INK, r=0.012, lift=0.006)


def expr_grumpy(f):
    f.eyes(w=0.12, h=0.18, z=0.08, shine=False)
    f.line([(-0.3, 0.22), (-0.1, 0.2)], M_INK, r=0.035)
    f.line([(0.1, 0.2), (0.3, 0.22)], M_INK, r=0.035)
    f.line([(-0.14, -0.21), (0, -0.17), (0.14, -0.21)], M_INK)


EXPRESSIONS = {
    "friendly": expr_friendly, "laugh": expr_laugh, "shocked": expr_shocked, "scared": expr_scared,
    "suspicious": expr_suspicious, "determined": expr_determined, "sad": expr_sad, "faceless": expr_faceless,
}


def set_face(parts, name, t):
    """Switch a character's expression at time t (seconds)."""
    for ename, objs in parts["faces"].items():
        for ob in objs:
            key(ob, "hide_render", t, ename != name)
            key(ob, "hide_viewport", t, ename != name)


# ---- body ---------------------------------------------------------------------
def character(name, pos, target, st):
    root = empty(name, pos, col=COL_CHARS)
    root.rotation_euler = (0, 0, facing_yaw(pos, target))

    def M(k, rgb, **kw):
        return mat("%s_%s" % (name, k), rgb, **kw)

    skin = M("Skin", st["skin"], rough=0.45)
    top = M("Shirt", st["top"], rough=0.6)
    pants = M("Pants", st["pants"], rough=0.65)
    V = Vector
    P = {"root": root, "M": M, "skin": skin, "top": top}

    for sx in (-0.5, 0.5):
        rpart("Leg", (1, 1, 2), V((sx, 0, 1)), pants, root)
        if st.get("shoe"):   # shoes are printed on the pants, like on Roblox
            rpart("ShoePrint", (1.012, 1.012, 0.34), V((sx, 0, 0.21)), M("Shoe", st["shoe"], rough=0.5), root, r=0.03)
            rpart("SolePrint", (1.02, 1.02, 0.09), V((sx, 0, 0.045)), M("Sole", st["sole"], rough=0.5), root, r=0.02)
    rpart("Torso", (2, 1, 2), V((0, 0, 3)), top, root)

    for side, sx in (("Left", -1.5), ("Right", 1.5)):
        sh = empty(side + "Shoulder", V((sx, 0, 3.5)), col=COL_CHARS, parent=root)
        sh.empty_display_size = 0.4
        rpart(side + "Arm", (1, 1, 2), V((0, 0, -0.5)), skin if st.get("bare_arms") else top, sh)
        rpart(side + "HandPrint", (1.012, 1.012, 0.32), V((0, 0, -1.34)), skin, sh, r=0.03)
        if st.get("cuff"):
            rpart(side + "CuffPrint", (1.014, 1.014, 0.12), V((0, 0, -1.12)), M("Cuff", st["cuff"]), sh, r=0.02)
        P[side] = sh

    neck = empty("Neck", V((0, 0, 4)), col=COL_CHARS, parent=root)
    neck.empty_display_size = 0.4
    P["neck"] = neck
    solid("Head", HEAD_MESH, (1, 1, 1), V((0, 0, 0.6)), skin, parent=neck, col=COL_CHARS)

    P["faces"] = {}
    for ename in st["faces"]:
        f = Face(neck, ename)
        fn = EXPRESSIONS[ename]
        fn(f, signature=st.get("signature", False)) if ename == "friendly" else fn(f)
        P["faces"][ename] = f.objs

    for fn in st.get("build", []):
        fn(neck, root, P)
    set_face(P, st["faces"][0], 0)
    return P


def flat(name, size, x, z, m, root, back=False):
    """A print on the torso front (or back)."""
    return rpart(name, (size[0], 0.01, size[1]), Vector((x, -0.506 if back else 0.506, z)), m, root, r=0.004)


# ---- MILO: the channel's main character ----------------------------------------
# Brand: mustard hoodie with a black KEYHOLE logo, messy brown hair with a
# two-strand cowlick, brass key necklace, white trainers with red soles,
# and his lopsided smirk.
MILO_STYLE = dict(
    skin=(234, 184, 146), top=(226, 156, 32), pants=(34, 44, 82), cuff=(186, 120, 20),
    shoe=(248, 248, 248), sole=(214, 52, 52), signature=True,
    faces=["friendly", "laugh", "shocked", "scared", "suspicious", "determined", "sad", "faceless"],
)


def milo_build(neck, root, P):
    V = Vector
    M = P["M"]
    hair = M("Hair", (70, 44, 30), rough=0.55)
    dark = M("ShirtDark", (186, 120, 20), rough=0.6)
    white = mat("PrintWhite", (250, 250, 250))
    # Hair accessory
    ball("HairCap", (1.36, 1.36, 0.62), V((0, -0.03, 1.18)), hair, neck)
    for i, x in enumerate((-0.42, -0.14, 0.14, 0.42)):
        ball("Fringe", (0.36, 0.3, 0.32), V((x, 0.46 - abs(x) * 0.25, 1.1 - (0.0, 0.06, 0.02, 0.07)[i])), hair, neck,
             rot=(math.radians(-25), 0, math.radians(x * 30)))
    for sx in (-0.6, 0.6):
        ball("SideHair", (0.22, 0.9, 0.45), V((sx, -0.08, 0.98)), hair, neck)
    ball("BackHair", (1.2, 0.36, 0.7), V((0, -0.5, 0.9)), hair, neck)
    rpart("Cowlick", (0.2, 0.2, 0.62), V((0.08, -0.25, 1.62)), hair, neck, r=0.09,
          rot=(math.radians(-22), math.radians(24), 0))
    rpart("Cowlick2", (0.17, 0.17, 0.45), V((0.3, -0.15, 1.52)), hair, neck, r=0.08,
          rot=(math.radians(-12), math.radians(48), 0))
    # Shirt prints
    flat("Pocket", (1.2, 0.42), 0, 2.32, dark, root)
    flat("PocketTop", (1.2, 0.05), 0, 2.53, mat("PocketLine", (160, 100, 15)), root)
    flat("CollarV", (0.9, 0.12), 0, 3.92, dark, root)
    for sx in (-0.3, 0.3):
        flat("Drawstring", (0.06, 0.42), sx, 3.66, white, root)
    flat("HoodPrint", (1.5, 0.55), 0, 3.6, dark, root, back=True)
    disc("LogoCircle", 0.36, 0.012, V((0, 0.508, 3.02)), M_INK, root)
    flat("LogoStem", (0.18, 0.32), 0, 2.8, M_INK, root)
    # Key necklace accessory
    cord = mat("Cord", (30, 30, 30))
    tube("KeyCord", [(-0.42, 0.42, 4.02), (-0.2, 0.53, 3.8), (0, 0.555, 3.72), (0.2, 0.53, 3.8), (0.42, 0.42, 4.02)],
         0.022, cord, root)
    disc("KeyBow", 0.24, 0.05, V((0, 0.57, 3.62)), M_BRASS, root)
    disc("KeyHole", 0.09, 0.06, V((0, 0.575, 3.62)), M_INK, root)
    rpart("KeyShaft", (0.065, 0.045, 0.32), V((0, 0.57, 3.36)), M_BRASS, root, r=0.015)
    for z in (3.25, 3.33):
        rpart("KeyTooth", (0.12, 0.045, 0.055), V((0.065, 0.57, z)), M_BRASS, root, r=0.012)


MILO_STYLE["build"] = [milo_build]

RAE_STYLE = dict(skin=(160, 105, 78), top=(122, 84, 170), pants=(30, 30, 40), cuff=(92, 60, 135),
                 shoe=(205, 170, 240), sole=(70, 45, 100), faces=["rae", "shocked", "scared", "sad"])


def rae_build(neck, root, P):
    V = Vector
    M = P["M"]
    hair = M("Hair", (28, 20, 20), rough=0.55)
    pink = M("Headphones", (236, 84, 150), rough=0.35)
    ball("HairCap", (1.36, 1.36, 0.6), V((0, -0.03, 1.18)), hair, neck)
    rpart("Bangs", (1.1, 0.25, 0.3), V((0, 0.45, 1.02)), hair, neck, r=0.12, rot=(math.radians(-12), 0, 0))
    rpart("LongHair", (1.3, 0.4, 1.6), V((0, -0.52, 0.45)), hair, neck, r=0.18)
    for sx in (-0.62, 0.62):
        rpart("SideHair", (0.18, 0.8, 1.2), V((sx, -0.12, 0.55)), hair, neck, r=0.08)
        disc("HeadphoneCup", 0.55, 0.22, V((sx * 1.15, 0, 0.75)), pink, neck, axis="X")
    tube("HeadphoneBand", [(-0.78, 0, 0.9), (-0.65, 0, 1.4), (0, 0, 1.58), (0.65, 0, 1.4), (0.78, 0, 0.9)],
         0.06, pink, neck)
    flat("Pocket", (1.2, 0.42), 0, 2.32, M("ShirtDark", (92, 60, 135)), root)
    flat("HoodPrint", (1.5, 0.55), 0, 3.6, M("ShirtDark", (92, 60, 135)), root, back=True)
    rpart("Notebook", (0.62, 0.16, 0.82), V((0, 0.6, -1.6)), M("Notebook", (170, 40, 45), rough=0.7), P["Left"],
          r=0.04)


RAE_STYLE["build"] = [rae_build]

MAYOR_STYLE = dict(skin=(234, 184, 146), top=(28, 28, 34), pants=(28, 28, 34), shoe=(15, 15, 15), sole=(5, 5, 5),
                   faces=["mayor", "suspicious"])


def mayor_build(neck, root, P):
    V = Vector
    M = P["M"]
    hat = M("Hat", (18, 18, 22), rough=0.35)
    solid("HatBrim", CYL, (1.75, 1.75, 0.12), V((0, 0, 1.25)), hat, parent=neck, col=COL_CHARS)
    solid("HatTop", CYL, (1.15, 1.15, 1.3), V((0, 0, 1.95)), hat, parent=neck, col=COL_CHARS)
    solid("HatBand", CYL, (1.18, 1.18, 0.2), V((0, 0, 1.41)), M("HatBand", (160, 25, 40)), parent=neck,
          col=COL_CHARS)
    stache = M("Moustache", (150, 150, 155), rough=0.6)
    tube("Moustache", [(-0.3, surf_y(0.3) + 0.03, 0.5), (-0.12, surf_y(0.12) + 0.05, 0.53),
                       (0, surf_y(0) + 0.05, 0.52), (0.12, surf_y(0.12) + 0.05, 0.53),
                       (0.3, surf_y(0.3) + 0.03, 0.5)], 0.06, stache, neck)
    flat("ShirtV", (0.6, 0.95), 0, 3.52, mat("PrintWhite", (250, 250, 250)), root)
    flat("Tie", (0.2, 0.85), 0, 3.45, M("Tie", (170, 30, 40)), root)
    for z in (2.6, 2.95):
        disc("Button", 0.12, 0.02, V((0.35, 0.51, z)), M_BRASS, root)


MAYOR_STYLE["build"] = [mayor_build]

NEIGHBOUR_STYLE = dict(skin=(124, 92, 70), top=(180, 44, 44), pants=(52, 74, 124), cuff=(120, 25, 25),
                       shoe=(110, 80, 55), sole=(50, 35, 25), faces=["grumpy", "shocked"])


def neighbour_build(neck, root, P):
    V = Vector
    M = P["M"]
    dark = M("Plaid", (110, 22, 22), rough=0.7)
    for z in (2.5, 3.3):
        rpart("PlaidBand", (2.012, 1.012, 0.16), V((0, 0, z)), dark, root, r=0.02)
    for x in (-0.5, 0.5):
        rpart("PlaidStripe", (0.12, 1.012, 2.0), V((x, 0, 3)), dark, root, r=0.02)
    cap = M("Cap", (40, 80, 150), rough=0.55)
    ball("Cap", (1.3, 1.3, 0.7), V((0, 0, 1.1)), cap, neck)
    rpart("CapBrim", (0.9, 0.6, 0.08), V((0, 0.75, 1.02)), cap, neck, r=0.03)
    hammer = empty("Hammer", V((0, 0.3, -1.5)), col=COL_CHARS, parent=P["Right"])
    rpart("HammerHandle", (0.22, 1.6, 0.22), V((0, 0.7, 0)), M_WOOD, hammer, r=0.05)
    rpart("HammerHead", (0.4, 0.4, 0.9), V((0, 1.5, 0)), M_METAL, hammer, r=0.05)


NEIGHBOUR_STYLE["build"] = [neighbour_build]
EXPRESSIONS.update({"rae": expr_rae, "mayor": expr_mayor, "grumpy": expr_grumpy})

# Milo starts at the fence
MILO_FENCE = R(21, 0, 27)
MILO_DOOR = R(0, 0.4, 34.5)
milo = character("Milo", MILO_FENCE, R(28, 0, 27), MILO_STYLE)
rae = character("Rae", R(28, 0, 27), R(21, 0, 27), RAE_STYLE)
mayor = character("Mayor", R(217, 0, 0), R(200, 0, 0), MAYOR_STYLE)
neighbour = character("Neighbour", R(-57, 0, -26), R(-57, 0, -30), NEIGHBOUR_STYLE)


# ---------------------------------------------------------------- TREES + HILLS
M_LEAF = tex_mat("Leaves", (66, 132, 52), "grass", rough=0.9)
M_BARK = tex_mat("Bark", (105, 76, 52), "plaster", rough=0.9)


def tree(x, z, s=1.0):
    root = empty("Tree", R(x, 0, z))
    cyl("Trunk", (1.4 * s, 1.4 * s, 9 * s), R(0, 4.5 * s, 0), M_BARK, parent=root)
    for ox, oy, oz, r in ((0, 11, 0, 7), (2.6, 9, 1.5, 5), (-2.3, 9.5, -1.5, 5), (0.6, 14, -0.6, 4.6)):
        solid("Leaves", SPHERE, (r * s, r * s, r * s * 0.9), R(ox * s, oy * s, oz * s), M_LEAF, parent=root)


random.seed(11)
for zz in (-64, 64):
    for x in range(-250, 251, 38):
        tree(x + random.uniform(-8, 8), zz + random.uniform(-6, 6), random.uniform(0.9, 1.25))
for x in (-125, -75, 75, 125):
    for zz in (-25, 25):
        tree(x, zz, 0.55)
M_HILL = tex_mat("Hills", (78, 140, 70), "grass", rough=1)
for i in range(10):
    a = 2 * math.pi * i / 10
    solid("Hill", SPHERE, (300, 300, 90), Vector((470 * math.cos(a), 330 * math.sin(a), -20)), M_HILL)
random.seed(7)


# ---------------------------------------------------------------- LIGHTING + WORLD
world = bpy.data.worlds.new("BloxburyWorld")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
_wn, _wl = world.node_tree.nodes, world.node_tree.links
_wn.clear()
_wout = _wn.new("ShaderNodeOutputWorld")
_tc = _wn.new("ShaderNodeTexCoord")
_sep = _wn.new("ShaderNodeSeparateXYZ")
_wl.new(_tc.outputs["Generated"], _sep.inputs[0])
# sky gradient: pale horizon -> blue overhead
_ramp = _wn.new("ShaderNodeValToRGB")
_wl.new(_sep.outputs["Z"], _ramp.inputs["Fac"])
_ramp.color_ramp.elements[0].position = 0.0
_ramp.color_ramp.elements[0].color = (*lin((226, 236, 247)), 1)
_ramp.color_ramp.elements[1].position = 0.55
_ramp.color_ramp.elements[1].color = (*lin((92, 148, 226)), 1)
_sky = _wn.new("ShaderNodeBackground")
_wl.new(_ramp.outputs["Color"], _sky.inputs["Color"])
# soft clouds projected on a dome
_add = _wn.new("ShaderNodeMath")
_add.operation = "ADD"
_add.inputs[1].default_value = 0.12
_wl.new(_sep.outputs["Z"], _add.inputs[0])
_comb = _wn.new("ShaderNodeCombineXYZ")
for _k in "XYZ":
    _wl.new(_add.outputs[0], _comb.inputs[_k])
_div = _wn.new("ShaderNodeVectorMath")
_div.operation = "DIVIDE"
_wl.new(_tc.outputs["Generated"], _div.inputs[0])
_wl.new(_comb.outputs[0], _div.inputs[1])
_cn = _wn.new("ShaderNodeTexNoise")
_cn.inputs["Scale"].default_value = 1.1
_cn.inputs["Detail"].default_value = 5
_wl.new(_div.outputs["Vector"], _cn.inputs["Vector"])
_cr = _wn.new("ShaderNodeValToRGB")
_cr.color_ramp.elements[0].position = 0.52
_cr.color_ramp.elements[1].position = 0.7
_wl.new(_cn.outputs["Fac"], _cr.inputs["Fac"])
_mask = _wn.new("ShaderNodeMath")
_mask.operation = "GREATER_THAN"
_mask.inputs[1].default_value = 0.03
_wl.new(_sep.outputs["Z"], _mask.inputs[0])
_cm = _wn.new("ShaderNodeMath")
_cm.operation = "MULTIPLY"
_wl.new(_cr.outputs["Color"], _cm.inputs[0])
_wl.new(_mask.outputs[0], _cm.inputs[1])
_cloud = _wn.new("ShaderNodeBackground")
_cloud.inputs["Color"].default_value = (1, 1, 1, 1)
_cloud.inputs["Strength"].default_value = 1.15
_day = _wn.new("ShaderNodeMixShader")
_wl.new(_cm.outputs[0], _day.inputs[0])
_wl.new(_sky.outputs[0], _day.inputs[1])
_wl.new(_cloud.outputs[0], _day.inputs[2])
_nightbg = _wn.new("ShaderNodeBackground")
_nightbg.inputs["Color"].default_value = (*lin((34, 42, 82)), 1)
_dn = _wn.new("ShaderNodeMixShader")
_wl.new(_day.outputs[0], _dn.inputs[1])
_wl.new(_nightbg.outputs[0], _dn.inputs[2])
_wl.new(_dn.outputs[0], _wout.inputs["Surface"])
NIGHT_MIX = _dn.inputs[0]
# distance haze: a big volume box around the town (a world volume would block the sun)
M_HAZE = bpy.data.materials.new("Haze")
try:
    M_HAZE.use_nodes = True
except Exception:
    pass
_hn = M_HAZE.node_tree
_hn.nodes.clear()
_hout = _hn.nodes.new("ShaderNodeOutputMaterial")
_vol = _hn.nodes.new("ShaderNodeVolumeScatter")
_vol.inputs["Color"].default_value = (*lin((215, 228, 245)), 1)
_hn.links.new(_vol.outputs[0], _hout.inputs["Volume"])
HAZE = _vol.inputs["Density"]
_haze_box = box("HazeVolume", (1400, 1400, 260), Vector((0, 0, 100)), M_HAZE)
_haze_box.hide_select = True

sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.angle = math.radians(7)
SUN = bpy.data.objects.new("Sun", sun_data)
link(SUN, COL_LIGHTS)
SUN.rotation_mode = "QUATERNION"
SUN.rotation_quaternion = Vector((0.45, 0.55, -0.7)).to_track_quat("-Z", "Y")

ml = bpy.data.lights.new("MiloLight", "POINT")
ml.color = lin((255, 225, 190))
ml.shadow_soft_size = 1.5
MILO_LIGHT_OB = bpy.data.objects.new("MiloLight", ml)
link(MILO_LIGHT_OB, COL_LIGHTS)
MILO_LIGHT_OB.location = R(0, 11.5, 40)
MILO_LIGHT = ml


def set_day(t):
    key(sun_data, "energy", t, 4.0)
    key(sun_data, "color", t, lin((255, 236, 208)))
    key(NIGHT_MIX, "default_value", t, 0.0)
    key(HAZE, "default_value", t, 0.0012)
    key(MILO_LIGHT, "energy", t, 1500)


def set_night(t):
    key(sun_data, "energy", t, 0.6)
    key(sun_data, "color", t, lin((140, 160, 255)))
    key(NIGHT_MIX, "default_value", t, 1.0)
    key(HAZE, "default_value", t, 0.003)
    key(MILO_LIGHT, "energy", t, 450)


def house_lights(t, on):
    key(_wb.inputs["Emission Strength"], "default_value", t, 5.0 if on else 0.0)
    for d in HOUSE_LIGHTS:
        key(d, "energy", t, 900 if on else 0)


def lamp_flicker(lamp, t0):
    head, m, ld = lamp
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    strength = bsdf.inputs["Emission Strength"]
    f0 = F(t0)
    pattern = [(0, False), (3, True), (5, False), (8, True), (10, False), (12, True), (15, False)]
    for off, on in pattern:
        t = Frame(f0 + off)
        key(strength, "default_value", t, 12.0 if on else 0.0)
        key(ld, "energy", t, 20000 if on else 0)
    key(bsdf.inputs["Base Color"], "default_value", t, (*lin((60, 60, 60)), 1))


# ---------------------------------------------------------------- CAMERA
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 22
cam_data.clip_start = 0.05
cam_data.clip_end = 3000
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 0.9   # lower = blurrier background
CAM = bpy.data.objects.new("Camera", cam_data)
link(CAM, COL_CAM)
CAM.rotation_mode = "QUATERNION"
scene.camera = CAM
_last_q = [None]


def look(pos, target):
    return (target - pos).to_track_quat("-Z", "Y")


def cam_key(t, pos, q, interp, focus=None, lens=None):
    if _last_q[0] is not None and _last_q[0].dot(q) < 0:
        q = Quaternion((-q.w, -q.x, -q.y, -q.z))
    _last_q[0] = q.copy()
    key(CAM, "location", t, pos.copy(), interp)
    key(CAM, "rotation_quaternion", t, q, interp)
    if focus is not None:
        key(cam_data.dof, "focus_distance", t, focus, interp)
    if lens is not None:
        key(cam_data, "lens", t, lens, interp)


def shot(t, pos, target, lens=22):
    """Hard cut to a static shot, focused on the target. lens 35-50 = close-up."""
    cam_key(t, pos, look(pos, target), "CONSTANT", (target - pos).length, lens)
    return pos, target


def move(t0, t1, p0, tg0, p1, tg1, interp="BEZIER", lens=22):
    cam_key(t0, p0, look(p0, tg0), interp, (tg0 - p0).length, lens)
    # end one frame early so a cut that starts exactly at t1 can't overwrite this key
    cam_key(Frame(F(t1) - 1), p1, look(p1, tg1), "CONSTANT", (tg1 - p1).length, lens)
    return p1, tg1


def push_in(t0, t1, pos, target, studs, lens=22):
    d = (target - pos).normalized() * studs
    return move(t0, t1, pos, target, pos + d, target, lens=lens)


def shake(t0, dur, pos, target, strength_deg):
    """Small jolt on the ONE big hit: smooth decaying wobble keyed every frame (23 Nov: the old random jitter every
    2 frames with LINEAR keys read as a stutter)."""
    base = look(pos, target)
    frames = max(2, int(dur * FPS)); ph = random.uniform(0, 6.28)
    for i in range(frames + 1):
        u = i / frames; env = math.sin(math.pi * min(1.0, u / 0.15)) if u < 0.15 else (1 - u) ** 2
        a = math.radians(strength_deg) * env
        t = i / FPS
        q = Quaternion((1, a * math.sin(31 * t + ph), a * math.sin(23 * t + 2 * ph), a * 0.5 * math.sin(17 * t + 1))).normalized()
        cam_key(t0 + t, pos, base @ q, "BEZIER", (target - pos).length)
    cam_key(t0 + dur + 1.0 / FPS, pos, base, "CONSTANT", (target - pos).length)


# Captions + black frame ride on the camera
M_CAP = mat("CaptionWhite", (255, 255, 255), emit=1.5)
M_CAP_RED = mat("CaptionRed", (255, 70, 70), emit=1.5)
M_CAP_YELLOW = mat("CaptionYellow", (255, 214, 60), emit=1.5)
M_CAP_OUTLINE = mat("CaptionOutline", (0, 0, 0))

CAP_DIST = 0.5
CAP_Y = -0.075


def caption(body, t0, dur, red=False):
    """One word at a time, big and centred. Words written in CAPS in the line turn yellow."""
    if not SHOW_CAPTIONS:
        return
    words = body.split()
    weights = [len(w) + 3 for w in words]
    t = t0
    for w, wt in zip(words, weights):
        d = dur * wt / sum(weights)
        shout = w.isupper() and any(c.isalpha() for c in w)
        m = M_CAP_RED if red else (M_CAP_YELLOW if shout else M_CAP)
        front = text("Word: " + w, w.upper(), 0.075, m, offset=0.0015, col=COL_CAM)
        back = text("Outline: " + w, w.upper(), 0.075, M_CAP_OUTLINE, offset=0.0065, col=COL_CAM)
        for ob, z in ((front, -CAP_DIST), (back, -CAP_DIST - 0.0005)):
            ob.parent = CAM
            ob.location = (0, CAP_Y, z)
            visible(ob, [(t, t + d)])
        t += d


M_FADE = bpy.data.materials.new("FadeBlack")
try:
    M_FADE.use_nodes = True
except Exception:
    pass
_nt = M_FADE.node_tree
_nt.nodes.clear()
_out = _nt.nodes.new("ShaderNodeOutputMaterial")
_mix = _nt.nodes.new("ShaderNodeMixShader")
_tr = _nt.nodes.new("ShaderNodeBsdfTransparent")
_em = _nt.nodes.new("ShaderNodeEmission")
_em.inputs["Color"].default_value = (0, 0, 0, 1)
_nt.links.new(_tr.outputs[0], _mix.inputs[1])
_nt.links.new(_em.outputs[0], _mix.inputs[2])
_nt.links.new(_mix.outputs[0], _out.inputs[0])
set_blended(M_FADE)
FADE = _mix.inputs[0]  # 1 = black
blackout = box("Blackout", (2.5, 2.5, 0.001), Vector((0, 0, -0.6)), M_FADE, parent=CAM, col=COL_CAM)


def fade(t, amount, interp="CONSTANT"):
    key(FADE, "default_value", t, amount, interp)


# ---------------------------------------------------------------- ANIMATION HELPERS
def rot(ob, t, x=0, y=0, z=0, interp="BEZIER"):
    key(ob, "rotation_euler", t, (math.radians(x), math.radians(y), math.radians(z)), interp)


def place(parts, t, pos, target):
    root = parts["root"]
    key(root, "location", t, pos.copy())
    key(root, "rotation_euler", t, (0, 0, facing_yaw(pos, target)))


def talk(parts, t0, t1):
    """Little head bobs while a line is spoken."""
    n = parts["neck"]
    t = t0
    while t < t1:
        rot(n, t, x=random.uniform(-6, 4), z=random.uniform(-6, 6))
        t += 0.35
    rot(n, t1, 0, 0, 0)


def record_sound(name, t):
    scene.timeline_markers.new(name, frame=F(t))
    if SOUND_DIR:
        path = os.path.join(SOUND_DIR, name.lower() + ".wav")
        if os.path.exists(path):
            se = scene.sequence_editor or scene.sequence_editor_create()
            strips = getattr(se, "strips", None) or getattr(se, "sequences")
            ch = 1 + len([s for s in strips if s.frame_final_start <= F(t) < s.frame_final_end]) % 6
            strips.new_sound(name, path, ch, F(t))


# ================================================================ TIMELINE (seconds)
# Part 1 runs about 1:21, over the 1-minute minimum for TikTok's Creator Rewards.
# Milo's own windows get their own see-through glass so you can look out of them,
# and so his house can stay lit when every other light goes out.
M_WINDOW_MILO = bpy.data.materials.new("WindowMilo")
try:
    M_WINDOW_MILO.use_nodes = True
except Exception:
    pass
_mwb = M_WINDOW_MILO.node_tree.nodes.get("Principled BSDF")
_mwb.inputs["Base Color"].default_value = (*lin(C["glass"]), 1)
_mwb.inputs["Roughness"].default_value = 0.05
_mwb.inputs["Alpha"].default_value = 0.3
_mwb.inputs["Emission Color"].default_value = (*lin(C["warm"]), 1)
_mwb.inputs["Emission Strength"].default_value = 0.0
set_blended(M_WINDOW_MILO)
for w in WINDOW_PARTS:
    if w.parent and w.parent.name == "MiloHouse":
        w.material_slots[0].material = M_WINDOW_MILO
MILO_GLOW = _mwb.inputs["Emission Strength"]

# Defaults at frame 1
set_day(0)
house_lights(0, False)
fade(0, 1.0)
for p in PLANKS:
    visible(p, [(29.8 if p.name.endswith("1") else 31.0, None)])
visible(CLOCK_TEXTS["2:59 AM"], [(0, 48.65)])
visible(CLOCK_TEXTS["3:00 AM"], [(48.65, None)])
rot(CLOSET_HANDLE, 0, 0, 0, 0, "CONSTANT")
rot(CLOSET_HINGE, 0, 0, 0, 0, "CONSTANT")
key(MILO_GLOW, "default_value", 0, 0.0)
MILO_LAWN = R(-2, 0, 22)
MILO_WINDOW = R(-7.25, 0.4, 33.5)
place(milo, 0, MILO_LAWN, R(-2, 0, 40))
rot(milo["neck"], 0, 0, 0, 0, "CONSTANT")
for _side in ("Left", "Right"):                       # arms down until something animates them
    for _ch in (milo, rae, mayor, neighbour):
        rot(_ch[_side], 0, 0, 0, 0, "CONSTANT")

# ---- 0.0–1.8  HOOK: black screen, three knocks
caption("NEVER open the door after 3AM.", 0.0, 1.8, red=True)
for t in (0.0, 0.4, 0.8):
    record_sound("KNOCK", t)

# ---- 1.8–4.8  Van passes the welcome sign
shot(0, R(-185, 5, 14), R(-205, 5, -14))
fade(1.8, 1.0, "LINEAR")
fade(2.05, 0.0)
caption("We moved to Bloxbury on a Tuesday.", 1.8, 3.0)

VAN_START, VAN_END, VAN_T0, VAN_DUR = R(-275, 0, -6), R(-15, 0, -6), 1.8, 7.5


def van_pos(t):
    a = min(max((t - VAN_T0) / VAN_DUR, 0), 1)
    return VAN_START.lerp(VAN_END, math.sin(a * math.pi / 2))  # ease out


t = 0.0
while t <= VAN_T0 + VAN_DUR + 0.01:
    key(VAN, "location", t, van_pos(t), "LINEAR")
    t += 1 / 6

# ---- 4.8–9.05  Camera chases the van
caption("By Wednesday, I knew something was wrong.", 4.8, 4.0)
follow_times = [4.8 + i / 6 for i in range(int((9.05 - 4.8) * 6))]
for i, t in enumerate(follow_times):
    body = van_pos(t) + Vector((0, 0, 4.5))
    cp_ = body + Vector((-14, -20, 7))
    cam_key(t, cp_, look(cp_, body + Vector((0, 0, 2))), "CONSTANT" if i == len(follow_times) - 1 else "LINEAR",
            (body - cp_).length, 22)

# ---- 9.05–15.5  NEW: Milo outside his new house. (Clue: Mum is never seen.)
push_in(9.05, 12.0, R(-5, 2.0, 14), R(0, 9, 31), 1.0, lens=24)        # low angle up at the house
caption("Mum said she'd be home late.", 9.2, 2.7)
push_in(12.0, 15.5, R(-1.4, 5.0, 25.0), R(-2, 4.6, 22), 0.4, lens=40)  # his face
caption("She ALWAYS was.", 12.1, 1.7)
caption("I never actually saw her.", 13.9, 1.6)
set_face(milo, "sad", 13.3)

# ---- 15.5–29.0  Rae at the fence: fast close-up cuts
place(milo, 15.5, MILO_FENCE, R(28, 0, 27))
set_face(milo, "friendly", 15.5)
fp, ft = R(16, 7, 21), R(27, 4.5, 28)
RAE_HEAD, MILO_HEAD = R(28, 4.6, 27), R(21, 4.6, 27)
RAE_CAM, MILO_CAM = R(24.2, 5.0, 25.6), R(24.4, 4.9, 28.6)
push_in(15.5, 18.5, RAE_CAM, RAE_HEAD, 0.6, lens=40)                   # Rae close-up
push_in(18.5, 21.0, MILO_CAM, MILO_HEAD, 0.4, lens=40)                 # Milo listening
ecu_p = R(25.2, 4.8, 26.3)
shot(21.0, ecu_p, RAE_HEAD, lens=45)                                   # extreme close-up: "EVER"
shake(21.0, 0.4, ecu_p, RAE_HEAD, 0.8)
shot(23.5, fp, ft, lens=24)                                            # wide: Milo laughs
push_in(25.5, 27.6, RAE_CAM, RAE_HEAD, 0.5, lens=40)                   # NEW: Rae's list
shot(27.6, MILO_CAM, MILO_HEAD, lens=40)                               # NEW: "Who's left?"
caption("New kid?", 15.5, 1.5)
caption("One rule.", 17.0, 1.5)
caption("Three knocks after 3AM...", 18.5, 2.5)
caption("...you don't answer. EVER.", 21.0, 2.5, red=True)
caption("She wasn't joking.", 23.5, 2.0)
caption("I keep a list. Of who's LEFT.", 25.6, 2.0)
caption("...Who's left?", 27.65, 1.35)
set_face(milo, "suspicious", 18.5)
set_face(milo, "laugh", 23.5)
set_face(milo, "friendly", 24.85)
set_face(milo, "suspicious", 27.6)
talk(rae, 15.5, 23.3)
talk(rae, 25.5, 27.5)
RAE_YAW = facing_yaw(R(28, 0, 27), R(21, 0, 27)) * 180 / math.pi
rot(rae["Right"], 18.35, 0, 0, 0)
rot(rae["Right"], 18.75, x=100)
rot(rae["Right"], 20.75, x=100)
rot(rae["Right"], 21.25, 0, 0, 0)
rot(rae["root"], 20.85, 0, 0, RAE_YAW)
rot(rae["root"], 21.15, x=-8, z=RAE_YAW)
rot(rae["root"], 22.95, x=-8, z=RAE_YAW)
rot(rae["root"], 23.45, 0, 0, RAE_YAW)
set_face(rae, "shocked", 15.45)
set_face(rae, "rae", 15.5)
for i, tt in enumerate((23.55, 23.75, 23.95, 24.15, 24.35)):
    rot(milo["neck"], tt, x=(12 if i % 2 == 0 else 2))
rot(milo["neck"], 24.65, 0, 0, 0)

# ---- 29.0–33.0  Neighbour boarding up windows
shot(29.0, R(-48, 7, -16), R(-56, 7.5, -29))
caption("Everyone boarded up their windows.", 29.0, 4.0)
record_sound("HAMMER", 29.8)
record_sound("HAMMER", 31.0)
rot(neighbour["Right"], 28.95, x=90)
t, up = 29.25, True
while t < 32.85:
    rot(neighbour["Right"], t, x=(150 if up else 80), interp="LINEAR")
    up = not up
    t += 0.2
rot(neighbour["Right"], 33.0, x=90)

# ---- 33.0–37.0  The Mayor's mansion with no door
push_in(33.0, 37.0, R(195, 6, 10), R(225, 9, 0), 10)
caption("The Mayor's house had no door.", 33.0, 4.0)
t = 33.0
while t < 36.85:
    rot(mayor["Right"], t, y=-150, interp="BEZIER")
    rot(mayor["Right"], t + 0.25, y=-170, interp="BEZIER")
    t += 0.5
rot(mayor["Right"], 36.95, 0, 0, 0)

# ---- 37.0–45.0  NEW: Night. Every light goes out... except Milo's.
fade(36.65, 0.0, "LINEAR")
fade(37.0, 1.0, "LINEAR")
fade(37.35, 0.0)
set_night(37.0)
house_lights(37.0, True)
for _ob in [o for o in bpy.data.objects if o.name.startswith("Hollow_")]:
    visible(_ob, [(37.0, 78.8)])     # fog walls vanish again for the daytime outro
record_sound("DRONE", 37.0)
place(milo, 37.0, MILO_WINDOW, R(-7.25, 0.4, 30))
push_in(37.0, 40.5, R(-5.8, 7.2, 37.5), R(-7.25, 7.5, 30.5), 0.8, lens=24)   # behind Milo at his window
caption("At 2:57, every light in Bloxbury...", 37.35, 3.1)
shot(40.5, R(-7.25, 8.8, 31.6), R(-30, 5, -45), lens=22)                     # looking out of his window
house_lights(41.2, False)
record_sound("LIGHTOFF", 41.2)
caption("...went OFF.", 40.9, 1.9)
shot(43.0, R(-24, 6, 6), R(-2, 8, 31), lens=24)                              # outside: his house glowing
key(MILO_GLOW, "default_value", 43.0, 2.5)
key(MILO_GLOW, "default_value", 45.0, 0.0)
caption("Except mine.", 43.15, 1.8, red=True)

# ---- 45.0–48.65  The clock reads 2:59
record_sound("TICK", 45.3)
cp, ct = push_in(45.0, 48.5, R(3, 8, 36), R(-10.9, 8.5, 40), 3)

# ---- 48.65–50.15  3:00 AM
shake(48.65, 0.5, cp, ct, 1.0)
caption("3:00 AM", 48.65, 1.5, red=True)

# ---- 50.15–55.95  Street lamps die, furthest first
shot(50.15, R(10, 20, 10), R(-200, 8, -4))
door_pos = R(0, 4.5, 30.5)
order = sorted(LAMPS, key=lambda L: -(L[0].location - door_pos).length)
for i, lamp in enumerate(order):
    lamp_flicker(lamp, 50.15 + i * 0.17)
    record_sound("LIGHTOFF", 50.15 + i * 0.17 + 15 / FPS)

# ---- 55.95–58.55  At the front door: KNOCK KNOCK KNOCK
place(milo, 55.95, MILO_DOOR, R(0, 0.4, 30.5))
set_face(milo, "scared", 55.95)
key(MILO_LIGHT, "energy", 55.95, 220)
dp, dt = R(3.5, 6.5, 40), R(0, 4.5, 30.5)
shot(55.95, dp, dt)
for i, tt in enumerate((55.95, 56.65, 57.35)):
    record_sound("KNOCK", tt)
    caption("KNOCK.", tt, 1.2 if i == 2 else 0.7)
    rot(milo["root"], tt, 0, 0, 0, "LINEAR")
    rot(milo["root"], tt + 0.08, x=5, interp="BEZIER")
    rot(milo["root"], tt + 0.4, 0, 0, 0)

# ---- 58.55–61.55  NEW: he checks the window. Nobody there.
shot(58.55, R(-7.0, 9, 32.2), R(-3, 3, 22), lens=24)
caption("Nobody was there.", 58.7, 2.7)

# ---- 61.55–66.55  His face. Silence.
FACE_P, FACE_T = R(0.7, 5.0, 31.4), R(0, 5.0, 34.5)
dp2, dt2 = push_in(61.55, 66.55, FACE_P, FACE_T, 0.8, lens=40)
caption("Then it went quiet.", 61.7, 2.0)
caption("...", 63.9, 2.4)
record_sound("DRONE_STOP", 63.9)

# ---- 66.55–72.05  The knocks come from INSIDE the closet
glow = bpy.data.lights.new("ClosetGlow", "POINT")
glow.color = lin((120, 160, 255))
glow_ob = bpy.data.objects.new("ClosetGlow", glow)
link(glow_ob, COL_LIGHTS)
glow_ob.location = R(7, 0.8, 44.8)
key(glow, "energy", 0, 0)
key(glow, "energy", 66.55, 400)
for tt in (66.55, 67.05, 67.55):
    record_sound("KNOCK", tt)
cl_p, cl_t = R(-3, 6, 35), R(7, 5, 46)
move(66.55, 66.75, dp2, dt2, cl_p, cl_t, "BEZIER")                 # whip pan to the closet
rot(milo["neck"], 66.55, 0, 0, 0)
rot(milo["neck"], 66.8, z=-70)
SHOCK_P = R(2.82, 5.0, 33.48)
shot(67.05, SHOCK_P, R(0, 5.0, 34.5), lens=40)                     # his shocked face
shake(67.05, 0.4, SHOCK_P, R(0, 5.0, 34.5), 0.8)
set_face(milo, "shocked", 67.05)
caption("It came from INSIDE my closet.", 66.85, 2.5, red=True)
move(68.05, 72.05, cl_p, cl_t, R(4.5, 5.5, 39.5), R(5.8, 4.5, 45.6), "BEZIER", lens=24)
record_sound("CREAK", 68.05)
rot(CLOSET_HANDLE, 68.05, 0, 0, 0)
rot(CLOSET_HANDLE, 71.05, y=70)
rot(CLOSET_HINGE, 71.05, 0, 0, 0)
rot(CLOSET_HINGE, 71.85, z=-12)

# ---- 72.05–76.7  NEW: a whisper from the crack
CRACK_P, CRACK_T = R(5.4, 5.6, 36.0), R(6.8, 4.4, 45.8)
_cp2, _ = push_in(72.05, 74.2, CRACK_P, CRACK_T, 1.0, lens=24)  # slow creep toward the glowing closet
caption("Then a voice whispered...", 72.15, 2.0)
key(glow, "energy", 74.15, 900)
record_sound("WHISPER", 74.2)
caption("\"Milo... let me OUT.\"", 74.2, 2.4, red=True)
shake(74.2, 0.5, _cp2, CRACK_T, 0.8)                            # jolt on "Milo..."
push_in(74.7, 76.65, _cp2, CRACK_T, 1.2, lens=24)                # keep creeping in

# ---- 76.7–78.8  HARD CUT TO BLACK: "It knew my name."
fade(76.7, 1.0)
record_sound("STING", 76.7)
caption("IT KNEW MY NAME.", 76.9, 2.0, red=True)

# ---- 78.8–85.5  OUTRO: daylight, Milo waves. "Follow and like for Part 2!"
# ...and on the last whisper, something faceless is standing in his window.
OUT_T = 78.8
fade(OUT_T, 0.0)
set_day(OUT_T)
key(glow, "energy", OUT_T, 0)
place(milo, OUT_T, MILO_LAWN, R(-2, 0, 0))            # facing the camera / street
rot(milo["neck"], OUT_T, 0, 0, 0, "CONSTANT")
set_face(milo, "friendly", OUT_T)
OUT_CAM, OUT_TGT = R(-4.0, 5.6, 10.5), R(-4.7, 7.0, 24)
push_in(OUT_T, 85.4, OUT_CAM, OUT_TGT, 2.0, lens=24)
rot(milo["Right"], OUT_T, 0, 0, 0)
t, up = OUT_T + 0.2, True                              # big friendly wave
while t < 82.6:
    rot(milo["Right"], t, y=(-150 if up else -172), interp="BEZIER")
    up = not up
    t += 0.28
rot(milo["Right"], 82.85, 0, 0, 0)
set_face(milo, "laugh", 80.95)                         # "Follow and like for Part 2!"
set_face(milo, "friendly", 82.4)
set_face(milo, "suspicious", 82.8)                     # "...and whatever you do..."

KNOCKER_STYLE = dict(skin=(205, 205, 212), top=(32, 32, 38), pants=(32, 32, 38), faces=["faceless"])
knocker = character("Knocker", R(-7.25, 0.4, 32.4), R(-7.25, 0.4, 25), KNOCKER_STYLE)
knocker["root"].scale = (1.9, 1.9, 1.9)                # tall: its blank face fills the window


def _descendants(root):
    out = []
    for ob in bpy.data.objects:
        p = ob
        while p:
            if p == root:
                out.append(ob)
                break
            p = p.parent
    return out


for _ob in _descendants(knocker["root"]):
    if _ob.type != "EMPTY":
        visible(_ob, [(84.2, None)])                     # appears on "don't open the door"
record_sound("STING_SMALL", 84.2)
fade(85.4, 1.0)                                        # hard cut to black
END = 86.3

# ---------------------------------------------------------------- RENDER SETTINGS
apply_interpolation()
set_interp("BEZIER")
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = F(END)
scene.frame_current = F(10)
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
try:
    scene.view_settings.look = "Medium High Contrast"
except Exception:
    pass

if ENGINE == "CYCLES":
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
else:
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = eng
            break
        except Exception:
            pass
    for attr, val in (("taa_render_samples", SAMPLES), ("use_gtao", True), ("use_raytracing", True),
                      ("volumetric_end", 900.0), ("use_shadows", True),
                      ("volumetric_tile_size", "16"), ("volumetric_samples", 32)):   # haze: invisible difference, faster
        try:
            setattr(scene.eevee, attr, val)
        except Exception:
            pass

try:
    scene.render.image_settings.media_type = "VIDEO"
except Exception:
    pass
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.audio_codec = "AAC"
scene.render.filepath = OUTPUT + "3Donly_"

# Make the viewport show the camera with materials, if Blender's UI is open
try:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.shading.type = "MATERIAL"
            space.region_3d.view_perspective = "CAMERA"
except Exception:
    pass


# ================================================================ FINAL VIDEO (render this scene)
# "FINAL" = the 3D scene + the soundtrack + one-word captions, all in Blender's
# video editor, so Ctrl+F12 renders the finished video with sound and captions.
# Caption times are in final-video seconds, matched to the voiceover.
CAPTION_FONT_SIZE = 165          # bigger number = bigger words
CAPTION_HEIGHT = 0.38            # 0 = bottom of screen, 1 = top
OUTRO_START = 80.6               # outro captions sit higher so they don't cover Milo's face
OUTRO_CAPTION_HEIGHT = 0.74
CAPTION_COLOURS = {"w": (1, 1, 1, 1), "y": (1.0, 0.84, 0.16, 1), "r": (1.0, 0.27, 0.27, 1)}

CAPTION_WORDS = [
    (0.05, 0.453, 'NEVER', 'r'),
    (0.453, 0.798, 'OPEN', 'r'),
    (0.798, 1.085, 'THE', 'r'),
    (1.085, 1.43, 'DOOR', 'r'),
    (1.43, 1.833, 'AFTER', 'r'),
    (1.833, 2.28, '3AM', 'r'),
    (2.3, 2.455, 'WE', 'w'),
    (2.455, 2.727, 'MOVED', 'w'),
    (2.727, 2.882, 'TO', 'w'),
    (2.882, 3.27, 'BLOXBURY', 'w'),
    (3.27, 3.425, 'ON', 'w'),
    (3.425, 3.541, 'A', 'w'),
    (3.541, 4.24, 'TUESDAY.', 'w'),
    (4.8, 4.976, 'BY', 'w'),
    (4.976, 5.65, 'WEDNESDAY,', 'w'),
    (5.67, 5.787, 'I', 'w'),
    (5.787, 6.022, 'KNEW', 'w'),
    (6.022, 6.451, 'SOMETHING', 'w'),
    (6.451, 6.647, 'WAS', 'w'),
    (6.647, 7.27, 'WRONG.', 'w'),
    (9.2, 9.381, 'MUM', 'w'),
    (9.381, 9.598, 'SAID', 'w'),
    (9.598, 9.851, "SHE'D", 'w'),
    (9.851, 9.996, 'BE', 'w'),
    (9.996, 10.213, 'HOME', 'w'),
    (10.213, 10.78, 'LATE.', 'w'),
    (12.1, 12.342, 'SHE', 'w'),
    (12.342, 12.728, 'ALWAYS', 'y'),
    (12.728, 13.32, 'WAS.', 'w'),
    (13.4, 13.528, '...I', 'w'),
    (13.528, 13.827, 'NEVER', 'y'),
    (13.827, 14.253, 'ACTUALLY', 'w'),
    (14.253, 14.467, 'SAW', 'w'),
    (14.467, 15.03, 'HER.', 'w'),
    (15.6, 15.823, 'THE', 'w'),
    (15.823, 16.091, 'GIRL', 'w'),
    (16.091, 16.359, 'NEXT', 'w'),
    (16.359, 16.626, 'DOOR,', 'y'),
    (16.626, 16.85, 'RAE,', 'y'),
    (16.85, 17.207, "DIDN'T", 'w'),
    (17.207, 17.474, 'EVEN', 'w'),
    (17.474, 17.698, 'SAY', 'w'),
    (17.698, 18.18, 'HELLO.', 'w'),
    (18.2, 18.46, 'NEW', 'w'),
    (18.46, 18.93, 'KID?', 'w'),
    (18.95, 19.195, 'ONE', 'w'),
    (19.195, 19.84, 'RULE.', 'w'),
    (20.2, 20.586, 'THREE', 'w'),
    (20.586, 21.028, 'KNOCKS', 'w'),
    (21.028, 21.414, 'AFTER', 'w'),
    (21.414, 22.04, '3AM...', 'w'),
    (22.1, 22.318, 'YOU', 'w'),
    (22.318, 22.622, "DON'T", 'w'),
    (22.622, 23.32, 'ANSWER.', 'w'),
    (23.4, 24.09, 'EVER.', 'r'),
    (25.75, 25.914, 'I', 'w'),
    (25.914, 26.406, 'THOUGHT', 'w'),
    (26.406, 26.679, 'SHE', 'w'),
    (26.679, 26.952, 'WAS', 'w'),
    (26.952, 27.39, 'JOKING.', 'w'),
    (27.39, 27.663, 'SHE', 'w'),
    (27.663, 28.43, "WASN'T.", 'w'),
    (28.45, 28.565, 'I', 'w'),
    (28.565, 28.795, 'KEEP', 'w'),
    (28.795, 28.91, 'A', 'w'),
    (28.91, 29.28, 'LIST.', 'w'),
    (29.3, 29.495, 'OF', 'w'),
    (29.495, 29.837, "WHO'S", 'w'),
    (29.837, 30.48, 'LEFT.', 'y'),
    (30.5, 30.828, "...WHO'S", 'w'),
    (30.828, 31.46, 'LEFT?', 'y'),
    (31.95, 32.201, 'THAT', 'w'),
    (32.201, 32.66, 'AFTERNOON,', 'w'),
    (32.66, 33.078, 'EVERYONE', 'w'),
    (33.078, 33.454, 'BOARDED', 'w'),
    (33.454, 33.621, 'UP', 'w'),
    (33.621, 33.914, 'THEIR', 'w'),
    (33.914, 34.64, 'WINDOWS.', 'w'),
    (35.95, 36.143, 'AND', 'w'),
    (36.143, 36.335, 'THE', 'w'),
    (36.335, 36.682, "MAYOR'S", 'w'),
    (36.682, 36.952, 'HOUSE', 'w'),
    (36.952, 37.145, 'HAD', 'w'),
    (37.145, 37.299, 'NO', 'w'),
    (37.299, 37.88, 'DOOR.', 'y'),
    (40.4, 40.652, 'AT', 'w'),
    (40.652, 41.029, '2:57,', 'w'),
    (41.029, 41.469, 'EVERY', 'w'),
    (41.469, 41.909, 'LIGHT', 'w'),
    (41.909, 42.161, 'IN', 'w'),
    (42.161, 43.14, 'BLOXBURY...', 'w'),
    (43.75, 44.077, 'WENT', 'w'),
    (44.077, 44.7, 'OFF.', 'y'),
    (45.95, 46.379, 'EXCEPT', 'r'),
    (46.379, 47.05, 'MINE.', 'r'),
    (51.5, 52.37, '3AM', 'r'),
    (57.75, 58.647, 'KNOCK.', 'y'),
    (58.647, 59.543, 'KNOCK.', 'y'),
    (59.543, 60.73, 'KNOCK.', 'y'),
    (60.75, 60.933, 'I', 'w'),
    (60.933, 61.481, 'CHECKED', 'w'),
    (61.481, 61.785, 'THE', 'w'),
    (61.785, 62.272, 'WINDOW.', 'w'),
    (62.272, 62.759, 'NOBODY', 'y'),
    (62.759, 63.064, 'WAS', 'w'),
    (63.064, 63.58, 'THERE.', 'w'),
    (63.6, 63.952, 'THEN', 'w'),
    (63.952, 64.187, 'IT', 'w'),
    (64.187, 64.539, 'WENT', 'w'),
    (64.539, 65.3, 'QUIET.', 'w'),
    (66.9, 67.145, 'THEN', 'w'),
    (67.145, 67.35, 'THE', 'w'),
    (67.35, 67.759, 'KNOCKING', 'w'),
    (67.759, 68.004, 'CAME', 'w'),
    (68.004, 68.64, 'AGAIN.', 'w'),
    (69.0, 69.328, 'FROM', 'r'),
    (69.328, 69.765, 'INSIDE', 'r'),
    (69.765, 69.983, 'MY', 'r'),
    (69.983, 70.77, 'CLOSET.', 'r'),
    (73.95, 74.158, 'AND', 'w'),
    (74.158, 74.282, 'A', 'w'),
    (74.282, 74.573, 'VOICE', 'w'),
    (74.573, 75.38, 'WHISPERED...', 'w'),
    (76.0, 76.486, 'MILO...', 'r'),
    (76.486, 76.891, 'LET', 'r'),
    (76.891, 77.215, 'ME', 'r'),
    (77.215, 77.97, 'OUT.', 'r'),
    (78.75, 78.988, 'IT', 'r'),
    (78.988, 79.345, 'KNEW', 'r'),
    (79.345, 79.583, 'MY', 'r'),
    (79.583, 80.29, 'NAME.', 'r'),
    (80.8, 81.014, 'WANT', 'w'),
    (81.014, 81.157, 'TO', 'w'),
    (81.157, 81.372, 'FIND', 'w'),
    (81.372, 81.551, 'OUT', 'w'),
    (81.551, 81.729, 'WHO', 'w'),
    (81.729, 81.908, 'WAS', 'w'),
    (81.908, 82.051, 'IN', 'w'),
    (82.051, 82.194, 'MY', 'w'),
    (82.194, 82.73, 'CLOSET?', 'y'),
    (82.75, 83.077, 'FOLLOW', 'y'),
    (83.077, 83.282, 'AND', 'w'),
    (83.282, 83.527, 'LIKE', 'y'),
    (83.527, 83.732, 'FOR', 'w'),
    (83.732, 83.977, 'PART', 'y'),
    (83.977, 84.45, '2!', 'y'),
    (84.6, 84.765, '...AND', 'w'),
    (84.765, 85.094, 'WHATEVER', 'w'),
    (85.094, 85.258, 'YOU', 'w'),
    (85.258, 85.74, 'DO...', 'w'),
    (86.0, 86.23, "DON'T", 'r'),
    (86.23, 86.428, 'OPEN', 'r'),
    (86.428, 86.593, 'THE', 'r'),
    (86.593, 87.14, 'DOOR.', 'r'),
]


def _caption_font():
    for p in ("C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Black.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            try:
                return bpy.data.fonts.load(p, check_existing=True)
            except Exception:
                pass
    return None


fin = bpy.data.scenes.new("FINAL")
fin.render.fps = FPS
fin.render.resolution_x, fin.render.resolution_y = 1080, 1920
fin.render.resolution_percentage = 100
fin.frame_start, fin.frame_end = 1, scene.frame_end
try:
    fin.render.image_settings.media_type = "VIDEO"
except Exception:
    pass
fin.render.image_settings.file_format = "FFMPEG"
fin.render.ffmpeg.format = "MPEG4"
fin.render.ffmpeg.codec = "H264"
fin.render.ffmpeg.constant_rate_factor = "HIGH"
fin.render.ffmpeg.audio_codec = "AAC"
for attr, val in (("audio_bitrate", 192), ("audio_mixrate", 48000), ("audio_channels", "STEREO")):
    try:
        setattr(fin.render.ffmpeg, attr, val)
    except Exception:
        pass
fin.render.filepath = OUTPUT
fin.render.use_sequencer = True

_se = fin.sequence_editor_create()
_strips = getattr(_se, "strips", None)
if _strips is None:
    _strips = _se.sequences

# The 3D picture comes from the PNG frames rendered by "Scene" (step 1), not a live
# scene strip: memory stays low and a crash only costs the frame in progress.
FRAMES_DIR = "//frames/"
_first = bpy.path.abspath(FRAMES_DIR + "0001.png")
_img = _strips.new_image("Bloxbury frames", _first, 1, 1)
for _f in range(2, scene.frame_end + 1):
    _img.elements.append("%04d.png" % _f)
if os.path.exists(AUDIO_FILE):
    _strips.new_sound("Soundtrack", AUDIO_FILE, 2, 1)
else:
    print("WARNING: soundtrack not found at", AUDIO_FILE, "- the video will be silent.")


def _new_text(name, channel, f0, f1):
    try:
        return _strips.new_effect(name=name, type="TEXT", channel=channel, frame_start=f0, length=f1 - f0)
    except TypeError:
        return _strips.new_effect(name=name, type="TEXT", channel=channel, frame_start=f0, frame_end=f1)


_cfont = _caption_font()
for i, (t0, t1, word, col) in enumerate(CAPTION_WORDS):
    f0 = int(round(t0 * FPS)) + 1
    f1 = max(int(round(t1 * FPS)) + 1, f0 + 2)
    st = _new_text("Cap %03d %s" % (i, word), 3 + (i % 2), f0, f1)
    st.text = word
    size = min(CAPTION_FONT_SIZE, int(940 / (0.8 * max(len(word), 1))))   # long words shrink to fit
    for attr, val in (("font_size", size), ("color", CAPTION_COLOURS[col]),
                      ("use_outline", True), ("outline_color", (0, 0, 0, 1)), ("outline_width", 0.25),
                      ("use_shadow", True), ("shadow_color", (0, 0, 0, 0.6)),
                      ("use_bold", _cfont is None),
                      ("location", (0.5, CAPTION_HEIGHT if t0 < OUTRO_START else OUTRO_CAPTION_HEIGHT)),
                      ("anchor_x", "CENTER"), ("anchor_y", "CENTER"), ("alignment_x", "CENTER"),
                      ("align_x", "CENTER"), ("wrap_width", 0.95)):
        try:
            setattr(st, attr, val)
        except Exception:
            pass
    if _cfont:
        try:
            st.font = _cfont
        except Exception:
            pass

try:
    bpy.context.window.scene = fin
except Exception:
    pass

print("Bloxbury Part 1 built: %d frames (%.1f s). Soundtrack: %s. Render > Render Animation (Ctrl+F12) renders the FINAL scene." % (scene.frame_end, warp(END), "found" if os.path.exists(AUDIO_FILE) else "MISSING"))
