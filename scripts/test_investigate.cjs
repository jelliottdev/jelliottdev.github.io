'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('../claim-specification'),I=require('../investigate'),S=require('../assistant-search');
const registry=JSON.parse(fs.readFileSync(require.resolve('../data/experiments.json'),'utf8'));
const docs=S.experimentDocs(registry.records),at='2026-10-24T12:00:00Z';
let count=0;
const test=(name,fn)=>{fn();count++;console.log('PASS '+name);};
test('exact scope lists/ranges preserve holes; invalid shorthand is rejected',()=>{
 assert.deepEqual(I.parseScope('LP2-15, LP2-17').value.pages,['lp2-15','lp2-17']);
 assert.deepEqual(I.parseScope('LP2-15–17').value.pages,['lp2-15','lp2-16','lp2-17']);
 assert.throws(()=>I.parseScope('15–17'));assert.throws(()=>I.parseScope('LP2-99'));
 assert.equal(I.parseScope('').status,'unspecified');
});
test('deciphering intake explicitly chooses evaluation without changing aim, method, scope or source',()=>{
 const H=require('../claim-share.js'),known=value=>C.field('specified',value,{kind:'supplied',refs:['fixture']}),source='Try this transformation to recover the hidden text.',base=C.createDraft({source:{text:source},aim:known({outcomeId:'decipher',wording:'Find readable text',detail:'Recover a complete passage'}),method:known({operations:[{id:'reverse_row_runes'}]}),scope:known({pages:['lp2-15']})});
 const question=I.intakeQuestions(base).find(q=>q.id==='evaluation');assert.equal(question.prompt,'What should this check look for?');assert.deepEqual(question.choices.map(c=>c.id),['research-first','language-samples','readable-text','warning-opening','inspect-output']);assert(question.choices.find(c=>c.id==='readable-text').label.includes('not available yet'));assert(question.choices.find(c=>c.id==='warning-opening').example.includes('first 12 runes'));
 for(const choice of C.EVALUATION_CHOICES){const next=I.answerIntake(base,'evaluation',choice.id);assert.deepEqual(next.rules.evaluation.value,choice.value);assert.deepEqual(next.aim,base.aim);assert.deepEqual(next.method,base.method);assert.deepEqual(next.scope,base.scope);assert.equal(next.source.text,source);assert(!I.intakeQuestions(next).some(q=>q.id==='evaluation'));assert.throws(()=>I.answerIntake(next,'evaluation',choice.id));const shared=H.cardData(C.confirm(next,{id:'evaluation-'+choice.id,at}));assert.deepEqual(shared.rules.evaluation.value,choice.value);assert(H.sections(shared).find(row=>row[0]==='Evaluation')[1].includes(choice.label));assert(I.rowsHTML(next).includes(choice.label));}
 assert.deepEqual(C.EVALUATION_CHOICES.find(c=>c.id==='warning-opening').value.values,[24,7,24,4,9,21,17,18,20,10,18,1]);
 const explicit={kind:'exact-prefix',values:[1,2,3]},supplied=C.revise(base,{rules:{evaluation:known(explicit)}});assert(!I.intakeQuestions(supplied).some(q=>q.id==='evaluation'));assert.deepEqual(supplied.rules.evaluation.value,explicit);
 for(const aim of [{outcomeId:'measure',detail:'Test the pattern'},{outcomeId:'unclassified',detail:'A custom research goal'},{outcomeId:'explain',detail:'Explain the drawing'}])assert(!I.intakeQuestions(C.revise(base,{aim:known(aim)})).some(q=>q.id==='evaluation'));
 for(const status of ['not_applicable','unrestricted']){const prior=C.field(status,undefined,{kind:'supplied',refs:['original:evaluation']}),unbounded=C.revise(base,{rules:{evaluation:prior}}),q=I.intakeQuestions(unbounded).find(q=>q.id==='evaluation');assert(q);assert.equal(q.context,'Choose a check if you have one in mind, or find related research first.');assert.deepEqual(unbounded.rules.evaluation,prior);const resolved=I.answerIntake(unbounded,'evaluation','warning-opening');assert.deepEqual(resolved.aim,base.aim);assert.deepEqual(resolved.clarifications.at(-1).previousRule,prior);assert.deepEqual(resolved.rules.evaluation.value,C.EVALUATION_CHOICES.find(c=>c.id==='warning-opening').value);assert(!I.intakeQuestions(resolved).some(q=>q.id==='evaluation'));}
 assert.throws(()=>I.answerIntake(base,'evaluation','automatic-plaintext-proof'));
});
test('arbitrary source is retained as editable method wording without an invented goal',()=>{
 const text='Try the odd columns, then my own key rule.';const d=I.initialDraft(text);
 assert.equal(d.source.text,text);assert.equal(d.method.value.operations[0].label,text);
 assert.equal(d.aim.status,'unspecified');assert.equal(d.rules.representation.status,'unspecified');
});
test('only known consequential reversal ambiguity is questioned',()=>{
 let d=I.initialDraft('Reverse the prime values of each row on LP2-15, keeping word boundaries.');
 assert.equal(C.questions(d)[0].id,'operation');
 d=C.clarify(d,'operation','reverse_row_runes');assert.equal(C.questions(d)[0].id,'word-boundary');
 d=C.clarify(d,'word-boundary','fixed_spaces');
 assert.equal(C.questions(d).length,0);assert(C.summary(d).includes('space positions'));
 assert(!C.summary(d).includes('prime values of each row'));
});
test('recognized reversal never drops an appended cipher, key, tail or explicit ordering',()=>{
 const text='Reverse digits of each prime value, then apply Vigenere with key FOO and reset at each page';
 const d=I.initialDraft(text),c=C.confirm(d,{id:'compound',at});
 assert.equal(d.method.value.operations.length,2);
 assert.equal(d.method.value.operations[0].id,'reverse_value_digits');
 assert.equal(d.method.value.operations[1].label,'apply Vigenere with key FOO and reset at each page');
 assert(C.summary(c).includes('prime value'));assert(C.summary(c).includes('key FOO'));assert(C.summary(c).includes('reset at each page'));
 assert(C.retrievalQuery(c).query.includes('key FOO'));assert(C.queryForResearch(c,{maxLength:6000}).query.includes('reset at each page'));
 const quoted=I.initialDraft('Reverse digits of each value, then use key "FOO then BAR", then Atbash');
 assert.equal(quoted.method.value.operations.length,2);
 assert.equal(quoted.method.value.operations[1].label,'use key "FOO then BAR", then Atbash');
 assert.equal(d.source.text,text);
});
test('ambiguous piece clarification preserves the cipher key and every later supplied step',()=>{
 let d=I.initialDraft('Reverse the prime values of each row on LP2-15, then apply Vigenere with key FOO; then rotate columns');
 const tail=C.serialize(d.method.value.operations[1]);
 assert.equal(C.questions(d)[0].id,'operation');
 d=C.clarify(d,'operation','reverse_value_digits');
 assert.equal(C.serialize(d.method.value.operations[1]),tail);
 assert.equal(d.method.value.operations[0].sourceText,'Reverse the prime values of each row on LP2-15');
 const c=C.confirm(d,{id:'clarified-compound',at});
 assert(C.summary(c).includes('key FOO'));assert(C.summary(c).includes('rotate columns'));
 assert(C.retrievalQuery(c).query.includes('key FOO'));
 assert.deepEqual(c.scope.value.pages,['lp2-15']);
});
test('negations, exceptions and uncertain attachments remain fully opaque instead of positive rules',()=>{
 for(const text of [
  'Do not reverse digits of each prime value on LP2-15',
  "Don't reverse each row; use Vigenere with key FOO instead",
  'Reverse each row except the heading on LP2-15',
  'Reverse digits of each prime value unless it is unmapped; keep the original rune',
  'If there is an F, then reverse each row',
  'Reverse the order within each row without preserving word boundaries',
  'Reverse each row, but never change key FOO',
  'Reverse digits of each prime value and apply Vigenere with key FOO',
  'Reverse each row after applying Vigenere with key FOO',
  'Do not preserve word boundaries; reverse each row on all pages excluding LP2-15'
 ]){
  const d=I.initialDraft(text),c=C.confirm(d,{id:'opaque',at});
  assert.equal(d.method.value.operations.length,1,text);
  assert.equal(d.method.value.operations[0].id,'described_method',text);
  assert.equal(d.method.value.operations[0].label,text);
  assert.equal(d.rules.wordBoundaries.status,'unspecified');
  assert.equal(C.questions(d).length,0);assert(C.summary(c).includes(text));
 }
 assert.equal(I.initialDraft('Reverse each row except LP2-15').scope.status,'unspecified');
});
test('answer validation binds ID, href AND complete exact source text',()=>{
 const source=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const answer={answer:'A bounded result [1].',sources:[source]};
 assert.equal(I.validateAnswer(answer,docs).sources[0],source);
 for(const changed of [{...source,text:source.text+'x'},{...source,href:'javascript:alert(1)'},{...source,id:'unknown'}])assert.throws(()=>I.validateAnswer({...answer,sources:[changed]},docs));
 assert.throws(()=>I.validateAnswer({...answer,answer:'Unsupported [2].'},docs));
 const second=docs.find(d=>d.id!==source.id);
 assert.equal(I.validateAnswer({answer:'Both studies [1, 2].',sources:[source,second]},docs).sources.length,2);
 assert.throws(()=>I.validateAnswer({...answer,answer:'Valid [1], invalid group [1, 99].'},docs));
 assert.throws(()=>I.validateAnswer({...answer,sources:[source,source]},docs));
});
test('related cards and findings share authored explanations without replacing evidence',()=>{
 const Reader=require('../record-test-view.js');
 const record=registry.records.find(r=>r.id==='wulfic-p21-running-key-layers'),doc=docs.find(d=>d.id===record.id);
 const before=JSON.stringify({record,doc});
 const preview=I.sourceHTML(doc,[record],{preview:true}),observed=I.observedFindingsHTML([doc],[record]);
 for(const html of [preview,observed]){assert(html.includes(Reader.title(record)));assert(html.includes(Reader.renderIntro(record)));assert(html.indexOf(Reader.renderIntro(record))<html.indexOf(record.reader_finding));}
 assert(observed.includes(record.reader_finding));assert.equal(JSON.stringify({record,doc}),before);
 const historic=I.observedFindingsHTML([doc],[{...record,reader_finding:'A different later result.'}]);assert(!historic.includes('A different later result.'));
});

