# cinema.py - Bloxbury camera grammar. Load after the scene's shot()/cam_key()/H() exist:
#     exec(open(SCR + "cinema.py").read())
# Shots are described by WHAT they frame, not by raw camera coordinates:
#     cine("P2 Did she knock?", 21.45, 23.35, rae, toward=milo, size="MCU", move="push", sx=-0.12)
# The solver puts the subject at a fixed screen spot and size at the start AND the end of the move, so a move can
# never drift off its subject or zoom into a cropped face. check_framing() fails the build if one does.
#
# Rules (from Pixar/Disney layout + horror practice, Joel 22 Nov):
#   - Dolly, don't zoom: the lens stays fixed inside a shot (lens changes only between shots).
#   - Moves are small and land early: <=25% size change, eased, then settle for the last ~20% of the shot.
#   - Eyes on the upper third; looking room in front of the face; leave empty space where the threat could be.
#   - Vary shot size and move between neighbouring cuts (wide -> MCU -> insert -> CU), never 3 of the same in a row.
#   - Horror toolkit: hold on the character (we hear it, don't see it), slow push on a realisation, pull-out reveal,
#     the threat in frame that the character misses, foreground occlusion (peeking past a door frame).
import math
from mathutils import Vector as _CV

HEAD_SPAN = 1.35                 # Roblox head + hair, studs
BODY_SPAN = 5.8                  # full R6 body incl. hair
SIZES = {                        # fraction of FRAME HEIGHT the head fills (FS/WS: the whole body)
    "ECU": 0.40, "CU": 0.28, "MCU": 0.19, "MS": 0.12,
    "FS": 0.62, "WS": 0.34,
}
bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1080, 1920   # portrait BEFORE any
# framing maths/checks: sensor fit AUTO puts the 36 mm sensor on the LONGER side (landscape default = wrong sizes)
MAX_HEAD = 0.45                  # bigger than this = the face is cropped ("zoomed into nothing")
FRAMING = {}                     # shot name -> [target]; target = (object, offset) or a fixed point
SHOT_META = {}                   # shot name -> (size, move) for the variety check
_CINE_ORDER = []


def _subj(P):
    """Head centre (static, at script time) + a live target for the framing check."""
    if isinstance(P, dict):
        return H(P), (P["head"], _CV((0, 0, 0)))
    v = _CV(P); return v, v


def _toward_dir(sv, toward):
    if isinstance(toward, dict): toward = H(toward)
    d = _CV(toward) - sv; d = _CV((d.x, d.y, 0))
    return d.normalized()


