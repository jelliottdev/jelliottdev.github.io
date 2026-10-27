/* One offline import for batches of complete saved rune programs. No decoding/search. */
import {readFile,writeFile,stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import J from '../finite-json.js';
import {prepareRetainedRuneOutputs} from './retained_program_output.mjs';
import * as Collection from './retained_program_collection.mjs';

const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)
 &&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const need=(condition,message)=>{if(!condition)throw Error(message);};
const capture=value=>J.capture(value,{maxBytes:Collection.LIMITS.bytes,maxNodes:Collection.LIMITS.nodes,maxDepth:Collection.LIMITS.depth});

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
  const value=await prepareSavedPrograms(parseSavedPrograms(await readFile(source)));
  await writeFile(destination,E.stable(value)+'\n',{flag:'wx'});
  console.log('RETAINED '+value.programs.length+' complete saved programs; no missing output generated');
 }catch(error){console.error(error.message);process.exitCode=1;}
}
