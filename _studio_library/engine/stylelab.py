# stylelab.py - experimental: textured Roblox clothing, strand hair, 5 face styles.
# exec() after base helpers + charlib are loaded.
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEXDIR = "/home/claude/renders/lab/tex"
os.makedirs(TEXDIR, exist_ok=True)
V = Vector


# =============================================================== UV + textured parts
def uv_box(me, size):
    """Roblox-template style UVs: [right side][front][left side][back] row, top above front, bottom below."""
    if me.uv_layers:
        return
    sx, sy, sz = size
    uvl = me.uv_layers.new(name="UV")
    W, H = 2 * sx + 2 * sy, sz + 2 * sy
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        pos = n[ax] > 0
        for li in p.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            x = max(-sx / 2, min(sx / 2, x)); y = max(-sy / 2, min(sy / 2, y)); z = max(-sz / 2, min(sz / 2, z))
            if ax == 2:
                u = sy + (sx / 2 - x)
                v = sy + sz + (sy / 2 - y) if pos else y + sy / 2
            else:
                v = z + sz / 2 + sy
                if ax == 0:
                    u = (y + sy / 2) if pos else sy + sx + (sy / 2 - y)
                else:
                    u = sy + (sx / 2 - x) if pos else 2 * sy + sx + (x + sx / 2)
            uvl.data[li].uv = (u / W, v / H)


def img_mat(name, path, rough=0.75):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=False)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return m


def rpart_t(name, size, loc, material, parent):
    me = rbox_mesh(size, 0.04)
    uv_box(me, size)
    return solid(name, me, (1, 1, 1), loc, material, parent=parent, col=COL_CHARS)


# =============================================================== texture painting
PPU = 128


class Tpl:
    def __init__(s, size):
        s.sx, s.sy, s.sz = size
        s.W = int(round((2 * s.sx + 2 * s.sy) * PPU)); s.H = int(round((s.sz + 2 * s.sy) * PPU))
        s.img = Image.new("RGB", (s.W, s.H), (128, 128, 128))
        s.d = ImageDraw.Draw(s.img)
        s.top, s.mid = int(s.sy * PPU), int((s.sy + s.sz) * PPU)

    def reg(s, name):
        sx, sy = s.sx, s.sy
        cols = {"R": (0, sy), "front": (sy, sy + sx), "L": (sy + sx, 2 * sy + sx), "back": (2 * sy + sx, 2 * sy + 2 * sx)}
        if name in cols:
            a, b = cols[name]
            return (int(a * PPU), s.top, int(b * PPU), s.mid)
        if name == "top":
            return (int(sy * PPU), 0, int((sy + sx) * PPU), s.top)
        if name == "bottom":
            return (int(sy * PPU), s.mid, int((sy + sx) * PPU), s.H)
        if name == "band":
            return (0, s.top, s.W, s.mid)

    def zrow(s, z):  # stud height from bottom of part -> image row
        return int(s.mid - z * PPU)

    def band(s, z0, z1, col, caps=True):
        s.d.rectangle((0, s.zrow(z1), s.W, s.zrow(z0)), fill=col)
        if caps and z0 <= 0.01:
            s.d.rectangle(s.reg("bottom"), fill=col)

    def fx(s, name, fx):  # front-relative x (0..1 of region width) -> px
        x0, _, x1, _ = s.reg(name)
        return x0 + fx * (x1 - x0)

    def arr(s):
        return np.asarray(s.img).astype(np.float32)

    def set(s, a):
        s.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        s.d = ImageDraw.Draw(s.img)

    def save(s, name):
        p = f"{TEXDIR}/{name}.png"
        s.img.save(p)
        return p


def mask_rect(t, box, z0=None, z1=None):
    m = np.zeros((t.H, t.W), np.float32)
    x0, y0, x1, y1 = box
    if z1 is not None: y0 = max(y0, t.zrow(z1))
    if z0 is not None: y1 = min(y1, t.zrow(z0))
    m[y0:y1, x0:x1] = 1
    return m


