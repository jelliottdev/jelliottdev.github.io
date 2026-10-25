'use strict';
/* Shared actual run.js fixture; private transport only, no production writes. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{createRequire}=require('node:module'),{webcrypto}=require('node:crypto');
const C=require('../claim-specification.js'),H=require('../claim-share.js'),E=require('../local-experiment.js'),Evidence=require('../computation-evidence.js');
const fixturePath=require.resolve('./test_local_run_ui.cjs'),source=fs.readFileSync(fixturePath,'utf8'),boundary=source.indexOf('\n(async()=>{');
assert(boundary>0,'Use the maintained fixture definitions without running its separate suite');
const shared={exports:{}};
vm.runInThisContext('(function(require,module,exports){'+source.slice(0,boundary)+'\nmodule.exports={fixture,card,makeTask,projection,receipt,proposalId,prepareEndpoint};\n})',{filename:fixturePath})(createRequire(fixturePath),shared,shared.exports);
const {fixture,card,makeTask,projection,receipt,proposalId,prepareEndpoint}=shared.exports;
const copy=structuredClone,route='#idea='+proposalId;
function exploratory(status='unspecified',wording='Maybe another text is the key'){
 const value=card();value.rules.evaluation={status};value.method.value.operations=[{id:'described_method',label:wording}];return value;
}
const posts=f=>f.requests.filter(r=>r.options.method==='POST');
function href(markup,id){const tag=markup.match(new RegExp('<a\\b[^>]*\\bid="'+id+'"[^>]*>'));assert(tag,'Missing navigation '+id);const value=tag[0].match(/\bhref="([^"]+)"/);assert(value,'Missing destination '+id);return value[1].replaceAll('&amp;','&').replaceAll('&#39;',"'").replaceAll('&quot;','"');}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 await test('each unspecified evaluation state preserves exploratory question without preparation writes or execution',async()=>{
  for(const status of ['unspecified','not_applicable','unrestricted']){
   const own=exploratory(status),before=E.stable(own),f=await fixture({hash:route,ideaCard:own,prepare:async()=>assert.fail('Exploratory load must not prepare')});
   try{assert.equal(f.doc.getElementById('idea-heading').textContent,'Research question saved');assert(f.doc.host.innerHTML.includes('No experiment is defined yet.'));assert(f.doc.host.innerHTML.includes('Maybe another text is the key'));assert(!f.doc.getElementById('prepare-experiment'));assert(!f.doc.getElementById('create-experiment'));assert(!f.doc.getElementById('run-browser'));assert.equal(posts(f).length,0);assert.equal(f.executions.length,0);assert.equal(f.controlExecutions.length,0);assert.equal(f.app.getState().prepared,null);assert.equal(E.stable(own),before);await f.app.reload();assert.equal(posts(f).length,0);assert.equal(f.executions.length,0);}finally{f.app.destroy();}
  }
 });
 await test('browse navigation and inline definition preserve the original idea without posting or running',async()=>{
  const wording='Use another text as the key; then reverse each row',own=exploratory('unspecified',wording),before=E.stable(own),f=await fixture({hash:route,ideaCard:own});
  try{assert.equal(href(f.doc.host.innerHTML,'explore-related-work'),'research.html#mode=list');assert.equal(f.doc.getElementById('explore-related-work').onclick,undefined);assert.equal(typeof f.doc.getElementById('define-check').onclick,'function');await f.click('define-check');assert(f.doc.getElementById('definition-heading'));assert(!f.doc.host.innerHTML.includes('research-first'));assert(f.doc.host.innerHTML.includes(wording));await f.click('evaluation-choice-language-samples');assert.equal(posts(f).length,0);await f.click('cancel-definition');assert(f.doc.getElementById('define-check'));assert.equal(f.doc.defaultView.location.hash,route);assert.equal(E.stable(f.app.getState().idea.card),before);assert.equal(posts(f).length,0);assert.equal(f.executions.length,0);}finally{f.app.destroy();}
 });
 await test('opaque method wording is visible as escaped text and cannot inject links or markup',async()=>{
  const wording='Try <img src=x onerror="run()"> & "book" as the key',f=await fixture({hash:route,ideaCard:exploratory('unspecified',wording)});
  try{const markup=f.doc.host.innerHTML;assert(markup.includes('Try &lt;img src=x onerror=&quot;run()&quot;&gt; &amp; &quot;book&quot; as the key'));assert(!markup.includes('<img'));assert.equal(new URLSearchParams(href(markup,'explore-related-work').split('#')[1]).get('q'),null);assert.equal(posts(f).length,0);assert.equal(f.executions.length,0);}finally{f.app.destroy();}
 });
 await test('multiple ordered method steps remain visible without a misleading literal filter',async()=>{
  const own=exploratory();own.method.value.operations=[{id:'described_method',label:'Use a poem as the key'},{id:'reverse_runes',label:'Reverse rune order within each word',unit:'word'}];const f=await fixture({hash:route,ideaCard:own});
  try{const words=H.sections(own).filter(([label])=>/^Step [0-9]+$/.test(label)).map(([,text])=>text);for(const word of words)assert(f.doc.host.innerHTML.includes(word));assert.equal(new URLSearchParams(href(f.doc.host.innerHTML,'explore-related-work').split('#')[1]).get('q'),null);assert.equal(posts(f).length,0);}finally{f.app.destroy();}
 });
 await test('an explicit supplied criterion still prepares automatically without running or saving',async()=>{
  const own=card();own.rules.evaluation={status:'specified',value:'measurement'};const task=await makeTask(),f=await fixture({hash:route,ideaCard:own,task,prepare:async()=>({state:'plan-ready',proposalId,parentTaskId:null,inputVersion:'raw',task,notes:[],purpose:'Exact supplied check'})});
  try{assert.equal(posts(f).length,1);assert.equal(posts(f)[0].url,prepareEndpoint);assert(f.app.getState().prepared);assert(f.doc.getElementById('create-experiment'));assert(!f.doc.host.innerHTML.includes('No experiment is defined yet.'));assert.equal(f.executions.length,0);assert.equal(f.controlExecutions.length,0);}finally{f.app.destroy();}
 });
 await test('existing tasks and truncated task history never falsely claim no experiment exists',async()=>{
  const task=await makeTask();for(const state of ['not-run','results-verified']){const f=await fixture({hash:route,ideaCard:exploratory(),ideaTasks:[{id:task.taskId,title:'Existing exact experiment',state}]});try{assert(f.doc.host.innerHTML.includes('Existing exact experiment'));assert(!f.doc.host.innerHTML.includes('No experiment is defined yet.'));assert(!f.doc.getElementById('define-check'));assert.equal(posts(f).length,0);assert.equal(f.executions.length,0);}finally{f.app.destroy();}}
  const f=await fixture({hash:route,ideaCard:exploratory(),ideaTruncated:true});try{assert(!f.doc.host.innerHTML.includes('No experiment is defined yet.'));assert(!f.doc.getElementById('define-check'));assert(f.doc.host.innerHTML.includes('Only the most recent experiments'));assert.equal(posts(f).length,0);}finally{f.app.destroy();}
  const unknown=await fixture({hash:route,ideaCard:exploratory(),ideaTruncated:null});try{assert(!unknown.doc.host.innerHTML.includes('No experiment is defined yet.'),'Unknown history completeness cannot claim zero experiments');assert(!unknown.doc.getElementById('define-check'));assert.equal(unknown.executions.length,0);}finally{unknown.app.destroy();}
 });
 await test('existing verified coverage and unreadable coverage retain their evidence lifecycle and never show an empty-question claim',async()=>{
  const task=await makeTask(),run=await receipt(E.run(task)),sources=[{task,inputVersion:'raw',run}],coverage={requestedTask:task,inputVersion:'raw',...await Evidence.compare(task,'raw',sources,webcrypto),truncated:false};
  const complete=await fixture({hash:route,ideaCard:exploratory(),ideaCoverage:coverage,get:async()=>Response.json(projection(task,run))});
  try{assert.equal(complete.doc.getElementById('idea-heading').textContent,'Review saved results');assert(!complete.doc.host.innerHTML.includes('No experiment is defined yet.'));assert(complete.doc.getElementById('idea-coverage').innerHTML.includes('This computation is already covered'));assert.equal(posts(complete).length,0);assert.equal(complete.executions.length,0);}finally{complete.app.destroy();}
  const broken=await fixture({hash:route,ideaCard:exploratory(),ideaCoverage:coverage,get:async()=>Response.json({error:'Private source unavailable'},{status:503})});
  try{assert.equal(broken.doc.getElementById('idea-heading').textContent,'Saved results could not be checked');assert(!broken.doc.host.innerHTML.includes('No experiment is defined yet.'));assert(broken.doc.getElementById('idea-error').textContent.includes('Saved evidence could not be checked'));assert.equal(posts(broken).length,0);assert.equal(broken.executions.length,0);}finally{broken.app.destroy();}
 });
 console.log(groups+' exploratory saved-idea UI groups passed; no hosted requests, writes or target execution');
})().catch(error=>{console.error(error);process.exitCode=1;});
