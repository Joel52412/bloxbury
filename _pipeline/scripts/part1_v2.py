# part1_v2.py - BLOXBURY: The 3AM Knock, Part 1 (redesign). 24 fps, rig v2 faces, library cast, director shots.
# Audio/cues/captions: _pipeline/audio_tools/prep_p1.py -> /home/claude/talk/{env_p1.json, part1_audio.wav, captions_p1.ass}
# Preview: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 python3 part1_v2.py      Pod: ENGINE=GPU RENDER=1 RX=1080 RY=1920 blender -b --python part1_v2.py
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
ENV = json.load(open("/home/claude/talk/env_p1.json"))
exec(open(SCR + "rig2.py").read())       # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ... (R = radians now)
exec(open(SCR + "monster.py").read())    # THE KNOCKER (pending Joel's approval)
DEG = math.radians
OUT = os.environ.get("OUT", "/home/claude/talk/frames_p1")
os.makedirs(OUT, exist_ok=True)
NF = ENV["nf"]
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


# ------------------------------------------------------------------ cast (recurring = fixed cards)
def make_rae():
    """RAE (fixed card, new): purple hoodie, black two braids, dark jeans, lilac trainers, red notebook."""
    S = new_set(); skin = (176, 122, 88); rng = RNG(311)
    d_hoodie(S, (122, 84, 170), rng, skin)
    b_trousers(S, (30, 30, 40), rng, kind="jeans")
    for k in LEGS: shoes(S[k], (205, 170, 240), (70, 45, 100))
    finish(S, rng)
    P = build_body("Rae", skin, S)
    add_hair4(P, "X5", random.Random(5), colour=(24, 20, 20))
    return P


def make_mayor():
    """THE MAYOR (fixed card, new): dark suit, red tie, grey crop (older man), glasses."""
    S = new_set(); skin = (234, 184, 146); rng = RNG(512)
    d_suit(S, rng, skin, col=(30, 30, 36), tie=(160, 25, 40))
    b_trousers(S, (30, 30, 36), rng, kind="tailored")
    s_shoes(S, "loafers", (15, 15, 18), rng)
    finish(S, rng)
    P = build_body("Mayor", skin, S)
    add_hair4(P, "X1", random.Random(9), colour=(150, 150, 155))
    a_glasses(P)
    return P


def make_neighbour():
    """Neighbour (extra from library parts): builder role, hi-vis + hard hat (under-hat hair)."""
    S = new_set(); skin = (124, 86, 62); rng = RNG(733)
    d_hivis(S, rng, skin, under=lambda S_: d_tee(S_, (52, 74, 124), rng, skin))
    b_trousers(S, (60, 60, 66), rng, kind="cargo"); s_shoes(S, "boots", (110, 80, 50), rng)
    finish(S, rng)
    P = build_body("Neighbour", skin, S)
    a_hardhat(P, (250, 200, 30)); hat_hair(P, (24, 20, 20), random.Random(4))
    return P


milo = make_milo(); rae = make_rae(); mayor = make_mayor(); nb = make_neighbour()
CAST_ALL = (milo, rae, mayor, nb)
for P in CAST_ALL: strip_faces(P)
for o in bpy.data.objects: o.animation_data_clear()
for P in CAST_ALL: upgrade_rig(P)
fm, fr_, fy, fn = (build_face_v2(P) for P in CAST_ALL)
RIGS = {"milo": fm, "rae": fr_, "mayor": fy, "nb": fn}

# ------------------------------------------------------------------ props (new for this episode: hammer, crate, notebook)
M_NOTE = pmat("NoteRed", (170, 40, 45), rough=0.7)
note = empty("Notebook", V((0, 0, 0)), col=COL_PROPS, parent=rae["tiltLeft"])
rb("NoteCover", (0.7, 0.14, 0.9), V((0, 0.05, 0.1)), M_NOTE, note, r=0.03)
note.location = (0.0, 0.55, 0.05); note.rotation_euler = (0, 0, 0)
hammer = empty("Hammer", V((0, 0, 0)), col=COL_PROPS, parent=nb["tiltRight"])
rb("HammerHandle", (0.2, 0.2, 1.5), V((0, 0.35, 0.55)), M_WOOD, hammer, r=0.05)
rb("HammerHead", (0.36, 0.85, 0.36), V((0, 0.35, 1.32)), M_METAL, hammer, r=0.05)
crate = rb("Crate", (2.6, 2.4, 2.0), V((-57, 28.2, 1.0)), wood("CrateWood", (150, 110, 70)), None, r=0.05)


def list_img(path):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (600, 800), (244, 238, 220)); d = ImageDraw.Draw(im)
    for y in range(90, 800, 52): d.line((30, y, 570, y), fill=(170, 190, 220), width=2)
    d.line((80, 0, 80, 800), fill=(220, 120, 120), width=3)
    try:
        fh = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        fw = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except Exception: fh = fw = ImageFont.load_default()
    d.text((100, 28), "WHO'S LEFT", fill=(150, 20, 20), font=fh)
    names = ["Mr. Hollis", "The Patels", "Jonah", "Mrs. Reed", "Old Tom", "Ellie", "The Grants", "Rae", "Milo?"]
    for i, nm in enumerate(names):
        y = 100 + i * 52 + 8
        d.text((100, y), nm, fill=(30, 30, 60), font=fw)
        if i < 7:
            w = d.textlength(nm, font=fw); d.line((96, y + 20, 104 + w, y + 18), fill=(30, 30, 40), width=5)
    im.save(path)


LP = "/tmp/p1_list.png"; list_img(LP)
NOTE_POS = V((600, 600, 0))
page = plane("ListPage", 3.0, 4.0, NOTE_POS + V((0, 0, 3.0)), imgmat("ListPage", LP, rough=0.85), None)
rb("ListCover", (3.4, 0.1, 4.4), NOTE_POS + V((0, -0.09, 3.0)), M_NOTE, None, r=0.04)
rb("ListBackdrop", (16, 0.2, 14), NOTE_POS + V((0, -0.6, 3.0)), wood("ListDesk", (70, 48, 34)), None, r=0.02)
ins_light = bpy.data.lights.new("InsertKey", "AREA"); ins_light.energy = 400; ins_light.size = 4
ilo = bpy.data.objects.new("InsertKey", ins_light); s.collection.objects.link(ilo)
ilo.location = NOTE_POS + V((2.5, 6, 6)); ilo.rotation_euler = (NOTE_POS + V((0, 0, 3)) - ilo.location).to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ house interior bits
FRONT_DOOR = [o for o in bpy.data.objects if o.name.startswith("FrontDoor")][0]
FD0 = FRONT_DOOR.location.copy()
M_WINDOW_MILO = bpy.data.materials.new("WindowMilo"); M_WINDOW_MILO.use_nodes = True
_mwb = M_WINDOW_MILO.node_tree.nodes.get("Principled BSDF")
_mwb.inputs["Base Color"].default_value = (*lin(C["glass"]), 1); _mwb.inputs["Roughness"].default_value = 0.05
_mwb.inputs["Alpha"].default_value = 0.22
_mwb.inputs["Emission Color"].default_value = (*lin(C["warm"]), 1); _mwb.inputs["Emission Strength"].default_value = 0.0
set_blended(M_WINDOW_MILO)
for w_ in WINDOW_PARTS:
    if w_.parent and w_.parent.name == "MiloHouse": w_.material_slots[0].material = M_WINDOW_MILO
