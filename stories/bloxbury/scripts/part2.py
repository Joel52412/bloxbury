# part2.py - BLOXBURY Part 2 "She Came Home". Built on the shared scene kit (scene_kit.py): this file is settings + beats.
# Rig v2 faces, library cast/sets (props3), director shots.
# Audio/cues/captions: stories/bloxbury/audio/prep_p2.py -> {env_p2.json, part2_audio.wav, captions_p2.ass}
# Preview: RENDER=1 OUT=dir RX=216 RY=384 SAMPLES=4 python3 part2.py      Pod: ENGINE=GPU RENDER=1 RX=1080 RY=1920 blender -b --python part2.py
import os
exec(open(os.environ.get("KIT", "/home/claude/studio_library/engine/scene_kit.py")).read())
boot("p2", world="bloxbury", patches=BLOX_LOW_WINDOWS)

# ================================================================== LIBRARY: cast cards, props batches, sets
load("recurring", "props2", "props3")

# ------------------------------------------------------------------ cast
milo, mum, rae, real, refl = cast(milo=(make_milo, "rest_flat"), mum=(lambda: make_mum("Mum"), "rest_smile"), rae=(make_rae, "rest_flat"),
                                  real=(lambda: make_mum("RealMum"), "rest_frown"), refl=(lambda: make_mum("ReflMum"), "rest_smile"))
fm, fmum, frae, freal, frefl = (RIGS[k] for k in ("milo", "mum", "rae", "real", "refl"))
note = p2_notebook(rae["tiltLeft"])
no_reflection(mum)                      # the fake Mum has NO reflection of her own: the mirror shows the twin
ray_only_glossy(refl)

# ------------------------------------------------------------------ sets
KO = V((520, 0, 400)); KIT = p3_kitchen_set(KO)
HO = V((560, 0, 400)); HALL = p3_hallway_set(HO)
if os.environ.get("DRESS", "1") == "1":            # set dressing (props4.py; DRESS=0 = bare sets for cost tests)
    load("props4"); dress_kitchen(KO); dress_hallway(HO); dress_bedroom()
    load("props5"); detail_town(houses)       # town houses: trim, shutters, porch, yard
p3_hollow_closet()
LIST = p3_list_insert(V((700, 700, 0)), path="/tmp/p3_list.png")
# pancakes: plate + three stacked discs + butter, on the table in front of Milo
rb("KitchenFrontWall", (26, 0.4, 11), KO + V((0, -9.0, 5.5)), tex_mat("KitchenWall", (246, 236, 206), "plaster"), None, r=0.02)   # closes the room for reverse shots
for o in [o for o in bpy.data.objects if o.name.startswith("Table_Chair")]:
    for c in [o] + list(o.children_recursive): c.hide_render = True                    # chairs blocked the hob shots and crowded the hug (they stand)
PLATE = KO + V((-5.9, -1.0, 3.96))
rcyl("Plate", 0.95, 0.08, PLATE, pmat("PlateW", (246, 246, 244), rough=0.25), None)
for k in range(3): rcyl("Pancake", 0.72 - k * 0.03, 0.16, PLATE + V((0, 0, 0.14 + k * 0.17)), pmat("PancakeM", (214, 158, 84), rough=0.6), None, bevel=0.07)
rb("Butter", (0.32, 0.32, 0.14), PLATE + V((0.05, 0, 0.66)), pmat("ButterM", (250, 226, 130), rough=0.3), None, r=0.04)
# Milo's room at night: dim cool fill, moonlight on the closet crack, light under the bedroom door
ROOMFILL = p3_area("RoomFill2", (-2, -36, 12.5), (2, -40, 0), 0, 8, (0.6, 0.7, 1.0))
CLOSET_IN = p3_area("ClosetIn", (3.2, -43.6, 6.2), (4.5, -45.7, 3.2), 0, 0.8, (0.7, 0.78, 1.0))
MKEY = p3_area("MiloKey", (5.5, -32.5, 7.5), (3.0, -38.6, 4.6), 0, 4, (1.0, 0.9, 0.8))
MRIM = p3_area("MiloRim", (0.0, -45.0, 8.0), (3.0, -38.6, 4.6), 0, 3, (0.6, 0.7, 1.0))
DOORLINE = rb("DoorLight", (4.4, 0.35, 0.02), V((0, -30.75, 0.42)), pmat("DoorLightM", (255, 200, 140), emit=0.0, emit_rgb=(255, 190, 120)), None, r=0.01)
DOORLINE_EM = DOORLINE.material_slots[0].material.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
FEET = [rb("FootShadow", (1.0, 0.36, 0.03), V((x, -30.75, 0.43)), pmat("FootShadowM", (0, 0, 0), rough=1.0), None, r=0.01) for x in (-0.7, 0.7)]
FRONT_DOOR = [o for o in bpy.data.objects if o.name.startswith("FrontDoor")][0]
FD_ROT = tuple(FRONT_DOOR.rotation_euler)
strip, cglow = p2_door_glow(7.0, -45.85)        # Part 1's closet glow (bridge only)
# the Knocker: bridge lunge (camera-visible) + toaster ghost (reflection-only)
KN = make_knocker("Knocker", 10.5); KR = KN["root"]
KG = make_knocker("KnockerGhost", 9.0); ray_only_glossy(KG)
KR.location = FAR; KG["root"].location = FAR

