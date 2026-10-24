/* Actual view + native-control handlers, no browser/network/model. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const E=require('../local-experiment.js'),V=require('../local-run-view.js');
assert.equal(V.pageLabel(['lp2-00','lp2-01','lp2-02','lp2-15','lp2-16'].map(id=>({id}))), 'LP2-00–02, LP2-15–16 (5 pages)');
assert.equal(V.pageLabel(['lp1-16','lp2-00','lp2-02'].map(id=>({id}))), 'LP1-16, LP2-00, LP2-02 (3 pages)');
assert.equal(V.pageLabel(['lp2-03','lp2-01'].map(id=>({id}))), 'LP2-03, LP2-01 (2 pages)', 'Scope summaries retain declared page order');
const alphabet=JSON.parse(fs.readFileSync(require.resolve('../data/index.json'),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
class Element{
 constructor(attributes={}){this.attributes=attributes;this.listeners=new Map();this.dataset={};this.value='';this.textContent='';}
 getAttribute(name){return this.attributes[name]??null;}
 setAttribute(name,value){this.attributes[name]=value;}
 addEventListener(type,fn){if(!this.listeners.has(type))this.listeners.set(type,new Set());this.listeners.get(type).add(fn);}
 removeEventListener(type,fn){this.listeners.get(type)?.delete(fn);}
 fire(type){for(const fn of this.listeners.get(type)||[])fn({target:this});}
}
function hostFor(multiple=true){
 const panel=new Element(),original=new Element(),after=new Element(),select=multiple?new Element():null;
 const runes=new Element({'data-run-text-mode':'runes'}),latin=new Element({'data-run-text-mode':'latin'});
 panel.querySelector=selector=>({'[data-run-text-page]':select,'[data-run-original]':original,'[data-run-after]':after}[selector]||null);
 panel.querySelectorAll=selector=>selector==='[data-run-text-mode]'?[runes,latin]:[];
 return {querySelector:selector=>selector==='.run-text-inspector'?panel:null,panel,original,after,select,runes,latin};
}
(async()=>{
 const first='<img src=x onerror=alert(1)>ᚠᚢ  ᚦ\r\nᚩ\tᚱ',second='ᚦᛡ, ᚠ\nᚢ';
 const task=await E.prepare({title:'Exact text inspection',alphabet,pages:[{id:'lp2-15',text:first},{id:'lp2-17',text:second}],steps:[{op:'reverse',unit:'line'}],criterion:{kind:'measurement'}}),result=await E.verify(task,E.run(task)),html=V.render(task,result);
 assert(html.indexOf('run-text-inspector')>html.indexOf('run-scope'));
 assert(html.includes('<summary>Inspect the text</summary>'));assert(html.includes('not a translation'));assert(html.includes('middle dot'));
 assert(html.includes('&lt;img src=x onerror=alert(1)&gt;'));assert(!html.includes('<img src=x'));
 assert.equal((html.match(/data-run-original/g)||[]).length,1);assert.equal((html.match(/data-run-after/g)||[]).length,1);
 assert(html.includes('<option value="lp2-15">LP2-15</option>'));assert(html.includes('<option value="lp2-17">LP2-17</option>'));
 assert(!html.includes(second),'Only selected-page text is expanded');
 const wrong=structuredClone(result);wrong.transformed[0].text+='X';assert.throws(()=>V.render(task,wrong));assert.throws(()=>V.bind(hostFor(),task,wrong));
 const host=hostFor(),cleanup=V.bind(host,task,result);assert.equal(host.original.textContent,first);assert.equal(host.after.textContent,'<img src=x onerror=alert(1)>ᚦᚢ  ᚠ\r\nᚱ\tᚩ');
 host.select.value='lp2-17';host.select.fire('change');assert.equal(host.original.textContent,second);assert.equal(host.after.textContent,'ᚠᛡ, ᚦ\nᚢ');
 host.latin.fire('click');assert.equal(host.original.textContent,'TH·IA, F\nU');assert.equal(host.after.textContent,'F·IA, TH\nU');assert.equal(host.latin.getAttribute('aria-pressed'),'true');assert.equal(host.runes.getAttribute('aria-pressed'),'false');
 host.select.value='lp2-15';host.select.fire('change');assert(host.original.textContent.startsWith('<img src=x onerror=alert(1)>F·U  TH\r\nO\tR'));
 host.runes.fire('click');assert.equal(host.original.textContent,first);assert.equal(host.panel.dataset.textMode,'runes');
 host.select.value='lp2-99';host.select.fire('change');assert.equal(host.original.textContent,first,'Invalid selection never chooses arbitrary data');
 task.pages[0].text='MUTATED';result.transformed[0].text='MUTATED';host.latin.fire('click');assert(!host.original.textContent.includes('MUTATED'));assert(!host.after.textContent.includes('MUTATED'));
 cleanup();host.runes.fire('click');assert.equal(host.panel.dataset.textMode,'latin');
 const one=await E.prepare({title:'One page',alphabet,pages:[{id:'lp2-15',text:'ᚠᚦ'}],steps:[],criterion:{kind:'measurement'}}),oneResult=await E.verify(one,E.run(one));assert(!V.render(one,oneResult).includes('data-run-text-page'));const oneHost=hostFor(false);V.bind(oneHost,one,oneResult);V.bind(oneHost,one,oneResult);assert.equal(oneHost.latin.listeners.get('click').size,1,'Rebinding removes the previous controls');
 const labelTask=structuredClone(one);labelTask.alphabet[0].latin='<svg>';labelTask.taskId=await E.identity(labelTask);const labelHost=hostFor(false);V.bind(labelHost,labelTask,await E.verify(labelTask,E.run(labelTask)));labelHost.latin.fire('click');assert.equal(labelHost.original.textContent,'<svg>·TH','Labels are inserted as literal text, never HTML');
 const css=fs.readFileSync(require.resolve('../local-run-view.css'),'utf8');assert(css.includes("fonts/NotoSansRunic-Regular.ttf"));assert(css.includes('@media(max-width:640px)'));assert(css.includes('grid-template-columns:repeat(2,minmax(0,1fr))'));assert(css.includes('grid-template-columns:minmax(0,1fr)'));assert(css.includes('white-space:pre-wrap'));assert(css.includes('min-height:44px'));
 console.log('PASS local run inspector: verified actual outputs, escaped text, one selected page, original/after, exact whitespace, unambiguous labels not translation, native page/mode controls, snapshots, cleanup and responsive CSS.');
})().catch(error=>{console.error(error);process.exitCode=1;});
