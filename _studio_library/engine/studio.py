# studio.py - THE STUDIO ASSET LIBRARY (approved assets only).
# Load order inside Blender (after the base helpers from the scene script):
#   charlib -> stylelab -> hair2 -> hair3 -> faces2 -> garments -> garments2 -> hair4 -> faces3 -> faces4 -> props -> studio
# Only what is listed here is approved for episodes. Anything else in the engine files is lab/test material.

STUDIO = {
    "version": "2026-11-22",
    "recurring": ["MILO (rig2.make_milo)", "RAE (recurring.make_rae)", "MAYOR (recurring.make_mayor)", "DAN (recurring.make_dan)", "NEIGHBOUR (recurring.make_neighbour)"],
    "props3": "props3 (Part 2, 22 Nov): toaster, list with Mum crossed off, p3_room/p3_area, SETS p3_kitchen_set, p3_hallway_set, p3_hollow_closet; MUM card in recurring.make_mum",
    "props2": "props2.PROPS2 (hammer, crate, notebook, WHO'S LEFT list insert, newspaper, hollow mug, cafe table, round bin, red-orange door glow)",
    "sets": ["BLOXBURY TOWN (bloxbury_part1.py prefix + trees/lighting; part1_v2 patches Milo's windows to sill 4/top 8)", "MILO'S ROOM (hollow MiloHouse interior: bed, closet with hinge, wall clock 2:59/3:00)"],
    "monsters": ["KNOCKER (monster.make_knocker): keep him in the dark, eyes pop, cool rim for silhouette, faint red underglow"],
    "face_style": "M2",   # midway Classic/Minimal, bright eye shine at 70% opacity
    "face_emotions": ["happy", "laugh", "angry", "sad", "shocked", "smug", "scared", "determined",
                      "crying", "evil", "sleepy", "wink"],
    "rare_faces": ["jaw-drop", "sparkle eyes", "dizzy", "rage", "deadpan", "waterfall sob", "flustered", "creepy grin",
                   "knocked out", "heart eyes", "money eyes", "horror", "cat smug", "side-eye"],
    "hair_women": ["H2", "H3", "H4", "H8"],
    "hair_men": ["M1", "M2", "M3", "M4", "M5", "M6"],
    "hair_extra": ["X1", "X2", "X3", "X4", "X5", "X6"],   # crop+fade, afro, bob, ponytail, braids, top bun
    "hat_hair": True,
    "outfits": ["O1", "O2", "O3", "O4"],
    "outfit_generators": ["fashion", "bakery", "casual", "student", "police", "doctor", "office", "elderly", "builder",
                          "sporty", "kid", "teen"],
    "ages": {"adult": 1.0, "teen": 0.86, "kid": 0.70},
    "props": "props.PROP_LIST (batch 1: 3 vehicles, 11 furniture pieces, 5 small props)",
    "rules": [
        "R6 Roblox body, classic rounded head, printed (textured) clothing with Roblox-style shading",
        "No clipping: hats use under-hat hair, long hair stays in front of/behind the torso, accessories sit outside the body",
        "Darker skin tones never get blonde/very light hair (except the named variants Joel approved)",
        "White/grey hair is for elderly characters",
        "No two identical-looking characters in one shot",
        "Only approved assets in episodes; new assets go through a test sheet + Joel's sign-off first",
        "Never use the downloaded .obj hair (rejected)",
    ],
}

# Ready-made cast. Each entry: (builder, index, light-hair variant?)
CAST = {}
for i in range(6):
    CAST[f"F{i + 1}"] = ("theme", i, False)
    CAST[f"B{i + 1}"] = ("theme", 6 + i, False)
for i in range(24):
    CAST[f"C{i + 1}"] = ("everyday", i, False)
for i in range(12):
    CAST[f"K{i + 1}"] = ("kids", i, False)
# Joel approved BOTH versions of these three: "a" = light hair (before the rule), "b" = dark hair (rule applied)
for tag, (kind, idx, name) in {"B4": ("theme", 9, "Bake3"), "C19": ("everyday", 18, "X18"), "K11": ("kids", 10, "K10")}.items():
    CAST[tag + "a"] = (kind, idx, name)
    CAST[tag + "b"] = (kind, idx, False)
    CAST[tag] = CAST[tag + "b"]


def studio_face(P, emotion="happy", key=None):
    fn = ALL_M2.get(emotion) or RARE.get(emotion)
    add_face(P, key or emotion, fn)


def studio_hair(P, key, rng, colour=None):
    if key in STUDIO["hair_men"]:
        return add_men_hair(P, key, rng, colour)
    if key in STUDIO["hair_women"]:
        return add_hair3(P, key, rng, colour=colour)
    if key in STUDIO["hair_extra"]:
        return add_hair4(P, key, rng, colour=colour)
    raise ValueError(f"hair {key} is not approved for the studio library")


