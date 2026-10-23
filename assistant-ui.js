'use strict';
const ideaAnswers=new Map();
let supportingIndex;
let refreshIdeaSupport=()=>{};
function rememberIdea(key,data){if(ideaAnswers.size>=20)ideaAnswers.delete(ideaAnswers.keys().next().value);ideaAnswers.set(key,{data,until:Date.now()+3600000});}
async function loadSupportingIndex(){
  if(!supportingIndex)supportingIndex=fetch('data/assistant-index.json').then(r=>{if(!r.ok)throw Error();return r.json();}).catch(()=>{supportingIndex=null;return {documents:[]};});
  return supportingIndex;
}
function ideaSourceType(source){
  if(source.kind!=='experiment')return 'Supporting manuscript context';
  const labels={method:'Solving test',measurement:'Manuscript measurement',control:'Control or calibration',
    alphabet:'Alphabet-wide analysis',audit:'Source or input audit',historical:'Historical reproduction',
    replay:'Method replay'};
  return Object.prototype.hasOwnProperty.call(labels,source.recordType)?labels[source.recordType]:'Research record';
}
function experimentSearchResult(r, requestedPages=[]){
  const missing=requestedPages.filter(id=>!r.scope.pages.includes(id));
  const outcome=Object.hasOwn(outcomes,r.outcome)?outcomes[r.outcome]:'Finding not classified';
  return `<article class="experiment-result"><h3><a href="#/experiments/${r.id}">${esc(r.title)}</a></h3>
    <p class="small muted">${esc(r.record_type?.label||'Research record')} · ${esc(experimentTargetSummary(r))} · ${esc(outcome)}</p>
    <p>${esc(r.reader_finding||r.finding)}</p>
    ${r.reader_limit?`<p class="small muted"><strong>Limit:</strong> ${esc(r.reader_limit)}</p>`:''}
    ${missing.length?`<p class="scope-mismatch">Not in this record’s page scope: ${missing.map(id=>esc(id.toUpperCase())).join(', ')}.</p>`:''}
    </article>`;
}
function ideaCoverageNote(record,records){
  const related=record.related.map(id=>records.find(r=>r.id===id)).filter(Boolean);
  return `<details class="experiment-browse-family"><summary><span>${esc(record.title)}</span><span class="small muted">${esc(record.status)}</span></summary>
    <p><a href="#/wiki/${esc(record.guide)}">Read the method guide</a></p><p>${esc(record.coverage)}</p><p><strong>To make a testable version:</strong> ${esc(record.needed)}</p>
    <p><strong>Proposed extension — not run:</strong> ${esc(record.next_test)}</p>
    <p class="small muted">Related records have narrower scopes; these links do not establish that your proposal was tested.</p>
    <ul>${related.map(r=>`<li><a href="#/experiments/${r.id}">${esc(r.title)}</a></li>`).join('')}</ul></details>`;
}
function ideaCoverageView(query='',records=experimentRecords||checkerRecords||[]){
  const families=query?IdeaCoverage.families(methodFamilyRecords||[],query):[];
  const familyHTML=families.length?`<details class="experiment-guide"><summary>Related method guides</summary><ul>${families.map(f=>`<li><a href="#/wiki/${esc(f.guide)}">${esc(f.title)}</a> · <a href="#/wiki/solving-methods?section=family-${esc(f.id)}">Related records</a></li>`).join('')}</ul></details>`:'';
  const failures=(methodFamilyUnavailable?'<p class="small muted">The method-family index could not be loaded. This is not evidence of missing research.</p>':'')+(ideaCoverageUnavailable?'<p class="small muted">Coverage notes could not be loaded. Experiment results remain available.</p>':'');
  const pending=query&&(methodFamilyPending||ideaCoveragePending)?'<p class="small muted" role="status">Checking method families and coverage notes…</p>':'';
  const notes=query?IdeaCoverage.match(ideaCoverageRecords||[],query):(ideaCoverageRecords||[]);
  if(!notes.length)return familyHTML+failures+pending;
  const body=`<p class="small muted">Editorial coverage notes, not experiment findings. “Needs a defined rule” identifies missing bounds; “Partially covered” links narrower tests. Proposed extensions have not been run.</p>${notes.map(record=>ideaCoverageNote(record,records)).join('')}`;
  return familyHTML+failures+pending+(query?`<h2>Coverage of this idea</h2>${body}`:`<details class="experiment-guide"><summary>Common ideas and gaps in coverage</summary>${body}</details>`);
}

