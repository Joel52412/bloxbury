# test2.py - Milo outro redo (smooth face rig v2) + coffee/newspaper body-acting test. 24 fps.
import bpy, math, random, os, json
from mathutils import Vector, Matrix
LIB = "/home/claude/studio_library/engine/"
src = open('/home/claude/bloxbury-blender/bloxbury_part1.py').read()
exec(src[:src.index('# Milo starts at the fence')])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for f in ("charlib", "stylelab", "hair2", "hair3", "faces2", "garments", "garments2", "hair4", "faces3", "faces4", "props"):
    exec(open(LIB + f + ".py").read())
V = Vector
OUT = os.environ.get("OUT", "/home/claude/talk/frames2")
os.makedirs(OUT, exist_ok=True)
ENV = json.load(open("/home/claude/talk/env2.json"))
FPS = 24
A_LEN, B_LEN, LEAD = ENV["a_len"], ENV["b_len"], ENV["lead"]
NF = len(ENV["rms"])
s = bpy.context.scene
s.render.fps = FPS
s.frame_start, s.frame_end = 1, NF
FA = lambda t: 1 + int(round(t * FPS))              # shot A time -> frame
B0 = FA(A_LEN)                                       # first frame of shot B
FB = lambda t: B0 + int(round(t * FPS))             # shot B time -> frame

# ------------------------------------------------------------------ keyframe helpers
_LOG = []


def kf(idb, path, frame, value, index=-1, interp="BEZIER"):
    if index >= 0: getattr(idb, path)[index] = value
    else: setattr(idb, path, value)
    idb.keyframe_insert(path, frame=frame, index=index)
    _LOG.append((idb, path, frame, interp))


def apply_interp():
    cache = {}
    for idb, path, frame, interp in _LOG:
        if idb not in cache:
            d = {}
            for fc in _fcurves(idb): d.setdefault(fc.data_path, []).append(fc)
            cache[idb] = d
        for fc in cache[idb].get(path, []):
            for kp in fc.keyframe_points:
                if int(round(kp.co.x)) == frame:
                    kp.interpolation = interp
                    if interp == "BEZIER": kp.easing = "AUTO"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def vis(objs, frame, on):
    for o in objs: kf(o, "hide_render", frame, not on, interp="CONSTANT")


R = math.radians

# ------------------------------------------------------------------ rig upgrade: hips / waist / head pivots
def upgrade_rig(P):
    """Adds Chest (waist pivot), HipL/HipR (leg pivots) and Head (nod layer under the neck)."""
    root = P["root"]; nm = root.name
    chest = empty(nm + "_Chest", V((0, 0, 2)), col=COL_CHARS, parent=root)
    hipL = empty(nm + "_HipL", V((-0.5, 0, 2)), col=COL_CHARS, parent=root)
    hipR = empty(nm + "_HipR", V((0.5, 0, 2)), col=COL_CHARS, parent=root)
    neck = P["neck"]
    head = empty(nm + "_Head", V((0, 0, 0)), col=COL_CHARS, parent=neck)

    def move(ob, piv, piv_body):
        ob.parent = piv
        ob.matrix_basis = Matrix.Translation(-V(piv_body)) @ ob.matrix_basis

    for ob in list(neck.children):                      # everything on the neck -> head layer (no offset)
        if ob is not head: ob.parent = head
    for ob in list(root.children):
        if ob in (chest, hipL, hipR): continue
        bb = [ob.matrix_basis @ V(c) for c in ob.bound_box] if ob.type != "EMPTY" else [ob.matrix_basis.translation]
        cz = sum(v.z for v in bb) / len(bb); cx = sum(v.x for v in bb) / len(bb)
        if ob.name.startswith("LegL") or (cz < 2.0 and cx < 0 and ob.type != "EMPTY"): move(ob, hipL, (-0.5, 0, 2))
        elif ob.name.startswith("LegR") or (cz < 2.0 and ob.type != "EMPTY"): move(ob, hipR, (0.5, 0, 2))
        elif cz > 4.05 and ob.type != "EMPTY": move(ob, head, (0, 0, 4))        # hair / hats parented to the root
        else: move(ob, chest, (0, 0, 2))                                        # torso, shoulders, neck, straps
    P.update(chest=chest, hipL=hipL, hipR=hipR, head=head)
    # grips at the hands (counter-rotated so held props stay upright) + tilt layer
    for side in ("Left", "Right"):
        g = empty(nm + "_Grip" + side, V((0, 0, -1.5)), col=COL_CHARS, parent=P[side]); g.rotation_mode = "ZYX"
        t = empty(nm + "_Tilt" + side, V((0, 0, 0)), col=COL_CHARS, parent=g)
        P["grip" + side] = g; P["tilt" + side] = t
    return P


SHOULDER = {"Left": V((-1.5, 0, 3.5)), "Right": V((1.5, 0, 3.5))}


def arm_angles(side, target):
    d = V(target) - SHOULDER[side]
    d.normalize()
    a = math.acos(max(-1, min(1, -d.z)))
    c = math.atan2(-d.x, d.y) if math.sin(a) > 1e-3 else 0.0
    return a, c


def arm(P, side, frame, target=None, euler=None, interp="BEZIER"):
    """Pose an arm by hand target (body space) or by raw euler; grip keeps held props level."""
    if target is not None:
        a, c = arm_angles(side, target)
    else:
        a, c = R(euler[0]), R(euler[1])
    kf(P[side], "rotation_euler", frame, (a, 0, c), interp=interp)
    kf(P["grip" + side], "rotation_euler", frame, (-a, 0, -c), interp=interp)


# ------------------------------------------------------------------ face rig v2 (smooth): brows/eyes are posed, mouths swap
def fsurf(x): return surf_y(max(-0.59, min(0.59, x)))


M_SPARK_CORE = mat("SparkCore", (255, 206, 40), emit=2.0, rough=0.5)
M_SPARK_HOT = mat("SparkHot", (255, 250, 215), emit=3.5, rough=0.5)


def spark_star(name, size, m, parent, dy):
    """Flat 4-point star facing the camera (+y): thin pointed rays, reads as a glint effect."""
    import bmesh as _bm2
    b = _bm2.new(); c = b.verts.new((0, dy, 0)); ring = []
    for i in range(8):
        a = i * math.pi / 4; r = size if i % 2 == 0 else size * 0.2
        ring.append(b.verts.new((r * math.cos(a), dy, r * math.sin(a))))
    for i in range(8):
        b.faces.new((c, ring[i], ring[(i + 1) % 8]))
    me = bpy.data.meshes.new(name); b.to_mesh(me); b.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); ob.parent = parent
    COL_CHARS.objects.link(ob)
    ob.visible_shadow = False; ob.visible_diffuse = False; ob.visible_glossy = False   # glows without lighting the eye
    return ob


