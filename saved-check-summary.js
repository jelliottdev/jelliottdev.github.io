/* One independently verified saved computation, never question-wide coverage. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,E=node?require('./local-experiment.js'):root.LocalExperiment,J=node?require('./finite-json.js'):root.FiniteJSON,Protocols=node?require('./experiment-protocols.js'):root.ExperimentProtocols;
 const SCHEMA='liberpedia-saved-check-summary-v1',MAX_BYTES=4*1024*1024,proofs=new WeakMap(),KINDS=['exact-prefix','exact-prefix-set','language-score','measurement','word-prime-sums','word-affine-count'];
 const need=(ok,message)=>{if(!ok)throw Error(message);},exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
 const capture=value=>J.capture(value,{maxBytes:MAX_BYTES,maxDepth:24,maxNodes:200000});
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 const count=value=>value.toLocaleString('en-US');
 function describe(task,result){
  const criterion=task.criterion,n=result.metrics.pages,scope='This describes only this saved calculation. Other settings and pages in the question may remain open.';
  if(criterion.kind==='exact-prefix')return {criterionLabel:'Supplied '+criterion.values.length+'-rune opening',heading:'Saved opening check',finding:result.matches.filter(page=>page.matched).length+' of '+n+' saved pages begin with the supplied '+criterion.values.length+'-rune sequence.',limit:'Only this exact sequence, method and page starts were checked. A match alone does not establish a decryption. '+scope};
  if(criterion.kind==='exact-prefix-set')return {criterionLabel:criterion.openings.length+' supplied opening sequences',heading:'Saved opening comparison',finding:result.matches.filter(page=>page.matched).length+' of '+n+' saved pages begin with at least one of the '+criterion.openings.length+' supplied rune sequences.',limit:'Only these supplied sequences, this method and page starts were checked. A match alone does not establish a decryption. '+scope};
  if(criterion.kind==='language-score'){
   const compared=result.languageScore.pages.filter(page=>page.status==='compared').length,short=result.languageScore.pages.filter(page=>page.status==='insufficient').length;
   return {criterionLabel:'Language-sample comparison',heading:'Saved language comparison',finding:compared+' '+(compared===1?'page compared':'pages compared')+' with eight fixed language samples.'+(short?' '+short+' '+(short===1?'page was':'pages were')+' too short to score (fewer than 40 runes).':''),limit:'These comparisons describe rune patterns, not readable text, a translation or a language probability. Too-short pages provide no language comparison. '+scope};
  }
  if(criterion.kind==='measurement')return {criterionLabel:'Rune counts and neighboring repeats',heading:'Saved rune measurements',finding:count(result.metrics.runes)+' runes and '+count(result.metrics.equalAdjacentPairs)+' equal neighboring pairs among '+count(result.metrics.adjacentPairs)+' within-page rune pairs in the saved output.',limit:'Non-runes are omitted when counting neighboring rune pairs. These counts do not test readability or identify a cipher. '+scope};
  const protocol=Protocols?.describe(criterion);need(protocol,'This saved measurement has no maintained summary.');
  if(criterion.kind==='word-prime-sums')return {criterionLabel:protocol.title,heading:'Saved rune-value sums',finding:count(result.wordSums.words)+' groups measured using '+(criterion.table==='reversed'?'reversed':'canonical')+' prime assignments; the sums total '+count(result.wordSums.total)+'.',limit:protocol.reviewBoundary+' '+protocol.limit+' '+scope};
  return {criterionLabel:protocol.title+'; multiplier '+criterion.a+', offset '+criterion.b,heading:'Saved within-group pair counts',finding:count(result.wordPairs.matches)+' matches among '+count(result.wordPairs.opportunities)+' rune pairs '+criterion.lag+' '+(criterion.lag===1?'position':'positions')+' apart inside the declared groups.',limit:protocol.reviewBoundary+' '+protocol.limit+' '+scope};
 }
 async function prepare(options,crypto=root.crypto){
  const input=capture(options);need(exact(input,['task','run'])&&exact(input.run,['id','createdAt','result']),'Use one complete saved task and result receipt.');
  J.capture(input.task,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000});J.capture(input.run.result,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000});
  need(typeof input.run.id==='string'&&input.run.id.length===64&&/^[a-f0-9]{64}$/.test(input.run.id),'The saved result digest is invalid.');
  const date=input.run.createdAt;need(typeof date==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(date)&&Number.isFinite(Date.parse(date))&&new Date(date).toISOString()===date,'The saved receipt date is invalid.');
  await E.checkIdentity(input.task,crypto);need(KINDS.includes(input.task.criterion.kind),'This saved calculation has no supported summary.');
  const result=await E.verify(input.task,input.run.result,crypto),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(result))))].map(n=>n.toString(16).padStart(2,'0')).join('');
  need(digest===input.run.id,'The saved result digest does not match its verified output.');
  const summary=freeze({schema:SCHEMA,...describe(input.task,result),pageIds:input.task.pages.map(page=>page.id),taskId:input.task.taskId,resultId:input.run.id,createdAt:date});
  need(E.stable(capture(options))===E.stable(input),'The saved calculation changed during verification.');
  const proof=Object.freeze({});proofs.set(proof,summary);return proof;
 }
 function inspect(proof){const summary=proofs.get(proof);need(summary,'Use an independently verified saved-check summary.');return summary;}
 const api={SCHEMA,MAX_BYTES,prepare,inspect};if(node)module.exports=api;else root.SavedCheckSummary=api;
})(typeof globalThis!=='undefined'?globalThis:this);
