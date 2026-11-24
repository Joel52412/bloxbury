# hm1.py - HEIGHT MOG "The Trenchcoat Mayor": the scene (24 timed scenes from env_hm1.json, a few split into 2 cuts).
# Set-up = hm1_assets.py (approved v3): Tallton town (Bloxbury map + props7), Kai, the three short guys in the coat.
# Build/checks:  python3 hm1.py      Stills:  RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 FRAMES=a,b python3 hm1.py
# Preview:       python3 _pipeline/preview_local.py hm1.py [--all]     Storyboard: python3 _pipeline/make_storyboard.py hm1
import os, math, random
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
boot("hm1", world="bloxbury", after_rig=(), lead="kai")
load("props4", "studio", "lookdev", "props7")
exec(open(SCR + "hm1_cast.py").read())


def shades(P):
    """Flat black sunglasses (two lenses + bridge) on the head layer."""
    h = P.get("head") or P["neck"]; fy = surf_y(0) + 0.02; m = P["M"]("Shades", (15, 15, 18), rough=0.15)
    for s_ in (-1, 1): rb("ShadeLens", (0.36, 0.06, 0.22), V((s_ * 0.24, fy, 0.72)), m, h, r=0.06)
    rb("ShadeBridge", (0.2, 0.05, 0.05), V((0, fy + 0.01, 0.77)), m, h, r=0.02)


CROWD_SEEDS = (51, 63, 74, 88, 95)
spec = dict(kai=(make_kai, "rest_smile"), top=(make_guy_top, "rest_flat"), mid=(make_guy_mid, "rest_flat"),
            bot=(make_guy_bot, "rest_flat"), tall=(lambda: random_extra("Tall", 28, role="office"), "rest_smirk"),
            avg=(lambda: random_extra("Avg", 11, role="casual"), "rest_flat"), aide=(lambda: random_extra("Aide", 7, role="office"), "rest_flat"))
for k, sd in enumerate(CROWD_SEEDS):
    spec["c%d" % k] = ((lambda sd=sd, k=k: random_extra("Crowd%d" % k, sd)), "rest_flat")
ALLP = cast(**spec)
kai, top, mid, bot, tall, avg, aide = ALLP[:7]; CROWD = ALLP[7:]
size_rig(tall, 1.12); size_rig(avg, 0.93); size_rig(aide, 0.95)
for k, P in enumerate(CROWD): size_rig(P, (0.92, 1.0, 1.05, 0.96, 1.1)[k])
shades(tall); hm_mustache(top)
ST = build_stack(bot, mid, top)
GUYS = (top, mid, bot)
COAT_OBJS = [ST["coat"]["root"]] + list(ST["coat"]["root"].children_recursive) + \
    [o for o in top["root"].children_recursive if o.name.split(".")[0] in ("SleeveLeft", "SleeveRight", "CuffLeft", "CuffRight",
                                                                            "GloveLeft", "GloveRight", "GloveSeam")]
TOP_HAT = [o for o in top["neck"].children_recursive if o.name.split(".")[0] in ("HatBrim", "HatTop", "HatBand")]
SHOE_OBJS = [o for r in ST["shoes"] for o in [r] + list(r.children_recursive)]

# ---------------------------------------------------------------- sets (as approved on the asset sheet)
for head_, m_, ld_ in LAMPS: ld_.energy = 0                     # daytime: street lamps off
for o in [o for o in bpy.data.objects if o.name.split(".")[0] in ("LampPole", "LampArm", "StreetLamp") and o.location.x > 160]:
    o.hide_render = True
for o in [o for o in bpy.data.objects if o.name.split(".")[0] in ("LampPole", "LampArm", "StreetLamp", "LampHead") and -80 < o.location.x < -30]:
    o.hide_render = True                         # clear the bus stop (a pole stood in front of the door)
PLAZA = hm_plaza((190, 0))
HALL = hm_town_makeover(houses)
STAGE = hm_stage((210, 0))
CURT = hm_curtain((700, 0, 400.0))
BUS = hm_bus("Bus", (-60, -6, 0.2)); BUS["root"].rotation_euler = (0, 0, math.radians(-90))
CAR = car("ShinyCar", body=(200, 28, 40), loc=V((-20, -17.5, 0.4))); CAR.rotation_euler = (0, 0, math.radians(-90))
DOG = hm_dog("Dog", (0, 0, 0))
TABLE = hm_banquet("Banquet", (120, 30, 0.4))
PEN = hm_pen("Pen", (0, 0, 0))


# ---------------------------------------------------------------- the ending coat: Kai on top of all three (ten feet, eight shoes)
ROOT2 = empty("Stack2", V((0, 0, 0)), col=COL_CHARS)          # identity until the ending: Kai's keys stay world coords
kai["root"].parent = ROOT2
KAI_TOP_Z = 7.4                                               # Kai's feet inside coat 2 (his shoulders at ~9.85)
COAT2 = hm_coat(ROOT2, kai, shoulder=10.25, belt=6.6, w_top=3.4, w_hem=6.0, d_top=1.6, d_hem=2.3)
SHOES2 = []
for k, (x, yaw_) in enumerate(((-0.4, 0), (0.4, 0), (-1.15, 0), (1.15, 0), (-1.9, 180), (1.9, 180), (-2.6, 8), (2.6, -8))):
    SHOES2.append(hm_shoe("YShoe%d" % k, V((x, 0.15 if yaw_ != 180 else -0.15, 0)), yaw_, ROOT2,
                          col=[(250, 205, 60), (250, 205, 60), (40, 30, 26), (40, 30, 26), (60, 60, 70), (60, 60, 70), (220, 60, 60), (220, 60, 60)][k]))
HATP = empty("KaiHatPivot", V((0, 0, 0.3)), col=COL_CHARS); HATP.parent = kai["neck"]
_before = set(bpy.data.objects)
hat_tophat(HATP, kai["M"], (214, 172, 70))
KAI_HAT = [o for o in bpy.data.objects if o not in _before]
COAT2_OBJS = [COAT2["root"]] + list(COAT2["root"].children_recursive) + KAI_HAT + \
    [o for o in kai["root"].children_recursive if o.name.split(".")[0] in ("SleeveLeft", "SleeveRight", "CuffLeft", "CuffRight",
                                                                            "GloveLeft", "GloveRight", "GloveSeam")] + \
    [o for r in SHOES2 for o in [r] + list(r.children_recursive)]
PACK = [o for o in kai["root"].children_recursive if o.name.split(".")[0] in ("Backpack", "BPPocket", "BPStrap", "BPStrapTop")]

# ---------------------------------------------------------------- extra props for the scene
def calendar_img():
    im = Image.new("RGB", (900, 1200), (250, 246, 232)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 899, 230), fill=(40, 50, 90))
    d.text((450, 80), "TALLTON", font=pfont(96), fill=(240, 190, 50), anchor="mm")
    d.text((450, 175), "TOWN HALL ROTA", font=pfont(58), fill=(250, 246, 232), anchor="mm")
    days = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
    for k, dname in enumerate(days):
        y = 330 + k * 170
        d.line((60, y + 75, 840, y + 75), fill=(200, 190, 170), width=4)
        d.text((90, y), dname, font=pfont(70), fill=(40, 50, 90), anchor="lm")
        d.text((820, y), ("speech", "SWAP DAY", "ribbon", "speech", "nap")[k], font=pfont(46), fill=(120, 110, 100), anchor="rm")
    y = 330 + 170
    d.ellipse((50, y - 78, 600, y + 78), outline=(215, 35, 40), width=14)          # TUESDAY circled in red
    return save_img(im, "hm_calendar")


def build_board(loc, yaw):
    """Town-hall notice board on two posts: framed calendar + a little roof (faces -X like the stage)."""
    r = root_of("NoticeBoard", loc); r.rotation_euler = (0, 0, math.radians(yaw))
    wd = dmat("hm_board_wood", (110, 70, 42), rough=0.7); navy = dmat("hm_board_navy", (40, 50, 90), rough=0.6)
    for sx in (-1.7, 1.7): rb("BoardPost", (0.3, 0.3, 6.6), V((sx, 0, 3.3)), wd, r, r=0.05)
    rb("BoardBack", (3.9, 0.25, 4.6), V((0, 0, 4.1)), navy, r, r=0.08)
    rb("BoardRoof", (4.5, 0.9, 0.25), V((0, 0.15, 6.55)), wd, r, r=0.06, rot=(math.radians(-12), 0, 0))
    plane("Calendar", 3.3, 4.4, V((0, 0.14, 4.1)), imgmat("hm_calendar", calendar_img(), rough=0.8), r)
    for sx, sz in ((-1.55, 6.2), (1.55, 6.2)): rcyl("BoardPin", 0.09, 0.08, V((sx, 0.16, sz)), dmat("hm_pin", (215, 35, 40)), r, axis="Y", seg=12)
    return r


