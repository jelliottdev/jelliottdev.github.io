/* Published research directory. Filtering never implies that an idea was tested. */
(function(root){
  const search=typeof module!=='undefined'?require('./search-engine.js'):root.WikiSearch;
  const labels={method:'Solving tests',replay:'Method replays',measurement:'Measurements',control:'Controls',
    alphabet:'Alphabet analyses',audit:'Source audits',historical:'Historical reproductions'};
  const outcomes={supported:'Supported within scope','not-supported':'Not supported within scope',inconclusive:'Inconclusive'};
  const pageSize=20,positions=new Map(),historyEntries=new Set();
  const historyKey='__liberpediaResearchEntry',historyPrefix=Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
  let historySequence=0;
  const collator=new Intl.Collator('en',{numeric:true,sensitivity:'base'});
  const topicLabels={feedback:'Feedback and autokey',seeded:'Seeded keys',radix:'Number bases',sums:'Gematria and sums',
    provenance:'Sources and transcription',repetition:'Repeats and doublets',polyalphabetic:'Polyalphabetic ciphers',
    cribs:'Cribs and known plaintext',blocks:'Block and matrix ciphers',distributions:'Frequency and distribution',
    'number-streams':'Numerical key streams','cryptographic-artifacts':'Public-key cryptography'};
  const topicId=topic=>typeof topic==='string'?topic:topic?.id;
  const topicLabel=id=>topicLabels[id]||id.replace(/-/g,' ').replace(/^./,letter=>letter.toUpperCase());
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function state(params=new URLSearchParams()){
    return {q:(params.get('q')||'').trim().slice(0,300),
      type:Object.hasOwn(labels,params.get('type'))?params.get('type'):'',
      method:(params.get('method')||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,120),
      family:(params.get('family')||'').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,120),
      outcome:Object.hasOwn(outcomes,params.get('outcome'))?params.get('outcome'):'',
      sort:['title','title-desc','recent'].includes(params.get('sort'))?params.get('sort'):'title',
      page:Math.max(1,Math.min(100000,Number.parseInt(params.get('page'),10)||1))};
  }
  function href(value){
    const params=new URLSearchParams();
    for(const key of ['q','type','method','family','outcome'])if(value[key])params.set(key,value[key]);
    if(value.sort&&value.sort!=='title')params.set('sort',value.sort);
    if(value.page>1)params.set('page',String(value.page));
    return '#/research'+(params.size?'?'+params:'');
  }
  function legacyHref(hash){
    const [path,query='']=String(hash).split('?');
    if(path!=='#/experiments')return null;
    const params=new URLSearchParams(query);
    if(!params.has('browse')&&params.get('section')!=='browse-experiments')return null;
    params.set('q',params.get('browse')||params.get('q')||'');
    return href(state(params));
  }
  function pageQuery(query){
    const pages=[];
    const text=query.replace(/\blp\s*([12])(?:[\s:·\-‐‑–—−]*pages?\s*)?[\s:#·\-‐‑–—−]*(\d{1,2})(?:\s*[‐‑–—−-]\s*(?:lp\s*\1(?:[\s:·\-‐‑–—−]*pages?\s*)?[\s:#·\-‐‑–—−]*)?(\d{1,2}))?\b/gi,(_,release,start,end)=>{
      const a=Number(start),b=end===undefined?a:Number(end);
      for(let n=Math.min(a,b);n<=Math.max(a,b);n++)pages.push(`lp${release}-${String(n).padStart(2,'0')}`);
      return ' ';
    }).trim();
    return {text,pages:[...new Set(pages)]};
  }
  function recordText(record){
    const pages=(record.scope?.pages||[]).flatMap(id=>[id,`${id.slice(0,3)} page ${Number(id.slice(4))}`]);
    return [record.title,record.summary,record.reader_finding||record.finding,record.family?.title,
      ...(record.tags||[]),...(record.method_topics||[]).flatMap(topic=>[topicId(topic),topic?.title,...(topic?.aliases||[])]),...pages].join(' ');
  }
  function detailFields(record){
    return [
      ['Input',record.scope?.representation,'experiment-input'],
      ['Method',record.scope?.procedure,'experiment-procedure'],
      ['Bounds',record.scope?.parameters,'experiment-bounds'],
      ['Not tested',record.scope?.exclusions,'experiment-exclusions'],
      ['Limitations',record.limitations,'experiment-limitations']
    ].filter(([,text])=>typeof text==='string'&&text.trim());
  }
  function matchingDetails(record,query){
    if(!query||search.has(recordText(record),query))return [];
    const fields=detailFields(record),whole=fields.filter(([,text])=>search.has(text,query));
    if(whole.length)return whole.slice(0,2);
    const terms=search.terms(query);
    return fields.filter(([,text])=>terms.some(term=>search.has(text,term))).slice(0,2);
  }
  function matchExcerpt(text,query){
    text=String(text||'').replace(/\s+/g,' ').trim();
    const words=search.terms(query),tokens=[...text.matchAll(/\S+/g)];
    const first=tokens.find(token=>words.some(word=>search.norm(token[0]).includes(word)));
    // Cut at a word boundary, leaving enough context to retain qualifiers such as "excluded".
    const start=first?Math.max(0,first.index-75):0;
    const from=start?text.lastIndexOf(' ',start)+1:0;
    return (from?'…':'')+excerpt(text.slice(from));
  }
  const checked=record=>/^\d{4}-\d{2}-\d{2}$/.test(record.review?.retested_on||'')?record.review.retested_on:'';
  function select(records,requested){
    const value={...requested},query=pageQuery(value.q||'');
    const families=new Map(records.filter(r=>r.family).map(r=>[r.family.id,r.family.title]));
    const topics=new Map();
    for(const record of records)for(const topic of record.method_topics||[]){
      const id=topicId(topic);if(id)topics.set(id,typeof topic?.title==='string'&&topic.title.trim()?topic.title:topics.get(id)||topicLabel(id));
    }
    if(value.family&&!families.has(value.family))value.family='';
    if(value.method&&!topics.has(value.method))value.method='';
    const matches=records.filter(record=>(!value.type||record.record_type?.id===value.type)&&
      (!value.method||(record.method_topics||[]).some(topic=>topicId(topic)===value.method))&&
      (!value.family||record.family?.id===value.family)&&(!value.outcome||record.outcome===value.outcome)&&
      query.pages.every(id=>(record.scope?.pages||[]).includes(id))&&search.has([recordText(record),...detailFields(record).map(([,text])=>text)].join(' '),query.text));
    const byTitle=(a,b)=>collator.compare(a.title,b.title)||a.id.localeCompare(b.id);
    matches.sort((a,b)=>value.sort==='recent'?
      (checked(a)&&checked(b)?checked(b).localeCompare(checked(a)):checked(a)?-1:checked(b)?1:0)||byTitle(a,b):
      value.sort==='title-desc'?-byTitle(a,b):byTitle(a,b));
    const pages=Math.max(1,Math.ceil(matches.length/pageSize));value.page=Math.min(value.page,pages);
    const start=(value.page-1)*pageSize;
    return {state:value,total:matches.length,pages,start,records:matches.slice(start,start+pageSize),families,topics};
  }
  function pageLabel(record){
    const pages=record.scope?.pages||[];
    if(!pages.length)return record.scope?.artifacts?.length?'Source files':'Page scope not recorded';
    if(pages.length===1)return pages[0].toUpperCase();
    const first=pages[0],last=pages.at(-1);
    const contiguous=pages.every((id,n)=>id.slice(0,3)===first.slice(0,3)&&Number(id.slice(4))===Number(first.slice(4))+n);
    return contiguous?`${first.toUpperCase()}–${last.slice(4)}`:`${pages.length} manuscript pages`;
  }
  function excerpt(text){
    text=String(text||'').replace(/\s+/g,' ').trim();
    if(text.length<=240)return text;
    const clipped=text.slice(0,237);return clipped.slice(0,Math.max(180,clipped.lastIndexOf(' ')))+'…';
  }
  function pagination(result){
    if(result.pages<2)return '';
    const value=result.state,numbers=[...new Set([1,value.page-1,value.page,value.page+1,result.pages])]
      .filter(n=>n>0&&n<=result.pages).sort((a,b)=>a-b);
    const pageLink=(page,label,extra='')=>`<a href="${esc(href({...value,page}))}" ${extra}>${label}</a>`;
    return '<nav class="research-pagination" aria-label="Research result pages">'+
      (value.page>1?pageLink(value.page-1,'Previous','rel="prev"'):'')+
      numbers.map((n,i)=>(i&&n>numbers[i-1]+1?'<span aria-hidden="true">…</span>':'')+
        (n===value.page?`<span aria-current="page" aria-label="Page ${n}">${n}</span>`:pageLink(n,String(n),`aria-label="Page ${n}"`))).join('')+
      (value.page<result.pages?pageLink(value.page+1,'Next','rel="next"'):'')+'</nav>';
  }
  function results(result){
    if(!result.total)return '<div class="empty research-empty"><h2>No matching research</h2><p>No record matches this combination of search terms and filters. Try fewer terms or clear the filters.</p></div>';
    return `<ol class="research-records" start="${result.start+1}">${result.records.map(record=>{
      const date=checked(record),recent=result.state.sort==='recent'&&date;
      const query=pageQuery(result.state.q||'').text,details=matchingDetails(record,query);
      return `<li><article class="research-record"><h2><a href="#/experiments/${esc(record.id)}">${esc(record.title)}</a></h2>
        <p class="research-record-meta">${esc(record.record_type?.label||'Research record')} · ${esc(pageLabel(record))} · ${esc(outcomes[record.outcome]||'Finding not classified')}${recent?' · Checked '+esc(date):''}</p>
        <p class="research-record-finding">${esc(excerpt(record.reader_finding||record.finding))}</p>
        ${details.map(([label,text,section])=>`<p class="research-match"><a href="#/experiments/${esc(record.id)}?section=${section}">${label==='Not tested'?'Mentioned under “Not tested”':'Matches '+esc(label.toLowerCase())}</a>: ${esc(matchExcerpt(text,query))}</p>`).join('')}
        ${record.family&&result.state.family!==record.family.id?`<a class="research-family-link" href="${esc(href({family:record.family.id,page:1}))}">More in ${esc(record.family.title)}</a>`:''}
      </article></li>`;
    }).join('')}</ol>${pagination(result)}`;
  }
  function filters(result){
    const value=result.state;
    const options=(items,chosen)=>items.map(([key,label])=>`<option value="${esc(key)}"${key===chosen?' selected':''}>${esc(label)}</option>`).join('');
    return `<form id="research-filters" class="research-filters" role="search" aria-label="Filter published research">
      <div class="research-query"><label for="research-query">Find research</label><input id="research-query" name="q" type="search" maxlength="300" placeholder="Method, page or result" value="${esc(value.q)}" autocomplete="off"></div>
      <div><label for="research-type">Record type</label><select id="research-type" name="type">${options([['','All research'],...Object.entries(labels)],value.type)}</select></div>
      <div><label for="research-method">Method</label><select id="research-method" name="method">${options([['','All methods'],...[...result.topics].sort((a,b)=>collator.compare(a[1],b[1]))],value.method)}</select></div>
      <div><label for="research-outcome">Finding</label><select id="research-outcome" name="outcome">${options([['','Any finding'],...Object.entries(outcomes)],value.outcome)}</select></div>
      <div><label for="research-sort">Sort</label><select id="research-sort" name="sort">${options([['title','Title A–Z'],['title-desc','Title Z–A'],['recent','Recently checked']],value.sort)}</select></div>
    </form>`;
  }
  function summary(result){
    return result.total?`${result.start+1}–${result.start+result.records.length} of ${result.total} records`:'0 matching records';
  }
  function familyContext(result){
    const value=result.state;
    return value.family?`Related test group: <strong>${esc(result.families.get(value.family))}</strong> · <a href="${esc(href({...value,family:'',page:1}))}">Clear group</a>`:'';
  }
  function remember(container,top){
    const index=container.querySelector('.research-index'),key=index?.dataset?.researchState;
    if(!key||!Number.isFinite(top))return;
    const active=container.ownerDocument?.activeElement,link=active?.closest?.('.research-record h2 a');
    const href=link&&index.contains?.(link)?link.getAttribute('href'):null;
    if(positions.size>=50&&!positions.has(key))positions.delete(positions.keys().next().value);
    positions.set(key,{top,focusHref:href&&/^#\/experiments\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(href)?href:null});
  }
  function position(container){return positions.get(container.querySelector('.research-index')?.dataset?.researchState)?.top??null;}
  function restoreHistoryFocus(container,history){
    const index=container.querySelector('.research-index'),key=index?.dataset?.researchState;
    if(!key||typeof history?.replaceState!=='function')return false;
    const state=history.state;
    if(state!==null&&state!==undefined&&(typeof state!=='object'||Array.isArray(state)))return false;
    const token=state?.[historyKey];
    if(typeof token==='string'&&historyEntries.has(token)){
      const href=positions.get(key)?.focusHref;
      const target=href?[...index.querySelectorAll('.research-record h2 a')].find(link=>link.getAttribute('href')===href):null;
      if(!target?.isConnected)return false;
      target.focus({preventScroll:true});return true;
    }
    // New fragment entries have no classic History state; Back/Forward restores it.
    const fresh=historyPrefix+'-'+(++historySequence);
    try{history.replaceState({...state,[historyKey]:fresh},'');}
    catch{return false;}
    if(historyEntries.size>=100)historyEntries.delete(historyEntries.values().next().value);
    historyEntries.add(fresh);return false;
  }
  const api={labels,outcomes,pageSize,state,href,legacyHref,pageQuery,select,results,filters,summary,familyContext,remember,position,restoreHistoryFocus};
  if(typeof module!=='undefined')module.exports=api;else root.ResearchIndex=api;
})(globalThis);
