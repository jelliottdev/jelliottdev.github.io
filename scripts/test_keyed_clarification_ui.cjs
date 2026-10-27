/* Actual run.js flow: explicit local method choices, canonical save, safe retries. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto}=require('node:crypto');
const UI=require('../run.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const at='2026-10-25T12:00:00.000Z',base='https://mock.example',key=[23,18,3,4],uuid='11111111-1111-4111-8111-111111111111';
const clone=v=>JSON.parse(JSON.stringify(v)),deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return{promise,resolve,reject};};
const turn=()=>new Promise(resolve=>setImmediate(resolve));async function until(fn){const end=Date.now()+3000;while(!fn()){if(Date.now()>end)throw Error('Timed out waiting for the production flow.');await turn();}}
function documentFixture(hash){
 const nodes=new Map(),events={};let host;
 function make(id){let html='',children=[];const el={id,textContent:'',disabled:false,hidden:false,focus(){},querySelector(){return null;}};
  Object.defineProperty(el,'innerHTML',{get:()=>html,set:value=>{for(const old of children)nodes.delete(old);children=[];if(el===host)nodes.clear();html=value;for(const m of value.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){const child=make(m[1]);child.disabled=/\sdisabled(?:\s|>)/.test(m[0]);child.hidden=/\shidden(?:\s|>)/.test(m[0]);nodes.set(child.id,child);children.push(child.id);}}});return el;
 }
 host=make('task-workspace');const location={hash,href:'https://example.org/run.html'+hash};
 return {host,events,defaultView:{location,addEventListener:(name,fn)=>events[name]=fn,removeEventListener:name=>delete events[name]},getElementById:id=>id==='task-workspace'?host:nodes.get(id)||null};
}
async function main(){
 const {planCard}=await import('../services/idea-assistant/prepare-task.mjs'),{canonicalProposal}=await import('../services/idea-assistant/proposals.mjs');
 const known=value=>C.field('specified',value,{kind:'supplied',refs:['original:literal-key']}),confirmed=C.confirm(C.createDraft({source:{text:'Use the explicit DEOR index key. Let me choose arithmetic and restart.'},aim:known('solve LP2'),method:known({operations:[{id:'repeating_key',label:'Repeating key',key}]}),scope:known({pages:['lp2-15']}),rules:{evaluation:known({kind:'exact-prefix',values:[24,7,24]})}}),{id:'original',at});
 const initial=await canonicalProposal({requestId:uuid,fragment:H.encode(confirmed)}),original=JSON.parse(initial.cardJson),originalBytes=C.serialize(original);
 const otherCard=clone(original);otherCard.scope.value.pages=['lp2-16'];const otherSnapshot=C.confirm(H.decode('#idea='+Buffer.from(JSON.stringify(otherCard)).toString('base64url')).draft,{id:'other',at}),other=await canonicalProposal({requestId:'22222222-2222-4222-8222-222222222222',fragment:H.encode(otherSnapshot)});
 const partialCard=clone(original);partialCard.method.value.operations[0].direction='subtract';const partialSnapshot=C.confirm(H.decode('#idea='+Buffer.from(JSON.stringify(partialCard)).toString('base64url')).draft,{id:'partial',at}),partial=await canonicalProposal({requestId:'33333333-3333-4333-8333-333333333333',fragment:H.encode(partialSnapshot)});
 async function fixture(options={}){
  let origin=initial;if(options.operations){const changed=clone(original);changed.method.value.operations=clone(options.operations);const draft=H.decode('#idea='+Buffer.from(JSON.stringify(changed)).toString('base64url')).draft;origin=await canonicalProposal({requestId:uuid,fragment:H.encode(C.confirm(draft,{id:'compound',at}))});}
  const doc=documentFixture('#idea='+origin.id),requests=[],proposals=[],published=[],executions=[],ids=new Map(),cards=new Map([[initial.id,clone(original)],[other.id,JSON.parse(other.cardJson)],[partial.id,JSON.parse(partial.cardJson)],[origin.id,JSON.parse(origin.cardJson)]]),settings={endpoint:base+'/ask',localTaskEndpoint:base+'/tasks',researchIdeaEndpoint:base+'/ideas',proposalEndpoint:base+'/proposals',taskPreparationEndpoint:base+'/prepare-task'};
  const view=id=>({id,card:clone(cards.get(id)),createdAt:at,tasks:[],tasksTruncated:id===other.id});
  const app=UI.createApp(doc,{crypto:webcrypto,executor:{start(task){executions.push(task);throw Error('Clarifying an idea must not run anything.');}},fetcher:async(url,init={})=>{
   const body=init.body?JSON.parse(init.body):null;requests.push({url,method:init.method||'GET',body,signal:init.signal});
   if(url==='data/assistant.json')return Response.json(settings);
   if(url.startsWith(base+'/ideas/')&&!init.method){const id=url.slice((base+'/ideas/').length);assert(cards.has(id));return Response.json(view(id));}
   if(url===settings.taskPreparationEndpoint){assert(cards.has(body.proposalId));assert.deepEqual(body,{proposalId:body.proposalId,parentTaskId:null,includeMethodClarification:true});const response={...planCard(cards.get(body.proposalId)),proposalId:body.proposalId};return options.prepare?options.prepare(response):Response.json(response);}
   if(url===settings.proposalEndpoint){const canonical=await canonicalProposal(body);proposals.push({body:clone(body),canonical});const prior=ids.get(canonical.requestId);if(prior&&prior!==canonical.requestHash)return Response.json({error:'The same request ID cannot describe another source context.'},{status:409});ids.set(canonical.requestId,canonical.requestHash);cards.set(canonical.id,JSON.parse(canonical.cardJson));return options.proposal?options.proposal(canonical,proposals.length):Response.json({id:canonical.id,status:prior?'already_received':'received',receivedAt:at});}
   if(url===settings.researchIdeaEndpoint){assert(cards.has(body.proposalId));published.push(body.proposalId);const response=view(body.proposalId);return options.publish?options.publish(response):Response.json(response);}
   throw Error('Unexpected request: '+url);
  }});
  const f={doc,app,origin,requests,proposals,published,executions,cards,async click(id){const node=doc.getElementById(id);assert(node,'Expected control '+id);assert(!node.disabled,'Control '+id+' is disabled');return node.onclick();},async navigateTo(id){doc.defaultView.location.hash='#idea='+id;await doc.events.hashchange();},async navigate(){await this.navigateTo(other.id);}};
  if(options.waitReady!==false)await app.ready;return f;
 }
 function noWork(f){assert.equal(f.executions.length,0);assert(!f.requests.some(r=>r.url.includes('/tasks/')));assert.equal(C.serialize(f.cards.get(initial.id)),originalBytes);assert(!f.doc.getElementById('create-experiment'));}
 async function choose(f){await f.click('method-choice-subtract');assert.equal(f.app.getState().methodSession.question.parameter,'reset');await f.click('method-choice-word');assert.equal(f.app.getState().methodSession.question,null);assert(f.doc.getElementById('save-method-idea'));}
 let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
 await test('browser helper loads after its protocol/evaluator dependencies and before run.js',()=>{
  const html=fs.readFileSync(require.resolve('../run.html'),'utf8'),script=name=>html.indexOf('src="'+name+'.js');
  for(const name of ['experiment-protocols','output-evaluators','keyed-method-clarification','run'])assert(script(name)>=0,name+' is loaded');
  assert(script('experiment-protocols')<script('keyed-method-clarification'));assert(script('output-evaluators')<script('keyed-method-clarification'));assert(script('keyed-method-clarification')<script('run'));
 });
 await test('actual hashed saved idea requests missing settings; choices stay local until reviewed save',async()=>{
  const f=await fixture();try{
   assert(f.doc.getElementById('method-choice-add'));assert.equal(f.app.getState().methodSession.proposalId,initial.id);assert.equal(f.requests.filter(r=>r.method==='POST').length,1);assert.equal(f.proposals.length,0);
   await choose(f);assert.equal(f.proposals.length,0);assert.equal(f.published.length,0);assert.equal(f.requests.filter(r=>r.method==='POST').length,1);noWork(f);
   const session=f.app.getState().methodSession;assert.equal(session.draft.method.provenance.kind,'user_clarification');assert(session.draft.method.provenance.refs.includes('proposal:'+initial.id));assert.deepEqual(session.choices.map(c=>[c.parameter,c.value]),[['direction','subtract'],['reset','word']]);
   await f.click('save-method-idea');assert.equal(f.proposals.length,1);assert.equal(f.published.length,1);const saved=f.proposals[0],card=JSON.parse(saved.canonical.cardJson),expected=clone(original);Object.assign(expected.method.value.operations[0],{direction:'subtract',reset:'word'});
   assert.equal(C.serialize(card),C.serialize(expected));assert.equal(f.doc.defaultView.location.hash,'#idea='+saved.canonical.id);assert.notEqual(saved.canonical.id,initial.id);assert.equal(saved.body.sourceUrl,'https://jelliottdev.github.io/run.html#idea='+initial.id);assert.match(saved.body.note,/direction=subtract; reset=word/);assert.deepEqual(card.method.value.operations[0].key,key);noWork(f);
  }finally{f.app.destroy();}
 });
 await test('literal Vigenere and autokey modes show their maintained name and save only explicit missing choices',async()=>{
  for(const [id,label,heading,mode]of [['vigenere','Vigenere','Vigen\u00e8re','repeat'],['plaintext_autokey','Plaintext autokey','Plaintext autokey','plaintext-autokey'],['ciphertext_autokey','Ciphertext autokey','Ciphertext autokey','ciphertext-autokey']]){
   const f=await fixture({operations:[{id,label,key}]});try{assert(f.doc.getElementById('prepared-plan').innerHTML.includes('<strong>'+heading+':</strong>'));assert(!f.doc.getElementById('save-method-idea'));assert.equal(f.proposals.length,0);await choose(f);const session=f.app.getState().methodSession;assert.equal(session.draft.method.value.operations[0].id,id);assert.deepEqual(session.draft.method.value.operations[0].key,key);assert.equal(f.proposals.length,0);noWork(f);await f.click('save-method-idea');assert.equal(f.proposals.length,1);const saved=JSON.parse(f.proposals[0].canonical.cardJson),before=JSON.parse(f.origin.cardJson);assert.deepEqual(saved.outcome,before.outcome);assert.deepEqual(saved.scope,before.scope);assert.deepEqual(saved.rules,before.rules);assert.deepEqual(saved.method.value.operations,[{id,label,key,direction:'subtract',reset:'word'}]);assert.deepEqual(planCard(saved).steps,[{op:'keyed-shift',key,mode,direction:'subtract',reset:'word'}]);assert.equal(f.doc.defaultView.location.hash,'#idea='+f.proposals[0].canonical.id);noWork(f);}finally{f.app.destroy();}
  }
 });
 await test('changing settings resets only local choices and performs no save or run',async()=>{
  const f=await fixture();try{await choose(f);await f.click('reset-method-choices');assert.equal(f.app.getState().methodSession.question.parameter,'direction');assert.deepEqual(f.app.getState().methodSession.choices,[]);assert.equal(f.proposals.length,0);noWork(f);}finally{f.app.destroy();}
 });
 await test('lost proposal response retries the same UUID, fragment and canonical idea',async()=>{
  const f=await fixture({proposal(canonical,attempt){if(attempt===1)throw Error('Lost response after accepting the original request.');return Response.json({id:canonical.id,status:'already_received',receivedAt:at});}});try{
   await choose(f);await f.click('save-method-idea');assert(f.doc.getElementById('method-error').textContent);assert.equal(f.published.length,0);assert.equal(f.doc.defaultView.location.hash,'#idea='+initial.id);
   await f.click('save-method-idea');assert.equal(f.proposals.length,2);assert.deepEqual(f.proposals[0].body,f.proposals[1].body);assert.equal(f.proposals[0].canonical.id,f.proposals[1].canonical.id);assert.equal(f.published.length,1);assert.equal(f.doc.defaultView.location.hash,'#idea='+f.proposals[0].canonical.id);noWork(f);
  }finally{f.app.destroy();}
 });
 await test('different original ideas resolving to the same card retain separate request context',async()=>{
  const f=await fixture();try{
   await choose(f);await f.click('save-method-idea');const first=f.proposals[0];
   await f.navigateTo(partial.id);assert.equal(f.app.getState().methodSession.question.parameter,'reset');await f.click('method-choice-word');await f.click('save-method-idea');
   assert.equal(f.proposals.length,2);assert.equal(f.proposals[1].canonical.id,first.canonical.id,'Canonical final card identity is shared.');assert.notEqual(f.proposals[1].body.requestId,first.body.requestId,'The human confirmation has a distinct original context.');
   assert.equal(f.proposals[1].body.sourceUrl,'https://jelliottdev.github.io/run.html#idea='+partial.id);assert(f.proposals[1].body.note.includes(partial.id));assert.equal(f.published.length,2);assert.equal(f.doc.defaultView.location.hash,'#idea='+first.canonical.id);assert.equal(C.serialize(f.cards.get(partial.id)),partial.cardJson);noWork(f);
  }finally{f.app.destroy();}
 });
 await test('mismatched proposal receipt or returned card cannot navigate to a revised idea',async()=>{
  for(const mode of ['proposal-id','receipt-status','saved-card']){
   const f=await fixture({proposal:mode==='saved-card'?undefined:canonical=>Response.json({id:mode==='proposal-id'?other.id:canonical.id,status:mode==='receipt-status'?'invented':'received',receivedAt:at}),publish:mode==='saved-card'?response=>{const bad=clone(response);bad.card.method.value.operations[0].reset='line';return Response.json(bad);}:undefined});try{
    await choose(f);await f.click('save-method-idea');assert.equal(f.doc.defaultView.location.hash,'#idea='+initial.id);assert(f.doc.getElementById('method-error').textContent);assert.equal(f.published.length,mode==='saved-card'?1:0);assert(f.doc.getElementById('save-method-idea'));noWork(f);
   }finally{f.app.destroy();}
  }
 });
 await test('forged typed choices never reach local selection or persistence',async()=>{
  const f=await fixture({prepare(response){response.clarification.choices[0].value='beaufort';return Response.json(response);}});try{assert.equal(f.app.getState().methodSession,null);assert(f.doc.getElementById('idea-error').textContent);assert(!f.doc.getElementById('method-choice-subtract'));assert.equal(f.proposals.length,0);noWork(f);}finally{f.app.destroy();}
 });
 await test('navigation suppresses a late clarification response',async()=>{
  const pending=deferred(),f=await fixture({waitReady:false,prepare:()=>pending.promise});try{
   await until(()=>f.requests.some(r=>r.url===base+'/prepare-task'));await f.navigate();const response={...planCard(original),proposalId:initial.id};pending.resolve(Response.json(response));await f.app.ready;
   assert.equal(f.app.getState().idea.id,other.id);assert.equal(f.app.getState().methodSession,null);assert.equal(f.doc.defaultView.location.hash,'#idea='+other.id);assert(!f.doc.getElementById('method-choice-subtract'));assert.equal(f.proposals.length,0);noWork(f);
  }finally{f.app.destroy();}
 });
 await test('navigation suppresses late proposal and public-card save responses',async()=>{
  for(const phase of ['proposal','publish']){
   const pending=deferred(),f=await fixture(phase==='proposal'?{proposal:()=>pending.promise}:{publish:()=>pending.promise});try{
    await choose(f);const saving=f.click('save-method-idea');await until(()=>phase==='proposal'?f.proposals.length===1:f.published.length===1);await f.navigate();
    pending.resolve(Response.json(phase==='proposal'?{id:f.proposals[0].canonical.id,status:'received',receivedAt:at}:{id:f.proposals[0].canonical.id,card:JSON.parse(f.proposals[0].canonical.cardJson),createdAt:at,tasks:[]}));await saving;
    assert.equal(f.app.getState().idea.id,other.id);assert.equal(f.app.getState().methodSession,null);assert.equal(f.doc.defaultView.location.hash,'#idea='+other.id);assert.equal(f.published.length,phase==='proposal'?0:1);assert(!f.doc.getElementById('save-method-idea'));noWork(f);
   }finally{f.app.destroy();}
  }
 });
 await test('compound programs clarify only their indexed key step and retain every other ordered operation',async()=>{
  const reverseLine={id:'reverse_runes',label:'Reverse rune order within each line',unit:'line'},reverseWord={id:'reverse_runes',label:'Reverse rune order within each word',unit:'word'},keyed={id:'repeating_key',label:'Repeating key',key};
  for(const [operations,index]of [[[reverseLine,keyed],1],[[keyed,reverseWord],0]]){const f=await fixture({operations});try{const before=JSON.parse(f.origin.cardJson),context=f.doc.getElementById('prepared-plan').innerHTML;assert.equal(f.app.getState().methodSession.question.operationIndex,index);assert(context.includes('Repeating key (step '+(index+1)+')'));assert(context.includes('<code>23, 18, 3, 4</code>'));assert(context.includes('How should the key indices in step '+(index+1)));await choose(f);const session=f.app.getState().methodSession;assert.deepEqual(session.choices.map(c=>c.operationIndex),[index,index]);const completed=clone(before);Object.assign(completed.method.value.operations[index],{direction:'subtract',reset:'word'});assert.deepEqual(session.draft.method.value.operations,completed.method.value.operations);assert.equal(f.proposals.length,0);assert.equal(f.requests.filter(r=>r.method==='POST').length,1);await f.click('save-method-idea');const actual=JSON.parse(f.proposals[0].canonical.cardJson);assert.equal(C.serialize(actual),C.serialize(completed));assert.deepEqual(actual.method.value.operations[1-index],before.method.value.operations[1-index]);assert.equal(C.serialize(f.cards.get(f.origin.id)),f.origin.cardJson);assert.equal(f.proposals[0].body.sourceUrl,'https://jelliottdev.github.io/run.html#idea='+f.origin.id);noWork(f);}finally{f.app.destroy();}}
 });
 await test('forged compound target index is rejected before local choices or any persistence',async()=>{const operations=[{id:'reverse_runes',label:'Reverse rune order within each line',unit:'line'},{id:'repeating_key',label:'Repeating key',key}],f=await fixture({operations,prepare(response){response.clarification.operationIndex=0;return Response.json(response);}});try{assert.equal(f.app.getState().methodSession,null);assert(f.doc.getElementById('idea-error').textContent);assert.equal(f.proposals.length,0);noWork(f);}finally{f.app.destroy();}});
 await test('long literal keys keep choice controls close while preserving all confirmed indices',async()=>{const longKey=Array.from({length:256},(_,i)=>i%29),f=await fixture({operations:[{id:'repeating_key',label:'Repeating key',key:longKey}]});try{const html=f.doc.getElementById('prepared-plan').innerHTML;assert(html.includes('256 indices'));assert(html.includes('starts [0, 1, 2, 3, 4, 5, …]'));assert(!html.includes(longKey.join(', ')));assert.deepEqual(f.app.getState().methodSession.card.method.value.operations[0].key,longKey);await choose(f);assert.deepEqual(f.app.getState().methodSession.draft.method.value.operations[0].key,longKey);assert.equal(f.proposals.length,0);noWork(f);}finally{f.app.destroy();}});
 console.log(groups+' actual keyed clarification UI groups passed; no target executions or task writes.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
