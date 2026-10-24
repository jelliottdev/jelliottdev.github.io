/* Production List renderer over current navigation; no browser/network calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const read=name=>JSON.parse(fs.readFileSync(require.resolve('../'+name),'utf8'));
const data=require('../research-browser-model.js').build(read('data/research-map.json'),read('data/experiments.json'));
const Index=require('../research-index.js'),source=fs.readFileSync(require.resolve('../research-browser.js'),'utf8');
const code=source.slice(source.indexOf(' function renderList(){'),source.indexOf('\n function filterMenu(){'));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(focusId,{matches=Object.keys(data.records),colour='methods',selected=''}={}){
 const nodes=new Map(data.views.all.nodes.map(n=>[n.id,n])),focus=nodes.get(focusId),matching=new Set(matches),calls=[];
 const container={html:'',scrollTop:0,set innerHTML(value){this.html=value;this.buttons=[...value.matchAll(/<button[^>]*data-list-node="([^"]+)"[^>]*>/g)].map(m=>({dataset:{listNode:m[1]},disabled:/ disabled/.test(m[0])}));},get innerHTML(){return this.html;},querySelectorAll(selector){return selector==='[data-list-node]'?this.buttons:[];},querySelector(selector){return selector==='#research-sort'&&this.html.includes('id="research-sort"')?{}:null;}};
 const state={view:'all',q:'',type:'',method:'',family:'',result:'',page:'',sort:'title',p:999,colour,record:selected};
 const context={state,data,nodes,focus,esc,aliases:{},sorts:{title:'Title A–Z'},chevron:'<svg aria-hidden="true"></svg>',count:n=>n.members.filter(id=>matching.has(id)).length,
  indexResult:Index.select(Object.values(data.records),{}),$:()=>container,listPositions:new Map(),listKey:'',scopeLabel:r=>r.pages.length+' pages',outcomes:{supported:'Supported within scope',inconclusive:'Inconclusive','not-supported':'Not supported within scope'},resultColours:{supported:'#138575',inconclusive:'#75649a','not-supported':'#7b899b'},navigate:changes=>calls.push(changes),clearFilters(){},dialog:{querySelectorAll:()=>[]},openDialog(){},closeDialog(){}};
 vm.createContext(context);vm.runInContext(code,context);context.renderList();return{container,context,calls,focus,nodes};
}
for(const focus of data.views.all.nodes.filter(n=>n.children.length)){
 const r=render(focus.id);assert.deepEqual(new Set(r.container.buttons.map(b=>b.dataset.listNode)),new Set(focus.children),'List contains exactly immediate map children: '+focus.id);
 assert(!r.container.html.includes('research-pagination'));assert(!r.container.html.includes('data-list-page'));assert.equal(r.context.state.p,999,'Rendering does not rewrite shared URL state or force a selected descendant page');
 for(const button of r.container.buttons){const node=r.nodes.get(button.dataset.listNode);button.onclick();const action=r.calls.at(-1);assert.equal(node.kind==='record'?action.record:action.branch,node.kind==='record'?node.record_id:node.id,'A click uses the exact child rather than skipping scope levels');assert.deepEqual(Object.keys(action).sort(),node.kind==='record'?['record']:['branch','record']);}
}
const root=render('all-research');assert.equal(root.container.buttons.length,6);assert(!root.container.html.includes('Open full record'),'Root never flattens descendant records into a wall');
const recordParent=data.views.all.nodes.find(n=>n.children.length&&n.children.every(id=>data.views.all.nodes.find(child=>child.id===id).kind==='record'));
const colored=render(recordParent.id,{colour:'results'}),child=colored.nodes.get(recordParent.children[0]),record=data.records[child.record_id];
assert(colored.container.html.includes('--branch-colour:'+colored.context.resultColours[record.outcome]));assert(colored.container.html.includes('href="'+record.href+'"'));assert(colored.container.html.includes(esc(record.title)));
const filtered=render('all-research',{matches:[record.id]});for(const button of filtered.container.buttons){const node=filtered.nodes.get(button.dataset.listNode);assert.equal(button.disabled,!node.members.includes(record.id));}
assert(filtered.container.html.includes('1 matching record</span>'));const empty=render('all-research',{matches:[]});assert(empty.container.html.includes('No matching research'));assert(empty.container.buttons.every(b=>b.disabled));
const css=fs.readFileSync(require.resolve('../research-browser.css'),'utf8');assert(css.includes('.research-branch-copy{display:block;min-width:0;flex:1;overflow-wrap:anywhere}'));assert(css.includes('min-height:64px'));
// Run the actual wheel/button and pinch paths: touching a fitted dense view must not snap its scale.
const pointerState=source.match(/^ function pointerState\(.*$/m)[0],pointerMove=source.split('\n').find(line=>line.startsWith(" svg.addEventListener('pointermove'")),zoom=source.match(/^ function zoom\(.*$/m)[0];
for(const scale of [.08,.1,.28,1,4,5,8])for(const factor of [.25,1,2]){
 let move;const context={camera:{x:0,y:0,k:scale},gesture:{center:{x:50,y:0},distance:100,camera:{x:0,y:0,k:scale}},moved:false,
  activePointers:new Map([[1,{x:0,y:0}],[2,{x:100,y:0}]]),map:{getBoundingClientRect:()=>({left:0,top:0,width:320,height:650})},applyCamera(){},svg:{addEventListener(type,handler){move=handler}}};
 vm.createContext(context);vm.runInContext(pointerState+'\n'+pointerMove+'\n'+zoom,context);move({pointerId:2,clientX:100*factor,clientY:0});const pinched=context.camera.k;
 context.camera={x:0,y:0,k:scale};context.zoom(factor);assert.equal(pinched,context.camera.k,'Pinch and button/wheel zoom share exact limits at '+scale+' × '+factor);
 if(factor===1)assert.equal(pinched,scale,'Starting a two-finger gesture preserves the current scale');
}
console.log('PASS map List: every branch exposes exactly one level, exact scope drill/record preview, shared filtering/counts/colors/links, no pagination/descendant wall, state unchanged, wrapping/touch targets.');
