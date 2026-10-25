/* Work visible in this loaded research snapshot, never an archive-wide completeness claim. */
(function(root){
 'use strict';
 const Followups=typeof module==='object'&&module.exports?require('./record-followup-view.js'):root.RecordFollowupView;
 const HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/;
 function communityTasks(value){
  if(!value||!Number.isSafeInteger(value.taskCount)||value.taskCount<0||!Number.isSafeInteger(value.verifiedTaskCount)||value.verifiedTaskCount<0||value.verifiedTaskCount>value.taskCount||!Array.isArray(value.tasks)||value.tasks.length>10||value.tasks.length>value.taskCount)return null;
  const seen=new Set();let verified=0,pending=0;const tasks=[];
  for(const task of value.tasks){
   if(!task||typeof task!=='object'||Array.isArray(task)||Object.keys(task).length!==3||!Object.hasOwn(task,'id')||!Object.hasOwn(task,'title')||!Object.hasOwn(task,'state')||!HEX.test(task.id)||seen.has(task.id)||typeof task.title!=='string'||!task.title.trim()||Array.from(task.title).length>300||!['not-run','results-verified'].includes(task.state))return null;
   seen.add(task.id);if(task.state==='results-verified')verified++;else pending++;
   tasks.push({id:task.id,title:task.title,state:task.state});
  }
  const pendingCount=value.taskCount-value.verifiedTaskCount;
  if(verified>value.verifiedTaskCount||pending>pendingCount)return null;
  return {taskCount:value.taskCount,verifiedTaskCount:value.verifiedTaskCount,pendingCount,tasks};
 }
 function describe(record){
  if(!record||typeof record!=='object')return null;
  if(record.community===true){
   if(typeof record.proposal_id!=='string'||!IDEA.test(record.proposal_id)||record.id!=='idea-'+record.proposal_id.slice(2))return null;
   const work=communityTasks({taskCount:record.task_count,verifiedTaskCount:record.verified_task_count,tasks:record.task_summaries});
   if(!work||!work.pendingCount)return null;
   const first=work.tasks.find(t=>t.state==='not-run');
   return {kind:'unfinished',count:work.pendingCount,label:work.pendingCount===1?'1 unfinished experiment':work.pendingCount+' unfinished experiments',
    href:first?'run.html#task='+first.id:'run.html#idea='+record.proposal_id};
  }
  const recipes=Followups.recipes(record);if(!recipes.length)return null;
  return {kind:'prepared',count:recipes.length,label:recipes.length===1?'1 prepared follow-up':recipes.length+' prepared follow-ups',href:'run.html#record='+record.id+'&followup='+recipes[0].id};
 }
 function matches(record,filter){
  if(filter===''||filter==='all'||filter===undefined)return true;
  const kind=filter==='1'||filter==='prepared'?'prepared':filter==='pending'||filter==='unfinished'?'unfinished':null;
  return kind!==null&&describe(record)?.kind===kind;
 }
 const api={communityTasks,describe,matches};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchWork=api;
})(typeof globalThis!=='undefined'?globalThis:this);
