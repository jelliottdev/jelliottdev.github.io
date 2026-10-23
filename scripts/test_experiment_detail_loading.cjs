/* Per-record detail loading and deferred related metadata; no browser/network. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),full=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'))).records;
const discovery=JSON.parse(fs.readFileSync(path.join(root,'data/experiment-index.json')));
const source=fs.readFileSync(path.join(root,'experiments.js'),'utf8');
const fixture=full.find(record=>record.id==='word-internal-affine-lags');
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const okay=data=>({ok:true,json:async()=>data});
function harness(){
 const pending=new Map(),events=[];let html='',slot=null;
 const context={esc,renderId:1,head:()=>'',footer:()=>'',document:{activeElement:null},
  fetch:url=>{events.push('fetch:'+url);return new Promise((resolve,reject)=>{const requests=pending.get(url)||[];requests.push({resolve,reject});pending.set(url,requests)})}};
 function target(initial=''){
  let content=initial,links=[];
  const node={isConnected:true,writes:0,attributes:{},hidden:false,disabled:false,textContent:'',
   get innerHTML(){return content},set innerHTML(value){content=value;this.writes++;for(const link of links)link.isConnected=false;
    links=[...value.matchAll(/<a href="([^"]+)"/g)].map(([,href])=>({isConnected:true,parent:node,getAttribute:()=>href,focus(){context.document.activeElement=this}}));},
   contains:active=>active?.parent===node,
   setAttribute(key,value){this.attributes[key]=value},focus(){context.document.activeElement=this},
   querySelectorAll:selector=>selector==='a'?links:[],querySelector:selector=>selector==='a'?links[0]||null:null};
  node.innerHTML=initial;node.writes=0;return node;
 }
 context.document.createElement=()=>target();
 context.main={get innerHTML(){return html},set innerHTML(value){
  if(slot)slot.isConnected=false;html=value;events.push('render');
  const id=value.match(/class="experiment-extra experiment-related" data-record="([^"]+)"/)?.[1];
  if(!id){slot=null;return;}
  const family=target(value.match(/<div data-family-members>([\s\S]*?)<\/div>/)?.[1]||''),other=target(value.match(/<div data-related-records>([\s\S]*?)<\/div>/)?.[1]||'');
  const status=target(),retry=target(),index=target();retry.hidden=true;
  slot={isConnected:true,open:false,dataset:{record:id},family,other,status,retry,index,
   querySelector:selector=>({'[data-family-members]':family,'[data-related-records]':other,'[data-related-status]':status,'[data-related-retry]':retry,'[data-related-index]':index}[selector]||null)};
 },querySelector:selector=>selector==='.experiment-related'?slot:null};
 vm.createContext(context);vm.runInContext(source,context);
 for(const name of ['bindRouteIllustration','bindLanguageBlockFigure','bindAffineLagFigure','bindBlockBoundaryFigure','startExperimentSupport'])context[name]=()=>{};
 return {context,pending,events,get slot(){return slot},next(url){const requests=pending.get(url);assert(requests?.length,'Expected '+url);return requests.shift()}};
}
(async()=>{
 const h=harness(),url=`reference/experiments/${fixture.id}.json`,opening=h.context.experimentsPage(fixture.id,1);
 assert.deepEqual(h.events,['fetch:'+url],'Cold primary load requests only its individual record');
 const shared=h.context.ensureExperimentRecord(fixture.id);assert.equal(h.pending.get(url).length,1,'Same-ID requests share one fetch');
 h.next(url).resolve(okay(fixture));await opening;assert.equal(await shared,fixture);
 assert(h.context.main.innerHTML.includes(esc(fixture.reader_finding||fixture.finding)));
 assert(h.context.main.innerHTML.includes('downloads/experiments/'+fixture.id+'.zip'));
 assert(h.context.main.innerHTML.includes('data-results='),'Primary native figure renders before metadata');
 assert(h.context.main.innerHTML.includes('id="experiment-family"'),'Family deep-link target exists before metadata arrives');
 assert(h.events.indexOf('render')<h.events.indexOf('fetch:data/experiment-index.json'));
 assert(vm.runInContext('experimentRecords===undefined&&checkerRecords===undefined&&researchRecords===undefined',h.context),'Individual row does not fill any catalog cache');
 const slot=h.slot;slot.open=true;const stableHeading={parent:slot};h.context.document.activeElement=stableHeading;
 assert(!h.context.main.innerHTML.includes('No other completed variant'),'Pending is not an empty family');
 h.next('data/experiment-index.json').resolve(okay(discovery));await flush();
 assert.equal(slot.open,true);assert.equal(h.context.document.activeElement,stableHeading,'Stable heading/anchor focus survives metadata arrival');
 assert.equal(h.events.filter(event=>event==='render').length,1,'Optional metadata never recreates the primary page');
 assert(slot.family.innerHTML.includes('#/experiments/'+fixture.id));assert.equal(slot.status.hidden,true);
 const writes=slot.family.writes;const focused=slot.family.querySelector('a');focused.focus();
 await slot.retry.onclick();assert.equal(slot.family.writes,writes,'Identical updates preserve link nodes');assert.equal(h.context.document.activeElement,focused);
 assert.equal(await h.context.ensureExperimentRecord(fixture.id),fixture,'Individual record cache survives navigation');
 const noRelations=full.find(record=>!record.family&&!record.related.length),standalone=harness();
 const standaloneLoad=standalone.context.experimentsPage(noRelations.id,1);standalone.next(`reference/experiments/${noRelations.id}.json`).resolve(okay(noRelations));await standaloneLoad;
 assert.equal(standalone.events.filter(event=>event.startsWith('fetch:')).length,1,'Records without relationships need no catalog');
 const warm=harness();warm.context.complete=full;vm.runInContext('experimentRecords=complete',warm.context);await warm.context.experimentsPage(fixture.id,1);
 assert.equal(warm.events.filter(event=>event.startsWith('fetch:')).length,0,'Warm full records serve both primary and relationships');
 const coldChecker=h.context.ensureCheckerRecords();assert(h.pending.has('data/checker-records.json'),'One cached individual record cannot stand in for the checker catalog');
 h.next('data/checker-records.json').resolve(okay(JSON.parse(fs.readFileSync(path.join(root,'data/checker-records.json')))));await coldChecker;
 assert(vm.runInContext('experimentRecords===undefined',h.context));
 const retry=harness();const attempt=retry.context.experimentsPage(fixture.id,1);retry.next(url).resolve(okay(fixture));await attempt;
 retry.next('data/experiment-index.json').reject(new Error('Offline'));await flush();
 const recovering=retry.slot;assert(!recovering.retry.hidden);assert(recovering.status.textContent.includes('finding and files remain available'));
 assert(retry.context.main.innerHTML.includes('Download experiment ZIP'));recovering.retry.focus();
 const first=recovering.retry.onclick(),second=recovering.retry.onclick();assert(recovering.retry.disabled&&!recovering.retry.hidden);
 assert.equal(retry.pending.get('data/experiment-index.json').length,1,'Repeated retry activation shares one request');
 retry.next('data/experiment-index.json').resolve(okay(discovery));await Promise.all([first,second]);
 assert(recovering.retry.hidden);assert.equal(retry.context.document.activeElement,recovering.family.querySelector('a'),'Successful retry restores visible focus');
 for(const failure of [false,true]){
  const stale=harness(),old=stale.context.experimentsPage(fixture.id,1);stale.next(url).resolve(okay(fixture));await old;
  stale.context.renderId=2;stale.context.main.innerHTML='<h1>New route</h1>';
  const request=stale.next('data/experiment-index.json');if(failure)request.reject(Error('Late error'));else request.resolve(okay(discovery));await flush();
  assert.equal(stale.context.main.innerHTML,'<h1>New route</h1>');
  const recordRace=harness(),loading=recordRace.context.experimentsPage(fixture.id,1);recordRace.context.renderId=2;recordRace.context.main.innerHTML='New record destination';
  const pending=recordRace.next(url);if(failure){pending.reject(Error('Late record error'));await assert.rejects(loading,/Late record/)}else{pending.resolve(okay(fixture));await loading}
  assert.equal(recordRace.context.main.innerHTML,'New record destination');
 }
 for(const bad of [{...fixture,id:'wrong-id'},{...fixture,status:'draft'},{...fixture,reproduction:undefined}]){
  const invalid=harness(),loading=invalid.context.ensureExperimentRecord(fixture.id);invalid.next(url).resolve(okay(bad));await assert.rejects(loading,/invalid format/);
  const again=invalid.context.ensureExperimentRecord(fixture.id);invalid.next(url).resolve(okay(fixture));assert.equal(await again,fixture);
 }
 const missing=harness(),load=missing.context.ensureExperimentRecord(fixture.id);missing.next(url).resolve({ok:false});await assert.rejects(load,/could not be loaded/);
 const retryMissing=missing.context.ensureExperimentRecord(fixture.id);missing.next(url).resolve(okay(fixture));await retryMissing;
 await assert.rejects(missing.context.ensureExperimentRecord('../bad'),/no published record/);
 const distinct=harness(),ids=full.slice(0,2).map(record=>record.id),loads=ids.map(id=>distinct.context.ensureExperimentRecord(id));
 for(const id of ids)distinct.next(`reference/experiments/${id}.json`).resolve(okay(full.find(record=>record.id===id)));assert.equal((await Promise.all(loads)).length,2);
 // Every existing individual export remains complete and yields identical finding/figure/file links.
 const compare=harness().context,catalog=discovery.records.map(record=>({...record,scope:{pages:record.pages,artifacts:record.artifacts||[]}}));
 const attr=(html,name)=>[...html.matchAll(new RegExp(name+'="([^"]+)"','g'))].map(match=>match[1]).sort();
 for(const record of full){
  const single=JSON.parse(fs.readFileSync(path.join(root,'reference/experiments',record.id+'.json')));assert.deepEqual(single,record);assert(compare.validExperimentRecord(single,record.id));
  const a=compare.experimentArticle(record,full),b=compare.experimentArticle(single,catalog);
  assert.deepEqual(attr(a,'href'),attr(b,'href'),'Detail links preserved: '+record.id);assert.deepEqual(attr(a,'src'),attr(b,'src'),'Figures preserved: '+record.id);
  if(record.family){
   const members=full.filter(item=>item.family?.id===record.family.id).map(item=>item.id);
   const markup=compare.experimentFamily(single,catalog);
   for(const id of members)assert.equal(markup.split('href="#/experiments/'+id+'"').length-1,members.length===1?0:1,'Every sibling appears once: '+id);
  }
  assert.equal(compare.experimentOtherRelated(record,full),compare.experimentOtherRelated(single,catalog));
 }
 console.log(`PASS: per-ID shared/cache/validation/retry/races, primary-before-related metadata, focus/disclosure continuity, and all ${full.length} complete detail links/figures/family IDs.`);
})().catch(error=>{console.error(error);process.exitCode=1});
