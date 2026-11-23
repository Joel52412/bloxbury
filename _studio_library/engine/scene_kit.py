# scene_kit.py - the shared scene kit. A part script = settings + beats; everything else lives here, so a fix reaches
# every part. Works for any series: the base world is a plug-in (WORLDS), the rest is story-agnostic.
#
#   exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
#   boot("p4", world="bloxbury", patches=BLOX_LOW_WINDOWS + BLOX_SIDE_WINDOW)   # world, engine, rig, env, timeline, helpers
#   load("recurring", "props2", "props3")                                         # library batches (asset files)
#   milo, rae = cast(milo=(make_milo, "rest_flat"), rae=(make_rae, "rest_flat"))  # rigs, v2 faces, RIGS, park()
#   camera_rig(); load("cinema", "motion")                                        # shot()/cine()/insert(), motion.py
#   ... beats: place/at, gesture/look/lean, say(line(t), ...), cine(...), live(...) ...
#   finish_part(life=True, allow=(...), motion_chars={...})                       # blinks, mouths, interpolation, life,
#                                                                                   # every check, render settings, render
# Env: RENDER=1 OUT=dir RX RY SAMPLES FRAMES=a,b FS FE ENGINE=GPU QUALITY PLAYBLAST=1 FORCE=1 ENV_<PART>=env.json
# Paths: KIT_SCR (scene scripts), KIT_LIB (library engine), KIT_TALK (audio data + shot lists) override the defaults.
import bpy, math, random, os, json
from mathutils import Vector, Matrix

SCR = os.environ.get("KIT_SCR", "/home/claude/bloxbury-blender/")
LIB = os.environ.get("KIT_LIB", "/home/claude/studio_library/engine/")
TALK = os.environ.get("KIT_TALK", "/home/claude/talk/")
_G = globals()                                   # the part script's namespace (this file is exec'd into it)
TOOLKIT = ("cinema", "motion", "director")        # these modules REPLACE kit helpers of the same name (newer grammar)
SCRIPT_MODULES = ("rig2", "cinema", "director")   # live in SCR, the rest in LIB
ENGINE_ORDER = ("charlib", "stylelab", "hair2", "hair3", "faces2", "garments", "garments2", "hair4", "faces3", "faces4", "props")

# ================================================================== helper registry
# Kit helpers are (re)installed after every world/asset load, so they win over older same-name helpers in Part 1's
# town script, rig2 and the props files, exactly like the hand-copied helpers did in each part. cinema/motion/director
# load later and win over the kit where they define the same name (e.g. motion.smear).
_KIT = {}


def kit(fn):
    _KIT[fn.__name__] = fn; return fn


def _install():
    _G.update(_KIT)


def load(*names):
    """Exec library modules into the part's namespace, in order. Asset files (props*, recurring, lookdev, monster, rig2)
    never override kit helpers; toolkit modules (cinema, motion, director) do."""
    for n in names:
        exec(open((SCR if n in SCRIPT_MODULES else LIB) + n + ".py").read(), _G)
        if _G.get("mouth") is not _KIT["mouth"]: _G["mouth_now"] = _G["mouth"]   # rig2's immediate mouth swap
        if os.environ.get("KIT_DEBUG"):
            hit = [k for k, f in _KIT.items() if _G.get(k) is not f]
            if hit: print("KIT", n, "defines", hit, "(toolkit wins)" if n in TOOLKIT else "(kit wins)")
        if n in TOOLKIT:
            for k in [k for k, f in _KIT.items() if _G.get(k) is not f]: del _KIT[k]
        else:
            _install()


# ================================================================== worlds (base sets + primitives). Add one per series.
WORLDS = {}


def world(name):
    def reg(fn): WORLDS[name] = fn; return fn
    return reg


def patch(src, patches):
    """[(old, new)] string patches on a world's source; every old string must still be there (no silent no-ops)."""
    for old, new in patches:
        assert old in src, "world patch no longer matches: " + old[:60]
        src = src.replace(old, new)
    return src


