# motion.py - ANIMATION LIBRARY (Joel 22 Nov 23:49: "fluid, never stiff, nothing like AI-slop channels").
# Roblox-animator rules baked in: every move has ANTICIPATION (a small wind-up the other way), an eased main move,
# OVERSHOOT and a SETTLE; fast moves get a smear frame; nobody is ever dead still (breathing, weight shift, head
# drift, eye-line darts, scared tremble) via an ADDITIVE LIFE LAYER baked on top of all keys at the end.
# Load after rig2.py (needs kf, arm_angles, R/DEG, FPS).  Scene usage:
#   gesture(P, "Right", fr, target=(x,y,z))        arm move with wind-up + overshoot + settle
#   look(P, fr, x, y, z)                            head turn (neck); x > 0 = head UP, x < 0 = looks DOWN (checked 23 Nov)
#   lean(P, fr, x, ...)                             x < 0 = leans FORWARD
#   lean(P, fr, x, y, z)                            chest lean with overshoot
#   run(P, f0, f1, [p0, p1, ...], z)                run cycle along a path (faces travel direction, leans, bounces)
#   crawl(P, fd, f0, f1, fu, p0, p1)                 drop to all fours, scramble, get up (under a fence rail)
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


# ------------------------------------------------------------------ EASED MOVES (Joel 23 Nov 10:14: "they start quick and stop quick")
# Every beat is written frame by frame from ONE smooth curve: slow-in, slow-out (smootherstep), with the wind-up and the
# overshoot built into the curve (a soft "back" ease), so nothing ever starts or stops on a dime. A new beat starts from
# wherever the body REALLY is (evaluated), so overlapping beats blend instead of jumping. dur <= 5 = a deliberately quick
# action (slap, flip); anything longer is stretched by PACE so normal moves breathe.
PACE = 1.5


def _ease(u, ant, over):
    """0..1 -> 0..1 slow-in / slow-out, dipping back by ~ant at the start and passing the end by ~over."""
    u = max(0.0, min(1.0, u))
    e = u * u * u * (u * (u * 6 - 15) + 10)                       # smootherstep: zero velocity AND acceleration at both ends
    dip = -ant * math.sin(math.pi * min(1.0, u / 0.3)) if u < 0.3 else 0.0          # gentle wind-up in the first 30%
    bump = over * math.sin(math.pi * (u - 0.55) / 0.45) if u > 0.55 else 0.0       # rises past the target, settles back
    return e + dip + bump


def _dur(dur):
    return dur if dur <= 5 else int(round(dur * PACE))


def _cur(ob, path, n, fr):
    """The channel's real value at frame fr (falls back to the current property)."""
    vals = list(getattr(ob, path))[:n]
    for fc in _fcurves(ob):
        if fc.data_path == path and fc.array_index < n: vals[fc.array_index] = fc.evaluate(fr)
    return vals


def _clear(ob, path, f0, f1):
    for fc in _fcurves(ob):
        if fc.data_path == path:
            for kp in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]: fc.keyframe_points.remove(kp)


def _beat(ob, path, fr, v1, dur, ant, over, mirror=None):
    """Write one eased beat on ob.path (3-vector) from its real value at fr to v1 over dur frames."""
    v0 = _cur(ob, path, 3, fr)
    _clear(ob, path, fr + 1, fr + dur + 1)
    if mirror is not None: _clear(mirror, path, fr + 1, fr + dur + 1)
    kf(ob, path, fr, tuple(v0))
    if mirror is not None: kf(mirror, path, fr, tuple(-x for x in v0))
    for i in range(1, dur + 1):
        k = _ease(i / dur, ant, over)
        v = tuple(a + (b - a) * k for a, b in zip(v0, v1))
        kf(ob, path, fr + i, v)
        if mirror is not None: kf(mirror, path, fr + i, tuple(-x for x in v))


def gesture(P, side, fr, target=None, euler=None, dur=8, ant=0.08, over=0.06, hold_from=None):
    """Arm move that STARTS at fr with slow-in, eased travel, a small overshoot and a slow settle."""
    a1, c1 = _arm_ae(side, target, euler); d = _dur(dur)
    _beat(P[side], "rotation_euler", fr, (a1, 0, c1), d, ant, over, mirror=P["grip" + side])
    _ST[(id(P), side)] = (a1, c1)
    return fr + d


def _rot_beat(P, part, fr, rot, dur, over, ant):
    r1 = tuple(math.radians(v) for v in rot)
    _beat(P[part], "rotation_euler", fr, r1, _dur(dur), ant, over)
    _ST[(id(P), part)] = r1


def look(P, fr, x=0, y=0, z=0, dur=8, over=0.05, ant=0.03):
    _rot_beat(P, "neck", fr, (x, y, z), dur, over, ant)


