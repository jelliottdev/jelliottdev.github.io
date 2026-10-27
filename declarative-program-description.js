/* Explain declared operations. Illustrations run invented input, never manuscript pages. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,R=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram,Legacy=node?require('./published-program-description.js'):root.PublishedProgramDescription,Evaluators=node?require('./output-evaluators.js'):root.OutputEvaluators;
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function boundary(unit){
  if(unit==='word')return 'Any space, punctuation or other non-rune character starts a new group. Each page starts fresh.';
  if(unit==='line')return 'Spaces and punctuation are kept but ignored when comparing neighboring runes. A carriage return or line feed starts a new group. Each page starts fresh.';
  if(unit==='page')return 'Spaces, punctuation and line breaks are kept but ignored when comparing neighboring runes. Each page starts fresh.';
  throw Error('This program has no supported boundary description.');
 }
 function describeStep(s,index,alphabet){
  const common={number:index+1,op:s.op};
  if(s.op==='remove-rune-types')return {...common,instruction:'Remove every occurrence of the specified rune types. Keep all other runes, spaces, punctuation and line breaks.',runeTypes:s.values.map(value=>({value,rune:alphabet[value].rune,label:alphabet[value].latin})),keyMaterial:null};
  if(s.op==='collapse-adjacent-repeats')return {...common,instruction:s.policy==='all-but-first'?'Keep only the first rune of each run of equal neighboring runes.':'Remove the second rune of each non-overlapping equal pair; keep an unmatched final rune.',repeatExample:s.policy==='all-but-first'?'AAA → A':'AAA → AA',repeatExampleNote:'A stands for one repeated rune, not a letter of decoded text.',boundary:boundary(s.unit),keyMaterial:null};
  // Reuse the maintained descriptions for existing arithmetic and order rules.
  const instruction=Legacy.step(s),keyMaterial=Array.isArray(s.key)?{kind:'literal-rune-values',label:'Supplied key values',length:s.key.length,preview:s.key.slice(0,8)}:null;
  return {...common,instruction,keyMaterial};
 }
 function criterion(value){
  if(value.kind==='measurement')return {label:'Rune measurements',description:'Report aggregate output rune and adjacent-pair counts, equal adjacent pairs, and pooled repeated-rune concentration (index of coincidence). Adjacent pairs are counted in each page’s rune-only sequence, ignoring spaces, punctuation and line breaks; none crosses a page boundary.',limit:'These measurements do not establish filler, statistical significance, readable text or a decryption.'};
  if(value.kind==='exact-prefix')return {label:'Supplied opening comparison',description:'Compare only the first '+value.values.length+' '+(value.values.length===1?'rune':'runes')+' of each page’s output with the supplied sequence.',limit:'An exact opening match does not establish a complete reading. Other positions and sequences are not checked.'};
  if(value.kind==='exact-prefix-set')return {label:'Supplied opening comparisons',description:'Compare the start of each page’s output with '+value.openings.length+' supplied rune sequences.',lengths:value.openings.map(item=>item.values.length),limit:'A literal sequence match does not establish a complete reading. Other positions and sequences are not checked.'};
  const maintained=Evaluators.describe(value);if(maintained)return {label:maintained.heading,description:maintained.plan,limit:maintained.limit};
  throw Error('This program has no maintained criterion description.');
 }
 function describe(input){const task=R.validateTask(input);return freeze({schema:'liberpedia-declarative-program-description-v1',steps:task.steps.map((s,i)=>describeStep(s,i,task.alphabet)),...(task.steps.length?{}:{unchanged:Legacy.program([])}),pageIds:task.pages.map(p=>p.id),criterion:criterion(task.criterion),limit:'This describes the declared program. It does not verify a result or establish the hypothesis.'});}
 async function example(input,crypto=root.crypto){
  const task=R.validateTask(input);describe(task);
  const removed=task.steps.find(s=>s.op==='remove-rune-types'),a=removed?removed.values[0]:0,b=(a+1)%29,A=task.alphabet[a].rune,B=task.alphabet[b].rune,text=A+A+A+' '+A+A+'\n'+A+A+B;
  let invented,result;
  try{invented=await R.prepare({title:'Invented transformation illustration',alphabet:task.alphabet,pages:[{id:'lp1-00',text}],steps:task.steps,criterion:{kind:'measurement'}},crypto);result=R.run(invented);}catch(error){if(task.steps.some(s=>s.op==='finite-shift')&&/finite key stream is shorter than a reset segment/.test(error.message))return null;throw error;}
  const output=result.transformed[0].text,labels=new Map(task.alphabet.map(item=>[item.rune,item.latin])),labelled=value=>Array.from(value,char=>labels.get(char)||char).join('');
  return freeze({schema:'liberpedia-declarative-program-example-v1',label:'Invented example — not manuscript evidence',input:text,output,inputLabels:labelled(text),outputLabels:labelled(output),labelNote:'Latin rune labels, not a translation.',removedRuneCount:result.alignment.pages[0].removed.length,steps:describe(task).steps});
 }
 async function renderExample(task,crypto=root.crypto){const m=await example(task,crypto);if(!m)return '';return '<figure class="protocol-example" aria-label="Invented transformation example"><figcaption>'+esc(m.label)+'</figcaption><p>'+esc(m.labelNote)+'</p><div class="protocol-example-outputs"><div><h3>Input</h3><pre><code>'+esc(m.inputLabels)+'</code></pre></div><div><h3>Output after all steps</h3><pre><code>'+esc(m.outputLabels)+'</code></pre></div></div><p>'+m.removedRuneCount+' '+(m.removedRuneCount===1?'rune removed':'runes removed')+' in this illustration. Spaces, punctuation and line breaks are retained.</p></figure>';}
 const api=Object.freeze({describe,example,renderExample});if(node)module.exports=api;else root.DeclarativeProgramDescription=api;
})(typeof globalThis!=='undefined'?globalThis:this);
