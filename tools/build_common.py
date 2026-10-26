"""Original CC0 modular tile and hazard models; run inside Blender."""
import bpy, math, random, json, zlib, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models/common'; OUT.mkdir(parents=True,exist_ok=True)
TEX=ROOT/'tools/textures'; TEX.mkdir(parents=True,exist_ok=True)
random.seed(309)

def rgba(h):
    rgb=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)+(1,)

def texture(name,color,kind):
    n=256; base=[int(color[i:i+2],16) for i in (1,3,5)]; rows=[]; rng=random.Random(name)
    for y in range(n):
        row=bytearray()
        for x in range(n):
            noise=rng.random()-.5
            if kind=='stone':
                v=.96+.026*math.sin(x*.06+math.sin(y*.024)*2)*math.cos(y*.071)+noise*.065
                v-=.12*max(0,1-abs(math.sin(x*.017+y*.009+math.sin(y*.035)*.2)))**40
            elif kind=='wood': v=.94+.035*math.sin(y*.54+math.sin(x*.025)*2)+noise*.025
            elif kind=='biscuit': v=.90+.05*math.sin(x*.031)*math.sin(y*.05)+noise*.09
            elif kind=='sugar': v=.91+noise*.17
            else: v=.98+noise*.025
            rgb=[max(0,min(255,round(c*v))) for c in base]
            if kind=='frost' and rng.random()<.004: rgb=[213,166,115] if rng.random()<.6 else [239,183,189]
            row.extend(rgb+[255])
        rows.append(b'\x00'+bytes(row))
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',n,n,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
    path=TEX/(name+'.png'); path.write_bytes(data); return path

def mat(name,color,rough=.72,metal=0,tex=None):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=rgba(color);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if tex:
        p.inputs['Base Color'].default_value=(1,1,1,1)
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(tex),check_existing=True);m.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
    return m

def box(name,loc,size,m,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if bevel:
        b=o.modifiers.new('Soft hand-finished edges','BEVEL');b.width=bevel;b.segments=3
        bpy.ops.object.modifier_apply(modifier=b.name)
        for f in o.data.polygons:f.use_smooth=True
        w=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=w.name)
    return o

def ball(name,loc,scale,m,seg=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    return o

def cyl(name,loc,r,depth,m,axis='Z',vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    b=o.modifiers.new('Edge bevel','BEVEL');b.width=min(.015,r*.12);b.segments=2;bpy.ops.object.modifier_apply(modifier=b.name)
    for f in o.data.polygons:f.use_smooth=True
    return o

def wire(name,points,r,m):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=r;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(m)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o

def leaf(name,loc,angle,m,length=.28,width=.12):
    x,y,z=loc;verts=[(0,0,0),(-width/2,length*.42,.025),(0,length,.015),(width/2,length*.42,.025),(0,length*.46,.045)]
    verts=[(x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),z+c) for a,b,c in verts]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

records=[]
def export(name,role):
    # Join static pieces by material; retain a compact one-root, Y-up GLB.
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];groups={}
    for o in objects:groups.setdefault(o.data.materials[0].name,[]).append(o)
    for group in groups.values():
        bpy.ops.object.select_all(action='DESELECT')
        for o in group:o.select_set(True)
        bpy.context.view_layer.objects.active=group[0]
        if len(group)>1:bpy.ops.object.join()
    bpy.ops.object.select_all(action='SELECT');bpy.context.scene.unit_settings.system='METRIC'
    for o in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_extras=True)
    records.append({'id':name,'path':'models/common/'+name+'.glb','role':role,'source':'Original modular models authored for this project','license':'CC0-1.0','units':'meters','up':'Y'})

stone=mat('Warm limestone','#ded4ad',tex=texture('stone-cream','#e7dab6','stone'))
moss=mat('Sage stone','#aab98a',tex=texture('stone-sage','#b2c397','stone'))
body=mat('Stone body','#b6a487',tex=texture('stone-body','#b9aa8d','stone'))
cake=mat('Baked biscuit','#cf9f65',tex=texture('baked-biscuit','#d9ad77','biscuit'))
cream=mat('Vanilla frosting','#fff0ce',.49,tex=texture('frost-vanilla','#fff0d4','frost'))
pink=mat('Strawberry frosting','#edb3c2',.49,tex=texture('frost-strawberry','#f1bdc9','frost'))
wood=mat('Beech grain','#d1a574',.65,tex=texture('beech','#d9b17c','wood'))
mint=mat('Mint handles','#a7c5b6',.48)
red=mat('Strawberry red','#df4050',.54);green=mat('Leaf green','#658d50',.9);seed=mat('Strawberry seeds','#e3bc72',.8)
steel=mat('Satin stainless steel','#b5bcc2',.24,.88);rose=mat('Mixer painted metal','#dd9caa',.4,.12);dark=mat('Dark detailing','#66534d',.75)

for name,top in [('tile_garden_cream',stone),('tile_garden_sage',moss)]:
    clear();box('tile_body',(0,0,-.155),(.96,.96,.24),body,.035);box('tile_surface',(0,0,-.043),(.97,.97,.086),top,.032)
    export(name,'tile;1x1 grid cell;top surface at Y=0;pivot at cell top center')
for name,top in [('tile_kitchen_vanilla',cream),('tile_kitchen_strawberry',pink)]:
    clear();box('biscuit_body',(0,0,-.16),(.95,.95,.24),cake,.045);box('frosting_surface',(0,0,-.043),(.97,.97,.086),top,.038)
    for yy in [-.468,.468]:box('biscuit_edge',(0,yy,-.17),(.82,.012,.018),wood,.005)
    export(name,'tile;1x1 grid cell;top surface at Y=0;pivot at cell top center')

