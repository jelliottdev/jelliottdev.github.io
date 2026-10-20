const assert=require('node:assert/strict');
const Search=require('../assistant-search.js'),Markdown=require('../assistant-markdown.js');
const page={id:'lp2-31-0',kind:'page',page:'lp2-31',title:'LP2-31',href:'#/page/lp2-31',text:'Page 31 has runes and a red header.'};
const experiment={id:'test',kind:'experiment',title:'Reverse prime sequence',href:'#/experiments/test',text:JSON.stringify({scope:{pages:['lp2-15'],procedure:'reverse prime values',parameters:'one row'},finding:'Inconclusive'})};
assert.equal(Search.select([page],'Vigenere on LP2-31').length,0);
assert.equal(Search.select([page,experiment],'Vigenere on LP2-31').length,0);
assert.equal(Search.select([page,experiment],'Vigenere on every row of LP2 page 31').length,0);
assert.equal(Search.select([page,experiment],'has anyone tested page 31').length,0);
assert.equal(Search.select([page,experiment],'reverse prime sequence on LP2-31')[0].id,'test');
assert.equal(Search.select([page,experiment],'reverse prime sequence on LP2-31')[1].id,'lp2-31-0');
const largeFirst={...experiment,id:'a',text:experiment.text.padEnd(6000,' ')};
const largeSecond={...experiment,id:'b',text:experiment.text.padEnd(5000,' ')};
const bounded=Search.select([largeFirst,largeSecond],'reverse prime sequence');
assert.deepEqual(bounded.map(d=>d.id),['a'],'Keep a complete best match when two cannot fit');
assert.equal(bounded[0].text,largeFirst.text,'Never truncate the chosen scope');
assert.equal(Search.select([{...largeFirst,text:largeFirst.text.padEnd(9001,' ')},largeSecond],
 'reverse prime sequence').length,0,'Do not replace an oversized best match with a weaker record');
const support=[0,1,2].map(n=>({...page,id:`support-${n}`}));
assert.equal(Search.select([largeFirst,largeSecond,...support],'reverse prime sequence on LP2-31')
 .filter(d=>d.kind==='page').length,2,'Keep the two-page supporting-context limit with one experiment');
assert.deepEqual(Search.pageIds('LP2-31 and lp1 4'),['lp2-31','lp1-04']);
for(const notation of ['LP2:31','LP2 : 31','LP2 page 31','LP2-page-31','LP2–31','LP2—31','LP2‑31','LP2−31','LP2 page #31']){
 assert.deepEqual(Search.pageIds(notation),['lp2-31']);
 assert.equal(Search.select([page,experiment],`has anyone tried ${notation}`).length,0,
   'A page notation must not become a technique match');
 assert.equal(Search.select([page,experiment],`reverse prime sequence on ${notation}`)[1].id,page.id);
}
// A page number in scope must not become lexical evidence for a technique.
const samePage={...experiment,id:'same-page',text:JSON.stringify({scope:{pages:['lp2-31'],procedure:'reverse prime values'},finding:'Inconclusive'})};
for(const query of ['has anyone tried LP2–31','has anyone tested page #31','has anyone tested pages #31–#32']){
 assert.equal(Search.experiments([samePage],query).length,0,query);
 assert.equal(Search.select([page,samePage],query).length,0,query);
}
const sources=[{title:'Scope',href:'#/experiments/test'}];
const html=Markdown.render('# Scope\n\n**One row** [1].\n\n- First\n- Second\n\n| Test | Scope |\n| --- | --- |\n| Reverse | One row |\n\n```py\nprint("<script>")\n```\n\n<img src=x onerror=alert(1)>\n\n[bad](javascript:alert(1))',sources);
assert(html.includes('<strong>One row</strong>'));assert(html.includes('<table>'));assert(html.includes('<li>Second</li>'));
assert(!html.includes('<img'));assert(!html.includes('<script>'));assert(!html.includes('href="javascript:'));assert(html.includes('href="#/experiments/test"'));
assert(!Markdown.render('`[1]`',sources).includes('<a '));
console.log('PASS: no page-only experiment matches, scope separation, page ID parsing, Markdown tables/lists/code, citation links and HTML/URL escaping.');

