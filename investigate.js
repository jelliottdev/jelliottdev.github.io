/* Standalone confirmation/research flow. All research comes from the real registry. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'?require('./claim-specification.js'):root.ClaimSpecification;
 const M=typeof module!=='undefined'?require('./assistant-markdown.js'):root.AssistantMarkdown;
 const S=typeof module!=='undefined'?require('./assistant-search.js'):root.AssistantSearch;
 const H=typeof module!=='undefined'?require('./claim-share.js'):root.ClaimShare;
 const R=typeof module!=='undefined'?require('./claim-research.js'):root.ClaimResearch;
 const P=typeof module!=='undefined'?require('./claim-interpretation.js'):root.ClaimInterpretation;
 const D=typeof module!=='undefined'?require('./recorded-comparison.js'):root.RecordedComparison;
 const Reader=typeof module!=='undefined'?require('./record-test-view.js'):root.RecordTestView;
 const Input=typeof module!=='undefined'?require('./idea-input.js'):root.IdeaInput;
 const WordSums=typeof module!=='undefined'?require('./word-sum-intake.js'):root.WordSumIntake;
 const WordAffine=typeof module!=='undefined'?require('./word-affine-intake.js'):root.WordAffineIntake;
 const Cumulative=typeof module!=='undefined'?require('./cumulative-intake.js'):root.CumulativeIntake;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const prov={kind:'supplied',refs:['original wording']};
 const known=v=>C.field('specified',v,prov);
 const editProvenance={kind:'user_clarification',refs:['interpretation editor']};
 const clarified=v=>C.field('specified',v,editProvenance);
 const plainPrimeReversal=/^reverse (?:the )?prime values (?:of|in) (?:(?:each|every) row|rows)$/i;
 function validServiceEndpoint(value,path,pageURL=''){
  if(typeof value!=='string'||!['ask','interpret','proposals','ideas'].includes(path))return false;
  if(new RegExp('^https://[a-z0-9.-]+/'+path+'$').test(value))return true;
  try{const page=new URL(pageURL),url=new URL(value);return ['localhost','127.0.0.1'].includes(page.hostname)&&page.protocol==='http:'&&url.origin===page.origin&&url.pathname==='/'+path&&!url.username&&!url.password&&!url.search&&!url.hash;}catch{return false;}
 }
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
   let value=piece.trim().replace(/[.!?]$/,'');
   value=value.replace(/,?\s+(?:keeping|preserving|keep|preserve) word boundaries$/i,'');
   // Strip only an exact, independently valid trailing positive page clause.
   const on=value.match(/\s+on\s+(LP[12]-[^.!?]+)$/i);
   if(on){try{parseScope(on[1]);value=value.slice(0,on.index);}catch{}}
   if(plainPrimeReversal.test(value))return {ambiguous:true,id:'ambiguous_reversal',label:piece,sourceText:piece};
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
 // Families organize ideas; only a visitor's explicit narrower choice supplies
 // an operation. Question identities include the revision so old forms cannot
 // apply a choice to a different operation after editing or recovery.
 function familyMethodQuestion(draft){
  const ops=draft.method.status==='specified'?draft.method.value.operations:[];
  for(const [index,op] of ops.entries()){
   const id='family-method:'+index+':'+draft.revision;
   if(op.id==='family_selection'&&Object.hasOwn(C.METHOD_FAMILIES,op.familyId)){
    const custom={id:'describe',label:'Describe another exact rule',requiresText:true,fieldLabel:'Describe the exact steps and settings'};
    const choices={
     'fixed-substitution':[{id:'affine',label:'An affine substitution with supplied settings',requiresText:true,fieldLabel:'Enter multiplier a and offset b (0–28)',placeholder:'7, 7'},{id:'affine-all',label:'Try all invertible affine substitutions',example:'Review the GP29 convention and complete search before running.'}],
     polyalphabetic:[{id:'repeating_key',label:'A repeating key with supplied GP indices',requiresText:true,fieldLabel:'Enter the key as GP indices (0–28)',placeholder:'3, 4, 7, 20'},{id:'keys-one',label:'Try all 29 one-rune repeating keys',example:'Explicit GP index domain 0–28; review its settings before running.'},{id:'keys-two',label:'Try all 841 two-rune repeating keys',example:'Every ordered pair of GP indices 0–28; review before running.'}],
     feedback:[{id:'plaintext_autokey',label:'Plaintext autokey with a supplied seed',requiresText:true,fieldLabel:'Enter the seed as GP indices (0–28)'},{id:'ciphertext_autokey',label:'Ciphertext autokey with a supplied seed',requiresText:true,fieldLabel:'Enter the seed as GP indices (0–28)'}],
     transposition:['word','line','page'].map(unit=>({id:'reverse-'+unit,label:'Reverse rune order within each '+unit,example:unit==='word'?'Keep the words in place.':unit==='line'?'Keep the lines in place.':'Reverse all runes on each page.'})),
     'prime-indices':[{id:'word_prime_sums',label:'Add GP prime values within each word',example:'Choose the prime table and word breaks. This produces totals, not plaintext.'}],
     'number-streams':[{id:'finite_key',label:'Use a supplied finite stream of GP indices',requiresText:true,fieldLabel:'Enter the complete stream as GP indices (0–28)',example:'The supplied stream must cover each selected segment; it does not repeat.'}],
     repetition:[{id:'word_affine_count',label:'Count within-word rune pairs following a formula',example:'Choose a distance and y = a·x + b modulo 29; compare with the rearrangement average.'}],
     'book-codes':[]
    }[op.familyId];
    return {id,prompt:'Which specific method do you mean?',context:C.METHOD_FAMILIES[op.familyId]+'. '+(op.familyId==='book-codes'?'Book and coordinate lookups need an exact source and lookup rule. The browser does not yet run a general book cipher.':'A family alone does not define a test. Choose an exact method or keep your own rule; other methods may need an adapter.'),choices:[...choices,custom]};
   }
   if(!Object.hasOwn(C.METHOD_FAMILIES,op.declaredFamilyId))continue;
   const setting=(name,prompt,choices,context)=>({id:'family-setting:'+index+':'+draft.revision+':'+name,prompt,choices,...(context?{context}:{})});
   if(['repeating_key','plaintext_autokey','ciphertext_autokey','finite_key'].includes(op.id)){
    if(!Object.hasOwn(op,'direction'))return setting('direction','How should the key indices be combined with the text?',[{id:'subtract',label:'Subtract key indices'},{id:'add',label:'Add key indices'}]);
    if(!Object.hasOwn(op,'reset'))return setting('reset','When should the key restart?',['page','line','word'].map(value=>({id:value,label:'Restart at each '+value})),draft.rules.reset.status==='specified'?'Your separately supplied reset condition is kept. These settings must agree before this can run.':undefined);
   }
   if(['word_prime_sums','word_affine_count'].includes(op.id)){
    if(op.id==='word_prime_sums'&&!Object.hasOwn(op,'table'))return setting('table','Which prime assignments should be added?',[{id:'canonical',label:'Usual GP prime table',example:'F = 2, U = 3, …, EA = 109'},{id:'reversed',label:'Reversed GP prime table',example:'F = 109, U = 107, …, EA = 2'}]);
    for(const [name,label,max] of op.id==='word_affine_count'?[['lag','Distance between runes',12],['a','Multiplier a',28],['b','Offset b',28]]:[]){if(!Object.hasOwn(op,name))return setting(name,label+'?', [{id:'supply',label:'Use my supplied value',requiresText:true,fieldLabel:label+' ('+(name==='lag'?1:0)+'–'+max+')'}]);}
    if(!Object.hasOwn(op,'boundaries'))return setting('boundaries','Where should each word end?',[{id:'non-rune',label:'Every non-rune character ends a word',example:'Spaces and line breaks also end words.'},{id:'hyphen-period',label:'Only hyphens and periods end words',example:'Spaces and line breaks join the runes on either side.'}]);
    const criterion={kind:op.id==='word_prime_sums'?'word-prime-sums':'word-affine-count',...Object.fromEntries((op.id==='word_prime_sums'?['table','boundaries']:['lag','a','b','boundaries']).map(key=>[key,op[key]]))};
    if(draft.rules.evaluation.status!=='specified'||C.serialize(draft.rules.evaluation.value)!==C.serialize(criterion))return {...setting('evaluation','What should this measurement establish?',[{id:'measurement',label:op.id==='word_prime_sums'?'List each word and its numerical total':'Count matching pairs and compare with the rearrangement average'},{id:'describe',label:'Keep a different intended check',requiresText:true,fieldLabel:'Describe the rule and intended check together'}],op.id==='word_prime_sums'?'This lists totals. It does not test readable text or statistical significance. Your original aim is kept.':'This is an exact count and rearrangement average, not a deciphering verdict or a tail probability. Your original aim is kept.'),criterion};
   }
  }
  return null;
 }
 function answerFamilyMethod(draft,id,choice,text){
  const question=familyMethodQuestion(draft),option=question?.choices.find(item=>item.id===choice);
  if(!question||question.id!==id||!option)throw Error('This method question changed. Review the current choices.');
  if(option.requiresText&&(typeof text!=='string'||!text.trim()))throw Error(option.fieldLabel+'.');
  const index=Number(id.split(':')[1]),prior=draft.method.value.operations[index],family=prior.familyId||prior.declaredFamilyId;
  let op={...prior};
  const integers=(value,maxCount=256)=>{let raw=value.trim();if(raw.startsWith('[')&&raw.endsWith(']'))raw=raw.slice(1,-1);if(!/^\d+(?:\s*,\s*\d+)*$/.test(raw))throw Error('Use comma-separated whole GP indices from 0 to 28.');const values=raw.split(',').map(Number);if(!values.length||values.length>maxCount||values.some(n=>!Number.isSafeInteger(n)||n>28))throw Error('Use whole GP indices from 0 to 28 within the supported key length.');return values;};
  if(id.startsWith('family-method:')){
   if(choice==='describe')op={id:'described_method',label:text.trim(),sourceText:text.trim()};
   else if(choice==='affine'){const values=integers(text,2);if(values.length!==2)throw Error('Supply exactly two indices: multiplier a, offset b.');op={id:'affine',label:'Affine substitution',a:values[0],b:values[1]};}
   else if(choice==='affine-all')op={id:'described_method',label:'Try all invertible affine substitutions'};
   else if(choice.startsWith('keys-'))op={id:'described_method',label:'Try all '+(choice==='keys-one'?'one':'two')+'-rune repeating keys using GP indices 0-28'};
   else if(choice.startsWith('reverse-')){const unit=choice.slice(8);op={id:'reverse_runes',label:'Reverse rune order within each '+unit,unit};}
   else if(['word_prime_sums','word_affine_count'].includes(choice))op={id:choice,label:choice==='word_prime_sums'?'Word prime sums':'Within-word affine pair count'};
   else op={id:choice,label:{repeating_key:'Repeating key',plaintext_autokey:'Plaintext autokey',ciphertext_autokey:'Ciphertext autokey',finite_key:'Finite key stream'}[choice],key:integers(text,choice==='finite_key'?20000:256)};
   // Imported family entries can carry additional supplied parameters. Keep
   // those active; an unsupported condition must refuse compilation, not vanish.
   const retained=Object.fromEntries(Object.entries(prior).filter(([key])=>!['id','familyId','label','sourceText','provenance','editHistory','declaredFamilyId'].includes(key)));
   op={...retained,...op,declaredFamilyId:family};
   // An already supplied global reset is an explicit setting, not a default.
   // Unknown conditions remain separate and are never coerced into a reset.
   if(['repeating_key','plaintext_autokey','ciphertext_autokey','finite_key'].includes(op.id)&&!Object.hasOwn(op,'reset')&&draft.rules.reset.status==='specified'){
    const supplied=draft.rules.reset.value,reset=typeof supplied==='string'?(supplied.match(/^reset at each (page|line|word)$/i)?.[1].toLowerCase()||supplied):null;
    if(['page','line','word'].includes(reset))op.reset=reset;
   }
  }else{
   const parameter=id.split(':')[3];
   if(parameter==='evaluation'&&choice==='measurement'){
    const next=C.revise(draft,{rules:{evaluation:clarified(question.criterion)}});next.clarifications.push({question:id,choice,revision:next.revision});return next;
   }
   if(parameter==='evaluation')op={id:'described_method',label:text.trim(),sourceText:text.trim(),declaredFamilyId:family};
   else if(['lag','a','b'].includes(parameter)){if(!/^\d+$/.test(text.trim()))throw Error('Supply one whole number.');const value=Number(text.trim()),min=parameter==='lag'?1:0,max=parameter==='lag'?12:28;if(!Number.isSafeInteger(value)||value<min||value>max)throw Error('Choose a whole number from '+min+' to '+max+'.');op[parameter]=value;}
   else op[parameter]=choice;
  }
  const next=C.applyMethodEdit(draft,{type:'replace',index,operation:op});next.clarifications.push({question:id,choice,...(option.requiresText?{text:text.trim()}:{}),revision:next.revision});return next;
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
  const familyQuestion=familyMethodQuestion(draft);if(familyQuestion)result.push(familyQuestion);
  if(draft.scope.status==='unspecified'&&!acknowledged('scope'))result.push({id:'scope',prompt:'Which material should this apply to?',choices:[
   {id:'unsolved-lp2',label:'The unsolved LP2 pages',example:'LP2-00–55'},
   {id:'specific',label:'Specific pages or a passage',requiresText:true,fieldLabel:'Name the pages or passage',placeholder:'LP2-15, LP2-17; or LP2-43, lines 2–3'},
   {id:'undecided',label:'Leave the scope undecided'}]});
  const wordQuestion=WordSums?.question(draft);if(wordQuestion)result.push(wordQuestion);
  const pairQuestion=WordAffine?.question(draft);if(pairQuestion)result.push(pairQuestion);
  const cumulativeQuestion=Cumulative?.question(draft);if(cumulativeQuestion)result.push(cumulativeQuestion);
  // Comparing prior work does not require the visitor to design a runnable
  // experiment. A deferral is local to this exact revision; it never supplies
  // a criterion or authorizes execution, and editing asks the question again.
  const deferred=draft.clarifications.some(item=>item.question==='evaluation'&&item.choice==='research-first'&&item.revision===draft.revision);
  const evaluation=C.evaluationQuestion(draft);if(evaluation&&!deferred)result.push({...evaluation,context:'Choose a check if you have one in mind, or find related research first.',choices:[{id:'research-first',label:'Find related research first',example:'Leave this undecided. No experiment will run.'},...evaluation.choices]});
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
  if(id==='evaluation'&&choice==='research-first'){
   if(!intakeQuestions(draft).some(question=>question.id===id&&question.choices.some(option=>option.id===choice)))throw Error('Choose an available answer.');
   const next=C.revise(draft,{});
   next.clarifications.push({question:id,choice,revision:next.revision});
   return next;
  }
  if(/^cumulative-(?:reset|initial|representation|confirm|interpretation):/.test(id))return Cumulative.clarify(draft,id,choice);
  if(/^word-affine-(?:boundaries|evaluation):/.test(id))return WordAffine.clarify(draft,id,choice);
  if(/^family-(?:method|setting):/.test(id))return answerFamilyMethod(draft,id,choice,text);
  if(WordSums?.question(draft)?.id===id)return WordSums.clarify(draft,choice);
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
 function validateAnswer(data,knownDocuments,confirmed){
  if(!data||typeof data.answer!=='string'||!data.answer.trim()||data.answer.length>12000||!Array.isArray(data.sources)||!data.sources.length||data.sources.length>4)throw Error('A sourced comparison is unavailable. You can inspect the related records below.');
  const seen=new Set();
  for(const source of data.sources){
   if(!source||seen.has(source.id)||!knownDocuments.some(d=>d.id===source.id&&d.href===source.href)||!M.safe(source.href))throw Error('The comparison returned an unrecognized source.');
   const current=knownDocuments.find(d=>d.id===source.id&&d.href===source.href);
   if(source.text!==current.text)throw Error('The source record changed while this comparison was prepared. Reload the research and try again.');
   if(data.kind==='recorded-overlap'&&C.serialize(source.recordedComparison)!==C.serialize(current.recordedComparison))throw Error('The recorded execution metadata changed while this comparison was prepared. Reload the research and try again.');
   if(data.kind==='recorded-overlap'&&C.serialize(source.discovery)!==C.serialize(current.discovery))throw Error('The recorded method metadata changed while this comparison was prepared. Reload the research and try again.');
   seen.add(source.id);
  }
  const citations=M.citationNumbers(data.answer,data.sources.length);
  if(!citations.length||citations.some(n=>n<1||n>data.sources.length))throw Error('The comparison could not be checked against its sources.');
  const sources=data.sources.map(s=>knownDocuments.find(d=>d.id===s.id&&d.href===s.href));
  if(data.kind!==undefined&&data.kind!=='recorded-overlap')throw Error('The comparison returned an unrecognized answer type.');
  if(data.kind==='recorded-overlap'){
   const checked=confirmed&&D.compare({snapshot:R.prepare(confirmed).snapshot,documents:sources});
   if(!checked||checked.answer!==data.answer||JSON.stringify(checked.sources.map(s=>s.id))!==JSON.stringify(sources.map(s=>s.id)))throw Error('The recorded comparison does not match the confirmed idea and sources.');
  }
  return {answer:data.answer,sources,cached:Boolean(data.cached),...(data.kind?{kind:data.kind}:{})};
 }
 function operationDetails(operation){
  if(!operation)return '';
  if(H.operationParameters){const rows=H.operationParameters(operation);return rows.length?'<dl class="method-parameters">'+rows.map(row=>'<div><dt>'+esc(row.label)+'</dt><dd>'+esc(row.value)+'</dd></div>').join('')+'</dl>':'';}
  const entries=Object.entries(operation).filter(([key])=>!['id','label','sourceText','provenance','editHistory','declaredFamilyId'].includes(key)&&!(key==='familyId'&&operation.id==='family_selection'));
  if(!entries.length)return '';
  const label=key=>key.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/_/g,' ').replace(/^./,c=>c.toUpperCase());
  const numeric=operation.id==='word_prime_sums'?H.wordPrimeSumLabels(operation.table,operation.boundaries):null;
  return '<dl class="method-parameters">'+entries.map(([key,value])=>'<div><dt>'+esc(key==='boundaries'&&numeric?'Word breaks':label(key))+'</dt><dd>'+esc(numeric&&['table','boundaries'].includes(key)?numeric[key]:typeof value==='string'?value:JSON.stringify(value))+'</dd></div>').join('')+'</dl>';
 }
 function rowsHTML(spec){return '<dl>'+C.reviewRows(spec).filter(r=>r.label!=='Unresolved'&&(r.tags||[]).length).map(r=>{
  const originalTags=r.label==='Scope'&&spec.scope.status==='specified'?r.tags.map(t=>t.id==='scope:description'?{...t,text:spec.scope.value.description}:t):r.tags;
  const tags=r.label==='Scope'&&spec.scope.status==='specified'&&spec.scope.value.pages?[...compactPages(spec.scope.value.pages),...originalTags.filter(t=>!/^lp[12]-\d{2}$/.test(t.id))]:originalTags;
  const label=r.label==='Aim'?'Outcome':r.label==='Rules'?'Bounds & rules':r.label;
  let content;
  if(r.label==='Method')content=tags.length>1?'<ol class="method-steps">'+tags.map((t,i)=>'<li>'+esc(t.text)+operationDetails(spec.method.value?.operations[i])+'</li>').join('')+'</ol>':'<div class="method-wording"><p>'+esc(tags[0].text)+'</p>'+operationDetails(spec.method.value?.operations[0])+'</div>';
  else content=tags.map(t=>{const key=t.id.startsWith('rule:')?t.id.slice(5):null,f=key?spec.rules[key]:null,v=key==='evaluation'&&f?.status==='specified'?f.value:null,numeric=v?.kind==='word-prime-sums'&&Object.keys(v).length===3?H.wordPrimeSumLabels(v.table,v.boundaries):null,plain=f?.status==='specified'?(H.protocolRuleLabel||H.wordPrimeSumRuleLabel)(spec,key,f.value):null;return '<span class="tag'+(t.unknown?' unknown':'')+'">'+esc(numeric?'Evaluation: '+numeric.evaluation:key==='evaluation'&&f?.status==='specified'&&(H.evaluationText||C.evaluationText)(f.value)?'Evaluation: '+(H.evaluationText||C.evaluationText)(f.value):plain||t.text)+'</span>';}).join('');
  if(r.label==='Aim'&&spec.aim.status==='specified'){
   const outcome=C.normalizeOutcome(spec.aim.value),detail=outcome.detail||outcome.wording;
   if(outcome.id==='unclassified')content='<span class="tag unknown">Outcome not classified</span>';
   const labelText=value=>value.toLowerCase().replace(/[\p{P}\s]+/gu,'');
   if(detail&&(outcome.id==='unclassified'||labelText(detail)!==labelText(outcome.label)))content+='<p class="objective-detail">'+esc(detail)+'</p>';
  }
  if(r.label==='Aim'&&spec.aim.status!=='specified')content='<span class="tag unknown">Outcome undecided</span>';
  if(r.label==='Method'){const families=C.classifyMethod(spec.method).familyIds;if(tags.length===1&&families.some(id=>C.METHOD_FAMILIES[id]===tags[0].text))content='';content=families.map(id=>'<span class="tag">'+esc(C.METHOD_FAMILIES[id])+'</span>').join('')+content;}
  return '<div class="tag-row"><dt>'+esc(label)+'</dt><dd>'+content+'</dd></div>';
 }).join('')+(spec.unresolved.length?'<div class="tag-row"><dt>Other details</dt><dd class="unresolved-details">'+spec.unresolved.map(item=>{const value={...item};delete value.provenance;const noteKeys=value.kind==='custom_interpretation'?['kind','question','text']:value.kind==='source_note'?['kind','text']:null;const readable=typeof value.text==='string'&&(Object.keys(value).length===1||noteKeys&&Object.keys(value).every(key=>noteKeys.includes(key))); return '<p>'+esc(readable?value.text:JSON.stringify(value))+'</p>';}).join('')+'</dd></div>':'')+'</dl>';}
 function methodText(spec){return C.reviewRows(spec).find(r=>r.label==='Method').tags.map(t=>t.text).join('; then ');}
 const nativeLinks=html=>html.replace(/<a /g,'<a target="_blank" rel="noopener" ').replace(/title="([^"]*)"/g,'title="$1 (opens in a new tab)"').replace(/href="#\//g,'href="index.html#/');
 // Editorial status belongs to the record workflow; preserve substantive uncertainty.
 function readerLimit(record){return String(record.reader_limit||record.limitations||'').replace(/\s*(?:Computational review\s*;\s*)?Human review(?: is)? pending\.?\s*$/i,'').replace(/[;\s]+$/,'').trim();}
 function observedFindingsHTML(docs,records=[]){
  const findings=docs.flatMap((doc,index)=>{
   if(doc.kind!=='experiment'||typeof doc.text!=='string')return [];
   try{
    const evidence=JSON.parse(doc.text);if(!evidence||typeof evidence!=='object'||Array.isArray(evidence))return [];
    const text=(primary,fallback)=>typeof primary==='string'&&primary.trim()?primary:typeof fallback==='string'?fallback:'';
    const record={finding:text(evidence.reader_finding,evidence.finding),limitations:text(evidence.reader_limit,evidence.limitations)};
    const authored=records.find(item=>item.id===doc.id);
    return record.finding.trim()?[{doc,index,record,authored}]:[];
   }catch{return [];}
  });
  if(!findings.length)return '';
  return '<h2>What the records found</h2>'+findings.map(({doc,index,record,authored})=>'<section class="source"><h3><a target="_blank" rel="noopener" title="Open source in a new tab" href="index.html'+esc(doc.href)+'">['+(index+1)+'] '+esc(Reader?.title(authored)||doc.title)+'</a></h3>'+(authored?Reader?.renderIntro(authored)||'':'')+'<p>'+esc(record.reader_finding||record.finding)+'</p>'+(readerLimit(record)?'<p class="source-limit"><strong>Limit:</strong> '+esc(readerLimit(record))+'</p>':'')+'</section>').join('');
 }
 function numericLeadDifference(record,discovery){
  const target=discovery?.steps?.length===1?discovery.steps[0].operation:null,ops=record.discovery?.operations;
  const valid=op=>op&&typeof op==='object'&&!Array.isArray(op)&&Object.keys(op).length===4&&['action','operand','within','table'].every(k=>Object.hasOwn(op,k))&&op.action==='sum'&&op.operand==='prime-values'&&['word','row','window'].includes(op.within)&&['canonical','reversed'].includes(op.table);
  if(!valid(target)||!Array.isArray(ops)||ops.length!==1||!valid(ops[0]))return '';
  const actual=ops[0],notes=[];
  if(actual.table!==target.table)notes.push(actual.table==='canonical'?'Uses the usual prime values; your idea reverses them.':'Uses reversed prime values; your idea uses the usual table.');
  if(actual.within!==target.within){const names={word:'words',row:'rows',window:'fixed-length rune groups'};notes.push('It sums '+names[actual.within]+' rather than '+names[target.within]+'.');}
  return notes.join(' ');
 }
 function sourceHTML(doc,records,{packet=false,preview=false,discovery=null}={}){
  const record=records.find(r=>r.id===doc.id);
  const heading='<section class="source"><h3><a target="_blank" rel="noopener" title="Open source in a new tab" href="index.html'+esc(doc.href)+'">'+esc(Reader?.title(record)||doc.title)+'</a></h3>'+(record?Reader?.renderIntro(record)||'':'');
  if(!record)return heading+'<p>Supporting manuscript context, not evidence that the idea was tested.</p></section>';
  const scope=record.scope||{},limit=readerLimit(record),finding=record.reader_finding||record.finding;
  const pages=Array.isArray(scope.pages)&&scope.pages.length?compactPages(scope.pages).map(p=>p.text).join(', '):'Not specified in this record';
  const facts=[['Page scope',pages],['Method',scope.procedure],['Input',scope.representation],['Bounds',scope.parameters],['Not tested',scope.exclusions]];
  if(record.materials)facts.push(['Saved results',[record.materials.summary,record.materials.reuse,record.materials.limits].join(' ')]);
  if(packet)facts.push(['Run',record.reproduction?.command],['Inputs',(record.reproduction?.inputs||[]).map(f=>f.path).join(', ')]);
  const difference=preview?numericLeadDifference(record,discovery):'';
  return heading+(difference?'<p class="source-difference">'+esc(difference)+'</p>':'')+(preview&&finding?'<p>'+esc(finding)+'</p>':'')+
   (preview?'':'<dl class="source-facts">'+facts.filter(([,value])=>value).map(([label,value])=>'<div><dt>'+label+'</dt><dd>'+esc(value)+'</dd></div>').join('')+'</dl>')+
   (preview&&limit?'<p class="source-limit"><strong>Limit:</strong> '+esc(limit)+'</p>':'')+'</section>';
 }
 function packetHTML(packet){
  const s=packet.confirmed,r=packet.research,docs=r.evidence.documents||[],noMatch=r.evidence.search?.reason==='no-matching-records',recorded=r.evidence.comparisonKind==='recorded-overlap'&&D.compare({snapshot:R.prepare(s).snapshot,documents:docs})?.answer===r.answer;
  return '<h1>Liberpedia · Research note</h1><p>'+esc(r.at)+'</p>'+rowsHTML(s)+
   observedFindingsHTML(docs,r.evidence.records)+'<h2>'+(noMatch?'Search result':'How this relates to your idea')+'</h2>'+(noMatch||recorded?'':'<p class="small answer-note">AI interpretation of the linked records.</p>')+'<div class="answer">'+nativeLinks(M.render(r.answer,docs))+'</div>'+
   (docs.length?'<h2>Sources &amp; details</h2>'+docs.map(d=>sourceHTML(d,r.evidence.records,{packet:true})).join(''):'<p>No close record was returned by this search. This is a search result, not a finding that the idea is untried.</p>')+
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
 const INTAKE_KEY='liberpedia-idea-intake-v1',INTAKE_LIMIT=40000;
 const intakeUUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
 function readIntake(serialized,at){
  try{
   if(typeof serialized!=='string'||serialized.length>INTAKE_LIMIT)return null;
   const value=JSON.parse(serialized),age=at-value.at;
   if(!value||Object.keys(value).sort().join(',')!=='at,body,receipt,version'||value.version!==1||!Number.isFinite(value.at)||!Number.isFinite(age)||age<0||age>RECOVERY_AGE)return null;
   const body=value.body;
   if(!body||Array.isArray(body)||Object.keys(body).some(k=>!['requestId','fragment','originalIdea'].includes(k))||!intakeUUID.test(body.requestId)||typeof body.fragment!=='string')return null;
   if(Object.hasOwn(body,'originalIdea')&&(typeof body.originalIdea!=='string'||body.originalIdea.length>8000))return null;
   const imported=H.decode(body.fragment);
   if(imported.draft.method.status!=='specified'||!imported.draft.method.value.operations.length)return null;
   if(H.encode(C.confirm(imported.draft,{id:'intake-validation',at:'2000-01-01T00:00:00.000Z'}))!==body.fragment)return null;
   if(new TextEncoder().encode(JSON.stringify(body)).length>32000)return null;
   const receipt=value.receipt;
   if(receipt!==null&&(!receipt||Object.keys(receipt).sort().join(',')!=='id,receivedAt,status'||!/^p_[a-f0-9]{64}$/.test(receipt.id)||!['received','already_received'].includes(receipt.status)||typeof receipt.receivedAt!=='string'||!Number.isFinite(Date.parse(receipt.receivedAt))))return null;
   return value;
  }catch{return null;}
 }
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
   if(value.version!==1||value.entry!==entry||!Number.isFinite(age)||age<0||age>RECOVERY_AGE||typeof value.raw!=='string'||value.raw.length>32000||typeof value.editing!=='boolean'||!['input','search','review','interpreting','research'].includes(value.stage))return null;
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
   return {raw:value.raw,stage:draft?'review':value.stage==='search'?'search':'input',draft,editing:!!baseline,baseline,overlay:overlay||{}};
  }catch{return null;}
 }
 function createApp(doc,{fetcher=root.fetch.bind(root),now=()=>new Date().toISOString(),id=()=>root.crypto.randomUUID(),printer=()=>root.print(),schedule=setTimeout,unschedule=clearTimeout,sharer=H.share,renderCard=H.renderPNG}={}){
  const host=doc.getElementById('investigate'),printHost=doc.getElementById('print-snapshot');
  let stage='input',draft=null,confirmed=null,result=null,packet=null,editing=false,editingBackup=null,raw='',records=[],documents=[],endpoint=null,loaded=false,loadError='',message='',error='',busy=false,controller=null,generation=0,registryId='';
  const incoming=new URLSearchParams(doc.defaultView?.location?.search||'');
  const entry=Input.read(doc.defaultView?.location);raw=entry.text;error=entry.error;
  let legacyScope=null;
  let shareBusy=false,shareNotice='',shareFallback=null,preparedCard=null,preparedFor=null;
  let intakeEndpoint=null,ideaEndpoint=null,intake=null,intakeController=null,intakeVersion=0;
  let renderedResearchCard=null;
  let searchedText='',relatedAnswer=null;
  let cardContract=false;
  let interpretationEndpoint=null,interpretController=null,interpretVersion=0,interpreting=false,interpretError='',guidedRecovery=null;
  let configResolved=false,configValid=false,configReady=null,configAttempt=null,loadVersion=0,destroyed=false;
  const fragment=doc.defaultView?.location?.hash||'';
  const recoveryEntry=JSON.stringify({search:doc.defaultView?.location?.search||'',fragment});
  let session=null;try{session=doc.defaultView?.sessionStorage;}catch{}
  let savedIntake=null;try{savedIntake=readIntake(session?.getItem(INTAKE_KEY),Date.parse(now()));}catch{}
  function persistIntake(current){
   savedIntake={version:1,at:current.at,body:current.body,receipt:current.receipt||null};
   try{const serialized=JSON.stringify(savedIntake);if(serialized.length<=INTAKE_LIMIT)session?.setItem(INTAKE_KEY,serialized);}catch{}
  }
  let restoringOverlay=null;
  if(fragment.startsWith('#idea=')){
   try{const shared=H.decode(fragment);draft=shared.draft;raw=draft.source.text;stage='review';message='Shared idea. Review the wording before checking prior research.';}
   catch{error='This shared idea link could not be read. Ask for a new link or enter the idea below.';}
  }
  const pageHint=incoming.getAll('pages').join(',');
  if(pageHint){try{legacyScope=parseScope(pageHint,{kind:'supplied',refs:['URL page hint']});}catch{message='The linked page selection could not be read. You can enter exact pages when reviewing the idea.';}}
  let recovered=null;try{recovered=readRecovery(session?.getItem(RECOVERY_KEY),recoveryEntry,Date.parse(now()));}catch{}
  if(recovered){
   ({raw,stage,draft,editing}=recovered);if(stage==='search')searchedText=raw;restoringOverlay=recovered.overlay;if(stage==='review')legacyScope=null;
   if(editing)editingBackup={stage:'review',draft:recovered.baseline,confirmed:null,result:null,packet:null,message:'',error:''};
   message=stage==='search'?'Search restored.':'Draft restored.';
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
  function stopInterpretation(){guidedRecovery=null;interpretVersion++;interpretController?.abort();interpretController=null;interpreting=false;}
  function stopIntake(clear=false){intakeVersion++;intakeController?.abort();intakeController=null;if(intake)intake.busy=false;if(clear)intake=null;}
  function render(){
   if(stage==='review'&&!editing&&draft)draft=Cumulative?.complete(draft)||draft;
   const prior=doc.activeElement?.id;
   const sameResearch=stage==='research'&&confirmed&&renderedResearchCard===confirmed;
   const disclosures=sameResearch?captureDisclosureState(host,doc.activeElement):[];
   const selection=(sameResearch||stage==='input'||stage==='search')&&prior&&Number.isInteger(doc.activeElement.selectionStart)&&Number.isInteger(doc.activeElement.selectionEnd)?{value:doc.activeElement.value,start:doc.activeElement.selectionStart,end:doc.activeElement.selectionEnd}:null;
   const pending=stage==='review'&&!editing?intakeQuestions(draft)[0]:null;
   if(stage==='input'||stage==='search'){
    host.innerHTML='<h1>Have we tried it?</h1><p>Ask a question or paste an idea to find related research. You don’t need a finished method or a page selection.</p><form id="intake"><label class="sr-only" for="idea">Your idea</label><textarea id="idea" required maxlength="8000" rows="6" aria-describedby="interpretation-status interpretation-error" placeholder="For example: reverse the prime values of each row on LP2-15">'+esc(raw)+'</textarea><p id="interpretation-status" class="small" role="status"></p><p id="interpretation-error" class="error" role="alert"></p><button id="guided-clarification" type="button" hidden>Answer a few questions</button><div class="actions"><a class="left" href="research.html#mode=list">Search existing research</a><button id="interpret-submit" class="primary" type="submit">Check idea</button></div></form><div id="related-research">'+roughResearchHTML()+'</div><div class="actions"><button id="define-test" type="button">Define a test</button></div><p class="small">Optional: turn your idea into an exact check you can review before running.</p>';
   }else{
    host.innerHTML='<button class="back" id="back" type="button">'+(pending?'Edit idea':'Back to idea')+'</button><h1 id="review-title"'+(pending?' class="question-title"':'')+' tabindex="-1">'+esc(pending?pending.prompt:stage==='research'?'Research comparison':'Is this the idea?')+'</h1>'+(pending?'<p class="idea-wording"><strong>Method:</strong> '+esc((C.reviewRows(draft).find(row=>row.label==='Method')?.tags||[]).map(tag=>tag.text).join(' → ').replace(/\s+/gu,' ').replace(/^(.{240})[\s\S]+$/u,'$1…'))+'</p>':'')+
     (stage==='research'?'<p id="error" class="notice error" role="alert">'+esc(error||loadError)+'</p>':'')+
     (pending?'':(stage==='research'?'<section class="confirmed-card"><button id="share-idea" class="share-icon" type="button" aria-label="Share confirmed idea" title="Share idea"'+(shareBusy?' disabled':'')+'><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V3m-4 4 4-4 4 4M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8"/></svg></button><details class="confirmed"><summary>Your idea</summary>':'<section aria-label="Interpreted idea">')+rowsHTML(confirmed||draft)+
     '<div class="actions"><button class="left" id="edit" type="button">Edit interpretation</button></div>'+(stage==='research'?'</details>'+intakeHTML()+'<p id="share-status" class="small" role="status">'+esc(shareNotice)+'</p><div id="share-fallback"></div></section>':'</section>')+
     '')+(editing?editorHTML():questionsHTML())+
     (stage==='review'?'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'')+
     (stage==='review'&&!editing&&!intakeQuestions(draft).length&&draft.method.status!=='specified'?'<p>Choose a method before comparing it with prior tests. <a href="research.html#mode=list">Browse research</a> for approaches.</p>':'')+
     (stage==='review'&&!editing&&!intakeQuestions(draft).length&&draft.method.status==='specified'?'<p id="collection-notice" class="small"'+(intakeEndpoint?'':' hidden')+'>'+(ideaEndpoint?'Your confirmed card becomes a shared research entry.':intakeEndpoint?'Confirmed ideas are saved for research review.':'')+'</p>'+'<div class="actions"><button class="primary" id="confirm" '+(!loaded?'disabled':'')+' type="button">Confirm and find research</button></div>':'')+
     (stage==='research'?researchHTML()+'<details><summary>Original idea</summary><pre>'+esc(draft.source.text)+'</pre></details>':'');
   }
   host.insertAdjacentHTML('beforeend','<p id="status" class="notice small" role="status">'+esc(message||(!loaded&&!loadError?'Loading research records…':''))+'</p>'+(stage==='research'?'':'<p id="error" class="notice error" role="alert">'+esc(error||loadError)+'</p>')+(!loaded&&loadError?'<button id="reload" type="button">Retry loading research</button>':'')+'<p class="small privacy">'+(endpoint?'Research questions are processed by Cloudflare. Don’t include private information.':'')+'</p>');
   bind();
   if(stage==='input'||stage==='search')updateInterpretationInput();
   if(restoringOverlay){restoreFields(restoringOverlay);restoringOverlay=null;}
   if(sameResearch)restoreDisclosureState(host,disclosures);
   if(prior&&doc.getElementById(prior))doc.getElementById(prior).focus({preventScroll:true});
   if(selection){const field=doc.getElementById(prior);if(field?.value===selection.value&&field.setSelectionRange)field.setSelectionRange(selection.start,selection.end);}
   renderedResearchCard=stage==='research'?confirmed:null;
   saveRecovery();
  }
  function intakeHTML(){
   if(!intakeEndpoint||!intake||intake.snapshot!==confirmed)return '';
   return '<div class="idea-save" id="idea-save"><span id="idea-save-status" class="small" role="status" tabindex="-1">'+intakeStatus()+'</span><button id="retry-save" type="button"'+(intake.error||intake.entryError?'':' hidden')+'>'+(intake.entryError?'Retry creating entry':'Retry saving')+'</button><a class="idea-next-action" id="open-research-entry"'+(intake.entrySaved?' href="run.html#idea='+esc(intake.receipt.id)+'"':' hidden')+'>View idea and experiments</a></div>';
  }
  function intakeStatus(){return intake.busy?(intake.saved&&ideaEndpoint?'Creating research entry…':'Saving idea…'):intake.entrySaved?'Research entry saved.':intake.entryError?'Idea saved. The research entry could not be created.':intake.saved?'Saved.':intake.error?"Couldn’t save this idea.":'';}
  function updateIntake(){
   const status=doc.getElementById('idea-save-status'),retry=doc.getElementById('retry-save');if(!status||!retry||intake?.snapshot!==confirmed)return false;
   status.textContent=intakeStatus();const held=doc.activeElement===retry;retry.hidden=!intake.error&&!intake.entryError;retry.textContent=intake.entryError?'Retry creating entry':'Retry saving';if(held&&retry.hidden)status.focus({preventScroll:true});
   const link=doc.getElementById('open-research-entry');if(link){link.hidden=!intake.entrySaved;if(intake.entrySaved)link.href='run.html#idea='+intake.receipt.id;}return true;
  }
  async function saveIntake(snapshot=confirmed){
   if(!intakeEndpoint||!snapshot||snapshot!==confirmed)return;
   if(!intake||intake.snapshot!==snapshot){
    stopIntake(true);
    intake={snapshot,requestId:id(),busy:false,saved:false,error:false};
    try{
     const identity={fragment:H.encode(snapshot),...(snapshot.source.origin==='shared_link'?{}:{originalIdea:snapshot.source.text})};
     const prior=readIntake(JSON.stringify(savedIntake),Date.parse(now()));
     const matches=prior&&prior.body.fragment===identity.fragment&&Object.hasOwn(prior.body,'originalIdea')===Object.hasOwn(identity,'originalIdea')&&prior.body.originalIdea===identity.originalIdea;
     intake.body=matches?prior.body:{requestId:intake.requestId,...identity};
     intake.requestId=intake.body.requestId;intake.at=matches?prior.at:Date.parse(now());
     // A local receipt is only a hint. Reconfirm using the same UUID so a
     // corrupt/misbound stored receipt cannot suppress the server check.
     intake.receipt=matches?prior.receipt:null;intake.saved=false;
     persistIntake(intake);
    }
    catch{intake.error=true;render();return;}
   }
   const current=intake;if(current.busy||current.saved&&(!ideaEndpoint||current.entrySaved)||!current.body)return;
   const token=++intakeVersion,requestController=new AbortController();intakeController=requestController;current.busy=true;current.error=false;if(!updateIntake())render();
   const timer=schedule(()=>requestController.abort(),30000);
   try{
    if(!current.saved){
     const response=await fetcher(intakeEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(current.body),signal:requestController.signal});
     const data=await response.json();
     if(requestController.signal.aborted)throw Error('Save interrupted');
     if(token!==intakeVersion||intake!==current||confirmed!==snapshot)return;
     if(!response.ok||!/^p_[a-f0-9]{64}$/.test(data.id)||!['received','already_received'].includes(data.status)||!Number.isFinite(Date.parse(data.receivedAt)))throw Error('Save unavailable');
     current.receipt={id:data.id,status:data.status,receivedAt:data.receivedAt};current.saved=true;persistIntake(current);
    }
    if(ideaEndpoint){
     current.entryError=false;updateIntake();
     try{
      const response=await fetcher(ideaEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proposalId:current.receipt.id}),signal:requestController.signal}),entry=await response.json();
      if(requestController.signal.aborted)throw Error('Save interrupted');
      if(token!==intakeVersion||intake!==current||confirmed!==snapshot)return;
      if(!response.ok||entry.id!==current.receipt.id||C.serialize(entry.card)!==C.serialize(H.cardData(snapshot)))throw Error('Entry mismatch');
      current.entrySaved=true;
     }catch{if(token===intakeVersion&&intake===current&&confirmed===snapshot)current.entryError=true;}
    }
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
    const base='https://jelliottdev.github.io/investigate.html?v=complete-current-20261024';
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
   return '<form id="clarification" class="question'+(q.id==='evaluation'?' evaluation-question':'')+'"><fieldset><legend class="sr-only">'+esc(q.prompt)+'</legend>'+(q.context?'<p class="condition-context">'+esc(q.context)+'</p>':'')+(q.example?'<p class="example">'+esc(q.example)+'</p>':'')+q.choices.map(c=>'<label><input type="radio" name="choice" value="'+esc(c.id)+'" required><span>'+esc(c.label)+(c.example?'<small class="example">'+esc(c.example)+'</small>':'')+'</span></label>').join('')+'</fieldset><label for="other-detail" id="other-label" hidden>Describe what you mean</label><textarea id="other-detail" hidden></textarea><div class="actions"><button class="primary" type="submit">Continue</button></div></form>';
  }
  function roughSourceHTML(document){
   const record=records.find(r=>r.id===document.id);if(!record)return '';
   const excerpt=(value,max)=>{const text=String(value||'').replace(/\s+/gu,' ').trim();if(text.length<=max)return text;const head=text.slice(0,max),cut=head.lastIndexOf(' ');return head.slice(0,cut>max*.6?cut:max)+'…';};
   const action=excerpt(record.reader_test?.action||record.scope?.procedure,260),finding=excerpt(record.reader_finding||record.finding,420),limit=excerpt(readerLimit(record),190);
   return '<section class="source"><h3><a href="library.html#/experiment/'+esc(record.id)+'">'+esc(Reader?.title(record)||document.title)+'</a></h3>'+
    (action?'<p><strong>What was tried:</strong> '+esc(action)+'</p>':'')+(finding?'<p><strong>Result:</strong> '+esc(finding)+'</p>':'')+
    (limit?'<p class="small source-limit"><strong>Limit:</strong> '+esc(limit)+'</p>':'')+'</section>';
  }
  function roughResearchHTML(){
   if(!searchedText)return '';
   const related=(S.related?S.related(documents,searchedText):S.select(documents,searchedText)).filter(d=>d.kind==='experiment'&&records.some(r=>r.id===d.id));
   return '<section aria-labelledby="related-title"><h2 id="related-title" tabindex="-1">Related research</h2>'+
    (!loaded?'<p role="status">'+esc(loadError?'The research records could not be loaded. Your wording is kept.':'Loading research records…')+'</p>':
    '<p>These records may help with your idea. A related record does not mean the same test has been done.</p>'+
    (relatedAnswer?'<p class="small answer-note">AI summary of the linked research.</p><div class="answer">'+nativeLinks(M.render(relatedAnswer.answer,relatedAnswer.sources))+'</div>':'')+
    (related.length?related.map(roughSourceHTML).join(''):'<p>No close match was found in this collection. That does not tell us whether someone has tried it elsewhere.</p><p><a href="research.html#mode=list">Explore the research map</a></p>'))+'</section>';
  }
  async function searchRelated(){
   stop();const token=generation,text=raw;searchedText=text;relatedAnswer=null;stage='search';draft=null;confirmed=null;render();focus('#related-title');
   // The local records remain useful while optional configuration/AI loads or fails.
   if(!configResolved)await configReady;
   if(destroyed||token!==generation||stage!=='search'||searchedText!==text||raw!==text||!endpoint)return;
   const requestController=new AbortController();controller=requestController;
   const timer=schedule(()=>requestController.abort(),30000);
   try{
    const data=await json(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'related-research',query:text}),signal:requestController.signal});
    if(destroyed||token!==generation||stage!=='search'||searchedText!==text||raw!==text)return;
    if(data.kind!=='related-research'&&data.comparisonKind!=='related-research')return;
    const checked=validateAnswer({...data,kind:undefined},documents,null);
    if(checked.sources.some(d=>d.kind!=='experiment'))return;
    relatedAnswer=checked;render();
   }catch{/* Optional synthesis must never remove local research or demand a formal card. */}
   finally{unschedule(timer);if(token===generation)controller=null;}
  }
  function researchHTML(){
   const controls='<div class="actions">'+(busy?'<button id="cancel" type="button">Stop waiting</button>':(!result?'<button id="retry" type="button">Try comparison again</button>':''))+(packet?'<button id="print" type="button">Print research note</button>':'')+'</div>';
   if(result)return observedFindingsHTML(result.sources,records)+'<h2>'+(result.noMatch?'Search result':'How this relates to your idea')+'</h2>'+(result.noMatch||result.kind==='recorded-overlap'?'':'<p class="small answer-note">AI interpretation of the linked records.</p>')+'<div class="answer">'+nativeLinks(M.render(result.answer,result.sources))+'</div>'+(result.sources.length?'<details class="source-evidence"><summary>Sources &amp; details ('+result.sources.length+')</summary>'+result.sources.map(d=>sourceHTML(d,records)).join('')+'</details>':'<p><a href="research.html#mode=list" target="_blank" rel="noopener">Browse research</a></p>')+controls;
   let q,scope;try{if(cardContract){const prepared=R.prepare(confirmed);q={query:prepared.query};scope=prepared;}else{q=C.retrievalQuery(confirmed);scope=C.queryForResearch(confirmed,{maxLength:6000});}}catch{q={};scope={};}
   const related=q.query?S.select(documents,q.query,scope.pages||[],scope.discovery).filter(d=>d.kind==='experiment'):[];
   return (busy?'<p aria-live="polite">Comparing the confirmed idea with published research…</p>':'')+controls+(related.length?'<h2>Related records</h2>'+related.map(d=>sourceHTML(d,records,{preview:true,discovery:scope.discovery})).join(''):'');
  }
  function bind(){
   doc.getElementById('retry-save')?.addEventListener('click',()=>saveIntake());
   doc.getElementById('share-idea')?.addEventListener('click',shareIdea);
   if(stage==='research')updateShare();
   bindMethodSteps();
   doc.getElementById('method-add')?.addEventListener('click',()=>editMethodStep({type:'add',index:methodOperations().length,operation:{id:'described_method',label:''}},'#'+(methodOperations().length?'edit-method-'+methodOperations().length:'edit-method')));
   doc.getElementById('idea')?.addEventListener('input',event=>{if(interpreting)stopInterpretation();if(stage==='search'){stop();searchedText='';relatedAnswer=null;const related=doc.getElementById('related-research');if(related)related.innerHTML='';}raw=event.target.value;guidedRecovery=null;interpretError='';updateInterpretationInput();saveRecovery();});
   doc.getElementById('idea')?.addEventListener('keydown',event=>{if(event.key==='Escape'&&interpreting){event.preventDefault();stopInterpretation();interpretError='';updateInterpretationInput();}});
   for(const name of Object.keys(recoveryFields()))if(name!=='choice'&&!name.startsWith('edit-method'))for(const type of ['input','change'])doc.getElementById(name)?.addEventListener(type,saveRecovery);
   for(const radio of doc.querySelectorAll?.('input[name=choice]')||[])radio.addEventListener('change',saveRecovery);
   doc.getElementById('guided-clarification')?.addEventListener('click',()=>{
    const recovery=guidedRecovery;
    if(!recovery||interpreting||stage!=='input'||recovery.version!==interpretVersion||recovery.text!==raw||doc.getElementById('idea')?.value!==raw)return;
    const inputError=Input.issue(raw);if(inputError){guidedRecovery=null;interpretError=inputError;updateInterpretationInput();focus('#idea');return;}
    stopInterpretation();interpretError='';acceptDraft(initialDraft(recovery.text));
   });
   doc.getElementById('intake')?.addEventListener('submit',event=>{
    event.preventDefault();if(interpreting)return;raw=doc.getElementById('idea').value;const inputError=!raw.trim()?'Describe an idea first.':raw.length>8000?'Paste up to 8,000 characters to find related research.':'';if(inputError){interpretError=inputError;updateInterpretationInput();focus('#idea');return;}
    stopIntake(true);stop();stopInterpretation();confirmed=null;result=null;packet=null;printHost.replaceChildren();editing=false;error='';message='';
    searchRelated();
   });
   doc.getElementById('define-test')?.addEventListener('click',()=>{
    if(interpreting)return;raw=doc.getElementById('idea').value;const inputError=raw.length>Input.MAX_LENGTH?'To define a test, shorten this to 1,500 characters. Your full text is kept; you can still search it.':Input.issue(raw);if(inputError){interpretError=inputError;updateInterpretationInput();focus('#idea');return;}
    stopIntake(true);stop();stopInterpretation();confirmed=null;result=null;packet=null;printHost.replaceChildren();editing=false;error='';message='';
    stage='input';interpret();
   });
   doc.getElementById('back')?.addEventListener('click',()=>{stopIntake(true);stop();stage='input';editing=false;confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#idea');});
   doc.getElementById('edit')?.addEventListener('click',()=>{stopIntake(true);stop();editingBackup={stage,draft,confirmed,result,packet,message,error};editing=true;stage='review';draft=C.revise(draft,{});confirmed=null;result=null;packet=null;printHost.replaceChildren();message='';error='';render();focus('#edit-method');});
   doc.getElementById('cancel-edit')?.addEventListener('click',()=>{editing=false;if(editingBackup){({stage,draft,confirmed,result,packet,message,error}=editingBackup);editingBackup=null;if(packet)printHost.innerHTML=packetHTML(packet);}render();focus('#edit');});
   doc.getElementById('editor')?.addEventListener('submit',event=>{
    event.preventDefault();try{
     flushMethodSteps();
     const ruleText=doc.getElementById('edit-rules').value.trim();
     const scopeText=doc.getElementById('edit-scope').value.trim();
     const outcomeId=doc.getElementById('edit-aim').value,objectiveInput=doc.getElementById('edit-objective').value;
     const priorOutcome=draft.aim.status==='specified'?C.normalizeOutcome(draft.aim.value):{id:'',wording:'',detail:''};
     const priorObjective=priorOutcome.detail||priorOutcome.wording,objective=objectiveInput===priorObjective?priorObjective:objectiveInput.trim();
     const patch={},scopeChange=scopeEdit(draft.scope,scopeText);
     if(scopeChange!==undefined)patch.scope=scopeChange;
     if(outcomeId!==priorOutcome.id||objective!==priorObjective)patch.aim=outcomeId?clarified({outcomeId:outcomeId==='unclassified'?C.normalizeOutcome(objective).id:outcomeId,wording:outcomeId==='unclassified'?objective:priorOutcome.wording||objective,detail:objective}):objective?clarified({outcomeId:'unclassified',wording:objective,detail:objective}):C.field();
     const removed=C.RULES.filter(key=>doc.getElementById('remove-rule-'+key)?.checked);
     const rulesChange=ruleEdits(draft.rules,ruleText,removed);
     if(rulesChange)patch.rules=rulesChange;
     draft=C.revise(draft,patch);
     editing=false;editingBackup=null;error='';render();focus('#review-title');
    }catch(e){error=e.message;doc.getElementById('error').textContent=error;}
   });
   const renderedQuestion=stage==='review'&&!editing?intakeQuestions(draft)[0]:null;
   doc.getElementById('clarification')?.addEventListener('change',()=>{
    const selected=doc.querySelector('input[name=choice]:checked')?.value,q=intakeQuestions(draft)[0];if(!q||q.id!==renderedQuestion?.id)return;
    const option=q.choices.find(c=>c.id===selected),other=Boolean(option?.requiresText);
    doc.getElementById('other-label').hidden=!other;doc.getElementById('other-label').textContent=option?.fieldLabel||'Describe what you mean';doc.getElementById('other-detail').hidden=!other;doc.getElementById('other-detail').required=other;doc.getElementById('other-detail').placeholder=option?.placeholder||'';
   });
   doc.getElementById('clarification')?.addEventListener('submit',event=>{
    event.preventDefault();const choice=doc.querySelector('input[name=choice]:checked')?.value;if(!choice)return;
    const q=intakeQuestions(draft)[0];if(!q||q.id!==renderedQuestion?.id)return;
    if(['aim','method','scope','evaluation'].includes(q.id)||/^family-(?:method|setting):/.test(q.id)||WordSums?.question(draft)?.id===q.id||WordAffine?.question(draft)?.id===q.id||Cumulative?.question(draft)?.id===q.id){
     try{draft=answerIntake(draft,q.id,choice,doc.getElementById('other-detail').value);message='';}catch(e){error=e.message;doc.getElementById('error').textContent=error;return;}
    }else if(choice==='other'){
     const text=doc.getElementById('other-detail').value.trim();if(!text)return;
     const previous={stage,draft,confirmed,result,packet,message,error};
     const revised=C.clarify(draft,q.id,choice,text);
     editingBackup=previous;draft=revised;editing=true;message='Your explanation is kept. Edit the method wording to make the interpretation explicit.';
    }else{draft=C.clarify(draft,q.id,choice,doc.getElementById('other-detail').value);message='';}
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
     stage='research';error='';message='';prepareCard();saveIntake(confirmed);compare();focus('#review-title');
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
  function updateInterpretationInput(){
   const button=doc.getElementById('interpret-submit'),status=doc.getElementById('interpretation-status'),notice=doc.getElementById('interpretation-error');
   if(button){button.disabled=interpreting;button.textContent='Check idea';}
   const define=doc.getElementById('define-test');if(define){define.disabled=interpreting;define.textContent=interpreting?'Preparing test…':'Define a test';}
   if(status)status.textContent=interpreting?'Preparing the test wording…':'';
   if(notice)notice.textContent=interpretError;
   const guided=doc.getElementById('guided-clarification');if(guided)guided.hidden=!guidedRecovery||interpreting||guidedRecovery.text!==raw||guidedRecovery.version!==interpretVersion;
  }
  async function interpret(){
   stopInterpretation();const token=interpretVersion,text=raw;let returnedInterpretation=false;
   const localDraft=initialDraft(text),localOperations=localDraft.method.status==='specified'?localDraft.method.value.operations:[];
   // The parser accepts an exact positive page clause but keeps conditional or
   // additional steps opaque. Only a whole, single recognized ambiguity skips AI.
   if((localOperations.length===1&&localOperations[0].id==='ambiguous_reversal')||WordSums?.matches(text)||WordAffine?.matches(text)||Cumulative?.matches(text)){acceptDraft(localDraft);return;}
   stage='input';interpreting=true;interpretError='';error='';message='';updateInterpretationInput();
   try{
    if(configResolved&&!configValid)loadConfig().catch(()=>{});
    while(!configResolved){
     await configReady;
     if(token!==interpretVersion||stage!=='input'||!interpreting||text!==raw)return;
    }
    if(token!==interpretVersion||stage!=='input'||!interpreting||text!==raw)return;
    if(!interpretationEndpoint)throw Error('Interpretation unavailable');
    P.validateInput(text);
    const requestController=new AbortController();interpretController=requestController;
    const timer=schedule(()=>requestController.abort(),30000);
    try{
     const response=await fetcher(interpretationEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text}),signal:requestController.signal});
     if(!response.ok){
      let reason;try{reason=(await response.json())?.reason;}catch{}
      const failure=Error('Interpretation request failed');failure.interpretationReason=response.status===429?'rate-limit':reason==='invalid-interpretation'?'invalid':reason==='timeout'?'timeout':'unavailable';throw failure;
     }
     returnedInterpretation=true;
     const data=await response.json();
     const digest=await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
     const expected=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
     if(requestController.signal.aborted)throw Object.assign(Error('Interpretation timed out'),{interpretationReason:'timeout'});
     if(token!==interpretVersion||stage!=='input'||!interpreting||text!==raw)return;
     if(data.sourceBinding!==expected)throw Error('The interpretation did not match your wording. You can continue with the original.');
     const proposed=P.toDraft(text,data.candidate);
     interpreting=false;acceptDraft(proposed.draft);
    }finally{unschedule(timer);}
   }catch(e){
    if(token===interpretVersion&&stage==='input'){
     interpreting=false;const reason=e.name==='AbortError'?'timeout':e.interpretationReason||(returnedInterpretation?'invalid':'unavailable');
     guidedRecovery={text,version:token};
     interpretError=({timeout:'The check timed out. Your text is kept. Try again.', 'rate-limit':'Too many checks. Try again in a minute.', invalid:'The wording couldn’t be interpreted reliably. Try rephrasing it.', unavailable:'The checker is temporarily unavailable. Your text is kept.'})[reason];updateInterpretationInput();
    }
   }finally{if(token===interpretVersion){interpreting=false;interpretController=null;}}
  }
  function availability(){
   const status=doc.getElementById('status'),notice=doc.getElementById('error'),confirm=doc.getElementById('confirm');
   if(status)status.textContent=message||(!loaded&&!loadError?'Loading research records…':'');
   if(notice)notice.textContent=error||loadError;
   if(confirm)confirm.disabled=!loaded;
   const collection=doc.getElementById('collection-notice');if(collection){collection.hidden=!intakeEndpoint;collection.textContent=ideaEndpoint?'Your confirmed card becomes a shared research entry.':intakeEndpoint?'Confirmed ideas are saved for research review.':'';}
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
    endpoint=validServiceEndpoint(config.endpoint,'ask',doc.defaultView?.location?.href||'')?config.endpoint:null;
    cardContract=config.researchContract==='card-v1';
    interpretationEndpoint=validServiceEndpoint(config.interpretationEndpoint,'interpret',doc.defaultView?.location?.href||'')?config.interpretationEndpoint:null;
    intakeEndpoint=validServiceEndpoint(config.proposalEndpoint,'proposals',doc.defaultView?.location?.href||'')?config.proposalEndpoint:null;
    ideaEndpoint=validServiceEndpoint(config.researchIdeaEndpoint,'ideas',doc.defaultView?.location?.href||'')&&intakeEndpoint&&new URL(config.researchIdeaEndpoint).origin===new URL(intakeEndpoint).origin?config.researchIdeaEndpoint:null;
    configValid=true;configResolved=true;availability();
   }).catch(e=>{
    if(!destroyed){endpoint=null;interpretationEndpoint=null;intakeEndpoint=null;ideaEndpoint=null;cardContract=false;configValid=false;configResolved=true;availability();}
    throw e;
   });
   configReady=configAttempt.catch(()=>{});
   return configAttempt;
  }
  async function load(){
   const token=++loadVersion;loadError='';loaded=false;availability();
   const configured=loadConfig();
   try{
    configured.catch(()=>{});
    const registry=await json('data/experiments.json',{signal:AbortSignal.timeout(8000)});
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
   availability();if(stage==='search')render();
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
     const answer='No close match was found in the published research. This does not establish whether the idea has been tried elsewhere.';
     const research=C.bindResearch(snapshot,{id:id(),at:now(),evidence:{snapshotId:registryId,records:[],documents:[],search:{query:compact.query,reason:data.reason}},answer});
     packet=C.packetSnapshot(snapshot,research);result=Object.freeze({answer,sources:[],noMatch:true});printHost.innerHTML=packetHTML(packet);return;
    }
    const checked=validateAnswer(data,documents,snapshot);
    const evidenceRecords=records.filter(r=>checked.sources.some(s=>s.kind==='experiment'&&s.id===r.id));
    if(!evidenceRecords.length)throw Error('No research record supports this comparison.');
    const research=C.bindResearch(snapshot,{id:id(),at:now(),evidence:{snapshotId:registryId,records:evidenceRecords,documents:checked.sources,...(checked.kind?{comparisonKind:checked.kind}:{})},answer:checked.answer});
    packet=C.packetSnapshot(snapshot,research);result=Object.freeze(checked);printHost.innerHTML=packetHTML(packet);
   }catch(e){if(token===generation)error=e.name==='AbortError'?'The comparison timed out. Your confirmed idea is kept; try again.':e.message;}
   finally{unschedule(timer);if(token===generation){busy=false;controller=null;render();}}
  }
  render();const ready=load();
  return {ready,getSnapshot:()=>({stage,draft,confirmed,result,packet,busy,interpreting}),destroy:()=>{destroyed=true;loadVersion++;stopInterpretation();stopIntake(true);stop();}};
 }
 const api={validServiceEndpoint,parseScope,initialDraft,intakeQuestions,answerIntake,compactPages,validateAnswer,rowsHTML,observedFindingsHTML,sourceHTML,packetHTML,scopeEditorText,scopeEdit,ruleNotesText,ruleEdits,captureDisclosureState,restoreDisclosureState,readRecovery,readIntake,createApp};
 if(typeof module!=='undefined')module.exports=api;
 else{root.Investigate=api;if(root.document?.getElementById('investigate'))root.investigateApp=createApp(root.document);}
})(globalThis);
