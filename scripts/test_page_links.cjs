// Render actual page-related sections without a browser or hosted inference.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const db = {...read('data/index.json'), topics: read('data/topics.json'),
  articles: read('data/articles.json')};
const esc = value => String(value).replace(/[&<>"']/g, ch =>
  ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
const context = {db, esc, label: page => page.id, link: page => '#/page/' + page.id};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'research.js'), 'utf8'), context);
let topicLinks = 0;
for (const summary of db.pages) {
  const page = read('data/pages/' + summary.id + '.json');
  const rendered = context.pageResearchTools(page);
  assert(rendered.includes('Cite or share this page'), summary.id);
  for (const topic of db.topics.filter(topic =>
    topic.links.some(link => link.href.startsWith('#/page/' + summary.id)))) {
    assert(rendered.includes('href="#/topics?topic=' + topic.id + '"'),
      summary.id + ' must link to ' + topic.id);
    topicLinks++;
  }
  for (const guide of db.articles.filter(guide => guide.pages?.includes(summary.id))) {
    assert(rendered.includes('href="#/wiki/' + guide.id + '"'),
      summary.id + ' must link to guide ' + guide.id);
  }
}
assert(topicLinks > 0, 'Fixture must exercise page records with related topics');
console.log(`PASS: related guides, topics and citations render for all ${db.pages.length} page records.`);
