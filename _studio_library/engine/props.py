# props.py - detailed Roblox-game-quality props & furniture (bevels, seams, decals, lights, textures)
# but render-cheap: no real glass transmission, no subdivision, textures are small images / procedural.
import bmesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
PROPTEX = "/home/claude/renders/props_tex"
os.makedirs(PROPTEX, exist_ok=True)
V = Vector
COL_PROPS = collection("Props")


# ---------------------------------------------------------------- materials (object-space so they move with props)
def _nodes(m):
    m.use_nodes = True
    return m.node_tree, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


_PM = {}


def pmat(name, rgb, rough=0.5, metal=0.0, emit=0.0, emit_rgb=None, coat=0.0):
    if name in _PM: return _PM[name]
    m = bpy.data.materials.new(name); nt, N, L, b = _nodes(m)
    b.inputs["Base Color"].default_value = (*lin(rgb), 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if coat: b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(emit_rgb or rgb), 1); b.inputs["Emission Strength"].default_value = emit
    _PM[name] = m; return m


def wood(name, rgb, scale=2.5, rough=0.55):
    if name in _PM: return _PM[name]
    m = bpy.data.materials.new(name); nt, N, L, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 8)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 2.5; wv.inputs["Detail"].default_value = 2
    L.new(mp.outputs["Vector"], wv.inputs["Vector"])
    r = N.new("ShaderNodeValToRGB"); L.new(wv.outputs["Fac"], r.inputs["Fac"])
    r.color_ramp.elements[0].color = (*lin(dk(rgb, 0.78)), 1); r.color_ramp.elements[1].color = (*lin(rgb), 1)
    L.new(r.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _PM[name] = m; return m


def fabric(name, rgb, rough=0.9, scale=60):
    if name in _PM: return _PM[name]
    m = bpy.data.materials.new(name); nt, N, L, b = _nodes(m)
    b.inputs["Base Color"].default_value = (*lin(rgb), 1); b.inputs["Roughness"].default_value = rough
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _PM[name] = m; return m


def imgmat(name, path, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name); nt, N, L, b = _nodes(m)
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    L.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit:
        L.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    if t.image.depth == 32 or path.endswith(".png"):
        L.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m


def wall_tiles(name, rgb, size=0.5):
    """Square tile grid on vertical (XZ) faces, object-space."""
    if name in _PM: return _PM[name]
    m = bpy.data.materials.new(name); nt, N, L, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], cmb.inputs["X"]); L.new(sep.outputs["Z"], cmb.inputs["Y"])
    br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0 / size; br.inputs["Brick Width"].default_value = 1.0
    br.inputs["Row Height"].default_value = 0.5; br.inputs["Mortar Size"].default_value = 0.03; br.offset = 0.0
    br.inputs["Color1"].default_value = (*lin(rgb), 1); br.inputs["Color2"].default_value = (*lin(dk(rgb, 0.96)), 1)
    br.inputs["Mortar"].default_value = (*lin(dk(rgb, 0.7)), 1)
    L.new(cmb.outputs[0], br.inputs["Vector"]); L.new(br.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.invert = True
    L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.2
    _PM[name] = m; return m


GLASS = lambda: pmat("Glass", (40, 52, 66), rough=0.04, coat=1.0)
CHROME = lambda: pmat("Chrome", (220, 222, 228), rough=0.15, metal=1.0)
RUBBER = lambda: pmat("Rubber", (26, 26, 28), rough=0.85)
BLACKPL = lambda: pmat("BlackPlastic", (22, 22, 24), rough=0.45)


# ---------------------------------------------------------------- geometry helpers
def _obj(name, me, m, loc, parent, rot=(0, 0, 0)):
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); link(ob, COL_PROPS)
    ob.location = loc; ob.rotation_euler = rot
    if parent: ob.parent = parent
    return ob


def rb(name, size, loc, m, parent, r=0.06, rot=(0, 0, 0)):
    return solid(name, rbox_mesh(size, r), (1, 1, 1), loc, m, rot=rot, parent=parent, col=COL_PROPS)


def taper(name, size, loc, m, parent, top=(0.8, 0.7), shift=0.0, r=0.15, rot=(0, 0, 0)):
    """Box whose top face is scaled (top=(sx,sy)) and shifted along Y - cabins, lampshades, pots."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        if v.co.z > 0:
            v.co.x *= top[0]; v.co.y = v.co.y * top[1] + shift
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(r, min(size) * 0.4), segments=3, affect="EDGES", profile=0.5,
                    clamp_overlap=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return _obj(name, me, m, loc, parent, rot)


def rcyl(name, radius, depth, loc, m, parent, axis="Z", bevel=0.05, seg=28, rot=None, top_scale=1.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=radius, radius2=radius * top_scale, depth=depth)
    rim = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-5]
    if bevel: bmesh.ops.bevel(bm, geom=rim, offset=min(bevel, radius * 0.4, depth * 0.4), segments=3, affect="EDGES", profile=0.5,
                              clamp_overlap=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = abs(p.normal.z) < 0.99
    r = rot or {"Z": (0, 0, 0), "X": (0, math.radians(90), 0), "Y": (math.radians(90), 0, 0)}[axis]
    return _obj(name, me, m, loc, parent, r)


def plane(name, w, h, loc, m, parent, rot=None):
    """Decal plane (w x h) with UVs; faces +Y and reads correctly from the front. rot=(90deg,0,0) lays it face-up."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(w / 2, 0, -h / 2), (-w / 2, 0, -h / 2), (-w / 2, 0, h / 2), (w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UV")
    for li, c in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[li].uv = c
    return _obj(name, me, m, loc, parent, (0, 0, 0) if rot is None else rot)


def root_of(name, loc=(0, 0, 0)):
    return empty(name, V(loc), col=COL_PROPS)


def save_img(im, name):
    p = f"{PROPTEX}/{name}.png"; im.save(p); return p


def pfont(sz, bold=True):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""), sz)


