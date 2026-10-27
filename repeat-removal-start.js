/* Explicit first observation, never an interpretation of a pasted hypothesis. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,MD=node?require('./method-design.js'):root.MethodDesign,J=node?require('./finite-json.js'):root.FiniteJSON;
 const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 const need=(ok,message)=>{if(!ok)throw Error(message);};
 // Version-one recipe wording is protocol data for exact matching. Changing
 // display labels must not change these maintained procedure definitions.
 const RECIPE_VERSION=1,BOUNDARY_RULES=freeze({word:'Every non-rune starts a new group, including spaces, punctuation and line breaks.',line:'Ignore retained spaces and punctuation when finding neighboring runes; a carriage return or line feed starts a new group.',page:'Ignore retained spaces, punctuation and line breaks when finding neighboring runes. No group crosses a page boundary.'});
 const OPTIONS=freeze({
  policies:[{value:'all-but-first',label:'Keep one rune per repeated run',example:'AAA → A'},{value:'non-overlapping-pairs',label:'Remove second rune of each pair',example:'AAA → AA'}],
  units:[{value:'word',label:'Restart at every separator',description:'Every non-rune starts a new group, including spaces, punctuation and line breaks.'},{value:'line',label:'Restart at each line',description:'Ignore retained spaces and punctuation when finding neighboring runes; a carriage return or line feed starts a new group.'},{value:'page',label:'Restart at each page',description:'Ignore retained spaces, punctuation and line breaks when finding neighboring runes. No group crosses a page boundary.'}],
  inputVersions:[{value:'raw',label:'Raw transcription'},{value:'reviewed',label:'Reviewed transcription'}]
 });
 function propose(input){
  const value=J.capture(input,{maxBytes:8192,maxDepth:4,maxNodes:200});
  need(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===4&&['policy','unit','pages','inputVersion'].every(key=>Object.hasOwn(value,key)),'Explicitly choose a repeat policy, boundaries, ordered pages and transcription.');
  need(['all-but-first','non-overlapping-pairs'].includes(value.policy)&&typeof value.unit==='string'&&Object.hasOwn(BOUNDARY_RULES,value.unit)&&['raw','reviewed'].includes(value.inputVersion),'Choose maintained repeat-removal settings without defaults.');
  const action=value.policy==='all-but-first'?'Keep only the first rune of each maximal run of equal neighboring rune values; remove every later rune in that run.':'For each maximal run of equal neighboring rune values, group its runes into non-overlapping pairs from the start and remove the second rune of each pair; retain any unmatched final rune.';
  const step=action+' '+BOUNDARY_RULES[value.unit]+' Keep all non-rune characters in their original order. Start fresh on every page.';
  const proposal=MD.validate({schema:MD.TYPED_SCHEMA,name:'Remove repeated runes',hypothesis:'Compare original text with a proposed repeat-removal version.',pages:value.pages,inputVersion:value.inputVersion,representation:{kind:'gp29'},keyUse:{kind:'not-used',material:'',application:''},steps:[step],parameters:[],evaluation:{kind:'original-output-measurements'},controls:[{kind:'implementation-sanity-v2'}],assumptions:['This is a proposed first observation, not a procedure stated by the original author.','Removing repetitions changes counts by construction. This observation cannot identify filler, establish statistical significance or verify a decryption.']});
  return freeze({proposal,programSteps:[{op:'collapse-adjacent-repeats',unit:value.unit,policy:value.policy}]});
 }
 function stable(value){return Array.isArray(value)?'['+value.map(stable).join(',')+']':value&&typeof value==='object'?'{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+stable(value[key])).join(',')+'}':JSON.stringify(value);}
 function match(input){
  let proposal;try{proposal=MD.validate(input);}catch{return null;}
  if(proposal.schema!==MD.TYPED_SCHEMA)return null;
  const expected=stable(proposal);
  for(const policy of ['all-but-first','non-overlapping-pairs'])for(const unit of ['word','line','page']){
   const candidate=propose({policy,unit,pages:proposal.pages,inputVersion:proposal.inputVersion});
   if(stable(candidate.proposal)===expected)return candidate.programSteps;
  }
  return null;
 }
 const api=Object.freeze({RECIPE_VERSION,OPTIONS,propose,match});if(node)module.exports=api;else root.RepeatRemovalStart=api;
})(typeof globalThis!=='undefined'?globalThis:this);
