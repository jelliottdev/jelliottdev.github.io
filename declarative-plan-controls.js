/* Independent synthetic implementation checks for declarative rune programs.
 * Expected transformations never call either production runner. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,V=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram,J=node?require('./finite-json.js'):root.FiniteJSON;
 const REFERENCE_VERSION=2,SCOPE='Three invented fixtures compare the declared operations, retained input slots and result arithmetic with an independent reference. They do not test manuscript readings or scientific significance. Short finite keys can restrict which synthetic patterns fit.';
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k)),ensure=(ok,message)=>{if(!ok)throw Error(message);},mod=v=>(v%29+29)%29;
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const capture=v=>J.capture(v,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:500000});
 async function hash(value,crypto){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(stable(value)))),v=>v.toString(16).padStart(2,'0')).join('');}
 function groups(tokens,names,unit){
  const result=[];let current=[];
  for(let position=0;position<tokens.length;position++){
   if(names.includes(tokens[position].ch))current.push(position);
   else if(unit==='word'||unit==='line'&&['\r','\n'].includes(tokens[position].ch)){result.push(current);current=[];}
  }
  result.push(current);return result;
 }
 function referenceTransform(text,steps,names){
  let tokens=Array.from(text,(ch,inputIndex)=>({ch,inputIndex}));const removed=[];
  for(let stepIndex=0;stepIndex<steps.length;stepIndex++){
   const step=steps[stepIndex],drop=new Set();
   if(step.op==='remove-rune-types'){
    tokens.forEach((token,i)=>{if(step.values.includes(names.indexOf(token.ch)))drop.add(i);});
   }else if(step.op==='collapse-adjacent-repeats'){
    for(const positions of groups(tokens,names,step.unit)){
     for(let begin=0;begin<positions.length;){let end=begin+1;while(end<positions.length&&tokens[positions[end]].ch===tokens[positions[begin]].ch)end++;
      for(let n=begin+1;n<end;n++)if(step.policy==='all-but-first'||(n-begin)%2===1)drop.add(positions[n]);begin=end;
     }
    }
   }else {
    const unit=step.op==='reverse'?step.unit:step.op==='affine'?'page':step.reset;
    for(const positions of groups(tokens,names,unit)){
     const input=positions.map(p=>names.indexOf(tokens[p].ch));let output=[];
     if(step.op==='reverse')output=input.slice().reverse();
     else if(step.op==='affine')output=input.map(v=>mod(step.a*v+step.b));
     else if(step.op==='cumulative-difference'){let prior=0;for(const value of input){output.push(mod(value-prior));prior=value;}}
     else if(step.op==='finite-shift'){
      if(input.length>step.key.length){const error=Error('Synthetic finite segment is too long.');error.finite=true;throw error;}
      output=input.map((v,i)=>mod(v+(step.direction==='add'?step.key[i]:-step.key[i])));
     }else if(step.op==='interrupted-keyed-shift'){
      let clock=0;for(const value of input){if(step.interrupts.includes(value))output.push(value);else{output.push(mod(value+(step.direction==='add'?step.key[clock%step.key.length]:-step.key[clock%step.key.length])));clock++;}}
     }else if(step.op==='keyed-shift'){
      for(let i=0;i<input.length;i++){const amount=step.mode==='repeat'?step.key[i%step.key.length]:i<step.key.length?step.key[i]:step.mode==='plaintext-autokey'?output[i-step.key.length]:input[i-step.key.length];output.push(mod(input[i]+(step.direction==='add'?amount:-amount)));}
     }else throw Error('The independent reference does not support this operation.');
     positions.forEach((position,i)=>{tokens[position]={...tokens[position],ch:names[output[i]]};});
    }
   }
   for(let i=0;i<tokens.length;i++)if(drop.has(i))removed.push({inputIndex:tokens[i].inputIndex,stepIndex,value:names.indexOf(tokens[i].ch)});
   tokens=tokens.filter((_,i)=>!drop.has(i));
  }
  return {text:tokens.map(t=>t.ch).join(''),inputLength:Array.from(text).length,outputToInput:tokens.map(t=>t.inputIndex),removed};
 }
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
  const names=task.alphabet.map(x=>x.rune),histogram=Array(29).fill(0),transformed=[],matches=[],traces=[],languagePages=[];let runes=0,pairs=0,equal=0;
  for(const page of task.pages){
   const output=referenceTransform(page.text,task.steps,names),values=Array.from(output.text).filter(ch=>names.includes(ch)).map(ch=>names.indexOf(ch));
   values.forEach((v,i)=>{histogram[v]++;runes++;if(i){pairs++;if(values[i-1]===v)equal++;}});
   const {text,...alignment}=output;transformed.push({page:page.id,text});traces.push({page:page.id,...alignment});
   if(task.criterion.kind==='exact-prefix')matches.push({page:page.id,matched:task.criterion.values.every((v,i)=>values[i]===v)});
   if(task.criterion.kind==='exact-prefix-set'){const matchingOpenings=task.criterion.openings.filter(o=>o.values.every((v,i)=>values[i]===v)).map(o=>o.id);matches.push({page:page.id,matched:matchingOpenings.length>0,matchingOpenings});}
   if(task.criterion.kind==='language-score')languagePages.push({page:page.id,...referenceLanguage(values)});
  }
  return {schema:V.RESULT,engine:V.ENGINE,runnerVersion:V.RUNNER_VERSION,taskId:task.taskId,metrics:{pages:task.pages.length,runes,adjacentPairs:pairs,equalAdjacentPairs:equal,ioc:runes>1?histogram.reduce((sum,n)=>sum+n*(n-1),0)/(runes*(runes-1)):0},matches,transformed,alignment:{kind:'retained-input-slots-v1',pages:traces},...(task.criterion.kind==='language-score'?{languageScore:{modelId:task.criterion.modelId,modelSha256:task.criterion.modelSha256,pages:languagePages}}:{})};
 }
 function fixtureText(target,reverse,page){
  const names=target.alphabet.map(v=>v.rune),size=Math.min(260,Math.max(45,...target.steps.filter(s=>s.op==='keyed-shift'||s.op==='interrupted-keyed-shift').map(s=>s.key.length+3))),encode=values=>values.map(v=>names[v]).join('');
  const punctuation=['/','-','.','🧩'].filter(ch=>!names.includes(ch)).join(''),base=encode(Array.from({length:size},(_,i)=>mod((reverse?28-i:i)*7+page*11)))+' '+punctuation+'\r\n'+encode([0,0,0,1,1,1,1,28])+'-'+encode([2,2,3,3])+'\r'+encode([4,4,4])+'\n'+encode([5,5]);
  let input=Array.from(base);
  // Fit the actual independently transformed finite-key stage, rather than
  // assuming that original and filtered rune counts are equal.
  for(let tries=0;tries<=512;tries++){
   try{referenceTransform(input.join(''),target.steps,names);return input.join('');}
   catch(error){if(!error.finite)throw error;let last=input.length-1;while(last>=0&&!names.includes(input[last]))last--;if(last<0)throw error;input.splice(last,1);}
  }
  throw Error('The synthetic finite-key fixture exceeds its preparation bound.');
 }
 async function prepare(input,crypto=root.crypto){
  const target=V.validateTask(input);await V.checkIdentity(target,crypto);const targetHash=await hash(target,crypto),cases=[];
  for(let index=0;index<3;index++){
   const id=['layout-forward','layout-reversed','empty-separators'][index],names=target.alphabet.map(x=>x.rune),pages=[0,1].map(page=>({id:'lp1-0'+page,text:index===2?(page?'':' \r\n\t'):fixtureText(target,index===1,page)}));
   let criterion=target.criterion;
   if(index<2&&['exact-prefix','exact-prefix-set'].includes(criterion.kind)){
    const values=Array.from(referenceTransform(pages[0].text,target.steps,names).text).filter(ch=>names.includes(ch)).map(ch=>names.indexOf(ch)).slice(0,12);
    if(values.length){const first=values.slice(),second=values.slice();first[0]=mod(first[0]+index);second[0]=mod(second[0]+index+1);criterion=criterion.kind==='exact-prefix'?{kind:'exact-prefix',values:first}:{kind:'exact-prefix-set',openings:[{id:'first-opening',values:first},{id:'second-opening',values:second}]};}
   }
   const task=await V.prepare({title:'Synthetic declarative reference 2: '+id+' for '+target.taskId,alphabet:target.alphabet,pages,steps:target.steps,criterion},crypto),expected=referenceResult(task),actual=V.run(task);
   ensure(stable(actual)===stable(expected),'The declarative runner disagrees with the independent synthetic reference.');cases.push({id,task,expectedResultSha256:await hash(expected,crypto)});
  }
  ensure(stable(target)===stable(capture(input)),'The target changed during synthetic preparation.');return freeze({version:2,targetId:target.taskId,targetHash,cases});
 }
 async function validate(input,target,crypto=root.crypto){
  const capturedTarget=V.validateTask(target),suite=capture(input);ensure(exact(suite,['version','targetId','targetHash','cases'])&&suite.version===2&&suite.targetId===capturedTarget.taskId&&typeof suite.targetHash==='string'&&/^[a-f0-9]{64}$/.test(suite.targetHash)&&Array.isArray(suite.cases)&&suite.cases.length===3&&suite.cases.every(c=>exact(c,['id','task','expectedResultSha256'])),'Use an exact version-two synthetic suite.');
  const expected=await prepare(capturedTarget,crypto);ensure(stable(capturedTarget)===stable(capture(target)),'The target changed during control validation.');ensure(stable(suite)===stable(expected),'The control suite differs from this exact declared program.');ensure(stable(suite)===stable(capture(input)),'The control suite changed during validation.');return expected;
 }
 const api=Object.freeze({REFERENCE_VERSION,SCOPE,prepare,validate});if(node)module.exports=api;else root.DeclarativePlanControls=api;
})(typeof globalThis!=='undefined'?globalThis:this);
