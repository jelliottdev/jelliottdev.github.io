import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createProposalHandler,canonicalProposal} from './proposals.mjs';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';

const origin='https://jelliottdev.github.io',at='2026-10-24T12:00:00.000Z';
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
function fragment(extra={}){return S.encode(C.confirm(C.createDraft({source:{text:'PRIVATE raw prompt',materials:[{name:'PRIVATE-file'}]},aim:known('solve LP2'),method:known({operations:[{id:'vigenere',label:'Vigenere',key:'FOO',reset:'page',sourceText:'PRIVATE source'}]}),scope:known({pages:['lp2-15','lp2-17']}),...extra}),{id:'private-confirmation',at}));}
function adapter(){
 const sqlite=new DatabaseSync(':memory:');for(const migration of ['0001_proposals.sql','0002_proposal_reviews.sql','0003_original_idea.sql'])sqlite.exec(readFileSync(new URL('./migrations/'+migration,import.meta.url),'utf8'));
 const db={sqlite,reads:0,failBatch:false,prepare(sql){return {bind(...args){return {sql,args,first:async()=>{db.reads++;return sqlite.prepare(sql).get(...args)||null;}};}};},async batch(statements){
  sqlite.exec('BEGIN IMMEDIATE');try{const rows=[];for(let i=0;i<statements.length;i++){if(db.failBatch&&i===1)throw Error('Injected storage failure');const s=statements[i],r=sqlite.prepare(s.sql).run(...s.args);rows.push({success:true,meta:{changes:Number(r.changes)}});}sqlite.exec('COMMIT');return rows;}catch(e){sqlite.exec('ROLLBACK');throw e;}
 }};return db;
}
function fixture(){const db=adapter(),rate=[];let day=at;const env={SITE_ORIGIN:origin,PROPOSALS:db,PROPOSAL_LIMIT:{limit:async value=>{rate.push(value);return {success:true};}}};return {db,env,rate,setDay:d=>{day=d;},handle:createProposalHandler({now:()=>new Date(day)})};}
const post=(data,headers={})=>new Request('https://worker.example/proposals',{method:'POST',headers:{origin,'content-type':'application/json','CF-Connecting-IP':'203.0.113.25',...headers},body:JSON.stringify(data)});
const request=(extra={})=>({requestId:crypto.randomUUID(),fragment:fragment(),...extra});
let count=0;async function test(name,fn){await fn();count++;console.log('PASS '+name);}