def adopt(objs, piv, piv_loc):
    for o in objs:
        o.parent = piv
        o.matrix_basis = Matrix.Translation(-V(piv_loc)) @ o.matrix_basis


MOUTHS = {
    "rest_smile": lambda f: f.line([(-0.13, -0.15), (-0.05, -0.2), (0.05, -0.2), (0.13, -0.15)], M_INK, r=0.024),
    "rest_flat": lambda f: f.line([(-0.1, -0.19), (0.1, -0.19)], M_INK, r=0.022),
    "rest_frown": lambda f: f.line([(-0.11, -0.21), (0, -0.175), (0.11, -0.21)], M_INK, r=0.022),
    "rest_smirk": lambda f: f.line([(-0.1, -0.18), (0.04, -0.19), (0.15, -0.13)], M_INK, r=0.022),
    "rest_creepy": lambda f: f.line([(-0.2, -0.13), (-0.1, -0.19), (0.1, -0.19), (0.2, -0.13)], M_INK, r=0.02),
    "M": lambda f: f.line([(-0.09, -0.19), (0.09, -0.19)], M_INK, r=0.03),
    "half": lambda f: (f.oval(0, -0.19, 0.16, 0.075, M_INK), f.oval(0, -0.205, 0.08, 0.03, M_TONGUE, lift=0.008)),
    "small_o": lambda f: (f.oval(0, -0.19, 0.08, 0.08, M_INK),),
    "A": lambda f: (f.oval(0, -0.19, 0.21, 0.16, M_INK), f.oval(0, -0.23, 0.12, 0.05, M_TONGUE, lift=0.008),
                    f.oval(0, -0.13, 0.15, 0.03, M_EYEWHITE, lift=0.008)),
    "E": lambda f: (f.oval(0, -0.185, 0.26, 0.085, M_INK), f.oval(0, -0.17, 0.2, 0.03, M_EYEWHITE, lift=0.008)),
    "O": lambda f: (f.oval(0, -0.2, 0.12, 0.14, M_INK), f.oval(0, -0.235, 0.07, 0.04, M_TONGUE, lift=0.008)),
    "grin_open": lambda f: (f.oval(0, -0.18, 0.3, 0.17, M_INK), f.oval(0, -0.12, 0.24, 0.04, M_EYEWHITE, lift=0.008),
                            f.oval(0, -0.23, 0.14, 0.05, M_TONGUE, lift=0.008)),
    "teeth": lambda f: (f.oval(0, -0.19, 0.3, 0.1, M_INK), f.oval(0, -0.19, 0.25, 0.055, M_EYEWHITE, lift=0.008),
                        f.line([(-0.12, -0.19), (0.12, -0.19)], M_INK, r=0.006, lift=0.012)),
}


def build_face_v2(P):
    global FACE_SKIN
    FACE_SKIN = P["skin"]
    head = P["head"]; nm = P["root"].name
    rig = {"mouths": {}, "P": P}
    EW, EH, EZ = 0.12, 0.18, 0.08
    for side, sx in (("L", -0.19), ("R", 0.19)):
        base = V((sx, fsurf(sx), EZ - EH / 2 + 0.6))           # eye pivot at the bottom of the eye
        pe = empty(f"{nm}_Eye{side}", base, col=COL_CHARS, parent=head)
        pb = empty(f"{nm}_Blink{side}", V((0, 0, 0)), col=COL_CHARS, parent=pe)
        f = Face(head, "eye"); f.oval(sx, EZ, EW, EH, M_INK)
        f.oval(sx + EW * 0.24, EZ + EH * 0.26, EW * 0.34, EH * 0.24, M_SHINE70, lift=0.008)
        adopt(f.objs, pb, base)
        # sparkle catchlights (scale 0 = off; popped in/out smoothly, gentle twinkle)
        sp = []
        for dx, dz, sz in ((0.035, 0.13, 0.05), (-0.045, 0.03, 0.026)):
            loc = V((sx + dx, fsurf(sx + dx) + 0.03, dz + 0.6))
            pv = empty(f"{nm}_Spark{side}", loc - base, col=COL_CHARS, parent=pb); pv.scale = (0, 0, 0)
            spark_star("SpkCore", sz * 1.25, M_SPARK_CORE, pv, 0.004)    # yellow glint
            spark_star("SpkHot", sz * 0.6, M_SPARK_HOT, pv, 0.008)      # hot centre, reads as light
            sp.append(pv)
        bz = 0.235
        pbr = empty(f"{nm}_Brow{side}", V((sx, fsurf(sx), bz + 0.6)), col=COL_CHARS, parent=head)
        f = Face(head, "brow")
        f.line([(sx - 0.09, bz - 0.006 * (1 if sx < 0 else -1)), (sx + 0.09, bz + 0.006 * (1 if sx < 0 else -1))], M_INK, r=0.024)
        adopt(f.objs, pbr, (sx, fsurf(sx), bz + 0.6))
        rig["eye" + side], rig["blink" + side], rig["spark" + side], rig["brow" + side] = pe, pb, sp, pbr
    for k, fn in MOUTHS.items():
        f = Face(head, "m_" + k); fn(f); rig["mouths"][k] = f.objs
        vis(f.objs, 1, False)
    rig["cur_m"] = None
    return rig


# expression presets: (browL z, browL tilt, browR z, browR tilt, eye width, eye height)   tilt>0 = angry (inner ends down)
EX = {
    "neutral":  (0.0, 0.0, 0.0, 0.0, 1.0, 1.0),
    "curious":  (0.0, 0.04, 0.075, -0.12, 1.04, 1.08),
    "question": (0.05, -0.08, 0.08, -0.1, 1.08, 1.12),
    "excited":  (0.065, -0.1, 0.065, -0.1, 1.12, 1.16),
    "lean_in":  (-0.01, 0.1, 0.03, 0.02, 1.0, 0.78),
    "ominous":  (-0.035, 0.22, -0.03, 0.2, 1.0, 0.6),
    "sly":      (-0.02, 0.14, 0.045, -0.02, 1.0, 0.68),
    "content":  (0.03, -0.12, 0.03, -0.12, 1.0, 0.82),
    "notice":   (0.04, -0.04, 0.05, -0.06, 1.05, 1.08),
    "reading":  (-0.005, 0.05, -0.005, 0.05, 1.0, 0.92),
    "annoyed":  (-0.035, 0.24, -0.01, 0.12, 1.0, 0.68),
    "effort":   (-0.045, 0.3, -0.045, 0.3, 1.0, 0.55),
    "smug":     (-0.015, 0.1, 0.05, -0.05, 1.0, 0.72),
}


