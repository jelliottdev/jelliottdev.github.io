/* Shared receipt verification for exact computation coverage. No target execution or writes. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,Evidence=node?require('./computation-evidence.js'):root.ComputationEvidence;
 const HEX=/^[a-f0-9]{64}$/,MAX=2*1024*1024;
 async function readJSON(response){
  if(!response||response.ok===false)throw Error('The saved evidence response is unavailable.');
  const length=response.headers?.get?.('content-length');if(length!==undefined&&length!==null&&(!/^\d+$/.test(length)||Number(length)>MAX))throw Error('The saved evidence response exceeds its bound.');
  const reader=response.body?.getReader?.();
  if(reader){
   const chunks=[];let size=0;
   try{while(true){const {done,value}=await reader.read();if(done)break;if(!ArrayBuffer.isView(value)||value.BYTES_PER_ELEMENT!==1)throw Error('The saved evidence response is unreadable.');size+=value.byteLength;if(size>MAX)throw Error('The saved evidence response exceeds its bound.');chunks.push(value);}}
   catch(error){try{await reader.cancel();}catch{}throw error;}
   finally{reader.releaseLock?.();}
   const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
   return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  }
  // Injectable transports may provide parsed JSON rather than a native Response.
  // Native fetch bodies always take the bounded streaming path above.
  if(typeof response.text==='function'){const text=await response.text();if(new TextEncoder().encode(text).length>MAX)throw Error('The saved evidence response exceeds its bound.');return JSON.parse(text);}
  if(typeof response.json==='function'){const value=await response.json();if(new TextEncoder().encode(E.stable(value)).length>MAX)throw Error('The saved evidence response exceeds its bound.');return value;}
  throw Error('The saved evidence response is unreadable.');
 }
 async function digest(value,cryptoAPI,serialize=E.stable){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(serialize(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 async function receipt(task,run,cryptoAPI){if(!run||!HEX.test(run.id)||!Number.isFinite(Date.parse(run.createdAt)))throw Error('The saved result receipt is invalid.');const result=await E.verify(task,run.result,cryptoAPI);if(await digest(result,cryptoAPI)!==run.id)throw Error('The saved result receipt does not match its computation.');return {...run,result};}
 async function sourceProjection(value,id,cryptoAPI){
  if(!value||value.id!==id||value.plan?.taskId!==id||!HEX.test(id)||value.state!=='results-verified'||!['raw','reviewed'].includes(value.inputVersion)||value.title!==value.plan.title||!value.latestRun)throw Error('The saved source identity or result state is invalid.');
  await E.checkIdentity(value.plan,cryptoAPI);return {...value,latestRun:await receipt(value.plan,value.latestRun,cryptoAPI)};
 }
 function create({request,endpoint,validEndpoint,crypto:cryptoAPI=root.crypto,projection=sourceProjection,taskLink=id=>'run.html#task='+id,pageLabel=pages=>pages.map(p=>p.id.toUpperCase()).join(', ')}={}){
  if(typeof request!=='function'||typeof validEndpoint!=='function')throw Error('Verified evidence needs a configured transport.');const cache=new WeakMap();
  async function checkCoverage(value,{inputVersion,isLive=()=>true}={}){
   const keys=['requestedTask','inputVersion','coveredPages','remainingPages','evidence','exactTaskId','truncated',...(Object.hasOwn(value||{},'familySources')?['familySources']:[]),...(Object.hasOwn(value||{},'publishedSources')?['publishedSources']:[])];
   if(!Evidence?.compare||!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k))||!['raw','reviewed'].includes(value.inputVersion)||(inputVersion!==undefined&&inputVersion!==value.inputVersion)||typeof value.truncated!=='boolean'||!Array.isArray(value.evidence)||value.evidence.length>75||!validEndpoint(endpoint,'tasks'))throw Error('The saved computation coverage could not be verified.');
   await E.checkIdentity(value.requestedTask,cryptoAPI);if(!isLive())throw new DOMException('Navigation changed.','AbortError');
   const sources=[],titles={},links={},familySources=new Map(),familyCases=new Set(),publishedSources=new Map(),publishedCases=new Set(),referenced=new Set(value.evidence.map(item=>item?.taskId));
   if(Object.hasOwn(value,'familySources')){
    if(!Array.isArray(value.familySources)||value.familySources.length>value.evidence.length)throw Error('The family evidence references are invalid.');
    for(const ref of value.familySources){
     const fields=['taskId','familyId','revision','caseId'];
     if(!ref||typeof ref!=='object'||Array.isArray(ref)||Object.keys(ref).length!==fields.length||fields.some(key=>!Object.hasOwn(ref,key))||!HEX.test(ref.taskId)||typeof ref.familyId!=='string'||!/^[a-z][a-z0-9-]{0,99}$/.test(ref.familyId)||!HEX.test(ref.revision)||typeof ref.caseId!=='string'||!/^[a-z][a-z0-9-]{0,199}$/.test(ref.caseId)||!referenced.has(ref.taskId)||familySources.has(ref.taskId))throw Error('The family evidence mapping is invalid.');
     const key=ref.familyId+'|'+ref.revision+'|'+ref.caseId;if(familyCases.has(key))throw Error('A family evidence case is repeated.');familyCases.add(key);familySources.set(ref.taskId,ref);
    }
   }
   if(Object.hasOwn(value,'publishedSources')){
    if(!Array.isArray(value.publishedSources)||value.publishedSources.length>value.evidence.length)throw Error('The published count references are invalid.');
    for(const ref of value.publishedSources){
     const fields=['taskId','resultId','recordId','revision','caseId'];
     if(!ref||typeof ref!=='object'||Array.isArray(ref)||Object.keys(ref).length!==fields.length||fields.some(key=>!Object.hasOwn(ref,key))||!HEX.test(ref.taskId)||!HEX.test(ref.resultId)||!HEX.test(ref.revision)||typeof ref.recordId!=='string'||ref.recordId.length>100||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(ref.recordId)||typeof ref.caseId!=='string'||ref.caseId.length>200||!/^[a-z0-9][a-z0-9-]*$/.test(ref.caseId)||!referenced.has(ref.taskId)||familySources.has(ref.taskId)||publishedSources.has(ref.taskId))throw Error('The published count mapping is invalid.');
     const key=ref.recordId+'|'+ref.revision+'|'+ref.caseId;if(publishedCases.has(key))throw Error('A published count projection is repeated.');publishedCases.add(key);publishedSources.set(ref.taskId,ref);
    }
   }
   for(let offset=0;offset<value.evidence.length;offset+=4){
    const batch=await Promise.all(value.evidence.slice(offset,offset+4).map(async item=>{
     if(!item||!HEX.test(item.taskId)||!HEX.test(item.resultId))throw Error('The saved computation evidence is invalid.');
     const published=publishedSources.get(item.taskId);
     if(published){
      if(item.resultId!==published.resultId)throw Error('The published count receipt differs from its source reference.');
      const base=new URL(endpoint).origin,path='/published-evidence/'+encodeURIComponent(published.recordId)+'/'+encodeURIComponent(published.caseId),response=await readJSON(await request(base+path+'?revision='+published.revision));
      const fields=['task','inputVersion','run','publishedSource','provenance'];
      if(!response||typeof response!=='object'||Array.isArray(response)||Object.keys(response).length!==fields.length||fields.some(key=>!Object.hasOwn(response,key))||E.stable(response.publishedSource)!==E.stable(published)||response.task?.taskId!==item.taskId||response.inputVersion!=='raw'||response.run?.id!==item.resultId)throw Error('The published count response changed its identity.');
      const p=response.provenance,projection=p?.projection;
      if(!p||E.stable(Object.keys(p).sort())!==E.stable(['schema','recordId','projection','sourcePins','checkedAt','dateMeaning','expectationMeaning'].sort())||p.schema!=='liberpedia-published-count-projection-v1'||p.recordId!==published.recordId||await digest(p,cryptoAPI)!==published.revision||typeof p.checkedAt!=='string'||!Number.isFinite(Date.parse(p.checkedAt))||response.run.createdAt!==p.checkedAt||!['dateMeaning','expectationMeaning'].every(key=>typeof p[key]==='string'&&p[key].trim()&&p[key].length<=1200)||!projection||E.stable(Object.keys(projection).sort())!==E.stable(['id','criterion','pages','alphabetSha256','taskId','resultId'].sort())||typeof projection.id!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(projection.id)||published.caseId!==projection.id+'--all-pages'||projection.taskId!==item.taskId||projection.resultId!==item.resultId||projection.criterion?.kind!=='word-affine-count'||response.task.steps.length||E.stable(projection.criterion)!==E.stable(response.task.criterion)||E.stable(projection.pages)!==E.stable(response.task.pages.map(page=>page.id))||await digest(response.task.alphabet,cryptoAPI)!==projection.alphabetSha256)throw Error('The published count provenance could not be verified.');
      if(!Array.isArray(p.sourcePins)||p.sourcePins.length>100||p.sourcePins.some((pin,i)=>!pin||Object.keys(pin).length!==2||typeof pin.path!=='string'||!HEX.test(pin.sha256)||i&&p.sourcePins[i-1].path>=pin.path))throw Error('The published input pins are invalid.');
      for(const page of response.task.pages){const pin=p.sourcePins.find(pin=>pin.path==='text/'+page.id+'.txt');if(!pin||await digest(page.text,cryptoAPI,v=>v)!==pin.sha256)throw Error('A published count input changed.');}
      const run=await receipt(response.task,response.run,cryptoAPI);titles[item.taskId]='Published count check · '+pageLabel(response.task.pages);links[item.taskId]='library.html#/experiment/'+encodeURIComponent(published.recordId);
      return {task:response.task,inputVersion:response.inputVersion,run};
     }
     const ref=familySources.get(item.taskId);
     if(ref){
      const base=new URL(endpoint).origin,path='/families/'+encodeURIComponent(ref.familyId)+'/cases/'+encodeURIComponent(ref.caseId),response=await readJSON(await request(base+path+'?revision='+ref.revision)),fields=['familyId','revision','caseId','task','result','resultId','verifiedAt'];
      if(!response||typeof response!=='object'||Array.isArray(response)||Object.keys(response).length!==fields.length||fields.some(key=>!Object.hasOwn(response,key))||response.familyId!==ref.familyId||response.revision!==ref.revision||response.caseId!==ref.caseId||response.task?.taskId!==item.taskId||!HEX.test(response.resultId)||response.resultId!==item.resultId||typeof response.verifiedAt!=='string'||!Number.isFinite(Date.parse(response.verifiedAt)))throw Error('The family result does not match its saved reference.');
      const result=await E.verify(response.task,response.result,cryptoAPI),mode=response.task.steps.find(step=>step.op==='keyed-shift')?.mode,label=ref.familyId==='deor-feedback-v1'?({repeat:'Repeating DEOR key','plaintext-autokey':'DEOR plaintext autokey','ciphertext-autokey':'DEOR ciphertext autokey'}[mode]):null;titles[item.taskId]=label&&response.task.pages.length===1?response.task.pages[0].id.toUpperCase()+' · '+label:response.task.title;links[item.taskId]='run.html#family='+encodeURIComponent(ref.familyId)+'&case='+encodeURIComponent(ref.caseId)+'&revision='+ref.revision;
      return {task:response.task,inputVersion:'raw',run:{id:response.resultId,createdAt:response.verifiedAt,result}};
     }
     const response=await readJSON(await request(endpoint+'/'+item.taskId)),source=await projection(response,item.taskId,cryptoAPI);
     if(!source.latestRun)throw Error('The source computation has no saved result.');titles[item.taskId]=source.title;links[item.taskId]=taskLink(item.taskId);
     return {task:source.plan,inputVersion:source.inputVersion,run:source.latestRun};
    }));sources.push(...batch);if(!isLive())throw new DOMException('Navigation changed.','AbortError');
   }
   const compared=await Evidence.compare(value.requestedTask,value.inputVersion,sources,cryptoAPI);
   for(const name of ['coveredPages','remainingPages','evidence','exactTaskId'])if(E.stable(value[name])!==E.stable(compared[name]))throw Error('The saved evidence does not cover the stated pages and settings.');
   if(!isLive())throw new DOMException('Navigation changed.','AbortError');const verified={...value,titles,links};cache.set(verified,sources);return verified;
  }
  return {checkCoverage,getSources(value){if(!cache.has(value))throw Error('Computation coverage has not been independently checked.');return cache.get(value);}};
 }
 const api={create};if(node)module.exports=api;else root.VerifiedEvidenceClient=api;
})(typeof globalThis!=='undefined'?globalThis:this);
