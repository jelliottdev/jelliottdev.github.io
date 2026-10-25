/* Pure authored operation comparison. No inference, discovery or coverage verdict. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const C=node?require('./claim-specification.js'):root.ClaimSpecification;
 const Research=node?require('./claim-research.js'):root.ClaimResearch,Search=node?require('./assistant-search.js'):root.AssistantSearch;
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
  // Findings and limits are shown before this comparison; complete conditions
  // and saved outputs remain in source details. Explain only the method match.
  for(let i=0;i<metadata.length;i++)for(const text of [metadata[i].input_description,metadata[i].evaluation.description]){
   const existing=sentences.find(entry=>entry.text===text);if(existing)existing.citations.push(i+1);else sentences.push({text,citations:[i+1]});
  }
  const citations=sources.map((_,i)=>i+1).join(', ');
  const answer='Reversing the runes within each row, while keeping rows in place, was tested on '+pageLabel(target)+' ['+citations+']. This matches the reversal step; other unspecified settings may differ.\n\n'+sentences.map(entry=>entry.text+' ['+entry.citations.join(', ')+']').join(' ');
  return answer.split(/\s+/).length<=180?answer:null;
 }
 function numericRelated(snapshot,documents){
  if(!Research?.prepare||!Search?.select||!Array.isArray(documents)||documents.length>5000)return null;
  const s=C.validateConfirmed(snapshot);
  if(s.unresolved.length||s.aim.status!=='specified'||s.scope.status!=='specified'||!keys(s.scope.value,['pages'])||!pages(s.scope.value.pages)||
    s.method.status!=='specified'||!keys(s.method.value,['operations'])||s.method.value.operations.length!==1)return null;
  const op=s.method.value.operations[0];
  if(!keys(op,['id','label','table','boundaries',...(own(op,'declaredFamilyId')?['declaredFamilyId']:[])])||
    op.id!=='word_prime_sums'||op.label!=='Word prime sums'||!['canonical','reversed'].includes(op.table)||
    !['non-rune','hyphen-period'].includes(op.boundaries)||own(op,'declaredFamilyId')&&op.declaredFamilyId!=='prime-indices')return null;
  const specified={representation:'GP29',inputVersion:'raw',wordBoundaries:'preserve',unmapped:'preserve'};
  if(Object.entries(specified).some(([k,v])=>s.rules[k]?.status!=='specified'||s.rules[k].value!==v))return null;
  if(s.rules.evaluation?.status!=='specified'||C.serialize(s.rules.evaluation.value)!==C.serialize({kind:'word-prime-sums',table:op.table,boundaries:op.boundaries}))return null;
  if(C.RULES.filter(k=>!own(specified,k)&&k!=='evaluation').some(k=>!['unspecified','not_applicable'].includes(s.rules[k]?.status)))return null;
  const prepared=Research.prepare(s),hint=prepared.discovery.steps[0]?.operation;
  if(prepared.discovery.steps.length!==1||!hint||hint.action!=='sum'||hint.operand!=='prime-values'||hint.within!=='word'||hint.table!==op.table)return null;
  const selected=Search.select(documents,prepared.query,prepared.pages,prepared.discovery).filter(d=>d.kind==='experiment').slice(0,2),sources=[],lines=[],tables=[],ids=new Set();let size=0;
  for(const doc of selected){
   if(ids.has(doc?.id))continue;
   if(!object(doc)||typeof doc.id!=='string'||!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(doc.id)||doc.href!=='#/experiments/'+doc.id||typeof doc.text!=='string')continue;
   const d=doc.discovery;
   if(!keys(d,['operations','evaluation'])||!Array.isArray(d.operations)||d.operations.length!==1||!Array.isArray(d.evaluation)||d.evaluation.length!==1||d.evaluation[0]!=='numeric-sums')continue;
   const actual=d.operations[0];
   if(!keys(actual,['action','operand','within','table'])||actual.action!=='sum'||actual.operand!=='prime-values'||!['word','row','window'].includes(actual.within)||!['canonical','reversed'].includes(actual.table))continue;
   let evidence;try{evidence=JSON.parse(doc.text);}catch{continue;}
   if(!object(evidence)||!['method','replay','measurement','control'].includes(evidence.record_type?.id)||doc.recordType&&doc.recordType!==evidence.record_type.id||!Array.isArray(evidence.scope?.pages))continue;
   const recordedPages=C.pages(evidence.scope.pages);
   if(!recordedPages.length||C.serialize(recordedPages)!==C.serialize(evidence.scope.pages))continue;
   if(size+doc.text.length>9000){if(!sources.length)return null;break;}
   size+=doc.text.length;ids.add(doc.id);sources.push(doc);tables.push(actual.table);const citation=' ['+sources.length+'].';
   const unit=actual.within==='word'?'words':actual.within==='row'?'rows':'windows';
   lines.push('Prime values summed within '+unit+' on '+pageLabel(recordedPages)+' ('+(actual.table==='canonical'?'usual':'reversed')+' table)'+citation);
  }
  if(!sources.length)return null;
  const compose=()=>{
   const requested=op.table==='canonical'?'usual':'reversed',different=tables.some(table=>table!==op.table);
   const used=[...new Set(tables)],actual=used.length===1?'the '+(used[0]==='canonical'?'usual':'reversed')+' table':'both the usual and reversed tables';
   const lead=different?'Your idea uses the '+requested+' prime table; these records use '+actual+'. They are related work, not the same test.':'These records use the '+requested+' prime table too. That establishes a shared summation step, not the same test.';
   return lead+'\n\n'+lines.join(' ')+' They do not establish that your chosen word boundaries or way of evaluating the sums were tested.';
  };
  let answer=compose();
  if(answer.split(/\s+/).length>180&&sources.length===2){sources.pop();lines.pop();tables.pop();answer=compose();}
  return answer.split(/\s+/).length<=180?{answer,sources,kind:'recorded-overlap'}:null;
 }
 function compare({snapshot,documents}={}){
  try{
   const numeric=numericRelated(snapshot,documents);if(numeric)return numeric;
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
