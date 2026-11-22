# props5.py - TOWN DETAIL PASS (draft for Joel's approval). Turns Bloxbury Town's box houses into Roblox-Bloxburg-style
# homes without rebuilding the town: reads each house's own Door / Window parts and adds trim around them.
# Load after the town is built + props.py/props4.py:  exec(open(LIB + "props5.py").read()); detail_town(houses, "MiloHouse")
# Render cost: ~40 boxes per house, shared materials, glows are emission only (no lights).
import math, random
from mathutils import Vector as _TV, Matrix as _TM

_T = {}


def tmat(name, rgb, **kw):
    if name not in _T: _T[name] = pmat("T_" + name, rgb, **kw)
    return _T[name]


def _tb(name, size, loc, m, parent, r=0.03, rot=(0, 0, 0)):
    return rb(name, tuple(size), _TV(loc), m, parent, r=r, rot=rot)


def _parent_keep(o, p):
    mw = o.matrix_world.copy(); o.parent = p; o.matrix_parent_inverse = p.matrix_world.inverted(); o.matrix_world = mw


def detail_house(root, seed=0, yard=True, hollow=False):
    """root = a town house empty (solid_house / milo_house). Front = the side the door is on."""
    bpy.context.view_layer.update()
    rnd = random.Random(seed)
    kids = list(root.children)
    door = next((o for o in kids if o.name.startswith(("Door", "FrontDoor"))), None)
    wins = [o for o in kids if o.name.startswith("Window")]
    if door is None: return
    ny = 1.0 if door.location.y > 0 else -1.0          # outward normal (local y)
    fw = ny * 10.0                                      # front wall outer face
    trim = tmat("trim", (246, 246, 240), rough=0.5)
    shutter = tmat("shut%d" % (seed % 4), [(60, 70, 90), (40, 70, 60), (110, 50, 45), (50, 50, 55)][seed % 4], rough=0.6)
    grey = tmat("plinth", (120, 118, 114), rough=0.9)
    # body: corner boards, plinth, fascia under the roof
    for x in (-12.1, 12.1):
        for y in (-10.1, 10.1):
            _tb("CornerB", (0.55, 0.55, 13.6), (x, y, 6.8), trim, root, r=0.04)
    for (sx, sy, x, y) in ((24.6, 0.35, 0, fw + ny * 0.12), (24.6, 0.35, 0, -fw - ny * 0.12), (0.35, 20.6, 12.12, 0), (0.35, 20.6, -12.12, 0)):
        _tb("Plinth", (sx, sy, 1.0), (x, y, 0.5), grey, root, r=0.03)
        _tb("Fascia", (sx + 2.2 if sx > 1 else sx, sy if sx > 1 else sy + 2.2, 0.7), (x * (1.08 if x else 1), y * (1.1 if y else 1), 13.75), trim, root, r=0.04)
    # windows: frame, sill, cross mullion, shutters, flower box
    for w in wins:
        wx, wz = w.location.x, w.location.z; sx, sz = w.scale.x, w.scale.z
        y0 = fw + ny * 0.25
        for dx in (-1, 1): _tb("WinTrimV", (0.4, 0.5, sz + 0.8), (wx + dx * (sx / 2 + 0.2), y0, wz), trim, root)
        _tb("WinTrimT", (sx + 1.2, 0.5, 0.4), (wx, y0, wz + sz / 2 + 0.2), trim, root)
        _tb("WinSill", (sx + 1.4, 0.9, 0.35), (wx, fw + ny * 0.45, wz - sz / 2 - 0.15), trim, root)
        gy = w.location.y + ny * (w.scale.y / 2)               # glass outer face
        _tb("WinMullV", (0.18, 0.2, sz), (wx, gy + ny * 0.1, wz), trim, root, r=0.02)
        _tb("WinMullH", (sx, 0.2, 0.18), (wx, gy + ny * 0.1, wz), trim, root, r=0.02)
        cur = tmat("curt%d" % (seed % 3), [(240, 232, 214), (214, 226, 240), (236, 214, 214)][seed % 3], rough=0.9)
        for dx in (-1, 1):                                     # curtains drawn to the sides, just in front of the glass
            _tb("Curtain", (sx * 0.22, 0.06, sz - 0.1), (wx + dx * sx * 0.37, gy + ny * 0.03, wz), cur, root, r=0.02)
        _tb("CurtainTop", (sx - 0.1, 0.06, sz * 0.14), (wx, gy + ny * 0.03, wz + sz * 0.42), cur, root, r=0.02)
        for dx in (-1, 1):
            sh = _tb("Shutter", (1.3, 0.25, sz + 0.6), (wx + dx * (sx / 2 + 1.1), fw + ny * 0.2, wz), shutter, root, r=0.04)
            for k in range(4):
                _tb("Louvre", (1.0, 0.1, 0.12), (wx + dx * (sx / 2 + 1.1), fw + ny * 0.36, wz - sz / 2 + 0.3 + k * (sz / 4 + 0.05)), shutter, root, r=0.02)
        if not hollow or wz < 7:
            _tb("FlowerBox", (sx + 0.4, 0.8, 0.6), (wx, fw + ny * 0.9, wz - sz / 2 - 0.65), tmat("fbox", (120, 80, 50), rough=0.8), root, r=0.05)
            for k in range(6):
                c = rnd.choice([(230, 70, 90), (250, 200, 60), (240, 240, 245), (170, 90, 200)])
                _tb("Flower", (0.32, 0.32, 0.32), (wx - sx / 2 + 0.5 + k * (sx - 0.8) / 5, fw + ny * (0.9 + rnd.uniform(-0.15, 0.15)), wz - sz / 2 - 0.2 + rnd.uniform(0, 0.15)), tmat("fl%s" % (c,), c, rough=0.6), root, r=0.1)
                _tb("Leaf", (0.4, 0.4, 0.2), (wx - sx / 2 + 0.5 + k * (sx - 0.8) / 5, fw + ny * 0.9, wz - sz / 2 - 0.38), tmat("leaf", (70, 130, 60), rough=0.8), root, r=0.08)
    # door: frame, raised panels + knob (parented to the door so knocks/hinges carry them), step, light, number, mat
    dx_, dz_ = door.location.x, door.location.z; dw, dh = door.scale.x, door.scale.z
    yd = fw + ny * 0.3
    for s_ in (-1, 1): _tb("DoorTrimV", (0.5, 0.5, dh + 0.5), (dx_ + s_ * (dw / 2 + 0.25), yd, dh / 2 + 0.25), trim, root)
    _tb("DoorTrimT", (dw + 1.5, 0.6, 0.55), (dx_, yd + ny * 0.05, dh + 0.3), trim, root)
    face = door.location.y + ny * (door.scale.y / 2 + 0.04)
    parts = [_tb("DoorPanel", (dw - 1.4, 0.12, dh * 0.36), (dx_, face, dh * 0.72), tmat("doorpan", (100, 66, 42), rough=0.7), root),
             _tb("DoorPanel", (dw - 1.4, 0.12, dh * 0.36), (dx_, face, dh * 0.3), tmat("doorpan", (100, 66, 42), rough=0.7), root),
             _tb("DoorKnob", (0.32, 0.3, 0.32), (dx_ + dw / 2 - 0.6, face + ny * 0.12, dh * 0.48), tmat("brass", (205, 170, 80), metal=0.85, rough=0.3), root, r=0.14),
             _tb("Letterbox", (1.2, 0.08, 0.3), (dx_, face + ny * 0.02, dh * 0.53), tmat("brass", (205, 170, 80), metal=0.85, rough=0.3), root, r=0.04)]
    bpy.context.view_layer.update()
    for p_ in parts: _parent_keep(p_, door)
    _tb("Step", (dw + 3.0, 2.2, 0.45), (dx_, fw + ny * 1.1, 0.22), grey, root, r=0.05)
    _tb("Step2", (dw + 2.0, 1.2, 0.45), (dx_, fw + ny * 2.7, 0.12), grey, root, r=0.05)
    _tb("Doormat", (dw - 0.6, 1.3, 0.06), (dx_, fw + ny * 1.2, 0.48), tmat("mat", (140, 100, 60), rough=1.0), root, r=0.02)
    _tb("PorchLight", (0.6, 0.4, 0.9), (dx_ + dw / 2 + 1.3, fw + ny * 0.35, dh * 0.78), tmat("lampblk", (30, 30, 34), rough=0.4), root, r=0.06)
    _tb("PorchGlow", (0.4, 0.3, 0.6), (dx_ + dw / 2 + 1.3, fw + ny * 0.5, dh * 0.75), tmat("porchglow", (255, 220, 160), emit=2.5, emit_rgb=(255, 210, 150)), root, r=0.05)
    _tb("HouseNo", (0.9, 0.12, 0.6), (dx_ - dw / 2 - 1.2, fw + ny * 0.1, dh * 0.75), tmat("plaque", (245, 245, 240), rough=0.5), root, r=0.04)
    # roof: gutter + downpipe + chimney
    _tb("Gutter", (26.0, 0.5, 0.45), (0, ny * 11.2, 13.85), trim, root, r=0.08)
    _tb("Downpipe", (0.4, 0.4, 13.6), (11.5, ny * 10.45, 6.9), trim, root, r=0.12)
    _tb("Chimney", (2.2, 2.2, 5.0), (5.5, -ny * 3.0, 20.0), tex_mat("Brick", (150, 70, 55), "tiles"), root, r=0.04)
    _tb("ChimneyCap", (2.7, 2.7, 0.4), (5.5, -ny * 3.0, 22.6), grey, root, r=0.05)
    if yard:
        # path to the pavement, two bushes, a flower bed, a mailbox
        for k in range(5):
            _tb("PathSlab", (3.2, 1.6, 0.12), (dx_ + rnd.uniform(-0.15, 0.15), fw + ny * (4.4 + k * 2.0), 0.06), tmat("slab", (196, 192, 184), rough=0.9), root, r=0.04)
        for s_ in (-1, 1):
            solid("Bush", SPHERE, (2.6, 2.2, 2.0), _TV((dx_ + s_ * 5.6, fw + ny * 1.8, 0.9)), tmat("bush", (60, 120, 55), rough=0.9), parent=root)
            solid("Bush", SPHERE, (1.8, 1.6, 1.5), _TV((dx_ + s_ * 7.6, fw + ny * 1.6, 0.7)), tmat("bush2", (75, 140, 62), rough=0.9), parent=root)
        bed_x = rnd.choice((-1, 1)) * 8.8
        _tb("Bed", (5.0, 1.6, 0.3), (bed_x, fw + ny * 4.2, 0.15), tmat("soil", (90, 62, 42), rough=1.0), root, r=0.05)
        for k in range(7):
            c = rnd.choice([(230, 70, 90), (250, 200, 60), (240, 240, 245), (170, 90, 200), (250, 140, 60)])
            _tb("BedFl", (0.4, 0.4, 0.55), (bed_x - 2.1 + k * 0.7, fw + ny * (4.2 + rnd.uniform(-0.4, 0.4)), 0.55), tmat("fl%s" % (c,), c, rough=0.6), root, r=0.12)
        mb = _TV((dx_ + 4.0, fw + ny * 13.0, 0))
        _tb("MailPost", (0.3, 0.3, 3.0), mb + _TV((0, 0, 1.5)), tmat("post", (240, 240, 236)), root, r=0.05)
        _tb("Mailbox", (0.9, 1.6, 0.9), mb + _TV((0, 0, 3.3)), tmat("mbox%d" % (seed % 3), [(40, 70, 140), (180, 50, 45), (40, 40, 44)][seed % 3], rough=0.4), root, r=0.3)
        _tb("MailFlag", (0.08, 0.5, 0.2), mb + _TV((0.5, 0, 3.5)), tmat("flag", (220, 40, 40)), root, r=0.02)


def detail_town(houses, milo_name="MiloHouse"):
    for i, (nm, root) in enumerate(sorted(houses.items())):
        detail_house(root, seed=i)
    m = bpy.data.objects.get(milo_name)
    if m is not None: detail_house(m, seed=7, hollow=True)