# ================================================================== CAMERA: hard cuts, each shot keyed inside its frames
camera_rig()
load("cinema")          # camera grammar: cine() / insert() / check_framing()

# ================================================================== 0  BRIDGE 0.00-1.25: Part 1's last image, then black
set_night(0.0); house_lights(0.0, False)
CL_X, CL_Y = 7.0, -45.85
kf(CLOSET_HINGE, "rotation_euler", 1, (0, 0, DEG(-88)), interp="CONSTANT")
kf(cglow, "energy", 1, 700, interp="CONSTANT"); kf(cglow, "energy", FT(0.8), 0, interp="CONSTANT")
s.frame_set(1); bpy.context.view_layer.update()
KR.location = (0, 0, 0); KR.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
HEAD_OFF = KN["head"].matrix_world.translation - KR.matrix_world.translation
BCAM = V((3.0, -40.6, 4.4)); BAIM = V((CL_X, CL_Y, 4.6))
LUNGE = BCAM + (BAIM - BCAM).normalized() * 1.9 + V((0, 0, -0.1))


def k_place(fr, head_world, yaw=0.0, interp="BEZIER"):
    rot = Matrix.Rotation(DEG(yaw), 3, "Z")
    kf(KR, "location", fr, V(head_world) - rot @ HEAD_OFF, interp=interp); kf(KR, "rotation_euler", fr, (0, 0, DEG(yaw)), interp=interp)


k_place(1, LUNGE + V((0.6, -1.4, 0.15)), 24); k_place(FT(0.55), LUNGE, 26); k_place(FT(0.8), LUNGE + V((0.04, 0.05, 0)), 26, interp="CONSTANT")
k_place(FT(0.8) + 1, FAR, 0, interp="CONSTANT")
krim = p3_area("KRimB", (6.4, -48.6, 9.5), LUNGE, 0, 2, (0.55, 0.65, 1.0))
kf(krim, "energy", 1, 650, interp="CONSTANT"); kf(krim, "energy", FT(0.8), 0, interp="CONSTANT")
shot("0 bridge lunge", 0.0, 0.8, [(0, BCAM, BAIM, 30), (1, BCAM + V((0, -0.08, 0)), BAIM, 30)])
# black card (bridge 0.8-1.25 and the hard cut 72.4-73.0)
blk = plane("Blackout", 4, 4, V((0, 0, 0)), pmat("BlackCard", (0, 0, 0), rough=1.0), cam)
blk.location = (0, 0, -0.3); blk.rotation_euler = (DEG(90), 0, 0); blk.visible_shadow = False
for fr_b, on in ((1, False), (FT(0.8), True), (FT(1.25), False), (FT(E2["black_cut"]), True), (FT(E2["outro0"]), False)):
    kf(blk, "hide_render", fr_b, not on, interp="CONSTANT")
shot("0b black", 0.8, 1.25, [(0, BCAM, BAIM, 30)])

# ================================================================== 1-2  KITCHEN 1.25-18.4 (day). Fake Mum: held smile, NEVER blinks, no breathing idle
set_day(1.25)
HOB = KO + V((-4.6, 4.3, 0)); MT = KO + V((-6.5, -6.4, 0))
at(mum, FT(1.25), HOB, 200)                    # at the hob, turned to us for the match cut
at(milo, FT(1.25), MT, -12)                     # at the table, facing the hob
expr(fmum, FT(1.25), "content"); mouth(fmum, FT(1.25), "rest_smile")
for t, z in ((1.25, 0), (2.4, 5), (3.6, -4), (4.9, 4), (6.2, 0)):            # humming: a slow, too-even head sway
    neck(mum, FT(t), 0, 0, z)
