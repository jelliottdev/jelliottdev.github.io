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

// Reopening a current result has no hashchange; restore its exact marks after closing Find.
{
 const vm=require('node:vm'),source=fs.readFileSync(path.join(root,'manuscript-reader.js'),'utf8');
 const handler=source.slice(source.indexOf('function openManuscriptSearchResult('),source.indexOf('function drawManuscriptSearchResults('));
 const events=[],hash='#lp1-06?view=text&version=reading&reading=context&textmatch=38-60';
 const context={location:{hash},URLSearchParams,closeFind:()=>events.push('clear'),applyAddressHighlight:p=>events.push(['address',p.get('line')]),applyTextMatch:p=>events.push(['mark',p.get('textmatch')])};
 vm.createContext(context);vm.runInContext(handler,context);
 context.openManuscriptSearchResult({button:0},hash);
 assert.deepEqual(events,['clear',['address',null],['mark','38-60']]);
 events.length=0;context.openManuscriptSearchResult({button:0},'#lp2-15?view=text&line=6&match=2-5');
 assert.deepEqual(events,['clear'],'A different target uses the normal hashchange loader');
 for(const modifier of ['ctrlKey','metaKey','shiftKey','altKey']){events.length=0;context.openManuscriptSearchResult({button:0,[modifier]:true},hash);assert.deepEqual(events,[],'Modified links keep the current search available');}
 events.length=0;context.openManuscriptSearchResult({button:1},hash);assert.deepEqual(events,[]);
 assert(source.includes('a.onclick=event=>openManuscriptSearchResult(event,a.hash)'));
 console.log('PASS: same-target search result restores exact highlighting after Find closes; other targets and modified clicks retain native navigation.');
}
