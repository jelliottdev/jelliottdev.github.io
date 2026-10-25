/* Finite declarations materialize ordinary cards; they do not supply execution authority. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),F=require('../finite-settings.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const clone=v=>JSON.parse(JSON.stringify(v)),at='2026-10-25T12:00:00.000Z',known=value=>C.field('specified',value,{kind:'supplied',refs:['original:finite-settings']});
function card({operations=[{id:'affine',label:'Affine'}],parameters=[{operation:0,name:'a',values:[2,1]},{operation:0,name:'b',values:[1,0]}],pages=['lp2-15'],aim='Solve LP2'}={}){
 return H.cardData(C.confirm(C.createDraft({source:{text:'Explicit finite alternatives supplied by the visitor.'},aim:known(aim),method:known({operations}),scope:known({pages}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known({kind:'exact-prefix',values:[24,7]}),searchBounds:known({kind:'finite-settings',version:1,parameters})}}),{id:'original',at}));
}
let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
(async()=>{
 const {planCard}=await import('../services/idea-assistant/prepare-task.mjs');
 await test('canonical Cartesian order preserves original card and supplies only declared missing fields',()=>{
  const original=card(),before=clone(original),expanded=F.expand(original);assert.deepEqual(expanded.declaration,{kind:'finite-settings',version:1,parameters:[{operation:0,name:'a',values:[1,2]},{operation:0,name:'b',values:[0,1]}],programCount:4,caseCount:4});assert.deepEqual(F.inspect(original),expanded.declaration);
  assert.deepEqual(expanded.variants.map(v=>v.settings.map(s=>s.value)),[[1,0],[1,1],[2,0],[2,1]]);assert.deepEqual(original,before);
  for(const member of expanded.variants){const expected=clone(original);expected.rules.searchBounds={status:'not_applicable'};for(const s of member.settings)expected.method.value.operations[s.operation][s.name]=s.value;assert.deepEqual(member.card,expected);const compiled=planCard(member.card);assert(!compiled.reason);assert.deepEqual(compiled.steps,[{op:'affine',a:member.settings[0].value,b:member.settings[1].value}]);}
  assert(Object.isFrozen(expanded));assert(Object.isFrozen(expanded.declaration.parameters[0].values));assert(Object.isFrozen(expanded.variants[0].card.method.value.operations[0]));assert.throws(()=>{expanded.variants[0].card.method.value.operations[0].a=25;},TypeError);
 });
 await test('key, arithmetic, reset and reversal alternatives use the same general fixed-plan compiler',()=>{
  const original=card({operations:[{id:'repeating_key',label:'Repeating key'},{id:'reverse_runes'}],parameters:[{operation:1,name:'unit',values:['word','line']},{operation:0,name:'reset',values:['word','page']},{operation:0,name:'direction',values:['subtract','add']},{operation:0,name:'key',values:[[3,1],[1,3]]}],pages:['lp2-15','lp2-16']}),before=clone(original),expanded=F.expand(original);assert.equal(expanded.declaration.programCount,16);assert.equal(expanded.declaration.caseCount,32);
  for(const v of expanded.variants){const p=planCard(v.card);assert(!p.reason);assert.equal(p.steps[0].op,'keyed-shift');assert.equal(p.steps[1].op,'reverse');assert.deepEqual(p.criterion,original.rules.evaluation.value);assert.deepEqual(p.pages,original.scope.value.pages);assert.equal(p.inputVersion,'raw');}
  assert.deepEqual(expanded.declaration.parameters.find(p=>p.name==='key').values,[[1,3],[3,1]]);assert.notEqual(expanded.variants[0].card.method.value.operations[0].key,expanded.variants[1].card.method.value.operations[0].key);assert.deepEqual(original,before);
 });
 await test('axis and alternative enumeration order do not alter the semantic declaration or expanded programs',()=>{
  const a=card(),b=clone(a);b.rules.searchBounds.value.parameters.reverse();b.rules.searchBounds.value.parameters.forEach(p=>p.values.reverse());assert.deepEqual(F.inspect(a),F.inspect(b));assert.deepEqual(F.expand(a),F.expand(b));
 });
 await test('one bounded member has exactly the same canonical card and settings as expansion',()=>{
  const original=card(),expanded=F.expand(original),before=clone(original);
  for(const variant of expanded.variants){const selected=F.member(original,variant.settings.slice().reverse());assert.deepEqual(selected,{declaration:expanded.declaration,...variant});assert(Object.isFrozen(selected.settings));assert(Object.isFrozen(selected.card));}
  assert.deepEqual(original,before);
  const keyed=card({operations:[{id:'repeating_key',direction:'subtract',reset:'word'}],parameters:[{operation:0,name:'key',values:[[1,2],[2,1]]}]});const chosen=F.member(keyed,[{operation:0,name:'key',value:[2,1]}]);assert.deepEqual(chosen.card.method.value.operations[0].key,[2,1]);assert(!planCard(chosen.card).reason);
 });
 await test('member admission rejects missing, extra, duplicate, malformed and undeclared assignments',()=>{
  const original=card(),settings=[{operation:0,name:'a',value:1},{operation:0,name:'b',value:0}];
  for(const change of [x=>x.pop(),x=>x.push({operation:0,name:'reset',value:'page'}),x=>x[1]=clone(x[0]),x=>x[0].value=28,x=>x[0].operation='0',x=>x[0].operation=1,x=>x[0].name='label',x=>x[0].extra=true,x=>{Object.defineProperty(x[0],'value',{enumerable:true,get(){throw Error('Do not execute accessors');}});},x=>{delete x[0];}]){const value=clone(settings);change(value);assert.throws(()=>F.member(original,value));}
  const fixed=card();fixed.method.value.operations[0].a=1;assert.throws(()=>F.member(fixed,settings),/supplied fixed/);
 });
 await test('closed schema, duplicate declarations and supplied fixed parameters are rejected',()=>{
  for(const change of [c=>c.rules.searchBounds.value.extra=true,c=>c.rules.searchBounds.value.version=2,c=>c.rules.searchBounds.value.kind='all-affine',c=>c.rules.searchBounds.value.parameters=[],c=>c.rules.searchBounds.value.parameters.push(clone(c.rules.searchBounds.value.parameters[0])),c=>c.rules.searchBounds.value.parameters[0].values.push(1),c=>c.rules.searchBounds.value.parameters[0].range=[0,28],c=>c.rules.searchBounds.value.parameters[0].operation=1,c=>c.rules.searchBounds.value.parameters[0].operation=.5,c=>c.rules.searchBounds.value.parameters[0].name='label',c=>c.method.value.operations[0].a=1,c=>c.scope.value.description='a passage',c=>c.scope.value.pages=[],c=>c.rules.searchBounds={status:'unrestricted'}]){const value=card();change(value);assert.throws(()=>F.expand(value));}
  assert.throws(()=>F.expand(card({operations:[{id:'repeating_key',key:[1,2]}],parameters:[{operation:0,name:'key',values:[[1,2]]}]})),/supplied fixed/);
 });
 await test('only bounded literal values are accepted, while operation compatibility remains compiler-owned',()=>{
  for(const [name,values] of [['a',[-1]],['b',[29]],['a',[1.5]],['direction',['beaufort']],['reset',['sentence']],['unit',['paragraph']],['key',[[]]],['key',[[29]]],['key',[[1],[1]]],['interrupts',[[2,1]]],['interrupts',[[1,1]]]])assert.throws(()=>F.inspect(card({parameters:[{operation:0,name,values}]})),name);
  const unsupported=F.expand(card({operations:[{id:'reverse_runes',unit:'line'}],parameters:[{operation:0,name:'a',values:[1,2]}]}));assert.equal(unsupported.variants.length,2);for(const v of unsupported.variants)assert(planCard(v.card).reason,'Pure expansion must not invent compatibility or authorize an unsupported parameter');
  const interrupted=F.expand(card({operations:[{id:'interrupted_repeating_key',label:'Interrupted repeating key',key:[1],direction:'subtract',reset:'page'}],parameters:[{operation:0,name:'interrupts',values:[[2,4],[1]]}]}));for(const v of interrupted.variants)assert(!planCard(v.card).reason);
 });
 await test('program and page-case limits reject rather than truncate, including exact boundary',()=>{
  const numbers=n=>Array.from({length:n},(_,i)=>i),parameters=[{operation:0,name:'a',values:numbers(8)},{operation:0,name:'b',values:numbers(8)},{operation:1,name:'a',values:numbers(4)},{operation:1,name:'b',values:numbers(4)}],operations=[{id:'affine'},{id:'affine'}],exact=card({operations,parameters,pages:['lp2-00','lp2-01','lp2-02','lp2-03']});assert.equal(F.inspect(exact).programCount,1024);assert.equal(F.inspect(exact).caseCount,4096);
  const tooManyPages=clone(exact);tooManyPages.scope.value.pages.push('lp2-04');assert.throws(()=>F.expand(tooManyPages),/4096/);
  assert.throws(()=>F.inspect(card({operations:[{id:'affine'},{id:'affine',b:0}],parameters:[{operation:0,name:'a',values:numbers(29)},{operation:0,name:'b',values:numbers(29)},{operation:1,name:'a',values:[1,2]}]})),/1024/);
  const original=H.cardData;let calls=0;H.cardData=(...args)=>{calls++;return original(...args);};try{const chosen=F.member(exact,[{operation:1,name:'b',value:3},{operation:0,name:'b',value:7},{operation:1,name:'a',value:2},{operation:0,name:'a',value:6}]);assert.equal(chosen.declaration.programCount,1024);assert.equal(chosen.declaration.caseCount,4096);assert.equal(chosen.card.method.value.operations[1].a,2);assert(calls<=3,'Selecting one member must not allocate or normalize 1024 variants');}finally{H.cardData=original;}
 });
 await test('large finite domains are size-checked before allocating all detached cards',()=>{
  const values=n=>Array.from({length:n},(_,i)=>i),large=card({aim:'x'.repeat(8000),operations:[{id:'affine'},{id:'affine'}],parameters:[{operation:0,name:'a',values:values(8)},{operation:0,name:'b',values:values(8)},{operation:1,name:'a',values:values(4)},{operation:1,name:'b',values:values(4)}]}),original=H.cardData;let normalizations=0;H.cardData=(...args)=>{normalizations++;return original(...args);};try{assert.throws(()=>F.expand(large),/8 MiB/);assert(normalizations<=2,'Reject the upper-bound estimate before creating the Cartesian members');}finally{H.cardData=original;}
 });
 await test('non-JSON objects, accessors, sparse arrays and mutable source aliases cannot cross the boundary',()=>{
  for(const make of [()=>{const c=card();Object.defineProperty(c.rules.searchBounds.value,'parameters',{get(){throw Error('Getter must never run');},enumerable:true});return c;},()=>{const c=card();c.rules.searchBounds.value.parameters[0].values=[,1];return c;},()=>{const c=card();c.rules.searchBounds.value.parameters[0].values.extra=1;return c;},()=>{const c=card();c.rules.searchBounds.value.parameters[0].values[0]=NaN;return c;},()=>{const c=card();c.rules.searchBounds.value.parameters[0].values[0]=new Date();return c;},()=>{const c=card();c[Symbol('hidden')]=1;return c;}])assert.throws(()=>F.inspect(make()));
  const input=card(),before=F.expand(input);input.method.value.operations[0].label='Changed';input.rules.searchBounds.value.parameters[0].values[0]=28;assert.equal(before.variants[0].card.method.value.operations[0].label,'Affine');assert.deepEqual(before.declaration.parameters[0].values,[1,2]);
 });
 await test('browser UMD export shares the same immutable declaration without requiring an engine',()=>{
  const context=vm.createContext({ClaimSpecification:C,ClaimShare:H,TextEncoder,btoa,atob,cardJSON:JSON.stringify(card())});vm.runInContext(fs.readFileSync('finite-settings.js','utf8'),context);const answer=vm.runInContext('FiniteSettings.inspect(JSON.parse(cardJSON))',context);assert.deepEqual(clone(answer),F.inspect(card()));assert(Object.isFrozen(answer));assert(!Object.hasOwn(context,'LocalExperiment'));
 });
 console.log(groups+' finite settings groups passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
