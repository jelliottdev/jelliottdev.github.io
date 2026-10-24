/* Editor preservation tests: actual event handlers, mocked local loads, no AI. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const C=require('../claim-specification.js');
const I=require('../investigate.js');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['exact supplied condition']});
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const decode=value=>value.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');

class Element{
 constructor(id){this.id=id;this.listeners={};this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.html='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){} remove(){} replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;}get innerHTML(){return this.html;}
 insertAdjacentHTML(where,value){this.html+=value;}
}
function fakeDocument(){
 const cache=new Map(),host=new Element('investigate'),print=new Element('print-snapshot');
 Object.defineProperty(host,'innerHTML',{get(){return this.html;},set(value){this.html=value;cache.clear();}});
 return {activeElement:null,defaultView:{location:{search:''}},host,print,
  getElementById(id){
   if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id)){
    const element=new Element(id),opening=host.html.match(new RegExp('<(input|textarea|select)[^>]*\\bid="'+id+'"[^>]*>'));
    if(opening){
     if(opening[1]==='input')element.value=decode(opening[0].match(/\bvalue="([^"]*)"/)?.[1]||'');
     else{
      const start=opening.index+opening[0].length,end=host.html.indexOf('</'+opening[1]+'>',start),content=host.html.slice(start,end);
      element.value=opening[1]==='textarea'?decode(content):decode(content.match(/<option\s+value="([^"]*)"\s+selected/)?.[1]||'');
     }
    }
    cache.set(id,element);
   }
   return cache.get(id);
  },
  querySelector(selector){if(selector.startsWith('#'))return this.getElementById(selector.slice(1));return null;}
 };
}
async function appFor(text){
 const doc=fakeDocument(),app=I.createApp(doc,{fetcher:async url=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:null});
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  throw Error('No inference or external fetch is allowed');
 }});
 await app.ready;
 doc.getElementById('idea').value=text;doc.getElementById('intake').fire('submit');
 return {doc,app};
}
function openEditor(doc){doc.getElementById('edit').fire('click');assert(doc.getElementById('editor'));}
function save(doc){doc.getElementById('editor').fire('submit');assert(!doc.getElementById('editor'),doc.getElementById('error')?.textContent);}

(async()=>{
 // No-op/aim-only editing of the actual parsed page+passage object must not
 // reduce it to only the displayed description or rewrite its provenance.
 const first=await appFor('Reverse each row on LP2-43, lines 2–3');
 const originalScope=structuredClone(first.app.getSnapshot().draft.scope);
 assert.deepEqual(originalScope.value,{pages:['lp2-43'],description:'LP2-43, lines 2–3'});
 openEditor(first.doc);first.doc.getElementById('edit-aim').value='measure';
 first.doc.getElementById('edit-objective').value='Compare the row structure';save(first.doc);
 assert.deepEqual(first.app.getSnapshot().draft.scope,originalScope);
 assert.equal(first.app.getSnapshot().draft.aim.outcome.id,'measure');first.app.destroy();

 const second=await appFor('Reverse each row');
 const state=second.app.getSnapshot().draft;
 state.scope=known({pages:['lp2-15'],description:'LP2-15, lines 2–3',artifacts:['fixed-panel.json'],inputVersion:'sha256:original',exclusions:['red passage']});
 state.rules={...state.rules,wordBoundaries:known('preserve'),boundaryMode:known('within_words'),representation:known('GP prime values'),reset:known('per_page'),searchBounds:C.field('unrestricted'),evaluation:C.field('not_applicable')};
 const before=structuredClone(state),typed=structuredClone(state.rules);
 openEditor(second.doc);
 assert.equal(second.doc.getElementById('edit-rules').value,'','Additional conditions must not contain flattened structured fields');
 assert(second.doc.host.html.includes('Other supplied scope details are kept'));
 assert(second.doc.host.html.includes('Evaluation: not applicable'));
 second.doc.getElementById('edit-rules').value='Do not cross the red passage.';save(second.doc);
 let saved=second.app.getSnapshot().draft;
 for(const key of C.RULES.filter(k=>k!=='exceptionalCases'))assert.deepEqual(saved.rules[key],typed[key],key);
 assert.equal(saved.rules.exceptionalCases.value,'Do not cross the red passage.');
 assert.deepEqual(saved.scope,before.scope);assert.equal(C.questions(saved).length,0);

 // Clearing the one notes field clears only that field.
 openEditor(second.doc);second.doc.getElementById('edit-rules').value='';save(second.doc);
 saved=second.app.getSnapshot().draft;
 assert.equal(saved.rules.exceptionalCases.status,'unspecified');
 for(const key of C.RULES.filter(k=>k!=='exceptionalCases'))assert.deepEqual(saved.rules[key],typed[key],key);

 // A deliberate page/passage replacement owns those two keys only. Preserve
 // exact artifact/version/exclusion fields and retain holes in the new set.
 openEditor(second.doc);second.doc.getElementById('edit-scope').value='LP2-17, LP2-19';save(second.doc);
 saved=second.app.getSnapshot().draft;
 assert.deepEqual(saved.scope.value,{pages:['lp2-17','lp2-19'],artifacts:['fixed-panel.json'],inputVersion:'sha256:original',exclusions:['red passage']});
 assert.deepEqual(before.scope.value.pages,['lp2-15'],'Original supplied object stays unchanged');
 assert(!Object.hasOwn(saved.scope.value,'description'));

 // Remove one named condition, not the whole set. The remaining four states
 // and their provenance survive and appear in the next confirmed context.
 openEditor(second.doc);second.doc.getElementById('remove-rule-reset').checked=true;save(second.doc);
 saved=second.app.getSnapshot().draft;assert.equal(saved.rules.reset.status,'unspecified');
 for(const key of C.RULES.filter(k=>!['reset','exceptionalCases'].includes(k)))assert.deepEqual(saved.rules[key],typed[key],key);
 const confirmed=C.confirm(saved,{id:'next',at:'2026-10-24T18:00:00Z'}),query=C.queryForResearch(confirmed,{maxLength:6000});
 assert(query.query.includes('fixed-panel.json'));assert(query.query.includes('sha256:original'));
 assert(query.query.includes('"status":"not_applicable"'));assert(query.query.includes('"status":"unrestricted"'));
 assert.deepEqual(query.pages,['lp2-17','lp2-19']);
 second.app.destroy();

 // Empty editor projections do not conflate unspecified, not-applicable,
 // unrestricted or an explicit empty page selection.
 for(const scope of [C.field(),C.field('not_applicable'),C.field('unrestricted'),known({pages:[]}),known({artifacts:['only.bin']})]){
  assert.equal(I.scopeEdit(scope,I.scopeEditorText(scope)),undefined);
 }
 const cleared=I.scopeEdit(before.scope,'');
 assert.deepEqual(cleared.value,{artifacts:['fixed-panel.json'],inputVersion:'sha256:original',exclusions:['red passage']});
 for(const field of [C.field(),C.field('not_applicable'),C.field('unrestricted'),known({maxSkipped:3})]){
  const rules={...typed,exceptionalCases:field};assert.equal(I.ruleEdits(rules,I.ruleNotesText(rules)),undefined);
 }
 assert.throws(()=>I.ruleEdits(typed,'',['not-a-rule']));
 console.log('PASS editor fidelity: real parsed page+passage survives aim edit; typed rules/provenance/four states survive notes; targeted removal and selection-only replacements retain other inputs; confirmed context stays exact. No inference.');
})().catch(error=>{console.error(error);process.exitCode=1;});
