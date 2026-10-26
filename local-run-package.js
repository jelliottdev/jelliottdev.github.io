/* Deterministic local-run archive. Packages data/source only; performs no I/O. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const encoder=new TextEncoder(),MAX_RUNNER=100000,MAX_TASK=2000000;
 const Control=typeof module==='object'&&module.exports?require('./local-control.js'):root.LocalControl;
 const finiteRelation=()=>typeof module==='object'&&module.exports?require('./finite-origin-relation.js'):root.FiniteOriginRelation;
 const Checks=typeof module==='object'&&module.exports?require('./local-plan-controls.js'):root.LocalPlanControls;
 const GUARD_SHA256='101f8b36f754c56206a10c69ad7e0f645b88d7950f8513757e35ee7389b29938';
 const SUBSET_GUARD_SHA256='52ecb30ba4e0f3f504742f28c6ceda3eebbd4f8750841bbea407301292380e44';
 const AUTHORED_LANGUAGE_GUARD_SHA256='eab2836a1fa76b0cff973cb26a8b227a730e30844207345ae32249852533dd75';
 const PLAN_GUARD_SHA256='941dfccdc32b58f40cc39cf8caff18e77dd4d8c1ec486f3f94646a0fcb97cf7d';
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
 const hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 async function digest(bytes){const hash=await root.crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');}
 function originSnapshot(origins){
  if(!Array.isArray(origins)||origins.length>10)throw Error('Invalid authored origins.');
  for(const entry of origins){
   if(!exact(entry,['origin','control','question','scopeChange','limitation',...(Object.hasOwn(entry||{},'scopeRelation')?['scopeRelation']:[])])||!exact(entry.origin,['recordId','followupId','recordSha256','protocolSha256']))throw Error('Invalid authored origin fields.');
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
  if(!(production||local)||parsed.username||parsed.password||parsed.pathname!=='/run.html'||parsed.search||!(parsed.hash==='#task='+taskId||new RegExp('^#task='+taskId+'&idea=p_[a-f0-9]{64}$').test(parsed.hash))||value!==parsed.origin+'/run.html'+parsed.hash)throw Error('Invalid return URL.');
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
 // Shared bounded writer for local multipart exports; existing archive APIs
 // retain their own validation and behavior.
 function zipFiles(files,{maxBytes=32*1024*1024}={}){
  if(!Array.isArray(files)||!files.length||files.length>16384||!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>64*1024*1024)throw Error('Invalid bounded ZIP limits.');
  const seen=new Set();let total=22;
  for(const item of files){if(!Array.isArray(item)||item.length!==2)throw Error('Invalid ZIP member.');const [name,bytes]=item;
   if(typeof name!=='string'||name.length>200||!/^[a-zA-Z0-9._-]+(?:\/[a-zA-Z0-9._-]+)*$/.test(name)||name.split('/').some(p=>p==='.'||p==='..')||seen.has(name)||!ArrayBuffer.isView(bytes)||Object.prototype.toString.call(bytes)!=='[object Uint8Array]')throw Error('ZIP members need unique safe paths and byte arrays.');
   seen.add(name);total+=bytes.byteLength+76+2*encoder.encode(name).length;if(total>maxBytes)throw Error('The local ZIP part exceeds its byte limit.');
  }
  return zip(files);
 }
 // API: build(task, runnerText, returnURL, origins = [], guardText, runnerControls = null).
 // Generic checks add a fixed Python guard and the exact deterministic suite.
 // origins is the task service's public [{origin,control,question,scopeChange,
 // limitation}] projection. Nonempty origins require the exact fixed guard
 // source fetched from tools/verify_controls.py; empty origins need no fetch
 // and preserve the original three-member archive byte for byte.
 async function build(task,runnerText,returnURL,origins=[],guardText,runnerControls=null,languageModelText=null,subsetOptions=null,languageOptions=null){
  // Snapshot before awaiting identity: later caller edits cannot change members.
  E.validateTask(task);
  const snapshot=JSON.parse(JSON.stringify(task)),savedOrigins=originSnapshot(origins);
  const subsets=savedOrigins.filter(entry=>Object.hasOwn(entry,'scopeRelation'));
  if(subsets.length){for(const entry of subsets){const r=entry.scopeRelation;if(r?.kind==='finite-settings-member'){const FiniteRelation=finiteRelation();if(!FiniteRelation?.validate)throw Error('The finite-member relation validator is unavailable.');FiniteRelation.validate(r,snapshot);continue;}const id=/^(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))$/;if(!exact(r,['kind','declaredPages','remainingPages'])||r.kind!=='remaining-pages'||!Array.isArray(r.declaredPages)||!Array.isArray(r.remainingPages)||!r.remainingPages.length||r.declaredPages.length>75||r.declaredPages.length<=r.remainingPages.length||[r.declaredPages,r.remainingPages].some(values=>values.some(v=>typeof v!=='string'||!id.test(v))||new Set(values).size!==values.length||E.stable(values)!==E.stable([...values].sort()))||E.stable(r.remainingPages)!==E.stable(snapshot.pages.map(p=>p.id))||r.remainingPages.some(v=>!r.declaredPages.includes(v)))throw Error('Invalid remaining-page origin relation.');}
   if(runnerControls===null)throw Error('Remaining-page checks require both control suites.');
   const finite=subsets.some(entry=>entry.scopeRelation.kind==='finite-settings-member');if(!exact(subsetOptions,['subsetGuardText','planGuardText',...(finite?['finiteGuardText']:[])])||Object.values(Object.getOwnPropertyDescriptors(subsetOptions)).some(d=>!Object.hasOwn(d,'value')))throw Error('Remaining-page checks require the fixed subset and runner guards.');subsetOptions={subsetGuardText:subsetOptions.subsetGuardText,planGuardText:subsetOptions.planGuardText,...(finite?{finiteGuardText:subsetOptions.finiteGuardText}:{})};
  }else if(subsetOptions!==null)throw Error('Only remaining-page origins use subset guards.');
  if(runnerControls!==null&&savedOrigins.length&&!subsets.length&&snapshot.criterion.kind!=='language-score')throw Error('Choose the authored controls or the generic runner checks, not both.');
  const authoredLanguage=savedOrigins.length&&snapshot.criterion.kind==='language-score';
  if(authoredLanguage&&runnerControls===null)throw Error('Authored language comparisons require independent scorer checks.');
  if(authoredLanguage&&!subsets.length){if(!exact(languageOptions,['authoredLanguageGuardText','planGuardText']))throw Error('Authored language comparisons require both fixed guards.');languageOptions={...languageOptions};}
  else if(languageOptions!==null)throw Error('Only full authored language comparisons use a language guard.');
  if(runnerControls!==null&&!Checks?.validate)throw Error('Runner checks could not be loaded.');
  const savedChecks=runnerControls===null?null:await Checks.validate(runnerControls,snapshot,root.crypto);
  await E.checkIdentity(snapshot);
  const address=returnAddress(returnURL,snapshot.taskId),runner=textBytes(runnerText,'Runner source',MAX_RUNNER);
  const taskBytes=textBytes(E.stable(snapshot)+'\n','Task',MAX_TASK);
  const modelMembers=[];
  if(snapshot.criterion.kind==='language-score'){
   textBytes(languageModelText,'Language reference model',MAX_TASK);let model;
   try{model=JSON.parse(languageModelText);}catch{throw Error('The language reference model is malformed.');}
   if(!exact(model,['payload','sha256'])||model.sha256!==snapshot.criterion.modelSha256||await digest(encoder.encode(E.stable(model.payload)))!==snapshot.criterion.modelSha256)throw Error('The pinned language reference model changed.');
   modelMembers.push(['language-model.json',encoder.encode(E.stable(model)+'\n')]);
  }else if(languageModelText!==null)throw Error('This experiment does not use a language reference model.');
  if(savedOrigins.length){
   if(!['measurement','exact-prefix','exact-prefix-set','word-affine-count','word-prime-sums','language-score'].includes(snapshot.criterion.kind))throw Error('Authored controls require a supported evaluation.');
   const guard=textBytes(guardText,'Control guard source',MAX_RUNNER);
   if(await digest(guard)!==GUARD_SHA256)throw Error('The fixed control guard source changed.');
   const controls=new Map();
   for(const entry of savedOrigins){
    const c=entry.control;await E.checkIdentity(c.task);
    for(const key of ['steps','alphabet'])if(E.stable(c.task[key])!==E.stable(snapshot[key]))throw Error('The control uses a different '+key+'.');
    if(!Control.compatible(c.task,entry.scopeRelation?.kind==='finite-settings-member'?{...snapshot,criterion:{kind:'measurement'}}:snapshot))throw Error('The control uses an unsupported criterion.');
    const result=E.run(c.task);
    if(!Control.passed(c.task,result))throw Error('The synthetic control failed; target package not prepared.');
    if(await digest(encoder.encode(E.stable(result)))!==c.expected_result_sha256)throw Error('The complete synthetic control result changed.');
    controls.set(c.task.taskId,c.task);
   }
   if(subsets.length){
    const subsetGuard=textBytes(subsetOptions.subsetGuardText,'Subset control guard source',MAX_RUNNER),planGuard=textBytes(subsetOptions.planGuardText,'Runner guard source',MAX_RUNNER);
    if(await digest(subsetGuard)!==SUBSET_GUARD_SHA256||await digest(planGuard)!==PLAN_GUARD_SHA256)throw Error('The fixed remaining-page control guards changed.');
    const finiteMembers=[];if(subsets.some(entry=>entry.scopeRelation.kind==='finite-settings-member')){const finiteGuard=textBytes(subsetOptions.finiteGuardText,'Finite member guard source',MAX_RUNNER);if(await digest(finiteGuard)!==FINITE_AUDIT_SHA256)throw Error('The fixed finite member guard changed.');finiteMembers.push(['verify_finite_search.py',finiteGuard]);}
    const instructions='Remaining pages from a declared check\n\nTask ID: '+snapshot.taskId+'\n\nExtract every file, including the controls folder. Review task.json, origins.json, runner-controls.json and the fixed Python files.\nPython 3.9 or later and its standard library are sufficient.\n\nRun:\n  python verify_subset_controls.py --task task.json --origins origins.json --controls runner-controls.json --out results.json\n\nBoth the original authored known-answer controls and the task-bound runner checks must pass before any target page runs. A failure writes no target result. The command refuses to overwrite results.json.\nThe scope relation names only these remaining pages; it does not reproduce or claim results for other declared pages. Published provenance is preserved, not independently authenticated offline.\nNo network calls or automatic uploads occur.\nReturn manually to inspect or select results at:\n  '+address+'\n';
    return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],['origins.json',textBytes(E.stable({version:1,origins:savedOrigins})+'\n','Authored origins',MAX_TASK)],['verify_controls.py',guard],...Array.from(controls.entries()).sort((a,b)=>a[0].localeCompare(b[0])).map(([id,task])=>['controls/'+id+'.json',textBytes(E.stable(task)+'\n','Synthetic control',MAX_TASK)]),['runner-controls.json',textBytes(E.stable(savedChecks)+'\n','Runner checks',MAX_TASK)],['verify_plan_controls.py',planGuard],['verify_subset_controls.py',subsetGuard],...finiteMembers,...modelMembers]);
   }
   if(authoredLanguage){
    const languageGuard=textBytes(languageOptions.authoredLanguageGuardText,'Authored language guard source',MAX_RUNNER),planGuard=textBytes(languageOptions.planGuardText,'Runner guard source',MAX_RUNNER);
    if(await digest(languageGuard)!==AUTHORED_LANGUAGE_GUARD_SHA256||await digest(planGuard)!==PLAN_GUARD_SHA256)throw Error('The fixed authored language guards changed.');
    const instructions='Authored language comparison\n\nExtract every file, including the controls folder and language-model.json. Python 3.9 or later and the standard library are sufficient. The model contains derived FLORES-200 statistics under CC BY-SA 4.0; its attribution and conversion are recorded inside it.\n\nRun:\n  python verify_authored_language.py --task task.json --origins origins.json --controls runner-controls.json --out results.json\n\nThe complete synthetic transform witness and both independent scorer checks must pass before target pages run. No score threshold is a success condition. A failed check writes no target result. No network calls or automatic uploads occur. The command refuses to overwrite results.json. Published provenance is retained, not independently authenticated offline. A score does not identify a language or establish a decryption.\n\nReturn manually to inspect results at:\n  '+address+'\n';
    return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],['origins.json',textBytes(E.stable({version:1,origins:savedOrigins})+'\n','Authored origins',MAX_TASK)],['verify_controls.py',guard],...Array.from(controls.entries()).sort((a,b)=>a[0].localeCompare(b[0])).map(([id,task])=>['controls/'+id+'.json',textBytes(E.stable(task)+'\n','Synthetic control',MAX_TASK)]),['runner-controls.json',textBytes(E.stable(savedChecks)+'\n','Runner checks',MAX_TASK)],['verify_plan_controls.py',planGuard],['verify_authored_language.py',languageGuard],...modelMembers]);
   }
   const instructions='Local rune experiment with authored controls\n\nTask ID: '+snapshot.taskId+'\n\n'+
    'Extract every file, including the controls folder. Review task.json, origins.json and the Python files before running.\n'+
    'Python 3.9 or later is required. Only the Python standard library is used; nothing is installed.\n\n'+
    'From that folder, run:\n  python verify_controls.py --task task.json --origins origins.json --out results.json\n\n'+
    'The fixed guard independently checks each synthetic control identity, exact program and full result hash.\n'+
    (snapshot.criterion.kind==='word-affine-count'?'Every control must recover all planted relations with a lower random-order expectation before the target runs.':snapshot.criterion.kind==='word-prime-sums'?'Every control must reproduce its complete declared word-sum ledger before the target runs.':snapshot.criterion.kind==='measurement'?'Every control must match every rune of its declared known answer before the target runs.':'Every control must match its declared prefix before the target runs.')+' A failed control stops the command without writing target results.\n'+
    'The command refuses to overwrite results.json. Keep all packaged inputs and Python files unchanged.\n'+
    'This local calculation makes no network calls and uploads nothing automatically. The origins describe saved published provenance, not a live source check.\n'+
    'To return manually and select your results file, open:\n  '+address+'\n\n'+
    'A matching calculation or short prefix does not establish a decryption.\n';
   return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],
    ['origins.json',encoder.encode(E.stable({version:1,origins:savedOrigins})+'\n')],['verify_controls.py',guard],
    ...[...controls].map(([id,control])=>['controls/'+id+'.json',encoder.encode(E.stable(control)+'\n')])]);
  }
  if(savedChecks){
   if(!Checks?.validate)throw Error('Runner checks could not be loaded.');
   await Checks.validate(savedChecks,snapshot,root.crypto);
   const guard=textBytes(guardText,'Runner check guard source',MAX_RUNNER);
   if(await digest(guard)!==PLAN_GUARD_SHA256)throw Error('The fixed runner check guard source changed.');
   const instructions='Local rune experiment with runner checks\n\nTask ID: '+snapshot.taskId+'\n\n'+
    (modelMembers.length?'Extract every file into one folder, including language-model.json. The model contains derived FLORES-200 statistics under CC BY-SA 4.0; its source attribution and spelling conversion are recorded inside it.\n':'Extract all five files into one folder. Review task.json, runner-controls.json and the Python files before running.\n')+
    'Python 3.9 or later is required. Only the Python standard library is used; nothing is installed.\n\n'+
    'Run:\n  python verify_plan_controls.py --task task.json --controls runner-controls.json --out results.json\n\n'+
    'Two small synthetic inputs check the exact ordered method against independently calculated outputs before manuscript pages run.\n'+
    'Prefix checks use a synthetic known match and a mismatch; they do not establish that the manuscript matches a proposed reading.\n'+
    'A failed check stops without writing manuscript results. The command refuses to overwrite results.json.\n'+
    'Keep all packaged files unchanged. No network calls or automatic uploads are made.\n\n'+
    'Return manually and select the results file at:\n  '+address+'\n\n'+
    'These checks verify the stated computation on small inputs, not a decryption or statistical conclusion.\n';
   return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],
    ['runner-controls.json',textBytes(E.stable(savedChecks)+'\n','Runner checks',MAX_TASK)],['verify_plan_controls.py',guard],...modelMembers]);
  }
  const instructions='Local rune experiment\n\nTask ID: '+snapshot.taskId+'\n\n'+
   (modelMembers.length?'Extract every file into one folder, including language-model.json. The model contains derived FLORES-200 statistics under CC BY-SA 4.0; its source attribution and spelling conversion are recorded inside it.\n':'Extract all three files into one folder. Review task.json and research_runner.py before running.\n')+
   'Python 3.9 or later is required. Only the Python standard library is used; nothing is installed.\n\n'+
   'From that folder, run:\n  python research_runner.py --task task.json --out results.json\n\n'+
   'The runner refuses to overwrite an existing results.json. Keep task.json and the runner unchanged.\n'+
   'This local calculation makes no network calls and uploads nothing automatically.\n'+
   'To return manually and select your results file, open:\n  '+address+'\n\n'+
   'The return page verifies results against this exact task. A matching calculation does not establish a decryption.\n';
  return zip([['task.json',taskBytes],['research_runner.py',runner],['START.txt',encoder.encode(instructions)],...modelMembers]);
 }
 // Whole-search exports audit existing saved computations. They never run missing cases.
 const FINITE_RUNNER_SHA256='1943aa4d77263869e5890df09f93199cdc60f464c3e4b1643b5fa7a57fc59a32';
 const FINITE_AUDIT_SHA256='b7d76511d4dbc464468131382303944c1c7f88e8287d9df80024514ddb123de7';
 async function buildSnapshot(snapshot,runnerText,auditText){
  const S=typeof module==='object'&&module.exports?require('./finite-search-snapshot.js'):root.FiniteSearchSnapshot;
  if(!S?.inspect)throw Error('The verified search snapshot could not be loaded.');
  const captured=S.inspect(snapshot),body=textBytes(E.stable(captured)+'\n','Search snapshot',S.MAX_BYTES),runner=textBytes(runnerText,'Runner source',MAX_RUNNER),audit=textBytes(auditText,'Search audit source',MAX_RUNNER);
  if(await digest(runner)!==FINITE_RUNNER_SHA256)throw Error('The fixed search runner source changed.');
  if(await digest(audit)!==FINITE_AUDIT_SHA256)throw Error('The fixed search audit source changed.');
  const instructions='Saved finite-search audit\n\nExtract all four files into one folder. Python 3.9 or later and its standard library are sufficient.\n\nRun:\n  python verify_finite_search.py snapshot.json\n\nThis independently replays the saved computations and checks the declared search and its coverage. It does not run missing cases, contact a server or upload anything.\nMissing cases mean absent from these packaged receipts, not that nobody has tried them. A matching opening is not a complete decryption. Original source dates are retained, not independently authenticated.\n';
  return zip([['snapshot.json',body],['research_runner.py',runner],['verify_finite_search.py',audit],['START.txt',encoder.encode(instructions)]]);
 }
 const api={build,buildSnapshot,zipFiles,GUARD_SHA256,AUTHORED_LANGUAGE_GUARD_SHA256,PLAN_GUARD_SHA256,SUBSET_GUARD_SHA256,FINITE_AUDIT_SHA256,FINITE_RUNNER_SHA256};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunPackage=api;
})(typeof globalThis!=='undefined'?globalThis:this);
