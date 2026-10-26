'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const V=require('../record-question-view.js'),L=require('../library.js');
const M=require('../record-question-model.js');
const actualRecord=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/lp2-known-vigenere-keys/record.json'),'utf8'));
const record={...actualRecord,browser_followups:[actualRecord.browser_followups[0]]};delete record.research_questions;
const legacyRecord={...record};delete legacyRecord.research_questions;
const open={id:'another-boundary',question:'Does another boundary change the result?',state:'open',note:'Keep the same key and pages.',records:[],followup:record.browser_followups[0].id};
const tested={id:'completed-comparison',question:'Has the fixed comparison been checked?',state:'tested',note:'The comparison was completed; it does not prove a cipher.',records:['lp1-section-balance']};
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name)}

test('actual known-key questions link all three42program source families without claiming results',()=>{
 const questions=M.questions(actualRecord,actualRecord.browser_followups);assert.equal(questions.length,3);
 const html=V.render(actualRecord);assert(html.includes('Questions to explore'));assert(!html.includes('What remains open'));
 for(const question of questions){assert.equal(question.state,'open');const ref=M.protocolReference(actualRecord,question.id);assert.equal(ref.id,'finite-settings-output');const recipe=actualRecord.browser_followups.find(r=>r.id===ref.followupId);const family=M.finiteRecipe(recipe);assert.equal(family.programCount,42);assert.equal(family.caseCount,2352);assert(html.includes('followup='+recipe.id));assert.deepEqual(ref.inputs,recipe.inputs);}
 assert(!V.coversFollowups(actualRecord),'The independent fixed comparison remains available alongside the three open finite questions');
});

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
 assert.match(V.render(legacyRecord,{fallback:'Keep a fixed comparison.'}),/What remains open/);assert.equal(V.render(legacyRecord),'');
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
 assert.match(html,/What does A &amp; B mean/);assert(!html.includes('<img'));assert.match(html,/A &amp; B &quot;quoted&quot;/);assert.match(html,/<h3>/);assert.match(html,/library\.html#\/experiment\/one/);assert.match(html,/Read completed test 2/);assert.match(V.render(legacyRecord,{fallback:'<script>bad</script>'}),/&lt;script&gt;/);
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
 const F=require('../record-followup-view.js'),r={...legacyRecord,browser_followups:[record.browser_followups[0]],research_questions:[{...tested,followup:open.followup}]};
 const html=V.render(r);assert(html.includes('Review this check'));assert(!html.includes('Review follow-up'));assert(html.indexOf('Read completed test')<html.indexOf('Review this check'));assert(V.coversFollowups(r));
 assert.equal(F.available(r).length,0);assert.equal(F.recipes(r).length,1);assert(F.render(r).includes('Reproduce a comparison'));
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
 const legacy=c.overview({...legacyRecord,next_steps:'Keep the original untyped suggestion.'});assert(legacy.includes('Keep the original untyped suggestion.'));assert(legacy.includes('What remains open'));
 assert(html.includes('record-question-view.css'));assert(html.indexOf('record-followup-view.js')<html.indexOf('record-question-view.js'));assert(html.indexOf('record-question-view.js')<html.indexOf('src="library.js'));
});
test('numerical extension and historical replay expose distinct authored purpose without changing canonical questions',()=>{
 const r=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/lp2-prime-openings/record.json'),'utf8')),before=JSON.stringify(r),html=V.render(r),cards=html.split('<li>').slice(1);
 assert.equal(cards.length,2);for(const [i,recipe]of r.browser_followups.entries()){const part=cards[i],details=part.indexOf('<details class="record-published-assessment">'),live=part.indexOf('<div class="record-live-question"');assert(part.indexOf(recipe.title)<live);assert(part.indexOf(recipe.motivation)<live);assert(part.indexOf(recipe.question)>details);assert.equal((part.match(/class="record-question-context"/g)||[]).length,1);assert.equal((part.match(/<details/g)||[]).length,1);assert(part.includes('followup='+recipe.id));assert.equal(V.questions(r)[i].question,recipe.question);}
 assert(cards[0].includes('this new comparison asks about language similarity'));assert(cards[0].includes('restart at each page, line or word'));assert(cards[1].includes('This repeats the earlier opening test'));assert(cards[1].includes('does not compare language scores or add line and word restarts'));assert.equal(JSON.stringify(r),before);
});
test('owned display context escapes source text, uses only validated recipes and bounds fallback prose',()=>{
 const r=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/lp2-prime-openings/record.json'),'utf8'));r.browser_followups=r.browser_followups.slice(0,1);r.research_questions=r.research_questions.slice(0,1);r.browser_followups[0].title='Compare A & B "quoted"';r.browser_followups[0].motivation='Try A & B, then inspect the output.';const html=V.render(r);assert(html.includes('Compare A &amp; B &quot;quoted&quot;'));assert(html.includes('Try A &amp; B, then inspect the output.'));assert(!html.includes('<img'));
 for(const mutate of [x=>x.browser_followups[0].motivation='<img src=x>',x=>x.browser_followups[0].title='x'.repeat(301),x=>x.browser_followups[0].inputs.pages[0].text_sha256='bad']){const bad=structuredClone(r);mutate(bad);assert.equal(V.render(bad),'');}
 delete r.browser_followups[0].motivation;r.browser_followups[0].scope_change='Try a different starting place.';assert(V.render(r).includes('<p class="record-question-context">Try a different starting place.</p>'));r.browser_followups[0].scope_change='Long source scope. '.repeat(30);assert(!V.render(r).includes('class="record-question-context"'));
});
test('unowned Deor question retains its maintained wording without invented display context',()=>{
 const r=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/wulfic-autokey-seed-families/record.json'),'utf8')),html=V.render(r),question=r.research_questions[0].question;assert(html.indexOf(question)<html.indexOf('data-live-question'));assert(!html.includes('class="record-question-context"'));assert(html.includes('class="record-question-exact"'));assert(html.indexOf('class="record-question-exact"')>html.indexOf('Exact question and background'));assert(!html.includes('Published as open'));
});
console.log(count+' record question view groups passed');
