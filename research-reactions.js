/* Interest signals and browser-local bookmarks; neither is research evidence. */
(function(root){
 'use strict';
 const validId=id=>typeof id==='string'&&id.length<=100&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)&&(!id.startsWith('idea-')||/^idea-[a-f0-9]{64}$/.test(id));
 function endpoint(config,pageURL){
  try{
   const page=new URL(pageURL),url=new URL(config.upvoteEndpoint),worker=new URL(config.endpoint);
   if(url.username||url.password||url.search||url.hash||url.pathname!=='/upvotes'||worker.username||worker.password||worker.search||worker.hash||worker.pathname!=='/ask'||url.origin!==worker.origin)return null;
   if(url.protocol==='https:'&&worker.protocol==='https:')return url.href;
   if(page.protocol==='http:'&&['localhost','127.0.0.1'].includes(page.hostname)&&url.origin===page.origin)return url.href;
  }catch{}return null;
 }
 const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 11 7-7 7 7M12 4v16"/></svg>',bookmark='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4Z"/></svg>';
 function create({preferences,fetcher=root.fetch?.bind(root),loadConfig,pageURL=root.location?.href,onChange=()=>{}}={}){
  if(!preferences||typeof fetcher!=='function'||typeof loadConfig!=='function')throw Error('Research reactions are unavailable');
  const counts=new Map(),mounted=new Set(),votes=new Map(),errors=new Map(),queue=[],inflight=new Map(),lastReads=new Map();let alive=true,configPromise=null,running=0;
  const notify=()=>{if(!alive)return;for(const mount of mounted)mount.render();onChange();};
  const remember=(id,count)=>{counts.delete(id);counts.set(id,count);while(counts.size>2000)counts.delete(counts.keys().next().value);};
  const pump=()=>{while(alive&&running<2&&queue.length){const item=queue.shift();running++;Promise.resolve().then(item.work).then(item.resolve,item.reject).finally(()=>{running--;pump();});}};
  const enqueue=work=>new Promise((resolve,reject)=>{queue.push({work,resolve,reject});pump();});
  async function json(url,options,limit){
   const controller=new AbortController();let timer;
   try{return await Promise.race([(async()=>{const response=await fetcher(url,{...options,signal:controller.signal});if(!response.ok)throw Error('Request failed');
    const length=response.headers?.get?.('Content-Length');if(length!==null&&length!==undefined&&(!/^\d+$/.test(length)||Number(length)>limit))throw Error('Response too large');
    let text;if(response.body?.getReader){const reader=response.body.getReader(),chunks=[];let size=0;try{while(true){const part=await reader.read();if(part.done)break;size+=part.value.byteLength;if(size>limit){await reader.cancel();throw Error('Response too large');}chunks.push(part.value);}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);}finally{reader.releaseLock();}}
    else{if(typeof response.text!=='function')throw Error('Invalid response');text=await response.text();if(text.length>limit||new TextEncoder().encode(text).length>limit)throw Error('Response too large');}return JSON.parse(text);
   })(),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Request timed out'));},10000);})]);}finally{clearTimeout(timer);}
  }
  const service=async()=>{if(!configPromise)configPromise=(async()=>{let timer;try{const config=await Promise.race([Promise.resolve().then(loadConfig),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Configuration timed out')),10000);})]);const url=endpoint(config,pageURL);if(!url)throw Error('Upvotes are unavailable. Try again later.');return url;}finally{clearTimeout(timer);}})().catch(error=>{configPromise=null;throw error;});return configPromise;};
  async function readCounts(selected){
   for(const id of selected){lastReads.delete(id);lastReads.set(id,Date.now());}while(lastReads.size>2000)lastReads.delete(lastReads.keys().next().value);
   const started=new Map(selected.map(id=>[id,votes.get(id)?.revision||0]));
   try{const url=new URL(await service());url.searchParams.set('ids',selected.join(','));const body=await json(url.href,{method:'GET',credentials:'omit'},128*1024);
    if(body?.schema!=='liberpedia-upvotes-v1'||body.meaning!=='interest'||!Array.isArray(body.counts)||body.counts.length>100)throw Error();
    const seen=new Set();for(const item of body.counts){if(!item||!selected.includes(item.recordId)||seen.has(item.recordId)||!Number.isSafeInteger(item.count)||item.count<0)throw Error();seen.add(item.recordId);}
    for(const item of body.counts)if((votes.get(item.recordId)?.revision||0)===started.get(item.recordId)&&!votes.get(item.recordId)?.pending)remember(item.recordId,item.count);
   }catch{/* Unknown remains unknown; a failed read never invents zero. */}notify();
  }
  async function loadCounts(ids,{refresh=false}={}){
   if(!Array.isArray(ids)||!alive)return;if(refresh)for(const id of ids.filter(validId)){counts.delete(id);lastReads.delete(id);}
   const selected=[...new Set(ids.filter(validId))].filter(id=>!counts.has(id)&&(inflight.has(id)||!lastReads.has(id)||Date.now()-lastReads.get(id)>=30000)),waiting=[...new Set(selected.map(id=>inflight.get(id)).filter(Boolean))],fresh=selected.filter(id=>!inflight.has(id));
   for(let index=0;index<fresh.length;index+=100){const batch=fresh.slice(index,index+100),request=enqueue(()=>readCounts(batch));for(const id of batch)inflight.set(id,request);request.finally(()=>{for(const id of batch)if(inflight.get(id)===request)inflight.delete(id);});waiting.push(request);}
   await Promise.all(waiting);
  }
  async function vote(id){
   if(!alive)return;let state=votes.get(id);if(!state){state={desired:preferences.isUpvoted(id),confirmed:preferences.isUpvoted(id),pending:false,revision:0};votes.set(id,state);}
   if(!state.pending)state.desired=state.volatile?state.confirmed:preferences.isUpvoted(id);state.desired=!state.desired;state.revision++;errors.delete(id);notify();if(state.pending)return;
   state.pending=true;notify();
   try{
    const token=preferences.voteToken();if(typeof token!=='string'||!/^[a-f0-9]{64}$/.test(token))throw Error(preferences.snapshot()?.message||'Upvotes could not be saved in this browser.');
    while(true){const active=state.desired,url=await service(),body=await json(url,{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify({recordId:id,token,active})},512);
     if(!body||body.recordId!==id||body.active!==active||!Number.isSafeInteger(body.count)||body.count<0)throw Error('Your upvote could not be confirmed. Try again.');
     remember(id,body.count);state.confirmed=active;try{preferences.setUpvoted(id,active);state.volatile=false;}catch{state.volatile=true;errors.set(id,'Upvote saved, but this browser could not remember it.');}
     if(state.desired===active)break;
    }
   }catch(error){state.desired=state.confirmed;errors.set(id,preferences.snapshot()?.message||'Your upvote could not be saved. Try again.');}
   finally{state.pending=false;notify();}
  }
  function mount(host,id){
   if(!validId(id)||!host||!alive)return ()=>{};
   host.innerHTML='<div class="research-reactions"><button type="button" data-upvote title="Show interest in this research">'+arrow+'<span data-vote-label>Upvote</span><span data-vote-count></span></button><button type="button" data-save title="Saved in this browser">'+bookmark+'<span data-save-label>Save</span></button><span class="reaction-message" role="status" aria-live="polite"></span></div>';
   const up=host.querySelector('[data-upvote]'),save=host.querySelector('[data-save]'),message=host.querySelector('.reaction-message');
   const instance={render(){const state=votes.get(id);if(state&&!state.pending&&!state.volatile)state.confirmed=preferences.isUpvoted(id);const active=state?.pending?state.desired:state?.confirmed??preferences.isUpvoted(id),saved=preferences.isSaved(id),count=counts.get(id);
    up.setAttribute('aria-pressed',String(active));up.setAttribute('aria-busy',String(!!state?.pending));host.querySelector('[data-vote-label]').textContent=active?'Upvoted':'Upvote';host.querySelector('[data-vote-count]').textContent=count===undefined?'':String(count);
    save.setAttribute('aria-pressed',String(saved));save.setAttribute('aria-label',(saved?'Saved':'Save')+' in this browser');host.querySelector('[data-save-label]').textContent=saved?'Saved':'Save';
    message.textContent=errors.get(id)||preferences.snapshot()?.message||'';
   }};
   const onVote=()=>{void vote(id);},onSave=()=>{if(!alive)return;try{preferences.toggleSaved(id);errors.delete(id);}catch{errors.set(id,preferences.snapshot()?.message||'This browser could not save the bookmark.');}notify();};up.addEventListener('click',onVote);save.addEventListener('click',onSave);mounted.add(instance);instance.render();void loadCounts([id]);
   return ()=>{mounted.delete(instance);up.removeEventListener('click',onVote);save.removeEventListener('click',onSave);};
  }
  return {mount,loadCounts,count:id=>counts.has(id)?counts.get(id):null,refresh:notify,destroy(){alive=false;mounted.clear();for(const item of queue.splice(0))item.resolve();}};
 }
 const api={create,validId,endpoint};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchReactions=api;
})(typeof globalThis==='object'?globalThis:this);
