# lookdev.py - CINEMATIC LOOK for every shot (Joel 22 Nov 22:10: "good lighting can make or break a scene").
# Post only, almost free to render: AgX + contrast look, a gentle bloom on practicals (lamps, door gap, torch, screens),
# a soft vignette, and a light split-tone (cool shadows, warm highlights). Lighting recipes (motivated key, low fill,
# rim for separation, warm/cool contrast) live in the scene scripts; this file only grades.
import bpy


def cinematic_look(scene=None, exposure=0.0, bloom=0.5, vignette=0.32, split=True, look="AgX - Medium High Contrast", fringe=0.012):
    s = scene or bpy.context.scene
    s.view_settings.view_transform = "AgX"
    try: s.view_settings.look = look
    except Exception: pass
    s.view_settings.exposure = exposure
    ng = bpy.data.node_groups.get("CineLook") or bpy.data.node_groups.new("CineLook", "CompositorNodeTree")
    ng.nodes.clear()
    if not ng.interface.items_tree:
        ng.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput"); cur = gi.outputs[0]
    if bloom:
        g = N.new("CompositorNodeGlare")
        for k, v in (("Type", "Bloom"), ("Quality", "Medium"), ("Threshold", 0.9), ("Strength", bloom), ("Size", 0.5)):
            try: g.inputs[k].default_value = v
            except Exception: pass
        L.new(cur, g.inputs["Image"]); cur = g.outputs[0]
    if fringe:                                                   # a hair of lens colour fringing at the frame edges (glass, not CG)
        ld = N.new("CompositorNodeLensdist")
        for k, v in (("Distortion", 0.0), ("Dispersion", fringe)):
            try: ld.inputs[k].default_value = v
            except Exception: pass
        L.new(cur, ld.inputs["Image"]); cur = ld.outputs[0]
    if split:
        cb = N.new("CompositorNodeColorBalance")
        try:
            cb.inputs["Factor"].default_value = 1.0
        except Exception: pass
        for sock, val in (("Lift", (0.97, 1.0, 1.05, 1)), ("Gain", (1.03, 1.0, 0.96, 1))):   # cool shadows, warm highlights
            for i in cb.inputs:
                if i.name == sock and i.bl_idname == "NodeSocketColor": i.default_value = val
        L.new(cur, cb.inputs["Image"]); cur = cb.outputs[0]
    if vignette:
        em = N.new("CompositorNodeEllipseMask")
        em.inputs["Size"].default_value = (0.95, 0.98); em.inputs["Value"].default_value = 1.0
        bl = N.new("CompositorNodeBlur"); bl.inputs["Size"].default_value = (260, 260)
        L.new(em.outputs[0], bl.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = vignette
        L.new(cur, mx.inputs[6])
        inv = N.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"; inv.inputs[1].default_value = 0.6; inv.inputs[2].default_value = 0.4
        L.new(bl.outputs[0], inv.inputs[0])                       # mask 0..1 -> 0.4..1.0 (corners never go black)
        L.new(inv.outputs[0], mx.inputs[7])
        cur = mx.outputs[2]
    L.new(cur, go.inputs[0])
    s.compositing_node_group = ng
    s.render.use_compositing = True
    return ng


# NOTE: ShaderNodeMix in RGBA mode: colour sockets are inputs[6]/[7] and outputs[2] (["A"]/["Result"] hit the hidden float ones)
# ------------------------------------------------------------------ SOFT LOOK (Joel 23 Nov 01:13 reference clips)
# What the refs do: big soft sources that wrap and fall off (no hard-edged pools), surfaces with grit for the light to
# rake across, halation/bloom round hot light, dust in the beams, grain. All cheap: no volumes, no extra bounces.
def soften_lights(datas, mult=7.0, min_r=1.4, blend=0.85, area_mult=1.6):
    """Spots: much bigger radius (soft shadow edge, wraps round heads) and a feathered cone; areas a bit bigger."""
    for d in datas:
        if d.type == "SPOT":
            d.shadow_soft_size = max(d.shadow_soft_size * mult, min_r); d.spot_blend = blend
        elif d.type == "AREA":
            d.size = d.size * area_mult
            try: d.size_y = d.size_y * area_mult
            except Exception: pass


def grit(strength=0.12, scale=220.0, skip=("Face", "Eye", "Mouth", "Screen", "Text", "Emis", "Glow", "Light")):
    """Micro surface break-up on every non-image Principled material: fine noise bump + roughness variation,
    so a soft key rakes across plastic/fabric/wood instead of sliding off a perfect CG surface."""
    n = 0
    for m in bpy.data.materials:
        if not m.use_nodes or any(k in m.name for k in skip): continue
        nt = m.node_tree; P = nt.nodes.get("Principled BSDF")
        if P is None or P.inputs["Normal"].is_linked: continue
        if any(x.type == "TEX_IMAGE" for x in nt.nodes): continue
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = 0.02
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
        if not P.inputs["Roughness"].is_linked:
            r0 = P.inputs["Roughness"].default_value
            mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = max(0.0, r0 - 0.15)
            mr.inputs["To Max"].default_value = min(1.0, r0 + 0.1)
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], P.inputs["Roughness"])
        n += 1
    print("GRIT on", n, "materials"); return n


