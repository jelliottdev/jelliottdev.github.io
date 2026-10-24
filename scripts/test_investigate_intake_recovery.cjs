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
const INTAKE='liberpedia-idea-intake-v1',AT='2026-10-24T12:00:00.000Z';
const turn=()=>new Promise(resolve=>setImmediate(resolve));
const known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']});
const operations=[{id:'vigenere',label:'Vigenere with key ABC',parameters:{key:'ABC'}}];
function server(){return {ledger:new Map(),posts:[],defer:false,fetch(body){
 const prior=this.ledger.get(body.requestId);if(prior)assert.deepEqual(body,prior,'A retried request UUID must preserve every byte of the body');else this.ledger.set(body.requestId,body);
 const receipt={id:'p_'+'a'.repeat(64),status:prior?'already_received':'received',receivedAt:AT};
 const post={body,receipt};this.posts.push(post);
 if(this.defer)return new Promise(resolve=>{post.resolve=()=>resolve(Response.json(receipt));});
 return Promise.resolve(Response.json(receipt));
}};}
async function fixture(session,backend,options={}){
 const doc=documentFixture(session,options.search||'',options.hash||'');
 const entries=[];
 const app=I.createApp(doc,{now:()=>options.at||AT,schedule:()=>0,unschedule:()=>{},renderCard:()=>Promise.reject(),fetcher:async(url,request)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',proposalEndpoint:'https://mock.example/proposals',interpretationEndpoint:'https://mock.example/interpret',...(options.community?{researchIdeaEndpoint:'https://mock.example/ideas'}:{})});
  if(url==='https://mock.example/interpret')return require('./mock_interpretation_response.cjs')(request);
  if(url.endsWith('/proposals'))return backend.fetch(JSON.parse(request.body));
  if(url.endsWith('/ideas')){entries.push(JSON.parse(request.body));if(options.communityFailure&&entries.length===1)return Response.json({error:'Temporary failure'},{status:503});return Response.json({id:entries.at(-1).proposalId,card:H.cardData(app.getSnapshot().confirmed)});}
  return Response.json({answer:null,sources:[],reason:'no-matching-records'});
 }});await app.ready;return {doc,app,entries};
}
async function submit(f,text){if(!f.doc.getElementById('idea'))f.doc.getElementById('back').fire('click');f.doc.getElementById('idea').value=text;f.doc.getElementById('idea').fire('input');f.doc.getElementById('intake').fire('submit');
 await require('./mock_interpretation_response.cjs').waitForReview(f.app);
 require('./mock_interpretation_response.cjs').acknowledge(f.doc,f.app);
 const d=f.app.getSnapshot().draft;d.aim=C.normalizeAim(known({outcomeId:'decipher',wording:'Find readable text',detail:''}));d.method=known({operations:JSON.parse(JSON.stringify(operations))});d.scope=known({pages:['lp2-15']});
 // Re-render through the existing edit/cancel path after replacing fixture fields.
 f.doc.getElementById('edit').fire('click');f.doc.getElementById('cancel-edit').fire('click');
}
async function confirm(f){assert(f.doc.getElementById('confirm'));f.doc.getElementById('confirm').fire('click');await turn();await turn();}
async function main(){
 const communityBackend=server(),community=await fixture(storage(),communityBackend,{community:true,communityFailure:true});
 await submit(community,'Use Vigenere on LP2-15');
 assert(community.doc.host.html.includes('Your confirmed card becomes a shared research entry.'));
 assert.equal(community.entries.length,0,'An unconfirmed draft cannot publish an entry');
 await confirm(community);for(let i=0;i<4;i++)await turn();
 assert.equal(community.entries.length,1);assert.deepEqual(Object.keys(community.entries[0]),['proposalId']);
 assert(community.doc.getElementById('idea-save-status').textContent.includes('Idea saved.'));
 community.doc.getElementById('retry-save').fire('click');for(let i=0;i<4;i++)await turn();
 assert.equal(communityBackend.posts.length,1,'Entry retry does not resubmit the original contribution');
 assert.equal(community.entries.length,2);assert.equal(community.doc.getElementById('open-research-entry').hidden,false);
 assert.equal(community.doc.getElementById('open-research-entry').href,'run.html#idea='+community.entries[0].proposalId);
 community.app.destroy();
 console.log('PASS public entry: explicit confirmation, private source omitted, separate retry and confirmed-card link.');
 for(const value of ['ᚠ'.repeat(1500),'  example("<&+#%?");\n\treturn "字";\n ']){
  const hash=new URL(require('../idea-input.js').href(value),'https://example.org/').hash,backend=server(),f=await fixture(storage(),backend,{hash});
  assert.equal(f.doc.getElementById('idea').value,value);assert.equal(f.app.getSnapshot().stage,'input');assert.equal(backend.posts.length,0,'Opening the input does not submit the idea');f.app.destroy();
 }
 const malformed=await fixture(storage(),server(),{hash:'#input=%E1'});assert(malformed.doc.host.html.includes('This idea link could not be read'));assert.equal(malformed.app.getSnapshot().stage,'input');malformed.app.destroy();
 const longText='ᚠ'.repeat(1501),over=await fixture(storage(),server(),{hash:'#input='+encodeURIComponent(longText)});
 over.doc.getElementById('intake').fire('submit');assert.equal(over.app.getSnapshot().stage,'input');assert.equal(over.doc.getElementById('idea').value,longText);assert(over.doc.getElementById('interpretation-error').textContent.includes('1,500 characters'));over.app.destroy();
 console.log('PASS fragment entry: exact input, no automatic submission, malformed-link recovery and editable over-limit text.');
 const text='  Use Vigenere with key ABC on LP2-15.\nKeep this original wording: \u16a0.  ';
 const session=storage(),backend=server();backend.defer=true;
 let f=await fixture(session,backend);await submit(f,text);await confirm(f);
 assert.equal(backend.posts.length,1,f.doc.host.html);const first=backend.posts[0].body;
 assert.equal(first.originalIdea,text);assert(I.readIntake(session.getItem(INTAKE),Date.parse(AT)));
 f.app.destroy();
 f=await fixture(session,backend);assert.equal(f.app.getSnapshot().stage,'review');assert.equal(backend.posts.length,1,'Refresh must not submit or confirm the recovered draft');
 backend.defer=false;await confirm(f);assert.equal(backend.posts.length,2);assert.deepEqual(backend.posts[1].body,first,'Server commit before lost receipt retries the identical body/UUID');assert.equal(backend.ledger.size,1);
 assert.equal(f.doc.getElementById('idea-save-status').textContent||f.doc.host.html.match(/id="idea-save-status"[^>]*>([^<]*)/)[1], 'Saved.');assert.equal(JSON.parse(session.getItem(INTAKE)).receipt.status,'already_received');
 const storedReceipt=session.getItem(INTAKE);f.app.destroy();
 f=await fixture(session,backend);assert.equal(backend.posts.length,2);await confirm(f);assert.equal(backend.posts.length,3,'Reconfirmation verifies a local receipt by rePOSTing the same UUID');assert.deepEqual(backend.posts[2].body,first);assert.equal(backend.ledger.size,1);assert.equal(f.doc.getElementById('idea-save-status').textContent||f.doc.host.html.match(/id="idea-save-status"[^>]*>([^<]*)/)[1], 'Saved.');f.app.destroy();
 console.log('PASS refresh/receipt: explicit reconfirmation only, original bytes, server-commit ambiguity and one idempotent contribution, server-verified local receipts.');

 backend.defer=true;f=await fixture(session,backend);await submit(f,'A changed original, with the same standardized method.');await confirm(f);const oldPost=backend.posts.at(-1);assert.notEqual(oldPost.body.requestId,first.requestId);assert.equal(oldPost.body.fragment,first.fragment,'Only original wording changed');
 f.doc.getElementById('edit').fire('click');oldPost.resolve();await turn();assert.equal(JSON.parse(session.getItem(INTAKE)).receipt,null,'Old pending completion while editing cannot attach a receipt');
 f.doc.getElementById('cancel-edit').fire('click');f.doc.getElementById('back').fire('click');await submit(f,'A third source wording.');await confirm(f);const newest=backend.posts.at(-1);assert.notEqual(newest.body.requestId,oldPost.body.requestId);
 oldPost.resolve();await turn();assert.deepEqual(JSON.parse(session.getItem(INTAKE)).body,newest.body);assert.equal(JSON.parse(session.getItem(INTAKE)).receipt,null);
 newest.resolve();await turn();await turn();assert.equal(f.doc.getElementById('idea-save-status').textContent||f.doc.host.html.match(/id="idea-save-status"[^>]*>([^<]*)/)[1], 'Saved.');f.app.destroy();
 console.log('PASS edits: new original gets new contribution; late old receipt never binds a changed card or editor.');
 const changed=await fixture(session,backend);await submit(changed,'A third source wording.');
 const changedDraft=changed.app.getSnapshot().draft;changedDraft.scope=known({pages:['lp2-17']});
 await confirm(changed);const different=backend.posts.at(-1);
 assert.equal(different.body.originalIdea,newest.body.originalIdea);assert.notEqual(different.body.fragment,newest.body.fragment);assert.notEqual(different.body.requestId,newest.body.requestId,'Changed card with unchanged original creates a new contribution');changed.app.destroy();
 const failedSession=storage(),failedBackend=server();let failedBody;
 const normal=failedBackend.fetch;failedBackend.fetch=function(body){failedBody=body;return Promise.reject(Error('Offline'));};
 f=await fixture(failedSession,failedBackend);await submit(f,text);await confirm(f);assert.equal(f.doc.getElementById('retry-save').hidden,false);f.app.destroy();
 failedBackend.fetch=normal;f=await fixture(failedSession,failedBackend);assert.equal(failedBackend.posts.length,0);await confirm(f);assert.deepEqual(failedBackend.posts[0].body,failedBody,'Failed unsaved request also retries exact UUID/body after refresh');f.app.destroy();
 console.log('PASS contribution identity: changed card with same original gets new UUID; failed save survives refresh without background submission.');


 const shared=C.confirm(C.createDraft({source:{text:'Private sender wording'},aim:known({outcomeId:'decipher',detail:''}),method:known({operations}),scope:known({pages:['lp2-15']})}),{id:'shared',at:AT});
 const sharedSession=storage(),sharedServer=server(),hash=H.encode(shared);
 f=await fixture(sharedSession,sharedServer,{hash});await confirm(f);assert(!Object.hasOwn(sharedServer.posts[0].body,'originalIdea'),'Shared-card reconstruction must not become original wording');const sharedBody=sharedServer.posts[0].body;f.app.destroy();
 f=await fixture(sharedSession,sharedServer,{hash});assert.equal(sharedServer.posts.length,1);await confirm(f);assert.equal(sharedServer.posts.length,2);assert.deepEqual(sharedServer.posts[1].body,sharedBody);assert.equal(sharedServer.ledger.size,1);assert.deepEqual(JSON.parse(sharedSession.getItem(INTAKE)).body,sharedBody);f.app.destroy();
 console.log('PASS shared links: omission of original wording preserved across refresh and receipt revalidation.');
 const corrupt=JSON.parse(sharedSession.getItem(INTAKE));corrupt.receipt.id='p_'+'b'.repeat(64);sharedSession.setItem(INTAKE,JSON.stringify(corrupt));
 f=await fixture(sharedSession,sharedServer,{hash});assert.equal(sharedServer.posts.length,2);await confirm(f);assert.equal(sharedServer.posts.length,3);assert.equal(sharedServer.ledger.size,1);assert.equal(JSON.parse(sharedSession.getItem(INTAKE)).receipt.id,'p_'+'a'.repeat(64),'A valid-shaped wrong stored receipt must be replaced by the server receipt');f.app.destroy();


 const valid=JSON.parse(storedReceipt),bad=[null,{}, {...valid,version:2},{...valid,at:Date.parse(AT)-86400001},{...valid,at:Date.parse(AT)+1},{...valid,at:String(valid.at)},{...valid,url:'https://evil.example'}, {...valid,body:{...valid.body,endpoint:'https://evil.example/proposals'}},{...valid,body:{...valid.body,requestId:'bad'}},{...valid,body:{...valid.body,fragment:'#idea=broken'}},{...valid,body:{...valid.body,originalIdea:42}},{...valid,receipt:{...valid.receipt,token:'credential'}},{...valid,receipt:{...valid.receipt,status:'pending'}}];
 for(const value of bad)assert.equal(I.readIntake(JSON.stringify(value),Date.parse(AT)),null);
 assert.equal(I.readIntake('x'.repeat(40001),Date.parse(AT)),null);
 const stale=storage();stale.setItem(INTAKE,JSON.stringify({...valid,at:Date.parse(AT)-86400001}));const staleServer=server();f=await fixture(stale,staleServer);await submit(f,text);await confirm(f);assert.notEqual(staleServer.posts[0].body.requestId,first.requestId);f.app.destroy();
 const blocked={getItem(){throw Error('blocked');},setItem(){throw Error('quota');},removeItem(){throw Error('blocked');}};f=await fixture(blocked,server());await submit(f,text);await confirm(f);assert.equal(f.doc.getElementById('idea-save-status').textContent||f.doc.host.html.match(/id="idea-save-status"[^>]*>([^<]*)/)[1], 'Saved.');f.app.destroy();
 console.log('PASS bounded storage: expiry, malformed/extra fields, invalid share/UUID, no stored endpoint/credentials, unavailable storage fallback.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
