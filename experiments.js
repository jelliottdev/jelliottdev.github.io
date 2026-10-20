 'use strict';
let experimentRecords, assistantConfig, experimentRequest;
const outcomes = {'supported':'Supported within scope','not-supported':'Not supported within scope','inconclusive':'Inconclusive'};
function stopExperimentAI(){experimentRequest?.abort();experimentRequest=null;}
async function experimentsPage(id, version, query='') {
  stopExperimentAI();
  if (!experimentRecords) {
    const response = await fetch('data/experiments.json');
    if (!response.ok) throw Error('The experiment index could not be loaded. Please retry.');
    const data = await response.json();
    if (!Array.isArray(data.records)) throw Error('The experiment index has an invalid format.');
    experimentRecords = data.records;
  }
  if (!assistantConfig) {
    try {const response=await fetch('data/assistant.json');assistantConfig=response.ok?await response.json():{};}catch{assistantConfig={};}
  }
  if (version !== renderId) return;
  if (id) {
    const record = experimentRecords.find(r => r.id === id);
    if (!record) throw Error('That experiment has no published record.');
    main.innerHTML = experimentArticle(record); return;
  }
  const endpoint=typeof assistantConfig.endpoint==='string'&&assistantConfig.endpoint.startsWith('https://')?assistantConfig.endpoint:null;
  main.innerHTML = head('Have we tried it?', 'Search documented experiments') + `<article class="reading-width">
    <p>Describe an idea to find related tests, their scope, and their results.</p>
    <form id="experiment-form"><label for="experiment-query">Your idea</label>
    <textarea id="experiment-query" rows="3" maxlength="1500" placeholder="For example: reverse prime values on LP2-15">${esc(query)}</textarea>
    <button type="submit">Find related work</button>
    ${endpoint?'<p class="small muted">Your idea and matching public records are sent to Cloudflare for an AI comparison. Check its claims against the sources.</p>':''}</form>
    <div id="experiment-answer" aria-live="polite"></div><div id="experiment-results" aria-live="polite"></div>
    <details class="experiment-guide"><summary>How this lookup works</summary>
    <p>Search matches words in published experiment records, including their scope and limitations. Related results are not necessarily the same test. No match does not establish that an idea is new.</p>
    <p>Records will be added after their scripts are written, retested, and reviewed. <a href="https://github.com/jelliottdev/jelliottdev.github.io/blob/main/experiments/README.md">Record format and contribution guide</a> · <a href="data/experiments.json" download>Download the index</a></p></details>
    ${footer()}</article>`;
  const input=$('#experiment-query');
  const reset=()=>{stopExperimentAI();$('#experiment-answer').replaceChildren();};
  const compare=async idea=>{
    const controller=new AbortController();experimentRequest=controller;
    const answer=$('#experiment-answer');answer.innerHTML='<p class="small muted" role="status">Comparing the matching records…</p>';
    const timeout=setTimeout(()=>controller.abort(),25000);
    try {
      const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:idea}),signal:controller.signal});
      const data=await response.json();
      if(experimentRequest!==controller)return;
      if(!response.ok)throw Error('Comparison unavailable');
      const sources=data.sources||[],cited=[...(data.answer||'').matchAll(/\[(\d+)\]/g)].map(m=>Number(m[1]));
      if(!data.answer||!cited.length||sources.some(source=>!experimentRecords.some(r=>r.id===source.id))||cited.some(n=>n<1||n>sources.length)){
        answer.innerHTML='<p class="small muted">Read the matching records below; an AI comparison is unavailable for this search.</p>';return;
      }
      answer.innerHTML='<h2>Comparison</h2><p class="ai-text">'+esc(data.answer).replace(/\[(\d+)\]/g,(_,n)=>`<a href="#/experiments/${sources[Number(n)-1].id}">[${n}]</a>`)+ '</p><p class="small muted">AI-generated. Check the cited scope and findings.</p>';
    }catch{if(experimentRequest===controller)answer.innerHTML='<p class="small muted">AI comparison is unavailable right now. The matching records are below.</p>';}
    finally{clearTimeout(timeout);if(experimentRequest===controller)experimentRequest=null;}
  };
  const draw=searchNow=>{
    reset();const idea=input.value.trim();
    const results=searchNow?ExperimentSearch.search(experimentRecords,idea):[];
    const container=$('#experiment-results');
    if(!experimentRecords.length)container.innerHTML='<h2>No experiment records published yet</h2><p>The registry is ready for new scripts and retested results. Earlier experiments have not been imported.</p>';
    else if(!searchNow||!idea)container.innerHTML=`<h2>Published experiments</h2>${experimentRecords.map(r=>`<p><a href="#/experiments/${r.id}">${esc(r.title)}</a><br><span class="small muted">${esc(r.summary)}</span></p>`).join('')}`;
    else if(!results.length)container.innerHTML='<h2>No matching documented experiment</h2><p>Try the page ID, method name, or a distinctive number. This index does not cover all previous research.</p>';
    else container.innerHTML=`<h2>${results.length} related ${results.length===1?'record':'records'}</h2><p class="small muted">Compare the scope before treating a result as a duplicate.</p>${results.map(({record:r,matched})=>`<article class="experiment-result"><h3><a href="#/experiments/${r.id}">${esc(r.title)}</a></h3><p>${esc(r.summary)}</p><p class="small"><b>Scope:</b> ${esc(r.scope.pages.join(', ').toUpperCase())} · ${esc(r.scope.representation)}</p><p class="small"><b>Finding:</b> ${esc(r.finding)}</p><p class="small muted">Matched: ${esc(matched.join(', '))} · Retested ${esc(r.review.retested_on)}</p></article>`).join('')}`;
    if(idea)container.innerHTML+=`<p><a href="#/search/${encodeURIComponent(idea)}">Search manuscript facts for this idea</a></p>`;
    if(results.length&&endpoint)compare(idea);
  };
  input.addEventListener('input',reset);
  $('#experiment-form').onsubmit=e=>{e.preventDefault();history.replaceState(null,'',`#/experiments?q=${encodeURIComponent(input.value.trim())}`);draw(true);};
  draw(Boolean(query));
}

