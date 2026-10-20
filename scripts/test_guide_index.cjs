// Verify real article coverage and saved category destinations without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const articles = JSON.parse(fs.readFileSync(path.join(root, 'data/articles.json'), 'utf8'));
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
