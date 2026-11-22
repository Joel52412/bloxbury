# hair2.py - Roblox-style hair: a scalp shell + many wide, flat, tapered locks
# layered like shingles (how real Roblox hair accessories are modelled).
HC = Vector((0, -0.03, 0.72))


def catmull(pts, n):
    P = [pts[0]] + pts + [pts[-1]]
    segs = len(pts) - 1
    out = []
    for i in range(n):
        t = i / (n - 1) * segs
        k = min(int(t), segs - 1); u = t - k
        p0, p1, p2, p3 = P[k], P[k + 1], P[k + 2], P[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u +
                          (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


def hair_mat(name, root, tip=None, rough=0.42):
    tip = tip or root
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]
    uv = N.new("ShaderNodeUVMap")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs["UV"], sep.inputs[0])
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (22, 1.2, 1)
    L.new(uv.outputs["UV"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 6
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.35
    L.new(nz.outputs["Fac"], mul.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"
    L.new(sep.outputs["Y"], add.inputs[0]); L.new(mul.outputs[0], add.inputs[1])
    ramp = N.new("ShaderNodeValToRGB"); L.new(add.outputs[0], ramp.inputs["Fac"])
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*lin(shade(root, 0.8)), 1)
    e[1].position = 1.05; e[1].color = (*lin(tip), 1)
    mid = e.new(0.72 if tip != root else 0.3); mid.color = (*lin(root), 1)
    L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.45
    L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return m


def lock(parent, pts, width, thick, m, n=20, ring=10, wpow=2.2, root_w=1.0, center=None):
    path = catmull([Vector(p) for p in pts], n)
    verts, faces = [], []
    for i, p in enumerate(path):
        t = i / (n - 1)
        T = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        Nr = (p - (center(p) if center else HC)).normalized()
        Nn = Nr - T * Nr.dot(T)
        Nn = Nn.normalized() if Nn.length > 1e-5 else Vector((0, 1, 0))
        B = T.cross(Nn)
        w = width * (1 - t ** wpow) * (root_w + (1 - root_w) * min(1, t * 4)) + 0.004
        th = thick * (1 - t) ** 0.6 + 0.004
        for k in range(ring):
            a = 2 * math.pi * k / ring
            verts.append(p + B * (w * 0.5 * math.cos(a)) + Nn * (th * 0.5 * math.sin(a)))
    for i in range(n - 1):
        for k in range(ring):
            a = i * ring + k; b = i * ring + (k + 1) % ring
            faces.append((a, b, b + ring, a + ring))
    faces.append(tuple(range(ring))[::-1])
    me = bpy.data.meshes.new("Lock"); me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi % ring) / ring, (vi // ring) / (n - 1))
    me.materials.append(m)
    ob = bpy.data.objects.new("Lock", me); link(ob, COL_CHARS); ob.parent = parent
    return ob


def surf(az, el, k=1.0):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e) * 0.65 * k, -0.04 + math.cos(a) * math.cos(e) * 0.67 * k,
                   0.82 + math.sin(e) * 0.54 * k))


def hdir(az):
    a = math.radians(az)
    return Vector((math.sin(a), math.cos(a), 0))


def flow(az, el0, el1, vol=0.12, hang=0.0, flick=0.0, wave=0.0, sweep=0.0, n=5, rng=None, curl=0.0):
    pts = []
    for i in range(n):
        s = i / (n - 1)
        a = az + sweep * s
        p = surf(a, el0 + (el1 - el0) * s, 1.03 + vol * math.sin(math.pi * s * 0.85))
        if wave:
            side = Vector((math.cos(math.radians(a)), -math.sin(math.radians(a)), 0))
            p = p + side * wave * math.sin(s * math.pi * 2)
        pts.append(p)
    a = az + sweep
    if hang > 0:
        last = pts[-1]
        front = math.cos(math.radians(a)) > 0.2
        steps = max(2, int(hang / 0.35))
        for j in range(1, steps + 1):
            z = last.z - hang * j / steps
            q = last + hdir(a) * (0.03 * j) + Vector((0, 0, z - last.z))
            if z < 0.05:   # keep clear of the torso: go in front of or behind it
                q.y = (max(q.y, 0.6) if front else min(q.y, -0.6))
            if wave:
                side = Vector((math.cos(math.radians(a)), -math.sin(math.radians(a)), 0))
                q = q + side * wave * math.sin(j * 1.7)
            pts.append(q)
    if curl:
        last, prev = pts[-1], pts[-2]
        d = (last - prev).normalized(); o = hdir(a)
        for j in range(1, 4):
            ang = j * 1.6
            pts.append(last + d * curl * math.sin(ang) * 0.8 + o * curl * (1 - math.cos(ang)))
    if flick:
        pts[-1] = pts[-1] + hdir(a) * flick + Vector((0, 0, flick * 0.6))
    return pts


def fringe_pts(x0, xtip, ztip, crown_el=62, off=0.075):
    az0 = math.degrees(math.asin(max(-0.9, min(0.9, x0 / 0.6))))
    return [surf(az0, crown_el, 1.02), surf(az0 * 0.9 + (xtip - x0) * 30, 40, 1.13),
            face_front((x0 + xtip) / 2, 1.04, off + 0.03), face_front(xtip, ztip, off)]