def noise(t, amt, rng, streak=False, mask=None):
    a = t.arr()
    if streak:   # denim: vertical streaks
        n = rng.normal(0, 1, (max(2, t.H // 10), t.W)).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((t.W, t.H), Image.BILINEAR),
                       np.float32) - 128
        n = n / 40 * amt + rng.normal(0, amt * 0.5, (t.H, t.W))
    else:
        n = rng.normal(0, amt, (t.H, t.W))
        n = np.asarray(Image.fromarray((n + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)),
                       np.float32) - 128
    if mask is not None: n = n * mask
    t.set(a + n[..., None])


def edge_shade(t, amt=0.22, regions=("front", "back", "L", "R")):
    a = t.arr()
    f = np.ones((t.H, t.W), np.float32)
    for r in regions:
        x0, y0, x1, y1 = t.reg(r)
        xs = np.linspace(0, 1, x1 - x0)[None, :]; ys = np.linspace(0, 1, y1 - y0)[:, None]
        dx = np.minimum(xs, 1 - xs); dy = np.minimum(ys, 1 - ys)
        e = np.clip(np.minimum(dx * 1.6, dy * 3.0) / 0.25, 0, 1)
        f[y0:y1, x0:x1] = 1 - amt * (1 - e) ** 2
    t.set(a * f[..., None])


def folds(t, rng, regions, n=6, strength=0.32, ang=(-35, 35), length=(0.25, 0.6), z0=None, z1=None, width=7):
    lay = Image.new("L", (t.W, t.H), 128)
    d = ImageDraw.Draw(lay)
    for r in regions:
        x0, y0, x1, y1 = t.reg(r)
        if z1 is not None: y0 = max(y0, t.zrow(z1))
        if z0 is not None: y1 = min(y1, t.zrow(z0))
        for _ in range(n):
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            a = math.radians(90 + rng.uniform(*ang))
            L = rng.uniform(*length) * (y1 - y0)
            dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
            px, py = -math.sin(a) * 5, math.cos(a) * 5
            w = int(width * rng.uniform(0.7, 1.3))
            d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=55, width=w)
            d.line((cx - dx + px, cy - dy + py, cx + dx + px, cy + dy + py), fill=200, width=max(2, w // 2))
    lay = lay.filter(ImageFilter.GaussianBlur(5))
    s = (np.asarray(lay, np.float32) - 128) / 128 * strength
    t.set(t.arr() * (1 + s[..., None]))


def stitch(t, x0, y0, x1, y1, col, dash=10):
    L = math.hypot(x1 - x0, y1 - y0); n = int(L / dash)
    for i in range(0, n, 2):
        a, b = i / n, min(1, (i + 1) / n)
        t.d.line((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), fill=col, width=3)


def rip(t, rng, cx, cy, w, h):
    pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        rr = rng.uniform(0.75, 1.1)
        pts.append((cx + math.cos(a) * w / 2 * rr, cy + math.sin(a) * h / 2 * rr))
    t.d.polygon(pts, fill=(225, 222, 218), outline=(35, 35, 38))
    for yy in range(int(cy - h / 2 + 6), int(cy + h / 2 - 4), 7):
        span = w / 2 * math.sqrt(max(0, 1 - ((yy - cy) / (h / 2)) ** 2)) * 0.9
        t.d.line((cx - span, yy + rng.uniform(-2, 2), cx + span, yy + rng.uniform(-2, 2)), fill=(150, 150, 152), width=2)
    t.d.line([pts[i] for i in range(0, 14, 2)] + [pts[0]], fill=(60, 60, 62), width=3)


def shoes(t, upper, sole, lace=(245, 245, 245)):
    t.band(0, 0.46, upper)
    t.band(0, 0.13, sole)
    t.d.line((0, t.zrow(0.13), t.W, t.zrow(0.13)), fill=tuple(int(c * 0.6) for c in sole), width=3)
    x0, _, x1, _ = t.reg("front")
    cx = (x0 + x1) / 2
    for z in (0.26, 0.33, 0.4):
        t.d.line((cx - 24, t.zrow(z), cx + 24, t.zrow(z)), fill=lace, width=6)
    t.d.arc((x0 + 10, t.zrow(0.3), x1 - 10, t.zrow(0.0)), 200, 340, fill=tuple(int(c * 0.75) for c in upper), width=4)


def hand(t, skin):
    t.band(0, 0.32, skin)


def fill_all(t, col):
    t.d.rectangle((0, 0, t.W, t.H), fill=col)


def font(sz, bold=True):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""), sz)


# =============================================================== outfits (original designs)
def outfit_white_tee(skin, rng):
    """O1: oversized white long-sleeve tee w/ tiny chest text + grey distressed denim."""
    out = {}
    base = (234, 234, 236)
    t = Tpl((2, 1, 2)); fill_all(t, base)
    folds(t, rng, ["front", "back", "L", "R"], n=9, strength=0.28, ang=(-25, 25))
    edge_shade(t, 0.2)
    x = t.fx("front", 0.62)
    t.d.text((x, t.zrow(1.62)), "N.V.R.", font=font(26), fill=(30, 30, 32))
    noise(t, 3, rng)
    out["Torso"] = t
    for side in ("ArmL", "ArmR"):
        a = Tpl((1, 1, 2)); fill_all(a, base)
        folds(a, rng, ["front", "back", "L", "R"], n=5, strength=0.3, ang=(-60, 60), length=(0.15, 0.35))
        a.band(0.32, 0.42, (214, 214, 218))
        edge_shade(a, 0.18); hand(a, skin); noise(a, 3, rng)
        out[side] = a
    for side in ("LegL", "LegR"):
        l = Tpl((1, 1, 2)); fill_all(l, (72, 74, 80))
        noise(l, 14, rng, streak=True)
        a = l.arr()
        for r in ("front", "back"):   # faded thighs
            x0, y0, x1, y1 = l.reg(r)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            g = np.exp(-(((xx - (x0 + x1) / 2) / ((x1 - x0) * 0.35)) ** 2 + ((yy - l.zrow(1.45)) / 70.0) ** 2))
            a[y0:y1, x0:x1] += (g * 45)[..., None]
        l.set(a)
        folds(l, rng, ["front", "back"], n=4, strength=0.3, ang=(-70, 70), length=(0.1, 0.2), z0=0.5, z1=1.3, width=5)
        x0, y0, x1, y1 = l.reg("front")
        rip(l, rng, (x0 + x1) / 2 + rng.uniform(-15, 15), l.zrow(1.0), 70, 46)
        if side == "LegR":
            rip(l, rng, (x0 + x1) / 2 - 20, l.zrow(1.55), 40, 26)
        for r in ("L", "R"):
            x0, y0, x1, y1 = l.reg(r)
            stitch(l, (x0 + x1) / 2, y0, (x0 + x1) / 2, y1, (150, 140, 120))
        edge_shade(l, 0.25)
        shoes(l, (120, 120, 124), (230, 230, 230))
        out[side] = l
    return out


def outfit_grunge(skin, rng):
    """O2: grey sketch-graphic tee, crossbody strap, black ripped jeans."""
    out = {}
    base = (152, 152, 156)
    t = Tpl((2, 1, 2)); fill_all(t, base)
    x0, y0, x1, y1 = t.reg("front")
    for _ in range(55):   # sketchy doodle print
        cx, cy = rng.uniform(x0 + 30, x1 - 30), rng.uniform(y0 + 40, y1 - 50)
        pts = [(cx, cy)]
        for k in range(rng.randint(3, 7)):
            pts.append((pts[-1][0] + rng.uniform(-28, 28), pts[-1][1] + rng.uniform(-22, 22)))
        t.d.line(pts, fill=(60, 60, 64) if rng.random() < 0.7 else (220, 220, 222), width=rng.choice([2, 3, 4]))
    t.d.text((x0 + 40, y0 + 175), "lost & found", font=font(24, False), fill=(35, 35, 38))
    folds(t, rng, ["front", "back", "L", "R"], n=7, strength=0.25)
    # crossbody strap: right shoulder -> left hip (front), mirrored on back
    t.d.line((t.fx("front", 0.18), y0, t.fx("front", 0.95), y1 - 60), fill=(28, 28, 30), width=30)
    t.d.line((t.fx("back", 0.82), t.top, t.fx("back", 0.05), t.mid - 60), fill=(28, 28, 30), width=30)
    t.d.rectangle(t.reg("top"), fill=base)
    edge_shade(t, 0.22); noise(t, 4, rng)
    out["Torso"] = t
    for side in ("ArmL", "ArmR"):
        a = Tpl((1, 1, 2)); fill_all(a, skin)
        a.band(1.3, 2.0, base)
        folds(a, rng, ["front", "back", "L", "R"], n=2, strength=0.28, z0=1.3, length=(0.1, 0.2))
        a.band(1.3, 1.36, (120, 120, 124))
        edge_shade(a, 0.14); noise(a, 2, rng)
        out[side] = a
    for side in ("LegL", "LegR"):
        l = Tpl((1, 1, 2)); fill_all(l, (34, 34, 38))
        noise(l, 10, rng, streak=True)
        folds(l, rng, ["front", "back", "L", "R"], n=4, strength=0.4, ang=(-80, 80), length=(0.08, 0.18), z0=0.5,
              width=5)
        x0, y0, x1, y1 = l.reg("front")
        rip(l, rng, (x0 + x1) / 2, l.zrow(1.05), 80, 52)
        rip(l, rng, (x0 + x1) / 2 + 12, l.zrow(1.6), 46, 22)
        edge_shade(l, 0.25)
        shoes(l, (90, 90, 96), (225, 225, 225))
        out[side] = l
    return out


def outfit_puffer(skin, rng):
    """O3: black puffer jacket open over grey tee + blue jeans."""
    out = {}
    blk = (30, 30, 34)

    def quilt(t, mask, period=0.4):
        a = t.arr()
        rows = np.arange(t.H, dtype=np.float32)
        ph = ((t.mid - rows) / PPU % period) / period
        f = 0.7 + 0.6 * np.sin(math.pi * ph)
        f = 1 + (f[:, None] - 1) * mask
        t.set(a * f[..., None] + (mask * (f > 1.15) * 10)[..., None])

    t = Tpl((2, 1, 2)); fill_all(t, blk)
    m = np.ones((t.H, t.W), np.float32)
    x0, y0, x1, y1 = t.reg("front")
    cx = (x0 + x1) / 2
    inner = (int(cx - 0.3 * PPU), y0, int(cx + 0.3 * PPU), y1)
    m[inner[1]:inner[3], inner[0]:inner[2]] = 0
    quilt(t, m)
    t.d.rectangle(inner, fill=(176, 176, 182))
    folds(t, rng, [], n=0)
    for xx in (inner[0], inner[2]):
        t.d.line((xx, y0, xx, y1), fill=(120, 120, 126), width=5)
    t.d.rectangle((0, t.top, t.W, t.top + 22), fill=(20, 20, 22))
    edge_shade(t, 0.3); noise(t, 4, rng)
    out["Torso"] = t
    for side in ("ArmL", "ArmR"):
        a = Tpl((1, 1, 2)); fill_all(a, blk)
        quilt(a, np.ones((a.H, a.W), np.float32), period=0.36)
        a.band(0.32, 0.46, (16, 16, 18))
        edge_shade(a, 0.3); hand(a, skin); noise(a, 3, rng)
        out[side] = a
    for side in ("LegL", "LegR"):
        l = Tpl((1, 1, 2)); fill_all(l, (44, 64, 110))
        noise(l, 12, rng, streak=True)
        folds(l, rng, ["front", "back"], n=3, strength=0.3, ang=(-80, 80), length=(0.08, 0.15), z0=0.5, width=5)
        for r in ("L", "R"):
            x0, y0, x1, y1 = l.reg(r)
            stitch(l, (x0 + x1) / 2, y0, (x0 + x1) / 2, y1, (200, 160, 90))
        edge_shade(l, 0.25)
        shoes(l, (26, 26, 30), (240, 240, 240))
        out[side] = l
    return out


def outfit_red_shirt(skin, rng):
    """O4: red button-up with collar & pocket, black jeans with rolled cuffs, white trainers."""
    out = {}
    red, dred = (196, 30, 34), (150, 18, 24)
    t = Tpl((2, 1, 2)); fill_all(t, red)
    folds(t, rng, ["front", "back", "L", "R"], n=8, strength=0.3)
    x0, y0, x1, y1 = t.reg("front")
    cx = (x0 + x1) / 2
    for s in (-1, 1):   # collar flaps
        t.d.polygon([(cx + s * 6, y0), (cx + s * 0.42 * PPU, y0), (cx + s * 0.16 * PPU, y0 + 0.38 * PPU)],
                    fill=dred, outline=(70, 10, 12))
    t.d.line((cx, y0 + 0.3 * PPU, cx, y1), fill=dred, width=5)
    for k in range(5):
        by = y0 + (0.5 + k * 0.32) * PPU
        t.d.ellipse((cx + 10, by - 6, cx + 22, by + 6), fill=(240, 240, 240), outline=(120, 120, 120))
    px = t.fx("front", 0.62)
    t.d.rectangle((px, y0 + 0.55 * PPU, px + 0.42 * PPU, y0 + 1.0 * PPU), outline=dred, width=4)
    t.d.line((px, y0 + 0.66 * PPU, px + 0.42 * PPU, y0 + 0.66 * PPU), fill=dred, width=4)
    bx0, by0, bx1, _ = t.reg("back")
    t.d.rectangle((bx0, by0, bx1, by0 + 20), fill=dred)
    t.d.rectangle((0, t.mid - 14, t.W, t.mid), fill=dred)
    edge_shade(t, 0.22); noise(t, 4, rng)
    out["Torso"] = t
    for side in ("ArmL", "ArmR"):
        a = Tpl((1, 1, 2)); fill_all(a, red)
        folds(a, rng, ["front", "back", "L", "R"], n=4, strength=0.3, ang=(-60, 60), length=(0.12, 0.3))
        a.band(0.32, 0.55, dred)
        x0, _, x1, _ = a.reg("front")
        a.d.ellipse((x1 - 34, a.zrow(0.48), x1 - 22, a.zrow(0.39)), fill=(240, 240, 240))
        edge_shade(a, 0.2); hand(a, skin); noise(a, 3, rng)
        out[side] = a
    for side in ("LegL", "LegR"):
        l = Tpl((1, 1, 2)); fill_all(l, (26, 26, 30))
        noise(l, 8, rng, streak=True)
        folds(l, rng, ["front", "back"], n=3, strength=0.4, ang=(-80, 80), length=(0.08, 0.15), z0=0.7, width=5)
        for r in ("L", "R"):
            x0, y0, x1, y1 = l.reg(r)
            stitch(l, (x0 + x1) / 2, y0, (x0 + x1) / 2, y1, (110, 110, 115))
        l.band(0.44, 0.66, (64, 64, 70), caps=False)
        l.d.line((0, l.zrow(0.66), l.W, l.zrow(0.66)), fill=(110, 110, 116), width=3)
        l.d.line((0, l.zrow(0.55), l.W, l.zrow(0.55)), fill=(40, 40, 44), width=2)
        edge_shade(l, 0.25)
        shoes(l, (240, 240, 240), (170, 170, 176), lace=(200, 200, 205))
        out[side] = l
    return out


OUTFITS = {"O1": outfit_white_tee, "O2": outfit_grunge, "O3": outfit_puffer, "O4": outfit_red_shirt}


# =============================================================== textured body
def character2(name, skin_rgb, outfit_key, seed=1):
    rng = np.random.default_rng(seed)
    prng = random.Random(seed)

    class R:  # adapter: python-random-like API on numpy rng
        uniform = staticmethod(lambda a, b: float(rng.uniform(a, b)))
        normal = staticmethod(lambda m, s, shape=None: rng.normal(m, s, shape))
        random = staticmethod(lambda: float(rng.random()))
        randint = staticmethod(lambda a, b: int(rng.integers(a, b + 1)))
        choice = staticmethod(lambda seq: seq[int(rng.integers(len(seq)))])
    tex = OUTFITS[outfit_key](skin_rgb, R)
    paths = {k: t.save(f"{name}_{k}") for k, t in tex.items()}
    root = empty(name, V((0, 0, 0)), col=COL_CHARS)
    skin = mat(name + "_Skin", skin_rgb, rough=0.45)
    P = {"root": root, "skin": skin, "skin_rgb": skin_rgb, "faces": {}, "hair": {},
         "M": (lambda k, rgb, **kw: mat(f"{name}_{k}", rgb, **kw))}
    TM = lambda k: img_mat(f"{name}_{k}", paths[k])
    rpart_t("LegR", (1, 1, 2), V((0.5, 0, 1)), TM("LegR"), root)
    rpart_t("LegL", (1, 1, 2), V((-0.5, 0, 1)), TM("LegL"), root)
    rpart_t("Torso", (2, 1, 2), V((0, 0, 3)), TM("Torso"), root)
    for side, sx, k in (("Left", -1.5, "ArmL"), ("Right", 1.5, "ArmR")):
        sh = empty(side + "Shoulder", V((sx, 0, 3.5)), col=COL_CHARS, parent=root)
        rpart_t(side + "Arm", (1, 1, 2), V((0, 0, -0.5)), TM(k), sh)
        P[side] = sh
    neck = empty("Neck", V((0, 0, 4)), col=COL_CHARS, parent=root)
    P["neck"] = neck
    solid("Head", HEAD_MESH, (1, 1, 1), V((0, 0, 0.6)), skin, parent=neck, col=COL_CHARS)
    return P


# =============================================================== strand hair
def strand(parent, pts, r0, m, tip=0.004, power=0.9):
    cu = bpy.data.curves.new("Strand", "CURVE")
    cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 3; cu.use_fill_caps = True
    cu.resolution_u = 8
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    n = len(pts)
    for i, (p, co) in enumerate(zip(sp.points, pts)):
        p.co = (*co, 1)
        p.radius = r0 * (1 - i / (n - 1)) ** power + tip
    sp.use_endpoint_u = True; sp.order_u = min(4, n)
    cu.materials.append(m)
    ob = bpy.data.objects.new("Strand", cu)
    link(ob, COL_CHARS); ob.parent = parent
    return ob


C0 = Vector((0, -0.02, 0.74))


def scalp(az, el, k=1.0):
    a, e = math.radians(az), math.radians(el)
    return C0 + Vector((math.sin(a) * math.cos(e) * 0.66, math.cos(a) * math.cos(e) * 0.66, math.sin(e) * 0.52)) * k


def outward(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))).normalized()


