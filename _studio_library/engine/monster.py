# monster.py - "THE KNOCKER" (Bloxbury's closet creature). APPROVED by Joel 22 Nov 2026 - studio library monster.
# Original design: ~12 studs tall (2.4x Milo), starved and stick-thin, hunched, smooth sinewy limbs (not blocky),
# arms past the knees with long pale-clawed fingers, narrow skull pushed forward and tilted, deep black sockets with
# tiny glowing white eyes, and a cheek-to-cheek grin of thin teeth glowing red-orange from inside.
# exec() after the base helpers (empty/COL_CHARS). make_knocker(name) -> dict of pivots for animation.
import bpy, math, bmesh, random as _rnd
from mathutils import Vector as _V


def _kmat(name, rgb, rough=0.5, emit=0.0, emit_rgb=None, coat=0.0, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    lin_ = lambda c: tuple((x / 255) ** 2.2 for x in c)
    b.inputs["Base Color"].default_value = (*lin_(rgb), 1); b.inputs["Roughness"].default_value = rough
    for k in ("Coat Weight", "Clearcoat"):
        if coat and k in b.inputs: b.inputs[k].default_value = coat; break
    if emit:
        b.inputs["Emission Color"].default_value = (*lin_(emit_rgb or rgb), 1); b.inputs["Emission Strength"].default_value = emit
    if bump:     # leathery skin: noise bump + slight colour mottling
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 9.0; nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _catmull(pts, n):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (_V(P[i - 1]), _V(P[i]), _V(P[i + 1]), _V(P[i + 2]))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(_V(pts[-1]))
    return out


def _tube(name, pts, radii, parent, m, n=8, ring=12, col=None, flat=1.0):
    """Smooth tapered tube through pts (spline), radius interpolated along it. flat<1 squashes it front-to-back."""
    path = _catmull(pts, n)
    rad = []; L = len(radii)
    for i in range(len(path)):
        u = i / (len(path) - 1) * (L - 1); k = min(int(u), L - 2); f = u - k
        rad.append(radii[k] * (1 - f) + radii[k + 1] * f)
    bm = bmesh.new(); rings = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        up = _V((0, 1, 0)) if abs(t.y) < 0.9 else _V((1, 0, 0))
        a = t.cross(up).normalized(); b = t.cross(a).normalized()
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * j / ring) + b * flat * math.sin(2 * math.pi * j / ring)) * rad[i])
                      for j in range(ring)])
    for i in range(len(rings) - 1):
        for j in range(ring):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % ring], rings[i + 1][(j + 1) % ring], rings[i + 1][j]))
    c0 = bm.verts.new(path[0]); c1 = bm.verts.new(path[-1] + (path[-1] - path[-2]).normalized() * rad[-1] * 0.6)
    for j in range(ring):
        bm.faces.new((c0, rings[0][(j + 1) % ring], rings[0][j])); bm.faces.new((c1, rings[-1][j], rings[-1][(j + 1) % ring]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); (col or COL_CHARS).objects.link(ob); ob.parent = parent; me.materials.append(m)
    return ob


def _blob(name, loc, scale, parent, m, seg=24, rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name)); COL_CHARS.objects.link(ob)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1); bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons: p.use_smooth = True
    ob.parent = parent; ob.location = loc; ob.scale = scale; ob.rotation_euler = rot; ob.data.materials.append(m)
    return ob


