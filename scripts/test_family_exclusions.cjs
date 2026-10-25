'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{webcrypto}=require('node:crypto');
const F=require('../research-family.js'),L=require('../local-experiment.js'),clone=v=>JSON.parse(JSON.stringify(v));
const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')),alphabet=bundle.alphabet,key=[23,18,3,4];
const criterion=JSON.parse(fs.readFileSync('experiments/records/lp2-known-vigenere-keys/record.json','utf8')).browser_followups[0].card.rules.evaluation.value;
const mod=n=>(n%29+29)%29;
function task(config,page){return L.prepare({title:'Synthetic exclusion verification',pages:[page],alphabet,steps:[{op:'keyed-shift',key,mode:config.mode,direction:config.direction,reset:config.reset}],criterion},webcrypto);}
function plant(config){
 const plain=criterion.values.map((v,i)=>alphabet[v].rune+(i===2?'-':i===6?'\n':'')).join('');let p=[],c=[],output='&\n/-';
 for(const ch of plain){
  const value=alphabet.findIndex(entry=>entry.rune===ch);
  if(value<0){output+=ch;if(config.reset==='word'||config.reset==='line'&&/[\r\n]/.test(ch)){p=[];c=[];}continue;}
  const n=p.length,k=n<key.length?key[n]:config.mode==='repeat'?key[n%key.length]:config.mode==='plaintext-autokey'?p[n-key.length]:c[n-key.length];
  const encoded=mod(value+(config.direction==='subtract'?k:-k));p.push(value);c.push(encoded);output+=alphabet[encoded].rune;
 }
 return output;
}
(async()=>{
 const view=await F.snapshot(bundle,webcrypto),before=L.stable(view),oldRun=L.run;let proof;
 L.run=()=>{throw Error('Exclusion proof cannot decode targets.');};try{proof=F.proveCaseExclusions(view,alphabet);}finally{L.run=oldRun;}
 assert.equal(proof.excluded.length,963);assert.equal(proof.eligible.length,27);assert.equal(new Set([...proof.excluded.map(e=>e.caseId),...proof.eligible]).size,990);assert.equal(L.stable(view),before);assert.deepEqual(proof.excluded.map(e=>e.caseId),proof.excluded.map(e=>e.caseId).slice().sort());
 for(const item of proof.excluded){assert.equal(item.rule,'first-rune');assert.equal(item.keyIndex,23);assert.equal(item.expectedIndex,24);assert.notEqual(item.actualIndex,item.expectedIndex);}
 const excluded=new Set(proof.excluded.map(e=>e.caseId));let checks=0;
 for(const config of view.configurations)for(const page of view.pages){const result=oldRun(await task(config,page));if(result.matches[0].matched)assert(!excluded.has(config.id+'--'+page.id));checks++;}
 // Exhaust every possible first input rune against the independent decoder,
 // including leading separators and every reset/history/direction combination.
 for(let value=0;value<29;value++){
  const synthetic=clone(view);synthetic.pages[0].text='&\n/-'+alphabet[value].rune+'-ᚠᚢ\nᚦᚩᚱᚳᚷᚹᚻᚾᛁ';const measured=F.proveCaseExclusions(synthetic,alphabet),rejects=new Map(measured.excluded.map(e=>[e.caseId,e]));
  for(const config of synthetic.configurations){
   const id=config.id+'--'+synthetic.pages[0].id,result=oldRun(await task(config,synthetic.pages[0])),first=Array.from(result.transformed[0].text).find(ch=>alphabet.some(a=>a.rune===ch)),actual=alphabet.findIndex(a=>a.rune===first),rejection=rejects.get(id);
   assert.equal(Boolean(rejection),actual!==criterion.values[0]);if(rejection)assert.equal(rejection.actualIndex,actual);if(result.matches[0].matched)assert(!rejection);checks++;
  }
 }
 // Known complete openings are planted separately for every family setting.
 // Test all settings on each fixture so exclusions also face true positives.
 let matches=0;
 for(const plantedConfig of view.configurations){
  const synthetic=clone(view);synthetic.pages[0].text=plant(plantedConfig);const rejected=new Set(F.proveCaseExclusions(synthetic,alphabet).excluded.map(e=>e.caseId));
  assert.equal(oldRun(await task(plantedConfig,synthetic.pages[0])).matches[0].matched,true);
  for(const config of synthetic.configurations){const result=oldRun(await task(config,synthetic.pages[0]));if(result.matches[0].matched){matches++;assert(!rejected.has(config.id+'--'+synthetic.pages[0].id));}checks++;}
 }
 assert(matches>=18);
 for(const change of [v=>v.id='other',v=>v.revision='bad',v=>v.totalCases=991,v=>v.configurations.pop(),v=>v.configurations[0].direction='other',v=>v.configurations[0].id=v.configurations[1].id,v=>v.pages.pop(),v=>v.pages[0].id=v.pages[1].id,v=>v.pages[0].text='&-/\n']){const changed=clone(view);change(changed);assert.throws(()=>F.proveCaseExclusions(changed,alphabet));}
 assert.throws(()=>F.proveCaseExclusions(view,alphabet.slice(1)));
 console.log('PASS first-rune proof: actual963 excluded/27 eligible; '+checks+' independent target checks, all29 first values and '+matches+' planted matching openings; no decoding during proof');
})().catch(error=>{console.error(error);process.exitCode=1;});
