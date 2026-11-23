# props6.py - PART 3 "Don't Say It" assets (NEW, awaiting Joel's approval). Load after props4.py / props5.py.
# Bedroom door detail + light gap + shadow feet, the note (two handwritings) + pencil, the LIGHTHOUSE crayon drawing,
# a side sash window in Milo's room (patched into the house wall by the scene script), the loose-picket fence gap,
# Rae's front door + hall set (night), her torch and phone. Cheap rules: bevelled boxes, shared materials,
# emission glows, ONE practical per set, no glass/volumes. Every picture/screen/label is a generated image.
import math, random
from mathutils import Vector as _V6

import os as _os6
_FD = next((d for d in ("/workspace/bloxbury/assets/fonts", "/home/claude/bloxbury/assets/fonts") if _os6.path.isdir(d)), ".")   # fonts ship in the repo (pods)
F_KID = _FD + "/ComicRelief-Bold.ttf"
F_MUM = _FD + "/Gelasio-Italic.ttf"
F_UI = _FD + "/Poppins-Bold.ttf"


def _font(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def _wobbly(d, im, xy, text, font, fill, seed=0, jitter=(3, 5), rot=6):
    """Hand-lettered text: every letter drawn on its own, with a small random lift and tilt."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seed); x, y = xy
    for ch in text:
        if ch == " ": x += font.size * 0.4; continue
        w = int(font.getlength(ch)) + 12; L = Image.new("RGBA", (w, font.size + 24), (0, 0, 0, 0))
        ImageDraw.Draw(L).text((6, 6), ch, font=font, fill=fill)
        L = L.rotate(rnd.uniform(-rot, rot), resample=Image.BICUBIC, expand=False)
        im.alpha_composite(L, (int(x), int(y + rnd.uniform(-jitter[1], jitter[1]))))
        x += font.getlength(ch) + rnd.uniform(-1, jitter[0])
    return x


# ------------------------------------------------------------------ generated images
def note_imgs(front="/tmp/p6_note_front.png", back="/tmp/p6_note_back.png"):
    """Torn notebook page. Front: LIGHTHOUSE in Milo's shaky pencil capitals. Back: Mum's neat ink, WINDOW. RAE'S. GO."""
    from PIL import Image, ImageDraw
    out = []
    for path, kind in ((front, "kid"), (back, "mum")):
        W, H = 520, 680; im = Image.new("RGBA", (W, H), (248, 245, 232, 255)); d = ImageDraw.Draw(im)
        rnd = random.Random(7 if kind == "kid" else 8)
        for y in range(90, H, 46): d.line((0, y, W, y), fill=(170, 195, 225, 255), width=2)          # ruled lines
        d.line((70, 0, 70, H), fill=(230, 150, 150, 255), width=2)                                      # margin
        for y in range(0, H, 9): d.rectangle((0, y, rnd.randint(4, 12), y + 9), fill=(0, 0, 0, 0))      # torn edge
        for k in range(3): d.ellipse((20, 120 + k * 210, 42, 142 + k * 210), fill=(0, 0, 0, 0))         # punch holes
        if kind == "kid":
            _wobbly(d, im, (88, 250), "LIGHT", _font(F_KID, 118), (70, 70, 78, 255), seed=3)
            _wobbly(d, im, (100, 380), "HOUSE", _font(F_KID, 118), (70, 70, 78, 255), seed=4)
            for k in range(3): d.line((96 + k * 4, 520, 420 - k * 9, 516 + k * 3), fill=(90, 90, 98, 255), width=4)   # underlined hard
        else:
            f = _font(F_MUM, 80)
            for i, t in enumerate(("WINDOW.", "RAE'S.", "GO.")):
                _wobbly(d, im, (90, 150 + i * 150), t, f, (25, 40, 110, 255), seed=10 + i, jitter=(0.5, 1.5), rot=1.5)
            d.line((100, 610, 300, 604), fill=(25, 40, 110, 255), width=4)
        im.save(path); out.append(path)
    return out


def lighthouse_drawing_img(path="/tmp/p6_drawing.png"):
    """Crayon drawing: sea, hill, a red/white lighthouse throwing a yellow beam, Milo + Mum holding hands.
    Rewatch bait: the secret word is written small INSIDE the beam (L I G H T H O U S E)."""
    from PIL import Image, ImageDraw
    W, H = 600, 440; im = Image.new("RGBA", (W, H), (252, 250, 243, 255)); d = ImageDraw.Draw(im); rnd = random.Random(21)

    def crayon(poly_or_box, col, kind="poly", n=60):
        # scribbly fill: many short strokes inside the shape's bbox, clipped by a mask
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        (md.polygon if kind == "poly" else md.ellipse)(poly_or_box, fill=255)
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        bb = m.getbbox() or (0, 0, 1, 1)
        for k in range(n):
            y = rnd.uniform(bb[1], bb[3]); ld.line((bb[0] - 10, y + rnd.uniform(-8, 8), bb[2] + 10, y + rnd.uniform(-8, 8)),
                                                   fill=col + (rnd.randint(170, 235),), width=rnd.randint(5, 9))
        im.paste(L, (0, 0), Image.composite(L, Image.new("RGBA", (W, H)), m))
    crayon([(0, 300), (W, 280), (W, H), (0, H)], (70, 120, 200), n=40)                    # sea
    crayon([(0, 330), (120, 230), (300, 250), (380, 340), (380, H), (0, H)], (90, 170, 80), n=50)   # hill
    crayon([(180, 92), (232, 92), (246, 262), (166, 262)], (235, 235, 235), n=30)         # tower
    for k in range(4): crayon([(170 + k * 1.5, 110 + k * 40), (240 - k * 1.5, 110 + k * 40), (243 - k * 1.5, 130 + k * 40), (168 + k * 1.5, 130 + k * 40)], (210, 50, 50), n=12)
    crayon([(176, 60), (236, 60), (232, 92), (180, 92)], (250, 220, 70), n=14)            # lamp room
    crayon([(170, 60), (206, 22), (242, 60)], (200, 50, 50), n=14)                        # cap
    crayon([(236, 64), (W, 0), (W, 130), (236, 86)], (255, 230, 90), n=26)                # beam
    f = _font(F_KID, 22)
    for i, ch in enumerate("LIGHTHOUSE"):                                                 # hidden word, pale orange, inside the beam
        d.text((262 + i * 31, 66 - i * 3.4 + (i % 2) * 3), ch, font=f, fill=(225, 150, 60, 255))
    for x, c, h in ((430, (60, 90, 200), 1.0), (480, (200, 60, 120), 1.25)):              # Milo + Mum, holding hands
        y0 = 300 - int(60 * h)
        d.ellipse((x - 14, y0 - 28, x + 14, y0), outline=c, width=4); d.line((x, y0, x, y0 + 40 * h), fill=c, width=4)
        d.line((x, y0 + 40 * h, x - 12, y0 + 62 * h), fill=c, width=4); d.line((x, y0 + 40 * h, x + 12, y0 + 62 * h), fill=c, width=4)
        d.line((x - 22, y0 + 14, x + 22, y0 + 14), fill=c, width=4)
    _wobbly(d, im, (404, 335), "ME + MUM", _font(F_KID, 30), (40, 40, 50, 255), seed=9)
    d.ellipse((30, 26, 96, 92), outline=(250, 200, 60, 255), width=6)                     # sun... no: a moon (night beam)
    im.save(path); return path


def phone_screen_img(path="/tmp/p6_phone.png", name="Milo", time="3:47"):
    """Incoming-call screen: time, 'incoming call', a Roblox-head avatar, the caller's name, decline/accept."""
    from PIL import Image, ImageDraw
    W, H = 360, 760; im = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for y in range(H): d.line((0, y, W, y), fill=(int(20 + 30 * y / H), int(24 + 20 * y / H), int(52 + 40 * y / H), 255))
    d.text((W / 2, 70), time, font=_font(F_UI, 54), fill=(240, 240, 250), anchor="mm")
    d.text((W / 2, 175), "incoming call", font=_font(F_UI, 22), fill=(170, 180, 210), anchor="mm")
    d.ellipse((W / 2 - 70, 220, W / 2 + 70, 360), fill=(90, 110, 170))
    d.rounded_rectangle((W / 2 - 38, 250, W / 2 + 38, 330), 14, fill=(255, 214, 170))         # Milo's head
    d.rectangle((W / 2 - 40, 244, W / 2 + 40, 268), fill=(95, 60, 35))
    for ex in (-15, 15): d.ellipse((W / 2 + ex - 5, 282, W / 2 + ex + 5, 294), fill=(20, 20, 20))
    d.arc((W / 2 - 14, 296, W / 2 + 14, 316), 200, 340, fill=(20, 20, 20), width=3)
    d.text((W / 2, 410), name, font=_font(F_UI, 56), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 462), "mobile", font=_font(F_UI, 22), fill=(170, 180, 210), anchor="mm")
    for x, c in ((W * 0.27, (230, 60, 60)), (W * 0.73, (60, 200, 100))):
        d.ellipse((x - 42, 610, x + 42, 694), fill=c)
    d.text((W * 0.27, 652), "x", font=_font(F_UI, 40), fill=(255, 255, 255), anchor="mm")
    d.polygon([(W * 0.73 - 14, 636), (W * 0.73 + 18, 652), (W * 0.73 - 14, 668)], fill=(255, 255, 255))
    im.save(path); return path


