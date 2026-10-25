/* Explicitly reviewed affine search proposal. No inference, persistence or execution. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,JSONData=node?require('./finite-json.js'):root.FiniteJSON,Settings=node?require('./finite-settings.js'):root.FiniteSettings,Compiler=node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler;
 const sessions=new WeakMap(),clone=v=>JSONData.capture(v,{maxBytes:H.MAX_BYTES,maxDepth:16,maxNodes:6000});
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const active=f=>f.status==='specified'?{status:f.status,value:clone(f.value)}:{status:f.status};
 function draftCard(draft){const outcome=active(draft.aim);if(outcome.status==='specified'){const v=C.normalizeOutcome(draft.aim);outcome.value={outcomeId:v.id,detail:v.detail};}return {version:1,outcome,method:active(draft.method),scope:active(draft.scope),rules:Object.fromEntries(C.RULES.map(k=>[k,active(draft.rules[k])])),unresolved:clone(draft.unresolved)};}
 function decode(input){const card=clone(input);let binary='';for(const b of new TextEncoder().encode(JSON.stringify(card)))binary+=String.fromCharCode(b);const draft=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft;if(C.serialize(card)!==C.serialize(draftCard(draft)))throw Error('The original idea is not canonical.');return {card,draft};}
 // Deliberately narrow positive wording. A generic inverse, a negation, an
 // extra condition or an unknown cipher is never silently replaced by affine.
 const intent=/^(?:(?:try|test|check|enumerate|apply|search(?: over)?)\s+)?all(?:\s+the)?\s+(?:invertible|bijective)\s+affine(?:\s+(?:settings|maps|mappings|transformations|substitutions|ciphers))?(?:\s+(?:mod(?:ulo)?\s*29|over\s+GP29))?[.!]?$/i;
 function retainedIntent(wording,scope){
  if(intent.test(wording))return true;
  // A method quote may also contain its exact page list. Accept that tail only
  // when independently represented by the unchanged canonical scope.
  const match=wording.match(/^([\s\S]+?)\s+(?:on|across|for)\s+(LP[12]-\d{1,2}(?:\s*(?:,|and)\s*LP[12]-\d{1,2})*)[.!]?$/i);
  if(!match||!intent.test(match[1])||scope.status!=='specified'||!exact(scope.value,['pages'])||!Array.isArray(scope.value.pages))return false;
  const pages=[...match[2].matchAll(/lp([12])-(\d{1,2})/gi)].map(m=>'lp'+m[1]+'-'+m[2].padStart(2,'0'));
  return new Set(pages).size===pages.length&&C.serialize(pages.slice().sort())===C.serialize(scope.value.pages.slice().sort());
 }
 function target(card){
  if(card.method.status!=='specified'||!Array.isArray(card.method.value.operations)||card.rules.searchBounds.status==='specified'||card.rules.searchBounds.status==='unrestricted')return null;
  const found=[];
  card.method.value.operations.forEach((op,index)=>{
   if(op.id==='affine'){
    if(Object.keys(op).some(k=>!['id','label','declaredFamilyId','a','b'].includes(k))||Object.hasOwn(op,'label')&&!['Affine','Affine substitution'].includes(op.label))return;
    if(['a','b'].some(k=>Object.hasOwn(op,k)&&(!Number.isInteger(op[k])||op[k]<0||op[k]>28))||op.a===0||Object.hasOwn(op,'a')&&Object.hasOwn(op,'b'))return;
    found.push({index,op});
   }else if(op.id==='described_method'){
    if(Object.keys(op).some(k=>!['id','label','sourceText','provenance','declaredFamilyId'].includes(k)))return;
    const wording=typeof op.sourceText==='string'?op.sourceText:op.label;
    if(typeof wording==='string'&&retainedIntent(wording.trim(),card.scope)&&(!op.sourceText||!op.label||op.label===op.sourceText))found.push({index,op});
   }
  });
  return found.length===1?found[0]:null;
 }
 function axes(t){return ['a','b'].filter(name=>!Object.hasOwn(t.op,name)).map(name=>({operation:t.index,name,values:Array.from({length:name==='a'?28:29},(_,i)=>name==='a'?i+1:i)}));}
 function descriptor(card){const t=target(card);if(!t)return null;const parameters=axes(t);return {version:1,kind:'affine-search',operationIndex:t.index,operationId:'affine',parameter:'convention',definition:{modulus:29,form:'a*x+b',parameters},choices:[{id:'gp29-invertible',value:'gp29-invertible',label:'Use c′ = a·c + b modulo 29; try every missing invertible multiplier and offset'}]};}
 function describe(card){return freeze(descriptor(decode(card).card));}
 const hash=async(v,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');
 function status(draft,confirmed,factored=false){
  const policy=factored?Settings.factored:Settings;
  const proposedCard=draftCard(draft);
  if(!confirmed)return {proposedCard:null,state:'needs-choice',question:{...descriptor(proposedCard),prompt:'Which affine convention and settings should this check?'}};
  if(draft.rules.inputVersion.status==='unspecified')return {proposedCard,state:'needs-choice',question:{version:1,kind:'affine-search',parameter:'inputVersion',prompt:'Which text edition should these settings use?',choices:[{id:'raw',value:'raw',label:'Archived rune text'},{id:'reviewed',value:'reviewed',label:'Reviewed derivative text'}]}};
  if(draft.rules.inputVersion.status!=='specified'||!['raw','reviewed'].includes(draft.rules.inputVersion.value))return {proposedCard,state:'unsupported',question:null,reason:'The supplied source-edition rule is not supported; it was retained.'};
  if(draft.scope.status!=='specified'||!exact(draft.scope.value,['pages'])||!Array.isArray(draft.scope.value.pages)||!draft.scope.value.pages.length)return {proposedCard,state:'needs-scope',question:null,reason:'Choose exact complete pages through the scope review. The original selection was retained.'};
  const parameters=draft.rules.searchBounds.value.parameters,programCount=parameters.reduce((n,p)=>n*p.values.length,1),caseCount=programCount*draft.scope.value.pages.length;
  if(caseCount>policy.LIMITS.cases)return {proposedCard,state:'needs-scope',question:null,programCount,caseCount,maximumPages:Math.floor(policy.LIMITS.cases/programCount),reason:'The requested page/settings domain exceeds the supported case budget. No pages or settings were omitted.'};
  if(draft.rules.evaluation.status==='unspecified')return {proposedCard,state:'needs-evaluation',question:null,programCount,caseCount,reason:'Choose the exact opening through the evaluation review; no opening was supplied.'};
  if(draft.rules.evaluation.status!=='specified'||draft.rules.evaluation.value?.kind!=='exact-prefix')return {proposedCard,state:'unsupported',question:null,programCount,caseCount,reason:'This finite search currently checks an exact supplied opening. The requested evaluation was retained, not replaced.'};
  try{
   const declaration=policy.inspect(proposedCard),first=parameters.map(axis=>({operation:axis.operation,name:axis.name,value:axis.values[0]})),member=policy.member(proposedCard,first),plan=Compiler.compile(member.card);
   if(plan.reason||!Array.isArray(plan.steps))return {proposedCard,state:'unsupported',question:null,programCount,caseCount,reason:plan.reason||'Another supplied condition needs an adapter.'};
   return {proposedCard,state:'ready',question:null,declaration,programCount,caseCount};
  }catch(error){return {proposedCard,state:'unsupported',question:null,programCount,caseCount,reason:error.message};}
 }
 function branded(v,factored=false){freeze(v);sessions.set(v,factored);return v;}
 async function verify(card,response,cryptoAPI=root.crypto,options={}){
  const capability=clone(options);if(Object.keys(capability).some(k=>k!=='factored')||Object.hasOwn(capability,'factored')&&typeof capability.factored!=='boolean')throw Error('Use the maintained local finite-search capability.');const factored=capability.factored===true;
  const original=decode(card),reply=clone(response),expected=descriptor(original.card);
  if(!expected||!exact(reply,['state','proposalId','field','reason','clarification'])||reply.state!=='needs-clarification'||reply.field!=='method'||typeof reply.reason!=='string'||!reply.reason.trim()||reply.reason.length>700||C.serialize(reply.clarification)!==C.serialize(expected))throw Error('The affine choice does not match this exact idea.');
  const proposalId='p_'+await hash(original.card,cryptoAPI);if(reply.proposalId!==proposalId)throw Error('The affine choice belongs to another saved idea.');
  return branded({proposalId,card:original.card,draft:original.draft,choices:[],...status(original.draft,false,factored)},factored);
 }
 function inspect(session){if(!sessions.has(session))throw Error('This affine choice has not been verified.');return session;}
 function choose(session,value){
  inspect(session);const factored=sessions.get(session),q=session.question,choice=q?.choices.find(c=>c.value===value);if(!choice)throw Error('Choose one of the offered affine settings.');
  let draft;const refs=['proposal:'+session.proposalId,'affine-search-v1:'+q.parameter],receipt={parameter:q.parameter,value,label:choice.label};
  if(q.parameter==='convention'){
   const t=target(session.card),operations=clone(session.draft.method.value.operations),before=clone(operations[t.index]),after={id:'affine',label:'Affine substitution',...(Object.hasOwn(before,'declaredFamilyId')?{declaredFamilyId:before.declaredFamilyId}:{}),...Object.fromEntries(['a','b'].filter(k=>Object.hasOwn(before,k)).map(k=>[k,before[k]]))};
   operations[t.index]=after;receipt.before=before;receipt.after=clone(after);
   draft=C.revise(session.draft,{method:C.field('specified',{operations},{kind:'user_clarification',refs:[...refs,'method:operation:'+t.index]}),rules:{searchBounds:C.field('specified',{kind:'finite-settings',version:1,parameters:axes(t)},{kind:'user_clarification',refs})}});
  }else if(q.parameter==='inputVersion'){
   if(session.draft.rules.inputVersion.status!=='unspecified')throw Error('A supplied edition cannot be replaced.');
   draft=C.revise(session.draft,{rules:{inputVersion:C.field('specified',value,{kind:'user_clarification',refs})}});
  }else throw Error('Unsupported affine choice');
  draft.clarifications.push({question:'affine-search:'+q.parameter,choice:value,revision:draft.revision});
  return branded({proposalId:session.proposalId,card:clone(session.card),draft,choices:[...clone(session.choices),receipt],...status(draft,true,factored)},factored);
 }
 const api={describe,verify,choose,inspect};if(node)module.exports=api;else root.AffineSearchClarification=api;
})(typeof globalThis!=='undefined'?globalThis:this);
