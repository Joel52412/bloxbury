# talktest.py - lip-sync + expression + fluid motion test (Rae v2 then Milo v2)
import bpy, math, random, os, json
from mathutils import Vector
LIB = "/home/claude/studio_library/engine/"
src = open('/home/claude/bloxbury-blender/bloxbury_part1.py').read()
exec(src[:src.index('# Milo starts at the fence')])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for f in ("charlib", "stylelab", "hair2", "hair3", "faces2", "garments", "garments2", "hair4", "faces3", "faces4", "props"):
    exec(open(LIB + f + ".py").read())
V = Vector
OUT = os.environ.get("OUT", "/home/claude/talk/frames")
os.makedirs(OUT, exist_ok=True)
ENV = json.load(open("/home/claude/talk/env.json"))
FPS = 30
NF = len(ENV["rms"])
s = bpy.context.scene
s.frame_start, s.frame_end = 1, NF
s.render.fps = FPS

# ------------------------------------------------------------------ keyframe helper (explicit interpolation)
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
    for o in objs:
        kf(o, "hide_render", frame, not on, interp="CONSTANT")


# ------------------------------------------------------------------ characters (library parts)
def make_rae():
    S = new_set(); skin = (160, 105, 78); rng = RNG(41)
    d_hoodie(S, (122, 84, 170), rng, skin)
    b_trousers(S, (34, 34, 44), rng, kind="jeans")
    s_shoes(S, "trainers", (205, 170, 240), rng)
    finish(S, rng)
    P = build_body("Rae", skin, S)
    add_hair3(P, "H3", random.Random(5), colour=(28, 20, 20))
    hat_headphones(P["neck"], P["M"], (236, 84, 150))
    return P


