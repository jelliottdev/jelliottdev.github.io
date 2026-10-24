/* Proposed normalization only: no research loader, source fetch or confirmation. */
import {SCHEMA,JSON_SCHEMA,PROMPT,validateInput,toDraft} from './interpretation.mjs';

export const MODEL='@cf/google/gemma-4-26b-a4b-it';
export const PROMPT_VERSION='interpret-v4-nullable-wire';
export const LIMITS=Object.freeze({bodyBytes:12000,modelBytes:24000,responseBytes:26000,timeoutMs:20000,concurrency:3,cacheEntries:50,cacheMs:600000,cooldownMs:60000});
const encoder=new TextEncoder();
const stepProperties=JSON_SCHEMA.properties.steps.items.properties;
const ruleProperties=JSON_SCHEMA.properties.rules.properties;
const ruleNames=Object.keys(ruleProperties),ruleShape=ruleProperties[ruleNames[0]].properties;
export const WIRE_SCHEMA={type:'object',additionalProperties:false,required:['schema','outcome','steps','scope','rules'],properties:{
 schema:JSON_SCHEMA.properties.schema,outcome:JSON_SCHEMA.properties.outcome,scope:JSON_SCHEMA.properties.scope,
 steps:{type:'array',maxItems:12,items:{type:'object',additionalProperties:false,required:['id','familyId','source','key'],properties:{id:stepProperties.id,familyId:stepProperties.familyId,source:stepProperties.source,key:{anyOf:[{type:'null'},stepProperties.parameters.properties.key]}}}},
 rules:{type:'array',maxItems:ruleNames.length,items:{type:'object',additionalProperties:false,required:['name','status','value','source'],properties:{name:{enum:ruleNames},status:ruleShape.status,value:{anyOf:[{type:'null'},ruleShape.value]},source:ruleShape.source}}}
}};
const exampleText='Reverse each row on LP2-15, preserving word boundaries.';
const example={schema:SCHEMA,outcome:null,steps:[{id:'reverse_row_runes',familyId:'transposition',source:{start:0,quote:'Reverse each row'},key:null}],scope:{pages:['lp2-15'],passage:null,source:{start:exampleText.indexOf('LP2-15'),quote:'LP2-15'}},rules:[{name:'wordBoundaries',status:'specified',value:'preserve',source:{start:exampleText.indexOf('preserving'),quote:'preserving word boundaries'}}]};
export const WIRE_PROMPT=PROMPT.replace('Rules use only the listed existing fields; omitted rules stay unspecified.','Rules list only explicitly supplied fields; an empty rules array means every rule remains unspecified.')+
 '\nMODEL WIRE LAYOUT: Every step has key:null when no literal key is supplied, otherwise key:{value,source}. There is NO parameters object. Rules is an ARRAY of {name,status,value,source}, containing only explicitly supplied rules, never a fixed list of all possible rules. Use rules:[] when none are stated. Each rule name appears at most once. A specified rule requires a literal string value; not_applicable/unrestricted require value:null and explicit evidence. All schema object fields are required; use the declared nulls for absent outcome, scope, passage, pages and key. A page ID and the word "row" are not cipher keys. Do not duplicate a step to satisfy a schema branch.\nSmall example input: '+JSON.stringify({text:exampleText})+'\nExact example output: '+JSON.stringify(example);
