/* One finite research family. Coverage means exact cases, never a cipher exclusion. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const ID='deor-feedback-v1',SCHEMA='liberpedia-family-plan-v1';
 const MODES=['repeat','plaintext-autokey','ciphertext-autokey'],DIRECTIONS=['subtract','add'],RESETS=['page','line','word'];
 const KEY=[23,18,3,4],WARNING=[24,7,24,4,9,21,17,18,20,10,18,1];
 const PAGE_IDS=Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0')).filter(id=>id!=='lp2-50');
 const TITLE='DEOR key: fixed Warning opening',QUESTION='Does this four-rune key recover the fixed 12-rune Warning opening at a page start?',LIMIT='Only the stated key, modes, arithmetic, reset rules and raw pages are tested. A matching opening is not a complete reading; a failure does not exclude another opening or cipher.';
 const clone=v=>JSON.parse(E.stable(v));
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value'));
 const scalar=s=>typeof s==='string'&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(s);
 async function hash(v,cryptoAPI){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(v)))),b=>b.toString(16).padStart(2,'0')).join('');}
 function inputs(bundle){
  if(!exact(bundle,['schema','alphabet','pages'])||bundle.schema!=='liberpedia-local-inputs-v1'||!Array.isArray(bundle.alphabet)||bundle.alphabet.length!==29||!Array.isArray(bundle.pages)||bundle.pages.length!==75)throw Error('The official family input bundle is malformed.');
  const runes=new Set();
  for(const entry of bundle.alphabet){
   if(!exact(entry,['rune','latin','prime'])||!scalar(entry.rune)||Array.from(entry.rune).length!==1||/\s/.test(entry.rune)||runes.has(entry.rune)||!scalar(entry.latin)||!entry.latin||Array.from(entry.latin).length>8||!Number.isInteger(entry.prime)||entry.prime<2||entry.prime>1000)throw Error('The official family alphabet is invalid.');
   runes.add(entry.rune);
  }
  const byId=new Map();
  for(const page of bundle.pages){
   if(!exact(page,['id','raw','reviewed_text'])||typeof page.id!=='string'||!/^(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))$/.test(page.id)||byId.has(page.id)||!scalar(page.raw)||page.raw.length>300000||!(page.reviewed_text===null||scalar(page.reviewed_text)&&page.reviewed_text.length<=300000))throw Error('The official family page is invalid.');
   byId.set(page.id,page);
  }
  const pages=PAGE_IDS.map(id=>({id,text:byId.get(id).raw}));
  if(pages.some(page=>!Array.from(page.text).some(ch=>runes.has(ch))))throw Error('A family page has no rune text.');
  const alphabet=clone(bundle.alphabet);
  // Reuse the executable engine's complete alphabet, page and work validation.
  E.validateTask({schema:'liberpedia-local-task-v1',engine:'rune-program-v1',taskId:'0'.repeat(64),title:TITLE,pages,alphabet,steps:[],criterion:{kind:'exact-prefix',values:WARNING.slice()}});
  return {alphabet,pages};
 }
 function configurations(){
  return MODES.flatMap(mode=>DIRECTIONS.flatMap(direction=>RESETS.map(reset=>({id:mode+'--'+direction+'--'+reset,mode,direction,reset,label:({'repeat':'Repeating key','plaintext-autokey':'Plaintext autokey','ciphertext-autokey':'Ciphertext autokey'}[mode])+' · '+direction+' · restart each '+reset}))));
 }
 async function snapshot(bundle,cryptoAPI=root.crypto){
  const source=inputs(bundle),configs=configurations();
  const semantic={familyId:ID,engine:'rune-program-v1',inputVersion:'raw',key:KEY.slice(),modes:MODES.slice(),directions:DIRECTIONS.slice(),resets:RESETS.slice(),criterion:{kind:'exact-prefix',values:WARNING.slice()},alphabet:source.alphabet,pages:source.pages};
  return {id:ID,revision:await hash(semantic,cryptoAPI),title:TITLE,question:QUESTION,limit:LIMIT,configurations:configs,pages:source.pages,totalCases:configs.length*source.pages.length};
 }
 function caseIds(view){
  if(!view||view.id!==ID||!Array.isArray(view.configurations)||!Array.isArray(view.pages))throw Error('Invalid family snapshot.');
  return view.configurations.flatMap(c=>view.pages.map(p=>c.id+'--'+p.id)).sort();
 }
 function selection(selected){
  if(!Array.isArray(selected)||selected.length<1||selected.length>12||selected.some(id=>typeof id!=='string')||new Set(selected).size!==selected.length)throw Error('Select one to 12 distinct family cases.');
  return selected.slice().sort();
 }
 async function prepareCases(view,alphabet,selected,cryptoAPI){
  const ids=selection(selected),allowed=new Set(caseIds(view));
  if(ids.some(id=>!allowed.has(id)))throw Error('The selected case is outside this family.');
  const cases=[];
  for(const id of ids){
   const pageId=id.slice(-6),configuration=id.slice(0,-8),config=view.configurations.find(c=>c.id===configuration),page=view.pages.find(p=>p.id===pageId);
   const task=await E.prepare({title:TITLE+' · '+configuration+' · '+pageId,pages:[page],alphabet,steps:[{op:'keyed-shift',key:KEY.slice(),mode:config.mode,direction:config.direction,reset:config.reset}],criterion:{kind:'exact-prefix',values:WARNING.slice()}},cryptoAPI);
   cases.push({id,configuration,pageId,task});
  }
  const body={schema:SCHEMA,familyId:ID,revision:view.revision,cases};
  return {...body,planId:await hash(body,cryptoAPI)};
 }
 async function createPreparer(bundle,cryptoAPI=root.crypto){
  const frozen=clone(bundle),view=await snapshot(frozen,cryptoAPI),alphabet=clone(frozen.alphabet);
  const prepare=selected=>prepareCases(view,alphabet,selected,cryptoAPI);
  return {snapshot:clone(view),prepare,validatePlan:plan=>validatePrepared(plan,prepare)};
 }
 async function prepare(bundle,selected,cryptoAPI=root.crypto){
  const ids=selection(selected),preparer=await createPreparer(bundle,cryptoAPI);return preparer.prepare(ids);
 }
 async function validatePlan(plan,bundle,cryptoAPI=root.crypto){
  const preparer=await createPreparer(bundle,cryptoAPI);return preparer.validatePlan(plan);
 }
 async function validatePrepared(plan,prepare){
  if(!exact(plan,['schema','familyId','revision','planId','cases'])||plan.schema!==SCHEMA||plan.familyId!==ID||!Array.isArray(plan.cases)||plan.cases.some(c=>!exact(c,['id','configuration','pageId','task'])))throw Error('The family plan is malformed.');
  const expected=await prepare(plan.cases.map(c=>c.id));
  if(E.stable(expected)!==E.stable(plan))throw Error('The family plan differs from its exact inputs and settings.');
  return expected;
 }
 async function validateExecutionPlan(plan,cryptoAPI=root.crypto){
  // Structural execution safety only. Source authorization still requires validatePlan.
  if(!exact(plan,['schema','familyId','revision','planId','cases'])||plan.schema!==SCHEMA||plan.familyId!==ID||typeof plan.revision!=='string'||typeof plan.planId!=='string'||!/^[a-f0-9]{64}$/.test(plan.revision)||!/^[a-f0-9]{64}$/.test(plan.planId)||!Array.isArray(plan.cases)||plan.cases.length<1||plan.cases.length>12)throw Error('The family execution plan is malformed.');
  const copy=clone(plan),configs=configurations(),pages=new Set(PAGE_IDS);let previous='',alphabet=null;
  for(const item of copy.cases){
   if(!exact(item,['id','configuration','pageId','task'])||typeof item.id!=='string'||typeof item.configuration!=='string'||!pages.has(item.pageId)||item.id!==item.configuration+'--'+item.pageId||item.id<=previous)throw Error('The family cases must be distinct and in canonical order.');
   previous=item.id;const config=configs.find(c=>c.id===item.configuration);if(!config)throw Error('The family configuration is invalid.');
   await E.checkIdentity(item.task,cryptoAPI);
   const task=item.task,expectedStep={op:'keyed-shift',key:KEY.slice(),mode:config.mode,direction:config.direction,reset:config.reset};
   if(task.title!==TITLE+' · '+item.configuration+' · '+item.pageId||task.pages.length!==1||task.pages[0].id!==item.pageId||E.stable(task.steps)!==E.stable([expectedStep])||E.stable(task.criterion)!==E.stable({kind:'exact-prefix',values:WARNING.slice()}))throw Error('The family task differs from its declared case.');
   const encoded=E.stable(task.alphabet);if(alphabet!==null&&alphabet!==encoded)throw Error('Family cases must use the same ordered alphabet.');alphabet=encoded;
   const runes=new Set(task.alphabet.map(entry=>entry.rune));if(!Array.from(task.pages[0].text).some(ch=>runes.has(ch)))throw Error('A family case has no rune text.');
  }
  const body={schema:copy.schema,familyId:copy.familyId,revision:copy.revision,cases:copy.cases};
  if(await hash(body,cryptoAPI)!==copy.planId)throw Error('The family execution plan identity changed.');
  return copy;
 }
 const api={snapshot,caseIds,prepare,validatePlan,validateExecutionPlan,createPreparer};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchFamily=api;
})(typeof globalThis!=='undefined'?globalThis:this);
