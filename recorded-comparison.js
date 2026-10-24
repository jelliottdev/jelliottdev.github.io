/* Pure authored operation comparison. No inference, discovery or coverage verdict. */
(function(root){
 'use strict';
 const C=typeof module==='object'&&module.exports?require('./claim-specification.js'):root.ClaimSpecification;
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
 const keys=(value,expected)=>object(value)&&Object.keys(value).sort().join('|')===[...expected].sort().join('|');
 const signature=value=>keys(value,['action','operand','within'])&&value.action==='reverse'&&value.operand==='rune-order'&&value.within==='row';
 function pages(value){
  if(!Array.isArray(value)||!value.length||value.length>75||value.some(p=>typeof p!=='string'))return null;
  try{const normalized=C.pages(value);return normalized.length===value.length&&normalized.every((p,i)=>p===value[i])?normalized:null;}catch{return null;}
 }
 function pageWords(text){
  const result=[];
  for(const piece of text.split(/\s*(?:,|;|\band\b)\s*/i)){
   const match=piece.match(/^LP([12])-(\d{2})(?:\s*[-–—]\s*(?:LP\1-)?(\d{2}))?$/i);
   if(!match)return null;
   const start=Number(match[2]),end=Number(match[3]||match[2]);if(end<start||end-start>74)return null;
   for(let i=start;i<=end;i++)result.push('lp'+match[1]+'-'+String(i).padStart(2,'0'));
  }
  return pages(result);
 }
 function positiveLabel(value,target,allowPages){
  if(typeof value!=='string'||value.length>500)return false;
  const parts=value.trim().replace(/[.!]$/,'').split(/\s+on\s+/i);
  if(parts.length>2||parts.length===2&&!allowPages)return false;
  if(!/^(?:reverse (?:the )?rune order within (?:each row|rows)|reverse each row|read each row backwards)$/i.test(parts[0]))return false;
  if(parts.length===2){const described=pageWords(parts[1]);if(!described||C.serialize(described)!==C.serialize(target))return false;}
  return true;
 }
 function supported(snapshot){
  const s=C.validateConfirmed(snapshot);
  if(s.aim.status!=='specified'||C.normalizeOutcome(s.aim).id!=='decipher'||s.unresolved.length)return null;
  if(s.scope.status!=='specified'||!keys(s.scope.value,['pages']))return null;
  const target=pages(s.scope.value.pages);if(!target)return null;
  if(Object.keys(s.rules).length!==C.RULES.length||C.RULES.some(key=>s.rules[key]?.status!=='unspecified'))return null;
  if(s.method.status!=='specified'||!keys(s.method.value,['operations'])||s.method.value.operations.length!==1)return null;
  const op=s.method.value.operations[0];
  if(!object(op)||op.id!=='reverse_row_runes'||Object.keys(op).some(key=>!['id','label','sourceText','provenance','declaredFamilyId'].includes(key)))return null;
  if(own(op,'declaredFamilyId')&&op.declaredFamilyId!=='transposition')return null;
  if(own(op,'label')&&!positiveLabel(op.label,target,false)||own(op,'sourceText')&&!positiveLabel(op.sourceText,target,true))return null;
  return target;
 }
 // These fields are plain prose, not embedded Markdown or source citations.
 const prose=value=>typeof value==='string'&&value.trim()===value&&value.length>0&&value.length<=500&&!/[\u0000-\u001f\u007f\[\]`*\\]/.test(value);
 function reviewed(doc,target){
  if(!object(doc)||doc.kind!=='experiment'||typeof doc.id!=='string'||!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(doc.id)||doc.href!=='#/experiments/'+doc.id||typeof doc.text!=='string'||doc.text.length>64000)return null;
  let evidence;try{evidence=JSON.parse(doc.text);}catch{return null;}
  if(!object(evidence)||evidence.record_type?.id!=='method'||doc.recordType&&doc.recordType!=='method')return null;
  const m=doc.recordedComparison;
  if(!keys(m,['version','operation','executed_pages','evaluation','input_description','reuse'])||m.version!==1||!signature(m.operation))return null;
  const executed=pages(m.executed_pages),scope=pages(evidence.scope?.pages);
  if(!executed||!scope||executed.some(p=>!scope.includes(p))||target.some(p=>!executed.includes(p)))return null;
  if(!keys(m.evaluation,['kind','description','limitation'])||!['known-opening','english-score'].includes(m.evaluation.kind))return null;
  if(![m.input_description,m.reuse,m.evaluation.description,m.evaluation.limitation].every(prose))return null;
  return m;
 }
 function pageLabel(target){
  const out=[];for(let i=0;i<target.length;i++){
   const first=target[i];let last=first;
   while(i+1<target.length&&target[i+1].slice(0,4)===first.slice(0,4)&&Number(target[i+1].slice(4))===Number(last.slice(4))+1)last=target[++i];
   out.push(first.toUpperCase()+(last===first?'':'–'+last.slice(4)));
  }return out.join(', ');
 }
 function answerFor(sources,metadata,target){
  const sentences=[];
  for(let i=0;i<metadata.length;i++)for(const text of [metadata[i].input_description,metadata[i].evaluation.description,metadata[i].evaluation.limitation,metadata[i].reuse]){
   const existing=sentences.find(entry=>entry.text===text);if(existing)existing.citations.push(i+1);else sentences.push({text,citations:[i+1]});
  }
  const citations=sources.map((_,i)=>i+1).join(', ');
  const answer='Reversing the runes within each row, while keeping rows in place, was tested on '+pageLabel(target)+' ['+citations+']. This matches the reversal step; other unspecified settings may differ.\n\n'+sentences.map(entry=>entry.text+' ['+entry.citations.join(', ')+']').join(' ');
  return answer.split(/\s+/).length<=180?answer:null;
 }
 function compare({snapshot,documents}={}){
  try{
   const target=supported(snapshot);if(!target||!Array.isArray(documents)||documents.length>5000)return null;
   const sources=[],metadata=[],ids=new Set();
   for(const doc of documents){
    if(ids.has(doc?.id))continue;const m=reviewed(doc,target);if(!m)continue;
    ids.add(doc.id);sources.push(doc);metadata.push(m);if(sources.length===2)break;
   }
   if(!sources.length)return null;
   let answer=answerFor(sources,metadata,target);
   if(!answer&&sources.length===2){sources.pop();metadata.pop();answer=answerFor(sources,metadata,target);}
   return answer?{answer,sources,kind:'recorded-overlap'}:null;
  }catch{return null;}
 }
 const api={compare};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordedComparison=api;
})(globalThis);
