# part3.py - BLOXBURY Part 3 "Don't Say It". 24 fps, rig v2 faces, library cast/sets/props 1-6, cinema shots,
# LIGHTING.md recipe (keyed per shot) + lookdev grade. Audio/cues/captions: prep_p3.py -> OUT_DIR {env_p3.json, part3_audio.wav, captions_p3.ass}
# Preview: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 part3.py      Pod: ENGINE=GPU RENDER=1 RX=1080 RY=1920 blender -b --python part3.py
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
# Part 3: sash window in Milo's RIGHT wall (faces Rae's): hole 4 wide (local z -6.5..-2.5) x 4 tall (4..8)
_wr = 'box("WallRight", RS(T, H, D), R(W / 2 - T / 2, H / 2, 0), m_wall, parent=root)'
assert pre.count(_wr) == 1
pre = pre.replace(_wr, 'box("WallRight", RS(T, H, 3.5), R(W / 2 - T / 2, H / 2, -8.25), m_wall, parent=root); '
                       'box("WallRight", RS(T, H, 12.5), R(W / 2 - T / 2, H / 2, 3.75), m_wall, parent=root); '
                       'box("WallRight", RS(T, 4, 4), R(W / 2 - T / 2, 2, -4.5), m_wall, parent=root); '
                       'box("WallRight", RS(T, H - 8, 4), R(W / 2 - T / 2, 8 + (H - 8) / 2, -4.5), m_wall, parent=root)')
exec(pre)
exec(src[src.index("# ---------------------------------------------------------------- TREES + HILLS"):
         src.index("# ---------------------------------------------------------------- CAMERA")])
RB = R                                    # Roblox coords (x, up, z) -> Blender
FPS = 24; WARP = []                       # old helpers (key/F/set_day) now run on the 24 fps timeline, no warp
for f in ("charlib", "stylelab", "hair2", "hair3", "faces2", "garments", "garments2", "hair4", "faces3", "faces4", "props"):
    exec(open(LIB + f + ".py").read())
V = Vector
ENV = json.load(open(os.environ.get("ENV_P3", "/home/claude/talk/env_p3.json"))); E2 = dict(ENV); ENV["rms"] = E2["rms"]["milo"]; ENV["cen"] = E2["cen"]["milo"]
exec(open(SCR + "rig2.py").read())       # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ... (R = radians now)
exec(open(LIB + "monster.py").read())    # THE KNOCKER (studio library)
DEG = math.radians
OUT = os.environ.get("OUT", "/home/claude/talk/frames_p3")
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
milo = make_milo(); rae = make_rae(); real = make_mum("RealMum")
CAST = (milo, rae, real)
for P in CAST: strip_faces(P)
for o in bpy.data.objects: o.animation_data_clear()
for P in CAST: upgrade_rig(P)
fm, frae, freal = (build_face_v2(P) for P in CAST)
RIGS = {"milo": fm, "rae": frae, "real": freal}
for rig, rest in ((fm, "rest_flat"), (frae, "rest_flat"), (freal, "rest_frown")):
    mouth(rig, 1, rest)
for P in CAST: place(P, 1, FAR + V((CAST.index(P) * 12, 0, 0)))


def park(P, fr):
    place(P, fr, FAR + V((CAST.index(P) * 12, 0, 0)))