def lean(P, fr, x=0, y=0, z=0, dur=10, over=0.04, ant=0.03):
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


def crawl(P, fd, f0, f1, fu, p0, p1, z=0.0, pitch=-76, cycle=9, arm=26, leg=20):
    """Drop to hands and knees (fd..f0), scramble from p0 to p1 (f0..f1), get back up (f1..fu).
    R6 has no knees: the whole body pitches forward from the feet (root), arms reach for the ground and alternate with
    the legs, head held up to look where he's going. Root = feet, so the HEAD is ~5 studs ahead of p (plan the gap)."""
    a = _MV((p0[0], p0[1], z)); b = _MV((p1[0], p1[1], z)); d = b - a
    yaw = math.atan2(-d.x, d.y); pr = math.radians(pitch)
    a_dn = math.radians(88)                                                  # arms down to the ground
    kf(P["root"], "rotation_euler", fd, (0, 0, yaw))
    kf(P["root"], "location", fd, a)
    kf(P["root"], "rotation_euler", fd + 2, (math.radians(4), 0, yaw))            # tiny wind-up back
    kf(P["root"], "rotation_euler", f0, (pr, 0, yaw))
    _arm_key(P, "Left", fd, *_last(P, "Left", (math.radians(4), math.radians(-6))))
    _arm_key(P, "Right", fd, *_last(P, "Right", (math.radians(4), math.radians(6))))
    _arm_key(P, "Left", f0, a_dn, math.radians(-8)); _arm_key(P, "Right", f0, a_dn, math.radians(8))
    kf(P["neck"], "rotation_euler", fd, _last(P, "neck", (0, 0, 0))); kf(P["neck"], "rotation_euler", f0, (math.radians(55), 0, 0))
    kf(P["chest"], "rotation_euler", fd, _last(P, "chest", (0, 0, 0))); kf(P["chest"], "rotation_euler", f0, (0, 0, 0))
    n = f1 - f0
    for i in range(0, n + 1, 2):
        fr = f0 + i; u = i / n; ue = u * u * (3 - 2 * u) * 0.35 + u * 0.65          # gentle ease, mostly steady
        ph = (i / cycle) * 2 * math.pi; sw = math.sin(ph); ramp = min(1.0, i / 4.0, (n - i) / 4.0)
        kf(P["root"], "location", fr, a.lerp(b, ue) + _MV((0, 0, 0.08 * abs(math.cos(ph)) * ramp)))
        kf(P["root"], "rotation_euler", fr, (pr + math.radians(1.5) * sw * ramp, 0, yaw + 0.04 * sw * ramp))
        _arm_key(P, "Left", fr, a_dn + math.radians(arm) * sw * ramp, math.radians(-8))
        _arm_key(P, "Right", fr, a_dn - math.radians(arm) * sw * ramp, math.radians(8))
        kf(P["hipL"], "rotation_euler", fr, (-math.radians(leg) * sw * ramp, 0, 0))
        kf(P["hipR"], "rotation_euler", fr, (math.radians(leg) * sw * ramp, 0, 0))
        kf(P["neck"], "rotation_euler", fr, (math.radians(55), 0, 0.05 * sw * ramp))
    kf(P["root"], "location", fu, b); kf(P["root"], "rotation_euler", fu - 2, (math.radians(-4), 0, yaw))
    kf(P["root"], "rotation_euler", fu, (0, 0, yaw))
    _arm_key(P, "Left", fu, math.radians(4), math.radians(-6)); _arm_key(P, "Right", fu, math.radians(4), math.radians(6))
    for h in ("hipL", "hipR"): kf(P[h], "rotation_euler", fu, (0, 0, 0))
    kf(P["neck"], "rotation_euler", fu, (0, 0, 0))
    _ST[(id(P), "Left")] = (math.radians(4), math.radians(-6)); _ST[(id(P), "Right")] = (math.radians(4), math.radians(6))
    _ST[(id(P), "neck")] = (0, 0, 0); _ST[(id(P), "chest")] = (0, 0, 0)
    return yaw


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
# Joel 23 Nov 09:13 "too much salt ruins the dish": subtle breathing + slow drift, no high-frequency tremble (it aliased
# against the 2-frame keys and read as flicker).
MOODS = {"calm": (0.7, 0.0, 0.5), "tense": (0.9, 0.0, 0.6), "scared": (1.1, 0.12, 0.7), "still": (0.5, 0.0, 0.3)}


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