# ---------------------------------------------------------------- VEHICLES
def wheel(parent, loc, side, R=1.15, W=0.85, rim_rgb=(200, 202, 210)):
    t = rcyl("Tyre", R, W, loc, RUBBER(), parent, axis="X", bevel=0.25)
    rcyl("Sidewall", R * 0.8, W + 0.04, loc, pmat("Sidewall", (40, 40, 44), rough=0.7), parent, axis="X", bevel=0.05)
    rim = pmat("Rim" + str(rim_rgb), rim_rgb, rough=0.25, metal=0.9)
    rx = loc[0] + side * (W / 2 + 0.01)
    rcyl("Rim", R * 0.7, 0.1, V((rx, loc[1], loc[2])), rim, parent, axis="X", bevel=0.04)
    rcyl("RimDish", R * 0.5, 0.12, V((rx + side * 0.01, loc[1], loc[2])), pmat("RimDish", dk(rim_rgb, 0.7), rough=0.3, metal=0.9), parent,
         axis="X", bevel=0.03)
    rcyl("Hub", R * 0.18, 0.14, V((rx + side * 0.03, loc[1], loc[2])), CHROME(), parent, axis="X", bevel=0.02)
    for k in range(5):
        a = k * 2 * math.pi / 5
        rb("Spoke", (0.1, R * 0.55, 0.2), V((rx + side * 0.07, loc[1] + math.cos(a) * R * 0.38, loc[2] + math.sin(a) * R * 0.38)),
           rim, parent, r=0.05, rot=(a - math.pi / 2, 0, 0))


def livery_texture(kind, body, name):
    """Door decal images (original designs, no real-world branding)."""
    W, H = 1024, 512
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "police":
        d.rectangle((0, 300, W, 360), fill=(30, 80, 200, 255))
        d.text((W / 2, 200), "POLICE", font=pfont(150), fill=(20, 24, 40, 255), anchor="mm")
        d.text((W / 2, 420), "BLOXBURY PD  ·  911", font=pfont(44), fill=(20, 24, 40, 255), anchor="mm")
    elif kind == "taxi":
        for i in range(0, W, 64):
            d.rectangle((i, 300, i + 32, 332), fill=(20, 20, 22, 255)); d.rectangle((i + 32, 332, i + 64, 364), fill=(20, 20, 22, 255))
        d.text((W / 2, 200), "TAXI", font=pfont(150), fill=(20, 20, 22, 255), anchor="mm")
    else:
        d.rectangle((0, 330, W, 346), fill=(*dk(body, 0.6), 255))
    return save_img(im, name)


