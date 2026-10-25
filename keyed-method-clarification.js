/* Explicit choices complete one literal-key method; this module never confirms or saves. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare,P=node?require('./experiment-protocols.js'):root.ExperimentProtocols,Evaluators=node?require('./output-evaluators.js'):root.OutputEvaluators;
 const sessions=new WeakSet(),clone=v=>JSON.parse(C.serialize(v));
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
  const card=draftCard(draft),rules=card.rules,operations=card.method.value?.operations;
  if(card.unresolved.length||card.method.status!=='specified'||!Array.isArray(operations)||operations.length!==1||card.scope.status!=='specified'||!exact(card.scope.value,['pages'])||!Array.isArray(card.scope.value.pages)||!card.scope.value.pages.length||Object.values(rules).some(rule=>rule.status==='unrestricted'))throw Error('This idea does not have one supported literal-key choice.');
  const op=operations[0];if(op.id!=='repeating_key'||Object.keys(op).some(k=>!['id','label','key','direction','reset'].includes(k))||Object.hasOwn(op,'label')&&!['Repeating key','Repeating-key','Vigenere','Vigenère'].includes(op.label)||!Array.isArray(op.key)||!op.key.length||op.key.length>256||op.key.some(n=>!Number.isInteger(n)||n<0||n>28))throw Error('A complete literal repeating key is required.');
  const specified=k=>rules[k].status==='specified',value=rules.evaluation.value;
  const prefix=exact(value,['kind','values'])&&value.kind==='exact-prefix'&&Array.isArray(value.values)&&value.values.length>0&&value.values.length<=256&&value.values.every(n=>Number.isInteger(n)&&n>=0&&n<=28);
  if(C.normalizeOutcome(card.outcome).id==='decipher'&&!specified('evaluation')||specified('evaluation')&&value!=='measurement'&&!prefix&&!Evaluators?.identify(value)||specified('evaluation')&&P?.identify(value))throw Error('The evaluation does not support this literal-key operation.');
  if(specified('inputVersion')&&!['raw','reviewed'].includes(rules.inputVersion.value)||specified('representation')&&rules.representation.value!=='GP29'||specified('unmapped')&&rules.unmapped.value!=='preserve'||specified('wordBoundaries')&&rules.wordBoundaries.value!=='preserve'||['boundaryMode','initialState','searchBounds','searchProtocol','exceptionalCases'].some(specified)||rules.reset.status==='not_applicable')throw Error('Another condition conflicts with this supported choice.');
  const globalReset=typeof rules.reset.value==='string'?(rules.reset.value.match(/^reset at each (page|line|word)$/i)?.[1].toLowerCase()||rules.reset.value):rules.reset.value;
  if(specified('reset')&&(!Object.hasOwn(op,'reset')||globalReset!==op.reset)||Object.hasOwn(op,'direction')&&!['subtract','add'].includes(op.direction)||Object.hasOwn(op,'reset')&&!['page','line','word'].includes(op.reset))throw Error('Supplied arithmetic or restart settings cannot be replaced.');
  const parameter=['direction','reset'].find(key=>!Object.hasOwn(op,key));if(!parameter)return null;
  const choices=parameter==='direction'?[{id:'subtract',value:'subtract',label:'Subtract key indices'},{id:'add',value:'add',label:'Add key indices'}]:['page','line','word'].map(value=>({id:value,value,label:'Restart the key at each '+value}));
  return {version:1,kind:'keyed-operation',operationIndex:0,operationId:'repeating_key',parameter,choices};
 }
 function question(draft){const value=descriptor(draft);return value?{...value,prompt:value.parameter==='direction'?'How should the key indices be combined with the page?':'When should the key restart?'}:null;}
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
  const before=clone(session.draft.method.value.operations[0]);if(Object.hasOwn(before,q.parameter))throw Error('A supplied method setting cannot be replaced.');const after={...before,[q.parameter]:selected.value};
  const refs=[...new Set([...session.draft.method.provenance.refs,'method:operation:0','keyed-operation-v1:'+q.parameter,'proposal:'+session.proposalId])],draft=C.revise(session.draft,{method:C.field('specified',{operations:[after]},{kind:'user_clarification',refs})});
  draft.clarifications.push({question:'keyed-operation:0:'+q.parameter,choice:selected.value,revision:draft.revision});
  const receipt={parameter:q.parameter,value:selected.value,label:selected.label,before,after:clone(after)},choices=[...clone(session.choices),receipt];
  return branded({proposalId:session.proposalId,card:clone(session.card),draft,question:question(draft),choices});
 }
 const api={verify,choose,inspect};if(node)module.exports=api;else root.KeyedMethodClarification=api;
})(typeof globalThis!=='undefined'?globalThis:this);
