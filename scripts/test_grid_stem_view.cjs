/* Archived data + production native figure lifecycle; no browser or model calls. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),source=fs.readFileSync(path.join(root,'grid-stem-view.js'),'utf8');
const archived=JSON.parse(fs.readFileSync(path.join(root,'experiments/records/grid-stem-uncertainty/results.json'),'utf8'));
const api=require('../grid-stem-view.js'),data=api.validate(archived);
const integrated={esc:String,GridStemView:api};vm.createContext(integrated);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),integrated);
const stem={id:'grid-stem-uncertainty'},visual={path:'experiments/records/grid-stem-uncertainty/stem-map.svg',caption:'Audited stem map'};
assert(integrated.experimentVisual(stem,visual).includes('data-stem-page'),'Production figure dispatcher uses the native map');
delete integrated.GridStemView;assert(integrated.experimentVisual(stem,visual).includes('<img'),'Missing module retains the static figure fallback');
const entry=fs.readFileSync(path.join(root,'index.html'),'utf8');assert(entry.indexOf('grid-stem-view.js')<entry.indexOf('experiments.js'),'Native module loads before its dispatcher');
assert.deepEqual(api.rows,{'lp2-49':10,'lp2-50':13,'lp2-51':9});
for(const [page,count] of Object.entries(api.rows)){
 const html=api.grid(data,page,'1:3');
 assert.equal((html.match(/<tr>/g)||[]).length,count+1);
 assert.equal((html.match(/<td>/g)||[]).length,count*8+1);
 assert.equal((html.match(/data-stem-cell=/g)||[]).length,page==='lp2-50'?5:page==='lp2-49'?4:2);
 for(const cell of api.cells(data,page)){
  assert(html.includes('data-stem-cell="'+cell.row+':'+cell.column+'"'));
  const detail=api.detail(cell);assert(detail.includes('row '+cell.row+', column '+cell.column));
  assert(detail.includes('<code>'+cell.archive_token+'</code>'));assert(detail.includes('<code>'+cell.wiki_token+'</code>'));
  assert(detail.includes('#/reader/'+page));
  if(!cell.separate)for(const value of cell.base60_bytes)assert(detail.includes('<strong>'+value+'</strong>'));
 }
}
assert(api.grid(data,'lp2-50','12:5').includes('class="stem-separate" aria-pressed="true"'));
for(const mutate of [d=>d.stem_cells.pop(),d=>d.stem_cells[0].base60_bytes[0]++,d=>d.stem_cells[0].row=99,d=>d.stem_cells[1]={...d.stem_cells[0]},d=>d.separate_case_disagreement.wiki_token='<script>']){
 const bad=structuredClone(data);mutate(bad);assert.throws(()=>api.validate(bad));
}
assert(api.render().includes('Blank cells are not transcribed'));
assert(api.render().includes('stem-map.svg" download'));
assert(!api.render().includes('<details'));
function harness(){
 const doc={activeElement:null};
 const node=()=>({disabled:false,hidden:false,textContent:'',innerHTML:'',listeners:{},addEventListener(type,fn){this.listeners[type]=fn},focus(options){doc.activeElement=this;this.focusOptions=options}});
 const select=node();select.value='lp2-49';const status=node(),retry=node(),info=node(),map=node();retry.hidden=true;
 let buttons=[];
 Object.defineProperty(map,'innerHTML',{set(html){this.html=html;buttons=[...html.matchAll(/data-stem-cell="([^"]+)"/g)].map(([,key])=>({dataset:{stemCell:key},attributes:{},closest(){return this},setAttribute(key,value){this.attributes[key]=value}}))},get(){return this.html||''}});
 map.querySelectorAll=()=>buttons;map.contains=button=>buttons.includes(button);
 const elements={'[data-stem-page]':select,'[data-stem-status]':status,'[data-stem-retry]':retry,'[data-stem-grid]':map,'[data-stem-detail]':info};
 const figure={isConnected:true,ownerDocument:doc,querySelector:selector=>elements[selector]};
 const timers=new Map();let timerId=0;const context={module:{exports:{}},globalThis:{},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++timerId,fn);return timerId},clearTimeout(id){timers.delete(id)},fetch(){throw Error('Unexpected fetch')}};vm.createContext(context);vm.runInContext(source,context);
 const requests=[];let current=true;
 const options={isCurrent:()=>current,fetcher:(url,options)=>new Promise((resolve,reject)=>requests.push({url,resolve,reject,signal:options.signal}))};
 return {api:context.module.exports,figure,select,status,retry,info,map,doc,requests,options,timers,buttons:()=>buttons,leave(){current=false}};
}
(async()=>{
 const h=harness(),loading=h.api.bind(h.figure,h.options);
 assert(h.select.disabled);assert(h.status.textContent.includes('Loading'));assert.equal(h.requests.length,1);
 const sibling=harness(),shared=h.api.bind(sibling.figure,sibling.options);assert.equal(sibling.requests.length,0,'Concurrent figure mounts share one data request');
 h.requests[0].resolve({ok:true,json:async()=>data});await loading;await shared;assert.equal(h.timers.size,0);assert(!sibling.select.disabled);
 const warm=harness();await h.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0,'Validated cache avoids another fetch');
 assert(!h.select.disabled);assert(h.info.innerHTML.includes('row 1, column 3'));
 h.select.value='lp2-50';h.doc.activeElement=h.select;h.select.listeners.change();
 assert(h.info.innerHTML.includes('row 2, column 3'));assert.equal(h.doc.activeElement,h.select);
 const separate=h.buttons().find(button=>button.dataset.stemCell==='12:5');h.map.listeners.click({target:separate});
 assert(h.info.innerHTML.includes('not included in their byte alternatives'));
 assert.equal(separate.attributes['aria-pressed'],'true');assert(h.status.textContent.includes('row 12, column 5 selected'));
 assert(h.buttons().filter(button=>button.attributes['aria-pressed']==='true').length===1);
 h.select.value='lp2-51';h.select.listeners.change();assert(h.info.innerHTML.includes('row 2, column 8'));assert.equal(h.requests.length,1);
 const failure=harness(),initial=failure.api.bind(failure.figure,failure.options);failure.requests[0].resolve({ok:false});await initial;
 assert(!failure.retry.hidden);assert(failure.select.disabled);assert(failure.status.textContent.includes('download'));
 failure.doc.activeElement=failure.retry;const retry=failure.retry.listeners.click(),duplicate=failure.retry.listeners.click();
 assert.equal(failure.requests.length,2);assert(failure.retry.disabled);
 failure.requests[1].resolve({ok:true,json:async()=>data});await Promise.all([retry,duplicate]);
 assert(failure.retry.hidden);assert.equal(failure.doc.activeElement,failure.select);assert.equal(failure.select.focusOptions.preventScroll,true);
 for(const invalid of [true,false]){
  const stale=harness(),request=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;
  stale.requests[0].resolve({ok:!invalid,json:async()=>data});await request;
  assert.equal(stale.status.textContent,before);assert.equal(stale.info.innerHTML,'');assert(stale.select.disabled);
 }
 const timeout=harness(),stalled=timeout.api.bind(timeout.figure,timeout.options);
 [...timeout.timers.values()][0]();await stalled;
 assert(timeout.requests[0].signal.aborted);assert(!timeout.retry.hidden);assert(timeout.select.disabled);
 const recovered=timeout.retry.listeners.click();assert.equal(timeout.requests.length,2);
 timeout.requests[1].resolve({ok:true,json:async()=>data});await recovered;
 const recoveredDetail=timeout.info.innerHTML;assert(!timeout.select.disabled);
 timeout.requests[0].resolve({ok:true,json:async()=>({})});await new Promise(resolve=>setImmediate(resolve));
 assert.equal(timeout.info.innerHTML,recoveredDetail,'Late timed-out data cannot overwrite successful retry');
 const invalid=harness(),request=invalid.api.bind(invalid.figure,invalid.options);invalid.requests[0].resolve({ok:true,json:async()=>({})});await request;
 assert(!invalid.retry.hidden);assert(invalid.select.disabled);assert.equal(invalid.info.innerHTML,'');
 console.log('PASS: all archived marked cells/bytes, 8-column page maps, native controls, selected detail, validation, loading/error/retry, focus and stale completion guards. No rendered layout claim.');
})().catch(error=>{console.error(error);process.exitCode=1});