BOARD = build_board(V((196.0, 14.0, 0.4)), 90)                 # faces -X (toward the square)
bpy.context.view_layer.update()
BOARD_PT = BOARD.matrix_world @ V((0, 0.14, 4.1))
TUE_PT = BOARD.matrix_world @ V((-0.55, 0.14, 4.1 + 2.2 - 500 / 1200 * 4.4))
PLATE = rcyl("MayorPlate", 0.6, 0.08, V((0, 0, 0)), dmat("hm_plate", (245, 245, 240), rough=0.3), None, seg=24)
rcyl("PlateFood", 0.3, 0.12, V((0, 0, 0.08)), dmat("hm_roast", (150, 80, 40), rough=0.6), PLATE, seg=16)
rb("PlatePea", (0.12, 0.12, 0.12), V((0.35, 0.1, 0.08)), dmat("hm_pea", (80, 160, 60)), PLATE, r=0.05)
PLATE.parent = top["gripRight"]; PLATE.location = V((0, 0.35, -2.05))
EYE = root_of("PeekEye", (0, 0, 0)); EYE.parent = ST["coat"]["root"]; EYE.location = V((-0.5, 0.74, 5.45))
rcyl("PeekWhite", 0.17, 0.04, V((0, 0, 0)), dmat("hm_eye_w", (250, 250, 250), rough=0.3), EYE, axis="Y", seg=16)
rcyl("PeekPupil", 0.08, 0.04, V((0.02, 0.02, 0)), dmat("hm_eye_k", (12, 12, 14), rough=0.2), EYE, axis="Y", seg=12)
FLAT = root_of("CoatFlat", (0, 0, 0))                          # the coat lying open after the topple
cmat = dmat("hm_coat", COAT_KHAKI, rough=0.75); cdk = dmat("hm_coat_dk", tuple(int(c * 0.72) for c in COAT_KHAKI), rough=0.8)
for sx in (-1, 1):
    rb("FlatPanel", (2.6, 8.6, 0.2), V((sx * 1.9, 0, 0.1)), cmat, FLAT, r=0.08, rot=(0, 0, math.radians(sx * 6)))
    rb("FlatSleeve", (1.2, 3.2, 0.35), V((sx * 4.0, 2.4, 0.17)), cmat, FLAT, r=0.12, rot=(0, 0, math.radians(sx * 35)))
    rb("FlatCollar", (1.2, 0.9, 0.3), V((sx * 0.9, 4.2, 0.16)), cmat, FLAT, r=0.08)
rb("FlatBelt", (7.0, 0.36, 0.26), V((0, -0.8, 0.24)), cdk, FLAT, r=0.08)
rb("FlatBuckle", (0.6, 0.48, 0.08), V((0.1, -0.8, 0.39)), dmat("hm_buckle", (214, 172, 70), metal=0.9, rough=0.3), FLAT, r=0.05)
for bx, by in ((-1.2, 1.5), (-1.2, -2.4), (1.4, 1.5), (1.4, -2.4)):
    rcyl("FlatBtn", 0.14, 0.08, V((bx, by, 0.24)), dmat("hm_btn", (70, 48, 30), rough=0.4), FLAT, seg=12)
PUFFS = [rcyl("Puff%d" % k, 0.5, 0.5, V((0, 0, -50)), dmat("hm_puff", (150, 150, 155), rough=1.0), None, seg=12) for k in range(6)]
WING = None


def area(name, loc, tgt, energy, size, col):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = V(loc); o.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler(); return o


C = CURT.location
WING = area("WingKey", C + V((9, -4, 9)), C + V((6, -2.8, 3)), 0, 3, (1.0, 0.85, 0.65))     # backstage: one warm work light

camera_rig(); load("cinema", "motion", "mocap")
set_day(0.0); house_lights(0.0, False)

# ================================================================== helpers
s.frame_set(1)
HDZ = {}
for P in ALLP: HDZ[id(P)] = P["head"].matrix_world.translation.z - P["root"].matrix_world.translation.z
Z0 = 0.4                                     # plaza floor
DECK = 2.4                                   # stage deck
WZ = C.z                                     # backstage floor
F = lambda t: FT(t)                          # seconds -> frame
VIS = [kai, top, mid, bot, tall, avg, aide] + list(CROWD)


def head(P, loc):
    """Head centre of P standing with its root at loc (world)."""
    return V(loc) + V((0, 0, HDZ[id(P)]))


def gz(x, y, z0=3.0):
    dg = bpy.context.evaluated_depsgraph_get(); hit = s.ray_cast(dg, V((x, y, z0)), V((0, 0, -1)))
    return hit[1].z if hit[0] else 0.4


def win(name, a=None, b=None):
    """Shot window (t0, t1) of env scene `name`, optionally cut at a / b."""
    t0, t1 = SC[name]; return (a if a is not None else t0), (b if b is not None else t1)


def stage_cast(f, *Ps, keep=()):
    """Place the listed (P, loc, yaw_facing) on frame f (a cut); everyone else in VIS (but `keep`) goes to the parking lot."""
    on = {id(p[0]) for p in Ps} | {id(P) for P in keep}
    for P in VIS:
        if id(P) not in on and P not in GUYS: park(P, f)
    for P, loc, yaw in Ps:
        place(P, f, V(loc), yaw); standing(P, f)
        snap_rot(P, "chest", f); snap_rot(P, "neck", f)
        pose_arm(P, "Left", f, euler=(4, 6)); pose_arm(P, "Right", f, euler=(4, -6))


def facing(d):
    """Yaw (deg) that turns a rig (front +Y at yaw 0) to face direction d=(x, y)."""
    return math.degrees(math.atan2(-d[0], d[1]))


def track(obj, f0, f1, fn):
    """Key obj's location + rotation on EVERY frame f0..f1 from fn(frame) -> (loc, (rx, ry, rz) degrees). f0 is a cut."""
    _CUTS.append((obj, f0))
    for fr in range(f0, f1 + 1):
        loc, rot = fn(fr)
        kf(obj, "location", fr, V(loc)); kf(obj, "rotation_euler", fr, tuple(math.radians(a) for a in rot))


def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def damp(t, f=1.6, k=5.0):
    """Damped wobble 0 -> peaks -> settles (t in seconds since the hit)."""
    return math.sin(2 * math.pi * f * t) * math.exp(-k * t) if t > 0 else 0.0


def stack_in(f, coat=True):
    """The three guys back inside the coat (stacked, arms up holding the guy above): on a cut."""
    for P, z in zip((bot, mid, top), STACK_Z):
        kf(P["root"], "location", f, V((0, 0, z)), interp="CONSTANT"); kf(P["root"], "rotation_euler", f, (0, 0, 0), interp="CONSTANT")
        standing(P, f)
    for P in (bot, mid):
        for sd in ("Left", "Right"): pose_arm(P, sd, f, euler=(165, 0))
    pose_arm(top, "Left", f, euler=(4, -6)); pose_arm(top, "Right", f, euler=(4, 6))
    for o in COAT_OBJS + SHOE_OBJS: vis_obj(o, f, coat)


def coat_vis(f, on):
    for o in COAT_OBJS + SHOE_OBJS: vis_obj(o, f, on)


def coat2_vis(f, on):
    for o in COAT2_OBJS: vis_obj(o, f, on)
    for o in PACK: vis_obj(o, f, not on)


def stack_still(f0, f1, loc, yaw, fn=None):
    """Stack 1 standing at loc (floor point), facing yaw; fn(fr) -> (dloc, drot) adds wobble etc."""
    def g(fr):
        dl, dr = fn(fr) if fn else ((0, 0, 0), (0, 0, 0))
        return V(loc) + V(dl), (dr[0], dr[1], yaw + dr[2])
    track(ST["root"], f0, f1, g)


def stack2(f0, f1, fn):
    track(ROOT2, f0, f1, fn)