@world("bloxbury")
def _bloxbury(patches=()):
    """Bloxbury town + Milo's house + primitives (box/plane/mat/key/R/RS...) from the Part 1 script, minus its own
    scenes and camera. 24 fps, no time warp."""
    src = open(SCR + "bloxbury_part1.py").read()
    exec(patch(src[:src.index("# Milo starts at the fence")], patches), _G)
    exec(src[src.index("# ---------------------------------------------------------------- TREES + HILLS"):
             src.index("# ---------------------------------------------------------------- CAMERA")], _G)
    _G["RB"] = _G["R"]                    # Roblox coords (x, up, z) -> Blender (rig2 rebinds R to radians)
    _G["FPS"] = 24; _G["WARP"] = []       # old helpers (key/F/set_day) run on the 24 fps timeline, no warp


# Bloxbury patches: Milo's windows lowered (sill 4, top 8) so a 5-stud character can look out (Parts 1+)
BLOX_LOW_WINDOWS = [
    ('box("WallFront", RS(4, 7, T), R(cx_, 3.5, fz), m_wall, parent=root)',
     'box("WallFront", RS(4, 4, T), R(cx_, 2.0, fz), m_wall, parent=root)'),
    ('box("WallFront", RS(4, H - 11, T), R(cx_, 11 + (H - 11) / 2, fz), m_wall, parent=root)',
     'box("WallFront", RS(4, H - 8, T), R(cx_, 8 + (H - 8) / 2, fz), m_wall, parent=root)'),
    ('WINDOW_PARTS.append(box("Window", RS(4, 4, 0.15), R(ox, 9, fz), M_WINDOW, parent=root))',
     'WINDOW_PARTS.append(box("Window", RS(4, 4, 0.15), R(ox, 6, fz), M_WINDOW, parent=root))')]
# Part 3+: sash window hole in Milo's RIGHT wall (faces Rae's): 4 wide (local z -6.5..-2.5) x 4 tall (4..8); props6 fills it
BLOX_SIDE_WINDOW = [
    ('box("WallRight", RS(T, H, D), R(W / 2 - T / 2, H / 2, 0), m_wall, parent=root)',
     'box("WallRight", RS(T, H, 3.5), R(W / 2 - T / 2, H / 2, -8.25), m_wall, parent=root); '
     'box("WallRight", RS(T, H, 12.5), R(W / 2 - T / 2, H / 2, 3.75), m_wall, parent=root); '
     'box("WallRight", RS(T, 4, 4), R(W / 2 - T / 2, 2, -4.5), m_wall, parent=root); '
     'box("WallRight", RS(T, H - 8, 4), R(W / 2 - T / 2, 8 + (H - 8) / 2, -4.5), m_wall, parent=root)')]

# extra rig v2 expressions (brow L, brow R tilt..., eye scale, mouth scale) used by every part
EXPR_EXTRA = {
    "sad":      (0.03, -0.16, 0.03, -0.16, 1.0, 0.84),
    "nervous":  (0.045, -0.15, 0.055, -0.12, 0.98, 1.02),
    "scared":   (0.075, -0.2, 0.075, -0.2, 0.92, 1.22),
    "shocked":  (0.1, -0.06, 0.1, -0.06, 1.14, 1.32),
    "deadpan":  (-0.02, 0.02, -0.02, 0.02, 1.0, 0.6),
    "laugh":    (0.05, -0.1, 0.05, -0.1, 1.0, 0.42),
    "friendly": (0.03, -0.06, 0.03, -0.06, 1.0, 1.0),
    "grin":     (0.01, 0.06, 0.01, 0.06, 1.0, 0.7),
}