def car(name, kind="civilian", body=(40, 110, 200), loc=(0, 0, 0)):
    """Sedan ~15 x 7 x 5.3 studs. kind: civilian | police | taxi."""
    root = root_of(name, loc)
    if kind == "police": body = (24, 26, 34)
    if kind == "taxi": body = (250, 196, 30)
    paint = pmat(f"Paint_{kind}_{body}", body, rough=0.25, coat=1.0)
    lower = pmat("PaintWhite", (238, 238, 240), rough=0.25, coat=1.0) if kind == "police" else paint
    trim = BLACKPL()
    L_, Wd = 15.0, 7.0
    # body: lower hull + doors band + bonnet/boot
    rb("Hull", (Wd, L_, 1.6), V((0, 0, 1.55)), lower, root, r=0.55)
    rb("Shoulder", (Wd * 0.98, L_ * 0.97, 1.0), V((0, 0, 2.75)), paint, root, r=0.45)
    rb("Bonnet", (Wd * 0.94, 4.4, 0.6), V((0, 5.0, 3.2)), paint, root, r=0.3, rot=(math.radians(-4), 0, 0))
    rb("Boot", (Wd * 0.94, 3.0, 0.6), V((0, -5.7, 3.25)), paint, root, r=0.3)
    # cabin (tapered greenhouse) + glass
    taper("Cabin", (Wd * 0.86, 7.2, 1.9), V((0, -0.6, 4.25)), paint, root, top=(0.84, 0.62), shift=-0.35, r=0.35)
    g = GLASS()
    taper("Windscreen", (Wd * 0.74, 0.12, 1.75), V((0, 2.55, 4.2)), g, root, top=(0.86, 1.0), shift=-1.1, r=0.04)
    taper("RearGlass", (Wd * 0.72, 0.12, 1.6), V((0, -3.6, 4.15)), g, root, top=(0.88, 1.0), shift=0.9, r=0.04)
    for s in (-1, 1):
        x = s * (Wd * 0.43 - 0.02)
        tilt = (0, -s * math.radians(14), 0)
        rb("SideGlassF", (0.06, 2.5, 1.2), V((s * 2.79, 0.75, 4.25)), g, root, r=0.06, rot=tilt)
        rb("SideGlassR", (0.06, 2.3, 1.15), V((s * 2.79, -2.0, 4.23)), g, root, r=0.06, rot=tilt)
        rb("BPillar", (0.08, 0.28, 1.35), V((s * 2.8, -0.6, 4.25)), trim, root, r=0.03, rot=tilt)
        # door seams + handles + mirrors
        for yy in (2.4, -0.6, -3.4):
            rb("DoorSeam", (0.04, 0.05, 2.4), V((s * Wd / 2 - 0.0, yy, 2.4)), trim, root, r=0.01)
        for yy in (0.2, -2.6):
            rb("Handle", (0.12, 0.6, 0.14), V((s * (Wd / 2 + 0.02), yy, 3.0)), CHROME(), root, r=0.05)
        rb("Mirror", (0.7, 0.4, 0.45), V((s * (Wd / 2 + 0.3), 2.3, 3.7)), paint, root, r=0.15)
        rb("MirrorGlass", (0.05, 0.3, 0.32), V((s * (Wd / 2 + 0.3), 2.1, 3.7)), CHROME(), root, r=0.03)
        rb("SideSkirt", (0.2, 8.0, 0.35), V((s * Wd / 2, 0, 0.95)), trim, root, r=0.08)
        # wheel arches + wheels
        for yy in (4.6, -4.4):
            rcyl("Arch", 1.45, 0.25, V((s * (Wd / 2 - 0.05), yy, 1.25)), trim, root, axis="X", bevel=0.08)
            wheel(root, V((s * (Wd / 2 - 0.45), yy, 1.15)), s)
        # door livery decal
        if kind in ("police", "taxi") or True:
            dm = imgmat(f"Livery_{kind}_{name}", livery_texture(kind, body, f"livery_{kind}_{name}"), rough=0.3)
            plane("Livery", 6.0, 3.0, V((s * (Wd / 2 + 0.03), -0.6, 2.5)), dm, root,
                  rot=(0, 0, math.radians(-90 if s > 0 else 90)))
    # front: grille, lights, bumper ; back: lights, plate
    rb("Grille", (3.2, 0.2, 0.7), V((0, L_ / 2 + 0.02, 2.35)), trim, root, r=0.1)
    for k in range(3):
        rb("Slat", (3.0, 0.22, 0.06), V((0, L_ / 2 + 0.04, 2.15 + k * 0.2)), CHROME(), root, r=0.02)
    hl = pmat("HeadLight", (255, 250, 230), rough=0.1, emit=3.0)
    tl = pmat("TailLight", (220, 20, 30), rough=0.2, emit=2.5)
    for s in (-1, 1):
        rb("HeadL", (1.3, 0.25, 0.5), V((s * 2.5, L_ / 2 - 0.02, 2.55)), hl, root, r=0.15)
        rb("TailL", (1.4, 0.25, 0.5), V((s * 2.55, -L_ / 2 + 0.02, 2.6)), tl, root, r=0.15)
        rb("FogL", (0.5, 0.2, 0.3), V((s * 2.6, L_ / 2 + 0.08, 1.4)), hl, root, r=0.1)
    rb("BumperF", (Wd * 0.96, 0.6, 0.65), V((0, L_ / 2 + 0.05, 1.25)), trim, root, r=0.25)
    rb("BumperR", (Wd * 0.96, 0.6, 0.65), V((0, -L_ / 2 - 0.05, 1.3)), trim, root, r=0.25)
    plate = Image.new("RGB", (512, 128), (245, 205, 40) if kind != "police" else (240, 240, 240)); dd = ImageDraw.Draw(plate)
    dd.rectangle((0, 0, 511, 127), outline=(20, 20, 20), width=6)
    dd.text((256, 64), {"police": "BPD 01", "taxi": "TX 4R1"}.get(kind, "BX " + str(abs(hash(name)) % 900 + 100)), font=pfont(70), fill=(20, 20, 20), anchor="mm")
    pm = imgmat("Plate" + name, save_img(plate, "plate_" + name), rough=0.4)
    plane("PlateR", 2.2, 0.55, V((0, -L_ / 2 - 0.37, 1.95)), pm, root, rot=(0, 0, math.radians(180)))
    plane("PlateF", 2.2, 0.55, V((0, L_ / 2 + 0.37, 1.25)), pm, root)
    if kind == "police":
        rb("LightBarBase", (4.6, 1.0, 0.25), V((0, -0.9, 5.35)), trim, root, r=0.08)
        red = pmat("LBRed", (255, 30, 40), rough=0.2, emit=6.0); blue = pmat("LBBlue", (30, 90, 255), rough=0.2, emit=6.0)
        for k in range(4):
            rb("LBlight", (0.95, 0.8, 0.4), V((-1.6 + k * 1.07, -0.9, 5.6)), red if k < 2 else blue, root, r=0.12)
        rb("PushBar", (3.6, 0.4, 1.6), V((0, L_ / 2 + 0.55, 1.8)), trim, root, r=0.15)
        rb("Antenna", (0.06, 0.06, 1.6), V((1.2, -4.5, 4.4)), trim, root, r=0.02)
        for s in (-1, 1):
            rb("GrilleStrobe", (0.5, 0.15, 0.2), V((s * 0.8, L_ / 2 + 0.18, 2.75)), red if s < 0 else blue, root, r=0.06)
    if kind == "taxi":
        rb("TaxiSign", (2.6, 1.0, 0.7), V((0, -0.8, 5.5)), pmat("TaxiSign", (250, 230, 160), rough=0.3, emit=1.5), root, r=0.2)
        ts = Image.new("RGB", (512, 160), (250, 230, 160)); dd = ImageDraw.Draw(ts); dd.text((256, 80), "TAXI", font=pfont(110), fill=(20, 20, 22), anchor="mm")
        tm = imgmat("TaxiSignTxt", save_img(ts, "taxisign"), emit=1.2)
        plane("TaxiTxtF", 2.4, 0.6, V((0, -0.28, 5.5)), tm, root)
        plane("TaxiTxtB", 2.4, 0.6, V((0, -1.32, 5.5)), tm, root, rot=(0, 0, math.radians(180)))
    return root


# ---------------------------------------------------------------- FURNITURE
def bed(name, duvet=(70, 120, 200), frame=(120, 80, 50), loc=(0, 0, 0)):
    root = root_of(name, loc); w = wood("Wood" + str(frame), frame)
    rb("BedBase", (7.4, 10.0, 1.1), V((0, 0, 1.15)), w, root, r=0.15)
    for x in (-3.4, 3.4):
        for y in (-4.7, 4.7):
            rb("BedLeg", (0.5, 0.5, 0.8), V((x, y, 0.4)), w, root, r=0.1)
    rb("Headboard", (7.6, 0.6, 4.2), V((0, -5.1, 2.6)), w, root, r=0.2)
    for x in (-1.8, 1.8):
        rb("HBPanel", (3.0, 0.15, 2.4), V((x, -4.8, 3.0)), wood("WoodDk" + str(frame), dk(frame, 0.8)), root, r=0.1)
    rb("Mattress", (7.0, 9.6, 1.0), V((0, 0.1, 2.15)), fabric("Mattress", (240, 240, 236)), root, r=0.4)
    dv = fabric("Duvet" + str(duvet), duvet)
    rb("Duvet", (7.3, 6.6, 0.55), V((0, 1.6, 2.75)), dv, root, r=0.27)
    rb("DuvetFold", (7.35, 1.2, 0.7), V((0, -1.7, 2.82)), fabric("DuvetIn", (245, 245, 245)), root, r=0.33)
    for x in (-1.8, 1.8):
        rb("Pillow", (3.0, 1.6, 0.7), V((x, -3.9, 2.95)), fabric("Pillow", (250, 250, 248)), root, r=0.33,
           rot=(math.radians(-12), 0, 0))
    # bedside table + lamp
    t = root_of(name + "_Side", (loc[0] + 5.2, loc[1] - 4.0, loc[2]))
    rb("Nightstand", (2.4, 2.2, 2.4), V((0, 0, 1.3)), w, t, r=0.12)
    rb("Drawer", (2.0, 0.12, 0.8), V((0, 1.12, 1.7)), wood("WoodDk" + str(frame), dk(frame, 0.8)), t, r=0.05)
    rb("Knob", (0.25, 0.15, 0.2), V((0, 1.2, 1.7)), CHROME(), t, r=0.06)
    rcyl("LampBase", 0.4, 0.8, V((0, 0, 2.9)), pmat("Ceramic", (230, 220, 200), rough=0.3), t)
    rcyl("LampShade", 0.75, 0.9, V((0, 0, 3.75)), pmat("Shade", (250, 236, 200), rough=0.8, emit=1.2, emit_rgb=(255, 210, 140)), t,
         top_scale=0.65, bevel=0.03)
    return root