MILO_GLOW = _mwb.inputs["Emission Strength"]
# closet: soft red-orange glow strip under the door + light inside + spill on Milo (kept from test 2)
CL_X, CL_Y = 7.0, -45.85
strip = rb("GlowStrip", (4.6, 0.3, 0.05), V((CL_X, CL_Y + 0.12, 0.43)), pmat("GlowRO", (255, 90, 30), emit=6.0, emit_rgb=(255, 82, 20)), None)
strip.scale = (1, 0, 0)
cglow = bpy.data.lights.new("ClosetGlow", "POINT"); cglow.color = (1.0, 0.32, 0.08); cglow.energy = 0; cglow.shadow_soft_size = 1.5
cgo = bpy.data.objects.new("ClosetGlow", cglow); s.collection.objects.link(cgo); cgo.location = (CL_X, CL_Y - 0.9, 1.2)
spill = bpy.data.lights.new("DoorSpill", "AREA"); spill.color = (1.0, 0.35, 0.1); spill.energy = 0; spill.size = 3
spo = bpy.data.objects.new("DoorSpill", spill); s.collection.objects.link(spo)
spo.location = (CL_X - 1, CL_Y + 2.5, 2.0); spo.rotation_euler = (V((0, -36, 4.5)) - spo.location).to_track_quat("-Z", "Y").to_euler()
inter = bpy.data.lights.new("RoomFill", "AREA"); inter.energy = 0; inter.size = 8; inter.color = (0.75, 0.8, 1.0)
ifo = bpy.data.objects.new("RoomFill", inter); s.collection.objects.link(ifo); ifo.location = (-2, -36, 12.5)
ifo.rotation_euler = (0, 0, 0)

# ------------------------------------------------------------------ day / night blocking
CUT_NIGHT1, CUT_DAY1, CUT_NIGHT2, CUT_OUTRO = 0.0, 2.6, 33.2, ENV["outro0"]
LAMP_LIGHTS = [L[2] for L in LAMPS]; LAMP_MATS = [L[1] for L in LAMPS]


def lamps(t, on):
    for ld in LAMP_LIGHTS: key(ld, "energy", t, 20000 if on else 0)
    for m in LAMP_MATS: key(m.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], "default_value", t, 12.0 if on else 0.0)


set_night(0.0); house_lights(0.0, True); lamps(0.0, True); key(MILO_GLOW, "default_value", 0.0, 2.0)
set_day(CUT_DAY1); house_lights(CUT_DAY1, False); lamps(CUT_DAY1, False); key(MILO_GLOW, "default_value", CUT_DAY1, 0.0)
set_night(CUT_NIGHT2); house_lights(CUT_NIGHT2, True); lamps(CUT_NIGHT2, True); key(MILO_GLOW, "default_value", CUT_NIGHT2, 0.0)
key(MILO_GLOW, "default_value", 38.1, 2.5); key(MILO_GLOW, "default_value", 40.4, 0.0)   # glows only in the outside shot
house_lights(36.55, False)                        # "went OFF" (Milo's window keeps glowing)
for i, lamp in enumerate(sorted(LAMPS, key=lambda L: -(L[0].location - V((0, -30, 0))).length)):
    lamp_flicker(lamp, 41.65 + i * 0.07)           # street lamps die, furthest first
set_day(CUT_OUTRO); key(MILO_GLOW, "default_value", CUT_OUTRO, 0.0); house_lights(CUT_OUTRO, False); lamps(CUT_OUTRO, False)
key(inter, "energy", 0.0, 0); key(inter, "energy", 43.3, 120); key(inter, "energy", 62.3, 0); key(inter, "energy", CUT_OUTRO, 0)
# clock texts (2:59 -> 3:00) live on the room's left wall
visible(CLOCK_TEXTS["2:59 AM"], [(0, 40.6)]); visible(CLOCK_TEXTS["3:00 AM"], [(40.6, None)])

# ------------------------------------------------------------------ dialogue: lip-sync every line, accents on stressed words
LINES = ENV["lines"]
for L in LINES:
    rig = fr_ if L["who"] == "rae" else fm
    f0, f1 = FT(L["t0"]) , FT(L["t1"]) + 1
    if L["file"] == "outro": continue                         # outro block below (test 2 shot A)
    style = "whisper" if L["t0"] > 57 and L["t0"] < 62.5 else ("excited" if "joking" in (L["text"] or "") else "calm")
    rest = "rest_flat"
    lipsync(rig, f0, f1, [(f0, rest, style)])
for rig, rest in ((fm, "rest_smile"), (fr_, "rest_flat"), (fy, "rest_creepy"), (fn, "rest_flat")):
    mouth(rig, 1, rest)

# ================================================================== SHOTS (video seconds)
# ---- A 0.0-2.6  HOOK: night, the front door shudders on three heavy knocks
place(milo, 1, (60, 60, 0)); place(rae, 1, (70, 60, 0)); place(mayor, 1, (218, 0, 0), 90); place(nb, 1, (-57, 28.2, 2.0), 0)
for t in (0.16, 0.46, 0.73, 1.04):
    f = FT(t)
    kf(FRONT_DOOR, "location", f - 1, FD0); kf(FRONT_DOOR, "location", f, FD0 + V((0, 0.12, 0)), interp="LINEAR")
    kf(FRONT_DOOR, "location", f + 3, FD0 + V((0, -0.02, 0))); kf(FRONT_DOOR, "location", f + 5, FD0)
# ---- B 2.6-4.7 van past the welcome sign / C 4.7-7.2 chase the van to the new house
VAN0, VAN1 = -275, -18


def van_x(t):
    u = min(max((t - 2.4) / 5.0, 0), 1); return VAN0 + (VAN1 - VAN0) * math.sin(u * math.pi / 2)


t = 0.0
while t <= 7.6:
    key(VAN, "location", t, V((van_x(t), 6, 0)), "LINEAR"); t += 1 / 12
key(VAN, "location", 7.7, V((van_x(7.7), 6, 0)), "CONSTANT"); key(VAN, "location", 33.2, V((-420, 6, 0)), "CONSTANT")   # van leaves after day 1
# ---- D 7.2-9.9 Milo on the lawn, the house behind him (Mum's never there)  / E 9.9-11.9 his face
MILO_LAWN = (-3.0, -22.0, 0.0)
place(milo, FT(7.2), MILO_LAWN, -10)
idle(milo, FT(7.2), FT(11.9))
expr(fm, FT(7.2), "friendly"); expr(fm, FT(8.6), "friendly"); expr(fm, FT(9.0), "content"); expr(fm, FT(9.8), "sad")
expr(fm, FT(11.9), "sad"); blink(fm, FT(8.0)); blink(fm, FT(10.2))
arms_down(milo, FT(7.2))
arm(milo, "Right", FT(8.95), euler=(4, 6)); arm(milo, "Right", FT(9.15), euler=(40, 30)); arm(milo, "Left", FT(8.95), euler=(4, -6))
arm(milo, "Left", FT(9.15), euler=(40, -30)); arms_down(milo, FT(9.6))                  # little shrug: "She always was."
chest(milo, FT(9.0)); chest(milo, FT(9.15), 3); chest(milo, FT(9.6))
neck(milo, FT(7.2), 0, 0, 0); neck(milo, FT(10.3), 0, 0, 0); neck(milo, FT(10.9), -14, 0, -28); neck(milo, FT(11.85), -16, 0, -30)   # looks back at the house
hits = accents(milo, fm, FT(7.3), FT(9.7), nod=3.0)
# ---- F 11.9-14.75 fence: Milo waves, Rae just stares
M_FENCE, R_FENCE = (23.3, -27.0, 0.0), (26.7, -27.0, 0.0)
place(milo, FT(11.9), M_FENCE, -90); place(rae, FT(11.9), R_FENCE, 90)
idle(milo, FT(11.9), FT(27.9)); idle(rae, FT(11.9), FT(27.9), amp=0.012, ph=1.0)
expr(fm, FT(11.9), "friendly"); expr(fm, FT(13.6), "friendly"); expr(fm, FT(14.0), "notice"); expr(fm, FT(14.7), "nervous")
arms_down(milo, FT(11.9)); arm(milo, "Right", FT(12.3), euler=(4, 6))
for i, t in enumerate((12.55, 12.8, 13.05, 13.3, 13.55)):                     # wave
    arm(milo, "Right", FT(t), euler=(160, 18 if i % 2 else -12))
