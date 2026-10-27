/* Generated procedure proposals. Validation never grants execution or user confirmation. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare;
 const SCHEMA='liberpedia-method-design-v1',fields=['schema','name','hypothesis','pages','inputVersion','representation','keyUse','steps','parameters','evaluation','controls','assumptions'];
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const stringSchema=max=>({type:'string',minLength:1,maxLength:max});
 const strings=(min,max,length)=>({type:'array',minItems:min,maxItems:max,items:stringSchema(length)});
 const JSON_SCHEMA=freeze({type:'object',additionalProperties:false,required:fields,properties:{schema:{const:SCHEMA},name:stringSchema(80),hypothesis:stringSchema(500),pages:{type:'array',minItems:1,maxItems:75,uniqueItems:true,items:{type:'string',pattern:'^lp[12]-[0-9]{2}$'}},inputVersion:{enum:['raw','reviewed']},representation:stringSchema(160),keyUse:{type:'object',additionalProperties:false,required:['kind','material','application'],properties:{kind:{enum:['not-used','proposed']},material:{type:'string',maxLength:400},application:{type:'string',maxLength:500}}},steps:strings(1,8,500),parameters:{type:'array',maxItems:8,items:{type:'object',additionalProperties:false,required:['name','values'],properties:{name:stringSchema(60),values:strings(1,32,100)}}},evaluation:stringSchema(500),controls:strings(1,4,400),assumptions:strings(1,8,350)}});
 function ensure(ok,message){if(!ok)throw Error(message);}
 function exact(v,keys){return v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));}
 function text(v,max){ensure(typeof v==='string'&&v.trim().length>0&&Array.from(v).length<=max&&!/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u.test(v)&&!/[\ud800-\udfff]/u.test(v),'Use bounded plain Unicode text.');}
 function list(v,min,max,length){ensure(Array.isArray(v)&&v.length>=min&&v.length<=max,'Proposal list exceeds its bound.');v.forEach(x=>text(x,length));}
 function validate(input){
  const p=J.capture(input,{maxBytes:20*1024,maxDepth:8,maxNodes:3000});ensure(exact(p,fields)&&p.schema===SCHEMA,'Use the exact method-design schema.');
  for(const [key,max]of Object.entries({name:80,hypothesis:500,representation:160,evaluation:500}))text(p[key],max);
  ensure(Array.isArray(p.pages)&&p.pages.length>=1&&p.pages.length<=75&&new Set(p.pages).size===p.pages.length,'Use unique ordered proposal pages.');
  ensure(p.pages.every((id,i)=>i===0||p.pages[i-1]<id),'Proposal pages must use canonical page order.');
  p.pages.forEach(id=>ensure(typeof id==='string'&&id.length===6&&/^lp[12]-[0-9]{2}$/.test(id)&&Number(id.slice(4))<=(id[2]==='1'?16:57),'Use a maintained LP1 or LP2 page identifier.'));
  ensure(exact(p.keyUse,['kind','material','application']),'Specify whether and how key material is used.');
  if(p.keyUse.kind==='not-used')ensure(p.keyUse.material===''&&p.keyUse.application==='','A keyless proposal cannot carry key instructions.');
  else {ensure(p.keyUse.kind==='proposed','Use a maintained key-use state.');text(p.keyUse.material,400);text(p.keyUse.application,500);}
  ensure(['raw','reviewed'].includes(p.inputVersion),'Use raw or reviewed input.');list(p.steps,1,8,500);list(p.controls,1,4,400);list(p.assumptions,1,8,350);
  ensure(Array.isArray(p.parameters)&&p.parameters.length<=8,'Use at most eight finite parameter lists.');p.parameters.forEach(v=>{ensure(exact(v,['name','values']),'Use an exact finite parameter.');text(v.name,60);list(v.values,1,32,100);});
  return freeze(p);
 }
 function format(input){
  const p=validate(input);return ['Generated procedure proposal: '+p.name,'Hypothesis: '+p.hypothesis,'Proposed pages (in order): '+p.pages.map(id=>id.toUpperCase()).join(', '),'Input: '+p.inputVersion,'Representation: '+p.representation,...(p.keyUse.kind==='not-used'?['No key used.']:['Key material: '+p.keyUse.material,'How the key is applied: '+p.keyUse.application]),'Proposed procedure:',...p.steps.map((s,i)=>(i+1)+'. '+s),'Finite parameters:',...(p.parameters.length?p.parameters.map(v=>v.name+': '+v.values.join(' | ')):['None proposed.']),'Proposed evaluation: '+p.evaluation,'Proposed controls:',...p.controls.map((s,i)=>(i+1)+'. '+s),'Assumptions requiring review:',...p.assumptions.map((s,i)=>(i+1)+'. '+s)].join('\n');
 }
 async function toDraft(input,options,crypto=root.crypto){
  const p=validate(input),parent=J.capture(options,{maxBytes:20*1024,maxDepth:24,maxNodes:5000});ensure(exact(parent,['parentId','parentCard'])&&typeof parent.parentId==='string'&&/^p_[a-f0-9]{64}$/.test(parent.parentId)&&parent.parentId.length===66,'Use an exact canonical parent reference.');
  const bytes=new TextEncoder().encode(JSON.stringify(parent.parentCard));let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
  const fragment='#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');const card=H.readCard(fragment);ensure(C.serialize(card)===C.serialize(parent.parentCard),'The parent card is not canonical.');
  ensure(crypto?.subtle,'SHA-256 is required for the parent identity.');const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(C.serialize(card))))).map(b=>b.toString(16).padStart(2,'0')).join('');ensure(parent.parentId==='p_'+digest,'The parent identity changed.');
  const full=format(p),supplied=value=>C.field('specified',value,{kind:'supplied',refs:['source:text']}),original=H.decode(fragment).draft;
  return C.createDraft({source:{text:full+'\n\nParent question: '+parent.parentId+'\nParent canonical context (not a claim of equivalent procedure):\n'+original.source.text},aim:card.outcome,method:supplied({operations:[{id:'described_method',label:p.name,sourceText:full}]}),scope:supplied({pages:p.pages}),rules:{inputVersion:supplied(p.inputVersion),representation:supplied(p.representation),searchProtocol:supplied({kind:'method-design',version:1,parentId:parent.parentId,proposal:p}),evaluation:supplied({kind:'method-design-evaluation',description:p.evaluation})},unresolved:[]});
 }
 function readCaptured(value){
  const protocol=value?.rules?.searchProtocol;
  if(protocol?.status!=='specified'||!protocol.value||typeof protocol.value!=='object'||protocol.value.kind!=='method-design'){
   ensure(value?.rules?.evaluation?.value?.kind!=='method-design-evaluation'&&!(protocol?.value&&typeof protocol.value==='object'&&(protocol.value.proposal?.schema===SCHEMA||typeof protocol.value.kind==='string'&&protocol.value.kind.startsWith('method-design'))),'A method-design evaluation needs its complete proposal.');return null;
  }
  const metadata=protocol.value;ensure(exact(metadata,['kind','version','parentId','proposal'])&&metadata.version===1&&typeof metadata.parentId==='string'&&metadata.parentId.length===66&&/^p_[a-f0-9]{64}$/.test(metadata.parentId),'Use exact method-design metadata.');
  ensure(Array.isArray(value.unresolved)&&value.unresolved.length===0,'A structured proposal cannot hide unresolved conditions.');
  const allowedRules=new Set(['inputVersion','representation','evaluation','searchProtocol']);ensure(exact(value.rules,C.RULES)&&Object.entries(value.rules).every(([key,field])=>allowedRules.has(key)||field?.status==='unspecified'),'A structured proposal cannot hide additional rules.');
  const proposal=validate(metadata.proposal),specified=(field,expected)=>field?.status==='specified'&&C.serialize(field.value)===C.serialize(expected),operations=value.method?.value?.operations;
  ensure(value.method?.status==='specified'&&exact(value.method.value,['operations'])&&Array.isArray(operations)&&operations.length===1,'The proposal method changed.');
  const operation=operations[0],keys=Object.hasOwn(operation||{},'sourceText')?['id','label','sourceText']:['id','label'];
  ensure(exact(operation,keys)&&operation.id==='described_method'&&operation.label===proposal.name&&(!Object.hasOwn(operation,'sourceText')||operation.sourceText===format(proposal)),'The proposal method changed.');
  ensure(specified(value.scope,{pages:proposal.pages})&&specified(value.rules.inputVersion,proposal.inputVersion)&&specified(value.rules.representation,proposal.representation),'The proposal inputs or scope changed.');
  ensure(specified(value.rules.evaluation,{kind:'method-design-evaluation',description:proposal.evaluation}),'The proposal evaluation changed.');
  return freeze({parentId:metadata.parentId,proposal});
 }
 function readDraft(draft){const captured=J.capture(draft,{maxBytes:128*1024,maxDepth:24,maxNodes:10000});ensure(captured?.schema===C.SCHEMA&&typeof captured.source?.text==='string'&&captured.aim&&typeof captured.aim==='object','Use a complete proposal draft.');return readCaptured(captured);}
 function readCard(input){
  const card=J.capture(input,{maxBytes:H.MAX_BYTES,maxDepth:24,maxNodes:10000});let binary='';for(const byte of new TextEncoder().encode(JSON.stringify(card)))binary+=String.fromCharCode(byte);
  const canonical=H.readCard('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''));ensure(C.serialize(card)===C.serialize(canonical),'Use a canonical proposal card.');return readCaptured(canonical);
 }
 function reviseDraft(input,newProposal){
  const original=J.capture(input,{maxBytes:128*1024,maxDepth:24,maxNodes:10000}),prior=readDraft(original);ensure(prior,'Review a structured method proposal before revising it.');
  const proposal=validate(newProposal),full=format(proposal),supplied=value=>C.field('specified',value,{kind:'user_clarification',refs:['source:text']}),source={...original.source,text:full+'\n\nParent question: '+prior.parentId+'\nThis generated procedure is a proposal, not the original author’s stated method.'};
  const draft=C.createDraft({source,aim:original.aim,method:supplied({operations:[{id:'described_method',label:proposal.name,sourceText:full}]}),scope:supplied({pages:proposal.pages}),rules:{inputVersion:supplied(proposal.inputVersion),representation:supplied(proposal.representation),evaluation:supplied({kind:'method-design-evaluation',description:proposal.evaluation}),searchProtocol:supplied({kind:'method-design',version:1,parentId:prior.parentId,proposal})},unresolved:[]});
  readCaptured(draft);return draft;
 }
 function fragmentForDraft(input){
  readDraft(input);const draft=J.capture(input,{maxBytes:128*1024,maxDepth:24,maxNodes:10000}),active=f=>f.status==='specified'?{status:f.status,value:f.value}:{status:f.status},outcome=active(draft.aim);
  if(outcome.status==='specified'){const aim=C.normalizeOutcome(draft.aim);outcome.value={outcomeId:aim.id,detail:aim.detail};}
  const method=active(draft.method);method.value={operations:method.value.operations.map(o=>({id:o.id,label:o.label}))};
  const payload={version:1,outcome,method,scope:active(draft.scope),rules:Object.fromEntries(C.RULES.map(k=>[k,active(draft.rules[k])])),unresolved:draft.unresolved};
  const bytes=new TextEncoder().encode(JSON.stringify(payload));ensure(bytes.length<=H.MAX_BYTES,'The proposed method exceeds the shared review byte bound.');let binary='';for(const b of bytes)binary+=String.fromCharCode(b);
  const fragment='#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');ensure(fragment.length<=H.MAX_URL,'The proposed review link exceeds its bound.');readCard(H.readCard(fragment));ensure(H.decode(fragment).draft.status==='draft','Review must remain unconfirmed.');return fragment;
 }
 async function toFragment(input,options,crypto=root.crypto){return fragmentForDraft(await toDraft(input,options,crypto));}
 const api=Object.freeze({SCHEMA,JSON_SCHEMA,validate,format,toDraft,toFragment,readDraft,readCard,reviseDraft,fragmentForDraft});if(node)module.exports=api;else root.MethodDesign=api;
})(typeof globalThis!=='undefined'?globalThis:this);
