# props7.py - HEIGHT MOG batch (NOT yet approved by Joel): mayor's trenchcoat + extra shoes, mustache, white gloves,
# town plaza + stage (podium, gooseneck mic, flags, "must be this tall" banner, bunting), backstage curtain, town bus,
# dog (pivots for sniff/sneeze), banquet table, fountain pen.
# Load after props.py + props4.py (pmat/rb/taper/rcyl/plane/imgmat/dmat/save_img/pfont). Blender coords (front = +Y).
# Render cost: bevelled boxes, shared materials, emission only, no glass/volumes.
import math, random
from mathutils import Vector as _V7
from PIL import Image, ImageDraw

D7 = math.radians


def m7(name, rgb, **kw): return dmat("hm_" + name, rgb, **kw)


# ================================================================== MAYOR: coat over three stacked short guys
COAT_KHAKI = (196, 160, 104)


def hm_coat(stack, top, col=COAT_KHAKI, hem=1.0, shoulder=7.35, w_top=3.25, w_hem=4.7, d_top=1.55, d_hem=2.05, belt=4.7):
    """Long trench over the stack (stack = empty at floor centre, front +Y). Body: tapered skirt + upper; raised collar,
    lapels, double-breasted buttons, belt + gold buckle + tie ends, pocket flaps, epaulettes, hem band, back vent.
    Sleeves + white gloves ride on the TOP guy's shoulder pivots (so his arms gesture inside the coat).
    Returns dict(root, parts, front(z) -> front-surface y, buttons)."""
    root = root_of("Coat", (0, 0, 0)); root.parent = stack
    cm = m7("coat", col, rough=0.75); cd = m7("coat_dk", dk(col, 0.72), rough=0.8)
    btn = m7("coat_btn", (70, 48, 30), rough=0.4); gold = m7("gold", (214, 172, 70), rough=0.3, metal=0.9)
    ink = m7("coat_seam", dk(col, 0.5), rough=0.9)
    skirt_h = belt - hem
    w_b = w_top - 0.05; d_b = d_top
    sk = taper("CoatSkirt", (w_hem, d_hem, skirt_h), _V7((0, 0, hem + skirt_h / 2)), cm, root,
               top=(w_b / w_hem, d_b / d_hem), r=0.22)
    up = rb("CoatUpper", (w_top, d_top, shoulder - belt), _V7((0, 0, (belt + shoulder) / 2)), cm, root, r=0.3)

    def front(z):  # front surface y of the coat at height z
        if z >= belt: return d_top / 2
        u = (z - hem) / skirt_h
        return (d_hem + (d_b - d_hem) * u) / 2

    def half_w(z):
        if z >= belt: return w_top / 2
        u = (z - hem) / skirt_h
        return (w_hem + (w_b - w_hem) * u) / 2

    rb("CoatHem", (w_hem + 0.06, d_hem + 0.06, 0.22), _V7((0, 0, hem + 0.11)), cd, root, r=0.08)
    # front overlap seam (left panel over right) down the skirt + upper
    for z0, z1 in ((hem + 0.25, belt - 0.2), (belt + 0.2, shoulder - 1.1)):
        zc = (z0 + z1) / 2; tilt = math.atan2(front(z0) - front(z1), z1 - z0)
        rb("CoatSeam", (0.05, 0.04, z1 - z0), _V7((0.32, front(zc) + 0.015, zc)), ink, root, r=0.01, rot=(-tilt, 0, 0))
    # back vent
    rb("CoatVent", (0.05, 0.04, 1.4), _V7((0, -front(hem + 0.8) - 0.015, hem + 0.8)), ink, root, r=0.01)
    # belt + buckle + tie ends
    rb("CoatBelt", (w_top + 0.12, d_top + 0.14, 0.34), _V7((0, 0, belt)), cd, root, r=0.1)
    rb("Buckle", (0.58, 0.08, 0.46), _V7((0.1, d_top / 2 + 0.09, belt)), gold, root, r=0.06)
    rb("BuckleIn", (0.34, 0.06, 0.24), _V7((0.1, d_top / 2 + 0.12, belt)), cd, root, r=0.03)
    for k, (dx, ang) in enumerate(((0.55, 8), (0.8, -6))):
        rb("BeltEnd", (0.26, 0.08, 1.0), _V7((dx, d_top / 2 + 0.12, belt - 0.55)), cd, root, r=0.05, rot=(0, D7(ang), 0))
    # double-breasted buttons: 2 columns x 3 rows (the middle-left one is the "peek" button in the scene)
    buttons = []
    for z in (belt + 0.75, belt + 1.55, belt - 0.8, belt - 1.7):
        for x in (-0.5, 0.62):
            y = front(z)
            b = rcyl("CoatBtn", 0.14, 0.08, _V7((x, y + 0.04, z)), btn, root, axis="Y", bevel=0.03, seg=16)
            buttons.append(b)
    # lapels (wide, tapering to the collar) + raised collar round the top guy's neck
    for s in (-1, 1):
        taper("Lapel", (0.75, 0.12, 1.5), _V7((s * 0.55, d_top / 2 + 0.05, shoulder - 0.85)), cm, root,
              top=(0.75, 1.0), shift=0.0, r=0.04, rot=(0, s * D7(-14), 0))
        rb("LapelEdge", (0.05, 0.05, 1.4), _V7((s * 0.86, d_top / 2 + 0.1, shoulder - 0.85)), ink, root, r=0.01,
           rot=(0, s * D7(-14), 0))
        rb("Collar", (0.62, 0.22, 0.82), _V7((s * 0.68, 0.22, shoulder + 0.3)), cm, root, r=0.08, rot=(D7(-6), 0, s * D7(-18)))
        # epaulette with a button
        rb("Epaulette", (0.95, 0.42, 0.1), _V7((s * (w_top / 2 - 0.55), 0, shoulder + 0.02)), cd, root, r=0.05)
        rcyl("EpBtn", 0.08, 0.06, _V7((s * (w_top / 2 - 0.2), 0, shoulder + 0.09)), btn, root, bevel=0.02, seg=12)
        # pocket flaps on the skirt
        zp = belt - 1.15; yp = front(zp)
        rb("PocketFlap", (0.8, 0.09, 0.3), _V7((s * (half_w(zp) - 0.6), yp + 0.04, zp)), cd, root, r=0.04,
           rot=(D7(-6), 0, 0))
    rb("CollarBack", (1.25, 0.24, 0.85), _V7((0, -0.28, shoulder + 0.33)), cm, root, r=0.08, rot=(D7(8), 0, 0))
    # sleeves + gloves on the top guy's shoulder pivots (local units are scaled by his body scale)
    for side in ("Left", "Right"):
        sh = top[side]
        rb("Sleeve" + side, (1.22, 1.22, 1.85), _V7((0, 0, -0.62)), cm, sh, r=0.15)
        rb("Cuff" + side, (1.28, 1.28, 0.28), _V7((0, 0, -1.45)), cd, sh, r=0.08)
        rb("Glove" + side, (0.95, 0.95, 0.62), _V7((0, 0, -1.86)), m7("glove", (245, 245, 240), rough=0.6), sh, r=0.2)
        for k in range(3):
            rb("GloveSeam", (0.04, 0.97, 0.3), _V7((-0.25 + k * 0.25, 0, -1.86)), m7("glove_seam", (200, 200, 195)), sh, r=0.01)
    return dict(root=root, front=front, half_w=half_w, buttons=buttons)


