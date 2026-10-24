/* Strict aggregate and cancellation tests. All responses are local fixtures. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseInputBundle,loadInputBundle} from './official-inputs.mjs';
const ids=[...Array.from({length:17},(_,i)=>'lp1-'+String(i).padStart(2,'0')),...Array.from({length:58},(_,i)=>'lp2-'+String(i).padStart(2,'0'))];
const alphabet=JSON.parse(readFileSync(new URL('../../data/index.json',import.meta.url),'utf8')).alphabet.map(({rune,latin,prime})=>({rune,latin,prime}));
const make=()=>({schema:'liberpedia-local-inputs-v1',alphabet:structuredClone(alphabet),pages:ids.map((id,i)=>({id,raw:'ᚠ-ᚢ  \r\n\t'+i,reviewed_text:i===0?null:i===1?'':'ᚢ\r\nᚠ '+i}))});
const url='https://jelliottdev.github.io/data/local-run-inputs.json';
async function read(response,max){
 assert.equal(max,2*1024*1024);if(!/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''))throw Error('JSON required');
 const declared=response.headers.get('content-length');if(declared!==null&&Number(declared)>max)throw Error('Body too large');
 const reader=response.body.getReader(),chunks=[];let size=0;while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('Body too large');}chunks.push(value);}const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
let count=0;async function test(name,fn){await fn();console.log('PASS '+name);count++;}
await test('strict projection preserves all75 exact raw/reviewed/empty/null values without mutation',()=>{
 const value=make(),before=structuredClone(value),result=parseInputBundle(value);assert.deepEqual(value,before);assert.deepEqual(result.alphabet,alphabet);assert.equal(result.pages.size,75);assert.deepEqual([...result.pages.keys()],ids);for(const p of value.pages)assert.deepEqual(result.pages.get(p.id),p);assert.equal(result.pages.get(ids[0]).reviewed_text,null);assert.equal(result.pages.get(ids[1]).reviewed_text,'');assert.equal(result.pages.get(ids[2]).raw,'ᚠ-ᚢ  \r\n\t2');
});
await test('malformed schemas, duplicate/missing IDs, absent reviewed values and extra fields are rejected',()=>{
 const edits=[v=>v.schema='other',v=>v.extra=1,v=>v.pages.pop(),v=>v.pages[1]=v.pages[0],v=>v.pages[0].id='lp2-58',v=>delete v.pages[0].reviewed_text,v=>v.pages[0].raw=null,v=>v.pages[0].reviewed_text=false,v=>v.pages[0].extra=1,v=>v.alphabet.pop(),v=>v.alphabet[1]=v.alphabet[0],v=>v.alphabet[0].prime=true,v=>v.alphabet[0].extra=1];
 for(const edit of edits){const value=make();edit(value);assert.throws(()=>parseInputBundle(value));}
});
await test('one fixed manual-redirect request; no per-page or arbitrary fallback',async()=>{
 let calls=0;const controller=new AbortController();const result=await loadInputBundle({signal:controller.signal,read,fetcher:async(actual,options)=>{calls++;assert.equal(actual,url);assert.equal(options.redirect,'manual');assert.equal(options.signal,controller.signal);return Response.json(make());}});assert.equal(calls,1);assert.equal(result.pages.size,75);
 for(const status of [302,404,503]){let requests=0,reads=0;await assert.rejects(loadInputBundle({read:async()=>{reads++;return make();},fetcher:async actual=>{requests++;assert.equal(actual,url);return new Response(null,{status,headers:{location:'https://evil.example/inputs'}});}}));assert.equal(requests,1);assert.equal(reads,0);}
});
await test('reader bound is2MiB; oversized declared/streamed source and nonJSON never accepted',async()=>{
 const responses=[()=>new Response('{}',{headers:{'content-type':'application/json','content-length':String(2*1024*1024+1)}}),()=>new Response(' '.repeat(2*1024*1024+1),{headers:{'content-type':'application/json'}}),()=>new Response(JSON.stringify(make()),{headers:{'content-type':'text/html'}})];
 for(const response of responses)await assert.rejects(loadInputBundle({read,fetcher:async()=>response()}));
});
await test('preabort makes zero requests; ignored fetch/read cancellation still releases awaiting caller',async()=>{
 const already=new AbortController();already.abort();let calls=0;await assert.rejects(loadInputBundle({signal:already.signal,read,fetcher:async()=>{calls++;return Response.json(make());}}),/cancelled/);assert.equal(calls,0);
 for(const stage of ['fetch','read']){
  const controller=new AbortController();let reached=false;
  const pending=loadInputBundle({signal:controller.signal,fetcher:async()=>{if(stage==='fetch'){reached=true;return new Promise(()=>{});}return Response.json(make());},read:async()=>{reached=true;return new Promise(()=>{});}});
  await new Promise(resolve=>setImmediate(resolve));assert(reached);controller.abort();
  await assert.rejects(Promise.race([pending,new Promise((_,reject)=>{const timer=setTimeout(()=>reject(Error('Cancellation did not settle')),100);timer.unref();})]),/cancelled/);
 }
});
console.log('PASS '+count+' official-input groups; no network or target computation.');
