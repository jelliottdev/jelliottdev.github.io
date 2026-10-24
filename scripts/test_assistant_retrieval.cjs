const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const Search=require('../assistant-search.js');
const root=path.resolve(__dirname,'..');
const records=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'))).records;
const pages=JSON.parse(fs.readFileSync(path.join(root,'data/assistant-index.json'))).documents;
const long='Like the circumference is somehow actually shed by whatever is used to decrypt. Interconnected in the sense of an autokey (recursion, self-reference, seek to find, LP is the way, direction, numbers are the map etc.). Emergent as in shedding the old version of the text allows the new to emerge. So when 3301 says "LP is the way," maybe it\'s not some hokey nonsense, but trying to knock some incredibly literal sense into us. Why else would you have a plaintext page? That\'s literally contained within a music track about emergence? Could it be a numerical (gematria) autokey? Does such a thing exist? This makes me think of the parable number. Maybe that\'s related somehow? I feel like both “instar emerging” and “interconnectedness” could be implying something about the method of decryption';
const short='Could an autokey use plaintext prime values from the parable?';
assert(records.length>=259,'Run the experiment builder before retrieval tests');
assert(records.find(record=>record.id==='cumulative-autokey-literal')?.method_topics?.some(topic=>topic.id==='feedback'),
  'The generated registry must carry authored, non-exclusive feedback hints');
const docs=Search.experimentDocs(records),withPages=[...pages,...docs];
const ids=(items)=>items.map(item=>item.id);
const visible=(query,targets=[])=>Search.classify(withPages,query,targets).tests.map(hit=>hit.document.id);
const selected=ids(Search.select(withPages,long));
assert.equal(selected[0],'gp-prime-plaintext-feedback','The specific plaintext-prime test should lead, without claiming to settle the vague shedding idea');
assert.deepEqual(visible(long),selected,'Visible test cards and Worker evidence must agree');
assert.equal(Search.select(withPages,short)[0].id,'gp-prime-plaintext-feedback','The prime-valued plaintext rule is closer than generic history feedback');
for(const [query,targets] of [[long+' on LP2-31',[]],[long,['lp2-31']]]){
 const found=Search.select(withPages,query,targets);
 assert.equal(found[0].id,'gp-prime-plaintext-feedback');
 assert.deepEqual(visible(query,targets),found.filter(doc=>doc.kind==='experiment').map(doc=>doc.id));
 assert(found.some(doc=>doc.kind==='page'&&doc.page==='lp2-31'),
   'Requested page context must follow the full method evidence');
 assert(found.reduce((sum,doc)=>sum+doc.text.length,0)<=11000);
}
assert.deepEqual(Search.select(withPages,'has anyone tried LP2-31'),[]);
const lexicalDocs=Search.experimentDocs(records.map(record=>({...record,method_topics:[]})));
for(const query of [
 'Could autokey and OutGuess decode LP2?',
 'Could Beaufort ciphertext autokey explain rare doublets?',
 'Could a plaintext autokey with Vigenere decode the parable?',
 'Could an iceflower cipher decode LP2?'
])assert.deepEqual(ids(Search.select(docs,query)),ids(Search.select(lexicalDocs,query)),
  'Mixed or unknown methods must retain the lexical fallback: '+query);
const malformed=Search.experimentDocs(records.map(record=>({...record,method_topics:{id:'feedback',aliases:['autokey']}})));
assert.deepEqual(ids(Search.select(malformed,long)),ids(Search.select(lexicalDocs,long)),
  'A nonarray topic container cannot crash or create an accidental method match');
const oversized=docs.map(doc=>doc.id==='gp-prime-plaintext-feedback'?{...doc,text:doc.text+'x'.repeat(9001)}:doc);
assert.deepEqual(Search.select(oversized,long),[],
  'An oversized rescued winner must refuse inference instead of substituting a weaker result');
assert.equal(Search.classify(oversized,long).tests.length,0);
assert.deepEqual(ids(Search.select(docs,'dead tree on LP2-55')),[]);
assert.equal(Search.classify(docs,'dead tree on LP2-55').tests.length,0);
assert(Search.classify(docs,'dead tree on LP2-55').supporting.length>0);
const auditQuery='Does the Latin and Greek language-model control validate the search?';
assert.equal(Search.select(docs,auditQuery)[0].id,'dukotah-nonenglish-control-gate');
assert.equal(Search.classify(docs,auditQuery).tests.length,0);
assert.equal(Search.classify(docs,auditQuery).supporting[0].document.recordType,'audit');
const lagClaim='The lag-6 relation inside words: c′ = 24 − 2c (mod 29). Two runes six positions apart satisfy this more often than chance, 80 against 45.7 expected; zero across word gaps and linked to doublets.';
const lagEvidence=Search.classify(docs,lagClaim);
assert.deepEqual(lagEvidence.tests,[],
 'An exact numeric/statistical claim must retain measurement evidence ahead of a generic doublet method');