def pose(P, loc, yaw):
    P["root"].location = V(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


area = p3_area

# ------------------------------------------------------------------ sets + Part 3 props (library batch 6)
exec(open(LIB + "props4.py").read()); dress_bedroom()
exec(open(LIB + "props5.py").read()); detail_town(houses)
exec(open(LIB + "props6.py").read())
p3_hollow_closet()
FRONT_DOOR = [o for o in bpy.data.objects if o.name.startswith("FrontDoor")][0]
BDOOR = p6_bedroom_door(FRONT_DOOR)
GAP = p6_light_gap(FRONT_DOOR)
FD_ROT = tuple(FRONT_DOOR.rotation_euler)
DRAW = p6_drawing("Drawing", (-7.0, -49.0, 0.4), (0, 1, 0), z=7.0, w=3.0)
NOTE_XY = V((4.4, -43.4, 0.43))
NOTE = p6_note("Note", NOTE_XY, (0, 0, DEG(-12)))
# a blank page over the written front while he writes (swapped off when the word is done)
from PIL import Image as _Im, ImageDraw as _Dr
_b = _Im.open("/tmp/p6_note_front.png").convert("RGBA"); _bd = _Dr.Draw(_b)
_bd.rectangle((80, 230, 520, 540), fill=(248, 245, 232, 255))
for y in range(274, 540, 46): _bd.line((80, y, 520, y), fill=(170, 195, 225, 255), width=2)
_b.save("/tmp/p6_note_blank.png")
NOTE_BLANK = plane("NoteBlank", 1.1, 1.42, V((0, 0, 0.02)), imgmat("NoteBlankM", "/tmp/p6_note_blank.png", rough=0.9), NOTE, rot=(DEG(90), 0, 0))
PENCIL = p6_pencil("Pencil", (3.6, -42.7, 0.46), (0, 0, DEG(35)))
SWIN = p6_side_window("SideWin", x_in=11.0, yc=-35.5, sill=4.4, open_u=0.0)
SW_LOWER = bpy.data.objects[SWIN["lower"]]; SW_Z0 = 4.4 + 1.0
FGAP, _gone = p6_fence_gap()
RO = V((720, 0, 400)); RAE_SET, RAE_HINGE = p6_rae_door_set(RO)
TORCH = p6_torch("Torch", rae["tiltRight"]); TORCH.location = (0, 0.35, 0.05)
TORCH_BEAM = bpy.data.objects[TORCH["beam"]]
PHONE = p6_phone("Phone", rae["tiltLeft"]); PHONE.location = (0, 0.5, 0.25)
PH_SCREEN_M = bpy.data.materials["PhoneScreenImg"]
BRANCH = p6_branches("Branches")
KN = make_knocker("Knocker", 10.5); KR = KN["root"]; KR.location = FAR     # rewatch bait: 4 frames in Milo's window
CLOCK_TEXTS["2:59 AM"].hide_render = True; CLOCK_TEXTS["3:00 AM"].hide_render = False
M_RED_TEXT.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.2     # red 3AM clock: an accent
for o in [o for o in bpy.data.objects if o.name.startswith(("DoorLight", "FootShadow"))]: o.hide_render = True

# ------------------------------------------------------------------ CINEMATIC NIGHT LIGHTING (LIGHTING.md), keyed per shot
exec(open(LIB + "lookdev.py").read()); cinematic_look(exposure=0.9, bloom=0.55, vignette=0.3)


def spot(name, loc, tgt, energy, size_deg, radius, col):
    d = bpy.data.lights.new(name, "SPOT"); d.energy = 0; d.spot_size = DEG(size_deg); d.spot_blend = 0.25
    d.shadow_soft_size = radius; d.color = col
    o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = V(loc)
    o.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler(); return d


LIGHTS = {
    "MoonSpot": spot("MoonSpot", (24.0, -34.0, 13.0), (-2.0, -39.0, 1.5), 0, 38, 0.15, (0.72, 0.8, 1.0)),
    "MoonIn": area("MoonIn", (16.0, -35.5, 9.0), (2.0, -38.0, 2.5), 0, 5, (0.62, 0.72, 1.0)),
    "DoorPrac": area("DoorPrac", (0.0, -31.0, 0.6), (-4.0, -38.0, 3.5), 0, 3, (1.0, 0.72, 0.45)),
    "RoomFillA": area("RoomFillA", (0.0, -40.0, 13.0), (0.0, -40.0, 0.0), 0, 10, (0.5, 0.58, 0.9)),
    "FairyGlow": area("FairyGlow", (-6.8, -47.6, 10.2), (-7.0, -49.0, 6.5), 0, 2.0, (1.0, 0.78, 0.5)),
    "FairyRim": area("FairyRim", (-6.6, -47.8, 10.0), (-6.2, -39.6, 5.0), 0, 1.5, (1.0, 0.72, 0.42)),
    "ClosetIn": area("ClosetIn", (3.2, -43.6, 6.2), (4.5, -45.7, 3.2), 0, 0.8, (0.7, 0.78, 1.0)),
    "Sodium": spot("Sodium", (31.0, -30.0, 11.0), (24.2, -37.0, 4.0), 0, 22, 0.3, (1.0, 0.55, 0.22)),
    "YardRim": area("YardRim", (15.0, -39.0, 12.0), (24.2, -37.0, 4.8), 0, 2.5, (0.62, 0.74, 1.0)),
    "WinGlow": area("WinGlow", (13.2, -35.5, 6.2), (22.0, -36.0, 1.5), 0, 3.5, (1.0, 0.75, 0.5)),
    "RunKey": spot("RunKey", (42.0, -18.0, 16.0), (40.0, -30.0, 3.0), 0, 40, 0.3, (1.0, 0.58, 0.26)),
    "RaeMoon": area("RaeMoon", RO + V((-14, -16, 16)), RO + V((0, 0, 4)), 0, 8, (0.6, 0.7, 1.0)),
    "RaeRim": area("RaeRim", RO + V((6, -3, 11)), RO + V((-1.6, -6.2, 4.8)), 0, 2, (0.62, 0.72, 1.0)),
    "MiloKeyR": area("MiloKeyR", RO + V((-3.0, -2.5, 8.0)), RO + V((-1.6, -6.2, 4.8)), 0, 1.5, (1.0, 0.76, 0.5)),
}
_LOBJ = {k: [o for o in bpy.data.objects if o.data == d][0] for k, d in LIGHTS.items()}
_LAMPS = [o.data for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("LampLight")]
_LAMP0 = [(d.energy, tuple(d.color)) for d in _LAMPS]


def look_at(o, tgt): return (V(tgt) - o.location).to_track_quat("-Z", "Y").to_euler()


def light_shot(t, exposure=0.9, sun=None, lamps=None, room=0, moon_from=(24.0, -34.0, 13.0), moon_at=(-2.0, -39.0, 1.5),
               cookie_at=None, **en):
    """Key the whole lighting state for the shot that starts at t (CONSTANT: it holds until the next call)."""
    fr = FT(t)
    for k, d in LIGHTS.items(): kf(d, "energy", fr, en.get(k, 0), interp="CONSTANT")
    mo = _LOBJ["MoonSpot"]; kf(mo, "location", fr, V(moon_from), interp="CONSTANT")
    kf(mo, "rotation_euler", fr, look_at(mo, moon_at), interp="CONSTANT")
    if cookie_at is not None:                                   # branch cookie on the moon's line, just outside the window
        a, b = V(moon_from), V(cookie_at); u = (a.x - 15.6) / (a.x - b.x)
        kf(BRANCH, "location", fr, a.lerp(b, u) + V((0, 0.9, 0.7)), interp="CONSTANT")
    else: kf(BRANCH, "location", fr, V((3000, 3000, -900)), interp="CONSTANT")
    for d, (e0, c0) in zip(_LAMPS, _LAMP0):
        kf(d, "energy", fr, e0 if lamps is None else lamps[0], interp="CONSTANT")
        kf(d, "color", fr, c0 if lamps is None else lamps[1], interp="CONSTANT")
    kf(sun_data, "energy", fr, 0.6 if sun is None else sun, interp="CONSTANT")
    kf(MILO_LIGHT, "energy", fr, room, interp="CONSTANT")
    s.view_settings.exposure = exposure; s.keyframe_insert("view_settings.exposure", frame=fr)
    _LOG.append((s, "view_settings.exposure", fr, "CONSTANT"))


def sway(t0, t1, amp=2.5):
    """Branches move in a light wind: slow, uneven sway (the cookie shadows drift across the room)."""
    for k, fr in enumerate(range(FT(t0), FT(t1) + 1, 9)):
        tt = fr / FPS
        kf(BRANCH, "rotation_euler", fr, (DEG(amp * math.sin(tt * 1.3)), DEG(amp * 0.6 * math.sin(tt * 0.9 + 1)), DEG(amp * 0.8 * math.sin(tt * 0.7))))


def sit(P, fr, loc, yaw):
    place(P, fr, loc, yaw)
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (DEG(90), 0, 0), interp="CONSTANT")


