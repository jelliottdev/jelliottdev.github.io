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
