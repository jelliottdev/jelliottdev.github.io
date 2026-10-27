/* Reconstruct one reviewed typed implementation from the unchanged official inputs.
 * Shape/mapping review is not proof that the program establishes its hypothesis. */
import C from '../../claim-specification.js';
import MD from '../../method-design.js';
import MI from '../../method-implementation.js';
import V from '../../declarative-rune-program.js';
import J from '../../finite-json.js';
import {loadInputBundle} from './official-inputs.mjs';
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const need=(ok,message)=>{if(!ok)throw Error(message);};
const sha=async(value,crypto)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(value)))),v=>v.toString(16).padStart(2,'0')).join('');
async function read(response,max){
 need(!response.redirected&&/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''),'The official source changed location or format.');
 const reader=response.body?.getReader();need(reader,'The official source has no body.');let size=0;const chunks=[];
 try{for(;;){const part=await reader.read();if(part.done)break;size+=part.value.byteLength;need(size<=max,'The official source exceeds its bound.');chunks.push(part.value);}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}finally{try{await reader.cancel();}catch{}}
}
export async function checkedMethodImplementation({basis,card,task,inputVersion,parentTaskId,fetcher=globalThis.fetch,signal,crypto=globalThis.crypto}){
 const captured=J.capture(basis,{maxBytes:128000,maxDepth:24,maxNodes:20000});
 need(exact(captured,['kind','implementation','review'])&&captured.kind==='method-implementation-v1','Use an exact reviewed implementation basis.');
 const source=MD.readCard(card);need(source&&parentTaskId===null&&inputVersion===source.proposal.inputVersion,'The implementation changed its proposal or source edition.');
 const token=await MI.bind({proposal:source.proposal,implementation:captured.implementation},crypto),bound=MI.inspect(token);
 need(bound.ready,'The proposed program still has unsupported details.');
 const review=captured.review;
 need(exact(review,['schema','proposalSha256','implementationSha256'])&&review.schema==='liberpedia-method-implementation-review-v1'&&review.proposalSha256===bound.implementation.proposalSha256&&review.implementationSha256===await sha(bound.implementation,crypto),'Review this exact proposed implementation first.');
 need(!signal?.aborted,'Implementation preparation cancelled.');
 const bundle=await loadInputBundle({fetcher,signal,read});
 const raw={schema:'liberpedia-local-inputs-v1',alphabet:bundle.alphabet,pages:[...bundle.pages.values()]};
 const expected=await V.prepare(MI.compileBody(token,{bundle:raw}),crypto);
 need(!signal?.aborted&&C.serialize(expected)===C.serialize(task),'The exact implementation, page scope or official input changed.');
 need(C.serialize(captured)===C.serialize(J.capture(basis,{maxBytes:128000,maxDepth:24,maxNodes:20000})),'The reviewed implementation changed during preparation.');
 return Object.freeze({implementation:bound.implementation,review:Object.freeze({...review})});
}
/* Historical display reads immutable admitted bindings; it does not refresh,
 * issue, or authorize a task against today's possibly changed source edition. */
export async function readStoredMethodImplementation({db,proposalId,card,task,inputVersion,crypto=globalThis.crypto}){
 const row=await db.prepare('SELECT basis_json,basis_hash,card_hash,task_hash,input_version,parent_task_id FROM prepared_plans WHERE proposal_id=? AND task_id=? ORDER BY created_at,id LIMIT 1').bind(proposalId,task.taskId).first();
 need(row&&row.input_version===inputVersion&&row.parent_task_id===null&&row.card_hash===await sha(card,crypto)&&proposalId==='p_'+row.card_hash&&row.task_hash===await sha(task,crypto),'The saved program has no matching reviewed preparation.');
 const basis=J.capture(JSON.parse(row.basis_json),{maxBytes:128000,maxDepth:24,maxNodes:20000});
 need(C.serialize(basis)===row.basis_json&&await sha(basis,crypto)===row.basis_hash&&exact(basis,['kind','implementation','review'])&&basis.kind==='method-implementation-v1','The saved implementation basis changed.');
 const source=MD.readCard(card);need(source&&inputVersion===source.proposal.inputVersion,'The saved proposal changed its input edition.');
 const bound=MI.inspect(await MI.bind({proposal:source.proposal,implementation:basis.implementation},crypto)),review=basis.review;
 need(bound.ready&&exact(review,['schema','proposalSha256','implementationSha256'])&&review.schema==='liberpedia-method-implementation-review-v1'&&review.proposalSha256===bound.implementation.proposalSha256&&review.implementationSha256===await sha(bound.implementation,crypto),'The saved program review changed.');
 need(task.title===source.proposal.name&&C.serialize(task.steps)===C.serialize(bound.implementation.steps)&&C.serialize(task.criterion)===C.serialize(bound.implementation.criterion)&&C.serialize(task.pages.map(p=>p.id))===C.serialize(source.proposal.pages),'The saved calculation differs from its reviewed program.');
 return Object.freeze({implementation:bound.implementation,review:Object.freeze({...review})});
}
