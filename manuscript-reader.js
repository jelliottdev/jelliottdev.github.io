'use strict';
(() => {
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)], A=ReaderAddress;
const icons={prev:'m14 6-6 6 6 6',next:'m10 6 6 6-6 6',close:'m6 6 12 12M6 18 18 6',options:'M4 6h16M4 12h16M4 18h16M8 3v6M16 9v6M10 15v6',plus:'M5 12h14M12 5v14',minus:'M5 12h14'};
for(const [id,name] of [['prev','prev'],['next','next'],['options-button','options'],['finder-close','close'],['options-close','close'],['reference-close','close'],['clear-selection','close'],['zoom-in','plus'],['zoom-out','minus']])$('#'+id).innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[name]}"/></svg>`;
const state={id:'lp2-15',view:innerWidth>760?'compare':'image',navigation:'turn',mode:'raw',size:23,numbers:true,wrap:true,range:null,target:null};
const cache=new Map(),pending=new Map(),imageStates=new Map(),positions=new Map();let restoring=false;
let db,observer,renderVersion=0,queryVersion=0,navigationVersion=0,toastTimer,scrollTimer,referenceTab='notes',searchController,searchMatches=[],searchPage=0;
try{const saved=JSON.parse(localStorage.getItem('liberpedia-manuscript-reader')||'{}');for(const key of ['view','navigation','mode','size','numbers','wrap'])if(saved[key]!==undefined)state[key]=saved[key];if(saved.continuous===true)state.navigation='scroll';if(saved.lines!==undefined)state.numbers=saved.lines;if(saved.mode==='reading')state.mode='literal'}catch{}
if(!['image','text','compare'].includes(state.view))state.view='image';if(innerWidth<=760&&state.view==='compare')state.view='image';if(!['turn','scroll'].includes(state.navigation))state.navigation='turn';if(!['raw','latin','reviewed','literal','context','visible'].includes(state.mode))state.mode='raw';state.size=Math.max(16,Math.min(32,Number(state.size)||23));
async function fetchJSON(path){const controller=new AbortController();let timer;try{return await Promise.race([fetch(path,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json()}),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Request timed out'))},10000)})])}finally{clearTimeout(timer)}}
function ownsHorizontalArrows(target){const pane=target.closest('.image-viewport,.text-viewport');return !!pane&&pane.scrollWidth>pane.clientWidth+1}
function persist(){try{localStorage.setItem('liberpedia-manuscript-reader',JSON.stringify({view:state.view,navigation:state.navigation,mode:state.mode,size:state.size,numbers:state.numbers,wrap:state.wrap}));sessionStorage.setItem('manuscript-reader-last-page',state.id)}catch{}}
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),2200)}
function node(tag,text,parent){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(parent)parent.append(el);return el}
function link(text,href,parent){const a=node('a',text,parent);a.href=href;return a}
const pageId=(release,n)=>release.toLowerCase()+'-'+String(n).padStart(2,'0');
const addressOf=id=>{const p=db.pages.find(p=>p.id===id);return{release:p.release,pages:[p.release_index,p.release_index],lines:null,words:null}};
function activeIds(){return state.range||db.pages.map(p=>p.id)}
async function getPage(id){if(cache.has(id))return cache.get(id);if(pending.has(id))return pending.get(id);const request=(async()=>{const p=await fetchJSON(`data/pages/${id}.json`);if(p.id!==id||typeof p.raw!=='string'||!Array.isArray(p.lines))throw Error('Invalid page data');cache.set(id,p);return p})().finally(()=>pending.delete(id));pending.set(id,request);return request}
function remember(){
 const article=document.querySelector(`article[data-id="${state.id}"]`);if(!article)return;
 const old=positions.get(state.id)||{},next={...old},continuous=$('#flow').dataset.navigation==='scroll';
 const pageBounds=article.getBoundingClientRect(),viewport=$('#viewport').getBoundingClientRect();
 const text=article.querySelector('.text-viewport'),image=article.querySelector('.image-viewport');
 if(text.getClientRects().length){
  next.text=text.scrollTop;
  const frame=continuous?viewport:text.getBoundingClientRect();
  const line=[...text.querySelectorAll('.source-line')].find(el=>{const r=el.getBoundingClientRect();return r.bottom>frame.top+4&&r.top<frame.bottom});
  if(line)next.textAnchor={line:Number(line.dataset.line),offset:line.getBoundingClientRect().top-frame.top};
  if(continuous)next.textPageRatio=(viewport.top-pageBounds.top)/pageBounds.height;
 }
 if(image.getClientRects().length){
  next.image=image.scrollTop;next.left=image.scrollLeft;
  if(continuous)next.imagePageRatio=(viewport.top-pageBounds.top)/pageBounds.height;
 }
 positions.set(state.id,next);
}
function updateBar(){const p=db.pages.find(p=>p.id===state.id);$('#location').textContent=p.release+' '+String(p.release_index).padStart(2,'0');$('#goto').setAttribute('aria-label',`Go to or search. Current page ${p.release} ${p.release_index}`);document.title=p.id.toUpperCase()+' · Liberpedia';const ids=activeIds(),i=ids.indexOf(state.id);$('#prev').disabled=i<=0;$('#next').disabled=i>=ids.length-1;$$('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(state.view===b.dataset.view)));$$('[data-navigation]').forEach(b=>b.setAttribute('aria-pressed',String(state.navigation===b.dataset.navigation)));$('#numbering').checked=state.numbers;$('#wrapping').checked=state.wrap;$('#size').value=state.size;document.body.style.setProperty('--size',state.size+'px');$('#range-option').hidden=!state.range;if(state.range)$('#range-label').textContent=state.range[0].toUpperCase()+' – '+state.range.at(-1).toUpperCase();persist()}
function versions(p){return p.visible_text?[['visible','Visible']]:[['raw','Runes'],['latin','Labels'],...(p.reviewed_text?[['reviewed','Reviewed']]:[]),...(p.reading?[['literal','Literal'],['context','Reading']]:[])]}
function effectiveMode(p){return versions(p).some(([v])=>v===state.mode)?state.mode:versions(p)[0][0]}
function updateVersions(p){$('#text-versions').replaceChildren(...versions(p).map(([value,label])=>{const b=node('button',label);b.setAttribute('aria-pressed',String(effectiveMode(p)===value));b.onclick=()=>{state.mode=value;if(state.target?.lines){state.target=null;updateSelection()}persist();for(const el of $$('article.page')){const data=cache.get(el.dataset.id);if(data)drawText(el,data)}updateVersions(p)};return b}))}
function originalText(p,mode=effectiveMode(p)){return mode==='latin'?ReaderSourceRows.labels(p.raw,db.alphabet):mode==='reviewed'?p.reviewed_text:mode==='literal'?p.reading.literal:mode==='context'?p.reading.reading:mode==='visible'?p.visible_text.text:p.raw}
function drawWords(parent,text,selected){const words=A.words(text);let offset=0;words.forEach((word,i)=>{parent.append(document.createTextNode(text.slice(offset,word.start)));const el=node(selected&&i+1>=selected[0]&&i+1<=selected[1]?'mark':'span',word.text,parent);el.dataset.word=i+1;offset=word.end});parent.append(document.createTextNode(text.slice(offset)))}
function drawText(article,p){const root=article.querySelector('.text-content'),mode=effectiveMode(p);root.replaceChildren();root.className='text-content'+(mode==='latin'?' latin':'')+(state.numbers?'':' no-numbers')+(state.wrap?'':' no-wrap');
 const caption=node('p',undefined,root);caption.className='text-caption';caption.textContent=mode==='context'?`Documented whole-section reading · ${p.reading.section_pages.map(x=>x.toUpperCase()).join(', ')}`:mode==='literal'?'Literal documented reading · source-row alignment not asserted':mode==='visible'?p.visible_text.basis:mode==='reviewed'?'Reviewed derivative · addresses use archived rows':mode==='latin'?'Latin rune labels · source rows':'Archived runes · source rows';
 if(['context','literal','visible'].includes(mode)||mode==='reviewed'&&!ReaderSourceRows.addressable(p,p.reviewed_text)){const prose=node('div',originalText(p,mode),root);prose.className='prose';return}
 // Archive rows are authoritative; standalone paragraph/segment markers do not increment them.
 let row=0;const archived=p.raw.split('\n');const reviewed=mode==='reviewed'?p.reviewed_text.split('\n'):null;
 for(let index=0;index<archived.length;index++){
  const raw=archived[index];if(!raw.trim()){node('div','\u200b',root).className='archive-marker';continue;}
  if(row<p.lines.length&&raw.trim()===p.lines[row].raw.trim()){
   row++;const line=node('div',undefined,root);line.className='source-line';line.dataset.line=row;line.id=p.id+'-line-'+row;
   const number=node('button',String(row),line);number.className='line-number';number.setAttribute('aria-label',`Select line ${row}`);const n=row;number.onclick=e=>{const previous=state.target;if(e.shiftKey&&previous?.lines&&state.id===p.id){const a=previous.lines[0];go({...addressOf(p.id),lines:[Math.min(a,n),Math.max(a,n)],words:null})}else go({...addressOf(p.id),lines:[n,n],words:null})};
   const value=node('span',undefined,line);value.className='line-value';const text=mode==='latin'?p.lines[row-1].latin:mode==='reviewed'?(reviewed[index]??raw):raw;
   const selected=state.target?.lines&&p.id===pageId(state.target.release,state.target.pages[0])&&row>=state.target.lines[0]&&row<=state.target.lines[1];if(selected)line.classList.add('selected');drawWords(value,text,selected?state.target.words:null);
  }else{const marker=node('div',mode==='latin'?raw:reviewed?.[index]??raw,root);marker.className='archive-marker'}
 }
 if(row!==p.lines.length){const warning=node('p','Source row alignment is incomplete; consult the page record.',root);warning.className='text-caption'}
}
function imageState(id){if(!imageStates.has(id))imageStates.set(id,{fit:'page',multiple:1});return imageStates.get(id)}
function fitImage(article){const p=cache.get(article.dataset.id),img=article.querySelector('img.manuscript');if(!p)return;const area=article.querySelector('.image-viewport'),settings=imageState(p.id),pad=innerWidth<=760?20:innerWidth<=1000?28:36;const w=p.image_dimensions[0],h=p.image_dimensions[1];let scale=(area.clientWidth-pad)/w;if(state.navigation==='turn'&&settings.fit==='page')scale=Math.min(scale,(area.clientHeight-pad)/h);scale=Math.max(.01,scale)*settings.multiple;img.style.width=Math.round(w*scale)+'px';img.style.height=Math.round(h*scale)+'px';article.querySelector('.image-stage').style.width=img.style.width;area.dataset.zoomed=String(settings.multiple>1.02);article.querySelector('.image-region').hidden=true}
function zoomImage(article,factor,point){const image=article.querySelector('img.manuscript'),area=article.querySelector('.image-viewport'),stage=article.querySelector('.image-stage');if(!image.naturalWidth)return;const bounds=stage.getBoundingClientRect(),frame=area.getBoundingClientRect(),x=point?.x??frame.left+area.clientWidth/2,y=point?.y??frame.top+area.clientHeight/2;const before=image.getBoundingClientRect().width;const u=(x-bounds.left)/before,v=(y-bounds.top)/before;const s=imageState(article.dataset.id);s.multiple=Math.max(.5,Math.min(8,s.multiple*factor));fitImage(article);const after=stage.getBoundingClientRect(),width=image.getBoundingClientRect().width;area.scrollLeft+=after.left+u*width-x;area.scrollTop+=after.top+v*width-y}
function makePage(id){const article=node('article');article.className='page';article.dataset.id=id;const header=node('header',undefined,article);header.className='page-label';node('span',id.toUpperCase(),header);link('Page record',`index.html#/page/${id}`,header);const spread=node('div',undefined,article);spread.className='spread';const image=node('section',undefined,spread);image.className='image-cell';const caption=node('span','',image);caption.className='source-caption';image.setAttribute('aria-label',id.toUpperCase()+' image');const area=node('div',undefined,image);area.className='image-viewport';area.tabIndex=0;area.setAttribute('aria-label','Page image. Pinch to zoom; drag to pan.');const stage=node('div',undefined,area);stage.className='image-stage';const img=node('img',undefined,stage);img.className='manuscript';img.alt=id.toUpperCase()+' manuscript';img.draggable=false;img.loading='lazy';img.width=2400;img.height=3600;img.style.width='min(100%,600px)';const region=node('div',undefined,stage);region.className='image-region';region.hidden=true;
 const split=node('div',undefined,spread);split.className='split';split.tabIndex=0;split.setAttribute('role','separator');split.setAttribute('aria-orientation','vertical');split.setAttribute('aria-label','Image width');split.setAttribute('aria-valuemin','30');split.setAttribute('aria-valuemax','70');split.setAttribute('aria-valuenow',String(Math.round(Number($('#flow').style.getPropertyValue('--image-share'))||50)));bindSplit(split);
 const text=node('section',undefined,spread);text.className='text-cell';text.setAttribute('aria-label',id.toUpperCase()+' text');const scroll=node('div',undefined,text);scroll.className='text-viewport';scroll.tabIndex=0;const content=node('div','Loading text…',scroll);content.className='text-content';bindGestures(article);const cached=cache.get(id);if(cached){drawText(article,cached);img.width=cached.image_dimensions[0];img.height=cached.image_dimensions[1]}return article}
function hydrate(article){if(article._hydration)return article._hydration;article._hydration=hydratePage(article).finally(()=>article._hydration=null);return article._hydration}
async function hydratePage(article){if(article.dataset.loaded==='true'||article.dataset.loading==='true')return;article.dataset.loading='true';const id=article.dataset.id;try{const p=await getPage(id);if(!article.isConnected)return;article.dataset.loaded='true';drawText(article,p);article.querySelector('.source-caption').textContent=p.id==='lp1-10'?'Four-page carrier':p.release==='LP2'?'Wiki JPEG':'Original JPEG';const img=article.querySelector('img.manuscript');img.onload=()=>{if(!article.isConnected)return;fitImage(article);};img.width=p.image_dimensions[0];img.height=p.image_dimensions[1];img.onerror=()=>{const area=article.querySelector('.image-viewport');img.hidden=true;const error=node('p','Image unavailable. ',area);error.className='image-error';link('Open original file',`images/${id}.jpg`,error);const retry=node('button','Retry',error);retry.onclick=()=>{img.hidden=false;error.remove();img.src=`images/${id}.jpg?retry=${Date.now()}`}};if(state.view!=='text')img.src=`images/${id}.jpg`;if(state.view==='text'){img.loading='lazy';img.src=`images/${id}.jpg`}
 if(id===state.id)updateVersions(p);
 }catch{if(article.isConnected){const root=article.querySelector('.text-content');root.replaceChildren();node('p','Page text unavailable.',root);link('Open static record',`reference/${id}.html`,root);const retry=node('button','Retry',root);retry.onclick=()=>{article.dataset.loading='false';hydrate(article)}}}finally{article.dataset.loading='false'}}
async function render(revealTarget=false,savePosition=true){
 if(savePosition)remember();restoring=true;clearTimeout(scrollTimer);const saved=positions.get(state.id),version=++renderVersion;observer?.disconnect();
 const flow=$('#flow');flow.dataset.view=state.view;flow.dataset.navigation=state.navigation;
 const ids=state.navigation==='turn'?[state.id]:activeIds();flow.replaceChildren(...ids.map(makePage));updateBar();$$('article.page').forEach(fitImage);
 observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting)hydrate(entry.target)}),{root:$('#viewport'),rootMargin:'700px'});
 $$('article.page').forEach(el=>observer.observe(el));
 const current=document.querySelector(`article[data-id="${state.id}"]`);
 if(state.navigation==='scroll')current?.scrollIntoView({block:'start'});else $('#viewport').scrollTop=0;
 if(current){if(state.navigation==='scroll'){const index=ids.indexOf(state.id);await Promise.all(ids.slice(Math.max(0,index-2),index+3).map(id=>hydrate(document.querySelector(`article[data-id="${id}"]`))))}else await hydrate(current)}if(version!==renderVersion)return;
 if(current&&state.view!=='text'){try{await Promise.race([current.querySelector('img.manuscript').decode(),new Promise(resolve=>setTimeout(resolve,8000))])}catch{}}
 await document.fonts.ready;if(version!==renderVersion)return;
 const target=revealTarget&&state.target?.lines?current?.querySelector(`[data-line="${state.target.lines[0]}"]`):null;
 if(target)target.scrollIntoView({block:'center'});
 else if(current&&saved){
  const text=current.querySelector('.text-viewport'),image=current.querySelector('.image-viewport');
  if(state.view!=='image'){
   const anchor=saved.textAnchor,line=anchor&&current.querySelector(`[data-line="${anchor.line}"]`);
   if(line){const area=state.navigation==='scroll'?$('#viewport'):text;area.scrollTop+=line.getBoundingClientRect().top-area.getBoundingClientRect().top-anchor.offset}
   else if(state.navigation==='turn')text.scrollTop=saved.text||0;
   else if(Number.isFinite(saved.textPageRatio))$('#viewport').scrollTop+=-current.getBoundingClientRect().top+$('#viewport').getBoundingClientRect().top+saved.textPageRatio*current.getBoundingClientRect().height;
  }else if(state.navigation==='scroll'&&Number.isFinite(saved.imagePageRatio)){
   $('#viewport').scrollTop+=-current.getBoundingClientRect().top+$('#viewport').getBoundingClientRect().top+saved.imagePageRatio*current.getBoundingClientRect().height;
  }
  if(state.view!=='text'){image.scrollTop=saved.image||0;image.scrollLeft=saved.left||0}
 }
 updateSelection();remember();restoring=false;
}
function updateSelection(){const target=state.target;$('#selection').hidden=!target?.lines;if(target?.lines)$('#selection-label').textContent=A.label(target)}
async function go(target,{history=true}={}){const navigation=++navigationVersion;if(target.error){toast(target.error);return false}let error=A.validate(target,db.pages);if(error){toast(error);return false}const id=pageId(target.release,target.pages[0]);if(target.lines){try{error=A.validate(target,db.pages,await getPage(id))}catch{toast('Cannot validate this location while the page is unavailable.');return false}if(error){toast(error);return false}}
 if(navigation!==navigationVersion)return false;remember();state.match=null;state.id=id;state.target=structuredClone(target);if(target.pages[0]!==target.pages[1]){state.range=db.pages.filter(p=>p.release===target.release&&p.release_index>=target.pages[0]&&p.release_index<=target.pages[1]).map(p=>p.id);state.navigation='scroll'}else if(state.range&&!state.range.includes(id))state.range=null;if(target.lines){state.mode='raw';state.view=innerWidth>760?'compare':'text'}if(history)window.history.pushState(null,'','#'+encodeURIComponent(A.short(target)));if($('#finder').open)$('#finder').close();await render(true,false);return navigation===navigationVersion}
