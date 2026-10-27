/* Self-contained V2 download. Export validates synthetic checks, never runs the target. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports;
 const V=node?require('./declarative-rune-program.js'):root.DeclarativeRuneProgram;
 const Controls=node?require('./declarative-plan-controls.js'):root.DeclarativePlanControls;
 const J=node?require('./finite-json.js'):root.FiniteJSON;
 const Zip=node?require('./local-run-package.js'):root.LocalRunPackage;
 const ORIGIN='https://jelliottdev.github.io',MAX_ZIP=16*1024*1024,encoder=new TextEncoder();
 const SOURCES=Object.freeze([{"path":"local-experiment.js","bytes":23602,"sha256":"2f1b9b18c2bb223215ba509aab31f101d992bb66305e300e7f6d8936af1b0426"},{"path":"finite-json.js","bytes":4221,"sha256":"84c7856112dbda25b672cc69d6f6b6ef134652f69ca411ffbacbf97b4d5257eb"},{"path":"declarative-rune-program.js","bytes":8175,"sha256":"399a1db0840cc94759afc2cc7ff1e0b95b9a638cc041b55247c6a9712c5b2574"},{"path":"declarative-plan-controls.js","bytes":11467,"sha256":"4989654ba52d8f12016dbeb919ac3067d23df1142f3ecf5e3211fa4f72cacb77"},{"path":"language-score.js","bytes":5750,"sha256":"e94976590207cf1464c4ecf68aa54ee5d1bff30ebbeca1ff9da9df96ee6b9635"},{"path":"language-model-data.js","bytes":1175650,"sha256":"bb5e15606af5dc60d4598c241040bf9f51213d3f64e0d4e3fde9fd474da510a2"}].map(pin=>Object.freeze(pin)));
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
 const ensure=(v,message)=>{if(!v)throw Error(message);};
 const capture=(v,maxBytes)=>J.capture(v,{maxBytes,maxDepth:24,maxNodes:2000000});
 const digest=async(bytes,crypto)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
 const RUNNER=String.raw`'use strict';
// Node 22+ and its standard library. No network, installation, uploads or generated code.
const fs=require('node:fs'),path=require('node:path'),{createHash,webcrypto}=require('node:crypto');
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const base=__dirname,MAX=16*1024*1024,hex=/^[a-f0-9]{64}$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const ensure=(v,m)=>{if(!v)throw Error(m);};
function read(name,max){const file=path.join(base,name),stat=fs.lstatSync(file);ensure(stat.isFile()&&!stat.isSymbolicLink()&&stat.size<=max,'Unsafe or oversized package file: '+name);return fs.readFileSync(file);}
(async()=>{
 ensure(process.argv.length===2,'Run node reproduce.cjs without arguments.');
 const manifest=JSON.parse(read('manifest.json',16000).toString('utf8'));
 ensure(exact(manifest,['schema','taskId','inputVersion','files'])&&manifest.schema==='liberpedia-declarative-run-package-v1'&&typeof manifest.taskId==='string'&&hex.test(manifest.taskId)&&['raw','reviewed'].includes(manifest.inputVersion),'Invalid package manifest.');
 const mandatory=['local-experiment.js','finite-json.js','declarative-rune-program.js','declarative-plan-controls.js','language-score.js','language-model-data.js','task.json','controls.json','reproduce.cjs','START.txt','package.json'];
 ensure(Array.isArray(manifest.files)&&[mandatory.length,mandatory.length+1].includes(manifest.files.length),'Invalid package members.');
 const expected=new Set([...mandatory,...(manifest.files.length>mandatory.length?['result.json']:[])]),bytes=new Map();let total=0;
 for(const entry of manifest.files){ensure(exact(entry,['path','bytes','sha256'])&&typeof entry.path==='string'&&expected.delete(entry.path)&&Number.isSafeInteger(entry.bytes)&&entry.bytes>=0&&entry.bytes<=8*1024*1024&&typeof entry.sha256==='string'&&hex.test(entry.sha256),'Invalid file commitment.');total+=entry.bytes;ensure(total<=MAX,'Package exceeds its byte budget.');const data=read(entry.path,entry.bytes);ensure(data.length===entry.bytes&&createHash('sha256').update(data).digest('hex')===entry.sha256,'Package file hash mismatch: '+entry.path);bytes.set(entry.path,data);}
 ensure(expected.size===0,'Missing package member.');
 // Hash every executable dependency before loading any packaged module.
 const V=require('./declarative-rune-program.js'),Controls=require('./declarative-plan-controls.js');
 const task=await V.checkIdentity(JSON.parse(bytes.get('task.json').toString('utf8')),webcrypto);ensure(task.taskId===manifest.taskId,'Manifest task mismatch.');
 await Controls.validate(JSON.parse(bytes.get('controls.json').toString('utf8')),task,webcrypto);
 let result;
 if(bytes.has('result.json')){const proof=await V.verify(task,JSON.parse(bytes.get('result.json').toString('utf8')),webcrypto);result=V.inspect(proof).result;}
 else result=V.run(task);
 const resultSha256=createHash('sha256').update(require('./local-experiment.js').stable(result)).digest('hex');
 console.log(JSON.stringify({taskId:task.taskId,resultSha256,pages:result.transformed.length,savedResultVerified:bytes.has('result.json')}));
 console.log('Exact computation and synthetic implementation checks only; no scientific reading or question-wide coverage is established.');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
`;
 const START='Reproduce this exact rune program\n\nExtract every file into one folder. Use Node.js 22 or later with no packages to install. Run:\n  node reproduce.cjs\n\nThis command checks all manifest file hashes before loading the packaged runtime, verifies the task identity and independent synthetic checks, then executes the exact target program. A packaged saved result is independently replayed and compared in full, including removed positions and retained input slots. It prints the canonical result SHA-256. Nothing is uploaded and no server is contacted.\n\nCreating this download did not execute the target. Any optional saved result still requires the offline replay. Raw/reviewed denotes the packaged source edition, not independent source authentication. Manifest hashes detect changed bytes; they are not a signature or proof that an untrusted archive is safe. Review sources before executing downloads.\n\nThis verifies computation only, not a reading, scientific conclusion or complete question coverage. Node execution can consume substantial memory for boundary-size tasks.\n';
 async function source(pin,fetcher,crypto,signal){
  const response=await fetcher(ORIGIN+'/'+pin.path,{redirect:'error',signal});ensure(response.ok,'The fixed runtime source is unavailable: '+pin.path);
  const declared=response.headers.get('Content-Length');ensure(declared===null||/^\d+$/.test(declared)&&Number(declared)<=2*1024*1024,'Invalid runtime transfer size.');
  const reader=response.body?.getReader();ensure(reader,'Missing runtime source bytes.');let length=0;const chunks=[];
  try{while(true){const {done,value}=await reader.read();if(done)break;length+=value.byteLength;ensure(length<=pin.bytes,'Runtime source exceeds its exact byte pin.');chunks.push(value);}}catch(error){await reader.cancel().catch(()=>{});throw error;}
  ensure(length===pin.bytes,'Runtime source size changed.');const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  ensure(await digest(bytes,crypto)===pin.sha256,'The fixed runtime source hash changed: '+pin.path);return bytes;
 }
 async function build(options){
  ensure(options&&typeof options==='object'&&!Array.isArray(options),'Use one exact package request.');const fields=Object.getOwnPropertyDescriptors(options),allowed=['task','inputVersion','controls','result','fetcher','crypto'];
  ensure(Object.keys(fields).every(k=>allowed.includes(k)&&Object.hasOwn(fields[k],'value'))&&['task','inputVersion','controls'].every(k=>Object.hasOwn(fields,k)),'Use exact data-only package fields.');
  const task=capture(fields.task.value,2000000),controls=capture(fields.controls.value,2*1024*1024),inputVersion=fields.inputVersion.value;
  const hasResult=Object.hasOwn(fields,'result'),result=hasResult?capture(fields.result.value,8*1024*1024):null;
  const crypto=fields.crypto?.value||root.crypto,fetcher=fields.fetcher?.value||root.fetch;
  ensure(['raw','reviewed'].includes(inputVersion)&&crypto?.subtle&&typeof fetcher==='function','Use a supported edition, SHA-256 and fixed-source transport.');
  await V.checkIdentity(task,crypto);await Controls.validate(controls,task,crypto);
  if(hasResult)ensure(exact(result,['schema','engine','runnerVersion','taskId','metrics','matches','transformed','alignment',...(task.criterion.kind==='language-score'?['languageScore']:[])])&&result.schema===V.RESULT&&result.engine===V.ENGINE&&result.runnerVersion===V.RUNNER_VERSION&&result.taskId===task.taskId,'The saved result belongs to another exact task.');
  const files=[],controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);
  try{for(const pin of SOURCES)files.push([pin.path,await Promise.race([source(pin,fetcher,crypto,controller.signal),new Promise((_,reject)=>{controller.signal.addEventListener('abort',()=>reject(Error('Runtime download timed out.')),{once:true});})])]);}finally{clearTimeout(timer);controller.abort();}
  files.push(['task.json',encoder.encode(stable(task)+'\n')],['controls.json',encoder.encode(stable(controls)+'\n')]);
  if(hasResult)files.push(['result.json',encoder.encode(stable(result)+'\n')]);
  files.push(['reproduce.cjs',encoder.encode(RUNNER)],['START.txt',encoder.encode(START)],['package.json',encoder.encode('{"type":"commonjs","private":true}\n')]);
  const commitments=[];for(const [path,bytes] of files)commitments.push({path,bytes:bytes.length,sha256:await digest(bytes,crypto)});
  const manifest={schema:'liberpedia-declarative-run-package-v1',taskId:task.taskId,inputVersion,files:commitments};files.push(['manifest.json',encoder.encode(JSON.stringify(manifest)+'\n')]);
  const zip=Zip.zipFiles(files,{maxBytes:MAX_ZIP});return Object.freeze({blob:new Blob([zip],{type:'application/zip'}),filename:'rune-program-v2-'+task.taskId+'.zip'});
 }
 const api=Object.freeze({build,SOURCES,MAX_ZIP});if(node)module.exports=api;else root.DeclarativeRunPackage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