def kai_top(f0, f1):
    """Kai rides coat 2: his root sits KAI_TOP_Z up inside it (local to Stack2)."""
    _CUTS.append((kai["root"], f0))
    for fr in range(f0, f1 + 1):
        kf(kai["root"], "location", fr, V((0, 0, KAI_TOP_Z))); kf(kai["root"], "rotation_euler", fr, (0, 0, 0))
    standing(kai, f0)


def eyes(*rigs_t):
    for rig, t0, t1 in rigs_t: blinks(rig, t0, t1)


def target(name, P, dz=0.0):
    """Framing check follows the head object (moving / parented subjects) instead of the script-time point."""
    FRAMING[name][0] = (P["head"], V((0, 0, dz)))


TOP_HZ = STACK_Z[2] + HDZ[id(top)]                              # top guy's head above the stack floor point
RG = RIGS
MAYOR_STAGE = V((210.0, -3.6, DECK))                            # beside the podium, clear of it (hook fix)
KAI_HOOK = V((204.3, -1.2, Z0))

# park everything not in a shot; Stack 2 is identity (Kai uses world coords) until the ending
kf(DOG["root"], "location", 1, V((0, 0, -60)), interp="CONSTANT")
kf(ROOT2, "location", 1, V((0, 0, 0)), interp="CONSTANT"); kf(ROOT2, "rotation_euler", 1, (0, 0, 0), interp="CONSTANT")
coat2_vis(1, False); vis_obj(EYE, 1, False); vis_obj(FLAT, 1, False)
for o in FLAT.children: vis_obj(o, 1, False)
for o in EYE.children: vis_obj(o, 1, False)
vis_obj(PLATE, 1, False)
for o in PLATE.children: vis_obj(o, 1, False)
for pf in PUFFS: kf(pf, "scale", 1, (0.01, 0.01, 0.01))


# ================================================================== 1 HOOK: low angle, the 9-ft mayor on the stage, tiny Kai looking up
def hook_staging(f, f_end, wobble_at=None):
    stage_cast(f, (kai, KAI_HOOK, -90), (CROWD[0], (199.5, 6.5, Z0), -110), (CROWD[1], (200.0, -10.5, Z0), -70),
               (CROWD[2], (201.5, 3.5, Z0), -100), (aide, (207.5, -8.0, DECK), 10))
    stack_in(f)
    def wob(fr):
        if wobble_at is None: return (0, 0, 0), (0, 0, 0)
        t = (fr - wobble_at) / FPS
        return (0, 0, 0), (0, 2.6 * damp(t, 1.4, 3.2), 0)            # the coat wobbles once (rewatch detail)
    stack_still(f, f_end, MAYOR_STAGE, 90, wob)
    pose_arm(top, "Right", f, euler=(135, -35))
    snap_rot(kai, "neck", f, x=24); expr(RG["kai"], f, "curious", ramp=0); expr(RG["top"], f, "smug", ramp=0)
    for P in (kai, CROWD[0], CROWD[1], CROWD[2], aide): live(P, f / FPS, f_end / FPS, "calm")


t0, t1 = win("hook_mayor_stage")
HOOK_SUBJ = MAYOR_STAGE + V((0, 0, 4.6))
hook_staging(1, F(t1) - 1, wobble_at=F(2.8))
cine("01 hook", t0, t1, HOOK_SUBJ, u=V((-1, -0.18, 0)), size=0.42, span=10.5, lens=26, tilt=-8, sy=0.12, sx=0.04,
     move="sink", amt=5, extra=[head(kai, KAI_HOOK), MAYOR_STAGE + V((0, 0, 0.3))])
look(top, F(2.6), z=-8, dur=8); look(top, F(3.0), z=0, dur=6)
eyes((RG["kai"], t0, t1), (RG["top"], t0, t1))

# ================================================================== 2 tall guy + shiny car
t0, t1 = win("tall_car"); f0, f1 = F(t0), F(t1) - 1
c = CAR.location; TALL = V((c.x - 1.0, c.y - 4.4, gz(c.x - 1.0, c.y - 4.4)))
stage_cast(f0, (tall, TALL, 195))
pose_arm(tall, "Left", f0, euler=(20, 30)); snap_rot(tall, "chest", f0, y=-6); expr(RG["tall"], f0, "smug", ramp=0)
gesture(tall, "Right", f0 + 10, euler=(40, -30), dur=10)              # a lazy "yeah, that's mine" hand toward the car
look(tall, f0 + 6, x=6, z=-10, dur=10)
live(tall, t0, t1, "calm"); eyes((RG["tall"], t0, t1))
cine("02 car", t0, t1, head(tall, TALL), u=V((0.62, -0.78, 0)), size="MS", lens=32, tilt=2, sx=0.1, sy=0.1, move="arc", amt=14,
     )
target("02 car", tall)

# ================================================================== 3 bus: the average guy steps on
t0, t1 = win("bus"); f0, f1 = F(t0), F(t1) - 1
b = BUS["root"].location; DOOR = V((b.x + 11.8, b.y - 5.3, 0))
gzb = gz(DOOR.x, DOOR.y - 3)
AV0 = V((b.x + 7.5, b.y - 12.0, gzb)); KAI_BUS = V((b.x - 19.0, b.y - 3.0, gz(b.x - 19, b.y - 3)))
stage_cast(f0, (avg, AV0, 0), (kai, KAI_BUS, -90))
mo_walk(avg, f0, f1 - 7, [AV0.xy, (DOOR.x - 0.5, DOOR.y - 2.2), (DOOR.x, DOOR.y - 0.6)], clip="walk", z=gzb, style={"arms": 0.35})
for i in range(1, 8):                                              # up the step into the door
    u = ease(i / 7); kf(avg["root"], "location", f1 - 7 + i, V((DOOR.x, DOOR.y - 0.6 + 1.1 * u, gzb + 0.7 * u)))
expr(RG["avg"], f0, "content", ramp=0); mouth(RG["avg"], f0, "rest_smile")
expr(RG["kai"], f0, "sad", ramp=0); live(kai, t0, t1, "still")
eyes((RG["avg"], t0, t1))
cine("03 bus", t0, t1, V((DOOR.x - 1.5, DOOR.y - 2.0, 4.2)), u=V((0.15, -1, 0)), size=0.55, span=12, lens=22, tilt=6, sy=0.05,
     move="drift", amt=6, extra=[DOOR + V((0, -0.6, 3.0))])

# ================================================================== 4 Kai walks behind the bus (it pulls away)
t0, t1 = win("behind_bus"); f0, f1 = F(t0), F(t1) - 1
BX0 = b.x
def bus_at(fr):
    u = (fr - f0) / (f1 - f0); return V((BX0 + 26 * (u ** 2.2), b.y, b.z))
track(BUS["root"], f0, f1, lambda fr: (bus_at(fr), (0, 0, -90)))
kf(BUS["root"], "location", f1 + 1, V((BX0, b.y, b.z)), interp="CONSTANT")       # back at the kerb for the rest of the film
KJ0 = V((b.x - 20.5, b.y - 2.2, 0)); KJ1 = V((b.x - 6.0, b.y - 2.2, 0))
ZS = 0.2                                                           # street surface
stage_cast(f0, (kai, V((KJ0.x, KJ0.y, ZS)), -90))
mo_walk(kai, f0, f1, [KJ0.xy, KJ1.xy], clip="jog", z=ZS)
expr(RG["kai"], f0, "annoyed", ramp=0); mouth(RG["kai"], f0, "rest_flat")
EXH = b + V((-15.4, 2.6, 1.0))
for k, pf in enumerate(PUFFS):                                     # exhaust puffs: grow, drift back, shrink away
    fa = f0 + 4 + k * 11; fb = fa + 22
    kf(pf, "scale", fa - 1, (0.01, 0.01, 0.01))
    for i in range(0, 23, 2):
        u = i / 22; fr = fa + i; src = bus_at(min(fa, f1)) + V((-15.4, 2.4 + 0.3 * k % 2, 1.0))
        kf(pf, "location", fr, src + V((-2.5 * u, -0.4 + 0.3 * math.sin(k + u * 3), 1.2 * u)))
        sc = 0.3 + 2.0 * u if u < 0.75 else (2.3 * (1 - u) / 0.25)
        kf(pf, "scale", fr, (max(0.01, sc),) * 3)
