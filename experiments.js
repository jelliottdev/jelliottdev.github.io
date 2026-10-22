 'use strict';
let experimentRecords, assistantConfig, experimentRequest, ideaCoverageRecords, ideaCoverageUnavailable=false, methodFamilyRecords, methodFamilyUnavailable=false, reportedAttemptRecords, reportedAttemptsUnavailable=false;
let methodRecordKinds={}, methodRecordKindById={};
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
  if (!ideaCoverageRecords || !methodFamilyRecords || !reportedAttemptRecords) {
    const load=async(path,key,whole=false)=>{const response=await fetch(path);if(!response.ok)throw Error('Index unavailable');const data=await response.json();if(!Array.isArray(data[key]))throw Error('Invalid index');return whole?data:data[key];};
    const [notes,families,reports]=await Promise.allSettled([
      load('data/idea-coverage.json','records'),load('data/method-families.json','families',true),
      load('data/reported-attempts.json','entries')
    ]);
    ideaCoverageUnavailable=notes.status!=='fulfilled';
    ideaCoverageRecords=ideaCoverageUnavailable?[]:notes.value;
    methodFamilyUnavailable=families.status!=='fulfilled';
    methodFamilyRecords=methodFamilyUnavailable?[]:families.value.families;
    methodRecordKinds=methodFamilyUnavailable?{}:families.value.record_kinds||{};
    methodRecordKindById=methodFamilyUnavailable?{}:families.value.record_kind_by_id||{};
    reportedAttemptsUnavailable=reports.status!=='fulfilled';
    reportedAttemptRecords=reportedAttemptsUnavailable?[]:reports.value;
  }
  if (!assistantConfig) {
    try {const response=await fetch('data/assistant.json');assistantConfig=response.ok?await response.json():{};}catch{assistantConfig={};}
  }
  if (version !== renderId) return;
  if (id) {
    const record = experimentRecords.find(r => r.id === id);
    if (!record) throw Error('That experiment has no published record.');
    main.innerHTML = experimentArticle(record);
    bindRouteIllustration();
    return;
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
  const title=group=>group[0].family?.title||group[0].title;
  const familyKey=record=>record.family?.id||record.id;
  const solvingFamilies=new Set(records.filter(r=>['method','replay'].includes(r.record_type?.id)).map(familyKey));
  const primary=records.filter(r=>solvingFamilies.has(familyKey(r)));
  const supporting=records.filter(r=>!solvingFamilies.has(familyKey(r)));
  const groups=items=>{const families=new Map();for(const record of items){const key=record.family?.id||record.id;if(!families.has(key))families.set(key,[]);families.get(key).push(record);}return [...families.values()];};
  const cards=items=>`<div class="experiment-browser">${groups(items).sort((a,b)=>title(a).localeCompare(title(b))).map(group=>{
      const family=group[0].family;
      const members=[...group].sort((a,b)=>Number(b.id===family?.baseline)-Number(a.id===family?.baseline)||a.title.localeCompare(b.title));
      const searchable=[title(group),family?.question||'',...members.flatMap(record=>[record.title,record.summary,record.scope?.procedure||'',...(record.scope?.pages||[]),...(record.tags||[])])].join(' ');
      return `<details class="experiment-browse-family" data-search="${esc(searchable)}"><summary><span>${esc(title(group))}</span><span class="small muted">${members.length} ${members.length===1?'record':'records'}</span></summary>
        ${family?`<p class="small muted">${esc(family.question)}</p>`:''}
        <ul>${members.map(record=>`<li><h3><a href="#/experiments/${record.id}">${esc(record.title)}</a></h3>
          <p class="small muted">${esc(record.record_type?.label||'Experiment')} · ${esc(outcomes[record.outcome]||record.outcome||'Outcome unavailable')}</p>
          ${family&&record.variant?.label?`<p class="small muted">${esc(record.variant.label)}</p>`:''}
          <p>${esc(record.finding)}</p></li>`).join('')}</ul></details>`;
    }).join('')}</div>`;
  const params=new URLSearchParams(location.hash.split('?')[1]||'');
  return `<details id="browse-experiments" class="experiment-archive" ${params.get('section')==='browse-experiments'||params.has('browse')?'open':''}><summary><span>Browse published research</span><span class="small muted">${records.length} records</span></summary><div class="experiment-archive-body"><div class="experiment-browse-filter"><label for="experiment-browse-query">Find a published record</label><input id="experiment-browse-query" type="search" placeholder="Method or page, such as LP2-15" autocomplete="off"><p id="experiment-browse-status" class="small muted" role="status"></p></div><details class="experiment-browse-section"><summary><h3>Solving tests</h3><span class="small muted">${groups(primary).length} groups</span></summary>${cards(primary)}</details><details class="experiment-browse-section"><summary><h3>Measurements, controls and source checks</h3><span class="small muted">${groups(supporting).length} groups</span></summary><p class="small muted">These records provide context; they do not test a decoding rule.</p>${cards(supporting)}</details><p class="small muted experiment-browse-caveat">Each finding applies to its stated bounds. <a href="#/wiki/first-experiment?section=outcomes">Reading the outcomes</a></p></div></details>`;
}
function experimentFamily(r){
  if(!r.family)return '';
  const f=r.family,members=experimentRecords.filter(x=>x.family?.id===f.id);
  members.sort((a,b)=>Number(b.id===f.baseline)-Number(a.id===f.baseline)||a.id.localeCompare(b.id));
  if(members.length===1)return `<section><h2>Record family</h2><p><strong>${esc(f.title)}</strong></p><p>${esc(f.question)}</p><p class="small muted">This record is the baseline. No completed variants have been published yet.</p></section>`;
  const names={pages:'Pages',artifacts:'Source artifacts',representation:'Input representation',procedure:'Procedure',parameters:'Parameter bounds',exclusions:'Exclusions'};
  const value=v=>esc(Array.isArray(v)?v.join(', '):v);
  return `<section aria-label="Experiment family comparison"><h2>${esc(f.title)}</h2><p>${esc(f.question)}</p>${members.map(x=>`<article class="family-member"><h3><a href="#/experiments/${x.id}" ${x.id===r.id?'aria-current="page"':''}>${esc(x.variant.label)}</a></h3><p>${esc(x.summary)}</p>${x.id===f.baseline?'<p class="small muted">Baseline for the comparisons below.</p>':`<p><strong>Changed:</strong> ${[...new Set(x.variant.changes.map(c=>c.reason))].map(esc).join(' ')}</p><details><summary>Compare exact scope with baseline</summary>${x.variant.changes.map(c=>`<h4>${esc(names[c.field]||c.field)}</h4><dl><dt>Baseline</dt><dd>${value(c.before)}</dd><dt>This variant</dt><dd>${value(c.after)}</dd></dl>`).join('')}</details>`}</article>`).join('')}<p class="small muted">Each record retains its own scope and findings. A match to this family does not mean every variant of an idea has been tested.</p></section>`;
}

