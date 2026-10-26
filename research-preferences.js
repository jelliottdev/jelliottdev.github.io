/* Browser-only saved research and acknowledged upvote selections. No network,
 * accounts, fingerprinting, evidence authority or token generation at startup. */
(function(root){
 'use strict';
 const KEY='liberpedia-research-preferences-v1',TOKEN_KEY='liberpedia-anonymous-vote-token-v1',LIMITS=Object.freeze({saved:2000,upvoted:2000,textLength:512000,idLength:100});
 const HEX=/^[a-f0-9]{64}$/,SLUG=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>{const descriptor=Object.getOwnPropertyDescriptor(value,key);return descriptor&&descriptor.enumerable&&Object.hasOwn(descriptor,'value');});
 function validId(value){return typeof value==='string'&&value.length>0&&value.length<=LIMITS.idLength&&SLUG.test(value)&&(!value.startsWith('idea-')||/^idea-[a-f0-9]{64}$/.test(value));}
 function id(value){if(!validId(value))throw Object.assign(Error('Choose an exact research record.'),{code:'invalid-id'});return value;}
 function failure(code,message){return Object.assign(Error(message),{code});}
 const empty=()=>({version:1,saved:[],upvoted:[]}),serialize=value=>JSON.stringify({version:1,saved:value.saved,upvoted:value.upvoted});
 function parse(raw){
  if(raw===null)return empty();if(typeof raw!=='string'||raw.length>LIMITS.textLength)throw failure('storage-corrupt','Saved research preferences could not be read. They have not been changed.');
  let value;try{value=JSON.parse(raw);}catch{throw failure('storage-corrupt','Saved research preferences could not be read. They have not been changed.');}
  if(!exact(value,['version','saved','upvoted'])||value.version!==1)throw failure('storage-corrupt','Saved research preferences use an unsupported format. They have not been changed.');
  for(const key of ['saved','upvoted'])if(!Array.isArray(value[key])||value[key].length>LIMITS[key]||value[key].some(v=>!validId(v))||new Set(value[key]).size!==value[key].length||value[key].some((v,i)=>i&&value[key][i-1]>=v))throw failure('storage-corrupt','Saved research preferences could not be read. They have not been changed.');
  // Our own compact canonical format also rejects duplicate JSON keys, escaped
  // aliases and ambiguous externally rewritten state without deleting it.
  if(serialize(value)!==raw)throw failure('storage-corrupt','Saved research preferences could not be read. They have not been changed.');
  return value;
 }
 function create(options={}){
  let storage,crypto,listener;try{storage=Object.hasOwn(options,'storage')?options.storage:root.localStorage;crypto=Object.hasOwn(options,'crypto')?options.crypto:root.crypto;listener=options.onChange;}catch{}
  if(listener!==undefined&&typeof listener!=='function')throw failure('invalid-options','Use a preferences change callback.');
  let state='ready',message='',data=empty(),closed=false;
  const usable=storage&&typeof storage.getItem==='function'&&typeof storage.setItem==='function';
  function snapshot(){return Object.freeze({state,saved:Object.freeze([...data.saved]),upvoted:Object.freeze([...data.upvoted]),message});}
  function emit(before){const next=snapshot();if(before!==JSON.stringify(next))try{listener?.(next);}catch{}return next;}
  function ensureOpen(){if(closed)throw failure('destroyed','Research preferences are closed.');}
  function read(){if(!usable)throw failure('storage-unavailable','Browser storage is unavailable. Saved research cannot be kept on this device.');let raw;try{raw=storage.getItem(KEY);}catch{throw failure('storage-unavailable','Browser storage is unavailable. Saved research cannot be kept on this device.');}return parse(raw);}
  function setError(error){state=error.code==='storage-corrupt'?'corrupt':'unavailable';message=error.message;}
  function refresh(){ensureOpen();const before=JSON.stringify(snapshot());try{data=read();state='ready';message='';}catch(error){data=empty();setError(error);}return emit(before);}
  function update(key,recordId,active){ensureOpen();id(recordId);if(typeof active!=='boolean')throw failure('invalid-value','Choose whether this record is selected.');const before=JSON.stringify(snapshot());let next;try{next=read();const values=new Set(next[key]);if(active){if(!values.has(recordId)&&values.size>=LIMITS[key])throw failure('limit','The device limit of '+LIMITS[key]+' '+(key==='saved'?'saved records':'remembered upvotes')+' has been reached. No selection was removed.');values.add(recordId);}else values.delete(recordId);next[key]=[...values].sort();const raw=serialize(next);if(raw.length>LIMITS.textLength)throw failure('limit','Research preferences exceed the device limit. No selection was removed.');storage.setItem(KEY,raw);if(storage.getItem(KEY)!==raw)throw failure('storage-unavailable','This selection could not be confirmed in browser storage. Refresh before trying again.');data=next;state='ready';message='';emit(before);return active;}catch(error){const problem=['storage-unavailable','storage-corrupt','limit'].includes(error?.code)?error:failure('storage-unavailable','This selection could not be kept on your device. No saved selection was removed.');if(problem.code!=='limit')setError(problem);emit(before);throw problem;}}
  function toggleSaved(recordId){ensureOpen();id(recordId);let latest;try{latest=read();}catch(error){const before=JSON.stringify(snapshot());setError(error);emit(before);throw error;}return update('saved',recordId,!latest.saved.includes(recordId));}
  function voteToken(){ensureOpen();if(!usable)throw failure('storage-unavailable','Upvoting needs browser storage to remember an anonymous token.');let token;try{token=storage.getItem(TOKEN_KEY);}catch{throw failure('storage-unavailable','The anonymous vote token could not be read on this device.');}if(token!==null){if(typeof token!=='string'||!HEX.test(token))throw failure('storage-corrupt','The anonymous vote token is invalid. It has not been replaced.');return token;}if(!crypto||typeof crypto.getRandomValues!=='function')throw failure('crypto-unavailable','Secure anonymous voting is unavailable in this browser.');const bytes=new Uint8Array(32);try{crypto.getRandomValues(bytes);}catch{throw failure('crypto-unavailable','Secure anonymous voting is unavailable in this browser.');}const generated=[...bytes].map(v=>v.toString(16).padStart(2,'0')).join('');try{storage.setItem(TOKEN_KEY,generated);token=storage.getItem(TOKEN_KEY);}catch{throw failure('storage-unavailable','The anonymous vote token could not be kept on this device.');}if(typeof token!=='string'||!HEX.test(token))throw failure('storage-unavailable','The anonymous vote token could not be kept on this device.');return token;}
  function handleStorageEvent(event){if(closed||!event||event.storageArea&&event.storageArea!==storage||event.key!==KEY&&event.key!==null)return false;refresh();return true;}
  refresh();
  return Object.freeze({snapshot,isSaved:recordId=>{id(recordId);return data.saved.includes(recordId);},toggleSaved,isUpvoted:recordId=>{id(recordId);return data.upvoted.includes(recordId);},setUpvoted:(recordId,active)=>update('upvoted',recordId,active),voteToken,refresh,handleStorageEvent,destroy(){closed=true;listener=null;}});
 }
 const api={create,validId,KEY,TOKEN_KEY,LIMITS};if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchPreferences=api;
})(typeof globalThis!=='undefined'?globalThis:this);
