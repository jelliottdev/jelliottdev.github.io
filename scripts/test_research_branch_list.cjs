/* Production List renderer over current navigation; no browser/network calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const read=name=>JSON.parse(fs.readFileSync(require.resolve('../'+name),'utf8'));
const data=require('../research-browser-model.js').build(read('data/research-map.json'),read('data/experiments.json'));
const Reader=require('../record-test-view.js'),Index=require('../research-index.js'),source=fs.readFileSync(require.resolve('../research-browser.js'),'utf8');
const originalRecordMetadata=JSON.stringify(data.records);
const helpers=['workFor','recordHref','traversalChildren','interest'].map(name=>source.split('\n').find(line=>line.startsWith(' function '+name+'('))).join('\n');
const code=source.slice(source.indexOf(' function renderList(){'),source.indexOf('\n function filterMenu(){'));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(focusId,{matches=Object.keys(data.records),colour='methods',selected='',sort='title',saved=false,counts={}}={}){
 const nodes=new Map(data.views.all.nodes.map(n=>[n.id,n])),focus=nodes.get(focusId),matching=new Set(matches),calls=[];
 const container={html:'',scrollTop:0,set innerHTML(value){this.html=value;this.buttons=[...value.matchAll(/<button[^>]*data-list-node="([^"]+)"[^>]*>/g)].map(m=>({dataset:{listNode:m[1]},disabled:/ disabled/.test(m[0])}));this.links=[...value.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/g)].filter(m=>/\bhref="/.test(m[1])).map(m=>({href:m[1].match(/\bhref="([^"]+)"/)[1],dataset:{listNode:m[1].match(/data-list-node="([^"]+)"/)?.[1]},html:m[2]}));},get innerHTML(){return this.html;},querySelectorAll(selector){return selector==='button[data-list-node]'?this.buttons:selector==='[data-list-node]'?[...this.buttons,...this.links.filter(a=>a.dataset.listNode)]:[];},querySelector(selector){return selector==='#research-sort'&&this.html.includes('id="research-sort"')?{}:null;}};
 const state={view:'all',q:'',type:'',method:'',family:'',result:'',page:'',sort,saved:saved?'1':'',p:999,colour,record:selected};
 const context={RecordTestView:Reader,readerTitle:Reader.title,readerBlurb:Reader.blurb,ResearchWork:require('../research-work.js'),state,data,nodes,focus,esc,aliases:{},sorts:{title:'Title A–Z',top:'Most upvoted'},votesLoading:false,reactions:{count:id=>counts[id]??null},loadTopVotes(){},passes:id=>matching.has(id),arrow:'<svg aria-hidden="true"></svg>',chevron:'<svg aria-hidden="true"></svg>',count:n=>n.members.filter(id=>matching.has(id)).length,
  indexResult:Index.select(Object.values(data.records),{}),$:()=>container,listPositions:new Map(),listKey:'',scopeLabel:r=>r.pages.length+' pages',outcomes:{supported:'Supported within scope',inconclusive:'Inconclusive','not-supported':'Not supported within scope'},resultColours:{supported:'#138575',inconclusive:'#75649a','not-supported':'#7b899b'},navigate:changes=>calls.push(changes),clearFilters(){},dialog:{querySelectorAll:()=>[]},openDialog(){},closeDialog(){}};
 vm.createContext(context);vm.runInContext(helpers+'\n'+code,context);context.renderList();return{container,context,calls,focus,nodes};
}
for(const focus of data.views.all.nodes.filter(n=>n.children.length)){
 const r=render(focus.id),children=focus.children.map(id=>r.nodes.get(id)),branches=children.filter(n=>n.kind!=='record'),records=children.filter(n=>n.kind==='record');
 assert.deepEqual(new Set(r.container.buttons.map(b=>b.dataset.listNode)),new Set(branches.map(n=>n.id)),'Only immediate nonterminal branches remain drill buttons: '+focus.id);
 assert.deepEqual(new Set(r.container.links.map(a=>a.href)),new Set(records.map(n=>data.records[n.record_id].href)),'Every immediate terminal record has its exact current record URL: '+focus.id);
 assert.equal(r.container.links.length,records.length,'A terminal record has one primary link, without a duplicate Open full record action');assert.equal((r.container.html.match(/<li\b/g)||[]).length,focus.children.length,'No child is lost or flattened');
 for(const a of r.container.links)assert.equal(a.onclick,undefined,'Record anchors must retain native direct navigation and modified-click behavior');
 for(const node of records){const record=data.records[node.record_id];assert(r.container.html.includes(esc(Reader.title(record))));if(Reader.blurb(record))assert(r.container.html.includes(esc(Reader.blurb(record))));}
 assert(!r.container.html.includes('research-pagination'));assert(!r.container.html.includes('data-list-page'));assert.equal(r.context.state.p,999,'Rendering does not rewrite shared URL state or force a selected descendant page');
 for(const button of r.container.buttons){const node=r.nodes.get(button.dataset.listNode);button.onclick();const action=r.calls.at(-1);assert.equal(action.branch,node.id,'A branch click uses the exact child rather than skipping scope levels');assert.deepEqual(Object.keys(action).sort(),['branch','record']);}
}
const root=render('all-research');assert.equal(root.container.buttons.length,6);assert(!root.container.html.includes('Open full record'),'Root never flattens descendant records into a wall');
const recordParent=data.views.all.nodes.find(n=>n.children.length&&n.children.every(id=>data.views.all.nodes.find(child=>child.id===id).kind==='record'));
const colored=render(recordParent.id,{colour:'results'}),child=colored.nodes.get(recordParent.children[0]),record=data.records[child.record_id];
assert(colored.container.html.includes('--branch-colour:'+colored.context.resultColours[record.outcome]));assert(colored.container.html.includes('href="'+record.href+'"'));assert(colored.container.html.includes(esc(Reader.title(record))));
const filtered=render('all-research',{matches:[record.id]});for(const button of filtered.container.buttons){const node=filtered.nodes.get(button.dataset.listNode);assert.equal(button.disabled,!node.members.includes(record.id));}
const filteredRecords=render(recordParent.id,{matches:[record.id]});assert.deepEqual(filteredRecords.container.links.map(a=>a.href),[record.href],'Unmatched terminal records must not retain active links through filters');for(const id of recordParent.children)assert(filteredRecords.container.html.includes(esc(Reader.title(data.records[colored.nodes.get(id).record_id]))),'Unmatched immediate records retain their authored identity');
assert(filtered.container.html.includes('1 matching record</span>'));const empty=render('all-research',{matches:[]});assert(empty.container.html.includes('No matching research'));assert(empty.container.buttons.every(b=>b.disabled));
const css=fs.readFileSync(require.resolve('../research-browser.css'),'utf8');assert(css.includes('.research-branch-copy{display:block;min-width:0;flex:1;overflow-wrap:anywhere}'));assert(css.includes('min-height:64px'));
assert.equal(JSON.stringify(data.records),originalRecordMetadata,'Navigation rendering cannot rewrite authored findings, scope, evaluation or record metadata');
// Run the actual wheel/button and pinch paths: touching a fitted dense view must not snap its scale.
const pointerState=source.match(/^ function pointerState\(.*$/m)[0],pointerMove=source.split('\n').find(line=>line.startsWith(" svg.addEventListener('pointermove'")),zoom=source.match(/^ function zoom\(.*$/m)[0];
for(const scale of [.08,.1,.28,1,4,5,8])for(const factor of [.25,1,2]){
 let move;const context={camera:{x:0,y:0,k:scale},gesture:{center:{x:50,y:0},distance:100,camera:{x:0,y:0,k:scale}},moved:false,
  activePointers:new Map([[1,{x:0,y:0}],[2,{x:100,y:0}]]),map:{getBoundingClientRect:()=>({left:0,top:0,width:320,height:650})},applyCamera(){},svg:{addEventListener(type,handler){move=handler}}};
 vm.createContext(context);vm.runInContext(pointerState+'\n'+pointerMove+'\n'+zoom,context);move({pointerId:2,clientX:100*factor,clientY:0});const pinched=context.camera.k;
 context.camera={x:0,y:0,k:scale};context.zoom(factor);assert.equal(pinched,context.camera.k,'Pinch and button/wheel zoom share exact limits at '+scale+' × '+factor);
 if(factor===1)assert.equal(pinched,scale,'Starting a two-finger gesture preserves the current scale');
}
console.log('PASS map List: every branch exposes exactly one level, direct native record links, exact scope/filtering/counts/colors, no duplicate record actions or pagination, metadata unchanged, wrapping/touch targets.');

// Interest is a separate ordering of the same children, never a new classification.
{
 const parent=data.views.all.nodes.find(n=>n.children.length>1&&n.children.every(id=>data.views.all.nodes.find(x=>x.id===id)?.kind==='record'));assert(parent);
 const ids=parent.children.map(id=>data.views.all.nodes.find(n=>n.id===id).record_id),counts=Object.fromEntries(ids.map(id=>[id,0]));counts[ids.at(-1)]=7;
 const top=render(parent.id,{sort:'top',counts});assert(top.container.links[0].href.endsWith('/'+ids.at(-1)));assert(top.container.html.includes('7 upvotes'));assert(top.container.html.includes('community interest'));assert(!top.container.html.includes('At least '));
 const partial=render(parent.id,{sort:'top',counts:{[ids[0]]:3}});assert(partial.container.html.includes('Some vote counts are unavailable'));assert(partial.container.html.includes('At least '));
 const root=render('all-research',{sort:'top',counts});assert.equal(root.container.buttons.length,6);assert(root.container.html.includes('across matching records'));
 const saved=render('all-research',{saved:true,matches:[ids[0]]});assert.equal(saved.container.buttons.length,1,'Saved traverses only the branch containing a bookmark');
 const empty=render('all-research',{saved:true,matches:[]});assert.equal(empty.container.buttons.length,0);assert(empty.container.html.includes('No saved research here'));
 const Model=require('../research-browser-model.js');assert.equal(Model.read('#saved=1&sort=top','list',Index.state).saved,'1');assert.equal(Model.read('#saved=1&sort=top','list',Index.state).sort,'top');assert.equal(Model.read('#saved=true','list',Index.state).saved,undefined);
 assert.equal(JSON.stringify(data.records),originalRecordMetadata,'Interest sorting and local bookmark filtering cannot edit evidence');
 console.log('PASS interest sorting, unknown vote counts, saved-only branch traversal, empty recovery and evidence separation');
}

// A vote acknowledgement changes neither the bookmark filter nor focused DOM.
{
 let renders=0,refreshes=0,buttons=0;const c={savedPreferenceKey:'one-record',data:{},state:{saved:'1'},reactions:{refresh(){refreshes++;}},render(){renders++;},updateSavedButton(){buttons++;}};vm.createContext(c);vm.runInContext(source.split('\n').find(line=>line.startsWith(' function preferencesChanged(')),c);
 c.preferencesChanged({saved:['one-record'],upvoted:['one-record']});assert.equal(renders,0);assert.equal(refreshes,1);assert.equal(buttons,1);
 c.preferencesChanged({saved:['one-record','two-record'],upvoted:['one-record']});assert.equal(renders,1);
 c.preferencesChanged({saved:['one-record','two-record'],upvoted:[]});assert.equal(renders,1,'Withdrawing a vote must preserve the same focused record controls');
 c.state.saved='';c.preferencesChanged({saved:[],upvoted:[]});assert.equal(renders,1,'A bookmark change outside Saved does not replace the page');
 console.log('PASS vote acknowledgements and cross-tab vote changes preserve focused controls; only bookmark changes refresh an active Saved filter');
}

// Navigation descriptions explain the actual method and cannot revive legacy labels.
{
 const navigation=require('../research-method-navigation.js'),shown=render('solve-lp2');
 for(const id of ['method:repeating-key','method:running-key','method:feedback','method:payload']){
  assert(shown.container.innerHTML.includes(navigation.LABELS[id]));
  assert(shown.container.innerHTML.includes(navigation.DESCRIPTIONS[id]));
 }
 assert(!shown.container.innerHTML.includes('Using another text as the key'));
 assert(!shown.container.innerHTML.includes('Using the number grid'));
 const node=data.views.all.nodes.find(n=>n.id==='method:running-key'),prior=node.description;
 node.description='<img src=x onerror=bad>';const escaped=render('solve-lp2').container.innerHTML;
 assert(escaped.includes('&lt;img src=x onerror=bad&gt;'));assert(!escaped.includes('<img src=x'));node.description=prior;
 console.log('PASS branch descriptions use reviewed method labels, escape text and avoid legacy key-source headings.');
}
