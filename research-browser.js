'use strict';
(()=>{
 const $=id=>document.getElementById(id),svg=$('graph'),world=$('world'),map=$('map'),panel=$('inspector'),dialog=$('map-dialog');
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const readerTitle=record=>globalThis.RecordTestView?.title(record)||record.title;
 const readerBlurb=record=>globalThis.RecordTestView?.blurb(record)||'';
 const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6"/></svg>';
 const chevron='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>';
 const aliases=ResearchBrowserModel.branchLabels;
 const outcomes={supported:'Supported within scope','not-supported':'Not supported within scope',inconclusive:'Inconclusive'},resultColours={supported:'#138575','not-supported':'#7b899b',inconclusive:'#75649a'};
 let publishedBaseline=null,communityEntries=[],communityCursor=null,communityEndpoint=null,communityBusy=false,communityError='',communityPendingRender=false;
 let data,state,nodes,focus,layout=new Map(),camera={x:0,y:0,k:1},cameraViewport=null,cameraFitted=true,previous='',previousRecord='',resizeTimer,dialogReturn=null,worldHeight=600,worldBounds={x:0,y:0,width:600,height:600},labelNodes=[],indexResult,matching=new Set(),lastGraphKey='',preferredMode='list';
 const listPositions=new Map();let listKey='',questionMount=null;try{const savedMode=localStorage.getItem('liberpedia-research-mode');if(['graph','list'].includes(savedMode))preferredMode=savedMode}catch{}
 const activePointers=new Map();let gesture=null,moved=false;
 const url=next=>'#'+new URLSearchParams(Object.entries(next).filter(([,v])=>v));
 function read(){return ResearchBrowserModel.read(location.hash,preferredMode,ResearchIndex.state)}
 function navigate(changes,replace=false){if(changes.mode==='list')changes={...changes,record:''};if(listKey&&state?.mode==='list'&&!$('research-list').hidden)listPositions.set(listKey,$('research-list').scrollTop);if(changes.mode){preferredMode=changes.mode;try{localStorage.setItem('liberpedia-research-mode',changes.mode)}catch{}}if(Object.keys(changes).some(k=>['view','branch','page','q','type','method','family','result','sort','followups'].includes(k))&&!Object.hasOwn(changes,'p'))changes={...changes,p:1};const next={...state,...changes};if(url(next)===location.hash){render();return}if(replace){history.replaceState(null,'',url(next));render()}else location.hash=url(next)}
 function workFor(record){return typeof ResearchWork==='undefined'?null:ResearchWork.describe(record);}
 function recordHref(record){const work=workFor(record);return record?.community&&['unfinished','question'].includes(work?.kind)?work.href:record.href;}
 function passesRecordFilters(record){return (!state.page||record.pages.includes(state.page))&&(!state.followups||typeof ResearchWork!=='undefined'&&ResearchWork.matches(record,state.followups))}
 function workFilterLabel(value){return value==='1'?'Prepared follow-ups':value==='pending'?'Unfinished experiments':value==='questions'?'Questions to review':'';}
 function passes(id){return matching.has(id)}
 const count=n=>n.members.filter(passes).length;
 function traversalChildren(node){return node.children.map(id=>nodes.get(id)).filter(child=>child&&(!state.followups||count(child)>0));}
 function lines(label,max=14,limit=3){const words=label.split(/\s+/).flatMap(word=>word.length>max?word.match(new RegExp('.{1,'+max+'}','g')):[word]),out=[];let line='';for(const word of words){if(line&&line.length+word.length+1>max){out.push(line);line=word}else line+=(line?' ':'')+word}if(line)out.push(line);if(out.length>limit){out.length=limit;out[limit-1]=out[limit-1].slice(0,max-1)+'…'}return out}
 function branchBelow(id){let n=nodes.get(id);while(n&&n.parent!==focus.id&&n.id!==focus.id)n=nodes.get(n.parent);return n?.id===focus.id?null:n}
 function position(){
  layout=new Map();labelNodes=[];layout.set(focus.id,{x:0,y:0,a:0,r:0,depth:0,activate:focus.id});
  const children=traversalChildren(focus),step=2*Math.PI/Math.max(children.length,1),radius=Math.max(155,children.length*25);
  children.forEach((child,index)=>{
   const angle=-Math.PI/2+step*index,leaves=[];
   function collect(n){const children=traversalChildren(n);if(!children.length)leaves.push(n);else children.forEach(collect)}collect(child);
   const leafAngles=new Map(leaves.map((leaf,i)=>[leaf.id,angle+((i+.5)/leaves.length-.5)*Math.min(step*.8,.85)]));
   function visit(n,depth){const angles=traversalChildren(n).map(child=>visit(child,depth+1)),a=angles.length?angles.reduce((sum,v)=>sum+v,0)/angles.length:leafAngles.get(n.id)??angle;
    const r=radius+(depth-1)*105;layout.set(n.id,{x:Math.cos(a)*r,y:Math.sin(a)*r,a,r,depth,activate:child.id});return a}
   visit(child,1);const point=layout.get(child.id);point.a=angle;point.x=Math.cos(angle)*radius;point.y=Math.sin(angle)*radius;
  });
  const points=[...layout.values()],xs=points.map(p=>p.x),ys=points.map(p=>p.y);
  const padding=children.length>10?120:95;
  worldBounds={x:Math.min(...xs)-padding,y:Math.min(...ys)-padding,width:Math.max(...xs)-Math.min(...xs)+padding*2,height:Math.max(...ys)-Math.min(...ys)+padding*2};
  worldHeight=worldBounds.height;
 }
 function paintGraph(){
  let edges='',marks='';labelNodes=[];
  for(const [id,p] of layout){const n=nodes.get(id),parent=layout.get(n.parent),isFocus=id===focus.id,isChild=n.parent===focus.id,record=n.kind==='record',matched=count(n);
   if(parent)edges+=`<path class="edge${matched?'':' muted'}" data-parent="${esc(n.parent)}" data-child="${esc(id)}" d="M${parent.x} ${parent.y} L${p.x} ${p.y}" stroke="${state.colour==='methods'?(focus.id==='all-research'?nodes.get(p.activate)?.color||n.color:n.color):'#aab6c3'}" vector-effect="non-scaling-stroke"/>`;
   const colour=record&&!data.records[n.record_id].community&&state.colour==='results'?resultColours[data.records[n.record_id].outcome]:(focus.id==='all-research'?nodes.get(p.activate)?.color||n.color:n.color);
   const label=lines(isFocus?n.label:aliases[n.id]||n.label.replace(/^LP[12][^:]{0,30}:\s*/,''),isFocus?24:22,isFocus?2:3);
   labelNodes.push({id,p,n,isFocus,isChild,record,matched,label});
   marks+=`<g class="node ${record?'record':''} ${isFocus?'aim':''} ${matched?'':'muted'} ${n.record_id===state.record?'selected':''}" data-node="${esc(id)}" aria-hidden="true" aria-label="${esc(n.label+(record?'':', '+matched+' records'))}"><title>${esc(n.label)}</title><circle class="hit" cx="${p.x}" cy="${p.y}" r="0"/>${n.record_id===state.record?`<circle class="selection" cx="${p.x}" cy="${p.y}" r="0" vector-effect="non-scaling-stroke"/>`:''}${!isFocus?`<circle class="mark" cx="${p.x}" cy="${p.y}" r="0" fill="${colour}" vector-effect="non-scaling-stroke"/>`:''}<g class="node-label"><rect class="label-hit" width="0" height="0"/><text>${label.map((line,i)=>`<tspan x="0" dy="${i?'1.2em':'0'}">${esc(line)}</tspan>`).join('')}</text>${!record?`<text class="count">${matched} records</text>`:''}</g></g>`;
  }
  world.innerHTML=edges+marks+'<g class="labels-layer"></g>';
  labelNodes.forEach(item=>{item.element=world.querySelector(`[data-node="${CSS.escape(item.id)}"]`);item.group=item.element.querySelector('.node-label');item.group.setAttribute('data-node',item.id);item.group.setAttribute('aria-hidden','true');world.querySelector('.labels-layer').appendChild(item.group);});
 }
 function applyCamera(){
  const syncAccessibility=()=>{for(const {element} of labelNodes)element.setAttribute('aria-hidden',String(element.getAttribute('tabindex')!=='0'));};
  const restoreFocus=()=>{const active=document.activeElement;if(!map.hidden&&!map.inert&&labelNodes.some(item=>item.element===active)&&active.getAttribute('tabindex')!=='0')map.focus({preventScroll:true})};
  const G=ResearchGraphGeometry,k=camera.k,r=map.getBoundingClientRect();
  world.setAttribute('transform',`translate(${camera.x} ${camera.y}) scale(${k})`);
  const occupied=[],candidates=[],markerBoxes=[];
  const controls=map.querySelector('.map-controls').getBoundingClientRect();
  occupied.push({x:controls.x-r.x-6,y:controls.y-r.y-6,width:controls.width+12,height:controls.height+12});
  const reserve=element=>{if(!element||element.hidden||getComputedStyle(element).display==='none')return;const box=element.getBoundingClientRect(),left=Math.max(0,box.left-r.left),top=Math.max(0,box.top-r.top),right=Math.min(r.width,box.right-r.left),bottom=Math.min(r.height,box.bottom-r.top);if(right>left&&bottom>top)occupied.push({x:left-6,y:top-6,width:right-left+12,height:bottom-top+12})};
  reserve(panel);reserve($('about-button'));reserve($('result-key'));
  const ordered=[...labelNodes].sort((a,b)=>a.p.depth-b.p.depth||a.id.localeCompare(b.id));
  for(const item of ordered){
   const {element,group,p,isFocus,isChild,n,record,matched}=item,x=camera.x+p.x*k,y=camera.y+p.y*k;
   const markerSize=isChild?6:record?2.5:4,box={x:x-markerSize,y:y-markerSize,width:markerSize*2,height:markerSize*2};
   const visible=isFocus||isChild||!markerBoxes.some(other=>G.intersects(box,other,1));
   element.querySelector('.mark')?.setAttribute('r',String(G.worldPixels(visible?markerSize:0,k)));
   element.querySelector('.selection')?.setAttribute('r',String(G.worldPixels(10,k)));
   element.querySelector('.hit').setAttribute('r',String(G.worldPixels(visible&&isChild?22:0,k)));
   element.dataset.revealed=String(visible);element.dataset.labelVisible='false';element.removeAttribute('tabindex');element.removeAttribute('role');
   if(visible&&!isFocus){markerBoxes.push(box);if(isChild&&matched&&x>=0&&x<=r.width&&y>=0&&y<=r.height&&!occupied.some(box=>x>=box.x&&x<=box.x+box.width&&y>=box.y&&y<=box.y+box.height)){element.setAttribute('tabindex','0');element.setAttribute('role','button')}}
   group.hidden=true;group.style.display='none';
   if(!visible||(!matched&&!isFocus)||(!isFocus&&!isChild&&k<.8))continue;
   const font=isFocus?17:isChild?14:13,lineHeight=font*1.2;
   const text=group.querySelector('text'),countText=group.querySelector('.count');text.style.fontSize=font+'px';text.setAttribute('x','0');text.setAttribute('y',String(font));
   text.querySelectorAll('tspan').forEach(span=>span.setAttribute('x','0'));
   if(countText){countText.style.fontSize='12px';countText.setAttribute('x','0');countText.setAttribute('y',String(item.label.length*lineHeight+17));}
   const labelHit=group.querySelector('.label-hit');labelHit.setAttribute('width','0');labelHit.setAttribute('height','0');
   group.style.display='';const measured=group.getBBox(),width=measured.width,height=measured.height+4;group.style.display='none';
   const centre=layout.get(focus.id),cx=camera.x+centre.x*k,cy=camera.y+centre.y*k;
   const outer=isChild&&focus.id==='all-research'?{x:Math.max(8,Math.min(r.width-width-8,cx+Math.cos(p.a)*(p.r*k+90)-width/2)),y:Math.max(8,Math.min(r.height-height-8,cy+Math.sin(p.a)*(p.r*k+90)-height/2))}:null;
   const placements=isFocus?[{x:x-width/2,y:y-height/2}]:[...(outer?[outer]:[]),
    {x:x+12,y:y-height/2},{x:x-width-12,y:y-height/2},{x:x-width/2,y:y-height-13},{x:x-width/2,y:y+13}];
   candidates.push({id:item.id,priority:isFocus?-2:n.record_id===state.record?-1:isChild?0:p.depth,width,height,placements});
   item.labelOffset={x:measured.x,y:measured.y};labelHit.setAttribute('x',String(measured.x-3));labelHit.setAttribute('y',String(measured.y-2));labelHit.setAttribute('width',String(width+6));labelHit.setAttribute('height',String(height+4));
  }
  if(r.width<20||r.height<20){syncAccessibility();restoreFocus();return;}
  const placed=G.placeOptionalLabels(candidates,{viewport:{x:8,y:8,width:r.width-16,height:r.height-16},occupied,gap:8}).placed;
  for(const placement of placed){const item=labelNodes.find(n=>n.id===placement.id),group=item.group;
   group.style.display='';group.hidden=false;
   group.setAttribute('transform',`translate(${(placement.x-camera.x)/k} ${(placement.y-camera.y)/k}) scale(${1/k}) translate(${-item.labelOffset.x} ${-item.labelOffset.y})`);
   item.element.dataset.labelVisible='true';if(!item.isFocus){item.element.setAttribute('tabindex','0');item.element.setAttribute('role','button');item.element.querySelector('.hit').setAttribute('r',String(G.worldPixels(22,k)));}
  }
  syncAccessibility();restoreFocus();
 }
 function availableMapHeight(){return map.getBoundingClientRect().height;}
 function revealSelection(){if(!state.record||panel.hidden||innerWidth<=900)return;const r=map.getBoundingClientRect(),point=layout.get(recordNode(state.record)?.id);if(!point)return;const x=camera.x+point.x*camera.k,y=camera.y+point.y*camera.k;if(x<32||x>r.width-32)camera.x+=r.width/2-x;if(y<32||y>r.height-32)camera.y+=r.height*.5-y;}
 function updatePreviewMode(){const reading=!panel.hidden&&innerWidth<=900;map.inert=reading;$('research-list').inert=reading;}

 function fit(){if(!state||state.mode==='list')return;const r=map.getBoundingClientRect(),h=availableMapHeight(),b=worldBounds,k=Math.min((r.width-20)/b.width,(h-20)/b.height,1.3);camera={x:(r.width-b.width*k)/2-b.x*k,y:(h-b.height*k)/2-b.y*k,k};cameraViewport={width:r.width,height:r.height};cameraFitted=true;applyCamera()}
 function reframe(){
  if(!data||!state||state.mode!=='graph')return;
  const r=map.getBoundingClientRect();if(!r.width||!r.height)return;updatePreviewMode();
  if(!cameraViewport||cameraFitted){fit();return;}
  camera.x+=(r.width-cameraViewport.width)/2;camera.y+=(r.height-cameraViewport.height)/2;
  cameraViewport={width:r.width,height:r.height};revealSelection();applyCamera();
 }
 function zoom(factor,point){cameraFitted=false;const r=map.getBoundingClientRect(),p=point||{x:r.width/2,y:r.height/2},k=Math.min(8,Math.max(.08,camera.k*factor)),ratio=k/camera.k;camera={x:p.x-(p.x-camera.x)*ratio,y:p.y-(p.y-camera.y)*ratio,k};applyCamera()}
 function recordNode(id){return [...nodes.values()].find(n=>n.record_id===id)}
 function readerLimit(value){return String(value??'').replace(/\s*(?:;\s*)?human review(?: is)? pending\.?\s*$/i,'').trim();}
 function previewScopeHTML(record){
  const text=value=>typeof value==='string'?value.trim():'',normal=value=>value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim(),parameters=text(record.scope?.parameters),excluded=Object.hasOwn(record,'research_questions')?'':text(record.scope?.exclusions),next=Object.hasOwn(record,'research_questions')?'':readerLimit(record.next_steps),limit=readerLimit(record.reader_limit||record.limitations);
  const already=[record.reader_finding||record.finding,excluded,next].map(value=>normal(text(value))).filter(Boolean),distinctLimit=limit&&!already.some(value=>value.includes(normal(limit)));
  return (distinctLimit?'<p class="record-limit"><strong>Limit:</strong> '+esc(limit)+'</p>':'')+
   (globalThis.RecordQuestionView?.render(record,{headingLevel:3})||'')+
   '<section class="record-scope"><h3>Tested bounds</h3><p>'+esc(pageRanges(record.pages))+'</p>'+(parameters?'<details class="preview-exact-settings"><summary>Exact test settings</summary><p>'+esc(parameters)+'</p></details>':'')+'</section>'+
   (excluded||next?'<section class="record-open-questions"><h3>Further checks</h3>'+(excluded?'<p><strong>Not tested:</strong> '+esc(excluded)+'</p>':'')+(next?'<p><strong>Next check:</strong> '+esc(next)+'</p>':'')+'</section>':'');
 }
 function previewFollowupsHTML(record,{secondary=false}={}){const html=globalThis.RecordQuestionView?.coversFollowups(record)?'':globalThis.RecordFollowupView?.render(record)||'';return html&&secondary?'<details class="other-prepared-checks"><summary>Other prepared checks</summary>'+html+'</details>':html;}
 function bindPreviewFollowups(record){globalThis.RecordFollowupView?.bind(panel,record);}
 function showInspector(){
  questionMount?.destroy();questionMount=null;
  const record=data.records[state.record];panel.hidden=!record;updatePreviewMode();if(!record)return;
  const labels={supported:'Supported within this test','not-supported':'Not supported by this test',inconclusive:'Inconclusive'},live=(globalThis.RecordQuestionView?.render(record)||'').includes('data-live-question=');
  panel.scrollTop=0;panel.innerHTML=`<div class="inspector-top"><button type="button" class="preview-back" aria-label="Back to map"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg>Back to map</button></div><div class="inspector-scroll"><h2 id="preview-title" tabindex="-1">${esc(readerTitle(record))}</h2>${globalThis.RecordTestView?.renderIntro(record)||''}<p class="preview-status">${esc(labels[record.outcome]||record.outcome)}</p>${record.reader_intro?'':globalThis.RecordTestView?.render(record,{headingLevel:3})||''}<h3 class="preview-heading">Result</h3><p class="record-finding">${esc(record.reader_finding||record.finding)}</p>${record.reader_intro?globalThis.RecordTestView?.render(record,{headingLevel:3})||'':''}${live?previewScopeHTML(record)+previewFollowupsHTML(record,{secondary:true}):previewFollowupsHTML(record)+previewScopeHTML(record)}</div><a class="record-open" href="${esc(recordHref(record))}">${record.community?(globalThis.ResearchWork?.isFiniteQuestion(record)?'Review question':workFor(record)?.href.startsWith('run.html#task=')?'Open unfinished experiment':'Open saved idea'):'Read full record'} ${arrow}</a>`;
  bindPreviewFollowups(record);questionMount=globalThis.RecordQuestionView?.mount?.(panel,record);panel.querySelector('.preview-back').onclick=()=>navigate({record:''},true);panel.onkeydown=event=>{if(event.key==='Escape'){event.preventDefault();navigate({record:''},true)}};
 }
 function pageRanges(pages){
  if(!pages.length)return 'Source material';const ranges=[];
  for(const release of ['lp1','lp2']){const values=[...new Set(pages.filter(id=>id.startsWith(release+'-')).map(id=>+id.slice(4)))].sort((a,b)=>a-b);
   for(let i=0;i<values.length;i++){let j=i;while(j+1<values.length&&values[j+1]===values[j]+1)j++;ranges.push(release.toUpperCase()+'-'+String(values[i]).padStart(2,'0')+(j>i?'–'+String(values[j]).padStart(2,'0'):''));i=j;}}
  return ranges.join(', ');
 }
 const sorts={title:'Title A–Z','title-desc':'Title Z–A',recent:'Recently checked'};
 function scopeLabel(record){const p=record.pages;if(!p.length)return 'Source material';if(p.length===1)return p[0].toUpperCase();return p.every((id,i)=>id.slice(0,3)===p[0].slice(0,3)&&+id.slice(4)===+p[0].slice(4)+i)?p[0].toUpperCase()+'–'+p.at(-1).slice(4):p.length+' pages'}
 function filteredChips(){
  const chips=[['q',state.q?`“${state.q}”`:''],['type',ResearchIndex.labels[state.type]],['method',indexResult.topics.get(state.method)],['family',indexResult.families.get(state.family)],['result',outcomes[state.result]],['followups',workFilterLabel(state.followups)]].filter(([,label])=>label);
  const holder=$('research-filter-chips');holder.hidden=!chips.length;holder.innerHTML=chips.map(([key,label])=>`<button data-clear-filter="${key}" aria-label="${key==='followups'?'Clear available work filter':key==='result'?'Clear result filter':'Clear '+key+' filter'}"><span>${esc(label)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button>`).join('');
  holder.querySelectorAll('[data-clear-filter]').forEach(b=>b.onclick=()=>navigate({[b.dataset.clearFilter]:'',record:''}));
  const badge=$('research-filter-count'),number=chips.length+(state.page?1:0);badge.hidden=!number;badge.textContent=number||'';
 }
 function clearFilters(){navigate({q:'',type:'',method:'',family:'',result:'',page:'',followups:'',record:''})}
 function renderList(){
  const children=traversalChildren(focus),hasBranches=children.some(n=>n.kind!=='record'),rank=new Map(indexResult.allRecords.map((r,i)=>[r.id,i]));
  if(!hasBranches)children.sort((a,b)=>(rank.get(a.record_id)??Infinity)-(rank.get(b.record_id)??Infinity));
  const container=$('research-list'),total=count(focus),noun=hasBranches?(children.every(n=>n.kind!=='record')?(children.length===1?'branch':'branches'):(children.length===1?'item':'items')):(children.length===1?'record':'records');
  listKey=JSON.stringify([state.view,focus.id,state.q,state.type,state.method,state.family,state.result,state.page,state.sort,state.followups]);
  container.innerHTML=`<div class="research-list-head"><span role="status">${children.length} ${noun} · ${total} matching ${total===1?'record':'records'}</span>${!hasBranches&&children.length?`<button id="research-sort" aria-label="Sort research">${sorts[state.sort]}${chevron}</button>`:''}</div><ul class="research-branch-list">${children.map(n=>{
   const record=n.kind==='record',r=record?data.records[n.record_id]:null,matched=count(n),colour=record&&!r?.community&&state.colour==='results'?resultColours[r?.outcome]:n.color;
   const safeColour=/^#[0-9a-f]{3,8}$/i.test(colour||'')?colour:'#64748b';
   const tag=record?(matched?'a':'span'):'button',attributes=record?(matched?`href="${esc(recordHref(r))}" data-list-record="${esc(r.id)}"`:'aria-disabled="true"'):`type="button" data-list-node="${esc(n.id)}"${matched?'':' disabled'}`;
   return `<li class="research-branch-row${matched?'':' muted'}" style="--branch-colour:${safeColour}"><${tag} class="research-branch-button" ${attributes}><span class="research-branch-mark" aria-hidden="true"></span><span class="research-branch-copy"><strong>${esc(record?readerTitle(r)||n.label:aliases[n.id]||n.label)}</strong>${record&&readerBlurb(r)?`<span class="research-row-description">${esc(readerBlurb(r))}</span>`:''}<span>${record?`${esc(scopeLabel(r))} · ${esc(r.community?CommunityResearch.label(r):outcomes[r.outcome]||r.outcome)}`:state.followups==='questions'?`${matched} ${matched===1?'question':'questions'} to review`:state.followups==='pending'?`${matched} ${matched===1?'idea':'ideas'} with unfinished experiments`:state.followups==='1'?`${matched} ${matched===1?'record':'records'} with prepared follow-ups`:`${matched} matching ${matched===1?'record':'records'}`}</span>${record&&matched&&workFor(r)?`<span class="research-work-cue">${esc(workFor(r).label)}</span>`:''}</span>${record?arrow:chevron}</${tag}></li>`;
  }).join('')}</ul>${!total?`<div class="research-empty"><h2>No matching research</h2><p>No loaded research matches these filters in this area.</p><button data-clear-all>Clear filters</button>${focus.id!==data.views[state.view].root?'<button data-search-all>Look across all research</button>':''}</div>`:''}`;
  container.querySelectorAll('[data-list-node]').forEach(button=>button.onclick=()=>{const n=nodes.get(button.dataset.listNode);if(!n||n.parent!==focus.id||!count(n))return;navigate({branch:n.id,record:''})});
  container.querySelector('[data-clear-all]')?.addEventListener('click',clearFilters);container.querySelector('[data-search-all]')?.addEventListener('click',()=>navigate({view:'all',branch:'',record:''}));
  const sortButton=container.querySelector('#research-sort');if(sortButton)sortButton.onclick=()=>{openDialog('Sort research',Object.entries(sorts).map(([id,label])=>`<button class="filter-option" data-sort="${id}" aria-pressed="${state.sort===id}">${label}</button>`).join(''),sortButton);dialog.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{closeDialog();navigate({sort:b.dataset.sort,record:''})})};
  container.scrollTop=listPositions.get(listKey)||0;
 }
 function filterMenu(){
  openDialog('Filters',`<div class="filter-menu">${[['area','Area',focus.label],['type','Record type',ResearchIndex.labels[state.type]||'All types'],['method','Method',indexResult.topics.get(state.method)||'All methods'],['result','Finding',outcomes[state.result]||'Any finding'],['followups','Available work',workFilterLabel(state.followups)||'All research']].map(([id,label,value])=>`<button data-filter-field="${id}"><span><small>${label}</small>${esc(value)}</span>${chevron}</button>`).join('')}</div><button class="quiet-action" id="reset-research-filters">Clear filters</button>`,$('research-filter-button'));
  dialog.querySelectorAll('[data-filter-field]').forEach(b=>b.onclick=()=>filterOptions(b.dataset.filterField));dialog.querySelector('#reset-research-filters').onclick=()=>{clearFilters();closeDialog()};
 }
 function filterOptions(field){
  const areas=data.views.all.nodes.filter(n=>n.parent==='all-research'),values=field==='followups'?[['','All research'],['1','Prepared follow-ups'],['pending','Unfinished experiments'],['questions','Questions to review']]:field==='area'?[['','All research'],...areas.map(n=>[n.id,n.label])]:field==='type'?[['','All types'],...Object.entries(ResearchIndex.labels)]:field==='method'?[['','All methods'],...[...indexResult.topics].sort((a,b)=>a[1].localeCompare(b[1]))]:[['','Any finding'],...Object.entries(outcomes)];
  $('map-dialog-title').textContent={area:'Research area',type:'Record type',method:'Method',result:'Finding',followups:'Available work'}[field];$('map-dialog-body').innerHTML=`<button class="quiet-action" id="back-to-filters">Back to filters</button>${field==='method'?'<label class="sr-only" for="filter-method-query">Find a method</label><input id="filter-method-query" class="find-field" type="search" placeholder="Find a method" autocomplete="off">':''}${field==='followups'?'<p class="filter-explanation">Prepared follow-ups are ready to review and run; a result may already exist. Unfinished experiments are saved community tasks without a saved result. Review saved ideas and declared searches, including work that may already answer the question. Counts cover only loaded ideas.</p>':''}<div class="filter-options"></div>`;
  const draw=query=>{dialog.querySelector('.filter-options').innerHTML=values.filter(([,label])=>!query||label.toLowerCase().includes(query.toLowerCase())).map(([id,label])=>`<button class="filter-option" data-filter-value="${esc(id)}" aria-pressed="${field==='area'?focus.id===id||(!id&&focus.id==='all-research'):state[field]===id}">${esc(label)}</button>`).join('');dialog.querySelectorAll('[data-filter-value]').forEach(b=>b.onclick=()=>{const changes=field==='area'?{view:'all',branch:b.dataset.filterValue,record:''}:{[field]:b.dataset.filterValue,record:''};navigate(changes);closeDialog()})};draw('');dialog.querySelector('#back-to-filters').onclick=filterMenu;dialog.querySelector('#filter-method-query')?.addEventListener('input',e=>draw(e.target.value));
 }
 function render(){
  const enteringGraph=state?.mode!=='graph',restoreListSortFocus=document.activeElement?.id==='research-sort';
  state=read();indexResult=ResearchIndex.select(Object.values(data.records),{q:state.q,type:state.type,method:state.method,family:state.family,outcome:state.result,sort:state.sort,page:1});state.method=indexResult.state.method;state.family=indexResult.state.family;matching=new Set(indexResult.allRecords.filter(passesRecordFilters).map(r=>r.id));const view=data.views[state.view];nodes=new Map(view.nodes.map(n=>[n.id,n]));focus=nodes.get(state.branch);if(!focus||focus.kind==='record')focus=nodes.get(view.root);
  if(state.record&&(!recordNode(state.record)||!passes(state.record)||!focus.members.includes(state.record)))state.record='';
  if(state.record&&(state.mode==='list'||data.records[state.record]?.community)){location.replace(recordHref(data.records[state.record]));return;}
  const trail=[];let n=focus;while(n){trail.unshift(n);n=nodes.get(n.parent)}
  $('map-trail').innerHTML=(state.view==='all'?'':'<button data-all-research>All research</button>'+chevron)+trail.map(n=>`<button data-branch="${esc(n.id)}"${n===focus?' aria-current="location"':''}>${esc(n.id===view.root?(state.view==='all'?'All research':n.label):n.label)}</button>`).join(chevron);
  const familyWork=$('family-work-link');if(familyWork)familyWork.hidden=!['method:feedback','method:repeating-key'].some(id=>focus.id===id||focus.id.startsWith(id+'/'));
  $('map-trail').querySelectorAll('button').forEach(button=>button.onclick=()=>navigate(button.hasAttribute('data-all-research')?{view:'all',branch:'',record:''}:{branch:button.dataset.branch===view.root?'':button.dataset.branch,record:''}));
  document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===state.view)));
  $('page-button').textContent=state.page?state.page.toUpperCase():'All pages';const keyPanel=$('result-key');keyPanel.hidden=state.colour!=='results'||!!state.result;keyPanel.innerHTML=state.result?`<span><i class="${esc(state.result)}"></i>${esc(outcomes[state.result])}</span><button aria-label="Clear result filter"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button>`:Object.entries(outcomes).map(([id,label])=>`<span><i class="${id}"></i>${esc(label.replace(' within scope',''))}</span>`).join('');keyPanel.querySelector('button')?.addEventListener('click',()=>navigate({result:''}));$('display-button').dataset.active=String(state.mode==='graph'&&state.colour==='results');
  document.body.dataset.researchMode=state.mode;map.hidden=state.mode==='list';$('research-list').hidden=state.mode!=='list';document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));filteredChips();showInspector();position();paintGraph();renderList();
  const key=JSON.stringify([state.view,focus.id,state.page,state.result,state.q,state.type,state.method,state.family,state.followups]);const graphKey=key;if(state.mode==='graph'){if(lastGraphKey!==graphKey)requestAnimationFrame(fit);else{if(previousRecord!==state.record||enteringGraph)revealSelection();applyCamera();}lastGraphKey=graphKey}if((previous!==key||previousRecord!==state.record)&&previous&&!document.querySelector('dialog[open]')){if(state.record)panel.querySelector('h2').focus({preventScroll:true});else if(state.mode==='graph')map.focus({preventScroll:true});else{$('research-list').setAttribute('tabindex','-1');$('research-list').focus({preventScroll:true})}}previous=key;previousRecord=state.record;
  if(state.mode==='list'&&restoreListSortFocus&&!document.querySelector('dialog[open]'))$('research-sort')?.focus({preventScroll:true});
  $('map-status').textContent=focus.label+': '+count(focus)+' matching '+(count(focus)===1?'record.':'records.');
  document.title=focus.label+' · Research map · Liberpedia';
 }
 function activate(id){const element=world.querySelector(`[data-node="${CSS.escape(id)}"]`),n=element?.dataset.revealed==='true'?nodes.get(id):branchBelow(id);if(!n||n.id===focus.id||!count(n))return;if(n.kind==='record'){const record=data.records[n.record_id];if(record?.community){location.assign(recordHref(record));return;}navigate({record:n.record_id});return}navigate({branch:n.id,record:''})}
 svg.addEventListener('click',event=>{if(event.detail!==0)return;const node=event.target.closest('[data-node]');if(node)activate(node.dataset.node)});
 svg.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)&&event.target.matches('[data-node]')&&event.target.getAttribute('tabindex')==='0'){event.preventDefault();activate(event.target.dataset.node)}});
 map.addEventListener('keydown',event=>{if(event.target!==map)return;const delta={ArrowLeft:[35,0],ArrowRight:[-35,0],ArrowUp:[0,35],ArrowDown:[0,-35]}[event.key];if(delta){event.preventDefault();cameraFitted=false;camera.x+=delta[0];camera.y+=delta[1];applyCamera()}else if(event.key==='Home'){event.preventDefault();fit()}});
 svg.addEventListener('wheel',event=>{event.preventDefault();const r=map.getBoundingClientRect();zoom(Math.exp(-event.deltaY*.002),{x:event.clientX-r.left,y:event.clientY-r.top})},{passive:false});
 function pointerState(){const ps=[...activePointers.values()],center={x:ps.reduce((s,p)=>s+p.x,0)/ps.length,y:ps.reduce((s,p)=>s+p.y,0)/ps.length},distance=ps.length>1?Math.hypot(ps[0].x-ps[1].x,ps[0].y-ps[1].y):0;return {center,distance}}
 svg.addEventListener('pointerdown',event=>{if(event.button!==0)return;activePointers.set(event.pointerId,{x:event.clientX,y:event.clientY});svg.setPointerCapture(event.pointerId);gesture={...pointerState(),camera:{...camera},node:event.target.closest('[data-node]')?.dataset.node};moved=activePointers.size>1});
 svg.addEventListener('pointermove',event=>{if(!activePointers.has(event.pointerId))return;activePointers.set(event.pointerId,{x:event.clientX,y:event.clientY});const next=pointerState(),dx=next.center.x-gesture.center.x,dy=next.center.y-gesture.center.y;if(Math.hypot(dx,dy)>5||activePointers.size>1){moved=true;cameraFitted=false;}const k=gesture.distance&&next.distance?Math.max(.08,Math.min(8,gesture.camera.k*next.distance/gesture.distance)):gesture.camera.k,ratio=k/gesture.camera.k,r=map.getBoundingClientRect(),origin={x:gesture.center.x-r.left,y:gesture.center.y-r.top};camera={x:origin.x-(origin.x-gesture.camera.x)*ratio+dx,y:origin.y-(origin.y-gesture.camera.y)*ratio+dy,k};applyCamera()});
 const up=event=>{const selected=gesture?.node;activePointers.delete(event.pointerId);if(activePointers.size)gesture={...pointerState(),camera:{...camera}};else if(event.type==='pointerup'&&!moved&&selected)activate(selected)};svg.addEventListener('pointerup',up);svg.addEventListener('pointercancel',up);
 $('zoom-in').onclick=()=>zoom(1.35);$('zoom-out').onclick=()=>zoom(1/1.35);$('fit').onclick=fit;
 document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>navigate({view:button.dataset.view,branch:'',record:''}));
 let helpCleanup=null;
 function clearHelp(){helpCleanup?.();helpCleanup=null;}
 function openDialog(title,html,button){clearHelp();dialogReturn=button;$('map-dialog-title').textContent=title;$('map-dialog-body').innerHTML=html;dialog.showModal();dialog.scrollTop=0}
 function closeDialog(){dialog.close();dialogReturn?.focus({preventScroll:true})}$('close-map-dialog').onclick=closeDialog;
 dialog.addEventListener('close',clearHelp);
 function helpResearch(){if(!data)return;openDialog('Help with an existing check',ResearchHelp.render(data.records),$('help-research-button'));const runtime=ResearchHelpRuntime.create({load:settings=>RecordQuestionRuntime.loadReadiness(settings),pageURL:location.href}),unbind=ResearchHelp.bind($('map-dialog-body'),data.records,{createReadiness:runtime.createReadiness});helpCleanup=()=>{unbind?.();runtime.destroy();};}
 $('help-research-button').onclick=helpResearch;
 dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeDialog()}});
 $('page-button').onclick=()=>{openDialog('Manuscript page','<button class="quiet-action" data-all-pages>All pages</button><div class="release-picker"><button data-release="2" aria-pressed="true">LP2</button><button data-release="1" aria-pressed="false">LP1</button></div><div class="page-picker"></div>',$('page-button'));
  const draw=release=>{dialog.querySelectorAll('[data-release]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.release===release)));const pages=[...new Set(Object.values(data.records).flatMap(r=>r.pages))].filter(p=>p.startsWith('lp'+release+'-')).sort();dialog.querySelector('.page-picker').innerHTML=pages.map(p=>`<button data-page="${p}" aria-label="${p.toUpperCase()}" aria-pressed="${state.page===p}">${p.slice(4)}</button>`).join('');dialog.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{closeDialog();navigate({page:b.dataset.page,record:''})})};draw(state.page?.[2]||'2');dialog.querySelectorAll('[data-release]').forEach(b=>b.onclick=()=>draw(b.dataset.release));dialog.querySelector('[data-all-pages]').onclick=()=>{closeDialog();navigate({page:'',record:''})};
 };
 $('display-button').onclick=()=>{openDialog('Display settings',`${state.mode==='graph'?`<div class="settings-label">Colour</div><div class="setting-options">${[['methods','Branches'],['results','Recorded results']].map(([id,label])=>`<button data-colour="${id}" aria-pressed="${state.colour===id}">${label}</button>`).join('')}</div>`:''}<button class="quiet-action" id="copy-map-link">Copy research link</button>`,$('display-button'));
  dialog.querySelectorAll('[data-colour]').forEach(b=>b.onclick=()=>{navigate({colour:b.dataset.colour});dialog.querySelectorAll('[data-colour]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});dialog.querySelector('#copy-map-link').onclick=async e=>{try{await navigator.clipboard.writeText(location.href);e.target.textContent='Link copied'}catch{e.target.textContent='Copy the address from your browser'}};
 };
 $('find-button').onclick=()=>{
  openDialog('Find research',`<form id="research-query-form"><label class="sr-only" for="map-find">Method, page or result</label><input id="map-find" class="find-field" type="search" placeholder="Method, page or result" value="${esc(state.q)}" autocomplete="off"><button class="search-research-submit" type="submit">Search research</button></form><div id="map-find-results"></div>`,$('find-button'));
  const field=$('map-find');field.focus();field.select();$('research-query-form').onsubmit=e=>{e.preventDefault();const q=field.value.trim();closeDialog();navigate({q,record:''})};
  field.oninput=()=>{const q=field.value.trim(),ids=new Set(focus.members),candidates=q?ResearchIndex.select(Object.values(data.records),{q,type:state.type,method:state.method,family:state.family,outcome:state.result,sort:state.sort,page:1}).allRecords.filter(r=>ids.has(r.id)&&passesRecordFilters(r)).slice(0,5):[];
   $('map-find-results').innerHTML=candidates.map(r=>`<div class="find-result"><button data-find-node="record:${esc(r.id)}">${esc(readerTitle(r))}<small>${esc(r.community?CommunityResearch.label(r):outcomes[r.outcome])}</small></button></div>`).join('')+(q&&!candidates.length?'<p>No matching records in this area and its filters.</p>':'');
   dialog.querySelectorAll('[data-find-node]').forEach(b=>b.onclick=()=>{const id=b.dataset.findNode.slice(7);closeDialog();if(state.mode==='list'||data.records[id].community)location.assign(recordHref(data.records[id]));else navigate({record:id,q:passes(id)?state.q:''})});
  };
 };
 $('about-button').onclick=()=>{openDialog('About this map',`<p>The top-level routes are editorial navigation. Below them, the method subtrees retain the existing draft classifications: method, operation, scope, experiment. The outer clusters show individual records. Tap a branch to explore it; tap an experiment to read its finding and limits.</p><p>Drag to move, pinch or use the zoom controls to look closer. Fit restores the current branch. Keyboard: Tab to a branch, Enter to open; arrow keys move the focused map.</p><p>These are related approaches, not proof that every configuration has been tested. The current registry has ${Object.values(data.records).filter(record=>!record.community).length} published records and ${data.community_count||0} community ideas. Community computations are not published experiment findings; ${data.awaiting_classification.length} await classification, and ${data.outside_selected_views.length} belong to other Cicada material.</p><p><a href="research.html#mode=list">Explore in List view</a> · <a href="data/research-map.json">Map data</a></p>`,$('about-button'))};
 function communityEndpointAllowed(config){
  const candidate=config?.communityResearchEndpoint;
  if(typeof candidate!=='string'||typeof config.endpoint!=='string')return false;
  if(/^https:\/\/[a-z0-9.-]+\/community-research$/.test(candidate)&&/^https:\/\/[a-z0-9.-]+\/ask$/.test(config.endpoint))return new URL(candidate).hostname===new URL(config.endpoint).hostname;
  try{const page=new URL(location.href),feed=new URL(candidate),worker=new URL(config.endpoint);return page.protocol==='http:'&&['localhost','127.0.0.1'].includes(page.hostname)&&feed.origin===page.origin&&worker.origin===page.origin&&feed.pathname==='/community-research'&&worker.pathname==='/ask'&&!feed.username&&!feed.password&&!feed.search&&!feed.hash&&!worker.username&&!worker.password&&!worker.search&&!worker.hash;}catch{return false;}
 }
 function communityStatus(){
  const holder=$('community-status'),text=$('community-message'),more=$('community-more'),retry=$('community-retry');
  if(!holder)return;holder.hidden=!communityError&&(!communityEndpoint||!communityCursor);
  text.textContent=communityError?'Community ideas could not be loaded. Published research is still available.':communityBusy?'Loading community ideas…':communityEntries.length+' community ideas loaded.';
  more.hidden=!communityCursor||!!communityError;more.disabled=communityBusy;retry.hidden=!communityError;retry.disabled=communityBusy;
 }
 function refreshCommunity(){
  if(dialog.open){communityPendingRender=true;return;}
  communityPendingRender=false;const active=document.activeElement,nodeId=active?.getAttribute?.('data-node'),listId=active?.dataset?.listRecord,branchId=active?.dataset?.listNode,panelFocus=panel.contains?.(active)?active?.classList?.contains('preview-back')?'.preview-back':active?.classList?.contains('record-open')?'.record-open':'h2':null;
  render();
  if(nodeId){const target=world.querySelector(`[data-node="${CSS.escape(nodeId)}"]`);if(target?.getAttribute('tabindex')==='0')target.focus({preventScroll:true});else if(!map.inert&&!map.hidden)map.focus({preventScroll:true});}
  else if(listId||branchId)$('research-list').querySelector(listId?`[data-list-record="${CSS.escape(listId)}"]`:`[data-list-node="${CSS.escape(branchId)}"]`)?.focus({preventScroll:true});
  else if(panelFocus&&!panel.hidden)panel.querySelector(panelFocus)?.focus({preventScroll:true});
 }
 async function loadCommunity(resetConfig=false){
  if(communityBusy||!publishedBaseline||typeof CommunityResearch==='undefined')return;communityBusy=true;communityError='';communityStatus();
  try{
   if(!communityEndpoint||resetConfig){const response=await fetch('data/assistant.json',{cache:'no-cache',signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error('Community configuration unavailable');const config=await response.json(),candidate=config?.communityResearchEndpoint;
    if(!candidate){communityEndpoint=null;return;}
    if(!communityEndpointAllowed(config))throw Error('Invalid community endpoint');
    communityEndpoint=candidate;
   }
   const requestedCursor=communityCursor,url=new URL(communityEndpoint);if(requestedCursor)url.searchParams.set('before',requestedCursor);
   const response=await fetch(url.href,{cache:'no-store',signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error('Community feed unavailable');const page=CommunityResearch.validate(await response.json());if(page.nextCursor&&page.nextCursor===requestedCursor)throw Error('Community cursor did not advance');
   const entries=[...new Map([...communityEntries,...page.entries].map(entry=>[entry.id,entry])).values()],merged=CommunityResearch.merge(publishedBaseline,entries);communityEntries=entries;communityCursor=page.nextCursor;data=merged;refreshCommunity();
  }catch(error){communityError=error.message;}
  finally{communityBusy=false;const more=$('community-more'),focusMore=document.activeElement===more;communityStatus();if(focusMore&&more.hidden){const target=$('community-status').hidden?(state.mode==='list'?$('research-list'):map):$('community-message');target?.setAttribute('tabindex','-1');target?.focus({preventScroll:true});}}
 }
 $('community-more').onclick=()=>loadCommunity();$('community-retry').onclick=()=>loadCommunity(!communityEndpoint);
 dialog.addEventListener('close',()=>{if(communityPendingRender)refreshCommunity()});
 let lastMapSize='';const ro=new ResizeObserver(entries=>{const r=entries[0].contentRect;if(!r.width||!r.height)return;const size=r.width+'|'+r.height;if(size===lastMapSize)return;lastMapSize=size;clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{reframe()},80)});ro.observe(map);
 $('research-filter-button').onclick=filterMenu;document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>navigate({mode:b.dataset.mode}));$('research-list').addEventListener('scroll',()=>{if(listKey&&state?.mode==='list'&&!$('research-list').hidden)listPositions.set(listKey,$('research-list').scrollTop)},{passive:true});
 window.addEventListener('hashchange',()=>{if(data)render()});
 Promise.all(['data/research-map.json','data/experiments.json'].map(url=>fetch(url,{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('The research data could not be loaded.');return r.json()}))).then(([mapData,registry])=>{publishedBaseline=ResearchBrowserModel.build(mapData,registry);data=publishedBaseline;render();if(['contribute','help'].some(key=>new URLSearchParams(location.search).get(key)==='1'))helpResearch();loadCommunity(true)}).catch(error=>{map.innerHTML=`<div class="map-error"><h2>Map unavailable</h2><p>${esc(error.message)}</p><button onclick="location.reload()">Retry</button></div>`});
})();