function reportedAttemptView(query=''){
  if(query&&reportedAttemptsPending)return '<p class="small muted" role="status">Checking earlier reported approaches…</p>';
  if(reportedAttemptsUnavailable)return '<p class="small muted">The prior-work index could not be loaded. <a href="#/wiki/reported-attempts">Open the saved register</a>.</p>';
  if(!query)return '<p class="small muted">Looking for earlier proposals that have not been fully retested? <a href="#/wiki/reported-attempts">Browse the reported-attempt register</a>.</p>';
  const hits=IdeaCoverage.match(reportedAttemptRecords||[],query);
  if(!hits.length)return '';
  const labels={'not-replayed':'Not replayed','related-only':'Related work only','partial':'Partly replayed'};
  return '<h2>Earlier reported approaches</h2><p class="small muted">These source notes are not completed experiments or evidence used by the AI comparison. Open a report to see what an exact replay still needs.</p>'+
    hits.map(r=>`<article class="experiment-result"><h3><a href="#/wiki/reported-attempts?section=${esc(r.id)}">${esc(r.title)}</a></h3>
      <p class="small muted">${esc(labels[r.status]||r.status)} · ${esc(r.source.author)} · ${esc(r.source.reported)}</p>
      <p>${esc(r.reported_idea)}</p><details><summary>Coverage and replay requirement</summary><p>${esc(r.coverage)}</p><p><strong>To reproduce:</strong> ${esc(r.replay_needed)}</p></details></article>`).join('');
}

