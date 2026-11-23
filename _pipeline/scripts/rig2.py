# rig2.py - shared animation rig + face v2 + Milo card, lifted from test2.py (approved 22 Nov).
# exec() this AFTER the base prefix and the studio library, with ENV (rms/cen per frame) and FPS defined.
# ------------------------------------------------------------------ keyframe helpers
_LOG = []


def kf(idb, path, frame, value, index=-1, interp="BEZIER"):
    if index >= 0: getattr(idb, path)[index] = value
    else: setattr(idb, path, value)
    idb.keyframe_insert(path, frame=frame, index=index)
    _LOG.append((idb, path, frame, interp))


def apply_interp():
    cache = {}
    for idb, path, frame, interp in _LOG:
        if idb not in cache:
            d = {}
            for fc in _fcurves(idb): d.setdefault(fc.data_path, []).append(fc)
            cache[idb] = d
        for fc in cache[idb].get(path, []):
            for kp in fc.keyframe_points:
                if int(round(kp.co.x)) == frame:
                    kp.interpolation = interp
                    if interp == "BEZIER": kp.easing = "AUTO"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def vis(objs, frame, on):
    for o in objs: kf(o, "hide_render", frame, not on, interp="CONSTANT")


R = math.radians

# ------------------------------------------------------------------ rig upgrade: hips / waist / head pivots
def upgrade_rig(P):
    """Adds Chest (waist pivot), HipL/HipR (leg pivots) and Head (nod layer under the neck)."""
    root = P["root"]; nm = root.name
    chest = empty(nm + "_Chest", V((0, 0, 2)), col=COL_CHARS, parent=root)
    hipL = empty(nm + "_HipL", V((-0.5, 0, 2)), col=COL_CHARS, parent=root)
    hipR = empty(nm + "_HipR", V((0.5, 0, 2)), col=COL_CHARS, parent=root)
    neck = P["neck"]
    head = empty(nm + "_Head", V((0, 0, 0)), col=COL_CHARS, parent=neck)

    def move(ob, piv, piv_body):
        ob.parent = piv
        ob.matrix_basis = Matrix.Translation(-V(piv_body)) @ ob.matrix_basis

    for ob in list(neck.children):                      # everything on the neck -> head layer (no offset)
        if ob is not head: ob.parent = head
    for ob in list(root.children):
        if ob in (chest, hipL, hipR): continue
        bb = [ob.matrix_basis @ V(c) for c in ob.bound_box] if ob.type != "EMPTY" else [ob.matrix_basis.translation]
        cz = sum(v.z for v in bb) / len(bb); cx = sum(v.x for v in bb) / len(bb)
        if ob.name.startswith("LegL") or (cz < 2.0 and cx < 0 and ob.type != "EMPTY"): move(ob, hipL, (-0.5, 0, 2))
        elif ob.name.startswith("LegR") or (cz < 2.0 and ob.type != "EMPTY"): move(ob, hipR, (0.5, 0, 2))
        elif cz > 4.05 and ob.type != "EMPTY": move(ob, head, (0, 0, 4))        # hair / hats parented to the root
        else: move(ob, chest, (0, 0, 2))                                        # torso, shoulders, neck, straps
    P.update(chest=chest, hipL=hipL, hipR=hipR, head=head)
    # grips at the hands (counter-rotated so held props stay upright) + tilt layer
    for side in ("Left", "Right"):
        g = empty(nm + "_Grip" + side, V((0, 0, -1.5)), col=COL_CHARS, parent=P[side]); g.rotation_mode = "ZYX"
        t = empty(nm + "_Tilt" + side, V((0, 0, 0)), col=COL_CHARS, parent=g)
        P["grip" + side] = g; P["tilt" + side] = t
    return P


SHOULDER = {"Left": V((-1.5, 0, 3.5)), "Right": V((1.5, 0, 3.5))}


def arm_angles(side, target):
    d = V(target) - SHOULDER[side]
    d.normalize()
    a = math.acos(max(-1, min(1, -d.z)))
    c = math.atan2(-d.x, d.y) if math.sin(a) > 1e-3 else 0.0
    return a, c