test('source and answer HTML are escaped and native citations stay local',()=>{
 const s=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const c=C.confirm(I.initialDraft('<img src=x onerror=alert(1)>'),{id:'x',at});
 const r=C.bindResearch(c,{id:'r',at,evidence:{snapshotId:'x',records:[registry.records.find(r=>r.id===s.id)],documents:[s]},answer:'<script>unsafe</script> [1].'});
 const html=I.packetHTML(C.packetSnapshot(c,r));
 assert(!html.includes('<script>'));assert(html.includes('&lt;script&gt;'));assert(html.includes('href="index.html#/experiments/fibonacci-stream-skip-grid"'));
 assert(html.includes('&lt;img'));
});
test('source inspection shows actual method and bounds, compact page holes, and no invented coverage',()=>{
 const record=registry.records.find(r=>r.id==='fibonacci-stream-skip-grid'),doc=docs.find(d=>d.id===record.id),before=JSON.stringify(record);
 const encoded=value=>value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
 const html=I.sourceHTML(doc,[record]);
 assert(html.includes('LP2-00–49, LP2-51–55'));assert(!html.includes('LP2-00–55'));
 for(const field of ['procedure','representation','parameters','exclusions'])assert(html.includes(encoded(record.scope[field])));
 assert(!html.includes(record.reader_finding)); // Findings already precede these source details.
 assert(!html.includes(record.reader_limit));assert(!html.includes('<details'));assert(!html.includes('sha256'));
 const preview=I.sourceHTML(doc,[record],{preview:true});assert(preview.includes(record.reader_finding));assert(!preview.includes('source-facts'));
 const packet=I.sourceHTML(doc,[record],{packet:true});assert(!packet.includes(record.reader_finding));assert(packet.includes(encoded(record.reproduction.command)));
 assert.equal(JSON.stringify(record),before);
 if(record.materials){assert(html.includes(encoded(record.materials.reuse)));assert(html.includes(encoded(record.materials.limits)));}
 const unknown={...record,scope:{},reader_limit:'',limitations:'No independent transcription check. Human review pending.'};
 const unknownHTML=I.sourceHTML(doc,[unknown]);assert(unknownHTML.includes('Not specified in this record'));const observed=I.observedFindingsHTML([{...doc,text:JSON.stringify({finding:unknown.finding,limitations:unknown.limitations})}],[record]);assert(observed.includes('No independent transcription check.'));assert(!observed.includes('Human review pending'));
 assert(unknown.limitations.endsWith('Human review pending.'));
 const payload={...unknown,scope:{procedure:'<img src=x onerror=alert(1)>',parameters:'a < 7 & b > 3'}};
 const safe=I.sourceHTML(doc,[payload]);assert(!safe.includes('<img'));assert(safe.includes('a &lt; 7 &amp; b &gt; 3'));
 assert(I.sourceHTML({id:'context',title:'Page context',href:'#/pages/lp2-15'},[]).includes('not evidence that the idea was tested'));
});

