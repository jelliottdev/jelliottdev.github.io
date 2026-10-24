/* Deterministic local-run archive. Packages data/source only; performs no I/O. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const encoder=new TextEncoder(),MAX_RUNNER=100000,MAX_TASK=2000000;
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
 async function build(task,runnerText,returnURL){
  // Snapshot before awaiting identity: later caller edits cannot change members.
  E.validateTask(task);
  const snapshot=JSON.parse(JSON.stringify(task));
  await E.checkIdentity(snapshot);
  const address=returnAddress(returnURL,snapshot.taskId),runner=textBytes(runnerText,'Runner source',MAX_RUNNER);
  const taskBytes=textBytes(E.stable(snapshot)+'\n','Task',MAX_TASK);
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
 const api={build};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunPackage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
