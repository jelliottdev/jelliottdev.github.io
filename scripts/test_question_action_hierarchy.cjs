'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const L=require('../library.js'),Q=require('../record-question-view.js'),F=require('../record-followup-view.js');
const read=id=>JSON.parse(fs.readFileSync(require.resolve('../experiments/records/'+id+'/record.json'),'utf8'));
const deor=read('wulfic-autokey-seed-families'),boundary=read('word-internal-affine-lags');
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const source=fs.readFileSync(require.resolve('../library.js'),'utf8'),library={RecordQuestionView:Q,RecordFollowupView:F,readerLimit:L.readerLimit,recordFiles:L.recordFiles,readerSections:L.readerSections,esc:escape,hasInteractive:()=>false,prepareAuthored:x=>x,renderExperimentMarkdown:L.renderMarkdown,url:(path,params={})=>{if(path==='experiments')return L.researchHref(params);const search=new URLSearchParams(Object.entries(params).filter(([,value])=>value!==''&&value!==null&&value!==undefined));return '#/'+path+(search.size?'?'+search:'');},experimentHref:id=>'library.html#/experiment/'+id,familyMembers:()=>[]};vm.createContext(library);vm.runInContext(source.slice(source.indexOf(' function overview('),source.indexOf(' function scope(')),library);
const mapSource=fs.readFileSync(require.resolve('../research-browser.js'),'utf8'),back={},panel={hidden:false,innerHTML:'',querySelector(selector){return selector==='.preview-back'?back:null;},contains(){return false;}};
const map={RecordQuestionView:{...Q,mount(){return {destroy(){}};}},RecordFollowupView:F,panel,data:{records:{}},state:{record:''},questionMount:null,updatePreviewMode(){},esc:escape,pageRanges:pages=>L.compactPages(pages),recordHref:record=>'library.html#/experiment/'+record.id,workFor:()=>null,arrow:'',navigate(){}};vm.createContext(map);vm.runInContext(mapSource.slice(mapSource.indexOf(' function readerLimit('),mapSource.indexOf(' function pageRanges(')),map);
function preview(record){map.data.records[record.id]=record;map.state.record=record.id;map.showInspector();return panel.innerHTML;}
function verify(html,record,live){
 const before=html.indexOf('data-live-question='),disclosure=html.indexOf('<details class="other-prepared-checks">'),legacy=html.indexOf('class="record-followups"');
 assert.equal((html.match(/<details class="other-prepared-checks">/g)||[]).length,live?1:0);
 if(live){assert(before>=0&&before<disclosure&&disclosure<legacy,'The current question precedes the one secondary recipe disclosure');assert.match(html,/<summary>Other prepared checks<\/summary>/);assert(!html.includes('<details class="other-prepared-checks" open'));}
 else assert(legacy>=0&&legacy<html.indexOf('id="experiment-remaining"'),'Ordinary authored follow-ups retain their original place');
 const options=[...html.matchAll(/<option value="([a-z0-9-]+)"/g)].map(m=>m[1]);assert.deepEqual(options,F.recipes(record).map(recipe=>recipe.id),'Every exact legacy recipe is present once, including distinct Beaufort and DIVINITY settings');assert.equal((html.match(/data-prepared-link/g)||[]).length,1);assert.equal((html.match(/id="experiment-remaining"/g)||[]).length,1);
 assert(html.includes('followup='+record.browser_followups[0].id));
}
for(const render of [record=>library.overview(record),preview]){
 const before=JSON.stringify(deor);verify(render(deor),deor,true);assert.equal(JSON.stringify(deor),before);
 const editorial=structuredClone(deor);editorial.research_questions[0].state='tested';editorial.research_questions[0].records=['lp1-section-balance'];verify(render(editorial),editorial,true);
 const ordinary=structuredClone(deor);delete ordinary.research_questions[0].protocol;verify(render(ordinary),ordinary,false);
 const onlyBoundary=structuredClone(boundary);onlyBoundary.browser_followups=onlyBoundary.browser_followups.filter(recipe=>recipe.id==='lag-six-non-rune-boundaries');const one=render(onlyBoundary);assert(one.includes('data-live-question='));assert(!one.includes('Other prepared checks'));assert(!one.includes('class="record-followups"'),'An exact question-owned recipe is not rendered twice');
 const expanded=render(boundary);verify(expanded,boundary,true);assert(expanded.includes('direct-reading-lag-six-control'),'The distinct readable-text control stays available beside the primary boundary question');
}
console.log('PASS library and map current questions lead; every distinct legacy setting remains once in one closed disclosure; ordinary records/editorial changes preserve their behavior and canonical data.');