test('authored findings and adjacent limits precede AI interpretation without repeating in source details or print',()=>{
 const escapedText=value=>value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
 const ids=['lp2-row-column-routes','lp2-row-column-english'],records=ids.map(id=>registry.records.find(r=>r.id===id)),sources=ids.map(id=>docs.find(d=>d.id===id));
 const context={id:'context',kind:'page',title:'LP2-15',href:'#/page/lp2-15',text:'Context only.'};
 const observed=I.observedFindingsHTML([...sources,context],records);
 assert(observed.startsWith('<h2>What the records found</h2>'));assert.equal((observed.match(/<section /g)||[]).length,2);assert(!observed.includes('<details'));
 records.forEach((record,index)=>{assert(observed.includes(escapedText(record.reader_finding||record.finding)));assert(observed.includes(escapedText(record.reader_limit||record.limitations)));assert(observed.includes('['+(index+1)+'] '+sources[index].title));});
 assert(!observed.includes('Context only'));assert.equal(I.observedFindingsHTML([context],records),'');
 const c=C.confirm(I.initialDraft('Reverse rows on LP2-15'),{id:'findings-first',at});
 const r=C.bindResearch(c,{id:'findings-first-result',at,evidence:{snapshotId:'x',records,documents:sources},answer:'These evaluations differ [1, 2].'});
 const printed=I.packetHTML(C.packetSnapshot(c,r));
 assert(printed.indexOf('What the records found')<printed.indexOf('How this relates to your idea'));
 assert(printed.indexOf('How this relates to your idea')<printed.indexOf('Sources &amp; details'));
 for(const record of records)assert.equal(printed.split(record.reader_finding||record.finding).length-1,1);
 const escaped=I.observedFindingsHTML([{...sources[0],text:JSON.stringify({reader_finding:'<img src=x>',reader_limit:'a < b & c'})}],records);
 assert(!escaped.includes('<img'));assert(escaped.includes('&lt;img src=x&gt;'));assert(escaped.includes('a &lt; b &amp; c'));
});

test('observed findings use exact validated source text rather than newer local reader fields',()=>{
 const source=docs.find(doc=>doc.kind==='experiment'),saved={reader_finding:'Saved concise finding.',reader_limit:'Saved concise limit.',finding:'Saved technical finding.',limitations:'Saved technical limit.'};
 const snapshot={...source,text:JSON.stringify(saved)},newer={id:source.id,reader_finding:'NEW local finding',reader_limit:'NEW local limit',finding:'NEW fallback',limitations:'NEW fallback limit'};
 const html=I.observedFindingsHTML([snapshot],[newer]);
 assert(html.includes(saved.reader_finding));assert(html.includes(saved.reader_limit));assert(!html.includes('NEW'));assert(!html.includes(saved.finding));
 for(const readerFields of [{},{reader_finding:'',reader_limit:'   '},{reader_finding:{text:'not prose'},reader_limit:['not prose']}]){
  const fallback=I.observedFindingsHTML([{...source,text:JSON.stringify({finding:saved.finding,limitations:saved.limitations,...readerFields})}],[newer]);
  assert(fallback.includes(saved.finding));assert(fallback.includes(saved.limitations));assert(!fallback.includes('NEW'));
 }
 for(const text of ['{broken','null','[]','"prose"','{}',JSON.stringify({finding:{text:'invalid'},limitations:'limit'})])assert.equal(I.observedFindingsHTML([{...source,text}],[newer]),'','Malformed snapshot must not fall back to live metadata');
 const c=C.confirm(I.initialDraft('A supplied method'),{id:'saved-findings',at});
 const r=C.bindResearch(c,{id:'saved-research',at,evidence:{snapshotId:'older',records:[{...registry.records.find(record=>record.id===source.id),...newer}],documents:[snapshot]},answer:'Scoped comparison [1].'});
 const printed=I.packetHTML(C.packetSnapshot(c,r));assert(printed.includes(saved.reader_finding));assert(printed.includes(saved.reader_limit));assert(!printed.includes('NEW local'));
});