def stand(P, fr):
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (0, 0, 0), interp="CONSTANT")


set_night(0.0); house_lights(0.0, False)

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

exec(open(SCR + "cinema.py").read())          # camera grammar: cine() / insert() / check_framing()



# ================================================================== SHOTS (times from env_p3 scenes; captions/lines from prep_p3)
ALLOW = ()
MB = V((-6.2, -39.6, 0.55)); MYAW = -34                      # Milo on the bed edge, facing the door
FWD = V((math.sin(DEG(-MYAW)), math.cos(DEG(-MYAW)), 0)); LEFT = V((-FWD.y, FWD.x, 0))
DOOR_LOW = V((0.0, -30.8, 0.9)); DOOR_MID = V((0.0, -30.7, 5.0))
CLOSET = V((4.6, -45.6, 3.4))
HOOK_LIGHT = dict(MoonSpot=45000, DoorPrac=30, RoomFillA=8, FairyRim=140, moon_from=(24.0, -32.8, 9.7), moon_at=(-6.2, -39.6, 4.9),
                  cookie_at=(-6.2, -39.6, 4.8))
for P in CAST: arms_down(P, 1)
sway(0, SC["escape"][0] + 2)

# ---------------- 0  HOOK 0.00-3.15: lit + readable from frame 0; voice at 0.1 s; cut at ~1.6 s
sit(milo, 1, MB, MYAW)
arm(milo, "Right", 1, target=(-1.3, 1.6, 5.4)); arm(milo, "Left", 1, target=(-0.6, 1.4, 2.6))   # hand clamped over his mouth
expr(fm, 1, "scared"); mouth(fm, 1, "rest_frown")
idle(milo, 1, FT(SC["door_feet"][1]), amp=0.01, base_z=MB.z)
light_shot(0.0, **HOOK_LIGHT)
cine("H1 hand over mouth", 0.0, 1.6, milo, u=FWD + LEFT * 0.45, size="CU", move="push", amt=1.15, lens=46, sx=0.04)
cine("H2 three hours", 1.6, 3.15, milo, u=FWD * 0.8 - LEFT * 0.6, size="MS", move="drift", amt=6, lens=30, sy=0.16, sx=0.1)
blinks(fm, 0.0, 10.0, every=2.6)

