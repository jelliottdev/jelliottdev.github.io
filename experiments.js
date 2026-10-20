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
function experimentBrowse(records){
  const families=new Map();
  for(const record of records){
    const key=record.family?.id||record.id;
    if(!families.has(key))families.set(key,[]);
    families.get(key).push(record);
  }
  const title=group=>group[0].family?.title||group[0].title;
  return `<h2>Browse published experiments</h2><p class="small muted">Open a family to choose a specific test. Each record has its own scope, findings, files and reproduction instructions.</p>
    <div class="experiment-browser">${[...families.values()].sort((a,b)=>title(a).localeCompare(title(b))).map(group=>{
      const family=group[0].family;
      const members=[...group].sort((a,b)=>Number(b.id===family?.baseline)-Number(a.id===family?.baseline)||a.title.localeCompare(b.title));
      return `<details class="experiment-browse-family"><summary><span>${esc(title(group))}</span><span class="small muted">${members.length} ${members.length===1?'record':'records'}</span></summary>
        ${family?`<p class="small muted">${esc(family.question)}</p>`:''}
        <ul>${members.map(record=>`<li><h3><a href="#/experiments/${record.id}">${esc(record.title)}</a></h3>
          ${family?`<p class="small muted">${esc(record.variant?.label||'')}</p>`:''}
          <p>${esc(record.summary)}</p></li>`).join('')}</ul></details>`;
    }).join('')}</div>`;
}
function experimentFamily(r){
  if(!r.family)return '';
  const f=r.family,members=experimentRecords.filter(x=>x.family?.id===f.id);
  members.sort((a,b)=>Number(b.id===f.baseline)-Number(a.id===f.baseline)||a.id.localeCompare(b.id));
  if(members.length===1)return `<section><h2>Experiment family</h2><p><strong>${esc(f.title)}</strong></p><p>${esc(f.question)}</p><p class="small muted">This record is the baseline. No completed variants have been published yet.</p></section>`;
  const names={pages:'Pages',artifacts:'Source artifacts',representation:'Input representation',procedure:'Procedure',parameters:'Parameter bounds',exclusions:'Exclusions'};
  const value=v=>esc(Array.isArray(v)?v.join(', '):v);
  return `<section aria-label="Experiment family comparison"><h2>${esc(f.title)}</h2><p>${esc(f.question)}</p>${members.map(x=>`<article class="family-member"><h3><a href="#/experiments/${x.id}" ${x.id===r.id?'aria-current="page"':''}>${esc(x.variant.label)}</a></h3><p>${esc(x.summary)}</p>${x.id===f.baseline?'<p class="small muted">Baseline for the comparisons below.</p>':`<p><strong>Changed:</strong> ${x.variant.changes.map(c=>esc(c.reason)).join(' ')}</p><details><summary>Compare exact scope with baseline</summary>${x.variant.changes.map(c=>`<h4>${esc(names[c.field]||c.field)}</h4><dl><dt>Baseline</dt><dd>${value(c.before)}</dd><dt>This variant</dt><dd>${value(c.after)}</dd></dl>`).join('')}</details>`}</article>`).join('')}<p class="small muted">Each record retains its own scope and findings. A match to this family does not mean every variant of an idea has been tested.</p></section>`;
}

