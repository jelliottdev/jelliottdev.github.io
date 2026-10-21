/* Editorial coverage notes are never experiment evidence or AI context. */
(function(root){
  const normalize=value=>String(value).normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  function match(records,query){
    const text=' '+normalize(query)+' ';
    return records.map(record=>({record,score:Math.max(0,...record.phrases.map(phrase=>{
      const term=normalize(phrase);return text.includes(' '+term+' ')?term.split(' ').length:0;
    }))})).filter(hit=>hit.score>0).sort((a,b)=>b.score-a.score||a.record.id.localeCompare(b.record.id)).slice(0,3).map(hit=>hit.record);
  }
  const api={match};
  if(typeof module!=='undefined')module.exports=api;else root.IdeaCoverage=api;
})(globalThis);
