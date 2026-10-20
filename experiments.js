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

// Group related records without merging their findings or scopes.
function experimentGroups(records, render){
  const groups=new Map();
  for(const r of records){const key=r.family?.id||r.id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);}
  return [...groups.values()].map(group=>{
    const f=group[0].family;
    return `<section class="experiment-family">${f?`<h3>${esc(f.title)}</h3><p>${esc(f.question)}</p>`:''}${group.map(render).join('')}</section>`;
  }).join('');
}
function experimentFamily(r){
  if(!r.family)return '';
  const f=r.family,members=experimentRecords.filter(x=>x.family?.id===f.id);
  members.sort((a,b)=>Number(b.id===f.baseline)-Number(a.id===f.baseline)||a.id.localeCompare(b.id));
  if(members.length===1)return `<section><h2>Experiment family</h2><p><strong>${esc(f.title)}</strong></p><p>${esc(f.question)}</p><p class="small muted">This record is the baseline. No completed variants have been published yet.</p></section>`;
  return `<section><h2>Experiment family: ${esc(f.title)}</h2><p>${esc(f.question)}</p><p>The baseline defines the comparison. Each variant keeps its own scope, evidence, and conclusion; a family match does not mean the same test was run.</p><div class="table-wrap" role="region" aria-label="Experiment family comparison" tabindex="0"><table><thead><tr><th>Test</th><th>Changes from baseline</th><th>Finding</th></tr></thead><tbody>${members.map(x=>`<tr><th scope="row"><a href="#/experiments/${x.id}" ${x.id===r.id?'aria-current="page"':''}>${esc(x.variant.label)}</a></th><td>${x.id===f.baseline?'Baseline':x.variant.changes.map(c=>`<strong>${esc(c.field)}</strong>: ${esc(Array.isArray(c.before)?c.before.join(', '):c.before)} → ${esc(Array.isArray(c.after)?c.after.join(', '):c.after)}<br>${esc(c.reason)}`).join('<br>')}</td><td>${esc(x.finding)}</td></tr>`).join('')}</tbody></table></div>${members.length===1?'<p class="small muted">Only the baseline has been published. No variants have been tested in this family yet.</p>':''}</section>`;
}

