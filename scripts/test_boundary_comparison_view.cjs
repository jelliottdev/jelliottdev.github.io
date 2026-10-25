'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),V=require('../boundary-comparison-view.js');
const alphabet=require('../data/index.json').alphabet,base={alphabet,criterion:{kind:'word-affine-count',a:1,b:0,lag:5,boundaries:'non-rune'}},before=structuredClone(base);
for(const boundaries of ['non-rune','hyphen-period']){
 const task={...base,criterion:{...base.criterion,boundaries}},saved=structuredClone(task),description=V.describe(task),html=V.render(task);
 assert.equal(description.actionLabel,boundaries==='hyphen-period'?'Review with joined words':'Review with separated words');
 assert(description.explanation.includes('counting rule, rune order and pages stay the same'));assert(html.includes('Pages remain separate'));
 assert(description.explanation.includes(boundaries==='hyphen-period'?"only '-' and '.' end a group":'each stretch of runes separate'));
 assert(html.includes('not manuscript evidence'));assert(html.includes('Two groups'));assert(html.includes('One group'));
 assert.equal((html.match(/class="boundary-comparison-row"/g)||[]).length,2);
 assert.equal((html.match(/class="boundary-comparison-word"/g)||[]).length,3,'Two separated groups and one joined group');
 for(const {rune} of alphabet.slice(0,4))assert.equal((html.match(new RegExp(rune,'g'))||[]).length,2,'Both rows preserve each supplied rune exactly once');
 assert(html.includes('synthetic space'));assert(html.includes('<code>-</code>'));assert(html.includes('<code>.</code>'));
 assert(!/<(?:button|input|select|details|summary|script)\b/.test(html));assert(!/matches|above average|decoded/.test(html));assert.deepEqual(task,saved);
}
for(let a=0;a<29;a++)for(let b=0;b<29;b++)for(const lag of [1,12]){
 const task={...base,criterion:{...base.criterion,a,b,lag}};assert(V.describe(task));assert(V.render(task));
}
for(const invalid of [null,{}, {...base,criterion:{...base.criterion,a:29}},{...base,criterion:{...base.criterion,lag:0}},{...base,criterion:{...base.criterion,extra:true}},{...base,criterion:{kind:'word-prime-sums',table:'canonical',boundaries:'non-rune'}},{...base,criterion:{...base.criterion,boundaries:'<img src=x>'}},{...base,alphabet:[]},{...base,alphabet:alphabet.slice(1)},{...base,alphabet:[...alphabet,alphabet[0]]},{...base,alphabet:alphabet.map((row,i)=>i?row:alphabet[1])},{...base,alphabet:alphabet.map((row,i)=>i?row:{rune:'<img src=x onerror=alert(1)>'})},{...base,alphabet:alphabet.map((row,i)=>i?row:{rune:'ᚠᚢ'})}]){
 assert.equal(V.render(invalid),'');assert.equal(V.describe(invalid),'');
}
const extra={...base,title:'<script>alert(1)</script>',alphabet:alphabet.map(row=>({...row,latin:'<img src=x>'}))};assert.equal(V.render(extra),V.render(base),'Only validated rune glyphs and fixed editorial text enter HTML');
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync(require.resolve('../experiment-protocols.js'),'utf8'),ctx);vm.runInContext(fs.readFileSync(require.resolve('../boundary-comparison-view.js'),'utf8'),ctx);ctx.input=base;assert.equal(vm.runInContext('BoundaryComparisonView.render(input)',ctx),V.render(base));assert.equal(JSON.stringify(vm.runInContext('BoundaryComparisonView.describe(input)',ctx)),JSON.stringify(V.describe(base)));
assert.deepEqual(base,before);
const css=fs.readFileSync(require.resolve('../boundary-comparison-view.css'),'utf8');assert(css.includes('max-width:252px'));assert(css.includes("font-family:'Local Runic'"));
console.log('PASS exact source runes, two groupings, target-mode labels, all coefficient/distance validation, injection rejection, immutability and UMD export');