function wireData(value,depth=0,budget={nodes:0}){
 if(depth>12||++budget.nodes>2000)throw Error('Wire structural limit');
 if(value===null||typeof value==='boolean'||typeof value==='number'&&Number.isFinite(value))return value;
 if(typeof value==='string'){if(value.length>24000)throw Error('Wire string limit');return value;}
 if(!value||typeof value!=='object'||![Object.prototype,null,Array.prototype].includes(Object.getPrototypeOf(value)))throw Error('Wire JSON data required');
 const result=Array.isArray(value)?[]:{};
 for(const key of Object.keys(value)){if(['__proto__','prototype','constructor'].includes(key))throw Error('Unsafe wire field');const descriptor=Object.getOwnPropertyDescriptor(value,key);if(!Object.hasOwn(descriptor,'value'))throw Error('Wire accessor rejected');result[key]=wireData(descriptor.value,depth+1,budget);}return result;
}
function wireObject(value,fields){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==fields.length||fields.some(k=>!Object.hasOwn(value,k)))throw Error('Wire fields mismatch');}
function wireSource(value){wireObject(value,['start','quote']);if(!Number.isInteger(value.start)||value.start<0||typeof value.quote!=='string'||!value.quote.trim())throw Error('Wire source required');}
export function fromWire(input){
 if(typeof input==='string'){if(encoder.encode(input).length>LIMITS.modelBytes)throw Error('Wire size limit');input=JSON.parse(input);}
 const wire=wireData(input);if(encoder.encode(JSON.stringify(wire)).length>LIMITS.modelBytes)throw Error('Wire size limit');
 wireObject(wire,['schema','outcome','steps','scope','rules']);if(wire.schema!==SCHEMA)throw Error('Wire schema version');
 if(wire.outcome!==null){wireObject(wire.outcome,['id','source']);if(!JSON_SCHEMA.properties.outcome.anyOf[1].properties.id.enum.includes(wire.outcome.id))throw Error('Wire outcome ID');wireSource(wire.outcome.source);}
 if(wire.scope!==null){wireObject(wire.scope,['pages','passage','source']);wireSource(wire.scope.source);if(wire.scope.pages!==null&&(!Array.isArray(wire.scope.pages)||wire.scope.pages.length>75||wire.scope.pages.some(p=>typeof p!=='string'||!/^lp[12]-\d{2}$/.test(p))))throw Error('Wire pages');if(wire.scope.passage!==null&&(typeof wire.scope.passage!=='string'||!wire.scope.passage.trim()))throw Error('Wire passage');}
 if(!Array.isArray(wire.steps)||wire.steps.length>12||!Array.isArray(wire.rules)||wire.rules.length>ruleNames.length)throw Error('Wire array limits');
 const steps=wire.steps.map(step=>{wireObject(step,['id','familyId','source','key']);if(!stepProperties.id.enum.includes(step.id)||step.familyId!==null&&!stepProperties.familyId.anyOf[1].enum.includes(step.familyId))throw Error('Wire operation/family ID');wireSource(step.source);
  if(step.key!==null){wireObject(step.key,['value','source']);wireSource(step.key.source);if(typeof step.key.value!=='string'||!step.key.value.length)throw Error('Wire key value');}
  return {id:step.id,familyId:step.familyId,source:step.source,parameters:step.key===null?{}:{key:step.key}};});
 const rules={};for(const rule of wire.rules){wireObject(rule,['name','status','value','source']);if(!ruleNames.includes(rule.name)||Object.hasOwn(rules,rule.name))throw Error('Unknown/duplicate wire rule');if(!ruleShape.status.enum.includes(rule.status)||(rule.status==='specified'?typeof rule.value!=='string'||!rule.value.trim():rule.value!==null))throw Error('Wire rule state/value mismatch');wireSource(rule.source);rules[rule.name]={status:rule.status,...(rule.status==='specified'?{value:rule.value}:{}),source:rule.source};}
 return {schema:wire.schema,outcome:wire.outcome,steps,scope:wire.scope,rules};
}
export async function sourceBinding(text){
 validateInput(text);
 const digest=await crypto.subtle.digest('SHA-256',encoder.encode(text));
 return [...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
}
async function digest(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
export function alignQuotePositions(text,content){
 validateInput(text);
 if(typeof content!=='string'||encoder.encode(content).length>LIMITS.modelBytes)throw Error('Invalid candidate JSON size');
 const candidate=JSON.parse(content);
 const align=source=>{
  // Only correct an existing position. Missing evidence fields still fail the
  // strict shared validator. No quote, value, ID or operation order changes.
  if(!source||typeof source!=='object'||Array.isArray(source)||!Object.hasOwn(source,'start')||typeof source.quote!=='string'||!source.quote.length)return;
  const index=text.indexOf(source.quote);
  if(index!==-1&&text.indexOf(source.quote,index+1)===-1)source.start=index;
 };
 align(candidate?.outcome?.source);
 if(Array.isArray(candidate?.steps))for(const step of candidate.steps){align(step?.source);align(step?.parameters?.key?.source);}
 align(candidate?.scope?.source);
 for(const name of Object.keys(JSON_SCHEMA.properties.rules.properties))align(candidate?.rules?.[name]?.source);
 return candidate;
}
async function readText(request){
 if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))throw Error('Expected JSON');
 const reader=request.body?.getReader();if(!reader)throw Error('Missing body');
 const parts=[];let length=0;
 try{
  while(true){const {done,value}=await reader.read();if(done)break;length+=value.byteLength;if(length>LIMITS.bodyBytes){await reader.cancel();throw Error('Body too large');}parts.push(value);}
 }finally{reader.releaseLock();}
 const bytes=new Uint8Array(length);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}
 const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).length!==1||!Object.hasOwn(data,'text'))throw Error('Expected exact text envelope');
 return validateInput(data.text);
}
const unavailable=reason=>({status:503,data:{error:'A proposed interpretation is temporarily unavailable. Retry explicitly or review the original wording.',reason}});

