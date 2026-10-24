/* Optional draft research hierarchies. No router or global event ownership. */
(function(root){
  'use strict';
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  function state(value={}){
    return {view:value.view==='analytics'?'analytics':'solving',branch:typeof value.branch==='string'?value.branch:'',page:Math.max(1,Math.floor(Number(value.page)||1))};
  }
  function href(value){const s=state(value),q=new URLSearchParams({view:s.view});if(s.branch)q.set('branch',s.branch);return '#/research-map?'+q;}
  function select(data,value){
    const s=state(value),view=data.views[s.view],nodes=new Map(view.nodes.map(n=>[n.id,n]));
    const candidate=nodes.get(s.branch),node=candidate&&candidate.kind!=='record'?candidate:nodes.get(view.root);
    s.branch=node.id===view.root?'':node.id;
    const trail=[];let cursor=node;
    while(cursor){trail.unshift(cursor);cursor=nodes.get(cursor.parent);}
    return {state:s,view,nodes,node,trail,children:node.children.map(id=>nodes.get(id)),records:node.members.map(id=>data.records[id])};
  }
  function lineage(nodes,id){
    const related=new Set();let n=nodes.get(id);
    if(!n)return related;
    const descend=node=>{related.add(node.id);node.children.forEach(child=>descend(nodes.get(child)));};descend(n);
    while(n){related.add(n.id);n=nodes.get(n.parent);}return related;
  }
  function nodeLink(n,s,data){
    const record=n.record_id&&data.records[n.record_id];
    return `<a class="rm-node ${record?'rm-leaf':''}" style="--branch-color:${esc(n.color)}" data-node="${esc(n.id)}" ${record?'':`data-branch="${esc(n.id)}"`} href="${esc(record?record.href:href({...s,branch:n.id}))}"><span class="rm-dot" aria-hidden="true"></span><span>${esc(n.label)}${record?'':`<small>${n.members.length} records · ${n.kind==='scope'?'page scope':'open branch'}</small>`}</span><span class="rm-arrow" aria-hidden="true">${record?'↗':'›'}</span></a>`;
  }
  function graph(result,data){
    const {children,node,state:s}=result,perPage=12,total=Math.ceil(children.length/perPage),page=Math.min(s.page,Math.max(total,1));
    const visible=children.slice((page-1)*perPage,page*perPage),height=Math.max(visible.length*66,100),mid=height/2;
    const paths=visible.map((child,i)=>`<path data-node="${esc(child.id)}" d="M22 ${mid} C64 ${mid} 52 ${i*66+33} 94 ${i*66+33}" stroke="${esc(child.color)}"/>`).join('');
    return `<div class="rm-graph" aria-label="Branches under ${esc(node.label)}"><div class="rm-parent" title="${esc(node.label)}"><span aria-hidden="true">●</span><span class="rm-sr">${esc(node.label)} connects to:</span></div><svg aria-hidden="true" class="rm-connectors" viewBox="0 0 110 ${height}" preserveAspectRatio="none">${paths}</svg><div class="rm-nodes">${visible.map(n=>nodeLink(n,s,data)).join('')}</div></div>${total>1?`<nav class="rm-paging" aria-label="Branch pages"><button data-page="${page-1}" ${page===1?'disabled':''}>Previous</button><span>${page} of ${total}</span><button data-page="${page+1}" ${page===total?'disabled':''}>Next</button></nav>`:''}`;
  }
  function recordList(result,data){
    if(result.node.id===result.view.root)return `<div class="rm-intro"><h2>Follow a branch</h2><p>Choose a category to see its operations, page scopes and individual records.</p><p>Each record explains what was tested and what its result can establish.</p><p class="rm-note">Nearby records are related by draft classifications. Their tests may cover different inputs and limits.</p></div>`;
    const limit=12,records=result.records;
    return `<h2>${records.length} records in this branch</h2><div class="rm-records">${records.map((r,i)=>`<article class="rm-record" ${i>=limit?'hidden':''}><h3><a href="${esc(r.href)}">${esc(r.title)}</a></h3><p>${esc(r.finding)}</p><details><summary>Scope and limits</summary><p>${esc(r.scope.representation)}</p><p>${esc(r.limitations)}</p>${r.changed_fields.includes('scope')?'<p class="rm-note">This record’s scope changed after the draft map was prepared. Its category has not been reassessed.</p>':''}</details></article>`).join('')}</div>${records.length>limit?`<button class="rm-more" data-more>Show ${Math.min(limit,records.length-limit)} more records</button><p class="rm-note rm-shown" aria-live="polite">Showing ${Math.min(limit,records.length)} of ${records.length}</p>`:''}`;
  }
  function render(data,value){
    const r=select(data,value),s=r.state;
    const tabs=['solving','analytics'].map(view=>`<a data-view="${view}" href="${esc(href({view}))}" ${s.view===view?'aria-current="page"':''}>${view==='solving'?'Solving LP2':'Research & analytics'}</a>`).join('');
    const crumbs=r.trail.map((n,i)=>i===r.trail.length-1?`<span aria-current="location" data-node="${esc(n.id)}">${esc(n.label)}</span>`:`<a data-node="${esc(n.id)}" data-branch="${esc(n.id)}" href="${esc(href({...s,branch:n.id}))}">${esc(n.label)}</a>`).join('<span class="rm-crumb-separator" aria-hidden="true">/</span>');
    const remainder=[...data.awaiting_classification,...data.outside_selected_views];
    return `<section class="research-map"><header class="rm-header"><h1>Explore the research</h1><p>Follow a research idea to the tests behind it.</p></header><nav class="rm-views" aria-label="Research map views">${tabs}</nav><p class="rm-legend"><span class="rm-draft">Draft classifications</span> Categories guide exploration; they do not establish equivalent tests.</p><nav class="rm-crumbs" aria-label="Map ancestry">${crumbs}</nav><div class="rm-layout"><section class="rm-map-panel"><div class="rm-branch-heading"><h2>${esc(r.node.label)}</h2><span>${r.node.members.length} records</span></div>${graph(r,data)}</section><section class="rm-results" aria-label="Records in selected branch">${recordList(r,data)}</section></div><footer class="rm-footer"><details><summary>About these categories · ${data.provenance.snapshot_records}-record source snapshot</summary><p>The two draft hierarchies were reviewed in the supplied design handoff. Solving attempts and research analytics are separate views. Titles and findings come from the current published records; the classification remains tied to the earlier snapshot.</p><p>${data.awaiting_classification.length} newer records await classification; ${data.outside_selected_views.length} source records are outside the selected views. <a href="#/research">Browse all ${data.provenance.current_records} records</a>.</p><ul>${remainder.map(id=>`<li><a href="${esc(data.records[id].href)}">${esc(data.records[id].title)}</a>${data.awaiting_classification.includes(id)?' · awaiting classification':''}</li>`).join('')}</ul><p class="rm-provenance">Source snapshot: <a href="https://github.com/jelliottdev/jelliottdev.github.io/commit/${esc(data.provenance.source_commit)}">${esc(data.provenance.source_commit.slice(0,12))}</a>. <a href="data/research-map.json">Map data and hashes</a>.</p></details></footer></section>`;
  }
  function mount(container,data,options={}){
    let current=state(options),destroyed=false;
    function draw(){
      const graph=container.querySelector('.rm-graph'),svg=graph?.querySelector('svg');if(!svg)return;
      const height=graph.offsetHeight,top=graph.getBoundingClientRect().top;
      svg.setAttribute('viewBox',`0 0 110 ${height}`);
      graph.querySelectorAll('.rm-node').forEach((node,i)=>{
        const box=node.getBoundingClientRect(),y=box.top-top+box.height/2;
        svg.children[i]?.setAttribute('d',`M22 ${height/2} C64 ${height/2} 52 ${y} 94 ${y}`);
      });
    }
    function paint(focus){
      if(destroyed)return;const selected=select(data,current);current=selected.state;container.innerHTML=render(data,current);
      draw();
      if(focus)container.querySelector('.rm-crumbs [aria-current]')?.focus?.();
    }
    function update(next,notify=true){current=state({...next,page:next.page||1});paint();if(notify)options.onStateChange?.({...current});}
    function click(event){
      const target=event.target.closest?.('[data-branch],[data-view],[data-page],[data-more]');if(!target||!container.contains(target))return;
      if(event.button||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
      if(target.hasAttribute('data-more')){
        const hidden=[...container.querySelectorAll('.rm-record[hidden]')];hidden.slice(0,12).forEach(el=>el.hidden=false);
        const left=hidden.length-12;if(left<=0)target.hidden=true;else target.textContent=`Show ${Math.min(12,left)} more records`;
        const total=container.querySelectorAll('.rm-record').length;container.querySelector('.rm-shown').textContent=`Showing ${total-Math.max(0,left)} of ${total}`;
        hidden[0]?.querySelector('a')?.focus();return;
      }
      event.preventDefault();
      if(target.hasAttribute('data-page')){current.page=Number(target.dataset.page);paint();return;}
      update(target.hasAttribute('data-view')?{view:target.dataset.view}:{...current,branch:target.dataset.branch,page:1});
      const heading=container.querySelector('.rm-branch-heading h2');heading.tabIndex=-1;heading.focus({preventScroll:true});
    }
    function highlight(event){
      const target=event.target.closest?.('[data-node]');if(!target||!container.contains(target))return;
      const r=select(data,current),related=lineage(r.nodes,target.dataset.node);container.querySelector('.research-map').classList.add('rm-highlighting');
      container.querySelectorAll('[data-node]').forEach(el=>el.classList.toggle('rm-related',related.has(el.dataset.node)));
    }
    function clear(){container.querySelector('.research-map')?.classList.remove('rm-highlighting');}
    function out(event){if(!event.relatedTarget||!event.relatedTarget.closest?.('[data-node]'))clear();}
    function key(event){if(event.key==='Escape')clear();}
    const listeners=[['click',click],['pointerover',highlight],['pointerout',out],['focusin',highlight],['focusout',out],['keydown',key]];
    listeners.forEach(([type,fn])=>container.addEventListener(type,fn));paint();
    const observer=typeof ResizeObserver==='function'?new ResizeObserver(draw):null;observer?.observe(container);
    return {setState(next){update(next,false);},getState(){return {...current};},destroy(){destroyed=true;observer?.disconnect();listeners.forEach(([type,fn])=>container.removeEventListener(type,fn));container.innerHTML='';}};
  }
  const api={state,href,select,lineage,render,mount};
  if(typeof module!=='undefined')module.exports=api;else root.WikiResearchMap=api;
})(globalThis);
