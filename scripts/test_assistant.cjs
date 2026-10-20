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
