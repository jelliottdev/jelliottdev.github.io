/* Source-bound pair-count clarification. No inference, execution or count-claim verification. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,J=node?require('./finite-json.js'):root.FiniteJSON;
 const BOUNDARIES='word-affine-boundaries',EVALUATION='word-affine-evaluation',own=(o,k)=>Object.hasOwn(o,k),capture=v=>J.capture(v,{maxBytes:160000,maxDepth:24,maxNodes:16000});
 const same=(a,b)=>C.serialize(a)===C.serialize(b),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function pages(text){
  const selected=[];for(const part of text.split(/\s*(?:,|;|\band\b)\s*/i)){
   const m=part.match(/^LP([12])-(\d{1,2})(?:\s*[-\u2013\u2014]\s*(?:LP\1-)?(\d{1,2}))?$/i);if(!m)return null;
   const first=+m[2],last=m[3]===undefined?first:+m[3];if(last<first||last>(m[1]==='1'?16:57))return null;
   for(let n=first;n<=last;n++)selected.push('lp'+m[1]+'-'+String(n).padStart(2,'0'));
  }try{return selected.length&&new Set(selected).size===selected.length?C.pages(selected):null;}catch{return null;}
 }
 function coefficient(text){if(!/^[+-]?\d{1,16}$/.test(text))return null;const n=BigInt(text);return n>=-9007199254740991n&&n<=9007199254740991n?Number((n%29n+29n)%29n):null;}
 function formula(text){
  const normalized=text.replace(/\u2212/g,'-').replace(/[\u2032\u2019]/g,"'").replace(/\s+/g,'');let m=normalized.match(/^(c'|y)=(.+)$/);if(!m)return null;
  const variable=m[1]==='y'?'x':'c',rhs=m[2];let suppliedA,suppliedB;
  m=rhs.match(new RegExp('^([+-]?\\d{1,16})?'+variable+'([+-]\\d{1,16})?$'));
  if(m){suppliedA=m[1]===undefined?'1':m[1];suppliedB=m[2]||'0';}
  else{m=rhs.match(new RegExp('^([+-]?\\d{1,16})([+-])(\\d{1,16})?'+variable+'$'));if(!m)return null;suppliedB=m[1];suppliedA=(m[2]==='-'?'-':'')+(m[3]||'1');}
  const a=coefficient(suppliedA),b=coefficient(suppliedB);return a===null||b===null?null:{a,b,suppliedA,suppliedB,source:text};
 }
 function parse(text){
  if(typeof text!=='string'||!text.trim()||text.length>1500||/[`{}\r\n<>]/.test(text))return null;
  let phrase=text.trim().replace(/[.!?]$/,'').trim(),scopePages=null;
  const on=phrase.match(/\s+on\s+(LP[12]-.+)$/i);if(on){scopePages=pages(on[1]);if(!scopePages)return null;phrase=phrase.slice(0,on.index);}
  const intent=phrase.match(/^(?:Count rune pairs (\d{1,2}) positions apart within (?:each word|words) satisfying|Test whether rune pairs (\d{1,2}) positions apart within (?:each word|words) follow)\s+(.+)$/i);if(!intent)return null;
  const lag=Number(intent[1]||intent[2]);if(lag<1||lag>12)return null;
  const mod=intent[3].match(/^(.+?)\s*(?:\(mod\s*(29)\)|mod(?:ulo)?\s*(29))$/i);if(!mod)return null;
  const equation=formula(mod[1].trim());return equation?freeze({lag,...equation,sourceText:text,...(scopePages?{scopePages}:{})}):null;
 }
 const matches=text=>!!parse(text);
 const binding=d=>C.serialize({source:d.source,aim:d.aim,method:d.method,scope:d.scope,rules:d.rules,unresolved:d.unresolved});
 function checked(draft){
  const d=capture(draft);if(!d||d.schema!==C.SCHEMA||d.status!=='draft'||d.confirmation||d.execution!=='not_run'||!Number.isSafeInteger(d.revision)||d.aim?.status!=='specified'||d.scope?.status!=='specified'||!Array.isArray(d.scope.value.pages)||!d.scope.value.pages.length||own(d.scope.value,'description')||d.method?.status!=='specified'||d.method.value.operations.length!==1||!Array.isArray(d.clarifications))return null;
  const op=d.method.value.operations[0];if(op.id!=='described_method'||Object.keys(op).some(key=>!['id','label','sourceText','declaredFamilyId','provenance'].includes(key))||typeof op.label!=='string'||own(op,'sourceText')&&op.sourceText!==op.label)return null;
  // A shared card preserves its entire method label, not private original notes.
  // Ordinary/AI drafts must cover the complete original, including any claims.
  if(d.source.origin!=='shared_link'&&op.label!==d.source.text)return null;
  const candidate=parse(op.label);if(!candidate||candidate.scopePages&&!same(candidate.scopePages,C.pages(d.scope.value.pages)))return null;
  // Do not retire an attached claim/constraint merely to obtain a count adapter.
  if(d.unresolved.length)return null;
  return {draft:d,candidate,binding:binding(d)};
 }
 function inspect(draft){try{const value=checked(draft);return value?freeze(value.candidate):null;}catch{return null;}}
 function question(draft){
  let value;try{value=checked(draft);}catch{return null;}if(!value)return null;const {draft:d,candidate:c,binding:key}=value;
  if(d.clarifications.some(item=>[BOUNDARIES,EVALUATION].includes(item.question)&&item.choice==='as-described'&&item.text===key))return null;
  const evaluation=d.rules.evaluation,criterion=evaluation.status==='specified'?evaluation.value:null,matching=criterion&&typeof criterion==='object'&&!Array.isArray(criterion)&&Object.keys(criterion).length===5&&criterion.kind==='word-affine-count'&&criterion.lag===c.lag&&criterion.a===c.a&&criterion.b===c.b&&['non-rune','hyphen-period'].includes(criterion.boundaries);
  const choice=d.clarifications.filter(item=>item.question===BOUNDARIES&&['non-rune','hyphen-period'].includes(item.choice)&&item.text===key).at(-1),boundaries=choice?.choice||(matching?criterion.boundaries:null),base=boundaries?EVALUATION:BOUNDARIES,id=base+':'+d.revision;
  if(!boundaries)return {id,prompt:'Where should each word end?',context:'Count rune pairs '+c.lag+' positions apart inside each word. Word breaks must be explicit.',choices:[{id:'non-rune',label:'Every non-rune character ends a word',example:'Spaces and line breaks also end words.'},{id:'hyphen-period',label:'Only hyphens and periods end words',example:'Spaces and line breaks join the runes on either side.'},{id:'as-described',label:'Keep my wording without choosing word breaks'}]};
  const normalized=c.suppliedA!==String(c.a)||c.suppliedB.replace(/^\+/,'')!==String(c.b)?' The supplied modulo-29 formula is equivalent to multiplier '+c.a+' and offset '+c.b+'.':'';
  const representation=d.rules.representation,conflict=representation.status!=='unspecified'&&!(representation.status==='specified'&&representation.value==='GP29');
  const source=d.rules.inputVersion.status==='specified'?'The supplied text edition is kept. ':'The text edition will be shown in the proposed plan. ';
  return {id,prompt:'What should this pair count establish?',context:'Treat c and c′ as GP rune indices 0–28, with c′ '+c.lag+' positions later in the same word.'+normalized+' '+source+(evaluation.status==='specified'&&!matching?'Choosing the numerical check replaces the current evaluation. ':'')+(conflict?'Your different representation condition is kept; it will prevent this GP-index calculation from running. ':'')+'This does not establish a cipher, a decryption, a tail probability or a reported count. Your original aim is kept.',choices:[{id:'count-only',label:'Count matching pairs and compare with their rearrangement average'},{id:'as-described',label:'Keep my intended check'}],boundaries};
 }
 function clarify(draft,id,choice){
  const value=checked(draft),q=question(draft);if(!value||!q||q.id!==id||!q.choices.some(item=>item.id===choice))throw Error('This pair-count question changed. Review the current choices.');
  const base=id.slice(0,id.lastIndexOf(':'));if(base===BOUNDARIES||choice==='as-described'){const next=C.revise(value.draft,{});next.clarifications.push({question:base,choice,text:value.binding,revision:next.revision});return next;}
  const c=value.candidate,boundaries=q.boundaries,criterion={kind:'word-affine-count',lag:c.lag,a:c.a,b:c.b,boundaries},op={id:'word_affine_count',label:'Within-word affine pair count',lag:c.lag,a:c.a,b:c.b,boundaries};
  const provenance={kind:'user_clarification',refs:[id,...value.draft.method.provenance.refs]},field=v=>C.field('specified',v,provenance),rules={evaluation:field(criterion)};
  if(value.draft.rules.representation.status==='unspecified')rules.representation=field('GP29');
  let next=C.applyMethodEdit(value.draft,{type:'replace',index:0,operation:op});next=C.revise(next,{rules});next.clarifications.push({question:base,choice,text:value.binding,revision:next.revision});return next;
 }
 const api={matches,inspect,question,clarify};if(node)module.exports=api;else root.WordAffineIntake=api;
})(typeof globalThis!=='undefined'?globalThis:this);
