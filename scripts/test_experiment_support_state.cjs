/* Deferred support loads must not close guides or replace focused links. No browser. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Model the relevant DOM serialization difference: quotes in text need no entities.
const normalize=html=>html.split(/(<[^>]*>)/).map(part=>part.startsWith('<')?part:part.replaceAll('&quot;','"').replaceAll('&#39;',"'")).join('');
function element(context,initial=''){
 let html=normalize(initial);
 return {writes:0,get innerHTML(){return html},set innerHTML(value){
  html=normalize(value);this.writes++;
  if(context.document.activeElement?.parent===this)context.document.activeElement=null;
 }};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function checkLoads(navigate=false){
 const pending=new Map(),record={id:'test-record'},other={id:'other-record'};
 const context={esc,AbortController,setTimeout,clearTimeout,
  location:{hash:'#/experiments/test-record'},document:{activeElement:null},
  fetch:url=>new Promise(resolve=>pending.set(url,resolve))};
 let slot=element(context);
 context.document.getElementById=id=>id==='experiment-method-guides'?slot:null;
 context.document.createElement=()=>element(context);
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
 context.records=[record,other];vm.runInContext('experimentRecords=records;startExperimentSupport()',context);
 const finish=async(name,data)=>{pending.get('data/'+name+'.json')({ok:true,json:async()=>data});await flush()};
 if(navigate){context.location.hash='#/research';slot=null;}
 await finish('method-families',{families:[{id:'test',related:['test-record'],guide:'test-guide',
  title:'A "quoted" guide',description:'Visible guide'}]});
 if(navigate){
  slot=element(context);context.location.hash='#/experiments/other-record';
 }else{
  assert.equal(slot.writes,1);assert(slot.innerHTML.startsWith('<h3>Method guides</h3>'));
  assert(!slot.innerHTML.includes('<details'),'No fresh nested collapsed panel');
  const expected=context.experimentMethodGuidesContent(record);
  assert.equal(slot.innerHTML,normalize(expected),'Late and initial guide content have the same shape');
  context.document.activeElement={parent:slot,id:'guide-link'};
 }
 const focused=context.document.activeElement,writes=slot.writes;
 await finish('idea-coverage',{records:[]});
 await finish('reported-attempts',{entries:[]});
 await finish('assistant',{});
 assert.equal(slot.writes,writes,'Unrelated support completions do not replace unchanged markup');
 assert.equal(context.document.activeElement,focused,'Focused links survive later resource loads');
 if(navigate)assert.equal(slot.innerHTML,'','An old record response cannot insert its guides into the new record');
 else assert(slot.innerHTML.includes('Visible guide'));
}
(async()=>{await checkLoads();await checkLoads(true);console.log('Experiment support state tests passed');})().catch(error=>{console.error(error);process.exitCode=1});
