/* Successful immutable compilation memo only. Not saved-card or source authority.
 * Callers MUST load the current original card from the database and fetch/check
 * the fresh official bundle on every request, before calling this helper.
 * No receipt/public association/lookup-completeness state is cached here. */
import Compiler from '../../factored-finite-search-compiler.js';
import Json from '../../finite-json.js';
import E from '../../local-experiment.js';
import Share from '../../claim-share.js';
export const LIMITS=Object.freeze({entries:3,bytes:8*1024*1024});
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key))&&Object.values(Object.getOwnPropertyDescriptors(value)).every(d=>d.enumerable&&Object.hasOwn(d,'value'));
const bytes=value=>new TextEncoder().encode(value).byteLength;
function createCompiler(compileMethod,{crypto=globalThis.crypto,maxEntries=LIMITS.entries,maxBytes=LIMITS.bytes}={}){
 if(!crypto?.subtle||!Number.isSafeInteger(maxEntries)||maxEntries<0||maxEntries>LIMITS.entries||!Number.isSafeInteger(maxBytes)||maxBytes<0||maxBytes>LIMITS.bytes)throw Error('Invalid factored compiler cache budget.');
 const entries=[];let retainedBytes=0;
 async function compile(options){
  if(!exact(options,['card','bundle']))throw Error('Compile the exact original card and fresh official bundle.');
  // Capture all caller data before the first await. The maintained compiler
  // performs canonical declaration/source checks; there is no second parser.
  const card=Json.capture(options.card,{maxBytes:Share.MAX_BYTES,maxDepth:16,maxNodes:6000}),bundle=Json.capture(options.bundle,{maxBytes:2*1024*1024,maxDepth:16,maxNodes:6000});
  const signature=E.stable({card,bundle}),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(signature)))].map(n=>n.toString(16).padStart(2,'0')).join('');
  const index=entries.findIndex(entry=>entry.digest===digest&&entry.signature===signature);
  if(index!==-1){const [entry]=entries.splice(index,1);entries.push(entry);return entry.compiled;}
  const compiled=await compileMethod(card,bundle,crypto),weight=bytes(signature)+bytes(E.stable(compiled))+bytes(digest)+128;
  // No pending promise or failed compile is retained. A too-large successful
  // compilation remains usable in full; it simply does not enter the memo.
  if(maxEntries&&weight<=maxBytes){
   // Concurrent exact compiles may finish together. Retain one canonical entry
   // without depending on or sharing another request's mutable/pending state.
   const existing=entries.findIndex(entry=>entry.digest===digest&&entry.signature===signature);
   if(existing!==-1){const [entry]=entries.splice(existing,1);entries.push(entry);return entry.compiled;}
   while(entries.length>=maxEntries||retainedBytes+weight>maxBytes)retainedBytes-=entries.shift().weight;
   entries.push({digest,signature,compiled,weight});retainedBytes+=weight;
  }
  return compiled;
 }
 return Object.freeze({compile});
}

export const createFactoredCompiler=options=>createCompiler(Compiler.compile,options);
export const createFactoredOutputCompiler=options=>createCompiler(Compiler.compileLanguageComparison,options);
export const createFactoredInspectionCompiler=options=>createCompiler(Compiler.compileOutputInspection,options);