// Published experiment prose must preserve literal reproduction syntax.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const experimentContext={esc:text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))};
vm.createContext(experimentContext);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../experiments.js'),'utf8'),experimentContext);
const literal=experimentContext.renderExperimentMarkdown('Use `**pattern**` beside **emphasis** and `<script>`.');
assert(literal.includes('<code>**pattern**</code>'));
assert(literal.includes('<strong>emphasis</strong>'));
assert(literal.includes('<code>&lt;script&gt;</code>'));
assert(!literal.includes('<script>'));
assert(!experimentContext.renderExperimentMarkdown('```\n**literal** <script>\n```').includes('<strong>'));
console.log('PASS: experiment inline and fenced code preserve literal syntax and escape HTML.');

const account=experimentContext.renderExperimentMarkdown('[Method](#/wiki/atbash?section=formula) [Source](https://example.com/evidence) [Input](text/lp2-31.txt) [Missing](private.txt) [Unsafe](javascript:alert) `[Literal](#/wiki/atbash)`',['text/lp2-31.txt']);
for(const href of ['#/wiki/atbash?section=formula','https://example.com/evidence','text/lp2-31.txt'])assert(account.includes('href="'+href+'"'));
assert(!account.includes('href="private.txt"'));
assert(!account.includes('href="javascript:'));
assert(account.includes('<code>[Literal](#/wiki/atbash)</code>'));
assert(!experimentContext.renderExperimentMarkdown('[escape](../file.txt)',['../file.txt']).includes('<a '));
assert(!experimentContext.renderExperimentMarkdown('[markup](https://example.com/"onclick="bad)').includes('<a '));
console.log('PASS: authored experiment links support methods, HTTPS sources and declared files without linking unsafe destinations.');

const tableAccount=experimentContext.renderExperimentMarkdown('Before.\n\n| Test | Result |\n| --- | --- |\n| **Control** | `**literal**` |\n| <img src=x> | [Method](#/wiki/atbash) |\n\nAfter.');
assert(tableAccount.includes('<th scope="col">Test</th>'));
assert(tableAccount.includes('<td><strong>Control</strong></td>'));
assert(tableAccount.includes('<td><code>**literal**</code></td>'));
assert(tableAccount.includes('&lt;img src=x&gt;'));
assert(!tableAccount.includes('<img'));
assert(tableAccount.includes('href="#/wiki/atbash"'));
assert(tableAccount.endsWith('<p>After.</p>'));
assert(!experimentContext.renderExperimentMarkdown('```\n| A | B |\n| --- | --- |\n```').includes('<table>'));
console.log('PASS: experiment tables preserve inline syntax, escape HTML, and leave fenced examples literal.');

for(const render of [Markdown.render,experimentContext.renderExperimentMarkdown]){
 for(const input of ['| A | B |\n| --- | --- |\n| 1 | 2 | EXTRA |',
                     '| A | B |\n| --- | --- |\n| MISSING |',
                     '| A | B | C |\n| --- | --- |\n| 1 | 2 | 3 |']){
  const result=render(input);
  assert(!result.includes('<table>'));
  assert(result.includes(input),'Malformed tables must retain every source character');
  assert(result.includes('column counts differ'));
 }
 const escaped=render('| A | B |\n| --- | --- |\n| 1 | 2 | <script> |');
 assert(escaped.includes('&lt;script&gt;'));assert(!escaped.includes('<script>'));
}
console.log('PASS: malformed comparison and experiment tables retain all cells as escaped source text.');

const familyFixtures=[{id:'one',family:{id:'f',title:'Family',question:'Question?'}},{id:'other'},{id:'two',family:{id:'f',title:'Family',question:'Question?'}}];
const grouped=experimentContext.experimentGroups(familyFixtures,r=>`<p>${r.id}</p>`);
assert.equal((grouped.match(/class="experiment-family"/g)||[]).length,2);
assert(grouped.indexOf('<p>two</p>')<grouped.indexOf('<p>other</p>'));
const chart='experiments/records/example/chart.svg';
assert(experimentContext.renderExperimentMarkdown(`![Data chart](${chart})`,[chart]).includes('<img'));
assert(!experimentContext.renderExperimentMarkdown(`![Data chart](${chart})`).includes('<img'));
assert(!experimentContext.renderExperimentMarkdown('![Unsafe](https://example.com/chart.svg)').includes('<img'));
console.log('PASS: family grouping preserves members; figures require declared local files.');