def hm_shoe(name, loc, yaw, parent, col=(40, 30, 26), sole=(235, 232, 225), stub=(40, 40, 46), stub_h=1.0):
    """One shoe + a trouser stub rising into the coat (the extra feet under the hem). yaw 180 = facing backwards."""
    r = root_of(name, loc); r.parent = parent; r.rotation_euler = (0, 0, D7(yaw))
    rb(name + "Stub", (0.66, 0.66, stub_h), _V7((0, 0, 0.3 + stub_h / 2)), m7("stub%d" % hash(stub), stub, rough=0.85), r, r=0.08)
    rb(name + "Sole", (0.74, 1.08, 0.14), _V7((0, 0.16, 0.07)), m7("sole%d" % hash(sole), sole, rough=0.7), r, r=0.05)
    rb(name + "Upper", (0.7, 1.0, 0.34), _V7((0, 0.14, 0.3)), m7("shoe%d" % hash(col), col, rough=0.45), r, r=0.14)
    for k in range(2):
        rb(name + "Lace", (0.4, 0.05, 0.05), _V7((0, 0.46 - k * 0.14, 0.46)), m7("lace", (245, 245, 245)), r, r=0.02)
    return r


def hm_mustache(P, col=(150, 60, 40)):
    """Big curled handlebar mustache on the head (sits above the mouth so lip-sync stays visible)."""
    head = P.get("head") or P["neck"]
    fy = surf_y(0) + 0.03; m = P["M"]("Stache", col, rough=0.8)
    rb("StacheMid", (0.3, 0.1, 0.1), _V7((0, fy + 0.02, 0.505)), m, head, r=0.045)
    for s in (-1, 1):
        rb("StacheWing", (0.3, 0.1, 0.09), _V7((s * 0.27, fy - 0.0, 0.5)), m, head, r=0.04, rot=(0, s * D7(-8), 0))
        rb("StacheCurl", (0.1, 0.09, 0.19), _V7((s * 0.45, fy - 0.04, 0.56)), m, head, r=0.04, rot=(0, s * D7(-28), 0))


# ================================================================== TOWN PLAZA + STAGE (faces -X, toward the crowd)
def banner_img(path):
    im = Image.new("RGB", (1600, 400), (250, 244, 225)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1599, 399), outline=(150, 30, 40), width=18)
    d.text((800, 120), "YOU MUST BE THIS TALL", font=pfont(120), fill=(150, 30, 40), anchor="mm")
    d.text((800, 260), "TO HAVE AN OPINION", font=pfont(96), fill=(40, 50, 90), anchor="mm")
    d.line((60, 345, 1540, 345), fill=(40, 50, 90), width=10)
    for k in range(0, 1480, 74): d.line((60 + k, 330, 60 + k, 360), fill=(40, 50, 90), width=6)
    return save_img(im, "hm_banner")


def seal_img(path):
    """Town seal on the podium: a ladder + crown (original design)."""
    im = Image.new("RGB", (600, 600), (40, 50, 90)); d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 580, 580), fill=(214, 172, 70)); d.ellipse((60, 60, 540, 540), fill=(40, 50, 90))
    for x in (240, 360): d.rectangle((x - 14, 150, x + 14, 470), fill=(245, 240, 220))
    for y in range(180, 461, 56): d.rectangle((240, y, 360, y + 14), fill=(245, 240, 220))
    d.polygon([(220, 140), (250, 90), (275, 125), (300, 70), (325, 125), (350, 90), (380, 140)], fill=(214, 172, 70))
    d.text((300, 515), "TALLER TOGETHER", font=pfont(34), fill=(214, 172, 70), anchor="mm")
    return save_img(im, "hm_seal")


def flag_img(path):
    """Town flag: navy + red bands, gold ladder crest."""
    im = Image.new("RGB", (600, 400), (40, 50, 90)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 200, 400), fill=(170, 35, 45)); d.rectangle((400, 0, 600, 400), fill=(170, 35, 45))
    for x in (270, 330): d.rectangle((x - 9, 110, x + 9, 300), fill=(214, 172, 70))
    for y in range(130, 291, 40): d.rectangle((270, y, 330, y + 10), fill=(214, 172, 70))
    return save_img(im, "hm_flag")


