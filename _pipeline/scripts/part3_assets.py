# part3_assets.py - Part 3 "Don't Say It": FULL ASSET SHEET (stills for Joel to approve before any pod).
# New: bedroom door detail + light gap + shadow feet, LIGHTHOUSE drawing, note (2 handwritings) + pencil, side sash window,
# fence gap, Rae's front door + hall (night), torch, phone. Props in _studio_library/engine/props6.py (NOT yet approved).
# Run: SHOTS=all SAMPLES=24 python3 part3_assets.py  -> /home/claude/talk/p3_assets/*.png
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
# Part 3: a sash window in Milo's RIGHT wall (faces Rae's), hole 4 wide (local z -6.5..-2.5) x 4 tall (4..8)
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
ENV = {"rms": [0.0] * 4000, "cen": [0.0] * 4000}
exec(open(SCR + "rig2.py").read())       # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ... (R = radians now)
exec(open(LIB + "monster.py").read())    # THE KNOCKER (studio library)
DEG = math.radians
OUT = os.environ.get("OUT", "/home/claude/talk/p3_assets")
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
KN = make_knocker("Knocker", 11.5)

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




# ================================================================== PART 3 NEW ASSETS (props6.py, awaiting approval)
exec(open(LIB + "props4.py").read()); dress_bedroom()
exec(open(LIB + "props5.py").read()); detail_town(houses)
exec(open(LIB + "props6.py").read())
FRONT_DOOR = [o for o in bpy.data.objects if o.name.startswith("FrontDoor")][0]
BDOOR = p6_bedroom_door(FRONT_DOOR)
GAP = p6_light_gap(FRONT_DOOR); gap_feet(GAP, True)
DRAW = p6_drawing("Drawing", (-7.0, -49.0, 0.4), (0, 1, 0), z=7.0, w=3.0)
NOTE = p6_note("Note", (4.6, -43.2, 0.43), (0, 0, DEG(-18)))
PENCIL = p6_pencil("Pencil", (3.7, -42.6, 0.46), (0, 0, DEG(35)))
SWIN = p6_side_window("SideWin", x_in=11.0, yc=-35.5, sill=4.4, open_u=0.0)
SW_LOWER = bpy.data.objects[SWIN["lower"]]
FGAP, _gone = p6_fence_gap()
RO = V((720, 0, 400)); RAE_SET, RAE_HINGE = p6_rae_door_set(RO)
TORCH = p6_torch("Torch", rae["tiltRight"]); TORCH.location = (0, 0.35, 0.05)
PHONE = p6_phone("Phone", rae["tiltLeft"]); PHONE.location = (0, 0.5, 0.25)
TORCH_BEAM = bpy.data.objects[TORCH["beam"]]
# props studio copies (cyc): a second note face-down, pencil, torch + phone standing
NOTE2 = p6_note("NoteB", SO + V((1.1, -1.0, 0.03)), (0, DEG(180), DEG(190)))
PEN2 = p6_pencil("PencilB", SO + V((0.0, -2.0, 0.07)), (0, 0, DEG(-20)))
NOTE3 = p6_note("NoteC", SO + V((-1.2, -1.0, 0.03)), (0, 0, DEG(172)))
TOR2 = p6_torch("TorchB"); TOR2.location = SO + V((2.5, -0.6, 0.17)); TOR2.rotation_euler = (0, 0, DEG(-30)); bpy.data.objects[TOR2["beam"]].data.energy = 0
PH2 = p6_phone("PhoneB"); PH2.location = SO + V((-2.5, -0.2, 0.62)); PH2.rotation_euler = (DEG(-12), 0, DEG(10))

# ---------------------------------------------------------------- CINEMATIC NIGHT LIGHTING (Joel 22:10)
# Recipe: one motivated KEY per shot (moon through the side window = cool, hard, with the window's own bar shadows;
# or a practical: door gap / porch lamp / phone screen = warm), very LOW fill (shadows stay dark but not crushed),
# a cool RIM for separation, warm-vs-cool contrast. Lights are cheap (no volumes, no extra bounces); grade in lookdev.py.
exec(open(LIB + "lookdev.py").read())
if os.environ.get("LOOK", "1") == "1": cinematic_look(exposure=0.9, bloom=0.55, vignette=0.3)


def spot(name, loc, tgt, energy, size_deg, radius, col):
    d = bpy.data.lights.new(name, "SPOT"); d.energy = 0; d.spot_size = DEG(size_deg); d.spot_blend = 0.25
    d.shadow_soft_size = radius; d.color = col
    o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = V(loc)
    o.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler(); return d


