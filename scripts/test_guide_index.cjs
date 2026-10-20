// Verify real article coverage and saved category destinations without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const articles = JSON.parse(fs.readFileSync(path.join(root, 'data/articles.json'), 'utf8'));
const {norm} = require('../search-engine.js');
function aliasConflicts(records) {
  const conflicts = [];
  for (const article of records) {
    for (const field of ['alias_sections', 'alias_pages']) {
      const seen = new Map();
      for (const [phrase, destination] of Object.entries(article[field] || {})) {
        const key = norm(phrase);
        const value = JSON.stringify(field === 'alias_pages' ? [...new Set(destination)].sort() : destination);
        const previous = seen.get(key);
        if (previous && previous.value !== value)
          conflicts.push(`${article.id}: ${field} has conflicting destinations for "${previous.phrase}" and "${phrase}"`);
        seen.set(key, {phrase, value});
      }
    }
  }
  return conflicts;
}
// Search ignores case, accents, repeated whitespace, and several dash variants.
// Metadata must not depend on which equivalent key happens to be listed first.
assert.equal(aliasConflicts([{id:'case',alias_sections:{'Daniel 4':'old','DANIEL 4':'new'}}]).length,1);
assert.equal(aliasConflicts([{id:'accent',alias_sections:{'Möbius':'old','mobius':'new'}}]).length,1);
assert.equal(aliasConflicts([{id:'spacing',alias_pages:{'page–detail':['lp2-01'],'PAGE_detail':['lp2-02']}}]).length,1);
assert.deepEqual(aliasConflicts([{id:'same',alias_pages:{'Two  pages':['lp2-01','lp2-02'],'two pages':['lp2-02','lp2-01']}}]),[]);
assert.deepEqual(aliasConflicts([{id:'one',alias_sections:{term:'first'}},{id:'two',alias_sections:{term:'second'}}]),[],
  'Different guides can legitimately discuss the same term');
const authored = JSON.parse(fs.readFileSync(path.join(root, 'articles/index.json'), 'utf8'));
for (const [name, records] of [['authored', authored], ['generated', articles]])
  assert.deepEqual(aliasConflicts(records), [], `${name} guide aliases must resolve unambiguously`);
console.log('PASS: normalized aliases have consistent section and page destinations');
const esc = value => String(value).replace(/[&<>"']/g, ch =>
  ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
const context = {db:{articles,guideCategories:JSON.parse(fs.readFileSync(path.join(root, 'data/guide-categories.json'), 'utf8'))}, esc, head:()=>'', footer:()=>'',
  document:{addEventListener:()=>{}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'wiki.js'), 'utf8'), context);
const html = context.wikiPage();
const directory = html.slice(html.indexOf('<section'));
for (const article of articles) {
  assert.equal(directory.split(`href="#/wiki/${article.id}"`).length - 1, 1,
    `${article.id} must appear once in the directory`);
}
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match=>match[1]);
assert.equal(new Set(ids).size, ids.length, 'Section IDs must be unique');
for (const match of html.matchAll(/data-anchor="([^"]+)"/g))
  assert(ids.includes(match[1]), `Category link ${match[1]} needs a destination`);
for (let i=0;i<9;i++)
  assert(ids.includes(`guide-group-${i}`), `Preserve old category bookmark ${i}`);
assert(html.indexOf('<section id="guides-known-readings"') <
       html.indexOf('<section id="guides-cipher-methods"'));
assert(!html.includes('<h2>Visual details</h2>'), 'Artwork should not be split into overlapping groups');
const standalone = fs.readFileSync(path.join(root, 'reference/index.html'), 'utf8');
const categoryIDs = text => [...text.matchAll(/<section id="(guides-[^"]+)"/g)].map(m=>m[1]);
assert.deepEqual(categoryIDs(standalone), categoryIDs(html),
  'Standalone and wiki category order must agree');
assert(!/<script\b/i.test(standalone), 'Standalone directory must not require JavaScript');
for (const article of articles)
  assert(standalone.includes(`href="articles/${article.id}.html"`),
    `Standalone directory must include ${article.id}`);
for (const id of categoryIDs(standalone))
  assert(standalone.includes(`href="#${id}"`), `Native category link missing: ${id}`);
// Future articles should remain visible even if their category is not configured yet.
context.db.articles = [...articles, {id:'future-guide',title:'Future guide',category:'New subject',summary:'Example'}];
assert(context.wikiPage().includes('href="#/wiki/future-guide"'));
console.log(`PASS: ${articles.length} guides, category destinations, legacy bookmarks, and unconfigured-category fallback.`);

for(const [id,href] of [['rune-entropy','#/wiki/analysis-and-measurement'],['reclining-figure','#/wiki/visual-index'],['analysis-and-measurement','#/wiki?section=guides-analysis']]){
 const article=articles.find(a=>a.id===id);
 assert.equal(context.wikiBreadcrumb(article).href,href);
 assert.equal(context.wikiBreadcrumb(article).label,article.category);
}
assert.equal(context.wikiBreadcrumb({id:'unknown',category:'Unconfigured'}).href,'#/wiki');
console.log('PASS: subject breadcrumbs return to hubs, avoid self-links, and retain a fallback');
