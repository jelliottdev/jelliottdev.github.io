/* Offline declarative extraction tests: invented saved arrays only. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,mkdir,rm,symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import {resolveSavedProgramOutputs,prepareSavedPrograms,REFERENCE_LIMITS} from './retain_saved_programs.mjs';
const alphabet=JSON.parse(await readFile(new URL('../data/local-run-inputs.json',import.meta.url))).alphabet;
const at='2026-10-27T00:00:00.000Z',sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const data={cases:[{plain:[0,1,2,3]},{plain:[3,2,1,0]}],empty:[],escaped:{'runes/~saved':[0,1,2,3]}};
const literal=()=>({alphabet,pages:[{id:'lp2-00',text:alphabet.slice(0,4).map(x=>x.rune).join('')},{id:'lp2-01',text:''}],criterion:{kind:'exact-prefix',values:[0,1]},programs:[{id:'invented-baseline',title:'Invented saved baseline',steps:[],createdAt:at,outputs:[{page:'lp2-00',values:[0,1,2,3]},{page:'lp2-01',values:[]}]},{id:'invented-reverse',title:'Invented saved reversal',steps:[{op:'reverse',unit:'page'}],createdAt:at,outputs:[{page:'lp2-00',values:[3,2,1,0]},{page:'lp2-01',values:[]}]}]});
const bytes=JSON.stringify(data),digest=sha(bytes);
function manifest(){const v=literal();v.programs.forEach((p,i)=>{delete p.outputs;p.outputRefs=[{page:'lp2-00',path:'results.json',sha256:digest,jsonPointer:'/cases/'+i+'/plain'},{page:'lp2-01',path:'results.json',sha256:digest,jsonPointer:'/empty'}];});return v;}
const temp=await mkdtemp(join(tmpdir(),'liberpedia-output-refs-')),root=join(temp,'record');await mkdir(root);await writeFile(join(root,'results.json'),bytes);
let groups=0;const test=async(name,fn)=>{await fn();groups++;console.log('PASS '+name);};
try{
await test('pinned references resolve all exact values and empty saved cases to the unchanged literal importer',async()=>{
 const v=manifest(),before=E.stable(v),resolved=await resolveSavedProgramOutputs(v,{root});assert.deepEqual(resolved,literal());assert.equal(E.stable(v),before);
 assert.deepEqual(await prepareSavedPrograms(resolved),await prepareSavedPrograms(literal()));
 const mixed=manifest();mixed.programs[1]=literal().programs[1];assert.deepEqual(await resolveSavedProgramOutputs(mixed,{root}),literal());
 const escaped=manifest();escaped.programs[0].outputRefs[0].jsonPointer='/escaped/runes~1~0saved';assert.deepEqual(await resolveSavedProgramOutputs(escaped,{root}),literal());
 resolved.programs[0].outputs[0].values[0]=28;assert.equal((await resolveSavedProgramOutputs(v,{root})).programs[0].outputs[0].values[0],0);
});
await test('exact schema, paths, raw pins, pointer syntax and page order fail closed before controls',async()=>{
 const edits=[v=>v.programs[0].outputs=[],v=>v.programs[0].outputRefs[0].extra=true,v=>v.programs[0].outputRefs.reverse(),v=>v.programs[0].outputRefs.pop(),v=>v.programs[0].outputRefs[0].sha256='0'.repeat(64),v=>v.programs[0].outputRefs[1].sha256='1'.repeat(64),v=>v.programs[0].outputRefs[0].jsonPointer=['/empty'],v=>v.programs[0].outputRefs[0].jsonPointer='/cases/00/plain',v=>v.programs[0].outputRefs[0].jsonPointer='/cases/9/plain',v=>v.programs[0].outputRefs[0].jsonPointer='/cases/~2/plain',v=>v.programs[0].outputRefs[0].jsonPointer='/cases/0/plain/0',v=>v.programs[0].outputRefs[0].jsonPointer='${cases[0]}',v=>v.programs[0].outputRefs[0].jsonPointer='/'+Array(25).fill('a').join('/'),v=>v.programs[0].outputRefs[0].jsonPointer='/'+ 'a'.repeat(512),v=>v.programs=Array(129).fill(v.programs[0])];
 for(const path of ['../results.json','/results.json','https://example.org/results.json','nested/../results.json','nested\\results.json','nested//results.json','results.txt','%2e%2e/results.json'])edits.push(v=>v.programs[0].outputRefs[0].path=path);
 const run=E.run;E.run=()=>assert.fail('Invalid references must not execute even controls');try{for(const edit of edits){const v=manifest();edit(v);await assert.rejects(resolveSavedProgramOutputs(v,{root}));}}finally{E.run=run;}
});
await test('selected arrays must be complete bounded numeric values; source JSON must have unique keys and valid UTF8',async()=>{
 for(const raw of ['{"x":[0,1,2,3],"x":[0,1,2,3]}','{"x":[0,1,2,3],"\\u0078":[0,1,2,3]}',JSON.stringify({x:[0,1,2]}),JSON.stringify({x:[0,1,2,29]}),JSON.stringify({x:[0,1,2,1.5]}),JSON.stringify({x:{0:0,1:1,2:2,3:3}}),JSON.stringify({x:[0,1,2,3],deep:Array.from({length:1},()=>0)}).replace('"deep":[0]','"deep":'+ '['.repeat(25)+'0'+']'.repeat(25)),Buffer.from([0xff,0xfe])]){
  await writeFile(join(root,'invalid.json'),raw);const v=manifest();v.programs=v.programs.slice(0,1);v.pages=v.pages.slice(0,1);v.programs[0].outputRefs=[{page:'lp2-00',path:'invalid.json',sha256:sha(raw),jsonPointer:'/x'}];await assert.rejects(resolveSavedProgramOutputs(v,{root}));
 }
 // A wrong raw pin rejects before parsing even when the selected value is identical.
 await writeFile(join(root,'results.json'),bytes+'\n');await assert.rejects(resolveSavedProgramOutputs(manifest(),{root}),/raw source hash/);await writeFile(join(root,'results.json'),bytes);
});
await test('all source bytes and selected output expansion retain the existing aggregate budgets',async()=>{
 await writeFile(join(root,'large.json'),' '.repeat(REFERENCE_LIMITS.bytes+1));let v=manifest();v.programs[0].outputRefs[0].path='large.json';await assert.rejects(resolveSavedProgramOutputs(v,{root}),/byte bound/);
 const raw=JSON.stringify({plain:[0,1,2,3],empty:[],padding:'x'.repeat(5*1024*1024)});await writeFile(join(root,'a.json'),raw);await writeFile(join(root,'b.json'),raw);v=manifest();v.programs=v.programs.slice(0,1);v.programs[0].outputRefs=[{page:'lp2-00',path:'a.json',sha256:sha(raw),jsonPointer:'/plain'},{page:'lp2-01',path:'b.json',sha256:sha(raw),jsonPointer:'/empty'}];await assert.rejects(resolveSavedProgramOutputs(v,{root}),/byte bound/);
 const amplified=JSON.stringify({plain:Array(25000).fill(0)});await writeFile(join(root,'amplified.json'),amplified);v=literal();v.pages=[{id:'lp2-00',text:alphabet[0].rune.repeat(25000)}];v.programs=Array.from({length:128},(_,i)=>({id:'invented-'+i,title:'Invented saved repeated array',steps:[],createdAt:at,outputRefs:[{page:'lp2-00',path:'amplified.json',sha256:sha(amplified),jsonPointer:'/plain'}]}));await assert.rejects(resolveSavedProgramOutputs(v,{root}),/node bound|byte bound/);
});
await test('source symlinks, directory symlinks and mutation of caller objects cannot retarget the import',async()=>{
 const outside=join(temp,'outside.json');await writeFile(outside,bytes);
 for(const [link,target,type] of [[join(root,'link.json'),outside,'file'],[join(root,'nested'),temp,'junction']]){
  try{await symlink(target,link,type);}catch(error){if(process.platform==='win32'&&error.code==='EPERM')continue;throw error;}
  const v=manifest();v.programs[0].outputRefs[0].path=type==='file'?'link.json':'nested/outside.json';await assert.rejects(resolveSavedProgramOutputs(v,{root}),/symbolic links/);
 }
 const v=manifest(),pending=resolveSavedProgramOutputs(v,{root});v.programs[0].outputRefs[0].path='../outside.json';v.programs[0].steps=[{op:'reverse',unit:'page'}];assert.deepEqual(await pending,literal());
 let calls=0;const getter=manifest();Object.defineProperty(getter.programs[0].outputRefs[0],'path',{enumerable:true,get(){calls++;return 'results.json';}});await assert.rejects(resolveSavedProgramOutputs(getter,{root}));assert.equal(calls,0);
});
await test('CLI uses the input file directory, refuses overwrite and writes nothing after any invalid reference',async()=>{
 const input=join(root,'saved.json'),output=join(root,'retained.json'),script=fileURLToPath(new URL('./retain_saved_programs.mjs',import.meta.url));await writeFile(input,JSON.stringify(manifest()));
 const cli=()=>spawnSync(process.execPath,[script,'--input',input,'--output',output],{cwd:temp,encoding:'utf8'});let run=cli();assert.equal(run.status,0,run.stderr);const old=await readFile(output);assert.equal(JSON.parse(old).programs.length,2);assert.notEqual(cli().status,0);assert.deepEqual(await readFile(output),old);
 await rm(output);const v=manifest();v.programs[1].outputRefs[0].sha256='0'.repeat(64);await writeFile(input,JSON.stringify(v));assert.notEqual(cli().status,0);await assert.rejects(readFile(output),/ENOENT/);
});
}finally{assert.equal(dirname(resolve(temp)),resolve(tmpdir()));assert(resolve(temp).includes('liberpedia-output-refs-'));await rm(temp,{recursive:true,force:true});}
console.log(groups+' stored-output reference groups passed; invented vectors only, no hosted writes or new searches.');
