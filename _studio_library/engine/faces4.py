# faces4.py - "rare" exaggerated reaction faces (gag / shock / horror), original designs in the M2 family
M_RED = mat("AngerRed", (220, 40, 50), rough=0.5)
M_HEART = mat("HeartRed", (232, 50, 80), emit=0.2, rough=0.4)
M_MONEY = mat("MoneyGreen", (40, 170, 70), rough=0.4)
M_GOLD = mat("SparkGold", (255, 214, 70), emit=0.5, rough=0.3)
M_PALE = mat("PaleBlue", (150, 170, 220), rough=0.6)


def spiral(f, cx, z, r=0.1, turns=2.5, m=None):
    pts = []
    for i in range(40):
        t = i / 39; a = t * turns * 2 * math.pi
        pts.append((cx + math.cos(a) * r * t, z + math.sin(a) * r * t * 1.15))
    f.line(pts, m or M_INK, r=0.014)


def sparkle(f, cx, z, s, m):
    f.line([(cx - s, z), (cx + s, z)], m, r=0.014, lift=0.012)
    f.line([(cx, z - s * 1.2), (cx, z + s * 1.2)], m, r=0.014, lift=0.012)
    f.oval(cx, z, s * 0.5, s * 0.5, m, lift=0.014)


def heart(f, cx, z, s, m):
    for dx in (-0.42, 0.42):
        f.oval(cx + dx * s, z + 0.15 * s, s * 0.95, s * 0.9, m)
    f.oval(cx, z - 0.15 * s, s * 0.9, s * 0.8, m)
    f.line([(cx - 0.8 * s, z), (cx, z - 0.85 * s), (cx + 0.8 * s, z)], m, r=s * 0.32)


def dollar(f, cx, z, s, m):
    f.line([(cx + s * 0.5, z + s * 0.7), (cx, z + s * 0.85), (cx - s * 0.5, z + s * 0.45), (cx, z),
            (cx + s * 0.5, z - s * 0.45), (cx, z - s * 0.85), (cx - s * 0.5, z - s * 0.7)], m, r=0.02)
    f.line([(cx, z + s * 1.15), (cx, z - s * 1.15)], m, r=0.016, lift=0.004)


def sweat(f, x, z, s=1.0):
    f.oval(x, z, 0.09 * s, 0.15 * s, M_TEAR, lift=0.004)


def R_jawdrop(f):
    for sx in (-0.17, 0.17): f.oval(sx, 0.2, 0.06, 0.075, M_INK)
    brows(f, [(-0.27, 0.34), (-0.1, 0.37)], [(0.1, 0.37), (0.27, 0.34)], rad=0.02)
    f.oval(0, -0.17, 0.36, 0.4, M_INK)
    f.oval(0, -0.3, 0.22, 0.12, M_TONGUE, lift=0.008)
    f.oval(0, -0.01, 0.24, 0.05, M_EYEWHITE, lift=0.008)


def R_sparkle(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.07, 0.2, 0.26, M_INK)
        sparkle(f, sx + 0.03, 0.1, 0.05, M_EYEWHITE)
        f.oval(sx - 0.05, 0.0, 0.04, 0.04, M_EYEWHITE, lift=0.012)
    for x, z in ((-0.38, 0.3), (0.4, 0.26), (0.36, -0.1)): sparkle(f, x, z, 0.035, M_GOLD)
    f.oval(0, -0.2, 0.22, 0.14, M_INK); f.oval(0, -0.24, 0.12, 0.05, M_TONGUE, lift=0.008)
    for sx in (-0.34, 0.34): f.oval(sx, -0.08, 0.13, 0.06, M_BLUSH, lift=0.002)


def R_dizzy(f):
    for sx in (-0.19, 0.19): spiral(f, sx, 0.08, r=0.1)
    f.line([(-0.15, -0.2), (-0.08, -0.16), (0, -0.21), (0.08, -0.16), (0.15, -0.2)], M_INK, r=0.022)
    f.oval(0.08, -0.25, 0.08, 0.06, M_TONGUE, lift=0.006)
    sweat(f, 0.42, 0.28)


