'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const C=require('../claim-specification.js'),S=require('../claim-share.js');
const known=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']});
const make=(extra={})=>C.confirm(C.createDraft({source:{text:'PRIVATE ORIGINAL PROMPT',materials:[{name:'private.png'}]},
 aim:known({outcomeId:'decipher',wording:'Original goal wording',detail:'Read just the selected opening; this is not a whole-page solve'}),
 method:known({operations:[{id:'vigenere',label:'Vigenere with key FOO',key:'FOO',reset:'page',sourceText:'PRIVATE SOURCE WORDING',provenance:{kind:'supplied',refs:['private']}},{id:'atbash',offset:3}],editHistory:[{text:'PRIVATE HISTORY'}]}),
 scope:known({pages:['lp2-17','lp2-15'],description:'Only lines 2–3'}),rules:{wordBoundaries:known('preserve'),reset:known({per:'page',offset:3})},methodEdits:[{previousOperation:{key:'PRIVATE OLD KEY'}}],...extra}),{id:'private-confirmation',at:'2026-10-24T12:00:00Z'});
const token=p=>'#idea='+Buffer.from(JSON.stringify(p)).toString('base64url');
let count=0;
async function test(name,fn){await fn();count++;console.log('PASS '+name);}
function canvasDocument(){const texts=[],rectangles=[];return {texts,rectangles,createElement(tag){assert.equal(tag,'canvas');const ctx={font:'',measureText:t=>({width:[...t].length*18}),fillText:(t,x,y)=>texts.push({text:t,x,y}),fillRect:(...r)=>rectangles.push(r)};return {width:0,height:0,getContext:()=>ctx,toBlob(cb,type){cb(new Blob(['mock PNG'],{type}));}};}};}
(async()=>{
 await test('UMD exposes the same bounded API without network or storage',()=>{
  const context={ClaimSpecification:C,TextEncoder,TextDecoder,btoa,atob,URL};vm.runInNewContext(fs.readFileSync(require.resolve('../claim-share.js'),'utf8'),context);
  assert.equal(context.ClaimShare.VERSION,1);assert.equal(typeof context.ClaimShare.decode,'function');
 });
 await test('only active standardized fields round-trip as an unconfirmed unexecuted shared draft',()=>{
  const spec=make(),p=S.cardData(spec),text=JSON.stringify(p);
  for(const marker of ['PRIVATE ORIGINAL','PRIVATE SOURCE','PRIVATE HISTORY','PRIVATE OLD KEY','private.png','private-confirmation','provenance','sourceText'])assert(!text.includes(marker),marker);
  const imported=S.decode(S.encode(spec));assert.equal(imported.version,1);assert.deepEqual(imported.acknowledged,{aim:true,scope:true});
  const d=imported.draft;assert.equal(d.status,'draft');assert.equal(d.execution,'not_run');assert.equal(d.confirmation,null);assert.equal(d.source.origin,'shared_link');
  assert(!d.source.text.includes('PRIVATE'));assert.deepEqual(d.source.materials,[]);assert.deepEqual(d.method.value.operations,p.method.value.operations);
  assert.deepEqual(d.scope.value,{pages:['lp2-15','lp2-17'],description:'Only lines 2–3'});assert.equal(d.aim.outcome.id,'decipher');assert.equal(d.aim.outcome.detail,p.outcome.value.detail);
  for(const k of C.RULES){assert.equal(d.rules[k].status,spec.rules[k].status);if(spec.rules[k].status==='specified')assert.deepEqual(d.rules[k].value,spec.rules[k].value);}
  assert.equal(d.method.provenance.kind,'project_context');assert.deepEqual(d.methodEdits,[]);
  assert.throws(()=>S.encode(d),/confirmed/); // Recipient must review; import is never approval.
 });
 await test('unknown is acknowledged as unknown; holes, opaque wording and active constraints remain',()=>{
  const d=S.decode(S.encode(make({aim:C.field(),scope:C.field(),method:known({operations:[{id:'described_method',sourceText:'Keep this exact custom operation'}]}),unresolved:[{kind:'custom',text:'Only test the specified opening',provenance:{kind:'supplied',refs:['source:text']}}]})));
  assert.equal(d.draft.aim.status,'unspecified');assert.equal(d.draft.scope.status,'unspecified');assert.deepEqual(d.acknowledged,{aim:true,scope:true});
  assert.equal(d.draft.method.value.operations[0].label,'Keep this exact custom operation');assert.equal(d.draft.unresolved[0].text,'Only test the specified opening');assert(!JSON.stringify(d.draft.unresolved).includes('provenance'));
 });
 await test('version, schema, state, rule, operation, page, UTF-8 and resource limits reject malformed links',()=>{
  const original=S.cardData(make());
  for(const alter of [p=>p.version=2,p=>p.source={text:'injected'},p=>p.outcome.value.outcomeId='new',p=>p.rules.extra={status:'unspecified'},p=>delete p.rules.reset,p=>p.scope.value.pages=['lp2-99'],p=>p.method.value.operations[0].sourceText='raw',p=>p.scope.status='unknown',p=>p.outcome.value.extra='x',p=>p.unresolved='x']){
   const p=JSON.parse(JSON.stringify(original));alter(p);assert.throws(()=>S.decode(token(p)));
  }
  assert.throws(()=>S.decode('#idea=_w'));assert.throws(()=>S.decode('#idea=AA='));assert.throws(()=>S.decode('#idea=A'));assert.throws(()=>S.decode('#idea='+'a'.repeat(17000)));
  assert.throws(()=>S.decode('#idea='+Buffer.from('{"__proto__":{}}').toString('base64url')),/Unsafe/);
  assert.throws(()=>S.encode(make({scope:known({description:'x'.repeat(13000)})})),/12,000/);
  let nested={};for(let i=0;i<18;i++)nested={nested};assert.throws(()=>S.encode(make({scope:known(nested)})),/deeply/);
 });
 await test('link removes old query/source hints and uses a bounded same-page fragment only',()=>{
  const url=S.link(make(),'https://example.test/investigate.html?q=PRIVATE#old');assert(url.startsWith('https://example.test/investigate.html#idea='));assert(!url.includes('PRIVATE'));assert(url.length<=16000);
  assert.throws(()=>S.link(make(),'javascript:alert(1)'));
 });
 await test('canvas has measured complete wrapping and refuses clipping or failed PNG output',async()=>{
  const doc=canvasDocument(),blob=await S.renderPNG(make(),{document:doc});assert.equal(blob.type,'image/png');
  assert(doc.texts.some(t=>t.text.includes('Vigenere')));assert(doc.texts.some(t=>t.text.includes('FOO')));assert(doc.texts.some(t=>t.text.includes('Not specified')));
  assert(doc.texts.some(t=>t.text==='LP2-15, LP2-17'));assert(doc.texts.some(t=>t.text==='Only lines 2–3'));assert(doc.texts.some(t=>t.text==='Word boundaries'));assert(doc.texts.some(t=>t.text.startsWith('Liberpedia')));
  assert(!doc.texts.some(t=>t.text==='wordBoundaries'||t.text==='{}'||t.text.includes('"pages":')));
  const height=doc.rectangles[0][3];assert(doc.texts.every(t=>t.y<height));
  await assert.rejects(S.renderPNG(make(),{document:canvasDocument(),maxHeight:200}),/too long/);
  await assert.rejects(S.renderPNG(make(),{document:{createElement:()=>({getContext:()=>null})}}),/unavailable/);
 });
 await test('native file sharing includes the same link and PNG; supported text fallback stays native',async()=>{
  const calls=[],FileType=class{constructor(parts,name,options){this.parts=parts;this.name=name;this.type=options.type;}};
  const spec=make(),preparedPNG=await S.prepare(spec,{document:canvasDocument()});
  const result=await S.share(spec,'https://example.test/investigate.html',{preparedPNG,document:canvasDocument(),File:FileType,navigator:{canShare:()=>true,share:async data=>calls.push(data)}});
  assert.equal(result.status,'shared');assert.equal(calls[0].files[0].type,'image/png');assert.equal(calls[0].url,result.url);assert.equal(S.decode(new URL(result.url).hash).draft.scope.value.pages.length,2);
  const text=[];await S.share(make(),'https://example.test/investigate.html',{document:canvasDocument(),navigator:{canShare:()=>false,share:async data=>text.push(data)}});assert(!text[0].files);assert(text[0].url);
  let synchronous=false;const pending=S.share(spec,'https://example.test/investigate.html',{document:{createElement:()=>assert.fail('No canvas during native click')},navigator:{share:()=>{synchronous=true;return Promise.resolve();}}});
  assert.equal(synchronous,true,'Native share must start before any await');await pending;
  const mismatched=[];await S.share(make({scope:known({pages:['lp2-43']})}),'https://example.test/investigate.html',{preparedPNG,File:FileType,navigator:{canShare:()=>true,share:async d=>mismatched.push(d)}});assert(!mismatched[0].files,'Stale prepared card must never accompany a new link');
 });
 await test('native cancel is quiet; absent/failed APIs expose usable link and PNG without sending',async()=>{
  let copied;const cancel=await S.share(make(),'https://example.test/investigate.html',{document:canvasDocument(),navigator:{share:async()=>{const e=Error('cancel');e.name='AbortError';throw e;},clipboard:{writeText:async()=>assert.fail('No copy on cancel')}}});assert.equal(cancel.status,'cancelled');assert(!cancel.error);
  const result=await S.share(make(),'https://example.test/investigate.html',{document:canvasDocument(),navigator:{clipboard:{writeText:async value=>{copied=value;}}}});assert.equal(result.status,'copied');assert.equal(result.url,copied);assert(result.png instanceof Blob);
  const failed=await S.share(make(),'https://example.test/investigate.html',{document:canvasDocument(),navigator:{clipboard:{writeText:async()=>{throw Error('Permission denied');}}}});assert.equal(failed.status,'fallback');assert(failed.url);assert.equal(failed.error,'Permission denied');assert(failed.png);
  const nativeFailed=await S.share(make(),'https://example.test/investigate.html',{document:canvasDocument(),navigator:{share:async()=>{throw Error('No targets');}}});assert.equal(nativeFailed.status,'fallback');assert.equal(nativeFailed.error,'No targets');
 });
 console.log('PASS '+count+' claim-share groups; canvas/native/clipboard are mocked, no real share, send, hosted calls or storage.');
})().catch(e=>{console.error(e);process.exitCode=1;});
