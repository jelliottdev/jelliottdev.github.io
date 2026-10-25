/* Strict intake clarification. No network, execution, or inferred word breaks. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'?require('./claim-specification.js'):root.ClaimSpecification;
 const ID='word-sum-boundaries',EVALUATION_ID='word-sum-evaluation',own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const normalize=s=>s.trim().replace(/\s+/g,' ');
 function scope(text){
  const pages=[];
  for(const item of text.split(/\s*(?:,|;|\band\b)\s*/i)){
   const m=item.match(/^LP([12])-(\d{1,2})(?:\s*[-–—]\s*(?:LP\1-)?(\d{1,2}))?$/i);
   if(!m)return null;
   const first=+m[2],last=m[3]===undefined?first:+m[3];
   if(last<first||last>(m[1]==='1'?16:57))return null;
   for(let n=first;n<=last;n++)pages.push('lp'+m[1]+'-'+String(n).padStart(2,'0'));
  }
  return pages.length?C.pages(pages):null;
 }
 function parse(text){
  if(typeof text!=='string'||text.length>3000||/[`{}\n\r<>]/.test(text))return null;
  let phrase=normalize(text).replace(/[.!?]$/,'').trim(),scopePages=null;
  const on=phrase.match(/\s+on\s+(LP[12]-.+)$/i);
  if(on){scopePages=scope(on[1]);if(!scopePages)return null;phrase=phrase.slice(0,on.index);}
  const reversed=phrase.match(/^reverse (?:the )?(?:gematria(?: primus)? prime|gematria primus|gematria|GP(?: prime)?) table(?:\s*(\([^)]*\)))?\s+(?:and|then)\s+sum (?:the words|each word|words)$/i);
  let table=null;
  if(reversed){
   if(reversed[1]&&!/^\(\s*F\s*=\s*109\s*,\s*U\s*=\s*107\s*(?:,\s*)?(?:\.{3}|\u2026)?\s*\)$/i.test(reversed[1]))return null;
   table='reversed';
  }else{
   // A table must be named explicitly. Bare "sum words" or an unspecified GP
   // table never receives the usual assignments by convention.
   const direct=/^(?:sum|add) (?:the )?(?:usual|standard|canonical) (?:GP|gematria(?: primus)?) prime values (?:within|in) each word$/i.test(phrase);
   const selected=phrase.match(/^use (?:the )?(usual|standard|canonical|reversed) (?:GP|gematria(?: primus)?) prime table(?:\s*(\([^)]*\)))?\s+(?:and|then)\s+sum (?:the words|each word|words)$/i);
   const trailing=phrase.match(/^sum (?:the words|each word|words) using (?:the )?(usual|standard|canonical|reversed) (?:GP|gematria(?: primus)?) prime table$/i);
   if(!direct&&!selected&&!trailing)return null;
   table=(selected?.[1]||trailing?.[1]||'canonical').toLowerCase()==='reversed'?'reversed':'canonical';
   if(selected?.[2]&&!(table==='reversed'?/^\(\s*F\s*=\s*109\s*,\s*U\s*=\s*107\s*(?:,\s*)?(?:\.{3}|\u2026)?\s*\)$/i:/^\(\s*F\s*=\s*2\s*,\s*U\s*=\s*3\s*(?:,\s*)?(?:\.{3}|\u2026)?\s*\)$/i).test(selected[2]))return null;
  }
  return {table,sourceText:text,...(scopePages?{scopePages}:{})};
 }
 const matches=text=>!!parse(text);
 const acknowledgement=draft=>C.serialize({source:draft.source.text,method:draft.method.value,aim:draft.aim,scope:draft.scope,rules:draft.rules});
 const provenance=value=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===2&&['supplied','user_clarification','project_context','proposed'].includes(value.kind)&&Array.isArray(value.refs)&&value.refs.length<=128&&value.refs.every(ref=>typeof ref==='string'&&ref.length<=12000);
 function inspect(draft){
  try{
   if(!draft||draft.schema!==C.SCHEMA||draft.status!=='draft'||draft.confirmation||draft.execution!=='not_run')return null;
   if(draft.aim?.status!=='specified'||draft.scope?.status!=='specified'||!Array.isArray(draft.scope.value.pages)||!draft.scope.value.pages.length||own(draft.scope.value,'description'))return null;
   const candidate=parse(draft.source?.text);if(!candidate)return null;
   const pages=C.pages(draft.scope.value.pages);
   if(candidate.scopePages&&C.serialize(candidate.scopePages)!==C.serialize(pages))return null;
   if(draft.method?.status!=='specified')return null;
   const ops=draft.method.value.operations;if(!Array.isArray(ops)||!ops.length||ops.length>2)return null;
   const spans=[];
   for(const op of ops){
    if(!op||op.id!=='described_method'||Object.keys(op).some(k=>!['id','label','sourceText','declaredFamilyId','provenance'].includes(k)))return null;
    if(own(op,'declaredFamilyId')&&op.declaredFamilyId!=='prime-indices')return null;
    if(own(op,'provenance')&&!provenance(op.provenance))return null;
    if(typeof op.label!=='string'||!op.label.trim()||own(op,'sourceText')&&(typeof op.sourceText!=='string'||normalize(op.sourceText)!==normalize(op.label)))return null;
    spans.push(normalize(op.label));
   }
   const source=normalize(draft.source.text);
   if(spans.length===1){if(spans[0]!==source)return null;}
   else{
    if(!source.startsWith(spans[0])||!source.endsWith(spans[1]))return null;
    const between=source.slice(spans[0].length,source.length-spans[1].length);
    if(!/^\s*[,;]?\s+(?:and|then)\s+$/i.test(between))return null;
   }
   for(const [name,value] of Object.entries({representation:'GP29',inputVersion:'raw',wordBoundaries:'preserve',unmapped:'preserve'})){
    const f=draft.rules[name];if(!f||f.status!=='unspecified'&&!(f.status==='specified'&&f.value===value))return null;
   }
   for(const name of ['boundaryMode','reset','initialState'])if(!['unspecified','not_applicable'].includes(draft.rules[name]?.status))return null;
   const evaluation=draft.rules.evaluation;
   if(evaluation.status!=='unspecified')return null;
   if(draft.unresolved.some(c=>c?.kind==='changed_method_rule'||c?.kind==='operation_ambiguity'))return null;
   return {...candidate,operationCount:ops.length};
  }catch{return null;}
 }
 function question(draft){
  const candidate=inspect(draft);if(!candidate||draft.clarifications.some(c=>[ID,EVALUATION_ID].includes(c.question)&&c.choice==='as-described'&&c.text===acknowledgement(draft)))return null;
  if(C.normalizeOutcome(draft.aim).id==='decipher'&&!draft.clarifications.some(c=>c.question===EVALUATION_ID&&c.choice==='numeric-ledger'&&c.text===acknowledgement(draft)))return {id:EVALUATION_ID,prompt:'What should the word sums establish?',context:'Adding prime values produces a numeric ledger. It does not test readable text or solve LP2. Your deciphering aim will stay unchanged.',choices:[{id:'numeric-ledger',label:'List numerical word sums',example:'Show each word and its total; do not judge readability or statistical significance.'},{id:'as-described',label:'Keep my intended evaluation'}]};
  return {id:ID,prompt:'Where should each word end?',
   context:'Use the archived raw rune text and the GP29 alphabet, with '+(candidate.table==='reversed'?'its prime values reversed (F=109, U=107, \u2026, EA=2)':'the usual prime assignments (F=2, U=3, \u2026, EA=109)')+'. This lists numeric word sums; it does not decode the text.',
   choices:[{id:'hyphen-period',label:'Hyphens and periods end words',example:'F / U-EA gives FU and EA; line breaks continue the word.'},
    {id:'non-rune',label:'Every non-rune ends a word',example:'F / U-EA gives F, U and EA; line breaks also end words.'},
    {id:'as-described',label:'Keep my wording; do not choose word boundaries'}]};
 }
 function clarify(draft,choice){
  const q=question(draft);if(!q||!q.choices.some(c=>c.id===choice))throw Error('Unavailable word-sum clarification');
  if(choice==='as-described'||q.id===EVALUATION_ID){
   const next=C.revise(draft,{});next.clarifications.push({question:q.id,choice,text:acknowledgement(draft),revision:next.revision});return next;
  }
  const references=[ID,...(draft.method.provenance?.refs||[]),...draft.method.value.operations.flatMap(op=>op.provenance?.refs||[])],provenance={kind:'user_clarification',refs:[...new Set(references)]},field=value=>C.field('specified',value,provenance),rules={};
  for(const [name,value] of Object.entries({representation:'GP29',inputVersion:'raw',wordBoundaries:'preserve',unmapped:'preserve'}))if(draft.rules[name].status==='unspecified')rules[name]=field(value);
  const table=inspect(draft).table;rules.evaluation=field({kind:'word-prime-sums',table,boundaries:choice});
  const method=field({...draft.method.value,operations:[{id:'word_prime_sums',label:'Word prime sums',table,boundaries:choice}]});
  const next=C.revise(draft,{method,rules});
  next.clarifications.push({question:ID,choice,revision:next.revision});return next;
 }
 const api={matches,inspect,question,clarify};
 if(typeof module!=='undefined')module.exports=api;else root.WordSumIntake=api;
})(typeof globalThis!=='undefined'?globalThis:this);
