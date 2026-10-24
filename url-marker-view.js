/* One fixed, published marker census; no configurable source paths or cipher search. */
(function(root){
 const base='experiments/records/url-marker-affine-census/',names=['WWW','HTTP','HTTPS','ONION'];
 const tokens={WWW:[7,7,7],HTTP:[8,16,16,13],HTTPS:[8,16,16,13,15],ONION:[3,9,10,3,9]};
 const labels=['R','X','X','O','L'];let cached,pending;
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function validate(results,matches){
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  if(results?.schema!=='url-marker-affine-census-result-v1'||results.map_count!==812||results.total_runes!==12956||results.nonempty_pages!==55||results.total_literal_matches!==2||results.distinct_page_map_start_positions!==1||!Array.isArray(results.original_equal_symbol_triples)||results.original_equal_symbol_triples.length||!Array.isArray(matches)||matches.length!==2)throw Error('Invalid marker census');
  for(const name of names)if(!same(results.tokens?.[name],tokens[name])||results.literal_matches_by_token?.[name]!==(['HTTP','HTTPS'].includes(name)?1:0))throw Error('Invalid marker count');
  const https=matches.find(m=>m.token==='HTTPS'),http=matches.find(m=>m.token==='HTTP');
  if(!https||!http||https.page!=='lp2-36'||https.a!==24||https.b!==28||https.rune_start_zero_based!==226||https.rune_end_exclusive!==231||!same(https.cipher_indices,[4,14,14,3,20])||!same(https.plain_indices,tokens.HTTPS))throw Error('Invalid marker window');
  if(http.page!==https.page||http.a!==https.a||http.b!==https.b||http.rune_start_zero_based!==https.rune_start_zero_based||http.rune_end_exclusive!==230||!same(http.cipher_indices,https.cipher_indices.slice(0,4))||!same(http.plain_indices,tokens.HTTP)||https.cipher_indices.some((c,i)=>(https.a*c+https.b)%29!==https.plain_indices[i]))throw Error('Invalid prefix relationship');
  return {results,https};
 }
 function content(data,alphabet=[]){
  const {results,https}=data;
  const symbols=https.cipher_indices.map((index,i)=>{
   const entry=Array.isArray(alphabet)?alphabet.find(a=>a.index===index&&a.latin===labels[i]):null;
   return entry&&typeof entry.rune==='string'&&/^\p{Script=Runic}$/u.test(entry.rune)?entry.rune:labels[i];
  });
  return '<h3 tabindex="-1" data-url-heading>One candidate location</h3><p><a href="#/reader/'+https.page+'">'+https.page.toUpperCase()+'</a> · rune start '+https.rune_start_zero_based+' (counting from zero)</p><p class="url-marker-formula">P = ('+https.a+'C + '+https.b+') mod 29</p><p class="url-marker-label">Cipher rune/index → decoded letter/index</p><ol class="url-marker-strip" aria-label="Five-rune marker mapping">'+https.cipher_indices.map((index,i)=>'<li><span class="sr-only">Cipher '+labels[i]+', index '+index+', maps to '+names[2][i]+', index '+https.plain_indices[i]+'.</span><div aria-hidden="true"><span class="url-marker-glyph rune">'+esc(symbols[i])+'</span><span class="url-marker-index">'+index+'</span><span class="url-marker-arrow">↓</span><strong>'+names[2][i]+'</strong><span class="url-marker-index">'+https.plain_indices[i]+'</span></div></li>').join('')+'</ol><p>These are alphabet indices, not prime values.</p><table class="url-marker-counts"><caption>Literal matches across '+results.map_count+' fixed maps</caption><thead><tr><th scope="col">Marker</th><th scope="col">Matches</th></tr></thead><tbody>'+names.map(name=>'<tr><th scope="row">'+name+'</th><td>'+results.literal_matches_by_token[name]+'</td></tr>').join('')+'</tbody></table><p><strong>HTTP is the prefix of this same HTTPS window.</strong> The two rows describe one location, not two candidates.</p><p><strong>Why no WWW?</strong> A fixed one-to-one map preserves repeats: WWW needs three identical adjacent source runes. The page streams contain none.</p><p>A short marker does not establish a web address or confirm plaintext. The no-WWW rule does not apply to maps that change with position.</p>';
 }
 function render(){
  return '<figure class="experiment-figure url-marker-view"><figcaption><strong>From five runes to a literal marker</strong></figcaption><p data-url-status role="status">Loading the marker counts…</p><button type="button" data-url-retry hidden>Retry marker counts</button><div data-url-content></div><p><a href="'+base+'marker-census.svg" download>Download the complete SVG figure</a></p></figure>';
 }
 async function bind(figure,{alphabet=[],isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!figure)return;
  const status=figure.querySelector('[data-url-status]'),retry=figure.querySelector('[data-url-retry]'),view=figure.querySelector('[data-url-content]');
  const current=()=>figure.isConnected&&isCurrent();let loading=false;
  const load=async()=>{
   if(loading||!current())return;loading=true;const hadFocus=figure.ownerDocument?.activeElement===retry;
   retry.disabled=true;status.textContent='Loading the marker counts…';
   try{
    if(!cached){
     if(!pending)pending=(async()=>{
      const controller=new AbortController();let timer;
      try{return await Promise.race([
       Promise.all(['results.json','matches.json'].map(async name=>{const response=await fetcher(base+name,{signal:controller.signal});if(!response.ok)throw Error('Marker request failed');return response.json();})).then(([r,m])=>validate(r,m)),
       new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Marker request timed out'));},10000);})
      ])}finally{clearTimeout(timer)}
     })().then(value=>cached=value).finally(()=>{pending=null});
     await pending;
    }
    if(!current())return;view.innerHTML=content(cached,alphabet);status.textContent='';
    if(hadFocus&&(figure.ownerDocument.activeElement===retry||figure.ownerDocument.activeElement===figure.ownerDocument.body))view.querySelector('[data-url-heading]')?.focus({preventScroll:true});
    retry.hidden=true;
   }catch{if(current()){status.textContent='The marker counts could not load. Retry or download the SVG figure below.';retry.hidden=false;}}
   finally{loading=false;if(current())retry.disabled=false;}
  };
  retry.addEventListener('click',load);return load();
 }
 const api={validate,content,render,bind};if(typeof module!=='undefined')module.exports=api;else root.UrlMarkerView=api;
})(globalThis);
