# render_cache.py - re-render ONLY the frames a story tweak changed, then splice them into the last render.
# Story-agnostic: works on any part script built on scene_kit.py (finish_part() with RENDER unset builds, checks, stops).
#
# How it knows what changed: it builds the scene and gives every frame a KEY = hash of everything that frame's render
# depends on: render settings (RX RY SAMPLES ENGINE QUALITY PLAYBLAST, colour management, compositor, world), the camera
# (matrix, lens, DOF), and every render-visible object near the camera (mesh, modifiers, materials + node values,
# images, its world matrix and every animated value on it, its data, shape keys and materials). Motion blur reads the
# next frame too, so a frame's key also covers frame+1. The cache keeps the keys of the frames already rendered into
# the part's MASTER (video-only, near-lossless). A new frame whose key exists anywhere in the master is reused, even if
# a tweak shifted it in time (only when the frame is truly identical); only frames with a new key are rendered.
#
#   cd /home/claude/bloxbury-blender
#   RX=1080 RY=1920 SAMPLES=32 ENGINE=GPU python3 <repo>/_tools/render_cache.py plan part3.py
#        -> builds, writes <cache>/p3.next.json, prints the changed frames per shot, RANGES=..., GPU time and cost
#   pod:    sh pod_patch.sh part3.py "<RANGES>"   -> /workspace/patch_p3.mp4 + patch_p3.json (only the changed frames)
#   local:  RENDER=1 OUT=dir RANGES="<RANGES>" RX.. python3 part3.py                -> dir/NNNN.png
#   python3 render_cache.py splice p3 --new <patch_p3.mp4 | frames dir> [--out Bloxbury_Part3.mp4 --audio a --captions c]
#        -> new master (reused frames + new frames) -> final mp4 via make_part.sh; the cache moves to the new keys
#   python3 render_cache.py accept p3 --master <frames dir | video>   after a FULL render (pod_finish.sh makes
#        <output>_master.mp4): stores that render as the cache, keys from the last plan (same settings).
#
# Cache: <repo>/stories/<story>/render_cache/ (STORY env or --story, default bloxbury): <part>.json (keys of the master,
# small, kept in git), <part>.next.json (keys of the scene as it is now), <part>_master.mp4 (laptop only, *.mp4 is
# gitignored).
# What counts for a frame: lights always; objects inside the view (widened 30%, CULL_WIDE), off-screen objects that are
# big or close enough to change its light or shadows (angular radius > CULL_ANG 0.15, or within CULL_NEAR 1 m), never
# anything over CULL_R (120 m) away. A mirror/chrome surface in view switches the view test off for that frame.
# CULL_VIEW=0 -> distance only, CULL_R=0 -> no limit (slowest, every change re-renders every frame it is visible in).
import sys, os, json, hashlib, subprocess, time, argparse, shutil

REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
SETTINGS_ENV = ("RX", "RY", "SAMPLES", "ENGINE", "QUALITY", "PLAYBLAST", "LOOK")
DEFAULTS = {"RX": "216", "RY": "384", "ENGINE": "CPU", "QUALITY": "fast"}
GPU_S_PER_FRAME = 1.5          # one RTX 4090 at 1080x1920, 32 samples (CLAUDE.md); scaled by pixels x samples
SECURE_4090 = 0.89             # $/hr


def cache_dir(story):
    d = os.environ.get("RENDER_CACHE") or os.path.join(REPO, "stories", story, "render_cache")
    os.makedirs(d, exist_ok=True); return d


def ranges(frames):
    """[1,2,3,7,9,10] -> '1-3,7,9-10'"""
    out = []; frames = sorted(frames)
    i = 0
    while i < len(frames):
        j = i
        while j + 1 < len(frames) and frames[j + 1] == frames[j] + 1: j += 1
        out.append(str(frames[i]) if i == j else "%d-%d" % (frames[i], frames[j])); i = j + 1
    return ",".join(out)


