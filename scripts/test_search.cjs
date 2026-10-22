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
for(const q of ['LP2-31','LP2:31','LP2 page 31','LP2–31','LP2—31','LP2‑31','LP2−31','LP2 page #31','LP 2 · 31','LP2-page-31'])assert.equal(search.search(db,q)[0].page.id,'lp2-31');
for(const q of ['page 15','page #15','page # 15'])assert.deepEqual(search.search(db,q).slice(0,2).map(h=>h.page.id),['lp1-15','lp2-15']);
for(const q of ['LP2–99','LP2 page #310'])assert.equal(search.search(db,q).filter(h=>h.page).length,0,'Do not truncate or invent a page ID: '+q);
assert.equal(search.search(db,'').length,0);
assert.equal(search.search(db,'zzzzzznotfound').length,0);
assert.equal(search.relevance('Atbash','', '','"atbash"'),650);
assert.equal(search.relevance('Some Wisdom','','a warning','wisdom warning'),60);
assert.equal(search.relevance('Some Wisdom','','a warning','"wisdom warning"'),0);
console.log('PASS: title/prefix ranking, page aliases, ambiguous numbering, phrases and empty results');

// Find a page's own literal wording even when the word wraps between lines.
const lp10=db.pages.find(p=>p.id==='lp1-10'),lp11=db.pages.find(p=>p.id==='lp1-11');
for(const q of ['"circumference practices"','"three behauiars"','"within the deceptian"']){
 const hit=search.page(lp10,q);
 assert.equal(hit.type,'Known reading · line wraps joined',q);
 assert.equal(hit.section,'reading');
 assert(!hit.text.includes('/\n'));
}
assert(search.page(lp10,'"circumference practices"').score>search.page(lp11,'"circumference practices"').score,
 'The page containing the words must outrank another page sharing its contextual section');
const phrasePages=search.search(db,'"circumference practices"').filter(hit=>hit.page);
assert.equal(phrasePages[0].page.id,'lp1-10');
assert.equal(phrasePages[0].matchLabel,'literal reading');
assert.equal(phrasePages.find(hit=>hit.page.id==='lp1-11').matchLabel,'section text');
const literalOnly={id:'lp1-10',literal:lp10.literal};
assert.equal(search.page(literalOnly,'"three behaviors"'),null,'Do not expand literal spelling silently');
assert.equal(search.page(literalOnly,'"enough preservation"'),null,'Do not join text from different pages');
assert.equal(search.page(literalOnly,'CIRCU/').type,'Known reading','Keep exact archived notation searchable');
console.log('PASS: literal words and phrases span line wraps without spelling expansion or cross-page joins');

for(const [queries,id,pageIds] of [
 [['dots','black dots'],'dots',['lp2-07','lp2-33','lp2-39']],
 [['five dots'],'dots',['lp2-07','lp2-23','lp2-56']],
 [['three dots'],'dots',['lp2-33','lp2-39']],
 [['mobius','Möbius','moebius','infinity'],'mobius',['lp2-15']],
 [['cuniform','cuneiform','cuneform','wedge marks'],'cuneiform',['lp2-33','lp2-34']],
 [['compasses','compass','1033.jpg'],'illustrated-cover',[]],
 [['ioc','index of coincidence'],'index-of-coincidence',[]],
 [['mayfly','mayflies'],'insects',['lp2-24','lp2-25']],
 [['wing','detached wing'],'wing-and-tree',['lp2-27']]
]){
 for(const q of queries){
  const hits=search.search(db,q);
  assert.equal(hits[0].href,'#/wiki/'+id,`Recognized subject ${q} must lead to its article`);
  for(const pid of pageIds)assert(hits.slice(0,5).some(h=>h.page?.id===pid),`${q}: ${pid} must be directly available`);
  assert.equal(new Set(hits.filter(h=>h.page).map(h=>h.page.id)).size,hits.filter(h=>h.page).length,'No duplicate page hits');
 }
}
for(const q of ['cuni','moeb','compass'])assert(search.search(db,q).length,'Spelling variants must work while typing');
assert.equal(search.search(db,'spirals')[0].href,'#/wiki/spirals');
assert.equal(search.search(db,'branches')[0].href,'#/wiki/branches');
for(const q of ['long-haired figures','women with long hair'])assert.equal(search.search(db,q)[0].href,'#/wiki/visual-index?section=lp1-frame',q);
console.log('PASS: visual names, spelling variants, partial aliases, direct page results, and subject anchors');

