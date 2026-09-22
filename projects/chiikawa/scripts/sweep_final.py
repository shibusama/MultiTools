import bpy, os
BASE = r'D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa'
OUT = os.path.join(BASE, 'renders')
body = bpy.data.objects.get('Chiikawa_Body')
ramp = None
for m in body.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'VALTORGB':
                ramp = n; break
    if ramp: break
sc = bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=400; sc.render.resolution_y=400
sc.render.film_transparent=False
sc.frame_set(1)
for thr in [0.90, 0.93, 0.95]:
    for m in body.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type=='VALTORGB':
                n.color_ramp.elements[0].position = thr
    sc.render.filepath = os.path.join(OUT, f'_thr{int(thr*100)}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', thr)
