# rs_world.py - RESPAWN: the LANTERNFALL world (exec'd after the scene kit, before boot()).
# @world("lanternfall"): Bloxbury's primitives + character engine only (no town), its own sky + sun.
# Builders (call after boot + load("props4", "studio", "lookdev")): market square + apple stall (checkpoint), timber
# houses, bell tower, lantern posts, side stalls, back alley, inn stairs, cellar, Theo's bedroom + laptop, respawn ring,
# THE HAND. Production look (CLAUDE.md): warm practicals vs cool fill, rims, haze/shaft cards, rich procedural textures.
# Blender coords, z up, front = +Y. Sets sit far apart: market (0,0), alley (300,0), inn (300,200), cellar (300,400),
# bedroom (600,0).
import math, random
from mathutils import Vector as _LV
from PIL import Image, ImageDraw, ImageFilter

DG = math.radians


@world("lanternfall")
def _lanternfall(patches=()):
    """Primitives (box/mat/key/R/RS/collections/fonts) + the R6 character section of the Part 1 script, no town."""
    src = open(SCR + "bloxbury_part1.py").read()
    exec(src[:src.index("# ---------------------------------------------------------------- GROUND + ROAD")], _G)
    exec(src[src.index("# ---------------------------------------------------------------- CHARACTERS"):
             src.index("# ---------------------------------------------------------------- TREES + HILLS")], _G)
    _G["RB"] = _G["R"]; _G["FPS"] = 24; _G["WARP"] = []
    _G["HOUSE_LIGHTS"] = []; _G["LAMPS"] = []
    sc = bpy.context.scene
    w = bpy.data.worlds.new("LanternfallSky"); sc.world = w
    try: w.use_nodes = True
    except Exception: pass
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N["Background"]; tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.02; ramp.color_ramp.elements[1].position = 0.4
    L.new(ramp.outputs["Color"], bg.inputs["Color"])
    _G["SKY"] = dict(ramp=ramp, bg=bg)
    sd = bpy.data.lights.new("Sun", "SUN"); sd.angle = DG(4)
    sun = bpy.data.objects.new("Sun", sd); sc.collection.objects.link(sun)
    _G["SUN"] = sun


# ================================================================== time of day (keyed per shot, CONSTANT at cuts)
LOOKS = {   # sun energy, sun colour, sun dir (to the sun), sky horizon, sky top, sky strength
    "noon":   (4.2, (255, 238, 210), (0.35, -0.55, 0.78), (236, 214, 178), (120, 170, 225), 0.9),
    "sunset": (3.2, (255, 150, 80), (0.2, -1.0, 0.2), (255, 150, 90), (70, 80, 140), 0.7),
    "dusk":   (0.5, (150, 160, 255), (-0.6, 0.4, 0.5), (60, 70, 120), (12, 16, 40), 0.35),
    "night":  (0.35, (130, 150, 255), (0.3, 0.6, 0.75), (22, 28, 52), (6, 8, 20), 0.25),
    "dim":    (2.0, (230, 220, 210), (0.35, -0.55, 0.78), (170, 160, 150), (90, 110, 140), 0.45),
    "inside": (0.0, (255, 255, 255), (0, 0, 1), (8, 10, 18), (4, 5, 10), 0.1),
}


def kx(db, path, fr, value, interp="BEZIER"):
    """kf() for anything (node sockets, ramp elements, view settings): logs the owning ID so apply_interp finds it."""
    setattr(db, path, value); db.keyframe_insert(path, frame=fr)
    try: full = db.path_from_id(path)
    except Exception: full = path
    _LOG.append((db.id_data, full, fr, interp))


def kc(datablock, path, fr, value):
    kx(datablock, path, fr, value, interp="CONSTANT")


def time_of_day(fr, name):
    e, col, d, hz, top, st = LOOKS[name]
    sd = SUN.data
    kc(sd, "energy", fr, e); kc(sd, "color", fr, lin(col))
    kc(SUN, "rotation_euler", fr, _LV(d).to_track_quat("Z", "Y").to_euler())
    r = SKY["ramp"].color_ramp
    kc(r.elements[0], "color", fr, (*lin(hz), 1)); kc(r.elements[1], "color", fr, (*lin(top), 1))
    kc(SKY["bg"].inputs["Strength"], "default_value", fr, st)


