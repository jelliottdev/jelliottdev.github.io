/* Server-only reader for results already admitted by the full replay gate.
 * Not an admission API: callers supply a row selected from local_task_results.
 * Browser consumers independently replay before using any scientific claims. */
import E from '../../local-experiment.js';
const HEX=/^[a-f0-9]{64}$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const ensure=(v,m)=>{if(!v)throw Error(m);};
export async function readAdmittedResult(task,row,crypto=globalThis.crypto){
 ensure(row&&HEX.test(row.id)&&typeof row.result_json==='string'&&new TextEncoder().encode(row.result_json).length<=8*1024*1024&&Number.isFinite(Date.parse(row.created_at)),'Stored result row is invalid');
 await E.checkIdentity(task,crypto);
 const result=JSON.parse(row.result_json),extra=task.criterion.kind==='language-score'?['languageScore']:task.criterion.kind==='word-prime-sums'?['wordSums']:task.criterion.kind==='word-affine-count'?['wordPairs']:[];
 ensure(exact(result,['schema','taskId','engine','runnerVersion','metrics','matches','transformed',...extra])&&result.schema===E.RESULT&&result.taskId===task.taskId&&result.engine===task.engine&&result.runnerVersion==='1','Stored result envelope changed');
 ensure(Array.isArray(result.transformed)&&result.transformed.length===task.pages.length&&Array.isArray(result.matches)&&result.matches.length===(task.criterion.kind==='exact-prefix'?task.pages.length:0),'Stored result scope changed');
 const runes=new Set(task.alphabet.map(r=>r.rune));
 for(let i=0;i<task.pages.length;i++){const output=result.transformed[i],input=Array.from(task.pages[i].text);ensure(exact(output,['page','text'])&&output.page===task.pages[i].id&&typeof output.text==='string','Stored output page changed');const chars=Array.from(output.text);ensure(chars.length===input.length&&input.every((ch,n)=>runes.has(ch)?runes.has(chars[n]):chars[n]===ch),'Stored output geometry changed');}
 const metrics=result.metrics;ensure(exact(metrics,['pages','runes','adjacentPairs','equalAdjacentPairs','ioc'])&&metrics.pages===task.pages.length&&['runes','adjacentPairs','equalAdjacentPairs'].every(k=>Number.isSafeInteger(metrics[k])&&metrics[k]>=0)&&metrics.equalAdjacentPairs<=metrics.adjacentPairs&&Number.isFinite(metrics.ioc)&&metrics.ioc>=0&&metrics.ioc<=1,'Stored metrics changed');
 if(task.criterion.kind==='language-score')ensure(exact(result.languageScore,['modelId','modelSha256','pages'])&&result.languageScore.modelId===task.criterion.modelId&&result.languageScore.modelSha256===task.criterion.modelSha256&&Array.isArray(result.languageScore.pages)&&result.languageScore.pages.length===task.pages.length&&result.languageScore.pages.every((p,i)=>p?.page===task.pages[i].id),'Stored language scope changed');
 const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.stable(result))))].map(v=>v.toString(16).padStart(2,'0')).join('');
 ensure(digest===row.id,'Stored result mismatch');
 return result;
}