def sofa(name, colour=(110, 130, 150), seats=3, loc=(0, 0, 0)):
    root = root_of(name, loc); f = fabric("Sofa" + str(colour), colour); fd = fabric("SofaDk" + str(colour), dk(colour, 0.85))
    Wd = 3.0 * seats + 2.0
    rb("SofaBase", (Wd - 0.1, 4.0, 1.4), V((0, 0, 1.4)), fd, root, r=0.3)
    rb("SofaBack", (Wd - 0.12, 1.2, 3.0), V((0, -1.6, 2.9)), fd, root, r=0.45)
    for s in (-1, 1):
        rb("Arm", (1.2, 4.35, 2.4), V((s * (Wd / 2 - 0.6), 0, 2.0)), f, root, r=0.34)
    for k in range(seats):
        x = -Wd / 2 + 1.0 + 1.5 + k * 3.0
        rb("SeatCush", (2.9, 3.0, 0.75), V((x, 0.45, 2.45)), f, root, r=0.35)
        rb("BackCush", (2.85, 0.9, 2.2), V((x, -0.75, 3.55)), f, root, r=0.42, rot=(math.radians(-10), 0, 0))
    rb("ThrowPillow", (1.4, 0.5, 1.4), V((-Wd / 2 + 1.9, -0.05, 3.3)), fabric("Throw", (230, 170, 70)), root, r=0.24,
       rot=(math.radians(-15), 0, math.radians(20)))
    for x in (-Wd / 2 + 0.6, Wd / 2 - 0.6):
        for y in (-1.6, 1.6):
            rcyl("SofaLeg", 0.18, 0.7, V((x, y, 0.35)), wood("WoodLeg", (90, 60, 40)), root, top_scale=0.7)
    return root


def armchair(name, colour=(150, 70, 60), loc=(0, 0, 0)):
    return sofa(name, colour, seats=1, loc=loc)


def dining_set(name, wood_rgb=(150, 100, 60), loc=(0, 0, 0)):
    root = root_of(name, loc); w = wood("Wood" + str(wood_rgb), wood_rgb)
    rb("TableTop", (8.0, 5.0, 0.35), V((0, 0, 3.6)), w, root, r=0.12)
    rb("Apron", (7.4, 4.4, 0.5), V((0, 0, 3.2)), w, root, r=0.06)
    for x in (-3.5, 3.5):
        for y in (-2.0, 2.0):
            taper("TLeg", (0.45, 0.45, 3.1), V((x, y, 1.55)), w, root, top=(1.3, 1.3), r=0.06)
    for x, y, a in ((-2, 3.2, 180), (2, 3.2, 180), (-2, -3.2, 0), (2, -3.2, 0)):
        c = root_of(name + "_Chair", (loc[0] + x, loc[1] + y, loc[2])); c.rotation_euler = (0, 0, math.radians(a))
        rb("Seat", (2.2, 2.2, 0.3), V((0, 0, 2.2)), w, c, r=0.1)
        rb("SeatPad", (1.9, 1.9, 0.2), V((0, 0.05, 2.45)), fabric("SeatPad", (190, 60, 60)), c, r=0.09)
        for xx in (-0.9, 0.9):
            for yy in (-0.9, 0.9):
                rb("CLeg", (0.25, 0.25, 2.1), V((xx, yy, 1.05)), w, c, r=0.05)
            rb("Post", (0.25, 0.25, 2.6), V((xx, -0.95, 3.55)), w, c, r=0.06)
        for k in range(3):
            rb("Slat", (1.6, 0.15, 0.3), V((0, -0.95, 3.0 + k * 0.7)), w, c, r=0.05)
    return root


