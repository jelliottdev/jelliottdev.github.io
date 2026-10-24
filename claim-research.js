/* One bounded active-card request for browser/Worker research. No network calls. */
(function(root){
 'use strict';
 const C=typeof module==='object'&&module.exports?require('./claim-specification.js'):root.ClaimSpecification;
 const H=typeof module==='object'&&module.exports?require('./claim-share.js'):root.ClaimShare;
 const VERSION=1,MAX_ORIGINAL=8000,MAX_QUERY=1500,MAX_CONTEXT=6000,MAX_BODY=32000;
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k),encoder=new TextEncoder();
 function failure(code,message){const error=Error(message);error.code=code;throw error;}
 function plain(value,depth=0,budget={nodes:0,bytes:0}){
  if(depth>16||++budget.nodes>6000)failure('invalid-card','The standardized card is too deeply nested.');
  let result;
  if(value===null||typeof value==='boolean'||(typeof value==='number'&&Number.isFinite(value)))result=value;
  else if(typeof value==='string'){if(value.length>H.MAX_BYTES)failure('invalid-card','The standardized card is too long.');result=value;}
  else if(Array.isArray(value)){
   if(value.length>6000)failure('invalid-card','The standardized card is too large.');result=[];
   for(let i=0;i<value.length;i++){
    const descriptor=Object.getOwnPropertyDescriptor(value,String(i));if(!descriptor||!own(descriptor,'value'))failure('invalid-card','Standardized arrays must be JSON data.');
    result.push(plain(descriptor.value,depth+1,budget));
   }
  }else if(value&&typeof value==='object'&&(Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null)){
   const keys=Object.keys(value);if(keys.length>3000)failure('invalid-card','The standardized card is too large.');result={};
   for(const key of keys){if(['__proto__','prototype','constructor'].includes(key))failure('invalid-card','Unsafe standardized field.');
    const descriptor=Object.getOwnPropertyDescriptor(value,key);if(!own(descriptor,'value'))failure('invalid-card','Standardized fields must be JSON data.');
    result[key]=plain(descriptor.value,depth+1,budget);
   }
  }else failure('invalid-card','Standardized fields must be JSON data.');
  // A small node/leaf budget bounds work before the final exact UTF-8 check.
  if(result===null||typeof result!=='object'){budget.bytes+=encoder.encode(JSON.stringify(result)).length;if(budget.bytes>H.MAX_BYTES)failure('invalid-card','The standardized card is too long.');}
  return result;
 }
 function base64url(text){let binary='';for(const byte of encoder.encode(text))binary+=String.fromCharCode(byte);return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
 function parameterValue(value){
  if(value&&typeof value==='object'&&!Array.isArray(value)&&own(value,'status')){
   if(value.status==='unspecified')return undefined;
   if(value.status==='specified'&&own(value,'value'))return parameterValue(value.value);
  }
  if(Array.isArray(value))return value.map(parameterValue).filter(v=>v!==undefined);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,parameterValue(v)]).filter(([,v])=>v!==undefined));
  return value;
 }
 function parameterTerms(snapshot){
  const terms=[];
  for(const op of snapshot.method.value.operations)for(const [key,raw]of Object.entries(op)){
   if(['id','label','sourceText','provenance','editHistory','declaredFamilyId'].includes(key)||(op.id==='family_selection'&&key==='familyId'))continue;
   const value=parameterValue(raw);if(value===undefined)continue;
   if(typeof value==='boolean')terms.push(key+'='+value);
   else terms.push(typeof value==='string'?value:C.serialize(value));
  }
  return terms;
 }
 function discoveryHints(snapshot){
  const labels=C.reviewRows(snapshot).find(row=>row.label==='Method').tags;
  const classified=C.classifyMethod(snapshot.method).operations;
  return {steps:snapshot.method.value.operations.map((op,index)=>{
   const query=[labels[index]?.text,...parameterTerms({method:{value:{operations:[op]}}})].filter(Boolean).join('. ');
   // Only a supported, positive canonical operation supplies these hints.
   // Opaque wording and family labels remain lexical leads, not guessed rules.
   let operation;
   if(op.id==='reverse_row_runes'&&classified[index]?.familyId==='transposition'){
    const boundary=snapshot.rules.boundaryMode;
    const mode=boundary.status==='specified'?boundary.value:null;
    operation={action:'reverse',operand:mode==='word_blocks'?'word-order':'rune-order',within:mode==='within_words'?'word':'row'};
   }
   return {query,...(operation?{operation}:{})};
  })};
 }
 function validate(input){
  if(!input||typeof input!=='object'||Array.isArray(input))failure('invalid-request','Unsupported research request.');
  for(const key of Object.keys(input)){
   if(!['version','card','originalIdea'].includes(key)||!own(Object.getOwnPropertyDescriptor(input,key),'value'))failure('invalid-request','Research request fields must be JSON data.');
  }
  if(input.version!==VERSION)failure('invalid-request','Unsupported research request.');
  if(!own(input,'card'))failure('invalid-request','A standardized card is required.');
  const original=own(input,'originalIdea')?input.originalIdea:undefined;
  if(original!==undefined&&(typeof original!=='string'||original.length>MAX_ORIGINAL))failure('original-too-long','Original idea must be at most 8,000 characters.');
  const cardText=JSON.stringify(plain(input.card));if(encoder.encode(cardText).length>H.MAX_BYTES)failure('invalid-card','The standardized card exceeds 12,000 bytes.');
  let imported;try{imported=H.decode('#idea='+base64url(cardText));}catch{failure('invalid-card','The standardized card could not be read.');}
  const source={text:original===undefined?'Standardized idea; original human wording was not supplied.':original,origin:original===undefined?'shared_link':'research_request'};
  const draft=C.createDraft({source,aim:imported.draft.aim,method:imported.draft.method,scope:imported.draft.scope,rules:imported.draft.rules,unresolved:imported.draft.unresolved});
  let snapshot;try{snapshot=C.confirm(draft,{id:'research-request-validation',at:'2000-01-01T00:00:00.000Z'});}catch{failure('needs-clarification','Resolve the consequential method ambiguity before comparison.');}
  if(!C.completeness(snapshot).researchReady)failure('needs-clarification','A meaningful method with resolved consequential questions is required.');
  const request={version:VERSION,card:JSON.parse(C.serialize(H.cardData(snapshot))),...(original!==undefined?{originalIdea:original}:{})};
  if(encoder.encode(C.serialize(request)).length>MAX_BODY)failure('body-too-long','The research request exceeds 32,000 bytes.');
  // Page selection is an exact separate hint. Repeating every ID in the
  // lexical query can make page mentions outweigh the requested technique.
  let ranking=snapshot;
  if(snapshot.scope.status==='specified'&&own(snapshot.scope.value,'pages')){
   const value={...snapshot.scope.value};delete value.pages;
   ranking=C.confirm(C.revise(snapshot,{scope:C.field('specified',value)}),{id:'research-ranking',at:'2000-01-01T00:00:00.000Z'});
  }
  const compact=C.retrievalQuery(ranking,{maxLength:MAX_QUERY});
  if(!compact.query)failure('query-too-long','The complete retrieval wording exceeds 1,500 characters.');
  const query=[compact.query,...parameterTerms(snapshot)].filter(Boolean).join('. ');
  if(query.length>MAX_QUERY)failure('query-too-long','The complete method and parameters exceed 1,500 retrieval characters.');
  const full=C.queryForResearch(snapshot,{maxLength:MAX_CONTEXT});
  if(!full.query)failure('context-too-long','The complete confirmed idea exceeds 6,000 comparison characters. Shorten the idea before comparing.');
  const confirmedQuery=full.query+'\nUnresolved constraints (not executed rules): '+C.serialize(snapshot.unresolved);
  if(confirmedQuery.length>MAX_CONTEXT)failure('context-too-long','The complete confirmed idea exceeds 6,000 comparison characters. Shorten the idea before comparing.');
  return {request,snapshot,query,confirmedQuery,pages:full.pages,discovery:discoveryHints(snapshot)};
 }
 function prepare(snapshot){
  const s=C.validateConfirmed(snapshot);
  return validate({version:VERSION,card:H.cardData(s),...(s.source.origin!=='shared_link'?{originalIdea:s.source.text}:{})});
 }
 async function binding(request,{crypto:cryptoAPI=root.crypto}={}){
  const canonical=validate(request).request;if(!cryptoAPI?.subtle?.digest)failure('hash-unavailable','Secure research binding is unavailable.');
  return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',encoder.encode(C.serialize(canonical))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 }
 const api={VERSION,MAX_ORIGINAL,MAX_QUERY,MAX_CONTEXT,MAX_BODY,prepare,validate,binding};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ClaimResearch=api;
})(typeof globalThis!=='undefined'?globalThis:this);