// These features share broad guide categories but belong to different sheets.
// Adding the red clusters previously displaced black-dot pages for "dots".
for(const [queries,id,section,pages] of [
 [['red dots','red closing mark'],'dots','red-clusters',['lp2-22','lp2-32','lp2-55']],
 [['reclining figure','reclining figures','lying human figure','lying man','laying man'],'reclining-figure','pages',['lp1-14','lp1-15','lp1-16','lp2-22']],
 [['blurry tree'],'branches','tree-comparison',['lp2-32']],
 [['faint tree'],'branches','tree-comparison',['lp2-55']],
 [['dots below hash','hash page dots'],'dots','hash-page-dots',['lp2-56']],
 [['spread wings','spread-wing insect'],'insects','spread-wings',['lp1-05']],
]){
 for(const query of queries){
  const hits=search.search(db,query);
  assert.equal(hits[0].href,`#/wiki/${id}?section=${section}`,query);
  for(const page of pages)
   assert(hits.slice(1,5).some(hit=>hit.page?.id===page),
    `${query}: make the actual feature page ${page} directly available`);
 }
}
assert.equal(search.search(db,'infinity').filter(hit=>hit.page)[0].page.id,'lp2-15',
 'The reclining figure must not replace the crossed-loop page for infinity');
console.log('PASS: specific red-dot, figure and tree queries retain their own page destinations');

// Different squares need different destinations, even though they share a guide.
for(const [query,section,page] of [
 ['1033 square','historical','lp1-05'],
 ['mixed grid','historical','lp1-05'],
 ['3301 square','lp1-16','lp1-16']
]){
 const hits=search.search(db,query);
 assert.equal(hits[0].href,`#/wiki/magic-squares?section=${section}`,query);
 assert(hits.slice(1,5).some(hit=>hit.page?.id===page),query+' must offer the original page');
}
console.log('PASS: mixed and decimal squares open their own explanations and pages');

// Visible title text should not send readers to unrelated numbered chapters.
for(const [query,section,page] of [
 ['Intus','intus','lp1-02'], ['Chapter 1','intus','lp1-02'],
 ['chapter one','intus','lp1-02'], ['plain title page','cover','lp1-00']
]){
 const hits=search.search(db,query);
 assert.equal(hits[0].href,`#/wiki/title-pages?section=${section}`,query);
 assert(hits.slice(1,5).some(hit=>hit.page?.id===page),query+' must expose the original image record');
}
console.log('PASS: visible title wording opens its own explanation and page');

// Distinctive literary phrases and catalogue identifiers should open their explanation.
for(const [query,id,section] of [
 ['all that lives is holy','william-blake','parallel'],
 ['outward circumference','william-blake','circumference'],
 ['N05058','blake-newton','collection'],
 ['N05059','blake-nebuchadnezzar','collection'],
 ['nebuchadnezar','blake-nebuchadnezzar','subject'],
 ['Book of Daniel','blake-nebuchadnezzar','daniel'],
 ['Urizen','urizen','character'],
 ['Europe a Prophecy','blake-ancient-of-days','frontispiece'],
 ['periodic ioc','periodic-ioc','columns'],
 ['column ioc','periodic-ioc','columns'],
 ['pooled ioc','periodic-ioc','columns'],
 ['foolish consistency','emerson-self-reliance','consistency'],
 ['Emerson conformity','emerson-self-reliance','conformity'],
 ['Emerson principles','emerson-self-reliance','fortune'],
 ['koan meaning','koans','term'],
 ['White Queen','lewis-carroll','queen-scene'],
 ['six impossible things','lewis-carroll','wording']
])assert.equal(search.search(db,query)[0].href,`#/wiki/${id}?section=${section}`,query);
console.log('PASS: literary phrases, artwork identifiers, and named concepts open their sections');