arm(milo, "Right", FT(13.85), euler=(150, 0)); arm(milo, "Right", FT(14.25), euler=(4, 6))   # ...slowly drops it
mouth(fm, FT(11.9), "rest_smile"); mouth(fm, FT(13.9), "rest_flat")
expr(fr_, FT(11.9), "deadpan"); expr(fr_, FT(14.7), "deadpan")
arms_down(rae, FT(11.9)); arm(rae, "Left", FT(11.9), (-0.6, 1.4, 2.8)); arm(rae, "Left", FT(14.7), (-0.6, 1.4, 2.8))   # notebook at her chest
blink(fr_, FT(13.2))
# ---- G 14.75-18.85 Rae close: "New kid? / One rule. / Three knocks after 3 AM..."
expr(fr_, FT(14.95), "curious"); expr(fr_, FT(15.6), "deadpan"); expr(fr_, FT(15.95), "lean_in"); expr(fr_, FT(17.0), "ominous")
expr(fr_, FT(18.8), "ominous")
neck(rae, FT(14.8)); neck(rae, FT(15.05), 0, 0, 0); neck(rae, FT(15.3), -6, 12, 0); neck(rae, FT(15.8), 0, 0, 0)   # head tilt "New kid?"
arm(rae, "Right", FT(15.9), euler=(4, 6)); arm(rae, "Right", FT(16.15), euler=(150, 8)); arm(rae, "Right", FT(16.3), euler=(140, 8))  # one finger up
arm(rae, "Right", FT(16.75), euler=(100, 14))
for t in (17.05, 17.35, 17.65):                              # knocks in the air on "Three knocks"
    arm(rae, "Right", FT(t), euler=(100, 14)); arm(rae, "Right", FT(t + 0.08), euler=(78, 14), interp="LINEAR")
    arm(rae, "Right", FT(t + 0.16), euler=(100, 14))
arm(rae, "Right", FT(18.6), euler=(4, 6))
chest(rae, FT(15.9)); chest(rae, FT(16.2), -6); chest(rae, FT(18.4), -10)
blink(fr_, FT(16.6)); accents(rae, fr_, FT(15.0), FT(18.6), nod=4.0)
# ---- H 18.85-20.2 Milo listening (nervous) / I 20.2-21.4 ECU Rae "EVER."
expr(fm, FT(18.85), "nervous"); expr(fm, FT(20.1), "scared"); blink(fm, FT(19.4))
neck(milo, FT(18.85), 0, 0, 0); neck(milo, FT(19.6), 4, 0, 0)
expr(fr_, FT(20.2), "ominous"); expr(fr_, FT(20.35), "annoyed"); expr(fr_, FT(21.3), "annoyed")
chest(rae, FT(20.25), -10); chest(rae, FT(20.4), -16); chest(rae, FT(21.3), -14)
# ---- J 21.4-23.8 wide two-shot: Milo laughs it off, Rae doesn't move. "She wasn't."
expr(fm, FT(21.45), "laugh"); expr(fm, FT(22.55), "laugh"); expr(fm, FT(22.9), "nervous"); expr(fm, FT(23.75), "nervous")
mouth(fm, FT(21.45), "grin_open")
for i, t in enumerate((21.55, 21.75, 21.95, 22.15, 22.35)):              # laugh bobs
    neck(milo, FT(t), 10 if i % 2 == 0 else 2, 0, 0); chest(milo, FT(t), -4 if i % 2 == 0 else 0)
neck(milo, FT(22.6), 0, 0, 0); chest(milo, FT(22.6))
arm(milo, "Left", FT(21.5), euler=(4, -6)); arm(milo, "Left", FT(21.7), euler=(40, -40)); arm(milo, "Left", FT(22.5), euler=(40, -40))
arms_down(milo, FT(22.9))
chest(rae, FT(21.4), -2); expr(fr_, FT(21.4), "deadpan"); expr(fr_, FT(23.8), "deadpan")
# ---- K 23.8-25.0 Rae lifts the notebook / K2 25.0-26.4 insert: the list
arm(rae, "Left", FT(23.9), (-0.6, 1.4, 2.8)); arm(rae, "Left", FT(24.3), (-0.2, 1.4, 3.6)); arm(rae, "Left", FT(26.3), (-0.2, 1.4, 3.6))
smear(rae, "Left", FT(24.1), 1.25)
expr(fr_, FT(24.0), "sly"); expr(fr_, FT(25.0), "sly"); blink(fr_, FT(24.35))
# ---- L 26.4-27.9 Milo: "...Who's left?"
expr(fm, FT(26.4), "nervous"); expr(fm, FT(26.7), "question"); expr(fm, FT(27.8), "scared"); blink(fm, FT(27.4))
neck(milo, FT(26.4), 0, 0, 0); neck(milo, FT(26.75), -4, -8, 0); neck(milo, FT(27.8), -4, -8, 0)
# ---- M 27.9-30.8 neighbour boards up his window (hammer hits on the SFX: 28.06 / 29.02 / 30.00)
nbr = nb["root"]
kf(nbr, "location", FT(27.9), (-57, 28.2, 2.0))
arm(nb, "Left", FT(27.9), euler=(95, -10))                     # left hand holds the plank
for t in (28.06, 29.02, 30.0):
    arm(nb, "Right", FT(t - 0.45), euler=(110, 6)); arm(nb, "Right", FT(t - 0.2), euler=(178, 6))       # wind up
    arm(nb, "Right", FT(t), euler=(118, 6), interp="LINEAR"); smear(nb, "Right", FT(t - 0.05), 1.3)      # strike
    arm(nb, "Right", FT(t + 0.12), euler=(126, 6)); kf(nbr, "location", FT(t), (-57, 28.2, 2.0))
    chest(nb, FT(t - 0.2), 6); chest(nb, FT(t), -6); chest(nb, FT(t + 0.25), 0)
