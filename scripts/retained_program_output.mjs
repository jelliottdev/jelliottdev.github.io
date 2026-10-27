/* Preserve an already computed fixed result; never invent or fill missing output. */
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import Controls from '../local-plan-controls.js';
import J from '../finite-json.js';
import {validateProgramCriterion} from '../services/idea-assistant/published-program-source-index.mjs';
export const SCHEMA='liberpedia-retained-program-output-v1';
const copy=v=>J.capture(v,{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000}),same=(a,b)=>E.stable(a)===E.stable(b),exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x)),need=(v,m)=>{if(!v)throw Error(m);},sha=v=>createHash('sha256').update(E.stable(v)).digest('hex'),date=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
export async function validateRetainedProgramOutput(input,crypto=globalThis.crypto){
 const v=copy(input),unchanged=()=>need(same(copy(input),v),'Retained program output changed during verification');need(exact(v,['schema','inputVersion','task','run','controls'])&&v.schema===SCHEMA&&v.inputVersion==='raw'&&exact(v.run,['id','createdAt','result'])&&date(v.run.createdAt),'Use an exact retained raw program output');validateProgramCriterion(v.task.criterion);await E.checkIdentity(v.task,crypto);unchanged();need(v.run.id===sha(v.run.result),'The retained result identity changed');await E.verify(v.task,v.run.result,crypto);unchanged();await Controls.validate(v.controls,v.task,crypto);unchanged();return v;
}
export async function prepareRetainedProgramOutput(input,crypto=globalThis.crypto){
 const v=copy(input),unchanged=()=>need(same(copy(input),v),'The supplied retained calculation changed');need(exact(v,['task','result','createdAt'])&&date(v.createdAt),'Supply an existing task, complete result and exact date');validateProgramCriterion(v.task.criterion);await E.checkIdentity(v.task,crypto);unchanged();await E.verify(v.task,v.result,crypto);unchanged();const controls=await Controls.prepare(v.task,crypto);unchanged();await Controls.validate(controls,v.task,crypto);unchanged();return {schema:SCHEMA,inputVersion:'raw',task:v.task,run:{id:sha(v.result),createdAt:v.createdAt,result:v.result},controls};
}
