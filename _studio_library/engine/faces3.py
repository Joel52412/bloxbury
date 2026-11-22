# faces3.py - 4 extra emotions in the approved M2 style (bright shine at 70%)
def _m2_eyes(f, w=0.12, h=0.18, z=0.08):
    for sx in (-0.19, 0.19):
        f.oval(sx, z, w, h, M_INK)
        f.oval(sx + w * 0.24, z + h * 0.26, w * 0.34, h * 0.24, M_SHINE70, lift=0.008)


def M2_crying(f):
    for sx in (-0.19, 0.19):
        f.line([(sx - 0.08, 0.1), (sx, 0.055), (sx + 0.08, 0.1)], M_INK, r=0.026)
        f.oval(sx, -0.08, 0.075, 0.24, M_TEAR, lift=0.004)
    brows(f, [(-0.29, 0.21), (-0.1, 0.28)], [(0.1, 0.28), (0.29, 0.21)], rad=0.022)
    f.oval(0, -0.22, 0.2, 0.12, M_INK); f.oval(0, -0.25, 0.1, 0.04, M_TONGUE, lift=0.008)


def M2_evil(f):
    for sx in (-0.19, 0.19):
        f.oval(sx, 0.05, 0.12, 0.09, M_INK)
        f.oval(sx + 0.03, 0.07, 0.04, 0.03, M_SHINE70, lift=0.008)
    brows(f, [(-0.3, 0.2), (-0.09, 0.11)], [(0.09, 0.11), (0.3, 0.2)], rad=0.03, lift=0.01)
    f.oval(0, -0.17, 0.44, 0.15, M_INK); f.oval(0, -0.15, 0.38, 0.06, M_EYEWHITE, lift=0.008)
    for x in (-0.12, -0.04, 0.04, 0.12):
        f.line([(x, -0.18), (x, -0.12)], M_INK, r=0.01, lift=0.012)


def M2_sleepy(f):
    for sx in (-0.19, 0.19):
        f.line([(sx - 0.08, 0.06), (sx, 0.03), (sx + 0.08, 0.06)], M_INK, r=0.024)
    brows(f, [(-0.28, 0.17), (-0.1, 0.17)], [(0.1, 0.17), (0.28, 0.17)], rad=0.02)
    f.oval(0.03, -0.2, 0.09, 0.11, M_INK)
    f.oval(0.24, -0.12, 0.06, 0.09, M_TEAR, lift=0.004)


def M2_wink(f):
    f.oval(-0.19, 0.08, 0.12, 0.18, M_INK); f.oval(-0.16, 0.13, 0.04, 0.04, M_SHINE70, lift=0.008)
    f.line([(0.11, 0.07), (0.19, 0.12), (0.27, 0.07)], M_INK, r=0.026)
    brows(f, [(-0.28, 0.25), (-0.1, 0.27)], [(0.1, 0.2), (0.28, 0.2)], rad=0.022)
    f.line([(-0.13, -0.15), (0, -0.21), (0.13, -0.15)], M_INK, r=0.024)
    f.oval(0.05, -0.24, 0.1, 0.08, M_TONGUE, lift=0.006)


EXTRA_EMO = {"crying": M2_crying, "evil": M2_evil, "sleepy": M2_sleepy, "wink": M2_wink}
ALL_M2 = dict(zip(EMO2, FACES2["M2"][1])); ALL_M2.update(EXTRA_EMO)
