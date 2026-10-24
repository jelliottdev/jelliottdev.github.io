/* Authored sections promoted without changing evidence or Markdown permissions. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),{spawnSync}=require('node:child_process');
const root=path.join(__dirname,'..'),esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context={esc,head:()=>'',footer:()=>''};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
const markdown='# Study\n\n## Finding\nA measured finding.\n\n## Useful <result>\nVisible **important result**.\n\n[Allowed](results.json) [Unsafe](javascript:alert)\n\n<script>unsafe()</script>\n\n### Example\nA subordinate explanation.\n\n## Secondary\nKeep this later.\n\n## Other useful result\nOne short second result.\n';
const selected=['Other useful result','Useful <result>'];
const extracted=context.experimentReaderSections(markdown,selected);
assert.deepEqual(Array.from(extracted.selected,s=>s.title),selected,'Authored selection order is preserved');
assert(extracted.remaining.includes('Keep this later.'));assert(!extracted.remaining.includes('important result'));assert(!extracted.remaining.includes('One short second result'));
assert(extracted.selected[1].body.includes('### Example'),'Subordinate sections travel with their selected parent');
const fenced='```md\n## Useful\n```\n\n~~~markdown\n## Useful\n~~~\n\n````md\n```\n## Useful\n````\n\n## Useful\nReal content.\n## After\nRetained.';
assert.equal(context.experimentReaderSections(fenced,['Useful']).selected[0].body.trim(),'Real content.');
const cases=[{markdown,titles:selected,valid:true},{markdown:fenced,titles:['Useful'],valid:true},{markdown,titles:[],valid:true},
 ...[null,'Useful',[1],[''],['\n'],['Finding','Finding'],['Finding','Secondary','Other useful result','Useful <result>'],['Absent'],['Example']].map(titles=>({markdown,titles,valid:false})),
 {markdown:'```\n## Fake\n```',titles:['Fake'],valid:false},
 {markdown:'~~~\n## Fake\n~~~',titles:['Fake'],valid:false},
 {markdown:'## Twice\nA\n## Twice\nB',titles:['Twice'],valid:false},
 {markdown:'## Title\r\nText\r\n## After\r\nLater',titles:['Title'],valid:true}];
for(const test of cases){if(test.valid)context.experimentReaderSections(test.markdown,test.titles);else assert.throws(()=>context.experimentReaderSections(test.markdown,test.titles));}
const python=spawnSync(process.env.PYTHON||'python',['-c',"import json,sys;sys.path.insert(0,'scripts');from build_experiments import validate_reader_sections\nfor case in json.load(sys.stdin):\n try:\n  validate_reader_sections(case['markdown'],case['titles']);valid=True\n except ValueError: valid=False\n assert valid==case['valid'],case\nprint('PASS Python reader_sections validation parity')"],{cwd:root,input:JSON.stringify(cases),encoding:'utf8'});
assert.equal(python.status,0,python.stderr||python.stdout);
const records=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8')).records;
const fixture={...records[0],family:null,related:[],reader_sections:selected,article:markdown,article_links:{'results.json':'experiments/records/sample/results.json'}};
const before=JSON.stringify(fixture),html=context.experimentArticle(fixture,records),files=html.indexOf('<h2 id="experiment-reproduce">'),details=html.indexOf('<summary>Detailed analysis and sources');
assert(html.indexOf('Visible <strong>important result</strong>')<files);assert(html.indexOf('One short second result')<files);
assert.equal((html.match(/important result/g)||[]).length,1,'The selected body is not repeated in Detailed analysis');
assert.equal((html.match(/One short second result/g)||[]).length,1);assert(html.indexOf('Keep this later.')>details);
assert(html.includes('<h3>Useful &lt;result&gt;</h3>'));assert(html.includes('&lt;script&gt;unsafe()&lt;/script&gt;'));assert(!html.includes('<script>'));
assert(html.includes('href="experiments/records/sample/results.json"'));assert(!html.includes('href="javascript:'));
assert.equal(JSON.stringify(fixture),before,'Rendering does not alter the exact authored article or metadata');
assert.equal(context.experimentReaderSections(markdown).remaining,markdown,'Records without metadata remain unchanged');
assert.throws(()=>context.experimentArticle({...fixture,reader_sections:['Missing']},records));
const shortTable='| Control | Result |\n| --- | --- |\n| Very-long-unbroken-label-that-must-wrap | **Correct recovery** |';
const compact=context.renderExperimentMarkdown(shortTable);
assert(compact.includes('class="table-wrap experiment-compact-table"'));assert(!compact.includes('table-scroll-hint'));assert(!compact.includes('tabindex="0"'),'A fitting table is not an unnecessary scroll focus stop');
assert(compact.includes('<strong>Correct recovery</strong>'));assert.equal((compact.match(/scope="col"/g)||[]).length,2);
const wide=context.renderExperimentMarkdown('| A | B | C |\n| --- | --- | --- |\n| 1 | 2 | 3 |');
assert(wide.includes('table-scroll-hint')&&wide.includes('tabindex="0"')&&wide.includes('Scrollable experiment data table'));assert(!wide.includes('experiment-compact-table'));
const selectedTable=context.experimentArticle({...fixture,reader_sections:['Control results'],article:'## Control results\n'+shortTable+'\n## Other\nOther content.'},records);
assert(selectedTable.indexOf('experiment-compact-table')<selectedTable.indexOf('<h2 id="experiment-reproduce">'));assert.equal((selectedTable.match(/Correct recovery/g)||[]).length,1);
const css=fs.readFileSync(path.join(root,'style.css'),'utf8');
assert(/\.experiment-prose \.experiment-compact-table table\{[^}]*min-width:0;table-layout:fixed/.test(css));
assert(/\.experiment-prose \.table-wrap\.experiment-compact-table th,\.experiment-prose \.table-wrap\.experiment-compact-table td\{min-width:0;overflow-wrap:anywhere/.test(css),'Both cells override the old first-child selector specificity and wrap long labels');
console.log(python.stdout.trim());console.log('PASS reader sections: selected prose visible before files once, unselected detail retained, safe links/HTML, exact H2 and fenced-code validation, Python/runtime parity; no browser/network.');
