'use strict';
// Simulated Git-index bytes only; the actual repository index is never changed.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const source=fs.readFileSync('scripts/check_staged_runtime_sources.cjs','utf8');
const names=['local-run-package.js','factored-finite-search-package.js','tools/verify_controls.py','tools/verify_subset_controls.py','tools/verify_plan_controls.py','tools/verify_authored_language.py','tools/research_runner.py','tools/verify_finite_search.py','tools/verify_factored_finite_search.py','tools/language-model.json','declarative-run-package.js','local-experiment.js','finite-json.js','declarative-rune-program.js','declarative-plan-controls.js','language-score.js','language-model-data.js'];
// These maintained text sources publish as LF; mimic Git's text normalization.
const files=new Map(names.map(name=>[name,Buffer.from(fs.readFileSync(name,'utf8').replace(/\r\n/g,'\n'))]));
function check(changed){const reads=[],messages=[];vm.runInNewContext(source,{console:{log:value=>messages.push(value)},require:name=>{if(name==='node:crypto')return crypto;assert.equal(name,'node:child_process');return {execFileSync(command,args,options){assert.equal(command,'git');assert.equal(args[0],'show');assert(args[1].startsWith(':'));const name=args[1].slice(1);assert(files.has(name),'Unexpected runtime source '+name);const bytes=changed?.(name,files.get(name))||files.get(name);assert(options.maxBuffer>=bytes.length,'Git source read must fit the actual pinned model');reads.push(name);return bytes;}};}});return {reads,messages};}
const value=check();assert.deepEqual(new Set(value.reads),new Set(names));assert(value.messages[0].includes('17 runtime source pins'));
for(const name of names.filter(name=>!name.endsWith('-package.js')))assert.throws(()=>check((actual,bytes)=>actual===name?Buffer.concat([bytes,Buffer.from('\n')]):bytes),/Staged runtime source pin differs/,'Every pinned source mutation must fail: '+name);
for(const name of ['local-run-package.js','factored-finite-search-package.js','declarative-run-package.js'])assert.throws(()=>check((actual,bytes)=>actual===name?Buffer.from(bytes.toString('utf8').replace(/[a-f0-9]{64}/g,'0'.repeat(64))):bytes),/Staged runtime source pin differs/);
// A declared byte count is independently checked even when its SHA remains exact.
assert.throws(()=>check((name,bytes)=>name==='declarative-run-package.js'?Buffer.from(bytes.toString('utf8').replace(/"bytes":(\d+)/,(_,length)=>'"bytes":'+(Number(length)+1))):bytes),/Staged runtime source pin differs/);
// Same-length damage must fail the digest comparison, not just the size guard.
for(const name of ['local-experiment.js','finite-json.js','declarative-rune-program.js','declarative-plan-controls.js','language-score.js','language-model-data.js']){
 assert.throws(()=>check((actual,bytes)=>{if(actual!==name)return bytes;const changed=Buffer.from(bytes);changed[changed.length-1]^=1;return changed;}),/Staged runtime source pin differs/,'Same-length index mutation must fail: '+name);
}
assert.throws(()=>check((name,bytes)=>name==='declarative-run-package.js'?Buffer.from('No source declarations'):bytes),/Missing or ambiguous declarative runtime source declarations/);
console.log('PASS all 17 runtime source pins, changed dependencies/owners and separate byte-length/hash poison cases use simulated Git bytes only; actual index untouched');
