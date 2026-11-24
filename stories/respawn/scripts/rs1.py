# rs1.py - RESPAWN Part 1 "Checkpoint": the scene (27 env scenes from env_rs1.json, split into ~45 cuts).
# World + cards: rs_world.py (Lanternfall) + rs_cast.py (Theo, Wren, Bramble, Ashby, thief, townsfolk).
# Build/checks:  python3 rs1.py      Stills: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 rs1.py
# Storyboard:    python3 _pipeline/make_storyboard.py rs1  (one key still per shot, BOARD panels for big moments)
# The respawn moment (shot "01 ring", RESPAWN_LEN frames) is staged identically at every respawn and listed in
# shots_rs1.json "reuse": the final render copies those frames instead of rendering them again.
import os, math, random
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
exec(open(os.environ.get("KIT_SCR", "/home/claude/bloxbury-blender/") + "rs_world.py").read())
boot("rs1", world="lanternfall", after_rig=(), lead="theo")
load("props4", "studio", "lookdev")
exec(open(SCR + "rs_cast.py").read())

EXTRA_SEEDS = (11, 23, 37, 41, 58, 64, 79, 86, 92, 105)
spec = dict(theo=(make_theo, "rest_flat"), wren=(make_wren, "rest_flat"), bramble=(make_bramble, "rest_smile"),
            ashby=(make_ashby, "rest_smile"), thief=(make_thief, "rest_flat"))
for k, sd in enumerate(EXTRA_SEEDS):
    spec["x%d" % k] = ((lambda sd=sd, k=k: lf_extra("Town%d" % k, sd, age="teen" if k in (3, 7) else "adult")), "rest_flat")
ALLP = cast(**spec)
theo, wren, bramble, ashby, thief = ALLP[:5]; TOWN = list(ALLP[5:])
for k, P in enumerate(TOWN):
    if k not in (3, 7): size_rig(P, (1.0, 1.05, 0.96, 1, 1.08, 0.98, 1.02, 1, 0.95, 1.04)[k])
RG = RIGS
VIS = list(ALLP)

# ---------------------------------------------------------------- sets + props
MK = market_square(); AL = alley(); INN = inn_stairs(); CEL = cellar(); BR = bedroom()
RING = respawn_ring("Ring", (0, 0, 0.0)); HAND = the_hand(); SUNL = sun_lantern(); POLE = lighting_pole()
BIRD = pigeon("Pigeon", (-3.0, -4.0, 9.0)); VOID = void_box()
LADDER = ladder("Ladder", (24.5, 23.0, 0), (24.5, 24.9, 13.1))
APL = apple("LooseApple", (0, 0, -60), None, 0, s=0.42)
rb("BramStep", (6.4, 1.8, 0.9), V((-0.4, 8.7, 0.45)), wood_mat("lf_plank", (140, 98, 60), 4.0), None, r=0.05)
POLE.parent = wren["gripRight"]; POLE.location = V((0, 0.25, -1.95))
SUNL.parent = thief["gripLeft"]; SUNL.location = V((0, 0.2, -1.9))
camera_rig(fstop=2.0); load("cinema", "motion", "mocap")
NG = cinematic_look(split=0.7)
halation(NG, amount=0.06)
grit(0.1)
HS = NG.nodes.new("CompositorNodeHueSat")                            # the time-freeze drains colour (keyed)
_go = [n for n in NG.nodes if n.type == "GROUP_OUTPUT"][0]; _src = _go.inputs[0].links[0].from_socket
NG.links.new(_src, HS.inputs["Image"]); NG.links.new(HS.outputs[0], _go.inputs[0])
SAT = HS.inputs["Saturation"]


def desat(fr, v): kx(SAT, "default_value", fr, v, interp="CONSTANT")


desat(1, 1.0)

# lights: one keyed rim (moves per shot), one keyed key/fill for interiors, haze cards per set
RIM = bpy.data.lights.new("Rim", "SPOT"); RIM.spot_size = DG(40); RIM.spot_blend = 0.6; RIM.shadow_soft_size = 1.2
RIMO = bpy.data.objects.new("Rim", RIM); s.collection.objects.link(RIMO)
for d_ in (AL["lantern"], INN["lantern"], CEL["light"], BR["light"], BR["moon"], MK["stall"]["lantern"]): pass
MOON = spot("AlleyMoon", AL["origin"] + V((0, 30, 40)), AL["origin"] + V((0, 0, 0)), 0, 30, 2.0, lin((140, 165, 255)))
INNWIN = spot("InnWinKey", INN["origin"] + V((10.6, 2, 11)), INN["origin"] + V((-2, 8, 3)), 0, 45, 1.5, lin((150, 175, 255)))
SQFILL = spot("SquareBounce", V((0, -40, 30)), V((0, 0, 3)), 0, 40, 6.0, lin((255, 220, 180)))
HAZE = []
for k, (loc, w, h, n, col, st) in enumerate((
        ((0, 26, 6), 70, 16, (0, -1, 0), (1.0, 0.86, 0.66), 0.18), ((0, -30, 6), 70, 16, (0, 1, 0), (1.0, 0.86, 0.66), 0.14),
        ((0, -100, 6), 30, 14, (0, 1, 0), (1.0, 0.6, 0.4), 0.25),
        (AL["origin"] + V((0, 17, 7)), 10, 16, (0, -1, 0), (0.55, 0.65, 1.0), 0.35), (AL["origin"] + V((0, -10, 5)), 10, 12, (0, -1, 0), (0.55, 0.65, 1.0), 0.12),
        (INN["origin"] + V((2, 0, 9)), 20, 16, (1, 0, 0), (0.8, 0.85, 1.0), 0.12), (CEL["origin"] + V((0, -6, 5)), 18, 10, (0, -1, 0), (1.0, 0.7, 0.4), 0.05))):
    HAZE.append(haze_card("Haze%d" % k, loc, w, h, n, col=col, strength=st))
SHAFT_INN = light_shaft("ShaftInn", INN["origin"] + V((11.2, 2, 10)), INN["origin"] + V((2, 6, 0.5)), width=3.0, col=(0.7, 0.8, 1.0), strength=0.3)
SHAFT_AL = light_shaft("ShaftAlley", AL["origin"] + V((0, 18, 17)), AL["origin"] + V((0, 2, 0.2)), width=4.0, col=(0.6, 0.7, 1.0), strength=0.22)
SHAFT_SQ = light_shaft("ShaftSquare", V((14, 26, 22)), V((2, 4, 0)), width=5.0, col=(1.0, 0.88, 0.7), strength=0.12)

s.frame_set(1)
HDZ = {id(P): P["head"].matrix_world.translation.z - P["root"].matrix_world.translation.z for P in ALLP}
F = lambda t: FT(t)
BOARD = {}                     # shot -> key frames for the storyboard (default: one, after the move lands)
REUSE = []                     # (src_f0, src_f1, dst_f0): identical respawn frames, rendered once


def head(P, loc): return V(loc) + V((0, 0, HDZ[id(P)]))


def win(name, a=None, b=None):
    t0, t1 = SC[name]; return (a if a is not None else t0), (b if b is not None else t1)


def facing(d): return math.degrees(math.atan2(-d[0], d[1]))


def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def stage(f, *Ps, keep=()):
    """(P, loc, yaw) on a cut; everyone else (but keep) parked."""
    on = {id(p[0]) for p in Ps} | {id(P) for P in keep}
    for P in VIS:
        if id(P) not in on: park(P, f)
    for P, loc, yaw in Ps:
        place(P, f, V(loc), yaw); standing(P, f)
        snap_rot(P, "chest", f); snap_rot(P, "neck", f)
        pose_arm(P, "Left", f, euler=(4, 6)); pose_arm(P, "Right", f, euler=(4, -6))


def kneel(P, f, loc, yaw):
    """On both knees (R6: legs swing back, root drops so the knees sit on the floor)."""
    kf(P["root"], "location", f, V(loc) + V((0, 0, -1.5 * P["root"].scale.z)), interp="CONSTANT")
    kf(P["root"], "rotation_euler", f, (0, 0, DG(yaw)), interp="CONSTANT"); _CUTS.append((P["root"], f))
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", f, (DG(-88), 0, 0), interp="CONSTANT")


def rise_from_knees(P, f0, dur, loc, yaw):
    """The respawn gasp: knees -> standing in `dur` frames (eased, small overshoot up)."""
    z0 = V(loc).z - 1.5 * P["root"].scale.z
    for i in range(dur + 1):
        u = ease(i / dur); fr = f0 + i
        kf(P["root"], "location", fr, V(loc) + V((0, 0, (z0 - V(loc).z) * (1 - u) + 0.12 * math.sin(math.pi * u))))
        for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (DG(-88) * (1 - u), 0, 0))