def monitor_img(name):
    im = Image.new("RGB", (640, 360), (40, 80, 140)); d = ImageDraw.Draw(im)
    for y in range(360): d.line((0, y, 640, y), fill=(40 + y // 6, 80 + y // 5, 160 + y // 8))
    d.rectangle((40, 40, 330, 250), fill=(245, 245, 250)); d.rectangle((40, 40, 330, 62), fill=(60, 120, 220))
    for k in range(6): d.rectangle((60, 80 + k * 26, 300 - k * 20, 92 + k * 26), fill=(180, 186, 200))
    d.rectangle((360, 90, 600, 300), fill=(30, 30, 36)); d.rectangle((360, 90, 600, 112), fill=(90, 90, 100))
    for k in range(7): d.rectangle((375, 125 + k * 22, 375 + 30 + (k * 37) % 170, 135 + k * 22), fill=(90, 220, 120) if k % 2 else (230, 200, 90))
    d.rectangle((0, 336, 640, 360), fill=(25, 25, 30))
    return save_img(im, name)


def keyboard_img(name):
    im = Image.new("RGB", (512, 160), (30, 30, 34)); d = ImageDraw.Draw(im)
    for r in range(4):
        for c in range(14):
            d.rounded_rectangle((8 + c * 36, 10 + r * 36, 38 + c * 36, 40 + r * 36), 5, fill=(58, 58, 64))
    d.rounded_rectangle((120, 150 - 6, 390, 155), 4, fill=(58, 58, 64))
    return save_img(im, name)


def desk_setup(name, loc=(0, 0, 0)):
    root = root_of(name, loc); w = wood("DeskWood", (200, 170, 130)); wd = wood("DeskWoodDk", (150, 120, 90))
    rb("DeskTop", (9.0, 4.0, 0.35), V((0, 0, 3.6)), w, root, r=0.1)
    rb("DrawerUnit", (2.6, 3.6, 3.3), V((3.0, 0, 1.75)), wd, root, r=0.1)
    for k in range(3):
        rb("DFront", (2.3, 0.12, 0.85), V((3.0, 1.82, 0.8 + k * 1.05)), w, root, r=0.05)
        rb("DHandle", (0.8, 0.12, 0.12), V((3.0, 1.92, 1.0 + k * 1.05)), CHROME(), root, r=0.04)
    for x in (-4.2,):
        for y in (-1.7, 1.7):
            rb("DLeg", (0.4, 0.4, 3.4), V((x, y, 1.7)), BLACKPL(), root, r=0.08)
    rb("MonStand", (1.2, 0.8, 0.12), V((-0.5, -0.9, 3.85)), BLACKPL(), root, r=0.05)
    rb("MonNeck", (0.25, 0.25, 1.1), V((-0.5, -1.0, 4.4)), BLACKPL(), root, r=0.06)
    rb("Monitor", (4.2, 0.25, 2.5), V((-0.5, -0.9, 5.6)), BLACKPL(), root, r=0.1)
    plane("Screen", 3.9, 2.2, V((-0.5, -0.76, 5.65)), imgmat("MonScreen", monitor_img("monitor"), emit=1.2), root)
    rb("Keyboard", (3.2, 1.0, 0.12), V((-0.5, 0.7, 3.84)), BLACKPL(), root, r=0.04)
    plane("Keys", 3.0, 0.9, V((-0.5, 0.7, 3.91)), imgmat("Keys", keyboard_img("keys")), root, rot=(math.radians(90), 0, 0))
    rb("Mouse", (0.4, 0.6, 0.2), V((1.6, 0.8, 3.86)), BLACKPL(), root, r=0.1)
    rcyl("Mug", 0.3, 0.6, V((-3.3, 0.6, 4.1)), pmat("MugRed", (200, 50, 50), rough=0.3), root)
    # office chair
    c = root_of(name + "_Chair", (loc[0] - 0.5, loc[1] + 3.6, loc[2])); c.rotation_euler = (0, 0, math.radians(180))
    for k in range(5):
        a = k * 2 * math.pi / 5
        rb("StarLeg", (0.3, 1.6, 0.25), V((math.sin(a) * 0.8, math.cos(a) * 0.8, 0.45)), BLACKPL(), c, r=0.08, rot=(0, 0, -a))
        rcyl("Caster", 0.18, 0.2, V((math.sin(a) * 1.55, math.cos(a) * 1.55, 0.2)), BLACKPL(), c, axis="X")
    rcyl("GasLift", 0.18, 1.6, V((0, 0, 1.3)), CHROME(), c)
    rb("Seat", (2.4, 2.4, 0.55), V((0, 0, 2.3)), fabric("ChairFab", (40, 44, 56)), c, r=0.25)
    rb("BackRest", (2.2, 0.45, 2.6), V((0, -1.2, 3.9)), fabric("ChairFab", (40, 44, 56)), c, r=0.3, rot=(math.radians(-8), 0, 0))
    for s in (-1, 1):
        rb("ArmRest", (0.3, 1.6, 0.18), V((s * 1.25, 0, 3.1)), BLACKPL(), c, r=0.06)
        rb("ArmPost", (0.2, 0.2, 0.7), V((s * 1.25, 0, 2.7)), BLACKPL(), c, r=0.05)
    return root


def wardrobe(name, wood_rgb=(240, 236, 228), loc=(0, 0, 0)):
    root = root_of(name, loc); w = wood("Ward" + str(wood_rgb), wood_rgb, scale=1.2)
    rb("WardBody", (6.0, 2.6, 8.4), V((0, 0, 4.45)), w, root, r=0.12)
    rb("Crown", (6.4, 2.9, 0.35), V((0, 0.05, 8.8)), w, root, r=0.1)
    rb("Plinth", (5.9, 2.5, 0.35), V((0, 0, 0.2)), wood("WardDk", dk(wood_rgb, 0.7)), root, r=0.05)
    for s in (-1, 1):
        x = s * 1.47
        rb("Door", (2.85, 0.15, 7.7), V((x, 1.32, 4.45)), w, root, r=0.06)
        for z, h in ((6.4, 2.6), (2.9, 3.6)):
            rb("Panel", (2.1, 0.08, h), V((x, 1.42, z)), wood("WardPanel" + str(wood_rgb), dk(wood_rgb, 0.92), scale=1.2), root, r=0.06)
        rb("WHandle", (0.14, 0.2, 1.2), V((s * 0.25, 1.5, 4.6)), CHROME(), root, r=0.06)
    return root


BOOK_COLS = [(180, 40, 40), (40, 80, 160), (40, 130, 80), (220, 180, 60), (120, 60, 140), (230, 230, 220), (30, 30, 36),
             (200, 110, 50), (90, 140, 190), (150, 30, 60)]


def bookshelf(name, wood_rgb=(110, 75, 45), loc=(0, 0, 0), seed=3):
    rng = random.Random(seed); root = root_of(name, loc); w = wood("Shelf" + str(wood_rgb), wood_rgb)
    rb("ShelfBack", (6.0, 0.2, 9.0), V((0, -1.05, 4.5)), wood("ShelfBk", dk(wood_rgb, 0.8)), root, r=0.05)
    for s in (-1, 1): rb("ShelfSide", (0.35, 2.3, 9.0), V((s * 2.85, 0, 4.5)), w, root, r=0.08)
    for k in range(5): rb("Shelf", (5.6, 2.2, 0.3), V((0, 0, 0.3 + k * 2.15)), w, root, r=0.05)
    rb("ShelfTop", (6.2, 2.5, 0.3), V((0, 0, 9.0)), w, root, r=0.08)
    for k in range(4):
        x = -2.5; z0 = 0.45 + k * 2.15
        while x < 2.4:
            bw = rng.uniform(0.25, 0.5); bh = rng.uniform(1.2, 1.85)
            if rng.random() < 0.12 and -1 < x < 1.2:   # gap with an ornament or leaning book (kept inside the frame)
                if rng.random() < 0.5:
                    rb("BookLean", (0.35, 1.5, 1.6), V((x + 0.5, -0.1, z0 + 0.75)), pmat("Book" + str(k), rng.choice(BOOK_COLS)), root,
                       r=0.04, rot=(0, math.radians(-25), 0))
                else:
                    rcyl("Vase", 0.35, 1.0, V((x + 0.4, 0, z0 + 0.5)), pmat("Vase", (90, 160, 160), rough=0.2), root, top_scale=0.6)
                x += 1.0; continue
            c = rng.choice(BOOK_COLS)
            rb("Book", (bw, 1.6, bh), V((x + bw / 2, -0.05, z0 + bh / 2)), pmat(f"Book{c}", c, rough=0.6), root, r=0.03)
            rb("BookBand", (bw + 0.01, 1.61, 0.08), V((x + bw / 2, -0.05, z0 + bh * 0.8)), pmat("BookBand", (220, 190, 90), rough=0.3, metal=0.6),
               root, r=0.01)
            x += bw + 0.03
    return root


def tv_img(name):
    im = Image.new("RGB", (640, 360)); d = ImageDraw.Draw(im)
    for y in range(360): d.line((0, y, 640, y), fill=(255 - y // 3, 140 - y // 5, 90 + y // 4))
    d.ellipse((380, 120, 520, 260), fill=(255, 220, 120))
    d.polygon([(0, 360), (180, 190), (330, 300), (470, 210), (640, 330), (640, 360)], fill=(60, 40, 90))
    d.polygon([(0, 360), (120, 280), (260, 340), (420, 290), (640, 360)], fill=(30, 20, 50))
    return save_img(im, name)


def tv_unit(name, loc=(0, 0, 0)):
    root = root_of(name, loc); w = wood("TVWood", (60, 50, 44))
    rb("Stand", (9.0, 2.6, 2.0), V((0, 0, 1.1)), w, root, r=0.1)
    for x in (-3.0, 0, 3.0):
        rb("StandDoor", (2.8, 0.1, 1.5), V((x, 1.32, 1.1)), wood("TVWood2", (80, 68, 58)), root, r=0.05)
        rb("SDKnob", (0.5, 0.1, 0.1), V((x, 1.4, 1.6)), CHROME(), root, r=0.03)
    for x in (-4.1, 4.1):
        rb("StandLeg", (0.3, 0.3, 0.4), V((x, 0, 0.2)), BLACKPL(), root, r=0.05)
    rb("TVFoot", (2.4, 1.0, 0.12), V((0, 0, 2.18)), BLACKPL(), root, r=0.05)
    rb("TVNeck", (0.4, 0.3, 0.6), V((0, -0.1, 2.5)), BLACKPL(), root, r=0.05)
    rb("TV", (7.2, 0.35, 4.2), V((0, -0.1, 4.8)), BLACKPL(), root, r=0.08)
    plane("TVScreen", 6.9, 3.9, V((0, 0.08, 4.8)), imgmat("TVScreen", tv_img("tv"), emit=1.5), root)
    rb("Console", (1.8, 1.2, 0.35), V((2.6, 0.3, 2.3)), pmat("ConsoleW", (240, 240, 244), rough=0.3), root, r=0.1)
    rb("ConsoleLight", (0.9, 0.05, 0.05), V((2.6, 0.92, 2.32)), pmat("CLight", (90, 180, 255), emit=4), root, r=0.02)
    rb("Gamepad", (0.9, 0.55, 0.22), V((-2.6, 0.5, 2.25)), BLACKPL(), root, r=0.12)
    return root


def fridge(name, colour=(232, 234, 238), loc=(0, 0, 0)):
    root = root_of(name, loc); m = pmat("Fridge" + str(colour), colour, rough=0.2, coat=0.5)
    rb("FridgeBody", (3.6, 3.4, 9.2), V((0, 0, 4.6)), m, root, r=0.25)
    rb("FreezerDoor", (3.5, 0.25, 2.9), V((0, 1.72, 7.4)), m, root, r=0.12)
    rb("FridgeDoor", (3.5, 0.25, 5.8), V((0, 1.72, 3.1)), m, root, r=0.12)
    rb("FHandleTop", (0.2, 0.35, 1.6), V((-1.4, 1.98, 6.9)), CHROME(), root, r=0.08)
    rb("FHandleBot", (0.2, 0.35, 2.6), V((-1.4, 1.98, 4.6)), CHROME(), root, r=0.08)
    for (x, z, c) in ((0.6, 4.2, (240, 90, 90)), (1.0, 3.2, (90, 160, 240)), (0.4, 7.5, (250, 210, 70))):
        rb("Magnet", (0.3, 0.1, 0.3), V((x, 1.88, z)), pmat("Mag" + str(c), c, rough=0.3), root, r=0.08)
    rb("Note", (0.9, 0.03, 1.1), V((0.9, 1.86, 3.6)), pmat("Note", (250, 245, 200), rough=0.8), root, r=0.01)
    return root


def kitchen(name, cab=(70, 90, 110), top=(230, 228, 222), loc=(0, 0, 0)):
    root = root_of(name, loc); cm = pmat("Cab" + str(cab), cab, rough=0.35); tm = pmat("Worktop" + str(top), top, rough=0.25)
    rb("Carcass", (12.0, 3.6, 3.4), V((0, 0, 1.9)), cm, root, r=0.08)
    rb("Kick", (11.8, 3.2, 0.25), V((0, -0.15, 0.13)), BLACKPL(), root, r=0.03)
    rb("Worktop", (12.3, 4.0, 0.35), V((0, 0.1, 3.75)), tm, root, r=0.08)
    for k in range(4):
        x = -4.5 + k * 3.0
        rb("CabDoor", (2.8, 0.1, 3.0), V((x, 1.82, 1.9)), cm, root, r=0.06)
        rb("CabPanel", (2.1, 0.06, 2.3), V((x, 1.88, 1.9)), pmat("CabPanel" + str(cab), dk(cab, 0.9), rough=0.35), root, r=0.06)
        rb("CabHandle", (1.0, 0.15, 0.12), V((x, 1.95, 3.1)), CHROME(), root, r=0.04)
    # sink + tap
    rb("SinkRim", (3.0, 2.2, 0.08), V((-3.0, 0.3, 3.95)), CHROME(), root, r=0.05)
    rb("SinkBasin", (2.6, 1.8, 0.08), V((-3.0, 0.3, 3.97)), pmat("SinkDark", (120, 124, 130), rough=0.3, metal=0.8), root, r=0.05)
    rcyl("TapBase", 0.15, 0.4, V((-3.0, -0.8, 4.15)), CHROME(), root)
    tube("Tap", [(-3.0, -0.8, 4.3), (-3.0, -0.8, 5.0), (-3.0, -0.4, 5.15), (-3.0, -0.05, 4.9)], 0.08, CHROME(), root)
    # hob
    rb("Hob", (3.0, 2.3, 0.06), V((2.6, 0.3, 3.95)), pmat("HobGlass", (20, 20, 24), rough=0.08, coat=1), root, r=0.04)
    for dx, dy, rr in ((-0.7, -0.5, 0.45), (0.7, -0.5, 0.35), (-0.7, 0.6, 0.35), (0.7, 0.6, 0.45)):
        rcyl("Ring", rr, 0.02, V((2.6 + dx, 0.3 + dy, 3.99)), pmat("HobRing", (90, 90, 96), rough=0.4), root, bevel=0.0)
    rb("Pan", (1.2, 1.2, 0.3), V((1.9, -0.2, 4.15)), pmat("PanBlack", (30, 30, 34), rough=0.4, metal=0.5), root, r=0.3)
    tube("PanHandle", [(1.3, -0.2, 4.2), (0.4, -0.2, 4.25)], 0.08, BLACKPL(), root)
    # backsplash tiles
    rb("Splash", (12.3, 0.2, 2.5), V((0, -1.75, 5.2)), wall_tiles("SplashTiles", (232, 238, 238)), root, r=0.03)
    return root


def floor_lamp(name, loc=(0, 0, 0)):
    root = root_of(name, loc)
    rcyl("LampFoot", 0.9, 0.2, V((0, 0, 0.12)), BLACKPL(), root)
    rcyl("LampPole", 0.08, 7.0, V((0, 0, 3.7)), CHROME(), root, bevel=0.0)
    rcyl("LampShade2", 1.3, 1.6, V((0, 0, 7.6)), pmat("Shade2", (245, 232, 205), rough=0.85, emit=1.5, emit_rgb=(255, 205, 140)), root,
         top_scale=0.6, bevel=0.03)
    return root


def door(name, colour=(250, 250, 248), frame=(235, 235, 230), loc=(0, 0, 0)):
    """Panelled interior door (4 x 7.5) with frame; the door leaf hangs on a hinge empty 'Hinge' (rotate Z to open)."""
    root = root_of(name, loc); fm = pmat("Frame" + str(frame), frame, rough=0.4); dm = pmat("DoorLeaf" + str(colour), colour, rough=0.35)
    for s in (-1, 1): rb("Jamb", (0.5, 0.9, 8.0), V((s * 2.3, 0, 4.0)), fm, root, r=0.06)
    rb("Head", (5.1, 0.9, 0.5), V((0, 0, 8.2)), fm, root, r=0.06)
    hinge = empty("Hinge", V((-2.0, 0, 0)), col=COL_PROPS, parent=root)
    rb("Leaf", (4.0, 0.3, 7.8), V((2.0, 0, 3.95)), dm, hinge, r=0.05)
    for z in (5.8, 2.4):
        rb("DPanel", (3.0, 0.08, 2.8 if z > 4 else 3.4), V((2.0, 0.18, z)), pmat("DPanel" + str(colour), dk(colour, 0.93), rough=0.35), hinge, r=0.1)
        rb("DPanelB", (3.0, 0.08, 2.8 if z > 4 else 3.4), V((2.0, -0.18, z)), pmat("DPanel" + str(colour), dk(colour, 0.93), rough=0.35), hinge, r=0.1)
    rb("Rose", (0.35, 0.1, 0.35), V((3.55, 0.2, 3.8)), CHROME(), hinge, r=0.1)
    rb("Lever", (0.7, 0.14, 0.12), V((3.3, 0.32, 3.8)), CHROME(), hinge, r=0.05)
    for z in (1.0, 6.9): rb("HingePlate", (0.12, 0.35, 0.6), V((0.02, 0, z)), CHROME(), hinge, r=0.03)
    return root


def laptop(name, loc=(0, 0, 0)):
    root = root_of(name, loc); al = pmat("Alu", (190, 192, 198), rough=0.3, metal=0.8)
    rb("LapBase", (3.0, 2.0, 0.14), V((0, 0, 0.07)), al, root, r=0.05)
    plane("LapKeys", 2.6, 1.0, V((0, -0.2, 0.15)), imgmat("LapKeys", keyboard_img("lapkeys")), root, rot=(math.radians(90), 0, 0))
    rb("Trackpad", (0.9, 0.55, 0.02), V((0, 0.6, 0.145)), pmat("Pad", (170, 172, 178), rough=0.25, metal=0.6), root, r=0.02)
    lid = empty("Lid", V((0, -1.0, 0.14)), col=COL_PROPS, parent=root); lid.rotation_euler = (math.radians(-15), 0, 0)
    rb("LapLid", (3.0, 0.1, 2.0), V((0, 0, 1.0)), al, lid, r=0.05)
    plane("LapScreen", 2.75, 1.75, V((0, 0.06, 1.0)), imgmat("LapScreen", monitor_img("lapscreen"), emit=1.2), lid)
    return root


def plant(name, loc=(0, 0, 0), seed=1):
    rng = random.Random(seed); root = root_of(name, loc)
    rcyl("Pot", 0.9, 1.6, V((0, 0, 0.8)), pmat("Terracotta", (190, 100, 60), rough=0.7), root, top_scale=1.25)
    rcyl("PotRim", 1.18, 0.3, V((0, 0, 1.6)), pmat("Terracotta2", (175, 90, 55), rough=0.7), root)
    rcyl("Soil", 1.0, 0.1, V((0, 0, 1.68)), pmat("Soil", (60, 40, 28), rough=1.0), root, bevel=0)
    leaf = pmat("Leaf", (60, 140, 60), rough=0.5); leaf2 = pmat("Leaf2", (90, 170, 70), rough=0.5)
    for k in range(14):
        a = k / 14 * 2 * math.pi + rng.uniform(-0.2, 0.2); h = rng.uniform(1.2, 2.6); out = rng.uniform(0.8, 1.6)
        p0 = V((0, 0, 1.7)); p1 = V((math.cos(a) * out * 0.4, math.sin(a) * out * 0.4, 1.7 + h * 0.7))
        p2 = V((math.cos(a) * out, math.sin(a) * out, 1.7 + h)); p3 = V((math.cos(a) * out * 1.3, math.sin(a) * out * 1.3, 1.7 + h * 0.75))
        lock(root, [p0, p1, p2, p3], rng.uniform(0.45, 0.65), 0.04, leaf if k % 2 else leaf2, n=14, wpow=1.6,
             center=lambda p: V((0, 0, p.z - 1.0)))
    return root


def clock_img(name):
    im = Image.new("RGBA", (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 508, 508), fill=(30, 30, 34, 255)); d.ellipse((30, 30, 482, 482), fill=(250, 248, 240, 255))
    for k in range(60):
        a = k / 60 * 2 * math.pi; r1 = 215; r2 = 190 if k % 5 == 0 else 205
        d.line((256 + math.sin(a) * r1, 256 - math.cos(a) * r1, 256 + math.sin(a) * r2, 256 - math.cos(a) * r2), fill=(30, 30, 34, 255),
               width=8 if k % 5 == 0 else 3)
    for n in range(1, 13):
        a = n / 12 * 2 * math.pi
        d.text((256 + math.sin(a) * 152, 256 - math.cos(a) * 152), str(n), font=pfont(42), fill=(30, 30, 34, 255), anchor="mm")
    return save_img(im, name)


def wall_clock(name, loc=(0, 0, 0)):
    root = root_of(name, loc)
    rcyl("ClockBody", 1.5, 0.35, V((0, 0, 0)), pmat("ClockRim", (30, 30, 34), rough=0.3), root, axis="Y")
    plane("ClockFace", 3.0, 3.0, V((0, 0.19, 0)), imgmat("ClockFace", clock_img("clockface")), root)
    rb("HourHand", (0.12, 0.05, 0.75), V((0.18, 0.23, 0.28)), BLACKPL(), root, r=0.02, rot=(0, math.radians(35), 0))
    rb("MinHand", (0.08, 0.05, 1.05), V((-0.32, 0.26, 0.36)), BLACKPL(), root, r=0.02, rot=(0, math.radians(-40), 0))
    rcyl("ClockPin", 0.08, 0.1, V((0, 0.29, 0)), pmat("RedPin", (200, 40, 40)), root, axis="Y")
    return root


def wheelie_bin(name, colour=(40, 90, 60), loc=(0, 0, 0)):
    root = root_of(name, loc); m = pmat("Bin" + str(colour), colour, rough=0.45)
    taper("BinBody", (2.6, 3.0, 4.2), V((0, 0, 2.3)), m, root, top=(1.08, 1.08), r=0.15)
    rb("BinLid", (2.95, 3.4, 0.25), V((0, 0.05, 4.5)), m, root, r=0.1)
    rb("BinHandle", (2.4, 0.3, 0.3), V((0, -1.75, 4.2)), m, root, r=0.12)
    for s in (-1, 1): rcyl("BinWheel", 0.45, 0.35, V((s * 1.0, -1.4, 0.45)), RUBBER(), root, axis="X")
    rb("BinNum", (0.9, 0.05, 0.5), V((0, 1.62, 3.3)), pmat("BinLabel", (240, 240, 240)), root, r=0.03)
    return root


PROP_LIST = [
    ("Police car", lambda: car("PoliceCar", "police")),
    ("Taxi", lambda: car("TaxiCar", "taxi")),
    ("Family car (any colour)", lambda: car("FamilyCar", "civilian", (200, 40, 50))),
    ("Bed + nightstand", lambda: bed("Bed")),
    ("Sofa", lambda: sofa("Sofa")),
    ("Armchair", lambda: armchair("Armchair")),
    ("Dining table + chairs", lambda: dining_set("Dining")),
    ("Desk + PC + office chair", lambda: desk_setup("Desk")),
    ("Wardrobe", lambda: wardrobe("Wardrobe")),
    ("Bookshelf", lambda: bookshelf("Bookshelf")),
    ("TV unit + console", lambda: tv_unit("TV")),
    ("Fridge", lambda: fridge("Fridge")),
    ("Kitchen counter (sink + hob)", lambda: kitchen("Kitchen")),
    ("Floor lamp", lambda: floor_lamp("FloorLamp")),
    ("Door (opens)", lambda: door("Door")),
    ("Laptop", lambda: laptop("Laptop")),
    ("House plant", lambda: plant("Plant")),
    ("Wall clock", lambda: wall_clock("Clock")),
    ("Wheelie bin", lambda: wheelie_bin("Bin")),
]
