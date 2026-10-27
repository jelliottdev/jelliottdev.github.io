/* Archive navigation metadata only: no target execution or database access. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import E from '../../local-experiment.js';
import Catalog from '../../published-program-source-catalog-data.js';
import {archivedVariationNavigation} from './archived-variation-navigation.mjs';
import {createArchivedParameterContextHandler,boundedContextBody} from './archived-parameter-context.mjs';

const root=new URL('../../',import.meta.url),bundle=JSON.parse(readFileSync(new URL('data/local-run-inputs.json',root))),origin='https://jelliottdev.github.io',empty={schema:'liberpedia-published-program-evidence-v1',records:[],entries:[]},index=entries=>({schema:'liberpedia-published-program-source-index-v1',entries}),phase=value=>({version:1,step:0,parameter:'phase',value});
const regular=Catalog.entries.find(e=>e.caseId==='known-keys-welcome-phase-0-subtract--all-pages'),destination=Catalog.entries.find(e=>e.caseId==='known-keys-welcome-phase-1-subtract--all-pages');
async function task(entry){return E.prepare({title:'Metadata-only navigation fixture',alphabet:bundle.alphabet,pages:entry.pages.map(p=>({id:p.id,text:bundle.pages.find(b=>b.id===p.id).raw})),steps:entry.steps,criterion:entry.criterion});}
const parent=await task(regular),copy=structuredClone,sha=value=>createHash('sha256').update(E.stable(value)).digest('hex');
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
const oldRun=E.run,oldVerify=E.verify,oldPrepare=E.prepare;E.run=E.verify=()=>assert.fail('Navigation must not execute or replay another output');
try{
await test('all904 current phase choices point to exact full-page active metadata without preparing child tasks',async()=>{
 const rows=Catalog.entries.filter(e=>e.steps.some(s=>s.op==='keyed-shift'&&s.mode==='repeat'));assert.equal(rows.length,74);let matched=0;
 for(const row of rows){const parent=await task(row);E.prepare=()=>assert.fail('No per-choice task preparation');let hints;try{hints=await archivedVariationNavigation({task:parent,inputVersion:row.inputVersion});}finally{E.prepare=oldPrepare;}assert.equal(hints.parentTaskHash,sha(parent));assert.equal(hints.inputVersion,row.inputVersion);assert(Object.isFrozen(hints.choices));for(const item of hints.choices.filter(c=>c.selection.parameter==='phase')){assert.equal(item.matchingPageCount,row.pages.length);assert(Catalog.entries.some(e=>e.recordId===item.reference.recordId&&e.revision===item.reference.revision&&e.caseId===item.reference.caseId));matched++;}}
 assert.equal(matched,904);
});
await test('largest exact intersection and stable pointer tie select only one navigation link',async()=>{
 const small=copy(destination);small.pages=small.pages.slice(0,2);small.caseId='small-case';const tie=copy(destination);tie.caseId='a-tie-case';const hints=await archivedVariationNavigation({task:parent,inputVersion:'raw'},{registry:empty,programIndex:index([small,destination,tie])}),found=hints.choices.find(c=>E.stable(c.selection)===E.stable(phase(1)));assert.equal(found.matchingPageCount,parent.pages.length);assert.equal(found.reference.caseId,'a-tie-case');assert.deepEqual(Object.keys(found),['selection','reference','matchingPageCount']);
 const partial=await archivedVariationNavigation({task:parent,inputVersion:'raw'},{registry:empty,programIndex:index([small])});assert.equal(partial.choices.find(c=>c.selection.parameter==='phase').matchingPageCount,2);assert(!('coveredPages' in partial));assert(!('lookupComplete' in partial));
});
await test('edition alphabet steps criterion and literal page hashes are all required',async()=>{
 for(const change of [e=>e.alphabetSha256='0'.repeat(64),e=>e.steps[0].direction='add',e=>e.criterion.values[0]=(e.criterion.values[0]+1)%29,e=>e.pages.forEach(p=>p.textSha256='0'.repeat(64))]){const entry=copy(destination);change(entry);const hints=await archivedVariationNavigation({task:parent,inputVersion:'raw'},{registry:empty,programIndex:index([entry])});assert(!hints.choices.some(c=>c.selection.parameter==='phase'&&c.selection.value===1));}
 const reviewed=await archivedVariationNavigation({task:parent,inputVersion:'reviewed'},{registry:empty,programIndex:index([destination])});assert.deepEqual(reviewed.choices,[]);
 const a=await archivedVariationNavigation({task:parent,inputVersion:'raw'},{registry:empty,programIndex:index([destination])}),changed=copy(destination);changed.caseId='different-case';const b=await archivedVariationNavigation({task:parent,inputVersion:'raw'},{registry:empty,programIndex:index([changed])});assert.notEqual(a.catalogGeneration,b.catalogGeneration);
});
await test('opt-in preserves old response and adds hints without additional archive source fetches',async()=>{
 let reads=0;const fetcher=async url=>{reads++;return new Response(readFileSync(new URL(new URL(url).pathname.slice(1),root)),{headers:{'content-type':'application/json'}});},handler=createArchivedParameterContextHandler({fetcher}),env={SITE_ORIGIN:origin,TASK_LIMIT:{limit:async()=>({success:true})},PROPOSALS:new Proxy({},{get(){assert.fail('No database for navigation');}})},ref={recordId:regular.recordId,revision:regular.revision,caseId:regular.caseId},request=body=>new Request('https://worker.test/parameter-questions/archive-context',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(body)});
 const first=await handler(request(ref),env);assert.equal(first.status,200);const original=await first.json();assert.deepEqual(Object.keys(original),['schema','context']);reads=0;const response=await handler(request({...ref,includeNavigationHints:true}),env);assert.equal(response.status,200);const value=await response.json();assert.deepEqual(value.context,original.context);assert(value.navigationHints.choices.some(c=>c.selection.parameter==='phase'));assert(reads<=1,'Hints must not hydrate other source receipts');assert.equal(value.navigationHints.parentTaskHash,sha(value.context.task));
 for(const extra of [{includeNavigationHints:false},{includeNavigationHints:1},{includeNavigationHints:true,navigationOffset:0},{includeNavigationHints:true,task:{}}])assert.equal((await handler(request({...ref,...extra}),env)).status,400);
 // A metadata-generation failure is optional; it cannot fabricate empty hints.
 const failGeneration={subtle:{digest:async(...args)=>{if(new TextDecoder().decode(args[1]).includes('"registries":'))throw Error('Optional fingerprint unavailable');return globalThis.crypto.subtle.digest(...args);}}};
 const optional=createArchivedParameterContextHandler({fetcher,crypto:failGeneration}),degraded=await optional(request({...ref,includeNavigationHints:true}),env);assert.equal(degraded.status,200);const fallback=await degraded.json();assert.equal(fallback.navigationHints,null);assert.deepEqual(fallback.context,original.context);
 // Source authentication itself is mandatory, even when hints are optional.
 const broken=createArchivedParameterContextHandler({fetcher,programIndex:{schema:'bad',entries:[]}});assert.equal((await broken(request({...ref,includeNavigationHints:true}),env)).status,503,'Invalid source registry still cannot authenticate parent');
});
await test('abort and captured-input mutation fail without manufactured empty completion',async()=>{
 const abort=new AbortController();abort.abort();await assert.rejects(archivedVariationNavigation({task:parent,inputVersion:'raw'},{signal:abort.signal}),/cancelled/);
 let reads=0;const getter=copy(parent);Object.defineProperty(getter,'steps',{enumerable:true,get(){reads++;return parent.steps;}});await assert.rejects(archivedVariationNavigation({task:getter,inputVersion:'raw'}));assert.equal(reads,0);
 const changed=copy(parent);let first=true;const crypto={subtle:{digest:async(...args)=>{const result=await globalThis.crypto.subtle.digest(...args);if(first){first=false;changed.pages[0].text+=' ';}return result;}}};await assert.rejects(archivedVariationNavigation({task:changed,inputVersion:'raw'},{crypto}),/changed/);
});
await test('optional hint bytes cannot displace an otherwise usable bounded context',()=>{
 const value={schema:'liberpedia-archived-parameter-context-v1',context:{text:'x'.repeat(8*1024*1024-200)},navigationHints:{metadata:'x'.repeat(300)}};
 assert(Buffer.byteLength(JSON.stringify(value))>8*1024*1024);const fallback=boundedContextBody(value);assert.equal(fallback.navigationHints,null);assert.equal(fallback.context,value.context);assert(Buffer.byteLength(JSON.stringify(fallback))<=8*1024*1024);assert.notEqual(value.navigationHints,null,'Fallback does not mutate original optional metadata');
 const oversized={...value,context:{text:'x'.repeat(8*1024*1024)}};assert.throws(()=>boundedContextBody(oversized),/response bound/);const normal={schema:value.schema,context:{},navigationHints:{choices:[]}};assert.equal(boundedContextBody(normal),normal);const old={schema:value.schema,context:{}};assert.equal(boundedContextBody(old),old);
});
}finally{E.run=oldRun;E.verify=oldVerify;E.prepare=oldPrepare;}
console.log(groups+' archived variation navigation groups passed; metadata links only.');
