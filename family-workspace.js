/* One finite research family: review, browser execution, saved coverage, next work. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const F=typeof module==='object'&&module.exports?require('./research-family.js'):root.ResearchFamily;
 const Runner=typeof module==='object'&&module.exports?require('./family-runner.js'):root.FamilyRunner;
 const Controls=typeof module==='object'&&module.exports?require('./local-plan-controls.js'):root.LocalPlanControls;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const compact=c=>({repeat:'Repeat', 'plaintext-autokey':'Plaintext', 'ciphertext-autokey':'Ciphertext'}[c.mode])+' · '+c.direction+' · '+c.reset;
 const Evidence=typeof module==='object'&&module.exports?require('./computation-evidence.js'):root.ComputationEvidence;
 const FAMILY='deor-feedback-v1',HEX=/^[a-f0-9]{64}$/;
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 async function hash(value,cryptoAPI){return Array.from(new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(value)))),b=>b.toString(16).padStart(2,'0')).join('');}
 function selectedRoute(value){
  if(typeof value!=='string'||!value.startsWith('#'))return null;const params=new URLSearchParams(value.slice(1));
  if(params.get('family')!==FAMILY||[...params.keys()].some(k=>!['family','case','revision'].includes(k))||new Set(params.keys()).size!==[...params.keys()].length)return null;
  const caseId=params.get('case'),revision=params.get('revision');
  if(revision!==null&&(!caseId||!HEX.test(revision))||caseId!==null&&!/^(?:repeat|plaintext-autokey|ciphertext-autokey)--(?:subtract|add)--(?:page|line|word)--lp2-(?:[0-4][0-9]|5[1-5])$/.test(caseId))return null;
  return {caseId,revision};
 }
 const route=value=>selectedRoute(value)!==null;
 async function checkedSavedCase(value,{caseId,revision,bundle,crypto:cryptoAPI=root.crypto}){
  if(value?.familyId!==FAMILY||value.caseId!==caseId||value.revision!==revision)throw Error('The saved result belongs to another case.');
  if(Object.hasOwn(value,'source')){
   if(!exact(value,['familyId','revision','caseId','source'])||!exact(value.source,['task','inputVersion','run'])||value.source.inputVersion!=='raw')throw Error('The shared result source is malformed.');
   const snapshot=await F.snapshot(bundle,cryptoAPI);if(revision!==snapshot.revision)throw Error('The shared case uses another input snapshot.');
   const expected=(await F.prepare(bundle,[caseId],cryptoAPI)).cases[0].task,source=value.source;
   const result=await E.verify(source.task,source.run.result,cryptoAPI),comparison=await Evidence.compare(expected,'raw',[source],cryptoAPI);
   if(comparison.coveredPages.length!==1||comparison.remainingPages.length)throw Error('The original run does not cover this case.');
   const pageId=expected.pages[0].id;
   return {task:expected,output:result.transformed.find(p=>p.page===pageId),matched:result.matches.find(p=>p.page===pageId).matched,sourceTaskId:source.task.taskId,savedAt:source.run.createdAt};
  }
  if(!exact(value,['familyId','revision','caseId','task','result','resultId','verifiedAt'])||!Number.isFinite(Date.parse(value.verifiedAt))||!HEX.test(value.resultId))throw Error('The saved case receipt is malformed.');
  const body={schema:'liberpedia-family-plan-v1',familyId:FAMILY,revision,cases:[{id:caseId,configuration:caseId.slice(0,-8),pageId:caseId.slice(-6),task:value.task}]};
  await F.validateExecutionPlan({...body,planId:await hash(body,cryptoAPI)},cryptoAPI);
  const result=await E.verify(value.task,value.result,cryptoAPI);if(await hash(result,cryptoAPI)!==value.resultId)throw Error('The saved result receipt could not be checked.');
  return {task:value.task,output:result.transformed[0],matched:result.matches[0].matched,sourceTaskId:null,savedAt:value.verifiedAt};
 }
 function savedCaseHTML(id,checked){
  return '<h2>'+esc(id.slice(-6).toUpperCase())+': '+(checked.matched?'opening matches':'opening does not match')+'</h2><p>This rule '+(checked.matched?'recovered':'did not recover')+' the fixed Warning opening on this page.</p>'+opening(checked.task,{transformed:[checked.output]})+(checked.sourceTaskId?'<p><a href="run.html#task='+esc(checked.sourceTaskId)+'">View the original run</a></p>':'')+'<details class="experiment-details"><summary>Complete output</summary><pre>'+esc(checked.output.text)+'</pre></details>';
 }
 function coverage(value,snapshot){
  const valid=new Set(F.caseIds(snapshot));
  if(!value||!Array.isArray(value.completed)||!Array.isArray(value.matched)||value.completed.length>snapshot.totalCases||new Set(value.completed).size!==value.completed.length||new Set(value.matched).size!==value.matched.length||value.completed.some(id=>!valid.has(id))||value.matched.some(id=>!value.completed.includes(id)))throw Error('The saved coverage could not be checked.');
  return {completed:[...value.completed],matched:[...value.matched]};
 }
 function nextCases(snapshot,saved,configuration){
  const done=new Set(saved.completed);
  return F.caseIds(snapshot).filter(id=>id.startsWith(configuration+'--')&&!done.has(id)).slice(0,12);
 }
 function opening(task,result){
  const index=new Map(task.alphabet.map((a,i)=>[a.rune,i])),values=Array.from(result.transformed[0].text).filter(ch=>index.has(ch)).map(ch=>index.get(ch)).slice(0,task.criterion.values.length),wanted=task.criterion.values;
  const mismatch=wanted.findIndex((v,i)=>values[i]!==v),cells=(items,output=false)=>items.map((v,i)=>'<span'+(output&&i===mismatch?' class="is-different" aria-label="Rune '+(i+1)+' differs"':'')+'>'+esc(task.alphabet[v]?.rune||'—')+'</span>').join('');
  return '<div class="family-opening"><p>'+ (mismatch<0?'All 12 opening runes match.':'The first difference is at rune '+(mismatch+1)+'.')+'</p><span class="small">Warning opening</span><div class="family-rune-row">'+cells(wanted)+'</div><span class="small">This output</span><div class="family-rune-row">'+cells(wanted.map((_,i)=>values[i]),true)+'</div></div>';
 }
 function createApp(doc,options={}){
  const win=options.window||root,fetcher=options.fetch||root.fetch.bind(root),cryptoAPI=options.crypto||root.crypto;
  const host=doc.getElementById('task-workspace'),runner=options.runner||Runner.createRunner({crypto:cryptoAPI});
  let generation=0,controller=null,active=null,snapshot=null,bundle=null,saved=null,endpoint=null,selection='',prepared=null,returned=null,busy=false,destroyed=false;
  const $=id=>doc.getElementById(id),live=token=>!destroyed&&token===generation&&route(win.location.hash);
  async function request(url,init={}){
   const abort=new AbortController(),timer=win.setTimeout(()=>abort.abort(),25000),parent=controller?.signal;
   const stop=()=>abort.abort();parent?.addEventListener('abort',stop,{once:true});
   try{const response=await fetcher(url,{...init,signal:abort.signal,redirect:'error'});if(!response.ok){let value;try{value=await response.json();}catch{}throw Error(value?.error||'The research service could not be reached. Please retry.');}return await response.json();}
   finally{win.clearTimeout(timer);parent?.removeEventListener('abort',stop);}
  }
  const set=(id,text)=>{if($(id))$(id).textContent=text;};
  function actions(){if($('family-review'))$('family-review').disabled=busy||!!returned||!nextCases(snapshot,saved,selection).length;if($('family-configuration'))$('family-configuration').disabled=busy||!!returned;if($('family-run'))$('family-run').disabled=busy||!prepared||!!returned;if($('family-save'))$('family-save').disabled=busy;if($('family-stop'))$('family-stop').hidden=!active;}
  function draw(){
   const done=new Set(saved.completed),counts=snapshot.configurations.map(c=>({configuration:c,count:F.caseIds(snapshot).filter(id=>id.startsWith(c.id+'--')&&done.has(id)).length}));
   if(!snapshot.configurations.some(c=>c.id===selection))selection=counts.find(c=>c.count<55)?.configuration.id||counts[0].configuration.id;
   host.innerHTML='<nav class="run-links"><a href="research.html#mode=list&branch=method:feedback">Research map</a></nav><h1>Checking the DEOR key</h1><p class="family-question">Can this key recover the Warning opening on another page?</p><p>Try the key from a known reading, either repeating it or extending it with earlier runes. This family checks 18 rules across 55 pages.</p><section class="family-coverage" aria-labelledby="coverage-title"><h2 id="coverage-title">What has been checked</h2><p id="family-total">'+done.size+' of '+snapshot.totalCases+' page-and-rule combinations saved</p><progress max="'+snapshot.totalCases+'" value="'+done.size+'" aria-labelledby="family-total"></progress><div class="family-coverage-grid">'+counts.map(({configuration:c,count})=>'<span title="'+esc(c.label)+': '+count+' of 55 pages" aria-label="'+esc(c.label)+': '+count+' of 55 pages saved" style="--completed:'+100*count/55+'%"><i></i></span>').join('')+'</div><p class="small">Each bar is one rule across 55 pages. '+saved.matched.length+' saved '+(saved.matched.length===1?'case matches':'cases match')+' the exact opening. A match would need further investigation.</p></section><section aria-labelledby="next-title"><h2 id="next-title">'+(done.size===snapshot.totalCases?'This family is fully checked':'Continue an unfinished rule')+'</h2><label for="family-configuration">Key rule</label><select id="family-configuration">'+counts.map(({configuration:c,count})=>'<option value="'+esc(c.id)+'"'+(c.id===selection?' selected':'')+'>'+esc(compact(c))+' · '+count+'/55</option>').join('')+'</select><p class="small" id="family-rule-description"></p><p class="small" id="family-next-count"></p><button class="primary" id="family-review">Review next batch</button><p class="notice" id="family-status" tabindex="-1" role="status" aria-live="polite"></p><p class="error" id="family-error" role="alert"></p><div id="family-plan"></div><div id="family-results"></div></section><details class="experiment-details"><summary>What this test can tell us</summary><p>Every case starts at the first rune of a complete page and looks for the same first 12 rune indices as the known Warning reading. It does not search for other sentences or score whether the full output is readable.</p><p>The seed is DEOR, encoded as [23, 18, 3, 4] in the ordered 29-rune alphabet. The choices are repeating key, plaintext autokey or ciphertext autokey; addition or subtraction modulo 29; and a restart at each page, line or word. A word ends at every non-rune character. Headings are included. Pages never share key state.</p><p>Inputs are the archived raw text of LP2-00–49 and LP2-51–55. LP2-50 has no runic text and is excluded. This ledger records this exact family and input snapshot; exact matching saved individual runs count here too. Other related experiments are not automatically counted.</p><p><a href="library.html#/experiment/wulfic-autokey-seed-families">Related DEOR research</a></p></details>';
   $('family-configuration').onchange=()=>{selection=$('family-configuration').value;prepared=null;$('family-plan').innerHTML='';updateNext();actions();};
   $('family-review').onclick=review;
   if(saved.completed.length){
    const holder=doc.createElement('details');holder.className='experiment-details';holder.innerHTML='<summary>Inspect saved results</summary><label for="family-saved-case">Saved page and rule</label><select id="family-saved-case">'+saved.completed.map(id=>{const c=snapshot.configurations.find(c=>id.startsWith(c.id+'--'));return '<option value="'+esc(id)+'">'+esc(id.slice(-6).toUpperCase()+' · '+compact(c))+'</option>';}).join('')+'</select><button id="family-read-saved">View saved result</button><p class="error" id="family-read-error" role="alert"></p><div id="family-saved-output"></div>';
    host.appendChild(holder);$('family-read-saved').onclick=readSaved;
   }
   updateNext();actions();
  }
  async function readSaved(){const token=generation,id=$('family-saved-case').value;if(!saved.completed.includes(id))return;const button=$('family-read-saved');button.disabled=true;set('family-read-error','');
   try{const value=await request(endpoint+'/cases/'+encodeURIComponent(id)+'?revision='+snapshot.revision);if(!live(token)||$('family-saved-case').value!==id)return;
    const checked=await checkedSavedCase(value,{caseId:id,revision:snapshot.revision,bundle,crypto:cryptoAPI});if(!live(token)||$('family-saved-case').value!==id)return;
    $('family-saved-output').innerHTML=savedCaseHTML(id,checked);
   }catch(error){if(live(token))set('family-read-error',error.message);}finally{if(live(token))button.disabled=false;}
  }
  function updateNext(){set('family-rule-description',snapshot.configurations.find(c=>c.id===selection)?.label||'');const n=nextCases(snapshot,saved,selection).length;set('family-next-count',n?'The next batch checks '+n+' uncompleted pages with this rule.':'All 55 pages have saved results for this rule. Choose another rule.');}
  async function review(){if(busy||returned)return;const token=generation,requested=nextCases(snapshot,saved,selection);busy=true;set('family-error','');set('family-status','Preparing the next uncovered pages…');actions();
   try{const value=await request(endpoint+'/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:snapshot.revision,caseIds:requested})});if(!live(token))return;await F.validatePlan(value.plan,bundle,cryptoAPI);if(E.stable(value.plan.cases.map(c=>c.id))!==E.stable(requested.slice().sort()))throw Error('The prepared batch differs from the requested pages.');
    if(!Array.isArray(value.controls)||value.controls.length!==value.plan.cases.length)throw Error('The calculation checks are incomplete.');
    for(const item of value.plan.cases){const suite=value.controls.filter(c=>c.caseId===item.id);if(suite.length!==1)throw Error('The calculation checks belong to another batch.');await Controls.validate(suite[0].suite,item.task,cryptoAPI);}if(!live(token))return;
    prepared=value;$('family-plan').hidden=false;const c=snapshot.configurations.find(c=>c.id===selection);$('family-plan').innerHTML='<section class="family-plan"><h3>Ready to check '+value.plan.cases.length+' pages</h3><p>'+esc(c.label)+'. Check the exact Warning opening.</p><p class="small">'+value.plan.cases.map(c=>esc(c.pageId.toUpperCase())).join(', ')+'</p><p class="small">Known-answer checks run first. Your device does the calculation; nothing is saved until you submit the results.</p><div class="run-actions"><button id="family-run" class="primary">Run in browser</button><button id="family-stop" hidden>Stop</button></div></section>';$('family-run').onclick=run;$('family-stop').onclick=stop;set('family-status','');
   }catch(error){if(live(token)){set('family-status','');set('family-error',error.message);}}finally{if(live(token)){busy=false;actions();}}
  }
  async function run(){if(busy||!prepared||returned)return;const token=generation;busy=true;set('family-error','');
   try{active=runner.start(prepared.plan,prepared.controls,{onProgress:p=>{if(live(token))set('family-status',(p.phase==='controls'?'Checking the calculation':'Checking pages')+': '+p.completed+' of '+p.total);}});actions();const value=await active.promise;if(!live(token))return;returned=value;set('family-status','Finished on your device. Results have not been saved.');showResults();
   }catch(error){if(live(token)){set('family-status',error.name==='AbortError'?'Stopped. No results were saved.':'');if(error.name!=='AbortError')set('family-error',error.message);}}finally{if(live(token)){active=null;busy=false;actions();}}
  }
  function stop(){active?.cancel();}
  function showResults(){
   const rows=returned.results.map(item=>{const c=returned.plan.cases.find(c=>c.id===item.caseId),page=item.result.transformed[0],match=item.result.matches.some(m=>m.page===c.pageId&&m.matched===true);return {case:c,result:item.result,page,match};});
   const hits=rows.filter(row=>row.match).length;$('family-plan').hidden=true;
   $('family-results').innerHTML='<section class="family-results"><h2 id="family-result-heading" tabindex="-1">'+ (hits?'An opening matched':'No Warning opening found')+'</h2><p>'+ (hits?hits+' of these '+rows.length+' cases match the fixed opening. Inspect the complete output before interpreting this.':'None of these '+rows.length+' cases began with the 12 runes of the Warning. This rules out this opening for these exact pages and settings; it does not rule out other text.')+'</p><h3>First page in this batch · '+esc(rows[0].case.pageId.toUpperCase())+'</h3>'+opening(rows[0].case.task,rows[0].result)+'<button id="family-save" class="primary">Save these results</button><p class="notice" id="family-save-status" role="status"></p><details class="experiment-details"><summary>Inspect outputs and reproduce</summary><p><button id="family-download">Download run data</button> · <a href="tools/reproduce_family.py" download>Batch runner</a> · <a href="tools/research_runner.py" download>Calculation engine</a></p><p class="small">For optional offline reproduction, keep both Python files beside the run data. This checks the manuscript calculations; the download does not contain the synthetic control inputs.</p><pre>python reproduce_family.py --batch deor-feedback-'+returned.plan.planId.slice(0,12)+'.json --out reproduced.json</pre>'+rows.map(row=>'<details><summary>'+esc(row.case.pageId.toUpperCase())+' output</summary><pre>'+esc(row.page?.output||row.page?.text||E.stable(row.result))+'</pre></details>').join('')+'</details></section>';
   $('family-save').onclick=save;$('family-download').onclick=download;$('family-result-heading').focus();
  }
  function download(){if(!returned)return;const blob=new Blob([JSON.stringify(returned,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=doc.createElement('a');a.href=url;a.download='deor-feedback-'+returned.plan.planId.slice(0,12)+'.json';a.click();win.setTimeout(()=>URL.revokeObjectURL(url),1000);}
  async function save(){if(busy||!returned)return;const token=generation,value=returned;busy=true;set('family-error','');set('family-save-status','Checking and saving the complete batch…');actions();
   try{const receipt=await request(endpoint+'/results',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});if(!live(token))return;if(receipt.familyId!==snapshot.id||receipt.revision!==snapshot.revision||E.stable([...receipt.accepted].sort())!==E.stable(value.plan.cases.map(c=>c.id).sort()))throw Error('The saved receipt does not match this batch.');
    const fresh=await request(endpoint);if(!live(token))return;if(fresh.family.revision!==snapshot.revision)throw Error('Results were saved for the earlier input snapshot. Reload to inspect the current family.');const checked=coverage(fresh.coverage,snapshot);if(value.plan.cases.some(c=>!checked.completed.includes(c.id)))throw Error('The saved coverage has not updated. Retry saving this same batch.');saved=checked;returned=null;prepared=null;if(!nextCases(snapshot,saved,selection).length)selection='';draw();set('family-status','Saved. Those pages are now covered; the next batch uses remaining pages.');$('family-status').focus?.();
   }catch(error){if(live(token)){set('family-save-status','Your local results are kept. They have not been confirmed as saved here.');set('family-error',error.message+' Retry Save these results.');}}finally{if(live(token)){busy=false;actions();}}
  }
  async function load(){const token=++generation;controller?.abort();active?.cancel();controller=new AbortController();active=null;busy=false;returned=null;prepared=null;host.innerHTML='<h1>Checking the DEOR key</h1><p role="status">Loading saved coverage…</p>';
   try{const [config,inputs]=await Promise.all([request('data/assistant.json'),request('data/local-run-inputs.json')]);if(!live(token))return;const base=new URL(config.localTaskEndpoint),here=new URL(win.location.href);if(base.pathname!=='/tasks'||base.search||base.hash||base.username||base.password||!(base.protocol==='https:'||here.hostname==='127.0.0.1'&&base.hostname==='127.0.0.1'&&base.protocol==='http:'))throw Error('The research service is not configured.');endpoint=base.origin+'/families/'+FAMILY;bundle=inputs;snapshot=await F.snapshot(bundle,cryptoAPI);
    const selected=selectedRoute(win.location.hash);
    if(selected?.caseId){
     const revision=selected.revision||snapshot.revision,value=await request(endpoint+'/cases/'+encodeURIComponent(selected.caseId)+'?revision='+revision);if(!live(token))return;
     const checked=await checkedSavedCase(value,{caseId:selected.caseId,revision,bundle,crypto:cryptoAPI});if(!live(token))return;
     host.innerHTML='<nav class="run-links"><a href="run.html#family='+FAMILY+'">Back to DEOR checks</a></nav><h1>Saved DEOR result</h1><p>'+esc(snapshot.configurations.find(c=>selected.caseId.startsWith(c.id+'--')).label)+'</p>'+savedCaseHTML(selected.caseId,checked)+'<p class="small">This is a saved calculation for these exact inputs. It does not establish a complete reading.</p>';return;
    }
    const value=await request(endpoint);if(!live(token))return;if(value.family.id!==snapshot.id||value.family.revision!==snapshot.revision)throw Error('The site and research service use different input snapshots. Reload after the update finishes.');saved=coverage(value.coverage,snapshot);draw();
   }catch(error){if(live(token)){host.innerHTML='<h1>Checking the DEOR key</h1><p class="error" role="alert">'+esc(error.message)+'</p><button id="family-retry">Retry</button><p><a href="research.html#mode=list">Back to research map</a></p>';$('family-retry').onclick=load;}}
  }
  const changed=()=>{if(route(win.location.hash))void load();else win.location.reload();};win.addEventListener('hashchange',changed);const ready=load();
  return {ready,destroy(){destroyed=true;generation++;controller?.abort();active?.cancel();win.removeEventListener('hashchange',changed);}};
 }
 const api={route,selectedRoute,checkedSavedCase,coverage,nextCases,opening,createApp};if(typeof module==='object'&&module.exports)module.exports=api;else root.FamilyWorkspace=api;
})(typeof globalThis!=='undefined'?globalThis:this);
