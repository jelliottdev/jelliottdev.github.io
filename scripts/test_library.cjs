'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const L=require('../library.js');
const root=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const guides=read('data/article-search.json'),categories=read('data/guide-categories.json'),index=read('data/experiment-index.json');
let groups=0;const test=(name,f)=>{f();groups++;console.log('PASS '+name)};
test('production adapters preserve every live guide and record, without snapshot data',()=>{
 const original=JSON.stringify({guides,categories,index}),d=L.adaptMetadata(guides,categories,index);
 assert.deepEqual(d.guides.map(g=>g.id),guides.map(g=>g.id));
 assert.deepEqual(d.experiments.map(r=>r.id),index.records.map(r=>r.id));
 for(const r of d.experiments)assert.deepEqual(r.pages,index.records.find(x=>x.id===r.id).scope.pages);
 assert.equal(JSON.stringify({guides,categories,index}),original);
 for(const g of d.guides)assert.ok(fs.existsSync(path.join(root,L.guideSource(g))),g.id);
 assert.throws(()=>L.adaptMetadata(null,categories,index));
});
test('page ranges preserve holes, releases and exact memberships',()=>{
 assert.equal(L.compactPages(['lp2-03','lp2-01','lp2-02','lp2-05','lp1-01','lp1-01']),'LP1-01, LP2-01\u201303, LP2-05');
 assert.equal(L.compactPages([]),'Artifact-specific');
 assert.equal(L.compactPages(['bad','lp2-1']),'Artifact-specific');
});
test('file inventory retains script, input and output hashes exactly once',()=>{
 const r={script_sha256:'script-hash',reproduction:{script:'script.py',inputs:[{path:'plan.json',sha256:'p'}],outputs:[{path:'result.json',sha256:'r'},{path:'script.py',sha256:'s'}]}};
 assert.deepEqual(L.recordFiles(r),[{path:'script.py',sha256:'script-hash'},{path:'plan.json',sha256:'p'},{path:'result.json',sha256:'r'}]);
});
test('reader sections retain exact authored content and exclude fenced fake headings',()=>{
 const md='# Title\n\n## Kept\nA\n### Nested\nB\n```\n## Kept\n```\n## Other\nC';
 const s=L.readerSections(md,['Kept']);assert.equal(s.selected[0].body,'A\n### Nested\nB\n```\n## Kept\n```');assert.ok(s.remaining.includes('## Other\nC'));assert.ok(!s.remaining.includes('Nested'));
 assert.throws(()=>L.readerSections('## Same\nA\n## Same\nB',['Same']));
 assert.throws(()=>L.readerSections(md,['Missing']));
});
test('all current records keep authored sections, exact reproduction inventory and declared visuals',()=>{
 let sections=0,files=0,visuals=0;
 for(const item of index.records){
  const r=read('reference/experiments/'+item.id+'.json');
  assert.equal(r.id,item.id);assert.equal(r.status,'published');
  const extracted=L.readerSections(r.article,r.reader_sections);sections+=extracted.selected.length;
  const inventory=L.recordFiles(r);files+=inventory.length;
  assert.equal(inventory[0].path,r.reproduction.script);
  for(const f of [...r.reproduction.inputs,...r.reproduction.outputs])assert.ok(inventory.some(x=>x.path===f.path),f.path);
  for(const v of r.visuals||[]){visuals++;assert.ok(inventory.some(f=>f.path===v.path),v.path);assert.ok(fs.existsSync(path.join(root,v.path)),v.path);}
 }
 assert.ok(sections>0&&files>0&&visuals>0);console.log('Current authored inventory:',index.records.length,'records,',sections,'reader sections,',visuals,'visuals');
});
test('guide references use only explicit known record links and both library/legacy routes',()=>{
 const known=new Set(['a','b']);assert.deepEqual(L.referencedRecords('<a href="#/experiments/a">A</a><a href="#/experiment/b?tab=scope">B</a><a href="#/experiment/stale">stale</a>',known),['a','b']);
 assert.deepEqual(L.referencedRecords('Tags: a b',known),[]);
});
test('authored Markdown remains escaped and retains declared visual, table and exact command content',()=>{
 const out=L.renderMarkdown('## Source\n\n<script>alert(1)</script>\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n![Evidence](fig.svg)\n\n```\npython replay.py --inputs ../local\n```',['fig.svg']);
 assert.ok(!out.includes('<script>'));assert.ok(out.includes('&lt;script&gt;'));assert.ok(out.includes('<table>'));assert.ok(out.includes('fig.svg'));assert.ok(out.includes('python replay.py --inputs ../local'));
 assert.ok(!L.renderMarkdown('[unsafe](javascript:alert)',['javascript:alert']).includes('href="javascript:'));
});
test('production shell has no archive-prefix/snapshot dependencies or native redirect loops',()=>{
 const js=fs.readFileSync(path.join(root,'library.js'),'utf8'),html=fs.readFileSync(path.join(root,'library.html'),'utf8');
 assert.ok(!js.includes('library-data/'));assert.ok(!js.includes('/archive/'));
 assert.ok(js.includes('index.html#/experiments/${record.id}?full=1'));
 assert.ok(html.includes('library-guides.js')&&html.includes('line-gap-view.js'));
 assert.ok(html.includes('library.js')&&html.includes('library.css'));
 for(const id of ['contents-dialog','files-dialog','variant-dialog'])assert.ok(html.includes('id="'+id+'"'));
});
test('legacy record sections select the correct complete panel',()=>{
 for(const key of ['input','procedure','bounds','exclusions','limitations'])assert.equal(L.sectionTab('experiment-'+key),'scope');
 assert.equal(L.sectionTab('experiment-reproduce'),'reproduce');assert.equal(L.sectionTab('experiment-sources'),'sources');
 assert.equal(L.sectionTab('experiment-finding'),'overview');assert.equal(L.sectionTab('made-up'),null);
});
test('one research directory receives supported query/filter state',()=>{
 const target=new URL(L.researchHref({q:'rune words',family:'routes',page:2}),'https://example.org/');assert.equal(target.pathname,'/research.html');assert(target.searchParams.get('v'));assert.equal(target.hash,'#mode=list&q=rune+words&family=routes&page=2');
 assert.equal(L.guideSource({id:'reading-warning',source:'readings/reading-warning.html'}),'articles/readings/reading-warning.html');
 assert.throws(()=>L.guideSource({source:'../escape.html'}));
});
test('library search reuses authored aliases and exact research page matching',()=>{
 const wiki=require('../search-engine.js'),research=require('../research-index.js'),engines={wiki,index:research},data=L.adaptMetadata(guides,categories,index);
 const alias=L.searchLibrary(data,'2012 puzzle',engines).guides;
 assert.equal(alias[0].guide.id,'cicada-history');assert.equal(alias[0].href,'#/guide/cicada-history?section=2012');
 for(const q of ['Fibonacci','LP2-15\u201317','max_skip','word boundaries']){
  const actual=L.searchLibrary(data,q,engines).experiments;
  const expected=research.select(data.experiments,{...research.state(new URLSearchParams()),q}).allRecords;
  assert.deepEqual(actual.map(r=>r.id),expected.map(r=>r.id),q);
  if(q.startsWith('LP2-'))for(const r of actual)for(const id of ['lp2-15','lp2-16','lp2-17'])assert.ok(r.scope.pages.includes(id));
 }
 assert.ok(L.searchLibrary(data,'Fibonacci',engines).experiments.some(r=>r.id==='fibonacci-stream-skip-grid'));
 assert.deepEqual(L.searchLibrary(data,'zzzz-no-source-record-xyz',engines),{guides:[],experiments:[]});
});
test('combined search passes the complete query rather than a shortened research state',()=>{
 const q='a'.repeat(500),seen=[];
 const result=L.searchLibrary({guides:[],experiments:[]},q,{wiki:{search(_,query){seen.push(query);return []}},index:{state(){return {q:'short'}},select(_,state){seen.push(state.q);return {allRecords:[]}}}});
 assert.deepEqual(seen,[q,q]);assert.deepEqual(result,{guides:[],experiments:[]});
 const html=fs.readFileSync(path.join(root,'library.html'),'utf8');
 for(const script of ['search-engine.js','research-index.js'])assert.equal([...html.matchAll(/src="([^"]+)"/g)].filter(m=>m[1].split('?')[0]===script).length,1);
});
console.log('Library checks:',groups,'groups PASS');

test('visitor limits strip only the trailing editorial review suffix',()=>{
 for(const tail of [' Human review pending.',' Human review is pending','; human review pending.','; Human review is pending.',' Computational review; human review pending.'])assert.equal(L.readerLimit('Not independently checked; language uncertain.'+tail),'Not independently checked; language uncertain.');
 for(const caveat of ['Not independently checked.','The reading remains uncertain.','Human review pending. This is an authored quotation.','No complete recovery; review still needed.'])assert.equal(L.readerLimit(caveat),caveat);
 assert.equal(L.readerLimit('Human review pending.'),'');
});

test('small evidence tables wrap while wide data tables retain scroll navigation',()=>{
 const compact=L.renderMarkdown('| Rule | First wrong rune |\n| --- | --- |\n| Word reversal | Rune 1 |');assert(compact.includes('experiment-compact-table'));assert(!compact.includes('Scroll table sideways'));
 const wide=L.renderMarkdown('| A | B | C |\n| --- | --- | --- |\n| 1 | 2 | 3 |');assert(wide.includes('Scroll table sideways'));assert(wide.includes('tabindex="0"'));
});

test('shared search always offers query-preserving saved-idea discovery with honest published scope',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.join(root,'library.js'),'utf8'),start=source.indexOf(' function renderSearch(s)'),end=source.indexOf('\n async function render()',start);assert(start>=0&&end>start);
 const Index=require('../research-index.js'),Browser=require('../research-browser-model.js'),q='reverse \u201cprime\u201d + words & LP2-15',target=new URL(L.researchHref({q}),'https://example.org/'),mapState=Browser.read(target.hash,'graph',Index.state);
 assert.equal(mapState.mode,'list');assert.equal(mapState.q,q,'The actual map reader applies the complete encoded search query');
 for(const count of [0,1,9]){
  const main={innerHTML:''},context={main,data:{},searchLibrary:()=>({guides:[],experiments:Array.from({length:count},(_,i)=>({id:String(i)}))}),esc:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),researchHref:L.researchHref,experimentRow:()=>'<article>Published result</article>',url:()=>'',finish(){}};
  vm.runInNewContext(source.slice(start,end)+';renderSearch({params:new URLSearchParams(query)});',Object.assign(context,{URLSearchParams,query:new URLSearchParams({q}).toString()}));
  assert.match(main.innerHTML,/Search saved ideas in Research map/);assert.match(main.innerHTML,/Includes loaded ideas/);assert.match(main.innerHTML,new RegExp('Published research · '+count));
  const href=main.innerHTML.match(/<a href="([^"]+)">Search saved ideas in Research map/)[1].replace(/&amp;/g,'&');assert.equal(href,L.researchHref({q}));
  if(count===0){assert.match(main.innerHTML,/No matching guides or published records/);assert.doesNotMatch(main.innerHTML,/No matching guides or research\./);}
 }
});

