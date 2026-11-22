# garments.py - modular Roblox clothing generator (tops, overlays, bottoms, shoes, 3D accessories)
# + themed random looks. Needs stylelab.py (Tpl & painting helpers) and hair2.py / faces2.py.


class RNG:
    def __init__(s, seed):
        s.g = np.random.default_rng(seed)
    def uniform(s, a, b): return float(s.g.uniform(a, b))
    def normal(s, m, sd, shape=None): return s.g.normal(m, sd, shape)
    def random(s): return float(s.g.random())
    def randint(s, a, b): return int(s.g.integers(a, b + 1))
    def choice(s, seq): return seq[int(s.g.integers(len(seq)))]


def dk(c, k=0.75): return tuple(max(0, min(255, int(v * k))) for v in c)


def new_set():
    return {"Torso": Tpl((2, 1, 2)), "ArmL": Tpl((1, 1, 2)), "ArmR": Tpl((1, 1, 2)),
            "LegL": Tpl((1, 1, 2)), "LegR": Tpl((1, 1, 2))}


TOPS, ARMS, LEGS = ("Torso",), ("ArmL", "ArmR"), ("LegL", "LegR")


# ---------------------------------------------------------------- patterns
def pat_check(t, c1, c2, size=24, box=None):
    x0, y0, x1, y1 = box or (0, 0, t.W, t.H)
    for yy in range(y0, y1, size):
        for xx in range(x0, x1, size):
            if ((xx - x0) // size + (yy - y0) // size) % 2:
                t.d.rectangle((xx, yy, min(xx + size, x1) - 1, min(yy + size, y1) - 1), fill=c2)


def pat_plaid(t, base, line, size=40, box=None):
    x0, y0, x1, y1 = box or (0, 0, t.W, t.H)
    for xx in range(x0, x1, size):
        t.d.line((xx, y0, xx, y1), fill=line, width=6)
    for yy in range(y0, y1, size):
        t.d.line((x0, yy, x1, yy), fill=line, width=6)


def pat_pinstripe(t, col, step=22, box=None):
    x0, y0, x1, y1 = box or (0, 0, t.W, t.H)
    for xx in range(x0, x1, step):
        t.d.line((xx, y0, xx, y1), fill=col, width=2)


def pat_stripes(t, col, step=36, w=14, box=None):
    x0, y0, x1, y1 = box or (0, 0, t.W, t.H)
    for yy in range(y0, y1, step):
        t.d.rectangle((x0, yy, x1, yy + w), fill=col)


def knit_ribs(t, col, step=9):
    for xx in range(0, t.W, step):
        t.d.line((xx, 0, xx, t.H), fill=col, width=2)


# ---------------------------------------------------------------- tops
def top_base(S, col, rng, skin, sleeve="long", pattern=None, knit=False):
    for k in TOPS + ARMS:
        t = S[k]; fill_all(t, col)
        if pattern: pattern(t)
        if knit: knit_ribs(t, dk(col, 0.88))
    folds(S["Torso"], rng, ["front", "back", "L", "R"], n=8, strength=0.26)
    for k in ARMS:
        a = S[k]
        folds(a, rng, ["front", "back", "L", "R"], n=4, strength=0.28, ang=(-60, 60), length=(0.12, 0.3))
        if sleeve == "short":
            a.band(0, 1.28, skin); a.band(1.28, 1.36, dk(col, 0.8), caps=False)
        elif sleeve == "none":
            a.band(0, 2.0, skin)
        else:
            a.band(0.32, 0.46 if not knit else 0.55, dk(col, 0.82), caps=False)
            hand(a, skin)
    if knit:
        S["Torso"].band(0, 0.2, dk(col, 0.82), caps=False)


def chest_print(S, text, col, size=40, y=0.75):
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front")
    f = font(size); tw = t.d.textlength(text, font=f)
    t.d.text(((x0 + x1 - tw) / 2, y0 + y * PPU - size), text, font=f, fill=col)


def small_logo(S, text, col, size=18):
    t = S["Torso"]; t.d.text((t.fx("front", 0.6), t.zrow(1.55)), text, font=font(size), fill=col)


def collar_flaps(t, col, outline, spread=0.42, drop=0.38):
    x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    for s in (-1, 1):
        t.d.polygon([(cx + s * 6, y0), (cx + s * spread * PPU, y0), (cx + s * 0.16 * PPU, y0 + drop * PPU)],
                    fill=col, outline=outline)


def placket(t, col, buttons=5, start=0.3, btn=(240, 240, 240)):
    x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.line((cx, y0 + start * PPU, cx, y1), fill=col, width=5)
    for k in range(buttons):
        by = y0 + (start + 0.2 + k * 0.32) * PPU
        if by < y1 - 10:
            t.d.ellipse((cx + 10, by - 6, cx + 22, by + 6), fill=btn, outline=(120, 120, 120))


def d_button_shirt(S, col, rng, skin, pattern=None):
    top_base(S, col, rng, skin, pattern=pattern)
    t = S["Torso"]; collar_flaps(t, dk(col, 0.8), dk(col, 0.45)); placket(t, dk(col, 0.8))
    px = t.fx("front", 0.62); y0 = t.reg("front")[1]
    t.d.rectangle((px, y0 + 0.55 * PPU, px + 0.42 * PPU, y0 + PPU), outline=dk(col, 0.75), width=4)


def d_polo(S, col, rng, skin, logo=None, logo_col=(255, 255, 255)):
    top_base(S, col, rng, skin, sleeve="short")
    t = S["Torso"]; collar_flaps(t, dk(col, 0.85), dk(col, 0.5), spread=0.34, drop=0.26)
    placket(t, dk(col, 0.8), buttons=2, start=0.2)
    if logo: small_logo(S, logo, logo_col)


def d_turtleneck(S, col, rng, skin):
    top_base(S, col, rng, skin, knit=True)
    t = S["Torso"]; t.d.rectangle((0, t.top, t.W, t.top + 30), fill=dk(col, 0.85))
    for xx in range(0, t.W, 9):
        t.d.line((xx, t.top, xx, t.top + 30), fill=dk(col, 0.7), width=2)


def d_tee(S, col, rng, skin, text=None, text_col=(20, 20, 22)):
    top_base(S, col, rng, skin, sleeve="short")
    t = S["Torso"]; x0, y0, x1, _ = t.reg("front"); cx = (x0 + x1) / 2
    t.d.arc((cx - 40, y0 - 30, cx + 40, y0 + 24), 0, 180, fill=dk(col, 0.75), width=6)
    if text: chest_print(S, text, text_col)


def d_hoodie(S, col, rng, skin, text=None):
    top_base(S, col, rng, skin)
    t = S["Torso"]; d = dk(col, 0.78)
    flat_pocket = (t.fx("front", 0.2), t.zrow(0.62), t.fx("front", 0.8), t.zrow(0.12))
    t.d.rectangle(flat_pocket, outline=d, width=5)
    for fx in (0.38, 0.62):
        t.d.line((t.fx("front", fx), t.reg("front")[1], t.fx("front", fx), t.zrow(1.55)), fill=(245, 245, 245), width=6)
    bx0, by0, bx1, _ = t.reg("back")
    t.d.ellipse((bx0 + 40, by0 - 60, bx1 - 40, by0 + 110), fill=d)
    if text: chest_print(S, text, (250, 250, 250), size=34, y=0.9)


def d_blazer(S, col, rng, skin, inner=(245, 245, 245), inner_kind="tee"):
    top_base(S, col, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 0.26 * PPU, y0), (cx + 0.26 * PPU, y0), (cx + 0.05 * PPU, y0 + 1.25 * PPU),
                 (cx - 0.05 * PPU, y0 + 1.25 * PPU)], fill=inner)
    if inner_kind == "turtle":
        t.d.rectangle((cx - 0.26 * PPU, y0, cx + 0.26 * PPU, y0 + 24), fill=dk(inner, 0.85))
    lap = dk(col, 0.82)
    for s in (-1, 1):
        t.d.polygon([(cx + s * 0.26 * PPU, y0), (cx + s * 0.5 * PPU, y0), (cx + s * 0.4 * PPU, y0 + 0.5 * PPU),
                     (cx + s * 0.24 * PPU, y0 + 0.62 * PPU), (cx + s * 0.05 * PPU, y0 + 1.25 * PPU)],
                    fill=lap, outline=dk(col, 0.55))
    t.d.line((cx, y0 + 1.25 * PPU, cx, y1), fill=dk(col, 0.55), width=3)
    for by in (1.38, 1.65):
        t.d.ellipse((cx - 8, y0 + by * PPU - 8, cx + 8, y0 + by * PPU + 8), fill=dk(col, 0.45))
    for fx in (0.12, 0.62):
        t.d.rectangle((t.fx("front", fx), t.zrow(0.55), t.fx("front", fx + 0.26), t.zrow(0.45)), fill=dk(col, 0.8),
                      outline=dk(col, 0.55))
    for k in ARMS:
        a = S[k]; xa, _, xb, _ = a.reg("front")
        for j in range(3):
            a.d.ellipse((xb - 30 - j * 16, a.zrow(0.52), xb - 20 - j * 16, a.zrow(0.44)), fill=dk(col, 0.45))


