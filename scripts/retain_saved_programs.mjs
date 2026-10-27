/* One offline import for batches of complete saved rune programs. No decoding/search. */
import {readFile,writeFile,stat,lstat,realpath,open} from 'node:fs/promises';
import {resolve,dirname,relative,isAbsolute,join} from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import J from '../finite-json.js';
import {prepareRetainedRuneOutputs} from './retained_program_output.mjs';
import * as Collection from './retained_program_collection.mjs';

const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)
 &&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const need=(condition,message)=>{if(!condition)throw Error(message);};
const capture=value=>J.capture(value,{maxBytes:Collection.LIMITS.bytes,maxNodes:Collection.LIMITS.nodes,maxDepth:Collection.LIMITS.depth});
export const REFERENCE_LIMITS=Object.freeze({sources:128*75,bytes:Collection.LIMITS.bytes,nodes:Collection.LIMITS.nodes,depth:24,pointerLength:512,pointerSegments:24});

function pointerParts(pointer){
 need(typeof pointer==='string'&&pointer.length<=REFERENCE_LIMITS.pointerLength
  &&(pointer===''||pointer.startsWith('/')),'Use a bounded literal JSON pointer');
 const parts=pointer===''?[]:pointer.slice(1).split('/');
 need(parts.length<=REFERENCE_LIMITS.pointerSegments&&parts.every(part=>!/~(?![01])/u.test(part)), 'Invalid JSON pointer escape or depth');
 return parts.map(part=>part.replace(/~1/g,'/').replace(/~0/g,'~'));
}
function selectPointer(value,parts){
 for(const part of parts){
  need(value!==null&&typeof value==='object'&&Object.hasOwn(value,part)
   &&(!Array.isArray(value)||/^(?:0|[1-9][0-9]*)$/.test(part)),'Stored output JSON pointer does not select an existing value');
  value=value[part];
 }
 return value;
}
async function localPath(root,name){
 need(typeof name==='string'&&name.length>=6&&name.length<=300&&name.endsWith('.json')
  &&name.split('/').every(part=>/^[a-zA-Z0-9_.-]+$/.test(part)&&part!=='.'&&part!=='..'),
 'Stored output paths must be explicit record-local JSON files');
 let target=root;const parts=name.split('/');
 for(let i=0;i<parts.length;i++){
  target=join(target,parts[i]);const info=await lstat(target);
  need(!info.isSymbolicLink()&&(i===parts.length-1?info.isFile():info.isDirectory()),'Stored output paths cannot follow symbolic links or non-files');
 }
 const actual=await realpath(target),within=relative(root,actual);
 need(within&&!isAbsolute(within)&&!within.split(/[\\/]/).includes('..'),'Stored output path escaped its record directory');
 return actual;
}
async function readPinnedJSON(root,name,sha256,remaining){
 const target=await localPath(root,name),handle=await open(target,'r');
 try{
  const before=await handle.stat();need(before.isFile()&&before.size<=remaining,'Stored output sources exceed their total byte bound');
  const chunks=[];let size=0;
  while(true){const buffer=Buffer.alloc(Math.min(65536,remaining-size+1)),part=await handle.read(buffer,0,buffer.length,null);if(!part.bytesRead)break;size+=part.bytesRead;need(size<=remaining,'Stored output sources exceed their total byte bound');chunks.push(buffer.subarray(0,part.bytesRead));}
  const after=await handle.stat(),current=await lstat(target);
  need(before.dev===after.dev&&before.ino===after.ino&&before.size===after.size&&before.mtimeMs===after.mtimeMs
   &&current.dev===after.dev&&current.ino===after.ino&&await localPath(root,name)===target,'Stored output source changed while reading');
  const bytes=Buffer.concat(chunks,size);need(createHash('sha256').update(bytes).digest('hex')===sha256,'Stored output raw source hash changed');
  return bytes;
 }finally{await handle.close();}
}
function nodeCount(value){let count=0;const pending=[value];while(pending.length){const item=pending.pop();count++;if(item&&typeof item==='object')for(const child of Object.values(item))pending.push(child);}return count;}