def tod(f, name):
    time_of_day(f, name)


QUIET = []                                                             # deliberate quick actions (check_motion skips them)


def lights(f, **on):
    """Key every set light for the shot starting at f (CONSTANT): names not given go to 0."""
    table = dict(moon=MOON, innwin=INNWIN, sqfill=SQFILL, alley_lan=AL["lantern"], inn_lan=INN["lantern"], candle=CEL["light"],
                 laptop=BR["light"], br_moon=BR["moon"], ring=None)
    for k, d_ in table.items():
        if d_ is None: continue
        kc(d_, "energy", f, on.get(k, 0.0))
    for k, (o, st) in enumerate(HAZE): kc(st, "default_value", f, on.get("haze", {}).get(k, 0.0))
    for nm, (o, st) in (("shaft_inn", SHAFT_INN), ("shaft_al", SHAFT_AL), ("shaft_sq", SHAFT_SQ)):
        kc(st, "default_value", f, on.get(nm, 0.0))


def posts(f, e):
    for r_, lt, ld in MK["posts"] + MK["street"]["posts"]:
        kc(ld, "energy", f, e)


def rim(f, subj, col=(170, 195, 255), e=900.0, back=9.0, up=5.0):
    """Rim/edge light for the shot starting at f: behind the subject, opposite the camera (CONSTANT keys)."""
    s.frame_set(f); cp = cam.matrix_world.translation.copy(); sp = V(subj)
    d = sp - cp; d.z = 0; d = d.normalized() if d.length > 1e-4 else V((0, 1, 0))
    loc = sp + d * back + V((0, 0, up))
    kc(RIMO, "location", f, loc); kc(RIMO, "rotation_euler", f, (sp - loc).to_track_quat("-Z", "Y").to_euler())
    kc(RIM, "energy", f, e); kc(RIM, "color", f, lin(col))


def C(name, t0, t1, subj, board=None, rimc=None, rime=900.0, **kw):
    """cine() + its storyboard key frames + the rim light. subj = P (frames the head) or a point."""
    cine(name, t0, t1, subj, **kw)
    f0, f1 = F(t0), F(t1) - 1
    BOARD[name] = [f0 + int(round(u * (f1 - f0))) for u in (board or (0.6,))]
    sp = subj["head"].matrix_world.translation.copy() if isinstance(subj, dict) else V(subj)
    if isinstance(subj, dict): s.frame_set(f0); sp = subj["head"].matrix_world.translation.copy()
    if rimc is not None: rim(f0, sp, rimc, rime)
    else: kc(RIM, "energy", f0, 0.0)


def black(name, t0, t1):
    """Cut to black: the camera sits inside the void box."""
    o = VOID.location
    shot(name, t0, t1, [(0, o, o + V((0, 10, 0)), 35), (1, o, o + V((0, 10, 0)), 35)])
    kc(RIM, "energy", F(t0), 0.0); BOARD[name] = [F(t0) + 2]


def target(name, P, dz=0.0):
    FRAMING[name][0] = (P["head"], V((0, 0, dz)))


def eyes(*rigs_t):
    for rig, t0, t1 in rigs_t: blinks(rig, t0, t1)


def track(obj, f0, f1, fn):
    _CUTS.append((obj, f0))
    for fr in range(f0, f1 + 1):
        loc, rot = fn(fr)
        kf(obj, "location", fr, V(loc)); kf(obj, "rotation_euler", fr, tuple(DG(a) for a in rot))


def apple_at(f, loc): kf(APL, "location", f, V(loc), interp="CONSTANT")


# market spots
Z0 = 0.0
SPOT = V((0, 0, Z0))                 # the checkpoint (the ring) - Theo faces -Y, the stall behind him
BRAM = V((0.8, 8.6, 0.9))                 # Bramble stands on a plank step behind the counter
DROP = V((0.9, 6.0, 4.9)); FLOOR = V((1.1, 4.8, 0.42)); SHOE = V((0.55, -1.0, 0.42))
TOWN_SPOTS = [(-7, -6, 30), (9, -4, -20), (-11, 3, 90), (10, 2, -100), (-4, -13, 0), (13, -9, 200), (-15, -7, 60),
              (4, 12, 160), (-6, 10, 200), (15, 6, -120)]


def town(f, n=10, idx=None):
    """Townsfolk at their market spots (facing roughly the square's middle); idx = which ones (keep camera lines clear)."""
    out = []
    for k in (idx if idx is not None else range(n)):
        x, y, yw = TOWN_SPOTS[k]
        out.append((TOWN[k], V((x, y, Z0)), yw))
    return out


def town_life(t0, t1, n=10, mood="calm"):
    for P in TOWN[:n]: live(P, t0, t1, mood)


def apple_drop(f0, f_land, f_rest, src=DROP, land=FLOOR, rest=SHOE):
    """Apple falls from Bramble's hand (gravity), one bounce, rolls to Theo's shoe and settles."""
    n = f_land - f0
    for i in range(n + 1):
        u = i / n; p = V((src.x + (land.x - src.x) * u, src.y + (land.y - src.y) * u, src.z - (src.z - land.z) * u * u))
        kf(APL, "location", f0 + i, p)
    kf(APL, "location", f_land + 3, land + V((0, -0.35, 0.35))); kf(APL, "location", f_land + 6, land + V((0, -0.7, 0)))
    m = f_land + 6
    for i in range(1, f_rest - m + 1):
        u = ease(i / (f_rest - m)); kf(APL, "location", m + i, (land + V((0, -0.7, 0))).lerp(rest, u))
        kf(APL, "rotation_euler", m + i, (DG(-720 * u), 0, 0))


def respawn_moment(f0, dst=False):
    """THE RESPAWN (rendered once): ring flash on Theo kneeling at the checkpoint, he gasps upright; Bramble behind
    the counter, two townsfolk. Identical staging every loop (its frames are reused)."""
    stage(f0, (bramble, BRAM, 180), (TOWN[0], V((-7, -6, Z0)), 30), (TOWN[1], V((6.5, -8.5, Z0)), -20))
    kneel(theo, f0, SPOT, 180); snap_rot(theo, "chest", f0, x=-22); snap_rot(theo, "neck", f0, x=-18)
    pose_arm(theo, "Left", f0, euler=(30, 20)); pose_arm(theo, "Right", f0, euler=(30, -20))
    rise_from_knees(theo, f0 + 8, 9, SPOT, 180)
    lean(theo, f0 + 8, x=8, dur=8); look(theo, f0 + 8, x=6, dur=8)
    gesture(theo, "Left", f0 + 9, euler=(12, 14), dur=8); gesture(theo, "Right", f0 + 9, euler=(12, -14), dur=8)
    expr(RG["theo"], f0, "scared", ramp=0); mouth(RG["theo"], f0, "rest_flat"); mouth(RG["theo"], f0 + 8, "small_o")
    mouth(RG["theo"], f0 + 22, "rest_flat")
    expr(RG["bramble"], f0, "content", ramp=0)
    ring_flash(RING, f0 + 1)
    apple_at(f0, V((0, 0, -60)))
    tod(f0, "noon"); desat(f0, 1.0); posts(f0, 0.0); lights(f0, sqfill=30000, haze={0: 0.18, 1: 0.12}, shaft_sq=0.1)


# ================================================================== 1 HOOK: the ring flashes, Theo gasps up (THE RESPAWN, reused)
RESPAWN_LEN = 38
t0, t1 = 0.0, (RESPAWN_LEN) / 24
respawn_moment(1)
C("01 ring", t0, t1, SPOT + V((0, 0, 2.4)), board=(0.05, 0.6), rimc=(255, 120, 110), rime=1200, u=V((-0.3, -1, 0)), size=0.42,
  span=6.2, lens=30, tilt=-6, sy=0.08, move="sink", amt=4, extra=[head(theo, SPOT), BRAM + V((0, 0, 4.2))])
eyes((RG["theo"], t0, t1))
for P in (bramble, TOWN[0], TOWN[1]): live(P, t0, 4.61, "calm")

# 1b Bramble drops the apple ("Mind yourself, lad")
t0, t1 = t1, 2.95
f0 = F(t0)
gesture(bramble, "Right", f0, euler=(70, -10), dur=6)
say(line(2.97), RG["bramble"], "rest_smile", style="calm", nod=3.0, P=bramble)
apple_drop(F(2.8), F(2.87) + 4, F(4.3))
C("01b bramble", t0, t1, bramble, rimc=(255, 220, 180), rime=500, u=V((0.35, -1, 0)), size="MS", lens=40, tilt=6, sy=0.1, move="hold",
  extra=[DROP])
