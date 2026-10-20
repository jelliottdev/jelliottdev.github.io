const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const search=require('../search-engine.js');
const root=path.join(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const db={...read('data/index.json'),articles:read('data/articles.json'),topics:read('data/topics.json')};
for(const q of ['Atba','Atbash','ATBASH']){
 const hits=search.search(db,q);
 assert.equal(hits[0].href,'#/wiki/atbash',q+' must lead with the method guide');
 assert(hits.findIndex(h=>h.href==='#/wiki/quick-start')>0,'incidental mentions must follow the subject');
}
for(const q of ['LP2-31','LP2:31','LP2 page 31'])assert.equal(search.search(db,q)[0].page.id,'lp2-31');
assert.deepEqual(search.search(db,'page 15').slice(0,2).map(h=>h.page.id),['lp1-15','lp2-15']);
assert.equal(search.search(db,'').length,0);
assert.equal(search.search(db,'zzzzzznotfound').length,0);
assert.equal(search.relevance('Atbash','', '','"atbash"'),650);
assert.equal(search.relevance('Some Wisdom','','a warning','wisdom warning'),60);
assert.equal(search.relevance('Some Wisdom','','a warning','"wisdom warning"'),0);
console.log('PASS: title/prefix ranking, page aliases, ambiguous numbering, phrases and empty results');

for(const [queries,id,pageIds] of [
 [['dots','black dots','three dots'],'dots',['lp2-33','lp2-39']],
 [['mobius','Möbius','moebius','infinity'],'mobius',['lp2-15']],
 [['cuniform','cuneiform','cuneform','wedge marks'],'cuneiform',['lp2-33','lp2-34']],
 [['compasses','compass','1033.jpg'],'illustrated-cover',[]],
 [['ioc','index of coincidence'],'index-of-coincidence',[]]
]){
 for(const q of queries){
  const hits=search.search(db,q);
  assert.equal(hits[0].href,'#/wiki/'+id,`Recognized subject ${q} must lead to its article`);
  for(const pid of pageIds)assert(hits.slice(0,5).some(h=>h.page?.id===pid),`${q}: ${pid} must be directly available`);
  assert.equal(new Set(hits.filter(h=>h.page).map(h=>h.page.id)).size,hits.filter(h=>h.page).length,'No duplicate page hits');
 }
}
for(const q of ['cuni','moeb','compass'])assert(search.search(db,q).length,'Spelling variants must work while typing');
assert.equal(search.search(db,'spirals')[0].href,'#/wiki/visual-index?section=spirals');
assert.equal(search.search(db,'branches')[0].href,'#/wiki/visual-index?section=branches');
console.log('PASS: visual names, spelling variants, partial aliases, direct page results, and subject anchors');

// Exercise the actual header input handler with an Android-style composing event.
// This is an isolated event test, not a physical-device keyboard simulation.
const vm=require('node:vm');
function target(){return {style:{},listeners:{},attrs:{},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(name,value){this.attrs[name]=value},getBoundingClientRect(){return {bottom:100}},contains(){return false}}}
const input=target(),form=target(),panel=target();input.value='Atba';
form.append=()=>{};panel.hidden=true;
let poll=null,release=null;const docListeners={};
const sandbox={setTimeout:fn=>{release=fn;return 2},clearTimeout:()=>{release=null},location:{hash:"#/experiments"},setNavigation(){},route(){},setInterval:fn=>{poll=fn;return 1},clearInterval:()=>{poll=null},queueMicrotask:fn=>fn(),db,WikiSearch:search,esc:String,marked:String,excerpt:String,
 $:s=>({'#search':input,'#search-form':form,'#search-suggestions':panel}[s]),
 document:{createElement:()=>panel,addEventListener(name,fn){docListeners[name]=fn}},
 window:{visualViewport:{height:430,addEventListener(){}}},innerHeight:430};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'search-ui.js'),'utf8'),sandbox);
vm.runInContext('bindWikiSearch()',sandbox);
input.listeners.input({isComposing:true});
assert.equal(panel.hidden,false,'Composing input must immediately show suggestions');
assert.match(panel.innerHTML,/#\/wiki\/atbash/);
assert.equal(input.value,'Atba','Rendering must not change keyboard composition text');
assert.equal(input.attrs['aria-expanded'],'true');
input.value='';input.listeners.input({isComposing:true});
assert.equal(panel.hidden,true,'Clearing composing text must hide suggestions');
console.log('PASS: composing input shows suggestions without blur or text mutation');

// Missing or delayed IME events: changed text must still render while focused.
sandbox.document.activeElement=input;input.listeners.focus();
input.value='Atbash';poll();
assert.equal(panel.hidden,false);
assert.match(panel.innerHTML,/#\/wiki\/atbash/);
const rendered=panel.innerHTML;panel.innerHTML='unchanged';poll();
assert.equal(panel.innerHTML,'unchanged','Unchanged input must not repeat the search');
input.listeners.blur();assert.equal(poll,null,'Stop the fallback when focus leaves');
console.log('PASS: eventless value changes update while focused; unchanged text does no work');

// A mobile tap can blur the field and commit composition before click arrives.
input.blur=()=>{sandbox.document.activeElement=null;input.listeners.blur();form.listeners.focusout()};
input.value='Koa';sandbox.document.activeElement=input;input.listeners.focus();
const beforeTap=panel.innerHTML;
panel.listeners.pointerdown();input.blur();
assert.equal(panel.hidden,false,'Blur during a result gesture must not hide its target');
input.value='Koan';input.listeners.compositionend();
assert.equal(panel.innerHTML,beforeTap,'Composition completion must not replace the touched link');
docListeners.pointerup();
let prevented=false;
const anchor={getAttribute:()=> '#/wiki/reading-first-koan'};
panel.listeners.click({target:{closest:()=>anchor},preventDefault(){prevented=true}});
assert.equal(sandbox.location.hash,'#/wiki/reading-first-koan');
assert(prevented);assert.equal(panel.hidden,true);assert.equal(release,null);
// Scrolling/cancelling a gesture must never activate a result.
sandbox.document.activeElement=input;input.listeners.focus();panel.listeners.pointerdown();
input.blur();docListeners.pointercancel();release();
assert.equal(sandbox.location.hash,'#/wiki/reading-first-koan');
assert.equal(panel.hidden,true);
// Enter produces click without a preceding pointer gesture.
sandbox.document.activeElement=input;input.listeners.focus();
panel.listeners.click({target:{closest:()=>({getAttribute:()=> '#/wiki/reading-second-koan'})},preventDefault(){}});
assert.equal(sandbox.location.hash,'#/wiki/reading-second-koan');
console.log('PASS: blur/composition before tap, cancelled gestures, and keyboard activation');