# ================================================================== boot
def boot(part, world="bloxbury", patches=(), lead="milo", after_rig=("monster",), env=None, fps=24):
    """World + character engine + rig v2 + the part's audio env (prep_pN.py output) + timeline + helpers.
    part: "p1".."pN" (names env_<part>.json, frames_<part>, shots_<part>.json). lead: the voice ENV['rms'] defaults to."""
    _G["PART"] = part
    WORLDS[world](patches); _install()       # (mouth_now is set by load("rig2") below)
    load(*ENGINE_ORDER)
    _G["V"] = Vector
    path = env or os.environ.get("ENV_" + part.upper(), TALK + "env_%s.json" % part)
    ENV = json.load(open(path)); E2 = ENV
    if isinstance(ENV.get("rms"), dict):              # several voices: ENV holds the lead's, E2 keeps them all
        E2 = dict(ENV); ENV["rms"] = E2["rms"][lead]; ENV["cen"] = E2["cen"][lead]
    _G.update(ENV=ENV, E2=E2)
    load("rig2", *after_rig)                            # kf, apply_interp, upgrade_rig, arm, face v2, expr, lipsync ...
    _G["DEG"] = math.radians
    OUT = os.environ.get("OUT", TALK + "frames_" + part); os.makedirs(OUT, exist_ok=True)
    s = bpy.context.scene; NF = E2["nf"]
    s.render.fps = fps; s.frame_start, s.frame_end = 1, NF
    _G.update(OUT=OUT, s=s, NF=NF, FPS=fps, FT=lambda t: 1 + int(round(t * fps)))     # FT: video seconds -> frame
    for o in [o for o in bpy.data.objects if o.name.startswith("HazeVolume")]:
        bpy.data.objects.remove(o, do_unlink=True)    # Cycles: the haze volume costs too much render time
    _G["EX"].update(EXPR_EXTRA)
    if E2.get("scenes"): _G["SC"] = {n: (a, b) for n, a, b in E2["scenes"]}
    _G["FAR"] = Vector((3000, 3000, -800))
    LN = {}
    for L in E2.get("lines", []):
        if L.get("text"): LN.setdefault(L["text"].split()[0].lower().strip(".,!?") + "@" + str(round(L["t0"])), L)
    _G["LN"] = LN


# ================================================================== mouths (events sorted at the end: no double mouths)
_MEV = {}


@kit
def mouth(rig, frame, key):
    _MEV.setdefault(id(rig), (rig, []))[1].append((frame, key))
    rig["cur_m"] = key


@kit
def flush_mouths():
    for rig, ev in _MEV.values():
        ev.sort(key=lambda e: e[0]); rig["cur_m"] = None
        last = {}
        for fr, k in ev: last[fr] = k                  # last call for a frame wins
        for fr in sorted(last): mouth_now(rig, fr, last[fr])


# ================================================================== blocking helpers
_CUTS = []        # (obj, frame) - hold the previous pose up to the cut, then snap


@kit
def place(P, fr, loc, yaw=0.0):
    r = P["root"]
    kf(r, "location", fr, Vector(loc)); kf(r, "rotation_euler", fr, (0, 0, DEG(yaw)))
    _CUTS.append((r, fr))


@kit
def hold_cuts():
    for ob, fr in _CUTS:
        for fc in _fcurves(ob):
            if fc.data_path not in ("location", "rotation_euler"): continue
            pts = [k for k in fc.keyframe_points if k.co.x < fr - 0.5]
            if not pts: continue
            prev = max(pts, key=lambda k: k.co.x)
            prev.interpolation = "CONSTANT"          # hold the last pose of the previous shot right up to the cut


@kit
def idle(P, f0, f1, amp=0.02, base_z=0.0, speed=2.2, ph=0.0):
    for fr in range(f0, f1, 12):
        kf(P["root"], "location", fr, base_z + amp * math.sin(fr / FPS * speed + ph), index=2)


@kit
def idle_here(P, f0, f1, amp=0.015, ph=0.0):
    idle(P, f0, f1, amp=amp, base_z=P["root"].location.z, ph=ph)     # idle() keys absolute z: keep the set's floor height


