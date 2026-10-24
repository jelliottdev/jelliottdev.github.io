'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const G=require('../research-graph-geometry.js');
for(const scale of [.28,.5,1,2,4])for(const pixels of [0,3,5,8,22])assert(Math.abs(G.worldPixels(pixels,scale)*scale-pixels)<1e-12);
assert.equal(G.worldPixels(22,4),5.5,'Hit radius must not acquire a world-space floor and become96 screen pixels');
for(const scale of [0,-1,NaN,Infinity])assert.throws(()=>G.worldPixels(22,scale));
const viewport={x:0,y:0,width:320,height:500},occupied=[{x:110,y:160,width:100,height:60}];
const candidates=[{id:'later',priority:2,x:110,y:160,width:100,height:40},{id:'first',priority:1,width:100,height:40,placements:[{x:110,y:160},{x:10,y:20}]},{id:'clipped',x:-20,y:100,width:100,height:40}];
const before=JSON.stringify({candidates,occupied}),result=G.placeOptionalLabels(candidates,{viewport,occupied});
assert.equal(JSON.stringify({candidates,occupied}),before,'Cannot move or rewrite required labels or caller geometry');
assert.deepEqual(result.placed,[{id:'first',x:10,y:20,width:100,height:40}]);
assert.deepEqual(result.omitted,[{id:'clipped',reason:'outside-viewport'},{id:'later',reason:'collision'}]);
assert.deepEqual(G.placeOptionalLabels([...candidates].reverse(),{viewport,occupied}),result,'Stable priorities/id ties must not flicker with DOM traversal order');
// Use actual dense branch titles. This deliberately tests a pannable graph's visible
// window; the renderer must space mandatory labels, not hide them through this helper.
const root=path.resolve(__dirname,'..'),B=require('../research-browser-model.js');
const data=B.build(JSON.parse(fs.readFileSync(path.join(root,'data/research-map.json'))),JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'))));
const branch=data.views.all.nodes.find(n=>n.id==='aim:unplaced');assert(branch.members.length>=19);
for(const width of [320,390,768,1440]){
 const nodes=branch.members.map((id,i)=>({id,x:40,y:30+i*76,width:Math.min(width-80,290),height:58}));
 const labels=G.placeOptionalLabels(nodes,{viewport:{x:0,y:0,width,height:500},gap:8});
 assert(labels.placed.length>=5,'Dense branch has several readable graph labels in the viewport');
 for(let i=0;i<labels.placed.length;i++)for(let j=i+1;j<labels.placed.length;j++)assert(!G.intersects(labels.placed[i],labels.placed[j],8));
 assert(labels.omitted.every(n=>n.reason==='outside-viewport'),'Spaced graph rows do not require collision hiding');
}
// Optional descendant text can emerge as zoom spreads nearby nodes apart.
const at=scale=>[0,1,2].map(i=>({id:String(i),x:20+i*35*scale,y:40,width:100,height:30}));
const low=G.placeOptionalLabels(at(.5),{viewport}),high=G.placeOptionalLabels(at(4),{viewport:{...viewport,width:600}});
assert(high.placed.length>low.placed.length);
assert.throws(()=>G.placeOptionalLabels([{id:'same',x:0,y:0,width:10,height:10},{id:'same',x:20,y:0,width:10,height:10}],{viewport}));
console.log('PASS graph geometry: constant screen pixels; immutable required obstacles; stable optional collision/clipping; actual dense branch at320/390/768/1440; zoom-driven space for descendant labels.');