def settings_now():
    s = {k: os.environ.get(k, DEFAULTS.get(k, "")) for k in SETTINGS_ENV}
    if not s.get("SAMPLES"): s["SAMPLES"] = "32" if s["ENGINE"] == "GPU" else "6"
    return s


# ====================================================================== hashing (inside bpy)
def build_keys(script):
    import io, contextlib
    import numpy as np
    os.environ.pop("RENDER", None)
    g = {"__name__": "__main__", "__file__": script}
    log = io.StringIO()
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(log):
            exec(compile(open(script).read(), script, "exec"), g)
    except SystemExit as e:
        print(log.getvalue()[-3000:]); raise SystemExit("build stopped (%s): fix the scene first" % e)
    import bpy
    from mathutils import Vector
    s = bpy.context.scene
    print("built %s in %.0f s" % (script, time.time() - t0))
    t0 = time.time()

    def H(*a):
        return hashlib.md5(json.dumps(a, sort_keys=True, default=str).encode()).hexdigest()

    def R(v, n=4):
        return round(float(v), n) + 0.0

    SKIP = {"rna_type", "name", "name_full", "original", "users", "session_uid", "is_evaluated", "tag", "is_runtime_data"}

    def rna(st, depth=0):
        """every simple property of an RNA struct (ints, floats, enums, strings, ID pointers by name), recursing a little."""
        out = {}
        if st is None: return None
        for p in st.bl_rna.properties:
            k = p.identifier
            if k in SKIP: continue
            try: v = getattr(st, k)
            except Exception: continue
            if p.type in ("BOOLEAN", "INT", "FLOAT"):
                if getattr(p, "is_array", False) or (hasattr(v, "__len__") and not isinstance(v, str)):
                    try: v = [R(x) if isinstance(x, float) else (list(x) if hasattr(x, "__len__") else x) for x in v]
                    except TypeError: v = str(v)
                elif isinstance(v, float): v = R(v)
                out[k] = v
            elif p.type in ("ENUM", "STRING"):
                out[k] = sorted(v) if isinstance(v, set) else v
            elif p.type == "POINTER":
                if isinstance(v, bpy.types.ID): out[k] = v.name
                elif v is not None and depth < 2: out[k] = rna(v, depth + 1)
        return out

    img_cache = {}

    def img_hash(im):
        if im.name in img_cache: return img_cache[im.name]
        h = None
        try:
            if im.packed_file is None and im.filepath and os.path.exists(bpy.path.abspath(im.filepath)):
                h = hashlib.md5(open(bpy.path.abspath(im.filepath), "rb").read()).hexdigest()
            elif im.size[0] * im.size[1] > 0:
                a = np.empty(im.size[0] * im.size[1] * im.channels, dtype=np.float32); im.pixels.foreach_get(a)
                h = hashlib.md5(np.round(a, 3).tobytes()).hexdigest()
        except Exception as e: h = "err:%s" % e
        img_cache[im.name] = h = H(im.name, list(im.size), im.source, h, im.colorspace_settings.name)
        return h

    tree_cache = {}

    def tree_hash(nt):
        if nt is None: return None
        if nt.name in tree_cache: return tree_cache[nt.name]
        tree_cache[nt.name] = "loop"
        nodes = []
        for n in nt.nodes:
            d = {"id": n.bl_idname, "n": n.name, "p": rna(n)}
            d["in"] = [[i.identifier, i.is_linked, None if i.is_linked or not hasattr(i, "default_value") else
                        (R(i.default_value) if isinstance(i.default_value, float) else
                         [R(x) for x in i.default_value] if hasattr(i.default_value, "__len__") and not isinstance(i.default_value, str)
                         else str(i.default_value))] for i in n.inputs]
            if getattr(n, "image", None): d["img"] = img_hash(n.image)
            if getattr(n, "node_tree", None): d["grp"] = tree_hash(n.node_tree)
            if getattr(n, "color_ramp", None): d["ramp"] = [[R(e.position), [R(c) for c in e.color]] for e in n.color_ramp.elements]
            if getattr(n, "mapping", None):
                try: d["curve"] = [[[R(p.location[0]), R(p.location[1])] for p in c.points] for c in n.mapping.curves]
                except Exception: pass
            nodes.append(d)
        links = sorted([l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier] for l in nt.links)
        tree_cache[nt.name] = h = H(sorted(nodes, key=lambda d: d["n"]), links)
        return h

    mat_cache = {}

    def mat_hash(m):
        if m is None: return None
        if m.name not in mat_cache:
            mat_cache[m.name] = H(rna(m), tree_hash(m.node_tree) if m.use_nodes else None)
        return mat_cache[m.name]

    P3 = np.array([1000003, 998244353, 1000000007], dtype=np.int64)

    def q(a):                         # quantise to 0.1 mm (int64) so float noise never changes a hash
        return np.round(np.asarray(a, dtype=np.float64) * 1e4).astype(np.int64)

    def mesh_hash(d):
        """order-free: builds can number the same faces/loops differently (Python set order), the render is the same.
        Every face -> sum over its loops of mix(this corner, next corner, uv) (keeps winding), + material + smooth;
        the mesh = the sorted list of face values."""
        nv, nl, npl = len(d.vertices), len(d.loops), len(d.polygons)
        if not npl: return "empty%d" % nv
        co = np.empty(nv * 3, dtype=np.float32); d.vertices.foreach_get("co", co); C = q(co).reshape(-1, 3) @ P3
        lv = np.empty(nl, dtype=np.int32); d.loops.foreach_get("vertex_index", lv)
        ls = np.empty(npl, dtype=np.int32); d.polygons.foreach_get("loop_start", ls)
        lt = np.empty(npl, dtype=np.int32); d.polygons.foreach_get("loop_total", lt)
        mi = np.empty(npl, dtype=np.int32); d.polygons.foreach_get("material_index", mi)
        sm = np.empty(npl, dtype=bool); d.polygons.foreach_get("use_smooth", sm)
        start = np.repeat(ls, lt); idx = np.arange(nl); nxt = start + (idx - start + 1) % np.repeat(lt, lt)
        a, b = C[lv], C[lv[nxt]]
        hl = a * 6364136223846793005 + b * 1442695040888963407 + (a ^ (b >> 7)) * 2862933555777941757
        for L in d.uv_layers[:2]:
            uv = np.empty(nl * 2, dtype=np.float32); L.data.foreach_get("uv", uv); U = q(uv).reshape(-1, 2) @ P3[:2]
            hl = hl + U * 3935559000370003845 + U[nxt] * 2685821657736338717
        hf = np.add.reduceat(hl, ls) + mi.astype(np.int64) * 7046029254386353131 + sm.astype(np.int64) * 3202034522624059733
        return hashlib.md5(np.sort(hf).tobytes()).hexdigest()

    def is_mirror(m):
        """sharp reflections (mirror glass, chrome): they show what's outside the view"""
        if not m.node_tree: return False
        for n in m.node_tree.nodes:
            def v(k):
                i = n.inputs.get(k)
                return None if i is None or i.is_linked else i.default_value
            rough = v("Roughness")
            if n.bl_idname == "ShaderNodeBsdfPrincipled" and (v("Metallic") or 0) > 0.5 and rough is not None and rough < 0.15: return True
            if n.bl_idname in ("ShaderNodeBsdfGlossy", "ShaderNodeBsdfAnisotropic", "ShaderNodeBsdfMetallic") and rough is not None and rough < 0.15: return True
        return False

    data_cache = {}

    def data_hash(o):
        d = o.data
        if d is None: return None
        key = (type(d).__name__, d.name)
        if key in data_cache: return data_cache[key]
        if o.type == "MESH":
            h = mesh_hash(d)
            sk = None
            if d.shape_keys:
                sk = []
                for k in d.shape_keys.key_blocks:
                    a = np.empty(len(k.data) * 3, dtype=np.float32); k.data.foreach_get("co", a)
                    sk.append([k.name, hashlib.md5(np.sort(q(a).reshape(-1, 3) @ P3).tobytes()).hexdigest()])
            h = H(h, sk, [mat_hash(m) for m in d.materials])
        else:
            extra = getattr(d, "body", None)
            h = H(rna(d), extra, [mat_hash(m) for m in getattr(d, "materials", [])])
        data_cache[key] = h
        return h

    def fcurves(idb):
        ad = getattr(idb, "animation_data", None)
        if not ad or not ad.action: return []
        act = ad.action; cs = []
        try: cs = list(act.fcurves)
        except Exception: pass
        if not cs:
            try:
                for l in act.layers:
                    for st in l.strips:
                        for cb in st.channelbags: cs += list(cb.fcurves)
            except Exception: pass
        return sorted(cs, key=lambda c: (c.data_path, c.array_index))

    def has_drivers(idb):
        ad = getattr(idb, "animation_data", None)
        return bool(ad and len(ad.drivers))

    # ---------------------------------------------------------------- per object: static hash, animated channels
    objs = [o for o in s.objects if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META", "LIGHT", "VOLUME", "POINTCLOUD", "CURVES")]
    info = []
    for o in objs:
        ids = [o, o.data] + ([o.data.shape_keys] if o.type == "MESH" and o.data.shape_keys else [])
        mats = [sl.material for sl in o.material_slots if sl.material]
        ids += mats + [m.node_tree for m in mats if m.node_tree]
        fcs = [c for i in ids if i is not None for c in fcurves(i)]
        anim = bool(fcs) or any(has_drivers(i) for i in ids if i is not None) or bool(o.constraints)
        p = o.parent
        while p is not None and not anim:
            anim = bool(fcurves(p)) or bool(p.constraints) or has_drivers(p); p = p.parent
        st = H(o.type, data_hash(o), [mat_hash(m) for m in mats], [sl.link for sl in o.material_slots],
               [rna(m) for m in o.modifiers], rna(getattr(o, "cycles", None)),
               [getattr(o, a, None) for a in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission",
                                              "visible_volume_scatter", "visible_shadow", "is_holdout", "is_shadow_catcher")])
        bb = np.array([v[:] for v in o.bound_box], dtype=np.float64)
        c = bb.mean(0); r = float(np.linalg.norm(bb - c, axis=1).max())
        info.append({"o": o, "st": st, "fcs": fcs, "anim": anim, "c": c, "r": r, "light": o.type == "LIGHT",
                     "mirror": any(is_mirror(m) for m in mats)})
    dyn = [i for i in info if i["anim"]]
    sta = [i for i in info if not i["anim"]]
    # static objects: one 64-bit number each (hash incl. its fixed matrix + visibility); summed per frame over the
    # ones near the camera (vectorised)
    s.frame_set(s.frame_start)
    st_num = np.array([int(H(i["st"], [R(x) for row in i["o"].matrix_world for x in row], i["o"].hide_render)[:15], 16) for i in sta], dtype=np.int64)
    st_c = np.array([(i["o"].matrix_world @ Vector(i["c"]))[:] for i in sta]).reshape(-1, 3)
    st_r = np.array([i["r"] * max(i["o"].matrix_world.to_scale()) for i in sta])
    st_on = np.array([not i["o"].hide_render for i in sta], dtype=bool)
    st_light = np.array([i["light"] for i in sta], dtype=bool)
    st_mirror = np.array([i["mirror"] for i in sta], dtype=bool)
    cam_fcs = []
    for cam in {o for o in s.objects if o.type == "CAMERA"}:
        cam_fcs += fcurves(cam) + fcurves(cam.data)

    vl = s.view_layers[0]
    G = H(settings_now(), bpy.app.version_string, s.render.fps, rna(s.render), rna(s.cycles), rna(s.view_settings),
          rna(s.display_settings), rna(vl), rna(getattr(vl, "cycles", None)),
          tree_hash(getattr(s, "compositing_node_group", None) or getattr(s, "node_tree", None)),
          s.world.name if s.world else None, tree_hash(s.world.node_tree) if s.world else None, rna(getattr(s.world, "cycles", None)))
    world_fcs = fcurves(s) + (fcurves(s.world) + fcurves(s.world.node_tree) if s.world else [])
    seed_anim = bool(getattr(s.cycles, "use_animated_seed", False))
    CULL = float(os.environ.get("CULL_R", 120)); FRUSTUM = os.environ.get("CULL_VIEW", "1") != "0"
    WIDE = float(os.environ.get("CULL_WIDE", 1.3)); ANG = float(os.environ.get("CULL_ANG", 0.15)); NEAR = float(os.environ.get("CULL_NEAR", 1.0))
    print("hashing %d frames: %d animated + %d static objects (%d mirrors), cull: view %s, %s m" % (s.frame_end - s.frame_start + 1, len(dyn), len(sta),
          sum(i["mirror"] for i in info), "on" if FRUSTUM else "off", CULL or "no limit"))

    def counts(c, r, cam, inv, tx, ty):
        """which objects can show in this frame: inside the (widened) view, or close/big enough off-screen to change
        light, shadows or bounce (angular radius > ANG), or anything within CULL_NEAR m of the lens."""
        ph = np.c_[c, np.ones(len(c))] @ inv.T                    # camera space: -z forward
        z = -ph[:, 2]; dist = np.linalg.norm(ph[:, :3], axis=1)
        zz = np.maximum(z, 1e-6)
        inview = (z + r > 0) & (np.abs(ph[:, 0]) - r <= tx * zz * WIDE + r) & (np.abs(ph[:, 1]) - r <= ty * zz * WIDE + r)
        ok = inview | (r > ANG * np.maximum(dist - r, 1e-6)) | (dist - r < NEAR)
        if CULL: ok &= dist - r < CULL
        return ok

    def frame_view(cam):
        fr = cam.data.view_frame(scene=s)
        tx = max(abs(v.x / v.z) for v in fr); ty = max(abs(v.y / v.z) for v in fr)
        return np.array(cam.matrix_world.inverted()), tx, ty

    dyn_c = lambda i: np.array((i["o"].matrix_world @ Vector(i["c"]))[:])

    def state(f):                     # f: frame, may be fractional (motion blur shutter)
        s.frame_set(int(f), subframe=f - int(f))
        cam = s.camera
        inv, tx, ty = frame_view(cam)
        parts = [G, f if seed_anim else 0, cam.name, [R(x, 5) for row in cam.matrix_world for x in row], H(rna(cam.data)),
                 [R(c.evaluate(f), 5) for c in world_fcs + cam_fcs]]
        live = [i for i in dyn if not i["o"].hide_render]
        dc = np.array([dyn_c(i) for i in live]).reshape(-1, 3)
        dr = np.array([i["r"] * max(i["o"].matrix_world.to_scale()) for i in live])
        dl = np.array([i["light"] for i in live], dtype=bool)
        # a mirror in view reflects what's behind the camera: then only the distance limit applies
        full = not FRUSTUM or (len(sta) and bool((st_on & st_mirror & counts(st_c, st_r, cam, inv, tx, ty)).any())) \
            or (len(live) and bool((np.array([i["mirror"] for i in live], dtype=bool) & counts(dc, dr, cam, inv, tx, ty)).any()))
        def mask(c, r, light):
            if full:
                return light | (np.linalg.norm(c - np.array(cam.matrix_world.translation[:]), axis=1) - r < CULL) if CULL else np.ones(len(c), bool)
            return light | counts(c, r, cam, inv, tx, ty)
        if len(sta):
            parts.append(int(st_num[st_on & mask(st_c, st_r, st_light)].sum()))   # wraps mod 2^64: order-free sum
        if len(live):
            for i, on in zip(live, mask(dc, dr, dl)):
                if on:
                    mw = i["o"].matrix_world
                    parts.append([i["st"], [R(x) for row in mw for x in row], [R(c.evaluate(f), 4) for c in i["fcs"]]])
        return H(parts)

    fs, fe = 1, s.frame_end
    try: nf = int(g.get("NF") or fe)
    except Exception: nf = fe
    fe = nf
    # motion blur: the shutter's start and end both count (START 0.5 = frame .. frame+0.5)
    sh = s.render.motion_blur_shutter if s.render.use_motion_blur else 0.0
    off = {"START": (0.0, sh), "CENTER": (-sh / 2, sh / 2), "END": (-sh, 0.0)}.get(s.render.motion_blur_position, (0.0, sh))
    offs = sorted({0.0, *off}) if sh else [0.0]
    # per-frame samples: scene_kit.render() boosts dark shots (dark_shots), so a frame's sample count is an input too
    dark = {}
    if "dark_shots" in g and s.cycles.samples >= 16 and s.render.engine == "CYCLES" and not os.environ.get("NODARK"):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): dark = g["dark_shots"](s.cycles.samples)
    keys = [hashlib.md5(("".join(state(f + o) for o in offs) + str(dark.get(f, ""))).encode()).hexdigest()[:20] for f in range(fs, fe + 1)]
    shots = [list(x) for x in g.get("SHOTS", [])]
    print("hashed in %.0f s (%.1f ms/frame)" % (time.time() - t0, 1000 * (time.time() - t0) / len(keys)))
    return {"part": g.get("PART", os.path.basename(script)[:-3]), "script": os.path.basename(script), "nf": nf,
            "fps": s.render.fps, "settings": settings_now(), "keys": keys, "shots": shots, "made": time.strftime("%Y-%m-%d %H:%M")}


