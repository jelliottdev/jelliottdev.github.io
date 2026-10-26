/* Immutable deployment metadata only: never cache caller indexes or evidence. */
import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import E from '../../local-experiment.js';
import Counts from '../../published-count-evidence-data.js';
import Programs from '../../published-opening-evidence-data.js';
import History from '../../published-evidence-history-data.js';
import Catalog from '../../published-program-source-catalog-data.js';
const digest=webcrypto.subtle.digest;let calls=0;
// Instrument the platform before importing the service, retaining actual native
// SHA-256 arithmetic. The service captures this unchanged platform reference.
webcrypto.subtle.digest=function(...args){calls++;return digest.apply(webcrypto.subtle,args);};
const {readEvidenceRegistryHash}=await import('./factored-evidence-provider.mjs');
const {publishedProgramIndex}=await import('./published-evidence.mjs');
const sha=value=>createHash('sha256').update(E.stable(value)).digest('hex');let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
try{
 await test('cold default fingerprint is exact and warm concurrent calls do not hash immutable metadata again',async()=>{const index=await publishedProgramIndex(),expected=sha({index,registries:[Counts,Programs],history:History}),before=calls,values=await Promise.all(Array.from({length:6},()=>readEvidenceRegistryHash({crypto:webcrypto})));assert(values.every(value=>value===expected));assert.equal(calls-before,1);const count=calls;assert.equal(await readEvidenceRegistryHash({crypto:webcrypto}),expected);assert.equal(calls,count);});
 await test('caller crypto remains uncached and cannot poison the default deployment fingerprint',async()=>{let custom=0;const crypto={subtle:{digest(...args){custom++;return digest.apply(webcrypto.subtle,args);}}},a=await readEvidenceRegistryHash({crypto}),b=await readEvidenceRegistryHash({crypto});assert.equal(a,b);assert.equal(custom,2);const zero={subtle:{digest:async()=>new Uint8Array(32)}};assert.equal(await readEvidenceRegistryHash({crypto:zero}),'0'.repeat(64));assert.equal(await readEvidenceRegistryHash({crypto:webcrypto}),a);});
 await test('mutable or frozen injected indexes and null index are independently validated and hashed every time',async()=>{const index={schema:'liberpedia-published-program-source-index-v1',entries:[]},before=calls,a=await readEvidenceRegistryHash({programIndex:index,crypto:webcrypto});index.entries.push(structuredClone(Catalog.entries[0]));const b=await readEvidenceRegistryHash({programIndex:index,crypto:webcrypto});assert.notEqual(a,b);assert.equal(calls-before,2);const frozen=Object.freeze({schema:index.schema,entries:Object.freeze([])}),count=calls;assert.equal(await readEvidenceRegistryHash({programIndex:frozen,crypto:webcrypto}),a);assert.equal(await readEvidenceRegistryHash({programIndex:frozen,crypto:webcrypto}),a);await readEvidenceRegistryHash({programIndex:null,crypto:webcrypto});await readEvidenceRegistryHash({programIndex:null,crypto:webcrypto});assert.equal(calls-count,4);});
 await test('malformed injected metadata still rejects and platform function replacement cannot acquire a cached hash',async()=>{let reads=0;const bad={schema:'liberpedia-published-program-source-index-v1'};Object.defineProperty(bad,'entries',{enumerable:true,get(){reads++;return[];}});await assert.rejects(readEvidenceRegistryHash({programIndex:bad,crypto:webcrypto}));assert.equal(reads,0);const previous=webcrypto.subtle.digest;try{webcrypto.subtle.digest=async()=>new Uint8Array(32);assert.equal(await readEvidenceRegistryHash({crypto:webcrypto}),'0'.repeat(64));}finally{webcrypto.subtle.digest=previous;}assert.notEqual(await readEvidenceRegistryHash({crypto:webcrypto}),'0'.repeat(64));});
}finally{webcrypto.subtle.digest=digest;}
console.log(groups+' immutable deployment fingerprint groups passed; no source lookup, admission or target execution.');
