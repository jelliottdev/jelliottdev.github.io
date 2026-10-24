/* Shared supplied sidebar. Navigation/search only; no research or file requests. */
(function(root){
 'use strict';
 const primary=[['Home','home.html','home'],['Read the manuscript','reader.html#lp1-01','reader'],['Have we tried it?','investigate.html?v=complete-current-20261024','idea'],['Research map','research.html?v=workspace-20261024b','research'],['Guides & methods','library.html?v=workspace-20261024b#/guides','guides']];
 const secondary=[['Introduction','library.html?v=workspace-20261024b#/guide/quick-start'],['Known readings','index.html#/readings'],['Alphabet','index.html#/alphabet'],['Artwork & symbols','library.html?v=workspace-20261024b#/guide/visual-index'],['Downloads','index.html#/downloads'],['Sources','index.html#/sources']];
 const icons={menu:'M4 6.5h16M4 12h16M4 17.5h16',close:'m6 6 12 12M18 6 6 18',search:'m16 16 4 4'};
 const icon=name=>'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'+(name==='search'?'<circle cx="10.5" cy="10.5" r="6.5"/>':'')+'<path d="'+icons[name]+'"/></svg>';
 function create(doc,win=doc.defaultView){
  const trigger=doc.querySelector('.site-menu');if(!trigger||doc.getElementById('site-sidebar'))return null;
  const dialog=doc.createElement('dialog');dialog.id='site-sidebar';dialog.setAttribute('aria-label','Site navigation');
  const links=items=>items.map(([label,href,id])=>'<a href="'+href+'"'+(id?' data-site-destination="'+id+'"':'')+'>'+label+'</a>').join('');
  dialog.innerHTML='<div class="site-sidebar-head"><button type="button" class="site-close" aria-label="Close navigation">'+icon('close')+'</button><a class="site-wordmark" href="home.html">Liberpedia</a></div><div class="site-sidebar-body"><form class="site-sidebar-search" role="search"><label class="site-sr-only" for="sidebar-query">Search Liberpedia</label><input id="sidebar-query" type="search" placeholder="Search Liberpedia" required><button type="submit" aria-label="Search">'+icon('search')+'</button></form><nav class="site-primary-nav" aria-label="Main destinations">'+links(primary)+'</nav><nav class="site-secondary-nav" aria-label="Reference">'+links(secondary)+'</nav></div>';
  doc.body.append(dialog);trigger.setAttribute('aria-haspopup','dialog');
  doc.querySelector('a.skip[href="#main"]')?.addEventListener('click',event=>{const main=doc.getElementById('main');if(!main)return;event.preventDefault();main.focus({preventScroll:true});main.scrollIntoView({block:'start'})});
  const closeButton=dialog.querySelector('.site-close'),form=dialog.querySelector('form'),field=form.querySelector('input');
  field.enterKeyHint='search';field.spellcheck=false;
  function close(){if(dialog.open)dialog.close();trigger.setAttribute('aria-expanded','false');if(trigger.isConnected)trigger.focus({preventScroll:true})}
  function open(search=false){
   if(doc.querySelector('dialog[open]:not(#site-sidebar)'))return;
   if(!dialog.open){dialog.showModal();trigger.setAttribute('aria-expanded','true')}
   dialog.scrollTop=0;if(search){field.focus({preventScroll:true});field.select()}else closeButton.focus({preventScroll:true});
  }
  function active(){
   const page=doc.body.dataset.sidebarPage,hash=win.location.hash;
   let key=page==='map'||page==='research'?'research':page;
   if(page==='library')key=/^#\/(?:experiment|family)/.test(hash)?'research':'guides';
   if(page==='app')key=/^#\/(?:research|experiments)(?:[/?]|$)/.test(hash)?'research':/^#\/reader\//.test(hash)?'reader':/^#\/wiki(?:[/?]|$)/.test(hash)?'guides':'';
   dialog.querySelectorAll('[data-site-destination]').forEach(link=>{if(link.dataset.siteDestination===key)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')});
  }
  trigger.addEventListener('click',()=>open());closeButton.addEventListener('click',close);
  dialog.addEventListener('cancel',event=>{event.preventDefault();close()});
  dialog.addEventListener('close',()=>{trigger.setAttribute('aria-expanded','false');if(trigger.isConnected)trigger.focus({preventScroll:true})});
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)close()}});
  dialog.querySelectorAll('a').forEach(link=>link.addEventListener('click',event=>{if(!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&event.button===0)close()}));
  field.addEventListener('input',()=>field.setCustomValidity(''));
  form.addEventListener('submit',event=>{event.preventDefault();const query=field.value.trim();field.setCustomValidity(query?'':'Enter a search term.');if(!field.reportValidity())return;close();win.location.assign('library.html?v=workspace-20261024b#/search?q='+encodeURIComponent(query))});
  doc.addEventListener('keydown',event=>{if(event.defaultPrevented)return;if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();open(true)}});
  win.addEventListener('hashchange',active);active();return {open,close,active,dialog};
 }
 const api={primary,secondary,icon,create};if(typeof module!=='undefined')module.exports=api;else{root.SiteNavigation=api;create(root.document)}
})(globalThis);
