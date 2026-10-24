const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),api=require('../reader/manuscript-search.js');
const root=path.join(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8')),index=read('data/index.json'),load=id=>read('data/pages/'+id+'.json');
const warning=load('lp1-01'),koan=load('lp1-06'),grid=load('lp2-15');
const local=api.pageHits(warning,index.alphabet,'EXPERIENCE YOUR DEATH',['context']);assert.equal(local.length,1);assert.equal(local[0].line,null);assert.equal(local[0].match,'EXPERIENCE YOUR DEATH');
const rows=api.sourceRows(grid.raw);assert.equal(rows[5].line,null);assert.equal(rows[6].line,null);assert.equal(rows[7].line,6);
const source=grid.lines[5].raw,parts=source.split('-'),query=parts.slice(1,3).join(' '),raw=api.pageHits(grid,index.alphabet,query,['raw']);assert(raw.some(h=>h.line===6&&source.slice(h.start,h.end)===h.match));
const unaligned={...grid,reviewed_text:'extra row\n'+grid.reviewed_text};assert(api.pageHits(unaligned,index.alphabet,'extra row',['reviewed']).every(h=>h.line===null),'A derivative with added rows does not invent source addresses');
assert(api.pageHits(grid,index.alphabet,'&',['raw']).length===0,'Standalone separators are not source rows');assert.equal(api.find('<script>sample</script>','<script>')[0].match,'<script>','Untrusted-looking matches remain text, not HTML');
(async()=>{
 let active=0,max=0,calls=[];const result=await api.search(index.pages,index.alphabet,async id=>{calls.push(id);active++;max=Math.max(max,active);await new Promise(r=>setImmediate(r));active--;return load(id)},{query:'STUDY WITH A MASTER',layers:['context']});
 assert.equal(result.checked,75);assert.equal(calls.length,75);assert(max<=4);assert.equal(result.total,1,'Whole-section contextual hits are deduplicated');assert.equal(result.results[0].section,'first-koan');assert.equal(result.results[0].page,'lp1-06');assert.equal(result.results[0].line,null);assert.deepEqual(result.results[0].section_pages,koan.reading.section_pages);
 const labels=await api.search(index.pages,index.alphabet,async id=>load(id),{query:grid.lines[5].latin.split('-').slice(1,3).join(' '),layers:['latin']});assert(labels.results.some(h=>h.page==='lp2-15'&&h.line===6));
 const partial=await api.search(index.pages,index.alphabet,async id=>{if(id==='lp1-01')throw Error('offline');return load(id)},{query:'EXPERIENCE YOUR DEATH',layers:['context']});assert.equal(partial.checked,74);assert.deepEqual(partial.failed,['lp1-01']);assert.equal(partial.total,0,'A missing page is reported separately from a complete no-match');
 const bad=await api.search(index.pages.slice(0,1),index.alphabet,async()=>({id:'wrong',raw:''}),{query:'test'});assert.deepEqual(bad.failed,['lp1-00']);
 const abort=new AbortController(),pending=[];const cancelled=api.search(index.pages,index.alphabet,(id,signal)=>new Promise((resolve,reject)=>{pending.push({id,resolve});signal.addEventListener('abort',()=>{const e=Error('cancelled');e.name='AbortError';reject(e)},{once:true})}),{query:'MASTER',signal:abort.signal});assert.equal(pending.length,4);abort.abort();await assert.rejects(cancelled,{name:'AbortError'});pending.forEach(r=>r.resolve(load(r.id)));assert.equal(pending.length,4,'Cancellation never starts the remaining71 requests');
 const retry=await api.search(index.pages,index.alphabet,async id=>load(id),{query:'EXPERIENCE YOUR DEATH',layers:['context']});assert.equal(retry.total,1);assert.equal(retry.checked,75);
 console.log('PASS: actual current/other-page source-layer phrases, offsets/rows/separators, contextual deduplication without invented alignment, max4 concurrent metadata requests, partial failures/cancel/retry.');
})().catch(e=>{console.error(e);process.exitCode=1});

// Dedicated reader keeps native modified links and renders exact offsets in the selected stored layer.
(async()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.join(root,'manuscript-reader.js'),'utf8');
 const fragment=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
 const state={id:'lp1-06'},events=[];let value,mark;
 const context={state,navigationVersion:0,URLSearchParams,addressOf:id=>({id}),async go(target){state.id=target.id;events.push('go');return true},async render(){events.push(['render',state.mode]);},history:{replaceState(a,b,hash){events.push(['hash',hash])}},node(tag,text){mark={tag,textContent:text,scrollIntoView(){events.push('reveal')}};return mark},document:{createTextNode:text=>({textContent:text}),querySelector(){return{querySelector:()=>value}}}};
 vm.createContext(context);vm.runInContext(fragment('function storedMatchHash(','let finderDraft='),context);
 const cases=[...local,...api.pageHits(warning,index.alphabet,warning.reading.literal.slice(5,22),['literal']), ...raw.filter(h=>h.line===6).slice(0,1), ...api.pageHits(grid,index.alphabet,'3299',['latin','reviewed'])];
 for(const hit of cases){
  const p=load(hit.page);const text=hit.line!==null?(hit.layer==='latin'?p.lines[hit.line-1].latin:api.sourceRows(hit.layer==='reviewed'?p.reviewed_text:p.raw).find(r=>r.line===hit.line).text):hit.layer==='context'?p.reading.reading:p.reading.literal;
  value={textContent:text,replaceChildren(...nodes){this.children=nodes}};events.length=0;
  let prevented=false;await context.openStoredMatchEvent({button:0,preventDefault(){prevented=true}},hit);
  assert(prevented);assert.equal(state.mode,hit.layer);assert.equal(mark.textContent,hit.match);assert.equal(value.children.map(n=>n.textContent).join(''),text,'Highlighting preserves exact layer bytes');assert(events.includes('reveal'));
  assert.equal(events.find(e=>Array.isArray(e)&&e[0]==='hash')[1],context.storedMatchHash(hit));
  const params=new URLSearchParams(context.storedMatchHash(hit).split('?')[1]);assert.equal(params.get(hit.line===null?'textmatch':'match'),hit.start+'-'+hit.end);
  for(const modifier of ['ctrlKey','metaKey','shiftKey','altKey']){events.length=0;context.openStoredMatchEvent({button:0,[modifier]:true,preventDefault(){throw Error('Must remain native')}},hit);assert.deepEqual(events,[])}
  context.openStoredMatchEvent({button:1,preventDefault(){throw Error('Must remain native')}},hit);
 }
 assert(source.includes('a.onclick=event=>openStoredMatchEvent(event,hit)'));
 console.log('PASS: production stored-result navigation preserves native modified links, exact literal/context/raw/Latin/reviewed offsets and layer bytes, including numeric duplicate layers.');
})().catch(e=>{console.error(e);process.exitCode=1});