def expr(rig, frame, key, interp="BEZIER"):
    lz, lt, rz, rt, ew, eh = EX[key]
    for side, z, tilt in (("L", lz, lt), ("R", rz, -rt)):
        b = rig["brow" + side]; base = b.get("bz0")
        if base is None: b["bz0"] = base = b.location.z
        kf(b, "location", frame, base + z, index=2, interp=interp)
        kf(b, "rotation_euler", frame, (0, tilt, 0), interp=interp)
        kf(rig["eye" + side], "scale", frame, (ew, 1, eh), interp=interp)


def blink(rig, frame, closed=2):
    for side in ("L", "R"):
        b = rig["blink" + side]
        kf(b, "scale", frame - 1, (1, 1, 1)); kf(b, "scale", frame + 1, (1, 1, 0.06))
        kf(b, "scale", frame + 1 + closed, (1, 1, 0.06)); kf(b, "scale", frame + 3 + closed, (1, 1, 1))


def eyes_closed(rig, f0, f1):
    for side in ("L", "R"):
        b = rig["blink" + side]
        kf(b, "scale", f0 - 2, (1, 1, 1)); kf(b, "scale", f0, (1.05, 1, 0.06))
        kf(b, "scale", f1, (1.05, 1, 0.06)); kf(b, "scale", f1 + 3, (1, 1, 1))


def sparkle(rig, f_on, f_off):
    for side in ("L", "R"):
        for i, pv in enumerate(rig["spark" + side]):
            kf(pv, "scale", f_on - 1, (0, 0, 0))
            kf(pv, "scale", f_on + 3, (1.25, 1.25, 1.25)); kf(pv, "scale", f_on + 6, (0.95, 0.95, 0.95))
            fr = f_on + 9
            k = 0
            while fr < f_off - 4:                                # gentle twinkle, no flicker
                sc = 1.0 + (0.1 if (k + i) % 2 == 0 else -0.06)
                kf(pv, "scale", fr, (sc, sc, sc)); kf(pv, "rotation_euler", fr, (0, R(8 if (k + i) % 2 else -8), 0))
                fr += 9; k += 1
            kf(pv, "scale", f_off - 2, (1.0, 1.0, 1.0)); kf(pv, "scale", f_off + 2, (0, 0, 0))


def mouth(rig, frame, key):
    if rig["cur_m"] == key: return
    if rig["cur_m"]: vis(rig["mouths"][rig["cur_m"]], frame, False)
    vis(rig["mouths"][key], frame, True); rig["cur_m"] = key


def lipsync(rig, f0, f1, segs):
    """segs: list of (frame, rest_mouth, style). Mouth shapes from loudness + brightness; holds 2+ frames (no flicker)."""
    rms, cen = ENV["rms"], ENV["cen"]
    peak = max(rms[f0 - 1:f1]) or 1
    held = 0
    for fr in range(f0, f1 + 1):
        seg = [sg for sg in segs if sg[0] <= fr][-1]
        rest, style = seg[1], seg[2]
        lvl = rms[fr - 1] / peak if fr - 1 < len(rms) else 0
        c = cen[fr - 1] if fr - 1 < len(cen) else 0
        if style == "whisper":
            m = rest if lvl < 0.05 else ("small_o" if c < 1600 else "half") if lvl < 0.2 else "half"
        elif lvl < 0.1: m = rest
        elif lvl < 0.32: m = "M" if (fr // 3) % 4 == 3 else "half"
        elif style == "excited": m = "grin_open" if c > 1700 else ("O" if c < 1100 else "A")
        else: m = ("E" if c > 1800 else "A") if (fr // 2) % 3 else "O"
        if held > 0 and m != rig["cur_m"] and not (rig["cur_m"] or "").startswith("rest"):
            held -= 1; continue
        if m != rig["cur_m"]:
            mouth(rig, fr, m); held = 1


def accents(P, rig, f0, f1, nod=4.0, pop=0.03):
    """Head nods + brow pops on stressed syllables (local loudness peaks)."""
    rms = ENV["rms"]; peak = max(rms[f0 - 1:f1]) or 1
    sm = [sum(rms[max(0, i - 1):i + 2]) / 3 for i in range(len(rms))]
    last = -99; hits = []
    for fr in range(f0 + 1, f1 - 1):
        v = sm[fr - 1] / peak
        if v > 0.5 and sm[fr - 1] >= sm[fr - 2] and sm[fr - 1] >= sm[fr] and fr - last >= 6:
            hits.append(fr); last = fr
    hd = P["head"]
    for fr in hits:
        kf(hd, "rotation_euler", fr - 2, (0, 0, 0)); kf(hd, "rotation_euler", fr, (R(nod), 0, 0)); kf(hd, "rotation_euler", fr + 4, (R(-0.8), 0, 0))
        kf(hd, "rotation_euler", fr + 7, (0, 0, 0))
    return hits


# ------------------------------------------------------------------ characters
def make_milo():
    S = new_set(); skin = (234, 184, 146); rng = RNG(42)
    d_hoodie(S, (226, 156, 32), rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.ellipse((cx - 26, t.zrow(1.18) - 26, cx + 26, t.zrow(1.18) + 26), fill=(20, 20, 24))
    t.d.polygon([(cx - 14, t.zrow(1.12)), (cx + 14, t.zrow(1.12)), (cx + 20, t.zrow(0.82)), (cx - 20, t.zrow(0.82))], fill=(20, 20, 24))
    b_trousers(S, (34, 44, 82), rng, kind="jeans")
    for k in LEGS: shoes(S[k], (248, 248, 248), (214, 52, 52))
    finish(S, rng)
    P = build_body("Milo", skin, S)
    add_men_hair(P, "M4", random.Random(8), colour=(70, 44, 30))
    root = P["root"]; brass = mat("Brass2", (214, 168, 64), rough=0.3, metallic=0.9)
    tube("KeyCord", [(-0.42, 0.42, 4.02), (-0.2, 0.53, 3.8), (0, 0.555, 3.72), (0.2, 0.53, 3.8), (0.42, 0.42, 4.02)], 0.022,
         mat("Cord", (30, 30, 30)), root)
    disc("KeyBow", 0.24, 0.05, V((0, 0.57, 3.62)), brass, root)
    rpart("KeyShaft", (0.065, 0.045, 0.32), V((0, 0.57, 3.36)), brass, root, r=0.015)
    return P


def make_dan():
    S = new_set(); skin = (196, 140, 104); rng = RNG(77)
    d_button_shirt(S, (118, 160, 214), rng, skin)
    b_trousers(S, (186, 164, 124), rng, kind="chinos")
    s_shoes(S, "trainers", (90, 70, 56), rng)
    finish(S, rng)
    P = build_body("Dan", skin, S)
    add_hair4(P, "X1", random.Random(3), colour=(36, 26, 22))
    return P


# ------------------------------------------------------------------ props for the coffee scene
def newspaper_img(path):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (640, 440), (238, 234, 222)); d = ImageDraw.Draw(im)
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 54)
        fh = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except Exception:
        fb = fh = ImageFont.load_default()
    d.text((320, 44), "BLOXBURY DAILY", fill=(20, 20, 22), font=fb, anchor="mm")
    d.line((24, 82, 616, 82), fill=(20, 20, 22), width=4); d.line((24, 90, 616, 90), fill=(20, 20, 22), width=1)
    d.text((320, 130), "KNOCKING CONTINUES", fill=(150, 20, 20), font=fh, anchor="mm")
    d.rectangle((30, 170, 300, 330), fill=(70, 72, 80)); d.rectangle((60, 200, 270, 300), fill=(120, 122, 132))
    for c, x0 in enumerate((320, 470)):
        for k in range(14): d.rectangle((x0, 172 + k * 18, x0 + 130 - (k * 23) % 40, 180 + k * 18), fill=(110, 108, 104))
    for k in range(5): d.rectangle((30, 345 + k * 18, 600 - (k * 37) % 90, 353 + k * 18), fill=(110, 108, 104))
    im.save(path)


def paper_obj(name, parent, M_front, M_back, w=1.7, h=1.15):
    root = empty(name, V((0, 0, 0)), col=COL_PROPS, parent=parent)
    plane(name + "_F", w, h, V((0, 0.012, 0)), M_front, root)
    plane(name + "_B", w, h, V((0, -0.012, 0)), M_back, root, rot=(0, 0, math.pi))
    return root


# ------------------------------------------------------------------ world
w = bpy.data.worlds.new("Room"); s.world = w
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.62, 0.66, 0.78, 1); bg.inputs[1].default_value = 0.45


