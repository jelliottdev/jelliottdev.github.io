/* Audited grid positions; this map does not transcribe the other cells. */
(function(root){
  const rows={'lp2-49':10,'lp2-50':13,'lp2-51':9},offsets={'lp2-49':0,'lp2-50':80,'lp2-51':184};
  const alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx';
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let cached,pending;
  function validate(data){
    if(data?.schema!=='liberpedia-grid-stem-uncertainty-v1'||data.grid_cells!==256||!Array.isArray(data.stem_cells)||data.stem_cells.length!==10)throw Error('Invalid stem map');
    const seen=new Set(),counts={};
    for(const cell of data.stem_cells){
      if(!Object.hasOwn(rows,cell.page)||!Number.isInteger(cell.row)||cell.row<1||cell.row>rows[cell.page]||!Number.isInteger(cell.column)||cell.column<1||cell.column>8)throw Error('Invalid cell');
      const key=cell.page+':'+cell.row+':'+cell.column;
      if(seen.has(key)||cell.sequence!==offsets[cell.page]+(cell.row-1)*8+cell.column)throw Error('Invalid position');
      seen.add(key);counts[cell.page]=(counts[cell.page]||0)+1;
      if(!/^[0-3][Il]$/.test(cell.wiki_token)||!/^[0-3][A-Za-z]$/.test(cell.archive_token)||!Array.isArray(cell.alternatives)||!Array.isArray(cell.base60_bytes)||cell.alternatives.length!==2||cell.base60_bytes.length!==2)throw Error('Invalid readings');
      const prefix=cell.wiki_token[0];
      if(cell.alternatives[0]!==prefix+'I'||cell.alternatives[1]!==prefix+'l'||cell.alternatives.some((token,i)=>cell.base60_bytes[i]!==60*Number(prefix)+alphabet.indexOf(token[1])))throw Error('Invalid byte alternatives');
    }
    const other=data.separate_case_disagreement;
    if(counts['lp2-49']!==4||counts['lp2-50']!==4||counts['lp2-51']!==2||other?.page!=='lp2-50'||other.row!==12||other.column!==5||other.wiki_token!=='2S'||other.archive_token!=='2s')throw Error('Invalid separate disagreement');
    return data;
  }
  function cells(data,page){return [...data.stem_cells.filter(cell=>cell.page===page),...(data.separate_case_disagreement.page===page?[{...data.separate_case_disagreement,separate:true}]:[])].sort((a,b)=>a.row-b.row||a.column-b.column);}
  function grid(data,page,selected){
    const marks=new Map(cells(data,page).map(cell=>[cell.row+':'+cell.column,cell]));
    let html='<table><caption>'+esc(page.toUpperCase())+' · '+rows[page]+' rows, 8 columns</caption><thead><tr><td></td>'+Array.from({length:8},(_,i)=>'<th scope="col">'+(i+1)+'</th>').join('')+'</tr></thead><tbody>';
    for(let row=1;row<=rows[page];row++){
      html+='<tr><th scope="row">'+row+'</th>';
      for(let col=1;col<=8;col++){
        const key=row+':'+col,cell=marks.get(key);
        html+='<td>'+(cell?'<button type="button" data-stem-cell="'+key+'" class="'+(cell.separate?'stem-separate':'stem-mark')+'" aria-pressed="'+(key===selected)+'" aria-label="Row '+row+', column '+col+': '+(cell.separate?'S or s disagreement':'I or lowercase l stem')+'">'+esc(cell.wiki_token)+'</button>':'<span class="stem-empty" aria-hidden="true"></span>')+'</td>';
      }
      html+='</tr>';
    }
    return html+'</tbody></table>';
  }
  function detail(cell){
    return '<h3>'+cell.page.toUpperCase()+' · row '+cell.row+', column '+cell.column+'</h3><p>Wiki reading: <code>'+esc(cell.wiki_token)+'</code> · Archive reading: <code>'+esc(cell.archive_token)+'</code></p>'+(cell.separate?'<p>This S/s disagreement is separate from the ten I/l stems; it is not included in their byte alternatives.</p>':'<p>Under the base-60 byte interpretation: '+cell.alternatives.map((token,i)=>'<code>'+esc(token)+'</code> → <strong>'+cell.base60_bytes[i]+'</strong>').join(' or ')+'.</p><p>The bare stem does not settle which case was intended.</p>')+'<a href="#/reader/'+cell.page+'">Inspect the original '+cell.page.toUpperCase()+' image</a>';
  }
  function render(){
    return '<figure class="experiment-figure grid-stem-view"><figcaption><strong>Where the readings are uncertain</strong><br>Inspect one page at a time. Blue cells mark I/l stems; the dashed cell marks a separate S/s disagreement. Blank cells are not transcribed in this map.</figcaption><label class="stem-page-label">Page<select data-stem-page disabled>'+Object.keys(rows).map(page=>'<option value="'+page+'">'+page.toUpperCase()+'</option>').join('')+'</select></label><p data-stem-status role="status">Loading the audited positions…</p><button type="button" data-stem-retry hidden>Retry map</button><div class="stem-grid-wrap" data-stem-grid></div><div class="stem-cell-detail" data-stem-detail></div><p><a href="experiments/records/grid-stem-uncertainty/stem-map.svg" download>Download the complete SVG map</a></p></figure>';
  }
  async function bind(figure,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
    if(!figure)return;
    const select=figure.querySelector('[data-stem-page]'),status=figure.querySelector('[data-stem-status]'),retry=figure.querySelector('[data-stem-retry]'),map=figure.querySelector('[data-stem-grid]'),info=figure.querySelector('[data-stem-detail]');
    const current=()=>figure.isConnected&&isCurrent();let data,loading=false;
    const choose=key=>{
      const cell=cells(data,select.value).find(cell=>cell.row+':'+cell.column===key);if(!cell)return;
      for(const button of map.querySelectorAll('[data-stem-cell]'))button.setAttribute('aria-pressed',String(button.dataset.stemCell===key));
      info.innerHTML=detail(cell);status.textContent=cell.page.toUpperCase()+', row '+cell.row+', column '+cell.column+' selected.';
    };
    const draw=()=>{if(!current()||!data)return;const first=cells(data,select.value)[0],key=first.row+':'+first.column;map.innerHTML=grid(data,select.value,key);choose(key);};
    select.addEventListener('change',draw);
    map.addEventListener('click',event=>{const button=event.target.closest('[data-stem-cell]');if(current()&&data&&button&&map.contains(button))choose(button.dataset.stemCell);});
    const load=async()=>{
      if(loading||!current())return;loading=true;retry.disabled=true;select.disabled=true;status.textContent='Loading the audited positions…';
      try{
        if(!cached){
          if(!pending)pending=(async()=>{
            const controller=new AbortController();let timer;
            try{
              return await Promise.race([
                (async()=>{const response=await fetcher('experiments/records/grid-stem-uncertainty/results.json',{signal:controller.signal});if(!response.ok)throw Error();return validate(await response.json());})(),
                new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Map request timed out'));},10000);})
              ]);
            }finally{clearTimeout(timer);}
          })().then(value=>cached=value).finally(()=>{pending=null});
          data=await pending;
        }else data=cached;
        if(!current())return;select.disabled=false;draw();
        if(figure.ownerDocument?.activeElement===retry)select.focus({preventScroll:true});retry.hidden=true;
      }catch{if(current()){status.textContent='The interactive map could not load. Retry or download the complete SVG map below.';retry.hidden=false;}}
      finally{loading=false;if(current())retry.disabled=false;}
    };
    retry.addEventListener('click',load);return load();
  }
  const api={rows,validate,cells,grid,detail,render,bind};
  if(typeof module!=='undefined')module.exports=api;else root.GridStemView=api;
})(globalThis);