visible(PLANKS[0], [(28.06, None)]); visible(PLANKS[1], [(29.02, None)])
expr(fn, 1, "effort")
# ---- N 30.8-33.2 the Mayor's house with no door; he waves, smiling too much
expr(fy, 1, "grin"); mouth(fy, FT(30.8), "rest_creepy")
for i, t in enumerate(x / 10 for x in range(310, 332, 5)):
    arm(mayor, "Right", FT(t), euler=(150, -20 if i % 2 else 10))
arm(mayor, "Left", FT(30.8), euler=(4, -6)); neck(mayor, FT(30.8), 0, 0, 0); neck(mayor, FT(32.6), 0, 6, 0)
blink(fy, FT(32.2))
# ---- O 33.2-36.4 night: behind Milo at his window, every house lit / P 36.4-38.1 they go off / Q 38.1-40.4 except his
WIN_IN = (-7.25, -32.4, 0.4)
place(milo, FT(33.2), WIN_IN, 0)
idle(milo, FT(33.2), FT(40.4), base_z=0.4)
expr(fm, FT(33.2), "nervous"); expr(fm, FT(36.5), "notice"); expr(fm, FT(36.7), "scared"); expr(fm, FT(40.3), "scared")
neck(milo, FT(33.2), -6, 0, 0); neck(milo, FT(36.55), -6, 0, 0); neck(milo, FT(36.7), 0, 0, 8)
arms_down(milo, FT(33.2)); arm(milo, "Right", FT(33.6), (1.2, 0.9, 4.6)); arm(milo, "Right", FT(40.3), (1.2, 0.9, 4.6))  # hand on the frame
# ---- R 40.4-41.6 the clock: 3:00 / S 41.6-43.3 street lamps die
# ---- T 43.3-45.8 inside the front door: every knock makes him flinch
DOOR_IN = (0.6, -34.3, 0.4)
place(milo, FT(43.3), DOOR_IN, 180)
idle(milo, FT(43.3), FT(45.8), base_z=0.4, amp=0.01, speed=6)
expr(fm, FT(43.3), "scared"); expr(fm, FT(45.7), "scared"); arms_down(milo, FT(43.3))
for t in (43.41, 43.70, 43.97, 44.25):
    f = FT(t)
    kf(FRONT_DOOR, "location", f - 1, FD0); kf(FRONT_DOOR, "location", f, FD0 + V((0, -0.12, 0)), interp="LINEAR")
    kf(FRONT_DOOR, "location", f + 4, FD0)
    chest(milo, f - 1, 0); chest(milo, f + 1, -9); chest(milo, f + 5, -3)
    neck(milo, f - 1, 0, 0, 0); neck(milo, f + 1, 8, 0, 4); neck(milo, f + 5, 2, 0, 2)
    arm(milo, "Left", f + 1, euler=(60, -30)); arm(milo, "Right", f + 1, euler=(60, 30))
arm(milo, "Left", FT(44.7), euler=(50, -26)); arm(milo, "Right", FT(44.7), euler=(50, 26))
mouth(fm, FT(43.3), "rest_frown"); mouth(fm, FT(43.45), "small_o"); mouth(fm, FT(44.6), "rest_frown")
eyes_closed(fm, FT(43.45), FT(43.6))
# ---- U 45.8-47.4 he goes to the window and peeks / U2 47.4-48.8 POV out the window: nobody
place(milo, FT(45.8), (-3.5, -34.0, 0.4), 52)
walk(milo, FT(45.8), FT(46.9), (-3.5, -34.0), (-6.6, -31.9), steps=3, z=0.4)
kf(milo["root"], "rotation_euler", FT(46.7), (0, 0, DEG(-4))); kf(milo["root"], "rotation_euler", FT(47.2), (0, 0, DEG(0)))
kf(milo["root"], "location", FT(47.4), (-6.6, -31.9, 0.4))
expr(fm, FT(45.8), "nervous"); expr(fm, FT(46.9), "curious"); expr(fm, FT(47.4), "curious")
chest(milo, FT(46.9), 0); chest(milo, FT(47.2), -8); neck(milo, FT(46.9), 0, 0, 0); neck(milo, FT(47.3), -4, 0, -10)
# ---- V 48.8-52.1 "Then it went quiet." Push in on his face. Silence.
place(milo, FT(48.8), (-7.6, -32.6, 0.4), 180)
idle(milo, FT(48.8), FT(55.4), base_z=0.4, amp=0.008)
arms_down(milo, FT(48.8)); chest(milo, FT(48.8)); neck(milo, FT(48.8), 0, 0, 0)
expr(fm, FT(48.8), "nervous"); expr(fm, FT(50.4), "sad"); expr(fm, FT(51.6), "nervous"); blink(fm, FT(49.9)); blink(fm, FT(51.3))
mouth(fm, FT(50.4), "rest_flat")
# ---- W 52.1-53.7 "Then the knocking came again." / W2 53.7-55.4 closet: muffled knocks, glow under the door
neck(milo, FT(53.6), 0, 0, 0); neck(milo, FT(53.85), -2, 0, 62); neck(milo, FT(55.4), -2, 0, 60)   # whip round to the closet
chest(milo, FT(53.6)); chest(milo, FT(53.85), 0, 0, 22)
expr(fm, FT(53.65), "nervous"); expr(fm, FT(53.85), "shocked"); expr(fm, FT(55.4), "shocked"); mouth(fm, FT(53.85), "small_o")
kf(strip, "scale", 1, (1, 0, 0)); kf(strip, "scale", FT(53.6), (1, 0, 0)); kf(strip, "scale", FT(54.4), (1, 1, 1))
kf(cglow, "energy", 1, 0); kf(cglow, "energy", FT(53.6), 0); kf(cglow, "energy", FT(54.5), 140)
kf(spill, "energy", 1, 0); kf(spill, "energy", FT(53.8), 0); kf(spill, "energy", FT(55.0), 900)
HINGE = CLOSET_HINGE
for t in (53.69, 53.99, 54.26, 54.53):
    f = FT(t); kf(HINGE, "rotation_euler", f - 1, (0, 0, 0)); kf(HINGE, "rotation_euler", f, (0, 0, DEG(-1.2)), interp="LINEAR")
    kf(HINGE, "rotation_euler", f + 3, (0, 0, 0))
