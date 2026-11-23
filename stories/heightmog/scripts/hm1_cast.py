# hm1_cast.py - HEIGHT MOG cards (NOT yet approved): KAI + the three short guys (TOP = the "mayor": mustache, top hat;
# MID: glasses, sweater vest; BOT: headband, tank). exec'd after the kit boot + props7 (needs garments, hair, props7).
# Heights (Kai = 1.0): short guys ~0.86, stack ~2.2, average adult ~1.25, tall ~1.5.

KAI_SKIN = (92, 62, 46)


def size_rig(P, bx, bz=None, head=None):
    """Roblox body-width/height scale: root (bx, bx, bz), head kept round at `head` world scale."""
    bz = bz or bx; head = head or bx
    P["root"].scale = (bx, bx, bz)
    P["neck"].scale = (head / bx, head / bx, head / bz)


def make_kai():
    """KAI (4 ft 1): mustard tee with a navy ruler print reading 4'1, teal joggers with a white stripe, coral trainers,
    red backpack, black M2 hair."""
    S = new_set(); rng = RNG(4101)
    d_tee(S, (250, 196, 50), rng, KAI_SKIN)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2; zr = t.zrow(1.05)
    t.d.rectangle((cx - 70, zr - 22, cx + 70, zr + 22), fill=(40, 50, 90))
    for k in range(-60, 61, 15): t.d.line((cx + k, zr - 22, cx + k, zr - (6 if k % 30 else 0)), fill=(250, 196, 50), width=3)
    t.d.text((cx, zr + 10), "4'1", font=pfont(22), fill=(250, 196, 50), anchor="mm")
    b_joggers(S, (40, 170, 170), rng, stripe=(245, 245, 245))
    for k in LEGS: shoes(S[k], (250, 110, 90), (245, 245, 245))
    finish(S, rng)
    P = build_body("Kai", KAI_SKIN, S)
    studio_hair(P, "M2", random.Random(41), colour=(22, 18, 18))
    a_backpack(P, (200, 45, 50))
    set_age(P, "kid")
    return P


GUY_BODY = (0.8, 0.56, 0.8)     # width, height, head  (short + stocky adults)


def make_guy_top():
    """TOP GUY = the mayor's face: purple suit + gold tie, ginger hair, thick handlebar mustache, top hat with a gold band (+ under-hat hair)."""
    S = new_set(); skin = (242, 200, 165); rng = RNG(901)
    d_suit(S, rng, skin, col=(78, 40, 112), tie=(240, 190, 50))
    b_trousers(S, (78, 40, 112), rng, kind="tailored")
    s_shoes(S, "loafers", (15, 15, 18), rng)
    finish(S, rng)
    P = build_body("GuyTop", skin, S)
    hat_hair(P, (150, 60, 40), random.Random(91))      # ginger (matches the mustache)
    hat_tophat(P["neck"], P["M"], (214, 172, 70))
    size_rig(P, *GUY_BODY)
    return P


def make_guy_mid():
    """MID GUY: sky-blue shirt + green sweater vest, round glasses, black crop."""
    S = new_set(); skin = (214, 158, 118); rng = RNG(902)
    d_button_shirt(S, (120, 180, 240), rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front")
    t.d.polygon([(x0 + 10, y1), (x1 - 10, y1), (x1 - 10, t.zrow(1.55)), ((x0 + x1) / 2, t.zrow(1.0)), (x0 + 10, t.zrow(1.55))],
                fill=(60, 140, 80))
    b_trousers(S, (200, 170, 110), rng, kind="chinos")
    s_shoes(S, "trainers", (60, 60, 70), rng)
    finish(S, rng)
    P = build_body("GuyMid", skin, S)
    add_hair4(P, "X1", random.Random(92), colour=(24, 20, 18))
    a_glasses(P)
    size_rig(P, *GUY_BODY)
    return P


def make_guy_bot():
    """BOT GUY: pink tank top, blue joggers, red headband, black afro (he carries everyone, always sweaty)."""
    S = new_set(); skin = (124, 86, 62); rng = RNG(903)
    d_tee(S, (236, 90, 150), rng, skin)
    for k in ("ArmL", "ArmR"):
        if k in S: S[k].band(0.0, 2.0, skin)
    b_joggers(S, (50, 90, 200), rng)
    s_shoes(S, "trainers", (250, 205, 60), rng)
    finish(S, rng)
    P = build_body("GuyBot", skin, S)
    add_hair4(P, "X2", random.Random(93), colour=(24, 20, 18))
    a_headband(P, (210, 40, 45))
    size_rig(P, *GUY_BODY)
    return P


# ------------------------------------------------------------------ the stack (coat on)
STACK_Z = (0.0, 2.55, 5.0)        # root heights of BOT, MID, TOP inside the coat (TOP sits low: suit hidden under the collar)


def build_stack(bot, mid, top, loc=(0, 0, 0), yaw=0.0, shoes=6):
    """Stack root + the three guys parented in + the coat + extra shoes under the hem (one pair backwards).
    Returns dict(root, coat, shoes=[roots]); stack['root'] is what the scene moves."""
    root = empty("Stack", V(loc), col=COL_CHARS); root.rotation_euler = (0, 0, math.radians(yaw))
    for P, z in zip((bot, mid, top), STACK_Z):
        P["root"].parent = root; P["root"].location = V((0, 0, z)); P["root"].rotation_euler = (0, 0, 0)
    coat = hm_coat(root, top)
    extra = []
    pairs = [((-1.25, 0.1), 0), ((1.25, 0.1), 0), ((-1.95, -0.1), 180), ((1.95, -0.1), 180)]   # outer pair faces backwards
    if shoes >= 8: pairs += [((-0.7, -0.8), 20), ((0.7, -0.8), -20)]
    for k, ((x, y), yaw_) in enumerate(pairs[:shoes - 2]):
        extra.append(hm_shoe("XShoe%d" % k, V((x, y, 0)), yaw_, root, col=[(40, 30, 26), (40, 30, 26), (60, 60, 70), (60, 60, 70),
                                                                            (220, 60, 60), (220, 60, 60)][k]))
    return dict(root=root, coat=coat, shoes=extra)
