/* Production breakpoint handler and view change, without browser/network calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../manuscript-reader.js'),'utf8');
const setView=source.match(/^function setView\(.*$/m)[0];
const remember=source.match(/^function remember\(.*$/m)[0],rememberScroll=source.match(/^function rememberViewportScroll\(.*$/m)[0];
const start=source.indexOf('let hiddenResponsiveFocus=null;'),end=source.indexOf('\nsmall.addEventListener',start);
assert(start>=0&&end>start);assert(source.includes("small.addEventListener('change',fitReaderViewport)"));
function fixture(view='compare',narrow=true){
 const doc={activeElement:null,body:{},addEventListener(){}},frames=[],remembered=[],stored=[],nodes=new Map();
 const make=(id,extra={})=>{const node={id,isConnected:true,hidden:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn},getClientRects(){return this.hidden?[]:[{}]},...extra,focus(options){doc.activeElement=this;this.options=options}};nodes.set(id,node);return node;};
 const copy=make('copy-location'),search=make('find-input'),textScroll=make('text-scroll',{scrollTop:123}),imageScroll=make('image-scroll',{scrollTop:456,scrollLeft:78});
 const image=make('image',{tagName:'BUTTON',dataset:{view:'image'},setAttribute(){}}),text=make('text',{tagName:'BUTTON',dataset:{view:'text'},setAttribute(){}}),compare=make('compare',{tagName:'BUTTON',dataset:{view:'compare'},setAttribute(){}});
 const pane={contains:node=>[copy,search,textScroll].includes(node)},reader={dataset:{view}};
 const select=selector=>selector==='#text-pane'?pane:selector==='#reader'?reader:selector.startsWith('button[data-view=')?nodes.get(selector.match(/"(.*?)"/)[1]):nodes.get(selector.slice(1));
 const context={document:doc,small:{matches:narrow},$:select,$$:()=>[image,text,compare],requestAnimationFrame:fn=>frames.push(fn),
  storeLast(id){stored.push(id)},zoom:1,savePreferences(){},syncContinuous(){if(context.view==='text')copy.hidden=search.hidden=textScroll.hidden=false},fitImage(){},view,page:{id:'lp2-00'},fitKind:'custom',positions:new Map()};
 vm.createContext(context);vm.runInContext(remember+'\n'+rememberScroll+'\n'+setView+'\n'+source.slice(start,end),context);
 const actualRemember=context.remember;context.remember=(persist)=>{remembered.push(context.view);actualRemember(persist)};
 return{doc,copy,search,textScroll,imageScroll,image,text,compare,context,frames,remembered,stored,run:()=>context.fitReaderViewport()};
}
for(const key of ['copy','search','textScroll']){
 const h=fixture();h.doc.activeElement=h[key];h.run();
 assert.equal(h.context.view,'text');assert.equal(h.doc.activeElement,h[key],'Focused text control remains visible when comparison collapses');
 assert.deepEqual(h.remembered,['compare']);h.frames.forEach(fn=>fn());
 assert.equal(h.textScroll.scrollTop,123);assert.equal(h.imageScroll.scrollTop,456);assert.equal(h.imageScroll.scrollLeft,78);
}
for(const selected of ['compare','text','image']){
 const h=fixture(selected);h.doc.activeElement=h.compare;h.run();
 const expected=selected==='text'?h.text:h.image;
 assert.equal(h.doc.activeElement,expected,'Hidden Compare toggle moves focus to the current visible representation');assert.equal(expected.options.preventScroll,true);
}
const imageFocus=fixture();imageFocus.doc.activeElement=imageFocus.imageScroll;imageFocus.run();assert.equal(imageFocus.context.view,'image');assert.equal(imageFocus.doc.activeElement,imageFocus.imageScroll);
const outside=fixture(),external={id:'external'};outside.doc.activeElement=external;outside.run();assert.equal(outside.context.view,'image');assert.equal(outside.doc.activeElement,external,'Do not move unrelated focus');
const wide=fixture('compare',false);wide.doc.activeElement=wide.copy;wide.run();assert.equal(wide.context.view,'compare');assert.equal(wide.frames.length,0);
for(const key of ['copy','compare']){
 const h=fixture();h[key].hidden=true;h.context.rememberResponsiveFocus({target:h[key],relatedTarget:null});h.doc.activeElement=h.doc.body;h.run();
 assert.equal(h.context.view,key==='copy'?'text':'image');assert.equal(h.doc.activeElement,key==='copy'?h.copy:h.image,'CSS-hidden focus is restored after media-query styles ran first');
}
for(const newerFocus of [true,false]){
 const h=fixture();h.copy.hidden=true;h.context.rememberResponsiveFocus({target:h.copy,relatedTarget:null});
 if(!newerFocus)h.copy.isConnected=false;
 h.doc.activeElement=newerFocus?h.image:h.doc.body;h.run();assert.equal(h.context.view,'image');assert.equal(h.doc.activeElement,newerFocus?h.image:h.doc.body,'Do not resurrect stale or superseded focus');
}
const ordinaryBlur=fixture();ordinaryBlur.context.rememberResponsiveFocus({target:ordinaryBlur.copy,relatedTarget:null});ordinaryBlur.doc.activeElement=ordinaryBlur.doc.body;ordinaryBlur.run();assert.equal(ordinaryBlur.context.view,'image','An ordinary visible-control blur is not remembered as a responsive loss');
const cleared=fixture();cleared.copy.hidden=true;cleared.context.rememberResponsiveFocus({target:cleared.copy,relatedTarget:null});cleared.context.rememberResponsiveFocus({target:cleared.image,relatedTarget:null});cleared.doc.activeElement=cleared.doc.body;cleared.run();assert.equal(cleared.context.view,'image','An unrelated later blur clears the responsive snapshot');
const resetByCSS=fixture();resetByCSS.context.rememberViewportScroll({currentTarget:resetByCSS.textScroll});
assert.equal(resetByCSS.stored.length,0,'Scroll caching does not write storage');
resetByCSS.copy.hidden=resetByCSS.textScroll.hidden=true;resetByCSS.textScroll.scrollTop=0;
resetByCSS.context.rememberResponsiveFocus({target:resetByCSS.copy,relatedTarget:null});resetByCSS.doc.activeElement=resetByCSS.doc.body;resetByCSS.run();resetByCSS.frames.forEach(fn=>fn());
assert.equal(resetByCSS.textScroll.scrollTop,123,'A CSS-hidden viewport returning zero must not overwrite its last visible scroll position');
const saved=resetByCSS.context.positions.get('lp2-00');resetByCSS.textScroll.hidden=true;resetByCSS.context.rememberViewportScroll({currentTarget:resetByCSS.textScroll});assert.equal(resetByCSS.context.positions.get('lp2-00'),saved,'Hidden viewport scroll events do not replace visible positions');
console.log('PASS reader responsive focus: text tools/search/viewport remain visible, hidden Compare returns to selected view, image/outside/wide focus untouched, saved text/image positions retained.');
