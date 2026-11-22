# garments2.py - library expansion batch 1: everyday story cast (casual, school, police, medical,
# office, elderly, construction, sporty) + extra 3D gear. Needs garments.py loaded first.

def d_zip_jacket(S, col, rng, skin, stripe=None, inner=(240, 240, 240), open_=True):
    top_base(S, col, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    if open_:
        t.d.rectangle((cx - 0.2 * PPU, y0, cx + 0.2 * PPU, y1), fill=inner)
        for xx in (cx - 0.2 * PPU, cx + 0.2 * PPU):
            t.d.line((xx, y0, xx, y1), fill=dk(col, 0.6), width=5)
    else:
        t.d.line((cx, y0, cx, y1), fill=(170, 170, 176), width=5)
    t.d.rectangle((0, t.top, t.W, t.top + 22), fill=dk(col, 0.8))
    t.d.rectangle((0, t.mid - 20, t.W, t.mid), fill=dk(col, 0.8))
    if stripe:
        for k in ARMS:   # stripes down the outer sleeve
            a = S[k]; r = "R" if k == "ArmR" else "L"
            x0a, y0a, x1a, y1a = a.reg(r); c = (x0a + x1a) / 2
            for o in (-14, 14):
                a.d.rectangle((c + o - 5, y0a, c + o + 5, a.zrow(0.46)), fill=stripe)


def d_bomber(S, col, rng, skin):
    d_zip_jacket(S, col, rng, skin, open_=False)
    t = S["Torso"]
    for fx in (0.15, 0.62):
        t.d.rectangle((t.fx("front", fx), t.zrow(1.0), t.fx("front", fx + 0.22), t.zrow(0.94)), fill=dk(col, 0.6))
    t.d.rectangle((t.fx("front", 0.66), t.zrow(1.65), t.fx("front", 0.82), t.zrow(1.5)), fill=(214, 120, 40))


def d_denim_jacket(S, rng, skin, col=(70, 110, 170), inner=(245, 245, 245)):
    top_base(S, col, rng, skin)
    for k in TOPS + ARMS: noise(S[k], 10, rng, streak=True)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.rectangle((cx - 0.22 * PPU, y0, cx + 0.22 * PPU, y1), fill=inner)
    collar_flaps(t, dk(col, 0.85), dk(col, 0.5))
    for fx in (0.08, 0.64):
        t.d.rectangle((t.fx("front", fx), t.zrow(1.55), t.fx("front", fx + 0.28), t.zrow(1.25)), outline=(200, 160, 90), width=3)
    for yy in range(int(y0 + 40), int(y1), 46):
        for s in (-1, 1):
            t.d.ellipse((cx + s * 0.28 * PPU - 6, yy - 6, cx + s * 0.28 * PPU + 6, yy + 6), fill=(200, 200, 205))


def d_school(S, rng, skin, blazer=(30, 40, 80), tie=((160, 30, 40), (240, 200, 60))):
    top_base(S, blazer, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 0.26 * PPU, y0), (cx + 0.26 * PPU, y0), (cx + 0.05 * PPU, y0 + 1.15 * PPU),
                 (cx - 0.05 * PPU, y0 + 1.15 * PPU)], fill=(245, 245, 245))
    tx = [(cx - 9, y0 + 18), (cx + 9, y0 + 18), (cx + 12, y0 + 1.05 * PPU), (cx, y0 + 1.15 * PPU), (cx - 12, y0 + 1.05 * PPU)]
    t.d.polygon(tx, fill=tie[0])
    for k in range(4):
        yy = y0 + 30 + k * 30; t.d.line((cx - 10, yy, cx + 10, yy + 10), fill=tie[1], width=5)
    for s in (-1, 1):
        t.d.polygon([(cx + s * 0.26 * PPU, y0), (cx + s * 0.48 * PPU, y0), (cx + s * 0.36 * PPU, y0 + 0.5 * PPU),
                     (cx + s * 0.05 * PPU, y0 + 1.15 * PPU)], fill=dk(blazer, 0.8), outline=dk(blazer, 0.5))
    ex = t.fx("front", 0.66); ey = t.zrow(1.45)
    t.d.polygon([(ex, ey), (ex + 40, ey), (ex + 40, ey + 34), (ex + 20, ey + 48), (ex, ey + 34)], fill=(240, 200, 60),
                outline=(140, 110, 30))
    t.d.ellipse((ex + 13, ey + 10, ex + 27, ey + 24), fill=blazer)