def sign_img(path, text, bg=(240, 220, 160), fg=(60, 40, 30), size=60, seed=1):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (420, 220), bg + (255,)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 412, 212), 18, outline=fg + (255,), width=6)
    y = 40
    for t in text.split("\n"):
        f = _font(F_KID, size); _wobbly(d, im, ((420 - f.getlength(t)) / 2, y), t, f, fg + (255,), seed=seed, rot=4); y += size + 14
    im.save(path); return path


def mat_img(path, text="HOME", bg=(120, 85, 55), fg=(200, 160, 110)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (480, 300), bg); d = ImageDraw.Draw(im); rnd = random.Random(3)
    for k in range(1600):
        x, y = rnd.randint(0, 479), rnd.randint(0, 299); d.point((x, y), fill=tuple(c + rnd.randint(-18, 18) for c in bg))
    d.rectangle((14, 14, 466, 286), outline=fg, width=8)
    d.text((240, 150), text, font=_font(F_UI, 110), fill=fg, anchor="mm")
    im.save(path); return path


# ------------------------------------------------------------------ props (local builds, then placed)
def p6_note(name="Note", loc=(0, 0, 0), rot=(0, 0, 0), crease=8.0):
    """The note: a torn page folded once (two halves meet at a shallow crease), front + back images on separate faces."""
    fr, bk = note_imgs()
    r = root_of(name, _V6(loc)); r.rotation_euler = rot
    mf, mb = imgmat(name + "Front", fr, rough=0.9), imgmat(name + "Back", bk, rough=0.9)
    w, h = 1.1, 1.42
    # lying face-up: plane faces +Y, rotate 90 on X so it faces +Z
    plane(name + "F", w, h, _V6((0, 0, 0.012)), mf, r, rot=(math.radians(90), 0, 0))
    plane(name + "B", w, h, _V6((0, 0, 0.004)), mb, r, rot=(-math.radians(90), 0, math.radians(180)))
    r["front"] = r.children[0].name
    return r