def hair_cap(neck, m, size=(1.32, 1.34, 0.72), z=1.08, objs=None):
    ob = ball("HairCap", size, V((0, -0.03, z)), m, neck)
    objs.append(ob)
    return ob


def face_front(x, z, off=0.06):
    return V((x, surf_y(max(-0.59, min(0.59, x))) + off, z))


def H_emo(neck, M, c, rng):
    m = M("HairEmo", c, rough=0.42); o = []
    hair_cap(neck, m, objs=o)
    o.append(ball("HairBack", (1.3, 0.7, 0.9), V((0, -0.38, 0.85)), m, neck))
    for az in range(60, 300, 18):   # sides/back layered, flicking out
        az = az + rng.uniform(-6, 6)
        p0 = scalp(az, 60); n = outward(az, 0)
        p1 = scalp(az, 25, 1.07); p2 = scalp(az, -5, 1.12); p3 = p2 + n * 0.16 + V((0, 0, -0.28 - rng.uniform(0, 0.12)))
        o.append(strand(neck, [p0, p1, p2, p3], rng.uniform(0.15, 0.2), m))
    for i in range(7):   # heavy side-swept fringe over the eyes
        x = -0.42 + i * 0.13
        ztip = 0.66 + rng.uniform(-0.04, 0.08) + (0.1 if x < -0.2 else 0)
        o.append(strand(neck, [V((x * 0.5, 0.25, 1.32)), face_front(x * 0.8 + 0.05, 1.12, 0.09),
                               face_front(x + 0.12, 0.92, 0.08), face_front(x + 0.2, ztip, 0.06)],
                        rng.uniform(0.15, 0.19), m))
    for az in (-150, -120, 150, 170, 200):  # messy crown
        p0 = scalp(az, 70)
        o.append(strand(neck, [p0, scalp(az, 80, 1.15), scalp(az + 20, 75, 1.3)], 0.13, m))
    return o


