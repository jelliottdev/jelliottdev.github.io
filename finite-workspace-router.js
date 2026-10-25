/* Choose a complete finite-search implementation without changing the question. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,Legacy=node?require('./finite-search-workspace.js'):root.FiniteSearchWorkspace,Full=node?require('./factored-finite-workspace.js'):root.FactoredFiniteWorkspace,SmallCompiler=node?require('./finite-search-compiler.js'):root.FiniteSearchCompiler,FullCompiler=node?require('./factored-finite-search-compiler.js'):root.FactoredFiniteSearchCompiler,J=node?require('./finite-json.js'):root.FiniteJSON,Evaluators=node?require('./output-evaluators.js'):root.OutputEvaluators;
 const actions=['prepare','run','save','cancel','inspect','download','downloadPart','restoreLocal','discardLocal','reviewRemaining','startRemaining','pauseRemaining','resumeRemaining'];
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function createWorkspace(doc,host,options){
  const idea=J.capture(options.idea,{maxBytes:128*1024,maxDepth:24,maxNodes:12000}),controller=new AbortController();let child=null,dead=false,generation=0,phase='loading',error='',route=null,loading=null;
  const live=token=>{if(dead||generation!==token||options.isLive&&!options.isLive())throw new DOMException('Navigation changed.','AbortError');};
  const prefixReuse=()=>typeof options.config?.factoredPrefixSearchEndpoint==='string'&&typeof options.validEndpoint==='function'&&options.validEndpoint(options.config?.factoredPrefixSearchEndpoint,'factored-prefix-search');
  const outputRequested=()=>idea.card?.rules?.evaluation?.status==='specified'&&idea.card.rules.evaluation.value?.kind==='language-score';
  const outputEnabled=()=>outputRequested()&&Evaluators.identify(idea.card.rules.evaluation.value)&&typeof options.validEndpoint==='function'&&options.validEndpoint(options.config?.factoredOutputSearchEndpoint,'factored-output-search');
  const expanded=()=>outputEnabled()||prefixReuse()||typeof options.validEndpoint==='function'&&options.validEndpoint(options.config?.factoredSearchEndpoint,'factored-search');
  function draw(){if(dead||child)return;host.innerHTML='<section class="finite-workspace" aria-live="polite">'+(error?'<p role="alert">'+esc(error)+'</p><button type="button" data-finite-router-retry>Retry</button>':'<p>Checking the complete search...</p>')+'</section>';}
  async function load(){if(dead)throw new DOMException('Navigation changed.','AbortError');if(child)return child.reload?.();if(loading)return loading;const token=generation;phase='loading';error='';draw();const operation=(async()=>{await Promise.resolve();try{
    if(outputRequested()&&!outputEnabled())throw Error('The pinned language comparison is not available here yet. No settings or pages were omitted.');
    if(!expanded()){route='legacy';child=Legacy.createWorkspace(doc,host,{...options,idea});await child.ready;live(token);phase='ready';return;}
    const response=await options.request('data/local-run-inputs.json',{signal:controller.signal},15000);live(token);if(!response.ok)throw Error('The manuscript inputs could not be loaded. Please retry.');const bundle=await Legacy.readJSON(response,2*1024*1024);live(token);let precompiled;
    if(outputEnabled()){precompiled=await FullCompiler.compileLanguageComparison(idea.card,bundle,options.crypto||root.crypto);route='output';}else if(prefixReuse()){precompiled=await FullCompiler.compile(idea.card,bundle,options.crypto||root.crypto);route='factored';}else try{precompiled=await SmallCompiler.compile(idea.card,bundle,options.crypto||root.crypto);route='legacy';}catch(smallError){live(token);precompiled=await FullCompiler.compile(idea.card,bundle,options.crypto||root.crypto);route='factored';}
    live(token);const factory=route==='legacy'?Legacy:Full;child=(route==='output'?Full.createOutputWorkspace:factory.createWorkspace)(doc,host,{...options,idea,precompiled,sourceBundle:bundle});await child.ready;live(token);phase='ready';
   }catch(e){if(!dead&&generation===token){phase='error';error=String(e.message||'This search could not be loaded.');draw();}throw e;}finally{if(loading===operation)loading=null;}})();loading=operation;operation.catch(()=>{});return operation;
  }
  function click(event){const button=event.target?.closest?.('[data-finite-router-retry]');if(button&&host.contains(button)&&!child)void load().catch(()=>{});}
  host.addEventListener('click',click);const api={ready:null,reload:load,getState:()=>child?child.getState():{phase,error,route},destroy(){if(dead)return;dead=true;generation++;controller.abort();child?.destroy();host.removeEventListener('click',click);}};for(const action of actions)api[action]=(...args)=>{if(dead)throw new DOMException('Navigation changed.','AbortError');if(!child)throw Error('Wait for the complete search to load.');if(typeof child[action]!=='function')throw Error('This action is not available for this search.');return child[action](...args);};api.ready=load();api.ready.catch(()=>{});return api;
 }
 const api={createWorkspace};if(node)module.exports=api;else root.FiniteWorkspaceRouter=api;
})(typeof globalThis!=='undefined'?globalThis:this);
