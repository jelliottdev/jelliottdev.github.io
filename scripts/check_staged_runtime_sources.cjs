/* Check the bytes Git will publish, including Windows line-ending normalization. */
'use strict';
const {execFileSync}=require('node:child_process'),{createHash}=require('node:crypto');
const read=name=>execFileSync('git',['show',':'+name],{maxBuffer:4*1024*1024}),checks=[
 ['tools/verify_subset_controls.py',/FINITE_AUDIT_SHA256 = '([a-f0-9]{64})'/g,'tools/verify_finite_search.py'],
 ['local-run-package.js',/const GUARD_SHA256='([a-f0-9]{64})';/g,'tools/verify_controls.py'],
 ['local-run-package.js',/const SUBSET_GUARD_SHA256='([a-f0-9]{64})';/g,'tools/verify_subset_controls.py'],
 ['local-run-package.js',/const PLAN_GUARD_SHA256='([a-f0-9]{64})';/g,'tools/verify_plan_controls.py'],
 ['local-run-package.js',/const AUTHORED_LANGUAGE_GUARD_SHA256='([a-f0-9]{64})';/g,'tools/verify_authored_language.py'],
 ['local-run-package.js',/const FINITE_RUNNER_SHA256='([a-f0-9]{64})';/g,'tools/research_runner.py'],
 ['local-run-package.js',/const FINITE_AUDIT_SHA256='([a-f0-9]{64})';/g,'tools/verify_finite_search.py'],
 ['factored-finite-search-package.js',/runner:'([a-f0-9]{64})'/g,'tools/research_runner.py'],
 ['factored-finite-search-package.js',/auditV1:'([a-f0-9]{64})'/g,'tools/verify_finite_search.py'],
 ['factored-finite-search-package.js',/auditV2:'([a-f0-9]{64})'/g,'tools/verify_factored_finite_search.py'],
 ['factored-finite-search-package.js',/languageModel:'([a-f0-9]{64})'/g,'tools/language-model.json']
],files=new Map();
for(const [owner,pattern,source]of checks){
 if(!files.has(owner))files.set(owner,read(owner).toString('utf8'));
 const matches=[...files.get(owner).matchAll(pattern)];if(matches.length!==1)throw Error('Missing or ambiguous source pin in '+owner+': '+source);
 const actual=createHash('sha256').update(read(source)).digest('hex');
 if(matches[0][1]!==actual)throw Error('Staged runtime source pin differs from published Git bytes: '+source+' in '+owner);
}
// Read the package's declared closure from the index as data, never require a
// working-tree module whose bytes could differ from what Git will publish.
const packageOwner='declarative-run-package.js',packageText=read(packageOwner).toString('utf8');
const declarations=[...packageText.matchAll(/const SOURCES=Object\.freeze\((\[[^\r\n]+\])\.map\(pin=>Object\.freeze\(pin\)\)\);/g)];
if(declarations.length!==1)throw Error('Missing or ambiguous declarative runtime source declarations');
const sources=JSON.parse(declarations[0][1]),expected=['local-experiment.js','finite-json.js','declarative-rune-program.js','declarative-plan-controls.js','language-score.js','language-model-data.js'];
if(!Array.isArray(sources)||sources.length!==expected.length)throw Error('Invalid declarative runtime closure');
for(let i=0;i<expected.length;i++){
 const pin=sources[i];
 if(!pin||typeof pin!=='object'||Array.isArray(pin)||Object.keys(pin).length!==3||pin.path!==expected[i]||!Number.isSafeInteger(pin.bytes)||pin.bytes<1||typeof pin.sha256!=='string'||!/^[a-f0-9]{64}$/.test(pin.sha256))throw Error('Invalid declarative runtime source pin: '+expected[i]);
 const bytes=read(pin.path),actual=createHash('sha256').update(bytes).digest('hex');
 if(bytes.length!==pin.bytes||actual!==pin.sha256)throw Error('Staged runtime source pin differs from published Git bytes: '+pin.path+' in '+packageOwner);
}
console.log('PASS: '+(checks.length+sources.length)+' runtime source pins match the staged Git bytes');
