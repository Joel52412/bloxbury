# hm1_assets.py - HEIGHT MOG "The Trenchcoat Mayor": FULL ASSET SHEET (stills for Joel before anything is saved).
# New: KAI, the three short guys + the mayor's trenchcoat stack (mustache, top hat, gloves, six shoes), town plaza + stage
# (podium + seal, gooseneck mic, flags, banner, bunting), backstage curtain, town bus, dog, banquet table, pen.
# Library reused: Bloxbury town (daytime), shiny car (props.car), extras (studio.random_extra).
# Run (from /home/claude/bloxbury-blender): SHOTS=all RX=270 RY=480 SAMPLES=8 python3 hm1_assets.py -> /home/claude/talk/hm1_assets
import os, math, random
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
os.environ.setdefault("OUT", "/home/claude/talk/hm1_assets")
boot("hm1", world="bloxbury", after_rig=(), lead="kai")
load("props4", "studio", "lookdev", "props7")
exec(open(SCR + "hm1_cast.py").read())


def shades(P):
    """Flat black sunglasses (two lenses + bridge) on the head layer."""
    h = P.get("head") or P["neck"]; fy = surf_y(0) + 0.02; m = P["M"]("Shades", (15, 15, 18), rough=0.15)
    for s in (-1, 1): rb("ShadeLens", (0.36, 0.06, 0.22), V((s * 0.24, fy, 0.72)), m, h, r=0.06)
    rb("ShadeBridge", (0.2, 0.05, 0.05), V((0, fy + 0.01, 0.77)), m, h, r=0.02)


kai, top, mid, bot, tall, avg, aide = cast(
    kai=(make_kai, "rest_smile"), top=(make_guy_top, "rest_flat"), mid=(make_guy_mid, "rest_flat"),
    bot=(make_guy_bot, "rest_flat"), tall=(lambda: random_extra("Tall", 61, role="office"), "rest_smirk"),
    avg=(lambda: random_extra("Avg", 77, role="casual"), "rest_flat"), aide=(lambda: random_extra("Aide", 33, role="office"), "rest_flat"))
size_rig(tall, 1.12); size_rig(avg, 0.93); size_rig(aide, 0.95)
shades(tall); hm_mustache(top)
ST = build_stack(bot, mid, top)
GUYS = (top, mid, bot)
FKAI, FTOP, FMID, FBOT, FTALL, FAVG, FAIDE = (RIGS[k] for k in ("kai", "top", "mid", "bot", "tall", "avg", "aide"))
COAT_OBJS = [ST["coat"]["root"]] + list(ST["coat"]["root"].children_recursive) + \
    [o for o in top["root"].children_recursive if o.name.split(".")[0] in ("SleeveLeft", "SleeveRight", "CuffLeft", "CuffRight",
                                                                            "GloveLeft", "GloveRight", "GloveSeam")]
SHOE_OBJS = [o for r in ST["shoes"] for o in [r] + list(r.children_recursive)]

# ---------------------------------------------------------------- sets
for head_, m_, ld_ in LAMPS:                     # daytime: street lamps off
    ld_.energy = 0
for o in [o for o in bpy.data.objects if o.name.split(".")[0] in ("LampPole", "LampArm", "StreetLamp") and o.location.x > 160]:
    o.hide_render = True                         # clear the plaza
PLAZA = hm_plaza((190, 0))
STAGE = hm_stage((210, 0))
CURT = hm_curtain((700, 0, 400.0))                                                 # backstage wing (stand-alone set)
BUS = hm_bus("Bus", (-60, -6, 0.2)); BUS["root"].rotation_euler = (0, 0, math.radians(-90))     # drives along +X
CAR = car("ShinyCar", body=(200, 28, 40), loc=V((-20, -17.5, 0.4))); CAR.rotation_euler = (0, 0, math.radians(-90))
DOG = hm_dog("Dog", (0, 0, 0))
TABLE = hm_banquet("Banquet", (120, 30, 0.4))
PEN = hm_pen("Pen", (0, 0, 0))

