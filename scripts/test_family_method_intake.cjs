'use strict';
// Maintained intake only. No hosted service, model, worker or public write.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js'),Compiler=require('../fixed-plan-compiler.js');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['original wording']});
const source='Look for an interconnected structure; keep every original condition.';
function draft(){return C.createDraft({source:{text:source},aim:known({outcomeId:'decipher',wording:'Find an explanation for LP2',detail:'Do not change this aim'}),scope:known({pages:['lp2-15','lp2-17']}),rules:{inputVersion:known('reviewed'),evaluation:known('measurement')}});}
function selectFamily(id){return I.answerIntake(draft(),'method','family:'+id);}
function current(d){return I.intakeQuestions(d).find(q=>/^family-/.test(q.id));}
function answer(d,choice,text=''){const q=current(d);assert(q,'Expected a maintained family question');return I.answerIntake(d,q.id,choice,text);}
function unchanged(original,value){assert.deepEqual(value.source,original.source);assert.deepEqual(value.aim,original.aim);assert.deepEqual(value.scope,original.scope);assert.deepEqual(value.rules.inputVersion,original.rules.inputVersion);}
function card(d){return H.cardData(C.confirm(d,{id:'private-fixture',at:'2026-10-25T12:00:00Z'}));}
let groups=0;function test(name,fn){fn();groups++;console.log('PASS '+name);}

