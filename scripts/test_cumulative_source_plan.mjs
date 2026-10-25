import assert from 'node:assert/strict';
import C from '../claim-specification.js';
import H from '../claim-share.js';
import F from '../fixed-plan-compiler.js';
import {createAIPlanner} from '../services/idea-assistant/propose-task-plan.mjs';
const field=value=>C.field('specified',value,{kind:'supplied',refs:['source']});
function card(text,pages=['lp2-15','lp2-17']){return H.cardData(C.confirm(C.createDraft({source:{text},aim:field('Inspect recurrence'),scope:field({pages}),method:field({operations:[{id:'described_method',label:text,sourceText:text}]}),rules:{representation:field('GP29'),inputVersion:field('reviewed'),evaluation:field('measurement'),initialState:field(0)}}),{id:'private-source-plan',at:'2026-10-25T12:00:00Z'}));}
// No provider is supplied; all accepted plans must pass the local complete grammar.
const planner=createAIPlanner({compile:F.compile});
for(const reset of ['page','line','word']){const text='Use cumulative difference reset at each '+reset+' on LP2-15, LP2-17',input=card(text),before=JSON.stringify(input),result=await planner(input);assert.deepEqual(result.plan.steps,[{op:'cumulative-difference',reset}]);assert.deepEqual(result.plan.pages,['lp2-15','lp2-17']);assert.equal(result.plan.inputVersion,'reviewed');assert.equal(JSON.stringify(input),before);assert.equal(result.mapping.steps[0].source.quote,text);}
for(const [text,pages]of [['Cumulative difference reset at each page on LP2-15',['lp2-15','lp2-17']],['Cumulative difference reset at each page on LP2-15-17',['lp2-15','lp2-17']],['Cumulative difference reset at each page on LP2-15, LP2-17 then reverse every rune',['lp2-15','lp2-17']],['Cumulative difference reset at each page on LP2-15, LP2-17 except F',['lp2-15','lp2-17']],['Cumulative difference reset at each page on LP2-15, lines 1-3',['lp2-15']],['Cumulative difference reset at each page on LP2-15, LP2-15',['lp2-15']],['Cumulative difference reset at each page, starting at 7 on LP2-15, LP2-17',['lp2-15','lp2-17']]])assert((await planner(card(text,pages))).reason,text);
const conflict=card('Cumulative difference reset at each page on LP2-15, LP2-17');conflict.rules.reset={status:'specified',value:'word'};assert((await planner(conflict)).reason);
console.log('PASS exact cumulative scope-tail local plans retain full source/edition/page holes; extra clauses, partial scope, duplicate pages and conflicting reset refuse without AI');
