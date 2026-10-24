/* Pure interpretation/snapshot model. No retrieval, execution or coverage inference. */
(function(root) {
  'use strict';
  const SCHEMA='liberpedia-claim-specification-v1';
  const STATES=['specified','unspecified','not_applicable','unrestricted'];
  const ORIGINS=['supplied','user_clarification','project_context','proposed'];
  const RULES=['representation','wordBoundaries','boundaryMode','unmapped','inputVersion',
    'evaluation','reset','initialState','searchBounds','searchProtocol','exceptionalCases'];
  const BOUNDARIES={
    within_words:'Reverse runes inside each word; keep word order.',
    fixed_spaces:'Reverse the rune sequence; keep space positions.',
    word_blocks:'Reverse whole-word order; keep each word unchanged.'
  };
  const OPERATIONS={reverse_row_runes:'Reverse rune order within rows',
    reverse_value_digits:'Reverse decimal digits of each value'};
  const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  function copy(value) {
    if(value===null||typeof value==='string'||typeof value==='boolean')return value;
    if(typeof value==='number'&&Number.isFinite(value))return value;
    if(Array.isArray(value))return value.map(copy);
    if(value&&typeof value==='object'&&(Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null)){
      const out={};
      for(const key of Object.keys(value)){
        if(['__proto__','prototype','constructor'].includes(key))throw Error('Unsafe object key');
        out[key]=copy(value[key]);
      }
      return out;
    }
    throw Error('Expected JSON data');
  }
  function stable(value) {
    if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
    if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
    return JSON.stringify(value);
  }
  function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
  function field(status='unspecified',value,provenance={kind:'proposed',refs:[]}) {
    if(!STATES.includes(status))throw Error('Invalid field state');
    if(!ORIGINS.includes(provenance.kind)||!Array.isArray(provenance.refs)||provenance.refs.some(r=>typeof r!=='string'))throw Error('Invalid field provenance');
    if(status==='specified'&&value===undefined)throw Error('Specified fields need an explicit value');
    if(status!=='specified'&&value!==undefined)throw Error('Only specified fields have values');
    return {status,...(status==='specified'?{value:copy(value)}:{}),provenance:copy(provenance)};
  }
  function checkedField(value){
    if(!value||typeof value!=='object')throw Error('Expected a stateful field');
    return field(value.status,value.value,value.provenance);
  }
  function pages(values){
    if(!Array.isArray(values)||values.some(p=>typeof p!=='string'||!/^lp[12]-\d{2}$/.test(p)||Number(p.slice(4))>(p.startsWith('lp1')?16:57)))throw Error('Invalid exact page set');
    return [...new Set(values)].sort();
  }
  function normalizeScope(value){
    const f=checkedField(value);
    if(f.status==='specified'){
      if(!f.value||typeof f.value!=='object'||Array.isArray(f.value))throw Error('Scope needs an object');
      if(own(f.value,'pages'))f.value.pages=pages(f.value.pages);
      // Never expand page sets to their envelope, or infer whole-page coverage.
    }
    return f;
  }
  function normalizeMethod(value){
    const f=checkedField(value);
    if(f.status==='specified'){
      if(!f.value||!Array.isArray(f.value.operations)||!f.value.operations.length||f.value.operations.some(o=>!o||typeof o.id!=='string'||!o.id.trim()))throw Error('Method needs ordered operations');
    }
    return f;
  }
  function createDraft({source,aim=field(),method=field(),scope=field(),rules={},unresolved=[]}={}) {
    if(!source||typeof source.text!=='string')throw Error('Preserve original source text');
    if(!Array.isArray(source.materials??[]))throw Error('Invalid material list');
    const material=(source.materials??[]).map(m=>{
      if(!m||typeof m.name!=='string')throw Error('Material needs a name');
      const x=copy(m);if(!own(x,'contentStatus'))x.contentStatus='metadata_only';return x;
    });
    const knownRules={};
    for(const key of RULES)knownRules[key]=own(rules,key)?checkedField(rules[key]):field();
    for(const key of Object.keys(rules))if(!RULES.includes(key))throw Error('Preserve unknown rules in unresolved constraints');
    if(!Array.isArray(unresolved))throw Error('Unresolved constraints must be a list');
    return {schema:SCHEMA,revision:1,status:'draft',execution:'not_run',
      source:{...copy(source),materials:material},aim:checkedField(aim),method:normalizeMethod(method),scope:normalizeScope(scope),
      rules:knownRules,unresolved:copy(unresolved),clarifications:[],confirmation:null};
  }
  // Arbitrary prose/code is preserved, never interpreted through fictional fixtures.
  function fromText(text,materials=[]){return createDraft({source:{text,materials}});}
  function operations(spec){return spec.method.status==='specified'?spec.method.value.operations:[];}
  function has(spec,id){return operations(spec).some(o=>o.id===id);}
  function specified(f,value){return f.status==='specified'&&(arguments.length===1||f.value===value);}
  function questions(spec){
    const result=[];
    if(spec.unresolved.some(c=>c&&c.kind==='operation_ambiguity'))result.push({id:'operation',prompt:'What should be reversed?',choices:[
      {id:'reverse_row_runes',label:OPERATIONS.reverse_row_runes,example:'13,19,37 → 37,19,13'},
      {id:'reverse_value_digits',label:OPERATIONS.reverse_value_digits,example:'13,19,37 → 31,91,73'},
      {id:'other',label:'Other',requiresText:true}]});
    if(has(spec,'reverse_row_runes')&&specified(spec.rules.wordBoundaries,'preserve')&&
       !(specified(spec.rules.boundaryMode)&&own(BOUNDARIES,spec.rules.boundaryMode.value)))result.push({
      id:'word-boundary',prompt:'How should the words change?',example:'AB CDE',choices:[
        {id:'within_words',label:BOUNDARIES.within_words,example:'BA EDC'},
        {id:'fixed_spaces',label:BOUNDARIES.fixed_spaces,example:'ED CBA'},
        {id:'word_blocks',label:BOUNDARIES.word_blocks,example:'CDE AB'},
        {id:'other',label:'Other',requiresText:true}]});
    return result;
  }
  function revise(draft,patch){
    if(!draft||draft.schema!==SCHEMA)throw Error('Invalid draft');
    const allowed=['aim','method','scope','rules','appendUnresolved'];
    if(!patch||Object.keys(patch).some(k=>!allowed.includes(k)))throw Error('Unsupported patch');
    const next=copy(draft);next.status='draft';next.execution='not_run';next.confirmation=null;next.revision++;
    if(own(patch,'aim'))next.aim=checkedField(patch.aim);
    if(own(patch,'scope'))next.scope=normalizeScope(patch.scope);
    if(own(patch,'method'))next.method=normalizeMethod(patch.method);
    if(own(patch,'rules'))for(const [key,value] of Object.entries(patch.rules)){
      if(!RULES.includes(key))throw Error('Unknown rule; append an unresolved constraint');
      next.rules[key]=checkedField(value);
    }
    if(own(patch,'appendUnresolved')){
      if(!Array.isArray(patch.appendUnresolved))throw Error('Invalid constraints');
      next.unresolved.push(...copy(patch.appendUnresolved));
    }
    // Changed procedures must revalidate the interpretation, never inherit a
    // now-inapplicable boundary answer when switching away and back.
    if(own(patch,'method')&&stable(draft.method)!==stable(next.method)&&!own(patch.rules||{},'boundaryMode')){
      next.rules.boundaryMode=field();
    }
    return next;
  }
  function clarify(draft,id,choice,text=''){
    const question=questions(draft).find(q=>q.id===id);
    if(!question||!question.choices.some(c=>c.id===choice))throw Error('Unavailable clarification');
    const provenance={kind:'user_clarification',refs:[id]};
    let next;
    if(choice==='other'){
      if(typeof text!=='string'||!text.trim())throw Error('Other needs an explanation');
      next=revise(draft,{appendUnresolved:[{kind:'custom_interpretation',question:id,text,provenance}]});
      // Preserve the ambiguity until a supported interpretation is explicitly
      // supplied. Recording free text does not mean understanding it.
    }else if(id==='operation'){
      const index=draft.unresolved.findIndex(c=>c?.kind==='operation_ambiguity');
      const ambiguity=draft.unresolved[index];
      const list=copy(operations(draft));
      const slot=ambiguity.operationIndex??0;
      if(!Number.isInteger(slot)||slot<0||(list.length>1&&!own(ambiguity,'operationIndex'))||slot>Math.max(0,list.length-1))throw Error('Identify the ambiguous operation in a compound method');
      list[slot]={...(list[slot]||{}),id:choice};
      if(!own(list[slot],'sourceText')&&typeof list[slot].label==='string')list[slot].sourceText=list[slot].label;
      delete list[slot].label; // The old ambiguous wording is not the chosen operation's label.
      next=revise(draft,{method:field('specified',{...((draft.method.status==='specified'&&draft.method.value)||{}),operations:list},provenance)});
      next.unresolved.splice(index,1);
    }else{
      next=revise(draft,{rules:{boundaryMode:field('specified',choice,provenance)}});
    }
    next.clarifications.push({question:id,choice,...(choice==='other'?{text}:{}),revision:next.revision});
    return next;
  }
  function completeness(spec){
    const missing=[];
    for(const name of ['aim','method','scope'])if(spec[name].status==='unspecified')missing.push(name);
    for(const name of RULES)if(spec.rules[name].status==='unspecified')missing.push('rules.'+name);
    function nested(value,path){
      if(!value||typeof value!=='object')return;
      if(value.status==='unspecified')missing.push(path);
      for(const [key,item] of Object.entries(value))if(key!=='provenance')nested(item,path+'.'+key);
    }
    for(const name of ['aim','method','scope'])if(spec[name].status==='specified')nested(spec[name].value,name+'.value');
    for(const name of RULES)if(spec.rules[name].status==='specified')nested(spec.rules[name].value,'rules.'+name+'.value');
    const ambiguities=questions(spec).map(q=>q.id);
    const unsupported=spec.unresolved.length>0;
    return {researchReady:spec.method.status==='specified'&&!ambiguities.length&&!unsupported,
      executionReady:!missing.length&&!ambiguities.length&&!unsupported,
      missing,ambiguities,unresolved:copy(spec.unresolved)};
  }
  function display(f,label){
    if(f.status==='specified')return typeof f.value==='string'?f.value:JSON.stringify(f.value);
    return {unspecified:label+' not specified',not_applicable:label+' not applicable',unrestricted:label+' explicitly unrestricted'}[f.status];
  }
  const RULE_LABELS={representation:'Representation',wordBoundaries:'Word boundaries',boundaryMode:'Word handling',
    unmapped:'Unmapped values',inputVersion:'Input version',evaluation:'Evaluation',reset:'Restart rule',
    initialState:'Initial state',searchBounds:'Search bounds',searchProtocol:'Search protocol',exceptionalCases:'Exceptional cases'};
  function ruleText(key,f){
    if(f.status==='unspecified')return RULE_LABELS[key]+': not decided';
    if(f.status==='unrestricted')return RULE_LABELS[key]+': explicitly unrestricted';
    if(key==='wordBoundaries'&&f.value==='preserve')return 'Preserve word boundaries';
    if(key==='boundaryMode'&&own(BOUNDARIES,f.value))return {within_words:'Keep word order',fixed_spaces:'Keep space positions',word_blocks:'Keep each word unchanged'}[f.value];
    if(key==='unmapped'&&f.value==='keep_original')return 'Keep unmapped values unchanged';
    if(key==='unmapped'&&f.value==='reject')return 'Reject unmapped values';
    return RULE_LABELS[key]+': '+display(f,RULE_LABELS[key]);
  }
  function reviewRows(spec){
    const methodTags=operations(spec).map((o,i)=>({id:'operation:'+i,text:o.label||OPERATIONS[o.id]||o.id,unknown:false}));
    if(has(spec,'reverse_row_runes')&&specified(spec.rules.boundaryMode)&&own(BOUNDARIES,spec.rules.boundaryMode.value)){
      const i=operations(spec).findIndex(o=>o.id==='reverse_row_runes');methodTags[i].text=BOUNDARIES[spec.rules.boundaryMode.value];
    }
    const scopeTags=[];
    if(spec.scope.status==='specified'){
      for(const p of spec.scope.value.pages||[])scopeTags.push({id:p,text:p.toUpperCase(),unknown:false});
      for(const [key,value] of Object.entries(spec.scope.value))if(key!=='pages')scopeTags.push({id:'scope:'+key,text:key+': '+(typeof value==='string'?value:JSON.stringify(value)),unknown:false});
      if(!scopeTags.length)scopeTags.push({id:'scope:empty',text:'Explicit empty selection',unknown:false});
    }else scopeTags.push({id:'scope:'+spec.scope.status,text:display(spec.scope,'Scope'),unknown:spec.scope.status==='unspecified'});
    return [
      {label:'Aim',tags:[{id:'aim',text:display(spec.aim,'Aim'),unknown:spec.aim.status==='unspecified'}]},
      {label:'Method',tags:methodTags.length?methodTags:[{id:'method:unknown',text:display(spec.method,'Method'),unknown:spec.method.status==='unspecified'}]},
      {label:'Scope',tags:scopeTags},
      {label:'Rules',tags:RULES.filter(key=>spec.rules[key].status==='specified'||spec.rules[key].status==='unrestricted'||
        (key==='unmapped'&&has(spec,'reverse_value_digits')&&spec.rules[key].status==='unspecified'))
        .map(key=>({id:'rule:'+key,text:ruleText(key,spec.rules[key]),unknown:spec.rules[key].status==='unspecified'}))},
      ...(spec.unresolved.length?[{label:'Unresolved',details:copy(spec.unresolved)}]:[])
    ];
  }
  function meaning(spec){return {aim:spec.aim,method:spec.method,scope:spec.scope,rules:spec.rules,unresolved:spec.unresolved};}
  function summary(spec){return reviewRows(spec).filter(r=>r.label!=='Unresolved'&&r.tags.length).map(r=>r.label+': '+r.tags.map(t=>t.text).join('; ')).join('. ')+'.';}
  function confirm(draft,{id,at}={}){
    if(!id||typeof id!=='string'||!at||!Number.isFinite(Date.parse(at)))throw Error('Confirmation needs an ID and timestamp');
    if(questions(draft).length)throw Error('Resolve consequential ambiguity before confirmation');
    const snapshot=copy(draft),ready=completeness(draft);
    snapshot.status=ready.executionReady?'confirmed_specified':'confirmed_incomplete';
    snapshot.execution='not_run';snapshot.confirmation={id,at};snapshot.canonical=summary(snapshot);
    return freeze(snapshot);
  }
  function validateConfirmed(value){
    if(!value||value.schema!==SCHEMA||!Number.isInteger(value.revision)||value.revision<1||
      !['confirmed_incomplete','confirmed_specified'].includes(value.status)||value.execution!=='not_run'||!value.confirmation)throw Error('Expected a confirmed interpretation');
    const rebuilt=createDraft({source:value.source,...meaning(value)});
    const expected=confirm(rebuilt,value.confirmation);
    if(value.status!==expected.status||value.canonical!==expected.canonical)throw Error('Inconsistent confirmation snapshot');
    return freeze(copy(value));
  }
  function binding(confirmed){const s=validateConfirmed(confirmed);return stable({schema:SCHEMA,revision:s.revision,source:s.source,...meaning(s),confirmation:s.confirmation});}
  function queryForResearch(confirmed,{maxLength=1500}={}){
    const snapshot=validateConfirmed(confirmed);
    if(!Number.isInteger(maxLength)||maxLength<1)throw Error('Invalid query limit');
    if(!completeness(snapshot).researchReady)return {query:null,needsClarification:true,needsShorter:false};
    const compact=f=>f.status==='specified'?{status:f.status,value:f.value}:{status:f.status};
    const rules=Object.fromEntries(RULES.map(k=>[k,compact(snapshot.rules[k])]));
    const query=['Confirmed interpretation; not an executed experiment.',
      'Aim: '+stable(compact(snapshot.aim)),
      'Method (ordered): '+stable(compact(snapshot.method)),
      'Scope: '+stable(compact(snapshot.scope)),
      'Rules: '+stable(rules),
      'Original wording (separate from interpretation):\n'+snapshot.source.text,
      ...(snapshot.source.materials.length?['Materials: '+stable(snapshot.source.materials)]:[])].join('\n');
    const selectedPages=snapshot.scope.status==='specified'?(snapshot.scope.value.pages||[]):[];
    if(query.length>maxLength)return {query:null,pages:copy(selectedPages),needsShorter:true,needsClarification:false,length:query.length,maxLength};
    return {query,pages:copy(selectedPages),needsShorter:false,needsClarification:false,length:query.length,maxLength};
  }
  function retrievalQuery(confirmed,{maxLength=1500}={}){
    const s=validateConfirmed(confirmed);
    if(!Number.isInteger(maxLength)||maxLength<1)throw Error('Invalid query limit');
    const parts=[];
    if(s.aim.status==='specified')parts.push(display(s.aim,'Aim'));
    parts.push(...reviewRows(s).find(r=>r.label==='Method').tags.map(t=>t.text));
    if(s.scope.status==='specified'){
      parts.push(...(s.scope.value.pages||[]).map(p=>p.toUpperCase()));
      for(const [key,value] of Object.entries(s.scope.value))if(key!=='pages')parts.push(key+': '+stable(value));
    }
    parts.push(...reviewRows(s).find(r=>r.label==='Rules').tags.filter(t=>!t.unknown).map(t=>t.text));
    const query=parts.join('. ');
    return {query:query.length<=maxLength?query:null,needsShorter:query.length>maxLength,length:query.length,maxLength};
  }
  function bindResearch(confirmed,{id,at,evidence,answer,openQuestions=[],proposedTests=[]}={}){
    const snapshot=validateConfirmed(confirmed);
    if(!completeness(snapshot).researchReady)throw Error('Interpretation is not ready for automatic comparison');
    if(typeof id!=='string'||!id||!Number.isFinite(Date.parse(at))||typeof answer!=='string'||!evidence||typeof evidence.snapshotId!=='string'||!Array.isArray(evidence.records))throw Error('Research needs a dated evidence snapshot');
    for(const r of evidence.records)if(!r||typeof r.id!=='string'||r.status!=='published'||!r.scope||!own(r,'finding')||!own(r,'limitations'))throw Error('Use complete published evidence, not retrieval titles');
    // Coverage, novelty and merit are deliberately not inferred from lexical
    // similarity, a family label, or a page-set subset.
    return freeze({schema:'liberpedia-claim-research-v1',id,at,claimBinding:binding(snapshot),
      confirmed:snapshot,evidence:copy(evidence),answer,openQuestions:copy(openQuestions),
      proposedTests:proposedTests.map(test=>({...copy(test),execution:'not_run'}))});
  }
  function packetSnapshot(confirmed,result){
    const snapshot=validateConfirmed(confirmed);
    if(!result||result.schema!=='liberpedia-claim-research-v1'||result.claimBinding!==binding(snapshot)||binding(result.confirmed)!==binding(snapshot))throw Error('Research belongs to another confirmed revision');
    return freeze({schema:'liberpedia-claim-packet-v1',confirmed:snapshot,research:copy(result)});
  }
  const api={SCHEMA,STATES,RULES,BOUNDARIES,field,pages,createDraft,fromText,revise,clarify,questions,
    completeness,reviewRows,summary,confirm,validateConfirmed,binding,queryForResearch,retrievalQuery,bindResearch,packetSnapshot,serialize:stable};
  if(typeof module!=='undefined')module.exports=api;else root.ClaimSpecification=api;
})(globalThis);
