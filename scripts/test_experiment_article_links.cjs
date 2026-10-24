/* Vetted article hyperlinks stay separate from scientific/image dependencies. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context={esc,head:()=>'',footer:()=>''};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
const render=(text,files=[],aliases={})=>context.renderExperimentMarkdown(text,files,aliases);
const aliases={
 'results.json':'experiments/records/sample/results.json',
 'experiments/records/other/article.md':'#/experiments/other',
 'downloads/experiments/future.zip':'downloads/experiments/future.zip',
 'images/lp2-27.jpg':'images/lp2-27.jpg',
 'research/source-intake/note.md':'research/source-intake/note.md'};
for(const [raw,href] of Object.entries(aliases)){
 const markdown=`[Public reference](${raw})`;
 assert.equal(render(markdown,[],aliases),`<p><a href="${href}">Public reference</a></p>`);
 assert(!render(markdown).includes('<a'),'Unvetted local navigation remains literal');
}
for(const bad of ['../escape.json','./results.json','part//file.json','/absolute.json','//host/file','C:/file','folder/../file',
 'folder/./file','%2e%2e/file','folder/%2Ffile','file.json?query=x','file.json#anchor','folder\\file','javascript:alert','data:text/html,bad','']){
 assert(!render('[Unsafe](unlisted.json)',[],{'unlisted.json':bad}).includes('<a'),'Unsafe mapped target rejected: '+bad);
 if(bad)assert(!render(`[Unsafe](${bad})`,[],{[bad]:'images/lp2-27.jpg'}).includes('<a'),'Unsafe raw alias rejected: '+bad);
}
assert(!render('[External alias](local.json)',[],{'local.json':'https://example.com/other'}).includes('<a'),'Aliases cannot introduce arbitrary external destinations');
assert(!render('[Unknown route](local.json)',[],{'local.json':'#/reader/lp2-27'}).includes('<a'),'Only the supported experiment-article route conversion is accepted');
assert(!render('[Inherited](results.json)',[],Object.create(aliases)).includes('<a'),'Inherited mappings never authorize a link');
for(const invalid of [null,[],{ 'results.json':{} }])assert(!render('[Invalid](results.json)',[],invalid).includes('<a'));
assert(render('[Existing](https://example.com/source)').includes('<a href="https://example.com/source">'));
assert(render('[Guide](#/wiki/search-space?section=bounds)').includes('<a href="#/wiki/search-space?section=bounds">'));
assert(render('[Declared](data/result.json)',['data/result.json']).includes('<a href="data/result.json">'));
assert(!render('![Not a declared image](images/lp2-27.jpg)',[],aliases).includes('<img'),'Hyperlink aliases do not authorize image embedding');
assert(render('![Declared image](images/lp2-27.jpg)',['images/lp2-27.jpg'],aliases).includes('<img'));
assert(!render('`[Example](results.json)`',[],aliases).includes('<a'),'Inline code remains literal');
assert(!render('```text\n[Example](results.json)\n```',[],aliases).includes('<a'),'Fenced code remains literal');
assert(render('[<result>](results.json)',[],aliases).includes('&lt;result&gt;'),'Labels remain escaped');
// Follow generated aliases through the actual full-detail callsite whenever available.
const records=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'))).records;
context.records=records;vm.runInContext('experimentRecords=records',context);
let aliasCount=0,recordCount=0;
for(const record of records){
 const entries=Object.entries(record.article_links||{});if(!entries.length)continue;recordCount++;
 const detail=context.experimentArticle(record,records);
 for(const [raw,href] of entries){
  assert(render(`[Reference](${raw})`,[],record.article_links).includes(`href="${esc(href)}"`),'Generated alias accepted: '+raw);
  assert(detail.includes(`href="${esc(href)}"`),'Actual detail forwards generated aliases: '+record.id+' -> '+raw);aliasCount++;
 }
}
const fixture={...records[0],article:'## Finding\n\n[Recorded result](results.json)',article_links:{'results.json':'experiments/records/sample/results.json'}};
assert(context.experimentArticle(fixture,records).includes('href="experiments/records/sample/results.json"'),'Detail forwarding works before generated data rebuild');
// Three real charts remain visible once in the main findings, with their detailed captions/source links retained.
const l7=records.find(record=>record.id==='l7-score-recovery-controls');assert(l7&&l7.visuals.length===3);
const l7Detail=context.experimentArticle(l7,records),l7Files=[l7.article_path,...l7.reproduction.inputs.map(f=>f.path),...l7.reproduction.outputs.map(f=>f.path)];
const l7Static=render(l7.article,l7Files,l7.article_links||{});
for(const visual of l7.visuals){
 assert.equal(l7Detail.split(`src="${visual.path}"`).length-1,1,'Each declared main chart is embedded exactly once');
 assert(l7Detail.includes(`href="${visual.path}" target="_blank" rel="noopener">Open full-size figure`),'Detailed source link is preserved');
 assert(l7Static.includes(`src="${visual.path}"`),'Standalone/offline Markdown retains every embedded chart');
}
assert.equal((l7Detail.match(/class="small experiment-figure-reference"/g)||[]).length,3);
const extra='experiments/records/example/extra.svg',caption='<source> & exact caption';
const mixed=context.renderExperimentMarkdown(`![${caption}](${extra})\n\n![Previously shown](${l7.visuals[0].path})`,[extra,l7.visuals[0].path],{},[l7.visuals[0].path]);
assert(mixed.includes(`src="${extra}"`),'An additional analysis-only figure is still embedded');
assert(mixed.includes('&lt;source&gt; &amp; exact caption'),'Captions remain escaped');
assert(!mixed.includes(`src="${l7.visuals[0].path}"`));assert(mixed.includes('Previously shown'));
assert(!context.renderExperimentMarkdown(`![Unvetted](${extra})`,[],{},[extra]).includes('<a'),'Already-shown list cannot grant image/link permission');
assert(context.renderExperimentMarkdown('```\n![Literal]('+extra+')\n```',[extra],{},[extra]).includes('![Literal]'),'Fenced examples remain literal');
console.log(`PASS: vetted local/basename/cross-record/ZIP aliases, unsafe/prototype/code/image guards, detail forwarding; ${aliasCount} generated aliases across ${recordCount} records currently checked.`);