test('All eight maintained families require a specific rule and preserve original fields',()=>{
 for(const id of Object.keys(C.METHOD_FAMILIES)){
  const original=draft(),family=I.answerIntake(original,'method','family:'+id),q=current(family);
  assert.equal(family.method.value.operations[0].id,'family_selection');assert(q.choices.some(c=>c.id==='describe'));
  assert(q.context.includes(id==='book-codes'?'does not yet run':'family alone'));unchanged(original,family);
  const described=answer(family,'describe','Use my exact source, coordinates, and lookup rule.');
  assert.equal(described.method.value.operations[0].id,'described_method');assert.equal(described.method.value.operations[0].declaredFamilyId,id);
  assert.equal(current(described),undefined);unchanged(original,described);assert.deepEqual(described.rules,original.rules);
  assert.equal(described.methodEdits.at(-1).previousOperation.id,'family_selection');
 }
});
test('Literal affine and rune reversal compile with exact settings; no family changes their meaning',()=>{
 const base=selectFamily('fixed-substitution'),a=answer(base,'affine','7, 7');
 assert.deepEqual(Compiler.compile(card(a)).steps,[{op:'affine',a:7,b:7}]);
 for(const text of ['7','7, 7, 7','29, 0','-1, 0','7, 7 then reverse','a=7'])assert.throws(()=>answer(base,'affine',text));
 for(const unit of ['word','line','page']){const r=answer(selectFamily('transposition'),'reverse-'+unit);assert.deepEqual(Compiler.compile(card(r)).steps,[{op:'reverse',unit}]);unchanged(draft(),r);}
});
test('Literal repeating, plaintext/ciphertext feedback and finite streams require explicit direction and reset',()=>{
 for(const [family,mode]of [['polyalphabetic','repeating_key'],['feedback','plaintext_autokey'],['feedback','ciphertext_autokey'],['number-streams','finite_key']]){
  const base=selectFamily(family),key=answer(base,mode,'[3, 4, 7, 20]');
  assert.equal(current(key).id.split(':')[3],'direction');assert(!Object.hasOwn(key.method.value.operations[0],'direction'));
  assert.equal(key.rules.reset.status,'unspecified');assert.equal(key.rules.representation.status,'unspecified');
  const directed=answer(key,'add');assert.equal(current(directed).id.split(':')[3],'reset');
  const ready=answer(directed,'word'),op=ready.method.value.operations[0];assert.equal(op.id,mode);assert.deepEqual(op.key,[3,4,7,20]);assert.equal(op.direction,'add');assert.equal(op.reset,'word');
  assert.equal(current(ready),undefined);const compiled=Compiler.compile(card(ready));assert(!compiled.reason,compiled.reason);assert.equal(compiled.steps[0].reset,'word');unchanged(draft(),ready);
  for(const value of ['ABC','3 4','3,-1','29','3,4; then reverse','[3,4','3,'])assert.throws(()=>answer(base,mode,value));
 }
});
test('Finite domains are explicit intents, never inferred from choosing a family',()=>{
 const affine=answer(selectFamily('fixed-substitution'),'affine-all');assert.equal(affine.rules.searchBounds.status,'unspecified');
 assert(require('../affine-search-clarification.js').describe(card(affine)));
 for(const length of ['one','two']){const key=answer(selectFamily('polyalphabetic'),'keys-'+length);assert.equal(key.rules.searchBounds.status,'unspecified');assert(require('../key-alternatives-clarification.js').describe(card(key)));}
});
test('An explicitly supplied global reset is kept without asking for it again',()=>{
 for(const reset of ['word','reset at each line']){const base=selectFamily('feedback');base.rules.reset=known(reset);const selected=answer(base,'plaintext_autokey','1,2'),ready=answer(selected,'subtract');assert.equal(current(ready),undefined);assert.deepEqual(ready.rules.reset,base.rules.reset);assert(!Compiler.compile(card(ready)).reason);}
 const base=selectFamily('feedback');base.rules.reset=known('Only reset after an F rune');const selected=answer(base,'plaintext_autokey','1,2');assert(!Object.hasOwn(selected.method.value.operations[0],'reset'));const directed=answer(selected,'subtract');assert.equal(current(directed).id.split(':')[3],'reset');assert(current(directed).context.includes('separately supplied'));const ready=answer(directed,'page');assert.deepEqual(ready.rules.reset,base.rules.reset);assert(Compiler.compile(card(ready)).reason,'An incompatible original condition is not silently dropped');
});
test('Prime sums explicitly choose both tables, both word boundaries and numeric evaluation without changing aim',()=>{
 for(const table of ['canonical','reversed'])for(const boundaries of ['non-rune','hyphen-period']){
  let value=answer(selectFamily('prime-indices'),'word_prime_sums');assert.equal(current(value).id.split(':')[3],'table');
  value=answer(value,table);value=answer(value,boundaries);assert.equal(current(value).id.split(':')[3],'evaluation');
  assert.equal(value.rules.evaluation.value,'measurement','Existing evaluation is not silently replaced');
  value=answer(value,'measurement');assert.equal(current(value),undefined);unchanged(draft(),value);
  assert.deepEqual(Compiler.compile(card(value)).criterion,{kind:'word-prime-sums',table,boundaries});
  assert.equal(value.rules.representation.status,'unspecified','No representation default was recorded');
 }
});
test('Affine pair measurement asks lag, multiplier, offset and boundaries; no sweep or significance claim',()=>{
 let value=answer(selectFamily('repetition'),'word_affine_count');assert.equal(current(value).id.split(':')[3],'lag');
 for(const text of ['0','13','1.5','six'])assert.throws(()=>answer(value,'supply',text));
 value=answer(value,'supply','6');assert.equal(current(value).id.split(':')[3],'a');assert.throws(()=>answer(value,'supply','29'));
 value=answer(value,'supply','1');value=answer(value,'supply','0');value=answer(value,'hyphen-period');
 assert(current(value).context.includes('not a deciphering verdict'));value=answer(value,'measurement');
 assert.deepEqual(Compiler.compile(card(value)).criterion,{kind:'word-affine-count',lag:6,a:1,b:0,boundaries:'hyphen-period'});unchanged(draft(),value);
});
test('Existing criterion can be retained by describing a different check; supplied conditions are never erased',()=>{
 const original=selectFamily('prime-indices');original.rules.exceptionalCases=known('Do not move the F rune');original.rules.evaluation=known({kind:'exact-prefix',values:[1,2]});
 let value=answer(original,'word_prime_sums');value=answer(value,'reversed');value=answer(value,'non-rune');
 const described=answer(value,'describe','Add primes but use my exact prefix check afterward.');
 assert.deepEqual(described.rules,original.rules);assert.equal(described.method.value.operations[0].id,'described_method');assert.equal(described.source.text,source);
});
test('Revision-bound answers reject stale edits and only replace the selected sibling operation',()=>{
 let value=selectFamily('feedback');const q=current(value);value=C.revise(value,{scope:known({pages:['lp2-01']})});
 assert.throws(()=>I.answerIntake(value,q.id,'plaintext_autokey','1,2'),/changed/);
 value=selectFamily('transposition');value=C.applyMethodEdit(value,{type:'add',index:0,operation:{id:'affine',label:'Affine',a:7,b:0}});
 const ready=answer(value,'reverse-line');assert.deepEqual(ready.method.value.operations[0],{id:'affine',label:'Affine',a:7,b:0});assert.equal(ready.method.value.operations[1].unit,'line');
 const imported=selectFamily('transposition');imported.method.value.operations[0].onlyAfter='F rune';const retained=answer(imported,'reverse-word');assert.equal(retained.method.value.operations[0].onlyAfter,'F rune');assert(Compiler.compile(card(retained)).reason,'Unknown supplied parameters must refuse rather than disappear');
});
test('Shared cards recover family and missing key choices without draft-only history',()=>{
 for(const original of [selectFamily('feedback'),answer(selectFamily('feedback'),'plaintext_autokey','1,2')]){
  const shared=H.decode(H.encode(C.confirm(original,{id:'private',at:'2026-10-25T12:00:00Z'}))).draft;
  assert(current(shared));let complete=original.method.value.operations[0].id==='family_selection'?answer(shared,'ciphertext_autokey','1,2'):shared;
  complete=answer(answer(complete,'subtract'),'page');assert.equal(current(complete),undefined);assert(!Compiler.compile(card(complete)).reason);
 }
});

