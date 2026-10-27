/* Execute production library callbacks, not a parallel restoration model. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),L=require('../library.js');
const source=fs.readFileSync(require.resolve('../library.js'),'utf8');
const part=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
function fixture(){
 const frames=[],events=[],link={getAttribute:()=> '#/experiment/current',focus:o=>events.push(['link',o.preventScroll])},target={closest:()=>null,focus:o=>events.push(['section',o.preventScroll]),scrollIntoView:()=>events.push(['jump'])};
 const c={version:0,currentEntry:'old',currentHash:'#/experiment/old',current:null,nextEntry:'old',location:{hash:'#/experiment/old'},positions:new Map(),headerActive(){},entryKey:()=>c.nextEntry,requestAnimationFrame:f=>frames.push(f),window:{scrollTo:(x,y)=>events.push(['scroll',y])},main:{focus:()=>events.push(['main']),querySelectorAll:()=>[link]},document:{getElementById:id=>id==='section'?target:null,querySelector:()=>null},state:()=>c.route};
 vm.createContext(c);vm.runInContext(part(' function restorePosition(',' const normal='),c);vm.runInContext(part(' function queuePosition(',' function crumb('),c);
 return {c,frames,events,flush(){while(frames.length)frames.shift()()}};
}
function finish(f,section){f.c.finish({params:new URLSearchParams(section?'section='+section:'')},'experiments','Record')}
(async()=>{
 for(const mode of ['restore','jump'])for(const change of ['hash','entry','version']){
  const f=fixture();if(mode==='restore')f.c.positions.set('old',{y:900,linkIndex:0});finish(f,mode==='jump'?'section':null);
  if(change==='hash')f.c.location.hash='#/experiment/new';if(change==='entry')f.c.currentEntry='new';if(change==='version')f.c.version++;
  f.flush();assert.deepEqual(f.events,[],mode+' cannot act after '+change+' changed');
 }
 const old=fixture();old.c.positions.set('old',{y:900,linkIndex:0});finish(old);old.c.location.hash='#/experiment/new';old.c.nextEntry='new';finish(old);old.flush();assert.deepEqual(old.events,[['scroll',0],['main']],'A saved old entry cannot move/focus the new record');
 const normal=fixture();normal.c.positions.set('old',{y:420,linkIndex:0});finish(normal);normal.flush();assert.deepEqual(normal.events,[['scroll',420],['link',true]]);
 const jump=fixture();finish(jump,'section');jump.flush();assert.deepEqual(jump.events,[['section',true],['jump']]);
 // Actual same-guide fast path queues both saved restoration and section jumps.
 for(const saved of [false,true])for(const stale of [false,true]){
  const f=fixture();f.c.current={path:'guide/atbash'};f.c.route={path:'guide/atbash',parts:['guide','atbash'],params:new URLSearchParams('section=section')};f.c.location.hash='#/guide/atbash?section=section';if(saved)f.c.positions.set('old',{y:77,linkIndex:0});
  vm.runInContext(part(' async function render(){'," document.querySelectorAll('[data-close-dialog]')"),f.c);await f.c.render();assert.equal(f.frames.length,1);
  if(stale)f.c.location.hash='#/experiment/new';f.flush();assert.deepEqual(f.events,stale?[]:saved?[['scroll',77],['link',true]]:[['section',true],['jump']]);
 }
 // Actual multi-figure record: its authored caveat belongs beside the result.
 const record=JSON.parse(fs.readFileSync(require.resolve('../reference/experiments/grid-round-glyphs.json'),'utf8'));
 assert(record.visuals.length>=3);const c={compactPages:L.compactPages,readerLimit:L.readerLimit,recordFiles:L.recordFiles,readerSections:L.readerSections,esc:value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])),hasInteractive:L.hasInteractive,prepareAuthored:x=>x,renderExperimentMarkdown:L.renderMarkdown,experimentHref:(id,tab)=>'#/experiment/'+id+'?tab='+tab,familyMembers:()=>[]};
 vm.createContext(c);vm.runInContext(part(' function overview(',' function scope('),c);const html=c.overview(record),finding=html.indexOf('class="finding"'),limit=html.indexOf('<strong>Limit:</strong>'),figure=html.indexOf('<figure');assert(finding>=0&&finding<limit&&limit<figure);assert(html.includes(c.esc(L.readerLimit(record.reader_limit||record.limitations))));assert.equal((html.match(/<strong>Limit:<\/strong>/g)||[]).length,1);assert.equal((html.match(/class="source-visual"/g)||[]).length,record.visuals.length);
 const scientific='Not independently checked; uncertain language.';const annotated={...record,reader_limit:scientific+'; Human review pending.',limitations:scientific+' Human review is pending.',next_steps:'Check a separately fixed continuation. Human review pending.'},before=JSON.stringify(annotated),clean=c.overview(annotated);assert(clean.includes(scientific));assert(clean.includes('Check a separately fixed continuation.'));assert(!/human review(?: is)? pending/i.test(clean));vm.runInContext(part(' function scope(',' function reproduction('),c);const scope=c.scope(annotated);assert(scope.includes(scientific));assert(!/human review(?: is)? pending/i.test(scope));assert.equal(JSON.stringify(annotated),before);
 // The near-finding question link uses the maintained question model and the
 // same section route/jump callbacks as record tabs, never a bare DOM hash.
 {
  const questionRecord=JSON.parse(fs.readFileSync(require.resolve('../reference/experiments/lp2-row-column-routes.json'),'utf8'));
  c.RecordQuestionView=require('../record-question-view.js');c.url=(path,params)=>'#/'+path+'?'+new URLSearchParams(params);const questionHTML=c.overview(questionRecord),href=questionHTML.match(/<a href="([^"]+)">Questions to explore \((\d+)\)<\/a>/);
  assert(href);assert.equal(Number(href[2]),c.RecordQuestionView.questions(questionRecord).length);assert(questionHTML.indexOf(href[0])<questionHTML.indexOf('<figure'),'The jump is visible before authored visuals');assert.equal((questionHTML.match(/id="experiment-remaining"/g)||[]).length,1,'Questions stay in one location');
  const route=new URL(href[1],'https://example.test/library.html').hash.slice(2),params=new URLSearchParams(route.split('?')[1]);assert.equal(route.split('?')[0],'experiment/'+questionRecord.id);assert.equal(L.sectionTab(params.get('section')),'overview','A link reached from a different tab selects the actual Finding tab');
  const navigation=fixture();navigation.c.document.getElementById=id=>id==='experiment-remaining'?{closest:()=>null,focus:o=>navigation.events.push(['questions-focus',o.preventScroll]),scrollIntoView:()=>navigation.events.push(['questions-jump'])}:null;navigation.c.finish({params},'experiments','Record');navigation.flush();assert.deepEqual(navigation.events,[['questions-focus',true],['questions-jump']]);
  assert(!c.overview(record).includes('Questions to explore ('),'A fallback open-scope paragraph does not manufacture authored questions');const malformed={...questionRecord,research_questions:[{id:'bad'}]};assert(!c.overview(malformed).includes('Questions to explore ('));
  delete c.RecordQuestionView;
 }
 // The actual comparison view applies the same display-only limit cleaning.
 const left={...annotated,id:'left',family:{id:'family',title:'Recorded variants',baseline:'left'}},right={...annotated,id:'right',family:{id:'family',title:'Recorded variants',baseline:'left'}},active={offsetLeft:0},nav={offsetLeft:0,querySelector:()=>active},main={innerHTML:'',querySelectorAll:()=>[],querySelector:()=>nav};
 const comparison={readerLimit:L.readerLimit,compactPages:L.compactPages,esc:c.esc,version:1,current:null,main,familyMembers:()=>[left,right],load:async path=>path.includes('/left.')?left:right,outcomeNames:{},familyHref:()=> '#/family/family',experimentHref:c.experimentHref,edit:()=>({}),url:()=>'',crumb:()=>'',chevron:'',finish(){}};vm.createContext(comparison);vm.runInContext(part(' async function renderFamily(',' function enhanceReading('),comparison);
 for(const field of ['findings','limitations']){await comparison.renderFamily({parts:['family','family'],path:'family/family',params:new URLSearchParams('field='+field)},1);assert(main.innerHTML.includes(scientific));assert(!/human review(?: is)? pending/i.test(main.innerHTML));}
 // Execute the production navigation and full-record renderer together. An old
 // unresolved record must never mount its question controller over a newer view.
 {
  const a=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/word-internal-affine-lags/record.json'),'utf8')),b=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/wulfic-autokey-seed-families/record.json'),'utf8')),pending=[],events=[],mounts=[];
  const active={offsetLeft:0,focus(){}},bar={offsetLeft:0,querySelector:()=>active,scrollIntoView(){}},main={innerHTML:'',querySelector:selector=>selector==='.record-tabs'?bar:null};
  const context={questionMount:null,publishedDiscoveryMount:null,reactionMount:null,reactions:null,version:0,current:null,currentRecord:null,currentEntry:'entry',currentHash:'',positions:new Map(),data:{experiments:[a,b]},main,location:{hash:''},state:()=>context.route,sectionTab:()=>null,load:path=>new Promise(resolve=>pending.push({path,resolve})),overview:r=>'<p>Original '+r.id+'</p>',scope:r=>'<p>Scope '+r.id+'</p>',esc:String,crumb:()=>'',outcomeNames:{},experimentHref:(id,tab)=>'#/experiment/'+id+'?tab='+tab,bindCodeTools(){},finish:s=>{context.current=s;},renderGuide:async()=>{main.innerHTML='Guide content';},RecordQuestionView:{mount(host,record){assert.equal(host,main);assert(Array.isArray(record.research_questions));assert(main.innerHTML.includes(record.id));const handle={record,destroyed:false,destroy(){assert(!this.destroyed,'A controller is destroyed once');this.destroyed=true;events.push('destroy:'+record.id);}};mounts.push(handle);events.push('mount:'+record.id);return handle;}}};
  vm.createContext(context);vm.runInContext(part(' async function renderExperiment(',' async function renderFamily('),context);vm.runInContext(part(' async function render(){'," document.querySelectorAll('[data-close-dialog]')"),context);
  const navigate=(record,tab)=>{context.route={path:'experiment/'+record.id,parts:['experiment',record.id],params:new URLSearchParams(tab?'tab='+tab:'')};context.location.hash='#/'+context.route.path;return context.render();};
  const old=navigate(a),newer=navigate(b);assert.equal(pending.length,2);pending[1].resolve(b);await newer;assert.equal(mounts.length,1);assert.equal(mounts[0].record,b);pending[0].resolve(a);await old;assert.equal(mounts.length,1,'A stale source response cannot attach a live controller');assert(main.innerHTML.includes(b.id));assert(!main.innerHTML.includes(a.id));
  const scope=navigate(b,'scope');assert.equal(mounts[0].destroyed,true,'Leaving overview destroys before the next source response');pending[2].resolve(b);await scope;assert.equal(mounts.length,1,'Secondary tabs do not create question subscriptions');
  const overview=navigate(b);pending[3].resolve(b);await overview;assert.equal(mounts.length,2);assert.equal(mounts[1].record,b);
  context.route={path:'guide/introduction',parts:['guide','introduction'],params:new URLSearchParams()};await context.render();assert(mounts[1].destroyed);assert.equal(context.questionMount,null);assert.equal(main.innerHTML,'Guide content');assert.deepEqual(events,['mount:'+b.id,'destroy:'+b.id,'mount:'+b.id,'destroy:'+b.id]);
 }
 console.log('PASS library: actual deferred restore/jump rejects stale hash/entry/version, live questions mount only current overview and destroy on tab/navigation, stale sources cannot mount, finding+limit precede figures.');
})().catch(error=>{console.error(error);process.exitCode=1});
