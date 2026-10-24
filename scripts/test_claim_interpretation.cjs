'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const I=require('../claim-interpretation.js');
const context=vm.createContext({TextEncoder});
vm.runInContext(fs.readFileSync(require.resolve('../claim-specification.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(require.resolve('../claim-interpretation.js'),'utf8'),context);
const B=context.ClaimInterpretation;
const local=value=>vm.runInContext('JSON.parse('+JSON.stringify(JSON.stringify(value))+')',context);
const plain=value=>JSON.parse(JSON.stringify(value));
const source=(raw,quote)=>({start:raw.indexOf(quote),quote});
const step=(raw,quote,id='described_method',familyId=null)=>({id,familyId,source:source(raw,quote),parameters:{}});
const candidate=(raw,steps=[step(raw,raw)])=>({schema:I.SCHEMA,outcome:null,steps,scope:null,rules:{}});
let count=0;const test=(name,fn)=>{fn();count++;console.log('PASS '+name);};

(async()=>{
 const E=await import('../services/idea-assistant/interpretation.mjs');
 const Adapter=await import('../services/idea-assistant/interpret-handler.mjs');
 test('plural rows wire reaches ambiguity instead of generic invalid interpretation',()=>{
  const raw='Reverse prime values in rows';
  const wire={schema:I.SCHEMA,outcome:null,steps:[{id:'ambiguous_reversal',familyId:null,source:source(raw,raw)}],scope:null,rules:[]};
  const proposed=Adapter.fromWire(wire,raw),draft=I.toDraft(raw,proposed).draft;
  assert.equal(draft.source.text,raw);assert.equal(require('../claim-specification.js').questions(draft)[0].id,'operation');
  assert.deepEqual(plain(B.toDraft(raw,local(proposed))),I.toDraft(raw,proposed));
  for(const text of ['Do not reverse prime values in rows','Reverse prime values in rows with key ABC','Reverse prime values in rows then apply Atbash','Reverse prime values in rows only if marked'])assert.throws(()=>I.validateCandidate(text,candidate(text,[step(text,text,'ambiguous_reversal')])));
 });
 test('browser UMD, CommonJS and existing ESM wrapper preserve the exact exports',()=>{
  assert.deepEqual(Object.keys(I).sort(),['SCHEMA','MAX_TEXT','JSON_SCHEMA','PROMPT','validateInput','validateCandidate','toDraft','pagesFromSource','keyDeclarations','outcomeEvidence'].sort());
  for(const key of Object.keys(I))assert.equal(E[key],I[key]);
  assert.equal(B.SCHEMA,I.SCHEMA);assert.equal(B.MAX_TEXT,I.MAX_TEXT);assert.equal(B.PROMPT,I.PROMPT);assert.deepEqual(plain(B.JSON_SCHEMA),I.JSON_SCHEMA);
  assert.equal(context.document,undefined);assert.equal(context.fetch,undefined);assert.equal(context.localStorage,undefined);
 });
 test('browser and Node preserve ambiguous reversal and existing boundary questions identically',()=>{
  for(const [raw,id] of [['Reverse prime values in each row.','ambiguous_reversal'],['Reverse each row, preserving word boundaries.','reverse_row_runes']]){
   const p=candidate(raw,[step(raw,raw,id)]);
   if(id==='reverse_row_runes')p.rules.wordBoundaries={status:'specified',value:'preserve',source:source(raw,'preserving word boundaries')};
   assert.deepEqual(plain(B.toDraft(raw,local(p))),I.toDraft(raw,p));
   assert.equal(B.toDraft(raw,local(p)).requiresConfirmation,true);assert.equal(B.toDraft(raw,local(p)).draft.confirmation,null);
  }
 });
 test('ordered compound, exact quoted key, page holes and opaque negation have browser parity',()=>{
  const raw='Reverse each row then use Vigenere with key "A B" on LP2-15 and LP2-17.',first='Reverse each row',tail='use Vigenere with key "A B" on LP2-15 and LP2-17.';
  const p=candidate(raw,[step(raw,first,'reverse_row_runes'),step(raw,tail)]);p.steps[1].parameters.key={value:'A B',source:source(raw,'key "A B"')};p.scope={pages:['lp2-15','lp2-17'],passage:null,source:source(raw,'LP2-15 and LP2-17')};
  assert.deepEqual(plain(B.validateCandidate(raw,local(p))),I.validateCandidate(raw,p));assert.deepEqual(plain(B.toDraft(raw,local(p))),I.toDraft(raw,p));
  const negative='Do not reverse each row unless the supplied key permits it.';assert.deepEqual(plain(B.toDraft(negative,local(candidate(negative)))),I.toDraft(negative,candidate(negative)));
 });
 test('untrusted invented quotes/categories and truncated conditional meaning fail with identical errors',()=>{
  const raw='Do not reverse each row.',cases=[candidate(raw,[step(raw,'reverse each row','reverse_row_runes')]),candidate(raw)];
  cases[1].steps[0].familyId='invented-category';const wrong=candidate(raw);wrong.steps[0].source.start=9;cases.push(wrong);
  for(const p of cases){let node,browser;try{I.validateCandidate(raw,p);}catch(e){node=e.message;}try{B.validateCandidate(raw,local(p));}catch(e){browser=e.message;}assert(node);assert.equal(browser,node);}
  for(const rawInput of ['', 'x'.repeat(1501)]){assert.throws(()=>I.validateInput(rawInput));assert.throws(()=>B.validateInput(rawInput));}
 });
 test('browser helpers and literal-key condition masking retain the same bounded semantics',()=>{
  assert.deepEqual(plain(B.pagesFromSource('LP2-15 through LP2-17, LP2-19')),I.pagesFromSource('LP2-15 through LP2-17, LP2-19'));
  assert.deepEqual(plain(B.keyDeclarations('Use key "IF" then reset the key at each word.')),I.keyDeclarations('Use key "IF" then reset the key at each word.'));
  const raw='Reverse every row then use Vigenere with key "IF".',tail='use Vigenere with key "IF".';
  const p=candidate(raw,[step(raw,'Reverse every row','reverse_row_runes'),step(raw,tail)]);p.steps[1].parameters.key={value:'IF',source:source(raw,'IF')};
  assert.deepEqual(plain(B.toDraft(raw,local(p))),I.toDraft(raw,p));
  for(const text of ['LP2-15 or LP2-17','LP1-15 to LP2-03']){assert.throws(()=>I.pagesFromSource(text));assert.throws(()=>B.pagesFromSource(text));}
 });
 test('browser and server gate unsupported known aims identically without changing source or useful steps',()=>{
  const raw='Try running the ciphertext through an autokey.',quote='running the ciphertext through an autokey',p=candidate(raw,[step(raw,quote)]);p.outcome={id:'decipher',source:source(raw,quote)};
  assert.deepEqual(plain(B.outcomeEvidence(raw,local(p.outcome))),I.outcomeEvidence(raw,p.outcome));assert.deepEqual(plain(B.toDraft(raw,local(p))),I.toDraft(raw,p));assert.equal(B.toDraft(raw,local(p)).draft.aim.status,'unspecified');
  const text='Count pairs on LP2-00 through LP2-55 apart from LP2-50.',selection='LP2-00 through LP2-55 apart from LP2-50',q=candidate(text);q.outcome={id:'measure',source:source(text,'Count pairs')};q.scope={pages:null,passage:selection,source:source(text,selection)};
  assert.deepEqual(plain(B.toDraft(text,local(q))),I.toDraft(text,q));assert.equal(B.toDraft(text,local(q)).candidate.outcome.id,'measure');
 });
 console.log('PASS '+count+' interpretation UMD parity groups; no DOM, network, model, execution or confirmation calls.');
})().catch(error=>{console.error(error);process.exitCode=1;});
