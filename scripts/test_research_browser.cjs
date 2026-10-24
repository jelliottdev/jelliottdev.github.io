'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),load=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const Browser=require('../research-browser-model.js'),Index=require('../research-index.js');
const source=load('data/research-map.json'),registry=load('data/experiments.json'),before=JSON.stringify(source);
const data=Browser.build(source,registry),published=registry.records.filter(r=>r.status==='published');
assert.equal(JSON.stringify(source),before,'Navigation building cannot rewrite source classification');
const nodes=new Map(data.views.all.nodes.map(n=>[n.id,n]));
const leaves=data.views.all.nodes.filter(n=>n.record_id);
assert.equal(leaves.length,published.length);assert.equal(new Set(leaves.map(n=>n.record_id)).size,published.length);
assert.deepEqual(new Set(nodes.get('all-research').members),new Set(published.map(r=>r.id)));
for(const record of published){
  assert.deepEqual(data.records[record.id].scope,record.scope);
  assert.equal(data.records[record.id].finding,record.finding);
  assert.equal(data.records[record.id].limitations,record.limitations);
  assert.deepEqual(data.records[record.id].method_topics,record.method_topics);
  const target=new URL(data.records[record.id].href,'https://example.org/');
  assert.equal(target.pathname,'/library.html');assert.deepEqual([...target.searchParams.keys()],['v']);assert(target.searchParams.get('v'));
  assert.equal(target.hash,'#/experiment/'+encodeURIComponent(record.id));
}
for(const view of Object.values(source.views))for(const node of view.nodes){
  if(!nodes.has(node.id)||!nodes.has(node.parent))continue;
  assert.equal(nodes.get(node.id).parent,node.parent,'Keep every original relation below the editorial area roots');
}
const selected=Index.select(Object.values(data.records),Index.state(new URLSearchParams()));
assert.equal(selected.allRecords.length,published.length);assert.equal(selected.records.length,20);
const exact=Index.select(Object.values(data.records),Index.state(new URLSearchParams('q=LP2-15&sort=recent')));
assert(exact.allRecords.length>0);assert(exact.allRecords.every(r=>r.scope.pages.includes('lp2-15')));
const added=structuredClone(registry),fresh=structuredClone(published[0]);fresh.id='future-record';fresh.title='A new record';added.records.push(fresh);
const future=Browser.build(source,added),unplaced=future.views.all.nodes.find(n=>n.id==='aim:unplaced');
assert(unplaced.members.includes(fresh.id),'New records stay accessible without inventing method classification');
assert.deepEqual(Browser.read('#/research?q=autokey&page=4&type=method','graph',Index.state),{view:'all',branch:'',record:'',page:'',colour:'methods',result:'',mode:'list',q:'autokey',type:'method',method:'',family:'',sort:'title',p:4});
assert.equal(Browser.read('#mode=graph','list',Index.state).mode,'graph');
assert.equal(Browser.read('','list',Index.state).mode,'list');
assert.equal(Browser.read('#page=lp2-15&mode=list','graph',Index.state).page,'lp2-15');
const html=fs.readFileSync(path.join(root,'research.html'),'utf8');
assert.equal((html.match(/src="research-index\.js/g)||[]).length,1);
assert(!/map-index-model|map-search-engine|map-study-data|\/archive\//.test(html));
console.log(`PASS unified research: ${published.length} current records, exact findings/scopes, every leaf once, preserved source parents, new-record access, shared selector/search and legacy state.`);

assert.equal(Browser.read('#result=%22%3E%3Cimg%20onerror%3Dalert(1)%3E','graph',Index.state).result,'');
assert.equal(Browser.read('#result=bogus&outcome=supported','graph',Index.state).result,'supported');
assert.equal(Browser.read('#record=__proto__','graph',Index.state).record,'');
