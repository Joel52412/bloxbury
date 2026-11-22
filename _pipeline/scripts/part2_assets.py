# part2_assets.py - Part 2 "She Came Home": FULL ASSET SHEET (stills for Joel to approve before any pod).
# Builds the new Part 2 assets (Mum card, kitchen, hallway mirror, Rae porch, list, bracelet, toaster) + recurring cast.
# Run: SHOTS=all RX=540 RY=960 SAMPLES=24 python3 part2_assets.py  -> /home/claude/talk/p2_assets/*.png
import bpy, math, random, os, json
from mathutils import Vector, Matrix
SCR = "/home/claude/bloxbury-blender/"
LIB = "/home/claude/studio_library/engine/"
src = open(SCR + "bloxbury_part1.py").read()
pre = src[:src.index("# Milo starts at the fence")]
# Milo's windows lowered (sill 4, top 8) so a 5-stud character can actually look out of them
pre = pre.replace('box("WallFront", RS(4, 7, T), R(cx_, 3.5, fz), m_wall, parent=root)',
                  'box("WallFront", RS(4, 4, T), R(cx_, 2.0, fz), m_wall, parent=root)')
pre = pre.replace('box("WallFront", RS(4, H - 11, T), R(cx_, 11 + (H - 11) / 2, fz), m_wall, parent=root)',
                  'box("WallFront", RS(4, H - 8, T), R(cx_, 8 + (H - 8) / 2, fz), m_wall, parent=root)')
pre = pre.replace('WINDOW_PARTS.append(box("Window", RS(4, 4, 0.15), R(ox, 9, fz), M_WINDOW, parent=root))',
                  'WINDOW_PARTS.append(box("Window", RS(4, 4, 0.15), R(ox, 6, fz), M_WINDOW, parent=root))')
assert pre.count("R(cx_, 2.0, fz)") == 1
exec(pre)
exec(src[src.index("# ---------------------------------------------------------------- TREES + HILLS"):
         src.index("# ---------------------------------------------------------------- CAMERA")])
RB = R                                    # Roblox coords (x, up, z) -> Blender
FPS = 24; WARP = []                       # old helpers (key/F/set_day) now run on the 24 fps timeline, no warp
for f in ("charlib", "stylelab", "hair2", "hair3", "faces2", "garments", "garments2", "hair4", "faces3", "faces4", "props"):
    exec(open(LIB + f + ".py").read())
V = Vector
ENV = {"rms": [0.0] * 4000, "cen": [0.0] * 4000}
exec(open(SCR + "rig2.py").read())       # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ... (R = radians now)
exec(open(LIB + "monster.py").read())    # THE KNOCKER (studio library)
DEG = math.radians
OUT = os.environ.get("OUT", "/home/claude/talk/p2_assets")
os.makedirs(OUT, exist_ok=True)
NF = 200
s = bpy.context.scene
s.render.fps = FPS
s.frame_start, s.frame_end = 1, NF
FT = lambda t: 1 + int(round(t * FPS))     # video seconds -> frame
for o in [o for o in bpy.data.objects if o.name.startswith("HazeVolume")]:
    bpy.data.objects.remove(o, do_unlink=True)   # Cycles: the haze volume costs too much render time

EX.update({
    "sad":      (0.03, -0.16, 0.03, -0.16, 1.0, 0.84),
    "nervous":  (0.045, -0.15, 0.055, -0.12, 0.98, 1.02),
    "scared":   (0.075, -0.2, 0.075, -0.2, 0.92, 1.22),
    "shocked":  (0.1, -0.06, 0.1, -0.06, 1.14, 1.32),
    "deadpan":  (-0.02, 0.02, -0.02, 0.02, 1.0, 0.6),
    "laugh":    (0.05, -0.1, 0.05, -0.1, 1.0, 0.42),
    "friendly": (0.03, -0.06, 0.03, -0.06, 1.0, 1.0),
    "grin":     (0.01, 0.06, 0.01, 0.06, 1.0, 0.7),
})

# ------------------------------------------------------------------ mouth events (sorted at the end: no double mouths)
_MEV = {}
_mouth_rt = mouth


def mouth(rig, frame, key):
    _MEV.setdefault(id(rig), (rig, []))[1].append((frame, key))
    rig["cur_m"] = key


def flush_mouths():
    for rig, ev in _MEV.values():
        ev.sort(key=lambda e: e[0]); rig["cur_m"] = None
        last = {}
        for fr, k in ev: last[fr] = k                  # last call for a frame wins
        for fr in sorted(last): _mouth_rt(rig, fr, last[fr])


