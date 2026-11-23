# mocap_import.py - BVH mocap -> R6 clip library (_studio_library/mocap/<name>.json). numpy only, no Blender.
# Source: CMU Graphics Lab Motion Capture Database (BVH by B. Hahne, mirrored at github.com/una-dinosauria/cmu-mocap):
#   "free for use in research and commercial projects worldwide" - credit line: "Motion data from mocap.cs.cmu.edu,
#   created with funding from NSF EIA-0196217." Any other BVH with the same joint names (or a NAMES map) works too.
# R6 retarget (see engine/mocap.py for the scene side):
#   root   = pelvis position on the ground plane (studs, scaled by hip height) + pelvis heading (yaw)
#   chest  = upper-spine rotation relative to the heading (R6 waist pivot)     neck = head relative to the chest
#   Left/Right/hipL/hipR = direction shoulder->wrist / hip->ankle as a twist-free swing from "hanging down"
#   root z = keeps the lower R6 foot on the ground (R6 legs have no knees), plus the pelvis rise in flight
# Loops (kind "cycle"): finds the gait period, resamples one cycle to whole 24 fps frames and spreads the seam error.
# Usage: python3 _tools/mocap_import.py <bvh_dir> [clip ...]     (missing CMU files are downloaded into bvh_dir; the BVHs
# are NOT kept in the repo, only the small R6 json clips). New clip: add a CLIPS line (browse cmu-mocap-index-text.txt in the
# mirror; skip each file's first ~0.3 s, it starts in a T-pose), build it, check `check_motion` in a test scene.
import math, json, os, sys
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_studio_library", "mocap")
FPS = 24
# name: (file, start s, end s, kind, notes)  - times in the source clip (seconds at its true speed)
CLIPS = {
    "walk":         ("08_01.bvh", 0.2, 2.3, "cycle", "normal walk (mirrored halves: plain, even)", {"sym": True, "style": {"torso": 0.35, "sway": 0.25}}),
    "walk_slow":    ("91_29.bvh", 4.0, 7.5, "cycle", "relaxed walk"),
    "walk_scared":  ("91_32.bvh", 6.0, 14.0, "cycle", "scared walk: hunched, short slow steps", {"period": (1.8, 2.8)}),
    "walk_sad":     ("91_13.bvh", 6.0, 14.0, "cycle", "sad walk: head down, dragging", {"period": (1.5, 2.4)}),
    "sneak":        ("120_08.bvh", 2.0, 8.0, "cycle", "cartoon tiptoe sneak: knees up, soft careful steps", {"period": (1.4, 2.6), "sym": True, "smooth": 1.3, "lean": 0.5}),
    "jog":          ("16_35.bvh", 0.2, 1.3, "cycle", "jog", {"period": (0.5, 0.9), "smooth": 0.6, "lean": 0.6}),
    "run":          ("16_55.bvh", 0.2, 1.5, "cycle", "run: arms pump high", {"period": (0.45, 0.8), "smooth": 1.4, "lean": 0.45, "sym": True,
                     "scale": {"Left": (1.35, 1, 1), "Right": (1.35, 1, 1)}, "offset": {"Left": (14, 0, 0), "Right": (14, 0, 0)},
                     "style": {"arms": 1.0, "legs": 1.0}}),
    "wave":         ("143_25.bvh", 0.3, 3.15, "clip", "LEFT hand up, friendly wave, ends raised (mirror=True for the right)", {"smooth": 1.3, "rest": False}),
    "wave_hello":   ("141_16.bvh", 0.15, 2.45, "clip", "quick RIGHT-hand hello wave", {"smooth": 0.8}),
    "shrug":        ("141_21.bvh", 0.2, 2.25, "clip", "small shrug, head tilt", {"smooth": 0.8}),
    "phone":        ("79_36.bvh", 0.9, 4.25, "clip", "RIGHT hand lifts a phone to the ear, holds, lowers", {"smooth": 0.8}),
    "scared_look":  ("79_73.bvh", 0.35, 6.2, "clip", "hands up at the chest, glances left/right, then relaxes (toned down for R6)", {"smooth": 1.6,
                     "scale": {"neck": (0.5, 0.5, 0.4), "chest": (0.55, 0.55, 0.5), "Left": (0.7, 0.7, 0.7), "Right": (0.7, 0.7, 0.7)}}),
    "idle":         ("113_21.bvh", 0.8, 11.0, "clip", "plain standing idle: breathing, tiny weight shift, feet planted", {"smooth": 1.5,
                     "centre": ("neck", "chest", "hipL", "hipR"), "scale": {"neck": (0.15, 0.15, 0.12), "chest": (0.6, 0.6, 0.6), "hipL": (0.0, 0.0, 0.0), "hipR": (0.0, 0.0, 0.0)}}),
}
C = np.array([[-1.0, 0, 0], [0, 0, 1.0], [0, 1.0, 0]])     # BVH (x=left, y=up, z=fwd) -> R6 (x=right, y=fwd, z=up)


