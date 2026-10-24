/* Production drawer event handlers; native modal behavior is browser QA separately. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),api=require('../site-navigation.js');
class Node{
 constructor(){this.listeners={};this.attrs={};this.isConnected=true;this.value='';this.scrollTop=0;this.dataset={};}
 addEventListener(type,fn){this.listeners[type]=fn;}setAttribute(key,value){this.attrs[key]=value;}removeAttribute(key){delete this.attrs[key];}
 focus(options){this.doc.activeElement=this;this.options=options;}select(){this.selected=true;}setCustomValidity(value){this.validity=value;}reportValidity(){return !this.validity;}
 showModal(){this.open=true;this.modalCalls=(this.modalCalls||0)+1;}close(){this.open=false;this.listeners.close?.();}
 getBoundingClientRect(){return{left:0,right:276,top:0,bottom:568};}
 fire(type,extra={}){const event={target:this,button:0,preventDefault(){this.prevented=true},...extra};this.listeners[type]?.(event);return event;}
}
function fixture(page='home',hash=''){
 const doc={activeElement:null,listeners:{},body:{dataset:{sidebarPage:page},append(node){doc.drawer=node}},addEventListener(type,fn){this.listeners[type]=fn;}};
 const win={location:{hash,assign(href){this.destination=href}},listeners:{},addEventListener(type,fn){this.listeners[type]=fn}};doc.defaultView=win;
 const node=()=>Object.assign(new Node(),{doc});const trigger=node(),close=node(),form=node(),field=node(),links=api.primary.map(([label,href,id])=>Object.assign(node(),{label,href,dataset:{siteDestination:id}}));
 form.querySelector=()=>field;
 const dialog=node();dialog.querySelector=s=>s==='.site-close'?close:s==='form'?form:null;dialog.querySelectorAll=s=>s==='a'?links:s==='[data-site-destination]'?links:[];
 doc.createElement=tag=>{assert.equal(tag,'dialog');return dialog};doc.getElementById=id=>id==='site-sidebar'?doc.drawer:null;
 doc.querySelector=s=>s==='.site-menu'?trigger:s==='dialog[open]:not(#site-sidebar)'?doc.otherDialog:null;
 const navigation=api.create(doc,win);return{doc,win,trigger,close,form,field,dialog,links,navigation};
}
const h=fixture();assert.equal(api.primary.length,5);assert.equal(api.primary.filter(r=>r[0]==='Research map').length,1);assert(!api.primary.some(r=>r[0]==='Experiments'));assert.equal(api.secondary.length,6);
assert(h.dialog.innerHTML.includes('role="search"'));assert(!h.dialog.innerHTML.includes('/archive/'));assert.equal(h.links.find(l=>l.dataset.siteDestination==='home').attrs['aria-current'],'page');
h.trigger.fire('click');assert(h.dialog.open);assert.equal(h.doc.activeElement,h.close,'Ordinary menu opening does not summon the phone keyboard');assert.equal(h.trigger.attrs['aria-expanded'],'true');
h.dialog.scrollTop=400;const ctrl={key:'k',ctrlKey:true,preventDefault(){this.prevented=true}};h.doc.listeners.keydown(ctrl);assert(ctrl.prevented);assert.equal(h.doc.activeElement,h.field);assert(h.field.selected);assert.equal(h.dialog.scrollTop,0);assert.equal(h.dialog.modalCalls,1,'CtrlK reuses the open native modal');
h.field.value='   ';h.form.fire('submit');assert(h.dialog.open);assert.equal(h.field.validity,'Enter a search term.');assert.equal(h.win.location.destination,undefined);
h.field.fire('input');assert.equal(h.field.validity,'');h.field.value=' row routes & LP2-15 ';h.form.fire('submit');assert.equal(h.win.location.destination,'library.html#/search?q=row%20routes%20%26%20LP2-15');assert(!h.dialog.open);assert.equal(h.doc.activeElement,h.trigger);
h.navigation.open();const cancelled=h.dialog.fire('cancel');assert(cancelled.prevented);assert(!h.dialog.open);assert.equal(h.doc.activeElement,h.trigger);assert.equal(h.trigger.attrs['aria-expanded'],'false');
h.navigation.open();h.dialog.fire('click',{clientX:290,clientY:120});assert(!h.dialog.open,'Backdrop click closes');h.navigation.open();h.dialog.fire('click',{clientX:100,clientY:120});assert(h.dialog.open,'Interior whitespace is not backdrop');h.navigation.close();
h.doc.otherDialog={open:true};h.navigation.open(true);assert(!h.dialog.open,'Do not stack navigation over file review or another document dialog');assert.equal(api.create(h.doc,h.win),null,'One mounted drawer per document');
for(const [page,hash,key] of [['map','','research'],['idea','','idea'],['reader','','reader'],['library','#/experiment/real','research'],['library','#/guide/atbash','guides'],['app','#/experiments/real','research']]){const f=fixture(page,hash);assert.equal(f.links.find(l=>l.attrs['aria-current']==='page')?.dataset.siteDestination,key);}
const home=fs.readFileSync(require.resolve('../home.html'),'utf8'),css=fs.readFileSync(require.resolve('../site-navigation.css'),'utf8');
assert(home.includes('data-sidebar-page="home"'));assert(home.includes('class="site-masthead"'));assert(!home.includes('id="site-search"'),'No persistent header search remains');assert(home.includes('research.html#mode=graph')&&home.includes('research.html#mode=list'));
assert(home.includes('these files are not uploaded or analyzed'),'Production attachment boundary remains explicit');assert(home.includes('id="file-preview" class="file-preview" tabindex="0"'));
assert(css.includes('max-width:calc(100vw - 44px)'));assert(css.includes('overscroll-behavior:contain'));assert(css.includes('.site-sidebar-search input{font-size:16px}'));
console.log('PASS shared navigation: five primary/six reference links, one research entry, native modal/close/Escape/backdrop/CtrlK, focus/blank-input/search routes/current route, home intake preserved; source/DOM only.');

assert.equal(api.primary.find(([, ,id])=>id==='idea')[1],'investigate.html?v=complete-current-20261024','Every shared drawer opens the fresh checker entry');
assert(home.includes('href="investigate.html?v=complete-current-20261024"'),'Home checker heading bypasses older cached HTML');
