import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import L from '../local-experiment.js';
import {findEvidence,rememberEvidence,readIdeaEvidence,checkedEvidence} from '../services/idea-assistant/task-evidence.mjs';
import Family from '../research-family.js';
import {readFamilyEvidence} from '../services/idea-assistant/family-evidence.mjs';
import Evidence from '../computation-evidence.js';
import Language from '../language-score.js';

const at='2026-10-24T12:00:00.000Z',alphabet=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8')).alphabet;
const digest=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(L.stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');
function fixture(){
 const sqlite=new DatabaseSync(':memory:'),dir=new URL('../services/idea-assistant/migrations/',import.meta.url);
 for(const name of readdirSync(dir).filter(name=>/^\d{4}_.*\.sql$/.test(name)).sort())sqlite.exec(readFileSync(new URL(name,dir),'utf8'));
 let writes=false,readHook=null;const queries=[],db={prepare(sql){if(!writes)assert.match(sql,/^\s*SELECT\b/,'Discovery must never write');queries.push(sql);return {bind(...args){return {all:async()=>{const results=sqlite.prepare(sql).all(...args);if(readHook)readHook({sql,args,results});return {results};},first:async()=>sqlite.prepare(sql).get(...args)||null,run:async()=>sqlite.prepare(sql).run(...args)};}};}};
 return {sqlite,db,queries,setWrites(value){writes=value;},setReadHook(fn){readHook=fn;}};
}
async function task({title='Requested',pages=['lp2-00','lp2-01'],text='ᚠᚢ-ᚦᚩ\nᚱ',steps=[{op:'reverse',unit:'word'}],criterion={kind:'exact-prefix',values:[1,0]}}={}){return L.prepare({title,pages:pages.map(id=>({id,text})),alphabet,steps,criterion});}
let sequence=0;
async function source(f,t,{published=true,version='raw',associationVersion=version,result=true,date=at}={}){
 const id='p_'+String(++sequence).padStart(64,'0');
 f.sqlite.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,id.slice(2),'{"PRIVATE ORIGINAL":"must never leak"}','private fragment',date);
 if(published)f.sqlite.prepare('INSERT INTO research_ideas VALUES(?,?,?)').run(id,date,date.slice(0,10));
 const json=L.stable(t),taskHash=await digest(t);
 const existing=f.sqlite.prepare('SELECT id FROM local_tasks WHERE id=?').get(t.taskId);
 if(!existing)f.sqlite.prepare('INSERT INTO local_tasks VALUES(?,?,?,?,?,?,?,?,?,?)').run(t.taskId,taskHash,'0'.repeat(64),id,'private card',json,version,null,date,date.slice(0,10));
 f.sqlite.prepare('INSERT INTO local_task_ideas VALUES(?,?,?,?,?,?)').run(t.taskId,id,associationVersion,null,date,date.slice(0,10));
 let run=null;if(result){const output=L.run(t),resultJson=L.stable(output),resultId=await digest(output);f.sqlite.prepare('INSERT OR IGNORE INTO local_task_results VALUES(?,?,?,?,?)').run(resultId,t.taskId,resultJson,date,date.slice(0,10));run={id:resultId,result:output};}
 return {id,task:t,run};
}
async function familySource(f,{page='lp2-00',bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8')),date=at}={}){
 const preparer=await Family.createPreparer(bundle),caseId='plaintext-autokey--subtract--word--'+page,plan=await preparer.prepare([caseId]),item=plan.cases[0],result=L.run(item.task),resultId=await digest(result);
 f.sqlite.prepare('INSERT INTO family_case_results VALUES(?,?,?,?,?,?,?,?,?,?)').run(plan.familyId,plan.revision,item.id,item.task.taskId,L.stable(item.task),resultId,L.stable(result),Number(result.matches[0].matched),date,date.slice(0,10));
 return {plan,item,result,resultId,bundle};
}
async function familyRequest(source,{pages=source.item.task.pages,steps=source.item.task.steps,criterion=source.item.task.criterion}={}){return L.prepare({title:'Independent generic wording',pages,alphabet:source.item.task.alphabet,steps,criterion});}
async function inspect(f,t,version='raw'){
 const original=L.run,verify=L.verify,before=f.sqlite.prepare('SELECT total_changes() n').get().n;
 L.run=()=>{throw Error('Evidence discovery must not execute a target');};L.verify=async()=>{throw Error('Evidence discovery must not replay a target');};
 try{const value=await findEvidence({db:f.db,task:t,inputVersion:version});assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);assert(!JSON.stringify(value).includes('PRIVATE ORIGINAL'));return value;}finally{L.run=original;L.verify=verify;}
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}

