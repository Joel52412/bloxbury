# lookdev.py - CINEMATIC LOOK for every shot (Joel 22 Nov 22:10: "good lighting can make or break a scene").
# Post only, almost free to render: AgX + contrast look, a gentle bloom on practicals (lamps, door gap, torch, screens),
# a soft vignette, and a light split-tone (cool shadows, warm highlights). Lighting recipes (motivated key, low fill,
# rim for separation, warm/cool contrast) live in the scene scripts; this file only grades.
import bpy


def cinematic_look(scene=None, exposure=0.0, bloom=0.5, vignette=0.32, split=True, look="AgX - Medium High Contrast"):
    s = scene or bpy.context.scene
    s.view_settings.view_transform = "AgX"
    try: s.view_settings.look = look
    except Exception: pass
    s.view_settings.exposure = exposure
    ng = bpy.data.node_groups.get("CineLook") or bpy.data.node_groups.new("CineLook", "CompositorNodeTree")
    ng.nodes.clear()
    if not ng.interface.items_tree:
        ng.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput"); cur = gi.outputs[0]
    if bloom:
        g = N.new("CompositorNodeGlare")
        for k, v in (("Type", "Bloom"), ("Quality", "Medium"), ("Threshold", 0.9), ("Strength", bloom), ("Size", 0.5)):
            try: g.inputs[k].default_value = v
            except Exception: pass
        L.new(cur, g.inputs["Image"]); cur = g.outputs[0]
    if split:
        cb = N.new("CompositorNodeColorBalance")
        try:
            cb.inputs["Factor"].default_value = 1.0
        except Exception: pass
        for sock, val in (("Lift", (0.97, 1.0, 1.05, 1)), ("Gain", (1.03, 1.0, 0.96, 1))):   # cool shadows, warm highlights
            for i in cb.inputs:
                if i.name == sock and i.bl_idname == "NodeSocketColor": i.default_value = val
        L.new(cur, cb.inputs["Image"]); cur = cb.outputs[0]
    if vignette:
        em = N.new("CompositorNodeEllipseMask")
        em.inputs["Size"].default_value = (0.95, 0.98); em.inputs["Value"].default_value = 1.0
        bl = N.new("CompositorNodeBlur"); bl.inputs["Size"].default_value = (260, 260)
        L.new(em.outputs[0], bl.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = vignette
        L.new(cur, mx.inputs["A"])
        inv = N.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"; inv.inputs[1].default_value = 0.6; inv.inputs[2].default_value = 0.4
        L.new(bl.outputs[0], inv.inputs[0])                       # mask 0..1 -> 0.4..1.0 (corners never go black)
        L.new(inv.outputs[0], mx.inputs["B"])
        cur = mx.outputs["Result"]
    L.new(cur, go.inputs[0])
    s.compositing_node_group = ng
    s.render.use_compositing = True
    return ng