# ====================================================================== plan / compare
def compare(cur, nxt):
    """-> (frame -> old frame to reuse or None). Same frame number first, else the nearest frame with that key,
    keeping reuse in time order (the splice streams the old master once)."""
    reuse = {}
    if not cur or cur.get("settings") != nxt["settings"]:
        return {f: None for f in range(1, nxt["nf"] + 1)}
    where = {}
    for i, k in enumerate(cur["keys"]): where.setdefault(k, []).append(i + 1)
    last = 0
    for f, k in enumerate(nxt["keys"], 1):
        cands = [g for g in where.get(k, []) if g >= last]
        g = f if f in cands else (min(cands, key=lambda g: abs(g - f)) if cands else None)
        reuse[f] = g
        if g: last = g
    return reuse


def plan(nxt, cur, story):
    reuse = compare(cur, nxt)
    dirty = [f for f, g in reuse.items() if g is None]
    shifted = sum(1 for f, g in reuse.items() if g and g != f)
    nf = nxt["nf"]
    print("\n%s: %d frames, %d to render (%.0f%%), %d reused%s" % (nxt["part"], nf, len(dirty), 100.0 * len(dirty) / nf,
          nf - len(dirty), " (%d shifted in time)" % shifted if shifted else ""))
    if not cur: print("  no cached render yet (first render renders everything; accept it afterwards)")
    elif cur.get("settings") != nxt["settings"]: print("  render settings differ from the cache:", cur.get("settings"), "->", nxt["settings"])
    ds = set(dirty)
    for name, a, b in nxt.get("shots", []):
        n = sum(1 for f in range(a, b + 1) if f in ds)
        if n: print("  %-34s %4d-%4d  %3d/%3d frames" % (name[:34], a, b, n, b - a + 1))
    st = nxt["settings"]
    px = int(st["RX"]) * int(st["RY"]) / (1080 * 1920.0); spp = int(st["SAMPLES"]) / 32.0
    sec = len(dirty) * GPU_S_PER_FRAME * px * spp + (120 if dirty else 0)         # + ~2 min pod setup
    print("  GPU estimate (1x 4090): %.1f min, ~$%.2f at Secure $%.2f/hr" % (sec / 60, sec / 3600 * SECURE_4090, SECURE_4090))
    print("RANGES=%s" % ranges(dirty))
    return dirty