def arm(P, side, frame, target=None, euler=None, interp="BEZIER"):
    """Pose an arm by hand target (body space) or by raw euler; grip keeps held props level."""
    if target is not None:
        a, c = arm_angles(side, target)
    else:
        a, c = R(euler[0]), R(euler[1])
    kf(P[side], "rotation_euler", frame, (a, 0, c), interp=interp)
    kf(P["grip" + side], "rotation_euler", frame, (-a, 0, -c), interp=interp)


# ------------------------------------------------------------------ face rig v2 (smooth): brows/eyes are posed, mouths swap
def fsurf(x): return surf_y(max(-0.59, min(0.59, x)))


M_SPARK_CORE = mat("SparkCore", (255, 206, 40), emit=2.0, rough=0.5)
M_SPARK_HOT = mat("SparkHot", (255, 250, 215), emit=3.5, rough=0.5)


def spark_star(name, size, m, parent, dy):
    """Flat 4-point star facing the camera (+y): thin pointed rays, reads as a glint effect."""
    import bmesh as _bm2
    b = _bm2.new(); c = b.verts.new((0, dy, 0)); ring = []
    for i in range(8):
        a = i * math.pi / 4; r = size if i % 2 == 0 else size * 0.2
        ring.append(b.verts.new((r * math.cos(a), dy, r * math.sin(a))))
    for i in range(8):
        b.faces.new((c, ring[i], ring[(i + 1) % 8]))
    me = bpy.data.meshes.new(name); b.to_mesh(me); b.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); ob.parent = parent
    COL_CHARS.objects.link(ob)
    ob.visible_shadow = False; ob.visible_diffuse = False; ob.visible_glossy = False   # glows without lighting the eye
    return ob


def adopt(objs, piv, piv_loc):
    for o in objs:
        o.parent = piv
        o.matrix_basis = Matrix.Translation(-V(piv_loc)) @ o.matrix_basis


MOUTHS = {
    "rest_smile": lambda f: f.line([(-0.13, -0.15), (-0.05, -0.2), (0.05, -0.2), (0.13, -0.15)], M_INK, r=0.024),
    "rest_flat": lambda f: f.line([(-0.1, -0.19), (0.1, -0.19)], M_INK, r=0.022),
    "rest_frown": lambda f: f.line([(-0.11, -0.21), (0, -0.175), (0.11, -0.21)], M_INK, r=0.022),
    "rest_smirk": lambda f: f.line([(-0.1, -0.18), (0.04, -0.19), (0.15, -0.13)], M_INK, r=0.022),
    "rest_creepy": lambda f: f.line([(-0.2, -0.13), (-0.1, -0.19), (0.1, -0.19), (0.2, -0.13)], M_INK, r=0.02),
    "M": lambda f: f.line([(-0.09, -0.19), (0.09, -0.19)], M_INK, r=0.03),
    "half": lambda f: (f.oval(0, -0.19, 0.16, 0.075, M_INK), f.oval(0, -0.205, 0.08, 0.03, M_TONGUE, lift=0.008)),
    "small_o": lambda f: (f.oval(0, -0.19, 0.08, 0.08, M_INK),),
    "A": lambda f: (f.oval(0, -0.19, 0.21, 0.16, M_INK), f.oval(0, -0.23, 0.12, 0.05, M_TONGUE, lift=0.008),
                    f.oval(0, -0.13, 0.15, 0.03, M_EYEWHITE, lift=0.008)),
    "E": lambda f: (f.oval(0, -0.185, 0.26, 0.085, M_INK), f.oval(0, -0.17, 0.2, 0.03, M_EYEWHITE, lift=0.008)),
    "O": lambda f: (f.oval(0, -0.2, 0.12, 0.14, M_INK), f.oval(0, -0.235, 0.07, 0.04, M_TONGUE, lift=0.008)),
    "grin_open": lambda f: (f.oval(0, -0.18, 0.3, 0.17, M_INK), f.oval(0, -0.12, 0.24, 0.04, M_EYEWHITE, lift=0.008),
                            f.oval(0, -0.23, 0.14, 0.05, M_TONGUE, lift=0.008)),
    "teeth": lambda f: (f.oval(0, -0.19, 0.3, 0.1, M_INK), f.oval(0, -0.19, 0.25, 0.055, M_EYEWHITE, lift=0.008),
                        f.line([(-0.12, -0.19), (0.12, -0.19)], M_INK, r=0.006, lift=0.012)),
}


