# props2.py - PROPS BATCH 2 (approved by Joel 22 Nov 2026, from Test 2 + Part 1).
# Load after props.py (needs rb, rcyl, plane, tube, pmat, wood, imgmat, empty, COL_PROPS, M_WOOD, M_METAL).
import math, bmesh as _bm_p2
from mathutils import Vector as _Vp


def p2_hammer(parent, name="Hammer"):
    """Claw-less hammer held in a hand grip (parent = P["tiltRight"])."""
    h = empty(name, _Vp((0, 0, 0)), col=COL_PROPS, parent=parent)
    rb(name + "Handle", (0.2, 0.2, 1.5), _Vp((0, 0.35, 0.55)), M_WOOD, h, r=0.05)
    rb(name + "Head", (0.36, 0.85, 0.36), _Vp((0, 0.35, 1.32)), M_METAL, h, r=0.05)
    return h


def p2_crate(loc, name="Crate", size=(2.6, 2.4, 2.0)):
    """Wooden crate to stand on (top at loc.z + size.z / 2)."""
    return rb(name, size, _Vp(loc), wood(name + "Wood", (150, 110, 70)), None, r=0.05)


def p2_notebook(parent, name="Notebook", colour=(170, 40, 45)):
    """Small red notebook held in a grip (parent = P["tiltLeft"])."""
    n = empty(name, _Vp((0, 0, 0)), col=COL_PROPS, parent=parent)
    rb(name + "Cover", (0.7, 0.14, 0.9), _Vp((0, 0.05, 0.1)), pmat(name + "Mat", colour, rough=0.7), n, r=0.03)
    n.location = (0.0, 0.55, 0.05)
    return n


def p2_list_img(path, title="WHO'S LEFT", names=("Mr. Hollis", "The Patels", "Jonah", "Mrs. Reed", "Old Tom", "Ellie",
                                                  "The Grants", "Rae", "Milo?"), crossed=7):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (600, 800), (244, 238, 220)); d = ImageDraw.Draw(im)
    for y in range(90, 800, 52): d.line((30, y, 570, y), fill=(170, 190, 220), width=2)
    d.line((80, 0, 80, 800), fill=(220, 120, 120), width=3)
    try:
        fh = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        fw = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except Exception: fh = fw = ImageFont.load_default()
    d.text((100, 28), title, fill=(150, 20, 20), font=fh)
    for i, nm in enumerate(names):
        y = 100 + i * 52 + 8
        d.text((100, y), nm, fill=(30, 30, 60), font=fw)
        if i < crossed:
            w = d.textlength(nm, font=fw); d.line((96, y + 20, 104 + w, y + 18), fill=(30, 30, 40), width=5)
    im.save(path)


def p2_list_insert(pos, path="/tmp/p2_list.png", **kw):
    """Open notebook page for insert shots: page (faces +y) on a red cover on a dark desk, its own soft key light.
    Camera: page centre is pos + (0, 0, 3)."""
    import bpy
    p2_list_img(path, **kw); pos = _Vp(pos)
    plane("ListPage", 3.0, 4.0, pos + _Vp((0, 0, 3.0)), imgmat("ListPage", path, rough=0.85), None)
    rb("ListCover", (3.4, 0.1, 4.4), pos + _Vp((0, -0.09, 3.0)), pmat("NoteRed", (170, 40, 45), rough=0.7), None, r=0.04)
    rb("ListBackdrop", (16, 0.2, 14), pos + _Vp((0, -0.6, 3.0)), wood("ListDesk", (70, 48, 34)), None, r=0.02)
    L = bpy.data.lights.new("InsertKey", "AREA"); L.energy = 400; L.size = 4
    o = bpy.data.objects.new("InsertKey", L); bpy.context.scene.collection.objects.link(o)
    o.location = pos + _Vp((2.5, 6, 6)); o.rotation_euler = (pos + _Vp((0, 0, 3)) - o.location).to_track_quat("-Z", "Y").to_euler()
    return pos + _Vp((0, 0, 3.0))


def p2_newspaper_img(path, title="BLOXBURY DAILY", headline="KNOCKING CONTINUES"):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (640, 440), (238, 234, 222)); d = ImageDraw.Draw(im)
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 54)
        fh = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except Exception: fb = fh = ImageFont.load_default()
    d.text((320, 44), title, fill=(20, 20, 22), font=fb, anchor="mm")
    d.line((24, 82, 616, 82), fill=(20, 20, 22), width=4); d.line((24, 90, 616, 90), fill=(20, 20, 22), width=1)
    d.text((320, 130), headline, fill=(150, 20, 20), font=fh, anchor="mm")
    d.rectangle((30, 170, 300, 330), fill=(70, 72, 80)); d.rectangle((60, 200, 270, 300), fill=(120, 122, 132))
    for c, x0 in enumerate((320, 470)):
        for k in range(14): d.rectangle((x0, 172 + k * 18, x0 + 130 - (k * 23) % 40, 180 + k * 18), fill=(110, 108, 104))
    for k in range(5): d.rectangle((30, 345 + k * 18, 600 - (k * 37) % 90, 353 + k * 18), fill=(110, 108, 104))
    im.save(path)


