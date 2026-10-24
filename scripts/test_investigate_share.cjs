/* Shared links never submit research. All network/native APIs are mocked. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const C=require('../claim-specification.js'),H=require('../claim-share.js'),I=require('../investigate.js');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
class Element{
 constructor(){this.listeners={};this.html='';this.value='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){} replaceChildren(){this.html='';}
 set innerHTML(v){this.html=v;}get innerHTML(){return this.html;}
 insertAdjacentHTML(_,v){this.html+=v;}
}
function documentFor(hash){
 const host=new Element(),print=new Element(),cache=new Map();
 Object.defineProperty(host,'innerHTML',{get(){return this.html;},set(v){this.html=v;cache.clear();}});
 return {host,defaultView:{location:{search:'',hash}},getElementById(id){
  if(id==='investigate')return host;if(id==='print-snapshot')return print;
  if(!host.html.includes('id="'+id+'"'))return null;
  if(!cache.has(id))cache.set(id,new Element());return cache.get(id);
 },querySelector(s){return s.startsWith('#')?this.getElementById(s.slice(1)):null;}};
}
const tick=()=>new Promise(r=>setTimeout(r,10));
async function until(predicate){const end=Date.now()+5000;while(Date.now()<end){if(predicate())return;await tick();}assert.fail('Share fixture did not reach the expected state');}
(async()=>{
 let source=I.initialDraft('Fibonacci keys on LP2-15');
 source=I.answerIntake(source,'aim','undecided');
 const confirmed=C.confirm(source,{id:'original',at:'2026-10-24T12:00:00Z'});
 const doc=documentFor(H.encode(confirmed));let posts=0,shares=0,releaseShare,shareResponse;
 const app=I.createApp(doc,{id:()=> 'recipient',now:()=> '2026-10-24T13:00:00Z',renderCard:async()=>new Blob(['png']),fetcher:async(url,options)=>{
  if(options?.method==='POST'){posts++;return Response.json({noMatch:true,sources:[]});}
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.invalid/ask'});
  return Response.json({documents:[]});
 },sharer:(snapshot,url)=>{shares++;assert.equal(snapshot,app.getSnapshot().confirmed);assert.equal(url,'https://jelliottdev.github.io/investigate.html');return shareResponse||new Promise(r=>releaseShare=r);}});
 await app.ready;assert.equal(posts,0);assert.equal(app.getSnapshot().stage,'review');
 assert.equal(app.getSnapshot().confirmed,null);assert(!doc.getElementById('share-idea'));
 assert.deepEqual(app.getSnapshot().draft.scope.value.pages,['lp2-15']);
 assert(doc.getElementById('confirm'),'unknown outcome remains acknowledged');
 doc.getElementById('confirm').fire('click');await until(()=>posts===1&&!app.getSnapshot().busy);assert.equal(posts,1);
 assert(doc.getElementById('share-idea'));assert(doc.host.html.includes('aria-label="Share confirmed idea"'));
 const pending=doc.getElementById('share-idea').fire('click');assert.equal(shares,1);
 doc.getElementById('share-idea').fire('click');assert.equal(shares,1,'double tap cannot share twice');
 releaseShare({status:'cancelled'});await pending;assert.equal(doc.getElementById('share-status').textContent,'');
 shareResponse=Promise.resolve({status:'copied',url:'https://example.invalid/#idea=abc'});
 await doc.getElementById('share-idea').fire('click');assert.equal(doc.getElementById('share-status').textContent,'Idea link copied.');
 assert(doc.getElementById('share-fallback').html.includes('readonly'));
 doc.getElementById('edit').fire('click');assert(!doc.getElementById('share-idea'));
 doc.getElementById('cancel-edit').fire('click');assert(doc.getElementById('share-idea'));
 app.destroy();
 const bad=documentFor('#idea=broken');const badApp=I.createApp(bad,{fetcher:async()=>Response.json({documents:[]})});
 assert.equal(badApp.getSnapshot().stage,'input');assert(bad.host.html.includes('could not be read'));badApp.destroy();
 console.log('PASS share integration: import preserves scope/no auto research; explicit confirmation reveals share; double tap guarded; cancel quiet; clipboard/manual fallback; edit hides share; malformed link recoverable.');
})().catch(e=>{console.error(e);process.exitCode=1;});
