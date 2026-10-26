/* Source-authored finite domains. Compile inputs and replay synthetic witnesses only. */
import E from '../../local-experiment.js';
import Control from '../../local-control.js';
import {describeFiniteSource} from './finite-source-descriptor.mjs';
import Inputs from '../../local-input-bundle.js';
import J from '../../finite-json.js';
import Context from '../../followup-context.js';
import {validateCard} from './idea-relations.mjs';

export const LIMITS=Object.freeze({sourceBytes:2*1024*1024,bundleBytes:2*1024*1024,programs:1024,controlRunes:256,totalControlRunes:262144});
const BASE='https://jelliottdev.github.io',HEX=/^[a-f0-9]{64}$/,ID=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const require=(condition,message)=>{if(!condition)throw Error(message);};
const digest=async(value,crypto)=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',typeof value==='string'?new TextEncoder().encode(value):value))].map(v=>v.toString(16).padStart(2,'0')).join('');
const prose=(v,max)=>typeof v==='string'&&v.trim().length>0&&Array.from(v).length<=max&&!/[\x00-\x1f\x7f\u2028\u2029\u202a-\u202e\u2066-\u2069\ud800-\udfff]/u.test(v);
// Only immutable, fully verified declarations are retained. Current official
// bytes are still fetched and hashed before a previous validation can be reused.
const verifiedPlans=new WeakMap(),CACHE_BYTES=16*1024*1024,CACHE_ENTRIES=8;
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const live=signal=>{if(signal?.aborted)throw Error('Finite source loading cancelled.');};

// Accept the original source bytes, never a reserialized approximation of them.
export async function compileFiniteRecordPlan({recordId,followupId,raw,bundle},{crypto=globalThis.crypto,signal}={}){
 live(signal);
 require([recordId,followupId].every(v=>typeof v==='string'&&v.length<=100&&ID.test(v)),'Invalid record or follow-up ID.');
 require(raw?.bytes instanceof Uint8Array&&raw.bytes.byteLength<=LIMITS.sourceBytes,'Finite source exceeds its byte bound.');
 const bytes=raw.bytes.slice(),captured=J.capture(bundle,{maxBytes:LIMITS.bundleBytes,maxDepth:16,maxNodes:6000}),recordSha256=await digest(bytes,crypto),bundleSha256=await digest(E.stable(captured),crypto);live(signal);
 const key=recordId+'|'+followupId+'|'+recordSha256+'|'+bundleSha256;let cache=verifiedPlans.get(crypto);if(!cache){cache={bytes:0,entries:new Map()};verifiedPlans.set(crypto,cache);}const prior=cache.entries.get(key);if(prior){cache.entries.delete(key);cache.entries.set(key,prior);return prior.plan;}
 const record=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
 require(record.id===recordId&&record.status==='published'&&Array.isArray(record.browser_followups)&&record.browser_followups.length<=8,'This published finite follow-up is unavailable.');
 const found=record.browser_followups.filter(v=>v?.id===followupId);require(found.length===1,'This published finite follow-up is unavailable.');
 const recipe=found[0],hasMotivation=Object.hasOwn(recipe,'motivation');
 require(exact(recipe,['kind','id','title','question','scope_change','limitation','card','inputs','control',...(hasMotivation?['motivation']:[])])&&recipe.kind==='finite-settings','The finite declaration is malformed.');
 for(const name of ['title','question','scope_change','limitation'])require(prose(recipe[name],name==='title'?300:1200),'The finite follow-up text is malformed.');
 require(!hasMotivation||Context.valid(recipe.motivation),'The finite follow-up motivation is malformed.');
 const card=validateCard(recipe.card);require(E.stable(card)===E.stable(recipe.card),'The declared finite card is not canonical.');
 const source=Inputs.parse(captured),pins=recipe.inputs;
 require(exact(pins,['version','alphabet_sha256','pages'])&&['raw','reviewed'].includes(pins.version)&&HEX.test(pins.alphabet_sha256)&&Array.isArray(pins.pages)&&pins.pages.length>=1&&pins.pages.length<=75,'The finite input pins are malformed.');
 require(card.rules?.inputVersion?.status==='specified'&&card.rules.inputVersion.value===pins.version&&card.scope?.status==='specified'&&E.stable(card.scope.value.pages)===E.stable(pins.pages.map(p=>p?.id)),'The finite input scope changed.');
 require(await digest(E.stable(source.alphabet),crypto)===pins.alphabet_sha256,'The official alphabet changed.');
 for(const pin of pins.pages){
  live(signal);
  require(exact(pin,['id','text_sha256'])&&HEX.test(pin.text_sha256),'The finite page pin is malformed.');
  const page=source.pages.get(pin.id),text=pins.version==='raw'?page?.raw:page?.reviewed_text;
  require(typeof text==='string'&&await digest(text,crypto)===pin.text_sha256,'The pinned manuscript input changed.');
 }
 live(signal);
 const evaluation=card.rules?.evaluation;require(evaluation?.status==='specified','The finite evaluation must be explicit.');
 const compiled=await describeFiniteSource({card,alphabet:source.alphabet,pages:pins.pages.map(pin=>({id:pin.id,text:pins.version==='raw'?source.pages.get(pin.id).raw:source.pages.get(pin.id).reviewed_text}))},{crypto,signal}),domain=compiled.domain;
 live(signal);
 const control=recipe.control;require(exact(control,['kind','members'])&&control.kind==='finite-program-controls'&&Array.isArray(control.members)&&control.members.length===compiled.members.length&&control.members.length<=LIMITS.programs,'The finite controls do not cover the complete declared family.');
 const programs=new Map(domain.programs.map(p=>[p.id,p])),runes=new Set(source.alphabet.map(v=>v.rune));let total=0;
 for(let i=0;i<compiled.members.length;i++){
  live(signal);
  const member=control.members[i],expected=compiled.members[i];
  require(exact(member,['settings','control'])&&E.stable(member.settings)===E.stable(expected.settings),'The finite control settings changed or are incomplete.');
  const witness=member.control;require(exact(witness,['label','task','expected_result_sha256'])&&prose(witness.label,300)&&HEX.test(witness.expected_result_sha256),'The finite synthetic control is malformed.');
  await E.checkIdentity(witness.task,crypto);
  live(signal);
  require(witness.label.toLowerCase().includes('synthetic')&&witness.task.title.toLowerCase().includes('synthetic'),'Finite controls must be labeled synthetic.');
  const task=witness.task,count=task.pages.reduce((n,p)=>n+Array.from(p.text).filter(ch=>runes.has(ch)).length,0);total+=count;
  require(task.pages.length===1&&count>=1&&count<=LIMITS.controlRunes&&total<=LIMITS.totalControlRunes,'The finite synthetic controls exceed their bound.');
  // A family witness must check every output rune, even for a prefix target.
  require(exact(task.criterion,['kind','values'])&&task.criterion.kind==='exact-prefix'&&task.criterion.values.length===count,'A finite witness must check its complete synthetic output.');
  require(E.stable(task.alphabet)===E.stable(source.alphabet)&&E.stable(task.steps)===E.stable(programs.get(expected.programId).steps),'The finite witness uses a different program or alphabet.');
  const result=E.run(task);require(Control.passed(task,result)&&await digest(E.stable(result),crypto)===witness.expected_result_sha256,'The declared finite synthetic control failed.');
 }
 live(signal);
 const protocolSha256=await digest(E.stable(recipe),crypto);live(signal);
 const verified=freeze({state:'finite-plan-ready',origin:{recordId,followupId,recordSha256,protocolSha256},card,inputVersion:pins.version,domain:{domainId:domain.id,programs:domain.programs.length,pages:domain.pages.length,totalCases:domain.totalCases,criterion:domain.criterion,...(domain.questionPolicy?{questionPolicy:domain.questionPolicy}:{})},question:recipe.question,scopeChange:recipe.scope_change,limitation:recipe.limitation,...(hasMotivation?{motivation:recipe.motivation}:{}),snapshot:recipe});
 const cost=new TextEncoder().encode(E.stable(verified)).byteLength;if(cost<=CACHE_BYTES){while(cache.entries.size&&(cache.entries.size>=CACHE_ENTRIES||cache.bytes+cost>CACHE_BYTES)){const oldest=cache.entries.keys().next().value;cache.bytes-=cache.entries.get(oldest).bytes;cache.entries.delete(oldest);}cache.entries.set(key,{plan:verified,bytes:cost});cache.bytes+=cost;}
 return verified;
}

