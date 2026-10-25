import {loadInputBundle} from './official-inputs.mjs';
import PlanControls from '../../local-plan-controls.js';
/* Source-bound proposed plans; inference can map wording, never execute code. */
import L from '../../local-experiment.js';
import C from '../../claim-specification.js';
import {validateCard} from './idea-relations.mjs';
import {createAIPlanner} from './propose-task-plan.mjs';
// Exact ordered GP table from data/index.json; RUNES/LATIN agree with scripts/reproduce_reading.py.
const ALPHABET=[{"rune":"ᚠ","latin":"F","prime":2},{"rune":"ᚢ","latin":"U","prime":3},{"rune":"ᚦ","latin":"TH","prime":5},{"rune":"ᚩ","latin":"O","prime":7},{"rune":"ᚱ","latin":"R","prime":11},{"rune":"ᚳ","latin":"C","prime":13},{"rune":"ᚷ","latin":"G","prime":17},{"rune":"ᚹ","latin":"W","prime":19},{"rune":"ᚻ","latin":"H","prime":23},{"rune":"ᚾ","latin":"N","prime":29},{"rune":"ᛁ","latin":"I","prime":31},{"rune":"ᛄ","latin":"J","prime":37},{"rune":"ᛇ","latin":"EO","prime":41},{"rune":"ᛈ","latin":"P","prime":43},{"rune":"ᛉ","latin":"X","prime":47},{"rune":"ᛋ","latin":"S","prime":53},{"rune":"ᛏ","latin":"T","prime":59},{"rune":"ᛒ","latin":"B","prime":61},{"rune":"ᛖ","latin":"E","prime":67},{"rune":"ᛗ","latin":"M","prime":71},{"rune":"ᛚ","latin":"L","prime":73},{"rune":"ᛝ","latin":"NG","prime":79},{"rune":"ᛟ","latin":"OE","prime":83},{"rune":"ᛞ","latin":"D","prime":89},{"rune":"ᚪ","latin":"A","prime":97},{"rune":"ᚫ","latin":"AE","prime":101},{"rune":"ᚣ","latin":"Y","prime":103},{"rune":"ᛡ","latin":"IA","prime":107},{"rune":"ᛠ","latin":"EA","prime":109}];
const PURPOSE='A proposed bounded computation, not a confirmed cipher rule or a decryption verdict.';
const fail=reason=>({reason});
export function planCard(input){
 const card=validateCard(input);
 if(card.unresolved.length)return fail('The idea still has unresolved conditions.');
 if(card.method.status!=='specified'||!card.method.value.operations.length)return fail('An explicit supported method is needed.');
 if(card.scope.status!=='specified'||!Array.isArray(card.scope.value.pages)||!card.scope.value.pages.length||Object.keys(card.scope.value).some(k=>k!=='pages'))return fail('Select exact complete pages; passages and descriptive scope need an adapter.');
 const rules=card.rules,operations=card.method.value.operations,notes=[];
 if(Object.values(rules).some(rule=>rule.status==='unrestricted'))return fail('An explicitly unrestricted rule cannot be represented by one fixed experiment.');
 let inputVersion='raw',criterion={kind:'measurement'};
 const specified=k=>rules[k].status==='specified';
 const resetValue=value=>typeof value==='string'?(value.match(/^reset at each (page|line|word)$/i)?.[1].toLowerCase()||value):value;
 if(specified('inputVersion')){
  if(!['raw','reviewed'].includes(rules.inputVersion.value))return fail('The specified input version needs an adapter.');
  inputVersion=rules.inputVersion.value;
 }else notes.push('Proposed input: the archived raw transcription.');
 if(specified('representation')&&rules.representation.value!=='GP29')return fail('The specified representation needs an adapter.');
 notes.push('Use the canonical ordered 29-rune GP alphabet; preserve non-rune characters.');
 if(specified('unmapped')&&rules.unmapped.value!=='preserve')return fail('The rule for non-rune characters needs an adapter.');
 if(specified('wordBoundaries')&&rules.wordBoundaries.value!=='preserve')return fail('The word-boundary rule needs an adapter.');
 if(specified('evaluation')){
  const value=rules.evaluation.value;
  if(value==='measurement')criterion={kind:'measurement'};
  else if(value&&typeof value==='object'&&value.kind==='exact-prefix'&&Object.keys(value).length===2&&Object.hasOwn(value,'values'))criterion={kind:value.kind,values:value.values};
  else if(value&&value.kind==='word-affine-count'&&Object.keys(value).length===5&&['kind','lag','a','b','boundaries'].every(k=>Object.hasOwn(value,k))&&Number.isInteger(value.lag)&&value.lag>=1&&value.lag<=12&&[value.a,value.b].every(n=>Number.isInteger(n)&&n>=0&&n<=28)&&['non-rune','hyphen-period'].includes(value.boundaries))criterion={...value};
  else if(value&&value.kind==='word-prime-sums'&&Object.keys(value).length===3&&['kind','table','boundaries'].every(k=>Object.hasOwn(value,k))&&['canonical','reversed'].includes(value.table)&&['non-rune','hyphen-period'].includes(value.boundaries))criterion={...value};
  else return fail('The requested evaluation needs an adapter.');
 }else notes.push('Proposed evaluation: measure rune frequencies and adjacent repeats; no readability decision.');
 for(const key of ['searchBounds','searchProtocol','exceptionalCases'])if(specified(key))return fail('The specified '+key+' condition needs an adapter.');
 if(operations.some(op=>op.id==='word_prime_sums')){
  const op=operations[0],allowed=['id','label','declaredFamilyId','table','boundaries'];
  if(operations.length!==1||op.id!=='word_prime_sums'||Object.keys(op).some(k=>!allowed.includes(k))||op.label!=='Word prime sums')return fail('Word prime sums need one explicit canonical measurement operation.');
  if(Object.hasOwn(op,'declaredFamilyId')&&(typeof op.declaredFamilyId!=='string'||!Object.hasOwn(C.METHOD_FAMILIES,op.declaredFamilyId)))return fail('A declared method family must use the maintained vocabulary.');
  const expected={kind:'word-prime-sums',table:op.table,boundaries:op.boundaries};
  if(criterion.kind!=='word-prime-sums'||L.stable(criterion)!==L.stable(expected))return fail('The prime-table and boundary settings must match the explicit evaluation.');
  if(['boundaryMode','reset','initialState'].some(specified)||rules.wordBoundaries.status==='not_applicable')return fail('The word-sum boundary conflicts with another supplied rule.');
  notes.push('Add the authorized GP prime value of every rune in each declared word. Reversed means reverse the prime assignments across the same ordered alphabet; it does not reverse digits or rune order. Non-rune characters are not assigned numbers. Pages remain separate.');
  return {pages:card.scope.value.pages,steps:[],inputVersion,criterion,notes};
 }
 if(criterion.kind==='word-prime-sums')return fail('The evaluation needs the matching word-prime-sum measurement operation.');
 if(operations.some(op=>op.id==='word_affine_count')){
  const op=operations[0],allowed=['id','label','declaredFamilyId','lag','a','b','boundaries'];
  if(operations.length!==1||op.id!=='word_affine_count'||Object.keys(op).some(k=>!allowed.includes(k))||op.label!==undefined&&op.label!=='Within-word affine pair count')return fail('The within-word count needs one explicit measurement operation.');
  const expected={kind:'word-affine-count',lag:op.lag,a:op.a,b:op.b,boundaries:op.boundaries};
  if(criterion.kind!=='word-affine-count'||L.stable(criterion)!==L.stable(expected))return fail('The measurement parameters and explicit evaluation must agree.');
  if(['boundaryMode','reset','initialState'].some(specified)||rules.wordBoundaries.status==='not_applicable')return fail('The measurement boundary conflicts with another supplied rule.');
  notes.push('Count only pairs within each page and declared word boundary. Compare with the exact average under uniformly shuffled rune order inside each word; this is not a tail probability or a correction for choosing a formula.');
  return {pages:card.scope.value.pages,steps:[],inputVersion,criterion,notes};
 }
 if(criterion.kind==='word-affine-count')return fail('The evaluation needs the matching within-word measurement operation.');
 const steps=[];let reverse=false,cumulative=false,keyed=false;
 const keyedModes={vigenere:'repeat',repeating_key:'repeat',plaintext_autokey:'plaintext-autokey',ciphertext_autokey:'ciphertext-autokey'};
 for(const operation of operations){
  const labels={reverse_row_runes:['Reverse rune order within rows','Reverse rune order within each row'],reverse_runes:['Reverse rune order within each line','Reverse rune order within each word','Reverse rune order within each page'],affine:['Affine','Affine substitution'],cumulative_difference:['Cumulative difference'],vigenere:['Vigenere','Vigenère'],repeating_key:['Repeating key','Repeating-key','Vigenere','Vigenère'],plaintext_autokey:['Plaintext autokey','Plaintext-autokey'],ciphertext_autokey:['Ciphertext autokey','Ciphertext-autokey'],finite_key:['Finite key stream'],interrupted_repeating_key:['Interrupted repeating key']};
  if(Object.hasOwn(operation,'label')&&(!labels[operation.id]||!labels[operation.id].includes(operation.label)))return fail('The operation wording contains details that need an execution adapter.');
  if(Object.keys(operation).some(k=>!['id','label','a','b','reset','unit','declaredFamilyId','key','direction','interrupts'].includes(k)))return fail('An operation contains parameters the runner cannot represent.');
  if(operation.id!=='interrupted_repeating_key'&&Object.hasOwn(operation,'interrupts'))return fail('Only an interrupted repeating key accepts literal interrupter indices.');
  if(operation.id!=='finite_key'&&operation.id!=='interrupted_repeating_key'&&!Object.hasOwn(keyedModes,operation.id)&&['key','direction'].some(k=>Object.hasOwn(operation,k)))return fail('This operation does not accept key parameters.');
  if(operation.id!=='reverse_runes'&&Object.hasOwn(operation,'unit'))return fail('This operation does not accept a reversal unit.');
  if(operation.id==='reverse_row_runes'){
   if(Object.keys(operation).some(k=>['a','b','reset'].includes(k)))return fail('The reversal has unsupported parameters.');
   reverse=true;
   if(specified('boundaryMode')&&!['fixed_spaces','within_words'].includes(rules.boundaryMode.value))return fail('This word-order rule needs a different reversal adapter.');
   if(specified('wordBoundaries')&&!specified('boundaryMode'))return fail('Choose how the reversal handles the preserved word boundaries.');
   steps.push({op:'reverse',unit:specified('boundaryMode')&&rules.boundaryMode.value==='within_words'?'word':'line'});
  }else if(operation.id==='reverse_runes'){
   if(!['line','word','page'].includes(operation.unit)||['a','b','reset'].some(k=>Object.hasOwn(operation,k)))return fail('A reversal needs an explicit line, word or page boundary.');
   if(operation.label!==undefined&&operation.label!=='Reverse rune order within each '+operation.unit)return fail('The reversal label conflicts with its boundary.');
   if(specified('boundaryMode')&&rules.boundaryMode.value!==(operation.unit==='word'?'within_words':'fixed_spaces'))return fail('The global boundary rule conflicts with a reversal step.');
   if(operation.unit==='page'&&specified('boundaryMode'))return fail('The global row boundary rule conflicts with a whole-page reversal.');
   reverse=true;steps.push({op:'reverse',unit:operation.unit});
  }else if(operation.id==='affine'){
   if(Object.hasOwn(operation,'reset')||!Number.isInteger(operation.a)||operation.a<0||operation.a>28||!Number.isInteger(operation.b)||operation.b<0||operation.b>28)return fail('An affine step needs explicit a and b indices from 0 to 28.');
   steps.push({op:'affine',a:operation.a,b:operation.b});
  }else if(operation.id==='cumulative_difference'){
   if(Object.hasOwn(operation,'a')||Object.hasOwn(operation,'b')||!['page','line','word'].includes(operation.reset))return fail('Cumulative difference needs an explicit page, line or word reset.');
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   if(rules.initialState.status==='not_applicable')return fail('Cumulative difference requires an initial state, which is marked not applicable.');
   if(specified('initialState')&&rules.initialState.value!==0)return fail('Only initial state zero is supported.');
   cumulative=true;steps.push({op:'cumulative-difference',reset:operation.reset});
  }else if(operation.id==='interrupted_repeating_key'){
   if(operation.label!=='Interrupted repeating key')return fail('An interrupted repeating key needs its exact canonical label.');
   if(['a','b','unit'].some(k=>Object.hasOwn(operation,k))||!Array.isArray(operation.key)||!operation.key.length||operation.key.length>256||operation.key.some(n=>!Number.isInteger(n)||n<0||n>28)||!['subtract','add'].includes(operation.direction)||!['page','line','word'].includes(operation.reset)||!Array.isArray(operation.interrupts)||!operation.interrupts.length||operation.interrupts.length>29||operation.interrupts.some((n,i)=>!Number.isInteger(n)||n<0||n>28||i>0&&n<=operation.interrupts[i-1]))return fail('An interrupted repeating key needs explicit GP key indices (0–28), add or subtract, a page, line or word reset, and sorted unique literal interrupter indices (0–28).');
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   keyed=true;steps.push({op:'interrupted-keyed-shift',key:[...operation.key],direction:operation.direction,reset:operation.reset,interrupts:[...operation.interrupts]});
  }else if(operation.id==='finite_key'||Object.hasOwn(keyedModes,operation.id)){
   if(['a','b','unit'].some(k=>Object.hasOwn(operation,k))||!Array.isArray(operation.key)||!operation.key.length||operation.key.length>(operation.id==='finite_key'?20000:256)||operation.key.some(n=>!Number.isInteger(n)||n<0||n>28)||!['subtract','add'].includes(operation.direction)||!['page','line','word'].includes(operation.reset))return fail('A keyed step needs explicit GP indices (0–28), add or subtract, and a page, line or word reset.');
   if(rules.reset.status==='not_applicable')return fail('An explicit reset conflicts with reset being marked not applicable.');
   if(specified('reset')&&resetValue(rules.reset.value)!==operation.reset)return fail('The global reset conflicts with an operation reset.');
   keyed=true;steps.push(operation.id==='finite_key'?{op:'finite-shift',key:[...operation.key],direction:operation.direction,reset:operation.reset}:{op:'keyed-shift',key:[...operation.key],mode:keyedModes[operation.id],direction:operation.direction,reset:operation.reset});
  }else return fail('This method needs an execution adapter before a faithful local plan can be prepared.');
 }
 if(specified('boundaryMode')&&!reverse)return fail('The boundary-mode condition is not represented by these steps.');
 if(specified('initialState')&&!cumulative)return fail('The initial-state condition is not represented by these steps.');
 if(specified('reset')&&!cumulative&&!keyed)return fail('The reset or initial-state condition is not represented by these steps.');
 if(steps.some(s=>s.op==='reverse'))notes.push('Reversal changes rune positions only, leaving separators in place; a word ends at any non-rune character.');
 if(keyed)notes.push('Key values are explicit GP alphabet indices, not prime values or guessed letters; non-rune characters do not consume the key. Each specified boundary restarts the key and autokey history.');
 if(steps.some(s=>s.op==='interrupted-keyed-shift'))notes.push('Literal interrupter indices are tested against the current step input, copied unchanged, and do not advance the repeating key. Other runes consume one key value. Each declared reset starts at the first key value; there is no autokey feedback.');
 if(steps.some(s=>s.op==='finite-shift'))notes.push('Finite key streams never wrap or extend themselves. The supplied key must cover every complete segment before the task can be prepared.');
 if(cumulative)notes.push('Cumulative difference starts at zero at each specified boundary; pages never share state.');
 notes.push('Each page is processed separately, in the stated method-step order; headings are included.');
 if(card.outcome.status==='specified'&&card.outcome.value.outcomeId==='decipher')notes.push('This is a preliminary measurement for the deciphering idea, not a test of whether the output is readable.');
 return {pages:card.scope.value.pages,steps,inputVersion,criterion,notes};
}
const proposePlan=createAIPlanner({compile:planCard});
async function jsonBody(message,max){
 if(!/^application\/json(?:\s*;|$)/i.test(message.headers.get('content-type')||''))throw Error();
 const declared=message.headers.get('content-length');if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>max))throw Error();
 const reader=message.body?.getReader();if(!reader)throw Error();const chunks=[];let size=0;
 while(true){const r=await reader.read();if(r.done)break;size+=r.value.length;if(size>max){await reader.cancel();throw Error();}chunks.push(r.value);}
 const bytes=new Uint8Array(size);let i=0;for(const chunk of chunks){bytes.set(chunk,i);i+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
export function createPrepareTaskHandler({fetcher=globalThis.fetch,now=()=>new Date(),prepareControls=PlanControls.prepare}={}){
 return async function handle(request,env){
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
  let allowed=false;try{allowed=typeof env?.SITE_ORIGIN==='string'&&new URL(env.SITE_ORIGIN).origin===env.SITE_ORIGIN&&['http:','https:'].includes(new URL(env.SITE_ORIGIN).protocol);}catch{}
  if(!allowed)return reply({error:'Plan preparation is unavailable.'},503);
  if(request.headers.get('origin')!==env.SITE_ORIGIN)return reply({error:'Request is not allowed.'},403);
  headers['Access-Control-Allow-Origin']=env.SITE_ORIGIN;
  if(new URL(request.url).pathname!=='/prepare-task')return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){
   const fields=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);
   if(request.headers.get('access-control-request-method')!=='POST'||fields.some(v=>v!=='content-type'))return reply({error:'Request is not allowed.'},403);
   return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});
  }
  if(request.method!=='POST')return reply({error:'Method is not allowed.'},405);
  if(!env.PROPOSALS?.prepare||!(env.TASK_LIMIT||env.PROPOSAL_LIMIT)?.limit)return reply({error:'Plan preparation is unavailable.'},503);
  let body;try{body=await jsonBody(request,32000);if(!body||typeof body!=='object'||Array.isArray(body)||Object.keys(body).length!==2||!Object.hasOwn(body,'proposalId')||!Object.hasOwn(body,'parentTaskId')||!/^p_[a-f0-9]{64}$/.test(body.proposalId)||(body.parentTaskId!==null&&!/^[a-f0-9]{64}$/.test(body.parentTaskId)))throw Error();}catch{return reply({error:'The plan request could not be read.'},400);}
  try{
   if(!(await (env.TASK_LIMIT||env.PROPOSAL_LIMIT).limit({key:request.headers.get('CF-Connecting-IP')||'unknown'}))?.success)return reply({error:'Please wait before trying again.'},429);
   const query=(sql,...args)=>env.PROPOSALS.prepare(sql).bind(...args).first();
   const row=await query('SELECT card_json FROM proposals WHERE id=?',body.proposalId);if(!row)return reply({error:'Confirmed idea not found.'},404);
   if(body.parentTaskId&&!await query('SELECT id FROM local_tasks WHERE id=?',body.parentTaskId))return reply({error:'Parent task not found.'},404);
   const card=validateCard(row.card_json);let plan=planCard(card),interpretationNotes=[];
   if(plan.reason){
    if(card.method.value?.operations?.some(op=>op.id==='word_prime_sums')||card.rules.evaluation.value?.kind==='word-prime-sums')return reply({state:'needs-adapter',reason:plan.reason,proposalId:body.proposalId});
    const mapped=await proposePlan(card,env);
    if(!mapped.reason){plan=mapped.plan;interpretationNotes=mapped.notes;}
    else return reply({state:'needs-adapter',reason:mapped.reason,proposalId:body.proposalId});
   }
   if(plan.reason)return reply({state:'needs-adapter',reason:plan.reason,proposalId:body.proposalId});
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);const pages=Array(plan.pages.length);let next=0,totalBytes=0;
   try{
    const bundle=plan.pages.length>40?await loadInputBundle({fetcher,signal:controller.signal,read:jsonBody}):null;if(bundle&&L.stable(bundle.alphabet)!==L.stable(ALPHABET))throw Error();
    const worker=async()=>{try{while(next<plan.pages.length){if(controller.signal.aborted)throw Error();const index=next++,id=plan.pages[index];const response=bundle?null:await fetcher('https://jelliottdev.github.io/data/pages/'+id+'.json',{redirect:'manual',signal:controller.signal});if(response&&!response.ok)throw Error();const page=bundle?bundle.pages.get(id):await jsonBody(response,512*1024),text=plan.inputVersion==='raw'?page.raw:page.reviewed_text;if(page.id!==id||typeof text!=='string')throw Error();totalBytes+=new TextEncoder().encode(text).length;if(totalBytes>2000000)throw Error();pages[index]={id,text};}}catch(error){controller.abort();throw error;}};
    await Promise.all(Array.from({length:Math.min(4,pages.length)},()=>worker()));
   }catch(error){console.warn('prepare-task: official manuscript source unavailable',error?.name||'Error',error?.message||'');return reply({error:'The selected manuscript text could not be loaded.'},422);}finally{clearTimeout(timer);}
   const title=plan.criterion.kind==='word-prime-sums'?'Word prime sums · '+plan.criterion.table+' table · '+plan.criterion.boundaries:plan.criterion.kind==='word-affine-count'?'Within-word rune pairs · lag '+plan.criterion.lag+' · '+plan.criterion.boundaries:plan.steps.map(s=>s.op==='reverse'?'Reverse rune order within each '+s.unit:s.op==='affine'?'Affine mapping ('+s.a+', '+s.b+')':s.op==='finite-shift'?'Finite key stream '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+' indices · '+s.reset+' resets':s.op==='interrupted-keyed-shift'?'Interrupted repeating-key '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+'-rune key · '+s.reset+' resets':s.op==='keyed-shift'?(s.mode==='repeat'?'Repeating-key':s.mode==='plaintext-autokey'?'Plaintext autokey':'Ciphertext autokey')+' '+(s.direction==='subtract'?'subtraction':'addition')+' · '+s.key.length+'-rune '+(s.mode==='repeat'?'key':'seed')+' · '+s.reset+' resets':'Cumulative difference with '+s.reset+' resets').join(', then ').slice(0,300);
   let task;try{task=await L.prepare({title,pages,alphabet:ALPHABET,steps:plan.steps,criterion:plan.criterion});}catch(error){return reply({state:'needs-adapter',reason:String(error?.message||'').startsWith('The finite key stream is shorter')?'The supplied finite stream is too short for a complete page segment. Supply enough values or specify a different reset.':'The explicit plan exceeds the supported runner bounds or criterion.',proposalId:body.proposalId});}
   let controls;
   try{controls=await prepareControls(task,crypto);await PlanControls.validate(controls,task,crypto);}
   catch{return reply({error:'The runner checks failed. No experiment was created.'},422);}
   return reply({state:'plan-ready',proposalId:body.proposalId,parentTaskId:body.parentTaskId,inputVersion:plan.inputVersion,task,controls,notes:[...interpretationNotes,...plan.notes],purpose:PURPOSE});
  }catch{return reply({error:'Plan preparation is temporarily unavailable.'},503);}
 };
}