test('combined search nests actual research cards under section headings while directories retain h2',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.join(root,'library.js'),'utf8'),rowStart=source.indexOf(' function experimentRow('),rowEnd=source.indexOf(' function filteredExperiments',rowStart),searchStart=source.indexOf(' function renderSearch(s)'),searchEnd=source.indexOf('\n async function render()',searchStart),record={id:'software',title:'Exact <research> title',reader_finding:'Original finding',pages:['lp2-15'],outcome:'unsupported'},main={innerHTML:''},context={main,data:{},searchLibrary:()=>({guides:[{href:'#guide',title:'A guide',text:'Guide summary',guide:{category:'Methods'}}],experiments:[record]}),esc:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),researchHref:L.researchHref,experimentHref:id=>'#/experiment/'+id,compactPages:L.compactPages,outcomeNames:{unsupported:'Not supported within scope'},familyMembers:()=>[],url:()=>'',finish(){},URLSearchParams};
 vm.createContext(context);vm.runInContext(source.slice(rowStart,rowEnd)+source.slice(searchStart,searchEnd)+';renderSearch({params:new URLSearchParams("q=research")});',context);
 const outline=[...main.innerHTML.matchAll(/<h([123])[^>]*>([\s\S]*?)<\/h[123]>/g)].map(m=>[Number(m[1]),m[2].replace(/<[^>]+>/g,'')]);assert.deepEqual(outline,[[1,'Search results'],[2,'Guides · 1'],[3,'A guide'],[2,'Published research · 1'],[3,'Exact &lt;research&gt; title']]);
 assert.match(context.experimentRow(record),/<h2 class="research-row-title">/);assert.doesNotMatch(context.experimentRow(record),/<h3 class="research-row-title">/);assert.match(context.experimentRow(record,3),/<h3 class="research-row-title">/);assert.throws(()=>context.experimentRow(record,1),/supported research heading/);assert.equal(record.reader_finding,'Original finding');const css=fs.readFileSync(path.join(root,'library.css'),'utf8');for(const suffix of ['', ' a', ' a:hover'])assert(css.includes('.list-row h2'+suffix+',.list-row h3.research-row-title'+suffix+'{'));assert(!css.includes('.list-row h3{'),'Guide styling remains unchanged');
});
