/* Literal cumulative plaintext sums only. No generic autokey inference or execution. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,J=node?require('./finite-json.js'):root.FiniteJSON;
 const own=(v,k)=>Object.hasOwn(v,k),capture=v=>J.capture(v,{maxBytes:160000,maxDepth:24,maxNodes:16000}),same=(a,b)=>C.serialize(a)===C.serialize(b);
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function pages(text){const result=[];for(const part of text.split(/\s*(?:,|;|\band\b)\s*/i)){const m=part.match(/^LP([12])-(\d{1,2})(?:\s*[-\u2013\u2014]\s*(?:LP\1-)?(\d{1,2}))?$/i);if(!m)return null;const first=+m[2],last=m[3]===undefined?first:+m[3];if(last<first||last>(m[1]==='1'?16:57))return null;for(let n=first;n<=last;n++)result.push('lp'+m[1]+'-'+String(n).padStart(2,'0'));}try{return result.length&&new Set(result).size===result.length?C.pages(result):null;}catch{return null;}}
 function parse(text){
  if(typeof text!=='string'||!text.trim()||text.length>1600||/[`{}\r\n]/.test(text))return null;
  let phrase=text.trim().replace(/[.!?]$/,'').trim(),scopePages=null,reset=null,initial=null;
  const scope=phrase.match(/\s+on\s+(LP[12]-.+)$/i);if(scope){scopePages=pages(scope[1]);if(!scopePages)return null;phrase=phrase.slice(0,scope.index);}
  const parts=phrase.split(/\s*,\s*/);if(parts.length>3)return null;
  for(const part of parts.slice(1)){
   let m=part.match(/^reset (?:the sum )?(to zero )?at each (page|line|word)$/i);
   if(m){if(reset!==null||m[1]&&initial!==null)return null;reset=m[2].toLowerCase();if(m[1])initial=0;continue;}
   m=part.match(/^starting (?:the sum )?at zero(?: (?:on|at) each (page|line|word))?$/i);
   if(!m||initial!==null||m[1]&&reset!==null)return null;initial=0;if(m[1])reset=m[1].toLowerCase();
  }
  const core=parts[0].replace(/\u2212/g,'-').replace(/\s+/g,' ').toLowerCase();
  const named=/^(?:apply |use )?cumulative plaintext[- ]sum autokey (?:modulo|mod)\s*29$/.test(core);
  const equation=core.replace(/^(?:use|apply) /,'').replace(/\s+/g,'');
  if(!named&&!/^(?:p_i=c_i-sum\(p_jforj<i\)|c_i=sum\(p_jforj<=i\))mod(?:ulo)?29$/.test(equation))return null;
  return freeze({sourceText:text,reset,initial,...(scopePages?{scopePages}:{})});
 }
 const matches=text=>!!parse(text),binding=d=>C.serialize({source:d.source,aim:d.aim,method:d.method,scope:d.scope,rules:d.rules,unresolved:d.unresolved});
 function checked(input){
  const d=capture(input);if(d?.schema!==C.SCHEMA||d.status!=='draft'||d.confirmation||d.execution!=='not_run'||!Number.isSafeInteger(d.revision)||d.aim?.status!=='specified'||d.scope?.status!=='specified'||!Array.isArray(d.scope.value.pages)||!d.scope.value.pages.length||own(d.scope.value,'description')||d.method?.status!=='specified'||d.method.value.operations.length!==1||d.unresolved.length||!Array.isArray(d.clarifications))return null;
  const op=d.method.value.operations[0];if(op.id!=='described_method'||typeof op.label!=='string'||Object.keys(op).some(k=>!['id','label','sourceText','declaredFamilyId','provenance'].includes(k))||own(op,'sourceText')&&op.sourceText!==op.label||d.source.origin!=='shared_link'&&d.source.text!==op.label)return null;
  const candidate=parse(op.label);if(!candidate||candidate.scopePages&&!same(candidate.scopePages,C.pages(d.scope.value.pages)))return null;
  return {draft:d,candidate,binding:binding(d)};
 }
 function inspect(input){try{return checked(input)?.candidate||null;}catch{return null;}}
 function settings(value){
  const {draft:d,candidate:c,binding:key}=value;
  const history=d.clarifications.filter(x=>x.text===key&&/^cumulative-(reset|initial|representation|confirm|interpretation)$/.test(x.question));
  const selected=kind=>history.filter(x=>x.question==='cumulative-'+kind).at(-1)?.choice;
  const combined=selected('interpretation'),global=d.rules.reset,representation=d.rules.representation,initialState=d.rules.initialState;
  const globalReset=global.status==='specified'&&['page','line','word'].includes(global.value)?global.value:null;
  const reset=c.reset||globalReset||selected('reset');
  const initial=c.initial===0||initialState.status==='specified'&&initialState.value===0||selected('initial')==='zero'||['zero','zero-gp29'].includes(combined);
  const gp=representation.status==='specified'&&representation.value==='GP29'||representation.status==='unspecified'&&(selected('representation')==='gp29'||['gp29','zero-gp29'].includes(combined));
  const conflict=global.status!=='unspecified'&&(global.status!=='specified'||!globalReset||c.reset&&globalReset!==c.reset)||initialState.status!=='unspecified'&&(initialState.status!=='specified'||initialState.value!==0)||representation.status!=='unspecified'&&(representation.status!=='specified'||representation.value!=='GP29');
  return {reset,initial,gp,blocked:conflict||history.some(x=>x.choice==='as-described')};
 }
 function complete(input){
  let value;try{value=checked(input);}catch{return input;}if(!value)return input;const state=settings(value);
  if(state.blocked||!['page','line','word'].includes(state.reset)||!state.initial||!state.gp)return input;
  const provenance={kind:'user_clarification',refs:['literal-cumulative-equivalence',...value.draft.method.provenance.refs]},field=v=>C.field('specified',v,provenance),rules={};
  if(value.draft.rules.representation.status==='unspecified')rules.representation=field('GP29');
  if(value.draft.rules.initialState.status==='unspecified')rules.initialState=field(0);
  let next=C.applyMethodEdit(value.draft,{type:'replace',index:0,operation:{id:'cumulative_difference',label:'Cumulative difference',reset:state.reset}});next=C.revise(next,{rules});return next;
 }
 function question(input){
  let value;try{value=checked(input);}catch{return null;}if(!value)return null;const state=settings(value);if(state.blocked)return null;
  const make=(kind,prompt,context,choices)=>({id:'cumulative-'+kind+':'+value.draft.revision,prompt,context,choices:[...choices,{id:'as-described',label:'Keep my wording without choosing this calculation'}]});
  if(!state.reset)return make('reset','When should the cumulative sum restart?','The literal plaintext-sum rule needs an explicit restart boundary. Each page is processed separately.',[{id:'page',label:'At each page',example:'Keep state across spaces and line breaks.'},{id:'line',label:'At each line',example:'Restart at each newline.'},{id:'word',label:'At every non-rune character',example:'Spaces, punctuation and line breaks all restart the sum.'}]);
  if(state.initial&&state.gp)return null;
  const choice=!state.initial&&!state.gp?'zero-gp29':!state.initial?'zero':'gp29';
  const label=choice==='zero-gp29'?'Use GP rune indices 0\u201328 and a zero starting sum':choice==='zero'?'Start the sum at zero after each restart':'Use GP rune indices 0\u201328';
  return make('interpretation','Use this interpretation of the formula?','Subtract the preceding ciphertext rune from each rune, modulo 29. The first rune after each '+(state.reset==='word'?'non-rune separator':state.reset)+' restart stays unchanged. This is the stated cumulative plaintext sum when the starting sum is zero. Your aim, text edition and chosen evaluation stay unchanged.',[{id:choice,label}]);
 }
 function clarify(input,id,choice){
  const value=checked(input),q=question(input);if(!value||!q||q.id!==id||!q.choices.some(x=>x.id===choice))throw Error('This cumulative-sum question changed. Review the current choices.');
  const next=C.revise(value.draft,{});next.clarifications.push({question:id.slice(0,id.lastIndexOf(':')),choice,text:value.binding,revision:next.revision});return complete(next);
 }
 const api={matches,inspect,question,clarify,complete};if(node)module.exports=api;else root.CumulativeIntake=api;
})(typeof globalThis!=='undefined'?globalThis:this);
