/* Real local SQLite and injected CLI I/O only; never runs Wrangler or a model. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {parseArgs,listSQL,notesSQL,decisionSQL,invocation,remoteExecutor,run} from './review-proposals.mjs';

const db=new DatabaseSync(':memory:');
db.exec(readFileSync(new URL('./migrations/0001_proposals.sql',import.meta.url),'utf8'));
db.exec(readFileSync(new URL('./migrations/0002_proposal_reviews.sql',import.meta.url),'utf8'));
db.exec(readFileSync(new URL('./migrations/0003_original_idea.sql',import.meta.url),'utf8'));
const cardJson=JSON.stringify({outcome:'measure',method:{operations:[{id:'reverse_row_runes'}]},scope:{pages:['lp2-15','lp2-17']},exact:"O'Brien's supplied wording"});
const hash=createHash('sha256').update(cardJson).digest('hex'),id='p_'+hash;
const otherJson='{"exact":"another immutable card"}',otherHash=createHash('sha256').update(otherJson).digest('hex'),otherId='p_'+otherHash;
const created='2026-10-24T12:00:00.000Z',reviewed='2026-10-24T13:00:00.000Z';
db.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,hash,cardJson,'#idea=canonical',created);
db.prepare('INSERT INTO proposals(id,card_hash,card_json,fragment,created_at,status,reviewed_at) VALUES(?,?,?,?,?,?,?)').run(otherId,otherHash,otherJson,'#idea=other',created,'declined',reviewed);
const submit=db.prepare('INSERT INTO proposal_submissions(request_id,proposal_id,request_hash,note,source_url,received_at,received_day,original_idea) VALUES(?,?,?,?,?,?,?,?)');
const first='00000000-0000-4000-8000-000000000001',second='00000000-0000-4000-8000-000000000002',later='00000000-0000-4000-8000-000000000003';
const originalIdea='Original idea wording: keep this separately from the standardized card.';
submit.run(first,id,'a'.repeat(64),'First note: preserve it.','https://example.org/source',created,'2026-10-24',originalIdea);
submit.run(second,id,'b'.repeat(64),"Second note with 'quotes'; do not change it.",'',created,'2026-10-24','');
submit.run(later,otherId,'c'.repeat(64),'Later contribution on a declined card.','','2026-10-24T14:00:00.000Z','2026-10-24','');
function execute(sql){
 // Generated list SQL has exactly two SELECTs. Mutations remain one atomic
 // UPDATE RETURNING; no splitting of a quoted decision reason is performed.
 const statements=sql.startsWith('UPDATE')?[sql]:sql.trim().split(/;\s*\n(?=SELECT)/);
 return statements.map(statement=>db.prepare(statement).all());
}
const json=value=>JSON.parse(JSON.stringify(value));
const published=new Set(JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8')).records.filter(r=>r.status==='published').map(r=>r.id));
const recordId='lp2-fibonacci-openings';assert(published.has(recordId));

for(const args of [[],['--help']])assert.equal(parseArgs(args).command,'help');
for(const args of [
 ['list'],['list','--local','--remote'],['list','--local','--status','unknown'],
 ['list','--local','--limit','101'],['list','--local','--limit','1; DROP TABLE proposals'],
 ['export','--local'],['show','--local'],['decide','--local','--id',id,'--status','planned','--expected-status','pending','--reason','x'],
 ['decide','--local','--id',id,'--status','accepted','--reason','x'],
 ['decide','--local','--id','p_123','--status','accepted','--expected-status','pending','--reason','x'],
 ['list','--remote','--persist-to','state'],['list','--local','--unknown','x'],['list','--local','--limit','2','--limit','3']
])assert.throws(()=>parseArgs(args),undefined,args.join(' '));
assert.equal(parseArgs(['list','--local']).database,'liberpedia-proposals-local');
assert.equal(parseArgs(['list','--remote']).database,'liberpedia-proposals');
const argvSQL="SELECT 'O''Brien; $(not-a-shell) `literal`' AS value;\nSELECT 2;";
const call=invocation(join(tmpdir(),'installed wrangler.js'),argvSQL,'liberpedia-proposals-local',{local:true,'persist-to':join(tmpdir(),'state')});
assert.equal(call.shell,false);assert.equal(call.command,process.execPath);assert(call.args.includes('--local'));assert(!call.args.includes('--remote'));
assert.equal(call.args[call.args.indexOf('--command')+1],argvSQL);assert(!call.args.includes('--file'));
assert.throws(()=>invocation(join(tmpdir(),'installed wrangler.js'),'SELECT\0 1;','liberpedia-proposals',{remote:true}),/NUL/);
for(const mode of ['local','remote']){
 const options=parseArgs(['show','--'+mode,'--id',id,'--wrangler',fileURLToPath(import.meta.url)]);
 let captured;
 const executor=remoteExecutor(options,{spawn:(command,args,settings)=>{
  captured={command,args,settings};return {status:0,stdout:JSON.stringify([{success:true,results:[{value:"O'Brien; $(not-a-shell) `literal`"}]},{success:true,results:[{value:2}]}])};
 }});
 assert.deepEqual(executor(argvSQL),[[{value:"O'Brien; $(not-a-shell) `literal`"}],[{value:2}]]);
 assert.equal(captured.command,process.execPath);assert.equal(captured.settings.shell,false);
 assert(captured.args.includes('--'+mode));assert(!captured.args.includes('--file'));
 assert.equal(captured.args[captured.args.indexOf('--command')+1],argvSQL,'Whole multi-statement SQL is one literal argv value');
 assert.equal(captured.settings.env.WRANGLER_SEND_METRICS,'false');assert.equal(captured.settings.timeout,60000);
 for(const result of [{status:0,stdout:'Import progress\n[]'},{status:0,stdout:'[{"success":false,"results":[]}]'},{status:1,stdout:'[]'},{error:Error('timeout')}]){
  assert.throws(()=>remoteExecutor(options,{spawn:()=>result})(argvSQL));
 }
}

const originalCard=db.prepare('SELECT card_json,fragment FROM proposals WHERE id=?').get(id);
const originalNotes=json(db.prepare('SELECT * FROM proposal_submissions ORDER BY request_id').all());
let printed=[];
await run(parseArgs(['list','--local']),{execute,stdout:value=>printed.push(value),now:()=>created});
const listing=JSON.parse(printed[0]);assert.equal(listing.counts.matching_cards,1);assert.equal(listing.counts.matching_submissions,2);
assert.equal(listing.cards.length,1);assert.equal(listing.cards[0].card_json,cardJson);assert.deepEqual(listing.cards[0].card.scope.pages,['lp2-15','lp2-17']);
assert.equal(listing.cards[0].submission_count,2,'Two submissions remain one card');

let written,writeOptions;
await run(parseArgs(['export','--local','--id',id,'--out','offline.json','--note-limit','1']),{
 execute,stdout(){},now:()=>created,write:(path,content,options)=>{written=JSON.parse(content);writeOptions=options;}});
assert.equal(writeOptions.flag,'wx');assert.equal(written.cards[0].card_json,cardJson);assert.equal(written.submissions.length,1);
assert.equal(written.submissions[0].original_idea,originalIdea);
assert.equal(written.next_after_note,first);assert.equal(written.notes_complete_for_selection,false);
const notePage=execute(notesSQL([id],{'note-limit':1,'after-note':first}))[0];assert.equal(notePage[0].request_id,second);
const newNotes=execute(listSQL(parseArgs(['list','--local','--new-notes'])))[1];
assert.equal(newNotes.length,1);assert.equal(newNotes[0].id,otherId);assert.equal(newNotes[0].unreviewed_submission_count,1);

const reason="Not a solve: O'Brien's note; '); UPDATE proposals SET card_json='tampered'; --";
const decision=parseArgs(['decide','--local','--id',id,'--status','accepted','--expected-status','pending','--reason',reason,'--record',recordId]);
assert.throws(()=>decisionSQL({...decision,record:'not-an-existing-record'},published,reviewed));
const sql=decisionSQL(decision,published,reviewed);
assert.match(sql,/^UPDATE proposals SET status=/);
const firstDecision=execute(sql)[0];assert.equal(firstDecision.length,1);assert.equal(firstDecision[0].review_reason,reason);assert.equal(firstDecision[0].record_id,recordId);
assert.equal(execute(sql)[0].length,0,'A stale expected-status mutation changes nothing');
assert.deepEqual(db.prepare('SELECT card_json,fragment FROM proposals WHERE id=?').get(id),originalCard);
assert.deepEqual(json(db.prepare('SELECT * FROM proposal_submissions ORDER BY request_id').all()),originalNotes);
await assert.rejects(run(decision,{execute,stdout(){},now:()=>reviewed}),/No decision confirmed/);
let executions=0;
await run({...decision,'dry-run':true},{execute(){executions++;throw Error('Must not run');},stdout(){},now:()=>reviewed});
assert.equal(executions,0);
assert.equal(execute(listSQL(parseArgs(['list','--local','--status','accepted'])))[1][0].id,id);
assert.equal(execute(listSQL(parseArgs(['show','--local','--id',id])))[1][0].status,'accepted');
const correction=parseArgs(['decide','--local','--id',id,'--status','declined','--expected-status','accepted','--reason','Reviewed correction: missing fixed inputs.']);
assert.equal(execute(decisionSQL(correction,published,'2026-10-24T15:00:00.000Z'))[0][0].status,'declined');
printed=[];
await run(parseArgs(['show','--local','--id',id,'--history-limit','1']),{execute,stdout:value=>printed.push(value),now:()=>reviewed});
const shown=JSON.parse(printed[0]);assert.equal(shown.cards[0].status,'declined');
assert.equal(shown.review_history_count,2);assert.equal(shown.review_history.length,1);
assert.equal(shown.review_history[0].old_status,'accepted');assert.equal(shown.review_history[0].new_status,'declined');
assert.equal(shown.review_history[0].old_review_reason,reason);assert.equal(shown.review_history[0].new_record_id,recordId,'Omitting --record preserves an existing link');
assert.equal(shown.next_before_review,shown.review_history[0].id);
assert.equal(shown.submissions.length,2);assert.equal(shown.cards[0].card_json,cardJson);
assert.equal(shown.submissions[0].original_idea,originalIdea,'Original source wording survives decisions and exports unchanged');
assert.deepEqual(json(db.prepare('SELECT * FROM proposal_submissions ORDER BY request_id').all()),originalNotes);
db.close();
console.log('PASS: explicit modes/IDs/statuses, bounded exact-card exports/note/history cursors, distinct counts, later-note discovery, safe argv/SQL quoting, published links, immutable cards/notes, full review transitions and atomic stale-decision conflict. SQLite only; no Wrangler, network or AI.');
