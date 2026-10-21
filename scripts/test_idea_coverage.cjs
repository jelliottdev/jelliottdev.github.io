const assert=require('node:assert/strict');
const fs=require('node:fs');
const Coverage=require('../idea-coverage.js');
const Search=require('../assistant-search.js');
const root=require('node:path').join(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(require('node:path').join(root,p),'utf8'));
const notes=read('data/idea-coverage.json').records;
const experiments=read('data/experiments.json').records;
const statuses=new Set(['Needs a defined rule','Partially covered','Proposed; not run']);
assert.equal(new Set(notes.map(n=>n.id)).size,notes.length);
for(const n of notes){
  assert(statuses.has(n.status),n.id);
  assert(n.needed&&n.next_test&&n.coverage,n.id);
  for(const id of n.related)assert(experiments.some(r=>r.id===id&&r.status==='published'),id);
}
for(const [query,id] of [
 ['Can I make it say whatever I want?','chosen-plaintext'],
 ['Try all operations on LP2-31','numeric-expressions'],
 ['I found a word on page 31','word-hits'],
 ['Try anagrams','anagrams'],
 ['Have we tested word sums?','sum-collisions'],
 ['Use a spiral on LP2-15','grid-choice'],
 ['Try a book key','book-selection'],
 ['Reset points on page 55','interrupters'],
 ['Compare word breaks','boundary-changes'],
 ['Ask ChatGPT to translate it','ai-readings'],
 ['Reveal a hidden image','image-processing'],
 ['Change rules whenever needed','adaptive-rules']
])assert.equal(Coverage.match(notes,query)[0]?.id,id,query);
assert.equal(Coverage.match(notes,'LP2-31').length,0);
assert.equal(Coverage.match(notes,'1301').length,0,'301 must be a whole token');
assert.equal(Coverage.match(notes,'').length,0);
assert.equal(Search.experimentDocs(notes).length,0,'Coverage notes must never become completed experiment evidence');
console.log('PASS: 12 coverage families, related published records, phrase boundaries and separation from AI evidence');

const guides=new Set(read('articles/index.json').map(r=>r.id));
for(const n of notes)assert(guides.has(n.guide),n.id);
const families=read('data/method-families.json').families;
assert.equal(new Set(families.map(f=>f.id)).size,families.length);
for(const f of families){
 assert(guides.has(f.guide),f.id);
 for(const id of f.related)assert(experiments.some(r=>r.id===id),id);
}
console.log('PASS: all method families and coverage notes link to existing guides and experiment records');

const linked=new Set(families.flatMap(f=>f.related));
for(const r of experiments.filter(r=>r.status==='published'))assert(linked.has(r.id),'Assign a method family to published experiment: '+r.id);

for(const [query,id] of [
 ['Have we tried homophonic substitution on LP2-31?','homophonic'],
 ['Could it be compression?','compression'],
 ['Try an acrostic','acrostics'],
 ['Try finite differences','differences'],
 ['Use a running key','running-key'],
 ['Use a codebook','codebooks']
])assert.equal(Coverage.families(families,query)[0]?.id,id,query);
assert.equal(Coverage.families(families,'LP2-31').length,0);
assert.equal(Search.experimentDocs(families).length,0);
const vm=require('node:vm');
const ui={IdeaCoverage:Coverage,methodFamilyRecords:families,methodFamilyUnavailable:false,ideaCoverageRecords:notes,ideaCoverageUnavailable:false,experimentRecords:experiments,esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')};
vm.createContext(ui);vm.runInContext(fs.readFileSync(require('node:path').join(root,'assistant-ui.js'),'utf8'),ui);
const emptyFamily=ui.ideaCoverageView('homophonic');
assert(emptyFamily.includes('#/wiki/method-homophonic'));
assert(emptyFamily.includes('No experiment is currently linked to this family.'));
assert(!emptyFamily.includes('Not supported within scope'));
const existingFamily=ui.ideaCoverageView('running key');
assert(existingFamily.includes('family-running-key'));
ui.methodFamilyUnavailable=true;
assert(ui.ideaCoverageView('unmatched').includes('could not be loaded'));
console.log('PASS: family-only matches expose guides, distinguish absent links from negative results, and survive index-load failures');
