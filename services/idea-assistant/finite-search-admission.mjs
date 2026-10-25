/* Admission of selected declared cases only. No AI, target execution or task writes. */
import C from '../../claim-specification.js';
import Share from '../../claim-share.js';
import Json from '../../finite-json.js';
import Settings from '../../finite-settings.js';
import Compiler from '../../fixed-plan-compiler.js';
import Policy from '../../finite-question-policy.js';
import E from '../../local-experiment.js';
import Evidence from '../../computation-evidence.js';
import Controls from '../../local-plan-controls.js';
import {parseInputBundle} from './official-inputs.mjs';
import {issue} from './prepared-plans.mjs';

export const LIMITS=Object.freeze({cases:12,selectionBytes:65536,sourceBytes:2*1024*1024,batchBytes:2*1024*1024});
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const hash=async(value,cryptoAPI)=>[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('');
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const captureCard=card=>Json.capture(card,{maxBytes:Share.MAX_BYTES,maxDepth:16,maxNodes:6000});

const checkedSettings=api=>{if(api!==Settings&&api!==Settings.factored)throw Error('Unsupported finite settings policy.');return api;};
export function compileFiniteMember(card,settings,settingsAPI=Settings,questionPolicy){
 if(questionPolicy!==undefined&&(questionPolicy!=='language-reference-comparison-v1'||settingsAPI!==Settings.factored))throw Error('Unsupported finite evaluation policy.');
 const original=captureCard(card),member=checkedSettings(settingsAPI).member(original,settings),plan=Compiler.compile(member.card);
 if(plan.reason||!Array.isArray(plan.steps))throw Error('The selected finite setting needs an execution adapter: '+(plan.reason||'unsupported program'));
 if(original.rules.inputVersion.status!=='specified'||!['raw','reviewed'].includes(original.rules.inputVersion.value)||original.rules.evaluation.status!=='specified'||(questionPolicy?Policy.describe(original.rules.evaluation.value).id!==questionPolicy:original.rules.evaluation.value?.kind!=='exact-prefix')
  ||plan.inputVersion!==original.rules.inputVersion.value||E.stable(plan.pages)!==E.stable(original.scope.value.pages)||E.stable(plan.criterion)!==E.stable(original.rules.evaluation.value))throw Error('Finite cases need the unchanged explicit text version, page scope and '+(questionPolicy?'pinned language comparison.':'opening check.'));
 return freeze({declaration:member.declaration,settings:member.settings,plan});
}

export async function prepareFiniteCases({db,proposalId,card,cases,bundle,crypto:cryptoAPI=globalThis.crypto,createdAt=new Date().toISOString(),prepareControls=Controls.prepare,settingsAPI=Settings,questionPolicy,signal}={}){
 const original=captureCard(card),selection=Json.capture(cases,{maxBytes:LIMITS.selectionBytes,maxDepth:16,maxNodes:6000}),source=parseInputBundle(Json.capture(bundle,{maxBytes:LIMITS.sourceBytes,maxDepth:16,maxNodes:6000}));
 const declaration=checkedSettings(settingsAPI).inspect(original);
 if(typeof proposalId!=='string'||proposalId!=='p_'+await hash(C.serialize(original),cryptoAPI))throw Error('The finite request does not match its original confirmed idea.');
 if(!Array.isArray(selection)||!selection.length||selection.length>LIMITS.cases||selection.some(item=>!exact(item,['settings','pageId'])||typeof item.pageId!=='string'))throw Error('Select one to twelve declared settings/page cases.');
 const seen=new Set(),compiled=new Map(),prepared=[];let inputVersion;
 for(const selected of selection){
  const key=E.stable(selected.settings);let member=compiled.get(key);if(!member){member=compileFiniteMember(original,selected.settings,settingsAPI,questionPolicy);compiled.set(key,member);}
  if(!member.plan.pages.includes(selected.pageId))throw Error('A selected page is outside the original finite question.');
  const row=source.pages.get(selected.pageId),version=member.plan.inputVersion,text=version==='raw'?row?.raw:row?.reviewed_text;
  if(typeof text!=='string')throw Error('A selected page has no text in the declared version.');
  inputVersion=version;
  const provisional=await E.prepare({title:'Declared finite settings case',pages:[{id:selected.pageId,text}],alphabet:source.alphabet,steps:member.plan.steps,criterion:member.plan.criterion},cryptoAPI),descriptor=await Evidence.describe(provisional,version,cryptoAPI),caseId=descriptor.pages[0].caseId;
  const task=await E.prepare({...provisional,title:'Finite program '+descriptor.protocolId},cryptoAPI);
  if(seen.has(caseId))throw Error('The selected finite case is repeated.');seen.add(caseId);
  prepared.push({caseId,settings:member.settings,pageId:selected.pageId,task});
 }
 // Complete validation first: a later invalid member cannot leave preparations.
 for(const item of prepared){item.controls=await prepareControls(item.task,cryptoAPI);await Controls.validate(item.controls,item.task,cryptoAPI);}
 prepared.sort((a,b)=>a.caseId.localeCompare(b.caseId));
 if(new TextEncoder().encode(E.stable(prepared)).length>LIMITS.batchBytes)throw Error('The selected cases exceed the bounded batch size. No preparations were issued.');
 for(const item of prepared){if(signal?.aborted)throw Object.assign(Error('The request was cancelled.'),{status:499});item.preparation=await issue({db,proposalId,card:original,task:item.task,inputVersion,parentTaskId:null,controls:item.controls,authority:'idea',basis:{kind:questionPolicy?'factored-output-settings':settingsAPI===Settings.factored?'factored-finite-settings':'finite-settings',settings:item.settings,caseId:item.caseId},createdAt});}
 return freeze({declaration,inputVersion,cases:prepared});
}