# ---- X 55.4-57.5 "From INSIDE my closet." His face, shake.
place(milo, FT(55.4), (-7.6, -32.6, 0.4), -160)
neck(milo, FT(55.4), 0, 0, 0); chest(milo, FT(55.4), 0, 0, 0)
expr(fm, FT(55.4), "shocked"); expr(fm, FT(57.4), "scared")
chest(milo, FT(55.5), 0); chest(milo, FT(55.7), -8); chest(milo, FT(57.4), -6)
# ---- Y 57.5-62.35 the door creaks open a crack; "Milo..." "let me OUT."
kf(HINGE, "rotation_euler", FT(57.4), (0, 0, 0)); kf(HINGE, "rotation_euler", FT(59.4), (0, 0, DEG(-9)))
kf(HINGE, "rotation_euler", FT(61.0), (0, 0, DEG(-10))); kf(HINGE, "rotation_euler", FT(61.3), (0, 0, DEG(-16)))
kf(cglow, "energy", FT(57.4), 140); kf(cglow, "energy", FT(59.9), 260); kf(cglow, "energy", FT(61.0), 520); kf(cglow, "energy", FT(62.3), 600)
kf(spill, "energy", FT(57.4), 900); kf(spill, "energy", FT(59.0), 600)
kf(strip, "scale", FT(59.4), (1.05, 1.8, 1))
# ---- Z 62.35-65.0 black: "It knew my name."
# ---- OUTRO 65.0-71.75 test 2 shot A, now in Milo's own room with his closet behind him
O = V((3.0, -38.6, 0.4))                         # Milo's spot in the room (test 2 had him at (40, 0, 0))
place(milo, FT(CUT_OUTRO), O, 0)
TA = lambda t: FT(CUT_OUTRO + ENV["lead"] + t)
m, mc, mn = milo["root"], milo["chest"], milo["neck"]
mR, mL = "Right", "Left"
expr(fm, FT(CUT_OUTRO), "curious"); expr(fm, TA(0.05), "curious"); expr(fm, TA(1.05), "question"); expr(fm, TA(1.6), "question")
expr(fm, TA(1.85), "excited"); expr(fm, TA(3.3), "excited")
expr(fm, TA(3.5), "lean_in"); expr(fm, TA(4.4), "lean_in"); expr(fm, TA(4.85), "ominous"); expr(fm, TA(5.85), "ominous")
expr(fm, TA(6.15), "sly"); expr(fm, NF, "sly")
sparkle(fm, TA(2.55), TA(3.4))
blink(fm, TA(0.75)); blink(fm, TA(3.45)); blink(fm, TA(5.95))
mouth(fm, FT(CUT_OUTRO), "rest_smile")
lipsync(fm, FT(CUT_OUTRO) + 1, TA(6.0), [(FT(CUT_OUTRO), "rest_smile", "calm"), (TA(0.0), "rest_smirk", "calm"), (TA(1.85), "rest_smile", "excited"),
                                        (TA(3.45), "rest_flat", "calm"), (TA(4.8), "rest_flat", "whisper")])
mouth(fm, TA(6.1), "rest_creepy")
accents(milo, fm, TA(0.0), TA(3.35), nod=5.0)
for fr in range(FT(CUT_OUTRO), NF, 12):
    kf(m, "location", fr, O.z + 0.02 * math.sin(fr / FPS * 2.2), index=2)
for t, (x, y, z) in ((-0.25, (0, 0, 0)), (0.3, (-3, 0, 9)), (0.9, (-2, 0, 11)), (1.3, (-5, -10, 22)), (1.6, (0, -6, 10)),
                     (1.95, (4, 0, 0)), (2.3, (-3, 0, -4)), (2.7, (-1, 0, 3)), (3.05, (-6, 0, 0)), (3.3, (0, 0, 0)),
                     (3.6, (6, 0, 0)), (4.4, (9, 0, 4)), (5.0, (12, 0, 0)), (5.8, (12, 0, -2)), (6.2, (10, -4, 8)), (6.5, (10, -4, 8))):
    kf(mn, "rotation_euler", TA(t), tuple(DEG(v) for v in (x, y, z)))
for t, lean, twist in ((-0.25, 0, 0), (0.6, -2, 6), (1.3, -3, 12), (1.8, 2, 0), (2.0, -4, 0), (2.25, 3, 0),
                       (3.3, 0, 0), (3.7, -10, 0), (4.4, -13, 0), (5.0, -15, 0), (6.5, -15, 3)):
    kf(mc, "rotation_euler", TA(t), (DEG(lean), 0, DEG(twist)))
for t, fwd in ((-0.25, 0), (3.4, 0), (4.4, 0.9), (5.2, 1.3), (6.5, 1.35)):
    kf(m, "location", TA(t), O.y + fwd, index=1)
arm(milo, mR, FT(CUT_OUTRO), euler=(4, 6))
arm(milo, mR, TA(0.85), euler=(10, 8)); arm(milo, mR, TA(1.15), euler=(150, -60)); arm(milo, mR, TA(1.25), euler=(140, -55))
arm(milo, mR, TA(1.6), euler=(135, -50)); arm(milo, mR, TA(1.85), euler=(30, 10))
arm(milo, mR, TA(1.98), euler=(-10, 5)); arm(milo, mR, TA(2.12), euler=(172, 4)); arm(milo, mR, TA(2.25), euler=(160, 4))
arm(milo, mR, TA(2.45), euler=(165, 4)); arm(milo, mR, TA(2.6), euler=(88, -6)); arm(milo, mR, TA(2.7), euler=(96, -6))
arm(milo, mR, TA(3.25), euler=(92, -6)); arm(milo, mR, TA(3.6), euler=(8, 4)); arm(milo, mR, TA(6.5), euler=(6, 4))
arm(milo, mL, FT(CUT_OUTRO), euler=(4, -6)); arm(milo, mL, TA(1.85), euler=(6, -8))
arm(milo, mL, TA(1.98), euler=(-10, -5)); arm(milo, mL, TA(2.12), euler=(172, -4)); arm(milo, mL, TA(2.25), euler=(160, -4))
arm(milo, mL, TA(2.5), euler=(150, -4)); arm(milo, mL, TA(2.7), euler=(20, -8)); arm(milo, mL, TA(3.6), euler=(6, -6))
arm(milo, mL, TA(6.5), euler=(5, -6))
for side in (mR, mL):
    sh = milo[side]
    kf(sh, "scale", TA(1.98), (1, 1, 1)); kf(sh, "scale", TA(2.06), (1, 1, 1.32)); kf(sh, "scale", TA(2.16), (1, 1, 1))
for t, z in ((1.9, 0.0), (2.02, -0.12), (2.15, 0.42), (2.3, 0.0), (2.36, -0.08), (2.45, 0.0)):
    kf(m, "location", TA(t), O.z + z, index=2)
neck(milo, FT(CUT_OUTRO) - 1, 0, 0, 0); chest(milo, FT(CUT_OUTRO) - 1)
# outro lights: test 2 key/fill/rim around Milo, room dims and the closet glow creeps in for the warning
def lamp_ob(name, loc, energy, size=6, col=(1, 1, 1), target=(0, 0, 4)):
    d = bpy.data.lights.new(name, "AREA"); d.energy = 0; d.color = col; d.size = size
    ob = bpy.data.objects.new(name, d); s.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return d


OT = O + V((0, 0, 4))
okey = lamp_ob("O_Key", O + V((5, 9, 8)), 0, col=(1.0, 0.93, 0.85), target=OT)
ofill = lamp_ob("O_Fill", O + V((-7, 7, 5)), 0, col=(0.8, 0.85, 1.0), target=OT)
orim = lamp_ob("O_Rim", O + V((-2, -6, 8)), 0, col=(0.85, 0.75, 1.0), target=OT)
for d_, e in ((okey, 800), (ofill, 260), (orim, 800)):
    kf(d_, "energy", 1, 0, interp="CONSTANT"); kf(d_, "energy", FT(CUT_OUTRO) - 1, 0, interp="CONSTANT"); kf(d_, "energy", FT(CUT_OUTRO), e)
