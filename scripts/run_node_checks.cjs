'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{createHash}=require('node:crypto'),{spawn}=require('node:child_process');
const ROOT=path.resolve(__dirname,'..'),DEFAULT_TIMEOUT=120000,MAX_TIMEOUT=600000;
function keys(value,allowed){return value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).every(k=>allowed.includes(k));}
function validateManifest(value){
 if(!keys(value,['schema','migration','checks'])||value.schema!=='liberpedia-node-checks-v1'||!Array.isArray(value.checks)||!value.checks.length)throw Error('Invalid Node check manifest');
 if(!keys(value.migration,['count','sha256'])||!Number.isInteger(value.migration.count)||value.migration.count<1||value.migration.count>value.checks.length||!/^[a-f0-9]{64}$/.test(value.migration.sha256))throw Error('Invalid migration snapshot');
 const seen=new Set();
 for(const check of value.checks){
  if(!keys(check,['args','timeoutMs','resources'])||!Array.isArray(check.args)||check.args.length<1||check.args.some(a=>typeof a!=='string'||!a||/[\0\r\n]/.test(a)))throw Error('Invalid check arguments');
  const args=check.args,script=args[0]==='--experimental-sqlite'?args[1]:args[0];
  if(args.length!==(args[0]==='--experimental-sqlite'?2:1)||!script||! /^(?:scripts|services\/idea-assistant)\/[a-zA-Z0-9_-]+\.(?:cjs|mjs)$/.test(script))throw Error('Unsupported Node check command');
  const id=JSON.stringify(args);if(seen.has(id))throw Error('Duplicate Node check: '+script);seen.add(id);
  if(check.timeoutMs!==undefined&&(!Number.isInteger(check.timeoutMs)||check.timeoutMs<1||check.timeoutMs>MAX_TIMEOUT))throw Error('Invalid timeout');
  if(check.resources!==undefined&&(!Array.isArray(check.resources)||check.resources.some(r=>typeof r!=='string'||! /^[a-zA-Z0-9_-]+$/.test(r))||new Set(check.resources).size!==check.resources.length))throw Error('Invalid resource locks');
 }
 const original=value.checks.slice(0,value.migration.count).map(check=>check.args);
 if(createHash('sha256').update(JSON.stringify(original)).digest('hex')!==value.migration.sha256)throw Error('Original Node checks changed; append new checks after the frozen migration prefix.');
 return value;
}
async function runChecks(checks,{workers=4,cwd=ROOT,executable=process.execPath,timeoutMs=DEFAULT_TIMEOUT,onResult=()=>{}}={}){
 if(!Number.isInteger(workers)||workers<1||workers>8)throw Error('Invalid worker count');
 if(!Number.isInteger(timeoutMs)||timeoutMs<1||timeoutMs>MAX_TIMEOUT)throw Error('Invalid timeout');
 const pending=checks.map((check,index)=>({check,index})),active=new Set(),locks=new Set(),results=[];
 async function execute({check,index}){
  const started=Date.now(),tempRoot=fs.realpathSync(os.tmpdir()),temp=fs.mkdtempSync(path.join(tempRoot,'liberpedia-node-check-'));let output='',truncated=false,timedOut=false;
  const append=chunk=>{const text=chunk.toString();if(output.length+text.length<=16*1024*1024)output+=text;else truncated=true;};
  let timer,hardTimer;
  try{
   const result=await new Promise(resolve=>{
    let child,spawnError;try{child=spawn(executable,check.args,{cwd,shell:false,env:{...process.env,TMPDIR:temp,TEMP:temp,TMP:temp},stdio:['ignore','pipe','pipe']});}catch(error){resolve({code:null,error:error.message});return;}
    child.stdout.on('data',append);child.stderr.on('data',append);
    child.on('error',error=>{spawnError=error.message;});
    child.on('close',(code,signal)=>resolve({code,signal,error:spawnError}));
    timer=setTimeout(()=>{timedOut=true;child.kill('SIGTERM');hardTimer=setTimeout(()=>child.kill('SIGKILL'),1000);},check.timeoutMs??timeoutMs);
   });
   return {index,args:check.args,...result,timedOut,output:output+(truncated?'\n[Output truncated at 16 MiB]\n':''),elapsedMs:Date.now()-started,passed:result.code===0&&!timedOut&&!result.error};
  }finally{
   clearTimeout(timer);clearTimeout(hardTimer);
   const target=fs.realpathSync(temp),relative=path.relative(tempRoot,target);
   if(!relative||path.isAbsolute(relative)||relative.split(path.sep).includes('..')||path.dirname(target)!==tempRoot||!path.basename(target).startsWith('liberpedia-node-check-'))throw Error('Unsafe temporary cleanup target');
   fs.rmSync(target,{recursive:true,force:true,maxRetries:3,retryDelay:100});
  }
 }
 while(pending.length||active.size){
  while(active.size<workers){
   const next=pending.findIndex(({check})=>(check.resources||[]).every(r=>!locks.has(r)));if(next<0)break;
   const item=pending.splice(next,1)[0];for(const r of item.check.resources||[])locks.add(r);
   const job=execute(item).catch(error=>({index:item.index,args:item.check.args,passed:false,error:error.message,output:'',elapsedMs:0})).then(result=>{results.push(result);onResult(result);}).finally(()=>{for(const r of item.check.resources||[])locks.delete(r);active.delete(job);});active.add(job);
  }
  if(active.size)await Promise.race(active);
 }
 return results.sort((a,b)=>a.index-b.index);
}
async function main(){
 const manifest=validateManifest(JSON.parse(fs.readFileSync(path.join(__dirname,'node-checks.json'),'utf8')));
 console.log('Running '+manifest.checks.length+' unconditional Node checks in 4 isolated processes.');
 const results=await runChecks(manifest.checks,{onResult:result=>{
  const command='node '+result.args.join(' ');console.log('::group::'+(result.passed?'PASS ':'FAIL ')+command+' ('+result.elapsedMs+' ms)');
  process.stdout.write(result.output);if(result.error)console.log(result.error);if(result.timedOut)console.log('Timed out');console.log('\n::endgroup::');
  if(!result.passed)console.log('::error::'+command+' failed'+(result.timedOut?' (timeout)':result.error?' (spawn/runner error)':' (exit '+result.code+')'));
 }});
 const failed=results.filter(r=>!r.passed);console.log('Node checks: '+(results.length-failed.length)+' passed, '+failed.length+' failed, '+results.filter(r=>r.timedOut).length+' timed out.');return failed.length?1:0;
}
module.exports={validateManifest,runChecks,main};
if(require.main===module)main().then(code=>{process.exitCode=code;}).catch(error=>{console.error(error);process.exitCode=1;});
