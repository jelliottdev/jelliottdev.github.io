/* Anonymous upvotes express interest only, never research evidence. */
const ID=/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/,IDEA=/^idea-([a-f0-9]{64})$/,TOKEN=/^[a-f0-9]{64}$/;
const MAX_IDS=100,MAX_BODY=512,INDEX_BYTES=128*1024,INDEX_URL='https://jelliottdev.github.io/data/research-record-ids.json';
const validId=id=>typeof id==='string'&&id.length<=100&&ID.test(id);
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
async function bytes(response,max){const length=response.headers.get('content-length');if(length!==null&&(!/^\d+$/.test(length)||Number(length)>max))throw Error('Size bound');const reader=response.body?.getReader();if(!reader)throw Error('Body required');let size=0;const parts=[];try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max)throw Error('Size bound');parts.push(value);}}catch(error){await reader.cancel().catch(()=>{});throw error;}const raw=new Uint8Array(size);let offset=0;for(const part of parts){raw.set(part,offset);offset+=part.byteLength;}return new TextDecoder('utf-8',{fatal:true}).decode(raw);}
export function createPublishedUpvoteTargets({fetcher=globalThis.fetch,now=()=>Date.now()}={}){
 let cached=null,pending=null,expires=0;
 return async()=>{if(cached&&now()<expires)return cached;if(pending)return pending;pending=(async()=>{const response=await fetcher(INDEX_URL,{redirect:'manual',cache:'no-cache',signal:AbortSignal.timeout(5000)});if(!response.ok||!/^application\/json(?:\s*;|$)/i.test(response.headers.get('content-type')||''))throw Error('Published targets unavailable');const data=JSON.parse(await bytes(response,INDEX_BYTES));if(!exact(data,['schema','ids'])||data.schema!=='liberpedia-published-record-ids-v1'||!Array.isArray(data.ids)||data.ids.length>10000)throw Error('Invalid published targets');const ids=new Set();for(const id of data.ids){if(!validId(id)||IDEA.test(id)||ids.has(id))throw Error('Invalid published target');ids.add(id);}cached=ids;expires=now()+60000;return cached;})();try{return await pending;}finally{pending=null;}};
}
export function createUpvoteHandler({fetcher=globalThis.fetch,loadPublishedIds=createPublishedUpvoteTargets({fetcher}),crypto:cryptoAPI=globalThis.crypto,now=()=>new Date()}={}){
 return async(request,env)=>{
  const allowed=env?.SITE_ORIGIN,headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'},reply=(value,status=200)=>new Response(JSON.stringify(value),{status,headers});
  let configured=false;try{configured=typeof allowed==='string'&&new URL(allowed).origin===allowed&&['http:','https:'].includes(new URL(allowed).protocol);}catch{}
  if(!configured)return reply({error:'Upvotes are unavailable.'},503);if(request.headers.get('origin')!==allowed)return reply({error:'Request is not allowed.'},403);headers['Access-Control-Allow-Origin']=allowed;
  const url=new URL(request.url);if(url.pathname!=='/upvotes')return reply({error:'Not found.'},404);
  if(request.method==='OPTIONS'){const method=request.headers.get('access-control-request-method'),hs=(request.headers.get('access-control-request-headers')||'').split(',').map(v=>v.trim().toLowerCase()).filter(Boolean);if(!['GET','POST'].includes(method)||hs.some(h=>h!=='content-type'))return reply({error:'Request is not allowed.'},403);return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600'}});}
  if(!['GET','POST'].includes(request.method)){headers.Allow='GET, POST, OPTIONS';return reply({error:'Method is not allowed.'},405);}
  let ids,body;
  try{if(request.method==='GET'){if(url.searchParams.size!==1||url.searchParams.getAll('ids').length!==1||url.search.length>12000)throw Error();ids=url.searchParams.get('ids').split(',');if(!ids.length||ids.length>MAX_IDS||ids.some(id=>!validId(id))||new Set(ids).size!==ids.length)throw Error();}
   else{if(url.search||!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type')||''))throw Error();const raw=await bytes(request,MAX_BODY);body=JSON.parse(raw);if(!exact(body,['recordId','token','active'])||!validId(body.recordId)||typeof body.token!=='string'||!TOKEN.test(body.token)||typeof body.active!=='boolean'||(raw.match(/"(?:[^"\\]|\\.)*"/g)||[]).length!==5)throw Error();ids=[body.recordId];}
  }catch{return reply({error:'Choose valid records and an explicit upvote setting.'},400);}
  const db=env?.PROPOSALS,rate=env?.TASK_LIMIT||env?.PROPOSAL_LIMIT;if(!db?.prepare||!rate?.limit||!cryptoAPI?.subtle)return reply({error:'Upvotes are unavailable.'},503);
  try{
   if(!(await rate.limit({key:'upvotes:'+(request.headers.get('CF-Connecting-IP')||'unknown')}))?.success)return reply({error:'Upvote request limit reached. Try again later.'},429);
   const published=ids.some(id=>!IDEA.test(id))?await loadPublishedIds():new Set(),actual=new Set(ids.filter(id=>published.has(id))),community=ids.filter(id=>IDEA.test(id));
   if(community.length){const rows=await db.prepare('SELECT i.proposal_id FROM research_ideas i JOIN proposals p ON p.id=i.proposal_id WHERE i.proposal_id IN ('+community.map(()=>'?').join(',')+')').bind(...community.map(id=>'p_'+IDEA.exec(id)[1])).all();for(const row of rows.results||[])actual.add('idea-'+row.proposal_id.slice(2));}
   if(request.method==='GET'){
    const ordered=ids.filter(id=>actual.has(id));if(!ordered.length)return reply({schema:'liberpedia-upvotes-v1',counts:[],meaning:'interest'});
    const rows=await db.prepare('SELECT record_id,COUNT(*) AS count FROM record_upvotes WHERE record_id IN ('+ordered.map(()=>'?').join(',')+') GROUP BY record_id').bind(...ordered).all(),counts=new Map((rows.results||[]).map(row=>[row.record_id,Number(row.count)]));return reply({schema:'liberpedia-upvotes-v1',counts:ordered.map(recordId=>({recordId,count:counts.get(recordId)||0})),meaning:'interest'});
   }
   if(!actual.has(body.recordId))return reply({error:'This research entry is not available.'},404);
   const voterHash=[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode('liberpedia-upvote-v1:'+body.token)))].map(v=>v.toString(16).padStart(2,'0')).join('');
   if(body.active)await db.prepare('INSERT INTO record_upvotes(record_id,voter_hash,created_at) VALUES(?,?,?) ON CONFLICT(record_id,voter_hash) DO NOTHING').bind(body.recordId,voterHash,now().toISOString()).run();else await db.prepare('DELETE FROM record_upvotes WHERE record_id=? AND voter_hash=?').bind(body.recordId,voterHash).run();
   const row=await db.prepare('SELECT COUNT(*) AS count,COALESCE(MAX(CASE WHEN voter_hash=? THEN 1 ELSE 0 END),0) AS active FROM record_upvotes WHERE record_id=?').bind(voterHash,body.recordId).first();return reply({recordId:body.recordId,count:Number(row.count),active:row.active===1});
  }catch{return reply({error:'Upvotes are temporarily unavailable.'},503);}
 };
}
