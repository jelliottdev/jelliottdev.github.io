const assert=require('node:assert/strict');
const fs=require('node:fs');
const Coverage=require('../idea-coverage.js');
const Search=require('../assistant-search.js');
const root=require('node:path').join(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(require('node:path').join(root,p),'utf8'));
const notes=read('data/idea-coverage.json').records;
const experiments=read('data/experiments.json').records;
const researchDocs=Search.experimentDocs(experiments);
assert.equal(Search.experiments(researchDocs,'dead tree on LP2-55').length,0);
assert.equal(Search.supporting(researchDocs,'dead tree on LP2-55')[0]?.document.id,'dead-tree-alignment');
assert(Search.experiments(researchDocs,'prime-minus-one shifts').slice(0,2).some(r=>r.document.id==='lp2-prime-minus-one-openings'));
assert.equal(Search.experiments(researchDocs,'trigram repeats on LP2-31').length,0);
assert.equal(Search.supporting(researchDocs,'trigram repeats on LP2-31')[0]?.document.id,'lp2-trigram-repeats');
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
const reported=read('data/reported-attempts.json').entries;
assert.equal(new Set(reported.map(r=>r.id)).size,reported.length);
assert.equal(Search.experimentDocs(reported).length,0,'Prior-work reports must never become completed experiment evidence');
assert.equal(Coverage.match(reported,'LP2-31').length,0,'A page mention alone must not imply a reported technique');
for(const [query,id] of [
 ['Was there a data matrix in the grid?','grid-data-matrix-report'],
 ['Try six F interrupters on pages 54-55','lanfear-six-f-interrupters'],
 ['Could QuagMirrors be the key?','quagmirrors-mobius-autokey']
])assert.equal(Coverage.match(reported,query)[0]?.id,id,query);
console.log('PASS: 12 coverage families, related published records, phrase boundaries and separation from AI evidence');

