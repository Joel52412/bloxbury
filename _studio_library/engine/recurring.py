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


def make_dan():
    """DAN (Test 2, approved 22 Nov): light-blue button shirt, chinos, brown trainers, dark X1 crop. Mug: props2.p2_mug."""
    S = new_set(); skin = (196, 140, 104); rng = RNG(77)
    d_button_shirt(S, (118, 160, 214), rng, skin)
    b_trousers(S, (186, 164, 124), rng, kind="chinos")
    s_shoes(S, "trainers", (90, 70, 56), rng)
    finish(S, rng)
    P = build_body("Dan", skin, S)
    add_hair4(P, "X1", random.Random(3), colour=(36, 26, 22))
    return P


def make_neighbour():
    """THE NEIGHBOUR (Part 1, approved 22 Nov): builder - hi-vis over navy tee, grey cargos, boots, yellow hard hat (under-hat hair)."""
    S = new_set(); skin = (124, 86, 62); rng = RNG(733)
    d_hivis(S, rng, skin, under=lambda S_: d_tee(S_, (52, 74, 124), rng, skin))
    b_trousers(S, (60, 60, 66), rng, kind="cargo"); s_shoes(S, "boots", (110, 80, 50), rng)
    finish(S, rng)
    P = build_body("Neighbour", skin, S)
    a_hardhat(P, (250, 200, 30)); hat_hair(P, (24, 20, 20), random.Random(4))
    return P


RECURRING.update({"DAN": make_dan, "NEIGHBOUR": make_neighbour})


def p3_bangle(P, name="Bangle"):
    """Thin gold bangle on the LEFT wrist: rounded-square (superellipse) ring that clears the 1x1 arm block."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = []
    for i in range(48):
        a = 2 * math.pi * i / 48; c, s_ = math.cos(a), math.sin(a)
        r = 0.66 / (abs(c) ** 4 + abs(s_) ** 4) ** 0.25
        vs.append(bm.verts.new((r * c, r * s_, 0)))
    for i in range(48): bm.edges.new((vs[i], vs[(i + 1) % 48]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.parent = P["Left"]; ob.location = (0, 0, -1.18)
    ob.modifiers.new("skin", "SKIN")
    for v in me.skin_vertices[0].data: v.radius = (0.055, 0.055)
    ob.modifiers.new("sub", "SUBSURF").levels = 1
    me.materials.append(pmat("BraceletGold", (222, 176, 70), rough=0.22, metal=1.0))
    return ob


def make_mum(name="Mum"):
    """MUM (Part 2, approved 22 Nov 13:27): Milo's skin tone, long curly brown H4 hair (family look), sage cardigan over a
    cream top, blue jeans, tan flats, gold bangle on her LEFT wrist (proves the closet hand is really her).
    The fake Mum is the SAME card: she's 'wrong' through acting only (held smile, never blinks, no breathing idle)."""
    S = new_set(); skin = (234, 184, 146); rng = RNG(905)
    d_cardigan(S, rng, skin, col=(132, 160, 132), inner=(244, 234, 214))
    b_trousers(S, (58, 78, 120), rng, kind="jeans")
    s_shoes(S, "loafers", (176, 130, 92), rng)
    finish(S, rng)
    P = build_body(name, skin, S)
    add_hair_any(P, "H4", random.Random(21), colour=(92, 60, 38))
    p3_bangle(P, name + "_Bangle")
    return P


RECURRING.update({"MUM": make_mum})
