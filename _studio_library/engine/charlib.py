# charlib.py - reusable Roblox R6 character generator (randomised avatars,
# hair/hats/accessories/held items, shirt prints, extra expressions).
# exec() this AFTER the base helpers from bloxbury_part1.py are loaded.
import random

# ---------------------------------------------------------------- palettes
SKINS = [(255, 224, 196), (242, 200, 165), (234, 184, 146), (214, 158, 118), (176, 122, 88),
         (160, 105, 78), (124, 86, 62), (92, 62, 46), (245, 205, 48)]          # last = classic Roblox yellow
CLOTH = [(226, 156, 32), (214, 52, 52), (40, 110, 200), (52, 150, 82), (122, 84, 170), (236, 84, 150),
         (30, 30, 36), (240, 240, 240), (90, 90, 100), (250, 205, 60), (40, 170, 170), (150, 90, 50),
         (255, 130, 60), (110, 180, 240), (70, 40, 110), (190, 30, 60)]
PANTS = [(34, 44, 82), (30, 30, 36), (70, 70, 80), (52, 74, 124), (120, 100, 70), (60, 80, 50),
         (200, 200, 205), (150, 40, 40)]
HAIRC = [(28, 20, 20), (70, 44, 30), (120, 80, 45), (230, 200, 120), (200, 90, 40), (240, 240, 245),
         (236, 84, 150), (80, 140, 230), (140, 230, 120), (60, 60, 65)]
NAMES = ["Jax", "Luna", "Theo", "Kira", "Zane", "Ivy", "Rocco", "Nia", "Felix", "Mae", "Otis", "Zara",
         "Bruno", "Pip", "Remy", "Juno", "Dex", "Lola", "Kai", "Sunny", "Ash", "Coco", "Finn", "Nova"]


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------------------------------------------------------------- extra faces
def expr_smile(f):
    f.eyes()
    f.line([(-0.16, -0.16), (0, -0.23), (0.16, -0.16)], M_INK)


def expr_angry(f):
    f.eyes(w=0.12, h=0.16, z=0.06, shine=False)
    f.line([(-0.32, 0.26), (-0.08, 0.15)], M_INK, r=0.04)
    f.line([(0.08, 0.15), (0.32, 0.26)], M_INK, r=0.04)
    f.oval(0, -0.21, 0.26, 0.1, M_INK)
    f.oval(0, -0.18, 0.2, 0.035, M_EYEWHITE, lift=0.008)


def expr_smug(f):
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.07, 0.13, 0.13, M_INK)
        f.line([(sx - 0.1, 0.12), (sx + 0.1, 0.14)], M_INK, r=0.032)
    f.line([(-0.12, -0.19), (0.04, -0.2), (0.2, -0.12)], M_INK)


def expr_cool(f):  # printed sunglasses decal
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.09, 0.3, 0.19, M_INK)
        f.oval(sx + 0.07, 0.13, 0.08, 0.04, M_SHINE, lift=0.008)
    f.line([(-0.06, 0.13), (0.06, 0.13)], M_INK, r=0.03)
    f.line([(-0.14, -0.18), (0.02, -0.21), (0.18, -0.15)], M_INK)


def expr_crying(f):
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.09, 0.1), (sx, 0.05), (sx + 0.09, 0.1)], M_INK, r=0.03)
        f.oval(sx, -0.08, 0.08, 0.26, M_TEAR, lift=0.004)
    f.line([(-0.3, 0.24), (-0.1, 0.3)], M_INK)
    f.line([(0.1, 0.3), (0.3, 0.24)], M_INK)
    f.oval(0, -0.22, 0.2, 0.13, M_INK)


def expr_wink(f):
    f.oval(-0.2, 0.1, 0.13, 0.24, M_INK)
    f.oval(-0.17, 0.17, 0.05, 0.07, M_SHINE, lift=0.008)
    f.line([(0.11, 0.08), (0.2, 0.14), (0.29, 0.08)], M_INK, r=0.03)
    f.line([(-0.16, -0.15), (0, -0.22), (0.16, -0.15)], M_INK)
    f.oval(0.06, -0.25, 0.12, 0.1, M_TONGUE, lift=0.006)


