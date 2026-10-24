/* Deterministic local-run archive. Packages data/source only; performs no I/O. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const encoder=new TextEncoder(),MAX_RUNNER=100000,MAX_TASK=2000000;
 const Control=typeof module==='object'&&module.exports?require('./local-control.js'):root.LocalControl;
 const GUARD_SHA256='0d858588069fe403591e89629bbaa8eb3f94104771bef52689e96e80023ceec7';
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
 const hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 async function digest(bytes){const hash=await root.crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function originSnapshot(origins){
  if(!Array.isArray(origins)||origins.length>10)throw Error('Invalid authored origins.');
  for(const entry of origins){
   if(!exact(entry,['origin','control','question','scopeChange','limitation'])||!exact(entry.origin,['recordId','followupId','recordSha256','protocolSha256']))throw Error('Invalid authored origin fields.');
   for(const key of ['recordId','followupId'])if(typeof entry.origin[key]!=='string'||entry.origin[key].length>100||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.origin[key]))throw Error('Invalid authored origin identifier.');
   for(const key of ['recordSha256','protocolSha256'])if(!hex(entry.origin[key]))throw Error('Invalid authored origin hash.');
   for(const key of ['question','scopeChange','limitation'])if(typeof entry[key]!=='string'||!entry[key].trim()||Array.from(entry[key]).length>1200)throw Error('Invalid authored origin text.');
   const c=entry.control;if(!exact(c,['label','task','expected_result_sha256'])||typeof c.label!=='string'||!c.label.trim()||c.label.length>300||!/synthetic/i.test(c.label)||!hex(c.expected_result_sha256))throw Error('Invalid synthetic control.');
   E.validateTask(c.task);if(!/synthetic/i.test(c.task.title))throw Error('The control task must be labeled synthetic.');
  }
  const serialized=E.stable(origins);textBytes(serialized,'Authored origins',MAX_TASK);return JSON.parse(serialized);
 }
 const table=Uint32Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
 function crc32(bytes){let crc=0xffffffff;for(const byte of bytes)crc=table[(crc^byte)&255]^(crc>>>8);return (crc^0xffffffff)>>>0;}
 function textBytes(text,label,limit){
  if(typeof text!=='string'||!text.length)throw Error(label+' must contain text.');
  for(const ch of text){const code=ch.codePointAt(0);if(code>=0xd800&&code<=0xdfff)throw Error(label+' contains an invalid Unicode character.');}
  const bytes=encoder.encode(text);if(bytes.length>limit)throw Error(label+' exceeds its byte limit.');return bytes;
 }
 function returnAddress(value,taskId){
  if(typeof value!=='string')throw Error('Invalid return URL.');
  let parsed;try{parsed=new URL(value);}catch{throw Error('Invalid return URL.');}
  const production=parsed.protocol==='https:'&&parsed.hostname==='jelliottdev.github.io'&&!parsed.port;
  const local=parsed.protocol==='http:'&&['localhost','127.0.0.1'].includes(parsed.hostname);
  if(!(production||local)||parsed.username||parsed.password||parsed.pathname!=='/run.html'||parsed.search||parsed.hash!=='#task='+taskId||value!==parsed.origin+'/run.html#task='+taskId)throw Error('Invalid return URL.');
  return value;
 }
 function zip(files){
  const chunks=[],central=[];let offset=0,centralSize=0;
  for(const [filename,bytes]of files){
   const name=encoder.encode(filename),crc=crc32(bytes),header=new Uint8Array(30+name.length),view=new DataView(header.buffer);
   view.setUint32(0,0x04034b50,true);view.setUint16(4,20,true);view.setUint16(6,0x0800,true);view.setUint16(12,33,true);
   view.setUint32(14,crc,true);view.setUint32(18,bytes.length,true);view.setUint32(22,bytes.length,true);view.setUint16(26,name.length,true);header.set(name,30);
   const entry=new Uint8Array(46+name.length),cv=new DataView(entry.buffer);
   cv.setUint32(0,0x02014b50,true);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x0800,true);cv.setUint16(14,33,true);
   cv.setUint32(16,crc,true);cv.setUint32(20,bytes.length,true);cv.setUint32(24,bytes.length,true);cv.setUint16(28,name.length,true);cv.setUint32(42,offset,true);entry.set(name,46);
   chunks.push(header,bytes);central.push(entry);offset+=header.length+bytes.length;centralSize+=entry.length;
  }
  const end=new Uint8Array(22),ev=new DataView(end.buffer);ev.setUint32(0,0x06054b50,true);ev.setUint16(8,files.length,true);ev.setUint16(10,files.length,true);ev.setUint32(12,centralSize,true);ev.setUint32(16,offset,true);
  const result=new Uint8Array(offset+centralSize+end.length);let cursor=0;
  for(const part of [...chunks,...central,end]){result.set(part,cursor);cursor+=part.length;}return result;
 }
 // API: build(task, runnerText, returnURL, origins = [], guardText).
 // origins is the task service's public [{origin,control,question,scopeChange,
 // limitation}] projection. Nonempty origins require the exact fixed guard
 // source fetched from tools/verify_controls.py; empty origins need no fetch
 // and preserve the original three-member archive byte for byte.
 async function build(task,runnerText,returnURL,origins=[],guardText){
  // Snapshot before awaiting identity: later caller edits cannot change members.
  E.validateTask(task);
  const snapshot=JSON.parse(JSON.stringify(task)),savedOrigins=originSnapshot(origins);
  await E.checkIdentity(snapshot);
  const address=returnAddress(returnURL,snapshot.taskId),runner=textBytes(runnerText,'Runner source',MAX_RUNNER);
  const taskBytes=textBytes(E.stable(snapshot)+'\n','Task',MAX_TASK);
  if(savedOrigins.length){
   if(!['exact-prefix','word-affine-count'].includes(snapshot.criterion.kind))throw Error('Authored controls require a supported evaluation.');
   const guard=textBytes(guardText,'Control guard source',MAX_RUNNER);
   if(await digest(guard)!==GUARD_SHA256)throw Error('The fixed control guard source changed.');
   const controls=new Map();
   for(const entry of savedOrigins){
    const c=entry.control;await E.checkIdentity(c.task);
    for(const key of ['steps','alphabet','criterion'])if(E.stable(c.task[key])!==E.stable(snapshot[key]))throw Error('The control uses a different '+key+'.');
    const result=E.run(c.task);
    if(!Control.passed(c.task,result))throw Error('The synthetic control failed; target package not prepared.');
    if(await digest(encoder.encode(E.stable(result)))!==c.expected_result_sha256)throw Error('The complete synthetic control result changed.');
    controls.set(c.task.taskId,c.task);
   }
   const instructions='Local rune experiment with authored controls\n\nTask ID: '+snapshot.taskId+'\n\n'+
    'Extract every file, including the controls folder. Review task.json, origins.json and the Python files before running.\n'+
    'Python 3.9 or later is required. Only the Python standard library is used; nothing is installed.\n\n'+
    'From that folder, run:\n  python verify_controls.py --task task.json --origins origins.json --out results.json\n\n'+
    'The fixed guard independently checks each synthetic control identity, exact program and full result hash.\n'+
    (snapshot.criterion.kind==='word-affine-count'?'Every control must recover all planted relations with a lower random-order expectation before the target runs.':'Every control must match its declared prefix before the target runs.')+' A failed control stops the command without writing target results.\n'+
    'The command refuses to overwrite results.json. Keep all packaged inputs and Python files unchanged.\n'+
    'This local calculation makes no network calls and uploads nothing automatically. The origins describe saved published provenance, not a live source check.\n'+
    'To return manually and select your results file, open:\n  '+address+'\n\n'+
    'A matching calculation or short prefix does not establish a decryption.\n';
   return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],
    ['origins.json',encoder.encode(E.stable({version:1,origins:savedOrigins})+'\n')],['verify_controls.py',guard],
    ...[...controls].map(([id,control])=>['controls/'+id+'.json',encoder.encode(E.stable(control)+'\n')])]);
  }
  const instructions='Local rune experiment\n\nTask ID: '+snapshot.taskId+'\n\n'+
   'Extract all three files into one folder. Review task.json and research_runner.py before running.\n'+
   'Python 3.9 or later is required. Only the Python standard library is used; nothing is installed.\n\n'+
   'From that folder, run:\n  python research_runner.py --task task.json --out results.json\n\n'+
   'The runner refuses to overwrite an existing results.json. Keep task.json and the runner unchanged.\n'+
   'This local calculation makes no network calls and uploads nothing automatically.\n'+
   'To return manually and select your results file, open:\n  '+address+'\n\n'+
   'The return page verifies results against this exact task. A matching calculation does not establish a decryption.\n';
  return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)]]);
 }
 const api={build,GUARD_SHA256};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunPackage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
