/* Existing guide interactions, scoped for the standalone library. No decoding/search calls. */
(function(root){'use strict';
 function bind(main,{isCurrent=()=>main.isConnected}={}){
function bindChoiceExplorer(){
 const figure=main.querySelector('#'+'choice-explorer');
 if(!figure)return;
 const controls=figure.querySelector('.choice-explorer-live');
 const fallback=figure.querySelector('.choice-explorer-static');
 const fields=['pages','orders','shifts','offsets'].map(name=>figure.querySelector('#choice-'+name));
 if(!controls||fields.some(field=>!field))return;
 controls.hidden=false;fallback.hidden=true;
 const update=()=>{
  let total=1;
  const values=fields.map(field=>Number(field.value));
  fields.forEach((field,index)=>{
   total*=values[index];
   figure.querySelector(`output[for="${field.id}"]`).textContent=String(values[index]);
   figure.querySelector('#choice-step-'+field.id.slice(7)).textContent=total.toLocaleString('en-US');
  });
  figure.querySelector('#choice-formula').textContent=values.join(' × ');
  figure.querySelector('#choice-total').textContent=total.toLocaleString('en-US')+' configurations';
 };
 fields.forEach(field=>field.addEventListener('input',update));
 update();
}
function bindFibonacciPanel(){
 const figure=main.querySelector('#'+'fib-panel'),ledger=main.querySelector('#'+'fib-ledger');
 if(!figure||!ledger)return;
 const rows=[...ledger.tBodies[0].rows].map(tr=>{
  const cells=[...tr.cells].map(cell=>cell.textContent.trim());
  const point=cells[1]?.match(/^\((\d+),\s*(\d+)\)$/);
  return point?{step:Number(cells[0]),row:Number(point[1]),column:Number(point[2]),index:Number(cells[2]),prime:Number(cells[3]),printed:Number(cells[5])}:null;
 });
 if(rows.length!==16||rows.some((item,i)=>!item||item.step!==i+1||!Number.isFinite(item.prime)))return;
 const live=figure.querySelector('.fib-panel-live'),fallback=figure.querySelector('.fib-panel-fallback');
 const cells=[...rows].sort((a,b)=>a.row-b.row||a.column-b.column);
 live.innerHTML=`<div class="fib-panel-grid" role="group" aria-label="LP2-15 number panel in image order">${cells.map(item=>`<button type="button" class="fib-panel-cell" data-step="${item.step}" data-red="${item.printed===3299}" aria-label="Step ${item.step}, row ${item.row}, column ${item.column}: ${item.printed}"><span class="fib-cell-step">${item.step}</span><strong>${item.printed}</strong></button>`).join('')}</div><div class="fib-panel-controls"><button type="button" data-fib-previous aria-label="Previous spiral step">Previous</button><input type="range" min="1" max="16" value="1" aria-label="Spiral step"><button type="button" data-fib-next aria-label="Next spiral step">Next</button></div><div class="fib-panel-reading" aria-live="polite"></div>`;
 live.hidden=false;fallback.hidden=true;
 const slider=live.querySelector('input'),reading=live.querySelector('.fib-panel-reading');
 const draw=()=>{
  const step=Number(slider.value),item=rows[step-1],difference=3301-item.prime;
  live.querySelectorAll('.fib-panel-cell').forEach(button=>{
   const number=Number(button.dataset.step);
   button.setAttribute('aria-current',String(number===step));
   button.classList.toggle('visited',number<step);
  });
  live.querySelector('[data-fib-previous]').disabled=step===1;
  live.querySelector('[data-fib-next]').disabled=step===16;
  reading.innerHTML=`<strong>Step ${step} of 16 · row ${item.row}, column ${item.column}</strong><span>Fibonacci index ${item.index} selects prime ${item.prime}. |3301 − ${item.prime}| = ${item.printed}.</span>${difference<0?`<small>The signed difference is ${difference}; the page prints its positive distance.</small>`:''}`;
 };
 slider.addEventListener('input',draw);
 live.querySelector('[data-fib-previous]').onclick=()=>{slider.value=String(Math.max(1,Number(slider.value)-1));draw()};
 live.querySelector('[data-fib-next]').onclick=()=>{slider.value=String(Math.min(16,Number(slider.value)+1));draw()};
 live.querySelectorAll('.fib-panel-cell').forEach(button=>button.onclick=()=>{slider.value=button.dataset.step;draw()});
 draw();
}
  if(!isCurrent())return Promise.resolve();
  bindChoiceExplorer();bindFibonacciPanel();
  const mount=main.querySelector('[data-line-gap-explorer]');
  if(mount&&root.LineGapView){mount.innerHTML=root.LineGapView.render();return root.LineGapView.bind(mount,{isCurrent:()=>main.isConnected&&isCurrent()});}
  return Promise.resolve();
 }
 const api={bind};if(typeof module!=='undefined')module.exports=api;else root.LibraryGuides=api;
})(globalThis);
