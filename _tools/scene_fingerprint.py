# scene_fingerprint.py - proves a refactor changed nothing: builds a part script, hashes the whole scene (objects,
# transforms, every keyframe, materials, lights, camera, render settings) and the check output.
#   python3 _tools/scene_fingerprint.py <partN.py> <out.json>          (run from the scripts folder; FORCE not needed)
#   python3 _tools/scene_fingerprint.py --cmp <old.json> <new.json>     -> per-category same/diff + the first differences
# Use before/after any scene_kit.py / engine change: build every part with the old and new code and compare.
import sys, json
if sys.argv[1] == "--cmp":
    sys.argv = sys.argv[1:]
    a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
    print({k: a["summary"][k] == b["summary"][k] for k in a["summary"]})
    for cat in ("objs", "mats", "lights", "cams"):
        A, B = a[cat], b[cat]
        only_a = sorted(set(A) - set(B)); only_b = sorted(set(B) - set(A))
        diff = [k for k in A if k in B and A[k] != B[k]]
        if only_a or only_b or diff:
            print(cat, "only_old", only_a[:8], "only_new", only_b[:8], "diff", len(diff), diff[:8])
            for k in diff[:3]:
                for f in A[k]:
                    if A[k][f] != B[k][f]: print("   ", k, f, str(A[k][f])[:300], "|||", str(B[k][f])[:300])
    for k in a["scene"]:
        if a["scene"][k] != b["scene"][k]: print("scene", k, str(a["scene"][k])[:200], "->", str(b["scene"][k])[:200])
    print("log same:", a["summary"]["log"] == b["summary"]["log"])

else:
    import os, hashlib, io, contextlib
    script, out = sys.argv[1], sys.argv[2]
    g = {"__name__": "__main__", "__file__": script}
    log = io.StringIO(); code = "ok"
    try:
        with contextlib.redirect_stdout(log):
            exec(compile(open(script).read(), script, "exec"), g)
    except SystemExit as e: code = "exit:%s" % e
    import bpy
    R = lambda v, n=4: round(float(v), n) + 0.0
    def vec(v, n=4): return [R(x, n) for x in v]
    def H(o): return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()
    def fcs(idb):
        out = []
        ad = getattr(idb, "animation_data", None)
        if not ad or not ad.action: return out
        act = ad.action
        curves = []
        try: curves = list(act.fcurves)
        except Exception: pass
        if not curves:
            try:
                for l in act.layers:
                    for st in l.strips:
                        for cb in st.channelbags: curves += list(cb.fcurves)
            except Exception: pass
        for c in curves:
            out.append([c.data_path, c.array_index, [[R(k.co.x), R(k.co.y), k.interpolation, k.easing, R(k.handle_left.y), R(k.handle_right.y)] for k in c.keyframe_points]])
        return sorted(out, key=lambda x: (x[0], x[1]))
    s = bpy.context.scene
    s.frame_set(1)                      # static values (hide_render, energy...) evaluated at the same frame
    objs = {}
    for o in bpy.data.objects:
        d = {"t": o.type, "p": o.parent.name if o.parent else None, "loc": vec(o.location), "rot": vec(o.rotation_euler), "sc": vec(o.scale),
             "hr": o.hide_render, "data": o.data.name if o.data else None, "mats": [m.material.name if m.material else None for m in o.material_slots],
             "anim": fcs(o), "vis": [getattr(o, a, None) for a in ("visible_camera", "visible_glossy", "visible_diffuse", "visible_shadow")]}
        if o.type == "MESH": d["mesh"] = H([vec(v.co, 3) for v in o.data.vertices]); d["nf"] = len(o.data.polygons)
        objs[o.name] = d
    mats = {}
    for m in bpy.data.materials:
        d = {"anim": fcs(m)}
        if m.node_tree:
            d["nodes"] = sorted([n.name, n.bl_idname, [str(getattr(i, "default_value", None) if not hasattr(getattr(i, "default_value", None), "__len__") else vec(i.default_value)) for i in n.inputs]] for n in m.node_tree.nodes)
            d["anim"] += fcs(m.node_tree)
        mats[m.name] = d
    lights = {l.name: {"e": R(l.energy), "c": vec(l.color), "anim": fcs(l), "ty": l.type} for l in bpy.data.lights}
    cams = {c.name: {"lens": R(c.lens), "anim": fcs(c)} for c in bpy.data.cameras}
    scene = {"fs": s.frame_start, "fe": s.frame_end, "fps": s.render.fps, "res": [s.render.resolution_x, s.render.resolution_y], "eng": s.render.engine,
             "samples": s.cycles.samples, "dev": s.cycles.device, "exp": R(s.view_settings.exposure), "anim": fcs(s), "mb": s.render.use_motion_blur,
             "filepath": s.render.filepath, "rq": [str(getattr(s.cycles, a, None)) for a in ("denoising_input_passes", "denoising_prefilter", "max_bounces", "diffuse_bounces", "glossy_bounces", "adaptive_threshold", "use_adaptive_sampling", "sample_clamp_indirect", "caustics_reflective", "use_light_tree")], "cam": s.camera.name if s.camera else None, "denoiser": str(getattr(s.cycles, "denoiser", "")),
             "world": fcs(s.world) + (fcs(s.world.node_tree) if s.world and s.world.node_tree else []) if s.world else None,
             "comp": H(sorted([n.name, n.bl_idname] for n in s.compositing_node_group.nodes)) if getattr(s, "compositing_node_group", None) else None}
    images = sorted(i.name for i in bpy.data.images)
    lines = [l for l in log.getvalue().splitlines() if l.startswith(("FACE CHECK", "SHOTLIST", "SHOT", "MOTION", "FRAMING", "DONE", "check", "CHECK", "OK", "POP", "CHATTER", "OFF", "CROP", "DRIFT", "SAME"))]
    res = {"code": code, "n_obj": len(objs), "objs": H(objs), "mats": H(mats), "lights": H(lights), "cams": H(cams), "scene": H(scene), "images": H(images), "log": lines}
    json.dump({"summary": res, "objs": objs, "mats": mats, "lights": lights, "cams": cams, "scene": scene, "images": images, "fulllog": log.getvalue().splitlines()}, open(out, "w"), default=str)
    print(json.dumps({k: v for k, v in res.items() if k != "log"}, indent=0)); print("\n".join(lines[-30:]))