test('compact retrieval avoids unknown-field scaffolding on actual published records',()=>{
 for(const text of ['Fibonacci keys on LP2-15','Test fixed invertible Hill matrix keys in two-rune blocks on LP2-15','Compare word lengths with other languages']){
  const c=C.confirm(I.initialDraft(text),{id:'x',at}),q=C.retrievalQuery(c).query;
  assert(!q.includes('unspecified'));assert(!q.includes('searchProtocol'));
  assert.deepEqual(S.select(docs,q).map(d=>d.id),S.select(docs,text).map(d=>d.id));
 }
});
test('three-page request can omit hint only while full confirmed scope remains explicit',()=>{
 const c=C.confirm(I.initialDraft('Fibonacci keys on LP2-15–17'),{id:'x',at});
 const full=C.queryForResearch(c,{maxLength:6000}),compact=C.retrievalQuery(c);
 assert.equal(full.pages.length,3);assert(full.query.includes('lp2-16'));assert(compact.query.includes('LP2-16'));
 assert.equal(C.queryForResearch(c,{maxLength:20}).query,null);
});
test('missing aim and scope ask once, without selecting values or conflating undecided with all',()=>{
 let d=I.initialDraft('Try a keyed spiral');
 assert.deepEqual(I.intakeQuestions(d).map(q=>q.id),['aim','scope']);
 assert.equal(d.aim.status,'unspecified');assert.equal(d.scope.status,'unspecified');
 d=I.answerIntake(d,'aim','undecided');assert.deepEqual(I.intakeQuestions(d).map(q=>q.id),['scope']);
 d=I.answerIntake(d,'scope','undecided');assert.equal(I.intakeQuestions(d).length,0);
 assert.equal(d.scope.status,'unspecified');assert.equal(d.aim.status,'unspecified');
 assert.equal(d.source.text,'Try a keyed spiral');
 assert.throws(()=>I.answerIntake(d,'scope','unsolved-lp2'));
});
test('explicit positive aim/scope skip questions while negation does not invent a goal',()=>{
 for(const text of ['Find readable text on LP2-15','Test a statistical effect on LP2-17','Reproduce the archived result on LP2-43','My goal is to compare the alignments on LP2-15']){
  const d=I.initialDraft(text);assert.equal(d.aim.status,'specified',text);assert.equal(d.scope.status,'specified',text);assert(!I.intakeQuestions(d).some(q=>['aim','scope'].includes(q.id)),text);
 }
 for(const text of ['Do not find readable text','Never reproduce the result','Compare whether others wanted to find readable text'])assert.equal(I.initialDraft(text).aim.status,'unspecified');
 const all=I.initialDraft('Find readable text on all unsolved LP2 pages');assert.equal(all.scope.value.pages.length,56);
 assert.equal(I.initialDraft('Find readable text on all unsolved LP2 pages except LP2-15').scope.status,'unspecified');
});
test('explicit page passage qualifier remains in confirmed scope instead of implying the whole page',()=>{
 const text='Reverse each row on LP2-43, lines 2–3';let d=I.initialDraft(text);
 assert.deepEqual(d.scope.value,{pages:['lp2-43'],description:'LP2-43, lines 2–3'});
 assert(!I.intakeQuestions(d).some(q=>q.id==='scope'));
 d=I.answerIntake(d,'aim','undecided');const c=C.confirm(d,{id:'passage',at});
 assert(I.rowsHTML(c).includes('LP2-43, lines 2–3'));
 assert(C.queryForResearch(c,{maxLength:6000}).query.includes('lines 2–3'));
 assert.equal(c.source.text,text);
 assert.equal(I.initialDraft('Do not reverse each row on LP2-43, lines 2–3').scope.status,'unspecified');
});
test('aim options/custom and exact custom scope preserve method, boundaries, source and independent fields',()=>{
 let d=I.initialDraft('Read each row backwards, keeping word boundaries.');d=C.clarify(d,'word-boundary','fixed_spaces');
 const oldMethod=C.serialize(d.method),source=d.source.text;
 d=I.answerIntake(d,'aim','unclassified','Check a visual symmetry');
 d=I.answerIntake(d,'scope','specific','LP2-43, lines 2–3');
 assert.equal(d.aim.value.detail,'Check a visual symmetry');assert.equal(d.aim.outcome.id,'unclassified');assert.equal(d.aim.provenance.kind,'user_clarification');
 assert.deepEqual(d.scope.value,{description:'LP2-43, lines 2–3'});assert.equal(C.serialize(d.method),oldMethod);
 assert(I.rowsHTML(d).includes('LP2-43, lines 2–3'));assert(!I.rowsHTML(d).includes('description:'));
 assert.equal(d.rules.boundaryMode.value,'fixed_spaces');assert.equal(d.source.text,source);
 const changed=C.revise(d,{aim:C.field('specified','Measure alignment',{kind:'user_clarification',refs:[]})});assert.deepEqual(changed.scope,d.scope);
 let exact=I.answerIntake(I.answerIntake(I.initialDraft('Try this'),'aim','decipher'),'scope','specific','LP2-15, LP2-17');
 assert.deepEqual(exact.scope.value.pages,['lp2-15','lp2-17']);
 assert.throws(()=>I.answerIntake(I.initialDraft('Try this'),'scope','specific','LP2-99'));
 assert.throws(()=>I.answerIntake(I.initialDraft('Try this'),'aim','unclassified',''));
});
test('bounded unsolved selection renders ranges without expanding holes or mutating confirmed scope',()=>{
 let d=I.answerIntake(I.answerIntake(I.initialDraft('Try this'),'aim','measure'),'scope','unsolved-lp2');
 assert.equal(d.scope.value.pages.length,56);const before=C.serialize(d.scope);
 const html=I.rowsHTML(d);assert(html.includes('LP2-00–55'));assert.equal((html.match(/scope-range/g)||[]).length,0);
 assert.equal(C.serialize(d.scope),before);
 assert.deepEqual(I.compactPages(['lp2-15','lp2-17']).map(t=>t.text),['LP2-15','LP2-17']);
 assert.deepEqual(I.compactPages(['lp1-15','lp1-16','lp2-00','lp2-01','lp2-03']).map(t=>t.text),['LP1-15–16','LP2-00–01','LP2-03']);
});
test('aim choices do not derail strong actual-record technique retrieval',()=>{
 for(const [text,id] of [['Fibonacci keys on LP2-15','fibonacci-stream-skip-grid'],['Test fixed invertible Hill matrix keys in two-rune blocks on LP2-15','direct-hill-key-feasibility']]){
  for(const aim of ['decipher','measure','reproduce']){
   const c=C.confirm(I.answerIntake(I.initialDraft(text),'aim',aim),{id:'qa',at});
   assert.equal(S.select(docs,C.retrievalQuery(c).query)[0].id,id);
  }
 }
});
test('canonical outcomes retain exact wording and do not create visitor categories',()=>{
 const ids=Object.keys(C.OUTCOMES),solve=I.initialDraft('solve LP2'),readable=I.initialDraft('Find readable text');
 assert.equal(solve.aim.outcome.id,'decipher');assert.equal(readable.aim.outcome.id,'decipher');
 for(const d of [solve,readable]){const html=I.rowsHTML(d);assert(html.includes('Outcome'));assert(html.includes('Decipher the text'));assert.equal(d.source.text,d.aim.value.wording);}
 let custom=I.answerIntake(I.initialDraft('Try a keyed spiral'),'aim','unclassified','Check the moth geometry');
 assert.equal(custom.aim.outcome.id,'unclassified');assert(!I.rowsHTML(custom).includes('class="tag">Check the moth geometry'));
 assert(I.rowsHTML(custom).includes('objective-detail'));assert.deepEqual(Object.keys(C.OUTCOMES),ids);
 const alias=I.answerIntake(I.initialDraft('Try a keyed spiral'),'aim','unclassified','solve LP2');assert.equal(alias.aim.outcome.id,'decipher');assert.equal(alias.aim.value.wording,'solve LP2');
});
test('exact objectives remain visible beneath shared categories on screen, packet and shared draft',()=>{
 const H=require('../claim-share.js'),ids=Object.keys(C.OUTCOMES);
 const goals=['solve LP2','Find readable text',{outcomeId:'decipher',wording:'Decipher the text',detail:'Find readable text'},
  {outcomeId:'decipher',detail:'Solve only the selected opening'},
  {outcomeId:'unclassified',detail:'Compare <img src=x onerror=alert(1)> & shapes'}];
 for(const aim of goals){
  const d=C.createDraft({source:{text:'An exact supplied method'},aim:C.field('specified',aim),
   method:C.field('specified',{operations:[{id:'reverse_row_runes',label:'Reverse each row'}]}),scope:C.field('specified',{pages:['lp2-15']})});
  const c=C.confirm(d,{id:'exact-goal',at}),detail=C.normalizeOutcome(c.aim).detail;
  const expected=detail.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const binding=C.binding(c),query=C.retrievalQuery(c),rank=S.select(docs,query.query).map(r=>r.id);
  assert(I.rowsHTML(c).includes('<p class="objective-detail">'+expected+'</p>'));
  assert.equal(I.rowsHTML(c).includes('<img'),false);
  const r=C.bindResearch(c,{id:'goal-result',at,evidence:{snapshotId:'x',records:[],documents:[],search:{reason:'no-matching-records'}},answer:'No match.'});
  assert(I.packetHTML(C.packetSnapshot(c,r)).includes('<p class="objective-detail">'+expected+'</p>'));
  const shared=H.decode(H.encode(c)).draft;
  assert.equal(C.normalizeOutcome(shared.aim).detail,detail);assert(I.rowsHTML(shared).includes('<p class="objective-detail">'+expected+'</p>'));
  assert.equal(C.binding(c),binding);assert.deepEqual(C.retrievalQuery(c),query);assert.deepEqual(S.select(docs,query.query).map(r=>r.id),rank);
 }
 for(const detail of ['Decipher the text','  DECIPHER THE TEXT.  ']){
  const d=C.createDraft({source:{text:'Rule'},aim:C.field('specified',{outcomeId:'decipher',detail})});
  assert(!I.rowsHTML(d).includes('objective-detail'),'Only a repetition of the canonical label is suppressed');
 }
 assert.deepEqual(Object.keys(C.OUTCOMES),ids);
});
test('outcome-only inputs never invent a method or retrieve arbitrary attempts',()=>{
 for(const text of ['Find readable text','solve LP2','Decipher LP2','Decrypt LP2',...Object.values(C.OUTCOMES)]){
  let d=I.initialDraft(text);assert.equal(d.method.status,'unspecified',text);assert(I.intakeQuestions(d).some(q=>q.id==='method'));
  d=I.answerIntake(d,'method','undecided');d=I.answerIntake(d,'scope','undecided');
  assert.equal(C.retrievalQuery(C.confirm(d,{id:'outcome-only',at})).query,null,text);
 }
 const full=I.initialDraft('solve LP2 using Vigenere with key FIRFUMFERENFE');assert.equal(full.method.status,'specified');assert(full.method.value.operations[0].label.includes('FIRFUMFERENFE'));
 let described=I.answerIntake(I.initialDraft('solve LP2'),'method','describe','Reverse each row, then apply key ABC');
 assert.equal(described.method.value.operations[0].label,'Reverse each row, then apply key ABC');
 assert.equal(described.source.text,'solve LP2');
 const family=I.answerIntake(I.initialDraft('solve LP2'),'method','family:feedback');assert.deepEqual(C.classifyMethod(family.method).familyIds,['feedback']);assert.equal(family.method.value.operations[0].id,'family_selection');assert.equal(family.rules.reset.status,'unspecified');
});
console.log('PASS '+count+' investigate helper/retrieval tests; all research uses actual registry records and no inference.');

