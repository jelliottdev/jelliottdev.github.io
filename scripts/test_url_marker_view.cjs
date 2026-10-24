/* Actual archived marker/GP data and production figure states; no browser or network. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const base='experiments/records/url-marker-affine-census/',results=read(base+'results.json'),matches=read(base+'matches.json');
const alphabet=read('data/index.json').alphabet,source=fs.readFileSync(path.join(root,'url-marker-view.js'),'utf8');
const api=require('../url-marker-view.js'),data=api.validate(results,matches),window=data.https;
const page=read('data/pages/'+window.page+'.json'),byRune=new Map(alphabet.map(a=>[a.rune,a.index]));
const raw=[...page.lines.map(line=>line.raw).join('')].filter(r=>byRune.has(r));
assert.deepEqual(raw.slice(window.rune_start_zero_based,window.rune_end_exclusive).map(r=>byRune.get(r)),window.cipher_indices);
const content=api.content(data,alphabet);
for(const index of window.cipher_indices){const entry=alphabet.find(a=>a.index===index);assert(content.includes(entry.rune),'Only actual canonical glyphs are used');}
assert.equal((content.match(/<li>/g)||[]).length,5);assert.equal((content.match(/<th scope="row">/g)||[]).length,4);
for(const name of ['WWW','HTTP','HTTPS','ONION'])assert(content.includes(`<th scope="row">${name}</th><td>${results.literal_matches_by_token[name]}</td>`));
assert(content.includes('HTTP is the prefix of this same HTTPS window'));assert(content.includes('three identical adjacent source runes'));
assert(content.includes('not establish a web address'));assert(content.includes('#/reader/lp2-36'));
assert(!api.content(data,alphabet.map(a=>({...a,rune:'<bad>'}))).includes('<bad>'),'Unavailable/unverified glyphs fall back to Latin labels');
assert(api.render().includes('download>Download the complete SVG figure'),'Fallback source is available before loading');
for(const mutate of [r=>r.total_literal_matches=3,r=>r.literal_matches_by_token.WWW=1,r=>r.original_equal_symbol_triples.push(1)]){
 const bad=structuredClone(results);mutate(bad);assert.throws(()=>api.validate(bad,matches));
}
const wrongPrefix=structuredClone(matches);wrongPrefix[0].rune_start_zero_based++;assert.throws(()=>api.validate(results,wrongPrefix));
const record=read(base+'record.json'),integrated={esc:String,UrlMarkerView:api};vm.createContext(integrated);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),integrated);
assert(integrated.experimentVisual(record,record.visuals[0]).includes('data-url-content'));
assert(integrated.experimentVisual({...record,reproduction:{outputs:[]}},record.visuals[0]).includes('<img'),'Undeclared payloads cannot enable fetching');
delete integrated.UrlMarkerView;assert(integrated.experimentVisual(record,record.visuals[0]).includes('<img'),'Missing module keeps the static chart');
function runtime(){
 const timers=new Map();let sequence=0;
 const context={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(++sequence,fn);return sequence},clearTimeout(id){timers.delete(id)}};
 vm.createContext(context);vm.runInContext(source,context);return {api:context.module.exports,timers};
}
function harness(run=runtime()){
 const doc={activeElement:null,body:{}},requests=[];
 const node=()=>({textContent:'',innerHTML:'',hidden:false,disabled:false,listeners:{},addEventListener(type,fn){this.listeners[type]=fn},focus(options){doc.activeElement=this;this.focusOptions=options}});
 const status=node(),retry=node(),view=node(),heading=node();retry.hidden=true;view.querySelector=()=>heading;
 const nodes={'[data-url-status]':status,'[data-url-retry]':retry,'[data-url-content]':view};
 const figure={isConnected:true,ownerDocument:doc,querySelector:s=>nodes[s]};let current=true;
 const options={alphabet,isCurrent:()=>current,fetcher:(url,options)=>new Promise((resolve,reject)=>requests.push({url,signal:options.signal,resolve,reject}))};
 const respond=(offset=0,invalid=false)=>requests.slice(offset).forEach(request=>request.resolve({ok:true,json:async()=>invalid?{}:request.url.endsWith('matches.json')?matches:results}));
 return {...run,figure,status,retry,view,heading,doc,requests,options,respond,leave(){current=false}};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const h=harness(),initial=h.api.bind(h.figure,h.options);assert.equal(h.requests.length,2);assert(h.status.textContent.includes('Loading'));
 for(const request of h.requests)assert([base+'results.json',base+'matches.json'].includes(request.url),'No arbitrary data URL');
 const sibling=harness({api:h.api,timers:h.timers}),shared=h.api.bind(sibling.figure,sibling.options);assert.equal(sibling.requests.length,0);
 h.respond();await initial;await shared;assert.equal(h.timers.size,0);assert(h.view.innerHTML.includes('One candidate location'));assert(sibling.view.innerHTML.includes('One candidate location'));
 const warm=harness({api:h.api,timers:h.timers});await warm.api.bind(warm.figure,warm.options);assert.equal(warm.requests.length,0);
 const failed=harness(),bad=failed.api.bind(failed.figure,failed.options);failed.respond(0,true);await bad;
 assert(!failed.retry.hidden);assert(failed.status.textContent.includes('download'));assert.equal(failed.view.innerHTML,'');
 failed.doc.activeElement=failed.retry;const retry=failed.retry.listeners.click();await failed.retry.listeners.click();assert.equal(failed.requests.length,4,'No overlapping duplicate retry');
 failed.doc.activeElement=failed.doc.body;failed.respond(2);await retry;
 assert(failed.retry.hidden);assert.equal(failed.doc.activeElement,failed.heading);assert.equal(failed.heading.focusOptions.preventScroll,true);
 for(const fail of [true,false]){
  const stale=harness(),pending=stale.api.bind(stale.figure,stale.options);stale.leave();const before=stale.status.textContent;
  if(fail)stale.requests[0].reject(Error('offline'));else stale.respond();await pending;
  assert.equal(stale.status.textContent,before);assert.equal(stale.view.innerHTML,'');
 }
 const stalled=harness(),pending=stalled.api.bind(stalled.figure,stalled.options);[...stalled.timers.values()][0]();await pending;
 assert(stalled.requests.every(r=>r.signal.aborted));assert(!stalled.retry.hidden);
 const recovery=stalled.retry.listeners.click();stalled.respond(2);await recovery;const saved=stalled.view.innerHTML;
 stalled.respond(0,true);await flush();assert.equal(stalled.view.innerHTML,saved,'Timed-out payload cannot replace the successful retry');
 const moved=harness(),first=moved.api.bind(moved.figure,moved.options);moved.requests[0].reject(Error('offline'));await first;
 moved.doc.activeElement=moved.retry;const again=moved.retry.listeners.click();const elsewhere={};moved.doc.activeElement=elsewhere;moved.respond(2);await again;assert.equal(moved.doc.activeElement,elsewhere);
 console.log('PASS: actual source runes/GP indices, all marker counts/prefix/equality rule, declared-path dispatcher/fallback, shared cache, malformed/error/timeout/retry/focus and stale guards. DOM/source checks only.');
})().catch(error=>{console.error(error);process.exitCode=1});
