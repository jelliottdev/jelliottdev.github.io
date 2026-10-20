/* Deterministic local search. No network search, query logging, or inferred facts. */
(function(root){
 const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[–—_]/g,'-').replace(/\s+/g,' ').trim();
 const terms=q=>[...String(q).matchAll(/"([^"]+)"|(\S+)/g)].map(m=>norm(m[1]||m[2])).filter(Boolean);
 const has=(text,q)=>terms(q).every(t=>norm(text).includes(t));
 function page(p,q){
  if(!q.trim())return {score:0,type:'Page record',text:p.title,section:'details'};
  const n=norm(q),id=n.match(/^lp([12])\s*[-:·]?\s*(?:page\s*)?0*(\d{1,2})$/),generic=n.match(/^page\s*0*(\d{1,2})$/),file=n.match(/^(\d{1,2})\.jpg$/);
  if(id)return p.id===`lp${id[1]}-${id[2].padStart(2,'0')}`?{score:1000,type:'Page identifier',text:p.id.toUpperCase(),section:'details'}:null;
  if(generic)return p.release_index===Number(generic[1])?{score:900,type:'Release page number',text:`${p.release} page ${p.release_index}; include the release when citing this page.`,section:'details'}:null;
  if(file)return (p.source_names||[]).some(s=>s.filename.toLowerCase()===n)?{score:950,type:'Archive filename',text:`${q} in the pinned combined archive corresponds to ${p.id.toUpperCase()}.`,section:'details'}:null;
  const fields=[['Page title',p.title,180,'details'],['Visual note',p.notes_text,150,'details'],['Correction',p.correction_text,145,'corrections'],['Known reading',p.literal,130,'reading'],['Contextual reading of section',p.contextual,75,'reading'],['Method',`${p.section||''} ${p.method||''}`,110,'reading']];
  let hits=fields.filter(([,s])=>s&&has(s,q)).map(([type,text,score,section])=>({type,text,score,section}));
  for(const row of p.text_rows||[]){if(has(row.raw,q))hits.push({type:`Archived text · row ${row.row}`,text:row.raw,score:170,section:'transcription',row:row.row,mode:'runes'});else if(has(row.latin,q))hits.push({type:`Latin labels · row ${row.row}`,text:row.latin,score:165,section:'transcription',row:row.row,mode:'latin'});}
  if(!hits.length&&has(`${p.id} ${p.release} page ${p.release_index} ${p.title} ${p.search}`,q))hits.push({type:'Page record',text:'Search terms occur across this page record. Open the transcription or related evidence below.',score:20,section:'details'});
  return hits.sort((a,b)=>b.score-a.score)[0]||null;
 }
 function distance(a,b){let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let next=[i];for(let j=1;j<=b.length;j++)next[j]=Math.min(next[j-1]+1,row[j]+1,row[j-1]+(a[i-1]!==b[j-1]));row=next;}return row[b.length];}
 function suggest(q,topics){const n=norm(q);if(!/^[a-z]{5,24}$/.test(n))return [];const words=[...new Set(topics.flatMap(t=>(norm(t.title+' '+t.terms).match(/[a-z]{5,24}/g)||[])))];return words.filter(w=>w!==n&&Math.abs(w.length-n.length)<=2).map(w=>({w,d:distance(n,w)})).filter(x=>x.d<=(n.length>7?2:1)).sort((a,b)=>a.d-b.d||a.w.localeCompare(b.w)).slice(0,3).map(x=>x.w);}
 const api={norm,terms,has,page,suggest};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.WikiSearch=api;
})(globalThis);
