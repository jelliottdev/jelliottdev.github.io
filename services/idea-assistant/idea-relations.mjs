/* Structural card comparison only. No novelty, equivalence or coverage oracle. */
import C from '../../claim-specification.js';
import S from '../../claim-share.js';

const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const encode=s=>{let binary='';for(const b of new TextEncoder().encode(s))binary+=String.fromCharCode(b);return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');};
const pointer=k=>String(k).replace(/~/g,'~0').replace(/\//g,'~1');
// Only these scalar scope metadata fields are known not to select a passage.
// Unknown scope properties are retained/compared, but cannot justify a page-only
// relationship. In particular, description is never assumed to mean full page.
const PAGE_METADATA=new Set(['artifactId','sourceId','release','inputVersion','transcription','corpus','manuscript','language']);
function charge(budget,size){budget.bytes+=size;if(budget.bytes>S.MAX_BYTES)throw Error('Card exceeds size limit');}
function boundedJSON(value,depth=0,budget={nodes:0,bytes:0}){
 if(depth>16||++budget.nodes>6000)throw Error('Card exceeds structural limits');
 if(value===null||typeof value==='boolean'){charge(budget,JSON.stringify(value).length);return value;}
 if(typeof value==='string'){if(value.length>S.MAX_BYTES)throw Error('Card exceeds size limit');charge(budget,new TextEncoder().encode(JSON.stringify(value)).length);return value;}
 if(typeof value==='number'&&Number.isFinite(value)){charge(budget,String(value).length);return value;}
 if(Array.isArray(value)){charge(budget,2+Math.max(0,value.length-1));return value.map(v=>boundedJSON(v,depth+1,budget));}
 if(value&&typeof value==='object'&&(Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null)){
  const keys=Object.keys(value);if(keys.length>3000)throw Error('Card exceeds structural limits');charge(budget,2+Math.max(0,keys.length-1));const result={};
  for(const key of keys){
   if(['__proto__','prototype','constructor'].includes(key))throw Error('Unsafe card field');
   charge(budget,new TextEncoder().encode(JSON.stringify(key)).length+1);
   const descriptor=Object.getOwnPropertyDescriptor(value,key);if(!own(descriptor,'value'))throw Error('Card fields must be data');
   result[key]=boundedJSON(descriptor.value,depth+1,budget);
  }return result;
 }throw Error('Card must contain JSON data');
}
export function validateCard(input){
 if(input&&typeof input==='object'&&!own(input,'version')&&own(input,'card')){
  const descriptor=Object.getOwnPropertyDescriptor(input,'card');if(!own(descriptor,'value'))throw Error('Card must be data');input=descriptor.value;
 }
 if(typeof input==='string'){
  if(new TextEncoder().encode(input).length>S.MAX_BYTES)throw Error('Card exceeds size limit');
  try{input=JSON.parse(input);}catch{throw Error('Invalid card JSON');}
 }
 const text=JSON.stringify(boundedJSON(input));if(new TextEncoder().encode(text).length>S.MAX_BYTES)throw Error('Card exceeds size limit');
 const draft=S.decode('#idea='+encode(text)).draft;
 const confirmed=C.confirm(draft,{id:'card-comparison-validation',at:'2000-01-01T00:00:00.000Z'});
 return JSON.parse(C.serialize(S.cardData(confirmed)));
}
function diff(left,right,path='',result=[]){
 if(C.serialize(left)===C.serialize(right))return result;
 if(left&&right&&typeof left==='object'&&typeof right==='object'&&Array.isArray(left)===Array.isArray(right)){
  const keys=Array.isArray(left)?Array.from({length:Math.max(left.length,right.length)},(_,i)=>String(i)):[...new Set([...Object.keys(left),...Object.keys(right)])].sort();
  for(const key of keys){
   const l=own(left,key),r=own(right,key),next=path+'/'+pointer(key);
   if(!l||!r)result.push({path:next,kind:l?'removed':'added',leftPresent:l,rightPresent:r,...(l?{left:left[key]}:{}),...(r?{right:right[key]}:{})});
   else diff(left[key],right[key],next,result);
  }
 }else result.push({path,kind:'changed',leftPresent:true,rightPresent:true,left,right});
 return result;
}
function purePages(scope){
 if(scope.status!=='specified'||!own(scope.value,'pages'))return false;
 return Object.entries(scope.value).every(([key,value])=>key==='pages'||(PAGE_METADATA.has(key)&&(value===null||['string','number','boolean'].includes(typeof value))));
}
function scopeMetadata(scope){return Object.fromEntries(Object.entries(scope.value).filter(([key])=>key!=='pages'));}
function methodOrderChanged(a,b){
 if(a.status!=='specified'||b.status!=='specified')return false;
 const x=a.value.operations.map(C.serialize),y=b.value.operations.map(C.serialize);
 return C.serialize(x)!==C.serialize(y)&&C.serialize([...x].sort())===C.serialize([...y].sort());
}
export function compareCards(leftInput,rightInput){
 const left=validateCard(leftInput),right=validateCard(rightInput),differences=diff(left,right);
 const exact=differences.length===0;
 const sameExceptScope=['outcome','method','rules','unresolved'].every(key=>C.serialize(left[key])===C.serialize(right[key]));
 const pageCandidate=!exact&&sameExceptScope&&purePages(left.scope)&&purePages(right.scope)&&C.serialize(scopeMetadata(left.scope))===C.serialize(scopeMetadata(right.scope));
 const pageDelta=pageCandidate?{added:right.scope.value.pages.filter(p=>!left.scope.value.pages.includes(p)),removed:left.scope.value.pages.filter(p=>!right.scope.value.pages.includes(p))}:null;
 const pageOnly=pageCandidate&&(pageDelta.added.length>0||pageDelta.removed.length>0);
 return {
  relationship:exact?'exact_same':pageOnly?'page_scope_variant':'different_specification',
  differences,
  changed:{outcome:C.serialize(left.outcome)!==C.serialize(right.outcome),method:C.serialize(left.method)!==C.serialize(right.method),methodOrder:methodOrderChanged(left.method,right.method),
   rules:C.RULES.filter(k=>C.serialize(left.rules[k])!==C.serialize(right.rules[k])),scope:C.serialize(left.scope)!==C.serialize(right.scope),unresolved:C.serialize(left.unresolved)!==C.serialize(right.unresolved)},
  ...(pageOnly?{pageDelta}:{}),novelty:'not_assessed',coverage:'not_assessed'
 };
}
