'use strict';
/* Exact cross-language archived-array hydration; no manuscript program is executed. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{execFileSync}=require('node:child_process'),{createHash,webcrypto}=require('node:crypto'),E=require('../local-experiment.js'),J=require('../finite-json.js'),Codec=require('../published-numeric-bank-source.js');
const sha=b=>createHash('sha256').update(b).digest('hex'),copy=structuredClone,bytes=m=>Buffer.from(E.stable(m)+'\n');
const python=String.raw`import sys,json,hashlib
sys.stdout.reconfigure(encoding='utf8')
sys.path.insert(0,'scripts')
import published_numeric_bank_projection as p
import numeric_bank_followups as n
bundles=[]
for rid in n.FAMILIES:
 v=p.prepare(rid)
 manifest=v.manifest()
 view=type('ReceiptView',(),{'manifest':lambda self:manifest})()
 expected=[]
 for program in manifest['payload']['programs']:
  r=p.Projection.receipt(view,program['id']);raw=(p.stable(r)+'\n').encode('utf8');e=r['entries'][0]
  expected.append({'programId':program['id'],'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'taskId':e['task']['taskId'],'resultId':e['run']['id'],'revision':e['revision']})
 bundles.append({'manifest':manifest,'sha256':hashlib.sha256(v.bytes()).hexdigest(),'bytes':len(v.bytes()),'expected':expected})
print(json.dumps(bundles,ensure_ascii=False,separators=(',',':')))`;
const fixtures=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',python],{cwd:require('node:path').resolve(__dirname,'..'),encoding:'utf8',maxBuffer:20*1024*1024}));
(async()=>{let groups=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
const handles=[];const run=E.run,verify=E.verify;E.run=E.verify=()=>assert.fail('Hydration cannot execute or claim replay of a target');
try{
await test('all232 hydrated manifests equal Python receipt bytes identities and dates with zero target runs',async()=>{let programs=0;for(const f of fixtures){const raw=bytes(f.manifest);assert.equal(raw.length,f.bytes);assert.equal(sha(raw),f.sha256);const h=await Codec.prepare(raw,{sha256:f.sha256,crypto:webcrypto});handles.push(h);assert.equal(Codec.inspect(h).programIds.length,58);assert.equal(Codec.inspect(h).recordId,f.manifest.payload.recordId);for(const expected of f.expected){const out=await Codec.hydrate(h,expected.programId),actual=bytes(out);assert.equal(actual.length,expected.bytes);assert.equal(sha(actual),expected.sha256);assert.equal(out.entries[0].task.taskId,expected.taskId);assert.equal(out.entries[0].run.id,expected.resultId);assert.equal(out.entries[0].revision,expected.revision);assert.equal(out.entries[0].run.createdAt,'2026-10-26T00:00:00.000Z');assert(Object.isFrozen(out.entries[0].run.result.transformed));programs++;}assert(!Object.hasOwn(h,'payload'));assert.throws(()=>Codec.inspect({...h}));}assert.equal(programs,232);});
await test('object and byte snapshots remain immutable across asynchronous caller edits',async()=>{const f=fixtures[0],original=copy(f.manifest),raw=bytes(original),pending=Codec.prepare(original,{sha256:f.sha256,crypto:webcrypto});original.payload.programs[0].outputRefs[0]=-1;original.payload.outputs[0].values[0]=99;const h=await pending;assert.equal(sha(bytes(await Codec.hydrate(h,f.expected[0].programId))),f.expected[0].sha256);const fromBytes=Codec.prepare(raw,{sha256:f.sha256,crypto:webcrypto});raw.fill(0);assert.equal(sha(bytes(await Codec.hydrate(await fromBytes,f.expected[0].programId))),f.expected[0].sha256);await assert.rejects(()=>Codec.hydrate(h,f.expected[0].programId,{sha256:'0'.repeat(64)}),/another pinned bundle/);await assert.rejects(()=>Codec.hydrate(h,'unknown-program'),/absent/);});
await test('rehashed malformed families schemas criteria banks rows refs and empty provenance fail closed',async()=>{const source=fixtures[0].manifest,mutations=[
 m=>m.schema='unknown',m=>m.payload.recordId='unknown-family',m=>m.payload.recordId='lp2-prime-openings',m=>m.payload.bank.id='prime-v1',m=>m.payload.bank.sha256='0'.repeat(64),m=>m.payload.bank.values[0]=29,
 m=>m.payload.criterion.openings.reverse(),m=>m.payload.criterion={kind:'exact-prefix',values:[0]},m=>m.payload.sourcePins[0].sha256='0'.repeat(64),m=>m.payload.sourcePins[1]=copy(m.payload.sourcePins[0]),m=>m.payload.sourcePins[0].path='../plan.json',
 m=>m.payload.pages.reverse(),m=>m.payload.pages.pop(),m=>m.payload.programs.pop(),m=>m.payload.programs.reverse(),m=>m.payload.programs[1].id=m.payload.programs[0].id,m=>m.payload.programs[0].offset=1,m=>m.payload.programs[0].direction='guess',
 m=>m.payload.programs[0].outputRefs[0]=m.payload.programs[0].outputRefs[1],m=>m.payload.programs[0].outputRefs[0]=-1,m=>m.payload.programs[0].outputRefs[0]=true,m=>m.payload.programs[0].outputRefs.pop(),
 m=>m.payload.outputs[0].values[0]=true,m=>m.payload.outputs[0].values[0]=(m.payload.outputs[0].values[0]+1)%29,m=>m.payload.outputs[0].matchingOpenings=['warning'],m=>m.payload.outputs.find(r=>r.page==='lp2-50').origin='archived',m=>m.payload.outputs[0].origin='structural-empty-input',m=>m.payload.outputs.push(copy(m.payload.outputs[0])),
 m=>m.payload.audit.historicalComparisons=1,m=>m.payload.checkedAt='2020-01-01T00:00:00.000Z',m=>m.payload.dateMeaning='Historical browser execution',m=>m.payload.extra=true];
 // These rehashed malformed bundles exercise the actual byte transport. Object
 // snapshot/accessor/sparse-array safety remains independently covered below.
 // Avoid recapturing ~750k output indices in every malformed-input fixture.
 for(let i=0;i<mutations.length;i++){const bad=copy(source);mutations[i](bad);bad.sha256=sha(Buffer.from(E.stable(bad.payload)));const raw=bytes(bad);await assert.rejects(()=>Codec.prepare(raw,{sha256:sha(raw),crypto:webcrypto}),'Mutation '+i+' must fail');}
 const badDigest=copy(source);badDigest.sha256='0'.repeat(64);await assert.rejects(()=>Codec.prepare(badDigest,{sha256:sha(bytes(badDigest)),crypto:webcrypto}),/payload digest/);await assert.rejects(()=>Codec.prepare(source,{sha256:'0'.repeat(64),crypto:webcrypto}),/pinned numeric bundle/);
});
await test('bounded plain inputs reject accessors hooks sparse arrays and oversized bytes before authority',async()=>{const f=fixtures[0];let invoked=0;const hostile={};Object.defineProperty(hostile,'schema',{enumerable:true,get(){invoked++;return Codec.SCHEMA;}});await assert.rejects(()=>Codec.prepare(hostile,{sha256:f.sha256,crypto:webcrypto}));assert.equal(invoked,0);const option={sha256:f.sha256};Object.defineProperty(option,'crypto',{enumerable:true,get(){invoked++;return webcrypto;}});await assert.rejects(()=>Codec.prepare(f.manifest,option));assert.equal(invoked,0);const sparse=copy(f.manifest);delete sparse.payload.outputs[0].values[0];await assert.rejects(()=>Codec.prepare(sparse,{sha256:f.sha256,crypto:webcrypto}));await assert.rejects(()=>Codec.prepare(new Uint8Array(Codec.LIMITS.bytes+1),{sha256:f.sha256,crypto:webcrypto}),/bounded UTF-8/);await assert.rejects(()=>Codec.prepare(new Uint8Array([255]),{sha256:sha(Buffer.from([255])),crypto:webcrypto}),/UTF-8 JSON/);await assert.rejects(()=>Codec.prepare(new Uint16Array([1,2]),{sha256:f.sha256,crypto:webcrypto}),/bounded UTF-8/);});
await test('browser UMD hydrates the same exact receipt with explicitly provided crypto',async()=>{const context=vm.createContext({LocalExperiment:E,FiniteJSON:J,TextEncoder,TextDecoder,Uint8Array,ArrayBuffer});vm.runInContext(fs.readFileSync(require('node:path').resolve(__dirname,'../published-numeric-bank-source.js'),'utf8'),context);const f=fixtures[2],h=await context.PublishedNumericBankSource.prepare(bytes(f.manifest),{sha256:f.sha256,crypto:webcrypto}),out=await context.PublishedNumericBankSource.hydrate(h,f.expected[0].programId);assert.equal(sha(bytes(out)),f.expected[0].sha256);});
}finally{E.run=run;E.verify=verify;}
console.log(groups+' strict numeric compact-source groups passed;232 exact manifests, no target execution.');})().catch(e=>{console.error(e);process.exitCode=1;});
