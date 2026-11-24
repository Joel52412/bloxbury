# rs_cast.py - RESPAWN cards (fixed recurring characters) + Lanternfall extras. exec'd after boot + load("props4",
# "studio", "lookdev") (needs garments, garments2, hair, stylelab, props).
#   THEO    teen lead: charcoal hoodie with a small red respawn-ring print, jeans, white trainers, brown skin, dark M3.
#   WREN    teen lamplighter's apprentice: bottle-green coat with brass buttons + belt, cream collar, braids (auburn),
#           brown satchel (flap + buckle + strap), brass-tipped lighting pole (held prop).
#   BRAMBLE apple merchant: rolled-sleeve cream shirt, green apron with an apple patch, brown breeches, boots, flat
#           cap + under-cap hair, mustache, stocky.
#   ASHBY   butler (only gloves, shoes and a smile in Part 1): black tailcoat, grey tie, WHITE GLOVES (3D cuffs),
#           polished shoes, grey hair (older).
#   THIEF   hooded cloak (back view / silhouette only).
#   lf_extra(name, seed): medieval townsfolk mixed from approved parts (tunic, belt, apron/hood, breeches, boots).
TEEN = "teen"


def size_rig(P, bx, bz=None, head=None):
    """Roblox body-width/height scale: root (bx, bx, bz), head kept round at `head` world scale."""
    bz = bz or bx; head = head or bx
    P["root"].scale = (bx, bx, bz)
    P["neck"].scale = (head / bx, head / bx, head / bz)


def belt(S, col=(70, 46, 30), buckle=(196, 150, 70), z=0.28):
    t = S["Torso"]; t.band(z - 0.08, z + 0.08, col, caps=False)
    x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.rectangle((cx - 18, t.zrow(z + 0.1), cx + 18, t.zrow(z - 0.1)), outline=buckle, width=6)


def make_theo():
    S = new_set(); skin = (176, 122, 88); rng = RNG(3001)
    d_hoodie(S, (58, 60, 68), rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2; zr = t.zrow(1.25)
    t.d.ellipse((cx - 26, zr - 26, cx + 26, zr + 26), outline=(214, 44, 44), width=7)     # tiny respawn-ring print
    t.d.ellipse((cx - 9, zr - 9, cx + 9, zr + 9), fill=(214, 44, 44))
    b_trousers(S, (52, 74, 112), rng, kind="jeans")
    for k in LEGS: shoes(S[k], (238, 238, 240), (210, 210, 214), lace=(200, 200, 206))
    finish(S, rng)
    P = build_body("Theo", skin, S)
    studio_hair(P, "X1", random.Random(31), colour=(34, 24, 20))     # crop + fade: eyes always readable
    set_age(P, TEEN)
    return P


def make_wren():
    S = new_set(); skin = (242, 200, 165); rng = RNG(3002); coat = (38, 84, 64)
    top_base(S, coat, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 0.3 * PPU, y0), (cx + 0.3 * PPU, y0), (cx, y0 + 0.45 * PPU)], fill=(232, 220, 196))        # cream collar
    t.d.line((cx + 10, y0 + 0.4 * PPU, cx + 10, y1), fill=dk(coat, 0.55), width=4)
    for k in range(5):
        by = y0 + (0.55 + k * 0.28) * PPU
        t.d.ellipse((cx - 22, by - 8, cx - 6, by + 8), fill=(214, 172, 70), outline=(120, 90, 40))
    belt(S, (92, 60, 36))
    for k in ARMS:
        a = S[k]; a.band(0.34, 0.5, dk(coat, 0.7), caps=False)                                      # turned-back cuffs
    b_trousers(S, (70, 56, 46), rng, kind="tailored")
    s_shoes(S, "boots", (60, 40, 28), rng)
    finish(S, rng)
    P = build_body("Wren", skin, S)
    studio_hair(P, "X5", random.Random(32), colour=(150, 64, 34))
    set_age(P, TEEN)
    # satchel on the left hip, strap over the right shoulder
    lea = P["M"]("Satchel", (122, 78, 44), rough=0.7); led = P["M"]("SatchelDk", (86, 54, 30), rough=0.75)
    root = P["root"]
    rpart("Satchel", (0.5, 1.2, 1.0), V((-1.12, 0.05, 2.3)), lea, root, r=0.12)
    rpart("SatchelFlap", (0.12, 1.22, 0.62), V((-1.4, 0.05, 2.55)), led, root, r=0.05)
    rpart("SatchelBuckle", (0.06, 0.26, 0.2), V((-1.47, 0.05, 2.4)), P["M"]("Brass", (196, 150, 70), rough=0.3, metallic=0.9), root, r=0.02)
    rpart("SatchelStrap", (0.2, 0.06, 2.9), V((0.0, 0.53, 3.2)), led, root, r=0.02, rot=(0, math.radians(-38), 0))
    rpart("SatchelStrapB", (0.2, 0.06, 2.9), V((0.0, -0.53, 3.2)), led, root, r=0.02, rot=(0, math.radians(38), 0))
    return P


def lighting_pole(name="WrenPole"):
    """Lamplighter's pole: long ash shaft, brass hook + wick cup at the top, leather grip wrap. Origin at the grip."""
    r = empty(name, V((0, 0, 0)), col=COL_PROPS)
    rcyl(name + "Shaft", 0.09, 9.0, V((0, 0, 2.6)), wood("lf_ash", (176, 140, 96), scale=6.0, rough=0.6), r, seg=10)
    rcyl(name + "Grip", 0.12, 1.0, V((0, 0, 0)), dmat("lf_grip", (86, 54, 30), rough=0.8), r, seg=10)
    br = dmat("lf_brass", (196, 150, 70), rough=0.3, metal=0.9)
    rcyl(name + "Ferrule", 0.13, 0.4, V((0, 0, 7.1)), br, r, seg=10)
    rb(name + "Hook", (0.08, 0.08, 0.9), V((0.22, 0, 7.6)), br, r, r=0.02, rot=(0, math.radians(30), 0))
    rcyl(name + "Cup", 0.18, 0.3, V((-0.05, 0, 7.5)), br, r, seg=10, top_scale=1.4)
    return r


