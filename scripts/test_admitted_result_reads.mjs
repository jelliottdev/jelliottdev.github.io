import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import {readAdmittedResult} from '../services/idea-assistant/admitted-result.mjs';
const alphabet=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ').map((rune,i)=>({rune,latin:'R'+i,prime:i+2}));
const task=await E.prepare({title:'Stored read fixture',alphabet,pages:[{id:'lp2-00',text:'ᚠᚢ ᚦᚩ\nᚱᚳ'}],steps:[{op:'reverse',unit:'page'}],criterion:{kind:'measurement'}}),result=E.run(task),hash=v=>createHash('sha256').update(E.stable(v)).digest('hex'),row={id:hash(result),created_at:'2026-10-25T12:00:00.000Z',result_json:JSON.stringify(result)};
const originalRun=E.run,originalVerify=E.verify;E.run=()=>{throw Error('No target work on read');};E.verify=()=>{throw Error('No score or transform replay on read');};
try{assert.deepEqual(await readAdmittedResult(task,row),result);for(const mutate of [r=>r.metrics.runes++,r=>r.transformed[0].text='broken',r=>r.taskId='0'.repeat(64)]){const bad=structuredClone(result);mutate(bad);await assert.rejects(()=>readAdmittedResult(task,{...row,result_json:JSON.stringify(bad)}));}await assert.rejects(()=>readAdmittedResult(task,{...row,id:'0'.repeat(64)}));console.log('PASS admitted receipt preserves exact bytes without target/score replay; changed digest, geometry, metadata and task reject');
const bad=structuredClone(result);bad.transformed.reverse();bad.metrics.pages=0;await assert.rejects(()=>readAdmittedResult(task,{...row,id:hash(bad),result_json:JSON.stringify(bad)}),/metrics/);console.log('PASS structurally invalid envelopes reject even with internally recomputed digest');
}finally{E.run=originalRun;E.verify=originalVerify;}

import S from '../language-score.js';
import {readFileSync} from 'node:fs';
const canonical=JSON.parse(readFileSync(new URL('../data/local-run-inputs.json',import.meta.url),'utf8')).alphabet;
const languageTask=await E.prepare({title:'Admitted language fixture',alphabet:canonical,pages:[{id:'lp2-00',text:canonical.map(a=>a.rune).join('').repeat(3)}],steps:[],criterion:S.criterion()}),languageResult=E.run(languageTask),languageRow={...row,id:hash(languageResult),result_json:JSON.stringify(languageResult)},score=S.evaluate;
S.evaluate=()=>{throw Error('Stored language scores must not be recalculated on read');};E.verify=()=>{throw Error('No admitted result replay');};
try{assert.deepEqual(await readAdmittedResult(languageTask,languageRow),languageResult);const bad=structuredClone(languageResult);bad.languageScore.pages[0].page='lp2-01';await assert.rejects(()=>readAdmittedResult(languageTask,{...languageRow,id:hash(bad),result_json:JSON.stringify(bad)}),/language scope/);console.log('PASS admitted language result reads preserve model/page pins without loading a second score pass');}finally{S.evaluate=score;E.verify=originalVerify;}