function experimentArticle(r){
  const pageLinks=r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`).join(', ');
  const fields=[['Pages',r.scope.pages.length>8?`<details><summary>${r.scope.pages.length} manuscript pages — show exact list</summary><p>${pageLinks}</p></details>`:pageLinks],['Input representation',esc(r.scope.representation)],['Procedure',esc(r.scope.procedure)],['Parameter bounds',esc(r.scope.parameters)],['Excluded',esc(r.scope.exclusions)]];
  const fileList=files=>`<ul class="source-list">${files.map(f=>`<li><a href="${esc(f.path)}" download>${esc(f.path)}</a><br><code>SHA-256: ${esc(f.sha256)}</code></li>`).join('')}</ul>`;
  return head(r.title,`${esc(outcomes[r.outcome])} · Retested ${esc(r.review.retested_on)}`,'Experiments')+`<article class="reading-width"><p><a href="#/experiments">← Have we tried it?</a></p><p class="lede">${esc(r.question)}</p><p>${esc(r.summary)}</p><p class="small muted">${esc(r.review.reviewer)}</p>${experimentFamily(r)}<h2>Scope</h2><dl class="experiment-scope">${fields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl><h2>Finding</h2><p>${esc(r.finding)}</p>${(r.visuals||[]).map(v=>`<figure class="experiment-figure"><img src="${esc(v.path)}" alt="${esc(v.caption)}" style="width:100%;max-width:480px;height:auto" loading="lazy"><figcaption>${esc(v.caption)}</figcaption></figure>`).join('')}<h3>Limitations</h3><p>${esc(r.limitations)}</p><h3>Remaining work</h3><p>${esc(r.next_steps)}</p><h2>Reproduce</h2><p>${esc(r.reproduction.environment)}</p><pre class="reading-text">${esc(r.reproduction.command)}</pre><p><a href="${esc(r.reproduction.script)}" download>Download script</a> · <a href="${esc(r.article_path)}" download>Download full article</a></p><details><summary>Input, output, and script checksums</summary><p class="hash">Script SHA-256: ${esc(r.script_sha256)}</p><h3>Inputs</h3>${fileList(r.reproduction.inputs)}<h3>Outputs</h3>${fileList(r.reproduction.outputs)}</details><details class="experiment-account"><summary>Full account: method, results, and retest</summary><div class="experiment-prose">${renderExperimentMarkdown(r.article,[r.reproduction.script,r.article_path,...r.reproduction.inputs.map(f=>f.path),...r.reproduction.outputs.map(f=>f.path)])}</div></details><h2>Sources</h2><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul><p class="small">Reviewed by ${esc(r.review.reviewer)} · Retested ${esc(r.review.retested_on)}</p>${r.related.length?`<h2>Related experiments</h2><ul>${r.related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}${footer()}</article>`;
}

// Authored experiment Markdown: escaped text, links, headings, lists, simple tables and code; no embedded HTML.
function renderExperimentMarkdown(markdown,files=[]){
  const safeLink=href=>/^https:\/\/[^\s<>"']+$/.test(href)||
    /^#\/(?:wiki\/[a-z0-9-]+|page\/lp[12]-\d{2}|reader\/lp[12]-\d{2}|experiments\/[a-z0-9-]+)(?:\?[a-zA-Z0-9_%=&.-]+)?$/.test(href)||
    (files.includes(href)&&/^[a-zA-Z0-9_./-]+$/.test(href)&&!href.startsWith('/')&&!href.split('/').includes('..'));

  let inCode=false,code=[],paragraph=[],html=[],listType='';
  const inline=text=>String(text).split(/(`[^`]+`|\[[^\]\n]+\]\([^)]+\))/g).map(part=>{
    if(/^`[^`]+`$/.test(part))return '<code>'+esc(part.slice(1,-1))+'</code>';
    const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if(link)return safeLink(link[2])?`<a href="${esc(link[2])}">${esc(link[1])}</a>`:esc(part);
    return esc(part).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  }).join('');
  const closeList=()=>{if(listType){html.push(`</${listType}>`);listType='';}};
  const flush=()=>{if(paragraph.length){html.push('<p>'+inline(paragraph.join(' '))+'</p>');paragraph=[];}};
  const lines=markdown.split('\n');
  const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(cell=>cell.trim());
  for(let i=0;i<lines.length;i++){
    const line=lines[i];
    if(line.startsWith('```')){flush();closeList();if(inCode){html.push('<pre class="reading-text">'+esc(code.join('\n'))+'</pre>');code=[];}inCode=!inCode;continue;}
    if(inCode){code.push(line);continue;}
    if(!line.trim()){flush();closeList();continue;}
    const figure=line.match(/^!\[([^\]]+)\]\(([^)]+)\)$/);
    if(figure&&files.includes(figure[2])&&safeLink(figure[2])&&/\.(?:svg|png|jpg|webp)$/.test(figure[2])){
      flush();closeList();html.push(`<figure class="experiment-figure"><img src="${esc(figure[2])}" alt="${esc(figure[1])}" style="width:100%;height:auto" loading="lazy"><figcaption>${esc(figure[1])}</figcaption></figure>`);continue;
    }
    if(line.includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i+1])){
      flush();closeList();const headers=cells(line),raw=[line,lines[i+1]];
      let valid=cells(lines[i+1]).length===headers.length;i++;
      const rows=[];
      while(i+1<lines.length&&lines[i+1].trim()&&lines[i+1].includes('|')){
        const values=cells(lines[++i]);raw.push(lines[i]);
        valid=valid&&values.length===headers.length;
        rows.push('<tr>'+headers.map((_,column)=>'<td>'+inline(values[column]||'')+'</td>').join('')+'</tr>');
      }
      if(!valid){html.push('<p class="small muted">Table shown as text because its column counts differ.</p><pre class="reading-text" tabindex="0">'+esc(raw.join('\n'))+'</pre>');continue;}
      html.push('<div class="table-wrap" role="region" aria-label="Experiment data table" tabindex="0"><table><thead><tr>'+headers.map(value=>'<th scope="col">'+inline(value)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>');
      continue;
    }
    const item=line.match(/^(?:([-*])|\d+\.) (.+)$/);
    if(item){flush();const type=item[1]?'ul':'ol';if(listType!==type){closeList();html.push(`<${type}>`);listType=type;}html.push('<li>'+inline(item[2])+'</li>');continue;}
    closeList();
    const heading=line.match(/^(#{1,6}) (.+)$/);
    if(heading){flush();const level=Math.min(4,heading[1].length+1);html.push(`<h${level}>${esc(heading[2])}</h${level}>`);}else paragraph.push(line);
  }
  flush();closeList();if(code.length)html.push('<pre class="reading-text">'+esc(code.join('\n'))+'</pre>');return html.join('');
}