# ---------------- 1  DOOR + FEET 3.15-9.97: the feet arrive at 3.45 (something wrong by ~3.5 s), knocks ~7.7, "Bug?" 8.77
gap_feet(GAP, False, 1); gap_feet(GAP, True, FT(3.45)); gap_feet(GAP, False, FT(SC["closet_crack"][0]))
gap_feet(GAP, True, FT(SC["door_ask"][0])); gap_feet(GAP, False, FT(SC["milo_push"][1]))
light_shot(3.15, MoonSpot=5000, RoomFillA=25, moon_at=(-1.5, -31.0, 2.0))
shot("D1 insert: the gap", 3.15, 5.1, [(0, V((1.7, -37.6, 1.2)), DOOR_LOW, 32), (0.8, V((1.55, -36.6, 1.15)), DOOR_LOW, 32)], fstop=3.5)
light_shot(5.1, **HOOK_LIGHT)
cine("D2 he stares at the door", 5.1, 7.55, milo, u=FWD + LEFT * 0.2, size="MCU", move="push", amt=1.2, lens=40, sx=-0.06)
light_shot(7.55, MoonSpot=9000, RoomFillA=70)
shot("D3 knocks / Bug?", 7.55, SC["door_feet"][1], [(0, V((0.6, -41.5, 5.2)), DOOR_MID, 30), (0.85, V((0.55, -40.6, 5.1)), DOOR_MID, 30)])
for tk in (7.78, 8.02, 8.26):                                                    # the door shivers on each soft knock
    kf(FRONT_DOOR, "rotation_euler", FT(tk) - 1, FD_ROT); kf(FRONT_DOOR, "rotation_euler", FT(tk), (FD_ROT[0], FD_ROT[1], FD_ROT[2] + DEG(0.5)))
    kf(FRONT_DOOR, "rotation_euler", FT(tk) + 3, FD_ROT)

# ---------------- milo_close 9.97-15.35: "Last night it didn't know that word / Then it heard Mum say it"
light_shot(SC["milo_close"][0], **HOOK_LIGHT)
expr(fm, FT(10.0), "scared"); expr(fm, FT(13.2), "shocked")
neck(milo, FT(10.0), 0, 0, 0); neck(milo, FT(13.0), 0, 0, 0); neck(milo, FT(14.2), 0, 0, -38)     # turns to the closet
cine("C1 it didn't know that word", SC["milo_close"][0], SC["milo_close"][1], milo, u=FWD + LEFT * 0.35, size="CU", move="push", amt=1.2, lens=55, sx=0.05)
blinks(fm, 10.0, 15.3, every=2.8, ph=0.5)

# ---------------- closet_crack 15.35-19.85: moonlight finds her hand + bracelet in the crack
C0 = SC["closet_crack"][0]
kf(CLOSET_HINGE, "rotation_euler", 1, (0, 0, 0), interp="CONSTANT")
kf(CLOSET_HINGE, "rotation_euler", FT(C0), (0, 0, DEG(-5))); kf(CLOSET_HINGE, "rotation_euler", FT(C0 + 1.2), (0, 0, DEG(-9)))
at(real, FT(C0), V((6.5, -47.9, 0.4)), 0)
arm(real, "Left", FT(C0), target=(-2.0, 2.2, 2.6)); arm(real, "Right", FT(C0), euler=(4, 6))
expr(freal, FT(C0), "scared"); mouth(freal, FT(C0), "rest_frown")
light_shot(C0, ClosetIn=320, MoonSpot=4000, RoomFillA=15, moon_from=(24.0, -22.0, 18.0), moon_at=(4.6, -45.0, 2.5), cookie_at=(4.6, -45.0, 2.5))
shot("K1 the crack: her hand", C0, SC["closet_crack"][1], [(0, V((1.3, -39.2, 4.3)), CLOSET, 46), (0.8, V((2.0, -40.9, 4.2)), CLOSET + V((0, -0.1, 0)), 46)], fstop=2.4)
park(real, FT(SC["closet_crack"][1]))