@kit
def walk(P, f0, f1, p0, p1, steps=4, leg=30, yaw=None, z=0.0):
    n = f1 - f0
    for i in range(n + 1):
        fr = f0 + i; u = i / n; e = u * u * (3 - 2 * u)
        ph = steps * e
        ramp = min(1.0, u / 0.12, (1 - u) / 0.12) if 0 < u < 1 else 0.0
        ang = DEG(leg) * math.sin(math.pi * ph) * ramp
        p = Vector(p0).lerp(Vector(p1), e)
        kf(P["root"], "location", fr, (p.x, p.y, z + 0.07 * (math.cos(2 * math.pi * ph) - 1) * -0.5 * ramp))
        kf(P["hipL"], "rotation_euler", fr, (ang, 0, 0)); kf(P["hipR"], "rotation_euler", fr, (-ang, 0, 0))
        arm(P, "Left", fr, euler=(-math.degrees(ang) * 0.8 + 3, -4)); arm(P, "Right", fr, euler=(math.degrees(ang) * 0.8 + 3, 4))
        kf(P["chest"], "rotation_euler", fr, (DEG(-5) * ramp, 0, -ang * 0.15))
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", f1 + 2, (0, 0, 0))


@kit
def neck(P, fr, x=0, y=0, z=0, interp="BEZIER"):
    kf(P["neck"], "rotation_euler", fr, (DEG(x), DEG(y), DEG(z)), interp=interp)


@kit
def chest(P, fr, x=0, y=0, z=0, interp="BEZIER"):
    kf(P["chest"], "rotation_euler", fr, (DEG(x), DEG(y), DEG(z)), interp=interp)


@kit
def arms_down(P, fr):
    arm(P, "Left", fr, euler=(4, -6)); arm(P, "Right", fr, euler=(4, 6))


@kit
def smear(P, side, fr, k=1.35):
    sh = P[side]
    kf(sh, "scale", fr - 1, (1, 1, 1)); kf(sh, "scale", fr, (1, 1, k)); kf(sh, "scale", fr + 2, (1, 1, 1))


@kit
def strip_faces(P):
    for objs in P["faces"].values():
        for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    P["faces"] = {}


@kit
def sit(P, fr, loc, yaw):
    place(P, fr, loc, yaw)
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (DEG(90), 0, 0), interp="CONSTANT")


@kit
def stand(P, fr):
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (0, 0, 0), interp="CONSTANT")


