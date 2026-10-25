'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const V=require('../record-question-view.js'),L=require('../library.js');
const M=require('../record-question-model.js');
const record=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/lp2-known-vigenere-keys/record.json'),'utf8'));
const open={id:'another-boundary',question:'Does another boundary change the result?',state:'open',note:'Keep the same key and pages.',records:[],followup:record.browser_followups[0].id};
const tested={id:'completed-comparison',question:'Has the fixed comparison been checked?',state:'tested',note:'The comparison was completed; it does not prove a cipher.',records:['lp1-section-balance']};
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name)}

test('maintained protocol references derive exact recipe inputs and ignore editorial completion',()=>{
 const r=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/word-internal-affine-lags/record.json'),'utf8')),before=JSON.stringify(r),q=r.research_questions[0],resolved=M.protocolReference(r,q.id);
 assert.equal(M.questions(r,r.browser_followups).length,1);assert.deepEqual(resolved,{id:'word-boundary-sensitivity',version:1,followupId:q.followup,parameters:{lag:6,a:27,b:24},inputs:r.browser_followups[0].inputs});assert.equal(JSON.stringify(r),before);
 const tested=structuredClone(r);tested.research_questions[0].state='tested';tested.research_questions[0].records=['another-record'];assert.deepEqual(M.protocolReference(tested,q.id),resolved);
 resolved.inputs.pages[0].id='mutated';assert.notEqual(r.browser_followups[0].inputs.pages[0].id,'mutated');
 for(const mutate of [x=>x.research_questions[0].protocol.id='unknown',x=>x.research_questions[0].protocol.version=true,x=>x.research_questions[0].protocol.parameters={},x=>delete x.research_questions[0].followup,x=>x.browser_followups[0].card.rules.evaluation.value.a=26,x=>x.browser_followups[0].card.method.value.operations.push({id:'reverse_runes'}),x=>x.browser_followups[0].inputs.pages[0].text_sha256='bad',x=>x.browser_followups[0].card.scope.value.pages.pop(),x=>x.browser_followups[0].card.rules.reset={status:'specified',value:'word'}]){const bad=structuredClone(r);mutate(bad);assert.deepEqual(M.questions(bad,bad.browser_followups),[]);assert.equal(M.protocolReference(bad,q.id),null);}
 const deor=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/wulfic-autokey-seed-families/record.json'),'utf8'));assert.deepEqual(M.protocolReference(deor,deor.research_questions[0].id),{id:'deor-warning-opening',version:1,familyId:'deor-feedback-v1'});
 const bad=structuredClone(deor);bad.research_questions[0].followup=record.browser_followups[0].id;bad.browser_followups=record.browser_followups;assert.deepEqual(M.questions(bad,bad.browser_followups),[]);
});
test('fixed program references preserve historical assessment and expose only owned structural pins',()=>{
 const r=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/lp2-row-column-routes/record.json'),'utf8')),before=JSON.stringify(r),q=r.research_questions[0],ref=M.protocolReference(r,q.id);
 assert.equal(q.state,'tested');assert.deepEqual(ref,{id:'fixed-program-prefix',version:1,followupId:q.followup,inputs:r.browser_followups[0].inputs});assert.equal(JSON.stringify(r),before);assert(!Object.hasOwn(ref,'state'));assert(!Object.hasOwn(ref,'answer'));
 for(const mutate of [x=>delete x.research_questions[0].followup,x=>x.research_questions[0].protocol.version=2,x=>x.browser_followups[0].card.rules.evaluation.value={kind:'measurement'},x=>x.browser_followups[0].card.rules.evaluation.value.values=[29],x=>x.browser_followups[0].inputs.pages[0].text_sha256='bad',x=>x.browser_followups[0].card.scope.value.pages.pop()]){const bad=structuredClone(r);mutate(bad);assert.deepEqual(M.questions(bad,bad.browser_followups),[]);}
});
test('open questions precede completed comparisons without mutation',()=>{
 const r={...record,research_questions:[tested,open]},before=JSON.stringify(r),html=V.render(r);
 assert.equal(JSON.stringify(r),before);assert.equal(V.questions(r)[0].state,'open');assert(html.indexOf(open.question)<html.indexOf(tested.question));assert.equal((html.match(/id="experiment-remaining"/g)||[]).length,1);assert.match(html,/<h2>Questions to explore<\/h2>/);assert.match(html,/Tested<\/span>/);assert.match(html,/library\.html#\/experiment\/lp1-section-balance/);assert.match(html,new RegExp('run.html#record='+record.id+'&amp;followup='+open.followup));assert(!/Run now|Create experiment|Proven|<details|<button/.test(html));
});
test('only missing typed questions permit legacy fallback',()=>{
 assert.match(V.render(record,{fallback:'Keep a fixed comparison.'}),/What remains open/);assert.equal(V.render(record),'');
 for(const value of [null,[],{},'',Array(13).fill(open)])assert.equal(V.render({...record,research_questions:value},{fallback:'Stale suggestion'}),'');
 assert.equal(V.render(null),'');assert.equal(V.render({},{}),'');
});
test('reject malformed questions rather than advertise partial or invented work',()=>{
 const invalid=[{...open,id:'../bad'},{...open,question:''},{...open,question:'x'.repeat(301)},{...open,note:'x'.repeat(701)},{...open,state:'proven'},{...open,records:['../bad']},{...open,records:[record.id]},{...open,records:['same','same']},{...open,followup:'not-declared'},{...open,extra:true},{...tested,records:[]},{...tested,records:[],followup:open.followup}];
 for(const item of invalid)assert.equal(V.render({...record,research_questions:[item]}),'',JSON.stringify(item));
 assert.equal(V.render({...record,research_questions:[open,open]}),'');
 assert.equal(V.render({...record,id:'../unsafe',research_questions:[open]}),'');
 const noAction=V.render({...record,research_questions:[{...open,followup:undefined}]});assert.equal(noAction,'');
 const unprepared={...open};delete unprepared.followup;assert(!V.render({...record,research_questions:[unprepared]}).includes('<a '));
});
test('escape prose, retain exact navigation and optional references',()=>{
 const r={...record,research_questions:[{...open,question:'What does A & B mean?',note:'A & B "quoted"'},{...tested,records:['one','two']}]},html=V.render(r,{headingLevel:3});
 assert.match(html,/What does A &amp; B mean/);assert(!html.includes('<img'));assert.match(html,/A &amp; B &quot;quoted&quot;/);assert.match(html,/<h3>/);assert.match(html,/library\.html#\/experiment\/one/);assert.match(html,/Read completed test 2/);assert.match(V.render(record,{fallback:'<script>bad</script>'}),/&lt;script&gt;/);
});

test('plain-text contract matches builder limits, trimming and own fields',()=>{
 for(const value of [' leading','trailing ', '\u0085leading', 'trailing\u00a0','<tag>','[link]','`code`','a*b','back\\slash','line\nfeed','control\x7f','line\u2028separator','\ud800','\udfff'])for(const key of ['question','note'])assert.equal(V.render({...record,research_questions:[{...open,[key]:value}]}),'',key+': '+JSON.stringify(value));
 for(const id of ['1-start','bad--slug','x'.repeat(101)])assert.equal(V.render({...record,research_questions:[{...open,id}]}),'');
 const inherited=Object.assign(Object.create({question:open.question}),open);delete inherited.question;assert.equal(V.render({...record,research_questions:[inherited]}),'');
 assert.equal(V.render({...record,research_questions:[{...open,records:Array(1)}]}),'');
 const inheritedAction={...open};delete inheritedAction.followup;Object.setPrototypeOf(inheritedAction,{followup:'unsafe'});assert(!V.render({...record,research_questions:[inheritedAction]}).includes('run.html'));assert(!V.coversFollowups({...record,research_questions:[inheritedAction]}));
 assert(V.render({...record,research_questions:[{...open,question:'😀'.repeat(150)}]}));assert.equal(V.render({...record,research_questions:[{...open,question:'😀'.repeat(151)}]}),'');
 assert(V.coversFollowups({...record,research_questions:[open]}));assert(!V.coversFollowups({...record,research_questions:[tested]}));assert(!V.coversFollowups(record));
});

test('completed owned recipes remain reproducible without advertising open work',()=>{
 const F=require('../record-followup-view.js'),r={...record,research_questions:[{...tested,followup:open.followup}]};
 const html=V.render(r);assert(html.includes('Review this check'));assert(!html.includes('Review follow-up'));assert(html.indexOf('Read completed test')<html.indexOf('Review this check'));assert(V.coversFollowups(r));
 assert.equal(F.available(r).length,0);assert.equal(F.recipes(r).length,record.browser_followups.length);assert(F.render(r).includes('Reproduce a comparison'));
 const conflict={...r,research_questions:[...r.research_questions,{...open,id:'conflicting-state'}]};assert.equal(V.render(conflict),'');assert.equal(F.available(conflict).length,0);
});

test('generated completed-test links select actual production experiment routes',()=>{
 const source=fs.readFileSync(require.resolve('../library.js'),'utf8'),route=source.slice(source.indexOf(' function state(){'),source.indexOf(' function edit('));
 const c={location:{hash:''},URLSearchParams};vm.createContext(c);vm.runInContext(route,c);
 const html=V.render({...record,research_questions:[{...tested,records:['lp1-section-balance','lp1-section-order']}]});
 const links=[...html.matchAll(/href="(library\.html[^"]+)"/g)].map(match=>match[1]);assert.equal(links.length,2);
 for(const [index,href] of links.entries()){const url=new URL(href,'https://liberpedia.test/');c.location.hash=url.hash;const selected=c.state();assert.equal(selected.parts[0],'experiment');assert.equal(selected.parts[1],['lp1-section-balance','lp1-section-order'][index]);assert.equal(selected.params.size,0);}
});
test('actual library overview uses typed questions and preserves legacy fallback',()=>{
 const source=fs.readFileSync(require.resolve('../library.js'),'utf8'),html=fs.readFileSync(require.resolve('../library.html'),'utf8');
 const c={RecordQuestionView:V,readerLimit:L.readerLimit,recordFiles:L.recordFiles,readerSections:L.readerSections,esc:JSON.stringify,hasInteractive:()=>false,prepareAuthored:x=>x,renderExperimentMarkdown:L.renderMarkdown,url:(path,params={})=>{if(path==='experiments')return L.researchHref(params);const search=new URLSearchParams(Object.entries(params).filter(([,value])=>value!==''&&value!==null&&value!==undefined));return '#/'+path+(search.size?'?'+search:'');},experimentHref:id=>'library.html#/experiment/'+id,familyMembers:()=>[]};vm.createContext(c);vm.runInContext(source.slice(source.indexOf(' function overview('),source.indexOf(' function scope(')),c);
 const typed=c.overview({...record,research_questions:[tested,open],next_steps:'Do the already completed comparison again.'});assert(typed.includes('Questions to explore'));assert(!typed.includes('Do the already completed comparison again.'));assert(typed.indexOf('experiment-finding')<typed.indexOf('Questions to explore'));
 const legacy=c.overview({...record,next_steps:'Keep the original untyped suggestion.'});assert(legacy.includes('Keep the original untyped suggestion.'));assert(legacy.includes('What remains open'));
 assert(html.includes('record-question-view.css'));assert(html.indexOf('record-followup-view.js')<html.indexOf('record-question-view.js'));assert(html.indexOf('record-question-view.js')<html.indexOf('src="library.js'));
});
console.log(count+' record question view groups passed');