def d_police(S, rng, skin, col=(28, 34, 52)):
    top_base(S, col, rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    collar_flaps(t, dk(col, 0.8), (10, 10, 14)); placket(t, dk(col, 0.7), btn=(30, 30, 30))
    bx = t.fx("front", 0.66); by = t.zrow(1.5)
    t.d.polygon([(bx, by), (bx + 34, by - 6), (bx + 40, by + 24), (bx + 20, by + 44), (bx, by + 24)], fill=(214, 180, 60),
                outline=(120, 100, 30))
    t.d.rectangle((0, t.zrow(0.32), t.W, t.zrow(0.12)), fill=(15, 15, 18))
    t.d.rectangle((cx - 16, t.zrow(0.3), cx + 16, t.zrow(0.14)), fill=(180, 180, 186))
    t.d.text((t.fx("back", 0.22), t.zrow(1.5)), "POLICE", font=font(40), fill=(235, 235, 240))
    for k in ARMS:
        a = S[k]; r = "R" if k == "ArmR" else "L"; xa, ya, xb, yb = a.reg(r)
        for j in range(3):
            a.d.rectangle((xa + 10, a.zrow(1.7 - j * 0.12), xb - 10, a.zrow(1.64 - j * 0.12)),
                          fill=(240, 240, 240) if j % 2 == 0 else (30, 30, 34))


def d_scrubs(S, rng, skin, col=(90, 160, 200)):
    top_base(S, col, rng, skin, sleeve="short")
    t = S["Torso"]; x0, y0, x1, _ = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 0.28 * PPU, y0), (cx + 0.28 * PPU, y0), (cx, y0 + 0.5 * PPU)], fill=skin, outline=dk(col, 0.6))
    t.d.rectangle((t.fx("front", 0.64), t.zrow(1.45), t.fx("front", 0.84), t.zrow(1.2)), outline=dk(col, 0.6), width=3)
    t.d.line((t.fx("front", 0.7), t.zrow(1.45), t.fx("front", 0.7), t.zrow(1.3)), fill=(40, 40, 44), width=4)


def d_labcoat(S, rng, skin, inner_fn=None, col=(246, 246, 246)):
    if inner_fn: inner_fn(S)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    keep = (int(cx - 0.24 * PPU), y0, int(cx + 0.24 * PPU), y1)
    inner = t.img.crop(keep)
    for k in TOPS + ARMS: fill_all(S[k], col)
    folds(t, rng, ["front", "back", "L", "R"], n=8, strength=0.2)
    t.img.paste(inner, keep[:2]); t.d = ImageDraw.Draw(t.img)
    for s in (-1, 1):
        t.d.polygon([(cx + s * 0.24 * PPU, y0), (cx + s * 0.5 * PPU, y0), (cx + s * 0.34 * PPU, y0 + 0.55 * PPU),
                     (cx + s * 0.24 * PPU, y0 + 1.0 * PPU)], fill=(232, 232, 236), outline=(180, 180, 186))
        t.d.line((cx + s * 0.24 * PPU, y0 + 1.0 * PPU, cx + s * 0.24 * PPU, y1), fill=(190, 190, 196), width=4)
    t.d.rectangle((t.fx("front", 0.1), t.zrow(0.5), t.fx("front", 0.3), t.zrow(0.25)), outline=(190, 190, 196), width=3)
    t.d.rectangle((t.fx("front", 0.7), t.zrow(0.5), t.fx("front", 0.9), t.zrow(0.25)), outline=(190, 190, 196), width=3)
    for k in ARMS:
        a = S[k]; folds(a, rng, ["front", "back", "L", "R"], n=3, strength=0.2); hand(a, skin)
    for k in LEGS:   # coat tails down over the thighs
        l = S[k]
        for r in ("front", "back", "R" if k == "LegR" else "L"):
            xa, ya, xb, yb = l.reg(r); l.d.rectangle((xa, ya, xb, l.zrow(1.25)), fill=col)
            l.d.line((xa, l.zrow(1.25), xb, l.zrow(1.25)), fill=(190, 190, 196), width=3)