def dust(name, centre, size=(6, 6, 6), count=220, seed=3, emit=0.5, col=(0.85, 0.9, 1.0)):
    """Specks floating in a light beam (tiny emissive-ish cubes that drift): reads as air without a volume."""
    import random
    rnd = random.Random(seed)
    me = bpy.data.meshes.new(name); verts = []; faces = []
    for i in range(count):
        c = [centre[k] + (rnd.random() - 0.5) * size[k] for k in range(3)]; r = 0.004 + rnd.random() * 0.006
        b = len(verts)
        verts += [(c[0] + dx * r, c[1] + dy * r, c[2] + dz * r) for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
        faces += [(b, b + 1, b + 3, b + 2), (b + 4, b + 6, b + 7, b + 5), (b, b + 4, b + 5, b + 1),
                  (b + 2, b + 3, b + 7, b + 6), (b, b + 2, b + 6, b + 4), (b + 1, b + 5, b + 7, b + 3)]
    me.from_pydata(verts, [], faces)
    mt = bpy.data.materials.new(name + "M"); mt.use_nodes = True; P = mt.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*col, 1); P.inputs["Emission Color"].default_value = (*col, 1)
    P.inputs["Emission Strength"].default_value = emit; P.inputs["Alpha"].default_value = 0.6
    me.materials.append(mt)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.visible_shadow = False
    return o


def halation(ng, amount=0.08, tint=(1.0, 0.3, 0.15, 1)):
    """Film halation: a wide red-orange glow off hot highlights, added after the main grade (CineLook group)."""
    N, L = ng.nodes, ng.links
    go = [n for n in N if n.type == "GROUP_OUTPUT"][0]
    src = go.inputs[0].links[0].from_socket
    g = N.new("CompositorNodeGlare")
    for k, v in (("Type", "Fog Glow"), ("Quality", "Medium"), ("Threshold", 1.0), ("Strength", 1.0), ("Size", 0.6)):
        try: g.inputs[k].default_value = v
        except Exception: pass
    L.new(src, g.inputs["Image"])
    # glow only (glare - source), tinted, added back
    sub = N.new("ShaderNodeMix"); sub.data_type = "RGBA"; sub.blend_type = "SUBTRACT"; sub.inputs["Factor"].default_value = 1
    L.new(g.outputs[0], sub.inputs[6]); L.new(src, sub.inputs[7])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
    L.new(sub.outputs[2], mul.inputs[6]); mul.inputs[7].default_value = tint
    add = N.new("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"; add.inputs["Factor"].default_value = amount
    L.new(src, add.inputs[6]); L.new(mul.outputs[2], add.inputs[7])
    L.new(add.outputs[2], go.inputs[0])


def shadow_cool(ng, tint=(0.8, 0.92, 1.2, 1), amount=0.8):
    """Cool the SHADOWS only (luminance mask), so skin and the deepest blacks stay neutral (no Instagram tint)."""
    N, L = ng.nodes, ng.links
    go = [n for n in N if n.type == "GROUP_OUTPUT"][0]
    src = go.inputs[0].links[0].from_socket
    bw = N.new("CompositorNodeRGBToBW"); L.new(src, bw.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.02; mr.inputs["From Max"].default_value = 0.35
    mr.inputs["To Min"].default_value = amount; mr.inputs["To Max"].default_value = 0.0
    L.new(bw.outputs[0], mr.inputs["Value"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    L.new(mr.outputs["Result"], mx.inputs["Factor"]); L.new(src, mx.inputs[6]); mx.inputs[7].default_value = tint
    L.new(mx.outputs[2], go.inputs[0])


# ------------------------------------------------------------------ REAL LOOK (Joel 23 Nov 08:46: "realistic good lighting")
# Physical sizes and colour temperatures; colour comes from the sources, the grade stays near neutral.
#   moon through a window: crisp-edged patch (small source), bluish ~ 7500K as film convention;
#   sky/bounce fill: big and soft, cool; practicals: tungsten 2700K, sodium ~2000K, torch LED 5000K.
def kelvin(k):
    """Approx. blackbody RGB (linear-ish) normalised to max 1, from Tanner Helland's fit."""
    import math
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    m = max(c); return tuple(x / m for x in c)          # sRGB-ish fit used as-is: tungsten reads warm, not orange


# Moon/sky as cinema renders them (day-for-night convention: clearly blue, ~ the eye's scotopic shift), not literal 4100K.
REAL_RGB = {"Moon": (0.52, 0.66, 1.0), "RoomFill": (0.42, 0.56, 1.0), "RaeMoon": (0.5, 0.64, 1.0), "YardRim": (0.55, 0.68, 1.0),
            "RaeRim": (0.55, 0.68, 1.0), "ClosetIn": (0.6, 0.7, 1.0)}
REAL_TEMP = {
             "Door": 2700, "Fairy": 2400, "WinGlow": 2700, "MiloKey": 2900, "Sodium": 2000, "RunKey": 2100}


def real_lights(lights):
    for k, d in lights.items():
        for pre, c in REAL_RGB.items():
            if k.startswith(pre): d.color = c; break
        else:
            for pre, K in REAL_TEMP.items():
                if k.startswith(pre): d.color = kelvin(K); break
        if d.type == "SPOT":
            if k.startswith("Moon"): d.shadow_soft_size = 0.35; d.spot_blend = 0.5      # crisp window patch, soft cone edge
            else: d.shadow_soft_size = max(d.shadow_soft_size, 0.8); d.spot_blend = 0.7   # lamp heads are not points
        elif d.type == "AREA" and k.startswith(("RoomFill", "RaeMoon")):
            d.size = d.size * 1.8                                                      # sky bounce is huge and soft


def white_balance(ng, mult=(0.8, 0.92, 1.2, 1)):
    """Camera white balance set for tungsten (~3200K), the real night-shoot practice: moonlight goes blue,
    tungsten practicals read warm-neutral, and black stays black (a multiply, unlike a lift tint)."""
    N, L = ng.nodes, ng.links
    go = [n for n in N if n.type == "GROUP_OUTPUT"][0]
    src = go.inputs[0].links[0].from_socket
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    L.new(src, mx.inputs[6]); mx.inputs[7].default_value = mult; L.new(mx.outputs[2], go.inputs[0])