def expr_nervous(f):
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.08, 0.1, 0.1, M_INK)
    f.line([(-0.3, 0.27), (-0.1, 0.33)], M_INK)
    f.line([(0.1, 0.33), (0.3, 0.27)], M_INK)
    f.line([(-0.18, -0.18), (-0.09, -0.14), (0, -0.18), (0.09, -0.14), (0.18, -0.18)], M_INK, r=0.022)
    f.oval(0.43, 0.3, 0.1, 0.16, M_TEAR, lift=0.004)
    f.oval(-0.42, 0.22, 0.07, 0.11, M_TEAR, lift=0.004)


def expr_evil(f):
    f.line([(-0.3, 0.2), (-0.1, 0.1)], M_INK, r=0.035)
    f.line([(0.1, 0.1), (0.3, 0.2)], M_INK, r=0.035)
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.04, 0.12, 0.07, M_INK)
    f.oval(0, -0.17, 0.5, 0.16, M_INK)
    f.oval(0, -0.15, 0.44, 0.07, M_EYEWHITE, lift=0.008)


def expr_sleepy(f):
    for sx in (-0.2, 0.2):
        f.line([(sx - 0.1, 0.07), (sx + 0.1, 0.07)], M_INK, r=0.03)
    f.oval(0.04, -0.2, 0.1, 0.12, M_INK)


def expr_starstruck(f):
    for sx in (-0.2, 0.2):
        f.oval(sx, 0.1, 0.2, 0.24, M_INK)
        f.oval(sx, 0.1, 0.11, 0.12, mat("StarGold", (255, 210, 60), emit=0.3), lift=0.008)
    f.oval(0, -0.2, 0.3, 0.18, M_INK)
    f.oval(0, -0.25, 0.16, 0.07, M_TONGUE, lift=0.008)


EXPRESSIONS.update({"smile": expr_smile, "angry": expr_angry, "smug": expr_smug, "cool": expr_cool,
                    "crying": expr_crying, "wink": expr_wink, "nervous": expr_nervous, "evil": expr_evil,
                    "sleepy": expr_sleepy, "starstruck": expr_starstruck})
ALL_FACES = ["smile", "laugh", "shocked", "scared", "suspicious", "determined", "sad", "angry", "smug",
             "cool", "crying", "wink", "nervous", "evil", "sleepy", "starstruck"]


# ---------------------------------------------------------------- hair
def hair_short(neck, M, c):
    h = M("Hair", c, rough=0.55)
    ball("HairCap", (1.34, 1.34, 0.6), Vector((0, -0.03, 1.18)), h, neck)
    for i, x in enumerate((-0.4, -0.13, 0.14, 0.41)):
        ball("Fringe", (0.36, 0.3, 0.3), Vector((x, 0.46 - abs(x) * 0.25, 1.1 - (0, .05, .02, .06)[i])), h, neck,
             rot=(math.radians(-25), 0, math.radians(x * 30)))
    ball("BackHair", (1.2, 0.36, 0.7), Vector((0, -0.5, 0.9)), h, neck)


def hair_spiky(neck, M, c):
    h = M("Hair", c, rough=0.5)
    ball("HairCap", (1.3, 1.3, 0.5), Vector((0, -0.03, 1.2)), h, neck)
    for x, y, tilt in ((-0.4, 0.1, -30), (-0.15, 0.2, -12), (0.12, 0.15, 10), (0.38, 0.05, 30),
                       (-0.25, -0.3, -20), (0.2, -0.3, 20), (0, -0.05, 0)):
        rpart("Spike", (0.26, 0.26, 0.7), Vector((x, y, 1.45)), h, neck, r=0.1,
              rot=(math.radians(-15 if y > 0 else 15), math.radians(tilt), 0))


def hair_long(neck, M, c):
    h = M("Hair", c, rough=0.55)
    ball("HairCap", (1.36, 1.36, 0.6), Vector((0, -0.03, 1.18)), h, neck)
    rpart("Bangs", (1.1, 0.25, 0.3), Vector((0, 0.45, 1.02)), h, neck, r=0.12, rot=(math.radians(-12), 0, 0))
    rpart("LongHair", (1.3, 0.4, 1.6), Vector((0, -0.52, 0.45)), h, neck, r=0.18)
    for sx in (-0.62, 0.62):
        rpart("SideHair", (0.18, 0.8, 1.2), Vector((sx, -0.12, 0.55)), h, neck, r=0.08)