def d_suit(S, rng, skin, col=(40, 44, 56), tie=(150, 30, 40)):
    d_blazer(S, col, rng, skin, inner=(245, 245, 245))
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 9, y0 + 14), (cx + 9, y0 + 14), (cx + 11, y0 + 1.0 * PPU), (cx, y0 + 1.1 * PPU), (cx - 11, y0 + 1.0 * PPU)],
                fill=tie)


def d_cardigan(S, rng, skin, col=(150, 110, 80), inner=(236, 228, 210)):
    top_base(S, col, rng, skin, knit=True)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.polygon([(cx - 0.3 * PPU, y0), (cx + 0.3 * PPU, y0), (cx + 0.06 * PPU, y0 + 0.9 * PPU), (cx - 0.06 * PPU, y0 + 0.9 * PPU)],
                fill=inner)
    t.d.line((cx, y0 + 0.9 * PPU, cx, y1), fill=dk(col, 0.6), width=4)
    for k in range(4):
        by = y0 + (1.0 + k * 0.24) * PPU
        t.d.ellipse((cx + 8, by - 7, cx + 22, by + 7), fill=(90, 60, 40))


def d_hivis(S, rng, skin, under=None, col=(220, 240, 40)):
    if under: under(S)
    t = S["Torso"]
    for r in ("front", "back", "L", "R"):
        x0, y0, x1, y1 = t.reg(r); t.d.rectangle((x0, y0 + 10, x1, y1), fill=col)
    for z in (0.5, 0.85):
        t.d.rectangle((0, t.zrow(z + 0.1), t.W, t.zrow(z)), fill=(200, 200, 206))
    x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    for s in (-1, 1):
        t.d.rectangle((cx + s * 0.32 * PPU - 10, y0 + 10, cx + s * 0.32 * PPU + 10, t.zrow(0.95)), fill=(200, 200, 206))
    t.d.line((cx, y0 + 10, cx, y1), fill=dk(col, 0.7), width=3)


def d_jersey(S, rng, skin, col, num_col=(245, 245, 245), number=None):
    top_base(S, col, rng, skin, sleeve="short")
    t = S["Torso"]
    n = str(number if number is not None else rng.randint(2, 99))
    f = font(150); x0, y0, x1, y1 = t.reg("back"); tw = t.d.textlength(n, font=f)
    t.d.text(((x0 + x1 - tw) / 2, y0 + 30), n, font=f, fill=num_col)
    f2 = font(44); x0, y0, x1, y1 = t.reg("front"); tw = t.d.textlength(n, font=f2)
    t.d.text((t.fx("front", 0.62), y0 + 34), n, font=f2, fill=num_col)
    for k in ARMS:
        a = S[k]; a.band(1.28, 1.42, num_col, caps=False)


def b_joggers(S, col, rng, stripe=None):
    for k in LEGS:
        l = S[k]; fill_all(l, col)
        folds(l, rng, ["front", "back", "L", "R"], n=4, strength=0.3, ang=(-70, 70), length=(0.1, 0.2), width=5)
        l.band(0.4, 0.58, dk(col, 0.8), caps=False)
        if stripe:
            r = "R" if k == "LegR" else "L"; x0, y0, x1, y1 = l.reg(r); c = (x0 + x1) / 2
            for o in (-14, 14):
                l.d.rectangle((c + o - 5, y0, c + o + 5, l.zrow(0.6)), fill=stripe)
        edge_shade(l, 0.22)


