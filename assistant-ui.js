'use strict';
const ideaAnswers=new Map();
let supportingIndex;
function rememberIdea(key,data){if(ideaAnswers.size>=20)ideaAnswers.delete(ideaAnswers.keys().next().value);ideaAnswers.set(key,{data,until:Date.now()+3600000});}
async function loadSupportingIndex(){
  if(!supportingIndex)supportingIndex=fetch('data/assistant-index.json').then(r=>{if(!r.ok)throw Error();return r.json();}).catch(()=>{supportingIndex=null;return {documents:[]};});
  return supportingIndex;
}
function experimentSearchResult(r, requestedPages=[]){
  const missing=requestedPages.filter(id=>!r.scope.pages.includes(id));
  return `<article class="experiment-result"><h3><a href="#/experiments/${r.id}">${esc(r.title)}</a></h3>
    ${experimentRecordType(r)}
    <p>${esc(r.summary)}</p>
    <dl class="idea-result-scope"><dt>Method tested</dt><dd>${esc(r.scope.procedure)}</dd><dt>Bounds</dt><dd>${esc(r.scope.parameters)}</dd><dt>Excluded</dt><dd>${esc(r.scope.exclusions)}</dd></dl>
    ${missing.length?`<p class="scope-mismatch">Not in this record’s page scope: ${missing.map(id=>esc(id.toUpperCase())).join(', ')}.</p>`:''}
    <details class="idea-match-details"><summary>Pages, inputs and limitations</summary><dl class="idea-result-scope"><dt>Targets</dt><dd>${experimentScopeLinks(r)}</dd><dt>Input</dt><dd>${esc(r.scope.representation)}</dd><dt>Finding</dt><dd>${esc(r.finding)}</dd><dt>Limits</dt><dd>${esc(r.limitations)}</dd></dl></details>
    <p class="small muted">${esc(r.review.reviewer)} · ${esc(outcomes[r.outcome]||r.outcome)} · Retested ${esc(r.review.retested_on)}</p></article>`;
}
function ideaCoverageNote(record){
  const related=record.related.map(id=>experimentRecords.find(r=>r.id===id)).filter(Boolean);
  return `<details class="experiment-browse-family"><summary>${esc(record.title)} <span class="small muted">${esc(record.status)}</span></summary>
    <p><a href="#/wiki/${esc(record.guide)}">Read the method guide</a></p><p>${esc(record.coverage)}</p><p><strong>To make a testable version:</strong> ${esc(record.needed)}</p>
    <p><strong>Proposed extension — not run:</strong> ${esc(record.next_test)}</p>
    <p class="small muted">Related tests have narrower scopes; these links do not establish that your proposal was tested.</p>
    <ul>${related.map(r=>`<li><a href="#/experiments/${r.id}">${esc(r.title)}</a></li>`).join('')}</ul></details>`;
}
function ideaCoverageView(query=''){
  const families=query?IdeaCoverage.families(methodFamilyRecords||[],query):[];
  const familyHTML=families.length?`<h2>Related method families</h2><p class="small muted">These guides describe approaches. They are not evidence that your specific proposal has been tested.</p><ul>${families.map(f=>`<li><p><a href="#/wiki/${esc(f.guide)}">${esc(f.title)}</a></p><p>${esc(f.description)}</p><p class="small muted">${f.related.length?`${f.related.length} narrower experiment ${f.related.length===1?'record is':'records are'} linked in the family map.`:'No experiment is currently linked to this family.'} <a href="#/wiki/solving-methods?section=family-${esc(f.id)}">Inspect family coverage</a></p></li>`).join('')}</ul>`:'';
  const failures=(methodFamilyUnavailable?'<p class="small muted">The method-family index could not be loaded. This is not evidence of missing research.</p>':'')+(ideaCoverageUnavailable?'<p class="small muted">Coverage notes could not be loaded. Experiment results remain available.</p>':'');
  const records=query?IdeaCoverage.match(ideaCoverageRecords||[],query):(ideaCoverageRecords||[]);
  if(!records.length)return familyHTML+failures;
  const body=`<p class="small muted">Editorial coverage notes, not experiment findings. “Needs a defined rule” identifies missing bounds; “Partially covered” links narrower tests. Proposed extensions have not been run.</p>${records.map(ideaCoverageNote).join('')}`;
  return familyHTML+failures+(query?`<h2>Coverage of this idea</h2>${body}`:`<details class="experiment-guide"><summary>Common ideas and gaps in coverage</summary>${body}</details>`);
}

