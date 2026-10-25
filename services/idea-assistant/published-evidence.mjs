/* Source-bound compiled count projections. These are not community submissions. */
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Registry from '../../published-count-evidence-data.js';
const HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const clone=v=>JSON.parse(E.stable(v));
const hash=async(v,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
const checkedDefault=new WeakMap();
async function checkRegistry(registry,cryptoAPI){
 if(!exact(registry,['schema','records','entries'])||registry.schema!=='liberpedia-published-count-evidence-v1'||!Array.isArray(registry.records)||registry.records.length>100||!Array.isArray(registry.entries)||registry.entries.length>100)throw Error('Published count registry is malformed.');
 const frozen=clone(registry),records=new Map(),seen=new Set(),receipts=[];
 for(const record of frozen.records){
  if(!exact(record,['recordId','revision','provenance'])||!SLUG.test(record.recordId)||!HEX.test(record.revision)||records.has(record.recordId))throw Error('Published record reference is malformed.');
  const p=record.provenance;
  if(!exact(p,['schema','recordId','projection','sourcePins','checkedAt','dateMeaning','expectationMeaning'])||p.schema!=='liberpedia-published-count-projection-v1'||p.recordId!==record.recordId||typeof p.checkedAt!=='string'||!Number.isFinite(Date.parse(p.checkedAt))||new Date(p.checkedAt).toISOString()!==p.checkedAt||typeof p.dateMeaning!=='string'||!p.dateMeaning.trim()||typeof p.expectationMeaning!=='string'||!p.expectationMeaning.trim()||await hash(p,cryptoAPI)!==record.revision)throw Error('Published projection provenance changed.');
  const projection=p.projection;
  if(!exact(projection,['id','criterion','pages','alphabetSha256','taskId','resultId'])||!SLUG.test(projection.id)||projection.criterion?.kind!=='word-affine-count'||!HEX.test(projection.alphabetSha256)||!HEX.test(projection.taskId)||!HEX.test(projection.resultId)||!Array.isArray(projection.pages)||!projection.pages.length||projection.pages.length>75||new Set(projection.pages).size!==projection.pages.length||projection.pages.some(id=>!/^lp[12]-[0-9]{2}$/.test(id)))throw Error('Published count projection is malformed.');
  if(!Array.isArray(p.sourcePins)||!p.sourcePins.length||p.sourcePins.length>100||p.sourcePins.some((pin,i)=>!exact(pin,['path','sha256'])||typeof pin.path!=='string'||!(/^[a-zA-Z0-9_./-]+$/.test(pin.path))||pin.path.startsWith('/')||pin.path.split('/').some(part=>!part||part==='.'||part==='..')||!HEX.test(pin.sha256)||i&&p.sourcePins[i-1].path>=pin.path))throw Error('Published source pins are malformed.');
  records.set(record.recordId,record);
 }
 for(const entry of frozen.entries){
  if(!exact(entry,['recordId','revision','caseId','task','inputVersion','run'])||!records.has(entry.recordId)||typeof entry.caseId!=='string'||entry.inputVersion!=='raw')throw Error('Published count receipt is malformed.');
  const record=records.get(entry.recordId),p=record.provenance,task=entry.task;
  if(entry.revision!==record.revision||entry.caseId!==p.projection.id+'--all-pages'||!exact(entry.run,['id','createdAt','result'])||entry.run.createdAt!==p.checkedAt||!HEX.test(entry.run.id)||task?.taskId!==p.projection.taskId||entry.run.id!==p.projection.resultId)throw Error('Published count receipt identifies another projection.');
  await E.checkIdentity(task,cryptoAPI);
  if(task.steps.length||E.stable(task.criterion)!==E.stable(p.projection.criterion)||E.stable(task.pages.map(page=>page.id))!==E.stable(p.projection.pages)||await hash(task.alphabet,cryptoAPI)!==p.projection.alphabetSha256||seen.has(task.taskId))throw Error('Published count task changed its declared scope or rules.');
  for(const page of task.pages){const pin=p.sourcePins.find(pin=>pin.path==='text/'+page.id+'.txt');if(!pin||await hash(page.text,cryptoAPI)!==pin.sha256)throw Error('Published page differs from its source bytes.');}
  const source={task,inputVersion:entry.inputVersion,run:entry.run};
  await Evidence.compare(task,entry.inputVersion,[source],cryptoAPI);
  seen.add(task.taskId);
  receipts.push({source,publishedSource:{taskId:task.taskId,resultId:entry.run.id,recordId:entry.recordId,revision:entry.revision,caseId:entry.caseId},provenance:p,protocolId:(await Evidence.describe(task,entry.inputVersion,cryptoAPI)).protocolId});
 }
 if(records.size!==new Set(frozen.entries.map(e=>e.recordId)).size)throw Error('Published record has no compiled receipt.');
 return receipts;
}
async function receipts(registry,cryptoAPI){
 if(registry!==Registry)return checkRegistry(registry,cryptoAPI);
 if(!checkedDefault.has(cryptoAPI))checkedDefault.set(cryptoAPI,checkRegistry(registry,cryptoAPI));
 return checkedDefault.get(cryptoAPI);
}
export async function findPublishedEvidence({task,inputVersion,crypto:cryptoAPI=globalThis.crypto,registry=Registry}){
 const descriptor=await Evidence.describe(task,inputVersion,cryptoAPI),all=await receipts(registry,cryptoAPI),sources=[],publishedSources=[];
 for(const receipt of all){
  if(receipt.source.inputVersion!==inputVersion||receipt.protocolId!==descriptor.protocolId)continue;
  const source=receipt.source;
  if(!task.pages.some(page=>source.task.pages.some(actual=>actual.id===page.id&&actual.text===page.text)))continue;
  sources.push(clone(source));publishedSources.push(clone(receipt.publishedSource));
 }
 return {sources,publishedSources};
}
export async function resolvePublishedEvidence({taskId,resultId,inputVersion,createdAt,crypto:cryptoAPI=globalThis.crypto,registry=Registry}){
 if(!HEX.test(taskId)||!HEX.test(resultId)||!['raw','reviewed'].includes(inputVersion)||createdAt!==undefined&&(typeof createdAt!=='string'||!Number.isFinite(Date.parse(createdAt))))throw Error('Pinned published source reference is invalid.');
 const found=(await receipts(registry,cryptoAPI)).find(r=>r.source.task.taskId===taskId&&r.source.run.id===resultId&&r.source.inputVersion===inputVersion&&(createdAt===undefined||r.source.run.createdAt===createdAt));
 return found?clone(found):null;
}
export async function readPublishedEvidence({recordId,revision,caseId,crypto:cryptoAPI=globalThis.crypto,registry=Registry}){
 if(!SLUG.test(recordId)||!HEX.test(revision)||typeof caseId!=='string'||caseId.length>200||!/^[a-z0-9-]+$/.test(caseId))throw Error('Published source reference is invalid.');
 const found=(await receipts(registry,cryptoAPI)).find(r=>r.publishedSource.recordId===recordId&&r.publishedSource.revision===revision&&r.publishedSource.caseId===caseId);
 return found?{...clone(found.source),publishedSource:clone(found.publishedSource),provenance:clone(found.provenance)}:null;
}
export function createPublishedEvidenceHandler({crypto:cryptoAPI=globalThis.crypto,registry=Registry}={}){
 return async(request,env)=>{
  const allowed=env?.SITE_ORIGIN,origin=request.headers.get('origin'),headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let valid=false;try{valid=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!valid)return reply({error:'Published computation evidence is unavailable.'},503);
  if(origin!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url),match=url.pathname.match(/^\/published-evidence\/([a-z0-9-]+)\/([a-z0-9-]+)$/);
  if(!match||[...url.searchParams.keys()].length!==1||!HEX.test(url.searchParams.get('revision')||''))return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   if(request.headers.get('access-control-request-method')!=='GET'||request.headers.get('access-control-request-headers'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Max-Age':'600'}});
  }
  if(request.method!=='GET')return reply({error:'Method not allowed.'},405);
  try{const found=await readPublishedEvidence({recordId:match[1],caseId:match[2],revision:url.searchParams.get('revision'),crypto:cryptoAPI,registry});return found?reply(found):reply({error:'Published source was not found.'},404);}catch{return reply({error:'Published computation evidence could not be verified.'},503);}
 };
}
