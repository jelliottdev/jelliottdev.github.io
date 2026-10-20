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

// Exercise the actual header input handler with an Android-style composing event.
// This is an isolated event test, not a physical-device keyboard simulation.
const vm=require('node:vm');
function target(){return {listeners:{},attrs:{},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(name,value){this.attrs[name]=value},getBoundingClientRect(){return {bottom:100}},contains(){return false}}}
const input=target(),form=target(),panel=target();input.value='Atba';
form.append=()=>{};panel.hidden=true;
const sandbox={db,WikiSearch:search,esc:String,marked:String,excerpt:String,
 $:s=>({'#search':input,'#search-form':form,'#search-suggestions':panel}[s]),
 document:{createElement:()=>panel,addEventListener(){}},
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