expr(RG["bramble"], f0, "friendly", ramp=0)
look(bramble, f0 + 4, x=-12, dur=8)
live(theo, 1.5, 4.61, "scared")
# 1c Theo mouths it along with him (his lips move on Bramble's words)
t0, t1 = 2.95, 4.61
f0 = F(t0)
L_ = line(2.97); ENV["rms"] = E2["rms"]["bramble"]; ENV["cen"] = E2["cen"]["bramble"]
lipsync(RG["theo"], F(L_["t0"]), F(L_["t1"]) + 1, [(F(L_["t0"]), "rest_flat", "calm")]); mouth(RG["theo"], F(L_["t1"]) + 2, "rest_flat")
expr(RG["theo"], f0, "deadpan", ramp=0)
C("01c mouths along", t0, t1, theo, rimc=(170, 200, 255), rime=900, u=V((-0.15, -1, 0)), size="CU", lens=55, tilt=2, sy=0.1, move="push", amt=1.12,
  board=(0.55,))
target("01c mouths along", theo)

# ================================================================== 2 same apple x3: fear, panic, dead-eyed (cuts every ~1 s)
t0, t1 = win("apple_cuts", b=5.5); f0 = F(t0)
apple_at(f0, SHOE); stage(f0, (theo, SPOT, 180), (bramble, BRAM, 180), keep=())
insert("02 apple shoe", t0, t1, SHOE + V((0, 0, 0.1)), SHOE + V((0, 0, 0.15)), V((0.2, -1, 0.12)), 4.0, 3.2, lens=32, land=0.7, fstop=2.2)
BOARD["02 apple shoe"] = [F(t0) + 12]; kc(RIM, "energy", f0, 0.0)
for k, (a_, b_, ex_, u_, lens_) in enumerate(((5.5, 6.35, "shocked", V((0.5, -1, 0)), 60), (6.35, 7.25, "scared", V((-0.6, -1, 0)), 50),
                                               (7.25, 8.24, "deadpan", V((0.05, -1, 0)), 45))):
    f0 = F(a_); expr(RG["theo"], f0, ex_, ramp=0); mouth(RG["theo"], f0, "small_o" if k == 1 else "rest_flat")
    stage(f0, (theo, SPOT, 180), (bramble, BRAM, 180), (TOWN[0], V((-7, -6, Z0)), 30), (TOWN[1], V((6.5, -8.5, Z0)), -20))
    if k == 2: snap_rot(theo, "neck", f0, x=-6)
    C("02%s face" % "bcd"[k], a_, b_, theo, rimc=(170, 200, 255), rime=900, u=u_, size=("CU", "MCU", "CU")[k], lens=lens_,
      tilt=(4, -10, 0)[k], sy=0.1, move=("hold", "push", "static")[k], amt=1.1, roll=(0, 5, 0)[k])
    target("02%s face" % "bcd"[k], theo)
eyes((RG["theo"], 4.61, 8.24))
live(theo, 5.5, 8.24, "tense")

# ================================================================== 3 bedroom: 3 AM, laptop glow on Theo's face
t0, t1 = win("bedroom"); f0 = F(t0)
BO = BR["origin"]; TB = BO + V((0.0, 3.9, 0))
seated(theo, f0, TB, 0, BO.z + 2.6); _CUTS.append((theo["root"], f0)); stage(f0, keep=(theo,))
seated(theo, f0, TB, 0, BO.z + 2.6)
snap_rot(theo, "chest", f0, x=-12); snap_rot(theo, "neck", f0, x=-6)
pose_arm(theo, "Left", f0, euler=(62, 8)); pose_arm(theo, "Right", f0, euler=(62, -8))
expr(RG["theo"], f0, "content", ramp=0); mouth(RG["theo"], f0, "rest_flat")
tod(f0, "inside"); lights(f0, laptop=1600, br_moon=900); posts(f0, 0.0)
C("03 bedroom", t0, t1, theo, rimc=(120, 150, 255), rime=500, u=V((0.6, 0.8, 0)), size="MCU", lens=28, tilt=4, sy=0.1, move="drift", amt=7,
  fstop=1.8)
target("03 bedroom", theo)
live(theo, t0, 17.87, "calm"); eyes((RG["theo"], t0, 17.87))

# ================================================================== 4 the server list: Lanternfall (1/1), cursor on Join
t0, t1 = win("server_list"); f0 = F(t0)
s.frame_set(f0); bpy.context.view_layer.update()
SCR_PT = BR["screen"].matrix_world.translation.copy(); SCR_N = (BR["lid"].matrix_world.to_3x3() @ V((0, -1, 0))).normalized()
lid_m = BR["screen"].matrix_world
lid_w = BR["lid"].matrix_world
def scr_px(px, py): return lid_w @ V(((px / 800 - 0.5) * 2.4, -0.03, 0.88 + (0.5 - py / 500) * 1.5))   # screen image px -> world
ROW = scr_px(400, 122); JOIN = scr_px(690, 122)
park(theo, f0); kc(BR["light"], "energy", f0, 0.0)
insert("04 server list", t0, t1, SCR_PT, ROW.lerp(JOIN, 0.55), SCR_N, 2.7, 1.5, lens=40, land=0.75, fstop=4.0)
BOARD["04 server list"] = [F(t0) + 10, F(t1) - 8]

# ================================================================== 5 click: the laptop light swallows the room
t0, t1 = win("click"); f0, f1 = F(t0), F(t1) - 1
fc = F(17.22) + 1
SCRM = BR["screen"].active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
kx(SCRM, "default_value", 1, 1.1, interp="CONSTANT"); kx(SCRM, "default_value", fc, 1.1); kx(SCRM, "default_value", f1, 400.0)
kc(BR["light"], "energy", f0, 700); kf(BR["light"], "energy", fc, 700); kf(BR["light"], "energy", f1, 30000)
kx(s.view_settings, "exposure", 1, 0.0, interp="CONSTANT"); kx(s.view_settings, "exposure", fc, 0.0); kx(s.view_settings, "exposure", f1, 4.0)
kx(s.view_settings, "exposure", f1 + 1, 0.0, interp="CONSTANT")
gesture(theo, "Right", f0 + 4, euler=(70, -14), dur=5)
expr(RG["theo"], fc, "shocked"); lean(theo, fc, x=10, dur=6)
C("05 click", t0, t1, theo, rimc=(120, 150, 255), rime=500, u=V((-0.75, 0.7, 0)), size="CU", lens=50, tilt=-2, sy=0.1, move="push", amt=1.2,
  board=(0.3, 0.92), fstop=1.8)
target("05 click", theo)

# ================================================================== 6 first arrival: he stumbles out of the ring, the crowd stares
t0, t1 = win("arrival"); f0, f1 = F(t0), F(t1) - 1
stage(f0, *town(f0, 8), (bramble, BRAM, 180), keep=(theo,))
place(theo, f0, SPOT, 180); standing(theo, f0)
ring_flash(RING, f0 + 1, strength=0.8)
mo_walk(theo, f0 + 6, f1 - 4, [SPOT.xy, (0.6, -3.2)], clip="walk_scared", z=Z0, accel=0.35, blend=10)
# (no extra head turns here: walk_scared carries its own head motion; a look() layered on mo_walk snaps at its end)
expr(RG["theo"], f0, "scared", ramp=0)
for k, P in enumerate(TOWN[:8]):
    x, y, _ = TOWN_SPOTS[k]; place(P, f0, V((x, y, Z0)), facing((0.3 - x, -1.5 - y)))
    expr(RG["x%d" % k], f0 + 6 + k, ("shocked", "curious", "nervous", "annoyed")[k % 4])
town_life(t0, t1, 8, "tense"); live(bramble, t0, t1, "calm")
tod(f0, "noon"); lights(f0, sqfill=30000, haze={0: 0.18, 1: 0.12}, shaft_sq=0.1)
C("06 arrival", t0, t1, SPOT + V((0.3, -1.5, 3.0)), rimc=(255, 220, 190), rime=600, u=V((0.3, -1, 0)), size=0.5, span=12, lens=28, tilt=8,
  sy=0.05, move="pull", amt=1.25, extra=[head(theo, SPOT)], board=(0.25, 0.8))
eyes((RG["theo"], t0, t1))

