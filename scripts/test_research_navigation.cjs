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
for(const name of ['passesRecordFilters','passes','recordNode','renderList','openDialog','closeDialog','render'])vm.runInContext(production(name),c);
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
panel.querySelector=selector=>selector==='h2'?heading:selector.includes('record-open')?recordLink:selector==='.preview-back'?backButton:null;
c.RecordFollowupView=require('../record-followup-view.js');c.esc=escapeHTML;c.arrow='';c.previewExpanded=false;c.innerWidth=390;
vm.runInContext(production('updatePreviewMode')+'\n'+production('pageRanges')+'\n'+production('readerLimit')+'\n'+production('previewScopeHTML')+'\n'+production('previewFollowupsHTML')+'\n'+production('bindPreviewFollowups')+'\n'+production('showInspector'),c);
requested.q='';requested.mode='graph';requested.record=parent.members[0];c.render();const record=data.records[requested.record];
assert.equal((panelHTML.match(/<button\b/g)||[]).length,1,'Record workspace has one Back control, not expand and close affordances');
assert(/>[^<]*Back\b|aria-label="Back\b/.test(panelHTML),'The single control explains its return action');
assert(panelHTML.includes(escapeHTML(record.reader_finding||record.finding)));assert(panelHTML.includes(escapeHTML(c.readerLimit(record.reader_limit||record.limitations))));assert(panelHTML.includes('href="'+escapeHTML(record.href)+'"'));
assert(panelHTML.includes(escapeHTML(c.pageRanges(record.pages))),'Tested material stays bound to the selected record pages');
assert.equal(map.inert,true,'Mobile full-workspace record view blocks graph keyboard targets');assert.equal(container.inert,true,'Underlying List controls are also unavailable while the mobile record is shown');assert.equal(doc.activeElement,heading);
backButton.onclick();assert.equal(requested.record,'');assert.equal(panel.hidden,true);assert.equal(map.inert,false);assert.equal(container.inert,false);assert.equal(doc.activeElement,map,'Back returns keyboard focus to the same graph workspace');assert.equal(requested.branch,parent.id);
requested.record=parent.members[0];c.render();let escaped=false;panel.onkeydown({key:'Escape',preventDefault(){escaped=true}});assert(escaped);assert.equal(requested.record,'');assert.equal(doc.activeElement,map);assert.equal(map.inert,false);
requested.record=parent.members[0];c.innerWidth=1200;c.render();assert.equal(map.inert,false,'Desktop side pane leaves the graph available');assert.equal(container.inert,false);
// Follow-up actions use the actual inspector helpers and the destination parser.
const selectedId=requested.record,originalRecord=data.records[selectedId];
const declared=read('experiments/records/lp2-known-vigenere-keys/record.json').browser_followups[0];const followup=(id,title,scope_change)=>({...structuredClone(declared),id,title,scope_change});data.records[selectedId]={...originalRecord,browser_followups:[followup('fixed-scope-control','A <fixed> continuation','Only the declared page scope.')]};c.showInspector();
assert(panelHTML.includes('Try a follow-up'));assert(panelHTML.includes('A &lt;fixed&gt; continuation'));assert(panelHTML.includes('Only the declared page scope.'));
const href=panelHTML.match(/href="(run\.html#record=[^"]+)"/)[1].replace(/&amp;/g,'&'),followupURL=new URL(href,'https://example.org/');
assert.equal(followupURL.pathname,'/run.html');assert.equal(followupURL.search,'');assert.deepEqual(require('../record-followups.js').reference(followupURL.hash),{kind:'record',recordId:selectedId,followupId:'fixed-scope-control',id:selectedId+'/fixed-scope-control'});
assert.equal(requested.record,selectedId,'Rendering an explicit follow-up link does not navigate or create a task');
data.records[selectedId].browser_followups.push(followup('another-control','Another setting','Different declared page bounds.'));
const setting={value:'fixed-scope-control'},selectedScope={textContent:''},selectedLink={href:'run.html#record='+selectedId+'&followup=fixed-scope-control'},priorQuery=panel.querySelector;panel.querySelector=selector=>({'[data-prepared-setting]':setting,'[data-prepared-scope]':selectedScope,'[data-prepared-link]':selectedLink}[selector]||priorQuery(selector));c.showInspector();assert(panelHTML.includes('data-prepared-setting'));assert.equal((panelHTML.match(/Review follow-up/g)||[]).length,1);setting.value='another-control';setting.onchange();assert.equal(selectedScope.textContent,'Different declared page bounds.');assert.equal(require('../record-followups.js').reference(new URL(selectedLink.href,'https://example.org/').hash).followupId,'another-control');assert.equal(requested.record,selectedId);panel.querySelector=priorQuery;
data.records[selectedId]={...originalRecord};delete data.records[selectedId].browser_followups;c.showInspector();assert(!panelHTML.includes('Review follow-up'),'No authored recipe means no generic runnable action');data.records[selectedId]=originalRecord;

