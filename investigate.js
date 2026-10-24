/* Standalone confirmation/research flow. All research comes from the real registry. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'?require('./claim-specification.js'):root.ClaimSpecification;
 const M=typeof module!=='undefined'?require('./assistant-markdown.js'):root.AssistantMarkdown;
 const S=typeof module!=='undefined'?require('./assistant-search.js'):root.AssistantSearch;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const prov={kind:'supplied',refs:['original wording']};
 const known=v=>C.field('specified',v,prov);
 const editProvenance={kind:'user_clarification',refs:['interpretation editor']};
 const clarified=v=>C.field('specified',v,editProvenance);
 function parseScope(text,provenance=prov){
  if(!text.trim())return C.field();
  const selected=[];
  for(const item of text.toLowerCase().split(/\s*(?:,|;|\band\b)\s*/)){
   const match=item.trim().match(/^lp([12])-(\d{1,2})(?:\s*[-–—]\s*(?:lp\1-)?(\d{1,2}))?$/);
   if(!match)throw Error('Use exact page IDs, such as LP2-15, LP2-17 or LP2-15–17.');
   const start=Number(match[2]),end=match[3]===undefined?start:Number(match[3]);
   if(end<start||end-start>74)throw Error('Check the page range.');
   for(let i=start;i<=end;i++)selected.push('lp'+match[1]+'-'+String(i).padStart(2,'0'));
  }
  return C.field('specified',{pages:C.pages(selected)},provenance);
 }
 function initialDraft(text){
  // Only explicit known reversal ambiguities are interpreted. Arbitrary method
  // wording remains exactly that: editable supplied wording, not parsed code.
  let id='described_method',label=text,unresolved=[];
  if(/\brevers(?:e|ing)\b[^.!?]*\bprime values\b[^.!?]*\brows?\b/i.test(text)&&! /\bdigits?\b/i.test(text)){
   unresolved=[{kind:'operation_ambiguity',operationIndex:0,text,provenance:prov}];
  }else if(/\brevers(?:e|ing)\b[^.!?]*\bdigits?\b/i.test(text)){id='reverse_value_digits';label='Reverse decimal digits of each value';}
  else if(/\bread each row backwards\b|\breverse (?:the )?(?:rune )?order within each row\b|\breverse each row\b/i.test(text)){id='reverse_row_runes';label='Reverse rune order within rows';}
  const rules={};
  if(/\b(?:keep(?:ing)?|preserv(?:e|ing)) word boundaries\b/i.test(text))rules.wordBoundaries=known('preserve');
  // Recognize only fully qualified, explicit page IDs/ranges. A shorthand
  // continuation is kept unresolved instead of claiming a partial exact set.
  const refs=text.match(/\bLP[12]-\d{1,2}(?:\s*[-–—]\s*(?:LP[12]-)?\d{1,2})?/gi)||[];
  let scope=C.field();
  if(refs.length&&!/LP[12]-\d{1,2}\s*(?:and|,)\s*\d/i.test(text)){
   try{scope=parseScope(refs.join(','));}catch{/* Keep unknown and let the user edit. */}
  }
  return C.createDraft({source:{text},method:known({operations:[{id,label}]}),scope,rules,unresolved});
 }
 function validateAnswer(data,knownDocuments){
  if(!data||typeof data.answer!=='string'||!data.answer.trim()||data.answer.length>12000||!Array.isArray(data.sources)||!data.sources.length||data.sources.length>4)throw Error('A sourced comparison is unavailable. You can inspect the related records below.');
  const seen=new Set();
  for(const source of data.sources){
   if(!source||seen.has(source.id)||!knownDocuments.some(d=>d.id===source.id&&d.href===source.href)||!M.safe(source.href))throw Error('The comparison returned an unrecognized source.');
   const current=knownDocuments.find(d=>d.id===source.id&&d.href===source.href);
   if(source.text!==current.text)throw Error('The source record changed while this comparison was prepared. Reload the research and try again.');
   seen.add(source.id);
  }
  const citations=[...data.answer.matchAll(/\[(\d+)\]/g)].map(m=>Number(m[1]));
  if(!citations.length||citations.some(n=>n<1||n>data.sources.length))throw Error('The comparison could not be checked against its sources.');
  return {answer:data.answer,sources:data.sources.map(s=>knownDocuments.find(d=>d.id===s.id&&d.href===s.href)),cached:Boolean(data.cached)};
 }
 function rowsHTML(spec){return '<dl>'+C.reviewRows(spec).filter(r=>r.label!=='Unresolved'&&(r.tags||[]).length).map(r=>'<div class="tag-row"><dt>'+esc(r.label)+'</dt><dd>'+r.tags.map(t=>'<span class="tag'+(t.unknown?' unknown':'')+'">'+esc(t.text)+'</span>').join('')+'</dd></div>').join('')+'</dl>';}
 function methodText(spec){return C.reviewRows(spec).find(r=>r.label==='Method').tags.map(t=>t.text).join('; then ');}
 const nativeLinks=html=>html.replace(/<a /g,'<a target="_blank" rel="noopener" ').replace(/title="([^"]*)"/g,'title="$1 (opens in a new tab)"').replace(/href="#\//g,'href="index.html#/');
 function sourceHTML(doc,records){
  const record=records.find(r=>r.id===doc.id);
  return '<section class="source"><h3><a target="_blank" rel="noopener" title="Open source in a new tab" href="index.html'+esc(doc.href)+'">'+esc(doc.title)+'</a></h3>'+
   (record?'<p>'+esc(record.reader_finding||record.finding)+'</p><p><strong>Limit:</strong> '+esc(record.reader_limit||record.limitations)+'</p>':'<p>Supporting manuscript context, not evidence that the idea was tested.</p>')+'</section>';
 }
 function packetHTML(packet){
  const s=packet.confirmed,r=packet.research,docs=r.evidence.documents||[];
  return '<h1>Liberpedia · Research note</h1><p>'+esc(r.at)+'</p>'+rowsHTML(s)+
   '<h2>Research comparison</h2><div class="answer">'+nativeLinks(M.render(r.answer,docs))+'</div>'+
   '<h2>Sources</h2>'+docs.map(d=>sourceHTML(d,r.evidence.records)).join('')+
   '<h2>Original idea</h2><pre>'+esc(s.source.text)+'</pre>';
 }
 function createApp(doc,{fetcher=root.fetch.bind(root),now=()=>new Date().toISOString(),id=()=>root.crypto.randomUUID(),printer=()=>root.print(),schedule=setTimeout,unschedule=clearTimeout}={}){
  const host=doc.getElementById('investigate'),printHost=doc.getElementById('print-snapshot');
  let stage='input',draft=null,confirmed=null,result=null,packet=null,editing=false,editingBackup=null,raw='',records=[],documents=[],endpoint=null,loaded=false,loadError='',message='',error='',busy=false,controller=null,generation=0,registryId='';
  const incoming=new URLSearchParams(doc.defaultView?.location?.search||'');
  raw=incoming.get('q')||'';
  let legacyScope=null;
  const pageHint=incoming.getAll('pages').join(',');
  if(pageHint){try{legacyScope=parseScope(pageHint,{kind:'supplied',refs:['URL page hint']});}catch{message='The linked page selection could not be read. You can enter exact pages when reviewing the idea.';}}
  const focus=selector=>doc.querySelector(selector)?.focus();
  function stop(){generation++;controller?.abort();controller=null;busy=false;}
  function render(){
   const prior=doc.activeElement?.id;
   if(stage==='input'){
    host.innerHTML='<h1>Have we tried it?</h1><p>Describe the idea or paste the rule you want to check.</p><form id="intake"><label class="sr-only" for="idea">Your idea</label><textarea id="idea" required maxlength="1500" rows="6" placeholder="For example: reverse the prime values of each row on LP2-15">'+esc(raw)+'</textarea><div class="actions"><button class="primary" type="submit">Review idea</button></div></form>';
   }else{
    host.innerHTML='<button class="back" id="back" type="button">Back to idea</button><h1 id="review-title" tabindex="-1">'+(stage==='research'?'Research comparison':'Is this the idea?')+'</h1>'+
     (stage==='research'?'<details class="confirmed"><summary>Your idea</summary>':'<section aria-label="Interpreted idea">')+rowsHTML(confirmed||draft)+
     '<div class="actions"><button class="left" id="edit" type="button">Edit interpretation</button></div>'+(stage==='research'?'</details>':'</section>')+
     (editing?editorHTML():questionsHTML())+
     (stage==='review'?'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'')+
     (stage==='review'&&!editing&&!C.questions(draft).length?'<p class="small">Unstated inputs and success criteria remain undecided. Confirming this wording does not mean a test has run.</p><div class="actions"><button class="primary" id="confirm" '+(!loaded?'disabled':'')+' type="button">Confirm and find research</button></div>':'')+
     (stage==='research'?researchHTML()+'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'');
   }
   host.insertAdjacentHTML('beforeend','<p id="status" class="notice small" role="status">'+esc(message||(!loaded&&!loadError?'Loading research records…':''))+'</p><p id="error" class="notice error" role="alert">'+esc(error||loadError)+'</p>'+(!loaded&&loadError?'<button id="reload" type="button">Retry loading research</button>':'')+'<p class="small privacy">'+(endpoint?'Research questions are processed by Cloudflare. Don’t include private information.':'')+'</p>');
   bind();
   if(prior&&doc.getElementById(prior))focus('#'+prior);
  }
  function editorHTML(){
   const scope=draft.scope.status==='specified'?(draft.scope.value.pages||[]).map(p=>p.toUpperCase()).join(', '):'';
   const method=draft.method.status==='specified'?methodText(draft):'';
   const rule=C.reviewRows(draft).find(r=>r.label==='Rules').tags.filter(t=>!t.unknown).map(t=>t.text).join('\n');
   return '<form class="editor" id="editor"><label for="edit-aim">Aim <span class="small">(optional)</span></label><input type="text" id="edit-aim" maxlength="240" value="'+esc(draft.aim.status==='specified'?draft.aim.value:'')+'"><label for="edit-method">Method</label><textarea id="edit-method" required maxlength="1200">'+esc(method)+'</textarea><label for="edit-scope">Pages <span class="small">(optional)</span></label><input type="text" id="edit-scope" value="'+esc(scope)+'" placeholder="LP2-15, LP2-17"><label for="edit-rules">Additional rules <span class="small">(optional)</span></label><textarea id="edit-rules" maxlength="600">'+esc(rule)+'</textarea><div class="actions"><button id="cancel-edit" type="button">Cancel</button><button class="primary" type="submit">Review changes</button></div></form>';
  }
  function questionsHTML(){
   if(stage!=='review')return '';
   const q=C.questions(draft)[0];if(!q)return '';
   return '<form id="clarification" class="question"><fieldset><legend>'+esc(q.prompt)+'</legend>'+(q.example?'<p class="example">'+esc(q.example)+'</p>':'')+q.choices.map(c=>'<label><input type="radio" name="choice" value="'+esc(c.id)+'" required><span>'+esc(c.label)+(c.example?'<small class="example">'+esc(c.example)+'</small>':'')+'</span></label>').join('')+'</fieldset><label for="other-detail" id="other-label" hidden>Describe what you mean</label><textarea id="other-detail" hidden></textarea><div class="actions"><button class="primary" type="submit">Review idea</button></div></form>';
  }
  function researchHTML(){
   const controls='<div class="actions">'+(busy?'<button id="cancel" type="button">Stop waiting</button>':(!result?'<button id="retry" type="button">Try comparison again</button>':''))+(packet?'<button id="print" type="button">Print research note</button>':'')+'</div>';
   if(result)return '<h2>What the records establish</h2><div class="answer">'+nativeLinks(M.render(result.answer,result.sources))+'</div><p class="small">AI comparison · Check the cited scope and findings.'+(result.cached?' Reused answer.':'')+'</p>'+result.sources.map(d=>sourceHTML(d,records)).join('')+controls;
   const q=C.retrievalQuery(confirmed),scope=C.queryForResearch(confirmed,{maxLength:6000}),related=q.query?S.select(documents,q.query,scope.pages||[]).filter(d=>d.kind==='experiment').slice(0,2):[];
   return (busy?'<p aria-live="polite">Comparing the confirmed idea with published research…</p>':'')+controls+(related.length?'<h2>Related records</h2>'+related.map(d=>sourceHTML(d,records)).join(''):'');
  }
  function bind(){
   doc.getElementById('idea')?.addEventListener('input',event=>{raw=event.target.value;});
   doc.getElementById('intake')?.addEventListener('submit',event=>{
    event.preventDefault();raw=doc.getElementById('idea').value;if(!raw.trim())return;
    stop();draft=initialDraft(raw);if(legacyScope){draft=C.revise(draft,{scope:legacyScope});legacyScope=null;message='The linked page selection is included in the scope below; the original wording is unchanged.';}else message='';confirmed=null;result=null;packet=null;printHost.replaceChildren();editing=false;stage='review';error='';render();focus('#review-title');
   });
   doc.getElementById('back')?.addEventListener('click',()=>{stop();stage='input';editing=false;confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#idea');});
   doc.getElementById('edit')?.addEventListener('click',()=>{stop();editingBackup={stage,draft,confirmed,result,packet,message,error};editing=true;stage='review';draft=C.revise(draft,{});confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#edit-method');});
   doc.getElementById('cancel-edit')?.addEventListener('click',()=>{editing=false;if(editingBackup){({stage,draft,confirmed,result,packet,message,error}=editingBackup);editingBackup=null;if(packet)printHost.innerHTML=packetHTML(packet);}render();focus('#edit');});
   doc.getElementById('editor')?.addEventListener('submit',event=>{
    event.preventDefault();try{
     const wording=doc.getElementById('edit-method').value.trim();
     const current=draft.method.status==='specified'?methodText(draft):'';
     const ruleText=doc.getElementById('edit-rules').value.trim();
     const previousRules=C.reviewRows(draft).find(r=>r.label==='Rules').tags.filter(t=>!t.unknown).map(t=>t.text).join('\n');
     const patch={aim:doc.getElementById('edit-aim').value.trim()?clarified(doc.getElementById('edit-aim').value.trim()):C.field(),scope:parseScope(doc.getElementById('edit-scope').value,editProvenance)};
     if(ruleText!==previousRules){patch.rules=Object.fromEntries(C.RULES.map(k=>[k,C.field()]));patch.rules.exceptionalCases=ruleText?clarified(ruleText):C.field();}
     if(wording!==current)patch.method=clarified({operations:[{id:'described_method',label:wording}]});
     draft=C.revise(draft,patch);
     if(patch.method)draft.unresolved=draft.unresolved.filter(c=>!['operation_ambiguity','custom_interpretation'].includes(c.kind));
     editing=false;editingBackup=null;error='';render();focus('#review-title');
    }catch(e){error=e.message;doc.getElementById('error').textContent=error;}
   });
   doc.getElementById('clarification')?.addEventListener('change',()=>{
    const other=doc.querySelector('input[name=choice]:checked')?.value==='other';
    doc.getElementById('other-label').hidden=!other;doc.getElementById('other-detail').hidden=!other;doc.getElementById('other-detail').required=other;
   });
   doc.getElementById('clarification')?.addEventListener('submit',event=>{
    event.preventDefault();const choice=doc.querySelector('input[name=choice]:checked')?.value;if(!choice)return;
    const q=C.questions(draft)[0];
    if(choice==='other'){
     const text=doc.getElementById('other-detail').value.trim();if(!text)return;
     draft=C.clarify(draft,q.id,choice,text);editing=true;message='Your explanation is kept. Edit the method wording to make the interpretation explicit.';
    }else{draft=C.clarify(draft,q.id,choice);message='';}
    error='';render();focus(editing?'#edit-method':'#review-title');
   });
   doc.getElementById('confirm')?.addEventListener('click',()=>{
    try{confirmed=C.confirm(draft,{id:id(),at:now()});const q=C.queryForResearch(confirmed,{maxLength:6000}),compact=C.retrievalQuery(confirmed);
     if(q.needsShorter||compact.needsShorter){error='This idea exceeds the comparison’s length limit. Shorten the wording without removing important rules.';confirmed=null;render();return;}
     if(q.needsClarification){error='The interpretation still needs clarification before automatic comparison.';confirmed=null;render();return;}
     stage='research';error='';message='';compare();
    }catch(e){error=e.message;render();}
   });
   doc.getElementById('cancel')?.addEventListener('click',()=>{stop();message='Stopped waiting. Your confirmed idea is kept.';error='';render();});
   doc.getElementById('retry')?.addEventListener('click',()=>compare());
   doc.getElementById('reload')?.addEventListener('click',()=>load());
   doc.getElementById('print')?.addEventListener('click',()=>{if(packet){printHost.innerHTML=packetHTML(packet);printer();}});
  }
  async function json(url,options){const response=await fetcher(url,options);if(!response.ok)throw Error('Research is temporarily unavailable. Try again or read the related records.');return response.json();}
  function availability(){
   const status=doc.getElementById('status'),notice=doc.getElementById('error'),confirm=doc.getElementById('confirm');
   if(status)status.textContent=message||(!loaded&&!loadError?'Loading research records…':'');
   if(notice)notice.textContent=error||loadError;
   if(confirm)confirm.disabled=!loaded;
   const privacy=doc.querySelector('.privacy');if(privacy)privacy.textContent=endpoint?'Research questions are processed by Cloudflare. Don’t include private information.':'';
   const retry=doc.getElementById('reload');
   if(loaded)retry?.remove();
   else if(loadError&&!retry){host.insertAdjacentHTML('beforeend','<button id="reload" type="button">Retry loading research</button>');doc.getElementById('reload')?.addEventListener('click',()=>load());}
  }
  async function load(){
   loadError='';availability();
   try{
    const [registry,config]=await Promise.all([json('data/experiments.json',{signal:AbortSignal.timeout(8000)}),json('data/assistant.json',{signal:AbortSignal.timeout(8000)})]);
    if(!Array.isArray(registry.records))throw Error('Research records could not be read.');
    records=registry.records.filter(r=>r.status==='published');documents=S.experimentDocs(records);
    if(!records.length)throw Error('No published research records are available.');
    endpoint=typeof config.endpoint==='string'&&/^https:\/\/[a-z0-9.-]+\/ask$/.test(config.endpoint)?config.endpoint:null;
    const hash=await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(registry)));
    registryId='sha256-json:'+Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
    loaded=true;
    availability();
    // Optional context cannot delay confirmation or rerender an editor/input.
    json('data/assistant-index.json',{signal:AbortSignal.timeout(5000)}).then(index=>{
     documents.push(...(index.documents||[]).filter(d=>typeof d.id==='string'&&M.safe(d.href)));
    }).catch(()=>{});
   }catch(e){loadError=e.message;loaded=false;}
   availability();
  }
  async function compare(){
   stop();const token=generation,snapshot=confirmed;
   if(!snapshot)return;
   if(!endpoint){error='Automatic comparison is unavailable. The related records remain available.';render();return;}
   const query=C.queryForResearch(snapshot,{maxLength:6000}),compact=C.retrievalQuery(snapshot);
   if(!query.query||!compact.query){error='The confirmed wording cannot fit this comparison. Edit the idea before retrying.';render();return;}
   busy=true;message='';error='';render();const requestController=new AbortController();controller=requestController;
   const timer=schedule(()=>requestController.abort(),30000);
   try{
    const data=await json(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:compact.query,confirmedQuery:query.query,pages:query.pages.length<=2?query.pages:[]}),signal:requestController.signal});
    if(token!==generation||confirmed!==snapshot)return;
    if(!data.answer&&data.reason==='no-matching-records'){message='No close record was returned for this wording. That does not establish that the idea is new or untried.';return;}
    const checked=validateAnswer(data,documents);
    const evidenceRecords=records.filter(r=>checked.sources.some(s=>s.kind==='experiment'&&s.id===r.id));
    if(!evidenceRecords.length)throw Error('No research record supports this comparison.');
    const research=C.bindResearch(snapshot,{id:id(),at:now(),evidence:{snapshotId:registryId,records:evidenceRecords,documents:checked.sources},answer:checked.answer});
    packet=C.packetSnapshot(snapshot,research);result=Object.freeze(checked);printHost.innerHTML=packetHTML(packet);
   }catch(e){if(token===generation)error=e.name==='AbortError'?'The comparison timed out. Your confirmed idea is kept; try again.':e.message;}
   finally{unschedule(timer);if(token===generation){busy=false;controller=null;render();}}
  }
  render();load();
  return {getSnapshot:()=>({stage,draft,confirmed,result,packet,busy}),destroy:stop};
 }
 const api={parseScope,initialDraft,validateAnswer,rowsHTML,packetHTML,createApp};
 if(typeof module!=='undefined')module.exports=api;
 else{root.Investigate=api;if(root.document?.getElementById('investigate'))root.investigateApp=createApp(root.document);}
})(globalThis);