# ---------------- rules_drawing 19.85-28.73: Mum's three rules; the drawing (LIGHTHOUSE hidden in the beam)
R0 = SC["rules_drawing"][0]
light_shot(R0, **HOOK_LIGHT)
neck(milo, FT(R0), 0, 0, -38); neck(milo, FT(R0 + 1.2), 0, 0, 30)                                  # looks up at his drawing
expr(fm, FT(R0), "sad")
cine("R1 Mum had three rules", R0, 22.1, milo, u=FWD * 0.3 + LEFT, size="MCU", move="hold", lens=36, sx=0.1)
DRW = V((-7.0, -48.94, 7.0))
light_shot(22.1, FairyGlow=70, RoomFillA=8, exposure=-0.2)
insert("R2 the drawing", 22.1, SC["rules_drawing"][1], DRW, DRW + V((0.75, 0, 0.62)), (0, 1, 0), 3.4, 1.7, lens=45, land=0.8)   # whole page -> the beam

# ---------------- door_ask 28.73-34.49 (MUSIC OUT): "Bug... if it's really you in there... tell me our word."
A0 = SC["door_ask"][0]
light_shot(A0, MoonSpot=5000, RoomFillA=12, moon_at=(-1.5, -31.0, 2.0))
shot("A1 the feet wait", A0, 31.4, [(0, V((1.4, -36.4, 1.0)), DOOR_LOW, 28), (1.0, V((1.4, -36.1, 1.0)), DOOR_LOW, 28)], fstop=3.5)   # near-static: dread
light_shot(31.4, **HOOK_LIGHT)
neck(milo, FT(29.0), 0, 0, 0)
expr(fm, FT(31.4), "shocked")
cine("A2 tell me our word", 31.4, SC["door_ask"][1], milo, u=FWD + LEFT * 0.5, size="ECU", move="sink", amt=6, lens=70, sx=0.0, sy=0.1)

# ---------------- milo_push 34.49-37.86: "It wasn't checking me. It was learning."
light_shot(SC["milo_push"][0], **HOOK_LIGHT)
expr(fm, FT(34.6), "scared"); expr(fm, FT(36.5), "ominous")
arm(milo, "Right", FT(36.0), target=(-1.3, 1.6, 5.4)); arm(milo, "Right", FT(36.8), euler=(6, 6))     # the hand comes down: a plan
cine("P1 it was learning", SC["milo_push"][0], SC["milo_push"][1], milo, u=FWD - LEFT * 0.3, size="MCU", move="push", amt=1.25, lens=50, sx=-0.08)
blinks(fm, 34.5, 37.8, every=2.0)

# ---------------- note 37.86-46.47: writes LIGHTHOUSE, pushes it into the crack, it comes back: WINDOW. RAE'S. GO.
N0 = SC["note"][0]
MF = V((4.4, -41.4, 0.42))
sit(milo, FT(N0), MF, 180)                                     # on the floor facing the closet
arm(milo, "Right", FT(N0), target=(0.4, 1.9, 0.9)); arm(milo, "Left", FT(N0), target=(-0.8, 1.6, 1.4))
for k, fr in enumerate(range(FT(39.9), FT(42.6), 3)):          # writing: small pencil strokes
    arm(milo, "Right", fr, target=(0.4 + 0.12 * math.sin(k * 1.7), 1.9 + 0.05 * math.cos(k * 2.3), 0.9))
