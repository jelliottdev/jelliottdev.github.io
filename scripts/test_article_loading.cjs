const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const full=JSON.parse(fs.readFileSync(path.join(root,'data/articles.json'),'utf8'));
const light=JSON.parse(fs.readFileSync(path.join(root,'data/article-search.json'),'utf8'));
assert.deepEqual(light,full.map(({html,...rest})=>rest));
for(const article of light){
 assert.equal(fs.readFileSync(path.join(root,'articles',article.source||article.id+'.html'),'utf8').replace(/\r\n?/g,'\n'),
              full.find(a=>a.id===article.id).html);
}
const search=require('../search-engine.js');
for(const query of ['Atbash','φ(n)','circumference','dots','padding','impose nothing']){
 assert.deepEqual(search.search({articles:light},query),search.search({articles:full},query));
}
async function checkNavigationRace(oldRequestFails){
 const pending=new Map();
 const main={innerHTML:'',focus(){},querySelector(){return {textContent:this.innerHTML}}};
 const sandbox={
  db:{articles:[{id:'older'},{id:'newer'}]},main,renderId:0,URLSearchParams,
  location:{hash:'#/wiki/older'},closeSearchSuggestions(){},setNavigation(){},
  stopExperimentAI(){},esc:String,
  window:{scrollTo(){}},
  document:{body:{classList:{toggle(){}}},addEventListener(){},
   querySelectorAll(){return []},getElementById(){return null}},
  fetch:url=>new Promise((resolve,reject)=>pending.set(url,{resolve,reject})),
 };
 vm.createContext(sandbox);
 vm.runInContext(fs.readFileSync(path.join(root,'wiki.js'),'utf8'),sandbox);
 // Exercise the production route with only DOM rendering replaced.
 const app=fs.readFileSync(path.join(root,'app.js'),'utf8');
 const start=app.indexOf('async function route()');
 const end=app.indexOf("\nPromise.all([",start);
 assert(start>=0&&end>start,'Locate the complete production router');
 vm.runInContext(app.slice(start,end),sandbox);
 vm.runInContext('wikiPage=id=>db.articles.find(a=>a.id===id).html',sandbox);
 const older=vm.runInContext('route()',sandbox);
 sandbox.location.hash='#/wiki/newer';
 const newer=vm.runInContext('route()',sandbox);
 pending.get('articles/newer.html').resolve({ok:true,text:async()=> 'Newer guide'});
 await newer;
 assert.equal(main.innerHTML,'Newer guide');
 if(oldRequestFails)pending.get('articles/older.html').reject(new Error('Old request failed'));
 else pending.get('articles/older.html').resolve({ok:true,text:async()=> 'Older guide'});
 await older;
 assert.equal(main.innerHTML,'Newer guide','Late success or error must not replace the current page');
 assert.equal(sandbox.document.title,'Newer guide — Liberpedia');
 let downloadQuery;
 sandbox.downloadsPage=async query=>{downloadQuery=query;main.innerHTML='Downloads'};
 for(const query of ['shift candidates','dots/punctuation','100%']){
  sandbox.location.hash='#/downloads/'+encodeURIComponent(query);
  await vm.runInContext('route()',sandbox);
  assert.equal(downloadQuery,query,'Download route must decode the URL search phrase');
 }

}
async function main(){
 let finish,calls=0;
 const sandbox={db:{articles:[{id:'example',source:'readings/example.html'}]},
  document:{addEventListener(){}},fetch:async url=>{
   calls++;assert.equal(url,'articles/readings/example.html');
   return new Promise(resolve=>{finish=resolve});
  }};
 vm.createContext(sandbox);
 vm.runInContext(fs.readFileSync(path.join(root,'wiki.js'),'utf8'),sandbox);
 const first=vm.runInContext("ensureWikiArticle('example')",sandbox);
 const second=vm.runInContext("ensureWikiArticle('example')",sandbox);
 assert.equal(calls,1);
 finish({ok:false});
 await Promise.all([assert.rejects(first,/could not be loaded/),assert.rejects(second,/could not be loaded/)]);
 assert.equal(sandbox.db.articles[0].html,undefined);
 const retry=vm.runInContext("ensureWikiArticle('example')",sandbox);
 assert.equal(calls,2);
 finish({ok:true,text:async()=>'<h2>Example</h2>'});
 await retry;
 await vm.runInContext("ensureWikiArticle('example')",sandbox);
 assert.equal(calls,2);
 assert.equal(sandbox.db.articles[0].html,'<h2>Example</h2>');
 await assert.rejects(vm.runInContext("ensureWikiArticle('missing')",sandbox),/does not exist/);
 await vm.runInContext("ensureWikiArticle('')",sandbox);
 assert.equal(calls,2);
 await checkNavigationRace(false);
 await checkNavigationRace(true);
 console.log('PASS: search parity, all source bodies, shared requests, retry, caching, and unknown guides.');
 console.log('PASS: production router ignores older guide responses and failures after navigation.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