def hm_plaza(c=(195, 0), r=34):
    """Paved square over the road end in front of the mansion: big slabs, kerb ring, two planters, a bench."""
    root = root_of("Plaza", (c[0], c[1], 0))
    rb("PlazaFloor", (2 * r, 2 * r + 10, 0.36), _V7((0, 0, 0.2)), tex_mat("PlazaSlabs", (214, 204, 186), "slabs"), root, r=0.05)
    kerb = m7("kerb", (170, 162, 150), rough=0.8)
    for s in (-1, 1):
        rb("Kerb", (2 * r, 0.6, 0.5), _V7((0, s * (r + 5), 0.25)), kerb, root, r=0.1)
    rb("CentreTile", (10, 10, 0.06), _V7((-14, 0, 0.4)), m7("tile_red", (170, 70, 60), rough=0.7), root, r=0.02)
    for s in (-1, 1):
        p = root_of("Planter", (c[0] - 20, c[1] + s * 22, 0)); p.parent = None
        rb("PlanterBox", (4, 4, 1.6), _V7((0, 0, 1.0)), kerb, p, r=0.15)
        rb("PlanterSoil", (3.5, 3.5, 0.1), _V7((0, 0, 1.8)), m7("soil", (70, 50, 35), rough=1.0), p, r=0.03)
        for k in range(5):
            a = k * 1.25
            rcyl("Flower", 0.35, 0.3, _V7((math.cos(a) * 1.1, math.sin(a) * 1.1, 2.1)),
                 m7("flower%d" % (k % 3), [(230, 70, 90), (250, 200, 60), (240, 240, 245)][k % 3]), p, bevel=0.1, seg=10)
            rb("Leaf", (0.5, 0.2, 0.5), _V7((math.cos(a) * 0.7, math.sin(a) * 0.7, 2.0)), m7("leaf", (70, 140, 60)), p, r=0.08)
    return root


def hm_stage(c=(209, 0), w=20, d=10, h=2.4):
    """Stage facing -X: plank deck, navy skirt with gold trim, red/white/navy bunting swags, front steps, back wall with the
    'must be this tall' banner, two flag poles, podium with the seal and a gooseneck mic. Returns dict of key objects."""
    x0, y0 = c
    root = root_of("Stage", (x0, y0, 0))
    plank = wood("hm_stageplank", (160, 112, 70), scale=3.0)
    rb("Deck", (d, w, 0.3), _V7((0, 0, h - 0.15)), plank, root, r=0.05)
    for k in range(-4, 5):
        rb("DeckGap", (d, 0.05, 0.02), _V7((0, k * 2.2, h + 0.005)), m7("deckgap", (90, 60, 40)), root, r=0.01)
    navy = m7("navy", (40, 50, 90), rough=0.85); gold = m7("gold", (214, 172, 70), rough=0.3, metal=0.9)
    rb("Skirt", (d - 0.2, w - 0.2, h - 0.3), _V7((0, 0, (h - 0.3) / 2)), navy, root, r=0.05)
    rb("SkirtTrim", (d + 0.05, w + 0.05, 0.18), _V7((0, 0, h - 0.38)), gold, root, r=0.04)
    # bunting swags along the front edge (-X face): little triangle flags on a sagging line
    cols = [m7("bunt_r", (190, 40, 50)), m7("bunt_w", (245, 245, 240)), m7("bunt_b", (40, 70, 150))]
    n = 18
    for k in range(n):
        u = (k + 0.5) / n; yy = -w / 2 + u * w
        sag = 0.45 * math.sin(math.pi * ((u * 3) % 1.0))
        tri = taper("Bunting", (0.06, 0.7, 0.7), _V7((-d / 2 - 0.08, yy, h - 0.75 - sag)), cols[k % 3], root,
                    top=(1.0, 0.05), r=0.01)
        tri.rotation_euler = (D7(180), 0, 0)
    # steps at the front-left
    for k in range(3):
        rb("Step", (1.2, 4, h * (k + 1) / 4), _V7((-d / 2 - 0.6 - (2 - k) * 1.2, -w / 2 + 3, h * (k + 1) / 8)), plank, root, r=0.05)
    # back wall + banner
    rb("BackWall", (0.6, w, 14), _V7((d / 2 - 0.3, 0, h + 7.0)), navy, root, r=0.1)
    rb("BackWallCap", (0.9, w + 0.3, 0.35), _V7((d / 2 - 0.3, 0, h + 14.0)), gold, root, r=0.06)
    bn = plane("Banner", 14, 3.5, _V7((d / 2 - 0.62, 0, h + 11.8)), imgmat("hm_banner", banner_img(None), rough=0.85), root,
               rot=(0, 0, D7(90)))
    # flag poles with flags (cloth slightly waved)
    fimg = imgmat("hm_flag", flag_img(None), rough=0.85)
    flags = []
    for s in (-1, 1):
        py = s * (w / 2 - 1.2)
        rcyl("FlagPole", 0.12, 15, _V7((d / 2 - 1.5, py, h + 7.5)), gold, root, seg=12)
        rcyl("PoleTop", 0.25, 0.4, _V7((d / 2 - 1.5, py, h + 15.1)), gold, root, seg=12)
        f = plane("Flag", 3.0, 2.0, _V7((d / 2 - 1.5, py - s * 1.6, h + 13.6)), fimg, root, rot=(0, 0, D7(90)))
        f.data.vertices[0].co.y += 0.25; f.data.vertices[3].co.y += 0.25      # a little wave in the fly end
        flags.append(f)
    pod = hm_podium(root, _V7((-1.0, 0, h)))
    return dict(root=root, deck_z=h, podium=pod, flags=flags, banner=bn, front_x=x0 - d / 2)


def hm_podium(parent, loc):
    """Wooden lectern facing -X: tapered body, slanted top with a paper sheet, the seal, a gooseneck mic with a foam ball."""
    r = root_of("Podium", loc); r.parent = parent; r.rotation_euler = (0, 0, D7(90))   # its local +Y = world -X
    wd = wood("hm_podium", (120, 74, 44), scale=2.0)
    taper("PodBody", (2.6, 1.6, 3.6), _V7((0, 0, 1.8)), wd, r, top=(1.1, 1.05), r=0.1)
    rb("PodBase", (3.0, 2.0, 0.3), _V7((0, 0, 0.15)), wd, r, r=0.06)
    rb("PodTop", (3.0, 2.0, 0.22), _V7((0, -0.1, 3.75)), wd, r, r=0.06, rot=(D7(-12), 0, 0))
    plane("PodPaper", 1.0, 1.3, _V7((-0.4, -0.1, 3.9)), m7("paper", (250, 248, 240), rough=0.9), r, rot=(D7(-78), 0, 0))
    plane("PodSeal", 1.5, 1.5, _V7((0, 0.86, 2.2)), imgmat("hm_seal", seal_img(None), rough=0.5), r)
    blk = m7("micblack", (25, 25, 28), rough=0.35, metal=0.4)
    neck = [_V7((0.8, -0.3, 3.85)), _V7((0.8, 0.1, 4.4)), _V7((0.7, 0.5, 4.75))]
    for a, b in zip(neck, neck[1:]):
        mid = (a + b) / 2; v = b - a
        rb("MicNeck", (0.1, 0.1, v.length + 0.05), mid, blk, r, r=0.04, rot=(-math.atan2(v.y, v.z), 0, 0))
    mic = rcyl("MicHead", 0.2, 0.5, _V7((0.7, 0.62, 4.82)), blk, r, axis="Y", bevel=0.08, seg=16)
    rcyl("MicFoam", 0.24, 0.3, _V7((0.7, 0.88, 4.85)), m7("micfoam", (190, 40, 50), rough=0.95), r, axis="Y", bevel=0.1, seg=16)
    return r


