const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),api=require('../reader/continuous-pages.js');
const root=path.join(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8')),pages=read('data/index.json').pages;
assert.deepEqual(api.neighborIds(pages,'lp1-00'),['lp1-00','lp1-01']);assert.deepEqual(api.neighborIds(pages,'lp2-57'),['lp2-56','lp2-57']);assert.deepEqual(api.neighborIds(pages,'lp2-15'),['lp2-14','lp2-15','lp2-16']);
assert.equal(api.visibleId([{id:'a',top:0,bottom:600},{id:'b',top:600,bottom:1200}],500,400),'b');
let frames=[];global.requestAnimationFrame=f=>(frames.push(f),frames.length);global.cancelAnimationFrame=()=>{};
class Node{
 constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];this.dataset={};this.listeners={};this.hidden=false;this.scrollTop=0;this.clientHeight=350;this.clientWidth=390;this.textContent='';}
 append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n)}}prepend(n){n.parent=this;this.children.unshift(n)}replaceChildren(...nodes){this.children.forEach(n=>n.parent=null);this.children=[];this.append(...nodes)}remove(){this.parent.children=this.parent.children.filter(n=>n!==this);this.parent=null}
 setAttribute(k,v){this[k]=v}addEventListener(t,f){this.listeners[t]=f}
 get isConnected(){return this.root||!!this.parent?.isConnected}get height(){return this.dataset.continuousPage?568:0}get scrollHeight(){return this.children.reduce((s,n)=>s+n.height,0)}get offsetTop(){return this.parent?this.parent.children.slice(0,this.parent.children.indexOf(this)).reduce((s,n)=>s+n.height,0):0}
 getBoundingClientRect(){return this.root?{top:0,bottom:350,height:350}:{top:this.offsetTop-(this.parent?.scrollTop||0),bottom:this.offsetTop-(this.parent?.scrollTop||0)+this.height,height:this.height}}
 querySelectorAll(s){return s==='[data-continuous-page]'?this.children.filter(n=>n.dataset.continuousPage):[]}querySelector(s){return s==='[data-continuous-status]'?this.children.find(n=>Object.hasOwn(n.dataset,'continuousStatus')):null}
}
const doc={createElement(tag){return new Node(tag,doc)},createTextNode(text){const n=new Node('text',doc);n.textContent=text;return n}};
function setup(load){const view=new Node('view',doc);view.root=true;const requested=[],active=[];const controller=api.create(view,{pages,loadPage:load||(async(id)=>{requested.push(id);return read('data/pages/'+id+'.json')}),onActive:id=>active.push(id)});return {view,controller,requested,active}}
const flush=()=>new Promise(r=>setImmediate(r));async function scroll(h,top){h.view.scrollTop=top;h.view.listeners.scroll();const q=frames;frames=[];q.forEach(f=>f());await flush();await flush();}
(async()=>{
 const h=setup();await h.controller.open('lp2-15');assert.deepEqual(h.requested,['lp2-14','lp2-15','lp2-16']);assert.equal(h.view.scrollTop,568);assert.equal(h.view.children.length,3);
 for(let i=0;i<9;i++){await scroll(h,h.view.scrollHeight-h.view.clientHeight);assert(h.view.querySelectorAll('[data-continuous-page]').length<=5,'At most five original images stay mounted');}
 assert(h.active.includes('lp2-16'));assert(h.active.includes('lp2-23'));assert(h.requested.length<20,'Never eager-load all75 originals');
 const before=h.requested.length,position=h.view.scrollTop;await h.controller.open(h.controller.currentId);assert.equal(h.requested.length,before);assert.equal(h.view.scrollTop,position,'Re-entering Image preserves continuous position');
 const failure=setup(async()=>({id:'wrong',image_dimensions:[2400,3600]}));await failure.controller.open('lp2-15');assert(failure.view.querySelector('[data-continuous-status]').textContent.includes('could not load'));
 const pending=[];const race=setup(id=>new Promise(resolve=>pending.push({id,resolve})));const old=race.controller.open('lp2-15'),next=race.controller.open('lp2-35');pending.slice(3).forEach(r=>r.resolve(read('data/pages/'+r.id+'.json')));await next;pending.slice(0,3).forEach(r=>r.resolve(read('data/pages/'+r.id+'.json')));await old;assert.equal(race.controller.currentId,'lp2-35');assert.deepEqual(race.view.querySelectorAll('[data-continuous-page]').map(n=>n.dataset.continuousPage),['lp2-34','lp2-35','lp2-36']);
 race.controller.destroy();assert.equal(race.view.children.length,0);
 console.log('PASS: real adjacent-page metadata, bounded rolling images, active-page identity, preserved position, malformed/stale loads, disposal. DOM model; browser QA separate.');
})().catch(e=>{console.error(e);process.exitCode=1});