async function read(response,max){
 require(response.ok!==false&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The official finite source is unavailable.');
 const size=response.headers.get('content-length');require(size===null||/^\d+$/.test(size)&&Number(size)<=max,'The finite source exceeds its byte bound.');
 const reader=response.body?.getReader();require(reader,'Missing finite source.');let length=0;const parts=[];
 while(true){const item=await reader.read();if(item.done)break;length+=item.value.length;if(length>max){await reader.cancel();throw Error('The finite source exceeds its byte bound.');}parts.push(item.value);}
 const bytes=new Uint8Array(length);let pos=0;for(const part of parts){bytes.set(part,pos);pos+=part.length;}return {bytes,value:JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes))};
}
// A caller may supply its already fetched raw source and shared bounded get(path,max)
// callback. That caller retains its deadline and abort ownership; no duplicate GET.
export async function loadFiniteRecordPlan(ref,{raw,get,fetcher=globalThis.fetch,timeoutMs=20000,crypto=globalThis.crypto,signal}={}){
 live(signal);
 require([ref?.recordId,ref?.followupId].every(v=>typeof v==='string'&&v.length<=100&&ID.test(v)),'Invalid record or follow-up ID.');
 require(Number.isFinite(timeoutMs)&&timeoutMs>=1&&timeoutMs<=20000,'Invalid finite source deadline.');
 const controller=get?null:new AbortController(),activeSignal=controller&&signal?AbortSignal.any([controller.signal,signal]):controller?.signal||signal;let timer;
 async function fetcherResponse(path){live(activeSignal);return fetcher(BASE+path,{redirect:'manual',signal:activeSignal,cache:'no-cache'});}
 // Keep the Response promise outside read() so both shared and standalone paths
 // have precisely the same bounded source representation.
 const request=get|| (async(path,max)=>read(await fetcherResponse(path),max));
 const work=async()=>{live(activeSignal);const source=raw||await request('/experiments/records/'+ref.recordId+'/record.json',LIMITS.sourceBytes);live(activeSignal);const bundle=await request('/data/local-run-inputs.json',LIMITS.bundleBytes);live(activeSignal);return compileFiniteRecordPlan({...ref,raw:source,bundle:bundle.value},{crypto,signal:activeSignal});};
 try{return get?await work():await Promise.race([work(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Official finite source loading timed out.'));},timeoutMs);})]);}finally{if(timer)clearTimeout(timer);controller?.abort();}
}
