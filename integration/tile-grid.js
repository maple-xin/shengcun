// Optional Three.js helper: batch repeated tile meshes while keeping per-cell control.
// Pass the same THREE namespace used by GLTFLoader. No external dependencies.
export function prepareTiles(stage,THREE){
  stage.updateMatrixWorld(true);
  const inv=stage.matrixWorld.clone().invert(),groups=new Map(),records=new Map();
  const tiles=[];stage.traverse(o=>{if(/^tile_\d\d_\d\d$/.test(o.name))tiles.push(o);});
  for(const tile of tiles){
    const root=inv.clone().multiply(tile.matrixWorld),localInv=tile.matrixWorld.clone().invert(),pieces=[];
    tile.traverse(o=>{if(!o.isMesh||o.isInstancedMesh)return;
      const key=o.geometry.uuid+':'+o.material.uuid;if(!groups.has(key))groups.set(key,{geometry:o.geometry,material:o.material,entries:[]});
      const entry={root,local:localInv.clone().multiply(o.matrixWorld),tile:tile.name};groups.get(key).entries.push(entry);pieces.push(entry);o.visible=false;
    });records.set(tile.name,pieces);
  }
  for(const group of groups.values()){
    const batch=new THREE.InstancedMesh(group.geometry,group.material,group.entries.length);batch.name='tile_batch';batch.castShadow=batch.receiveShadow=true;batch.frustumCulled=false;
    group.entries.forEach((e,i)=>{e.batch=batch;e.index=i;batch.setMatrixAt(i,e.root.clone().multiply(e.local));});stage.add(batch);
  }
  function setTile(name,{visible=true,flip=0,drop=0}={}){
    const delta=new THREE.Matrix4().makeTranslation(0,-drop,0).multiply(new THREE.Matrix4().makeRotationX(flip));
    if(!visible)delta.multiply(new THREE.Matrix4().makeScale(0,0,0));
    for(const e of records.get(name)||[]){e.batch.setMatrixAt(e.index,e.root.clone().multiply(delta).multiply(e.local));e.batch.instanceMatrix.needsUpdate=true;}
  }
  return {names:[...records.keys()],setTile,reset(){for(const name of records.keys())setTile(name);},batches:groups.size};
}
