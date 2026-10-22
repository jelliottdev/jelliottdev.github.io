 'use strict';
let experimentRecords, experimentRecordsPromise, assistantConfig, assistantConfigPromise, experimentRequest, ideaCoverageRecords=[], ideaCoverageUnavailable=false, methodFamilyRecords=[], methodFamilyUnavailable=false, reportedAttemptRecords=[], reportedAttemptsUnavailable=false;
let experimentSupportStarted=false;
let ideaCoveragePending=true,methodFamilyPending=true,reportedAttemptsPending=true;
let methodRecordKinds={}, methodRecordKindById={};
const outcomes = {'supported':'Supported within scope','not-supported':'Not supported within scope','inconclusive':'Inconclusive'};
function stopExperimentAI(){experimentRequest?.abort();experimentRequest=null;}
const assistantEndpoint=()=>typeof assistantConfig?.endpoint==='string'&&assistantConfig.endpoint.startsWith('https://')?assistantConfig.endpoint:null;
function refreshExperimentSupportUI(){
 const slot=document.getElementById('experiment-method-guides');
 const id=location.hash.match(/^#\/experiments\/([^?]+)/)?.[1];
 if(slot&&id){
  const record=experimentRecords?.find(item=>item.id===id);
  if(record){const guides=experimentMethodGuides(record);slot.innerHTML=guides?`<details class="experiment-extra experiment-method-disclosure"><summary>Related method guides</summary>${guides}</details>`:'';}
 }
 if(typeof refreshIdeaSupport==='function')refreshIdeaSupport();
}
function startExperimentSupport(){
 if(experimentSupportStarted)return;
 experimentSupportStarted=true;
 const read=async path=>{
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),5000);
  try{const response=await fetch(path,{signal:controller.signal});if(!response.ok)throw Error('Index unavailable');return await response.json()}
  finally{clearTimeout(timer)}
 };
 const load=async(path,key,whole=false)=>{const data=await read(path);if(!Array.isArray(data[key]))throw Error('Invalid index');return whole?data:data[key];};
 load('data/idea-coverage.json','records').then(records=>{ideaCoverageRecords=records}).catch(()=>{ideaCoverageUnavailable=true}).finally(()=>{ideaCoveragePending=false;refreshExperimentSupportUI()});
 load('data/method-families.json','families',true).then(data=>{methodFamilyRecords=data.families;methodRecordKinds=data.record_kinds||{};methodRecordKindById=data.record_kind_by_id||{}}).catch(()=>{methodFamilyUnavailable=true}).finally(()=>{methodFamilyPending=false;refreshExperimentSupportUI()});
 load('data/reported-attempts.json','entries').then(records=>{reportedAttemptRecords=records}).catch(()=>{reportedAttemptsUnavailable=true}).finally(()=>{reportedAttemptsPending=false;refreshExperimentSupportUI()});
 assistantConfigPromise=read('data/assistant.json').catch(()=>({})).then(config=>{assistantConfig=config;refreshExperimentSupportUI()});
}
async function experimentsPage(id, version, query='') {
  stopExperimentAI();
  if (!experimentRecords) {
    experimentRecordsPromise??=fetch('data/experiments.json').then(async response=>{
      if (!response.ok) throw Error('The experiment index could not be loaded. Please retry.');
      const data=await response.json();
      if (!Array.isArray(data.records)) throw Error('The experiment index has an invalid format.');
      return data.records;
    }).catch(error=>{experimentRecordsPromise=null;throw error});
    experimentRecords=await experimentRecordsPromise;
  }
  if (version !== renderId) return;
  if (id) {
    const record = experimentRecords.find(r => r.id === id);
    if (!record) throw Error('That experiment has no published record.');
    main.innerHTML = experimentArticle(record);
    bindRouteIllustration();
    bindLanguageBlockFigure();
    bindAffineLagFigure();
    bindBlockBoundaryFigure();
    startExperimentSupport();
    return;
  }
  renderIdeaChecker(query);
  startExperimentSupport();
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
  if(members.length===1)return '<p>No other completed variant in this family yet.</p>';
  return `<section aria-label="Experiment family comparison"><h2>${esc(f.title)}</h2><p>${esc(f.question)}</p><ul class="experiment-related-list">${members.map(x=>`<li><a href="#/experiments/${x.id}" ${x.id===r.id?'aria-current="page"':''}>${esc(x.variant.label)}</a><p>${esc(x.finding)}</p></li>`).join('')}</ul></section>`;
}

