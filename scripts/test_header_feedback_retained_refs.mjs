/* Verify the declarative adoption against complete old arrays; never generate target output. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import {resolveSavedProgramOutputs} from './retain_saved_programs.mjs';
import * as Collection from './retained_program_collection.mjs';
const root=new URL('../',import.meta.url),here=new URL('experiments/records/lp2-54-header-feedback/',root);
const json=async url=>JSON.parse(await readFile(url,'utf8'));
const [manifest,collection,plan,report,bundle]=await Promise.all(['saved-feedback-programs.json','retained-feedback-programs.json','plan.json','results.json'].map(name=>json(new URL(name,here))).concat(json(new URL('data/local-run-inputs.json',root))));
const sourceBytes=await readFile(new URL('results.json',here)),sourceSha=createHash('sha256').update(sourceBytes).digest('hex'),run=E.run;
let syntheticCalls=0;
E.run=task=>{assert(task.title.toLowerCase().includes('synthetic'),'Only independent synthetic controls may execute');syntheticCalls++;return run(task);};
try{
 const expectedCriterion={kind:'exact-prefix-set',openings:plan.first_plain_rune_candidates.map(label=>({id:'first-rune-'+label.toLowerCase(),values:[plan.labels.indexOf(label)]}))};
 assert.deepEqual(expectedCriterion,{kind:'exact-prefix-set',openings:[{id:'first-rune-a',values:[24]},{id:'first-rune-i',values:[10]},{id:'first-rune-o',values:[3]}]});
 assert.deepEqual(manifest.criterion,expectedCriterion);assert.deepEqual(collection.criterion,expectedCriterion);
 assert.deepEqual(manifest.alphabet,bundle.alphabet);assert.deepEqual(collection.alphabet,bundle.alphabet);
 const raw=await readFile(new URL('text/lp2-54.txt',root),'utf8');assert.equal(createHash('sha256').update(raw).digest('hex'),plan.input.sha256);
 assert.deepEqual(manifest.pages,[{id:'lp2-54',text:raw}]);assert.deepEqual(collection.pages,manifest.pages);
 assert.equal(Array.from(raw).filter(r=>plan.alphabet.includes(r)).length,232);
 const resolved=await resolveSavedProgramOutputs(manifest,{root:here}),handle=Collection.prepare(collection),seen=new Set();let values=0,matches=0;
 assert.equal(manifest.programs.length,58);assert.equal(collection.programs.length,58);assert.equal(report.cases.length,58);
 for(let i=0;i<report.cases.length;i++){
  const old=report.cases[i],author=manifest.programs[i],saved=collection.programs[i],mode={ciphertext_feedback:'ciphertext-autokey',plaintext_feedback:'plaintext-autokey'}[old.mode];
  assert(mode);assert(Number.isInteger(old.primer)&&old.primer>=0&&old.primer<29);assert(!seen.has(old.mode+'/'+old.primer));seen.add(old.mode+'/'+old.primer);
  assert.deepEqual(author.outputRefs,[{page:'lp2-54',path:'results.json',sha256:sourceSha,jsonPointer:'/cases/'+i+'/plain_indices'}]);assert(!Object.hasOwn(author,'outputs'));
  const steps=[{op:'keyed-shift',mode,key:[old.primer],direction:'subtract',reset:'page'}];assert.deepEqual(author.steps,steps);assert.deepEqual(saved.steps,steps);
  assert.equal(author.id,old.mode.replaceAll('_','-')+'-primer-'+String(old.primer).padStart(2,'0'));assert.equal(saved.id,author.id);assert.equal(saved.title,author.title);assert.equal(saved.createdAt,author.createdAt);
  assert(!/warning|language|readability|english/i.test(author.title));assert(author.title.includes('first rune A/I/O only'));
  assert.deepEqual(resolved.programs[i].outputs,[{page:'lp2-54',values:old.plain_indices}]);assert.deepEqual(saved.outputs,resolved.programs[i].outputs);assert.equal(old.plain_indices.length,232);values+=old.plain_indices.length;
  const retained=await Collection.hydrate(handle,saved.id);assert.equal(retained.task.taskId,saved.taskId);assert.deepEqual(retained.task.steps,steps);assert.deepEqual(retained.task.criterion,expectedCriterion);
  const expectedMatch=plan.first_plain_rune_candidates.includes(old.first_plain_rune);assert.equal(retained.run.result.matches[0].matched,expectedMatch);if(expectedMatch)matches++;
 }
 assert.equal(values,13456);assert.equal(matches,6);assert.equal(new Set(collection.programs.map(p=>p.taskId)).size,58);
 assert.equal(syntheticCalls,232,'Two independent controls are generated and revalidated for each retained program; no target program runs');
 console.log('PASS all 58 declarative references preserve 13,456 saved values, exact one-page feedback programs and only the six historical A/I/O first-rune highlights');
}finally{E.run=run;}