function turn(delta){const ids=activeIds(),next=ids[ids.indexOf(state.id)+delta];if(next){state.target=null;go(addressOf(next))}}
function setView(value){remember();state.view=innerWidth<=760&&value==='compare'?'image':value;return render()}
function setNavigation(value){remember();state.navigation=value;return render()}
function message(text){const p=node('p',text,$('#suggestions'));p.className='finder-message'}
function suggestion(title,detail,action,primary=false){const button=node('button',undefined,$('#suggestions'));button.className='suggestion'+(primary?' primary':'');node('strong',title,button);if(detail)node('small',detail,button);button.onclick=action;return button}
async function search(){searchController?.abort();const generation=++queryVersion,q=$('#query').value.trim(),root=$('#suggestions');root.replaceChildren();const release=db.pages.find(p=>p.id===state.id).release;
 if(!q){message('Go to a location, a section or matching text.');const examples=node('div',undefined,root);examples.className='section-links';for(const text of ['15:4','15:4:2-6','15-17','first koan']){const b=node('button',text,examples);b.onclick=()=>{$('#query').value=text;search()}}const jumps=node('div',undefined,root);jumps.className='page-jumps';for(const p of db.pages.filter(p=>p.release===release)){const b=node('button',String(p.release_index).padStart(2,'0'),jumps);b.setAttribute('aria-label',p.id.toUpperCase());b.onclick=()=>go(addressOf(p.id))}return}
 const address=A.parse(q,release);if(address){if(address.error){message(address.error);return}let error=A.validate(address,db.pages);if(!error&&address.lines){try{error=A.validate(address,db.pages,await getPage(pageId(address.release,address.pages[0])))}catch{error='Cannot validate this location. Try again.'}}if(generation!==queryVersion)return;if(error){message(error);return}suggestion(A.label(address),address.words?'Archive words follow transcription delimiters; they are not established plaintext words.':address.lines?'Stable source rows; wrapping does not change their numbers.':'Open the requested pages.',()=>go(address),true);return}
 if(q.includes(':')&&/^(?:lp[12][ -]?)?\d/i.test(q)){message('Use page:line:word. For example, 15:4:2-6.');return}
 for(const p of db.pages)if(p.title?.toLowerCase().includes(q.toLowerCase()))suggestion(p.id.toUpperCase()+' · '+p.title,'Page title',()=>go(addressOf(p.id)));
 const normalized=q.toLowerCase().replace(/[-_\s]+/g,' ').trim(),sections=new Map();for(const p of db.pages){if(p.section){const name=p.section.replaceAll('-',' ');if(name.toLowerCase().includes(normalized)){if(!sections.has(p.section))sections.set(p.section,[]);sections.get(p.section).push(p)}}}
 for(const [section,pages] of sections){const first=pages[0],last=pages.at(-1),target={release:first.release,pages:[first.release_index,last.release_index],lines:null,words:null};suggestion(section.replaceAll('-',' '),A.label(target),()=>go(target),root.childElementCount===0)}
 await searchStored(q,generation);
}
function drawSearchMatches(){
 const root=$('#suggestions'),start=searchPage*10;
 for(const hit of searchMatches.slice(start,start+10)){const a=link('',storedMatchHash(hit),root);a.className='suggestion'+(root.childElementCount===1?' primary':'');node('strong',hit.page.toUpperCase()+(hit.line?' · source row '+hit.line:''),a);node('small',`${hit.layer}: ${hit.before}${hit.match}${hit.after}`,a);a.onclick=event=>openStoredMatchEvent(event,hit);}
 if(searchMatches.length>10){const nav=node('div',undefined,root);nav.className='search-pagination';for(const [label,delta,disabled]of [['Previous results',-1,searchPage===0],['Next results',1,start+10>=searchMatches.length]]){const button=node('button',label,nav);button.disabled=disabled;button.onclick=()=>{searchPage+=delta;root.replaceChildren();drawSearchMatches();root.querySelector('.suggestion')?.focus()}}}
}
async function searchStored(query,generation){
 searchController?.abort();const controller=new AbortController();searchController=controller;$('#search-cancel').hidden=false;const selected=$('#search-layer').value;
 try{const result=await ReaderManuscriptSearch.search(db.pages,db.alphabet,getPage,{query,layers:selected==='all'?ReaderManuscriptSearch.layers:[selected],signal:controller.signal});if(generation!==queryVersion||controller.signal.aborted)return;searchMatches=result.results;searchPage=0;drawSearchMatches();message(`${result.total} text matches in ${result.checked} checked pages.`+(result.failed.length?` ${result.failed.length} pages unavailable; search again to retry.`:''));}
 catch(error){if(generation===queryVersion&&error.name!=='AbortError')message('Search unavailable. Try again.');}
 finally{if(generation===queryVersion)$('#search-cancel').hidden=true}
}
function storedMatchHash(hit){const params=new URLSearchParams({view:'text',version:['literal','context'].includes(hit.layer)?'reading':hit.layer});if(['literal','context'].includes(hit.layer))params.set('reading',hit.layer==='context'?'context':'literal');if(hit.line!==null){params.set('line',String(hit.line));params.set('match',hit.start+'-'+hit.end)}else params.set('textmatch',hit.start+'-'+hit.end);return '#'+hit.page+'?'+params}
function openStoredMatchEvent(event,hit){if(event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;event.preventDefault();return openStoredMatch(hit)}
async function openStoredMatch(hit){
 const target=addressOf(hit.page);if(!await go(target))return;const navigation=navigationVersion;state.mode=hit.layer;state.view='text';state.match=hit;await render();
 if(navigation!==navigationVersion||state.id!==hit.page)return;history.replaceState(null,'',storedMatchHash(hit));revealMatch();
}
function revealMatch(){const hit=state.match;if(!hit)return;const article=document.querySelector(`article[data-id="${hit.page}"]`);if(!article)return;const value=hit.line!==null?article.querySelector(`[data-line="${hit.line}"] .line-value`):article.querySelector('.prose');if(!value)return;const text=value.textContent;if(!Number.isInteger(hit.start)||!Number.isInteger(hit.end)||hit.start<0||hit.end<=hit.start||hit.end>text.length)return;const mark=node('mark',text.slice(hit.start,hit.end));mark.className='source-match';value.replaceChildren(document.createTextNode(text.slice(0,hit.start)),mark,document.createTextNode(text.slice(hit.end)));mark.scrollIntoView({block:'center'})}
let finderDraft='',finderSearchVersion=0,finderCommitVersion=0,finderTask=Promise.resolve();
function refreshFinder(){
 const version=++finderSearchVersion;$('#suggestions').setAttribute('aria-busy','true');
 finderTask=search().finally(()=>{if(version===finderSearchVersion)$('#suggestions').setAttribute('aria-busy','false')});
 return finderTask;
}
function openFinder(){
 if(!db)return;
 $('#query').value=finderDraft;$('#finder').showModal();refreshFinder();$('#query').focus();$('#query').select();
}
function bindFinder(){
 $('#suggestions').setAttribute('role','region');$('#suggestions').setAttribute('aria-label','Search results');
 $('#query').setAttribute('aria-controls','suggestions');$('#query').setAttribute('aria-describedby','address-help');
 $('#query').oninput=()=>{finderDraft=$('#query').value;finderCommitVersion++;refreshFinder()};
 $('#query').onkeydown=async event=>{
  if(event.key==='Enter'){
   event.preventDefault();const version=++finderCommitVersion,value=$('#query').value;
   await refreshFinder();
   if(version===finderCommitVersion&&$('#finder').open&&$('#query').value===value)$('#suggestions .suggestion')?.click();
  }else if(event.key==='ArrowDown'){
   event.preventDefault();await finderTask;
   if($('#finder').open)$('#suggestions .suggestion, #suggestions button')?.focus();
  }
 };
 $('#suggestions').onkeydown=event=>{
  if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
  const items=[...$('#suggestions').querySelectorAll('button:not(:disabled),a.suggestion[href]')],i=items.indexOf(document.activeElement);
  if(i<0)return;event.preventDefault();
  if(event.key==='ArrowUp'&&i===0){$('#query').focus();return}
  const next=event.key==='Home'?0:event.key==='End'?items.length-1:Math.max(0,Math.min(items.length-1,i+(event.key==='ArrowDown'?1:-1)));
  items[next]?.focus();
 };
 $('#finder').addEventListener('close',()=>{finderDraft=$('#query').value;finderCommitVersion++;queryVersion++;searchController?.abort()});
}
function bindSplit(split){let down=false;const set=value=>{const v=Math.max(30,Math.min(70,value));$('#flow').style.setProperty('--image-share',v);try{localStorage.setItem('liberpedia-manuscript-reader-split',String(v))}catch{}$$('.split').forEach(el=>el.setAttribute('aria-valuenow',String(Math.round(v))));$$('article.page').forEach(fitImage)};split.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();split.setPointerCapture(e.pointerId);down=true};split.onpointermove=e=>{if(!down)return;const r=split.parentElement.getBoundingClientRect();set((e.clientX-r.left)/r.width*100)};split.onpointerup=split.onpointercancel=()=>down=false;split.ondblclick=()=>set(50);split.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Enter'].includes(e.key)){e.preventDefault();e.stopPropagation();const current=Number(split.getAttribute('aria-valuenow'));set(e.key==='Enter'?50:current+(e.key==='ArrowRight'?2:-2))}}}
function bindGestures(article){const area=article.querySelector('.image-viewport'),touches=new Map();let start=null,previous=null,pinched=false,mouse=null;
 const geometry=()=>{const p=[...touches.values()];return p.length>1?{x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2,d:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y)}:p[0]};
 area.onpointerdown=e=>{if(e.pointerType==='touch'){touches.set(e.pointerId,{x:e.clientX,y:e.clientY});area.setPointerCapture(e.pointerId);previous=geometry();if(touches.size===1){start={x:e.clientX,y:e.clientY,time:performance.now()};pinched=false}else pinched=true}else if(e.button===0&&imageState(article.dataset.id).multiple>1){mouse={x:e.clientX,y:e.clientY,left:area.scrollLeft,top:area.scrollTop};area.setPointerCapture(e.pointerId)}};
 area.onpointermove=e=>{if(e.pointerType==='touch'&&touches.has(e.pointerId)){touches.set(e.pointerId,{x:e.clientX,y:e.clientY});const point=geometry();if(previous){if(touches.size>1&&previous.d)zoomImage(article,point.d/previous.d,previous);const dx=point.x-previous.x,dy=point.y-previous.y;if(imageState(article.dataset.id).multiple>1.02||touches.size>1){area.scrollLeft-=dx;area.scrollTop-=dy}else if(state.navigation==='scroll')$('#viewport').scrollTop-=dy;else area.scrollTop-=dy}previous=point}else if(mouse){area.scrollLeft=mouse.left+mouse.x-e.clientX;area.scrollTop=mouse.top+mouse.y-e.clientY}};
 function end(e){if(e.pointerType==='touch'){touches.delete(e.pointerId);if(!touches.size&&start&&!pinched&&e.type==='pointerup'&&state.navigation==='turn'&&imageState(article.dataset.id).multiple<=1.02){const dx=e.clientX-start.x,dy=e.clientY-start.y;if(Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.5&&performance.now()-start.time<850)turn(dx<0?1:-1)}previous=geometry();if(!touches.size)start=null}else mouse=null}
 area.onpointerup=end;area.onpointercancel=end;area.ondblclick=()=>{const s=imageState(article.dataset.id);s.multiple=s.multiple>1?1:2;fitImage(article)};area.addEventListener('wheel',e=>{if(e.ctrlKey||e.metaKey){e.preventDefault();zoomImage(article,e.deltaY<0?1.1:1/1.1,{x:e.clientX,y:e.clientY})}},{passive:false});
 for(const pane of article.querySelectorAll('.image-viewport,.text-viewport'))pane.addEventListener('scroll',()=>{if(!restoring&&article.dataset.id===state.id&&pane.getClientRects().length)remember()},{passive:true});
 let textStart=null;const text=article.querySelector('.text-viewport');text.style.touchAction='pan-y';text.onpointerdown=e=>{if(e.pointerType==='touch'&&!e.target.closest('button,a,input'))textStart={x:e.clientX,y:e.clientY,time:performance.now()}};text.onpointercancel=()=>textStart=null;text.onpointerup=e=>{if(!textStart)return;const dx=e.clientX-textStart.x,dy=e.clientY-textStart.y;if(state.navigation==='turn'&&Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.5&&performance.now()-textStart.time<850&&!getSelection().toString())turn(dx<0?1:-1);textStart=null}}