def d_chef_jacket(S, col, rng, skin, piping=(30, 30, 34)):
    top_base(S, col, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.rectangle((0, t.top, t.W, t.top + 26), fill=dk(col, 0.95))
    t.d.line((0, t.top + 26, t.W, t.top + 26), fill=piping, width=4)
    t.d.line((cx + 0.32 * PPU, y0 + 26, cx + 0.32 * PPU, y1), fill=dk(col, 0.78), width=4)
    for k in range(4):
        by = y0 + (0.42 + k * 0.36) * PPU
        for bx in (cx - 0.28 * PPU, cx + 0.18 * PPU):
            t.d.ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=dk(col, 0.7), outline=dk(col, 0.5))
    for k in ARMS:
        a = S[k]; a.band(0.32, 0.5, dk(col, 0.92), caps=False)
        a.d.line((0, a.zrow(0.5), a.W, a.zrow(0.5)), fill=piping, width=4)


def d_sweater(S, col, rng, skin, stripe=None):
    pat = (lambda t: pat_stripes(t, stripe, step=48, w=18)) if stripe else None
    top_base(S, col, rng, skin, pattern=pat, knit=True)
    t = S["Torso"]; x0, y0, x1, _ = t.reg("front"); cx = (x0 + x1) / 2
    t.d.arc((cx - 46, y0 - 34, cx + 46, y0 + 30), 0, 180, fill=dk(col, 0.7), width=10)


