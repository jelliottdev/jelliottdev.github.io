// Sidebar context follows the authored category; exact navigation links win in route().
function wikiSidebarHref(id){
 const article=db.articles.find(a=>a.id===id);
 const destinations={
  'Getting started':'#/wiki/quick-start',
  'Complete known readings':'#/readings',
  'Analysis and reproduction':'#/wiki/analysis-and-measurement',
  'Philosophy and literary references':'#/wiki/philosophical-themes',
  'Artwork and visual features':'#/wiki/visual-index'
 };
 return destinations[article?.category]||null;
}
function wikiBreadcrumb(article){
 const category=db.guideCategories.find(group=>group.title===article.category);
 if(!category)return {label:'Guides and methods',href:'#/wiki'};
 const hub=wikiSidebarHref(article.id);
 return {label:category.title,href:hub&&hub!=='#/wiki/'+article.id?hub:'#/wiki?section=guides-'+category.id};
}
/* Authored reference articles. Never treated as completed experiment records. */
const wikiArticleLoads=new Map();
async function ensureWikiArticle(id){
 if(!id)return;
 const article=db.articles.find(a=>a.id===id);
 if(!article)throw Error('This guide does not exist. Open Guides and methods to find an article.');
 if(typeof article.html==='string')return;
 if(!wikiArticleLoads.has(id)){
  const pending=fetch('articles/'+(article.source||id+'.html'),{cache:'no-cache'})
   .then(response=>{if(!response.ok)throw Error('This guide could not be loaded. Please retry.');return response.text()})
   .then(body=>{article.html=body})
   .finally(()=>wikiArticleLoads.delete(id));
  wikiArticleLoads.set(id,pending);
 }
 await wikiArticleLoads.get(id);
}
function wikiPage(id='') {
 const articles=db.articles;
 if(!id){
 const guideCategories=db.guideCategories;
 const known=new Set(guideCategories.map(g=>g.title));
 const extra=[...new Set(articles.map(a=>a.category||'Reference'))].filter(g=>!known.has(g));
 const groups=[...guideCategories,...extra.map((title,i)=>({title,id:`other-${i}`,legacy:[],description:''}))].filter(g=>articles.some(a=>(a.category||'Reference')===g.title));
 return head('Guides and methods','Background, worked examples, and reproduction instructions')+
 `<article class="reading-width"><p>New to the manuscript? Begin with <a href="#/wiki/quick-start">Start solving</a>. Follow a known result, look up an unfamiliar term, or learn how to preserve evidence.</p><nav class="section-nav" aria-label="Guide categories">${groups.map(g=>`<a href="#/wiki?section=guides-${g.id}" data-anchor="guides-${g.id}">${esc(g.title)}</a>`).join('')}</nav>${groups.map(g=>`<section id="guides-${g.id}">${g.legacy.map(i=>`<span id="guide-group-${i}" class="guide-category-alias" aria-hidden="true"></span>`).join('')}<h2>${esc(g.title)}</h2>${g.description?`<p>${esc(g.description)}</p>`:''}<dl class="article-directory guide-directory">${articles.filter(a=>(a.category||'Reference')===g.title).map(a=>`<div><dt><a href="#/wiki/${a.id}">${esc(a.title)}</a></dt><dd>${esc(a.summary)}</dd></div>`).join('')}</dl></section>`).join('')}${footer()}</article>`;
 }
 const a=articles.find(a=>a.id===id);
 if(!a)throw Error('This guide does not exist. Open Guides and methods to find an article.');
 const doc=new DOMParser().parseFromString(a.html,'text/html');
 const headings=[...doc.querySelectorAll('h2[id],h3[id]')];
 const contentsGroups=[];
 headings.forEach(h=>{
  const entry={heading:h,children:[]};
  if(h.tagName==='H3'&&contentsGroups.length)contentsGroups.at(-1).children.push(entry);
  else contentsGroups.push(entry);
 });
 const contentsList=groups=>`<ul class="guide-contents-list">${groups.map(({heading:h,children})=>`<li><a href="#/wiki/${id}?section=${encodeURIComponent(h.id)}" data-anchor="${h.id}">${esc(h.textContent)}</a>${children.length?contentsList(children):''}</li>`).join('')}</ul>`;
 const contentsHTML=contentsList(contentsGroups);
 doc.querySelectorAll('pre').forEach((pre,i)=>{
  const wrapper=doc.createElement('div');wrapper.className='copyable-block';
  const tools=doc.createElement('div');tools.className='block-tools';
  const status=doc.createElement('span');status.setAttribute('role','status');
  const wrap=doc.createElement('button');wrap.type='button';wrap.dataset.wrapBlock='';
  wrap.textContent='Wrap lines';wrap.setAttribute('aria-pressed','true');
  wrap.setAttribute('aria-label',`Wrap lines in text block ${i+1}`);
  pre.tabIndex=0;pre.setAttribute('aria-label',`Text block ${i+1}`);
  const button=doc.createElement('button');button.type='button';button.dataset.copyBlock='';
  button.textContent='Copy';button.setAttribute('aria-label',`Copy text block ${i+1}`);
  tools.append(status,wrap,button);pre.replaceWith(wrapper);wrapper.append(tools,pre);
 });
 const backlinks=articles.filter(b=>b.id!==id&&b.linked_articles?.includes(id));
 const breadcrumb=wikiBreadcrumb(a);
 return head(a.title,esc(a.summary),breadcrumb.label,breadcrumb.href)+`<div class="article-grid"><article class="wiki-article">
 <p class="small"><a href="#/wiki">All guides</a> · <a href="reference/articles/${id}.html">Standalone page</a> · <a href="reference/articles/${id}.txt" download>Download text</a></p>
 <details class="mobile-article-contents"><summary>On this page</summary>${contentsHTML}</details>
 ${doc.body.innerHTML}${a.pages?.length?`<section><h2>Manuscript pages discussed</h2><p>${a.pages.map(id=>`<a href="#/page/${id}">${id.toUpperCase()}</a>`).join(' · ')}</p></section>`:''}${backlinks.length?`<section><h2>Guides linking here</h2><ul>${backlinks.map(b=>`<li><a href="#/wiki/${b.id}">${esc(b.title)}</a></li>`).join('')}</ul></section>`:''}${footer()}</article>
 <aside class="contents"><strong>On this page</strong>${contentsHTML}</aside></div>`;
}
document.addEventListener('click',async event=>{
 const wrap=event.target.closest('[data-wrap-block]');
 if(wrap){
  const block=wrap.closest('.copyable-block');
  const enabled=wrap.getAttribute('aria-pressed')!=='true';
  wrap.setAttribute('aria-pressed',String(enabled));
  block.classList.toggle('unwrapped',!enabled);
  return;
 }
 const button=event.target.closest('[data-copy-block]');if(!button)return;
 const block=button.closest('.copyable-block'),pre=block?.querySelector('pre');
 if(!pre)return;
 const status=block.querySelector('[role="status"]');
 button.disabled=true;status.textContent='';
 try{
  await navigator.clipboard.writeText(pre.textContent);
  button.textContent='Copied';status.textContent='Text copied.';
 }catch{
  button.textContent='Copy';
  status.textContent='Could not copy. Select the text and copy it manually.';
 }finally{button.disabled=false;}
});
function payloadSection(p){
 const r=db.payloads.records.find(r=>r.page===p.id);
 if(!r)return '';
 const early=['lp1-00','lp1-01','lp1-02'].includes(p.id);
 const explanation=early?'This image carries a signed hexadecimal body. Together, the cover, warning, and chapter-title bodies decode to three byte streams whose XOR reconstructs another signed message.':
 p.id==='lp1-03'?'The signed body contains “Let the text guide you,” a good-luck message, and hexadecimal JPEG data. The embedded image is separate from this visible manuscript page.':
 'The signed body contains historical instructions about a Tor hidden service, uploads, and magic squares. Read it as an archived puzzle document, not a current instruction for this site.';
 return `<section id="embedded"><h2>Embedded OutGuess content</h2><p>${explanation}</p><p>Default-key extraction reproduced ${db.payloads.verified_on}: <b>${r.payload_bytes.toLocaleString()} bytes</b>. The separated signed message verified against the <a href="#/wiki/pgp-signatures">recorded public key</a>. This verifies the message, not the entire JPEG.</p>
 <dl class="article-directory">
 <div><dt><a href="${esc(r.payload_path)}" download>Full extraction</a></dt><dd>Unchanged OutGuess output (${r.payload_bytes.toLocaleString()} bytes). Compare this file with a fresh extraction from the original JPEG.</dd></div>
 <div><dt><a href="${esc(r.signed_path)}" download>Signed message</a></dt><dd>The armored PGP block, used to verify the signature against the recorded key.</dd></div>
 <div><dt><a href="${esc(r.body_path)}">Read the message body</a> · <a href="${esc(r.body_path)}" download>Download</a></dt><dd>${early?'The hexadecimal content inside the signed message. This body file is not itself a signed block.':'The message content separated from its signature. Keep the signed message when checking authenticity.'}</dd></div>
 ${r.decoded_path?`<div><dt><a href="${esc(r.decoded_path)}" download>Decoded bytes for XOR</a></dt><dd>${r.hex_decoded_bytes.toLocaleString()} bytes decoded from the hex body. Combine these with the other two pages’ decoded streams; do not XOR the text of the hex digits.</dd></div>`:''}
 </dl>
 ${r.embedded_image_path?`<figure><a href="#/wiki/lp1-03-embedded-image"><img class="embedded-facsimile" src="${esc(r.embedded_image_path)}" loading="lazy" alt="Small JPEG decoded from LP1-03’s signed body: a row of runes and decimal digits."></a><figcaption>This image was decoded from the hidden message; it is not a crop of the manuscript. <a href="${esc(r.embedded_image_path)}" download>Download the decoded JPEG</a> · <a href="#/wiki/lp1-03-embedded-image">Read its transcription and reproduction steps</a>.</figcaption></figure>`:''}
 <p><a href="#/downloads/${p.id}">All page files, sizes and checksums</a></p>
 <p><a href="#/wiki/${early?'cover-chain':'embedded-payloads'}">${early?'Follow the three-image chain':'Read the payload inventory'}</a> · <a href="#/wiki/outguess">How to extract it</a> · <a href="${r.source_url}">Archived source</a></p>
 <details><summary>Exact payload checksum</summary><p class="checksum">${esc(r.payload_sha256)}</p><p class="small">SHA-256 of the full extraction. <a href="data/evidence/embedded-payloads.json">Manifest with separate signed-block and body hashes</a>.</p></details></section>`;
}
