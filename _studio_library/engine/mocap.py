# mocap.py - MOCAP LAYER: real human motion retargeted onto R6 (story-agnostic). Load AFTER rig2.py + motion.py.
# Clips live in _studio_library/mocap/*.json, built from CMU mocap BVH by _tools/mocap_import.py (free for commercial use;
# credit "Motion data from mocap.cs.cmu.edu (NSF EIA-0196217)" in the video description). Every channel is keyed on EVERY
# frame (no mixed key grids), every window blends in and out of whatever is already keyed (zero-speed ends), so
# check_motion passes and gesture()/look()/lean() before and after keep working.
#   mo_walk(P, f0, f1, [p0, p1, ...], clip="walk")   walk/run along a path: real gait cycle, steps scaled to the path
#                                                     speed, eases in/out, turns into curves, R6 feet kept ON the floor
#                                                     clips: walk, walk_slow, walk_scared, walk_sad, sneak (tiptoe), jog, run
#   mo_clip(P, "wave", fr)                            play a captured action on the upper body, blended in/out
#                                                     clips: wave (left hand), wave_hello (right), shrug, phone (right
#                                                     hand to ear), scared_look, idle (plain, feet planted); mirror=True swaps sides
#   mo_clip(..., mode="add")                          layer only the clip's MOVEMENT on top of the pose that is there
#                                                     (an idle on a seated or leaning pose)
#   mo_list()                                         names, lengths, notes
# Mocap windows already breathe and drift: life() there is optional (bake_life stays subtle on top).
import json, os, math
from mathutils import Euler as _ME, Vector as _MV2

_MO = {}
MO_PARTS = ("chest", "neck", "Left", "Right", "hipL", "hipR")
_SWAP = {"Left": "Right", "Right": "Left", "hipL": "hipR", "hipR": "hipL", "chest": "chest", "neck": "neck"}
ARM_REST = {"Left": (math.radians(4), 0.0, math.radians(-6)), "Right": (math.radians(4), 0.0, math.radians(6))}


def _mo_dirs():
    here = globals().get("LIB", "")
    return [os.path.join(here, "..", "mocap"), "/home/claude/bloxbury/_studio_library/mocap",
            "/workspace/bloxbury/_studio_library/mocap", os.environ.get("MOCAP_DIR", "")]


def mo_load(name):
    if name not in _MO:
        for d in _mo_dirs():
            p = os.path.join(d, name + ".json")
            if d and os.path.exists(p):
                _MO[name] = json.load(open(p)); break
        else:
            raise FileNotFoundError("mocap clip %r not found in %s" % (name, _mo_dirs()))
    return _MO[name]


def mo_list():
    for d in _mo_dirs():
        if d and os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    c = mo_load(f[:-5]); print("%-12s %-5s %4.1f s  %s" % (f[:-5], c["kind"], c["n"] / 24, c["note"]))
            return


def _lerp3(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))


