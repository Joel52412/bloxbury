# part2.py - BLOXBURY Part 2 "She Came Home". 24 fps, rig v2 faces, library cast/sets (props3), director shots.
# Audio/cues/captions: _pipeline/audio_tools/prep_p2.py -> /home/claude/talk/{env_p2.json, part2_audio.wav, captions_p2.ass}
# Preview: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 python3 part2.py      Pod: ENGINE=GPU RENDER=1 RX=1080 RY=1920 blender -b --python part2.py
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
ENV = json.load(open("/home/claude/talk/env_p2.json")); E2 = dict(ENV); ENV["rms"] = E2["rms"]["milo"]; ENV["cen"] = E2["cen"]["milo"]
exec(open(SCR + "rig2.py").read())       # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ... (R = radians now)
exec(open(LIB + "monster.py").read())    # THE KNOCKER (studio library)
DEG = math.radians
OUT = os.environ.get("OUT", "/home/claude/talk/frames_p2")
os.makedirs(OUT, exist_ok=True)
NF = E2["nf"]
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




# ================================================================== LIBRARY: cast cards, props batches, sets
exec(open(LIB + "recurring.py").read())
exec(open(LIB + "props2.py").read())
exec(open(LIB + "props3.py").read())
SC = {n: (a, b) for n, a, b in E2["scenes"]}
FAR = V((3000, 3000, -800))


def ray_only_glossy(P, on=True):
    """Mirror twin: visible ONLY in reflections (and the real one is hidden from reflections)."""
    for o in [P["root"]] + list(P["root"].children_recursive):
        if hasattr(o, "visible_camera"):
            o.visible_camera = not on; o.visible_diffuse = not on; o.visible_shadow = not on
            o.visible_transmission = not on; o.visible_volume_scatter = not on; o.visible_glossy = True


def no_reflection(P):
    for o in [P["root"]] + list(P["root"].children_recursive):
        if hasattr(o, "visible_glossy"): o.visible_glossy = False


# ------------------------------------------------------------------ cast
milo = make_milo(); mum = make_mum("Mum"); rae = make_rae(); real = make_mum("RealMum"); refl = make_mum("ReflMum")
CAST = (milo, mum, rae, real, refl)
for P in CAST: strip_faces(P)
for o in bpy.data.objects: o.animation_data_clear()
for P in CAST: upgrade_rig(P)
fm, fmum, frae, freal, frefl = (build_face_v2(P) for P in CAST)
RIGS = {"milo": fm, "mum": fmum, "rae": frae, "real": freal, "refl": frefl}
note = p2_notebook(rae["tiltLeft"])
no_reflection(mum)                      # the fake Mum has NO reflection of her own: the mirror shows the twin
ray_only_glossy(refl)
for rig, rest in ((fm, "rest_flat"), (fmum, "rest_smile"), (frae, "rest_flat"), (freal, "rest_frown"), (frefl, "rest_smile")):
    mouth(rig, 1, rest)
for P in CAST: place(P, 1, FAR + V((CAST.index(P) * 12, 0, 0)))


def park(P, fr):
    place(P, fr, FAR + V((CAST.index(P) * 12, 0, 0)))


# ------------------------------------------------------------------ sets
KO = V((520, 0, 400)); KIT = p3_kitchen_set(KO)
HO = V((560, 0, 400)); HALL = p3_hallway_set(HO)
p3_hollow_closet()
LIST = p3_list_insert(V((700, 700, 0)), path="/tmp/p3_list.png")
# pancakes: plate + three stacked discs + butter, on the table in front of Milo
rb("KitchenFrontWall", (26, 0.4, 11), KO + V((0, -9.0, 5.5)), tex_mat("KitchenWall", (246, 236, 206), "plaster"), None, r=0.02)   # closes the room for reverse shots
for o in [o for o in bpy.data.objects if o.name.startswith("Table_Chair")]:
    for c in [o] + list(o.children_recursive): c.hide_render = True                    # chairs blocked the hob shots and crowded the hug (they stand)