// Minimal event-DOM harness: no browser engine, network or UI automation.
class Element{
 constructor(id){this.id=id;this.listeners={};this.disabled=false;this.textContent='';this.value='';this.hidden=false;this.html='';}
 addEventListener(type,fn){this.listeners[type]=fn;}
 fire(type){return this.listeners[type]?.({preventDefault(){},target:this});}
 focus(){} remove(){} replaceChildren(){this.html='';}
 set innerHTML(value){this.html=value;}get innerHTML(){return this.html;}
 insertAdjacentHTML(where,value){this.html+=value;}
}
function fakeDocument(search=''){
 const host=new Element('investigate'),print=new Element('print-snapshot'),cache=new Map();
 return {defaultView:{location:{search}},activeElement:null,
  getElementById(id){
   if(id==='investigate')return host;if(id==='print-snapshot')return print;
   if(!host.html.includes('id="'+id+'"')&&!cache.get('method-step-list')?.html.includes('id="'+id+'"'))return null;
   if(!cache.has(id))cache.set(id,new Element(id));return cache.get(id);
  },querySelector(selector){if(selector==='input[name=choice]:checked')return this.selectedChoice?{value:this.selectedChoice}:null;if(selector==='.privacy')return null;if(selector.startsWith('#'))return this.getElementById(selector.slice(1));return null;},
  host,print};
}
function answerInDOM(doc,choice,text=''){
 doc.selectedChoice=choice;doc.getElementById('other-detail').value=text;
 doc.getElementById('clarification').fire('change');doc.getElementById('clarification').fire('submit');doc.selectedChoice=null;
}
async function mockInterpretation(options){
 const P=require('../claim-interpretation'),text=JSON.parse(options.body).text,draft=I.initialDraft(text),pages=P.pagesFromSource(text);
 const candidate={schema:P.SCHEMA,outcome:draft.aim.status==='specified'?{id:C.normalizeOutcome(draft.aim.value).id,source:{start:0,quote:text}}:null,
  steps:draft.method.status==='specified'?draft.method.value.operations.map(op=>({id:op.id==='ambiguous_reversal'?'ambiguous_reversal':['reverse_row_runes','reverse_value_digits'].includes(op.id)?op.id:'described_method',familyId:null,source:{start:text.indexOf(op.sourceText||op.label),quote:op.sourceText||op.label},parameters:{}})):[],
  scope:pages.length?{pages,passage:null,source:{start:0,quote:text}}:null,rules:{}};
 P.validateCandidate(text,candidate);
 return Response.json({candidate,sourceBinding:Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex')});
}
async function waitForReview(app){await require('./mock_interpretation_response.cjs').waitForReview(app);assert.equal(app.getSnapshot().stage,'review','Validated mocked interpretation reaches review');}
(async()=>{
 const doc=fakeDocument('?q=Fibonacci%20keys&pages=lp2-15&pages=lp2-17');
 let resolveOptional;const optional=new Promise(resolve=>{resolveOptional=resolve;});
 const app=I.createApp(doc,{fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret'});
  if(url==='https://mock.example/interpret')return mockInterpretation(options);
  return optional;
 },now:()=>at,id:()=> 'test-id'});
 assert(doc.host.html.includes('Fibonacci keys'));assert.equal(app.getSnapshot().stage,'input');
 await app.ready;
 doc.getElementById('idea').value='Fibonacci keys';doc.getElementById('intake').fire('submit');
 await waitForReview(app);
 assert.deepEqual(app.getSnapshot().draft.scope.value.pages,['lp2-15','lp2-17']);
 assert(doc.host.html.includes('class="question-title"'));assert(!doc.host.html.includes('id="confirm"'));
 answerInDOM(doc,'undecided');
 assert.equal(doc.getElementById('confirm').disabled,false,'Optional context cannot stall confirmation');
 doc.getElementById('edit').fire('click');
 const before=doc.host.innerHTML;doc.getElementById('edit-method').value='Unsaved method edit';
 resolveOptional(Response.json({documents:[]}));await new Promise(resolve=>setTimeout(resolve,10));
 assert.equal(doc.host.innerHTML,before);assert.equal(doc.getElementById('edit-method').value,'Unsaved method edit');
 assert.equal(app.getSnapshot().draft.source.text,'Fibonacci keys');
 app.destroy();console.log('PASS mocked event-DOM: legacy prefill/no autosubmit, exact page hints, optional index does not stall or erase editor.');
 const journey=fakeDocument('?q=Fibonacci%20keys%20on%20LP2-15');
 const requests=[],timers=[];let prints=0,serial=0;
 const application=I.createApp(journey,{fetcher:async(url,options)=>{
  if(url==='data/experiments.json')return Response.json(registry);
  if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret'});
  if(url==='https://mock.example/interpret')return mockInterpretation(options);
  if(url==='data/assistant-index.json')return Response.json({documents:[]});
  return new Promise(resolve=>requests.push({resolve,options}));
 },now:()=>at,id:()=> 'test-'+(++serial),printer:()=>{prints++;},schedule:fn=>{timers.push(fn);return timers.length-1;},unschedule:()=>{}});
 await application.ready;
 journey.getElementById('idea').value='Fibonacci keys on LP2-15';journey.getElementById('intake').fire('submit');
 await waitForReview(application);
 answerInDOM(journey,'undecided');
 journey.getElementById('confirm').fire('click');
 assert.equal(requests.length,1);assert.equal(application.getSnapshot().busy,true);
 const sent=JSON.parse(requests[0].options.body);
 assert.equal(sent.query,'Fibonacci keys on LP2-15. LP2-15');assert(sent.confirmedQuery.includes('Original wording'));assert.deepEqual(sent.pages,['lp2-15']);
 const evidence=docs.find(d=>d.id==='fibonacci-stream-skip-grid');
 const reply=()=>Response.json({answer:'The published Fibonacci stream test is bounded [1].',sources:[evidence]});
 requests[0].resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 let state=application.getSnapshot();assert(state.result&&state.packet);assert(Object.isFrozen(state.packet));
 const frozen=C.serialize(state.packet),confirmedBinding=C.binding(state.confirmed);
 journey.getElementById('print').fire('click');assert.equal(prints,1);assert(journey.print.html.includes(state.result.answer.replace(' [1].','')));
 journey.getElementById('edit').fire('click');assert.equal(application.getSnapshot().confirmed,null);
 journey.getElementById('cancel-edit').fire('click');
 assert.equal(C.serialize(application.getSnapshot().packet),frozen);assert.equal(C.binding(application.getSnapshot().confirmed),confirmedBinding);
 // Retry while preserving an old answer is not exposed; edit then reconfirm.
 journey.getElementById('edit').fire('click');
 journey.getElementById('edit-aim').value='';journey.getElementById('edit-objective').value='';journey.getElementById('edit-method').value='Fibonacci stream keys';journey.getElementById('edit-scope').value='LP2-15';journey.getElementById('edit-rules').value='';
 journey.getElementById('editor').fire('submit');journey.getElementById('confirm').fire('click');
 assert.equal(requests.length,2);const old=requests[1];
 journey.getElementById('cancel').fire('click');assert.equal(old.options.signal.aborted,true);assert.equal(application.getSnapshot().busy,false);
 journey.getElementById('retry').fire('click');assert.equal(requests.length,3);
 const current=requests[2];assert.equal(current.options.signal.aborted,false);
 timers[1]();assert.equal(current.options.signal.aborted,false,'An older timeout cannot abort the new request');
 old.resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 assert.equal(application.getSnapshot().result,null,'Canceled late response cannot populate the current result');
 current.resolve(reply());await new Promise(resolve=>setTimeout(resolve,5));
 assert(application.getSnapshot().result&&application.getSnapshot().packet);
 const saved=application.getSnapshot().packet;
 journey.getElementById('back').fire('click');assert.equal(application.getSnapshot().stage,'input');assert.equal(application.getSnapshot().packet,null);
 assert.equal(saved.research.answer,'The published Fibonacci stream test is bounded [1].','Old frozen packet remains unchanged after leaving');
 journey.getElementById('idea').value='Unmatched careful idea';journey.getElementById('intake').fire('submit');
 await waitForReview(application);
 answerInDOM(journey,'unclassified','Check the visual alignment');answerInDOM(journey,'specific','LP2-43, lines 2–3');
 journey.getElementById('confirm').fire('click');
 assert.equal(requests.length,4);
 const noMatchConfirmed=application.getSnapshot().confirmed;
 requests[3].resolve(Response.json({answer:null,sources:[],reason:'no-matching-records'}));await new Promise(resolve=>setTimeout(resolve,5));
 const empty=application.getSnapshot();assert.equal(empty.result.noMatch,true);assert.deepEqual(empty.result.sources,[]);
 assert.equal(C.binding(empty.packet.confirmed),C.binding(noMatchConfirmed));assert(!journey.host.html.includes('AI comparison'));
 assert(journey.host.html.includes('<h2>Search result</h2>'));assert(!journey.host.html.includes('AI interpretation'));
 const noMatchPrint=I.packetHTML(empty.packet);assert(noMatchPrint.includes('<h2>Search result</h2>'));assert(!noMatchPrint.includes('AI interpretation'));assert(!noMatchPrint.includes('How this relates'));
 assert(journey.getElementById('print'));assert(!journey.getElementById('retry'));
 journey.getElementById('edit').fire('click');assert.equal(application.getSnapshot().draft.source.text,'Unmatched careful idea');journey.getElementById('cancel-edit').fire('click');assert.equal(application.getSnapshot().result.noMatch,true);
 journey.getElementById('edit').fire('click');assert(journey.host.html.includes('LP2-43, lines 2–3'));
 journey.getElementById('edit-aim').value='unclassified';journey.getElementById('edit-objective').value='Check a different alignment';journey.getElementById('edit-method').value='Unmatched careful idea';journey.getElementById('edit-scope').value='LP2-43, lines 2–3';journey.getElementById('edit-rules').value='';
 journey.getElementById('editor').fire('submit');
 assert.deepEqual(application.getSnapshot().draft.scope.value,{description:'LP2-43, lines 2–3'},'Custom passage survives an unrelated aim edit');
 assert.equal(application.getSnapshot().draft.source.text,'Unmatched careful idea');
 // Controlled editor category/detail round trips never mint categories or erase source.
 for(const [category,detail,expected] of [['measure','Find plaintext in the comparison','measure'],['unclassified','Estimate publication date','unclassified'],['unclassified','Find plaintext','decipher']]){
  journey.getElementById('edit').fire('click');journey.getElementById('edit-aim').value=category;journey.getElementById('edit-objective').value=detail;
  journey.getElementById('edit-method').value='Unmatched careful idea';journey.getElementById('edit-scope').value='LP2-43, lines 2–3';journey.getElementById('edit-rules').value='';journey.getElementById('editor').fire('submit');
  assert.equal(application.getSnapshot().draft.aim.outcome.id,expected);assert.equal(application.getSnapshot().draft.aim.value.detail,detail);
  assert.equal(application.getSnapshot().draft.source.text,'Unmatched careful idea');
 }
 const beforeGoalOnly=requests.length;journey.getElementById('back').fire('click');journey.getElementById('idea').value='solve LP2';journey.getElementById('intake').fire('submit');
 await waitForReview(application);
 assert(journey.host.html.includes('What method do you want to check?'));answerInDOM(journey,'undecided');answerInDOM(journey,'undecided');
 assert.equal(journey.getElementById('confirm'),null);assert(journey.host.html.includes('Browse research'));assert.equal(requests.length,beforeGoalOnly,'A goal without method sends no research request');
 application.destroy();console.log('PASS mocked full journey: success, exact print packet, edit/cancel restoration, new confirmation, cancel/retry, stale response guard and request-local timeout.');
})().catch(error=>{console.error(error);process.exitCode=1;});

(async()=>{
 const doc=fakeDocument(),app=I.createApp(doc,{fetcher:async(url,options)=>url==='https://mock.example/interpret'?mockInterpretation(options):Response.json(url==='data/experiments.json'?registry:url==='data/assistant.json'?{endpoint:'https://mock.example/ask',interpretationEndpoint:'https://mock.example/interpret'}:{documents:[]})});
 await app.ready;
 const source='Reverse each row on LP2-15, then apply Vigenere with key FIRFUMFERENFE';
 doc.getElementById('idea').value=source;doc.getElementById('intake').fire('submit');await waitForReview(app);answerInDOM(doc,'decipher');answerInDOM(doc,'inspect-output');
 const original=app.getSnapshot().draft;
 original.method.value.operations[1].parameters={key:'FIRFUMFERENFE',offset:7};
 original.unresolved.push({kind:'source_note',text:'Preserve this independent constraint'});
 const initial=C.serialize(original.method),first=C.serialize(original.method.value.operations[0]);
 doc.getElementById('edit').fire('click');
 assert(doc.host.html.includes('Exact rule for step 1'));assert(doc.host.html.includes('Exact rule for step 2'));
 const fillSteps=()=>app.getSnapshot().draft.method.value.operations.forEach((op,index)=>{
  doc.getElementById(index?'edit-method-'+index:'edit-method').value=op.label||op.sourceText||'';
  doc.getElementById('edit-method-family-'+index).value=op.declaredFamilyId||'';
 });
 fillSteps();doc.getElementById('edit-objective').value='An unsaved objective';
 doc.getElementById('edit-method-1').value='Apply ciphertext autokey';doc.getElementById('method-up-1').fire('click');
 let state=app.getSnapshot().draft;
 assert.equal(state.method.value.operations[0].label,'Apply ciphertext autokey');assert.equal(C.serialize(state.method.value.operations[1]),first);
 assert(state.methodEdits.some(edit=>edit.previousOperation?.parameters?.offset===7));
 assert(state.unresolved.some(note=>note.text==='Preserve this independent constraint'));assert.equal(doc.getElementById('edit-objective').value,'An unsaved objective','Step actions preserve other unsaved editor inputs');
 fillSteps();doc.getElementById('method-add').fire('click');assert.equal(app.getSnapshot().draft.method.value.operations.length,3);
 fillSteps();doc.getElementById('edit-method-2').value='Shift each rune by three';doc.getElementById('method-up-2').fire('click');
 assert.equal(app.getSnapshot().draft.method.value.operations[1].label,'Shift each rune by three');
 fillSteps();doc.getElementById('edit-method-family-2').value='feedback';doc.getElementById('method-remove-1').fire('click');
 state=app.getSnapshot().draft;assert.equal(state.method.value.operations.length,2);
 assert.equal(state.method.value.operations[1].declaredFamilyId,'feedback');assert.equal(C.classifyMethod(state.method).operations[1].basis,'category_conflict');
 assert.equal(state.source.text,source);assert.equal(doc.getElementById('edit-objective').value,'An unsaved objective');
 doc.getElementById('cancel-edit').fire('click');assert.equal(C.serialize(app.getSnapshot().draft.method),initial,'Cancel restores the original ordered operations and parameters');
 app.destroy();console.log('PASS method editor DOM: independent exact steps, add/remove/reorder/category, retained metadata/history/constraints, unsaved other inputs and cancel restoration.');
})().catch(error=>{console.error(error);process.exitCode=1;});
