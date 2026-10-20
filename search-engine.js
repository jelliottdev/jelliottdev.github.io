/* Deterministic local search. No network search, query logging, or inferred facts. */
(function(root){
 const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[–—_]/g,'-').replace(/\s+/g,' ').trim();
 const terms=q=>[...String(q).matchAll(/"([^"]+)"|(\S+)/g)].map(m=>norm(m[1]||m[2])).filter(Boolean);
 // One parsed query can be reused across every field. Keep only the current
 // query, and leave the public terms() result independent and mutable.
 let lastQuery,lastTerms;
 const has=(text,q)=>{
  if(q!==lastQuery||!lastTerms){lastQuery=q;lastTerms=terms(q);}
  if(!lastTerms.length)return true;
  const normalized=norm(text);
  return lastTerms.every(t=>normalized.includes(t));
 };
 function page(p,q){
  if(!q.trim())return {score:0,type:'Page record',text:p.title,section:'details'};
  const n=norm(q),id=n.match(/^lp([12])\s*[-:·]?\s*(?:page\s*)?0*(\d{1,2})$/),generic=n.match(/^page\s*0*(\d{1,2})$/),file=n.match(/^(\d{1,2})\.jpg$/);
  if(id)return p.id===`lp${id[1]}-${id[2].padStart(2,'0')}`?{score:1000,type:'Page identifier',text:p.id.toUpperCase(),section:'details'}:null;
  if(generic)return p.release_index===Number(generic[1])?{score:900,type:'Release page number',text:`${p.release} page ${p.release_index}; include the release when citing this page.`,section:'details'}:null;
  if(file)return (p.source_names||[]).some(s=>s.filename.toLowerCase()===n)?{score:950,type:'Archive filename',text:`${q} in the pinned combined archive corresponds to ${p.id.toUpperCase()}.`,section:'details'}:null;
  const fields=[['Embedded payload',p.embedded_text,155,'embedded'],['Page title',p.title,180,'details'],['Visual note',p.notes_text,150,'details'],['Correction',p.correction_text,145,'corrections'],['Known reading',p.literal,130,'reading'],['Contextual reading of section',p.contextual,75,'reading'],['Method',`${p.section||''} ${p.method||''}`,110,'reading']];
  let hits=fields.filter(([,s])=>s&&has(s,q)).map(([type,text,score,section])=>({type,text,score,section}));
  for(const row of p.text_rows||[]){if(has(row.raw,q))hits.push({type:`Archived text · row ${row.row}`,text:row.raw,score:170,section:'transcription',row:row.row,mode:'runes'});else if(has(row.latin,q))hits.push({type:`Latin labels · row ${row.row}`,text:row.latin,score:165,section:'transcription',row:row.row,mode:'latin'});}
  if(!hits.length&&has(`${p.id} ${p.release} page ${p.release_index} ${p.title} ${p.search}`,q))hits.push({type:'Page record',text:'Search terms occur across this page record. Open the transcription or related evidence below.',score:20,section:'details'});
  return hits.sort((a,b)=>b.score-a.score)[0]||null;
 }
 function distance(a,b){let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let next=[i];for(let j=1;j<=b.length;j++)next[j]=Math.min(next[j-1]+1,row[j]+1,row[j-1]+(a[i-1]!==b[j-1]));row=next;}return row[b.length];}
 function suggest(q,topics){const n=norm(q);if(!/^[a-z]{5,24}$/.test(n))return [];const words=[...new Set(topics.flatMap(t=>(norm(t.title+' '+t.terms).match(/[a-z]{5,24}/g)||[])))];return words.filter(w=>w!==n&&Math.abs(w.length-n.length)<=2).map(w=>({w,d:distance(n,w)})).filter(x=>x.d<=(n.length>7?2:1)).sort((a,b)=>a.d-b.d||a.w.localeCompare(b.w)).slice(0,3).map(x=>x.w);}
 function relevance(title,summary,body,q){
  const n=norm(q);if(!n)return 0;
  const normalizedTitle=norm(title);
  if(normalizedTitle===n)return 1200;
  if(normalizedTitle.startsWith(n))return 800;
  if(has(title,q))return 650;
  if(has(summary,q))return 300;
  return has(title+' '+summary+' '+body,q)?60:0;
 }
 // Curated names and spelling variants belong to the article metadata. They
 // identify a subject; they never turn an interpretation into a page fact.
 function aliasScore(aliases,q){
  const n=norm(q);
  if(!n)return 0;
  if((aliases||[]).some(a=>norm(a)===n))return 1100;
  if(n.length>=3&&(aliases||[]).some(a=>norm(a).startsWith(n)))return 780;
  return 0;
 }
 // Destination keys follow the same case/accent rules as alias matching.
 const aliasDestination=(mapping,q)=>Object.entries(mapping||{}).find(([key])=>norm(key)===norm(q))?.[1];
 function search(db,q){
  if(!norm(q))return [];
  const hits=[];
  const features=new Map();
  for(const a of db.articles||[]){
   const alias=aliasScore(a.aliases,q),score=Math.max(alias,relevance(a.title,a.summary,a.text,q));
   const section=alias?aliasDestination(a.alias_sections,q):null;
   if(score)hits.push({type:'guide',title:a.title,text:a.summary,href:'#/wiki/'+a.id+(section?'?section='+encodeURIComponent(section):''),score});
   if(alias)for(const id of aliasDestination(a.alias_pages,q)||a.feature_pages||[])if(!features.has(id))features.set(id,a);
  }
  for(const p of db.pages||[]){const hit=page(p,q);if(hit)hits.push({type:'page',title:p.id.toUpperCase()+(p.title?' · '+p.title:''),text:hit.text,href:'#/page/'+p.id+'?'+(hit.row?'line='+hit.row+'&mode='+hit.mode:'section='+hit.section),score:hit.score,page:p});}
  for(const [id,a] of features){
   const p=(db.pages||[]).find(p=>p.id===id);if(!p)continue;
   const existing=hits.find(h=>h.page?.id===id);
   const score=aliasScore(a.aliases,q)>=1100?900:700;
   if(existing&&existing.score>=score)continue;
   const feature={type:'page',title:id.toUpperCase()+' · '+a.title,text:a.summary,href:'#/page/'+id+'?section=details',score,page:p};
   if(existing)Object.assign(existing,feature);else hits.push(feature);
  }
  for(const t of db.topics||[]){const score=relevance(t.title,t.summary,t.terms,q);if(score)hits.push({type:'topic',title:t.title,text:t.summary,href:'#/topics?topic='+t.id,score:score===1200?1100:score-40});}
  for(const r of db.sources||[]){if(has(decodeURI(r.url).replaceAll('-',' '),q))hits.push({type:'source',title:decodeURI(new URL(r.url).pathname),text:new URL(r.url).hostname,href:r.url,score:10});}
  return hits.sort((a,b)=>b.score-a.score||a.title.localeCompare(b.title));
 }
 const api={norm,terms,has,page,suggest,relevance,aliasScore,search};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.WikiSearch=api;
})(globalThis);