def b_school_skirt(S, rng, skin, col=(60, 60, 70)):
    b_trousers(S, col, rng, kind="skirt", skin=skin)
    for k in LEGS:
        l = S[k]; l.band(0.42, 0.62, (245, 245, 245), caps=False)


# ---------------------------------------------------------------- 3D gear
def a_stethoscope(P):
    m = mat("Stetho", (30, 30, 34), rough=0.4)
    tube("StethoTube", [(-0.5, 0.42, 4.02), (-0.42, 0.54, 3.7), (-0.25, 0.56, 3.3), (0, 0.56, 3.15), (0.25, 0.56, 3.3),
                        (0.42, 0.54, 3.7), (0.5, 0.42, 4.02)], 0.03, m, P["root"])
    disc("StethoBell", 0.2, 0.06, V((0.25, 0.6, 3.3)), M_METAL, P["root"])


def a_lanyard(P, col=(40, 90, 200)):
    m = mat("Lanyard" + str(col), col, rough=0.6)
    for s in (-1, 1):
        lock(P["root"], [V((s * 0.4, 0.42, 4.02)), V((s * 0.3, 0.54, 3.7)), V((s * 0.08, 0.56, 3.25)), V((0, 0.56, 3.1))],
             0.08, 0.012, m, n=12, wpow=8, center=lambda p: V((0, -0.6, p.z)))
    rpart("IDCard", (0.32, 0.03, 0.42), V((0, 0.57, 2.85)), mat("IDCard", (245, 245, 245)), P["root"], r=0.02)
    rpart("IDPhoto", (0.12, 0.035, 0.14), V((-0.06, 0.575, 2.92)), mat("IDPhoto", (120, 160, 210)), P["root"], r=0.01)


def a_hardhat(P, col=(250, 200, 30)):
    m = P["M"]("HardHat", col, rough=0.35)
    ball("HardHat", (1.42, 1.48, 0.86), V((0, 0, 1.18)), m, P["neck"])
    rpart("HatBrim", (1.5, 1.7, 0.06), V((0, 0.05, 0.98)), m, P["neck"], r=0.03)
    rpart("HatRidge", (0.16, 1.2, 0.12), V((0, 0, 1.6)), m, P["neck"], r=0.05)


def a_policecap(P):
    n = P["neck"]; navy = P["M"]("PCap", (24, 28, 44), rough=0.5)
    solid("PCapBand", CYL, (1.3, 1.3, 0.3), V((0, 0, 1.22)), mat("PCapCheck", (230, 230, 230)), parent=n, col=COL_CHARS)
    ball("PCapTop", (1.5, 1.55, 0.4), V((0, -0.02, 1.42)), navy, n)
    rpart("PCapPeak", (1.0, 0.5, 0.06), V((0, 0.72, 1.12)), mat("PCapPeak", (10, 10, 12), rough=0.2), n, r=0.03,
          rot=(math.radians(14), 0, 0))
    disc("PCapBadge", 0.22, 0.04, V((0, 0.66, 1.3)), mat("PBadge", (214, 180, 60), metallic=0.8, rough=0.3), n)


def a_headband(P, col):
    solid("Headband", CYL, (1.24, 1.24, 0.14), V((0, 0, 1.0)), P["M"]("Headband", col), parent=P["neck"], col=COL_CHARS)


def a_backpack(P, col):
    root = P["root"]
    rpart("Backpack", (1.5, 0.6, 1.6), V((0, -0.82, 2.95)), P["M"]("Backpack", col, rough=0.6), root, r=0.15)
    rpart("BPPocket", (1.0, 0.2, 0.6), V((0, -1.16, 2.55)), P["M"]("BPPocket", dk(col, 0.7)), root, r=0.08)
    for s in (-1, 1):
        rpart("BPStrap", (0.22, 0.06, 1.8), V((s * 0.55, 0.53, 3.05)), P["M"]("BPStrapF", (40, 40, 44)), root, r=0.02)
        rpart("BPStrapTop", (0.22, 1.1, 0.06), V((s * 0.55, -0.02, 4.02)), P["M"]("BPStrapT", (40, 40, 44)), root, r=0.02)