def load_json(p):
    try: return json.load(open(p))
    except (OSError, ValueError): return None


# ====================================================================== splice (ffmpeg only, runs anywhere)
def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                                   "stream=width,height,nb_read_packets", "-of", "csv=p=0", path]).decode().strip().split(",")
    return int(out[0]), int(out[1]), int(out[2])


def reader(args):
    return subprocess.Popen(["ffmpeg", "-v", "error"] + args + ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)


def read_exact(p, n):
    buf = bytearray()
    while len(buf) < n:
        b = p.stdout.read(n - len(buf))
        if not b: return None
        buf += b
    return bytes(buf)


def splice(part, story, new, out_master, crf):
    d = cache_dir(story)
    cur = load_json(os.path.join(d, part + ".json")); nxt = load_json(os.path.join(d, part + ".next.json"))
    old_master = os.path.join(d, part + "_master.mp4")
    if not nxt: raise SystemExit("no %s.next.json: run plan first" % part)
    reuse = compare(cur, nxt)
    need = [f for f, g in reuse.items() if g is None]
    # the new frames: a folder of NNNN.png or a patch video (+ its .json frame list from pod_patch.sh)
    if os.path.isdir(new):
        miss = [f for f in need if not (os.path.exists(os.path.join(new, "%04d.png" % f)) and os.path.getsize(os.path.join(new, "%04d.png" % f)) > 0)]
        if miss: raise SystemExit("missing new frames: %s" % ranges(miss))
        seq = os.path.join(d, ".splice_seq"); shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq)
        for i, f in enumerate(need):            # the new frames as one numbered sequence, in time order
            os.symlink(os.path.abspath(os.path.join(new, "%04d.png" % f)), os.path.join(seq, "%06d.png" % i))
        W = Hh = None
        if need:
            W, Hh = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                                                        os.path.join(seq, "000000.png")]).decode().strip().split(",")[:2])
        src_new = reader(["-framerate", str(nxt["fps"]), "-i", os.path.join(seq, "%06d.png")]) if need else None
        order = need
    else:
        meta = load_json(os.path.splitext(new)[0] + ".json") or {}
        order = meta.get("frames") or need
        if set(order) < set(need): raise SystemExit("patch lacks frames: %s" % ranges(sorted(set(need) - set(order))))
        W, Hh, n = probe(new)
        if n != len(order): raise SystemExit("patch has %d frames, its list %d" % (n, len(order)))
        src_new = reader(["-i", new])
    if cur and any(g for g in reuse.values()):
        if not os.path.exists(old_master): raise SystemExit("no cached master %s" % old_master)
        OW, OH, on = probe(old_master)
        if on != cur["nf"]: raise SystemExit("cached master has %d frames, its keys %d" % (on, cur["nf"]))
        if W and (OW, OH) != (W, Hh): raise SystemExit("size mismatch: master %dx%d, new frames %dx%d" % (OW, OH, W, Hh))
        W, Hh = OW, OH
        src_old = reader(["-i", old_master])
    else:
        src_old = None
    FS = W * Hh * 3 // 2
    tmp = out_master + ".part.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "%dx%d" % (W, Hh), "-r", str(nxt["fps"]),
                            "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", str(crf), "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    old_pos = 0; old_frame = None; new_q = list(order); new_frames = {}
    for f in range(1, nxt["nf"] + 1):
        g = reuse[f]
        if g:
            while old_pos < g:
                old_frame = read_exact(src_old, FS); old_pos += 1
                if old_frame is None: raise SystemExit("old master ended at %d" % old_pos)
            enc.stdin.write(old_frame)
        else:
            while f not in new_frames:
                if not new_q: raise SystemExit("ran out of new frames at %d" % f)
                k = new_q.pop(0); fr = read_exact(src_new, FS)
                if fr is None: raise SystemExit("new frames ended early")
                if k in reuse and reuse[k] is None: new_frames[k] = fr
            enc.stdin.write(new_frames.pop(f))
    enc.stdin.close(); enc.wait()
    for p in (src_old, src_new):
        if p: p.kill()
    if enc.returncode: raise SystemExit("encode failed")
    os.replace(tmp, out_master)
    shutil.rmtree(os.path.join(d, ".splice_seq"), ignore_errors=True)
    print("spliced %s: %d frames reused from the cache, %d new -> %s" % (part, nxt["nf"] - len(need), len(need), out_master))
    return need


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("plan", "splice", "accept", "status"))
    ap.add_argument("target", help="plan: the part script (part3.py); others: the part name (p3)")
    ap.add_argument("--story", default=os.environ.get("STORY", "bloxbury"))
    ap.add_argument("--new", help="splice: folder of new NNNN.png frames or the pod's patch_<part>.mp4")
    ap.add_argument("--master", help="accept: frames folder or video of a FULL render made with the planned settings")
    ap.add_argument("--out", help="splice: also make the final mp4 (make_part.sh) with --audio and --captions")
    ap.add_argument("--audio"); ap.add_argument("--captions")
    ap.add_argument("--crf", type=int, default=10)
    a = ap.parse_args()
    d = cache_dir(a.story)
    if a.cmd == "plan":
        nxt = build_keys(a.target)
        json.dump(nxt, open(os.path.join(d, nxt["part"] + ".next.json"), "w"))
        plan(nxt, load_json(os.path.join(d, nxt["part"] + ".json")), a.story)
        return
    part = a.target
    cur_p, nxt_p, m = (os.path.join(d, part + x) for x in (".json", ".next.json", "_master.mp4"))
    if a.cmd == "status":
        cur, nxt = load_json(cur_p), load_json(nxt_p)
        print("cache:", cur and {k: cur[k] for k in ("made", "nf", "settings")}, "master:", os.path.exists(m))
        if nxt: plan(nxt, cur, a.story)
        return
    if a.cmd == "accept":
        nxt = load_json(nxt_p)
        if not nxt or not a.master: raise SystemExit("accept needs a plan and --master")
        if os.path.isdir(a.master):
            subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-framerate", str(nxt["fps"]), "-i", os.path.join(a.master, "%04d.png"),
                                   "-frames:v", str(nxt["nf"]), "-c:v", "libx264", "-preset", "fast", "-crf", str(a.crf), "-pix_fmt", "yuv420p", m])
        elif os.path.abspath(a.master) != os.path.abspath(m):
            shutil.copyfile(a.master, m)
        n = probe(m)[2]
        if n != nxt["nf"]: raise SystemExit("master has %d frames, the plan %d: not accepted" % (n, nxt["nf"]))
        os.replace(nxt_p, cur_p); print("cached %s: %d frames, %s" % (part, n, nxt["settings"]))
        return
    if a.cmd == "splice":
        tmp_master = m + ".new.mp4"
        splice(part, a.story, a.new, tmp_master, a.crf)
        os.replace(tmp_master, m); os.replace(nxt_p, cur_p)
        print("cache now holds the spliced render (%s)" % m)
        if a.out:
            subprocess.check_call(["sh", os.path.join(REPO, "_pipeline", "make_part.sh"), m, a.out, a.audio, a.captions])


if __name__ == "__main__":
    main()
