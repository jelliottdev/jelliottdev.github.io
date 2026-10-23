/* Production checker lifecycle with deferred records; no browser/model requests. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),Search=require('../assistant-search.js');
const record={id:'prime-example',status:'published',title:'Prime stream test',question:'Does a prime stream recover text?',
 summary:'Prime stream opening test',tags:['prime stream'],scope:{pages:['lp2-15'],representation:'runes',procedure:'fixed subtraction',parameters:'one key',exclusions:'other keys'},
 finding:'Technical finding for exact evidence',reader_finding:'Plain result for readers',limitations:'Technical limits for exact evidence',reader_limit:'Other keys remain open.',
 article:'Exact article lexical text',outcome:'not-supported',record_type:{id:'method',label:'Solving test',description:'A finite test'},related:[],method_topics:[]};
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function harness(query=''){
 let elements=new Map(),html='',registryCalls=0,apiCalls=0;const pending=[];
 const context={URLSearchParams,AbortController,setTimeout,clearTimeout,renderId:1,
  location:{hash:'#/experiments'},history:{replaceState(){}},db:{pages:[{id:'lp2-15'}]},
  head:()=>'',footer:()=>'',esc:String,AssistantSearch:Search,AssistantMarkdown:require('../assistant-markdown.js'),IdeaCoverage:require('../idea-coverage.js'),
  document:{activeElement:null},$:id=>elements.get(id),
  fetch:(url,options)=>{
   if(options?.method==='POST'){apiCalls++;return Promise.resolve({ok:false,status:503,json:async()=>({})})}
   assert.equal(url,'data/checker-records.json','Cold readiness uses the dedicated evidence payload');
   registryCalls++;return new Promise((resolve,reject)=>pending.push({resolve,reject}));
  }};
 context.main={set innerHTML(value){
  for(const el of elements.values())el.isConnected=false;elements=new Map();html=value;
  for(const [,id] of value.matchAll(/id="([^"]+)"/g)){
   const el={isConnected:true,value:'',innerHTML:'',textContent:'',hidden:false,disabled:false,listeners:{},attributes:{},
    addEventListener(type,fn){this.listeners[type]=fn},setAttribute(name,value){this.attributes[name]=value},replaceChildren(){this.innerHTML=''},
    focus(){context.document.activeElement=this}};elements.set('#'+id,el);
  }
  const input=elements.get('#experiment-query');if(input)input.value=value.match(/<textarea[^>]*>([^<]*)<\/textarea>/)?.[1]||'';
 },get innerHTML(){return html}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
 vm.runInContext(fs.readFileSync(path.join(root,'assistant-ui.js'),'utf8'),context);
 vm.runInContext("startExperimentSupport=()=>{};assistantConfig={endpoint:'https://mock.example/ask'};methodFamilyPending=false;ideaCoveragePending=false;reportedAttemptsPending=false;",context);
 const $=id=>elements.get('#'+id),okay=records=>({ok:true,json:async()=>({schema:'liberpedia-checker-records-v1',registry_sha256:'a'.repeat(64),records})});
 return {context,$,pending,okay,get registryCalls(){return registryCalls},get apiCalls(){return apiCalls},query};
}
(async()=>{
 const h=harness();await h.context.experimentsPage('',1);
 assert(h.$('experiment-query'),'Editable shell exists while registry is unresolved');
 const input=h.$('experiment-query');input.value='prime stream LP2-15';input.focus();input.listeners.input();
 assert(h.$('idea-submit').disabled);assert(h.$('idea-status').textContent.includes('Loading research records'));
 assert(!h.$('experiment-results').innerHTML.includes('No matching'),'Pending data is never an empty archive');
 h.$('experiment-form').onsubmit({preventDefault(){}});assert.equal(h.apiCalls,0,'Forced submit cannot send an early API request');
 h.context.coverageFixture={id:'prime-notes',title:'Prime stream notes',phrases:['prime stream'],related:['prime-example'],status:'Partially covered',guide:'prime-guide',coverage:'A fixed key',needed:'Choose a rule',next_test:'Other keys'};
 vm.runInContext('ideaCoverageRecords=[coverageFixture]',h.context);
 const shared=h.context.ensureCheckerRecords();assert.equal(h.registryCalls,1,'Other consumers share the same registry fetch');
 h.pending[0].resolve(h.okay([record]));await shared;await flush();
 assert.equal(h.$('experiment-query'),input,'Completion never replaces the input');assert.equal(input.value,'prime stream LP2-15');
 assert.equal(h.context.document.activeElement,input);assert(!h.$('idea-submit').disabled);assert.equal(h.apiCalls,0,'Readiness does not request AI');
 assert(vm.runInContext('experimentRecords===undefined',h.context),'Cold checker must not fill the detail cache');
 assert(h.$('idea-coverage').innerHTML.includes('href="#/experiments/prime-example"'),'Coverage links use checker-local titles without a full registry');
 assert(h.$('experiment-results').innerHTML.includes(record.reader_finding));assert(h.$('experiment-results').innerHTML.includes(record.reader_limit));
 assert(!h.$('experiment-results').innerHTML.includes(record.finding),'Visible cards prefer reader text');
 assert(h.$('experiment-results').innerHTML.includes('<strong>Limit:</strong>'));
 assert(!h.context.experimentSearchResult({...record,reader_limit:undefined}).includes(record.limitations),'Cards do not expand long technical limitations when no curated limit exists');
 const exact=JSON.parse(Search.experimentDocs([record])[0].text);assert.equal(exact.finding,record.finding);assert.equal(exact.limitations,record.limitations,'Model evidence remains exact');
 // Editing invalidates every result surface, including asynchronously refreshed support.
 const snapshotSections=['experiment-results','idea-coverage','reported-attempts','experiment-answer'];
 let classifyCalls=0;const classify=h.context.AssistantSearch.classify;
 h.context.AssistantSearch={...Search,classify(...args){classifyCalls++;return classify(...args)}};
 for(const value of ['unrelated new method','']){
  for(const id of snapshotSections)h.$(id).innerHTML='Previous idea content';
  input.value=value;input.listeners.input();
  for(const id of snapshotSections)assert.equal(h.$(id).innerHTML,'',id+' clears when the idea changes');
  vm.runInContext('refreshIdeaSupport()',h.context);
  for(const id of snapshotSections)assert.equal(h.$(id).innerHTML,'',id+' stays clear after late support completion');
 }
 assert.equal(classifyCalls,0,'Editing never launches local classification');assert.equal(h.apiCalls,0,'Editing never launches inference');
 // Pending configuration must not submit the old question after an edit.
 let resolveConfig;h.context.pendingConfig=new Promise(resolve=>{resolveConfig=resolve});
 vm.runInContext('assistantConfig=null;assistantConfigPromise=pendingConfig',h.context);
 input.value='prime stream LP2-15';h.$('experiment-form').onsubmit({preventDefault(){}});
 assert(classifyCalls>0);assert(h.$('experiment-results').innerHTML.includes(record.reader_finding),'Explicit submit restores current matches');
 assert.equal(h.$('idea-status').textContent,'Preparing the comparison…');
 input.value='unrelated new method';input.listeners.input();
 vm.runInContext("assistantConfig={endpoint:'https://mock.example/ask'}",h.context);resolveConfig();await flush();
 assert.equal(h.apiCalls,0,'Superseded configuration cannot request comparison');
 for(const id of snapshotSections)assert.equal(h.$(id).innerHTML,'');
 // An in-flight comparison cannot restore stale answer/status or support after editing.
 let resolveComparison,comparisonSignal;
 h.context.fetch=(url,options)=>{assert.equal(options.method,'POST');comparisonSignal=options.signal;return new Promise(resolve=>{resolveComparison=resolve})};
 h.context.loadSupportingIndex=async()=>({documents:[]});
 input.value='prime stream LP2-15';h.$('experiment-form').onsubmit({preventDefault(){}});
 assert.equal(h.$('idea-status').textContent,'Comparing the documented scope…');
 input.value='';input.listeners.input();assert(comparisonSignal.aborted,'Editing aborts the superseded comparison');
 resolveComparison({ok:true,json:async()=>({answer:'Old comparison [1]',sources:[{id:record.id,href:'#/experiments/'+record.id,title:record.title}]})});await flush();
 for(const id of snapshotSections)assert.equal(h.$(id).innerHTML,'',id+' ignores a late comparison');
 assert.equal(h.$('idea-status').textContent,'');assert(!h.$('idea-submit').disabled);
 const retry=harness('prime stream');await retry.context.experimentsPage('',1,retry.query);
 retry.pending[0].reject(new Error('Offline'));await flush();
 assert(!retry.$('idea-retry').hidden);assert(retry.$('idea-submit').disabled);assert.equal(retry.$('experiment-query').value,'prime stream');
 const retryButton=retry.$('idea-retry');retryButton.focus();const first=retryButton.onclick(),second=retryButton.onclick();
 assert.equal(retry.registryCalls,2,'Repeated retry activation shares one load');
 assert(!retryButton.hidden&&retryButton.disabled,'Retry stays visible while awaiting its request');
 retry.pending[1].resolve(retry.okay([record]));await Promise.all([first,second]);
 assert.equal(retry.context.document.activeElement,retry.$('experiment-query'),'Retry recovery leaves no focus on a hidden button');
 assert.equal(retry.apiCalls,0,'Deep-link query and successful retry only show local matches');
 for(const fails of [false,true]){
  const stale=harness('prime stream');await stale.context.experimentsPage('',1,stale.query);
  const old=stale.$('experiment-query');stale.context.renderId=2;stale.context.main.innerHTML='<h1>New route</h1>';
  if(fails)stale.pending[0].reject(new Error('Late failure'));else stale.pending[0].resolve(stale.okay([record]));await flush();
  assert.equal(stale.context.main.innerHTML,'<h1>New route</h1>');assert(!old.isConnected);assert.equal(stale.apiCalls,0);
 }
 const empty=harness();await empty.context.experimentsPage('',1);assert.equal(empty.$('experiment-results').innerHTML,'');
 empty.pending[0].resolve(empty.okay([]));await flush();assert(empty.$('experiment-results').innerHTML.includes('No experiment records published yet'),'A confirmed empty registry is distinct from loading');
 console.log('PASS: immediate editable checker, shared deferred load, loading/empty/error/retry, preserved input/focus, stale success/error, plain cards with exact model evidence, edited-idea invalidation, late support/config/comparison guards and zero automatic AI requests.');
})().catch(error=>{console.error(error);process.exitCode=1});