PLATE = KO + V((-5.9, -1.0, 3.96))
rcyl("Plate", 0.95, 0.08, PLATE, pmat("PlateW", (246, 246, 244), rough=0.25), None)
for k in range(3): rcyl("Pancake", 0.72 - k * 0.03, 0.16, PLATE + V((0, 0, 0.14 + k * 0.17)), pmat("PancakeM", (214, 158, 84), rough=0.6), None, bevel=0.07)
rb("Butter", (0.32, 0.32, 0.14), PLATE + V((0.05, 0, 0.66)), pmat("ButterM", (250, 226, 130), rough=0.3), None, r=0.04)
# Milo's room at night: dim cool fill, moonlight on the closet crack, light under the bedroom door
ROOMFILL = p3_area("RoomFill2", (-2, -36, 12.5), (2, -40, 0), 0, 8, (0.6, 0.7, 1.0))
CLOSET_IN = p3_area("ClosetIn", (3.2, -43.6, 6.2), (4.5, -45.7, 3.2), 0, 0.8, (0.7, 0.78, 1.0))
MKEY = p3_area("MiloKey", (5.5, -32.5, 7.5), (3.0, -38.6, 4.6), 0, 4, (1.0, 0.9, 0.8))
MRIM = p3_area("MiloRim", (0.0, -45.0, 8.0), (3.0, -38.6, 4.6), 0, 3, (0.6, 0.7, 1.0))
DOORLINE = rb("DoorLight", (4.4, 0.35, 0.02), V((0, -30.75, 0.42)), pmat("DoorLightM", (255, 200, 140), emit=0.0, emit_rgb=(255, 190, 120)), None, r=0.01)
DOORLINE_EM = DOORLINE.material_slots[0].material.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
FEET = [rb("FootShadow", (1.0, 0.36, 0.03), V((x, -30.75, 0.43)), pmat("FootShadowM", (0, 0, 0), rough=1.0), None, r=0.01) for x in (-0.7, 0.7)]
FRONT_DOOR = [o for o in bpy.data.objects if o.name.startswith("FrontDoor")][0]
FD_ROT = tuple(FRONT_DOOR.rotation_euler)
strip, cglow = p2_door_glow(7.0, -45.85)        # Part 1's closet glow (bridge only)
# the Knocker: bridge lunge (camera-visible) + toaster ghost (reflection-only)
KN = make_knocker("Knocker", 10.5); KR = KN["root"]
KG = make_knocker("KnockerGhost", 9.0); ray_only_glossy(KG)
KR.location = FAR; KG["root"].location = FAR

# ------------------------------------------------------------------ helpers
def vis_obj(o, fr, on): kf(o, "hide_render", fr, not on, interp="CONSTANT")


_BLINKS = []


def blinks(rig, t0, t1, every=3.1, ph=0.0):
    _BLINKS.append((rig, t0, t1, every, ph))      # applied at the end, once every cut is known (no closed eyes before a cut)


def apply_blinks():
    for rig, t0, t1, every, ph in _BLINKS:
        t = t0 + 0.9 + ph
        while t < t1 - 0.4:
            fr = FT(t)
            if all(not (c - 7 <= fr <= c + 1) for c in CUT_FR): blink(rig, fr)
            t += every + 0.6 * math.sin(t * 1.7)


def say(L, rig, rest, style="calm", nod=3.0, P=None):
    ENV["rms"] = E2["rms"][L["who"]]; ENV["cen"] = E2["cen"][L["who"]]
    f0, f1 = FT(L["t0"]), FT(L["t1"]) + 1
    lipsync(rig, f0, f1, [(f0, rest, style)]); mouth(rig, f1 + 1, rest)
    if P is not None: accents(P, rig, f0, f1, nod=nod)


LN = {}
for L in E2["lines"]: LN.setdefault(L["text"].split()[0].lower().strip(".,!?") + "@" + str(round(L["t0"])), L)


def line(t0):
    return min(E2["lines"], key=lambda L: abs(L["t0"] - t0))


# ================================================================== CAMERA (from Part 1: hard cuts, each shot keyed inside its frames)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4; cam.data.sensor_width = 36; cam.data.clip_end = 3000
_PREV_E = [None]
SHOTS = []


def cam_key(fr, pos, tgt, lens, focus=None, interp="BEZIER"):
    pos = V(pos); tgt = V(tgt)
    kf(cam, "location", fr, pos, interp=interp)
    e = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    if _PREV_E[0] is not None: e.make_compatible(_PREV_E[0])
    _PREV_E[0] = e.copy()
    kf(cam, "rotation_euler", fr, e, interp=interp)
    kf(cam.data, "lens", fr, lens, interp=interp)
    cam.data.dof.focus_distance = focus or (tgt - pos).length
    cam.data.keyframe_insert("dof.focus_distance", frame=fr); _LOG.append((cam.data, "dof.focus_distance", fr, interp))


def shot(name, t0, t1, keys, fstop=2.4):
    """keys: [(u 0..1, pos, tgt, lens)]; calm eased moves only (hard rule)."""
    f0, f1 = FT(t0), FT(t1) - 1
    SHOTS.append((name, f0, f1))
    for i, (u, p, g, l) in enumerate(keys):
        fr = f0 + int(round(u * (f1 - f0)))
        cam_key(fr, p, g, l, interp="CONSTANT" if fr >= f1 else "BEZIER")
    if keys[-1][0] < 1: cam_key(f1, keys[-1][1], keys[-1][2], keys[-1][3], interp="CONSTANT")
    cam.data.dof.aperture_fstop = fstop; cam.data.keyframe_insert("dof.aperture_fstop", frame=f0)
    _LOG.append((cam.data, "dof.aperture_fstop", f0, "CONSTANT"))


