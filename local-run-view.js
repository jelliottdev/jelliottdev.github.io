/* Shared result view. All conclusions and chart values come from replayed data. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const bindings=new WeakMap(),languageComparisons=new WeakMap(),inspectionOutputs=new WeakMap();
 const LANGUAGE_REFERENCES=[['eng_Latn','English'],['cym_Latn','Welsh'],['deu_Latn','German'],['fra_Latn','French'],['spa_Latn','Spanish'],['ita_Latn','Italian'],['por_Latn','Portuguese'],['fin_Latn','Finnish']];
 function languageDescriptor(task){
  const registry=typeof module==='object'&&module.exports?require('./output-evaluators.js'):root.OutputEvaluators;
  const descriptor=registry?.describe(task.criterion);if(!descriptor)throw Error('The language comparison is not supported by this view.');return descriptor;
 }
 function finiteShiftExample(task,result,id){
  if(task.steps.length!==1||task.steps[0].op!=='finite-shift')return '';
  const step=task.steps[0],page=task.pages.find(p=>p.id===id),after=result.transformed.find(p=>p.page===id);
  if(!page||!after)return '';
  const index=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),original=Array.from(page.text),output=Array.from(after.text),rows=[];let position=0;
  for(let i=0;i<original.length&&rows.length<3;i++){
   const ch=original[i];
   if(!index.has(ch)){if(step.reset==='word'||step.reset==='line'&&/[\r\n]/.test(ch))position=0;continue;}
   const input=index.get(ch),key=step.key[position++],raw=input+(step.direction==='add'?key:-key),value=((raw%29)+29)%29;
   if(!Number.isInteger(key)||output[i]!==task.alphabet[value]?.rune)return '';
   rows.push({input,key,raw,value});
  }
  if(!rows.length)return '';
  const symbol=step.direction==='add'?'+':'−',cell=value=>'<td><span class="run-step-rune">'+esc(task.alphabet[value].rune)+'</span><small>'+value+'</small></td>',first=rows[0];
  const reset={page:'Start the sequence again on each page.',line:'Start the sequence again on each line.',word:'Start the sequence again after every non-rune character.'}[step.reset];
  return '<figure class="run-step-example"><figcaption>How this setting changes the runes</figcaption><table><caption>'+esc(id.toUpperCase())+' · first '+rows.length+' rune'+(rows.length===1?'':'s')+'</caption><thead><tr><th scope="col">Rune</th>'+rows.map((_,i)=>'<th scope="col">'+(i+1)+'</th>').join('')+'</tr></thead><tbody><tr><th scope="row">Original</th>'+rows.map(row=>cell(row.input)).join('')+'</tr><tr><th scope="row">'+(step.direction==='add'?'Add':'Subtract')+'</th>'+rows.map(row=>'<td class="run-step-change">'+symbol+' '+row.key+'</td>').join('')+'</tr><tr><th scope="row">Result</th>'+rows.map(row=>cell(row.value)).join('')+'</tr></tbody></table><p class="run-step-equation">First rune: '+first.input+' '+symbol+' '+first.key+' = '+first.raw+(first.raw===first.value?'.':'; wrap to '+first.value+'.')+'</p><p class="run-text-note">Rune numbers go from 0 to 28 and wrap around. '+reset+' The sequence is not repeated within a '+step.reset+'.</p></figure>';
 }
 function languagePage(task,result,id,comparison=null){
  const page=comparison||result.languageScore.pages.find(p=>p.page===id),output=result.transformed.find(p=>p.page===id),characters=Array.from(output.text),excerpt=characters.slice(0,120).join('');
  const introduction=finiteShiftExample(task,result,id)+'<h3>After the method · '+esc(id.toUpperCase())+'</h3><p class="run-text-note">Rune labels, not a translation.'+(characters.length>120?' First 120 characters; inspect the complete text below.':'')+'</p><pre class="run-language-excerpt">'+esc(transliteration(excerpt,task.alphabet))+(characters.length>120?'…':'')+'</pre>';
  if(page.status==='insufficient')return introduction+'<h3>Too little text to compare</h3><p>This page has '+page.runes+' runes. This comparison needs at least 40. No language scores were calculated.</p><p>Inspect the output directly, or separately review a longer passage to check.</p>';
  return introduction+'<h3>Compared with rearranged text</h3><p>For each reference, the bar counts how many of 32 rearrangements scored at least as high as this output. Every rearrangement keeps the same runes and length.</p><p class="run-language-caution"><strong>A short bar is not evidence of readable text.</strong> Unreadable outputs can also score above all 32 rearrangements. These rows do not identify the language.</p><ul class="run-language-comparisons" aria-label="Language reference comparisons">'+LANGUAGE_REFERENCES.map(([id,label])=>{const model=page.models.find(m=>m.id===id);if(!model)throw Error('A language reference is missing.');return '<li><div class="run-language-row"><span>'+label+'</span><span>'+model.shuffledAtOrAbove+' of 32</span></div><div class="run-language-track" role="img" aria-label="'+label+': '+model.shuffledAtOrAbove+' of 32 rearrangements scored at least as high as the output"><span style="width:'+(model.shuffledAtOrAbove/32*100)+'%"></span></div></li>';}).join('')+'</ul><p class="run-text-note">References stay in a fixed order. Each compares groups of three runes after the same spelling conversion. Counts describe these 32 rearrangements, not confidence in a language.</p><details class="run-language-values"><summary>Exact comparison values</summary><div class="run-language-table-wrap"><table><thead><tr><th>Reference</th><th>Output score</th><th>Rearranged range</th></tr></thead><tbody>'+LANGUAGE_REFERENCES.map(([id,label])=>{const model=page.models.find(m=>m.id===id);return '<tr><th scope="row">'+label+'</th><td>'+model.total+'</td><td>'+model.shuffledMin+' to '+model.shuffledMax+'</td></tr>';}).join('')+'</tbody></table></div><p class="run-text-note">Scores are model-specific integer totals. Compare each output with its own rearrangements, not raw scores across languages.</p></details>';
 }
 function languageView(task,result){
  const descriptor=languageDescriptor(task),first=task.pages[0].id;
  return '<section class="run-language" data-run-language>'+ (task.pages.length>1?'<label class="run-language-page">Page<select data-run-language-page>'+task.pages.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.id.toUpperCase())+'</option>').join('')+'</select></label>':'')+'<div data-run-language-content>'+languagePage(task,result,first)+'</div><section class="run-language-next"><h3>What to check next</h3><p>'+esc(descriptor.next)+'</p><p>'+esc(descriptor.limit)+'</p></section></section>';
 }
 function bindLanguage(host,task,result,initialPage){
  const panel=host.querySelector?.('[data-run-language]'),select=panel?.querySelector('[data-run-language-page]'),content=panel?.querySelector('[data-run-language-content]');
  if(!select||!content)return ()=>{};
  const change=()=>{if(task.pages.some(p=>p.id===select.value))content.innerHTML=languagePage(task,result,select.value);};
  if(initialPage){select.value=initialPage;change();}select.addEventListener('change',change);return ()=>select.removeEventListener?.('change',change);
 }
 function outputExcerpt(task,result,id){
  const output=result.transformed.find(page=>page.page===id),chars=Array.from(output.text),excerpt=chars.slice(0,120).join('');
  return finiteShiftExample(task,result,id)+'<p class="run-text-note">'+esc(id.toUpperCase())+(chars.length>120?' · First 120 characters':'')+'</p><pre class="run-language-excerpt">'+esc(transliteration(excerpt,task.alphabet))+(chars.length>120?'…':'')+'</pre>';
 }
 function outputPreview(task,result){
  return '<section data-run-output-preview><h2 id="local-run-finding">What the method produced</h2><p>Shown with Latin rune labels, not a translation. This run does not decide whether the output is readable.</p>'+(task.pages.length>1?'<label class="run-language-page">Page<select data-run-output-page>'+task.pages.map(page=>'<option value="'+esc(page.id)+'">'+esc(page.id.toUpperCase())+'</option>').join('')+'</select></label>':'')+'<div data-run-output-content>'+outputExcerpt(task,result,task.pages[0].id)+'</div></section>';
 }
 function bindOutputPreview(host,task,result,pageId){
  const panel=host.querySelector?.('[data-run-output-preview]'),select=panel?.querySelector('[data-run-output-page]'),content=panel?.querySelector('[data-run-output-content]');if(!select||!content)return ()=>{};
  const change=()=>{if(task.pages.some(page=>page.id===select.value))content.innerHTML=outputExcerpt(task,result,select.value);};
  select.addEventListener('change',change);if(pageId){select.value=pageId;change();}return ()=>select.removeEventListener?.('change',change);
 }
 function pageLabel(pages){
  const groups=[];for(const page of pages){const id=page.id,last=groups.at(-1);if(last&&last.at(-1).slice(0,4)===id.slice(0,4)&&Number(last.at(-1).slice(4))+1===Number(id.slice(4)))last.push(id);else groups.push([id]);}
  return groups.map(group=>group[0].toUpperCase()+(group.length>1?'–'+group.at(-1).slice(4):'')).join(', ')+(pages.length>1?' ('+pages.length+' pages)':'');
 }
 function transliteration(text,alphabet,joined=false){
  const labels=new Map(alphabet.map(entry=>[entry.rune,entry.latin]));let previousRune=false,out='';
  for(const character of text){const rune=labels.has(character);out+=(rune&&previousRune&&!joined?'·':'')+(rune?labels.get(character):character);previousRune=rune;}
  return out;
 }
 function prefixDifference(task,result,pageId,expected){
  const indices=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),text=result.transformed.find(page=>page.page===pageId).text,observed=Array.from(text).filter(rune=>indices.has(rune)).map(rune=>indices.get(rune));
  return {observed,mismatch:expected.findIndex((value,i)=>observed[i]!==value)};
 }
 function prefixMismatch(task,result){
  for(const page of task.pages){
   const {observed,mismatch}=prefixDifference(task,result,page.id,task.criterion.values);if(mismatch<0)continue;
   const expected=task.alphabet[task.criterion.values[mismatch]].rune,actual=observed[mismatch]===undefined?null:task.alphabet[observed[mismatch]].rune;
   return '<p class="run-prefix-status"><strong>'+esc(page.id.toUpperCase())+' · '+(task.pages.length>1?'example: ':'')+(actual===null?'output ends before rune ':'first mismatch at rune ')+(mismatch+1)+'.</strong> Expected <span class="run-prefix-symbol">'+esc(expected)+'</span>; '+(actual===null?'no output rune remains.':'actual <span class="run-prefix-symbol">'+esc(actual)+'</span>.')+'</p>';
  }
  return '';
 }
 function prefixAlignment(task,result,pageId,mode='runes',expected=task.criterion.values){
  const {observed,mismatch}=prefixDifference(task,result,pageId,expected),start=mismatch<0?0:Math.max(0,mismatch-3),end=Math.min(expected.length,start+8),label=value=>value===undefined?'Missing':mode==='latin'?task.alphabet[value].latin:task.alphabet[value].rune;
  const status=mismatch<0?'All '+expected.length+' prefix positions match.':observed[mismatch]===undefined?'The output ends before prefix position '+(mismatch+1)+'.':'First mismatch at prefix position '+(mismatch+1)+'.';
  return '<section class="run-prefix-alignment"><h3>Expected and observed prefix</h3><p class="run-prefix-status">'+esc(pageId.toUpperCase()+': '+status)+'</p><p class="run-text-note">'+'Showing positions '+(start+1)+'–'+end+' of '+expected.length+'. '+'Positions count runes only; separators do not occupy a position.</p><table class="run-prefix-table"><thead><tr><th scope="col">Position</th><th scope="col">Expected</th><th scope="col">Actual</th><th scope="col">Result</th></tr></thead><tbody>'+expected.slice(start,end).map((value,offset)=>{const i=start+offset,missing=observed[i]===undefined,same=value===observed[i];return '<tr class="run-prefix-pair'+(same?'':' is-different')+'"><th scope="row">'+(i+1)+'</th><td class="run-prefix-symbol">'+esc(label(value))+'</td><td'+(missing?'':' class="run-prefix-symbol"')+'>'+esc(label(observed[i]))+'</td><td>'+(same?'Match':missing?'Missing':'Different')+'</td></tr>';}).join('')+'</tbody></table></section>';
 }
 function prefixChart(task,result){
  const matched=result.matches.filter(row=>row.matched).length,total=task.pages.length,notMatched=total-matched;
  return '<figure class="local-run-chart run-prefix-chart"><figcaption>Exact starting-sequence check</figcaption><div class="run-prefix-total" role="img" aria-label="'+matched+' of '+total+' pages matched all '+task.criterion.values.length+' prefix positions; '+notMatched+' did not match."><span class="run-prefix-match" style="width:'+(100*matched/total).toFixed(4)+'%"></span><span class="run-prefix-other" style="width:'+(100*notMatched/total).toFixed(4)+'%"></span></div><dl class="run-prefix-counts"><div><dt>Matched every position</dt><dd>'+matched+' of '+total+' pages</dd></div><div><dt>Did not match</dt><dd>'+notMatched+' of '+total+' pages</dd></div></dl><p class="run-chart-note">The fixed prefix has '+task.criterion.values.length+' rune positions.</p></figure>';
 }
 function openingName(id){const names={warning:'Warning',welcome:'Welcome','some-wisdom':'Some Wisdom','first-koan':'First Koan','loss-of-divinity':'Loss of Divinity','second-koan':'Second Koan',instruction:'Instruction','lp2-56':'LP2 page 56','lp2-57':'LP2 page 57'};return Object.hasOwn(names,id)?names[id]:id;}
 function openingSetPage(task,result,pageId){
  const indices=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),text=result.transformed.find(page=>page.page===pageId).text,values=Array.from(text).filter(ch=>indices.has(ch)).map(ch=>indices.get(ch)),matched=result.matches.find(page=>page.page===pageId).matchingOpenings;
  const status=!values.length?'No runes to compare.':matched.length?'Full opening match: '+matched.map(openingName).join(', ')+'.':values.length<Math.min(...task.criterion.openings.map(item=>item.values.length))?'The output is too short to contain any complete supplied opening.':'No complete supplied opening matched.';
  return finiteShiftExample(task,result,pageId)+'<h3>'+esc(pageId.toUpperCase())+'</h3><p class="run-prefix-status">'+esc(status)+'</p><table class="run-prefix-table" style="table-layout:fixed;width:100%"><caption>Supplied openings compared with this page’s output</caption><thead><tr><th scope="col" style="width:44%">Opening</th><th scope="col" style="width:18%">Runes</th><th scope="col">Result</th></tr></thead><tbody>'+task.criterion.openings.map(item=>{const mismatch=item.values.findIndex((value,i)=>values[i]!==value),matching=matched.includes(item.id),short=values.length<item.values.length&&mismatch===values.length,assessment=matching?'<strong>Full match</strong>':!values.length?'No runes':short?'Too short<br>'+values.length+' of '+item.values.length+' runes':'Different<br>Rune '+(mismatch+1);return '<tr class="run-prefix-pair'+(matching?'':' is-different')+'"><th scope="row" style="overflow-wrap:anywhere">'+esc(openingName(item.id))+'</th><td>'+item.values.length+'</td><td>'+assessment+'</td></tr>';}).join('')+'</tbody></table>';
 }
 function openingSetView(task,result){
  const matched=result.matches.filter(page=>page.matched).length,indices=new Set(task.alphabet.map(item=>item.rune)),empty=result.transformed.filter(page=>!Array.from(page.text).some(ch=>indices.has(ch))).length;
  return '<section class="local-run-result" aria-labelledby="local-run-finding"><p class="run-state">Computation verified</p><h2 id="local-run-finding">'+(matched?'An output matches a supplied opening':'No supplied opening found')+'</h2><p>'+matched+' of '+task.pages.length+' page outputs begin with at least one of the '+task.criterion.openings.length+' supplied openings.'+(empty?' '+empty+' '+(empty===1?'output contains':'outputs contain')+' no runes.':'')+'</p><p class="run-limit">Only a complete opening counts as a match. A match does not establish a decryption; a missing match does not rule out the broader idea.</p><section data-run-opening-set>'+(task.pages.length>1?'<label class="run-language-page">Page<select data-run-opening-set-page>'+task.pages.map(page=>'<option value="'+esc(page.id)+'">'+esc(page.id.toUpperCase())+'</option>').join('')+'</select></label>':'')+'<div data-run-opening-set-content>'+openingSetPage(task,result,task.pages[0].id)+'</div></section><p class="run-text-note">Positions count runes only; spaces and punctuation are ignored. Opening names identify the supplied sequences, not a new translation.</p>'+inspector(task,result)+'</section>';
 }
 function bindOpeningSet(host,task,result,initialPage){
  const panel=host.querySelector?.('[data-run-opening-set]'),select=panel?.querySelector('[data-run-opening-set-page]'),content=panel?.querySelector('[data-run-opening-set-content]');if(!select||!content)return ()=>{};
  const change=()=>{if(task.pages.some(page=>page.id===select.value))content.innerHTML=openingSetPage(task,result,select.value);};
  select.addEventListener('change',change);if(initialPage){select.value=initialPage;change();}return ()=>select.removeEventListener?.('change',change);
 }
 function wordPairExample(task,result){
  if(!result.wordPairs.matches)return '';
  const rule=task.criterion,indices=new Map(task.alphabet.map((entry,i)=>[entry.rune,i]));
  const firstMatch=group=>{for(let i=0;i+rule.lag<group.length;i++)if(group[i+rule.lag].index===(rule.a*group[i].index+rule.b)%29)return group.slice(i,i+rule.lag+1);return null;};
  for(const page of result.transformed){
   let group=[],position=0,offset=0;
   const draw=span=>{
    const first=span[0],last=span.at(-1),joined=last.offset-first.offset>rule.lag;
    return '<figure class="run-word-example"><figcaption>One matching pair</figcaption><p class="run-word-example-location">'+esc(page.page.toUpperCase())+' · page rune positions '+first.position+' and '+last.position+'</p><div class="run-word-example-strip" style="--pair-columns:'+span.length+'" role="img" aria-label="'+esc('A matching pair '+rule.lag+' rune positions apart. '+span.map((r,i)=>'Position '+(i+1)+': '+r.char+(i===0||i===span.length-1?', highlighted endpoint':'')).join('. '))+'">'+span.map((r,i)=>'<span class="run-word-example-cell'+(i===0||i===span.length-1?' is-endpoint':'')+'" aria-hidden="true"><span class="run-word-example-rune">'+esc(r.char)+'</span><span class="run-word-example-position">'+(i+1)+'</span></span>').join('')+'</div><p class="run-word-example-rule">Strip positions 1 and '+span.length+' are '+rule.lag+' '+(rule.lag===1?'position':'positions')+' apart. '+(rule.a===1&&rule.b===0?'Both highlighted runes are '+esc(first.char)+'.':'In the 0–28 numbering, '+esc(first.char)+' = '+first.index+' and '+esc(last.char)+' = '+last.index+'. The checked rule gives ('+rule.a+' × '+first.index+' + '+rule.b+') mod 29 = '+last.index+'.')+'</p><p class="run-word-example-note">'+(rule.boundaries==='non-rune'?'This span stays inside one uninterrupted run of runes.':joined?'This joined span ignores non-rune separators between the endpoints.':'This span belongs to a sequence bounded only by ASCII hyphens or periods.')+' Positions count runes only. This is a counted relation, not a translation.</p></figure>';
   };
   for(const ch of page.text){
    if(indices.has(ch))group.push({char:ch,index:indices.get(ch),position:++position,offset});
    else if(rule.boundaries==='non-rune'||ch==='-'||ch==='.'){
     const span=firstMatch(group);if(span)return draw(span);group=[];
    }
    offset++;
   }
   const span=firstMatch(group);if(span)return draw(span);
  }
  return '';
 }
 function wordPairChart(task,result){
  const pairs=result.wordPairs,n=BigInt(pairs.expected.numerator),d=BigInt(pairs.expected.denominator),scaled=(n*100n+d/2n)/d;
  const expected=Number(n*1000000n/d)/1000000,average=n>0n&&scaled===0n?'<0.01':(Number(scaled)/100).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}),actual=pairs.matches.toLocaleString('en-US'),total=pairs.opportunities.toLocaleString('en-US'),max=Math.max(1,pairs.matches,expected);
  const boundary=task.criterion.boundaries==='non-rune'?'Every non-rune character ends a word.':'Only ASCII hyphens (-) and periods (.) end a word; other non-rune characters, including line breaks, are joined.';
  const rows=[{label:'Observed matches',value:pairs.matches,text:actual},{label:'Random-order average',value:expected,text:average}];
  return '<figure class="local-run-chart run-word-pair-chart"><figcaption>Matching pairs inside words</figcaption><p class="run-word-pair-total">'+actual+(pairs.matches===1?' match in ':' matches in ')+total+' available pairs</p><div role="img" aria-label="'+esc('Observed matches: '+actual+'. Random-order average: approximately '+average+'. Both compare the same '+total+' available pairs.')+'">'+rows.map((row,i)=>'<div class="run-word-pair-row"><span>'+row.label+'</span><strong>'+esc(row.text)+'</strong><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div></div>').join('')+'</div><p class="run-chart-note">Average across all possible orderings of the same runes within each word. Rounded here to two decimal places.</p><p class="run-chart-note">'+esc(boundary)+'</p><details class="run-pair-arithmetic"><summary>Exact average</summary><p>'+esc(pairs.expected.numerator)+' ÷ '+esc(pairs.expected.denominator)+' matches.</p></details></figure>';
 }
 const SUM_PAGE_SIZE=8,SUM_PREVIEW=12;
 function wordSumCalculation(task,page,index){
  const word=page.words[index];if(!word)return '<p class="run-sum-empty">No rune words were measured on this page.</p>';
  const runes=Array.from(word.runes),shown=runes.slice(0,SUM_PREVIEW),indices=new Map(task.alphabet.map((v,i)=>[v.rune,i])),long=runes.length>SUM_PREVIEW;
  return '<section class="run-sum-calculation"><h3>Word '+(index+1)+' · '+esc(page.page.toUpperCase())+'</h3><p class="run-sum-calculation-note">'+(long?'Showing the first '+SUM_PREVIEW+' of '+runes.length+' runes. The full sum includes all '+runes.length+'.':'Add the assigned prime value of each rune.')+'</p><ol class="run-sum-terms" aria-label="Assigned prime value for each displayed rune">'+shown.map(rune=>{const i=indices.get(rune),prime=task.alphabet[task.criterion.table==='reversed'?28-i:i].prime;return '<li><span class="run-sum-rune">'+esc(rune)+'</span><span class="run-sum-prime">'+prime+'</span></li>';}).join('')+'</ol><p class="run-sum-total">'+(long?'Full word sum':'Word sum')+': <strong>'+word.sum.toLocaleString('en-US')+'</strong></p></section>';
 }
 function wordSumRows(page,batch,selected){
  const start=batch*SUM_PAGE_SIZE,rows=page.words.slice(start,start+SUM_PAGE_SIZE);
  if(!rows.length)return '';
  return '<table class="run-sum-table"><thead><tr><th scope="col">Word</th><th scope="col">Sum</th></tr></thead><tbody>'+rows.map((word,offset)=>{const i=start+offset,runes=Array.from(word.runes),long=runes.length>SUM_PREVIEW,preview=runes.slice(0,SUM_PREVIEW).join('');return '<tr><td><button type="button" data-run-sum-word="'+i+'" aria-pressed="'+(i===selected)+'" aria-label="Inspect word '+(i+1)+' on '+esc(page.page.toUpperCase())+', '+runes.length+' runes"><span class="run-sum-word-number">'+(i+1)+'</span><span class="run-sum-word">'+esc(preview)+(long?'…':'')+'</span>'+(long?'<span class="run-sum-word-length">'+runes.length+' runes</span>':'')+'</button></td><td>'+word.sum.toLocaleString('en-US')+'</td></tr>';}).join('')+'</tbody></table>';
 }
 function wordSumsView(task,result){
  const page=result.wordSums.pages[0],boundary=task.criterion.boundaries==='non-rune'?'Every non-rune character separates words.':'Only ASCII hyphens (-) and periods (.) separate groups. Other non-rune characters, including spaces and line breaks, are joined.';
  return '<section class="run-word-sums" data-run-word-sums aria-label="Measured word sums"><p class="run-sum-table-choice"><strong>'+(task.criterion.table==='reversed'?'Reversed':'Canonical')+' prime assignments</strong></p><p class="run-sum-boundary">'+esc(boundary)+'</p><div class="run-sum-controls">'+(result.wordSums.pages.length>1?'<label>Page<select data-run-sum-page aria-label="Measured page">'+result.wordSums.pages.map(p=>'<option value="'+esc(p.page)+'">'+esc(p.page.toUpperCase())+'</option>').join('')+'</select></label>':'<p>'+esc(page.page.toUpperCase())+'</p>')+'</div><div data-run-sum-calculation>'+wordSumCalculation(task,page,0)+'</div><h3>Word totals</h3><p class="run-sum-instruction">Select a word to see its calculation.</p><div data-run-sum-list>'+wordSumRows(page,0,0)+'</div><div class="run-sum-pagination"><button type="button" data-run-sum-prev disabled>Previous</button><p data-run-sum-range role="status">'+(page.words.length?'Words 1–'+Math.min(SUM_PAGE_SIZE,page.words.length)+' of '+page.words.length:'0 words')+' · '+esc(page.page.toUpperCase())+'</p><button type="button" data-run-sum-next'+(page.words.length<=SUM_PAGE_SIZE?' disabled':'')+'>Next</button></div></section>';
 }
 function bindWordSums(host,task,result,initialPage){
  const panel=host.querySelector?.('[data-run-word-sums]');if(!panel)return ()=>{};
  const select=panel.querySelector('[data-run-sum-page]'),calculation=panel.querySelector('[data-run-sum-calculation]'),list=panel.querySelector('[data-run-sum-list]'),range=panel.querySelector('[data-run-sum-range]'),prev=panel.querySelector('[data-run-sum-prev]'),next=panel.querySelector('[data-run-sum-next]');
  if(!calculation||!list||!range||!prev||!next)return ()=>{};
  let page=result.wordSums.pages[0],batch=0,selected=0;const listeners=[];
  const update=()=>{const start=batch*SUM_PAGE_SIZE;calculation.innerHTML=wordSumCalculation(task,page,selected);list.innerHTML=wordSumRows(page,batch,selected);range.textContent=(page.words.length?'Words '+(start+1)+'–'+Math.min(start+SUM_PAGE_SIZE,page.words.length)+' of '+page.words.length:'0 words')+' · '+page.page.toUpperCase();prev.disabled=batch===0;next.disabled=(batch+1)*SUM_PAGE_SIZE>=page.words.length;};
  const listen=(node,event,fn)=>{node.addEventListener(event,fn);listeners.push(()=>node.removeEventListener?.(event,fn));};
  if(select)listen(select,'change',()=>{const chosen=result.wordSums.pages.find(p=>p.page===select.value);if(!chosen){select.value=page.page;return;}page=chosen;batch=selected=0;update();});
  listen(prev,'click',()=>{if(batch>0){batch--;selected=batch*SUM_PAGE_SIZE;update();}});
  listen(next,'click',()=>{if((batch+1)*SUM_PAGE_SIZE<page.words.length){batch++;selected=batch*SUM_PAGE_SIZE;update();}});
  listen(list,'click',event=>{const button=event.target?.closest?.('[data-run-sum-word]');if(!button||!list.contains(button)||!/^\d+$/.test(button.dataset.runSumWord||''))return;const i=Number(button.dataset.runSumWord);if(i<batch*SUM_PAGE_SIZE||i>=Math.min((batch+1)*SUM_PAGE_SIZE,page.words.length))return;selected=i;calculation.innerHTML=wordSumCalculation(task,page,selected);list.querySelectorAll('[data-run-sum-word]').forEach(node=>node.setAttribute('aria-pressed',String(Number(node.dataset.runSumWord)===selected)));});
  if(initialPage){const chosen=result.wordSums.pages.find(p=>p.page===initialPage);if(chosen){page=chosen;if(select)select.value=initialPage;}}
  update();return ()=>listeners.forEach(remove=>remove());
 }
 function inspector(task,result){
  const first=task.pages[0],after=result.transformed.find(page=>page.page===first.id),single=['word-affine-count','word-prime-sums'].includes(task.criterion.kind)&&!task.steps.length;
  return '<details class="run-text-inspector"><summary>Inspect the text</summary><div class="run-text-controls">'+
   (task.pages.length>1?'<label class="run-text-page">Page<select data-run-text-page aria-label="Text page">'+task.pages.map(page=>'<option value="'+esc(page.id)+'">'+esc(page.id.toUpperCase())+'</option>').join('')+'</select></label>':'<p class="run-text-single">'+esc(first.id.toUpperCase())+'</p>')+
   '<div class="run-text-modes" role="group" aria-label="Text representation"><button type="button" data-run-text-mode="runes" aria-pressed="true">Runes</button><button type="button" data-run-text-mode="latin" aria-pressed="false">Transliteration</button></div></div>'+
   '<p class="run-text-note">Transliteration shows rune labels, not a translation. A middle dot (·) separates adjacent labels; original spaces, punctuation and line breaks remain.</p>'+
   (task.criterion.kind==='exact-prefix'?'<div data-run-prefix>'+prefixAlignment(task,result,first.id)+'</div>':'')+
   '<div class="run-text-columns'+(single?' run-text-columns-single':'')+'"><section><h3>'+(single?'Text measured':'Original')+'</h3><pre class="run-text-value" data-run-original>'+esc(first.text)+'</pre></section>'+(single?'':'<section><h3>After the method</h3><pre class="run-text-value" data-run-after>'+esc(after.text)+'</pre></section>')+'</div></details>';
 }
 function bind(host,task,result,options={}){
  E.summary(task,result);return bindOutput(host,task,result,options);
 }
 function bindOutput(host,task,result,options={}){
  bindings.get(host)?.();
  const snapshot=JSON.parse(JSON.stringify({task,result})),initialPage=options.pageId===undefined?snapshot.task.pages[0].id:options.pageId;if(!snapshot.task.pages.some(p=>p.id===initialPage))throw Error('Choose a page in the original output.');
  const sumsCleanup=task.criterion.kind==='exact-prefix-set'?bindOpeningSet(host,snapshot.task,snapshot.result,initialPage):task.criterion.kind==='word-prime-sums'?bindWordSums(host,snapshot.task,snapshot.result,initialPage):task.criterion.kind==='language-score'?bindLanguage(host,snapshot.task,snapshot.result,initialPage):task.criterion.kind==='measurement'&&task.steps.length?bindOutputPreview(host,snapshot.task,snapshot.result,initialPage):()=>{};
  const panel=host.querySelector?.('.run-text-inspector');if(!panel){bindings.set(host,sumsCleanup);return sumsCleanup;}
  const select=panel.querySelector('[data-run-text-page]'),buttons=[...panel.querySelectorAll('[data-run-text-mode]')];
  const original=panel.querySelector('[data-run-original]'),after=panel.querySelector('[data-run-after]');
  if(!original||!after&&!(['word-affine-count','word-prime-sums'].includes(task.criterion.kind)&&!task.steps.length)){bindings.set(host,sumsCleanup);return sumsCleanup;}
  let pageId=initialPage,mode='runes';if(select)select.value=pageId;const listeners=[];
  const update=()=>{
   const page=snapshot.task.pages.find(p=>p.id===pageId),output=snapshot.result.transformed.find(p=>p.page===pageId);
   original.textContent=mode==='latin'?transliteration(page.text,snapshot.task.alphabet):page.text;
   if(after)after.textContent=mode==='latin'?transliteration(output.text,snapshot.task.alphabet):output.text;
   const prefix=panel.querySelector('[data-run-prefix]');if(prefix)prefix.innerHTML=prefixAlignment(snapshot.task,snapshot.result,pageId,mode);
   panel.dataset.textMode=mode;
   buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.getAttribute('data-run-text-mode')===mode)));
  };
  const listen=(node,event,fn)=>{node.addEventListener(event,fn);listeners.push(()=>node.removeEventListener?.(event,fn));};
  if(select)listen(select,'change',()=>{if(snapshot.task.pages.some(p=>p.id===select.value)){pageId=select.value;update();}});
  const selectors=['[data-finite-output-page]','[data-run-opening-set-page]','[data-run-language-page]','[data-run-output-page]','[data-run-sum-page]'],primary=selectors.map(selector=>host.querySelector?.(selector)).find(Boolean)||select;
  if(primary){
   primary.value=initialPage;
   for(const candidate of [...selectors.slice(1).map(selector=>host.querySelector?.(selector)),select])if(candidate&&candidate!==primary){const label=candidate.closest?.('label');if(label)label.hidden=true;}
   if(primary!==select)listen(primary,'change',()=>{if(snapshot.task.pages.some(p=>p.id===primary.value)){pageId=primary.value;if(select)select.value=pageId;update();}});
  }
  buttons.forEach(button=>listen(button,'click',()=>{const chosen=button.getAttribute('data-run-text-mode');if(['runes','latin'].includes(chosen)){mode=chosen;update();}}));
  update();const cleanup=()=>{listeners.forEach(remove=>remove());sumsCleanup();};bindings.set(host,cleanup);return cleanup;
 }
 function render(task,result){
  const data=E.summary(task,result),max=Math.max(1,...(data.comparison||[]).map(r=>r.value));
  if(task.criterion.kind==='exact-prefix-set')return openingSetView(task,result);
  if(task.criterion.kind==='language-score')return '<section class="local-run-result" aria-labelledby="local-run-finding"><h2 id="local-run-finding">Output</h2>'+languageView(task,result)+'<dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
  if(task.criterion.kind==='measurement'&&task.steps.length)return '<section class="local-run-result" aria-labelledby="local-run-finding">'+outputPreview(task,result)+'<dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'<details><summary>Rune counts</summary><p>Computation verified. '+esc(data.finding)+'</p><ul>'+data.comparison.map(row=>'<li>'+esc(row.label+': '+row.value+' of '+row.total+' pairs')+'</li>').join('')+'</ul><p>'+esc(data.limit)+'</p></details></section>';
  return '<section class="local-run-result" aria-labelledby="local-run-finding"><p class="run-state">Computation verified</p><h2 id="local-run-finding">What this run found</h2><p>'+esc(data.finding)+'</p>'+
   (task.criterion.kind==='exact-prefix'?prefixMismatch(task,result):'')+(task.criterion.kind==='word-prime-sums'?wordSumsView(task,result):task.criterion.kind==='word-affine-count'?wordPairChart(task,result):task.criterion.kind==='exact-prefix'?prefixChart(task,result):'<figure class="local-run-chart"><figcaption>Repeated neighbouring runes</figcaption><div role="img" aria-label="'+esc(data.comparison.map(r=>r.label+': '+r.value+' of '+r.total+' pairs').join('. '))+'">'+
   data.comparison.map((row,i)=>'<div class="run-bar-row"><span>'+esc(row.label)+'</span><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div><strong>'+row.value+'</strong></div>').join('')+
   '</div><p class="run-chart-note">Counts follow the rune sequence on each page, ignoring spaces and punctuation.</p></figure>')+
   (task.criterion.kind==='word-affine-count'?wordPairExample(task,result):'')+'<p class="run-limit">'+esc(data.limit)+'</p><dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
 }
 function archivedModel(model){
  const client=typeof module==='object'&&module.exports?require('./published-output-client.js'):root.PublishedOutputClient;
  if(!client?.isVerified?.(model))throw Error('Load an authenticated archived calculation before display.');
  return model;
 }
 function renderArchived(model){
  const {task,run}=archivedModel(model),result=run.result;
  if(task.criterion.kind==='exact-prefix-set')return openingSetView(task,result);
  if(task.criterion.kind==='exact-prefix')return '<section class="local-run-result"><h2>What this check found</h2><p>'+result.matches.filter(page=>page.matched).length+' of '+task.pages.length+' pages begin with the supplied rune sequence.</p>'+prefixMismatch(task,result)+prefixChart(task,result)+'<p class="run-limit">A matching opening alone does not establish a decryption.</p>'+inspector(task,result)+'</section>';
  if(task.criterion.kind==='word-affine-count')return '<section class="local-run-result"><h2>Matches inside words</h2><p>'+result.wordPairs.matches+' matches among '+result.wordPairs.opportunities.toLocaleString('en-US')+' pairs '+task.criterion.lag+' rune positions apart inside words.</p>'+wordPairChart(task,result)+wordPairExample(task,result)+'<p class="run-limit">The comparison describes this rule and these word boundaries. It does not identify an encryption method.</p>'+inspector(task,result)+'</section>';
  if(task.criterion.kind==='measurement'&&!task.steps.length)return '<section class="local-run-result"><h2>Repeated neighbouring runes</h2><p>'+result.metrics.equalAdjacentPairs+' repeated pairs among '+result.metrics.adjacentPairs.toLocaleString('en-US')+' neighbouring rune pairs.</p><p class="run-limit">These counts describe the archived text. They do not identify a cipher.</p>'+inspector(task,result)+'</section>';
  throw Error('This archived calculation has no supported output view.');
 }
 function bindArchived(host,model,options={}){const {task,run}=archivedModel(model);return bindOutput(host,task,run.result,options);}
 function renderPrefixComparison(task,result,criterion,pageId){
  E.summary(task,result);
  if(criterion?.kind!=='exact-prefix'||!Array.isArray(criterion.values)||criterion.values.length<1||criterion.values.length>256||criterion.values.some(v=>!Number.isInteger(v)||v<0||v>28)||!task.pages.some(p=>p.id===pageId)||!result.transformed.some(p=>p.page===pageId))throw Error('Use an explicit opening and an original output page.');
  return prefixAlignment(task,result,pageId,'runes',criterion.values);
 }
 async function prepareLanguageComparison(task,result,criterion,pageId,crypto=root.crypto){
  const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,S=node?require('./language-score.js'):root.RuneLanguageScore;
  const captured=J.capture({task,result,criterion,pageId},{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});S.validateCriterion(captured.criterion);
  if(!captured.task.pages?.some(page=>page.id===captured.pageId))throw Error('Choose an original output page.');
  const verified=await E.verify(captured.task,captured.result,crypto),output=verified.transformed.find(page=>page.page===captured.pageId);if(!output)throw Error('The original output page is missing.');
  const indices=new Map(captured.task.alphabet.map((entry,i)=>[entry.rune,i])),values=Array.from(output.text).filter(ch=>indices.has(ch)).map(ch=>indices.get(ch)),comparison=S.evaluate(values),descriptor=languageDescriptor({criterion:captured.criterion}),token=Object.freeze({});
  languageComparisons.set(token,{task:captured.task,result:verified,pageId:captured.pageId,comparison,descriptor});return token;
 }
 function renderLanguageComparison(token){
  const value=languageComparisons.get(token);if(!value)throw Error('Prepare the original verified output comparison before displaying it.');
  return '<section class="run-language">'+languagePage(value.task,value.result,value.pageId,value.comparison)+'<section class="run-language-next"><h3>What to check next</h3><p>'+esc(value.descriptor.next)+'</p><p>'+esc(value.descriptor.limit)+'</p></section></section>';
 }
 function criterionLabel(criterion){return ({measurement:'Rune measurements','exact-prefix':'Exact opening','exact-prefix-set':'Supplied opening comparison','word-affine-count':'Word pair counts','word-prime-sums':'Word prime sums','language-score':'Language reference comparison'})[criterion?.kind]||'Original check';}
 async function prepareInspectionOutput(task,result,pageId,crypto=root.crypto){
  const J=typeof module==='object'&&module.exports?require('./finite-json.js'):root.FiniteJSON,captured=J.capture({task,result,pageId},{maxBytes:8*1024*1024,maxDepth:24,maxNodes:500000});
  if(!captured.task.pages?.some(page=>page.id===captured.pageId))throw Error('Choose an original output page.');
  const verified=await E.verify(captured.task,captured.result,crypto),page=verified.transformed.find(page=>page.page===captured.pageId);if(!page)throw Error('The original output page is missing.');
  const token=Object.freeze({});inspectionOutputs.set(token,{example:finiteShiftExample(captured.task,verified,captured.pageId),text:page.text,pageId:captured.pageId,hasRunes:Array.from(page.text).some(ch=>captured.task.alphabet.some(entry=>entry.rune===ch))});return token;
 }
 function renderInspectionOutput(token){
  const value=inspectionOutputs.get(token);if(!value)throw Error('Verify the original output before displaying it.');
  return '<section class="run-output-inspection">'+value.example+'<h3>Transformed text · '+esc(value.pageId.toUpperCase())+'</h3><p>'+ (value.hasRunes?'Exact rune text after the declared method.':'This output contains no runes. Its exact punctuation and spacing are shown below.')+' This does not decide readability or a decryption.</p><pre class="run-language-excerpt" data-inspection-rune-text>'+esc(value.text)+'</pre></section>';
 }
 const measurementComparisons=new WeakMap();
 function measurementData(token){const value=measurementComparisons.get(token);if(!value)throw Error('Use independently verified saved measurements.');return value;}
 async function prepareMeasurementComparison(value,crypto=root.crypto){
  const node=typeof module==='object'&&module.exports,J=node?require('./finite-json.js'):root.FiniteJSON,R=node?require('./computation-evidence.js'):root.ComputationEvidence,Q=node?require('./question-evidence.js'):root.QuestionEvidence;
  const captured=J.capture(value,{maxBytes:16*1024*1024,maxDepth:24,maxNodes:1000000});
  if(!captured||Object.keys(captured).length!==3||!['task','inputVersion','sources'].every(key=>Object.hasOwn(captured,key))||!['measurement','word-affine-count','word-prime-sums','language-score'].includes(captured.task?.criterion?.kind)||!Array.isArray(captured.sources)||captured.sources.length>75)throw Error('Use bounded original saved measurements for this exact question.');
  const comparison=await R.compare(captured.task,captured.inputVersion,captured.sources,crypto),verified=new Map();
  // Verify whole original receipts, including pages outside the requested subset.
  for(const source of captured.sources){const result=await E.verify(source.task,source.run.result,crypto);verified.set(source.task.taskId,{...source,run:{...source.run,result}});}
  const witnesses=new Map();for(const ref of comparison.evidence)for(const id of ref.pages)if(!witnesses.has(id))witnesses.set(id,verified.get(ref.taskId));
  const pages=captured.task.pages.filter(page=>witnesses.has(page.id)),task={...captured.task,pages},outputs=pages.map(page=>witnesses.get(page.id).run.result.transformed.find(row=>row.page===page.id));
  const data={task,coveredPages:comparison.coveredPages,remainingPages:comparison.remainingPages,declaredCount:captured.task.pages.length,outputs,runes:outputs.reduce((total,page)=>total+Array.from(page.text).filter(ch=>captured.task.alphabet.some(entry=>entry.rune===ch)).length,0)};
  if(captured.task.criterion.kind==='word-affine-count')data.wordPairs=(await Q.summarize(captured.task,captured.inputVersion,captured.sources,crypto)).wordPairs;
  if(captured.task.criterion.kind==='word-prime-sums'){
   const sums=pages.map(page=>witnesses.get(page.id).run.result.wordSums.pages.find(row=>row.page===page.id));data.wordSums={pages:sums,words:sums.reduce((n,page)=>n+page.words.length,0),total:sums.reduce((n,page)=>n+page.words.reduce((m,word)=>m+word.sum,0),0)};
  }
  if(captured.task.criterion.kind==='language-score')data.languageScore={modelId:captured.task.criterion.modelId,modelSha256:captured.task.criterion.modelSha256,pages:pages.map(page=>verified.get(witnesses.get(page.id).task.taskId).run.result.languageScore.pages.find(row=>row.page===page.id))};
  const token=Object.freeze({});measurementComparisons.set(token,data);return token;
 }
 function renderMeasurementComparison(token){
  const data=measurementData(token),{task}=data,partial=data.remainingPages.length>0,scope='<p class="run-text-note">'+data.coveredPages.length+' of '+data.declaredCount+' declared pages. '+(partial?'These values describe covered pages only.':'All declared pages have saved calculations.')+'</p>';
  if(!data.coveredPages.length)return '<section class="measurement-comparison"><p>No saved calculations for these exact settings.</p></section>';
  let body;
  if(task.criterion.kind==='word-affine-count')body='<h3>Saved within-word pair counts</h3>'+wordPairChart(task,{wordPairs:data.wordPairs})+'<p class="run-limit">This is an exact rearrangement average, not a significance test or evidence of a decipherment.</p>';
  else if(task.criterion.kind==='word-prime-sums')body='<h3>Saved word totals</h3><p>'+data.wordSums.words.toLocaleString('en-US')+' measured words; combined total '+data.wordSums.total.toLocaleString('en-US')+'.</p>'+wordSumsView(task,{wordSums:data.wordSums})+'<p class="run-limit">These totals do not decode the text or establish that a pattern is meaningful.</p>';
  else if(task.criterion.kind==='language-score')body='<h3>Saved language comparisons</h3>'+languageView(task,{transformed:data.outputs,languageScore:data.languageScore});
  else body=outputPreview(task,{transformed:data.outputs})+'<p>'+data.runes.toLocaleString('en-US')+' runes in the saved output.</p>';
  return '<section class="measurement-comparison">'+scope+body+'</section>';
 }
 function bindMeasurementComparison(host,token){const data=measurementData(token);if(!data.coveredPages.length)return ()=>{};return data.task.criterion.kind==='word-prime-sums'?bindWordSums(host,data.task,{wordSums:data.wordSums}):data.task.criterion.kind==='language-score'?bindLanguage(host,data.task,{transformed:data.outputs,languageScore:data.languageScore}):data.task.criterion.kind==='measurement'?bindOutputPreview(host,data.task,{transformed:data.outputs}):()=>{};}
 // Workflow copy describes confirmed calculation state, never scientific support.
 function actionCopy({stage,preparedSource=false}={}){
  if(stage==='ready'&&preparedSource===true)return 'This check is ready to run on this device. No settings to choose. Save the result afterward to add it to the shared research.';
  if(stage==='local')return 'Finished on this device. Save to add this calculation to the shared research.';
  if(stage==='saved')return 'Saved to this research entry.';
  return '';
 }
 function continuationHTML({verified=false,unsaved=false,hasNext=false}={}){
  if(verified!==true||unsaved!==false||hasNext!==false)return '';
  return '<p class="research-continuation"><a href="research.html?contribute=1">Find another check <span aria-hidden="true">→</span></a></p>';
 }
 const api={actionCopy,continuationHTML,prepareMeasurementComparison,renderMeasurementComparison,bindMeasurementComparison,renderArchived,bindArchived,render,bind,pageLabel,criterionLabel,prepareInspectionOutput,renderInspectionOutput,renderPrefixComparison,prepareLanguageComparison,renderLanguageComparison};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