export async function resolveSavedProgramOutputs(input,{root}={}){
 const value=capture(input);
 need(exact(value,['alphabet','pages','criterion','programs'])&&Array.isArray(value.programs)
  &&value.programs.length>=1&&value.programs.length<=Collection.LIMITS.programs
  &&Array.isArray(value.pages)&&value.pages.length>=1&&value.pages.length<=75&&Array.isArray(value.alphabet),
 'Supply a bounded saved-program manifest');
 const runeNames=new Set(value.alphabet.map(entry=>entry.rune));
 const counts=value.pages.map(page=>{need(page&&typeof page.id==='string'&&typeof page.text==='string','Saved page inputs are missing');return Array.from(page.text).filter(rune=>runeNames.has(rune)).length;});
 let references=0;const sources=new Map();
 for(const program of value.programs){
  const refs=Object.hasOwn(program,'outputRefs');
  need(exact(program,['id','title','steps','createdAt',refs?'outputRefs':'outputs']),'Use literal outputs or outputRefs exclusively');
  if(!refs)continue;
  need(Array.isArray(program.outputRefs)&&program.outputRefs.length===value.pages.length,'Every declared page needs one ordered stored output reference');
  for(let i=0;i<program.outputRefs.length;i++){
   const ref=program.outputRefs[i];need(exact(ref,['page','path','sha256','jsonPointer'])&&ref.page===value.pages[i].id
    &&typeof ref.sha256==='string'&&/^[a-f0-9]{64}$/.test(ref.sha256),'Use exact ordered stored output references and raw source hashes');
   pointerParts(ref.jsonPointer);references++;need(references<=REFERENCE_LIMITS.sources,'Too many stored output references');
   // Validate all path syntax before the first asynchronous file read.
   need(typeof ref.path==='string'&&ref.path.length>=6&&ref.path.length<=300&&ref.path.endsWith('.json')
    &&ref.path.split('/').every(part=>/^[a-zA-Z0-9_.-]+$/.test(part)&&part!=='.'&&part!=='..'),'Stored output paths must be explicit record-local JSON files');
   const prior=sources.get(ref.path);need(!prior||prior.sha256===ref.sha256,'Conflicting raw source pins');sources.set(ref.path,{sha256:ref.sha256});
  }
 }
 if(references){
  need(typeof root==='string'||root instanceof URL,'Stored output references need an explicit record directory');
  const directory=await realpath(root);need((await stat(directory)).isDirectory(),'Stored output root is not a directory');
  let bytes=0,nodes=0;
  for(const [name,source] of sources){
   const raw=await readPinnedJSON(directory,name,source.sha256,REFERENCE_LIMITS.bytes-bytes);bytes+=raw.length;
   source.value=parseSavedPrograms(raw);nodes+=nodeCount(source.value);need(nodes<=REFERENCE_LIMITS.nodes,'Stored output sources exceed their total node bound');
  }
 }
 const programs=value.programs.map(program=>{
  if(!Object.hasOwn(program,'outputRefs'))return program;
  const outputs=program.outputRefs.map((ref,index)=>{
   const values=selectPointer(sources.get(ref.path).value,pointerParts(ref.jsonPointer));
   need(Array.isArray(values)&&values.length===counts[index]&&values.every(v=>Number.isInteger(v)&&v>=0&&v<29),'Stored output must be the complete numeric rune array for its page');
   // Keep a temporary reference here: bounded capture below copies each selection
   // independently and rejects amplification before allocating unbounded copies.
   return {page:ref.page,values};
  });
  const {outputRefs,...metadata}=program;return {...metadata,outputs};
 });
 // Detach repeated selections and enforce the unchanged aggregate bound after expansion.
 return capture({...value,programs});
}

export async function prepareSavedPrograms(input){
 // A detached snapshot is the only source used after asynchronous validation.
 const value=capture(input);
 need(exact(value,['alphabet','pages','criterion','programs'])&&Array.isArray(value.programs)
  &&value.programs.length>=1&&value.programs.length<=Collection.LIMITS.programs,'Supply a bounded batch of complete saved programs');
 const seen=new Set();
 for(const program of value.programs){
  need(exact(program,['id','title','steps','createdAt','outputs'])&&typeof program.id==='string'
   &&program.id.length<=80&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?![\s\S])/.test(program.id)
   &&!seen.has(program.id),'Use unique named saved programs with exact fields');
  seen.add(program.id);
 }
 const programs=[];
 for(const program of value.programs){
  const task=await E.prepare({title:program.title,alphabet:value.alphabet,pages:value.pages,
   steps:program.steps,criterion:value.criterion});
  // This path consumes every saved value. The shared verifier rejects missing,
  // truncated or wrong vectors; it never substitutes newly decoded output.
  const retained=await prepareRetainedRuneOutputs({task,outputs:program.outputs,createdAt:program.createdAt});
  programs.push({id:program.id,taskId:task.taskId,title:task.title,steps:task.steps,
   createdAt:retained.run.createdAt,outputs:program.outputs,controls:retained.controls});
 }
 const collection={schema:Collection.SCHEMA,inputVersion:'raw',alphabet:value.alphabet,
  pages:value.pages,criterion:value.criterion,programs};
 // Shared aggregate validation also enforces exact alphabets, page ordering,
 // complete vectors and the same bounds as ordinary retained publication.
 Collection.prepare(collection);
 return collection;
}

export function parseSavedPrograms(bytes){
 need(bytes instanceof Uint8Array&&bytes.byteLength<=Collection.LIMITS.bytes,'Saved batch exceeds its byte bound');
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes),value=JSON.parse(text);
 const strings=text=>(text.match(/"(?:[^"\\]|\\.)*"/g)||[]).length;
 need(strings(text)===strings(JSON.stringify(value)),'Repeated saved-program JSON field');
 return capture(value);
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const args=process.argv.slice(2);
  need(args.length===4&&args[0]==='--input'&&args[2]==='--output','Use --input saved-programs.json --output retained-programs.json');
  const source=resolve(args[1]),destination=resolve(args[3]);
  need(source!==destination,'Keep the saved input and retained output separate');
  need((await stat(source)).size<=Collection.LIMITS.bytes,'Saved batch exceeds its byte bound');
  const input=await resolveSavedProgramOutputs(parseSavedPrograms(await readFile(source)),{root:dirname(source)});
  const value=await prepareSavedPrograms(input);
  await writeFile(destination,E.stable(value)+'\n',{flag:'wx'});
  console.log('RETAINED '+value.programs.length+' complete saved programs; no missing output generated');
 }catch(error){console.error(error.message);process.exitCode=1;}
}
