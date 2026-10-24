/* A rolling window of original pages; no text/image alignment is inferred. */
(function(root){
 function neighborIds(pages,id){const i=pages.findIndex(p=>p.id===id);return pages.slice(Math.max(0,i-1),i+2).map(p=>p.id);}
 function visibleId(entries,top,height){const middle=top+height*.4;return entries.find(e=>e.top<=middle&&e.bottom>middle)?.id||entries.at(-1)?.id;}
 function create(view,{pages,loadPage,onActive=()=>{},onInspect=()=>{},onRetryNeeded=()=>{}}){
  let generation=0,currentId=null,busy=false,frame=0,anchor=null,lastWidth=0;const doc=view.ownerDocument;
  const index=id=>pages.findIndex(p=>p.id===id),live=()=>view.isConnected&&!view.hidden;
  function cards(){return [...view.querySelectorAll('[data-continuous-page]')];}
  async function card(id,token){
   const data=await loadPage(id);if(token!==generation)return null;
   if(data?.id!==id||!Array.isArray(data.image_dimensions)||data.image_dimensions.length!==2||!data.image_dimensions.every(n=>Number.isInteger(n)&&n>0))throw Error('Page metadata unavailable');
   const section=doc.createElement('section');section.dataset.continuousPage=id;section.className='continuous-page';
   const bar=doc.createElement('header'),heading=doc.createElement('h2'),inspect=doc.createElement('button');heading.textContent=id.toUpperCase();inspect.type='button';inspect.textContent='Inspect page';inspect.setAttribute('aria-label','Inspect '+id.toUpperCase()+' with image controls');inspect.onclick=()=>onInspect(id);bar.append(heading,inspect);
   const img=doc.createElement('img');img.alt=id.toUpperCase()+' original manuscript page';img.width=data.image_dimensions[0];img.height=data.image_dimensions[1];img.loading='lazy';img.decoding='async';
   const source='images/'+id+'.jpg',error=doc.createElement('p');error.hidden=true;error.setAttribute('role','status');error.append(doc.createTextNode('Image unavailable. '));const direct=doc.createElement('a');direct.href=source;direct.textContent='Open original';const retry=doc.createElement('button');retry.type='button';retry.textContent='Retry image';retry.onclick=()=>{error.hidden=true;img.src=source+'?retry='+Date.now()};error.append(direct,doc.createTextNode(' '),retry);
   img.onerror=()=>{if(token===generation&&section.isConnected)error.hidden=false};img.onload=()=>{if(token===generation)error.hidden=true};img.src=source;section.append(bar,img,error);return section;
  }
  async function extend(direction,token){
   const list=cards(),edge=direction<0?list[0]:list.at(-1),next=pages[index(edge?.dataset.continuousPage)+direction];if(!next)return;
   const item=await card(next.id,token);if(!item||!live())return;
   const before=view.scrollHeight;if(direction<0){view.prepend(item);view.scrollTop+=view.scrollHeight-before;}else view.append(item);
   const all=cards();if(all.length>5){const removed=direction<0?all.at(-1):all[0],height=view.scrollHeight;removed.remove();if(direction>0)view.scrollTop=Math.max(0,view.scrollTop-(height-view.scrollHeight));}
  }
  async function update(){
   frame=0;if(!live()||busy)return;
   const list=cards();if(!list.length)return;
   const bounds=view.getBoundingClientRect(),positions=list.map(e=>{const r=e.getBoundingClientRect();return {id:e.dataset.continuousPage,top:r.top-bounds.top+view.scrollTop,bottom:r.bottom-bounds.top+view.scrollTop}}),active=visibleId(positions,view.scrollTop,view.clientHeight);
   if(active&&active!==currentId){currentId=active;onActive(active);}
   const position=positions.find(e=>e.id===currentId);if(position)anchor={id:currentId,ratio:(view.scrollTop-position.top)/(position.bottom-position.top)};
   let direction=0;if(view.scrollTop<view.clientHeight*.6&&index(list[0].dataset.continuousPage)>0)direction=-1;else if(view.scrollHeight-view.scrollTop-view.clientHeight<view.clientHeight*.6&&index(list.at(-1).dataset.continuousPage)<pages.length-1)direction=1;
   if(!direction)return;busy=true;const token=generation;try{await extend(direction,token)}catch{if(token===generation)status('The next page could not load. Use Retry pages.',true);}finally{if(token===generation)busy=false;}
  }
  function status(text,retry=false){onRetryNeeded(retry);let p=view.querySelector('[data-continuous-status]');if(!p){p=doc.createElement('p');p.dataset.continuousStatus='';p.className='continuous-status';p.setAttribute('role','status');view.append(p);}p.textContent=text;}
  async function open(id){
   if(id===currentId&&cards().length)return;const token=++generation;busy=true;currentId=id;anchor={id,ratio:0};view.replaceChildren();status('Loading nearby original pages…');
   try{const nearby=await Promise.all(neighborIds(pages,id).map(x=>card(x,token)));if(token!==generation||!live())return;view.replaceChildren(...nearby.filter(Boolean));view.scrollTop=cards().find(e=>e.dataset.continuousPage===id)?.offsetTop||0;lastWidth=view.clientWidth;}
   catch{if(token===generation&&live())status('The nearby pages could not load. Use Retry pages.',true);}
   finally{if(token===generation)busy=false;}
  }
  view.addEventListener('scroll',()=>{if(!frame)frame=requestAnimationFrame(update);},{passive:true});
  const observer=typeof ResizeObserver!=='undefined'?new ResizeObserver(()=>{const width=view.clientWidth;if(!live()||!width||busy)return;if(lastWidth&&width!==lastWidth&&anchor){const item=cards().find(e=>e.dataset.continuousPage===anchor.id);if(item)view.scrollTop=item.offsetTop+anchor.ratio*item.getBoundingClientRect().height;}lastWidth=width;}):null;observer?.observe(view);
  return {open,retry(){const id=currentId;currentId=null;return open(id)},destroy(){generation++;observer?.disconnect();if(frame)cancelAnimationFrame(frame);view.replaceChildren();currentId=null},get currentId(){return currentId}};
 }
 const api={create,neighborIds,visibleId};if(typeof module!=='undefined')module.exports=api;else root.ReaderContinuousPages=api;
})(globalThis);
