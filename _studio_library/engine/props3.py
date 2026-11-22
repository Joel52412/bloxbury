# props3.py - PROPS + SETS BATCH 3 (Part 2 "She Came Home", approved by Joel 22 Nov 2026 13:27).
# Load after props.py / props2.py (uses pmat, rb, root_of, CHROME, BLACKPL, tex_mat, kitchen, fridge, dining_set...).
import math, bmesh
from mathutils import Vector as _V3


def p3_toaster(loc, name="Toaster"):
    """Chrome two-slot toaster (put on a worktop). Rewatch bait: its chrome reflects the room."""
    r = root_of(name, loc); ch = CHROME()
    rb(name + "Body", (1.7, 1.0, 1.15), _V3((0, 0, 0.6)), ch, r, r=0.25)
    for dx in (-0.35, 0.35): rb(name + "Slot", (0.18, 0.75, 0.06), _V3((dx, 0, 1.18)), BLACKPL(), r, r=0.02)
    rb(name + "Lever", (0.12, 0.25, 0.12), _V3((0.92, 0, 0.75)), BLACKPL(), r, r=0.03)
    rb(name + "Base", (1.8, 1.1, 0.12), _V3((0, 0, 0.06)), BLACKPL(), r, r=0.04)
    return r


def p3_room(name, org, w, d, h, wall_rgb, floor_rgb, wall_kind="plaster", floor_kind="planks"):
    """Open-front box room (floor, back/left/right walls, ceiling, skirting). Camera looks from -y toward +y."""
    o = _V3(org); root = root_of(name, o)
    fm = tex_mat(name + "Floor", floor_rgb, floor_kind, rough=0.6) if floor_kind else pmat(name + "Floor", floor_rgb)
    wm = tex_mat(name + "Wall", wall_rgb, wall_kind)
    rb(name + "FloorB", (w, d, 0.3), _V3((0, 0, -0.15)), fm, root, r=0.02)
    rb(name + "Back", (w, 0.4, h), _V3((0, d / 2, h / 2)), wm, root, r=0.02)
    rb(name + "Left", (0.4, d, h), _V3((-w / 2, 0, h / 2)), wm, root, r=0.02)
    rb(name + "Right", (0.4, d, h), _V3((w / 2, 0, h / 2)), wm, root, r=0.02)
    rb(name + "Ceil", (w, d, 0.3), _V3((0, 0, h + 0.15)), pmat(name + "CeilM", (240, 238, 232), rough=0.9), root, r=0.02)
    rb(name + "Skirt", (w - 0.5, 0.2, 0.5), _V3((0, d / 2 - 0.25, 0.25)), pmat(name + "SkirtM", (246, 246, 242)), root, r=0.02)
    return root


