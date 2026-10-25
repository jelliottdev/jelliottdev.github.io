/* Pinned descriptive rune-order references. Never a readability/language verdict. */
(function(root){
 'use strict';
 const data=typeof module==='object'&&module.exports?require('./language-model-data.js'):root.RuneLanguageModelData;
 const ID='gp29-flores-trigram-v1',PIN='8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4';
 const IDS=['eng_Latn','cym_Latn','deu_Latn','fra_Latn','spa_Latn','ita_Latn','por_Latn','fin_Latn'];
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
 function sha256(text){
  const input=new TextEncoder().encode(text),size=Math.ceil((input.length+9)/64)*64,bytes=new Uint8Array(size),view=new DataView(bytes.buffer);bytes.set(input);bytes[input.length]=128;view.setUint32(size-8,Math.floor(input.length/0x20000000));view.setUint32(size-4,(input.length*8)>>>0);
  const k=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19],w=new Uint32Array(64),rotate=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let offset=0;offset<size;offset+=64){
   for(let i=0;i<16;i++)w[i]=view.getUint32(offset+i*4);
   for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(rotate(a,7)^rotate(a,18)^(a>>>3))+w[i-7]+(rotate(b,17)^rotate(b,19)^(b>>>10)))>>>0;}
   let [a,b,c,d,e,f,g,j]=h;
   for(let i=0;i<64;i++){const t1=(j+(rotate(e,6)^rotate(e,11)^rotate(e,25))+((e&f)^(~e&g))+k[i]+w[i])>>>0,t2=((rotate(a,2)^rotate(a,13)^rotate(a,22))+((a&b)^(a&c)^(b&c)))>>>0;j=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
   [a,b,c,d,e,f,g,j].forEach((v,i)=>h[i]=(h[i]+v)>>>0);
  }
  return h.map(n=>n.toString(16).padStart(8,'0')).join('');
 }
 function freeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 if(!exact(data,['payload','sha256'])||data.sha256!==PIN||sha256(stable(data.payload))!==PIN)throw Error('The pinned rune-language reference model is unavailable or changed.');
 const p=data.payload;
 if(p.schema!=='liberpedia-language-model-v1'||p.modelId!==ID||p.scoreVersion!==1||p.minimumRunes!==40||p.shuffle.replicates!==32||p.scoring.scale!==1000||p.scoring.gramOrder!==3||p.alphabet.length!==29||p.models.length!==8)throw Error('The rune-language reference protocol is invalid.');
 const models=p.models.map((m,i)=>{if(m.id!==IDS[i]||!Array.isArray(m.scores)||m.scores.length!==29**3||m.scores.some(n=>!Number.isInteger(n)||n< -32768||n>0))throw Error('A rune-language reference table is invalid.');return{id:m.id,scores:Int16Array.from(m.scores)};});freeze(data);
 function criterion(){return{kind:'language-score',modelId:ID,modelSha256:PIN};}
 function validateCriterion(c){if(!exact(c,['kind','modelId','modelSha256'])||c.kind!=='language-score'||c.modelId!==ID||c.modelSha256!==PIN)throw Error('Choose the pinned rune-language comparison criterion.');return c;}
 function total(values,scores){let sum=0;for(let i=2;i<values.length;i++)sum+=scores[(values[i-2]*29+values[i-1])*29+values[i]];return sum;}
 function shuffle(values,replicate){
  const out=values.slice();let state=(0x33010000^Math.imul(values.length,0x9e3779b1)^Math.imul(replicate+1,0x85ebca6b))>>>0;if(!state)state=1;
  for(let i=out.length-1;i>0;i--){state=(state^(state<<13))>>>0;state=(state^(state>>>17))>>>0;state=(state^(state<<5))>>>0;const j=state%(i+1),v=out[i];out[i]=out[j];out[j]=v;}return out;
 }
 function evaluate(values){
  if(!(Array.isArray(values)||ArrayBuffer.isView(values)&&!(values instanceof DataView))||values.length>20000)throw Error('Supply at most 20,000 rune indices.');
  const input=Array.from(values);if(input.some(v=>!Number.isInteger(v)||v<0||v>28))throw Error('Rune indices must be integers from zero to 28.');
  const windows=Math.max(0,input.length-2);if(input.length<40)return{runes:input.length,windows,status:'insufficient',models:[]};
  const compared=models.map(m=>({id:m.id,total:total(input,m.scores),shuffledMin:Infinity,shuffledMax:-Infinity,shuffledAtOrAbove:0}));
  for(let replicate=0;replicate<32;replicate++){const shuffled=shuffle(input,replicate);models.forEach((m,i)=>{const score=total(shuffled,m.scores),row=compared[i];row.shuffledMin=Math.min(row.shuffledMin,score);row.shuffledMax=Math.max(row.shuffledMax,score);if(score>=row.total)row.shuffledAtOrAbove++;});}
  return{runes:input.length,windows,status:'compared',models:compared};
 }
 const api={criterion,validateCriterion,evaluate,data};if(typeof module==='object'&&module.exports)module.exports=api;else root.RuneLanguageScore=api;
})(typeof globalThis!=='undefined'?globalThis:this);
