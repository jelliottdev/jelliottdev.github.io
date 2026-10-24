/* Saved synthetic controls; no decryption, scoring or remote services. */
(function(root){
 const base='experiments/records/keyword-skip-family/',svg=base+'control-recovery.svg';
 let cached,pending;
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const count=n=>Number.isInteger(n)&&n>=0;
 function canRender(record,visual){return record?.id==='keyword-skip-family'&&visual?.path===svg&&['control-summary.json','control-recovery.svg'].every(name=>record.reproduction?.outputs?.some(file=>file.path===base+name))}
 function validate(result){
  const k=result?.known_key,w=result?.whole_search,e=result?.example;
  if(result?.schema!=='keyword-skip-controls-v1'||!k||!w||![k.total,k.score_passes,k.exact_recoveries,w.total,w.exact_recoveries,w.keyword_labels].every(count)||k.total<1||k.total>100000||k.score_passes!==k.total||k.exact_recoveries>k.score_passes||w.total<1||w.exact_recoveries>w.total||w.keyword_labels<1)throw Error('Invalid control counts');
  if(!e||e.score_pass!==true||!Number.isInteger(e.excerpt_start)||e.excerpt_start<1||!Number.isInteger(e.first_difference)||e.first_difference<e.excerpt_start||!Array.isArray(e.expected_indices)||e.expected_indices.length<1||e.expected_indices.length>24||!Array.isArray(e.recovered_indices)||e.recovered_indices.length!==e.expected_indices.length)throw Error('Invalid control example');
  const arrays=[e.expected_indices,e.recovered_indices];
  if(arrays.some(a=>a.some(n=>!Number.isInteger(n)||n<0||n>28)))throw Error('Invalid rune indices');
  for(const key of ['expected_labels','recovered_labels'])if(!Array.isArray(e[key])||e[key].length!==e.expected_indices.length||e[key].some(x=>typeof x!=='string'||! /^[A-Z]{1,3}$/.test(x)))throw Error('Invalid rune labels');
  const first=e.expected_indices.findIndex((n,i)=>n!==e.recovered_indices[i]);
  if(first<0||first+e.excerpt_start!==e.first_difference)throw Error('Invalid mismatch position');
  for(let i=0;i<e.expected_indices.length;i++)if((e.expected_indices[i]===e.recovered_indices[i])!==(e.expected_labels[i]===e.recovered_labels[i]))throw Error('Inconsistent rune labels');
  return {known:{...k},whole:{...w},example:{...e},wrong:k.score_passes-k.exact_recoveries};
 }
 function content(data){
  const k=data.known,w=data.whole,e=data.example;
  const bars=[['Passed the English-score test',k.score_passes],['Recovered the exact text',k.exact_recoveries]];
  return '<h3 data-keyword-heading tabindex="-1">English-like is not the same as correct</h3><p>The original messages were known in these checks:</p><dl class="keyword-skip-bars">'+bars.map(([label,n])=>'<div><dt>'+label+'</dt><dd><strong>'+n+' / '+k.total+'</strong><span class="keyword-skip-track" aria-hidden="true"><span style="width:'+100*n/k.total+'%"></span></span></dd></div>').join('')+'</dl><p><strong>'+data.wrong+' accepted outputs were wrong.</strong> These checks supplied the key and reused two known passages; the counts are not probabilities of solving LP2.</p><section class="keyword-skip-example"><h4>One accepted output changed the message</h4><p>GP labels from a saved excerpt. Changed runes are outlined.</p><div class="keyword-skip-pair">'+[['Original','expected'],['Recovered','recovered']].map(([label,key])=>'<div><b>'+label+'</b><ol start="'+e.excerpt_start+'">'+e[key+'_labels'].map((token,i)=>'<li'+(e.expected_indices[i]!==e.recovered_indices[i]?' class="keyword-skip-changed"':'')+'><span class="sr-only">Rune '+(e.excerpt_start+i)+': </span>'+esc(token)+(e.expected_indices[i]!==e.recovered_indices[i]?'<span class="sr-only">, changed</span>':'')+'</li>').join('')+'</ol></div>').join('')+'</div><p>The first wrong rune was at position '+e.first_difference+'. The English-score test still accepted this output.</p></section><p>When the key was also searched across <strong>'+w.keyword_labels+' keyword labels</strong>, the complete search recovered <strong>'+w.exact_recoveries+' of '+w.total+'</strong> planted messages.</p>';
 }
 function render(){return '<figure class="experiment-figure keyword-skip-results"><div data-keyword-content></div><p data-keyword-status role="status">Loading saved recovery checks…</p><button type="button" data-keyword-retry hidden>Retry saved checks</button><p><a href="'+svg+'" download>Download the control figure</a> · <a href="'+base+'control-summary.json" download>Saved control summary</a></p></figure>'}
 async function bind(figure,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!figure)return;const view=figure.querySelector('[data-keyword-content]'),status=figure.querySelector('[data-keyword-status]'),retry=figure.querySelector('[data-keyword-retry]');
  const current=()=>figure.isConnected&&isCurrent();let loading=false;
  async function load(){
   if(loading||!current())return;loading=true;const held=figure.ownerDocument?.activeElement===retry;retry.disabled=true;status.textContent='Loading saved recovery checks…';
   try{
    if(!cached){if(!pending)pending=(async()=>{const controller=new AbortController();let timer;try{return await Promise.race([(async()=>{const response=await fetcher(base+'control-summary.json',{signal:controller.signal});if(!response.ok)throw Error();return validate(await response.json())})(),new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Timed out'))},10000)})])}finally{clearTimeout(timer);controller.abort()}})().then(value=>cached=value).finally(()=>{pending=null});await pending}
    if(!current())return;view.innerHTML=content(cached);status.textContent='';if(held&&(figure.ownerDocument.activeElement===retry||figure.ownerDocument.activeElement===figure.ownerDocument.body))view.querySelector('[data-keyword-heading]')?.focus({preventScroll:true});retry.hidden=true;
   }catch{if(current()){status.textContent='Saved checks could not load. Retry or open the control figure.';view.innerHTML='<a href="'+svg+'"><img src="'+svg+'" alt="Saved known-message recovery checks"></a>';retry.hidden=false}}
   finally{loading=false;if(current()){retry.disabled=false;if(held&&!retry.hidden&&figure.ownerDocument.activeElement===figure.ownerDocument.body)retry.focus({preventScroll:true})}}
  }
  retry.addEventListener('click',load);return load();
 }
 const api={canRender,validate,content,render,bind};if(typeof module!=='undefined')module.exports=api;else root.KeywordSkipView=api;
})(globalThis);