kf(PENCIL, "location", FT(N0), V((3.95, -42.75, 0.46)), interp="CONSTANT")
vis_obj(NOTE_BLANK, 1, True); vis_obj(NOTE_BLANK, FT(42.45), False)
expr(fm, FT(N0), "nervous"); expr(fm, FT(42.6), "scared")
light_shot(N0, exposure=1.35, MoonSpot=9000, RoomFillA=170, DoorPrac=140, moon_from=(24.0, -22.0, 18.0), moon_at=(4.5, -43.3, 0.4), cookie_at=(4.5, -43.3, 0.4))
cine("N1 so I didn't say it", N0, 40.0, milo, u=V((0.5, 1, 0)), size="MS", move="drift", amt=6, lens=26, sy=0.2, sx=-0.12)
insert("N2 he writes it down", 40.0, 42.75, NOTE_XY + V((0, 0, 0.02)), NOTE_XY + V((0, 0, 0.02)), (0.9, 0.15, 1), 2.4, 1.9, lens=40, land=0.85, fstop=4.0)   # from his right side, clear of his head
# slide: into the crack (42.77-43.77), silence, back out FLIPPED (44.67-45.97)
IN_PT = V((4.75, -45.55, 0.43)); OUT_PT = V((4.45, -43.9, 0.43))
kf(NOTE, "location", FT(42.75), NOTE_XY); kf(NOTE, "location", FT(43.75), IN_PT)
kf(NOTE, "rotation_euler", FT(42.75), (0, 0, DEG(-12))); kf(NOTE, "rotation_euler", FT(43.75), (0, 0, DEG(-4)))
kf(NOTE, "location", FT(44.6), IN_PT, interp="CONSTANT"); kf(NOTE, "rotation_euler", FT(44.6), (0, DEG(180), DEG(176)), interp="CONSTANT")
kf(NOTE, "location", FT(44.67), IN_PT); kf(NOTE, "location", FT(45.95), OUT_PT)
arm(milo, "Right", FT(42.75), target=(0.4, 1.9, 0.9)); arm(milo, "Right", FT(43.6), target=(0.3, 2.3, 0.7)); arm(milo, "Right", FT(44.2), euler=(20, 10))
shot("N3 into the crack", 42.75, 44.55, [(0, V((3.0, -41.6, 1.6)), V((4.6, -45.3, 0.6)), 32), (0.85, V((3.1, -42.0, 1.55)), V((4.6, -45.4, 0.6)), 32)], fstop=3.2)
insert("N4 WINDOW. RAE'S. GO.", 44.55, SC["note"][1], OUT_PT + V((0, -0.5, 0.02)), OUT_PT + V((0, 0, 0.02)), (0, 0, 1), 2.6, 1.7, lens=40, land=0.85, fstop=4.0)
blinks(fm, N0, 44.5, every=2.7)

# ---------------- escape 46.47-52.50: the window, the fence gap (Knocker in his window: 4 frames), the run to Rae's
E0 = SC["escape"][0]
stand(milo, FT(E0))
at(milo, FT(E0), V((9.2, -35.5, 0.4)), -90); arms_down(milo, FT(E0))
arm(milo, "Right", FT(E0), target=(0.6, 1.8, 6.0)); arm(milo, "Left", FT(E0), target=(-0.6, 1.8, 6.0))     # both hands lift the sash
kf(SW_LOWER, "location", 1, (SW_LOWER.location.x, SW_LOWER.location.y, SW_Z0), interp="CONSTANT")
kf(SW_LOWER, "location", FT(E0), (SW_LOWER.location.x, SW_LOWER.location.y, SW_Z0))
kf(SW_LOWER, "location", FT(E0 + 1.4), (SW_LOWER.location.x, SW_LOWER.location.y, SW_Z0 + 1.6))
expr(fm, FT(E0), "nervous")
light_shot(E0, MoonSpot=9000, RoomFillA=60, MoonIn=420, moon_from=(24.0, -32.8, 9.0), moon_at=(8.0, -35.5, 4.0), cookie_at=(8.0, -35.5, 4.0))
cine("E1 the window", E0, 48.5, milo, u=V((-1, -0.35, 0)), size="MS", move="push", amt=1.2, lens=30, sy=0.12)
TE1 = 48.5
light_shot(TE1, YardMoon=0, WinGlow=260, room=300, Sodium=14000, YardRim=650, exposure=0.3, sun=0.18, lamps=(2600, (1.0, 0.6, 0.28)))
at(milo, FT(TE1), V((21.5, -36.8, 0.0)), -90); arms_down(milo, FT(TE1))
walk(milo, FT(TE1), FT(50.6), V((21.5, -36.8, 0.0)), V((26.0, -37.0, 0.0)), steps=3, leg=28)     # ducks through the gap
kf(KR, "location", FT(49.3), V((8.6, -35.5, 0.4)), interp="CONSTANT"); kf(KR, "rotation_euler", FT(49.3), (0, 0, DEG(-90)), interp="CONSTANT")
kf(KR, "location", FT(49.3) + 4, FAR, interp="CONSTANT"); kf(KR, "location", 1, FAR, interp="CONSTANT")
expr(fm, FT(TE1), "scared")
shot("E2 the fence gap", TE1, 50.6, [(0, V((33.0, -43.5, 4.4)), V((21.8, -36.8, 3.6)), 26), (1, V((33.4, -42.6, 4.4)), V((26.0, -37.0, 3.6)), 26)])   # pans with him through the gap; his window stays in frame
TE2 = 50.6
light_shot(TE2, RunKey=30000, exposure=0.3, sun=0.18, lamps=(2600, (1.0, 0.6, 0.28)))
walk(milo, FT(TE2), FT(SC["escape"][1]), V((29.0, -35.0, 0.0)), V((44.0, -27.5, 0.0)), steps=5, leg=36)
shot("E3 the run", TE2, SC["escape"][1], [(0, V((36.0, -12.0, 5.5)), V((30.0, -34.0, 3.0)), 24), (1, V((38.5, -13.0, 5.2)), V((43.0, -28.5, 3.0)), 24)])   # pans with him: a tracking shot