function experimentScopeLinks(r){
  return [...r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`),...(r.scope.artifacts||[]).map(path=>`<a href="${esc(path)}">${esc(path.split('/').pop())}</a>`)].join(', ');
}
function experimentRecordType(r){
  const kind=r.record_type||methodRecordKinds[methodRecordKindById[r.id]];
  if(!kind?.label)return '';
  return `<p class="small muted"><strong>${esc(kind.label)}</strong> · <a href="#/wiki/solving-methods?section=record-types">About record types</a></p>`;
}
function experimentMethodGuides(r){
  if(methodFamilyUnavailable)return '<div id="experiment-methods"><p>The method index could not be loaded. You can still browse the <a href="#/wiki/solving-methods">method-family map</a>.</p></div>';
  const families=(methodFamilyRecords||[]).filter(f=>f.related.includes(r.id));
  if(!families.length)return '';
  return `<div id="experiment-methods"><ul>${families.map(f=>`<li><a href="#/wiki/${esc(f.guide)}">${esc(f.title)}</a> — ${esc(f.description)} <a class="small" href="#/wiki/solving-methods?section=family-${esc(f.id)}">Compare tests</a></li>`).join('')}</ul></div>`;
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
// The first four rune positions on LP2-31 source lines 1–4, checked against
// lp2-row-column-routes/results.json source_positions (line, rune_position, index).
const routeExcerpt=[[2,5,17,21],[8,13,12,1],[27,3,15,19],[20,7,15,4]];
function routeExcerptOrder(axis,alternating){
  const cells=[];
  for(let outer=0;outer<4;outer++)for(let inner=0;inner<4;inner++){
    const position=alternating&&outer%2?3-inner:inner;
    cells.push(axis==='row'?[outer,position]:[position,outer]);
  }
  return cells;
}
function routeIllustration(){
  const rows=routeExcerpt.map((values,row)=>`<tr><th scope="row">${row+1}</th>${values.map((value,col)=>`<td data-route-cell="${row}-${col}"><span class="route-demo-step"></span><strong class="route-demo-index">${value}</strong></td>`).join('')}</tr>`).join('');
  return `<div class="route-demo" aria-label="Illustration of row and column routes on a cropped LP2-31 excerpt">
    <h3>How the route changes</h3>
    <p class="route-demo-note">Illustration only: the first four rune positions on each of LP2-31’s first four source lines. The complete test uses all 269 positions, including unequal line lengths.</p>
    <div class="route-demo-controls"><div role="group" aria-label="Reading order"><button type="button" data-route-axis="row" aria-pressed="false">Rows first</button><button type="button" data-route-axis="column" aria-pressed="true">Columns first</button></div><div role="group" aria-label="Direction within each row or column"><button type="button" data-route-pattern="straight" aria-pressed="true">Same direction</button><button type="button" data-route-pattern="alternating" aria-pressed="false">Alternate direction</button></div></div>
    <div class="route-demo-table"><table><caption>LP2-31 rune indices; the numbered marker shows output order</caption><thead><tr><th scope="col">Line</th><th scope="col">Rune 1</th><th scope="col">Rune 2</th><th scope="col">Rune 3</th><th scope="col">Rune 4</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="route-demo-reading" aria-live="polite"></p>
  </div>`;
}
function bindRouteIllustration(){
  const demo=main.querySelector('.route-demo');
  if(!demo)return;
  const update=()=>{
    const axis=demo.querySelector('[data-route-axis][aria-pressed="true"]').dataset.routeAxis;
    const alternating=demo.querySelector('[data-route-pattern][aria-pressed="true"]').dataset.routePattern==='alternating';
    const order=routeExcerptOrder(axis,alternating);
    order.forEach(([row,col],i)=>{
      const cell=demo.querySelector(`[data-route-cell="${row}-${col}"]`);
      cell.querySelector('.route-demo-step').textContent=`#${i+1}`;
      cell.setAttribute('aria-label',`Source line ${row+1}, rune ${col+1}: index ${routeExcerpt[row][col]}, output step ${i+1}`);
    });
    demo.querySelector('.route-demo-reading').textContent=`First eight indices: ${order.slice(0,8).map(([row,col])=>routeExcerpt[row][col]).join(' → ')}.`;
  };
  demo.addEventListener('click',event=>{
    const button=event.target.closest('button[data-route-axis],button[data-route-pattern]');
    if(!button||!demo.contains(button))return;
    const attribute=button.hasAttribute('data-route-axis')?'data-route-axis':'data-route-pattern';
    demo.querySelectorAll(`button[${attribute}]`).forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
    update();
  });
  update();
}
function experimentVisual(r,v){
  if(r.id==='lp2-row-column-routes'&&v.path.endsWith('/source-trace.svg')){
    const rows=[[1,1,1,2],[2,2,1,8],[3,3,1,27],[4,4,1,20],[5,5,1,17],[6,6,1,19]];
    return `${routeIllustration()}<details class="experiment-extra route-trace-disclosure"><summary>See the exact full-page trace</summary><figure class="experiment-figure route-trace"><div class="route-trace-head"><strong>LP2-31 · column-first route</strong><span>Down each ordinal column, then move right</span></div><table><thead><tr><th scope="col">Output step</th><th scope="col">Source line · rune</th><th scope="col">Rune index</th></tr></thead><tbody>${rows.map(([step,line,rune,index])=>`<tr><th scope="row">${step}</th><td>${line} · ${rune}</td><td>${index}</td></tr>`).join('')}</tbody></table><p>First six of 269 source positions. The complete route uses each position once.</p><figcaption><a href="${esc(v.path)}" download>Download the archived SVG</a></figcaption></figure></details>`;
  }
  const comparisons={
    'lp2-word-order-reversal':{
      path:'source-trace.svg',title:'LP2-31 · reverse segment order',
      note:'The first six outputs agree under both boundary rules; the complete routes diverge later.',
      rows:[[0,266,266],[1,267,267],[2,268,268],[3,258,258],[4,259,259],[5,260,260]]
    },
    'lp2-word-reversal':{
      path:'boundary-trace.svg',title:'LP2-31 · reverse within segments',
      note:'These are the first six outputs where the two boundary rules differ.',
      rows:[[43,44,48],[44,43,47],[45,48,46],[46,47,45],[47,46,44],[48,45,43]]
    }
  };
  const comparison=comparisons[r.id];
  if(comparison&&v.path.endsWith('/'+comparison.path)){
    return `<figure class="experiment-figure route-trace"><div class="route-trace-head"><strong>${comparison.title}</strong><span>Original source rune positions, counted from zero</span></div><table><thead><tr><th scope="col">Output</th><th scope="col">Split lines</th><th scope="col">Join lines</th></tr></thead><tbody>${comparison.rows.map(([output,split,joined])=>`<tr><th scope="row">${output}</th><td>${split}</td><td>${joined}</td></tr>`).join('')}</tbody></table><p>${comparison.note}</p><figcaption><a href="${esc(v.path)}" download>Download the archived SVG</a></figcaption></figure>`;
  }
  return `<figure class="experiment-figure"><img src="${esc(v.path)}" alt="${esc(v.caption)}" style="width:100%;max-width:480px;height:auto" loading="lazy"><figcaption>${esc(v.caption)}</figcaption></figure>`;
}
function experimentArticle(r){
  const solving=['method','replay'].includes(r.record_type?.id);
  const pageLinks=experimentScopeLinks(r);
  const targets=r.scope.pages.length>8?`<details><summary>${r.scope.pages.length} manuscript pages — show exact list</summary><p>${pageLinks}</p></details>`:pageLinks;
  const fields=[['Targets',targets],['Tested bounds',esc(r.scope.parameters)],['Not covered',esc(r.scope.exclusions)]];
  const exactFields=[['Input representation',esc(r.scope.representation)],['Procedure',esc(r.scope.procedure)]];
  const fileList=files=>`<ul class="source-list">${files.map(f=>`<li><a href="${esc(f.path)}" download>${esc(f.path)}</a><br><code>SHA-256: ${esc(f.sha256)}</code></li>`).join('')}</ul>`;
  const needsImages=r.reproduction.inputs.some(f=>/^images\/.*\.(jpe?g|png)$/i.test(f.path));
  const familyIds=new Set(experimentRecords.filter(x=>r.family&&x.family?.id===r.family.id).map(x=>x.id));
  const related=r.related.filter(id=>!familyIds.has(id));
  const methodGuides=experimentMethodGuides(r);
  const sections=[['experiment-finding','Result'],['experiment-scope','Scope'],...(methodGuides?[['experiment-methods','Methods']]:[]),['experiment-reproduce','Reproduce'],...(r.family?[['experiment-family','Related tests']]:[]),['experiment-sources','Sources']];
  const sectionLinks=sections.map(([id,label])=>`<a href="#/experiments/${esc(r.id)}?section=${id}" data-anchor="${id}">${esc(label)}</a>`).join('');
  return head(r.title,`${esc(r.record_type?.label||'Research record')} · ${esc(outcomes[r.outcome])}`,'Research records')+`<article class="reading-width experiment-article">
    <p class="lede">${esc(r.question)}</p>
    <nav class="section-nav experiment-section-nav" aria-label="Experiment sections">${sectionLinks}</nav>
    <p class="experiment-mobile-jump"><a href="#/experiments/${esc(r.id)}?section=experiment-reproduce" data-anchor="experiment-reproduce">Jump to files and steps ↓</a></p>
    <section aria-labelledby="experiment-finding"><h2 id="experiment-finding">Result</h2><p class="experiment-finding">${esc(r.finding)}</p>
      <p class="experiment-limit"><strong>Limit:</strong> ${esc(r.limitations.replace(/\s*Human review pending\./g,''))}</p>
      ${(r.visuals||[]).map(v=>experimentVisual(r,v)).join('')}
    </section>
    <section aria-labelledby="experiment-scope"><h2 id="experiment-scope">Scope</h2>${solving?'':'<p class="small">This record does not establish that an LP2 decoding method was tried.</p>'}<dl class="experiment-scope">${fields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl><details class="experiment-extra"><summary>Exact input and procedure</summary><dl class="experiment-scope">${exactFields.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl></details><p class="small"><a href="#/wiki/search-space">How to read search bounds</a></p></section>
    ${methodGuides?`<details class="experiment-extra experiment-method-disclosure"><summary>Related method guides</summary>${methodGuides}</details>`:''}
    <section aria-labelledby="experiment-reproduce"><h2 id="experiment-reproduce">Reproduce &amp; download</h2>
      <p><a class="experiment-bundle-link" href="downloads/experiments/${esc(r.id)}.zip" download>Download this experiment (ZIP)</a> <span class="small muted">Scripts, inputs, results and a start file.</span></p>
      <p>Run from the extracted folder:</p><pre class="reading-text">${esc(r.reproduction.command)}</pre>
      <details class="experiment-extra"><summary>Setup and individual files</summary><p>${esc(r.reproduction.environment)}${needsImages?' Original image inputs are separate: extract <a href="downloads/original-images.zip" download>original-images.zip</a> into the same folder.':''} See the <a href="#/wiki/running-scripts">script setup guide</a> for help. The <a href="downloads/reference-data.zip" download>full reference-data bundle</a> is available for work across experiments.</p>${experimentDownloads(r)}<details><summary>All files &amp; SHA-256 checksums</summary><p class="hash">Script SHA-256: ${esc(r.script_sha256)}</p><h3>Inputs</h3>${fileList(r.reproduction.inputs)}<h3>Outputs</h3>${fileList(r.reproduction.outputs)}</details></details>
    </section>
    <details class="experiment-extra"><summary>Related tests and next steps</summary>
      ${r.family?`<div id="experiment-family">${experimentFamily(r)}</div>`:''}
      ${related.length?`<h3>Other related experiments</h3><ul>${related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}
      <h3 id="experiment-remaining">What remains open</h3><p>${esc(r.next_steps)}</p>
    </details>
    <details class="experiment-extra"><summary>Full account and sources</summary>
      <details class="experiment-account"><summary>Method, results and retest</summary><div class="experiment-prose">${renderExperimentMarkdown(r.article,[r.reproduction.script,r.article_path,...r.reproduction.inputs.map(f=>f.path),...r.reproduction.outputs.map(f=>f.path)])}</div></details>
      <h3 id="experiment-sources">Sources</h3><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul>
    </details>
    ${footer()}</article>`;
}

// Authored experiment Markdown: escaped text, links, headings, lists, simple tables and code; no embedded HTML.
function renderExperimentMarkdown(markdown,files=[]){
  const safeLink=href=>/^https:\/\/[^\s<>"']+$/.test(href)||
    /^#\/(?:wiki\/[a-z0-9-]+|page\/lp[12]-\d{2}|reader\/lp[12]-\d{2}|experiments\/[a-z0-9-]+)(?:\?[a-zA-Z0-9_%=&.-]+)?$/.test(href)||
    (files.includes(href)&&/^[a-zA-Z0-9_./-]+$/.test(href)&&!href.startsWith('/')&&!href.split('/').includes('..'));

  let inCode=false,code=[],paragraph=[],html=[],listType='',codeNumber=0;
  const codeBlock=lines=>{const number=++codeNumber;return `<div class="copyable-block unwrapped"><div class="block-tools"><span role="status"></span><button type="button" data-wrap-block aria-pressed="false" aria-label="Wrap lines in experiment text block ${number}">Wrap lines</button><button type="button" data-copy-block aria-label="Copy experiment text block ${number}">Copy</button></div><pre class="reading-text" tabindex="0" aria-label="Experiment text block ${number}">${esc(lines.join('\n'))}</pre></div>`;};
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
    if(line.startsWith('```')){flush();closeList();if(inCode){html.push(codeBlock(code));code=[];}inCode=!inCode;continue;}
    if(inCode){code.push(line);continue;}
    if(!line.trim()){flush();closeList();continue;}
    const figure=line.match(/^!\[([^\]]+)\]\(([^)]+)\)$/);
    if(figure&&files.includes(figure[2])&&safeLink(figure[2])&&/\.(?:svg|png|jpg|webp)$/.test(figure[2])){
      flush();closeList();html.push(`<figure class="experiment-figure"><a class="experiment-figure-image" href="${esc(figure[2])}" target="_blank" rel="noopener"><img src="${esc(figure[2])}" alt="${esc(figure[1])}" loading="lazy"></a><figcaption>${esc(figure[1])} <a href="${esc(figure[2])}" target="_blank" rel="noopener">Open full-size figure ↗</a></figcaption></figure>`);continue;
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
      if(!valid){html.push('<p class="small muted">Table shown as text because its column counts differ.</p>'+codeBlock(raw));continue;}
      html.push('<p class="table-scroll-hint">Scroll table sideways for all columns →</p><div class="table-wrap" role="region" aria-label="Scrollable experiment data table" tabindex="0"><table><thead><tr>'+headers.map(value=>'<th scope="col">'+inline(value)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>');
      continue;
    }
    const item=line.match(/^(?:([-*])|\d+\.) (.+)$/);
    if(item){flush();const type=item[1]?'ul':'ol';if(listType!==type){closeList();html.push(`<${type}>`);listType=type;}html.push('<li>'+inline(item[2])+'</li>');continue;}
    closeList();
    const heading=line.match(/^(#{1,6}) (.+)$/);
    if(heading){flush();const level=Math.min(4,heading[1].length+1);html.push(`<h${level}>${esc(heading[2])}</h${level}>`);}else paragraph.push(line);
  }
  flush();closeList();if(code.length)html.push(codeBlock(code));return html.join('');
}