function renderIdeaChecker(query,version){
  const params=new URLSearchParams(location.hash.split('?')[1]||'');
  const legacyPages=(params.get('pages')||'').split(',').filter(id=>db.pages.some(p=>p.id===id)&&!AssistantSearch.pageIds(query).includes(id));
  if(query&&legacyPages.length)query+=' on '+legacyPages.map(id=>id.toUpperCase()).join(' and ');
  main.innerHTML=head('Have we tried it?','Check an idea against published tests')+`<article class="reading-width idea-checker">
    <p class="idea-index-link"><a href="#/research">Browse the research index</a></p>
    <form id="experiment-form">
      <label for="experiment-query">What would you try?</label>
      <textarea id="experiment-query" rows="3" maxlength="1500" required placeholder="For example: reverse the prime values within each row of LP2-15, keeping word boundaries">${esc(query)}</textarea>
      <div class="idea-actions"><button id="idea-submit" type="submit" disabled>Check idea</button><button id="idea-retry" type="button" hidden>Retry loading records</button><button id="idea-cancel" type="button" hidden>Stop waiting</button><span id="idea-status" class="small muted" role="status"></span></div>
      <p id="idea-privacy" class="idea-privacy small muted" ${assistantEndpoint()?'':'hidden'}>Questions are processed by Cloudflare. Don’t include private information.</p>
    </form>
    <section id="experiment-results" aria-label="Matching research records"></section>
    <section id="experiment-answer" aria-label="Experiment comparison"></section>
    <section id="idea-coverage" aria-label="Idea coverage"></section>
    <section id="reported-attempts" aria-label="Earlier reported approaches"></section>
    ${footer()}</article>`;
  const input=$('#experiment-query'),answer=$('#experiment-answer'),results=$('#experiment-results'),submit=$('#idea-submit'),status=$('#idea-status'),cancel=$('#idea-cancel'),retry=$('#idea-retry');
  let localRecords=experimentRecords||checkerRecords;
  let shownIdea='',pendingConfigRequest=0,recordsReady=Array.isArray(localRecords),loadingRecords=false;
  const current=()=>input.isConnected&&(version===undefined||version===renderId);
  refreshIdeaSupport=()=>{
    if(!current())return;
    $('#idea-privacy').hidden=!assistantEndpoint();
    if(!shownIdea||input.value.trim()!==shownIdea)return;
    $('#idea-coverage').innerHTML=ideaCoverageView(shownIdea,localRecords||[]);
    $('#reported-attempts').innerHTML=reportedAttemptView(shownIdea);
  };
  const pages=()=>AssistantSearch.pageIds(input.value.trim());
  let experimentDocuments=recordsReady?AssistantSearch.experimentDocs(localRecords):[];
  const documents=()=>experimentDocuments;
  const cacheKey=()=>JSON.stringify([input.value.trim().replace(/\s+/g,' '),pages(),
    AssistantSearch.select(experimentDocuments,input.value.trim(),pages()).slice(0,2).map(r=>r.id)]);
  const busy=value=>{submit.disabled=value||!recordsReady;cancel.hidden=!value;answer.setAttribute('aria-busy',String(value));};
  const reset=()=>{pendingConfigRequest++;stopExperimentAI();busy(false);status.textContent=recordsReady?'':loadingRecords?'Loading research records. You can write your idea now.':'Research records unavailable. Retry loading to check your idea.';answer.replaceChildren();};
  function sourceExcerpt(s){
    if(s.kind==='experiment'){
      let r;try{r=JSON.parse(s.text);}catch{return '<p>Open the record to inspect its scope.</p>';}
      return '<dl class="idea-result-scope">'+[['Targets',[...(r.scope.pages||[]).map(p=>p.toUpperCase()),...(r.scope.artifacts||[])].join(', ')],['Input',r.scope.representation],['Method',r.scope.procedure],['Bounds',r.scope.parameters],['Excluded',r.scope.exclusions],['Finding',r.finding],['Limits',r.limitations]].map(([key,value])=>`<dt>${key}</dt><dd>${esc(value||'Not specified')}</dd>`).join('')+'</dl>';
    }
    return `<div class="source-excerpt">${esc(s.text||'Open the page to inspect its evidence.')}</div>`;
  }
  function showAnswer(data){
    answer.innerHTML=`<div class="answer-heading"><h2>What overlaps</h2><button type="button" id="idea-copy">Copy answer</button></div>
      <div class="answer-prose">${AssistantMarkdown.render(data.answer,data.sources)}</div>
      <p class="small muted">AI comparison · Check the cited scope and findings.${data.cached?' Reused answer; sources unchanged.':''}</p>
      <details class="answer-sources"><summary>Sources used (${data.sources.length})</summary><ol>${data.sources.map(s=>`<li>
        <a href="${esc(s.href)}">${esc(s.title)}</a> <span class="small muted">${esc(ideaSourceType(s))}</span>
        ${s.page?` · <a href="#/reader/${esc(s.page)}">Open reader</a>`:''}
        <p class="small muted">${esc(s.excerpt||'Complete recorded scope, finding, and limitations')}</p>${sourceExcerpt(s)}</li>`).join('')}</ol></details>`;
    const copyButton=$('#idea-copy');
    copyButton.onclick=async()=>{
      const text=data.answer+'\n\nSources:\n'+data.sources.map((s,i)=>`[${i+1}] ${s.title} — https://jelliottdev.github.io/${s.href}`).join('\n');
      try{await navigator.clipboard.writeText(text);if(copyButton.isConnected)copyButton.textContent='Copied';}
      catch{if(copyButton.isConnected)copyButton.textContent='Select answer to copy';}
    };
    status.textContent='Comparison ready.';
  }
  async function compare(idea){
    const key=cacheKey(),cached=ideaAnswers.get(key);
    if(cached&&cached.until>Date.now()){showAnswer({...cached.data,cached:true});return;}
    const controller=new AbortController();experimentRequest=controller;busy(true);status.textContent='Comparing the documented scope…';
    answer.innerHTML='<p class="small muted">The matching records below are ready to read.</p>';
    const timeout=setTimeout(()=>controller.abort(),25000);
    try {
      const [response,index]=await Promise.all([
        fetch(assistantEndpoint(),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:idea,pages:pages()}),signal:controller.signal}),
        loadSupportingIndex()
      ]);
      const data=await response.json();if(experimentRequest!==controller)return;
      if(!response.ok)throw Error(response.status===429?'Please wait a minute before another comparison.':'AI comparison is unavailable right now.');
      const known=[...documents(),...index.documents],sources=data.sources||[];
      const cited=[...(data.answer||'').matchAll(/\[(\d+)\]/g)].map(m=>Number(m[1]));
      if(!data.answer||typeof data.answer!=='string'||data.answer.length>12000||!sources.length||sources.length>4||!cited.length||
        sources.some(s=>!known.some(d=>d.id===s.id&&d.href===s.href)||!AssistantMarkdown.safe(s.href))||
        cited.some(n=>n<1||n>sources.length))throw Error('A sourced comparison is unavailable for this search.');
      rememberIdea(key,data);showAnswer(data);
    } catch(error){
      if(experimentRequest===controller){answer.innerHTML='<p class="answer-notice">'+esc(error.name==='AbortError'?'The comparison took too long. Read the matching records below or try again.':error.message)+' The source records remain available.</p>';status.textContent='Comparison unavailable.';}
    } finally {clearTimeout(timeout);if(experimentRequest===controller){experimentRequest=null;busy(false);}}
  }
  function draw(searchNow,requestAI=false){
    reset();if(!recordsReady)return;const idea=input.value.trim();shownIdea=searchNow?idea:'';refreshIdeaSupport();const {tests:matches,supporting}=searchNow?AssistantSearch.classify(documents(),idea,pages()):{tests:[],supporting:[]};
    const canCompare=Boolean(searchNow&&idea&&AssistantSearch.select(documents(),idea,pages()).length);
    const selected=items=>items.slice(0,3).map(m=>localRecords.find(r=>r.id===m.document.id)).filter(Boolean)
      .map(r=>experimentSearchResult(r,[...new Set([...pages(),...AssistantSearch.pageIds(idea)])])).join('');
    if(!localRecords.length)results.innerHTML='<h2>No experiment records published yet</h2><p>No tests have been added to this index. This does not tell us whether your technique has been tried elsewhere.</p>';
    else if(!searchNow||!idea)results.innerHTML='';
    else results.innerHTML=`<h2>${matches.length?'Related tests':supporting.length?'Related evidence':'No matching record'}</h2>${!matches.length&&!supporting.length?'<p>This index doesn’t cover every past attempt. <a href="#/research">Browse the research index</a>.</p>':''}${selected(matches)}${supporting.length?`${matches.length?'<h2>Other evidence</h2>':''}${selected(supporting)}`:''}${matches.length>3||supporting.length>3?`<p class="small"><a href="#/research?q=${encodeURIComponent(idea)}">Browse more records</a></p>`:''}`;
    if((matches.length||supporting.length)&&canCompare&&assistantEndpoint()){
      const cached=ideaAnswers.get(cacheKey());
      if(cached&&cached.until>Date.now())showAnswer({...cached.data,cached:true});
      else if(requestAI)compare(idea);
      else status.textContent='Press Check idea to compare the documented scope.';
    } else if((matches.length||supporting.length)&&canCompare&&requestAI&&!assistantConfig){
      const token=++pendingConfigRequest;
      status.textContent='Preparing the comparison…';
      assistantConfigPromise.then(()=>{
        if(token!==pendingConfigRequest||!current()||input.value.trim()!==idea)return;
        if(assistantEndpoint())compare(idea);
        else status.textContent='Index checked. AI comparison is unavailable; the matching records are ready.';
      });
    } else if(searchNow&&idea)status.textContent=!canCompare&&(matches.length||supporting.length)?
      'Read the related evidence below; no AI comparison was requested.':'Index checked. No AI request was needed.';
  }
  input.addEventListener('input',()=>{shownIdea='';reset()});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();if(!submit.disabled)$('#experiment-form').requestSubmit();}});
  cancel.onclick=()=>{pendingConfigRequest++;stopExperimentAI();busy(false);answer.innerHTML='<p class="small muted">Stopped waiting. You can read the records below.</p>';status.textContent='';};
  $('#experiment-form').onsubmit=e=>{e.preventDefault();if(submit.disabled)return;const p=new URLSearchParams({q:input.value.trim()});history.replaceState(null,'','#/experiments?'+p);draw(true,true);};
  async function loadRecords(){
    if(loadingRecords||!current())return;
    loadingRecords=true;retry.disabled=true;busy(false);
    status.textContent='Loading research records. You can write your idea now.';
    results.setAttribute('aria-busy','true');
    try{
      const records=await ensureCheckerRecords();
      if(!current())return;
      localRecords=records;recordsReady=true;experimentDocuments=AssistantSearch.experimentDocs(records);
      const retryFocused=document.activeElement===retry;
      retry.hidden=true;
      draw(Boolean(input.value.trim()));
      if(retryFocused)input.focus({preventScroll:true});
    }catch{
      if(!current())return;
      retry.hidden=false;
      status.textContent='Research records unavailable. Your idea is kept; retry loading to check it.';
    }finally{
      if(current()){loadingRecords=false;retry.disabled=false;results.setAttribute('aria-busy','false');busy(false);}
    }
  }
  retry.onclick=loadRecords;
  if(recordsReady)draw(Boolean(query));
  else loadRecords();

}