@kit
def pose(P, loc, yaw):
    P["root"].location = Vector(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


@kit
def at(P, fr, loc, yaw):
    place(P, fr, Vector(loc), yaw); P["root"].location = Vector(loc); P["root"].rotation_euler = (0, 0, DEG(yaw))


@kit
def H(P, dz=0.0):
    return Vector(P["root"].location) + Vector((0, 0, 4.6 + dz))


@kit
def ray_only_glossy(P, on=True):
    """Mirror twin: visible ONLY in reflections (and the real one is hidden from reflections)."""
    for o in [P["root"]] + list(P["root"].children_recursive):
        if hasattr(o, "visible_camera"):
            o.visible_camera = not on; o.visible_diffuse = not on; o.visible_shadow = not on
            o.visible_transmission = not on; o.visible_volume_scatter = not on; o.visible_glossy = True


@kit
def no_reflection(P):
    for o in [P["root"]] + list(P["root"].children_recursive):
        if hasattr(o, "visible_glossy"): o.visible_glossy = False


@kit
def vis_obj(o, fr, on): kf(o, "hide_render", fr, not on, interp="CONSTANT")


@kit
def look_at(o, tgt): return (Vector(tgt) - o.location).to_track_quat("-Z", "Y").to_euler()


@kit
def spot(name, loc, tgt, energy, size_deg, radius, col):
    """Spot light aimed at tgt; energy is keyed per shot (starts at 0). Returns the light data."""
    d = bpy.data.lights.new(name, "SPOT"); d.energy = 0; d.spot_size = DEG(size_deg); d.spot_blend = 0.25
    d.shadow_soft_size = radius; d.color = col
    o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = Vector(loc)
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return d


# ================================================================== cast
@kit
def cast(park_far=True, **spec):
    """cast(milo=(make_milo, "rest_flat"), mum=(lambda: make_mum("Mum"), "rest_smile"), ...) -> the characters, in order.
    Strips the old faces, clears all animation, upgrades rigs, builds v2 faces. Sets CAST, RIGS (name -> face rig),
    keys each rest mouth at frame 1 (None = key it yourself) and parks everyone at FAR (park(P, fr) sends one back)."""
    Ps = [maker() for maker, _ in spec.values()]
    for P in Ps: strip_faces(P)
    for o in bpy.data.objects: o.animation_data_clear()
    for P in Ps: upgrade_rig(P)
    rigs = [build_face_v2(P) for P in Ps]
    _G["CAST"] = tuple(Ps); _G["RIGS"] = dict(zip(spec, rigs))
    for rig, (_, rest) in zip(rigs, spec.values()):
        if rest: mouth(rig, 1, rest)
    if park_far:
        for P in Ps: park(P, 1)
    return Ps


@kit
def park(P, fr):
    place(P, fr, FAR + Vector((CAST.index(P) * 12, 0, 0)))


# ================================================================== dialogue + blinks
_BLINKS = []


@kit
def blinks(rig, t0, t1, every=3.1, ph=0.0):
    _BLINKS.append((rig, t0, t1, every, ph))      # applied at the end, once every cut is known (no closed eyes before a cut)


@kit
def apply_blinks():
    for rig, t0, t1, every, ph in _BLINKS:
        t = t0 + 0.9 + ph
        while t < t1 - 0.4:
            fr = FT(t)
            if all(not (c - 7 <= fr <= c + 1) for c in CUT_FR): blink(rig, fr)
            t += every + 0.6 * math.sin(t * 1.7)


@kit
def say(L, rig, rest, style="calm", nod=3.0, P=None):
    """Lip-sync one in-scene line (L from line(t)) with that speaker's loudness envelope; accents (nods) if P is given."""
    ENV["rms"] = E2["rms"][L["who"]]; ENV["cen"] = E2["cen"][L["who"]]
    f0, f1 = FT(L["t0"]), FT(L["t1"]) + 1
    lipsync(rig, f0, f1, [(f0, rest, style)]); mouth(rig, f1 + 1, rest)
    if P is not None: accents(P, rig, f0, f1, nod=nod)


@kit
def line(t0):
    """The cue-sheet line that starts nearest t0 (seconds)."""
    return min(E2["lines"], key=lambda L: abs(L["t0"] - t0))


@kit
def live(P, t0, t1, mood):
    life(P, FT(t0), FT(t1) - 1, mood)       # motion.py life layer for a shot window


# ================================================================== camera (hard cuts, each shot keyed inside its frames)
def camera_rig(fstop=2.4):
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(cam); s.camera = cam
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop; cam.data.sensor_width = 36; cam.data.clip_end = 3000
    _G.update(cam=cam, SHOTS=[], _PREV_E=[None])
    return cam


@kit
def cam_key(fr, pos, tgt, lens, focus=None, interp="BEZIER"):
    pos = Vector(pos); tgt = Vector(tgt)
    kf(cam, "location", fr, pos, interp=interp)
    q = (tgt - pos).to_track_quat("-Z", "Y")
    if "CAM_ROLL" in _G and CAM_ROLL[0]:
        from mathutils import Quaternion as _Q; q = q @ _Q((0, 0, 1), DEG(CAM_ROLL[0]))
    e = q.to_euler()
    if _PREV_E[0] is not None: e.make_compatible(_PREV_E[0])
    _PREV_E[0] = e.copy()
    kf(cam, "rotation_euler", fr, e, interp=interp)
    kf(cam.data, "lens", fr, lens, interp=interp)
    cam.data.dof.focus_distance = focus or (tgt - pos).length
    cam.data.keyframe_insert("dof.focus_distance", frame=fr); _LOG.append((cam.data, "dof.focus_distance", fr, interp))


@kit
def shot(name, t0, t1, keys, fstop=2.4):
    """keys: [(u 0..1, pos, tgt, lens)] inside the shot; hard cut at t0. Character shots: use cinema.cine() instead."""
    f0, f1 = FT(t0), FT(t1) - 1
    SHOTS.append((name, f0, f1))
    for i, (u, p, g, l) in enumerate(keys):
        fr = f0 + int(round(u * (f1 - f0)))
        cam_key(fr, p, g, l, interp="CONSTANT" if fr >= f1 else "BEZIER")
    if keys[-1][0] < 1: cam_key(f1, keys[-1][1], keys[-1][2], keys[-1][3], interp="CONSTANT")
    cam.data.dof.aperture_fstop = fstop; cam.data.keyframe_insert("dof.aperture_fstop", frame=f0)
    _LOG.append((cam.data, "dof.aperture_fstop", f0, "CONSTANT"))


@kit
def ots(subj, other, along=3.0, side=1.3, dz=0.25):
    """Legacy over-the-shoulder camera point (use cine()): on the subj->other axis, pushed sideways off the other head."""
    a = H(subj); b = H(other); d = (b - a); d.z = 0; L = d.length; d.normalize()
    perp = Vector((d.y, -d.x, 0)) * side
    return a + d * min(along, L - 1.6) + perp + Vector((0, 0, dz))


# ================================================================== checks
def check_faces():
    """One mouth on every frame for every rig; no closed eyes in the 4 frames before a cut."""
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


def run_checks(allow=(), motion_chars=None, quiet=(), air=("MoonDust", "Smear"), shots=True, framing=True):
    """Every QA gate: faces, shots (camera in a mesh / blocked / lens covered), motion (POP/CHATTER), framing.
    Returns (face_probs, shot_probs). Writes TALK/shots_<part>.json for motion_audit.py."""
    probs = check_faces()
    print("FACE CHECK", "OK" if not probs else probs[:20])
    if "check_lipsync" in _G and any(r.get("lip_log") for r in RIGS.values()):     # speech-driven mouths (rig2 + visemes)
        lp = check_lipsync(RIGS); print("LIPSYNC CHECK", "OK" if not lp else lp[:20]); probs += lp
    json.dump({"shots": SHOTS, "nf": NF}, open(TALK + "shots_%s.json" % PART, "w"))
    load("director")                    # shot checker + render_quality
    shot_probs = []
    if shots:
        hid = [o for o in bpy.data.objects if o.name.startswith(air)]      # air specks are not blockers
        for o in hid: o.hide_viewport = True
        shot_probs = check_shots(SHOTS, allow=allow)
        if motion_chars:
            shot_probs += check_motion(motion_chars, SHOTS, NF, quiet=quiet)
        print("SHOTLIST", [(n, (a + b) // 2) for n, a, b in SHOTS])
        for o in hid:
            if not o.name.startswith("Smear"): o.hide_viewport = False
    if framing and "check_framing" in _G:
        shot_probs += check_framing(SHOTS)
    return probs, shot_probs


# ================================================================== finish: blinks, mouths, interpolation, life, checks, render
def finish_part(life=False, allow=(), motion_chars=None, quiet=(), shots=True, framing=True):
    """Call once after the last beat."""
    _G["CUT_FR"] = [f0 for _, f0, _ in SHOTS[1:]]
    apply_blinks()
    flush_mouths(); apply_interp(); hold_cuts(); apply_interpolation()
    if "breathe" in _G: breathe()                    # cinema.py: subtle camera breathing on held shots
    if life: bake_life()                             # motion.py life layer goes on top of everything
    probs, shot_probs = run_checks(allow, motion_chars, quiet, shots=shots, framing=framing)
    if shot_probs and not os.environ.get("FORCE"):
        raise SystemExit("shot check failed - fix the cameras (FORCE=1 to render anyway)")
    render_settings()
    if probs and not os.environ.get("FORCE"):
        raise SystemExit("face check failed - not rendering")
    render()


def render_settings():
    """Cycles on CPU here (SAMPLES, default 6) or GPU on the pod (ENGINE=GPU, OptiX then CUDA, SAMPLES default 32),
    QUALITY=fast light paths, OIDN albedo+normal (steadiest frame to frame), motion blur 0.5 START, PLAYBLAST=1 EEVEE."""
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
        s.cycles.device = "GPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 32))
    else:
        s.cycles.device = "CPU"; s.cycles.samples = int(os.environ.get("SAMPLES", 6))
    s.render.engine = "CYCLES"; s.cycles.use_denoising = True
    if "render_quality" not in _G: load("director")
    render_quality(s, os.environ.get("QUALITY", "fast"))     # Joel picked fast 22 Nov 15:23
    try:
        s.cycles.denoiser = "OPENIMAGEDENOISE"; s.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        s.cycles.denoising_prefilter = "ACCURATE"; s.cycles.denoising_use_gpu = True
    except Exception as _e: print("denoise opts", _e)
    s.render.use_persistent_data = True
    s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5; s.render.motion_blur_position = "START"
    s.render.resolution_x, s.render.resolution_y = int(os.environ.get("RX", 216)), int(os.environ.get("RY", 384))
    s.render.image_settings.file_format = "PNG"
    if os.environ.get("PLAYBLAST"):            # MOTION PREVIEW: EEVEE, low res, fast
        eng_ids = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
        s.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in eng_ids else "BLENDER_EEVEE_NEXT"
        try: s.eevee.taa_render_samples = int(os.environ.get("SAMPLES", 4))
        except Exception: pass
        s.render.use_motion_blur = False
    s.render.filepath = OUT + "/"
    s.frame_start = int(os.environ.get("FS", 1)); s.frame_end = int(os.environ.get("FE", NF))
    s.render.use_overwrite = False; s.render.use_placeholder = True


def frame_list(spec):
    """"5,12-40,300-310" -> [5, 12, 13, ... 40, 300, ... 310] (render_cache.py writes these RANGES)."""
    out = []
    for part in spec.replace(" ", "").split(","):
        if part:
            a, _, b = part.partition("-"); out += range(int(a), int(b or a) + 1)
    return out


def motion_flips(f0, f1):
    """Frames where an object in view (or the camera) starts or stops moving.
    Cycles bug (Blender 5.3, found 23 Nov): with persistent data + motion blur, an object whose motion starts or stops
    keeps stale motion data on that frame and renders as a black/unlit silhouette for that ONE frame. Moving(f) = its
    world matrix differs between shutter open (f) and close (f+0.5, motion_blur START). Cached per range in OUT."""
    from bpy_extras.object_utils import world_to_camera_view
    cache = OUT + "/.motion_flips_%d_%d.json" % (f0, f1)
    try: return set(json.load(open(cache)))
    except (OSError, ValueError): pass
    obs = [o for o in s.objects if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META") and not o.hide_render]
    cam = s.camera; sh = s.render.motion_blur_shutter
    def in_view(o, m):                                             # roughly in view: any bbox corner inside +10%
        for c in o.bound_box:
            v = world_to_camera_view(s, cam, m @ Vector(c))
            if v.z > 0 and -0.1 < v.x < 1.1 and -0.1 < v.y < 1.1: return True
        return False
    flips, prev = [], None
    for f in range(f0, f1 + 1):
        s.frame_set(f); a = [o.matrix_world.copy() for o in obs]; ca = cam.matrix_world.copy()
        s.frame_set(f, subframe=sh); mv = [x != o.matrix_world for x, o in zip(a, obs)]; cmv = ca != cam.matrix_world
        if prev is not None and (cmv != prev[1] or any(x != y and in_view(o, m) for x, y, o, m in zip(mv, prev[0], obs, a))):
            flips.append(f)
        prev = (mv, cmv)
    s.frame_set(f0)
    try: json.dump(flips, open(cache, "w"))
    except OSError: pass
    return set(flips)


def dark_shots(base):
    """Shots dark enough to show denoiser blotches at the base settings. One tiny render per shot (mid frame,
    72x128, 4 samples, ~0.3 s each), mean luma 0-1. Shots between 0.03 (intended black) and DARK_LUMA (default 0.13),
    darkest first, get DARK_SAMPLES (default 2x base) at noise threshold 0.01 until they cover DARK_BUDGET of the
    frames (default 0.08). Measured 23 Nov on Part 3 dark shots (CPU, vs a 256-sample reference): 64 spp + threshold
    0.01 = +1.8 dB, 22% less frame-to-frame flicker, 1.87x time per boosted frame -> <=7% extra render time.
    (64 spp at the normal 0.02 threshold gained nothing: the threshold, not the cap, limits dark shots.)
    Cached in OUT. Returns {frame: samples}."""
    cache = OUT + "/.dark_shots_%d.json" % base
    try: return {int(k): v for k, v in json.load(open(cache)).items()}
    except (OSError, ValueError): pass
    r = s.render; keep = (r.resolution_x, r.resolution_y, s.cycles.samples, r.filepath, r.use_motion_blur)
    r.resolution_x, r.resolution_y, s.cycles.samples, r.use_motion_blur = 72, 128, 4, False
    lum = []
    for name, f0, f1 in SHOTS:
        s.frame_set((f0 + f1) // 2); r.filepath = os.path.join(bpy.app.tempdir or "/tmp", "kit_lum.png"); bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(r.filepath, check_existing=False); px = list(im.pixels)
        lum.append((sum(0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2] for i in range(0, len(px), 4)) / (len(px) // 4),
                    name, f0, f1))
        bpy.data.images.remove(im)
    r.resolution_x, r.resolution_y, s.cycles.samples, r.filepath, r.use_motion_blur = keep
    thr = float(os.environ.get("DARK_LUMA", 0.13)); budget = float(os.environ.get("DARK_BUDGET", 0.08)) * NF
    hi = int(os.environ.get("DARK_SAMPLES", 2 * base)); out, used = {}, 0
    for l, name, f0, f1 in sorted(lum):
        if l >= thr: break
        if l < 0.03: continue                                      # intended black: nothing to clean
        if used + (f1 - f0 + 1) > budget: continue
        used += f1 - f0 + 1; out.update({f: hi for f in range(f0, f1 + 1)}); print("DARK SHOT %s %.3f -> %d samples" % (name, l, hi))
    print("SHOT LUMA", [(n, round(l, 3)) for l, n, _, _ in sorted(lum)][:12], "boosted frames", used)
    try: json.dump(out, open(cache, "w"))
    except OSError: pass
    return out


def _render_frame(fr, fresh):
    """One frame. fresh=True drops Cycles' persistent data for it (rebuilt from scratch = correct motion data)."""
    s.render.use_persistent_data = not fresh
    s.frame_set(fr); s.render.filepath = OUT + "/%04d.png" % fr; bpy.ops.render.render(write_still=True)
    s.render.use_persistent_data = True


def render():
    """RENDER=1: FRAMES=a,b stills, RANGES=a-b,c only those frames (render_cache.py: what a tweak changed), else the
    whole range. Frames come from a shared queue (atomic 0-byte placeholder
    per frame, so several GPUs/helpers can work one folder); frames where something starts or stops moving render
    without persistent data (see motion_flips). Persistent data stays on elsewhere (~30% faster per frame)."""
    if os.environ.get("RENDER"):
        os.makedirs(OUT, exist_ok=True)
        if os.environ.get("FRAMES"):
            frames = [int(x) for x in os.environ["FRAMES"].split(",")]
            flips = motion_flips(min(frames), max(frames)) if s.render.use_motion_blur else set()
            for fr in frames: _render_frame(fr, fr in flips)
        else:
            frames = frame_list(os.environ["RANGES"]) if os.environ.get("RANGES") else list(range(s.frame_start, s.frame_end + 1))
            flips = motion_flips(max(1, min(frames) - 1), max(frames)) if s.render.use_motion_blur else set()
            print("MOTION FLIPS (fresh render, no persistent data):", sorted(flips))
            base, thr0 = s.cycles.samples, s.cycles.adaptive_threshold
            dark = dark_shots(base) if base >= 16 and s.render.engine == "CYCLES" and not os.environ.get("NODARK") else {}
            for fr in frames:
                try: os.close(os.open(OUT + "/%04d.png" % fr, os.O_CREAT | os.O_EXCL))   # claim the frame
                except FileExistsError: continue                                         # done or someone's on it
                s.cycles.samples = dark.get(fr, base); s.cycles.adaptive_threshold = 0.01 if fr in dark else thr0
                _render_frame(fr, fr in flips)
            s.cycles.samples, s.cycles.adaptive_threshold = base, thr0
    print("DONE", NF)