kf(okey, "energy", TA(3.4), 800); kf(okey, "energy", TA(4.8), 330)
kf(ofill, "energy", TA(3.4), 260); kf(ofill, "energy", TA(4.8), 80)
key(MILO_LIGHT, "energy", CUT_OUTRO, 700); key(MILO_LIGHT, "energy", CUT_OUTRO + ENV["lead"] + 4.0, 300)
kf(cglow, "energy", FT(62.35), 600, interp="CONSTANT"); kf(cglow, "energy", FT(CUT_OUTRO), 0); kf(cglow, "energy", TA(3.6), 0); kf(cglow, "energy", TA(5.0), 160)
kf(strip, "scale", FT(62.35), (1.05, 1.8, 1), interp="CONSTANT"); kf(strip, "scale", FT(CUT_OUTRO), (1, 0, 0), interp="CONSTANT")
kf(strip, "scale", TA(3.6), (1, 0, 0)); kf(strip, "scale", TA(4.6), (1, 1, 1))
kf(spill, "energy", FT(62.35), 500, interp="CONSTANT"); kf(spill, "energy", FT(CUT_OUTRO), 0); kf(spill, "energy", TA(3.7), 0); kf(spill, "energy", TA(5.1), 1800)
kf(HINGE, "rotation_euler", FT(62.35), (0, 0, DEG(-16)), interp="CONSTANT"); kf(HINGE, "rotation_euler", FT(CUT_OUTRO), (0, 0, 0), interp="CONSTANT")

# ================================================================== THE KNOCKER: eyes in the crack, fingers round the door, the lunge
KN = make_knocker("Knocker", height=10.5)
KR = KN["root"]
KOBJ = [o for o in KR.children_recursive if o.type == "MESH"]
for o in KOBJ: o.animation_data_clear()
s.frame_set(1); bpy.context.view_layer.update()
KR.location = (0, 0, 0); KR.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
HEAD_OFF = KN["head"].matrix_world.translation - KR.matrix_world.translation        # head pivot relative to the root (rest pose)
SCARE = FT(61.32)                    # door ripped open on "OUT"
CREEP_CAM = V((3.0, -40.6, 4.4))     # where the camera ends up when it lunges
def k_place(fr, head_world, yaw=0.0, interp="BEZIER"):
    rot = Matrix.Rotation(DEG(yaw), 3, "Z")
    kf(KR, "location", fr, V(head_world) - rot @ HEAD_OFF, interp=interp); kf(KR, "rotation_euler", fr, (0, 0, DEG(yaw)), interp=interp)
CRACK = V((4.95, -46.3, 4.9))        # just behind the door's open edge (hinge is on the +x side)
for fr_k, on in ((1, False), (FT(59.75), True), (FT(62.35), False), (FT(CUT_OUTRO) + 1, False)):
    for o in KOBJ: kf(o, "hide_render", fr_k, not on, interp="CONSTANT")
k_place(FT(59.75), CRACK + V((0.25, -0.5, 0)), 8); k_place(FT(60.3), CRACK, 8); k_place(FT(61.0), CRACK + V((-0.05, 0.05, -0.05)), 10)
k_place(SCARE - 1, CRACK + V((-0.1, 0.1, 0)), 10)
LUNGE = CREEP_CAM + (V((CL_X, CL_Y, 4.6)) - CREEP_CAM).normalized() * 1.25 + V((0, 0, -0.15))
k_place(SCARE + 3, LUNGE + V((0, -0.2, 0.1)), 24, interp="LINEAR"); k_place(SCARE + 5, LUNGE, 26); k_place(FT(62.3), LUNGE + V((0.05, 0.08, 0)), 26)
hd_k = KN["head"]; base_r = tuple(hd_k.rotation_euler)
for fr_k, dr in ((FT(59.75), (0, 0, 0)), (FT(60.6), (0, -8, 0)), (FT(61.0), (0, 10, 0)), (SCARE, (0, 4, 0)), (SCARE + 3, (12, 18, 0)), (FT(62.3), (8, 14, 4))):
    kf(hd_k, "rotation_euler", fr_k, tuple(b + DEG(d) for b, d in zip(base_r, dr)))
for e in KN["eyes"]:                 # eyes flare on "Milo..." and at the lunge
    kf(e, "scale", FT(59.7), tuple(e.scale) , interp="CONSTANT")
# right hand: long fingers curl round the door edge on "let me OUT" (numeric search for the shoulder pose)
sh = KN["shoulderR"]; hand = KN["handR"]; EDGE = V((4.55, -45.7, 5.6))
def hand_err(rx, rz):
    sh.rotation_euler = (DEG(rx), 0, DEG(rz)); bpy.context.view_layer.update()
    return (hand.matrix_world.translation - EDGE).length
k_place(1, CRACK, 10); s.frame_set(1); KR.location = CRACK - Matrix.Rotation(DEG(10), 3, "Z") @ HEAD_OFF; KR.rotation_euler = (0, 0, DEG(10))
bpy.context.view_layer.update()
best = min(((hand_err(rx, rz), rx, rz) for rx in range(-20, 181, 10) for rz in range(-120, 121, 10)))
_, bx, bz = best
best = min(((hand_err(rx, rz), rx, rz) for rx in range(bx - 10, bx + 11, 2) for rz in range(bz - 10, bz + 11, 2)))
print("KNOCKER HAND", best)
_, bx, bz = best
sh0 = (DEG(26), 0, DEG(6))
kf(sh, "rotation_euler", FT(60.2), sh0); kf(sh, "rotation_euler", SCARE - 1, sh0)
kf(sh, "rotation_euler", SCARE + 3, (DEG(70), 0, DEG(30))); kf(sh, "rotation_euler", FT(62.3), (DEG(64), 0, DEG(26)))   # claws come up at the lens
# the door is ripped open (smear: overshoot + settle), glow blasts out
kf(HINGE, "rotation_euler", SCARE - 1, (0, 0, DEG(-16))); kf(HINGE, "rotation_euler", SCARE + 2, (0, 0, DEG(-96)), interp="LINEAR")
kf(HINGE, "rotation_euler", SCARE + 4, (0, 0, DEG(-84))); kf(HINGE, "rotation_euler", SCARE + 7, (0, 0, DEG(-88)))
kf(cglow, "energy", SCARE - 1, 520); kf(cglow, "energy", SCARE + 2, 900)
kf(spill, "energy", FT(59.7), 260); kf(spill, "energy", SCARE - 1, 260); kf(spill, "energy", SCARE + 2, 500)
# keep him in the dark: no room fill, a cold rim from behind for the silhouette, eyes do the work
kf(inter, "energy", FT(57.4), 120); kf(inter, "energy", FT(58.6), 0)
krim = bpy.data.lights.new("KnockerRim", "SPOT"); krim.color = (0.55, 0.65, 1.0); krim.energy = 0; krim.spot_size = DEG(40); krim.shadow_soft_size = 0.4
kro = bpy.data.objects.new("KnockerRim", krim); s.collection.objects.link(kro)
kro.location = (6.4, -48.6, 9.5); kro.rotation_euler = (V((5.2, -45.2, 4.8)) - kro.location).to_track_quat("-Z", "Y").to_euler()
for fr_k, e_k in ((1, 0), (FT(59.7), 0), (FT(59.75), 650), (FT(62.35), 0)):
    kf(krim, "energy", fr_k, e_k, interp="CONSTANT")
# "Then it went quiet." - behind Milo, through the window: his silhouette and eyes, gone by the next beat
WIN_HEAD = V((-5.95, -28.0, 5.6))
for o in KOBJ:
    kf(o, "hide_render", FT(49.7), False, interp="CONSTANT"); kf(o, "hide_render", FT(51.7), True, interp="CONSTANT")