# ---------------- rae_door 52.50-60.70: "Milo? You just called me. You said the word. Lighthouse."
D0 = SC["rae_door"][0]
RAE = RO + V((0.5, -0.2, 0.5)); MILO_P = RO + V((-1.6, -6.2, 0.5))
at(rae, FT(D0), RAE, 190); at(milo, FT(D0), MILO_P, 8)
arm(rae, "Right", FT(D0), target=(0.6, 1.6, 3.4)); arm(rae, "Left", FT(D0), euler=(4, -6))
idle_here(rae, FT(D0), FT(SC["phone"][1]), amp=0.012, ph=1.0); idle_here(milo, FT(D0), FT(SC["phone"][1]))
arm(milo, "Right", FT(D0), target=(-1.3, 1.6, 5.4)); arm(milo, "Left", FT(D0), euler=(4, -6))              # hand still over his mouth
expr(frae, FT(D0), "nervous"); expr(frae, FT(56.7), "scared"); expr(frae, FT(59.0), "ominous")
expr(fm, FT(D0), "scared"); expr(fm, FT(59.2), "shocked")
for t in (52.85, 54.52, 56.76, 59.10): say(line(t), frae, "rest_flat", "whisper" if t > 59 else "calm", nod=2.5, P=rae)
light_shot(D0, RaeMoon=140, RaeRim=520, MiloKeyR=60)
cine("RD1 Milo? You just called me", D0, 55.9, rae, toward=milo, ang=24, size="MCU", move="drift", amt=6, lens=36, sx=-0.08)
cine("RD2 You said the word", 55.9, 58.95, rae, toward=milo, ang=30, size="CU", move="push", amt=1.2, lens=55, sx=-0.06)
cine("RD3 Lighthouse.", 58.95, SC["rae_door"][1], milo, toward=rae, ang=-28, size="CU", move="hold", lens=60, sx=0.08)     # the word lands on HIS face
blinks(frae, D0, 76.9, every=3.4, ph=1.1)

# ---------------- milo_realise 60.70-73.26: narration on Milo; phone buzz 72.06 (the one startle, in silence)
Q0 = SC["milo_realise"][0]
arm(milo, "Right", FT(Q0), target=(-1.3, 1.6, 5.4)); arm(milo, "Right", FT(Q0 + 0.8), euler=(6, 6))           # the hand drops
expr(fm, FT(Q0), "shocked"); expr(fm, FT(65.5), "sad"); expr(fm, FT(68.0), "scared")
neck(milo, FT(65.4), 0, 0, 0); neck(milo, FT(66.4), 0, 0, 55); neck(milo, FT(67.6), 0, 0, 0)                 # looks back toward his house
cine("Q1 I never said it out loud", Q0, 65.4, milo, toward=rae, ang=-22, size="CU", move="push", amt=1.2, lens=55, sx=0.06)
cine("Q2 I gave it to the closet", 65.4, 67.9, milo, u=V((0.85, 0.6, 0)), size="MCU", move="hold", lens=40, sx=-0.1)
cine("Q3 Most of you told me", 67.9, 72.0, milo, u=V((0.15, 1, 0)), size="CU", move="drift", amt=5, lens=30)      # almost to us: the comments line
light_shot(Q0, RaeMoon=140, RaeRim=520, MiloKeyR=110)
# phone: buzz 72.06 -> Rae looks down, raises it; the screen: Milo calling
arm(rae, "Left", FT(72.1), euler=(4, -6)); arm(rae, "Left", FT(72.6), target=(-0.4, 1.4, 3.6))
neck(rae, FT(72.1), 0, 0, 0); neck(rae, FT(72.5), 20, 0, 0)
expr(frae, FT(72.1), "notice"); expr(frae, FT(73.6), "shocked")
kf(PHONE, "rotation_euler", 1, (0, 0, 0), interp="CONSTANT"); kf(PHONE, "rotation_euler", FT(72.9), (0, 0, 0)); kf(PHONE, "rotation_euler", FT(73.4), (0, 0, DEG(180)))   # she turns the screen to Milo
cine("F1 the buzz", 72.0, 73.55, rae, toward=milo, ang=34, size="MS", move="hold", lens=36, sy=0.2, sx=-0.05)
light_shot(73.55, RaeMoon=120, MiloKeyR=60)
s.frame_set(FT(74.0)); bpy.context.view_layer.update(); PP = PHONE.matrix_world.translation.copy()
shot("F2 Rae, it's me", 73.55, 75.35, [(0, PP + V((-0.35, -2.4, 0.4)), PP + V((0, 0, 0.1)), 40), (0.85, PP + V((-0.3, -2.0, 0.35)), PP + V((0, 0, 0.1)), 40)], fstop=2.4)
neck(rae, FT(75.3), 20, 0, 0); neck(rae, FT(75.9), -4, 0, 0)                                                   # looks up at Milo
cine("F3 Don't let him in", 75.35, SC["phone"][1], rae, toward=milo, ang=18, size="CU", move="push", amt=1.15, lens=60, sx=-0.04)
blinks(fm, Q0, 76.9, every=2.9, ph=0.4)

