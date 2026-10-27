/* Community entries are navigation objects, never published solving evidence. */
(function(root){
 'use strict';
 const Work=typeof module==='object'&&module.exports?require('./research-work.js'):root.ResearchWork;
 const C=typeof module==='object'&&module.exports?require('./claim-specification.js'):root.ClaimSpecification;
 const H=typeof module==='object'&&module.exports?require('./claim-share.js'):root.ClaimShare;
 const MD=typeof module==='object'&&module.exports?require('./method-design.js'):root.MethodDesign;
 const Starter=typeof module==='object'&&module.exports?require('./repeat-removal-start.js'):root.RepeatRemovalStart;
 const HEX=/^[a-f0-9]{64}$/,IDEA=/^p_[a-f0-9]{64}$/;
 const parents={'fixed-substitution':'method:substitution',polyalphabetic:'method:repeating-key',feedback:'method:feedback',transposition:'method:routes','prime-indices':'method:numeric','number-streams':'method:generated-key','book-codes':'method:running-key',repetition:'method:rune-patterns'};
 const routes={decipher:'solve-lp2',measure:'aim:understand',explain:'aim:understand',reproduce:'aim:validate',verify_source:'aim:sources'};
 function exact(o,keys){if(!o||typeof o!=='object'||Array.isArray(o)||Object.keys(o).some(k=>!keys.includes(k)))throw Error('Unexpected community fields.');}
 function decodeCard(card){
  const text=JSON.stringify(card);if(new TextEncoder().encode(text).length>H.MAX_BYTES)throw Error('Community card exceeds its bounds.');
  let binary='';for(const byte of new TextEncoder().encode(text))binary+=String.fromCharCode(byte);
  return H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')).draft;
 }
 function validate(feed){
  exact(feed,['schema','entries','nextCursor']);
  if(feed.schema!=='liberpedia-community-research-v1'||!Array.isArray(feed.entries)||feed.entries.length>50||!(feed.nextCursor===null||typeof feed.nextCursor==='string'&&/^[-_a-zA-Z0-9]{1,240}$/.test(feed.nextCursor)))throw Error('Invalid community feed.');
  const ids=new Set();
  for(const entry of feed.entries){
   exact(entry,['id','card','createdAt','tasks','taskCount','verifiedTaskCount','hasSharedComputation']);
   if(Object.hasOwn(entry,'hasSharedComputation')&&typeof entry.hasSharedComputation!=='boolean')throw Error('Invalid shared computation status.');
   if(!Work.communityTasks(entry))throw Error('Inconsistent community task counts or summaries.');
   if(!Number.isSafeInteger(entry.verifiedTaskCount)||entry.verifiedTaskCount<0||entry.verifiedTaskCount>entry.taskCount)throw Error('Invalid verified task count.');
   if(!IDEA.test(entry.id)||ids.has(entry.id)||!Number.isFinite(Date.parse(entry.createdAt))||!Array.isArray(entry.tasks)||entry.tasks.length>10||!Number.isSafeInteger(entry.taskCount)||entry.taskCount<entry.tasks.length)throw Error('Invalid community entry.');
   ids.add(entry.id);decodeCard(entry.card);const tasks=new Set();
   for(const task of entry.tasks){
    exact(task,['id','title','state']);
    if(!HEX.test(task.id)||tasks.has(task.id)||typeof task.title!=='string'||!task.title.trim()||Array.from(task.title).length>300||!['not-run','results-verified'].includes(task.state))throw Error('Invalid community task summary.');
    tasks.add(task.id);
   }
  }
  return feed;
 }
 function maintainedStarter(card){
  if(!MD?.readCard||!Starter?.match)return null;
  try{const source=MD.readCard(card);return source&&Starter.match(source.proposal)?source.proposal:null;}catch{return null;}
 }
 function label(record){return record.community?(Work.isFiniteQuestion(record)?'Review question':record.evidence_state==='computation-available'?'Computation available':'Untested idea'):null;}
 function merge(source,entries){
  // Validate in feed-sized batches without limiting previously loaded pages.
  const seen=new Set();for(let i=0;i<entries.length;i+=50)validate({schema:'liberpedia-community-research-v1',entries:entries.slice(i,i+50),nextCursor:null});
  const data=structuredClone(source),view=data.views.all,nodes=new Map(view.nodes.map(n=>[n.id,n]));
  if(!nodes.has('all-research'))throw Error('The research root is missing.');
  for(const entry of entries){
   if(seen.has(entry.id))throw Error('Repeated community idea.');seen.add(entry.id);
   const draft=decodeCard(entry.card),aim=C.normalizeOutcome(draft.aim),starter=maintainedStarter(entry.card),classified=starter?{familyIds:['repetition'],complete:true,operations:[]}:C.classifyMethod(draft.method),area=routes[aim.id]||'aim:unplaced';
   let parent=nodes.get(area)||nodes.get('aim:unplaced'),candidate=classified.familyIds.length===1?nodes.get(parents[classified.familyIds[0]]):null;
   if(classified.familyIds.length>1)candidate=nodes.get('method:combined');
   if(data.method_navigation){
    // Source material is not a cipher. Route literal finite streams by their
    // explicit non-repeating operation, not a number/book source-family tag.
    if(classified.familyIds.length===1&&classified.familyIds[0]==='number-streams'){
     const ops=classified.operations.map(row=>row.operation);
     candidate=ops.length&&ops.every(op=>['finite_key','finite_key_bank'].includes(op.id))?nodes.get('method:running-key'):null;
    }
    if(classified.familyIds.length===1&&classified.familyIds[0]==='book-codes')candidate=null;
    if(classified.familyIds.length===1&&classified.familyIds[0]==='prime-indices')candidate=nodes.get('method:direct-mapping');
   }
   if(starter&&area==='solve-lp2'){
    // A deletion rule is not a reordering, substitution or a different aim.
    // Add one shared operation family only when a matching decoding idea needs it.
    if(!nodes.has('method:rune-removal')){
     const solve=nodes.get('solve-lp2');
     if(solve){const family={id:'method:rune-removal',parent:solve.id,label:'Removing runes',color:solve.color,kind:'family',record_id:null,children:[],members:[],parent_basis:'maintained operation navigation'};solve.children.push(family.id);view.nodes.push(family);nodes.set(family.id,family);}
    }
    candidate=nodes.get('method:rune-removal');
   }
   if(!classified.complete)candidate=null;
   if(candidate){let ancestor=candidate;while(ancestor&&ancestor.id!==area)ancestor=nodes.get(ancestor.parent);if(ancestor)parent=candidate;}
   const id='idea-'+entry.id.slice(2);if(data.records[id]||nodes.has('record:'+id))throw Error('Community identity conflicts with a research record.');
   const operations=draft.method.status==='specified'?draft.method.value.operations:[];
   const description=starter?starter.name:operations.map(o=>o.label||o.sourceText||o.id).join(', then '),letters=Array.from(description),title=description?letters.slice(0,157).join('')+(letters.length>157?'…':''):'Unspecified research method';
   const evaluation=draft.rules.evaluation,check=evaluation.status==='specified'?C.evaluationText(evaluation.value):null;
   const choice=check?C.EVALUATION_CHOICES.find(item=>C.serialize(item.value)===C.serialize(evaluation.value)):null;
   const checkName=choice?choice.label:evaluation.status==='specified'&&evaluation.value?.kind==='exact-prefix-set'?'Compare supplied openings':null;
   const readableTitle=starter?starter.name:checkName?checkName+' · '+title:null;
   const readerTitle=readableTitle?Array.from(readableTitle).slice(0,109).join('')+(Array.from(readableTitle).length>109?'…':''):null;
   const pages=draft.scope.status==='specified'&&Array.isArray(draft.scope.value.pages)?draft.scope.value.pages:[];
   // Navigation metadata comes only from the decoded original card. It is not
   // a supplied feed flag or evidence that this finite question remains open.
   const bounds=draft.rules.searchBounds,finite=bounds.status==='specified'&&bounds.value?.kind==='finite-settings'&&bounds.value.version===1;
   const record={id,title,...(readerTitle?{reader_title:readerTitle}:{}),...(check&&Array.from(check).length<=280?{reader_intro:check}:{}),question:aim.detail||aim.wording||description,summary:description,community:true,proposal_id:entry.id,
    evidence_state:finite?'question-review':entry.verifiedTaskCount>0||entry.hasSharedComputation===true?'computation-available':'untested',created_at:entry.createdAt,...(finite?{finite_search:{kind:'finite-settings',version:1}}:{}),
    reader_finding:finite?'Open this question to see the saved evidence for its declared settings.':entry.verifiedTaskCount>0?'Saved checks are available. Open the idea to read their findings and exact page scope.':entry.hasSharedComputation===true?'Related saved calculations are available. Open the idea to check what they cover.':'No saved result is listed for this idea.',outcome:'',record_type:{id:'idea',label:'Community idea'},method_topics:classified.familyIds.map(id=>({id,title:C.METHOD_FAMILIES[id]})),
    pages,scope:{pages,representation:'',procedure:description,parameters:'',exclusions:''},href:'run.html#idea='+entry.id,task_count:entry.taskCount,verified_task_count:entry.verifiedTaskCount,task_summaries:structuredClone(entry.tasks)};
   data.records[id]=record;
   const node={id:'record:'+id,parent:parent.id,label:title,color:parent.color,kind:'record',record_id:id,children:[],members:[id],parent_basis:'confirmed idea navigation'};
   parent.children.push(node.id);view.nodes.push(node);nodes.set(node.id,node);
   for(let p=parent;p;p=nodes.get(p.parent))p.members.push(id);
  }
  data.community_count=entries.length;return data;
 }
 const api={validate,merge,label,decodeCard};if(typeof module==='object'&&module.exports)module.exports=api;else root.CommunityResearch=api;
})(typeof globalThis!=='undefined'?globalThis:this);
