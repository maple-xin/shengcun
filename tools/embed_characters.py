"""Embed Kenney's separate PNGs without changing any animation or geometry."""
import json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=R.parents[1]/'work/blox-common-intake/Models/GLB format'
for source,target in [('character-b.glb','player-boy.glb'),('character-e.glb','player-girl.glb')]:
    raw=(S/source).read_bytes();size=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+size]);off=20+size
    n=struct.unpack_from('<I',raw,off)[0];binary=bytearray(raw[off+8:off+8+n])
    for im in j.get('images',[]):
        uri=im.pop('uri');data=(S/uri).read_bytes()
        binary.extend(b'\x00'*((-len(binary))%4));start=len(binary);binary.extend(data)
        im['bufferView']=len(j.setdefault('bufferViews',[]));im['mimeType']='image/png';j['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(data)})
    j['buffers'][0]['byteLength']=len(binary);binary.extend(b'\x00'*((-len(binary))%4))
    doc=json.dumps(j,separators=(',',':')).encode();doc+=b' '*((-len(doc))%4)
    result=struct.pack('<4sII',b'glTF',2,12+8+len(doc)+8+len(binary))+struct.pack('<II',len(doc),0x4e4f534a)+doc+struct.pack('<II',len(binary),0x004e4942)+binary
    (R/'models/common'/target).write_bytes(result)
    print(target,len(result),'bytes, animation untouched')