def H_fluffy(neck, M, c, rng):
    m = M("HairFluffy", c, rough=0.6); o = []
    hair_cap(neck, m, size=(1.42, 1.44, 0.85), z=1.1, objs=o)
    for ring, el in ((0, 38), (1, 10), (2, 62)):
        step = 22 if ring < 2 else 40
        for az in range(0, 360, step):
            az = az + rng.uniform(-8, 8) + ring * 11
            if ring < 2 and -40 < ((az + 180) % 360 - 180) < 40:
                continue
            n = outward(az, el)
            p0 = scalp(az, el + 10, 0.95)
            p1 = scalp(az, el, 1.15)
            p2 = p1 + n * 0.16 + V((0, 0, -0.14 if ring < 2 else 0.1))
            o.append(strand(neck, [p0, p1, p2], rng.uniform(0.18, 0.23), m))
    for i in range(6):   # pointy fringe tufts
        x = -0.4 + i * 0.16
        o.append(strand(neck, [V((x * 0.6, 0.3, 1.3)), face_front(x, 1.08, 0.12), face_front(x + 0.05, 0.86 + rng.uniform(0, 0.08), 0.07)],
                        rng.uniform(0.15, 0.19), m))
    return o


def H_spikes(neck, M, c, rng):
    m = M("HairSpikes", c, rough=0.38); o = []
    hair_cap(neck, m, size=(1.3, 1.32, 0.66), objs=o)
    for az, el, L in ((180, 60, 1.0), (150, 55, 0.95), (210, 55, 0.95), (120, 40, 0.8), (240, 40, 0.8),
                      (180, 30, 0.85), (90, 35, 0.7), (270, 35, 0.7), (160, 80, 0.8), (200, 80, 0.8),
                      (130, 70, 0.75), (230, 70, 0.75), (0, 80, 0.55)):
        p0 = scalp(az, el, 0.9); n = outward(az, el + 15)
        p1 = scalp(az, el, 1.1) + V((0, 0, 0.05))
        p2 = p1 + n * L + V((0, -0.15, 0.12))
        o.append(strand(neck, [p0, p1, p2], 0.24, m, power=1.1))
    for x, z in ((-0.25, 0.86), (0.05, 0.8), (0.32, 0.88)):   # bangs
        o.append(strand(neck, [V((x * 0.5, 0.3, 1.3)), face_front(x, 1.1, 0.1), face_front(x + 0.08, z, 0.06)], 0.17, m))
    return o