def _smooth01(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (u * (u * 6 - 15) + 10)


def _mo_pose(c, t, mirror=False, cyc=False):
    """Pose (dict part -> euler) at fractional clip frame t (wraps for cycles)."""
    n = c["n"]
    if cyc: t = t % n; i = int(math.floor(t)); j = (i + 1) % n
    else: t = max(0.0, min(n - 1.0, t)); i = int(math.floor(t)); j = min(n - 1, i + 1)
    u = t - i; out = {}
    for p in MO_PARTS:
        a, b = c["ch"][p][i], c["ch"][p][j]; e = _lerp3(a, b, u)
        if mirror: out[_SWAP[p]] = (e[0], -e[1], -e[2])
        else: out[p] = e
    return out


def _mo_root(c, t, cyc=False):
    n = c["n"]; r = c["root"]
    if cyc: t = t % n; i = int(math.floor(t)); j = (i + 1) % n
    else: t = max(0.0, min(n - 1.0, t)); i = int(math.floor(t)); j = min(n - 1, i + 1)
    u = t - i
    return {k: r[k][i] + (r[k][j] - r[k][i]) * u for k in r}


_LEG_CORNERS = [_MV2((x, y, -2.0)) for x in (-0.5, 0.5) for y in (-0.5, 0.5)]


def mo_contact(eL, eR):
    """Root height that puts the lowest corner of the lower R6 leg exactly on the floor (no feet through the floor)."""
    zs = [(_ME(e, "XYZ").to_matrix() @ c).z for e in (eL, eR) for c in _LEG_CORNERS]
    lo = min(zs); k = 0.015                         # soft minimum: no kink when the weight passes foot to foot (<0.03 stud)
    low = lo - k * math.log(sum(math.exp(-(z - lo) / k) for z in zs))
    return -2.0 - low


def _mo_key(P, part, fr, e):
    kf(P[part], "rotation_euler", fr, e)
    if part in ("Left", "Right"): kf(P["grip" + part], "rotation_euler", fr, (-e[0], -e[1], -e[2]))


def _mo_old(P, part, f0, f1):
    return [tuple(_cur(P[part], "rotation_euler", 3, f)) for f in range(f0, f1 + 1)]


def _mo_clear(P, part, f0, f1):
    _clear(P[part], "rotation_euler", f0, f1)
    if part in ("Left", "Right"): _clear(P["grip" + part], "rotation_euler", f0, f1)


def mo_clip(P, name, fr, speed=1.0, t0=0.0, t1=None, mirror=False, parts=("chest", "neck", "Left", "Right"), legs=False,
            blend=8, blend_out=None, weight=1.0, mode="replace", amp=1.0):
    """Play clip `name` from frame fr. speed < 1 = slower. t0/t1 trim the clip (seconds). legs=True also plays the legs
    (weight shifts, small steps in place) with the feet kept on the floor. mode="add": only the clip's movement (minus its
    first pose) is added to what is keyed - e.g. an idle on top of a seated pose. amp scales the movement.
    Blends from the existing keys over `blend` frames and back to them over `blend_out` (0 = hold the clip's last pose
    up to the next key you set). Returns the end frame."""
    c = mo_load(name); fps = c["fps"]
    a = t0 * fps; b = (t1 * fps if t1 is not None else c["n"] - 1)
    n = int(round((b - a) / speed)); f1 = fr + n
    parts = list(parts) + (["hipL", "hipR"] if legs else [])
    old = {p: _mo_old(P, p, fr, f1) for p in parts}
    if blend_out is None:            # the further the clip ends from the pose it hands back to, the longer the hand-back
        pe = _mo_pose(c, b, mirror)
        gap = max(abs(math.degrees(x - y)) for p in parts for x, y in zip(pe[p], old[p][-1])) if mode != "add" else 0
        bo = max(blend, min(n // 2, int(round(gap / 6.0))))
    else: bo = blend_out
    z_old = [_cur(P["root"], "location", 3, f)[2] for f in range(fr, f1 + 1)] if legs else None
    for p in parts: _mo_clear(P, p, fr + 1, f1)
    p0 = _mo_pose(c, a, mirror)
    if mode != "add":                # a clip that starts far from the current pose (mid-gesture) eases in for longer
        gap = max(abs(math.degrees(x - y)) for p in parts for x, y in zip(p0[p], old[p][0]))
        blend = max(blend, min(n // 2, int(round(gap / 6.0))))
    for i in range(n + 1):
        f = fr + i; w = weight * _smooth01(i / max(1, blend))
        if bo > 0: w *= _smooth01((n - i) / bo)
        pose = _mo_pose(c, a + i * speed, mirror)
        cur = {}
        for p in parts:
            tgt = pose[p]
            if mode == "add": tgt = tuple(o + (t - s) * amp for o, t, s in zip(old[p][i], tgt, p0[p]))
            elif amp != 1.0: tgt = tuple(t * amp for t in tgt)
            cur[p] = _lerp3(old[p][i], tgt, w); _mo_key(P, p, f, cur[p])
        if legs:
            lift = mo_contact(cur["hipL"], cur["hipR"]) if mode != "add" else 0.0     # lower foot stays ON the floor
            kf(P["root"], "location", f, z_old[i] + lift, index=2)
    for p in parts: _ST[(id(P), p)] = cur[p] if p not in ("Left", "Right") else (cur[p][0], cur[p][2])
    return f1


# Gait strength per body region (Joel 23 Nov: raw mocap walk "slightly over exaggerated" on a blocky R6): stiff R6 limbs
# read bigger than real ones, so swings are toned down; legs keep most of theirs so steps still match the ground speed.
GAIT_STYLE = {"legs": 0.85, "arms": 0.6, "torso": 0.5, "sway": 0.35}
_REGION = {"hipL": "legs", "hipR": "legs", "Left": "arms", "Right": "arms", "chest": "torso", "neck": "torso"}


def mo_walk(P, f0, f1, pts, clip="walk", z=0.0, accel=0.2, blend=6, phase=0.0, turn=0.25, gain=1.0, end_rest=True, style=None):
    """Walk/run along a polyline from f0 to f1 with a captured gait. Speeds up and slows down at the ends (accel = share
    of the time), the step length/rate adapts to the speed the path needs (sqrt split, so feet barely slide), the body
    turns into curves (turn = smoothing per frame), the clip's own sway/bob rides on top, and the lower foot always sits
    on the floor (z = floor height). end_rest: arrives in a relaxed standing pose (else the gait just fades out).
    Returns the end yaw (radians)."""
    c = mo_load(clip); assert c["kind"] == "cycle", clip + " is not a gait cycle"
    N = c["n"]; D = c["stride"]; v_nat = c["speed"] / 24.0
    pts = [_MV2((p[0], p[1], z)) for p in pts]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; L = sum(seg); n = f1 - f0

    def at_s(sv):
        acc = 0
        for i, sl in enumerate(seg):
            if acc + sl >= sv or i == len(seg) - 1:
                u = (sv - acc) / sl if sl else 0
                return pts[i].lerp(pts[i + 1], min(1, max(0, u))), (pts[i + 1] - pts[i]).normalized()
            acc += sl
    prof = [_smooth01(min(1.0, (i / n) / accel, (1 - i / n) / accel)) for i in range(n + 1)]
    cum = [0.0]
    for k in range(1, n + 1): cum.append(cum[-1] + (prof[k] + prof[k - 1]) / 2)
    v_cruise = L / cum[-1]                                                  # studs per frame at full speed
    r = max(0.4, min(2.5, v_cruise / v_nat))                                 # half the speed change in stride, half in cadence
    amp = max(0.75, min(1.15, r ** 0.5)) * gain
    st = dict(GAIT_STYLE, **c.get("style", {})); st.update(style or {})      # studio default < clip's own < this call
    stride = D * amp * st["legs"]                                           # leg swing scale = stride scale: feet don't slide
    parts = list(MO_PARTS)
    old = {p: _mo_old(P, p, f0, f1) for p in parts}
    for p in parts: _mo_clear(P, p, f0 + 1, f1)
    _clear(P["root"], "location", f0 + 1, f1); _clear(P["root"], "rotation_euler", f0 + 1, f1)
    yaw_prev = _cur(P["root"], "rotation_euler", 3, f0)[2]
    rest = {p: ARM_REST.get(p, (0.0, 0.0, 0.0)) for p in parts}; rows = []
    for i in range(n + 1):
        fr = f0 + i; sv = cum[i] / cum[-1] * L
        p, d = at_s(sv)
        ph = phase * N + sv / stride * N                                 # clip frame from distance -> no sliding
        w = prof[i]                                                            # gait strength follows the speed
        pose = _mo_pose(c, ph, cyc=True); rt = _mo_root(c, ph, cyc=True)
        yaw_t = math.atan2(-d.x, d.y)
        while yaw_t - yaw_prev > math.pi: yaw_t -= 2 * math.pi
        while yaw_t - yaw_prev < -math.pi: yaw_t += 2 * math.pi
        yaw = yaw_prev + (yaw_t - yaw_prev) * turn if i else yaw_prev
        yaw_prev = yaw
        b_in = _smooth01(i / max(1, blend))
        cur = {}
        for q in parts:
            g = tuple(rv + (pv - rv) * amp * st[_REGION[q]] for pv, rv in zip(pose[q], rest[q] if q in ARM_REST else (0, 0, 0)))
            tgt = _lerp3(rest[q] if end_rest or q in ("hipL", "hipR") else old[q][i], g, w)
            cur[q] = _lerp3(old[q][i], tgt, b_in) if i < blend else tgt
            _mo_key(P, q, fr, cur[q])
        perp = _MV2((d.y, -d.x, 0))
        loc = p + perp * rt["lat"] * w * amp * st["sway"]
        flight = max(0.0, rt["z"] - mo_contact(pose["hipL"], pose["hipR"])) * w
        rows.append((fr, loc.x, loc.y, z + mo_contact(cur["hipL"], cur["hipR"]), flight))
        kf(P["root"], "rotation_euler", fr, (0, 0, yaw + rt["yaw"] * w * amp * st["sway"]))
    hz = [r[3] + r[4] for r in rows]   # height = foot contact + flight, smoothed over ~3 frames: the lowest corner switching
    for k, (fr, x, y, _, _) in enumerate(rows):       # from foot to foot on a fast step must not flicker (<0.02 stud dip)
        g = [(j, math.exp(-0.5 * ((j - k) / 1.3) ** 2)) for j in range(max(0, k - 4), min(len(hz), k + 5))]
        kf(P["root"], "location", fr, (x, y, sum(hz[j] * wj for j, wj in g) / sum(wj for _, wj in g)))
    for q in parts: _ST[(id(P), q)] = cur[q] if q not in ("Left", "Right") else (cur[q][0], cur[q][2])
    return yaw_prev