# ---------------------------------------------------------------- role builders
CASUAL_COLS = [(214, 52, 52), (40, 110, 200), (52, 150, 82), (30, 30, 36), (240, 240, 240), (122, 84, 170),
               (250, 205, 60), (90, 90, 100), (236, 120, 160), (40, 170, 170), (230, 140, 60), (150, 90, 50)]


def role_outfit(role, rng, prng, skin):
    S = new_set(); gear = []; desc = [role]
    C = lambda: prng.choice(CASUAL_COLS)
    if role == "casual":
        kind = prng.choice(["tee", "hoodie", "zip", "bomber", "denim", "sweater", "shirt"])
        if kind == "tee": d_tee(S, C(), rng, skin, text=prng.choice([None, None, "CHILL", "NO.7", "WAVES", "OK"]))
        elif kind == "hoodie": d_hoodie(S, C(), rng, skin)
        elif kind == "zip": d_zip_jacket(S, C(), rng, skin, stripe=(245, 245, 245) if prng.random() < 0.5 else None, inner=C())
        elif kind == "bomber": d_bomber(S, prng.choice([(60, 80, 50), (30, 30, 36), (120, 30, 40)]), rng, skin)
        elif kind == "denim": d_denim_jacket(S, rng, skin, inner=C())
        elif kind == "sweater": d_sweater(S, C(), rng, skin, stripe=prng.choice([None, (245, 245, 245)]))
        else: d_button_shirt(S, C(), rng, skin, pattern=prng.choice([None, lambda t: pat_plaid(t, None, (30, 30, 36), size=34)]))
        desc.append(kind)
        bot = prng.choice(["jeans", "jeans", "joggers", "cargo", "shorts", "chinos", "skirt"])
        if bot == "joggers": b_joggers(S, prng.choice([(30, 30, 36), (90, 90, 100), (40, 50, 90)]), rng, stripe=prng.choice([None, (245, 245, 245)]))
        else: b_trousers(S, prng.choice([(52, 74, 124), (34, 44, 82), (120, 150, 190), (30, 30, 36), (196, 170, 120), (90, 90, 100)]),
                         rng, kind=bot, skin=skin)
        s_shoes(S, prng.choice(["trainers", "trainers", "boots"]), prng.choice([(245, 245, 245), (30, 30, 36), (214, 52, 52)]), rng)
        if prng.random() < 0.3: gear.append(("backpack", C()))
        if prng.random() < 0.2: gear.append(("headphones", C()))
    elif role == "student":
        d_school(S, rng, skin, blazer=prng.choice([(30, 40, 80), (20, 60, 40), (90, 20, 30), (30, 30, 36)]))
        if prng.random() < 0.5: b_trousers(S, (70, 70, 78), rng, kind="tailored")
        else: b_school_skirt(S, rng, skin)
        s_shoes(S, "loafers", (20, 20, 24), rng); gear.append(("backpack", C()))
    elif role == "police":
        d_police(S, rng, skin); b_trousers(S, (22, 26, 40), rng, kind="tailored"); s_shoes(S, "boots", (15, 15, 18), rng)
        gear.append(("policecap", None))
    elif role == "doctor":
        if prng.random() < 0.5:
            d_labcoat(S, rng, skin, inner_fn=lambda S_: d_button_shirt(S_, prng.choice([(200, 220, 245), (245, 245, 245)]), rng, skin))
            b_trousers(S, (40, 44, 56), rng, kind="tailored"); desc.append("lab coat")
        else:
            c = prng.choice([(90, 160, 200), (70, 150, 120), (110, 90, 170)])
            d_scrubs(S, rng, skin, col=c); b_joggers(S, c, rng); desc.append("scrubs")
        s_shoes(S, prng.choice(["trainers", "clogs"]), (245, 245, 245), rng); gear += [("stethoscope", None), ("lanyard", (40, 90, 200))]
    elif role == "office":
        if prng.random() < 0.5: d_suit(S, rng, skin, col=prng.choice([(40, 44, 56), (60, 60, 66), (30, 30, 36), (50, 60, 90)]),
                                       tie=prng.choice([(150, 30, 40), (40, 80, 150), (60, 120, 80)])); desc.append("suit")
        else: d_button_shirt(S, prng.choice([(245, 245, 245), (200, 220, 245), (235, 220, 230)]), rng, skin); desc.append("shirt")
        b_trousers(S, prng.choice([(40, 44, 56), (60, 60, 66), (30, 30, 36)]), rng, kind="tailored")
        s_shoes(S, "loafers", prng.choice([(20, 20, 24), (90, 60, 40)]), rng)
        if prng.random() < 0.6: gear.append(("lanyard", prng.choice([(40, 90, 200), (200, 40, 50)])))
    elif role == "elderly":
        if prng.random() < 0.6: d_cardigan(S, rng, skin, col=prng.choice([(150, 110, 80), (120, 60, 70), (80, 90, 110), (170, 160, 140)]))
        else: d_sweater(S, prng.choice([(120, 60, 70), (80, 90, 110), (170, 160, 140)]), rng, skin)
        b_trousers(S, prng.choice([(120, 110, 100), (70, 70, 78), (150, 140, 120)]), rng, kind="chinos")
        s_shoes(S, "loafers", (90, 60, 40), rng); gear.append(("glasses", None))
    elif role == "builder":
        d_hivis(S, rng, skin, under=lambda S_: d_tee(S_, prng.choice([(90, 90, 100), (30, 30, 36), (52, 74, 124)]), rng, skin))
        b_trousers(S, prng.choice([(60, 60, 66), (52, 74, 124)]), rng, kind="cargo"); s_shoes(S, "boots", (110, 80, 50), rng)
        gear.append(("hardhat", prng.choice([(250, 200, 30), (245, 245, 245), (230, 120, 30)])))
    elif role == "sporty":
        if prng.random() < 0.5:
            c = C(); d_zip_jacket(S, c, rng, skin, stripe=(245, 245, 245), open_=False); b_joggers(S, c, rng, stripe=(245, 245, 245)); desc.append("tracksuit")
        else:
            c = C(); d_jersey(S, rng, skin, c, number=prng.randint(2, 99)); b_trousers(S, dk(c, 0.5), rng, kind="shorts", skin=skin); desc.append("jersey")
        s_shoes(S, "trainers", prng.choice([(245, 245, 245), (30, 30, 36)]), rng)
        if prng.random() < 0.4: gear.append(("headband", C()))
    finish(S, rng)
    return S, gear, desc


