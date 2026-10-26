/* Source-bound compilation only. No controls, admission, output or coverage evidence. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,P=node?require('./pinned-domain-partitions.js'):root.PinnedDomainPartitions,B=node?require('./repeating-key-banks.js'):root.RepeatingKeyBanks,S=node?require('./periodic-key-scope.js'):root.PeriodicKeyScope,E=node?require('./local-experiment.js'):root.LocalExperiment,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,F=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler,I=node?require('./local-input-bundle.js'):root.LocalInputBundle;
 const bound=new WeakMap(),members=new WeakMap(),SCHEMA='liberpedia-pinned-domain-member-v1',ALPHABET='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f',same=(a,b)=>E.stable(a)===E.stable(b),need=(v,m)=>{if(!v)throw Error(m);},exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k)),capture=v=>J.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),copy=v=>capture(v),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function unicode(v){if(typeof v==='string')need(!/[\ud800-\udfff]/u.test(v),'Use exact Unicode scalar source text.');else if(v&&typeof v==='object')for(const k of Object.keys(v)){unicode(k);unicode(v[k]);}}
 async function hash(v,crypto,raw=false){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function operation(s){
  if(s.op==='reverse')return {id:'reverse_runes',label:'Reverse rune order within each '+s.unit,unit:s.unit};
  if(s.op==='affine')return {id:'affine',label:'Affine substitution',a:s.a,b:s.b};
  if(s.op==='cumulative-difference')return {id:'cumulative_difference',label:'Cumulative difference',reset:s.reset};
  const common={key:copy(s.key),direction:s.direction,reset:s.reset};
  if(s.op==='finite-shift')return {id:'finite_key',label:'Finite key stream',...common};
  if(s.op==='interrupted-keyed-shift')return {id:'interrupted_repeating_key',label:'Interrupted repeating key',interrupts:copy(s.interrupts),...common};
  const mode={'repeat':['repeating_key','Repeating key'],'plaintext-autokey':['plaintext_autokey','Plaintext autokey'],'ciphertext-autokey':['ciphertext_autokey','Ciphertext autokey']}[s.mode];
  need(s.op==='keyed-shift'&&mode,'This unchanged operation needs a maintained canonical adapter.');return {id:mode[0],label:mode[1],...common};
 }
 async function prepare(parentDomain,{bundle,crypto=root.crypto}={}){
  const domain=capture(parentDomain),source=capture(bundle);unicode(domain);unicode(source);
  const unchanged=()=>need(same(capture(parentDomain),domain)&&same(capture(bundle),source),'The parent domain or official source changed during binding.');
  const plan=await P.prepare(domain,{crypto});unchanged();
  // Parse the complete official aggregate, then independently pin every declared
  // full-parent page. Unselected bundle pages never authorize a new scope.
  need(Array.isArray(source.pages)&&source.pages.every(p=>typeof p?.id==='string'&&p.id.length===6),'Use exact official source page identities.');
  const official=I.parse(source);need(await hash(official.alphabet,crypto)===ALPHABET&&domain.alphabetSha256===ALPHABET,'The canonical GP29 alphabet pin changed.');unchanged();
  const pages=[];for(const pin of domain.pages){const page=official.pages.get(pin.id),text=page?.[domain.inputVersion==='raw'?'raw':'reviewed_text'];need(typeof text==='string'&&await hash(text,crypto,true)===pin.textSha256,'A complete parent page or input-edition pin changed.');unchanged();pages.push({id:pin.id,text});}
  const token=freeze({state:'source-bound-planning-only',domainId:plan.domainId});bound.set(token,{domain:freeze(domain),plan,alphabet:freeze(copy(official.alphabet)),pages:freeze(pages),crypto});return token;
 }
 function inspect(token){const value=bound.get(token);need(value,'Use an unchanged source-bound parent token.');return freeze({state:'source-bound-planning-only',domain:value.domain,plan:value.plan});}
 async function derive(token,selection){
  const parent=bound.get(token);need(parent,'Use an unchanged source-bound parent token.');const chosen=capture(selection),unchanged=()=>need(same(capture(selection),chosen),'The selected domain member changed during compilation.');
  need(exact(chosen,['globalSettingIndex','pageIds'])&&Number.isSafeInteger(chosen.globalSettingIndex)&&chosen.globalSettingIndex>=0&&chosen.globalSettingIndex<parent.domain.bank.count&&Array.isArray(chosen.pageIds)&&chosen.pageIds.length>0&&chosen.pageIds.length<=parent.pages.length&&chosen.pageIds.every(id=>typeof id==='string'&&id.length===6)&&new Set(chosen.pageIds).size===chosen.pageIds.length,'Choose one exact global setting and ordered nonempty page subset.');
  const selected=parent.pages.filter(p=>chosen.pageIds.includes(p.id));need(same(selected.map(p=>p.id),chosen.pageIds),'Selected pages must preserve the complete parent order and scope.');
  const crypto=parent.crypto,domain=parent.domain,key=copy(B.resolve({...domain.bank,start:chosen.globalSettingIndex,count:1})[0]),steps=copy(domain.steps),sourceStep={...steps[domain.keyOperation],key};let proof=null;
  if(sourceStep.op==='keyed-shift'&&key.length>256){
   need(sourceStep.mode==='repeat','An oversized autokey seed cannot be silently replaced by periodic arithmetic.');
   // All planner-supported operations preserve rune membership and every
   // non-rune position. Earlier operations therefore cannot enlarge a segment.
   proof=await S.prepare({cycle:key,direction:sourceStep.direction,reset:sourceStep.reset,inputVersion:domain.inputVersion,alphabet:parent.alphabet,pages:parent.pages},{crypto});unchanged();steps[domain.keyOperation]=copy(proof.step);
  }else steps[domain.keyOperation]=sourceStep;
  const field=value=>C.field('specified',value),draft=C.createDraft({source:{text:'One exact source-pinned parent-domain setting.'},aim:field({outcomeId:domain.aim.outcomeId,detail:domain.aim.detail,wording:domain.aim.detail}),method:field({operations:steps.map(operation)}),scope:field({pages:chosen.pageIds}),rules:{inputVersion:field(domain.inputVersion),representation:field('GP29'),unmapped:field('preserve'),wordBoundaries:field('preserve'),...(steps.some(s=>s.op==='cumulative-difference')?{initialState:field(0)}:{}),evaluation:field(domain.criterion.kind==='measurement'?'measurement':copy(domain.criterion))}}),card=H.cardData(C.confirm(draft,{id:'pinned-domain-member',at:'2000-01-01T00:00:00.000Z'}));
  need(new TextEncoder().encode(E.stable(card)).length<=H.MAX_BYTES,'This complete member exceeds the canonical question size; nothing was shortened.');
  const plan=F.compile(card);need(!plan.reason&&!plan.state&&same(plan.steps,steps)&&same(plan.pages,chosen.pageIds)&&same(plan.criterion,domain.criterion)&&plan.inputVersion===domain.inputVersion,'The canonical fixed compiler cannot preserve this exact selected program.');
  need(card.outcome.status==='specified'&&card.outcome.value.outcomeId===domain.aim.outcomeId&&card.outcome.value.detail===domain.aim.detail,'The selected canonical question changed its parent aim.');
  const task=await E.prepare({title:'Pinned domain member',pages:copy(selected),alphabet:copy(parent.alphabet),steps:plan.steps,criterion:plan.criterion},crypto);unchanged();const cardSha256=await hash(C.serialize(card),crypto,true),taskSha256=await hash(task,crypto);unchanged();
  const basis={schema:SCHEMA,parentDomainId:parent.plan.domainId,globalSettingIndex:chosen.globalSettingIndex,selection:chosen,sourceStep,actualSteps:steps,representationProof:proof,cardIdentity:'p_'+cardSha256,cardSha256,taskSha256,inputVersion:domain.inputVersion};
  const memberId='m_'+await hash(basis,crypto);unchanged();const member=freeze({...basis,memberId,state:'compiled-only',checks:{admission:false,controls:false,execution:false,evidence:false},card,task,plan});members.set(member,token);return member;
 }
 function inspectMember(member,options={}){need(options&&typeof options==='object'&&!Array.isArray(options)&&Reflect.ownKeys(options).every(k=>k==='parent'),'Use an exact optional parent binding.');const parent=Object.getOwnPropertyDescriptor(options,'parent');need(members.has(member)&&(!parent||Object.hasOwn(parent,'value')&&parent.enumerable&&members.get(member)===parent.value),'Use an unchanged member compiled from this exact source-bound parent.');return member;}
 const api=Object.freeze({SCHEMA,prepare,inspect,derive,inspectMember});if(node)module.exports=api;else root.PinnedDomainMembers=api;
})(typeof globalThis!=='undefined'?globalThis:this);
