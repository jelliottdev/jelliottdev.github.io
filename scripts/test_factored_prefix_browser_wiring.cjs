'use strict';
// Browser-global dependency integration only; synthetic arithmetic, no hosted writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),{webcrypto}=require('node:crypto');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'run.html'),'utf8'),scripts=[...html.matchAll(/<script\b[^>]*\bsrc="([^"]+)"/g)].map(m=>m[1].split('?')[0]).filter(s=>!['site-navigation.js','run.js'].includes(s));
const context=vm.createContext({console,crypto:webcrypto,TextEncoder,TextDecoder,AbortController,AbortSignal,DOMException,URL,URLSearchParams,Blob,Response,Request,setTimeout,clearTimeout,atob,btoa});
for(const script of scripts)vm.runInContext(fs.readFileSync(path.join(root,script),'utf8'),context,{filename:script});
context.bundleJSON=fs.readFileSync(path.join(root,'data/local-run-inputs.json'),'utf8');
(async()=>{
 assert(context.FactoredPrefixReuse&&context.VerifiedPrefixEvaluation&&context.FactoredSearchSession&&context.FiniteWorkspaceRouter);
 console.log('PASS actual run.html browser script order resolves all prefix dependencies without CommonJS');
 const value=await vm.runInContext(`(async()=>{
  const E=LocalExperiment,Q=FactoredFiniteQuestion,bundle=JSON.parse(bundleJSON),alphabet=bundle.alphabet,pages=[{id:'lp2-15',text:alphabet[0].rune+alphabet[1].rune}],criterion={kind:'exact-prefix',values:[0]},domain=await Q.bind({engine:E.ENGINE,inputVersion:'raw',alphabet,pages,criterion,programs:[{steps:[{op:'affine',a:1,b:0}]}]}),task=await E.prepare({title:'Original negative software check',alphabet,pages,steps:domain.programs[0].steps,criterion:{kind:'exact-prefix',values:[28]}}),result=E.run(task);
  const hash=async x=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(x))))).map(v=>v.toString(16).padStart(2,'0')).join(''),source={task,inputVersion:'raw',run:{id:await hash(result),createdAt:'2026-10-25T12:00:00.000Z'}},proposalId='p_'+'a'.repeat(64);source.run.result=result;
  const page={schema:'liberpedia-factored-prefix-evidence-page-v1',evidenceMode:'verified-output-prefix-v1',proposalId,domainId:domain.id,inputVersion:'raw',scanId:'A'.repeat(24),sequence:0,previousPageSha256:null,sources:[source],sourceLinks:[{taskId:task.taskId,href:"run.html#task="+task.taskId,label:"Original software output"}],continuation:{nextCursor:null,complete:true},snapshotToken:'isolated-browser-token'};page.pageSha256=await hash({...page,continuation:{complete:true}});
  let staged=0;E.run=()=>{throw Error('Client must not execute requested targets');};
  const scan=FactoredEvidenceClient.createScan({proposalId,domain,evidenceMode:'verified-output-prefix-v1',fetchPage:async()=>page,onSources:()=>{staged++;}});await scan.step();
  const inspected=scan.evidence().sources[0],markup=FiniteSearchWorkspaceView.render(null,{phase:'ready',inspected:{task,result:await E.verify(task,result),evidenceKind:'derived-prefix',requestedCriterion:criterion,pageId:'lp2-15',label:'Original verified output'}});
  const strict=FactoredEvidenceClient.createScan({proposalId,domain,fetchPage:async()=>page});let strictRejected=false;try{await strict.step();}catch{strictRejected=true;}
  return {oldMatched:result.matches[0].matched,proof:scan.getState().proof,inspected,staged,markup,strictRejected};
 })()`,context);
 assert.equal(value.oldMatched,false);assert.equal(value.proof.decision.answer,'prefix-found');assert.equal(value.proof.derivedCases,1);assert.equal(value.staged,1);assert.equal(value.inspected.evidenceKind,'derived-prefix');assert.equal(value.strictRejected,true);assert.match(value.markup,/Original saved result/);assert.match(value.markup,/All 1 prefix positions match/);
 console.log('PASS browser-global client independently derives new hit while original result remains negative and default rejects new wire');
 console.log('2 browser prefix wiring groups passed; no target execution or network writes');
})().catch(e=>{console.error(e);process.exitCode=1;});