def make_knocker(name="Knocker", height=12.0):
    sk = _kmat(name + "_Skin", (9, 8, 9), rough=0.62, bump=0.6)
    claw = _kmat(name + "_Claw", (182, 172, 150), rough=0.5)
    tooth = _kmat(name + "_Teeth", (196, 180, 140), rough=0.45)
    eye = _kmat(name + "_Eye", (255, 252, 244), rough=0.3, emit=40.0, emit_rgb=(255, 252, 240))
    hole = _kmat(name + "_Hole", (0, 0, 0), rough=1.0)
    maw = _kmat(name + "_Maw", (20, 0, 0), rough=0.8, emit=0.9, emit_rgb=(255, 18, 0))
    K = height / 12.0
    root = empty(name, _V((0, 0, 0)), col=COL_CHARS); root.scale = (K, K, K)
    P = {"root": root, "mats": dict(skin=sk, eye=eye, maw=maw, teeth=tooth)}
    hips = empty(name + "_Hips", _V((0, 0, 5.7)), col=COL_CHARS, parent=root)
    hips.rotation_euler = (math.radians(-32), 0, 0)                       # heavy hunch
    # ---- torso: narrow pelvis, caved belly, ribcage, bony shoulders
    _tube(name + "_Spine", [(0, 0, -0.1), (0, 0.04, 0.7), (0, 0.02, 1.5), (0, 0.12, 2.3), (0, 0.32, 3.0), (0, 0.5, 3.35)],
          [0.4, 0.2, 0.26, 0.56, 0.58, 0.34], hips, sk, ring=18, flat=0.7)
    for sx in (-1, 1):
        for i, z in enumerate((1.75, 2.05, 2.35, 2.65)):                # ribs pressing through
            w = 0.56 + 0.03 * i
            _tube(name + "_Rib", [(sx * 0.05, 0.3 + 0.04 * i, z), (sx * 0.3, 0.27 + 0.04 * i, z - 0.06), (sx * w, 0.05, z - 0.16),
                                  (sx * (w - 0.05), -0.18, z - 0.22)], [0.06, 0.07, 0.06, 0.04], hips, sk, n=6, ring=8)
        _tube(name + "_Clav", [(0, 0.48, 3.25), (sx * 0.5, 0.46, 3.36), (sx * 0.9, 0.3, 3.25)], [0.1, 0.12, 0.16], hips, sk, ring=10)
        _tube(name + "_Pelvis", [(0, 0.12, 0.05), (sx * 0.32, 0.1, 0.0), (sx * 0.4, -0.05, -0.15)], [0.12, 0.13, 0.11], hips, sk, ring=10)
    for i in range(9):                                                   # spine knobs + a few spikes
        z = 0.2 + i * 0.36; y = -0.24 + 0.15 * (z / 3.2) ** 2
        big = i in (4, 6, 7)
        _tube(name + "_Knob", [(0, y + 0.04, z), (0, y - (0.32 if big else 0.08), z + (0.14 if big else 0.02))],
              [0.08, 0.01 if big else 0.05], hips, claw if big else sk, n=4, ring=8)
    # ---- legs: long, thin, knees bent forward, feet with long toes
    for sx, nm in ((-1, "L"), (1, "R")):
        h = empty(f"{name}_Hip{nm}", _V((sx * 0.34, 0, -0.1)), col=COL_CHARS, parent=hips)
        h.rotation_euler = (math.radians(30), 0, 0)                     # legs stay vertical under the hunch
        _tube(name + "_Leg" + nm, [(0, 0, 0), (sx * 0.06, 0.25, -1.4), (sx * 0.08, 0.42, -2.75), (sx * 0.1, 0.08, -4.1),
                                    (sx * 0.12, -0.12, -5.25), (sx * 0.12, 0.15, -5.55)],
              [0.27, 0.19, 0.15, 0.1, 0.085, 0.09], h, sk, ring=12)
        _blob(name + "_Knee", (sx * 0.08, 0.46, -2.75), (0.15, 0.15, 0.17), h, sk)
        for t in (-0.12, -0.02, 0.09):
            _tube(name + "_Toe", [(sx * 0.12 + t * 0.6, 0.15, -5.55), (sx * 0.12 + t * 1.3, 0.75, -5.6), (sx * 0.12 + t * 1.7, 1.25, -5.62)],
                  [0.06, 0.045, 0.03], h, sk, n=4, ring=8)
            _tube(name + "_ToeClaw", [(sx * 0.12 + t * 1.7, 1.25, -5.62), (sx * 0.12 + t * 1.8, 1.48, -5.68)], [0.03, 0.004], h, claw, n=3, ring=8)
        P["hip" + nm] = h
    # ---- arms: hang past the knees, sharp elbows, huge spidery hands
    for sx, nm in ((-1, "L"), (1, "R")):
        sh = empty(f"{name}_Shoulder{nm}", _V((sx * 0.9, 0.3, 3.2)), col=COL_CHARS, parent=hips)
        sh.rotation_euler = (math.radians(26), 0, math.radians(sx * 6))
        _blob(name + "_ShoulderBone", (0, 0, 0.02), (0.17, 0.15, 0.15), sh, sk)
        elbow = (sx * 0.36, -0.3, -3.2); wrist = (sx * 0.3, 0.5, -6.3)
        _tube(name + "_Arm" + nm, [(0, 0, 0), (sx * 0.2, -0.12, -1.6), elbow, (sx * 0.34, 0.12, -4.8), wrist],
              [0.15, 0.11, 0.075, 0.07, 0.06], sh, sk, ring=12)
        _blob(name + "_Elbow", elbow, (0.09, 0.1, 0.12), sh, sk)
        hand = empty(f"{name}_Hand{nm}", _V(wrist), col=COL_CHARS, parent=sh)
        _blob(name + "_Palm", (0, 0.04, -0.28), (0.13, 0.07, 0.3), hand, sk)
        for j, (fx, ln, curl) in enumerate(((-0.12, 1.15, 0.25), (-0.04, 1.45, 0.3), (0.05, 1.55, 0.32), (0.13, 1.3, 0.28), (0.2, 0.85, 0.2))):
            fx = fx * sx
            base = (fx, 0.06 + (0.1 if j == 4 else 0), -0.5)
            k1 = (fx * 1.25, 0.12 + curl * 0.3, -0.5 - ln * 0.45); k2 = (fx * 1.4, 0.18 + curl * 0.9, -0.5 - ln * 0.8)
            tip = (fx * 1.45, 0.3 + curl * 1.5, -0.5 - ln)
            _tube(name + "_Finger", [base, k1, k2, tip], [0.04, 0.035, 0.03, 0.025], hand, sk, n=5, ring=8)
            for kn in (k1, k2): _blob(name + "_Knuckle", kn, (0.042, 0.042, 0.045), hand, sk, seg=12)
            d = (_V(tip) - _V(k2)).normalized()
            _tube(name + "_Claw", [tip, tuple(_V(tip) + d * 0.18 + _V((0, 0.06, 0))), tuple(_V(tip) + d * 0.34 + _V((0, 0.16, 0)))],
                  [0.026, 0.014, 0.002], hand, claw, n=4, ring=8)
        P["shoulder" + nm] = sh; P["hand" + nm] = hand
    # ---- neck pushed forward, narrow skull tilted hard to one side
    neck = empty(name + "_Neck", _V((0, 0.52, 3.35)), col=COL_CHARS, parent=hips)
    neck.rotation_euler = (math.radians(22), 0, 0)
    _tube(name + "_NeckMesh", [(0, 0, -0.1), (0, 0.25, 0.45), (0, 0.55, 0.85), (0, 0.72, 1.15)], [0.2, 0.13, 0.12, 0.15], neck, sk, ring=12)
    head = empty(name + "_Head", _V((0, 0.78, 1.25)), col=COL_CHARS, parent=neck)
    head.rotation_euler = (math.radians(-6), math.radians(-30), 0)      # the tilt, face pushed out at you
    A, B, Cz = 0.56, 0.58, 1.0

    def skull_xyz(x, y, z):
        w = 1.0 - 0.35 * max(0.0, -z) ** 1.3
        return (x * A * w, y * B * (0.85 if y > 0 else 1.0) * (1 - 0.15 * max(0, -z)), z * Cz)

    sk_ob = bpy.data.objects.new(name + "_Skull", bpy.data.meshes.new(name + "_Skull")); COL_CHARS.objects.link(sk_ob)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1)
    for v in bm.verts: v.co = _V(skull_xyz(*v.co))        # long skull, narrow pointed chin, flatter face
    bm.to_mesh(sk_ob.data); bm.free()
    for p in sk_ob.data.polygons: p.use_smooth = True
    sk_ob.parent = head; sk_ob.location = (0, 0, 0.5); sk_ob.data.materials.append(sk)

    def on_head(x, z, out=0.0):
        """point on the front surface of the skull (head space)"""
        zz = (z - 0.5) / Cz
        w = 1.0 - 0.35 * max(0.0, -zz) ** 1.3
        xx = x / (A * w)
        y = B * 0.85 * (1 - 0.15 * max(0, -zz)) * math.sqrt(max(0.0, 1 - xx * xx - zz * zz))
        return (x, y + out, z)

    for sx, rr, zz in ((-0.22, 0.19, 0.7), (0.21, 0.16, 0.75)):           # deep black sockets, pin-point glowing eyes
        _blob(name + "_Socket", on_head(sx, zz, -0.04), (rr, 0.1, rr * 1.3), head, hole, rot=(0, 0, -sx * 0.6))
        e = _blob(name + "_Eye", on_head(sx * 0.95, zz - 0.02, 0.03), (rr * 0.36, 0.03, rr * 0.42), head, eye, seg=16)
        e.visible_shadow = False
        P.setdefault("eyes", []).append(e)
    # grin: cheek to cheek, thin and stretched, glowing from inside, packed with thin crooked teeth
    rr_ = _rnd.Random(13)
    n = 22; top, bot = [], []
    for i in range(n + 1):
        u = i / n; x = -0.48 + 0.96 * u; s_ = math.sin(u * math.pi)
        zt = 0.22 + 0.24 * (2 * u - 1) ** 2                    # corners pulled way up
        zb = zt - 0.04 - 0.3 * s_ ** 0.7
        top.append((x, zt)); bot.append((x, zb))
    bm = bmesh.new(); vt = [bm.verts.new(on_head(x, z, 0.008)) for x, z in top]; vb = [bm.verts.new(on_head(x, z, 0.008)) for x, z in bot]
    for i in range(n): bm.faces.new((vt[i], vt[i + 1], vb[i + 1], vb[i]))
    mme = bpy.data.meshes.new(name + "_Maw"); bm.to_mesh(mme); bm.free()
    mo = bpy.data.objects.new(name + "_Maw", mme); COL_CHARS.objects.link(mo); mo.parent = head; mme.materials.append(maw)
    mo.visible_shadow = False; P["maw"] = mo
    for i in range(1, n):
        for (x, z), (x2, z2), down in ((top[i], bot[i], -1), (bot[i], top[i], 1)):
            if rr_.random() < 0.3: continue
            ln = abs(z2 - z) * rr_.uniform(0.35, 0.6)
            a = on_head(x, z, 0.014); b = on_head(x + rr_.uniform(-0.012, 0.012), z + down * ln, 0.018)
            _tube(name + "_Tooth", [a, b], [0.014 + 0.006 * rr_.random(), 0.002], head, tooth, n=2, ring=6)
    P.update(hips=hips, neck=neck, head=head)
    return P
