/* Shared browser/Worker retrieval. Page IDs are exact; prose uses lexical ranking. */
(function(root) {
  const stop = new Set('a an the is it this that to of for on in with and or we i have has had tried try could would can does do what if using use how why are was were about explain compare please page pages test tests tested testing technique method any anyone already every all been done applying apply row rows line lines input inputs data manuscript rune runes result results one each'.split(' '));
  for(const word of ['its','than','be','checking','check','whether','know'])stop.add(word);
  const aliases={languages:'language',primes:'prime',emirps:'emirp',reversal:'reverse',reversing:'reverse',reversed:'reverse',shifts:'shift',shifted:'shift',shifting:'shift'};
  const pageReference=/\blp\s*([12])(?:[\s:\-‐‑–—−]*page\s*)?[\s:#\-‐‑–—−]*(\d{1,2})\b/gi;
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
      phrases:r.tags||[]
    }));
  }
  function techniqueQuery(query) {
    return query.replace(pageReference,' ').replace(/\bpages?\s*#?\s*\d+(?:\s*[-‐‑–—−]\s*#?\s*\d+)?/gi,' ');
  }
  function search(documents, query, pages=[]) {
    const terms=[...new Set(tokens(query))], explicit=[...new Set([...pages,...pageIds(query)])];
    const corpus=documents.map(d=>({document:d,words:tokens(d.title+' '+d.title+' '+d.text+' '+(d.keywords||''))}));
    const avg=corpus.reduce((sum,d)=>sum+d.words.length,0)/(corpus.length||1)||1;
    const df=new Map(terms.map(t=>[t,corpus.filter(d=>d.words.includes(t)).length]));
    return corpus.map(({document,words})=>{
      let score=0,matched=[];
      for(const term of terms){const n=words.filter(w=>w===term).length;if(!n)continue;matched.push(term);
        score+=Math.log(1+(corpus.length-df.get(term)+.5)/(df.get(term)+.5))*n*2.2/(n+1.2*(.25+.75*words.length/avg));}
      // A complete authored technique phrase outranks incidental body mentions.
      // Use only the strongest phrase: duplicate/overlapping tags cannot stack.
      const queryPhrase=' '+tokens(query).join(' ')+' ';
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
  function select(documents,query,pages=[]) {
    const ranked=experiments(documents,query,pages);
    // A manuscript page match is never evidence that a technique was tested.
    if(!ranked.length)return [];
    const selected=[ranked[0].document];
    let size=selected[0].text.length;
    if(size>9000)return []; // Never replace an oversized best match with a weaker one.
    const second=ranked[1]?.document;
    if(second&&size+second.text.length<=9000){selected.push(second);size+=second.text.length;}
    // Keep the best complete scope when its sibling cannot fit; never truncate either.
    const explicit=[...new Set([...pages,...pageIds(query)])];
    let pageCount=0;
    for(const {document} of search(documents.filter(d=>d.kind!=='experiment'),query,explicit)){
      if(pageCount===2)break;
      if(!explicit.includes(document.page)||size+document.text.length>11000)continue;
      selected.push(document);size+=document.text.length;pageCount++;
    }
    return selected;
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
    const ranked=rankedRecords(documents,query,pages);
    const tests=ranked.filter(r=>!r.document.recordType||['method','replay'].includes(r.document.recordType));
    const supporting=ranked.filter(r=>r.document.recordType&&!['method','replay'].includes(r.document.recordType));
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