def idle_here(P, f0, f1, amp=0.015, ph=0.0):
    idle(P, f0, f1, amp=amp, base_z=P["root"].location.z, ph=ph)     # Part 1's idle() keys absolute z: keep the set's floor height


def ots(subj, other, along=3.0, side=1.3, dz=0.25):
    """Over-the-shoulder camera for a CU on subj: on the subj->other axis, pushed sideways so it never sits in the other head."""
    a = H(subj); b = H(other); d = (b - a); d.z = 0; L = d.length; d.normalize()
    perp = V((d.y, -d.x, 0)) * side
    return a + d * min(along, L - 1.6) + perp + V((0, 0, dz))


def H(P, dz=0.0):
    return V(P["root"].location) + V((0, 0, 4.6 + dz))


def at(P, fr, loc, yaw):
    place(P, fr, V(loc), yaw); P["root"].location = V(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


# ================================================================== 0  BRIDGE 0.00-1.25: Part 1's last image, then black
set_night(0.0); house_lights(0.0, False)
CL_X, CL_Y = 7.0, -45.85
kf(CLOSET_HINGE, "rotation_euler", 1, (0, 0, DEG(-88)), interp="CONSTANT")
kf(cglow, "energy", 1, 700, interp="CONSTANT"); kf(cglow, "energy", FT(0.8), 0, interp="CONSTANT")
s.frame_set(1); bpy.context.view_layer.update()
KR.location = (0, 0, 0); KR.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
HEAD_OFF = KN["head"].matrix_world.translation - KR.matrix_world.translation
BCAM = V((3.0, -40.6, 4.4)); BAIM = V((CL_X, CL_Y, 4.6))
LUNGE = BCAM + (BAIM - BCAM).normalized() * 1.9 + V((0, 0, -0.1))


def k_place(fr, head_world, yaw=0.0, interp="BEZIER"):
    rot = Matrix.Rotation(DEG(yaw), 3, "Z")
    kf(KR, "location", fr, V(head_world) - rot @ HEAD_OFF, interp=interp); kf(KR, "rotation_euler", fr, (0, 0, DEG(yaw)), interp=interp)


k_place(1, LUNGE + V((0.6, -1.4, 0.15)), 24); k_place(FT(0.55), LUNGE, 26); k_place(FT(0.8), LUNGE + V((0.04, 0.05, 0)), 26, interp="CONSTANT")
k_place(FT(0.8) + 1, FAR, 0, interp="CONSTANT")
krim = p3_area("KRimB", (6.4, -48.6, 9.5), LUNGE, 0, 2, (0.55, 0.65, 1.0))
kf(krim, "energy", 1, 650, interp="CONSTANT"); kf(krim, "energy", FT(0.8), 0, interp="CONSTANT")
shot("0 bridge lunge", 0.0, 0.8, [(0, BCAM, BAIM, 30), (1, BCAM + V((0, -0.08, 0)), BAIM, 30)])
# black card (bridge 0.8-1.25 and the hard cut 72.4-73.0)
blk = plane("Blackout", 4, 4, V((0, 0, 0)), pmat("BlackCard", (0, 0, 0), rough=1.0), cam)
blk.location = (0, 0, -0.3); blk.rotation_euler = (DEG(90), 0, 0); blk.visible_shadow = False
for fr_b, on in ((1, False), (FT(0.8), True), (FT(1.25), False), (FT(E2["black_cut"]), True), (FT(E2["outro0"]), False)):
    kf(blk, "hide_render", fr_b, not on, interp="CONSTANT")
shot("0b black", 0.8, 1.25, [(0, BCAM, BAIM, 30)])

# ================================================================== 1-2  KITCHEN 1.25-18.4 (day). Fake Mum: held smile, NEVER blinks, no breathing idle
set_day(1.25)
HOB = KO + V((-4.6, 4.3, 0)); MT = KO + V((-6.5, -6.4, 0))
at(mum, FT(1.25), HOB, 200)                    # at the hob, turned to us for the match cut
at(milo, FT(1.25), MT, -12)                     # at the table, facing the hob
expr(fmum, FT(1.25), "content"); mouth(fmum, FT(1.25), "rest_smile")
for t, z in ((1.25, 0), (2.4, 5), (3.6, -4), (4.9, 4), (6.2, 0)):            # humming: a slow, too-even head sway
    neck(mum, FT(t), 0, 0, z)
arm(mum, "Right", FT(1.25), euler=(55, 20)); arm(mum, "Right", FT(5.4), euler=(55, 20)); arm(mum, "Right", FT(5.9), euler=(8, 6))
arm(mum, "Left", FT(1.25), euler=(4, -6))
idle_here(milo, FT(1.25), FT(18.4))
expr(fm, FT(1.25), "nervous"); expr(fm, FT(5.6), "friendly"); expr(fm, FT(6.8), "nervous")
MH = H(milo); MUH = H(mum)
shot("K1 match cut: her smile", 1.25, 4.1, [(0, MUH + V((0.55, -2.4, 0.05)), MUH + V((0, 0, -0.05)), 62),
                                             (1, MUH + V((1.6, -7.2, 0.6)), MUH + V((-0.4, 0, -0.6)), 34)])
shot("K2 Milo at the table", 4.1, 5.5, [(0, MH + V((1.8, 4.6, 0.2)), MH, 52), (1, MH + V((1.6, 4.1, 0.2)), MH, 56)])
say(line(5.60), fmum, "rest_smile", "excited")                               # "Morning, Milo!" bright
expr(fmum, FT(5.6), "excited"); expr(fmum, FT(6.9), "content")
shot("K3 Morning, Milo!", 5.5, 7.0, [(0, MUH + V((-1.6, -4.4, 0.2)), MUH, 44), (1, MUH + V((-1.4, -3.9, 0.15)), MUH, 48)])
# pancakes: her hand slides the plate in (plate rides on her hand, then stays)
shot("K4 pancakes", 7.0, 9.0, [(0, PLATE + V((-1.4, -3.2, 2.4)), PLATE + V((0, 0, 0.2)), 40), (1, PLATE + V((-1.2, -2.8, 2.0)), PLATE + V((0, 0, 0.2)), 44)], fstop=3.2)
at(mum, FT(7.0), KO + V((-4.4, 0.9, 0)), 200)
arm(mum, "Right", FT(7.0), euler=(70, 12)); arm(mum, "Right", FT(8.2), euler=(70, 12)); arm(mum, "Right", FT(8.6), euler=(6, 6))
# toaster + humming at the hob; the Knocker ghost shows in the chrome for 4 frames (rewatch bait)
at(mum, FT(9.0), HOB, 175)
for t, z in ((9.0, 0), (9.7, 6), (10.4, -6), (11.0, 0)): neck(mum, FT(t), 0, 0, z)
arm(mum, "Right", FT(9.0), euler=(55, 20)); arm(mum, "Left", FT(9.0), euler=(4, -6))
TST = KO + V((-6.6, 6.6, 4.7))
shot("K5 toaster + humming", 9.0, 11.0, [(0, TST + V((-2.6, -3.6, 0.5)), TST + V((1.4, 0, -0.1)), 34), (1, TST + V((-2.4, -3.3, 0.45)), TST + V((1.5, 0, -0.1)), 36)])
KG["root"].location = FAR
kf(KG["root"], "location", FT(9.95), TST + V((1.2, -4.4, -4.7)), interp="CONSTANT"); kf(KG["root"], "rotation_euler", FT(9.95), (0, 0, DEG(160)), interp="CONSTANT")
kf(KG["root"], "location", FT(9.95) + 4, FAR, interp="CONSTANT"); kf(KG["root"], "location", 1, FAR, interp="CONSTANT")
# the hug: from behind Milo (his body hides where her arms pass), her face over his shoulder, smile held, eyes open
HUG = MT + V((-1.15, -1.0, 0.25))                 # behind him, a little to his right, so her face sits beside his
at(mum, FT(11.0), HUG, -12)
arm(mum, "Left", FT(11.0), target=(0.2, 1.9, 3.3)); arm(mum, "Right", FT(11.0), target=(1.3, 1.9, 3.4))   # arms wrap round his chest (hug contact is OK)
arm(milo, "Left", FT(11.0), euler=(4, -6)); arm(milo, "Right", FT(11.0), euler=(4, 6))
neck(mum, FT(11.0), -4, 0, 6); expr(fmum, FT(11.0), "content")
expr(fm, FT(11.0), "nervous"); expr(fm, FT(14.2), "notice"); expr(fm, FT(16.3), "scared")
neck(milo, FT(11.0), 0, 0, 0); neck(milo, FT(15.0), 0, 0, 0); neck(milo, FT(16.6), 0, 0, 12)      # his head slides toward her face
MH2 = H(milo); MUH2 = HUG + V((0, 0, 4.6))
TW = (MH2 + MUH2) / 2
shot("K6 the long hug", 11.0, 14.15, [(0, TW + V((1.6, 6.4, 0.6)), TW, 40), (1, TW + V((1.4, 5.4, 0.5)), TW, 46)])
shot("K7 she called me Milo", 14.15, 16.25, [(0, MH2 + V((1.6, 4.0, 0.3)), MH2 + V((-0.25, 0, 0)), 48), (1, MH2 + V((1.4, 3.6, 0.28)), MH2 + V((-0.25, 0, 0)), 52)])
shot("K8 never calls me Milo", 16.25, SC["kitchen"][1], [(0, MH2 + V((1.0, 3.0, 0.15)), MH2 + V((0, 0, 0.05)), 64), (1, MH2 + V((0.85, 2.6, 0.12)), MH2 + V((0, 0, 0.05)), 72)])
blinks(fm, 1.25, 18.4)

# ================================================================== 3-4  RAE'S PORCH 18.4-39.9 (day, town)
P0 = SC["porch"][0]
RAEP = V((50.0, -28.4, 0.0)); MILP = V((47.6, -24.2, 0.0))
park(mum, FT(P0))
at(rae, FT(P0), RAEP, 30); at(milo, FT(P0), MILP + V((-5.5, 8.0, 0)), 210)
walk(milo, FT(P0), FT(19.3), MILP + V((-5.5, 8.0, 0)), MILP, steps=4, leg=34)          # he runs up to her door
idle_here(rae, FT(P0), FT(39.9), amp=0.012, ph=1.0); idle_here(milo, FT(19.4), FT(39.9))
arms_down(rae, FT(P0)); arm(rae, "Left", FT(P0), (-0.6, 1.4, 2.8)); arm(rae, "Left", FT(28.3), (-0.6, 1.4, 2.8))
arm(rae, "Left", FT(28.9), (-0.4, 1.8, 3.6)); arm(rae, "Left", FT(34.9), (-0.4, 1.8, 3.6)); arm(rae, "Left", FT(35.5), (-0.6, 1.4, 2.8))
expr(frae, FT(P0), "deadpan"); expr(frae, FT(28.6), "sad"); expr(frae, FT(33.3), "ominous"); expr(frae, FT(37.0), "deadpan")
expr(fm, FT(P0), "scared"); expr(fm, FT(23.4), "nervous"); expr(fm, FT(29.0), "shocked"); expr(fm, FT(35.1), "scared")
for t in (18.80, 23.40, 35.10): say(line(t), fm, "rest_flat", "excited" if t < 19 else "calm", P=milo)
for t in (21.50, 25.50, 28.60, 30.00, 33.30, 37.00, 38.20): say(line(t), frae, "rest_flat", "calm", nod=2.5, P=rae)
RH = V((50.0, -28.4, 4.6)); MHP = MILP + V((0, 0, 4.6))
shot("P1 he runs to Rae", P0, 21.45, [(0, (55.5, -17.0, 5.6), (49.0, -25.5, 4.0), 28), (1, (55.0, -18.2, 5.4), (48.8, -26.4, 4.1), 30)])
shot("P2 Did she knock?", 21.45, 23.35, [(0, ots(rae, milo, 3.1, 1.3), RH, 46), (1, ots(rae, milo, 2.9, 1.25), RH, 50)])
shot("P3 she had a key", 23.35, 25.45, [(0, ots(milo, rae, 3.1, -1.3), MHP, 46), (1, ots(milo, rae, 2.9, -1.25), MHP, 50)])
shot("P4 doesn't need to knock", 25.45, 28.5, [(0, ots(rae, milo, 3.2, 1.35), RH, 46), (1, ots(rae, milo, 2.7, 1.2), RH, 56)])
shot("P5 she opens the list", 28.5, 29.95, [(0, ots(rae, milo, 3.0, 1.6, -0.4), RH + V((-0.2, 0, -1.0)), 38), (1, ots(rae, milo, 2.9, 1.55, -0.4), RH + V((-0.2, 0, -1.0)), 40)])
shot("P5b insert: Mum crossed off", 29.95, 33.2, [(0, LIST + V((0.1, 5.4, 0.4)), LIST + V((0, 0, 0.4)), 42), (1, LIST + V((-0.2, 3.6, 1.1)), LIST + V((-0.6, 0, 1.2)), 50)], fstop=5)
shot("P6 Three weeks ago", 33.2, 35.0, [(0, ots(rae, milo, 2.6, 0.9, 0.1), RH, 58), (1, ots(rae, milo, 2.5, 0.85, 0.1), RH, 64)])
shot("P7 who's in my kitchen", 35.0, 36.95, [(0, ots(milo, rae, 3.0, -1.25), MHP, 50), (1, ots(milo, rae, 2.7, -1.15), MHP, 56)])
shot("P8 Mirrors don't lie", 36.95, SC["porch"][1], [(0, ots(rae, milo, 3.2, 1.4), RH, 44), (1, ots(rae, milo, 2.6, 1.15), RH, 56)])
blinks(fm, P0, 39.9, ph=0.7); blinks(frae, P0, 39.9, every=4.2, ph=1.3)

# ================================================================== 5  HALLWAY MIRROR 39.9-51.7 (night)
M0 = SC["mirror"][0]
set_night(M0)
park(rae, FT(M0))
MILH = HO + V((-1.0, 0.6, 0)); MUMH = HO + V((1.8, 11.0, 0))
at(milo, FT(M0), MILH, 100); at(mum, FT(M0), MUMH, 180); at(refl, FT(M0), MUMH, 180)
for P in (milo, mum, refl): arms_down(P, FT(M0))
for P in (mum, refl): neck(P, FT(M0) - 1, 0, 0, 0, interp="CONSTANT")
idle_here(milo, FT(M0), FT(51.7), amp=0.012)
expr(fm, FT(M0), "nervous"); expr(fm, FT(41.2), "content"); expr(fm, FT(42.6), "nervous"); expr(fm, FT(45.2), "scared"); expr(fm, FT(47.6), "shocked")
mouth(fm, FT(M0), "rest_flat")
# real Mum: smile drops on "Then Mum stopped smiling"; reflection keeps it, then its head turns to Milo (in silence)
expr(fmum, FT(M0), "content"); mouth(fmum, FT(M0), "rest_smile"); expr(fmum, FT(43.0), "content"); expr(fmum, FT(43.4), "deadpan")
mouth(fmum, FT(43.3), "rest_flat")
expr(frefl, FT(M0), "content"); mouth(frefl, FT(M0), "rest_smile"); mouth(frefl, FT(44.6), "rest_creepy")
neck(refl, FT(M0), 0, 0, 0); neck(refl, FT(46.2), 0, 0, 0); neck(refl, FT(47.6), -6, 0, -32)
say(line(47.80), fmum, "rest_flat", "calm", P=mum); say(line(49.00), fmum, "rest_flat", "calm", P=mum)
neck(mum, FT(47.6), 0, 0, 0); neck(mum, FT(49.0), 0, 0, 8)       # a slight, slow head tilt
GL = HO + V((-4.49, 2.0, 5.0)); VIRT = V((2 * (HO.x - 4.49) - MUMH.x, MUMH.y, MUMH.z + 4.6))
shot("M1 It looked like Mum", M0, 42.2, [(0, HO + V((3.18, -9.0, 5.0)), GL, 30), (1, HO + V((2.9, -7.9, 5.0)), GL, 34)])
shot("M2 she stops smiling", 42.2, 44.5, [(0, HO + V((0.6, -2.0, 5.2)), H(mum), 46), (1, HO + V((0.7, -0.6, 5.1)), H(mum), 54)])
shot("M3 her reflection didn't", 44.5, 47.75, [(0, HO + V((0.5, -6.0, 5.0)), VIRT, 70), (1, HO + V((0.35, -5.4, 5.0)), VIRT, 84)], fstop=3.0)
shot("M4 who told you about the mirror", 47.75, SC["mirror"][1], [(0, HO + V((0.9, -1.0, 5.0)), H(mum), 50), (1, HO + V((1.0, 1.6, 5.0)), H(mum), 60)])
blinks(fm, M0, 51.7, every=2.6)
park(refl, FT(SC["mirror"][1])); park(mum, FT(SC["mirror"][1]))

# Part 1's room clock: tonight it already says 3:00 AM (2:59 hidden)
CLOCK_TEXTS["2:59 AM"].hide_render = True; CLOCK_TEXTS["3:00 AM"].hide_render = False
# ================================================================== 6-7  MILO'S BEDROOM 51.7-72.4 (night)
B0 = SC["bedroom"][0]
park(mum, FT(B0)); park(refl, FT(B0))
kf(ROOMFILL, "energy", 1, 0, interp="CONSTANT"); kf(ROOMFILL, "energy", FT(B0), 70, interp="CONSTANT")
kf(CLOSET_HINGE, "rotation_euler", FT(1.25), (0, 0, 0), interp="CONSTANT")
MB = V((1.5, -36.0, 0.4))
at(milo, FT(B0), MB + V((-0.8, 3.0, 0)), 0)
walk(milo, FT(B0), FT(53.2), MB + V((-0.8, 3.0, 0)), MB, steps=2, leg=18, z=0.4)       # backs away from the locked door
arms_down(milo, FT(53.3)); idle(milo, FT(53.4), FT(72.4), amp=0.012, base_z=0.4)
expr(fm, FT(B0), "scared"); expr(fm, FT(53.4), "notice"); expr(fm, FT(56.8), "scared"); expr(fm, FT(59.7), "shocked")
expr(fm, FT(62.5), "sad"); expr(fm, FT(64.3), "scared"); expr(fm, FT(65.3), "shocked"); expr(fm, FT(69.6), "scared")
neck(milo, FT(B0), 0, 0, 0); neck(milo, FT(56.9), 0, 0, 0); neck(milo, FT(58.6), 0, 0, -70)    # slowly turns to the closet
neck(milo, FT(65.1), 0, 0, -70); neck(milo, FT(65.8), 0, 0, 0)                                   # footsteps: back to the door
for tk in (67.90, 68.20, 68.48):                                                                 # flinch on each knock
    kf(milo["chest"], "rotation_euler", FT(tk) - 1, (0, 0, 0)); kf(milo["chest"], "rotation_euler", FT(tk) + 1, (DEG(-5), 0, 0))
    kf(milo["chest"], "rotation_euler", FT(tk) + 5, (0, 0, 0))
    kf(FRONT_DOOR, "rotation_euler", FT(tk) - 1, FD_ROT); kf(FRONT_DOOR, "rotation_euler", FT(tk), (FD_ROT[0], FD_ROT[1], FD_ROT[2] + DEG(0.6)))
    kf(FRONT_DOOR, "rotation_euler", FT(tk) + 3, FD_ROT)
say(line(64.30), fm, "rest_flat", "whisper")                                                     # "Mum?"
# closet: door eases open a crack, moonlight finds her hand + bangle on "I heard it too"
kf(CLOSET_HINGE, "rotation_euler", FT(57.8), (0, 0, 0)); kf(CLOSET_HINGE, "rotation_euler", FT(59.4), (0, 0, DEG(-9)))
kf(CLOSET_HINGE, "rotation_euler", FT(SC["black"][0]), (0, 0, DEG(-9)), interp="CONSTANT")
at(real, FT(B0), V((6.5, -47.9, 0.4)), 0)
arm(real, "Left", FT(B0), euler=(4, -6)); arm(real, "Left", FT(62.2), euler=(4, -6)); arm(real, "Left", FT(63.0), target=(-2.0, 2.2, 2.6))
arm(real, "Right", FT(B0), euler=(4, 6))
expr(freal, FT(B0), "scared"); mouth(freal, FT(B0), "rest_frown")
kf(CLOSET_IN, "energy", 1, 0, interp="CONSTANT"); kf(CLOSET_IN, "energy", FT(59.4), 0); kf(CLOSET_IN, "energy", FT(60.2), 160)
kf(CLOSET_IN, "energy", FT(65.1), 0, interp="CONSTANT")
park(real, FT(SC["black"][0]))
# the landing light comes on under the door with the footsteps; two shadows stop in it
key(DOORLINE_EM, "default_value", 0.0, 0.0); key(DOORLINE_EM, "default_value", 65.0, 0.0); key(DOORLINE_EM, "default_value", 65.6, 6.0)
key(DOORLINE_EM, "default_value", SC["black"][0] - 0.01, 6.0); key(DOORLINE_EM, "default_value", SC["black"][0], 0.0)
for o in FEET: vis_obj(o, 1, False); vis_obj(o, FT(67.45), True); vis_obj(o, FT(SC["black"][0]), False)
MHB = MB + V((0, 0, 4.6)); DOOR_IN = V((0, -30.6, 4.4)); CLOSET = V((5.6, -45.9, 4.2))
shot("B1 I locked my door", B0, 53.35, [(0, (6.0, -44.0, 5.6), MB + V((0, 2.5, 4.0)), 28), (1, (5.6, -43.0, 5.4), MB + V((0, 2.0, 4.0)), 30)])
shot("B2 Dinner's ready", 53.35, 56.55, [(0, MHB + V((1.3, 4.6, 0.3)), MHB, 46), (1, MHB + V((1.15, 4.0, 0.28)), MHB, 52)])
shot("B3 a voice in my closet", 56.55, 59.5, [(0, MHB + V((-1.6, 2.6, 0.6)), CLOSET, 32), (1, MHB + V((-1.2, 1.6, 0.4)), CLOSET, 40)])
shot("B4 the crack: her hand", 59.5, 64.2, [(0, (1.3, -39.2, 4.3), (4.6, -45.5, 3.4), 42), (1, (1.9, -40.4, 4.2), (4.6, -45.6, 3.4), 50)], fstop=2.4)
shot("B5 Mum?", 64.2, 65.1, [(0, MHB + V((3.8, 1.2, 0.2)), MHB, 56), (1, MHB + V((3.5, 1.1, 0.2)), MHB, 60)])
shot("B6 footsteps + knocks", 65.1, 69.45, [(0, (-7.2, -46.5, 7.0), (0.8, -34.0, 3.4), 24), (1, (-6.6, -45.5, 6.6), (0.6, -33.5, 3.4), 26)])
shot("B7 Who are you talking to?", 69.45, SC["bedroom"][1], [(0, (4.6, -37.5, 1.7), (0, -30.6, 1.4), 34), (1, (4.2, -35.8, 1.8), (0, -30.6, 1.5), 44)], fstop=2.2)
blinks(fm, B0, 72.4, every=2.4, ph=0.3); blinks(freal, B0, 72.4, every=3.6)
shot("Z black", SC["black"][0], SC["black"][1], [(0, (0, -40, 5), (0, -30, 5), 30)])

# ================================================================== 8  OUTRO 73.0-80.0: to camera, both doors behind him
O0 = SC["outro"][0]
O = V((3.0, -38.6, 0.4))
at(milo, FT(O0), O, 0)
kf(MKEY, "energy", 1, 0, interp="CONSTANT"); kf(MKEY, "energy", FT(O0), 500, interp="CONSTANT")
kf(MRIM, "energy", 1, 0, interp="CONSTANT"); kf(MRIM, "energy", FT(O0), 300, interp="CONSTANT")
kf(CLOSET_HINGE, "rotation_euler", FT(O0), (0, 0, DEG(-6)), interp="CONSTANT")
expr(fm, FT(O0), "ominous"); expr(fm, FT(75.1), "curious"); expr(fm, FT(76.0), "question"); expr(fm, FT(76.9), "excited"); expr(fm, FT(78.6), "sly")
for t in (73.25, 75.20, 76.90):
    say(line(t), fm, "rest_flat" if t < 76 else "rest_smile", "whisper" if t < 75 else ("calm" if t < 76 else "excited"), nod=4.5, P=milo)
mouth(fm, FT(79.5), "rest_creepy")
for t, lean in ((73.0, 0), (74.9, -6), (76.8, -2), (78.5, -9), (80.0, -10)): chest(milo, FT(t), lean, 0, 0)
arms_down(milo, FT(O0)); arm(milo, "Right", FT(73.9), euler=(70, -10)); arm(milo, "Right", FT(74.5), euler=(8, 6))   # "One door." - points back
arm(milo, "Left", FT(73.25), euler=(60, 20)); arm(milo, "Left", FT(73.8), euler=(6, -6))                              # "Two mums." - a hand up
idle(milo, FT(O0), NF, amp=0.015, base_z=0.4)
OH = O + V((0, 0, 4.6))
shot("O outro", O0, E2["total"], [(0, OH + V((0, 6.6, 0.2)), OH + V((0, 0, -0.2)), 34), (0.55, OH + V((0, 5.4, 0.15)), OH + V((0, 0, -0.15)), 38),
                                  (1, OH + V((0, 4.6, 0.1)), OH + V((0, 0, -0.1)), 42)])
blinks(fm, O0, E2["total"], every=2.9, ph=0.2)

# ================================================================== finish
CUT_FR = [f0 for _, f0, _ in SHOTS[1:]]
apply_blinks()
flush_mouths(); apply_interp(); hold_cuts(); apply_interpolation()


def check_faces():
    probs = []
    for nm_, rig in RIGS.items():
        curves = {}
        for k, objs in rig["mouths"].items():
            fc = [c for c in _fcurves(objs[0]) if c.data_path == "hide_render"]
            curves[k] = fc[0] if fc else None
        for fr in range(1, NF + 1):
            on = [k for k, c in curves.items() if c is not None and c.evaluate(fr) < 0.5]
            if len(on) != 1: probs.append((nm_, fr, on))
    for nm_, rig in RIGS.items():
        for side in ("L", "R"):
            fc = [c for c in _fcurves(rig["blink" + side]) if c.data_path == "scale" and c.array_index == 2]
            if fc:
                for cut in CUT_FR:
                    if any(fc[0].evaluate(f) < 0.9 for f in range(cut - 4, cut)): probs.append(("eyes closed before cut", nm_, cut))
    return probs


probs = check_faces()
print("FACE CHECK", "OK" if not probs else probs[:20])
json.dump({"shots": SHOTS, "nf": NF}, open("/home/claude/talk/shots_p2.json", "w"))
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
try: s.cycles.denoiser = "OPTIX" if eng == "GPU" else "OPENIMAGEDENOISE"
except Exception: pass
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
