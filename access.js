let readerMode=localStorage.getItem('liberpedia-reader-mode')||'raw',readerSize=Number(localStorage.getItem('liberpedia-reader-size'))||20,readerView=localStorage.getItem('liberpedia-reader-view')||null;
let readerPositions={image:null,text:null,compare:null},readerPositionPage=null;
let readerScrollController=null;
const readerPositionKey=id=>`liberpedia-reader-positions:${id}`;
function saveReaderPositions(){
 if(!readerPositionPage)return;
 try{sessionStorage.setItem(readerPositionKey(readerPositionPage),JSON.stringify(readerPositions))}catch{}
}
function restoreReaderPosition(id){
 if(readerPositionPage!==id||!location.hash.startsWith(`#/reader/${id}`))return;
 const offset=readerPositions[readerView];
 if(!Number.isFinite(offset))return;
 requestAnimationFrame(()=>requestAnimationFrame(()=>{
  const workspace=document.querySelector('.reader-workspace');
  if(!workspace||readerPositionPage!==id)return;
  window.scrollTo({top:Math.max(0,workspace.getBoundingClientRect().top+window.scrollY+offset),behavior:'instant'});
 }));
}
function refreshReaderSupplementary(){
 const id=location.hash.match(/^#\/reader\/([^?]+)/)?.[1],p=id&&currentPage?.id===id?currentPage:null;
 if(!p)return;
 const guide=p.reading&&db.articles.find(a=>a.id==='reading-'+p.reading.section);
 const links=document.getElementById('reader-reading-links');
 if(links&&guide)links.innerHTML=`<a href="#/wiki/${esc(guide.id)}?section=method">How this was decoded</a><a href="#/wiki/${esc(guide.id)}">Read the complete section</a><a href="#/wiki/${esc(guide.id)}?section=trace">Inspect the decoding trace</a>`;
 const payload=document.getElementById('reader-payload-link');
 if(payload&&db.payloads.records.some(r=>r.page===id))payload.innerHTML=`<a href="${link(p)}?section=embedded">Signed OutGuess payload</a>`;
 const notice=partialDataNotice(['payloads']);
 if(notice&&!document.querySelector('.manuscript-reader .data-notice'))document.querySelector('.manuscript-reader')?.insertAdjacentHTML('afterbegin',notice);
}
const fileSize=n=>n>=1048576?`${(n/1048576).toFixed(1)} MB`:n>=1024?`${(n/1024).toFixed(1)} KB`:`${n} bytes`;
function closeReaderSearchOnEscape(event){
 if(event.key!=='Escape'||!document.body.classList.contains('reader-search-open'))return;
 document.body.classList.remove('reader-search-open');
 closeSearchSuggestions();
 const toggle=document.getElementById('reader-search-toggle');
 toggle.setAttribute('aria-expanded','false');toggle.focus();
 // Consume Escape before suggestion handlers can refocus the now-hidden input.
 event.preventDefault();event.stopPropagation();
}
async function readerPage(id,version){
 let p=cache.get(id);if(!p){const response=await fetch(`data/pages/${id}.json`,{cache:"no-cache"});if(!response.ok)throw Error('The reader could not load this page.');p=await response.json();cache.set(id,p)}if(version!==renderId)return;currentPage=p;
 const topbar=document.querySelector('.topbar');
 let searchToggle=document.getElementById('reader-search-toggle');
 if(!searchToggle){
  searchToggle=document.createElement('button');searchToggle.id='reader-search-toggle';searchToggle.type='button';
  searchToggle.textContent='Search';searchToggle.setAttribute('aria-label','Search Liberpedia');
  searchToggle.setAttribute('aria-controls','search-form');topbar.append(searchToggle);
  searchToggle.onclick=()=>{
   const open=document.body.classList.toggle('reader-search-open');
   searchToggle.setAttribute('aria-expanded',String(open));
   if(open)document.getElementById('search').focus();else searchToggle.focus();
  };
  document.addEventListener('keydown',closeReaderSearchOnEscape,true);
 }
 document.body.classList.remove('reader-search-open');searchToggle.setAttribute('aria-expanded','false');
 const i=db.pages.findIndex(x=>x.id===id),prev=db.pages[i-1],next=db.pages[i+1];
 if(readerPositionPage!==id){
  readerPositions={image:null,text:null,compare:null};readerPositionPage=id;
  try{
   const saved=JSON.parse(sessionStorage.getItem(readerPositionKey(id))||'{}');
   for(const view of ['image','text','compare'])if(Number.isFinite(saved[view]))readerPositions[view]=saved[view];
  }catch{}
 }
 const requestedView=new URLSearchParams(location.hash.split('?')[1]||'').get('view');
 if(['image','text','compare'].includes(requestedView))readerView=requestedView;
 if(!readerView)readerView=main.clientWidth>=760?'compare':'image';
 main.innerHTML=`<div class="manuscript-reader">
 <header class="reader-heading"><h1>${label(p)}</h1><a href="${link(p)}">Page record ↗</a></header>
 <div class="reader-toolbar">
 <nav class="reader-pagination" aria-label="Manuscript pages">
 ${prev?`<a href="#/reader/${prev.id}" aria-label="Previous page">←</a>`:'<span aria-disabled="true" aria-label="First page">←</span>'}
 <label class="sr-only" for="reader-page">Page</label><select id="reader-page">${['LP1','LP2'].map(release=>`<optgroup label="${release==='LP1'?'First release · 17 pages':'Second release · 58 pages'}">${db.pages.filter(x=>x.release===release).map(x=>`<option value="${x.id}" ${x.id===id?'selected':''}>${label(x)}</option>`).join('')}</optgroup>`).join('')}</select>
 ${next?`<a href="#/reader/${next.id}" aria-label="Next page">→</a>`:'<span aria-disabled="true" aria-label="Last page">→</span>'}
 </nav>
 <div class="reader-views" role="group" aria-label="Reader view"><button data-reader-view="image">Image</button><button data-reader-view="text">Text</button><button data-reader-view="compare" class="reader-compare">Compare</button></div>
 </div>
 ${id==='lp1-00'?'<p class="reader-cover-link">For the compasses collage, open the <a href="#/wiki/illustrated-cover">illustrated cover</a>.</p>':''}
 ${id==='lp1-10'?'<p class="reader-cover-link">This archive file contains four concatenated JPEGs. <a href="#/wiki/2014-sixth-onion">See the page-only LP1-10 image and the source replay</a>.</p>':''}
 <div class="reader-workspace">
 <section class="manuscript-image" aria-label="Original manuscript image">
 <div class="reader-pane-bar"><span>${id==='lp1-10'?'Archived four-page carrier':p.release==='LP2'?'Wiki page JPEG':'Original JPEG'}</span><button id="reader-zoom">Enlarge ↗</button></div>
 <p class="reader-image-loading" role="status" hidden>Loading page image…</p>
 <button class="manuscript-sheet" id="reader-sheet" aria-label="Enlarge original manuscript"><img src="images/${id}.jpg" alt="Original ${label(p)}" width="${p.image_dimensions?.[0]||2400}" height="${p.image_dimensions?.[1]||3600}"></button>
 <p class="reader-image-error" hidden>Image unavailable. <a href="images/${id}.jpg">Open the original file</a> or reload this page.</p>
 </section>
 <section class="manuscript-text" aria-label="Page text">
 <div class="reader-version"><label for="reader-mode">Text version</label><select id="reader-mode">${p.visible_text?'<option value="visible">Visible Latin text</option>':'<option value="raw">Archived runes</option><option value="latin">Latin rune labels</option>'}${p.reviewed_text?'<option value="reviewed">Reviewed runes</option>':''}${p.reading?'<option value="literal">Literal known reading</option><option value="context">Contextual whole-section reading</option>':''}</select></div>
 <div class="reader-type-size"><label for="reader-size">Text size</label><input id="reader-size" type="range" min="16" max="32" value="${readerSize}"><output id="reader-size-value">${readerSize}px</output></div>
 <p id="reader-text-note" class="small muted"></p>
 <p id="reader-reading-links" class="reader-text-links reader-reading-links"></p>
 <pre id="reader-text"></pre>
 <p class="reader-text-links"><a href="${link(p)}?section=transcription">Transcription notes</a> · <a href="${link(p)}?section=page-sources">Sources</a></p>
 </section></div>
 <footer class="reader-resources">${id==='lp1-10'?'<a href="exports/sources/cicada-2014-sixth-onion/10-page.jpg" download="lp1-10-page.jpg">Download page-only JPEG</a><a href="images/lp1-10.jpg" download="lp1-10-carrier.jpg">Download four-page carrier</a>':p.release==='LP2'?`<a href="images/${id}.jpg" download="${id}-wiki.jpg">Download wiki JPEG</a><a href="exports/sources/cicada-2014-seventh-onion/${p.release_index}.jpg" download="${id}-2014-archive.jpg">Download archived JPEG</a><a href="#/wiki/2014-seventh-onion">Compare versions</a>`:`<a href="images/${id}.jpg" download="${id}.jpg">Download original JPEG</a>`}<a href="#/downloads/${id}">All page files & checksums</a><span id="reader-payload-link"></span><span>Page ${i+1} of ${db.pages.length} · <a href="#/numbering">Numbering guide</a></span></footer></div>`;
 const select=$('#reader-mode');if([...select.options].some(o=>o.value===readerMode))select.value=readerMode;else {select.selectedIndex=0;readerMode=select.value;}
 const draw=()=>{readerMode=select.value;const vals={visible:p.visible_text?.text,raw:p.raw,latin:p.lines.map(l=>l.latin).join('\n'),reviewed:p.reviewed_text,literal:p.reading?.literal,context:p.reading?.reading};$('#reader-text').textContent=vals[readerMode]||'No text is stored for this version. The original image is the reference.';$('#reader-text').className=['raw','reviewed'].includes(readerMode)?'reader-runes':'';$('#reader-text').style.fontSize=readerSize+'px';$('#reader-text-note').textContent=readerMode==='visible'?p.visible_text.basis:readerMode==='context'?`Contextual English for the entire section: ${p.reading.section_pages.join(', ')}. This may extend beyond the displayed image.`:readerMode==='literal'?'Known decoded text, preserving literal Latin conventions.':readerMode==='reviewed'?'Reviewed derivative. The archived source remains available separately.':readerMode==='latin'?'Transliteration labels, not automatically plaintext. Standalone archive separators are omitted in this view.':'Archived transcription; includes editorial separators and line markers.';};select.onchange=()=>{localStorage.setItem('liberpedia-reader-mode',select.value);draw()};draw();$('#reader-size').oninput=e=>{readerSize=Number(e.target.value);localStorage.setItem('liberpedia-reader-size',String(readerSize));$('#reader-size-value').textContent=readerSize+'px';draw()};
 const workspace=$('.reader-workspace');
 const canCompare=()=>Boolean(document.querySelector('.manuscript-reader')?.clientWidth>=760);
 const setView=view=>{readerView=view;workspace.dataset.view=view;document.querySelectorAll('[data-reader-view]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.readerView===view));};
 if(readerView==='compare'&&!canCompare())readerView='image';
 setView(readerView);
 readerScrollController?.abort();readerScrollController=new AbortController();
 window.addEventListener('scroll',()=>{
  if(!workspace.isConnected||window.scrollY===0)return;
  readerPositions[readerView]=window.scrollY-(workspace.getBoundingClientRect().top+window.scrollY);
  saveReaderPositions();
 },{passive:true,signal:readerScrollController.signal});
 refreshReaderSupplementary();
 document.querySelectorAll('[data-reader-view]').forEach(b=>b.onclick=()=>{
  const next=b.dataset.readerView;if(next==='compare'&&!canCompare())return;
  const origin=workspace.getBoundingClientRect().top+window.scrollY;
  if(window.scrollY>0){readerPositions[readerView]=window.scrollY-origin;saveReaderPositions()}
  setView(next);localStorage.setItem('liberpedia-reader-view',next);
  const url=new URL(location.href);url.hash=`/reader/${id}?view=${next}`;history.replaceState(null,'',url);
  requestAnimationFrame(()=>window.scrollTo({top:Math.max(0,origin+(readerPositions[next]??0)),behavior:'instant'}));
 });
 const resizeObserver=new ResizeObserver(()=>{if(!workspace.isConnected){resizeObserver.disconnect();return}if(readerView==='compare'&&!canCompare())document.querySelector('[data-reader-view="image"]')?.click()});
 resizeObserver.observe(document.querySelector('.manuscript-reader'));
 $('#reader-page').onchange=e=>location.hash='/reader/'+e.target.value;
 $('#reader-zoom').onclick=$('#reader-sheet').onclick=()=>openImage();
 const image=$('#reader-sheet img'),loading=$('.reader-image-loading'),imageError=$('.reader-image-error'),sheet=$('#reader-sheet'),zoomButton=$('#reader-zoom');
 let imageTimer;
 const stopLoading=()=>{clearTimeout(imageTimer);loading.hidden=true};
 image.onload=stopLoading;
 image.onerror=()=>{stopLoading();sheet.hidden=true;zoomButton.disabled=true;imageError.hidden=false};
 if(image.complete){if(!image.naturalWidth)image.onerror()}else imageTimer=setTimeout(()=>{if(image.isConnected&&!image.complete)loading.hidden=false},350);
 setTimeout(()=>restoreReaderPosition(id),0);
}
function downloadTypeMatches(file,type){
 if(type==='experiments')return file.role==='Experiment ZIP';
 if(type==='records')return file.role==='Structured experiment record';
 if(type==='images')return ['Original JPEG','Page-only JPEG','Historical page copy','Archived seventh-onion JPEG','Historical illustrated cover','Historical opening image'].includes(file.role);
 if(type==='scripts')return file.path.endsWith('.py');
 if(type==='data')return /\.(json|csv|tsv)$/.test(file.path);
 return true;
}
async function downloadsPage(pageId,version){if(!db.catalog){const response=await fetch('data/catalog.json',{cache:'no-cache'});if(!response.ok)throw Error('The download catalog could not be loaded.');db.catalog=await response.json()}if(version!==renderId)return;const bundleOrder=['downloads/reference-data.zip','downloads/original-images.zip','downloads/transcriptions-and-readings.zip'];const bundles=db.catalog.files.filter(f=>f.role==='ZIP bundle').sort((a,b)=>{const rank=path=>{const i=bundleOrder.indexOf(path);return i<0?bundleOrder.length:i};return rank(a.path)-rank(b.path)});const descriptions={'original-images.zip':'Wiki page JPEGs for 75 manuscript pages, plus separately labelled archived LP2 copies, the LP1-10 page-only cut, and historical images.','reference-data.zip':'Start here to reproduce readings or measurements: archived rune text, guides, evidence, and scripts. Add original-images.zip for image-based checks.','transcriptions-and-readings.zip':'Archived rune text and separately labeled reviewed and decoded readings.'};main.innerHTML=head('Downloads','Original files, clearly labeled derivatives, and verified bundles')+`<article><p class="lede">Choose the right page JPEG for image work, archived text for the source transcription, or a labeled reading derivative. LP2 has both wiki and seventh-onion archive JPEGs with distinct checksums. Each file has a recorded byte size and SHA-256 checksum.</p><p>For a first decoding exercise, download <a href="downloads/reference-data.zip" download>reference-data.zip</a> and follow <a href="#/wiki/running-scripts">the setup walkthrough</a>. For artwork or hidden-message extraction, choose a declared JPEG version; screenshots and thumbnails are not substitutes for source files.</p><div class="table-wrap"><table><thead><tr><th>Bundle</th><th>Contents</th><th>Size</th></tr></thead><tbody>${bundles.map(f=>`<tr><td><a href="${f.path}" download>${esc(f.path.split('/').pop())}</a></td><td>${esc(descriptions[f.path.split('/').pop()]||'Verified file bundle.')}<small>${f.members} content files; member checksums included</small></td><td>${fileSize(f.bytes)}</td></tr>`).join('')}</tbody></table></div><p class="small"><a href="downloads/SHA256SUMS.txt" download>Download all checksums</a> · <a href="data/catalog.json" download>Download the structured file catalog</a></p><p>Extract bundles with their folders intact. If you need images and scripts together, extract both into the same folder. <a href="#/wiki/checksums?section=bundle">Verify the extracted files</a> using each bundle’s separately named manifest. The reference-data bundle contains guides and reproduction inputs; it is not a complete offline copy of the website.</p><h2 id="individual-files">Find a file or experiment bundle</h2><p>For one test, choose <strong>Experiment bundles</strong> below. Each archive links back to its scope and results. You can also <a href="#/research">browse the research index</a>.</p><p>Research data: <a href="#/downloads/prime%20sum%20comparison">Archived and decoded prime sums</a> · <a href="#/downloads/whole-page%20rune%20statistics">Whole-page rune statistics</a></p><p>Historical sources: <a href="#/downloads/compasses">Compasses cover</a> · <a href="#/downloads/opening-2014">2014 opening image</a> · <a href="#/downloads/emerson">Emerson source and replay</a></p><div class="filters"><div><label for="download-query">Page, subject, filename, or file type</label><input id="download-query" type="search" placeholder="e.g. lp2-15, compasses, or zN4h51m.jpg" value="${esc(pageId||'')}"></div><div><label for="download-release">Release</label><select id="download-release"><option value="">All files</option><option>LP1</option><option>LP2</option></select></div><div><label for="download-type">File type</label><select id="download-type"><option value="">All file types</option><option value="experiments">Experiment bundles</option><option value="records">Experiment records</option><option value="images">Page images</option><option value="scripts">Python scripts</option><option value="data">JSON, CSV and TSV</option></select></div><span id="download-count" class="count" role="status"></span></div><div id="download-results"></div><h2>Verify a downloaded file</h2><p class="small">Select a file to compare its SHA-256 checksum with this catalog. The calculation happens in your browser; the file is not uploaded. A match confirms the cataloged bytes, not the identity of the manuscript’s creator.</p><label for="verify-file" class="sr-only">Choose a downloaded file to verify</label><input id="verify-file" type="file"><p id="verify-result" role="status"></p>${footer()}</article>`;
 const draw=()=>{const q=$('#download-query').value,release=$('#download-release').value,type=$('#download-type').value;const files=db.catalog.files.filter(f=>f.role!=='ZIP bundle'&&downloadTypeMatches(f,type)&&(!release||f.release===release||(f.releases||[]).includes(release))&&matches(`${f.path} ${f.role} ${f.page||''} ${(f.pages||[]).join(' ')} ${f.title||''} ${(f.aliases||[]).join(' ')}`,q));$('#download-count').textContent=`${files.length} ${files.length===1?'file':'files'}`;$('#download-results').innerHTML=files.length?`<div class="table-wrap"><table class="download-table"><thead><tr><th>File</th><th>Version</th><th>Size</th><th>Checksum</th></tr></thead><tbody>${files.map(f=>`<tr><td><a href="${f.path}" download>${esc(f.path.split('/').pop())}</a>${f.title?`<small>${esc(f.title)}</small>`:''}${f.guide?`<small><a href="#/wiki/${esc(f.guide)}">About these files</a></small>`:''}${f.experiment?`<small><a href="#/experiments/${esc(f.experiment)}">Experiment scope and results</a></small>`:''}${f.original_images_required?`<small>Also needs the separate <a href="downloads/original-images.zip" download>original-images ZIP</a>.</small>`:''}${f.releases?.length?`<small>Includes ${f.releases.map(esc).join(' and ')}</small>`:''}${f.page?`<small><a href="#/page/${f.page}">${f.page.toUpperCase()} record</a></small>`:''}</td><td>${esc(f.role)}</td><td>${fileSize(f.bytes)}</td><td><details><summary>SHA-256</summary><code class="hash">${f.sha256}</code></details></td></tr>`).join('')}</tbody></table></div>`:'<p class="empty">No matching files. Clear the search or reset the filters.</p>';};$('#download-query').oninput=draw;$('#download-release').onchange=draw;$('#download-type').onchange=draw;draw();
 let verifyVersion=0;$('#verify-file').onchange=async e=>{const version=++verifyVersion,file=e.target.files[0];if(!file)return;$('#verify-result').textContent='Calculating SHA-256…';try{const bytes=await file.arrayBuffer();const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');if(version!==verifyVersion)return;const matches=db.catalog.files.filter(f=>f.sha256===hash&&f.bytes===file.size);$('#verify-result').textContent=matches.length?'Verified exact match: '+matches.map(f=>f.path).join(', '):'No exact match in this catalog. The file may be renamed and changed, from another edition, or incomplete; compare its source before using it.';}catch{if(version===verifyVersion)$('#verify-result').textContent='Browser verification is unavailable. Download SHA256SUMS.txt and verify with a local checksum tool.'}};
}
document.addEventListener('keydown',e=>{const readerId=location.hash.match(/^#\/reader\/(lp[12]-\d{2})(?:[?]|$)/)?.[1];if(!readerId||!db?.pages||$('#image-dialog').open||e.ctrlKey||e.altKey||e.metaKey||e.shiftKey||e.target.closest('input,select,textarea,button,[contenteditable]'))return;const i=db.pages.findIndex(p=>p.id===readerId);if(i<0)return;const next=e.key==='ArrowRight'?db.pages[i+1]:e.key==='ArrowLeft'?db.pages[i-1]:null;if(next){e.preventDefault();location.hash='/reader/'+next.id}});
