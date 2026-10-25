/* Closed mathematical question definitions; display prose is not identity. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const HEX=/^[a-f0-9]{64}$/;
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const clone=v=>JSON.parse(E.stable(v));
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 const DEOR={key:[23,18,3,4],values:[24,7,24,4,9,21,17,18,20,10,18,1],modes:['ciphertext-autokey','plaintext-autokey','repeat'],directions:['add','subtract'],resets:['line','page','word']};
 function definition(id,parameters,version=1){
  if(version!==1)throw Error('The question version is not maintained.');
  if(id==='word-boundary-sensitivity'){
   if(!exact(parameters,['lag','a','b'])||!Number.isInteger(parameters.lag)||parameters.lag<1||parameters.lag>12||!Number.isInteger(parameters.a)||parameters.a<0||parameters.a>28||!Number.isInteger(parameters.b)||parameters.b<0||parameters.b>28)throw Error('Unsupported boundary question settings.');
   return freeze({id,version:1,evidenceKind:'paired-word-affine-count',evaluatorId:'paired-above-own-mean-v1',parameters:clone(parameters),scopePolicy:'same-pinned-inputs',nextByState:{answered:null,'missing-evidence':'run-missing-evidence',unavailable:'retry-evidence'},mathematics:{modulus:29,boundaries:['non-rune','hyphen-period'],transforms:[],expectation:'uniform-orders-within-each-group',comparison:'strictly-above-own-exact-mean'},question:'Does the above-average count require joining across layout marks?',limit:'Each grouping uses its own rearrangement average. This is not a significance test or independent confirmation, and it does not establish which breaks are correct.'});
  }
  if(id==='deor-warning-opening'){
   if(!exact(parameters,['key','values','modes','directions','resets']))throw Error('Unsupported finite-prefix question settings.');
   const normalized={key:parameters.key,values:parameters.values,modes:Array.isArray(parameters.modes)?parameters.modes.slice().sort():null,directions:Array.isArray(parameters.directions)?parameters.directions.slice().sort():null,resets:Array.isArray(parameters.resets)?parameters.resets.slice().sort():null};
   if(E.stable(normalized)!==E.stable(DEOR))throw Error('The finite-prefix question must retain the declared DEOR domain.');
   return freeze({id,version:1,evidenceKind:'finite-exact-prefix',evaluatorId:'finite-exact-prefix-existence-v1',parameters:clone(DEOR),scopePolicy:'same-pinned-inputs',nextByState:{'missing-evidence':'run-missing-evidence',unavailable:'retry-evidence'},nextByAnswer:{'prefix-found':'inspect-evidence','prefix-not-found':null},mathematics:{familyId:'deor-feedback-v1',modulus:29,pageStart:true,headings:'included',separatorRule:'preserve-and-do-not-advance-key',pageState:'fresh',resetBoundaries:{page:'page-start',line:'CR-or-LF',word:'every-non-rune'},necessaryExclusion:'first-rune-mismatch',stop:'first-verified-full-prefix-match-or-all-cases-excluded'},question:'Does the DEOR key recover the fixed 12-rune Warning opening in any declared case?',limit:'Covers DEOR, the 12-rune Warning opening, these restart rules and these page texts. A match needs the rest of the page checked; other openings and cipher rules remain open.'});
  }
  if(id==='fixed-program-prefix'){
   if(!exact(parameters,['steps','criterion'])||parameters.criterion?.kind!=='exact-prefix')throw Error('The fixed program question needs an exact prefix criterion and ordered steps.');
   // Reuse the engine's structural validation without executing a target or
   // substituting input values. The real alphabet/pages bind below; an empty
   // validation page cannot establish finite-key sufficiency for real inputs.
   E.validateTask({schema:E.TASK,engine:E.ENGINE,taskId:'0'.repeat(64),title:'Question structure validation',alphabet:Array.from({length:29},(_,i)=>({rune:String.fromCodePoint(0x16a0+i),latin:'R'+i,prime:i+2})),pages:[{id:'lp2-00',text:''}],steps:parameters.steps,criterion:parameters.criterion});
   return freeze({id,version:1,evidenceKind:'fixed-program-exact-prefix',evaluatorId:'verified-page-prefix-existence-v1',parameters:clone(parameters),scopePolicy:'same-pinned-inputs',nextByState:{'missing-evidence':'run-missing-evidence',unavailable:'retry-evidence'},nextByAnswer:{'prefix-found':'inspect-evidence','prefix-not-found':null},mathematics:{engine:E.ENGINE,modulus:29,pageStart:true,headings:'included',prefixUnit:'ordered-rune-index',pageState:'fresh',stop:'first-verified-full-prefix-match-or-all-declared-pages-checked'},question:'Does this fixed program produce the specified opening on any declared page?',limit:'Covers only these ordered steps, the exact prefix and the pinned complete pages. A matching opening is not a complete reading; other prefixes, rules and inputs remain open.'});
  }
  throw Error('The question protocol is not maintained.');
 }
 async function hash(value,cryptoAPI){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value)))),n=>n.toString(16).padStart(2,'0')).join('');}
 async function identity(id,parameters,cryptoAPI=root.crypto){const d=definition(id,parameters);const {question,limit,...semantic}=d;return {id:d.id,version:d.version,definitionSha256:await hash({schema:'liberpedia-question-definition-v1',...semantic},cryptoAPI)};}
 async function bindInputs(id,parameters,inputs,cryptoAPI=root.crypto){
  parameters=clone(parameters);inputs=clone(inputs);
  const keys=['engine','inputVersion','alphabetSha256','pages',...(Object.hasOwn(inputs||{},'domainRevision')?['domainRevision']:[])];
  if(!exact(inputs,keys)||inputs.engine!==E.ENGINE||!['raw','reviewed'].includes(inputs.inputVersion)||!HEX.test(inputs.alphabetSha256)||!Array.isArray(inputs.pages)||!inputs.pages.length||inputs.pages.length>75||inputs.pages.some(p=>!exact(p,['id','sha256'])||!/^lp[12]-\d{2}$/.test(p.id)||!HEX.test(p.sha256))||new Set(inputs.pages.map(p=>p.id)).size!==inputs.pages.length||Object.hasOwn(inputs,'domainRevision')&&!HEX.test(inputs.domainRevision))throw Error('Question inputs require an exact pinned scope.');
  const protocol=await identity(id,parameters,cryptoAPI),pinned=clone(inputs);pinned.pages.sort((a,b)=>a.id.localeCompare(b.id));
  const body={schema:'liberpedia-question-instance-v1',questionId:protocol.id,version:protocol.version,definitionSha256:protocol.definitionSha256,inputs:pinned};
  return freeze({...body,id:await hash(body,cryptoAPI)});
 }
 async function bindTask(id,parameters,task,inputVersion,cryptoAPI=root.crypto){
  const frozen=clone(task);parameters=clone(parameters);await E.checkIdentity(frozen,cryptoAPI);
  const boundary=id==='word-boundary-sensitivity'&&frozen.criterion.kind==='word-affine-count'&&!frozen.steps.length&&E.stable(parameters)===E.stable({lag:frozen.criterion.lag,a:frozen.criterion.a,b:frozen.criterion.b}),prefix=id==='fixed-program-prefix'&&frozen.criterion.kind==='exact-prefix'&&E.stable(parameters)===E.stable({steps:frozen.steps,criterion:frozen.criterion});
  if(!boundary&&!prefix)throw Error('The task does not implement this exact question protocol.');
  const pages=[];for(const page of frozen.pages)pages.push({id:page.id,sha256:Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(page.text))),n=>n.toString(16).padStart(2,'0')).join('')});
  return bindInputs(id,parameters,{engine:frozen.engine,inputVersion,alphabetSha256:await hash(frozen.alphabet,cryptoAPI),pages},cryptoAPI);
 }
 const api={definition,identity,bindInputs,bindTask};if(typeof module==='object'&&module.exports)module.exports=api;else root.QuestionProtocols=api;
})(typeof globalThis!=='undefined'?globalThis:this);
