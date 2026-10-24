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
 test('browser UMD, CommonJS and existing ESM wrapper preserve seven exact exports',()=>{
  assert.deepEqual(Object.keys(I).sort(),['SCHEMA','MAX_TEXT','JSON_SCHEMA','PROMPT','validateInput','validateCandidate','toDraft'].sort());
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
 console.log('PASS '+count+' interpretation UMD parity groups; no DOM, network, model, execution or confirmation calls.');
})().catch(error=>{console.error(error);process.exitCode=1;});