# ------------------------------------------------------------------ BVH
def parse_bvh(path):
    tok = open(path).read().split()
    joints, stack, i = [], [], 0
    while tok[i] != "MOTION":
        t = tok[i]
        if t in ("ROOT", "JOINT"):
            joints.append({"name": tok[i + 1], "parent": stack[-1] if stack else -1, "chan": [], "end": None}); i += 2
        elif t == "End":
            joints.append({"name": joints[stack[-1]]["name"] + "_End", "parent": stack[-1], "chan": [], "end": True}); i += 2
        elif t == "{": stack.append(len(joints) - 1); i += 1
        elif t == "}": stack.pop(); i += 1
        elif t == "OFFSET": joints[-1]["off"] = np.array([float(x) for x in tok[i + 1:i + 4]]); i += 4
        elif t == "CHANNELS":
            n = int(tok[i + 1]); joints[-1]["chan"] = tok[i + 2:i + 2 + n]; i += 2 + n
        else: i += 1
    nf = int(tok[i + 2]); dt = float(tok[i + 5])
    data = np.array([float(x) for x in tok[i + 6:]]).reshape(nf, -1)
    return joints, data, dt


def _rot(axis, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a); n = len(a)
    R = np.zeros((n, 3, 3)); R[:, 0, 0] = R[:, 1, 1] = R[:, 2, 2] = 1
    i, j = {"X": (1, 2), "Y": (2, 0), "Z": (0, 1)}[axis]
    R[:, i, i] = c; R[:, j, j] = c; R[:, i, j] = -s; R[:, j, i] = s
    return R


def fk(joints, data):
    nf = len(data); col = 0; G, P = [], []
    for j in joints:
        Rl = np.tile(np.eye(3), (nf, 1, 1)); tr = np.zeros((nf, 3))
        for ch in j["chan"]:
            if ch.endswith("position"): tr[:, "XYZ".index(ch[0])] = data[:, col]
            else: Rl = Rl @ _rot(ch[0], data[:, col])
            col += 1
        if j["parent"] < 0: G.append(Rl); P.append(j["off"] + tr)
        else:
            Gp, Pp = G[j["parent"]], P[j["parent"]]
            P.append(Pp + np.einsum("fij,j->fi", Gp, j["off"])); G.append(Gp @ Rl)
    return {j["name"]: (P[k], G[k]) for k, j in enumerate(joints)}


# ------------------------------------------------------------------ maths
def euler_xyz(R):
    """Blender XYZ euler (R = Rz Ry Rx), unwrapped over time."""
    x = np.arctan2(R[:, 2, 1], R[:, 2, 2]); y = np.arcsin(np.clip(-R[:, 2, 0], -1, 1)); z = np.arctan2(R[:, 1, 0], R[:, 0, 0])
    return np.unwrap(np.stack([x, y, z], 1), axis=0)


def from_euler(e):
    return _rot("Z", np.degrees(e[:, 2])) @ _rot("Y", np.degrees(e[:, 1])) @ _rot("X", np.degrees(e[:, 0]))


