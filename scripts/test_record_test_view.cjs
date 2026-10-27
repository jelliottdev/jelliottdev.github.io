'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),View=require('../record-test-view.js');
const root=path.join(__dirname,'..'),metadata={input:'Archived manuscript runes.',action:'Try the declared rule.',check:'Compare the complete output with the known reading.'},record={reader_test:metadata};
const before=JSON.stringify(record),html=View.render(record);
assert(View.valid(metadata));assert.equal(JSON.stringify(record),before);
assert(html.startsWith('<section class="record-test" aria-label="What was tried"><h2>What was tried</h2>'));
for(const label of ['Used','Tried','Checked'])assert(html.includes('<dt>'+label+'</dt>'));
assert.equal((html.match(/<dd>/g)||[]).length,3);assert(!/<(?:button|a|details|form)\b/.test(html),'An authored test description has no execution controls');
assert(View.render(record,{headingLevel:3}).includes('<h3>What was tried</h3>'));assert(View.render(record,{headingLevel:'3'}).includes('<h2>'));assert(View.render(record,{headingLevel:1}).includes('<h2>'));
for(const value of [undefined,null,[],{},'test',{...metadata,extra:'Unexpected'},{input:metadata.input,action:metadata.action},Object.assign({...metadata},{[Symbol('extra')]:true})])assert.equal(View.render({reader_test:value}),'');
for(const invalid of ['', ' ', ' Text.', 'Text. ',42,null,[],{},'x'.repeat(321),'<b>Text</b>','a < b','a > b','First\nSecond','a\rb','a\tb','a\0b','a\x85b','a\u2028b','a\u2029b','a\u202eb','a\u2066b','a\u200bb','a\ud800b','a\udc00b']){
 for(const field of ['input','action','check'])assert.equal(View.render({reader_test:{...metadata,[field]:invalid}}),'','Reject malformed '+field+': '+JSON.stringify(invalid));
}
const getter={...metadata};Object.defineProperty(getter,'input',{enumerable:true,get(){throw Error('Must not execute a metadata getter');}});assert.equal(View.render({reader_test:getter}),'');
const escaped=View.render({reader_test:{input:'A & B "quoted" and \'single\'.',action:'**Literal** [text](url) and `code` stay text.',check:'ᚠ and 字 remain readable.'}});
assert(escaped.includes('A &amp; B &quot;quoted&quot; and &#39;single&#39;.'));assert(escaped.includes('**Literal** [text](url) and `code` stay text.'));assert(!escaped.includes('<strong>')&&!escaped.includes('<a '));assert(escaped.includes('ᚠ and 字'));
assert(View.valid({...metadata,input:'😀'.repeat(320)}),'The limit counts Unicode codepoints, not UTF-16 units');assert(!View.valid({...metadata,input:'😀'.repeat(321)}));
assert.equal(View.render({title:'A guessed method',browser_followups:[{motivation:'A different future check'}]}),'','Missing metadata is never inferred from another field');
Object.freeze(metadata);Object.freeze(record);assert.equal(View.render(record),html);

const catalogue=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8')).records;
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context={esc:escape,head:()=>'',footer:()=>'',RecordTestView:View};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
const fixture={...catalogue[0],family:null,related:[],reader_test:metadata},fixtureBefore=JSON.stringify(fixture),legacy=context.experimentArticle(fixture,catalogue);
assert(legacy.includes(html));assert(legacy.indexOf('class="record-test"')<legacy.indexOf('id="experiment-finding"'),'Legacy description precedes finding');assert(legacy.includes('id="experiment-scope"'));assert(legacy.includes(escape(fixture.scope.procedure)));assert.equal(JSON.stringify(fixture),fixtureBefore);
delete context.RecordTestView;assert(!context.experimentArticle(fixture,catalogue).includes('class="record-test"'),'Legacy remains usable when the optional module is absent');
const library=fs.readFileSync(path.join(root,'library.js'),'utf8'),overview=library.slice(library.indexOf(' function overview(record)'),library.indexOf(' function scope(record)'));
assert(overview.includes('RecordTestView?.render(record,{headingLevel:2})'));assert(overview.indexOf('RecordTestView?.render')<overview.indexOf('<div class="finding"'),'Library description precedes finding');
const browser=fs.readFileSync(path.join(root,'research-browser.js'),'utf8'),inspector=browser.slice(browser.indexOf(' function showInspector('),browser.indexOf(' const sorts='));
assert(inspector.includes('RecordTestView?.render(record,{headingLevel:3})'));assert(inspector.indexOf('RecordTestView?.render')<inspector.indexOf('<h3 class="preview-heading">Result</h3>'),'Map description precedes finding');assert(browser.includes('holder.hidden=!chips.length;'));assert(!browser.includes('data-work-shortcut'),'Active chips remain, without a duplicate default work shortcut');
for(const name of ['wulfic-p21-running-key-layers','alternating-alphabet-interruption-clocks','dukotah-payload-key-skip','payload-ciphertext-skip-replay']){
 const source=JSON.parse(fs.readFileSync(path.join(root,'experiments/records',name,'record.json'),'utf8'));assert(View.valid(source.reader_test),name+' has valid source-authored metadata');assert(View.render(source).includes('What was tried'));
}
console.log('PASS authored test metadata: exact fields, Unicode bounds, markup/control/bidi/surrogate rejection, escaped literal punctuation, immutable rendering, no inference, shared placement before findings and optional legacy integration.');

