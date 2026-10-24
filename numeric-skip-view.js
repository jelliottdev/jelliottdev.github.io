/* Declared skip-search receipts. Presentation only; no decoding or parameter search. */
(function(root){
 const prefix='experiments/records/',configs={
  'payload-phase-skip-grid':{kind:'phase',plan:'frozen-plan.json',svg:'payload-phases.svg',screens:30112,full:234,bestPage:'lp2-49',title:'Moving the number-grid key: search results',control:{file:'frozen-plan.json',total:1616,exact:1540}},
  'page-number-prime-skip-grid':{kind:'page',plan:'plan.json',svg:'page-ramp-search.svg',screens:660,full:7,bestPage:'lp2-39',title:'Page-number keys: search results',receipt:'figure-receipt.json',control:{file:'control-check.json',total:112,exact:98}},
  'numeric-stream-skip-grid':{kind:'numeric',plan:'frozen-plan.json',svg:'numeric-skip.svg',screens:36300,full:322,bestPage:'lp2-49',title:'Numeric keys: how the search narrowed',control:{file:'controls/summary.json',branch:'numeric',total:660,exact:634}},
  'artifact-stream-skip-grid':{kind:'artifact',plan:'plan.json',svg:'screen-and-skip.svg',screens:23100,full:194,bestPage:'lp2-49',title:'Puzzle numbers and sequences: search results',receipt:'figure-receipt.json',control:{file:'control/summary.json',branch:'numeric2A',total:420,exact:402}},
  'fibonacci-stream-skip-grid':{kind:'fibonacci',plan:'plan.json',svg:'fibonacci-alias-and-search.svg',screens:92510,full:900,bestPage:'lp2-55',title:'Fibonacci keys: how the search narrowed',control:{file:'preflight-independent-check.json',total:841,exact:805}}
 };
 const cache=new Map(),pending=new Map(),mod=n=>(n%29+29)%29;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function config(id){if(!Object.hasOwn(configs,id))throw Error('Unknown skip figure');return configs[id]}
 function canRender(record,visual){
  if(!Object.hasOwn(configs,record?.id))return false;
  const c=configs[record.id],base=prefix+record.id+'/';
  return visual?.path===base+c.svg&&record.reproduction?.inputs?.some(f=>f.path===base+c.plan)&&
   [...(record.reproduction?.inputs||[]),...(record.reproduction?.outputs||[])].some(f=>f.path===base+c.control.file)&&
   ['results.json',c.svg,...(c.receipt?[c.receipt]:[])].every(name=>record.reproduction?.outputs?.some(f=>f.path===base+name));
 }
 function validate(id,plan,results,receipt,controlReceipt){
  const c=config(id),grid=plan?.grid;let screens,full,passes,best,threshold;
  if(c.kind==='phase'||c.kind==='page'){
   threshold=grid?.full_strict_gate;
   if(c.kind==='phase'){
    if(plan?.schema!=='payload-phase-skip-target-v1'||grid.screen_length!==50||grid.screen_strict_gate!==-6.5||grid.screens!==c.screens)throw Error('Invalid payload phase data');
    screens=results.screens;full=results.full_survivors;passes=results.source_gate_passes;best={page:results.best_full?.page,score:results.best_full?.score};
   }else{
    if(plan?.schema!=='page-number-prime-skip-target-plan-v1'||results?.schema!=='page-number-ramp-target-v1'||grid.screen_runes!==50||grid.screen_strict_gate!==-6.5||grid.settings!==c.screens||results.distinct_signed_arrays!==112)throw Error('Invalid page key data');
    screens=results.target_settings;full=results.full_confirmations;passes=results.source_gate_passes;best={page:results.best_full?.page,score:results.best_full?.full_score};
    const r=receipt;
    if(!r||r.setting?.page!=='lp2-39'||r.setting.sign!==-1||r.setting.atbash!==1||r.rune_position_zero_based!==105||r.previous_transformed_cipher_index!==19||r.current_transformed_cipher_index!==20||r.signed_slope!==28||mod(r.previous_transformed_cipher_index-r.current_transformed_cipher_index)!==r.signed_slope||r.key_pointer_before!==104||r.key_pointer_after!==106)throw Error('Invalid page pair illustration');
   }
  }else if(c.kind==='numeric'){
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
  let controls;
  if(c.kind==='phase'){
   const r=controlReceipt?.control_decision;controls={total:r?.cells,exact:r?.exact_full,score:r?.full_pass};
  }else if(c.kind==='page'){
   if(controlReceipt?.schema!=='page-ramp-independent-controls-v1'||controlReceipt.genuine_skip_plants!==112)throw Error('Invalid page control receipt');
   controls={total:controlReceipt.control_arrays_checked,exact:controlReceipt.exact_recoveries,score:controlReceipt.score_gate_passes};
  }else if(c.control.branch){
   const branch=controlReceipt?.branches?.[c.control.branch];
   if(!branch||branch.target_screen_settings!==c.screens)throw Error('Invalid known-message branch');
   controls={total:branch.cells,exact:branch.exact_complete_recovery,score:branch.full_gate_pass};
  }else{
   if(controlReceipt?.schema!=='fibonacci-preflight-independent-check-v1'||controlReceipt.independently_reconstructed_plants!==841)throw Error('Invalid known-message receipt');
   controls={total:controlReceipt.canonical_pairs,exact:controlReceipt.exact_complete_recovery,score:controlReceipt.score_gate_passes};
  }
  if(controls.total!==c.control.total||controls.exact!==c.control.exact||controls.score!==controls.total)throw Error('Invalid known-message counts');
  return {id,title:c.title,screens,full,passes,threshold,best,receipt,controls,sourceLabels:c.kind==='fibonacci'?results.source_labeled_screens:null};
 }
 function content(data){
  const stages=[['First 50-rune checks',data.screens],['Complete-page checks',data.full],['Passed the fixed English-score test',data.passes]];
  let html='<h3 data-skip-heading tabindex="-1">'+esc(data.title)+'</h3><ol class="numeric-skip-stages" role="list">'+stages.map(([label,count])=>'<li><span>'+label+'</span><strong>'+count.toLocaleString('en-US')+'</strong></li>').join('')+'</ol><p>Only short outputs scoring above −6.5 advanced to a complete-page check.</p><dl class="numeric-skip-scores"><div><dt>Best complete-page score · <a href="#/reader/'+data.best.page+'">'+data.best.page.toUpperCase()+'</a></dt><dd>'+data.best.score.toFixed(3).replace('-','−')+'</dd></div><div><dt>Fixed pass line</dt><dd>'+String(data.threshold).replace('-','−')+'</dd></div></dl><p>Higher scores resemble this model’s English more closely. The best output did not pass. A score alone cannot confirm plaintext.</p>';
  const controls=data.controls;
  html+='<section class="numeric-skip-controls"><h4>Check against known messages</h4><dl class="numeric-skip-control-rows">'+[['Correct reading recovered',controls.exact],['Passed the English-score test',controls.score]].map(([label,count])=>'<div><dt>'+label+'</dt><dd><strong>'+count+' / '+controls.total+'</strong></dd></div>').join('')+'</dl><p><strong>'+(controls.score-controls.exact)+' incorrect outputs still passed the score test.</strong> These are checks on known messages, not independent success probabilities.</p></section>';
  const r=data.receipt;
  if(r&&data.id==='page-number-prime-skip-grid')html+='<section class="numeric-skip-step"><h4>When one key value can be skipped</h4><p>One returned candidate on <a href="#/reader/lp2-39">LP2-39</a> uses neighboring transformed ciphertext values <strong>19 then 20</strong> at rune index 105 (counting from zero).</p><p class="numeric-skip-equation">(19 − 20) mod 29 = 28</p><p>The difference equals this key’s signed step, 28, so the rule permits one skipped value. The key pointer moves from 104 to 106. This is an allowed candidate path, not confirmed plaintext or evidence of a real skip.</p></section>';
  else if(r)html+='<section class="numeric-skip-step"><h4>One rejected key slot in a candidate</h4><p>This is a permitted path from the strongest returned candidate, not confirmed plaintext. Its candidate rune value is <strong>'+r.candidate_plain_index+'</strong>; the preceding ciphertext value is <strong>'+r.previous_transformed_cipher_index+'</strong>.</p><ol><li><strong>Reject key slot '+r.rejected_key_position+' · value '+r.rejected_key_value+'</strong><p class="numeric-skip-equation">'+r.candidate_plain_index+' − '+r.rejected_key_value+' = '+r.previous_transformed_cipher_index+' (mod 29)</p><p>That repeats the preceding ciphertext rune. Consume this key slot and try the same candidate rune again.</p></li><li><strong>Accept key slot '+r.accepted_key_position+' · value '+r.accepted_key_value+'</strong><p class="numeric-skip-equation">'+r.candidate_plain_index+' − '+r.accepted_key_value+' = '+r.current_transformed_cipher_index+' (mod 29)</p><p>This matches the current ciphertext value, '+r.current_transformed_cipher_index+'.</p></li></ol><p>Key slots start at zero. These are alphabet indices, not prime values.</p></section>';
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
       Promise.all([...new Set([c.plan,'results.json',c.control.file,...(c.receipt?[c.receipt]:[])])].map(async name=>{const response=await fetcher(base+name,{signal:controller.signal});if(!response.ok)throw Error();return response.json();})).then(values=>{const names=[...new Set([c.plan,'results.json',c.control.file,...(c.receipt?[c.receipt]:[])])],byName=Object.fromEntries(names.map((name,i)=>[name,values[i]]));return validate(id,byName[c.plan],byName['results.json'],byName[c.receipt],byName[c.control.file]);}),
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
