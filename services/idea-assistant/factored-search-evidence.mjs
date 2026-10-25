/* Read-only, authenticated discovery over one immutable factored question.
 * Receipt computations are replayed by the client, never executed here. */
import E from '../../local-experiment.js';
import Q from '../../factored-finite-question.js';
import Evidence from '../../computation-evidence.js';
import Counts from '../../published-count-evidence-data.js';
import Programs from '../../published-opening-evidence-data.js';
import {readPublishedEvidence} from './published-evidence.mjs';
import {validateFamilyReceipt} from './family-evidence.mjs';
const LIMITS=Object.freeze({sources:12,metadata:256,bytes:8*1024*1024,cursorBytes:32768,ttlMs:48*60*60*1000});
const enc=new TextEncoder(),HEX=/^[a-f0-9]{64}$/,fields=['schema','proposalId','domainId','inputVersion','queryHash','registryHash','scanId','issuedAt','sequence','previous','water','stage','after','served'];
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const b64=v=>btoa(String.fromCharCode(...v)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');
function un64(v){if(typeof v!=='string'||!v.length||!/^[a-zA-Z0-9_-]+$/.test(v))throw Error('Invalid base64 cursor.');return Uint8Array.from(atob(v.replaceAll('-','+').replaceAll('_','/')),c=>c.charCodeAt(0));}
function fail(code,message){const e=new Error(message);e.code=code;e.status=code==='stale-scan'?409:code==='source-too-large'?413:code==='invalid-cursor'?400:503;return e;}
const size=v=>enc.encode(E.stable(v)).length;
async function hash(v,c){return [...new Uint8Array(await c.subtle.digest('SHA-256',enc.encode(E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function keyFor(value,c){const bytes=typeof value==='string'?enc.encode(value):value;if(!(bytes instanceof Uint8Array)||bytes.length<32||bytes.length>1024)throw fail('unavailable','A dedicated evidence cursor key is required.');return c.subtle.importKey('raw',bytes,{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
async function seal(value,key,c){const body=enc.encode(E.stable(value));return b64(body)+'.'+b64(new Uint8Array(await c.subtle.sign('HMAC',key,body)));}
async function open(token,key,c){try{if(typeof token!=='string'||token.length>LIMITS.cursorBytes)throw Error();const bits=token.split('.');if(bits.length!==2)throw Error();const body=un64(bits[0]),signature=un64(bits[1]);if(signature.length!==32||!await c.subtle.verify('HMAC',key,signature,body))throw Error();const raw=new TextDecoder('utf-8',{fatal:true}).decode(body),value=JSON.parse(raw);if(E.stable(value)!==raw||!exact(value,fields))throw Error();return value;}catch{throw fail('invalid-cursor','The evidence cursor could not be authenticated.');}}
const tables=['local_tasks','local_task_results','local_task_ideas','research_ideas','family_case_results'];
async function boundary(db){let row;try{row=await db.prepare('SELECT epoch,'+tables.map((t,i)=>'(SELECT COALESCE(MAX(rowid),0) FROM '+t+') AS h'+i).join(',')+' FROM finite_evidence_epoch WHERE id=1').bind().first();}catch{throw fail('unavailable','The evidence snapshot fence is unavailable.');}if(!row||!Number.isSafeInteger(row.epoch)||row.epoch<0||tables.some((_,i)=>!Number.isSafeInteger(row['h'+i])||row['h'+i]<0))throw fail('unavailable','The evidence snapshot fence is unavailable.');return row;}
async function epoch(db,water){let row;try{row=await db.prepare('SELECT epoch FROM finite_evidence_epoch WHERE id=1').bind().first();}catch{throw fail('unavailable','The evidence snapshot fence is unavailable.');}if(!row||row.epoch!==water.epoch)throw fail('stale-scan','Saved evidence changed during this scan. Start a fresh lookup.');}
function positions(source,d,programs,pages){const index=programs.get(E.stable(source.task.steps));if(index===undefined||source.inputVersion!==d.inputVersion)return [];return source.task.pages.flatMap(p=>{const target=pages.get(p.id);return target&&target.text===p.text?[index*d.pages.length+target.index]:[];});}
function bitmap(value,count){const bytes=un64(value);if(bytes.length!==Math.ceil(count/8)||count%8&&bytes.at(-1)>>(count%8))throw fail('invalid-cursor','The evidence cursor bitmap changed.');return bytes;}
const marked=(bits,n)=>!!(bits[n>>3]&(1<<(n%8)));
const mark=(bits,n)=>{bits[n>>3]|=1<<(n%8);};
export {LIMITS};
export async function readFactoredEvidencePage({db,proposalId,domain,inputVersion,cursor=null,cursorKey,now=Date.now(),crypto:c=globalThis.crypto}){
 const d=Q.inspect(domain);if(!/^p_[a-f0-9]{64}$/.test(proposalId)||inputVersion!==d.inputVersion||!Number.isSafeInteger(now)||typeof db?.prepare!=='function')throw fail('unavailable','A bound original question and evidence store are required.');
 const key=await keyFor(cursorKey,c),registry=[...Counts.entries,...Programs.entries].map(v=>({recordId:v.recordId,revision:v.revision,caseId:v.caseId,inputVersion:v.inputVersion,task:v.task})).sort((a,b)=>E.stable([a.recordId,a.revision,a.caseId]).localeCompare(E.stable([b.recordId,b.revision,b.caseId]))),registryHash=await hash(registry,c),queryHash=await hash({engine:d.engine,inputVersion,alphabet:d.alphabet,programs:d.programs,pages:d.pages,criterion:d.criterion},c);
 let state=cursor===null?{schema:'liberpedia-factored-evidence-cursor-v1',proposalId,domainId:d.id,inputVersion,queryHash,registryHash,scanId:b64(c.getRandomValues(new Uint8Array(18))),issuedAt:now,sequence:0,previous:null,water:await boundary(db),stage:0,after:0,served:b64(new Uint8Array(Math.ceil(d.totalCases/8)))}:await open(cursor,key,c);
 if(state.schema!=='liberpedia-factored-evidence-cursor-v1'||state.proposalId!==proposalId||state.domainId!==d.id||state.inputVersion!==inputVersion||state.queryHash!==queryHash||state.registryHash!==registryHash)throw fail('stale-scan','This cursor belongs to another question or published source snapshot.');
 if(!Number.isSafeInteger(state.issuedAt)||state.issuedAt>now||now-state.issuedAt>LIMITS.ttlMs||!Number.isSafeInteger(state.sequence)||state.sequence<0||state.sequence>1000000||![0,1,2,3].includes(state.stage)||!Number.isSafeInteger(state.after)||state.after<0||typeof state.scanId!=='string'||!/^[a-zA-Z0-9_-]{24}$/.test(state.scanId)||state.previous!==null&&!HEX.test(state.previous)||!exact(state.water,['epoch','h0','h1','h2','h3','h4'])||Object.values(state.water).some(v=>!Number.isSafeInteger(v)||v<0))throw fail('invalid-cursor','The evidence cursor is invalid or expired.');
 await epoch(db,state.water);
 const served=bitmap(state.served,d.totalCases),programs=new Map(d.programs.map((p,i)=>[E.stable(p.steps),i])),pages=new Map(d.pages.map((p,i)=>[p.id,{text:p.text,index:i}])),stepJSON=E.stable(d.programs.map(p=>E.stable(p.steps))),scope=E.stable(d.pages),alphabet=E.stable(d.alphabet),criterion=E.stable(d.criterion),sources=[],sourceLinks=[];
 let reviewed=0;
 const response=()=>({schema:'liberpedia-factored-evidence-page-v1',proposalId,domainId:d.id,inputVersion,scanId:state.scanId,sequence:state.sequence,previousPageSha256:state.previous,sources,sourceLinks,continuation:{nextCursor:null,complete:false},pageSha256:'0'.repeat(64)});
 async function retain(source,link){await Evidence.compare(source.task,inputVersion,[source],c);if(source.task.engine!==d.engine||E.stable(source.task.alphabet)!==alphabet||E.stable(source.task.criterion)!==criterion)throw fail('unavailable','A selected receipt changed its protocol.');const ids=positions(source,d,programs,pages);if(!ids.length)throw fail('unavailable','A selected receipt changed its exact inputs.');if(ids.every(id=>marked(served,id)))return true;
  const addition={taskId:source.task.taskId,...link};sources.push(source);sourceLinks.push(addition);
  if(size(response())+LIMITS.cursorBytes+2048>LIMITS.bytes){sources.pop();sourceLinks.pop();if(!sources.length)throw fail('source-too-large','One original receipt exceeds the evidence page limit. No cursor was advanced.');return false;}
  ids.forEach(id=>mark(served,id));return true;
 }
 while(state.stage<3&&reviewed<LIMITS.metadata&&sources.length<LIMITS.sources){
  if(state.stage===2){const item=registry[state.after];if(!item){state.stage=3;state.after=0;break;}reviewed++;if(item.inputVersion===inputVersion&&programs.has(E.stable(item.task.steps))&&E.stable(item.task.criterion)===criterion&&item.task.pages.some(p=>pages.get(p.id)?.text===p.text)){
    const ids=positions({task:item.task,inputVersion},d,programs,pages);if(!ids.every(id=>marked(served,id))){const proof=await readPublishedEvidence({recordId:item.recordId,revision:item.revision,caseId:item.caseId,crypto:c});if(!proof)throw fail('unavailable','A published source is unavailable.');if(!await retain({task:proof.task,inputVersion:proof.inputVersion,run:proof.run},{href:'library.html#/experiment/'+item.recordId,label:'Inspect published calculations'}))break;}}
   state.after++;continue;
  }
  if(state.stage===1&&inputVersion!=='raw'){state.stage=2;state.after=0;continue;}
  const remaining=LIMITS.metadata-reviewed,local=state.stage===0;
  const sql=local?`SELECT r.rowid AS position,t.id AS task_id,t.task_hash,r.id AS result_id,r.created_at,json_extract(t.task_json,'$.steps') AS steps,
   (SELECT json_group_array(json_extract(wanted.value,'$.id')) FROM json_each(?) wanted WHERE EXISTS(SELECT 1 FROM json_each(t.task_json,'$.pages') actual WHERE json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text'))) AS pages
   FROM local_task_results r JOIN local_tasks t ON t.id=r.task_id WHERE r.rowid>? AND r.rowid<=? AND t.rowid<=? AND t.input_version=? AND json_extract(t.task_json,'$.engine')=? AND json_extract(t.task_json,'$.alphabet')=? AND json_extract(t.task_json,'$.criterion')=? AND json_extract(t.task_json,'$.steps') IN(SELECT value FROM json_each(?))
   AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=? AND links.rowid<=? AND public.rowid<=?)
   AND EXISTS(SELECT 1 FROM json_each(?) wanted JOIN json_each(t.task_json,'$.pages') actual ON json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text')) ORDER BY r.rowid,r.id LIMIT ?`:
   `SELECT saved.rowid AS position,saved.family_id,saved.revision,saved.case_id,saved.task_id,saved.result_hash AS result_id,saved.created_at,json_extract(saved.task_json,'$.steps') AS steps,json_array(json_extract(saved.task_json,'$.pages[0].id')) AS pages FROM family_case_results saved WHERE saved.rowid>? AND saved.rowid<=? AND saved.family_id='deor-feedback-v1' AND json_extract(saved.task_json,'$.engine')=? AND json_extract(saved.task_json,'$.alphabet')=? AND json_extract(saved.task_json,'$.criterion')=? AND json_extract(saved.task_json,'$.steps') IN(SELECT value FROM json_each(?)) AND EXISTS(SELECT 1 FROM json_each(?) wanted JOIN json_each(saved.task_json,'$.pages') actual ON json_extract(actual.value,'$.id')=json_extract(wanted.value,'$.id') AND json_extract(actual.value,'$.text')=json_extract(wanted.value,'$.text')) ORDER BY saved.rowid,saved.family_id,saved.revision,saved.case_id LIMIT ?`;
  const args=local?[scope,state.after,state.water.h1,state.water.h0,inputVersion,d.engine,alphabet,criterion,stepJSON,inputVersion,state.water.h2,state.water.h3,scope,remaining]:[state.after,state.water.h4,d.engine,alphabet,criterion,stepJSON,scope,remaining];
  const rows=(await db.prepare(sql).bind(...args).all())?.results;if(!Array.isArray(rows)||rows.length>remaining)throw fail('unavailable','The evidence index is malformed.');
  let stopped=false;
  for(const row of rows){reviewed++;if(!Number.isSafeInteger(row.position)||row.position<=state.after||!HEX.test(row.task_id)||!HEX.test(row.result_id)||!Number.isFinite(Date.parse(row.created_at))||!programs.has(row.steps))throw fail('unavailable','A source pin is malformed.');const ids=JSON.parse(row.pages);if(!Array.isArray(ids)||!ids.length||new Set(ids).size!==ids.length||ids.some(id=>!pages.has(id)))throw fail('unavailable','A source scope is malformed.');const pi=programs.get(row.steps),positions=ids.map(id=>pi*d.pages.length+pages.get(id).index);
   if(!positions.every(id=>marked(served,id))){let source,link;
    if(local){const loaded=await db.prepare(`SELECT t.task_json,t.task_hash,t.input_version,r.result_json,r.created_at FROM local_tasks t JOIN local_task_results r ON r.task_id=t.id WHERE t.id=? AND t.task_hash=? AND r.id=? AND r.rowid=? AND r.created_at=? AND t.rowid<=? AND EXISTS(SELECT 1 FROM local_task_ideas links JOIN research_ideas public ON public.proposal_id=links.proposal_id WHERE links.task_id=t.id AND links.input_version=? AND links.rowid<=? AND public.rowid<=?)`).bind(row.task_id,row.task_hash,row.result_id,row.position,row.created_at,state.water.h0,inputVersion,state.water.h2,state.water.h3).first();if(!loaded)throw fail('stale-scan','A selected public receipt is unavailable.');const task=JSON.parse(loaded.task_json);if(task.taskId!==row.task_id||await hash(task,c)!==row.task_hash||loaded.input_version!==inputVersion)throw fail('unavailable','A selected task identity changed.');source={task,inputVersion,run:{id:row.result_id,createdAt:loaded.created_at,result:JSON.parse(loaded.result_json)}};link={href:'run.html#task='+row.task_id,label:'Inspect saved output'};}
    else{const loaded=await db.prepare('SELECT * FROM family_case_results WHERE rowid=? AND family_id=? AND revision=? AND case_id=? AND task_id=? AND result_hash=? AND created_at=?').bind(row.position,row.family_id,row.revision,row.case_id,row.task_id,row.result_id,row.created_at).first();if(!loaded)throw fail('stale-scan','A selected family receipt is unavailable.');source=(await validateFamilyReceipt(loaded,c)).source;link={href:'run.html#family=deor-feedback-v1&case='+row.case_id+'&revision='+row.revision,label:'Inspect family output'};}
    if(!await retain(source,link)){stopped=true;break;}
   }
   state.after=row.position;if(sources.length>=LIMITS.sources){stopped=true;break;}
  }
  if(stopped)break;if(rows.length<remaining){state.stage++;state.after=0;}
 }
 await epoch(db,state.water);state.served=b64(served);const out=response(),complete=state.stage===3;out.continuation.complete=complete;
 // The page digest excludes its next cursor, avoiding a circular hash. The
 // authenticated cursor pins this digest and the next monotonic sequence.
 const digestBody={...out};delete digestBody.pageSha256;digestBody.continuation={complete};out.pageSha256=await hash(digestBody,c);
 if(!complete)out.continuation.nextCursor=await seal({...state,sequence:state.sequence+1,previous:out.pageSha256},key,c);
 if(size(out)>LIMITS.bytes)throw fail('source-too-large','The original receipts exceed the evidence page limit. No cursor was advanced.');return out;
}