def build_face_v2(P):
    global FACE_SKIN
    FACE_SKIN = P["skin"]
    head = P["head"]; nm = P["root"].name
    rig = {"mouths": {}, "P": P}
    EW, EH, EZ = 0.12, 0.18, 0.08
    for side, sx in (("L", -0.19), ("R", 0.19)):
        base = V((sx, fsurf(sx), EZ - EH / 2 + 0.6))           # eye pivot at the bottom of the eye
        pe = empty(f"{nm}_Eye{side}", base, col=COL_CHARS, parent=head)
        ea = empty(f"{nm}_EyeAcc{side}", V((0, 0, 0)), col=COL_CHARS, parent=pe)   # emphasis layer (talk_face), never keyed by expr
        pb = empty(f"{nm}_Blink{side}", V((0, 0, 0)), col=COL_CHARS, parent=ea)
        f = Face(head, "eye"); f.oval(sx, EZ, EW, EH, M_INK)
        f.oval(sx + EW * 0.24, EZ + EH * 0.26, EW * 0.34, EH * 0.24, M_SHINE70, lift=0.008)
        adopt(f.objs, pb, base)
        # sparkle catchlights (scale 0 = off; popped in/out smoothly, gentle twinkle)
        sp = []
        for dx, dz, sz in ((0.035, 0.13, 0.05), (-0.045, 0.03, 0.026)):
            loc = V((sx + dx, fsurf(sx + dx) + 0.03, dz + 0.6))
            pv = empty(f"{nm}_Spark{side}", loc - base, col=COL_CHARS, parent=pb); pv.scale = (0, 0, 0)
            spark_star("SpkCore", sz * 1.25, M_SPARK_CORE, pv, 0.004)    # yellow glint
            spark_star("SpkHot", sz * 0.6, M_SPARK_HOT, pv, 0.008)      # hot centre, reads as light
            sp.append(pv)
        bz = 0.235
        pbr = empty(f"{nm}_Brow{side}", V((sx, fsurf(sx), bz + 0.6)), col=COL_CHARS, parent=head)
        f = Face(head, "brow")
        f.line([(sx - 0.09, bz - 0.006 * (1 if sx < 0 else -1)), (sx + 0.09, bz + 0.006 * (1 if sx < 0 else -1))], M_INK, r=0.024)
        ba = empty(f"{nm}_BrowAcc{side}", V((0, 0, 0)), col=COL_CHARS, parent=pbr)  # emphasis layer (talk_face)
        adopt(f.objs, ba, (sx, fsurf(sx), bz + 0.6))
        rig["browAcc" + side], rig["eyeAcc" + side] = ba, ea
        rig["eye" + side], rig["blink" + side], rig["spark" + side], rig["brow" + side] = pe, pb, sp, pbr
    for k, fn in MOUTHS.items():
        f = Face(head, "m_" + k); fn(f); rig["mouths"][k] = f.objs
        vis(f.objs, 1, False)
    rig["cur_m"] = None
    return rig


# expression presets: (browL z, browL tilt, browR z, browR tilt, eye width, eye height)   tilt>0 = angry (inner ends down)
EX = {
    "neutral":  (0.0, 0.0, 0.0, 0.0, 1.0, 1.0),
    "curious":  (0.0, 0.04, 0.075, -0.12, 1.04, 1.08),
    "question": (0.05, -0.08, 0.08, -0.1, 1.08, 1.12),
    "excited":  (0.065, -0.1, 0.065, -0.1, 1.12, 1.16),
    "lean_in":  (-0.01, 0.1, 0.03, 0.02, 1.0, 0.78),
    "ominous":  (-0.035, 0.22, -0.03, 0.2, 1.0, 0.6),
    "sly":      (-0.02, 0.14, 0.045, -0.02, 1.0, 0.68),
    "content":  (0.03, -0.12, 0.03, -0.12, 1.0, 0.82),
    "notice":   (0.04, -0.04, 0.05, -0.06, 1.05, 1.08),
    "reading":  (-0.005, 0.05, -0.005, 0.05, 1.0, 0.92),
    "annoyed":  (-0.035, 0.24, -0.01, 0.12, 1.0, 0.68),
    "effort":   (-0.045, 0.3, -0.045, 0.3, 1.0, 0.55),
    "smug":     (-0.015, 0.1, 0.05, -0.05, 1.0, 0.72),
}


