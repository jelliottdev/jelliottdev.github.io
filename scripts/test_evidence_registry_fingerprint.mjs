/* Build parity for trusted Worker-local metadata, no receipt runs. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {artifact,build,compilerSourceSha256} from './build_evidence_registry_fingerprint.mjs';
import Data from '../services/idea-assistant/evidence-registry-fingerprint-data.mjs';
import E from '../local-experiment.js';
import Counts from '../published-count-evidence-data.js';
import Programs from '../published-opening-evidence-data.js';
import History from '../published-evidence-history-data.js';
import Catalog from '../published-program-source-catalog-data.js';
import {checkedProgramIndex} from '../services/idea-assistant/published-program-source-index.mjs';
import {readEvidenceRegistryHash} from '../services/idea-assistant/factored-evidence-provider.mjs';
const sha=v=>createHash('sha256').update(v).digest('hex'),root=new URL('../',import.meta.url);
build({check:true});assert.deepEqual(artifact().value,Data);assert.equal(artifact().text,artifact().text);
const index=checkedProgramIndex(Catalog);assert.equal(Data.archiveSha256,sha(E.stable({index,registries:[Counts,Programs],history:History})));
const metadata=[...[...Counts.entries,...Programs.entries].map(({recordId,revision,caseId,inputVersion,task})=>({recordId,revision,caseId,inputVersion,task})),...index.entries.map(item=>({...item,indexed:true}))].sort((a,b)=>E.stable([a.recordId,a.revision,a.caseId]).localeCompare(E.stable([b.recordId,b.revision,b.caseId])));
assert.equal(Data.discoverySha256,sha(E.stable(metadata)));for(const pin of Data.sourcePins)assert.equal(pin.sha256,sha(readFileSync(new URL(pin.path,root))));assert.equal(Data.compilerSourceNormalization,'utf8-lf');for(const pin of Data.compilerSourcePins)assert.equal(pin.sha256,sha(readFileSync(new URL(pin.path,root),'utf8').replaceAll('\r\n','\n')));assert.equal(compilerSourceSha256('const label=\"rune\";\r\nnext();\r\n'),compilerSourceSha256('const label=\"rune\";\nnext();\n'));assert.notEqual(compilerSourceSha256('one\n'),compilerSourceSha256('two\n'));assert.notEqual(sha('one\r\n'),sha('one\n'));
console.log('PASS generated fingerprints match checked current index, embedded receipts, retained history and exact dependency bytes');
const stable=E.stable;try{E.stable=value=>{if(value&&Object.hasOwn(value,'registries'))throw Error('Runtime serialized the full immutable archive');return stable(value);};assert.equal(await readEvidenceRegistryHash(),Data.archiveSha256);await assert.rejects(readEvidenceRegistryHash({programIndex:Catalog}),/serialized/);}finally{E.stable=stable;}
console.log('PASS default native path skips archive serialization while explicitly injected data keeps full validation and hashing');
const changed=structuredClone(Catalog);changed.entries.pop();assert.notEqual(await readEvidenceRegistryHash({programIndex:changed}),Data.archiveSha256);await assert.rejects(readEvidenceRegistryHash({programIndex:{...Catalog,hash:Data.archiveSha256}}));
console.log('PASS altered indexes change their fingerprint and caller supplied fingerprint fields cannot acquire deployment authority');
console.log('3 generated registry fingerprint groups passed; no evidence outputs, epochs or admission cached.');
