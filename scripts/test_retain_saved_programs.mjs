import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import {prepareSavedPrograms,parseSavedPrograms} from './retain_saved_programs.mjs';
import * as Collection from './retained_program_collection.mjs';
const alphabet=JSON.parse(await readFile(new URL('../data/local-run-inputs.json',import.meta.url))).alphabet;
const at='2026-10-27T00:00:00.000Z',schema=()=>({alphabet,pages:[{id:'lp2-00',text:alphabet.slice(0,2).map(r=>r.rune).join('')+' '+alphabet.slice(2,4).map(r=>r.rune).join('')+'\n'+alphabet.slice(4,6).map(r=>r.rune).join('')},{id:'lp2-01',text:''}],criterion:{kind:'exact-prefix-set',openings:[{id:'invented-forward',values:[0,1]},{id:'invented-backward',values:[5,4]}]},programs:[{id:'invented-baseline',title:'Invented original order',steps:[],createdAt:at,outputs:[{page:'lp2-00',values:[0,1,2,3,4,5]},{page:'lp2-01',values:[]}]},{id:'invented-reversal',title:'Invented page reversal',steps:[{op:'reverse',unit:'page'}],createdAt:at,outputs:[{page:'lp2-00',values:[5,4,3,2,1,0]},{page:'lp2-01',values:[]}]}]});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('one input imports all supplied programs and preserves exact saved empty cases and criteria',async()=>{
 const input=schema(),before=E.stable(input),collection=await prepareSavedPrograms(input),handle=Collection.prepare(collection);
 assert.equal(collection.programs.length,2);assert.equal(E.stable(input),before);assert.deepEqual(collection.criterion,input.criterion);
 for(const p of collection.programs){const retained=await Collection.hydrate(handle,p.id);assert.equal(retained.run.createdAt,at);assert.equal(retained.task.taskId,p.taskId);assert.equal(retained.run.result.transformed[1].text,'');assert.deepEqual(p.outputs,input.programs.find(x=>x.id===p.id).outputs);assert.equal(retained.run.result.matches[0].matched,true);}
 assert.deepEqual(collection.programs[0].steps,[]);
});
await test('missing wrong reordered duplicate and unknown outputs cannot be filled from the program',async()=>{
 for(const edit of [v=>v.programs[0].outputs.pop(),v=>v.programs[0].outputs[0].values.pop(),v=>v.programs[0].outputs[0].values[0]=28,v=>v.programs[0].outputs.reverse(),v=>v.programs.push(structuredClone(v.programs[0])),v=>v.programs[0].outputs[0].extra=true,v=>v.programs[0].createdAt='yesterday',v=>v.programs[0].result={},v=>v.extra=true]){const v=schema();edit(v);await assert.rejects(prepareSavedPrograms(v));}
});
await test('untrusted objects are detached without running getters and JSON rejects repeated fields',async()=>{
 let calls=0;const input=schema();Object.defineProperty(input.programs[0],'title',{enumerable:true,get(){calls++;return 'injected';}});await assert.rejects(prepareSavedPrograms(input));assert.equal(calls,0);
 const value=schema(),pending=prepareSavedPrograms(value);value.programs[0].outputs[0].values[0]=28;const saved=await pending;assert.equal(saved.programs[0].outputs[0].values[0],0);
 assert.throws(()=>parseSavedPrograms(new TextEncoder().encode('{"programs":[],"programs":[]}')),/Repeated/);
 assert.throws(()=>parseSavedPrograms(new TextEncoder().encode('{"programs":[],"\\u0070rograms":[]}')),/Repeated/);
 assert.deepEqual(parseSavedPrograms(new TextEncoder().encode(E.stable(schema()))),schema());
});
await test('CLI writes one retained collection exclusively and invalid saved input writes nothing',async()=>{
 const temp=await mkdtemp(join(tmpdir(),'liberpedia-saved-batch-'));try{
 const input=join(temp,'saved.json'),output=join(temp,'retained.json'),script=fileURLToPath(new URL('./retain_saved_programs.mjs',import.meta.url));await writeFile(input,E.stable(schema()));
 const run=()=>spawnSync(process.execPath,[script,'--input',input,'--output',output],{encoding:'utf8'});assert.equal(run().status,0);const before=await readFile(output);assert.equal(JSON.parse(before).programs.length,2);assert.notEqual(run().status,0);assert.deepEqual(await readFile(output),before);
 await rm(output);const bad=schema();bad.programs[0].outputs=[];await writeFile(input,E.stable(bad));assert.notEqual(run().status,0);await assert.rejects(readFile(output),/ENOENT/);
 }finally{assert.equal(dirname(resolve(temp)),resolve(tmpdir()));assert(join(temp).includes('liberpedia-saved-batch-'));await rm(temp,{recursive:true,force:true});}
});
console.log(groups+' saved program batch groups passed; invented inputs only, no hosted writes or searches.');
