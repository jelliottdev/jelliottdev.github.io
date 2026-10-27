/* Private admission request reuse: synthetic controls only, no target outputs. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import E from '../../local-experiment.js';
import Controls from '../../local-plan-controls.js';
import {prepare as bind,cardFromMaintained} from './pinned-domain-question.mjs';
import {createPinnedQuestionRequestContext as create,closePinnedQuestionRequestContext as close} from './pinned-question-request-context.mjs';
import {preparePinnedQuestionMember as prepare,checkedPinnedQuestionMember as checked,issuePinnedQuestionPreparation as issue} from './pinned-question-admission.mjs';
import {preparePinnedDomainMember as domain} from './pinned-domain-admission.mjs';
const ROOT=new URL('../../',import.meta.url),sourceId='rotating-left-nine-openings-v1',db={prepare(){throw Error('No DB access required');},batch(){throw Error('No DB writes required');}};
let fetches=0;const fetcher=async url=>{fetches++;return new Response(readFileSync(new URL(new URL(url).pathname.slice(1),ROOT)));};
async function question(){const card=cardFromMaintained(sourceId),proposalId='p_'+createHash('sha256').update(C.serialize(card)).digest('hex');return bind({card,proposalId},{fetcher});}
const selection={globalSettingIndex:0,pageIds:['lp2-00']};let groups=0,runs=0;async function test(name,fn){await fn();groups++;console.log('PASS '+name);}
const run=E.run;E.run=task=>{assert(task.title.startsWith('Synthetic complete-output pinned control: ')||task.title.startsWith('Synthetic local reference '));runs++;return run(task);};
try{
await test('prepare and fresh checked admission share one source but independently rerun all controls',async()=>{const q=await question(),context=create(q,{db,fetcher}),before=fetches,start=runs,p=await prepare({question:q,selection,fetcher,requestContext:context});assert(runs>start);const n=runs,v=await checked({basis:p.basis,card:p.card,task:p.task,inputVersion:p.inputVersion,fetcher,requestContext:context});assert(runs>n);assert.deepEqual(v,p);assert.equal(fetches,before);await assert.rejects(issue({db,prepared:p,requestContext:{}}),/differs/);close(context);await assert.rejects(issue({db,prepared:p,requestContext:context}),/live private context/);});
await test('forged contexts other question tokens dependencies and source overrides fail before controls',async()=>{const q=await question(),other=await question(),controller=new AbortController(),context=create(q,{db,fetcher,signal:controller.signal}),base={question:q,selection,fetcher,signal:controller.signal,requestContext:context},before=runs;for(const bad of [{...base,requestContext:{}},{...base,question:other},{...base,signal:undefined},{...base,fetcher:async()=>{}},{...base,crypto:{}},{...base,loadDomain:async()=>{}},{...base,loadBundle:async()=>{}}])await assert.rejects(prepare(bad));await assert.rejects(domain({sourceId,selection,fetcher,signal:controller.signal,requestContext:context,bundle:{}}));await assert.rejects(domain({sourceId:'rotating-right-nine-openings-v1',selection,fetcher,signal:controller.signal,requestContext:context}));assert.equal(runs,before);close(context);});
await test('closure during awaited controls cannot return a reusable preparation',async()=>{const q=await question(),context=create(q,{db,fetcher}),original=Controls.prepare;Controls.prepare=async(...args)=>{const result=await original(...args);close(context);return result;};try{await assert.rejects(prepare({question:q,selection,fetcher,requestContext:context}),/live private context/);}finally{Controls.prepare=original;}});
await test('changed canonical original card or declared task cannot reuse context admission',async()=>{const q=await question(),context=create(q,{db,fetcher}),p=await prepare({question:q,selection,fetcher,requestContext:context});const card=structuredClone(p.card);card.outcome.detail+=' changed';await assert.rejects(checked({basis:p.basis,card,task:p.task,inputVersion:p.inputVersion,fetcher,requestContext:context}));const task=structuredClone(p.task);task.title+=' changed';await assert.rejects(checked({basis:p.basis,card:p.card,task,inputVersion:p.inputVersion,fetcher,requestContext:context}));close(context);});
}finally{E.run=run;}
console.log(groups+' request-context admission groups passed; '+runs+' synthetic controls, no target output.');