def p6_pencil(name="Pencil", loc=(0, 0, 0), rot=(0, 0, 0), L=1.3):
    """Hex yellow pencil: painted hex body, bare wood cone, graphite tip, metal ferrule with a groove, pink eraser, a chew mark."""
    r = root_of(name, _V6(loc)); r.rotation_euler = rot
    rcyl(name + "Body", 0.055, L * 0.72, _V6((0, 0, 0)), dmat("pencilY", (240, 190, 40), rough=0.45), r, axis="X", seg=6, bevel=0.006)
    rcyl(name + "Wood", 0.055, L * 0.12, _V6((L * 0.42, 0, 0)), dmat("pencilWood", (226, 190, 140), rough=0.8), r, axis="X", seg=12, bevel=0.0, top_scale=0.28)
    rcyl(name + "Lead", 0.016, L * 0.04, _V6((L * 0.5, 0, 0)), dmat("graphite", (50, 50, 55), rough=0.3, metal=0.4), r, axis="X", seg=8, bevel=0.0, top_scale=0.2)
    rcyl(name + "Ferrule", 0.06, L * 0.08, _V6((-L * 0.4, 0, 0)), dmat("ferrule", (190, 190, 180), metal=0.8, rough=0.35), r, axis="X", seg=16, bevel=0.01)
    rcyl(name + "Groove", 0.062, 0.012, _V6((-L * 0.4, 0, 0)), dmat("ferruleD", (120, 120, 115), metal=0.8, rough=0.4), r, axis="X", seg=16, bevel=0.0)
    rcyl(name + "Eraser", 0.054, L * 0.07, _V6((-L * 0.475, 0, 0)), dmat("eraser", (240, 140, 150), rough=0.8), r, axis="X", seg=16, bevel=0.02)
    rb(name + "Chew", (0.08, 0.02, 0.03), _V6((-L * 0.3, 0, 0.05)), dmat("pencilChew", (200, 150, 30), rough=0.6), r, r=0.008)
    return r


def p6_drawing(name="Drawing", loc=(0, -49, 0.4), n=(0, 1, 0), z=6.8, w=3.0):
    """Taped-up crayon drawing on a wall: page, four strips of masking tape, one corner curling off the wall."""
    path = lighthouse_drawing_img(); h = w * 440 / 600
    r = wall_root(name, loc, n)
    plane(name + "P", w, h, _V6((0, -0.03, z)), imgmat(name + "Img", path, rough=0.85), r, rot=(0, 0, math.pi))
    tape = dmat("tape", (236, 222, 170), rough=0.7)
    for sx, sz, a in ((-1, 1, 30), (1, 1, -30), (-1, -1, -30)):
        rb(name + "Tape", (0.5, 0.02, 0.16), _V6((sx * (w / 2 - 0.1), -0.045, z + sz * (h / 2 - 0.06))), tape, r, r=0.005, rot=(0, math.radians(a), 0))
    # bottom-right corner peeled forward (no tape): a small folded triangle, back side plain paper
    curl = rb(name + "Curl", (0.42, 0.012, 0.42), _V6((w / 2 - 0.2, -0.16, z - h / 2 + 0.2)), dmat("paperback", (236, 232, 222), rough=0.9), r, r=0.004,
              rot=(math.radians(-28), math.radians(45), 0))
    return r


