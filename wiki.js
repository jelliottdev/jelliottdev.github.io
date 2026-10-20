/* Authored reference articles. Never treated as completed experiment records. */
function wikiPage(id='') {
 const articles=db.articles;
 if(!id){
 const groups=[...new Set(articles.map(a=>a.category||'Reference'))];
 return head('Guides and methods','Background, worked examples, and reproduction instructions')+
 `<article class="reading-width"><p>New to the manuscript? Begin with <a href="#/wiki/quick-start">Start solving</a>. Follow a known result, look up an unfamiliar term, or learn how to preserve evidence.</p><nav class="section-nav" aria-label="Guide categories">${groups.map((g,i)=>`<a href="#guide-group-${i}" data-anchor="guide-group-${i}">${esc(g)}</a>`).join('')}</nav>${groups.map((g,i)=>`<section id="guide-group-${i}"><h2>${esc(g)}</h2><dl class="article-directory guide-directory">${articles.filter(a=>(a.category||'Reference')===g).map(a=>`<div><dt><a href="#/wiki/${a.id}">${esc(a.title)}</a></dt><dd>${esc(a.summary)}</dd></div>`).join('')}</dl></section>`).join('')}${footer()}</article>`;
 }
 const a=articles.find(a=>a.id===id);
 if(!a)throw Error('This guide does not exist. Open Guides and methods to find an article.');
 const doc=new DOMParser().parseFromString(a.html,'text/html');
 const headings=[...doc.querySelectorAll('h2[id]')];
 const backlinks=articles.filter(b=>b.id!==id&&b.linked_articles?.includes(id));
 return head(a.title,esc(a.summary),'Guides and methods')+`<div class="article-grid"><article class="wiki-article">
 <p class="small"><a href="#/wiki">All guides</a> · <a href="reference/articles/${id}.html">Standalone page</a> · <a href="reference/articles/${id}.txt" download>Download text</a></p>
 <details class="mobile-article-contents"><summary>On this page</summary>${headings.map(h=>`<a href="#${h.id}" data-anchor="${h.id}">${esc(h.textContent)}</a>`).join('')}</details>
 ${a.html}${a.pages?.length?`<section><h2>Manuscript pages discussed</h2><p>${a.pages.map(id=>`<a href="#/page/${id}">${id.toUpperCase()}</a>`).join(' · ')}</p></section>`:''}${backlinks.length?`<section><h2>Guides linking here</h2><ul>${backlinks.map(b=>`<li><a href="#/wiki/${b.id}">${esc(b.title)}</a></li>`).join('')}</ul></section>`:''}${footer()}</article>
 <aside class="contents"><strong>On this page</strong>${headings.map(h=>`<a href="#${h.id}" data-anchor="${h.id}">${esc(h.textContent)}</a>`).join('')}</aside></div>`;
}
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