def solve(sv, u, size, lens, sx=0.0, sy=0.12, tilt=4.0, span=None, yaw=0.0):
    """Camera (pos, aim) so a span-stud subject at sv fills `size` of the frame height, sitting at screen (sx, sy)
    (fractions of the frame, +sy = up). u = horizontal direction from subject to camera; tilt > 0 = camera above
    looking down (vulnerable), tilt < 0 = below looking up (threat). yaw rotates u (degrees) for orbit/drift."""
    span = span or (BODY_SPAN if size in ("FS", "WS") else HEAD_SPAN)
    f = SIZES[size] if isinstance(size, str) else size
    h = span / f                                   # frame height in studs at the subject
    d = h * lens / 36.0                            # sensor 36 mm fits the frame height (portrait render)
    c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    u = _CV((u.x * c - u.y * s_, u.x * s_ + u.y * c, 0)).normalized()
    t = math.radians(tilt)
    dirn = u * math.cos(t) + _CV((0, 0, math.sin(t)))
    pos = sv + dirn * d
    fwd = -dirn; right = fwd.cross(_CV((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
    aim = sv - right * (sx * h * 9 / 16) - up * (sy * h)
    return pos, aim


CAM_ROLL = [0.0]          # dutch angle (deg) applied by cam_key while a shot is keyed


def cine(name, t0, t1, subj, toward=None, size="MCU", move="push", lens=40, sx=0.0, sy=0.12, tilt=4.0,
         amt=None, land=0.8, fstop=2.4, span=None, extra=(), u=None, ang=0.0, roll=0.0, hand=0.0):
    """One shot from the move vocabulary:
       hold   - near-locked-off (3%): dread, let the line land
       push   - slow dolly in (amt=1.2): realisation, a key word
       pull   - dolly out (amt=1.35): reveal / isolation
       drift  - slow orbit (amt=8 deg) at constant size: parallax, life in a dialogue shot
       rise / sink - camera height change (amt=8 deg tilt): sink = looking up at a threat
       static - locked off (geography wides, the stare, listening); breathe() still floats it a hair
       arc    - orbit amt=24 deg at constant size: swivel with a head turn instead of cutting to a reverse
       crane  - big height change (amt=20 deg tilt), descending from high: top-down -> closer to eye level
       roll = dutch angle in degrees (wrongness); hand = handheld float strength for panic shots (0.003-0.005)
       CAMERA.md says when to use which.
       toward = a character/point the camera sits on the side of; ang swings the camera round the subject from that
       line (degrees), e.g. ang=28 for a clean over-the-shoulder that never sits inside the other head.
       Subject = character dict (frames the head) or a world point. extra = more targets the frame must keep."""
    sv, tgt = _subj(subj)
    if u is None:
        u = _toward_dir(sv, toward) if toward is not None else _CV((0, -1, 0))
    f = SIZES[size] if isinstance(size, str) else size
    sp = span or (BODY_SPAN if size in ("FS", "WS") else HEAD_SPAN)
    a = dict(lens=lens, sx=sx, sy=sy, tilt=tilt, span=sp)
    if move == "hold":   A, B = dict(size=f), dict(size=f * 1.03)
    elif move == "push": A, B = dict(size=f / (amt or 1.2) ** 0.5), dict(size=f * (amt or 1.2) ** 0.5)
    elif move == "pull": A, B = dict(size=f * (amt or 1.35) ** 0.5), dict(size=f / (amt or 1.35) ** 0.5)
    elif move == "drift": A, B = dict(size=f, yaw=-(amt or 8) / 2), dict(size=f * 1.04, yaw=(amt or 8) / 2)
    elif move == "static": A, B = dict(size=f), dict(size=f)
    elif move == "arc": A, B = dict(size=f, yaw=-(amt or 24) / 2), dict(size=f * 1.02, yaw=(amt or 24) / 2)
    elif move == "crane": A, B = dict(size=f * 0.95, tilt=tilt + (amt or 20) / 2), dict(size=f, tilt=tilt - (amt or 20) / 2)
    elif move in ("rise", "sink"):
        k = (amt or 8) / 2 * (1 if move == "rise" else -1)
        A, B = dict(size=f, tilt=tilt - k), dict(size=f * 1.04, tilt=tilt + k)
    else: raise ValueError(move)
    A["yaw"] = A.get("yaw", 0) + ang; B["yaw"] = B.get("yaw", 0) + ang
    pa, ga = solve(sv, u, **{**a, **A}); pb, gb = solve(sv, u, **{**a, **B})
    keys = [(0, pa, ga, lens), (land, pb, gb, lens)]
    if move == "static": keys = [(0, pa, ga, lens), (1, pa, ga, lens)]
    elif land < 1:                                   # settle: a last 1% creep so the frame never goes dead-still
        pc = pb + (pb - pa).normalized() * 0.02 if (pb - pa).length > 1e-4 else pb
        keys.append((1, pc, gb, lens))
    CAM_ROLL[0] = roll; shot(name, t0, t1, keys, fstop=fstop); CAM_ROLL[0] = 0.0
    if hand: handheld(t0, t1, hand)
    FRAMING[name] = [tgt] + list(extra)
    SHOT_META[name] = (size if isinstance(size, str) else "custom", move)
    _CINE_ORDER.append(name)


def insert(name, t0, t1, start_pt, end_pt, normal, start_w, end_w, lens=50, land=0.75, fstop=5.0):
    """Insert shot on a flat thing (a page, a photo): frames start_w studs wide around start_pt, then glides to
    end_w around end_pt (e.g. whole page -> the crossed-out name), lands at `land` and holds."""
    n = _CV(normal).normalized()
    def at(pt, w):
        h = w * 16 / 9; d = h * lens / 36.0
        return _CV(pt) + n * d + _CV((0, 0, 0.02 * d)), _CV(pt)
    pa, ga = at(start_pt, start_w); pb, gb = at(end_pt, end_w)
    shot(name, t0, t1, [(0, pa, ga, lens), (land, pb, gb, lens), (1, pb + (pb - gb).normalized() * -0.01, gb, lens)], fstop=fstop)
    FRAMING[name] = [_CV(end_pt)]
    SHOT_META[name] = ("insert", "push")
    _CINE_ORDER.append(name)


_HAND = []


def handheld(t0, t1, strength=0.004):
    """Panic float for one shot only (restricted-range noise on the camera rotation, blended in/out). Applied by breathe()."""
    _HAND.append((FT(t0), FT(t1) - 1, strength))


def breathe(strength=0.0012, scale=70):
    """Barely-there handheld float on the camera rotation (never a shake). Call once, after all shots."""
    ad = cam.animation_data
    for fc in _fcurves(cam):
        if fc.data_path == "rotation_euler" and fc.array_index in (0, 2):
            m = fc.modifiers.new("NOISE"); m.strength = strength; m.scale = scale; m.phase = 7 * fc.array_index + 3
            for k, (f0, f1, st) in enumerate(_HAND):
                h = fc.modifiers.new("NOISE"); h.strength = st; h.scale = 9; h.phase = 13 * k + 5 * fc.array_index
                h.use_restricted_range = True; h.frame_start = f0; h.frame_end = f1; h.blend_in = 3; h.blend_out = 3


def _proj(scene, camo, p):
    from bpy_extras.object_utils import world_to_camera_view
    return world_to_camera_view(scene, camo, p)


def check_framing(shots, edge=0.06, max_drift=0.28, verbose=True):
    """OFF   - a framed target leaves the picture (or sits on its very edge) at the start, middle or end
       CROP  - a head fills more than MAX_HEAD of the frame height (face cut off)
       DRIFT - the target slides more than max_drift of the frame during the shot
       SAME  - three neighbouring shots with the same size AND move (monotonous)"""
    scene = bpy.context.scene; camo = scene.camera; probs = []
    for name, f0, f1 in shots:
        if name not in FRAMING: continue
        pos = []
        for fr in (f0, (f0 + f1) // 2, f1):
            scene.frame_set(fr)
            for t in FRAMING[name][:1] + FRAMING[name][1:]:
                p = (t[0].matrix_world.translation + t[1]) if isinstance(t, tuple) else _CV(t)
                c = _proj(scene, camo, p)
                if c.z <= 0 or not (edge < c.x < 1 - edge and edge < c.y < 1 - edge):
                    probs.append(("OFF", name, fr, "target at (%.2f, %.2f)" % (c.x, c.y)))
                if isinstance(t, tuple):
                    top = _proj(scene, camo, p + _CV((0, 0, HEAD_SPAN / 2))); bot = _proj(scene, camo, p - _CV((0, 0, HEAD_SPAN / 2)))
                    if abs(top.y - bot.y) > MAX_HEAD: probs.append(("CROP", name, fr, "head %.0f%% of frame" % (100 * abs(top.y - bot.y))))
            pos.append(c)
        if SHOT_META.get(name, ("",))[0] != "insert" and (_CV((pos[0].x, pos[0].y)) - _CV((pos[-1].x, pos[-1].y))).length > max_drift:
            probs.append(("DRIFT", name, f1, "slid %.2f of the frame" % (_CV((pos[0].x, pos[0].y)) - _CV((pos[-1].x, pos[-1].y))).length))
    o = _CINE_ORDER
    for i in range(2, len(o)):
        if SHOT_META[o[i]] == SHOT_META[o[i - 1]] == SHOT_META[o[i - 2]]:
            probs.append(("SAME", o[i], 0, "3 in a row: %s %s" % SHOT_META[o[i]]))
    if verbose:
        print("FRAMING CHECK", "OK (%d framed shots)" % len(FRAMING) if not probs else "%d problems" % len(probs))
        for p in probs: print("   ", *p)
    return probs