EXPR_RAMP = 4          # frames an expression change takes (23 Nov: without a hold key the face morphed over the whole gap)


def _hold_before(ob, path, frame, n):
    """Key the channel's current value n frames before `frame` (unless a key already sits in that span), so the change
    happens in n frames instead of creeping across the whole gap since the previous key."""
    for fc in _fcurves(ob):
        if fc.data_path != path or not len(fc.keyframe_points): continue
        if any(frame - n <= k.co.x < frame for k in fc.keyframe_points): continue
        if min(k.co.x for k in fc.keyframe_points) >= frame - n: continue
        v = fc.evaluate(frame - n)
        kp = fc.keyframe_points.insert(frame - n, v); kp.interpolation = "BEZIER"


def expr(rig, frame, key, interp="BEZIER", ramp=None):
    lz, lt, rz, rt, ew, eh = EX[key]; n = EXPR_RAMP if ramp is None else ramp
    for side, z, tilt in (("L", lz, lt), ("R", rz, -rt)):
        b = rig["brow" + side]; base = b.get("bz0")
        if base is None: b["bz0"] = base = b.location.z
        if interp != "CONSTANT" and n:
            for ob, path in ((b, "location"), (b, "rotation_euler"), (rig["eye" + side], "scale")): _hold_before(ob, path, frame, n)
        kf(b, "location", frame, base + z, index=2, interp=interp)
        kf(b, "rotation_euler", frame, (0, tilt, 0), interp=interp)
        kf(rig["eye" + side], "scale", frame, (ew, 1, eh), interp=interp)


def blink(rig, frame, closed=2):
    for side in ("L", "R"):
        b = rig["blink" + side]
        kf(b, "scale", frame - 1, (1, 1, 1)); kf(b, "scale", frame + 1, (1, 1, 0.06))
        kf(b, "scale", frame + 1 + closed, (1, 1, 0.06)); kf(b, "scale", frame + 3 + closed, (1, 1, 1))


def eyes_closed(rig, f0, f1):
    for side in ("L", "R"):
        b = rig["blink" + side]
        kf(b, "scale", f0 - 2, (1, 1, 1)); kf(b, "scale", f0, (1.05, 1, 0.06))
        kf(b, "scale", f1, (1.05, 1, 0.06)); kf(b, "scale", f1 + 3, (1, 1, 1))


def sparkle(rig, f_on, f_off):
    for side in ("L", "R"):
        for i, pv in enumerate(rig["spark" + side]):
            kf(pv, "scale", f_on - 1, (0, 0, 0))
            kf(pv, "scale", f_on + 3, (1.25, 1.25, 1.25)); kf(pv, "scale", f_on + 6, (0.95, 0.95, 0.95))
            fr = f_on + 9
            k = 0
            while fr < f_off - 4:                                # gentle twinkle, no flicker
                sc = 1.0 + (0.1 if (k + i) % 2 == 0 else -0.06)
                kf(pv, "scale", fr, (sc, sc, sc)); kf(pv, "rotation_euler", fr, (0, R(8 if (k + i) % 2 else -8), 0))
                fr += 9; k += 1
            kf(pv, "scale", f_off - 2, (1.0, 1.0, 1.0)); kf(pv, "scale", f_off + 2, (0, 0, 0))


def mouth(rig, frame, key):
    if rig["cur_m"] == key: return
    if rig["cur_m"]: vis(rig["mouths"][rig["cur_m"]], frame, False)
    vis(rig["mouths"][key], frame, True); rig["cur_m"] = key


# ------------------------------------------------------------------ lip-sync from the speech itself (visemes.py codes)
# One code per frame from the prep script's phone alignment: X rest, M closed (M B P), T teeth-on-lip (F V), U pucker,
# O round, A open, E spread, H half. Mapped onto the existing mouth shapes per speaking style; loudness picks between the
# full and the softer shape so unstressed syllables don't gape.
VIS_MOUTH = {
    "calm":    {"M": "M", "T": "teeth", "U": "small_o", "O": "O", "A": "A", "E": "E", "H": "half"},
    "excited": {"M": "M", "T": "teeth", "U": "small_o", "O": "O", "A": "grin_open", "E": "grin_open", "H": "half"},
    "whisper": {"M": "M", "T": "half", "U": "small_o", "O": "small_o", "A": "half", "E": "half", "H": "half"},
}
VIS_SOFT = {"A": "H", "E": "H", "O": "U"}       # quiet frame -> next-smaller shape
VIS_KEEP = {"H": 0, "X": 1, "T": 2, "U": 3, "E": 4, "O": 5, "A": 6, "M": 7}     # merge order for 1-frame shapes
VIS_OPEN = {"X": 0, "M": 0, "U": 1, "T": 1, "H": 2, "E": 2, "O": 3, "A": 4}
LIP_LEAD = 1            # mouths land one frame before the sound (animators' rule; reads as in sync)