ROLES = ["casual", "casual", "casual", "student", "police", "doctor", "office", "elderly", "builder", "sporty"]


def apply_gear(P, gear):
    hatted = False
    for g, c in gear:
        if g == "backpack": a_backpack(P, c)
        elif g == "headphones": hat_headphones(P["neck"], P["M"], c)
        elif g == "policecap": a_policecap(P); hatted = True
        elif g == "stethoscope": a_stethoscope(P)
        elif g == "lanyard": a_lanyard(P, c)
        elif g == "glasses": a_glasses(P)
        elif g == "hardhat": a_hardhat(P, c); hatted = True
        elif g == "headband": a_headband(P, c)
    return hatted


# ---------------------------------------------------------------- ages: kids & teens
AGE = {"adult": (1.0, 1.0), "teen": (0.86, 0.95), "kid": (0.7, 0.88)}


def set_age(P, age):
    body, head = AGE[age]
    P["root"].scale = (body, body, body)
    k = head / body
    P["neck"].scale = (k, k, k)
    P["age"] = age


HAIR_COLS_YOUNG_FIX = {(236, 236, 240): (110, 74, 44)}
KID_COLS = [(250, 80, 80), (60, 140, 240), (70, 200, 110), (255, 200, 40), (180, 110, 240), (255, 140, 60),
            (60, 210, 210), (250, 120, 180), (245, 245, 245), (40, 40, 50)]