def hm_curtain(loc=(214, 16, 0), w=6, h=12, rgb=(150, 28, 40)):
    """Backstage wing: heavy red curtain in alternating folds (faces -X), gold tie-back rope, rail, a dark wing behind,
    a sandbag + a coiled cable on the floor."""
    root = root_of("Curtain", loc)
    vel = m7("velvet", rgb, rough=0.95); vel2 = m7("velvet_dk", dk(rgb, 0.6), rough=0.95)
    n = 12
    for k in range(n):
        y = -w / 2 + (k + 0.5) * w / n + 2.0
        rb("Fold", (0.5 if k % 2 else 0.35, w / n + 0.12, h), _V7((0.25 if k % 2 else 0.0, y, h / 2)), vel if k % 2 == 0 else vel2, root, r=0.15)
    rb("Rail", (0.3, w + 1, 0.3), _V7((0.1, 2.0, h + 0.2)), m7("gold", (214, 172, 70), rough=0.3, metal=0.9), root, r=0.1)
    rb("TieRope", (0.7, 0.25, 0.25), _V7((-0.2, -w / 2 + 2.6, h * 0.42)), m7("gold", (214, 172, 70), rough=0.3, metal=0.9), root, r=0.1)
    rcyl("Tassel", 0.18, 0.7, _V7((-0.25, -w / 2 + 2.3, h * 0.42 - 0.6)), m7("gold", (214, 172, 70), rough=0.3, metal=0.9), root, seg=10)
    dark = m7("wing_dark", (24, 22, 26), rough=1.0)
    rb("WingFloor", (24, 22, 0.2), _V7((4, 0, -0.1)), m7("wing_floor", (50, 42, 38), rough=0.9), root, r=0.02)
    rb("WingBack", (0.4, 20, h + 2), _V7((14, 0, (h + 2) / 2)), dark, root, r=0.05)
    rb("WingRoof", (16, 20, 0.4), _V7((7, 0, h + 2)), dark, root, r=0.05)
    for s_ in (-1, 1): rb("WingSide", (16, 0.4, h + 2), _V7((7, s_ * 10, (h + 2) / 2)), dark, root, r=0.05)
    rb("Ladder", (0.2, 1.4, 9), _V7((13.5, 5, 4.5)), m7("ladder", (120, 90, 60)), root, r=0.05)
    for k in range(8): rb("Rung", (0.3, 1.4, 0.12), _V7((13.4, 5, 1 + k * 1.05)), m7("ladder", (120, 90, 60)), root, r=0.03)
    rb("Sandbag", (1.2, 0.8, 0.6), _V7((2.5, -w / 2 + 1.5, 0.5)), m7("sand", (150, 130, 95), rough=0.95), root, r=0.25)
    for k in range(4):
        rcyl("Cable", 0.6 - k * 0.04, 0.08, _V7((4.5, 1.5, 0.25 + k * 0.08)), m7("cable", (30, 30, 30)), root, bevel=0.03, seg=20)
    return root


# ================================================================== TOWN BUS
def bus_ad_img(path):
    im = Image.new("RGB", (1200, 360), (250, 210, 60)); d = ImageDraw.Draw(im)
    d.text((600, 110), "STAND TALLER", font=pfont(110), fill=(40, 50, 90), anchor="mm")
    d.text((600, 240), "LIFT SHOES  +3 INCHES", font=pfont(70), fill=(170, 35, 45), anchor="mm")
    return save_img(im, "hm_bus_ad")


def route_img(path):
    im = Image.new("RGB", (800, 160), (20, 20, 22)); d = ImageDraw.Draw(im)
    d.text((400, 80), "7  TOWN SQUARE", font=pfont(90), fill=(255, 170, 40), anchor="mm")
    return save_img(im, "hm_route")


