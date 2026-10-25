/* Explicit choices complete one literal-key method; this module never confirms or saves. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare;
 const sessions=new WeakSet(),clone=v=>JSON.parse(C.serialize(v));
 const modeLabel=id=>({repeating_key:'Repeating key',vigenere:'Vigenère',plaintext_autokey:'Plaintext autokey',ciphertext_autokey:'Ciphertext autokey'}[id]||'Keyed method');
 // In the browser the shared compiler may be loaded later in the deferred
 // script list; resolve it when a reviewed choice is actually requested.
 const compiler=()=>node?require('./fixed-plan-compiler.js'):root.FixedPlanCompiler;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const active=f=>f.status==='specified'?{status:f.status,value:clone(f.value)}:{status:f.status};
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 function draftCard(draft){const outcome=active(draft.aim);if(outcome.status==='specified'){const value=C.normalizeOutcome(draft.aim);outcome.value={outcomeId:value.id,detail:value.detail};}return {version:1,outcome,method:active(draft.method),scope:active(draft.scope),rules:Object.fromEntries(C.RULES.map(key=>[key,active(draft.rules[key])])),unresolved:clone(draft.unresolved)};}
 function decode(card){
  const original=clone(card);let binary='';for(const b of new TextEncoder().encode(JSON.stringify(original)))binary+=String.fromCharCode(b);
  const draft=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft;
  if(C.serialize(original)!==C.serialize(draftCard(draft)))throw Error('The original idea is not canonical.');return {card:original,draft};
 }
 function descriptor(draft){
  const card=draftCard(draft),engine=compiler();if(!engine?.compile)throw Error('The maintained method compiler is unavailable.');
  const result=engine.compile(card);
  if(result.state==='needs-clarification'&&result.field==='method'&&result.clarification?.kind==='keyed-operation')return clone(result.clarification);
  if(!result.reason&&Array.isArray(result.steps))return null;
  throw Error('This idea does not have one supported literal-key choice.');
 }
 function question(draft){const value=descriptor(draft);return value?{...value,prompt:value.parameter==='direction'?(draft.method.value.operations.length===1?'How should the key indices be combined with the page?':'How should the key indices in step '+(value.operationIndex+1)+' be combined with the page?'):(draft.method.value.operations.length===1?'When should the key restart?':'When should the key in step '+(value.operationIndex+1)+' restart?')}:null;}
 function branded(value){freeze(value);sessions.add(value);return value;}
 async function verify(card,response,cryptoAPI=root.crypto){
  const captured=decode(card),reply=clone(response),expected=descriptor(captured.draft);
  if(!expected||!exact(reply,['state','proposalId','field','reason','clarification'])||reply.state!=='needs-clarification'||reply.field!=='method'||typeof reply.reason!=='string'||!reply.reason.trim()||reply.reason.length>700||C.serialize(reply.clarification)!==C.serialize(expected))throw Error('The method choice does not match this exact idea.');
  const hash=[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(captured.card))))].map(n=>n.toString(16).padStart(2,'0')).join(''),proposalId='p_'+hash;
  if(reply.proposalId!==proposalId)throw Error('The method choice belongs to another saved idea.');
  return branded({proposalId,card:captured.card,draft:captured.draft,question:question(captured.draft),choices:[]});
 }
 function inspect(session){if(!session||!sessions.has(session))throw Error('This method choice has not been verified.');return session;}
 function choose(session,value){
  inspect(session);const q=session.question,selected=q?.choices.find(choice=>choice.value===value);if(!selected)throw Error('Choose one of the offered method settings.');
  const before=clone(session.draft.method.value.operations[q.operationIndex]);if(Object.hasOwn(before,q.parameter))throw Error('A supplied method setting cannot be replaced.');const after={...before,[q.parameter]:selected.value};
  const refs=[...new Set([...session.draft.method.provenance.refs,'method:operation:'+q.operationIndex,'keyed-operation-v1:'+q.parameter,'proposal:'+session.proposalId])],operations=clone(session.draft.method.value.operations);operations[q.operationIndex]=after;const draft=C.revise(session.draft,{method:C.field('specified',{...clone(session.draft.method.value),operations},{kind:'user_clarification',refs})});
  draft.clarifications.push({question:'keyed-operation:'+q.operationIndex+':'+q.parameter,choice:selected.value,revision:draft.revision});
  const receipt={...(session.card.method.value.operations.length>1?{operationIndex:q.operationIndex}:{}),parameter:q.parameter,value:selected.value,label:selected.label,before,after:clone(after)},choices=[...clone(session.choices),receipt];
  return branded({proposalId:session.proposalId,card:clone(session.card),draft,question:question(draft),choices});
 }
 const api={verify,choose,inspect,modeLabel};if(node)module.exports=api;else root.KeyedMethodClarification=api;
})(typeof globalThis!=='undefined'?globalThis:this);
