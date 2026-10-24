/* Browser-free regression for the reader/search Escape event conflict. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const elements=new Map(),classes=new Set(),events=[];
const element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,attributes:{},setAttribute(key,value){this.attributes[key]=value},focus(){events.push(['focus',id])}});return elements.get(id)};
const context={localStorage:{getItem:()=>null},document:{
 body:{classList:{contains:key=>classes.has(key),remove:key=>classes.delete(key),add:key=>classes.add(key)}},
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

// Run the production header breakpoint callback independently of page rendering.
const app=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
let registered;context.matchMedia=()=>({addEventListener(type,fn){assert.equal(type,'change');registered=fn}});
context.setNavigation=open=>events.push(['navigation',open]);
context.main={focus(options){events.push(['focus','main',options.preventScroll])}};
element('search-form').contains=node=>node===element('search')||node===element('suggestion-link');
const start=app.indexOf('function adaptHeaderToViewport('),end=app.indexOf("if($('#search-form'))",start);
assert(start>=0&&end>start);vm.runInContext(app.slice(start,end),context);
assert.equal(registered,context.adaptHeaderToViewport);
const run=(mobile,active)=>{events.length=0;context.document.activeElement=active;registered({matches:mobile});return [...events]};
classes.add('reader-active');classes.delete('reader-search-open');
assert.deepEqual(run(true,element('search')),[['navigation',false]]);
assert(classes.has('reader-search-open'),'Desktop input stays visible when entering compact reader');
assert.equal(element('reader-search-toggle').attributes['aria-expanded'],'true');
assert.deepEqual(run(false,element('reader-search-toggle')),[['navigation',false],['focus','search']]);
assert(!classes.has('reader-search-open'));
assert.equal(element('reader-search-toggle').attributes['aria-expanded'],'false');
const mobileLink={closest:selector=>selector==='#sidebar .mobile-nav'?{}:null};
const desktopLink={closest:selector=>selector==='#sidebar .desktop-nav'?{}:null};
assert.deepEqual(run(false,mobileLink),[['navigation',false],['focus','main',true]]);
assert.deepEqual(run(true,desktopLink),[['navigation',false],['focus','menu']]);
assert.deepEqual(run(false,element('menu')),[['navigation',false],['focus','main',true]]);
classes.delete('reader-active');classes.delete('reader-search-open');
assert.deepEqual(run(true,element('search')),[['navigation',false]],'Ordinary header search retains focus');
assert(!classes.has('reader-search-open'));
assert.deepEqual(run(true,{closest:()=>null}),[['navigation',false]],'Reading focus is not moved');
console.log('PASS: breakpoint swaps preserve active reader search and return hidden menu/toggle/navigation focus to visible controls. DOM stubs do not verify rendering.');

const findElement=context.document.getElementById;context.document.getElementById=()=>null;
assert.deepEqual(run(false,null),[['navigation',false]],'No absent toggle can accidentally claim focus');
context.document.getElementById=findElement;