def R_rage(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.05, 0.2, 0.15, M_INK); f.oval(sx, 0.05, 0.16, 0.11, M_EYEWHITE, lift=0.006)
        f.oval(sx + (0.02 if sx < 0 else -0.02), 0.04, 0.04, 0.04, M_INK, lift=0.012)
    brows(f, [(-0.36, 0.25), (-0.06, 0.1)], [(0.06, 0.1), (0.36, 0.25)], rad=0.045, lift=0.02)
    # clenched teeth: outlined white bar, centre line, tooth gaps, corners pulled down
    f.oval(0, -0.2, 0.48, 0.17, M_INK)
    f.oval(0, -0.2, 0.42, 0.12, M_EYEWHITE, lift=0.006)
    f.line([(-0.2, -0.2), (0.2, -0.2)], M_INK, r=0.008, lift=0.012)
    for x in (-0.14, -0.07, 0, 0.07, 0.14):
        f.line([(x, -0.255), (x, -0.145)], M_INK, r=0.007, lift=0.012)
    f.line([(-0.24, -0.2), (-0.29, -0.26)], M_INK, r=0.016); f.line([(0.24, -0.2), (0.29, -0.26)], M_INK, r=0.016)
    for dx, dz in ((-0.035, 0.0), (0.035, 0.0)):   # anger vein mark
        f.line([(0.33 + dx, 0.29), (0.33 + dx * 0.4, 0.34), (0.33 + dx, 0.39)], M_RED, r=0.014)


def R_deadpan(f):
    for sx in (-0.19, 0.19): f.oval(sx, 0.06, 0.055, 0.055, M_INK)
    brows(f, [(-0.27, 0.15), (-0.11, 0.15)], [(0.11, 0.15), (0.27, 0.15)], rad=0.018)
    f.line([(-0.1, -0.2), (0.1, -0.2)], M_INK, r=0.016)


def R_sob(f):
    for sx in (-0.19, 0.19):
        f.line([(sx - 0.09, 0.1), (sx, 0.04), (sx + 0.09, 0.1)], M_INK, r=0.03)
        f.line([(sx, 0.02), (sx * 1.1, -0.15), (sx * 1.15, -0.36)], M_TEAR, r=0.045, lift=0.006)
    brows(f, [(-0.3, 0.2), (-0.1, 0.3)], [(0.1, 0.3), (0.3, 0.2)], rad=0.026)
    f.oval(0, -0.2, 0.3, 0.2, M_INK); f.oval(0, -0.26, 0.16, 0.06, M_TONGUE, lift=0.008)
    f.line([(-0.12, -0.11), (0, -0.13), (0.12, -0.11)], M_EYEWHITE, r=0.012, lift=0.008)


def R_flustered(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.08, 0.17, 0.2, M_EYEWHITE); f.oval(sx, 0.08, 0.05, 0.06, M_INK, lift=0.008)
    for sx in (-0.34, 0.34):
        for k in range(3):
            x = sx - 0.05 + k * 0.05
            f.line([(x - 0.02, -0.12), (x + 0.02, -0.04)], M_HEART, r=0.012, lift=0.003)
    f.line([(-0.13, -0.2), (-0.06, -0.16), (0, -0.2), (0.06, -0.16), (0.13, -0.2)], M_INK, r=0.018)
    sweat(f, -0.42, 0.3, 0.9); sweat(f, 0.44, 0.2, 0.7)


def R_creepy(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.12, 0.17, 0.2, M_EYEWHITE); f.oval(sx, 0.12, 0.035, 0.045, M_INK, lift=0.008)
        f.line([(sx - 0.09, 0.03), (sx, 0.0), (sx + 0.09, 0.03)], M_BAG, r=0.014)
        f.line([(sx - 0.08, 0.255), (sx + 0.08, 0.25)], M_INK, r=0.016)
    # wide crescent grin from cheek to cheek, built from columns (no cover shapes)
    n = 42
    for i in range(n):
        x = -0.37 + 0.74 * i / (n - 1)
        up = -0.12 + 0.11 * (x / 0.37) ** 2
        lo = -0.12 - 0.15 * math.sqrt(max(0.0, 1 - (x / 0.39) ** 2)) + 0.11 * (x / 0.37) ** 2
        f.line([(x, lo), (x, up)], M_INK, r=0.013)
        if abs(x) < 0.33 and i % 4 != 0 and up - lo > 0.06:
            f.line([(x, lo + 0.03), (x, up - 0.012)], M_EYEWHITE, r=0.0105, lift=0.006)


