import * as THREE from 'three';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
import {OrbitControls} from './vendor/controls/OrbitControls.js';
import {prepareTiles} from './integration/tile-grid.js';
const $=id=>document.getElementById(id),view=$('viewport');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0xf1eddd);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;view.prepend(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,1,.01,1000),controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;scene.add(new THREE.HemisphereLight(0xffffff,0xb3a784,2.4));
for(const [pos,intensity] of [[[8,15,8],3],[[-8,5,-6],1.5]]){const light=new THREE.DirectionalLight(0xfff4dd,intensity);light.position.set(...pos);scene.add(light);}
const loader=new GLTFLoader();let current,mixer,tiles,clips=[],ticket=0;
const manifest=await fetch('./manifest.json').then(r=>{if(!r.ok)throw Error('Manifest unavailable');return r.json();});
const models=[...manifest.models].sort((a,b)=>(a.group==='stages'?0:1)-(b.group==='stages'?0:1)||a.id.localeCompare(b.id));
for(const m of models){const option=document.createElement('option');option.value=m.id;option.textContent=`${m.group} / ${m.label}`;$('model').append(option);}
function dispose(root){const geos=new Set(),mats=new Set(),textures=new Set();root.traverse(o=>{if(o.geometry)geos.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])if(m){mats.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v);}});for(const x of [...geos,...mats,...textures])x.dispose();}
function resize(){const w=view.clientWidth,h=view.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(view);resize();
async function show(){const n=++ticket,m=models.find(x=>x.id===$('model').value);$('status').textContent='Loading…';
  try{const gltf=await loader.loadAsync(m.path);if(n!==ticket){dispose(gltf.scene);return;}if(current){scene.remove(current);dispose(current);}mixer?.stopAllAction();current=gltf.scene;tiles=null;scene.add(current);
    const box=new THREE.Box3().setFromObject(current),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
    controls.target.copy(center);const distance=Math.max(size.x/(camera.aspect||1),size.y,size.z)*1.7;
    camera.position.copy(center).add(new THREE.Vector3(.8,1.05,1.45).normalize().multiplyScalar(distance));camera.near=Math.max(.001,distance/1000);camera.far=distance*30;camera.updateProjectionMatrix();controls.minDistance=distance*.15;controls.maxDistance=distance*4;controls.update();
    if(m.group==='stages')tiles=prepareTiles(current,THREE);
    $('stageActions').hidden=!tiles;$('stageActions').style.display=tiles?'flex':'none';
    clips=gltf.animations;mixer=clips.length?new THREE.AnimationMixer(current):null;$('animation').replaceChildren();
    for(const clip of clips){const option=document.createElement('option');option.value=clip.name;option.textContent=clip.name;$('animation').append(option);}
    $('animationActions').style.display=clips.length?'flex':'none';if(clips.length){$('animation').value=clips.some(x=>x.name==='idle')?'idle':clips[0].name;play();}
    $('download').href=m.path;$('url').textContent=new URL(m.path,location.href).href;
    $('stats').textContent=`${(m.bytes/1024).toFixed(0)} KB · ${m.triangles.toLocaleString()} triangles · ${m.embeddedImages} embedded textures · ${clips.length} animation clips${tiles?` · ${tiles.names.length} tiles / ${tiles.batches} tile batches`:''}`;
    $('status').textContent=tiles?'144 tiles ready · Drag to orbit':'Loaded · Drag to orbit';
  }catch(e){$('status').textContent=`Load failed: ${e.message}`;console.error(e);}}
function play(){if(mixer){mixer.stopAllAction();mixer.clipAction(THREE.AnimationClip.findByName(clips,$('animation').value)).play();}}
$('animation').onchange=play;$('model').onchange=show;
$('hole').onclick=()=>{tiles?.setTile('tile_05_05',{visible:false});$('status').textContent='Center tile hidden · Hole is open';};
$('shrink').onclick=()=>{for(const name of tiles?.names||[]){const [,r,c]=name.split('_').map(Number);tiles.setTile(name,{visible:r>=2&&r<10&&c>=2&&c<10});}$('status').textContent='64 tiles remain · 8 × 8';};
$('flip').onclick=()=>{tiles?.setTile('tile_05_05',{flip:Math.PI*.75});$('status').textContent='Sample tile flipped around its top-center pivot';};
$('reset').onclick=()=>{tiles?.reset();$('status').textContent='144 tiles restored';};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('url').textContent);$('status').textContent='Model URL copied';}catch{$('status').textContent='Select and copy the URL below';}};
$('check').onclick=async()=>{const button=$('check');button.disabled=true;let count=0,failed=[];
  for(const m of models){$('testResult').textContent=`Checking ${count+1}/${models.length}: ${m.id}`;let root;
    try{const gltf=await loader.loadAsync(m.path);root=gltf.scene;let meshes=0;root.traverse(o=>{if(o.isMesh)meshes++;});if(!meshes)throw Error('No meshes');
      if(m.group==='stages'){const t=prepareTiles(root,THREE);if(t.names.length!==144)throw Error('Expected 144 tiles');const b=root.children.find(o=>o.isInstancedMesh),before=new THREE.Matrix4(),after=new THREE.Matrix4();b.getMatrixAt(0,before);t.setTile(t.names[0],{visible:false});b.getMatrixAt(0,after);if(before.equals(after))throw Error('Tile visibility did not change');t.reset();b.getMatrixAt(0,after);if(!before.equals(after))throw Error('Tile reset failed');}
      if(gltf.animations.length!==m.animations.length)throw Error('Animation count mismatch');count++;
    }catch(e){failed.push(`${m.id}: ${e.message}`);}finally{if(root)dispose(root);}}
  $('testResult').textContent=`${count}/${models.length} GLBs loaded successfully. Stage tile hide/reset checked.${failed.length?'\n'+failed.join('\n'):''}`;button.disabled=false;};
const clock=new THREE.Clock();renderer.setAnimationLoop(()=>{mixer?.update(Math.min(clock.getDelta(),.05));controls.update();renderer.render(scene,camera);});
await show();