def p6_bedroom_door(door, name="BDoor"):
    """Inside face of Milo's door (the front-wall door, inside face at y=-30.7): raised panels, frame trim, knob + rose,
    a brass slide bolt SHUT (he locked it), scuffed kick plate, a hand-made sign on a string, dressing gown on a hook."""
    c = door.matrix_world.translation; y = c.y - 0.21                     # inside face of the door slab
    r = root_of(name, _V6((c.x, y, 0.4)))
    wd = dmat("doorPanel", (150, 104, 68), rough=0.6); trim = dmat("doorTrim", (236, 232, 222), rough=0.5)
    for dx in (-1.15, 1.15):
        for z0, hh in ((1.2, 2.9), (4.8, 3.0)):
            rb(name + "Pnl", (1.7, 0.08, hh), _V6((dx, -0.03, z0 + hh / 2)), wd, r, r=0.05)
    rb(name + "TrimL", (0.45, 0.22, 9.3), _V6((-2.75, -0.05, 4.65)), trim, r, r=0.04)
    rb(name + "TrimR", (0.45, 0.22, 9.3), _V6((2.75, -0.05, 4.65)), trim, r, r=0.04)
    rb(name + "TrimT", (6.0, 0.22, 0.45), _V6((0, -0.05, 9.2)), trim, r, r=0.04)
    brass = dmat("brassK", (200, 168, 80), metal=0.85, rough=0.3)
    rcyl(name + "Rose", 0.26, 0.06, _V6((1.9, -0.08, 4.1)), brass, r, axis="Y", seg=20)
    rcyl(name + "Knob", 0.2, 0.32, _V6((1.9, -0.26, 4.1)), brass, r, axis="Y", seg=20, bevel=0.08)
    rb(name + "Keyhole", (0.08, 0.02, 0.2), _V6((1.9, -0.1, 3.65)), dmat("keyhole", (20, 18, 16)), r, r=0.01)
    # slide bolt (the working part): plate on the door, keeper on the frame, bolt SHOT across into the keeper
    rb(name + "BoltPlate", (0.9, 0.05, 0.32), _V6((2.1, -0.06, 5.9)), brass, r, r=0.03)
    rb(name + "Bolt", (1.05, 0.1, 0.12), _V6((2.55, -0.14, 5.9)), brass, r, r=0.04)
    rb(name + "BoltKnob", (0.1, 0.22, 0.1), _V6((2.25, -0.25, 5.97)), brass, r, r=0.04)
    rb(name + "Keeper", (0.3, 0.16, 0.42), _V6((3.0, -0.12, 5.9)), brass, r, r=0.03)
    rb(name + "Kick", (4.2, 0.05, 0.7), _V6((0, -0.04, 0.42)), dmat("kick", (110, 110, 112), metal=0.6, rough=0.55), r, r=0.02)
    for k, (dx, a) in enumerate(((-1.1, 20), (0.4, -12), (1.4, 8))):
        rb(name + "Scuff", (0.5, 0.01, 0.06), _V6((dx, -0.07, 0.35 + 0.15 * k)), dmat("scuff", (60, 60, 62), rough=0.9), r, r=0.002, rot=(0, math.radians(a), 0))
    sg = sign_img("/tmp/p6_sign.png", "MILO'S ROOM\nKNOCK FIRST", seed=2)
    rb(name + "Nail", (0.08, 0.2, 0.08), _V6((0, -0.08, 8.25)), dmat("nail", (80, 80, 84), metal=0.7), r, r=0.02)
    for sx in (-1, 1): rb(name + "String", (0.04, 0.02, 0.62), _V6((sx * 0.36, -0.11, 7.95)), dmat("string", (230, 230, 220)), r, r=0.01, rot=(0, math.radians(-sx * 40), 0))
    plane(name + "Sign", 1.6, 0.84, _V6((0, -0.12, 7.25)), imgmat(name + "SignImg", sg, rough=0.8), r, rot=(0, 0, math.pi))
    rb(name + "SignBack", (1.64, 0.04, 0.88), _V6((0, -0.095, 7.25)), dmat("card", (200, 170, 120)), r, r=0.01)
    # dressing gown on a hook (left of the knob side) - soft blue, belt hanging
    rb(name + "Hook", (0.12, 0.3, 0.12), _V6((-1.6, -0.15, 7.6)), brass, r, r=0.04)
    taper(name + "Gown", (1.3, 0.5, 3.6), _V6((-1.6, -0.38, 5.7)), dmat("gown", (90, 120, 170), rough=0.95), r, top=(0.45, 0.8), r=0.18)
    rb(name + "Belt", (0.12, 0.08, 1.6), _V6((-1.3, -0.65, 4.4)), dmat("gownBelt", (70, 95, 140), rough=0.95), r, r=0.04)
    return r


