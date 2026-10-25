/* The finite compiler preserves one original idea and reuses fixed program semantics. */
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import C from '../claim-specification.js';
import H from '../claim-share.js';
import E from '../local-experiment.js';
import Questions from '../finite-program-question.js';
import {compileFiniteSearch} from '../services/idea-assistant/finite-search-plans.mjs';
const clone=value=>JSON.parse(JSON.stringify(value));
const specified=value=>({status:'specified',value});
const known=value=>C.field('specified',value,{kind:'supplied',refs:['visitor:original']});
const alphabet=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
function bundle(){return {schema:'liberpedia-local-inputs-v1',alphabet:clone(alphabet),pages:[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))].map(id=>({id,raw:'ᚠᚢ ᚦ\nᚩᚱ',reviewed_text:id==='lp2-15'?'ᚢᚠ ᚦ\nᚩᚱ':null}))};}
function card(){return H.cardData(C.confirm(C.createDraft({source:{text:'Try the explicit affine settings against this exact opening.'},aim:known('Solve LP2'),method:known({operations:[{id:'affine',label:'Affine substitution'}]}),scope:known({pages:['lp2-15','lp2-16']}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[0,1]}),searchBounds:known({kind:'finite-settings',version:1,parameters:[{operation:0,name:'a',values:[1,28]},{operation:0,name:'b',values:[0,1]}]})}}),{id:'visitor',at:'2026-10-25T12:00:00.000Z'}));}
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('every declared setting compiles through the existing fixed compiler; original card and source remain unchanged',async()=>{
 const input=card(),source=bundle(),before=clone({input,source}),out=await compileFiniteSearch(input,source,webcrypto);
 assert.equal(out.declaration.programCount,4);assert.equal(out.domain.totalCases,8);assert.equal(out.members.length,4);assert.deepEqual({input,source},before);assert(Object.isFrozen(out));
 for(const member of out.members){const expected=Object.fromEntries(member.settings.map(s=>[s.name,s.value])),program=out.domain.programs.find(p=>p.id===member.programId);assert(program);assert.deepEqual(program.task.steps,[{op:'affine',a:expected.a,b:expected.b}]);assert.deepEqual(program.task.criterion,{kind:'exact-prefix',values:[0,1]});}
});
await test('finite identity reuses exact computation across reordered axes and different aims',async()=>{
 const left=card(),right=clone(left);right.rules.searchBounds.value.parameters.reverse();right.rules.searchBounds.value.parameters.forEach(axis=>axis.values.reverse());right.outcome={...right.outcome,value:{outcomeId:'reproduce',detail:'Reproduce a result'}};
 const a=await compileFiniteSearch(left,bundle(),webcrypto),b=await compileFiniteSearch(right,bundle(),webcrypto);assert.equal(a.domain.id,b.domain.id);
});
await test('common source version and exact evaluation cannot be guessed or silently changed',async()=>{
 for(const change of [c=>c.rules.inputVersion={status:'unspecified'},c=>c.rules.evaluation=specified('measurement'),c=>c.rules.inputVersion=specified('reviewed'),c=>c.rules.searchProtocol=specified('Ignore failures and keep trying')]){const input=card();change(input);await assert.rejects(()=>compileFiniteSearch(input,bundle(),webcrypto));}
 const input=card();input.scope=specified({pages:['lp2-15']});input.rules.inputVersion=specified('reviewed');const out=await compileFiniteSearch(input,bundle(),webcrypto);assert.equal(out.domain.inputVersion,'reviewed');assert.equal(out.domain.programs[0].task.pages[0].text,'ᚢᚠ ᚦ\nᚩᚱ');
});
await test('one invalid member rejects the entire declaration before producing runnable work',async()=>{
 const input=card();input.rules.searchBounds.value.parameters[0].values=[1,29];await assert.rejects(()=>compileFiniteSearch(input,bundle(),webcrypto),/adapter|indices|setting/i);
 const incompatible=card();incompatible.rules.searchBounds.value.parameters.push({operation:0,name:'reset',values:['page','line']});await assert.rejects(()=>compileFiniteSearch(incompatible,bundle(),webcrypto),/adapter|affine|parameter/i);
});
await test('812 explicit affine programs fit one pinned question without executing a manuscript target',async()=>{
 const input=card();input.scope=specified({pages:['lp2-15']});input.rules.searchBounds.value.parameters[0].values=Array.from({length:28},(_,i)=>i+1);input.rules.searchBounds.value.parameters[1].values=Array.from({length:29},(_,i)=>i);
 const run=E.run;E.run=()=>{throw Error('Compilation must not execute manuscript targets');};try{const out=await compileFiniteSearch(input,bundle(),webcrypto);assert.equal(out.domain.totalCases,812);assert.equal(out.declaration.programCount,812);assert.equal(Questions.inspect(out.domain).totalCases,812);}finally{E.run=run;}
});
await test('oversized complete declarations fail before task creation instead of truncating the search',async()=>{
 const input=card(),source=bundle();input.rules.searchBounds.value.parameters[0].values=[1,2,3,4];source.pages.find(p=>p.id==='lp2-15').raw='ᚠ'.repeat(300000);await assert.rejects(()=>compileFiniteSearch(input,source,webcrypto),/budget/);
});
await test('JSON capture rejects accessors and serialization hooks before they can execute',async()=>{
 for(const target of ['card-object','card-array','bundle-object','bundle-array','toJSON','undefined','sparse']){
  const input=card(),source=bundle();let calls=0;
  if(target==='card-object')Object.defineProperty(input.rules.searchBounds.value,'parameters',{enumerable:true,get(){calls++;return [];}});
  if(target==='card-array')Object.defineProperty(input.rules.searchBounds.value.parameters[0].values,'0',{enumerable:true,get(){calls++;return 1;}});
  if(target==='bundle-object')Object.defineProperty(source.pages[0],'raw',{enumerable:true,get(){calls++;return '';}});
  if(target==='bundle-array')Object.defineProperty(source.pages,'0',{enumerable:true,get(){calls++;return null;}});
  if(target==='toJSON')input.toJSON=()=>{calls++;return card();};
  if(target==='undefined')input.method.value.operations[0].ignored=undefined;
  if(target==='sparse')delete source.pages[0];
  await assert.rejects(()=>compileFiniteSearch(input,source,webcrypto),/data|JSON|fields|dense/);assert.equal(calls,0,target);
 }
});
await test('inputs are detached before the first digest so callers cannot change a pending domain',async()=>{
 const input=card(),source=bundle();let release,started=false;const gate=new Promise(resolve=>release=resolve),crypto={subtle:{async digest(...args){if(!started){started=true;await gate;}return webcrypto.subtle.digest(...args);}}};
 const pending=compileFiniteSearch(input,source,crypto);assert(started);input.rules.searchBounds.value.parameters[0].values=[3];input.scope.value.pages=['lp2-00'];source.pages.find(p=>p.id==='lp2-15').raw='changed after capture';source.alphabet[0].rune='!';release();
 const out=await pending;assert.equal(out.declaration.programCount,4);assert.equal(out.domain.totalCases,8);assert(out.domain.programs.every(p=>p.task.pages[0].id==='lp2-15'&&p.task.pages[0].text==='ᚠᚢ ᚦ\nᚩᚱ'&&p.task.alphabet[0].rune==='ᚠ'));
});
console.log(groups+' finite search compiler groups passed');