clear();cyl('rolling_pin_barrel',(0,0,0),.145,1.38,wood,'X',40)
for x in [-.89,.89]:cyl('mint_handle',(x,0,0),.07,.40,mint,'X',24)
for x in [-.71,.71]:cyl('handle_collar',(x,0,0),.09,.05,mint,'X',24)
export('hazard_rolling_pin','rolling obstacle;long axis X;pivot at center')

clear();sugar=mat('Sugar grain','#fff9e7',.95,tex=texture('sugar-grain','#fffbea','sugar'));box('sugar_cube',(0,0,.30),(.60,.60,.60),sugar,.045)
export('hazard_sugar_cube','falling sugar bomb;bottom Y=0')

clear();verts=[];uv=[];faces=[];N=22;M=16
for j in range(M+1):
    t=j/M;r=.28*math.sin(math.pi*t)**.65*(.55+.65*t);z=.70*t
    for i in range(N+1):
        a=i/N*math.tau;verts.append((r*math.cos(a),r*math.sin(a),z));uv.append((i/N,t))
        if j<M and i<N:q=j*(N+1)+i;faces.append((q,q+1,q+N+2,q+N+1))
me=bpy.data.meshes.new('Strawberry organic body');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('strawberry_body',me);bpy.context.collection.objects.link(o);o.data.materials.append(red)
for p in me.polygons:p.use_smooth=True
for row in range(1,7):
    t=.1+row*.11;r=.28*math.sin(math.pi*t)**.65*(.55+.65*t)
    for k in range(9):
        a=k/9*math.tau+(row%2)*.34;ss=ball('seed',(r*math.cos(a)*1.008,r*math.sin(a)*1.008,t*.70),(.010,.010,.022),seed,8,4);ss.rotation_euler[1]=-.35*math.cos(a)
for i in range(6):leaf('calyx',(0,0,.665),i*math.tau/6,green,.24,.11)
cyl('fruit_stem',(0,0,.742),.025,.14,green,vertices=12)
export('hazard_strawberry','falling strawberry;bottom Y=0')

clear();rock=mat('Meteor charcoal','#534c43',.88);ember=mat('Meteor warm facets','#b85129',.8)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.36,location=(0,0,.36));o=bpy.context.object;o.name='meteor_rock';o.data.materials.append(rock);o.data.materials.append(ember)
for v in o.data.vertices:v.co*=random.uniform(.88,1.12)
for p in o.data.polygons:p.material_index=1 if random.random()<.16 else 0
export('hazard_meteor','falling rock;add fire trail, warnings and shockwaves at runtime')

clear();box('mixer_base',(0,0,.06),(.74,.72,.12),rose,.07);box('rear_column',(0,.23,.47),(.25,.29,.78),rose,.09);box('motor_head',(0,-.015,.94),(.48,.78,.27),rose,.12)
cyl('speed_dial',(.254,.11,.94),.055,.03,steel,'X',20)
# Open bowl made with outer and inner profiles, never a filled solid hemisphere.
profile=[(.04,.13),(.16,.14),(.27,.22),(.32,.36),(.33,.48),(.31,.49),(.30,.36),(.25,.23),(.15,.16),(.04,.16)];vv=[];ff=[];segments=40
for r,z in profile:
    for i in range(segments):a=i/segments*math.tau;vv.append((r*math.cos(a),-.10+r*math.sin(a),z))
for j in range(len(profile)-1):
    for i in range(segments):q=j*segments+i;n=j*segments+(i+1)%segments;ff.append((q,n,n+segments,q+segments))
me=bpy.data.meshes.new('bowl');me.from_pydata(vv,[],ff);me.update();o=bpy.data.objects.new('steel_bowl',me);bpy.context.collection.objects.link(o);o.data.materials.append(steel)
for p in me.polygons:p.use_smooth=True
cyl('whisk_spindle',(0,-.18,.65),.018,.31,steel,vertices=12)
for k in range(6):
    a=k*math.tau/6;points=[]
    for j in range(25):t=j/24*math.tau;r=.12*math.sin(t);points.append((r*math.cos(a),-.18+r*math.sin(a),.51+.16*math.cos(t)))
    wire('whisk_wire',points,.006,steel)
export('prop_stand_mixer','kitchen backdrop;bottom Y=0;static decorative mixer')

clear();petal=mat('Daisy ivory','#fff7dc',.84);center=mat('Daisy pollen','#dfb55b',.94)
for i in range(5):
    a=i*2.4;r=.10+.05*(i%2);x=math.cos(a)*r;y=math.sin(a)*r;h=.16+.03*(i%3)
    cyl('flower_stem',(x,y,h/2),.009,h,green,vertices=8)
    for k in range(5):
        t=k*math.tau/5;pp=ball('petal',(x+math.cos(t)*.045,y+math.sin(t)*.045,h),(.037,.018,.009),petal,8,4);pp.rotation_euler[2]=t
    ball('flower_center',(x,y,h+.011),(.023,.023,.012),center,10,5)
    leaf('ground_leaf',(x,y,.012),a,green,.15,.055)
export('prop_flower_patch','small decorative daisy clump;bottom Y=0')

(ROOT/'common-report.json').write_text(json.dumps({'author':'Original modular add-ons','license':'CC0-1.0','models':records},indent=2))
(ROOT/'licenses/common/Original-models-CC0.txt').write_text('Original tile, mixer and hazard models in models/common are dedicated to the public domain under CC0 1.0 Universal.\nhttps://creativecommons.org/publicdomain/zero/1.0/\nSource script: tools/build_common.py\nKenney character is separately licensed; see Kenney-Blocky-Characters-License.txt.\n')
print('COMMON_DONE',len(records))
