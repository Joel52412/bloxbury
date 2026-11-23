# motion.py - ANIMATION LIBRARY (Joel 22 Nov 23:49: "fluid, never stiff, nothing like AI-slop channels").
# Roblox-animator rules baked in: every move has ANTICIPATION (a small wind-up the other way), an eased main move,
# OVERSHOOT and a SETTLE; fast moves get a smear frame; nobody is ever dead still (breathing, weight shift, head
# drift, eye-line darts, scared tremble) via an ADDITIVE LIFE LAYER baked on top of all keys at the end.
# Load after rig2.py (needs kf, arm_angles, R/DEG, FPS).  Scene usage:
#   gesture(P, "Right", fr, target=(x,y,z))        arm move with wind-up + overshoot + settle
#   look(P, fr, x, y, z)                            head turn (neck) with overshoot
#   lean(P, fr, x, y, z)                            chest lean with overshoot
#   run(P, f0, f1, [p0, p1, ...], z)                run cycle along a path (faces travel direction, leans, bounces)
#   sit_down(P, f0, f1, loc, yaw, seat_z)           stand -> sit (legs forward, bottom ON the seat)
#   life(P, f0, f1, mood="calm"|"scared"|"tense")   register a life window; bake_life() once at the very end
import math, random
from mathutils import Vector as _MV

_ST = {}          # (id(P), part) -> last pose, so the next move winds up from where the body really is
SIT_DROP = 1.5    # R6: hips pivot 2 studs above the root, legs 1 thick -> root sits 1.5 below the seat surface


def _last(P, key, default):
    return _ST.get((id(P), key), default)


def _arm_ae(side, target=None, euler=None):
    if target is not None: return arm_angles(side, target)
    return (math.radians(euler[0]), math.radians(euler[1]))


def _arm_key(P, side, fr, a, c, interp="BEZIER"):
    kf(P[side], "rotation_euler", fr, (a, 0, c), interp=interp)
    kf(P["grip" + side], "rotation_euler", fr, (-a, 0, -c), interp=interp)


def pose_arm(P, side, fr, target=None, euler=None):
    """Snap an arm (use on a CUT): no wind-up, just remembers the pose."""
    a, c = _arm_ae(side, target, euler); _arm_key(P, side, fr, a, c, interp="CONSTANT"); _ST[(id(P), side)] = (a, c)


def gesture(P, side, fr, target=None, euler=None, dur=8, ant=0.14, over=0.12, hold_from=None):
    """Arm move that STARTS at fr: wind-up (2 f), eased travel, overshoot, settle at fr+dur. Smear on big fast moves."""
    a1, c1 = _arm_ae(side, target, euler)
    a0, c0 = _last(P, side, (math.radians(4), math.radians(-6 if side == "Left" else 6)))
    _arm_key(P, side, (hold_from if hold_from is not None else fr) - 1, a0, c0)
    _arm_key(P, side, fr + 2, a0 - (a1 - a0) * ant, c0 - (c1 - c0) * ant)
    _arm_key(P, side, fr + 2 + int(dur * 0.55), a1 + (a1 - a0) * over, c1 + (c1 - c0) * over)
    _arm_key(P, side, fr + 2 + dur, a1, c1)
    if abs(a1 - a0) + abs(c1 - c0) > math.radians(55) and dur <= 9:
        sh = P[side]; m = fr + 2 + int(dur * 0.3)
        kf(sh, "scale", m - 1, (1, 1, 1)); kf(sh, "scale", m, (1, 1, 1.3)); kf(sh, "scale", m + 2, (1, 1, 1))
    _ST[(id(P), side)] = (a1, c1)
    return fr + 2 + dur


def _rot_beat(P, part, fr, rot, dur, over, ant):
    r0 = _last(P, part, (0.0, 0.0, 0.0)); r1 = tuple(math.radians(v) for v in rot)
    ob = P[part]
    kf(ob, "rotation_euler", fr - 1, r0)
    kf(ob, "rotation_euler", fr + 2, tuple(a - (b - a) * ant for a, b in zip(r0, r1)))
    kf(ob, "rotation_euler", fr + 2 + int(dur * 0.6), tuple(b + (b - a) * over for a, b in zip(r0, r1)))
    kf(ob, "rotation_euler", fr + 2 + dur, r1)
    _ST[(id(P), part)] = r1


def look(P, fr, x=0, y=0, z=0, dur=8, over=0.15, ant=0.08):
    _rot_beat(P, "neck", fr, (x, y, z), dur, over, ant)


