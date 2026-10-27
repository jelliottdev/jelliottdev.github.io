/* A generated method is a proposal to review, never an execution permission. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,MD=node?require('./method-design.js'):root.MethodDesign,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare;
 const LIMITS=Object.freeze({bytes:24*1024,timeoutMs:20000}),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),need=(v,m)=>{if(!v)throw Error(m);};
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 function pages(ids){const out=[];for(let i=0;i<ids.length;i++){const start=ids[i];let end=start;while(i+1<ids.length&&ids[i+1].slice(0,4)===start.slice(0,4)&&Number(ids[i+1].slice(4))===Number(end.slice(4))+1)end=ids[++i];out.push(start.toUpperCase()+(end===start?'':'–'+end.slice(4)));}return out.join(', ');}
 function endpoint(value,pageURL){const url=new URL(value);need(!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname==='/design-method','Use the configured method drafting service.');if(url.protocol!=='https:'){const page=new URL(pageURL);need(url.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&page.origin===url.origin,'Use HTTPS or the same local service.');}return url.href;}
 async function relatedIds(value){try{const resolved=await(typeof value==='function'?value():value),ids=J.capture(resolved,{maxBytes:1024,maxDepth:2,maxNodes:10});return Array.isArray(ids)&&ids.length<=4&&new Set(ids).size===ids.length&&ids.every(id=>typeof id==='string'&&id.length<=100&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))?ids:[];}catch{return [];}}
 function mount(initialHost,options={}){
  const crypto=options.crypto||root.crypto,fetcher=options.fetcher||root.fetch?.bind(root),parentId=options.parentId;
  let host=initialHost,dead=false,generation=0,controller=null,phase='idle',proposal=null,error='',parentCard=null,cardSha256=null,service=null,unbind=()=>{};
  const live=token=>!dead&&generation===token&&!options.signal?.aborted&&options.isLive?.()!==false;
  function draw(){
   if(!host||!live(generation))return;unbind();let body;
   if(proposal){
    const key=proposal.keyUse?.kind==='proposed'?'<dl class="method-design-facts"><div><dt>Key material</dt><dd>'+esc(proposal.keyUse.material)+'</dd></div><div><dt>How it is applied</dt><dd>'+esc(proposal.keyUse.application)+'</dd></div></dl>':'<p>No key used.</p>';
    body='<h2>'+esc(proposal.name)+'</h2><p class="method-design-note">Proposed method — review before preparing any check.</p><p>'+esc(proposal.hypothesis)+'</p><h3>Key</h3>'+key+'<h3>What to do</h3><ol>'+proposal.steps.map(step=>'<li>'+esc(step)+'</li>').join('')+'</ol><dl class="method-design-facts"><div><dt>Pages</dt><dd>'+esc(pages(proposal.pages))+'</dd></div><div><dt>Transcription</dt><dd>'+esc(proposal.inputVersion==='raw'?'Raw':'Reviewed')+'</dd></div><div><dt>Representation</dt><dd>'+esc(proposal.representation)+'</dd></div></dl>'+(proposal.parameters.length?'<h3>Conditions</h3><dl class="method-design-facts">'+proposal.parameters.map(item=>'<div><dt>'+esc(item.name)+'</dt><dd>'+item.values.map(esc).join('; ')+'</dd></div>').join('')+'</dl>':'')+'<h3>What would count</h3><p>'+esc(proposal.evaluation)+'</p><h3>Proposed controls</h3><p class="method-design-note">These checks have not been validated.</p><ul>'+proposal.controls.map(value=>'<li>'+esc(value)+'</li>').join('')+'</ul><h3>Assumptions to review</h3><ul>'+proposal.assumptions.map(value=>'<li>'+esc(value)+'</li>').join('')+'</ul><p class="method-design-note">Reviewing does not save or run this method.</p>';
   }else body='<p>Turn this idea into a specific test. Nothing is saved or run.</p>';
   if(error)body+='<p class="method-design-error" role="alert">'+esc(error)+'</p>';
   body+=phase==='loading'?'<p role="status" aria-live="polite">Drafting a method…</p><button type="button" data-method-design="cancel">Cancel</button>':proposal?'<button type="button" data-method-design="review"'+(phase==='reviewing'?' disabled aria-busy="true"':'')+'>'+(phase==='reviewing'?'Opening review…':'Review method')+'</button>':'<button type="button" data-method-design="draft">'+(phase==='error'?'Retry draft':'Develop this idea')+'</button>';
   host.innerHTML='<section class="method-design" aria-label="Develop this idea"'+(phase==='loading'?' aria-busy="true"':'')+'>'+body+'</section>';
   const removers=[];for(const button of host.querySelectorAll?.('[data-method-design]')||[]){const action=button.getAttribute('data-method-design'),fn=()=>action==='draft'?draft():action==='cancel'?cancel():review();button.addEventListener('click',fn);removers.push(()=>button.removeEventListener('click',fn));}unbind=()=>removers.forEach(remove=>remove());
  }
  async function validateParent(){
   need(typeof parentId==='string'&&/^p_[a-f0-9]{64}$/.test(parentId)&&crypto?.subtle&&typeof fetcher==='function','The saved question could not be verified.');
   const snapshot=J.capture(options.card,{maxBytes:20*1024,maxDepth:24,maxNodes:10000}),bytes=new TextEncoder().encode(JSON.stringify(snapshot));let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
   const card=H.readCard('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''));need(C.serialize(card)===C.serialize(snapshot),'The saved question changed its canonical wording.');
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(card))))).map(b=>b.toString(16).padStart(2,'0')).join('');need(parentId==='p_'+digest,'The saved question changed its identity.');
   parentCard=freeze(card);cardSha256=digest;service=endpoint(options.endpoint,options.pageURL||root.location?.href||'');
  }
  async function draft(){
   if(phase==='loading'||phase==='reviewing'||!live(generation))return;const token=++generation;phase='loading';error='';draw();controller?.abort();const request=new AbortController();controller=request;let reader,rejectAbort;
   const stop=()=>{try{void reader?.cancel().catch(()=>{});}catch{}rejectAbort?.(Error('Draft request cancelled.'));},cancelled=new Promise((_,reject)=>{rejectAbort=reject;request.signal.addEventListener('abort',stop,{once:true});}),timer=setTimeout(()=>request.abort(),LIMITS.timeoutMs);
   const work=async()=>{await ready;need(parentCard&&service,'The saved question or drafting service could not be verified.');if(!live(token)||request.signal.aborted)return;
    const ids=await relatedIds(options.relatedIds);if(!live(token)||request.signal.aborted)return;const body=JSON.stringify({parentId,card:parentCard,...(ids.length?{relatedIds:ids}:{})});need(new TextEncoder().encode(body).length<=LIMITS.bytes,'The question is too long for this draft request.');
    const response=await fetcher(service,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body,credentials:'omit',redirect:'error',cache:'no-store',signal:request.signal});
    need(live(token)&&!request.signal.aborted,'Draft request cancelled.');need(!response.redirected&&(!response.url||response.url===service),'The drafting response changed location.');need(response.ok,response.status===429?'The drafting service is busy. Please try again shortly.':'The drafting service is unavailable. Please try again.');need(/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The drafting response could not be verified.');
    const length=response.headers.get('content-length');need(length===null||/^\d+$/.test(length)&&Number(length)<=LIMITS.bytes,'The drafting response is too large.');reader=response.body?.getReader();need(reader,'The drafting response could not be read.');let size=0;const chunks=[];
    for(;;){const part=await reader.read();need(live(token)&&!request.signal.aborted,'Draft request cancelled.');if(part.done)break;size+=part.value.byteLength;need(size<=LIMITS.bytes,'The drafting response is too large.');chunks.push(part.value);}
    const raw=new Uint8Array(size);let at=0;for(const chunk of chunks){raw.set(chunk,at);at+=chunk.byteLength;}
    const value=J.capture(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)),{maxBytes:LIMITS.bytes,maxDepth:12,maxNodes:5000});need(value&&Object.keys(value).length===4&&['schema','parentId','cardSha256','proposal'].every(k=>Object.hasOwn(value,k))&&value.schema==='liberpedia-method-design-response-v1'&&value.parentId===parentId&&value.cardSha256===cardSha256,'The draft does not belong to this saved question.');return MD.validate(value.proposal);
   };
   try{const result=await Promise.race([work(),cancelled]);if(live(token)&&!request.signal.aborted){proposal=result;phase='draft';}}
   catch(e){if(live(token)&&!request.signal.aborted){phase='error';error=e.message;}else if(live(token)){phase='error';error='The draft request timed out. Please try again.';}}
   finally{clearTimeout(timer);request.signal.removeEventListener('abort',stop);request.abort();if(live(token))draw();}
  }
  function cancel(){generation++;controller?.abort();phase=proposal?'draft':'idle';error='';draw();}
  async function review(){if(!proposal||phase==='reviewing'||!live(generation)||typeof options.onReview!=='function')return;const token=generation;phase='reviewing';error='';draw();try{await options.onReview(proposal);if(live(token))phase='draft';}catch{if(live(token)){phase='draft';error='The method could not be opened for review. Please try again.';}}finally{if(live(token))draw();}}
  function attach(next){if(dead)return;unbind();if(host&&host!==next)host.innerHTML='';host=next;draw();}
  function destroy(){if(dead)return;dead=true;generation++;controller?.abort();unbind();options.signal?.removeEventListener('abort',destroy);if(host)host.innerHTML='';host=null;}
  const ready=validateParent().catch(()=>{if(live(generation)){phase='error';error='The saved question or drafting service could not be verified.';draw();}});
  options.signal?.addEventListener('abort',destroy,{once:true});if(options.signal?.aborted)destroy();else draw();
  return Object.freeze({ready,attach,destroy,getState:()=>Object.freeze({phase,proposal,error,loading:phase==='loading'})});
 }
 const api=Object.freeze({mount,LIMITS});if(node)module.exports=api;else root.MethodDesignWorkspace=api;
})(typeof globalThis!=='undefined'?globalThis:this);
