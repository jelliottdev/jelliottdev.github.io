'use strict';
// Production home handlers in an isolated DOM fixture; no browser, network or real files.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../home.js'),'utf8');
const markup=fs.readFileSync(require.resolve('../home.html'),'utf8'),previewTag=markup.match(/<div\b[^>]*id="file-preview"[^>]*>/)?.[0];
assert(previewTag&&/tabindex="0"/.test(previewTag)&&/role="region"/.test(previewTag)&&/aria-label="File preview"/.test(previewTag),'Long local previews have a named keyboard-focusable scroll region');
assert(/\.file-preview:focus-visible\{[^}]*outline:2px solid/.test(fs.readFileSync(require.resolve('../home-intake.css'),'utf8')),'Keyboard focus remains visible on the preview region');
const Input=require('../idea-input.js');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
class Element{
 constructor(id=''){this.id=id;this.children=[];this.value='';this.listeners={};this.dataset={};this.classList={add(){},remove(){}};this.files=[];}
 addEventListener(type,handler){this.listeners[type]=handler;}
 setCustomValidity(message){this.validationMessage=message;}replaceChildren(){this.children=[];}append(...items){this.children.push(...items);}
 setAttribute(name,value){this[name]=value;}showModal(){this.open=true;}focus(){}
 get innerHTML(){return this.markup||'';}set innerHTML(value){this.markup=value;}
 reportValidity(){return !this.validationMessage;}
}
function fixture({attachments=true}={}){
 const ids=new Map(),get=id=>{if(!ids.has(id))ids.set(id,new Element(id));return ids.get(id);};
 const reads=[],windowEvents={},revoked=[],navigations=[];
 const text={name:'synthetic-example.js',type:'text/javascript',size:48,lastModified:1,slice(){const read=deferred();reads.push(read);return {text:()=>read.promise};}};
 const image={name:'synthetic-image.png',type:'image/png',size:64,lastModified:1};
 const env={IdeaInput:require('../idea-input.js'),document:{getElementById:get,createElement:tag=>Object.assign(new Element(),{tagName:tag.toUpperCase()})},
  window:{indexedDB:{open:()=>({})},addEventListener(type,handler){windowEvents[type]=handler;}},sessionStorage:{getItem:()=>'',setItem(){}},crypto,Blob,
  URL:{createObjectURL:()=> 'blob:synthetic-local-image',revokeObjectURL(url){revoked.push(url);}},location:{assign(url){navigations.push(url);}},console};
 vm.runInNewContext(source,env,{filename:'home.js'});
 if(attachments){get('file-input').files=[text,image];get('file-input').onchange();
 // Open through the actual first attachment action, then use its real dialog buttons.
 get('attachments').children[0].children[0].onclick();}
 return {get,reads,revoked,navigations,pagehide:persisted=>windowEvents.pagehide({persisted}),select:index=>get('review-tabs').children[index].onclick(),preview:()=>get('file-preview').children};
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
function cachedNavigation(){
 const f=fixture();f.select(1);const image=f.preview()[0];
 f.pagehide(true);assert.deepEqual(f.revoked,[],'A page kept for Back navigation retains its live image URLs');
 assert.equal(f.preview()[0],image);f.select(1);assert.equal(f.preview()[0].src,image.src);
 f.pagehide(false);assert.deepEqual(f.revoked,['blob:synthetic-local-image'],'Discarding the page releases image URLs');
 f.pagehide(false);assert.equal(f.revoked.length,1,'Released URLs are cleared');
}
function exactTextHandoff(){
 for(const text of ['ᚠ'.repeat(1500),'😀'.repeat(750),'  code("<&+#%?");\n\treturn "ᚠ 字";\n  ']){
  for(const attachments of [false,true]){
   const f=fixture({attachments}),field=f.get(attachments?'review-idea':'idea');field.value=text;
   f.get(attachments?'review-form':'check-idea').listeners.submit({preventDefault(){}});
   assert.equal(f.navigations.length,1);const link=new URL(f.navigations[0],'https://example.org/');
   assert.equal(link.pathname,'/investigate.html');assert.equal(link.search,'?v=complete-current-20261024','Only a fixed checker-version marker belongs in the HTTP request target');
   assert.equal(Input.read(link).text,text,'The real home handler must preserve all text through the shared checker decoder');
   assert.equal(f.navigations[0],Input.href(text));
  }
 }
 const invalid=fixture({attachments:false});invalid.get('idea').value='ᚠ'.repeat(1501);invalid.get('check-idea').listeners.submit({preventDefault(){}});
 assert.equal(invalid.navigations.length,0);assert.equal(invalid.get('idea').value.length,1501,'Overlong drafts stay editable without truncation');
 assert.equal(Input.read({search:'?q=old+link%20%26%20%E1%9A%A0'}).text,'old link & ᚠ');
 assert(Input.read({hash:'#input=%E1'}).error);assert.equal(Input.read({hash:'#input=%E1',search:'?q=other'}).text,'','Broken fragments must not silently compare a different query');
 assert.throws(()=>Input.href(' '));assert.throws(()=>Input.href('x'.repeat(1501)));
 const home=fs.readFileSync(require.resolve('../home.html'),'utf8');assert(home.indexOf('src="idea-input.js')<home.indexOf('src="home.js'),'Shared contract loads before home handlers');
 console.log('PASS home handoff: exact Unicode/emoji/code at the limit, text-only and file-review routes, no text in HTTP query, legacy links and malformed-link recovery.');
}
function titleDraftHandoff(){
 const f=fixture({attachments:false}),entry=f.get('idea-entry');
 assert.equal(entry.href,'investigate.html?v=complete-current-20261024');
 const text='  Compare ᚠ and 字\nwith 0X / 0x  ';f.get('idea').value=text;f.get('idea').listeners.input();
 assert.equal(entry.href,Input.href(text),'The title link preserves exact draft text, including for native modified clicks');
 let prevented=false;entry.listeners.click({preventDefault(){prevented=true;}});
 assert.equal(prevented,false);assert.equal(f.navigations.length,0,'The title remains navigation and never submits a check');
 assert.equal(Input.read(new URL(entry.href,'https://example.org/')).text,text);
 f.get('idea').value='x'.repeat(1501);entry.listeners.click({preventDefault(){prevented=true;}});
 assert.equal(prevented,true);assert.equal(f.get('idea').value.length,1501);assert.match(f.get('idea-feedback').textContent,/1,500/);
 assert(markup.includes('href="research.html?help=1">Help with an existing check</a>'));
 console.log('PASS home title: exact draft navigation, no submission, overlong draft recovery and direct existing-check route.');
}
(async()=>{await switchedRead('success');await switchedRead('failure');await sameFileRecovery();await overlappingSameFile();cachedNavigation();exactTextHandoff();titleDraftHandoff();console.log('PASS production home preview: stale reads ignored, current errors and exact-code retry preserved, Back-cache URLs retained and discarded-page URLs released; no browser/network/uploads.');})().catch(error=>{console.error(error);process.exitCode=1;});