const guides=new Set(read('articles/index.json').map(r=>r.id));
for(const n of notes)assert(guides.has(n.guide),n.id);
const families=read('data/method-families.json').families;
const familyData=read('data/method-families.json');
assert.deepEqual(Object.keys(familyData.record_kind_by_id).sort(),experiments.map(r=>r.id).sort());
for(const kind of Object.values(familyData.record_kind_by_id)){
 assert(familyData.record_kinds[kind]?.label);
 assert(familyData.record_kinds[kind]?.description);
}
assert.equal(familyData.record_kind_by_id['seed-crib-controls'],'control');
assert.equal(familyData.record_kind_by_id['known-reading-languages'],'control');
assert.equal(familyData.record_kind_by_id['image-row-coverage'],'audit');
assert.equal(familyData.record_kind_by_id['literal-prime-affine'],'alphabet');
assert.equal(familyData.record_kind_by_id['totient-map-route'],'replay');
assert.equal(familyData.record_kind_by_id['emerson-book-cipher-control'],'historical');
assert.equal(familyData.record_kind_by_id['lp2-prime-minus-one-openings'],'method');
assert.equal(familyData.record_kind_by_id['doublet-context'],'measurement');
assert.equal(familyData.record_kind_by_id['dead-tree-alignment'],'audit');
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
 ['Use a codebook','codebooks'],
 ['Read every third rune on page 31','grilles'],
 ['Could a keyboard layout explain it?','symbol-systems'],
 ['Try Morse code','symbol-systems'],
 ['Read backwards','transposition'],
 ['Read in a snake pattern','routes'],
 ['Combine ciphers','composition'],
 ['Remove some runes first','null-removal'],
 ['book cipher','book-codes'],
 ['fractionation','fractionation'],
 ['transposition','transposition'],
 ['substitution','fixed-substitution'],
 ['frequency analysis','distributions'],
 ['entropy','distributions'],
 ['IoC','distributions'],
 ['block cipher','blocks'],
 ['beam search','automatic-search'],
 ['Try a SAT solver','constraints'],
 ['Use Z3 on page 31','constraints'],
 ['Try constraint solving','constraints'],
 ['Have we tried spirals?','routes'],
 ['Try acrostics on page 31','acrostics'],
 ['Take the first runes of each word','acrostics'],
 ['Try anagrams','transposition'],
 ['Reorder pages before decoding','page-order'],
 ['Compare the SHA-512 target','hashes'],
 ['Could the text be compressed?','compression'],
 ['Try 5-bit packing','compression'],
 ['Try zlib','compression'],
 ['Look for number coincidences','expressions'],
 ['Use SAT solvers','constraints'],
 ['Could it be non-English?','language'],
 ['Try a cipher disk','moving-alphabets'],
 ['Use rotors','moving-alphabets'],
 ['Could an evolving alphabet work?','moving-alphabets'],
 ['Decode odd and even positions separately','interleaving'],
 ['Try interleaved streams','interleaving'],
 ['Could spelling errors be a parity check?','error-correction'],
 ['Try an error correcting code','error-correction']
])assert.equal(Coverage.families(families,query)[0]?.id,id,query);
assert.equal(Coverage.families(families,'LP2-31').length,0);
assert.equal(Coverage.families(families,'hashish seedlings').length,0,'Aliases must match whole words, not substrings');
assert.equal(Search.experimentDocs(families).length,0);
const vm=require('node:vm');
const ui={IdeaCoverage:Coverage,methodFamilyRecords:families,methodFamilyUnavailable:false,ideaCoverageRecords:notes,ideaCoverageUnavailable:false,reportedAttemptRecords:reported,reportedAttemptsUnavailable:false,experimentRecords:experiments,esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')};
vm.createContext(ui);vm.runInContext(fs.readFileSync(require('node:path').join(root,'assistant-ui.js'),'utf8'),ui);
const emptyFamily=ui.ideaCoverageView('homophonic');
assert(emptyFamily.includes('#/wiki/method-homophonic'));
assert(emptyFamily.includes('No research record is currently linked to this family.'));
assert(!emptyFamily.includes('Not supported within scope'));
const existingFamily=ui.ideaCoverageView('running key');
assert(existingFamily.includes('family-running-key'));
ui.methodFamilyUnavailable=true;
assert(ui.ideaCoverageView('unmatched').includes('could not be loaded'));
assert(ui.reportedAttemptView('data matrix').includes('#/wiki/reported-attempts?section=grid-data-matrix-report'));
assert(!ui.reportedAttemptView('LP2-31').includes('Earlier reported approaches'));
assert(ui.reportedAttemptView('').includes('Browse the reported-attempt register'));
ui.reportedAttemptsUnavailable=true;
assert(ui.reportedAttemptView('data matrix').includes('could not be loaded'));
console.log('PASS: family-only matches expose guides, distinguish absent links from negative results, and survive index-load failures');

const detail={esc:ui.esc, records:experiments, families, familyData, head:()=>'', footer:()=>''};
vm.createContext(detail);
vm.runInContext(fs.readFileSync(require('node:path').join(root,'experiments.js'),'utf8'),detail);
vm.runInContext('experimentRecords=records; methodFamilyRecords=families; methodRecordKinds=familyData.record_kinds; methodRecordKindById=familyData.record_kind_by_id;',detail);
for(const record of experiments.filter(r=>r.status==='published')){
 const html=detail.experimentMethodGuides(record);
 const expected=families.filter(f=>f.related.includes(record.id));
 assert(expected.length>0);
 for(const f of expected){
  assert(html.includes(`#/wiki/${f.guide}`),record.id);
  assert(html.includes(`section=family-${f.id}`),record.id);
 }
 for(const f of families.filter(f=>!f.related.includes(record.id)))
  assert(!html.includes(`section=family-${f.id}\"`),record.id);
 const article=detail.experimentArticle(record);
 const kind=familyData.record_kinds[familyData.record_kind_by_id[record.id]];
 assert(article.includes(`<strong>${kind.label}</strong>`));
 assert(article.includes('section=record-types'));
 assert(article.includes('data-anchor="experiment-methods"'));
 assert(article.indexOf('id="experiment-scope"')<article.indexOf('id="experiment-methods"'));
 assert(article.indexOf('id="experiment-methods"')<article.indexOf('id="experiment-reproduce"'));
}
assert.equal(detail.experimentMethodGuides({id:'unmapped-example'}),'');
assert.equal(detail.experimentRecordType({id:'unmapped-example'}),'');
vm.runInContext(fs.readFileSync(require('node:path').join(root,'assistant-ui.js'),'utf8'),detail);
const control=experiments.find(r=>r.id==='seed-crib-controls');
assert(detail.experimentSearchResult(control).includes('<strong>Control</strong>'));
assert(detail.experimentSearchResult(control).includes('<dt>Check performed</dt>'));
const tree=experiments.find(r=>r.id==='dead-tree-alignment');
assert(!detail.experimentBrowse(experiments).split('<h3>Measurements, controls and source checks</h3>')[0].includes('dead-tree-alignment'));
assert(detail.experimentBrowse(experiments).split('<h3>Measurements, controls and source checks</h3>')[1].includes('dead-tree-alignment'));
assert(detail.experimentArticle(tree).includes('does not establish that an LP2 decoding method was tried'));
vm.runInContext('methodRecordKinds={};',detail);
assert(detail.experimentRecordType(control).includes('<strong>Control</strong>'));
vm.runInContext('methodFamilyUnavailable=true;',detail);
assert(detail.experimentMethodGuides(experiments[0]).includes('could not be loaded'));
assert(!detail.experimentMethodGuides(experiments[0]).includes('No experiment'));
console.log('PASS: every published experiment links only to assigned method families, after scope, with an index-failure fallback');
