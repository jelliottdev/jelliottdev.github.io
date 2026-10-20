/* Shared browser/Worker retrieval. Page IDs are exact; prose uses lexical ranking. */
(function(root) {
  const stop = new Set('a an the is it this that to of for on in with and or we i have has had tried try could would can does do what if using use how why are was were about explain compare please page pages test tests tested testing technique method any anyone already every all been done applying apply row rows line lines input inputs data manuscript rune runes result results one each'.split(' '));
  const aliases={primes:'prime',emirps:'emirp',reversal:'reverse',reversing:'reverse',reversed:'reverse',shifts:'shift',shifted:'shift',shifting:'shift'};
  const pageReference=/\blp\s*([12])(?:[\s:\-‐‑–—−]*page\s*)?[\s:#\-‐‑–—−]*(\d{1,2})\b/gi;
  const tokens = text => (String(text).normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(t=>!stop.has(t)).map(t=>aliases[t]||t);
  function pageIds(text) {
    return [...new Set([...text.matchAll(pageReference)]
      .map(m=>`lp${m[1]}-${m[2].padStart(2,'0')}`))];
  }
  function experimentDocs(records) {
    return records.filter(r=>r.status==='published').map(r=>({
      id:r.id, title:r.title, kind:'experiment', href:`#/experiments/${r.id}`,
      text:JSON.stringify({question:r.question,family:r.family,variant:r.variant,scope:r.scope,outcome:r.outcome,finding:r.finding,limitations:r.limitations}),
      // Retrieval can use prose, but evidence always preserves the complete scope.
      keywords:[r.summary,...(r.tags||[]),r.article||''].join(' ')
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
    const selected=ranked.slice(0,2).map(r=>r.document);
    let size=selected.reduce((sum,d)=>sum+d.text.length,0);
    if(size>9000)return []; // Do not truncate experiment scope to fit a prompt.
    const explicit=[...new Set([...pages,...pageIds(query)])];
    for(const {document} of search(documents.filter(d=>d.kind!=='experiment'),query,explicit)){
      if(selected.length===4)break;
      if(!explicit.includes(document.page)||size+document.text.length>11000)continue;
      selected.push(document);size+=document.text.length;
    }
    return selected;
  }
  function experiments(documents,query,pages=[]) {
    const technique=techniqueQuery(query);
    if(!tokens(technique).length)return [];
    // Rank the technique without page numbers. Page overlap is secondary.
    const explicit=[...new Set([...pages,...pageIds(query)])];
    return search(documents.filter(d=>d.kind==='experiment'),technique).map(r=>{
      let scope=[];try{scope=JSON.parse(r.document.text).scope.pages;}catch{}
      return {...r,pageOverlap:explicit.some(p=>scope.includes(p))};
    }).sort((a,b)=>b.score-a.score||Number(b.pageOverlap)-Number(a.pageOverlap));
  }
  const api={tokens,pageIds,experimentDocs,search,select,experiments,techniqueQuery};
  if(typeof module!=='undefined')module.exports=api;else root.AssistantSearch=api;
})(globalThis);
