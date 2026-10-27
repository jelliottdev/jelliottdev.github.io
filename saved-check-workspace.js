/* Read-only inspection of one saved computation associated with a public question. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,Client=node?require('./saved-check-client.js'):root.SavedCheckClient,View=node?require('./saved-check-view.js'):root.SavedCheckView,J=node?require('./finite-json.js'):root.FiniteJSON;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function mount(initialHost,options={}){
  const tasks=J.capture(options.tasks||[],{maxBytes:2*1024*1024,maxDepth:24,maxNodes:300000}),seen=new Set(),available=(Array.isArray(tasks)?tasks:[]).filter(t=>t&&typeof t.id==='string'&&/^[a-f0-9]{64}$/.test(t.id)&&t.state==='results-verified'&&!seen.has(t.id)&&(seen.add(t.id),true)),saved=available.slice(0,10),truncated=options.tasksTruncated===true||available.length>saved.length;
  let host=null,dead=false,generation=0,controller=null,client=null,phase='empty',selected=saved[0]?.id||null,value=null,unbind=()=>{};
  const live=token=>!dead&&token===generation&&options.isLive?.()!==false&&!options.signal?.aborted;
  function draw(){
   if(!host||!live(generation))return;const outgoing=host.querySelector?.('[data-saved-check-select]'),restoreFocus=!!outgoing&&outgoing.ownerDocument?.activeElement===outgoing;unbind();
   if(!saved.length){host.innerHTML='';unbind=()=>{};return;}
   const picker=saved.length>1?'<label class="saved-check-picker">Saved computation <select data-saved-check-select>'+saved.map((t,i)=>'<option value="'+t.id+'"'+(t.id===selected?' selected':'')+'>Saved check '+(i+1)+(typeof t.title==='string'&&t.title?' — '+esc(t.title):'')+'</option>').join('')+'</select></label>':'';
   host.innerHTML=picker+(phase==='ready'?View.render(value.proof,value):View.renderState(phase))+(phase==='error'?'<button type="button" class="saved-check-retry" data-saved-check-retry>Try again</button>':'')+(truncated?'<p class="saved-check-state">Only part of this question’s saved computations is shown here.</p>':'');
   const select=host.querySelector?.('[data-saved-check-select]'),retry=host.querySelector?.('[data-saved-check-retry]'),change=()=>{if(saved.some(t=>t.id===select.value)&&selected!==select.value){selected=select.value;void load();}},again=()=>{void load();};
   select?.addEventListener('change',change);retry?.addEventListener('click',again);unbind=()=>{select?.removeEventListener('change',change);retry?.removeEventListener('click',again);};if(restoreFocus)select?.focus?.();
  }
  async function load(){
   if(!selected||dead||options.signal?.aborted||options.isLive?.()===false)return;
   controller?.abort();const token=++generation;controller=new AbortController();const request=controller;phase='loading';value=null;draw();
   try{
    if(!client)client=Client.create({endpoint:options.endpoint,pageURL:options.pageURL||root.location?.href||'',...(options.fetcher?{fetcher:options.fetcher}:{}),...(options.crypto?{crypto:options.crypto}:{})});
    const result=await client.read({taskId:selected,proposalId:options.ideaId,card:options.card,signal:request.signal});
    if(!live(token)||request.signal.aborted)return;value=result;phase=result?'ready':'empty';
   }catch{if(!live(token)||request.signal.aborted)return;phase='error';value=null;}
   finally{if(live(token)&&!request.signal.aborted)draw();}
  }
  function attach(next){if(dead)return;unbind();if(host&&host!==next)host.innerHTML='';host=next;unbind=()=>{};draw();}
  function destroy(){if(dead)return;dead=true;generation++;controller?.abort();unbind();options.signal?.removeEventListener('abort',destroy);if(host)host.innerHTML='';host=null;value=null;}
  options.signal?.addEventListener('abort',destroy,{once:true});
  if(options.signal?.aborted)destroy();else attach(initialHost);
  const ready=dead||!saved.length?Promise.resolve():load();
  return Object.freeze({ready,attach,destroy});
 }
 const api=Object.freeze({mount});if(node)module.exports=api;else root.SavedCheckWorkspace=api;
})(typeof globalThis!=='undefined'?globalThis:this);
