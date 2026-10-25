/* Fixed synthetic implementation checks. No target execution, network or generated code. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const REFERENCE_VERSION=1;
 const SCOPE='Two small synthetic inputs check the declared operations and result calculations against an independent reference. They do not test whether manuscript output is a solution. Finite-key limits can reduce the available control segments.';
 const encoder=new TextEncoder(),clone=value=>JSON.parse(JSON.stringify(value)),mod=n=>(n%29+29)%29;
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
 async function digest(value,cryptoAPI){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',encoder.encode(E.stable(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 function splitPositions(chars,alphabet,unit){
  const groups=[];let positions=[];
  for(let n=0;n<chars.length;n++){
   if(alphabet.includes(chars[n]))positions.push(n);
   else if(unit==='word'||unit==='line'&&(chars[n]==='\r'||chars[n]==='\n')){if(positions.length)groups.push(positions);positions=[];}
  }
  if(positions.length)groups.push(positions);return groups;
 }
 function referenceText(text,steps,alphabet){
  const names=alphabet.map(v=>v.rune),chars=Array.from(text);
  for(const step of steps){
   const unit=step.op==='reverse'?step.unit:step.op==='affine'?'page':step.reset;
   for(const positions of splitPositions(chars,names,unit)){
    const input=positions.map(i=>names.indexOf(chars[i]));let output=[];
    if(step.op==='reverse')output=[...input].reverse();
    else if(step.op==='affine')output=input.map(value=>mod(step.a*value+step.b));
    else if(step.op==='cumulative-difference'){
     let prior=0;for(const value of input){const decoded=mod(value-prior);output.push(decoded);prior=mod(prior+decoded);}
    }else if(step.op==='finite-shift')output=input.map((value,i)=>mod(value+(step.direction==='add'?step.key[i]:-step.key[i])));
    else if(step.op==='interrupted-keyed-shift'){
     let clock=0;for(const value of input){if(step.interrupts.includes(value))output.push(value);else{const amount=step.key[clock%step.key.length];output.push(mod(value+(step.direction==='add'?amount:-amount)));clock++;}}
    }else if(step.op==='keyed-shift'){
     for(let i=0;i<input.length;i++){
      const amount=step.mode==='repeat'?step.key[i%step.key.length]:i<step.key.length?step.key[i]:step.mode==='plaintext-autokey'?output[i-step.key.length]:input[i-step.key.length];
      output.push(mod(input[i]+(step.direction==='add'?amount:-amount)));
     }
    }else throw Error('The synthetic reference does not support this operation.');
    for(let i=0;i<positions.length;i++)chars[positions[i]]=names[output[i]];
   }
  }
  return chars.join('');
 }
 function words(text,names,boundaries){
  const result=[];let word=[];
  for(const ch of text){if(names.includes(ch))word.push(names.indexOf(ch));else if(boundaries==='non-rune'||ch==='-'||ch==='.'){if(word.length)result.push(word);word=[];}}
  if(word.length)result.push(word);return result;
 }
 function gcd(a,b){while(b){const r=a%b;a=b;b=r;}return a;}
 function rational(n,d){const factor=gcd(n,d);return [n/factor,d/factor];}
 function add(a,b){return rational(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);}
 const fraction=value=>({numerator:value[0].toString(),denominator:value[1].toString()});
 function referenceLanguage(values){
  // Share immutable reference tables only. This arithmetic deliberately does
  // not call the production scorer or copy its typed-array implementation.
  const data=(typeof module==='object'&&module.exports?require('./language-score.js'):root.RuneLanguageScore)?.data?.payload;
  if(!data)throw Error('The fixed rune-language tables could not be loaded for the independent checks.');
  const base={runes:values.length,windows:Math.max(0,values.length-2)};
  if(values.length<data.minimumRunes)return {...base,status:'insufficient',models:[]};
  const score=(sequence,table)=>{let amount=0;for(let offset=0;offset+2<sequence.length;offset++)amount+=table[841*sequence[offset]+29*sequence[offset+1]+sequence[offset+2]];return amount;};
  const totals=data.models.map(model=>score(values,model.scores)),samples=data.models.map(()=>[]),mask=0xffffffffn;
  for(let replicate=1;replicate<=32;replicate++){
   let state=Number((0x33010000n^(BigInt(values.length)*0x9e3779b1n&mask)^(BigInt(replicate)*0x85ebca6bn&mask))&mask)||1;
   const shuffled=Array.from(values);
   for(let cursor=shuffled.length-1;cursor>=1;cursor--){
    state=((state<<13)^state)>>>0;state=((state>>>17)^state)>>>0;state=((state<<5)^state)>>>0;
    const other=state%(cursor+1);[shuffled[cursor],shuffled[other]]=[shuffled[other],shuffled[cursor]];
   }
   data.models.forEach((model,i)=>samples[i].push(score(shuffled,model.scores)));
  }
  return {...base,status:'compared',models:data.models.map((model,i)=>({id:model.id,total:totals[i],shuffledMin:Math.min(...samples[i]),shuffledMax:Math.max(...samples[i]),shuffledAtOrAbove:samples[i].filter(amount=>amount>=totals[i]).length}))};
 }
 function referenceResult(task){
  const names=task.alphabet.map(v=>v.rune),counts=Array(29).fill(0),transformed=[],matches=[];
  let runeCount=0,pairCount=0,repeats=0,opportunities=0,affineMatches=0,expected=[0n,1n],sumWords=0,sumTotal=0;
  const pairPages=[],sumPages=[],languagePages=[],criterion=task.criterion;
  for(const page of task.pages){
   const text=referenceText(page.text,task.steps,task.alphabet),values=Array.from(text).filter(ch=>names.includes(ch)).map(ch=>names.indexOf(ch));
   for(let i=0;i<values.length;i++){counts[values[i]]++;runeCount++;if(i){pairCount++;if(values[i]===values[i-1])repeats++;}}
   transformed.push({page:page.id,text});
   if(criterion.kind==='exact-prefix')matches.push({page:page.id,matched:criterion.values.every((value,i)=>values[i]===value)});
   if(criterion.kind==='language-score')languagePages.push({page:page.id,...referenceLanguage(values)});
   if(criterion.kind==='word-affine-count'){
    let localOpportunities=0,localMatches=0,localExpected=[0n,1n];
    for(const word of words(text,names,criterion.boundaries)){
     const possible=Math.max(0,word.length-criterion.lag);localOpportunities+=possible;
     for(let i=0;i<possible;i++)if(word[i+criterion.lag]===mod(criterion.a*word[i]+criterion.b))localMatches++;
     if(possible){
      // Enumerate distinct labelled positions, independently of the engine's
      // frequency-product formula. Fixtures are deliberately small.
      let favourable=0;for(let i=0;i<word.length;i++)for(let j=0;j<word.length;j++)if(i!==j&&word[j]===mod(criterion.a*word[i]+criterion.b))favourable++;
      localExpected=add(localExpected,rational(BigInt(possible)*BigInt(favourable),BigInt(word.length)*BigInt(word.length-1)));
     }
    }
    opportunities+=localOpportunities;affineMatches+=localMatches;expected=add(expected,localExpected);
    pairPages.push({page:page.id,opportunities:localOpportunities,matches:localMatches,expected:fraction(localExpected)});
   }
   if(criterion.kind==='word-prime-sums'){
    const assignments=criterion.table==='reversed'?[...task.alphabet].reverse():task.alphabet;
    const groups=words(text,names,criterion.boundaries).map(word=>{const sum=word.reduce((total,value)=>total+assignments[value].prime,0);sumWords++;sumTotal+=sum;return {runes:word.map(value=>names[value]).join(''),sum};});
    sumPages.push({page:page.id,words:groups});
   }
  }
  const result={schema:E.RESULT,taskId:task.taskId,engine:E.ENGINE,runnerVersion:'1',metrics:{pages:task.pages.length,runes:runeCount,adjacentPairs:pairCount,equalAdjacentPairs:repeats,ioc:runeCount>1?counts.reduce((sum,n)=>sum+n*(n-1),0)/(runeCount*(runeCount-1)):0},matches,transformed};
  if(criterion.kind==='word-affine-count')result.wordPairs={opportunities,matches:affineMatches,expected:fraction(expected),pages:pairPages};
  if(criterion.kind==='word-prime-sums')result.wordSums={words:sumWords,total:sumTotal,pages:sumPages};
  if(criterion.kind==='language-score')result.languageScore={modelId:criterion.modelId,modelSha256:criterion.modelSha256,pages:languagePages};
  return result;
 }
 function fixtureText(target,reverse,pageIndex){
  const finite=target.steps.filter(step=>step.op==='finite-shift'),positions=finite.map(()=>0);
  // Reach a repeating/autokey seed boundary when finite keys permit it.
  const longest=Math.max(12,target.criterion.kind==='language-score'?45:0,target.criterion.kind==='word-affine-count'?target.criterion.lag+3:0,...target.steps.filter(s=>s.op==='keyed-shift'||s.op==='interrupted-keyed-shift').map(s=>s.key.length+3));
  const values=Array.from({length:longest},(_,i)=>mod((reverse?28-i:i)*7+pageIndex*11));
  const chunks=[values,[0,0,28,1],[27,4,16,0],[1,28,0,3],[8,8,9]];
  const separators=[' /💡\r\n','-','.\r','\n'];let source='';
  for(let k=0;k<chunks.length;k++){source+=chunks[k].map(i=>target.alphabet[i].rune).join('');if(k<separators.length)source+=separators[k];}
  if(target.criterion.kind==='word-affine-count'&&!target.steps.length){
   // One declared match and one declared mismatch exercise the counting
   // kernel even at lag 12. No transformed program is claimed to preserve them.
   const rule=target.criterion,match=Array.from({length:rule.lag+1},(_,i)=>mod(i*5+pageIndex));
   match[0]=0;match[rule.lag]=rule.b;
   const mismatch=[...match];mismatch[rule.lag]=mod(rule.b+1);
   const encode=word=>word.map(i=>target.alphabet[i].rune).join('');
   source=encode(match)+'-'+encode(mismatch)+'-'+source;
  }
  let out='';
  for(const ch of source){
   if(target.alphabet.some(entry=>entry.rune===ch)){
    if(finite.some((step,i)=>positions[i]>=step.key.length))continue;
    for(let i=0;i<positions.length;i++)positions[i]++;out+=ch;
   }else{
    out+=ch;for(let i=0;i<finite.length;i++)if(finite[i].reset==='word'||finite[i].reset==='line'&&(ch==='\r'||ch==='\n'))positions[i]=0;
   }
  }
  return out;
 }
 async function prepare(target,cryptoAPI=root.crypto){
  E.validateTask(target);const snapshot=clone(target);await E.checkIdentity(snapshot,cryptoAPI);
  const cases=[];
  for(const [caseIndex,id]of ['layout-forward','layout-reversed'].entries()){
   const pages=[0,1].map(n=>({id:'lp1-0'+n,text:fixtureText(snapshot,caseIndex===1,n)}));
   const body={title:'Synthetic local reference '+REFERENCE_VERSION+': '+id+' for '+snapshot.taskId,pages,alphabet:snapshot.alphabet,steps:snapshot.steps,criterion:snapshot.criterion};
   if(snapshot.criterion.kind==='exact-prefix'){
    const output=referenceText(pages[0].text,snapshot.steps,snapshot.alphabet),names=snapshot.alphabet.map(v=>v.rune);
    const values=Array.from(output).filter(ch=>names.includes(ch)).map(ch=>names.indexOf(ch)).slice(0,256);
    if(!values.length)throw Error('The synthetic prefix control needs at least one rune.');
    if(caseIndex===1)values[0]=mod(values[0]+1);
    body.criterion={kind:'exact-prefix',values};
   }
   const task=await E.prepare(body,cryptoAPI),expected=referenceResult(task),actual=E.run(task);
   if(E.stable(actual)!==E.stable(expected))throw Error('The local runner disagrees with the independent synthetic reference.');
   if(snapshot.criterion.kind==='exact-prefix'&&expected.matches[0].matched!==(caseIndex===0))throw Error('The synthetic prefix control lost its declared positive or negative result.');
   cases.push({id,task,expectedResultSha256:await digest(expected,cryptoAPI)});
  }
  return {version:1,targetId:snapshot.taskId,cases};
 }
 async function validate(suite,target,cryptoAPI=root.crypto){
  if(!exact(suite,['version','targetId','cases'])||suite.version!==1||suite.targetId!==target?.taskId||!Array.isArray(suite.cases)||suite.cases.length!==2||suite.cases.some(c=>!exact(c,['id','task','expectedResultSha256'])))throw Error('The synthetic control suite is malformed or belongs to another task.');
  for(const item of suite.cases)E.validateTask(item.task);
  const snapshot=clone(suite),expected=await prepare(target,cryptoAPI);
  if(E.stable(snapshot)!==E.stable(expected))throw Error('The synthetic control suite differs from this exact plan.');
  return expected;
 }
 const api={REFERENCE_VERSION,SCOPE,prepare,validate};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalPlanControls=api;
})(typeof globalThis!=='undefined'?globalThis:this);