for(const [queries,id,section] of [
 [['phi','φ','ϕ','φ(n)','ϕ(n)','coprime','relatively prime'],'totient','examples'],
 [['phi(prime)'],'totient','lp2'],
 [['μ','µ','μ(n)','mu(n)','square free'],'mobius-function','definition'],
 [['mod 29','modulo 29','modulo'],'modular-arithmetic','definition'],
 [['negative modulo'],'modular-arithmetic','examples'],
 [['exclusive or','exclusive-or','⊕'],'xor','operation'],
 [['π(n)','pi(n)','prime counting'],'prime-indices','directions'],
 [['nth prime','p_n'],'prime-indices','definition'],
])for(const query of queries){
 assert.equal(search.search(db,query)[0].href,`#/wiki/${id}?section=${section}`,query);
}
console.log('PASS: arithmetic names, symbol variants, and notation open the relevant definitions');
for(const [query,id,section] of [
 ['ragged grid','transposition','partial-row'],
 ['transposition padding','transposition','partial-row'],
 ['odd parity','xor','parity'],
 ['three input xor','xor','parity'],
 ['sampling without replacement','index-of-coincidence','replacement'],
 ['sampling with replacement','index-of-coincidence','replacement'],
 ['self pairs','index-of-coincidence','replacement'],
 ['connected components','image-regions','components'],
 ['diagonal pixels','image-regions','diagonal-example'],
 ['flood fill','image-regions','component-code'],
 ['crop rectangle','image-regions','coordinates'],
 ['rune count vs character count','transliteration','counting-example'],
 ['counting runes','transliteration','counting-example'],
 ['TH and NG','transliteration','counting-example'],
 ['maximum empirical entropy','rune-entropy','finite-length'],
])assert.equal(search.search(db,query)[0].href,`#/wiki/${id}?section=${section}`,query);
console.log('PASS: measurement and grid terminology opens worked examples directly');

// Concept locations follow the actual passage, including literal rune-label spellings.
for(const [query,section,pages] of [
 ['consumption','consumption',['lp1-10','lp1-11']],
 ['consumptian','consumption',['lp1-10','lp1-11']],
 ['preservation','preservation',['lp1-11','lp1-12']],
 ['preseruatian','preservation',['lp1-11','lp1-12']],
 ['adherence','adherence',['lp1-12']],
 ['dogma or reason','adherence',['lp1-12']],
 ['to belong is death','adherence',['lp1-12']],
 ['attachment','wealth',['lp1-13']],
 ['possessions','wealth',['lp1-13']],
 ['amass great wealth','wealth',['lp1-13']],
 ['never become attached','wealth',['lp1-13']],
]){
 const hits=search.search(db,query);
 assert.equal(hits[0].href,`#/wiki/consumption-preservation-adherence?section=${section}`,query);
 assert.deepEqual(hits.filter(hit=>hit.page).slice(0,pages.length).map(hit=>hit.page.id),pages,query);
}
console.log('PASS: philosophical concepts and literal spellings prioritize their actual passage pages');