def hair_bun(neck, M, c):
    h = M("Hair", c, rough=0.55)
    ball("HairCap", (1.34, 1.34, 0.6), Vector((0, -0.03, 1.18)), h, neck)
    rpart("Bangs", (1.0, 0.22, 0.24), Vector((0, 0.46, 1.06)), h, neck, r=0.1, rot=(math.radians(-12), 0, 0))
    ball("Bun", (0.62, 0.62, 0.55), Vector((0, -0.15, 1.62)), h, neck)


def hair_afro(neck, M, c):
    ball("Afro", (1.9, 1.75, 1.35), Vector((0, -0.12, 1.15)), M("Hair", c, rough=0.9), neck)


def hair_ponytail(neck, M, c):
    h = M("Hair", c, rough=0.55)
    ball("HairCap", (1.34, 1.34, 0.6), Vector((0, -0.03, 1.18)), h, neck)
    rpart("Bangs", (1.05, 0.22, 0.26), Vector((0, 0.46, 1.05)), h, neck, r=0.1, rot=(math.radians(-14), 0, 0))
    rpart("Tail", (0.4, 0.4, 1.3), Vector((0, -0.75, 0.7)), h, neck, r=0.18, rot=(math.radians(-18), 0, 0))
    ball("Tie", (0.34, 0.34, 0.2), Vector((0, -0.66, 1.25)), M("HairTie", (236, 84, 150)), neck)


def hair_pigtails(neck, M, c):
    h = M("Hair", c, rough=0.55)
    ball("HairCap", (1.34, 1.34, 0.6), Vector((0, -0.03, 1.18)), h, neck)
    rpart("Bangs", (1.05, 0.22, 0.26), Vector((0, 0.46, 1.05)), h, neck, r=0.1, rot=(math.radians(-14), 0, 0))
    for sx in (-1, 1):
        ball("Pigtail", (0.45, 0.45, 0.85), Vector((sx * 0.8, -0.1, 0.8)), h, neck, rot=(0, math.radians(sx * 25), 0))


def hair_buzz(neck, M, c):
    ball("Buzz", (1.25, 1.25, 0.34), Vector((0, -0.02, 1.13)), M("Hair", c, rough=0.9), neck)


HAIRS = {"short": hair_short, "spiky": hair_spiky, "long": hair_long, "bun": hair_bun, "afro": hair_afro,
         "ponytail": hair_ponytail, "pigtails": hair_pigtails, "buzz": hair_buzz, "bald": None}


# ---------------------------------------------------------------- hats (sit on hair)
def hat_cap(neck, M, c, back=False):
    m = M("Cap", c, rough=0.55)
    ball("Cap", (1.36, 1.36, 0.72), Vector((0, 0, 1.12)), m, neck)
    rpart("CapBrim", (0.9, 0.62, 0.08), Vector((0, -0.75 if back else 0.75, 1.04)), m, neck, r=0.03)
    disc("CapLogo", 0.26, 0.02, Vector((0, 0.66, 1.25)), mat("PrintWhite", (250, 250, 250)), neck) if not back else None


def hat_beanie(neck, M, c):
    m = M("Beanie", c, rough=0.9)
    ball("Beanie", (1.36, 1.36, 0.95), Vector((0, -0.02, 1.15)), m, neck)
    solid("BeanieCuff", CYL, (1.38, 1.38, 0.26), Vector((0, 0, 1.06)), M("BeanieCuff", shade(c, 0.75)), parent=neck,
          col=COL_CHARS)
    ball("Pom", (0.32, 0.32, 0.32), Vector((0, 0, 1.68)), mat("PrintWhite", (250, 250, 250)), neck)


def hat_crown(neck, M, c):
    solid("CrownBase", CYL, (1.05, 1.05, 0.3), Vector((0, 0, 1.32)), M_BRASS, parent=neck, col=COL_CHARS)
    for a in range(5):
        ang = a * 2 * math.pi / 5
        rpart("CrownPoint", (0.16, 0.16, 0.36), Vector((0.45 * math.sin(ang), 0.45 * math.cos(ang), 1.58)), M_BRASS,
              neck, r=0.06)
    disc("CrownGem", 0.16, 0.05, Vector((0, 0.53, 1.32)), mat("Gem", (214, 40, 70), rough=0.2), neck)