def p3_area(name, loc, tgt, energy, size, col=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.energy = energy; d_.size = size; d_.color = col
    ob = bpy.data.objects.new(name, d_); bpy.context.scene.collection.objects.link(ob); ob.location = _V3(loc)
    ob.rotation_euler = (_V3(tgt) - _V3(loc)).to_track_quat("-Z", "Y").to_euler(); return d_


def p3_kitchen_set(KO):
    """SET: Mum's sunny kitchen (26 x 18 x 11). Build in the air (z=400) so town hills stay out of frame.
    Hob at KO+(2.6, 5.5); toaster at KO+(-6.6, 6.6, 4.1); table at KO+(-6.5, -2.5). Returns dict of handles."""
    KO = _V3(KO)
    p3_room("Kitchen", KO, 26, 18, 11, (246, 236, 206), (196, 160, 118))
    kit = kitchen("KitUnit", cab=(120, 156, 170), top=(238, 234, 226), loc=KO + _V3((-2, 7.2, 0))); kit.rotation_euler = (0, 0, math.radians(180))
    fridge("Fridge", loc=KO + _V3((9.6, 6.8, 0)))
    dining_set("Table", loc=KO + _V3((-6.5, -2.5, 0)))
    plant("KPlant", loc=KO + _V3((-11.5, 7.5, 0)), seed=4)
    wall_clock("KClock", loc=KO + _V3((6, 8.75, 8.2))).rotation_euler = (0, 0, math.radians(180))
    toast = p3_toaster(KO + _V3((-6.6, 6.6, 4.1)), "Toaster")
    rb("KWindow", (6.0, 0.1, 3.6), KO + _V3((1.0, 8.75, 7.4)), pmat("KSky", (200, 225, 255), emit=3.0, emit_rgb=(225, 238, 255)), None, r=0.02)
    wf = pmat("WinFrame", (250, 250, 248))
    for dx in (-3.05, 3.05): rb("KWinF", (0.25, 0.3, 3.9), KO + _V3((1.0 + dx, 8.65, 7.4)), wf, None, r=0.03)
    for dz in (-1.9, 1.9): rb("KWinF", (6.3, 0.3, 0.25), KO + _V3((1.0, 8.65, 7.4 + dz)), wf, None, r=0.03)
    sun = p3_area("KSun", KO + _V3((1.0, 7.5, 9.5)), KO + _V3((-3, -2, 0)), 2600, 6, (1.0, 0.9, 0.75))
    fill = p3_area("KFill", KO + _V3((0, -14, 9)), KO + _V3((0, 2, 3)), 1400, 14, (1.0, 0.97, 0.92))
    return {"toaster": toast, "sun": sun, "fill": fill, "hob": KO + _V3((2.6, 5.5, 4.0))}


def p3_hallway_set(HO):
    """SET: upstairs hallway at night (10 wide x 26 deep x 11), wall mirror on the LEFT wall (glass at x=-4.49,
    centre y=+2, z=5.2, 3.2 x 5.4), red runner, door at the far end (y=+12.8), warm ceiling lamp + cold moon fill.
    Mirror maths: camera at HO+(3.18,-9,5) aimed at the glass sees HO+(1.8,11) reflected in the middle."""
    HO = _V3(HO)
    p3_room("Hall", HO, 10, 26, 11, (182, 170, 150), (120, 86, 60))
    rb("MirrorFrame", (0.3, 3.8, 6.0), HO + _V3((-4.7, 2.0, 5.2)), pmat("MirrorWood", (70, 46, 30), rough=0.5), None, r=0.08)
    glass = rb("MirrorGlass", (0.06, 3.2, 5.4), HO + _V3((-4.52, 2.0, 5.2)), pmat("Mirror", (235, 238, 240), rough=0.0, metal=1.0), None, r=0.01)
    door("HallDoorEnd", loc=HO + _V3((0, 12.8, 0)))
    rb("Runner", (3.6, 22, 0.05), HO + _V3((0, 0, 0.03)), fabric("RunnerFab", (120, 40, 44)), None, r=0.01)
    lamp = p3_area("HallLamp", HO + _V3((0, 6, 10.5)), HO + _V3((0, 6, 0)), 260, 2.5, (1.0, 0.72, 0.45))
    moon = p3_area("HallMoon", HO + _V3((4.5, -12, 8)), HO + _V3((-3, 4, 3)), 300, 6, (0.55, 0.65, 1.0))
    return {"glass": glass, "lamp": lamp, "moon": moon}


def p3_hollow_closet():
    """Milo's closet as a HOLLOW shell (same outside as the solid ClosetBox, which gets hidden).
    Inside: x 4.2..9.8, y -48.8..-46.0, floor 0.4. The door hinge (CLOSET_HINGE) is on the +x side; the crack opens at x~4.6."""
    cb = bpy.data.objects["ClosetBox"]; cm = cb.material_slots[0].material; cb.hide_render = True; cb.hide_viewport = True
    for nm_, sz_, lc_ in (("ClosetBackP", (6.0, 0.2, 10.0), (7.0, -48.9, 5.0)), ("ClosetSideL", (0.2, 3.0, 10.0), (4.1, -47.5, 5.0)),
                          ("ClosetSideR", (0.2, 3.0, 10.0), (9.9, -47.5, 5.0)), ("ClosetTopP", (6.0, 3.0, 0.2), (7.0, -47.5, 9.9))):
        rb(nm_, sz_, _V3(lc_), cm, None, r=0.01)


P3_LIST_NAMES = ("Milo's Mum", "Mr. Hollis", "The Patels", "Jonah", "Mrs. Reed", "Old Tom", "Ellie", "Rae", "Milo?")


def p3_list_insert(pos, path="/tmp/p3_list.png"):
    """WHO'S LEFT page for Part 2: Milo's Mum crossed off FIRST (three weeks ago), ends 'Rae / Milo?'."""
    return p2_list_insert(pos, path=path, names=P3_LIST_NAMES, crossed=7)