def hm_bus(name="Bus", loc=(0, 0, 0), body=(60, 150, 120)):
    """City bus ~30 long x 9 wide x 11 tall, front +Y: two-tone body, window band, folding door, route LED sign,
    side ad, wheels, bumpers, lights, mirrors, roof AC pod, exhaust pipe at the back."""
    root = root_of(name, loc)
    paint = pmat("BusPaint", body, rough=0.3, coat=0.8); cream = pmat("BusCream", (245, 240, 225), rough=0.3, coat=0.8)
    trim = m7("bus_trim", (30, 30, 34), rough=0.5); win = m7("bus_win", (30, 40, 55), rough=0.08, metal=0.2)
    L, W, H = 30.0, 9.0, 10.5
    rb("BusLower", (W, L, 4.2), _V7((0, 0, 3.2)), paint, root, r=0.6)
    rb("BusBand", (W + 0.02, L + 0.02, 0.4), _V7((0, 0, 5.2)), cream, root, r=0.15)
    rb("BusUpper", (W - 0.1, L - 0.2, 4.6), _V7((0, -0.1, 7.6)), cream, root, r=0.8)
    rb("BusRoofAC", (5, 7, 0.9), _V7((0, -4, 10.3)), cream, root, r=0.3)
    for s in (-1, 1):
        for k in range(6):
            rb("BusWin", (0.08, 3.8, 3.0), _V7((s * (W / 2 - 0.03), -12 + k * 4.4 + (1.6 if s > 0 and k == 5 else 0), 7.6)), win, root, r=0.15)
        rb("BusSkirt", (0.2, L - 2, 0.6), _V7((s * W / 2, 0, 1.3)), trim, root, r=0.1)
        for yy in (9.5, -9.5):
            rcyl("BusArch", 2.1, 0.25, _V7((s * (W / 2 - 0.05), yy, 1.7)), trim, root, axis="X", bevel=0.08)
            wheel(root, _V7((s * (W / 2 - 0.6), yy, 1.6)), s, R=1.6, W=1.1)
        rb("BusMirror", (0.3, 0.6, 1.2), _V7((s * (W / 2 + 0.6), L / 2 - 0.6, 7.2)), trim, root, r=0.1)
        rb("BusMirArm", (1.0, 0.15, 0.15), _V7((s * (W / 2 + 0.2), L / 2 - 0.6, 7.9)), trim, root, r=0.05)
    # door (right side, front): two folding leaves with glass
    for k in range(2):
        rb("BusDoor", (0.1, 1.6, 6.8), _V7((W / 2 + 0.02, 11.0 + k * 1.65, 4.6)), win, root, r=0.1)
        rb("BusDoorFrame", (0.12, 1.7, 0.2), _V7((W / 2 + 0.04, 11.0 + k * 1.65, 1.3)), trim, root, r=0.05)
    plane("BusAd", 12, 3.6, _V7((-W / 2 - 0.05, -2, 3.3)), imgmat("hm_bus_ad", bus_ad_img(None), rough=0.4), root, rot=(0, 0, D7(90)))
    plane("BusAd2", 12, 3.6, _V7((W / 2 + 0.05, -4, 3.3)), imgmat("hm_bus_ad", bus_ad_img(None), rough=0.4), root, rot=(0, 0, D7(-90)))
    # front: big windscreen, route sign, lights, bumper, plate
    rb("BusScreen", (W - 1.2, 0.1, 4.2), _V7((0, L / 2 + 0.0, 7.3)), win, root, r=0.2)
    rsign = plane("BusRoute", 6, 1.1, _V7((0, L / 2 + 0.06, 9.85)), imgmat("hm_route", route_img(None), emit=1.5), root)
    hl = pmat("BusHead", (255, 250, 230), rough=0.1, emit=2.0); tl = pmat("BusTail", (220, 20, 30), rough=0.2, emit=2.0)
    for s in (-1, 1):
        rcyl("BusHeadL", 0.45, 0.2, _V7((s * 3.2, L / 2 + 0.05, 2.6)), hl, root, axis="Y", bevel=0.05, seg=16)
        rb("BusTailL", (0.8, 0.15, 1.6), _V7((s * 3.6, -L / 2 - 0.05, 3.5)), tl, root, r=0.1)
    rb("BusBumperF", (W, 0.7, 0.9), _V7((0, L / 2 + 0.2, 1.4)), trim, root, r=0.25)
    rb("BusBumperR", (W, 0.7, 0.9), _V7((0, -L / 2 - 0.2, 1.4)), trim, root, r=0.25)
    rb("BusGrille", (4, 0.12, 1.0), _V7((0, L / 2 + 0.03, 2.6)), trim, root, r=0.1)
    exhaust = rcyl("BusExhaust", 0.25, 1.0, _V7((-3.0, -L / 2 - 0.4, 1.0)), CHROME(), root, axis="Y", bevel=0.05, seg=12)
    return dict(root=root, exhaust=exhaust, door_y=11.8)


# ================================================================== DOG (pivots: head, tail, 4 legs)
def hm_dog(name="Dog", loc=(0, 0, 0), coat=(196, 140, 80), patch=(245, 240, 230)):
    """Blocky R6-style dog, front +Y, ~2.6 tall: body, chest patch, head on a pivot (snout, black nose, eyes with
    catchlights, floppy ears), tail on a pivot, four legs on hip pivots with white socks, red collar + gold tag."""
    root = root_of(name, loc)
    fur = m7("dogfur%d" % hash(coat), coat, rough=0.85); pt = m7("dogpatch", patch, rough=0.85)
    ink = m7("dogink", (20, 18, 18), rough=0.3)
    rb("DogBody", (1.4, 3.0, 1.3), _V7((0, 0, 1.75)), fur, root, r=0.25)
    rb("DogChest", (1.0, 0.2, 0.9), _V7((0, 1.5, 1.6)), pt, root, r=0.15)
    legs = {}
    for k, (lx, ly) in enumerate(((-0.42, 1.05), (0.42, 1.05), (-0.42, -1.05), (0.42, -1.05))):
        hip = root_of(name + "Hip%d" % k, (lx, ly, 1.3)); hip.parent = root
        rb("DogLeg", (0.45, 0.45, 1.15), _V7((0, 0, -0.6)), fur, hip, r=0.12)
        rb("DogSock", (0.48, 0.55, 0.3), _V7((0, 0.05, -1.1)), pt, hip, r=0.1)
        legs[k] = hip
    hp = root_of(name + "Head", (0, 1.45, 2.35)); hp.parent = root
    rb("DogHead", (1.15, 1.1, 1.05), _V7((0, 0.35, 0.25)), fur, hp, r=0.25)
    rb("DogSnout", (0.65, 0.7, 0.5), _V7((0, 1.05, 0.05)), pt, hp, r=0.15)
    rb("DogNose", (0.3, 0.15, 0.2), _V7((0, 1.42, 0.2)), ink, hp, r=0.07)
    rb("DogMouth", (0.32, 0.05, 0.04), _V7((0, 1.41, -0.08)), ink, hp, r=0.01)
    for s in (-1, 1):
        rb("DogEye", (0.18, 0.06, 0.22), _V7((s * 0.27, 0.92, 0.45)), ink, hp, r=0.06)
        rb("DogSpark", (0.06, 0.02, 0.06), _V7((s * 0.24, 0.96, 0.5)), m7("dogspark", (255, 255, 255), emit=1.0), hp, r=0.02)
        rb("DogEar", (0.28, 0.45, 0.7), _V7((s * 0.62, 0.25, 0.35)), m7("dogear", dk(coat, 0.6), rough=0.85), hp, r=0.1,
           rot=(D7(10), s * D7(18), 0))
    rb("DogCollar", (1.25, 0.25, 0.22), _V7((0, 1.35, 2.05)), m7("collar", (200, 40, 45), rough=0.5), root, r=0.08, rot=(D7(-30), 0, 0))
    rcyl("DogTag", 0.14, 0.05, _V7((0, 1.55, 1.85)), m7("gold", (214, 172, 70), rough=0.3, metal=0.9), root, axis="Y", bevel=0.02, seg=12)
    tp = root_of(name + "Tail", (0, -1.5, 2.2)); tp.parent = root
    rb("DogTail", (0.26, 0.26, 1.1), _V7((0, -0.15, 0.45)), fur, tp, r=0.1, rot=(D7(-30), 0, 0))
    rb("DogTailTip", (0.28, 0.28, 0.3), _V7((0, -0.42, 0.95)), pt, tp, r=0.1)
    return dict(root=root, head=hp, tail=tp, legs=legs)