arm(mum, "Right", FT(1.25), euler=(55, 20)); arm(mum, "Right", FT(5.4), euler=(55, 20)); arm(mum, "Right", FT(5.9), euler=(8, 6))
arm(mum, "Left", FT(1.25), euler=(4, -6))
idle_here(milo, FT(1.25), FT(18.4))
expr(fm, FT(1.25), "nervous"); expr(fm, FT(5.6), "friendly"); expr(fm, FT(6.8), "nervous")
MH = H(milo); MUH = H(mum)
cine("K1 match cut: her smile", 1.25, 4.1, MUH, u=V((0.22, -1, 0)), size="MCU", move="pull", amt=2.4, lens=30, sy=0.14, land=0.75)   # Knocker-size CU -> reveals the kitchen
cine("K2 Milo at the table", 4.1, 5.5, milo, u=V((0.36, 1, 0)), size="MCU", move="hold", lens=50, sx=0.1)
say(line(5.60), fmum, "rest_smile", "excited")                               # "Morning, Milo!" bright
expr(fmum, FT(5.6), "excited"); expr(fmum, FT(6.9), "content")
cine("K3 Morning, Milo!", 5.5, 7.0, MUH, u=V((-0.34, -1, 0)), size="MCU", move="drift", amt=6, lens=26, sx=-0.08, tilt=4)   # slightly below her: too bright, too big
# pancakes: her hand slides the plate in (plate rides on her hand, then stays)
cine("K4 pancakes", 7.0, 9.0, PLATE + V((0, 0, 0.3)), u=V((-0.42, -1, 0)), size=0.42, span=1.4, move="push", amt=1.15, lens=40, sy=-0.12, tilt=32, fstop=3.2, extra=[(mum["head"], V((0, 0, 0)))])   # plate low, her face in the top of frame
at(mum, FT(7.0), KO + V((-4.4, 0.9, 0)), 200)
arm(mum, "Right", FT(7.0), euler=(70, 12)); arm(mum, "Right", FT(8.2), euler=(70, 12)); arm(mum, "Right", FT(8.6), euler=(6, 6))
# toaster + humming at the hob; the Knocker ghost shows in the chrome for 4 frames (rewatch bait)
at(mum, FT(9.0), HOB, 175)
for t, z in ((9.0, 0), (9.7, 6), (10.4, -6), (11.0, 0)): neck(mum, FT(t), 0, 0, z)
arm(mum, "Right", FT(9.0), euler=(55, 20)); arm(mum, "Left", FT(9.0), euler=(4, -6))
TST = KO + V((-6.6, 6.6, 4.7))
cine("K5 toaster + humming", 9.0, 11.0, TST + V((0.3, 0, -0.1)), u=V((-0.6, -1, 0)), size=0.34, span=1.5, move="drift", amt=10, lens=40, sy=0.0, tilt=6, fstop=2.8)   # parallax across the chrome (ghost at 9.95)
KG["root"].location = FAR
kf(KG["root"], "location", FT(9.95), TST + V((1.2, -4.4, -4.7)), interp="CONSTANT"); kf(KG["root"], "rotation_euler", FT(9.95), (0, 0, DEG(160)), interp="CONSTANT")
kf(KG["root"], "location", FT(9.95) + 4, FAR, interp="CONSTANT"); kf(KG["root"], "location", 1, FAR, interp="CONSTANT")
# the hug: from behind Milo (his body hides where her arms pass), her face over his shoulder, smile held, eyes open
HUG = MT + V((-1.15, -1.0, 0.25))                 # behind him, a little to his right, so her face sits beside his
at(mum, FT(11.0), HUG, -12)
arm(mum, "Left", FT(11.0), target=(0.2, 1.9, 3.3)); arm(mum, "Right", FT(11.0), target=(1.3, 1.9, 3.4))   # arms wrap round his chest (hug contact is OK)
arm(milo, "Left", FT(11.0), euler=(4, -6)); arm(milo, "Right", FT(11.0), euler=(4, 6))
neck(mum, FT(11.0), -4, 0, 6); expr(fmum, FT(11.0), "content")
expr(fm, FT(11.0), "nervous"); expr(fm, FT(14.2), "notice"); expr(fm, FT(16.3), "scared")
neck(milo, FT(11.0), 0, 0, 0); neck(milo, FT(15.0), 0, 0, 0); neck(milo, FT(16.6), 0, 0, 12)      # his head slides toward her face
MH2 = H(milo); MUH2 = HUG + V((0, 0, 4.6))
TW = (MH2 + MUH2) / 2
cine("K6 the long hug", 11.0, 14.15, TW, u=V((0.25, 1, 0)), size=0.2, move="hold", lens=32, sy=0.15, tilt=12, extra=[(milo["head"], V((0, 0, 0))), (mum["head"], V((0, 0, 0)))])   # hold: the hug goes on too long
cine("K7 she called me Milo", 14.15, 16.25, milo, u=V((0.4, 1, 0)), size="MCU", move="push", amt=1.25, lens=55, sx=0.12, extra=[(mum["head"], V((0, 0, 0)))])
cine("K8 never calls me Milo", 16.25, SC["kitchen"][1], milo, u=V((0.3, 1, 0)), size="CU", move="push", amt=1.15, lens=65, sx=0.05)
blinks(fm, 1.25, 18.4)