await test('strict origin, preflight, path/method and required bindings fail closed without persistence',async()=>{
 const f=fixture();
 assert.equal((await f.handle(post(request(),{origin:'https://other.example'}),f.env)).status,403);
 assert.equal((await f.handle(post(request(),{origin:''}),f.env)).status,403);
 for(const key of ['PROPOSALS','PROPOSAL_LIMIT','SITE_ORIGIN'])assert.equal((await f.handle(post(request()),{...f.env,[key]:undefined})).status,503);
 const preflight=()=>new Request('https://worker.example/proposals',{method:'OPTIONS',headers:{origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'}});
 const response=await f.handle(preflight(),f.env);assert.equal(response.status,204);assert.equal(response.headers.get('access-control-allow-origin'),origin);
 assert.equal((await f.handle(new Request('https://worker.example/proposals',{headers:{origin}}),f.env)).status,405);
 assert.equal((await f.handle(new Request('https://worker.example/other',{headers:{origin}}),f.env)).status,404);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) AS n FROM proposals').get().n,0);assert.equal(f.rate.length,0);
});
await test('canonicalization stores exact active card separately from optional original idea and no history/result/IP',async()=>{
 const f=fixture(),body=request({note:'A distinct historical source',sourceUrl:'https://github.com/example/project/blob/main/method.py',originalIdea:'  Try Vigenere key FOO on these two pages.\nKeep word spaces.  '}),response=await f.handle(post(body),f.env),result=await response.json();
 assert.equal(response.status,200);assert.deepEqual(Object.keys(result).sort(),['id','receivedAt','status']);assert.equal(result.status,'received');assert.equal(result.receivedAt,at);assert.match(result.id,/^p_[a-f0-9]{64}$/);
 const card=f.db.sqlite.prepare('SELECT * FROM proposals').get(),submission=f.db.sqlite.prepare('SELECT * FROM proposal_submissions').get();
 assert.equal(card.status,'pending');assert.equal(card.id,result.id);assert(!JSON.stringify(card).includes('PRIVATE'));assert(!JSON.stringify(submission).includes('203.0.113.25'));
 assert.equal(submission.note,body.note);assert.equal(submission.source_url,body.sourceUrl);assert.equal(submission.received_day,'2026-10-24');
 assert.equal(submission.original_idea,body.originalIdea);assert(!card.card_json.includes(body.originalIdea));
 assert.equal(S.decode(card.fragment).draft.method.value.operations[0].key,'FOO');assert.deepEqual(JSON.parse(card.card_json).scope.value.pages,['lp2-15','lp2-17']);assert.equal(f.rate[0].key,'203.0.113.25');
});
await test('identity is canonical exact card, never broad category/note/original wording; changed keys/scope/states differ',async()=>{
 const first=await canonicalProposal(request()),p=JSON.parse(Buffer.from(fragment().slice(6),'base64url').toString());
 p.method.value.operations[0]={reset:'page',key:'FOO',label:'Vigenere',id:'vigenere'};
 const reordered='#idea='+Buffer.from(JSON.stringify(p)).toString('base64url');
 assert.equal((await canonicalProposal(request({fragment:reordered,note:'Different note',originalIdea:'Different supplied source wording'}))).cardHash,first.cardHash);
 for(const changed of [fragment({scope:known({pages:['lp2-15','lp2-16','lp2-17']})}),fragment({method:known({operations:[{id:'vigenere',key:'BAR',reset:'page'}]})}),fragment({scope:C.field('unrestricted')})])assert.notEqual((await canonicalProposal(request({fragment:changed}))).cardHash,first.cardHash);
 const f=fixture(),a=request({originalIdea:'First source wording'}),b=request({note:'Additional note on same card',originalIdea:'Second source wording'});
 const ra=await(await f.handle(post(a),f.env)).json(),rb=await(await f.handle(post(b),f.env)).json();assert.equal(ra.id,rb.id);assert.equal(rb.status,'received');
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,2);
 assert.deepEqual(f.db.sqlite.prepare('SELECT original_idea FROM proposal_submissions ORDER BY rowid').all().map(r=>r.original_idea),['First source wording','Second source wording']);
});
await test('allowed idempotent retry avoids cap/duplicate; altered requestId reuse conflicts without losing notes',async()=>{
 const f=fixture(),a=request({note:'Original note'}),one=await(await f.handle(post(a),f.env)).json();
 const retry=await(await f.handle(post(a),f.env)).json();assert.equal(retry.status,'already_received');assert.equal(retry.id,one.id);assert.equal(retry.receivedAt,one.receivedAt);assert.equal(f.rate.length,2);
 assert.equal((await f.handle(post({...a,note:'Changed'}),f.env)).status,409);
 assert.equal((await f.handle(post({...a,originalIdea:'Added original idea after confirmation'}),f.env)).status,409);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,1);
 assert.equal(f.db.sqlite.prepare('SELECT note FROM proposal_submissions').get().note,'Original note');
 const reads=f.db.reads,denied={...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}};
 assert.equal((await f.handle(post(a),denied)).status,429);assert.equal(f.db.reads,reads,'Even retries must be rate-gated before database reads');
});
await test('concurrent SQLite-backed submissions enforce durable50/day atomically and reset by UTC day',async()=>{
 const f=fixture(),requests=Array.from({length:75},(_,i)=>request({note:'Contribution '+i}));
 const responses=await Promise.all(requests.map(r=>f.handle(post(r),f.env)));
 assert.equal(responses.filter(r=>r.status===200).length,50);assert.equal(responses.filter(r=>r.status===429).length,25);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,50);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1);
 const rows=f.db.sqlite.prepare('SELECT request_id FROM proposal_submissions LIMIT 1').get();const original=requests.find(r=>r.requestId===rows.request_id);
 assert.equal((await(await f.handle(post(original),f.env)).json()).status,'already_received');
 assert.equal((await f.handle(post(request({fragment:fragment({scope:known({pages:['lp2-43']})})})),f.env)).status,429);
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1,'Daily rejection cannot leave an orphan card');
 f.setDay('2026-10-25T00:00:01.000Z');assert.equal((await f.handle(post(request()),f.env)).status,200);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,51);
});
await test('same request concurrent retries or conflicting bodies cannot create duplicate submissions/orphan cards',async()=>{
 const f=fixture(),a=request();const responses=await Promise.all(Array.from({length:8},()=>f.handle(post(a),f.env)));assert(responses.every(r=>r.status===200));
 const values=await Promise.all(responses.map(r=>r.json()));assert.equal(values.filter(v=>v.status==='received').length,1);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,1);
 const conflicting=await f.handle(post({...a,fragment:fragment({scope:known({pages:['lp2-43']})})}),f.env);assert.equal(conflicting.status,409);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1);
 const g=fixture(),sharedId=crypto.randomUUID();
 const simultaneous=await Promise.all([g.handle(post(request({requestId:sharedId})),g.env),g.handle(post(request({requestId:sharedId,fragment:fragment({scope:known({pages:['lp2-43']})})})),g.env)]);
 assert.deepEqual(simultaneous.map(r=>r.status).sort(),[200,409]);assert.equal(g.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,1);
});
await test('review metadata changes append old/new audit rows; no-op updates preserve history/cards/notes',async()=>{
 const f=fixture(),r=await(await f.handle(post(request({note:'Immutable note'})),f.env)).json(),db=f.db.sqlite;
 const card=db.prepare('SELECT card_json, fragment, card_hash, created_at FROM proposals WHERE id=?').get(r.id);
 const submissions=db.prepare('SELECT * FROM proposal_submissions').all();
 assert.equal(db.prepare('SELECT COUNT(*) n FROM proposal_reviews').get().n,0);
 db.prepare('UPDATE proposals SET status=?,reviewed_at=?,review_reason=?,record_id=? WHERE id=? AND status=?').run('accepted',at,'Initial reason','existing-record',r.id,'pending');
 let rows=db.prepare('SELECT * FROM proposal_reviews ORDER BY id').all();assert.equal(rows.length,1);
 assert.equal(rows[0].proposal_id,r.id);assert.equal(rows[0].old_status,'pending');assert.equal(rows[0].new_status,'accepted');assert.equal(rows[0].old_reviewed_at,null);assert.equal(rows[0].new_reviewed_at,at);assert.equal(rows[0].old_review_reason,null);assert.equal(rows[0].new_review_reason,'Initial reason');assert.equal(rows[0].new_record_id,'existing-record');assert(Number.isFinite(Date.parse(rows[0].changed_at)));
 db.prepare('UPDATE proposals SET status=status,reviewed_at=reviewed_at,review_reason=review_reason,record_id=record_id WHERE id=?').run(r.id);
 assert.equal(db.prepare('SELECT COUNT(*) n FROM proposal_reviews').get().n,1);
 db.prepare('UPDATE proposals SET status=?,reviewed_at=?,review_reason=?,record_id=NULL WHERE id=? AND status=?').run('declined','2026-10-25T12:00:00.000Z','Corrected reason',r.id,'accepted');
 rows=db.prepare('SELECT * FROM proposal_reviews ORDER BY id').all();assert.equal(rows.length,2);assert.equal(rows[1].old_status,'accepted');assert.equal(rows[1].new_status,'declined');assert.equal(rows[1].old_review_reason,'Initial reason');assert.equal(rows[1].new_review_reason,'Corrected reason');assert.equal(rows[1].old_record_id,'existing-record');assert.equal(rows[1].new_record_id,null);
 db.prepare('UPDATE proposals SET review_reason=NULL WHERE id=?').run(r.id);assert.equal(db.prepare('SELECT COUNT(*) n FROM proposal_reviews').get().n,3);
 db.prepare('UPDATE proposals SET review_reason=NULL WHERE id=?').run(r.id);assert.equal(db.prepare('SELECT COUNT(*) n FROM proposal_reviews').get().n,3);
 assert.deepEqual(db.prepare('SELECT card_json, fragment, card_hash, created_at FROM proposals WHERE id=?').get(r.id),card);assert.deepEqual(db.prepare('SELECT * FROM proposal_submissions').all(),submissions);
});
await test('invalid bounds/content/source and unavailable storage/rate never persist or leak internal errors',async()=>{
 const f=fixture();
 // Structural legacy reads must never become new human confirmation at intake.
 for(const change of [c=>c.unresolved=[{kind:'source_note',text:'Never change F.'}],c=>{c.method.value.operations=[{id:'reverse_row_runes'}];c.rules.wordBoundaries={status:'specified',value:'preserve'};c.rules.boundaryMode={status:'unspecified'};}]){const legacy=S.readCard(fragment());change(legacy);const encoded='#idea='+Buffer.from(JSON.stringify(legacy)).toString('base64url');assert.equal(C.serialize(S.readCard(encoded)),C.serialize(legacy));assert.equal((await f.handle(post(request({fragment:encoded})),f.env)).status,400);}
 for(const altered of [request({note:'x'.repeat(1201)}),request({sourceUrl:'https://127.0.0.1/x'}),request({sourceUrl:'http://10.0.0.1'}),request({sourceUrl:'https://user:pass@github.com/x'}),request({sourceUrl:'file:///private'}),request({sourceUrl:'https://localhost/x'}),request({sourceUrl:'https://example.test/x'}),request({fragment:'#idea=invalid'}),request({requestId:'not-a-uuid'}),request({originalPrompt:'forbidden'}),request({note:null}),request({sourceUrl:'x'.repeat(1501)})]){
  assert.equal((await f.handle(post(altered),f.env)).status,400);
 }
 assert.equal((await f.handle(post(request(),{'content-type':'text/plain'}),f.env)).status,400);
 assert.equal((await f.handle(post(request({fragment:fragment({method:C.field()})})),f.env)).status,400);
 assert.equal((await f.handle(post(request({sourceUrl:null})),f.env)).status,400);
 for(const originalIdea of [null,{},'x'.repeat(8001)])assert.equal((await f.handle(post(request({originalIdea})),f.env)).status,400);
 const accepted=fixture();assert.equal((await accepted.handle(post(request({originalIdea:'x'.repeat(8000)})),accepted.env)).status,200);
 assert.equal((await f.handle(post(request({note:'x'.repeat(33000)})),f.env)).status,400);
 const stream=new ReadableStream({start(controller){controller.enqueue(new TextEncoder().encode('x'.repeat(32001)));controller.close();}});
 const oversized=new Request('https://worker.example/proposals',{method:'POST',headers:{origin,'content-type':'application/json'},body:stream,duplex:'half'});
 assert.equal((await f.handle(oversized,f.env)).status,400);
 const denied={...f.env,PROPOSAL_LIMIT:{limit:async()=>({success:false})}};assert.equal((await f.handle(post(request()),denied)).status,429);assert.equal(f.db.reads,0);
 f.db.failBatch=true;const failed=await f.handle(post(request()),f.env);assert.equal(failed.status,503);assert(!JSON.stringify(await failed.json()).includes('Injected'));
 assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposals').get().n,0);assert.equal(f.db.sqlite.prepare('SELECT COUNT(*) n FROM proposal_submissions').get().n,0);
});
console.log('PASS '+count+' proposal groups using real node:sqlite transactions; no remote database, auth, deploy, inference or network calls.');
