/* Reviewed proposal-to-program mapping data. Completeness is not review or admission authority. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,MD=node?require('./method-design.js'):root.MethodDesign,V=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram,J=node?require('./finite-json.js'):root.FiniteJSON,Bundle=node?require('./local-input-bundle.js'):root.LocalInputBundle;
 const SCHEMA='liberpedia-method-implementation-v1',LIMITS=Object.freeze({bytes:2*1024*1024,coverage:23,issues:16}),bindings=new WeakMap();
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;},ensure=(ok,message)=>{if(!ok)throw Error(message);};
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
 const capture=value=>J.capture(value,{maxBytes:LIMITS.bytes,maxDepth:24,maxNodes:300000});
 const str=max=>({type:'string',minLength:1,maxLength:max}),integer=(min,max)=>({type:'integer',minimum:min,maximum:max}),enumOf=values=>({enum:values}),array=(items,min,max)=>({type:'array',items,minItems:min,maxItems:max}),object=properties=>({type:'object',additionalProperties:false,required:Object.keys(properties),properties}),key=array(integer(0,28),1,256),reset=enumOf(['page','line','word']),direction=enumOf(['add','subtract']);
 const STEP_SCHEMA={anyOf:[object({op:{const:'reverse'},unit:reset}),object({op:{const:'affine'},a:integer(0,28),b:integer(0,28)}),object({op:{const:'cumulative-difference'},reset}),object({op:{const:'keyed-shift'},key,mode:enumOf(['repeat','plaintext-autokey','ciphertext-autokey']),direction,reset}),object({op:{const:'interrupted-keyed-shift'},key,direction,reset,interrupts:array(integer(0,28),1,29)}),object({op:{const:'finite-shift'},key:array(integer(0,28),1,20000),direction,reset}),object({op:{const:'remove-rune-types'},values:array(integer(0,28),1,29)}),object({op:{const:'collapse-adjacent-repeats'},unit:reset,policy:enumOf(['all-but-first','non-overlapping-pairs'])})]};
 const CRITERION_SCHEMA={anyOf:[{type:'null'},object({kind:{const:'measurement'}}),object({kind:{const:'exact-prefix'},values:array(integer(0,28),1,256)}),object({kind:{const:'exact-prefix-set'},openings:array(object({id:{type:'string',pattern:'^[a-z][a-z0-9-]{0,63}$'},values:array(integer(0,28),1,256)}),1,32)}),object({kind:{const:'language-score'},modelId:str(100),modelSha256:{type:'string',pattern:'^[a-f0-9]{64}$'}})]};
 const JSON_SCHEMA=freeze(object({schema:{const:SCHEMA},proposalSha256:{type:'string',pattern:'^[a-f0-9]{64}$'},steps:array(STEP_SCHEMA,0,8),criterion:CRITERION_SCHEMA,coverage:array(object({part:enumOf(['step','evaluation','key-use','representation','parameter','control']),index:integer(0,7),status:enumOf(['implemented','unsupported']),programSteps:array(integer(1,8),0,8),note:str(500)}),1,23),issues:array(str(500),0,16)}));
 const TYPED_SCHEMA='liberpedia-method-design-v2',UNRESOLVED='Some proposed requirements remain unresolved. See their individual notes.';
 function checks(){const value=node?require('./method-check-contract.js'):root.MethodCheckContract;ensure(value,'Typed check definitions are unavailable.');return value;}
 function typedRequirements(input){
  const p=MD.validate(input);ensure(p.schema===TYPED_SCHEMA,'Use a reviewed typed method proposal.');const K=checks(),criterion=K.resolveEvaluation(p.evaluation),owned=[],requirements=[];
  const put=(part,index,supported,note)=>owned.push({part,index,status:supported?'implemented':'unsupported',programSteps:[],note});
  const evaluationNotes={'original-output-measurements':'Compare the exact original input with verified changed output: counts, repeated-pair rates and pooled index of coincidence. Descriptive differences only; no significance or hypothesis verdict is requested.','output-measurements':'Report aggregate output rune counts, adjacent and equal-adjacent rune pairs, and pooled index of coincidence. No significance or hypothesis verdict is requested.','exact-prefix':'Compare each output page with the exact reviewed opening rune sequence.','exact-prefix-set':'Compare each output page with the exact reviewed named opening rune sequences.','language-score':'Apply the exact reviewed fixed language reference criterion. A short output is insufficient, not a failed reading.'};
  put('evaluation',0,criterion!==null,evaluationNotes[p.evaluation.kind]||'The described evaluation has no maintained executable comparator.');
  if(p.keyUse.kind==='not-used')put('key-use',0,true,'The reviewed proposal uses no key material.');else requirements.push({part:'key-use',index:0});
  const representation=K.resolveRepresentation(p.representation);put('representation',0,representation.supported,representation.supported?representation.description:'The described representation has no maintained typed implementation.');
  p.parameters.forEach((parameter,index)=>{if(parameter.values.length>1)put('parameter',index,false,'This single-program runtime does not execute every alternative value for parameter '+parameter.name+'.');else requirements.push({part:'parameter',index});});
  p.controls.forEach((control,index)=>{const fact=K.resolveControl(control);put('control',index,fact.supported,fact.supported?fact.description:'The described control has no maintained typed implementation.');});
  return freeze({criterion,owned,draft:{steps:p.steps.map((_,index)=>({part:'step',index})),requirements}});
 }
 async function fromTypedDraft(proposalInput,input,crypto=root.crypto){
  const p=MD.validate(proposalInput),facts=typedRequirements(p),value=capture(input);
  ensure(exact(value,['steps','coverage'])&&exact(value.coverage,['steps','requirements']),'Use the exact typed procedure draft fields.');
  const rows=(items,inventory,procedure)=>{ensure(Array.isArray(items)&&items.length===inventory.length,'The typed draft inventory changed.');return items.map((item,index)=>{ensure(exact(item,procedure?['status','programSteps','note']:['status','note']),'Typed draft metadata is compiler-owned.');return {...inventory[index],status:item.status,programSteps:procedure?item.programSteps:[],note:item.note};});};
  const coverage=[...rows(value.coverage.steps,facts.draft.steps,true),...facts.owned,...rows(value.coverage.requirements,facts.draft.requirements,false)],implementation={schema:SCHEMA,proposalSha256:await hash(p,crypto),steps:value.steps,criterion:facts.criterion,coverage,issues:coverage.some(item=>item.status==='unsupported')?[UNRESOLVED]:[]};
  return validateBinding(p,implementation,crypto);
 }
 function text(value){ensure(typeof value==='string'&&value.trim()&&Array.from(value).length<=500&&!/[\u0000-\u001f\u007f-\u009f\u2028\u2029\ud800-\udfff]/u.test(value),'Use bounded plain implementation notes.');}
 function syntax(steps,criterion){
  let labels=null;if(criterion?.kind==='language-score'){const scorer=node?require('./language-score.js'):root.RuneLanguageScore;labels=scorer?.data?.payload?.alphabet;ensure(labels,'The maintained language model is unavailable.');}
  const alphabet=Array.from({length:29},(_,i)=>({rune:String.fromCodePoint(0x16a0+i),latin:labels?labels[i]:'R'+i,prime:i+2}));
  // This empty invented page is a syntax probe only. Measurement here never
  // supplies a missing requested criterion, and no runner is called.
  V.validateTask({schema:V.TASK,engine:V.ENGINE,taskId:'0'.repeat(64),title:'Synthetic implementation syntax only',alphabet,pages:[{id:'lp1-00',text:''}],steps,criterion:criterion===null?{kind:'measurement'}:criterion});
 }
 function validate(proposalInput,input){
  const proposal=MD.validate(proposalInput),value=capture(input);ensure(exact(value,['schema','proposalSha256','steps','criterion','coverage','issues'])&&value.schema===SCHEMA&&typeof value.proposalSha256==='string'&&value.proposalSha256.length===64&&/^[a-f0-9]{64}$/.test(value.proposalSha256),'Use the exact implementation schema and proposal hash.');
  syntax(value.steps,value.criterion);
  ensure(Array.isArray(value.issues)&&value.issues.length<=LIMITS.issues,'Use bounded unresolved implementation issues.');value.issues.forEach(text);
  const expected=new Set(['evaluation:0','key-use:0','representation:0',...proposal.steps.map((_,i)=>'step:'+i),...proposal.parameters.map((_,i)=>'parameter:'+i),...proposal.controls.map((_,i)=>'control:'+i)]),seen=new Set(),referenced=new Set();
  ensure(Array.isArray(value.coverage)&&value.coverage.length===expected.size&&value.coverage.length<=LIMITS.coverage,'Every proposal part needs exactly one implementation status.');
  for(const item of value.coverage){
   ensure(exact(item,['part','index','status','programSteps','note'])&&typeof item.part==='string'&&Number.isSafeInteger(item.index)&&item.index>=0,'Use exact proposal coverage coordinates.');const coordinate=item.part+':'+item.index;
   ensure(expected.has(coordinate)&&!seen.has(coordinate),'Proposal coverage is missing, repeated or out of range.');seen.add(coordinate);text(item.note);
   ensure(['implemented','unsupported'].includes(item.status)&&Array.isArray(item.programSteps)&&item.programSteps.length<=8&&item.programSteps.every((n,i)=>Number.isSafeInteger(n)&&n>=1&&n<=value.steps.length&&(i===0||item.programSteps[i-1]<n)),'Use sorted distinct one-based program step references.');
   ensure(item.status!=='unsupported'||item.programSteps.length===0,'An unsupported part cannot claim program steps.');
   if(item.part==='step'&&item.status==='implemented'){ensure(item.programSteps.length>0,'An implemented proposal step must name its program steps.');item.programSteps.forEach(n=>referenced.add(n));}
   if(item.part==='parameter'&&item.status==='implemented')ensure(proposal.parameters[item.index].values.length===1,'A single program cannot implement multiple alternative parameter values.');
   if(item.part==='evaluation'&&item.status==='implemented')ensure(value.criterion!==null,'An implemented evaluation needs its exact maintained criterion.');
  }
  // Coverage array order is incidental; the proposal's own procedure order is not.
  // One combined span may implement adjacent prose steps. Otherwise spans may
  // only advance, sharing an endpoint but never crossing or moving backwards.
  const ordered=value.coverage.filter(item=>item.part==='step'&&item.status==='implemented').sort((a,b)=>a.index-b.index);
  for(let i=1;i<ordered.length;i++){
   const previous=ordered[i-1].programSteps,current=ordered[i].programSteps;
   ensure(stable(previous)===stable(current)||previous[previous.length-1]<=current[0],'Implemented proposal steps must preserve their declared procedure order.');
  }
  ensure(value.steps.every((_,i)=>referenced.has(i+1)),'Every program step must be accounted for by a proposal step.');
  if(proposal.schema===TYPED_SCHEMA){
   const facts=typedRequirements(proposal);ensure(stable(value.criterion)===stable(facts.criterion),'The program changed the reviewed typed evaluation.');
   for(const fact of facts.owned){
    const actual=value.coverage.find(item=>item.part===fact.part&&item.index===fact.index);
    // Persisted notes are bounded annotations, not freshly generated identity or
    // capability facts. Copy changes must not invalidate an admitted binding.
    ensure(actual.part===fact.part&&actual.index===fact.index&&actual.status===fact.status&&stable(actual.programSteps)===stable(fact.programSteps),'Typed runtime capability facts cannot be changed by a draft.');
   }
   if(proposal.keyUse.kind==='not-used')ensure(!value.steps.some(step=>Array.isArray(step.key)),'A keyless typed proposal cannot add a keyed operation.');
   const unresolved=value.coverage.some(item=>item.status==='unsupported');ensure(unresolved===(value.issues.length>0),'Typed unresolved state must follow exact requirement coverage.');
  }
  return freeze(value);
 }
 async function hash(value,crypto){ensure(crypto?.subtle,'SHA-256 is required.');return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(stable(value)))),v=>v.toString(16).padStart(2,'0')).join('');}
 async function validateBinding(proposalInput,input,crypto=root.crypto){
  const proposal=MD.validate(proposalInput),implementation=validate(proposal,input);ensure(await hash(proposal,crypto)===implementation.proposalSha256,'The implementation belongs to another proposal.');ensure(stable(proposal)===stable(MD.validate(proposalInput))&&stable(implementation)===stable(capture(input)),'The proposal or implementation changed during binding.');return implementation;
 }
 async function bind(options,crypto=root.crypto){
  const captured=capture(options);ensure(exact(captured,['proposal','implementation']),'Bind one exact proposal and implementation.');const proposal=MD.validate(captured.proposal),implementation=await validateBinding(proposal,captured.implementation,crypto);ensure(stable(captured)===stable(capture(options)),'The implementation binding changed.');
  const ready=implementation.criterion!==null&&!implementation.issues.length&&implementation.coverage.every(item=>item.status==='implemented'),token=Object.freeze({});bindings.set(token,freeze({proposal,implementation,ready,limit:'The actual program uses the ordered GP29 rune alphabet. A complete mapping is a proposal for review, not proof of faithful interpretation, successful controls, admission or a scientific finding. Supplied input-bundle authenticity must be checked by the caller.'}));return token;
 }
 function inspect(token){ensure(bindings.has(token),'Use a verified implementation binding.');return bindings.get(token);}
 function compileBody(token,options){
  const binding=inspect(token);ensure(binding.ready,'Resolve every unsupported proposal part before preparing a program.');const input=capture(options);ensure(exact(input,['bundle']),'Use one supplied official input bundle without scope overrides.');
  const bundle=Bundle.parse(input.bundle),proposal=binding.proposal,pages=proposal.pages.map(id=>{const page=bundle.pages.get(id),text=proposal.inputVersion==='raw'?page?.raw:page?.reviewed_text;ensure(typeof text==='string','The proposed input edition is unavailable.');return {id,text};});
  const body={title:proposal.name,alphabet:bundle.alphabet,pages,steps:binding.implementation.steps,criterion:binding.implementation.criterion};V.validateTask({...body,schema:V.TASK,engine:V.ENGINE,taskId:'0'.repeat(64)});return freeze(capture(body));
 }
 const api=Object.freeze({SCHEMA,LIMITS,JSON_SCHEMA,typedRequirements,fromTypedDraft,validate,validateBinding,bind,inspect,compileBody});if(node)module.exports=api;else root.MethodImplementation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