def vis_clean(codes):
    """Readable 24 fps mouth timing: every shape holds 2+ frames (no chatter), closures (M) are never dropped,
    wide-open shapes get a half-open in-between coming from / going to closed."""
    c = list(codes)
    for _ in range(len(c)):                                 # merge one 1-frame run at a time, least important first
        runs = []; i = 0
        while i < len(c):
            j = i
            while j + 1 < len(c) and c[j + 1] == c[i]: j += 1
            runs.append((c[i], i, j)); i = j + 1
        single = [k for k, (code, i, j) in enumerate(runs) if i == j and 0 < k < len(runs) - 1]
        if not single: break
        done = False
        for k in sorted(single, key=lambda k: VIS_KEEP[runs[k][0]]):
            code, i, _ = runs[k]; prv, nxt = runs[k - 1], runs[k + 1]
            if code == "M":                                 # 1-frame closure: steal a frame from a neighbour with 3+
                donor = max((r for r in (prv, nxt) if r[0] != "X" and r[2] - r[1] >= 2), key=lambda r: r[2] - r[1], default=None)
                if donor is None: continue
                c[i - 1 if donor is prv else i + 1] = "M"; done = True; break
            best = min((prv, nxt), key=lambda r: (abs(VIS_OPEN[r[0]] - VIS_OPEN[code]), -(r[2] - r[1])))
            c[i] = best[0]; done = True; break
        if not done: break
    for i in range(1, len(c) - 3):                          # closed -> A A A A  becomes  closed -> H A A A
        if VIS_OPEN[c[i - 1]] == 0 and c[i:i + 4] == ["A"] * 4: c[i] = "H"
    for i in range(3, len(c) - 1):                          # A A A A -> closed  becomes  A A A H -> closed
        if VIS_OPEN[c[i + 1]] == 0 and c[i - 3:i + 1] == ["A"] * 4: c[i] = "H"
    return "".join(c)


def lipsync(rig, f0, f1, segs, who=None):
    """segs: list of (frame, rest_mouth, style). Uses the speech-driven codes in ENV (from visemes.py via the prep script)
    when present, else falls back to the old loudness/brightness flap."""
    vis = ENV.get("vis", {}).get(who) if who else ENV.get("vis_all")
    if not vis: return _lipsync_env(rig, f0, f1, segs)
    rms = ENV.get("rms") or [1.0] * len(vis)
    peak = max(rms[max(0, f0 - 1):f1] or [1]) or 1
    lo = max(1, f0 - 1); hi = min(len(vis), f1 + LIP_LEAD)
    sty = lambda fr: [sg for sg in segs if sg[0] <= fr][-1] if any(sg[0] <= fr for sg in segs) else segs[0]
    raw = []                                                # raw[k] is frame lo + k
    for i in range(lo - 1, hi + 1):
        c = vis[i] if i < len(vis) else "X"
        if c in VIS_SOFT and sty(i + 1 - LIP_LEAD)[2] != "excited" and i < len(rms) and rms[i] / peak < 0.3:
            c = VIS_SOFT[c]                                 # quiet syllable -> softer shape
        raw.append(c)
    codes = vis_clean(raw)
    log = rig.setdefault("lip_log", [])
    for fr in range(max(1, f0 - LIP_LEAD), f1 + 1):         # the lead may open the mouth a frame before the line window
        _, rest, style = sty(fr)
        k = fr + LIP_LEAD - lo
        c = codes[k] if 0 <= k < len(codes) else "X"
        m = rest if c == "X" else VIS_MOUTH.get(style, VIS_MOUTH["calm"])[c]
        if m != rig["cur_m"]: mouth(rig, fr, m); log.append((fr, m))