# ================================================================== 7 Wren vaults the apple stall after the thief
t0, t1 = win("wren_vault", b=22.9); f0, f1 = F(t0), F(t1) - 1
stage(f0, (bramble, V((-2.2, 8.6, 0.9)), 180), *town(f0, idx=(0, 2, 6)), keep=(theo, wren, thief))
place(theo, f0, V((2.6, -2.4, Z0)), 160); standing(theo, f0)
TH0, TH1 = V((-12, 14, Z0)), V((14, -4, Z0))
place(thief, f0, TH0, 120); mo_walk(thief, f0, f1, [TH0.xy, (0, 3.0), TH1.xy], clip="run", z=Z0)
WV0 = V((0.6, 10.4, Z0)); WTOP = V((0.4, 7.0, 3.6)); WV1 = V((0.2, 3.4, Z0))
place(wren, f0, WV0, 180); standing(wren, f0)
fj = f0 + 22; fl = fj + 12
for i in range(fl - fj + 1):
    u = (i) / (fl - fj); p = WV0.lerp(WV1, u) + V((0, 0, 5.2 * 4 * u * (1 - u)))
    kf(wren["root"], "location", fj + i, p)
for h, a in (("hipL", 70), ("hipR", 40)):
    kf(wren[h], "rotation_euler", fj, (0, 0, 0)); kf(wren[h], "rotation_euler", fj + 5, (DG(a), 0, 0))
    kf(wren[h], "rotation_euler", fl, (0, 0, 0))
gesture(wren, "Right", fj - 4, euler=(150, -10), dur=5); gesture(wren, "Left", fj, euler=(80, 30), dur=5)
gesture(wren, "Right", fl - 6, euler=(40, 0), dur=8); gesture(wren, "Left", fl - 4, euler=(30, 10), dur=8)   # arms down before the run
QUIET += list(range(fj - 6, fl + 3))                                   # the vault itself is a deliberate quick action
mo_walk(wren, fl + 1, f1 + 52, [WV1.xy, (-2.5, -4.0), (-8, -12), (-11.5, -17.5)], clip="run", z=Z0, blend=10, end_rest=False)
QUIET += list(range(fl + 1, f1 + 53, 4))                              # run cycles are meant to be fast (as Part 3)
expr(RG["wren"], f0, "determined" if "determined" in EX else "annoyed", ramp=0); mouth(RG["wren"], f0, "rest_flat")
expr(RG["theo"], f0, "shocked", ramp=0); look(theo, fj, z=-25, x=10, dur=8)
expr(RG["bramble"], fj, "shocked")
town_life(t0, t1, 6, "tense"); live(theo, t0, t1, "tense")
C("07 vault", t0, t1, WTOP, rimc=(255, 220, 180), rime=700, u=V((1, -0.7, 0)), size=0.5, span=10, lens=28, tilt=6, sy=0.06,
  move="arc", amt=18, extra=[V((0.2, 3.4, 4.0))])
BOARD["07 vault"] = [fj - 8, fj + 6]
# 7b "Oi! Stop that lantern!" - she skids past Theo
t0, t1 = 22.9, win("wren_vault")[1]; f0, f1 = F(t0), F(t1) - 1
say(line(23.02), RG["wren"], "rest_flat", style="excited", nod=5.0, P=wren)
expr(RG["wren"], f0, "angry" if "angry" in EX else "annoyed", ramp=0)
gesture(wren, "Left", f0 + 6, euler=(95, 40), dur=12)
def wren_head(fr): s.frame_set(fr); return wren["head"].matrix_world.translation.copy()
follow_keys = []
for k in range(6):
    u = k / 5; fr = f0 + int(round(u * (f1 - f0))); p = wren_head(fr); follow_keys.append((u, p + V((-2.0, -8.0, 0.4)), p, 34))
shot("07b oi", t0, t1, follow_keys, fstop=2.0)
FRAMING["07b oi"] = [(wren["head"], V((0, 0, 0)))]; SHOT_META["07b oi"] = ("MS", "follow"); _CINE_ORDER.append("07b oi")
BOARD["07b oi"] = [f0 + 14]; rim(f0, wren_head(f0), (255, 210, 170), 700)
eyes((RG["wren"], t0, t1))