def light(name, loc, energy, size=6, col=(1, 1, 1), target=(0, 0, 4), kind="AREA"):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
    if kind == "AREA": d.size = size
    else: d.shadow_soft_size = size
    ob = bpy.data.objects.new(name, d); s.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


floor = bpy.data.objects.new("Floor", CUBE); s.collection.objects.link(floor); floor.scale = (80, 80, 0.1); floor.location = (0, 0, -0.05)
floor.material_slots[0].link = "OBJECT"; floor.material_slots[0].material = wood("FloorWood", (150, 110, 80), scale=0.6)
wall = bpy.data.objects.new("Wall", CUBE); s.collection.objects.link(wall); wall.scale = (60, 0.5, 30); wall.location = (0, -9, 15)
wall.material_slots[0].link = "OBJECT"; wall.material_slots[0].material = tex_mat("WallPaint", (120, 110, 150), "plaster")

milo = make_milo(); dan = make_dan()
for o in bpy.data.objects: o.animation_data_clear()
upgrade_rig(milo); upgrade_rig(dan)
milo["root"].location = (40, 0, 0)
fm = build_face_v2(milo); fd = build_face_v2(dan)

# ---- Milo's set: his room, closet door behind him (glow comes on for the warning)
MX = 40
light("M_Key", (MX + 5, 9, 8), 1500, col=(1.0, 0.93, 0.85), target=(MX, 0, 4))
mfill = light("M_Fill", (MX - 7, 7, 5), 500, col=(0.8, 0.85, 1.0), target=(MX, 0, 4))
light("M_Rim", (MX - 2, -8, 8), 1300, col=(0.85, 0.75, 1.0), target=(MX, 0, 4))
mkey = [o for o in bpy.data.objects if o.name == "M_Key"][0]
dr = door("ClosetDoor", loc=(MX + 4.2, -8.45, 0))
glow_l = light("ClosetGlow", (MX + 4.2, -7.6, 0.4), 0, size=2.5, col=(1.0, 0.32, 0.08), kind="POINT", target=(MX + 4.2, 0, 0))
strip = rb("GlowStrip", (3.2, 0.25, 0.06), V((MX + 4.2, -8.1, 0.05)), pmat("GlowRO", (255, 90, 30), emit=6.0, emit_rgb=(255, 82, 20)), None)
strip.scale = (1, 0, 0)
pl = plant("M_Plant", loc=(MX - 5.5, -5.5, 0), seed=4)
cl = wall_clock("M_Clock", loc=(MX - 3.6, -8.4, 8.2))

