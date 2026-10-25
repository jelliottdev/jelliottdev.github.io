import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';
import L from '../../local-experiment.js';
import {canonicalProposal} from './proposals.mjs';
import {issue as issuePreparation} from './prepared-plans.mjs';
import Family from '../../research-family.js';
import {createTaskExtensionHandler} from './task-extensions.mjs';

const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const alphabet=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
const bundleURL=origin+'/data/local-run-inputs.json';
const sourcePage=id=>({id,raw:id==='lp2-50'?'':alphabet[Number(id.slice(4))%29].rune+' /\r\n',reviewed_text:alphabet[(Number(id.slice(4))+1)%29].rune});
const pageIds=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
const sourceBundle=(letters=alphabet)=>({schema:'liberpedia-local-inputs-v1',alphabet:letters.map(entry=>({...entry})),pages:pageIds.map(sourcePage)});
const digest=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
function fixture({fetcher,timeoutMs=20000}={}){
 const sqlite=new DatabaseSync(':memory:');for(const name of readdirSync(new URL('./migrations/',import.meta.url)).filter(name=>name.endsWith('.sql')).sort())sqlite.exec(readFileSync(new URL('./migrations/'+name,import.meta.url),'utf8'));
 const queries=[],calls=[],rates=[];let aiCalls=0,bundleAlphabet=alphabet;
 const db={prepare(sql){assert.match(sql,/^\s*(?:SELECT\b|INSERT INTO (?:prepared_plans|idea_computation_evidence)\b)/i,'Extension may only issue an admission receipt');queries.push(sql);return {bind(...args){return {first:async()=>sqlite.prepare(sql).get(...args)||null,all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:async()=>sqlite.prepare(sql).run(...args)};}};}};
 const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{limit:async value=>{rates.push(value);return {success:true};}},AI:{run(){aiCalls++;throw Error('No AI allowed');}}};
 const handle=createTaskExtensionHandler({timeoutMs,fetcher:async(url,options)=>{
  calls.push({url,options});assert(url===bundleURL||/^https:\/\/jelliottdev\.github\.io\/data\/pages\/lp2-(?:[0-4]\d|5[0-5])\.json$/.test(url));assert.equal(options.redirect,'manual');
  if(fetcher)return fetcher(url,options);
  if(url===bundleURL)return Response.json(sourceBundle(bundleAlphabet));
  return Response.json(sourcePage(url.split('/').pop().slice(0,-5)));
 }});
 return {sqlite,env,handle,calls,queries,rates,setAlphabet(value){bundleAlphabet=value;},get aiCalls(){return aiCalls;}};
}
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
async function proposal(f,name='public',published=true){
 const card=C.createDraft({source:{text:'PRIVATE original '+name},aim:known(name==='private'?'Find readable text':name==='public'?'Measure repeat counts':'Measure repeat counts: '+name),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'}]}),scope:known({pages:['lp2-15']})});
 const p=await canonicalProposal({requestId:crypto.randomUUID(),fragment:S.encode(C.confirm(card,{id:name,at}))});
 f.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at)VALUES(?,?,?,?,?)').run(p.id,p.cardHash,p.cardJson,p.fragment,at);
 if(published)f.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(p.id,at,at.slice(0,10));return p;
}
async function parent(f,p,{pages=[{id:'lp2-15',text:'ᚠᚢ\r\nᚦ'}],title='Parent experiment',version='reviewed',verified=true}={}){
 const task=await L.prepare({title,pages,alphabet,steps:[{op:'reverse',unit:'word'},{op:'affine',a:2,b:7},{op:'cumulative-difference',reset:'line'}],criterion:{kind:'exact-prefix',values:[1,2,3]}});
 await insertTask(f,p,task,{version,verified});return task;
}
async function insertTask(f,p,task,{version='reviewed',parentTaskId=null,verified=true}={}){
 const text=L.stable(task);f.sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(task.taskId,await digest(text),'0'.repeat(64),p.id,p.cardJson,text,version,parentTaskId,at,at.slice(0,10));
 f.sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(task.taskId,p.id,version,parentTaskId,at,at.slice(0,10));
 if(verified)await submitFixture(f,task);
}
async function submitFixture(f,task){
 const result=await L.verify(task,L.run(task)),text=L.stable(result);
 f.sqlite.prepare('INSERT OR IGNORE INTO local_task_results VALUES(?,?,?,?,?)').run(await digest(text),task.taskId,text,at,at.slice(0,10));
}
function req(id,{scope='remaining-lp2'}={},options={}){return new Request('https://worker.example'+(options.path||'/tasks/'+id+'/extensions'),{method:options.method||'POST',headers:{origin,'content-type':'application/json',...options.headers},...((options.method||'POST')==='POST'?{body:JSON.stringify({scope})}:{})});}
async function ready(f,t){const response=await f.handle(req(t.taskId),f.env);assert.equal(response.status,200,await response.clone().text());return response.json();}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}

