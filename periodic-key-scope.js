/* Scope-bound representation proof only. No task admission, evaluation or execution. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON;
 const LIMITS=Object.freeze({bytes:2*1024*1024,nodes:30000,stream:20000,pages:75}),bindings=new WeakMap(),ALPHABET='06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f';
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
 const exact=(v,ks)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===ks.length&&ks.every(k=>Object.hasOwn(v,k));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 function capture(input){
  const v=J.capture(input,{maxBytes:LIMITS.bytes,maxDepth:12,maxNodes:LIMITS.nodes});
  if(!exact(v,['cycle','direction','reset','inputVersion','alphabet','pages'])||!['add','subtract'].includes(v.direction)||!['page','line','word'].includes(v.reset)||!['raw','reviewed'].includes(v.inputVersion))throw Error('Declare the exact periodic key and input scope.');
  if(!Array.isArray(v.cycle)||!v.cycle.length||v.cycle.length>LIMITS.stream||v.cycle.some(n=>!Number.isSafeInteger(n)||n<0||n>28))throw Error('Use a complete bounded GP29 key cycle.');
  if(!Array.isArray(v.alphabet)||v.alphabet.length!==29||v.alphabet.some(a=>!exact(a,['rune','prime','latin'])||typeof a.rune!=='string'||!/^\p{Script=Runic}$/u.test(a.rune)||!Number.isSafeInteger(a.prime)||a.prime<2||typeof a.latin!=='string'||/[\ud800-\udfff]/u.test(a.latin))||new Set(v.alphabet.map(a=>a.rune)).size!==29)throw Error('Use the complete GP29 alphabet.');
  if(!Array.isArray(v.pages)||!v.pages.length||v.pages.length>LIMITS.pages||new Set(v.pages.map(p=>p?.id)).size!==v.pages.length||v.pages.some(p=>!exact(p,['id','text'])||typeof p.id!=='string'||p.id.length!==6||!/^lp(?:1-(?:0\d|1[0-6])|2-(?:[0-4]\d|5[0-7]))$/.test(p.id)||typeof p.text!=='string'||/[\ud800-\udfff]/u.test(p.text)))throw Error('Use unique complete manuscript page inputs with valid Unicode.');
  return v;
 }
 async function hash(value,crypto,raw=false){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw?value:stable(value))))].map(n=>n.toString(16).padStart(2,'0')).join('');}
 async function prepare(input,{crypto=root.crypto}={}){
  const v=capture(input),alphabetSha256=await hash(v.alphabet,crypto),runes=new Set(v.alphabet.map(a=>a.rune));let maximumSegment=0;
  if(alphabetSha256!==ALPHABET)throw Error('The canonical GP29 alphabet changed.');
  const pages=[];
  for(const page of v.pages){
   let segment=0,count=0,maximum=0;
   for(const ch of page.text){if(runes.has(ch)){count++;maximum=Math.max(maximum,++segment);}else if(v.reset==='word'||v.reset==='line'&&/[\r\n]/.test(ch))segment=0;}
   maximumSegment=Math.max(maximumSegment,maximum);pages.push({id:page.id,textSha256:await hash(page.text,crypto,true),runes:count,maximumSegment:maximum});
  }
  // Keep every value of every cycle, including the final unused tail. A
  // finite stream is equivalent only on this pinned bounded input scope.
  const cycles=Math.max(1,Math.ceil(maximumSegment/v.cycle.length)),length=cycles*v.cycle.length;
  if(length>LIMITS.stream)throw Error('Complete key cycles exceed the existing finite-stream bound; nothing was shortened.');
  const key=Array.from({length},(_,i)=>v.cycle[i%v.cycle.length]);
  const basis={schema:'liberpedia-periodic-key-scope-v1',inputVersion:v.inputVersion,alphabetSha256,pages,sourceCycleSha256:await hash(v.cycle,crypto),sourcePeriod:v.cycle.length,direction:v.direction,reset:v.reset,maximumSegment,cycles,streamLength:length,step:{op:'finite-shift',key,direction:v.direction,reset:v.reset}};
  const result=freeze({...basis,id:await hash(basis,crypto),state:'representation-only'});bindings.set(result,stable(v));return result;
 }
 function inspect(result,input){
  if(!bindings.has(result)||bindings.get(result)!==stable(capture(input)))throw Error('This representation belongs to different periodic-key inputs.');return result;
 }
 const api=Object.freeze({prepare,inspect,LIMITS});if(node)module.exports=api;else root.PeriodicKeyScope=api;
})(typeof globalThis!=='undefined'?globalThis:this);