function renderIdeaChecker(endpoint,query){
  const params=new URLSearchParams(location.hash.split('?')[1]||'');
  const chosen=(params.get('pages')||'').split(',').filter(id=>db.pages.some(p=>p.id===id)).slice(0,2);
  const options=selected=>'<option value="">Any page</option>'+db.pages.map(p=>`<option value="${p.id}" ${selected===p.id?'selected':''}>${p.id.toUpperCase()}${p.title?' · '+esc(p.title):''}</option>`).join('');
  main.innerHTML=head('Have we tried it?','Check a technique against documented experiments')+`<article class="reading-width idea-checker">
    <p>Describe the technique, inputs, and bounds you want to test. Still choosing an approach? <a href="#/wiki/solving-methods">Browse solving-method families</a>. For what the archive covers and what comes next, see <a href="#/wiki/research-coverage">research coverage</a>.</p>
    <form id="experiment-form">
      <label for="experiment-query">Technique or idea</label>
      <textarea id="experiment-query" rows="3" maxlength="1500" required placeholder="For example: reverse the prime values within each row of LP2-15, keeping word boundaries">${esc(query)}</textarea>
      <details class="idea-pages" ${chosen.length?'open':''}><summary>Specify pages <span class="muted">(optional)</span></summary>
        <div class="idea-page-fields"><div><label for="idea-page-one">Page</label><select id="idea-page-one">${options(chosen[0])}</select></div>
        <div><label for="idea-page-two">Second page</label><select id="idea-page-two">${options(chosen[1])}</select></div></div>
        <p class="small muted">Page numbers start at zero in each release. Related techniques tested on other pages can still appear.</p>
      </details>
      <div class="idea-actions"><button id="idea-submit" type="submit">Check idea</button><button id="idea-cancel" type="button" hidden>Stop waiting</button><span id="idea-status" class="small muted" role="status"></span></div>
      ${endpoint?'<p class="idea-privacy small muted">Questions are processed by Cloudflare. Don’t include private information.</p>':''}
    </form>
    <section id="experiment-answer" aria-label="Experiment comparison"></section>
    <section id="idea-coverage" aria-label="Idea coverage"></section>
    <section id="experiment-results" aria-label="Matching experiments"></section>
    <details class="experiment-guide"><summary>Coverage and how to interpret a match</summary>
      <p>This checks published experiment records by technique. A page number alone is not a match. Related work can use different inputs or bounds; inspect the scope before treating it as the same test.</p>
      <p>The AI compares retrieved records; it does not run your idea or prove that all previous research has been searched. Manuscript excerpts can clarify context but never establish that an experiment happened. No match means no matching record in this index, not that an idea is new or promising. Coverage notes separately identify broader proposals and missing bounds; they are not sent to the AI as experiment evidence. <a href="#/wiki/scoped-constraints">Check which narrow models are actually ruled out</a>.</p>
      <p>Answers may be cached for up to a day and reused for the same question and evidence. Reopening a result does not automatically request a new answer. Sources remain available when AI is busy.</p>
      <p><a href="https://github.com/jelliottdev/jelliottdev.github.io/blob/main/experiments/README.md">Record format and contribution guide</a> · <a href="data/experiments.json" download>Download experiment index</a></p>
    </details>${footer()}</article>`;
  const input=$('#experiment-query'),answer=$('#experiment-answer'),results=$('#experiment-results'),submit=$('#idea-submit'),status=$('#idea-status'),cancel=$('#idea-cancel');
  const pages=()=>[...new Set([$('#idea-page-one').value,$('#idea-page-two').value].filter(Boolean))].sort();
  const experimentDocuments=AssistantSearch.experimentDocs(experimentRecords);
  const documents=()=>experimentDocuments;
  const cacheKey=()=>JSON.stringify([input.value.trim().replace(/\s+/g,' '),pages(),
    AssistantSearch.experiments(experimentDocuments,input.value.trim(),pages()).slice(0,2).map(r=>r.document)]);
  const busy=value=>{submit.disabled=value;cancel.hidden=!value;answer.setAttribute('aria-busy',String(value));};
  const reset=()=>{stopExperimentAI();busy(false);status.textContent='';answer.replaceChildren();};
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
        <a href="${esc(s.href)}">${esc(s.title)}</a> <span class="small muted">${s.kind==='experiment'?'Experiment record':'Supporting manuscript context'}</span>
        ${s.page?` · <a href="#/reader/${esc(s.page)}">Open reader</a>`:''}
        <p class="small muted">${esc(s.excerpt||'Complete recorded scope, finding, and limitations')}</p>${sourceExcerpt(s)}</li>`).join('')}</ol></details>`;
    $('#idea-copy').onclick=async()=>{
      const text=data.answer+'\n\nSources:\n'+data.sources.map((s,i)=>`[${i+1}] ${s.title} — https://jelliottdev.github.io/${s.href}`).join('\n');
      try{await navigator.clipboard.writeText(text);$('#idea-copy').textContent='Copied';}
      catch{$('#idea-copy').textContent='Select answer to copy';}
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
        fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:idea,pages:pages()}),signal:controller.signal}),
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
    reset();const idea=input.value.trim();$('#idea-coverage').innerHTML=ideaCoverageView(searchNow?idea:'');const matches=searchNow?AssistantSearch.experiments(documents(),idea,pages()):[];
    if(!experimentRecords.length)results.innerHTML='<h2>No experiment records published yet</h2><p>The registry is ready for new scripts and retested results. Earlier experiments have not been imported. This does not tell us whether your technique has been tried elsewhere.</p>';
    else if(!searchNow||!idea)results.innerHTML=experimentBrowse(experimentRecords);
    else if(!matches.length)results.innerHTML='<h2>No matching documented technique</h2><p>Try the operation, cipher, key, or transformation rather than only a page number. This index does not cover all previous research.</p>';
    else results.innerHTML=`<h2>${matches.length} related ${matches.length===1?'record':'records'}</h2><p class="small muted">Compare the method and exclusions before treating a record as the same test.</p>${experimentGroups(matches.slice(0,12).map(m=>experimentRecords.find(r=>r.id===m.document.id)),r=>experimentSearchResult(r,[...new Set([...pages(),...AssistantSearch.pageIds(idea)])]))}`;
    if(matches.length&&endpoint){
      const cached=ideaAnswers.get(cacheKey());
      if(cached&&cached.until>Date.now())showAnswer({...cached.data,cached:true});
      else if(requestAI)compare(idea);
      else status.textContent='Press Check idea to compare the documented scope.';
    } else if(searchNow&&idea)status.textContent='Index checked. No AI request was needed.';
  }
  input.addEventListener('input',reset);
  for(const id of ['#idea-page-one','#idea-page-two'])$(id).addEventListener('change',reset);
  input.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();if(!submit.disabled)$('#experiment-form').requestSubmit();}});
  cancel.onclick=()=>{stopExperimentAI();busy(false);answer.innerHTML='<p class="small muted">Stopped waiting. You can read the records below.</p>';status.textContent='';};
  $('#experiment-form').onsubmit=e=>{e.preventDefault();if(submit.disabled)return;const p=new URLSearchParams({q:input.value.trim()});if(pages().length)p.set('pages',pages().join(','));history.replaceState(null,'','#/experiments?'+p);draw(true,true);};
  draw(Boolean(query));
}