# ---------------- black 76.96-77.66
blk = plane("Blackout", 4, 4, V((0, 0, 0)), pmat("BlackCard", (0, 0, 0), rough=1.0), cam)
blk.location = (0, 0, -0.3); blk.rotation_euler = (DEG(90), 0, 0); blk.visible_shadow = False
for fr_b, on in ((1, False), (FT(E2["black_cut"]), True), (FT(E2["outro0"]), False)):
    kf(blk, "hide_render", fr_b, not on, interp="CONSTANT")
shot("Z black", SC["black"][0], SC["black"][1], [(0, RO + V((0, -14, 5)), RO + V((0, 0, 5)), 30)])

# ---------------- outro 77.66-84.24: to camera on Rae's porch, the porch lamp on him
O0 = SC["outro"][0]
park(rae, FT(O0))
at(milo, FT(O0), RO + V((0.0, -4.8, 0.5)), 0)
arms_down(milo, FT(O0))
light_shot(O0, RaeMoon=260, RaeRim=420, MiloKeyR=700)
kf(_LOBJ["MiloKeyR"], "rotation_euler", FT(O0), look_at(_LOBJ["MiloKeyR"], RO + V((0.0, -4.8, 4.8))), interp="CONSTANT")
expr(fm, FT(O0), "ominous"); expr(fm, FT(79.3), "curious"); expr(fm, FT(81.2), "question"); expr(fm, FT(83.1), "sly")
for t in (77.66, 79.35, 81.24): say(line(t), fm, "rest_flat", "whisper" if t < 81 else "calm", nod=4.0, P=milo)
arm(milo, "Left", FT(77.9), euler=(55, 20)); arm(milo, "Left", FT(78.6), euler=(6, -6))      # "on the porch" - a hand down at the boards
arm(milo, "Right", FT(79.5), euler=(60, -14)); arm(milo, "Right", FT(80.3), euler=(6, 6))     # "on the phone" - toward the door
mouth(fm, FT(83.4), "rest_creepy")
idle(milo, FT(O0), NF, amp=0.015, base_z=0.5)
cine("O outro", O0, E2["total"], milo, u=V((0, 1, 0)), size="MCU", move="push", amt=1.5, lens=30, sy=0.1, land=0.9)
blinks(fm, O0, E2["total"], every=2.9, ph=0.2)

# ================================================================== finish
CUT_FR = [f0 for _, f0, _ in SHOTS[1:]]
apply_blinks()
flush_mouths(); apply_interp(); hold_cuts(); apply_interpolation(); breathe()


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
json.dump({"shots": SHOTS, "nf": NF}, open("/home/claude/talk/shots_p3.json", "w"))
exec(open(SCR + "director.py").read())     # shot checker: camera inside a mesh / subject blocked / lens covered
shot_probs = check_shots(SHOTS, allow=ALLOW)
shot_probs += check_framing(SHOTS)
if shot_probs and not os.environ.get("FORCE"):
    raise SystemExit("shot check failed - fix the cameras (FORCE=1 to render anyway)")
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
exec(open(SCR + "director.py").read()) if "render_quality" not in globals() else None
render_quality(s, os.environ.get("QUALITY", "fast"))     # Joel picked fast 22 Nov 15:23
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