const relatedRecord={id:'literal-related',title:'Literal <title>',reader_test:{input:'A page',action:'Try one exact rule',check:'Compare with one supplied opening'},reader_finding:'A literal <result> & no injected markup.',reader_limit:'A limitation '.repeat(35)};
const relatedBefore=JSON.stringify(relatedRecord),relatedHTML=View.renderRelated(relatedRecord);assert(relatedHTML.includes('library.html#/experiment/literal-related'));assert(relatedHTML.includes('Try one exact rule'));assert(relatedHTML.includes('&lt;result&gt; &amp;'));assert(!relatedHTML.includes('<result>'));assert(relatedHTML.includes('…'));assert.equal(JSON.stringify(relatedRecord),relatedBefore);assert.equal(View.renderRelated({...relatedRecord,id:'https://evil.example'}),'');let relatedReads=0;const relatedGetter={};Object.defineProperty(relatedGetter,'id',{enumerable:true,get(){relatedReads++;return 'literal-related';}});assert.equal(View.renderRelated(relatedGetter),'');assert.equal(relatedReads,0);console.log('PASS shared related-record excerpts preserve authored findings, escape source text, mark truncation and reject unsafe links/accessors.');

const ordered=View.renderRelated({id:'ordered-check',title:'A supplied check',reader_test:metadata,reader_finding:'The supplied opening did not appear.',reader_limit:'Other readings were not checked.'});
assert(ordered.indexOf('<strong>Result:</strong>')<ordered.indexOf('<strong>What was checked:</strong>'));
assert(ordered.includes(metadata.action+' '+metadata.check),'Both exact authored strings remain visible in one text block');
assert.equal((ordered.match(/<p>/g)||[]).length,2,'Result and checked text use two ordinary paragraphs; limit retains existing small paragraph');
const duplicate=View.renderRelated({id:'duplicate-check',title:'Repeated description',reader_test:{...metadata,check:metadata.action},finding:'No match'});assert.equal(duplicate.split(metadata.action).length-1,1,'Only exact duplicate strings are omitted');
const missing=View.renderRelated({id:'no-authored-check',title:'Unknown check',scope:{procedure:'A source-authored procedure'},finding:'A source-authored result'});assert(missing.includes('What was tried:'));assert(!missing.includes('What was checked:'));assert(!missing.includes(metadata.check));
const malformed=View.renderRelated({id:'invalid-authored-check',title:'Invalid supplied metadata',reader_test:{...metadata,check:undefined},scope:{procedure:'The exact recorded procedure'},finding:'Recorded result'});assert(!malformed.includes('What was checked:'));assert(malformed.includes('The exact recorded procedure'));
const longAuthored={input:'Known source',action:'A'.repeat(300),check:'B'.repeat(300)},longHTML=View.renderRelated({id:'whole-author-text',title:'Exact authored descriptions',reader_test:longAuthored,finding:'Recorded result'});assert(longHTML.includes(longAuthored.action+' '+longAuthored.check),'Valid action and check are not silently truncated');assert(!/<details|<summary|<button/.test(longHTML),'Important findings and check remain visible');
console.log('PASS related previews lead with results, retain exact authored action and criterion in one paragraph, omit exact duplication and never invent a missing check.');
