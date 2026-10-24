/* Actual render/Sort callbacks and camera resize function; no browser or network. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../research-browser.js'),'utf8');
function production(name){const at=source.search(new RegExp('^ function '+name+'\\(','m'));assert(at>=0,name);let code='';for(const line of source.slice(at).split('\n')){code+=line+'\n';try{new vm.Script(code);return code}catch(e){if(!/Unexpected end of input/.test(e.message))throw e}}throw Error(name)}
const read=name=>JSON.parse(fs.readFileSync(require.resolve('../'+name),'utf8'));
const Index=require('../research-index.js'),data=require('../research-browser-model.js').build(read('data/research-map.json'),read('data/experiments.json'));
const allNodes=new Map(data.views.all.nodes.map(n=>[n.id,n]));
const parent=data.views.all.nodes.find(n=>n.children.length>1&&n.children.every(id=>allNodes.get(id).kind==='record'));
const requested={view:'all',branch:parent.id,mode:'list',q:'',type:'',method:'',family:'',result:'',page:'',sort:'title',record:'',colour:'methods',p:1};
const doc={body:{dataset:{},classList:{toggle(){}}},activeElement:null,querySelectorAll:()=>[],querySelector:()=>modalOpen?dialog:null};doc.activeElement=doc.body;
const elements=new Map();let modalOpen=false;
function element(id){const attrs={};return{id,dataset:{},style:{},inert:false,isConnected:true,hidden:false,scrollTop:0,classList:{toggle(){}},setAttribute(k,v){attrs[k]=String(v)},getAttribute:k=>attrs[k]??null,removeAttribute(k){delete attrs[k]},focus(){doc.activeElement=this},querySelectorAll:()=>[],querySelector:()=>null}}
const container=element('research-list');let sortNode;
Object.defineProperty(container,'innerHTML',{set(html){if(sortNode){sortNode.isConnected=false;if(doc.activeElement===sortNode)doc.activeElement=doc.body}this.html=html;sortNode=html.includes('id="research-sort"')?element('research-sort'):null},get(){return this.html}});
container.querySelector=selector=>selector==='#research-sort'?sortNode:null;
const dialog=element('map-dialog');dialog.showModal=()=>{modalOpen=true;doc.activeElement=dialog.options?.[0]||dialog};dialog.close=()=>{modalOpen=false};dialog.querySelectorAll=()=>dialog.options||[];
const dialogBody=element('map-dialog-body');Object.defineProperty(dialogBody,'innerHTML',{set(html){dialog.options=[...html.matchAll(/data-sort="([^"]+)"/g)].map(m=>({...element('sort-'+m[1]),dataset:{sort:m[1]}}))}});
for(const id of ['map-trail','page-button','result-key','display-button','map-status','map-dialog-title','close-map-dialog','map-workspace'])elements.set(id,element(id));elements.set('research-list',container);elements.set('map-dialog-body',dialogBody);
const map=element('map'),panel=element('inspector'),heading=element('preview-heading');panel.querySelector=()=>heading;
const c={document:doc,ResearchIndex:Index,data,map,panel,dialog,dialogReturn:null,state:null,previous:'',previousRecord:'',lastGraphKey:'',preferredMode:'graph',indexResult:null,matching:new Set(),nodes:null,focus:null,layout:new Map(),listPositions:new Map(),listKey:'',camera:{x:21,y:-34,k:2.3},fitCalls:0,revealCalls:0,applyCalls:0,
 read:()=>structuredClone(requested),$:id=>id==='research-sort'?sortNode:elements.get(id),esc:String,aliases:{},outcomes:Index.outcomes,sorts:{title:'Title A–Z','title-desc':'Title Z–A',recent:'Recently checked'},resultColours:{},arrow:'',chevron:'',scopeLabel:()=>'',clearFilters(){},filteredChips(){},position(){},paintGraph(){},fit(){c.fitCalls++},revealSelection(){c.revealCalls++},applyCamera(){c.applyCalls++},showInspector(){panel.hidden=!c.state.record},requestAnimationFrame:fn=>fn(),url:next=>'#'+new URLSearchParams(next),navigate(changes){Object.assign(requested,changes);c.render()}};
vm.createContext(c);vm.runInContext(source.match(/^ const count=.*$/m)[0],c);
for(const name of ['passes','recordNode','renderList','openDialog','closeDialog','render'])vm.runInContext(production(name),c);
// The complete production Sort path closes its dialog, focuses the old action,
// and replaces List DOM. The new action must regain focus after replacement.
c.render();const oldSort=sortNode;oldSort.onclick();assert(modalOpen);const descending=dialog.options.find(n=>n.dataset.sort==='title-desc');descending.onclick();
assert(!modalOpen);assert.equal(requested.sort,'title-desc');assert.notEqual(sortNode,oldSort);assert.equal(doc.activeElement,sortNode,'Sort must not leave keyboard focus on body after replacing its trigger');
// An unchanged research context retains the camera when returning from List.
requested.mode='graph';c.render();const initialFits=c.fitCalls;c.camera={x:213,y:-145,k:2.3};
requested.mode='list';c.render();const before=c.revealCalls;requested.mode='graph';c.render();
assert.equal(c.fitCalls,initialFits,'Graph/List mode does not refit the research context');assert.equal(c.camera.k,2.3);assert.equal(c.camera.x,213);assert.equal(c.camera.y,-145);assert(c.revealCalls>before,'Returning to Graph reveals the retained context');
// Old List+record URLs still reach the exact full record, rather than reviving a
// floating preview. Actual navigate also clears a Graph selection on List entry.
const redirected=[];c.location={replace:href=>redirected.push(href)};
requested.mode='list';requested.record=parent.members[0];c.render();assert.deepEqual(redirected,[data.records[requested.record].href]);
requested.mode='graph';requested.record='';c.render();
const navigation={state:{...requested,record:parent.members[0]},listKey:'',preferredMode:'graph',localStorage:{setItem(){}},$:()=>container,url:next=>JSON.stringify(next),location:{hash:''},render(){throw Error('Unexpected same-route render')}};
vm.createContext(navigation);vm.runInContext(production('navigate'),navigation);navigation.navigate({mode:'list'});const listRoute=JSON.parse(navigation.location.hash);assert.equal(listRoute.record,'');assert.equal(listRoute.branch,parent.id);assert.equal(listRoute.mode,'list');
const fitsBeforeFilter=c.fitCalls;requested.q='no-such-phrase-12345';requested.record='';c.render();assert.equal(c.fitCalls,fitsBeforeFilter+1,'Changed filtering gets a fresh geometric fit');
// Run actual resize math against a movable map viewport. Preserve the world
// coordinate at the screen centre and the zoom; only first use is allowed to Fit.
let size={width:600,height:450};const resize={data:{},state:{mode:'graph'},camera:{x:140,y:-70,k:2.4},cameraViewport:{width:600,height:450},map:{getBoundingClientRect:()=>({...size,left:0,top:0})},fitCalls:0,revealCalls:0,applyCalls:0,fit(){resize.fitCalls++},updatePreviewMode(){},revealSelection(){resize.revealCalls++},applyCamera(){resize.applyCalls++}};
vm.createContext(resize);vm.runInContext(production('reframe'),resize);
const centre=()=>({x:(size.width/2-resize.camera.x)/resize.camera.k,y:(size.height/2-resize.camera.y)/resize.camera.k});const worldCentre=centre();
size={width:390,height:600};resize.reframe();assert.equal(resize.camera.k,2.4);assert.deepEqual(centre(),worldCentre);assert.equal(resize.fitCalls,0);assert.equal(resize.applyCalls,1);
size={width:1440,height:700};resize.reframe();assert.deepEqual(centre(),worldCentre);assert.equal(resize.camera.k,2.4);assert.equal(resize.applyCalls,2);
resize.cameraViewport=null;resize.reframe();assert.equal(resize.fitCalls,1,'Initial sizing may Fit rather than preserve a nonexistent camera');
resize.state.mode='list';const lastCamera={...resize.camera};size={width:0,height:0};resize.reframe();assert.deepEqual(resize.camera,lastCamera,'Hidden List layout cannot corrupt the saved graph camera');
// Execute the production record panel rather than inventing a generic preview:
// exact authored finding/limit/link remain attached to the selected record.
const escapeHTML=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let panelHTML='',backButton,recordLink;Object.defineProperty(panel,'innerHTML',{set(html){panelHTML=html;backButton=element('preview-back');recordLink=element('record-open');heading.isConnected=true},get(){return panelHTML}});
panel.querySelector=selector=>selector==='h2'?heading:selector.includes('record-open')?recordLink:backButton;
c.esc=escapeHTML;c.arrow='';c.previewExpanded=false;c.innerWidth=390;
vm.runInContext(production('updatePreviewMode')+'\n'+production('pageRanges')+'\n'+production('showInspector'),c);
requested.q='';requested.mode='graph';requested.record=parent.members[0];c.render();const record=data.records[requested.record];
assert.equal((panelHTML.match(/<button\b/g)||[]).length,1,'Record workspace has one Back control, not expand and close affordances');
assert(/>[^<]*Back\b|aria-label="Back\b/.test(panelHTML),'The single control explains its return action');
assert(panelHTML.includes(escapeHTML(record.reader_finding||record.finding)));assert(panelHTML.includes(escapeHTML(record.reader_limit||record.limitations)));assert(panelHTML.includes('href="'+escapeHTML(record.href)+'"'));
assert(panelHTML.includes(escapeHTML(c.pageRanges(record.pages))),'Tested material stays bound to the selected record pages');
assert.equal(map.inert,true,'Mobile full-workspace record view blocks graph keyboard targets');assert.equal(container.inert,true,'Underlying List controls are also unavailable while the mobile record is shown');assert.equal(doc.activeElement,heading);
backButton.onclick();assert.equal(requested.record,'');assert.equal(panel.hidden,true);assert.equal(map.inert,false);assert.equal(container.inert,false);assert.equal(doc.activeElement,map,'Back returns keyboard focus to the same graph workspace');assert.equal(requested.branch,parent.id);
requested.record=parent.members[0];c.render();let escaped=false;panel.onkeydown({key:'Escape',preventDefault(){escaped=true}});assert(escaped);assert.equal(requested.record,'');assert.equal(doc.activeElement,map);assert.equal(map.inert,false);
requested.record=parent.members[0];c.innerWidth=1200;c.render();assert.equal(map.inert,false,'Desktop side pane leaves the graph available');assert.equal(container.inert,false);
console.log('PASS research navigation: Sort restores replacement focus; Graph/List preserves camera; legacy List links open exact records; mobile preview is source-bound, inert and returns focus via Back/Escape; resize retains world centre and zoom.');