// The new availability filter intersects the shared selector on both views.
const allBefore=JSON.stringify(data.records),F=require('../record-followup-view.js');
Object.assign(requested,{branch:'',record:'',q:'',type:'',method:'',family:'',result:'',page:'',mode:'graph',followups:'1'});c.render();
const eligible=Index.select(Object.values(data.records),{sort:requested.sort}).allRecords.filter(r=>!r.community&&F.recipes(data.records[r.id]).length).map(r=>r.id).sort();
assert(eligible.length>0);assert.deepEqual([...c.matching].sort(),eligible);assert.equal(vm.runInContext('count(focus)',c),eligible.length);
assert.equal(c.passesRecordFilters({...data.records[eligible[0]],community:true}),false,'A community entry cannot borrow canonical follow-up availability');
const unsafeId='invalid-followup-filter-fixture';data.records[unsafeId]={id:unsafeId,pages:['lp2-00'],browser_followups:[{id:'../unsafe',title:'Invalid',scope_change:'Not a usable recipe'}]};assert.equal(c.passesRecordFilters(data.records[unsafeId]),false,'Invalid declarations do not produce a runnable branch');delete data.records[unsafeId];
const graphMatches=[...c.matching].sort(),graphFocus=c.focus.id;requested.mode='list';c.render();assert.deepEqual([...c.matching].sort(),graphMatches);assert.equal(c.focus.id,graphFocus);assert(container.innerHTML.includes(eligible.length+' matching records'));
const followupBranch=data.views.all.nodes.find(n=>n.kind!=='record'&&n.id!=='all-research'&&n.members.some(id=>eligible.includes(id)));requested.branch=followupBranch.id;c.render();assert.equal(c.focus.id,followupBranch.id);assert.equal(requested.followups,'1');assert.equal(vm.runInContext('count(focus)',c),followupBranch.members.filter(id=>eligible.includes(id)).length,'Drilling retains the same availability intersection');
requested.page='lp2-54';c.render();assert([...c.matching].every(id=>data.records[id].pages.includes('lp2-54')),'Page scope intersects availability');
requested.q='zzzzno-such-followupzzzz';c.render();assert.equal(c.matching.size,0);assert(container.innerHTML.includes('No matching research'));assert(container.innerHTML.includes('data-clear-all'));assert(container.innerHTML.includes('data-search-all'));
assert.equal(JSON.stringify(data.records),allBefore,'Filtering never mutates canonical records');
Object.assign(requested,{q:'',page:'',followups:'',branch:'',record:''});c.render();

// Exercise the actual dialog options, filter chips and reset callbacks.
let lastDialog='',changes=null,closed=0;const optionHolder={innerHTML:''},chipHolder={hidden:true,innerHTML:'',querySelectorAll(){return this.buttons||[]}},badge={},title={},body={innerHTML:''},back={},reset={};
const buttons=()=>[...optionHolder.innerHTML.matchAll(/data-filter-value="([^"]*)"/g)].map(m=>({dataset:{filterValue:m[1]}}));
const filterContext={data,focus:allNodes.get('all-research'),state:{...requested,followups:'1'},ResearchIndex:Index,indexResult:{topics:new Map(),families:new Map()},outcomes:Index.outcomes,esc:escapeHTML,chevron:'',navigate(value){changes=value},closeDialog(){closed++},openDialog(title,html){lastDialog=html},$:id=>({'map-dialog-title':title,'map-dialog-body':body,'research-filter-button':{},'research-filter-chips':chipHolder,'research-filter-count':badge}[id]),dialog:{querySelector:selector=>({'.filter-options':optionHolder,'#back-to-filters':back,'#reset-research-filters':reset}[selector]||null),querySelectorAll:selector=>selector==='[data-filter-value]'?(filterContext.options=buttons()):[]}};
vm.createContext(filterContext);for(const name of ['filterMenu','filterOptions','filteredChips','clearFilters'])vm.runInContext(production(name),filterContext);
filterContext.filterMenu();assert(lastDialog.includes('data-filter-field="followups"'));assert(lastDialog.includes('Browser follow-ups'));assert(lastDialog.includes('With browser follow-ups'));
filterContext.filterOptions('followups');assert.equal(title.textContent,'Browser follow-ups');assert(body.innerHTML.includes('A result may already have been saved'));assert(optionHolder.innerHTML.includes('data-filter-value="1" aria-pressed="true"'));assert(!body.innerHTML.includes('untested'));
filterContext.options.find(b=>b.dataset.filterValue==='').onclick();assert.equal(changes.followups,'');assert.equal(changes.record,'');assert.equal(closed,1);
chipHolder.buttons=[{dataset:{clearFilter:'followups'}}];filterContext.filteredChips();assert(!chipHolder.hidden);assert(chipHolder.innerHTML.includes('Clear browser follow-ups filter'));assert.equal(badge.textContent,1);chipHolder.buttons[0].onclick();assert.equal(changes.followups,'');
filterContext.clearFilters();assert.equal(changes.followups,'');assert.equal(changes.page,'');assert.equal(changes.q,'');
filterContext.state.followups='';chipHolder.buttons=[];filterContext.filteredChips();assert(chipHolder.hidden);assert.equal(badge.hidden,true);
const filterNavigation={...navigation,state:{...requested,followups:'1',p:9},location:{hash:''}};vm.createContext(filterNavigation);vm.runInContext(production('navigate'),filterNavigation);filterNavigation.navigate({mode:'graph',branch:followupBranch.id});assert.equal(JSON.parse(filterNavigation.location.hash).followups,'1');filterNavigation.navigate({followups:''});assert.equal(JSON.parse(filterNavigation.location.hash).p,1,'Changing availability resets legacy pagination');
console.log('PASS browser follow-up filter: validated canonical recipes, selector/page intersection, shared Graph/List counts, retained branch drill, empty recovery, no data mutation, dialog choices/chip/badge/reset.');

console.log('PASS research navigation: Sort restores replacement focus; Graph/List preserves camera; legacy List links open exact records; mobile preview is source-bound, inert and returns focus via Back/Escape; resize retains world centre and zoom.');