# ================================================================== 3-4  RAE'S PORCH 18.4-39.9 (day, town)
P0 = SC["porch"][0]
RAEP = V((50.0, -28.4, 0.0)); MILP = V((47.6, -24.2, 0.0))
park(mum, FT(P0))
at(rae, FT(P0), RAEP, 30); at(milo, FT(P0), MILP + V((-5.5, 8.0, 0)), 210)
walk(milo, FT(P0), FT(19.3), MILP + V((-5.5, 8.0, 0)), MILP, steps=4, leg=34)          # he runs up to her door
idle_here(rae, FT(P0), FT(39.9), amp=0.012, ph=1.0); idle_here(milo, FT(19.4), FT(39.9))
arms_down(rae, FT(P0)); arm(rae, "Left", FT(P0), (-0.6, 1.4, 2.8)); arm(rae, "Left", FT(28.3), (-0.6, 1.4, 2.8))
arm(rae, "Left", FT(28.9), (-0.4, 1.8, 3.6)); arm(rae, "Left", FT(34.9), (-0.4, 1.8, 3.6)); arm(rae, "Left", FT(35.5), (-0.6, 1.4, 2.8))
expr(frae, FT(P0), "deadpan"); expr(frae, FT(28.6), "sad"); expr(frae, FT(33.3), "ominous"); expr(frae, FT(37.0), "deadpan")
expr(fm, FT(P0), "scared"); expr(fm, FT(23.4), "nervous"); expr(fm, FT(29.0), "shocked"); expr(fm, FT(35.1), "scared")
for t in (18.80, 23.40, 35.10): say(line(t), fm, "rest_flat", "excited" if t < 19 else "calm", P=milo)
for t in (21.50, 25.50, 28.60, 30.00, 33.30, 37.00, 38.20): say(line(t), frae, "rest_flat", "calm", nod=2.5, P=rae)
RH = V((50.0, -28.4, 4.6)); MHP = MILP + V((0, 0, 4.6))
shot("P1 he runs to Rae", P0, 21.45, [(0, (55.5, -17.0, 5.6), (49.0, -25.5, 4.0), 28), (0.85, (54.9, -18.6, 5.4), (48.8, -26.4, 4.1), 28)])
cine("P2 Did she knock?", 21.45, 23.35, rae, toward=milo, ang=30, size="MCU", move="drift", amt=6, lens=50, sx=-0.1)
cine("P3 she had a key", 23.35, 25.45, milo, toward=rae, ang=-38, size="MCU", move="hold", lens=26, sx=0.1)
cine("P4 doesn't need to knock", 25.45, 28.5, rae, toward=milo, ang=26, size="CU", move="push", amt=1.2, lens=55, sx=-0.08)
cine("P5 she opens the list", 28.5, 29.95, rae, toward=milo, ang=34, size="MS", move="hold", lens=40, sy=0.22, sx=-0.06)   # chest-up: the notebook comes up into frame
insert("P5b insert: Mum crossed off", 29.95, 33.2, LIST + V((0, 0, 0.2)), LIST + V((0.72, 0, 1.36)), (0, 1, 0), 3.4, 1.35, lens=50, land=0.7)   # whole page -> lands on Milo's Mum, crossed out
cine("P6 Three weeks ago", 33.2, 35.0, rae, toward=milo, ang=40, size="CU", move="hold", lens=45, tilt=-4, sx=-0.06)   # low, still, ominous
cine("P7 who's in my kitchen", 35.0, 36.95, milo, toward=rae, ang=-38, size="CU", move="push", amt=1.2, lens=36, sx=0.08)
cine("P8 Mirrors don't lie", 36.95, SC["porch"][1], rae, toward=milo, ang=30, size="MCU", move="sink", amt=8, lens=50, sx=-0.1)   # camera lowers: she looms on the button line
blinks(fm, P0, 39.9, ph=0.7); blinks(frae, P0, 39.9, every=4.2, ph=1.3)