def bake_life(step=3):
    """Add breathing, head drift, eye-line darts, weight sway and (scared) tremble ON TOP of every existing key:
    sample each channel, add the signal, write keys every `step` frames inside each life window."""
    import bpy
    for P, f0, f1, mood, seed in _LIFE:
        breath, trem, drift = MOODS[mood]
        chans = [(P["chest"], "rotation_euler", 0, lambda t: math.radians(1.1 * breath) * math.sin(t * 2 * math.pi / (3.6 / breath ** 0.5))),
                 (P["chest"], "rotation_euler", 2, lambda t: math.radians(1.6 * drift) * _noise(t * 0.5, seed + 1)),
                 (P["neck"], "rotation_euler", 0, lambda t: math.radians(2.0 * drift) * _noise(t * 0.6, seed + 2) + math.radians(0.9 * trem) * math.sin(t * 7.0)),
                 (P["neck"], "rotation_euler", 2, lambda t: math.radians(3.5 * drift) * _noise(t * 0.45, seed + 3) + math.radians(1.2 * trem) * math.sin(t * 6.1 + 1)),
                 (P["neck"], "rotation_euler", 1, lambda t: math.radians(1.5 * drift) * _noise(t * 0.35, seed + 4)),
                 (P["Left"], "rotation_euler", 0, lambda t: math.radians(1.4 * breath) * math.sin(t * 2 * math.pi / 3.6 + 0.6) + math.radians(0.8 * trem) * math.sin(t * 6.6)),
                 (P["Right"], "rotation_euler", 0, lambda t: math.radians(1.4 * breath) * math.sin(t * 2 * math.pi / 3.6 + 0.9) + math.radians(0.8 * trem) * math.sin(t * 5.7 + 2))]
        for ob, path, idx, sig in chans:
            fc = _fc(ob, path, idx)
            base = {fr: fc.evaluate(fr) for fr in range(f0, f1 + 1, step)}
            for fr, v in base.items():
                kp = fc.keyframe_points.insert(fr, v + sig(fr / FPS), options={"FAST"})
                kp.interpolation = "BEZIER"
            fc.update()


# ------------------------------------------------------------------ DRAWN SMEAR (from Joel's fight reference, used sparingly)
def smear(name, point_fn, fa, fb, show, width=0.35, col=(1.0, 0.92, 0.82), alpha=0.5, steps=8):
    """A 2D-style motion streak for ONE frame (`show`): a tapered ribbon along the path point_fn(frame) took from fa to fb,
    turned to face the camera. Roblox-fight style, but at most 2-3 per part (salt, not the dish)."""
    import bpy
    sc = bpy.context.scene; cam = sc.camera
    pts = []
    for i in range(steps + 1):
        fr = fa + (fb - fa) * i / steps
        sc.frame_set(int(fr), subframe=fr - int(fr)); bpy.context.view_layer.update(); pts.append(_MV(point_fn()))
    sc.frame_set(show); bpy.context.view_layer.update()
    eye = cam.matrix_world.translation.copy()
    verts, faces = [], []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, steps)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross((eye - p).normalized()).normalized() * width * (0.15 + 0.85 * i / steps) * 0.5   # thin tail -> full head
        verts += [p + side, p - side]
        if i: faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True; P_ = m.node_tree.nodes["Principled BSDF"]
    P_.inputs["Base Color"].default_value = (*col, 1); P_.inputs["Emission Color"].default_value = (*col, 1)
    P_.inputs["Emission Strength"].default_value = 0.6; P_.inputs["Alpha"].default_value = alpha
    me.materials.append(m)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.visible_shadow = False
    for fr, h in ((1, True), (show, False), (show + 1, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=fr)
        o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=fr)
    for fc in _fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
    return o


def check_motion(chars, shots, f_end, parts=("Left", "Right", "neck", "chest"), max_jerk=8.0, quiet=()):
    """POP check: within a shot, an angle channel must not jump in speed from one frame to the next (sudden start/stop).
    jerk = |v(f) - v(f-1)| in degrees/frame. Reports the worst offenders; deliberate quick actions go in quiet=(frames)."""
    import bpy
    cut = set()
    for _, a, b in shots: cut.update((a - 1, a, a + 1, b, b + 1))
    probs = []
    for name, P in chars.items():
        for part in parts:
            for fc in _fcurves(P[part]):
                if fc.data_path != "rotation_euler": continue
                v = [math.degrees(fc.evaluate(f)) for f in range(1, f_end + 1)]
                for f in range(3, f_end - 1):
                    if any(abs(f - c) <= 2 for c in cut) or any(abs(f - q) <= 4 for q in quiet): continue
                    j = abs((v[f] - v[f - 1]) - (v[f - 1] - v[f - 2]))
                    if j > max_jerk: probs.append((round(j, 1), name, part, fc.array_index, f + 1))
    probs.sort(reverse=True)
    print("MOTION CHECK", "OK" if not probs else "%d pops (worst first)" % len(probs))
    for p in probs[:12]: print("    POP %.1f deg/f^2 %s %s[%d] at frame %d" % p)
    return probs
