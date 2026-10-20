/* Authored reference articles. Never treated as completed experiment records. */
const guideCategories = [
 {title:'Getting started',id:'getting-started',legacy:[0],description:'Learn the page conventions, run the scripts, and record work that others can reproduce.'},
 {title:'Complete known readings',id:'known-readings',legacy:[8],description:'Read each decoded section with its literal output, manuscript images, and reproduction instructions.'},
 {title:'Runes and cipher methods',id:'cipher-methods',legacy:[1],description:'Understand rune representations and follow the transformations used in known readings.'},
 {title:'Numbers and arithmetic',id:'numbers',legacy:[2],description:'Distinguish prime values, indices, sums, and arithmetic functions before using them in a proposal.'},
 {title:'Analysis and reproduction',id:'analysis',legacy:[5],description:'Measure rune distributions and repeats, understand what a statistic can show, and reproduce the calculation.'},
 {title:'Hidden content and verification',id:'hidden-content',legacy:[3],description:'Extract embedded messages, follow the earlier puzzle chains, and verify files and signatures.'},
 {title:'Page studies',id:'page-studies',legacy:[],description:'Inspect particular headings, number panels, title images, and unresolved page details.'},
 {title:'Philosophy and literary references',id:'philosophy',legacy:[4],description:'Compare manuscript passages and outside works, keeping interpretation separate from source attribution.'},
 {title:'Artwork and visual features',id:'artwork',legacy:[6,7],description:'Find a drawing or motif, inspect the preserved image, and follow the evidence for artwork identifications.'}
];
function wikiPage(id='') {
 const articles=db.articles;
 if(!id){
 const known=new Set(guideCategories.map(g=>g.title));
 const extra=[...new Set(articles.map(a=>a.category||'Reference'))].filter(g=>!known.has(g));
 const groups=[...guideCategories,...extra.map((title,i)=>({title,id:`other-${i}`,legacy:[],description:''}))].filter(g=>articles.some(a=>(a.category||'Reference')===g.title));
 return head('Guides and methods','Background, worked examples, and reproduction instructions')+
 `<article class="reading-width"><p>New to the manuscript? Begin with <a href="#/wiki/quick-start">Start solving</a>. Follow a known result, look up an unfamiliar term, or learn how to preserve evidence.</p><nav class="section-nav" aria-label="Guide categories">${groups.map(g=>`<a href="#/wiki?section=guides-${g.id}" data-anchor="guides-${g.id}">${esc(g.title)}</a>`).join('')}</nav>${groups.map(g=>`<section id="guides-${g.id}">${g.legacy.map(i=>`<span id="guide-group-${i}" class="guide-category-alias" aria-hidden="true"></span>`).join('')}<h2>${esc(g.title)}</h2>${g.description?`<p>${esc(g.description)}</p>`:''}<dl class="article-directory guide-directory">${articles.filter(a=>(a.category||'Reference')===g.title).map(a=>`<div><dt><a href="#/wiki/${a.id}">${esc(a.title)}</a></dt><dd>${esc(a.summary)}</dd></div>`).join('')}</dl></section>`).join('')}${footer()}</article>`;
 }
 const a=articles.find(a=>a.id===id);
 if(!a)throw Error('This guide does not exist. Open Guides and methods to find an article.');
 const doc=new DOMParser().parseFromString(a.html,'text/html');
 const headings=[...doc.querySelectorAll('h2[id]')];
 doc.querySelectorAll('pre').forEach((pre,i)=>{
  const wrapper=doc.createElement('div');wrapper.className='copyable-block';
  const tools=doc.createElement('div');tools.className='block-tools';
  const status=doc.createElement('span');status.setAttribute('role','status');
  const button=doc.createElement('button');button.type='button';button.dataset.copyBlock='';
  button.textContent='Copy';button.setAttribute('aria-label',`Copy text block ${i+1}`);
  tools.append(status,button);pre.replaceWith(wrapper);wrapper.append(tools,pre);
 });
 const backlinks=articles.filter(b=>b.id!==id&&b.linked_articles?.includes(id));
 return head(a.title,esc(a.summary),'Guides and methods')+`<div class="article-grid"><article class="wiki-article">
 <p class="small"><a href="#/wiki">All guides</a> · <a href="reference/articles/${id}.html">Standalone page</a> · <a href="reference/articles/${id}.txt" download>Download text</a></p>
 <details class="mobile-article-contents"><summary>On this page</summary>${headings.map(h=>`<a href="#/wiki/${id}?section=${encodeURIComponent(h.id)}" data-anchor="${h.id}">${esc(h.textContent)}</a>`).join('')}</details>
 ${doc.body.innerHTML}${a.pages?.length?`<section><h2>Manuscript pages discussed</h2><p>${a.pages.map(id=>`<a href="#/page/${id}">${id.toUpperCase()}</a>`).join(' · ')}</p></section>`:''}${backlinks.length?`<section><h2>Guides linking here</h2><ul>${backlinks.map(b=>`<li><a href="#/wiki/${b.id}">${esc(b.title)}</a></li>`).join('')}</ul></section>`:''}${footer()}</article>
 <aside class="contents"><strong>On this page</strong>${headings.map(h=>`<a href="#/wiki/${id}?section=${encodeURIComponent(h.id)}" data-anchor="${h.id}">${esc(h.textContent)}</a>`).join('')}</aside></div>`;
}
document.addEventListener('click',async event=>{
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
 <p><a href="${r.payload_path}" download>Download full extraction</a> · <a href="${r.signed_path}" download>Signed message</a> · <a href="${r.body_path}">Message body</a></p>
 <p><a href="#/wiki/${early?'cover-chain':'embedded-payloads'}">${early?'Follow the three-image chain':'Read the payload inventory'}</a> · <a href="#/wiki/outguess">How to extract it</a> · <a href="${r.source_url}">Archived source</a></p>
 <details><summary>Exact payload checksum</summary><p class="checksum">${esc(r.payload_sha256)}</p><p class="small">SHA-256 of the full extraction. <a href="data/evidence/embedded-payloads.json">Manifest with separate signed-block and body hashes</a>.</p></details></section>`;
}