// Exercise the actual header input handler with an Android-style composing event.
// This is an isolated event test, not a physical-device keyboard simulation.
const vm=require('node:vm');
function target(){return {style:{},listeners:{},attrs:{},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(name,value){this.attrs[name]=value},getBoundingClientRect(){return {bottom:100}},contains(){return false}}}
const input=target(),form=target(),panel=target();input.value='Atba';
form.append=()=>{};panel.hidden=true;
let poll=null,release=null;const docListeners={};
const sandbox={setTimeout:fn=>{release=fn;return 2},clearTimeout:()=>{release=null},location:{hash:"#/experiments"},setNavigation(){},route(){},setInterval:fn=>{poll=fn;return 1},clearInterval:()=>{poll=null},queueMicrotask:fn=>fn(),db,WikiSearch:search,esc:String,marked:String,excerpt:String,
 $:s=>({'#search':input,'#search-form':form,'#search-suggestions':panel}[s]),
 document:{createElement:()=>panel,addEventListener(name,fn){docListeners[name]=fn}},
 window:{visualViewport:{height:430,addEventListener(){}}},innerHeight:430};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'search-ui.js'),'utf8'),sandbox);
vm.runInContext('bindWikiSearch()',sandbox);
input.listeners.input({isComposing:true});
assert.equal(panel.hidden,false,'Composing input must immediately show suggestions');
assert.match(panel.innerHTML,/#\/wiki\/atbash/);
assert.equal(input.value,'Atba','Rendering must not change keyboard composition text');
assert.equal(input.attrs['aria-expanded'],'true');
input.value='';input.listeners.input({isComposing:true});
assert.equal(panel.hidden,true,'Clearing composing text must hide suggestions');
console.log('PASS: composing input shows suggestions without blur or text mutation');

// Missing or delayed IME events: changed text must still render while focused.
sandbox.document.activeElement=input;input.listeners.focus();
input.value='Atbash';poll();
assert.equal(panel.hidden,false);
assert.match(panel.innerHTML,/#\/wiki\/atbash/);
const rendered=panel.innerHTML;panel.innerHTML='unchanged';poll();
assert.equal(panel.innerHTML,'unchanged','Unchanged input must not repeat the search');
input.listeners.blur();assert.equal(poll,null,'Stop the fallback when focus leaves');
console.log('PASS: eventless value changes update while focused; unchanged text does no work');

// A mobile tap can blur the field and commit composition before click arrives.
input.blur=()=>{sandbox.document.activeElement=null;input.listeners.blur();form.listeners.focusout()};
input.value='Koa';sandbox.document.activeElement=input;input.listeners.focus();
const beforeTap=panel.innerHTML;
panel.listeners.pointerdown();input.blur();
assert.equal(panel.hidden,false,'Blur during a result gesture must not hide its target');
input.value='Koan';input.listeners.compositionend();
assert.equal(panel.innerHTML,beforeTap,'Composition completion must not replace the touched link');
docListeners.pointerup();
let prevented=false;
const anchor={getAttribute:()=> '#/wiki/reading-first-koan'};
panel.listeners.click({target:{closest:()=>anchor},preventDefault(){prevented=true}});
assert.equal(sandbox.location.hash,'#/wiki/reading-first-koan');
assert(prevented);assert.equal(panel.hidden,true);assert.equal(release,null);
// Scrolling/cancelling a gesture must never activate a result.
sandbox.document.activeElement=input;input.listeners.focus();panel.listeners.pointerdown();
input.blur();docListeners.pointercancel();release();
assert.equal(sandbox.location.hash,'#/wiki/reading-first-koan');
assert.equal(panel.hidden,true);
// Enter produces click without a preceding pointer gesture.
sandbox.document.activeElement=input;input.listeners.focus();
panel.listeners.click({target:{closest:()=>({getAttribute:()=> '#/wiki/reading-second-koan'})},preventDefault(){}});
assert.equal(sandbox.location.hash,'#/wiki/reading-second-koan');
console.log('PASS: blur/composition before tap, cancelled gestures, and keyboard activation');

assert(!search.search(db,'five dots').some(h=>h.page?.id==='lp2-33'));
assert(!search.search(db,'three dots').some(h=>h.page?.id==='lp2-07'));

// Grid arrays, arithmetic squares, and botanical borders are different subjects.
for (const [query, section] of [
 ['letter number grid','layout'], ['letters and numbers','layout'],
 ['256','counts'], ['grid repeats','repetition'], ['grid frequencies','repetition'],
 ['grid csv','downloads'], ['grid coordinates','downloads']
]) {
 const hits=search.search(db,query);
 assert.equal(hits[0].href,`#/wiki/alphanumeric-grids?section=${section}`,query);
 for (const page of ['lp2-49','lp2-50','lp2-51'])
  assert(hits.slice(1,5).some(hit=>hit.page?.id===page),query+' must expose '+page);
}
for (const query of ['plant border','plant borders','paired plants'])
 assert.equal(search.search(db,query)[0].href,'#/wiki/branches?section=paired-plants',query);
console.log('PASS: alphanumeric arrays, repeats, downloads and plant borders have distinct destinations');

// Encoding terminology must not be displaced by coincidental rune labels.
for (const [query, section] of [['base 16','encoding'],['base16','encoding'],['hex to decimal','place-values'],['0x prefix','boundaries'],['decode hex','replicate']])
 assert.equal(search.search(db,query)[0].href,`#/wiki/hexadecimal?section=${section}`,query);
for (const query of ['hex image','hex JPEG','hidden rune image']) {
 const hits=search.search(db,query);
 assert.equal(hits[0].href,'#/wiki/lp1-03-embedded-image?section=image',query);
 assert(hits.slice(1,5).some(hit=>hit.page?.id==='lp1-03'),query+' must expose the enclosing manuscript page');
}
assert.equal(search.search(db,'0x')[0].page?.id,'lp2-49','Literal grid tokens retain their manuscript match');
console.log('PASS: hex encoding terms and hidden-image searches keep distinct destinations');

for(const [query,section] of [['pilgrimage',''],['end to self','self']]){
 assert.equal(search.search(db,query)[0].href,'#/wiki/pilgrimage'+(section?'?section='+section:''),query);
}
assert(search.search(db,'command your own self').slice(0,3).some(hit=>hit.href==='#/wiki/pilgrimage?section=self'),
 'Keep the close reading beside the existing visual study of the instruction');
console.log('PASS: pilgrimage and selfhood queries open the close reading.');

for(const q of ['signpost','signposts','cross','crosses','cross-like drawings']){
 const hits=search.search(db,q);
 assert.equal(hits[0].href,'#/wiki/visual-index?section=signposts',q);
 for(const id of ['lp2-00','lp2-01','lp2-02']){
  const hit=hits.find(h=>h.page?.id===id);
  assert(hit && hits.indexOf(hit)<5 && hit.href==='#/page/'+id+'?section=details', q+' should surface the illustrated page '+id);
 }
}
console.log('PASS: signpost and cross aliases lead to their guide section and manuscript pages');

const crossPage=search.search(db,'signposts').find(h=>h.page?.id==='lp2-00');
assert.equal(crossPage.title,'LP2-00');
assert(crossPage.text.includes('Cross-like drawings'));
assert(db.pages.find(p=>p.id==='lp2-00').notes_text.includes(crossPage.text));
const noNotes=search.search({articles:[{id:'example',title:'Example guide',summary:'Not page evidence',aliases:['shape'],feature_pages:['lp2-00']}],pages:[{id:'lp2-00',title:'Page title'}]},'shape').find(h=>h.page);
assert.equal(noNotes.title,'LP2-00 · Page title');
assert(noNotes.text.startsWith('Listed in Example guide.'));
assert(!noNotes.text.includes('Not page evidence'));
console.log('PASS: feature results use page titles and recorded visual evidence, with an explicit fallback');

for(const query of ['crib','known plaintext crib','withheld text','withheld continuation','prefix match']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/candidate-readings?section=crib',query);
}
for(const query of ['missing line','image row coverage','whole line omission']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/transcription-checking?section=image-row-coverage',query);
}
for(const query of ['could my scoring method miss the answer','check my solver']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/analysis-and-measurement?section=method-controls',query);
}
console.log('PASS: crib definitions, missing-line coverage and solver checks open the relevant explanation.');

for(const query of ['U+16C2','16C2','ᛂ','extra rune','corpus alphabet','corpus symbol inventory','outside alphabet symbols','Runeberg alphabet']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/word-lengths?section=corpus-symbol-census',query);
}
console.log('PASS: corpus symbol names and alphabet differences open the complete audit section.');
for(const query of ['unchanged runes','fixed points','copied rune','zero key value','147 unchanged runes']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/interruptions?section=unchanged',query);
}
console.log('PASS: unchanged-rune and zero-shift queries reach the fixed-point distinction.');
for(const query of ['928','928 words','928-word carrier','grille','carrier midpoint']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/grille-carrier?section=carrier-928',query);
}
console.log('PASS: carrier and grille queries open the bounded carrier inventory.');
for(const query of ['word lookup','304 forms','216 repeated positions']){
 assert.equal(search.search(db,query)[0].href,'#/wiki/grille-carrier?section=word-identity',query);
}
console.log('PASS: word lookup and repeated-position counts reach the identity audit.');
assert.equal(search.search(db,'grille mask')[0].href,'#/wiki/grille-carrier?section=definition');
assert.equal(search.search(db,'grille readout')[0].href,'#/wiki/grille-carrier?section=testable-rule');

// Common reproduction questions must reach the worked step, not its broad introduction.
assert.equal(search.search(db,"Reddit post order")[0].href,"#/wiki/historical-book-codes?section=post-order","Reddit post order");
assert.equal(search.search(db,"third and fourth lines")[0].href,"#/wiki/historical-book-codes?section=post-order","third and fourth lines");
assert.equal(search.search(db,"CAMT")[0].href,"#/wiki/historical-book-codes?section=post-order","CAMT");
assert.equal(search.search(db,"CageThrottleUs")[0].href,"#/wiki/historical-book-codes?section=post-order","CageThrottleUs");
assert.equal(search.search(db,"Mabinogion replay")[0].href,"#/wiki/historical-book-codes?section=mabinogion-replay","Mabinogion replay");
assert.equal(search.search(db,"missing h")[0].href,"#/wiki/historical-book-codes?section=liber-al-replay","missing h");
assert.equal(search.search(db,"Liber AL counting")[0].href,"#/wiki/historical-book-codes?section=liber-al-replay","Liber AL counting");
assert.equal(search.search(db,"2013 book code")[0].href,"#/wiki/historical-book-codes?section=liber-al-replay","2013 book code");
assert.equal(search.search(db,"Blake counting")[0].href,"#/wiki/historical-book-codes?section=blake-replay","Blake counting");
assert.equal(search.search(db,"Voice of the Devil")[0].href,"#/wiki/historical-book-codes?section=blake-replay","Voice of the Devil");
assert.equal(search.search(db,"Blake replay")[0].href,"#/wiki/historical-book-codes?section=blake-replay","Blake replay");
assert.equal(search.search(db,"page joins")[0].href,"#/wiki/transcription-checking?section=page-joins","page joins");
assert.equal(search.search(db,"page breaks")[0].href,"#/wiki/transcription-checking?section=page-joins","page breaks");
assert.equal(search.search(db,"split words")[0].href,"#/wiki/transcription-checking?section=page-joins","split words");
assert.equal(search.search(db,"cross-page words")[0].href,"#/wiki/transcription-checking?section=page-joins","cross-page words");
assert.equal(search.search(db,"32 of 55")[0].href,"#/wiki/transcription-checking?section=page-joins","32 of 55");
assert.equal(search.search(db,"disputed runes")[0].href,"#/wiki/transcription-checking?section=coverage","disputed runes");
assert.equal(search.search(db,"contested readings")[0].href,"#/wiki/transcription-checking?section=coverage","contested readings");
assert.equal(search.search(db,"word separators")[0].href,"#/wiki/transcription-checking?section=coverage","word separators");
console.log('PASS: historical replay questions and disputed-boundary queries reach the relevant sections.');
