'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const V=require('../protocol-example-view.js');
const alphabet=require('../data/index.json').alphabet,original=JSON.stringify(alphabet);
const base={kind:'word-affine-count',lag:1,a:1,b:0,boundaries:'non-rune'};
let checked=0;
for(const lag of [1,12])for(let a=0;a<29;a++)for(let b=0;b<29;b++){
 const criterion={...base,lag,a,b},saved=JSON.stringify(criterion),html=V.render({criterion,alphabet}),later=(a+b)%29;
 if(a===1&&b===0){
  assert.equal((html.match(new RegExp(alphabet[1].rune,'g'))||[]).length,2,'The equality example shows the same actual rune at both ends');
  assert(html.includes(`same rune appears ${lag} position${lag===1?'':'s'} ahead inside the same word, count one match`));
  assert(!/index|mod 29|×/.test(html),'Equality needs no index or modular-arithmetic lesson');
 }else{
  assert(html.includes(`(${a} × 1 + ${b}) mod 29 = ${later}`));
  assert(html.includes(`${alphabet[later].rune}</span><small>index ${later}</small>`));
  assert(html.includes(`rune ${lag} position${lag===1?'':'s'} ahead in the same word has index ${later}, count one match`));
 }
 assert(html.includes(lag===1?'Adjacent runes':'11 intervening runes'));
 assert(html.includes('not manuscript evidence'));assert(!html.includes('<details'));
 assert.equal(JSON.stringify(criterion),saved);checked++;
}
for(let lag=1;lag<=12;lag++)for(const boundaries of ['non-rune','hyphen-period']){
 const html=V.render({criterion:{...base,lag,boundaries},alphabet});
 assert(html.includes('count one match'));assert(!/index|mod 29|×/.test(html));
 assert(html.includes(lag===1?'Adjacent runes':`${lag-1} intervening rune${lag===2?'':'s'}`));
}
for(const table of ['canonical','reversed'])for(const boundaries of ['non-rune','hyphen-period']){
 const html=V.render({criterion:{kind:'word-prime-sums',table,boundaries},alphabet});
 const primes=table==='canonical'?[2,3,5]:[109,107,103];
 for(let i=0;i<3;i++)assert(html.includes(`${alphabet[i].rune}</span> = ${primes[i]}`));
 assert(html.includes(primes.join(' + ')+' = '+primes.reduce((a,b)=>a+b,0)));
 assert.equal(html.includes('across all 29 alphabet runes'),table==='reversed');
 assert(!html.includes('boundary example'),'Scope stays in the existing review wording, outside this calculation');
}
for(const criterion of [null,{},[],{...base,lag:0},{...base,lag:13},{...base,a:29},{...base,b:-1},{...base,boundaries:'<img src=x>'},{...base,extra:true},{kind:'word-prime-sums',table:'invalid',boundaries:'non-rune'}])assert.equal(V.render({criterion,alphabet}),'');
for(const bad of [null,[],alphabet.slice(1),[...alphabet,alphabet[0]],alphabet.map((item,i)=>i?item:{...item,rune:'<img src=x onerror=alert(1)>'}),alphabet.map((item,i)=>i?item:{...item,prime:Infinity}),alphabet.map((item,i)=>i?item:{...item,prime:2.5}),alphabet.map((item,i)=>i?item:{...item,prime:Number.MAX_SAFE_INTEGER}),alphabet.map((item,i)=>i?item:alphabet[1])])assert.equal(V.render({criterion:base,alphabet:bad}),'');
assert.equal(V.render(null),'');assert.equal(V.render(), '');assert.equal(JSON.stringify(alphabet),original);
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync(require.resolve('../experiment-protocols.js'),'utf8'),ctx);vm.runInContext(fs.readFileSync(require.resolve('../protocol-example-view.js'),'utf8'),ctx);
ctx.input={criterion:base,alphabet};assert.equal(vm.runInContext('ProtocolExampleView.render(input)',ctx),V.render({criterion:base,alphabet}));
console.log(`PASS ${checked} coefficient/distance examples, real usual/reversed prime sums under both boundaries, malformed/injection rejection, immutability and browser export`);