test('Contradictory supplied operation and global reset remain active instead of silently selecting one',()=>{let value=selectFamily('polyalphabetic');value.method.value.operations[0].reset='word';value=C.revise(value,{rules:{reset:known('page')}});value=answer(value,'repeating_key','1,2');assert.equal(value.method.value.operations[0].reset,'word');assert.equal(value.rules.reset.value,'page');value=answer(value,'subtract');assert.equal(current(value),undefined);assert(Compiler.compile(card(value)).reason,'The incompatible preserved reset conditions must refuse execution');});

class Element{constructor(){this.listeners={};this.value='';this.html='';}addEventListener(t,f){this.listeners[t]=f;}fire(t){return this.listeners[t]?.({preventDefault(){},target:this});}focus(){}replaceChildren(){this.html='';}set innerHTML(v){this.html=v;this.onRender?.();}get innerHTML(){return this.html;}insertAdjacentHTML(_,v){this.html+=v;}}
function documentFor(hash,session){const host=new Element(),cache=new Map();host.onRender=()=>cache.clear();return {host,selectedChoice:null,defaultView:{location:{search:'',hash},sessionStorage:session},getElementById(id){if(id==='investigate')return host;if(id==='print-snapshot')return new Element();if(!host.html.includes('id="'+id+'"'))return null;if(!cache.has(id))cache.set(id,new Element());return cache.get(id);},querySelector(s){return s==='input[name=choice]:checked'?(this.selectedChoice?{value:this.selectedChoice}:null):s.startsWith('#')?this.getElementById(s.slice(1)):null;}};}
async function ui(){
 const memory=new Map(),session={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)},original=selectFamily('feedback'),hash=H.encode(C.confirm(original,{id:'private',at:'2026-10-25T12:00:00Z'})),requests=[];
 async function mount(){const doc=documentFor(hash,session),app=I.createApp(doc,{fetcher:async(url,options)=>{requests.push({url,method:options?.method||'GET'});if(options?.method==='POST')throw Error('No service write allowed');if(url==='data/experiments.json')return Response.json(JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8')));if(url==='data/assistant.json')return Response.json({});return Response.json({documents:[]});}});await app.ready;return {doc,app};}
 function choose(f,choice,text=''){f.doc.selectedChoice=choice;if(f.doc.getElementById('other-detail'))f.doc.getElementById('other-detail').value=text;f.doc.getElementById('clarification').fire('submit');}
 let f=await mount();assert(f.doc.host.html.includes('Which specific method'));assert.equal(f.doc.getElementById('confirm'),null);
 const oldForm=f.doc.getElementById('clarification');choose(f,'plaintext_autokey','3,4');assert(f.doc.host.html.includes('How should the key indices'));
 const before=f.app.getSnapshot().draft;f.doc.selectedChoice='subtract';oldForm.fire('submit');assert.deepEqual(f.app.getSnapshot().draft,before,'Detached stale form cannot answer a newer question');
 f.app.destroy();f=await mount();assert(f.doc.host.html.includes('How should the key indices'),'Recovery resumes the essential choice');
 choose(f,'subtract');assert(f.doc.host.html.includes('When should the key restart'));choose(f,'line');assert(f.doc.getElementById('confirm'));assert.equal(f.app.getSnapshot().confirmed,null);
 const complete=f.app.getSnapshot().draft;f.doc.getElementById('edit').fire('click');f.doc.getElementById('cancel-edit').fire('click');assert.deepEqual(f.app.getSnapshot().draft,complete);
 assert(requests.every(r=>r.method==='GET'));f.doc.getElementById('back').fire('click');assert(f.doc.getElementById('idea'));f.app.destroy();
 groups++;console.log('PASS actual intake DOM events, edit/cancel, recovery, back and no service writes before explicit confirmation');
}
ui().then(()=>console.log('PASS '+groups+' family-method intake groups')).catch(error=>{console.error(error);process.exitCode=1;});
