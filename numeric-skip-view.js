/* Declared skip-search receipts. Presentation only; no decoding or parameter search. */
(function(root){
 const prefix='experiments/records/',configs={
  'numeric-stream-skip-grid':{kind:'numeric',plan:'frozen-plan.json',svg:'numeric-skip.svg',screens:36300,full:322,bestPage:'lp2-49',title:'Numeric keys: how the search narrowed'},
  'artifact-stream-skip-grid':{kind:'artifact',plan:'plan.json',svg:'screen-and-skip.svg',screens:23100,full:194,bestPage:'lp2-49',title:'Artifact keys: how the search narrowed',receipt:'figure-receipt.json'},
  'fibonacci-stream-skip-grid':{kind:'fibonacci',plan:'plan.json',svg:'fibonacci-alias-and-search.svg',screens:92510,full:900,bestPage:'lp2-55',title:'Fibonacci keys: how the search narrowed'}
 };
 const cache=new Map(),pending=new Map(),mod=n=>(n%29+29)%29;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function config(id){if(!Object.hasOwn(configs,id))throw Error('Unknown skip figure');return configs[id]}
 function canRender(record,visual){
  if(!Object.hasOwn(configs,record?.id))return false;
  const c=configs[record.id],base=prefix+record.id+'/';
  return visual?.path===base+c.svg&&record.reproduction?.inputs?.some(f=>f.path===base+c.plan)&&
   ['results.json',c.svg,...(c.receipt?[c.receipt]:[])].every(name=>record.reproduction?.outputs?.some(f=>f.path===base+name));
 }
 function validate(id,plan,results,receipt){
  const c=config(id),grid=plan?.grid;let screens,full,passes,best,threshold;
  if(c.kind==='numeric'){
   threshold=Number(grid?.confirmation?.match(/strict full score > (-?\d+(?:\.\d+)?)/)?.[1]);
   if(plan?.schema!=='numeric-skip-target-v1'||grid.screen_length!==50||grid.screen_strict_threshold!==-6.5||grid.screen_count!==c.screens||!Array.isArray(results?.stream_logs)||results.stream_logs.length!==33||results.stream_logs.reduce((n,s)=>n+s.screens,0)!==c.screens||results.stream_logs.reduce((n,s)=>n+s.full_survivors,0)!==c.full)throw Error('Invalid numeric screen data');
   screens=results.screen_count;full=results.full_survivors;passes=results.above_full_gate;
   best={page:results.best_full?.page,score:results.best_full?.score};
  }else if(c.kind==='fibonacci'){
   threshold=grid?.full_strict_threshold;
   if(plan?.schema!=='fibonacci-canonical-target-plan-v1'||grid.screen_runes!==50||grid.screen_strict_threshold!==-6.5||grid.canonical_screens!==c.screens||results?.schema!=='fibonacci-canonical-target-v1'||results.source_labeled_screens!==c.screens*10||results.source_labeled_full_confirmations!==c.full*10||results.source_labeled_gate_passes!==0)throw Error('Invalid Fibonacci screen data');
   screens=results.canonical_screens;full=results.canonical_full_confirmations;passes=results.canonical_source_gate_passes;
   best={page:results.best_full?.page,score:results.best_full?.full_score};
  }else{
   threshold=grid?.full_strict_gate;
   if(plan?.schema!=='artifact-stream-skip-target-plan-v1'||grid.screen_runes!=='min(50,page length)'||grid.screen_strict_gate!==-6.5||grid.settings!==c.screens||results?.schema!=='artifact-stream-skip-grid-v1'||results.named_streams!==21)throw Error('Invalid artifact screen data');
   screens=results.settings;full=results.full_confirmations;passes=results.source_gate_passes;
   best={page:results.best_full?.page,score:results.best_full?.full_score};
   const r=receipt,b=results.best_full;
   if(!r||r.rune_position_zero_based!==29||r.candidate_plain_index!==28||r.previous_transformed_cipher_index!==26||r.current_transformed_cipher_index!==25||r.rejected_key_position!==29||r.rejected_key_value!==2||r.accepted_key_position!==30||r.accepted_key_value!==3||r.source_final_threshold!==threshold||r.complete_page_score!==best.score||!Array.isArray(b.full_indices)||b.full_indices[r.rune_position_zero_based]!==r.candidate_plain_index||!['page','stream','sign','atbash','offset'].every(key=>r.setting?.[key]===b[key])||r.setting.sign!==1||r.setting.atbash!==0||mod(r.candidate_plain_index-r.rejected_key_value)!==r.previous_transformed_cipher_index||mod(r.candidate_plain_index-r.accepted_key_value)!==r.current_transformed_cipher_index)throw Error('Invalid candidate skip step');
  }
  if(screens!==c.screens||full!==c.full||passes!==0||threshold!==-5.5||best.page!==c.bestPage||!Number.isFinite(best.score)||best.score>=threshold)throw Error('Invalid skip summary');
  return {id,title:c.title,screens,full,passes,threshold,best,receipt,sourceLabels:c.kind==='fibonacci'?results.source_labeled_screens:null};
 }
 function content(data){
  const stages=[['First 50-rune checks',data.screens],['Complete-page checks',data.full],['Passed the fixed English-score test',data.passes]];
  let html='<h3 data-skip-heading tabindex="-1">'+esc(data.title)+'</h3><ol class="numeric-skip-stages" role="list">'+stages.map(([label,count])=>'<li><span>'+label+'</span><strong>'+count.toLocaleString('en-US')+'</strong></li>').join('')+'</ol><p>Only short outputs scoring above −6.5 advanced to a complete-page check.</p><dl class="numeric-skip-scores"><div><dt>Best complete-page score · <a href="#/reader/'+data.best.page+'">'+data.best.page.toUpperCase()+'</a></dt><dd>'+data.best.score.toFixed(3).replace('-','−')+'</dd></div><div><dt>Fixed pass line</dt><dd>'+String(data.threshold).replace('-','−')+'</dd></div></dl><p>Higher scores resemble this model’s English more closely. The best output did not pass. A score alone cannot confirm plaintext.</p>';
  const r=data.receipt;
  if(r)html+='<section class="numeric-skip-step"><h4>One rejected key slot in a candidate</h4><p>This is a permitted path from the strongest returned candidate, not confirmed plaintext. Its candidate rune value is <strong>'+r.candidate_plain_index+'</strong>; the preceding ciphertext value is <strong>'+r.previous_transformed_cipher_index+'</strong>.</p><ol><li><strong>Reject key slot '+r.rejected_key_position+' · value '+r.rejected_key_value+'</strong><p class="numeric-skip-equation">'+r.candidate_plain_index+' − '+r.rejected_key_value+' = '+r.previous_transformed_cipher_index+' (mod 29)</p><p>That repeats the preceding ciphertext rune. Consume this key slot and try the same candidate rune again.</p></li><li><strong>Accept key slot '+r.accepted_key_position+' · value '+r.accepted_key_value+'</strong><p class="numeric-skip-equation">'+r.candidate_plain_index+' − '+r.accepted_key_value+' = '+r.current_transformed_cipher_index+' (mod 29)</p><p>This matches the current ciphertext value, '+r.current_transformed_cipher_index+'.</p></li></ol><p>Key slots start at zero. These are alphabet indices, not prime values.</p></section>';
  if(data.sourceLabels)html+='<p>These counts use '+data.screens.toLocaleString('en-US')+' canonical settings. The source’s '+data.sourceLabels.toLocaleString('en-US')+' labels repeat each setting ten times; they are not extra tests. The downloadable SVG also illustrates this alias relationship.</p>';
  return html;
 }
 function render(id){
  const c=config(id);return '<figure class="experiment-figure numeric-skip-view" data-skip-study="'+id+'"><figcaption><strong>From short screens to complete-page checks</strong></figcaption><p data-skip-status role="status">Loading the saved search counts…</p><button type="button" data-skip-retry hidden>Retry search counts</button><div data-skip-content></div><p><a href="'+prefix+id+'/'+c.svg+'" download>Download the original SVG figure</a></p></figure>';
 }
 async function bind(figure,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!figure||!Object.hasOwn(configs,figure.dataset.skipStudy))return;
  const id=figure.dataset.skipStudy,c=configs[id],base=prefix+id+'/',status=figure.querySelector('[data-skip-status]'),retry=figure.querySelector('[data-skip-retry]'),view=figure.querySelector('[data-skip-content]');
  const current=()=>figure.isConnected&&isCurrent();let loading=false;
  const load=async()=>{
   if(loading||!current())return;loading=true;const hadFocus=figure.ownerDocument?.activeElement===retry;retry.disabled=true;status.textContent='Loading the saved search counts…';
   try{
    if(!cache.has(id)){
     if(!pending.has(id))pending.set(id,(async()=>{
      const controller=new AbortController();let timer;
      try{return await Promise.race([
       Promise.all([c.plan,'results.json',...(c.receipt?[c.receipt]:[])].map(async name=>{const response=await fetcher(base+name,{signal:controller.signal});if(!response.ok)throw Error();return response.json();})).then(([p,r,s])=>validate(id,p,r,s)),
       new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Skip counts timed out'));},10000);})
      ])}finally{clearTimeout(timer);controller.abort();}
     })().then(data=>{cache.set(id,data);return data}).finally(()=>pending.delete(id)));
     await pending.get(id);
    }
    if(!current())return;view.innerHTML=content(cache.get(id));status.textContent='';
    if(hadFocus&&(figure.ownerDocument.activeElement===retry||figure.ownerDocument.activeElement===figure.ownerDocument.body))view.querySelector('[data-skip-heading]')?.focus({preventScroll:true});retry.hidden=true;
   }catch{if(current()){status.textContent='The saved counts could not load. Retry or download the SVG figure below.';retry.hidden=false;}}
   finally{loading=false;if(current()){retry.disabled=false;if(hadFocus&&!retry.hidden&&figure.ownerDocument.activeElement===figure.ownerDocument.body)retry.focus({preventScroll:true});}}
  };
  retry.addEventListener('click',load);return load();
 }
 const api={canRender,validate,content,render,bind};if(typeof module!=='undefined')module.exports=api;else root.NumericSkipView=api;
})(globalThis);
