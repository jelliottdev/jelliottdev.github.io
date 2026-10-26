/* Exact complete-source mapping shared by planning, inspection and variations.
 * A compatible program does not change the original question identity and does
 * not establish that a preparation was historically consumed or a result found.
 * No network, target execution, generation or title-based inference. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,L=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,F=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler;
 const SCHEMA='liberpedia-reviewed-program-v1',ALPHABET_SHA256='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f',LIMITS=Object.freeze({responseBytes:16000});
 const exact=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k)),clone=value=>JSON.parse(L.stable(value)),same=(a,b)=>L.stable(a)===L.stable(b),ensure=(value,message)=>{if(!value)throw Error(message);},freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 const requiresExplicitInterrupters=card=>card.method.status==='specified'&&card.method.value.operations.some(op=>op.id==='interrupted_repeating_key'||Object.hasOwn(op,'interrupts'));
 const INTERRUPTER_REASON='Interrupted repeating keys require complete explicit canonical parameters; generated mapping is unavailable.';
 function validateCard(input){
  const value=J.capture(input,{maxBytes:H.MAX_BYTES,maxDepth:24,maxNodes:20000}),text=L.stable(value);let binary='';for(const byte of new TextEncoder().encode(text))binary+=String.fromCharCode(byte);
  const decoded=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft,checked=H.cardData(C.confirm(decoded,{id:'reviewed-program-validation',at:'2000-01-01T00:00:00.000Z'}));ensure(same(checked,value),'Use unchanged canonical questions.');return checked;
 }
function reversal(text){
 const m=text.match(/^reverse (?:(?:each|every) (line|row|word|page)|(?:the )?(?:runes|rune order) (?:within|inside|in) (?:each|every) (line|row|word|page))$/i);
 if(!m)return null;const unit=(m[1]||m[2]).toLowerCase();return {op:'reverse',unit:unit==='row'?'line':unit};
}
function exactScopeTail(text,scope){
 if(scope?.status!=='specified'||!exact(scope.value,['pages'])||!Array.isArray(scope.value.pages))return false;
 const pages=[];
 for(const part of text.split(/\s*(?:,|;|\band\b)\s*/i)){
  const m=part.match(/^LP([12])-(\d{1,2})(?:\s*[-–—]\s*(?:LP\1-)?(\d{1,2}))?$/i);if(!m)return false;
  const start=Number(m[2]),end=m[3]===undefined?start:Number(m[3]);if(end<start||end-start>74)return false;
  for(let i=start;i<=end;i++)pages.push('lp'+m[1]+'-'+String(i).padStart(2,'0'));
 }
 try{return new Set(pages).size===pages.length&&L.stable(C.pages(pages))===L.stable(scope.value.pages);}catch{return false;}
}
function parse(quote,scope){
 const q=quote.trim().replace(/[.!]$/,'').trim();let m;
 const direct=reversal(q);if(direct)return direct;
 // Retain and validate the entire quoted source; only a complete positive
 // reversal page clause may repeat the already-confirmed exact scope.
 const scoped=q.match(/^(reverse [\s\S]+?)\s+on\s+([\s\S]+)$/i);
 if(scoped&&reversal(scoped[1])&&exactScopeTail(scoped[2],scope))return reversal(scoped[1]);
 if((m=q.match(/^(?:apply |use )?affine(?: mapping| substitution)? a\s*=\s*(\d{1,2})\s*,\s*b\s*=\s*(\d{1,2})$/i))&&Number(m[1])<=28&&Number(m[2])<=28)return {op:'affine',a:Number(m[1]),b:Number(m[2])};
 if((m=q.match(/^(?:apply |use )?cumulative[ -]difference(?: with)? reset (?:at |per )?(?:each |every )?(page|line|word)$/i)))return {op:'cumulative-difference',reset:m[1].toLowerCase()};
 const scopedCumulative=q.match(/^((?:apply |use )?cumulative[ -]difference(?: with)? reset (?:at |per )?(?:each |every )?(page|line|word))\s+on\s+([\s\S]+)$/i);
 if(scopedCumulative&&exactScopeTail(scopedCumulative[3],scope))return {op:'cumulative-difference',reset:scopedCumulative[2].toLowerCase()};
 if((m=q.match(/^(?:apply |use |using )?finite key stream with key indices \[([0-9,\s]+)\], (subtract|add), reset at each (page|line|word)$/i))){
  const tokens=m[1].split(',').map(n=>n.trim());if(!tokens.length||tokens.length>2048||tokens.some(n=>!/^\d{1,2}$/.test(n)||Number(n)>28))return null;
  return {op:'finite-shift',key:tokens.map(Number),direction:m[2].toLowerCase(),reset:m[3].toLowerCase()};
 }
 if((m=q.match(/^(?:apply |use |using )?(Vigen[eè]re|repeating[ -]key|plaintext[ -]autokey|ciphertext[ -]autokey) with key indices \[([0-9,\s]+)\], (subtract|add), reset at each (page|line|word)$/i))){
  const tokens=m[2].split(',').map(n=>n.trim());if(!tokens.length||tokens.length>256||tokens.some(n=>!/^\d{1,2}$/.test(n)||Number(n)>28))return null;
  const name=m[1].toLowerCase();return {op:'keyed-shift',key:tokens.map(Number),mode:name.startsWith('plaintext')?'plaintext-autokey':name.startsWith('ciphertext')?'ciphertext-autokey':'repeat',direction:m[3].toLowerCase(),reset:m[4].toLowerCase()};
 }
 return null;
}
function connectors(text){return text.replace(/[\s,;.!]+/g,' ').trim().split(/\s+/).every(word=>!word||['please','try','then','and'].includes(word.toLowerCase()));}
function orderedSpans(label){
 if(typeof label!=='string'||!label.length||label.length>12000||/["'`{}]/.test(label))return null;
 const cuts=[];let depth=0;
 for(let i=0;i<label.length;i++){
  const ch=label[i];if(ch==='['){if(depth)return null;depth=1;continue;}if(ch===']'){if(!depth)return null;depth=0;continue;}
  if(depth||label.slice(i,i+4).toLowerCase()!=='then'||i===0||!(/\s/).test(label[i-1])||!(/\s/).test(label[i+4]||''))continue;
  let start=i;while(start>0&&/\s/.test(label[start-1]))start--;if(start>0&&/[,;]/.test(label[start-1]))start--;
  let end=i+4;while(end<label.length&&/\s/.test(label[end]))end++;
  cuts.push({start,end});if(cuts.length>=8)return null;i=end-1;
 }
 if(depth||!cuts.length)return null;
 const spans=[];let start=0;
 for(const stop of [...cuts,{start:label.length,end:label.length}]){
  let a=start,b=stop.start;while(a<b&&/\s/.test(label[a]))a++;while(b>a&&/\s/.test(label[b-1]))b--;
  if(a===b||b-a>1200)return null;spans.push({start:a,quote:label.slice(a,b)});start=stop.end;
 }
 return spans;
}
function deterministicCandidate(card){
 const operations=card.method.value.operations;if(!operations.length||operations.length>8)return null;const steps=[];
 for(let operationIndex=0;operationIndex<operations.length;operationIndex++){
  const operation=operations[operationIndex],label=operation.label;if(typeof label!=='string'||!label.length||label.length>12000)return null;
  const whole=label.length<=1200?parse(label,card.scope):null;let parts;
  if(whole)parts=[{start:0,quote:label,step:whole}];
  else{
   if(operation.id!=='described_method')return null;const spans=orderedSpans(label);if(!spans)return null;
   parts=spans.map(span=>({...span,step:parse(span.quote,card.scope)}));if(parts.some(part=>!part.step))return null;
  }
  for(const {start,quote,step}of parts){if(steps.length===8)return null;steps.push({source:{operationIndex,start,quote},step});}
 }
 return {version:1,steps,unsupported:[]};
}
function checkCandidate(input,candidate,{compile}={}){
 try{
  const card=validateCard(input);
  if(typeof compile!=='function')return {reason:'A reviewed deterministic compiler is required.'};
  if(card.unresolved.length)return {reason:'The idea has unresolved conditions.'};
  if(Object.values(card.rules).some(rule=>rule.status==='unrestricted'))return {reason:'An explicitly unrestricted rule cannot be represented by one fixed experiment.'};
  if(card.method.status!=='specified')return {reason:'The method wording is unspecified.'};
  if(requiresExplicitInterrupters(card))return {reason:INTERRUPTER_REASON};
  if(!exact(candidate,['version','steps','unsupported'])||candidate.version!==1||!Array.isArray(candidate.steps)||!candidate.steps.length||candidate.steps.length>8||!Array.isArray(candidate.unsupported)||candidate.unsupported.length>32||candidate.unsupported.some(s=>typeof s!=='string'||s.length>500)||new TextEncoder().encode(JSON.stringify(candidate)).length>LIMITS.responseBytes)return {reason:'The proposed mapping is malformed.'};
  if(candidate.unsupported.length)return {reason:'Some method wording needs an execution adapter.'};
  const original=card.method.value.operations,coverage=original.map(()=>[]),steps=[],notes=[];let previous=[-1,-1];
  for(const item of candidate.steps){
   if(!exact(item,['source','step'])||!exact(item.source,['operationIndex','start','quote']))return {reason:'Each step needs exact source evidence.'};
   const {operationIndex:index,start,quote}=item.source;
   if(!Number.isInteger(index)||index<0||index>=original.length||!Number.isInteger(start)||start<0||typeof quote!=='string'||!quote.length||quote.length>1200)return {reason:'Invalid source evidence.'};
   const operation=original[index];
   const keyedLabels={vigenere:['Vigenere','Vigenère'],repeating_key:['Repeating key','Repeating-key','Vigenere','Vigenère'],plaintext_autokey:['Plaintext autokey','Plaintext-autokey'],ciphertext_autokey:['Ciphertext autokey','Ciphertext-autokey'],finite_key:['Finite key stream']};
   if(Object.hasOwn(keyedLabels,operation.id)&&(!keyedLabels[operation.id].includes(operation.label)||!['key','direction','reset'].every(k=>Object.hasOwn(operation,k))))return {reason:'Explicit keyed operations require their exact parameters and plain matching label.'};
   if(Object.keys(operation).some(k=>!['id','label','declaredFamilyId','a','b','reset','unit','key','direction'].includes(k))||typeof operation.label!=='string'||operation.label.slice(start,start+quote.length)!==quote)return {reason:'The mapping does not preserve an exact method source.'};
   if(index<previous[0]||index===previous[0]&&start<previous[1])return {reason:'Method steps were reordered or overlap.'};
   const parsed=parse(quote,card.scope);if(!parsed||L.stable(parsed)!==L.stable(item.step))return {reason:'The complete source phrase does not support the proposed operation.'};
   const known={affine:'affine',cumulative_difference:'cumulative-difference',reverse_row_runes:'reverse',reverse_runes:'reverse',vigenere:'keyed-shift',repeating_key:'keyed-shift',plaintext_autokey:'keyed-shift',ciphertext_autokey:'keyed-shift',finite_key:'finite-shift'};
   if(Object.hasOwn(known,operation.id)&&known[operation.id]!==parsed.op)return {reason:'The mapping conflicts with an explicit operation.'};
   for(const key of ['a','b','reset','unit','key','direction'])if(Object.hasOwn(operation,key)&&L.stable(operation[key])!==L.stable(parsed[key]))return {reason:'An explicit parameter changed.'};
   const modes={vigenere:'repeat',repeating_key:'repeat',plaintext_autokey:'plaintext-autokey',ciphertext_autokey:'ciphertext-autokey'};if(Object.hasOwn(modes,operation.id)&&modes[operation.id]!==parsed.mode)return {reason:'The explicit keyed mode changed.'};
   if(!['described_method',...Object.keys(known)].includes(operation.id))return {reason:'The source operation needs an adapter.'};
   coverage[index].push([start,start+quote.length]);previous=[index,start+quote.length];steps.push(parsed);const description=parsed.op==='reverse'?'Reverse rune order within each '+parsed.unit:parsed.op==='affine'?'Map each rune index using ('+parsed.a+' × index + '+parsed.b+') modulo 29':parsed.op==='finite-shift'?'Apply a finite stream of '+parsed.key.length+' supplied GP indices, '+parsed.direction+', resetting at each '+parsed.reset+' without repetition':parsed.op==='keyed-shift'?'Apply '+parsed.mode+' using GP indices ['+parsed.key.join(',')+'], '+parsed.direction+', resetting at each '+parsed.reset:'Apply cumulative difference, resetting at each '+parsed.reset;notes.push('Proposed interpretation of “'+quote+'”: '+description+'.');
  }
  for(let i=0;i<original.length;i++){
   if(!coverage[i].length)return {reason:'An original method step was omitted.'};
   let end=0;
   for(const [start,stop]of coverage[i]){if(!connectors(original[i].label.slice(end,start)))return {reason:'Method conditions remain outside the proposed operations.'};end=stop;}
   if(!connectors(original[i].label.slice(end)))return {reason:'Method conditions remain outside the proposed operations.'};
  }
  const normalized=clone(card);
  normalized.method.value.operations=steps.map(s=>s.op==='reverse'?{id:'reverse_runes',label:'Reverse rune order within each '+s.unit,unit:s.unit}:s.op==='affine'?{id:'affine',a:s.a,b:s.b}:s.op==='finite-shift'?{id:'finite_key',key:s.key,direction:s.direction,reset:s.reset}:s.op==='keyed-shift'?{id:s.mode==='repeat'?'vigenere':s.mode==='plaintext-autokey'?'plaintext_autokey':'ciphertext_autokey',key:s.key,direction:s.direction,reset:s.reset}:{id:'cumulative_difference',reset:s.reset});
  if(steps.some(s=>s.op==='reverse'))notes.push('Reversal boundaries are proposed separately for each step; non-rune separators stay in place.');
  const validated=validateCard(normalized),plan=compile(validated);
  if(!plan||plan.reason)return {reason:plan?.reason||'The mapped plan could not be validated.'};
  if(L.stable(plan.steps)!==L.stable(steps))return {reason:'The deterministic compiler changed the proposed operations.'};
  return {card:validated,notes,steps:clone(steps),plan:clone(plan),mapping:clone(candidate)};
 }catch{return {reason:'The proposed method mapping could not be validated.'};}
}

 function validateCandidate(input,candidate,{compile}={}){
  try{return checkCandidate(validateCard(input),J.capture(candidate,{maxBytes:LIMITS.responseBytes,maxDepth:16,maxNodes:10000}),{compile});}catch{return {reason:'The proposed method mapping could not be validated.'};}
 }

 function validateMapping(originalCard,mapping){
  const original=validateCard(originalCard),candidate=J.capture(mapping,{maxBytes:LIMITS.responseBytes,maxDepth:16,maxNodes:10000}),out=validateCandidate(original,candidate,{compile:F.compile});ensure(!out.reason,out.reason||'The source mapping could not be verified.');return freeze(out);
 }
 async function hash(value,crypto){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:L.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 async function verify(input,crypto=root.crypto){
  const capture=value=>J.capture(value,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),value=capture(input),unchanged=()=>ensure(same(capture(input),value),'The reviewed program changed during verification.');
  ensure(exact(value,['originalCard','normalizedCard','mapping','task','inputVersion'])&&['raw','reviewed'].includes(value.inputVersion)&&crypto?.subtle,'Use the exact original question, reviewed mapping, normalized question, task and edition.');
  const originalCard=validateCard(value.originalCard),normalizedCard=validateCard(value.normalizedCard),mapped=validateMapping(originalCard,value.mapping);ensure(same(mapped.card,normalizedCard),'The normalized question differs from the exact source mapping.');
  const plan=mapped.plan,task=value.task;await L.checkIdentity(task,crypto);unchanged();
  ensure(plan.inputVersion===value.inputVersion&&same(plan.steps,task.steps)&&same(plan.criterion,task.criterion),'The reviewed mapping does not describe the exact task and edition.');
  ensure(Array.isArray(plan.pages)&&task.pages.length>0&&same(task.pages.map(p=>p.id),plan.pages.filter(id=>task.pages.some(p=>p.id===id))),'The reviewed task is not an ordered subset of the declared pages.');
  ensure(await hash(task.alphabet,crypto)===ALPHABET_SHA256,'The reviewed task must use the canonical GP29 alphabet.');unchanged();
  const originalProposalId='p_'+await hash(C.serialize(originalCard),crypto);unchanged();const normalizedProposalId='p_'+await hash(C.serialize(normalizedCard),crypto);unchanged();const taskSha256=await hash(task,crypto);unchanged();const mappingSha256=await hash(value.mapping,crypto);unchanged();
  return freeze({schema:SCHEMA,originalCard,normalizedCard,mapping:clone(value.mapping),inputVersion:value.inputVersion,originalProposalId,normalizedProposalId,taskId:task.taskId,taskSha256,mappingSha256});
 }
 // This verifies retained mapping contents, not that preparationId identifies
 // an authentic service row, nor that any source task was actually executed.
 async function verifyMappingProof(input,crypto=root.crypto){
  const capture=value=>J.capture(value,{maxBytes:128*1024,maxDepth:24,maxNodes:40000}),value=capture(input),unchanged=()=>ensure(same(capture(input),value),'The retained program proof changed during verification.');
  ensure(exact(value,['proof','originalCard','inputVersion'])&&['raw','reviewed'].includes(value.inputVersion)&&exact(value.proof,['schema','preparationId','basisSha256','normalizedCard','mapping'])&&value.proof.schema==='liberpedia-prepared-program-proof-v1'&&typeof value.proof.preparationId==='string'&&/^prep_[a-f0-9]{64}$/.test(value.proof.preparationId)&&typeof value.proof.basisSha256==='string'&&/^[a-f0-9]{64}$/.test(value.proof.basisSha256),'Use an exact retained prepared-program proof.');
  const proof=value.proof,originalCard=validateCard(value.originalCard),normalizedCard=validateCard(proof.normalizedCard),mapped=validateMapping(originalCard,proof.mapping);ensure(same(mapped.card,normalizedCard)&&mapped.plan.inputVersion===value.inputVersion,'The retained mapping changed its normalized question or input edition.');
  ensure(proof.basisSha256===await hash({kind:'mapped-card',normalizedCard:proof.normalizedCard,mapping:proof.mapping},crypto),'The retained mapped-basis identity changed.');unchanged();const originalProposalId='p_'+await hash(C.serialize(originalCard),crypto);unchanged();const normalizedProposalId='p_'+await hash(C.serialize(normalizedCard),crypto);unchanged();return freeze({proof,mapped,originalProposalId,normalizedProposalId});
 }
 async function verifyProof(input,crypto=root.crypto){
  const capture=value=>J.capture(value,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),value=capture(input),unchanged=()=>ensure(same(capture(input),value),'The retained program proof changed during verification.');ensure(exact(value,['proof','originalCard','task','inputVersion']),'Use an exact retained program and task.');
  const retained=await verifyMappingProof({proof:value.proof,originalCard:value.originalCard,inputVersion:value.inputVersion},crypto);unchanged();const proof=retained.proof,program=await verify({originalCard:value.originalCard,normalizedCard:proof.normalizedCard,mapping:proof.mapping,task:value.task,inputVersion:value.inputVersion},crypto);unchanged();return freeze({proof,program});
 }

 const api={SCHEMA,ALPHABET_SHA256,validateMapping,validateCandidate,verify,verifyProof,verifyMappingProof};if(node)module.exports=api;else root.ReviewedProgram=api;
})(typeof globalThis!=='undefined'?globalThis:this);
