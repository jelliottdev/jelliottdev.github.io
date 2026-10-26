'use strict';
/* Lossless storage checks only; no controls or manuscript programs are executed. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),S=require('../finite-control-storage.js'),E=require('../local-experiment.js');
const copy=structuredClone,bytes=v=>Buffer.byteLength(JSON.stringify(v)),stable=E.stable,records=[];
for(const folder of fs.readdirSync('experiments/records')){const path='experiments/records/'+folder+'/record.json';if(fs.existsSync(path)){const record=JSON.parse(fs.readFileSync(path,'utf8'));for(const recipe of record.browser_followups||[])if(recipe.kind==='finite-settings')records.push({recordId:record.id,id:recipe.id,control:S.expand(recipe.control)});}}
assert.equal(records.length,15,'Exercise all fifteen maintained finite recipes');const sample=records.find(r=>r.control.members.length===54).control;
let groups=0;function test(name,fn){fn();groups++;console.log('PASS '+name);}
test('all fifteen real finite control sets round trip exact stable JSON without execution or mutation',()=>{
 const run=E.run;E.run=()=>assert.fail('Storage codec must never execute a control');try{for(const entry of records){const before=stable(entry.control),out=S.compact(entry.control);assert.equal(out.kind,'finite-program-controls-shared-v1');assert.equal(stable(S.expand(out)),before);assert.equal(stable(entry.control),before);assert.equal(stable(S.compact(out)),stable(out));assert.deepEqual(Object.keys(out).sort(),['alphabet','criterion','kind','members']);assert(out.members.every(m=>!Object.hasOwn(m.control.task,'alphabet')&&!Object.hasOwn(m.control.task,'criterion')));}}finally{E.run=run;}
});
test('representative large families shrink at least35 percent and remain fully detached',()=>{
 for(const entry of records.filter(r=>r.control.members.length>=42)){const compact=S.compact(entry.control);assert(bytes(compact)<=bytes(entry.control)*.65,entry.id+' storage reduction');}
 const original=copy(sample),compact=S.compact(original),before=stable(compact);original.members[0].control.task.alphabet[0].latin='CHANGED';assert.equal(stable(compact),before);
 const expanded=S.expand(compact);expanded.members[0].control.task.alphabet[0].latin='ALTERED';assert.equal(stable(compact),before);assert.notEqual(expanded.members[0].control.task.alphabet[0].latin,expanded.members[1].control.task.alphabet[0].latin,'Expanded members do not share mutable alphabet aliases');
});
test('nonshared alphabet or criterion and extra legacy fields remain lossless for existing validators',()=>{
 for(const mutate of [v=>v.members[1].control.task.alphabet[0].latin='different',v=>v.members[1].control.task.criterion.values[0]=0,v=>v.extra='preserve me',v=>v.members[0].control.task.extra='preserve task field',v=>v.members[0].control.task.criterion={kind:'measurement'}]){const value=copy(sample);mutate(value);const before=stable(value),compact=S.compact(value);assert.equal(compact.kind,'finite-program-controls');assert.equal(stable(compact),before);assert.equal(stable(S.expand(value)),before);assert.notEqual(compact,value);}
 const fake=copy(sample);fake.members[0].control.expected_result_sha256='0'.repeat(64);assert.equal(S.expand(S.compact(fake)).members[0].control.expected_result_sha256,'0'.repeat(64),'Storage cannot certify a scientific result');
});
test('compact envelope, members, controls and tasks reject extra or ambiguous shared fields',()=>{
 const compact=S.compact(sample);
 for(const mutate of [v=>v.extra=1,v=>v.members[0].extra=1,v=>v.members[0].control.extra=1,v=>v.members[0].control.task.extra=1,v=>v.members[0].control.task.alphabet=v.alphabet,v=>v.members[0].control.task.criterion=v.criterion,v=>v.criterion.extra=true,v=>v.members[0].settings[0].extra=1,v=>v.members[0].control.task.pages[0].extra=1,v=>v.alphabet[0].extra=1]){const bad=copy(compact);mutate(bad);assert.throws(()=>S.expand(bad));assert.throws(()=>S.compact(bad));}
 for(const kind of ['finite-program-controls-shared-v2','finite-program-controls-shared']){assert.throws(()=>S.expand({...compact,kind}));assert.throws(()=>S.compact({...compact,kind}));}
});
test('shared cardinality and typed structure bounds reject malformed compact data',()=>{
 const compact=S.compact(sample);
 for(const mutate of [v=>v.members=[],v=>v.members=Array.from({length:1025},()=>v.members[0]),v=>v.alphabet.pop(),v=>v.alphabet[0].rune='ab',v=>v.alphabet[0].latin='',v=>v.alphabet[0].prime=0,v=>v.criterion.kind='language-score',v=>v.criterion.values=[],v=>v.criterion.values=Array(257).fill(0),v=>v.criterion.values[0]=29,v=>v.criterion.values[0]=.5,v=>v.members[0].control.task.taskId='invalid',v=>v.members[0].control.expected_result_sha256='invalid',v=>v.members[0].control.task.pages=[],v=>v.members[0].control.task.steps=Array(9).fill({}),v=>v.members[0].settings[0].operation=8]){const bad=copy(compact);mutate(bad);assert.throws(()=>S.expand(bad));}
});
test('accessors, custom prototypes, symbols, sparse arrays and serialization hooks are rejected without invocation',()=>{
 let calls=0;const getter=copy(sample);Object.defineProperty(getter.members[0].control.task,'alphabet',{enumerable:true,get(){calls++;return sample.members[0].control.task.alphabet;}});
 const compact=S.compact(sample),nestedGetter=copy(compact);Object.defineProperty(nestedGetter,'kind',{enumerable:true,get(){calls++;return compact.kind;}});
 const hook={kind:'finite-program-controls',members:[],toJSON(){calls++;return {};}};
 for(const value of [getter,nestedGetter,hook,Object.assign(Object.create({inherited:true}),compact),{...compact,members:Array(2)},{...compact,[Symbol('hidden')]:1}]){assert.throws(()=>S.expand(value));assert.throws(()=>S.compact(value));}assert.equal(calls,0);
});
test('input and expanded output obey twoMiB, depth and node budgets',()=>{
 const compact=S.compact(sample);assert.throws(()=>S.expand({...compact,padding:'x'.repeat(2*1024*1024)}),/byte bound/);
 let deep={};for(let i=0;i<30;i++)deep={next:deep};assert.throws(()=>S.compact({kind:'finite-program-controls',members:[],deep}),/depth/);
 assert.throws(()=>S.expand({kind:'finite-program-controls',members:Array.from({length:300001},()=>0)}),/node|bounded/);
 const expanded=copy(compact);expanded.members=Array.from({length:900},()=>copy(compact.members[0]));for(const member of expanded.members)member.control.task.pages[0].text='x'.repeat(900);assert(bytes(expanded)<2*1024*1024);assert.throws(()=>S.expand(expanded),/byte bound/,'Sharing does not remove expanded-output resource limits');
});
test('browser UMD exposes identical detached compact and legacy representations',()=>{
 const context=vm.createContext({TextEncoder});vm.runInContext(fs.readFileSync('finite-json.js','utf8'),context);vm.runInContext(fs.readFileSync('finite-control-storage.js','utf8'),context);assert.equal(typeof context.FiniteControlStorage.compact,'function');
 const compact=context.FiniteControlStorage.compact(sample);assert.equal(stable(compact),stable(S.compact(sample)));assert.equal(stable(context.FiniteControlStorage.expand(compact)),stable(sample));assert.equal(stable(sample),stable(records.find(r=>r.control.members.length===54).control));
});
console.log(groups+' lossless finite-control storage groups passed; no task execution or scientific validation is replaced.');