function experimentScopeLinks(r){
  return [...r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`),...(r.scope.artifacts||[]).map(path=>`<a href="${esc(path)}">${esc(path.split('/').pop())}</a>`)].join(', ');
}
function experimentDetailedTargets(r){
  if(r.scope.pages.length<=8)return experimentScopeLinks(r);
  const first=r.scope.pages[0],last=r.scope.pages[r.scope.pages.length-1];
  return `<a href="#/page/${first}">${esc(first.toUpperCase())}</a>–<a href="#/page/${last}">${esc(last.slice(4))}</a> · ${r.scope.pages.length} pages. <a href="reference/experiments/${esc(r.id)}.json">Exact page list and record</a>.`;
}
function experimentTargetSummary(r){
  const pages=r.scope.pages||[];
  if(!pages.length)return (r.scope.artifacts||[]).length?`${r.scope.artifacts.length} source ${(r.scope.artifacts||[]).length===1?'file':'files'}`:'No manuscript page';
  if(pages.length===1)return pages[0].toUpperCase();
  const first=pages[0],last=pages[pages.length-1],release=first.slice(0,3);
  const consecutive=pages.every((page,index)=>page.slice(0,3)===release&&Number(page.slice(4))===Number(first.slice(4))+index);
  return consecutive?`${first.toUpperCase()}–${last.slice(4)} · ${pages.length} pages`:`${pages.length} manuscript pages`;
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
    <p class="route-demo-note">Four lines from LP2-31 show how the reading order changes. The test used all 269 runes on that page, including shorter lines.</p>
    <div class="route-demo-controls"><div role="group" aria-label="Reading order"><button type="button" data-route-axis="row" aria-pressed="false">Rows first</button><button type="button" data-route-axis="column" aria-pressed="true">Columns first</button></div><div role="group" aria-label="Direction within each row or column"><button type="button" data-route-pattern="straight" aria-pressed="true">Same direction</button><button type="button" data-route-pattern="alternating" aria-pressed="false">Alternate direction</button></div></div>
    <div class="route-demo-table"><table aria-label="LP2-31 rune indices; number signs mark the selected output order"><thead><tr><th scope="col">Line</th><th scope="col">Rune 1</th><th scope="col">Rune 2</th><th scope="col">Rune 3</th><th scope="col">Rune 4</th></tr></thead><tbody>${rows}</tbody></table></div>
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
    demo.querySelector('.route-demo-reading').textContent=`First eight rune indices: ${order.slice(0,8).map(([row,col])=>routeExcerpt[row][col]).join(' → ')}.`;
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
// Exact observed_R fractions and fixed_width_tails from lp1-width-selection/results.json.
// Each fixed-width estimate includes its tie count and the plus-one correction over 49,999 shuffles.
const widthSelectionComparison=[
  [2,"4167/245948",6006],
  [4,"18057/122974",3429],
  [8,"148623/430409",3317],
  [16,"77321/307435",54],
  [32,"17834297/57182910",5],
  [64,"79242913/108463068",2044]
];
// Median, minimum and maximum TV distance across the eight aligned blocks in
// parallel-language-blocks/results.json. All eight languages use the same styling.
const languageBlockSummary={
  letters:[['English',.09233,.07102,.10345],['Finnish',.40709,.37258,.43160],['French',.18360,.17310,.20795],['German',.17495,.16957,.19606],['Italian',.23612,.22739,.24674],['Portuguese',.21583,.20072,.22998],['Spanish',.22712,.20906,.24017],['Welsh',.17915,.14159,.19403]],
  folded:[['English',.09233,.07126,.10345],['Finnish',.40709,.37292,.43160],['French',.18360,.17310,.20795],['German',.17495,.16957,.19606],['Italian',.23612,.22739,.24674],['Portuguese',.21583,.20072,.22998],['Spanish',.22712,.20906,.24017],['Welsh',.17915,.14159,.19403]],
  'gp-length':[['English',.12385,.09719,.14182],['Finnish',.39778,.36207,.41617],['French',.17898,.16829,.20280],['German',.17025,.16597,.19015],['Italian',.23215,.22472,.24111],['Portuguese',.20845,.19049,.21772],['Spanish',.21520,.19720,.22909],['Welsh',.17739,.15599,.18665]]
};
function languageBlockRows(mode){
  return languageBlockSummary[mode].map(([language,median,minimum,maximum])=>`<tr><th scope="row">${esc(language)}</th><td><span class="language-block-value">${median.toFixed(5)}</span><span class="language-block-track" aria-hidden="true"><span style="width:${(median/.45*100).toFixed(1)}%"></span></span></td><td>${minimum.toFixed(5)}–${maximum.toFixed(5)}</td></tr>`).join('');
}
function languageBlockFigure(){
  return `<figure class="experiment-figure language-block-figure"><figcaption><strong>Eight languages across eight aligned blocks.</strong> Each row shows the median word-length distance to the pooled LP2 text and the range across blocks. Lower means a closer distribution under this measure; it does not identify the plaintext language.</figcaption><div class="language-block-modes" role="group" aria-label="Word-length representation"><button type="button" data-language-mode="letters" aria-pressed="true">Letters</button><button type="button" data-language-mode="folded" aria-pressed="false">Accent-folded</button><button type="button" data-language-mode="gp-length" aria-pressed="false">GP grouping</button></div><div class="table-wrap"><table><thead><tr><th scope="col">Language</th><th scope="col">Median</th><th scope="col">Block range</th></tr></thead><tbody class="language-block-rows">${languageBlockRows('letters')}</tbody></table></div><p>All 1,012 evaluation sentences are used once per language. Blocks may share source articles, so they are not independent trials. <a href="experiments/records/parallel-language-blocks/results.json" download>Download all block scores</a>.</p></figure>`;
}
function bindLanguageBlockFigure(){
  const figure=main.querySelector('.language-block-figure');
  if(!figure)return;
  figure.addEventListener('click',event=>{
    const button=event.target.closest('button[data-language-mode]');
    if(!button||!figure.contains(button))return;
    figure.querySelectorAll('button[data-language-mode]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
    figure.querySelector('.language-block-rows').innerHTML=languageBlockRows(button.dataset.languageMode);
  });
}
function experimentVisual(r,v){
  if(r.id==='block-boundary-doublets'&&v.path.endsWith('/boundaries.svg')){
    const sizes=Array.from({length:28},(_,index)=>`<option value="${index+2}">${index+2}</option>`).join('');
    return `<figure class="experiment-figure affine-lag-figure block-boundary-figure" data-results="experiments/records/block-boundary-doublets/results.json"><figcaption><strong>Inspect the 434 placements</strong><br>Choose a block size and a shared phase. Phase zero places a boundary after every full block, counting from the start of each page.</figcaption><div class="affine-lag-controls"><label>Block size<select data-block-size>${sizes}</select></label><label>Phase<select data-block-phase></select></label></div><div class="affine-lag-readout" role="status">Loading the verified counts…</div><p class="small muted">The size and phase search was compared with the same search on 3,000 fixed-count controls. A single appealing row is not a selected-search result.</p><a href="${esc(v.path)}" download>Download summary figure</a></figure>`;
  }
  if(r.id==='word-internal-affine-lags'&&v.path.endsWith('/comparison.svg')){
    const choices=Array.from({length:29},(_,n)=>`<option value="${n}">${n}</option>`).join('');
    return `<figure class="experiment-figure affine-lag-figure" data-results="experiments/records/word-internal-affine-lags/results.json"><figcaption><strong>Actual text against a shuffled baseline</strong><br>Of 1,267 rune pairs six places apart inside words, how many fit the selected rule?</figcaption><div class="affine-lag-readout" role="status">Loading the verified counts…</div><details class="affine-lag-options"><summary>Explore other rules</summary><p>Change the coefficients in c′ = ac + b (mod 29). The highlighted rule is a = 27, b = 24.</p><div class="affine-lag-controls"><label>Multiplier a<select data-affine-a>${choices}</select></label><label>Offset b<select data-affine-b>${choices}</select></label></div></details><p class="small muted">The baseline shuffles runes within each word. It preserves word lengths, but it does not simulate an encryption method. <a href="${esc(v.path)}" download>Download the summary figure</a>.</p></figure>`;
  }
  if(r.id==='word-internal-affine-all-lags'&&v.path.endsWith('/selection-null.svg')){
    return `<figure class="experiment-figure all-lag-figure"><figcaption><strong>The strongest pattern: a rune repeats five places later</strong><br>Actual manuscript count compared with the average after shuffling runes inside each word.</figcaption><div class="all-lag-bars" role="img" aria-label="Same-rune repeats five places apart: 102 in the manuscript and 60.6 on average after shuffling words."><div><span>Actual text</span><i><b style="width:92.7%"></b></i><strong>102</strong></div><div><span>Shuffled words</span><i><b style="width:55.1%"></b></i><strong>60.6</strong></div></div><p><strong>4 of 999</strong> shuffled-word searches found a pattern this strong after trying all 12 distances and 841 formulas at each distance.</p><details><summary>See the full search distribution</summary><img src="${esc(v.path)}" alt="${esc(v.caption)}" loading="lazy"></details><p class="small muted">The proposed six-rune formula is below this peak. <a href="${esc(v.path)}" download>Download the distribution chart</a>.</p></figure>`;
  }
  if(r.id==='lp1-width-selection'&&v.path.endsWith('/width-comparison.svg')){
    const rows=widthSelectionComparison.map(([width,fraction,tail])=>{
      const [numerator,denominator]=fraction.split('/').map(Number);
      const score=numerator/denominator;
      const estimate=(tail+1)/50000;
      return `<tr><th scope="row">${width}${width===2?' <span class="width-selection-note">lowest R</span>':''}${width===32?' <span class="width-selection-note">smallest fixed tail</span>':''}</th><td><span class="width-selection-score">${score.toFixed(5)}</span><span class="width-selection-track" aria-hidden="true"><span class="width-selection-fill" style="width:${(score*100).toFixed(2)}%"></span></span></td><td>${estimate.toFixed(5)}</td></tr>`;
    }).join('');
    return `<figure class="experiment-figure width-selection-figure"><figcaption><strong>Six widths, two rankings.</strong> The frozen rule selects the smallest normalized imbalance R: width 2. Width 32 has the smallest unadjusted fixed-width tail; that was not the selection rule.</figcaption><div class="table-wrap"><table><caption>Observed R and diagnostic fixed-width tails for every tested width</caption><thead><tr><th scope="col">Width</th><th scope="col">Observed R</th><th scope="col">Fixed tail</th></tr></thead><tbody>${rows}</tbody></table></div><p>The matched six-width search gives a selected tail of <strong>0.12072</strong> (6,035 of 49,999 shuffled controls at or below the observed minimum, plus one). The six fixed-width tails are diagnostic; they are not adjusted or independent.</p><a href="${esc(v.path)}" download>Download the archived SVG</a></figure>`;
  }
  if(r.id==='lp1-width-selection'&&v.path.endsWith('/selected-null.svg')){
    return `<details class="experiment-extra width-selection-detail"><summary>Inspect the matched null distribution</summary><figure class="experiment-figure"><img src="${esc(v.path)}" alt="${esc(v.caption)}" loading="lazy"><figcaption>${esc(v.caption)} <a href="${esc(v.path)}" download>Download SVG</a></figcaption></figure></details>`;
  }
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
async function bindAffineLagFigure(){
  const figure=main.querySelector('.affine-lag-figure:not(.block-boundary-figure)');
  if(!figure)return;
  const a=figure.querySelector('[data-affine-a]'),b=figure.querySelector('[data-affine-b]');
  a.value='27';b.value='24';
  try{
    const response=await fetch(figure.dataset.results);
    if(!response.ok)throw Error();
    const data=await response.json();
    if(!figure.isConnected)return;
    const counts=data.affine_family.counts_by_a_b, expected=data.affine_family.word_shuffle_expected_by_a_b;
    if(counts.length!==29||expected.length!==29)throw Error();
    const all=counts.flat();
    const update=()=>{
      const multiplier=Number(a.value),offset=Number(b.value),observed=counts[multiplier][offset],mean=expected[multiplier][offset];
      const rank=1+all.filter(value=>value>observed).length;
      const scale=Math.max(80,observed,mean)*1.05;
      figure.querySelector('.affine-lag-readout').innerHTML=`<div class="affine-comparison" role="img" aria-label="Actual text: ${observed} matching pairs. Average after shuffling within words: ${mean.toFixed(1)} matching pairs."><div class="affine-comparison-row"><span>Actual text</span><div class="affine-comparison-track"><i style="width:${(observed/scale*100).toFixed(1)}%"></i></div><strong>${observed}</strong></div><div class="affine-comparison-row"><span>Shuffled words</span><div class="affine-comparison-track"><i style="width:${(mean/scale*100).toFixed(1)}%"></i></div><strong>${mean.toFixed(1)}</strong></div></div><p>This rule ranks <strong>${rank} of 841</strong> formulas checked at this distance.${multiplier===27&&offset===24?' Only <strong>3 of 2,000</strong> shuffles produced a best-rule count at least this high.':''}</p>`;
    };
    a.addEventListener('change',update);b.addEventListener('change',update);update();
  }catch{if(figure.isConnected)figure.querySelector('.affine-lag-readout').textContent='The interactive counts could not load. Download the saved result below.';}
}
async function bindBlockBoundaryFigure(){
  const figure=main.querySelector('.block-boundary-figure');
  if(!figure)return;
  const size=figure.querySelector('[data-block-size]'),phase=figure.querySelector('[data-block-phase]');
  size.value='5';
  try{
    const response=await fetch(figure.dataset.results);
    if(!response.ok)throw Error();
    const data=await response.json();
    if(!figure.isConnected)return;
    const rows=new Map(data.all_placements.map(row=>[`${row.size}:${row.phase}`,row]));
    if(rows.size!==434)throw Error();
    const setPhases=()=>{
      const previous=Number(phase.value);
      phase.innerHTML=Array.from({length:Number(size.value)},(_,n)=>`<option value="${n}">${n}</option>`).join('');
      phase.value=String(previous<Number(size.value)?previous:0);
    };
    const update=()=>{
      const row=rows.get(`${size.value}:${phase.value}`);
      figure.querySelector('.affine-lag-readout').innerHTML=`<strong>${row.matches} doublets</strong> <span>of 86 on these edges</span><div class="affine-lag-track" aria-hidden="true"><span style="width:${Math.min(100,row.matches/30*100).toFixed(1)}%"></span></div><p>Expected with page counts fixed: <strong>${row.expected.toFixed(1)}</strong> · Standardized excess: <strong>${row.z.toFixed(2)}</strong>.</p>`;
    };
    size.addEventListener('change',()=>{setPhases();update()});phase.addEventListener('change',update);
    setPhases();update();
  }catch{if(figure.isConnected)figure.querySelector('.affine-lag-readout').textContent='The interactive counts could not load. Download the saved result below.';}
}
function experimentArticle(r){
  const needsImages=r.reproduction.inputs.some(f=>/^images\/.*\.(jpe?g|png)$/i.test(f.path));
  const familyIds=new Set(experimentRecords.filter(x=>r.family&&x.family?.id===r.family.id).map(x=>x.id));
  const related=r.related.filter(id=>!familyIds.has(id));
  const methodGuides=experimentMethodGuides(r);
  const sections=[['experiment-finding','Finding'],['experiment-reproduce','Files'],...(r.family?[['experiment-family','Related tests']]:[]),['experiment-sources','Sources']];
  const sectionLinks=sections.map(([id,label])=>`<a href="#/experiments/${esc(r.id)}?section=${id}" data-anchor="${id}">${esc(label)}</a>`).join('');
  const accountFiles=[r.reproduction.script,r.article_path,...r.reproduction.inputs.map(f=>f.path),...r.reproduction.outputs.map(f=>f.path)];
  const articleFinding=r.article.match(/^## Finding\s*\n\s*\n([^\n]+(?:\n(?!\n)[^\n]+)*)/m);
  const findingHTML=articleFinding?renderExperimentMarkdown(articleFinding[1],accountFiles):`<p>${esc(r.finding)}</p>`;
  const checked=esc(r.scope_summary||`${experimentTargetSummary(r)}. ${r.bounds_note||r.scope.parameters}`);
  return head(r.title,esc(r.record_type?.label||'Research record'),'Research records')+`<article class="reading-width experiment-article">
    <p class="lede">${esc(r.reader_question||r.question)}</p>
    <nav class="section-nav experiment-section-nav" aria-label="Experiment sections">${sectionLinks}</nav>
    <section aria-labelledby="experiment-finding"><h2 id="experiment-finding">What we found</h2><div class="experiment-finding">${findingHTML}</div>
      ${(r.visuals||[]).map(v=>experimentVisual(r,v)).join('')}${r.id==='parallel-language-blocks'?languageBlockFigure():''}
      ${r.reader_note?`<div class="experiment-meaning"><h3>What it means</h3><p>${esc(r.reader_note)}</p></div>`:''}
      <p id="experiment-scope" class="experiment-checked"><strong>Checked:</strong> ${checked}</p>
      <p class="experiment-limit"><strong>Still unknown:</strong> ${esc(r.reader_limit||r.limitations.replace(/;\s*human review pending\./gi,'.').replace(/\s*human review pending\./gi,'').trim())}</p>
    </section>
    <section aria-labelledby="experiment-reproduce"><h2 id="experiment-reproduce">Get the files</h2>
      <p><a class="experiment-bundle-link" href="downloads/experiments/${esc(r.id)}.zip" download>Download experiment ZIP</a></p>
      <details class="experiment-extra"><summary>Run it yourself and browse individual files</summary><p>${esc(r.reproduction.environment)}${needsImages?' Original image inputs are separate: extract <a href="downloads/original-images.zip" download>original-images.zip</a> into the same folder.':''} The <a href="#/wiki/running-scripts">script setup guide</a> explains how to run the command below.</p>
        <div class="copyable-block experiment-command"><div class="experiment-command-heading"><p>Run from the extracted folder:</p><span role="status"></span><button type="button" data-copy-block>Copy command</button></div><pre class="reading-text" tabindex="0" aria-label="Experiment command">${esc(r.reproduction.command)}</pre></div>
        ${experimentDownloads(r)}<p class="small">Verify downloaded files against the <a href="downloads/SHA256SUMS.txt">checksums</a>, or get the <a href="downloads/reference-data.zip" download>complete reference bundle</a>.</p></details>
    </section>
    <details class="experiment-extra"><summary>Related tests</summary>
      ${r.family?`<div id="experiment-family">${experimentFamily(r)}</div>`:''}
      ${related.length?`<h3>Other related experiments</h3><ul>${related.map(id=>`<li><a href="#/experiments/${id}">${esc(experimentRecords.find(x=>x.id===id)?.title||id)}</a></li>`).join('')}</ul>`:''}
      <h3 id="experiment-remaining">What remains open</h3><p>${esc(r.next_steps)}</p>
    </details>
    <details class="experiment-extra"><summary>Detailed analysis and sources</summary>
      <dl class="experiment-scope"><dt>Pages and files</dt><dd>${experimentDetailedTargets(r)}</dd><dt>Input</dt><dd>${esc(r.scope.representation)}</dd><dt>Method</dt><dd>${esc(r.scope.procedure)}</dd><dt>Bounds</dt><dd>${esc(r.scope.parameters)}</dd><dt>Not tested</dt><dd>${esc(r.scope.exclusions)}</dd></dl>
      <div class="experiment-prose">${renderExperimentMarkdown(r.article,accountFiles)}</div>
      <div id="experiment-method-guides">${methodGuides?`<h3>Method guides</h3>${methodGuides}`:''}</div>
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
    return esc(part).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g,'<em>$1</em>');
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