# ================================================================== 5  HALLWAY MIRROR 39.9-51.7 (night)
M0 = SC["mirror"][0]
set_night(M0)
park(rae, FT(M0))
MILH = HO + V((-1.0, 0.6, 0)); MUMH = HO + V((1.8, 11.0, 0))
at(milo, FT(M0), MILH, 100); at(mum, FT(M0), MUMH, 180); at(refl, FT(M0), MUMH, 180)
for P in (milo, mum, refl): arms_down(P, FT(M0))
for P in (mum, refl): neck(P, FT(M0) - 1, 0, 0, 0, interp="CONSTANT")
idle_here(milo, FT(M0), FT(51.7), amp=0.012)
expr(fm, FT(M0), "nervous"); expr(fm, FT(41.2), "content"); expr(fm, FT(42.6), "nervous"); expr(fm, FT(45.2), "scared"); expr(fm, FT(47.6), "shocked")
mouth(fm, FT(M0), "rest_flat")
# real Mum: smile drops on "Then Mum stopped smiling"; reflection keeps it, then its head turns to Milo (in silence)
expr(fmum, FT(M0), "content"); mouth(fmum, FT(M0), "rest_smile"); expr(fmum, FT(43.0), "content"); expr(fmum, FT(43.4), "deadpan")
mouth(fmum, FT(43.3), "rest_flat")
expr(frefl, FT(M0), "content"); mouth(frefl, FT(M0), "rest_smile"); mouth(frefl, FT(44.6), "rest_creepy")
neck(refl, FT(M0), 0, 0, 0); neck(refl, FT(46.2), 0, 0, 0); neck(refl, FT(47.6), -6, 0, -32)
say(line(47.80), fmum, "rest_flat", "calm", P=mum); say(line(49.00), fmum, "rest_flat", "calm", P=mum)
neck(mum, FT(47.6), 0, 0, 0); neck(mum, FT(49.0), 0, 0, 8)       # a slight, slow head tilt
GL = HO + V((-4.49, 2.0, 5.0)); VIRT = V((2 * (HO.x - 4.49) - MUMH.x, MUMH.y, MUMH.z + 4.6))
shot("M1 It looked like Mum", M0, 42.2, [(0, HO + V((3.18, -9.0, 5.0)), GL, 32), (0.85, HO + V((2.95, -7.6, 5.0)), GL, 32)])
cine("M2 she stops smiling", 42.2, 44.5, mum, u=V((0.15, -1, 0)), size="MS", move="push", amt=1.25, lens=30)
cine("M3 her reflection didn't", 44.5, 47.75, VIRT, u=(HO + V((0.5, -6.0, 5.0)) - VIRT), size=0.13, move="push", amt=1.2, lens=80, sy=0.0, tilt=0, fstop=3.0)   # through the mirror: same sight line, dolly only
cine("M4 who told you about the mirror", 47.75, SC["mirror"][1], mum, u=V((0.1, -1, 0)), size="MCU", move="push", amt=1.25, lens=50, tilt=-3)
blinks(fm, M0, 51.7, every=2.6)
park(refl, FT(SC["mirror"][1])); park(mum, FT(SC["mirror"][1]))

