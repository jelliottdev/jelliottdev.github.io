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
 function identify(value){return Boolean(value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===3&&['kind','modelId','modelSha256'].every(key=>Object.hasOwn(value,key)&&Object.getOwnPropertyDescriptor(value,key)?.value===definition[key]));}
 function criterion(){return {kind:definition.kind,modelId:definition.modelId,modelSha256:definition.modelSha256};}
 function describe(value){return identify(value)?{...definition}:null;}
 const api={identify,criterion,describe};if(typeof module==='object'&&module.exports)module.exports=api;else root.OutputEvaluators=api;
})(typeof globalThis!=='undefined'?globalThis:this);
