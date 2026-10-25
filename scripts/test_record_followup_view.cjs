'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const V=require('../record-followup-view.js');
const read=id=>JSON.parse(fs.readFileSync(path.join(__dirname,'../experiments/records',id,'record.json'),'utf8'));
const single=read('lp2-known-vigenere-keys'),multi=read('wulfic-autokey-seed-families');
let groups=0;function test(name,f){f();groups++;console.log('PASS '+name)}
test('every authored canonical recipe is available without changing its source',()=>{
 let count=0;for(const dir of fs.readdirSync(path.join(__dirname,'../experiments/records'))){const p=path.join(__dirname,'../experiments/records',dir,'record.json');if(!fs.existsSync(p))continue;const r=JSON.parse(fs.readFileSync(p,'utf8'));if(!r.browser_followups)continue;const before=JSON.stringify(r);assert.equal(V.recipes(r).length,r.browser_followups.length,dir);V.render(r);assert.equal(JSON.stringify(r),before);count+=r.browser_followups.length}assert.ok(count>=13);
});
test('one recipe is a direct review link, while multiple use one labeled setting selector',()=>{
 const one=V.render(single,{headingLevel:2});assert.match(one,/<h2>Try a follow-up<\/h2>/);assert.ok(!one.includes('<select'));assert.match(one,/Review follow-up/);assert.match(one,/run.html#record=lp2-known-vigenere-keys&amp;followup=second-koan-word-reset-warning/);
 const many=V.render(multi,{selectId:'library-setting'});assert.equal((many.match(/<select/g)||[]).length,1);assert.equal((many.match(/<option /g)||[]).length,8);assert.match(many,/<label for="library-setting">Setting<\/label>/);assert.equal((many.match(/<a /g)||[]).length,1);assert.ok(!/Run now|Create experiment|ready to run|onclick|<button/i.test(many));
});
test('malformed or missing recipes do not advertise actions, and duplicate IDs appear once',()=>{
 for(const r of [null,{}, {...single,id:'../unsafe'},{...single,browser_followups:[]},{...single,browser_followups:Array(9).fill(single.browser_followups[0])}])assert.equal(V.render(r),'');
 for(const change of [f=>f.id='x&bad',f=>f.title='',f=>delete f.inputs,f=>f.inputs.pages[0].text_sha256='bad',f=>f.control.task.engine='arbitrary-code',f=>delete f.control,f=>f.card.version=99]){const r=structuredClone(single);change(r.browser_followups[0]);assert.equal(V.render(r),'')}
 const r=structuredClone(single);r.browser_followups.push(r.browser_followups[0]);assert.equal(V.recipes(r).length,1);
});
test('authored text is escaped and setting updates stay text-only and within validated IDs',()=>{
 const r=structuredClone(multi);r.browser_followups[1].title='<img src=x>';r.browser_followups[1].scope_change='<script>do not execute</script>';const html=V.render(r);assert.ok(html.includes('&lt;img src=x&gt;'));assert.ok(!html.includes('<script>'));
 const nodes={select:{value:r.browser_followups[0].id},scope:{textContent:''},link:{href:''}};
 const container={querySelector:s=>({'[data-prepared-setting]':nodes.select,'[data-prepared-scope]':nodes.scope,'[data-prepared-link]':nodes.link})[s]};V.bind(container,r);
 const next=r.browser_followups[1];nodes.select.value=next.id;nodes.select.onchange();assert.equal(nodes.scope.textContent,next.scope_change);assert.equal(nodes.link.href,'run.html#record='+r.id+'&followup='+next.id);
 const previous=nodes.link.href;nodes.select.value='forged';nodes.select.onchange();assert.equal(nodes.select.value,next.id);assert.equal(nodes.link.href,previous);V.bind(null,r);
});
test('full record shows the shared action after finding and figures, before extra detail',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../library.js'),'utf8'),html=fs.readFileSync(path.join(__dirname,'../library.html'),'utf8');const overview=source.slice(source.indexOf(' function overview('),source.indexOf(' function scope('));
 const vm=require('node:vm'),L=require('../library.js'),Q=require('../record-question-view.js'),context={RecordQuestionView:Q,RecordFollowupView:V,readerLimit:L.readerLimit,recordFiles:L.recordFiles,readerSections:L.readerSections,esc:String,hasInteractive:()=>false,prepareAuthored:x=>x,renderExperimentMarkdown:L.renderMarkdown,url:(path,params={})=>{if(path==='experiments')return L.researchHref(params);const search=new URLSearchParams(Object.entries(params).filter(([,value])=>value!==''&&value!==null&&value!==undefined));return '#/'+path+(search.size?'?'+search:'');},experimentHref:id=>'library.html#/experiment/'+id,familyMembers:()=>[]};
 const record=JSON.parse(fs.readFileSync(path.join(__dirname,'../experiments/records/wulfic-autokey-seed-families/record.json'),'utf8'));delete record.research_questions[0].protocol;record.visuals=[{path:'source-fixture.svg',caption:'Source figure'}];vm.createContext(context);vm.runInContext(overview,context);const rendered=context.overview(record);
 assert.ok(rendered.indexOf('id="experiment-finding"')<rendered.indexOf('source-visual'));assert.ok(rendered.indexOf('source-visual')<rendered.indexOf('class="record-followups"'));assert.ok(rendered.indexOf('class="record-followups"')<rendered.indexOf('reader-sections'));assert.match(source,/if\(tab==='overview'\)\{globalThis\.RecordFollowupView\?\.bind\(main,record\)/);assert.ok(html.indexOf('record-followup-view.js')<html.indexOf('src="library.js'));
});
test('map and full record use the same component and load it before their controllers',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../research-browser.js'),'utf8'),html=fs.readFileSync(path.join(__dirname,'../research.html'),'utf8');
 assert.match(source,/globalThis\.RecordFollowupView\?\.render\(record\)/);assert.match(source,/globalThis\.RecordFollowupView\?\.bind\(panel,record\)/);assert.ok(!source.includes('function followupRecipes('));assert.ok(html.indexOf('record-followup-view.js')<html.indexOf('src="research-browser.js'));
});
console.log(groups+' shared follow-up view groups passed');