def make_milo():
    S = new_set(); skin = (234, 184, 146); rng = RNG(42)
    d_hoodie(S, (226, 156, 32), rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2   # keyhole logo
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


# ------------------------------------------------------------------ face rig: eye sets + mouth shapes (M2 style)
def build_face_rig(P):
    global FACE_SKIN
    FACE_SKIN = P["skin"]
    neck = P["neck"]
    W, H = 0.12, 0.18
    eyes, mouths, sparkles = {}, {}, []

    def mk(store, key, fn):
        f = Face(neck, key); fn(f); store[key] = f.objs

    def plain(f, h=H, z=0.08, look=0.0, shine=True):
        for sx in (-0.19, 0.19):
            f.oval(sx + look, z, W, h, M_INK)
            if shine: f.oval(sx + look + W * 0.24, z + h * 0.26, W * 0.34, h * 0.24, M_SHINE70, lift=0.008)

    E = {
        "neutral": lambda f: (plain(f), brows(f, [(-0.28, 0.23), (-0.1, 0.24)], [(0.1, 0.24), (0.28, 0.23)], rad=0.022)),
        "happy": lambda f: (plain(f), brows(f, [(-0.28, 0.25), (-0.1, 0.28)], [(0.1, 0.28), (0.28, 0.25)], rad=0.022)),
        "serious": lambda f: (plain(f, h=H * 0.8, z=0.07), [f.line([(sx - 0.075, 0.115), (sx + 0.075, 0.12)], M_INK, r=0.024, lift=0.012) for sx in (-0.19, 0.19)],
                              brows(f, [(-0.29, 0.19), (-0.1, 0.17)], [(0.1, 0.17), (0.29, 0.19)], rad=0.026)),
        "determined": lambda f: (plain(f, h=H * 0.9, z=0.07), brows(f, [(-0.29, 0.22), (-0.1, 0.18)], [(0.1, 0.18), (0.29, 0.22)], rad=0.028)),
        "angry": lambda f: (plain(f, h=H * 0.78, z=0.06), brows(f, [(-0.31, 0.24), (-0.08, 0.14)], [(0.08, 0.14), (0.31, 0.24)], rad=0.034, lift=0.012)),
        "smug": lambda f: ([(f.oval(sx, 0.06, W, H * 0.62, M_INK), f.line([(sx - 0.075, 0.1), (sx + 0.075, 0.105)], M_INK, r=0.026))
                            for sx in (-0.19, 0.19)], brows(f, [(-0.28, 0.2), (-0.1, 0.2)], [(0.1, 0.23), (0.28, 0.28)], rad=0.022)),
        "shocked": lambda f: ([(f.oval(sx, 0.08, 0.17, 0.21, M_EYEWHITE), f.oval(sx, 0.08, 0.075, 0.095, M_INK, lift=0.008)) for sx in (-0.19, 0.19)],
                              brows(f, [(-0.28, 0.3), (-0.1, 0.33)], [(0.1, 0.33), (0.28, 0.3)], rad=0.022)),
        "blink": lambda f: ([f.line([(sx - 0.075, 0.07), (sx, 0.04), (sx + 0.075, 0.07)], M_INK, r=0.024) for sx in (-0.19, 0.19)],
                            brows(f, [(-0.28, 0.22), (-0.1, 0.23)], [(0.1, 0.23), (0.28, 0.22)], rad=0.022)),
    }
    for k, fn in E.items(): mk(eyes, k, fn)

    def sparkle_eyes(f):
        for sx in (-0.19, 0.19):
            f.oval(sx, 0.07, 0.2, 0.26, M_INK)
            f.oval(sx - 0.05, 0.0, 0.04, 0.04, M_EYEWHITE, lift=0.012)
        brows(f, [(-0.28, 0.3), (-0.1, 0.33)], [(0.1, 0.33), (0.28, 0.3)], rad=0.022)
    mk(eyes, "sparkle", sparkle_eyes)
    # animated sparkle stars (own objects so they can twinkle): an empty per star, parented to the neck
    for sx, z, sz, m in ((-0.16, 0.1, 0.055, M_EYEWHITE), (0.22, 0.1, 0.055, M_EYEWHITE),
                         (-0.42, 0.34, 0.04, M_GOLD), (0.44, 0.3, 0.035, M_GOLD), (0.4, -0.12, 0.03, M_GOLD)):
        piv = empty("Spark", V((sx, surf_y(max(-0.59, min(0.59, sx))) + 0.03, z + 0.6)), col=COL_CHARS, parent=neck)
        f = Face(piv, "spk"); f.neck = piv
        a = tube("SpkH", [(-sz, 0, 0), (sz, 0, 0)], 0.012, m, piv); b = tube("SpkV", [(0, 0, -sz * 1.2), (0, 0, sz * 1.2)], 0.012, m, piv)
        c = ball("SpkC", (sz * 0.5, 0.02, sz * 0.5), V((0, 0, 0)), m, piv)
        sparkles.append((piv, [a, b, c]))
        eyes["sparkle"] += [a, b, c]

    # mouth shapes
    M = {
        "rest_smile": lambda f: f.line([(-0.13, -0.15), (-0.05, -0.2), (0.05, -0.2), (0.13, -0.15)], M_INK, r=0.024),
        "rest_flat": lambda f: f.line([(-0.1, -0.19), (0.1, -0.19)], M_INK, r=0.022),
        "rest_frown": lambda f: f.line([(-0.11, -0.21), (0, -0.175), (0.11, -0.21)], M_INK, r=0.022),
        "rest_smirk": lambda f: f.line([(-0.1, -0.18), (0.04, -0.19), (0.15, -0.13)], M_INK, r=0.022),
        "M": lambda f: f.line([(-0.09, -0.19), (0.09, -0.19)], M_INK, r=0.03),
        "half": lambda f: (f.oval(0, -0.19, 0.16, 0.075, M_INK), f.oval(0, -0.205, 0.08, 0.03, M_TONGUE, lift=0.008)),
        "A": lambda f: (f.oval(0, -0.19, 0.21, 0.16, M_INK), f.oval(0, -0.23, 0.12, 0.05, M_TONGUE, lift=0.008),
                        f.oval(0, -0.13, 0.15, 0.03, M_EYEWHITE, lift=0.008)),
        "E": lambda f: (f.oval(0, -0.185, 0.26, 0.085, M_INK), f.oval(0, -0.17, 0.2, 0.03, M_EYEWHITE, lift=0.008)),
        "O": lambda f: (f.oval(0, -0.2, 0.12, 0.14, M_INK), f.oval(0, -0.235, 0.07, 0.04, M_TONGUE, lift=0.008)),
        "grin_open": lambda f: (f.oval(0, -0.18, 0.3, 0.17, M_INK), f.oval(0, -0.12, 0.24, 0.04, M_EYEWHITE, lift=0.008),
                                f.oval(0, -0.23, 0.14, 0.05, M_TONGUE, lift=0.008)),
        "teeth": lambda f: (f.oval(0, -0.19, 0.3, 0.1, M_INK), f.oval(0, -0.19, 0.25, 0.055, M_EYEWHITE, lift=0.008),
                            f.line([(-0.12, -0.19), (0.12, -0.19)], M_INK, r=0.006, lift=0.012)),
    }
    for k, fn in M.items(): mk(mouths, k, fn)
    return eyes, mouths, sparkles


def drive_face(rig, segs, f0, f1, blinks=()):
    """segs: list of (frame_start, eyes_key, rest_mouth, talk_style). Lip-sync from audio loudness."""
    eyes, mouths, sparkles = rig
    rms, cen = ENV["rms"], ENV["cen"]
    peak = max(rms[f0 - 1:f1]) or 1
    cur_e = cur_m = None; hold = 0; last_open = "A"
    for fr in range(f0, f1 + 1):
        seg = [sg for sg in segs if sg[0] <= fr][-1]
        e_key = "blink" if any(b <= fr < b + 4 for b in blinks) and seg[1] not in ("sparkle", "shocked") else seg[1]
        lvl = rms[fr - 1] / peak if fr - 1 < len(rms) else 0
        style = seg[3]
        if lvl < 0.12: m_key = seg[2]
        elif lvl < 0.38: m_key = "M" if (fr // 3) % 4 == 3 else "half"
        else:
            if style == "angry": m_key = "teeth"
            elif style == "excited": m_key = "grin_open" if cen[fr - 1] > 1500 else "O"
            else: m_key = ("E" if cen[fr - 1] > 1800 else "A") if (fr // 2) % 3 else "O"
        if hold > 0 and m_key != cur_m and not (cur_m or "").startswith("rest"): hold -= 1; m_key = cur_m
        if e_key != cur_e:
            if cur_e: vis(eyes[cur_e], fr, False)
            vis(eyes[e_key], fr, True); cur_e = e_key
        if m_key != cur_m:
            if cur_m: vis(mouths[cur_m], fr, False)
            vis(mouths[m_key], fr, True); cur_m = m_key; hold = 1
    for k, objs in list(eyes.items()) + list(mouths.items()):   # hidden before/after
        if k != cur_e and k != cur_m: pass
    vis(eyes[cur_e], f1 + 1, False); vis(mouths[cur_m], f1 + 1, False)
    # sparkle twinkle (subtle): scale breathing + gentle spin, little gold pops staggered
    for i, (piv, objs) in enumerate(sparkles):
        for fr in range(f0, f1 + 1, 3):
            t = fr / FPS
            if i < 2: sc = 0.85 + 0.25 * (0.5 + 0.5 * math.sin(t * 9 + i * 1.7))
            else: sc = max(0.0, math.sin(t * 4.2 + i * 2.1)) ** 2 * 1.3
            kf(piv, "scale", fr, (sc, sc, sc)); kf(piv, "rotation_euler", fr, (0, math.radians((t * 60 + i * 40) % 360) * 0.3, 0))


def hide_all(rig, frame=1):
    eyes, mouths, _ = rig
    for objs in list(eyes.values()) + list(mouths.values()): vis(objs, frame, False)


# ------------------------------------------------------------------ scene
w = bpy.data.worlds.new("Room"); s.world = w
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.62, 0.66, 0.78, 1); bg.inputs[1].default_value = 0.55


def light(name, loc, energy, size=6, col=(1, 1, 1), target=(0, 0, 4)):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col
    ob = bpy.data.objects.new(name, d); s.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


light("Key", (5, 9, 8), 1500, col=(1.0, 0.93, 0.85)); light("Fill", (-7, 7, 5), 450, col=(0.8, 0.85, 1.0))
light("Rim", (-2, -8, 8), 1300, col=(0.85, 0.75, 1.0))
floor = bpy.data.objects.new("Floor", CUBE); s.collection.objects.link(floor); floor.scale = (80, 80, 0.1); floor.location = (0, 0, -0.05)
floor.material_slots[0].link = "OBJECT"; floor.material_slots[0].material = wood("FloorWood", (150, 110, 80), scale=0.6)
wall = bpy.data.objects.new("Wall", CUBE); s.collection.objects.link(wall); wall.scale = (60, 0.5, 30); wall.location = (0, -9, 15)
wall.material_slots[0].link = "OBJECT"; wall.material_slots[0].material = tex_mat("WallPaint", (120, 110, 150), "plaster")

rae = make_rae(); milo = make_milo()
rae["root"].location = (0, 0, 0); milo["root"].location = (40, 0, 0)
for o in bpy.data.objects: o.animation_data_clear()
rig_r = build_face_rig(rae); rig_m = build_face_rig(milo)
hide_all(rig_r); hide_all(rig_m)

# set dressing behind each character (library props, out of focus)
sh = bookshelf("BG_Shelf"); sh.location = (-6, -6.5, 0)
lp = floor_lamp("BG_Lamp"); lp.location = (5, -5, 0)
pl = plant("BG_Plant"); pl.location = (40 - 5, -5, 0)
cl = wall_clock("BG_Clock"); cl.location = (40 + 4, -8.4, 8)

F = lambda t: int(round(t * FPS)) + 1
R0, R1 = 1, F(6.0)          # Rae shot
M0, M1 = F(6.1), NF         # Milo shot (audio starts 6.15)

# ------------------------------------------------------------------ RAE: performance
drive_face(rig_r, [(1, "neutral", "rest_flat", "calm"), (F(0.0), "smug", "rest_smirk", "calm"), (F(0.9), "determined", "rest_flat", "calm"),
                   (F(1.9), "serious", "rest_flat", "calm"), (F(3.8), "serious", "rest_frown", "calm"), (F(5.05), "angry", "rest_frown", "angry")],
           R0, R1, blinks=(F(1.7), F(3.6)))
r, nk, rs, ls = rae["root"], rae["neck"], rae["Right"], rae["Left"]
# idle breathing on the whole body, continuous
for fr in range(R0, R1 + 1, 15):
    t = fr / FPS
    kf(r, "location", fr, 0.025 * math.sin(t * 2.1), index=2)
# head acting (overshoot + settle)
for t, (x, y, z) in ((0.0, (0, 0, 0)), (0.25, (-6, 9, 6)), (0.5, (-4, 7, 4)), (0.95, (2, 0, 0)), (1.15, (-3, -2, 0)),
                     (1.9, (-2, 0, 0)), (2.6, (-6, -3, -4)), (3.4, (-5, -3, -2)), (3.85, (0, 0, 8)), (4.15, (0, 0, -8)),
                     (4.45, (0, 0, 6)), (4.75, (0, 0, 0)), (5.02, (-4, 0, 0)), (5.15, (12, 0, 0)), (5.3, (9, 0, 0)), (6.0, (8, 0, 0))):
    kf(nk, "rotation_euler", F(t), tuple(math.radians(v) for v in (x, y, z)))
# right arm: "One rule." - raise with anticipation, overshoot, settle, drop
for t, ang, out in ((0.0, 0, 0), (0.85, -8, 0), (1.05, 125, 8), (1.18, 112, 6), (1.35, 116, 6), (1.85, 114, 6), (2.15, 20, 2), (2.35, 0, 0)):
    kf(rs, "rotation_euler", F(t), (math.radians(ang), math.radians(out), 0))
# left arm relaxed sway
for t, ang in ((0.0, 0), (2.0, 4), (4.0, -3), (6.0, 2)):
    kf(ls, "rotation_euler", F(t), (math.radians(ang), 0, math.radians(-3)))
# body: lean toward camera on the warning, snap on EVER
for t, lean, fwd in ((0.0, 0, 0), (1.9, 0, 0), (2.8, -5, 0.25), (4.9, -6, 0.3), (5.12, -11, 0.7), (5.3, -9, 0.6), (6.0, -9, 0.6)):
    kf(r, "rotation_euler", F(t), (math.radians(lean), 0, math.radians(-12)))
    kf(r, "location", F(t), fwd, index=1)

# ------------------------------------------------------------------ MILO: performance (audio at 6.15)
T0 = 6.15
drive_face(rig_m, [(M0, "happy", "rest_smile", "calm"), (F(T0 + 0.05), "happy", "rest_smile", "excited"),
                   (F(T0 + 1.0), "smug", "rest_smirk", "excited"), (F(T0 + 1.85), "sparkle", "rest_smile", "excited")],
           M0, M1, blinks=(F(T0 + 0.7),))
m, mn, mr, ml = milo["root"], milo["neck"], milo["Right"], milo["Left"]
for fr in range(M0, M1 + 1, 15):
    kf(m, "location", fr, 0.025 * math.sin(fr / FPS * 2.3), index=2)
for t, (x, y, z) in ((0, (0, 0, 0)), (0.4, (-4, -8, 0)), (1.0, (-2, -10, 4)), (1.6, (3, 0, 0)), (1.85, (-6, 0, 0)), (2.0, (4, 6, 0)),
                     (2.4, (-2, -6, 0)), (2.9, (2, 6, 0)), (3.3, (0, 0, 0)), (3.95, (-3, 4, 0))):
    kf(mn, "rotation_euler", F(T0 + t), tuple(math.radians(v) for v in (x, y, z)))
# shrug on the question, then point at the viewer on FOLLOW, bounce on PART 2
for t, a in ((0, 0), (0.35, 45), (0.5, 38), (1.5, 36), (1.8, -10), (1.95, 95), (2.08, 85), (3.2, 88), (3.6, 10)):
    kf(mr, "rotation_euler", F(T0 + t), (math.radians(a), 0, math.radians(8 if t < 1.7 else -6)))
for t, a in ((0, 0), (0.35, 45), (0.5, 38), (1.5, 36), (1.9, 5), (3.95, 0)):
    kf(ml, "rotation_euler", F(T0 + t), (math.radians(a), 0, math.radians(-8)))
for t, z in ((2.7, 0.0), (2.85, 0.35), (3.0, 0.0), (3.08, -0.05), (3.2, 0.0)):
    kf(m, "location", F(T0 + t), z, index=2)
kf(m, "rotation_euler", M0, (0, 0, math.radians(10)))

# ------------------------------------------------------------------ cameras (cut between shots), gentle push-ins + DOF
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2; cam.data.sensor_width = 36


def cam_key(fr, pos, tgt, lens, focus, interp="BEZIER"):
    kf(cam, "location", fr, V(pos), interp=interp)
    kf(cam, "rotation_euler", fr, (V(tgt) - V(pos)).to_track_quat("-Z", "Y").to_euler(), interp=interp)
    kf(cam.data, "lens", fr, lens, interp=interp)
    cam.data.dof.focus_distance = focus; cam.data.keyframe_insert("dof.focus_distance", frame=fr); _LOG.append((cam.data, "dof.focus_distance", fr, interp))


cam_key(R0, (2.2, 9.8, 4.6), (0, 0, 4.0), 50, 10.0)
cam_key(F(4.95), (1.6, 8.6, 4.55), (0, 0.3, 4.1), 52, 8.6)
cam_key(F(5.15), (0.8, 5.6, 4.6), (0, 0.6, 4.45), 55, 5.1)       # snap push-in on EVER
cam_key(R1, (0.75, 5.3, 4.6), (0, 0.6, 4.45), 55, 4.8, interp="CONSTANT")
cam_key(M0, (40 - 2.0, 9.0, 4.4), (40, 0, 3.9), 48, 9.2, interp="CONSTANT")   # hard cut
cam_key(M0 + 1, (40 - 2.0, 9.0, 4.4), (40, 0, 3.9), 48, 9.2)
cam_key(F(T0 + 1.85), (40 - 1.4, 7.6, 4.5), (40, 0, 4.1), 52, 7.6)
cam_key(M1, (40 - 1.0, 6.6, 4.6), (40, 0, 4.3), 54, 6.6)
for fr in range(F(5.15), F(5.5)):   # tiny shake on EVER
    a = (F(5.5) - fr) / 10
    base = V((0.8, 5.6, 4.6)).lerp(V((0.75, 5.3, 4.6)), (fr - F(5.15)) / (R1 - F(5.15)))
    kf(cam, "location", fr, base + V((random.uniform(-1, 1) * 0.03 * a, 0, random.uniform(-1, 1) * 0.03 * a)))
apply_interp()

# ------------------------------------------------------------------ render settings
eng = os.environ.get("ENGINE", "EEVEE")
if eng == "GPU":
    pr = bpy.context.preferences.addons["cycles"].preferences
    for be in ("OPTIX", "CUDA"):
        try:
            pr.compute_device_type = be; pr.get_devices()
            gpus = [d for d in pr.devices if d.type == be]
            if gpus:
                for d in pr.devices: d.use = d.type == be
                print("GPU BACKEND", be, [d.name for d in gpus]); break
        except Exception as e: print("backend fail", be, e)
    s.render.engine = "CYCLES"; s.cycles.device = "GPU"; s.cycles.samples = 32; s.cycles.use_denoising = True
    s.render.use_persistent_data = True
elif eng == "EEVEE":
    s.render.engine = "BLENDER_EEVEE"; s.eevee.taa_render_samples = 16
else:
    s.render.engine = "CYCLES"; s.cycles.samples = 10; s.cycles.use_denoising = True; s.cycles.device = "CPU"
s.render.resolution_x, s.render.resolution_y = int(os.environ.get("RX", 540)), int(os.environ.get("RY", 960))
s.render.image_settings.file_format = "PNG"
s.render.filepath = OUT + "/"
s.frame_start = int(os.environ.get("FS", 1)); s.frame_end = int(os.environ.get("FE", NF))
s.render.use_overwrite = False; s.render.use_placeholder = True
if os.environ.get("RENDER"):
    bpy.ops.render.render(animation=True)
print("DONE", NF)
