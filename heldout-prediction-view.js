/* Saved held-out measurements only. No model fitting, scoring or external calls. */
(function(root){
 const base='experiments/records/heldout-rune-prediction/',svg=base+'predictive-controls.svg';
 const names=['kt','ppm'].flatMap(model=>Array.from({length:8},(_,i)=>model+(i+1)));
 let cached,pending;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const integer=(n,min,max)=>Number.isInteger(n)&&n>=min&&n<=max;
 function canRender(record,visual){
  return record?.id==='heldout-rune-prediction'&&visual?.path===svg&&
   ['results.json','predictive-controls.svg'].every(name=>record.reproduction?.outputs?.some(file=>file.path===base+name));
 }
 function validate(result){
  const f=result?.family,p=result?.compression?.packed,tolerance=result?.uniform_gain_equivalence_tolerance;
  if(result?.schema!=='heldout-rune-prediction-results-v1'||result.metric_count!==26||result.marginal_flag_count!==0||
   !f||f.reference_rows!==1001||!integer(f.rank,1,1001)||f.controls_at_least_as_strong!==f.rank-1||f.gate!==false||f.fixed_fraction_gate!==0.01||
   !Number.isFinite(f.rank_fraction)||Math.abs(f.rank_fraction-f.rank/f.reference_rows)>1e-12||f.rank_fraction<0.01||
   !Number.isFinite(result.uniform_bits_per_rune)||Math.abs(result.uniform_bits_per_rune-Math.log2(29))>1e-12||tolerance!==1e-10||
   !Array.isArray(result.predictors)||result.predictors.length!==16)throw Error('Invalid held-out summary');
  const groups={better:[],equivalent:[],worse:[]};
  const predictors=result.predictors.map((row,i)=>{
   if(row?.name!==names[i]||!Number.isFinite(row.bits_per_rune)||row.bits_per_rune<=0||!Number.isFinite(row.gain_over_uniform)||
    Math.abs(result.uniform_bits_per_rune-row.bits_per_rune-row.gain_over_uniform)>1e-12||!integer(row.nulls_at_least_as_good,0,1000))throw Error('Invalid prediction row');
   const classification=Math.abs(row.gain_over_uniform)<=tolerance?'equivalent':row.gain_over_uniform>0?'better':'worse';
   if(row.uniform_classification!==classification)throw Error('Invalid uniform comparison');
   const clean={name:row.name.toUpperCase(),bits:row.bits_per_rune,gain:row.gain_over_uniform,controls:row.nulls_at_least_as_good};
   groups[classification].push(clean);return clean;
  });
  if(!p||p.control_constant!==true||p.control_count!==1000||!integer(p.compressed_bytes,1,1000000)||
   p.reference_min_bytes!==p.compressed_bytes||p.reference_max_bytes!==p.compressed_bytes||p.plant_detections!==0||p.plant_count!==18||p.gross_plant_detections!==0||p.gross_plant_count!==12)throw Error('Invalid packed control result');
  return {groups,predictors,rank:f.rank,rows:f.reference_rows,stronger:f.controls_at_least_as_strong,packedBytes:p.compressed_bytes,packedTotal:p.plant_count,packedGross:p.gross_plant_count};
 }
 function compactNames(rows){
  const labels=[];
  for(let i=0;i<rows.length;i++){
   const start=rows[i].name.match(/^(KT|PPM)(\d)$/),first=Number(start[2]);let last=first;
   while(i+1<rows.length&&rows[i+1].name===start[1]+(last+1)){i++;last++;}
   labels.push(start[1]+first+(last===first?'':'–'+last));
  }
  return labels.join(', ');
 }
 function content(data){
  const summaries=[['better','Tiny gains'],['equivalent','Tied'],['worse','Worse']];
  let html='<h3 data-heldout-heading tabindex="-1">Did other pages help predict the runes?</h3><p>Compared with giving every rune the same chance:</p>'+
   '<ul class="heldout-results-groups">'+summaries.map(([key,label])=>'<li><strong>'+data.groups[key].length+' / 16</strong><span><b>'+label+'</b><span>'+compactNames(data.groups[key])+'</span></span></li>').join('')+'</ul>'+
   '<p>These groups describe prediction quality against equal rune chances; they are not significance results.</p>';
  if(data.groups.better.length)html+='<dl class="heldout-gains">'+data.groups.better.map(row=>'<div><dt>'+esc(row.name)+'</dt><dd>'+row.gain.toFixed(6)+' bits saved per rune. '+row.controls+' of 1,000 comparison streams did at least as well.</dd></div>').join('')+'</dl>';
  html+='<section class="heldout-family-result"><h4>The complete comparison</h4><p>Across prediction, compression and frequency patterns, none of the <strong>26 measurements</strong> crossed its fixed 1% comparison line. The whole-search rank was <strong>'+data.rank+' / '+data.rows.toLocaleString('en-US')+'</strong> (about '+(100*data.rank/data.rows).toFixed(1)+'%): '+data.stronger+' comparison streams plus the manuscript itself.</p></section>'+
   '<section class="heldout-packed-limit"><h4>Packed compression missed known patterns</h4><p><strong>0 of '+data.packedGross+' known patterns detected.</strong> It flagged 0 of '+data.packedTotal+' synthetic examples in total, including the negative checks. The manuscript and all 1,000 comparison streams compressed to the same '+data.packedBytes.toLocaleString('en-US')+' bytes. This compression check could not distinguish them.</p></section>'+
   '<p>This does not establish randomness, a one-time pad or the absence of plaintext.</p>'+
   '<details><summary>All 16 prediction scores</summary><p>Lower bits per rune means better prediction. Counts compare each model with 1,000 generated streams; they are not independent tests.</p><div class="table-wrap" tabindex="0" role="region" aria-label="All prediction scores; scroll horizontally if needed"><table><thead><tr><th scope="col">Model</th><th scope="col">Bits per rune</th><th scope="col">Comparison streams as good</th></tr></thead><tbody>'+data.predictors.map(row=>'<tr><th scope="row">'+esc(row.name)+'</th><td>'+row.bits.toFixed(6)+'</td><td>'+row.controls+' / 1,000</td></tr>').join('')+'</tbody></table></div></details>';
  return html;
 }
 function render(){
  return '<figure class="experiment-figure heldout-results"><div data-heldout-content></div><p data-heldout-status role="status">Loading the saved prediction results…</p><button type="button" data-heldout-retry hidden>Retry saved results</button><p><a href="'+svg+'" download>Download the SVG summary</a> · <a href="'+base+'results.json" download>All saved measurements</a></p></figure>';
 }
 async function bind(figure,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!figure)return;
  const view=figure.querySelector('[data-heldout-content]'),status=figure.querySelector('[data-heldout-status]'),retry=figure.querySelector('[data-heldout-retry]');
  const current=()=>figure.isConnected&&isCurrent();let loading=false;
  const load=async()=>{
   if(loading||!current())return;loading=true;const heldFocus=figure.ownerDocument?.activeElement===retry;retry.disabled=true;status.textContent='Loading the saved prediction results…';
   try{
    if(!cached){
     if(!pending)pending=(async()=>{
      const controller=new AbortController();let timer;
      try{return await Promise.race([
       (async()=>{const response=await fetcher(base+'results.json',{signal:controller.signal});if(!response.ok)throw Error();return validate(await response.json());})(),
       new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Prediction results timed out'));},10000);})
      ])}finally{clearTimeout(timer);controller.abort();}
     })().then(value=>cached=value).finally(()=>{pending=null});
     await pending;
    }
    if(!current())return;view.innerHTML=content(cached);status.textContent='';
    if(heldFocus&&(figure.ownerDocument.activeElement===retry||figure.ownerDocument.activeElement===figure.ownerDocument.body))view.querySelector('[data-heldout-heading]')?.focus({preventScroll:true});retry.hidden=true;
   }catch{if(current()){status.textContent='The saved results could not load. Retry or use the summary figure below.';view.innerHTML='<a href="'+svg+'" target="_blank" rel="noopener"><img src="'+svg+'" alt="Archived prediction and control summary"></a>';retry.hidden=false;}}
   finally{loading=false;if(current()){retry.disabled=false;if(heldFocus&&!retry.hidden&&figure.ownerDocument.activeElement===figure.ownerDocument.body)retry.focus({preventScroll:true});}}
  };
  retry.addEventListener('click',load);return load();
 }
 const api={canRender,validate,content,render,bind};if(typeof module!=='undefined')module.exports=api;else root.HeldoutPredictionView=api;
})(globalThis);
