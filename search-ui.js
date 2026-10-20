/* Shared local ranking for the header suggestions and full search results. */
const searchTypeNames={guide:'Guide',page:'Manuscript page',topic:'Topic',source:'Source'};
function searchResultHTML(hit,q,compact=false){return `<a class="wiki-search-hit" href="${esc(hit.href)}"><span class="search-hit-type">${searchTypeNames[hit.type]}${hit.matchLabel?' · '+esc(hit.matchLabel):''}</span><strong>${marked(hit.title,q)}</strong>${compact?'':`<span class="search-hit-excerpt">${marked(excerpt(hit.text,q),q)}</span>`}</a>`;}
function closeSearchSuggestions(){const panel=$('#search-suggestions');if(panel)panel.hidden=true;$('#search')?.setAttribute('aria-expanded','false');}
function submitWikiSearch(value){const q=value.trim();closeSearchSuggestions();$('#search').blur();setNavigation(false);const target='#/search/'+encodeURIComponent(q);if(location.hash===target)route();else location.hash=target;}
function bindWikiSearch(){
 const input=$('#search'),form=$('#search-form');
 const panel=document.createElement('div');panel.id='search-suggestions';panel.hidden=true;panel.setAttribute('role','region');panel.setAttribute('aria-label','Search suggestions');form.append(panel);
 input.setAttribute('aria-controls',panel.id);input.setAttribute('aria-expanded','false');
 const size=()=>{panel.style.maxHeight=Math.max(100,Math.min(420,(window.visualViewport?.height||innerHeight)-form.getBoundingClientRect().bottom-12))+'px';};
 let observedValue=input.value,watchTimer=null,resultPointer=false,pointerRelease=null;
 const draw=()=>{if(resultPointer)return;observedValue=input.value;const q=input.value.trim();if(q.length<2){closeSearchSuggestions();return}const hits=WikiSearch.search(db,q).slice(0,5);panel.innerHTML=hits.length?hits.map(h=>searchResultHTML(h,q,true)).join(''):`<p class="suggestions-empty">No matches for “${esc(q)}”.</p>`;panel.innerHTML+=`<a class="search-all" href="#/search/${encodeURIComponent(q)}">See all results for “${esc(q)}” →</a>`;panel.hidden=false;input.setAttribute('aria-expanded','true');size();};
 // Android keyboards can keep a whole word in composition. Rendering suggestions
 // is read-only with respect to the input, so do not wait for compositionend.
 input.addEventListener('input',draw);input.addEventListener('compositionend',draw);
 // Some mobile IMEs update the value without delivering a usable input event.
 // Watch only the focused field, and search only when its value actually changes.
 const stopWatching=()=>{if(watchTimer!==null)clearInterval(watchTimer);watchTimer=null;};
 const startWatching=()=>{stopWatching();draw();watchTimer=setInterval(()=>{if(document.activeElement!==input){stopWatching();return}if(input.value!==observedValue)draw()},120);};
 input.addEventListener('focus',startWatching);input.addEventListener('blur',stopWatching);
 if(document.activeElement===input)startWatching();
 input.addEventListener('keydown',e=>{if(e.key==='Escape'){closeSearchSuggestions();e.stopPropagation()}else if(e.key==='ArrowDown'&&!panel.hidden){e.preventDefault();panel.querySelector('a')?.focus()}});
 panel.addEventListener('keydown',e=>{if(e.key==='Escape'){input.focus();closeSearchSuggestions();e.preventDefault()}else if(['ArrowDown','ArrowUp'].includes(e.key)){const links=[...panel.querySelectorAll('a')],i=links.indexOf(document.activeElement);e.preventDefault();if(e.key==='ArrowUp'&&i===0)input.focus();else links[(i+(e.key==='ArrowDown'?1:-1)+links.length)%links.length].focus();}});
 // Keep the touched link alive through blur and IME composition events. A touch
 // may become a scroll, so navigation still belongs to click, never pointerdown.
 panel.addEventListener('pointerdown',()=>{clearTimeout(pointerRelease);resultPointer=true;});
 const releasePointer=()=>{if(!resultPointer)return;clearTimeout(pointerRelease);pointerRelease=setTimeout(()=>{resultPointer=false;if(!form.contains(document.activeElement))closeSearchSuggestions();else if(document.activeElement===input&&input.value!==observedValue)draw();},250);};
 document.addEventListener('pointerup',releasePointer);
 document.addEventListener('pointercancel',releasePointer);
 panel.addEventListener('click',e=>{const link=e.target.closest('a');if(!link)return;if(e.button>0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;const href=link.getAttribute('href');e.preventDefault();clearTimeout(pointerRelease);resultPointer=false;input.blur();closeSearchSuggestions();setNavigation(false);if(location.hash===href)route();else location.hash=href;});
 document.addEventListener('pointerdown',e=>{if(!form.contains(e.target))closeSearchSuggestions()});
 form.addEventListener('focusout',()=>{queueMicrotask(()=>{if(!resultPointer&&!form.contains(document.activeElement))closeSearchSuggestions()})});
 window.visualViewport?.addEventListener('resize',size);
}
function wikiSearchPage(query,release='',coverage=''){
 $('#search').value=query;
 const initial=new URLSearchParams(location.hash.split('?')[1]||'');let selected='all';
 main.innerHTML=`<div class="wiki-search-page"><header class="search-results-heading"><h1>${query?'Search results':'Search the wiki'}</h1><p id="wiki-search-count" role="status"></p></header><div class="search-result-controls"><div class="search-kind-tabs" role="group" aria-label="Result type">${[['all','All'],['guide','Guides'],['page','Pages'],['topic','Topics'],['source','Sources']].map(([id,name])=>`<button data-search-kind="${id}" aria-pressed="${id==='all'}">${name}</button>`).join('')}</div><details class="search-page-filters" ${(release||coverage||initial.get('type'))?'open':''}><summary>Page filters</summary><div class="filters"><div><label for="search-release">Release</label><select id="search-release"><option value="">Both releases</option><option>LP1</option><option>LP2</option></select></div><div><label for="search-coverage">Information available</label><select id="search-coverage"><option value="">All records</option><option value="readings">Known reading</option><option value="corrections">Documented corrections</option><option value="notes">Visual notes</option></select></div><div><label for="search-page-type">Page type</label><select id="search-page-type"><option value="">All types</option><option value="cover/title">Title pages</option><option value="runic-text">Runic text</option><option value="other">Other / numerical</option></select></div></div><p class="small muted">These filters apply only to manuscript pages.</p></details></div><div id="ranked-search-results"></div><details class="search-help"><summary>Search tips</summary><p>Use LP2-15 for a specific page, or “page 15” for both releases. Put exact phrases in quotes. Results include guides, manuscript text, annotations and topics; source links are searched by their address. This search does not establish whether a technique has been tested. For that, use <a href="#/experiments">Have we tried it?</a>.</p></details></div>`;
 $('#search-release').value=release;$('#search-coverage').value=coverage;$('#search-page-type').value=initial.get('type')||'';
 const allHits=WikiSearch.search(db,query);
 const draw=()=>{const r=$('#search-release').value,c=$('#search-coverage').value,t=$('#search-page-type').value;const hits=allHits.filter(h=>{if(selected!=='all'&&h.type!==selected)return false;if(h.type!=='page')return true;const p=h.page;return (!r||r===p.release)&&(!c||(c==='readings'?p.has_reading:c==='corrections'?p.correction_count:p.has_notes))&&(!t||(t==='other'?!['cover/title','runic-text'].includes(p.kind):p.kind===t))});
 $('#wiki-search-count').textContent=query?`${hits.length} ${hits.length===1?'result':'results'} for “${query}”`: 'Search by subject, phrase, rune sequence or page number using the search field above.';
 $('#ranked-search-results').innerHTML=hits.length?hits.map(h=>searchResultHTML(h,query)).join(''):query?`<p class="search-no-results">No matches${selected!=='all'?' in this result type':''}. Try another term${r||c||t?', or clear the page filters':''}.</p>${WikiSearch.suggest(query,db.topics).map(s=>`<p>Try <a href="#/search/${encodeURIComponent(s)}">${esc(s)}</a></p>`).join('')}`:'';
 const params=new URLSearchParams();if(r)params.set('release',r);if(c)params.set('coverage',c);if(t)params.set('type',t);history.replaceState(null,'',`#/search/${encodeURIComponent(query)}${params.size?'?'+params:''}`);
 };
 document.querySelectorAll('[data-search-kind]').forEach(b=>b.onclick=()=>{selected=b.dataset.searchKind;document.querySelectorAll('[data-search-kind]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw()});
 ['#search-release','#search-coverage','#search-page-type'].forEach(s=>$(s).onchange=draw);draw();
}
