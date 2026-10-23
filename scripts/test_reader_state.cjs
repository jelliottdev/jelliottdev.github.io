/* Reader state and focus regressions using archived pages and DOM stubs. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..'),stored=new Map([['liberpedia-reader-mode','latin']]);
const timers=[],cleared=new Set(),elements=new Map();
const context={localStorage:{getItem:key=>stored.get(key)||null},document:{activeElement:null,addEventListener(){},querySelector:key=>elements.get(key)},
 setTimeout(fn,ms){timers.push({fn,ms});return timers.length-1},clearTimeout:id=>cleared.add(id)};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'access.js'),'utf8'),context);
function node(){return {hidden:false,disabled:false,focus(){context.document.activeElement=this},contains:()=>false,querySelector:()=>null}};
function versionSelect(page){
 const values=page.visible_text?['visible']:['raw','latin'];if(page.reviewed_text)values.push('reviewed');if(page.reading)values.push('literal','context');
 let value=values[0];return {options:values.map(value=>({value})),get value(){return value},set value(next){value=next},set selectedIndex(index){value=values[index]}};
}
const page=id=>JSON.parse(fs.readFileSync(path.join(root,'data/pages/'+id+'.json'),'utf8'));
const runic=versionSelect(page('lp2-02')),cover=versionSelect(page('lp1-00'));
context.selectReaderTextVersion(runic);assert.equal(runic.value,'latin');
context.selectReaderTextVersion(cover);assert.equal(cover.value,'visible');
assert.equal(stored.get('liberpedia-reader-mode'),'latin','A page-specific fallback does not overwrite the preference');
context.selectReaderTextVersion(runic);assert.equal(runic.value,'latin','Latin preference survives visiting a visible-text-only page');
stored.set('liberpedia-reader-mode','reviewed');context.selectReaderTextVersion(runic);assert.equal(runic.value,'raw','Unavailable versions use the current page’s first valid option');
const workspace={isConnected:true},imageButton=node(),textButton=node(),compareButton=node(),control=node();
elements.set('[data-reader-view="image"]',imageButton);elements.set('[data-reader-view="text"]',textButton);elements.set('[data-reader-view="compare"]',compareButton);
elements.set('.manuscript-text',{contains:active=>active===control});
imageButton.click=()=>vm.runInContext("readerView='image'",context);
for(const active of [control,compareButton]){
 vm.runInContext("readerView='compare'",context);context.document.activeElement=active;
 context.fitReaderComparison(workspace,()=>false);assert.equal(context.document.activeElement,imageButton,'A hidden comparison control returns focus to the Image view button');
 assert.equal(vm.runInContext('readerView',context),'image');
}
vm.runInContext("readerView='text'",context);context.document.activeElement=compareButton;
context.fitReaderComparison(workspace,()=>false);assert.equal(context.document.activeElement,textButton,'A hidden inactive Compare button returns focus to the selected Text button');
vm.runInContext("readerView='compare'",context);context.document.activeElement=control;
context.fitReaderComparison(workspace,()=>true);assert.equal(context.document.activeElement,control);
workspace.isConnected=false;context.fitReaderComparison(workspace,()=>false);assert.equal(vm.runInContext('readerView',context),'compare','Detached readers do not change the current view');
function imageState(complete=false,naturalWidth=0){
 const image={isConnected:true,complete,naturalWidth},loading=node(),error=node(),sheet=node(),zoom=node(),original=node();
 loading.hidden=true;error.hidden=true;error.querySelector=selector=>selector==='a'?original:null;error.contains=active=>active===original;
 context.bindReaderImageState(image,loading,error,sheet,zoom);return {image,loading,error,sheet,zoom,original};
}
const pending=imageState(),timer=timers.at(-1);assert.equal(timer.ms,350);timer.fn();assert.equal(pending.loading.hidden,false);
context.document.activeElement=pending.sheet;pending.image.onerror();
assert.equal(pending.loading.hidden,true);assert.equal(pending.sheet.hidden,true);assert.equal(pending.zoom.disabled,true);assert.equal(pending.error.hidden,false);
assert.equal(context.document.activeElement,pending.original,'Failed image does not leave focus on its hidden image button');
pending.image.onload();assert.equal(pending.sheet.hidden,false);assert.equal(pending.zoom.disabled,false);assert.equal(pending.error.hidden,true);
assert.equal(context.document.activeElement,pending.sheet,'A later successful load does not hide the focused error link');
const zoomFailure=imageState();context.document.activeElement=zoomFailure.zoom;zoomFailure.image.onerror();assert.equal(context.document.activeElement,zoomFailure.original);
const elsewhere=node(),background=imageState();context.document.activeElement=elsewhere;background.image.onerror();assert.equal(context.document.activeElement,elsewhere,'Background image failure does not steal reading focus');
const broken=imageState(true,0);assert.equal(broken.error.hidden,false,'A cached broken image uses the same error state');
const loaded=imageState(true,2400);assert.equal(loaded.error.hidden,true);assert.equal(loaded.sheet.hidden,false);
const stale=imageState();stale.image.isConnected=false;timers.at(-1).fn();stale.image.onerror();stale.image.onload();
assert.equal(stale.loading.hidden,true);assert.equal(stale.error.hidden,true);assert.equal(stale.sheet.hidden,false);assert.equal(stale.zoom.disabled,false);
assert(fs.readFileSync(path.join(root,'access.js'),'utf8').includes('class="reader-image-error" role="alert" hidden'));
// Delayed restore belongs to the exact reader instance, hash and representation.
const frames=[],scrolls=[];
context.requestAnimationFrame=fn=>frames.push(fn);context.location={hash:'#/reader/lp2-02?view=image'};
context.window={scrollY:10,scrollTo:value=>scrolls.push(value)};
function scheduleRestore(){
 const current={isConnected:true,getBoundingClientRect:()=>({top:90})};
 elements.set('.reader-workspace',current);context.location.hash='#/reader/lp2-02?view=image';
 vm.runInContext("readerPositionPage='lp2-02';readerView='image';readerPositions={image:500,text:20,compare:null}",context);
 context.restoreReaderPosition('lp2-02');assert.equal(frames.length,1);
 frames.shift()();assert.equal(frames.length,1);return current;
}
function finishRestore(){const before=scrolls.length;frames.shift()();return scrolls.length-before;}
scheduleRestore();assert.equal(finishRestore(),1);assert.equal(scrolls.at(-1).top,600);
scheduleRestore();vm.runInContext("readerView='text'",context);assert.equal(finishRestore(),0,'Image restore cannot override a newly selected Text position');
context.location.hash='#/reader/lp2-02?view=text';context.restoreReaderPosition('lp2-02');frames.shift()();
assert.equal(finishRestore(),1);assert.equal(scrolls.at(-1).top,120,'Text restores its own independent saved position');
scheduleRestore();elements.set('.reader-workspace',{isConnected:true});assert.equal(finishRestore(),0,'Same-page rerender invalidates the old instance');
const detached=scheduleRestore();detached.isConnected=false;assert.equal(finishRestore(),0);
scheduleRestore();context.location.hash='#/reader/lp2-03';vm.runInContext("readerPositionPage='lp2-03'",context);assert.equal(finishRestore(),0,'Navigation invalidates pending restoration');
scheduleRestore();context.location.hash='#/reader/lp2-02?view=text';assert.equal(finishRestore(),0,'A changed hash invalidates restoration even before view state catches up');
const missing=scheduleRestore();frames.length=0;missing.isConnected=false;context.restoreReaderPosition('lp2-02');assert.equal(frames.length,0,'Detached readers do not schedule work');
console.log('PASS: text-version preference fallback, comparison/image focus, and delayed reader restoration guarded by view, hash, page and exact connected instance. DOM stubs do not verify layout.');