# ------------------------------------------------------------------ blocking helpers
_CUTS = []        # (obj, frame) - hold the previous pose up to the cut, then snap


def place(P, fr, loc, yaw=0.0):
    r = P["root"]
    kf(r, "location", fr, V(loc)); kf(r, "rotation_euler", fr, (0, 0, DEG(yaw)))
    _CUTS.append((r, fr))


def hold_cuts():
    for ob, fr in _CUTS:
        for fc in _fcurves(ob):
            if fc.data_path not in ("location", "rotation_euler"): continue
            pts = [k for k in fc.keyframe_points if k.co.x < fr - 0.5]
            if not pts: continue
            prev = max(pts, key=lambda k: k.co.x)
            prev.interpolation = "CONSTANT"          # hold the last pose of the previous shot right up to the cut


def idle(P, f0, f1, amp=0.02, base_z=0.0, speed=2.2, ph=0.0):
    for fr in range(f0, f1, 12):
        kf(P["root"], "location", fr, base_z + amp * math.sin(fr / FPS * speed + ph), index=2)


def walk(P, f0, f1, p0, p1, steps=4, leg=30, yaw=None, z=0.0):
    n = f1 - f0
    for i in range(n + 1):
        fr = f0 + i; u = i / n; e = u * u * (3 - 2 * u)
        ph = steps * e
        ramp = min(1.0, u / 0.12, (1 - u) / 0.12) if 0 < u < 1 else 0.0
        ang = DEG(leg) * math.sin(math.pi * ph) * ramp
        p = V(p0).lerp(V(p1), e)
        kf(P["root"], "location", fr, (p.x, p.y, z + 0.07 * (math.cos(2 * math.pi * ph) - 1) * -0.5 * ramp))
        kf(P["hipL"], "rotation_euler", fr, (ang, 0, 0)); kf(P["hipR"], "rotation_euler", fr, (-ang, 0, 0))
        arm(P, "Left", fr, euler=(-math.degrees(ang) * 0.8 + 3, -4)); arm(P, "Right", fr, euler=(math.degrees(ang) * 0.8 + 3, 4))
        kf(P["chest"], "rotation_euler", fr, (DEG(-5) * ramp, 0, -ang * 0.15))
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", f1 + 2, (0, 0, 0))


def neck(P, fr, x=0, y=0, z=0, interp="BEZIER"):
    kf(P["neck"], "rotation_euler", fr, (DEG(x), DEG(y), DEG(z)), interp=interp)


def chest(P, fr, x=0, y=0, z=0, interp="BEZIER"):
    kf(P["chest"], "rotation_euler", fr, (DEG(x), DEG(y), DEG(z)), interp=interp)


def arms_down(P, fr):
    arm(P, "Left", fr, euler=(4, -6)); arm(P, "Right", fr, euler=(4, 6))


def smear(P, side, fr, k=1.35):
    sh = P[side]
    kf(sh, "scale", fr - 1, (1, 1, 1)); kf(sh, "scale", fr, (1, 1, k)); kf(sh, "scale", fr + 2, (1, 1, 1))


def strip_faces(P):
    for objs in P["faces"].values():
        for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    P["faces"] = {}




# ================================================================== PART 2 ASSETS
exec(open(LIB + "recurring.py").read())
exec(open(LIB + "props2.py").read())
GOLD = pmat("BraceletGold", (222, 176, 70), rough=0.22, metal=1.0)


def make_mum():
    """MUM (new, Part 2): Milo's skin tone and long curly brown H4 hair (family look), sage cardigan over a cream top, blue jeans,
    tan flats, thin gold bangle on her LEFT wrist (the bracelet that proves the closet hand is really her)."""
    S = new_set(); skin = (234, 184, 146); rng = RNG(905)
    d_cardigan(S, rng, skin, col=(132, 160, 132), inner=(244, 234, 214))
    b_trousers(S, (58, 78, 120), rng, kind="jeans")
    s_shoes(S, "loafers", (176, 130, 92), rng)
    finish(S, rng)
    P = build_body("Mum", skin, S)
    add_hair_any(P, "H4", random.Random(21), colour=(92, 60, 38))
    return P


