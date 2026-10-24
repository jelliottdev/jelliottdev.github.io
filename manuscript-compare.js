'use strict';
(() => {
 const reader=document.getElementById('reader');
 const divider=document.getElementById('comparison-divider');
 const image=document.getElementById('image-pane');
 const text=document.getElementById('text-pane');
 let share=50,dragging=false;
 try {share=Number(localStorage.getItem('liberpedia-manuscript-reader-split'))||50} catch {}
 function bounds(){
  const width=image.getBoundingClientRect().width+text.getBoundingClientRect().width;
  const min=Math.max(25,Math.min(50,280/Math.max(1,width)*100));
  return {min,max:100-min,width};
 }
 function update(value,persist=false){
  const {min,max}=reader.dataset.view==='compare'&&innerWidth>760?bounds():{min:25,max:75};
  share=Math.max(min,Math.min(max,Number.isFinite(value)?value:50));
  reader.style.setProperty('--image-share',share);
  divider.setAttribute('aria-valuenow',String(Math.round(share)));
  divider.setAttribute('aria-valuemin',String(Math.ceil(min)));
  divider.setAttribute('aria-valuemax',String(Math.floor(max)));
  divider.setAttribute('aria-valuetext',`${Math.round(share)} percent image, ${Math.round(100-share)} percent text`);
  if(persist)try{localStorage.setItem('liberpedia-manuscript-reader-split',String(share))}catch{}
 }
 divider.addEventListener('pointerdown',event=>{
  if(event.button!==0)return;
  event.preventDefault();divider.focus();divider.setPointerCapture(event.pointerId);
  dragging=true;document.body.classList.add('resizing-comparison');
 });
 divider.addEventListener('pointermove',event=>{
  if(!dragging)return;
  const {width}=bounds(),left=image.getBoundingClientRect().left;
  update((event.clientX-left)/Math.max(1,width)*100);
 });
 function finish(){if(!dragging)return;dragging=false;document.body.classList.remove('resizing-comparison');update(share,true)}
 for(const type of ['pointerup','pointercancel','lostpointercapture'])divider.addEventListener(type,finish);
 divider.addEventListener('dblclick',()=>update(50,true));
 divider.addEventListener('keydown',event=>{
  const {min,max}=bounds();
  const next={ArrowLeft:share-2,ArrowRight:share+2,Home:min,End:max,Enter:50}[event.key];
  if(next===undefined)return;
  event.preventDefault();event.stopPropagation();update(next,true);
 });
 // Preserve the chosen ratio when a temporary single-pane/mobile view hides it.
 new ResizeObserver(()=>{if(reader.dataset.view==='compare'&&innerWidth>760)update(share)}).observe(reader);
 new MutationObserver(()=>{if(reader.dataset.view==='compare'&&innerWidth>760)update(share)}).observe(reader,{attributes:true,attributeFilter:['data-view','class']});
 requestAnimationFrame(()=>update(share));
})();
