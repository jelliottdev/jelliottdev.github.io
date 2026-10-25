/* Lazy, bounded evidence lookup for an open contribution chooser. No writes. */
(function(root){
 'use strict';
 function create({load,fetcher=root.fetch?.bind(root),pageURL=root.location?.href,limit=2}={}){
  if(typeof load!=='function'||!Number.isInteger(limit)||limit<1||limit>2)throw Error('Current-work lookup is unavailable.');
  const queue=[],controllers=new Set(),shared=new Map(),abort=new AbortController();let active=0,closed=false;
  function source(path){
   if(shared.has(path))return shared.get(path);
   const pending=(async()=>{const response=await fetcher(path,{cache:'no-store',signal:AbortSignal.any([abort.signal,AbortSignal.timeout(20000)])});if(!response.ok)throw Error('Source is unavailable.');const text=await response.text();if(new TextEncoder().encode(text).length>2*1024*1024)throw Error('Source exceeds its bound.');return JSON.parse(text);})();
   shared.set(path,pending);pending.catch(()=>{if(shared.get(path)===pending)shared.delete(path);});return pending;
  }
  function drain(){while(!closed&&active<limit&&queue.length){const job=queue.shift();active++;Promise.resolve().then(job).catch(()=>{}).finally(()=>{active--;drain();});}}
  function createReadiness({record,check,onState}){
   let dead=false,controller=null,pending=null;
   const emit=value=>{if(!dead&&!closed)onState(value);};
   function start(retry=false){
    if(dead||closed)return Promise.resolve(null);if(pending)return pending;
    emit({state:'loading'});
    pending=new Promise(resolve=>{queue.push(async()=>{try{
     if(dead||closed)return resolve(null);
     const tools=await load();if(dead||closed)return resolve(null);
     if(!controller)controller=tools.createController({record,check,onState:emit,fetcher,pageURL,loadConfig:()=>source('data/assistant.json'),loadInputs:()=>source('data/local-run-inputs.json')});
     resolve(await (retry?controller.retry():controller.activate()));
    }catch{emit({state:'unavailable'});resolve(null);}finally{pending=null;}});drain();});return pending;
   }
   const wrapper={activate:()=>start(),retry:()=>start(true),destroy(){dead=true;controller?.destroy();controllers.delete(wrapper);}};
   controllers.add(wrapper);return wrapper;
  }
  return {createReadiness,destroy(){closed=true;abort.abort();for(const c of controllers)c.destroy();controllers.clear();shared.clear();for(const job of queue.splice(0))void job();}};
 }
 const api={create};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchHelpRuntime=api;
})(typeof globalThis!=='undefined'?globalThis:this);
