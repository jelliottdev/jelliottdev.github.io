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
assert.deepEqual(Browser.read('#/research?q=autokey&page=4&type=method','graph',Index.state),{view:'all',branch:'',record:'',page:'',colour:'methods',result:'',mode:'list',q:'autokey',type:'method',method:'',family:'',sort:'title',followups:'',p:4});
assert.equal(Browser.read('#mode=graph','list',Index.state).mode,'graph');
assert.equal(Browser.read('','list',Index.state).mode,'list');
assert.equal(Browser.read('#page=lp2-15&mode=list','graph',Index.state).page,'lp2-15');
assert.equal(Browser.read('#followups=1&mode=list&branch=solve-lp2','graph',Index.state).followups,'1');assert.equal(Browser.read('#followups=pending&mode=list','graph',Index.state).followups,'pending');
for(const value of ['','0','true','2','<img>'])assert.equal(Browser.read('#followups='+encodeURIComponent(value),'graph',Index.state).followups,'','Only explicit followups=1 activates the filter');
const html=fs.readFileSync(path.join(root,'research.html'),'utf8');
assert.equal((html.match(/src="research-index\.js/g)||[]).length,1);
assert(!/map-index-model|map-search-engine|map-study-data|\/archive\//.test(html));
console.log(`PASS unified research: ${published.length} current records, exact findings/scopes, every leaf once, preserved source parents, new-record access, shared selector/search and legacy state.`);

assert.equal(Browser.read('#result=%22%3E%3Cimg%20onerror%3Dalert(1)%3E','graph',Index.state).result,'');
assert.equal(Browser.read('#result=bogus&outcome=supported','graph',Index.state).result,'supported');
assert.equal(Browser.read('#record=__proto__','graph',Index.state).record,'');

// Exercise the production preview renderer, not a parallel view implementation.
{
 const vm=require('node:vm'),script=fs.readFileSync(path.join(root,'research-browser.js'),'utf8'),start=script.indexOf(' function readerLimit('),end=script.indexOf(' const sorts=',start);assert(start>=0&&end>start);
 let back=null,previewUpdates=0;const backControl={},panel={innerHTML:'',hidden:true,querySelector:selector=>selector==='.preview-back'?backControl:null},fixture={title:'Actual <record>',outcome:'inconclusive',pages:['lp2-00','lp2-02'],reader_finding:'A bounded result <safe>.',finding:'Technical finding',scope:{parameters:'Only keys [1,2], with page resets.',exclusions:'Line resets and unknown keys.'},next_steps:'Measure recovery on held-out controls.',reader_limit:'Two known texts do not establish performance on every language.',href:'library.html#/experiment/fixture'};
 const context={questionMount:null,ResearchWork:require('../research-work.js'),RecordFollowupView:require('../record-followup-view.js'),panel,state:{record:'fixture'},data:{records:{fixture}},esc:value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])),arrow:'',updatePreviewMode(){previewUpdates++;},navigate(value,replace){back={value,replace};}};
 vm.createContext(context);for(const name of ['workFor','recordHref'])vm.runInContext(script.match(new RegExp('^ function '+name+'\\(.*$','m'))[0],context);vm.runInContext(script.slice(start,end),context);context.showInspector();let html=panel.innerHTML;
 assert(!panel.hidden);assert.equal(previewUpdates,1);assert(html.indexOf('A bounded result')<html.indexOf('Tested bounds'));assert(html.includes('LP2-00, LP2-02'));assert(!html.includes('LP2-00–02'),'Page holes remain explicit');for(const expected of ['Only keys [1,2], with page resets.','Not tested:</strong> Line resets and unknown keys.','Next check:</strong> Measure recovery on held-out controls.','Limit:</strong> Two known texts'])assert(html.includes(expected),expected);assert(html.includes('A bounded result &lt;safe&gt;.'));assert(!html.includes('What this leaves open'));assert(!html.includes('<details'));assert(html.includes('Read full record'));backControl.onclick();assert.equal(back.value.record,'');assert.equal(back.replace,true);
 const scientific='Not independently checked; language uncertainty remains.';fixture.reader_limit=scientific+'; Human review is pending.';fixture.next_steps='Check another fixed passage. Human review pending.';context.showInspector();assert(panel.innerHTML.includes(scientific));assert(panel.innerHTML.includes('Check another fixed passage.'));assert(!/human review(?: is)? pending/i.test(panel.innerHTML));assert.equal(fixture.reader_limit,scientific+'; Human review is pending.','Display cleaning does not rewrite canonical evidence');
 fixture.reader_limit=fixture.scope.exclusions;context.showInspector();assert(!panel.innerHTML.includes('<strong>Limit:</strong>'),'An already visible exclusion is not repeated as a limit');fixture.scope.exclusions='';fixture.next_steps='';fixture.reader_limit='';fixture.limitations='';context.showInspector();assert(!panel.innerHTML.includes('Further checks'));assert(!panel.innerHTML.includes('<strong>Limit:</strong>'),'Absent authored fields do not produce invented open claims');
 assert(!panel.innerHTML.includes('Review follow-up'),'Records without declared recipes have no runnable action');
 const recipe=JSON.parse(fs.readFileSync(path.join(root,'experiments/records/lp2-known-vigenere-keys/record.json'),'utf8')).browser_followups[0];const setting=(id,title,scope_change)=>({...structuredClone(recipe),id,title,scope_change});fixture.id='fixture-record';fixture.browser_followups=[setting('prefix-control','Compare <prefix>','Only the fixed LP2-15 prefix.')];context.showInspector();assert(panel.innerHTML.includes('Try a follow-up'));assert(panel.innerHTML.includes('Compare &lt;prefix&gt;'));assert(panel.innerHTML.includes('Only the fixed LP2-15 prefix.'));assert(panel.innerHTML.includes('href="run.html#record=fixture-record&amp;followup=prefix-control"'));assert(panel.innerHTML.indexOf('A bounded result')<panel.innerHTML.indexOf('Try a follow-up'));
 fixture.browser_followups=[setting('first-control','First fixed setting','First page scope.'),setting('second-control','Second <setting>','Second scope <literal>.')];
 const select={value:'first-control'},scope={textContent:''},link={href:'run.html#record=fixture-record&followup=first-control'},oldQuery=panel.querySelector;panel.querySelector=selector=>({'[data-prepared-setting]':select,'[data-prepared-scope]':scope,'[data-prepared-link]':link}[selector]||oldQuery(selector));context.showInspector();assert(panel.innerHTML.includes('<label for="prepared-followup-setting">Setting</label>'));assert(panel.innerHTML.includes('Second &lt;setting&gt;'));assert.equal((panel.innerHTML.match(/Review follow-up/g)||[]).length,1,'Many recipes have one review link, not repeated paragraphs/actions');assert(panel.innerHTML.includes('First page scope.'));assert(!panel.innerHTML.includes('Second scope &lt;literal&gt;'),'Only the selected scope is expanded');select.value='second-control';select.onchange();assert.equal(scope.textContent,'Second scope <literal>.');assert.equal(link.href,'run.html#record=fixture-record&followup=second-control');const retained=link.href;select.value='../injected';select.onchange();assert.equal(select.value,'second-control');assert.equal(link.href,retained);assert.equal(scope.textContent,'Second scope <literal>.');assert.equal(back.value.record,'','Changing the prepared setting does not navigate');panel.querySelector=oldQuery;
 fixture.browser_followups=[setting('../unsafe','Unsafe','Wrong'),setting('good','<img onerror=bad>','<script>literal</script>')];context.showInspector();assert(!panel.innerHTML.includes('../unsafe'));assert(panel.innerHTML.includes('&lt;img onerror=bad&gt;'));assert(panel.innerHTML.includes('&lt;script&gt;literal&lt;/script&gt;'));assert(!panel.innerHTML.includes('<img onerror'));
 fixture.id='../bad';context.showInspector();assert(!panel.innerHTML.includes('Review follow-up'));delete fixture.browser_followups;fixture.id='fixture-record';
 const communityId='idea-'+'a'.repeat(64),pendingId='b'.repeat(64),community={...fixture,id:communityId,community:true,proposal_id:'p_'+'a'.repeat(64),href:'run.html#idea=p_'+'a'.repeat(64),task_count:2,verified_task_count:1,task_summaries:[{id:pendingId,title:'Synthetic unfinished check',state:'not-run'}],browser_followups:[]};context.data.records[communityId]=community;context.state.record=communityId;context.showInspector();assert(panel.innerHTML.includes('href="run.html#task='+pendingId+'"'));assert(panel.innerHTML.includes('Open unfinished experiment'));community.task_count=community.verified_task_count=0;community.task_summaries=[];context.showInspector();assert(panel.innerHTML.includes('Open saved idea'));assert(!panel.innerHTML.includes('run.html#task='),'A zero-task idea does not get a fabricated experiment action');delete context.data.records[communityId];context.state.record='fixture';
 // The generated model keeps all authored follow-up and scope fields available.
 for(const record of published){assert.equal(data.records[record.id].next_steps,record.next_steps);assert.deepEqual(data.records[record.id].browser_followups,record.browser_followups);assert.deepEqual(data.records[record.id].scope,record.scope);}
 // The production inspector owns one live-question subscription. Changing its
 // selected record or closing it tears down the previous full-record mount.
 const lifecycle=[],mounted=[],first=JSON.parse(fs.readFileSync(path.join(root,'experiments/records/word-internal-affine-lags/record.json'),'utf8')),second=JSON.parse(fs.readFileSync(path.join(root,'experiments/records/wulfic-autokey-seed-families/record.json'),'utf8'));
 for(const record of [first,second])Object.assign(record,{pages:record.scope.pages,href:'library.html#/experiment/'+record.id});
 context.RecordQuestionView={render:()=>'',coversFollowups:()=>false,mount(host,record){assert.equal(host,panel);assert(Array.isArray(record.research_questions));assert(panel.innerHTML.includes(record.title));const handle={record,destroyed:false,destroy(){assert(!this.destroyed);this.destroyed=true;lifecycle.push('destroy:'+record.id);}};mounted.push(handle);lifecycle.push('mount:'+record.id);return handle;}};
 context.data.records[first.id]=first;context.data.records[second.id]=second;context.state.record=first.id;context.showInspector();assert.equal(mounted[0].record,first);assert.equal(context.questionMount,mounted[0]);
 context.state.record=second.id;context.showInspector();assert(mounted[0].destroyed);assert.equal(mounted[1].record,second);assert.equal(context.questionMount,mounted[1]);assert(!panel.innerHTML.includes(first.title));
 context.state.record='';context.showInspector();assert(mounted[1].destroyed);assert.equal(context.questionMount,null);assert.equal(panel.hidden,true);assert.equal(mounted.length,2,'Closing cannot create another question controller');
 context.state.record='missing-record';context.showInspector();assert.equal(mounted.length,2);assert.deepEqual(lifecycle,['mount:'+first.id,'destroy:'+first.id,'mount:'+second.id,'destroy:'+second.id]);
 console.log('PASS authored map preview: result first, exact scope, scientific limits, safe navigation, and live-question mounts destroy on selection/close without subscribing missing records.');
}
