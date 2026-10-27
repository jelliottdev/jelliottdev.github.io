/* Fixed-criterion intake and shared output view, using independently replayed engine results. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const C=require('../claim-specification.js'),E=require('../local-experiment.js'),V=require('../local-run-view.js'),O=require('../output-evaluators.js');
const alphabet=JSON.parse(fs.readFileSync(require.resolve('../data/index.json'),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const references=['English','Welsh','German','French','Spanish','Italian','Portuguese','Finnish'];
class Element{
 constructor(){this.listeners=new Set();this.value='';this.innerHTML='';}
 addEventListener(type,fn){assert.equal(type,'change');this.listeners.add(fn);}
 removeEventListener(type,fn){this.listeners.delete(fn);}
 change(){for(const fn of this.listeners)fn();}
}
(async()=>{
 const choice=C.EVALUATION_CHOICES.find(c=>c.id==='language-samples');assert(choice);assert.deepEqual(choice.value,O.criterion());assert.equal(choice.label,'Compare patterns with language samples');
 assert.deepEqual(C.EVALUATION_CHOICES.find(c=>c.id==='readable-text').value,{kind:'readability'});assert(C.evaluationText({kind:'readability'}).includes('not available'));
 assert(C.evaluationText(choice.value).includes('similarity is not a translation'));assert(!C.evaluationText(choice.value).includes('12 runes'));
 const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']}),draft=C.createDraft({source:{text:'Reverse the runes to decipher LP2.'},aim:known({outcomeId:'decipher',wording:'Decipher LP2'}),method:known({operations:[{id:'reverse_row_runes'}]}),scope:known({pages:['lp2-15']})});
 const clarified=C.clarify(draft,'evaluation','language-samples');assert.deepEqual(clarified.aim,draft.aim);assert.deepEqual(clarified.rules.evaluation.value,O.criterion());assert(!C.evaluationQuestion(clarified));assert.equal(clarified.source.text,draft.source.text);
 // The lightweight intake must not load either model artifact or scorer.
 const intake=fs.readFileSync(require.resolve('../claim-specification.js'),'utf8');assert(!/require\(['"].*language-(?:score|model)/.test(intake));
 const text=n=>Array.from({length:n},(_,i)=>alphabet[(i*7+i%3)%29].rune).join('');
 const task=await E.prepare({title:'Language reference UI',alphabet,pages:[{id:'lp2-15',text:'<img src=x>'+text(80)},{id:'lp2-16',text:text(39)}],steps:[{op:'reverse',unit:'line'}],criterion:O.criterion()}),result=await E.verify(task,E.run(task));
 const html=V.render(task,result);assert(html.includes('run-language-excerpt'));assert(html.indexOf('run-language-excerpt')<html.indexOf('How this page compares with shuffles'));assert(html.indexOf('How this page compares with shuffles')<html.indexOf('<details'));
 assert(html.includes('&lt;img src=x&gt;'));assert(!html.includes('<img src=x>'));assert(html.includes('Rune labels, not a translation'));assert(html.includes('A short bar is not evidence of readable text'));assert(html.includes('Trying many rules or outputs can produce unusual scores by chance'));
 assert(html.includes('not language probabilities'));assert(html.includes('not raw scores across languages'));assert(html.includes(O.describe(task.criterion).next));assert(!html.includes('Repeated neighbouring runes'));
 let previous=-1;for(const reference of references){const at=html.indexOf('<span>'+reference+'</span>');assert(at>previous,reference+' retains fixed reference order');previous=at;}
 assert.equal((html.match(/class="run-language-track"/g)||[]).length,8);assert(!/winner|most likely|probability|passed|decryption confirmed/i.test(html));
 for(const model of result.languageScore.pages[0].models)assert(html.includes(model.shuffledAtOrAbove+' of 32'));
 const changed=structuredClone(result);changed.languageScore.pages[0].models[0].total++;assert.throws(()=>V.render(task,changed));assert.throws(()=>V.render(task,{...result,languageScore:{...result.languageScore,modelSha256:'f'.repeat(64)}}));
 const select=new Element(),content=new Element(),panel={querySelector:s=>s==='[data-run-language-page]'?select:s==='[data-run-language-content]'?content:null},host={querySelector:s=>s==='[data-run-language]'?panel:null};
 const cleanup=V.bind(host,task,result);select.value='lp2-16';select.change();assert(content.innerHTML.includes('This page has 39 runes'));assert(content.innerHTML.includes('at least 40'));assert(!content.innerHTML.includes('run-language-track'));assert(content.innerHTML.includes('run-language-excerpt'));
 const short=content.innerHTML;select.value='lp2-99';select.change();assert.equal(content.innerHTML,short);
 task.pages[0].text='mutated';assert.throws(()=>{result.transformed[0].text='mutated';},TypeError);select.value='lp2-15';select.change();assert(content.innerHTML.includes('How this page compares with shuffles'));assert(!content.innerHTML.includes('mutated'));
 cleanup();select.value='lp2-16';select.change();assert(content.innerHTML.includes('How this page compares with shuffles'),'Cleaned-up selector cannot change the view');
 const forty=await E.prepare({title:'Minimum passage',alphabet,pages:[{id:'lp2-00',text:text(40)}],steps:[],criterion:O.criterion()}),fortyResult=await E.verify(forty,E.run(forty));assert.equal(fortyResult.languageScore.pages[0].status,'compared');assert(V.render(forty,fortyResult).includes('run-language-track'));
 const long=await E.prepare({title:'Bounded excerpt',alphabet,pages:[{id:'lp2-00',text:text(260)}],steps:[],criterion:O.criterion()}),longResult=await E.verify(long,E.run(long));assert(V.render(long,longResult).includes('First 120 characters'));
 const sandbox={LocalExperiment:E,OutputEvaluators:O};vm.runInNewContext(fs.readFileSync(require.resolve('../local-run-view.js'),'utf8'),sandbox);assert.equal(sandbox.LocalRunView.render(forty,fortyResult),V.render(forty,fortyResult));
 const missing={LocalExperiment:E};vm.runInNewContext(fs.readFileSync(require.resolve('../local-run-view.js'),'utf8'),missing);assert.throws(()=>missing.LocalRunView.render(forty,fortyResult),/not supported/);
 console.log('Language UI: explicit criterion, preserved aim, equal references, excerpt, short text, replay integrity, controls and UMD passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