# ================================================================== BANQUET TABLE + PEN
def hm_banquet(name="Banquet", loc=(0, 0, 0), L=22, seats=5):
    """Long town-dinner table along Y: white cloth with a red runner, plates with food, cups, a roast centrepiece,
    flower vases, candlesticks (unlit), benches on both sides. Seat height 1.9 (short legs: town furniture)."""
    root = root_of(name, loc)
    cloth = m7("cloth", (248, 246, 240), rough=0.9); run = m7("runner", (170, 35, 45), rough=0.9)
    wd = wood("hm_table", (130, 86, 52), scale=2.0)
    th = 3.0
    rb("TableTop", (4.2, L, 0.25), _V7((0, 0, th)), cloth, root, r=0.06)
    rb("ClothDrop", (4.3, L + 0.1, 0.45), _V7((0, 0, th - 0.3)), cloth, root, r=0.05)
    rb("Runner", (1.2, L - 1, 0.03), _V7((0, 0, th + 0.14)), run, root, r=0.01)
    for sx in (-1.6, 1.6):
        for sy in (-L / 2 + 1, L / 2 - 1):
            rb("TableLeg", (0.4, 0.4, th - 0.9), _V7((sx, sy, (th - 0.9) / 2)), wd, root, r=0.06)
    plate = m7("plate", (250, 250, 252), rough=0.25); foods = [m7("peas", (90, 160, 60)), m7("mash", (240, 225, 180)),
                                                                m7("meat", (150, 80, 50))]
    for s in (-1, 1):
        rb("Bench", (1.5, L - 1, 0.35), _V7((s * 3.4, 0, 1.75)), wd, root, r=0.08)
        for sy in (-L / 2 + 2, 0, L / 2 - 2):
            rb("BenchLeg", (1.2, 0.35, 1.6), _V7((s * 3.4, sy, 0.8)), wd, root, r=0.05)
        for k in range(seats):
            y = -L / 2 + (k + 0.5) * L / seats
            rcyl("Plate", 0.6, 0.08, _V7((s * 1.4, y, th + 0.17)), plate, root, bevel=0.03, seg=20)
            rcyl("Food", 0.28, 0.12, _V7((s * 1.4 + 0.1, y + 0.12, th + 0.25)), foods[(k + (s > 0)) % 3], root, bevel=0.05, seg=10)
            rcyl("Cup", 0.2, 0.5, _V7((s * 1.0, y + 0.6, th + 0.38)), m7("cup%d" % (k % 2), [(80, 140, 210), (230, 120, 60)][k % 2], rough=0.4),
                 root, bevel=0.04, seg=14)
    roast = m7("roast", (180, 110, 50), rough=0.5)
    rb("Platter", (1.4, 2.2, 0.08), _V7((0, 0, th + 0.18)), m7("silver", (210, 212, 218), rough=0.2, metal=0.9), root, r=0.04)
    rb("Roast", (0.9, 1.4, 0.7), _V7((0, 0, th + 0.55)), roast, root, r=0.3)
    for s in (-1, 1):
        rb("Drumstick", (0.3, 0.6, 0.3), _V7((s * 0.5, 0.5, th + 0.5)), roast, root, r=0.12, rot=(0, 0, s * D7(30)))
        for yy in (-6, 6):
            rcyl("Vase", 0.25, 0.7, _V7((0, yy + s * 1.5, th + 0.5)), m7("vase", (60, 90, 160), rough=0.3), root, bevel=0.08, seg=14)
            rcyl("Bloom", 0.3, 0.3, _V7((0, yy + s * 1.5, th + 1.0)), m7("flower0", (230, 70, 90)), root, bevel=0.1, seg=10)
            rcyl("Candle", 0.1, 0.9, _V7((0, yy, th + 0.6)), m7("candle", (250, 245, 225), rough=0.6), root, seg=10)
    return root


def hm_pen(name="Pen", loc=(0, 0, 0), parent=None):
    """Mayor's fountain pen (~0.9 long, along Y): black lacquer barrel, gold bands + clip, gold nib."""
    r = root_of(name, loc)
    if parent: r.parent = parent
    lac = m7("pen_lacquer", (20, 20, 26), rough=0.15); gold = m7("gold", (214, 172, 70), rough=0.3, metal=0.9)
    rcyl("PenBarrel", 0.06, 0.62, _V7((0, -0.05, 0)), lac, r, axis="Y", bevel=0.02, seg=14)
    rcyl("PenCap", 0.065, 0.28, _V7((0, -0.42, 0)), lac, r, axis="Y", bevel=0.03, seg=14)
    for yy in (-0.29, -0.55): rcyl("PenBand", 0.068, 0.04, _V7((0, yy, 0)), gold, r, axis="Y", bevel=0.01, seg=14)
    rb("PenClip", (0.03, 0.24, 0.03), _V7((0, -0.42, 0.075)), gold, r, r=0.01)
    rcyl("PenNib", 0.05, 0.16, _V7((0, 0.34, 0)), gold, r, axis="Y", bevel=0.0, seg=10, top_scale=0.15)
    return r


# ================================================================== TOWN MAKEOVER: Bloxbury map -> TALLTON (sunny comedy town)
HM_HOUSE_COLS = [(250, 200, 120), (140, 210, 190), (245, 150, 140), (180, 170, 235), (150, 200, 240), (250, 230, 140),
                 (235, 170, 200), (170, 220, 140), (255, 185, 110), (130, 190, 220), (240, 220, 200), (200, 160, 220)]
HM_ROOF_COLS = [(190, 90, 60), (60, 90, 130), (50, 120, 110), (120, 60, 90)]
HM_SHOPS = [("TALL & CO.", "LIFT SHOES", (40, 50, 90), (250, 205, 60)), ("LADDER BAKERY", "FRESH DAILY", (170, 60, 50), (250, 240, 220)),
            ("STILTS", "ICE CREAM", (230, 90, 150), (255, 250, 240)), ("UP-TOWN CAFE", "COFFEE + CAKE", (50, 120, 110), (250, 240, 220)),
            ("HIGH CUTS", "BARBER", (30, 30, 36), (240, 60, 60)), ("TOP SHELF", "BOOKS", (90, 60, 140), (250, 230, 160))]