def check_lipsync(rigs):
    """QA: mouths that show for a single frame (chatter) or swap more than 8 times a second. Returns problems."""
    probs = []
    for nm_, rig in rigs.items():
        log = sorted(set(rig.get("lip_log", [])))
        for (fa, ma), (fb, mb) in zip(log, log[1:]):
            if fb - fa == 1 and ma != "M" and not (ma == "half" and mb in ("A", "grin_open")): probs.append((nm_, "1-frame mouth", fa, ma))
        for i in range(len(log) - 8):
            if log[i + 8][0] - log[i][0] < 24: probs.append((nm_, "chatter >8 swaps/s", log[i][0])); break
    return probs


def _lipsync_env(rig, f0, f1, segs):
    """Legacy (pre 23 Nov): mouth shapes from loudness + brightness; used only when the env has no viseme track."""
    rms, cen = ENV["rms"], ENV["cen"]
    peak = max(rms[f0 - 1:f1]) or 1
    held = 0
    for fr in range(f0, f1 + 1):
        seg = [sg for sg in segs if sg[0] <= fr][-1]
        rest, style = seg[1], seg[2]
        lvl = rms[fr - 1] / peak if fr - 1 < len(rms) else 0
        c = cen[fr - 1] if fr - 1 < len(cen) else 0
        # Joel 22 Nov 23:49: mouths must read clearly -> open shapes come in earlier and stay bigger
        if style == "whisper":
            m = rest if lvl < 0.04 else ("small_o" if c < 1600 else "half") if lvl < 0.14 else ("O" if c < 1300 else "A")
        elif lvl < 0.07: m = rest
        elif lvl < 0.2: m = "M" if (fr // 3) % 4 == 3 else "half"
        elif style == "excited": m = "grin_open" if c > 1700 else ("O" if c < 1100 else "A")
        else: m = ("E" if c > 1800 else "A") if (fr // 2) % 3 else "O"
        if held > 0 and m != rig["cur_m"] and not (rig["cur_m"] or "").startswith("rest"):
            held -= 1; continue
        if m != rig["cur_m"]:
            mouth(rig, fr, m); held = 1


def _nod_shape(d):
    """Head-nod pulse around a stressed syllable at d = 0: eases up over 4 frames, peaks at +1, dips to -0.15 and
    settles by +10. Zero speed at both ends (23 Nov: the old 2-frame keyed nod snapped)."""
    if d < -3 or d > 10: return 0.0
    if d <= 1:
        u = (d + 3) / 4.0; return u * u * (3 - 2 * u)
    w = (d - 1) / 9.0
    return 0.5 * (1 + math.cos(math.pi * w)) - 0.15 * math.sin(math.pi * w) ** 2


BROW_LIFT, EYE_WIDEN = 0.032, 0.07     # talk_face: subtle on purpose ("too much salt ruins the dish")


def _widen_shape(d):
    """Eye-widen pulse: in over 3 frames, holds, eases out by +16. Zero speed at both ends."""
    if d < -3 or d > 16: return 0.0
    if d <= 0:
        u = (d + 3) / 3.0; return u * u * (3 - 2 * u)
    if d <= 6: return 1.0
    u = (d - 6) / 10.0; return 1 - u * u * (3 - 2 * u)


def talk_face(rig, hits, levels):
    """Brows lift on stressed syllables (the same hits the head nods on), eyes widen once on the line's loudest word.
    Keyed per frame on separate layers (BrowAcc/EyeAcc) so expr() keys never fight it. Story-agnostic, automatic."""
    if not hits or "browAccL" not in rig: return
    top = max(levels); a = min(hits) - 3; b = max(hits) + 16
    strong = [(h, v) for h, v in zip(hits, levels) if v >= 0.65 * top]
    big = max(zip(hits, levels), key=lambda t: t[1])[0]
    def cur(ob, path, i, fr, dflt):                         # windows of neighbouring lines add up instead of cutting
        fc = next((c for c in _fcurves(ob) if c.data_path == path and c.array_index == i), None)
        return fc.evaluate(fr) if fc else dflt
    for side in ("L", "R"):
        ba, ea = rig["browAcc" + side], rig["eyeAcc" + side]
        old = {fr: (cur(ba, "location", 2, fr, 0.0), cur(ea, "scale", 0, fr, 1.0), cur(ea, "scale", 2, fr, 1.0)) for fr in range(a, b + 1)}
        for fr in range(a, b + 1):
            lift = BROW_LIFT * min(1.0, sum(_nod_shape(fr - h) * (0.6 + 0.4 * v / top) for h, v in strong))
            w = EYE_WIDEN * _widen_shape(fr - big); z, sx, sz = old[fr]
            kf(ba, "location", fr, min(z + lift, BROW_LIFT * 1.2), index=2)
            kf(ea, "scale", fr, (min(sx + w * 0.5, 1 + EYE_WIDEN), 1, min(sz + w, 1 + EYE_WIDEN * 1.2)))


def accents(P, rig, f0, f1, nod=5.5, pop=0.03):
    """Head nods on stressed syllables (local loudness peaks), ADDED on top of whatever the head already does and keyed on
    every frame of the window, so overlapping nods sum smoothly instead of fighting each other's keys."""
    rms = ENV["rms"]; peak = max(rms[f0 - 1:f1]) or 1
    sm = [sum(rms[max(0, i - 1):i + 2]) / 3 for i in range(len(rms))]
    last = -99; hits = []
    for fr in range(f0 + 1, f1 - 1):
        v = sm[fr - 1] / peak
        if v > 0.5 and sm[fr - 1] >= sm[fr - 2] and sm[fr - 1] >= sm[fr] and fr - last >= 6:
            hits.append(fr); last = fr
    if not hits: return hits
    talk_face(rig, hits, [sm[h - 1] / peak for h in hits])
    hd = P["head"]; a = min(hits) - 3; b = max(hits) + 10
    hd.keyframe_insert("rotation_euler", frame=a, index=0)
    fc = next(c for c in _fcurves(hd) if c.data_path == "rotation_euler" and c.array_index == 0)
    base = {fr: fc.evaluate(fr) for fr in range(a, b + 1)}
    for fr in range(a, b + 1):
        add = sum(_nod_shape(fr - h) for h in hits)
        kp = fc.keyframe_points.insert(fr, base[fr] + R(nod) * add, options={"FAST"}); kp.interpolation = "BEZIER"
    fc.update()
    return hits


def make_milo():
    S = new_set(); skin = (234, 184, 146); rng = RNG(42)
    d_hoodie(S, (226, 156, 32), rng, skin)
    t = S["Torso"]; x0, y0, x1, y1 = t.reg("front"); cx = (x0 + x1) / 2
    t.d.ellipse((cx - 26, t.zrow(1.18) - 26, cx + 26, t.zrow(1.18) + 26), fill=(20, 20, 24))
    t.d.polygon([(cx - 14, t.zrow(1.12)), (cx + 14, t.zrow(1.12)), (cx + 20, t.zrow(0.82)), (cx - 20, t.zrow(0.82))], fill=(20, 20, 24))
    b_trousers(S, (34, 44, 82), rng, kind="jeans")
    for k in LEGS: shoes(S[k], (248, 248, 248), (214, 52, 52))
    finish(S, rng)
    P = build_body("Milo", skin, S)
    add_men_hair(P, "M4", random.Random(8), colour=(70, 44, 30))
    root = P["root"]; brass = mat("Brass2", (214, 168, 64), rough=0.3, metallic=0.9)
    tube("KeyCord", [(-0.42, 0.42, 4.02), (-0.2, 0.53, 3.8), (0, 0.555, 3.72), (0.2, 0.53, 3.8), (0.42, 0.42, 4.02)], 0.022,
         mat("Cord", (30, 30, 30)), root)
    disc("KeyBow", 0.24, 0.05, V((0, 0.57, 3.62)), brass, root)
    rpart("KeyShaft", (0.065, 0.045, 0.32), V((0, 0.57, 3.36)), brass, root, r=0.015)
    return P


def make_dan():
    S = new_set(); skin = (196, 140, 104); rng = RNG(77)
    d_button_shirt(S, (118, 160, 214), rng, skin)
    b_trousers(S, (186, 164, 124), rng, kind="chinos")
    s_shoes(S, "trainers", (90, 70, 56), rng)
    finish(S, rng)
    P = build_body("Dan", skin, S)
    add_hair4(P, "X1", random.Random(3), colour=(36, 26, 22))
    return P

