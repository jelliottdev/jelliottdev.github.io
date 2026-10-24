/* Dependency positions only: no rune values, solver or candidate plaintext. */
(function(root){
 const base='experiments/records/prime-lag-autokey-openings/',expected=[2,3,5,7,11,13,17,19,23,29,31],length=12;
 let cached,pending;
 function validate(plan,results){
  const rule=plan?.prime_lag_autokey;
  if(plan?.schema!=='public-repo-expansion-bounded-followups-v1'||JSON.stringify(rule?.lags)!==JSON.stringify(expected)||JSON.stringify(rule?.modes)!==JSON.stringify(['ciphertext','plaintext'])||!Array.isArray(rule.primers)||rule.primers.length!==29||rule.primers.some((p,i)=>p!==i)||!/^First12 runes/.test(rule.target)||rule.primer_rule!=='One rune repeated for consumed j<lag; afterwards subtract prior cipher at lag or recovered plaintext at lag. No interruptions; reset each page.')throw Error('Invalid autokey rule');
  if(results?.settings!==638||results.opening_comparisons!==315810||results.exact64_rune_plant_controls_passed!==638||!Array.isArray(results.matches)||results.matches.length||!Array.isArray(results.equivalence_by_page)||results.equivalence_by_page.length!==55)throw Error('Invalid autokey results');
  const seen=new Set();
  for(const row of results.equivalence_by_page){
   if(!/^lp2-\d{2}$/.test(row.page)||seen.has(row.page)||row.parameter_settings!==638||row.lag13_to31_parameter_settings!==348||row.lag13_to31_distinct_prefixes!==29||![315,316].includes(row.distinct_predicted12_rune_prefixes))throw Error('Invalid prefix equivalence');
   seen.add(row.page);
  }
  return {lags:rule.lags.slice(),longSettings:results.equivalence_by_page[0].lag13_to31_parameter_settings,longPrefixes:results.equivalence_by_page[0].lag13_to31_distinct_prefixes};
 }
 function timeline(lag){
  if(!expected.includes(lag))throw Error('Unknown frozen delay');
  return Array.from({length},(_,j)=>({position:j+1,source:j<lag?'primer':'earlier',earlierPosition:j<lag?null:j-lag+1}));
 }
 function positions(lag){
  return '<ol class="prime-lag-positions" aria-label="Value used at each of the twelve opening positions">'+timeline(lag).map(cell=>'<li class="'+(cell.source==='primer'?'prime-lag-primer':'prime-lag-feedback')+'"><span class="prime-lag-position">Position '+cell.position+'</span><strong>'+ (cell.source==='primer'?'Primer':'Earlier rune '+cell.earlierPosition)+'</strong></li>').join('')+'</ol>';
 }
 function explanation(lag){
  const count=Math.max(0,length-lag);
  return '<strong>Feedback begins at position '+(lag+1)+'.</strong> '+(count?count+' of these 12 positions use an earlier rune.':'That is beyond this 12-rune opening: every position still uses the same primer.');
 }
 function render(){
  return '<figure class="experiment-figure prime-lag-view"><figcaption><strong>When does feedback actually begin?</strong><br>Each box names the value subtracted at that opening position.</figcaption><label class="prime-lag-label">Prime delay p<select data-prime-lag disabled><option>Loading delays…</option></select></label><p data-prime-status role="status">Loading the fixed delay rules…</p><button type="button" data-prime-retry hidden>Retry delay rules</button><div data-prime-positions></div><p data-prime-explanation role="status"></p><p data-prime-counts></p><p>The primer is one starting rune, repeated until feedback begins. Afterward, the two tested modes use either an earlier ciphertext rune or an earlier recovered plaintext rune.</p><p>Positions here start at 1. The source starts at j = 0 and uses the primer while j &lt; p; the first feedback position is p + 1. This diagram shows dependencies, not a plaintext reading.</p><p><a href="'+base+'prime-lag.svg" download>Download the original SVG summary</a></p></figure>';
 }
 async function bind(figure,{isCurrent=()=>true,fetcher=(...args)=>fetch(...args)}={}){
  if(!figure)return;
  const select=figure.querySelector('[data-prime-lag]'),status=figure.querySelector('[data-prime-status]'),retry=figure.querySelector('[data-prime-retry]'),grid=figure.querySelector('[data-prime-positions]'),note=figure.querySelector('[data-prime-explanation]'),counts=figure.querySelector('[data-prime-counts]');
  const current=()=>figure.isConnected&&isCurrent();let loading=false,data;
  const draw=()=>{if(!current()||!data||!data.lags.includes(Number(select.value)))return;grid.innerHTML=positions(Number(select.value));note.innerHTML=explanation(Number(select.value));};
  select.addEventListener('change',draw);
  const load=async()=>{
   if(loading||!current())return;loading=true;const hadFocus=figure.ownerDocument?.activeElement===retry;select.disabled=true;retry.disabled=true;status.textContent='Loading the fixed delay rules…';
   try{
    if(!cached){
     if(!pending)pending=(async()=>{
      const controller=new AbortController();let timer;
      try{return await Promise.race([
       Promise.all(['plan-frozen-original.json','results.json'].map(async name=>{const response=await fetcher(base+name,{signal:controller.signal});if(!response.ok)throw Error();return response.json();})).then(([p,r])=>validate(p,r)),
       new Promise((resolve,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Delay request timed out'));},10000);})
      ])}finally{clearTimeout(timer);controller.abort();}
     })().then(value=>cached=value).finally(()=>{pending=null});
     await pending;
    }
    if(!current())return;data=cached;
    select.innerHTML=data.lags.map(lag=>'<option value="'+lag+'">'+lag+'</option>').join('');select.value='13';select.disabled=false;draw();
    counts.textContent='In the saved scan, the six delays from 13 to 31 give '+data.longSettings+' settings but only '+data.longPrefixes+' distinct opening predictions per page. Neither mode reaches feedback within these 12 positions.';
    status.textContent='';
    if(hadFocus&&(figure.ownerDocument.activeElement===retry||figure.ownerDocument.activeElement===figure.ownerDocument.body))select.focus({preventScroll:true});retry.hidden=true;
   }catch{if(current()){status.textContent='The delay rules could not load. Retry or download the SVG summary below.';retry.hidden=false;}}
   finally{loading=false;if(current())retry.disabled=false;}
  };
  retry.addEventListener('click',load);return load();
 }
 const api={validate,timeline,positions,explanation,render,bind};if(typeof module!=='undefined')module.exports=api;else root.PrimeLagView=api;
})(globalThis);
