/* Real reader options handler: delayed metadata must not open over later intent. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../manuscript-reader.js'),'utf8');
const start=source.indexOf('let optionsRequestVersion='),end=source.indexOf("$('#search-layer').onchange=",start);
assert(start>=0&&end>start);assert(source.includes("$('#options-button').onclick=openOptions;"));
function fixture(focused=true){
 const opener={},body={},document={activeElement:focused?opener:body},requests=[],events=[],dialogs=[];
 const options={showModal(){events.push('open');dialogs.push(options)}};
 const context={document,state:{id:'lp2-15'},navigationVersion:0,$:s=>{assert.equal(s,'#options');return options},$$:s=>{assert.equal(s,'dialog[open]');return dialogs},getPage:id=>new Promise((resolve,reject)=>requests.push({id,resolve,reject})),updateVersions:p=>events.push('versions:'+p.id),updateBar:()=>events.push('bar'),toast:text=>events.push(text)};
 vm.createContext(context);vm.runInContext(source.slice(start,end),context);
 return{context,document,opener,body,requests,events,dialogs,click:()=>context.openOptions()};
}
(async()=>{
 for(const focused of [true,false]){const f=fixture(focused),pending=f.click();assert.equal(f.requests[0].id,'lp2-15');f.requests[0].resolve({id:'lp2-15'});await pending;assert.deepEqual(f.events,['versions:lp2-15','bar','open'],'Normal click opens, including browsers that leave focus on body');}
 for(const fail of [false,true])for(const change of ['page','navigation','focus','dialog']){
  const f=fixture(),pending=f.click();
  if(change==='page')f.context.state.id='lp2-16';
  if(change==='navigation')f.context.navigationVersion++;
  if(change==='focus')f.document.activeElement={};
  if(change==='dialog')f.dialogs.push({});
  fail?f.requests[0].reject(Error('old request')):f.requests[0].resolve({id:'lp2-15'});
  await pending;assert.deepEqual(f.events,[],change+' invalidates stale success/error without focus theft or toast');
 }
 const overlap=fixture(),old=overlap.click(),latest=overlap.click();overlap.requests[0].resolve({id:'lp2-15'});await old;assert.deepEqual(overlap.events,[]);overlap.requests[1].resolve({id:'lp2-15'});await latest;assert.deepEqual(overlap.events,['versions:lp2-15','bar','open']);
 const failure=fixture(),pending=failure.click();failure.requests[0].reject(Error('unavailable'));await pending;assert.deepEqual(failure.events,['Page options unavailable.']);
 const retry=failure.click();failure.requests[1].resolve({id:'lp2-15'});await retry;assert.deepEqual(failure.events,['Page options unavailable.','versions:lp2-15','bar','open']);
 console.log('PASS reader options: normal/body-focus click, stale page/navigation/focus/dialog success and failure, superseded requests, current error and retry; production handler VM, no network.');
})().catch(error=>{console.error(error);process.exitCode=1});