function experimentScopeLinks(r){
  return [...r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`),...(r.scope.artifacts||[]).map(path=>`<a href="${esc(path)}">${esc(path.split('/').pop())}</a>`)].join(', ');
}
function experimentDownloads(r){
  const root=`experiments/records/${r.id}/`;
  const links=[{path:r.reproduction.script,label:'Run script'},
    ...r.reproduction.inputs.filter(f=>f.path===root+'check.py').map(f=>({...f,label:'Check results'})),
    ...r.reproduction.inputs.filter(f=>f.path===root+'plan.json').map(f=>({...f,label:'Test plan'})),
    ...r.reproduction.outputs.filter(f=>/\.(json|csv|tsv|txt)$/.test(f.path)).map(f=>({...f,label:'Recorded result'})),
    {path:r.article_path,label:'Full account'}];
  return `<ul class="experiment-downloads">${links.map(f=>`<li><a href="${esc(f.path)}" download><strong>${esc(f.label)}</strong><span>${esc(f.path.split('/').pop())}</span></a></li>`).join('')}</ul>`;
}
function experimentArticle(r){
  const pageLinks=experimentScopeLinks(r);
  const fields=[['Targets',r.scope.pages.length>8?`<details><summary>${r.scope.pages.length} manuscript pages — show exact list</summary><p>${pageLinks}</p></details>`:pageLinks],['Input representation',esc(r.scope.representation)],['Procedure',esc(r.scope.procedure)],['Parameter bounds',esc(r.scope.parameters)],['Excluded',esc(r.scope.exclusions)]];
  const fileList=files=>`<ul class="source-list">${files.map(f=>`<li><a href="${esc(f.path)}" download>${esc(f.path)}</a><br><code>SHA-256: ${esc(f.sha256)}</code></li>`).join('')}</ul>`;
  const needsImages=r.reproduction.inputs.some(f=>/\.(jpe?g|png)$/i.test(f.path));
  const familyIds=new Set(experimentRecords.filter(x=>r.family&&x.family?.id===r.family.id).map(x=>x.id));
  const related=r.related.filter(id=>!familyIds.has(id));
  return head(r.title,`${esc(outcomes[r.outcome])} · Retested ${esc(r.review.retested_on)}`,'Experiments')+`<article class="reading-width experiment-article">
    <p><a href="#/experiments">← Have we tried it?</a></p>
    <p class="lede">${esc(r.question)}</p>
    <section aria-labelledby="experiment-finding"><h2 id="experiment-finding">Finding</h2><p>${esc(r.finding)}</p>
      <h3>What this does and does not establish</h3><p>${esc(r.limitations)}</p>
      <p class="small muted">${esc(r.review.reviewer)}</p>
      ${(r.visuals||[]).map(v=>`<figure class="experiment-figure"><img src="${esc(v.path)}" alt="${esc(v.caption)}" style="width:100%;max-width:480px;height:auto" loading="lazy"><figcaption>${esc(v.caption)}</figcaption></figure>`).join('')}
    </section>
    <section aria-labelledby="experiment-scope"><h2 id="experiment-scope">Scope</h2><dl class="experiment-scope">${fields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl></section>
    <section aria-labelledby="experiment-reproduce"><h2 id="experiment-reproduce">Reproduce &amp; download</h2>
      <p>Starting from scratch? Download <a href="downloads/reference-data.zip" download>reference-data.zip</a> and extract it with its folders intact.${needsImages?' Also extract <a href="downloads/original-images.zip" download>original-images.zip</a> into the same folder for the original image inputs.':''} Follow the <a href="#/wiki/running-scripts">script setup guide</a>, then run this command from the extracted repository root.</p>
      <p>${esc(r.reproduction.environment)}</p><pre class="reading-text">${esc(r.reproduction.command)}</pre>
      <h3>Individual files</h3><p class="small muted">Use these to inspect the method or results. The run script also needs the inputs listed below.</p>
      ${experimentDownloads(r)}
      <details><summary>All files &amp; SHA-256 checksums</summary><p class="hash">Script SHA-256: ${esc(r.script_sha256)}</p><h3>Inputs</h3>${fileList(r.reproduction.inputs)}<h3>Outputs</h3>${fileList(r.reproduction.outputs)}</details>
    </section>
    ${experimentFamily(r)}
    <h2>Remaining work</h2><p>${esc(r.next_steps)}</p>
    <details class="experiment-account"><summary>Full account: method, results, and retest</summary><div class="experiment-prose">${renderExperimentMarkdown(r.article,[r.reproduction.script,r.article_path,...r.reproduction.inputs.map(f=>f.path),...r.reproduction.outputs.map(f=>f.path)])}</div></details>
    <h2>Sources</h2><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul>
    ${related.length?`<h2>Related experiments</h2><ul>${related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}${footer()}</article>`;
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
