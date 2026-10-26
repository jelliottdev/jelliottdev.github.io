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
  // Intent categories, never success criteria or findings. Expand by editing
  // this registry deliberately; visitor wording cannot mint another category.
  const OUTCOMES=Object.freeze({decipher:'Decipher the text',measure:'Test a pattern',
    reproduce:'Reproduce a result',explain:'Explain a feature',verify_source:'Verify source material'});
  const EVALUATION_CHOICES=freeze([
    {id:'language-samples',label:'Compare patterns with language samples',example:'Compare short rune patterns with eight fixed language samples. Similarity is not a translation.',value:{kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'}},
    {id:'readable-text',label:'Look for readable text — not available yet',example:'The browser cannot judge readability with this option yet.',value:{kind:'readability'}},
    {id:'warning-opening',label:'Match an already-decoded opening',example:'Check the first 12 runes against the opening of the decoded Warning passage. This checks page starts only.',value:{kind:'exact-prefix',values:[24,7,24,4,9,21,17,18,20,10,18,1]}},
    {id:'inspect-output',label:'Show what the rule produces',example:'Show the resulting runes and counts for you to inspect.',value:'measurement'}
  ]);
  function evaluationText(value){
    if(value?.kind==='exact-prefix-set'&&Array.isArray(value.openings)&&value.openings.length>=1&&value.openings.length<=32)return 'Compare the output openings with '+value.openings.length+' supplied rune sequences. A match is not a complete reading.';
    const choice=EVALUATION_CHOICES.find(item=>stable(item.value)===stable(value));
    if(!choice)return null;
    return choice.label+(choice.id==='language-samples'?' — eight fixed samples; similarity is not a translation.':choice.id==='readable-text'?'':choice.id==='inspect-output'?' — runes and counts, without a readability verdict.':' — first 12 runes of the decoded Warning passage, at page starts only.');
  }
  function evaluationQuestion(spec){
    if(normalizeOutcome(spec.aim).id!=='decipher'||spec.method?.status!=='specified'||!['unspecified','not_applicable','unrestricted'].includes(spec.rules?.evaluation?.status))return null;
    return {id:'evaluation',prompt:'What should this check look for?',...(spec.rules.evaluation.status!=='unspecified'?{context:'A bounded decoding test needs a specific check.'}:{}),choices:EVALUATION_CHOICES.map(({value,...choice})=>({...choice}))};
  }
  const OUTCOME_ALIASES=Object.freeze({
    decipher:['decipher','decipher the text','decipher lp2','decrypt','decrypt the text','decrypt lp2','solve lp2','solving lp2','solving','solve liber primus','find readable text','find plaintext','recover plaintext','produce readable text','find readable plaintext'],
    measure:['measure','test a pattern','test a statistical effect','test statistical effect','measure a pattern','test a statistical pattern'],
    reproduce:['reproduce','reproduce a result','reproduce an existing result','replicate a result','rerun a result'],
    explain:['explain','explain a feature','explain a manuscript feature'],
    verify_source:['verify source material','verify the source','check source material','verify a transcription','check a transcription']
  });
  const METHOD_FAMILIES=Object.freeze({
    'fixed-substitution':'Fixed alphabet substitutions',polyalphabetic:'Repeating-key and polyalphabetic ciphers',
    feedback:'Autokey and ciphertext feedback',transposition:'Transposition and permutations',
    'prime-indices':'Prime indexing and value transforms','number-streams':'Arithmetic keystreams',
    'book-codes':'Book ciphers and coordinate lookups',repetition:'Repeats, doublets and word structure'
  });
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
  function normalizeOutcome(value){
    if(value&&typeof value==='object'&&own(value,'status'))value=value.status==='specified'?value.value:undefined;
    let wording='',detail='',explicit;
    if(typeof value==='string')wording=detail=value;
    else if(value&&typeof value==='object'&&!Array.isArray(value)){
      explicit=value.outcomeId;
      wording=typeof value.wording==='string'?value.wording:typeof value.detail==='string'?value.detail:'';
      detail=typeof value.detail==='string'?value.detail:wording;
    }
    let id='unclassified';
    if(typeof explicit==='string'&&own(OUTCOMES,explicit))id=explicit;
    else if(explicit===undefined||explicit==='unclassified'){
      // A custom choice cannot mint a second category for an exact alias.
      // Its edited detail is authoritative over preserved original wording.
      const current=explicit==='unclassified'&&typeof value.detail==='string'?detail:wording;
      const alias=current.trim().toLowerCase().replace(/[.!?]$/,'').trim();
      for(const [candidate,aliases] of Object.entries(OUTCOME_ALIASES))if(aliases.includes(alias)||OUTCOMES[candidate].toLowerCase()===alias){id=candidate;break;}
    }
    return {id,label:own(OUTCOMES,id)?OUTCOMES[id]:'Aim not classified',wording,detail};
  }
  function normalizeAim(value){
    const f=checkedField(value);
    // Recompute derived metadata; supplied .outcome is never authoritative.
    if(f.status==='specified')f.outcome=normalizeOutcome(f.value);
    return f;
  }
  function outcomeLabel(value){
    if(typeof value==='string'&&own(OUTCOMES,value))return OUTCOMES[value];
    if(value&&typeof value==='object'&&own(value,'status')&&value.status!=='specified')return display(value,'Aim');
    return normalizeOutcome(value).label;
  }
  function classifyMethod(value){
    const f=normalizeMethod(value);
    if(f.status!=='specified')return {familyIds:[],complete:false,operations:[]};
    const ids={caesar:'fixed-substitution',caesar_shift:'fixed-substitution',atbash:'fixed-substitution',
      affine_substitution:'fixed-substitution',vigenere:'polyalphabetic',vigenere_cipher:'polyalphabetic',
      repeating_key:'polyalphabetic',autokey:'feedback',ciphertext_autokey:'feedback',plaintext_autokey:'feedback',
      transposition:'transposition',reverse_row_runes:'transposition',reverse_word_order:'transposition',reverse_runes:'transposition',
      prime_value_mapping:'prime-indices',prime_mapping:'prime-indices',prime_index:'prime-indices',reverse_prime_digits:'prime-indices',
      word_affine_count:'repetition',word_prime_sums:'prime-indices',interrupted_repeating_key:'polyalphabetic',finite_key:'number-streams',finite_key_bank:'number-streams',prime_keystream:'number-streams',numeric_keystream:'number-streams',book_cipher:'book-codes',book_code:'book-codes'};
    const rows=f.value.operations.map((operation,index)=>{
      const text=typeof operation.label==='string'?operation.label:typeof operation.sourceText==='string'?operation.sourceText:'';
      const evidence=[operation.label,operation.sourceText].filter(t=>typeof t==='string'&&
        !(operation.id==='family_selection'&&t===METHOD_FAMILIES[operation.familyId])).join('\n ');
      const unsafe=/\b(?:not|never|unless|except|excluding|if|when|without|only|instead|otherwise|but|then|after|before|and)\b|\bdon['’]t\b|[`{}]|=>|\b(?:const|function|return|def)\b/i.test(evidence)||[operation.label,operation.sourceText].some(t=>typeof t==='string'&&t.includes('\n'));
      let familyId='unclassified',basis='unclassified';
      if(!unsafe){
        if(operation.id==='family_selection'&&own(METHOD_FAMILIES,operation.familyId)){familyId=operation.familyId;basis='explicit_family';}
        else if(own(ids,operation.id)){familyId=ids[operation.id];basis='operation_id';}
        else{
          const name=text.trim().replace(/[.]$/,'');
          if(/^(?:apply |use )?(?:Caesar(?: cipher| shift)?|shift cipher)(?: with (?:shift|key) [+-]?\d+)?$/i.test(name))familyId='fixed-substitution';
          else if(/^(?:apply |use )?Vigen[eè]re(?: cipher)?(?: with (?:the )?key (?:[\w-]+|"[^"\n]+"|'[^'\n]+'))?$/i.test(name))familyId='polyalphabetic';
          else if(/^(?:apply |use )?(?:(?:plaintext|ciphertext) )?autokey(?: cipher)?$/i.test(name))familyId='feedback';
          else if(/^(?:apply |use )?(?:transposition|reverse rune order within rows|reverse each row)$/i.test(name))familyId='transposition';
          else if(/^(?:apply |use )?(?:prime index mapping|prime value mapping|reverse (?:the )?(?:decimal )?digits of each prime value)$/i.test(name))familyId='prime-indices';
          else if(/^(?:apply |use )?(?:book cipher|book code)$/i.test(name))familyId='book-codes';
          if(familyId!=='unclassified')basis='anchored_name';
        }
      }
      if(own(METHOD_FAMILIES,operation.declaredFamilyId)){
        if(familyId!=='unclassified'&&familyId!==operation.declaredFamilyId){familyId='unclassified';basis='category_conflict';}
        else if(!unsafe){familyId=operation.declaredFamilyId;basis='declared_family';}
      }
      return {index,familyId,label:own(METHOD_FAMILIES,familyId)?METHOD_FAMILIES[familyId]:'Method not classified',basis,
        ...(own(operation,'declaredFamilyId')?{declaredFamilyId:operation.declaredFamilyId}:{}),operation:copy(operation)};
    });
    return {familyIds:[...new Set(rows.filter(r=>r.familyId!=='unclassified').map(r=>r.familyId))],complete:rows.every(r=>r.familyId!=='unclassified'),operations:rows};
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
  function createDraft({source,aim=field(),method=field(),scope=field(),rules={},unresolved=[],methodEdits=[]}={}) {
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
    if(!Array.isArray(methodEdits))throw Error('Method history must be a list');
    return {schema:SCHEMA,revision:1,status:'draft',execution:'not_run',
      source:{...copy(source),materials:material},aim:normalizeAim(aim),method:normalizeMethod(method),scope:normalizeScope(scope),
      rules:knownRules,unresolved:copy(unresolved),methodEdits:copy(methodEdits),clarifications:[],confirmation:null};
  }
  // Arbitrary prose/code is preserved, never interpreted through fictional fixtures.
  function fromText(text,materials=[]){return createDraft({source:{text,materials}});}
  function operations(spec){return spec.method.status==='specified'?spec.method.value.operations:[];}
  function has(spec,id){return operations(spec).some(o=>o.id===id);}
  function specified(f,value){return f.status==='specified'&&(arguments.length===1||f.value===value);}
  function questions(spec){
    const result=[];
    for(const constraint of spec.unresolved.filter(c=>c?.kind==='changed_method_rule'&&RULES.includes(c.field))){
      result.push({id:'rule-review:'+constraint.field,prompt:'Does this condition still apply?',
        context:ruleText(constraint.field,spec.rules[constraint.field]),choices:[
          {id:'keep',label:'Keep this condition'},
          {id:'replace',label:'Replace it',requiresText:true,fieldLabel:'Write the condition for the edited method'},
          {id:'remove',label:'Remove this condition'}]});
    }
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
    if(own(patch,'aim'))next.aim=normalizeAim(patch.aim);
    else next.aim=normalizeAim(next.aim);
    if(own(patch,'scope'))next.scope=normalizeScope(patch.scope);
    if(own(patch,'method'))next.method=normalizeMethod(patch.method);
    if(own(patch,'rules'))for(const [key,value] of Object.entries(patch.rules)){
      if(!RULES.includes(key))throw Error('Unknown rule; append an unresolved constraint');
      next.rules[key]=checkedField(value);
      if(next.rules[key].status!=='unspecified'){
        const linked=(draft.rules[key].provenance.refs||[]).filter(ref=>/^method:operation:\d+$/.test(ref));
        next.rules[key].provenance.refs=[...new Set([...next.rules[key].provenance.refs,...linked])];
      }
      // An explicit rule edit also resolves its dependency on an older step.
      next.unresolved=next.unresolved.filter(c=>!(c?.kind==='changed_method_rule'&&c.field===key));
    }
    if(own(patch,'appendUnresolved')){
      if(!Array.isArray(patch.appendUnresolved))throw Error('Invalid constraints');
      next.unresolved.push(...copy(patch.appendUnresolved));
    }
    // Boundary handling belongs to the reversal operation, not every sibling
    // cipher. Adding an independent step must not erase its explicit answer.
    const reversalMeaning=s=>operations(s).filter(o=>o.id==='reverse_row_runes').map(o=>{
      const semantic=copy(o);delete semantic.declaredFamilyId;return semantic;
    });
    if(own(patch,'method')&&stable(reversalMeaning(draft))!==stable(reversalMeaning(next))&&!own(patch.rules||{},'boundaryMode')){
      next.rules.boundaryMode=field();
    }
    return next;
  }
  function sourceRanges(provenance,text){
    return (provenance?.refs||[]).flatMap(ref=>{
      try{
        const span=JSON.parse(ref);
        return span?.source==='original wording'&&Number.isInteger(span.start)&&Number.isInteger(span.end)&&
          span.start>=0&&span.end>span.start&&span.end<=text.length&&typeof span.quote==='string'&&
          text.slice(span.start,span.end)===span.quote?[span]:[];
      }catch{return [];}
    });
  }
  function applyMethodEdit(draft,edit){
    if(!edit||!['add','remove','move','wording','replace','category'].includes(edit.type))throw Error('Unknown method edit');
    const prior=operations(draft),list=copy(prior),count=list.length;
    const add=edit.type==='add';
    if(!Number.isInteger(edit.index)||edit.index<0||edit.index>(add?count:count-1))throw Error('Invalid operation index');
    const map=Array.from({length:count},(_,i)=>i),archived=[];
    const old=edit.index<count?copy(list[edit.index]):null;
    let changedIndex=null;
    if(edit.type==='add'){
      list.splice(edit.index,0,copy(edit.operation));
      for(let i=edit.index;i<count;i++)map[i]++;
    }else if(edit.type==='remove'){
      list.splice(edit.index,1);map[edit.index]=null;
      for(let i=edit.index+1;i<count;i++)map[i]--;
    }else if(edit.type==='move'){
      if(!Number.isInteger(edit.toIndex)||edit.toIndex<0||edit.toIndex>=count)throw Error('Invalid destination index');
      const order=Array.from({length:count},(_,i)=>i),[moved]=order.splice(edit.index,1);order.splice(edit.toIndex,0,moved);
      list.splice(0,count,...order.map(i=>copy(prior[i])));order.forEach((original,current)=>{map[original]=current;});
    }else if(edit.type==='wording'){
      if(typeof edit.text!=='string'||!edit.text.trim())throw Error('Operation wording required');
      const current=old.label||OPERATIONS[old.id]||old.id;
      if(edit.text===current)return copy(draft);
      list[edit.index]={id:'described_method',label:edit.text,
        sourceText:typeof old.sourceText==='string'?old.sourceText:current,
        provenance:{kind:'user_clarification',refs:['method:operation:'+edit.index]}};
      changedIndex=edit.index;
    }else if(edit.type==='replace'){
      list[edit.index]=copy(edit.operation);changedIndex=edit.index;
    }else{
      if(edit.familyId!==null&&!own(METHOD_FAMILIES,edit.familyId))throw Error('Unknown method family');
      if(edit.familyId===null)delete list[edit.index].declaredFamilyId;
      else list[edit.index].declaredFamilyId=edit.familyId;
    }
    const unresolved=[];
    for(const constraint of draft.unresolved){
      const implicitSingle=constraint?.kind==='operation_ambiguity'&&!own(constraint,'operationIndex')&&count===1;
      if(!Number.isInteger(constraint?.operationIndex)&&!implicitSingle){unresolved.push(copy(constraint));continue;}
      const i=implicitSingle?0:constraint.operationIndex;
      if(i<0||i>=count)throw Error('Constraint references missing operation');
      if(map[i]===null||i===changedIndex){archived.push(copy(constraint));continue;}
      unresolved.push({...copy(constraint),operationIndex:map[i]});
    }
    const value=draft.method.status==='specified'?copy(draft.method.value):{operations:[]};
    value.operations=list;
    const receipt={revision:draft.revision+1,type:edit.type,index:edit.index,
      ...(edit.type==='move'?{toIndex:edit.toIndex}:{}),indexMap:map,
      ...(old?{previousOperation:old}:{}),...(archived.length?{retiredConstraints:archived}:{})};
    // Empty method retains its history outside active semantics.
    const method=list.length?field('specified',value,{kind:'user_clarification',refs:['method:edit']}):field();
    const next=revise(draft,{method});next.unresolved=unresolved;
    // Keep the dependency through user clarification and sibling reordering.
    // These links are draft provenance, not new cipher parameters.
    for(const rule of Object.values(next.rules))rule.provenance.refs=rule.provenance.refs.flatMap(ref=>{
      const match=ref.match(/^method:operation:(\d+)$/);
      if(!match)return [ref];
      const destination=map[Number(match[1])];
      return Number.isInteger(destination)?['method:operation:'+destination]:[];
    });
    if(old&&(changedIndex!==null||edit.type==='remove')){
      const spans=sourceRanges(old.provenance,draft.source.text);
      for(const key of RULES){
        if(next.rules[key].status==='unspecified')continue;
        const dependent=draft.rules[key].provenance.refs.includes('method:operation:'+edit.index)||sourceRanges(draft.rules[key].provenance,draft.source.text)
          .some(rule=>spans.some(step=>rule.start<step.end&&step.start<rule.end));
        if(dependent){
          const destination=map[edit.index];
          if(Number.isInteger(destination))next.rules[key].provenance.refs=[...new Set([...next.rules[key].provenance.refs,'method:operation:'+destination])];
          if(!next.unresolved.some(c=>c?.kind==='changed_method_rule'&&c.field===key))next.unresolved.push({kind:'changed_method_rule',field:key});
        }
      }
    }
    next.methodEdits=[...(draft.methodEdits||[]),receipt];
    return next;
  }
  function clarify(draft,id,choice,text=''){
    const question=id==='evaluation'?evaluationQuestion(draft):questions(draft).find(q=>q.id===id);
    if(!question||!question.choices.some(c=>c.id===choice))throw Error('Unavailable clarification');
    const provenance={kind:'user_clarification',refs:[id]};
    let next;
    if(id==='evaluation'){
      next=revise(draft,{rules:{evaluation:field('specified',EVALUATION_CHOICES.find(item=>item.id===choice).value,provenance)}});
    }else if(id.startsWith('rule-review:')){
      const key=id.slice('rule-review:'.length);
      if(choice==='replace'&&(typeof text!=='string'||!text.trim()))throw Error('Write the replacement condition.');
      const current=draft.rules[key];
      next=revise(draft,{rules:{[key]:choice==='remove'?field():choice==='replace'?field('specified',text.trim(),provenance):field(current.status,current.value,provenance)}});
    }else if(choice==='other'){
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
      // The explicit choice supplies the active meaning. Keep the old wording
      // as provenance, but do not let sharing promote it back into the label.
      list[slot].label=OPERATIONS[choice];
      next=revise(draft,{method:field('specified',{...((draft.method.status==='specified'&&draft.method.value)||{}),operations:list},provenance)});
      next.unresolved.splice(index,1);
    }else{
      next=revise(draft,{rules:{boundaryMode:field('specified',choice,provenance)}});
    }
    next.clarifications.push({question:id,choice,...(['other','replace'].includes(choice)?{text}:{}),...(id==='evaluation'&&draft.rules.evaluation.status!=='unspecified'?{previousRule:copy(draft.rules.evaluation)}:{}),revision:next.revision});
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
      {label:'Aim',tags:[{id:'aim:'+normalizeOutcome(spec.aim).id,text:outcomeLabel(spec.aim),unknown:spec.aim.status==='unspecified'||(spec.aim.status==='specified'&&normalizeOutcome(spec.aim).id==='unclassified')}]},
      {label:'Method',tags:methodTags.length?methodTags:[{id:'method:unknown',text:display(spec.method,'Method'),unknown:spec.method.status==='unspecified'}]},
      {label:'Scope',tags:scopeTags},
      {label:'Rules',tags:RULES.filter(key=>spec.rules[key].status==='specified'||spec.rules[key].status==='unrestricted'||
        (key==='unmapped'&&has(spec,'reverse_value_digits')&&spec.rules[key].status==='unspecified'))
        .map(key=>({id:'rule:'+key,text:ruleText(key,spec.rules[key]),unknown:spec.rules[key].status==='unspecified'}))},
      ...(spec.unresolved.length?[{label:'Unresolved',details:copy(spec.unresolved)}]:[])
    ];
  }
  function meaning(spec){return {aim:spec.aim,method:spec.method,scope:spec.scope,rules:spec.rules,unresolved:spec.unresolved,methodEdits:spec.methodEdits||[]};}
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
    if(stable(value.aim)!==stable(rebuilt.aim))throw Error('Inconsistent aim category metadata');
    const expected=confirm(rebuilt,value.confirmation);
    if(value.status!==expected.status||value.canonical!==expected.canonical)throw Error('Inconsistent confirmation snapshot');
    return freeze(copy(value));
  }
  function binding(confirmed){const s=validateConfirmed(confirmed);return stable({schema:SCHEMA,revision:s.revision,source:s.source,...meaning(s),confirmation:s.confirmation});}
  function queryForResearch(confirmed,{maxLength=1500}={}){
    const snapshot=validateConfirmed(confirmed);
    if(!Number.isInteger(maxLength)||maxLength<1)throw Error('Invalid query limit');
    if(!completeness(snapshot).researchReady)return {query:null,needsClarification:true,needsShorter:false};
    const compact=f=>f.status==='specified'?{status:f.status,value:f.value,...(f.outcome?{outcomeId:f.outcome.id}:{})}:{status:f.status};
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
    if(!completeness(s).researchReady)return {query:null,needsClarification:true,needsShorter:false};
    const parts=[];
    parts.push(...reviewRows(s).find(r=>r.label==='Method').tags.map(t=>t.text));
    if(s.scope.status==='specified'){
      parts.push(...(s.scope.value.pages||[]).map(p=>p.toUpperCase()));
      for(const [key,value] of Object.entries(s.scope.value))if(key!=='pages')parts.push(key+': '+stable(value));
    }
    parts.push(...reviewRows(s).find(r=>r.label==='Rules').tags.filter(t=>!t.unknown).map(t=>t.text));
    if(s.aim.status==='specified'){
      const aim=normalizeOutcome(s.aim);
      // Generic intent labels are not method-search terms. Keep only specific
      // unmatched authored wording/detail; full intent remains in confirmedQuery.
      if(aim.wording&&normalizeOutcome(aim.wording).id==='unclassified')parts.push(aim.wording);
      if(aim.detail&&aim.detail!==aim.wording&&normalizeOutcome(aim.detail).id==='unclassified')parts.push(aim.detail);
    }
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
  const api={SCHEMA,STATES,RULES,BOUNDARIES,OUTCOMES,EVALUATION_CHOICES,evaluationText,evaluationQuestion,METHOD_FAMILIES,METHODS:METHOD_FAMILIES,normalizeOutcome,normalizeAim,outcomeLabel,classifyMethod,field,pages,createDraft,fromText,revise,clarify,questions,
    completeness,reviewRows,summary,confirm,validateConfirmed,binding,queryForResearch,retrievalQuery,bindResearch,packetSnapshot,applyMethodEdit,serialize:stable};
  if(typeof module!=='undefined')module.exports=api;else root.ClaimSpecification=api;
})(globalThis);
