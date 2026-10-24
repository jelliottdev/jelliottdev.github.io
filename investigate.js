/* Standalone confirmation/research flow. All research comes from the real registry. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'?require('./claim-specification.js'):root.ClaimSpecification;
 const M=typeof module!=='undefined'?require('./assistant-markdown.js'):root.AssistantMarkdown;
 const S=typeof module!=='undefined'?require('./assistant-search.js'):root.AssistantSearch;
 const H=typeof module!=='undefined'?require('./claim-share.js'):root.ClaimShare;
 const R=typeof module!=='undefined'?require('./claim-research.js'):root.ClaimResearch;
 const P=typeof module!=='undefined'?require('./claim-interpretation.js'):root.ClaimInterpretation;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const prov={kind:'supplied',refs:['original wording']};
 const known=v=>C.field('specified',v,prov);
 const editProvenance={kind:'user_clarification',refs:['interpretation editor']};
 const clarified=v=>C.field('specified',v,editProvenance);
 function parseScope(text,provenance=prov){
  if(!text.trim())return C.field();
  const selected=[];
  for(const item of text.toLowerCase().split(/\s*(?:,|;|\band\b)\s*/)){
   const match=item.trim().match(/^lp([12])-(\d{1,2})(?:\s*[-–—]\s*(?:lp\1-)?(\d{1,2}))?$/);
   if(!match)throw Error('Use exact page IDs, such as LP2-15, LP2-17 or LP2-15–17.');
   const start=Number(match[2]),end=match[3]===undefined?start:Number(match[3]);
   if(end<start||end-start>74)throw Error('Check the page range.');
   for(let i=start;i<=end;i++)selected.push('lp'+match[1]+'-'+String(i).padStart(2,'0'));
  }
  return C.field('specified',{pages:C.pages(selected)},provenance);
 }
 function initialDraft(text){
  // Recognize complete, tiny prose forms only. Substring recognition would
  // silently discard appended ciphers, conditions, keys and negative wording.
  // Conditions/negations/code stay opaque and fully visible, not "understood".
  const opaque=/\b(?:not|never|unless|except|excluding|exclude|avoid|if|when|without|only|instead|otherwise|but|until|provided)\b|\bdon['’]t\b|[`{}\n]/i.test(text);
  const rules={},unresolved=[];
  function recognized(piece){
   if(opaque)return null;
   let value=piece.trim().replace(/[.]$/,'');
   value=value.replace(/,?\s+(?:keeping|preserving|keep|preserve) word boundaries$/i,'');
   // Strip only an exact, independently valid trailing positive page clause.
   const on=value.match(/\s+on\s+(LP[12]-[^.!?]+)$/i);
   if(on){try{parseScope(on[1]);value=value.slice(0,on.index);}catch{}}
   if(/^reverse (?:the )?prime values (?:of|in) (?:each|every) row$/i.test(value))return {ambiguous:true,id:'ambiguous_reversal',label:piece,sourceText:piece};
   if(/^reverse (?:the )?(?:decimal )?digits of each (?:prime )?value(?: in (?:each|every) row)?$/i.test(value))return {
    id:'reverse_value_digits',label:/\bprime\b/i.test(value)?'Reverse decimal digits of each prime value':'Reverse decimal digits of each value',sourceText:piece};
   if(/^(?:read each row backwards|reverse (?:the )?(?:rune )?order within each row|reverse each row)$/i.test(value))return {id:'reverse_row_runes',label:'Reverse rune order within rows',sourceText:piece};
   return null;
  }
  // An explicit "then" supplies order, not a general program parse. Keep the
  // entire remaining phrase(s) as opaque operations, including their key/rules.
  const separator=opaque?null:/\s*[,;]?\s+then\s+/i.exec(text);
  // Split at most once. The tail may contain arbitrary code, quoted keys or
  // more steps: its complete wording stays together instead of being parsed.
  const pieces=separator?[text.slice(0,separator.index),text.slice(separator.index+separator[0].length)]:[text];
  const parsed=pieces.map(recognized);
  const hasKnown=parsed.some(Boolean);
  const operations=hasKnown?pieces.map((piece,index)=>{
   const operation=parsed[index]||{id:'described_method',label:piece,sourceText:piece};
   if(operation.ambiguous){unresolved.push({kind:'operation_ambiguity',operationIndex:index,text:piece,provenance:prov});delete operation.ambiguous;}
   return operation;
  }):[{id:'described_method',label:text,sourceText:text}];
  if(hasKnown&&/\b(?:keep(?:ing)?|preserv(?:e|ing)) word boundaries[.]?$/i.test(text))rules.wordBoundaries=known('preserve');
  // Recognize only fully qualified, explicit page IDs/ranges. A shorthand
  // continuation is kept unresolved instead of claiming a partial exact set.
  const refs=text.match(/\bLP[12]-\d{1,2}(?:\s*[-–—]\s*(?:LP[12]-)?\d{1,2})?/gi)||[];
  let scope=C.field();
  if(!opaque&&refs.length&&!/LP[12]-\d{1,2}\s*(?:and|,)\s*\d/i.test(text)){
   try{scope=parseScope(refs.join(','));}catch{/* Keep unknown and let the user edit. */}
  }
  // A page mention followed by an explicit passage qualifier is not a whole
  // page selection. Retain the source's qualifier as prose, without guessing
  // its numbering convention, endpoints or execution semantics.
  if(!opaque&&scope.status==='specified'){
   const passages=[...text.matchAll(/\bLP[12]-\d{1,2}\s*,?\s+(?:lines?|rows?|runes?|positions?|words?|paragraphs?|clauses?)\b[^.!?\n;]*/gi)]
    .map(match=>match[0].split(/,?\s+then\s+/i)[0].trim());
   if(passages.length)scope=known({...scope.value,description:passages.join('; ')});
  }
  if(!opaque&&/\ball (?:the )?unsolved LP2(?: pages)?\b/i.test(text))scope=known({pages:Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0'))});
  let aim=C.field();
  if(!opaque){
   const explicit=text.match(/\b(?:my\s+)?(?:aim|goal)\s*(?:is|:)\s*([^.!?\n]+)/i);
   if(explicit)aim=known(explicit[1].trim());
   else if(/^(?:I (?:want|would like) to\s+)?(?:solve|decipher|decrypt)\s+(?:LP2|Liber Primus|the (?:text|manuscript))\b/i.test(text.trim()))aim=known({outcomeId:'decipher',wording:text.trim(),detail:text.trim()});
   else if(/^(?:I (?:want|would like) to\s+)?(?:find|recover|produce) (?:readable (?:text|plaintext)|plaintext)\b/i.test(text.trim()))aim=known({outcomeId:'decipher',wording:text.trim(),detail:text.trim()});
   else if(/^(?:I (?:want|would like) to\s+)?(?:test|measure|check) (?:a |the )?statistical (?:effect|pattern|difference)\b/i.test(text.trim()))aim=known({outcomeId:'measure',wording:text.trim(),detail:text.trim()});
   else if(/^(?:I (?:want|would like) to\s+)?(?:reproduce|replicate|rerun)\b/i.test(text.trim()))aim=known({outcomeId:'reproduce',wording:text.trim(),detail:text.trim()});
  }
  let goalOnly=text.trim().replace(/[.!?]$/,'').replace(/^(?:I (?:want|would like) to\s+|(?:my\s+)?(?:aim|goal)\s*(?:is|:)\s*)/i,'');
  const goalScope=goalOnly.match(/\s+on\s+(.+)$/i);
  if(goalScope){try{if(!/^all (?:the )?unsolved LP2(?: pages)?$/i.test(goalScope[1]))parseScope(goalScope[1]);goalOnly=goalOnly.slice(0,goalScope.index);}catch{/* A method tail is not a scope suffix. */}}
  const goalCategory=C.normalizeOutcome(goalOnly),outcomeOnly=!opaque&&goalCategory.id!=='unclassified';
  if(outcomeOnly)aim=known({outcomeId:goalCategory.id,wording:text.trim(),detail:text.trim()});
  return C.createDraft({source:{text},aim,method:outcomeOnly?C.field():known({operations}),scope,rules,unresolved});
 }
 function intakeQuestions(draft){
  const result=C.questions(draft);
  const acknowledged=name=>draft.clarifications.some(c=>c.question===name&&c.choice==='undecided');
  if(draft.aim.status==='unspecified'&&!acknowledged('aim'))result.push({id:'aim',prompt:'What outcome are you looking for?',choices:[
   ...Object.entries(C.OUTCOMES).map(([id,label])=>({id,label})),
   {id:'unclassified',label:'None of these fits',requiresText:true,fieldLabel:'Describe the outcome you want'},
   {id:'undecided',label:'Leave the outcome undecided'}]});
  if(draft.method.status==='unspecified'&&!acknowledged('method'))result.push({id:'method',prompt:'What method do you want to check?',choices:[
   ...Object.entries(C.METHOD_FAMILIES).map(([id,label])=>({id:'family:'+id,label})),
   {id:'describe',label:'Describe the method',requiresText:true,fieldLabel:'Describe the rule or steps you want to test'},
   {id:'undecided',label:'I haven’t chosen a method'}]});
  if(draft.scope.status==='unspecified'&&!acknowledged('scope'))result.push({id:'scope',prompt:'Which material should this apply to?',choices:[
   {id:'unsolved-lp2',label:'The unsolved LP2 pages',example:'LP2-00–55'},
   {id:'specific',label:'Specific pages or a passage',requiresText:true,fieldLabel:'Name the pages or passage',placeholder:'LP2-15, LP2-17; or LP2-43, lines 2–3'},
   {id:'undecided',label:'Leave the scope undecided'}]});
  return result;
 }
 function chosenScope(text){
  try{return parseScope(text,editProvenance);}catch(error){
   // A malformed page list is an error; a prose passage remains exact prose.
   const residue=text.replace(/lp[12]-/gi,'').replace(/\band\b/gi,'').replace(/[\s\d,;–—-]/g,'');
   if(!residue)throw error;
   return clarified({description:text.trim()});
  }
 }
 function scopeEditorText(scope){
  if(scope.status!=='specified')return '';
  return typeof scope.value.description==='string'&&scope.value.description?
   scope.value.description:(scope.value.pages||[]).map(p=>p.toUpperCase()).join(', ');
 }
 function scopeEdit(scope,text){
  const value=text.trim();
  if(value===scopeEditorText(scope).trim())return undefined;
  // This control owns pages/passage only. Other supplied inputs, versions,
  // artifacts and exclusions remain exact, including when selection is cleared.
  const retained=scope.status==='specified'?Object.fromEntries(Object.entries(scope.value).filter(([key])=>!['pages','description'].includes(key))):{};
  const selection=value?chosenScope(value):C.field();
  const combined={...retained,...(selection.status==='specified'?selection.value:{})};
  return Object.keys(combined).length?clarified(combined):C.field();
 }
 function ruleNotesText(rules){
  const notes=rules.exceptionalCases;
  return notes.status==='specified'?(typeof notes.value==='string'?notes.value:JSON.stringify(notes.value)):'';
 }
 function ruleEdits(rules,text,removed=[]){
  if(!Array.isArray(removed)||removed.some(key=>!C.RULES.includes(key)))throw Error('Choose an existing condition to remove.');
  const patch=Object.fromEntries(removed.map(key=>[key,C.field()]));
  const value=text.trim();
  if(value!==ruleNotesText(rules).trim()){
   if(removed.includes('exceptionalCases')&&value)throw Error('Choose either removing the additional condition or replacing its text.');
   patch.exceptionalCases=value?clarified(value):C.field();
  }
  return Object.keys(patch).length?patch:undefined;
 }
 function scopeRetainedHTML(scope){
  const extras=scope.status==='specified'?Object.entries(scope.value).filter(([key])=>!['pages','description'].includes(key)):[];
  if(!extras.length)return '';
  return '<details class="small"><summary>Other supplied scope details are kept</summary><dl>'+extras.map(([key,value])=>'<div><dt>'+esc(key)+'</dt><dd>'+esc(typeof value==='string'?value:JSON.stringify(value))+'</dd></div>').join('')+'</dl></details>';
 }
 function retainedRulesHTML(draft){
  const visible=new Map(C.reviewRows(draft).find(row=>row.label==='Rules').tags.map(tag=>[tag.id,tag.text]));
  const keys=C.RULES.filter(key=>draft.rules[key].status!=='unspecified'&&
   (key!=='exceptionalCases'||draft.rules[key].status!=='specified'));
  if(!keys.length)return '';
  return '<div class="retained-rules"><p class="small">Recorded conditions are kept unless you remove one.</p>'+keys.map(key=>{
   const label=key.replace(/([a-z])([A-Z])/g,'$1 $2');
   const text=visible.get('rule:'+key)||label.charAt(0).toUpperCase()+label.slice(1)+': not applicable';
   return '<label class="retained-rule small"><input type="checkbox" id="remove-rule-'+key+'"><span>Remove: '+esc(text)+'</span></label>';
  }).join('')+'</div>';
 }
 function answerIntake(draft,id,choice,text=''){
  if(!['aim','method','scope'].includes(id))return C.clarify(draft,id,choice,text);
  const question=intakeQuestions(draft).find(q=>q.id===id),option=question?.choices.find(c=>c.id===choice);
  if(!option)throw Error('Choose an available answer.');
  if(option.requiresText&&!text.trim())throw Error(option.fieldLabel+'.');
  let value=C.field();
  if(id==='aim'&&choice!=='undecided'){const wording=choice==='unclassified'?text.trim():option.label;value=clarified({outcomeId:choice==='unclassified'?C.normalizeOutcome(wording).id:choice,wording,detail:choice==='unclassified'?wording:''});}
  if(id==='method'&&choice.startsWith('family:'))value=clarified({operations:[{id:'family_selection',familyId:choice.slice(7),label:option.label}]});
  if(id==='method'&&choice==='describe')value=clarified({operations:[{id:'described_method',label:text.trim(),sourceText:text.trim()}]});
  if(id==='scope'&&choice==='specific')value=chosenScope(text);
  if(id==='scope'&&choice==='unsolved-lp2')value=clarified({pages:Array.from({length:56},(_,i)=>'lp2-'+String(i).padStart(2,'0'))});
  const next=C.revise(draft,{[id]:value});
  next.clarifications.push({question:id,choice,...(option.requiresText?{text}:{}),revision:next.revision});
  return next;
 }
 function compactPages(values){
  const selected=C.pages(values),ranges=[];
  for(let i=0;i<selected.length;){
   const first=selected[i];let last=first,j=i+1;
   while(j<selected.length&&selected[j].slice(0,3)===first.slice(0,3)&&Number(selected[j].slice(4))===Number(last.slice(4))+1)last=selected[j++];
   ranges.push({id:'scope-range:'+first+':'+last,text:first.toUpperCase()+(last===first?'':'–'+last.slice(4)),unknown:false});i=j;
  }
  return ranges;
 }
 function validateAnswer(data,knownDocuments){
  if(!data||typeof data.answer!=='string'||!data.answer.trim()||data.answer.length>12000||!Array.isArray(data.sources)||!data.sources.length||data.sources.length>4)throw Error('A sourced comparison is unavailable. You can inspect the related records below.');
  const seen=new Set();
  for(const source of data.sources){
   if(!source||seen.has(source.id)||!knownDocuments.some(d=>d.id===source.id&&d.href===source.href)||!M.safe(source.href))throw Error('The comparison returned an unrecognized source.');
   const current=knownDocuments.find(d=>d.id===source.id&&d.href===source.href);
   if(source.text!==current.text)throw Error('The source record changed while this comparison was prepared. Reload the research and try again.');
   seen.add(source.id);
  }
  const citations=[...data.answer.matchAll(/\[(\d+)\]/g)].map(m=>Number(m[1]));
  if(!citations.length||citations.some(n=>n<1||n>data.sources.length))throw Error('The comparison could not be checked against its sources.');
  return {answer:data.answer,sources:data.sources.map(s=>knownDocuments.find(d=>d.id===s.id&&d.href===s.href)),cached:Boolean(data.cached)};
 }
 function operationDetails(operation){
  if(!operation)return '';
  const entries=Object.entries(operation).filter(([key])=>!['id','label','sourceText','provenance','editHistory','declaredFamilyId'].includes(key)&&!(key==='familyId'&&operation.id==='family_selection'));
  if(!entries.length)return '';
  const label=key=>key.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/_/g,' ').replace(/^./,c=>c.toUpperCase());
  return '<dl class="method-parameters">'+entries.map(([key,value])=>'<div><dt>'+esc(label(key))+'</dt><dd>'+esc(typeof value==='string'?value:JSON.stringify(value))+'</dd></div>').join('')+'</dl>';
 }
 function rowsHTML(spec){return '<dl>'+C.reviewRows(spec).filter(r=>r.label!=='Unresolved'&&(r.tags||[]).length).map(r=>{
  const originalTags=r.label==='Scope'&&spec.scope.status==='specified'?r.tags.map(t=>t.id==='scope:description'?{...t,text:spec.scope.value.description}:t):r.tags;
  const tags=r.label==='Scope'&&spec.scope.status==='specified'&&spec.scope.value.pages?[...compactPages(spec.scope.value.pages),...originalTags.filter(t=>!/^lp[12]-\d{2}$/.test(t.id))]:originalTags;
  const label=r.label==='Aim'?'Outcome':r.label==='Rules'?'Bounds & rules':r.label;
  let content;
  if(r.label==='Method')content=tags.length>1?'<ol class="method-steps">'+tags.map((t,i)=>'<li>'+esc(t.text)+operationDetails(spec.method.value?.operations[i])+'</li>').join('')+'</ol>':'<div class="method-wording"><p>'+esc(tags[0].text)+'</p>'+operationDetails(spec.method.value?.operations[0])+'</div>';
  else content=tags.map(t=>'<span class="tag'+(t.unknown?' unknown':'')+'">'+esc(t.text)+'</span>').join('');
  if(r.label==='Aim'&&spec.aim.status==='specified'){
   const outcome=C.normalizeOutcome(spec.aim.value),detail=outcome.detail||outcome.wording;
   if(outcome.id==='unclassified')content='<span class="tag unknown">Outcome not classified</span>';
   if(detail&&detail!==outcome.label&&(outcome.id==='unclassified'||C.normalizeOutcome(detail).id!==outcome.id))content+='<p class="objective-detail">'+esc(detail)+'</p>';
  }
  if(r.label==='Aim'&&spec.aim.status!=='specified')content='<span class="tag unknown">Outcome undecided</span>';
  if(r.label==='Method'){const families=C.classifyMethod(spec.method).familyIds;if(tags.length===1&&families.some(id=>C.METHOD_FAMILIES[id]===tags[0].text))content='';content=families.map(id=>'<span class="tag">'+esc(C.METHOD_FAMILIES[id])+'</span>').join('')+content;}
  return '<div class="tag-row"><dt>'+esc(label)+'</dt><dd>'+content+'</dd></div>';
 }).join('')+(spec.unresolved.length?'<div class="tag-row"><dt>Other details</dt><dd class="unresolved-details">'+spec.unresolved.map(item=>{const value={...item};delete value.provenance;const noteKeys=value.kind==='custom_interpretation'?['kind','question','text']:value.kind==='source_note'?['kind','text']:null;const readable=typeof value.text==='string'&&(Object.keys(value).length===1||noteKeys&&Object.keys(value).every(key=>noteKeys.includes(key))); return '<p>'+esc(readable?value.text:JSON.stringify(value))+'</p>';}).join('')+'</dd></div>':'')+'</dl>';}
 function methodText(spec){return C.reviewRows(spec).find(r=>r.label==='Method').tags.map(t=>t.text).join('; then ');}
 const nativeLinks=html=>html.replace(/<a /g,'<a target="_blank" rel="noopener" ').replace(/title="([^"]*)"/g,'title="$1 (opens in a new tab)"').replace(/href="#\//g,'href="index.html#/');
 // Editorial status belongs to the record workflow; preserve substantive uncertainty.
 function readerLimit(record){return String(record.reader_limit||record.limitations||'').replace(/\s*Human review pending\.?\s*$/i,'').trim();}
 function sourceHTML(doc,records,{packet=false,preview=false}={}){
  const record=records.find(r=>r.id===doc.id);
  const heading='<section class="source"><h3><a target="_blank" rel="noopener" title="Open source in a new tab" href="index.html'+esc(doc.href)+'">'+esc(doc.title)+'</a></h3>';
  if(!record)return heading+'<p>Supporting manuscript context, not evidence that the idea was tested.</p></section>';
  const scope=record.scope||{},limit=readerLimit(record),finding=record.reader_finding||record.finding;
  const pages=Array.isArray(scope.pages)&&scope.pages.length?compactPages(scope.pages).map(p=>p.text).join(', '):'Not specified in this record';
  const facts=[['Page scope',pages],['Method',scope.procedure],['Input',scope.representation],['Bounds',scope.parameters],['Not tested',scope.exclusions]];
  if(record.materials)facts.push(['Saved results',[record.materials.summary,record.materials.reuse,record.materials.limits].join(' ')]);
  if(packet)facts.push(['Run',record.reproduction?.command],['Inputs',(record.reproduction?.inputs||[]).map(f=>f.path).join(', ')]);
  return heading+((packet||preview)&&finding?'<p>'+esc(finding)+'</p>':'')+
   (preview?'':'<dl class="source-facts">'+facts.filter(([,value])=>value).map(([label,value])=>'<div><dt>'+label+'</dt><dd>'+esc(value)+'</dd></div>').join('')+'</dl>')+
   (limit?'<p class="source-limit"><strong>Limit:</strong> '+esc(limit)+'</p>':'')+'</section>';
 }
 function packetHTML(packet){
  const s=packet.confirmed,r=packet.research,docs=r.evidence.documents||[];
  return '<h1>Liberpedia · Research note</h1><p>'+esc(r.at)+'</p>'+rowsHTML(s)+
   '<h2>Findings</h2><div class="answer">'+nativeLinks(M.render(r.answer,docs))+'</div>'+
   (docs.length?'<h2>Sources</h2>'+docs.map(d=>sourceHTML(d,r.evidence.records,{packet:true})).join(''):'<p>No close record was returned by this search. This is a search result, not a finding that the idea is untried.</p>')+
   '<h2>Original idea</h2><pre>'+esc(s.source.text)+'</pre>';
 }
 function disclosureNodes(host){
  const nodes=[],keys=new Map(),counts=new Map();
  for(const detail of host.querySelectorAll?.('details')||[]){
   const summary=detail.querySelector(':scope > summary');if(!summary)continue;
   const parent=detail.parentElement?.closest('details'),prefix=keys.get(parent)||'';
   const base=prefix+'/'+encodeURIComponent(summary.textContent.trim()),ordinal=counts.get(base)||0;counts.set(base,ordinal+1);
   const key=base+'#'+ordinal;keys.set(detail,key);nodes.push({key,detail,summary});
  }
  return nodes;
 }
 function captureDisclosureState(host,active){return disclosureNodes(host).map(({key,detail,summary})=>({key,open:detail.open,focused:summary===active}));}
 function restoreDisclosureState(host,states){
  const saved=new Map(states.map(state=>[state.key,state]));let target=null;
  for(const {key,detail,summary}of disclosureNodes(host)){const state=saved.get(key);if(state){detail.open=state.open;if(state.focused)target=summary;}}
  target?.focus({preventScroll:true});
 }
 const RECOVERY_KEY='liberpedia-idea-draft-v1',RECOVERY_LIMIT=160000,RECOVERY_AGE=86400000;
 function recoveryDraft(value){
  if(!value||value.schema!==C.SCHEMA||typeof value.source?.text!=='string'||value.source.text.length>32000)throw Error('Invalid saved draft');
  const draft=C.createDraft(value);
  if(!Number.isInteger(value.revision)||value.revision<1||value.revision>100000)throw Error('Invalid saved revision');
  if(!Array.isArray(value.clarifications)||value.clarifications.length>128)throw Error('Invalid saved answers');
  for(const answer of value.clarifications)if(!answer||typeof answer.question!=='string'||typeof answer.choice!=='string'||!Number.isInteger(answer.revision)||answer.revision<1||answer.revision>value.revision||(answer.text!==undefined&&typeof answer.text!=='string'))throw Error('Invalid saved answer');
  draft.revision=value.revision;draft.clarifications=JSON.parse(JSON.stringify(value.clarifications));return draft;
 }
 function readRecovery(serialized,entry,at){
  try{
   if(typeof serialized!=='string'||serialized.length>RECOVERY_LIMIT)return null;
   const value=JSON.parse(serialized),age=at-value.at;
   if(value.version!==1||value.entry!==entry||!Number.isFinite(age)||age<0||age>RECOVERY_AGE||typeof value.raw!=='string'||value.raw.length>32000||typeof value.editing!=='boolean'||!['input','review','interpreting','research'].includes(value.stage))return null;
   const draft=['review','research'].includes(value.stage)?recoveryDraft(value.draft):null;
   if(value.editing&&!draft)return null;
   if(draft&&draft.source.text!==value.raw)return null;
   const baseline=value.editing?recoveryDraft(value.baseline):null;
   if(baseline&&baseline.source.text!==value.raw)return null;
   const overlay=value.overlay;
   if(overlay!==null&&overlay!==undefined){
    if(!overlay||typeof overlay!=='object'||Array.isArray(overlay))return null;
    for(const [key,field]of Object.entries(overlay))if(!/^(edit-(aim|objective|scope|rules|method(?:-\d+)?|method-family-\d+)|remove-rule-[A-Za-z]+|other-detail|choice)$/.test(key)||!['string','boolean'].includes(typeof field)||(typeof field==='string'&&field.length>32000))return null;
   }
   return {raw:value.raw,stage:draft?'review':'input',draft,editing:!!baseline,baseline,overlay:overlay||{}};
  }catch{return null;}
 }
 function createApp(doc,{fetcher=root.fetch.bind(root),now=()=>new Date().toISOString(),id=()=>root.crypto.randomUUID(),printer=()=>root.print(),schedule=setTimeout,unschedule=clearTimeout,sharer=H.share,renderCard=H.renderPNG}={}){
  const host=doc.getElementById('investigate'),printHost=doc.getElementById('print-snapshot');
  let stage='input',draft=null,confirmed=null,result=null,packet=null,editing=false,editingBackup=null,raw='',records=[],documents=[],endpoint=null,loaded=false,loadError='',message='',error='',busy=false,controller=null,generation=0,registryId='';
  const incoming=new URLSearchParams(doc.defaultView?.location?.search||'');
  raw=incoming.get('q')||'';
  let legacyScope=null;
  let shareBusy=false,shareNotice='',shareFallback=null,preparedCard=null,preparedFor=null;
  let intakeEndpoint=null,intake=null,intakeController=null,intakeVersion=0;
  let renderedResearchCard=null;
  let cardContract=false;
  let interpretationEndpoint=null,interpretController=null,interpretVersion=0,interpreting=false,interpretError='';
  let configResolved=false,configValid=false,configReady=null,configAttempt=null,loadVersion=0,destroyed=false;
  const fragment=doc.defaultView?.location?.hash||'';
  const recoveryEntry=JSON.stringify({search:doc.defaultView?.location?.search||'',fragment});
  let session=null;try{session=doc.defaultView?.sessionStorage;}catch{}
  let restoringOverlay=null;
  if(fragment.startsWith('#idea=')){
   try{const shared=H.decode(fragment);draft=shared.draft;for(const name of ['aim','scope'])if(draft[name].status==='unspecified')draft=answerIntake(draft,name,'undecided');raw=draft.source.text;stage='review';message='Shared idea. Review the wording before checking prior research.';}
   catch{error='This shared idea link could not be read. Ask for a new link or enter the idea below.';}
  }
  const pageHint=incoming.getAll('pages').join(',');
  if(pageHint){try{legacyScope=parseScope(pageHint,{kind:'supplied',refs:['URL page hint']});}catch{message='The linked page selection could not be read. You can enter exact pages when reviewing the idea.';}}
  let recovered=null;try{recovered=readRecovery(session?.getItem(RECOVERY_KEY),recoveryEntry,Date.parse(now()));}catch{}
  if(recovered){
   ({raw,stage,draft,editing}=recovered);restoringOverlay=recovered.overlay;if(stage==='review')legacyScope=null;
   if(editing)editingBackup={stage:'review',draft:recovered.baseline,confirmed:null,result:null,packet:null,message:'',error:''};
   message='Draft restored.';
  }
  function recoveryFields(){
   const fields={};
   for(const name of ['edit-aim','edit-objective','edit-scope','edit-rules','other-detail',...C.RULES.map(k=>'remove-rule-'+k),...(draft?.method.status==='specified'?draft.method.value.operations:[]).flatMap((_,i)=>[i?'edit-method-'+i:'edit-method','edit-method-family-'+i])]){
    const field=doc.getElementById(name);if(field)fields[name]=name.startsWith('remove-rule-')?!!field.checked:field.value;
   }
   const choice=doc.querySelector('input[name=choice]:checked');if(choice)fields.choice=choice.value;
   return fields;
  }
  function saveRecovery(){
   if(!session||destroyed)return;
   try{
    const value=JSON.stringify({version:1,entry:recoveryEntry,at:Date.parse(now()),raw,stage,draft:stage==='review'||stage==='research'?draft:null,editing,baseline:editing?editingBackup?.draft:null,overlay:recoveryFields()});
    if(value.length<=RECOVERY_LIMIT)session.setItem(RECOVERY_KEY,value);
    else session.removeItem(RECOVERY_KEY);
   }catch{}
  }
  function restoreFields(fields){
   for(const [name,value]of Object.entries(fields)){
    if(name==='choice')continue;const field=doc.getElementById(name);if(field){if(name.startsWith('remove-rule-'))field.checked=value;else field.value=value;}
   }
   if(fields.choice){
    const radio=[...(doc.querySelectorAll?.('input[name=choice]')||[])].find(r=>r.value===fields.choice);
    if(radio){radio.checked=true;const option=intakeQuestions(draft)[0]?.choices.find(c=>c.id===fields.choice),other=!!option?.requiresText;
     const detail=doc.getElementById('other-detail'),label=doc.getElementById('other-label');if(detail){detail.hidden=!other;detail.required=other;}if(label){label.hidden=!other;label.textContent=option?.fieldLabel||'Describe what you mean';}}
   }
  }
  const focus=selector=>doc.querySelector(selector)?.focus();
  function stop(){generation++;controller?.abort();controller=null;busy=false;}
  function stopInterpretation(){interpretVersion++;interpretController?.abort();interpretController=null;interpreting=false;}
  function stopIntake(clear=false){intakeVersion++;intakeController?.abort();intakeController=null;if(intake)intake.busy=false;if(clear)intake=null;}
  function render(){
   const prior=doc.activeElement?.id;
   const sameResearch=stage==='research'&&confirmed&&renderedResearchCard===confirmed;
   const disclosures=sameResearch?captureDisclosureState(host,doc.activeElement):[];
   const selection=sameResearch&&prior&&Number.isInteger(doc.activeElement.selectionStart)&&Number.isInteger(doc.activeElement.selectionEnd)?{value:doc.activeElement.value,start:doc.activeElement.selectionStart,end:doc.activeElement.selectionEnd}:null;
   const pending=stage==='review'&&!editing?intakeQuestions(draft)[0]:null;
   if(stage==='input'){
    host.innerHTML='<h1>Have we tried it?</h1><p>Describe the idea or paste the rule you want to check.</p><form id="intake"><label class="sr-only" for="idea">Your idea</label><textarea id="idea" required maxlength="1500" rows="6" placeholder="For example: reverse the prime values of each row on LP2-15">'+esc(raw)+'</textarea><div class="actions"><button class="primary" type="submit">Review idea</button></div></form>';
   }else if(stage==='interpreting'){
    host.innerHTML='<button class="back" id="cancel-interpretation" type="button">Back to idea</button><h1 id="interpret-title" tabindex="-1">Review your idea</h1>'+
     '<p role="status">'+esc(interpreting?'Preparing the method and scope for your review…':interpretError||'Continue with your original wording.')+'</p>'+
     '<details><summary>Original idea</summary><pre>'+esc(raw)+'</pre></details><div class="actions"><button id="use-original" type="button">Use my original wording</button>'+(!interpreting?'<button class="primary" id="retry-interpretation" type="button">Try again</button>':'')+'</div>';
   }else{
    host.innerHTML='<button class="back" id="back" type="button">Back to idea</button><h1 id="review-title"'+(pending?' class="question-title"':'')+' tabindex="-1">'+esc(pending?pending.prompt:stage==='research'?'Research comparison':'Is this the idea?')+'</h1>'+
     (pending?'':(stage==='research'?'<section class="confirmed-card"><button id="share-idea" class="share-icon" type="button" aria-label="Share confirmed idea" title="Share idea"'+(shareBusy?' disabled':'')+'><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V3m-4 4 4-4 4 4M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8"/></svg></button><details class="confirmed"><summary>Your idea</summary>':'<section aria-label="Interpreted idea">')+rowsHTML(confirmed||draft)+
     '<div class="actions"><button class="left" id="edit" type="button">Edit interpretation</button></div>'+(stage==='research'?'</details>'+intakeHTML()+'<p id="share-status" class="small" role="status">'+esc(shareNotice)+'</p><div id="share-fallback"></div></section>':'</section>')+
     '')+(editing?editorHTML():questionsHTML())+(pending?'<button id="edit" type="button">Edit interpretation</button>':'')+
     (stage==='review'?'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'')+
     (stage==='review'&&!editing&&!intakeQuestions(draft).length&&draft.method.status!=='specified'?'<p>Choose a method before comparing it with prior tests. <a href="index.html#/research">Browse the research index</a> for approaches.</p>':'')+
     (stage==='review'&&!editing&&!intakeQuestions(draft).length&&draft.method.status==='specified'?'<p id="collection-notice" class="small"'+(intakeEndpoint?'':' hidden')+'>'+(intakeEndpoint?'Confirmed ideas are saved for research review.':'')+'</p>'+'<div class="actions"><button class="primary" id="confirm" '+(!loaded?'disabled':'')+' type="button">Confirm and find research</button></div>':'')+
     (stage==='research'?researchHTML()+'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'');
   }
   host.insertAdjacentHTML('beforeend','<p id="status" class="notice small" role="status">'+esc(message||(!loaded&&!loadError?'Loading research records…':''))+'</p><p id="error" class="notice error" role="alert">'+esc(error||loadError)+'</p>'+(!loaded&&loadError?'<button id="reload" type="button">Retry loading research</button>':'')+'<p class="small privacy">'+(endpoint?'Research questions are processed by Cloudflare. Don’t include private information.':'')+'</p>');
   bind();
   if(restoringOverlay){restoreFields(restoringOverlay);restoringOverlay=null;}
   if(sameResearch)restoreDisclosureState(host,disclosures);
   if(prior&&doc.getElementById(prior))doc.getElementById(prior).focus({preventScroll:true});
   if(selection){const field=doc.getElementById(prior);if(field?.value===selection.value&&field.setSelectionRange)field.setSelectionRange(selection.start,selection.end);}
   renderedResearchCard=stage==='research'?confirmed:null;
   saveRecovery();
  }
  function intakeHTML(){
   if(!intakeEndpoint||!intake||intake.snapshot!==confirmed)return '';
   return '<div class="idea-save" id="idea-save"><span id="idea-save-status" class="small" role="status" tabindex="-1">'+intakeStatus()+'</span><button id="retry-save" type="button"'+(intake.error?'':' hidden')+'>Retry saving</button></div>';
  }
  function intakeStatus(){return intake.busy?'Saving idea…':intake.saved?'Saved.':intake.error?"Couldn’t save this idea.":'';}
  function updateIntake(){
   const status=doc.getElementById('idea-save-status'),retry=doc.getElementById('retry-save');if(!status||!retry||intake?.snapshot!==confirmed)return false;
   status.textContent=intakeStatus();const held=doc.activeElement===retry;retry.hidden=!intake.error;if(held&&retry.hidden)status.focus({preventScroll:true});return true;
  }
  async function saveIntake(snapshot=confirmed){
   if(!intakeEndpoint||!snapshot||snapshot!==confirmed)return;
   if(!intake||intake.snapshot!==snapshot){
    stopIntake(true);
    intake={snapshot,requestId:id(),busy:false,saved:false,error:false};
    try{intake.body={requestId:intake.requestId,fragment:H.encode(snapshot),...(snapshot.source.origin==='shared_link'?{}:{originalIdea:snapshot.source.text})};}
    catch{intake.error=true;render();return;}
   }
   const current=intake;if(current.busy||current.saved||!current.body)return;
   const token=++intakeVersion,requestController=new AbortController();intakeController=requestController;current.busy=true;current.error=false;if(!updateIntake())render();
   const timer=schedule(()=>requestController.abort(),30000);
   try{
    const response=await fetcher(intakeEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(current.body),signal:requestController.signal});
    const data=await response.json();
    if(requestController.signal.aborted)throw Error('Save interrupted');
    if(token!==intakeVersion||intake!==current||confirmed!==snapshot)return;
    if(!response.ok||!/^p_[a-f0-9]{64}$/.test(data.id)||!['received','already_received'].includes(data.status)||!Number.isFinite(Date.parse(data.receivedAt)))throw Error('Save unavailable');
    current.saved=true;
   }catch{if(token===intakeVersion&&intake===current&&confirmed===snapshot)current.error=true;}
   finally{unschedule(timer);if(token===intakeVersion&&intake===current&&confirmed===snapshot){current.busy=false;intakeController=null;updateIntake();}}
  }
  function prepareCard(){
   const snapshot=confirmed;preparedFor=snapshot;preparedCard=null;shareNotice='';shareFallback=null;
   Promise.resolve().then(()=>renderCard(snapshot,{document:doc})).then(blob=>{if(preparedFor===snapshot)preparedCard=blob;}).catch(()=>{});
  }
  function updateShare(){
   const button=doc.getElementById('share-idea');if(button)button.disabled=shareBusy;
   const status=doc.getElementById('share-status');if(status)status.textContent=shareNotice;
   const fallback=doc.getElementById('share-fallback');if(!fallback)return;
   fallback.innerHTML=shareFallback?'<label for="share-link">Idea link</label><input id="share-link" readonly value="'+esc(shareFallback.url)+'">'+(shareFallback.png?'<button id="download-idea" type="button">Download card image</button>':''):'';
   doc.getElementById('share-link')?.addEventListener('click',event=>event.target.select());
   doc.getElementById('download-idea')?.addEventListener('click',()=>{const url=URL.createObjectURL(shareFallback.png),a=doc.createElement('a');a.href=url;a.download='liber-primus-idea.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  }
  async function shareIdea(){
   if(!confirmed||shareBusy)return;
   const snapshot=confirmed;shareBusy=true;shareNotice='';shareFallback=null;updateShare();
   try{
    const base='https://jelliottdev.github.io/investigate.html';
    const response=await sharer(snapshot,base,{document:doc,preparedPNG:preparedFor===snapshot?preparedCard:null});
    if(confirmed!==snapshot)return;
    if(response.status==='shared')shareNotice='';
    else if(response.status==='copied'){shareNotice='Idea link copied.';shareFallback=response;}
    else if(response.status==='fallback'){shareNotice='Copy the link below to share this idea.';shareFallback=response;}
   }catch(e){if(confirmed===snapshot)shareNotice='Could not share this card. '+e.message;}
   finally{shareBusy=false;if(confirmed===snapshot)updateShare();}
  }
  const methodOperations=()=>draft?.method.status==='specified'?draft.method.value.operations:[];
  const stepText=operation=>operation.label??operation.sourceText??operation.id;
  function methodStepsHTML(){
   const operations=methodOperations(),classified=C.classifyMethod(draft.method).operations;
   return '<ol class="method-editor-list" id="method-step-list">'+operations.map((operation,index)=>{
    const family=classified[index],textId=index?'edit-method-'+index:'edit-method';
    const automatic=family.familyId==='unclassified'?'No detected category':'Detected: '+family.label;
    return '<li><div class="method-step-heading">Step '+(index+1)+'</div><label for="edit-method-family-'+index+'">Category</label><select id="edit-method-family-'+index+'"><option value="">'+esc(automatic)+'</option>'+Object.entries(C.METHOD_FAMILIES).map(([id,label])=>'<option value="'+esc(id)+'"'+(operation.declaredFamilyId===id?' selected':'')+'>'+esc(label)+'</option>').join('')+'</select><label for="'+textId+'">Exact rule for step '+(index+1)+'</label><textarea id="'+textId+'" required maxlength="1200">'+esc(stepText(operation))+'</textarea>'+(family.basis==='category_conflict'?'<p class="small">The category differs from the recorded rule. The exact rule is retained.</p>':'')+'<div class="method-step-actions"><button type="button" id="method-up-'+index+'" aria-label="Move step '+(index+1)+' earlier"'+(index===0?' disabled':'')+'>Earlier</button><button type="button" id="method-down-'+index+'" aria-label="Move step '+(index+1)+' later"'+(index===operations.length-1?' disabled':'')+'>Later</button><button type="button" id="method-remove-'+index+'" aria-label="Remove step '+(index+1)+'">Remove</button></div></li>';
   }).join('')+'</ol>';
  }
  function flushMethodSteps(){
   const operations=methodOperations().slice();
   operations.forEach((operation,index)=>{
    const text=doc.getElementById(index?'edit-method-'+index:'edit-method')?.value.trim()??stepText(operation);
    const family=doc.getElementById('edit-method-family-'+index)?.value||null;
    if(text!==stepText(operation))draft=C.applyMethodEdit(draft,{type:'wording',index,text});
    if(family!==(methodOperations()[index].declaredFamilyId||null))draft=C.applyMethodEdit(draft,{type:'category',index,familyId:family});
   });
  }
  function refreshMethodSteps(target){
   const list=doc.getElementById('method-step-list');
   if(list){const html=methodStepsHTML();list.innerHTML=html.slice(html.indexOf('>')+1,html.lastIndexOf('</ol>'));bindMethodSteps();focus(target);}
  }
  function editMethodStep(edit,target){
   try{flushMethodSteps();draft=C.applyMethodEdit(draft,edit);error='';doc.getElementById('error').textContent='';refreshMethodSteps(target);saveRecovery();}
   catch(e){error=e.message;doc.getElementById('error').textContent=error;}
  }
  function bindMethodSteps(){
   methodOperations().forEach((operation,index)=>{
    for(const name of [index?'edit-method-'+index:'edit-method','edit-method-family-'+index])for(const type of ['input','change'])doc.getElementById(name)?.addEventListener(type,saveRecovery);
    doc.getElementById('method-up-'+index)?.addEventListener('click',()=>editMethodStep({type:'move',index,toIndex:index-1},'#'+(index===1?'edit-method':'edit-method-'+(index-1))));
    doc.getElementById('method-down-'+index)?.addEventListener('click',()=>editMethodStep({type:'move',index,toIndex:index+1},'#edit-method-'+(index+1)));
    doc.getElementById('method-remove-'+index)?.addEventListener('click',()=>editMethodStep({type:'remove',index},methodOperations().length===1?'#method-add':'#'+(index===0?'edit-method':'edit-method-'+(index-1))));
   });
  }
  function editorHTML(){
   const scope=scopeEditorText(draft.scope);
   const rule=ruleNotesText(draft.rules);
   const outcome=draft.aim.status==='specified'?C.normalizeOutcome(draft.aim.value):{id:'',wording:'',detail:''};
   return '<form class="editor" id="editor"><label for="edit-aim">Outcome</label><select id="edit-aim"><option value="">Undecided</option>'+Object.entries(C.OUTCOMES).map(([id,label])=>'<option value="'+esc(id)+'"'+(outcome.id===id?' selected':'')+'>'+esc(label)+'</option>').join('')+'<option value="unclassified"'+(outcome.id==='unclassified'?' selected':'')+'>None of these fits</option></select><label for="edit-objective">Objective detail <span class="small">(optional)</span></label><textarea id="edit-objective" maxlength="600">'+esc(outcome.detail||outcome.wording)+'</textarea><fieldset class="method-editor"><legend>Method steps</legend>'+methodStepsHTML()+'<button id="method-add" type="button">Add step</button></fieldset><label for="edit-scope">Pages or passage <span class="small">(optional)</span></label><input type="text" id="edit-scope" value="'+esc(scope)+'" placeholder="LP2-15, LP2-17">'+scopeRetainedHTML(draft.scope)+retainedRulesHTML(draft)+'<label for="edit-rules">Additional conditions <span class="small">(optional)</span></label><textarea id="edit-rules" maxlength="600">'+esc(rule)+'</textarea><div class="actions"><button id="cancel-edit" type="button">Cancel</button><button class="primary" type="submit">Review changes</button></div></form>';
  }
  function questionsHTML(){
   if(stage!=='review')return '';
   const q=intakeQuestions(draft)[0];if(!q)return '';
   return '<form id="clarification" class="question"><fieldset><legend class="sr-only">'+esc(q.prompt)+'</legend>'+(q.example?'<p class="example">'+esc(q.example)+'</p>':'')+q.choices.map(c=>'<label><input type="radio" name="choice" value="'+esc(c.id)+'" required><span>'+esc(c.label)+(c.example?'<small class="example">'+esc(c.example)+'</small>':'')+'</span></label>').join('')+'</fieldset><label for="other-detail" id="other-label" hidden>Describe what you mean</label><textarea id="other-detail" hidden></textarea><div class="actions"><button class="primary" type="submit">Review idea</button></div></form>';
  }
  function researchHTML(){
   const controls='<div class="actions">'+(busy?'<button id="cancel" type="button">Stop waiting</button>':(!result?'<button id="retry" type="button">Try comparison again</button>':''))+(packet?'<button id="print" type="button">Print research note</button>':'')+'</div>';
   if(result)return '<h2>Findings</h2><div class="answer">'+nativeLinks(M.render(result.answer,result.sources))+'</div>'+(result.sources.length?'<details class="source-evidence"><summary>Sources ('+result.sources.length+')</summary>'+result.sources.map(d=>sourceHTML(d,records)).join('')+'</details>':'<p><a href="index.html#/research" target="_blank" rel="noopener">Browse the research index</a></p>')+controls+(result.noMatch?'':'<p class="small answer-note">AI comparison based on the linked records.</p>');
   let q,scope;try{if(cardContract){const prepared=R.prepare(confirmed);q={query:prepared.query};scope=prepared;}else{q=C.retrievalQuery(confirmed);scope=C.queryForResearch(confirmed,{maxLength:6000});}}catch{q={};scope={};}
   const related=q.query?S.select(documents,q.query,scope.pages||[]).filter(d=>d.kind==='experiment').slice(0,2):[];
   return (busy?'<p aria-live="polite">Comparing the confirmed idea with published research…</p>':'')+controls+(related.length?'<h2>Related records</h2>'+related.map(d=>sourceHTML(d,records,{preview:true})).join(''):'');
  }
  function bind(){
   doc.getElementById('cancel-interpretation')?.addEventListener('click',()=>{stopInterpretation();stage='input';error='';message='';render();focus('#idea');});
   doc.getElementById('use-original')?.addEventListener('click',()=>{stopInterpretation();acceptDraft(initialDraft(raw),'Using your original wording. Review the method and scope below.');});
   doc.getElementById('retry-interpretation')?.addEventListener('click',()=>interpret());
   doc.getElementById('retry-save')?.addEventListener('click',()=>saveIntake());
   doc.getElementById('share-idea')?.addEventListener('click',shareIdea);
   if(stage==='research')updateShare();
   bindMethodSteps();
   doc.getElementById('method-add')?.addEventListener('click',()=>editMethodStep({type:'add',index:methodOperations().length,operation:{id:'described_method',label:''}},'#'+(methodOperations().length?'edit-method-'+methodOperations().length:'edit-method')));
   doc.getElementById('idea')?.addEventListener('input',event=>{raw=event.target.value;saveRecovery();});
   for(const name of Object.keys(recoveryFields()))if(name!=='choice'&&!name.startsWith('edit-method'))for(const type of ['input','change'])doc.getElementById(name)?.addEventListener(type,saveRecovery);
   for(const radio of doc.querySelectorAll?.('input[name=choice]')||[])radio.addEventListener('change',saveRecovery);
   doc.getElementById('intake')?.addEventListener('submit',event=>{
    event.preventDefault();raw=doc.getElementById('idea').value;if(!raw.trim())return;
    stopIntake(true);stop();stopInterpretation();confirmed=null;result=null;packet=null;printHost.replaceChildren();editing=false;error='';message='';
    if(configResolved&&!interpretationEndpoint)acceptDraft(initialDraft(raw));else interpret();
   });
   doc.getElementById('back')?.addEventListener('click',()=>{stopIntake(true);stop();stage='input';editing=false;confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#idea');});
   doc.getElementById('edit')?.addEventListener('click',()=>{stopIntake(true);stop();editingBackup={stage,draft,confirmed,result,packet,message,error};editing=true;stage='review';draft=C.revise(draft,{});confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#edit-method');});
   doc.getElementById('cancel-edit')?.addEventListener('click',()=>{editing=false;if(editingBackup){({stage,draft,confirmed,result,packet,message,error}=editingBackup);editingBackup=null;if(packet)printHost.innerHTML=packetHTML(packet);}render();focus('#edit');});
   doc.getElementById('editor')?.addEventListener('submit',event=>{
    event.preventDefault();try{
     flushMethodSteps();
     const ruleText=doc.getElementById('edit-rules').value.trim();
     const scopeText=doc.getElementById('edit-scope').value.trim();
     const outcomeId=doc.getElementById('edit-aim').value,objective=doc.getElementById('edit-objective').value.trim();
     const priorOutcome=draft.aim.status==='specified'?C.normalizeOutcome(draft.aim.value):{id:'',wording:'',detail:''};
     const patch={},scopeChange=scopeEdit(draft.scope,scopeText);
     if(scopeChange!==undefined)patch.scope=scopeChange;
     if(outcomeId!==priorOutcome.id||objective!==(priorOutcome.detail||priorOutcome.wording))patch.aim=outcomeId?clarified({outcomeId:outcomeId==='unclassified'?C.normalizeOutcome(objective).id:outcomeId,wording:outcomeId==='unclassified'?objective:priorOutcome.wording||objective,detail:objective}):objective?clarified({outcomeId:'unclassified',wording:objective,detail:objective}):C.field();
     const removed=C.RULES.filter(key=>doc.getElementById('remove-rule-'+key)?.checked);
     const rulesChange=ruleEdits(draft.rules,ruleText,removed);
     if(rulesChange)patch.rules=rulesChange;
     draft=C.revise(draft,patch);
     editing=false;editingBackup=null;error='';render();focus('#review-title');
    }catch(e){error=e.message;doc.getElementById('error').textContent=error;}
   });
   doc.getElementById('clarification')?.addEventListener('change',()=>{
    const selected=doc.querySelector('input[name=choice]:checked')?.value,q=intakeQuestions(draft)[0],option=q.choices.find(c=>c.id===selected),other=Boolean(option?.requiresText);
    doc.getElementById('other-label').hidden=!other;doc.getElementById('other-label').textContent=option?.fieldLabel||'Describe what you mean';doc.getElementById('other-detail').hidden=!other;doc.getElementById('other-detail').required=other;doc.getElementById('other-detail').placeholder=option?.placeholder||'';
   });
   doc.getElementById('clarification')?.addEventListener('submit',event=>{
    event.preventDefault();const choice=doc.querySelector('input[name=choice]:checked')?.value;if(!choice)return;
    const q=intakeQuestions(draft)[0];
    if(['aim','method','scope'].includes(q.id)){
     try{draft=answerIntake(draft,q.id,choice,doc.getElementById('other-detail').value);message='';}catch(e){error=e.message;doc.getElementById('error').textContent=error;return;}
    }else if(choice==='other'){
     const text=doc.getElementById('other-detail').value.trim();if(!text)return;
     const previous={stage,draft,confirmed,result,packet,message,error};
     const revised=C.clarify(draft,q.id,choice,text);
     editingBackup=previous;draft=revised;editing=true;message='Your explanation is kept. Edit the method wording to make the interpretation explicit.';
    }else{draft=C.clarify(draft,q.id,choice);message='';}
    error='';render();focus(editing?'#edit-method':'#review-title');
   });
   doc.getElementById('confirm')?.addEventListener('click',()=>{
    if(!loaded)return;
    try{if(draft.method.status!=='specified')throw Error('Choose a method before comparing prior tests.');if(intakeQuestions(draft).length)throw Error('Review the unanswered question before confirming.');confirmed=C.confirm(draft,{id:id(),at:now()});const q=C.queryForResearch(confirmed,{maxLength:6000}),compact=C.retrievalQuery(confirmed);
     if(cardContract)R.prepare(confirmed);
     else{
      if(q.needsShorter||compact.needsShorter){error='This idea exceeds the comparison’s length limit. Shorten the wording without removing important rules.';confirmed=null;render();return;}
      if(q.needsClarification){error='The interpretation still needs clarification before automatic comparison.';confirmed=null;render();return;}
     }
     stage='research';error='';message='';prepareCard();saveIntake(confirmed);compare();
    }catch(e){error=e.message;render();}
   });
   doc.getElementById('cancel')?.addEventListener('click',()=>{stop();message='Stopped waiting. Your confirmed idea is kept.';error='';render();});
   doc.getElementById('retry')?.addEventListener('click',()=>compare());
   doc.getElementById('reload')?.addEventListener('click',()=>load());
   doc.getElementById('print')?.addEventListener('click',()=>{if(packet){printHost.innerHTML=packetHTML(packet);printer();}});
  }
  async function json(url,options){const response=await fetcher(url,options);if(!response.ok)throw Error('Research is temporarily unavailable. Try again or read the related records.');return response.json();}
  function acceptDraft(value,notice=''){
   draft=value;
   if(legacyScope){draft=C.revise(draft,{scope:legacyScope});legacyScope=null;notice='The linked page selection is included below; the original wording is unchanged.';}
   stage='review';editing=false;error='';message=notice;render();focus('#review-title');
  }
  async function interpret(){
   stopInterpretation();const token=interpretVersion,text=raw;
   stage='interpreting';interpreting=true;interpretError='';error='';message='';render();focus('#interpret-title');
   try{
    while(!configResolved){
     await configReady;
     if(token!==interpretVersion||stage!=='interpreting'||text!==raw)return;
    }
    if(token!==interpretVersion||stage!=='interpreting'||text!==raw)return;
    if(!interpretationEndpoint){interpreting=false;acceptDraft(initialDraft(text));return;}
    P.validateInput(text);
    const requestController=new AbortController();interpretController=requestController;
    const timer=schedule(()=>requestController.abort(),30000);
    try{
     const response=await fetcher(interpretationEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text}),signal:requestController.signal});
     if(!response.ok)throw Error('Interpretation is unavailable. You can continue with your original wording.');
     const data=await response.json();
     const digest=await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
     const expected=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
     if(requestController.signal.aborted)throw Error('Interpretation timed out. Your original wording is kept.');
     if(token!==interpretVersion||stage!=='interpreting'||text!==raw)return;
     if(data.sourceBinding!==expected)throw Error('The interpretation did not match your wording. You can continue with the original.');
     const proposed=P.toDraft(text,data.candidate);
     interpreting=false;acceptDraft(proposed.draft);
    }finally{unschedule(timer);}
   }catch(e){
    if(token===interpretVersion&&stage==='interpreting'){
     interpreting=false;interpretError=e.name==='AbortError'?'Interpretation timed out. Your original wording is kept.':'The idea could not be interpreted reliably. You can continue with your original wording.';render();focus('#use-original');
    }
   }finally{if(token===interpretVersion){interpreting=false;interpretController=null;}}
  }
  function availability(){
   const status=doc.getElementById('status'),notice=doc.getElementById('error'),confirm=doc.getElementById('confirm');
   if(status)status.textContent=message||(!loaded&&!loadError?'Loading research records…':'');
   if(notice)notice.textContent=error||loadError;
   if(confirm)confirm.disabled=!loaded;
   const collection=doc.getElementById('collection-notice');if(collection){collection.hidden=!intakeEndpoint;collection.textContent=intakeEndpoint?'Confirmed ideas are saved for research review.':'';}
   const privacy=doc.querySelector('.privacy');if(privacy)privacy.textContent=endpoint?'Research questions are processed by Cloudflare. Don’t include private information.':'';
   const retry=doc.getElementById('reload');
   if(loaded)retry?.remove();
   else if(loadError&&!retry){host.insertAdjacentHTML('beforeend','<button id="reload" type="button">Retry loading research</button>');doc.getElementById('reload')?.addEventListener('click',()=>load());}
  }
  function loadConfig(){
   if(configValid||configAttempt&&!configResolved)return configAttempt;
   configResolved=false;
   // Interpretation needs configuration only. Settle that readiness separately
   // from registry download/validation/hash, without replacing any editor DOM.
   configAttempt=json('data/assistant.json',{signal:AbortSignal.timeout(8000)}).then(config=>{
    if(destroyed)return;
    if(!config||typeof config!=='object'||Array.isArray(config))throw Error('Research configuration could not be read.');
    endpoint=typeof config.endpoint==='string'&&/^https:\/\/[a-z0-9.-]+\/ask$/.test(config.endpoint)?config.endpoint:null;
    cardContract=config.researchContract==='card-v1';
    interpretationEndpoint=typeof config.interpretationEndpoint==='string'&&/^https:\/\/[a-z0-9.-]+\/interpret$/.test(config.interpretationEndpoint)?config.interpretationEndpoint:null;
    intakeEndpoint=typeof config.proposalEndpoint==='string'&&/^https:\/\/[a-z0-9.-]+\/proposals$/.test(config.proposalEndpoint)?config.proposalEndpoint:null;
    configValid=true;configResolved=true;availability();
   }).catch(e=>{
    if(!destroyed){endpoint=null;interpretationEndpoint=null;intakeEndpoint=null;cardContract=false;configValid=false;configResolved=true;availability();}
    throw e;
   });
   configReady=configAttempt.catch(()=>{});
   return configAttempt;
  }
  async function load(){
   const token=++loadVersion;loadError='';loaded=false;availability();
   const configured=loadConfig();
   try{
    const [registry]=await Promise.all([json('data/experiments.json',{signal:AbortSignal.timeout(8000)}),configured]);
    if(token!==loadVersion)return;
    if(!Array.isArray(registry.records))throw Error('Research records could not be read.');
    const published=registry.records.filter(r=>r.status==='published');
    if(!published.length)throw Error('No published research records are available.');
    const hash=await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(registry)));
    if(token!==loadVersion)return;
    records=published;documents=S.experimentDocs(records);
    registryId='sha256-json:'+Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
    loaded=true;
    availability();
    // Optional context cannot delay confirmation or rerender an editor/input.
    json('data/assistant-index.json',{signal:AbortSignal.timeout(5000)}).then(index=>{
     if(token!==loadVersion)return;
     documents.push(...(index.documents||[]).filter(d=>typeof d.id==='string'&&M.safe(d.href)));
    }).catch(()=>{});
   }catch(e){if(token!==loadVersion)return;loadError=e.message;loaded=false;}
   availability();
  }
  async function compare(){
   stop();const token=generation,snapshot=confirmed;
   if(!snapshot)return;
   if(!endpoint){error='Automatic comparison is unavailable. The related records remain available.';render();return;}
   let prepared,query,compact;
   try{prepared=cardContract?R.prepare(snapshot):null;query=prepared?{query:prepared.confirmedQuery,pages:prepared.pages}:C.queryForResearch(snapshot,{maxLength:6000});compact=prepared?{query:prepared.query}:C.retrievalQuery(snapshot);}
   catch(e){error=e.message;render();return;}
   if(!query.query||!compact.query){error='The confirmed wording cannot fit this comparison. Edit the idea before retrying.';render();return;}
   busy=true;message='';error='';render();const requestController=new AbortController();controller=requestController;
   const timer=schedule(()=>requestController.abort(),30000);
   try{
    const expectedBinding=prepared?await R.binding(prepared.request):null;
    if(token!==generation||confirmed!==snapshot)return;
    const body=prepared?prepared.request:{query:compact.query,confirmedQuery:query.query,pages:query.pages.length<=2?query.pages:[]};
    const data=await json(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:requestController.signal});
    if(token!==generation||confirmed!==snapshot)return;
    if(expectedBinding&&data.claimBinding!==expectedBinding)throw Error('This response does not match your confirmed idea. Try the comparison again.');
    if(!data.answer&&data.reason==='no-matching-records'){
     const answer='No close research record was returned for this confirmed idea. The search covered the published research index; it does not establish that nobody has tried the idea.\n\nYou can edit the method wording or inspect the research index. Without a closer record, this comparison cannot judge what has already been tested or whether another run would add useful evidence.';
     const research=C.bindResearch(snapshot,{id:id(),at:now(),evidence:{snapshotId:registryId,records:[],documents:[],search:{query:compact.query,reason:data.reason}},answer});
     packet=C.packetSnapshot(snapshot,research);result=Object.freeze({answer,sources:[],noMatch:true});printHost.innerHTML=packetHTML(packet);return;
    }
    const checked=validateAnswer(data,documents);
    const evidenceRecords=records.filter(r=>checked.sources.some(s=>s.kind==='experiment'&&s.id===r.id));
    if(!evidenceRecords.length)throw Error('No research record supports this comparison.');
    const research=C.bindResearch(snapshot,{id:id(),at:now(),evidence:{snapshotId:registryId,records:evidenceRecords,documents:checked.sources},answer:checked.answer});
    packet=C.packetSnapshot(snapshot,research);result=Object.freeze(checked);printHost.innerHTML=packetHTML(packet);
   }catch(e){if(token===generation)error=e.name==='AbortError'?'The comparison timed out. Your confirmed idea is kept; try again.':e.message;}
   finally{unschedule(timer);if(token===generation){busy=false;controller=null;render();}}
  }
  render();const ready=load();
  return {ready,getSnapshot:()=>({stage,draft,confirmed,result,packet,busy,interpreting}),destroy:()=>{destroyed=true;loadVersion++;stopInterpretation();stopIntake(true);stop();}};
 }
 const api={parseScope,initialDraft,intakeQuestions,answerIntake,compactPages,validateAnswer,rowsHTML,sourceHTML,packetHTML,scopeEditorText,scopeEdit,ruleNotesText,ruleEdits,captureDisclosureState,restoreDisclosureState,readRecovery,createApp};
 if(typeof module!=='undefined')module.exports=api;
 else{root.Investigate=api;if(root.document?.getElementById('investigate'))root.investigateApp=createApp(root.document);}
})(globalThis);
