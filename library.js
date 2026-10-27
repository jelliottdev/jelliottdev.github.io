'use strict';
// Layout adapted from the supplied complete-current handoff; data is live.
function readerLimit(value){return String(value??'').replace(/\s*(?:Computational review\s*;\s*)?human review(?: is)? pending\.?\s*$/i,'').replace(/[;\s]+$/,'').trim();}
function libraryEscape(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
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
  const codeBlock=lines=>{const number=++codeNumber;return `<div class="copyable-block unwrapped"><div class="block-tools"><span role="status"></span><button type="button" data-wrap-block aria-pressed="false" aria-label="Wrap lines in experiment text block ${number}">Wrap lines</button><button type="button" data-copy-block aria-label="Copy experiment text block ${number}">Copy</button></div><pre class="reading-text" tabindex="0" aria-label="Experiment text block ${number}">${libraryEscape(lines.join('\n'))}</pre></div>`;};
  const inline=text=>String(text).split(/(`[^`]+`|\[[^\]\n]+\]\([^)]+\))/g).map(part=>{
    if(/^`[^`]+`$/.test(part))return '<code>'+libraryEscape(part.slice(1,-1))+'</code>';
    const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if(link){const href=anchorHref(link[2]);return href?`<a href="${libraryEscape(href)}">${libraryEscape(link[1])}</a>`:libraryEscape(part);}
    return libraryEscape(part).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g,'<em>$1</em>');
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
        flush();closeList();html.push(`<p class="small experiment-figure-reference">${libraryEscape(figure[1])} <a href="${libraryEscape(figure[2])}" target="_blank" rel="noopener">Open full-size figure ↗</a></p>`);continue;
      }
      flush();closeList();html.push(`<figure class="experiment-figure"><a class="experiment-figure-image" href="${libraryEscape(figure[2])}" target="_blank" rel="noopener"><img src="${libraryEscape(figure[2])}" alt="${libraryEscape(figure[1])}" loading="lazy"></a><figcaption>${libraryEscape(figure[1])} <a href="${libraryEscape(figure[2])}" target="_blank" rel="noopener">Open full-size figure ↗</a></figcaption></figure>`);continue;
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
      const compact=headers.length<=2;
      html.push((compact?'<div class="table-wrap experiment-compact-table">':'<p class="table-scroll-hint">Scroll table sideways for all columns →</p><div class="table-wrap" role="region" aria-label="Scrollable experiment data table" tabindex="0">')+'<table><thead><tr>'+headers.map(value=>'<th scope="col">'+inline(value)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>');
      continue;
    }
    const item=line.match(/^(?:([-*])|\d+\.) (.+)$/);
    if(item){flush();const type=item[1]?'ul':'ol';if(listType!==type){closeList();html.push(`<${type}>`);listType=type;}html.push('<li>'+inline(item[2])+'</li>');continue;}
    closeList();
    const heading=line.match(/^(#{1,6}) (.+)$/);
    if(heading){flush();const level=Math.min(4,heading[1].length+1);html.push(`<h${level}>${libraryEscape(heading[2])}</h${level}>`);}else paragraph.push(line);
  }
  flush();closeList();if(code.length)html.push(codeBlock(code));return html.join('');
}



// Maintained presentation adapters; authoritative content remains in production exports.
function compactPages(pages=[]){const out=[];for(const release of [1,2]){const values=[...new Set(pages.filter(id=>new RegExp('^lp'+release+'-\\d{2}$').test(id)).map(id=>Number(id.slice(4))))].sort((a,b)=>a-b);for(let i=0;i<values.length;i++){let j=i;while(j+1<values.length&&values[j+1]===values[j]+1)j++;out.push('LP'+release+'-'+String(values[i]).padStart(2,'0')+(j>i?'–'+String(values[j]).padStart(2,'0'):''));i=j}}return out.join(', ')||'Artifact-specific'}
function recordFiles(record){const r=record.reproduction||{};return [{path:r.script,sha256:r.script_sha256||record.script_sha256},...(r.inputs||[]),...(r.outputs||[])].filter((f,i,list)=>f.path&&list.findIndex(x=>x.path===f.path)===i)}
function recordFileHref(file){if(file.source_path===undefined)return file.path;if(!/^experiments\/records\/[a-z0-9]+(?:-[a-z0-9]+)*\/record\.json$/.test(file.path)||!/^[a-f0-9]{64}$/.test(file.sha256)||file.source_path!=='published-sources/records/'+file.sha256+'.json')throw Error('Invalid retained reproduction source');return file.source_path}
function recordArticleLinks(record){const links={...(record.article_links||{})};for(const file of recordFiles(record))if(file.source_path!==undefined)links[file.path]=recordFileHref(file);return links}
function readerSections(markdown,titles){if(titles===undefined)return {selected:[],remaining:markdown};if(!Array.isArray(titles)||titles.length>3||titles.some(x=>typeof x!=='string'||!x.trim())||new Set(titles).size!==titles.length)throw Error('Invalid reader sections');const lines=markdown.split('\n'),headings=[];let fence=null;for(let i=0;i<lines.length;i++){const marker=lines[i].match(/^ {0,3}(`{3,}|~{3,})(.*)$/);if(fence){if(marker&&marker[1][0]===fence[0]&&marker[1].length>=fence.length&&!marker[2].trim())fence=null;continue}if(marker){fence=marker[1];continue}const h=lines[i].match(/^ {0,3}(#{1,2})[\t ]+(.+?)\r?$/);if(h)headings.push({i,level:h[1].length,title:h[2]})}const removed=new Set(),selected=titles.map(title=>{const matches=headings.filter(h=>h.level===2&&h.title===title);if(matches.length!==1)throw Error('Reader section not found: '+title);const h=matches[0],end=headings.find(x=>x.i>h.i)?.i??lines.length;for(let i=h.i;i<end;i++)removed.add(i);return {title,body:lines.slice(h.i+1,end).join('\n')}});return {selected,remaining:lines.filter((_,i)=>!removed.has(i)).join('\n')}}
function referencedRecords(html,known){return [...new Set([...html.matchAll(/#\/experiments?\/([a-z0-9]+(?:-[a-z0-9]+)*)/g)].map(x=>x[1]))].filter(id=>known.has(id))}
function adaptMetadata(guides,categories,index){const rows=Array.isArray(guides)?guides:guides?.guides;if(!Array.isArray(rows)||!Array.isArray(categories)||!Array.isArray(index?.records))throw Error('The library index is invalid.');const known=new Set(index.records.map(r=>r.id));return {guides:rows.map(g=>({...g,experiments:referencedRecords((g.references||[]).join(' '),known)})),categories,experiments:index.records.map(r=>({...r,pages:r.scope?.pages||r.pages||[]}))}}
function guideSource(guide){const source=guide.source||guide.id+'.html';if(!/^[a-z0-9/-]+\.html$/.test(source)||source.split('/').some(p=>p==='..'))throw Error('Invalid guide source');return 'articles/'+source}

const interactiveRecordIds=new Set(['keyword-skip-family','heldout-rune-prediction','payload-phase-skip-grid','page-number-prime-skip-grid','numeric-stream-skip-grid','artifact-stream-skip-grid','fibonacci-stream-skip-grid','prime-lag-autokey-openings','url-marker-affine-census','grid-stem-uncertainty','block-boundary-doublets','word-internal-affine-lags']);
function hasInteractive(record){return interactiveRecordIds.has(record.id)&&!!record.visuals?.length}

function researchHref(params={}){const query=new URLSearchParams({mode:'list'});for(const [key,value] of Object.entries(params)){if(['q','family','type','method','page','outcome'].includes(key)&&value!==null&&value!==undefined&&value!=='')query.set(key,String(value))}return 'research.html?v=record-panel-20261024#'+query.toString()}
function sectionTab(section){return ({'experiment-finding':'overview','experiment-remaining':'overview','experiment-family':'overview','experiment-reproduce':'reproduce','experiment-sources':'sources','experiment-method-guides':'sources','experiment-input':'scope','experiment-procedure':'scope','experiment-bounds':'scope','experiment-exclusions':'scope','experiment-limitations':'scope'})[section]||null}


function searchLibrary(data,query,{wiki=globalThis.WikiSearch,index=globalThis.ResearchIndex}={}){if(!wiki?.search||!index?.select)throw Error('Search could not load. Please retry.');const q=String(query||'').trim();if(!q)return {guides:[],experiments:[]};const guides=wiki.search({articles:data.guides},q).filter(h=>h.type==='guide').map(hit=>{const id=hit.href.match(/^#\/wiki\/([^?]+)/)?.[1];return {...hit,guide:data.guides.find(g=>g.id===id),href:hit.href.replace(/^#\/wiki\//,'#/guide/')}}).filter(h=>h.guide);const defaults=index.state(new URLSearchParams());const research=index.select(data.experiments,{...defaults,q});return {guides,experiments:research.allRecords}}

const LibraryView={readerLimit,compactPages,recordFiles,recordFileHref,recordArticleLinks,readerSections,referencedRecords,adaptMetadata,searchLibrary,researchHref,sectionTab,guideSource,hasInteractive,renderMarkdown:renderExperimentMarkdown};
if(typeof module!=='undefined'&&module.exports)module.exports=LibraryView;
if(typeof window!=='undefined')window.LibraryView=LibraryView;
'use strict';
(() => {
 if(typeof document==='undefined')return;
 const main=document.getElementById('main'),contents=document.getElementById('contents-dialog'),filesDialog=document.getElementById('files-dialog');
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const chevron='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>';
 const searchIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>';
 const typeNames={method:'Solving tests',replay:'Method replays',measurement:'Measurements',control:'Controls',alphabet:'Alphabet analyses',audit:'Source audits',historical:'Historical reproductions'};
 const outcomeNames={supported:'Supported within scope','not-supported':'Not supported within scope',inconclusive:'Inconclusive'};
 const cache=new Map(),positions=new Map();let data,version=0,current=null,currentRecord=null,currentEntry=null,currentHash='',questionMount=null,publishedDiscoveryMount=null;
 let reactionMount=null,reactions=null,reactionPreferences=null;
 if(globalThis.ResearchPreferences&&globalThis.ResearchReactions){
  let reactionStorage=null;try{reactionStorage=globalThis.localStorage;}catch{}
  reactionPreferences=globalThis.ResearchPreferences.create({storage:reactionStorage,crypto:globalThis.crypto,onChange:()=>reactions?.refresh()});
  reactions=globalThis.ResearchReactions.create({preferences:reactionPreferences,fetcher:(...args)=>fetch(...args),loadConfig:()=>fetch('data/assistant.json').then(response=>{if(!response.ok)throw Error('Configuration unavailable');return response.json();}),pageURL:location.href});
  window.addEventListener('storage',event=>reactionPreferences.handleStorageEvent(event));
 }
 history.scrollRestoration='manual';
 function entryKey(){
  if(window.navigation?.currentEntry?.key)return window.navigation.currentEntry.key;
  const previous=history.state||{};
  if(previous.libraryEntry?.url===location.href)return previous.libraryEntry.key;
  const value={key:crypto.randomUUID(),url:location.href};history.replaceState({...previous,libraryEntry:value},'',location.href);return value.key;
 }
 function savePosition(force=false,anchor=null){
  if(!currentEntry||!current||(!force&&location.hash!==currentHash))return;
  const focus=anchor||document.activeElement,links=[...main.querySelectorAll('a')];
  positions.set(currentEntry,{y:scrollY,href:focus?.closest?.('a')?.getAttribute('href')||'',linkIndex:links.indexOf(focus?.closest?.('a')),id:focus?.id||''});
 }
 function restorePosition(saved){
  window.scrollTo(0,saved.y);
  const target=(saved.id&&document.getElementById(saved.id))||[...main.querySelectorAll('a')][saved.linkIndex]||[...main.querySelectorAll('a')].find(a=>a.getAttribute('href')===saved.href);
  target?.focus({preventScroll:true});
 }
 const normal=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
 const url=(path,params={})=>{if(path==='experiments')return researchHref(params);const search=new URLSearchParams(Object.entries(params).filter(([,value])=>value!==''&&value!==null&&value!==undefined));return '#/'+path+(search.size?'?'+search:'')};
 function state(){const [path,query='']=(location.hash.slice(2)||'guides').split('?');return {path,parts:path.split('/'),params:new URLSearchParams(query)}}
 function edit(params,changes){return {...Object.fromEntries(params),...changes}}
 async function load(path){if(cache.has(path))return cache.get(path);const promise=fetch(path,{cache:'no-cache'}).then(response=>{if(!response.ok)throw Error('This source could not be loaded.');return path.endsWith('.json')?response.json():response.text()}).catch(error=>{cache.delete(path);throw error});cache.set(path,promise);return promise}
 function categories(){const known=new Set(data.categories.map(group=>group.title));return [...data.categories,...[...new Set(data.guides.map(guide=>guide.category))].filter(title=>!known.has(title)).map((title,i)=>({id:'other-'+i,title}))]}
 function guideHref(id){return url('guide/'+id)}
 function experimentHref(id,tab='overview'){return url('experiment/'+id,tab==='overview'?{}:{tab})}
 function familyMembers(id){return data.experiments.filter(record=>record.family?.id===id)}
 function familyHref(id,params={}){return url('family/'+id,params)}
 function rewriteHref(href,guideId=''){
  if(!href)return href;
  const canonical=href.match(/^https:\/\/jelliottdev\.github\.io\/(#.*)$/);if(canonical)href=canonical[1];
  let match=href.match(/^#\/wiki\/([^?]+)(.*)$/);if(match)return '#/guide/'+match[1]+match[2];
  match=href.match(/^#\/experiments\/([^?]+)(.*)$/);if(match)return '#/experiment/'+match[1]+match[2];
  if(/^#\/wiki(?:\?|$)/.test(href))return '#/guides';
  if(/^#\/(?:research|experiments)(?:\?|$)/.test(href))return href.replace(/^#\/(research|experiments)/,'#/experiments');
  match=href.match(/^#\/reader\/(lp[12]-\d{2})/);if(match)return 'reader.html#'+match[1];
  if(href.startsWith('#/'))return 'index.html'+href;
  if(href.startsWith('#')&&guideId)return url('guide/'+guideId,{section:href.slice(1)});
  if(/^(https?:|mailto:|data:|blob:|\/)/.test(href))return href;
  return href;
 }
 function prepareAuthored(html,guideId=''){
  const doc=new DOMParser().parseFromString(html,'text/html');doc.querySelectorAll('script,iframe,object,embed,base').forEach(el=>el.remove());doc.querySelectorAll('*').forEach(el=>{for(const a of [...el.attributes])if(/^on/i.test(a.name)||a.name==='srcdoc'||['href','src','xlink:href'].includes(a.name)&&/^\s*(?:javascript|vbscript):/i.test(a.value))el.removeAttribute(a.name)});
  doc.querySelectorAll('a[href]').forEach(anchor=>anchor.setAttribute('href',rewriteHref(anchor.getAttribute('href'),guideId)));
  doc.querySelectorAll('img[src]').forEach(img=>img.setAttribute('src',rewriteHref(img.getAttribute('src'))));
  doc.querySelectorAll('table').forEach(table=>{if(!table.parentElement.classList.contains('table-wrap')){const wrap=doc.createElement('div');wrap.className='table-wrap';table.before(wrap);wrap.append(table)}if(!table.parentElement.classList.contains('experiment-compact-table')){table.parentElement.tabIndex=0;table.parentElement.setAttribute('role','region');table.parentElement.setAttribute('aria-label',table.caption?.textContent||'Scrollable data table')}});
  return doc.body.innerHTML;
 }
 function headerActive(kind){document.querySelectorAll('[data-nav]').forEach(anchor=>{if(anchor.dataset.nav===kind)anchor.setAttribute('aria-current','page');else anchor.removeAttribute('aria-current')})}
 function queuePosition(callback){const entry=currentEntry,hash=location.hash,run=version;
  requestAnimationFrame(()=>{if(version===run&&currentEntry===entry&&currentHash===hash&&location.hash===hash)callback()});
 }
 function finish(s,kind,title){headerActive(kind);document.title=title+' · Liberpedia';current=s;currentHash=location.hash;currentEntry=entryKey();
  const field=document.getElementById('global-query');if(field){field.value=s.params.get('q')||'';field.placeholder='Search Liberpedia';const label=document.querySelector('label[for="global-query"]');if(label)label.textContent=field.placeholder;}
  const saved=positions.get(currentEntry);if(saved){queuePosition(()=>restorePosition(saved));return}
  const section=s.params.get('section');if(section){queuePosition(()=>jump(section));return}
  window.scrollTo(0,0);main.focus({preventScroll:true});
 }
 function jump(id){const target=document.getElementById(id);if(!target)return;for(let p=target.closest('details');p;p=p.parentElement?.closest('details'))p.open=true;target.tabIndex=-1;target.focus({preventScroll:true});target.scrollIntoView({block:'start'})}
 function crumb(items){return '<nav class="breadcrumb" aria-label="Breadcrumb">'+items.map(([text,href])=>href?`<a href="${esc(href)}">${esc(text)}</a>`:esc(text)).join(chevron)+'</nav>'}
 function queryMatch(item,query,isExperiment=false){
  const requested=[];const rest=query.replace(/\blp\s*([12])[- :]*(\d{1,2})(?:\s*[–-]\s*(\d{1,2}))?\b/gi,(_,release,start,end)=>{for(let n=+start;n<=+(end??start);n++)requested.push(`lp${release}-${String(n).padStart(2,'0')}`);return ''});
  if(requested.length&&!requested.every(page=>(item.pages||[]).includes(page)))return false;
  const text=normal([item.title,item.reader_title,item.reader_intro,item.text,item.summary,item.finding,item.reader_finding,item.category,...(item.aliases||[]),...(item.tags||[]),...(item.method_topics||[]).map(topic=>topic.title),item.family?.title].join(' '));
  return normal(rest).split(' ').filter(Boolean).every(word=>text.includes(word));
 }
 function directoryNav(s,isExperiment){const links=isExperiment?[['','All experiments'],...Object.entries(typeNames)]:[['','All subjects'],...categories().map(group=>[group.id,group.title])];const key=isExperiment?'type':'category';
  return links.map(([id,title])=>`<a href="${esc(url(s.path,edit(s.params,{[key]:id,page:null})))}"${(s.params.get(key)||'')===id?' aria-current="page"':''}>${esc(title)}</a>`).join('');
 }
 function pagination(s,total,page,size){const pages=Math.max(1,Math.ceil(total/size));if(pages<2)return '';return `<nav class="page-controls" aria-label="Result pages">${page>1?`<a href="${esc(url(s.path,edit(s.params,{page:page-1})))}">Previous</a>`:'<span></span>'}<span>Page ${page} of ${pages}</span>${page<pages?`<a href="${esc(url(s.path,edit(s.params,{page:page+1})))}">Next</a>`:'<span></span>'}</nav>`}
 function guideRow(guide,categoryVisible=true){return `<article class="list-row"><h2><a href="${guideHref(guide.id)}">${esc(guide.title)}</a></h2><p>${esc(guide.summary)}</p>${categoryVisible?`<div class="row-meta"><span>${esc(guide.category)}</span></div>`:''}</article>`}
 function experimentRow(record,level=2){if(level!==2&&level!==3)throw Error('Use a supported research heading level.');return `<article class="list-row"><h${level} class="research-row-title"><a href="${experimentHref(record.id)}">${esc(globalThis.RecordTestView?.title(record)||record.title)}</a></h${level}>${globalThis.RecordTestView?.renderIntro(record)||''}<p>${esc(record.reader_finding||record.finding)}</p><div class="row-meta"><span>${esc(record.record_type?.label||'Research record')}</span><span class="finding-label">${esc(outcomeNames[record.outcome]||record.outcome)}</span><span>${esc(compactPages(record.pages))}</span>${record.family&&familyMembers(record.family.id).length>1?`<a href="${familyHref(record.family.id,{from:record.id})}">See related tests</a>`:''}</div></article>`}
 function filteredExperiments(s){
  const q=s.params.get('q')||'',guide=data.guides.find(g=>g.id===s.params.get('guide'));
  let records=data.experiments.filter(item=>queryMatch(item,q,true));
  if(s.params.get('guide')&&guide&&!guide.experiments.length){records=[];}if(s.params.get('type'))records=records.filter(record=>record.record_type?.id===s.params.get('type'));
  if(guide)records=records.filter(record=>guide.experiments.includes(record.id));
  if(s.params.get('family'))records=records.filter(record=>record.family?.id===s.params.get('family'));
  if(s.params.get('method'))records=records.filter(record=>(record.method_topics||[]).some(topic=>topic.id===s.params.get('method')));
  if(q)records.sort((a,b)=>(normal(b.title).includes(normal(q))?1:0)-(normal(a.title).includes(normal(q))?1:0));
  return records;
 }
 function renderExperimentDirectory(s){
  const q=s.params.get('q')||'',records=filteredExperiments(s),groups=new Map();
  for(const record of records)for(const topic of record.method_topics||[]){if(!groups.has(topic.id))groups.set(topic.id,{id:topic.id,title:topic.title,records:new Set()});groups.get(topic.id).records.add(record.id)}
  const byMethod=s.params.get('view')==='methods'||(!s.params.get('view')&&!q&&!['method','family','guide'].some(key=>s.params.has(key)));
  const methods=[...groups.values()].sort((a,b)=>a.title.localeCompare(b.title)),items=byMethod?methods:records;
  const size=20,page=Math.min(Math.max(1,Number(s.params.get('page'))||1),Math.max(1,Math.ceil(items.length/size))),shown=items.slice((page-1)*size,page*size);
  const methodId=s.params.get('method'),method=methodId?data.experiments.flatMap(record=>record.method_topics||[]).find(topic=>topic.id===methodId):null;
  const family=s.params.get('family')?familyMembers(s.params.get('family'))[0]?.family:null,guide=data.guides.find(g=>g.id===s.params.get('guide'));
  const title=method?.title||family?.title||'Experiments',nav=directoryNav(s,true),subject=typeNames[s.params.get('type')]||'All experiment types';
  const modes=`<nav class="browse-modes" aria-label="Browse experiments"><a href="${url('experiments',edit(s.params,{view:'methods',method:null,family:null,guide:null,page:null}))}"${byMethod?' aria-current="page"':''}>Methods</a><a href="${url('experiments',edit(s.params,{view:'records',page:null}))}"${!byMethod?' aria-current="page"':''}>All experiments</a></nav>`;
  const breadcrumbs=method||family?crumb([['Research','research.html?v=record-panel-20261024#mode=list'],[method?'Method':'Family',null]]):'';
  main.innerHTML=`${breadcrumbs}<header class="page-title"><h1>${esc(title)}</h1></header><div class="directory-grid"><aside class="directory-nav" aria-label="Experiment types">${nav}</aside><div class="directory-content">${modes}${guide?`<p class="filter-note">Referenced in <a href="${guideHref(guide.id)}">${esc(guide.title)}</a>.</p>`:''}${family&&familyMembers(family.id).length>1?`<p class="filter-note"><a href="${familyHref(family.id)}">See related tests</a></p>`:''}<div class="result-meta"><button class="mobile-subject-button" data-categories>${esc(subject)}</button><span>${items.length} ${byMethod?'method':'experiment'}${items.length===1?'':'s'}</span>${q?`<a href="${esc(url('experiments',edit(s.params,{q:null,page:null})))}">Clear search</a>`:''}</div>${shown.length?shown.map(item=>byMethod?`<article class="list-row method-row"><h2><a href="${url('experiments',edit(s.params,{method:item.id,view:'records',page:null}))}">${esc(item.title)}</a></h2><span>${item.records.size} experiment${item.records.size===1?'':'s'}</span></article>`:experimentRow(item)).join(''):'<div class="empty"><h2>No matching records</h2><p>Try another phrase or clear the selected type. Missing search matches do not establish that an idea is untested.</p></div>'}${pagination(s,items.length,page,size)}</div></div>`;
  main.querySelector('[data-categories]')?.addEventListener('click',()=>{document.getElementById('contents-title').textContent='Experiment types';document.getElementById('mobile-contents').innerHTML=nav;contents.showModal()});
  finish(s,'experiments',title);
 }
 function renderDirectory(s,isExperiment){
  if(isExperiment){renderExperimentDirectory(s);return}
  const q=s.params.get('q')||'',category=categories().find(group=>group.id===s.params.get('category')),guide=data.guides.find(g=>g.id===s.params.get('guide'));
  let rows=isExperiment?data.experiments.filter(item=>queryMatch(item,q,true)):q?searchLibrary(data,q).guides.map(hit=>hit.guide):[...data.guides];
  if(!isExperiment&&category)rows=rows.filter(item=>item.category===category.title);
  if(isExperiment){if(s.params.get('type'))rows=rows.filter(item=>item.record_type?.id===s.params.get('type'));if(guide)rows=rows.filter(item=>guide.experiments.includes(item.id));if(s.params.get('family'))rows=rows.filter(item=>item.family?.id===s.params.get('family'));if(s.params.get('method'))rows=rows.filter(item=>(item.method_topics||[]).some(topic=>topic.id===s.params.get('method')))}
  if(q)rows.sort((a,b)=>(normal(b.title).includes(normal(q))?1:0)-(normal(a.title).includes(normal(q))?1:0));
  const size=20,page=Math.min(Math.max(1,Number(s.params.get('page'))||1),Math.max(1,Math.ceil(rows.length/size))),shown=rows.slice((page-1)*size,page*size),title=isExperiment?'Experiments':'Guides and methods';
  const nav=directoryNav(s,isExperiment),subject=isExperiment?(typeNames[s.params.get('type')]||'All experiments'):(category?.title||'All subjects');
  const family=s.params.get('family')?data.experiments.find(r=>r.family?.id===s.params.get('family'))?.family:null;
  main.innerHTML=`<header class="page-title"><h1>${title}</h1></header><div class="directory-grid"><aside class="directory-nav" aria-label="${isExperiment?'Experiment types':'Guide subjects'}">${nav}</aside><div class="directory-content">${guide?`<p class="filter-note">Experiments mentioned in <a href="${guideHref(guide.id)}">${esc(guide.title)}</a>.</p>`:family?`<p class="filter-note">${esc(family.title)} · <a href="research.html?v=record-panel-20261024#mode=list">All experiments</a></p>`:''}<div class="result-meta"><button class="mobile-subject-button" data-categories>${esc(subject)}</button><span>${rows.length} ${isExperiment?'experiment':'guide'}${rows.length===1?'':'s'}</span>${q?`<a href="${esc(url(s.path,edit(s.params,{q:null,page:null})))}">Clear search</a>`:''}</div>${shown.length?shown.map(item=>isExperiment?experimentRow(item):guideRow(item,!category)).join(''):'<div class="empty"><h2>No matching records</h2><p>Try another phrase or clear the filters. A missing search match does not establish that an idea is untested.</p></div>'}${pagination(s,rows.length,page,size)}</div></div>`;

  main.querySelector('[data-categories]')?.addEventListener('click',()=>{document.getElementById('contents-title').textContent=isExperiment?'Experiment types':'Guide subjects';document.getElementById('mobile-contents').innerHTML=nav;contents.showModal()});
  finish(s,isExperiment?'experiments':'guides',title);
 }
 async function renderGuide(s,run){
  const guide=data.guides.find(g=>g.id===s.parts[1]);if(!guide)throw Error('This guide could not be found.');
  const original=await load(guideSource(guide));const html=prepareAuthored(original,guide.id);if(run!==version)return;
  guide.experiments=referencedRecords(html,new Set(data.experiments.map(r=>r.id)));
  const doc=new DOMParser().parseFromString(html,'text/html'),headings=[...doc.querySelectorAll('h2[id],h3[id]')];
  const toc=headings.map(h=>`<a${h.tagName==='H3'?' class="subsection"':''} href="${url('guide/'+guide.id,{section:h.id})}">${esc(h.textContent)}</a>`).join('');
  const category=categories().find(c=>c.title===guide.category);
  main.innerHTML=`${crumb([['Guides','#/guides'],[guide.category,url('guides',{category:category?.id})]])}<header class="article-header"><h1>${esc(guide.title)}</h1><p class="summary">${esc(guide.summary)}</p><div class="article-actions"><button class="contents-trigger" data-contents>On this page</button>${guide.experiments.length?`<button data-references>Referenced research</button>`:''}<a href="reference/articles/${guide.id}.txt" download>Text version</a></div></header><div class="article-grid"><article class="prose">${html}</article><aside class="contents-rail" aria-label="Article contents"><strong>On this page</strong>${toc}</aside></div>`;
  document.getElementById('contents-title').textContent='On this page';document.getElementById('mobile-contents').innerHTML=toc;
  main.querySelector('[data-contents]')?.addEventListener('click',()=>contents.showModal());main.querySelector('[data-references]')?.addEventListener('click',()=>{document.getElementById('files-title').textContent='Research referenced in this guide';document.getElementById('file-inventory').innerHTML='<nav>'+guide.experiments.map(id=>{const r=data.experiments.find(r=>r.id===id);return '<p><a href="'+experimentHref(id)+'">'+esc(globalThis.RecordTestView?.title(r)||r.title)+'</a></p>'}).join('')+'</nav>';filesDialog.showModal()});
  enhanceReading();bindCodeTools();finish(s,'guides',guide.title);if(window.LibraryGuides){const article=main.querySelector('.article-grid');window.LibraryGuides.bind(article,{isCurrent:()=>article.isConnected}).catch(()=>{});}
 }
 function renderFileInventory(record){document.getElementById('files-title').textContent='Files and checksums';document.getElementById('file-inventory').innerHTML=recordFiles(record).map(file=>`<div class="inventory-row"><a href="${esc(recordFileHref(file))}" download>${esc(file.path)}</a>${file.sha256?`<code>SHA-256 ${esc(file.sha256)}</code>`:''}</div>`).join('');filesDialog.showModal()}
 function renderPageInventory(record){document.getElementById('files-title').textContent='Pages in this experiment';document.getElementById('file-inventory').innerHTML='<nav class="page-grid" aria-label="Declared manuscript pages">'+record.scope.pages.map(page=>`<a href="reader.html#${page}">${page.toUpperCase()}</a>`).join('')+'</nav>';filesDialog.showModal()}
 function overview(record){
  const files=recordFiles(record).map(f=>f.path),sections=readerSections(record.article||'',record.reader_sections),limit=readerLimit(record.reader_limit||record.limitations),remaining=readerLimit(record.next_steps||record.reader_limit||record.limitations);
  const questions=globalThis.RecordQuestionView?globalThis.RecordQuestionView.render(record,{headingLevel:2,fallback:remaining}):remaining?`<section id="experiment-remaining"><h2>What remains open</h2><p>${esc(remaining)}</p></section>`:'',live=questions.includes('data-live-question=');
  const completeQuestions=globalThis.PinnedQuestionEntry?.render?.(record,{headingLevel:2})||'';
  const questionCount=globalThis.RecordQuestionView?.questions?.(record)?.length||0,questionJump=questionCount?`<p><a href="${esc(url('experiment/'+record.id,{section:'experiment-remaining'}))}">Questions to explore (${questionCount})</a></p>`:'';
  const followups=globalThis.RecordQuestionView?.coversFollowups(record)?'':globalThis.RecordFollowupView?.render(record,{headingLevel:2,selectId:'library-followup-setting'})||'',secondary=live&&followups?`<details class="other-prepared-checks"><summary>Other prepared checks</summary>${followups}</details>`:followups;
  return `${record.reader_intro?'':globalThis.RecordTestView?.render(record,{headingLevel:2})||''}<div class="finding" id="experiment-finding">${esc(record.reader_finding||record.finding)}</div>${limit?`<p><strong>Limit:</strong> ${esc(limit)}</p>`:''}${completeQuestions}${questionJump}${hasInteractive(record)?`<p><a href="index.html#/experiments/${record.id}?full=1">Open the interactive figure</a></p>`:''}${(record.visuals||[]).map(v=>`<figure class="source-visual"><img src="${esc(v.path)}" alt="${esc(v.caption)}" loading="lazy"><figcaption>${esc(v.caption)}</figcaption></figure>`).join('')}${record.reader_intro?globalThis.RecordTestView?.render(record,{headingLevel:2})||'':''}<div id="record-saved-calculations"></div>${live?questions:''}${secondary}<div class="reader-sections">${sections.selected.map(s=>`<section><h2>${esc(s.title)}</h2>${prepareAuthored(renderExperimentMarkdown(s.body,files,recordArticleLinks(record),(record.visuals||[]).map(v=>v.path)))}</section>`).join('')}</div>${live?'':questions}<div class="actions" id="experiment-family"><a class="primary-link" href="${experimentHref(record.id,'reproduce')}">Reproduce this test</a>${record.family&&familyMembers(record.family.id).length>1?`<a href="${familyHref(record.family.id,{from:record.id})}">See related tests</a>`:''}</div>`;
 }
 function scope(record){return `<dl class="scope-list"><div><dt>Question</dt><dd>${esc(record.question)}</dd></div><div><dt>Pages</dt><dd>${esc(compactPages(record.scope.pages))}${record.pages_note?'<p>'+esc(record.pages_note)+'</p>':''}${record.scope.pages.length?`<br><button data-pages>View all ${record.scope.pages.length} pages</button>`:''}</dd></div>${record.scope.artifacts?.length?'<div><dt>Files or objects</dt><dd><ul>'+record.scope.artifacts.map(p=>'<li>'+esc(p)+'</li>').join('')+'</ul></dd></div>':''}${[['Input','representation'],['Method','procedure'],['Bounds','parameters'],['Not tested','exclusions']].map(([label,key])=>`<div><dt id="experiment-${key==='representation'?'input':key==='parameters'?'bounds':key}">${label}</dt><dd>${esc(record.scope[key])}</dd></div>`).join('')}${readerLimit(record.limitations)?`<div><dt id="experiment-limitations">Limitations</dt><dd>${esc(readerLimit(record.limitations))}</dd></div>`:''}</dl>`}
 function reproduction(record){const files=recordFiles(record),primary=files.filter(file=>/\/(plan\.json|check\.py|results\.json)$/.test(file.path));const images=record.reproduction.inputs.some(file=>/^(images\/|exports\/sources\/)/.test(file.path));return `<h2 id="experiment-reproduce">Reproduction files</h2><div class="actions"><a class="primary-link" href="downloads/experiments/${record.id}.zip" download>Experiment ZIP</a><a href="downloads/reference-data.zip" download>Reference data</a>${images?'<a href="downloads/original-images.zip" download>Original images</a>':''}</div><p>${esc(record.reproduction.environment)}</p>${images?'<p>Original image inputs are separate. Extract the image bundle into the same folder.</p>':''}<div class="code-tools"><span>Run from the extracted project folder</span><button data-copy-command>Copy command</button></div><pre id="reproduction-command" tabindex="0">${esc(record.reproduction.command)}</pre><div class="file-links">${primary.map(file=>`<a href="${esc(recordFileHref(file))}" download>${esc(file.path.split('/').at(-1))}</a>`).join('')}</div><div class="actions"><button class="quiet-button" data-files>All files and checksums (${files.length})</button><a href="${guideHref('running-scripts')}">Script setup guide</a></div>`}
 function sources(record){return `<h2 id="experiment-sources">Sources and review</h2><p>${esc(record.review?.reviewer||'See the recorded review details.')}${record.review?.retested_on?' · '+esc(record.review.retested_on):''}</p><ul class="source-list">${(record.sources||[]).map(source=>`<li><a href="${esc(rewriteHref(source.url))}">${esc(source.label||source.url)}</a></li>`).join('')}</ul><div class="record-related"><a href="experiments/records/${record.id}/record.json">Original structured record</a><a href="${esc(record.article_path||'experiments/records/'+record.id+'/article.md')}">Full authored Markdown</a><a href="index.html#/experiments/${record.id}?full=1">Original experiment page and specialist figures</a></div>`}
 async function renderExperiment(s,run){
  const id=s.parts[1];if(!data.experiments.some(record=>record.id===id))throw Error('This experiment could not be found.');
  const record=await load(`reference/experiments/${id}.json`);if(run!==version)return;currentRecord=record;if(record.id!==id||record.status!=='published')throw Error('This published record is unavailable.');
  const tabs={overview:'Finding',scope:'Scope',reproduce:'Reproduce',analysis:'Analysis',sources:'Sources'};const tab=Object.hasOwn(tabs,s.params.get('tab'))?s.params.get('tab'):'overview';
  const review=[record.record_type?.label,record.review?.retested_on?'Checked '+record.review.retested_on:''].filter(Boolean).join(' · ');
  let content;
  if(tab==='overview')content=overview(record);else if(tab==='scope')content=scope(record);else if(tab==='reproduce')content=reproduction(record);else if(tab==='sources')content=sources(record);else{const files=recordFiles(record).map(file=>file.path);content=prepareAuthored(renderExperimentMarkdown(readerSections(record.article||'',record.reader_sections).remaining.replace(/^#[^\n]+\n/,''),files,recordArticleLinks(record)))}
  main.innerHTML=`${crumb([['Research','research.html?v=record-panel-20261024#mode=list'],...(record.family?[[record.family.title,url('experiments',{family:record.family.id})]]:[])])}<header class="article-header experiment-header"><h1>${esc(globalThis.RecordTestView?.title(record)||record.title)}</h1>${globalThis.RecordTestView?.renderIntro(record)||''}<div class="record-meta">${esc(outcomeNames[record.outcome]||record.outcome)}</div><div data-record-reactions></div></header><nav class="record-tabs" aria-label="Experiment sections">${Object.entries(tabs).map(([key,label])=>`<a href="${experimentHref(id,key)}"${key===tab?' aria-current="page"':''}>${label}</a>`).join('')}</nav><section class="record-panel prose" aria-label="${tabs[tab]}">${tab==='sources'?`<p class="small">${esc(review)}</p>`:''}${content}</section>`;
  reactionMount=reactions?.mount(main.querySelector('[data-record-reactions]'),record.id)||null;
  if(tab==='overview'){globalThis.RecordFollowupView?.bind(main,record);questionMount=globalThis.RecordQuestionView?.mount?.(main,record);const holder=main.querySelector('#record-saved-calculations');if(holder&&globalThis.PublishedProgramDiscovery?.hasRecord?.(record.id))publishedDiscoveryMount=globalThis.PublishedProgramDiscovery?.mount?.(holder,{recordId:record.id,isLive:()=>run===version});}
  main.querySelector('[data-files]')?.addEventListener('click',()=>renderFileInventory(record));main.querySelector('[data-pages]')?.addEventListener('click',()=>renderPageInventory(record));
  main.querySelector('[data-copy-command]')?.addEventListener('click',async event=>{try{await navigator.clipboard.writeText(record.reproduction.command);event.target.textContent='Copied'}catch{event.target.textContent='Select the command to copy'}});
  const changingTab=current?.path===s.path;
  bindCodeTools();finish(s,'experiments',globalThis.RecordTestView?.title(record)||record.title);
  const tabBar=main.querySelector('.record-tabs'),active=tabBar.querySelector('[aria-current]');
  tabBar.scrollLeft=active.offsetLeft-tabBar.offsetLeft-24;
  if(changingTab&&!positions.has(currentEntry)&&!s.params.has('section')){active.focus({preventScroll:true});tabBar.scrollIntoView({block:'start'})}
 }
 async function renderFamily(s,run){
  const members=familyMembers(s.parts[1]);if(!members.length)throw Error('These related tests could not be found.');
  const family=members[0].family,ordered=members.slice().sort((a,b)=>Number(b.id===family.baseline)-Number(a.id===family.baseline)),records=await Promise.all(ordered.map(record=>load(`reference/experiments/${record.id}.json`)));if(run!==version)return;
  const from=s.params.get('from'),currentId=members.some(record=>record.id===from)?from:null;
  const tests=records.map(record=>{
   const title=globalThis.RecordTestView?.title(record)||record.reader_title||record.title,test=globalThis.RecordTestView?.valid(record.reader_test)?record.reader_test:null,tried=test?.action||record.scope?.procedure,checked=test?.check,finding=record.reader_finding||record.finding,limit=readerLimit(record.reader_limit||record.limitations),current=record.id===currentId;
   return `<article class="related-test" id="related-test-${esc(record.id)}" aria-labelledby="related-test-title-${esc(record.id)}"${current?' data-current-test':''}><div class="related-test-meta">${current?'<span class="related-test-current">Current test</span>':''}<span>${esc(compactPages(record.scope?.pages||record.pages||[]))}</span></div><h2 id="related-test-title-${esc(record.id)}">${esc(title)}</h2>${finding?`<p class="related-test-finding"><strong>Result</strong> ${esc(finding)}</p>`:''}${tried||checked?`<dl class="related-test-method">${tried?`<div><dt>What was tried</dt><dd>${esc(tried)}</dd></div>`:''}${checked?`<div><dt>What was checked</dt><dd>${esc(checked)}</dd></div>`:''}</dl>`:''}${limit&&limit!==finding?`<p class="related-test-limit"><strong>Limit:</strong> ${esc(limit)}</p>`:''}<a class="related-test-open" href="${experimentHref(record.id)}">Open test<span class="sr-only">: ${esc(title)}</span></a></article>`;
  }).join('');
  main.innerHTML=`${crumb([['Research','research.html?v=record-panel-20261024#mode=list'],['Related tests',null]])}<header class="article-header related-tests-header"><h1>${esc(family.title)}</h1>${family.question&&family.question!==family.title?`<p class="summary">${esc(family.question)}</p>`:''}</header><section class="related-tests" aria-label="Published tests">${tests}</section>`;
  finish(s,'experiments',family.title);
 }
 function enhanceReading(){
  main.querySelectorAll('.prose pre').forEach(pre=>{
   if(pre.closest('.copyable-block')||pre.id==='reproduction-command')return;
   const block=document.createElement('div');block.className='copyable-block reading-code';
   pre.before(block);block.innerHTML='<div class="block-tools"><button data-wrap-block aria-pressed="false">Wrap</button><button data-copy-block aria-live="polite">Copy</button></div>';block.append(pre);pre.tabIndex=0;
  });
 }
 function bindCodeTools(){main.querySelectorAll('[data-copy-block]').forEach(button=>button.onclick=async()=>{try{await navigator.clipboard.writeText(button.closest('.copyable-block').querySelector('pre').textContent);button.textContent='Copied'}catch{button.textContent='Select text to copy'}});main.querySelectorAll('[data-wrap-block]').forEach(button=>button.onclick=()=>{const pre=button.closest('.copyable-block').querySelector('pre'),wrap=button.getAttribute('aria-pressed')!=='true';button.setAttribute('aria-pressed',String(wrap));pre.style.whiteSpace=wrap?'pre-wrap':'pre'})}
 function renderSearch(s){const q=s.params.get('q')||'',matches=searchLibrary(data,q),guides=matches.guides,experiments=matches.experiments;main.innerHTML=`<header class="page-title"><h1>Search results</h1><p>${esc(q)}</p></header><div class="record-panel"><p><a href="${esc(researchHref({q}))}">Search saved ideas in Research map</a>. <span class="small">Includes loaded ideas.</span></p><h2>Guides · ${guides.length}</h2>${guides.slice(0,8).map(hit=>`<article class="list-row"><h3><a href="${esc(hit.href)}">${esc(hit.title)}</a></h3><p>${esc(hit.text)}</p><div class="row-meta"><span>Guide</span><span>${esc(hit.guide.category)}</span></div></article>`).join('')}${guides.length>8?`<a href="${url('guides',{q})}">All matching guides</a>`:''}<h2 style="margin-top:36px">Published research · ${experiments.length}</h2>${experiments.slice(0,8).map(record=>experimentRow(record,3)).join('')}${experiments.length>8?`<a href="${researchHref({q})}">All matching published records</a>`:''}${!guides.length&&!experiments.length?'<p>No matching guides or published records. Try another phrase.</p>':''}</div>`;finish(s,'','Search results')}
 async function render(){const run=++version,s=state();if(s.parts[0]==='experiments'){location.replace(researchHref(Object.fromEntries(s.params)));return;}if(s.parts[0]==='experiment'&&!s.params.has('tab')){const tab=sectionTab(s.params.get('section'));if(tab)s.params.set('tab',tab);}if(current?.path===s.path&&s.parts[0]==='guide'){current=s;currentHash=location.hash;currentEntry=entryKey();const saved=positions.get(currentEntry);if(saved)queuePosition(()=>restorePosition(saved));else queuePosition(()=>jump(s.params.get('section')));return}questionMount?.destroy();questionMount=null;publishedDiscoveryMount?.destroy();publishedDiscoveryMount=null;reactionMount?.();reactionMount=null;try{
   if(!data){const [guides,categories,index]=await Promise.all([load('data/article-search.json'),load('data/guide-categories.json'),load('data/experiment-index.json')]);data=adaptMetadata(guides,categories,index);}if(run!==version)return;
   if(s.parts[0]==='guide')await renderGuide(s,run);else if(s.parts[0]==='experiment')await renderExperiment(s,run);else if(s.parts[0]==='family')await renderFamily(s,run);else if(s.parts[0]==='search')renderSearch(s);else renderDirectory({...s,path:s.parts[0]==='experiments'?'experiments':'guides'},s.parts[0]==='experiments');
  }catch(error){if(run!==version)return;current=null;currentRecord=null;headerActive(s.parts[0]==='guide'?'guides':'experiments');document.title='Page unavailable · Liberpedia';main.innerHTML=`<div class="error-message"><h1>Page unavailable</h1><p>${esc(error.message)}</p><button id="retry">Retry</button> · <a href="#/guides">Guides</a> · <a href="research.html?v=record-panel-20261024#mode=list">Experiments</a></div>`;document.getElementById('retry').onclick=render;window.scrollTo(0,0);main.focus()}}
 document.querySelectorAll('[data-close-dialog]').forEach(button=>button.onclick=()=>button.closest('dialog').close());
 document.addEventListener('click',event=>{const anchor=event.target.closest('a');if(!anchor||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button!==0)return;const href=anchor.getAttribute('href');if(href==='#main'){event.preventDefault();main.focus({preventScroll:true});main.scrollIntoView({block:'start'});return;}if(href?.startsWith('#/')){savePosition(true,anchor);if(contents.open)contents.close();if(filesDialog.open)filesDialog.close()}});
 const searchForm=document.getElementById('global-search');if(searchForm)searchForm.onsubmit=event=>{event.preventDefault();const q=document.getElementById('global-query').value.trim();if(!q)return;const s=state();savePosition(true);location.hash=url('search',{q})};
 let scrollFrame=0;window.addEventListener('scroll',()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(()=>{scrollFrame=0;savePosition()})},{passive:true});
 window.addEventListener('popstate',()=>savePosition(true));

 window.addEventListener('hashchange',render);render();
})();
