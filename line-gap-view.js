/* Original-image coordinates only; presentation does not measure or resize the source. */
(function(root){
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let cached,pending;
 function validate(data){
  if(data?.schema!=='liberpedia-line-gap-measurements-v1'||!Array.isArray(data.rows)||!data.rows.length)throw Error('Invalid gap measurements');
  const seen=new Set();
  for(const r of data.rows){
   if(!/^[a-z0-9-]+$/.test(r.id)||seen.has(r.id)||!/^lp2-\d{2}$/.test(r.page)||r.image_path!=='images/'+r.page+'.jpg'||r.width!==2400||r.height!==3600||!Array.isArray(r.rect_xyxy)||r.rect_xyxy.length!==4||!r.rect_xyxy.every(Number.isInteger))throw Error('Invalid source region');
   seen.add(r.id);const [x1,y1,x2,y2]=r.rect_xyxy;
   if(x1<0||y1<0||x2>=r.width||y2>=r.height||x2<=x1||y2<=y1||!Array.isArray(r.lines)||r.lines.length<2||!Array.isArray(r.gaps)||r.gaps.length!==r.lines.length-1)throw Error('Invalid region bounds');
   r.lines.forEach((l,i)=>{if(!Number.isInteger(l.top)||!Number.isInteger(l.bottom)||l.top<y1||l.bottom>y2||l.top>l.bottom||(i&&l.top<=r.lines[i-1].bottom))throw Error('Invalid ink edges');});
   r.gaps.forEach((g,i)=>{if(g.from_line!==i+1||g.to_line!==i+2||g.top!==r.lines[i].bottom+1||g.bottom!==r.lines[i+1].top-1||g.pixels!==g.bottom-g.top+1||g.pixels<1)throw Error('Invalid blank gap');});
   if(r.overlay_path!=='exports/line-gaps/'+r.id+'.svg')throw Error('Invalid overlay path');
  }return data;
 }
 function graphic(r,index,{guides=true,overview=false}={}){
  const g=r.gaps[index],a=r.lines[g.from_line-1],b=r.lines[g.to_line-1],[left,,right]=r.rect_xyxy;
  const pad=Math.max(24,Math.round((b.bottom-a.top)*.12)),x=overview?0:Math.max(0,left-24),y=overview?0:Math.max(0,a.top-pad),w=overview?r.width:Math.min(r.width-x,625),h=overview?r.height:Math.min(r.height-y,b.bottom-a.top+1+pad*2),caliper=left+30;
  const lines=guides?'<g class="line-gap-guides" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"><path vector-effect="non-scaling-stroke" d="M '+left+' '+a.bottom+' H '+right+' M '+left+' '+b.top+' H '+right+'"/><path vector-effect="non-scaling-stroke" d="M '+caliper+' '+g.top+' V '+g.bottom+' M '+(caliper-18)+' '+g.top+' H '+(caliper+18)+' M '+(caliper-18)+' '+g.bottom+' H '+(caliper+18)+'"/></g>':'';
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+[x,y,w,h].join(' ')+'" role="img" aria-label="'+esc(r.page.toUpperCase()+', space between lines '+g.from_line+' and '+g.to_line+': '+g.pixels+' original-image pixels')+'"><image href="'+esc(r.image_path)+'" x="0" y="0" width="'+r.width+'" height="'+r.height+'"/>'+lines+'</svg>';
 }
 function widestGap(r){return r.gaps.reduce((best,g,i)=>g.pixels>r.gaps[best].pixels?i:best,0);}
 function measurementHtml(r,index){const g=r.gaps[index];return '<strong>'+g.pixels+' pixels</strong><span>Space between lines '+g.from_line+' and '+g.to_line+'</span><small>Original 2400 × 3600 image; not screen pixels.</small>';}
 function render(){return '<div class="line-gap-view"><p role="status" data-gap-status>Loading the page measurements…</p><button type="button" data-gap-retry hidden>Retry measurements</button><div data-gap-body></div></div>';}
 async function bind(mount,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!mount)return;const status=mount.querySelector('[data-gap-status]'),retry=mount.querySelector('[data-gap-retry]'),body=mount.querySelector('[data-gap-body]');if(!status||!retry||!body)return;
  const current=()=>mount.isConnected&&isCurrent();let loading=false,region,index=0,guides=true,overview=false;
  function paint(){
   const r=region,g=r.gaps[index];
   body.querySelector('[data-gap-measurement]').innerHTML=measurementHtml(r,index);
   const imageView=body.querySelector('[data-gap-image]');imageView.innerHTML=graphic(r,index,{guides,overview});status.textContent='';
   const image=imageView.querySelector?.('image');image?.addEventListener('error',()=>{if(current()&&image.isConnected)status.textContent='The original image could not load. Try its direct link or download the annotated SVG below.';});
   for(const button of body.querySelectorAll('[data-gap-pair]'))button.setAttribute('aria-pressed',String(Number(button.dataset.gapPair)===index));
   const strip=body.querySelector('[data-gap-pairs]'),selected=strip.querySelector?.('[data-gap-pair="'+index+'"]');
   if(selected&&Number.isFinite(selected.offsetLeft)&&strip.clientWidth>0)strip.scrollLeft=Math.max(0,selected.offsetLeft-(strip.clientWidth-selected.offsetWidth)/2);
   const prev=body.querySelector('[data-gap-prev]'),next=body.querySelector('[data-gap-next]'),focused=mount.ownerDocument?.activeElement;
   prev.disabled=index===0;next.disabled=index===r.gaps.length-1;
   if(focused===prev&&prev.disabled&&!next.disabled)next.focus({preventScroll:true});else if(focused===next&&next.disabled&&!prev.disabled)prev.focus({preventScroll:true});
   const original=body.querySelector('[data-gap-original]');original.href=r.image_path;original.textContent='Open original '+r.page.toUpperCase()+' image';
   const overlay=body.querySelector('[data-gap-overlay]');overlay.hidden=!r.overlay_path;overlay.href=r.overlay_path||r.image_path;
  }
  function choose(r){region=r;index=widestGap(r);
   body.querySelector('[data-gap-pairs]').innerHTML=r.gaps.map((g,i)=>'<button type="button" data-gap-pair="'+i+'" aria-label="Lines '+g.from_line+' to '+g.to_line+': '+g.pixels+' pixels">'+g.pixels+'<span> px</span></button>').join('');paint();
  }
  async function load(){
   if(loading||!current())return;loading=true;const focused=mount.ownerDocument?.activeElement===retry;retry.disabled=true;status.textContent='Loading the page measurements…';
   try{
    if(!cached){if(!pending)pending=(async()=>{const controller=new AbortController();let timer;try{return await Promise.race([fetcher('exports/line-gap-measurements.json',{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(validate),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Timeout'));},10000);})]);}finally{clearTimeout(timer);controller.abort();}})().then(d=>(cached=d)).finally(()=>pending=null);await pending;}
    if(!current())return;
    body.innerHTML='<label class="line-gap-region">Measured part of the page<select data-gap-region>'+cached.rows.map(r=>'<option value="'+r.id+'">'+esc(r.label||r.page.toUpperCase())+'</option>').join('')+'</select></label><div class="line-gap-measurement" data-gap-measurement aria-live="polite" aria-atomic="true"></div><div class="line-gap-image" data-gap-image></div><div class="line-gap-options"><label><input type="checkbox" data-gap-guides checked> Show measurement lines</label><label><input type="checkbox" data-gap-overview> Show whole page</label></div><div class="line-gap-pairs" data-gap-pairs role="group" aria-label="Choose a gap; values in original-image pixels"></div><nav class="line-gap-navigation" aria-label="Gap navigation"><button type="button" data-gap-prev>Previous gap</button><button type="button" data-gap-next>Next gap</button></nav><p class="line-gap-source"><a data-gap-original>Open original image</a><a data-gap-overlay download>Download annotated SVG</a></p>';
    const select=body.querySelector('[data-gap-region]'),initial=cached.rows.find(r=>r.page==='lp2-04')||cached.rows[0];select.value=initial.id;choose(initial);
    select.addEventListener('change',()=>{if(current())choose(cached.rows.find(r=>r.id===select.value)||initial);});
    body.querySelector('[data-gap-pairs]').addEventListener('click',event=>{const button=event.target.closest('[data-gap-pair]');if(button&&current()){index=Number(button.dataset.gapPair);paint();}});
    for(const [selector,delta] of [['[data-gap-prev]',-1],['[data-gap-next]',1]])body.querySelector(selector).addEventListener('click',()=>{if(current()){index=Math.max(0,Math.min(region.gaps.length-1,index+delta));paint();}});
    body.querySelector('[data-gap-guides]').addEventListener('change',e=>{guides=e.target.checked;if(current())paint();});body.querySelector('[data-gap-overview]').addEventListener('change',e=>{overview=e.target.checked;if(current())paint();});
    status.textContent='';retry.hidden=true;if(focused&&(mount.ownerDocument.activeElement===retry||mount.ownerDocument.activeElement===mount.ownerDocument.body))select.focus({preventScroll:true});
   }catch{if(current()){status.textContent='The measurements could not load. Retry, or use the original-page and download links in the article.';retry.hidden=false;}}
   finally{loading=false;if(current())retry.disabled=false;}
  }retry.addEventListener('click',load);return load();
 }
 const api={validate,graphic,widestGap,measurementHtml,render,bind};if(typeof module!=='undefined')module.exports=api;else root.LineGapView=api;
})(globalThis);