HAIR_POOL = ["H2", "H3", "H4", "H8", "M1", "M2", "M3", "M4", "M5", "M6", "X1", "X2", "X3", "X4", "X5", "X6"]


def make_everyday_cast(N=24, seed=77, only=None):
    """C1..C24 - everyday roles (rebuilds exactly the approved cast)."""
    prng = random.Random(seed); cast = []
    for i in range(N):
        role = ROLES[i % len(ROLES)] if i < len(ROLES) * 2 else prng.choice(ROLES)
        skin = prng.choice(SKIN_POOL)
        S, gear, desc = role_outfit(role, RNG(500 + i), prng, skin)
        P = build_body(f"X{i}", skin, S)
        emo = prng.choice(["happy", "happy", "smug", "determined", "laugh", "wink", "sleepy", "shocked"])
        add_face(P, "f", ALL_M2[emo])
        hatted = apply_gear(P, gear)
        hcol = prng.choice([(200, 200, 205), (236, 236, 240), (150, 150, 155)]) if role == "elderly" else prng.choice(HAIR_COLS)
        if role != "elderly": hcol = HAIR_COLS_YOUNG_FIX.get(hcol, hcol)
        hcol = fix_hair_col(skin, hcol, f"X{i}", elderly=(role == "elderly"))
        hk = prng.choice(["X1", "X3", "X6", "H2"]) if role == "elderly" else prng.choice(HAIR_POOL)
        if hatted: hat_hair(P, hcol, random.Random(i))
        else: studio_hair(P, hk, random.Random(i), colour=hcol)
        cast.append(P)
    return cast


def make_kids_cast(seed=909):
    """K1..K12 - six kids then six teens."""
    prng = random.Random(seed); out = []
    S0, g0, d0 = role_outfit("casual", RNG(9), random.Random(9), (214, 158, 118))   # keeps the RNG stream identical
    hair_k = ["M1", "M3", "M4", "M6", "H3", "H4", "X2", "X3", "X4", "X5", "X6", "X1", "H2"]
    for i in range(12):
        teen = i >= 6
        skin = prng.choice(SKIN_POOL)
        S, gear, desc = kid_outfit(RNG(700 + i), prng, skin, teen=teen)
        P = build_body(f"K{i}", skin, S)
        add_face(P, "f", ALL_M2[prng.choice(["happy", "laugh", "wink", "smug", "shocked", "determined"])])
        apply_gear(P, gear)
        hk = prng.choice(hair_k)
        hcol = HAIR_COLS_YOUNG_FIX.get(prng.choice(HAIR_COLS), None) or prng.choice(HAIR_COLS[:6])
        hcol = fix_hair_col(skin, hcol, f"K{i}")
        studio_hair(P, hk, random.Random(i), colour=hcol)
        set_age(P, "teen" if teen else "kid")
        out.append(P)
    return out


def studio_character(tag):
    """Build one ready-made character by tag, e.g. 'F3', 'B4a', 'C19b', 'K11a'."""
    kind, idx, exempt = CAST[tag]
    if exempt: HAIR_RULE_EXEMPT.add(exempt)
    try:
        if kind == "theme": built = [P for _, P, _ in make_theme_looks(42)]
        elif kind == "everyday": built = make_everyday_cast()
        else: built = make_kids_cast()
    finally:
        HAIR_RULE_EXEMPT.discard(exempt) if exempt else None
    keep = built[idx]
    for P in built:   # remove the others
        if P is not keep:
            for o in [P["root"]] + list(P["root"].children_recursive):
                bpy.data.objects.remove(o, do_unlink=True)
    return keep


def random_extra(name, seed, role=None, age="adult"):
    """A fresh background character mixed from approved parts only (all studio rules applied)."""
    prng = random.Random(seed)
    skin = prng.choice(SKIN_POOL)
    if age in ("kid", "teen"):
        S, gear, desc = kid_outfit(RNG(seed), prng, skin, teen=(age == "teen"))
    else:
        S, gear, desc = role_outfit(role or prng.choice(ROLES), RNG(seed), prng, skin)
    P = build_body(name, skin, S)
    studio_face(P, prng.choice(["happy", "happy", "smug", "determined", "laugh", "wink"]))
    hatted = apply_gear(P, gear)
    elderly = role == "elderly"
    hcol = HAIR_COLS_YOUNG_FIX.get(prng.choice(HAIR_COLS), None) if not elderly else prng.choice([(200, 200, 205), (150, 150, 155)])
    hcol = fix_hair_col(skin, hcol or (60, 40, 30), name, elderly=elderly)
    if hatted: hat_hair(P, hcol, random.Random(seed))
    else: studio_hair(P, prng.choice(HAIR_POOL), random.Random(seed), colour=hcol)
    if age != "adult": set_age(P, age)
    return P