# Part 1's room clock: tonight it already says 3:00 AM (2:59 hidden)
CLOCK_TEXTS["2:59 AM"].hide_render = True; CLOCK_TEXTS["3:00 AM"].hide_render = False
# ================================================================== 6-7  MILO'S BEDROOM 51.7-72.4 (night)
B0 = SC["bedroom"][0]
park(mum, FT(B0)); park(refl, FT(B0))
kf(ROOMFILL, "energy", 1, 0, interp="CONSTANT"); kf(ROOMFILL, "energy", FT(B0), 70, interp="CONSTANT")
kf(CLOSET_HINGE, "rotation_euler", FT(1.25), (0, 0, 0), interp="CONSTANT")
MB = V((1.5, -36.0, 0.4))
at(milo, FT(B0), MB + V((-0.8, 3.0, 0)), 0)
walk(milo, FT(B0), FT(53.2), MB + V((-0.8, 3.0, 0)), MB, steps=2, leg=18, z=0.4)       # backs away from the locked door
arms_down(milo, FT(53.3)); idle(milo, FT(53.4), FT(72.4), amp=0.012, base_z=0.4)
expr(fm, FT(B0), "scared"); expr(fm, FT(53.4), "notice"); expr(fm, FT(56.8), "scared"); expr(fm, FT(59.7), "shocked")
expr(fm, FT(62.5), "sad"); expr(fm, FT(64.3), "scared"); expr(fm, FT(65.3), "shocked"); expr(fm, FT(69.6), "scared")
neck(milo, FT(B0), 0, 0, 0); neck(milo, FT(56.9), 0, 0, 0); neck(milo, FT(58.6), 0, 0, -70)    # slowly turns to the closet
neck(milo, FT(65.1), 0, 0, -70); neck(milo, FT(65.8), 0, 0, 0)                                   # footsteps: back to the door
for tk in (67.90, 68.20, 68.48):                                                                 # flinch on each knock
    kf(milo["chest"], "rotation_euler", FT(tk) - 1, (0, 0, 0)); kf(milo["chest"], "rotation_euler", FT(tk) + 1, (DEG(-5), 0, 0))
    kf(milo["chest"], "rotation_euler", FT(tk) + 5, (0, 0, 0))
    kf(FRONT_DOOR, "rotation_euler", FT(tk) - 1, FD_ROT); kf(FRONT_DOOR, "rotation_euler", FT(tk), (FD_ROT[0], FD_ROT[1], FD_ROT[2] + DEG(0.6)))
    kf(FRONT_DOOR, "rotation_euler", FT(tk) + 3, FD_ROT)
