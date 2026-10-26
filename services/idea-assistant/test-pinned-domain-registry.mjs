import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import sources from './pinned-domain-sources.mjs';
import {createPinnedDomainSourceLoader,listPinnedDomains} from './pinned-domain-registry.mjs';
import M from '../../pinned-domain-members.js';
import W from '../../pinned-warning-controls.js';
const raw=path=>readFileSync(new URL('../../'+path,import.meta.url));
const bundle=JSON.parse(raw('data/local-run-inputs.json'));
const fetcher=async url=>{const source=sources.find(s=>url==='https://jelliottdev.github.io/'+s.manifestPath);assert(source);return new Response(raw(source.manifestPath));};
let groups=0;async function test(name,fn){await fn();console.log('PASS '+name);groups++;}
await test('both authoritative complete banks bind all offline commitments and real source pages',async()=>{
 const loader=createPinnedDomainSourceLoader(fetcher),catalog=listPinnedDomains();assert.equal(catalog.length,2);
 for(const entry of catalog){assert.equal(entry.settings,2561);assert.equal(entry.pages,55);const value=await loader(entry.sourceId),parent=await M.prepare(value.domain,{bundle}),manifest=await W.read(value.manifestBytes,{sha256:value.manifestSha256,parent,template:value.template});
  for(const globalSettingIndex of [0,2560]){const member=await M.derive(parent,{globalSettingIndex,pageIds:[value.domain.pages[0].id]}),proof=await W.verify(member,manifest);assert.equal(W.inspect(proof,{member,manifest}).checkedRunes,184);}
 }
});
await test('unknown and forged identifiers cannot choose remote data or replace maintained pins',async()=>{
 let calls=0;const loader=createPinnedDomainSourceLoader(async()=>{calls++;throw Error('should not fetch');});
 for(const id of ['https://evil.example','../left',{},null,'rotating-left-nine-openings-v2'])await assert.rejects(()=>loader(id));assert.equal(calls,0);
 const catalog=listPinnedDomains();catalog[0].settings=1;assert.equal(listPinnedDomains()[0].settings,2561);
});
await test('cached bytes and returned declarations are detached and concurrent requests share one read',async()=>{
 let calls=0;const read=async url=>{calls++;return fetcher(url);},loader=createPinnedDomainSourceLoader(read),id=sources[0].sourceId;
 const [a,b]=await Promise.all([loader(id),createPinnedDomainSourceLoader(read)(id)]);assert.equal(calls,1);assert.notEqual(a.manifestBytes,b.manifestBytes);a.manifestBytes[0]=0;a.domain.pages=[];a.template.values=[];
 const c=await loader(id);assert.equal(calls,1);assert.equal(c.manifestBytes[0],123);assert.equal(c.domain.pages.length,55);assert.equal(c.template.values.length,184);
});
await test('failed fetches and changed commitments are never cached as authority',async()=>{
 let attempts=0;const source=sources[0],loader=createPinnedDomainSourceLoader(async url=>{attempts++;if(attempts===1)return new Response('',{status:503});if(attempts===2){const changed=new Uint8Array(raw(source.manifestPath));changed[50]^=1;return new Response(changed);}return fetcher(url);});
 await assert.rejects(()=>loader(source.sourceId));await assert.rejects(()=>loader(source.sourceId),/changed/);assert((await loader(source.sourceId)).manifestBytes.length>100000);assert.equal(attempts,3);
});
await test('declared and streamed oversized artifacts fail within the fixed byte bound',async()=>{
 const source=sources[0];for(const response of [()=>new Response('x',{headers:{'Content-Length':String(2*1024*1024+1)}}),()=>new Response(new Uint8Array(2*1024*1024+1))]){
  const loader=createPinnedDomainSourceLoader(async()=>response());await assert.rejects(()=>loader(source.sourceId),/bound/);
 }
});
console.log(groups+' maintained complete-domain registry groups passed; synthetic controls only, no target execution or writes.');
