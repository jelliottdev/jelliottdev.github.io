/* Clipboard completion must stay with its original answer. No browser or API. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assistant-ui.js'),'utf8');
const start=source.indexOf('  function showAnswer(data){'),end=source.indexOf('  async function compare(idea){',start);
assert(start>=0&&end>start,'Locate the complete production answer renderer');
let button,resolveCopy,rejectCopy,copied;
const context={esc:String,status:{textContent:''},AssistantMarkdown:{render:answer=>answer},
 sourceExcerpt:()=>'',ideaSourceType:()=>'',
 $:selector=>{assert.equal(selector,'#idea-copy');return button},
 navigator:{clipboard:{writeText:text=>{copied=text;return new Promise((resolve,reject)=>{resolveCopy=resolve;rejectCopy=reject})}}},
 answer:{set innerHTML(value){if(button)button.isConnected=false;button={isConnected:true,textContent:'Copy answer'};}}
};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
const data={answer:'First comparison',sources:[{title:'Test record',href:'#/experiments/test',text:'Evidence'}]};
(async()=>{
 for(const failure of [false,true]){
  context.showAnswer(data);const original=button,pending=original.onclick();
  assert(copied.startsWith('First comparison'));assert(copied.includes('https://jelliottdev.github.io/#/experiments/test'));
  if(failure)rejectCopy(new Error('Clipboard denied'));else resolveCopy();await pending;
  assert.equal(original.textContent,failure?'Select answer to copy':'Copied','Current-answer copy reports success or fallback');
  context.showAnswer(data);const stale=button,oldCopy=stale.onclick();
  context.showAnswer({...data,answer:'New comparison'});const newer=button;
  if(failure)rejectCopy(new Error('Clipboard denied'));else resolveCopy();await oldCopy;
  assert.equal(newer.textContent,'Copy answer','Old completions do not change a new answer button');
  assert.equal(stale.textContent,'Copy answer','Detached elements are left untouched');
  const navigatedCopy=newer.onclick();newer.isConnected=false;button=null;
  if(failure)rejectCopy(new Error('Clipboard denied'));else resolveCopy();await navigatedCopy;
  assert.equal(button,null,'Navigation to a route without a copy button is safe');
 }
 console.log('PASS: actual answer copy success/fallback, replacement and navigation races; clipboard mocked.');
})().catch(error=>{console.error(error);process.exitCode=1});
