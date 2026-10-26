"""Validate standalone GLBs and generate the public catalog, without dependencies."""
from pathlib import Path
import json, struct, hashlib, math
R=Path(__file__).resolve().parents[1]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
I=[[int(i==j) for j in range(4)] for i in range(4)]
def transform(n):
    if 'matrix' in n:return [[n['matrix'][j*4+i] for j in range(4)] for i in range(4)]
    x,y,z,w=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1]*3);t=n.get('translation',[0]*3)
    q=[[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]]
    return [[q[i][j]*s[j] for j in range(3)]+[t[i]] for i in range(3)]+[[0,0,0,1]]
def read(path):
    raw=path.read_bytes();magic,v,size=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and v==2 and size==len(raw),str(path)
    off=12;parts={}
    while off<len(raw):
        length,kind=struct.unpack_from('<II',raw,off);off+=8;parts[kind]=raw[off:off+length];off+=length
    assert off==len(raw);j=json.loads(parts[0x4e4f534a]);binary=parts.get(0x004e4942,b'')
    for b in j.get('buffers',[]):assert not b.get('uri') and b['byteLength']<=len(binary)
    for image in j.get('images',[]):assert not image.get('uri') and 'bufferView' in image
    for view in j.get('bufferViews',[]):assert 0<=view.get('byteOffset',0)<=len(binary) and view.get('byteOffset',0)+view['byteLength']<=len(binary)
    for a in j.get('accessors',[]):
        assert a.get('count',0)>0
        for key in ['min','max']:assert all(math.isfinite(x) for x in a.get(key,[]))
    bounds=[[math.inf]*3,[-math.inf]*3];triangles=0;meshes=0;tiles=[]
    def walk(index,parent):
        nonlocal triangles,meshes
        n=j['nodes'][index];m=mul(parent,transform(n));name=n.get('name','')
        if name.startswith('tile_') and len(name)==10 and name[5:7].isdigit() and name[8:10].isdigit():tiles.append(name)
        if 'mesh' in n:
            meshes+=1
            for p in j['meshes'][n['mesh']]['primitives']:
                a=j['accessors'][p['attributes']['POSITION']]
                if p.get('mode',4)==4:triangles+=j['accessors'][p['indices']]['count']//3 if 'indices'in p else a['count']//3
                lo,hi=a.get('min',[0]*3),a.get('max',[0]*3)
                for x in [lo[0],hi[0]]:
                    for y in [lo[1],hi[1]]:
                        for z in [lo[2],hi[2]]:
                            v=[x,y,z,1];pt=[sum(m[i][k]*v[k] for k in range(4)) for i in range(3)]
                            for k in range(3):bounds[0][k]=min(bounds[0][k],pt[k]);bounds[1][k]=max(bounds[1][k],pt[k])
        for child in n.get('children',[]):walk(child,m)
    for n in j['scenes'][j.get('scene',0)]['nodes']:walk(n,I)
    for a in j.get('animations',[]):assert a.get('channels') and a.get('samplers')
    if path.parent.name=='stages':assert len(set(tiles))==144,(path.name,len(set(tiles)))
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':triangles,'meshNodes':meshes,'materials':len(j.get('materials',[])),'embeddedImages':len(j.get('images',[])),'externalDependencies':0,'bounds':{'min':bounds[0],'max':bounds[1]},'animations':[a.get('name','') for a in j.get('animations',[])],'tileNodes':len(set(tiles))}

source={}
for report in ['forest-report.json','kitchen-report.json']:
    for a in json.loads((R/report).read_text())['assets']:source[a.get('path',a.get('file'))]=a
for a in json.loads((R/'common-report.json').read_text())['models']:source[a['path']]=a
assets=[]
for f in sorted((R/'models').rglob('*.glb')):
    rel=f.relative_to(R).as_posix();group=f.parent.name;old=source.get(rel,{})
    a={'id':group+'/'+f.stem,'label':old.get('label',f.stem.replace('_',' ').replace('-',' ').title()),'group':group,'path':rel,'license':'CC0-1.0',**read(f)}
    for key in ['sourcePage','sourceRepository','originalFile','role','originalNode']:
        if key in old:a[key]=old[key]
    if f.name.startswith('player-'):
        a.update({'author':'Kenney','sourcePage':'https://kenney.nl/assets/blocky-characters','originalFile':'character-b.glb' if 'boy'in f.name else 'character-e.glb','recommendedScale':.5})
    if group=='forest':a.update({'author':'Kay Lousberg','sourcePage':'https://kaylousberg.itch.io/kaykit-forest'})
    if group=='stages':a.update({'note':'Editable static opening layout; 144 independent tile roots; player loaded separately. Includes no gameplay or lights.','tilePrefix':'tile_RR_CC','cellSize':1,'tileTopY':0,'up':'Y','spawnNode':'player_spawn'})
    assets.append(a)
result={'title':'Blox Survival GLB Pack','version':'1.0.0','created':'2026-10-26','assetCount':len(assets),'totalBytes':sum(a['bytes'] for a in assets),'maxChallengeSeconds':40,'models':assets}
(R/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'assets':len(assets),'bytes':result['totalBytes'],'largest':max(a['bytes'] for a in assets),'stages':[(a['path'],a['triangles'],a['tileNodes']) for a in assets if a['group']=='stages']},indent=2))