def p2_newspaper(name, parent, path="/tmp/p2_news.png", w=1.7, h=1.15, **kw):
    """Two-sided newspaper (printed front, plain back). Returns its root empty."""
    p2_newspaper_img(path, **kw)
    mf = imgmat(name + "Front", path, rough=0.8); mb = pmat(name + "Back", (228, 224, 212), rough=0.85)
    root = empty(name, _Vp((0, 0, 0)), col=COL_PROPS, parent=parent)
    plane(name + "_F", w, h, _Vp((0, 0.012, 0)), mf, root)
    plane(name + "_B", w, h, _Vp((0, -0.012, 0)), mb, root, rot=(0, 0, math.pi))
    return root


def p2_mug(parent, name="Mug", colour=(196, 52, 46)):
    """HOLLOW mug (open top, 0.045 wall, coffee inside) in a right-hand grip. Sip pose: arm target (0.2, 0.75, 3.7), tilt ~25 deg."""
    m = pmat(name + "Mat", colour, rough=0.35, coat=0.6)
    mug = empty(name, _Vp((-0.1, 0.5, 0.15)), col=COL_PROPS, parent=parent)
    body = rcyl(name + "Body", 0.3, 0.62, _Vp((0, 0, 0)), m, mug, bevel=0.0)
    b = _bm_p2.new(); b.from_mesh(body.data)
    _bm_p2.ops.delete(b, geom=[f for f in b.faces if f.normal.z > 0.99 and f.calc_center_median().z > 0.3], context="FACES_ONLY")
    b.to_mesh(body.data); b.free()
    so = body.modifiers.new("Wall", "SOLIDIFY"); so.thickness = 0.045; so.offset = -1; so.use_even_offset = True
    bv = body.modifiers.new("RimRound", "BEVEL"); bv.width = 0.012; bv.segments = 2; bv.limit_method = "ANGLE"
    rcyl(name + "Coffee", 0.252, 0.02, _Vp((0, 0, 0.16)), pmat("Coffee", (60, 34, 20), rough=0.15), mug, bevel=0.0)
    tube(name + "Handle", [(0.28, 0, 0.18), (0.48, 0, 0.12), (0.48, 0, -0.12), (0.28, 0, -0.18)], 0.06, m, mug)
    mug.rotation_euler = (0, 0, math.radians(-90))
    return mug


def p2_cafe_table(loc, name="Cafe"):
    loc = _Vp(loc); tw = wood(name + "Wood", (130, 88, 56)); blk = pmat(name + "Black", (30, 30, 34), rough=0.4)
    rcyl(name + "Top", 1.6, 0.16, loc + _Vp((0, 0, 2.45)), tw, None)
    rcyl(name + "Stem", 0.16, 2.3, loc + _Vp((0, 0, 1.2)), blk, None, bevel=0.0)
    rcyl(name + "Foot", 0.9, 0.1, loc + _Vp((0, 0, 0.06)), blk, None)
    return loc + _Vp((0, 0, 2.53))      # table-top height


def p2_round_bin(loc, name="Bin"):
    loc = _Vp(loc)
    rcyl(name, 0.85, 2.1, loc + _Vp((0, 0, 1.05)), pmat(name + "Grey", (70, 74, 80), rough=0.35, metal=0.4), None, bevel=0.03)
    rcyl(name + "In", 0.75, 0.05, loc + _Vp((0, 0, 2.08)), pmat(name + "Dark", (18, 18, 20), rough=0.9), None, bevel=0.0)
    return loc + _Vp((0, 0, 2.3))       # drop point


def p2_door_glow(x, y, width=4.6, floor_z=0.43, name="GlowStrip"):
    """The approved soft RED-ORANGE glow under a door: emissive strip (scale y 0 = off) + point light behind the door.
    Returns (strip, light_data). Key strip.scale (1,0,0)->(1,1,1) and light energy 0->140 (up to ~600 at the climax)."""
    import bpy
    strip = rb(name, (width, 0.3, 0.05), _Vp((x, y + 0.12, floor_z)), pmat(name + "Mat", (255, 90, 30), emit=6.0, emit_rgb=(255, 82, 20)), None)
    strip.scale = (1, 0, 0)
    L = bpy.data.lights.new(name + "Light", "POINT"); L.color = (1.0, 0.32, 0.08); L.energy = 0; L.shadow_soft_size = 1.5
    o = bpy.data.objects.new(name + "Light", L); bpy.context.scene.collection.objects.link(o); o.location = (x, y - 0.9, 1.2)
    return strip, L


PROPS2 = ["hammer", "crate", "notebook", "WHO'S LEFT list insert", "newspaper (BLOXBURY DAILY)", "hollow mug",
          "cafe table", "round bin", "door glow (red-orange)"]