const artifactRecord={id:'artifact-control',status:'published',title:'Emerson book cipher',question:'Reproduce the historical lookup?',scope:{pages:[],artifacts:['exports/source.pdf'],procedure:'Book cipher lookup'},tags:['Emerson'],summary:'Historical source only',finding:'Control reproduced',limitations:'No manuscript-page test'};
const artifactDocs=Search.experimentDocs([artifactRecord]);
assert.equal(Search.experiments(artifactDocs,'Emerson book cipher LP2-31')[0].pageOverlap,false);
assert.equal(Search.experiments(artifactDocs,'LP2-31').length,0);
assert(experimentContext.experimentScopeLinks(artifactRecord).includes('href="exports/source.pdf"'));
assert(!experimentContext.experimentScopeLinks(artifactRecord).includes('#/page/'));
console.log('PASS: artifact-only controls retain file targets without inventing manuscript-page coverage.');
const published=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/experiments.json'),'utf8')).records;
const browse=experimentContext.experimentBrowse(published);
assert.equal((browse.match(/<details class="experiment-browse-family">/g)||[]).length,new Set(published.map(r=>r.family?.id||r.id)).size);
for(const record of published)assert.equal(browse.split(`href="#/experiments/${record.id}"`).length-1,1,'Each record has one direct browse link');
assert(!browse.includes('<details class="experiment-browse-family" open'),'Browse families start collapsed');
assert(browse.indexOf('href="#/experiments/lp2-prime-minus-one-openings"')<browse.indexOf('href="#/experiments/lp2-fibonacci-openings"'),'Baseline precedes its variants');
assert(!browse.includes('Retested '),'Full review metadata belongs to the record rather than every browse entry');
assert(!experimentContext.experimentBrowse([{id:'safe',title:'<img src=x>',summary:'<script>unsafe</script>'}]).includes('<script>'));
console.log('PASS: family browsing retains one direct link per record, baseline order and escaped content.');
experimentContext.published=published;
experimentContext.head=()=>'';
experimentContext.footer=()=>'';
vm.runInContext('experimentRecords=published',experimentContext);
for(const record of published){
 const rendered=experimentContext.experimentArticle(record);
 assert(rendered.indexOf('id="experiment-finding"')<rendered.indexOf('id="experiment-scope"'));
 const downloads=experimentContext.experimentDownloads(record);
 assert(downloads.includes(`href="${record.reproduction.script}" download`));
 for(const output of record.reproduction.outputs.filter(f=>/\.(json|csv|tsv|txt)$/.test(f.path))){
  assert(downloads.includes(`href="${output.path}" download`),'A readable result must be directly downloadable');
 }
 assert(rendered.includes('href="downloads/reference-data.zip" download'));
 assert.equal(rendered.includes('href="downloads/original-images.zip" download'),record.reproduction.inputs.some(f=>/\.(jpe?g|png)$/i.test(f.path)));
 const family=rendered.indexOf('aria-label="Experiment family comparison"');
 if(family>=0)assert(family>rendered.indexOf('id="experiment-reproduce"'));
}
console.log('PASS: published records lead with findings; result downloads and required bundles remain accessible.');
vm.runInContext(fs.readFileSync(path.join(__dirname,'../assistant-ui.js'),'utf8'),experimentContext);
const totient=published.find(r=>r.id==='lp2-totient-openings');
const scopedResult=experimentContext.experimentSearchResult(totient,['lp2-31','lp2-56']);
assert(scopedResult.indexOf(experimentContext.esc(totient.scope.procedure))<scopedResult.indexOf('<details'));
assert(scopedResult.indexOf(experimentContext.esc(totient.scope.exclusions))<scopedResult.indexOf('<details'));
assert(scopedResult.includes('Not in this record’s page scope: LP2-56.'));
assert(!scopedResult.includes('Not in this record’s page scope: LP2-31'));
assert(!experimentContext.experimentSearchResult(totient,['lp2-31']).includes('scope-mismatch'));
const liveDocs=Search.experimentDocs(published);
assert.equal(Search.experiments(liveDocs,'totient of rune values on LP2-31')[0].document.id,totient.id);
assert.equal(Search.experiments(liveDocs,'Fibonacci on LP2-31')[0].document.id,'lp2-fibonacci-openings');
assert.equal(Search.experiments(liveDocs,'OutGuess on LP2-31')[0].document.id,'outguess-default-key');
assert.equal(Search.experiments(liveDocs,'has anyone tried LP2-31').length,0);
console.log('PASS: method and exclusions remain visible; mixed page requests disclose uncovered pages; real-record lexical retrieval stays separate from proof of identical scope.');
