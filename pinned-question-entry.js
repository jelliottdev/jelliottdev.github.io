/* Plain links to two build-verified original questions. No saving or execution. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,Data=node?require('./pinned-question-entries-data.js'):root.PinnedQuestionEntriesData;
 const exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===k.length&&k.every(x=>Object.hasOwn(v,x)),text=(v,max)=>typeof v==='string'&&v.length>0&&v.length<=max&&!/[<>\u0000-\u001f\u007f]/.test(v),slug=v=>typeof v==='string'&&/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(v),esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function capture(){
  try{const data=J.capture(Data,{maxBytes:16384,maxDepth:6,maxNodes:100});const descriptors=Object.getOwnPropertyDescriptors(data);if(!exact(data,['schema','available','entries'])||Object.values(descriptors).some(d=>!d.enumerable||!Object.hasOwn(d,'value'))||data.schema!=='liberpedia-pinned-question-entries-v1'||typeof data.available!=='boolean'||!Array.isArray(data.entries)||data.entries.length!==2)return [];
   const seen=new Set();for(const e of data.entries){const d=Object.getOwnPropertyDescriptors(e);if(!exact(e,['sourceId','proposalId','recordId','title','description'])||Object.values(d).some(v=>!v.enumerable||!Object.hasOwn(v,'value'))||!slug(e.sourceId)||typeof e.proposalId!=='string'||!/^p_[a-f0-9]{64}$/.test(e.proposalId)||!slug(e.recordId)||!text(e.title,160)||!text(e.description,400)||seen.has(e.proposalId))return [];seen.add(e.proposalId);}return data;
  }catch{return null;}
 }
 const link=e=>Object.freeze({...e,href:'run.html#idea='+e.proposalId});
 function entries(record){const identity=record&&typeof record==='object'?Object.getOwnPropertyDescriptor(record,'id'):null;if(!identity?.enumerable||!Object.hasOwn(identity,'value')||!slug(identity.value))return [];const data=capture();return data?.available===true?data.entries.filter(e=>e.recordId===identity.value).map(link):[];}
 function forProposal(id){if(typeof id!=='string'||!/^p_[a-f0-9]{64}$/.test(id))return null;const entry=capture()?.entries.find(e=>e.proposalId===id);return entry?link(entry):null;}

 function render(record,{headingLevel=2}={}){const items=entries(record);if(!items.length)return '';const level=[2,3,4].includes(headingLevel)?headingLevel:2;return '<section class="record-questions pinned-question-entries" aria-labelledby="complete-question-heading"><h'+level+' id="complete-question-heading">Continue the rotating-key checks</h'+level+'><ul>'+items.map(e=>'<li><p class="record-question-title"><a href="'+esc(e.href)+'">'+esc(e.title)+'</a></p><p>'+esc(e.description)+'</p></li>').join('')+'</ul></section>';}
 const api=Object.freeze({entries,forProposal,render});if(node)module.exports=api;else root.PinnedQuestionEntry=api;
})(typeof globalThis==='undefined'?this:globalThis);
