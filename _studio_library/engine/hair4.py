# hair4.py - library expansion: 6 more hairstyles (crop, afro, bob, high ponytail, braids, top bun + bangs)


def X_crop(neck, c, rng, P=None):
    m = hair_mat("HairX1" + str(rng.random())[2:6], c); o = []
    shell(neck, m, o, size=(1.25, 1.28, 0.62), z=1.03)
    for az in range(0, 360, 16):
        a = az + rng.uniform(-5, 5)
        if abs(((a + 180) % 360) - 180) < 35: continue
        o.append(lock(neck, jitter(flow(a, 86, 22 if abs(((a + 180) % 360) - 180) < 100 else 12, vol=0.08), rng, 0.02), 0.3, 0.07, m))
    for i in range(7):
        x = -0.36 + i * 0.12
        o.append(lock(neck, fringe_pts(x * 0.8, x + 0.06, 1.06 + rng.uniform(-0.01, 0.02)), 0.22, 0.07, m, wpow=1.4))
    skin = (P or {}).get("skin_rgb", (234, 184, 146))
    o.append(solid("Fade", HEAD_MESH, (1.018, 1.018, 1.004), Vector((0, 0, 0.6)), fade_mat(c, skin), parent=neck, col=COL_CHARS))
    return o


def fade_mat(hair, skin):
    m = bpy.data.materials.new("Fade"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180
    L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.04
    L.new(nz.outputs["Fac"], mul.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; L.new(sep.outputs["Z"], add.inputs[0]); L.new(mul.outputs[0], add.inputs[1])
    r = N.new("ShaderNodeValToRGB"); L.new(add.outputs[0], r.inputs["Fac"])
    e = r.color_ramp.elements
    e[0].position = 0.4; e[0].color = (*lin(skin), 1)
    e[1].position = 0.86; e[1].color = (*lin(hair), 1)
    mid = e.new(0.64); mid.color = (*lin(tuple(int(h * 0.6 + s_ * 0.4) for h, s_ in zip(hair, skin))), 1)
    L.new(r.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.72; mr.inputs["From Max"].default_value = 0.8
    mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
    L.new(sep.outputs["Y"], mr.inputs["Value"]); L.new(mr.outputs["Result"], b.inputs["Alpha"])
    return m


def X_afro(neck, c, rng, P=None):
    m = hair_mat("HairX2" + str(rng.random())[2:6], c, rough=0.85)
    ob = ball("Afro", (1.95, 1.85, 1.5), Vector((0, -0.2, 1.18)), m, neck)
    me = ob.data.copy(); ob.data = me
    sub = ob.modifiers.new("Sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2
    tex = bpy.data.textures.new("AfroNoise" + str(rng.random())[2:6], "CLOUDS"); tex.noise_scale = 0.08; tex.noise_depth = 2
    dm = ob.modifiers.new("Fuzz", "DISPLACE"); dm.texture = tex; dm.strength = 0.09; dm.mid_level = 0.5
    o = [ob]
    for x in (-0.3, -0.1, 0.1, 0.3):   # soft hairline curls at the forehead
        o.append(ball("AfroEdge", (0.3, 0.26, 0.26), face_front(x, 1.08, 0.04), m, neck))
    return o


def X_bob(neck, c, rng, P=None):
    m = hair_mat("HairX3" + str(rng.random())[2:6], c, rough=0.38); o = []
    shell(neck, m, o, back=True)
    for az in range(36, 325, 11):   # outer layer, all ending at the same chin line, tips curl in
        a = az + rng.uniform(-2, 2)
        p = flow(a, 86, -36, vol=0.2)
        p[-1] = p[-1] - hdir(a) * 0.07 + Vector((0, 0, 0.03))
        o.append(lock(neck, p, 0.38, 0.09, m, n=22, wpow=6))
    for az in range(42, 320, 16):   # inner/middle layer for fullness (no gaps)
        o.append(lock(neck, flow(az + 8, 70, -22, vol=0.1), 0.36, 0.07, m, n=18, wpow=5))
    for s_ in (-1, 1):   # front sides down to the same chin line
        for i in range(2):
            o.append(lock(neck, [surf(s_ * 8, 76), surf(s_ * (32 + i * 10), 40, 1.16), face_front(s_ * (0.5 + i * 0.04), 0.8, 0.1),
                                 face_front(s_ * (0.53 + i * 0.04), 0.48, 0.09)], 0.3, 0.08, m, n=20, wpow=6))
    for i in range(9):   # blunt full-width bangs
        x = -0.44 + i * 0.11
        o.append(lock(neck, fringe_pts(x * 0.85, x, 0.93), 0.2, 0.07, m, wpow=8))
    return o


def X_ponytail(neck, c, rng, P=None):
    m = hair_mat("HairX4" + str(rng.random())[2:6], c, rough=0.4); o = []
    shell(neck, m, o, size=(1.27, 1.3, 0.74), z=1.0)
    tie = Vector((0, -0.42, 1.4))
    for az in range(-160, 161, 16):   # smooth, flat, pulled-back sides
        a = az + rng.uniform(-2, 2)
        p0 = surf(a, 10 if abs(a) > 60 else 42, 1.0)
        mid = surf(a * 0.75 + (180 if a > 0 else -180) * 0.25, 48, 1.03)
        o.append(lock(neck, [p0, mid, tie + Vector((0, 0.08, -0.03))], 0.44, 0.03, m, wpow=0.5))
    o.append(ball("PonyTie", (0.3, 0.3, 0.3), tie, mat("HairTie" + str(rng.random())[2:5], (214, 52, 90)), neck))
    for k in range(7):   # the tail
        ang = k / 7 * math.pi * 2
        off = Vector((math.cos(ang) * 0.07, math.sin(ang) * 0.05, 0))
        o.append(lock(neck, [tie + off, tie + off + Vector((0, -0.28, 0.0)), tie + off * 1.5 + Vector((0, -0.42, -0.45)),
                             tie + off * 1.2 + Vector((0, -0.38, -1.05))], 0.24, 0.1, m, n=24, wpow=3))
    for x in (-0.3, 0.3):   # face-framing strands
        o.append(lock(neck, [surf(math.copysign(40, x), 50), face_front(x * 1.5, 0.85, 0.08), face_front(x * 1.6, 0.5, 0.1)],
                      0.12, 0.05, m, wpow=3))
    return o


def X_braids(neck, c, rng, P=None):
    m = hair_mat("HairX5" + str(rng.random())[2:6], c, rough=0.45); o = []
    shell(neck, m, o, back=True, size=(1.27, 1.3, 0.76), z=1.0)
    tie_m = mat("BTie", (214, 52, 90))
    for s in (-1, 1):
        for i in range(4):   # centre part, sides pulled down to the braid roots
            o.append(lock(neck, [surf(s * 4, 78 - i * 4), surf(s * (35 + i * 14), 45, 1.08), surf(s * (75 + i * 10), 0, 1.08),
                                 Vector((s * 0.6, 0.12, 0.42))], 0.36, 0.06, m, wpow=1.0))
        nseg = 11
        for k in range(nseg):   # plait: overlapping diagonal locks alternating left/right
            t = k / (nseg - 1)
            z = 0.42 - 1.35 * t
            y = 0.12 + 0.5 * min(1, t * 2.2)
            if z < 0.05: y = max(y, 0.62)
            x = s * 0.64
            d = 1 if k % 2 else -1
            w = 0.2 - 0.06 * t
            o.append(lock(neck, [Vector((x - d * 0.07, y, z + 0.08)), Vector((x, y + 0.03, z)), Vector((x + d * 0.07, y, z - 0.1))],
                          w, 0.12, m, n=10, wpow=2.5, center=lambda p, x=x: Vector((x, p.y - 0.5, p.z))))
        z_end = 0.42 - 1.35
        o.append(ball("BraidTie", (0.15, 0.15, 0.1), Vector((s * 0.64, 0.62, z_end - 0.08)), tie_m, neck))
        o.append(lock(neck, [Vector((s * 0.64, 0.62, z_end - 0.1)), Vector((s * 0.66, 0.64, z_end - 0.22)),
                             Vector((s * 0.68, 0.64, z_end - 0.34))], 0.2, 0.06, m, wpow=1.5))
    return o


def X_topbun(neck, c, rng, P=None):
    m = hair_mat("HairX6" + str(rng.random())[2:6], c, rough=0.45); o = []
    shell(neck, m, o, size=(1.27, 1.3, 0.74), z=1.0)
    bun = Vector((0, -0.12, 1.62))
    for az in range(-160, 161, 20):
        a = az + rng.uniform(-4, 4)
        o.append(lock(neck, [surf(a, 8, 1.03), surf(a, 55, 1.06), bun + Vector((0, 0, -0.12))], 0.3, 0.06, m, wpow=0.8))
    o.append(ball("Bun", (0.66, 0.66, 0.56), bun, m, neck))
    for k in range(5):
        a = k * 72
        o.append(lock(neck, [bun + Vector((math.cos(math.radians(a)) * 0.22, math.sin(math.radians(a)) * 0.22, 0.14)),
                             bun + Vector((math.cos(math.radians(a + 60)) * 0.34, math.sin(math.radians(a + 60)) * 0.34, 0.0)),
                             bun + Vector((math.cos(math.radians(a + 110)) * 0.3, math.sin(math.radians(a + 110)) * 0.3, -0.16))],
                      0.16, 0.06, m, wpow=1.5))
    for i in range(8):
        x = -0.42 + i * 0.12
        o.append(lock(neck, fringe_pts(x * 0.85, x + 0.03, 0.92 + (0.03 if i % 2 else 0)), 0.18, 0.06, m, wpow=2))
    return o


HAIR4 = {"X1": ("Short crop", X_crop, (40, 30, 24)), "X2": ("Afro", X_afro, (28, 20, 18)),
         "X3": ("Bob + blunt bangs", X_bob, (60, 36, 26)), "X4": ("High ponytail", X_ponytail, (200, 150, 80)),
         "X5": ("Two braids", X_braids, (110, 60, 40)), "X6": ("Top bun + bangs", X_topbun, (24, 20, 20))}


def add_hair4(P, key, rng, colour=None):
    name, fn, c = HAIR4[key]
    P["hair"][key] = fn(P["neck"], colour or c, rng, P)
    return P["hair"][key]