def b_overalls(S, rng, col=(70, 110, 170)):
    b_trousers(S, col, rng, kind="jeans")
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.rectangle((cx - 0.55 * PPU, t.zrow(1.0), cx + 0.55 * PPU, y1), fill=col)
    t.d.rectangle((cx - 0.3 * PPU, t.zrow(0.85), cx + 0.3 * PPU, t.zrow(0.55)), outline=dk(col, 0.6), width=4)
    for s_ in (-1, 1):
        t.d.rectangle((cx + s_ * 0.45 * PPU - 12, y0, cx + s_ * 0.45 * PPU + 12, t.zrow(1.0)), fill=col)
        t.d.ellipse((cx + s_ * 0.45 * PPU - 10, t.zrow(1.0) - 10, cx + s_ * 0.45 * PPU + 10, t.zrow(1.0) + 10), fill=(214, 180, 60))
    bx0, by0, bx1, by1 = t.reg("back"); bc = (bx0 + bx1) / 2
    t.d.line((bc - 0.45 * PPU, by0, bc + 0.3 * PPU, t.zrow(0.6)), fill=col, width=24)
    t.d.line((bc + 0.45 * PPU, by0, bc - 0.3 * PPU, t.zrow(0.6)), fill=col, width=24)
    t.d.rectangle((0, t.zrow(0.35), t.W, t.mid), fill=col)


def kid_outfit(rng, prng, skin, teen=False):
    S = new_set(); gear = []; desc = []
    C = lambda: prng.choice(KID_COLS if not teen else CASUAL_COLS)
    kind = prng.choice(["tee", "tee", "hoodie", "sweater", "zip", "school"] if not teen else ["hoodie", "hoodie", "tee", "zip", "bomber", "denim", "school"])
    if kind == "tee": d_tee(S, C(), rng, skin, text=prng.choice([None, "RAWR", "GAME ON", "8", "SPACE"] if not teen else [None, "CHILL", "NO.7", "WAVES"]),
                           text_col=(30, 30, 36))
    elif kind == "hoodie": d_hoodie(S, C(), rng, skin)
    elif kind == "sweater": d_sweater(S, C(), rng, skin, stripe=prng.choice([(245, 245, 245), (255, 200, 40), None]))
    elif kind == "zip": d_zip_jacket(S, C(), rng, skin, stripe=(245, 245, 245), inner=C())
    elif kind == "bomber": d_bomber(S, prng.choice([(60, 80, 50), (30, 30, 36), (120, 30, 40)]), rng, skin)
    elif kind == "denim": d_denim_jacket(S, rng, skin, inner=C())
    else: d_school(S, rng, skin, blazer=prng.choice([(30, 40, 80), (20, 60, 40), (90, 20, 30)]))
    desc.append("school uniform" if kind == "school" else kind)
    if kind == "school":
        if prng.random() < 0.5: b_trousers(S, (70, 70, 78), rng, kind="tailored")
        else: b_school_skirt(S, rng, skin)
        s_shoes(S, "loafers", (20, 20, 24), rng); gear.append(("backpack", C()))
    else:
        bot = prng.choice(["jeans", "shorts", "joggers", "overalls"] if not teen else ["jeans", "jeans", "joggers", "cargo", "shorts"])
        if bot == "overalls" and kind in ("tee", "sweater"): b_overalls(S, rng)
        elif bot == "joggers": b_joggers(S, prng.choice([(30, 30, 36), (90, 90, 100), (40, 50, 90)]), rng, stripe=(245, 245, 245))
        else: b_trousers(S, prng.choice([(52, 74, 124), (120, 150, 190), (30, 30, 36), (90, 90, 100)]), rng,
                         kind="jeans" if bot == "overalls" else bot, skin=skin)
        desc.append(bot)
        s_shoes(S, "trainers", C(), rng)
        if prng.random() < 0.4: gear.append(("backpack", C()))
        if teen and prng.random() < 0.3: gear.append(("headphones", C()))
    finish(S, rng)
    return S, gear, desc