# ---- Dan's set: kitchen, café table with the paper, bin
light("D_Key", (8, 10, 10), 1700, col=(1.0, 0.92, 0.8), target=(0, 0, 3))
light("D_Fill", (-12, 9, 6), 650, col=(0.8, 0.86, 1.0), target=(-4, 0, 3))
light("D_Rim", (0, -7, 9), 1100, col=(1.0, 0.85, 0.7), target=(0, 0, 3))
kitchen("D_Kitchen", loc=(8.5, -5.8, 0))
fridge("D_Fridge", loc=(16, -6.2, 0))
plant("D_Plant", loc=(-12.5, -5.5, 0), seed=2)
wall_clock("D_Clock", loc=(-3, -8.4, 8.5))
win = rb("WinFrame", (5.2, 0.3, 3.8), V((-6.5, -8.45, 7.2)), pmat("WinWhite", (240, 240, 236), rough=0.4), None)
rb("WinSky", (4.6, 0.32, 3.2), V((-6.5, -8.43, 7.2)), pmat("Sky", (170, 205, 245), emit=1.2, emit_rgb=(180, 210, 250)), None)
rb("WinBar", (0.15, 0.36, 3.2), V((-6.5, -8.4, 7.2)), pmat("WinWhite", (240, 240, 236), rough=0.4), None)
TW = wood("CafeWood", (130, 88, 56))
TABLE = V((-6.3, 0.2, 0))
rcyl("CafeTop", 1.6, 0.16, TABLE + V((0, 0, 2.45)), TW, None)
rcyl("CafeStem", 0.16, 2.3, TABLE + V((0, 0, 1.2)), pmat("TblBlack", (30, 30, 34), rough=0.4), None, bevel=0.0)
rcyl("CafeFoot", 0.9, 0.1, TABLE + V((0, 0, 0.06)), pmat("TblBlack", (30, 30, 34), rough=0.4), None)
BIN = V((-10.2, -1.8, 0))
binm = pmat("BinGrey", (70, 74, 80), rough=0.35, metal=0.4)
rcyl("Bin", 0.85, 2.1, BIN + V((0, 0, 1.05)), binm, None, bevel=0.03)
rcyl("BinIn", 0.75, 0.05, BIN + V((0, 0, 2.08)), pmat("BinDark", (18, 18, 20), rough=0.9), None, bevel=0.0)
NP = "/tmp/bloxbury_news.png"; newspaper_img(NP)
M_NEWS = imgmat("News", NP, rough=0.8)
M_NEWSB = pmat("NewsBack", (228, 224, 212), rough=0.85)
# the three newspapers (table / hand / flying), only one visible at a time
pap_table = paper_obj("PaperTable", None, M_NEWS, M_NEWSB, 1.3, 0.9)
pap_table.location = TABLE + V((0.7, 0.15, 2.55)); pap_table.rotation_euler = (R(90), 0, R(-15))
pap_hand = paper_obj("PaperHand", dan["tiltLeft"], M_NEWS, M_NEWSB)
pap_fly = paper_obj("PaperFly", None, M_NEWS, M_NEWSB)
# mug in Dan's right hand
mugm = pmat("MugRed", (196, 52, 46), rough=0.35, coat=0.6)
mug = empty("Mug", V((-0.1, 0.5, 0.15)), col=COL_PROPS, parent=dan["tiltRight"])
_mb = rcyl("MugBody", 0.3, 0.62, V((0, 0, 0)), mugm, mug, bevel=0.0)
import bmesh as _bm
_b = _bm.new(); _b.from_mesh(_mb.data)
_bm.ops.delete(_b, geom=[f for f in _b.faces if f.normal.z > 0.99 and f.calc_center_median().z > 0.3], context="FACES_ONLY")
_b.to_mesh(_mb.data); _b.free()
_sol = _mb.modifiers.new("Wall", "SOLIDIFY"); _sol.thickness = 0.045; _sol.offset = -1; _sol.use_even_offset = True
_bev = _mb.modifiers.new("RimRound", "BEVEL"); _bev.width = 0.012; _bev.segments = 2; _bev.limit_method = "ANGLE"
rcyl("Coffee", 0.252, 0.02, V((0, 0, 0.16)), pmat("Coffee", (60, 34, 20), rough=0.15), mug, bevel=0.0)
tube("MugHandle", [(0.28, 0, 0.18), (0.48, 0, 0.12), (0.48, 0, -0.12), (0.28, 0, -0.18)], 0.06, mugm, mug)
mug.rotation_euler = (0, 0, R(-90))           # handle toward the hand

# ================================================================== SHOT A: Milo outro (0 - 6.75 s)
T = lambda t: FA(LEAD + t)          # audio time -> frame
m, mc, mn, mh = milo["root"], milo["chest"], milo["neck"], milo["head"]
mR, mL = "Right", "Left"
# face: expression beats that follow the line, plus syllable accents
expr(fm, 1, "curious"); expr(fm, T(0.05), "curious"); expr(fm, T(1.05), "question"); expr(fm, T(1.6), "question")
expr(fm, T(1.85), "excited"); expr(fm, T(3.3), "excited")
expr(fm, T(3.5), "lean_in"); expr(fm, T(4.4), "lean_in"); expr(fm, T(4.85), "ominous"); expr(fm, T(5.85), "ominous")
expr(fm, T(6.15), "sly"); expr(fm, FA(A_LEN) - 1, "sly")
sparkle(fm, T(2.55), T(3.4))
blink(fm, T(0.75)); blink(fm, T(3.45)); blink(fm, T(5.95))
mouth(fm, 1, "rest_smile")
lipsync(fm, 2, T(6.0), [(1, "rest_smile", "calm"), (T(0.0), "rest_smirk", "calm"), (T(1.85), "rest_smile", "excited"),
                        (T(3.45), "rest_flat", "calm"), (T(4.8), "rest_flat", "whisper")])
mouth(fm, T(6.1), "rest_creepy")
hits_m = accents(milo, fm, T(0.0), T(3.35), nod=5.0)
# body: idle sway, a thumb back at the closet, hype on FOLLOW/LIKE/PART 2, lean in for the warning
for fr in range(1, B0, 12):
    kf(m, "location", fr, 0.02 * math.sin(fr / FPS * 2.2), index=2)
for t, (x, y, z) in ((-0.25, (0, 0, 0)), (0.3, (-3, 0, 9)), (0.9, (-2, 0, 11)), (1.3, (-5, -10, 22)), (1.6, (0, -6, 10)),
                     (1.95, (4, 0, 0)), (2.3, (-3, 0, -4)), (2.7, (-1, 0, 3)), (3.05, (-6, 0, 0)), (3.3, (0, 0, 0)),
                     (3.6, (6, 0, 0)), (4.4, (9, 0, 4)), (5.0, (12, 0, 0)), (5.8, (12, 0, -2)), (6.2, (10, -4, 8)), (6.5, (10, -4, 8))):
    kf(mn, "rotation_euler", T(t), tuple(R(v) for v in (x, y, z)))
for t, lean, twist in ((-0.25, 0, 0), (0.6, -2, 6), (1.3, -3, 12), (1.8, 2, 0), (2.0, -4, 0), (2.25, 3, 0),
                       (3.3, 0, 0), (3.7, -10, 0), (4.4, -13, 0), (5.0, -15, 0), (6.5, -15, 3)):
    kf(mc, "rotation_euler", T(t), (R(lean), 0, R(twist)))
for t, fwd in ((-0.25, 0), (3.4, 0), (4.4, 0.9), (5.2, 1.3), (6.5, 1.35)):
    kf(m, "location", T(t), fwd, index=1)
