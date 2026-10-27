/* Maintained output questions. Separate from transformations and measurement methods. */
(function(root){
 'use strict';
 const definition=Object.freeze({
  kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4',
  heading:'Compare with language samples',
  question:'Does the rune order resemble the reference texts more than rearrangements of the same runes?',
  plan:'Compare groups of three runes with eight fixed language samples. For each page, compare its score with 32 rearrangements of the same runes. Pages with fewer than 40 runes are too short for this comparison.',
  limit:'This compares rune patterns under a stated spelling conversion. It does not identify the language or establish a decryption. Trying many outputs can produce high scores by chance.',
  next:'Inspect the complete output for coherent meaning. A promising score needs a separate test on text that was not used to choose the rule.',
  references:'English, Welsh, German, French, Spanish, Italian, Portuguese and Finnish',
  minimumRunes:40,replicates:32
 });
 const decodedOpenings={warning:['Warning',[24,7,24,4,9,21,17,18,20,10,18,1]],welcome:['Welcome',[7,18,20,5,3,19,18,7,18,20,5,3]],'some-wisdom':['Some Wisdom',[15,3,19,18,7,10,15,23,3,19,2,18]],'first-koan':['First Koan',[24,5,3,24,9,24,19,24,9,23,18,5]],'loss-of-divinity':['Loss of Divinity',[2,18,20,3,15,15,3,0,23,10,1,10]],'second-koan':['Second Koan',[24,5,3,24,9,23,1,4,21,24,20,18]],instruction:['Instruction',[24,9,10,9,15,16,4,1,5,16,27,9]],'lp2-56':['LP2 page 56',[24,9,18,9,23,7,10,2,10,9,2,18]],'lp2-57':['LP2 page 57',[13,24,4,24,17,20,18,20,10,5,18,2]]};
 const decodedOpeningPages={warning:'lp1-01',welcome:'lp1-03','some-wisdom':'lp1-05','first-koan':'lp1-06','loss-of-divinity':'lp1-10','second-koan':'lp1-14',instruction:'lp1-16','lp2-56':'lp2-56','lp2-57':'lp2-57'};
 // Literal sequence metadata only; naming is never inferred from an ID alone.
 function openingReference(item){
  try{if(!item||typeof item!=='object'||Array.isArray(item)||Reflect.ownKeys(item).length!==2)return null;const id=Object.getOwnPropertyDescriptor(item,'id')?.value,values=Object.getOwnPropertyDescriptor(item,'values')?.value;
   if(typeof id!=='string'||!Array.isArray(values)||values.length>256)return null;
   const known=Object.hasOwn(decodedOpenings,id)&&decodedOpenings[id];if(!known||values.length!==known[1].length)return null;
   for(let i=0;i<values.length;i++)if(Object.getOwnPropertyDescriptor(values,String(i))?.value!==known[1][i])return null;
   return Object.freeze({label:known[0],page:decodedOpeningPages[id]});
  }catch{return null;}
 }
 function openingLength(criterion){
  try{const kind=Object.getOwnPropertyDescriptor(criterion,'kind')?.value,sets=kind==='exact-prefix'?[Object.getOwnPropertyDescriptor(criterion,'values')?.value]:kind==='exact-prefix-set'?Object.getOwnPropertyDescriptor(criterion,'openings')?.value:null;
   if(!Array.isArray(sets)||!sets.length||sets.length>32)return null;const lengths=[];
   for(let i=0;i<sets.length;i++){const item=Object.getOwnPropertyDescriptor(sets,String(i))?.value,values=kind==='exact-prefix'?item:Object.getOwnPropertyDescriptor(item,'values')?.value;if(!Array.isArray(values)||!values.length||values.length>256)return null;for(let j=0;j<values.length;j++){const value=Object.getOwnPropertyDescriptor(values,String(j))?.value;if(!Number.isInteger(value)||value<0||value>28)return null;}lengths.push(values.length);}
   const min=Math.min(...lengths),max=Math.max(...lengths);return min===max?(min===1?'Only the first rune of each output is compared.':'Only the first '+min+' runes of each output are compared.'):'Only the first '+min+'–'+max+' runes of each output are compared, using each supplied sequence’s full length.';
  }catch{return null;}
 }
 function identify(value){return Boolean(value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===3&&['kind','modelId','modelSha256'].every(key=>Object.hasOwn(value,key)&&Object.getOwnPropertyDescriptor(value,key)?.value===definition[key]));}
 function criterion(){return {kind:definition.kind,modelId:definition.modelId,modelSha256:definition.modelSha256};}
 function describe(value){return identify(value)?{...definition}:null;}
 const api={identify,criterion,describe,openingReference,openingLength};if(typeof module==='object'&&module.exports)module.exports=api;else root.OutputEvaluators=api;
})(typeof globalThis!=='undefined'?globalThis:this);