k_place(FT(49.7), WIN_HEAD, 182, interp="BEZIER"); k_place(FT(51.6), WIN_HEAD + V((0.1, 0.15, -0.05)), 186, interp="CONSTANT")
k_place(FT(59.75) - 1, CRACK + V((0.25, -0.5, 0)), 8, interp="CONSTANT")
wback = bpy.data.lights.new("WinBack", "AREA"); wback.color = (0.5, 0.6, 1.0); wback.energy = 0; wback.size = 6
wbo = bpy.data.objects.new("WinBack", wback); s.collection.objects.link(wbo); wbo.location = (-9.0, -21.0, 9.0)
wbo.rotation_euler = (WIN_HEAD - wbo.location).to_track_quat("-Z", "Y").to_euler()
for fr_k, e_k in ((1, 0), (FT(49.7), 900), (FT(51.7), 0)):
    kf(wback, "energy", fr_k, e_k, interp="CONSTANT")
# outro callback: the closet door drifts open a crack behind Milo and two eyes glow in it on "...don't open the door."
ECHO = FT(CUT_OUTRO + ENV["lead"] + 5.3)
for o in KOBJ:
    kf(o, "hide_render", ECHO, False, interp="CONSTANT")
    kf(o, "hide_render", NF + 1, False, interp="CONSTANT")
k_place(FT(CUT_OUTRO) + 1, CRACK + V((0.15, -0.55, -0.4)), 6, interp="CONSTANT"); k_place(ECHO, CRACK + V((0.15, -0.55, -0.4)), 6)
k_place(NF, CRACK + V((0.05, -0.35, -0.4)), 6)
kf(sh, "rotation_euler", FT(CUT_OUTRO) + 1, sh0, interp="CONSTANT")
kf(hd_k, "rotation_euler", FT(CUT_OUTRO) + 1, base_r, interp="CONSTANT")
kf(HINGE, "rotation_euler", ECHO - 12, (0, 0, 0)); kf(HINGE, "rotation_euler", ECHO + 6, (0, 0, DEG(-10)))

# ================================================================== CAMERA (hard cuts; each shot keyed inside its own frames)
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
    """keys: [(u 0..1, pos, tgt, lens)] inside the shot. Hard cut at t0."""
    f0, f1 = FT(t0), FT(t1) - 1
    SHOTS.append((name, f0, f1))
    for i, (u, p, g, l) in enumerate(keys):
        fr = f0 + int(round(u * (f1 - f0)))
        cam_key(fr, p, g, l, interp="CONSTANT" if fr >= f1 else "BEZIER")
    if keys[-1][0] < 1: cam_key(f1, keys[-1][1], keys[-1][2], keys[-1][3], interp="CONSTANT")
    cam.data.dof.aperture_fstop = fstop; cam.data.keyframe_insert("dof.aperture_fstop", frame=f0)
    _LOG.append((cam.data, "dof.aperture_fstop", f0, "CONSTANT"))


def head_of(P, dz=0.0):
    r = P["root"]; return V(r.location) + V((0, 0, 4.6 + dz))


DOOR_OUT = V((0, -30.2, 4.5))
shot("A hook door", 0.0, 2.6, [(0, (2.5, -13.0, 3.2), DOOR_OUT + V((0, 0, 1.5)), 24), (1, (1.6, -17.5, 3.6), DOOR_OUT + V((0, 0, 1.0)), 28)])
SIGN = RB(-200, 6, -20)
shot("B sign + van", 2.6, 4.7, [(0, SIGN + V((24, -27, -1.5)), SIGN + V((-3, 0, 0.5)), 30), (1, SIGN + V((18, -25, -1.0)), SIGN + V((-6, 0, 0.3)), 32)])
ck = []
for i in range(6):
    t = 4.7 + i * 2.5 / 5; vx = van_x(t)
    ck.append((i / 5, (vx - 16, -14, 9.0), (vx + 4, 4, 3.5), 26))
shot("C chase van", 4.7, 7.2, ck)
shot("D lawn, house behind", 7.2, 9.9, [(0, (-1.5, -11.5, 2.6), (-3.0, -24, 5.6), 30), (1, (-1.8, -12.8, 2.7), (-3.0, -24, 5.4), 32)])
shot("E his face", 9.9, 11.9, [(0, (-2.4, -16.2, 4.7), (-3.0, -22, 4.6), 52), (1, (-2.5, -17.4, 4.7), (-3.0, -22, 4.6), 56)])
shot("F fence wide", 11.9, 14.75, [(0, (25.0, -15.0, 5.4), (25.0, -27, 3.6), 26), (1, (25.0, -16.5, 5.2), (25.0, -27, 3.7), 28)])
RH = V((26.7, -27, 4.6)); MH = V((23.3, -27, 4.6))
shot("G Rae close", 14.75, 18.85, [(0, RH + V((-4.8, -3.4, 0.3)), RH, 46), (0.45, RH + V((-4.4, -3.1, 0.25)), RH + V((0, 0, 0.05)), 50), (1, RH + V((-3.8, -2.6, 0.2)), RH, 56)])
shot("H Milo listens", 18.85, 20.2, [(0, MH + V((4.6, -3.2, 0.3)), MH, 50), (1, MH + V((4.2, -2.9, 0.25)), MH, 54)])
RF = RH + V((-0.45, 0, 0.0))
shot("I ECU EVER", 20.2, 21.4, [(0, RH + V((-3.8, -1.6, 0.15)), RF, 48), (0.12, RH + V((-3.5, -1.45, 0.15)), RF, 52),
                                (0.25, RH + V((-3.58, -1.5, 0.2)), RF + V((0, 0, 0.03)), 52), (0.4, RH + V((-3.5, -1.45, 0.13)), RF, 52),
                                (1, RH + V((-3.4, -1.4, 0.15)), RF, 54)])
shot("J two-shot", 21.4, 23.8, [(0, (25.0, -14.0, 5.0), (25.0, -27, 4.0), 28), (1, (25.0, -16.0, 4.9), (25.0, -27, 4.1), 32)])
shot("K Rae lifts the list", 23.8, 25.0, [(0, RH + V((-5.0, -3.6, 0.0)), RH + V((-0.4, 0, -0.3)), 40), (1, RH + V((-4.6, -3.2, 0.0)), RH + V((-0.4, 0, -0.3)), 44)])
NP_ = NOTE_POS + V((0, 0, 3.0))
shot("K2 insert list", 25.0, 26.4, [(0, NP_ + V((0.15, 5.6, 0.5)), NP_ + V((0, 0, 0.4)), 40), (1, NP_ + V((0.05, 3.9, -1.0)), NP_ + V((0, 0, -1.15)), 44)], fstop=5)
shot("L who's left", 26.4, 27.9, [(0, MH + V((4.3, -2.9, 0.2)), MH, 54), (1, MH + V((3.7, -2.5, 0.2)), MH, 60)])
shot("M boarding up", 27.9, 30.8, [(0, (-49.5, 17.5, 6.5), (-57, 29, 7.2), 30), (1, (-50.5, 19.0, 6.8), (-57, 29, 7.4), 34)])
shot("N mansion no door", 30.8, 33.2, [(0, (192, -5, 4.6), (222, 0, 7.5), 26), (1, (208, -1.8, 4.9), (218, 0, 4.8), 34)])
shot("O behind Milo at the window", 33.2, 36.4, [(0, (-8.8, -37.8, 6.4), (-6.0, -20, 4.2), 26), (1, (-8.4, -36.0, 6.0), (-6.4, -20, 4.2), 30)])
shot("P out of the window", 36.4, 38.1, [(0, (-7.25, -30.75, 6.0), (-6, 30, 7), 20), (1, (-7.25, -30.7, 6.0), (-6, 30, 7), 22)], fstop=8)
shot("Q except mine", 38.1, 40.4, [(0, (-26, 6, 7.5), (-2, -32, 5), 26), (1, (-23, 2.5, 7.0), (-2, -32, 5), 30)])
CLK = CLOCK_TEXTS["3:00 AM"].location.copy()
shot("R clock 3AM", 40.4, 41.6, [(0, CLK + V((9.0, 0.8, 0.0)), CLK, 36), (0.15, CLK + V((7.0, 0.6, 0.0)), CLK, 38), (0.22, CLK + V((7.08, 0.6, 0.05)), CLK, 38),
                                 (0.3, CLK + V((6.96, 0.62, -0.04)), CLK, 38), (1, CLK + V((6.4, 0.5, 0.0)), CLK, 40)])
