/* Canonical bounded next work from owned verified coverage. No admission or execution. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Q=node?require('./factored-finite-question.js'):root.FactoredFiniteQuestion,Groups=node?require('./factored-page-groups.js'):root.FactoredPageGroups,Session=node?require('./factored-search-session.js'):root.FactoredSearchSession,Compiler=node?require('./factored-finite-search-compiler.js'):root.FactoredFiniteSearchCompiler;
 const capture=v=>J.capture(v,{maxBytes:2*1024*1024+131072,maxDepth:24,maxNodes:500000}),exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 function readOptions(options){if(!exact(options,['compiled','card','bundle','session']))throw Error('Use the original question and owned verified session.');const descriptors=Object.getOwnPropertyDescriptors(options);if(Object.values(descriptors).some(d=>!d.enumerable||!Object.hasOwn(d,'value')))throw Error('Use plain next-group options.');return {compiled:descriptors.compiled.value,session:descriptors.session.value,...capture({card:descriptors.card.value,bundle:descriptors.bundle.value})};}
 async function select(options,crypto=root.crypto){
  const input=readOptions(options),authority=Session.inspect(input.session),domain=Q.inspect(input.compiled.domain);Compiler.inspect(input.compiled,{card:input.card,bundle:input.bundle});
  if(authority.domain!==domain||E.stable(authority.card)!==E.stable(input.card))throw Error('The next-group selection changed its original question.');
  function check(){const state=authority.getState(),proof=state.proof;if(state.local||state.pending||state.prepared)throw Error('Save, restore or discard reviewed work before selecting the next groups.');if(state.requiresFreshLookup){const e=Error('Refresh saved evidence before selecting the next groups.');e.code='fresh-evidence-required';throw e;}if(!proof||Q.inspectEvidence(proof).domainId!==domain.id||!proof.lookupComplete)throw Error('Complete the verified saved-evidence lookup before selecting groups.');if(state.phase!=='ready')throw Error('Finish the current research action before selecting the next groups.');return state;}
  let state=check();if(state.decision.state==='answered')return null;if(state.decision.state!=='missing-evidence'||!state.nextCases.length)throw Error('The verified question has no selectable missing work.');
  const first=domain.programs.findIndex(p=>p.id===state.nextCases[0].programId);if(first<0)throw Error('The next verified case changed its declared program.');
  const alphabet=new Set(domain.alphabet.map(r=>r.rune)),sizes=new Map(),limits=Groups.LIMITS,requests=[];for(const page of domain.pages){let runes=0,chars=0;for(const char of page.text){chars++;if(alphabet.has(char))runes++;}sizes.set(page.id,{chars,runes});}let runes=0,chars=0,cases=0,finished=false;
  for(let pi=first;pi<domain.programs.length&&!finished&&requests.length<limits.groups;pi++){
   const program=domain.programs[pi],missing=new Set();
   for(let offset=0;offset<domain.pages.length;offset+=12){const refs=(await Q.cases(domain,{cursor:pi*domain.pages.length+offset,limit:Math.min(12,domain.pages.length-offset)},crypto)).cases;state=check();if(state.decision.state==='answered')return null;const coverage=await authority.coverage(refs);state=check();if(state.decision.state==='answered')return null;const ids=new Set(coverage.missingCaseIds);for(const ref of refs)if(ids.has(ref.id))missing.add(ref.pageId);}
   const pageIds=[];for(const page of domain.pages){if(!missing.has(page.id))continue;const size=sizes.get(page.id);if(cases===limits.cases||runes+size.runes>limits.runes||chars+size.chars>limits.inputChars){if(!cases)throw Error('The next page exceeds a bounded grouped calculation. Review an ordinary small batch.');finished=true;break;}pageIds.push(page.id);cases++;runes+=size.runes;chars+=size.chars;}
   if(pageIds.length)requests.push({programId:program.id,pageIds});
  }
  if(!requests.length)throw Error('The verified missing work changed. Refresh saved evidence.');
  const build=groups=>Groups.select({compiled:input.compiled,card:input.card,bundle:input.bundle,groups},crypto);
  let selection;try{selection=await build(requests);}catch(error){
   // Work and identity failures are never repaired. Only an ordinary task byte
   // bound can shorten THIS batch's canonical prefix; the question stays whole.
   if(!/exceed.*(?:byte budget)/.test(error.message))throw error;
   const prefix=n=>{const out=[];for(const request of requests){if(!n)break;const pageIds=request.pageIds.slice(0,n);out.push({programId:request.programId,pageIds});n-=pageIds.length;}return out;};
   let low=1,high=cases-1;while(low<=high){const mid=Math.floor((low+high)/2);try{const candidate=await build(prefix(mid));selection=candidate;low=mid+1;}catch(e){if(!/exceed.*(?:byte budget)/.test(e.message))throw e;high=mid-1;}state=check();if(state.decision.state==='answered')return null;}
   if(!selection)throw Error('The next whole page exceeds the grouped task byte bound. Review an ordinary small batch.');
  }
  state=check();return state.decision.state==='answered'?null:selection;
 }
 const api={select};if(node)module.exports=api;else root.FactoredNextPageGroups=api;
})(typeof globalThis!=='undefined'?globalThis:this);