def shop_sign_img(name, sub, bg, fg):
    im = Image.new("RGB", (1000, 300), bg); d = ImageDraw.Draw(im)
    d.rectangle((10, 10, 989, 289), outline=fg, width=10)
    d.text((500, 120), name, font=pfont(110), fill=fg, anchor="mm"); d.text((500, 230), sub, font=pfont(54), fill=fg, anchor="mm")
    return save_img(im, "hm_shop_" + name.replace(" ", "_").replace("&", "and").replace(".", ""))


def town_sign_img():
    im = Image.new("RGB", (1200, 460), (250, 244, 225)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1199, 459), outline=(40, 50, 90), width=16)
    d.text((600, 120), "WELCOME TO", font=pfont(70), fill=(40, 50, 90), anchor="mm")
    d.text((600, 230), "TALLTON", font=pfont(150), fill=(170, 35, 45), anchor="mm")
    d.text((600, 360), "Population 214 (listed by height)", font=pfont(52), fill=(60, 60, 60), anchor="mm")
    return save_img(im, "hm_town_sign")


def clock_img():
    im = Image.new("RGB", (600, 600), (40, 50, 90)); d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 580, 580), fill=(250, 244, 225), outline=(214, 172, 70), width=24)
    for k in range(12):
        a = k * math.pi / 6; d.line((300 + 230 * math.sin(a), 300 - 230 * math.cos(a), 300 + 260 * math.sin(a), 300 - 260 * math.cos(a)),
                                    fill=(40, 40, 40), width=14)
    d.line((300, 300, 300, 120), fill=(20, 20, 20), width=16); d.line((300, 300, 420, 330), fill=(20, 20, 20), width=12)
    return save_img(im, "hm_clock")


def _kids(root): return [root] + list(root.children_recursive)


def _front(root):
    """House front (Blender): returns (front_y, dirn) where dirn = +1 if the front faces +Y."""
    y = root.location.y
    return (y + 10.0, 1) if y < 0 else (y - 10.0, -1)


def hm_shopfront(root, k):
    """Striped awning, a big sign board with a generated name, a display window with goods, a planter, a bench."""
    name, sub, bg, fg = HM_SHOPS[k % len(HM_SHOPS)]
    fy, n = _front(root); x0 = root.location.x
    r = root_of("Shop_" + name, (x0, fy, 0)); r.rotation_euler = (0, 0, 0 if n > 0 else math.pi)   # local +Y = out of the wall
    stripes = (m7("awn_%d" % k, bg, rough=0.8), m7("awn_w", (250, 248, 240), rough=0.8))
    for i in range(10):
        rb("Awning", (2.0, 3.0, 0.15), _V7((-9 + i * 2.0, 1.4, 11.2)), stripes[i % 2], r, r=0.03, rot=(D7(-20), 0, 0))
    for i in range(10):
        rb("AwnFlap", (2.0, 0.08, 0.6), _V7((-9 + i * 2.0, 2.85, 10.4)), stripes[i % 2], r, r=0.02)
    plane("ShopSign", 12, 3.6, _V7((0, 0.32, 12.6)), imgmat("hm_shopsign_%d" % k, shop_sign_img(name, sub, bg, fg), rough=0.5), r)
    rb("SignFrame", (12.6, 0.3, 4.2), _V7((0, 0.12, 12.6)), m7("signframe", (60, 45, 35)), r, r=0.08)
    win = m7("shopwin", (40, 55, 70), rough=0.08, metal=0.2)
    for s in (-1, 1):
        rb("ShopWin", (6.0, 0.2, 4.6), _V7((s * 6.6, 0.3, 4.2)), win, r, r=0.05)
        rb("ShopWinFrame", (6.4, 0.25, 0.3), _V7((s * 6.6, 0.33, 1.8)), m7("winframe", (250, 248, 240)), r, r=0.05)
        for j in range(3):                                                 # goods on the display shelf
            rb("Goods", (1.0, 0.6, 1.0 + 0.3 * j), _V7((s * 6.6 - 1.8 + j * 1.8, 0.0, 2.6 + 0.15 * j)),
               m7("goods%d" % ((k + j) % 3), [(250, 205, 60), (230, 90, 150), (60, 150, 220)][(k + j) % 3], rough=0.4), r, r=0.15)
        rb("Planter", (2.2, 1.2, 1.2), _V7((s * 3.6, 1.2, 0.6)), m7("planter", (120, 80, 60)), r, r=0.1)
        for j in range(3):
            rcyl("PFlower", 0.4, 0.4, _V7((s * 3.6 - 0.6 + j * 0.6, 1.2, 1.4)), m7("flower%d" % j, [(230, 70, 90), (250, 200, 60), (240, 240, 245)][j]),
                 r, bevel=0.1, seg=10)
    return r


