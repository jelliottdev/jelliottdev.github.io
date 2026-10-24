/* Search actual stored representations; contextual prose has no source-row address. */
(function(root){
 const layers=['raw','latin','reviewed','literal','context','visible'];
 function sourceRows(text){let row=0;return String(text||'').split('\n').map(text=>({text,line:/[^\s\-.,/&$§%]/u.test(text)?++row:null}));}
 function searchable(text,archive=false){let value='',offsets=[];for(let i=0;i<text.length;i++){const c=text[i],space=/\s/u.test(c)||(archive&&/[-/&$§%]/u.test(c));if(space){if(value&&!value.endsWith(' ')){value+=' ';offsets.push(i)}}else{value+=c.toLocaleLowerCase();offsets.push(i)}}return {value,offsets};}
 function find(text,query,archive=false){const hay=searchable(text,archive),needle=searchable(query,archive).value.trim();if(!needle)return [];const hits=[];let at=hay.value.indexOf(needle);while(at>=0){const start=hay.offsets[at],end=hay.offsets[at+needle.length-1]+1;hits.push({start,end,before:text.slice(Math.max(0,start-45),start),match:text.slice(start,end),after:text.slice(end,end+65)});at=hay.value.indexOf(needle,at+Math.max(1,needle.length));}return hits;}
 function pageHits(page,alphabet,query,selected=layers){
  const out=[],map=new Map(alphabet.map(a=>[a.rune,a.latin]));
  for(const layer of selected){
   if(!layers.includes(layer))throw Error('Unknown source layer');
   if(layer==='raw'||layer==='latin'||layer==='reviewed'){
    if(layer==='reviewed'&&typeof page.reviewed_text!=='string')continue;
    if(layer==='reviewed'){const original=sourceRows(page.raw),derived=sourceRows(page.reviewed_text);if(original.length!==derived.length||original.some((r,i)=>(r.line===null)!==(derived[i].line===null))){for(const hit of find(page.reviewed_text,query,true))out.push({...hit,page:page.id,layer,line:null,section:null,section_pages:[page.id]});continue;}}
    for(const r of sourceRows(layer==='reviewed'?page.reviewed_text:page.raw)){if(r.line===null)continue;const text=layer==='latin'?[...r.text].map(c=>map.get(c)||c).join(''):r.text;for(const hit of find(text,query,true))out.push({...hit,page:page.id,layer,line:r.line,section:null,section_pages:[page.id]});}
   }else{
    const text=layer==='literal'?page.reading?.literal:layer==='context'?page.reading?.reading:page.visible_text?.text;
    if(typeof text!=='string')continue;for(const hit of find(text,query,layer==='literal'))out.push({...hit,page:page.id,layer,line:null,section:layer==='context'?page.reading?.section:null,section_pages:layer==='context'?page.reading?.section_pages||[page.id]:[page.id]});
   }
  }return out;
 }
 async function search(pages,alphabet,loadPage,{query,layers:selected=layers,signal,concurrency=4}={}){
  if(!String(query||'').trim())return {results:[],total:0,failed:[],checked:0};
  let next=0,checked=0;const found=[],failed=[];
  function cancelled(){if(signal?.aborted){const e=Error('Search cancelled');e.name='AbortError';throw e}}
  await Promise.all(Array.from({length:Math.min(4,Math.max(1,concurrency),pages.length)},async()=>{while(next<pages.length){cancelled();const meta=pages[next++];try{const data=await loadPage(meta.id,signal);cancelled();if(data?.id!==meta.id||typeof data.raw!=='string')throw Error('Invalid page text');found.push(...pageHits(data,alphabet,query,selected));checked++;}catch(e){if(e.name==='AbortError'||signal?.aborted)throw e;failed.push(meta.id);}}}));
  cancelled();const order=new Map(pages.map((p,i)=>[p.id,i]));found.sort((a,b)=>order.get(a.page)-order.get(b.page)||layers.indexOf(a.layer)-layers.indexOf(b.layer)||(a.line||0)-(b.line||0)||a.start-b.start);
  const seen=new Set(),results=found.filter(h=>{const key=h.layer==='context'?[h.layer,h.section||h.page,h.start,h.end].join(':'):null;if(key&&seen.has(key))return false;if(key)seen.add(key);return true;});
  return {results,total:results.length,failed,checked};
 }
 const api={layers,find,pageHits,search,sourceRows};if(typeof module!=='undefined')module.exports=api;else root.ReaderManuscriptSearch=api;
})(globalThis);
