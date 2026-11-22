# director.py - shot checker for Bloxbury scene scripts (runs in the workspace, no rendering, ~seconds per shot).
# Load at the end of a scene script, after SHOTS / cam are built:
#     exec(open(SCR + "director.py").read()); shot_probs = check_shots(SHOTS)
# For every shot it samples the start, middle and end frame and flags:
#   INSIDE   - the camera sits inside a mesh (most rays from the lens hit back faces: inside a head, wall, hill)
#   BLOCKED  - something sits between the lens and the aim point (the subject is hidden behind a wall/door/person)
#   LENS     - a big chunk of the frame is covered by something closer than 0.5 studs (shoulder/prop on the lens)
# Hidden objects, glossy-only reflections and holdouts are skipped, so it sees what the camera sees.
import bpy
from mathutils import Vector


def _visible_to_camera(o, fr):
    if o is None:
        return False
    if o.hide_render or not getattr(o, "visible_camera", True):
        return False
    p = o.parent
    while p is not None:                      # a hidden parent hides the child in our rigs
        if p.hide_render:
            return False
        p = p.parent
    return True


SEE_THROUGH = ("Glass", "Window", "Mirror")      # we aim THROUGH these on purpose (mirror shots, window shots)


def _root(o):
    while o.parent is not None:
        o = o.parent
    return o


def _all_hits(scene, dg, origin, d, fr, max_d):
    """Every camera-visible hit along d up to max_d: [(distance, obj)]."""
    out, o, travelled = [], Vector(origin), 0.0
    for _ in range(40):
        hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, o, d, distance=max_d - travelled)
        if not hit:
            break
        dist = travelled + (loc - o).length
        if "Mirror" in obj.name and _visible_to_camera(obj, fr):
            out.append((dist, obj)); break          # aiming into a mirror: the reflection is the subject, stop here
        if _visible_to_camera(obj, fr) and not any(k in obj.name for k in SEE_THROUGH):
            out.append((dist, obj))
        travelled = dist + 1e-3
        o = loc + d * 1e-3
    return out


def _cast(scene, dg, origin, d, fr, max_d=3000.0):
    """First camera-visible hit along d: (distance, obj, normal) or None. Steps past hidden/glossy-only objects."""
    o, travelled = Vector(origin), 0.0
    for _ in range(12):
        hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, o, d, distance=max_d - travelled)
        if not hit:
            return None
        dist = travelled + (loc - o).length
        if _visible_to_camera(obj, fr):
            return dist, obj, nrm
        travelled = dist + 1e-3
        o = loc + d * 1e-3
    return None


def _frame_dirs(cam, scene, n=5):
    """n x n ray directions across the camera frame (world space)."""
    fr = cam.data.view_frame(scene=scene)            # 4 corners in camera space at z=-1-ish
    xs = [v.x for v in fr]; ys = [v.y for v in fr]; z = fr[0].z
    m = cam.matrix_world.to_3x3()
    out = []
    for i in range(n):
        for j in range(n):
            x = min(xs) + (max(xs) - min(xs)) * (i + 0.5) / n
            y = min(ys) + (max(ys) - min(ys)) * (j + 0.5) / n
            out.append((m @ Vector((x, y, z))).normalized())
    return out


def check_shots(shots, cam=None, near=0.5, lens_frac=0.25, allow=(), verbose=True):
    """allow: shot names (or parts of names) where a blocker is the point, e.g. the Knocker lunging at the lens."""
    scene = bpy.context.scene
    cam = cam or scene.camera
    probs = []
    six = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    for name, f0, f1 in shots:
        if "black" in name.lower():                   # deliberate black frames
            continue
        if any(a in name for a in allow):
            continue
        for fr in sorted({f0, (f0 + f1) // 2, f1}):
            scene.frame_set(fr)
            dg = bpy.context.evaluated_depsgraph_get()
            P = cam.matrix_world.translation.copy()
            fwd = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            # INSIDE: rays in 6 directions; a back-face hit (normal pointing away from us) means we are inside that mesh
            inside = {}
            for d in six:
                h = _cast(scene, dg, P, d, fr, 60)
                if h and h[2].dot(d) > 0:
                    inside[h[1].name] = inside.get(h[1].name, 0) + 1
            for oname, c in inside.items():
                if c >= 4:
                    probs.append(("INSIDE", name, fr, oname))
            # BLOCKED: the aim point is at the focus distance (cam_key sets it to |target - camera|)
            focus = cam.data.dof.focus_distance
            hits = _all_hits(scene, dg, P, fwd, fr, focus + 2.5)
            if hits and near < hits[0][0] < focus - 1.6 and "Mirror" not in hits[0][1].name:
                near_aim = [x for x in hits if abs(x[0] - focus) < 2.5]
                subj = min(near_aim, key=lambda x: abs(x[0] - focus))[1] if near_aim else None   # what sits at the aim point
                if subj is None or _root(hits[0][1]) is not _root(subj):  # the subject's own arm/hair in front is fine
                    probs.append(("BLOCKED", name, fr, "%s (%s) at %.1f of %.1f studs, in front of %s" % (
                        hits[0][1].name, _root(hits[0][1]).name, hits[0][0], focus, _root(subj).name if subj else "the aim point")))
            # LENS: a big part of the frame covered by something right on the lens
            dirs = _frame_dirs(cam, scene)
            close = {}
            for d in dirs:
                hh = _cast(scene, dg, P, d, fr, near)
                if hh:
                    close[hh[1].name] = close.get(hh[1].name, 0) + 1
            tot = sum(close.values())
            if tot / len(dirs) >= lens_frac:
                probs.append(("LENS", name, fr, "%d%% of frame within %.1f studs: %s" % (
                    100 * tot // len(dirs), near, ", ".join(sorted(close, key=close.get, reverse=True)[:3]))))
    if verbose:
        print("SHOT CHECK", "OK (%d shots)" % len(shots) if not probs else "%d problems" % len(probs))
        for p in probs:
            print("   ", *p)
    return probs


def render_quality(s, mode="fast"):
    """Cycles light-path settings. "full" = Blender defaults (Parts 1-2). "fast" = trimmed for Roblox-style scenes:
    plastic surfaces, no glass/caustics, so extra bounces and a tight noise threshold cost time but don't show.
    The mirror shots still work (glossy 2 = mirror + one bounce inside it)."""
    c = s.cycles
    if mode == "full":
        return
    c.use_adaptive_sampling = True; c.adaptive_threshold = 0.04; c.adaptive_min_samples = 8
    c.max_bounces = 6; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 2
    c.transparent_max_bounces = 8; c.volume_bounces = 0
    c.caustics_reflective = False; c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    try: c.use_light_tree = True
    except AttributeError: pass
    if mode == "turbo":                    # one bounce of bounce-light: flatter shadows in corners, ~fastest
        c.adaptive_threshold = 0.06; c.max_bounces = 4; c.diffuse_bounces = 1; c.glossy_bounces = 1
    print("RENDER QUALITY", mode)
