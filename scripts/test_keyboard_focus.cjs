/* Browser-free regression for the reader/search Escape event conflict. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const elements=new Map(),classes=new Set(),events=[];
const element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,attributes:{},setAttribute(key,value){this.attributes[key]=value},focus(){events.push(['focus',id])}});return elements.get(id)};
const context={localStorage:{getItem:()=>null},document:{
 body:{classList:{contains:key=>classes.has(key),remove:key=>classes.delete(key)}},
 getElementById:element,addEventListener(){}},$:selector=>element(selector.slice(1))};
vm.createContext(context);
for(const file of ['access.js','search-ui.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'..',file),'utf8'),context);
const keyEvent=key=>({key,preventDefault(){events.push(['prevent'])},stopPropagation(){events.push(['stop'])}});
classes.add('reader-search-open');
context.closeReaderSearchOnEscape(keyEvent('Escape'));
assert(!classes.has('reader-search-open'));
assert.equal(element('search-suggestions').hidden,true,'Suggestions close with the reader search form');
assert.equal(element('search').attributes['aria-expanded'],'false');
assert.equal(element('reader-search-toggle').attributes['aria-expanded'],'false');
assert.deepEqual(events,[['focus','reader-search-toggle'],['prevent'],['stop']],
 'Escape restores visible Search focus and prevents the suggestion panel refocusing its hidden input');
events.length=0;
context.closeReaderSearchOnEscape(keyEvent('Escape'));
classes.add('reader-search-open');context.closeReaderSearchOnEscape(keyEvent('Tab'));
assert.deepEqual(events,[],'Other keys and Escape outside reader search keep their normal handling');
assert(classes.has('reader-search-open'));
console.log('PASS: reader Escape closes suggestions, restores visible focus, consumes the conflicting event, and leaves unrelated keys unchanged. DOM stubs do not verify rendering.');