await test('exact remaining-only plan preserves scientific inputs, publishes nothing and never runs AI',async()=>{
 const f=fixture(),p=await proposal(f),t=await parent(f,p,{pages:[{id:'lp1-00',text:'ᚠ'},{id:'lp2-00',text:'ᚢ'},{id:'lp2-15',text:'ᚦ'},{id:'lp2-56',text:'ᚩ'}]});
 const before=f.sqlite.prepare('SELECT * FROM local_tasks').all(),changes=f.sqlite.prepare('SELECT total_changes() n').get().n;
 const output=await ready(f,t);assert.equal(output.state,'plan-ready');assert.equal(output.proposalId,p.id);assert.equal(output.parentTaskId,t.taskId);assert.equal(output.inputVersion,'reviewed');
 assert.deepEqual(output.coveredPages,['lp2-00','lp2-15']);
 assert.deepEqual(output.task.steps,t.steps);assert.deepEqual(output.task.alphabet,t.alphabet);assert.deepEqual(output.task.criterion,t.criterion);
 assert.deepEqual(output.task.pages.map(p=>p.id),Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0')).filter(id=>!['lp2-00','lp2-15'].includes(id)));
 assert(output.task.pages.every(page=>page.text===alphabet[(Number(page.id.slice(4))+1)%29].rune));await L.checkIdentity(output.task);assert.notEqual(output.task.taskId,t.taskId);
 assert.match(output.purpose,/beyond the original request/);assert(!JSON.stringify(output).includes('PRIVATE'));
 assert.equal(f.calls.length,1);assert.equal(f.calls[0].url,bundleURL);assert(f.calls.every(c=>c.options.signal===f.calls[0].options.signal));assert.equal(f.aiCalls,0);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,changes+1);assert.match(output.preparation.id,/^prep_[a-f0-9]{64}$/);assert.equal(output.preparation.authority,'remaining-lp2');assert.deepEqual(f.sqlite.prepare('SELECT * FROM local_tasks').all(),before);
});
await test('large55-page scopes use one exact aggregate fetch with raw/reviewed bytes and no fallback',async()=>{
 for(const version of ['raw','reviewed']){const f=fixture(),p=await proposal(f),t=await parent(f,p,{version}),out=await ready(f,t);assert.equal(out.task.pages.length,55);assert.equal(f.calls.length,1);assert.equal(f.calls[0].url,bundleURL);assert.deepEqual(out.task.pages,out.task.pages.map(page=>({id:page.id,text:sourcePage(page.id)[version==='raw'?'raw':'reviewed_text']})));assert.equal(out.task.pages.find(page=>page.id==='lp2-50').text,version==='raw'?'':sourcePage('lp2-50').reviewed_text);if(version==='raw')assert(out.task.pages.find(page=>page.id==='lp2-00').text.endsWith(' /\r\n'));await L.checkIdentity(out.task);}
 for(const damage of [bundle=>{bundle.pages[1]=bundle.pages[0];},bundle=>{bundle.pages.pop();},bundle=>{bundle.schema='other';},bundle=>{bundle.alphabet[0].latin='DIFFERENT';},bundle=>{bundle.pages.find(p=>p.id==='lp2-00').reviewed_text=null;}]){
  const bundle=sourceBundle();damage(bundle);const f=fixture({fetcher:async()=>Response.json(bundle)}),p=await proposal(f),t=await parent(f,p),before=f.sqlite.prepare('SELECT total_changes() n').get().n,response=await f.handle(req(t.taskId),f.env);assert.equal(response.status,422);assert(!Object.hasOwn(await response.json(),'task'));assert.equal(f.calls.length,1,'Invalid aggregate never falls back to55 external page requests');assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 }
 const oversized=fixture({fetcher:async()=>new Response('{}',{headers:{'Content-Type':'application/json','Content-Length':String(2*1024*1024+1)}})}),p=await proposal(oversized),t=await parent(oversized,p);assert.equal((await oversized.handle(req(t.taskId),oversized.env)).status,422);assert.equal(oversized.calls.length,1);
});
await test('public association selected instead of private original, retaining its input version',async()=>{
 const f=fixture(),privateIdea=await proposal(f,'private',false),publicIdea=await proposal(f),t=await parent(f,privateIdea,{version:'raw'});
 assert.equal((await f.handle(req(t.taskId),f.env)).status,404);assert.equal(f.calls.length,0);
 f.sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(t.taskId,publicIdea.id,'reviewed',null,at,at.slice(0,10));
 const output=await ready(f,t);assert.equal(output.proposalId,publicIdea.id);assert.equal(output.inputVersion,'reviewed');assert(!JSON.stringify(output).includes(privateIdea.id));
});
await test('covered scope returns exact parent/idea context without fetching or saving; title bounded in codepoints',async()=>{
 const f=fixture(),p=await proposal(f),pages=Array.from({length:56},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:''})),t=await parent(f,p,{pages});
 const output=await ready(f,t);assert.deepEqual(Object.keys(output).sort(),['coveredPages','parentTaskId','plannedPages','proposalId','reason','state']);assert.equal(output.state,'scope-covered');assert.equal(output.proposalId,p.id);assert.equal(output.parentTaskId,t.taskId);assert.equal(f.calls.length,0);assert.deepEqual(output.coveredPages,pages.map(p=>p.id));
 const g=fixture(),q=await proposal(g),long=await parent(g,q,{title:'🧪'.repeat(300)});const plan=await ready(g,long);assert(Array.from(plan.task.title).length<=300);assert(plan.task.title.endsWith(' · remaining LP2 pages'));await L.checkIdentity(plan.task);
});
await test('source batch max4 concurrent workers, shared abort, redirect rejection and actual deadline',async()=>{
 let active=0,max=0;const f=fixture({fetcher:async(url)=>{active++;max=Math.max(max,active);await new Promise(resolve=>setTimeout(resolve,1));active--;return Response.json({id:url.split('/').pop().slice(0,-5),raw:'ᚠ'});}}),p=await proposal(f),t=await parent(f,p,{version:'raw',pages:Array.from({length:20},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:'ᚠ'}))});
 assert.equal((await ready(f,t)).state,'plan-ready');assert.equal(max,4);assert.equal(f.calls.length,36);assert(f.calls.every(c=>c.url!==bundleURL),'Small remaining scopes retain bounded per-page loading');
 for(const fetcher of [async()=>new Response(null,{status:302,headers:{location:'https://evil.example'}}),async()=>Response.json({id:'wrong',raw:'ᚠ'}),()=>{throw Error('PRIVATE failure');}]){
  const g=fixture({fetcher}),q=await proposal(g),u=await parent(g,q,{version:'raw'});const response=await g.handle(req(u.taskId),g.env);assert.equal(response.status,422);assert.equal(g.calls.length,1);assert.equal(g.calls[0].url,bundleURL,'Failed aggregate cannot fall back to page requests');assert.equal(g.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);assert(!(await response.text()).includes('PRIVATE'));
 }
 const failedSmall=fixture({fetcher:async()=>{throw Error('Small source failure');}}),smallIdea=await proposal(failedSmall),smallParent=await parent(failedSmall,smallIdea,{pages:Array.from({length:20},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:'ᚠ'}))});assert.equal((await failedSmall.handle(req(smallParent.taskId),failedSmall.env)).status,422);assert(failedSmall.calls.every(c=>c.options.signal.aborted),'Small per-page failures still cancel the whole shared batch');
 const hanging=fixture({timeoutMs:10,fetcher:()=>new Promise(()=>{})}),q=await proposal(hanging),u=await parent(hanging,q);
 const response=await hanging.handle(req(u.taskId),hanging.env);assert.equal(response.status,422);assert.equal(hanging.calls.length,1);assert.equal(hanging.calls[0].url,bundleURL);assert(hanging.calls.every(c=>c.options.signal.aborted));
});
await test('source and final runner bounds fail closed without altering parent or returning partial plan',async()=>{
 for(const text of ['ᚠ'.repeat(401),' '.repeat(6000)]){
  const f=fixture({fetcher:async url=>{assert.equal(url,bundleURL);const bundle=sourceBundle();bundle.pages=bundle.pages.map(page=>({...page,raw:text}));return Response.json(bundle);}}),p=await proposal(f),t=await parent(f,p,{version:'raw'});
  const before=f.sqlite.prepare('SELECT total_changes() n').get().n,response=await f.handle(req(t.taskId),f.env);assert.equal(response.status,422);assert(!Object.hasOwn(await response.json(),'task'));assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 }
});
await test('already-associated exact child opens existing task without relabeling old parent edge',async()=>{
 const f=fixture(),p=await proposal(f),t=await parent(f,p),planned=await ready(f,t),oldParent=await parent(f,p,{title:'Earlier different parent'});
 await insertTask(f,p,planned.task,{version:'reviewed',parentTaskId:oldParent.taskId,verified:false});const before=f.sqlite.prepare('SELECT * FROM local_task_ideas WHERE task_id=?').get(planned.task.taskId);
 const existing=await ready(f,t);assert.deepEqual(Object.keys(existing).sort(),['coveredPages','parentTaskId','plannedPages','proposalId','reason','state','taskId']);assert.equal(existing.state,'existing-task');assert.deepEqual(existing.coveredPages,['lp2-15']);assert.equal(existing.parentTaskId,t.taskId);assert.equal(existing.taskId,planned.task.taskId);assert.deepEqual(f.sqlite.prepare('SELECT * FROM local_task_ideas WHERE task_id=?').get(planned.task.taskId),before);
 f.sqlite.prepare('UPDATE local_task_ideas SET input_version=? WHERE task_id=?').run('raw',planned.task.taskId);assert.equal((await f.handle(req(t.taskId),f.env)).status,409);
});
await test('single-page parent plus remaining-only child covers history once without alternating new tasks',async()=>{
 const f=fixture(),p=await proposal(f),t=await parent(f,p),first=await ready(f,t);
 assert.equal(first.task.pages.length,55);await insertTask(f,p,first.task,{parentTaskId:t.taskId});f.calls.length=0;
 const before=f.sqlite.prepare('SELECT total_changes() n').get().n,second=await ready(f,first.task);
 assert.equal(second.state,'scope-covered');assert.equal(second.parentTaskId,first.task.taskId);assert.equal(second.coveredPages.length,56);assert.deepEqual(second.coveredPages,Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0')));assert.equal(f.calls.length,0);assert(!Object.hasOwn(second,'task'));assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
});
await test('unsubmitted current run is pending, not covered, even if every LP2 page is planned',async()=>{
 const f=fixture(),p=await proposal(f),pages=Array.from({length:56},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:''})),t=await parent(f,p,{pages,verified:false});
 const before=f.sqlite.prepare('SELECT total_changes() n').get().n,out=await ready(f,t);
 assert.equal(out.state,'runs-pending');assert.deepEqual(out.coveredPages,[]);assert.deepEqual(out.plannedPages,pages.map(p=>p.id));assert.deepEqual(out.pendingTasks,[{id:t.taskId,pages:pages.map(p=>p.id)}]);assert(!Object.hasOwn(out,'task'));assert.equal(f.calls.length,0);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 // A local computation alone is not a saved receipt.
 await L.verify(t,L.run(t));assert.equal((await ready(f,t)).state,'runs-pending');
 await submitFixture(f,t);const saved=await ready(f,t);assert.equal(saved.state,'scope-covered');assert.deepEqual(saved.coveredPages,pages.map(p=>p.id));assert.deepEqual(saved.plannedPages,saved.coveredPages);
});
await test('verified child with unsubmitted compatible ancestor directs that existing run then closes after receipt',async()=>{
 const f=fixture(),p=await proposal(f),t=await parent(f,p,{verified:false});
 const remaining=Array.from({length:56},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:'ᚠ'})).filter(page=>page.id!=='lp2-15');
 const child=await L.prepare({...t,title:'Verified remaining pages',pages:remaining});await insertTask(f,p,child,{parentTaskId:t.taskId});
 const before=f.sqlite.prepare('SELECT total_changes() n').get().n,out=await ready(f,child);
 assert.equal(out.state,'runs-pending');assert.deepEqual(out.coveredPages,remaining.map(p=>p.id));assert.equal(out.plannedPages.length,56);assert.deepEqual(out.pendingTasks,[{id:t.taskId,pages:['lp2-15']}]);assert.equal(f.calls.length,0);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 await submitFixture(f,t);const after=await ready(f,child);assert.equal(after.state,'scope-covered');assert.equal(after.coveredPages.length,56);assert(!Object.hasOwn(after,'pendingTasks'));
});
await test('verified overlapping exact inputs suppress redundant pending tasks, but different bytes and LP1 remain pending',async()=>{
 for(const mode of ['identical','changed-text','unverified-lp1']){
  const f=fixture(),p=await proposal(f),oldPages=[{id:'lp2-15',text:'ᚠᚢ'}];if(mode==='unverified-lp1')oldPages.unshift({id:'lp1-00',text:'ᚦ'});
  const old=await parent(f,p,{pages:oldPages,verified:false});
  const pages=Array.from({length:56},(_,i)=>({id:'lp2-'+String(i).padStart(2,'0'),text:i===15?(mode==='changed-text'?'ᚠᚦ':'ᚠᚢ'):'ᚠ'}));
  const child=await L.prepare({...old,title:'Full verified overlap '+mode,pages});await insertTask(f,p,child,{parentTaskId:old.taskId});
  const before=f.sqlite.prepare('SELECT total_changes() n').get().n,out=await ready(f,child);
  assert.equal(out.coveredPages.length,56);assert.equal(out.plannedPages.length,56);assert.equal(f.calls.length,0);assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
  if(mode==='identical'){assert.equal(out.state,'scope-covered');assert(!Object.hasOwn(out,'pendingTasks'));}
  else{assert.equal(out.state,'runs-pending');assert.deepEqual(out.pendingTasks,[{id:old.taskId,pages:oldPages.map(page=>page.id)}]);}
 }
});
await test('pending lineage uses exact public-compatible scopes and does not expose foreign or changed ancestors',async()=>{
 for(const change of ['steps','inputVersion','foreign']){
  const f=fixture(),p=await proposal(f),other=change==='foreign'?await proposal(f,'private',false):p;
  const old=await parent(f,other,{verified:false}),body={...old,title:'New independent pending',pages:[{id:'lp1-00',text:'ᚠ'},{id:'lp2-00',text:'ᚦ'},{id:'lp2-56',text:'ᚢ'}]};
  if(change==='steps')body.steps=[{op:'affine',a:1,b:0}];
  const child=await L.prepare(body);await insertTask(f,p,child,{verified:false,parentTaskId:old.taskId,version:change==='inputVersion'?'raw':'reviewed'});
  const out=await ready(f,child);assert.equal(out.state,'runs-pending');assert.deepEqual(out.plannedPages,['lp2-00']);assert.deepEqual(out.coveredPages,[]);assert.deepEqual(out.pendingTasks,[{id:child.taskId,pages:['lp1-00','lp2-00','lp2-56']}]);assert(!JSON.stringify(out).includes(old.taskId));assert.equal(f.calls.length,0);
 }
});
await test('changed protocol or input version stops history without excluding older pages',async()=>{
 for(const change of ['steps','alphabet','criterion','inputVersion']){
  const f=fixture(),p=await proposal(f),old=await parent(f,p),body=structuredClone(old);delete body.taskId;body.title='Changed '+change;body.pages=[{id:'lp2-00',text:'ᚠ'}];
  if(change==='steps')body.steps[1].b=8;if(change==='alphabet')body.alphabet[0].latin='OTHER';if(change==='criterion')body.criterion.values=[4];
  const child=await L.prepare(body);if(change==='alphabet')f.setAlphabet(child.alphabet);await insertTask(f,p,child,{version:change==='inputVersion'?'raw':'reviewed',parentTaskId:old.taskId});
  const output=await ready(f,child);assert.equal(output.state,'plan-ready');assert.deepEqual(output.coveredPages,['lp2-00']);assert(output.task.pages.some(page=>page.id==='lp2-15'));assert(output.notes.some(note=>note.includes('Earlier tasks used different settings')));
 }
});
await test('foreign private ancestor context is never counted or projected',async()=>{
 const f=fixture(),privateIdea=await proposal(f,'private',false),publicIdea=await proposal(f),old=await parent(f,privateIdea);
 const child=await L.prepare({...old,title:'Public child',taskId:undefined,pages:[{id:'lp2-00',text:'ᚠ'}]});await insertTask(f,publicIdea,child,{parentTaskId:old.taskId});
 const output=await ready(f,child);assert.deepEqual(output.coveredPages,['lp2-00']);assert(output.task.pages.some(page=>page.id==='lp2-15'));assert(!JSON.stringify(output).includes(privateIdea.id));assert(!JSON.stringify(output).includes(old.taskId));assert(output.notes.some(note=>note.includes('no association')));
});
await test('cyclic, corrupt and excessive same-idea ancestry fails before source fetch',async()=>{
 for(const mode of ['cycle','corrupt']){
  const f=fixture(),p=await proposal(f),old=await parent(f,p),child=await parent(f,p,{title:'Child'});
  f.sqlite.prepare('UPDATE local_task_ideas SET parent_task_id=? WHERE task_id=? AND proposal_id=?').run(old.taskId,child.taskId,p.id);
  if(mode==='cycle')f.sqlite.prepare('UPDATE local_task_ideas SET parent_task_id=? WHERE task_id=? AND proposal_id=?').run(child.taskId,old.taskId,p.id);
  else f.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('0'.repeat(64),old.taskId);
  const response=await f.handle(req(child.taskId),f.env);assert.equal(response.status,503);assert.equal(f.calls.length,0);
 }
 const f=fixture(),p=await proposal(f);let previous=null,last;
 for(let i=0;i<76;i++){last=await L.prepare({title:'Chain '+i,pages:[{id:'lp2-15',text:'ᚠ'}],alphabet,steps:[],criterion:{kind:'measurement'}});await insertTask(f,p,last,{parentTaskId:previous});previous=last.taskId;}
 assert.equal((await f.handle(req(last.taskId),f.env)).status,503);assert.equal(f.calls.length,0);
});
await test('global public exact evidence removes duplicate page work and freezes verifiable provenance',async()=>{
 const f=fixture(),p=await proposal(f),other=await proposal(f,'Different scientific wording'),t=await parent(f,p);
 const shared=await L.prepare({...t,title:'A different public experiment',pages:[{id:'lp2-16',text:sourcePage('lp2-16').reviewed_text}]});await insertTask(f,other,shared);
 const out=await ready(f,t);
 assert.deepEqual(out.coveredPages,['lp2-15','lp2-16']);assert(!out.task.pages.some(page=>page.id==='lp2-16'));assert(out.plannedPages.includes('lp2-16'));
 assert.deepEqual(out.coverage.coveredPages,['lp2-16']);assert.equal(out.coverage.evidence[0].taskId,shared.taskId);assert.equal(out.coverage.inputVersion,'reviewed');
 const basis=JSON.parse(f.sqlite.prepare('SELECT basis_json FROM prepared_plans WHERE id=?').get(out.preparation.id).basis_json);
 assert.equal(basis.requestedTaskId,out.coverage.requestedTask.taskId);assert.deepEqual(basis.evidence,out.coverage.evidence);
 const args={db:f.env.PROPOSALS,proposalId:p.id,card:JSON.parse(p.cardJson),task:out.task,inputVersion:'reviewed',parentTaskId:t.taskId,controls:out.controls,authority:'remaining-lp2',createdAt:at};
 for(const bad of [{...basis,evidence:[]},{...basis,requestedTaskId:'0'.repeat(64)},{...basis,evidence:basis.evidence.map(ref=>({...ref,resultId:'0'.repeat(64)}))},{...basis,requestedTaskId:undefined}])await assert.rejects(()=>issuePreparation({...args,basis:bad}));
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,2);assert(!JSON.stringify(out).includes(other.id));
});
await test('public evidence with different criterion, source version, exact text or settings cannot exclude work',async()=>{
 for(const damage of ['criterion','version','text','steps','private','unsaved']){
  const f=fixture(),p=await proposal(f),other=await proposal(f,'Different '+damage,damage!=='private'),t=await parent(f,p);
  const body={...t,title:'Separate '+damage,pages:[{id:'lp2-16',text:sourcePage('lp2-16').reviewed_text}]};
  if(damage==='criterion')body.criterion={kind:'measurement'};if(damage==='steps')body.steps=[{op:'reverse',unit:'line'}];if(damage==='text')body.pages[0].text+='ᚠ';
  const source=await L.prepare(body);await insertTask(f,other,source,{version:damage==='version'?'raw':'reviewed',verified:damage!=='unsaved'});
  const out=await ready(f,t);assert.deepEqual(out.coveredPages,['lp2-15']);assert(out.task.pages.some(page=>page.id==='lp2-16'));assert(!Object.hasOwn(out,'coverage'));
 }
});
await test('corrupt shared result fails closed without issuing a new extension receipt',async()=>{
 const f=fixture(),p=await proposal(f),other=await proposal(f,'Corrupt public source'),t=await parent(f,p),source=await L.prepare({...t,title:'Corrupt shared',pages:[{id:'lp2-16',text:sourcePage('lp2-16').reviewed_text}]});await insertTask(f,other,source);
 f.sqlite.prepare('UPDATE local_task_results SET result_json=? WHERE task_id=?').run('{}',source.taskId);const before=f.sqlite.prepare('SELECT total_changes() n FROM local_tasks').get().n;
 assert.equal((await f.handle(req(t.taskId),f.env)).status,503);assert.equal(f.sqlite.prepare('SELECT total_changes() n FROM local_tasks').get().n,before);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM prepared_plans').get().n,0);
});
await test('global family receipts prevent duplicate generic extension work without copying task records',async()=>{
 const bundle=JSON.parse(readFileSync(new URL('../../data/local-run-inputs.json',import.meta.url),'utf8')),factory=await Family.createPreparer(bundle),plan=await factory.prepare(['plaintext-autokey--subtract--word--lp2-16']),item=plan.cases[0],result=L.run(item.task),resultId=await digest(L.stable(result));
 const f=fixture({fetcher:async url=>{assert.equal(url,bundleURL);return Response.json(bundle);}}),p=await proposal(f);
 const t=await L.prepare({...item.task,title:'Different generic proposal',pages:[{id:'lp2-15',text:bundle.pages.find(page=>page.id==='lp2-15').raw}]});await insertTask(f,p,t,{version:'raw'});
 f.sqlite.prepare('INSERT INTO family_case_results VALUES(?,?,?,?,?,?,?,?,?,?)').run(plan.familyId,plan.revision,item.id,item.task.taskId,L.stable(item.task),resultId,L.stable(result),Number(result.matches[0].matched),at,at.slice(0,10));
 const out=await ready(f,t);assert.deepEqual(out.coveredPages,['lp2-15','lp2-16']);assert(!out.task.pages.some(page=>page.id==='lp2-16'));assert.equal(out.coverage.familySources[0].caseId,item.id);assert.equal(out.coverage.evidence[0].resultId,resultId);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,1);
});
await test('strict origin/body/routes/methods, rate-before-DB and unavailable bindings',async()=>{
 const f=fixture(),p=await proposal(f),t=await parent(f,p);
 assert.equal((await f.handle(req(t.taskId,undefined,{headers:{origin:'https://evil.example'}}),f.env)).status,403);
 for(const method of ['GET','PUT','DELETE'])assert.equal((await f.handle(req(t.taskId,undefined,{method}),f.env)).status,405);
 for(const path of ['/tasks/bad/extensions','/tasks/'+t.taskId+'/extensions?scope=all','/tasks/'+t.taskId])assert.equal((await f.handle(req(t.taskId,undefined,{path}),f.env)).status,404);
 for(const scope of ['all',null,{},'x'.repeat(1100)])assert.equal((await f.handle(req(t.taskId,{scope}),f.env)).status,400);
 for(const body of [{scope:'remaining-lp2',steps:[]},{scope:'remaining-lp2',proposalId:p.id},null,[]]){
  const request=new Request('https://worker.example/tasks/'+t.taskId+'/extensions',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(body)});assert.equal((await f.handle(request,f.env)).status,400);
 }
 const pre=await f.handle(req(t.taskId,undefined,{method:'OPTIONS',headers:{'access-control-request-method':'POST','access-control-request-headers':'content-type'}}),f.env);assert.equal(pre.status,204);assert.equal(pre.headers.get('access-control-allow-origin'),origin);
 assert.equal(f.queries.length,0);assert.equal(f.rates.length,0);
 assert.equal((await f.handle(req(t.taskId),{...f.env,TASK_LIMIT:{limit:async()=>({success:false})}})).status,429);assert.equal(f.queries.length,0);
 for(const key of ['SITE_ORIGIN','PROPOSALS','TASK_LIMIT'])assert.equal((await f.handle(req(t.taskId),{...f.env,[key]:undefined})).status,503);
 assert.equal((await f.handle(req('0'.repeat(64)),f.env)).status,404);
 const fallback={...f.env,TASK_LIMIT:undefined,PROPOSAL_LIMIT:f.env.TASK_LIMIT};assert.equal((await f.handle(req(t.taskId),fallback)).status,200);
});
await test('corrupt stored parent/card rejected before loading any new input',async()=>{
 for(const mutate of [(f,t)=>f.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('0'.repeat(64),t.taskId),
  (f,t)=>f.sqlite.prepare('UPDATE local_tasks SET task_json=? WHERE id=?').run(JSON.stringify({...t,title:'Changed'}),t.taskId),
  f=>f.sqlite.prepare('UPDATE proposals SET card_hash=?').run('0'.repeat(64))]){
  const f=fixture(),p=await proposal(f),t=await parent(f,p);mutate(f,t);assert.equal((await f.handle(req(t.taskId),f.env)).status,503);assert.equal(f.calls.length,0);
 }
});
console.log('PASS '+groups+' scope-extension groups: real SQLite, bounded mocked official source, no model or task persistence.');
