/* Navigation metadata only. Existing published sources retain all proof authority. */
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import E from '../local-experiment.js';
import Description from '../published-program-description.js';
import J from '../finite-json.js';
import Registry from '../published-opening-evidence-data.js';
import {checkedProgramIndex,validateProgramCriterion} from '../services/idea-assistant/published-program-source-index.mjs';
const ROOT=new URL('../',import.meta.url),SCHEMA='liberpedia-published-program-discovery-v1',MAX=256*1024;
const sha=v=>createHash('sha256').update(typeof v==='string'||v instanceof Uint8Array?v:E.stable(v)).digest('hex'),need=(v,m)=>{if(!v)throw Error(m);};
const plain=v=>J.capture(v,{maxBytes:4*1024*1024,maxDepth:24,maxNodes:300000}),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));

export function discovery({catalog,registry=Registry,records}){
 const index=checkedProgramIndex(catalog),registered=plain(registry),owners=new Set(plain(records).filter(record=>record.status==='published').map(record=>record.id));
 need(registered.schema==='liberpedia-published-program-evidence-v1'&&Array.isArray(registered.records)&&Array.isArray(registered.entries),'Use the maintained program registry');
 const rows=index.entries.map(entry=>({recordId:entry.recordId,caseId:entry.caseId,revision:entry.revision,steps:entry.steps}));
 for(const entry of registered.entries){const record=registered.records.find(r=>r.recordId===entry.recordId&&r.revision===entry.revision),p=record?.provenance,projection=p?.projection;need(record&&sha(p)===entry.revision&&p.schema==='liberpedia-published-program-projection-v1'&&projection&&projection.taskId===entry.task.taskId&&projection.resultId===entry.run.id&&entry.caseId===projection.id+'--all-pages'&&entry.inputVersion===projection.inputVersion&&E.stable(projection.pages)===E.stable(entry.task.pages.map(p=>p.id))&&E.stable(projection.steps)===E.stable(entry.task.steps)&&E.stable(projection.criterion)===E.stable(entry.task.criterion)&&owners.has(projection.ownerRecordId),'The embedded published program association changed');E.validateTask(entry.task);validateProgramCriterion(entry.task.criterion);need(['exact-prefix','exact-prefix-set'].includes(entry.task.criterion.kind),'Count-only sources are not program navigation');rows.push({ownerRecordId:projection.ownerRecordId,recordId:entry.recordId,caseId:entry.caseId,revision:entry.revision,steps:entry.task.steps});}
 const groups=[],byOwner=new Map(),seen=new Set();
 for(const row of rows){const owner=row.ownerRecordId||row.recordId;need(owners.has(owner),'A published program has no published owner record');const reference={recordId:row.recordId,caseId:row.caseId,revision:row.revision},identity=E.stable(reference);need(!seen.has(identity),'Repeated published calculation reference');seen.add(identity);let group=byOwner.get(owner);if(!group){group={recordId:owner,calculations:[]};groups.push(group);byOwner.set(owner,group);}const first=row.steps[0],action=!first?'keep original rune order':first.direction?first.direction+' key values':first?.op==='reverse'?'reverse rune order':first?.op==='affine'?'replace rune indices':'transform rune indices',label='Setting '+(group.calculations.length+1)+' — '+action,settings=Description.program(row.steps);need(label.length<=160&&settings.length<=1200,'Published setting description exceeds its navigation bound');group.calculations.push({reference,label,settings});}
 need(groups.length<=100&&seen.size<=1024,'Published navigation exceeds its group or entry bound');const value={schema:SCHEMA,groups};need(Buffer.byteLength(E.stable(value))<=MAX,'Published navigation exceeds its byte bound');return value;
}
export async function build({root=ROOT,catalog,registry=Registry,records,read=readFile}={}){
 catalog??=JSON.parse(await read(new URL('data/published-program-source-catalog.json',root)));records??=JSON.parse(await read(new URL('data/experiment-index.json',root))).records;
 const value=discovery({catalog,registry,records}),seen=new Set();for(const entry of checkedProgramIndex(catalog).entries){if(seen.has(entry.path))continue;seen.add(entry.path);const bytes=await read(new URL(entry.path,root));need(bytes.byteLength===entry.bytes&&sha(bytes)===entry.sha256,'Published program source bytes changed: '+entry.path);}
 const owners={schema:'liberpedia-published-program-discovery-owners-v1',recordIds:value.groups.map(g=>g.recordId)},ownersBytes="/* Generated discovery owners only; no execution or evidence authority. */\n(function(root){'use strict';const data="+E.stable(owners)+";Object.freeze(data.recordIds);Object.freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedProgramDiscoveryOwners=data;})(typeof globalThis==='object'?globalThis:this);\n";
 return {path:new URL('data/published-program-discovery.json',root),bytes:E.stable(value)+'\n',data:value,owners:{path:new URL('published-program-discovery-owners.js',root),bytes:ownersBytes,data:owners}};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags=process.argv.slice(2);need(flags.length<=1&&flags.every(x=>['--write','--check'].includes(x)),'Use --write or --check');const result=await build();for(const output of [result,result.owners])if(flags.includes('--write'))await writeFile(output.path,output.bytes);else need((await readFile(output.path,'utf8'))===output.bytes,'Published program discovery output is stale: '+output.path);console.log('PASS '+result.data.groups.reduce((n,g)=>n+g.calculations.length,0)+' exact published calculation links across '+result.data.groups.length+' records; navigation only');
}
