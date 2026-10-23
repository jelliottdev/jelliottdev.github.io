/* Shared browser/Worker retrieval. Page IDs are exact; prose uses lexical ranking. */
(function(root) {
  const stop = new Set('a an the is it this that to of for on in with and or we i have has had tried try could would can does do what if using use how why are was were about explain compare please page pages test tests tested testing technique method any anyone already every all been done applying apply row rows line lines input inputs data manuscript rune runes result results one each'.split(' '));
  for(const word of ['its','than','be','checking','check','whether','know'])stop.add(word);
  const aliases={languages:'language',primes:'prime',emirps:'emirp',reversal:'reverse',reversing:'reverse',reversed:'reverse',shifts:'shift',shifted:'shift',shifting:'shift'};
  const pageReference=/\blp\s*([12])(?:[\s:\-‐‑–—−]*page\s*)?[\s:#\-‐‑–—−]*(\d{1,2})\b/gi;
  const wordIndex=new WeakMap();
  const tokens = text => (String(text).normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(t=>!stop.has(t)).map(t=>aliases[t]||t);
  function pageIds(text) {
    return [...new Set([...text.matchAll(pageReference)]
      .map(m=>`lp${m[1]}-${m[2].padStart(2,'0')}`))];
  }
  function experimentDocs(records) {
    return records.filter(r=>r.status==='published').map(r=>({
      id:r.id, title:r.title, kind:'experiment', recordType:r.record_type?.id||'method', href:`#/experiments/${r.id}`,
      text:JSON.stringify({record_type:r.record_type,question:r.question,family:r.family,variant:r.variant,scope:r.scope,outcome:r.outcome,finding:r.finding,limitations:r.limitations}),
      // Retrieval can use prose, but evidence always preserves the complete scope.
      keywords:[r.summary,...(r.tags||[]),r.article||''].join(' '),
      phrases:r.tags||[],
      // Authored metadata ranks a named method; it is not evidence of a test.
      retrieval:{question:r.question||'',summary:r.summary||'',tags:r.tags||[],topics:r.method_topics||[]}
    }));
  }
  function techniqueQuery(query) {
    return query.replace(pageReference,' ').replace(/\bpages?\s*#?\s*\d+(?:\s*[-‐‑–—−]\s*#?\s*\d+)?/gi,' ');
  }
  function search(documents, query, pages=[]) {
    const terms=[...new Set(tokens(query))], explicit=[...new Set([...pages,...pageIds(query)])];
    const corpus=documents.map(document=>{
      let index=wordIndex.get(document);
      if(!index){
        const words=tokens(document.title+' '+document.title+' '+document.text+' '+(document.keywords||''));
        const counts=new Map();
        for(const word of words)counts.set(word,(counts.get(word)||0)+1);
        index={length:words.length,counts};wordIndex.set(document,index);
      }
      return {document,index};
    });
    const avg=corpus.reduce((sum,d)=>sum+d.index.length,0)/(corpus.length||1)||1;
    const df=new Map(terms.map(term=>[term,corpus.filter(d=>d.index.counts.has(term)).length]));
    const queryPhrase=' '+tokens(query).join(' ')+' ';
    return corpus.map(({document,index})=>{
      let score=0,matched=[];
      for(const term of terms){const n=index.counts.get(term)||0;if(!n)continue;matched.push(term);
        score+=Math.log(1+(corpus.length-df.get(term)+.5)/(df.get(term)+.5))*n*2.2/(n+1.2*(.25+.75*index.length/avg));}
      // A complete authored technique phrase outranks incidental body mentions.
      // Use only the strongest phrase: duplicate/overlapping tags cannot stack.
      const phraseBoost=Math.max(0,...(document.phrases||[]).map(phrase=>{
        const parts=tokens(phrase);
        return parts.length>=1&&queryPhrase.includes(' '+parts.join(' ')+' ')?Math.min(6,parts.length*2):0;
      }));
      score+=phraseBoost;
      const pinned=explicit.includes(document.page);
      if(pinned)score+=document.kind==='page'?100:20;
      // Bare generic words must not send arbitrary manuscript metadata to inference.
      return {document,score,matched,pinned};
    }).filter(r=>r.score>0).sort((a,b)=>b.score-a.score||a.document.id.localeCompare(b.document.id));
  }
  function lexicalSelect(documents,query,pages=[]) {
    // Include measurement and control records as evidence of what was measured.
    // Their record type remains explicit so inference cannot call them solve attempts.
    const all=rankedRecords(documents,query,pages);
    const ranked=all.filter(r=>r.score>=Math.max(.5,(all[0]?.score||0)*.62) &&
      (!r.document.recordType||['method','replay','measurement','control'].includes(r.document.recordType)));
    // A source audit belongs in comparison context only when its match is
    // substantially stronger than any selectable test or measurement AND the
    // query names more than a shared subject. This keeps a bare artwork/page
    // mention from becoming evidence of a solving experiment.
    const audit=all.find(r=>r.document.recordType==='audit');
    const auditQuestion=new Set(tokens(audit?.document.retrieval?.question||''));
    const auditTitle=new Set(tokens([audit?.document.title,...(audit?.document.retrieval?.tags||[])].join(' ')));
    const auditTerms=[...new Set(tokens(techniqueQuery(query)))];
    const auditOverlap=auditTerms.filter(word=>auditQuestion.has(word)||auditTitle.has(word));
    const auditNamesOperation=auditOverlap.length>=2&&auditOverlap.some(word=>auditQuestion.has(word));
    if(audit&&auditNamesOperation&&audit.score>=Math.max(3,(ranked[0]?.score||0)*1.4)){
      ranked.push(audit);
      ranked.sort((a,b)=>b.score-a.score||a.document.id.localeCompare(b.document.id));
    }
    // A manuscript page match is never evidence that a technique was tested.
    if(!ranked.length)return [];
    const selected=[ranked[0].document];
    let size=selected[0].text.length;
    if(size>9000)return []; // Never replace an oversized best match with a weaker one.
    const second=ranked[1]?.document;
    if(second&&size+second.text.length<=9000){selected.push(second);size+=second.text.length;}
    // Keep the best complete scope when its sibling cannot fit; never truncate either.
    return addPageContext(selected,documents,query,pages,size);
  }
  function addPageContext(selected,documents,query,pages,size) {
    const explicit=[...new Set([...pages,...pageIds(query)])];
    let pageCount=0;
    for(const {document} of search(documents.filter(d=>d.kind!=='experiment'),query,explicit)){
      if(pageCount===2)break;
      if(!explicit.includes(document.page)||size+document.text.length>11000)continue;
      selected.push(document);size+=document.text.length;pageCount++;
    }
    return selected;
  }
  function occurrences(haystack,needle) {
    if(!needle.length)return 0;
    let count=0;
    for(let i=0;i<=haystack.length-needle.length;i++)
      if(needle.every((word,j)=>haystack[i+j]===word))count++;
    return count;
  }
  function authoredWords(document) {
    const r=document.retrieval;
    return r?tokens([document.title,r.question,...r.tags].join(' ')):[];
  }
  function methodIntent(documents,query) {
    const words=tokens(techniqueQuery(query));
    if(!words.length)return null;
    const families=new Map();
    for(const document of documents)for(const topic of
      (Array.isArray(document.retrieval?.topics)?document.retrieval.topics:[])){
      if(!topic||typeof topic.id!=='string'||!Array.isArray(topic.aliases))continue;
      if(!families.has(topic.id))families.set(topic.id,{id:topic.id,aliases:topic.aliases,related:new Set()});
      families.get(topic.id).related.add(document.id);
    }
    const intents=[];
    for(const family of families.values())for(const alias of family.aliases){
      const needle=tokens(alias),count=occurrences(words,needle);
      if(!count||needle.join('').length<6)continue;
      const matched=documents.filter(document=>document.kind==='experiment'&&
        occurrences(authoredWords(document),needle));
      const purity=matched.length?matched.filter(document=>family.related.has(document.id)).length/matched.length:0;
      if(purity<.55)continue;
      intents.push({family,needle,count,score:count*needle.length});
    }
    intents.sort((a,b)=>b.score-a.score||b.count-a.count||a.family.id.localeCompare(b.family.id));
    // A query naming two different methods with equal evidence is a mixed
    // proposal. Do not silently collapse it into whichever family sorts first.
    if(intents.some(intent=>intent.family.id!==intents[0]?.family.id&&intent.score===intents[0].score))return null;
    return intents[0]||null;
  }
  function rescueSelection(documents,query,pages,baseline) {
    const intent=methodIntent(documents,query);
    if(!intent)return null;
    const queryWords=tokens(techniqueQuery(query));
    const candidates=documents.filter(document=>document.kind==='experiment'&&
      occurrences(authoredWords(document),intent.needle));
    if(!candidates.length)return null;
    const coverage=document=>new Set(authoredWords(document).filter(word=>queryWords.includes(word))).size;
    const top=baseline[0];
    const bestCoverage=Math.max(...candidates.map(coverage));
    // A precise measurement can match substantially more of a stated formula
    // than a generic named-method record. Preserve that stronger evidence.
    if(top&&coverage(top)>=bestCoverage+2)return null;
    if(top&&occurrences(authoredWords(top),intent.needle)&&bestCoverage-coverage(top)<2)return null;
    // Score only concise authored fields for this rescue. Long motif prose cannot
    // swamp the explicitly named operation, but full evidence remains unchanged.
    const ranked=search(candidates.map(document=>({
      ...document,text:document.retrieval.question+' '+document.retrieval.summary,
      keywords:document.retrieval.tags.join(' ')
    })),query);
    for(const hit of ranked){
      const r=hit.document.retrieval;
      hit.score+=occurrences(tokens(hit.document.title),intent.needle)?4:
        occurrences(tokens(r.question),intent.needle)?2:.5;
    }
    const explicit=[...new Set([...pages,...pageIds(query)])];
    for(const hit of ranked){
      const complete=candidates.find(item=>item.id===hit.document.id);
      let covered=[];try{covered=JSON.parse(complete?.text||'{}').scope?.pages||[];}catch{}
      hit.pageOverlap=explicit.some(page=>covered.includes(page));
    }
    // As in rankedRecords, page overlap breaks score ties but does not claim
    // that a related method was actually tested on the requested page.
    ranked.sort((a,b)=>b.score-a.score||Number(b.pageOverlap)-Number(a.pageOverlap)||a.document.id.localeCompare(b.document.id));
    const methods=ranked.filter(hit=>!hit.document.recordType||['method','replay'].includes(hit.document.recordType));
    const ordered=[...methods,...ranked.filter(hit=>!methods.includes(hit))];
    const first=candidates.find(item=>item.id===ordered[0]?.document.id);
    if(!first)return null;
    // Keep the original all-or-nothing first-result budget rule. Never skip a
    // long leading record to replace it with a weaker and incomplete lead.
    if(first.text.length>9000)return [];
    const second=candidates.find(item=>item.id===ordered[1]?.document.id);
    const selected=second&&first.text.length+second.text.length<=9000?[first,second]:[first];
    return addPageContext(selected,documents,query,pages,selected.reduce((sum,item)=>sum+item.text.length,0));
  }
  function select(documents,query,pages=[]) {
    const baseline=lexicalSelect(documents,query,pages);
    const rescue=rescueSelection(documents,query,pages,baseline);
    return rescue===null?baseline:rescue;
  }
  function rankedRecords(documents,query,pages=[]) {
    const technique=techniqueQuery(query);
    if(!tokens(technique).length)return [];
    // Rank the technique without page numbers. Page overlap is secondary.
    const explicit=[...new Set([...pages,...pageIds(query)])];
    return search(documents.filter(d=>d.kind==='experiment'),technique).map(r=>{
      let scope=[];try{scope=JSON.parse(r.document.text).scope.pages;}catch{}
      return {...r,pageOverlap:explicit.some(p=>scope.includes(p))};
    }).sort((a,b)=>b.score-a.score||Number(b.pageOverlap)-Number(a.pageOverlap));
  }
  function classify(documents,query,pages=[]) {
    // The visible record lists and Worker evidence must agree about a rescued
    // named method. Do not leave unrelated motif hits atop the local results.
    const rescue=rescueSelection(documents,query,pages,lexicalSelect(documents,query,pages));
    if(rescue!==null){
      const hits=rescue.filter(document=>document.kind==='experiment')
        .map((document,index)=>({document,score:1/(index+1),matched:[],pageOverlap:false}));
      return {
        tests:hits.filter(hit=>!hit.document.recordType||['method','replay'].includes(hit.document.recordType)),
        supporting:hits.filter(hit=>hit.document.recordType&&!['method','replay'].includes(hit.document.recordType))
      };
    }
    const ranked=rankedRecords(documents,query,pages);
    // Retrieval is a lead, not proof of an identical experiment. Keep only
    // the strongest few; a shared generic word must not make a long list.
    const strongest=ranked[0]?.score||0;
    const candidates=ranked.filter(r=>r.score>=Math.max(.5,strongest*.62)).slice(0,8);
    const tests=candidates.filter(r=>!r.document.recordType||['method','replay'].includes(r.document.recordType));
    const supporting=candidates.filter(r=>r.document.recordType&&!['method','replay'].includes(r.document.recordType));
    // A strong diagnostic/source match should not trigger a weak, incidental method hit.
    return {tests:supporting.length&&tests.length&&supporting[0].score>=tests[0].score*1.5?[]:tests,supporting};
  }
  function experiments(documents,query,pages=[]) {
    return classify(documents,query,pages).tests;
  }
  function supporting(documents,query,pages=[]) {
    return classify(documents,query,pages).supporting;
  }
  const api={tokens,pageIds,experimentDocs,search,select,experiments,supporting,classify,techniqueQuery};
  if(typeof module!=='undefined')module.exports=api;else root.AssistantSearch=api;
})(globalThis);
