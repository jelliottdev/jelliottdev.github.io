/* Production Downloads interactions with a small DOM harness; no rendered-device claims. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..');
function setup(files){
 const nodes=new Map();let pageHTML='';
 const document={activeElement:null,addEventListener(){}};
 function node(id,attrs=''){
  return {id,value:attrs.match(/value="([^"]*)"/)?.[1]||'',textContent:'',innerHTML:'',isConnected:true,
   hidden:/\bhidden\b/.test(attrs),disabled:false,
   focus(options){document.activeElement=this;this.focusOptions=options}};
 }
 const $=key=>{if(!nodes.has(key))nodes.set(key,node(key.slice(1)));return nodes.get(key)};
 const ctx={localStorage:{getItem:()=>null},document,$,db:{catalog:{files}},renderId:1,
  head:()=>'',footer:()=>'',esc:s=>String(s??'').replace(/&/g,'&amp;').replace(/"/g,'&quot;'),
  matches:(text,q)=>text.toLowerCase().includes(q.toLowerCase()),
  main:{set innerHTML(html){
   for(const n of nodes.values())n.isConnected=false;nodes.clear();pageHTML=html;
   for(const m of html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g))nodes.set('#'+m[1],node(m[1],m[0]));
  }}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'access.js'),'utf8'),ctx);
 return {ctx,$,document,get html(){return pageHTML}};
}
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'),'utf8'));
const rows=html=>[...html.matchAll(/<tr><td><a href="([^"]+)" download>/g)].map(m=>m[1]);
(async()=>{
 const h=setup(catalog.files);await h.ctx.downloadsPage('',1);
 const {$,document}=h,query=$('#download-query'),prev=$('#download-prev'),next=$('#download-next');
 assert.match(h.html,/class="download-bundle-table"/,'Top bundles remain present');
 assert.match(h.html,/aria-label="File results pages"/);
 const wanted=catalog.files.filter(f=>f.role!=='ZIP bundle').map(f=>f.path),seen=[];
 assert.ok(wanted.length>50,'Use the actual growing catalog rather than a tiny implementation-shaped fixture');
 for(let page=1;;page++){
  const current=rows($('#download-results').innerHTML);assert.ok(current.length<=50);seen.push(...current);
  assert.match($('#download-page').textContent,new RegExp(`^Page ${page} of `));
  assert.equal($('#download-query'),query,'Typing control is never recreated');
  assert.equal($('#download-next'),next,'Pagination button is never recreated');
  if(next.disabled)break;
  document.activeElement=next;next.onclick();
 }
 assert.deepEqual(seen,wanted,'Every catalog file remains traversable once, in original order');
 assert.equal(document.activeElement,$('#download-results'),'Disabling a focused endpoint control leaves focus in visible results');
 assert.equal(document.activeElement.focusOptions.preventScroll,true);
 prev.onclick();assert.ok(rows($('#download-results').innerHTML).length<=50);
 document.activeElement=query;query.value='lp2-15';query.oninput();
 assert.match($('#download-page').textContent,/^Page 1 of /,'Search resets the page');
 assert.equal(document.activeElement,query,'Typing retains focus');
 assert.ok(rows($('#download-results').innerHTML).every(p=>catalog.files.find(f=>f.path===p)));
 $('#download-type').value='images';$('#download-type').onchange();
 assert.match($('#download-page').textContent,/^Page 1 of /);
 query.value='no-such-file-3301-qa';query.oninput();
 assert.equal($('#download-count').textContent,'0 files');assert.equal($('#download-pagination').hidden,true);
 assert.match($('#download-results').innerHTML,/No matching files/);assert.equal(rows($('#download-results').innerHTML).length,0);
 query.value='';$('#download-type').value='';$('#download-release').value='LP1';$('#download-release').onchange();
 const lp1=rows($('#download-results').innerHTML);assert.ok(lp1.length>0);
 for(const p of lp1){const f=catalog.files.find(f=>f.path===p);assert.ok(f.release==='LP1'||f.releases?.includes('LP1'))}
 $('#download-release').value='';$('#download-release').onchange();assert.equal(rows($('#download-results').innerHTML).length,50);
 // A route-provided page query still initializes the filter; detached callbacks cannot rewrite a replacement route.
 await h.ctx.downloadsPage('lp2-15',1);assert.equal($('#download-query').value,'lp2-15');
 const staleNext=$('#download-next'),staleRows=$('#download-results'),before=staleRows.innerHTML;
 h.ctx.renderId=2;staleNext.disabled=false;staleNext.onclick();assert.equal(staleRows.innerHTML,before);
 // Fetch failure leaves existing content intact for the router's error recovery; stale successful loads do not render.
 const failure=setup([]);failure.ctx.db.catalog=null;failure.ctx.fetch=async()=>({ok:false});
 await assert.rejects(()=>failure.ctx.downloadsPage('',1),/download catalog could not be loaded/);
 assert.equal(failure.html,'');
 let resolve;failure.ctx.fetch=()=>new Promise(r=>resolve=r);const pending=failure.ctx.downloadsPage('',1);
 failure.ctx.renderId=2;resolve({ok:true,json:async()=>({files:[]})});await pending;assert.equal(failure.html,'');
 console.log(`PASS: ${wanted.length} real catalog files traverse bounded50-row pages; stable controls, filter reset, empty/error, scoped route and stale callbacks checked. DOM harness does not verify device rendering.`);
})().catch(error=>{console.error(error);process.exitCode=1});