# right arm: thumb over the shoulder at "closet" (1.2 s), pump on FOLLOW (smear), point at viewer on PART 2
arm(milo, mR, 1, euler=(4, 6))
arm(milo, mR, T(0.85), euler=(10, 8)); arm(milo, mR, T(1.15), euler=(150, -60)); arm(milo, mR, T(1.25), euler=(140, -55))
arm(milo, mR, T(1.6), euler=(135, -50)); arm(milo, mR, T(1.85), euler=(30, 10))
arm(milo, mR, T(1.98), euler=(-10, 5)); arm(milo, mR, T(2.12), euler=(172, 4)); arm(milo, mR, T(2.25), euler=(160, 4))   # pump
arm(milo, mR, T(2.45), euler=(165, 4)); arm(milo, mR, T(2.6), euler=(88, -6)); arm(milo, mR, T(2.7), euler=(96, -6))   # point
arm(milo, mR, T(3.25), euler=(92, -6)); arm(milo, mR, T(3.6), euler=(8, 4)); arm(milo, mR, T(6.5), euler=(6, 4))
arm(milo, mL, 1, euler=(4, -6)); arm(milo, mL, T(1.85), euler=(6, -8))
arm(milo, mL, T(1.98), euler=(-10, -5)); arm(milo, mL, T(2.12), euler=(172, -4)); arm(milo, mL, T(2.25), euler=(160, -4))
arm(milo, mL, T(2.5), euler=(150, -4)); arm(milo, mL, T(2.7), euler=(20, -8)); arm(milo, mL, T(3.6), euler=(6, -6))
arm(milo, mL, T(6.5), euler=(5, -6))
for side in (mR, mL):                                   # smear: arms stretch for the fastest frame of the pump
    sh = milo[side]
    kf(sh, "scale", T(1.98), (1, 1, 1)); kf(sh, "scale", T(2.06), (1, 1, 1.32)); kf(sh, "scale", T(2.16), (1, 1, 1))
for t, z in ((1.9, 0.0), (2.02, -0.12), (2.15, 0.42), (2.3, 0.0), (2.36, -0.08), (2.45, 0.0)):   # hop on FOLLOW
    kf(m, "location", T(t), z, index=2)
# lighting mood shift for the warning: room dims, closet glow creeps under the door
kf(mkey.data, "energy", T(3.4), 1500); kf(mkey.data, "energy", T(4.8), 650)
kf(mfill.data, "energy", T(3.4), 500); kf(mfill.data, "energy", T(4.8), 160)
kf(glow_l.data, "energy", T(3.6), 0); kf(glow_l.data, "energy", T(5.0), 160)
kf(strip, "scale", 1, (1, 0, 0)); kf(strip, "scale", T(3.6), (1, 0, 0)); kf(strip, "scale", T(4.6), (1, 1, 1))
ro = light("M_DoorSpill", (MX + 5.5, -4.5, 4.5), 0, size=3, col=(1.0, 0.35, 0.1), target=(MX, 0.5, 4.4))
kf(ro.data, "energy", 1, 0); kf(ro.data, "energy", T(3.7), 0); kf(ro.data, "energy", T(5.1), 1800)

# ================================================================== SHOT B: coffee + newspaper (8 s)
d, dc, dn, dh = dan["root"], dan["chest"], dan["neck"], dan["head"]
X0, X1, WY = 5.0, -3.0, 0.6
WY0 = -1.2
kf(d, "location", 1, (X0, WY0, 0)); kf(d, "location", FB(0.0), (X0, WY0, 0))
kf(d, "rotation_euler", 1, (0, 0, 0)); kf(d, "rotation_euler", FB(0.0), (0, 0, 0))
CHEST_MUG = (0.85, 0.75, 2.7)
SIP = (0.2, 0.75, 3.7)                 # rim on the mouth, mug in front of the face (searched, no clipping)
# --- sip (0 - 1.75)
arm(dan, "Right", FB(0.0), CHEST_MUG); arm(dan, "Right", FB(0.3), CHEST_MUG); arm(dan, "Right", FB(0.42), (0.9, 0.75, 2.55))
arm(dan, "Right", FB(0.8), SIP); arm(dan, "Right", FB(1.4), SIP); arm(dan, "Right", FB(1.75), CHEST_MUG)
tr = dan["tiltRight"]
for t, a in ((0.0, 0), (0.55, 0), (0.85, 22), (1.3, 26), (1.5, 0)):
    kf(tr, "rotation_euler", FB(t), (R(a), 0, 0))
arm(dan, "Left", FB(0.0), euler=(3, -4)); arm(dan, "Left", FB(1.9), euler=(3, -4))
for t, x in ((0.0, 0), (0.5, 0), (0.85, -14), (1.35, -16), (1.65, 2), (1.8, 0)):
    kf(dn, "rotation_euler", FB(t), (R(x), 0, 0))
expr(fd, 1, "neutral"); expr(fd, FB(0.0), "neutral"); expr(fd, FB(0.6), "content"); expr(fd, FB(1.8), "content")
eyes_closed(fd, FB(0.75), FB(1.45))
mouth(fd, 1, "rest_flat"); mouth(fd, FB(0.6), "small_o"); mouth(fd, FB(1.45), "O"); mouth(fd, FB(1.72), "rest_smile")
for t, lean in ((0.0, 0), (0.8, 4), (1.4, 4), (1.75, 0)):
    kf(dc, "rotation_euler", FB(t), (R(-lean), 0, 0))
# --- turn and walk to the table (1.75 - 4.15)
W0, W1 = 2.05, 4.15
kf(d, "rotation_euler", FB(1.75), (0, 0, 0)); kf(d, "rotation_euler", FB(1.88), (0, 0, R(-8)))
kf(d, "rotation_euler", FB(2.15), (0, 0, R(78)))
kf(dc, "rotation_euler", FB(1.88), (R(4), 0, 0)); kf(dc, "rotation_euler", FB(2.1), (R(-6), 0, 0))
STEPS = 4; A_LEG = R(30)
step_times = []
nW = FB(W1) - FB(W0)
prev_phase = 0
for i in range(nW + 1):
    fr = FB(W0) + i; u = i / nW
    e = u * u * (3 - 2 * u)
    ph = STEPS * e
    ramp = min(1.0, u / 0.12, (1 - u) / 0.12) if 0 < u < 1 else 0.0
    ang = A_LEG * math.sin(math.pi * ph) * ramp
    x = X0 + (X1 - X0) * e
    kf(d, "location", fr, (x, WY0 + (WY - WY0) * e, 0.07 * (math.cos(2 * math.pi * ph) - 1) * -0.5 * ramp + 0.0))
    kf(dan["hipL"], "rotation_euler", fr, (ang, 0, 0)); kf(dan["hipR"], "rotation_euler", fr, (-ang, 0, 0))
    arm(dan, "Left", fr, euler=(-math.degrees(ang) * 0.8 + 3, -4))
    kf(dc, "rotation_euler", fr, (R(-6) * ramp, 0, -ang * 0.15))
    if math.floor(ph + 0.5) != math.floor(prev_phase + 0.5) and 0 < ph < STEPS: step_times.append((fr - B0) / FPS)
    prev_phase = ph
