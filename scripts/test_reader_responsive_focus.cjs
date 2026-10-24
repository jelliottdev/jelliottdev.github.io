/* Compact reader migration: production state functions, no browser/network calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../manuscript-reader.js'),'utf8');
const line=name=>source.match(new RegExp('^(?:async )?function '+name+'\\(.*$','m'))[0];
const block=(name,next)=>source.slice(source.indexOf('function '+name+'('),source.indexOf(next,source.indexOf('function '+name+'(')));
function fixture(){
 const state={id:'lp2-15',view:'compare',navigation:'turn'},positions=new Map(),doc={body:{},activeElement:null};let renders=0;
 const make=(text,top)=>({scrollTop:top,scrollLeft:17,hidden:false,isConnected:true,getClientRects(){return this.hidden?[]:[{}]},getBoundingClientRect(){return{top:0,bottom:600,height:600}},querySelectorAll(){return[]},closest(s){return text&&s==='.text-cell'?{}:null},matches(){return false},focus(){doc.activeElement=this}});
 const image=make(false,456),text=make(true,350),article={getBoundingClientRect:()=>({top:0,height:900}),querySelector:s=>s==='.text-viewport'?text:image};
 const flow={dataset:{navigation:'turn'}},viewport={getBoundingClientRect:()=>({top:0,bottom:600})};
 const c={state,positions,document:doc,innerWidth:390,$:s=>s==='#flow'?flow:s==='#viewport'?viewport:{focus(){}},$$:()=>[],fitImage(){},async render(){renders++},hiddenResponsiveFocus:null};
 doc.querySelector=s=>s.startsWith('article[data-id=')&&s.includes('-viewport')?(s.includes('.text-')?text:image):article;
 vm.createContext(c);vm.runInContext(block('remember','function updateBar')+'\n'+line('ownsHorizontalArrows')+'\n'+line('setView')+'\n'+block('fitReaderViewport','let resize;'),c);
 return{c,state,positions,doc,image,text,get renders(){return renders}};
}
(async()=>{
 const h=fixture();h.c.remember();assert.equal(h.positions.get(h.state.id).text,350);assert.equal(h.positions.get(h.state.id).image,456);
 h.text.hidden=true;h.text.scrollTop=0;h.c.remember();assert.equal(h.positions.get(h.state.id).text,350,'CSS-hidden text cannot overwrite the last visible position');
 h.image.hidden=true;h.image.scrollTop=0;h.c.remember();assert.equal(h.positions.get(h.state.id).image,456,'Hidden image cannot overwrite its last position');
 for(const focus of ['text','image']){const f=fixture();f.doc.activeElement=f[focus];f.c.fitReaderViewport();await Promise.resolve();assert.equal(f.state.view,focus);assert.equal(f.doc.activeElement,f[focus],'Focus returns to the regenerated visible viewport')}
 const hidden=fixture();hidden.text.hidden=true;hidden.doc.activeElement=hidden.doc.body;hidden.c.hiddenResponsiveFocus={target:hidden.text,text:true};hidden.c.fitReaderViewport();assert.equal(hidden.state.view,'text','Responsive blur snapshot keeps text selected');
 const superseded=fixture();superseded.c.hiddenResponsiveFocus={target:superseded.text,text:true};superseded.doc.activeElement=superseded.image;superseded.c.fitReaderViewport();assert.equal(superseded.state.view,'image','A newer focus wins over an old blur snapshot');
 const wide=fixture();wide.c.innerWidth=1000;wide.c.fitReaderViewport();assert.equal(wide.state.view,'compare');assert.equal(wide.renders,1,'Reflow restores the saved source anchor even when view stays the same');
 const view=fixture();await view.c.setView('compare');assert.equal(view.state.view,'image');view.c.innerWidth=1000;await view.c.setView('text');assert.equal(view.state.view,'text');
 for(const width of [101,100,99]){const pane={scrollWidth:width,clientWidth:99};assert.equal(view.c.ownsHorizontalArrows({closest:()=>pane}),width>100)}
 assert.equal(view.c.ownsHorizontalArrows({closest:()=>null}),false);
 console.log('PASS compact reader focus: visible-only scroll merging, responsive focused pane, stale blur, narrow Compare, and native overflowing-pane arrows.');
})().catch(error=>{console.error(error);process.exitCode=1});