# ---------------------------------------------------------------- overlays
def o_apron(S, col, rng, flour=False, text=None, text_col=(250, 250, 250), bib=True, legs=False):
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    hw = 0.62 * PPU
    edge = dk(col, 0.7)
    if bib:
        t.d.rectangle((cx - hw, t.zrow(1.55), cx + hw, y1), fill=col, outline=edge, width=3)
        for s in (-1, 1):
            t.d.line((cx + s * hw, t.zrow(1.55), cx + s * 0.4 * PPU, y0), fill=edge, width=14)
            t.d.line((t.fx("back", 0.5 - s * 0.3), t.top, t.fx("back", 0.5 + s * 0.2), t.zrow(0.3)), fill=edge, width=14)
        stitch(t, cx - hw + 8, t.zrow(1.55) + 8, cx + hw - 8, t.zrow(1.55) + 8, dk(col, 1.25))
    t.d.rectangle((0, t.zrow(0.32), t.W, t.zrow(0.18)), fill=edge)
    for k in (LEGS if legs else ()):
        l = S[k]; lx0, ly0, lx1, ly1 = l.reg("front")
        inner = lx0 if k == "LegR" else lx1
        l.d.rectangle((lx0, ly0, lx1, l.zrow(0.85)), fill=col)
        l.d.line((lx0, l.zrow(0.85), lx1, l.zrow(0.85)), fill=edge, width=4)
        stitch(l, lx0, l.zrow(0.85) - 10, lx1, l.zrow(0.85) - 10, dk(col, 1.25))
    if text:
        sz = 26
        while sz > 10 and t.d.textlength(text, font=font(sz)) > 1.1 * PPU: sz -= 1
        f = font(sz); tw = t.d.textlength(text, font=f)
        t.d.text((cx - tw / 2, t.zrow(1.0)), text, font=f, fill=text_col)
    if flour:
        for k in ("Torso",):
            tt = S[k]; lay = Image.new("L", (tt.W, tt.H), 0); d = ImageDraw.Draw(lay)
            fx0, fy0, fx1, fy1 = tt.reg("front")
            for _ in range(14):
                x, y, r = rng.uniform(fx0, fx1), rng.uniform(fy0 + (fy1 - fy0) * 0.35, fy1), rng.uniform(3, 11)
                d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=int(rng.uniform(40, 110)))
            m = np.asarray(lay.filter(ImageFilter.GaussianBlur(5)), np.float32)[..., None] / 255
            a = tt.arr(); tt.set(a * (1 - m) + 248 * m)


# ---------------------------------------------------------------- bottoms
def b_trousers(S, col, rng, kind="jeans", skin=None, accent=None):
    for k in LEGS:
        l = S[k]; fill_all(l, col)
        if kind == "jeans":
            noise(l, 12, rng, streak=True)
            for r in ("L", "R"):
                x0, y0, x1, y1 = l.reg(r); stitch(l, (x0 + x1) / 2, y0, (x0 + x1) / 2, y1, (200, 160, 90))
        elif kind == "check":
            pat_check(l, col, accent or (30, 30, 34), size=14)
        elif kind == "plaid":
            pat_plaid(l, col, accent or dk(col, 0.6))
        elif kind == "pinstripe":
            pat_pinstripe(l, accent or dk(col, 1.6))
        folds(l, rng, ["front", "back"], n=3, strength=0.32, ang=(-80, 80), length=(0.08, 0.16), z0=0.5, width=5)
        if kind in ("tailored", "pinstripe", "chinos"):
            for r in ("front", "back"):
                x0, y0, x1, y1 = l.reg(r); cx = (x0 + x1) / 2
                l.d.line((cx, y0, cx, y1), fill=dk(col, 1.25 if sum(col) < 200 else 0.85), width=3)
        if kind == "cargo":
            for r in ("L", "R"):
                x0, y0, x1, y1 = l.reg(r)
                l.d.rectangle((x0 + 14, l.zrow(1.25), x1 - 14, l.zrow(0.8)), fill=dk(col, 0.9), outline=dk(col, 0.6), width=4)
                l.d.rectangle((x0 + 10, l.zrow(1.3), x1 - 10, l.zrow(1.15)), fill=dk(col, 0.8), outline=dk(col, 0.55), width=3)
        if kind == "shorts":
            l.band(0, 1.05, skin); l.band(1.05, 1.12, dk(col, 0.75), caps=False)
        if kind == "skirt":
            l.band(0, 0.95, skin)
            for r in ("front", "back", "L", "R"):
                x0, y0, x1, y1 = l.reg(r)
                for xx in range(x0 + 16, x1, 32):
                    l.d.line((xx, y0, xx, l.zrow(0.95)), fill=dk(col, 0.7), width=3)
            l.band(0.95, 1.0, dk(col, 0.7), caps=False)
        edge_shade(l, 0.24)


