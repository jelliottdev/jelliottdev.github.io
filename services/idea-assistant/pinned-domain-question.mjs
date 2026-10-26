/* Exact public-question binding to maintained complete searches. No public route,
 * controls, admission, execution or writes. Loader seams are private dependencies. */
import Sources from './pinned-domain-sources.mjs';
import {createPinnedDomainSourceLoader} from './pinned-domain-registry.mjs';
import {loadInputBundle} from './official-inputs.mjs';
import C from '../../claim-specification.js';
import H from '../../claim-share.js';
import E from '../../local-experiment.js';
import J from '../../finite-json.js';
import M from '../../pinned-domain-members.js';
const bound=new WeakMap(),MAX=2*1024*1024,SCHEMA='liberpedia-pinned-domain-question-v1',HEX=/^[a-f0-9]{64}$/;
const need=(v,m)=>{if(!v)throw Error(m);},same=(a,b)=>E.stable(a)===E.stable(b),capture=v=>J.capture(v,{maxBytes:MAX,maxDepth:24,maxNodes:100000}),freeze=v=>{if(v&&typeof v==='object'&&!ArrayBuffer.isView(v)){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x));
const maintained=freeze(capture(Sources)),field=value=>C.field('specified',value),knownLabels=new Set(['Repeating key','Repeating-key','Vigenere','Vigenère']);
function unicode(v){if(typeof v==='string')need(!/[\ud800-\udfff]/u.test(v),'Use Unicode scalar question text.');else if(v&&typeof v==='object')for(const k of Object.keys(v)){unicode(k);unicode(v[k]);}}
async function hash(v,crypto,raw=false){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',raw?v:new TextEncoder().encode(typeof v==='string'?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
function canonical(input,readOnly=false){const value=J.capture(input,{maxBytes:H.MAX_BYTES,maxDepth:16,maxNodes:6000});unicode(value);const text=JSON.stringify(value),fragment='#idea='+btoa(String.fromCharCode(...new TextEncoder().encode(text))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');const draft=H.decode(fragment).draft,card=readOnly?H.readCard(fragment):H.cardData(C.confirm(draft,{id:'pinned-question-binding',at:'2000-01-01T00:00:00.000Z'}));need(same(value,card),'Use an exact canonical confirmed question.');return card;}
function detail(value){need(typeof value==='string'&&value.trim()===value&&[...value].length>=1&&[...value].length<=1000&&!/[\p{Cc}\p{Cf}]/u.test(value),'Use a bounded plain aim detail.');return value;}
export function cardFromMaintained(sourceId,options={}){
 const v=capture(options);need(exact(v,Object.hasOwn(v||{},'detail')?['detail']:[]),'Declare only optional original aim detail.');const source=maintained.find(s=>s.sourceId===sourceId);need(source,'Choose a maintained complete question.');const d=source.domain,aimDetail=detail(v.detail??d.aim.detail);
 return freeze(H.cardData(C.confirm(C.createDraft({source:{text:'Maintained complete source-pinned search.'},aim:field({outcomeId:d.aim.outcomeId,detail:aimDetail,wording:aimDetail}),method:field({operations:[{id:'repeating_key',label:'Repeating key',direction:d.steps[0].direction,reset:d.steps[0].reset}]}),scope:field({pages:d.pages.map(p=>p.id)}),rules:{representation:field('GP29'),inputVersion:field(d.inputVersion),unmapped:field('preserve'),wordBoundaries:field('preserve'),evaluation:field(capture(d.criterion)),searchBounds:field({kind:'finite-settings',version:1,parameters:[{operation:d.keyOperation,name:'key',valuesFrom:capture(d.bank)}]})}}),{id:'maintained-pinned-question',at:'2000-01-01T00:00:00.000Z'})));
}
function matches(card,source){
 const d=source.domain;if(card.unresolved.length||card.outcome.status!=='specified'||card.outcome.value.outcomeId!==d.aim.outcomeId||card.method.status!=='specified'||!exact(card.method.value,['operations'])||card.method.value.operations.length!==1||card.scope.status!=='specified'||!same(card.scope.value,{pages:d.pages.map(p=>p.id)}))return false;
 detail(card.outcome.value.detail);const op=card.method.value.operations[0],keys=['id','direction','reset',...(Object.hasOwn(op,'label')?['label']:[]),...(Object.hasOwn(op,'declaredFamilyId')?['declaredFamilyId']:[])];if(!exact(op,keys)||!['repeating_key','vigenere'].includes(op.id)||Object.hasOwn(op,'label')&&!knownLabels.has(op.label)||Object.hasOwn(op,'declaredFamilyId')&&op.declaredFamilyId!=='polyalphabetic'||d.keyOperation!==0||!same(d.steps,[{op:'keyed-shift',mode:'repeat',direction:op.direction,reset:op.reset}]))return false;
 const required={representation:'GP29',inputVersion:d.inputVersion,unmapped:'preserve',wordBoundaries:'preserve',evaluation:d.criterion,searchBounds:{kind:'finite-settings',version:1,parameters:[{operation:0,name:'key',valuesFrom:d.bank}]}};
 for(const [name,value]of Object.entries(required))if(!same(card.rules[name],{status:'specified',value}))return false;
 for(const name of C.RULES)if(!Object.hasOwn(required,name)&&!(card.rules[name].status==='unspecified'||name!=='reset'&&card.rules[name].status==='not_applicable'))return false;
 return true;
}
export function identify(input){
 const card=canonical(input,true);if(card.unresolved.length||card.outcome.status!=='specified')return null;
 const value=card.outcome.value.detail;if(typeof value!=='string'||value.trim()!==value||[...value].length<1||[...value].length>1000||/[\p{Cc}\p{Cf}]/u.test(value))return null;
 const candidates=maintained.filter(source=>matches(card,source));return candidates.length===1?candidates[0].sourceId:null;
}
function descriptor(input,expected){
 need(input&&typeof input==='object'&&!Array.isArray(input)&&Reflect.ownKeys(input).length===5,'Use an exact maintained source descriptor.');const v={};for(const name of ['sourceId','domain','template','manifestBytes','manifestSha256']){const d=Object.getOwnPropertyDescriptor(input,name);need(d?.enumerable&&Object.hasOwn(d,'value'),'Maintained source fields must be data.');v[name]=d.value;}
 need(v.sourceId===expected.sourceId&&v.manifestSha256===expected.manifestSha256&&v.manifestBytes instanceof Uint8Array&&v.manifestBytes.byteLength<=MAX,'The maintained source identity changed.');const result={sourceId:v.sourceId,domain:capture(v.domain),template:capture(v.template),manifestSha256:v.manifestSha256,manifestBytes:new Uint8Array(v.manifestBytes)};need(same(result.domain,expected.domain)&&same(result.template,expected.template),'The maintained domain or template changed.');return result;
}
async function official(fetcher){let raw;await loadInputBundle({fetcher,signal:AbortSignal.timeout(15000),read:async(response,max)=>{const reader=response.body?.getReader();need(reader,'Official source bytes unavailable.');const parts=[];let count=0;for(;;){const {done,value}=await reader.read();if(done)break;count+=value.byteLength;if(count>max){await reader.cancel();throw Error('Official source exceeds its bound.');}parts.push(value);}const bytes=new Uint8Array(count);let n=0;for(const part of parts){bytes.set(part,n);n+=part.byteLength;}raw=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));return raw;}});return raw;}
export async function prepare(input,{bundle,loadDomain,loadBundle,fetcher=globalThis.fetch,crypto=globalThis.crypto}={}){
 const v=capture(input);need(exact(v,['card','proposalId'])&&typeof v.proposalId==='string'&&/^p_[a-f0-9]{64}$/.test(v.proposalId)&&crypto?.subtle,'Use one exact original question and proposal identity.');const card=canonical(v.card),unchanged=()=>need(same(capture(input),v),'The original question changed during binding.');need(v.proposalId==='p_'+await hash(C.serialize(card),crypto),'The original question identity changed.');unchanged();
 const candidates=maintained.filter(source=>matches(card,source));need(candidates.length===1,'This exact question does not name one maintained complete search.');const expected=candidates[0],source=descriptor(await (loadDomain||createPinnedDomainSourceLoader(fetcher))(expected.sourceId),expected);unchanged();need(HEX.test(source.manifestSha256)&&await hash(source.manifestBytes,crypto,true)===source.manifestSha256,'The independently pinned control manifest changed.');unchanged();const inputs=capture(bundle===undefined?await (loadBundle?loadBundle():official(fetcher)):bundle),parent=await M.prepare(source.domain,{bundle:inputs,crypto});unchanged();
 const token=Object.freeze({});bound.set(token,{schema:SCHEMA,state:'bound-question-only',sourceId:source.sourceId,card:freeze(card),proposalId:v.proposalId,parent,source,parentDomainId:M.inspect(parent).plan.domainId,checks:freeze({admission:false,controls:false,execution:false,persistence:false,evidence:false})});return token;
}
export function inspect(token){const value=bound.get(token);need(value,'Use a private complete-question binding.');return freeze({...value,source:{...value.source,domain:capture(value.source.domain),template:capture(value.source.template),manifestBytes:new Uint8Array(value.source.manifestBytes)}});}
