/* Independent inverse template plus offline commitments. Never generates an
 * expected result with the decoder, admits tasks, or evaluates manuscript text. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,E=node?require('./local-experiment.js'):root.LocalExperiment,M=node?require('./pinned-domain-members.js'):root.PinnedDomainMembers;
 const manifests=new WeakMap(),proofs=new WeakMap(),HEX=/^[a-f0-9]{64}$/,TEMPLATE='liberpedia-warning-template-v1',SCHEMA='liberpedia-pinned-control-commitments-v1',TEXT='0a7853f7058b8dc008cb4b9a11e898ca6824536786c317bbab6f9cabf8427c44',VALUES='e52befa494d00d54874384ca55fc696c6e9b911d2659f8054f7b7aa73502d68e',ALPHABET='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f';
 const need=(v,m)=>{if(!v)throw Error(m);},exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k)),capture=v=>J.capture(v,{maxBytes:2*1024*1024,maxDepth:24,maxNodes:100000}),copy=v=>capture(v),same=(a,b)=>E.stable(a)===E.stable(b),pin=v=>typeof v==='string'&&v.length===64&&HEX.test(v),freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 async function hash(v,crypto,raw=false){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',v instanceof Uint8Array?v:new TextEncoder().encode(raw?v:E.stable(v))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function sourcePins(values){need(Array.isArray(values)&&values.length>0&&values.length<=1024,'Use bounded independent source pins.');const seen=new Set();for(const value of values){need(exact(value,['path','sha256'])&&typeof value.path==='string'&&value.path.length<=350&&!/[^a-zA-Z0-9_./-]/.test(value.path)&&value.path.split('/').every(part=>part&&part!=='.'&&part!=='..')&&pin(value.sha256)&&!seen.has(value.path),'Invalid independent source pin.');seen.add(value.path);}}
 function inverse(text,steps,alphabet){
  const runes=alphabet.map(a=>a.rune),index=new Map(runes.map((r,i)=>[r,i])),mod=n=>(n%29+29)%29;let output=Array.from(text);
  for(const step of steps.slice().reverse()){
   const desired=output.slice();
   if(step.op==='reverse'){
    let positions=[];const flush=()=>{const values=positions.map(i=>desired[i]).reverse();positions.forEach((p,i)=>{output[p]=values[i];});positions=[];};
    for(let i=0;i<desired.length;i++)if(index.has(desired[i]))positions.push(i);else if(step.unit==='word'||step.unit==='line'&&/[\r\n]/.test(desired[i]))flush();flush();
   }else if(step.op==='affine'){
    let inv=0;for(let n=1;n<29;n++)if(n*step.a%29===1){inv=n;break;}need(inv,'A noninvertible affine step cannot encode the full Warning control.');output=desired.map(ch=>index.has(ch)?runes[mod((index.get(ch)-step.b)*inv)]:ch);
   }else{
    let ciphertext=[],known=[],cumulative=0;
    for(let i=0;i<desired.length;i++){
     const ch=desired[i];if(!index.has(ch)){if(step.reset==='word'||step.reset==='line'&&/[\r\n]/.test(ch)){ciphertext=[];known=[];cumulative=0;}continue;}
     const value=index.get(ch);let encoded;
     if(step.op==='cumulative-difference'){cumulative=mod(cumulative+value);encoded=cumulative;}
     else if(step.op==='finite-shift'){need(ciphertext.length<step.key.length,'The full Warning control exceeds this finite stream.');encoded=mod(value+(step.direction==='subtract'?step.key[ciphertext.length]:-step.key[ciphertext.length]));}
     else if(step.op==='interrupted-keyed-shift'){
      if(step.interrupts.includes(value)){output[i]=ch;continue;}const amount=step.key[ciphertext.length%step.key.length];encoded=mod(value+(step.direction==='subtract'?amount:-amount));need(!step.interrupts.includes(encoded),'The full Warning cannot be independently encoded with this interrupted setting.');
     }else{
      need(step.op==='keyed-shift','This ordered step needs an independent inverse template.');const position=ciphertext.length,amount=step.mode==='repeat'?step.key[position%step.key.length]:position<step.key.length?step.key[position]:(step.mode==='plaintext-autokey'?known:ciphertext)[position-step.key.length];need(Number.isInteger(amount),'The independent autokey history is incomplete.');encoded=mod(value+(step.direction==='subtract'?amount:-amount));
     }
     output[i]=runes[encoded];ciphertext.push(encoded);known.push(value);
    }
   }
  }
  return output.join('');
 }
 async function read(raw,options){
  need(raw instanceof Uint8Array&&raw.byteLength<=2*1024*1024,'Use bounded exact commitment bytes.');
  need(options&&typeof options==='object'&&!Array.isArray(options)&&Reflect.ownKeys(options).every(k=>['sha256','parent','template','crypto'].includes(k))&&['sha256','parent','template'].every(k=>Object.hasOwn(options,k))&&Object.values(Object.getOwnPropertyDescriptors(options)).every(d=>Object.hasOwn(d,'value')&&d.enumerable),'Use exact independent source descriptors.');
  const bytes=new Uint8Array(raw),{sha256,parent,template,crypto=root.crypto}=options,declared=M.inspect(parent),basis=capture(template),unchanged=()=>need(same(capture(template),basis),'The independent template changed during loading.');
  need(pin(sha256)&&await hash(bytes,crypto)===sha256,'The independently committed control source changed.');
  const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes),data=capture(JSON.parse(text));need(text===E.stable(data)||text===E.stable(data)+'\n','Use canonical unique-key commitment JSON.');
  need(exact(data,['schema','parentDomainId','templateSha256','encoder','sourcePins','entries'])&&data.schema===SCHEMA&&data.parentDomainId===declared.plan.domainId&&data.encoder==='warning-inverse-v1'&&pin(data.templateSha256),'The control commitments belong to a different parent or encoder.');
  sourcePins(data.sourcePins);sourcePins(basis.sourcePins);
  need(exact(basis,['schema','alphabetSha256','plaintext','values','sourcePins'])&&basis.schema===TEMPLATE&&basis.alphabetSha256===ALPHABET&&typeof basis.plaintext==='string'&&!/[\ud800-\udfff]/u.test(basis.plaintext)&&Array.isArray(basis.values)&&basis.values.length===184&&basis.values.every(v=>Number.isInteger(v)&&v>=0&&v<29),'Use the complete independently documented Warning template.');
  need(await hash(basis,crypto)===data.templateSha256&&await hash(basis.plaintext,crypto,true)===TEXT&&await hash(basis.values,crypto)===VALUES,'The full Warning template or its independent trace changed.');unchanged();
  for(const p of [...declared.domain.sourcePins,...basis.sourcePins])need(data.sourcePins.some(q=>q.path===p.path&&q.sha256===p.sha256),'The control manifest omitted an independent or parent source pin.');
  need(Array.isArray(data.entries)&&data.entries.length===declared.domain.bank.count&&data.entries.every(row=>Array.isArray(row)&&row.length===2&&row.every(pin)),'Commit every complete parent setting in exact order.');
  const token=freeze({state:'independent-commitments-loaded',parentDomainId:data.parentDomainId,sha256,settings:data.entries.length});manifests.set(token,{parent,template:freeze(basis),manifest:freeze(data),crypto});return token;
 }
 async function prepare(member,manifest){
  const binding=manifests.get(manifest);need(binding,'Use a loaded independent control manifest.');const value=M.inspectMember(member,{parent:binding.parent}),{template,crypto}=binding,alphabet=value.task.alphabet,index=new Map(alphabet.map((r,i)=>[r.rune,i]));
  need(await hash(alphabet,crypto)===template.alphabetSha256&&same(Array.from(template.plaintext).filter(ch=>index.has(ch)).map(ch=>index.get(ch)),template.values),'The independent plaintext and alphabet disagree.');
  const text=inverse(template.plaintext,value.actualSteps,alphabet),task=await E.prepare({title:'Synthetic complete-output pinned control: '+value.parentDomainId+' setting '+(value.globalSettingIndex+1),pages:[{id:'lp1-01',text}],alphabet:copy(alphabet),steps:copy(value.actualSteps),criterion:{kind:'exact-prefix',values:copy(template.values)}},crypto),entry=binding.manifest.entries[value.globalSettingIndex];
  need(task.taskId===entry[0],'The independent encoder differs from the offline committed task.');
  return freeze({task,expectedResultSha256:entry[1]});
 }
 async function verify(member,manifest){
  const binding=manifests.get(manifest);need(binding,'Use a loaded independent control manifest.');const control=await prepare(member,manifest),result=E.run(control.task);
  need(result.transformed.length===1&&result.transformed[0].text===binding.template.plaintext&&result.matches.length===1&&result.matches[0].matched===true&&await hash(result,binding.crypto)===control.expectedResultSha256,'The complete independently committed synthetic control failed.');
  const proof=freeze({state:'independent-control-passed',parentDomainId:member.parentDomainId,memberId:member.memberId,controlTaskId:control.task.taskId,controlResultSha256:control.expectedResultSha256,manifestSha256:manifest.sha256,checkedRunes:184,checks:{admission:false,targetExecution:false,persistence:false}});proofs.set(proof,{member,manifest});return proof;
 }
 function inspect(proof,{member,manifest}){const binding=proofs.get(proof);need(binding&&binding.member===member&&binding.manifest===manifest,'Use the independently verified control for this exact member and manifest.');M.inspectMember(member);return proof;}
 const api=Object.freeze({read,prepare,verify,inspect});if(node)module.exports=api;else root.PinnedWarningControls=api;
})(typeof globalThis!=='undefined'?globalThis:this);