(async()=>{
 const E=require('../local-experiment.js'),{webcrypto}=require('node:crypto');let cases=0;
 for(const mode of ['repeat','plaintext-autokey','ciphertext-autokey'])for(const direction of ['add','subtract'])for(const reset of ['page','line','word'])for(const length of [1,4,256])for(let value=0;value<29;value++){
  const step={op:'keyed-shift',mode,direction,reset,key:Array.from({length},(_,i)=>(value+i*7)%29)},plan={alphabet,steps:[step]},before=JSON.stringify(plan),example=V.keyedExample(plan),html=V.renderKeyed(plan);
  const text=Array.from({length:length+1},(_,i)=>alphabet[(5+i)%29].rune).join(''),task=await E.prepare({title:'Illustrative key example only',alphabet:alphabet.map(({rune,latin,prime})=>({rune,latin,prime})),pages:[{id:'lp2-00',text}],steps:[step],criterion:{kind:'measurement'}},webcrypto),output=Array.from(E.run(task).transformed[0].text).map(rune=>alphabet.findIndex(a=>a.rune===rune));
  assert.equal(example.first.input,5);assert.equal(example.first.key,value);assert.equal(example.first.output,output[0]);assert.equal(example.next.input,(5+length)%29);assert.equal(example.next.position,length+1);assert.equal(example.next.output,output[length]);assert.equal(example.next.key,mode==='repeat'?value:mode==='plaintext-autokey'?output[0]:5);
  assert(html.includes('not manuscript evidence'));assert(html.includes('In a '+reset+' longer than '+length));assert(html.includes(mode==='repeat'?'return to the first key rune.':mode==='plaintext-autokey'?'from the first output above.':'from the first input above.'));assert.equal((html.match(/<tr>/g)||[]).length,2,'One illustrative calculation and one header row');assert(!/<(?:button|a|details|input)\b/.test(html));assert.equal(JSON.stringify(plan),before);cases++;
 }
 const step={op:'keyed-shift',mode:'plaintext-autokey',direction:'subtract',reset:'word',key:[2,3,4,5]},plan={alphabet,steps:[step]};
 for(const change of [null,[],{}, {...step,extra:true},{...step,op:'interrupted-keyed-shift'},{...step,mode:'other'},{...step,direction:'multiply'},{...step,reset:'paragraph'},{...step,key:[]},{...step,key:Array(2)},{...step,key:[null]},{...step,key:[-1]},{...step,key:[29]},{...step,key:[0.5]},{...step,key:Array(257).fill(1)}])assert.equal(V.renderKeyed({...plan,steps:[change]}),'');
 for(const steps of [[],[step,step],null,'keyed-shift'])assert.equal(V.renderKeyed({...plan,steps}),'','A multi-step program must not be illustrated as a whole one-step transformation');
 const sparse=alphabet.slice();delete sparse[1];assert.equal(V.renderKeyed({...plan,alphabet:sparse}),'');assert.equal(V.renderKeyed(null),'');
 Object.defineProperty(plan,'pages',{get(){throw Error('Illustration must never read manuscript inputs');}});assert(V.renderKeyed(plan).includes('Illustrative example'));
 ctx.keyedPlan={alphabet,steps:[step]};assert.equal(vm.runInContext('ProtocolExampleView.renderKeyed(keyedPlan)',ctx),V.renderKeyed(plan));
 console.log('PASS '+cases+' synthetic key examples agree with the maintained engine across all first key indices, modes, directions, reset domains and short/long keys; malformed/sparse/multistep rejection, immutable rendering and no manuscript access.');
})().catch(error=>{console.error(error);process.exitCode=1;});
