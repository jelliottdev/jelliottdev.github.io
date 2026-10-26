/* Read-only, authenticated discovery over one immutable factored question.
 * Receipt computations are replayed by the client, never executed here. */
import E from '../../local-experiment.js';
import Json from '../../finite-json.js';
import {readAdmittedResult} from './admitted-result.mjs';
import Q from '../../factored-finite-question.js';
import Evidence from '../../computation-evidence.js';
import Counts from '../../published-count-evidence-data.js';
import Programs from '../../published-opening-evidence-data.js';
import RetainedHistory from '../../published-evidence-history-data.js';
import {readPublishedEvidence,publishedProgramIndex} from './published-evidence.mjs';
import {validateFamilyReceipt} from './family-evidence.mjs';
import {chooseLocalMetadataQuery,LIMITS as QUERY_LIMITS} from './factored-query-strategy.mjs';
const LIMITS=Object.freeze({sources:12,metadata:256,localRowids:2048,lookupValueBytes:1900000,bytes:8*1024*1024,cursorBytes:32768,ttlMs:48*60*60*1000});
const retainedPages=new WeakMap(),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
const enc=new TextEncoder(),HEX=/^[a-f0-9]{64}$/,fields=['schema','proposalId','domainId','inputVersion','queryHash','registryHash','scanId','issuedAt','sequence','previous','water','stage','after','served'];
// Internal performance budget only; this supplies no source or domain authority.
export function fitsLookupBudget(scopeIndex,servedJSON){
 if(typeof scopeIndex!=='string'||typeof servedJSON!=='string')return false;
 const scopeBytes=enc.encode(scopeIndex).length,servedBytes=enc.encode(servedJSON).length;
 return scopeBytes<=LIMITS.lookupValueBytes&&servedBytes<=LIMITS.lookupValueBytes&&2*scopeBytes+servedBytes<=LIMITS.bytes;
}
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const b64=v=>btoa(String.fromCharCode(...v)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');
function un64(v){if(typeof v!=='string'||!v.length||!/^[a-zA-Z0-9_-]+$/.test(v))throw Error('Invalid base64 cursor.');return Uint8Array.from(atob(v.replaceAll('-','+').replaceAll('_','/')),c=>c.charCodeAt(0));}
function fail(code,message){const e=new Error(message);e.code=code;e.status=code==='stale-scan'?409:code==='source-too-large'?413:code==='invalid-cursor'?400:503;return e;}
const size=v=>enc.encode(E.stable(v)).length;
async function hashText(v,c){return [...new Uint8Array(await c.subtle.digest('SHA-256',enc.encode(v)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function hash(v,c){return [...new Uint8Array(await c.subtle.digest('SHA-256',enc.encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function keyFor(value,c){const bytes=typeof value==='string'?enc.encode(value):value;if(!(bytes instanceof Uint8Array)||bytes.length<32||bytes.length>1024)throw fail('unavailable','A dedicated evidence cursor key is required.');return c.subtle.importKey('raw',bytes,{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
async function seal(value,key,c){const body=enc.encode(E.stable(value));return b64(body)+'.'+b64(new Uint8Array(await c.subtle.sign('HMAC',key,body)));}
async function open(token,key,c,expected=fields){try{if(typeof token!=='string'||token.length>LIMITS.cursorBytes)throw Error();const bits=token.split('.');if(bits.length!==2)throw Error();const body=un64(bits[0]),signature=un64(bits[1]);if(signature.length!==32||!await c.subtle.verify('HMAC',key,signature,body))throw Error();const raw=new TextDecoder('utf-8',{fatal:true}).decode(body),value=JSON.parse(raw);if(E.stable(value)!==raw||!exact(value,expected))throw Error();return value;}catch{throw fail('invalid-cursor','The evidence cursor could not be authenticated.');}}
// Server-only provenance seam. No fields are added to the public page/schema.
// Fingerprints capture all original source bytes before returning the page;
// copied pages, changed source arrays and getters cannot acquire this authority.
export async function inspectRetainedOrigins(page){
 const proof=retainedPages.get(page);if(!proof)throw fail('unavailable','Use an original source-context evidence page.');
 const descriptor=Object.getOwnPropertyDescriptor(page,'sources');if(!descriptor?.enumerable||!Object.hasOwn(descriptor,'value'))throw fail('unavailable','The retained source array changed.');
 const sources=Json.capture(descriptor.value,{maxBytes:LIMITS.bytes,maxDepth:32,maxNodes:500000});
 if(!Array.isArray(sources)||sources.length!==proof.entries.length)throw fail('unavailable','The retained source count changed.');
 for(let i=0;i<sources.length;i++)if(await hash(sources[i],proof.crypto)!==proof.entries[i].sourceSha256)throw fail('unavailable','Original retained source bytes changed.');
 return freeze(proof.entries.map(entry=>Json.capture(entry.origin,{maxBytes:4096,maxDepth:4,maxNodes:32})));
}
function retainedOrigin(source,location){
 const extra=location?.kind==='local'?[]:location?.kind==='family'?['familyId','revision','caseId']:location?.kind==='published'?['recordId','revision','caseId']:null;
 if(!extra||!exact(location,['kind',...extra]))throw fail('unavailable','Retained archive provenance is unavailable.');
 return freeze(Json.capture({...location,taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt},{maxBytes:4096,maxDepth:4,maxNodes:32}));
}
const tables=['local_tasks','local_task_results','local_task_ideas','research_ideas','family_case_results'];
async function boundary(db){let row;try{row=await db.prepare('SELECT epoch,'+tables.map((t,i)=>'(SELECT COALESCE(MAX(rowid),0) FROM '+t+') AS h'+i).join(',')+' FROM finite_evidence_epoch WHERE id=1').bind().first();}catch{throw fail('unavailable','The evidence snapshot fence is unavailable.');}if(!row||!Number.isSafeInteger(row.epoch)||row.epoch<0||tables.some((_,i)=>!Number.isSafeInteger(row['h'+i])||row['h'+i]<0))throw fail('unavailable','The evidence snapshot fence is unavailable.');return row;}
// Internal composition seam. Public handlers never accept a caller fence.
// A multi-domain coordinator must authenticate its original fence before reuse.
export async function readEvidenceFence(db){return Object.freeze({...await boundary(db)});}
async function checkedFence(db,input){
 let value;try{value=Json.capture(input,{maxBytes:1024,maxDepth:3,maxNodes:16});}catch{throw fail('invalid-cursor','The evidence snapshot fence is invalid.');}
 if(!exact(value,['epoch','h0','h1','h2','h3','h4'])||Object.values(value).some(v=>!Number.isSafeInteger(v)||v<0))throw fail('invalid-cursor','The evidence snapshot fence is invalid.');
 const current=await boundary(db);if(value.epoch!==current.epoch||tables.some((_,i)=>value['h'+i]>current['h'+i]))throw fail('stale-scan','The original evidence snapshot is unavailable.');return value;
}
async function epoch(db,water){let row;try{row=await db.prepare('SELECT epoch FROM finite_evidence_epoch WHERE id=1').bind().first();}catch{throw fail('unavailable','The evidence snapshot fence is unavailable.');}if(!row||row.epoch!==water.epoch)throw fail('stale-scan','Saved evidence changed during this scan. Start a fresh lookup.');}
function positions(source,d,programs,pages){const index=programs.get(E.stable(source.task.steps));if(index===undefined||source.inputVersion!==d.inputVersion)return [];return source.task.pages.flatMap(p=>{const target=pages.get(p.id);return target&&target.text===p.text?[index*d.pages.length+target.index]:[];});}
function bitmap(value,count){const bytes=un64(value);if(bytes.length!==Math.ceil(count/8)||count%8&&bytes.at(-1)>>(count%8))throw fail('invalid-cursor','The evidence cursor bitmap changed.');return bytes;}
const marked=(bits,n)=>!!(bits[n>>3]&(1<<(n%8)));
const mark=(bits,n)=>{bits[n>>3]|=1<<(n%8);};
export {LIMITS};
export const STRICT_POLICY=Object.freeze({mode:'strict',page:'liberpedia-factored-evidence-page-v1',cursor:'liberpedia-factored-evidence-cursor-v1',snapshot:'liberpedia-factored-evidence-snapshot-v1'});
export const PREFIX_POLICY=Object.freeze({mode:'verified-output-prefix-v1',page:'liberpedia-factored-prefix-evidence-page-v1',cursor:'liberpedia-factored-prefix-evidence-cursor-v1',snapshot:'liberpedia-factored-prefix-evidence-snapshot-v1'});
export const OUTPUT_POLICY=Object.freeze({mode:'language-reference-comparison-v1',page:'liberpedia-factored-output-evidence-page-v1',cursor:'liberpedia-factored-output-evidence-cursor-v1',snapshot:'liberpedia-factored-output-evidence-snapshot-v1'});
export const INSPECTION_POLICY=Object.freeze({mode:'transformed-output-inspection-v1',page:'liberpedia-factored-inspection-evidence-page-v1',cursor:'liberpedia-factored-inspection-evidence-cursor-v1',snapshot:'liberpedia-factored-inspection-evidence-snapshot-v1'});
const fullOutputPolicy=policy=>policy===OUTPUT_POLICY||policy===INSPECTION_POLICY;
function checkedPolicy(policy){if(policy!==STRICT_POLICY&&policy!==PREFIX_POLICY&&policy!==OUTPUT_POLICY&&policy!==INSPECTION_POLICY)throw fail('unavailable','Use a maintained evidence policy.');return policy;}
const outputSourceKinds=Object.freeze(['measurement','exact-prefix','exact-prefix-set','word-affine-count','word-prime-sums','language-score']);
const criterionMatches=(criterion,target,policy)=>policy===STRICT_POLICY?E.stable(criterion)===E.stable(target):(fullOutputPolicy(policy)?outputSourceKinds:['measurement','exact-prefix']).includes(criterion?.kind);
const queryDefinition=(d,inputVersion,policy,includeSourceContext=false)=>({... (includeSourceContext?{sourceContext:'verified-original-source-v1'}:{}),publishedSelection:'exact-settings-and-page-pins-v1',...((policy===PREFIX_POLICY)?{evidenceMode:policy.mode,sourceCriteria:['measurement','exact-prefix']}:fullOutputPolicy(policy)?{questionPolicy:policy.mode,sourceCriteria:outputSourceKinds}:{}),engine:d.engine,inputVersion,alphabet:d.alphabet,programs:d.programs,pages:d.pages,criterion:d.criterion});

async function registryMetadata(programIndex){const index=await publishedProgramIndex({programIndex});return [...[...Counts.entries,...Programs.entries].map(v=>({recordId:v.recordId,revision:v.revision,caseId:v.caseId,inputVersion:v.inputVersion,task:v.task})),...(index?.entries||[]).map(item=>({...item,indexed:true}))].sort((a,b)=>E.stable([a.recordId,a.revision,a.caseId]).localeCompare(E.stable([b.recordId,b.revision,b.caseId])));}
// Durable archive generations bind current and retained published authorities.
// This is deliberately broader than a discovery page's current metadata hash.
export async function readEvidenceRegistryHash({programIndex,crypto:c=globalThis.crypto}={}){
 const index=await publishedProgramIndex({programIndex});return hash({index,registries:[Counts,Programs],history:RetainedHistory},c);
}
export async function readEvidencePage(policy,{db,proposalId,domain,inputVersion,cursor=null,cursorKey,now=Date.now(),crypto:c=globalThis.crypto,programIndex,fetcher=globalThis.fetch,signal,includeSourceContext=false,snapshotFence,responseReserveBytes=0}){
 checkedPolicy(policy);if(!Number.isSafeInteger(responseReserveBytes)||responseReserveBytes<0||responseReserveBytes>1024*1024)throw fail('unavailable','Use a bounded internal response reserve.');if(typeof includeSourceContext!=='boolean')throw fail('unavailable','Use an explicit source-context mode.');const d=Q.inspect(domain);if(policy===INSPECTION_POLICY&&(d.schema!=='liberpedia-factored-finite-output-question-v1'||d.questionPolicy!==policy.mode||d.criterion.kind!=='measurement'))throw fail('unavailable','Use the maintained transformed-output inspection.');if(policy===OUTPUT_POLICY&&(d.schema!=='liberpedia-factored-finite-output-question-v1'||d.questionPolicy!==policy.mode))throw fail('unavailable','Use the maintained pinned language comparison.');if(policy===STRICT_POLICY&&d.schema!=='liberpedia-factored-finite-question-v2')throw fail('unavailable','Use a maintained prefix question.');if(policy===PREFIX_POLICY&&d.criterion.kind!=='exact-prefix')throw fail('unavailable','Derived prefix discovery requires an exact-prefix question.');if(!/^p_[a-f0-9]{64}$/.test(proposalId)||inputVersion!==d.inputVersion||!Number.isSafeInteger(now)||typeof db?.prepare!=='function')throw fail('unavailable','A bound original question and evidence store are required.');
 const key=await keyFor(cursorKey,c),registrySnapshot=await registryMetadata(programIndex),registryHash=await hash(registrySnapshot,c),queryHash=await hash(queryDefinition(d,inputVersion,policy,includeSourceContext),c);
 const fixedFence=snapshotFence===undefined?null:await checkedFence(db,snapshotFence);
 let state=cursor===null?{schema:policy.cursor,proposalId,domainId:d.id,inputVersion,queryHash,registryHash,scanId:b64(c.getRandomValues(new Uint8Array(18))),issuedAt:now,sequence:0,previous:null,water:fixedFence||await boundary(db),stage:0,after:0,served:b64(new Uint8Array(Math.ceil(d.totalCases/8)))}:await open(cursor,key,c);
 if(fixedFence&&E.stable(state.water)!==E.stable(fixedFence))throw fail('stale-scan','This continuation belongs to a different evidence snapshot.');
 if(state.schema!==policy.cursor||state.proposalId!==proposalId||state.domainId!==d.id||state.inputVersion!==inputVersion||state.queryHash!==queryHash||state.registryHash!==registryHash)throw fail('stale-scan','This cursor belongs to another question or published source snapshot.');
 if(!Number.isSafeInteger(state.issuedAt)||state.issuedAt>now||now-state.issuedAt>LIMITS.ttlMs||!Number.isSafeInteger(state.sequence)||state.sequence<0||state.sequence>1000000||![0,1,2,3].includes(state.stage)||!Number.isSafeInteger(state.after)||state.after<0||typeof state.scanId!=='string'||!/^[a-zA-Z0-9_-]{24}$/.test(state.scanId)||state.previous!==null&&!HEX.test(state.previous)||!exact(state.water,['epoch','h0','h1','h2','h3','h4'])||Object.values(state.water).some(v=>!Number.isSafeInteger(v)||v<0))throw fail('invalid-cursor','The evidence cursor is invalid or expired.');
 await epoch(db,state.water);
 const served=bitmap(state.served,d.totalCases),programs=new Map(d.programs.map((p,i)=>[E.stable(p.steps),i])),pages=new Map(d.pages.map((p,i)=>[p.id,{text:p.text,index:i}])),stepJSON=E.stable(d.programs.map(p=>E.stable(p.steps))),scope=E.stable(d.pages),alphabet=E.stable(d.alphabet),criterion=E.stable(d.criterion),sources=[],sourceLinks=[],retainedOrigins=[];
 const indexedAlphabet=registrySnapshot.some(item=>item.indexed)?await hash(d.alphabet,c):null,indexedPages=new Map(indexedAlphabet?await Promise.all(d.pages.map(async p=>[p.id,await hashText(p.text,c)])):[]);
 // Unrelated archive entries must not consume network continuation pages.
 // Filter only exact metadata predicates already required below. Every selected
 // original still passes full receipt verification; the signed snapshot retains
 // the entire registry hash, and the query version invalidates older frontiers.
 const registry=registrySnapshot.filter(item=>item.inputVersion===inputVersion&&criterionMatches(item.indexed?item.criterion:item.task.criterion,d.criterion,policy)&&programs.has(E.stable(item.indexed?item.steps:item.task.steps))&&(item.indexed?item.alphabetSha256===indexedAlphabet&&item.pages.some(pin=>indexedPages.get(pin.id)===pin.textSha256):item.task.pages.some(p=>pages.get(p.id)?.text===p.text)));
 let reviewed=0;
 const response=()=>({schema:policy.page,...(policy===PREFIX_POLICY?{evidenceMode:policy.mode}:fullOutputPolicy(policy)?{questionPolicy:policy.mode}:{}),proposalId,domainId:d.id,inputVersion,scanId:state.scanId,sequence:state.sequence,previousPageSha256:state.previous,sources,sourceLinks,continuation:{nextCursor:null,complete:false},snapshotToken:null,pageSha256:'0'.repeat(64)});
 async function retain(source,link,admitted=false,location=null){if(!admitted)await Evidence.compare(source.task,inputVersion,[source],c);if(source.task.engine!==d.engine||E.stable(source.task.alphabet)!==alphabet||!criterionMatches(source.task.criterion,d.criterion,policy))throw fail('unavailable','A selected receipt changed its protocol.');const ids=positions(source,d,programs,pages);if(!ids.length)throw fail('unavailable','A selected receipt changed its exact inputs.');if(ids.every(id=>marked(served,id)))return true;
  const selectedLink=includeSourceContext?link:{href:link.href,label:link.label},addition={taskId:source.task.taskId,...selectedLink,...(includeSourceContext&&link.sourceKind?{sourceReceipt:{taskId:source.task.taskId,resultId:source.run.id,inputVersion:source.inputVersion,createdAt:source.run.createdAt}}:{})};sources.push(source);sourceLinks.push(addition);
  if(size(response())+LIMITS.cursorBytes+2048+responseReserveBytes>LIMITS.bytes){sources.pop();sourceLinks.pop();if(!sources.length)throw fail('source-too-large','One original receipt exceeds the evidence page limit. No cursor was advanced.');return false;}
  if(includeSourceContext)retainedOrigins.push(freeze({origin:retainedOrigin(source,location),sourceSha256:await hash(source,c)}));ids.forEach(id=>mark(served,id));return true;
 }
 while(state.stage<3&&reviewed<LIMITS.metadata&&sources.length<LIMITS.sources){
  if(state.stage===2){const item=registry[state.after];if(!item){state.stage=3;state.after=0;break;}reviewed++;const metadata=item.indexed?{steps:item.steps,criterion:item.criterion,pages:item.alphabetSha256===indexedAlphabet?d.pages.filter(p=>item.pages.some(pin=>pin.id===p.id&&pin.textSha256===indexedPages.get(p.id))):[]}:item.task;if(item.inputVersion===inputVersion&&programs.has(E.stable(metadata.steps))&&criterionMatches(metadata.criterion,d.criterion,policy)&&metadata.pages.some(p=>pages.get(p.id)?.text===p.text)){
    const ids=positions({task:metadata,inputVersion},d,programs,pages);if(!ids.every(id=>marked(served,id))){const proof=await readPublishedEvidence({recordId:item.recordId,revision:item.revision,caseId:item.caseId,crypto:c,programIndex,fetcher,signal});if(!proof)throw fail('unavailable','A published source is unavailable.');if(!await retain({task:proof.task,inputVersion:proof.inputVersion,run:proof.run},{href:'library.html#/experiment/'+item.recordId,label:'Inspect published calculations',sourceKind:'published-program',proposalId,publishedSource:{recordId:proof.publishedSource.recordId,revision:proof.publishedSource.revision,caseId:proof.publishedSource.caseId}},false,{kind:'published',recordId:proof.publishedSource.recordId,revision:proof.publishedSource.revision,caseId:proof.publishedSource.caseId}))break;}}
   state.after++;continue;
  }
  if(state.stage===1&&inputVersion!=='raw'){state.stage=2;state.after=0;continue;}
  const remaining=LIMITS.metadata-reviewed,local=state.stage===0;
  const criterionSQL=alias=>policy===STRICT_POLICY?`json_extract(${alias}.task_json,'$.criterion')=?`:`json_extract(${alias}.task_json,'$.criterion.kind') IN(SELECT value FROM json_each(?))`,criterionBinding=policy===STRICT_POLICY?criterion:E.stable(fullOutputPolicy(policy)?outputSourceKinds:['measurement','exact-prefix']);
  const sql=local?`SELECT r.rowid AS position,t.id AS task_id,t.task_hash,r.id AS result_id,r.created_at,json_extract(t.task_json,'$.steps') AS steps,
   (SELECT json_group_array(json_extract(wanted.value,'$.id')) FROM json_each(?) wanted WHERE EXISTS(SELECT 1 FROM json_each(t.task_json,'$.pages') actual WHERE json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text'))) AS pages
   FROM local_task_results r JOIN local_tasks t ON t.id=r.task_id WHERE r.rowid>? AND r.rowid<=? AND t.rowid<=? AND t.input_version=? AND json_extract(t.task_json,'$.engine')=? AND json_extract(t.task_json,'$.alphabet')=? AND ${criterionSQL('t')} AND json_extract(t.task_json,'$.steps') IN(SELECT value FROM json_each(?))
   AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=? AND links.rowid<=? AND public.rowid<=?)
   AND EXISTS(SELECT 1 FROM json_each(?) wanted JOIN json_each(t.task_json,'$.pages') actual ON json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text')) ORDER BY r.rowid,r.id LIMIT ?`:
   `SELECT saved.rowid AS position,saved.family_id,saved.revision,saved.case_id,saved.task_id,saved.result_hash AS result_id,saved.created_at,json_extract(saved.task_json,'$.steps') AS steps,json_array(json_extract(saved.task_json,'$.pages[0].id')) AS pages FROM family_case_results saved WHERE saved.rowid>? AND saved.rowid<=? AND saved.family_id='deor-feedback-v1' AND json_extract(saved.task_json,'$.engine')=? AND json_extract(saved.task_json,'$.alphabet')=? AND ${criterionSQL('saved')} AND json_extract(saved.task_json,'$.steps') IN(SELECT value FROM json_each(?)) AND EXISTS(SELECT 1 FROM json_each(?) wanted JOIN json_each(saved.task_json,'$.pages') actual ON json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text')) ORDER BY saved.rowid,saved.family_id,saved.revision,saved.case_id LIMIT ?`;
  const args=local?[scope,state.after,state.water.h1,state.water.h0,inputVersion,d.engine,alphabet,criterionBinding,stepJSON,inputVersion,state.water.h2,state.water.h3,scope,remaining]:[state.after,state.water.h4,d.engine,alphabet,criterionBinding,stepJSON,scope,remaining];
  // Query planning is not evidence. Both strategies retain the same predicates,
  // snapshot fences, rowid order and limit; all selected originals still pass
  // the unchanged receipt validation below. Strict legacy policy is untouched.
  const query=local&&policy===PREFIX_POLICY&&d.programs.length>=QUERY_LIMITS.minPrograms?await chooseLocalMetadataQuery({db,sql,bindings:args}):{sql,bindings:args};
  // A signed served bit excludes only an already validated exact case. Iterate
  // actual source pages once, preserving exact page bytes. Dense duplicate tails
  // are bounded by a rowid window; an exhausted nonfinal window stays incomplete.
  let metadataSQL=query.sql,metadataBindings=[...query.bindings],windowHigh=null;
  if(local&&policy===PREFIX_POLICY&&query.strategy==='rowid-keyset'){
   const tail="AND EXISTS(SELECT 1 FROM json_each(?) wanted JOIN json_each(t.task_json,'$.pages') actual ON json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text')) ORDER BY",scopePath="'$.'||json_quote(''||json_extract(actual.value,'$.id'))",stepPath="'$.'||json_quote(''||json_extract(t.task_json,'$.steps'))",replacement="AND EXISTS(SELECT 1 FROM json_each(t.task_json,'$.pages') actual WHERE json_extract(?, "+scopePath+"||'.text')=json_extract(actual.value,'$.text') AND COALESCE(substr(json_extract(?, "+stepPath+"),json_extract(?, "+scopePath+"||'.index')+1,1),'0')<>'1') ORDER BY";
   if(!metadataSQL.includes(tail))throw fail('unavailable','The maintained evidence query changed.');
   const scopeIndex=E.stable(Object.fromEntries(d.pages.map((page,index)=>[page.id,{text:page.text,index}]))),servedIndex={};
   for(const [steps,programIndex]of programs){let bits='';for(let page=0;page<d.pages.length;page++)bits+=marked(served,programIndex*d.pages.length+page)?'1':'0';if(bits.includes('1'))servedIndex[steps]=bits;}
   const servedJSON=E.stable(servedIndex);
   // This is an optional query optimization. An excessive derived lookup keeps
   // the original full query; it never drops declared pages, programs or proofs.
   // Each additional D1 string also stays below its 2,000,000-byte limit, with
   // 100,000 bytes of headroom. Measure UTF-8 bytes, not JavaScript characters.
   if(fitsLookupBudget(scopeIndex,servedJSON)){
    windowHigh=Math.min(state.water.h1,state.after+LIMITS.localRowids);
    metadataSQL=metadataSQL.replace(tail,replacement);metadataBindings[2]=windowHigh;
    metadataBindings.splice(metadataBindings.length-2,1,scopeIndex,servedJSON,scopeIndex);
   }
  }
  const rows=(await db.prepare(metadataSQL).bind(...metadataBindings).all())?.results;if(!Array.isArray(rows)||rows.length>remaining)throw fail('unavailable','The evidence index is malformed.');
  let stopped=false;
  for(const row of rows){reviewed++;if(!Number.isSafeInteger(row.position)||row.position<=state.after||row.position>(local?(windowHigh??state.water.h1):state.water.h4)||!HEX.test(row.task_id)||!HEX.test(row.result_id)||!Number.isFinite(Date.parse(row.created_at))||!programs.has(row.steps))throw fail('unavailable','A source pin is malformed.');const ids=JSON.parse(row.pages);if(!Array.isArray(ids)||!ids.length||new Set(ids).size!==ids.length||ids.some(id=>!pages.has(id)))throw fail('unavailable','A source scope is malformed.');const pi=programs.get(row.steps),positions=ids.map(id=>pi*d.pages.length+pages.get(id).index);
   if(!positions.every(id=>marked(served,id))){let source,link,location;
    if(local){location={kind:'local'};const loaded=await db.prepare(`SELECT t.task_json,t.task_hash,t.input_version,r.result_json,r.created_at FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id WHERE t.id=? AND t.task_hash=? AND r.id=? AND r.rowid=? AND r.created_at=? AND t.rowid<=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=? AND links.rowid<=? AND public.rowid<=?)`).bind(row.task_id,row.task_hash,row.result_id,row.position,row.created_at,state.water.h0,inputVersion,state.water.h2,state.water.h3).first();if(!loaded)throw fail('stale-scan','A selected public receipt is unavailable.');const task=JSON.parse(loaded.task_json);if(task.taskId!==row.task_id||await hash(task,c)!==row.task_hash||loaded.input_version!==inputVersion)throw fail('unavailable','A selected task identity changed.');source={task,inputVersion,run:{id:row.result_id,createdAt:loaded.created_at,result:await readAdmittedResult(task,{id:row.result_id,created_at:loaded.created_at,result_json:loaded.result_json},c)}};link={href:'run.html#task='+row.task_id,label:'Inspect saved output'};const associated=includeSourceContext&&await db.prepare('SELECT links.proposal_id FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=? AND links.proposal_id=? AND links.input_version=? AND links.rowid<=? AND public.rowid<=?').bind(row.task_id,proposalId,inputVersion,state.water.h2,state.water.h3).first();if(associated)Object.assign(link,{sourceKind:'saved-task',proposalId});}
    else{const loaded=await db.prepare('SELECT * FROM family_case_results WHERE rowid=? AND family_id=? AND revision=? AND case_id=? AND task_id=? AND result_hash=? AND created_at=?').bind(row.position,row.family_id,row.revision,row.case_id,row.task_id,row.result_id,row.created_at).first();if(!loaded)throw fail('stale-scan','A selected family receipt is unavailable.');const validated=await validateFamilyReceipt(loaded,c);source=validated.source;location={kind:'family',familyId:validated.familySource.familyId,revision:validated.familySource.revision,caseId:validated.familySource.caseId};link={href:'run.html#family=deor-feedback-v1&case='+row.case_id+'&revision='+row.revision,label:'Inspect family output'};}
    if(!await retain(source,link,local,location)){stopped=true;break;}
   }
   state.after=row.position;if(sources.length>=LIMITS.sources){stopped=true;break;}
  }
  if(stopped)break;if(rows.length<remaining){if(local&&windowHigh!==null&&windowHigh<state.water.h1){state.after=windowHigh;break;}state.stage++;state.after=0;}
 }
 await epoch(db,state.water);state.served=b64(served);const out=response(),complete=state.stage===3;out.continuation.complete=complete;if(complete)out.snapshotToken=await seal({schema:policy.snapshot,proposalId,domainId:d.id,inputVersion,queryHash,registryHash,scanId:state.scanId,issuedAt:state.issuedAt,water:state.water,stage:3,sequence:state.sequence,previousPageSha256:state.previous},key,c);
 // The page digest excludes its next cursor, avoiding a circular hash. The
 // authenticated cursor pins this digest and the next monotonic sequence.
 const digestBody={...out};delete digestBody.pageSha256;digestBody.continuation={complete};out.pageSha256=await hash(digestBody,c);
 if(!complete)out.continuation.nextCursor=await seal({...state,sequence:state.sequence+1,previous:out.pageSha256},key,c);
 if(size(out)+responseReserveBytes>LIMITS.bytes)throw fail('source-too-large','The original receipts exceed the evidence page limit. No cursor was advanced.');if(includeSourceContext)retainedPages.set(out,{crypto:c,entries:Object.freeze(retainedOrigins)});return out;
}

// Admission checks this signed completed baseline before and after its bounded
// selected-case reuse lookup. Later inserts are allowed; edits invalidate it.
export async function verifySnapshot(policy,{db,proposalId,domain,inputVersion,snapshotToken,cursorKey,now=Date.now(),crypto:c=globalThis.crypto,programIndex}){
 checkedPolicy(policy);const d=Q.inspect(domain);if(policy===INSPECTION_POLICY&&(d.schema!=='liberpedia-factored-finite-output-question-v1'||d.questionPolicy!==policy.mode||d.criterion.kind!=='measurement'))throw fail('unavailable','Use the maintained transformed-output inspection.');if(policy===OUTPUT_POLICY&&(d.schema!=='liberpedia-factored-finite-output-question-v1'||d.questionPolicy!==policy.mode))throw fail('unavailable','Use the maintained pinned language comparison.');if(policy===STRICT_POLICY&&d.schema!=='liberpedia-factored-finite-question-v2')throw fail('unavailable','Use a maintained prefix question.');if(policy===PREFIX_POLICY&&d.criterion.kind!=='exact-prefix')throw fail('unavailable','Derived prefix discovery requires an exact-prefix question.');const key=await keyFor(cursorKey,c),names=['schema','proposalId','domainId','inputVersion','queryHash','registryHash','scanId','issuedAt','water','stage','sequence','previousPageSha256'],value=await open(snapshotToken,key,c,names);
 const registry=await registryMetadata(programIndex);
 if(value.schema!==policy.snapshot||value.stage!==3||!Number.isSafeInteger(value.sequence)||value.sequence<0||value.sequence>1000000||(value.sequence===0?value.previousPageSha256!==null:!HEX.test(value.previousPageSha256))||value.proposalId!==proposalId||value.domainId!==d.id||inputVersion!==d.inputVersion||value.inputVersion!==inputVersion||!((await Promise.all([false,true].map(mode=>hash(queryDefinition(d,inputVersion,policy,mode),c)))).includes(value.queryHash))||value.registryHash!==await hash(registry,c)||!Number.isSafeInteger(now)||!Number.isSafeInteger(value.issuedAt)||value.issuedAt>now||now-value.issuedAt>LIMITS.ttlMs||typeof value.scanId!=='string'||!/^[a-zA-Z0-9_-]{24}$/.test(value.scanId)||!exact(value.water,['epoch','h0','h1','h2','h3','h4'])||Object.values(value.water).some(v=>!Number.isSafeInteger(v)||v<0))throw fail('stale-scan','This completed lookup no longer matches the declared question.');
 await epoch(db,value.water);return Object.freeze({proposalId,domainId:d.id,inputVersion,scanId:value.scanId,issuedAt:value.issuedAt,epoch:value.water.epoch});
}
