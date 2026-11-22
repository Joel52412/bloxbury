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
exec(open(LIB + "props3.py").read())        # props/sets batch 3 (Part 2, approved 22 Nov)


def pose(P, loc, yaw):
    P["root"].location = V(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


area = p3_area


# ---------------------------------------------------------------- cast
milo = make_milo(); mum = make_mum("Mum"); rae = make_rae(); real = make_mum("RealMum")
CAST = (milo, mum, rae, real)
for P in CAST: strip_faces(P)
for o in bpy.data.objects: o.animation_data_clear()
for P in CAST: upgrade_rig(P)
fm, fmum, frae, freal = (build_face_v2(P) for P in CAST)
note = p2_notebook(rae["tiltLeft"])
KN = make_knocker("Knocker", 11.5)

# ---------------------------------------------------------------- SET: sunny kitchen (new)
KO = V((520, 0, 400)); KIT = p3_kitchen_set(KO)
pose(mum, KO + V((2.6, 4.3, 0)), 180); pose(milo, KO + V((-4.0, -0.5, 0)), 20)
HO = V((560, 0, 400)); HALL = p3_hallway_set(HO)

# ---------------------------------------------------------------- list page (Mum crossed out FIRST, three weeks ago)
LIST = p3_list_insert(V((700, 700, 0)), path="/tmp/p2_list_mum.png")

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
p3_hollow_closet()     # Part 2: the real Mum is inside it


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