# studio cyc for character cards
SO = V((600, 0, 400))
rb("CycFloor", (70, 40, 0.3), SO + V((0, 6, -0.15)), pmat("CycGrey", (168, 170, 176), rough=0.8), None, r=0.02)
rb("CycBack", (70, 0.3, 30), SO + V((0, 14, 15)), pmat("CycGrey2", (150, 152, 160), rough=0.85), None, r=0.02)


def area(name, loc, tgt, energy, size, col):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = col
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = V(loc); o.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler(); return o


area("SKey", SO + V((-10, -14, 14)), SO + V((0, 0, 3.5)), 5200, 10, (1.0, 0.96, 0.9))
area("SFill", SO + V((12, -10, 6)), SO + V((0, 0, 3.5)), 1800, 12, (0.85, 0.9, 1.0))
area("SRim", SO + V((0, 12, 12)), SO + V((0, 0, 4)), 2600, 8, (1, 1, 1))
WING = area("WingKey", (213, 13, 9.5), (218, 16, 5), 0, 3, (1.0, 0.85, 0.65))      # backstage: one warm work light

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
cam.data.sensor_width = 36; cam.data.clip_end = 3000


def look(pos, tgt, lens=35, fstop=None):
    cam.location = V(pos); cam.rotation_euler = (V(tgt) - V(pos)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    cam.data.dof.use_dof = fstop is not None
    if fstop: cam.data.dof.aperture_fstop = fstop; cam.data.dof.focus_distance = (V(tgt) - V(pos)).length


ALL = (kai, tall, avg, aide)
PARK = {}


def only(*Ps, stack=None, coat=True):
    """Pose the visible characters (P, loc, yaw) and park the rest; stack=(loc, yaw) shows the coat stack."""
    vis = {id(p[0]) for p in Ps}
    for i, P in enumerate(ALL):
        if id(P) not in vis: pose(P, (2000 + 12 * i, 2000, -500), 0)
    for P, loc, yaw in Ps: pose(P, loc, yaw + 180)          # yaw 0 = facing the -Y camera
    r = ST["root"]
    if stack is None: r.location = V((2100, 2100, -500)); return
    r.location = V(stack[0]); r.rotation_euler = (0, 0, math.radians(stack[1] + 180))
    for o in COAT_OBJS + SHOE_OBJS: o.hide_render = not coat
    if coat:
        for P, z in zip((bot, mid, top), STACK_Z): P["root"].location = V((0, 0, z))
        for P in (bot, mid):
            for sd in ("Left", "Right"): arm(P, sd, 1, euler=(165, 0))       # hands up, holding the guy above
    else:                                                                    # coat off: the three side by side
        for P, x in zip((bot, mid, top), (-2.6, 0, 2.6)): P["root"].location = V((x, 0, 0))


def face(rig, ex, mo): expr(rig, 1, ex); mouth(rig, 1, mo)


SHOTS = []


def add(name, fn, wide=False): SHOTS.append((name, fn, wide))


# ---------------------------------------------------------------- shots
def sh_lineup():      # heights: tall, avg, Kai, and the three short guys (coat off)
    only((tall, SO + V((-7.5, 0, 0)), 10), (avg, SO + V((-4.2, 0, 0)), 5), (kai, SO + V((-1.2, 0, 0)), 0),
         stack=(SO + V((4.2, 0, 0)), -8), coat=False)
    face(FKAI, "friendly", "rest_smile"); face(FTOP, "nervous", "rest_flat"); face(FMID, "deadpan", "rest_flat"); face(FBOT, "sad", "rest_flat")
    look(SO + V((-1.0, -22, 3.2)), SO + V((-1.0, 0, 2.9)), 45)


def sh_stack():       # the mayor (coat on) + Kai looking up at him
    only((kai, SO + V((-2.4, -1.0, 0)), 50), stack=(SO + V((1.2, 0.5, 0)), -15))
    face(FKAI, "curious", "rest_flat"); face(FTOP, "smug", "rest_flat"); neck(kai, 1, x=24)
    look(SO + V((-0.5, -15, 2.0)), SO + V((0, 0, 4.4)), 40)


def sh_mayor_face():  # close: mustache, top hat, raised collar, gloves
    only(stack=(SO + V((0, 0, 0)), 0))
    face(FTOP, "smug", "rest_flat"); arm(top, "Right", 1, euler=(30, -10))
    look(SO + V((0.8, -6.5, 8.5)), SO + V((0, 0, 7.9)), 50)


def sh_hem():         # insert: six shoes under the hem, one pair backwards
    only(stack=(SO + V((0, 0, 0)), -20))
    look(SO + V((1.0, -6.5, 0.9)), SO + V((0, 0, 0.6)), 32)


def sh_plaza():       # the hook framing: low angle, mayor at the podium, Kai small in front
    p = STAGE["podium"].matrix_world.translation
    only((kai, (202.0, -3.2, 0.4), 80), (avg, (193, 6, 0.4), 80), (aide, (194, -8, 0.4), 100),
         stack=((p.x + 2.2, 0, STAGE["deck_z"]), -90))
    face(FKAI, "curious", "rest_flat"); face(FTOP, "smug", "rest_flat"); neck(kai, 1, x=22)
    arm(top, "Right", 1, euler=(150, 20))
    look((189, -0.6, 1.2), (206, -0.4, 7.4), 26)


def sh_bus():         # bus at the kerb, average guy stepping on, Kai behind it
    b = BUS["root"].location
    only((avg, (b.x + 11.8, b.y - 5.8, 0.4), 180), (kai, (b.x - 18, b.y - 3, 0.4), 90))
    face(FAVG, "content", "rest_smile"); face(FKAI, "sad", "rest_flat")
    look((b.x + 2, b.y - 22, 4.0), (b.x - 2, b.y, 5.0), 22)


def sh_car():         # tall guy in shades leaning on the shiny car
    c = CAR.location
    only((tall, (c.x - 1.0, c.y - 4.4, 0.4), 15))
    face(FTALL, "smug", "rest_smirk"); arm(tall, "Left", 1, euler=(20, 30)); chest(tall, 1, y=-6)
    look((c.x + 10, c.y - 11.5, 3.4), (c.x - 1.5, c.y - 1.5, 3.0), 26)


def sh_dog():         # the dog sniffs the coat hem
    only(stack=(SO + V((0, 0, 0)), -30))
    DOG["root"].location = SO + V((1.0, -3.4, 0)); DOG["root"].rotation_euler = (0, 0, math.radians(18))
    DOG["head"].rotation_euler = (math.radians(-18), 0, 0)
    DOG["tail"].rotation_euler = (math.radians(-25), 0, math.radians(15))
    look(SO + V((-6.5, -8.5, 2.4)), SO + V((0.4, -1.6, 1.6)), 36)


def sh_banquet():     # town dinner: everyone seated, the mayor standing with his plate at his chin
    t = TABLE.location
    only((kai, (t.x + 3.4, t.y - 5, t.z), -90), (avg, (t.x + 3.4, t.y + 1, t.z), -90), (aide, (t.x - 3.4, t.y - 4, t.z), 90),
         stack=((t.x - 3.3, t.y + 1, t.z), 90))
    for P in (kai, avg, aide):
        for h in ("hipL", "hipR"): P[h].rotation_euler = (math.radians(90), 0, 0)
    kai["root"].location.z = t.z + 1.9 - 1.4; avg["root"].location.z = t.z + 1.9 - 1.86; aide["root"].location.z = t.z + 1.9 - 1.9
    face(FKAI, "deadpan", "rest_flat"); face(FTOP, "smug", "rest_flat")
    look((t.x - 1, t.y - 19, 6.5), (t.x, t.y + 1, 3.6), 30)


def sh_backstage():   # Kai peeks round the curtain; the coat stands alone in the dark wing
    c = CURT.location
    WING.data.energy = 1400; WING.location = c + V((9, -4, 9)); WING.rotation_euler = (V((6, -2.8, 3)) - V((9, -4, 9))).to_track_quat("-Z", "Y").to_euler()
    only((kai, (c.x - 0.8, c.y - 1.7, c.z), 120), stack=((c.x + 6, c.y - 2.8, c.z), 100))
    face(FKAI, "shocked", "rest_flat"); face(FTOP, "nervous", "rest_flat")
    look((c.x - 9, c.y - 9, c.z + 3.6), (c.x + 4, c.y - 1.5, c.z + 3.8), 30)


def sh_props():       # the dog on the cyc (front 3/4)
    only()
    DOG["root"].location = SO + V((0, -1, 0)); DOG["root"].rotation_euler = (0, 0, math.radians(200))
    DOG["head"].rotation_euler = (0, 0, math.radians(-12)); DOG["tail"].rotation_euler = (math.radians(-35), 0, 0)
    look(SO + V((-1.5, -9, 2.6)), SO + V((0, -1, 1.5)), 40)


def sh_pen():         # insert: the mayor's pen on the stage planks
    only()
    PEN.location = STAGE["root"].location + V((-3.0, -3.0, STAGE["deck_z"] + 0.07)); PEN.rotation_euler = (0, 0, math.radians(30))
    p = PEN.location
    look(p + V((-1.4, -1.0, 1.3)), p + V((0, 0, 0)), 50)


add("01_cast_heights", sh_lineup, wide=True)
add("02_mayor_stack_kai", sh_stack)
add("03_mayor_face", sh_mayor_face)
add("04_hem_six_shoes", sh_hem)
add("05_plaza_stage_hook", sh_plaza)
add("06_bus", sh_bus)
add("07_tall_guy_car", sh_car)
add("08_dog_sniff", sh_dog)
add("09_banquet", sh_banquet)
add("10_backstage", sh_backstage)
add("11_dog", sh_props)
add("12_pen", sh_pen)

# ---------------------------------------------------------------- render
s.render.engine = "CYCLES"; s.cycles.use_denoising = True
if os.environ.get("ENGINE", "CPU") == "GPU":
    pr = bpy.context.preferences.addons["cycles"].preferences
    for be in ("OPTIX", "CUDA"):
        try:
            pr.compute_device_type = be; pr.get_devices()
            if [x for x in pr.devices if x.type == be]:
                for x in pr.devices: x.use = x.type == be
                break
        except Exception as e: print("backend fail", be, e)
    s.cycles.device = "GPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 32))
else:
    s.cycles.device = "CPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 8))
    try: s.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
s.render.use_motion_blur = False
s.render.image_settings.file_format = "PNG"
cinematic_look(s, split=0.5)
RX, RY = int(os.environ.get("RX", 540)), int(os.environ.get("RY", 960))
want = os.environ.get("SHOTS", "all").split(",")
OUTD = os.environ["OUT"]; os.makedirs(OUTD, exist_ok=True)
for name, fn, wide in SHOTS:
    if want != ["all"] and not any(name.startswith(w) for w in want): continue
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action: o.animation_data_clear()
    _MEV.clear(); _CUTS.clear(); WING.data.energy = 0
    for P in ALL + GUYS:
        arms_down(P, 1); P["hipL"].rotation_euler = (0, 0, 0); P["hipR"].rotation_euler = (0, 0, 0)
        neck(P, 1); chest(P, 1)
    set_day(0.0); house_lights(0.0, False)
    fn()
    flush_mouths(); apply_interp(); apply_interpolation()
    s.render.resolution_x, s.render.resolution_y = (RY, RY) if wide else (RX, RY)
    s.frame_set(1); s.render.filepath = f"{OUTD}/{name}.png"; bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)
print("DONE")
