'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),load=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const Browser=require('../research-browser-model.js'),Index=require('../research-index.js');
const source=load('data/research-map.json'),registry=load('data/experiments.json'),before=JSON.stringify(source);
const data=Browser.build(source,registry),published=registry.records.filter(r=>r.status==='published');
assert.equal(JSON.stringify(source),before,'Navigation building cannot rewrite source classification');
const nodes=new Map(data.views.all.nodes.map(n=>[n.id,n]));
const leaves=data.views.all.nodes.filter(n=>n.record_id);
assert.equal(leaves.length,published.length);assert.equal(new Set(leaves.map(n=>n.record_id)).size,published.length);
assert.deepEqual(new Set(nodes.get('all-research').members),new Set(published.map(r=>r.id)));
for(const record of published){
  assert.deepEqual(data.records[record.id].scope,record.scope);
  assert.equal(data.records[record.id].finding,record.finding);
  assert.equal(data.records[record.id].limitations,record.limitations);
  assert.deepEqual(data.records[record.id].method_topics,record.method_topics);
  const target=new URL(data.records[record.id].href,'https://example.org/');
  assert.equal(target.pathname,'/library.html');assert.deepEqual([...target.searchParams.keys()],['v']);assert(target.searchParams.get('v'));
  assert.equal(target.hash,'#/experiment/'+encodeURIComponent(record.id));
}
for(const view of Object.values(source.views))for(const node of view.nodes){
  if(!nodes.has(node.id)||!nodes.has(node.parent))continue;
  assert.equal(nodes.get(node.id).parent,node.parent,'Keep every original relation below the editorial area roots');
}
const selected=Index.select(Object.values(data.records),Index.state(new URLSearchParams()));
assert.equal(selected.allRecords.length,published.length);assert.equal(selected.records.length,20);
const exact=Index.select(Object.values(data.records),Index.state(new URLSearchParams('q=LP2-15&sort=recent')));
assert(exact.allRecords.length>0);assert(exact.allRecords.every(r=>r.scope.pages.includes('lp2-15')));
const added=structuredClone(registry),fresh=structuredClone(published[0]);fresh.id='future-record';fresh.title='A new record';added.records.push(fresh);
const future=Browser.build(source,added),unplaced=future.views.all.nodes.find(n=>n.id==='aim:unplaced');
assert(unplaced.members.includes(fresh.id),'New records stay accessible without inventing method classification');
assert.deepEqual(Browser.read('#/research?q=autokey&page=4&type=method','graph',Index.state),{view:'all',branch:'',record:'',page:'',colour:'methods',result:'',mode:'list',q:'autokey',type:'method',method:'',family:'',sort:'title',p:4});
assert.equal(Browser.read('#mode=graph','list',Index.state).mode,'graph');
assert.equal(Browser.read('','list',Index.state).mode,'list');
assert.equal(Browser.read('#page=lp2-15&mode=list','graph',Index.state).page,'lp2-15');
const html=fs.readFileSync(path.join(root,'research.html'),'utf8');
assert.equal((html.match(/src="research-index\.js/g)||[]).length,1);
assert(!/map-index-model|map-search-engine|map-study-data|\/archive\//.test(html));
console.log(`PASS unified research: ${published.length} current records, exact findings/scopes, every leaf once, preserved source parents, new-record access, shared selector/search and legacy state.`);

assert.equal(Browser.read('#result=%22%3E%3Cimg%20onerror%3Dalert(1)%3E','graph',Index.state).result,'');
assert.equal(Browser.read('#result=bogus&outcome=supported','graph',Index.state).result,'supported');
assert.equal(Browser.read('#record=__proto__','graph',Index.state).record,'');

// Exercise the production preview renderer, not a parallel view implementation.
{
 const vm=require('node:vm'),script=fs.readFileSync(path.join(root,'research-browser.js'),'utf8'),start=script.indexOf(' function previewScopeHTML('),end=script.indexOf(' const sorts=',start);assert(start>=0&&end>start);
 let back=null,previewUpdates=0;const backControl={},panel={innerHTML:'',hidden:true,querySelector:selector=>selector==='.preview-back'?backControl:null},fixture={title:'Actual <record>',outcome:'inconclusive',pages:['lp2-00','lp2-02'],reader_finding:'A bounded result <safe>.',finding:'Technical finding',scope:{parameters:'Only keys [1,2], with page resets.',exclusions:'Line resets and unknown keys.'},next_steps:'Measure recovery on held-out controls.',reader_limit:'Two known texts do not establish performance on every language.',href:'library.html#/experiment/fixture'};
 const context={panel,state:{record:'fixture'},data:{records:{fixture}},esc:value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])),arrow:'',updatePreviewMode(){previewUpdates++;},navigate(value,replace){back={value,replace};}};
 vm.createContext(context);vm.runInContext(script.slice(start,end),context);context.showInspector();let html=panel.innerHTML;
 assert(!panel.hidden);assert.equal(previewUpdates,1);assert(html.indexOf('A bounded result')<html.indexOf('Tested bounds'));assert(html.includes('LP2-00, LP2-02'));assert(!html.includes('LP2-00–02'),'Page holes remain explicit');for(const expected of ['Only keys [1,2], with page resets.','Not tested:</strong> Line resets and unknown keys.','Next check:</strong> Measure recovery on held-out controls.','Limit:</strong> Two known texts'])assert(html.includes(expected),expected);assert(html.includes('A bounded result &lt;safe&gt;.'));assert(!html.includes('What this leaves open'));assert(!html.includes('<details'));assert(html.includes('Read full record'));backControl.onclick();assert.equal(back.value.record,'');assert.equal(back.replace,true);
 fixture.reader_limit=fixture.scope.exclusions;context.showInspector();assert(!panel.innerHTML.includes('<strong>Limit:</strong>'),'An already visible exclusion is not repeated as a limit');fixture.scope.exclusions='';fixture.next_steps='';fixture.reader_limit='';fixture.limitations='';context.showInspector();assert(!panel.innerHTML.includes('Further checks'));assert(!panel.innerHTML.includes('<strong>Limit:</strong>'),'Absent authored fields do not produce invented open claims');
 assert(!panel.innerHTML.includes('Run a follow-up'),'Records without declared recipes have no runnable action');
 fixture.id='fixture-record';fixture.browser_followups=[{id:'prefix-control',title:'Compare <prefix>',scope_change:'Only the fixed LP2-15 prefix.'}];context.showInspector();assert(panel.innerHTML.includes('Prepared follow-up'));assert(panel.innerHTML.includes('Compare &lt;prefix&gt;'));assert(panel.innerHTML.includes('Only the fixed LP2-15 prefix.'));assert(panel.innerHTML.includes('href="run.html#record=fixture-record&amp;followup=prefix-control"'));assert(panel.innerHTML.indexOf('A bounded result')<panel.innerHTML.indexOf('Prepared follow-up'));
 fixture.browser_followups=[{id:'../unsafe',title:'Unsafe',scope_change:'Wrong'},{id:'good',title:'<img onerror=bad>',scope_change:'<script>literal</script>'}];context.showInspector();assert(!panel.innerHTML.includes('../unsafe'));assert(panel.innerHTML.includes('&lt;img onerror=bad&gt;'));assert(panel.innerHTML.includes('&lt;script&gt;literal&lt;/script&gt;'));assert(!panel.innerHTML.includes('<img onerror'));
 fixture.id='../bad';context.showInspector();assert(!panel.innerHTML.includes('Run a follow-up'));delete fixture.browser_followups;fixture.id='fixture-record';
 // The generated model keeps all authored follow-up and scope fields available.
 for(const record of published){assert.equal(data.records[record.id].next_steps,record.next_steps);assert.deepEqual(data.records[record.id].browser_followups,record.browser_followups);assert.deepEqual(data.records[record.id].scope,record.scope);}
 console.log('PASS authored map preview: result first, exact page holes/parameters, separate exclusions and next check, nonduplicate scientific limits, escaping and unchanged navigation.');
}