def H_curtain(neck, M, c, rng):
    m = M("HairCurtain", c, rough=0.45); o = []
    hair_cap(neck, m, size=(1.36, 1.38, 0.76), objs=o)
    o.append(ball("HairBack", (1.34, 0.8, 1.1), V((0, -0.35, 0.78)), m, neck))
    for s in (-1, 1):
        for i in range(5):   # swoops from the centre part
            x0 = s * (0.03 + i * 0.05)
            sw = 0.25 + i * 0.07
            o.append(strand(neck, [V((x0, 0.2 - i * 0.06, 1.36)), face_front(s * sw * 0.7, 1.12, 0.1),
                                   face_front(s * (sw + 0.15), 0.85, 0.1),
                                   V((s * (0.58 + i * 0.03), 0.3 - i * 0.08, 0.5))], 0.15, m))
        for az in range(60, 170, 22):   # side/back length
            a = s * az
            p0 = scalp(a, 50); p1 = scalp(a, 10, 1.1); p2 = scalp(a, -30, 1.12) + V((0, 0, -0.15))
            o.append(strand(neck, [p0, p1, p2], 0.18, m))
    return o


def H_curly(neck, M, c, rng):
    m = M("HairCurly", c, rough=0.75); fade = M("HairFade", shade(c, 1.4) if sum(c) < 150 else shade(c, 0.7), rough=0.9)
    o = [ball("Fade", (1.27, 1.27, 0.5), V((0, -0.02, 1.0)), fade, neck)]
    for k in range(70):
        az = rng.uniform(0, 360); el = rng.uniform(45, 90)
        if el < 60 and -60 < ((az + 180) % 360 - 180) < 60 and False:
            continue
        p = scalp(az, el, 1.02) + V((0, 0, 0.14))
        r = rng.uniform(0.2, 0.3)
        o.append(ball("Curl", (r, r, r), p, m, neck))
    return o


def H_long(neck, M, c, rng):
    m = M("HairLong", c, rough=0.45); o = []
    hair_cap(neck, m, size=(1.36, 1.38, 0.76), objs=o)
    o.append(rpart("HairBackPanel", (1.3, 0.35, 1.9), V((0, -0.55, 0.3)), m, neck, r=0.16))
    for az in range(70, 291, 16):
        az = az + rng.uniform(-5, 5)
        n = outward(az, 0)
        p0 = scalp(az, 55); p1 = scalp(az, 5, 1.1)
        w = 0.08 * (1 if rng.random() < 0.5 else -1)
        pts = [p0, p1]
        for k in range(3):
            pts.append(pts[-1] + V((0, 0, -0.42)) + n * (w if k % 2 == 0 else -w) * 2)
        o.append(strand(neck, pts, 0.17, m))
    for s in (-1, 1):   # front locks over shoulders
        for i in range(2):
            x = s * (0.42 + i * 0.12)
            o.append(strand(neck, [V((s * 0.15, 0.3, 1.33)), face_front(s * 0.35, 1.05, 0.1),
                                   V((x, 0.32, 0.6)), V((x + s * 0.05, 0.45, 0.1)), V((x, 0.5, -0.35))], 0.15, m))
    for i in range(5):
        x = -0.3 + i * 0.15
        o.append(strand(neck, [V((x * 0.5, 0.3, 1.32)), face_front(x, 1.1, 0.1), face_front(x, 0.95, 0.07)], 0.14, m))
    return o


