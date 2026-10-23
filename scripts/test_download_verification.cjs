/* Production download-verifier races with deferred file reads/digests. No browser. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {createHash}=require('node:crypto');
const bytes=Uint8Array.from([1,2,3]),hash=createHash('sha256').update(bytes).digest('hex');
const digestBytes=Uint8Array.from(Buffer.from(hash,'hex')).buffer;
const nodes=new Map();let digestCalls=0;
const $=key=>{if(!nodes.has(key))nodes.set(key,{value:'',textContent:'',innerHTML:'',isConnected:true});return nodes.get(key)};
const realDigest=async()=>{digestCalls++;return digestBytes};
const context={localStorage:{getItem:()=>null},document:{addEventListener(){},activeElement:{id:'reading-link'}},$,
 db:{catalog:{files:[{path:'images/fixture.jpg',role:'Original JPEG',sha256:hash,bytes:3}]}},renderId:1,
 head:()=>'',footer:()=>'',esc:String,matches:()=>true,crypto:{subtle:{digest:realDigest}},
 main:{set innerHTML(value){for(const node of nodes.values())node.isConnected=false;nodes.clear()}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'..','access.js'),'utf8'),context);
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no});return {promise,resolve,reject}};
const file=read=>({size:3,arrayBuffer:read});
const render=()=>context.downloadsPage('',1);
const start=chosen=>$('#verify-file').onchange({target:{files:[chosen]}});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const guard=setTimeout(()=>{console.error('Verifier race test did not finish');process.exitCode=1},5000);
(async()=>{
 await render();const focus=context.document.activeElement;
 const oldRead=deferred(),oldResult=$('#verify-result'),oldPending=start(file(()=>oldRead.promise));
 assert.equal(oldResult.textContent,'Calculating SHA-256…');
 await render();const newResult=$('#verify-result');oldRead.resolve(bytes.buffer);await oldPending;
 assert.equal(newResult.textContent,'','An old read cannot write into a replacement Downloads page');
 assert.equal(digestCalls,0,'A superseded file read is discarded before hashing');
 assert.equal(context.document.activeElement,focus,'Verification does not move or hide reading focus');
 const first=deferred(),second=deferred();
 const firstPending=start(file(()=>first.promise)),secondPending=start(file(()=>second.promise));
 second.resolve(bytes.buffer);await secondPending;const latest=newResult.textContent;
 assert.equal(latest,'Verified exact match: images/fixture.jpg');
 first.resolve(bytes.buffer);await firstPending;assert.equal(newResult.textContent,latest,'Earlier selection cannot replace the latest file result');
 assert.equal(digestCalls,1);
 const staleError=deferred(),errorPending=start(file(()=>staleError.promise));
 await render();const afterError=$('#verify-result');staleError.reject(Error('old read failed'));await errorPending;
 assert.equal(afterError.textContent,'','A stale read failure cannot replace new-page state or throw a null-write error');
 const slowDigest=deferred();context.crypto.subtle.digest=()=>slowDigest.promise;
 const digestPending=start(file(async()=>bytes.buffer));await flush();
 await render();const afterDigest=$('#verify-result');slowDigest.resolve(digestBytes);await digestPending;
 assert.equal(afterDigest.textContent,'','A completed digest cannot write into another route');
 const failedDigest=deferred();context.crypto.subtle.digest=()=>failedDigest.promise;
 const failPending=start(file(async()=>bytes.buffer));await flush();
 // Simulate leaving Downloads entirely: the old result is detached and no current result exists.
 for(const node of nodes.values())node.isConnected=false;nodes.clear();
 failedDigest.reject(Error('old digest failed'));await failPending;
 assert.equal(nodes.has('#verify-result'),false,'Stale errors do not re-query or recreate a missing result');
 await render();context.crypto.subtle.digest=async()=>{throw Error('digest unavailable')};
 await start(file(async()=>bytes.buffer));assert($('#verify-result').textContent.includes('Browser verification is unavailable'));
 assert.equal(context.document.activeElement,focus);
 console.log('PASS: captured verifier result, overlapping file choices, stale reads/digests/errors, latest-result accuracy and unchanged focus. DOM stubs do not verify rendering.');
})().catch(error=>{console.error(error);process.exitCode=1}).finally(()=>clearTimeout(guard));