MOON_SPOT = spot("MoonSpot", (24.0, -34.0, 13.0), (-2.0, -39.0, 1.5), 0, 38, 0.15, (0.6, 0.72, 1.0))   # through the side window
MOON_IN = area("MoonIn", (16.0, -35.5, 9.0), (2.0, -38.0, 2.5), 0, 5, (0.62, 0.72, 1.0))
DOOR_PRAC = area("DoorPrac", (0.0, -31.0, 0.6), (-4.0, -38.0, 3.5), 0, 3, (1.0, 0.72, 0.45))            # gap light, low = under-light
ROOM_FILL = area("RoomFillA", (0.0, -40.0, 13.0), (0.0, -40.0, 0.0), 0, 10, (0.5, 0.58, 0.9))
MILO_RIM = area("MiloRimA", (-10.0, -46.0, 9.5), (-6.2, -39.6, 4.6), 0, 2.5, (0.6, 0.72, 1.0))
RAE_MOON = area("RaeMoon", RO + V((-14, -16, 16)), RO + V((0, 0, 4)), 0, 8, (0.6, 0.7, 1.0))
RAE_RIM = area("RaeRim", RO + V((6, -3, 11)), RO + V((-1.6, -6.2, 4.8)), 0, 2, (0.62, 0.72, 1.0))
YARD_MOON = area("YardMoon", (40.0, -46.0, 18.0), (22.0, -36.0, 2.0), 0, 8, (0.6, 0.7, 1.0))           # front-side moon key
WIN_GLOW = area("WinGlow", (13.2, -35.5, 6.2), (22.0, -36.0, 1.5), 0, 3.5, (1.0, 0.75, 0.5))            # room light out of the window
SCREEN = area("ScreenGlow", (0, 0, 0), (0, 0, 1), 0, 0.5, (0.75, 0.85, 1.0))
NIGHT_LIGHTS = (MOON_SPOT, MOON_IN, DOOR_PRAC, ROOM_FILL, MILO_RIM, RAE_MOON, RAE_RIM, YARD_MOON, WIN_GLOW, SCREEN)


MOON_FACE = area("MoonFace", (8.0, -36.0, 8.0), (-6.2, -39.6, 4.6), 0, 3.0, (0.62, 0.74, 1.0))   # window-side soft key on faces
FAIRY = area("FairyGlow", (-6.8, -47.6, 10.2), (-7.0, -49.0, 6.5), 0, 2.0, (1.0, 0.78, 0.5))       # motivated by the fairy lights
NIGHT_LIGHTS = NIGHT_LIGHTS + (MOON_FACE, FAIRY)


def aim(L, tgt):
    o = [o for o in bpy.data.objects if o.data == L][0]
    o.rotation_euler = (V(tgt) - o.location).to_track_quat("-Z", "Y").to_euler()


def night(**en):
    set_night(0.0); house_lights(0.0, False)
    aim(MOON_SPOT, en.pop("moon_at", (-2.0, -39.0, 1.5)))
    key(MILO_LIGHT, "energy", 0.0, en.pop("room", 0))                    # Part 1's warm room bulb: off unless asked
    for L in NIGHT_LIGHTS: L.energy = en.get(L.name, 0)


def sit(P, loc, yaw):
    pose(P, loc, yaw)
    for h in ("hipL", "hipR"): P[h].rotation_euler = (DEG(90), 0, 0)


def stand(P):
    for h in ("hipL", "hipR"): P[h].rotation_euler = (0, 0, 0)


def sh_hook():
    night(MoonSpot=6000, MoonFace=380, DoorPrac=110, RoomFillA=18, MiloRimA=420, moon_at=(-7.5, -42.0, 5.0)); only(milo); stand(milo)
    sit(milo, (-6.2, -39.6, 0.55), -34)
    arm(milo, "Right", 1, target=tuple(float(v) for v in os.environ.get("HAND", "-1.3,1.6,5.4").split(","))); arm(milo, "Left", 1, target=(-0.6, 1.4, 2.6))
    setface(fm, "scared", "rest_frown")
    look((-1.8, -33.8, 5.6), (-6.0, -39.4, 4.2), 30, fstop=2.8)


def sh_door_feet():
    night(MoonSpot=6000, RoomFillA=25, moon_at=(-1.5, -31.0, 2.0)); only()
    look((1.6, -37.4, 1.25), (0.0, -30.8, 0.9), 32, fstop=3.5)


def sh_door():
    night(MoonSpot=9000, RoomFillA=50, moon_at=(-1.2, -31.0, 4.5)); only()
    look((0.6, -41.5, 5.2), (0.0, -30.7, 5.0), 30)


def sh_drawing():
    night(FairyGlow=180, RoomFillA=30, MoonSpot=6000, moon_at=(-4.0, -44.0, 1.0)); only()
    look((-5.6, -43.8, 6.4), (-7.0, -49.0, 7.0), 45, fstop=4.0)


def sh_note_front():
    night(MoonSpot=7000, RoomFillA=60, DoorPrac=50, moon_at=(4.5, -43.3, 0.4)); only()
    look((4.6, -41.3, 2.6), (4.4, -43.4, 0.45), 40, fstop=4.0)


def sh_note_back():
    night(MoonSpot=7000, RoomFillA=60, DoorPrac=50, moon_at=(4.5, -43.3, 0.4)); only()
    NOTE.rotation_euler = (0, DEG(180), DEG(-18)); NOTE.location.z = 0.43
    look((4.6, -41.3, 2.6), (4.4, -43.4, 0.45), 40, fstop=4.0)