def R_knockout(f):
    for sx in (-0.19, 0.19):
        f.line([(sx - 0.07, 0.15), (sx + 0.07, 0.01)], M_INK, r=0.026)
        f.line([(sx - 0.07, 0.01), (sx + 0.07, 0.15)], M_INK, r=0.026)
    f.line([(-0.12, -0.18), (0.12, -0.18)], M_INK, r=0.02)
    f.oval(0.06, -0.25, 0.1, 0.12, M_TONGUE, lift=0.006)
    for x, z in ((-0.3, 0.42), (0.0, 0.46), (0.3, 0.42)): sparkle(f, x, z, 0.04, M_GOLD)


def R_hearts(f):
    for sx in (-0.19, 0.19): heart(f, sx, 0.08, 0.12, M_HEART)
    f.oval(0, -0.2, 0.22, 0.13, M_INK); f.oval(0, -0.24, 0.12, 0.05, M_TONGUE, lift=0.008)
    for sx in (-0.34, 0.34): f.oval(sx, -0.08, 0.13, 0.06, M_BLUSH, lift=0.002)


def R_money(f):
    for sx in (-0.19, 0.19): dollar(f, sx, 0.08, 0.1, M_MONEY)
    f.oval(0, -0.19, 0.36, 0.14, M_INK); f.oval(0, -0.16, 0.3, 0.05, M_EYEWHITE, lift=0.008)
    f.line([(-0.24, -0.16), (-0.18, -0.1)], M_INK, r=0.014); f.line([(0.24, -0.16), (0.18, -0.1)], M_INK, r=0.014)


def R_horror(f):
    for x in (-0.35, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.35):   # gloom lines over the forehead
        f.line([(x, 0.42), (x, 0.3 - abs(x) * 0.2)], M_PALE, r=0.013)
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.1, 0.2, 0.24, M_INK); f.oval(sx, 0.1, 0.17, 0.21, M_EYEWHITE, lift=0.006)
        f.oval(sx + 0.01, 0.08, 0.03, 0.035, M_INK, lift=0.012)
    brows(f, [(-0.3, 0.27), (-0.08, 0.34)], [(0.08, 0.34), (0.3, 0.27)], rad=0.022, lift=0.016)
    # screaming mouth: tall, top teeth, tongue
    f.oval(0, -0.22, 0.24, 0.3, M_INK)
    f.oval(0, -0.1, 0.17, 0.04, M_EYEWHITE, lift=0.008)
    f.oval(0, -0.32, 0.13, 0.07, M_TONGUE, lift=0.008)
    sweat(f, 0.43, 0.2); sweat(f, -0.44, 0.06, 0.8)


def R_cat(f):
    for sx in (-0.19, 0.19): f.line([(sx - 0.08, 0.05), (sx, 0.12), (sx + 0.08, 0.05)], M_INK, r=0.026)
    f.line([(-0.12, -0.15), (-0.06, -0.2), (0, -0.15), (0.06, -0.2), (0.12, -0.15)], M_INK, r=0.02)
    for sx in (-0.34, 0.34): f.oval(sx, -0.06, 0.13, 0.06, M_BLUSH, lift=0.002)


def R_sideeye(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.07, 0.17, 0.12, M_EYEWHITE); f.oval(sx + 0.055, 0.07, 0.06, 0.09, M_INK, lift=0.008)
        f.line([(sx - 0.1, 0.12), (sx + 0.1, 0.12)], M_INK, r=0.024, lift=0.012)
    brows(f, [(-0.28, 0.2), (-0.1, 0.18)], [(0.1, 0.18), (0.28, 0.2)], rad=0.022)
    f.oval(0.06, -0.2, 0.07, 0.05, M_INK)


RARE = {"jaw-drop": R_jawdrop, "sparkle eyes": R_sparkle, "dizzy": R_dizzy, "rage": R_rage, "deadpan": R_deadpan,
        "waterfall sob": R_sob, "flustered": R_flustered, "creepy grin": R_creepy, "knocked out": R_knockout,
        "heart eyes": R_hearts, "money eyes": R_money, "horror": R_horror, "cat smug": R_cat, "side-eye": R_sideeye}
