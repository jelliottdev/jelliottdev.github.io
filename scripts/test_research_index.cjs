/* Browser-free directory behavior and checker contract checks. No inference requests. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const Index=require('../research-index.js');
const Search=require('../assistant-search.js');
const WikiSearch=require('../search-engine.js');
const root=path.resolve(__dirname,'..');
const state=query=>Index.state(new URLSearchParams(query));
const fixture=(id,title,extra={})=>({id,title,status:'published',question:'Reverse a prime sequence?',summary:'A fixed prime reversal test',
  tags:['reverse','prime'],method_topics:[{id:'transposition',aliases:['reverse']}],scope:{pages:['lp2-15'],procedure:'reverse prime sequence',representation:'runes',parameters:'one row',exclusions:'other rows'},
  finding:'The fixed rule did not recover the known reading.',limitations:'One fixed rule.',outcome:'inconclusive',
  record_type:{id:'method',label:'Bounded solving test'},review:{retested_on:'2026-10-22'},reproduction:{inputs:[],outputs:[]},related:[],...extra});
const family={id:'prime-reversal',title:'Prime reversal'};
const records=[
  fixture('b','Case 10',{family,review:{retested_on:'2026-10-23'}}),
  fixture('a','Case 2',{family,review:{retested_on:'2026-10-23'}}),
  fixture('c','Case 1',{review:{},record_type:{id:'audit',label:'Source audit'},outcome:'not-supported',scope:{pages:['lp2-31']},finding:'This mentions LP2-15 outside the tested scope.'}),
  fixture('d','Case 3',{review:{retested_on:'2026-10-21'},record_type:{id:'measurement',label:'Measurement'},outcome:'supported',scope:{pages:['lp2-15','lp2-16','lp2-17']}})
];
assert.deepEqual(Index.select(records,state('')).records.map(r=>r.id),['c','a','d','b']);
assert.deepEqual(Index.select(records,state('sort=title-desc')).records.map(r=>r.id),['b','d','a','c']);
assert.deepEqual(Index.select(records,state('sort=recent')).records.map(r=>r.id),['a','b','d','c'],'Known dates first, then stable numeric-aware title order');
assert.deepEqual(Index.select(records,state('q=prime+LP2+page+15&type=method&method=transposition&family=prime-reversal&outcome=inconclusive')).records.map(r=>r.id),['a','b']);
assert.equal(Index.select(records,state('method=unknown')).state.method,'');
const authored=fixture('authored','Source title',{method_topics:[{id:'transposition',title:'Routes and rearrangements',aliases:[]}]});
const authoredResult=Index.select([authored,...records],state('q=Routes+and+rearrangements'));
assert.equal(authoredResult.topics.get('transposition'),'Routes and rearrangements','Authored titles override inferred labels even beside older metadata');
assert.deepEqual(authoredResult.records.map(r=>r.id),['authored'],'Authored method names are searchable');
assert(Index.filters(authoredResult).includes('Routes and rearrangements'));
assert.equal(Index.select(records,state('')).topics.get('transposition'),'Transposition','Older cached metadata retains a useful fallback');
assert.deepEqual(Index.select(records,state('q=LP2-15–17')).records.map(r=>r.id),['d'],'Every requested page must be inside scope');
const gapped=fixture('gapped','Endpoint-only scope',{scope:{pages:['lp2-15','lp2-17']}});
for(const query of ['LP2-15–LP2-17','LP2 pages 15–LP2 page 17','LP2-17—LP2-15']){
 assert.deepEqual(Index.select([...records,gapped],state('q='+encodeURIComponent(query))).records.map(r=>r.id),['d'],
  'A fully written range requires interior pages, not only its endpoints: '+query);
}
assert.deepEqual(Index.pageQuery('LP2 pages 15–LP2 page 17').pages,['lp2-15','lp2-16','lp2-17']);
assert.deepEqual(Index.pageQuery('LP1-16–LP2-02').pages,['lp1-16','lp2-02'],'A different release is not folded into the first release’s numeric range');
assert.equal(Index.select(records,state('q=LP2-99')).total,0);
assert(!Index.select(records,state('q=LP2-15')).records.some(r=>r.id==='c'),'A page mentioned in findings cannot masquerade as tested scope');
assert(!Index.select(records,state('q=LP2‑15')).records.some(r=>r.id==='c'),'Pasted Unicode hyphens retain exact page scope');
assert.equal(Index.select(records,state('family=missing')).state.family,'');
assert.equal(state('type=__proto__&outcome=constructor&sort=unknown&page=-4').type,'');
assert.equal(state('type=__proto__&outcome=constructor&sort=unknown&page=-4').outcome,'');
assert.equal(state('page=-4').page,1);
const sourceOrder=records.map(r=>r.id);Index.select(records,state('sort=recent'));assert.deepEqual(records.map(r=>r.id),sourceOrder);
const chosen=state('q=prime+%26+shift&type=method&method=transposition&family=prime-reversal&outcome=inconclusive&sort=recent&page=2');
assert.deepEqual(state(Index.href(chosen).split('?')[1]),chosen,'All filters, sort and page survive shareable URLs');
assert.equal(Index.legacyHref('#/experiments?browse=prime%20shift&section=browse-experiments'),'#/research?q=prime+shift');
assert.equal(Index.legacyHref('#/experiments?section=browse-experiments'),'#/research');
assert.equal(Index.legacyHref('#/experiments?q=reverse'),null,'Idea queries remain checker routes');
assert.equal(Index.legacyHref('#/experiments/a?browse=prime'),null,'Direct records never redirect');
const many=Array.from({length:45},(_,n)=>fixture('record-'+n,'Record '+n));
const second=Index.select(many,state('page=2'));
assert.equal(second.records.length,20);assert.equal(second.start,20);assert.equal(second.pages,3);
assert.equal(Index.select(many,state('page=999')).state.page,3);
assert(Index.results(second).includes('aria-current="page"'));
assert(!Index.results(second).includes('<details'),'Findings do not sit inside nested disclosures');
const emptyHTML=Index.results(Index.select(records,state('q=absent-word')));
assert(emptyHTML.includes('No matching research'));
assert(!emptyHTML.includes('data-research-reset'),'Empty copy must not duplicate the persistent Clear filters action');
const unsafe=Index.results(Index.select([fixture('safe','<img src=x>',{finding:'<script>unsafe</script>'})],state('')));
assert(!unsafe.includes('<script>'));assert(!unsafe.includes('<img'));
const grouped=Index.results(Index.select(records,state('q=Case+2')));
assert(grouped.includes('href="#/research?family=prime-reversal"'),'Related-group traversal clears the narrowing title query');
assert(grouped.includes('Inconclusive'),'Finding classification is explicit in every row');
assert(Index.familyContext(Index.select(records,state('family=prime-reversal'))).includes('Related test group:'));
const detailOnly=fixture('details','A bounded test',{scope:{pages:['lp2-15'],procedure:'Rotate each column',representation:'Prime digits',parameters:'Three fixed seeds',exclusions:'Unrestricted autokey and <script> are not tested.'},limitations:'No independent holdout was used.'});
for(const [query,label,section] of [['column','Matches method','experiment-procedure'],['unrestricted autokey','Mentioned under “Not tested”','experiment-exclusions'],['holdout','Matches limitations','experiment-limitations']]){
 const selected=Index.select([detailOnly],state('q='+encodeURIComponent(query)));
 assert.equal(selected.total,1);
 const html=Index.results(selected);assert(html.includes(label));assert(html.includes('?section='+section));assert(!html.includes('<script>'));
}
assert.equal(Index.select([detailOnly],state('q=LP2-31+autokey')).total,0,'Exclusion discovery does not expand page scope');
assert(!Index.results(Index.select([detailOnly],state('q=bounded'))).includes('research-match'),'No redundant matching panel for ordinary title matches');
assert(Index.results(Index.select([fixture('unknown','No page metadata',{scope:{pages:[]}})],state(''))).includes('Page scope not recorded'));
const published=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8')).records;
const all=[];
for(let page=1;page<=Math.ceil(published.length/Index.pageSize);page++){
  const result=Index.select(published,state('page='+page)),html=Index.results(result);
  const links=[...html.matchAll(/href="#\/experiments\/([a-z0-9-]+)"/g)].map(m=>m[1]);
  assert.equal(links.length,result.records.length);all.push(...links);
}
assert.equal(new Set(all).size,published.length);assert.equal(all.length,published.length);
const container={querySelector:()=>({dataset:{researchState:'#/research?q=prime&page=2'}})};
Index.remember(container,340);assert.equal(Index.position(container),340);
container.querySelector=()=>({dataset:{researchState:'#/research?q=prime'}});assert.equal(Index.position(container),null);
console.log('PASS: directory query/type/group/outcome intersections, exact page scope, dates/missing dates, stable sorting, URL round trips, pagination, group traversal, escaping and remembered return positions.');

// Execute the actual checker with small DOM stubs. This validates behavior, not layout.
const elements=new Map(),document={activeElement:null};let html='',lastURL='',workerBody=null;
function element(id){if(!elements.has(id))elements.set(id,{value:'',innerHTML:'',textContent:'',isConnected:true,hidden:false,disabled:false,
  addEventListener(type,fn){this[type]=fn},setAttribute(){},replaceChildren(){this.innerHTML=''},focus(){this.focused=true;document.activeElement=this}});return elements.get(id);}
const context={URLSearchParams,URL,AbortController,setTimeout,clearTimeout,console,document,ResearchIndex:Index,WikiSearch,
  AssistantSearch:Search,AssistantMarkdown:require('../assistant-markdown.js'),IdeaCoverage:require('../idea-coverage.js'),
  location:{hash:'#/experiments'},history:{replaceState(a,b,url){lastURL=url}},db:{pages:[{id:'lp2-15'},{id:'lp2-31'}]},
  head:()=>'',footer:()=>'',esc:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
  main:{set innerHTML(value){html=value},get innerHTML(){return html}},$:selector=>element(selector),
  fetch:async(url,options)=>{
    if(url==='https://assistant.example/ask'){workerBody=JSON.parse(options.body);return {ok:false,status:503,json:async()=>({})};}
    return {ok:true,json:async()=>({documents:[]})};
  }};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'assistant-ui.js'),'utf8'),context);
context.records=[fixture('prime-reversal','Reverse prime sequence')];
vm.runInContext('experimentRecords=records; assistantConfig={}; methodFamilyPending=false; ideaCoveragePending=false; reportedAttemptsPending=false;',context);
context.renderIdeaChecker('');
assert(html.includes('href="#/research"'));assert(!html.includes('Specify pages'));
assert(!html.includes('What does a match mean?'));
assert(!html.includes('idea-page-one'));assert(!html.includes('browse-experiments'));
assert.equal(element('#experiment-results').innerHTML,'','Checker starts with its form, not the research archive');
element('#experiment-query').value='unmatched research fixture';context.renderIdeaChecker('unmatched research fixture');
assert(element('#experiment-results').innerHTML.includes('doesn’t cover every past attempt'));
assert(element('#experiment-results').innerHTML.includes('href="#/research"'));
element('#experiment-query').value='reverse prime sequence LP2-15';
vm.runInContext("assistantConfig={endpoint:'https://assistant.example/ask'}",context);
element('#experiment-form').onsubmit({preventDefault(){}});
assert.deepEqual(workerBody.pages,['lp2-15'],'Pages still come from natural-language text in the Worker contract');
assert.equal(workerBody.query,'reverse prime sequence LP2-15');
assert(lastURL.startsWith('#/experiments?q='));assert(!lastURL.includes('pages='));
assert(!elements.has('#idea-page-one'));
context.location.hash='#/experiments?q=reverse&pages=lp2-31';
context.renderIdeaChecker('reverse');assert(html.includes('reverse on LP2-31'),'Old page-picker links retain their explicit page context');
const app=fs.readFileSync(path.join(root,'app.js'),'utf8'),shell=fs.readFileSync(path.join(root,'index.html'),'utf8');
assert(app.includes("type==='research'"));assert(app.includes('ResearchIndex.legacyHref'));
assert(app.includes('ResearchIndex.position(main)'));assert(app.includes('ResearchIndex.remember(main,window.scrollY)'));
assert(shell.includes('site-navigation.js'),'The shared drawer owns research navigation');
assert.equal(require('../site-navigation.js').primary.filter(([,href])=>href==='research.html?v=workspace-20261024b').length,1);
console.log('PASS: focused checker has no archive/page picker; natural-language pages and old page links remain usable; directory route/navigation/scroll hooks are installed. No live model requests.');

const lifecycleGuard=setTimeout(()=>{console.error('Research lifecycle test did not finish');process.exitCode=1},5000);
(async()=>{
  context.renderId=1;context.window={scrollY:215};
  const article={dataset:{},addEventListener(type,fn){this[type]=fn}};
  context.main.querySelector=selector=>selector==='.research-index'?article:null;
  context.records=records;vm.runInContext('experimentRecords=records;',context);
  for(const [key,value] of Object.entries({query:'prime',type:'method',method:'transposition',outcome:'inconclusive',sort:'recent'}))element('#research-'+key).value=value;
  await context.researchIndexPage(1,new URLSearchParams('q=prime&type=method&method=transposition&family=prime-reversal&outcome=inconclusive&sort=recent'));
  assert(html.includes('id="research-filters"'));
  assert(lastURL.includes('family=prime-reversal'));
  element('#research-query').value='no-such-test';element('#research-query').input();
  assert.equal(element('#research-count').textContent,'0 matching records');
  assert.equal(element('#research-reset').hidden,false,'Active filters remain clearable when no records match');
  assert.equal((html.match(/data-research-reset/g)||[]).length,1,'The index owns one persistent reset action');
  assert(!element('#research-results').innerHTML.includes('data-research-reset'),'Zero-result updates do not add a second reset button');
  assert(lastURL.includes('family=prime-reversal'),'Editing visible filters keeps the active related-test group');
  article.click({target:{closest:()=>({})}});
  assert.equal(element('#research-query').value,'');assert.equal(element('#research-sort').value,'title');
  assert.equal(article.dataset.researchState,'#/research','Clear filters resets hidden family context too');
  assert.equal(element('#research-family-context').hidden,true);
  assert.equal(element('#research-query').focused,true);
  const before=html;await context.researchIndexPage(99);assert.equal(html,before,'Stale route calls cannot replace the current view');
  context.records=published;vm.runInContext('experimentRecords=records;',context);
  for(const name of ['bindRouteIllustration','bindLanguageBlockFigure','bindAffineLagFigure','bindBlockBoundaryFigure','startExperimentSupport'])context[name]=()=>{};
  await context.experimentsPage(published[0].id,1);
  assert(html.includes('id="experiment-finding"'));assert(html.includes('downloads/experiments/'+published[0].id+'.zip'));
  await assert.rejects(context.experimentsPage('missing-record-fixture',1),/no published record/);
  const discovery=published.map(record=>({id:record.id,title:record.title,summary:record.summary,tags:record.tags,
    family:record.family,outcome:record.outcome,finding:record.reader_finding||record.finding,
    record_type:record.record_type,method_topics:record.method_topics,pages:record.scope.pages,artifacts:record.scope.artifacts,
    retested_on:record.review.retested_on,scope:record.scope,limitations:record.limitations}));
  const clearCaches=()=>vm.runInContext('experimentRecords=undefined;experimentRecordsPromise=null;researchRecords=undefined;researchRecordsPromise=null;',context);
  clearCaches();const requests=[];
  context.fetch=async url=>{requests.push(url);return {ok:true,json:async()=>({records:discovery})}};
  const [first,second]=await Promise.all([context.ensureResearchRecords(),context.ensureResearchRecords()]);
  assert.equal(requests.length,1);assert.equal(requests[0],'data/experiment-index.json');
  assert.equal(first,second);assert.deepEqual(Array.from(first[0].scope.pages),published[0].scope.pages);
  assert.equal(first[0].review.retested_on,published[0].review.retested_on);
  assert(vm.runInContext('experimentRecords===undefined',context),'Reduced discovery rows must never populate the full-scope checker registry');
  for(const query of ['', 'q=LP2-15&type=method&method=feedback', 'sort=recent', 'family=prime-reversal']){
    const cold=Index.select(first,state(query)),warm=Index.select(published,state(query));
    assert.deepEqual(cold.records.map(r=>r.id),warm.records.map(r=>r.id),'Cold lightweight and warm full records filter/sort identically');
  }
  await context.ensureResearchRecords();assert.equal(requests.length,1,'The directory cache avoids repeat loads');
  clearCaches();let attempts=0;
  context.fetch=async url=>{assert.equal(url,'data/experiment-index.json');attempts++;return {ok:attempts>1,json:async()=>({records:discovery})}};
  await assert.rejects(context.ensureResearchRecords(),/could not be loaded/);
  await context.ensureResearchRecords();assert.equal(attempts,2,'Failed directory loads can retry without a full-registry request');
  clearCaches();const fallback=[];
  context.fetch=async url=>{fallback.push(url);return {ok:true,json:async()=>({records:url==='data/experiment-index.json'?[{id:'old-discovery'}]:published})}};
  await context.ensureResearchRecords();
  assert.deepEqual(fallback,['data/experiment-index.json','data/experiments.json'],'Old discovery payloads missing required fields fall back to complete records once');
  await context.ensureResearchRecords();assert.equal(fallback.length,2);
  let finish;
  context.fetch=()=>new Promise(resolve=>{finish=resolve});
  clearCaches();
  const pending=context.researchIndexPage(1);context.renderId=2;html='Newer route';
  finish({ok:true,json:async()=>({records:discovery})});await pending;
  assert.equal(html,'Newer route','An index load finishing after navigation cannot overwrite the newer route');
  console.log('PASS: actual directory handlers/reset, active family retention, direct/missing records, lightweight shared loads/cache/retry/fallback and stale navigation. DOM stubs do not assert visual layout.');
})().catch(error=>{console.error(error);process.exitCode=1}).finally(()=>clearTimeout(lifecycleGuard));