function experimentArticle(r){
  const fields=[['Pages',r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`).join(', ')],['Input representation',esc(r.scope.representation)],['Procedure',esc(r.scope.procedure)],['Parameter bounds',esc(r.scope.parameters)],['Excluded',esc(r.scope.exclusions)]];
  const fileList=files=>`<ul class="source-list">${files.map(f=>`<li><a href="${esc(f.path)}" download>${esc(f.path)}</a><br><code>SHA-256: ${esc(f.sha256)}</code></li>`).join('')}</ul>`;
  return head(r.title,`${esc(outcomes[r.outcome])} · Retested ${esc(r.review.retested_on)}`,'Experiments')+`<article class="reading-width"><p><a href="#/experiments">← Have we tried it?</a></p><p class="lede">${esc(r.question)}</p><p>${esc(r.summary)}</p><h2>Scope</h2><dl class="experiment-scope">${fields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl><h2>Finding</h2><p>${esc(r.finding)}</p><h3>Limitations</h3><p>${esc(r.limitations)}</p><h3>Remaining work</h3><p>${esc(r.next_steps)}</p><h2>Reproduce</h2><p>${esc(r.reproduction.environment)}</p><pre class="reading-text">${esc(r.reproduction.command)}</pre><p><a href="${esc(r.reproduction.script)}" download>Download script</a> · <a href="${esc(r.article_path)}" download>Download full article</a></p><details><summary>Input, output, and script checksums</summary><p class="hash">Script SHA-256: ${esc(r.script_sha256)}</p><h3>Inputs</h3>${fileList(r.reproduction.inputs)}<h3>Outputs</h3>${fileList(r.reproduction.outputs)}</details><h2>Full account</h2><div class="experiment-prose">${renderExperimentMarkdown(r.article)}</div><h2>Sources</h2><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul><p class="small">Reviewed by ${esc(r.review.reviewer)} · Retested ${esc(r.review.retested_on)}</p>${r.related.length?`<h2>Related experiments</h2><ul>${r.related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}${footer()}</article>`;
}

// Deliberately small Markdown subset: text, headings, lists and fenced code; no embedded HTML.
function renderExperimentMarkdown(markdown){
  let inCode=false,code=[],paragraph=[],html=[],listType='';
  const inline=text=>esc(text).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  const closeList=()=>{if(listType){html.push(`</${listType}>`);listType='';}};
  const flush=()=>{if(paragraph.length){html.push('<p>'+inline(paragraph.join(' '))+'</p>');paragraph=[];}};
  for(const line of markdown.split('\n')){
    if(line.startsWith('```')){flush();closeList();if(inCode){html.push('<pre class="reading-text">'+esc(code.join('\n'))+'</pre>');code=[];}inCode=!inCode;continue;}
    if(inCode){code.push(line);continue;}
    if(!line.trim()){flush();closeList();continue;}
    const item=line.match(/^(?:([-*])|\d+\.) (.+)$/);
    if(item){flush();const type=item[1]?'ul':'ol';if(listType!==type){closeList();html.push(`<${type}>`);listType=type;}html.push('<li>'+inline(item[2])+'</li>');continue;}
    closeList();
    const heading=line.match(/^(#{1,6}) (.+)$/);
    if(heading){flush();const level=Math.min(4,heading[1].length+1);html.push(`<h${level}>${esc(heading[2])}</h${level}>`);}else paragraph.push(line);
  }
  flush();closeList();if(code.length)html.push('<pre class="reading-text">'+esc(code.join('\n'))+'</pre>');return html.join('');
}
