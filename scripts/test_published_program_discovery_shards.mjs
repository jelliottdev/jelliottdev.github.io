/* Navigation transport only: no source execution or result claims. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash,webcrypto} from 'node:crypto';
import vm from 'node:vm';
import E from '../local-experiment.js';
import J from '../finite-json.js';
import {build,checkOutputs} from './build_published_program_discovery.mjs';

const result=await build(),source=await readFile(new URL('../published-program-discovery.js',import.meta.url),'utf8');
const hash=value=>createHash('sha256').update(value).digest('hex');
function client(owners=result.owners.data){
 const scope=vm.createContext({FiniteJSON:J,PublishedProgramDiscoveryOwners:owners,crypto:webcrypto,TextEncoder,TextDecoder,AbortController,AbortSignal,Response,setTimeout,clearTimeout});
 vm.runInContext(source,scope);return scope.PublishedProgramDiscovery;
}
function host(){return {innerHTML:'',querySelector(){return null;}};}
let passed=0;
async function test(name,fn){await fn();console.log('PASS '+name);passed++;}
await test('compressed transfer length is independent of exact decoded length and SHA',async()=>{
 const D=client(),shard=result.shards[0],id=shard.data.groups[0].recordId;
 let fetched;
 const mount=D.mount(host(),{recordId:id,fetcher:async url=>{fetched=url;return new Response(shard.bytes,{headers:{'content-length':'10','content-encoding':'gzip'}});}});
 await mount.ready;assert.equal(mount.getState().phase,'ready');assert(fetched.startsWith('data/published-program-discovery/'+id+'.json?v='));mount.destroy();
});
await test('decoded hash, length, count and requested owner are independently enforced',async()=>{
 const first=result.shards[0],second=result.shards[1],id=first.data.groups[0].recordId;
 for(const change of ['hash','length','owner','count']){
  const owners=structuredClone(result.owners.data),descriptor=owners.shards[0];let bytes=first.bytes;
  if(change==='hash')bytes=bytes.replace('Setting','Sitting');
  if(change==='length')bytes+=' ';
  if(change==='owner'){bytes=second.bytes;descriptor.bytes=Buffer.byteLength(bytes);descriptor.sha256=hash(bytes);}
  if(change==='count')descriptor.count=descriptor.count===1?2:descriptor.count-1;
  const D=client(owners),mount=D.mount(host(),{recordId:id,fetcher:async()=>new Response(bytes)});await mount.ready;assert.equal(mount.getState().phase,'error',change);mount.destroy();
 }
 const D=client(),mount=D.mount(host(),{recordId:id,index:second.data});await mount.ready;assert.equal(mount.getState().phase,'error');mount.destroy();
});
await test('LRU retains at most eight owner shards and never requests the aggregate',async()=>{
 assert(result.shards.length>8);const D=client();let reads=0;
 const fetcher=async url=>{reads++;assert(!url.startsWith('data/published-program-discovery.json'));const shard=result.shards.find(s=>url.startsWith('data/published-program-discovery/'+s.data.groups[0].recordId+'.json?'));assert(shard);return new Response(shard.bytes);};
 async function visit(shard){const m=D.mount(host(),{recordId:shard.data.groups[0].recordId,fetcher});await m.ready;assert.equal(m.getState().phase,'ready');m.destroy();}
 for(const shard of result.shards.slice(0,9))await visit(shard);
 assert.equal(reads,9);await visit(result.shards[8]);assert.equal(reads,9);await visit(result.shards[0]);assert.equal(reads,10);
});
await test('decoded cache also evicts before its one MiB byte bound',async()=>{
 const owners={schema:result.owners.data.schema,recordIds:[],shards:[]},bodies=new Map();
 for(let i=0;i<6;i++){
  const recordId='large-owner-'+i,group={recordId,calculations:Array.from({length:150},(_,n)=>({reference:{recordId,caseId:'case-'+n,revision:'a'.repeat(64)},label:'Setting '+n,settings:'x'.repeat(1200)}))},bytes=E.stable({schema:result.data.schema,groups:[group]})+'\n',path='data/published-program-discovery/'+recordId+'.json';
  assert(Buffer.byteLength(bytes)<256*1024);owners.recordIds.push(recordId);owners.shards.push({recordId,path,bytes:Buffer.byteLength(bytes),sha256:hash(bytes),count:150});bodies.set(path,bytes);
 }
 const D=client(owners);let reads=0;async function visit(recordId){const m=D.mount(host(),{recordId,fetcher:async url=>{reads++;return new Response(bodies.get(url.split('?')[0]));}});await m.ready;assert.equal(m.getState().phase,'ready');m.destroy();}
 for(const id of owners.recordIds)await visit(id);assert.equal(reads,6);await visit(owners.recordIds[0]);assert.equal(reads,7);
});
await test('335 owner navigation exceeds the former aggregate limit while each owner stays bounded',async()=>{
 const original=JSON.parse(await readFile(new URL('../data/published-program-source-catalog.json',import.meta.url))).entries[0];
 const raw=new Uint8Array([1,2,3]),entries=[],records=[];
 for(let i=0;i<335;i++){const entry=structuredClone(original);entry.recordId='owner-'+i;entry.path='published-evidence/programs/fixture-'+i+'.json';entry.bytes=raw.length;entry.sha256=hash(raw);entry.steps=Array.from({length:6},()=>({op:'keyed-shift',mode:'repeat',direction:'subtract',reset:'page',key:[1,2,3,4,5,6,7]}));entries.push(entry);records.push({id:entry.recordId,status:'published'});}
 const value=await build({catalog:{schema:'liberpedia-published-program-source-index-v1',entries},registry:{schema:'liberpedia-published-program-evidence-v1',records:[],entries:[]},records,read:async()=>raw});
 assert(Buffer.byteLength(value.bytes)>256*1024);assert(value.shards.every(s=>Buffer.byteLength(s.bytes)<=256*1024));assert.equal(value.owners.data.recordIds.length,335);assert.equal(value.outputs.length,337);
 const oversized=Array.from({length:300},(_,i)=>({...structuredClone(entries[0]),caseId:'large-case-'+i}));
 await assert.rejects(build({catalog:{schema:'liberpedia-published-program-source-index-v1',entries:oversized},registry:{schema:'liberpedia-published-program-evidence-v1',records:[],entries:[]},records:[records[0]],read:async()=>raw}),/owner shard exceeds/);
});
await test('check mode checks every declared shard and fails on stale or missing bytes',async()=>{
 const stored=new Map(result.outputs.map(output=>[String(output.path),output.bytes]));
 const read=async path=>{if(!stored.has(String(path)))throw Error('Missing owner shard');return stored.get(String(path));};
 await checkOutputs(result,read);const path=String(result.shards.at(-1).path);stored.set(path,'{}');await assert.rejects(checkOutputs(result,read),/stale/);stored.delete(path);await assert.rejects(checkOutputs(result,read),/Missing owner shard/);
});
console.log(passed+' owner-sharded navigation groups passed.');