def s_shoes(S, kind, col, rng, skin=None):
    for k in LEGS:
        l = S[k]
        if kind == "trainers":
            shoes(l, col, (240, 240, 240))
        elif kind == "boots":
            l.band(0, 0.75, col); l.band(0, 0.12, dk(col, 0.5))
            x0, _, x1, _ = l.reg("front"); cx = (x0 + x1) / 2
            for z in (0.3, 0.42, 0.54, 0.66):
                l.d.line((cx - 20, l.zrow(z), cx + 20, l.zrow(z - 0.05)), fill=dk(col, 1.6), width=4)
        elif kind == "loafers":
            l.band(0, 0.28, col); l.band(0, 0.08, dk(col, 0.5))
            x0, _, x1, _ = l.reg("front"); l.d.rectangle((x0 + 30, l.zrow(0.24), x1 - 30, l.zrow(0.18)), fill=dk(col, 0.6))
        elif kind == "clogs":
            l.band(0, 0.36, col); l.band(0, 0.1, (240, 240, 240))
        elif kind == "heels":
            l.band(0, 0.24, col); l.band(0.24, 0.5, skin or (230, 190, 160), caps=False)
            x0, _, x1, _ = l.reg("back"); l.d.rectangle(((x0 + x1) / 2 - 10, l.zrow(0.24), (x0 + x1) / 2 + 10, l.zrow(0)), fill=dk(col, 0.6))


def finish(S, rng):
    for k, t in S.items():
        if k == "Torso" or k in ARMS:
            edge_shade(t, 0.2)
        noise(t, 3, rng)


# ---------------------------------------------------------------- body from texture set
def build_body(name, skin_rgb, S):
    paths = {k: t.save(f"{name}_{k}") for k, t in S.items()}
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


# ---------------------------------------------------------------- 3D accessories
def a_beret(P, col):
    ball("Beret", (1.4, 1.35, 0.4), V((0.12, -0.05, 1.32)), P["M"]("Beret", col, rough=0.85), P["neck"],
         rot=(0, math.radians(-12), 0))
    ball("BeretStem", (0.1, 0.1, 0.12), V((0.16, -0.05, 1.53)), P["M"]("BeretStem", dk(col, 0.7)), P["neck"])


def a_toque(P):
    w = mat("ChefWhite", (248, 248, 248), rough=0.8)
    solid("ToqueBand", CYL, (1.3, 1.3, 0.45), V((0, 0, 1.28)), w, parent=P["neck"], col=COL_CHARS)
    for x, y in ((0, 0), (0.28, 0.1), (-0.28, 0.1), (0.15, -0.25), (-0.15, -0.25)):
        ball("ToquePuff", (0.8, 0.8, 0.75), V((x, y, 1.75)), w, P["neck"])


def a_flatcap(P, col):
    m = P["M"]("FlatCap", col, rough=0.8)
    ball("FlatCap", (1.36, 1.4, 0.55), V((0, 0.02, 1.2)), m, P["neck"])
    rpart("FlatBrim", (1.0, 0.45, 0.07), V((0, 0.72, 1.12)), m, P["neck"], r=0.03, rot=(math.radians(10), 0, 0))


def a_tape(P):
    """Tape measure draped over the shoulders, outside the head and torso."""
    m = mat("TapeYellow", (250, 205, 50), rough=0.4)
    cen = lambda p: V((p.x * 0.6, -0.6, p.z - (0.7 if p.z > 3.95 else 0.0)))
    for s in (-1, 1):
        lock(P["root"], [V((s * 0.66, -0.47, 4.035)), V((s * 0.74, 0.0, 4.045)), V((s * 0.7, 0.5, 4.0)),
                         V((s * 0.66, 0.56, 3.75)), V((s * 0.62, 0.56, 3.1)), V((s * 0.64, 0.56, 2.55))],
             0.16, 0.016, m, n=26, wpow=14, center=cen)


def a_pincushion(P):
    ball("PinCushion", (0.42, 0.42, 0.26), V((0, 0.6, -1.05)), mat("Pin", (214, 52, 70), rough=0.8), P["Left"],
         rot=(math.radians(90), 0, 0))
    solid("PinBand", CYL, (1.03, 1.03, 0.1), V((0, 0, -1.05)), mat("PinBand", (40, 40, 44)), parent=P["Left"], col=COL_CHARS)


