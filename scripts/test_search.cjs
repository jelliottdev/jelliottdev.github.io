const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const search=require('../search-engine.js');
const root=path.join(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const db={...read('data/index.json'),articles:read('data/articles.json'),topics:read('data/topics.json')};
for(const q of ['Atba','Atbash','ATBASH']){
 const hits=search.search(db,q);
 assert.equal(hits[0].href,'#/wiki/atbash',q+' must lead with the method guide');
 assert(hits.findIndex(h=>h.href==='#/wiki/quick-start')>0,'incidental mentions must follow the subject');
}
for(const q of ['LP2-31','LP2:31','LP2 page 31'])assert.equal(search.search(db,q)[0].page.id,'lp2-31');
assert.deepEqual(search.search(db,'page 15').slice(0,2).map(h=>h.page.id),['lp1-15','lp2-15']);
assert.equal(search.search(db,'').length,0);
assert.equal(search.search(db,'zzzzzznotfound').length,0);
assert.equal(search.relevance('Atbash','', '','"atbash"'),650);
assert.equal(search.relevance('Some Wisdom','','a warning','wisdom warning'),60);
assert.equal(search.relevance('Some Wisdom','','a warning','"wisdom warning"'),0);
console.log('PASS: title/prefix ranking, page aliases, ambiguous numbering, phrases and empty results');