def shell(neck, m, o, back=False, size=(1.27, 1.3, 0.74), z=1.0):
    o.append(ball("HairShell", size, Vector((0, -0.07, z)), m, neck))
    if back:
        o.append(ball("HairShellBack", (1.22, 0.85, 1.0), Vector((0, -0.32, 0.72)), m, neck))


# ---------------------------------------------------------------- styles
def S_fluffy(neck, c, rng, tip=None):
    m = hair_mat("HairS1", c, tip); o = []; shell(neck, m, o, back=True)
    for az in range(0, 360, 26):
        if abs(((az + 180) % 360) - 180) < 40: continue
        o.append(lock(neck, flow(az + rng.uniform(-5, 5), 84, -22, vol=0.2, flick=0.05, rng=rng), 0.52, 0.1, m))
    for az in range(13, 373, 30):
        if abs(((az + 180) % 360) - 180) < 30: continue
        o.append(lock(neck, flow(az + rng.uniform(-6, 6), 88, 8, vol=0.22, flick=0.04), 0.5, 0.1, m))
    for i, x in enumerate((-0.42, -0.26, -0.1, 0.06, 0.22, 0.38)):
        o.append(lock(neck, fringe_pts(x * 0.8, x + 0.1, 0.9 + (0.06 if i % 2 else 0) + rng.uniform(-0.02, 0.03)),
                      0.34, 0.1, m))
    return o


def S_wavy_part(neck, c, rng, tip=None):
    m = hair_mat("HairS2", c, tip); o = []; shell(neck, m, o, back=True)
    for s in (-1, 1):
        for i in range(4):
            o.append(lock(neck, [surf(s * 6, 74 - i * 3), surf(s * (28 + i * 8), 58 - i * 4, 1.16),
                                 face_front(s * (0.36 + i * 0.05), 1.1 - i * 0.03, 0.1),
                                 surf(s * (72 + i * 6), 18 - i * 6, 1.16), surf(s * (78 + i * 6), -18, 1.22)],
                          0.36, 0.09, m))
        for az in range(85, 180, 22):
            o.append(lock(neck, flow(s * az + rng.uniform(-4, 4), 66, -20, vol=0.16, wave=0.05, flick=0.06, hang=0.1),
                          0.4, 0.09, m))
    o.append(lock(neck, flow(180, 70, -22, vol=0.16, wave=0.05, flick=0.06, hang=0.1), 0.42, 0.09, m))
    return o


def S_long_straight(neck, c, rng, tip=None, curls=False, bangs=False, name="HairS3"):
    m = hair_mat(name, c, tip, rough=0.38); o = []; shell(neck, m, o, back=True)
    S_long_straight.last = m
    for az in range(95, 266, 10):   # back curtain
        L = 1.5 + rng.uniform(-0.15, 0.15)
        o.append(lock(neck, flow(az + rng.uniform(-3, 3), 82, -8, vol=0.12, hang=L, wave=0.04 if not curls else 0.0,
                                 curl=0.14 if curls else 0.0), 0.42, 0.08, m, n=28, wpow=5))
    for s in (-1, 1):
        for i in range(3):   # part -> sides -> over the shoulders in front
            az = s * (40 + i * 16)
            pts = [surf(s * 4, 76), surf(s * (20 + i * 10), 60, 1.12), surf(az, 20, 1.16), surf(az + s * 8, -12, 1.2)]
            last = pts[-1]
            for j in (1, 2, 3):
                q = last + Vector((s * 0.05 * j, 0, -0.45 * j)); q.y = max(q.y, 0.62) if q.z < 0.05 else q.y
                pts.append(q)
            if curls:
                pts.append(pts[-1] + Vector((s * 0.12, 0.05, 0.05)))
            o.append(lock(neck, pts, 0.38, 0.08, m, n=28, wpow=5))
    if bangs:
        for i, x in enumerate((-0.36, -0.22, -0.08, 0.08, 0.22, 0.36)):
            o.append(lock(neck, fringe_pts(x * 0.9, x, 0.93 + rng.uniform(-0.01, 0.02)), 0.24, 0.07, m, wpow=3))
    return o


def S_sideswept(neck, c, rng, tip=None):
    m = hair_mat("HairS5", c, tip, rough=0.35); o = []; shell(neck, m, o)
    for i, az in enumerate(range(-80, 200, 20)):   # everything flows from a right-side parting
        o.append(lock(neck, [surf(-75, 62), surf(az * 0.6 - 30, 78, 1.14), surf(az, 45, 1.18), surf(az + 25, 5, 1.12)],
                      0.42, 0.1, m))
    for x in (-0.35, -0.15, 0.05):   # front sweep across the forehead top
        o.append(lock(neck, [surf(-70, 60), surf(-30, 60, 1.16), face_front(x, 1.08, 0.1), face_front(x + 0.4, 1.0, 0.09)],
                      0.34, 0.1, m))
    for az in range(120, 250, 26):
        o.append(lock(neck, flow(az, 50, -5, vol=0.08), 0.4, 0.08, m))
    return o