def hm_town_hall():
    """The mansion becomes Tallton Town Hall: warm stone + terracotta roof, clock tower with a flag, pediment sign."""
    for nm, col in (("Marble", (238, 226, 205)), ("MansionRoof", (180, 85, 60))):
        m = bpy.data.materials.get(nm)
        if m: _nodes(m)[3].inputs["Base Color"].default_value = (*lin(col), 1)
    root = root_of("TownHall", (245, 0, 0))
    stone = m7("hall_stone", (238, 226, 205), rough=0.6); terr = m7("hall_roof", (180, 85, 60), rough=0.7)
    gold = m7("gold", (214, 172, 70), rough=0.3, metal=0.9)
    rb("Tower", (9, 9, 12), _V7((0, 0, 35)), stone, root, r=0.2)
    rb("TowerTrim", (9.6, 9.6, 0.6), _V7((0, 0, 41.2)), gold, root, r=0.1)
    taper("TowerRoof", (10, 10, 6), _V7((0, 0, 44.5)), terr, root, top=(0.05, 0.05), r=0.1)
    plane("Clock", 6, 6, _V7((-4.56, 0, 35.5)), imgmat("hm_clock", clock_img(), rough=0.4), root, rot=(0, 0, D7(90)))
    rcyl("TPole", 0.15, 6, _V7((0, 0, 50)), gold, root, seg=10)
    f = plane("TFlag", 3.6, 2.4, _V7((0, -1.9, 51.6)), imgmat("hm_flag", flag_img(None), rough=0.85), root, rot=(0, 0, D7(90)))
    taper("Pediment", (2.0, 44, 5), _V7((-21.5, 0, 31.5)), stone, root, top=(1.0, 0.05), r=0.1)
    im = Image.new("RGB", (1400, 220), (238, 226, 205)); d = ImageDraw.Draw(im)
    d.text((700, 110), "TALLTON TOWN HALL", font=pfont(130), fill=(40, 50, 90), anchor="mm")
    plane("HallSign", 22, 3.4, _V7((-20.62, 0, 26.0)), imgmat("hm_hallsign", save_img(im, "hm_hallsign"), rough=0.6), root, rot=(0, 0, D7(90)))
    for k in range(4):                                                   # front steps
        rb("HallStep", (2.0, 30, 0.5 * (k + 1)), _V7((-21 - (3 - k) * 2.0, 0, 0.25 * (k + 1))), stone, root, r=0.05)
    return root


def hm_bunting_line(a, b, n=22, sag=1.2, seed=0):
    """A string of triangle flags hung between two points (sags in the middle)."""
    a, b = _V7(a), _V7(b); root = root_of("BuntLine", a)
    cols = [m7("bunt_r", (190, 40, 50)), m7("bunt_w", (245, 245, 240)), m7("bunt_b", (40, 70, 150)), m7("bunt_y", (250, 205, 60))]
    d = b - a; yaw = math.atan2(d.y, d.x)
    for k in range(n):
        u = (k + 0.5) / n; p = d * u + _V7((0, 0, -sag * 4 * u * (1 - u)))
        t = taper("Flaglet", (0.06, 0.9, 0.9), p + _V7((0, 0, -0.45)), cols[(k + seed) % 4], root, top=(1.0, 0.05), r=0.01)
        t.rotation_euler = (D7(180), 0, yaw + D7(90))
    for k in range(12):
        u0, u1 = k / 12, (k + 1) / 12
        p0 = d * u0 + _V7((0, 0, -sag * 4 * u0 * (1 - u0))); p1 = d * u1 + _V7((0, 0, -sag * 4 * u1 * (1 - u1)))
        v = p1 - p0; mid = (p0 + p1) / 2
        rb("BuntRope", (v.length + 0.05, 0.05, 0.05), mid, m7("rope", (240, 240, 235)), root, r=0.02, rot=(0, -math.atan2(v.z, math.hypot(v.x, v.y)), yaw))
    return root


def hm_town_makeover(houses):
    """Recolour + redress the Bloxbury map into Tallton: pastel houses with coloured roofs/doors, six shopfronts near the plaza,
    the town hall, bunting across the road, painted green lamp posts with flower baskets, a zebra crossing, a new welcome
    sign; horror leftovers (fog walls, moving van, boards, clock text, old sign text) hidden."""
    hide = ("Hollow_", "MoveVan", "VanBody", "VanCab", "VanWindshield", "Wheel", "VanLabel", "BoardPlank", "Clock ", "SignTitle", "SignPopulation")
    for o in bpy.data.objects:
        if o.name.startswith(hide): o.hide_render = True
    van = bpy.data.objects.get("MoveVan")
    if van:
        for o in _kids(van): o.hide_render = True
    allh = dict(houses)
    for nm in ("MiloHouse",):
        if bpy.data.objects.get(nm): allh[nm] = bpy.data.objects[nm]
    for i, (nm, root) in enumerate(sorted(allh.items())):
        body = tex_mat("HM_" + nm, HM_HOUSE_COLS[i % len(HM_HOUSE_COLS)], "siding")
        roof = m7("roof%d" % (i % 4), HM_ROOF_COLS[i % 4], rough=0.75)
        door = m7("door%d" % (i % 5), [(40, 70, 150), (190, 40, 50), (50, 120, 110), (250, 205, 60), (90, 60, 140)][i % 5], rough=0.4)
        for o in _kids(root):
            b = o.name.split(".")[0]
            if o.type != "MESH": continue
            if b in ("Body", "WallFront", "WallBack", "WallLeft", "WallRight", "WallFrontTop"): o.data.materials[0] = body if o.data.materials else None
            elif b in ("Roof", "Attic"): o.data.materials[0] = roof
            elif b in ("Door", "FrontDoor"): o.data.materials[0] = door
    shops = [n for n in sorted(allh) if n.startswith("House_") and allh[n].location.x >= 50]
    for k, nm in enumerate(shops): hm_shopfront(allh[nm], k)
    m = bpy.data.materials.get("Metal")
    if m: _nodes(m)[3].inputs["Base Color"].default_value = (*lin((40, 80, 60)), 1)
    for o in [o for o in bpy.data.objects if o.name.split(".")[0] == "LampPole" and not o.hide_render]:
        p = o.location; s_ = 1 if p.y > 0 else -1
        rb("Basket", (1.6, 1.6, 1.0), _V7((p.x, p.y - s_ * 1.1, 10.5)), m7("basket", (120, 80, 50)), None, r=0.3)
        for j in range(4):
            rcyl("BFlower", 0.45, 0.4, _V7((p.x - 0.5 + (j % 2), p.y - s_ * 1.1 - 0.4 + (j // 2) * 0.8, 11.1)),
                 m7("flower%d" % (j % 3), [(230, 70, 90), (250, 200, 60), (240, 240, 245)][j % 3]), None, bevel=0.1, seg=10)
    for x in range(-125, 150, 50):
        hm_bunting_line((x, -15, 14.5), (x + 6, 15, 14.5), seed=x // 50)
    for k in range(7):
        rb("Zebra", (1.6, 20, 0.04), _V7((132 + k * 3.2, 0, 0.24)), m7("zebra", (250, 250, 248), rough=0.6), None, r=0.01)
    plane("TownSign", 18, 6.9, _V7((-200, 19.6, 7.0)), imgmat("hm_town_sign", town_sign_img(), rough=0.6), None, rot=(0, 0, D7(180)))
    return hm_town_hall()