async function renderReference(){const id=state.id;let p;try{p=await getPage(id)}catch{$('#reference-body').textContent='Page reference unavailable.';return}if(id!==state.id)return;const root=$('#reference-body');root.replaceChildren();$$('[data-tab]').forEach(b=>b.setAttribute('aria-pressed',String(referenceTab===b.dataset.tab)));$('#reference-title').textContent=p.id.toUpperCase();if(referenceTab==='notes'){for(const note of p.notes||[]){node('h3',note.title,root);node('p',note.text,root);if(note.rect){const b=node('button','Locate in image',root);b.className='locate';b.onclick=async()=>{$('#reference').close();if(state.view==='text')await setView('image');const article=document.querySelector(`article[data-id="${p.id}"]`);if(!article)return;const s=imageState(p.id),area=article.querySelector('.image-viewport');s.fit='width';s.multiple=1;fitImage(article);const scale=article.querySelector('img').getBoundingClientRect().width/p.image_dimensions[0],r=article.querySelector('.image-region');Object.assign(r.style,{left:note.rect[0]*scale+'px',top:note.rect[1]*scale+'px',width:note.rect[2]*scale+'px',height:note.rect[3]*scale+'px'});r.hidden=false;area.scrollTop=Math.max(0,note.rect[1]*scale-area.clientHeight/3)}}}if(!p.notes?.length)node('p','No visual notes recorded.',root);if(p.corrections?.length)node('p',`${p.corrections.length} documented transcription corrections. Reviewed is a derivative; Runes retains the archived text.`,root);if(p.status_basis)node('p',p.status_basis,root);if(p.reading){const base=`index.html#/wiki/reading-${p.reading.section}`;link('How this section was decoded',base+'?section=method',root);link('Read the complete section',base,root);link('Inspect the decoding trace',base+'?section=trace',root);}if(p.embedded_payload)link('Signed OutGuess payload',`index.html#/page/${p.id}?section=embedded`,root);if(p.id==='lp1-00')link('Separate compasses collage','index.html#/wiki/illustrated-cover',root);if(p.id==='lp1-10'){node('p','The archived file carries four concatenated JPEGs. A page-only version is linked under Files.',root);link('Inspect the carrier and page-only source','index.html#/wiki/2014-sixth-onion',root);}link('Full page record',`index.html#/page/${p.id}`,root)}else if(referenceTab==='alphabet'){node('p','Gematria Primus · label / prime',root);const grid=node('div',undefined,root);grid.className='alphabet';for(const item of db.alphabet){const cell=node('div',undefined,grid);node('strong',item.rune,cell);node('small',`${item.latin} / ${item.prime}`,cell)}node('h3','Archive separators',root);node('p','- word · / line · . clause · & paragraph · $ segment · § chapter · % page. These are transcription conventions.',root)}else{link(p.release==='LP2'?'Wiki JPEG':p.id==='lp1-10'?'Four-page carrier JPEG':'Original JPEG',`images/${p.id}.jpg`,root).download='';if(p.release==='LP2')link('2014 archived JPEG',`exports/sources/cicada-2014-seventh-onion/${p.release_index}.jpg`,root).download='';if(p.id==='lp1-10')link('Page-only JPEG','exports/sources/cicada-2014-sixth-onion/10-page.jpg',root).download='';link('Page data',`data/pages/${p.id}.json`,root);link('All files and checksums',`index.html#/downloads/${p.id}`,root);node('h3','Image SHA-256',root);node('code',p.image_sha256,root);node('p',p.image_dimensions.join(' × ')+' pixels',root);node('h3','Image sources',root);for(const source of p.sources||[]){try{const url=new URL(source.url);if(['https:','http:'].includes(url.protocol))link(source.name||url.hostname,url.href,root)}catch{}}}}
try{const share=Number(localStorage.getItem('liberpedia-manuscript-reader-split'));if(share>=30&&share<=70)$('#flow').style.setProperty('--image-share',share)}catch{}
let optionsRequestVersion=0;
async function openOptions(){
 const request=++optionsRequestVersion,id=state.id,navigation=navigationVersion,focus=document.activeElement;
 const current=()=>request===optionsRequestVersion&&id===state.id&&navigation===navigationVersion&&document.activeElement===focus&&!$$('dialog[open]').length;
 try{
  const page=await getPage(id);
  if(!current())return;
  updateVersions(page);updateBar();$('#options').showModal();
 }catch{if(current())toast('Page options unavailable.')}
}
$('#search-layer').onchange=()=>{finderCommitVersion++;refreshFinder()};$('#search-cancel').onclick=()=>{finderCommitVersion++;queryVersion++;searchController?.abort();$('#search-cancel').hidden=true;message('Search cancelled.');$('#query').focus()};$('#goto').onclick=openFinder;$('#finder-close').onclick=()=>$('#finder').close();bindFinder();
$('#prev').onclick=()=>turn(-1);$('#next').onclick=()=>turn(1);$$('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));$$('[data-navigation]').forEach(b=>b.onclick=()=>setNavigation(b.dataset.navigation));$('#options-button').onclick=openOptions;$('#options-close').onclick=()=>$('#options').close();$('#clear-range').onclick=()=>{state.range=null;render()};$('#numbering').onchange=()=>{state.numbers=$('#numbering').checked;persist();for(const el of $$('article.page'))if(cache.has(el.dataset.id))drawText(el,cache.get(el.dataset.id))};$('#wrapping').onchange=()=>{state.wrap=$('#wrapping').checked;persist();for(const el of $$('article.page'))if(cache.has(el.dataset.id))drawText(el,cache.get(el.dataset.id))};$('#size').oninput=()=>{state.size=Number($('#size').value);document.body.style.setProperty('--size',state.size+'px');persist()};
for(const [id,fit] of [['fit-page','page'],['fit-width','width']])$('#'+id).onclick=()=>{const settings=imageState(state.id);settings.fit=fit;settings.multiple=1;const article=document.querySelector(`article[data-id="${state.id}"]`);if(article)fitImage(article);$('#options').close()};for(const [id,factor] of [['zoom-in',1.3],['zoom-out',1/1.3]])$('#'+id).onclick=()=>{const article=document.querySelector(`article[data-id="${state.id}"]`);if(article)zoomImage(article,factor);$('#options').close()};
$('#copy-text').onclick=async()=>{try{await navigator.clipboard.writeText(originalText(await getPage(state.id)));toast('Page text copied');$('#options').close()}catch{toast('Copy is unavailable. Select the text to copy.')}};$('#full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();$('#options').close()}catch{toast('Fullscreen is unavailable.')}};$('#reference-button').onclick=()=>{$('#options').close();$('#reference').showModal();renderReference()};$('#reference-close').onclick=()=>$('#reference').close();$$('[data-tab]').forEach(b=>b.onclick=()=>{referenceTab=b.dataset.tab;renderReference()});
$('#copy-location').onclick=async()=>{try{const url=new URL(location.href);url.hash=encodeURIComponent(A.short(state.target));await navigator.clipboard.writeText(url.href);toast('Location link copied')}catch{toast('Copy is unavailable.')}};$('#clear-selection').onclick=()=>{state.target=null;updateSelection();for(const el of $$('article.page'))if(cache.has(el.dataset.id))drawText(el,cache.get(el.dataset.id));history.replaceState(null,'','#'+encodeURIComponent(A.short(addressOf(state.id))))};
for(const [id,returnTo] of [['finder','goto'],['options','options-button'],['reference','options-button']])$('#'+id).addEventListener('close',()=>$('#'+returnTo).focus());
document.addEventListener('keydown',e=>{if(e.key==='Escape'){const open=$$('dialog[open]').at(-1);if(open){e.preventDefault();open.close()}return}if(e.target.closest('input,textarea,select,dialog,[role=separator],[contenteditable=true]')||e.altKey)return;if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openFinder();return}if(e.metaKey||e.ctrlKey)return;if(e.key==='/'){e.preventDefault();openFinder()}if((e.key==='ArrowLeft'||e.key==='ArrowRight')&&ownsHorizontalArrows(e.target))return;if(e.key==='ArrowLeft'){e.preventDefault();turn(-1)}if(e.key==='ArrowRight'){e.preventDefault();turn(1)}});
function updateActivePage(){if(restoring||state.navigation!=='scroll')return;const boundary=$('#viewport').getBoundingClientRect().top+Math.min(180,innerHeight*.22);let current=$$('article.page')[0];for(const el of $$('article.page')){if(el.getBoundingClientRect().top<=boundary)current=el;else break}if(current&&current.dataset.id!==state.id){remember();state.id=current.dataset.id;updateBar();if(cache.has(state.id))updateVersions(cache.get(state.id));if(!state.target?.lines)history.replaceState(null,'','#'+encodeURIComponent(A.short(addressOf(state.id))));remember()}}
$('#viewport').addEventListener('scroll',()=>{if(restoring||state.navigation!=='scroll')return;remember();clearTimeout(scrollTimer);scrollTimer=setTimeout(updateActivePage,90)},{passive:true});
let hiddenResponsiveFocus=null;
function rememberResponsiveFocus(event){const target=event.target;if(!target?.getClientRects)return;hiddenResponsiveFocus=!event.relatedTarget&&!target.getClientRects().length?{target,text:!!target.closest('.text-cell')}:null}
document.addEventListener('focusout',rememberResponsiveFocus);
function fitReaderViewport(){
 if(innerWidth<=760&&state.view==='compare'){
  const focused=document.activeElement,restorable=hiddenResponsiveFocus?.target;
  const fallback=(!focused||focused===document.body)&&restorable?.isConnected?hiddenResponsiveFocus:null;
  const text=!!focused?.closest?.('.text-cell')||!!fallback?.text,oldFocus=fallback?.target||focused;
  state.view=text?'text':'image';
  render(false,false).then(()=>{if(oldFocus?.matches?.('[data-view="compare"]'))$(`[data-view="${state.view}"]`)?.focus({preventScroll:true});else if(oldFocus?.closest?.('article.page'))document.querySelector(`article[data-id="${state.id}"] .${text?'text':'image'}-viewport`)?.focus({preventScroll:true})});
 }else render(false,false);
 hiddenResponsiveFocus=null;
}
let resize;window.addEventListener('resize',()=>{restoring=true;clearTimeout(scrollTimer);clearTimeout(resize);resize=setTimeout(fitReaderViewport,120)});
async function fromHash(){
 let raw;try{raw=decodeURIComponent(location.hash.slice(1))}catch{raw='invalid'}
 const [base,query='']=raw.split('?'),params=new URLSearchParams(query),legacy=/^(lp[12])-(\d{2})$/i.exec(base);
 const target=legacy?A.parse(legacy[1]+' '+legacy[2]+(params.has('line')?':'+params.get('line'):'')+(params.has('word')?':'+params.get('word'):''),'LP2'):A.parse(base||state.id,'LP2');
 if(target&&!target.error){
  if(['image','text','compare'].includes(params.get('view')))state.view=innerWidth<=760&&params.get('view')==='compare'?'image':params.get('view');
  if(['continuous','single'].includes(params.get('navigation')))state.navigation=params.get('navigation')==='continuous'?'scroll':'turn';
  let version=params.get('version');if(version==='reading')version=params.get('reading')==='context'?'context':'literal';
  const isMatch=params.has('match')||params.has('textmatch'),destination=isMatch?{...target,lines:null,words:null}:target;
  const hash=location.hash;if(await go(destination,{history:false})){if(location.hash!==hash)return;
   if(['raw','latin','reviewed','literal','context','visible'].includes(version)&&(!target.lines||isMatch)){state.mode=version;await render();}
   if(isMatch){const range=(params.get('match')||params.get('textmatch')).split('-').map(Number);state.match={page:state.id,line:params.has('match')?Number(params.get('line')):null,start:range[0],end:range[1]};revealMatch();}
   return;
  }
 }else if(raw)toast('Invalid location. Showing the last page.');
 if(location.hash.slice(1)!==encodeURIComponent(raw)&&location.hash.slice(1)!==raw){try{if(decodeURIComponent(location.hash.slice(1))!==raw)return}catch{return}}
 await go(addressOf(state.id),{history:false});
}
window.addEventListener('hashchange',()=>fromHash());window.readerFocus={state,getPage,go,search,cache,setView,setNavigation,render,remember};
(async()=>{try{db=await fetchJSON('data/index.json');if(!location.hash){try{const last=sessionStorage.getItem('manuscript-reader-last-page');if(db.pages.some(p=>p.id===last))state.id=last}catch{}}await fromHash()}catch{$('#flow').replaceChildren();node('p','Manuscript index unavailable. Reload to retry.',$('#flow'));link('Static index','reference/index.html',$('#flow'))}})();
})();