def sh_window_in():
    night(MoonSpot=9000, RoomFillA=25, MoonIn=200); only(); SW_LOWER.location.z = 4.4 + 1.0 + 0.7 * 1.8
    look((3.0, -39.8, 5.4), (11.0, -35.5, 6.2), 28)


def sh_yard():
    night(YardMoon=2600, WinGlow=260, room=300, RaeRim=0); only(milo); stand(milo); aim(YARD_MOON, (24.2, -37.0, 3.0))
    pose(milo, (24.2, -37.0, 0.0), -90); arm(milo, "Right", 1, euler=(25, 8)); arm(milo, "Left", 1, euler=(-20, -8))
    setface(fm, "scared", "rest_frown")
    look((33.5, -42.5, 4.6), (22.0, -36.5, 3.0), 28)


def sh_rae_door():
    night(RaeMoon=260, RaeRim=420); only(rae, milo); stand(milo); stand(rae)
    pose(rae, RO + V((0.5, -0.2, 0.5)), 190); arm(rae, "Right", 1, target=(0.6, 1.6, 3.4)); arm(rae, "Left", 1, euler=(4, -6))
    pose(milo, RO + V((-1.6, -6.2, 0.5)), 8)
    setface(frae, "nervous", "rest_flat"); setface(fm, "scared", "rest_frown")
    look(RO + V((4.2, -12.0, 5.4)), RO + V((-0.4, 0.0, 4.2)), 30)


def sh_phone():
    night(RaeMoon=160); only(rae); stand(rae)
    pose(rae, RO + V((0.5, -0.2, 0.5)), 180); arm(rae, "Left", 1, target=(-0.3, 1.9, 4.3)); arm(rae, "Right", 1, euler=(4, 6))
    PHONE.rotation_euler = (0, 0, DEG(180))                     # she turns the screen to Milo: "Milo" is calling
    TORCH_BEAM.data.energy = 0; setface(frae, "scared", "rest_frown")
    bpy.context.view_layer.update(); p = PHONE.matrix_world.translation
    so = bpy.data.objects["ScreenGlow"]; so.location = p + V((0, -0.35, 0)); so.rotation_euler = (DEG(-70), 0, 0); SCREEN.energy = 0
    look(p + V((-0.5, -3.2, 0.3)), p + V((0.1, 0, 0.25)), 40, fstop=2.4)


def sh_props():
    set_day(0.0); only()
    look(SO + V((0, -4.6, 3.8)), SO + V((0, -0.7, 0.25)), 40)


add("01_hook_milo_bed", (540, 960), sh_hook)
add("02_door_gap_feet", (540, 960), sh_door_feet)
add("03_bedroom_door", (540, 960), sh_door)
add("04_lighthouse_drawing", (540, 960), sh_drawing)
add("05_note_front", (540, 960), sh_note_front)
add("06_note_back", (540, 960), sh_note_back)
add("07_side_window", (540, 960), sh_window_in)
add("08_yard_fence_gap", (540, 960), sh_yard)
add("09_rae_door_torch", (540, 960), sh_rae_door)
add("10_phone_screen", (540, 960), sh_phone)
add("11_props_cyc", (960, 960), sh_props)

s.render.engine = "CYCLES"; s.cycles.use_denoising = True
if os.environ.get("ENGINE", "CPU") == "GPU":                # pod: pod_stills.sh -> full-res stills at final quality
    pr = bpy.context.preferences.addons["cycles"].preferences
    for be in ("OPTIX", "CUDA"):
        try:
            pr.compute_device_type = be; pr.get_devices()
            gpus = [x for x in pr.devices if x.type == be]
            if gpus:
                for x in pr.devices: x.use = x.type == be
                print("GPU BACKEND", be, [x.name for x in gpus]); break
        except Exception as e: print("backend fail", be, e)
    s.cycles.device = "GPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 32))
    try: s.cycles.denoiser = "OPTIX"
    except Exception: pass
else:
    s.cycles.device = "CPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 16))
    try: s.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
s.render.use_motion_blur = False
s.render.image_settings.file_format = "PNG"
want = os.environ.get("SHOTS", "all").split(",")
SCALE = float(os.environ.get("SCALE", 1.0))
for name, (rx, ry), fn in SHOT_LIST:
    if want != ["all"] and not any(name.startswith(w) for w in want): continue
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action: o.animation_data_clear()
    _MEV.clear(); _CUTS.clear(); reset_arms(); stand(milo)
    NOTE.rotation_euler = (0, 0, DEG(-18)); SW_LOWER.location.z = 4.4 + 1.0; TORCH_BEAM.data.energy = 900; PHONE.rotation_euler = (0, 0, 0)
    fn()
    flush_mouths(); apply_interp(); apply_interpolation()
    s.render.resolution_x, s.render.resolution_y = int(rx * SCALE), int(ry * SCALE)
    s.frame_set(1); s.render.filepath = f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)
print("DONE")
