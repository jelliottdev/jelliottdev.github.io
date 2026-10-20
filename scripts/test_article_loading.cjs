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
 console.log('PASS: search parity, all source bodies, shared requests, retry, caching, and unknown guides.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