# ================================================================== materials (shared, procedural texture = "rich")
def stone_mat(name, rgb, scale=1.6, rough=0.85, mortar=0.04, bump=0.55, row=0.55, width=1.0):
    """Cobbles / ashlar: brick texture + noise colour break-up + strong bump (light rakes across it)."""
    if name in _DM: return _DM[name]
    m = bpy.data.materials.new(name); nt, Nn, Ll, b = _nodes(m)
    tc = Nn.new("ShaderNodeTexCoord")
    br = Nn.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale
    br.inputs["Brick Width"].default_value = width; br.inputs["Row Height"].default_value = row
    br.inputs["Mortar Size"].default_value = mortar; br.inputs["Mortar Smooth"].default_value = 0.4
    col = lin(rgb)
    br.inputs["Color1"].default_value = (*[c * 0.82 for c in col], 1); br.inputs["Color2"].default_value = (*[c * 1.12 for c in col], 1)
    br.inputs["Mortar"].default_value = (*[c * 0.4 for c in col], 1)
    Ll.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = Nn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8
    Ll.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = Nn.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.45
    Ll.new(br.outputs["Color"], mx.inputs[6]); Ll.new(nz.outputs["Color"], mx.inputs[7])
    Ll.new(mx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    bp = Nn.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.invert = True
    ad = Nn.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; ad.inputs[1].default_value = 1.0; ad.inputs[2].default_value = 0.0
    Ll.new(br.outputs["Fac"], ad.inputs[0])
    ad2 = Nn.new("ShaderNodeMath"); ad2.operation = "MULTIPLY_ADD"; ad2.inputs[1].default_value = 0.25
    Ll.new(nz.outputs["Fac"], ad2.inputs[0]); Ll.new(ad.outputs[0], ad2.inputs[2])
    Ll.new(ad2.outputs[0], bp.inputs["Height"]); Ll.new(bp.outputs["Normal"], b.inputs["Normal"])
    _DM[name] = m; return m


def plaster_mat(name, rgb): return tex_mat(name, rgb, "plaster", rough=0.9)


def wood_mat(name, rgb, scale=3.0): return wood(name, rgb, scale=scale, rough=0.7)


def tiles_mat(name, rgb): return stone_mat(name, rgb, scale=2.4, rough=0.7, mortar=0.06, bump=0.7, row=0.5, width=0.7)


def glowm(name, rgb, strength): return dmat(name, rgb, emit=strength, emit_rgb=rgb)


LFM = {}


def _lfm():
    if LFM: return LFM
    LFM.update(
        cobble=stone_mat("lf_cobble", (150, 140, 128), scale=1.9, bump=0.8, mortar=0.06, row=0.5, width=0.8),
        ashlar=stone_mat("lf_ashlar", (176, 166, 150), scale=0.9, row=0.5, width=1.2, bump=0.5),
        darkstone=stone_mat("lf_darkstone", (96, 92, 92), scale=1.1, row=0.5, width=1.0, bump=0.6),
        beam=wood_mat("lf_beam", (70, 46, 30), 2.0), plank=wood_mat("lf_plank", (140, 98, 60), 4.0),
        oldwood=wood_mat("lf_oldwood", (104, 78, 56), 5.0),
        iron=dmat("lf_iron", (34, 32, 34), rough=0.45, metal=0.8), brass=dmat("lf_brass", (196, 150, 70), rough=0.3, metal=0.9),
        roof_red=tiles_mat("lf_roof_red", (132, 64, 46)), roof_slate=tiles_mat("lf_roof_slate", (70, 74, 86)),
        lamp=glowm("lf_lampglow", (255, 186, 96), 9.0), window=glowm("lf_winglow", (255, 176, 92), 2.2),
        win_dark=dmat("lf_windark", (28, 30, 38), rough=0.25),
        cloth_red=fabric("lf_cloth_red", (176, 44, 40)), cloth_cream=fabric("lf_cloth_cream", (232, 214, 180)),
        sack=fabric("lf_sack", (180, 150, 104)), apple=dmat("lf_apple", (196, 28, 30), rough=0.32),
        apple2=dmat("lf_apple2", (220, 60, 34), rough=0.35), leaf=dmat("lf_leaf", (60, 120, 50), rough=0.6),
        stem=dmat("lf_stem", (70, 48, 30), rough=0.8), black=dmat("lf_black", (4, 4, 5), rough=0.9),
    )
    return LFM


PLASTERS = [(232, 220, 196), (214, 196, 160), (196, 206, 196), (226, 200, 186), (208, 200, 220), (236, 226, 206)]


# ================================================================== small props
def apple(name, loc, parent, k=0, s=0.36):
    m = _lfm()
    a = ball(name, (s, s, s * 0.92), V(loc), m["apple" if k % 3 else "apple2"], parent)
    rb(name + "Stem", (0.04, 0.04, 0.14), V(loc) + V((0, 0, s * 0.5)), m["stem"], parent, r=0.01)
    return a


def crate(name, loc, parent, w=2.2, d=1.5, h=1.0, apples=True, seed=0, yaw=0):
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.parent = parent; r.rotation_euler = (0, 0, DG(yaw))
    for sy in (-1, 1): rb(name + "Side", (w, 0.12, h), V((0, sy * (d / 2 - 0.06), h / 2)), m["plank"], r, r=0.03)
    for sx in (-1, 1): rb(name + "End", (0.12, d, h), V((sx * (w / 2 - 0.06), 0, h / 2)), m["plank"], r, r=0.03)
    for zz in (0.25, 0.75):
        rb(name + "Slat", (w + 0.02, 0.05, 0.16), V((0, -d / 2 - 0.01, h * zz)), m["oldwood"], r, r=0.02)
    rb(name + "Base", (w, d, 0.1), V((0, 0, 0.05)), m["plank"], r, r=0.02)
    if apples:
        rng = random.Random(seed); k = 0
        for ix in range(int(w / 0.42)):
            for iy in range(int(d / 0.42)):
                x = -w / 2 + 0.3 + ix * 0.42 + rng.uniform(-0.04, 0.04); y = -d / 2 + 0.3 + iy * 0.42 + rng.uniform(-0.04, 0.04)
                apple(name + "Ap", (x, y, h - 0.05 + rng.uniform(0, 0.12)), r, k); k += 1
    return r


def barrel(name, loc, parent=None, h=2.4, rad=0.95, yaw=0):
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.parent = parent; r.rotation_euler = (0, 0, DG(yaw))
    rcyl(name + "Body", rad, h, V((0, 0, h / 2)), m["oldwood"], r, seg=18, bevel=0.15)
    rcyl(name + "Belly", rad * 1.07, h * 0.5, V((0, 0, h / 2)), m["oldwood"], r, seg=18, bevel=0.2)
    for z in (0.18, 0.82):
        rcyl(name + "Hoop", rad * 1.04, 0.12, V((0, 0, h * z)), m["iron"], r, seg=18, bevel=0.03)
    rcyl(name + "Lid", rad * 0.92, 0.06, V((0, 0, h + 0.01)), m["plank"], r, seg=18, bevel=0.02)
    return r


def sack(name, loc, parent=None, s=1.0):
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.parent = parent
    ball(name + "Body", (1.1 * s, 0.9 * s, 1.2 * s), V((0, 0, 0.55 * s)), m["sack"], r)
    rcyl(name + "Tie", 0.16 * s, 0.25 * s, V((0, 0, 1.15 * s)), dmat("lf_rope", (150, 120, 80), rough=0.9), r, seg=10)
    return r


def lantern(name, loc, parent=None, s=1.0, light=None, col=(255, 170, 90), radius=0.25):
    """Iron lantern: cap, 4 posts, glowing panes, ring on top. Optional small point light (the practical)."""
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.parent = parent
    g_ = rb(name + "Glow", (0.6 * s, 0.6 * s, 0.8 * s), V((0, 0, 0)), m["lamp"], r, r=0.05); g_.visible_shadow = False
    for sx in (-1, 1):
        for sy in (-1, 1): rb(name + "Post", (0.08 * s, 0.08 * s, 0.95 * s), V((sx * 0.32 * s, sy * 0.32 * s, 0)), m["iron"], r, r=0.02)
    taper(name + "Cap", (0.85 * s, 0.85 * s, 0.35 * s), V((0, 0, 0.55 * s)), m["iron"], r, top=(0.3, 0.3), r=0.04)
    rb(name + "Base", (0.8 * s, 0.8 * s, 0.1 * s), V((0, 0, -0.45 * s)), m["iron"], r, r=0.03)
    rcyl(name + "Ring", 0.14 * s, 0.05 * s, V((0, 0, 0.8 * s)), m["iron"], r, axis="Y", seg=12)
    ld = None
    if light is not None:
        ld = bpy.data.lights.new(name + "L", "POINT"); ld.energy = light; ld.color = lin(col); ld.shadow_soft_size = radius
        o = bpy.data.objects.new(name + "L", ld); s_ = bpy.context.scene; s_.collection.objects.link(o)
        o.parent = r; o.location = V((0, 0, 0))
    return r, ld


def lamp_post(name, loc, parent=None, light=600.0, h=8.5):
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.parent = parent
    rcyl(name + "Foot", 0.45, 0.6, V((0, 0, 0.3)), m["iron"], r, seg=12)
    rcyl(name + "Pole", 0.16, h, V((0, 0, h / 2)), m["iron"], r, seg=12)
    rb(name + "Arm", (1.3, 0.1, 0.1), V((0.55, 0, h - 0.2)), m["iron"], r, r=0.03)
    rb(name + "Scroll", (0.1, 0.1, 0.7), V((0.35, 0, h - 0.6)), m["iron"], r, r=0.03, rot=(0, DG(-35), 0))
    lt, ld = lantern(name + "Lan", (1.15, 0, h - 1.0), r, s=0.9, light=light)
    return r, lt, ld


def bunting(name, a, b, n=14, sag=0.9, parent=None, seed=0):
    rng = random.Random(seed); a, b = V(a), V(b)
    cols = [(196, 44, 40), (232, 200, 90), (60, 110, 170), (232, 222, 200), (70, 140, 80)]
    pts = []
    for i in range(n + 1):
        u = i / n; p = a.lerp(b, u) - V((0, 0, sag * 4 * u * (1 - u))); pts.append(p)
    tube(name + "Line", pts, 0.03, dmat("lf_rope", (150, 120, 80), rough=0.9), parent)
    d = (b - a).normalized(); yaw = math.atan2(d.y, d.x)
    for i in range(1, n):
        p = pts[i]; c = cols[(i + seed) % len(cols)]
        f = taper(name + "Flag", (0.6, 0.04, 0.8), p - V((0, 0, 0.42)), fabric("lf_flag%d" % ((i + seed) % len(cols)), c),
                  parent, top=(1.0, 1.0), r=0.01, rot=(0, 0, yaw))
        f.scale = (1, 1, 1); f.data.vertices  # flags: thin tapered pennants
        for v in f.data.vertices:
            if v.co.z < 0: v.co.x *= 0.05
    return pts


# ================================================================== buildings
def timber_house(name, loc, yaw, w=10.0, d=8.0, h1=7.0, h2=6.0, col=None, roof="red", seed=0, sign=None, door=True):
    """Half-timbered house, front = local -Y (faces the square): plaster walls with dark beams (posts, rails, braces),
    jettied upper floor, steep tiled gable roof, warm/dark leaded windows, plank door + iron studs, chimney, optional
    hanging sign. Roof ridge runs along X (walkable)."""
    m = _lfm(); rng = random.Random(seed); col = col or PLASTERS[seed % len(PLASTERS)]
    r = empty(name, V(loc), col=COL_PROPS); r.rotation_euler = (0, 0, DG(yaw))
    pm = plaster_mat("lf_plaster%d" % (seed % len(PLASTERS)), col)
    rb(name + "Ground", (w, d, h1), V((0, 0, h1 / 2)), pm, r, r=0.05)
    rb(name + "Plinth", (w + 0.3, d + 0.3, 1.0), V((0, 0, 0.5)), m["darkstone"], r, r=0.08)
    j = 0.7                                                      # jetty: upper floor overhangs the front
    rb(name + "Upper", (w + 0.4, d + j, h2), V((0, -j / 2, h1 + h2 / 2)), pm, r, r=0.05)
    rb(name + "Jetty", (w + 0.6, d + j + 0.2, 0.45), V((0, -j / 2, h1 + 0.1)), m["beam"], r, r=0.06)
    fy0, fy1 = -d / 2 - 0.06, -d / 2 - j - 0.06
    for k in range(5):                                           # beams: posts on both floors + rails + braces
        x = -w / 2 + k * w / 4
        rb(name + "Post", (0.38, 0.14, h1 - 1.0), V((x, fy0, 1.0 + (h1 - 1.0) / 2)), m["beam"], r, r=0.04)
        rb(name + "PostU", (0.38, 0.14, h2), V((x * (w + 0.4) / w, fy1, h1 + h2 / 2)), m["beam"], r, r=0.04)
    rb(name + "Rail", (w + 0.4, 0.14, 0.3), V((0, fy1, h1 + h2 * 0.45)), m["beam"], r, r=0.04)
    rb(name + "RailTop", (w + 0.4, 0.14, 0.32), V((0, fy1, h1 + h2 - 0.15)), m["beam"], r, r=0.04)
    for k in range(4):
        xa = -w / 2 + k * w / 4 + w / 8; sgn = 1 if k % 2 else -1
        rb(name + "Brace", (0.3, 0.12, h2 * 0.5), V((xa * (w + 0.4) / w, fy1 - 0.01, h1 + h2 * 0.22)), m["beam"], r, r=0.03,
           rot=(0, DG(sgn * 38), 0))
    # side beams
    for sx in (-1, 1):
        for yy in (-d / 2, 0, d / 2):
            rb(name + "SidePost", (0.14, 0.38, h1 - 1.0), V((sx * (w / 2 + 0.06), yy, 1.0 + (h1 - 1.0) / 2)), m["beam"], r, r=0.04)
    # windows (upper: two lit/dark leaded windows with shutters; ground: one + door)
    lit = [rng.random() < 0.55 for _ in range(3)]
    for k, x in enumerate((-w / 4, w / 4)):
        wm = m["window"] if lit[k] else m["win_dark"]
        rb(name + "Win", (1.8, 0.12, 2.1), V((x, fy1 - 0.02, h1 + h2 * 0.62)), wm, r, r=0.04)
        rb(name + "Mull", (0.1, 0.16, 2.1), V((x, fy1 - 0.06, h1 + h2 * 0.62)), m["beam"], r, r=0.02)
        rb(name + "Trans", (1.8, 0.16, 0.1), V((x, fy1 - 0.06, h1 + h2 * 0.62 + 0.2)), m["beam"], r, r=0.02)
        rb(name + "Sill", (2.3, 0.4, 0.18), V((x, fy1 - 0.2, h1 + h2 * 0.62 - 1.15)), m["beam"], r, r=0.04)
        for sx in (-1, 1):
            rb(name + "Shutter", (0.85, 0.1, 2.2), V((x + sx * 1.42, fy1 - 0.05, h1 + h2 * 0.62)),
               dmat("lf_shutter%d" % (seed % 3), [(70, 100, 80), (120, 60, 50), (60, 80, 120)][seed % 3], rough=0.7), r, r=0.04)
        if rng.random() < 0.6:                                   # flower box
            rb(name + "FBox", (2.0, 0.5, 0.45), V((x, fy1 - 0.4, h1 + h2 * 0.62 - 1.45)), m["plank"], r, r=0.05)
            for q in range(4):
                ball(name + "Flower", (0.32, 0.32, 0.3), V((x - 0.7 + q * 0.47, fy1 - 0.4, h1 + h2 * 0.62 - 1.12)),
                     dmat("lf_flower%d" % (q % 3), [(200, 50, 70), (240, 200, 80), (160, 90, 200)][q % 3], rough=0.6), r)
    gx = -w / 4 if door else 0
    wm = m["window"] if lit[2] else m["win_dark"]
    rb(name + "WinG", (2.2, 0.12, 1.8), V((w / 4, fy0 - 0.02, 3.6)), wm, r, r=0.04)
    for q in (-0.37, 0.37): rb(name + "MullG", (0.1, 0.16, 1.8), V((w / 4 + q, fy0 - 0.06, 3.6)), m["beam"], r, r=0.02)
    rb(name + "LintelG", (2.6, 0.3, 0.3), V((w / 4, fy0 - 0.1, 4.6)), m["beam"], r, r=0.04)
    if door:
        rb(name + "Door", (2.2, 0.14, 4.0), V((gx, fy0 - 0.03, 3.0)), wood_mat("lf_door", (92, 58, 36), 6.0), r, r=0.05)
        rb(name + "DoorFrame", (2.7, 0.24, 0.35), V((gx, fy0 - 0.08, 5.1)), m["beam"], r, r=0.05)
        for zz in (2.0, 4.0):
            rb(name + "Strap", (2.0, 0.06, 0.16), V((gx, fy0 - 0.12, zz)), m["iron"], r, r=0.02)
        rcyl(name + "Ring", 0.18, 0.05, V((gx + 0.6, fy0 - 0.14, 3.0)), m["iron"], r, axis="Y", seg=12)
        rb(name + "Step", (2.8, 0.9, 0.35), V((gx, fy0 - 0.45, 1.05)), m["darkstone"], r, r=0.06)
    # steep gable roof, ridge along X (two tilted slabs + ridge cap + gable ends)
    ztop = h1 + h2; rh = d * 0.62; ang = math.atan2(rh, (d + j) / 2)
    slab = math.hypot(rh, (d + j) / 2) + 0.9
    rm = m["roof_red" if roof == "red" else "roof_slate"]
    for sy in (-1, 1):
        rb(name + "Roof", (w + 1.6, slab, 0.45), V((0, -j / 2 + sy * (d + j) / 4 + sy * 0.15, ztop + rh / 2 - 0.1)), rm, r, r=0.06,
           rot=(sy * ang, 0, 0))
    rb(name + "Ridge", (w + 1.8, 0.7, 0.45), V((0, -j / 2, ztop + rh + 0.15)), m["beam"], r, r=0.1)
    for sx in (-1, 1):                                           # gable triangle (plaster) as a tapered box
        taper(name + "Gable", (0.3, d + j, rh), V((sx * (w / 2 + 0.05), -j / 2, ztop + rh / 2)), pm, r, top=(1.0, 0.02), r=0.03)
    cx = rng.choice((-1, 1)) * w * 0.28
    rb(name + "Chimney", (1.2, 1.2, rh + 2.2), V((cx, -j / 2 + 0.6, ztop + rh / 2 + 1.0)), m["ashlar"], r, r=0.05)
    rb(name + "ChimCap", (1.5, 1.5, 0.3), V((cx, -j / 2 + 0.6, ztop + rh + 2.15)), m["darkstone"], r, r=0.05)
    if sign:
        rb(name + "SignArm", (0.12, 1.8, 0.12), V((-w / 2 + 0.6, fy1 - 0.9, h1 + 0.9)), m["iron"], r, r=0.03)
        p = sign_img(sign, seed)
        pl = plane(name + "Sign", 1.5, 1.1, V((-w / 2 + 0.6, fy1 - 1.2, h1 + 0.15)), imgmat("lf_sign_" + sign, p, rough=0.7), r,
                   rot=(0, 0, DG(90)))
        rb(name + "SignBack", (0.06, 1.6, 1.2), V((-w / 2 + 0.6 - 0.04, fy1 - 1.2, h1 + 0.15)), m["plank"], r, r=0.02)
    r["roof_z"] = ztop + rh + 0.4
    return r


def sign_img(kind, seed=0):
    im = Image.new("RGB", (300, 220), (104, 72, 44)); d = ImageDraw.Draw(im)
    d.rectangle((8, 8, 291, 211), outline=(196, 150, 70), width=8)
    if kind == "inn":
        d.ellipse((90, 40, 210, 150), fill=(214, 172, 70)); d.rectangle((120, 80, 180, 170), fill=(214, 172, 70))
        d.text((150, 190), "THE LANTERN", font=pfont(30), fill=(236, 220, 190), anchor="mm")
    elif kind == "bread":
        d.ellipse((60, 60, 240, 160), fill=(214, 160, 90))
        for x in (110, 150, 190): d.line((x - 15, 80, x + 15, 140), fill=(150, 100, 50), width=8)
    elif kind == "key":
        d.ellipse((60, 70, 140, 150), outline=(220, 220, 210), width=14); d.rectangle((135, 102, 250, 118), fill=(220, 220, 210))
        d.rectangle((210, 118, 225, 150), fill=(220, 220, 210))
    else:
        d.text((150, 110), kind.upper(), font=pfont(44), fill=(236, 220, 190), anchor="mm")
    return save_img(im, "lf_sign_" + kind)


def bell_tower(name, loc, h=34.0):
    """Stone bell tower: ashlar shaft with corner quoins, clock face (generated image), open belfry with a bronze
    bell, pointed slate spire + iron vane. Story beat: the last bell."""
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS)
    w = 7.0
    rb(name + "Shaft", (w, w, h), V((0, 0, h / 2)), m["ashlar"], r, r=0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(int(h / 2.4)):
                rb(name + "Quoin", (0.8, 0.8, 1.1), V((sx * w / 2, sy * w / 2, 1.2 + k * 2.4)), m["darkstone"], r, r=0.06)
    rb(name + "Band", (w + 0.6, w + 0.6, 0.6), V((0, 0, h - 0.3)), m["darkstone"], r, r=0.08)
    bz = h + 3.5                                                 # belfry: four corner piers, bell visible through arches
    for sx in (-1, 1):
        for sy in (-1, 1): rb(name + "Pier", (1.6, 1.6, 7.0), V((sx * (w / 2 - 0.8), sy * (w / 2 - 0.8), bz)), m["ashlar"], r, r=0.08)
    rb(name + "BelfryTop", (w + 0.8, w + 0.8, 0.8), V((0, 0, bz + 3.8)), m["darkstone"], r, r=0.08)
    bell = rcyl(name + "Bell", 1.6, 2.6, V((0, 0, bz + 0.6)), dmat("lf_bronze", (150, 104, 50), rough=0.35, metal=0.9), r,
                seg=24, top_scale=0.55)
    rcyl(name + "BellLip", 1.75, 0.35, V((0, 0, bz - 0.6)), dmat("lf_bronze", (150, 104, 50), rough=0.35, metal=0.9), r, seg=24)
    rb(name + "Yoke", (4.6, 0.5, 0.5), V((0, 0, bz + 2.4)), m["beam"], r, r=0.06)
    taper(name + "Spire", (w + 0.8, w + 0.8, 9.0), V((0, 0, bz + 8.7)), m["roof_slate"], r, top=(0.03, 0.03), r=0.05)
    rcyl(name + "Vane", 0.08, 2.4, V((0, 0, bz + 14.3)), m["iron"], r, seg=8)
    rb(name + "VaneArrow", (1.6, 0.06, 0.3), V((0.3, 0, bz + 14.8)), m["iron"], r, r=0.02)
    im = Image.new("RGB", (512, 512), (240, 230, 206)); d = ImageDraw.Draw(im)
    d.ellipse((6, 6, 506, 506), outline=(40, 34, 30), width=18)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.text((256 + 196 * math.sin(a), 256 - 196 * math.cos(a)), "I II III IV V VI VII VIII IX X XI XII".split()[k - 1 if k else 11],
               font=pfont(34), fill=(40, 34, 30), anchor="mm")
    d.line((256, 256, 256, 96), fill=(30, 26, 24), width=14); d.line((256, 256, 256, 150), fill=(30, 26, 24), width=20)   # noon
    d.ellipse((240, 240, 272, 272), fill=(30, 26, 24))
    clk = imgmat("lf_clock", save_img(im, "lf_clock"), rough=0.6)
    for k, yaw in enumerate((0, 90, 180, 270)):
        p = plane(name + "Clock", 4.2, 4.2, V((0, 0, 0)), clk, r)
        a = DG(yaw); p.location = V((math.sin(a) * (w / 2 + 0.06), -math.cos(a) * (w / 2 + 0.06), h - 4.0))
        p.rotation_euler = (0, 0, a + math.pi)
        p.rotation_euler = (0, 0, a)
        rcyl(name + "ClockRim", 2.3, 0.2, p.location + V((0, 0, 0)) * 1.0, m["brass"], r, axis="Y", seg=28,
             rot=(DG(90), 0, a))
    r["bell"] = bell; r["bell_z"] = bz
    return r


# ================================================================== the apple stall (checkpoint) + side stalls
def stripe_img(c1, c2, n=8, name="lf_stripe"):
    im = Image.new("RGB", (512, 256), c1); d = ImageDraw.Draw(im)
    for k in range(n):
        if k % 2: d.rectangle((k * 512 // n, 0, (k + 1) * 512 // n, 256), fill=c2)
    for x in range(0, 512, 32): d.pieslice((x, 216, x + 32, 256 + 40), 180, 360, fill=c1 if (x // 64) % 2 else c2)
    return save_img(im.filter(ImageFilter.GaussianBlur(0.6)), name)


def stall(name, loc, yaw=0, w=7.0, c1=(176, 44, 40), c2=(232, 214, 180), goods="apples", seed=0, lantern_light=0.0):
    """Market stall, customer side = local -Y: plank counter with a front skirt, four poles, striped sloping awning
    with scalloped edge, goods on the counter + crates, chalk price board, hanging lantern."""
    m = _lfm(); r = empty(name, V(loc), col=COL_PROPS); r.rotation_euler = (0, 0, DG(yaw))
    rng = random.Random(seed)
    rb(name + "Counter", (w, 2.4, 0.3), V((0, 0, 3.0)), m["plank"], r, r=0.05)
    rb(name + "Skirt", (w - 0.2, 0.12, 2.6), V((0, -1.15, 1.6)), m["oldwood"], r, r=0.03)
    for k in range(int(w / 0.8)):
        rb(name + "Board", (0.05, 0.16, 2.6), V((-w / 2 + 0.4 + k * 0.8, -1.22, 1.6)), m["beam"], r, r=0.01)
    for sx in (-1, 1):
        for sy, hh in ((-1, 6.6), (1, 7.8)):
            rb(name + "Pole", (0.28, 0.28, hh), V((sx * (w / 2 - 0.15), sy * 1.1, hh / 2)), m["beam"], r, r=0.04)
    aw = imgmat("lf_awning_%d" % seed, stripe_img(c1, c2, name="lf_awning_%d" % seed), rough=0.85)
    ang = math.atan2(7.8 - 6.6, 2.2 + 1.4)
    p = plane(name + "Awning", w + 0.8, 3.9, V((0, -0.5, 7.25)), aw, r, rot=(math.pi / 2 - ang + math.pi / 2, 0, 0))
    p.rotation_euler = (DG(90) + ang - DG(90) + DG(-90) + DG(180) - ang * 2 + ang, 0, 0)
    p.rotation_euler = (-(DG(90) - ang), 0, 0)
    rb(name + "AwnBack", (w + 0.8, 3.9, 0.06), V((0, -0.5, 7.22)), fabric("lf_awn_under%d" % seed, dk(c2, 0.8)), r, r=0.02,
       rot=(ang, 0, 0))
    p.location = V((0, -0.5, 7.27)); p.rotation_euler = (ang + DG(90), 0, 0)
    p.rotation_euler = (DG(90) + ang, 0, 0)
    p.rotation_euler = (-DG(90) + ang, 0, DG(180))
    if goods == "apples":
        for k, x in enumerate((-w / 3, 0, w / 3)):
            crate(name + "Crate%d" % k, (x, 0.1, 3.15), r, w=w / 3 - 0.3, d=1.8, h=0.7, seed=seed + k)
        crate(name + "Floor0", (-w / 2 - 1.4, -0.6, 0), r, w=2.0, d=1.6, h=1.1, seed=seed + 7, yaw=8)
        crate(name + "Floor1", (-w / 2 - 1.3, -0.4, 1.12), r, w=1.8, d=1.4, h=0.9, seed=seed + 8, yaw=-5)
        barrel(name + "Barrel", (w / 2 + 1.3, 0.3, 0), r, h=2.6, rad=0.9)
        rb(name + "Scale", (0.12, 0.12, 1.6), V((w / 2 - 0.6, 0.6, 3.95)), m["brass"], r, r=0.03)
        rb(name + "ScaleBar", (1.4, 0.08, 0.08), V((w / 2 - 0.6, 0.6, 4.75)), m["brass"], r, r=0.02)
        for sx in (-1, 1): rcyl(name + "Pan", 0.36, 0.06, V((w / 2 - 0.6 + sx * 0.65, 0.6, 4.2)), m["brass"], r, seg=16)
        im = Image.new("RGB", (300, 220), (30, 34, 32)); d = ImageDraw.Draw(im)
        d.rectangle((6, 6, 293, 213), outline=(120, 90, 60), width=12)
        d.text((150, 70), "APPLES", font=pfont(46), fill=(236, 236, 226), anchor="mm")
        d.text((150, 150), "2 for 1c", font=pfont(38), fill=(240, 120, 110), anchor="mm")
        d.ellipse((30, 120, 70, 160), fill=(200, 40, 40))
        board = plane(name + "Price", 1.6, 1.15, V((-w / 2 + 1.0, -1.25, 2.1)), imgmat("lf_price", save_img(im, "lf_price"), rough=0.9), r)
        board.rotation_euler = (0, 0, DG(180)); board.rotation_euler = (0, 0, 0)
        board.location = V((-w / 2 + 1.0, -1.27, 2.1)); board.rotation_euler = (0, 0, DG(180))
        board.rotation_euler = (0, 0, 0)
    elif goods == "bread":
        for k in range(9):
            ball(name + "Loaf", (0.9, 0.55, 0.45), V((-w / 2 + 0.8 + k * (w - 1.6) / 8, rng.uniform(-0.6, 0.6), 3.4)),
                 dmat("lf_loaf", (196, 140, 76), rough=0.7), r, rot=(0, 0, rng.uniform(-0.5, 0.5)))
        for k in range(3): sack(name + "Sack%d" % k, (-w / 2 - 1.0 + k * 0.4, -0.4 + k * 0.5, 0), r, s=0.9 + 0.1 * k)
    elif goods == "cloth":
        for k in range(5):
            c = [(60, 100, 160), (170, 60, 90), (220, 180, 80), (70, 130, 90), (140, 80, 160)][k]
            rb(name + "Bolt", (0.8, 2.0, 0.8), V((-w / 2 + 0.9 + k * (w - 1.8) / 4, 0, 3.55)), fabric("lf_bolt%d" % k, c), r, r=0.3)
        for k in range(3):
            c = [(200, 70, 60), (60, 120, 160), (220, 200, 140)][k]
            rb(name + "Hang", (1.2, 0.05, 2.2), V((-w / 2 + 1.5 + k * 1.6, -1.4, 5.3)), fabric("lf_hang%d" % k, c), r, r=0.02)
    lt, ld = lantern(name + "Lan", (w / 2 - 0.15, -1.45, 5.6), r, s=0.7, light=lantern_light)
    rb(name + "LanHook", (0.08, 0.6, 0.08), V((w / 2 - 0.15, -1.25, 6.15)), m["iron"], r, r=0.02)
    r["lantern"] = ld
    return r


# ================================================================== the market square (+ rooftops + the lantern street)
SQUARE_HOUSES = [  # (x, y, yaw, w, d, h1, h2, roof, seed, sign)
    (-24, 30, 0, 11, 9, 7, 6, "red", 0, "inn"), (-11, 31, 0, 9, 9, 6.5, 6, "slate", 1, None),
    (26, 29, 0, 11, 9, 7, 6.5, "red", 2, "bread"), (37, 26, -20, 9, 8, 6.5, 5.5, "slate", 3, None),
    (-34, 14, 90, 12, 9, 7, 6, "red", 4, "key"), (-35, -4, 90, 10, 9, 6.5, 6, "slate", 5, None),
    (-34, -20, 90, 11, 9, 7, 5.5, "red", 6, None), (34, 10, -90, 12, 9, 7, 6.5, "red", 7, None),
    (35, -8, -90, 10, 9, 6.5, 6, "slate", 8, None), (34, -24, -90, 11, 9, 7, 6, "red", 9, None),
    (-24, -38, 180, 10, 9, 7, 6, "red", 10, None), (24, -38, 180, 10, 9, 7, 6, "slate", 11, None),
    (-12, -40, 180, 9, 8, 6.5, 5.5, "red", 12, None), (12, -40, 180, 9, 8, 6.5, 5.5, "red", 13, None),
]


def market_square():
    """Lanternfall market square (noon checkpoint). Returns dict of the pieces the scene needs."""
    m = _lfm(); out = {}
    g = rb("Cobbles", (140, 140, 1.0), V((0, 0, -0.5)), m["cobble"], None, r=0.05)
    rcyl("Fountain", 3.2, 1.4, V((-14, -12, 0.7)), m["ashlar"], None, seg=32)
    rcyl("FountainIn", 2.7, 0.2, V((-14, -12, 1.35)), dmat("lf_water", (40, 70, 90), rough=0.08), None, seg=32)
    rcyl("FountainCol", 0.5, 3.6, V((-14, -12, 2.4)), m["ashlar"], None, seg=16)
    rcyl("FountainBowl", 1.3, 0.5, V((-14, -12, 4.1)), m["ashlar"], None, seg=24, top_scale=1.3)
    out["houses"] = [timber_house("House%d" % k, (x, y, 0), yw, w, d, h1, h2, roof=rf, seed=sd, sign=sg)
                     for k, (x, y, yw, w, d, h1, h2, rf, sd, sg) in enumerate(SQUARE_HOUSES)]
    for k in range(10):                                         # back rows: more roofs behind the square (depth)
        a = k / 10 * 2 * math.pi; rr = 62 + (k % 3) * 6
        timber_house("Far%d" % k, (rr * math.cos(a), rr * math.sin(a), 0), math.degrees(a) + 90, 12, 10, 8, 7,
                     roof="red" if k % 2 else "slate", seed=k + 3, door=False)
    out["tower"] = bell_tower("BellTower", (6, 46, 0))
    out["stall"] = stall("AppleStall", (0, 7, 0), 0, w=7.0, seed=1, lantern_light=0.0)
    out["stalls"] = [stall("BreadStall", (-16, 12, 0), 25, w=6.0, c1=(60, 100, 150), c2=(232, 220, 190), goods="bread", seed=2),
                     stall("ClothStall", (17, 13, 0), -30, w=6.0, c1=(70, 120, 80), c2=(236, 214, 160), goods="cloth", seed=3)]
    for k, (x, y) in enumerate(((-9, 18), (11, -14), (24, -2), (-25, 2), (-6, -22))):
        barrel("SqBarrel%d" % k, (x, y, 0), yaw=k * 40)
        if k % 2: sack("SqSack%d" % k, (x + 1.6, y + 0.4, 0))
    out["posts"] = [lamp_post("Post%d" % k, (x, y, 0), light=0.0)
                    for k, (x, y) in enumerate(((-9, 8), (12, -13), (-20, 20), (21, 20), (-22, -18), (22, -18)))]
    bunting("Bunt0", (-24, 25.5, 12.2), (26, 24.5, 12.6), n=20, sag=2.4, seed=0)
    bunting("Bunt1", (-29, 14, 11.5), (29, 10, 12.0), n=20, sag=2.0, seed=2)
    out["street"] = lantern_street()
    return out


def lantern_street():
    """The street off the square toward -Y (the chase at sunset; lamps go out one by one toward camera)."""
    houses = []; posts = []
    for k in range(6):
        y = -60 - k * 14
        for sx, yaw in ((-1, 90), (1, -90)):
            houses.append(timber_house("St%d%s" % (k, "LR"[sx > 0]), (sx * 13, y, 0), yaw, 12, 9, 7, 6,
                                       roof="red" if (k + sx) % 2 else "slate", seed=k * 2 + (sx > 0) + 20))
        posts.append(lamp_post("StPost%d" % k, (-5.5 if k % 2 else 5.5, y + 5, 0), light=0.0))
    rb("StreetCobbles", (40, 110, 1.0), V((0, -105, -0.49)), _lfm()["cobble"], None, r=0.05)
    return dict(houses=houses, posts=posts)


def ladder(name, base, top, parent=None, w=1.6):
    base, top = V(base), V(top); d = top - base; L_ = d.length
    r = empty(name, base, col=COL_PROPS); r.parent = parent
    r.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    for sx in (-1, 1): rb(name + "Rail", (0.18, 0.18, L_), V((sx * w / 2, 0, L_ / 2)), _lfm()["oldwood"], r, r=0.03)
    for k in range(int(L_ / 1.0)): rb(name + "Rung", (w, 0.14, 0.14), V((0, 0, 0.6 + k * 1.0)), _lfm()["plank"], r, r=0.03)
    return r


# ================================================================== back alley (night, cold)
def alley(origin=(300, 0, 0)):
    """Narrow back alley: two tall walls (ashlar + plaster), a dead-end arch, doors, drain pipes, a laundry line, crates,
    barrels, puddles (glossy), one wall lantern (the practical) and the cold moon from the far end."""
    m = _lfm(); O = V(origin); r = empty("Alley", O, col=COL_PROPS)
    rb("AlleyFloor", (12, 44, 1.0), V((0, 0, -0.5)), m["cobble"], r, r=0.05)
    for sx in (-1, 1):
        rb("AlleyWall", (2.0, 44, 18), V((sx * 4.2, 0, 9)), m["ashlar"] if sx < 0 else plaster_mat("lf_plaster_al", (150, 146, 140)), r, r=0.05)
        for k in range(5):
            y = -16 + k * 8
            rb("AlleyBeam", (0.2, 0.4, 18), V((sx * 3.18, y, 9)), m["beam"], r, r=0.04)
        rb("AlleyPipe", (0.3, 0.3, 17), V((sx * 3.05, -6 + sx * 4, 8.5)), m["iron"], r, r=0.12)
    for k, (sx, y) in enumerate(((-1, -9), (1, 4), (-1, 12))):
        rb("AlleyDoor", (0.2, 2.4, 4.4), V((sx * 3.15, y, 2.2)), wood_mat("lf_door", (92, 58, 36), 6.0), r, r=0.04)
        rb("AlleyStep", (1.0, 3.0, 0.4), V((sx * 2.8, y, 0.2)), m["darkstone"], r, r=0.05)
    rb("AlleyEnd", (12, 2, 18), V((0, 21, 9)), m["darkstone"], r, r=0.05)
    rb("AlleyArch", (6, 1.0, 2.0), V((0, -18, 14)), m["ashlar"], r, r=0.1)
    for k, (x, y, yw) in enumerate(((-2.2, 6, 10), (2.0, -4, -20), (-2.0, 14, 0))):
        crate("AlCrate%d" % k, (x, y, 0), r, w=1.8, d=1.5, h=1.3, apples=False, yaw=yw)
    barrel("AlBarrel0", (2.1, 9, 0), r, h=2.4, rad=0.85); barrel("AlBarrel1", (-2.3, -12, 0), r, h=2.2, rad=0.8)
    for k, (x, y, s) in enumerate(((0.6, -2, 1.6), (-0.8, 8, 1.1), (1.0, 15, 1.3))):
        rcyl("Puddle", s, 0.02, V((x, y, 0.02)), dmat("lf_puddle", (16, 20, 26), rough=0.03), r, seg=20)
    pts = [V((-3.1, -14 + 0, 11)), V((0, -14, 9.6)), V((3.1, -14, 11))]
    tube("AlLine", pts, 0.03, dmat("lf_rope", (150, 120, 80), rough=0.9), r)
    for k, x in enumerate((-1.8, -0.4, 1.2)):
        rb("Laundry", (1.1, 0.05, 1.5), V((x, -14, 9.4 - 0.05 * abs(x))), fabric("lf_laundry%d" % k, [(200, 196, 180), (120, 140, 170), (170, 120, 110)][k]), r, r=0.02)
    lt, ld = lantern("AlleyLan", (-2.7, 2, 8.2), r, s=0.7, light=0.0, col=(255, 150, 70))
    rb("AlleyLanArm", (1.3, 0.1, 0.1), V((-2.8, 2, 8.85)), m["iron"], r, r=0.03)
    return dict(root=r, lantern=ld, origin=O)


# ================================================================== inn stairs + cellar (loops 2 + 3)
def inn_stairs(origin=(300, 200, 0)):
    """Inn stairwell: plank floor, plastered walls with beams, a steep wooden staircase with banister + spindles,
    a cracked step (Stair_crack beat), a framed picture, a wall lantern, a window with cool light."""
    m = _lfm(); O = V(origin); r = empty("Inn", O, col=COL_PROPS)
    pm = plaster_mat("lf_plaster_inn", (214, 196, 160))
    rb("InnFloor", (24, 24, 1.0), V((0, 0, -0.5)), wood_mat("lf_floor", (120, 84, 52), 7.0), r, r=0.03)
    rb("InnCeil", (24, 24, 1.0), V((0, 0, 20.5)), m["beam"], r, r=0.03)
    for (x, y, w, d) in ((0, 12, 24, 1), (-12, 0, 1, 24), (12, 0, 1, 24), (0, -12.5, 24, 1)):
        rb("InnWall", (w, d, 20), V((x, y, 10)), pm, r, r=0.03)
    for k in range(5):
        rb("InnBeamV", (0.5, 0.4, 20), V((-10 + k * 5, 11.4, 10)), m["beam"], r, r=0.05)
    rb("InnBeamH", (24, 0.4, 0.5), V((0, 11.4, 9.5)), m["beam"], r, r=0.05)
    steps = []
    for k in range(14):                                        # staircase up the back wall, rising to +X
        x = -6 + k * 1.0; z = 0.5 + k * 0.72
        st = rb("Step%d" % k, (1.05, 4.0, 0.3), V((x, 9.0, z)), m["plank"], r, r=0.04); steps.append(st)
        rb("Riser", (0.1, 4.0, 0.72), V((x - 0.48, 9.0, z - 0.36)), m["oldwood"], r, r=0.02)
        rb("Spindle", (0.16, 0.16, 3.0), V((x, 7.15, z + 1.5)), m["beam"], r, r=0.04)
    rb("Stringer", (15, 0.4, 0.9), V((0.5, 7.0, 5.4)), m["beam"], r, r=0.05, rot=(0, -math.atan2(0.72, 1.0), 0))
    rb("Banister", (15.5, 0.35, 0.35), V((0.6, 7.15, 8.5)), m["beam"], r, r=0.1, rot=(0, -math.atan2(0.72, 1.0), 0))
    rb("NewelPost", (0.5, 0.5, 4.2), V((-6.6, 7.15, 2.1)), m["beam"], r, r=0.08)
    ball("NewelCap", (0.6, 0.6, 0.5), V((-6.6, 7.15, 4.35)), m["beam"], r)
    im = Image.new("RGB", (240, 300), (60, 70, 60)); d = ImageDraw.Draw(im)
    d.rectangle((0, 180, 240, 300), fill=(70, 100, 60)); d.ellipse((150, 40, 210, 100), fill=(240, 210, 120))
    d.polygon([(20, 180), (90, 90), (160, 180)], fill=(90, 100, 120))
    plane("InnPicture", 2.2, 2.8, V((-4, 11.38, 9.0)), imgmat("lf_innpic", save_img(im, "lf_innpic"), rough=0.7), r, rot=(0, 0, DG(180)))
    rb("InnPicFrame", (2.6, 0.12, 3.2), V((-4, 11.45, 9.0)), m["brass"], r, r=0.05)
    lt, ld = lantern("InnLan", (-9, 10.6, 9.5), r, s=0.7, light=0.0)
    rb("InnWindow", (0.2, 3.0, 4.0), V((11.45, 2, 9)), dmat("lf_innwin", (120, 150, 200), emit=1.4, emit_rgb=(120, 150, 200)), r, r=0.04)
    for q in (-0.75, 0.75): rb("InnWinBar", (0.3, 0.12, 4.0), V((11.4, 2 + q, 9)), m["beam"], r, r=0.02)
    barrel("InnKeg", (-9, 3, 0), r, h=2.2, rad=0.8)
    rb("InnTable", (3.5, 2.5, 0.25), V((4, -3, 3.0)), m["plank"], r, r=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1): rb("InnTLeg", (0.25, 0.25, 3.0), V((4 + sx * 1.5, -3 + sy * 1.0, 1.5)), m["beam"], r, r=0.04)
    return dict(root=r, steps=steps, lantern=ld, origin=O)


def cellar(origin=(300, 400, 0)):
    """Cellar: dark stone walls + barrel vault ribs, racked barrels, shelves of jars, sacks, straw, one candle on a
    crate (the only practical). Something breathes in the dark (the scene adds two faint eyes)."""
    m = _lfm(); O = V(origin); r = empty("Cellar", O, col=COL_PROPS)
    rb("CelFloor", (20, 24, 1.0), V((0, 0, -0.5)), m["darkstone"], r, r=0.03)
    rb("CelCeil", (20, 24, 1.0), V((0, 0, 11.5)), m["darkstone"], r, r=0.03)
    for (x, y, w, d) in ((0, 12, 20, 1), (-10, 0, 1, 24), (10, 0, 1, 24), (0, -12.5, 20, 1)):
        rb("CelWall", (w, d, 12), V((x, y, 6)), m["darkstone"], r, r=0.03)
    for k in range(4):
        rb("CelRib", (20, 0.8, 0.8), V((0, -9 + k * 6, 10.8)), m["ashlar"], r, r=0.1)
    for k in range(4):
        b = barrel("CelBarrel%d" % k, (-7.5 + k * 2.1, 9.6, 0.6), r, h=2.2, rad=0.95)
        b.rotation_euler = (DG(90), 0, 0)
    rb("CelRack", (9, 2.4, 0.5), V((-4.4, 9.6, 0.25)), m["beam"], r, r=0.05)
    for k in range(3):
        rb("CelShelf", (0.9, 5.0, 0.2), V((9.3, -3, 2.5 + k * 2.4)), m["plank"], r, r=0.03)
        for q in range(5):
            rcyl("CelJar", 0.32, 0.9, V((9.2, -5 + q * 1.0, 3.05 + k * 2.4)), dmat("lf_jar%d" % (q % 3), [(140, 110, 70), (90, 110, 80), (150, 80, 60)][q % 3], rough=0.4), r, seg=12)
    for k in range(3): sack("CelSack%d" % k, (-7 + k * 1.3, -6 + k * 0.6, 0), r, s=1.1)
    crate("CelCrate", (1.5, 1.5, 0), r, w=1.8, d=1.6, h=1.6, apples=False)
    rcyl("Candle", 0.13, 0.8, V((1.5, 1.5, 2.0)), dmat("lf_wax", (236, 226, 200), rough=0.5), r, seg=12)
    flame = ball("CandleFlame", (0.05, 0.05, 0.12), V((1.5, 1.5, 2.5)), glowm("lf_flame", (255, 200, 110), 3.0), r)
    rcyl("CandleDish", 0.36, 0.08, V((1.5, 1.5, 1.62)), m["brass"], r, seg=16)
    ld = bpy.data.lights.new("CandleL", "POINT"); ld.energy = 0.0; ld.color = lin((255, 160, 80)); ld.shadow_soft_size = 0.08
    o = bpy.data.objects.new("CandleL", ld); bpy.context.scene.collection.objects.link(o); o.parent = r; o.location = V((1.5, 1.5, 2.75))
    for x in (-0.9, 0.9):                                         # the eyes in the dark (scene keys their glow)
        ball("DarkEye", (0.16, 0.08, 0.1), V((-5.5 + x * 0.5, -10.0, 4.6)), glowm("lf_darkeye", (220, 230, 255), 0.0), r)
    return dict(root=r, flame=flame, light=ld, origin=O, candle_pt=O + V((1.5, 1.5, 2.55)))


# ================================================================== Theo's bedroom (3 AM, laptop glow)
def server_img(cursor=True, name="lf_server"):
    im = Image.new("RGB", (800, 500), (24, 26, 32)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 800, 56), fill=(40, 44, 54)); d.text((24, 28), "Servers", font=pfont(30), fill=(235, 235, 240), anchor="lm")
    rows = [("Lanternfall", "1/1", (226, 70, 70)), ("Bloxville RP", "48/50", (120, 124, 134)),
            ("Obby Rush", "32/40", (120, 124, 134)), ("Pizza Shift", "12/30", (120, 124, 134))]
    for k, (nm, pl, c) in enumerate(rows):
        y = 80 + k * 100
        d.rounded_rectangle((20, y, 780, y + 84), 12, fill=(46, 50, 60) if k else (60, 40, 44))
        d.rectangle((36, y + 12, 136, y + 72), fill=(30, 30, 36) if k else (90, 60, 30))
        if not k:
            d.rectangle((70, y + 22, 102, y + 62), fill=(255, 190, 90))
        d.text((156, y + 30), nm, font=pfont(34), fill=(240, 240, 244), anchor="lm")
        d.text((156, y + 64), pl + " players", font=pfont(24, bold=False), fill=c, anchor="lm")
        d.rounded_rectangle((620, y + 20, 760, y + 64), 10, fill=(40, 160, 80))
        d.text((690, y + 42), "Join", font=pfont(28), fill=(255, 255, 255), anchor="mm")
    if cursor:
        cx, cy = 702, 128
        d.polygon([(cx, cy), (cx, cy + 40), (cx + 11, cy + 30), (cx + 20, cy + 48), (cx + 27, cy + 45), (cx + 18, cy + 27), (cx + 31, cy + 27)],
                  fill=(255, 255, 255), outline=(0, 0, 0))
    return save_img(im, name)


def bedroom(origin=(600, 0, 0)):
    """Theo's bedroom at 3 AM: bed with rumpled duvet + pillow, desk, laptop (server list screen = the key light),
    gaming posters, shelf, window with cold blue night, a phone face-down. Modern (contrast with Lanternfall)."""
    m = _lfm(); O = V(origin); r = empty("Bedroom", O, col=COL_PROPS)
    rb("BrFloor", (20, 20, 1), V((0, 0, -0.5)), wood_mat("lf_brfloor", (150, 116, 84), 7.0), r, r=0.02)
    wallm = plaster_mat("lf_brwall", (70, 84, 110))
    for (x, y, w, d) in ((0, 10, 20, 1), (-10, 0, 1, 20), (10, 0, 1, 20)):
        rb("BrWall", (w, d, 14), V((x, y, 7)), wallm, r, r=0.03)
    rb("BrCeil", (20, 20, 1), V((0, 0, 14.5)), wallm, r, r=0.03)
    rb("BedFrame", (6.4, 9.5, 1.6), V((-5.5, 4.5, 0.8)), wood_mat("lf_bedw", (60, 50, 46), 5.0), r, r=0.1)
    rb("Mattress", (6.0, 9.0, 1.0), V((-5.5, 4.5, 2.0)), fabric("lf_sheet", (220, 222, 230)), r, r=0.3)
    duvet = rb("Duvet", (6.2, 6.0, 0.6), V((-5.5, 3.0, 2.7)), fabric("lf_duvet", (50, 70, 130)), r, r=0.28)
    rb("DuvetRuck", (5.0, 1.3, 0.8), V((-5.6, 5.6, 2.8)), fabric("lf_duvet", (50, 70, 130)), r, r=0.35, rot=(0, 0, DG(6)))
    rb("Pillow", (3.6, 1.6, 0.8), V((-5.5, 8.0, 2.85)), fabric("lf_pillow", (236, 236, 240)), r, r=0.35)
    rb("Desk", (6.0, 3.0, 0.25), V((0.0, 7.0, 3.4)), wood_mat("lf_desk", (180, 170, 160), 3.0), r, r=0.04)
    for sx in (-1, 1): rb("DeskLeg", (0.25, 2.8, 3.3), V((0.0 + sx * 2.8, 7.0, 1.65)), m["iron"], r, r=0.04)
    rb("LapBase", (2.6, 1.8, 0.12), V((0.0, 6.6, 3.6)), dmat("lf_lap", (60, 62, 68), rough=0.3, metal=0.6), r, r=0.04)
    lid = empty("LapLid", O + V((0.0, 7.45, 3.62)), col=COL_PROPS); lid.parent = r; lid.location = V((0.0, 7.45, 3.62))
    lid.rotation_euler = (DG(-14), 0, 0)
    rb("LapLidBack", (2.6, 0.1, 1.75), V((0, 0.03, 0.88)), dmat("lf_lap", (60, 62, 68), rough=0.3, metal=0.6), lid, r=0.04)
    scr = plane("LapScreen", 2.4, 1.5, V((0, -0.03, 0.88)), imgmat("lf_server", server_img(), rough=0.3, emit=3.5), lid, rot=(0, 0, DG(180)))
    rb("LapKeys", (2.2, 1.0, 0.03), V((0.0, 6.4, 3.67)), dmat("lf_keys", (30, 30, 34), rough=0.5), r, r=0.01)
    ld = bpy.data.lights.new("LaptopL", "AREA"); ld.energy = 0.0; ld.size = 2.4; ld.color = lin((170, 200, 255))
    o = bpy.data.objects.new("LaptopL", ld); bpy.context.scene.collection.objects.link(o); o.parent = lid; o.location = V((0, -0.3, 0.9))
    o.rotation_euler = (DG(90), 0, 0)
    for k, (x, c) in enumerate(((-3.5, (200, 60, 60)), (0.5, (60, 120, 200)))):
        im = Image.new("RGB", (240, 340), c); d = ImageDraw.Draw(im)
        d.rectangle((20, 20, 220, 220), fill=dk(c, 0.6)); d.rectangle((60, 60, 120, 120), fill=(240, 240, 240))
        d.text((120, 280), ("OBBY", "SPEED")[k], font=pfont(46), fill=(250, 250, 250), anchor="mm")
        plane("Poster%d" % k, 2.4, 3.4, V((x, 9.45, 9.0)), imgmat("lf_poster%d" % k, save_img(im, "lf_poster%d" % k), rough=0.8), r,
              rot=(0, 0, DG(180)))
    rb("BrWindow", (0.2, 4.0, 4.4), V((-9.45, -1, 8.0)), dmat("lf_brwin", (40, 60, 120), emit=1.2, emit_rgb=(60, 90, 170)), r, r=0.04)
    for q in (-1, 1): rb("BrWinBar", (0.3, 0.14, 4.4), V((-9.4, -1 + q * 0.0, 8.0)), dmat("lf_white", (230, 230, 230)), r, r=0.02)
    rb("BrCurtain", (0.2, 1.4, 6.0), V((-9.3, 1.8, 7.6)), fabric("lf_curtain", (80, 60, 90)), r, r=0.05)
    rb("Phone", (0.5, 0.9, 0.06), V((-3.6, 6.8, 3.08)), dmat("lf_phone", (20, 20, 24), rough=0.3), r, r=0.04)
    rb("BrShelf", (5.0, 1.2, 0.2), V((4.5, 9.3, 8.5)), wood_mat("lf_desk", (180, 170, 160), 3.0), r, r=0.03)
    for q in range(5):
        rb("Book", (0.35, 1.0, 1.3 + 0.1 * q), V((2.6 + q * 0.4, 9.3, 9.25 + 0.05 * q)),
           dmat("lf_book%d" % (q % 3), [(160, 50, 50), (50, 90, 150), (220, 190, 60)][q % 3], rough=0.6), r, r=0.03)
    ld2 = bpy.data.lights.new("BrMoon", "AREA"); ld2.energy = 0.0; ld2.size = 4.0; ld2.color = lin((110, 140, 255))
    o2 = bpy.data.objects.new("BrMoon", ld2); bpy.context.scene.collection.objects.link(o2); o2.parent = r
    o2.location = V((-8.5, -1, 8.0)); o2.rotation_euler = (0, DG(-90), 0)
    return dict(root=r, screen=scr, light=ld, moon=ld2, origin=O, lid=lid, screen_pt=lambda: scr.matrix_world.translation.copy())


# ================================================================== the respawn ring + THE HAND
def respawn_ring(name, loc):
    """Red Roblox respawn ring: a glowing floor disc ring + 3 thin vertical light rings that rise and fade (keyed by
    the scene with ring_flash). Emission only (no lights) apart from one red point light."""
    r = empty(name, V(loc), col=COL_PROPS)
    red = bpy.data.materials.new(name + "Glow"); red.use_nodes = True
    P = red.node_tree.nodes["Principled BSDF"]; P.inputs["Base Color"].default_value = (*lin((255, 40, 40)), 1)
    P.inputs["Emission Color"].default_value = (*lin((255, 30, 30)), 1); P.inputs["Emission Strength"].default_value = 0.0
    floor = bpy.data.meshes.new(name + "Disc")
    import bmesh as _bm
    bm = _bm.new(); _bm.ops.create_circle(bm, cap_ends=False, radius=2.6, segments=48)
    ext = _bm.ops.extrude_edge_only(bm, edges=list(bm.edges)); vs = [v for v in ext["geom"] if isinstance(v, _bm.types.BMVert)]
    for v in vs: v.co *= 0.86
    bm.to_mesh(floor); bm.free()
    disc = bpy.data.objects.new(name + "Disc", floor); link(disc, COL_PROPS); disc.parent = r; disc.location = V((0, 0, 0.04))
    floor.materials.append(red)
    rings = []
    for k in range(3):
        bm = _bm.new(); _bm.ops.create_circle(bm, cap_ends=False, radius=2.4, segments=48)
        ex = _bm.ops.extrude_edge_only(bm, edges=list(bm.edges))
        for v in [v for v in ex["geom"] if isinstance(v, _bm.types.BMVert)]: v.co.z += 0.14
        me = bpy.data.meshes.new(name + "Band%d" % k); bm.to_mesh(me); bm.free(); me.materials.append(red)
        o = bpy.data.objects.new(name + "Band%d" % k, me); link(o, COL_PROPS); o.parent = r; o.location = V((0, 0, 0.1))
        o.visible_shadow = False
        rings.append(o)
    ld = bpy.data.lights.new(name + "L", "POINT"); ld.energy = 0.0; ld.color = lin((255, 40, 40)); ld.shadow_soft_size = 1.5
    lo = bpy.data.objects.new(name + "L", ld); bpy.context.scene.collection.objects.link(lo); lo.parent = r; lo.location = V((0, 0, 1.2))
    return dict(root=r, mat=P.inputs["Emission Strength"], rings=rings, light=ld, disc=disc)


def ring_flash(RG_, f0, strength=1.0):
    """The respawn flash: snaps on (2 frames), bands rise and fade over ~22 frames, floor ring lingers then dies."""
    E = RG_["mat"]
    for fr, v in ((f0 - 1, 0.0), (f0, 16.0 * strength), (f0 + 6, 9.0 * strength), (f0 + 22, 3.0 * strength), (f0 + 40, 0.0)):
        kx(E, "default_value", fr, v)
    for o in [RG_["disc"]] + RG_["rings"]:
        kf(o, "hide_render", f0 - 1, True, interp="CONSTANT"); kf(o, "hide_render", f0, False, interp="CONSTANT")
        kf(o, "hide_render", f0 + 41, True, interp="CONSTANT")
    for fr, v in ((f0 - 1, 0.0), (f0, 900.0 * strength), (f0 + 8, 500.0 * strength), (f0 + 40, 0.0)):
        kf(RG_["light"], "energy", fr, v)
    for k, o in enumerate(RG_["rings"]):
        fa = f0 + k * 3
        kf(o, "location", fa - 1, V((0, 0, 0.1))); kf(o, "scale", fa - 1, (1, 1, 1))
        kf(o, "location", fa + 18, V((0, 0, 6.5 + k))); kf(o, "scale", fa + 18, (0.75, 0.75, 1))
        kf(o, "scale", fa + 19, (0.001, 0.001, 1)); kf(o, "location", fa + 19, V((0, 0, 0.1)))


def the_hand(name="TheHand"):
    """THE HAND: a long pure-black arm with smoke-edged wisps (alpha-noise cards), four long fingers + thumb on
    pivots (curl keyed by the scene). Matte black, no specular: it reads as a hole in the frame."""
    blk = dmat("lf_void", (2, 2, 2), rough=1.0)
    r = empty(name, V((0, 0, 0)), col=COL_PROPS)
    arm = taper(name + "Arm", (0.9, 0.9, 7.0), V((0, 0, -3.5)), blk, r, top=(1.3, 1.3), r=0.3)
    palm = rb(name + "Palm", (1.25, 0.45, 1.3), V((0, 0, 0.5)), blk, r, r=0.2)
    fingers = []
    for k, x in enumerate((-0.45, -0.15, 0.15, 0.45)):
        piv = empty(name + "Fp%d" % k, V((x, 0, 1.1)), col=COL_PROPS); piv.parent = r; piv.location = V((x, 0, 1.1))
        seg1 = taper(name + "F%da" % k, (0.26, 0.26, 1.0), V((0, 0, 0.5)), blk, piv, top=(0.85, 0.85), r=0.1)
        p2 = empty(name + "Fq%d" % k, V((0, 0, 1.0)), col=COL_PROPS); p2.parent = piv; p2.location = V((0, 0, 1.0))
        taper(name + "F%db" % k, (0.22, 0.22, 0.9 + 0.15 * (k in (1, 2))), V((0, 0, 0.45)), blk, p2, top=(0.4, 0.4), r=0.08)
        fingers.append((piv, p2))
    th = empty(name + "Th", V((-0.6, 0.1, 0.4)), col=COL_PROPS); th.parent = r; th.location = V((-0.6, 0.1, 0.4))
    taper(name + "Thumb", (0.26, 0.26, 0.9), V((0, 0, 0.45)), blk, th, top=(0.5, 0.5), r=0.08); th.rotation_euler = (0, DG(-50), 0)
    # smoke: alpha-noise cards along the arm
    sm = bpy.data.materials.new(name + "Smoke"); sm.use_nodes = True; nt = sm.node_tree; Nn, Ll = nt.nodes, nt.links
    out = Nn["Material Output"]; Pp = Nn["Principled BSDF"]
    Pp.inputs["Base Color"].default_value = (0.002, 0.002, 0.002, 1); Pp.inputs["Roughness"].default_value = 1.0
    tc = Nn.new("ShaderNodeTexCoord"); nz = Nn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; nz.inputs["Detail"].default_value = 6
    Ll.new(tc.outputs["UV"], nz.inputs["Vector"])
    gr = Nn.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    mp = Nn.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (0.5, 0.5, 0); Ll.new(tc.outputs["UV"], mp.inputs["Vector"])
    sub = Nn.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
    Ll.new(tc.outputs["UV"], sub.inputs[0]); sc_ = Nn.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 2.0
    Ll.new(sub.outputs[0], sc_.inputs[0]); Ll.new(sc_.outputs[0], gr.inputs["Vector"])
    mul = Nn.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; Ll.new(gr.outputs["Fac"], mul.inputs[0]); Ll.new(nz.outputs["Fac"], mul.inputs[1])
    pw = Nn.new("ShaderNodeMath"); pw.operation = "MULTIPLY"; pw.inputs[1].default_value = 2.2; Ll.new(mul.outputs[0], pw.inputs[0])
    Ll.new(pw.outputs[0], Pp.inputs["Alpha"])
    try: sm.blend_method = "HASHED"
    except Exception: pass
    rng = random.Random(9); wisps = []
    for k in range(10):
        z = -6.5 + k * 0.75; s = 1.6 + rng.uniform(0, 0.8)
        w_ = plane(name + "Wisp%d" % k, s, s * 1.2, V((rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2), z)), sm, r,
                   rot=(DG(90 + rng.uniform(-20, 20)), 0, DG(rng.uniform(0, 180))))
        w_.visible_shadow = False; wisps.append(w_)
    return dict(root=r, fingers=fingers, thumb=th, wisps=wisps)


# ================================================================== production look helpers (cheap: cards, no volumes)
def haze_card(name, loc, w, h, normal, col=(1.0, 0.85, 0.65), strength=0.25, density=0.35, parent=None):
    """Faked haze: a soft-edged, noise-broken emissive card (transparent mix) that sits between camera and set.
    Reads as light hanging in the air. Shadows off, no volume."""
    mt = bpy.data.materials.new(name + "M"); mt.use_nodes = True; nt = mt.node_tree; Nn, Ll = nt.nodes, nt.links
    for n_ in list(Nn): Nn.remove(n_)
    out = Nn.new("ShaderNodeOutputMaterial"); tr = Nn.new("ShaderNodeBsdfTransparent"); em = Nn.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    add = Nn.new("ShaderNodeAddShader"); Ll.new(tr.outputs[0], add.inputs[0]); Ll.new(em.outputs[0], add.inputs[1])
    mix = Nn.new("ShaderNodeMixShader"); Ll.new(tr.outputs[0], mix.inputs[1]); Ll.new(add.outputs[0], mix.inputs[2])
    tc = Nn.new("ShaderNodeTexCoord"); nz = Nn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 3
    Ll.new(tc.outputs["UV"], nz.inputs["Vector"])
    sub = Nn.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
    Ll.new(tc.outputs["UV"], sub.inputs[0]); ln = Nn.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; Ll.new(sub.outputs[0], ln.inputs[0])
    fall = Nn.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.5; fall.inputs["From Max"].default_value = 0.1
    Ll.new(ln.outputs["Value"], fall.inputs["Value"])
    mul = Nn.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; Ll.new(fall.outputs["Result"], mul.inputs[0]); Ll.new(nz.outputs["Fac"], mul.inputs[1])
    mul2 = Nn.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = density; Ll.new(mul.outputs[0], mul2.inputs[0])
    Ll.new(mul2.outputs[0], mix.inputs[0]); Ll.new(mix.outputs[0], out.inputs["Surface"])
    try: mt.blend_method = "BLEND"
    except Exception: pass
    p = plane(name, w, h, V(loc), mt, parent)
    n = V(normal).normalized(); p.rotation_euler = n.to_track_quat("Y", "Z").to_euler()
    p.visible_shadow = False
    try: p.visible_glossy = False
    except Exception: pass
    return p, em.inputs["Strength"]


def light_shaft(name, src, dst, width=1.5, col=(1.0, 0.85, 0.6), strength=0.35, parent=None):
    """A beam of light (window / gap / lantern): a long soft card from src to dst, brightest at the source."""
    src, dst = V(src), V(dst); d = dst - src; L_ = d.length
    p, st = haze_card(name, (src + dst) / 2, width, L_, (0, 0, 1), col=col, strength=strength, density=0.55, parent=parent)
    p.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    p.rotation_euler.rotate_axis("X", DG(90)); p.rotation_euler.rotate_axis("X", DG(-90))
    q = d.normalized().to_track_quat("Z", "X"); p.rotation_mode = "QUATERNION"; p.rotation_quaternion = q
    me = p.data                                              # card lies in local XZ: rotate so its long side runs along d
    for v in me.vertices: v.co = V((v.co.x, 0, v.co.z))
    return p, st


# ================================================================== story props
def sun_lantern(name="SunLantern"):
    """The stolen SUN LANTERN: ornate brass cage (8 ribs, crown, ring), a glowing gold core, sun-ray plate on top.
    Origin at the carry ring."""
    m = _lfm(); r = empty(name, V((0, 0, 0)), col=COL_PROPS)
    core = ball(name + "Core", (0.9, 0.9, 1.1), V((0, 0, -1.3)), glowm("lf_suncore", (255, 200, 90), 14.0), r)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        rb(name + "Rib", (0.08, 0.08, 1.5), V((0.55 * math.cos(a), 0.55 * math.sin(a), -1.3)), m["brass"], r, r=0.02)
    rcyl(name + "Base", 0.7, 0.2, V((0, 0, -2.1)), m["brass"], r, seg=16)
    rcyl(name + "Crown", 0.7, 0.3, V((0, 0, -0.5)), m["brass"], r, seg=16, top_scale=0.5)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        rb(name + "Ray", (0.1, 0.05, 0.35), V((0.45 * math.cos(a), 0.45 * math.sin(a), -0.25)), m["brass"], r, r=0.02, rot=(0, 0, a))
    rcyl(name + "Ring", 0.22, 0.06, V((0, 0, 0)), m["brass"], r, axis="Y", seg=14)
    return r


def pigeon(name, loc):
    """A town pigeon (stops mid-air in the freeze): grey body, darker wings out, small head + beak."""
    r = empty(name, V(loc), col=COL_PROPS)
    g = dmat("lf_pigeon", (130, 132, 140), rough=0.7); dg = dmat("lf_pigeon_dk", (80, 82, 92), rough=0.7)
    ball(name + "Body", (0.6, 1.0, 0.55), V((0, 0, 0)), g, r)
    ball(name + "Head", (0.36, 0.36, 0.36), V((0, 0.55, 0.22)), dg, r)
    rb(name + "Beak", (0.08, 0.2, 0.08), V((0, 0.78, 0.2)), dmat("lf_beak", (200, 160, 90)), r, r=0.02)
    for sx in (-1, 1):
        rb(name + "Wing", (1.3, 0.6, 0.08), V((sx * 0.85, -0.05, 0.25)), dg, r, r=0.04, rot=(0, DG(sx * -20), 0))
    rb(name + "Tail", (0.4, 0.5, 0.06), V((0, -0.65, 0.05)), dg, r, r=0.03)
    return r


def void_box(loc=(-3000, 0, 0)):
    """A closed black room far away: the camera sits inside for cut-to-black shots (no light, no sky)."""
    return rb("Void", (40, 40, 40), V(loc), dmat("lf_voidbox", (0, 0, 0), rough=1.0), None, r=0.1)
