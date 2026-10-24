'use strict';
// Production home handlers in an isolated DOM fixture; no browser, network or real files.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../home.js'),'utf8');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
class Element{
 constructor(id=''){this.id=id;this.children=[];this.value='';this.listeners={};this.dataset={};this.classList={add(){},remove(){}};this.files=[];}
 addEventListener(type,handler){this.listeners[type]=handler;}
 setCustomValidity(){}replaceChildren(){this.children=[];}append(...items){this.children.push(...items);}
 setAttribute(name,value){this[name]=value;}showModal(){this.open=true;}focus(){}
 get innerHTML(){return this.markup||'';}set innerHTML(value){this.markup=value;}
 reportValidity(){return true;}
}
function fixture(){
 const ids=new Map(),get=id=>{if(!ids.has(id))ids.set(id,new Element(id));return ids.get(id);};
 const reads=[];
 const text={name:'synthetic-example.js',type:'text/javascript',size:48,lastModified:1,slice(){const read=deferred();reads.push(read);return {text:()=>read.promise};}};
 const image={name:'synthetic-image.png',type:'image/png',size:64,lastModified:1};
 const env={document:{getElementById:get,createElement:tag=>Object.assign(new Element(),{tagName:tag.toUpperCase()})},
  window:{indexedDB:{open:()=>({})},addEventListener(){}},sessionStorage:{getItem:()=>'',setItem(){}},crypto,Blob,
  URL:{createObjectURL:()=> 'blob:synthetic-local-image',revokeObjectURL(){}},location:{assign(){assert.fail('Preview cannot navigate or submit');}},console};
 vm.runInNewContext(source,env,{filename:'home.js'});
 get('file-input').files=[text,image];get('file-input').onchange();
 // Open through the actual first attachment action, then use its real dialog buttons.
 get('attachments').children[0].children[0].onclick();
 return {get,reads,select:index=>get('review-tabs').children[index].onclick(),preview:()=>get('file-preview').children};
}
async function switchedRead(kind){
 const f=fixture();assert.equal(f.reads.length,1);f.select(1);
 const image=f.preview()[0];assert.equal(image.src,'blob:synthetic-local-image');assert.equal(f.get('review-tabs').children[1]['aria-pressed'],'true');
 if(kind==='success')f.reads[0].resolve('OLD FILE CONTENT');else f.reads[0].reject(Error('Synthetic old file read failure'));
 await turn();assert.equal(f.preview().length,1,'A stale '+kind+' cannot append to the current file');assert.equal(f.preview()[0],image,'A stale '+kind+' cannot replace the current image');
}
async function sameFileRecovery(){
 const f=fixture();f.reads[0].reject(Error('Synthetic current read failure'));await turn();
 assert.equal(f.preview().length,1);assert.equal(f.preview()[0].textContent,'The file could not be previewed. It is still attached.','A current failure is visible');
 assert.equal(f.get('attachments').children.length,2,'A failed read keeps its attachment');
 f.select(0);assert.equal(f.preview().length,0,'Selecting the file again clears the old error');assert.equal(f.reads.length,2);
 const content='function sample() {\n  return "<literal>";\n}\n';f.reads[1].resolve(content);await turn();
 assert.equal(f.preview().length,1);assert.equal(f.preview()[0].tagName,'PRE');assert.equal(f.preview()[0].textContent,content,'Retry restores exact code/whitespace as text');
 assert.equal(f.get('review-tabs').children[0]['aria-pressed'],'true');
}
async function overlappingSameFile(){
 const f=fixture();f.select(0);assert.equal(f.reads.length,2);f.reads[1].resolve('NEWEST READ');await turn();const newest=f.preview()[0];
 f.reads[0].reject(Error('Older same-file failure'));await turn();assert.equal(f.preview().length,1);assert.equal(f.preview()[0],newest);assert.equal(newest.textContent,'NEWEST READ','Older same-file attempts cannot corrupt a successful retry');
}
(async()=>{await switchedRead('success');await switchedRead('failure');await sameFileRecovery();await overlappingSameFile();console.log('PASS production home preview: switched-file delayed success/failure ignored, current error retained, exact-code retry recovery, overlapping same-file reads guarded; no browser/network/uploads.');})().catch(error=>{console.error(error);process.exitCode=1;});