def lean(P, fr, x=0, y=0, z=0, dur=10, over=0.12, ant=0.1):
    _rot_beat(P, "chest", fr, (x, y, z), dur, over, ant)


def snap_rot(P, part, fr, x=0, y=0, z=0):
    r = tuple(math.radians(v) for v in (x, y, z)); kf(P[part], "rotation_euler", fr, r, interp="CONSTANT"); _ST[(id(P), part)] = r


def run(P, f0, f1, pts, z=0.0, stride=2.6, leg=50, arm_sw=58, lean_deg=14, bounce=0.28, accel=0.18):
    """Run cycle along a polyline: speeds up / slows down at the ends, turns to face where it's going (smoothed),
    legs + opposite arm pump, forward lean, double bounce per stride, head counter-bob. Returns the end yaw."""
    pts = [_MV((p[0], p[1], z)) for p in pts]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; L = sum(seg)
    n = f1 - f0; yaw_prev = None
    def at_s(sv):
        acc = 0
        for i, sl in enumerate(seg):
            if acc + sl >= sv or i == len(seg) - 1:
                u = (sv - acc) / sl if sl else 0; return pts[i].lerp(pts[i + 1], min(1, max(0, u))), (pts[i + 1] - pts[i])
            acc += sl
    vel = [min(1.0, (i / n) / accel, (1 - i / n) / accel) + 0.05 for i in range(n + 1)]   # speed up, cruise, slow down
    cum = [0.0]
    for v in vel[1:]: cum.append(cum[-1] + v)
    for i in range(n + 1):
        fr = f0 + i; u = i / n
        sv = cum[i] / cum[-1] * L
        p, d = at_s(sv)
        yaw = math.atan2(-d.x, d.y)
        if yaw_prev is not None:
            while yaw - yaw_prev > math.pi: yaw -= 2 * math.pi
            while yaw - yaw_prev < -math.pi: yaw += 2 * math.pi
            yaw = yaw_prev + (yaw - yaw_prev) * 0.25            # smooth turn into curves
        yaw_prev = yaw
        ph = sv / stride * math.pi
        ramp = min(1.0, u / 0.08, (1 - u) / 0.08) if 0 < u < 1 else 0.0
        sw = math.sin(ph)
        kf(P["root"], "location", fr, (p.x, p.y, z + bounce * abs(math.sin(ph)) * ramp))
        kf(P["root"], "rotation_euler", fr, (0, 0, yaw))
        kf(P["hipL"], "rotation_euler", fr, (math.radians(leg) * sw * ramp, 0, 0))
        kf(P["hipR"], "rotation_euler", fr, (-math.radians(leg) * sw * ramp, 0, 0))
        _arm_key(P, "Left", fr, math.radians(-arm_sw * sw * ramp + 12), math.radians(-10))
        _arm_key(P, "Right", fr, math.radians(arm_sw * sw * ramp + 12), math.radians(10))
        kf(P["chest"], "rotation_euler", fr, (math.radians(-lean_deg) * ramp, 0, -0.12 * sw * ramp))
        kf(P["neck"], "rotation_euler", fr, (math.radians(lean_deg * 0.6) * ramp, 0, 0.06 * sw * ramp))
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", f1 + 3, (0, 0, 0))
    _ST[(id(P), "Left")] = (math.radians(4), math.radians(-6)); _ST[(id(P), "Right")] = (math.radians(4), math.radians(6))
    _ST[(id(P), "chest")] = (0, 0, 0); _ST[(id(P), "neck")] = (0, 0, 0)
    kf(P["chest"], "rotation_euler", f1 + 4, (0, 0, 0)); kf(P["neck"], "rotation_euler", f1 + 4, (0, 0, 0))
    return yaw_prev


