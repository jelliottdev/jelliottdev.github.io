/* Read-only navigation among exact public question variations. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,Links=node?require('./question-variation-links.js'):root.QuestionVariationLinks,View=node?require('./question-variations-view.js'):root.QuestionVariationsView;
 const ID=/^p_[a-f0-9]{64}$/,MAX=4*1024*1024,exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),ensure=(v,m)=>{if(!v)throw Error(m);};
 function service(baseURL,pageURL){const u=new URL(baseURL);ensure(!u.username&&!u.password&&!u.search&&!u.hash&&u.pathname==='/','Use one service origin.');if(u.protocol!=='https:'){const page=new URL(pageURL);ensure(u.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(u.hostname)&&u.origin===page.origin,'Use HTTPS or the same local test origin.');}return u.origin;}
 function cursor(value){if(value===null)return null;ensure(typeof value==='string'&&value.length<=240&&/^[-_a-zA-Z0-9]+$/.test(value),'The variation page cursor is invalid.');const c=JSON.parse(atob(value.replace(/-/g,'+').replace(/_/g,'/')));ensure(exact(c,['createdAt','id'])&&typeof c.createdAt==='string'&&new Date(c.createdAt).toISOString()===c.createdAt&&/^[a-f0-9]{64}$/.test(c.id)&&btoa(JSON.stringify(c)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')===value,'The variation page cursor changed.');return value;}
 function mount(initialHost,options={}){
  const {ideaId,baseURL,pageURL=root.location?.href||'',fetcher=root.fetch?.bind(root),crypto=root.crypto,timeoutMs=15000}=options,view=options.view||View;
  ensure(ID.test(ideaId)&&typeof fetcher==='function'&&crypto?.subtle&&Number.isSafeInteger(timeoutMs)&&timeoutMs>0&&timeoutMs<=45000&&view?.render&&view?.bind,'Question navigation is unavailable.');
  const origin=service(baseURL,pageURL),groups={parents:{items:[],cursor:null,seen:new Set(),busy:false,error:false,loaded:false},children:{items:[],cursor:null,seen:new Set(),busy:false,error:false,loaded:false}};
  let host=null,unbind=()=>{},dead=false;const controllers=new Set();
  function model(){return {parents:groups.parents.items.slice(),children:groups.children.items.slice(),loading:groups.parents.busy||groups.children.busy,error:groups.parents.error||groups.children.error?'Related questions could not be loaded. Please try again.':'',moreParents:!!groups.parents.cursor,moreChildren:!!groups.children.cursor,loadingParents:groups.parents.busy,loadingChildren:groups.children.busy};}
  function draw(){if(dead||!host)return;unbind();host.innerHTML=view.render(model());unbind=view.bind(host,{moreParents:()=>load('parents',true),moreChildren:()=>load('children',true),retry:()=>retry()},model())||(()=>{});}
  function attach(next){if(dead)return;ensure(next&&typeof next.querySelectorAll==='function','Choose a question navigation container.');if(host!==next){unbind();if(host)host.innerHTML='';host=next;unbind=()=>{};}draw();}
  async function page(direction,before){
   const controller=new AbortController();controllers.add(controller);let reader,rejectAbort;const cancel=()=>{try{void reader?.cancel().catch(()=>{});}catch{}rejectAbort?.(Error('Question navigation was cancelled.'));},aborted=new Promise((_,reject)=>{rejectAbort=reject;controller.signal.addEventListener('abort',cancel,{once:true});}),timer=setTimeout(()=>controller.abort(),timeoutMs);
   const work=async()=>{
    const url=origin+'/ideas/'+ideaId+'/variations?direction='+direction+(before?'&before='+encodeURIComponent(before):''),response=await fetcher(url,{method:'GET',headers:{Accept:'application/json'},credentials:'omit',redirect:'error',cache:'no-store',signal:controller.signal});
    ensure(!dead&&!controller.signal.aborted&&response.ok&&!response.redirected&&(!response.url||response.url===url)&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The related questions could not be loaded.');
    const size=response.headers.get('content-length');ensure(size===null||/^\d+$/.test(size)&&Number(size)<=MAX,'The related questions exceed their byte bound.');reader=response.body?.getReader();ensure(reader,'The related question body is unavailable.');let length=0;const chunks=[];
    for(;;){const part=await Promise.race([reader.read(),aborted]);if(part.done)break;length+=part.value.byteLength;ensure(length<=MAX,'The related questions exceed their byte bound.');chunks.push(part.value);}
    const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    const body=J.capture(JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(bytes)),{maxBytes:MAX,maxDepth:24,maxNodes:300000});
    ensure(exact(body,['schema','ideaId','direction','entries','nextCursor'])&&body.schema==='liberpedia-question-variations-v1'&&body.ideaId===ideaId&&body.direction===direction&&Array.isArray(body.entries)&&body.entries.length<=10,'The related questions changed their identity.');
    const next=cursor(body.nextCursor);ensure(!next||body.entries.length===10,'A partial variation page cannot advertise another page.');
    const items=[];for(const entry of body.entries){ensure(!dead&&!controller.signal.aborted,'Question navigation was cancelled.');items.push(await Links.validate(entry,{ideaId,direction,crypto}));}
    ensure(new Set(items.map(item=>item.id)).size===items.length,'A variation page repeats a relationship.');
    for(let i=0;i<items.length;i++){const current=items[i],prior=i?items[i-1]:before?JSON.parse(atob(before.replace(/-/g,'+').replace(/_/g,'/'))):null;ensure(!prior||current.createdAt<prior.createdAt||current.createdAt===prior.createdAt&&current.id<prior.id,'Variation order changed.');}
    if(next){const tail=items.at(-1),position=JSON.parse(atob(next.replace(/-/g,'+').replace(/_/g,'/')));ensure(position.createdAt===tail.createdAt&&position.id===tail.id,'The next cursor does not follow these relationships.');}
    return {items,cursor:next};
   };
   try{return await Promise.race([work(),aborted]);}finally{clearTimeout(timer);controller.signal.removeEventListener('abort',cancel);controllers.delete(controller);try{void reader?.cancel().catch(()=>{});}catch{}}
  }
  async function load(direction,append=false){const g=groups[direction];if(dead||g.busy||append&&!g.cursor)return;const before=append?g.cursor:null;g.busy=true;g.error=false;draw();try{const result=await page(direction,before);if(dead)return;ensure(!result.items.some(item=>append&&g.seen.has(item.id)),'The variation listing repeated an earlier relationship.');if(!append){g.items=[];g.seen.clear();}g.items.push(...result.items);for(const item of result.items)g.seen.add(item.id);g.cursor=result.cursor;g.loaded=true;}catch{if(!dead)g.error=true;}finally{g.busy=false;draw();}}
  async function retry(){await Promise.all(Object.keys(groups).filter(key=>groups[key].error).map(key=>load(key,groups[key].loaded&&!!groups[key].cursor)));}
  function destroy(){if(dead)return;dead=true;for(const c of controllers)c.abort();unbind();if(host)host.innerHTML='';options.signal?.removeEventListener('abort',destroy);}
  const api={ready:null,attach,destroy,getState:()=>({phase:dead?'destroyed':Object.values(groups).some(g=>g.busy)?'loading':Object.values(groups).some(g=>g.error)?'error':'ready',...model()})};
  if(options.signal?.aborted){destroy();api.ready=Promise.resolve();}else{options.signal?.addEventListener('abort',destroy,{once:true});attach(initialHost);api.ready=Promise.all(['parents','children'].map(key=>load(key)));}return api;
 }
 const api={mount};if(node)module.exports=api;else root.QuestionVariationsWorkspace=api;
})(typeof globalThis!=='undefined'?globalThis:this);