def hat_tophat(neck, M, c):
    m = M("Hat", (18, 18, 22), rough=0.35)
    solid("HatBrim", CYL, (1.75, 1.75, 0.12), Vector((0, 0, 1.25)), m, parent=neck, col=COL_CHARS)
    solid("HatTop", CYL, (1.15, 1.15, 1.3), Vector((0, 0, 1.95)), m, parent=neck, col=COL_CHARS)
    solid("HatBand", CYL, (1.18, 1.18, 0.2), Vector((0, 0, 1.41)), M("HatBand", c), parent=neck, col=COL_CHARS)


def hat_headphones(neck, M, c):
    m = M("Headphones", c, rough=0.35)
    for sx in (-0.62, 0.62):
        disc("HeadphoneCup", 0.55, 0.22, Vector((sx * 1.15, 0, 0.75)), m, neck, axis="X")
    tube("HeadphoneBand", [(-0.78, 0, 0.9), (-0.65, 0, 1.4), (0, 0, 1.58), (0.65, 0, 1.4), (0.78, 0, 0.9)],
         0.06, m, neck)


def hat_bandana(neck, M, c):
    m = M("Bandana", c, rough=0.7)
    solid("Band", CYL, (1.25, 1.25, 0.22), Vector((0, 0, 1.0)), m, parent=neck, col=COL_CHARS)
    rpart("Knot", (0.22, 0.4, 0.4), Vector((0.2, -0.65, 0.85)), m, neck, r=0.06, rot=(math.radians(20), 0, 0))


HATS = {"cap": hat_cap, "backcap": lambda n, M, c: hat_cap(n, M, c, back=True), "beanie": hat_beanie,
        "crown": hat_crown, "tophat": hat_tophat, "headphones": hat_headphones, "bandana": hat_bandana}
HAT_OK = {"cap": {"short", "long", "ponytail", "buzz", "bald", "pigtails"}, "backcap": {"short", "buzz", "bald", "long"},
          "beanie": {"short", "long", "buzz", "bald", "ponytail"}, "crown": set(HAIRS), "tophat": {"short", "buzz", "bald"},
          "headphones": set(HAIRS) - {"afro"}, "bandana": {"short", "spiky", "long", "buzz", "bald", "ponytail"}}


# ---------------------------------------------------------------- face accessories
def glasses(neck, M, c):
    m = M("Glasses", c, rough=0.3)
    for sx in (-0.2, 0.2):
        pts = [(sx + 0.15 * math.cos(a), surf_y(sx) + 0.03, 0.7 + 0.13 * math.sin(a))
               for a in [i * 2 * math.pi / 12 for i in range(13)]]
        tube("Lens", pts, 0.025, m, neck)
    tube("Bridge", [(-0.05, surf_y(0) + 0.03, 0.73), (0.05, surf_y(0) + 0.03, 0.73)], 0.025, m, neck)


# ---------------------------------------------------------------- torso prints / body accessories
def print_stripes(root, M, c, P):
    d = M("Stripe", shade(c, 0.65))
    for z in (2.35, 2.85, 3.35):
        rpart("Stripe", (2.012, 1.012, 0.18), Vector((0, 0, z)), d, root, r=0.02)


def print_jacket(root, M, c, P):
    inner = mat("PrintWhite", (250, 250, 250))
    flat("Inner", (0.62, 1.95), 0, 3.0, inner, root)
    disc("ShirtLogo", 0.3, 0.012, Vector((0, 0.508, 3.15)), M("JLogo", (214, 52, 52)), root)
    for sx in (-0.33, 0.33):
        flat("Zip", (0.05, 1.95), sx, 3.0, M("Zip", shade(c, 0.6)), root)


def print_hoodie(root, M, c, P):
    d = M("ShirtDark", shade(c, 0.75))
    flat("Pocket", (1.2, 0.42), 0, 2.32, d, root)
    flat("CollarV", (0.9, 0.12), 0, 3.92, d, root)
    for sx in (-0.3, 0.3):
        flat("Drawstring", (0.06, 0.42), sx, 3.66, mat("PrintWhite", (250, 250, 250)), root)
    flat("HoodPrint", (1.5, 0.55), 0, 3.6, d, root, back=True)


def print_star(root, M, c, P):
    disc("Star", 0.8, 0.012, Vector((0, 0.508, 3.05)), M("StarPrint", random.choice([(250, 250, 250), (250, 205, 60)])),
         root)
    disc("StarInner", 0.45, 0.014, Vector((0, 0.51, 3.05)), M("StarInner", c), root)