def p6_light_gap(door, name="Gap", floor_z=0.4, width=4.6, gap=0.38):
    """Warm light under the door. The door slab is lifted so there is a REAL gap; outside, a warm glow card lights it.
    Someone standing there = two soft feet blocking the glow (seen only as dark notches in the gap) and two shadows
    baked INTO the floor light: they fan out from the door and soften with distance, like real penumbra (Joel 22:08:
    no black blocks). Swap with feet(on). Returns dict(root, card, feet, spill, spill_feet, on)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    c = door.matrix_world.translation; top = c.z + door.dimensions.z / 2
    door.location.z += gap / 2; door.scale.z *= (top - floor_z - gap) / door.dimensions.z   # bottom now at floor + gap
    W, H = 512, 256; PW = width + 2.0; ppu = W / PW
    base = Image.new("L", (W, H), 0); d = ImageDraw.Draw(base)
    for k in range(64):                                                    # fan: brightest at the door, fading into the room
        a = int(255 * (1 - k / 64) ** 1.6)
        d.polygon([(70 - k * 1.5, k * 4), (W - 70 + k * 1.5, k * 4), (W - 70 + k * 1.6, k * 4 + 4), (70 - k * 1.6, k * 4 + 4)], fill=a)
    base = base.filter(ImageFilter.GaussianBlur(5))
    sh = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sh)
    for fx in (-0.62, 0.62):                                               # each shoe's shadow: narrow at the door, wider + softer inside
        x0 = W / 2 + fx * ppu; hw = 0.36 * ppu; spread = fx * ppu * 0.55
        sd.polygon([(x0 - hw, 0), (x0 + hw, 0), (x0 + hw * 1.9 + spread, H), (x0 - hw * 1.9 + spread, H)], fill=255)
    near = sh.filter(ImageFilter.GaussianBlur(3)); far = sh.filter(ImageFilter.GaussianBlur(16))
    ramp = Image.linear_gradient("L").resize((W, H))                       # 0 at the door -> 255 deep in the room
    shadow = Image.composite(far, near, ramp)
    dark = shadow.point(lambda v: int(v * 0.82))
    feet_alpha = ImageChops.subtract(base, ImageChops.multiply(base, dark))
    for path, alpha in (("/tmp/p6_spill.png", base), ("/tmp/p6_spill_feet.png", feet_alpha)):
        im = Image.new("RGBA", (W, H), (255, 190, 120, 0)); im.putalpha(alpha); im.save(path)
    r = root_of(name, _V6((c.x, c.y, floor_z)))
    card = rb(name + "Card", (width + 0.6, 0.06, 1.2), _V6((0, 0.9, 0.6)), dmat("gapGlow", (255, 196, 130), emit=9.0, emit_rgb=(255, 190, 120)), r, r=0.01)
    out = {"root": r, "card": card, "feet": []}
    for key, path in (("spill", "/tmp/p6_spill.png"), ("spill_feet", "/tmp/p6_spill_feet.png")):
        pl = plane(name + key, PW, 3.2, _V6((0, -0.21 - 1.6, 0.008)), imgmat(name + key + "M", path, rough=1.0, emit=2.2), r, rot=(math.radians(90), 0, math.pi))
        pl.visible_shadow = False; out[key] = pl
    shoe = dmat("shoeShadow", (22, 18, 16), rough=1.0)
    for x in (-0.62, 0.62):                                                # trainers outside: rounded toes, only their bottoms show in the gap
        out["feet"].append(rb(name + "Shoe", (0.62, 1.0, 0.5), _V6((x, 0.42, 0.25)), shoe, r, r=0.2))
        out["feet"].append(rb(name + "Toe", (0.6, 0.4, 0.36), _V6((x, -0.02, 0.18)), shoe, r, r=0.17))
    return out


def gap_feet(G, on, fr=None):
    """Someone outside (on) / nobody (off). With fr, keys the swap on the timeline."""
    for o, vis in [(o, on) for o in G["feet"]] + [(G["spill_feet"], on), (G["spill"], not on)]:
        o.hide_render = not vis
        if fr is not None: o.keyframe_insert("hide_render", frame=fr)


def p6_side_window(name="SideWin", x_in=11.0, yc=-35.5, sill=4.4, w=4.0, h=4.0, open_u=0.0):
    """Sash window on Milo's right wall (opening cut by the scene script): frame + trim, upper fixed sash,
    LOWER SASH SLIDES UP (open_u 0..1) with lift handles, a turned sash lock, sill with a toy robot + plant, curtains."""
    r = root_of(name, _V6((x_in, yc, 0)))
    fw = dmat("winFrame", (240, 238, 232), rough=0.45); sash = dmat("winSash", (232, 230, 224), rough=0.4)
    for dy in (-w / 2 - 0.18, w / 2 + 0.18):
        rb(name + "Jamb", (0.9, 0.36, h + 0.7), _V6((-0.2, dy, sill + h / 2)), fw, r, r=0.05)
    rb(name + "Head", (0.9, w + 0.72, 0.36), _V6((-0.2, 0, sill + h + 0.18)), fw, r, r=0.05)
    rb(name + "Sill", (1.3, w + 1.2, 0.3), _V6((-0.45, 0, sill - 0.15)), fw, r, r=0.06)
    rb(name + "Apron", (0.2, w + 0.6, 0.6), _V6((-0.08, 0, sill - 0.6)), fw, r, r=0.04)
    rb(name + "UTop", (0.2, w, 0.25), _V6((0.15, 0, sill + h - 0.12)), sash, r, r=0.03)          # upper sash = frame, open pane (no glass)
    rb(name + "UMeet", (0.2, w, 0.2), _V6((0.15, 0, sill + h / 2 + 0.1)), sash, r, r=0.03)
    up = root_of(name + "Lower", (0, 0, 0)); up.parent = r; up.location = (-0.05, 0, sill + h * 0.25 + open_u * h * 0.45)
    r["lower"] = up.name
    for dy in (-w / 2 + 0.1, w / 2 - 0.1): rb(name + "LStile", (0.18, 0.2, h / 2), _V6((0, dy, 0)), sash, up, r=0.03)
    rb(name + "LRailT", (0.2, w, 0.22), _V6((0, 0, h / 4 - 0.11)), sash, up, r=0.03)
    rb(name + "LRailB", (0.2, w, 0.3), _V6((0, 0, -h / 4 + 0.15)), sash, up, r=0.03)
    rb(name + "LMuntin", (0.12, 0.1, h / 2), _V6((0, 0, 0)), sash, up, r=0.02)
    for dy in (-w / 2 + 0.1, w / 2 - 0.1): rb(name + "UStile", (0.18, 0.2, h / 2), _V6((0.15, dy, sill + h * 0.75)), sash, r, r=0.03)
    rb(name + "UMuntin", (0.12, 0.1, h / 2), _V6((0.15, 0, sill + h * 0.75)), sash, r, r=0.02)
    brass = dmat("brassK", (200, 168, 80), metal=0.85, rough=0.3)
    for dy in (-1.1, 1.1): rb(name + "Lift", (0.18, 0.4, 0.12), _V6((-0.22, dy, -h / 4 + 0.15)), brass, up, r=0.04)
    rb(name + "Lock", (0.16, 0.5, 0.1), _V6((-0.05, 0.3, h / 4 + 0.02)), brass, up, r=0.03, rot=(0, 0, math.radians(35)))  # turned open
    # sill life: toy robot (boxes) + a little cactus
    rb(name + "Bot", (0.5, 0.45, 0.6), _V6((-0.55, -1.4, sill + 0.3)), dmat("bot", (200, 70, 60), rough=0.4), r, r=0.08)
    rb(name + "BotHead", (0.4, 0.36, 0.34), _V6((-0.55, -1.4, sill + 0.78)), dmat("botH", (210, 210, 215), metal=0.5, rough=0.35), r, r=0.08)
    rb(name + "BotEye", (0.04, 0.22, 0.07), _V6((-0.76, -1.4, sill + 0.8)), glow("botEye", (120, 220, 255), 3.0), r, r=0.02)
    rcyl(name + "Pot", 0.26, 0.4, _V6((-0.55, 1.4, sill + 0.2)), dmat("pot", (190, 100, 60), rough=0.8), r, seg=14, top_scale=1.15)
    rcyl(name + "Cactus", 0.16, 0.6, _V6((-0.55, 1.4, sill + 0.7)), dmat("cactus", (80, 150, 80), rough=0.7), r, seg=10, bevel=0.1)
    # curtains: three soft folds each side, tied back
    cur = dmat("curtain", (70, 80, 130), rough=0.95)
    for side in (-1, 1):
        for k in range(3):
            rb(name + "Fold", (0.35, 0.62, h + 1.6), _V6((-0.55 - 0.08 * (k % 2), side * (w / 2 + 0.55 + k * 0.42), sill + h / 2 + 0.2)), cur, r, r=0.16)
        rb(name + "Tie", (0.5, 1.5, 0.2), _V6((-0.72, side * (w / 2 + 0.95), sill + 0.9)), dmat("tie", (220, 190, 90)), r, r=0.06)
    rcyl(name + "Rod", 0.07, w + 4.2, _V6((-0.6, 0, sill + h + 0.85)), dmat("rod", (40, 40, 44), metal=0.6), r, axis="Y", seg=10)
    return r


def p6_fence_gap(x=25.0, ys=(-36.0, -38.0), name="FenceGap"):
    """Hide two pickets (Milo's secret gap to Rae's) and lay one in the grass, a nail still in it."""
    gone = []
    for o in bpy.data.objects:
        if o.name.startswith("Picket") and abs(o.location.x - x) < 0.5 and any(abs(o.location.y - y) < 0.5 for y in ys):
            o.hide_render = True; o.hide_viewport = True; gone.append(o)
    for o in bpy.data.objects:                                            # lower rail: split, leaving a snapped gap
        if o.name.startswith("Rail") and abs(o.location.x - x) < 0.5 and abs(o.location.z - 1.5) < 0.3 and not o.hide_render:
            o.hide_render = True; o.hide_viewport = True; gone.append(o)
            y0, y1 = o.location.y - o.dimensions.y / 2, o.location.y + o.dimensions.y / 2; g0, g1 = min(ys) - 1.3, max(ys) + 1.3
            for a, b in ((y0, g0), (g1, y1)):
                rb(name + "Rail", (0.3, b - a, 0.5), _V6((x, (a + b) / 2, 1.5)), dmat("fenceW", (245, 245, 240), rough=0.7), None, r=0.03)
            rb(name + "Stub", (0.3, 1.1, 0.5), _V6((x, g1 - 0.45, 1.25)), dmat("fenceW", (245, 245, 240), rough=0.7), None, r=0.03, rot=(math.radians(28), 0, 0))
    r = root_of(name, _V6((x + 1.4, ys[0] - 1.0, 0.25)))
    rb(name + "Fallen", (0.4, 1.2, 4.0), _V6((0, 0, 0)), dmat("fenceW", (245, 245, 240), rough=0.7), r, r=0.05, rot=(0, math.radians(84), math.radians(20)))
    rb(name + "Nail", (0.06, 0.06, 0.3), _V6((0.0, 0.2, 0.5)), dmat("nailR", (130, 80, 50), metal=0.5), r, r=0.01)
    return r, gone


def p6_torch(name="Torch", parent=None):
    """Torch: rubber grip rings, flared head, chrome bezel, glowing lens, a button; one narrow spot (no volume)."""
    r = root_of(name, (0, 0, 0))
    if parent is not None: r.parent = parent
    body = dmat("torchBody", (40, 60, 110), metal=0.4, rough=0.4)
    rcyl(name + "Body", 0.14, 1.1, _V6((0, 0, 0)), body, r, axis="Y", seg=18)
    for k in range(4): rcyl(name + "Ring", 0.155, 0.06, _V6((0, -0.35 + k * 0.14, 0)), dmat("torchGrip", (25, 25, 28), rough=0.9), r, axis="Y", seg=18, bevel=0.02)
    rcyl(name + "Head", 0.16, 0.42, _V6((0, 0.72, 0)), body, r, axis="Y", seg=20, top_scale=1.45)
    rcyl(name + "Bezel", 0.25, 0.08, _V6((0, 0.95, 0)), dmat("chrome", (220, 220, 225), metal=1.0, rough=0.15), r, axis="Y", seg=24)
    rcyl(name + "Lens", 0.2, 0.02, _V6((0, 0.99, 0)), glow("torchLens", (255, 246, 220), 18.0), r, axis="Y", seg=24, bevel=0.0)
    rb(name + "Btn", (0.12, 0.16, 0.06), _V6((0, 0.2, 0.15)), dmat("torchBtn", (200, 60, 50), rough=0.5), r, r=0.03)
    ld = bpy.data.lights.new(name + "Beam", "SPOT"); ld.energy = 900; ld.spot_size = math.radians(34); ld.spot_blend = 0.6
    ld.color = (1.0, 0.95, 0.85); ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(name + "Beam", ld); COL_PROPS.objects.link(lo); lo.parent = r; lo.location = (0, 1.0, 0)
    lo.rotation_euler = (math.radians(-90), 0, 0)
    r["beam"] = lo.name
    return r


def p6_phone(name="Phone", parent=None, screen_on=True, caller="Milo"):
    """Phone: rounded slab, glowing call screen (image), camera bump, side buttons, a sticker on the case."""
    img = phone_screen_img(name=caller)
    r = root_of(name, (0, 0, 0))
    if parent is not None: r.parent = parent
    rb(name + "Body", (0.56, 0.07, 1.12), _V6((0, 0, 0)), dmat("phoneCase", (230, 120, 150), rough=0.55), r, r=0.08)
    rb(name + "Bezel", (0.52, 0.02, 1.06), _V6((0, -0.035, 0)), dmat("phoneBezel", (15, 15, 18), rough=0.3), r, r=0.06)
    plane(name + "Screen", 0.48, 1.0, _V6((0, -0.048, 0)), imgmat(name + "ScreenImg", img, rough=0.3, emit=2.2 if screen_on else 0.0), r, rot=(0, 0, math.pi))
    rb(name + "Cam", (0.22, 0.04, 0.22), _V6((-0.12, 0.05, 0.38)), dmat("phoneCam", (30, 30, 34), rough=0.3), r, r=0.05)
    rcyl(name + "Lens", 0.05, 0.03, _V6((-0.12, 0.075, 0.38)), dmat("chrome", (220, 220, 225), metal=1.0, rough=0.15), r, axis="Y", seg=14)
    for z in (0.25, 0.08): rb(name + "Btn", (0.03, 0.04, 0.12), _V6((0.29, 0, z)), dmat("phoneBtn", (200, 100, 130)), r, r=0.01)
    rcyl(name + "Sticker", 0.09, 0.01, _V6((0.1, 0.04, -0.3)), dmat("sticker", (250, 210, 60)), r, axis="Y", seg=12, bevel=0.0)
    return r


def p6_rae_door_set(RO, name="RaeDoor"):
    """Rae's front door at night (stand-alone set at z=400): porch deck + step, lavender siding facade with trim, the
    door swung IN, peephole, letterbox, house number, ONE porch
    lamp (the practical), doormat, and a warm-dark hall behind: two-tone walls, coat hooks, stairs, hall table + key bowl."""
    RO = _V6(RO); r = root_of(name, RO)
    siding = tex_mat("RaeSiding", (190, 170, 220), "siding"); trim = dmat("raeTrim", (245, 244, 240), rough=0.45)
    deck = tex_mat("RaeDeck", (140, 110, 85), "planks", rough=0.7)
    rb(name + "Deck", (16, 8, 0.5), RO + _V6((0, -4, 0.25)), deck, None, r=0.04)
    rb(name + "Step", (8, 1.6, 0.5), RO + _V6((0, -8.6, 0.0)), deck, None, r=0.04)
    rb(name + "Lawn", (80, 40, 0.2), RO + _V6((0, -26, -0.2)), dmat("lawnNight", (40, 70, 40), rough=1.0), None, r=0.02)
    # facade (door opening 5 x 9 at x -2.5..2.5)
    for x0, x1 in ((-12, -2.5), (2.5, 12)):
        rb(name + "Wall", (x1 - x0, 0.8, 14), RO + _V6(((x0 + x1) / 2, 0.4, 7.5)), siding, None, r=0.03)
    rb(name + "WallTop", (5, 0.8, 5), RO + _V6((0, 0.4, 12.0)), siding, None, r=0.03)
    for dx in (-2.75, 2.75): rb(name + "Casing", (0.5, 1.0, 9.6), RO + _V6((dx, 0.3, 5.3)), trim, None, r=0.05)
    rb(name + "Lintel", (6.2, 1.0, 0.6), RO + _V6((0, 0.3, 10.1)), trim, None, r=0.05)
    rb(name + "Num", (0.9, 0.1, 1.1), RO + _V6((4.0, -0.05, 8.3)), dmat("numPlate", (40, 40, 44), metal=0.5, rough=0.4), None, r=0.06)
    num = sign_img("/tmp/p6_num.png", "7", bg=(40, 40, 44), fg=(230, 200, 120), size=150, seed=4)
    plane(name + "NumImg", 0.8, 0.5, RO + _V6((4.0, -0.11, 8.3)), imgmat(name + "NumM", num, rough=0.5), None, rot=(0, 0, math.pi))
    # porch lamp: the one practical light
    rb(name + "LampBox", (0.7, 0.6, 1.1), RO + _V6((-4.0, -0.3, 8.2)), dmat("lampBlack", (30, 30, 32), metal=0.4, rough=0.5), None, r=0.08)
    rb(name + "LampGlow", (0.5, 0.05, 0.8), RO + _V6((-4.0, -0.62, 8.2)), glow("lampWarm", (255, 200, 130), 8.0), None, r=0.04)
    lp = bpy.data.lights.new(name + "Lamp", "POINT"); lp.energy = 260; lp.color = (1.0, 0.74, 0.46); lp.shadow_soft_size = 0.12   # small = crisp top-light shadows
    lo = bpy.data.objects.new(name + "Lamp", lp); COL_PROPS.objects.link(lo); lo.location = RO + _V6((-4.0, -1.4, 8.0))
    # door swung in 70 deg, hinge on the left (x=-2.5), chain from door edge to the frame
    hinge = root_of(name + "Hinge", RO + _V6((-2.45, 0.7, 0.5))); hinge.rotation_euler = (0, 0, math.radians(68))   # swings IN (into the hall)
    dw = dmat("raeDoor", (120, 70, 90), rough=0.5)
    rb(name + "Door", (4.9, 0.35, 9.0), _V6((2.45, 0, 4.5)), dw, hinge, r=0.05)
    for z0 in (1.3, 5.2): rb(name + "DPnl", (3.6, 0.1, 3.0), _V6((2.45, -0.2, z0 + 1.5)), dmat("raeDoorPnl", (135, 82, 104), rough=0.5), hinge, r=0.06)
    brass = dmat("brassK", (200, 168, 80), metal=0.85, rough=0.3)
    rcyl(name + "Peep", 0.1, 0.1, _V6((2.45, -0.22, 7.2)), brass, hinge, axis="Y", seg=14)
    rb(name + "Letter", (1.4, 0.08, 0.36), _V6((2.45, -0.22, 3.4)), brass, hinge, r=0.04)
    rcyl(name + "Knob", 0.2, 0.3, _V6((4.3, -0.32, 4.3)), brass, hinge, axis="Y", seg=18, bevel=0.08)
    # (security chain removed, Joel 23 Nov: read as a random hanging thing)
    # doormat
    plane(name + "Mat", 4.0, 2.4, RO + _V6((0, -2.2, 0.52)), imgmat(name + "MatM", mat_img("/tmp/p6_mat.png"), rough=1.0), None, rot=(math.radians(90), 0, math.pi))
    # hall behind (y 0.8 .. 16)
    rb(name + "HallFloor", (14, 16, 0.4), RO + _V6((0, 8.8, 0.3)), tex_mat("RaeHallFloor", (120, 90, 70), "planks", rough=0.6), None, r=0.02)
    for x in (-7, 7): rb(name + "HallSide", (0.6, 16, 14), RO + _V6((x, 8.8, 7)), tex_mat("RaeHallWall", (215, 205, 190), "plaster"), None, r=0.02)
    rb(name + "HallBack", (14, 0.6, 14), RO + _V6((0, 16.8, 7)), tex_mat("RaeHallWall", (215, 205, 190), "plaster"), None, r=0.02)
    rb(name + "HallCeil", (14, 16, 0.4), RO + _V6((0, 8.8, 14.2)), dmat("ceilW", (235, 232, 226)), None, r=0.02)
    wainscot(name + "Wain", -6.7, 6.7, 0.8, 16.5, "LRB", h=3.6, rgb=(110, 90, 130), top=None, z0=0.5)
    coat_hooks(name + "Coats", RO + _V6((-6.7, 6.0, 0.5)), (1, 0, 0), z=7.4, coats=((122, 84, 170), (70, 90, 60), (180, 150, 90)))
    picture(name + "Pic1", RO + _V6((6.7, 5.0, 0.5)), (-1, 0, 0), 7.6, w=2.0, h=2.4, kind="family", seed=33)
    picture(name + "Pic2", RO + _V6((6.7, 9.0, 0.5)), (-1, 0, 0), 7.2, w=1.6, h=2.0, kind="land", seed=34)
    for k in range(7):                                                   # stairs climbing away on the right, back of the hall
        rb(name + "Stair", (4.0, 1.2, 0.9 * (k + 1)), RO + _V6((4.4, 10.4 + k * 1.0, 0.5 + 0.45 * (k + 1))), tex_mat("RaeStairs", (130, 95, 70), "planks", rough=0.6), None, r=0.04)
    rb(name + "Banister", (0.25, 7.6, 0.3), RO + _V6((2.3, 13.4, 5.2)), dmat("banister", (90, 60, 40), rough=0.5), None, r=0.06, rot=(math.radians(-41), 0, 0))
    rb(name + "Table", (3.0, 1.2, 0.25), RO + _V6((-5.5, 11.5, 3.3)), dmat("hallTable", (110, 75, 50), rough=0.5), None, r=0.05)
    for dx in (-1.2, 1.2): rb(name + "TLeg", (0.2, 0.2, 2.9), RO + _V6((-5.5 + dx, 11.5, 1.85)), dmat("hallTable", (110, 75, 50)), None, r=0.04)
    rcyl(name + "Bowl", 0.5, 0.25, RO + _V6((-5.4, 11.4, 3.55)), dmat("bowl", (60, 110, 150), rough=0.3), None, seg=16, top_scale=1.3)
    rb(name + "Keys", (0.3, 0.1, 0.12), RO + _V6((-5.3, 11.3, 3.75)), dmat("keys", (200, 190, 120), metal=0.8, rough=0.3), None, r=0.03)
    rcyl(name + "LampBase", 0.3, 1.2, RO + _V6((-6.3, 11.6, 4.0)), dmat("lampBase", (220, 210, 190), rough=0.4), None, seg=14)
    rcyl(name + "LampShade", 0.6, 0.9, RO + _V6((-6.3, 11.6, 5.0)), glow("shadeWarm", (255, 210, 150), 2.5), None, seg=18, top_scale=0.7)
    hf = bpy.data.lights.new(name + "HallFill", "AREA"); hf.energy = 260; hf.size = 6; hf.color = (1.0, 0.8, 0.58)
    ho = bpy.data.objects.new(name + "HallFill", hf); COL_PROPS.objects.link(ho); ho.location = RO + _V6((0, 9, 13.5))
    return r, hinge


def p6_branches(name="Branches", loc=(15.2, -33.0, 9.0), seed=4):
    """A bare-ish tree limb outside Milo's side window: a few tapering twigs + small leaf clusters. Cheap boxes, but
    it's the room's COOKIE: the moon spot casts its moving shadow across Milo, the wall, the notes. Sway it with
    rotation keys on the root (scene). Returns root."""
    rnd = random.Random(seed); r = root_of(name, _V6(loc))
    bark = dmat("bark", (60, 48, 40), rough=0.9); leaf = dmat("leafNight", (40, 60, 40), rough=0.9)

    def limb(p, d, L, w, depth):
        if depth == 0 or L < 0.6: return
        q = p + d * L; mid = (p + q) / 2
        rot = d.to_track_quat("Z", "Y").to_euler()
        rb(name + "Twig", (w, w, L), mid, bark, r, r=min(0.05, w * 0.4), rot=tuple(rot))
        if depth <= 2:
            for k in range(2):
                c = q + _V6((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.3, 0.4)))
                rb(name + "Leaf", (rnd.uniform(0.5, 0.9), rnd.uniform(0.5, 0.9), 0.12), c, leaf, r, r=0.05,
                   rot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 3)))
        for k in range(2 if depth > 1 else 1):
            nd = (d + _V6((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(-0.4, 0.5)))).normalized()
            limb(q, nd, L * rnd.uniform(0.55, 0.75), w * 0.65, depth - 1)
    limb(_V6((0, 0, -4.0)), _V6((-0.35, -0.25, 1)).normalized(), 3.2, 0.32, 4)
    limb(_V6((0, 0, -1.0)), _V6((-0.4, 0.6, 0.6)).normalized(), 2.6, 0.22, 3)
    return r