await test('empty storage and unrun sources leave exact requested scope open',async()=>{
 const f=fixture(),t=await task();assert.deepEqual(await inspect(f,t),{coveredPages:[],remainingPages:['lp2-00','lp2-01'],evidence:[],exactTaskId:null,truncated:false});await source(f,await task({title:'Unrun'}),{result:false});assert.deepEqual((await inspect(f,t)).remainingPages,['lp2-00','lp2-01']);
});
await test('public disjoint batches union exact covered pages without inventing an exact whole task',async()=>{
 const f=fixture(),t=await task(),a=await source(f,await task({title:'First batch',pages:['lp2-00']})),b=await source(f,await task({title:'Second batch',pages:['lp2-01']}));await source(f,await task({title:'Other page',pages:['lp2-03']}));
 const value=await inspect(f,t);assert.deepEqual(value.coveredPages,['lp2-00','lp2-01']);assert.deepEqual(value.remainingPages,[]);assert.equal(value.exactTaskId,null);assert.deepEqual(new Set(value.evidence.map(e=>e.taskId)),new Set([a.task.taskId,b.task.taskId]));assert(value.evidence.every(e=>Object.keys(e).sort().join(',')==='createdAt,pages,resultId,taskId'));
});
await test('contributing source proofs retain full overlapping pages and compare canonically',async()=>{
 const f=fixture(),t=await task({pages:['lp2-00','lp2-01','lp2-02']});await source(f,await task({title:'First overlap',pages:['lp2-00','lp2-01']}));await source(f,await task({title:'Second overlap',pages:['lp2-01','lp2-02']}));
 const coverage=await inspect(f,t);assert.equal(coverage.evidence.length,2);assert(coverage.evidence.every(ref=>ref.pages.includes('lp2-01')));assert.deepEqual(coverage.coveredPages,['lp2-00','lp2-01','lp2-02']);
 const checked=await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:coverage.evidence});assert.deepEqual(checked,{coveredPages:coverage.coveredPages,remainingPages:coverage.remainingPages,evidence:coverage.evidence,exactTaskId:coverage.exactTaskId});
});
await test('titles and page batch order do not prevent complete task reuse',async()=>{
 const f=fixture(),t=await task(),saved=await source(f,await task({title:'Earlier wording',pages:['lp2-01','lp2-00']}));const value=await inspect(f,t);assert.equal(value.exactTaskId,saved.task.taskId);assert.deepEqual(value.coveredPages,['lp2-00','lp2-01']);assert.deepEqual(value.evidence[0].pages,['lp2-00','lp2-01']);
});
await test('partial evidence, changed text, criterion, step order and version stay separate',async()=>{
 const f=fixture(),t=await task();await source(f,await task({title:'One exact page',pages:['lp2-00']}));
 await source(f,await task({title:'Different bytes',pages:['lp2-01'],text:'ᚠᚢ-ᚦᚩ\nᚳ'}));await source(f,await task({title:'Different criterion',pages:['lp2-01'],criterion:{kind:'measurement'}}));await source(f,await task({title:'Different steps',pages:['lp2-01'],steps:[{op:'reverse',unit:'line'}]}));await source(f,await task({title:'Reviewed',pages:['lp2-01']}),{version:'reviewed'});
 const value=await inspect(f,t);assert.deepEqual(value.coveredPages,['lp2-00']);assert.deepEqual(value.remainingPages,['lp2-01']);assert.equal(value.exactTaskId,null);assert.equal(value.evidence.length,1);
});
await test('only matching public associations are considered; original and association versions both bind',async()=>{
 const f=fixture(),t=await task();await source(f,await task({title:'Private'}),{published:false});await source(f,await task({title:'Private raw but public reviewed association'}),{associationVersion:'reviewed'});await source(f,await task({title:'Reviewed origin raw association'}),{version:'reviewed',associationVersion:'raw'});assert.deepEqual((await inspect(f,t)).coveredPages,[]);
 const shared=await task({title:'Public shared computation'});await source(f,shared,{published:false});await source(f,shared,{published:true});assert.equal((await inspect(f,t)).exactTaskId,shared.taskId);assert.equal((await inspect(f,t)).evidence.length,1);
});
await test('corrupt task hash or latest result fails closed, never looks like missing work',async()=>{
 for(const mutation of ['task','result']){const f=fixture(),t=await task(),saved=await source(f,t);if(mutation==='task')f.sqlite.prepare('UPDATE local_tasks SET task_hash=?').run('0'.repeat(64));else f.sqlite.prepare('UPDATE local_task_results SET result_json=? WHERE id=?').run('{}',saved.run.id);await assert.rejects(()=>inspect(f,t));}
 const f=fixture(),t=await task();await source(f,t);f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run('0'.repeat(64),t.taskId,'{}','2026-10-25T12:00:00.000Z','2026-10-25');await assert.rejects(()=>inspect(f,t));
});
await test('bounded candidate discovery reports truncation and deterministically prefers recent saved results',async()=>{
 const f=fixture(),t=await task({pages:['lp2-00']}),sources=[];
 for(let i=0;i<102;i++)sources.push(await source(f,await task({title:'Historical candidate '+i,pages:['lp2-00']}),{date:new Date(Date.UTC(2026,9,24,0,0,i)).toISOString()}));
 const value=await inspect(f,t);assert.equal(value.truncated,true);assert.equal(value.evidence.length,1,'duplicate coverage retains one bounded proof');assert(!value.evidence.some(e=>e.taskId===sources[0].task.taskId||e.taskId===sources[1].task.taskId));assert.equal(value.exactTaskId,value.evidence[0].taskId);assert.deepEqual(await inspect(f,t),value);
});
await test('protocol expression index covers historical immutable rows without backfill',async()=>{
 const f=fixture(),t=await task();await source(f,t);const before=f.sqlite.prepare('SELECT task_json,task_hash,id FROM local_tasks').all();await inspect(f,t);
 const lookup=f.queries.findLast(sql=>sql.includes('FROM local_tasks t JOIN local_task_results')),plan=f.sqlite.prepare('EXPLAIN QUERY PLAN '+lookup).all(L.stable(t.pages),'raw',t.engine,L.stable(t.alphabet),L.stable(t.steps),L.stable(t.criterion),'raw');assert(plan.some(row=>String(row.detail).includes('local_tasks_protocol_lookup')));assert.deepEqual(f.sqlite.prepare('SELECT task_json,task_hash,id FROM local_tasks').all(),before);
});
await test('frozen requested computation survives reload while coverage is derived afresh',async()=>{
 const f=fixture(),t=await task(),idea=await source(f,await task({title:'Unrun idea anchor'}),{result:false});f.setWrites(true);
 await rememberEvidence({db:f.db,proposalId:idea.id,task:t,inputVersion:'raw',coverage:{complete:true,PRIVATE:'never stored'},createdAt:at});f.setWrites(false);
 const row=f.sqlite.prepare('SELECT * FROM idea_computation_evidence').get();assert.equal(row.requested_task_id,t.taskId);assert(!Object.keys(row).some(key=>/coverage|complete/.test(key)));assert(!JSON.stringify(row).includes('PRIVATE'));assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 const before=f.sqlite.prepare('SELECT total_changes() n').get().n,empty=await readIdeaEvidence({db:f.db,proposalId:idea.id});assert.deepEqual(empty.remainingPages,['lp2-00','lp2-01']);assert.deepEqual(empty.requestedTask,t);assert.equal(empty.inputVersion,'raw');assert.equal(f.sqlite.prepare('SELECT total_changes() n').get().n,before);
 await source(f,await task({title:'Later public result'}));const covered=await readIdeaEvidence({db:f.db,proposalId:idea.id});assert.deepEqual(covered.remainingPages,[]);assert.deepEqual(covered.coveredPages,['lp2-00','lp2-01']);assert.deepEqual(f.sqlite.prepare('SELECT * FROM idea_computation_evidence').get(),row);
});
await test('new preparations retain earlier frozen snapshots; selected read and latest read are deterministic',async()=>{
 const f=fixture(),first=await task(),second=await task({title:'Fresh requested source',text:'ᚢᚦ-ᚩᚱ\nᚳ'}),idea=await source(f,await task({title:'Anchor'}),{result:false});f.setWrites(true);
 await rememberEvidence({db:f.db,proposalId:idea.id,task:first,inputVersion:'raw',createdAt:at});await rememberEvidence({db:f.db,proposalId:idea.id,task:second,inputVersion:'raw',createdAt:'2026-10-25T12:00:00.000Z'});f.setWrites(false);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM idea_computation_evidence').get().n,2);assert.equal((await readIdeaEvidence({db:f.db,proposalId:idea.id})).requestedTask.taskId,second.taskId);assert.equal((await readIdeaEvidence({db:f.db,proposalId:idea.id,taskId:first.taskId})).requestedTask.taskId,first.taskId);
 f.setWrites(true);await assert.rejects(()=>rememberEvidence({db:f.db,proposalId:idea.id,task:first,inputVersion:'reviewed',createdAt:at}));await assert.rejects(()=>rememberEvidence({db:f.db,proposalId:'p_'+'f'.repeat(64),task:first,inputVersion:'raw',createdAt:at}));await assert.rejects(()=>rememberEvidence({db:f.db,proposalId:idea.id,task:first,inputVersion:'raw',createdAt:'2026-10-24'}));f.setWrites(false);
 f.sqlite.prepare('UPDATE idea_computation_evidence SET requested_task_hash=? WHERE requested_task_id=?').run('0'.repeat(64),first.taskId);await assert.rejects(()=>readIdeaEvidence({db:f.db,proposalId:idea.id,taskId:first.taskId}));assert.equal(await readIdeaEvidence({db:f.db,proposalId:idea.id,taskId:'e'.repeat(64)}),null);
});
await test('pinned immutable evidence remains valid when newer candidates appear and rejects altered receipts',async()=>{
 const f=fixture(),t=await task(),saved=await source(f,await task({title:'Pinned public source'})),proof=(await inspect(f,t)).evidence;
 const original=L.run,verify=L.verify;L.run=()=>{throw Error('No target execution');};L.verify=async()=>{throw Error('No target replay');};
 try{const checked=await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:proof});assert.deepEqual(checked.coveredPages,['lp2-00','lp2-01']);
  // A newer corrupted result cannot replace the exact older immutable receipt.
  f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run('0'.repeat(64),saved.task.taskId,'{}','2026-10-25T12:00:00.000Z','2026-10-25');assert.deepEqual((await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:proof})).coveredPages,checked.coveredPages);
  for(const mutate of [p=>{p[0].pages=['lp2-03'];},p=>{p[0].createdAt='2026-10-25T12:00:00.000Z';},p=>{p[0].resultId='f'.repeat(64);},p=>{p.push(p[0]);}]){const altered=structuredClone(proof);mutate(altered);await assert.rejects(()=>checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:altered}));}
  f.sqlite.prepare('DELETE FROM research_ideas WHERE proposal_id=?').run(saved.id);await assert.rejects(()=>checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:proof}));
 }finally{L.run=original;L.verify=verify;}
});
await test('generic discovery consumes family receipts without copying tasks or fabricating public ideas',async()=>{
 const f=fixture(),saved=await familySource(f),t=await familyRequest(saved),coverage=await inspect(f,t);
 assert.deepEqual(coverage.coveredPages,['lp2-00']);assert.deepEqual(coverage.remainingPages,[]);assert.equal(coverage.exactTaskId,saved.item.task.taskId);assert.deepEqual(coverage.familySources,[{taskId:saved.item.task.taskId,familyId:saved.plan.familyId,revision:saved.plan.revision,caseId:saved.item.id}]);assert.equal(coverage.evidence[0].resultId,saved.resultId);
 assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_tasks').get().n,0);assert.equal(f.sqlite.prepare('SELECT COUNT(*) n FROM local_task_results').get().n,0);
 assert.deepEqual((await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:coverage.evidence})).coveredPages,['lp2-00']);
 const lookup=f.queries.findLast(sql=>sql.includes('SELECT saved.* FROM family_case_results')),query=f.sqlite.prepare('EXPLAIN QUERY PLAN '+lookup).all('deor-feedback-v1',t.engine,L.stable(t.alphabet),L.stable(t.steps),L.stable(t.criterion),L.stable(t.pages));assert(query.some(row=>String(row.detail).includes('family_case_protocol_lookup')));
});
await test('mixed stores union exact pages, preserve family routing and refresh frozen idea coverage',async()=>{
 const f=fixture(),saved=await familySource(f),pages=['lp2-00','lp2-01','lp2-02'].map(id=>({id,text:saved.bundle.pages.find(p=>p.id===id).raw})),t=await familyRequest(saved,{pages});
 const generic=await source(f,await familyRequest(saved,{pages:[pages[1]]}));const coverage=await inspect(f,t);assert.deepEqual(coverage.coveredPages,['lp2-00','lp2-01']);assert.deepEqual(coverage.remainingPages,['lp2-02']);assert.equal(coverage.evidence.length,2);assert.equal(coverage.familySources.length,1);assert(!coverage.familySources.some(ref=>ref.taskId===generic.task.taskId));
 assert.deepEqual((await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:coverage.evidence})).evidence,coverage.evidence);
 f.setWrites(true);await rememberEvidence({db:f.db,proposalId:generic.id,task:t,inputVersion:'raw',coverage,createdAt:at});f.setWrites(false);
 assert.deepEqual((await readIdeaEvidence({db:f.db,proposalId:generic.id})).familySources,coverage.familySources);
 await familySource(f,{page:'lp2-02'});const refreshed=await readIdeaEvidence({db:f.db,proposalId:generic.id});assert.deepEqual(refreshed.remainingPages,[]);assert.equal(refreshed.familySources.length,2);
});
await test('family evidence cannot cover changed rules, changed page bytes or reviewed source context',async()=>{
 const f=fixture(),saved=await familySource(f),normal=await familyRequest(saved);
 for(const changed of [await familyRequest(saved,{pages:[{...normal.pages[0],text:normal.pages[0].text+'ᚠ'}]}),await familyRequest(saved,{steps:[{...normal.steps[0],reset:'line'}]}),await familyRequest(saved,{criterion:{kind:'measurement'}}),await familyRequest(saved,{steps:[{...normal.steps[0],key:[1,2,3,4]}]})]){const coverage=await inspect(f,changed);assert.deepEqual(coverage.coveredPages,[]);assert(!Object.hasOwn(coverage,'familySources'));}
 assert.deepEqual((await inspect(f,normal,'reviewed')).coveredPages,[]);
 const privateSource=await source(f,normal,{published:false});const coverage=await inspect(f,normal);assert.equal(coverage.evidence.length,1);assert.equal(coverage.evidence[0].taskId,saved.item.task.taskId);assert(!JSON.stringify(coverage).includes(privateSource.id));
});
await test('family case, result and verdict corruption fails closed across discovery and pinned checks',async()=>{
 for(const mutation of ['result','case','task','verdict']){
  const f=fixture(),saved=await familySource(f),t=await familyRequest(saved),proof=(await inspect(f,t)).evidence;
  if(mutation==='result')f.sqlite.prepare('UPDATE family_case_results SET result_json=?').run('{}');
  if(mutation==='case')f.sqlite.prepare('UPDATE family_case_results SET case_id=?').run('plaintext-autokey--subtract--line--lp2-00');
  if(mutation==='task')f.sqlite.prepare('UPDATE family_case_results SET task_id=?').run('0'.repeat(64));
  if(mutation==='verdict')f.sqlite.prepare('UPDATE family_case_results SET matched=1-matched').run();
  await assert.rejects(()=>inspect(f,t));await assert.rejects(()=>checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:proof}));
 }
});
await test('historical family revisions remain readable and pinned receipts survive newer equivalent rows',async()=>{
 const f=fixture(),first=await familySource(f),t=await familyRequest(first),proof=(await inspect(f,t)).evidence;
 const next=structuredClone(first.bundle);next.pages.find(p=>p.id==='lp2-01').raw+='ᚠ';const second=await familySource(f,{bundle:next,date:'2026-10-25T12:00:00.000Z'});assert.notEqual(second.plan.revision,first.plan.revision);assert.equal(second.item.task.taskId,first.item.task.taskId);
 const original=L.run,verify=L.verify;L.run=()=>{throw Error('No target decode');};L.verify=async()=>{throw Error('No target replay');};
 try{const old=await readFamilyEvidence({db:f.db,familyId:first.plan.familyId,revision:first.plan.revision,caseId:first.item.id,taskId:first.item.task.taskId,resultId:first.resultId});assert.equal(old.source.run.createdAt,at);assert.deepEqual(old.source.run.result,first.result);assert.deepEqual((await checkedEvidence({db:f.db,task:t,inputVersion:'raw',evidence:proof})).evidence,proof);
  const newest=await inspect(f,t);assert.equal(newest.familySources[0].revision,second.plan.revision);assert.equal(newest.evidence[0].createdAt,'2026-10-25T12:00:00.000Z');assert.equal(await readFamilyEvidence({db:f.db,familyId:first.plan.familyId,revision:'f'.repeat(64),caseId:first.item.id}),null);
 }finally{L.run=original;L.verify=verify;}
});
await test('one request-local comparison preserves the old canonical proof without rescoring retained language sources',async()=>{
 const f=fixture(),t=await task({pages:['lp2-00'],text:'ᚠᚢᚦᚩᚱᚳᚷᚹ'.repeat(10),criterion:Language.criterion()}),saved=[];
 for(let i=0;i<100;i++)saved.push(await source(f,await task({title:'Equivalent language source '+i,pages:['lp2-00'],text:t.pages[0].text,criterion:Language.criterion()})));
 const sources=saved.map(item=>({task:item.task,inputVersion:'raw',run:{...item.run,createdAt:at}})),originalCompare=Evidence.compare,originalEvaluate=Language.evaluate;
 // Independently run the former two-comparison implementation as the byte-for-
 // byte oracle, including exact-witness preference and canonical receipt order.
 let oldEvaluations=0;Language.evaluate=(...args)=>{oldEvaluations++;return originalEvaluate(...args);};
 let expected;
 try{const comparison=await originalCompare(t,'raw',sources),represented=new Set(),proof=[];for(const item of comparison.evidence.slice().sort((a,b)=>Number(b.taskId===comparison.exactTaskId)-Number(a.taskId===comparison.exactTaskId)||a.taskId.localeCompare(b.taskId)||a.resultId.localeCompare(b.resultId)))if(item.pages.some(id=>!represented.has(id))){proof.push(item);item.pages.forEach(id=>represented.add(id));}const retained=new Set(proof.map(p=>p.taskId));expected={...await originalCompare(t,'raw',sources.filter(s=>retained.has(s.task.taskId))),truncated:false};}finally{Language.evaluate=originalEvaluate;}
 let compares=0,evaluations=0;Evidence.compare=async(...args)=>{compares++;return originalCompare(...args);};Language.evaluate=(...args)=>{evaluations++;return originalEvaluate(...args);};
 const start=performance.now();let actual;
 try{actual=await inspect(f,t);assert.equal(compares,1);assert.equal(evaluations,1,'One exact vector evaluation serves all sources while every claimed score remains checked');assert.equal(oldEvaluations,2,'Separate comparisons cannot reuse a previous request-local evaluation');assert.equal(L.stable(actual),L.stable(expected));}
 finally{Evidence.compare=originalCompare;Language.evaluate=originalEvaluate;}
 console.log('BENCH 100 duplicate language sources: '+(performance.now()-start).toFixed(1)+' ms; '+evaluations+' distinct-vector evaluation versus '+oldEvaluations+' in the independent two-pass oracle, identical proof bytes.');
 // Returned comparison objects and stored rows remain mutable outside discovery;
 // neither can authorize reuse in the next lookup. A discarded witness is not
 // authoritative evidence: its corruption must not contribute or alter coverage.
 actual.coveredPages=[];actual.evidence=[];const discarded=saved.find(s=>s.task.taskId!==expected.exactTaskId),tampered=structuredClone(discarded.run.result);tampered.languageScore.pages[0].models[0].total++;const id=await digest(tampered);
 f.sqlite.prepare('DELETE FROM local_task_results WHERE task_id=?').run(discarded.task.taskId);f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run(id,discarded.task.taskId,L.stable(tampered),at,at.slice(0,10));
 assert.equal(L.stable(await inspect(f,t)),L.stable(expected),'Discarded corrupt receipts cannot contribute to the independently validated proof');
 const chosen=saved.find(s=>s.task.taskId===expected.exactTaskId),bad=structuredClone(chosen.run.result);bad.languageScore.pages[0].models[0].total++;const badId=await digest(bad);f.sqlite.prepare('DELETE FROM local_task_results WHERE task_id=?').run(chosen.task.taskId);f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run(badId,chosen.task.taskId,L.stable(bad),at,at.slice(0,10));await assert.rejects(()=>inspect(f,t),/language comparison is inconsistent/,'Selected corrupt receipts must still be fully validated');
});
await test('100 full 58-page duplicate receipts load and validate one complete payload with unchanged canonical proof',async()=>{
 const f=fixture(),bundle=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8')),pages=bundle.pages.filter(page=>page.id.startsWith('lp2-')).map(page=>({id:page.id,text:page.raw}));
 const requested=await L.prepare({title:'Requested 58-page diagnostic',pages,alphabet,steps:[{op:'reverse',unit:'line'}],criterion:Language.criterion()}),base=L.run(requested),saved=[];
 for(let i=0;i<100;i++){
  const t=await L.prepare({...requested,title:'Historical complete diagnostic '+i}),anchor=await source(f,t,{result:false}),result={...base,taskId:t.taskId},resultId=await digest(result);
  f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run(resultId,t.taskId,L.stable(result),at,at.slice(0,10));saved.push({task:t,inputVersion:'raw',run:{id:resultId,createdAt:at,result}});
 }
 const selected=saved.slice().sort((a,b)=>a.task.taskId.localeCompare(b.task.taskId))[0],expected={...await Evidence.compare(requested,'raw',[selected]),truncated:false};
 let metadataRows=0,payloadRows=0,validatedSources=0;f.setReadHook(({sql,results})=>{if(sql.includes('AS matching_pages')){metadataRows+=results.length;assert(results.every(row=>!Object.hasOwn(row,'task_json')&&!Object.hasOwn(row,'result_json')));}if(sql.includes('FROM json_each(?) proof JOIN local_tasks'))payloadRows+=results.length;});
 const compare=Evidence.compare;Evidence.compare=async(...args)=>{validatedSources+=args[2].length;return compare(...args);};let actual;const start=performance.now();try{actual=await inspect(f,requested);}finally{Evidence.compare=compare;}
 assert.equal(metadataRows,100);assert.equal(payloadRows,1);assert.equal(validatedSources,1);assert.equal(L.stable(actual),L.stable(expected));assert.equal(actual.coveredPages.length,58);assert.equal(actual.remainingPages.length,0);
 console.log('BENCH 100 x 58 pages: '+(performance.now()-start).toFixed(1)+' ms; 100 metadata rows, 1 full receipt loaded and validated; '+base.metrics.runes+' runes per source.');
});
await test('metadata and full receipt races preserve pinned evidence or fail closed, never replace it with latest',async()=>{
 for(const race of ['new-latest','delete-result','remove-public','change-task-hash']){
  const f=fixture(),requested=await task(),saved=await source(f,await task({title:'Race source '+race}));let changed=false;
  f.setReadHook(({sql})=>{if(!changed&&sql.includes('AS matching_pages')){changed=true;if(race==='new-latest')f.sqlite.prepare('INSERT INTO local_task_results VALUES(?,?,?,?,?)').run('0'.repeat(64),saved.task.taskId,'{}','2026-10-25T12:00:00.000Z','2026-10-25');if(race==='delete-result')f.sqlite.prepare('DELETE FROM local_task_results WHERE id=?').run(saved.run.id);if(race==='remove-public')f.sqlite.prepare('DELETE FROM research_ideas WHERE proposal_id=?').run(saved.id);if(race==='change-task-hash')f.sqlite.prepare('UPDATE local_tasks SET task_hash=? WHERE id=?').run('0'.repeat(64),saved.task.taskId);}});
  if(race==='new-latest'){const value=await findEvidence({db:f.db,task:requested,inputVersion:'raw'});assert.equal(value.evidence[0].resultId,saved.run.id);assert.equal(value.evidence[0].createdAt,at);assert.equal(value.coveredPages.length,2);}else await assert.rejects(()=>findEvidence({db:f.db,task:requested,inputVersion:'raw'}),/unavailable|identity|immutable/);
  assert(changed);
 }
});
console.log('Task evidence discovery: '+groups+' groups passed');
