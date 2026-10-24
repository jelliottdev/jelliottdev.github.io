/* Declarative local experiments. No generated code, I/O, inference or execution of source text. */
(function(root){
 'use strict';
 const TASK='liberpedia-local-task-v1',RESULT='liberpedia-local-result-v1',ENGINE='rune-program-v1';
 const verifiedResults=new WeakMap();
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const length=s=>Array.from(s).length;
 function scalarText(s){return typeof s==='string'&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(s);}
 function object(value,keys){
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!keys.includes(k)))throw Error('Unexpected experiment fields.');
  if(keys.some(k=>!own(value,k)))throw Error('Missing experiment fields.');
 }
 function integer(v,min,max){if(!Number.isInteger(v)||v<min||v>max)throw Error('Experiment number is outside its bounds.');}
 function stable(value){
  if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
  if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
  return JSON.stringify(value);
 }
 function validateTask(task){
  object(task,['schema','engine','taskId','title','pages','alphabet','steps','criterion']);
  if(task.schema!==TASK||task.engine!==ENGINE||!/^[a-f0-9]{64}$/.test(task.taskId))throw Error('Unsupported experiment version or identity.');
  if(!scalarText(task.title)||!task.title.trim()||length(task.title)>300)throw Error('Give the experiment a short title.');
  if(!Array.isArray(task.alphabet)||task.alphabet.length!==29)throw Error('The task needs an ordered 29-rune alphabet.');
  const runes=new Set();
  for(const entry of task.alphabet){
   object(entry,['rune','latin','prime']);
   if(!scalarText(entry.rune)||length(entry.rune)!==1||/\s/.test(entry.rune)||runes.has(entry.rune))throw Error('Alphabet runes must be distinct characters.');
   runes.add(entry.rune);
   if(!scalarText(entry.latin)||!entry.latin||length(entry.latin)>8)throw Error('Invalid rune label.');
   integer(entry.prime,2,1000000);
  }
  if(!Array.isArray(task.pages)||!task.pages.length||task.pages.length>75)throw Error('Select between one and 75 pages.');
  const ids=new Set();let count=0,total=0;
  for(const page of task.pages){
   object(page,['id','text']);
   if(typeof page.id!=='string'||!/^lp[12]-\d{2}$/.test(page.id)||ids.has(page.id)||Number(page.id.slice(4))>(page.id[2]==='1'?16:57))throw Error('Invalid or repeated manuscript page.');
   ids.add(page.id);
   if(!scalarText(page.text))throw Error('Missing page text.');
   total+=length(page.text);
   for(const ch of page.text)if(runes.has(ch))count++;
  }
  if(count>20000||total>300000)throw Error('The task exceeds the local runner bounds.');
  if(!Array.isArray(task.steps)||task.steps.length>8)throw Error('Use at most eight method steps.');
  for(const step of task.steps){
   if(step?.op==='reverse'){object(step,['op','unit']);if(!['line','word','page'].includes(step.unit))throw Error('Choose a reversal boundary.');}
   else if(step?.op==='affine'){object(step,['op','a','b']);integer(step.a,0,28);integer(step.b,0,28);}
   else if(step?.op==='cumulative-difference'){object(step,['op','reset']);if(!['page','line','word'].includes(step.reset))throw Error('Choose a feedback reset.');}
   else if(step?.op==='keyed-shift'){
    object(step,['op','key','mode','direction','reset']);
    if(!Array.isArray(step.key)||!step.key.length||step.key.length>256)throw Error('Give one to 256 key indices.');
    for(const value of step.key)integer(value,0,28);
    if(!['repeat','plaintext-autokey','ciphertext-autokey'].includes(step.mode)||!['subtract','add'].includes(step.direction)||!['page','line','word'].includes(step.reset))throw Error('Choose the key mode, arithmetic direction and reset.');
   }
   else throw Error('This method needs an execution adapter before it can run.');
  }
  if(task.criterion?.kind==='measurement')object(task.criterion,['kind']);
  else if(task.criterion?.kind==='exact-prefix'){
   object(task.criterion,['kind','values']);
   if(!Array.isArray(task.criterion.values)||!task.criterion.values.length||task.criterion.values.length>256)throw Error('Give a prefix of one to 256 rune indices.');
   task.criterion.values.forEach(v=>integer(v,0,28));
  }else throw Error('Choose a supported result criterion.');
  if(new TextEncoder().encode(stable(task)).length>2000000)throw Error('The task exceeds the local runner file limit.');
  return task;
 }
 async function identity(task,cryptoAPI=root.crypto){
  const body={...task};delete body.taskId;
  const hash=await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(stable(body)));
  return [...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');
 }
 async function prepare(body,cryptoAPI=root.crypto){
  const task=JSON.parse(JSON.stringify({...body,schema:TASK,engine:ENGINE,taskId:'0'.repeat(64)}));
  validateTask(task);task.taskId=await identity(task,cryptoAPI);return task;
 }
 async function checkIdentity(task,cryptoAPI=root.crypto){validateTask(task);if(await identity(task,cryptoAPI)!==task.taskId)throw Error('The experiment changed after it was prepared.');return task;}
 function transform(text,steps,alphabet){
  const index=new Map(alphabet.map((r,i)=>[r.rune,i])),mod=n=>(n%29+29)%29;
  let chars=Array.from(text);
  for(const step of steps){
   if(step.op==='reverse'){
    let positions=[];
    const flush=()=>{const values=positions.map(i=>chars[i]).reverse();positions.forEach((i,n)=>{chars[i]=values[n];});positions=[];};
    for(let i=0;i<chars.length;i++){
     if(index.has(chars[i]))positions.push(i);
     else if(step.unit==='word'||step.unit==='line'&&/[\r\n]/.test(chars[i]))flush();
    }flush();
   }else if(step.op==='affine')chars=chars.map(ch=>index.has(ch)?alphabet[mod(step.a*index.get(ch)+step.b)].rune:ch);
   else if(step.op==='cumulative-difference'){
    let sum=0;
    chars=chars.map(ch=>{
     if(!index.has(ch)){if(step.reset==='word'||step.reset==='line'&&/[\r\n]/.test(ch))sum=0;return ch;}
     const p=mod(index.get(ch)-sum);sum=mod(sum+p);return alphabet[p].rune;
    });
   }else if(step.op==='keyed-shift'){
    let input=[],output=[];
    chars=chars.map(ch=>{
     if(!index.has(ch)){if(step.reset==='word'||step.reset==='line'&&/[\r\n]/.test(ch)){input=[];output=[];}return ch;}
     const c=index.get(ch),j=input.length,m=step.key.length;
     const k=j<m?step.key[j]:step.mode==='repeat'?step.key[j%m]:step.mode==='plaintext-autokey'?output[j-m]:input[j-m];
     const p=mod(c+(step.direction==='add'?k:-k));input.push(c);output.push(p);return alphabet[p].rune;
    });
   }
  }
  return chars.join('');
 }
 function run(task,{onProgress}={}){
  validateTask(task);
  const index=new Map(task.alphabet.map((r,i)=>[r.rune,i])),frequencies=Array(29).fill(0);
  let runes=0,adjacentPairs=0,equalAdjacentPairs=0;const transformed=[],matches=[];
  for(const page of task.pages){
   const text=transform(page.text,task.steps,task.alphabet),values=Array.from(text).filter(ch=>index.has(ch)).map(ch=>index.get(ch));
   values.forEach(v=>frequencies[v]++);runes+=values.length;adjacentPairs+=Math.max(0,values.length-1);
   for(let i=1;i<values.length;i++)if(values[i]===values[i-1])equalAdjacentPairs++;
   transformed.push({page:page.id,text});
   if(task.criterion.kind==='exact-prefix')matches.push({page:page.id,matched:task.criterion.values.every((v,i)=>values[i]===v)});
   if(onProgress)onProgress({phase:'running',completed:transformed.length,total:task.pages.length});
  }
  return {schema:RESULT,taskId:task.taskId,engine:ENGINE,runnerVersion:'1',
   metrics:{pages:task.pages.length,runes,adjacentPairs,equalAdjacentPairs,ioc:runes>1?frequencies.reduce((s,n)=>s+n*(n-1),0)/(runes*(runes-1)):0},matches,transformed};
 }
 function sameResult(actual,expected){
  if(typeof actual!==typeof expected||actual===null||expected===null)return actual===expected;
  if(typeof expected==='number')return Number.isFinite(actual)&&(Number.isInteger(expected)?actual===expected:Math.abs(actual-expected)<=1e-12);
  if(Array.isArray(expected))return Array.isArray(actual)&&actual.length===expected.length&&expected.every((v,i)=>sameResult(actual[i],v));
  if(typeof expected==='object')return !Array.isArray(actual)&&Object.keys(actual).length===Object.keys(expected).length&&Object.keys(expected).every(k=>own(actual,k)&&sameResult(actual[k],expected[k]));
  return actual===expected;
 }
 async function verify(task,result,cryptoAPI=root.crypto){
  await checkIdentity(task,cryptoAPI);
  const expected=run(task);
  if(!sameResult(result,expected))throw Error('The returned results do not match this exact experiment.');
  verifiedResults.set(expected,stable(task));
  return expected;
 }
 function summary(task,result){
  validateTask(task);
  if(!result||verifiedResults.get(result)!==stable(task)||!sameResult(result,run(task)))throw Error('Results must be verified before display.');
  const baseline=run({...task,steps:[],criterion:{kind:'measurement'}}).metrics;
  const matched=result.matches.filter(v=>v.matched).length;
  return {finding:task.criterion.kind==='measurement'
   ?(baseline.equalAdjacentPairs===result.metrics.equalAdjacentPairs
    ?'The method left neighbouring rune repeats unchanged: '+result.metrics.equalAdjacentPairs+' across '+result.metrics.adjacentPairs.toLocaleString('en-US')+' pairs.'
    :'The method changed neighbouring rune repeats from '+baseline.equalAdjacentPairs+' to '+result.metrics.equalAdjacentPairs+' across '+result.metrics.adjacentPairs.toLocaleString('en-US')+' pairs.')
   :matched+' of '+result.metrics.pages+' pages begin with the exact rune sequence specified before the run. A prefix match alone does not establish a decryption.',
   comparison:[{label:'Original text',value:baseline.equalAdjacentPairs,total:baseline.adjacentPairs},
    {label:'After the method',value:result.metrics.equalAdjacentPairs,total:result.metrics.adjacentPairs}],
   limit:task.criterion.kind==='measurement'?'This run measures repeat patterns. It does not test readability or identify a cipher.':'The result covers only the specified starting sequence, pages and method.'};
 }
 const api={TASK,RESULT,ENGINE,stable,validateTask,identity,prepare,checkIdentity,run,verify,summary};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalExperiment=api;
})(typeof globalThis!=='undefined'?globalThis:this);