# ================================================================== 8 rooftop: Wren scanning, Theo panting up the ladder
HOUSE = MK["houses"][2]; HX = HOUSE.location; RIDGE_Z = HOUSE["roof_z"]
RW = V((HX.x - 2.5, HX.y - 0.35, RIDGE_Z)); RT = V((HX.x + 1.5, HX.y - 0.35, RIDGE_Z))
t0, t1 = win("rooftop"); f0, f1 = F(t0), F(t1) - 1
stage(f0, (wren, RW, -160), keep=(theo,))
place(theo, f0, V((24.5, 24.3, 9.0)), 0); standing(theo, f0)
kf(theo["root"], "location", f0 + 30, V((24.5, 24.6, 12.0)))
for k in range(0, f1 - f0, 12):
    fr = f0 + k; gesture(theo, "Left" if (k // 12) % 2 else "Right", fr, euler=(140, 0), dur=11)
pose_arm(wren, "Left", f0, euler=(100, 40)); look(wren, f0 + 10, z=-35, dur=14); look(wren, f0 + 50, z=25, dur=14)
expr(RG["wren"], f0, "curious", ramp=0); expr(RG["theo"], f0, "effort" if "effort" in EX else "nervous", ramp=0)
mouth(RG["theo"], f0, "small_o")
tod(f0, "noon"); lights(f0, sqfill=30000, haze={0: 0.2})
live(wren, t0, 39.07, "calm"); live(theo, t0, t1, "tense")
C("08 rooftop", t0, t1, wren, rimc=(255, 230, 200), rime=900, u=V((0.2, -1, 0)), size="MS", lens=30, tilt=-14, sy=0.14, move="crane", amt=16,
  board=(0.3, 0.8))
target("08 rooftop", wren)
eyes((RG["wren"], t0, 39.07))

# ================================================================== 9 the warning ("...the dark comes in")
t0, t1 = 29.31, 33.5; f0 = F(t0)
stage(f0, (wren, RW, -130), (theo, RT, 130))
say(line(29.66), RG["wren"], "rest_flat", style="calm", nod=3.0, P=wren); expr(RG["wren"], f0, "nervous", ramp=0)
look(wren, F(31.2), z=-20, x=8, dur=12)                                   # glances at the bell tower
C("09 last bell", t0, t1, wren, rimc=(255, 220, 180), rime=800, u=V((0.3, -1, 0)), size="MCU", lens=50, tilt=-4, sy=0.12, move="drift",
  amt=6)
target("09 last bell", wren)
t0, t1 = 33.5, 36.4; f0 = F(t0)
say(line(33.73), RG["theo"], "rest_smirk", style="calm", nod=3.0, P=theo); expr(RG["theo"], f0, "grin", ramp=0)
gesture(theo, "Right", f0 + 8, euler=(40, -30), dur=11)
C("09b like night", t0, t1, theo, rimc=(170, 200, 255), rime=800, u=V((-0.35, -1, 0)), size="MS", lens=40, tilt=2, sy=0.12, move="hold")
target("09b like night", theo); live(theo, t0, 39.07, "calm")
t0, t1 = 36.4, win("warning")[1]; f0 = F(t0)
say(line(36.62), RG["wren"], "rest_flat", style="calm", nod=1.5, P=wren); expr(RG["wren"], f0, "deadpan", ramp=0)
C("09c the dark", t0, t1, wren, rimc=(255, 200, 160), rime=900, u=V((0.1, -1, 0)), size="CU", lens=65, tilt=0, sy=0.1, move="push", amt=1.22,
  fstop=1.8)
target("09c the dark", wren)
eyes((RG["theo"], 33.5, 39.07))

# ================================================================== 10 the chase till sunset; the lamps go out one by one
t0, t1 = win("chase_sunset", b=41.6); f0, f1 = F(t0), F(t1) - 1
P0, P1 = V((-1.5, -62, Z0)), V((-1.0, -82, Z0))
stage(f0, keep=(theo, wren))
place(wren, f0, P0, 180); place(theo, f0, P0 + V((2.6, 0.6, 0)), 180)
mo_walk(wren, f0, f1, [P0.xy, P1.xy], clip="run", z=Z0)
mo_walk(theo, f0, f1, [(P0 + V((2.6, 0.6, 0))).xy, (P1 + V((2.6, 0.6, 0))).xy], clip="run", z=Z0)
QUIET += list(range(f0, f1 + 1, 4))
expr(RG["wren"], f0, "annoyed", ramp=0); expr(RG["theo"], f0, "effort" if "effort" in EX else "nervous", ramp=0)
tod(f0, "sunset"); posts(f0, 300.0); lights(f0, haze={2: 0.3})
def chase_pt(fr):
    s.frame_set(fr); return (wren["head"].matrix_world.translation + theo["head"].matrix_world.translation) / 2
ks = []
for k in range(6):
    u = k / 5; fr = f0 + int(round(u * (f1 - f0))); p = chase_pt(fr); ks.append((u, p + V((-5.5, -12.0, 0.6)), p + V((0, 0, -0.4)), 30))
shot("10 chase", t0, t1, ks, fstop=2.4)
FRAMING["10 chase"] = [(wren["head"], V((0, 0, 0)))]; SHOT_META["10 chase"] = ("WS", "follow"); _CINE_ORDER.append("10 chase")
BOARD["10 chase"] = [f0 + 30]; rim(f0, chase_pt(f0), (255, 150, 90), 1200)
eyes((RG["wren"], t0, t1), (RG["theo"], t0, t1))
# 10b the last bell: lamps die toward camera (dusk)
t0, t1 = 41.6, win("chase_sunset")[1]; f0, f1 = F(t0), F(t1) - 1
stage(f0)
tod(f0, "dusk"); posts(f0, 500.0); lights(f0, haze={2: 0.18})
SP = MK["street"]["posts"]
for k, (r_, lt, ld) in enumerate(reversed(SP)):
    fo = f0 + 8 + k * 9
    kf(ld, "energy", fo, 500.0); kf(ld, "energy", fo + 2, 0.0)
    gm = lt.children[0].active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"] if False else None
C("10b lamps out", t0, t1, V((0, -100, 6.0)), u=V((0.05, 1, 0.0)), size=0.6, span=26, lens=24, tilt=-4, sy=0.0, move="static",
  extra=[V((0, -82, 8))], board=(0.15, 0.85))
kc(RIM, "energy", f0, 0.0)

# ================================================================== 11 the back alley, the last bell rang... a white glove (4 frames). Black.
AO = AL["origin"]
t0, t1 = win("alley", b=45.9); f0, f1 = F(t0), F(t1) - 1
TA, WA = AO + V((0.2, 1.0, 0)), AO + V((-0.2, 2.4, 0))
stage(f0, (theo, TA, 180), (wren, WA, 0))
expr(RG["theo"], f0, "scared", ramp=0); expr(RG["wren"], f0, "nervous", ramp=0)
look(theo, f0 + 20, z=30, dur=14); look(wren, f0 + 30, z=-30, dur=14)
pose_arm(wren, "Right", f0, euler=(30, -10))
tod(f0, "night"); posts(f0, 0.0); lights(f0, moon=400000, alley_lan=1500, haze={3: 0.35, 4: 0.1}, shaft_al=0.25)
live(theo, t0, 46.9, "scared"); live(wren, t0, 46.9, "tense")
C("11 back to back", t0, t1, AO + V((0, 1.7, 3.6)), rimc=(140, 165, 255), rime=1500, u=V((0.05, -1, 0)), size=0.42, span=8, lens=28, tilt=4,
  sy=0.06, move="push", amt=1.15, extra=[head(theo, TA), head(wren, WA)], board=(0.5,))
eyes((RG["theo"], t0, 46.9), (RG["wren"], t0, 46.9))
t0, t1 = 45.9, 46.73; f0 = F(t0)
look(theo, f0, z=-8, x=-4, dur=10)
C("11b listening", t0, t1, theo, rimc=(140, 165, 255), rime=1500, u=V((-0.4, -1, 0)), size="CU", lens=60, tilt=0, sy=0.1, move="hold", fstop=1.6)
target("11b listening", theo)
# the glove: 4 frames, Ashby's white hand out of the dark behind Theo
t0, t1 = 46.73, 46.73 + 4 / 24; f0 = F(t0)
ASH = AO + V((3.0, 2.4, 0))
stage(f0, (theo, TA, 180), (ashby, ASH, 180), keep=(wren,))
kc(AL["lantern"], "energy", f0, 5000); kc(AL["lantern"], "energy", f0 + 5, 1500)          # the glove catches the lantern
pose_arm(ashby, "Right", f0, euler=(50, 8)); gesture(ashby, "Right", f0, euler=(58, 4), dur=5)
s.frame_set(f0); GL = ashby["gripRight"].matrix_world.translation.copy() + V((0, 0, -0.3))
C("11c glove", t0, t1, V((GL.x - 0.6, GL.y, GL.z - 0.2)), u=V((0.1, -1, 0)), size=0.4, span=2.0, lens=50, tilt=2, sy=0.0, move="static", extra=[], fstop=2.0,
  rimc=(170, 190, 255), rime=1400)
black("11d black", 46.73 + 4 / 24, win("alley")[1])

# ================================================================== 12 respawn 2: the same ring (reused frames), he catches the apple
t0 = win("respawn_2")[0]; f0 = F(t0)
REUSE.append((1, RESPAWN_LEN, f0))
respawn_moment(f0)
C("12 ring again", t0, t0 + RESPAWN_LEN / 24, SPOT + V((0, 0, 2.4)), board=(0.6,), rimc=(255, 120, 110), rime=1200, u=V((-0.3, -1, 0)), size=0.42,
  span=6.2, lens=30, tilt=-6, sy=0.08, move="sink", amt=4, extra=[head(theo, SPOT), BRAM + V((0, 0, 4.2))])
for P in (bramble, TOWN[0], TOWN[1]): live(P, t0, t0 + RESPAWN_LEN / 24, "calm")
say(line(49.53), RG["bramble"], "rest_smile", style="calm", nod=3.0, P=bramble)
t0, t1 = t0 + RESPAWN_LEN / 24, win("respawn_2")[1]; f0, f1 = F(t0), F(t1) - 1
stage(f0, (theo, V((0.3, 4.2, Z0)), 0), (bramble, BRAM, 180))
fg = f0 + 14
s.frame_set(f0)
apple_at(f0, V((0, 0, -60)))
APS = V((0.9, 6.0, 4.4)); CATCH = V((0.75, 5.3, 3.4))
for i in range(0, 9):
    u = i / 8; kf(APL, "location", f0 + 6 + i, APS.lerp(CATCH, u) - V((0, 0, 0.6 * u * u)))
gesture(theo, "Right", fg - 5, euler=(80, -12), dur=5); QUIET += list(range(fg - 6, fg + 4))   # the catch: quick on purpose
expr(RG["theo"], f0, "determined" if "determined" in EX else "annoyed", ramp=0); expr(RG["bramble"], fg, "shocked")
look(bramble, fg, x=-8, dur=6)
def apple_in_hand(fr):
    s.frame_set(fr); return theo["gripRight"].matrix_world.translation + V((0, 0.2, -1.95))
for fr in range(fg, f1 + 1): kf(APL, "location", fr, apple_in_hand(fr))
live(theo, t0, t1, "tense"); live(bramble, t0, t1, "calm")
C("12b catch", t0, t1, CATCH + V((0, 0, 0.6)), rimc=(255, 220, 180), rime=700, u=V((1, -0.45, 0)), size=0.4, span=5.5, lens=35, tilt=4, sy=0.04,
  move="hold", extra=[head(theo, V((0.3, 4.2, Z0)))], board=(0.55,))
eyes((RG["theo"], t0, t1))

# ================================================================== 13 loop 2: the inn stairs (Stair_crack gap kept), cut to black on the crack
IO = INN["origin"]
t0, t1 = win("stairs", b=55.0); f0, f1 = F(t0), F(t1) - 1
STEP = lambda k: IO + V((-6 + k * 1.0, 9.0, 0.5 + k * 0.72 + 0.15))
stage(f0, (theo, IO + V((-8.2, 6.2, 0)), 60), (wren, STEP(3), -90))
for k in range(4, 10):
    kf(wren["root"], "location", f0 + (k - 3) * 7, STEP(k))
mo_clip(wren, "idle", f0, legs=False) if False else None
look(theo, f0 + 10, x=18, dur=10); expr(RG["theo"], f0, "content", ramp=0); expr(RG["wren"], f0, "content", ramp=0)
tod(f0, "inside"); lights(f0, inn_lan=900, innwin=9000, haze={5: 0.14}, shaft_inn=0.3)
live(theo, t0, t1, "calm")
C("13 inn stairs", t0, t1, IO + V((-3, 8, 5.0)), rimc=(150, 175, 255), rime=600, u=V((0.35, -1, 0)), size=0.5, span=12, lens=26, tilt=6,
  sy=0.04, move="rise", amt=8, extra=[head(theo, IO + V((-8.2, 6.2, 0)))], board=(0.5,))
eyes((RG["theo"], t0, t1), (RG["wren"], t0, t1))
t0, t1 = 55.0, 56.69; f0 = F(t0)
SK = 9
place(wren, f0, STEP(SK), -90)
crack = INN["steps"][SK]; kc(INN["lantern"], "energy", f0, 3000)
kf(crack, "rotation_euler", F(56.3), (0, 0, 0)); kf(crack, "rotation_euler", F(56.55), (DG(-9), DG(4), 0))
C("13b crack", t0, t1, STEP(SK) + V((0, 0, 0.4)), rimc=(255, 200, 150), rime=2000, u=V((-1, -0.3, 0.0)), size=0.4, span=2.2, lens=45, tilt=20,
  sy=0.0, move="push", amt=1.15, extra=[], fstop=1.8)
black("13c black", 56.69, win("stairs")[1])

# ================================================================== 14 loop 3: the cellar, one candle, something breathes. The candle dies.
CO = CEL["origin"]
t0, t1 = win("cellar", b=59.6); f0, f1 = F(t0), F(t1) - 1
TC, WC = CO + V((2.6, 3.0, 0)), CO + V((0.4, 3.4, 0))
s.frame_set(1)
stage(f0, keep=(theo, wren))
kneel(theo, f0, TC, 200); kneel(wren, f0, WC, 160)
snap_rot(theo, "chest", f0, x=-10); snap_rot(wren, "chest", f0, x=-10)
pose_arm(wren, "Left", f0, euler=(40, 30)); pose_arm(theo, "Right", f0, euler=(30, -20))
expr(RG["theo"], f0, "nervous", ramp=0); expr(RG["wren"], f0, "scared", ramp=0)
tod(f0, "inside"); lights(f0, candle=120, haze={6: 0.06})
for fr in range(f0, F(60.76)):
    kf(CEL["light"], "energy", fr, 120 * (1 + 0.08 * math.sin(fr * 0.7) + 0.05 * math.sin(fr * 1.9)))
live(theo, t0, 61.26, "scared"); live(wren, t0, 61.26, "scared")
C("14 cellar", t0, t1, CO + V((1.5, 3.2, 2.6)), rimc=(120, 140, 220), rime=150, u=V((-0.2, -1, 0)), size=0.5, span=4.2, lens=40, tilt=4, sy=0.08,
  move="drift", amt=6, extra=[head(theo, TC - V((0, 0, 1.3))), head(wren, WC - V((0, 0, 1.3)))], fstop=1.8)
eyes((RG["theo"], t0, 61.2), (RG["wren"], t0, 61.2))
t0, t1 = 59.6, 60.76; f0 = F(t0)
EYES = [o for o in CEL["root"].children if o.name.startswith("DarkEye")]
EM = EYES[0].active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
kx(EM, "default_value", 1, 0.0, interp="CONSTANT"); kx(EM, "default_value", f0 + 6, 0.0); kx(EM, "default_value", f0 + 16, 1.6)
kx(EM, "default_value", F(60.8), 1.6); kx(EM, "default_value", F(61.3), 0.0)
look(theo, f0, z=40, x=-4, dur=12); look(wren, f0, z=-30, dur=12)
C("14b the dark", t0, t1, CO + V((-5.5, -10.0, 4.6)), u=V((0.45, 1, 0.05)), size=0.5, span=9, lens=30, tilt=0, sy=0.0, move="push", amt=1.1,
  extra=[], board=(0.8,), fstop=2.0)
t0, t1 = 60.76, 61.26; f0 = F(t0)
FL = CEL["flame"]
FS0 = FL.scale.copy(); kf(FL, "scale", f0, tuple(FS0)); kf(FL, "scale", f0 + 6, tuple(FS0 * 0.25)); kf(FL, "scale", f0 + 7, tuple(FS0 * 0.01))
kf(CEL["light"], "energy", f0, 120); kf(CEL["light"], "energy", f0 + 7, 0.0)
insert("14c candle out", t0, t1, CEL["candle_pt"], CEL["candle_pt"], V((-0.3, -1, 0.1)), 1.6, 1.5, lens=50, land=0.6, fstop=2.0)
BOARD["14c candle out"] = [f0 + 2]; kc(RIM, "energy", f0, 0.0)
black("14d black", 61.26, win("cellar")[1])

# ================================================================== 15 back at the stall: he runs to Wren... "Sorry... have we met?"
t0, t1 = win("back_to_wren", b=64.4); f0, f1 = F(t0), F(t1) - 1
WS = V((-3.2, 4.2, Z0)); T0_ = V((0, 0, Z0)); T1_ = V((-2.4, 1.6, Z0))
stage(f0, (wren, WS, -140), (bramble, BRAM, 180), *town(f0, idx=(0, 2, 4, 6, 7, 8)), keep=(theo,))
place(theo, f0, T0_, 180); mo_walk(theo, f0 + 2, f1 - 6, [T0_.xy, (-1.2, -0.6), T1_.xy], clip="jog", z=Z0)
expr(RG["theo"], f0, "excited", ramp=0); mouth(RG["theo"], f0, "grin_open")
expr(RG["wren"], f0, "content", ramp=0); mouth(RG["wren"], f0, "rest_smile")
pose_arm(wren, "Left", f0, euler=(50, 10))
tod(f0, "noon"); posts(f0, 0.0); lights(f0, sqfill=30000, haze={0: 0.18, 1: 0.12}, shaft_sq=0.1)
town_life(t0, 69.68, 6, "calm"); live(wren, t0, 69.68, "calm"); live(bramble, t0, 69.68, "calm")
C("15 run to her", t0, t1, V((-1.4, 1.4, 3.6)), rimc=(255, 230, 200), rime=700, u=V((0.75, -0.7, 0)), size=0.45, span=8, lens=30, tilt=4, sy=0.06,
  move="truck" if False else "arc", amt=16, extra=[head(wren, WS)])
t0, t1 = 64.4, win("back_to_wren")[1]; f0 = F(t0)
place(theo, f0, T1_, facing((WS - T1_).xy)); standing(theo, f0)
place(wren, f0, WS, facing((T1_ - WS).xy)); standing(wren, f0)
say(line(64.47), RG["wren"], "rest_smile", style="calm", nod=2.0, P=wren); expr(RG["wren"], f0, "friendly", ramp=0)
C("15b have we met", t0, t1, wren, rimc=(255, 220, 180), rime=800, toward=theo, ang=22, size="MCU", lens=55, tilt=2, sy=0.12, move="hold")
target("15b have we met", wren)
expr(RG["theo"], F(65.0), "sad"); mouth(RG["theo"], F(65.0), "rest_frown")
eyes((RG["wren"], 62.06, 69.68), (RG["theo"], 62.06, 69.68))

# ================================================================== 16 alone: the slow push, the market moving round him (the scene's push)
t0, t1 = win("alone"); f0, f1 = F(t0), F(t1) - 1
stage(f0, (theo, V((0, -2.0, Z0)), 180), (bramble, BRAM, 180), keep=tuple(TOWN[:8]))
expr(RG["theo"], f0, "sad", ramp=0); mouth(RG["theo"], f0, "rest_frown")
paths = [((-12, 1.5), (12, 2.5)), ((10, 4), (-10, 3.5)), ((-9, -9), (-6, 9)), ((8, -9), (6, 9)), ((-14, 6), (12, 7)),
         ((14, -3), (4, 12)), ((-14, -4), (-4, 12)), ((7, 10), (-12, 0))]      # behind + beside him, never across the lens
for k, (a_, b_) in enumerate(paths):
    P = TOWN[k]; place(P, f0, V((a_[0], a_[1], Z0)), facing((b_[0] - a_[0], b_[1] - a_[1])))
    mo_walk(P, f0, f1 + 20, [a_, b_], clip="walk", z=Z0, phase=k * 0.17)
C("16 alone", t0, t1, theo, rimc=(255, 220, 190), rime=900, u=V((0.1, -1, 0)), size=0.1, span=1.35, lens=50, tilt=8, sy=0.12, move="push",
  amt=1.25, board=(0.2, 0.9))
target("16 alone", theo)
eyes((RG["theo"], t0, t1)); live(theo, t0, t1, "still")

# ================================================================== 17 the fourth time: he walks straight up to Wren and grabs her hand
t0, t1 = win("grab"); f0, f1 = F(t0), F(t1) - 1
G0, G1 = V((3.5, -6, Z0)), V((-1.6, 2.2, Z0))
stage(f0, (wren, WS, -140), (bramble, BRAM, 180), *town(f0, idx=(1, 3, 5, 7, 9)), keep=(theo,))
place(theo, f0, G0, facing((G1 - G0).xy)); mo_walk(theo, f0, f1 - 12, [G0.xy, G1.xy], clip="walk", z=Z0)
gesture(theo, "Right", f1 - 10, euler=(62, -30), dur=5); QUIET += list(range(f1 - 11, f1 - 2))   # the grab; gesture(wren, "Left", f1 - 8, euler=(55, 15), dur=6)
look(wren, f1 - 20, z=30, dur=10); expr(RG["wren"], f1 - 8, "shocked")
expr(RG["theo"], f0, "determined" if "determined" in EX else "annoyed", ramp=0)
C("17 grab", t0, t1, V((-1.4, 1.6, 3.4)), rimc=(255, 220, 190), rime=800, u=V((-0.3, -1, 0)), size=0.45, span=6.5, lens=35, tilt=6, sy=0.05,
  move="arc", amt=20, extra=[head(wren, WS)], board=(0.4, 0.92))
eyes((RG["theo"], t0, t1))

# ================================================================== 18 two-shot: "Wren. Listen. I've died three times today..." -> FREEZE
t0, t1 = win("two_shot", b=75.6); f0 = F(t0)
TT, WT = V((-3.0, -1.0, Z0)), V((-4.6, 0.6, Z0))
stage(f0, (theo, TT, facing((WT - TT).xy)), (wren, WT, facing((TT - WT).xy)), (bramble, BRAM, 180), *town(f0, idx=(3, 7, 9)))
pose_arm(theo, "Right", f0, euler=(55, -30)); pose_arm(wren, "Left", f0, euler=(50, 20))
say(line(73.16), RG["theo"], "rest_flat", style="excited", nod=4.0, P=theo); expr(RG["theo"], f0, "nervous", ramp=0)
expr(RG["wren"], f0, "nervous", ramp=0); mouth(RG["wren"], f0, "rest_flat"); lean(wren, f0 + 20, x=8, dur=14)
live(theo, t0, 78.13, "tense"); live(wren, t0, 78.13, "tense"); town_life(t0, 78.13, 4)
C("18 listen", t0, t1, theo, rimc=(255, 220, 190), rime=900, toward=wren, ang=42, size="MCU", lens=45, tilt=2, sy=0.12, move="drift", amt=6)
target("18 listen", theo)
t0, t1 = 75.6, 78.13; f0 = F(t0)
lean(wren, f0, x=14, dur=12); gesture(wren, "Left", f0 + 6, euler=(30, 30), dur=8); look(wren, f0, z=12, dur=10)
expr(RG["wren"], f0, "scared"); mouth(RG["wren"], f0, "rest_frown")
C("18b pulling away", t0, t1, wren, rimc=(255, 220, 190), rime=900, toward=theo, ang=-26, size="CU", lens=60, tilt=0, sy=0.1, move="hold",
  fstop=1.6)
target("18b pulling away", wren)
eyes((RG["theo"], 72.86, 78.1), (RG["wren"], 72.86, 78.1))
# the freeze hits: colour drains, the pigeon and the apple hang in the air
FZ = F(78.13)
t0, t1 = 78.13, win("two_shot")[1]
desat(FZ, 0.12)
stage(FZ, (theo, TT, facing((WT - TT).xy)), (wren, WT, facing((TT - WT).xy)), (bramble, BRAM, 180), *town(FZ, idx=(3, 7, 8, 9)))
apple_at(FZ, V((0.9, 5.6, 2.6)))
kf(BIRD, "location", 1, V((-3.0, -4.0, 9.0)), interp="CONSTANT")
kf(BIRD, "location", FZ, V((-3.6, -0.5, 7.5)), interp="CONSTANT")
kf(BIRD, "location", F(88.28), V((0, 0, -60)), interp="CONSTANT")
tod(FZ, "noon"); lights(FZ, sqfill=30000)
C("18c freeze", t0, t1, V((-3.4, 0.4, 4.6)), u=V((0.35, -1, 0)), size=0.6, span=10, lens=26, tilt=10, sy=0.02, move="static",
  extra=[V((-3.6, -0.5, 7.5))], rimc=(200, 210, 230), rime=500)
for P in VIS:                                         # everyone but Theo stops dead (no life layer in the freeze)
    pass

# ================================================================== 19 "Everything stopped. Except me." Theo turns his head (swivel, not a reverse)
t0, t1 = win("freeze"); f0 = F(t0)
look(theo, f0 + 6, z=-40, dur=16); look(theo, f0 + 40, z=25, dur=16)
expr(RG["theo"], f0, "scared", ramp=0)
live(theo, t0, 89.33, "scared")
FWT = (WT - TT).normalized(); U19 = V((FWT.x * math.cos(DG(35)) - FWT.y * math.sin(DG(35)), FWT.x * math.sin(DG(35)) + FWT.y * math.cos(DG(35)), 0))
C("19 except me", t0, t1, theo, rimc=(200, 210, 230), rime=700, u=U19, size="MCU", lens=45, tilt=0, sy=0.12, move="arc", amt=26)
target("19 except me", theo)
eyes((RG["theo"], t0, 89.3))

# ================================================================== 20 THE HAND: over his shoulder, toward his chest. "Not. Yours. To tell."
t0, t1 = win("hand", b=85.6); f0, f1 = F(t0), F(t1) - 1
s.frame_set(f0)
FW = V((-math.sin(theo["root"].rotation_euler.z), math.cos(theo["root"].rotation_euler.z), 0))
SD = V((FW.y, -FW.x, 0))
HD = head(theo, TT); CHEST = TT + V((0, 0, 2.9 * theo["root"].scale.z)) + FW * 0.75 + SD * 0.15
H0 = HD - FW * 3.0 - SD * 1.0 + V((0, 0, 1.8)); H1 = HD - FW * 0.2 - SD * 0.95 + V((0, 0, -0.1)); H2 = CHEST + FW * 0.1
def hand_at(fr):
    if fr < f0 + 40: u = ease((fr - f0) / 40); a_, b_ = H0, H1
    else: u = ease((fr - f0 - 40) / 30); a_, b_ = H1, H2
    p = a_.lerp(b_, u); d = (b_ - a_).normalized()
    e = d.to_track_quat("Z", "Y").to_euler(); return p, tuple(math.degrees(v) for v in e)
track(HAND["root"], f0, F(88.28), hand_at)
park(wren, f0)                                       # she stands behind the lens in the hand close-ups
kf(HAND["root"], "location", 1, V((0, 0, -80)), interp="CONSTANT"); kf(HAND["root"], "location", F(88.28) + 1, V((0, 0, -80)), interp="CONSTANT")
for k, (pv, p2) in enumerate(HAND["fingers"]):
    kf(pv, "rotation_euler", f0, (DG(15), 0, 0)); kf(p2, "rotation_euler", f0, (DG(10), 0, 0))
    fc_ = F(86.6) + k
    kf(pv, "rotation_euler", fc_, (DG(15), 0, 0)); kf(pv, "rotation_euler", fc_ + 6, (DG(78), 0, 0))
    kf(p2, "rotation_euler", fc_, (DG(10), 0, 0)); kf(p2, "rotation_euler", fc_ + 6, (DG(70), 0, 0))
for k, w_ in enumerate(HAND["wisps"]):
    for fr in range(f0, F(88.28), 4):
        kf(w_, "rotation_euler", fr, (DG(90 + 14 * math.sin(fr * 0.07 + k)), 0, DG(k * 37 + fr * 0.6)))
look(theo, f0 + 4, z=-20, x=-6, dur=12)
C("20 the hand", t0, t1, HD - SD * 0.6 + V((0, 0, -0.2)), u=(FW - SD * 0.6).normalized(), size=0.45, span=3.6, lens=40, tilt=2, sy=0.04,
  move="push", amt=1.12, extra=[HD], fstop=1.8, rimc=(200, 210, 230), rime=700, board=(0.35, 0.9))
t0, t1 = 85.6, 88.28; f0 = F(t0)
expr(RG["theo"], f0, "shocked", ramp=0); mouth(RG["theo"], f0, "small_o")
C("20b closes", t0, t1, HD + V((0, 0, -0.9)) + FW * 0.4, u=(FW - SD * 0.4).normalized(), size=0.55, span=2.6, lens=55, tilt=-4, sy=0.02,
  move="hold", extra=[HD], fstop=1.6, rimc=(200, 210, 230), rime=700, board=(0.3, 0.85))
black("20c black", 88.28, win("black")[1])
desat(F(88.28), 1.0)

# ================================================================== 21 respawn 3: dim. On his knees at the stall.
t0, t1 = win("respawn_3"); f0 = F(t0)
stage(f0, (bramble, BRAM, 180), (TOWN[0], V((-7, -6, Z0)), 30), keep=(theo,))
kneel(theo, f0, V((0.2, 1.4, Z0)), 180); snap_rot(theo, "chest", f0, x=-26); snap_rot(theo, "neck", f0, x=-20)
pose_arm(theo, "Left", f0, euler=(25, 20)); pose_arm(theo, "Right", f0, euler=(25, -20))
expr(RG["theo"], f0, "sad", ramp=0); mouth(RG["theo"], f0, "rest_frown")
ring_flash(RING, f0 - 6, strength=0.45)
tod(f0, "dim"); lights(f0, sqfill=8000, haze={0: 0.1})
apple_at(f0, V((0, 0, -60)))
live(theo, t0, 101.4, "still"); live(bramble, t0, t1, "calm")
C("21 dim respawn", t0, t1, V((0.2, 1.4, 2.4)), u=V((-0.1, -1, 0)), size=0.5, span=8, lens=26, tilt=28, sy=0.06, move="hold",
  extra=[BRAM + V((0, 0, 4.0))], rimc=(255, 140, 120), rime=600)
eyes((RG["theo"], t0, 104.3))

# ================================================================== 22 the apple rolls PAST him... to polished black shoes. A white glove.
t0, t1 = win("apple_glove", b=97.6); f0, f1 = F(t0), F(t1) - 1
SH = V((-1.0, -7.5, Z0))
stage(f0, (ashby, SH, 0), keep=(theo, bramble))
for i in range(0, f1 - f0 + 1):
    u = ease(i / (f1 - f0)); kf(APL, "location", f0 + i, V((0.8, 3.0, 0.42)).lerp(SH + V((1.5, 1.1, 0.42)), u))
    kf(APL, "rotation_euler", f0 + i, (DG(900 * u), 0, 0))
C("22 apple rolls", t0, t1, SH + V((0.5, 2.6, 0.6)), u=V((1, -0.1, 0.0)), size=0.4, span=4.0, lens=32, tilt=-2, sy=-0.1, move="push", amt=1.12,
  extra=[], fstop=2.0, rimc=(255, 220, 190), rime=400)
t0, t1 = 97.6, win("apple_glove")[1]; f0, f1 = F(t0), F(t1) - 1
APR = SH + V((1.5, 1.1, 0.42))
apple_at(f0, APR)
place(ashby, f0, SH, 0)
lean(ashby, f0 + 4, x=-40, dur=10); gesture(ashby, "Right", f0 + 4, euler=(45, -2), dur=10)
gesture(ashby, "Right", F(98.62) + 2, euler=(85, -2), dur=8); lean(ashby, F(98.62) + 2, x=-10, dur=8)
def apple_glove(fr):
    s.frame_set(fr); g = ashby["gripRight"].matrix_world.translation + V((0, 0.1, -0.35))
    return APR.lerp(g, ease(min(1.0, (fr - F(98.62)) / 4)))             # quick snatch: 4 frames from the cobbles into the glove
for fr in range(F(98.62), f1 + 30): kf(APL, "location", fr, apple_glove(fr))
GE = apple_glove(f1); C("22b glove", t0, t1, APR.lerp(GE, 0.55), u=V((0.9, 0.45, 0)), size=0.4, span=max(2.0, (GE - APR).length + 1.0), lens=45, tilt=10, sy=0.0, move="rise", amt=6,
  extra=[], fstop=1.8, rimc=(255, 220, 190), rime=400, board=(0.2, 0.85))

# ================================================================== 23 only a smile: "Welcome back, Theo."
t0, t1 = win("smile"); f0 = F(t0)
place(ashby, f0, SH, 0); standing(ashby, f0); snap_rot(ashby, "chest", f0); snap_rot(ashby, "neck", f0, x=-6)
pose_arm(ashby, "Right", f0, euler=(70, -10)); pose_arm(ashby, "Left", f0, euler=(4, 6))
for fr in range(f0, F(t1) + 1): kf(APL, "location", fr, apple_glove(fr))
mouth(RG["ashby"], f0, "rest_smile"); expr(RG["ashby"], f0, "content", ramp=0)
s.frame_set(f0); AH = ashby["head"].matrix_world.translation.copy()
C("23 smile", t0, t1, AH + V((0, 0, -0.35)), u=V((0.15, 1, 0)), size=0.5, span=2.2, lens=60, tilt=-8, sy=0.27, move="rise", amt=6,
  extra=[], fstop=1.6, rimc=(255, 220, 190), rime=500)
live(ashby, t0, t1, "still")

# ================================================================== 24 Theo's face: nobody here knows my name
t0, t1 = win("theo_face"); f0 = F(t0)
stage(f0, (bramble, BRAM, 180), keep=(theo, ashby))
kneel(theo, f0, V((0.2, 1.4, Z0)), 200); snap_rot(theo, "chest", f0, x=-8); snap_rot(theo, "neck", f0, x=10)
expr(RG["theo"], f0, "scared", ramp=0); mouth(RG["theo"], f0, "rest_flat")
C("24 his name", t0, t1, theo, u=V((0.2, -1, 0)), size="CU", lens=60, tilt=6, sy=0.12, move="hold", fstop=1.6, rimc=(255, 220, 190), rime=900)
target("24 his name", theo)

# ================================================================== 25 Wren across the square looks back a beat too long
t0, t1 = win("wren_look"); f0 = F(t0)
WL = V((-9.0, -12.0, Z0))
stage(f0, (wren, WL, facing((-0.36, 0.93))), *town(f0, idx=(1, 2, 3, 5, 6, 7)), keep=(theo,))
look(wren, f0 + 14, z=-55, dur=16); look(wren, F(107.6), z=-40, dur=14)
expr(RG["wren"], f0, "curious", ramp=0); mouth(RG["wren"], f0, "rest_flat")
town_life(t0, t1, 8); live(wren, t0, t1, "still")
C("25 wren looks back", t0, t1, wren, u=V((0.75, 0.66, 0)), size="MS", lens=85, tilt=1, sy=0.12, move="hold", fstop=1.6,
  rimc=(255, 220, 190), rime=900, board=(0.35, 0.8))
target("25 wren looks back", wren)
eyes((RG["wren"], t0, t1))

# ================================================================== 26 the loop: wide on the checkpoint, then the respawn ring again (reused)
t0, t1 = win("ring_loop")[0], 111.66; f0 = F(t0)
stage(f0, (bramble, BRAM, 180), *town(f0, 8)[:8], keep=(theo,))
place(theo, f0, SPOT, 180); standing(theo, f0)
expr(RG["theo"], f0, "sad", ramp=0); mouth(RG["theo"], f0, "rest_flat")
tod(f0, "noon"); lights(f0, sqfill=30000, haze={0: 0.18, 1: 0.12}, shaft_sq=0.1)
town_life(t0, t1, 8); live(theo, t0, t1, "still")
C("26 checkpoint", t0, t1, SPOT + V((0, 0, 2.5)), u=V((0.2, -0.6, 0.0)), size=0.25, span=7, lens=30, tilt=60, sy=0.0, move="crane", amt=14,
  extra=[BRAM + V((0, 0, 4))], rimc=(255, 220, 190), rime=700)
t0 = 111.66; f0 = F(t0)
REUSE.append((1, RESPAWN_LEN, f0))
respawn_moment(f0)
C("26b ring", t0, t0 + RESPAWN_LEN / 24, SPOT + V((0, 0, 2.4)), board=(0.6,), rimc=(255, 120, 110), rime=1200, u=V((-0.3, -1, 0)), size=0.42,
  span=6.2, lens=30, tilt=-6, sy=0.08, move="sink", amt=4, extra=[head(theo, SPOT), BRAM + V((0, 0, 4.2))])
for P in (bramble, TOWN[0], TOWN[1]): live(P, t0, t0 + RESPAWN_LEN / 24, "calm")
t0, t1 = t0 + RESPAWN_LEN / 24, win("ring_loop")[1]; f0 = F(t0)
C("26c hold", t0, t1, theo, u=V((-0.15, -1, 0)), size="MCU", lens=50, tilt=2, sy=0.1, move="hold", rimc=(170, 200, 255), rime=900)
target("26c hold", theo)
eyes((RG["theo"], 108.19, 114.41))

# ================================================================== finish
def tidy_lips(rig):
    log = sorted(set(rig.get("lip_log", [])))
    drop, last = set(), -9
    for fa, ma in log:                       # every shape holds >= 3 frames (fast lines read as chatter otherwise)
        if fa - last < 3 and ma != "M": drop.add((fa, ma))
        else: last = fa
    rig["lip_log"] = [e for e in log if e not in drop]
    ev = _MEV[id(rig)][1]; ev[:] = [e for e in ev if (e[0], e[1]) not in drop]


for k in ("theo", "wren", "bramble"): tidy_lips(RG[k])
_dump_shots = run_checks


def run_checks(allow=(), motion_chars=None, quiet=(), **kw):
    r = _dump_shots(allow, motion_chars, quiet, air=("MoonDust", "Smear", "Haze", "Shaft", "Wisp", "Ring"), **kw)
    j = TALK + "shots_%s.json" % PART; d = json.load(open(j)); d["board"] = BOARD; d["reuse"] = REUSE; json.dump(d, open(j, "w"))
    return r


ALLOW = ("11c glove", "14 cellar", "11d black", "13c black", "14d black", "20c black", "04 server list", "14b the dark", "23 smile")
finish_part(life=True, allow=ALLOW, quiet=QUIET, motion_chars=None if not os.environ.get("MOTION") else {"theo": theo, "wren": wren})
