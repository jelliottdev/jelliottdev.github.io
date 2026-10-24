/* Screen-space geometry only. Mandatory labels are reserved by the renderer. */
(function(root){
 'use strict';
 const finite=n=>typeof n==='number'&&Number.isFinite(n);
 function worldPixels(pixels,scale){
  if(!finite(pixels)||pixels<0||!finite(scale)||scale<=0)throw Error('Invalid screen size or scale');
  return pixels/scale;
 }
 function rectangle(value){
  if(!value||!['x','y','width','height'].every(k=>finite(value[k]))||value.width<=0||value.height<=0)throw Error('Invalid screen rectangle');
  return {x:value.x,y:value.y,width:value.width,height:value.height};
 }
 function intersects(a,b,gap=0){
  if(!finite(gap)||gap<0)throw Error('Invalid label gap');
  return a.x<b.x+b.width+gap&&a.x+a.width+gap>b.x&&a.y<b.y+b.height+gap&&a.y+a.height+gap>b.y;
 }
 function inside(box,viewport){return box.x>=viewport.x&&box.y>=viewport.y&&box.x+box.width<=viewport.x+viewport.width&&box.y+box.height<=viewport.y+viewport.height}
 function placeOptionalLabels(candidates,{viewport,occupied=[],gap=4}={}){
  const bounds=rectangle(viewport),reserved=occupied.map(rectangle),seen=new Set();
  if(!finite(gap)||gap<0)throw Error('Invalid label gap');
  const ordered=candidates.map(candidate=>{
   if(!candidate||typeof candidate.id!=='string'||!candidate.id||seen.has(candidate.id))throw Error('Invalid or repeated label id');
   seen.add(candidate.id);
   if(!finite(candidate.priority??0))throw Error('Invalid label priority');
   const placements=(candidate.placements||[candidate]).map(position=>rectangle({...position,width:candidate.width,height:candidate.height}));
   return {...candidate,priority:candidate.priority??0,placements};
  }).sort((a,b)=>a.priority-b.priority||(a.id<b.id?-1:a.id>b.id?1:0));
  const placed=[],omitted=[];
  for(const candidate of ordered){
   let chosen,inBounds=false;
   for(const box of candidate.placements){
    if(!inside(box,bounds))continue;
    inBounds=true;
    if(!reserved.some(other=>intersects(box,other,gap))){chosen=box;break}
   }
   if(chosen){placed.push({id:candidate.id,...chosen});reserved.push(chosen)}
   else omitted.push({id:candidate.id,reason:inBounds?'collision':'outside-viewport'});
  }
  return {placed,omitted};
 }
 const api={worldPixels,intersects,placeOptionalLabels};
 if(typeof module!=='undefined')module.exports=api;else root.ResearchGraphGeometry=api;
})(globalThis);
