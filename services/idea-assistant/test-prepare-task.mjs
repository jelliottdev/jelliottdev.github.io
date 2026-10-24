/* Deterministic planner: real SQLite, fixed injected pages, no AI/network. */
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createPrepareTaskHandler,planCard} from './prepare-task.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import L from '../../local-experiment.js';
const origin='https://jelliottdev.github.io',id='p_'+'a'.repeat(64),parent='b'.repeat(64),at='2026-10-24T12:00:00.000Z';
const index=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8'));
const alphabet=index.alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const raw=alphabet.slice(0,3).map(r=>r.rune).join('')+' '+alphabet[0].rune,reviewed=raw+'\n'+alphabet[2].rune;
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
function card(extra={}){return H.cardData(C.confirm(C.createDraft({source:{text:'PRIVATE original idea'},aim:known('solve LP2'),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]}),scope:known({pages:['lp2-15']}),...extra}),{id:'test',at}));}
function fixture(data=card()){
 const sqlite=new DatabaseSync(':memory:');for(const migration of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql','0004_local_tasks.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+migration,import.meta.url),'utf8'));
 sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,'a'.repeat(64),C.serialize(data),'unused',at);
 let reads=0,calls=0;const urls=[],rate=[];
 const env={SITE_ORIGIN:origin,PROPOSALS:{prepare(sql){assert(!sql.includes('original_idea'));assert(!sql.includes('proposal_submissions'));return {bind(...args){return {first:async()=>{reads++;return sqlite.prepare(sql).get(...args)||null;}};}};}},PROPOSAL_LIMIT:{limit:async value=>{rate.push(value);return {success:true};}},AI:{run(){throw Error('Planner must not call AI');}}};
 const handle=createPrepareTaskHandler({now:()=>new Date(at),fetcher:async(url,options)=>{calls++;urls.push(url);assert.equal(url,origin+'/data/pages/lp2-15.json');assert.equal(options.redirect,'error');assert(options.signal);return Response.json({id:'lp2-15',raw,reviewed_text:reviewed});}});
 return {sqlite,env,handle,urls,rate,get reads(){return reads;},get calls(){return calls;}};
}
const request=(body={proposalId:id,parentTaskId:null},extra={})=>new Request('https://worker.example/prepare-task',{method:'POST',headers:{origin,'content-type':'application/json','CF-Connecting-IP':'203.0.113.9',...extra},body:JSON.stringify(body)});
async function submit(f,body){const response=await f.handle(request(body),f.env);return {response,value:await response.json()};}
let count=0;async function test(name,fn){await fn();console.log('PASS '+name);count++;}
await test('supported reversal proposes canonical source-bound task without persistence/inference',async()=>{
 const f=fixture(),{response,value}=await submit(f);assert.equal(response.status,200);assert.equal(value.state,'plan-ready');assert.equal(value.parentTaskId,null);assert.equal(value.inputVersion,'raw');assert.deepEqual(value.task.alphabet,alphabet);assert.deepEqual(value.task.steps,[{op:'reverse',unit:'line'}]);assert.deepEqual(value.task.pages,[{id:'lp2-15',text:raw}]);await L.checkIdentity(value.task);
 assert(value.notes.some(n=>n.includes('preliminary measurement')));assert(value.notes.some(n=>n.includes('headings')));assert(!JSON.stringify(value).includes('PRIVATE'));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.rate[0].key,'203.0.113.9');
 const python=readFileSync(new URL('../../scripts/reproduce_reading.py',import.meta.url),'utf8');assert.equal(python.match(/RUNES = "([^"]+)"/)[1],alphabet.map(r=>r.rune).join(''));assert.deepEqual(python.match(/LATIN = "([^"]+)"/)[1].split(' '),alphabet.map(r=>r.latin));
});
await test('ordered explicit affine/feedback/boundary rules and reviewed text remain exact',async()=>{
 const f=fixture(card({method:known({operations:[{id:'affine',a:28,b:3},{id:'cumulative_difference',reset:'word'},{id:'reverse_row_runes'}]}),rules:{boundaryMode:known('within_words'),wordBoundaries:known('preserve'),inputVersion:known('reviewed'),representation:known('GP29'),unmapped:known('preserve'),reset:known('word'),initialState:known(0),evaluation:known({kind:'exact-prefix',values:[1,2]})}}));
 const {value}=await submit(f);assert.equal(value.state,'plan-ready');assert.deepEqual(value.task.steps,[{op:'affine',a:28,b:3},{op:'cumulative-difference',reset:'word'},{op:'reverse',unit:'word'}]);assert.deepEqual(value.task.criterion,{kind:'exact-prefix',values:[1,2]});assert.equal(value.task.pages[0].text,reviewed);assert.equal(value.inputVersion,'reviewed');
});
await test('opaque, incomplete, passage and unhandled consequential rules require adapter before fetching',async()=>{
 const inputs=[
  card({method:known({operations:[{id:'vigenere',key:'FOO'}]})}),
  card({method:known({operations:[{id:'affine',a:2}]})}),
  card({method:known({operations:[{id:'cumulative_difference'}]})}),
  card({method:known({operations:[{id:'reverse_row_runes',label:'Reverse rows except the heading'}]})}),
  card({scope:C.field()}),card({scope:known({pages:['lp2-15'],description:'Only lines 2–3'})}),
  card({unresolved:[{kind:'unknown',text:'Skip some positions'}]}),
  ...Object.entries({exceptionalCases:'Except the heading',searchBounds:{keys:['ABC']},searchProtocol:'shuffle 2000 times',representation:'decimal primes',evaluation:'English readability',inputVersion:'another text',boundaryMode:'word_blocks',reset:'line',initialState:4}).map(([key,value])=>card({rules:{[key]:known(value)}})),
  card({method:known({operations:[{id:'cumulative_difference',reset:'word'}]}),rules:{reset:known('line')}}),
  card({method:known({operations:[{id:'reverse_row_runes',key:'SECRET'}]})})];
 for(const c of inputs){const f=fixture(c),{value}=await submit(f);assert.equal(value.state,'needs-adapter',JSON.stringify(c));assert.equal(f.calls,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);}
});
await test('strict route/method/origin/fields/bounds, configuration and rate protect DB',async()=>{
 const f=fixture();for(const extra of [{origin:'https://evil.example'},{origin:''}])assert.equal((await f.handle(request(undefined,extra),f.env)).status,403);
 assert.equal((await f.handle(new Request('https://worker.example/prepare-task',{headers:{origin}}),f.env)).status,405);
 assert.equal((await f.handle(new Request('https://worker.example/other',{headers:{origin}}),f.env)).status,404);
 assert.equal((await f.handle(request(undefined,{'content-type':'text/plain'}),f.env)).status,400);
 assert.equal((await f.handle(request(undefined,{'content-length':'32001'}),f.env)).status,400);
 for(const b of [{proposalId:id},{proposalId:id,parentTaskId:null,extra:true},{proposalId:'wrong',parentTaskId:null}])assert.equal((await submit(f,b)).response.status,400);
 assert.equal((await f.handle(request(),{...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}})).status,429);assert.equal(f.reads,0);
 assert.equal((await f.handle(request(),{...f.env,PROPOSALS:null})).status,503);
 const pre=new Request('https://worker.example/prepare-task',{method:'OPTIONS',headers:{origin,'access-control-request-method':'POST','access-control-request-headers':'content-type'}});assert.equal((await f.handle(pre,f.env)).status,204);
});
await test('pure card planner and task-specific rate binding share production validation',async()=>{
 const input=card(),copy=structuredClone(input),plan=planCard(input);assert.deepEqual(input,copy);assert.deepEqual(plan.steps,[{op:'reverse',unit:'line'}]);assert.equal(plan.inputVersion,'raw');
 assert.throws(()=>planCard({...input,version:999}));
 const f=fixture();let limited=0;
 const env={...f.env,TASK_LIMIT:{limit:async()=>{limited++;return {success:true};}},PROPOSAL_LIMIT:{limit:async()=>{throw Error('Wrong limiter');}}};
 assert.equal((await f.handle(request(),env)).status,200);assert.equal(limited,1);
});
await test('multi-page loading stays at four workers with a shared cancellation signal',async()=>{
 const pages=Array.from({length:9},(_,i)=>'lp2-'+String(i).padStart(2,'0')),f=fixture(card({scope:known({pages})}));let active=0,max=0;const signals=[];
 const handle=createPrepareTaskHandler({fetcher:async(url,options)=>{assert.match(url,/^https:\/\/jelliottdev\.github\.io\/data\/pages\/lp2-0[0-8]\.json$/);signals.push(options.signal);active++;max=Math.max(max,active);await new Promise(resolve=>setTimeout(resolve,1));active--;return Response.json({id:url.split('/').pop().slice(0,-5),raw});}});
 const response=await handle(request(),f.env),value=await response.json();assert.equal(value.state,'plan-ready');assert.equal(max,4);assert(signals.every(signal=>signal===signals[0]));assert.deepEqual(value.task.pages.map(p=>p.id),pages);
});
await test('missing references and source fetch failures are recoverable, no task stored',async()=>{
 const f=fixture();assert.equal((await submit(f,{proposalId:'p_'+'c'.repeat(64),parentTaskId:null})).response.status,404);assert.equal((await submit(f,{proposalId:id,parentTaskId:parent})).response.status,404);
 const handle=createPrepareTaskHandler({fetcher:async()=>Response.json({id:'lp2-15',reviewed_text:reviewed})});assert.equal((await handle(request(),f.env)).status,422);
 const tooLarge=createPrepareTaskHandler({fetcher:async()=>Response.json({id:'lp2-15',raw:'X'.repeat(524289)})});assert.equal((await tooLarge(request(),f.env)).status,422);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);
});
console.log('PASS '+count+' deterministic prepare-task groups; all source fetches mocked, no AI/storage writes/deployment.');