def print_overalls(root, M, c, P):
    o = M("Overalls", (52, 74, 124), rough=0.7)
    flat("Bib", (1.1, 0.9), 0, 2.45, o, root)
    for sx in (-0.55, 0.55):
        flat("Strap", (0.2, 1.1), sx, 3.4, o, root)
        disc("StrapButton", 0.12, 0.02, Vector((sx, 0.51, 2.95)), M_BRASS, root)


def print_tie(root, M, c, P):
    flat("ShirtV", (0.6, 0.95), 0, 3.52, mat("PrintWhite", (250, 250, 250)), root)
    flat("Tie", (0.2, 0.85), 0, 3.45, M("Tie", random.choice(CLOTH)), root)


PRINTS = {"plain": None, "stripes": print_stripes, "jacket": print_jacket, "hoodie": print_hoodie,
          "star": print_star, "overalls": print_overalls, "tie": print_tie}


def acc_backpack(root, M, P):
    m = M("Backpack", random.choice(CLOTH), rough=0.6)
    rpart("Backpack", (1.5, 0.6, 1.6), Vector((0, -0.8, 2.95)), m, root, r=0.15)
    rpart("BackpackPocket", (1.0, 0.2, 0.6), Vector((0, -1.15, 2.55)), M("BPocket", (40, 40, 45)), root, r=0.08)
    for sx in (-0.55, 0.55):
        flat("BPStrap", (0.18, 1.9), sx, 3.0, M("BPStrap", (40, 40, 45)), root)


def acc_scarf(root, M, P):
    m = M("Scarf", random.choice(CLOTH), rough=0.9)
    solid("ScarfRing", CYL, (1.5, 1.2, 0.35), Vector((0, 0, 3.95)), m, parent=root, col=COL_CHARS)
    rpart("ScarfEnd", (0.36, 0.14, 1.0), Vector((0.45, 0.6, 3.4)), m, root, r=0.05)


def acc_chain(root, M, P):
    tube("Chain", [(-0.45, 0.42, 4.02), (-0.2, 0.54, 3.75), (0, 0.56, 3.62), (0.2, 0.54, 3.75), (0.45, 0.42, 4.02)],
         0.035, M_BRASS, root)
    disc("Medal", 0.3, 0.06, Vector((0, 0.58, 3.5)), M_BRASS, root)


def acc_cape(root, M, P):
    m = M("Cape", random.choice([(190, 30, 60), (40, 110, 200), (30, 30, 36), (122, 84, 170)]), rough=0.6)
    rpart("Cape", (2.2, 0.08, 3.3), Vector((0, -0.62, 2.35)), m, root, r=0.03, rot=(math.radians(6), 0, 0))


def acc_sword_back(root, M, P):
    rpart("SwordBlade", (0.2, 0.08, 2.4), Vector((0.2, -0.62, 3.2)), M_METAL, root, r=0.03, rot=(0, math.radians(30), 0))
    rpart("SwordGuard", (0.6, 0.12, 0.12), Vector((-0.4, -0.62, 4.25)), M_BRASS, root, r=0.03, rot=(0, math.radians(30), 0))


ACCS = {"none": None, "backpack": acc_backpack, "scarf": acc_scarf, "chain": acc_chain, "cape": acc_cape,
        "sword": acc_sword_back}


