'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto}=require('node:crypto');
const P=require('../experiment-protocols.js'),E=require('../local-experiment.js'),V=require('../task-variants.js');
const alphabet=JSON.parse(fs.readFileSync('data/index.json','utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
let checked=0;
function check(c){
 const saved=structuredClone(c),def=P.identify(c),d=P.describe(c);assert(def);assert.equal(d.id,c.kind);assert.equal(d.operationId,def.operation.id);assert(d.heading&&d.question&&d.review&&d.reviewBoundary&&d.plan&&d.limit&&d.compilerNote);assert.equal(d.heading,c.kind==='word-prime-sums'?'Adding rune values within words':`Rune pairs ${c.lag} positions apart`);assert(!d.heading.includes('hyphen-period'));assert(!d.heading.includes(' · '));assert.equal(d.settings.length,Object.keys(def.fields).length);
 const op={id:def.operation.id,label:def.operation.label};for(const k of Object.keys(def.fields))op[k]=c[k];assert.deepEqual(P.fromOperation(op),c);
 if(!def.operation.labelRequired){delete op.label;assert.deepEqual(P.fromOperation(op),c);}else{delete op.label;assert.equal(P.fromOperation(op),null);}
 assert.equal(P.fromOperation({...op,extra:true}),null);assert.equal(P.fromOperation({...op,declaredFamilyId:'word-structure'}),null);assert.equal(P.fromOperation({...op,label:'Other'}),null);
 assert.deepEqual(P.variant(P.variant(c,'word-boundaries'),'word-boundaries'),c);assert.equal(P.variant(c,'arbitrary'),null);assert.deepEqual(c,saved);checked++;
}
(async()=>{
 for(const table of ['canonical','reversed'])for(const boundaries of ['non-rune','hyphen-period']){
  const c={kind:'word-prime-sums',table,boundaries};check(c);assert.equal(P.describe(c).title,`Word prime sums · ${table} table · ${boundaries}`);
 }
 for(const lag of [1,12])for(const a of [0,28])for(const b of [0,28])for(const boundaries of ['non-rune','hyphen-period']){
  const c={kind:'word-affine-count',lag,a,b,boundaries};check(c);assert.equal(P.describe(c).title,`Within-word rune pairs · lag ${lag} · ${boundaries}`);
 }
 const base={kind:'word-affine-count',lag:6,a:27,b:24,boundaries:'non-rune'};
 for(const invalid of [null,[],{},'word-prime-sums',{kind:'measurement'},{...base,extra:1},{...base,lag:0},{...base,lag:13},{...base,lag:1.5},{...base,lag:'6'},{...base,a:-1},{...base,a:29},{...base,b:NaN},{...base,b:Infinity},{...base,b:null},{...base,b:undefined},{...base,boundaries:'space'}, {kind:'word-prime-sums',table:'normal',boundaries:'non-rune'}, {kind:'word-prime-sums',table:'reversed'}]){
  assert.equal(P.identify(invalid),null);assert.equal(P.describe(invalid),null);assert.equal(P.variant(invalid,'word-boundaries'),null);
 }
 for(const key of ['lag','a','b'])for(const value of [-1,29,0.5,'1',null,undefined,NaN,Infinity])assert.equal(P.identify({...base,[key]:value}),null);
 const hostContext=vm.createContext({});const cross=vm.runInContext("({kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'})",hostContext);assert(P.describe(cross));
 assert.deepEqual(P.fromOperation(vm.runInContext("({id:'word_affine_count',lag:6,a:27,b:24,boundaries:'non-rune'})",hostContext)),base);
 assert.equal(P.identify(new (class {constructor(){Object.assign(this,base);}})()),null);
 assert.equal(P.identify(Object.assign(Object.create({}),base)),null);
 const getter={...base};Object.defineProperty(getter,'lag',{enumerable:true,get(){throw Error('Getter must not run');}});assert.equal(P.identify(getter),null);
 const symbolic={...base,[Symbol('extra')]:true};assert.equal(P.describe(symbolic),null);assert.equal(P.fromOperation({id:'word_affine_count',...base}),null);
 const definitions=P.list();definitions[0].fields.table.values.push('fake');definitions[0].operation.id='fake';P.identify(base).fields.lag.max=999;P.describe(base).settings[0].value=999;assert.equal(P.list()[0].operation.id,'word_prime_sums');assert.equal(P.identify(base).fields.lag.max,12);
 for(const c of [{kind:'word-prime-sums',table:'reversed',boundaries:'hyphen-period'},base]){
  const parent=await E.prepare({title:'Any parent title',pages:[{id:'lp2-15',text:'ᚠᚢ /\r\nᛠ-ᚠᚢ.ᛠ'}],alphabet,steps:[],criterion:c},webcrypto),criterion={...c,boundaries:c.boundaries==='non-rune'?'hyphen-period':'non-rune'};
  const oldTitle=c.kind==='word-prime-sums'?`Word prime sums · ${c.table} table · ${criterion.boundaries}`:`Within-word rune pairs · lag ${c.lag} · ${criterion.boundaries}`;
  const legacy=await E.prepare({...parent,title:oldTitle,criterion},webcrypto),actual=await V.prepare(parent,webcrypto);assert.deepEqual(actual,legacy);assert.equal(actual.taskId,legacy.taskId);
 }
 const ctx={};vm.createContext(ctx);vm.runInContext(fs.readFileSync('experiment-protocols.js','utf8'),ctx);assert.equal(vm.runInContext("ExperimentProtocols.describe({kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'}).title",ctx),'Word prime sums · reversed table · non-rune');
 console.log('PASS '+checked+' protocol enum/integer combinations, strict malformed rejection, cloned metadata, browser export and unchanged full variant identities');
})().catch(e=>{console.error(e);process.exitCode=1;});
