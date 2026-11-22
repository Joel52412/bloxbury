# hair3.py - men's "fluffy messy" Roblox UGC-style hair: many thin pointed locks in
# several volume layers, messy top arches, wispy fringe, stray strands, optional curl tips.


def jitter(pts, rng, amt):
    out = [pts[0]]
    for p in pts[1:-1]:
        out.append(p + Vector((rng.uniform(-amt, amt), rng.uniform(-amt, amt), rng.uniform(-amt, amt) * 0.6)))
    out.append(pts[-1])
    return out


def curl_end(pts, r, side=1, turns=1.0):
    last, prev = pts[-1], pts[-2]
    d = (last - prev).normalized()
    o = Vector((d.y, -d.x, 0)).normalized() * side if abs(d.z) < 0.99 else Vector((1, 0, 0))
    out = list(pts)
    for j in range(1, 6):
        a = j / 5 * math.pi * 2 * turns
        out.append(last + d * r * math.sin(a) + o * r * (1 - math.cos(a)) + Vector((0, 0, r * 0.25 * j / 5)))
    return out


def messy(neck, rng, mats, vol=1.0, length=0.0, fringe_z=(0.8, 0.96), wave=0.0, curl=0.0, top_arches=12,
          strays=4, fringe_n=10, back_len=-28, thin=1.0, split=False):
    """mats: function(az) -> material (lets us do split two-tone)."""
    o = []
    shell(neck, mats(0), o, back=False, size=(1.26, 1.29, 0.72), z=1.02)
    o.append(ball("NapeShell", (1.2, 0.7, 0.62), Vector((0, -0.3, 0.86)), mats(0), neck))
    W = lambda w: w * thin

    def L(pts, w, th=0.08, m=None, n=20, wpow=2.0):
        o.append(lock(neck, pts, w, th, m or mats(0), n=n, wpow=wpow))

    # layer 1: base coverage, sides + back down to the nape
    for az in range(30, 331, 14):
        a = az + rng.uniform(-6, 6)
        el1 = back_len - length * 30 + rng.uniform(-8, 6) if 100 < az < 260 else -12 + rng.uniform(-6, 6)
        p = flow(a, 84, el1, vol=0.16 * vol, wave=wave, flick=0.03, sweep=rng.uniform(-12, 12))
        if curl: p = curl_end(p, curl * rng.uniform(0.7, 1.2), side=1 if az < 180 else -1)
        L(jitter(p, rng, 0.03), W(0.3), m=mats(a), n=24 if curl else 20)
    # layer 2: volume - puffier, shorter, tips flick out
    for az in range(0, 360, 17):
        a = az + rng.uniform(-8, 8)
        if abs(((a + 180) % 360) - 180) < 30: continue
        p = flow(a, 88, rng.uniform(5, 25), vol=0.3 * vol, flick=rng.uniform(0.03, 0.09), wave=wave * 0.6,
                 sweep=rng.uniform(-18, 18))
        L(jitter(p, rng, 0.04), W(0.26), m=mats(a))
    # messy top arches: rise up from the crown then fall in random directions
    for k in range(top_arches):
        a = rng.uniform(0, 360)
        c = surf(a, 86, 1.05)
        peak = surf(a, 80, 1.16 * vol + 0.04) + Vector((0, 0, 0.05 * vol))
        end = surf(a + rng.uniform(-25, 25), rng.uniform(35, 55), 1.14 * vol + 0.04)
        L([c, peak, end], W(rng.uniform(0.16, 0.24)), th=0.07, m=mats(a))
    # fringe: thin locks from the crown over the forehead, varied lengths, some crossing
    for i in range(fringe_n):
        x = -0.46 + i * (0.92 / max(1, fringe_n - 1)) + rng.uniform(-0.03, 0.03)
        xt = x + rng.uniform(-0.1, 0.12)
        z = rng.uniform(*fringe_z)
        pts = fringe_pts(x * 0.75, xt, z)
        if curl and rng.random() < 0.4: pts = curl_end(pts, curl * 0.6, side=1 if x > 0 else -1)
        L(jitter(pts, rng, 0.02), W(rng.uniform(0.17, 0.25)), th=0.07,
          m=mats(math.degrees(math.asin(max(-0.9, min(0.9, x / 0.6))))), n=22, wpow=1.6)
    # stray strands sticking out
    for k in range(strays):
        a = rng.uniform(0, 360); el = rng.uniform(40, 80)
        p0 = surf(a, el, 1.1 * vol); d = (p0 - HC).normalized()
        L([p0, p0 + d * 0.12 + Vector((0, 0, 0.03)), p0 + d * 0.2 + Vector((rng.uniform(-.08, .08), rng.uniform(-.08, .08), -0.03))],
          W(0.09), th=0.04, m=mats(a))
    if length > 0:   # extra back length (mullet / wavy full)
        for az in range(120, 241, 16):
            a = az + rng.uniform(-5, 5)
            p = flow(a, 70, -35, vol=0.14 * vol, hang=0.25 * length, wave=wave, flick=0.06)
            if curl: p = curl_end(p, curl, side=1 if az < 180 else -1)
            L(jitter(p, rng, 0.03), W(0.3), m=mats(a), n=24)
    return o


def _hmats(name, root, tip=None, split=None):
    m1 = hair_mat(name, root, tip)
    if not split:
        return lambda az: m1
    m2 = hair_mat(name + "_B", split[0], split[1])
    return lambda az: (m2 if math.sin(math.radians(az)) < 0 else m1)


MEN = {
    "M1": ("Fluffy messy (black)", dict(), ((22, 22, 26), (60, 60, 68))),
    "M2": ("Fluffy anime (ash)", dict(vol=1.12, top_arches=14, strays=6), ((170, 165, 168), (215, 212, 214))),
    "M3": ("Curly fluffy (blonde)", dict(wave=0.05, curl=0.07, vol=1.1, top_arches=14), ((214, 176, 120), (242, 220, 176))),
    "M4": ("Wavy full messy (brown)", dict(wave=0.06, length=1.0, vol=1.05), ((92, 58, 36), (140, 98, 64))),
    "M5": ("Split two-tone", dict(vol=1.05), ((24, 22, 26), (50, 48, 54)), ((226, 196, 150), (246, 226, 190))),
    "M6": ("Messy + curly ends", dict(curl=0.1, length=0.6, back_len=-40, fringe_z=(0.74, 0.92)), ((20, 20, 24), (54, 54, 60))),
}


def add_men_hair(P, key, rng, colour=None):
    spec = MEN[key]
    name, cfg, cols = spec[0], spec[1], spec[2]
    split = spec[3] if len(spec) > 3 else None
    root, tip = (colour, None) if colour else cols
    mats = _hmats("Hair" + key + P["root"].name, root, tip, None if colour else split)
    P["hair"][key] = messy(P["neck"], rng, mats, **cfg)
    return P["hair"][key]