assert.deepEqual(lagEvidence.supporting.map(hit=>hit.document.id),
 ['word-internal-affine-lags','word-internal-affine-all-lags','lp2-page-join-lag-six-sensitivity']);
// New source records must be reachable through ordinary descriptions. A leading
// measurement/control/audit keeps that type; it must not become a cipher result.
for(const [query,id,type] of [
 ['Could confusing O A AE rune readings explain low doublets?','oae-uniform-remapping','measurement'],
 ['Do the archived signed messages retain trailing spaces and tabs?','dukotah-h02-raw-whitespace-census','audit'],
 ['Have we tried skipping two key draws when repeated runes collide?','c2-extension-generator-controls','control'],
 ['Do the ornament boxes with n less than 16 have only 16 glyphs?','dukotah-ornament-component-recount','measurement']
]){
 const selected=Search.select(docs,query);
 assert.equal(selected[0]?.id,id,query);
 assert.equal(selected[0]?.recordType,type,query);
}
const webMarkers=Search.select(docs,'Have we tried WWW HTTP HTTPS ONION markers with affine rune maps?');
assert.equal(webMarkers[0]?.id,'url-marker-affine-census');
assert.equal(webMarkers[0]?.recordType,'measurement','A literal marker census must not become a verified URL solve');
const shiftedPages=Search.classify(docs,'Have we tried shifting two pages and measuring their difference IoC?');
assert(shiftedPages.supporting.some(hit=>hit.document.id==='lp2-shifted-page-pair-differences'),
 'Shifted-page questions must include the actual all-offset measurement, not only a shared-key control');
for(const query of [long,short,auditQuery,'OutGuess on LP2-31']){
 const found=Search.select(withPages,query);
 assert(found.filter(doc=>doc.kind==='experiment').reduce((sum,doc)=>sum+doc.text.length,0)<=9000);
 assert(found.reduce((sum,doc)=>sum+doc.text.length,0)<=11000);
 for(const doc of found.filter(doc=>doc.kind==='experiment')){
  const source=records.find(record=>record.id===doc.id);
  assert.equal(doc.text,JSON.stringify({record_type:source.record_type,question:source.question,
   family:source.family,variant:source.variant,scope:source.scope,outcome:source.outcome,
   finding:source.finding,limitations:source.limitations}),
  'Selected evidence must preserve the entire recorded scope and limits');
 }
}
const browser={};vm.runInNewContext(fs.readFileSync(path.join(root,'assistant-search.js'),'utf8'),browser);
for(const query of [long,short,auditQuery])assert.equal(
 JSON.stringify(ids(browser.AssistantSearch.select(docs,query))),JSON.stringify(ids(Search.select(docs,query))),
 'Browser global and Worker/CommonJS ranking must agree');
const ui={};vm.runInNewContext(fs.readFileSync(path.join(root,'assistant-ui.js'),'utf8'),ui);
assert.equal(ui.ideaSourceType({kind:'experiment'}),'Research record',
 'Old cached Worker responses without a type must not be labeled solving tests');
assert.equal(ui.ideaSourceType({kind:'experiment',recordType:'constructor'}),'Research record');
assert.equal(ui.ideaSourceType({kind:'experiment',recordType:'method'}),'Solving test');
assert.equal(ui.ideaSourceType({kind:'experiment',recordType:'historical'}),'Historical reproduction');
assert.equal(ui.ideaSourceType({kind:'experiment',recordType:'alphabet'}),'Alphabet-wide analysis');
assert.equal(ui.ideaSourceType({kind:'experiment',recordType:'audit'}),'Source or input audit');
console.log('PASS: generated method hints, named/mixed/unknown methods, pages, visible/Worker parity, full evidence budgets, audits, and malformed metadata.');

for(const [query,expected] of [
 ['Can a guessed word seed an LFSR feedback key using Berlekamp Massey?','wulfic-crib-lfsr-recurrence'],
 ['Did the Round 19 decoder recover a full book with the known key?','round19-full-book-decoder-power']
]){
 assert.equal(Search.select(docs,query)[0].id,expected,'Specific source method/control queries should retrieve the matching scoped record');
 const bucket=expected==='round19-full-book-decoder-power'?'supporting':'tests';
 const classified=Search.classify(withPages,query);
 assert.equal(classified[bucket][0].document.id,expected,'A control remains supporting evidence; a replay remains a method result');
 assert(!classified[bucket==='tests'?'supporting':'tests'].some(hit=>hit.document.id===expected),'The record must not appear under the wrong evidence type');
 assert.equal(Search.select(withPages,query)[0].id,expected,'Worker evidence and the first visible result must agree');
}
console.log('PASS: crib-derived feedback and full-book known-key questions reach their distinct scoped records.');
