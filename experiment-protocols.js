/* Maintained measurement protocols. Metadata only: no numerical evaluation or inference. */
(function(root){
 'use strict';
 const boundaries=['non-rune','hyphen-period'];
 const boundaryNames={'non-rune':'Every non-rune character','hyphen-period':'Hyphens and periods'};
 const boundaryDescriptions={'non-rune':'Separate words at every non-rune character.','hyphen-period':'Separate words only at hyphens and periods.'};
 const definitions=[{
  id:'word-prime-sums',operation:{id:'word_prime_sums',label:'Word prime sums',labelRequired:true},
  fields:{table:{type:'enum',values:['canonical','reversed'],label:'Prime table',names:{canonical:'Usual table',reversed:'Reversed table'}},boundaries:{type:'enum',values:boundaries,label:'Word boundaries',names:boundaryNames}},
  title:'Word prime sums · {table} table · {boundaries}',heading:'Adding rune values within words',
  question:'What total does each word give when its rune values are added?',
  review:'Add values from the {tableName} within each word.',
  plan:'Use the {tableName} to assign a prime value to each rune, then add the values within each word. {boundaryPlan} Keep pages separate.',
  compilerNote:'Add the authorized GP prime value of every rune in each declared word. Reversed means reverse the prime assignments across the same ordered alphabet; it does not reverse digits or rune order. Non-rune characters are not assigned numbers. Pages remain separate.',
  limit:'These totals describe the selected words. They do not decode the text or show that a pattern is meaningful.',
  followups:[{id:'word-boundaries',field:'boundaries',label:'Compare word boundaries',choices:boundaries,descriptions:boundaryDescriptions}]
 },{
  id:'word-affine-count',operation:{id:'word_affine_count',label:'Within-word affine pair count',labelRequired:false},
  fields:{lag:{type:'integer',min:1,max:12,label:'Distance between runes'},a:{type:'integer',min:0,max:28,label:'Multiplier'},b:{type:'integer',min:0,max:28,label:'Offset'},boundaries:{type:'enum',values:boundaries,label:'Word boundaries',names:boundaryNames}},
  title:'Within-word rune pairs · lag {lag} · {boundaries}',heading:'Rune pairs {lag} positions apart',
  question:'How often does the chosen rule connect runes {lag} positions apart inside a word?',
  review:'Count pairs {lag} runes apart when later = ({a} × earlier + {b}) mod 29. Use alphabet positions 0–28.',
  plan:'Count pairs {lag} positions apart within each word that follow y = {a}x + {b} (mod 29). Compare the count with the average when all orders of the same runes within each word are equally likely. {boundaryPlan} Keep pages separate.',
  compilerNote:'Count only pairs within each page and declared word boundary. Compare with the exact average under uniformly shuffled rune order inside each word; this is not a tail probability or a correction for choosing a formula.',
  limit:'A count above the rearrangement average does not identify the cipher. This comparison does not account for trying other rules or distances.',
  followups:[{id:'word-boundaries',field:'boundaries',label:'Compare word boundaries',choices:boundaries,descriptions:boundaryDescriptions}]
 }];
 const clone=value=>JSON.parse(JSON.stringify(value));
 function plainPrototype(proto){
  if(proto===null||proto===Object.prototype)return true;
  if(Object.getPrototypeOf(proto)!==null)return false;
  const ctor=Object.getOwnPropertyDescriptor(proto,'constructor');
  return ctor&&Object.hasOwn(ctor,'value')&&typeof ctor.value==='function'
   &&Function.prototype.toString.call(ctor.value)===Function.prototype.toString.call(Object)
   &&Reflect.ownKeys(proto).every(k=>typeof k==='string')
   &&JSON.stringify(Object.getOwnPropertyNames(proto).sort())===JSON.stringify(Object.getOwnPropertyNames(Object.prototype).sort());
 }
 const data=o=>o&&typeof o==='object'&&!Array.isArray(o)&&plainPrototype(Object.getPrototypeOf(o))&&Reflect.ownKeys(o).every(k=>typeof k==='string'&&Object.getOwnPropertyDescriptor(o,k)?.enumerable&&Object.hasOwn(Object.getOwnPropertyDescriptor(o,k),'value'));
 const exact=(o,keys)=>data(o)&&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
 function find(criterion){
  if(!data(criterion))return null;
  const def=definitions.find(d=>d.id===criterion.kind);if(!def||!exact(criterion,['kind',...Object.keys(def.fields)]))return null;
  for(const [key,field] of Object.entries(def.fields)){
   const value=criterion[key];
   if(field.type==='enum'?!field.values.includes(value):!Number.isInteger(value)||value<field.min||value>field.max)return null;
  }return def;
 }
 function identify(criterion){const def=find(criterion);return def?clone(def):null;}
 function format(template,criterion,def){return template.replace(/\{([a-z]+)\}/gi,(_,key)=>key==='tableName'?criterion.table==='reversed'?'reversed prime table':'usual prime table':key==='boundaryPlan'?criterion.boundaries==='non-rune'?'Every non-rune character separates words.':"Only literal '-' and '.' separate words; spaces and line breaks join the runes on either side.":String(criterion[key]));}
 function describe(criterion){
  const def=find(criterion);if(!def)return null;
  return {id:def.id,operationId:def.operation.id,label:def.operation.label,
   title:format(def.title,criterion,def),heading:format(def.heading,criterion,def),question:format(def.question,criterion,def),review:def.id==='word-affine-count'&&criterion.a===1&&criterion.b===0?'Count pairs of the same rune '+criterion.lag+' '+(criterion.lag===1?'position':'positions')+' apart inside a word.':format(def.review,criterion,def),reviewBoundary:format('{boundaryPlan}',criterion,def),plan:format(def.plan,criterion,def),compilerNote:def.compilerNote,limit:def.limit,
   settings:Object.entries(def.fields).map(([key,field])=>({key,label:field.label,value:criterion[key],display:field.names?.[criterion[key]]??String(criterion[key])})),
   followups:def.followups.map(f=>{const from=criterion[f.field],to=f.choices.find(v=>v!==from);return {id:f.id,label:f.label,description:f.descriptions[to],from,to};})};
 }
 function fromOperation(op){
  if(!data(op))return null;
  const def=definitions.find(d=>d.operation.id===op.id);if(!def)return null;
  const hasLabel=Object.hasOwn(op,'label');
  if(def.operation.labelRequired&&!hasLabel||hasLabel&&op.label!==def.operation.label||!exact(op,['id',...(hasLabel?['label']:[]),...Object.keys(def.fields)]))return null;
  const criterion={kind:def.id};for(const key of Object.keys(def.fields))criterion[key]=op[key];return find(criterion)?criterion:null;
 }
 function variant(criterion,dimension){
  const def=find(criterion),followup=def?.followups.find(f=>f.id===dimension);if(!followup)return null;
  return {...criterion,[followup.field]:followup.choices.find(v=>v!==criterion[followup.field])};
 }
 const api={list:()=>clone(definitions),identify,describe,fromOperation,variant};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ExperimentProtocols=api;
})(typeof globalThis!=='undefined'?globalThis:this);
