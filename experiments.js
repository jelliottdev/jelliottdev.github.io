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
  renderIdeaChecker(endpoint,query);
}

function experimentArticle(r){
  const fields=[['Pages',r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`).join(', ')],['Input representation',esc(r.scope.representation)],['Procedure',esc(r.scope.procedure)],['Parameter bounds',esc(r.scope.parameters)],['Excluded',esc(r.scope.exclusions)]];
  const fileList=files=>`<ul class="source-list">${files.map(f=>`<li><a href="${esc(f.path)}" download>${esc(f.path)}</a><br><code>SHA-256: ${esc(f.sha256)}</code></li>`).join('')}</ul>`;
  return head(r.title,`${esc(outcomes[r.outcome])} · Retested ${esc(r.review.retested_on)}`,'Experiments')+`<article class="reading-width"><p><a href="#/experiments">← Have we tried it?</a></p><p class="lede">${esc(r.question)}</p><p>${esc(r.summary)}</p><h2>Scope</h2><dl class="experiment-scope">${fields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl><h2>Finding</h2><p>${esc(r.finding)}</p><h3>Limitations</h3><p>${esc(r.limitations)}</p><h3>Remaining work</h3><p>${esc(r.next_steps)}</p><h2>Reproduce</h2><p>${esc(r.reproduction.environment)}</p><pre class="reading-text">${esc(r.reproduction.command)}</pre><p><a href="${esc(r.reproduction.script)}" download>Download script</a> · <a href="${esc(r.article_path)}" download>Download full article</a></p><details><summary>Input, output, and script checksums</summary><p class="hash">Script SHA-256: ${esc(r.script_sha256)}</p><h3>Inputs</h3>${fileList(r.reproduction.inputs)}<h3>Outputs</h3>${fileList(r.reproduction.outputs)}</details><h2>Full account</h2><div class="experiment-prose">${renderExperimentMarkdown(r.article)}</div><h2>Sources</h2><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul><p class="small">Reviewed by ${esc(r.review.reviewer)} · Retested ${esc(r.review.retested_on)}</p>${r.related.length?`<h2>Related experiments</h2><ul>${r.related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}${footer()}</article>`;
}

// Deliberately small Markdown subset: text, headings, lists and fenced code; no embedded HTML.
function renderExperimentMarkdown(markdown){
  let inCode=false,code=[],paragraph=[],html=[],listType='';
  const inline=text=>String(text).split(/(`[^`]+`)/g).map(part=>{
    if(/^`[^`]+`$/.test(part))return '<code>'+esc(part.slice(1,-1))+'</code>';
    return esc(part).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  }).join('');
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