def a_glasses(P): glasses(P["neck"], P["M"], (25, 25, 30))


def held2(P, item):
    sh = P["Right"]; sh.rotation_euler = (math.radians(38), 0, 0)
    h = empty("Held", V((0, 0.15, -1.5)), col=COL_CHARS, parent=sh); h.rotation_euler = (math.radians(-38), 0, 0)
    if item == "sketchbook":
        rpart("Sketch", (0.85, 0.12, 1.05), V((0, 0.5, 0.2)), mat("SketchCover", (30, 30, 34)), h, r=0.03)
        rpart("SketchPages", (0.78, 0.13, 0.98), V((0, 0.52, 0.2)), mat("Paper", (245, 240, 228)), h, r=0.02)
    elif item == "scissors":
        for s in (-1, 1):
            rpart("Blade", (0.06, 0.04, 0.6), V((s * 0.05, 0.5, 0.45)), M_METAL, h, r=0.01, rot=(0, math.radians(s * 8), 0))
            disc("Handle", 0.2, 0.05, V((s * 0.09, 0.5, 0.05)), mat("ScissorHandle", (40, 40, 44)), h)
    elif item == "hanger":
        tube("Hanger", [(-0.45, 0.5, 0.3), (0, 0.5, 0.55), (0.45, 0.5, 0.3), (-0.45, 0.5, 0.3)], 0.025, M_METAL, h)
        tube("Hook", [(0, 0.5, 0.55), (0, 0.5, 0.75), (0.1, 0.5, 0.82)], 0.025, M_METAL, h)
    elif item == "rollingpin":
        rpart("Pin", (1.3, 0.22, 0.22), V((0, 0.5, 0.1)), M_WOOD, h, r=0.1)
    elif item == "croissant":
        cm = mat("Pastry", (214, 150, 70), rough=0.6)
        for k, (x, s) in enumerate(((-0.22, 0.2), (-0.1, 0.27), (0.05, 0.3), (0.18, 0.25), (0.28, 0.18))):
            ball("Croissant", (s, s, s * 0.9), V((x, 0.5, 0.1 + abs(x) * 0.35)), cm, h)
    elif item == "baguette":
        rpart("Baguette", (0.24, 0.24, 1.6), V((0, 0.5, 0.55)), mat("Bread", (210, 150, 80), rough=0.7), h, r=0.11,
              rot=(0, math.radians(20), 0))
    elif item == "cakebox":
        rpart("CakeBox", (0.9, 0.9, 0.6), V((0, 0.6, 0.25)), mat("Box", (250, 200, 215), rough=0.7), h, r=0.03)
        rpart("Ribbon", (0.93, 0.93, 0.08), V((0, 0.6, 0.25)), mat("Ribbon", (214, 52, 90)), h, r=0.01)
    elif item == "whisk":
        rpart("WhiskHandle", (0.1, 0.1, 0.4), V((0, 0.5, 0.05)), mat("WhiskH", (40, 40, 44)), h, r=0.04)
        for a in range(0, 180, 45):
            tube("Wire", [(0, 0.5, 0.25), (0.12 * math.cos(math.radians(a)), 0.5 + 0.12 * math.sin(math.radians(a)), 0.55),
                          (0, 0.5, 0.75)], 0.012, M_METAL, h)
    elif item == "coffee":
        held(P, P["M"], "cup")


def grunge_extras(P):
    root = P["root"]; M = P["M"]
    rpart("Bag", (0.62, 0.3, 0.55), V((-0.8, 0.64, 2.18)), M("Bag", (28, 28, 30), rough=0.5), root, r=0.08)
    rpart("BagTab", (0.14, 0.06, 0.26), V((-0.88, 0.56, 2.5)), M("BagTab", (40, 40, 44)), root, r=0.02)
    rpart("Buckle", (0.24, 0.04, 0.16), V((0.2, 0.535, 3.53)), mat("Silver", (200, 200, 208), rough=0.25, metallic=1.0),
          root, r=0.015, rot=(0, math.radians(45), 0))
    silver = mat("Silver2", (200, 200, 208), rough=0.25, metallic=1.0)
    tube("Chain", [(-0.42, 0.42, 4.02), (-0.2, 0.53, 3.78), (0, 0.55, 3.66), (0.2, 0.53, 3.78), (0.42, 0.42, 4.02)],
         0.02, silver, root)
    rpart("CrossV", (0.07, 0.04, 0.34), V((0, 0.56, 3.45)), silver, root, r=0.01)
    rpart("CrossH", (0.22, 0.04, 0.07), V((0, 0.56, 3.52)), silver, root, r=0.01)


