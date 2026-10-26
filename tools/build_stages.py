"""Assemble editable 12x12 opening stages from the supplied CC0 GLBs."""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
(R/'models/stages').mkdir(parents=True,exist_ok=True)
(R/'previews').mkdir(exist_ok=True)

def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);return o

def bounds(objects):
    bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    return Vector([min(v[k] for v in pts) for k in range(3)]),Vector([max(v[k] for v in pts) for k in range(3)])

def clone_tree(src,parent=None):
    c=src.copy();bpy.context.collection.objects.link(c);c.parent=parent
    for child in src.children:clone_tree(child,c)
    return c

def dedup_images():
    canonical={}
    for image in list(bpy.data.images):
        if not image.packed_file:continue
        key=hashlib.sha256(image.packed_file.data).hexdigest()
        if key not in canonical:canonical[key]=image;continue
        for m in bpy.data.materials:
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type=='TEX_IMAGE' and n.image==image:n.image=canonical[key]

def stage(kind):
    clear();cache={};templates=[];root=empty(kind+'_stage');root['cell_size']=1.;root['rows']=12;root['columns']=12;root['tile_top_y']=0.;root['note']='Opening layout. Tiles are independent nodes, no solid floor underneath.'
    tiles=empty('tiles');tiles.parent=root;decor=empty('decor');decor.parent=root
    def put(path,name,pos,height=None,rotation=0,tile=False):
        if path not in cache:
            before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/path));objects=list(set(bpy.data.objects)-before)
            lo,hi=bounds(objects);t=empty('TEMPLATE_'+Path(path).stem)
            for o in objects:
                if o.parent is None:o.parent=t
            cache[path]=(t,lo,hi);templates.append(t)
        t,lo,hi=cache[path];scale=height/(hi.z-lo.z) if height else 1
        outer=empty(name);outer.location=pos;outer.rotation_euler.z=rotation;outer.parent=tiles if tile else decor
        c=clone_tree(t,outer);c.name=name+'_visual';c.scale=(scale,)*3
        if not tile:c.location=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))*scale
        return outer
    for row in range(12):
        for col in range(12):
            variant=('cream' if (row+col)%2==0 else 'sage') if kind=='forest' else ('vanilla' if (row+col)%2==0 else 'strawberry')
            prefix='garden' if kind=='forest' else 'kitchen'
            o=put(f'models/common/tile_{prefix}_{variant}.glb',f'tile_{row:02d}_{col:02d}',(col-5.5,5.5-row,0),tile=True)
            o['kind']='tile';o['row']=row;o['column']=col;o['grid_size']=1.
    spawn=empty('player_spawn');spawn.parent=root;spawn.location=(0,-1.5,.02);spawn['note']='Place separately loaded animated player here.'
    if kind=='forest':
        positions=[(-6.7,5.7,3.6),(6.7,5.8,3.3),(-7.0,1.8,2.8),(7.0,2.2,3.1),(-7.1,-2.7,2.5),(7.1,-2.5,2.6),(-4.2,7.0,3.7),(0,7.4,3.2),(4.0,7.0,3.5)]
        for i,(x,y,h) in enumerate(positions):put('models/forest/'+['tree-round-large','tree-flat-large','tree-fir-large'][i%3]+'.glb',f'tree_{i:02d}',(x,y,-.08),h,i*.71)
        for i in range(16):
            side=-1 if i%2 else 1;y=5.7-(i//2)*1.65
            put('models/forest/bush-round.glb',f'hedge_{i:02d}',(side*6.35,y,-.14),.65,i)
        for i in range(14):
            x=-5.8+i*.89
            for s in [-1,1]:
                put('models/forest/rock-angular.glb',f'edge_rock_{i}_{s}',(x,s*6.24,-.85),1.05,.3*i)
                put('models/common/prop_flower_patch.glb',f'flowers_{i}_{s}',(x,s*6.13,-.02),.31,.5*i)
        for i,(x,y) in enumerate([(-6.2,-5),(-6.2,-1),(-6.2,3),(6.2,-5),(6.2,-1),(6.2,3)]):put('models/forest/rock-round.glb',f'cliff_{i}',(x,y,-1.9),1.95,i*.7)
    else:
        put('models/common/prop_stand_mixer.glb','giant_mixer',(6.6,6.8,-.20),4.6,-.12)
        put('models/kitchen/strawberry-cake.glb','giant_cake',(-6.3,6.8,0),3.5,.15)
        put('models/kitchen/oven-stove.glb','giant_oven',(3.4,8.6,-.20),3.0,0)
        put('models/kitchen/fridge.glb','giant_fridge',(-3.1,8.7,-.20),4.1,0)
        put('models/kitchen/utensils-cup.glb','utensil_cup',(0,8.2,.0),2.4,.2)
        put('models/kitchen/ingredient-jar.glb','flour_jar',(-7,1.5,-.1),2.0,-.2)
        put('models/kitchen/kettle.glb','kettle',(7.0,1.7,-.1),1.9,-.2)
        put('models/kitchen/pink-donut.glb','donut',(-6.7,-3.7,-.1),.8,.2)
        put('models/kitchen/cupcake.glb','cupcake',(6.8,-3.4,-.1),1.4,.2)
        put('models/common/hazard_rolling_pin.glb','rolling_pin_display',(0,7.1,.18),.45,0)
        for i in range(15):
            x=-5.8+i*.83
            for s in [-1,1]:put('models/common/hazard_strawberry.glb',f'border_strawberry_{i}_{s}',(x,s*6.15,-.1),.31,i)
    # Remove original import templates, retaining the linked-mesh copies under stage nodes.
    for t in templates:
        for o in list(t.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.objects.remove(t,do_unlink=True)
    dedup_images();bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(R/f'models/stages/{kind}_stage.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_extras=True)
    # Render-only surroundings and lighting; not included in the model.
    world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=((.50,.68,.70,1) if kind=='forest' else (.78,.64,.61,1));world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-2.4));plane=bpy.context.object
    m=bpy.data.materials.new('preview_ground');m.diffuse_color=((.22,.48,.49,1) if kind=='forest' else (.86,.70,.61,1));plane.data.materials.append(m)
    for loc,power,size in [((-6,-7,15),2300,8),((8,3,12),1700,9),((-4,10,8),1000,7)]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,1,0))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(9,-15,23));cam=bpy.context.object;cam.rotation_euler=(Vector((0,1,.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=26;bpy.context.scene.camera=cam
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.filepath=str(R/f'previews/{kind}-stage.png')
    bpy.ops.render.render(write_still=True)
    print('STAGE_DONE',kind)

for name in ['forest','kitchen']:stage(name)