def helix(c, axis, r=0.09, turns=1.3, length=0.26, n=9):
    axis = axis.normalized()
    u = axis.cross(Vector((0, 0, 1)))
    if u.length < 0.1: u = axis.cross(Vector((1, 0, 0)))
    u.normalize(); v = axis.cross(u)
    return [c + axis * length * i / (n - 1) + (u * math.cos(2 * math.pi * turns * i / (n - 1)) +
                                                 v * math.sin(2 * math.pi * turns * i / (n - 1))) * r * (1 - 0.35 * i / (n - 1))
            for i in range(n)]


def S_curly(neck, c, rng, tip=None):
    m = hair_mat("HairS6", c, tip, rough=0.6); o = []
    shell(neck, m, o, size=(1.34, 1.36, 0.9), z=1.02)
    for k in range(140):
        az = rng.uniform(0, 360); el = rng.uniform(5, 90)
        if abs(((az + 180) % 360) - 180) < 55 and el < 48: continue
        base = surf(az, el, 1.08 + rng.uniform(0, 0.08))
        down = Vector((0, 0, -1)) * 0.5 + hdir(az) * 0.5 + Vector((rng.uniform(-.3, .3), rng.uniform(-.3, .3), 0))
        o.append(lock(neck, helix(base, down, r=0.1, length=0.26, turns=rng.uniform(1.1, 1.6)), 0.2, 0.09, m, n=24, wpow=3))
    for x in (-0.36, -0.18, 0.0, 0.18, 0.36):   # curls on the forehead
        base = face_front(x, 1.08, 0.12)
        o.append(lock(neck, helix(base, Vector((0, 0.3, -1)), r=0.07, length=0.2), 0.16, 0.08, m, n=24, wpow=3))
    return o


def S_wolf(neck, c, rng, tip=None):
    m = hair_mat("HairS7", c, tip, rough=0.5); o = []; shell(neck, m, o, back=True)
    for az in range(40, 330, 22):
        o.append(lock(neck, flow(az + rng.uniform(-5, 5), 70, -24, vol=0.14, flick=0.14, hang=0.12), 0.36, 0.09, m))
    for az in range(51, 320, 30):
        o.append(lock(neck, flow(az + rng.uniform(-6, 6), 88, 22, vol=0.3, flick=0.12), 0.34, 0.09, m))
    for s in (-1, 1):
        o.append(lock(neck, [surf(s * 30, 70), surf(s * 45, 40, 1.15), face_front(s * 0.5, 0.75, 0.1),
                             face_front(s * 0.56, 0.5, 0.12)], 0.26, 0.08, m))
    for i, x in enumerate((-0.38, -0.2, -0.02, 0.16, 0.34)):
        o.append(lock(neck, fringe_pts(x * 0.8, x + 0.06, 0.88 + (0.07 if i % 2 else 0)), 0.27, 0.08, m))
    return o


def S_anime_long(neck, c, rng, tip=None):
    o = S_long_straight(neck, c, rng, tip, bangs=False, name="HairS8")
    m = S_long_straight.last
    for s in (-1, 1):   # long side locks framing the face
        o.append(lock(neck, [surf(s * 25, 70), surf(s * 42, 40, 1.14), face_front(s * 0.5, 0.8, 0.1),
                             Vector((s * 0.62, 0.45, 0.2)), Vector((s * 0.66, 0.64, -0.5)), Vector((s * 0.6, 0.66, -0.95))],
                      0.24, 0.07, m, n=26))
    for i, x in enumerate((-0.34, -0.17, 0.0, 0.17, 0.34)):   # choppy bangs
        o.append(lock(neck, fringe_pts(x * 0.8, x + (0.05 if x < 0 else -0.05), 0.86 + rng.uniform(-0.03, 0.06)),
                      0.25, 0.07, m))
    return o


def S_long_curly(neck, c, rng, tip=None):
    return S_long_straight(neck, c, rng, tip, curls=True, bangs=True, name="HairS4")


HAIR3 = {
    "H1": ("Messy fluffy (two-tone)", S_fluffy, (24, 22, 30), (40, 120, 230)),
    "H2": ("Wavy middle part", S_wavy_part, (92, 60, 38), (140, 100, 66)),
    "H3": ("Long straight", S_long_straight, (214, 168, 110), (240, 210, 160)),
    "H4": ("Long curly + bangs", S_long_curly, (60, 40, 30), (110, 78, 56)),
    "H5": ("Short side-swept", S_sideswept, (150, 100, 40), (200, 150, 70)),
    "H6": ("Curly mop", S_curly, (50, 32, 24), (90, 60, 40)),
    "H7": ("Wolf cut", S_wolf, (236, 236, 240), (190, 190, 200)),
    "H8": ("Long anime (two-tone)", S_anime_long, (28, 26, 30), (200, 200, 214)),
}


def add_hair3(P, key, rng, colour=None, tip=None):
    name, fn, c, t = HAIR3[key]
    P["hair"][key] = fn(P["neck"], colour or c, rng, tip or (t if colour is None else None))
    return P["hair"][key]
