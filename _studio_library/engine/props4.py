# props4.py - SET DRESSING BATCH 4 (approved by Joel 22 Nov 2026 20:40). Cheap detail for any set.
# Load after props.py / props3.py:   exec(open(LIB + "props4.py").read())
# Render-cost rules: low-poly bevelled boxes, shared materials, no glass/volumes/transparency, glows are emission
# (no extra lights) except ONE warm practical per room. Detail sits where the camera looks (walls behind faces).
import math, random
from mathutils import Vector as _DV

_DM = {}


def dmat(name, rgb, **kw):
    """Cached material: one per look, shared by every dressing piece."""
    if name not in _DM: _DM[name] = pmat("D_" + name, rgb, **kw)
    return _DM[name]


def glow(name, rgb, strength=3.0):
    return dmat(name, rgb, emit=strength, emit_rgb=rgb)


def wall_root(name, loc, n):
    """Root on a wall: loc = point on the wall's inner face at floor height, n = wall normal into the room.
    Children are built with the wall at local y=0, facing -y, heights in local z."""
    r = root_of(name, _DV(loc)); n = _DV(n)
    r.rotation_euler = (0, 0, math.atan2(n.x, -n.y)); return r


# ------------------------------------------------------------------ wall pieces (local: wall at y=0, front at -y)
def art_img(path, kind, rgb=(120, 150, 170), seed=0):
    """Tiny generated pictures so frames never show a flat colour: 'land' (hills + sun), 'sea', 'portrait'
    (Roblox-style head + shoulders on a tinted backdrop), 'family' (two/three figures), 'abstract' (colour blocks)."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seed); W_, H_ = 240, 300; im = Image.new("RGB", (W_, H_), rgb); d = ImageDraw.Draw(im)
    sk = tuple(min(255, c + 60) for c in rgb)
    if kind in ("land", "sea"):
        d.rectangle((0, 0, W_, H_), fill=(150, 195, 235) if kind == "land" else (170, 205, 240))
        d.ellipse((150, 40, 205, 95), fill=(250, 220, 120))
        if kind == "land":
            d.ellipse((-80, 150, 200, 380), fill=(110, 170, 90)); d.ellipse((90, 170, 360, 400), fill=(80, 140, 75))
            for k in range(3): x = rnd.randint(30, 200); d.rectangle((x, 175, x + 6, 200), fill=(90, 60, 40)); d.ellipse((x - 14, 150, x + 20, 185), fill=(60, 120, 60))
        else:
            d.rectangle((0, 170, W_, H_), fill=(60, 120, 180)); d.rectangle((0, 240, W_, H_), fill=(230, 210, 160))
            d.polygon([(70, 165), (100, 110), (100, 165)], fill=(250, 250, 250)); d.line((100, 110, 100, 170), fill=(80, 60, 40), width=3)
    elif kind in ("portrait", "family"):
        d.rectangle((0, 0, W_, H_), fill=sk)
        figs = [(120, 1.0)] if kind == "portrait" else [(75, 0.8), (165, 0.8)] + ([(120, 0.55)] if rnd.random() < 0.7 else [])
        for x, sc in figs:
            skin = rnd.choice([(255, 215, 175), (225, 170, 120), (160, 110, 75), (110, 72, 50)])
            top = rnd.choice([(200, 80, 70), (70, 110, 180), (90, 150, 100), (230, 180, 60), (120, 90, 160)])
            hy = int(200 - 90 * sc)
            d.rectangle((x - int(55 * sc), hy + int(48 * sc), x + int(55 * sc), H_), fill=top)
            d.rounded_rectangle((x - int(32 * sc), hy - int(30 * sc), x + int(32 * sc), hy + int(34 * sc)), 10, fill=skin)
            d.rectangle((x - int(34 * sc), hy - int(36 * sc), x + int(34 * sc), hy - int(16 * sc)), fill=rnd.choice([(40, 30, 25), (90, 60, 35), (20, 20, 22)]))
            for ex in (-12, 12): d.ellipse((x + int(ex * sc) - 3, hy, x + int(ex * sc) + 3, hy + 7), fill=(20, 20, 20))
            d.arc((x - int(12 * sc), hy + 8, x + int(12 * sc), hy + 22), 20, 160, fill=(20, 20, 20), width=2)
    else:
        for k in range(5):
            c = rnd.choice([(220, 90, 70), (240, 200, 80), (70, 120, 190), (240, 240, 230), (40, 40, 50), (90, 170, 140)])
            x0, y0 = rnd.randint(-40, 180), rnd.randint(-40, 240); d.rectangle((x0, y0, x0 + rnd.randint(60, 160), y0 + rnd.randint(60, 160)), fill=c)
    im.save(path); return path


_ART = ["land", "family", "portrait", "sea", "abstract"]


def picture(name, loc, n, z, w=1.6, h=2.0, img=None, rgb=(120, 150, 170), frame=(60, 40, 30), kind=None, seed=None):
    """Framed picture. With no img a small painting/photo is generated (kind: land/sea/portrait/family/abstract)."""
    if img is None:
        sd = seed if seed is not None else sum(map(ord, name))
        img = art_img("/tmp/d_art_%s.png" % name, kind or _ART[sd % len(_ART)], rgb, sd)
    r = wall_root(name, loc, n)
    rb(name + "F", (w, 0.12, h), _DV((0, -0.06, z)), dmat("frame%s" % (frame,), frame, rough=0.6), r, r=0.03)
    if img: plane(name + "P", w - 0.3, h - 0.3, _DV((0, -0.125, z)), imgmat(name + "Img", img, rough=0.8), r, rot=(0, 0, math.pi))
    else: rb(name + "P", (w - 0.3, 0.04, h - 0.3), _DV((0, -0.13, z)), dmat("pic%s" % (rgb,), rgb, rough=0.8), r, r=0.005)
    return r


def switch(name, loc, n, z=4.0):
    r = wall_root(name, loc, n)
    rb(name, (0.45, 0.06, 0.65), _DV((0, -0.03, z)), dmat("switch", (240, 240, 236)), r, r=0.02)
    rb(name + "R", (0.12, 0.05, 0.22), _DV((0, -0.08, z)), dmat("switch", (240, 240, 236)), r, r=0.01)
    return r


def outlet(name, loc, n, z=0.9):
    r = wall_root(name, loc, n)
    rb(name, (0.55, 0.06, 0.45), _DV((0, -0.03, z)), dmat("switch", (240, 240, 236)), r, r=0.02)
    for dx in (-0.12, 0.12): rb(name + "H", (0.05, 0.02, 0.12), _DV((dx, -0.065, z)), dmat("hole", (40, 40, 40)), r, r=0.005)
    return r


def shelf_books(name, loc, n, z, w=4.0, seed=1, toys=True):
    """Wall shelf with a row of books (+ a couple of chunky toys). ~20 boxes."""
    rnd = random.Random(seed); r = wall_root(name, loc, n)
    rb(name + "Board", (w, 0.9, 0.15), _DV((0, -0.45, z)), dmat("shelfwood", (150, 108, 70), rough=0.7), r, r=0.02)
    for dx in (-w / 2 + 0.4, w / 2 - 0.4):
        rb(name + "Brk", (0.12, 0.6, 0.5), _DV((dx, -0.3, z - 0.3)), dmat("bracket", (60, 60, 64), metal=0.6, rough=0.4), r, r=0.01)
    cols = [(170, 50, 50), (50, 90, 160), (230, 190, 60), (60, 140, 90), (240, 240, 230), (120, 70, 150), (40, 40, 50)]
    x = -w / 2 + 0.25; stop = w * (0.55 if toys else 0.95) - w / 2
    while x < stop:
        t = rnd.uniform(0.18, 0.32); hh = rnd.uniform(0.75, 1.15); c = rnd.choice(cols)
        rb(name + "Bk", (t, 0.65, hh), _DV((x + t / 2, -0.45, z + 0.08 + hh / 2)), dmat("book%s" % (c,), c, rough=0.7), r, r=0.02)
        x += t + 0.02
    if toys:
        rb(name + "Cube", (0.6, 0.6, 0.6), _DV((w / 2 - 1.3, -0.45, z + 0.38)), dmat("toyred", (210, 60, 50)), r, r=0.08)
        rcyl(name + "Ball", 0.35, 0.7, _DV((w / 2 - 0.5, -0.45, z + 0.43)), dmat("toyblue", (60, 120, 220)), r, seg=16)
    return r


def coat_hooks(name, loc, n, z=6.2, coats=((90, 110, 80), (60, 70, 110), (150, 60, 50))):
    """Wooden rail with hooks and hanging coats (simple tapered blocks)."""
    r = wall_root(name, loc, n); w = 1.4 * len(coats) + 0.6
    rb(name + "Rail", (w, 0.12, 0.45), _DV((0, -0.06, z)), dmat("shelfwood", (150, 108, 70), rough=0.7), r, r=0.03)
    for i, c in enumerate(coats):
        dx = -w / 2 + 1.0 + i * 1.4
        rb(name + "Hk", (0.1, 0.35, 0.1), _DV((dx, -0.2, z + 0.05)), dmat("bracket", (60, 60, 64), metal=0.6, rough=0.4), r, r=0.02)
        taper(name + "Coat", (1.1, 0.45, 2.6), _DV((dx, -0.32, z - 1.45)), dmat("coat%s" % (c,), c, rough=0.9), r, top=(0.55, 0.8), r=0.12)
    return r


def radiator(name, loc, n, w=4.0):
    r = wall_root(name, loc, n)
    m = dmat("radiator", (236, 236, 232), rough=0.35)
    for i in range(int(w / 0.35)):
        rb(name + "Fin", (0.22, 0.35, 2.2), _DV((-w / 2 + 0.2 + i * 0.35, -0.35, 1.7)), m, r, r=0.06)
    rb(name + "Pipe", (w, 0.2, 0.2), _DV((0, -0.35, 0.55)), m, r, r=0.08)
    return r


def sconce(name, loc, n, z=7.0, light=False, energy=40):
    """Warm wall lamp: glowing shade (emission). light=True adds the ONE real practical for the room."""
    r = wall_root(name, loc, n)
    rb(name + "Plate", (0.4, 0.08, 0.6), _DV((0, -0.04, z)), dmat("brass", (170, 130, 70), metal=0.8, rough=0.35), r, r=0.03)
    rb(name + "Arm", (0.1, 0.5, 0.1), _DV((0, -0.3, z)), dmat("brass", (170, 130, 70), metal=0.8, rough=0.35), r, r=0.03)
    taper(name + "Shade", (0.9, 0.9, 0.8), _DV((0, -0.6, z + 0.25)), glow("shade", (255, 205, 150), 2.2), r, top=(0.6, 0.6), r=0.08)
    if light:
        L = bpy.data.lights.new(name + "L", "POINT"); L.energy = energy; L.shadow_soft_size = 0.4; L.color = (1.0, 0.72, 0.45)
        o = bpy.data.objects.new(name + "L", L); bpy.context.scene.collection.objects.link(o); o.parent = r; o.location = (0, -1.0, z + 0.1)
    return r


def calendar(name, loc, n, z=6.0, crossed=21, path="/tmp/d_calendar.png"):
    """Wall calendar: a month grid with the first `crossed` days crossed off, then they stop (rewatch bait)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (420, 560), (250, 248, 240)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 420, 230), fill=(120, 160, 200)); d.rectangle((40, 40, 380, 190), fill=(150, 190, 120))
    d.ellipse((240, 60, 320, 140), fill=(250, 230, 120))
    d.rectangle((0, 240, 420, 280), fill=(190, 50, 50))
    for i in range(35):
        cx, cy = 10 + (i % 7) * 57, 290 + (i // 7) * 52
        d.rectangle((cx, cy, cx + 54, cy + 48), outline=(170, 170, 170), width=2)
        if i < crossed:
            d.line((cx + 6, cy + 6, cx + 48, cy + 42), fill=(200, 30, 30), width=5); d.line((cx + 48, cy + 6, cx + 6, cy + 42), fill=(200, 30, 30), width=5)
    im.save(path)
    r = wall_root(name, loc, n)
    rb(name + "Pin", (0.1, 0.1, 0.1), _DV((0, -0.05, z + 1.45)), dmat("hole", (40, 40, 40)), r, r=0.03)
    plane(name + "Pg", 2.1, 2.8, _DV((0, -0.04, z)), imgmat(name + "Img", path, rough=0.85), r, rot=(0, 0, math.pi))
    return r


def drawing_img(path, kind="family"):
    """Kid's crayon drawing: three stick figures holding hands (Mum, Milo, Dad) - the Mum figure scribbled out."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (300, 220), (252, 250, 244)); d = ImageDraw.Draw(im)
    d.rectangle((0, 180, 300, 220), fill=(120, 200, 110)); d.ellipse((230, 15, 285, 70), fill=(250, 210, 60))
    for i, (x, c) in enumerate(((70, (200, 60, 120)), (150, (230, 160, 30)), (225, (60, 90, 200)))):
        d.ellipse((x - 18, 70, x + 18, 106), outline=c, width=4); d.line((x, 106, x, 150), fill=c, width=4)
        d.line((x, 150, x - 14, 178), fill=c, width=4); d.line((x, 150, x + 14, 178), fill=c, width=4); d.line((x - 30, 120, x + 30, 120), fill=c, width=4)
    for k in range(9): d.line((48 + k * 4, 64 + (k % 2) * 4, 96 - k * 2, 182 - (k % 3) * 6), fill=(40, 40, 50), width=3)   # Mum scribbled out
    im.save(path); return path


def string_lights(name, a, b, n=14, sag=0.7, rgb=(255, 200, 120), seed=3):
    """Fairy lights between two points: tiny emission bulbs on a sagging wire (no real lights)."""
    a, b = _DV(a), _DV(b); r = root_of(name, (0, 0, 0)); rnd = random.Random(seed)
    for i in range(n):
        t = (i + 0.5) / n; p = a.lerp(b, t) - _DV((0, 0, sag * 4 * t * (1 - t)))
        rcyl(name + "B", 0.09, 0.18, p, glow("fairy", rgb, 6.0), r, seg=8)
    return r


def ceiling_stars(name, x0, x1, y0, y1, z, n=26, seed=5):
    """Glow-in-the-dark stickers on the ceiling: faint green-white emission, reads in the 3AM shots."""
    rnd = random.Random(seed); r = root_of(name, (0, 0, 0))
    for i in range(n):
        p = _DV((rnd.uniform(x0, x1), rnd.uniform(y0, y1), z - 0.02)); s_ = rnd.uniform(0.12, 0.25)
        rb(name + "S", (s_, s_, 0.02), p, glow("star", (190, 255, 200), 1.4), r, r=0.0, rot=(0, 0, rnd.uniform(0, 1.5)))
    return r


def floor_clutter(name, loc, seed=2):
    """Backpack + a dropped hoodie + two books: breaks up an empty floor."""
    rnd = random.Random(seed); r = root_of(name, _DV(loc)); r.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    rb(name + "Bag", (1.3, 0.8, 1.6), _DV((0, 0, 0.8)), dmat("bag", (40, 90, 150), rough=0.85), r, r=0.25)
    rb(name + "Pocket", (0.9, 0.2, 0.7), _DV((0, -0.45, 0.55)), dmat("bag2", (30, 60, 110), rough=0.85), r, r=0.12)
    hm = dmat("hood", (120, 120, 130), rough=0.95)                       # dropped hoodie: body, both sleeves, hood
    rb(name + "Hood", (1.7, 1.3, 0.22), _DV((1.9, 0.4, 0.12)), hm, r, r=0.1, rot=(0, 0, 0.5))
    rb(name + "SlvL", (0.5, 1.5, 0.2), _DV((1.0, 1.3, 0.11)), hm, r, r=0.1, rot=(0, 0, 1.2))
    rb(name + "SlvR", (0.5, 1.4, 0.2), _DV((2.9, -0.3, 0.11)), hm, r, r=0.1, rot=(0, 0, -0.3))
    rb(name + "HoodUp", (0.9, 0.7, 0.35), _DV((2.4, 1.15, 0.2)), hm, r, r=0.16, rot=(0, 0, 0.5))
    rb(name + "Pkt", (0.7, 0.4, 0.05), _DV((1.75, 0.1, 0.25)), dmat("hood2", (100, 100, 110), rough=0.95), r, r=0.04, rot=(0, 0, 0.5))
    for k in range(2):
        rb(name + "Bk", (0.9, 0.7, 0.15), _DV((-1.4, 0.6 + k * 0.1, 0.08 + k * 0.15)), dmat("book%s" % k, ((170, 50, 50), (230, 190, 60))[k], rough=0.7), r, r=0.02, rot=(0, 0, k * 0.4))
    return r


# ------------------------------------------------------------------ room-level passes
def wainscot(name, x0, x1, y0, y1, walls, h=3.4, rgb=(150, 120, 95), rail=(240, 238, 230), top=None, z0=0.0):
    """Two-tone wall: darker lower panel + dado rail (+ crown moulding at `top`). walls: subset of 'BLR' for a room
    whose interior is x0..x1, y0..y1 with the back wall at y1 (B), front wall at y0 (F), left at x0 (L), right at x1 (R).
    z0 = floor height (sets built in the air sit at z=400). Biggest look
    gain for ~6 boxes."""
    pm = dmat("wain%s" % (rgb,), rgb, rough=0.7); rm = dmat("rail%s" % (rail,), rail, rough=0.5)
    for wl in walls:
        if wl == "B": c, sz = _DV(((x0 + x1) / 2, y1 - 0.06, z0)), _DV((x1 - x0 - 0.1, 0.12, 0))
        elif wl == "F": c, sz = _DV(((x0 + x1) / 2, y0 + 0.06, z0)), _DV((x1 - x0 - 0.1, 0.12, 0))
        elif wl == "L": c, sz = _DV((x0 + 0.06, (y0 + y1) / 2, z0)), _DV((0.12, y1 - y0 - 0.1, 0))
        else: c, sz = _DV((x1 - 0.06, (y0 + y1) / 2, z0)), _DV((0.12, y1 - y0 - 0.1, 0))
        thick = lambda k: _DV((sz.x if sz.x > 1 else sz.x * k, sz.y if sz.y > 1 else sz.y * k, 0))
        p = thick(1); rb(name + wl + "Pan", (p.x, p.y, h), c + _DV((0, 0, h / 2)), pm, None, r=0.0)
        q = thick(2.2); rb(name + wl + "Rail", (q.x, q.y, 0.25), c + _DV((0, 0, h + 0.12)), rm, None, r=0.04)
        q = thick(2.0); rb(name + wl + "Skirt", (q.x, q.y, 0.45), c + _DV((0, 0, 0.22)), rm, None, r=0.03)
        if top: q = thick(3.0); rb(name + wl + "Crown", (q.x, q.y, 0.4), c + _DV((0, 0, top - 0.2)), rm, None, r=0.08)


def dress_kitchen(KO):
    KO = _DV(KO)
    wainscot("KWain", KO.x - 12.8, KO.x + 12.8, KO.y - 8.8, KO.y + 8.8, "LRF", h=3.2, rgb=(176, 196, 186), top=11, z0=KO.z)
    calendar("KCal", KO + _DV((-3.4, -8.8, 0)), (0, 1, 0), z=6.4, crossed=21)          # behind Milo: "three weeks ago"
    picture("KFPhoto1", KO + _DV((-9.4, -8.8, 0)), (0, 1, 0), 6.8, w=2.0, h=2.4, rgb=(196, 168, 140))
    picture("KFPhoto2", KO + _DV((-7.0, -8.8, 0)), (0, 1, 0), 7.4, w=1.4, h=1.4, rgb=(150, 180, 200))
    picture("KFPhoto3", KO + _DV((-7.0, -8.8, 0)), (0, 1, 0), 5.6, w=1.4, h=1.2, rgb=(180, 140, 160))
    switch("KFSw", KO + _DV((-0.8, -8.8, 0)), (0, 1, 0))
    # utensil rail above the hob + spice shelf by the window
    rail = wall_root("KRail", KO + _DV((3.0, 8.8, 0)), (0, -1, 0))
    rb("KRailBar", (3.2, 0.12, 0.12), _DV((0, -0.25, 7.6)), dmat("steel", (190, 192, 196), metal=0.9, rough=0.3), rail, r=0.05)
    for i, dx in enumerate((-1.1, -0.35, 0.4, 1.15)):
        rb("KUtH", (0.08, 0.08, 0.9), _DV((dx, -0.28, 7.05)), dmat("steel", (190, 192, 196), metal=0.9, rough=0.3), rail, r=0.03)
        rb("KUt", (0.4 if i % 2 else 0.3, 0.08, 0.5), _DV((dx, -0.28, 6.4)), dmat("ut%d" % (i % 2), ((40, 40, 44), (190, 192, 196))[i % 2], metal=0.3 * (i % 2), rough=0.5), rail, r=0.04)
    sp = wall_root("KSpice", KO + _DV((-4.4, 8.8, 0)), (0, -1, 0))
    rb("KSpB", (2.6, 0.6, 0.12), _DV((0, -0.3, 7.2)), dmat("shelfwood", (150, 108, 70), rough=0.7), sp, r=0.02)
    for i in range(6):
        c = ((200, 80, 40), (230, 200, 90), (110, 150, 70), (150, 60, 50), (220, 220, 210), (90, 60, 40))[i]
        rcyl("KJar", 0.17, 0.5, _DV((-1.05 + i * 0.42, -0.3, 7.52)), dmat("jar%d" % i, c, rough=0.5), sp, seg=12)
    picture("KDraw", KO + _DV((9.6, 7.4, 0)), (0, -1, 0), 5.6, w=1.5, h=1.2, img=drawing_img("/tmp/d_draw.png"), frame=(250, 250, 250))  # on the fridge door
    for i, c in enumerate(((220, 60, 60), (60, 160, 220), (240, 200, 60))):
        rb("KMag", (0.25, 0.08, 0.25), KO + _DV((8.6 + i * 0.6, 7.1, 7.0 - i * 0.3)), dmat("mag%s" % (c,), c), None, r=0.06)
    shelf_books("KShelf", KO + _DV((-12.8, 4.0, 0)), (1, 0, 0), 7.6, w=3.6, seed=4, toys=False)
    picture("KPhoto1", KO + _DV((12.8, 0.0, 0)), (-1, 0, 0), 6.6, w=1.8, h=2.2, rgb=(200, 170, 140))
    picture("KPhoto2", KO + _DV((12.8, -3.2, 0)), (-1, 0, 0), 6.0, w=1.4, h=1.4, rgb=(140, 180, 200))
    switch("KSw", KO + _DV((12.8, 3.5, 0)), (-1, 0, 0)); outlet("KOut", KO + _DV((-12.8, -5.0, 0)), (1, 0, 0))
    radiator("KRad", KO + _DV((12.8, -6.0, 0)), (-1, 0, 0), w=3.6)
    # worktop life: fruit bowl, kettle, mug, tea towel
    bowl = KO + _DV((1.6, 7.0, 4.1))
    rcyl("KBowl", 0.9, 0.4, bowl + _DV((0, 0, 0.2)), dmat("bowl", (240, 240, 235)), None, seg=20, top_scale=1.3)
    for k, (dx, dy, c) in enumerate(((-0.3, 0, (220, 60, 40)), (0.3, 0.1, (240, 190, 40)), (0, -0.3, (120, 190, 60)))):
        rcyl("KFruit", 0.3, 0.55, bowl + _DV((dx, dy, 0.6)), dmat("fruit%s" % (c,), c, rough=0.4), None, seg=12)
    rcyl("KKettle", 0.55, 1.3, KO + _DV((4.6, 7.2, 4.75)), dmat("kettle", (210, 70, 60), rough=0.3), None, seg=18, top_scale=0.8)
    rb("KTowel", (0.9, 0.06, 1.3), KO + _DV((0.4, 5.0, 3.1)), fabric("TowelFab", (210, 90, 80)), None, r=0.02)


def dress_hallway(HO):
    """Hallway at night: wainscot + crown, coats, framed family photos, sconces (one real light), radiator, outlet."""
    HO = _DV(HO)
    wainscot("HWain", HO.x - 4.8, HO.x + 4.8, HO.y - 13, HO.y + 12.8, "LRB", h=3.4, rgb=(110, 84, 64), top=11, z0=HO.z)
    coat_hooks("HCoats", HO + _DV((4.8, -6.5, 0)), (-1, 0, 0), z=6.4)
    for i, (dy, z, c, sz) in enumerate(((7.5, 6.6, (190, 160, 130), (1.8, 2.2)), (9.8, 5.8, (150, 170, 190), (1.4, 1.4)), (5.4, 5.6, (170, 150, 120), (1.2, 1.6)))):
        picture("HPhoto%d" % i, HO + _DV((-4.8, dy, 0)), (1, 0, 0), z, w=sz[0], h=sz[1], rgb=c)
    picture("HPhotoR", HO + _DV((4.8, 4.0, 0)), (-1, 0, 0), 6.4, w=2.2, h=1.6, rgb=(120, 140, 110))
    sconce("HSconceL", HO + _DV((-4.8, -4.5, 0)), (1, 0, 0), z=7.2, light=True, energy=35)
    sconce("HSconceR", HO + _DV((4.8, 8.6, 0)), (-1, 0, 0), z=7.2)
    radiator("HRad", HO + _DV((4.8, 0.5, 0)), (-1, 0, 0), w=3.2)
    switch("HSw", HO + _DV((-2.7, 12.8, 0)), (0, -1, 0)); outlet("HOut", HO + _DV((-4.8, -9.5, 0)), (1, 0, 0))


def dress_bedroom():
    """Milo's room (interior x -11..11, y -49..-31, floor 0.4, ceiling 14). Kept clear of the closet (x 4..10 at the back),
    the bed (back left), the door and the two front windows."""
    wainscot("BWain", -11, 11, -49, -31, "RB", h=3.4, rgb=(80, 100, 140), top=None, z0=0.4)
    shelf_books("BShelf", (11, -40.5, 0.4), (-1, 0, 0), 6.6, w=4.4, seed=7)
    picture("BPoster1", (11, -45.5, 0.4), (-1, 0, 0), 7.2, w=2.6, h=3.4, rgb=(40, 60, 120), frame=(30, 30, 30))
    picture("BPoster2", (-1.0, -49, 0.4), (0, 1, 0), 7.6, w=2.4, h=3.2, rgb=(170, 60, 50), frame=(30, 30, 30))
    string_lights("BFairy", (-10.5, -48.8, 10.5), (-3.2, -48.8, 10.5), n=14, sag=0.9)
    ceiling_stars("BStars", -10, 10, -48, -32, 14.0)
    floor_clutter("BClutter", (8.4, -36.0, 0.4), seed=2)
    switch("BSw", (3.4, -31, 0.4), (0, -1, 0)); outlet("BOut", (11, -34.0, 0.4), (-1, 0, 0))