eyes((RG["kai"], t0, t1))
def follow(name, t0, t1, P, path_fn, off, lens, look_dz=0.0, lag=0.85):
    """Camera keeps pace with a moving subject (same direction, slight lag, eases in and out); framing follows its head."""
    fa, fb = F(t0), F(t1) - 1; keys = []
    for k in range(6):
        u = k / 5; fr = fa + int(round(u * (fb - fa)))
        p = path_fn(fr); keys.append((u, p + off, p + V((0, 0, look_dz)), lens))
    shot(name, t0, t1, keys)
    FRAMING[name] = [(P["head"], V((0, 0, 0)))]; SHOT_META[name] = ("WS", "follow"); _CINE_ORDER.append(name)
def kai_path(fr):
    u = ease((fr - f0) / (f1 - f0)); return KJ0.lerp(KJ1, u * 0.85) + V((0, 0, 2.6))
follow("04 behind bus", t0, t1, kai, kai_path, V((-3.0, -11.0, -1.3)), 28, look_dz=0.6)

# ================================================================== 5 the mayor glides past; people bow (button peek = rewatch detail)
t0, t1 = win("mayor_glide"); f0, f1 = F(t0), F(t1) - 1
GL0, GL1 = V((150.0, -3.0, 0)), V((174.0, -3.0, 0)); zg = gz(160, -3)
def glide(fr):
    u = (fr - f0) / (f1 - f0); u = 0.12 * u + 0.88 * ease(u)
    return GL0.lerp(GL1, u) + V((0, 0, zg))
stack_in(f0)
track(ST["root"], f0, f1, lambda fr: (glide(fr), (0, 0, -90)))
bows = [(CROWD[0], (154, -8.5), 0), (avg, (159, -8.5), 0), (CROWD[1], (158, 3.5), 180), (CROWD[3], (164, 3.5), 180), (aide, (170, 3.5), 180)]
stage_cast(f0, *[(P, V((x, y, gz(x, y))), yw) for P, (x, y), yw in bows])
for k, (P, (x, y), yw) in enumerate(bows):
    fb = f0 + int((x - 150) / 24 * (f1 - f0)) - 8
    look(P, max(f0 + 2, fb - 10), z=40 if yw == 0 else -40, dur=10)
    lean(P, max(f0 + 4, fb), x=-26, dur=10); look(P, max(f0 + 4, fb), x=-10, dur=10)
    live(P, t0, t1, "calm")
look(top, f0 + 10, z=12, dur=14); look(top, f0 + 50, z=-10, dur=16)
fp = f0 + 58                                                       # the middle button gaps for 4 frames: an eye peeks out
btn = ST["coat"]["buttons"][0]; b0 = btn.location.copy()
kf(btn, "location", fp - 1, b0); kf(btn, "location", fp + 1, b0 + V((0.25, 0.12, -0.05)))
kf(btn, "location", fp + 4, b0 + V((0.25, 0.12, -0.05))); kf(btn, "location", fp + 6, b0)
vis_obj(EYE, fp, True); vis_obj(EYE, fp + 5, False)
for o in EYE.children: vis_obj(o, fp, True); vis_obj(o, fp + 5, False)
expr(RG["top"], f0, "smug", ramp=0)
eyes((RG["top"], t0, t1))
def glide_cam(fr): return glide(fr) + V((0, 0, 4.4))
follow("05 glide", t0, t1, top, glide_cam, V((-3.0, -14.5, -1.4)), 24, look_dz=0.4)

# ================================================================== 6 "Taxes... doubled." close on the mustache, way up high
t0, t1 = win("mayor_close"); f0, f1 = F(t0), F(t1) - 1
MC = V((GL1.x, GL1.y, zg))
stack_still(f0, f1, MC, -90)
stage_cast(f0, (CROWD[2], (MC.x + 5.5, MC.y - 4.5, zg), 60), (CROWD[4], (MC.x + 6.5, MC.y + 3.0, zg), 120))
say(line(14.47), RG["top"], "rest_flat", style="calm", nod=4.0, P=top)
expr(RG["top"], f0, "smug", ramp=0); gesture(top, "Right", f0 + 4, euler=(88, -28), dur=8)
gesture(top, "Right", f1 - 14, euler=(10, 8), dur=10)
for P in (CROWD[2], CROWD[4]): live(P, t0, t1, "calm")
expr(RG["c2"], f0 + 20, "sad"); expr(RG["c4"], f0 + 22, "annoyed")
eyes((RG["top"], t0, t1))
cine("06 taxes doubled", t0, t1, MC + V((0, 0, TOP_HZ)), u=V((1, -0.45, 0)), size="CU", lens=60, tilt=-16, sx=-0.04, sy=0.1,
     move="hold")
target("06 taxes doubled", top)

# ================================================================== 7 Kai squints at him (to camera)
t0, t1 = win("kai_squint"); f0, f1 = F(t0), F(t1) - 1
KS = V((182.0, -9.0, gz(182, -9)))
stage_cast(f0, (kai, KS, 160))
snap_rot(kai, "neck", f0, x=14, z=-35); look(kai, f0 + 10, x=2, z=0, dur=10)
expr(RG["kai"], f0, "curious", ramp=0); expr(RG["kai"], f0 + 14, "annoyed"); mouth(RG["kai"], f0, "rest_flat")
live(kai, t0, t1, "calm"); eyes((RG["kai"], t0, t1))
cine("07 kai squint", t0, t1, head(kai, KS), u=V((-0.34, -0.94, 0)), size=0.3, span=1.1, lens=50, tilt=1, sy=0.06, move="static")
target("07 kai squint", kai)

# ================================================================== 8 town dinner: everyone sits, the mayor stands, plate at his chin
t0, t1 = win("dinner"); f0, f1 = F(t0), F(t1) - 1
tb = TABLE.location
seats = [(kai, (tb.x + 3.4, tb.y - 5), -90 + 180 - 180, 1.4), (avg, (tb.x + 3.4, tb.y + 1), 90 - 180, 1.86),
         (aide, (tb.x - 3.4, tb.y - 4), 90, 1.9), (CROWD[0], (tb.x + 3.4, tb.y + 7), 90 - 180, 1.9), (CROWD[1], (tb.x - 3.4, tb.y + 6), 90, 1.9)]
stage_cast(f0, *[(P, V((x, y, tb.z + 1.9 - dz)), yw) for P, (x, y), yw, dz in seats])
for P, _, _, _ in seats:
    for hh in ("hipL", "hipR"): kf(P[hh], "rotation_euler", f0, (math.radians(90), 0, 0), interp="CONSTANT")
    live(P, t0, t1, "calm")
stack_in(f0); MD = V((tb.x - 3.3, tb.y + 1, tb.z))
stack_still(f0, f1, MD, -90)
pose_arm(top, "Right", f0, euler=(118, 4)); vis_obj(PLATE, f0, True); vis_obj(PLATE, f1 + 1, False)
for o in PLATE.children: vis_obj(o, f0, True); vis_obj(o, f1 + 1, False)
snap_rot(top, "neck", f0, x=-6); expr(RG["top"], f0, "smug", ramp=0)
look(kai, f0 + 8, z=40, x=10, dur=10); expr(RG["kai"], f0, "deadpan", ramp=0)
eyes((RG["top"], t0, t1), (RG["kai"], t0, t1))
cine("08 dinner", t0, t1, MD + V((0, 0, 5.4)), u=V((1, -0.2, 0)), size=0.5, span=10.5, lens=30, tilt=8, sy=0.04,
     move="drift", amt=6, extra=[MD + V((0, 0, TOP_HZ))])

# ================================================================== 9 he never bends down: the pen drops, an aide picks it up
t0, t1 = win("pen_drop"); f0, f1 = F(t0), F(t1) - 1
MP = V((180.0, 12.0, Z0))
stack_in(f0); stack_still(f0, f1, MP, 0)              # facing +Y (camera on the side)
pose_arm(top, "Left", f0, euler=(32, -6))
s.frame_set(f0); g0 = top["gripLeft"].matrix_world.translation.copy() + V((0, 0, -0.6))
PEN_FLOOR = V((MP.x - 1.6, MP.y + 2.0, Z0 + 0.06))
fd = f0 + 6
kf(PEN, "location", 1, V((0, 0, -60)), interp="CONSTANT"); kf(PEN, "location", f0, g0, interp="CONSTANT")
kf(PEN, "rotation_euler", f0, (math.radians(70), 0, 0))
for i in range(1, 9):                                                   # falls (gravity), bounces once
    u = i / 8; kf(PEN, "location", fd + i, g0.lerp(PEN_FLOOR, u) * 1 + V((0, 0, (g0.z - PEN_FLOOR.z) * (u - u * u) * 0)))
    kf(PEN, "location", fd + i, V((g0.x + (PEN_FLOOR.x - g0.x) * u, g0.y + (PEN_FLOOR.y - g0.y) * u, g0.z - (g0.z - PEN_FLOOR.z) * u * u)))
