# recurring.py - FIXED CARDS for recurring characters (approved by Joel 22 Nov 2026).
# Load after the studio library (garments, garments2, hair4, charlib...). Faces come from build_face_v2 (rig2.py), not decals.
# Milo's card lives in rig2.make_milo (approved in Test 2).


def make_rae():
    """RAE: purple hoodie, black X5 two braids, dark jeans, lilac trainers (red notebook is a scene prop)."""
    S = new_set(); skin = (176, 122, 88); rng = RNG(311)
    d_hoodie(S, (122, 84, 170), rng, skin)
    b_trousers(S, (30, 30, 40), rng, kind="jeans")
    for k in LEGS: shoes(S[k], (205, 170, 240), (70, 45, 100))
    finish(S, rng)
    P = build_body("Rae", skin, S)
    add_hair4(P, "X5", random.Random(5), colour=(24, 20, 20))
    return P


def make_mayor():
    """THE MAYOR: dark suit, red tie, grey X1 crop (older man), glasses."""
    S = new_set(); skin = (234, 184, 146); rng = RNG(512)
    d_suit(S, rng, skin, col=(30, 30, 36), tie=(160, 25, 40))
    b_trousers(S, (30, 30, 36), rng, kind="tailored")
    s_shoes(S, "loafers", (15, 15, 18), rng)
    finish(S, rng)
    P = build_body("Mayor", skin, S)
    add_hair4(P, "X1", random.Random(9), colour=(150, 150, 155))
    a_glasses(P)
    return P


RECURRING = {"RAE": make_rae, "MAYOR": make_mayor}   # + MILO: rig2.make_milo
