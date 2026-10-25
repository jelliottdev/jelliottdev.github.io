'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{webcrypto,createHash}=require('node:crypto');
const E=require('../local-experiment.js'),F=require('../research-family.js');
const clone=v=>JSON.parse(JSON.stringify(v));
const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));
const source=fs.readFileSync('research-family.js','utf8');
function browser(code=source){const context={LocalExperiment:E,TextEncoder,crypto:webcrypto};vm.createContext(context);vm.runInContext(code,context);return context.ResearchFamily;}
(async()=>{
 const original=E.stable(bundle),view=await F.snapshot(bundle,webcrypto),ids=F.caseIds(view);
 assert.equal(view.id,'deor-feedback-v1');assert.equal(view.configurations.length,18);assert.equal(view.pages.length,55);assert.equal(view.totalCases,990);assert.equal(ids.length,990);assert.equal(new Set(ids).size,990);
 assert(!view.pages.some(p=>p.id==='lp2-50'));assert.equal(view.pages[0].id,'lp2-00');assert.equal(view.pages.at(-1).id,'lp2-55');
 assert.deepEqual(ids,ids.slice().sort());assert.deepEqual(view.configurations.map(c=>[c.mode,c.direction,c.reset]).sort(),['repeat','plaintext-autokey','ciphertext-autokey'].flatMap(m=>['subtract','add'].flatMap(d=>['page','line','word'].map(r=>[m,d,r]))).sort());
 // The criterion comes from an existing reviewed recipe rather than a fresh crib.
 const published=JSON.parse(fs.readFileSync('experiments/records/lp2-known-vigenere-keys/record.json','utf8')).browser_followups[0].card.rules.evaluation.value;
 let plan;const oldRun=E.run;E.run=()=>{throw Error('Family preparation must not execute manuscript work.');};
 try{plan=await F.prepare(bundle,[ids[989],ids[0]],webcrypto);assert.deepEqual(await F.validatePlan(plan,bundle,webcrypto),plan);}finally{E.run=oldRun;}
 assert.deepEqual(plan.cases.map(c=>c.id),[ids[0],ids[989]]);assert.deepEqual(await F.prepare(bundle,[ids[0],ids[989]],webcrypto),plan);
 let digests=0;const counted={subtle:{digest(...args){digests++;return webcrypto.subtle.digest(...args);}}},factoryInput=clone(bundle),preparer=await F.createPreparer(factoryInput,counted);
 assert.equal(digests,1);assert.deepEqual(preparer.snapshot,view);factoryInput.alphabet.reverse();preparer.snapshot.pages[0].text='Changed public snapshot';preparer.snapshot.configurations[0].mode='changed';
 assert.deepEqual(await preparer.prepare([ids[989],ids[0]]),plan);assert.equal(digests,4,'Each batch hashes only its tasks and envelope after one family revision');assert.deepEqual(await preparer.validatePlan(plan),plan);
 const badPrepared=clone(plan);badPrepared.extra=true;await assert.rejects(preparer.validatePlan(badPrepared));
 assert.deepEqual(Object.keys(plan).sort(),['schema','familyId','revision','planId','cases'].sort());
 for(const item of plan.cases){assert.equal(item.id,item.configuration+'--'+item.pageId);assert.equal(item.task.pages.length,1);assert.equal(item.task.pages[0].id,item.pageId);assert.deepEqual(item.task.steps[0].key,[23,18,3,4]);assert.deepEqual(item.task.criterion,published);await E.checkIdentity(item.task,webcrypto);assert.deepEqual(oldRun(item.task),oldRun(await E.prepare({...item.task},webcrypto)));}
 const max=await F.prepare(bundle,ids.slice(0,12),webcrypto);assert.equal(max.cases.length,12);
 assert.deepEqual(await F.validateExecutionPlan(plan,webcrypto),plan);assert.deepEqual(await F.validateExecutionPlan(max,webcrypto),max);
 const rehash=p=>{const body={...p};delete body.planId;p.planId=createHash('sha256').update(E.stable(body)).digest('hex');return p;};
 for(const alter of [p=>p.extra=true,p=>p.familyId='other',p=>p.schema='other',p=>p.revision='unknown',p=>p.planId='0'.repeat(64),p=>p.cases=[],p=>p.cases.reverse(),p=>p.cases.push(p.cases[0]),p=>p.cases[0].configuration='repeat--add--word',p=>p.cases[0].pageId='lp2-50',p=>p.cases[0].extra=true]){const modified=clone(plan);alter(modified);await assert.rejects(F.validateExecutionPlan(modified,webcrypto));}
 // Even a newly hashed, otherwise engine-valid task cannot change this family's rule.
 for(const change of [t=>t.title='Other',t=>t.steps[0].key[0]=0,t=>t.steps[0].mode=t.steps[0].mode==='repeat'?'plaintext-autokey':'repeat',t=>t.criterion.values[0]=0,t=>t.pages[0].id='lp2-56',t=>t.pages[0].text='',t=>t.alphabet.reverse()]){const modified=clone(plan),task=clone(modified.cases[0].task);change(task);modified.cases[0].task=await E.prepare(task,webcrypto);rehash(modified);await assert.rejects(F.validateExecutionPlan(modified,webcrypto));}
 const expanded=clone(max);expanded.cases.push(clone(plan.cases[1]));rehash(expanded);await assert.rejects(F.validateExecutionPlan(expanded,webcrypto));
 for(const invalid of [null,[],ids.slice(0,13),[ids[0],ids[0]],['repeat--add--page--lp2-50'],['repeat--add--page--lp2-56'],['repeat--subtract--page--lp2-00 '],[{id:ids[0]}]])await assert.rejects(F.prepare(bundle,invalid,webcrypto));
 for(const alter of [p=>p.title='new',p=>p.planId='0'.repeat(64),p=>p.revision='0'.repeat(64),p=>p.cases.reverse(),p=>p.cases[0].configuration='repeat--add--word',p=>p.cases[0].pageId='lp2-56',p=>p.cases[0].task.title='Changed title',p=>p.cases[0].task.steps[0].key[0]=0,p=>p.cases[0].task.criterion.values[0]=0,p=>p.cases[0].task.pages[0].text+='x',p=>p.cases[0].extra=true]){const modified=clone(plan);alter(modified);await assert.rejects(F.validatePlan(modified,bundle,webcrypto));}
 // Semantic input order is canonical, regardless of aggregate file ordering.
 const shuffled=clone(bundle);shuffled.pages.reverse();assert.equal((await F.snapshot(shuffled,webcrypto)).revision,view.revision);
 for(const change of [b=>b.pages.find(p=>p.id==='lp2-00').raw+=' ',b=>b.alphabet[0].prime=3,b=>b.alphabet.reverse(),b=>b.alphabet[0].latin='FF']){const changed=clone(bundle);change(changed);assert.notEqual((await F.snapshot(changed,webcrypto)).revision,view.revision);await assert.rejects(F.validatePlan(plan,changed,webcrypto));}
 const irrelevant=clone(bundle);irrelevant.pages.find(p=>p.id==='lp2-56').raw+=' ';irrelevant.pages[0].reviewed_text='Alternate reviewed transcription';assert.equal((await F.snapshot(irrelevant,webcrypto)).revision,view.revision);
 for(const change of [b=>b.schema='other',b=>b.extra=true,b=>b.pages.pop(),b=>b.pages[0].id=b.pages[1].id,b=>b.pages[0].raw=null,b=>b.pages[0].raw='\ud800',b=>b.pages.find(p=>p.id==='lp2-00').raw='',b=>b.alphabet[0].rune=b.alphabet[1].rune,b=>b.alphabet[0].extra=true,b=>b.pages[0].reviewed_text=12]){const changed=clone(bundle);change(changed);await assert.rejects(F.snapshot(changed,webcrypto));}
 assert.equal(E.stable(bundle),original);
 // Browser UMD parity, presentation independence and semantic-definition invalidation.
 const browserView=await browser().snapshot(bundle,webcrypto);assert.equal(E.stable(browserView),E.stable(view));
 assert.equal(E.stable(await browser().validateExecutionPlan(plan,webcrypto)),E.stable(plan));
 const relabelled=source.replace("TITLE='DEOR key: fixed Warning opening'","TITLE='A different display title'").replace("QUESTION='Does this four-rune key", "QUESTION='Could this four-rune key").replace("'Repeating key'","'A presentation label'");
 assert.notEqual(relabelled,source);assert.equal((await browser(relabelled).snapshot(bundle,webcrypto)).revision,view.revision);
 for(const altered of [source.replace('KEY=[23,18,3,4]','KEY=[23,12,3,4]'),source.replace('WARNING=[24,7,24','WARNING=[23,7,24'),source.replace("RESETS=['page','line','word']","RESETS=['page','line']"),source.replace("DIRECTIONS=['subtract','add']","DIRECTIONS=['subtract']")]){assert.notEqual(altered,source);assert.notEqual((await browser(altered).snapshot(bundle,webcrypto)).revision,view.revision);}
 console.log('PASS finite 990-case family, exact reviewed opening, canonical bounded plans, semantic revisions, tamper/input rejection, no preparation execution and browser parity');
})().catch(error=>{console.error(error);process.exitCode=1;});
