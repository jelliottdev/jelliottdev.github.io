/* Independent default-catalog validation bypass boundaries, no source receipts run. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import Catalog from '../published-program-source-catalog-data.js';
import Compiled,{metadata} from '../services/idea-assistant/compiled-program-index-data.mjs';
import {artifact,build,compilerSourceSha256} from './build_compiled_program_index.mjs';
import {checkedProgramIndex} from '../services/idea-assistant/published-program-source-index.mjs';
import {publishedProgramIndex} from '../services/idea-assistant/published-evidence.mjs';
import J from '../finite-json.js';
import E from '../local-experiment.js';
const total=Catalog.entries.length,root=new URL('../',import.meta.url),sha=v=>createHash('sha256').update(v).digest('hex');
build({check:true});const checked=checkedProgramIndex(Catalog);assert.deepEqual(Compiled,checked);assert.strictEqual(Compiled,Catalog);assert.deepEqual(metadata,artifact().metadata);assert.equal(metadata.entries,total);assert.equal(metadata.indexSha256,sha(E.stable(checked)));for(const pin of metadata.sourcePins)assert.equal(pin.sha256,sha(readFileSync(new URL(pin.path,root))));assert.equal(metadata.compilerSourceNormalization,'utf8-lf');for(const pin of metadata.compilerSourcePins)assert.equal(pin.sha256,sha(readFileSync(new URL(pin.path,root),'utf8').replaceAll('\r\n','\n')));assert.equal(compilerSourceSha256('const label=\"rune\";\r\nnext();\r\n'),compilerSourceSha256('const label=\"rune\";\nnext();\n'));assert.notEqual(compilerSourceSha256('one\n'),compilerSourceSha256('two\n'));assert.notEqual(sha('one\r\n'),sha('one\n'));
const frozen=value=>{if(!value||typeof value!=='object')return;assert(Object.isFrozen(value));for(const child of Object.values(value))frozen(child);};frozen(Compiled);assert.throws(()=>{Compiled.entries[0].path='published-evidence/programs/forged.json';});
console.log('PASS checked compilation preserves all current exact records, settings, paths, hashes and nested immutable data without duplicating the catalog');
const capture=J.capture;let calls=0;try{J.capture=(...args)=>{calls++;return capture(...args);};const first=await publishedProgramIndex();assert.strictEqual(first,Compiled);const values=await Promise.all(Array.from({length:4},()=>publishedProgramIndex()));assert(values.every(value=>value===Compiled));assert.equal(calls,0);
 const input=structuredClone(Catalog),one=await publishedProgramIndex({programIndex:input});assert.deepEqual(one,Catalog);assert.notStrictEqual(one,input);assert(calls>0);input.entries.pop();const two=await publishedProgramIndex({programIndex:input});assert.equal(two.entries.length,total-1);assert.equal(one.entries.length,total);assert.equal((await publishedProgramIndex()).entries.length,total);
 let getters=0;const bad={schema:Catalog.schema};Object.defineProperty(bad,'entries',{enumerable:true,get(){getters++;return Catalog.entries;}});await assert.rejects(publishedProgramIndex({programIndex:bad}));assert.equal(getters,0);await assert.rejects(publishedProgramIndex({programIndex:{...Catalog,artifact:metadata}}));const invalid=structuredClone(Catalog);invalid.entries[0].sha256='broken';await assert.rejects(publishedProgramIndex({programIndex:invalid}));assert.equal(await publishedProgramIndex({programIndex:null}),null);assert.equal(await publishedProgramIndex({registry:{}}),null);
}finally{J.capture=capture;}
console.log('PASS cold and warm defaults skip JSON capture while mutable, malformed, getter and artifact-injected indexes retain full validation');
console.log('2 compiled default program index groups passed; no receipt execution or caller artifacts accepted.');