def make_bramble():
    S = new_set(); skin = (234, 184, 146); rng = RNG(3003)
    top_base(S, (232, 222, 196), rng, skin, sleeve="short")
    for k in ARMS: S[k].band(1.28, 1.45, (214, 204, 180), caps=False)                                # rolled sleeves
    o_apron(S, (64, 104, 62), rng)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2; zr = t.zrow(0.9)
    t.d.ellipse((cx - 22, zr - 20, cx + 22, zr + 22), fill=(196, 40, 40)); t.d.line((cx, zr - 20, cx + 6, zr - 34), fill=(70, 48, 30), width=5)
    b_trousers(S, (110, 76, 50), rng, kind="chinos")
    s_shoes(S, "boots", (70, 46, 30), rng)
    finish(S, rng)
    P = build_body("Bramble", skin, S)
    hat_hair(P, (110, 74, 44), random.Random(33))
    a_flatcap(P, (96, 84, 70))
    m = P["M"]("Stache", (100, 66, 40), rough=0.8); fy = surf_y(0) + 0.03
    for s_ in (-1, 1): rpart("Stache", (0.36, 0.1, 0.13), V((s_ * 0.17, fy, 0.47)), m, P["neck"], r=0.05, rot=(0, math.radians(s_ * -14), 0))
    size_rig(P, 1.12, 1.0, 1.04)
    return P


def make_ashby():
    S = new_set(); rng = RNG(3004)
    d_suit(S, rng, (248, 248, 246), col=(24, 24, 28), tie=(96, 96, 104))            # hands drawn white = gloves
    b_trousers(S, (24, 24, 28), rng, kind="tailored")
    s_shoes(S, "loafers", (10, 10, 12), rng)
    finish(S, rng)
    P = build_body("Ashby", (230, 196, 170), S)
    studio_hair(P, "X1", random.Random(34), colour=(186, 186, 190))
    wm = P["M"]("Glove", (250, 250, 248), rough=0.55)
    for side in ("Left", "Right"):
        rpart("GloveCuff", (1.06, 1.06, 0.22), V((0, 0, -1.2)), wm, P[side], r=0.06)
    gl = P["M"]("ShoeGloss", (8, 8, 10), rough=0.08)
    for x in (-0.5, 0.5): rpart("ShoeToe", (1.02, 0.5, 0.3), V((x, 0.3, 0.14)), gl, P["root"], r=0.12)
    return P


def make_thief():
    S = new_set(); skin = (214, 158, 118); rng = RNG(3005); cl = (54, 44, 40)
    top_base(S, cl, rng, skin); belt(S, (30, 24, 20))
    b_trousers(S, (40, 34, 30), rng); s_shoes(S, "boots", (30, 24, 20), rng)
    finish(S, rng)
    P = build_body("Thief", skin, S)
    m = P["M"]("Hood", cl, rough=0.9)
    ball("Hood", (1.42, 1.45, 1.5), V((0, -0.1, 0.7)), m, P["neck"])
    rpart("Cloak", (2.3, 0.3, 3.6), V((0, -0.65, 2.4)), m, P["root"], r=0.12)
    return P


TUNICS = [(120, 70, 50), (70, 90, 120), (110, 120, 70), (150, 120, 80), (130, 60, 70), (90, 70, 110), (60, 100, 90), (170, 150, 110)]


def lf_extra(name, seed, age="adult"):
    """Lanternfall townsperson: tunic (+ collar lacing), belt, maybe apron / hood / cap, breeches, boots, studio hair."""
    prng = random.Random(seed); rng = RNG(5000 + seed)
    skin = prng.choice(SKIN_POOL); col = prng.choice(TUNICS)
    S = new_set(); top_base(S, col, rng, skin, sleeve=prng.choice(("long", "long", "short")))
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 16, y0), (cx + 16, y0), (cx, y0 + 0.5 * PPU)], fill=dk(col, 0.6))
    for k in range(3): t.d.line((cx - 12, y0 + 12 + k * 18, cx + 12, y0 + 22 + k * 18), fill=(220, 200, 160), width=3)
    belt(S, prng.choice(((70, 46, 30), (40, 30, 24))))
    if prng.random() < 0.35: o_apron(S, prng.choice(((220, 210, 190), (120, 100, 80), (150, 60, 50))), rng)
    b_trousers(S, prng.choice(((90, 70, 50), (70, 70, 74), (110, 90, 60), (60, 50, 44))), rng, kind="tailored")
    s_shoes(S, "boots", prng.choice(((60, 40, 28), (40, 30, 24))), rng)
    finish(S, rng)
    P = build_body(name, skin, S)
    studio_face(P, prng.choice(["happy", "happy", "smug", "determined", "laugh", "wink"]))
    hcol = fix_hair_col(skin, prng.choice(HAIR_COLS[:6]), name)
    if prng.random() < 0.3:
        hat_hair(P, hcol, random.Random(seed)); a_flatcap(P, prng.choice(((96, 84, 70), (60, 70, 90), (120, 60, 50))))
    else:
        studio_hair(P, prng.choice(HAIR_POOL), random.Random(seed), colour=hcol)
    if age != "adult": set_age(P, age)
    return P