kf(PEN, "rotation_euler", fd + 8, (0, 0, math.radians(30)))
kf(PEN, "location", fd + 10, PEN_FLOOR + V((0, 0, 0.18))); kf(PEN, "location", fd + 12, PEN_FLOOR)
kf(PEN, "rotation_euler", fd + 12, (0, 0, math.radians(38)))
look(top, fd + 12, x=-22, dur=8)                                         # stares down. does not bend.
AID0 = V((MP.x - 9.0, MP.y + 3.0, Z0)); AID1 = V((PEN_FLOOR.x - 2.2, PEN_FLOOR.y + 0.4, Z0))
stage_cast(f0, (aide, AID0, -90))
mo_walk(aide, f0 + 2, f0 + 26, [AID0.xy, AID1.xy], clip="walk", z=Z0, style={"arms": 0.35})
lean(aide, f0 + 27, x=-48, dur=8); gesture(aide, "Right", f0 + 27, euler=(70, 6), dur=8)
gesture(aide, "Right", f1 - 6, euler=(95, 6), dur=7); lean(aide, f1 - 6, x=-30, dur=7)
s.frame_set(f1 - 6); s.frame_set(f1)
hand = aide["gripRight"].matrix_world.translation.copy() + V((0, 0, -0.8))
kf(PEN, "location", f1 - 6, PEN_FLOOR); kf(PEN, "location", f1, hand)
kf(PEN, "location", f1 + 1, V((0, 0, -60)), interp="CONSTANT")
expr(RG["top"], f0, "smug", ramp=0); expr(RG["aide"], f0 + 26, "nervous")
live(aide, t0, t1, "calm"); eyes((RG["top"], t0, t1), (RG["aide"], t0, t1))
cine("09 pen", t0, t1, MP + V((-1.6, 0, 4.6)), u=V((-0.3, 1, 0)), size=0.6, span=11.5, lens=30, tilt=4, sy=0.0,
     move="hold", extra=[PEN_FLOOR, MP + V((0, 0, TOP_HZ))])

# ================================================================== 10 the dog sniffs the coat ... and the coat sneezes
t0, t1 = win("dog_sniff", b=25.6); f0, f1 = F(t0), F(t1) - 1
MS_ = V((178.0, -14.0, Z0)); MYAW = 160                           # coat faces (-0.34, -0.94): toward the camera side
FW = V((-math.sin(math.radians(MYAW)), math.cos(math.radians(MYAW)), 0))
SIDE = V((FW.y, -FW.x, 0))                                         # coat's right-hand side (screen left)
NOSE = MS_ + FW * 1.35 - SIDE * 0.9                                # sniff spot on the front of the hem, slightly to one side
DDIR = (-SIDE + FW * 0.25).normalized()                            # the dog walks in from screen right, toward that spot
D1 = NOSE - DDIR * 2.15; D0 = D1 - DDIR * 8.0
fA = F(27.36)                                                      # "achoo"
def sneeze(fr):
    if fr < fA - 2: return (0, 0, 0), (0, 0, 0)
    tt = (fr - fA + 2) / FPS
    return (0, 0, 0.3 * max(0.0, damp(tt, 2.4, 6.0))), (-5.0 * damp(tt, 2.4, 4.5), 1.5 * damp(tt, 1.8, 4.0), 0)
stack_in(f0); stack_still(f0, F(28.09) - 1, MS_, MYAW, sneeze)
yaw_d = facing(DDIR.xy)
def dog_at(fr):
    u = ease((fr - f0 - 2) / 34); p = D0.lerp(D1, u)
    if fr >= fA: p = p - DDIR * 1.6 * ease((fr - fA) / 6)            # jumps back on the sneeze
    return p
track(DOG["root"], f0, F(28.09) - 1, lambda fr: (dog_at(fr), (0, 0, yaw_d)))
for k, hp in DOG["legs"].items():                                   # trot: diagonal pairs, fades in and out
    for fr in range(f0, f0 + 41):
        w = min(1.0, (fr - f0) / 5, max(0.0, (f0 + 38 - fr) / 6)); ph = (fr - f0) / 7 * math.pi * 2 + (0 if k in (0, 3) else math.pi)
        kf(hp, "rotation_euler", fr, (math.radians(22 * math.sin(ph) * w), 0, 0))
for fr in range(f0, F(28.09)):                                      # sniffing bobs, tail wag
    sn = min(1.0, max(0.0, (fr - f0 - 34) / 6)) * (1.0 if fr < fA else max(0.0, 1 - (fr - fA) / 6))
    kf(DOG["head"], "rotation_euler", fr, (math.radians(-14 - 9 * sn * (0.5 + 0.5 * math.sin(fr * 1.1))), 0, math.radians(5 * math.sin(fr * 0.19))))
    kf(DOG["tail"], "rotation_euler", fr, (math.radians(-30), 0, math.radians(20 * math.sin(fr * 0.55))))
kf(DOG["root"], "location", F(28.09), V((0, 0, -60)), interp="CONSTANT")
expr(RG["top"], f0, "smug", ramp=0); snap_rot(top, "neck", f0)
eyes((RG["top"], t0, 28.0))
cine("10 dog sniff", t0, t1, NOSE + V((0, 0, 1.6)), u=(FW - SIDE * 0.9).normalized(), size=0.42, span=4.6, lens=30, tilt=7, sy=0.02,
     move="push", amt=1.15, extra=[D1 + DDIR * 2.0 + V((0, 0, 2.0)), MS_ + FW * 1.1 + V((0, 0, 0.3))])
t0, t1 = win("dog_sniff", a=25.6)
expr(RG["top"], F(27.0), "deadpan"); look(top, fA + 6, z=0, x=2, dur=6)
cine("10b achoo", t0, t1, MS_ + V((0, 0, 4.8)), u=(FW + SIDE * 0.35).normalized(), size=0.6, span=10.5, lens=32, tilt=3, sy=0.04,
     move="static", extra=[MS_ + V((0, 0, TOP_HZ)), D1 + V((0, 0, 1.5))])

# ================================================================== 11 six shoes (FIX: camera low at the hem, all six in frame)
t0, t1 = win("six_shoes"); f0, f1 = F(t0), F(t1) - 1
stack_still(F(28.09), f1, MS_, MYAW)
for k, r in enumerate(ST["shoes"]):                    # shuffle: each extra shoe lifts + twists once, staggered
    base = r.location.copy(); yr = r.rotation_euler.z
    fa = f0 + 8 + k * 7
    kf(r, "location", fa, base); kf(r, "location", fa + 3, base + V((0, 0.12, 0.22))); kf(r, "location", fa + 7, base)
    kf(r, "rotation_euler", fa, (0, 0, yr)); kf(r, "rotation_euler", fa + 4, (0, 0, yr + math.radians(10 if k % 2 else -10)))
    kf(r, "rotation_euler", fa + 8, (0, 0, yr))
for k, hh in enumerate(("hipL", "hipR")):
    fa = f0 + 12 + k * 14
    kf(bot[hh], "rotation_euler", fa, (0, 0, 0)); kf(bot[hh], "rotation_euler", fa + 4, (math.radians(-12), 0, 0))
    kf(bot[hh], "rotation_euler", fa + 9, (0, 0, 0))
HEM = MS_ + FW * 0.6 + V((0, 0, 0.55))                  # FIX (j): camera down at the hem, all six shoes across the frame
insert("11 six shoes", t0, t1, HEM + V((0, 0, 0.35)), HEM + V((0, 0, 0.15)), FW, 6.4, 5.7, lens=30, land=0.75, fstop=6.0)
FRAMING["11 six shoes"] = [HEM - SIDE * 1.95 - V((0, 0, 0.3)), HEM + SIDE * 1.95 - V((0, 0, 0.3))]