def H_buns(neck, M, c, rng):
    m = M("HairBuns", c, rough=0.5); o = []
    hair_cap(neck, m, objs=o)
    for s in (-1, 1):
        o.append(ball("Bun", (0.62, 0.62, 0.6), V((s * 0.5, -0.1, 1.42)), m, neck))
        for k in range(5):
            a = k * 72
            o.append(strand(neck, [V((s * 0.5, -0.1, 1.42)) + V((math.cos(math.radians(a)) * 0.2, math.sin(math.radians(a)) * 0.2, 0.15)),
                                   V((s * 0.5, -0.1, 1.42)) + V((math.cos(math.radians(a + 50)) * 0.33, math.sin(math.radians(a + 50)) * 0.33, 0.02))],
                            0.1, m))
    for i in range(8):   # choppy bangs
        x = -0.42 + i * 0.12
        o.append(strand(neck, [V((x * 0.5, 0.25, 1.32)), face_front(x, 1.1, 0.1),
                               face_front(x + 0.02, 0.9 + (0.05 if i % 2 else 0), 0.07)], 0.13, m))
    for s in (-1, 1):
        o.append(strand(neck, [scalp(s * 75, 40), scalp(s * 80, 0, 1.08), V((s * 0.62, 0.15, 0.35))], 0.12, m))
    return o


def H_quiff(neck, M, c, rng):
    m = M("HairQuiff", c, rough=0.35); o = []
    o.append(ball("Side", (1.29, 1.29, 0.5), V((0, -0.03, 1.05)), m, neck))
    for i in range(9):
        x = -0.36 + i * 0.09
        h = 0.32 + 0.12 * math.cos((x / 0.4) * 1.2)
        o.append(strand(neck, [V((x, 0.42, 1.12)), V((x * 1.05, 0.62, 1.3 + h * 0.5)),
                               V((x * 0.9, 0.35, 1.38 + h)), V((x * 0.8, -0.3, 1.35)), V((x * 0.7, -0.6, 1.05))],
                        0.17, m))
    return o


HAIR2 = {"H1": ("Messy emo fringe", H_emo, (22, 20, 22)), "H2": ("Fluffy wolf cut", H_fluffy, (236, 236, 240)),
         "H3": ("Anime spikes", H_spikes, (30, 30, 34)), "H4": ("Curtain middle part", H_curtain, (92, 58, 36)),
         "H5": ("Curly top + fade", H_curly, (24, 18, 16)), "H6": ("Long wavy", H_long, (226, 190, 110)),
         "H7": ("Space buns + bangs", H_buns, (236, 110, 160)), "H8": ("Slick quiff", H_quiff, (190, 90, 40))}


def add_hair(P, key, rng):
    name, fn, col = HAIR2[key]
    P["hair"][key] = fn(P["neck"], P["M"], col, rng)


def show_hair(P, key):
    for k, objs in P["hair"].items():
        for ob in objs:
            ob.hide_render = (k != key)


# =============================================================== five face styles
M_IRIS = mat("Iris", (60, 120, 220), rough=0.3)
M_IRIS2 = mat("Iris2", (120, 80, 40), rough=0.3)
M_BAG = mat("EyeBag", (150, 120, 140), rough=0.8)
FACE_SKIN = None


def lid(f, x, z, w, h, frac=0.5, lift=0.026):
    """Skin-coloured upper lid covering the top part of an eye + lid line."""
    f.oval(x, z + h * (1 - frac), w * 1.3, h * 1.0, FACE_SKIN, lift=lift)
    yl = z + h * (0.5 - frac)
    f.line([(x - w * 0.6, yl + 0.01), (x, yl), (x + w * 0.6, yl + 0.01)], M_INK, r=0.024, lift=lift + 0.006)


def brows(f, l, r, rad=0.026, lift=0.0):
    f.line(l, M_INK, r=rad, lift=lift); f.line(r, M_INK, r=rad, lift=lift)


def mirror(pts):
    return [(-x, z) for x, z in pts][::-1]


# ---- Style A: classic (current)
def A_happy(f): f.eyes(); f.line([(-0.16, -0.16), (0, -0.23), (0.16, -0.16)], M_INK)
def A_laugh(f): expr_laugh(f)
def A_angry(f): expr_angry(f)
def A_sad(f): expr_sad(f)
def A_shocked(f): expr_shocked(f)
def A_smug(f): expr_smug(f)


# ---- Style B: anime gloss
def b_eye(f, sx, z=0.07, w=0.17, h=0.27, look=0.0, iris=None, small=False):
    iris = iris or M_IRIS
    f.oval(sx, z, w, h, M_EYEWHITE)
    if small:
        f.oval(sx + look, z, w * 0.28, h * 0.25, M_INK, lift=0.012)
    else:
        f.oval(sx + look, z - 0.02, w * 0.82, h * 0.8, iris, lift=0.006)
        f.oval(sx + look, z - 0.03, w * 0.42, h * 0.42, M_INK, lift=0.012)
        f.oval(sx + look + w * 0.2, z + h * 0.14, w * 0.32, h * 0.24, M_SHINE, lift=0.018)
        f.oval(sx + look - w * 0.16, z - h * 0.24, w * 0.14, h * 0.1, M_SHINE, lift=0.018)
    f.line([(sx - w * 0.62, z + h * 0.36), (sx, z + h * 0.54), (sx + w * 0.62, z + h * 0.42)], M_INK, r=0.032, lift=0.02)


