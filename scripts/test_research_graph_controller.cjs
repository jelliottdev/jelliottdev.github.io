/* Execute production graph functions with SVG geometry stubs. Browser font/layout QA is separate. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const G=require('../research-graph-geometry.js'),source=fs.readFileSync(require.resolve('../research-browser.js'),'utf8');
function production(name){
 const at=source.search(new RegExp('^ function '+name+'\\(','m'));assert(at>=0,name);
 let candidate='';for(const line of source.slice(at).split('\n')){candidate+=line+'\n';try{new vm.Script(candidate);return candidate}catch(error){if(!/Unexpected end of input/.test(error.message))throw error}}
 throw Error('Unclosed production function '+name);
}
const attributes=html=>Object.fromEntries([...html.matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],m[2]]));
const decode=s=>s.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
class Shape{
 constructor(html=''){this.attrs=attributes(html);this.style={};this.dataset={};this.children=[];for(const[k,v]of Object.entries(this.attrs))if(k.startsWith('data-'))this.dataset[k.slice(5)]=v}
 setAttribute(k,v){this.attrs[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5)]=String(v)}getAttribute(k){return this.attrs[k]??null}removeAttribute(k){delete this.attrs[k]}
 appendChild(child){if(child.parent)child.parent.children=child.parent.children.filter(n=>n!==child);this.children.push(child);child.parent=this;return child}
 closest(selector){return selector==='[data-node]'?(this.attrs['data-node']?this:this.parent?.closest(selector)):null}
}
class Label extends Shape{
 constructor(html){super();this.hit=new Shape(html.match(/<rect([^>]*)\/>/)?.[1]||'');this.appendChild(this.hit);this.texts=[...html.matchAll(/<text([^>]*)>([\s\S]*?)<\/text>/g)].map(m=>{const text=new Shape(m[1]);text.lines=[...m[2].matchAll(/<tspan[^>]*>(.*?)<\/tspan>/g)].map(v=>decode(v[1]));if(!text.lines.length)text.lines=[decode(m[2])];text.querySelectorAll=()=>text.lines.map(()=>new Shape());this.appendChild(text);return text})}
 querySelector(s){return s==='.label-hit'?this.hit:s==='.count'?this.texts.find(n=>(n.attrs.class||'').includes('count')):this.texts[0]}
 getBBox(){const widths=this.texts.map(t=>Math.max(...t.lines.map(s=>s.length))*parseFloat(t.style.fontSize||'14')*.55);const heights=this.texts.map(t=>t.lines.length*parseFloat(t.style.fontSize||'14')*1.2);return{x:0,y:0,width:Math.max(...widths),height:heights.reduce((a,b)=>a+b,0)}}
}
class Element extends Shape{
 constructor(html,body){super(html);this.group=new Label(body.match(/<g class="node-label">([\s\S]*)<\/g>$/)?.[1]||'');this.appendChild(this.group);this.parts={};for(const c of body.matchAll(/<circle([^>]*)\/>/g)){const shape=new Shape(c[1]);this.parts[shape.attrs.class]=shape;this.appendChild(shape)}}
 querySelector(s){return s==='.node-label'?this.group:this.parts[s.slice(1)]||null}
}
function fixture({width=1000,height=700,focus='root',real=false,panelFraction=.44}={}){
 const records={a:{outcome:'inconclusive'},b:{outcome:'supported'},c:{outcome:'inconclusive'}};
 let entries=[{id:'root',parent:null,label:'Root',kind:'aim',children:['branch','other'],members:['a','b','c']},{id:'branch',parent:'root',label:'Branch',kind:'method',children:['leaf-a','leaf-b'],members:['a','b']},{id:'other',parent:'root',label:'Other',kind:'record',record_id:'c',children:[],members:['c']},{id:'leaf-a',parent:'branch',label:'First measured record',kind:'record',record_id:'a',children:[],members:['a']},{id:'leaf-b',parent:'branch',label:'Second measured record',kind:'record',record_id:'b',children:[],members:['b']}];
 if(real){const B=require('../research-browser-model.js');const data=B.build(JSON.parse(fs.readFileSync(require.resolve('../data/research-map.json'))),JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'))));entries=data.views.all.nodes;Object.assign(records,data.records)}
 const nodes=new Map(entries.map(n=>[n.id,n])),groups=new Map(),events=[];
 const world=new Shape();Object.defineProperty(world,'innerHTML',{set(html){this.html=html;this.children=[];groups.clear();const top=[];for(const m of html.matchAll(/<g (class="node[^"]*"[^>]*)>([\s\S]*?<g class="node-label">[\s\S]*?<\/g>)<\/g>/g)){const el=new Element(m[1],m[2]);groups.set(decode(el.attrs['data-node']),el);top.push({at:m.index,element:el})}const layer=html.match(/<g class="labels-layer"><\/g>/);this.layer=layer?new Shape('class="labels-layer"'):null;if(layer)top.push({at:layer.index,element:this.layer});top.sort((a,b)=>a.at-b.at).forEach(n=>this.appendChild(n.element))},get(){return this.html}});
 world.querySelector=s=>s==='.labels-layer'?world.layer:groups.get(s.match(/data-node="(.*?)"/)?.[1]);
 const rect=(x,y,w,h)=>({x,y,width:w,height:h,left:x,top:y,right:x+w,bottom:y+h});
 const panel={hidden:true,getBoundingClientRect:()=>panel.hidden?rect(0,0,0,0):rect(12,height*(1-panelFraction)-12,width-24,height*panelFraction),getClientRects:()=>panel.hidden?[]:[panel.getBoundingClientRect()]};
 const controls={getBoundingClientRect:()=>rect(width-60,!panel.hidden&&width<=760?height*(1-panelFraction)-145:height-150,40,120)};
 const help={getBoundingClientRect:()=>!panel.hidden&&width<=760?rect(0,0,0,0):rect(22,height-54,105,36),getClientRects:()=>!panel.hidden&&width<=760?[]:[help.getBoundingClientRect()]};
 const map={getBoundingClientRect:()=>rect(0,0,width,height),querySelector:selector=>selector==='.map-help'?help:controls,querySelectorAll:()=>[controls,help]};
 const c={ResearchGraphGeometry:G,CSS:{escape:s=>s},getComputedStyle:el=>({display:el.hidden||!el.getBoundingClientRect().width?'none':'block'}),camera:{x:width/2,y:height/2,k:1},world,map,panel,innerWidth:width,state:{mode:'graph',record:'',colour:'methods'},nodes,focus:nodes.get(focus),data:{records},matching:new Set(Object.keys(records)),layout:new Map(),labelNodes:[],worldBounds:{},worldHeight:600,aliases:{},resultColours:{},$:id=>id==='about-button'?help:null,esc:s=>String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;'),navigate:change=>events.push(change)};
 vm.createContext(c);vm.runInContext(source.match(/^ const count=.*$/m)[0],c);for(const name of ['passes','lines','branchBelow','position','paintGraph','applyCamera','availableMapHeight','recordNode','revealSelection','fit','activate'])vm.runInContext(production(name),c);
 c.position();c.paintGraph();return{c,groups,events,width,height};
}
function visibleBoxes(f){return[...f.groups].filter(([,el])=>el.group.style.display!=='none').map(([id,el])=>{const m=el.group.attrs.transform.match(/^translate\(([-\d.e]+) ([-\d.e]+)\)/),b=el.group.getBBox();return{id,x:f.c.camera.x+Number(m[1])*f.c.camera.k,y:f.c.camera.y+Number(m[2])*f.c.camera.k,width:b.width,height:b.height+4}})}
function visibleHitBoxes(f){return[...f.groups].filter(([,el])=>el.group.style.display!=='none').map(([id,el])=>{const m=el.group.attrs.transform.match(/^translate\(([-\d.e]+) ([-\d.e]+)\).*translate\(([-\d.e]+) ([-\d.e]+)\)$/),h=el.group.hit.attrs;return{id,x:f.c.camera.x+Number(m[1])*f.c.camera.k+Number(m[3])+Number(h.x),y:f.c.camera.y+Number(m[2])*f.c.camera.k+Number(m[4])+Number(h.y),width:Number(h.width),height:Number(h.height)}})}
for(const scale of [.28,1,4,8]){
 const f=fixture();f.c.camera.k=scale;f.c.applyCamera();
 assert.equal(f.c.world.children.at(-1),f.c.world.layer,'The label overlay must be after every marker node, so a neighbor hit circle cannot intercept a label');
 assert.equal(f.c.world.layer.children.length,f.groups.size);
 for(const [id,el] of f.groups){const item=f.c.labelNodes.find(x=>x.id===id),mark=el.parts.mark,hit=el.parts.hit;
  assert.equal(el.group.parent,f.c.world.layer,'Production moves each label into the top overlay');assert(!el.children.includes(el.group));assert.equal(el.group.hit.closest('[data-node]').getAttribute('data-node'),id,'Label rectangle retains its own node target after reparenting');
  if(mark&&Number(mark.attrs.r)>0)assert(Math.abs(Number(mark.attrs.r)*scale-(item.isChild?6:item.record?2.5:4))<1e-12);
  if(Number(hit.attrs.r)>0)assert(Math.abs(Number(hit.attrs.r)*scale-18)<1e-12);
  if(mark)assert.equal(mark.attrs['vector-effect'],'non-scaling-stroke');
 }
 const boxes=visibleBoxes(f);for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++)assert(!G.intersects(boxes[i],boxes[j],8));
 for(const edge of f.c.world.innerHTML.matchAll(/<path([^>]*)\/>/g))assert.equal(attributes(edge[1])['vector-effect'],'non-scaling-stroke');
}
const reveal=fixture();reveal.c.camera.k=.5;reveal.c.applyCamera();const low=visibleBoxes(reveal).filter(b=>b.id.startsWith('leaf')).length;
reveal.c.camera.k=1.2;reveal.c.applyCamera();const high=visibleBoxes(reveal).filter(b=>b.id.startsWith('leaf')).length;assert(high>low,'Actual controller must generate and reveal deeper labels when space permits');
const leaf=[...reveal.groups].find(([id,el])=>id.startsWith('leaf')&&el.group.style.display!=='none');assert(leaf);const hitTarget=leaf[1].group.hit;assert(Number(hitTarget.attrs.width)>0&&Number(hitTarget.attrs.height)>0,'Visible label owns a bounded hit rectangle');reveal.c.activate(hitTarget.closest('[data-node]').getAttribute('data-node'));assert.equal(reveal.events.at(-1).record,reveal.c.nodes.get(leaf[0]).record_id,'The overlay rectangle opens the exact deep record rather than its neighbor or ancestor');
for(const width of [320,390,768,1440]){
 const f=fixture({width,height:600,real:true,focus:'aim:unplaced'});f.c.fit();const b=f.c.worldBounds,k=f.c.camera.k;
 assert(b.x*k+f.c.camera.x>=9.999);assert(b.y*k+f.c.camera.y>=9.999);assert((b.x+b.width)*k+f.c.camera.x<=width-9.999);assert((b.y+b.height)*k+f.c.camera.y<=590.001);
 const boxes=visibleBoxes(f);assert(boxes.length>1);for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++)assert(!G.intersects(boxes[i],boxes[j],8));
 for(const box of boxes){assert(box.x>=8&&box.y>=8);assert(box.x+box.width<=width-8+1e-8);assert(box.y+box.height<=592+1e-8);assert(!G.intersects(box,{x:width-66,y:444,width:52,height:132},8),'Label must not cover the fixed zoom controls')}
}
const panelFit=fixture({width:390,height:600,real:true,focus:'aim:unplaced'});panelFit.c.panel.hidden=false;panelFit.c.fit();const pb=panelFit.c.worldBounds,pc=panelFit.c.camera;assert((pb.y+pb.height)*pc.k+pc.y<=320.001,'Mobile fit reserves the visible inspector height');
// Crowded real Combined ciphers branch: the actual mobile inspector rectangle is
// an obstacle at every zoom, not merely an estimated height used by Fit.
for(const width of [320,390])for(const panelFraction of [.4,.55,.7,.8]){
 const f=fixture({width,height:650,real:true,focus:'method:combined',panelFraction});f.c.panel.hidden=false;f.c.fit();
 for(const scale of [f.c.camera.k,.8,1.8]){f.c.camera.k=scale;f.c.applyCamera();const inspector=f.c.panel.getBoundingClientRect(),boxes=visibleHitBoxes(f);assert(boxes.length>0,JSON.stringify({width,panelFraction,scale}));
  for(const box of boxes)assert(!G.intersects(box,inspector),'A displayed label or its click rectangle must never sit underneath the mobile preview');
  for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++)assert(!G.intersects(boxes[i],boxes[j]),'Padded title hit rectangles must not overlap');
  for(const box of boxes){const target=f.groups.get(box.id).group.hit.closest('[data-node]');assert.equal(target.getAttribute('data-node'),box.id)}
 }
 const selected=f.c.labelNodes.find(n=>n.record);assert(selected);f.c.state.record=selected.n.record_id;f.c.camera={x:-900,y:1200,k:1.8};f.c.revealSelection();
 const x=f.c.camera.x+selected.p.x*f.c.camera.k,y=f.c.camera.y+selected.p.y*f.c.camera.k;
 assert.equal(f.c.camera.k,1.8,'Selecting a record must pan without discarding the current zoom');assert(x>=32&&x<=width-32);assert(y>=32&&y<=f.c.availableMapHeight()-32,'Selected marker must pan above the actual preview, not a fixed55% guess');
}
console.log('PASS production graph VM: screen-constant marks/hits and non-scaling strokes; collision-free measured-stub labels; deep reveal/activation; actual dense-branch fit bounds at320/390/768/1440. CSS/font/browser QA remains separate.');
