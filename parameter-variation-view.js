/* Presentation only: the controller verifies sources and creates reviewed variations. */
(function(root){
 'use strict';
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const text=value=>typeof value==='string'?value.trim():'';
 const phases=new Set(['choose','previewing','review','creating','error','complete']);
 function selectionEqual(a,b){return !!a&&!!b&&a.step===b.step&&a.parameter===b.parameter&&a.value===b.value;}
 function reset(value){return ({page:'each page',line:'each line',word:'each word'})[value]||'';}
 function mode(value){return ({repeat:'Repeat the starting key', 'plaintext-autokey':'Use earlier decoded runes', 'ciphertext-autokey':'Use earlier original runes'})[value]||'';}
 function setting(selection,value){return selection.parameter==='phase'&&Number.isInteger(value)&&value>=0&&value<=255?'Start at key position '+(value+1):['a','b'].includes(selection.parameter)&&Number.isInteger(value)&&value>=0&&value<=28?(selection.parameter==='a'?'Multiply rune values by '+value:'Add '+value+' after multiplying'):selection.parameter==='mode'?mode(value):selection.parameter==='unit'?(reset(value)?'Reverse runes within '+reset(value):''):selection.parameter==='direction'?({add:'Add the key values',subtract:'Subtract the key values'})[value]||'':reset(value)?'Restart the key at '+reset(value):'';}
 function href(value){return typeof value==='string'&&/^run\.html#(?:task=[a-f0-9]{64}(?:&idea=p_[a-f0-9]{64})?|idea=p_[a-f0-9]{64})$/.test(value)?value:'';}
 function sourceHref(value){return href(value)||typeof value==='string'&&/^run\.html#published=[a-z0-9]+(?:-[a-z0-9]+)*&case=[a-z0-9][a-z0-9-]*&revision=[a-f0-9]{64}$/.test(value)&&value||typeof value==='string'&&/^(?:library\.html#\/experiment\/[a-z0-9]+(?:-[a-z0-9]+)*|run\.html#family=[a-z0-9]+(?:-[a-z0-9]+)*&case=[a-z0-9][a-z0-9-]*&revision=[a-f0-9]{64})$/.test(value)&&value||'';}
 function pageLabel(pages){
  if(typeof pages==='string')return pages;
  if(!Array.isArray(pages)||!pages.length)return '';
  const ids=pages.map(p=>typeof p==='string'?p:p?.id).filter(p=>typeof p==='string');
  if(ids.length!==pages.length)return '';
  const matches=ids.map(id=>/^(lp[12])-(\d{2})$/i.exec(id));
  if(matches.every(Boolean)){
   const runs=[];let start=0;
   for(let i=1;i<=ids.length;i++)if(i===ids.length||matches[i][1].toLowerCase()!==matches[i-1][1].toLowerCase()||Number(matches[i][2])!==Number(matches[i-1][2])+1){runs.push(ids[start].toUpperCase()+(i-start>1?'–'+matches[i-1][2]:''));start=i;}
   return runs.join(', ');
  }
  return ids.map(id=>id.toUpperCase()).join(', ');
 }
 function model(input={}){
  const choices=(Array.isArray(input.choices)?input.choices:[]).map((choice,index)=>{
   const s=choice?.selection;
   if(!s||!Number.isInteger(s.step)||s.step<0||!['direction','reset','unit','mode','a','b','phase'].includes(s.parameter)||!setting(s,s.value))return null;
   const describe=value=>choice.op==='cumulative-difference'&&s.parameter==='reset'&&reset(value)?'Restart the running total at '+reset(value):setting(s,value);
   const v=choice.verified,verified=v&&Number.isInteger(v.covered)&&Number.isInteger(v.total)&&v.covered>0&&v.total>=v.covered?{covered:v.covered,total:v.total,...(v.derived===true?{derived:true}:{}),sources:(Array.isArray(v.sources)?v.sources:[]).slice(0,8).map(item=>({href:sourceHref(item.href),label:v.derived===true?'Inspect original saved output':'View verified saved output'})).filter(item=>item.href)}:null;return {index,selection:{...s},from:choice.from,verified,listed:!verified&&typeof choice.listed?.href==='string'&&choice.listed.href.startsWith('run.html#published=')&&sourceHref(choice.listed.href)?{href:choice.listed.href}:null,keyExample:s.parameter==='phase'&&choice.keyExample&&Array.isArray(choice.keyExample.before)&&Array.isArray(choice.keyExample.after)&&[...choice.keyExample.before,...choice.keyExample.after].every(v=>Number.isInteger(v)&&v>=0&&v<=28)&&choice.keyExample.before.length<=8&&choice.keyExample.after.length<=8?choice.keyExample:null,question:text(choice.question),reason:text(choice.reason),reading:text(choice.reading),modeExample:s.parameter==='mode'&&mode(choice.from)&&choice.from!==s.value?{before:choice.from,after:s.value}:null,reverseExample:s.parameter==='unit'&&reset(choice.from)&&choice.from!==s.value?{before:choice.from,after:s.value}:null,resetExample:s.parameter==='reset'&&reset(choice.from)&&choice.from!==s.value?{before:choice.from,after:s.value}:null,label:text(choice.question)||text(choice.label)||describe(s.value)+(s.parameter==='direction'?' instead':''),stepLabel:Object.hasOwn(choice,'stepLabel')?text(choice.stepLabel):'Step '+(s.step+1),before:text(choice.before)||describe(choice.from),after:text(choice.after)||describe(s.value)};
  }).filter(Boolean);
  const selected=choices.find(c=>typeof input.selected==='number'?c.index===input.selected:selectionEqual(c.selection,input.selected))||null;
  const phase=phases.has(input.phase)?input.phase:'choose',change=input.change||{},scope=input.scope||{};
  const steps=(Array.isArray(input.steps)?input.steps:[]).filter(s=>Number.isInteger(s?.index)&&s.index>=0).filter((s,i,all)=>all.findIndex(other=>other.index===s.index)===i).map(s=>({index:s.index,label:text(s.label)||'Step '+(s.index+1)}));
  const stepIndex=steps.some(s=>s.index===input.stepIndex)?input.stepIndex:steps[0]?.index;
  const c=input.coverage,coverage=c&&Array.isArray(c.coveredPages)&&Array.isArray(c.remainingPages)?{derived:c.derived===true,covered:c.coveredPages.length,remaining:c.remainingPages.length,complete:c.lookupComplete===true&&c.coveredPages.length+c.remainingPages.length>0,finding:c.finding?.kind==='opening-check'&&Array.isArray(c.finding.matchingPages)?{matches:c.finding.matchingPages.length,pages:pageLabel(c.finding.matchingPages)}:null,links:[...(Array.isArray(c.evidence)?c.evidence:[]),...(c.derived===true&&Array.isArray(c.sourceLinks)?c.sourceLinks:[])].map(ref=>({href:sourceHref(ref.href),label:text(ref.label)||'View saved calculation',pages:pageLabel(ref.pages)})).filter(ref=>ref.href)}:null;
  return {choices,selected,steps,stepIndex,phase,coverage,change:{before:text(change.before)||selected?.before||'',after:text(change.after)||selected?.after||'',stepLabel:text(change.stepLabel)||selected?.stepLabel||''},scope:{pages:pageLabel(scope.pages)||text(scope.label),kind:scope.kind==='question'?'question':'calculation',sourcePages:pageLabel(scope.sourcePages),key:text(scope.key),keyLabel:text(scope.keyLabel)||'Key',comparison:text(scope.comparison),openings:(Array.isArray(scope.openings)?scope.openings:[]).slice(0,32).map(item=>({label:text(item.label),runes:item.runes,href:typeof item.href==='string'&&/^index\.html#\/reader\/lp[12]-[0-9]{2}$/.test(item.href)?item.href:''})).filter(item=>item.label&&Number.isInteger(item.runes)&&item.runes>0&&item.runes<=256)},error:text(input.error),check:{href:href(input.check?.href),covered:input.check?.covered===true,title:text(input.check?.title)}};
 }
 function coverageHTML(c){
  if(!c)return '';
  const total=c.covered+c.remaining,full=c.complete&&c.covered>0&&!c.remaining;
  const finding=c.covered&&c.finding?(c.finding.matches?(c.derived?'Comparing saved output: a supplied sequence matched on ':'A supplied opening matched on ')+esc(c.finding.pages)+'.':c.derived?'No supplied sequence matched when comparing the saved output.':'No supplied opening matched in the saved results.'):'',summary=(full?total===1?'Saved results cover this page.':'Saved results cover all '+total+' pages.':c.complete?c.covered?'Saved results cover '+c.covered+' of '+total+' pages.':'No matching saved results were found for these exact settings.':'The saved-result lookup is incomplete.')+(c.complete&&c.covered&&c.remaining?' '+c.remaining+' '+(c.remaining===1?'page remains':'pages remain')+' to check.':'');
  const presentedSummary=c.derived?(!c.complete?summary:full?'Earlier output answers this comparison on '+total+' '+(total===1?'page.':'pages.'):c.covered?'Earlier output answers this comparison on '+c.covered+' of '+total+' pages.'+(c.remaining?' '+c.remaining+' '+(c.remaining===1?'page remains':'pages remain')+' to check.':''):summary):summary;
  let result='<div class="parameter-variation-coverage" role="status">'+(c.derived?'<p class="small">Comparison from saved output</p>':'')+(finding?'<p><strong>'+finding+'</strong></p><p>'+presentedSummary+'</p>':'<p><strong>'+presentedSummary+'</strong></p>');
  const link=ref=>'<li><a href="'+esc(ref.href)+'">'+esc(ref.label)+(ref.pages?' · '+esc(ref.pages):'')+'</a></li>';
  if(c.links.length)result+='<ul>'+c.links.slice(0,3).map(link).join('')+'</ul>'+(c.links.length>3?'<details><summary>More saved sources ('+(c.links.length-3)+')</summary><ul>'+c.links.slice(3).map(link).join('')+'</ul></details>':'');
  return result+'</div>';
 }
 function resetIllustration(example){
  if(!example)return '';
  function sequence(mode){return Array.from({length:2},(_,line)=>'<div class="parameter-variation-example-line">'+Array.from({length:2},(_,word)=>'<span class="parameter-variation-example-word">'+Array.from({length:2},(_,rune)=>'<span>'+((mode==='page'?line*4+word*2:mode==='line'?word*2:0)+rune+1)+'</span>').join('')+'</span>').join('')+'</div>').join('');}
  return '<figure class="parameter-variation-example"><figcaption>Where the count starts over</figcaption><div class="parameter-variation-example-pair">'+[['Before',example.before],['After',example.after]].map(([label,mode])=>'<div><p>'+label+' · '+esc(reset(mode))+'</p><div aria-label="'+label+': rune count restarts at '+esc(reset(mode))+'">'+sequence(mode)+'</div></div>').join('')+'</div><p>Example: four short words on two lines. Numbers count runes since the last restart; they are not key values or results.</p></figure>';
 }
 function reverseIllustration(example){
  if(!example)return '';
  const output={word:'BA DC.\nFE HG!',line:'DC BA.\nHG FE!',page:'HG FE.\nDC BA!'};
  return '<figure class="parameter-variation-reversal"><figcaption>Example rune order</figcaption><p>Input</p><pre><code>AB CD.\nEF GH!</code></pre><div class="parameter-variation-reversal-pair">'+[['Before',example.before],['After',example.after]].map(([label,unit])=>'<div><p>'+label+' · '+esc(reset(unit))+'</p><pre><code>'+esc(output[unit])+'</code></pre></div>').join('')+'</div><p>A–H stand for eight runes. Spaces, punctuation and line breaks stay in place.</p></figure>';
 }
 function modeIllustration(example){
  if(!example)return '';
  const examples={repeat:{values:[2,5],source:'From the starting key'},'plaintext-autokey':{values:[8,7],source:'From earlier decoded runes'},'ciphertext-autokey':{values:[10,12],source:'From earlier original runes'}};
  const chips=values=>'<span class="parameter-variation-key-chips">'+values.map(value=>'<span>'+value+'</span>').join('')+'</span>';
  const source=(label,values)=>'<div class="parameter-variation-key-source-group"><span>'+label+'</span>'+chips(values)+'</div>';
  return '<figure class="parameter-variation-key-source"><figcaption>Example: where later key numbers come from</figcaption><div class="parameter-variation-key-equation" role="group" aria-label="Illustration: original rune numbers 10, 12 minus starting key 2, 5 produce decoded rune numbers 8, 7.">'+source('Original runes',[10,12])+'<span class="parameter-variation-key-operator" aria-hidden="true">−</span>'+source('Starting key',[2,5])+'<span class="parameter-variation-key-operator" aria-hidden="true">=</span>'+source('Decoded runes',[8,7])+'</div><div class="parameter-variation-key-source-pair">'+[['Before',example.before],['After',example.after]].map(([label,value])=>'<div><h3>'+label+' · '+esc(mode(value))+'</h3><p>'+examples[value].source+'</p><div class="parameter-variation-key-next"><span>Next key</span><span aria-hidden="true">→</span>'+chips(examples[value].values)+'</div></div>').join('')+'</div><p>Illustration only, not manuscript output. The supplied key, arithmetic and restart boundaries stay unchanged.</p></figure>';
 }
 function verifiedLabel(choice){return choice.verified?(choice.verified.derived?(choice.verified.covered===choice.verified.total?'Comparison from saved output':'Comparison from saved output on '+choice.verified.covered+' of '+choice.verified.total+' pages'):choice.verified.covered===choice.verified.total?'Saved output verified':'Saved output verified on '+choice.verified.covered+' of '+choice.verified.total+' pages'):choice.listed?'Archived output listed':'';}
 function choiceSources(choice){if(choice?.listed)return '<a href="'+esc(choice.listed.href)+'">Review listed output</a>';return choice?.verified?.sources?.length?choice.verified.sources.map(source=>'<a href="'+esc(source.href)+'">'+esc(source.label)+'</a>').join(' · '):'';}
 function phaseStatus(choice){const label=choice&&verifiedLabel(choice);return label?'<span>'+esc(label)+'</span>'+(choiceSources(choice)?' · '+choiceSources(choice):''):'';}
 function phaseChoices(m){
  const choices=m.choices.filter(c=>c.selection.parameter==='phase');if(!choices.length)return '';const allVerified=choices.every(c=>c.verified&&c.verified.covered===c.verified.total);
  return '<div class="parameter-variation-coefficients">'+(allVerified?'<p class="small">'+(choices.some(c=>c.verified?.derived)?'All starting places shown have comparisons from saved output.':'All starting places shown have verified saved output.')+'</p>':'')+'<label class="parameter-variation-step-select">Start the repeating key later<select data-variation-phase><option value="">Choose a starting place</option>'+choices.map(c=>'<option value="'+c.index+'">'+c.selection.value+' '+(c.selection.value===1?'rune':'runes')+' later · position '+(c.selection.value+1)+(verifiedLabel(c)?' — '+esc(verifiedLabel(c)):'')+'</option>').join('')+'</select></label><p class="small" data-variation-phase-status hidden></p><button type="button" data-parameter-variation="review-phase" disabled>Review this change</button></div>';
 }
 function phaseIllustration(example){
  if(!example)return '';
  return '<figure class="parameter-variation-reversal"><figcaption>Repeating key values</figcaption><div class="parameter-variation-reversal-pair">'+[['Before · position 1',example.before],['After · position '+example.position,example.after]].map(([label,values])=>'<div><p>'+esc(label)+'</p><pre><code>'+esc(values.join(' · '))+'</code></pre></div>').join('')+'</div><p>'+(example.length>8?'First 8 of '+esc(example.length)+' key values. ':'')+'Key sequence only, not calculated output.</p></figure>';
 }
 function affineChoices(m){
  const choices=m.choices.filter(c=>['a','b'].includes(c.selection.parameter));if(!choices.length)return '';
  const parameters=[...new Set(choices.map(c=>c.selection.parameter))],first=parameters[0];
  return '<div class="parameter-variation-coefficients"><label class="parameter-variation-step-select">Change which number?<select data-variation-coefficient>'+parameters.map(parameter=>'<option value="'+parameter+'">'+(parameter==='a'?'Multiply rune values':'Add after multiplying')+'</option>').join('')+'</select></label><p data-variation-coefficient-current>Currently '+esc(choices.find(c=>c.selection.parameter===first).from)+'</p><label class="parameter-variation-step-select">New number<select data-variation-coefficient-value><option value="">Choose a number</option>'+choices.filter(c=>c.selection.parameter===first).map(c=>'<option value="'+c.index+'">'+c.selection.value+(verifiedLabel(c)?' — '+esc(verifiedLabel(c)):'')+'</option>').join('')+'</select></label><p class="small" data-variation-coefficient-status hidden></p><button type="button" data-parameter-variation="review-affine" disabled>Review this change</button></div>';
 }
 function render(input={}){
  const m=model(input);if(!m.choices.length&&m.phase!=='complete')return '';
  let body='<h2>'+esc(m.phase==='choose'?'Try a variation':m.selected?.question||(m.phase==='complete'?'Variation saved':'Review the change'))+'</h2>';
  if(m.phase==='complete'){
   body+='<p role="status">'+(m.check.covered?'This calculation already has saved results.':'Your variation is saved. Review the check before running it on your device.')+'</p>'+(m.check.href?'<a class="parameter-variation-primary" href="'+esc(m.check.href)+'">'+(m.check.covered?'View saved results':'Review and run')+'</a>':'');
  }else if(m.phase==='choose'){
   body+='<p>Change one part of this calculation.</p>'+(m.steps.length>1?'<label class="parameter-variation-step-select">Change which step?<select data-parameter-variation-step>'+m.steps.map(s=>'<option value="'+s.index+'"'+(s.index===m.stepIndex?' selected':'')+'>'+esc(s.label)+'</option>').join('')+'</select></label>':'')+affineChoices(m)+phaseChoices(m)+'<div class="parameter-variation-choices">'+m.choices.filter(c=>!['a','b','phase'].includes(c.selection.parameter)).map(c=>'<button type="button" data-parameter-variation="select" data-variation-index="'+c.index+'">'+(c.stepLabel?'<span class="parameter-variation-step">'+esc(c.stepLabel)+'</span>':'')+esc(c.label)+(verifiedLabel(c)?'<span class="parameter-variation-step">'+esc(verifiedLabel(c))+'</span>':'')+'</button>').join('')+'</div>';
  }else if(m.phase==='review'&&m.coverage?.complete&&m.coverage.covered&&!m.coverage.remaining){
   const reading=m.coverage.finding?(m.coverage.finding.matches?'Inspect the full output. An opening match alone does not establish a decryption.':'Other possible text remains untested by this opening check.'):m.selected?.reading;
   body+=(m.selected?.reason?'<p>'+esc(m.selected.reason)+'</p>':'')+coverageHTML(m.coverage)+(reading?'<p>'+esc(reading)+'</p>':'')+'<button type="button" data-parameter-variation="cancel">Choose another change</button>';
  }else{
   body+=coverageHTML(m.coverage);
   body+=(m.selected?.reason?'<p>'+esc(m.selected.reason)+'</p>':'')+(m.change.stepLabel?'<p class="parameter-variation-step">'+esc(m.change.stepLabel)+'</p>':'');
   body+=m.selected?.keyExample?phaseIllustration(m.selected.keyExample):m.selected?.modeExample?modeIllustration(m.selected.modeExample):m.selected?.reverseExample?reverseIllustration(m.selected.reverseExample):m.selected?.question&&m.selected.resetExample?resetIllustration(m.selected.resetExample):'<dl class="parameter-variation-change"><div><dt>Before</dt><dd>'+esc(m.change.before)+'</dd></div><div><dt>After</dt><dd>'+esc(m.change.after)+'</dd></div></dl>';
   body+='<p class="parameter-variation-scope">'+(m.scope.kind==='question'?'This variation checks':'Applies to the full original calculation')+(m.scope.pages?': <strong>'+esc(m.scope.pages)+'</strong>':'.')+(m.scope.kind==='question'&&m.scope.sourcePages&&m.scope.sourcePages!==m.scope.pages?'. The earlier result checked <strong>'+esc(m.scope.sourcePages)+'</strong>.':'')+'</p>';
   const same=[m.selected?.selection.parameter!=='unit'&&m.scope.key&&[m.scope.keyLabel,m.scope.key],m.scope.comparison&&['Comparison',m.scope.comparison]].filter(Boolean);
   if(same.length)body+='<dl class="parameter-variation-same">'+same.map(([label,value])=>'<div><dt>'+esc(label)+' · unchanged</dt><dd>'+esc(value)+'</dd></div>').join('')+'</dl>';
   if(m.scope.openings.length)body+='<details class="experiment-details"><summary>Which openings are compared?</summary><ul>'+m.scope.openings.map(item=>'<li>'+(item.href?'<a href="'+esc(item.href)+'">'+esc(item.label)+'</a>':esc(item.label))+' · '+item.runes+' runes</li>').join('')+'</ul><p>Only the start of each page’s output is compared.</p></details>';
   if(m.selected?.reading)body+='<p class="parameter-variation-reading">'+esc(m.selected.reading)+'</p>';
   if(m.phase==='previewing')body+='<p role="status" aria-live="polite">Reviewing this change and checking saved results…</p>';
   if(m.phase==='creating')body+='<p role="status" aria-live="polite">Preparing check…</p>';
   if(m.phase==='error')body+='<p class="parameter-variation-error" role="alert">'+esc(m.error||'The variation could not be created. Try again.')+'</p>';
   const incomplete=m.coverage&&!m.coverage.complete;
   body+=(!['creating','previewing','error'].includes(m.phase)&&!incomplete?'<p class="small">Saves a shared question. Running it on your device is a separate step.</p>':'')+'<div class="parameter-variation-actions">'+(['creating','previewing'].includes(m.phase)?'':'<button type="button" class="parameter-variation-primary" data-parameter-variation="'+(m.phase==='error'||incomplete?'retry':'create')+'">'+(incomplete?'Retry saved-result lookup':m.phase==='error'?'Try again':'Save variation')+'</button>')+'<button type="button" data-parameter-variation="cancel">Cancel</button></div>';
  }
  return '<section class="parameter-variation" aria-label="Change this calculation"'+(['creating','previewing'].includes(m.phase)?' aria-busy="true"':'')+'>'+body+'</section>';
 }
 function bind(host,actions={},input={}){
  const m=model(input),removers=[];
  for(const button of host.querySelectorAll?.('[data-parameter-variation]')||[]){
   const action=button.getAttribute('data-parameter-variation');
   const listener=()=>{if(action==='review-phase'){const value=host.querySelector?.('[data-variation-phase]')?.value;if(!/^(0|[1-9][0-9]*)$/.test(value||''))return;const c=m.choices.find(choice=>choice.index===Number(value)&&choice.selection.parameter==='phase');if(c)actions.select?.(c.index,c);}else if(action==='review-affine'){const parameter=host.querySelector?.('[data-variation-coefficient]')?.value,value=host.querySelector?.('[data-variation-coefficient-value]')?.value;if(!/^(0|[1-9][0-9]*)$/.test(value||''))return;const c=m.choices.find(choice=>choice.index===Number(value)&&choice.selection.parameter===parameter);if(c)actions.select?.(c.index,c);}else if(action==='select'){const c=m.choices.find(choice=>choice.index===Number(button.getAttribute('data-variation-index')));if(c)actions.select?.(c.index,c);}else if(action==='retry'&&m.coverage&&!m.coverage.complete){if(m.selected)actions.select?.(m.selected.index,m.selected);}else if(['create','cancel','retry'].includes(action))actions[action]?.();};
   button.addEventListener('click',listener);removers.push(()=>button.removeEventListener('click',listener));
  }
  const hasCoefficients=m.choices.some(c=>['a','b'].includes(c.selection.parameter)),coefficient=hasCoefficients?host.querySelector?.('[data-variation-coefficient]'):null,coefficientValue=hasCoefficients?host.querySelector?.('[data-variation-coefficient-value]'):null;
  if(coefficient&&coefficientValue){const review=host.querySelector?.('[data-parameter-variation="review-affine"]'),current=host.querySelector?.('[data-variation-coefficient-current]');const valueChange=()=>{const found=m.choices.find(c=>c.selection.parameter===coefficient.value&&String(c.index)===coefficientValue.value);if(review)review.disabled=!found;const status=host.querySelector?.('[data-variation-coefficient-status]');if(status){status.innerHTML=phaseStatus(found);status.hidden=!status.innerHTML;}};const change=()=>{const choices=m.choices.filter(c=>c.selection.parameter===coefficient.value&&['a','b'].includes(c.selection.parameter));coefficientValue.innerHTML='<option value="">Choose a number</option>'+choices.map(c=>'<option value="'+c.index+'">'+c.selection.value+(verifiedLabel(c)?' — '+esc(verifiedLabel(c)):'')+'</option>').join('');coefficientValue.value='';if(current)current.textContent=choices.length?'Currently '+choices[0].from:'';valueChange();};coefficient.addEventListener('change',change);coefficientValue.addEventListener('change',valueChange);removers.push(()=>coefficient.removeEventListener('change',change),()=>coefficientValue.removeEventListener('change',valueChange));}
  const phaseSelect=m.choices.some(c=>c.selection.parameter==='phase')?host.querySelector?.('[data-variation-phase]'):null;if(phaseSelect){const review=host.querySelector?.('[data-parameter-variation="review-phase"]'),change=()=>{const chosen=m.choices.find(c=>c.selection.parameter==='phase'&&String(c.index)===phaseSelect.value);if(review)review.disabled=!chosen;const status=host.querySelector?.('[data-variation-phase-status]');if(status){status.innerHTML=phaseStatus(chosen);status.hidden=!status.innerHTML;}};phaseSelect.addEventListener('change',change);removers.push(()=>phaseSelect.removeEventListener('change',change));}
  const stepSelect=host.querySelector?.('[data-parameter-variation-step]');
  if(stepSelect){const change=event=>{const value=event?.target?.value;if(!/^(0|[1-9][0-9]*)$/.test(value))return;const index=Number(value);if(m.steps.some(step=>step.index===index))actions.step?.(index);};stepSelect.addEventListener('change',change);removers.push(()=>stepSelect.removeEventListener('change',change));}
  return ()=>removers.forEach(remove=>remove());
 }
 const api={model,render,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.ParameterVariationView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
