'use strict';
// Production handlers with per-tab storage; every service is an offline mock.
const assert=require('node:assert/strict'),fs=require('node:fs');
const I=require('../investigate.js'),C=require('../claim-specification.js'),H=require('../claim-share.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const KEY='liberpedia-idea-draft-v1';
const decode=s=>s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
class Element{
 constructor(id){this.id=id;this.listeners={};this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.html='';}
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
 fire(type){for(const fn of this.listeners[type]||[])fn({target:this,preventDefault(){}});}
 focus(){}remove(){}replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;this.onRender?.();}get innerHTML(){return this.html;}
 insertAdjacentHTML(_,value){this.html+=value;}
}
function storage(){const data=new Map();return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};}
function documentFixture(session,search='',hash=''){
 const host=new Element('investigate'),print=new Element('print-snapshot'),cache=new Map();let radios=[];
 host.onRender=()=>{cache.clear();radios=[];for(const m of host.html.matchAll(/<input\b[^>]*name="choice"[^>]*>/g)){const radio=new Element('');radio.value=m[0].match(/value="([^"]*)"/)[1];radios.push(radio);}};
 return {defaultView:{location:{search,hash},sessionStorage:session},host,print,
  getElementById(id){if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id)){const field=new Element(id),tag=host.html.match(new RegExp('<([a-z]+)[^>]*id="'+id+'"[^>]*>'));
    field.disabled=/\sdisabled(?:\s|>|=)/.test(tag[0]);
    if(tag[1]==='textarea')field.value=decode(host.html.slice(tag.index+tag[0].length).split('</textarea>')[0]);
    else if(tag[1]==='select'){const body=host.html.slice(tag.index+tag[0].length).split('</select>')[0],selected=body.match(/<option value="([^"]*)"[^>]*selected/);field.value=decode(selected?.[1]??body.match(/<option value="([^"]*)"/)?.[1]??'');}
    else field.value=decode(tag[0].match(/value="([^"]*)"/)?.[1]||'');
    if(id==='method-step-list')field.onRender=()=>{host.html=host.html.replace(/(<ol[^>]*id="method-step-list"[^>]*>)[\s\S]*?(<\/ol>)/,'$1'+field.html+'$2');for(const key of cache.keys())if(key.startsWith('edit-method')||key.startsWith('method-up-')||key.startsWith('method-down-')||key.startsWith('method-remove-'))cache.delete(key);};
    cache.set(id,field);
   }return cache.get(id);},
  querySelector(selector){if(selector==='input[name=choice]:checked')return radios.find(r=>r.checked)||null;return selector.startsWith('#')?this.getElementById(selector.slice(1)):null;},
  querySelectorAll(selector){return selector==='input[name=choice]'?radios:[];}};
}
async function fixture(session,options={}){
 const doc=documentFixture(session,options.search,options.hash),calls=[];
 const app=I.createApp(doc,{now:()=>options.at||'2026-10-24T12:00:00.000Z',id:()=> 'recovery-test',schedule:()=>0,unschedule:()=>{},renderCard:()=>Promise.reject(),fetcher:async(url,request)=>{
  if(url==='https://mock.example/interpret'&&!options.interpret)return require('./mock_interpretation_response.cjs')(request);
  if(request?.method==='POST'){calls.push({url,request});return new Promise(()=>{});}
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  return Response.json({endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret'});
 }});await app.ready;return {doc,app,calls,pending:options.interpret};
}
async function submit(f,text){const field=f.doc.getElementById('idea');field.value=text;field.fire('input');f.doc.getElementById('define-test').fire('click');if(!f.pending)await reviewed(f);}
async function reviewed(f){const end=Date.now()+5000;while(f.app.getSnapshot().stage!=='review'&&Date.now()<end)await new Promise(resolve=>setImmediate(resolve));assert.equal(f.app.getSnapshot().stage,'review',f.doc.getElementById('interpretation-error')?.textContent);}
function answer(f,choice,text=''){for(const radio of f.doc.querySelectorAll('input[name=choice]'))radio.checked=radio.value===choice;f.doc.getElementById('other-detail').value=text;f.doc.getElementById('clarification').fire('submit');}
async function main(){
 const session=storage(),text='Use Vigenere with key "A B".';
 let f=await fixture(session);await submit(f,text);answer(f,'undecided');answer(f,'specific','LP2-00, LP2-02; lines 2–3');
 const baseline=C.serialize(f.app.getSnapshot().draft);f.app.destroy();
 f=await fixture(session);assert.equal(f.app.getSnapshot().stage,'review');assert.equal(C.serialize(f.app.getSnapshot().draft),baseline);assert.deepEqual(I.intakeQuestions(f.app.getSnapshot().draft),[]);assert.equal(f.app.getSnapshot().confirmed,null);assert.equal(f.calls.length,0);assert.match(f.doc.host.html,/Draft restored\./);
 f.doc.getElementById('edit').fire('click');
 const editingDraft=C.serialize(f.app.getSnapshot().draft);
 const method=f.doc.getElementById('edit-method'),scope=f.doc.getElementById('edit-scope'),objective=f.doc.getElementById('edit-objective');
 method.value='Apply Vigenere with key "C D", then reverse rows.';method.fire('input');scope.value='LP2-05, lines 4–6';scope.fire('input');objective.value='Only the first twelve runes';objective.fire('input');
 const remove=f.doc.getElementById('remove-rule-exceptionalCases');if(remove){remove.checked=true;remove.fire('change');}
 f.app.destroy();f=await fixture(session);
 assert.equal(f.doc.getElementById('edit-method').value,'Apply Vigenere with key "C D", then reverse rows.');assert.equal(f.doc.getElementById('edit-scope').value,'LP2-05, lines 4–6');assert.equal(f.doc.getElementById('edit-objective').value,'Only the first twelve runes');assert.equal(C.serialize(f.app.getSnapshot().draft),editingDraft,'Unsaved text must not be interpreted as applied semantics');
 assert.equal(f.calls.length,0);f.doc.getElementById('cancel-edit').fire('click');assert.equal(C.serialize(f.app.getSnapshot().draft),baseline,'Cancel restores original draft including acknowledgements');f.app.destroy();

 // Newly rendered method controls keep their recovery listeners.
 const steps=storage();f=await fixture(steps);await submit(f,'Reverse each row.');require('./mock_interpretation_response.cjs').acknowledge(f.doc,f.app);f.doc.getElementById('edit').fire('click');const stepBaseline=C.serialize(f.app.getSnapshot().draft);f.doc.getElementById('method-add').fire('click');const newStep=f.doc.getElementById('edit-method-1');assert(newStep);newStep.value='Apply Vigenere with key Z';newStep.fire('input');f.app.destroy();f=await fixture(steps);assert.equal(f.doc.getElementById('edit-method-1').value,'Apply Vigenere with key Z');assert.equal(f.app.getSnapshot().draft.method.value.operations[1].label,'','New unsaved step wording is only an overlay');f.doc.getElementById('cancel-edit').fire('click');assert.equal(f.app.getSnapshot().draft.method.value.operations.length,1);assert.equal(f.app.getSnapshot().draft.revision,JSON.parse(stepBaseline).revision-1);f.app.destroy();

 // Pending Other text and selected radio survive without applying the answer.
 const pending=storage();f=await fixture(pending);await submit(f,'Reverse each row.');
 const radio=f.doc.querySelectorAll('input[name=choice]').find(r=>r.value==='unclassified');radio.checked=true;radio.fire('change');const other=f.doc.getElementById('other-detail');other.value='Explain the spacing';other.fire('input');const before=C.serialize(f.app.getSnapshot().draft);f.app.destroy();
 f=await fixture(pending);assert.equal(f.doc.querySelector('input[name=choice]:checked').value,'unclassified');assert.equal(f.doc.getElementById('other-detail').value,'Explain the spacing');assert.equal(f.doc.getElementById('other-detail').hidden,false);assert.equal(C.serialize(f.app.getSnapshot().draft),before);f.app.destroy();

 // An in-flight interpretation returns to exact input and never restarts.
 const waiting=storage();f=await fixture(waiting,{interpret:true});await submit(f,'Try an autokey on LP2-15.');assert.equal(f.calls.length,1);f.app.destroy();f=await fixture(waiting,{interpret:true});assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.doc.getElementById('idea').value,'Try an autokey on LP2-15.');assert.equal(f.calls.length,0);f.app.destroy();
 const hinted=storage(),search='?q=Reverse+each+row.&pages=LP2-17';f=await fixture(hinted,{search});f.app.destroy();f=await fixture(hinted,{search});f.doc.getElementById('define-test').fire('click');await reviewed(f);assert.deepEqual(f.app.getSnapshot().draft.scope.value.pages,['lp2-17'],'An input-stage recovery retains the unconsumed URL page hint');f.app.destroy();

 // A finalized card is recovered only as a draft, with no result or POST.
 f=await fixture(session);f.doc.getElementById('confirm').fire('click');assert.equal(f.app.getSnapshot().stage,'research');assert(f.app.getSnapshot().confirmed);f.app.destroy();f=await fixture(session);assert.equal(f.app.getSnapshot().stage,'review');assert.equal(f.app.getSnapshot().confirmed,null);assert.equal(f.app.getSnapshot().result,null);assert.equal(f.app.getSnapshot().packet,null);assert.equal(f.calls.length,0);f.app.destroy();

 // Explicit new q / imported card always wins over a different saved entry.
 f=await fixture(session,{search:'?q=New+idea&pages=LP2-17'});assert.equal(f.app.getSnapshot().stage,'input');assert.equal(f.doc.getElementById('idea').value,'New idea');f.app.destroy();
 const shared=C.confirm(C.createDraft({source:{text:'Original'},method:C.field('specified',{operations:[{id:'described_method',label:'A literal supplied rule'}]})}),{id:'shared',at:'2026-10-24'}),fragment=H.encode(shared);
 f=await fixture(session,{hash:fragment});assert.equal(f.app.getSnapshot().draft.source.origin,'shared_link');assert.equal(f.app.getSnapshot().draft.method.value.operations[0].label,'A literal supplied rule');require('./mock_interpretation_response.cjs').acknowledge(f.doc,f.app);f.doc.getElementById('edit').fire('click');f.doc.getElementById('edit-method').value='Recipient revised exact rule';f.doc.getElementById('edit-method').fire('input');f.app.destroy();
 f=await fixture(session,{hash:fragment});assert.equal(f.doc.getElementById('edit-method').value,'Recipient revised exact rule');assert.equal(f.app.getSnapshot().draft.source.origin,'shared_link');assert.equal(f.calls.length,0);f.app.destroy();

 for(const stored of ['{broken',JSON.stringify({version:99}), 'x'.repeat(160001)]){const bad=storage();bad.setItem(KEY,stored);f=await fixture(bad);assert.equal(f.app.getSnapshot().stage,'input');f.app.destroy();}
 const stale=storage();stale.setItem(KEY,session.getItem(KEY));f=await fixture(stale,{at:'2026-10-26T12:00:00Z',hash:fragment});assert.equal(f.doc.getElementById('edit-method'),null);f.app.destroy();
 const blocked={getItem(){throw Error('blocked');},setItem(){throw Error('quota');},removeItem(){throw Error('blocked');}};f=await fixture(blocked);await submit(f,'Reverse each row.');assert.equal(f.app.getSnapshot().stage,'review');f.app.destroy();
 console.log('PASS tab-session recovery: exact draft/source/acknowledgements, unapplied editor+Cancel, pending Other, no restarted services/results, entry precedence, shared-card edits, stale/corrupt/unavailable storage.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
