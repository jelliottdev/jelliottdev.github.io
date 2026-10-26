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
 await test('word prime sum sections explain assignments and word breaks without changing card identity',()=>{
  for(const table of ['canonical','reversed'])for(const boundaries of ['non-rune','hyphen-period']){
   const criterion={kind:'word-prime-sums',table,boundaries},spec=make({method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table,boundaries,declaredFamilyId:'prime-indices'}]}),rules:{evaluation:known(criterion)}}),payload=S.cardData(spec),before=JSON.stringify(payload),fragment=S.encode(spec),rows=S.sections(payload),step=rows.find(row=>row[0]==='Step 1'),evaluation=rows.find(row=>row[0]==='Evaluation');
   assert.equal(step[1],'Word prime sums');assert(step[2].includes(table==='reversed'?'F=109, U=107, …, EA=2':'F=2, U=3, …, EA=109'));assert(step[2].includes(boundaries==='non-rune'?'Every non-rune character separates words':"Only ASCII '-' and '.' separate groups"));assert(evaluation[1].includes('Add the '+(table==='reversed'?'reversed':'usual')+' prime values'));assert(!evaluation[1].includes('{'));assert(!step[2].includes('non-rune\n'));assert.equal(JSON.stringify(payload),before);assert.equal(S.encode(spec),fragment);assert.equal(fragment,token(payload),'Display wording cannot alter serialized link bytes');assert.equal(spec.source.text,'PRIVATE ORIGINAL PROMPT');assert.deepEqual(S.cardData(C.confirm(S.decode(fragment).draft,{id:'recipient',at:'2026-10-24T12:00:00Z'})),payload);
  }
  const spec=make({method:known({operations:[{id:'word_prime_sums',label:'Original exact wording',table:'reversed',boundaries:'non-rune',extra:'Keep this parameter visible'}]}),rules:{evaluation:known({kind:'word-prime-sums',table:'reversed',boundaries:'non-rune',extra:'Do not hide this'})}}),rows=S.sections(S.cardData(spec));assert.equal(rows.find(r=>r[0]==='Step 1')[1],'Original exact wording');assert(rows.find(r=>r[0]==='Step 1')[2].includes('Extra: Keep this parameter visible'));assert(rows.find(r=>r[0]==='Evaluation')[1].includes('Do not hide this'),'Malformed or extended criteria keep every field visible');assert.equal(S.wordPrimeSumLabels('custom','non-rune'),null);assert.equal(S.wordPrimeSumLabels('reversed','custom'),null);
  const other=make({rules:{evaluation:known({kind:'exact-prefix',values:[1,2]})}});assert.equal(S.sections(S.cardData(other)).find(r=>r[0]==='Evaluation')[1],JSON.stringify({kind:'exact-prefix',values:[1,2]}),'Other evaluation kinds remain unchanged');
  const numeric=make({method:known({operations:[{id:'word_prime_sums',label:'Word prime sums',table:'reversed',boundaries:'non-rune'}]}),rules:{evaluation:known({kind:'word-prime-sums',table:'reversed',boundaries:'non-rune'}),inputVersion:known('raw'),representation:known('GP29'),unmapped:known('preserve'),wordBoundaries:known('preserve')}}),payload=S.cardData(numeric),serialized=JSON.stringify(payload),encoded=S.encode(numeric),plain=new Map(S.sections(payload).map(row=>[row[0],row[1]]));
  for(const [key,label]of [['Input version','Archived rune text'],['Representation','29-rune GP alphabet'],['Unmapped values','Keep original separators'],['Word boundaries','Keep original word marks']])assert.equal(plain.get(key),label);
  assert.equal(S.wordPrimeSumRuleLabel(numeric,'inputVersion','raw'),'Archived rune text','Draft/shared views can reuse the same guarded wording');assert.equal(JSON.stringify(payload),serialized);assert.equal(S.encode(numeric),encoded);
  const unusual=structuredClone(payload);unusual.rules.inputVersion.value='another edition';unusual.rules.representation.value={custom:'explicit encoding'};const unusualRows=new Map(S.sections(unusual).map(row=>[row[0],row[1]]));assert.equal(unusualRows.get('Input version'),'another edition');assert.equal(unusualRows.get('Representation'),JSON.stringify({custom:'explicit encoding'}));
  const mismatch=structuredClone(payload);mismatch.rules.evaluation.value.table='canonical';assert.equal(new Map(S.sections(mismatch).map(row=>[row[0],row[1]])).get('Input version'),'raw','Conflicting numeric specifications do not receive the recognized-card display shortcuts');
  const generic=make({rules:{inputVersion:known('raw'),representation:known('GP29')}}),genericRows=new Map(S.sections(S.cardData(generic)).map(row=>[row[0],row[1]]));assert.equal(genericRows.get('Input version'),'raw');assert.equal(genericRows.get('Representation'),'GP29','Other methods retain their existing display');
 });
 await test('maintained affine cards share readable parameters and checks without changing exact input',()=>{
  const record=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/word-internal-affine-lags/record.json'),'utf8')),card=record.browser_followups[0].card,before=JSON.stringify(card),rows=S.sections(card),plain=new Map(rows.map(row=>[row[0],row[1]])),step=rows.find(row=>row[0]==='Step 1');
  assert.equal(step[1],'Within-word affine pair count');assert.match(step[2],/Rune distance: 6 rune positions/);assert.match(step[2],/Multiplier: 27/);assert.match(step[2],/Offset: 24/);assert.match(step[2],/Word breaks: Every non-rune character separates words/);assert(!step[2].includes('Boundaries: non-rune'));
  assert.match(plain.get('Evaluation'),/Count pairs 6 rune positions apart inside each word/);assert.match(plain.get('Evaluation'),/y = 27x \+ 24 \(mod 29\)/);assert.match(plain.get('Evaluation'),/average after rearranging the same runes/);assert(!plain.get('Evaluation').includes('{'));assert.equal(plain.get('Representation'),'29-rune GP alphabet');assert.equal(plain.get('Input version'),'Archived rune text');
  assert.deepEqual(S.operationParameters(card.method.value.operations[0]).map(row=>row.label),['Rune distance','Multiplier','Offset','Word breaks']);assert.equal(S.evaluationText(card.rules.evaluation.value),plain.get('Evaluation'));assert.equal(S.protocolRuleLabel(card,'inputVersion','raw'),'Archived rune text');assert.equal(JSON.stringify(card),before,'Plain display must preserve the authored criterion, aim, scope and pins');
  const other=structuredClone(card);other.rules.evaluation.value.boundaries='hyphen-period';other.method.value.operations[0].boundaries='hyphen-period';assert.match(S.sections(other).find(row=>row[0]==='Evaluation')[1],/Only ASCII '-' and '\.' separate groups; other non-rune characters are ignored/);assert.equal(JSON.stringify(card),before);
  for(const mutate of [x=>x.extra='Keep this exact field',x=>x.lag=13,x=>x.a=29,x=>x.boundaries='custom']){const criterion=structuredClone(card.rules.evaluation.value);mutate(criterion);assert.equal(S.evaluationText(criterion),null);const changed=structuredClone(card);changed.rules.evaluation.value=criterion;assert.equal(S.sections(changed).find(row=>row[0]==='Evaluation')[1],JSON.stringify(criterion));assert.equal(S.protocolRuleLabel(changed,'inputVersion','raw'),null);}
  const extended={...card.method.value.operations[0],custom:{preserve:'exact value'}};assert(S.operationParameters(extended).some(row=>row.label==='Custom'&&row.value==='{"preserve":"exact value"}'),'Unrecognized operation fields remain inspectable');
  const unknown={kind:'custom',settings:{a:1}};assert.equal(S.evaluationText(unknown),null);assert.equal(S.evaluationText({kind:'exact-prefix',values:[1,2]}),null);assert.equal(S.evaluationText({kind:'readability'}),C.evaluationText({kind:'readability'}));assert.deepEqual(S.operationParameters(null),[]);
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
  const versioned=S.link(make(),'https://example.test/investigate.html?v=complete-current-20261024&q=PRIVATE&pages=LP2-15#old');
  assert.equal(new URL(versioned).search,'?v=complete-current-20261024');
  assert(!versioned.includes('PRIVATE'));assert(!versioned.includes('pages='));
  assert.equal(new URL(versioned).hash,S.encode(make()));assert.deepEqual(S.decode(new URL(versioned).hash).draft.method.value.operations,S.cardData(make()).method.value.operations);
  assert.equal(new URL(S.link(make(),'https://example.test/investigate.html?v=PRIVATE')).search,'');
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
 await test('legacy unresolved and ambiguous cards remain structurally readable without confirmation or changed identity',()=>{
  const base=S.cardData(make()),legacy=structuredClone(base);legacy.unresolved=[{kind:'source_note',text:'Keep every F rune unchanged.'}];const fragment=token(legacy),before=C.serialize(legacy),read=S.readCard(fragment);assert.equal(C.serialize(read),before);assert.equal(C.serialize(S.readCard(token(read))),before);assert.equal(read.unresolved[0].text,legacy.unresolved[0].text);assert(!Object.hasOwn(read,'confirmation'));assert(!Object.hasOwn(read,'execution'));const draft=S.decode(fragment).draft;assert.equal(C.completeness(draft).researchReady,false);assert.throws(()=>C.confirm(draft,{id:'cannot-confirm-read',at:'2026-10-26T00:00:00.000Z'}),/Resolve consequential/);assert.equal(C.serialize(legacy),before);
  const ambiguous=structuredClone(base);ambiguous.method.value.operations=[{id:'reverse_row_runes'}];ambiguous.rules.wordBoundaries={status:'specified',value:'preserve'};ambiguous.rules.boundaryMode={status:'unspecified'};const reading=S.readCard(token(ambiguous));assert.equal(C.serialize(reading),C.serialize(ambiguous));assert.throws(()=>C.confirm(S.decode(token(ambiguous)).draft,{id:'still-ambiguous',at:'2026-10-26T00:00:00.000Z'}));
  const context=vm.createContext({TextEncoder,TextDecoder,btoa,atob,URL});vm.runInContext(fs.readFileSync(require.resolve('../claim-specification.js'),'utf8'),context);vm.runInContext(fs.readFileSync(require.resolve('../claim-share.js'),'utf8'),context);assert.equal(C.serialize(context.ClaimShare.readCard(fragment)),before);let calls=0;const forged={};Object.defineProperty(forged,'toString',{get(){calls++;return()=>fragment;}});assert.throws(()=>S.readCard(forged));assert.equal(calls,0);assert.throws(()=>S.readCard('#idea='+('A'.repeat(17000))));assert.throws(()=>S.readCard(token({...legacy,source:'not active-card data'})));
 });
 console.log('PASS '+count+' claim-share groups; canvas/native/clipboard are mocked, no real share, send, hosted calls or storage.');
})().catch(e=>{console.error(e);process.exitCode=1;});