shot("S lamps die", 41.6, 43.3, [(0, (14, -10, 9), (-160, 14, 10), 24), (1, (14, -9, 9), (-160, 14, 9), 26)])
shot("T front door inside", 43.3, 45.8, [(0, (2.0, -43.5, 4.6), (0.4, -31.0, 4.0), 28), (1, (1.8, -42.0, 4.6), (0.5, -31, 4.2), 32)])
shot("U to the window", 45.8, 47.4, [(0, (-1.0, -38.5, 5.0), (-6.0, -32.3, 4.4), 32), (1, (-2.2, -37.4, 5.0), (-6.6, -32.0, 4.5), 36)])
shot("U2 nobody", 47.4, 48.8, [(0, (-7.25, -30.75, 5.9), (-1.5, -22.0, 1.6), 26), (1, (-7.25, -30.7, 5.9), (-1.2, -21.0, 1.4), 28)], fstop=8)
FACE = V((-7.6, -32.6, 5.0))
shot("V it went quiet", 48.8, 52.1, [(0, FACE + V((0.4, -5.8, 0)), FACE, 42), (1, FACE + V((0.3, -4.6, 0.05)), FACE, 46)])
shot("W knocking again", 52.1, 53.95, [(0, FACE + V((0.3, -4.4, 0.05)), FACE, 50), (1, FACE + V((0.25, -4.0, 0.05)), FACE, 52)])
CLD = V((CL_X, CL_Y, 3.0))
shot("W2 closet", 53.95, 55.4, [(0, (-2.5, -37.5, 5.2), CLD, 30), (1, (-1.5, -38.3, 4.8), CLD + V((0, 0, -0.4)), 34)])
FX = FACE + V((0.5, -4.6, 0.1))
shot("X INSIDE my closet", 55.4, 57.5, [(0, FX, FACE, 50), (0.07, FX + V((0.06, 0.0, 0.05)), FACE, 50), (0.14, FX + V((-0.05, 0.0, -0.03)), FACE, 50),
                                        (0.22, FX + V((0.02, 0, 0.0)), FACE, 50), (1, FX + V((0.1, 0.6, 0)), FACE, 56)])
shot("Y the voice", 57.5, 62.35, [(0, (-1.2, -37.6, 4.6), CLD + V((-1.5, 0, 1.6)), 28), (0.48, (1.6, -39.6, 4.5), CRACK, 32),
                                  (0.49, (1.7, -39.65, 4.55), CRACK, 32), (0.51, (1.62, -39.6, 4.47), CRACK, 32),
                                  (0.79, (3.0, -40.6, 4.4), CRACK, 34), (0.8, (2.95, -40.45, 4.42), CRACK, 34),
                                  (0.86, (2.75, -39.6, 4.6), CRACK + V((-0.8, 3.4, 0.1)), 26), (0.9, (2.85, -39.7, 4.55), CRACK + V((-0.7, 3.3, 0.1)), 26),
                                  (0.94, (2.7, -39.5, 4.62), CRACK + V((-0.8, 3.5, 0.1)), 26), (1, (2.8, -39.6, 4.6), CRACK + V((-0.8, 3.4, 0.1)), 26)], fstop=3.2)
shot("Z black", 62.35, CUT_OUTRO, [(0, (3.6, -42.3, 3.0), CLD, 32)])
MC = lambda x, y, z: O + V((x, y, z))
shot("OUTRO", CUT_OUTRO, ENV["total"] + 1 / FPS, [              # same camera moves as test 2 (front wall hidden)
    (0.0, MC(1.8, 11.5, 4.2), MC(0.2, 0, 3.7), 42),
    ((ENV["lead"] + 1.6) / 6.75, MC(1.5, 10.6, 4.3), MC(0.2, 0, 3.8), 44),
    ((ENV["lead"] + 1.95) / 6.75, MC(1.2, 8.4, 4.5), MC(0.1, 0, 4.0), 48),
    ((ENV["lead"] + 3.3) / 6.75, MC(1.0, 8.0, 4.5), MC(0.1, 0, 4.1), 48),
    ((ENV["lead"] + 4.6) / 6.75, MC(0.6, 6.3, 4.7), MC(0.2, 0.9, 4.35), 52),
    (1.0, MC(0.42, 6.2, 4.7), MC(0.25, 1.1, 4.46), 50)])
FRONT_PARTS = [o for o in MILO.children if o.name.split(".")[0] in ("WallFront", "WallFrontTop", "FrontDoor", "Window")]
for o in FRONT_PARTS:
    kf(o, "hide_render", 1, False, interp="CONSTANT"); kf(o, "hide_render", FT(CUT_OUTRO), True, interp="CONSTANT")
# hard cut to black for "It knew my name.": a black card in front of the lens
blk = plane("Blackout", 4, 4, V((0, 0, 0)), pmat("BlackCard", (0, 0, 0), rough=1.0), cam)
blk.location = (0, 0, -0.3); blk.rotation_euler = (DEG(90), 0, 0)
blk.visible_shadow = False
for fr_b, on in ((1, False), (FT(62.35), True), (FT(CUT_OUTRO), False)):
    kf(blk, "hide_render", fr_b, not on, interp="CONSTANT")

# ================================================================== finish: mouths, cut holds, interpolation
flush_mouths()
apply_interp()
hold_cuts()
apply_interpolation()                       # old-style key() curves (day/night, lamps, fades, van)


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
    cuts = [f0 for _, f0, _ in SHOTS[1:]]
    for nm_, rig in RIGS.items():
        for side in ("L", "R"):
            fc = [c for c in _fcurves(rig["blink" + side]) if c.data_path == "scale" and c.array_index == 2]
            if fc:
                for cut in cuts:
                    if any(fc[0].evaluate(f) < 0.9 for f in range(cut - 4, cut)): probs.append(("eyes closed before cut", nm_, cut))
    return probs


probs = check_faces()
print("FACE CHECK", "OK" if not probs else probs[:20])
json.dump({"shots": SHOTS, "nf": NF}, open("/home/claude/talk/shots_p1.json", "w"))

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
