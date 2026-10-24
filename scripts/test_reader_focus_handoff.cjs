/* Latest supplied reader interaction contracts, evaluated against production functions. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../manuscript-reader.js'),'utf8');
const line=name=>source.match(new RegExp('^(?:async )?function '+name+'\\(.*$','m'))[0];
const slice=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
const rows=require('../reader/source-rows.js');global.ReaderSourceRows=rows;const A=require('../reader/reader-address.js');
const db=JSON.parse(fs.readFileSync(require.resolve('../data/index.json'),'utf8'));
function context(values){const c={...values};vm.createContext(c);return c}
(async()=>{
 for(const raw of ['15 words 2','LP2 page 15 words 2-3'])assert(A.parse(raw).error,'Words require one explicit line');
 assert.equal(A.parse('3299'),null,'Long numeric text stays searchable');
 // Actual source-row rendering, including archive markers and raw copy bytes.
 class Node{
  constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.dataset={};this.className='';this.classList={add:value=>this.className+=' '+value}}
  append(...values){this.children.push(...values)}replaceChildren(...values){this.children=values}setAttribute(){}querySelector(){return this.root||null}
 }
 const c=context({state:{mode:'raw',numbers:true,wrap:true,target:null},A,db,ReaderSourceRows:rows,document:{createTextNode:text=>new Node('text',text)},node(tag,text,parent){const n=new Node(tag,text);parent?.append(n);return n},go(){},addressOf(){}});
 vm.runInContext(line('versions')+'\n'+line('effectiveMode')+'\n'+line('originalText')+'\n'+line('drawWords')+'\n'+slice('function drawText(','function imageState('),c);
 let count=0;for(const meta of db.pages){const p=JSON.parse(fs.readFileSync(require.resolve('../data/pages/'+meta.id+'.json'),'utf8')),root=new Node('div'),article={querySelector:()=>root};c.drawText(article,p);const numbered=root.children.filter(n=>n.className.startsWith('source-line'));assert.equal(numbered.length,p.lines.length,p.id);assert.equal(c.originalText(p,'raw'),p.raw);numbered.forEach((n,i)=>assert.equal(n.dataset.line,i+1));count+=numbered.length;}
 assert.equal(count,797);
 // Enter awaits async validation; subsequent edits/close cancel commit. Keyboard result traversal uses the same production binding.
 const nodes=new Map(),input={value:'20:4',setAttribute(){},focus(){document.activeElement=this},select(){}},finder={open:true,listeners:{},showModal(){this.open=true},addEventListener(t,f){this.listeners[t]=f}},button={clicks:0,click(){this.clicks++},focus(){document.activeElement=this}},second={focus(){document.activeElement=this}};
 const document={activeElement:input};nodes.set('#query',input);nodes.set('#finder',finder);nodes.set('#suggestions',{setAttribute(){},querySelectorAll:()=>[button,second]});nodes.set('#suggestions .suggestion',button);nodes.set('#suggestions button',button);
 let release;const f=context({document,queryVersion:0,searchController:null,$:s=>nodes.get(s),db,search:()=>new Promise(resolve=>release=resolve)});
 vm.runInContext(slice("let finderDraft=",'function bindSplit('),f);f.bindFinder();
 const submit=f.$('#query').onkeydown({key:'Enter',preventDefault(){}});assert.equal(button.clicks,0);release();await submit;assert.equal(button.clicks,1);
 const stale=f.$('#query').onkeydown({key:'Enter',preventDefault(){}});input.value='21:3';finder.listeners.close();release();await stale;assert.equal(button.clicks,1,'Closed finder cannot commit an older Enter');
 document.activeElement=button;nodes.get('#suggestions').onkeydown({key:'ArrowUp',preventDefault(){}});assert.equal(document.activeElement,input);
 document.activeElement=button;nodes.get('#suggestions').onkeydown({key:'End',preventDefault(){}});assert.equal(document.activeElement,second);
 // Direct navigation checks sequence after async page validation, preserving latest intent.
 let resolveOld;const nav=context({state:{id:'lp2-15',range:null},navigationVersion:0,db,A,innerWidth:1000,$:()=>({open:false}),remember(){},render:async()=>{},toast(){},pageId:(r,n)=>r.toLowerCase()+'-'+String(n).padStart(2,'0'),getPage:id=>id==='lp2-16'?new Promise(r=>resolveOld=r):Promise.resolve({id,raw:'x',lines:[{raw:'x'}]}),window:{history:{pushState(){}}},structuredClone});
 vm.runInContext(slice('async function go(','function turn('),nav);const old=nav.go({release:'LP2',pages:[16,16],lines:[1,1],words:null},{history:false});await nav.go({release:'LP2',pages:[17,17],lines:null,words:null},{history:false});resolveOld({id:'lp2-16',raw:'x',lines:[{raw:'x'}]});assert.equal(await old,false);assert.equal(nav.state.id,'lp2-17');
 assert(source.includes('ReaderManuscriptSearch.search(db.pages'),'Production full search, not prototype ten-page truncation');
 assert(!source.includes('/archive/'));
 console.log('PASS reader handoff: all797 rendered rows/raw copies; explicit address grammar; async Enter/close cancellation; result keys; stale navigation; full production search.');
})().catch(error=>{console.error(error);process.exitCode=1});