def b_blush(f):
    for sx in (-0.36, 0.36):
        f.oval(sx, -0.08, 0.16, 0.07, M_BLUSH, lift=0.002)


def B_happy(f):
    for sx in (-0.21, 0.21): b_eye(f, sx)
    f.oval(0, -0.2, 0.14, 0.08, M_INK); f.oval(0, -0.22, 0.08, 0.04, M_TONGUE, lift=0.008); b_blush(f)


def B_laugh(f):
    for sx in (-0.21, 0.21):
        f.line([(sx - 0.1, 0.03), (sx, 0.13), (sx + 0.1, 0.03)], M_INK, r=0.034)
    f.oval(0, -0.19, 0.32, 0.22, M_INK); f.oval(0, -0.25, 0.18, 0.09, M_TONGUE, lift=0.008); b_blush(f)


def B_angry(f):
    for sx in (-0.21, 0.21): b_eye(f, sx, h=0.22)
    brows(f, [(-0.34, 0.27), (-0.1, 0.16)], [(0.1, 0.16), (0.34, 0.27)], rad=0.036, lift=0.03)
    f.oval(0, -0.2, 0.26, 0.09, M_INK); f.oval(0, -0.19, 0.22, 0.04, M_EYEWHITE, lift=0.008)


def B_sad(f):
    for sx in (-0.21, 0.21):
        b_eye(f, sx, look=0.0)
        f.oval(sx, -0.06, 0.14, 0.08, M_TEAR, lift=0.024)
    brows(f, [(-0.32, 0.28), (-0.12, 0.34)], [(0.12, 0.34), (0.32, 0.28)])
    f.line([(-0.1, -0.22), (0, -0.18), (0.1, -0.22)], M_INK)


def B_shocked(f):
    for sx in (-0.21, 0.21): b_eye(f, sx, small=True)
    brows(f, [(-0.32, 0.33), (-0.1, 0.37)], [(0.1, 0.37), (0.32, 0.33)])
    f.oval(0, -0.21, 0.1, 0.14, M_INK)


def B_smug(f):
    for sx in (-0.21, 0.21):
        b_eye(f, sx, look=0.03)
        lid(f, sx, 0.07, 0.17, 0.27, frac=0.45)
    f.line([(-0.1, -0.19), (0.05, -0.2), (0.17, -0.13)], M_INK); b_blush(f)


# ---- Style C: bold cartoon (thick outlines)
def c_eye(f, sx, z=0.08, w=0.2, h=0.25, look=0.0, pup=0.08):
    f.oval(sx, z, w + 0.05, h + 0.05, M_INK)
    f.oval(sx, z, w, h, M_EYEWHITE, lift=0.006)
    f.oval(sx + look, z - 0.01, pup, pup * 1.25, M_INK, lift=0.012)
    f.oval(sx + look + 0.02, z + 0.03, pup * 0.35, pup * 0.35, M_SHINE, lift=0.018)


def C_happy(f):
    for sx in (-0.2, 0.2): c_eye(f, sx)
    brows(f, [(-0.3, 0.29), (-0.11, 0.31)], [(0.11, 0.31), (0.3, 0.29)], rad=0.04)
    f.oval(0, -0.2, 0.4, 0.2, M_INK)
    f.oval(0, -0.13, 0.32, 0.06, M_EYEWHITE, lift=0.006)
    f.oval(0, -0.25, 0.18, 0.07, M_TONGUE, lift=0.006)


def C_laugh(f):
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.11, 0.05), (sx, 0.15), (sx + 0.11, 0.05)], M_INK, r=0.045)
    f.oval(0, -0.19, 0.48, 0.28, M_INK)
    f.oval(0, -0.09, 0.4, 0.07, M_EYEWHITE, lift=0.006)
    f.oval(0, -0.27, 0.24, 0.1, M_TONGUE, lift=0.006)


def C_angry(f):
    for sx in (-0.2, 0.2): c_eye(f, sx, h=0.2, z=0.06)
    brows(f, [(-0.36, 0.27), (-0.08, 0.13)], [(0.08, 0.13), (0.36, 0.27)], rad=0.05, lift=0.03)
    f.oval(0, -0.2, 0.42, 0.15, M_INK)
    f.oval(0, -0.2, 0.36, 0.09, M_EYEWHITE, lift=0.006)
    for x in (-0.1, 0, 0.1):
        f.line([(x, -0.245), (x, -0.155)], M_INK, r=0.012, lift=0.012)


def C_sad(f):
    for sx in (-0.2, 0.2): c_eye(f, sx, look=0.0, pup=0.07)
    brows(f, [(-0.32, 0.27), (-0.1, 0.34)], [(0.1, 0.34), (0.32, 0.27)], rad=0.04)
    f.line([(-0.16, -0.25), (0, -0.17), (0.16, -0.25)], M_INK, r=0.038)
    f.oval(0.26, -0.08, 0.08, 0.15, M_TEAR, lift=0.02)


def C_shocked(f):
    for sx in (-0.2, 0.2): c_eye(f, sx, w=0.24, h=0.3, pup=0.05)
    brows(f, [(-0.32, 0.36), (-0.1, 0.4)], [(0.1, 0.4), (0.32, 0.36)], rad=0.04)
    f.oval(0, -0.22, 0.2, 0.24, M_INK); f.oval(0, -0.28, 0.12, 0.07, M_TONGUE, lift=0.008)


def C_smug(f):
    for sx in (-0.2, 0.2):
        c_eye(f, sx, look=0.04)
        lid(f, sx, 0.08, 0.25, 0.3, frac=0.45)
    brows(f, [(-0.32, 0.26), (-0.1, 0.27)], [(0.1, 0.31), (0.32, 0.37)], rad=0.04, lift=0.03)
    f.line([(-0.12, -0.19), (0.06, -0.2), (0.22, -0.11)], M_INK, r=0.038)


