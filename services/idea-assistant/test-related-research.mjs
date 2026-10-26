/* Informal source discovery does not require a formal experiment or hosted AI. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHandler,RELATED_PROMPT,COMPARISON_PROMPT} from './worker.mjs';
import Search from '../../assistant-search.js';
const docs=Search.experimentDocs(JSON.parse(readFileSync(new URL('../../data/experiments.json',import.meta.url),'utf8')).records),origin='https://jelliottdev.github.io',copy=structuredClone;
const informal="Hello, ive been working with claude and we've tried, just a whole heap of stuff But most recently, we're toying with the idea that the reason for the unexplained doubles, is that the first unsolved section has some sort of junk added to it Like there are extra runes that have been added to make decryption that much harder If anyone has any input thatd be amazing, im half flying blind here";
const post=body=>new Request('https://fixture.workers.dev/ask',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(body)}),base={SITE_ORIGIN:origin,IDEA_LIMIT:{limit:async()=>({success:true})}},request=query=>({kind:'related-research',query});
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
await test('casual null-insertion/doubles wording retrieves relevant complete bounded research across types',async()=>{
 for(const q of [informal,'Maybe extra junk or null runes were inserted in the first unsolved section, causing unexplained doublets?','Could extra junk runes have been added to LP2, and removing these null runes reveals the text?']){
  const records=Search.related(docs,q),ids=records.map(d=>d.id);assert(ids.includes('single-rune-null-doublets'));assert(ids.includes('doublet-collision-edits'));
  assert(records.length<=4);assert(records.reduce((n,d)=>n+d.text.length,0)<=11000);for(const record of records)assert.equal(record,docs.find(d=>d.id===record.id));
 }
 const records=Search.related(docs,informal);assert(records.some(r=>r.recordType==='audit'));assert(records.some(r=>r.recordType==='measurement'));assert(!records.some(r=>r.id==='known-reading-languages'));
});
await test('related source API accepts unclassified hypotheses without cards aims scopes interpretation or model',async()=>{
 const h=createHandler(async()=>docs),response=await h(post(request(informal)),base),data=await response.json();assert.equal(response.status,200);assert.equal(data.comparisonKind,'related-research');assert.equal(data.answer,null);assert.equal(data.claimBinding,undefined);assert.deepEqual(data.sources.map(s=>s.id),Search.related(docs,informal).map(d=>d.id));assert(!Object.hasOwn(data,'proposalId'));assert(!Object.hasOwn(data,'task'));
 const pasted=informal+'\n'+('Context from the conversation. '.repeat(100));assert(pasted.length>1500&&pasted.length<8000);assert.equal((await h(post(request(pasted)),base)).status,200);
});
await test('model sees unchanged original hypothesis and related-only limits with unchanged source evidence',async()=>{
 let messages;const response=await createHandler(async()=>docs)(post(request(informal)),{...base,AI:{run:async(_m,options)=>{messages=options.messages;return {choices:[{message:{content:'Deleting one fixed rune type is related to the proposal, but checks a narrower diagnostic [1].'}}]};}}}),data=await response.json();assert.equal(response.status,200);assert.equal(messages[0].content,RELATED_PROMPT);assert.notEqual(messages[0].content,COMPARISON_PROMPT);assert.equal(JSON.parse(messages[1].content).idea,informal);assert.match(RELATED_PROMPT,/not proof/);assert.match(RELATED_PROMPT,/Stay within the quantity actually measured/);assert.match(RELATED_PROMPT,/doublet counts.*cannot by itself exclude that fixed type as a null/);assert.match(RELATED_PROMPT,/exclude a decryption rule, establish that removal decrypts the text/);assert.equal(data.comparisonKind,'related-research');assert(data.answer.includes('[1]'));for(const source of data.sources)assert.equal(source.text,docs.find(d=>d.id===source.id).text);
});
await test('provider failures uncited answers and missing AI preserve related research as usable200 sources',async()=>{
 for(const run of [async()=>{throw Error('provider unavailable');},async()=>({choices:[{message:{content:'Unsupported no citations'}}]})]){const h=createHandler(async()=>docs),response=await h(post(request(informal)),{...base,AI:{run}}),data=await response.json();assert.equal(response.status,200);assert.equal(data.answer,null);assert.equal(data.comparisonKind,'related-research');assert(data.sources.some(s=>s.id==='single-rune-null-doublets'));}
});
await test('null statistical controls negation and byte padding do not get rewritten into a filler-rune hypothesis',async()=>{
 for(const q of ['Use a null hypothesis to compare shuffled runes','Not null runes; compare compressed output','Compare byte padding in RSA ciphertext']){const records=Search.related(docs,q);assert(records.length);if(q.includes('null hypothesis'))assert(records.some(d=>['search-maximum-controls','doublet-event-shuffle','doublet-context','lp2-word-internal-lag-six-affine'].includes(d.id))||!records.some(d=>d.id==='single-rune-null-doublets'));}
 const q='Not null runes; compare compressed output',records=Search.related(docs,q);assert(!records.slice(0,2).some(d=>d.id==='single-rune-null-doublets'));
});
await test('strict raw request bounds reject forged structured fields while source-less search stays honest',async()=>{
 const h=createHandler(async()=>docs);for(const body of [request(' '),request('x'.repeat(8001)),request('bad\ud800'),{...request(informal),card:{}},{...request(informal),pages:['lp2-00']},{kind:'other',query:informal},request([informal])])assert.equal((await h(post(body),base)).status,400);
 const response=await createHandler(async()=>[])(post(request('Unrecognized new cipher hypothesis')),base),data=await response.json();assert.equal(response.status,200);assert.equal(data.reason,'no-matching-records');assert.deepEqual(data.sources,[]);assert.equal(data.comparisonKind,'related-research');
});
console.log(groups+' informal related-research groups passed; no experiment creation or execution.');