def swing(d, rest=(0, 0, -1.0)):
    """Twist-free rotation taking `rest` to each unit direction d (n,3)."""
    a = np.array(rest); d = d / np.linalg.norm(d, axis=1, keepdims=True)
    ax = np.cross(np.tile(a, (len(d), 1)), d); s = np.linalg.norm(ax, axis=1); c = d @ a
    ax = np.where(s[:, None] > 1e-6, ax / np.maximum(s, 1e-9)[:, None], np.array([1.0, 0, 0]))
    ang = np.arctan2(s, c); K = np.zeros((len(d), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 2] = -ax[:, 2], ax[:, 1], -ax[:, 0]
    K[:, 1, 0], K[:, 2, 0], K[:, 2, 1] = ax[:, 2], -ax[:, 1], ax[:, 0]
    return np.eye(3) + np.sin(ang)[:, None, None] * K + (1 - np.cos(ang))[:, None, None] * (K @ K)


def limb_rot(d, zmax=0.75, pull=0.03):
    """Rotation that points a hanging R6 limb along d, with a minimal-twist roll carried frame to frame (parallel
    transport of the limb's local X axis), clamped so X never tips past |z| = zmax: the Blender XYZ euler then never nears
    gimbal lock (|y| <= 44 deg) and raised / sideways arms (waves, shrugs) stay smooth. The roll is around the limb's own
    axis, which barely shows on a square R6 arm."""
    d = d / np.linalg.norm(d, axis=1, keepdims=True); Xs = swing(d)[:, :, 0]; X = Xs[0]; out = np.zeros((len(d), 3, 3))
    for i, di in enumerate(d):
        X = X + pull * (Xs[i] - X)                                                 # drift back toward zero roll, slowly
        X = X - di * (X @ di); X /= np.linalg.norm(X)                              # carry the roll over (no twist)
        z0 = zmax - 0.3                                                            # soft clamp past z0: smooth, no kink
        if abs(X[2]) > z0 and abs(di[2]) < 0.999:
            zt = math.copysign(z0 + 0.3 * math.tanh((abs(X[2]) - z0) / 0.3), X[2])
            e1 = np.cross(di, (0, 0, 1.0)); e1 /= np.linalg.norm(e1); e2 = np.cross(e1, di)
            if e2[2] < 0: e2 = -e2
            sz = max(-1.0, min(1.0, zt / max(e2[2], 1e-9))); c = math.copysign(math.sqrt(1 - sz * sz), X @ e1)
            X = c * e1 + sz * e2
        out[i] = np.stack([X, np.cross(-di, X), -di], 1)
    return out


def gauss(x, sigma, axis=0, wrap=False):
    if sigma <= 0: return x
    r = int(math.ceil(sigma * 3)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    x = np.moveaxis(x, axis, 0)
    pad = np.concatenate([x[-r:], x, x[:r]]) if wrap else np.concatenate([np.repeat(x[:1], r, 0), x, np.repeat(x[-1:], r, 0)])
    out = sum(k[i] * pad[i:i + len(x)] for i in range(2 * r + 1))
    return np.moveaxis(out, 0, axis)


def yaw_mat(yaw):
    return _rot("Z", np.degrees(yaw))


def orthonormal(R):
    U, _, Vt = np.linalg.svd(R); D = np.ones((len(R), 3)); D[:, 2] = np.sign(np.linalg.det(U @ Vt))
    return U @ (D[:, :, None] * Vt)


def smooth_rot(R, sigma, wrap=False):
    return orthonormal(gauss(R, sigma, wrap=wrap)) if sigma > 0 else R


def clamp_dir(d, side, kind):
    """No glitch clipping: arms may not swing into the torso unless they are well in front of it; legs never cross."""
    d = d.copy(); inward = 1.0 if side == "L" else -1.0       # R6 left limbs sit at -x: inward is +x
    if kind == "arm": lim = np.clip(d[:, 1] - 0.35, 0, None) * 1.2 + np.clip(d[:, 2] - 0.6, 0, None) * 0.0
    else: lim = np.zeros(len(d))
    i = d[:, 0] * inward; d[:, 0] = np.minimum(i, lim) * inward
    return d / np.linalg.norm(d, axis=1, keepdims=True)


LIMBS = {"Left": ("LeftArm", "LeftHand", "L", "arm", "LeftForeArm"), "Right": ("RightArm", "RightHand", "R", "arm", "RightForeArm"),
         "hipL": ("LeftUpLeg", "LeftFoot", "L", "leg", None), "hipR": ("RightUpLeg", "RightFoot", "R", "leg", None)}


def retarget(path, sigma_out=0.6, arm_mix=0.0):
    """arm_mix: 0 = the R6 arm points shoulder->wrist (gestures: the hand goes where the hand went), 1 = along the upper
    arm (locomotion: a real pendulum swing instead of bent-elbow pumping forward only).
    Whole file -> dict of per-source-frame arrays in R6 space (rotation matrices + root), already anti-aliased."""
    J, D, dt = parse_bvh(path); W = fk(J, D); n = len(D)
    rest = fk(J, np.zeros((1, D.shape[1])))
    feet = [k for k in ("LeftToeBase_End", "LeftToeBase", "LeftFoot") if k in rest]
    hip_h = rest["Hips"][0][0, 1] - rest[feet[0]][0][0, 1]
    scale = 2.0 / hip_h                                      # R6 hip pivot is 2 studs above the soles
    sig = sigma_out * (1.0 / dt) / FPS                       # smoothing in source frames (anti-alias for 24 fps)
    cv = lambda v: v @ C.T                                   # positions / directions (n,3) -> R6 axes
    cr = lambda R: C @ R @ C.T
    Rh = cr(W["Hips"][1]); fwd = Rh[:, :, 1]
    yaw = np.unwrap(np.arctan2(-fwd[:, 0], fwd[:, 1])); yaw = gauss(yaw, sig * 2.5)
    Y = yaw_mat(yaw)
    spine = "Spine1" if "Spine1" in W else "Spine"
    Rc_w = smooth_rot(cr(W[spine][1]), sig); Rc = np.transpose(Y, (0, 2, 1)) @ Rc_w
    Rn = np.transpose(Rc_w, (0, 2, 1)) @ smooth_rot(cr(W["Head"][1]), sig)
    out = {"chest": Rc, "neck": Rn}
    for part, (a, b, side, kind, el) in LIMBS.items():
        d = W[b][0] - W[a][0]; d = d / np.linalg.norm(d, axis=1, keepdims=True)
        if el and arm_mix > 0:
            de = W[el][0] - W[a][0]; d = (1 - arm_mix) * d + arm_mix * de / np.linalg.norm(de, axis=1, keepdims=True)
        d = gauss(cv(d), sig)
        frame = Rc_w if kind == "arm" else Y
        d = np.einsum("fji,fj->fi", frame, d)                 # world -> chest (arms) / heading (legs) space
        out[part] = limb_rot(clamp_dir(d / np.linalg.norm(d, axis=1, keepdims=True), side, kind))
    hp = cv(W["Hips"][0]) * scale
    ground = np.percentile(np.minimum(W[feet[-1]][0][:, 1], W["RightFoot"][0][:, 1]), 2) if "RightFoot" in W else 0
    lf = (W["LeftFoot"][0][:, 1] - ground) * scale; rf = (W["RightFoot"][0][:, 1] - ground) * scale
    foot0 = np.percentile(np.minimum(lf, rf), 5)
    out["flight"] = gauss(np.clip(np.minimum(lf, rf) - foot0 - 0.12, 0, None), sig)   # both feet off the floor
    out["xy"] = gauss(hp[:, :2], sig); out["yaw"] = yaw
    return out, dt, n


def contact_z(Rl, Rr):
    """Root height that keeps the lowest corner of the lower R6 leg ON the floor (legs 1x1x2 hanging from z=2)."""
    cs = np.array([[x, y, -2.0] for x in (-0.5, 0.5) for y in (-0.5, 0.5)])
    low = np.minimum((Rl @ cs.T)[:, 2, :].min(1), (Rr @ cs.T)[:, 2, :].min(1))
    return -2.0 - low


def sample(arr, t):
    """Linear sample of a per-source-frame array at fractional frames t."""
    t = np.clip(t, 0, len(arr) - 1.000001); i = np.floor(t).astype(int); u = (t - i).reshape((-1,) + (1,) * (arr.ndim - 1))
    return arr[i] * (1 - u) + arr[i + 1] * u


def rest_calibrate(e, k=6, reach=70.0):
    """Actors hang their arms a little forward / out (wrists by the thighs); on a blocky R6 that reads as arms sticking
    out. Measure the clip's relaxed arm (its last k frames), rotate that to hanging straight down, and fade the correction
    out as the arm moves away from it (raised, reaching arms keep their real direction)."""
    R = from_euler(e); d = -R[:, :, 2]; dr = d[-k:].mean(0); dr /= np.linalg.norm(dr)
    ax = np.cross(dr, (0, 0, -1.0)); sa = np.linalg.norm(ax)
    if sa < 1e-4: return e
    ax /= sa; full = math.atan2(sa, dr @ np.array([0, 0, -1.0]))
    ang = np.degrees(np.arccos(np.clip(d @ dr, -1, 1))); w = np.clip(1 - ang / reach, 0, 1); w = w * w * (3 - 2 * w)
    out = []
    for di, wi in zip(d, w):
        a = full * wi; c, s_ = math.cos(a), math.sin(a)
        out.append(di * c + np.cross(ax, di) * s_ + ax * (ax @ di) * (1 - c))
    return euler_xyz(limb_rot(np.array(out)))


PARTS = ("chest", "neck", "Left", "Right", "hipL", "hipR")


def feat(o):
    return np.concatenate([o[p][:, :, 2] for p in ("Left", "Right", "hipL", "hipR")] + [o[p][:, :, 1] for p in ("chest",)], 1)


def find_cycle(o, dt, a, b, pmin, pmax):
    """Best gait period inside [a, b) source frames: pose + velocity match between t and t+P."""
    F = feat(o); Vv = np.gradient(F, axis=0) * 8; best = None
    for P in range(int(pmin / dt), int(pmax / dt) + 1):
        for t in range(a, b - P, 2):
            c = np.sum((F[t] - F[t + P]) ** 2) + np.sum((Vv[t] - Vv[t + P]) ** 2)
            if best is None or c < best[0]: best = (c, t, P)
    return best


MIRROR = "https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/%03d/%s"


def fetch(f, bvh_dir):
    p = os.path.join(bvh_dir, f)
    if not os.path.exists(p):
        import urllib.request
        os.makedirs(bvh_dir, exist_ok=True)
        urllib.request.urlretrieve(MIRROR % (int(f.split("_")[0]), f), p)
    return p


def build(name, bvh_dir):
    f, t0, t1, kind, note = CLIPS[name][:5]; opt = CLIPS[name][5] if len(CLIPS[name]) > 5 else {}
    fetch(f, bvh_dir)
    o, dt, n = retarget(os.path.join(bvh_dir, f), arm_mix=opt.get("arm_mix", 0.6 if kind == "cycle" else 0.0))
    a, b = int(t0 / dt), min(n - 1, int(t1 / dt))
    res = {"name": name, "kind": kind, "fps": FPS, "note": note, "source": "CMU mocap " + f.replace(".bvh", ""),
           "credit": "Motion data from mocap.cs.cmu.edu (NSF EIA-0196217)"}
    if kind == "cycle":
        c, a, P = find_cycle(o, dt, a, b, *opt.get("period", (0.8, 1.5)))
        N = max(8, int(round(P * dt * FPS)))
        if opt.get("sym"): N += N % 2                                  # mirrored half-cycles need an even length
        ts = a + np.arange(N + 1) * P / N
        res.update(period_src=P * dt, seam_cost=round(float(c), 4))
    else:
        N = int(round((b - a) * dt * FPS)); ts = a + np.arange(N + 1) / (FPS * dt)
    ch = {}
    for p in PARTS:
        e = euler_xyz(sample(o[p], ts))
        if kind == "cycle":
            e = e - np.outer(np.arange(N + 1) / N, e[-1] - e[0])      # spread the seam error over the cycle
            e = gauss(e[:-1], opt.get("smooth", 0.0), wrap=True)
            if p in ("chest", "neck"): e[:, 1:] -= e[:, 1:].mean(0)    # no constant side tilt / twist in a loop
            if p in ("hipL", "hipR"): e[:, 0] -= e[:, 0].mean() * opt.get("leg_recentre", 0.5)   # rigid R6 legs: swing around the hip
        else: e = gauss(e, opt.get("smooth", 0.0))
        ch[p] = e
    SW = {"Left": "Right", "Right": "Left", "hipL": "hipR", "hipR": "hipL", "chest": "chest", "neck": "neck"}
    if kind == "cycle" and opt.get("sym"):     # left step = mirrored right step: an even, plain gait (no limp, no lean)
        h = N // 2; M = np.array([1.0, -1.0, -1.0])
        ch = {p: 0.5 * (ch[p] + np.roll(ch[SW[p]], -h, 0) * M) for p in PARTS}
    for p in opt.get("scale", {}):            # per-channel movement scale, e.g. {"Left": (1.4, 1, 1)}: around the cycle mean,
        m = ch[p].mean(0) if kind == "cycle" else ch[p][:6].mean(0)     # or around a clip's start pose (it still starts there)
        ch[p] = m + (ch[p] - m) * np.array(opt["scale"][p])
    for p in opt.get("centre", ()): ch[p] = ch[p] - ch[p].mean(0)          # no constant head turn / tilt (plain idle)
    for p, off in opt.get("offset", {}).items(): ch[p] = ch[p] + np.radians(off)   # degrees added to a channel
    if kind == "clip" and opt.get("rest", True):
        for p in ("Left", "Right"): ch[p] = rest_calibrate(ch[p], opt.get("rest_frames", 6))
    k = opt.get("lean", 1.0)                                  # torso pitch scale; the head keeps its world angle
    if k != 1.0:
        dx = ch["chest"][:, 0] * (1 - k); ch["chest"][:, 0] -= dx; ch["neck"][:, 0] += dx
    Rl, Rr = from_euler(ch["hipL"]), from_euler(ch["hipR"])
    z = contact_z(Rl, Rr) + sample(o["flight"], ts[:len(ch["hipL"])])
    xy = sample(o["xy"], ts); yaw = sample(o["yaw"], ts)
    if kind == "cycle":
        d = xy[-1] - xy[0]; D = float(np.linalg.norm(d)); u = d / D; perp = np.array([u[1], -u[0]])
        line_yaw = math.atan2(-u[0], u[1]); rel = xy - xy[0]
        s_ = rel @ u; lat = rel @ perp; lat = lat - np.arange(N + 1) / N * lat[-1]
        yr = yaw - line_yaw; yr = yr - np.arange(N + 1) / N * (yr[-1] - yr[0])
        yr = (yr + np.pi) % (2 * np.pi) - np.pi; yr = yr - yr[:-1].mean()   # heading relative to travel: no 360 wraps, no constant turn
        lat = lat - lat[:-1].mean()
        if opt.get("sym"):
            h = N // 2; lat[:-1] = 0.5 * (lat[:-1] - np.roll(lat[:-1], -h)); yr[:-1] = 0.5 * (yr[:-1] - np.roll(yr[:-1], -h))
        res.update(stride=round(D, 4), speed=round(D / (P * dt), 4),
                   root={"s": s_[:-1].round(4).tolist(), "lat": lat[:-1].round(4).tolist(), "z": z.round(4).tolist(),
                         "yaw": yr[:-1].round(4).tolist()})
    else:
        Y0 = yaw[0]; c0, s0 = math.cos(-Y0), math.sin(-Y0); rel = xy - xy[0]
        rx = rel[:, 0] * c0 - rel[:, 1] * s0; ry = rel[:, 0] * s0 + rel[:, 1] * c0
        res.update(root={"x": rx.round(4).tolist(), "y": ry.round(4).tolist(), "z": z.round(4).tolist(), "yaw": (yaw - Y0).round(4).tolist()})
    if opt.get("style"): res["style"] = opt["style"]                  # per-clip GAIT_STYLE override (engine/mocap.py)
    res["n"] = len(ch["chest"])
    res["ch"] = {p: ch[p].round(4).tolist() for p in PARTS}
    return res


if __name__ == "__main__":
    src = sys.argv[1]; names = sys.argv[2:] or list(CLIPS)
    os.makedirs(OUT, exist_ok=True)
    for nm in names:
        r = build(nm, src)
        json.dump(r, open(os.path.join(OUT, nm + ".json"), "w"), separators=(",", ":"))
        print("%-14s %-6s %3d frames %s" % (nm, r["kind"], r["n"], ("stride %.2f studs, %.2f studs/s, seam %.3f" % (r["stride"], r["speed"], r["seam_cost"])) if r["kind"] == "cycle" else ""))
