/* The built compact artifact must preserve exact retrieval, cards and budgets. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createHash}=require('node:crypto');
const root=path.join(__dirname,'..'),Search=require('../assistant-search.js');
const fullBytes=fs.readFileSync(path.join(root,'data/experiments.json')),full=JSON.parse(fullBytes);
const payload=JSON.parse(fs.readFileSync(process.argv[2]||path.join(root,'data/checker-records.json')));
assert.equal(payload.registry_sha256,createHash('sha256').update(fullBytes).digest('hex'),'Artifact must come from the same complete registry');
const ui={esc:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))};
vm.createContext(ui);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),ui);
vm.runInContext(fs.readFileSync(path.join(root,'assistant-ui.js'),'utf8'),ui);
assert(ui.validCheckerPayload(payload),'Built artifact meets the runtime schema');
const complete=Search.experimentDocs(full.records),compact=Search.experimentDocs(payload.records);
assert.equal(JSON.stringify(compact),JSON.stringify(complete),'Every evidence and lexical retrieval byte must match');
assert(payload.records.every(record=>!Object.hasOwn(record,'reproduction')),'Compact rows must not masquerade as complete detail records');
for(let n=0;n<full.records.length;n++)for(const pages of [[],['lp2-31','lp2-56']])assert.equal(
 ui.experimentSearchResult(full.records[n],pages),ui.experimentSearchResult(payload.records[n],pages));
// Capture comprehensive real regression queries; compare both artifacts under the same contexts.
const cases=new Map(),original={};
for(const name of ['select','classify','supporting','experiments']){
 original[name]=Search[name];Search[name]=function(documents,query,pages=[]){cases.set(JSON.stringify([query,pages]),[query,pages]);return original[name](documents,query,pages)};
}
try{require('./test_assistant.cjs');require('./test_assistant_retrieval.cjs')}
finally{for(const [name,fn] of Object.entries(original))Search[name]=fn;}
const pageDocs=JSON.parse(fs.readFileSync(path.join(root,'data/assistant-index.json'))).documents;
for(const [query,pages] of cases.values())for(const context of [[],pageDocs]){
 const a=[...context,...complete],b=[...context,...compact];
 const selected=Search.select(a,query,pages),other=Search.select(b,query,pages);
 assert.equal(JSON.stringify(other),JSON.stringify(selected),'Selection/source-validation/cache identities: '+query);
 assert.equal(JSON.stringify(Search.classify(b,query,pages)),JSON.stringify(Search.classify(a,query,pages)),'Classification: '+query);
 assert(selected.filter(doc=>doc.kind==='experiment').reduce((sum,doc)=>sum+doc.text.length,0)<=9000);
 assert(selected.reduce((sum,doc)=>sum+doc.text.length,0)<=11000);
}
const long=[...cases.values()].find(([query])=>query.startsWith('Like the circumference'))[0];
const oversized=docs=>docs.map(doc=>doc.id==='gp-prime-plaintext-feedback'?{...doc,text:doc.text+'x'.repeat(9001)}:doc);
assert.deepEqual(Search.select(oversized(compact),long),[]);assert.deepEqual(Search.select(oversized(complete),long),[]);
console.log(`PASS: built compact artifact, ${full.records.length} exact docs/cards, ${cases.size*2} retrieval contexts, source identities and unchanged 9k/11k budgets.`);