def sit_down(P, f0, f1, loc, yaw, seat_z):
    """Standing at loc (feet on seat_z - the floor under it) -> sitting with the bottom ON seat_z, legs forward."""
    loc = _MV(loc)
    kf(P["root"], "location", f0, (loc.x, loc.y, loc.z)); kf(P["root"], "rotation_euler", f0, (0, 0, math.radians(yaw)))
    mid = f0 + (f1 - f0) // 2
    kf(P["root"], "location", mid, (loc.x, loc.y, loc.z - 0.4))                   # knees give
    kf(P["root"], "location", f1, (loc.x, loc.y, seat_z - SIT_DROP))
    kf(P["root"], "location", f1 + 3, (loc.x, loc.y, seat_z - SIT_DROP - 0.06)); kf(P["root"], "location", f1 + 6, (loc.x, loc.y, seat_z - SIT_DROP))
    for h in ("hipL", "hipR"):
        kf(P[h], "rotation_euler", f0, (0, 0, 0)); kf(P[h], "rotation_euler", f1, (math.radians(94), 0, 0)); kf(P[h], "rotation_euler", f1 + 4, (math.radians(90), 0, 0))
    lean(P, f0, -14, 0, 0, dur=max(4, (f1 - f0) // 2)); lean(P, f1, -6, 0, 0, dur=6)


def seated(P, fr, loc, yaw, seat_z):
    """Snap to a sitting pose (on a CUT)."""
    loc = _MV(loc)
    kf(P["root"], "location", fr, (loc.x, loc.y, seat_z - SIT_DROP), interp="CONSTANT"); kf(P["root"], "rotation_euler", fr, (0, 0, math.radians(yaw)), interp="CONSTANT")
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (math.radians(90), 0, 0), interp="CONSTANT")


def standing(P, fr):
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fr, (0, 0, 0), interp="CONSTANT")


# ------------------------------------------------------------------ the LIFE LAYER (additive, baked at the end)
_LIFE = []
MOODS = {"calm": (1.0, 0.0, 1.0), "tense": (1.4, 0.25, 1.3), "scared": (1.8, 0.7, 1.6), "still": (0.6, 0.0, 0.5)}


def life(P, f0, f1, mood="calm", seed=None):
    _LIFE.append((P, f0, f1, mood, seed if seed is not None else len(_LIFE) * 7 + 3))


def _noise(t, seed, k=3):
    rnd = random.Random(seed); s = 0.0
    for i in range(k):
        f = rnd.uniform(0.15, 0.6) * (i + 1); ph = rnd.uniform(0, 6.28); s += math.sin(t * f * 6.28 + ph) / (i + 1)
    return s / 1.8


def _fc(ob, path, idx):
    for fc in _fcurves(ob):
        if fc.data_path == path and fc.array_index == idx: return fc
    ob.keyframe_insert(path, frame=1, index=idx)
    for fc in _fcurves(ob):
        if fc.data_path == path and fc.array_index == idx: return fc


def bake_life(step=2):
    """Add breathing, head drift, eye-line darts, weight sway and (scared) tremble ON TOP of every existing key:
    sample each channel, add the signal, write keys every `step` frames inside each life window."""
    import bpy
    for P, f0, f1, mood, seed in _LIFE:
        breath, trem, drift = MOODS[mood]
        chans = [(P["chest"], "rotation_euler", 0, lambda t: math.radians(1.1 * breath) * math.sin(t * 2 * math.pi / (3.6 / breath ** 0.5))),
                 (P["chest"], "rotation_euler", 2, lambda t: math.radians(1.6 * drift) * _noise(t * 0.5, seed + 1)),
                 (P["neck"], "rotation_euler", 0, lambda t: math.radians(2.0 * drift) * _noise(t * 0.6, seed + 2) + math.radians(0.9 * trem) * math.sin(t * 37)),
                 (P["neck"], "rotation_euler", 2, lambda t: math.radians(3.5 * drift) * _noise(t * 0.45, seed + 3) + math.radians(1.2 * trem) * math.sin(t * 41 + 1)),
                 (P["neck"], "rotation_euler", 1, lambda t: math.radians(1.5 * drift) * _noise(t * 0.35, seed + 4)),
                 (P["Left"], "rotation_euler", 0, lambda t: math.radians(1.4 * breath) * math.sin(t * 2 * math.pi / 3.6 + 0.6) + math.radians(0.8 * trem) * math.sin(t * 43)),
                 (P["Right"], "rotation_euler", 0, lambda t: math.radians(1.4 * breath) * math.sin(t * 2 * math.pi / 3.6 + 0.9) + math.radians(0.8 * trem) * math.sin(t * 47 + 2))]
        for ob, path, idx, sig in chans:
            fc = _fc(ob, path, idx)
            base = {fr: fc.evaluate(fr) for fr in range(f0, f1 + 1, step)}
            for fr, v in base.items():
                kp = fc.keyframe_points.insert(fr, v + sig(fr / FPS), options={"FAST"})
                kp.interpolation = "BEZIER"
            fc.update()
