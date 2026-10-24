 'use strict';
let experimentRecords, experimentRecordsPromise, assistantConfig, assistantConfigPromise, experimentRequest, ideaCoverageRecords=[], ideaCoverageUnavailable=false, methodFamilyRecords=[], methodFamilyUnavailable=false, reportedAttemptRecords=[], reportedAttemptsUnavailable=false;
let experimentSupportStarted=false;
let ideaCoveragePending=true,methodFamilyPending=true,reportedAttemptsPending=true;
let methodRecordKinds={}, methodRecordKindById={};
let researchRecords,researchRecordsPromise,checkerRecords,checkerRecordsPromise;
const experimentRecordCache=new Map(),experimentRecordLoads=new Map();
const outcomes = {'supported':'Supported within scope','not-supported':'Not supported within scope','inconclusive':'Inconclusive'};
function stopExperimentAI(){experimentRequest?.abort();experimentRequest=null;}
const assistantEndpoint=()=>typeof assistantConfig?.endpoint==='string'&&assistantConfig.endpoint.startsWith('https://')?assistantConfig.endpoint:null;
function refreshExperimentSupportUI(){
 const slot=document.getElementById('experiment-method-guides');
 const id=location.hash.match(/^#\/experiments\/([^?]+)/)?.[1];
 if(slot&&id){
  const record=experimentRecordCache.get(id)||experimentRecords?.find(item=>item.id===id);
  if(record){
   const html=experimentMethodGuidesContent(record),preview=document.createElement('div');
   preview.innerHTML=html;
   // Compare parsed markup: entity serialization must not replace focused links.
   if(slot.innerHTML!==preview.innerHTML)slot.innerHTML=html;
  }
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
async function ensureExperimentRecords() {
  if (!experimentRecords) {
    experimentRecordsPromise??=fetch('data/experiments.json').then(async response=>{
      if (!response.ok) throw Error('The experiment index could not be loaded. Please retry.');
      const data=await response.json();
      if (!Array.isArray(data.records)) throw Error('The experiment index has an invalid format.');
      return data.records;
    }).catch(error=>{experimentRecordsPromise=null;throw error});
    experimentRecords=await experimentRecordsPromise;
  }
  return experimentRecords;
}
function validMaterials(value){
 return value&&typeof value==='object'&&!Array.isArray(value)&&
  Object.keys(value).sort().join(',')==='evidence,limits,reuse,summary'&&
  ['summary','reuse','limits'].every(key=>typeof value[key]==='string'&&value[key].trim())&&
  Array.isArray(value.evidence)&&value.evidence.length>=1&&value.evidence.length<=3&&
  value.evidence.every(path=>typeof path==='string'&&/^[a-zA-Z0-9_./-]+$/.test(path)&&!path.startsWith('/')&&!path.split('/').some(part=>!part||part==='.'||part==='..'))&&
  new Set(value.evidence).size===value.evidence.length&&[...JSON.stringify(value)].length<=1200;
}
function validCheckerPayload(data){
 const strings=values=>Array.isArray(values)&&values.every(value=>typeof value==='string');
 const text=value=>typeof value==='string'&&value.trim().length>0;
 const ids=new Set(),types=['method','replay','measurement','control','alphabet','audit','historical'];
 return data?.schema==='liberpedia-checker-records-v1'&&/^[a-f0-9]{64}$/.test(data.registry_sha256||'')&&
  Array.isArray(data.records)&&data.records.every(record=>{
   if(!record||typeof record.id!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(record.id)||ids.has(record.id))return false;
   ids.add(record.id);
   return record.status==='published'&&['title','question','summary','finding','limitations','article'].every(key=>text(record[key]))&&
    types.includes(record.record_type?.id)&&text(record.record_type?.label)&&text(record.record_type?.description)&&
    strings(record.tags)&&Array.isArray(record.method_topics)&&record.method_topics.every(topic=>
     topic&&text(topic.id)&&text(topic.title)&&strings(topic.aliases))&&
    record.scope&&strings(record.scope.pages)&&record.scope.pages.every(id=>/^lp[12]-\d{2}$/.test(id))&&
    (!Object.hasOwn(record.scope,'artifacts')||strings(record.scope.artifacts))&&
    ['representation','procedure','parameters','exclusions'].every(key=>text(record.scope[key]))&&
    ['supported','not-supported','inconclusive'].includes(record.outcome)&&
    (!record.family||['id','title','question','baseline'].every(key=>text(record.family[key])))&&
    (!record.variant||text(record.variant.label))&&
    ['reader_finding','reader_limit'].every(key=>!Object.hasOwn(record,key)||text(record[key]))&&
    (!Object.hasOwn(record,'materials')||validMaterials(record.materials));
  });
}
async function ensureCheckerRecords(){
 if(experimentRecords)return experimentRecords;
 if(checkerRecords)return checkerRecords;
 checkerRecordsPromise??=fetch('data/checker-records.json').then(async response=>{
  if(!response.ok)throw Error('The idea-checker records could not be loaded. Please retry.');
  const data=await response.json();
  if(!validCheckerPayload(data))throw Error('The idea-checker records have an invalid format. Please retry.');
  return data.records;
 }).catch(error=>{checkerRecordsPromise=null;throw error});
 checkerRecords=await checkerRecordsPromise;
 return checkerRecords;
}
function validExperimentRecord(record,id){
 if(record?.id!==id||!validCheckerPayload({schema:'liberpedia-checker-records-v1',registry_sha256:'0'.repeat(64),records:[record]}))return false;
 const text=value=>typeof value==='string'&&value.trim().length>0;
 const files=values=>Array.isArray(values)&&values.every(file=>file&&text(file.path)&&/^[a-f0-9]{64}$/.test(file.sha256||''));
 return text(record.article_path)&&text(record.next_steps)&&record.reproduction&&
  ['script','command','environment'].every(key=>text(record.reproduction[key]))&&
  files(record.reproduction.inputs)&&files(record.reproduction.outputs)&&
  Array.isArray(record.sources)&&record.sources.every(source=>text(source.label)&&text(source.url))&&
  Array.isArray(record.related)&&record.related.every(value=>typeof value==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value))&&
  (!record.visuals||Array.isArray(record.visuals)&&record.visuals.every(visual=>text(visual.path)&&text(visual.caption)));
}
async function ensureExperimentRecord(id){
 if(typeof id!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))throw Error('That experiment has no published record.');
 const warm=experimentRecords?.find(record=>record.id===id)||experimentRecordCache.get(id);
 if(warm)return warm;
 if(experimentRecords)throw Error('That experiment has no published record.');
 if(!experimentRecordLoads.has(id)){
  const loading=fetch(`reference/experiments/${id}.json`).then(async response=>{
   if(!response.ok)throw Error('That experiment record could not be loaded. Please retry.');
   const record=await response.json();
   if(!validExperimentRecord(record,id))throw Error('That experiment record has an invalid format. Please retry.');
   experimentRecordCache.set(id,record);return record;
  }).finally(()=>experimentRecordLoads.delete(id));
  experimentRecordLoads.set(id,loading);
 }
 return experimentRecordLoads.get(id);
}
async function experimentsPage(id, version, query='') {
  stopExperimentAI();
  if (version !== renderId) return;
  if (id) {
    const record=await ensureExperimentRecord(id);
    if (version !== renderId) return;
    const catalog=experimentRecords||researchRecords||checkerRecords;
    main.innerHTML = experimentArticle(record,catalog);
    bindExperimentRelated(record,version,catalog);
    bindRouteIllustration();
    bindLanguageBlockFigure();
    bindAffineLagFigure();
    bindBlockBoundaryFigure();
    if(typeof GridStemView!=='undefined')GridStemView.bind(main.querySelector('.grid-stem-view'),{isCurrent:()=>version===renderId});
    if(typeof UrlMarkerView!=='undefined')UrlMarkerView.bind(main.querySelector('.url-marker-view'),{alphabet:db.alphabet,isCurrent:()=>version===renderId});
    if(typeof PrimeLagView!=='undefined')PrimeLagView.bind(main.querySelector('.prime-lag-view'),{isCurrent:()=>version===renderId});
    if(typeof NumericSkipView!=='undefined')NumericSkipView.bind(main.querySelector('.numeric-skip-view'),{isCurrent:()=>version===renderId});
    if(typeof HeldoutPredictionView!=='undefined')HeldoutPredictionView.bind(main.querySelector('.heldout-results'),{isCurrent:()=>version===renderId});
    startExperimentSupport();
    return;
  }
  renderIdeaChecker(query,version);
  startExperimentSupport();
}
async function ensureResearchRecords(){
  if(experimentRecords)return experimentRecords;
  if(researchRecords)return researchRecords;
  researchRecordsPromise??=fetch('data/experiment-index.json').then(async response=>{
    if(!response.ok)throw Error('The research index could not be loaded. Please retry.');
    const data=await response.json();
    if(!Array.isArray(data.records))throw Error('The research index has an invalid format.');
    const complete=data.records.every(record=>typeof record.finding==='string'&&record.record_type?.id&&
      Array.isArray(record.method_topics)&&Array.isArray(record.pages)&&typeof record.limitations==='string'&&
      ['representation','procedure','parameters','exclusions'].every(key=>typeof record.scope?.[key]==='string'));
    if(!complete)return ensureExperimentRecords();
    return data.records.map(record=>({...record,status:'published',
      scope:{...record.scope,pages:record.pages,artifacts:record.artifacts||[]},review:{retested_on:record.retested_on}}));
  }).catch(error=>{researchRecordsPromise=null;throw error});
  researchRecords=await researchRecordsPromise;
  return researchRecords;
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
async function researchIndexPage(version,params=new URLSearchParams()) {
  stopExperimentAI();
  const records=await ensureResearchRecords();
  if(version!==renderId)return;
  let result=ResearchIndex.select(records,ResearchIndex.state(params));
  main.innerHTML=head('Research index','Published tests, measurements and source checks')+`<article class="research-index" data-research-state="${esc(ResearchIndex.href(result.state))}">
    <p class="research-index-actions"><a href="#/experiments">Check an idea</a> · <a href="#/wiki/solving-methods">Method guides</a></p>
    ${ResearchIndex.filters(result)}
    <p id="research-family-context" class="research-family-context"${result.state.family?'':' hidden'}>${ResearchIndex.familyContext(result)}</p>
    <div class="research-list-tools"><p id="research-count" role="status">${esc(ResearchIndex.summary(result))}</p><button id="research-reset" type="button" data-research-reset>Clear filters</button></div>
    <div id="research-results">${ResearchIndex.results(result)}</div>${footer()}</article>`;
  const article=main.querySelector('.research-index'),form=$('#research-filters');
  const fields={q:$('#research-query'),type:$('#research-type'),method:$('#research-method'),outcome:$('#research-outcome'),sort:$('#research-sort')};
  const sync=()=>{
    article.dataset.researchState=ResearchIndex.href(result.state);
    history.replaceState(history.state,'',article.dataset.researchState);
    $('#research-count').textContent=ResearchIndex.summary(result);
    $('#research-family-context').innerHTML=ResearchIndex.familyContext(result);$('#research-family-context').hidden=!result.state.family;
    $('#research-reset').hidden=(!result.state.family&&!Object.entries(fields).some(([key,field])=>field.value&&(key!=='sort'||field.value!=='title')));
  };
  const draw=(clearFamily=false)=>{
    ResearchIndex.remember(main,window.scrollY);
    const params=new URLSearchParams(Object.entries(fields).map(([key,field])=>[key,field.value]));
    if(result.state.family&&clearFamily!==true)params.set('family',result.state.family);
    result=ResearchIndex.select(records,ResearchIndex.state(params));
    $('#research-results').innerHTML=ResearchIndex.results(result);sync();
  };
  form.addEventListener('submit',event=>{event.preventDefault();draw()});
  fields.q.addEventListener('input',draw);
  for(const key of ['type','method','outcome','sort'])fields[key].addEventListener('change',draw);
  article.addEventListener('click',event=>{
    if(!event.target.closest('[data-research-reset]'))return;
    for(const [key,field] of Object.entries(fields))field.value=key==='sort'?'title':'';
    draw(true);fields.q.focus();
  });
  sync();
}
function experimentFamilyMembers(r,catalog){
 if(!catalog)return '';
 const members=catalog.filter(record=>record.family?.id===r.family.id);
 if(!members.some(record=>record.id===r.id))members.push(r);
 if(members.length===1)return '<p>No other completed variant in this group yet.</p>';
 members.sort((a,b)=>Number(b.id===r.family.baseline)-Number(a.id===r.family.baseline)||a.id.localeCompare(b.id));
 return `<ul class="experiment-related-list">${members.map(record=>`<li><a href="#/experiments/${record.id}" ${record.id===r.id?'aria-current="page"':''}>${esc(record.variant?.label||record.variant_label||record.title)}</a><p>${esc(record.reader_finding||record.finding)}</p></li>`).join('')}</ul>`;
}
function experimentFamily(r,catalog=experimentRecords){
 if(!r.family)return '';
 return `<section aria-label="Experiment family comparison"><h2>${esc(r.family.title)}</h2><p>${esc(r.family.question)}</p><div data-family-members>${experimentFamilyMembers(r,catalog)}</div></section>`;
}
function experimentOtherRelated(r,catalog){
 if(!catalog)return '';
 const siblings=new Set(catalog.filter(record=>r.family&&record.family?.id===r.family.id).map(record=>record.id));
 const ids=r.related.filter(id=>!siblings.has(id));
 return ids.length?`<h3>Other related experiments</h3><ul>${ids.map(id=>`<li><a href="#/experiments/${id}">${esc(catalog.find(record=>record.id===id)?.title||id)}</a></li>`).join('')}</ul>`:'';
}
function bindExperimentRelated(r,version,catalog){
 const slot=main.querySelector('.experiment-related');
 if(!slot||(!r.family&&!r.related.length)||catalog)return;
 const family=slot.querySelector('[data-family-members]'),other=slot.querySelector('[data-related-records]'),status=slot.querySelector('[data-related-status]'),retry=slot.querySelector('[data-related-retry]');
 const current=()=>version===renderId&&slot.isConnected&&slot.dataset.record===r.id;
 let loading=false;
 const replace=(target,html)=>{
  if(!target)return;
  const preview=document.createElement('div');preview.innerHTML=html;
  if(target.innerHTML===preview.innerHTML)return;
  const active=document.activeElement,hadFocus=target.contains(active),href=hadFocus?active.getAttribute?.('href'):null;
  target.innerHTML=html;
  if(hadFocus){
   const replacement=href?[...target.querySelectorAll('a')].find(link=>link.getAttribute('href')===href):null;
   if(!replacement)target.setAttribute('tabindex','-1');
   (replacement||target).focus({preventScroll:true});
  }
 };
 const load=async()=>{
  if(loading||!current())return;
  loading=true;retry.disabled=true;status.hidden=false;status.textContent='Loading related research…';
  try{
   const records=await ensureResearchRecords();
   if(!current())return;
   const retryFocused=document.activeElement===retry;
   replace(family,r.family?experimentFamilyMembers(r,records):'');replace(other,experimentOtherRelated(r,records));
   status.hidden=true;retry.hidden=true;
   if(retryFocused)(family?.querySelector('a')||other.querySelector('a')||slot.querySelector('[data-related-index]')).focus({preventScroll:true});
  }catch{
   if(!current())return;
   status.textContent='Related research could not be loaded. The finding and files remain available.';retry.hidden=false;
  }finally{if(current()){loading=false;retry.disabled=false;}}
 };
 retry.onclick=load;
 return load();
}

function experimentScopeLinks(r){
  return [...r.scope.pages.map(id=>`<a href="#/page/${id}">${esc(id.toUpperCase())}</a>`),...(r.scope.artifacts||[]).map(path=>`<a href="${esc(path)}">${esc(path.split('/').pop())}</a>`)].join(', ');
}
function experimentDetailedTargets(r){
  if(r.scope.pages.length<=8)return experimentScopeLinks(r);
  const first=r.scope.pages[0],last=r.scope.pages[r.scope.pages.length-1];
  const consecutive=r.scope.pages.every((page,index)=>page.slice(0,3)===first.slice(0,3)&&Number(page.slice(4))===Number(first.slice(4))+index);
  const label=consecutive?`<a href="#/page/${first}">${esc(first.toUpperCase())}</a>–<a href="#/page/${last}">${esc(last.slice(4))}</a> · ${r.scope.pages.length} pages`:`${r.scope.pages.length} manuscript pages`;
  return `${label}. <a href="reference/experiments/${esc(r.id)}.json">Exact page list and record</a>.`;
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
function experimentMethodGuidesContent(r){
 const guides=experimentMethodGuides(r);
 return guides?`<h3>Method guides</h3>${guides}`:'';
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
// LP2-02, line 1, fourth word; checked against the archived transcription.
const affineLagExample={runes:['ᛒ','ᛇ','ᛚ','ᛞ','ᚻ','ᛒ','ᛗ'],indices:[17,12,20,23,8,17,19]};
function affineLagWorkedExample(){
 return `<figure class="affine-worked-example"><figcaption><strong>What six places apart means</strong> · <a href="#/page/lp2-02?line=1">LP2-02, line 1</a></figcaption>
 <ol class="affine-example-strip" aria-label="The seven runes in the fourth word, with alphabet indices">${affineLagExample.runes.map((rune,index)=>`<li class="${index===0||index===6?'affine-example-endpoint':''}" data-example-index="${affineLagExample.indices[index]}" aria-label="Position ${index+1}, alphabet index ${affineLagExample.indices[index]}"><span class="affine-example-position" aria-hidden="true">${index+1}</span><span class="affine-example-rune" aria-hidden="true">${esc(rune)}</span><span class="affine-example-index" aria-hidden="true">${affineLagExample.indices[index]}</span></li>`).join('')}</ol>
 <p class="affine-example-distance">Six steps; five runes between.</p>
 <p>The rule compares the first rune’s index, <strong>17</strong>, with the seventh rune’s index, <strong>19</strong>.</p>
 <div class="affine-example-calculation" aria-label="24 minus 2 times 17 equals minus 10. Add 29 to get 19."><span>24 − 2 × 17 = −10</span><span>−10 + 29 = <strong>19</strong></span></div>
 <p>Use alphabet indices <strong>0–28</strong>; prime values aren’t used. Adding 29 brings −10 back into that range.</p>
 <p class="affine-example-note">This is one matching pair, not proof of a cipher. The full count and shuffled comparison follow.</p></figure>`;
}
function experimentVisual(r,v){
  if(typeof HeldoutPredictionView!=='undefined'&&HeldoutPredictionView.canRender(r,v))return HeldoutPredictionView.render();
  if(typeof NumericSkipView!=='undefined'&&NumericSkipView.canRender(r,v))return NumericSkipView.render(r.id);
  if(r.id==='prime-lag-autokey-openings'&&v.path==='experiments/records/prime-lag-autokey-openings/prime-lag.svg'&&typeof PrimeLagView!=='undefined'&&r.reproduction?.inputs?.some(file=>file.path==='experiments/records/prime-lag-autokey-openings/plan-frozen-original.json')&&r.reproduction?.outputs?.some(file=>file.path==='experiments/records/prime-lag-autokey-openings/results.json'))return PrimeLagView.render();
  if(r.id==='url-marker-affine-census'&&v.path==='experiments/records/url-marker-affine-census/marker-census.svg'&&typeof UrlMarkerView!=='undefined'&&['results.json','matches.json'].every(name=>r.reproduction?.outputs?.some(file=>file.path==='experiments/records/url-marker-affine-census/'+name)))return UrlMarkerView.render();
  if(r.id==='grid-stem-uncertainty'&&v.path.endsWith('/stem-map.svg')&&typeof GridStemView!=='undefined')return GridStemView.render();
  if(r.id==='block-boundary-doublets'&&v.path.endsWith('/boundaries.svg')){
    const sizes=Array.from({length:28},(_,index)=>`<option value="${index+2}">${index+2}</option>`).join('');
    return `<figure class="experiment-figure affine-lag-figure block-boundary-figure" data-results="experiments/records/block-boundary-doublets/results.json"><figcaption><strong>Inspect the 434 placements</strong><br>Choose a block size and a shared phase. Phase zero places a boundary after every full block, counting from the start of each page.</figcaption><div class="affine-lag-controls"><label>Block size<select data-block-size disabled>${sizes}</select></label><label>Phase<select data-block-phase disabled></select></label></div><div class="affine-lag-readout" role="status">Loading the verified counts…</div><button type="button" data-figure-retry hidden style="min-height:44px">Retry counts</button><p class="small muted">The size and phase search was compared with the same search on 3,000 fixed-count controls. A single appealing row is not a selected-search result.</p><a href="${esc(v.path)}" download>Download summary figure</a></figure>`;
  }
  if(r.id==='word-internal-affine-lags'&&v.path.endsWith('/comparison.svg')){
    const choices=Array.from({length:29},(_,n)=>`<option value="${n}">${n}</option>`).join('');
    return `${affineLagWorkedExample()}<figure class="experiment-figure affine-lag-figure" data-results="experiments/records/word-internal-affine-lags/results.json"><figcaption><strong>Actual text against a shuffled baseline</strong><br>Of 1,267 rune pairs six places apart inside words, how many fit the selected rule?</figcaption><div class="affine-lag-readout" role="status">Loading the verified counts…</div><button type="button" data-figure-retry hidden style="min-height:44px">Retry counts</button><details class="affine-lag-options"><summary>Explore other rules</summary><p>Change the coefficients in c′ = ac + b (mod 29). The highlighted rule is a = 27, b = 24.</p><div class="affine-lag-controls"><label>Multiplier a<select data-affine-a disabled>${choices}</select></label><label>Offset b<select data-affine-b disabled>${choices}</select></label></div></details><p class="small muted">The baseline shuffles runes within each word. It preserves word lengths, but it does not simulate an encryption method. <a href="${esc(v.path)}" download>Download the summary figure</a>.</p></figure>`;
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
function bindFigureCounts(figure,controls,initialize){
  const readout=figure.querySelector('.affine-lag-readout'),retry=figure.querySelector('[data-figure-retry]');
  let loading=false;
  const load=async()=>{
    if(loading||!figure.isConnected)return;
    const retryHadFocus=document.activeElement===retry;
    loading=true;controls.forEach(control=>control.disabled=true);retry.disabled=true;
    readout.textContent='Loading the verified counts…';
    const controller=new AbortController();let timer;
    try{
      const data=await Promise.race([
        (async()=>{const response=await fetch(figure.dataset.results,{signal:controller.signal});if(!response.ok)throw Error();return response.json();})(),
        new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Figure request timed out'));},10000);})
      ]);
      if(!figure.isConnected)return;
      initialize(data);controls.forEach(control=>control.disabled=false);
      if(retryHadFocus&&(document.activeElement===retry||document.activeElement===document.body))controls[0].focus({preventScroll:true});
      retry.hidden=true;
    }catch{
      if(figure.isConnected){
        readout.textContent='The interactive counts could not load. Retry or download the saved result below.';
        retry.hidden=false;retry.disabled=false;
        if(retryHadFocus&&document.activeElement===document.body)retry.focus({preventScroll:true});
      }
    }finally{
      clearTimeout(timer);
      loading=false;if(figure.isConnected)retry.disabled=false;
    }
  };
  retry.addEventListener('click',load);
  return load();
}
async function bindAffineLagFigure(){
  const figure=main.querySelector('.affine-lag-figure:not(.block-boundary-figure)');
  if(!figure)return;
  const a=figure.querySelector('[data-affine-a]'),b=figure.querySelector('[data-affine-b]');
  a.value='27';b.value='24';
  return bindFigureCounts(figure,[a,b],data=>{
    const counts=data.affine_family?.counts_by_a_b,expected=data.affine_family?.word_shuffle_expected_by_a_b;
    const matrix=(values,integer)=>Array.isArray(values)&&values.length===29&&values.every(row=>Array.isArray(row)&&row.length===29&&row.every(value=>Number.isFinite(value)&&value>=0&&(!integer||Number.isInteger(value))));
    if(!matrix(counts,true)||!matrix(expected,false))throw Error();
    const all=counts.flat();
    const update=()=>{
      const multiplier=Number(a.value),offset=Number(b.value),observed=counts[multiplier][offset],mean=expected[multiplier][offset];
      const rank=1+all.filter(value=>value>observed).length;
      const scale=Math.max(80,observed,mean)*1.05;
      figure.querySelector('.affine-lag-readout').innerHTML=`<div class="affine-comparison" role="img" aria-label="Actual text: ${observed} matching pairs. Average after shuffling within words: ${mean.toFixed(1)} matching pairs."><div class="affine-comparison-row"><span>Actual text</span><div class="affine-comparison-track"><i style="width:${(observed/scale*100).toFixed(1)}%"></i></div><strong>${observed}</strong></div><div class="affine-comparison-row"><span>Shuffled words</span><div class="affine-comparison-track"><i style="width:${(mean/scale*100).toFixed(1)}%"></i></div><strong>${mean.toFixed(1)}</strong></div></div><p>This rule ranks <strong>${rank} of 841</strong> formulas checked at this distance.${multiplier===27&&offset===24?' Only <strong>3 of 2,000</strong> shuffles produced a best-rule count at least this high.':''}</p>`;
    };
    update();a.addEventListener('change',update);b.addEventListener('change',update);
  });
}
async function bindBlockBoundaryFigure(){
  const figure=main.querySelector('.block-boundary-figure');
  if(!figure)return;
  const size=figure.querySelector('[data-block-size]'),phase=figure.querySelector('[data-block-phase]');
  size.value='5';
  return bindFigureCounts(figure,[size,phase],data=>{
    const total=data.doublet_count;
    if(!Number.isInteger(total)||total<=0||!Array.isArray(data.all_placements))throw Error();
    const rows=new Map(data.all_placements.map(row=>[`${row.size}:${row.phase}`,row]));
    if(rows.size!==434||[...rows.values()].some(row=>!Number.isInteger(row.size)||row.size<2||row.size>29||!Number.isInteger(row.phase)||row.phase<0||row.phase>=row.size||!Number.isInteger(row.matches)||row.matches<0||row.matches>total||!Number.isFinite(row.expected)||!Number.isFinite(row.z)))throw Error();
    const setPhases=()=>{
      const previous=Number(phase.value);
      phase.innerHTML=Array.from({length:Number(size.value)},(_,n)=>`<option value="${n}">${n}</option>`).join('');
      phase.value=String(previous<Number(size.value)?previous:0);
    };
    const update=()=>{
      const row=rows.get(`${size.value}:${phase.value}`);
      figure.querySelector('.affine-lag-readout').innerHTML=`<strong>${row.matches} doublets</strong> <span>of ${total} on these edges</span><div class="affine-lag-track" aria-hidden="true"><span style="width:${(row.matches/total*100).toFixed(1)}%"></span></div><p>Expected with page counts fixed: <strong>${row.expected.toFixed(1)}</strong> · Standardized excess: <strong>${row.z.toFixed(2)}</strong>.</p>`;
    };
    setPhases();update();size.addEventListener('change',()=>{setPhases();update()});phase.addEventListener('change',update);
  });
}

function experimentFindingText(text,pages){
  const declared=new Set(Array.isArray(pages)?pages:[]);
  return String(text).split(/(\bLP[12]-\d{2}\b)/gi).map(part=>
    declared.has(part.toLowerCase())?`<a href="#/reader/${part.toLowerCase()}">${esc(part)}</a>`:esc(part)
  ).join('');
}

function experimentArticle(r,catalog=experimentRecords){
  const needsImages=r.reproduction.inputs.some(f=>/^(?:images\/.*\.(?:jpe?g|png)|exports\/sources\/cicada-2014-seventh-onion\/\d+\.jpg)$/i.test(f.path));
  const sections=[['experiment-finding','Finding'],['experiment-reproduce','Files'],...(r.family?[['experiment-family','Related tests']]:[]),['experiment-sources','Sources']];
  const sectionLinks=sections.map(([id,label])=>`<a href="#/experiments/${esc(r.id)}?section=${id}" data-anchor="${id}">${esc(label)}</a>`).join('');
  const accountFiles=[r.reproduction.script,r.article_path,...r.reproduction.inputs.map(f=>f.path),...r.reproduction.outputs.map(f=>f.path)];
  const findingHTML=`<p>${experimentFindingText(r.reader_finding||r.finding,r.scope.pages)}</p>`;
  const checked=esc(r.scope_summary||`${experimentTargetSummary(r)}. ${r.bounds_note||r.scope.parameters}`);
  return head(r.title,esc(r.record_type?.label||'Research record'),'Research index','#/research')+`<article class="reading-width experiment-article">
    <p class="lede">${esc(r.reader_question||r.question)}</p>
    <nav class="section-nav experiment-section-nav" aria-label="Experiment sections">${sectionLinks}</nav>
    <section aria-labelledby="experiment-finding"><h2 id="experiment-finding">What we found</h2><div class="experiment-finding">${findingHTML}</div>
      ${(r.visuals||[]).map(v=>experimentVisual(r,v)).join('')}${r.id==='parallel-language-blocks'?languageBlockFigure():''}
      ${r.reader_note?`<div class="experiment-meaning"><h3>What it means</h3><p>${esc(r.reader_note)}</p></div>`:''}
      <p id="experiment-scope" class="experiment-checked"><strong>Checked:</strong> ${checked}</p>
      <p class="experiment-limit"><strong>Limit:</strong> ${esc(r.reader_limit||r.limitations.replace(/;\s*human review pending\./gi,'.').replace(/\s*human review pending\./gi,'').trim())}</p>
    </section>
    <section aria-labelledby="experiment-reproduce"><h2 id="experiment-reproduce">Get the files</h2>
      <p><a class="experiment-bundle-link" href="downloads/experiments/${esc(r.id)}.zip" download>Download experiment ZIP</a></p>
      <details class="experiment-extra"><summary>Run it yourself and browse individual files</summary><p>${esc(r.reproduction.environment)}${needsImages?' Original image inputs are separate: extract <a href="downloads/original-images.zip" download>original-images.zip</a> into the same folder.':''} The <a href="#/wiki/running-scripts">script setup guide</a> explains how to run the command below.</p>
        <div class="copyable-block experiment-command"><div class="experiment-command-heading"><p>Run from the extracted folder:</p><span role="status"></span><button type="button" data-copy-block>Copy command</button></div><pre class="reading-text" tabindex="0" aria-label="Experiment command">${esc(r.reproduction.command)}</pre></div>
        ${experimentDownloads(r)}<p class="small">Verify downloaded files against the <a href="downloads/SHA256SUMS.txt">checksums</a>, or get the <a href="downloads/reference-data.zip" download>complete reference bundle</a>.</p></details>
    </section>
    <details class="experiment-extra experiment-related" data-record="${esc(r.id)}"><summary>Related tests</summary>
      ${r.family?`<div id="experiment-family">${experimentFamily(r,catalog)}</div>`:''}
      <div data-related-records>${experimentOtherRelated(r,catalog)}</div>
      ${r.family||r.related.length?`<p class="small muted" data-related-status role="status"${catalog?' hidden':''}>Loading related research…</p><button type="button" data-related-retry hidden>Retry related research</button><p class="small"><a data-related-index href="#/research${r.family?'?family='+encodeURIComponent(r.family.id):''}">Browse related research in the index</a></p>`:''}
      <h3 id="experiment-remaining">What remains open</h3><p>${esc(r.next_steps)}</p>
    </details>
    <details class="experiment-extra"><summary>Detailed analysis and sources</summary>
      <dl class="experiment-scope"><dt>Pages and files</dt><dd>${experimentDetailedTargets(r)}</dd><dt id="experiment-input">Input</dt><dd>${esc(r.scope.representation)}</dd><dt id="experiment-procedure">Method</dt><dd>${esc(r.scope.procedure)}</dd><dt id="experiment-bounds">Bounds</dt><dd>${esc(r.scope.parameters)}</dd><dt id="experiment-exclusions">Not tested</dt><dd>${esc(r.scope.exclusions)}</dd><dt id="experiment-limitations">Limitations</dt><dd>${esc(r.limitations)}</dd></dl>
      <div class="experiment-prose">${renderExperimentMarkdown(r.article,accountFiles,r.article_links||{},(r.visuals||[]).map(visual=>visual.path))}</div>
      <div id="experiment-method-guides">${experimentMethodGuidesContent(r)}</div>
      <h3 id="experiment-sources">Sources</h3><ul>${r.sources.map(s=>`<li><a href="${esc(s.url)}">${esc(s.label)}</a></li>`).join('')}</ul>
    </details>
    ${footer()}</article>`;
}

// Authored experiment Markdown: escaped text, links, headings, lists, simple tables and code; no embedded HTML.
function renderExperimentMarkdown(markdown,files=[],articleLinks={},shownVisuals=[]){
  const safeLink=href=>/^https:\/\/[^\s<>"']+$/.test(href)||
    /^#\/(?:pages|wiki\/[a-z0-9-]+|page\/lp[12]-\d{2}|reader\/lp[12]-\d{2}|experiments\/[a-z0-9-]+)(?:\?[a-zA-Z0-9_%=&.-]+)?$/.test(href)||
    (files.includes(href)&&/^[a-zA-Z0-9_./-]+$/.test(href)&&!href.startsWith('/')&&!href.split('/').includes('..'));

  const canonicalLocal=href=>typeof href==='string'&&/^[a-zA-Z0-9_./-]+$/.test(href)&&
    href.split('/').every(part=>part&&part!=='.'&&part!=='..');
  const anchorHref=href=>{
    // Aliases are builder-vetted navigation, never new image/reproduction inputs.
    const aliases=articleLinks&&typeof articleLinks==='object'&&!Array.isArray(articleLinks)?articleLinks:{};
    if(Object.hasOwn(aliases,href)&&canonicalLocal(href)){
      const target=aliases[href];
      if(canonicalLocal(target)||typeof target==='string'&&/^#\/experiments\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(target))return target;
    }
    return safeLink(href)?href:null;
  };

  const shownFigures=new Set(Array.isArray(shownVisuals)?shownVisuals:[]);
  let inCode=false,code=[],paragraph=[],html=[],listType='',codeNumber=0;
  const codeBlock=lines=>{const number=++codeNumber;return `<div class="copyable-block unwrapped"><div class="block-tools"><span role="status"></span><button type="button" data-wrap-block aria-pressed="false" aria-label="Wrap lines in experiment text block ${number}">Wrap lines</button><button type="button" data-copy-block aria-label="Copy experiment text block ${number}">Copy</button></div><pre class="reading-text" tabindex="0" aria-label="Experiment text block ${number}">${esc(lines.join('\n'))}</pre></div>`;};
  const inline=text=>String(text).split(/(`[^`]+`|\[[^\]\n]+\]\([^)]+\))/g).map(part=>{
    if(/^`[^`]+`$/.test(part))return '<code>'+esc(part.slice(1,-1))+'</code>';
    const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if(link){const href=anchorHref(link[2]);return href?`<a href="${esc(href)}">${esc(link[1])}</a>`:esc(part);}
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
      if(shownFigures.has(figure[2])){
        flush();closeList();html.push(`<p class="small experiment-figure-reference">${esc(figure[1])} <a href="${esc(figure[2])}" target="_blank" rel="noopener">Open full-size figure ↗</a></p>`);continue;
      }
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