# ---- Style D: minimal dots
def d_eyes(f, z=0.07, r=0.1):
    for sx in (-0.19, 0.19): f.oval(sx, z, r, r * 1.15, M_INK)


def D_happy(f): d_eyes(f); f.line([(-0.12, -0.15), (0, -0.21), (0.12, -0.15)], M_INK, r=0.02)
def D_laugh(f):
    for sx in (-0.19, 0.19): f.line([(sx - 0.07, 0.05), (sx, 0.11), (sx + 0.07, 0.05)], M_INK, r=0.02)
    f.oval(0, -0.17, 0.2, 0.12, M_INK)
def D_angry(f): d_eyes(f, r=0.09); brows(f, [(-0.28, 0.22), (-0.1, 0.16)], [(0.1, 0.16), (0.28, 0.22)], rad=0.02); f.line([(-0.1, -0.2), (0, -0.17), (0.1, -0.2)], M_INK, r=0.02)
def D_sad(f): d_eyes(f, r=0.09); brows(f, [(-0.28, 0.2), (-0.1, 0.25)], [(0.1, 0.25), (0.28, 0.2)], rad=0.02); f.line([(-0.1, -0.21), (0, -0.17), (0.1, -0.21)], M_INK, r=0.02); f.oval(0.22, -0.03, 0.05, 0.09, M_TEAR, lift=0.004)
def D_shocked(f): d_eyes(f, r=0.08); brows(f, [(-0.27, 0.27), (-0.1, 0.3)], [(0.1, 0.3), (0.27, 0.27)], rad=0.02); f.oval(0, -0.19, 0.09, 0.11, M_INK)
def D_smug(f):
    for sx in (-0.19, 0.19): f.line([(sx - 0.08, 0.07), (sx + 0.08, 0.07)], M_INK, r=0.022)
    f.line([(-0.08, -0.18), (0.06, -0.18), (0.16, -0.12)], M_INK, r=0.02)


# ---- Style E: chill / grunge (heavy lids, eye bags)
def e_eye(f, sx, z=0.07, w=0.19, h=0.17, frac=0.42, look=0.02, bags=True):
    f.oval(sx, z, w, h, M_EYEWHITE)
    f.oval(sx + look, z - 0.005, w * 0.5, h * 0.72, M_INK, lift=0.008)
    f.oval(sx + look + 0.025, z + 0.02, 0.03, 0.03, M_SHINE, lift=0.014)
    if frac: lid(f, sx, z, w, h, frac=frac)
    if bags:
        f.line([(sx - w * 0.45, z - h * 0.62), (sx, z - h * 0.75), (sx + w * 0.45, z - h * 0.62)], M_BAG, r=0.016)


def E_happy(f):  # chill
    for sx in (-0.2, 0.2): e_eye(f, sx)
    brows(f, [(-0.3, 0.22), (-0.1, 0.22)], [(0.1, 0.22), (0.3, 0.22)], rad=0.026)
    f.line([(-0.08, -0.2), (0.04, -0.2), (0.12, -0.17)], M_INK, r=0.022)


def E_laugh(f):
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.1, 0.05), (sx, 0.1), (sx + 0.1, 0.05)], M_INK, r=0.026)
        f.line([(sx - 0.08, -0.04), (sx, -0.06), (sx + 0.08, -0.04)], M_BAG, r=0.016)
    f.oval(0, -0.2, 0.3, 0.15, M_INK); f.oval(0, -0.15, 0.24, 0.05, M_EYEWHITE, lift=0.006)


def E_angry(f):
    for sx in (-0.2, 0.2): e_eye(f, sx, frac=0.5, look=0)
    brows(f, [(-0.33, 0.21), (-0.09, 0.12)], [(0.09, 0.12), (0.33, 0.21)], rad=0.036, lift=0.035)
    f.oval(0, -0.21, 0.26, 0.08, M_INK); f.oval(0, -0.21, 0.22, 0.035, M_EYEWHITE, lift=0.006)


def E_sad(f):
    for sx in (-0.2, 0.2): e_eye(f, sx, frac=0.5, look=0)
    brows(f, [(-0.3, 0.18), (-0.1, 0.25)], [(0.1, 0.25), (0.3, 0.18)])
    f.line([(-0.1, -0.22), (0, -0.19), (0.1, -0.22)], M_INK, r=0.022)


def E_shocked(f):
    for sx in (-0.2, 0.2): e_eye(f, sx, w=0.2, h=0.22, frac=0, look=0)
    brows(f, [(-0.3, 0.3), (-0.1, 0.32)], [(0.1, 0.32), (0.3, 0.3)])
    f.oval(0, -0.21, 0.09, 0.11, M_INK)


def E_smug(f):
    for sx in (-0.2, 0.2): e_eye(f, sx, frac=0.6, look=0.05)
    brows(f, [(-0.3, 0.2), (-0.1, 0.2)], [(0.1, 0.24), (0.3, 0.3)], lift=0.035)
    f.line([(-0.1, -0.19), (0.06, -0.19), (0.17, -0.13)], M_INK, r=0.022)


FACE_STYLES = {
    "A": ("Classic", [A_happy, A_laugh, A_angry, A_sad, A_shocked, A_smug]),
    "B": ("Anime gloss", [B_happy, B_laugh, B_angry, B_sad, B_shocked, B_smug]),
    "C": ("Bold cartoon", [C_happy, C_laugh, C_angry, C_sad, C_shocked, C_smug]),
    "D": ("Minimal dots", [D_happy, D_laugh, D_angry, D_sad, D_shocked, D_smug]),
    "E": ("Chill / grunge", [E_happy, E_laugh, E_angry, E_sad, E_shocked, E_smug]),
}
EMOTIONS = ["happy", "laugh", "angry", "sad", "shocked", "smug"]


def add_face(P, key, fn):
    global FACE_SKIN
    FACE_SKIN = P["skin"]
    f = Face(P["neck"], key)
    fn(f)
    P["faces"][key] = f.objs


def show_face2(P, key):
    for k, objs in P["faces"].items():
        for ob in objs:
            ob.hide_render = (k != key)
