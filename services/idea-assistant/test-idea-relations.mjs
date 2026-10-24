import assert from 'node:assert/strict';
import C from '../../claim-specification.js';
import S from '../../claim-share.js';
import {compareCards,validateCard} from './idea-relations.mjs';

const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
const make=(extra={})=>S.cardData(C.confirm(C.createDraft({source:{text:'Separate original wording'},aim:known({outcomeId:'decipher',detail:'Recover only this opening'}),method:known({operations:[{id:'vigenere',key:'FOO',reset:'page'},{id:'atbash'}]}),scope:known({pages:['lp2-15','lp2-17']}),rules:{reset:known('page')},...extra}),{id:'fixture',at:'2026-10-24T00:00:00Z'}));
const clone=x=>JSON.parse(JSON.stringify(x));
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name);}

test('exact active card identity ignores member order and wrapper form but retains all explicit states',()=>{
 const card=make(),json=C.serialize(card),a=compareCards(json,{card:clone(card),id:'internal-export-row'});
 assert.equal(a.relationship,'exact_same');assert.deepEqual(a.differences,[]);assert.equal(a.novelty,'not_assessed');assert.equal(a.coverage,'not_assessed');
 assert.deepEqual(a.changed,{outcome:false,method:false,methodOrder:false,rules:[],scope:false,unresolved:false});
 assert.deepEqual(validateCard(card),JSON.parse(json));assert.equal(JSON.stringify(card),JSON.stringify(make()),'No mutation');
});
test('page-only changes retain exact holes and directional additions/removals without coverage claims',()=>{
 const a=make(),b=make({scope:known({pages:['lp2-15','lp2-16','lp2-18']})});
 const result=compareCards(a,b);assert.equal(result.relationship,'page_scope_variant');assert.deepEqual(result.pageDelta,{added:['lp2-16','lp2-18'],removed:['lp2-17']});assert.equal(result.changed.scope,true);
 assert(result.differences.every(d=>d.path.startsWith('/scope/')));assert.equal(result.coverage,'not_assessed');
 assert.deepEqual(compareCards(b,a).pageDelta,{added:['lp2-17'],removed:['lp2-16','lp2-18']});
 const metadata=compareCards(make({scope:known({pages:['lp2-15'],inputVersion:'fixed-v1'})}),make({scope:known({pages:['lp2-17'],inputVersion:'fixed-v1'})}));assert.equal(metadata.relationship,'page_scope_variant');
});
test('passage descriptions, positions, unknown qualifiers and changed metadata prevent page-only inference',()=>{
 for(const field of [{description:'lines 2–3'},{positions:[2,3]},{region:{x:0,y:30}},{customQualifier:'line six'}]){
  const result=compareCards(make({scope:known({pages:['lp2-15'],...field})}),make({scope:known({pages:['lp2-17'],...field})}));
  assert.equal(result.relationship,'different_specification');assert(!result.pageDelta);
 }
 const result=compareCards(make({scope:known({pages:['lp2-15'],inputVersion:'v1'})}),make({scope:known({pages:['lp2-17'],inputVersion:'v2'})}));assert.equal(result.relationship,'different_specification');
});
test('added/removed key and parameter changes are explicit differences, never automatic novelty',()=>{
 const a=make(),b=clone(a);delete b.method.value.operations[0].key;
 const removed=compareCards(a,b);assert.equal(removed.relationship,'different_specification');assert.equal(removed.changed.method,true);
 const difference=removed.differences.find(d=>d.path==='/method/value/operations/0/key');assert.deepEqual(difference,{path:'/method/value/operations/0/key',kind:'removed',leftPresent:true,rightPresent:false,left:'FOO'});
 const added=compareCards(b,a).differences.find(d=>d.path.endsWith('/key'));assert.equal(added.kind,'added');assert.equal(added.right,'FOO');
 b.method.value.operations[0].key='BAR';assert(compareCards(a,b).differences.some(d=>d.path.endsWith('/key')&&d.left==='FOO'&&d.right==='BAR'));
});
test('ordered compound changes are enumerated; same category or operation multiset is not equivalence',()=>{
 const a=make(),b=clone(a);b.method.value.operations.reverse();const r=compareCards(a,b);
 assert.equal(r.relationship,'different_specification');assert.equal(r.changed.methodOrder,true);assert(r.differences.some(d=>d.path==='/method/value/operations/0/id'));
 const changed=clone(b);changed.method.value.operations[1].key='BAR';assert.equal(compareCards(a,changed).changed.methodOrder,false,'Flag only exact reorder, not guessed similarity');
});
test('unknown, unrestricted, not-applicable and specified values never act as wildcards',()=>{
 const a=make(),b=clone(a);b.rules.searchBounds={status:'unrestricted'};
 const r=compareCards(a,b);assert.equal(r.relationship,'different_specification');assert.deepEqual(r.changed.rules,['searchBounds']);assert(r.differences.some(d=>d.path==='/rules/searchBounds/status'&&d.left==='unspecified'&&d.right==='unrestricted'));
 for(const scope of [C.field(),C.field('unrestricted'),C.field('not_applicable')]){
  const other=make({scope});assert.equal(compareCards(a,other).relationship,'different_specification');assert(!compareCards(a,other).pageDelta);
 }
 const empty=compareCards(a,make({scope:known({pages:[]})}));assert.equal(empty.relationship,'page_scope_variant');assert.deepEqual(empty.pageDelta,{added:[],removed:['lp2-15','lp2-17']});
});
test('canonical outcome aliases retain exact detail/success criteria and cannot infer scope or equivalence',()=>{
 const a=make({aim:known('solve LP2')}),b=make({aim:known('find readable text')});
 assert.equal(a.outcome.value.outcomeId,b.outcome.value.outcomeId);const r=compareCards(a,b);assert.equal(r.relationship,'different_specification');assert.equal(r.changed.outcome,true);assert(r.differences.some(d=>d.path==='/outcome/value/detail'));
 const explicit=make({aim:known({outcomeId:'decipher',wording:'Different source phrase',detail:'Recover only this opening'})});assert.equal(compareCards(make(),explicit).relationship,'exact_same');
 const unknown=make({aim:C.field()});assert.equal(compareCards(a,unknown).relationship,'different_specification');
});
test('active unresolved constraints are compared, including escaped property paths',()=>{
 const a=make(),b=make({unresolved:[{kind:'custom',text:'Need a finite reset rule'}]});assert.equal(compareCards(a,b).changed.unresolved,true);assert.equal(compareCards(a,b).relationship,'different_specification');
 const c=clone(a);c.method.value.operations[0]['a/b~c']=4;assert(compareCards(a,c).differences.some(d=>d.path==='/method/value/operations/0/a~1b~0c'&&d.kind==='added'));
});
test('bounded validation rejects malformed fields, unsafe/deep/oversized input and accessors without executing them',()=>{
 assert.throws(()=>validateCard('not JSON'));assert.throws(()=>validateCard('x'.repeat(12001)));assert.throws(()=>validateCard({...make(),source:'raw'}));
 const invalid=make();invalid.scope.value.pages=['lp2-99'];assert.throws(()=>validateCard(invalid));
 const key=JSON.parse('{"__proto__":{}}');assert.throws(()=>validateCard(key),/Unsafe/);
 let value={};for(let i=0;i<18;i++)value={nested:value};assert.throws(()=>validateCard(value),/structural/);
 const cycle={};cycle.next=cycle;assert.throws(()=>validateCard(cycle),/structural/);
 let read=false;const accessor={};Object.defineProperty(accessor,'card',{enumerable:true,get(){read=true;return make();}});assert.throws(()=>validateCard(accessor),/data/);assert.equal(read,false);
 const huge=make();huge.scope.value.description='x'.repeat(12000);assert.throws(()=>validateCard(huge),/size/);
});
console.log('PASS '+count+' pure idea-relation groups; no network, coverage lookup, UI, semantic novelty decision or mutation.');
