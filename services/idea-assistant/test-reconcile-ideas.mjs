/* Offline fixtures in OS temporary storage only. No Wrangler/model/network. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdtempSync,unlinkSync,rmdirSync,existsSync,symlinkSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';
import {parseArgs,reconcile,render,run,privateOutput} from './reconcile-ideas.mjs';
const sha=s=>createHash('sha256').update(s).digest('hex'),clone=x=>JSON.parse(JSON.stringify(x));
const known=value=>C.field('specified',value),stamp='2026-10-24T12:00:00.000Z';
function make(pages=['lp2-15'],overrides={}){
 const confirmed=C.confirm(C.createDraft({source:{text:'Original wording'},aim:known({outcomeId:'decipher',detail:'PRIVATE OUTCOME SHOULD NOT RANK'}),method:known({operations:[{id:'vigenere',key:'FOO',reset:'page'}]}),scope:known({pages}),...overrides}),{id:'test',at:stamp});
 const card=S.cardData(confirmed),card_json=C.serialize(card),card_hash=sha(card_json);
 return {id:'p_'+card_hash,card_hash,card_json,card,fragment:S.encode(confirmed),status:'pending',created_at:stamp,reviewed_at:null,review_reason:null,record_id:null,submission_count:1};
}
function submission(row,n=1){return {request_id:'00000000-0000-4000-8000-'+String(n).padStart(12,'0'),proposal_id:row.id,original_idea:'PRIVATE ORIGINAL ![remote](https://example.org/pixel) <script>alert(1)</script>',note:'A distinct contribution '+n,source_url:'https://example.org/private',received_at:stamp,received_day:stamp.slice(0,10)};}
function exported(cards=[make()]){return {schema:'liberpedia-proposal-review-export-v1',read_started_at:stamp,read_finished_at:stamp,counts:{matching_cards:cards.length,matching_submissions:cards.length,selected_cards:cards.length,selected_submissions:cards.length},cards,submissions:cards.map((c,i)=>submission(c,i+1)),notes_complete_for_selection:true,next_after:null,next_after_note:null,filter:{status:'pending'}};}
const registry=JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8'));
const evidence={inputHash:'a'.repeat(64),registryHash:'b'.repeat(64),generatedAt:stamp};
let tests=0;function test(name,fn){fn();tests++;console.log('PASS '+name);}
test('CLI explicit inputs, no modes/network, no unknown or duplicate options',()=>{
 assert(parseArgs([]).help);assert.throws(()=>parseArgs(['--input','x']));assert.throws(()=>parseArgs(['--input','x','--out','x','--out','y']));assert.throws(()=>parseArgs(['--input','x','--out','y','--remote','true']));
 assert(parseArgs(['--input','x','--out','y']).registry.endsWith('experiments.json'));
});
test('all contributions kept separately from exact card and zero tasks/results',()=>{
 const data=exported();data.cards[0].submission_count=2;data.submissions.push(submission(data.cards[0],2));data.counts.selected_submissions=2;data.counts.matching_submissions=2;
 const before=C.serialize(data),report=reconcile(data,registry,evidence);
 assert.equal(report.groups.length,1);assert.equal(report.groups[0].contributions.length,2);assert.equal(report.counts.saved_incoming_cards,1);assert.equal(report.counts.contributions,2);
 assert.equal(report.counts.pending_tasks_created,0);assert.equal(report.counts.experiments_executed,0);assert.equal(report.groups[0].card_json,data.cards[0].card_json);assert.equal(C.serialize(data),before);
 assert.equal(report.snapshot.input_sha256,evidence.inputHash);assert.equal(report.groups[0].coverage,'not_assessed');
});
test('page variants preserve directional delta, ordered methods/rules and whole candidate records',()=>{
 const report=reconcile(exported([make(),make(['lp2-15','lp2-17'])]),registry,evidence);
 assert.equal(report.relations[0].relationship,'page_scope_variant');assert.deepEqual(report.relations[0].pageDelta,{added:['lp2-17'],removed:[]});
 const group=report.groups[0];assert(group.retrieval.query.includes('FOO'));assert(!group.retrieval.query.includes('PRIVATE'));assert(!group.retrieval.query.includes('OUTCOME'));assert(!group.retrieval.query.includes('lp2'));
 assert(group.candidates.length>0);for(const candidate of group.candidates){assert.deepEqual(candidate.record,registry.records.find(r=>r.id===candidate.id));assert(candidate.record.scope);assert.equal(candidate.record_sha256,sha(C.serialize(candidate.record)));}
 const changed=make(['lp2-15'],{rules:{searchBounds:C.field('unrestricted')}});assert.equal(reconcile(exported([make(),changed]),registry,evidence).relations[0].relationship,'different_specification');
});
test('missing methods/no matches remain needs comparison or clarification, never new',()=>{
 const absent=reconcile(exported([make(['lp2-15'],{method:C.field()})]),registry,evidence);assert.equal(absent.groups[0].retrieval.state,'needs_clarification');assert.equal(absent.groups[0].candidates.length,0);
 const empty={schema:'liberpedia-experiments-v1',records:[]};const report=reconcile(exported(),empty,evidence);assert.equal(report.groups[0].retrieval.state,'needs_comparison');assert.equal(report.groups[0].novelty,'not_assessed');
});
test('different original wording and generic/custom outcomes cannot change method ranking',()=>{
 const first=exported(),second=exported([make(['lp2-15'],{aim:known({outcomeId:'measure',detail:'gematria constellation Fibonacci language'})})]);second.submissions[0].original_idea='Lag six modulo 28 PRIVATE DO NOT RANK';
 const a=reconcile(first,registry,evidence).groups[0],b=reconcile(second,registry,evidence).groups[0];
 assert.equal(a.retrieval.query,b.retrieval.query);assert.deepEqual(a.candidates.map(c=>c.id),b.candidates.map(c=>c.id));assert.notDeepEqual(a.card.outcome,b.card.outcome);
});
test('partial, stale, malformed, duplicated and missing immutable information fails closed',()=>{
 const checks=[d=>d.notes_complete_for_selection=false,d=>d.next_after_note='cursor',d=>d.submissions=[],d=>delete d.submissions[0].original_idea,d=>d.submissions.push(clone(d.submissions[0])),d=>d.submissions[0].proposal_id='missing',d=>d.cards[0].card_hash='0'.repeat(64),d=>d.cards[0].id='p_stale',d=>d.cards[0].card.scope.value.pages=['lp2-17'],d=>d.cards[0].fragment=make(['lp2-17']).fragment,d=>d.cards[0].record_id='stale-record',d=>d.cards[0].status='planned',d=>d.submissions[0].note='x'.repeat(1201),d=>d.counts.selected_submissions=2,d=>d.cards.push(clone(d.cards[0])),d=>d.submissions[0].received_day='2020-01-01'];
 for(const change of checks){const data=exported();change(data);assert.throws(()=>reconcile(data,registry,evidence));}
 const noncanonical=exported();noncanonical.cards[0].card_json=JSON.stringify(noncanonical.cards[0].card,null,2);noncanonical.cards[0].card_hash=sha(noncanonical.cards[0].card_json);noncanonical.cards[0].id='p_'+noncanonical.cards[0].card_hash;assert.throws(()=>reconcile(noncanonical,registry,evidence),/canonical/);
 const duplicate=clone(registry);duplicate.records.push(duplicate.records[0]);assert.throws(()=>reconcile(exported(),duplicate,evidence),/duplicate/);
 const unsafe={schema:registry.schema,records:[{id:'bad](https://example.org)',status:'published'}]};assert.throws(()=>reconcile(exported(),unsafe,evidence));
});
test('owner report renders supplied Markdown/HTML/URLs as inert escaped text',()=>{
 const report=reconcile(exported(),registry,evidence),md=render(report);assert(md.includes('&lt;script&gt;'));assert(!md.includes('<script>'));assert(md.includes('<pre>'));assert(md.includes('![remote]'),'Literal Markdown remains inside inert HTML pre block');
 assert(md.includes('[Open published record](https://jelliottdev.github.io/#/experiments/'));assert(!md.includes('src="https://'));
});
test('bounded card-page export is labelled and original matching counts preserved',()=>{
 const data=exported();data.counts.matching_cards=42;data.counts.matching_submissions=50;data.next_after=data.cards[0].id;
 const report=reconcile(data,registry,evidence);assert.equal(report.counts.saved_incoming_cards,1);assert.equal(report.snapshot.matching_counts.matching_cards,42);assert.equal(report.snapshot.next_after,data.next_after);
});
test('actual private files, byte snapshots, refusal to overwrite or write repository outputs',()=>{
 const temp=mkdtempSync(join(tmpdir(),'liberpedia-private-reconcile-')),input=join(temp,'input.json'),out=join(temp,'owner-review');
 writeFileSync(input,JSON.stringify(exported()),'utf8');
 try{
  const result=run(parseArgs(['--input',input,'--out',out]));assert.equal(result.counts.saved_incoming_cards,1);
  const report=JSON.parse(readFileSync(join(out,'queue-review.json'),'utf8'));assert.equal(report.snapshot.input_sha256,sha(readFileSync(input)));assert.equal(report.snapshot.registry_sha256,sha(readFileSync(new URL('../../data/experiments.json',import.meta.url))));
  assert(report.snapshot.code_sha256['idea-relations.mjs']);assert.throws(()=>run(parseArgs(['--input',input,'--out',out])),/new private/);
  assert.throws(()=>privateOutput(fileURLToPath(new URL('../../data/no-private-test-output',import.meta.url))),/outside/);
  const redirected=join(temp,'redirected-public');symlinkSync(fileURLToPath(new URL('../../',import.meta.url)),redirected,process.platform==='win32'?'junction':'dir');
  try{assert.throws(()=>privateOutput(join(redirected,'no-private-test-output')),/outside/);}finally{if(process.platform==='win32')rmdirSync(redirected);else unlinkSync(redirected);}
  const tooBig=join(temp,'oversize.json');writeFileSync(tooBig,' '.repeat(8*1024*1024+1));assert.throws(()=>run(parseArgs(['--input',tooBig,'--out',join(temp,'must-not-exist')])),/byte limit/);assert(!existsSync(join(temp,'must-not-exist')));unlinkSync(tooBig);
 }finally{for(const name of ['queue-review.json','queue-review.md'])if(existsSync(join(out,name)))unlinkSync(join(out,name));if(existsSync(out))rmdirSync(out);unlinkSync(input);rmdirSync(temp);}
});
console.log('PASS '+tests+' offline reconciliation groups; no remote/model calls or public fixture outputs');