# ---------------------------------------------------------------- strap fix for O2
def draw_strap(t, width=30, col=(28, 28, 30)):
    x0, y0, x1, y1 = t.reg("front")
    fa, fb = (t.fx("front", 0.18), y0), (t.fx("front", 1.0), y1 - 56)
    ba, bb = (t.fx("back", 0.82), t.top), (t.fx("back", 0.0), t.mid - 56)
    lx0, _, lx1, _ = t.reg("L")
    side = [(lx0, y1 - 56), (lx1, t.mid - 56)]
    tx = t.fx("top", 0.18)
    segs = [(fa, fb), (ba, bb), (side[0], side[1]), ((tx, 0), (tx, t.top))]
    sh = Image.new("L", (t.W, t.H), 0); d = ImageDraw.Draw(sh)
    for a, b in segs:
        d.line((a[0] + 5, a[1] + 7, b[0] + 5, b[1] + 7), fill=170, width=width + 8)
    m = np.asarray(sh.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
    t.set(t.arr() * (1 - 0.55 * m))
    for a, b in segs:
        t.d.line((a, b), fill=col, width=width)
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        for o in (-width * 0.35, width * 0.35):
            stitch(t, a[0] + nx * o, a[1] + ny * o, b[0] + nx * o, b[1] + ny * o, (95, 95, 100), dash=8)
        t.d.line((a[0] + nx * width / 2, a[1] + ny * width / 2, b[0] + nx * width / 2, b[1] + ny * width / 2), fill=(70, 70, 74), width=2)


_orig_grunge = OUTFITS["O2"]


def outfit_grunge_fixed(skin, rng):
    out = _orig_grunge(skin, rng)
    draw_strap(out["Torso"])
    return out


OUTFITS["O2"] = outfit_grunge_fixed


# ---------------------------------------------------------------- themes
SKIN_POOL = [(255, 224, 196), (242, 200, 165), (234, 184, 146), (214, 158, 118), (176, 122, 88), (124, 86, 62),
             (92, 62, 46)]
HAIR_COLS = [(24, 20, 20), (60, 40, 30), (110, 74, 44), (200, 150, 80), (226, 196, 140), (150, 60, 40),
             (236, 236, 240), (40, 40, 46)]


HAIR_CHANGED = []
HAIR_RULE_EXEMPT = set()   # character names Joel approved with light hair on darker skin (e.g. "Bake3" = B4 blonde)
DARK_HAIR = [(24, 20, 20), (40, 30, 24), (60, 40, 30), (30, 26, 28)]


def _lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def fix_hair_col(skin, col, who="", elderly=False):
    """Studio rule: darker skin tones never get blonde/very light hair (greys allowed for elderly only)."""
    if who in HAIR_RULE_EXEMPT:
        return col
    grey = max(col) - min(col) < 20
    if _lum(skin) < 150 and _lum(col) > 120 and not (elderly and grey):
        new = DARK_HAIR[sum(skin) % len(DARK_HAIR)]
        HAIR_CHANGED.append(who)
        return new
    return col


def look_fashion(i, rng, prng):
    skin = prng.choice(SKIN_POOL)
    S = new_set()
    neutrals = [(20, 20, 24), (238, 232, 218), (196, 160, 110), (90, 90, 96), (245, 245, 245), (60, 50, 44)]
    accents = [(214, 120, 150), (60, 100, 70), (180, 40, 50), (70, 90, 160), (230, 170, 60)]
    top = prng.choice(["turtle", "blazer", "stripe_shirt", "sweater", "graphic", "blazer"])
    desc = []
    if top == "turtle":
        c = prng.choice(neutrals[:4]); d_turtleneck(S, c, rng, skin); desc.append("turtleneck")
    elif top == "blazer":
        c = prng.choice(neutrals + accents)
        inner = prng.choice([(245, 245, 245), (20, 20, 24), (238, 232, 218)])
        d_blazer(S, c, rng, skin, inner=inner, inner_kind=prng.choice(["tee", "turtle"])); desc.append("blazer")
    elif top == "stripe_shirt":
        c = prng.choice([(245, 245, 245), (220, 232, 245)])
        d_button_shirt(S, c, rng, skin, pattern=lambda t: pat_pinstripe(t, (70, 100, 180), step=16)); desc.append("striped shirt")
    elif top == "sweater":
        c = prng.choice(neutrals + accents); d_sweater(S, c, rng, skin, stripe=prng.choice([None, dk(c, 0.6), (245, 245, 245)]))
        desc.append("knit sweater")
    else:
        c = prng.choice([(245, 245, 245), (20, 20, 24)])
        d_tee(S, c, rng, skin, text=prng.choice(["ATELIER", "DRAFT 01", "FW/27", "SAMPLE"]),
              text_col=(20, 20, 24) if sum(c) > 300 else (245, 245, 245)); desc.append("graphic tee")
    bot = prng.choice(["tailored", "pinstripe", "skirt", "chinos", "plaid", "jeans"])
    bc = prng.choice(neutrals)
    b_trousers(S, bc if bot != "jeans" else (120, 150, 190), rng, kind=bot, skin=skin,
               accent=(200, 200, 205) if bot == "pinstripe" else None)
    desc.append({"tailored": "tailored trousers", "pinstripe": "pinstripe trousers", "skirt": "pleated skirt",
                 "chinos": "chinos", "plaid": "plaid trousers", "jeans": "light jeans"}[bot])
    sh = prng.choice(["loafers", "boots", "trainers", "heels"] if bot == "skirt" else ["loafers", "boots", "trainers"])
    s_shoes(S, sh, prng.choice([(20, 20, 24), (90, 60, 40), (245, 245, 245)]), rng, skin); desc.append(sh)
    finish(S, rng)
    P = build_body(f"Fash{i}", skin, S)
    extras = []
    if prng.random() < 0.6: a_tape(P); extras.append("tape measure")
    if prng.random() < 0.35: a_glasses(P); extras.append("glasses")
    if prng.random() < 0.3: a_pincushion(P); extras.append("pin cushion")
    item = prng.choice(["sketchbook", "scissors", "hanger", "none", "coffee"])
    if item != "none": held2(P, item); extras.append(item)
    hk = prng.choice(list(HAIR3))
    hat = prng.random() < 0.3 and hk in ("H2", "H5", "H6", "H7")
    hcol = fix_hair_col(skin, prng.choice(HAIR_COLS), f"Fash{i}")
    if hat: hat_hair(P, hcol, random.Random(i))
    else: add_hair_any(P, hk, random.Random(i), colour=hcol)
    if hat: a_beret(P, prng.choice(accents + [(20, 20, 24)])); extras.append("beret")
    return P, desc + extras


def look_bakery(i, role, rng, prng):
    skin = prng.choice(SKIN_POOL)
    S = new_set()
    pastel = [(250, 200, 215), (190, 230, 210), (250, 225, 170), (200, 215, 245)]
    browns = [(120, 80, 50), (160, 110, 70), (90, 60, 40)]
    desc = [role]
    apron = None
    if role in ("head baker", "pastry chef"):
        d_chef_jacket(S, (246, 246, 246), rng, skin, piping=(30, 30, 34) if role == "head baker" else (214, 90, 130))
        b_trousers(S, (245, 245, 245), rng, kind="check", accent=(30, 30, 34))
        s_shoes(S, "clogs", (30, 30, 34), rng)
        if prng.random() < 0.6 or role == "pastry chef":
            apron = (prng.choice(pastel) if role == "pastry chef" else (245, 245, 245), True, None)
            o_apron(S, apron[0], rng, flour=True, bib=False)
    elif role == "cashier":
        c = prng.choice(pastel)
        d_polo(S, c, rng, skin, logo="CRUMB & CO.", logo_col=(90, 60, 40))
        b_trousers(S, (40, 40, 46), rng, kind="chinos")
        s_shoes(S, "trainers", (245, 245, 245), rng)
        apron = (prng.choice(browns), False, None)
        o_apron(S, apron[0], rng, text="CRUMB & CO.")
    elif role == "baker":
        d_tee(S, prng.choice([(245, 245, 245), (40, 40, 46), (250, 225, 170)]), rng, skin)
        b_trousers(S, (52, 74, 124), rng, kind="jeans")
        s_shoes(S, "boots", (90, 60, 40), rng)
        apron = (prng.choice([(60, 80, 120), (120, 80, 50), (245, 245, 245)]), True, None)
        o_apron(S, apron[0], rng, flour=True)
    elif role == "delivery":
        d_hoodie(S, prng.choice([(214, 90, 130), (90, 60, 40), (40, 40, 46)]), rng, skin, text="CRUMB & CO.")
        b_trousers(S, (60, 60, 66), rng, kind="cargo")
        s_shoes(S, "trainers", (40, 40, 46), rng)
    else:   # customer
        d_sweater(S, prng.choice(pastel + [(200, 60, 60)]), rng, skin, stripe=(245, 245, 245))
        b_trousers(S, (52, 74, 124), rng, kind="jeans")
        s_shoes(S, "trainers", (245, 245, 245), rng)
    finish(S, rng)
    P = build_body(f"Bake{i}", skin, S)
    hk = prng.choice(["H2", "H5", "H6", "H1", "H7"] if role in ("head baker", "pastry chef") else list(HAIR3))
    if apron:
        a_apron_panel(P, apron[0], rng, flour=apron[1])
    capped = (role == "cashier" and hk in ("H5", "H2", "H6", "H1")) or (role == "baker" and hk in ("H5", "H2", "H6", "H1", "H7"))
    if role in ("head baker", "pastry chef"):
        hk = prng.choice(["H5", "H2"]); hat_hair(P, fix_hair_col(skin, prng.choice(HAIR_COLS), f"Bake{i}"), random.Random(i)); a_toque(P)
        desc.append("chef hat")
    else:
        hcol = fix_hair_col(skin, prng.choice(HAIR_COLS), f"Bake{i}")
        if capped: hat_hair(P, hcol, random.Random(i))
        else: add_hair_any(P, hk, random.Random(i), colour=hcol)
    if role == "cashier" and hk in ("H5", "H2", "H6", "H1"):
        hat_cap(P["neck"], P["M"], (90, 60, 40)); desc.append("cap")
    if role == "baker" and hk in ("H5", "H2", "H6", "H1", "H7"):
        a_flatcap(P, (120, 110, 100)); desc.append("flat cap")
    item = {"head baker": "baguette", "pastry chef": prng.choice(["rollingpin", "whisk"]), "cashier": "croissant",
            "baker": prng.choice(["rollingpin", "baguette"]), "delivery": "cakebox", "customer": "coffee"}[role]
    held2(P, item); desc.append(item)
    return P, desc


def make_theme_looks(seed=42):
    prng = random.Random(seed); out = []
    for i in range(6):
        rng = RNG(seed + i)
        P, d = look_fashion(i, rng, prng)
        face = FACES2["M2"][1][prng.choice([0, 0, 5, 7, 1])]
        add_face(P, "f", face)
        out.append(("fashion", P, d))
    roles = ["head baker", "pastry chef", "cashier", "baker", "delivery", "customer"]
    for i, role in enumerate(roles):
        rng = RNG(seed + 100 + i)
        P, d = look_bakery(i, role, rng, prng)
        face = FACES2["M2"][1][prng.choice([0, 0, 1, 7])]
        add_face(P, "f", face)
        out.append(("bakery", P, d))
    return out


# ---------------------------------------------------------------- fixes v3
def a_apron_panel(P, col, rng, flour=False, text=None):
    """3D apron skirt hanging from the waist across both legs (like a Roblox apron accessory)."""
    t = Tpl((2.1, 0.06, 1.25)); fill_all(t, col)
    x0, y0, x1, y1 = t.reg("front"); edge = dk(col, 0.7)
    t.d.rectangle((x0, y0, x1, y1), outline=edge, width=5)
    stitch(t, x0 + 12, y1 - 12, x1 - 12, y1 - 12, dk(col, 1.3))
    stitch(t, x0 + 12, y0 + 12, x0 + 12, y1 - 12, dk(col, 1.3)); stitch(t, x1 - 12, y0 + 12, x1 - 12, y1 - 12, dk(col, 1.3))
    px = t.fx("front", 0.55)
    t.d.rectangle((px, y0 + 0.25 * PPU, px + 0.6 * PPU, y0 + 0.75 * PPU), outline=edge, width=4)
    if text:
        sz = 26
        while sz > 10 and t.d.textlength(text, font=font(sz)) > 0.8 * PPU: sz -= 1
        t.d.text((t.fx("front", 0.12), y0 + 0.35 * PPU), text, font=font(sz), fill=dk(col, 0.55) if sum(col) > 400 else (245, 245, 245))
    folds(t, rng, ["front"], n=4, strength=0.25, ang=(-10, 10), length=(0.4, 0.8))
    if flour:
        lay = Image.new("L", (t.W, t.H), 0); d = ImageDraw.Draw(lay)
        for _ in range(12):
            x, y, r = rng.uniform(x0, x1), rng.uniform(y0 + (y1 - y0) * 0.3, y1), rng.uniform(3, 10)
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=int(rng.uniform(40, 110)))
        m = np.asarray(lay.filter(ImageFilter.GaussianBlur(5)), np.float32)[..., None] / 255
        t.set(t.arr() * (1 - m) + 248 * m)
    edge_shade(t, 0.15, regions=("front",))
    mt = img_mat(P["root"].name + "_ApronPanel", t.save(P["root"].name + "_ApronPanel"))
    rpart_t("ApronPanel", (2.1, 0.06, 1.25), V((0, 0.56, 1.45)), mt, P["root"])
    rpart("ApronTie", (2.12, 1.04, 0.12), V((0, 0, 2.0)), P["M"]("ApronTie", dk(col, 0.7)), P["root"], r=0.03)


def hat_hair(P, colour, rng):
    """Short hair that sits under a hat brim (no top volume -> no clipping)."""
    m = hair_mat("HatHair" + P["root"].name, colour)
    o = []
    for az in range(40, 321, 16):
        a = az + rng.uniform(-5, 5)
        o.append(lock(P["neck"], flow(a, 28, -18 if 100 < az < 260 else -8, vol=0.06, flick=0.02), 0.32, 0.07, m))
    for x in (-0.42, -0.26, 0.26, 0.42):
        o.append(lock(P["neck"], [face_front(x, 1.06, 0.03), face_front(x * 1.05, 0.98, 0.06), face_front(x * 1.08, 0.9, 0.06)],
                      0.2, 0.06, m))
    P["hair"]["hat"] = o


MEN_MAP = {"H1": "M1", "H5": "M4", "H6": "M3", "H7": "M2"}


def add_hair_any(P, hk, rng, colour=None):
    if hk in MEN_MAP:
        return add_men_hair(P, MEN_MAP[hk], rng, colour)
    return add_hair3(P, hk, rng, colour=colour)