def bracelet(P, name="Bangle"):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    # rounded-square bangle (superellipse) that clears the 1x1 arm block: corners 0.73 > 0.707, faces 0.6 > 0.5 (no clipping)
    vs = []
    for i in range(48):
        a = 2 * math.pi * i / 48; c, s_ = math.cos(a), math.sin(a)
        r = 0.66 / (abs(c) ** 4 + abs(s_) ** 4) ** 0.25
        vs.append(bm.verts.new((r * c, r * s_, 0)))
    for i in range(48): bm.edges.new((vs[i], vs[(i + 1) % 48]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); s.collection.objects.link(ob)
    ob.parent = P["Left"]; ob.location = (0, 0, -1.18)
    sk = ob.modifiers.new("skin", "SKIN")
    for v in me.skin_vertices[0].data: v.radius = (0.055, 0.055)
    ob.modifiers.new("sub", "SUBSURF").levels = 1
    me.materials.append(GOLD)
    return ob


def toaster(loc, name="Toaster"):
    r = root_of(name, loc); ch = CHROME()
    rb(name + "Body", (1.7, 1.0, 1.15), V((0, 0, 0.6)), ch, r, r=0.25)
    for dx in (-0.35, 0.35): rb(name + "Slot", (0.18, 0.75, 0.06), V((dx, 0, 1.18)), BLACKPL(), r, r=0.02)
    rb(name + "Lever", (0.12, 0.25, 0.12), V((0.92, 0, 0.75)), BLACKPL(), r, r=0.03)
    rb(name + "Base", (1.8, 1.1, 0.12), V((0, 0, 0.06)), BLACKPL(), r, r=0.04)
    return r


def room(name, org, w, d, h, wall_rgb, floor_rgb, wall_kind="plaster", floor_kind="planks"):
    """Open-front box room: floor, back/left/right walls, ceiling. Camera looks from -y toward +y."""
    o = V(org); root = root_of(name, o)
    fm = tex_mat(name + "Floor", floor_rgb, floor_kind, rough=0.6) if floor_kind else pmat(name + "Floor", floor_rgb)
    wm = tex_mat(name + "Wall", wall_rgb, wall_kind)
    rb(name + "FloorB", (w, d, 0.3), V((0, 0, -0.15)), fm, root, r=0.02)
    rb(name + "Back", (w, 0.4, h), V((0, d / 2, h / 2)), wm, root, r=0.02)
    rb(name + "Left", (0.4, d, h), V((-w / 2, 0, h / 2)), wm, root, r=0.02)
    rb(name + "Right", (0.4, d, h), V((w / 2, 0, h / 2)), wm, root, r=0.02)
    rb(name + "Ceil", (w, d, 0.3), V((0, 0, h + 0.15)), pmat(name + "CeilM", (240, 238, 232), rough=0.9), root, r=0.02)
    rb(name + "Skirt", (w - 0.5, 0.2, 0.5), V((0, d / 2 - 0.25, 0.25)), pmat(name + "SkirtM", (246, 246, 242)), root, r=0.02)
    return root, o


def area(name, loc, tgt, energy, size, col=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.energy = energy; d_.size = size; d_.color = col
    ob = bpy.data.objects.new(name, d_); s.collection.objects.link(ob); ob.location = V(loc)
    ob.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler(); return d_


def pose(P, loc, yaw):
    P["root"].location = V(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


# ---------------------------------------------------------------- cast
milo = make_milo(); mum = make_mum(); rae = make_rae(); real = make_mum()
CAST = (milo, mum, rae, real)
for P in CAST: strip_faces(P)
for o in bpy.data.objects: o.animation_data_clear()
for P in CAST: upgrade_rig(P)
fm, fmum, frae, freal = (build_face_v2(P) for P in CAST)
bracelet(mum, "BangleMum"); bracelet(real, "BangleReal")
note = p2_notebook(rae["tiltLeft"])
KN = make_knocker("Knocker", 11.5)

# ---------------------------------------------------------------- SET: sunny kitchen (new)
KO = V((520, 0, 400))
kroot, _ = room("Kitchen", KO, 26, 18, 11, (246, 236, 206), (196, 160, 118))
kit = kitchen("KitUnit", cab=(120, 156, 170), top=(238, 234, 226), loc=KO + V((-2, 7.2, 0))); kit.rotation_euler = (0, 0, DEG(180))
fridge("Fridge", loc=KO + V((9.6, 6.8, 0)))
dining_set("Table", loc=KO + V((-6.5, -2.5, 0)))
plant("KPlant", loc=KO + V((-11.5, 7.5, 0)), seed=4)
wall_clock("KClock", loc=KO + V((6, 8.75, 8.2))).rotation_euler = (0, 0, DEG(180))
toaster(KO + V((-6.6, 6.6, 4.1)), "Toaster")
# window over the sink: bright sky panel + sunlight pouring in
win = rb("KWindow", (6.0, 0.1, 3.6), KO + V((1.0, 8.75, 7.4)), pmat("KSky", (200, 225, 255), emit=3.0, emit_rgb=(225, 238, 255)), None, r=0.02)
for dx in (-3.05, 3.05): rb("KWinF", (0.25, 0.3, 3.9), KO + V((1.0 + dx, 8.65, 7.4)), pmat("WinFrame", (250, 250, 248)), None, r=0.03)
for dz in (-1.9, 1.9): rb("KWinF", (6.3, 0.3, 0.25), KO + V((1.0, 8.65, 7.4 + dz)), pmat("WinFrame", (250, 250, 248)), None, r=0.03)
area("KSun", KO + V((1.0, 7.5, 9.5)), KO + V((-3, -2, 0)), 2600, 6, (1.0, 0.9, 0.75))
area("KFill", KO + V((0, -14, 9)), KO + V((0, 2, 3)), 1400, 14, (1.0, 0.97, 0.92))
pose(mum, KO + V((2.6, 4.3, 0)), 180)          # at the hob (back to camera in the hook; turned for the sheet)
pose(milo, KO + V((-4.0, -0.5, 0)), 20)

# ---------------------------------------------------------------- SET: upstairs hallway + mirror, night (new)
HO = V((560, 0, 400))
room("Hall", HO, 10, 26, 11, (182, 170, 150), (120, 86, 60), wall_kind="plaster")
mirror_m = pmat("Mirror", (235, 238, 240), rough=0.0, metal=1.0)
rb("MirrorFrame", (0.3, 3.8, 6.0), HO + V((-4.7, 2.0, 5.2)), pmat("MirrorWood", (70, 46, 30), rough=0.5), None, r=0.08)
rb("MirrorGlass", (0.06, 3.2, 5.4), HO + V((-4.52, 2.0, 5.2)), mirror_m, None, r=0.01)
door("HallDoorEnd", loc=HO + V((0, 12.8, 0)))
rb("Runner", (3.6, 22, 0.05), HO + V((0, 0, 0.03)), fabric("RunnerFab", (120, 40, 44)), None, r=0.01)
area("HallLamp", HO + V((0, 6, 10.5)), HO + V((0, 6, 0)), 260, 2.5, (1.0, 0.72, 0.45))
area("HallMoon", HO + V((4.5, -12, 8)), HO + V((-3, 4, 3)), 300, 6, (0.55, 0.65, 1.0))

# ---------------------------------------------------------------- list page (Mum crossed out FIRST, three weeks ago)
LIST_PATH = "/tmp/p2_list_mum.png"
LIST = p2_list_insert(V((700, 700, 0)), path=LIST_PATH,
                      names=("Milo's Mum", "Mr. Hollis", "The Patels", "Jonah", "Mrs. Reed", "Old Tom", "Ellie", "Rae", "Milo?"), crossed=7)

# ---------------------------------------------------------------- camera + shot list
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
cam.data.sensor_width = 36; cam.data.clip_end = 3000; cam.data.dof.use_dof = False


def look(pos, tgt, lens=35, fstop=None, focus=None):
    cam.location = V(pos); cam.rotation_euler = (V(tgt) - V(pos)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    cam.data.dof.use_dof = fstop is not None
    if fstop: cam.data.dof.aperture_fstop = fstop; cam.data.dof.focus_distance = focus or (V(tgt) - V(pos)).length


def head(P): return P["root"].matrix_world @ V((0, 0, 4.5))


def show(objs_on):
    pass


def setface(rig, ex, mo):
    expr(rig, 1, ex); mouth(rig, 1, mo)


SHOTS = {}


def shot(name):
    def deco(fn): SHOTS[name] = fn; return fn
    return deco


set_day(0.0); house_lights(0.0, False)
MILO_LIGHT_KEEP = None

# ---------------------------------------------------------------- STUDIO (neutral cyc for character cards)
SO = V((600, 0, 400))
rb("CycFloor", (60, 40, 0.3), SO + V((0, 6, -0.15)), pmat("CycGrey", (168, 170, 176), rough=0.8), None, r=0.02)
rb("CycBack", (60, 0.3, 30), SO + V((0, 14, 15)), pmat("CycGrey2", (150, 152, 160), rough=0.85), None, r=0.02)
STUDIO_L = [area("SKey", SO + V((-10, -14, 14)), SO + V((0, 0, 3.5)), 5200, 10, (1.0, 0.96, 0.9)),
            area("SFill", SO + V((12, -10, 6)), SO + V((0, 0, 3.5)), 1800, 12, (0.85, 0.9, 1.0)),
            area("SRim", SO + V((0, 12, 12)), SO + V((0, 0, 4)), 2600, 8, (1, 1, 1))]
# void for the Knocker (dark: eyes + cold rim + faint red underglow)
DO = V((660, 0, 400))
rb("VoidFloor", (40, 40, 0.3), DO + V((0, 0, -0.15)), pmat("VoidM", (6, 6, 8), rough=1.0), None, r=0.02)
for nm_, sz_, lc_ in (("VoidBack", (30, 0.4, 24), (0, 10, 12)), ("VoidL", (0.4, 30, 24), (-12, 0, 12)), ("VoidR", (0.4, 30, 24), (12, 0, 12)),
                     ("VoidFront", (30, 0.4, 24), (0, -20, 12)), ("VoidTop", (30, 32, 0.4), (0, -4, 24))):
    rb(nm_, sz_, DO + V(lc_), pmat("VoidM", (6, 6, 8), rough=1.0), None, r=0.02)
area("KRim", DO + V((5, 8, 12)), DO + V((0, 0, 6)), 900, 4, (0.55, 0.65, 1.0))
area("KUnder", DO + V((0, -3, 0.5)), DO + V((0, 0, 7)), 60, 3, (1.0, 0.12, 0.05))


def k_at(loc, yaw):
    KN["root"].location = V(loc) if isinstance(KN, dict) else V(loc)


try: KROOT = KN["root"]
except Exception: KROOT = KN
KROOT.location = DO; KROOT.rotation_euler = (0, 0, DEG(180))

# ---------------------------------------------------------------- shots
SHOT_LIST = []


def add(name, res, fn): SHOT_LIST.append((name, res, fn))


ALL = (milo, mum, rae, real)
# Part 2 needs a HOLLOW closet (the real Mum is inside it): swap the solid ClosetBox for a shell with the same outside
_cb = bpy.data.objects["ClosetBox"]; _cm = _cb.material_slots[0].material; _cb.hide_render = True; _cb.hide_viewport = True
for nm_, sz_, lc_ in (("ClosetBackP", (6.0, 0.2, 10.0), (7.0, -48.9, 5.0)), ("ClosetSideL", (0.2, 3.0, 10.0), (4.1, -47.5, 5.0)),
                      ("ClosetSideR", (0.2, 3.0, 10.0), (9.9, -47.5, 5.0)), ("ClosetTopP", (6.0, 3.0, 0.2), (7.0, -47.5, 9.9))):
    rb(nm_, sz_, V(lc_), _cm, None, r=0.01)


def reset_arms():
    for P in ALL: arms_down(P, 1)


def only(*Ps):
    for i, P in enumerate(ALL):
        if P not in Ps: pose(P, (2000 + 10 * i, 2000, -500), 0)


def sh_lineup():
    set_day(0.0); only(milo, mum, rae)
    for P, x in ((milo, -4.2), (mum, 0.0), (rae, 4.2)): pose(P, SO + V((x, 0, 0)), 180)
    setface(fm, "friendly", "rest_smile"); setface(fmum, "content", "rest_smile"); setface(frae, "deadpan", "rest_flat")
    look(SO + V((0, -22, 4.2)), SO + V((0, 0, 3.0)), 50)


def sh_mums():
    set_day(0.0); only(mum, real)
    pose(mum, SO + V((-2.6, 0, 0)), 195); pose(real, SO + V((2.6, 0, 0)), 165)
    setface(fmum, "content", "rest_creepy"); setface(freal, "scared", "rest_frown")
    look(SO + V((0, -14, 4.4)), SO + V((0, 0, 3.6)), 50)


def sh_bracelet():
    set_day(0.0); only(mum); setface(fmum, "content", "rest_smile")
    pose(mum, SO + V((0, 0, 0)), 200); arm(mum, "Left", 1, target=(-1.4, 1.5, 2.7))
    bpy.context.view_layer.update(); w = mum["Left"].matrix_world @ V((0, 0, -1.2))
    look(w + V((-2.2, -4.2, 1.4)), w + V((0.3, 0, 0.3)), 55, fstop=2.4)


def sh_kitchen():
    set_day(0.0); only(mum, milo)
    pose(mum, KO + V((2.6, 4.3, 0)), 195); pose(milo, KO + V((-4.2, -1.2, 0)), 30)
    setface(fmum, "content", "rest_smile"); setface(fm, "nervous", "rest_flat")
    look(KO + V((-0.5, -12.5, 6.2)), KO + V((-0.6, 2.5, 3.9)), 24)


def sh_toaster():
    set_day(0.0); only(mum)
    pose(mum, KO + V((-3.2, 3.9, 0)), 10)
    t = KO + V((-6.6, 6.6, 4.8))
    look(t + V((1.4, -6.8, 1.8)), t + V((0, 0, -0.2)), 45, fstop=2.8)


def sh_mirror():
    set_night(0.0); only(milo, mum)
    pose(milo, HO + V((-1.0, 0.6, 0)), 100); pose(mum, HO + V((1.8, 11.0, 0)), 180)
    setface(fm, "nervous", "rest_flat"); setface(fmum, "content", "rest_creepy")
    look(HO + V((3.18, -9.0, 5.0)), HO + V((-4.0, 2.4, 4.8)), 30)


def sh_porch():
    set_day(0.0); only(rae, milo)
    pose(rae, (50.0, -28.4, 0.0), 30); pose(milo, (47.6, -24.2, 0.0), 210)
    setface(frae, "deadpan", "rest_flat"); setface(fm, "nervous", "rest_flat")
    look((55.5, -18.5, 5.4), (48.8, -26.6, 4.2), 30)


def sh_list():
    look(LIST + V((0, 5.2, 0)), LIST, 50)


def sh_knocker():
    only()
    look(DO + V((0, -14, 7.8)), DO + V((0, 0, 7.6)), 48)


CLOSET_IN = area("ClosetIn", (3.2, -43.6, 6.2), (4.5, -45.7, 3.2), 0, 0.8, (0.7, 0.78, 1.0))   # thin moonlight on the hand only


def sh_closet():
    set_night(0.0); only(real); CLOSET_IN.energy = 70
    CLOSET_HINGE.rotation_euler = (0, 0, DEG(-9))
    pose(real, (6.5, -47.9, 0.4), 0); arm(real, "Left", 1, target=(-2.0, 2.2, 2.6)); setface(freal, "scared", "rest_frown")
    look((1.3, -39.2, 4.3), (4.6, -45.5, 3.4), 42, fstop=2.4)


def sh_dbg():
    set_night(0.0); only(real); CLOSET_IN.energy = 60
    CLOSET_HINGE.rotation_euler = (0, 0, DEG(-20))
    pose(real, (6.4, -47.6, 0.4), 0); arm(real, "Left", 1, target=(-1.9, 2.2, 3.0))
    look((7.0, -36.0, 14.0), (6.5, -46.5, 2.0), 24)


# add("zz_dbg", (540, 960), sh_dbg)   # closet layout debug view
add("01_cast_lineup", (1440, 810), sh_lineup)
add("02_fake_vs_real_mum", (1440, 810), sh_mums)
add("03_bracelet", (960, 960), sh_bracelet)
add("04_kitchen", (540, 960), sh_kitchen)
add("05_toaster", (540, 960), sh_toaster)
add("06_hallway_mirror", (540, 960), sh_mirror)
add("07_rae_porch", (540, 960), sh_porch)
add("08_list", (540, 960), sh_list)
add("09_knocker_bridge", (540, 960), sh_knocker)
add("10_closet_hand", (540, 960), sh_closet)

s.render.engine = "CYCLES"; s.cycles.device = "CPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 16))
s.cycles.use_denoising = True
try: s.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception: pass
s.render.use_motion_blur = False
s.render.image_settings.file_format = "PNG"
want = os.environ.get("SHOTS", "all").split(",")
SCALE = float(os.environ.get("SCALE", 1.0))
for name, (rx, ry), fn in SHOT_LIST:
    if want != ["all"] and not any(name.startswith(w) for w in want): continue
    for o in bpy.data.objects: o.animation_data_clear()
    _MEV.clear(); _CUTS.clear(); reset_arms(); CLOSET_IN.energy = 0; CLOSET_HINGE.rotation_euler = (0, 0, 0)
    fn()
    flush_mouths(); apply_interp(); apply_interpolation()
    s.render.resolution_x, s.render.resolution_y = int(rx * SCALE), int(ry * SCALE)
    s.frame_set(1); s.render.filepath = f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)
print("DONE")
