M_SHINE70 = mat("Shine70", (255, 255, 255), emit=0.6, alpha=0.7)
# faces2.py - "M" styles: midway between Classic (A) and Minimal (D)
def m_eyes(f, w=0.105, h=0.16, z=0.08, dx=0.19, shine=False, look=0.0):
    for sx in (-dx, dx):
        f.oval(sx + look, z, w, h, M_INK)
        if shine:
            f.oval(sx + look + w * 0.24, z + h * 0.26, w * 0.34, h * 0.24, M_SHINE70, lift=0.008)


def mk(shine, big):
    W, H = (0.12, 0.18) if big else (0.105, 0.16)
    E = lambda f, **k: m_eyes(f, w=k.pop("w", W), h=k.pop("h", H), shine=shine, **k)
    R = 0.024

    def happy(f):
        E(f); f.line([(-0.14, -0.15), (-0.05, -0.205), (0.05, -0.205), (0.14, -0.15)], M_INK, r=R)

    def laugh(f):
        for sx in (-0.19, 0.19):
            f.line([(sx - 0.075, 0.05), (sx, 0.125), (sx + 0.075, 0.05)], M_INK, r=0.026)
        f.oval(0, -0.18, 0.26, 0.17, M_INK); f.oval(0, -0.23, 0.13, 0.06, M_TONGUE, lift=0.008)
        f.oval(0, -0.115, 0.18, 0.035, M_EYEWHITE, lift=0.008)

    def angry(f):
        E(f, h=H * 0.82, z=0.06)
        brows(f, [(-0.3, 0.24), (-0.09, 0.15)], [(0.09, 0.15), (0.3, 0.24)], rad=0.028, lift=0.01)
        f.line([(-0.12, -0.21), (0, -0.17), (0.12, -0.21)], M_INK, r=R)

    def sad(f):
        E(f, h=H * 0.9, z=0.06)
        brows(f, [(-0.29, 0.2), (-0.1, 0.27)], [(0.1, 0.27), (0.29, 0.2)], rad=0.022)
        f.line([(-0.11, -0.22), (0, -0.175), (0.11, -0.22)], M_INK, r=R)
        f.oval(0.21, -0.05, 0.055, 0.1, M_TEAR, lift=0.004)

    def shocked(f):
        for sx in (-0.19, 0.19):
            f.oval(sx, 0.08, 0.17, 0.21, M_EYEWHITE); f.oval(sx, 0.08, 0.075, 0.095, M_INK, lift=0.008)
        brows(f, [(-0.28, 0.3), (-0.1, 0.33)], [(0.1, 0.33), (0.28, 0.3)], rad=0.022)
        f.oval(0, -0.2, 0.1, 0.13, M_INK)

    def smug(f):
        for sx in (-0.19, 0.19):
            f.oval(sx, 0.06, W, H * 0.62, M_INK)
            f.line([(sx - 0.075, 0.1), (sx + 0.075, 0.105)], M_INK, r=0.026)
        brows(f, [(-0.28, 0.2), (-0.1, 0.2)], [(0.1, 0.23), (0.28, 0.28)], rad=0.022)
        f.line([(-0.1, -0.18), (0.04, -0.19), (0.15, -0.13)], M_INK, r=R)

    def scared(f):
        for sx in (-0.19, 0.19):
            f.oval(sx, 0.08, 0.16, 0.2, M_EYEWHITE); f.oval(sx - 0.02, 0.07, 0.06, 0.075, M_INK, lift=0.008)
        brows(f, [(-0.29, 0.26), (-0.1, 0.32)], [(0.1, 0.32), (0.29, 0.26)], rad=0.022)
        f.line([(-0.15, -0.2), (-0.075, -0.165), (0, -0.2), (0.075, -0.165), (0.15, -0.2)], M_INK, r=0.02)
        f.oval(0.4, 0.27, 0.08, 0.13, M_TEAR, lift=0.004)

    def determined(f):
        E(f, h=H * 0.9, z=0.07)
        brows(f, [(-0.29, 0.22), (-0.1, 0.18)], [(0.1, 0.18), (0.29, 0.22)], rad=0.028)
        f.line([(-0.12, -0.18), (0.02, -0.2), (0.13, -0.16)], M_INK, r=R)

    return [happy, laugh, angry, sad, shocked, smug, scared, determined]


EMO2 = ["happy", "laugh", "angry", "sad", "shocked", "smug", "scared", "determined"]
FACES2 = {"M1": ("Mid - clean", mk(False, False)), "M2": ("Mid - with shine", mk(True, True))}
M2_happy = FACES2["M2"][1][0]