# ================================================================== 12 backstage: Kai peeks; the coat stands alone in the dark wing
t0, t1 = win("backstage", b=32.6); f0, f1 = F(t0), F(t1) - 1
fB1 = F(37.36) - 1
kf(WING.data, "energy", 1, 0, interp="CONSTANT"); kf(WING.data, "energy", f0, 1400, interp="CONSTANT"); kf(WING.data, "energy", fB1 + 1, 0, interp="CONSTANT")
KP0 = V((C.x - 1.1, C.y - 1.7, WZ)); KP1 = V((C.x - 1.1, C.y - 3.0, WZ))      # hidden -> head past the curtain edge
WS_ = V((C.x + 6, C.y - 2.8, WZ))
stack_in(f0)
def jostle(fr):
    tt = fr / FPS
    a = 0.6 * math.sin(tt * 2.1) + (1.4 * math.sin(tt * 7.0) if F(32.64) < fr < F(34.18) else 0)
    return (0, 0, 0), (0.0, a, 0)
stack_still(f0, fB1, WS_, facing((-1, -0.45)), jostle)
stage_cast(f0, (kai, KP0, -90))
kf(kai["root"], "location", f0 + 6, KP0); kf(kai["root"], "location", f0 + 18, KP1)
lean(kai, f0 + 6, y=-8, dur=12); expr(RG["kai"], f0, "curious", ramp=0); expr(RG["kai"], f0 + 18, "shocked")
mouth(RG["kai"], f0, "rest_flat")
live(kai, t0, 37.36, "tense"); eyes((RG["kai"], t0, 37.3), (RG["top"], t0, 37.3))
cine("12 backstage peek", t0, t1, head(kai, KP1), u=V((-0.55, -0.83, 0)), size=0.13, span=1.1, lens=30, tilt=4, sx=-0.18, sy=0.06,
     move="hold")
target("12 backstage peek", kai)
t0, t1 = win("backstage", a=32.6, b=34.25)
say(line(32.64), RG["top"], "rest_flat", style="calm", nod=3.0, P=top); expr(RG["top"], F(32.6), "annoyed", ramp=0)
cine("12b stop moving", t0, t1, WS_ + V((0, 0, TOP_HZ)), u=V((-1, -0.75, 0)), size="MCU", lens=40, tilt=-4, sy=0.1,
     move="push", amt=1.12)
target("12b stop moving", top)
t0, t1 = win("backstage", a=34.25); f0, f1 = F(t0), F(t1) - 1
bb = ST["coat"]["buttons"][4]; bb0 = bb.location.copy()
for k, w in enumerate(([0.40, 0.95], [1.25, 1.75])):           # the middle buttons bulge on "knee" and "ear"
    fa = F(34.28 + w[0]); fb = F(34.28 + w[1])
    kf(bb, "location", fa - 2, bb0); kf(bb, "location", fa + 2, bb0 + V((0, 0.3, 0.05))); kf(bb, "location", fb, bb0 + V((0, 0.22, 0)))
    kf(bb, "location", fb + 4, bb0)
for k, r in enumerate(ST["shoes"]):                           # "I'm hungry": the hem shuffles
    base = r.location.copy(); fa = F(36.4) + k * 2
    kf(r, "location", fa, base); kf(r, "location", fa + 3, base + V((0.1, 0, 0.18))); kf(r, "location", fa + 7, base)
cine("12c knee in my ear", t0, t1, WS_ + V((0, 0, 3.4)), u=V((-1, -0.5, 0)), size=0.45, span=6.5, lens=30, tilt=2, sy=0.0,
     move="drift", amt=6)

# ================================================================== 13 the big speech: Kai crawls through the crowd
t0, t1 = win("speech_crawl"); f0, f1 = F(t0), F(t1) - 1
crowd_spots = [(CROWD[0], (196.5, 1.5)), (CROWD[1], (193.5, -0.6)), (CROWD[2], (198.5, -3.2)), (CROWD[3], (193.0, -2.0)),
               (CROWD[4], (200.5, 0.6)), (tall, (196.0, -11.0)), (avg, (194.5, 3.0))]
stage_cast(f0, *[(P, V((x, y, Z0)), -90) for P, (x, y) in crowd_spots], (kai, V((186.5, -4.6, Z0)), -90))
stack_in(f0); stack_still(f0, F(44.9) - 1, MAYOR_STAGE, 90)
crawl(kai, f0, f0 + 14, f1 + 4, f1 + 20, (186.5, -4.6), (196.0, -4.6), z=Z0, cycle=14)
for P, _ in crowd_spots: live(P, t0, 44.9, "calm")
expr(RG["kai"], f0, "lean_in", ramp=0)
def kai_head_at(fr):
    s.frame_set(fr); return kai["head"].matrix_world.translation.copy()
follow("13 crawl", t0, t1, kai, kai_head_at, V((-3.5, -5.0, 0.4)), 24, look_dz=0.6)

# ================================================================== 14 "Citizens! ...short people are banned from the-"
t0, t1 = win("podium"); f0, f1 = F(t0), F(t1) - 1
say(line(40.43), RG["top"], "rest_flat", style="excited", nod=5.0, P=top)
expr(RG["top"], f0, "smug", ramp=0); gesture(top, "Right", F(40.4), euler=(150, -40), dur=12)
gesture(top, "Right", F(42.9), euler=(115, -55), dur=9); gesture(top, "Left", F(43.6), euler=(75, 35), dur=8)
expr(RG["top"], F(43.0), "ominous")
eyes((RG["top"], t0, t1))
cine("14 podium", t0, t1, MAYOR_STAGE + V((0, 0, TOP_HZ - 0.6)), u=V((-1, -0.3, 0)), size="MS", lens=40, tilt=-14, sx=0.06, sy=0.1,
     move="push", amt=1.25)
target("14 podium", top)

