"""
补全场景设置：相机 + 世界背景
（v6 材质脚本专注材质，场景单独配置）
"""
import bpy
import math
import os


def setup_camera():
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA':
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.camera_add(location=(0, -6.2, 1.15))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.data.lens = 55
    # 直接朝向角色中心
    cam.rotation_euler = (math.radians(90), 0, 0)

    bpy.context.scene.camera = cam

    # 用约束精确对准
    body = bpy.data.objects.get("Body")
    if body:
        c = cam.constraints.new(type='TRACK_TO')
        c.target = body
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'
    return cam


def setup_world():
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is None:
        bg = world.node_tree.nodes.new('ShaderNodeBackground')
        out = world.node_tree.nodes.get('World Output')
        if out:
            world.node_tree.links.new(bg.outputs['Background'], out.inputs['Surface'])
    bg.inputs['Color'].default_value = (0.87, 0.89, 0.93, 1.0)
    bg.inputs['Strength'].default_value = 1.0


def setup_render():
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x = 1080
    s.render.resolution_y = 1080
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    try:
        s.view_settings.view_transform = 'Standard'
    except Exception:
        pass


def main():
    print("配置场景：相机 + 世界 + 渲染设置")
    setup_render()
    setup_world()
    cam = setup_camera()
    print(f"  相机: {cam.name} 位置={tuple(round(v,2) for v in cam.location)}")
    print(f"  引擎: {bpy.context.scene.render.engine}")
    print(f"  分辨率: {bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}")

    out = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\models\chiikawa_toon.blend"
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"  已保存: {out}")


if __name__ == "__main__":
    main()