arm(dan, "Right", FB(W0), CHEST_MUG); arm(dan, "Right", FB(W1), CHEST_MUG)
expr(fd, FB(2.0), "neutral"); expr(fd, FB(4.2), "neutral")
mouth(fd, FB(2.3), "rest_flat")
blink(fd, FB(2.6)); blink(fd, FB(3.9))
# --- stop, face camera, notice the paper (4.15 - 4.8)
kf(dc, "rotation_euler", FB(4.15), (R(-6), 0, 0)); kf(dc, "rotation_euler", FB(4.3), (R(-11), 0, 0)); kf(dc, "rotation_euler", FB(4.5), (R(-2), 0, 0))
kf(d, "rotation_euler", FB(4.2), (0, 0, R(78))); kf(d, "rotation_euler", FB(4.55), (0, 0, R(-6))); kf(d, "rotation_euler", FB(4.7), (0, 0, R(0)))
kf(d, "location", FB(4.15), (X1, WY, 0)); kf(d, "location", FB(8.0), (X1, WY, 0))
for h in ("hipL", "hipR"):
    kf(dan[h], "rotation_euler", FB(4.3), (0, 0, 0)); kf(dan[h], "rotation_euler", FB(8.0), (0, 0, 0))
for t, (x, z) in ((2.0, (0, 0)), (4.5, (0, 0)), (4.75, (16, 32)), (4.95, (14, 28)), (5.15, (18, 26)), (5.45, (12, 4)),
                  (5.6, (14, 0)), (6.0, (14, 0)), (6.1, (14, 7)), (6.2, (14, -7)), (6.3, (13, 0)), (6.5, (4, -10)),
                  (6.7, (-6, 18)), (7.1, (-4, 30)), (7.45, (-2, 26)), (7.65, (0, 0)), (8.0, (-4, 0))):
    kf(dn, "rotation_euler", FB(t), (R(x), 0, R(z)))
expr(fd, FB(4.6), "notice"); expr(fd, FB(4.95), "notice")
arm(dan, "Left", FB(4.3), euler=(3, -4)); arm(dan, "Left", FB(4.75), euler=(-6, -10))
# --- reach + grab (4.8 - 5.1)
pt = pap_table.location; dl = V((X1, WY, 0))
grab_body = V((pt.x - dl.x, pt.y - dl.y, 2.62))
GRAB_FR = FB(5.12)
arm(dan, "Left", FB(5.1), grab_body + V((0.0, 0.0, -0.1))); arm(dan, "Left", GRAB_FR + 1, grab_body + V((0.0, 0.0, -0.05)))
kf(dc, "rotation_euler", FB(4.8), (R(-2), 0, 0)); kf(dc, "rotation_euler", FB(5.1), (R(-3), 0, R(4)))
kf(dc, "rotation_euler", FB(5.45), (R(0), 0, 0))
vis([pap_table] + list(pap_table.children), 1, True); vis([pap_table] + list(pap_table.children), GRAB_FR, False)
hand_objs = list(pap_hand.children)
vis(hand_objs, 1, False); vis(hand_objs, GRAB_FR, True)
tl = dan["tiltLeft"]
kf(pap_hand, "location", 1, (-0.039, -0.12, -0.145)); kf(pap_hand, "location", GRAB_FR, (-0.039, -0.12, -0.145))
kf(tl, "rotation_euler", GRAB_FR, (R(90), 0, R(-15))); kf(tl, "rotation_euler", FB(5.55), (0, 0, 0))
# --- lift and read (5.1 - 6.25)
READ = (-0.9, 1.45, 3.6)
arm(dan, "Left", FB(5.55), READ); arm(dan, "Left", FB(6.2), READ)
kf(pap_hand, "location", FB(5.55), (0.35, 0.62, 0.3))
expr(fd, FB(5.6), "reading"); expr(fd, FB(5.85), "reading"); expr(fd, FB(6.05), "annoyed"); expr(fd, FB(6.3), "annoyed")
mouth(fd, FB(5.7), "rest_flat"); mouth(fd, FB(6.0), "rest_frown")
# --- wind-up, throw (smear), follow-through (6.25 - 7.2)
WIND = (-1.9, -1.0, 4.7); REL = (-2.9, 0.4, 4.6); FOLLOW = (-2.6, 0.9, 2.6)
arm(dan, "Left", FB(6.45), WIND); arm(dan, "Left", FB(6.55), WIND)
arm(dan, "Left", FB(6.66), REL, interp="LINEAR"); arm(dan, "Left", FB(6.8), FOLLOW); arm(dan, "Left", FB(7.2), euler=(4, -6))
kf(dan["Left"], "scale", FB(6.55), (1, 1, 1)); kf(dan["Left"], "scale", FB(6.62), (1, 1, 1.38)); kf(dan["Left"], "scale", FB(6.72), (1, 1, 1))
kf(dc, "rotation_euler", FB(6.3), (0, 0, 0)); kf(dc, "rotation_euler", FB(6.55), (R(4), 0, R(16)))
kf(dc, "rotation_euler", FB(6.7), (R(-6), 0, R(-14))); kf(dc, "rotation_euler", FB(6.95), (R(-2), 0, R(-6))); kf(dc, "rotation_euler", FB(7.3), (0, 0, 0))
expr(fd, FB(6.4), "effort"); expr(fd, FB(6.7), "effort"); expr(fd, FB(7.1), "smug"); expr(fd, FB(8.0), "smug")
mouth(fd, FB(6.4), "teeth"); mouth(fd, FB(6.85), "rest_flat"); mouth(fd, FB(7.4), "rest_smirk")
blink(fd, FB(7.05))
REL_FR = FB(6.64)
vis(hand_objs, REL_FR, False)
fly_objs = list(pap_fly.children)
vis(fly_objs, 1, False); vis(fly_objs, REL_FR, True)
apply_interp()
s.frame_set(REL_FR)
start = pap_hand.matrix_world.copy()
loc0 = start.translation.copy(); rot0 = start.to_euler()
LAND = BIN + V((0, 0, 2.3))
fly_t1 = 7.42
nfly = FB(fly_t1) - REL_FR
for i in range(nfly + 1):
    u = i / nfly; fr = REL_FR + i
    p = loc0.lerp(LAND, u) + V((0, 0, 2.2 * 4 * u * (1 - u)))
    kf(pap_fly, "location", fr, p)
    kf(pap_fly, "rotation_euler", fr, (rot0.x + R(150) * u, rot0.y + R(50) * u, rot0.z + R(120) * u))
    sc = 1.0 - 0.4 * u
    kf(pap_fly, "scale", fr, (sc, sc, sc))