# ================================================================== 15 one tickle: Kai's hand slides under the hem
t0, t1 = win("tickle"); f0, f1 = F(t0), F(t1) - 1
KT = V((MAYOR_STAGE.x - 0.3, MAYOR_STAGE.y - 3.75, DECK))
stack_still(F(44.9), F(48.9) - 1, MAYOR_STAGE, 90, lambda fr: ((0, 0, 0), (0, 0, 0)) if fr < F(46.07) else
            ((0, 0, 0.12 * abs(math.sin((fr - F(46.07)) * 0.9)) * (1 if (fr // 5) % 3 else 0.3)),
             (0, 2.2 * math.sin((fr - F(46.07)) * 0.55) * min(1, (fr - F(46.07)) / 6), 0)))
stage_cast(f0, (kai, KT, 0))
snap_rot(kai, "chest", f0, x=-30); pose_arm(kai, "Left", f0, euler=(40, 10))
gesture(kai, "Left", f0 + 2, euler=(78, 18), dur=9); look(kai, f0, x=-10, dur=6)
expr(RG["kai"], f0, "sly", ramp=0); mouth(RG["kai"], f0, "rest_smirk")
live(kai, t0, t1, "calm")
HEM_T = MAYOR_STAGE + V((0, -2.2, 0.7))
cine("15 tickle", t0, t1, HEM_T, u=V((-1, 0.2, 0)), size=0.35, span=2.6, lens=40, tilt=10, sy=0.0, move="push", amt=1.12)

# ================================================================== 16 the giggle, the sway, the topple (music cuts on the thud)
t0, t1 = win("sway", b=48.9); f0, f1 = F(t0), F(t1) - 1
stage_cast(f0, (kai, V((KT.x - 1.2, KT.y - 1.0, DECK)), 20), *[(P, V((x, y, Z0)), -90) for P, (x, y) in crowd_spots[:5]])
expr(RG["top"], f0, "effort", ramp=0); mouth(RG["top"], f0, "rest_flat"); mouth(RG["top"], f0 + 1, "grin_open")
mouth(RG["top"], F(48.6), "rest_flat")
expr(RG["kai"], f0, "excited", ramp=0); look(kai, f0, x=24, dur=8)
for P, _ in crowd_spots[:5]: live(P, t0, 51.15, "tense")
eyes((RG["top"], t0, 51.1), (RG["kai"], t0, 51.1))
cine("16 giggle", t0, t1, MAYOR_STAGE + V((0, 0, 4.8)), u=V((-0.5, -1, 0)), size=0.6, span=10.5, lens=24, tilt=-6, sy=0.05,
     move="static", extra=[MAYOR_STAGE + V((0, 0, TOP_HZ))])
t0, t1 = win("sway", a=48.9); f0, f1 = F(t0), F(t1) - 1
fT, fH = F(49.7), F(50.3)
LAND = V((MAYOR_STAGE.x - 3.5, MAYOR_STAGE.y, Z0 + 0.8))
def topple(fr):
    if fr < fT:                                     # sway: back (anticipation), forward, back... then over
        u = (fr - f0) / max(1, fT - f0)
        return MAYOR_STAGE, (0, -7 * math.sin(u * math.pi * 2.0) * (0.4 + 0.6 * u), 90)
    if fr <= fH:
        u = (fr - fT) / (fH - fT); a = 90 * u ** 2.0
        return MAYOR_STAGE.lerp(LAND, u ** 2.2), (-a, 0, 90)
    tt = (fr - fH) / FPS
    return LAND + V((0, 0, 0.25 * abs(damp(tt, 2.5, 7.0)))), (-90 + 3 * damp(tt, 2.5, 6.0), 0, 90)
track(ST["root"], f0, f1, topple)
expr(RG["top"], fT - 4, "shocked"); expr(RG["kai"], fT, "shocked")
for P, _ in crowd_spots[:5]: lean(P, fH + 2, x=12, dur=8)
cine("16b topple", t0, t1, V((204.5, -3.6, 3.8)), u=V((-0.2, -1, 0)), size=0.4, span=12, lens=26, tilt=4, sy=0.02,
     move="hold", extra=[LAND + V((-6, 0, 0))])

# ================================================================== 17 reveal: three short guys in a heap. "...Please don't tell."
t0, t1 = win("reveal"); f0, f1 = F(t0), F(t1) - 1
HEAP = V((198.5, -3.6, Z0))
coat_vis(f0, False); vis_obj(FLAT, f0, True)
for o in FLAT.children: vis_obj(o, f0, True)
kf(FLAT, "location", f0, HEAP + V((0, 0, 0.0)), interp="CONSTANT"); kf(FLAT, "rotation_euler", f0, (0, 0, math.radians(90)), interp="CONSTANT")
track(ST["root"], f0, F(55.97) - 1, lambda fr: (HEAP, (0, 0, 0)))
SIT_Z = 0.55 - SIT_DROP
heap = [(top, (-2.4, 0.4, SIT_Z + 0.25), 200, 15), (mid, (0.3, -1.2, SIT_Z + 0.25), 175, 8), (bot, (2.6, 0.6, SIT_Z + 0.25), 150, -10)]
for P, (x, y, z), yw, tilt in heap:
    kf(P["root"], "location", f0, V((x, y, z)), interp="CONSTANT"); kf(P["root"], "rotation_euler", f0, (0, math.radians(tilt * 0.3), math.radians(yw)), interp="CONSTANT")
    for hh in ("hipL", "hipR"): kf(P[hh], "rotation_euler", f0, (math.radians(80), 0, math.radians(8 if hh == "hipL" else -8)), interp="CONSTANT")
    pose_arm(P, "Left", f0, euler=(25, -25)); pose_arm(P, "Right", f0, euler=(25, 25))
    snap_rot(P, "neck", f0, x=8); look(P, f0 + 6, x=30, dur=10)
    live(P, t0, t1, "scared")
ring = [(CROWD[0], (193.0, 4.0)), (CROWD[1], (195.0, -12.0)), (CROWD[2], (189.5, 3.0)), (CROWD[3], (196.0, 5.5)), (CROWD[4], (199.0, -12.5))]
stage_cast(f0, *[(P, V((x, y, Z0)), facing((HEAP.x - x, HEAP.y - y))) for P, (x, y) in ring])
for P, _ in ring: live(P, t0, 55.97, "tense"); lean(P, f0 + 2, x=-10, dur=10)
mouth(RG["top"], f0, "rest_frown")
say(line(51.5), RG["top"], "rest_frown", style="calm", nod=2.0, P=top)
for rig in ("top", "mid", "bot"): expr(RG[rig], f0, "nervous", ramp=0)
mouth(RG["mid"], f0, "small_o"); mouth(RG["bot"], f0, "rest_frown")
eyes((RG["top"], t0, t1), (RG["mid"], t0, t1), (RG["bot"], t0, t1))
cine("17 reveal", t0, t1, HEAP + V((0, -0.3, 1.6)), u=V((-1, -0.1, 0)), size=0.36, span=4.5, lens=32, tilt=38, sy=0.06,
     move="pull", amt=1.2)

# ================================================================== 18 two-shot: Kai is the tallest for once. "I could've exposed them..."
t0, t1 = win("two_shot"); f0, f1 = F(t0), F(t1) - 1
KTS = HEAP + V((-1.2, 2.6, 0))
for P, y, rn in zip((top, mid, bot), (-0.6, -2.5, -4.4), ("top", "mid", "bot")):
    kf(P["root"], "location", f0, V((-0.6 + 0.3 * y, y, 0)), interp="CONSTANT"); kf(P["root"], "rotation_euler", f0, (0, 0, math.radians(facing((-0.6 - (-0.6 + 0.3 * y) - 0.8, 2.6 - y)))), interp="CONSTANT")
    standing(P, f0); pose_arm(P, "Left", f0, euler=(6, -8)); pose_arm(P, "Right", f0, euler=(6, 8))
    snap_rot(P, "neck", f0, x=16, z=-12); live(P, t0, t1, "scared"); expr(RG[rn], f0, "nervous", ramp=0)
stage_cast(f0, (kai, KTS, facing((0.3, -1))), *[(P, V((x, y, Z0)), facing((HEAP.x - x, HEAP.y - y))) for P, (x, y) in ring[:4]])
for o in TOP_HAT: vis_obj(o, f0, False); vis_obj(o, F(55.97), True)     # his hat came off in the fall
expr(RG["kai"], f0, "content", ramp=0); mouth(RG["kai"], f0, "rest_smirk")
look(kai, F(54.7), z=50, x=4, dur=12); look(kai, F(55.4), z=-25, x=-14, dur=10)          # the crowd ... then the empty coat
expr(RG["kai"], F(54.7), "curious")
live(kai, t0, t1, "calm"); None
eyes((RG["kai"], t0, t1), (RG["top"], t0, t1), (RG["mid"], t0, t1), (RG["bot"], t0, t1))
cine("18 two shot", t0, t1, HEAP + V((-0.6, -0.8, 2.0)), u=V((-1, 0.15, 0)), size=0.38, span=6.0, lens=30, tilt=2, sy=0.0,
     move="arc", amt=20, extra=[head(kai, KTS)])

# ================================================================== the ending: Kai on top of the coat (ten feet, eight shoes)
fE = F(55.97)
track(ST["root"], fE, F(68.28) - 1, lambda fr: (V((2200, 2200, -500)), (0, 0, 0)))          # stack 1 parked (it's inside coat 2 now)
stack_in(fE, coat=False)
coat2_vis(fE, True); vis_obj(FLAT, fE, False)
for o in FLAT.children: vis_obj(o, fE, False)
gesture(kai, "Left", fE, euler=(6, -6), dur=4); snap_rot(kai, "chest", fE); snap_rot(kai, "neck", fE)
C2 = V((198.0, -3.6, Z0))

# 19 "Taxes... cancelled." (music back, crowd cheers)
t0, t1 = win("coat_ten_feet"); f0, f1 = F(t0), F(t1) - 1
stack2(f0, f1, lambda fr: (C2, (0, 0, 90)))
kai_top(f0, F(68.28) - 1)
stage_cast(f0, *[(P, V((x - 8.5, y, Z0)), -90) for P, (x, y) in crowd_spots[:5]], keep=(kai,))
say(line(56.27), RG["kai"], "rest_smirk", style="calm", nod=4.0, P=kai)
expr(RG["kai"], f0, "smug", ramp=0); gesture(kai, "Right", f0 + 4, euler=(105, -75), dur=12)
for k, (P, _) in enumerate(crowd_spots[:5]):
    mo_clip(P, "wave" if k % 2 else "wave_hello", F(57.0) + k * 2, speed=1.2, t1=1.5)
    expr(RG["c%d" % k], F(57.0), "excited")
eyes((RG["kai"], t0, t1))
cine("19 taxes cancelled", t0, t1, C2 + V((0, 0, KAI_TOP_Z + HDZ[id(kai)])), u=V((-1, 0.2, 0)), size="MCU", lens=45, tilt=-18,
     sy=0.12, move="rise", amt=8)
target("19 taxes cancelled", kai)

# 20 the coat struts through the square
t0, t1 = win("strut"); f0, f1 = F(t0), F(t1) - 1
SA, SB = V((188.0, -6.5, Z0)), V((176.0, -6.5, Z0))
def strut(fr):
    u = (fr - f0) / (f1 - f0); u = 0.15 * u + 0.85 * ease(u)
    return SA.lerp(SB, u), (0, 2.0 * math.sin(u * math.pi * 3), 90)
stack2(f0, f1, strut)
gesture(kai, "Right", f0, euler=(10, -8), dur=12); look(kai, f0 + 6, z=-30, dur=10)
expr(RG["kai"], f0, "content", ramp=0); mouth(RG["kai"], f0, "rest_smile")
stage_cast(f0, (CROWD[1], (180, 2.5, Z0), 180), (CROWD[3], (174, 3.0, Z0), 200), (avg, (186, 3.5, Z0), 160), keep=(kai,))
for P in (CROWD[1], CROWD[3], avg): live(P, t0, t1, "calm"); lean(P, f0 + 10, x=-18, dur=10)
eyes((RG["kai"], t0, t1))
follow("20 strut", t0, t1, kai, lambda fr: strut(fr)[0] + V((0, 0, 5.5)), V((-15.0, -12.0, -1.5)), 30, look_dz=0.5)

# 21 calendar: TUESDAY circled ... the coat stomps past ("It's not Tuesday.")
t0, t1 = win("calendar", b=61.9); f0, f1 = F(t0), F(t1) - 1
stack2(f0, f1, lambda fr: (V((2300, 2300, -500)), (0, 0, 0)))
insert("21 calendar", t0, t1, BOARD_PT, TUE_PT, V((-1, 0, 0)), 4.4, 3.0, lens=45, land=0.7)
t0, t1 = win("calendar", a=61.9); f0, f1 = F(t0), F(t1) - 1
CA, CB = V((191.0, 21.0, Z0)), V((189.0, 9.0, Z0))
def stomp(fr):
    u = (fr - f0) / (f1 - f0); p = CA.lerp(CB, 0.1 * u + 0.9 * ease(u))
    st_ = abs(math.sin((fr - f0) / 9 * math.pi))                 # heavy grumpy steps
    return p + V((0, 0, -0.22 * (1 - st_) + 0.12)), (0, 2.5 * math.sin((fr - f0) / 9 * math.pi), 180)
stack2(f0, f1, stomp)
expr(RG["kai"], f0, "annoyed", ramp=0); mouth(RG["kai"], f0, "rest_flat"); look(kai, f0 + 8, z=-35, dur=10)
eyes((RG["kai"], t0, t1))
cine("21b stomp", t0, t1, V((191.5, 14.0, 6.0)), u=V((-0.7, -1, 0)), size=0.6, span=14, lens=28, tilt=4, sy=0.04,
     move="static", extra=[BOARD_PT])
target("21b stomp", kai)

# 22 eight shoes now ("Your knee is in my ear!")
t0, t1 = win("eight_shoes"); f0, f1 = F(t0), F(t1) - 1
C3 = V((186.0, 10.0, Z0))
stack2(f0, F(69.92) - 1, lambda fr: (C3, (0, 0, -90 if fr < F(65.89) else -90)))
for k, r in enumerate(SHOES2):
    base = r.location.copy(); yr = r.rotation_euler.z; fa = f0 + 6 + (k * 5) % 30
    kf(r, "location", fa, base); kf(r, "location", fa + 3, base + V((0, 0.1, 0.2))); kf(r, "location", fa + 7, base)
    kf(r, "rotation_euler", fa, (0, 0, yr)); kf(r, "rotation_euler", fa + 4, (0, 0, yr + math.radians(-9 if k % 2 else 9)))
    kf(r, "rotation_euler", fa + 8, (0, 0, yr))
HEM2 = C3 + V((0, 0, 0.6))
insert("22 eight shoes", t0, t1, HEM2 + V((0.9, 0, 0.6)), HEM2 + V((0.9, 0, 0.45)), V((1, 0.12, 0)), 8.0, 7.2, lens=28, land=0.7, fstop=6.0)
FRAMING["22 eight shoes"] = [HEM2 + V((0.9, -2.7, -0.3)), HEM2 + V((0.9, 2.7, -0.3))]

# 23 the coat tips its hat to camera. "Would you expose them... or join them?"
t0, t1 = win("hat_tip"); f0, f1 = F(t0), F(t1) - 1
expr(RG["kai"], f0, "sly", ramp=0); mouth(RG["kai"], f0, "rest_smirk"); snap_rot(kai, "neck", f0)
gesture(kai, "Right", f0, euler=(165, 30), dur=14)
kf(HATP, "location", 1, V((0, 0, 0.3))); kf(HATP, "rotation_euler", 1, (0, 0, 0))
for fr, dz, rx in ((f0 + 19, 0.0, 0), (f0 + 25, 0.55, -18), (f0 + 34, 0.55, -18), (f0 + 40, 0.0, 0)):
    kf(HATP, "location", fr, V((0, 0, 0.3 + dz))); kf(HATP, "rotation_euler", fr, (math.radians(rx), 0, 0))
gesture(kai, "Right", f0 + 38, euler=(8, -8), dur=12)
expr(RG["kai"], f0 + 26, "grin"); mouth(RG["kai"], f0 + 26, "rest_smile")
live(kai, t0, t1, "calm"); eyes((RG["kai"], t0, t1))
cine("23 hat tip", t0, t1, C3 + V((0, 0, KAI_TOP_Z + HDZ[id(kai)])), u=V((1, 0, 0)), size="MCU", lens=50, tilt=0, sy=0.08,
     move="hold")
target("23 hat tip", kai)

# 24 loop: cut back to the opening framing (loops into line 1)
t0, t1 = win("loop_opening"); f0, f1 = F(t0), F(t1) - 1
coat2_vis(f0, False); kf(ROOT2, "location", f0, V((0, 0, 0)), interp="CONSTANT"); kf(ROOT2, "rotation_euler", f0, (0, 0, 0), interp="CONSTANT")
for fr in range(f0 + 1, F(69.92) + 1):
    kf(ROOT2, "location", fr, V((0, 0, 0))); kf(ROOT2, "rotation_euler", fr, (0, 0, 0))
hook_staging(f0, F(69.92))
cine("24 loop", t0, t1, HOOK_SUBJ, u=V((-1, -0.18, 0)), size=0.42, span=10.5, lens=26, tilt=-8 + 2.5, sy=0.12, sx=0.04,
     move="hold", extra=[head(kai, KAI_HOOK), MAYOR_STAGE + V((0, 0, 0.3))])
eyes((RG["kai"], t0, t1), (RG["top"], t0, t1))

# ================================================================== finish
def tidy_lips(rig):
    """Drop 1-frame non-M shapes from the speech mouths (the previous shape holds a frame longer): no flicker, no chatter."""
    log = sorted(set(rig.get("lip_log", [])))
    drop = {(fa, ma) for (fa, ma), (fb, mb) in zip(log, log[1:]) if fb - fa == 1 and ma != "M"}
    rig["lip_log"] = [e for e in log if e not in drop]
    ev = _MEV[id(rig)][1]; ev[:] = [e for e in ev if (e[0], e[1]) not in drop]


tidy_lips(RG["top"]); tidy_lips(RG["kai"])
QUIET = (F(27.36), F(50.3), F(49.7), F(37.36) + 19)          # sneeze jolt, topple + thud, crawl arms start
finish_part(life=True, allow=("03 bus", "09 pen", "21b stomp"), motion_chars={"kai": kai, "top": top, "avg": avg, "aide": aide, "tall": tall}, quiet=QUIET)
if os.environ.get("DBG"):
    for fr in (85, 107, 760, 1344, 1368):
        s.frame_set(fr)
        print("DBGP", fr, s.render.resolution_x, s.render.resolution_y, cam.data.lens, cam.data.sensor_fit, tuple(round(v,2) for v in cam.matrix_world.translation), _proj(s, cam, tall["head"].matrix_world.translation), _proj(s, cam, kai["head"].matrix_world.translation), [_proj(s, cam, t[0].matrix_world.translation + t[1]) if isinstance(t, tuple) else _proj(s, cam, V(t)) for t in FRAMING[[n for n, a_, b_ in SHOTS if a_ <= fr <= b_][0]]])
        for P in (kai, tall): print("DBG", fr, P["head"].name, tuple(round(v, 2) for v in P["head"].matrix_world.translation), tuple(round(v, 2) for v in P["root"].matrix_world.translation))