say(line(64.30), fm, "rest_flat", "whisper")                                                     # "Mum?"
# closet: door eases open a crack, moonlight finds her hand + bangle on "I heard it too"
kf(CLOSET_HINGE, "rotation_euler", FT(57.8), (0, 0, 0)); kf(CLOSET_HINGE, "rotation_euler", FT(59.4), (0, 0, DEG(-9)))
kf(CLOSET_HINGE, "rotation_euler", FT(SC["black"][0]), (0, 0, DEG(-9)), interp="CONSTANT")
at(real, FT(B0), V((6.5, -47.9, 0.4)), 0)
arm(real, "Left", FT(B0), euler=(4, -6)); arm(real, "Left", FT(62.2), euler=(4, -6)); arm(real, "Left", FT(63.0), target=(-2.0, 2.2, 2.6))
arm(real, "Right", FT(B0), euler=(4, 6))
expr(freal, FT(B0), "scared"); mouth(freal, FT(B0), "rest_frown")
kf(CLOSET_IN, "energy", 1, 0, interp="CONSTANT"); kf(CLOSET_IN, "energy", FT(59.4), 0); kf(CLOSET_IN, "energy", FT(60.2), 160)
kf(CLOSET_IN, "energy", FT(65.1), 0, interp="CONSTANT")
park(real, FT(SC["black"][0]))
# the landing light comes on under the door with the footsteps; two shadows stop in it
key(DOORLINE_EM, "default_value", 0.0, 0.0); key(DOORLINE_EM, "default_value", 65.0, 0.0); key(DOORLINE_EM, "default_value", 65.6, 6.0)
key(DOORLINE_EM, "default_value", SC["black"][0] - 0.01, 6.0); key(DOORLINE_EM, "default_value", SC["black"][0], 0.0)
for o in FEET: vis_obj(o, 1, False); vis_obj(o, FT(67.45), True); vis_obj(o, FT(SC["black"][0]), False)
MHB = MB + V((0, 0, 4.6)); DOOR_IN = V((0, -30.6, 4.4)); CLOSET = V((5.6, -45.9, 4.2))
shot("B1 I locked my door", B0, 53.35, [(0, (6.0, -44.0, 5.6), MB + V((0, 2.5, 4.0)), 28), (1, (5.6, -43.0, 5.4), MB + V((0, 2.0, 4.0)), 30)])
cine("B2 Dinner's ready", 53.35, 56.55, milo, u=V((0.8, 1, 0)), size="MCU", move="hold", lens=30, sx=0.08)   # hold on him: we only HEAR her
cine("B3 a voice in my closet", 56.55, 59.5, CLOSET + V((0, 0, 0.6)), toward=MHB + V((-1.6, 1.2, 0)), size=0.55, span=8.0, move="push", amt=1.12, lens=35, sy=0.05, tilt=4, fstop=2.8)   # over his shoulder, the closet waits
shot("B4 the crack: her hand", 59.5, 64.2, [(0, (1.3, -39.2, 4.3), (4.6, -45.5, 3.4), 46), (0.8, (2.0, -40.9, 4.2), (4.6, -45.6, 3.4), 46)], fstop=2.4)
cine("B5 Mum?", 64.2, 65.1, milo, u=V((1, 0.3, 0)), size="CU", move="hold", lens=60, sx=-0.08)
shot("B6 footsteps + knocks", 65.1, 69.45, [(0, (-7.2, -46.5, 7.0), (0.8, -34.0, 3.4), 25), (0.85, (-6.5, -45.2, 6.6), (0.6, -33.5, 3.4), 25)])
shot("B7 Who are you talking to?", 69.45, SC["bedroom"][1], [(0, (4.6, -37.5, 1.7), (0, -30.6, 1.4), 38), (0.85, (3.9, -35.0, 1.8), (0, -30.6, 1.5), 38)], fstop=2.2)
blinks(fm, B0, 72.4, every=2.4, ph=0.3); blinks(freal, B0, 72.4, every=3.6)
shot("Z black", SC["black"][0], SC["black"][1], [(0, (0, -40, 5), (0, -30, 5), 30)])

# ================================================================== 8  OUTRO 73.0-80.0: to camera, both doors behind him
O0 = SC["outro"][0]
O = V((3.0, -38.6, 0.4))
at(milo, FT(O0), O, 0)
kf(MKEY, "energy", 1, 0, interp="CONSTANT"); kf(MKEY, "energy", FT(O0), 500, interp="CONSTANT")
kf(MRIM, "energy", 1, 0, interp="CONSTANT"); kf(MRIM, "energy", FT(O0), 300, interp="CONSTANT")
kf(CLOSET_HINGE, "rotation_euler", FT(O0), (0, 0, DEG(-6)), interp="CONSTANT")
expr(fm, FT(O0), "ominous"); expr(fm, FT(75.1), "curious"); expr(fm, FT(76.0), "question"); expr(fm, FT(76.9), "excited"); expr(fm, FT(78.6), "sly")
for t in (73.25, 75.20, 76.90):
    say(line(t), fm, "rest_flat" if t < 76 else "rest_smile", "whisper" if t < 75 else ("calm" if t < 76 else "excited"), nod=4.5, P=milo)
mouth(fm, FT(79.5), "rest_creepy")
for t, lean in ((73.0, 0), (74.9, -6), (76.8, -2), (78.5, -9), (80.0, -10)): chest(milo, FT(t), lean, 0, 0)
arms_down(milo, FT(O0)); arm(milo, "Right", FT(73.9), euler=(70, -10)); arm(milo, "Right", FT(74.5), euler=(8, 6))   # "One door." - points back
arm(milo, "Left", FT(73.25), euler=(60, 20)); arm(milo, "Left", FT(73.8), euler=(6, -6))                              # "Two mums." - a hand up
idle(milo, FT(O0), NF, amp=0.015, base_z=0.4)
OH = O + V((0, 0, 4.6))
cine("O outro", O0, E2["total"], milo, u=V((0, 1, 0)), size="MCU", move="push", amt=1.6, lens=28, sy=0.1, land=0.9)   # to camera, slow push on the question
blinks(fm, O0, E2["total"], every=2.9, ph=0.2)

# ================================================================== finish
finish_part(allow=("bridge lunge",))     # the lunge AT the lens is the scare