# ---------------------------------------------------------------- held items (right hand)
def held(P, M, item):
    sh = P["Right"]
    sh.rotation_euler = (math.radians(38), 0, 0)
    h = empty("Held", Vector((0, 0.15, -1.5)), col=COL_CHARS, parent=sh)
    h.rotation_euler = (math.radians(-38), 0, 0)
    if item == "phone":
        rpart("Phone", (0.42, 0.08, 0.75), Vector((0, 0.55, 0.1)), mat("PhoneBody", (25, 25, 30)), h, r=0.05)
        rpart("Screen", (0.36, 0.02, 0.62), Vector((0, 0.6, 0.1)), mat("Screen", (120, 200, 255), emit=1.5), h, r=0.02)
    elif item == "flashlight":
        rpart("Torch", (0.24, 0.9, 0.24), Vector((0, 0.7, 0)), mat("TorchBody", (40, 40, 45)), h, r=0.08)
        disc("TorchLens", 0.3, 0.05, Vector((0, 1.17, 0)), mat("TorchLens", (255, 240, 190), emit=4.0), h)
    elif item == "bat":
        rpart("Bat", (0.2, 0.2, 2.0), Vector((0, 0.45, 0.9)), M_WOOD, h, r=0.09)
    elif item == "sword":
        rpart("Grip", (0.16, 0.16, 0.45), Vector((0, 0.45, 0)), mat("Grip", (60, 35, 25)), h, r=0.05)
        rpart("Guard", (0.6, 0.14, 0.12), Vector((0, 0.45, 0.28)), M_BRASS, h, r=0.03)
        rpart("Blade", (0.2, 0.06, 2.0), Vector((0, 0.45, 1.3)), M_METAL, h, r=0.03)
    elif item == "cup":
        solid("Cup", CYL, (0.4, 0.4, 0.55), Vector((0, 0.5, 0.1)), mat("CupWhite", (245, 245, 245)), parent=h,
              col=COL_CHARS)
        solid("Sleeve", CYL, (0.42, 0.42, 0.22), Vector((0, 0.5, 0.08)), mat("Sleeve", (150, 100, 60)), parent=h,
              col=COL_CHARS)
    elif item == "book":
        rpart("Book", (0.7, 0.18, 0.9), Vector((0, 0.5, 0.15)), mat("BookCover", random.choice(CLOTH)), h, r=0.04)
    elif item == "pizza":
        rpart("Pizza", (0.7, 0.05, 0.7), Vector((0, 0.55, 0.1)), mat("Cheese", (250, 200, 80)), h, r=0.02,
              rot=(0, math.radians(45), 0))
        for x, z in ((-0.1, 0.15), (0.12, 0.0), (0.0, -0.15)):
            disc("Pep", 0.14, 0.02, Vector((x, 0.585, z + 0.1)), mat("Pep", (190, 40, 40)), h)
    elif item == "wand":
        rpart("Wand", (0.08, 0.08, 1.0), Vector((0, 0.45, 0.45)), mat("WandBody", (30, 25, 25)), h, r=0.03)
        ball("WandTip", (0.2, 0.2, 0.2), Vector((0, 0.45, 0.98)), mat("WandGlow", (160, 220, 255), emit=6.0), h)


ITEMS = ["none", "phone", "flashlight", "bat", "sword", "cup", "book", "pizza", "wand"]


# ---------------------------------------------------------------- generator
def random_style(rng, faces):
    """Pick a coherent random look. Returns (style dict, description dict)."""
    hair = rng.choice(list(HAIRS))
    hat_opts = [h for h, ok in HAT_OK.items() if hair in ok]
    weights = {"crown": 0.25, "tophat": 0.6}
    pool = hat_opts + ["none"] * 2
    hat = rng.choices(pool, [weights.get(h, 1.0) for h in pool])[0]
    top = rng.choice(CLOTH)
    d = dict(name=rng.choice(NAMES), skin=rng.choice(SKINS), top=top, pants=rng.choice(PANTS),
             hair=hair, hairc=rng.choice(HAIRC), hat=hat, hatc=rng.choice(CLOTH),
             print=rng.choice(list(PRINTS)), acc=rng.choice(list(ACCS) + ["none"]),
             item=rng.choice(ITEMS + ["none"]), glasses=rng.random() < 0.25,
             bare=rng.random() < 0.2, shoe=rng.choice([(248, 248, 248), (30, 30, 36), (214, 52, 52), (110, 80, 55)]))
    return d


def style_from(d, faces):
    def build(neck, root, P):
        M = P["M"]
        if HAIRS[d["hair"]]:
            HAIRS[d["hair"]](neck, M, d["hairc"])
        if d["hat"] != "none":
            HATS[d["hat"]](neck, M, d["hatc"])
        if d["glasses"]:
            glasses(neck, M, (25, 25, 30))
        if PRINTS[d["print"]]:
            PRINTS[d["print"]](root, M, d["top"], P)
        if ACCS[d["acc"]]:
            ACCS[d["acc"]](root, M, P)
        if d["item"] != "none":
            held(P, M, d["item"])
    sole = shade(d["shoe"], 0.6) if d["shoe"] != (248, 248, 248) else (214, 52, 52)
    return dict(skin=d["skin"], top=d["top"], pants=d["pants"], cuff=shade(d["top"], 0.75),
                shoe=d["shoe"], sole=sole, bare_arms=d["bare"], faces=faces, build=[build])