// Clock/timer injection is for offline tests. Provider calls are never retried.
export function createInterpretHandler({now=()=>Date.now(),schedule=setTimeout,unschedule=clearTimeout}={}){
 const memory=new Map(),pending=new Map();let coolingUntil=0;
 const remember=(key,data)=>{
  for(const [k,item]of memory)if(item.until<=now())memory.delete(k);
  if(memory.size>=LIMITS.cacheEntries)memory.delete(memory.keys().next().value);
  memory.set(key,{until:now()+LIMITS.cacheMs,data});
 };
 const fail=reason=>{coolingUntil=now()+LIMITS.cooldownMs;return unavailable(reason);};
 return async function interpret(request,env={}){
  const allowed=env.SITE_ORIGIN||'https://jelliottdev.github.io',origin=request.headers.get('origin');
  const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
  let configured=false;try{const parsed=new URL(allowed);configured=parsed.origin===allowed&&['https:','http:'].includes(parsed.protocol);}catch{}
  if(configured&&origin===allowed)headers['Access-Control-Allow-Origin']=allowed;
  const reply=(data,status=200)=>Response.json(data,{status,headers});
  if(new URL(request.url).pathname!=='/interpret')return reply({error:'Not found'},404);
  if(!configured)return reply({error:'Interpretation is not configured.'},503);
  if(origin!==allowed)return reply({error:'Origin not allowed'},403);
  if(request.method==='OPTIONS')return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'86400'}});
  if(request.method!=='POST')return new Response(JSON.stringify({error:'Use POST'}),{status:405,headers:{...headers,Allow:'POST, OPTIONS'}});
  let text;try{text=await readText(request);}catch{return reply({error:'Send only text containing 1–1,500 characters, in a JSON body of at most 12,000 bytes.'},400);}
  if(typeof env.AI?.run!=='function'||typeof env.IDEA_LIMIT?.limit!=='function')return reply({error:'Interpretation is not configured.'},503);
  try{
   const limit=await env.IDEA_LIMIT.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'});
   if(!limit?.success)return reply({error:'Please wait a minute before requesting another interpretation.'},429);
  }catch{return reply({error:'Interpretation is temporarily unavailable.'},503);}
  const binding=await sourceBinding(text),key=await digest(JSON.stringify([PROMPT_VERSION,MODEL,SCHEMA,WIRE_PROMPT,WIRE_SCHEMA,text]));
  const hit=memory.get(key);if(hit&&hit.until>now())return reply({...hit.data,cached:true});if(hit)memory.delete(key);
  // A timed-out provider still occupies its slot until the actual call settles.
  // Repeated requests join its already-settled timeout response, never retry it.
  if(pending.has(key)){const result=await pending.get(key).response;return reply(result.data,result.status);}
  if(coolingUntil>now()||pending.size>=LIMITS.concurrency){const result=unavailable('busy');return reply(result.data,result.status);}
  let timer,settled=false,timedOut=false;
  const job={response:null};pending.set(key,job);
  const provider=Promise.resolve().then(()=>env.AI.run(MODEL,{
   messages:[{role:'system',content:WIRE_PROMPT},
    {role:'user',content:JSON.stringify({text})}],
   response_format:{type:'json_schema',json_schema:{name:'proposed_interpretation_wire',strict:true,schema:WIRE_SCHEMA}},
   temperature:0,max_completion_tokens:2500,stream:false,store:false,chat_template_kwargs:{enable_thinking:false}
  }));
  const completion=provider.then(result=>{
   if(timedOut)return unavailable('timeout');
   const content=result?.choices?.[0]?.message?.content;
   if(typeof content!=='string'||!content.trim()||encoder.encode(content).length>LIMITS.modelBytes)return fail('invalid-interpretation');
   let candidate;try{candidate=toDraft(text,alignQuotePositions(text,JSON.stringify(fromWire(content)))).candidate;}catch{return fail('invalid-interpretation');}
   const data={candidate,sourceBinding:binding,requiresConfirmation:true,meaningVerified:false};
   if(encoder.encode(JSON.stringify(data)).length>LIMITS.responseBytes)return fail('invalid-interpretation');
   if(!timedOut)remember(key,data);return {status:200,data};
  },()=>timedOut?unavailable('timeout'):fail('provider-unavailable'));
  // This cleanup follows actual settlement, independently of the response race.
  const observed=completion.finally(()=>{settled=true;if(pending.get(key)===job)pending.delete(key);});
  const timeout=new Promise(resolve=>{timer=schedule(()=>{if(!settled){timedOut=true;resolve(fail('timeout'));}},LIMITS.timeoutMs);});
  job.response=Promise.race([observed,timeout]).finally(()=>unschedule(timer));
  const result=await job.response;return reply(result.data,result.status);
 };
}
