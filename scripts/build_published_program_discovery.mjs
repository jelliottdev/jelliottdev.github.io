/* Navigation metadata only. Existing published sources retain all proof authority. */
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import E from '../local-experiment.js';
import Description from '../published-program-description.js';
import J from '../finite-json.js';
import Registry from '../published-opening-evidence-data.js';
import {checkedProgramIndex,validateProgramCriterion} from '../services/idea-assistant/published-program-source-index.mjs';
const ROOT=new URL('../',import.meta.url),SCHEMA='liberpedia-published-program-discovery-v1',MAX=256*1024,AGGREGATE_MAX=4*1024*1024,OWNERS_MAX=512*1024;
const sha=v=>createHash('sha256').update(typeof v==='string'||v instanceof Uint8Array?v:E.stable(v)).digest('hex'),need=(v,m)=>{if(!v)throw Error(m);};
const plain=v=>J.capture(v,{maxBytes:4*1024*1024,maxDepth:24,maxNodes:300000}),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));

export function discovery({catalog,registry=Registry,records}){
 const index=checkedProgramIndex(catalog),registered=plain(registry),owners=new Set(plain(records).filter(record=>record.status==='published').map(record=>record.id));
 need(registered.schema==='liberpedia-published-program-evidence-v1'&&Array.isArray(registered.records)&&Array.isArray(registered.entries),'Use the maintained program registry');
 const rows=index.entries.map(entry=>({recordId:entry.recordId,caseId:entry.caseId,revision:entry.revision,steps:entry.steps}));
 for(const entry of registered.entries){const record=registered.records.find(r=>r.recordId===entry.recordId&&r.revision===entry.revision),p=record?.provenance,projection=p?.projection;need(record&&sha(p)===entry.revision&&p.schema==='liberpedia-published-program-projection-v1'&&projection&&projection.taskId===entry.task.taskId&&projection.resultId===entry.run.id&&entry.caseId===projection.id+'--all-pages'&&entry.inputVersion===projection.inputVersion&&E.stable(projection.pages)===E.stable(entry.task.pages.map(p=>p.id))&&E.stable(projection.steps)===E.stable(entry.task.steps)&&E.stable(projection.criterion)===E.stable(entry.task.criterion)&&owners.has(projection.ownerRecordId),'The embedded published program association changed');E.validateTask(entry.task);validateProgramCriterion(entry.task.criterion);need(['exact-prefix','exact-prefix-set'].includes(entry.task.criterion.kind),'Count-only sources are not program navigation');rows.push({ownerRecordId:projection.ownerRecordId,recordId:entry.recordId,caseId:entry.caseId,revision:entry.revision,steps:entry.task.steps});}
 const groups=[],byOwner=new Map(),seen=new Set();
 for(const row of rows){const owner=row.ownerRecordId||row.recordId;need(owners.has(owner),'A published program has no published owner record');const reference={recordId:row.recordId,caseId:row.caseId,revision:row.revision},identity=E.stable(reference);need(!seen.has(identity),'Repeated published calculation reference');seen.add(identity);let group=byOwner.get(owner);if(!group){group={recordId:owner,calculations:[]};groups.push(group);byOwner.set(owner,group);}const first=row.steps[0],action=!first?'keep original rune order':first.direction?first.direction+' key values':first?.op==='reverse'?'reverse rune order':first?.op==='affine'?'replace rune indices':'transform rune indices',label='Setting '+(group.calculations.length+1)+' — '+action,settings=Description.program(row.steps);need(label.length<=160&&settings.length<=1200,'Published setting description exceeds its navigation bound');group.calculations.push({reference,label,settings});}
 need(groups.length<=1024&&groups.every(group=>group.calculations.length<=1024),'Published navigation exceeds its owner or per-owner entry bound');const value={schema:SCHEMA,groups};need(Buffer.byteLength(E.stable(value))<=AGGREGATE_MAX,'Build-only published navigation listing exceeds its byte bound');return value;
}
export async function build({root=ROOT,catalog,registry=Registry,records,read=readFile}={}){
 catalog??=JSON.parse(await read(new URL('data/published-program-source-catalog.json',root)));records??=JSON.parse(await read(new URL('data/experiment-index.json',root))).records;
 const value=discovery({catalog,registry,records}),seen=new Set();for(const entry of checkedProgramIndex(catalog).entries){if(seen.has(entry.path))continue;seen.add(entry.path);const bytes=await read(new URL(entry.path,root));need(bytes.byteLength===entry.bytes&&sha(bytes)===entry.sha256,'Published program source bytes changed: '+entry.path);}
 const shards=value.groups.map(group=>{const data={schema:SCHEMA,groups:[group]},bytes=E.stable(data)+'\n';need(Buffer.byteLength(bytes)<=MAX,'Published owner shard exceeds its byte bound: '+group.recordId);return {path:new URL('data/published-program-discovery/'+group.recordId+'.json',root),bytes,data};});
 const owners={schema:'liberpedia-published-program-discovery-owners-v2',recordIds:value.groups.map(g=>g.recordId),shards:shards.map(shard=>({recordId:shard.data.groups[0].recordId,path:'data/published-program-discovery/'+shard.data.groups[0].recordId+'.json',bytes:Buffer.byteLength(shard.bytes),sha256:sha(shard.bytes),count:shard.data.groups[0].calculations.length}))};
 need(Buffer.byteLength(E.stable(owners))<=OWNERS_MAX,'Published owner manifest exceeds its byte bound');
 const ownersBytes="/* Generated pinned owner shards only; no execution or evidence authority. */\n(function(root){'use strict';const data="+E.stable(owners)+";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedProgramDiscoveryOwners=data;})(typeof globalThis==='object'?globalThis:this);\n";
 // The complete v1 listing remains a bounded build/export artifact. Browsers
 // fetch only the pinned single-owner shards, never this aggregate payload.
 const aggregate={path:new URL('data/published-program-discovery.json',root),bytes:E.stable(value)+'\n',data:value},ownerOutput={path:new URL('published-program-discovery-owners.js',root),bytes:ownersBytes,data:owners};
 return {...aggregate,owners:ownerOutput,shards,outputs:[aggregate,ownerOutput,...shards]};
}
export async function checkOutputs(result,read=readFile){
 for(const output of result.outputs)need((await read(output.path,'utf8'))===output.bytes,'Published program discovery output is stale: '+output.path);
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags=process.argv.slice(2);need(flags.length<=1&&flags.every(x=>['--write','--check'].includes(x)),'Use --write or --check');const result=await build();if(flags.includes('--write'))for(const output of result.outputs){await mkdir(dirname(fileURLToPath(output.path)),{recursive:true});await writeFile(output.path,output.bytes);}else await checkOutputs(result);console.log('PASS '+result.data.groups.reduce((n,g)=>n+g.calculations.length,0)+' exact published calculation links across '+result.data.groups.length+' records; navigation only');
}