kf(pap_fly, "location", FB(7.55), BIN + V((0, 0, 1.2)))
vis(fly_objs, FB(7.55), False)
# --- smug sip at the end (7.5 - 8.0)
arm(dan, "Right", FB(7.45), CHEST_MUG); arm(dan, "Right", FB(7.92), SIP); arm(dan, "Right", FB(8.0), SIP)
kf(tr, "rotation_euler", FB(7.6), (0, 0, 0)); kf(tr, "rotation_euler", FB(7.95), (R(25), 0, 0))
eyes_closed(fd, FB(7.85), FB(8.2))
for fr in range(FB(4.7), FB(8.0), 12):
    kf(d, "location", fr, 0.018 * math.sin(fr / FPS * 2.0), index=2)

# ================================================================== cameras (cut A -> B)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4; cam.data.sensor_width = 36


_PREV_E = [None]


def cam_key(fr, pos, tgt, lens, focus=None, interp="BEZIER"):
    pos = V(pos); tgt = V(tgt)
    kf(cam, "location", fr, pos, interp=interp)
    e = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    if _PREV_E[0] is not None: e.make_compatible(_PREV_E[0])      # no 360-degree spins between keys
    _PREV_E[0] = e.copy()
    kf(cam, "rotation_euler", fr, e, interp=interp)
    kf(cam.data, "lens", fr, lens, interp=interp)
    cam.data.dof.focus_distance = focus or (tgt - pos).length
    cam.data.keyframe_insert("dof.focus_distance", frame=fr); _LOG.append((cam.data, "dof.focus_distance", fr, interp))


MC = lambda x, y, z: (MX + x, y, z)
cam_key(1, MC(1.8, 11.5, 4.2), MC(0.2, 0, 3.7), 42)
cam_key(T(1.6), MC(1.5, 10.6, 4.3), MC(0.2, 0, 3.8), 44)
cam_key(T(1.95), MC(1.2, 8.4, 4.5), MC(0.1, 0, 4.0), 48)                 # punch-in on FOLLOW
cam_key(T(3.3), MC(1.0, 8.0, 4.5), MC(0.1, 0, 4.1), 48)
cam_key(T(4.6), MC(0.6, 6.3, 4.7), MC(0.2, 0.9, 4.35), 52)               # creep in for the warning
cam_key(T(6.0), MC(0.45, 6.4, 4.7), MC(0.25, 1.1, 4.45), 50)
cam_key(B0 - 1, MC(0.42, 6.2, 4.7), MC(0.25, 1.1, 4.46), 50, interp="CONSTANT")
cam_key(B0, (X0 - 1.0, 11.5, 4.9), (X0, 0, 3.7), 40, interp="CONSTANT")   # hard cut
cam_key(B0 + 1, (X0 - 1.0, 11.5, 4.9), (X0, 0, 3.7), 40)
cam_key(FB(1.6), (X0 - 0.7, 10.2, 4.8), (X0, 0, 3.8), 43)
cam_key(FB(2.3), (X0 - 4.0, 12.0, 4.8), (X0 - 0.8, 0, 3.4), 38)
cam_key(FB(3.3), (-2.8, 12.3, 4.7), (0.2, 0, 3.3), 38)
cam_key(FB(4.4), (-4.0, 11.6, 4.6), (-4.4, 0, 3.4), 40)
cam_key(FB(5.5), (-3.6, 9.6, 4.6), (-3.6, 0, 3.7), 43)
cam_key(FB(6.45), (-3.7, 9.4, 4.6), (-3.8, 0, 3.8), 43)
cam_key(FB(7.0), (-5.0, 11.2, 5.0), (-7.6, -1.0, 3.0), 38)               # follow the paper to the bin
cam_key(FB(7.45), (-5.4, 11.4, 5.0), (-8.3, -1.2, 2.6), 38)
cam_key(FB(7.75), (-4.0, 10.0, 4.7), (-3.4, 0, 3.8), 42)
cam_key(NF, (-3.8, 9.4, 4.7), (-3.2, 0, 3.9), 43)
apply_interp()

# ================================================================== checks (fail loudly instead of rendering a broken face)
def check_faces():
    probs = []
    for nm_, rig, (f0, f1) in (("Milo", fm, (1, B0 - 1)), ("Dan", fd, (B0, NF))):
        curves = {}
        for k, objs in rig["mouths"].items():
            o = objs[0]
            fc = [c for c in _fcurves(o) if c.data_path == "hide_render"]
            curves[k] = fc[0] if fc else None
        for fr in range(f0, f1 + 1):
            on = [k for k, c in curves.items() if c is not None and c.evaluate(fr) < 0.5]
            if len(on) != 1: probs.append((nm_, fr, on))
    return probs


probs = check_faces()
for rig_, cut in ((fm, B0),):
    for side in ("L", "R"):
        fc = [c for c in _fcurves(rig_["blink" + side]) if c.data_path == "scale" and c.array_index == 2]
        if fc and any(fc[0].evaluate(f) < 0.9 for f in range(cut - 6, cut)): probs.append(("eyes closed before cut", cut))
print("FACE CHECK", "OK" if not probs else probs[:20])
json.dump({"steps": step_times, "sip": [0.8, 1.4], "sip2": 7.92, "grab": 5.12, "read_shake": 6.1, "throw": 6.62, "bin": 7.42},
          open("/home/claude/talk/timing2.json", "w"))

# ================================================================== render settings
eng = os.environ.get("ENGINE", "CPU")
if eng == "GPU":
    pr = bpy.context.preferences.addons["cycles"].preferences
    for be in ("OPTIX", "CUDA"):
        try:
            pr.compute_device_type = be; pr.get_devices()
            gpus = [x for x in pr.devices if x.type == be]
            if gpus:
                for x in pr.devices: x.use = x.type == be
                print("GPU BACKEND", be, [x.name for x in gpus]); break
        except Exception as e: print("backend fail", be, e)
    s.cycles.device = "GPU"; s.cycles.samples = 32
else:
    s.cycles.device = "CPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 6))
s.render.engine = "CYCLES"; s.cycles.use_denoising = True
s.render.use_persistent_data = True
s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5; s.render.motion_blur_position = "START"
s.render.resolution_x, s.render.resolution_y = int(os.environ.get("RX", 216)), int(os.environ.get("RY", 384))
s.render.image_settings.file_format = "PNG"
s.render.filepath = OUT + "/"
s.frame_start = int(os.environ.get("FS", 1)); s.frame_end = int(os.environ.get("FE", NF))
s.render.use_overwrite = False; s.render.use_placeholder = True
if probs and not os.environ.get("FORCE"):
    raise SystemExit("face check failed - not rendering")
if os.environ.get("RENDER"):
    if os.environ.get("FRAMES"):
        for fr in [int(x) for x in os.environ["FRAMES"].split(",")]:
            s.frame_set(fr); s.render.filepath = OUT + "/%04d.png" % fr; bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
print("DONE", NF)
