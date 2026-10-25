/* Shared result view. All conclusions and chart values come from replayed data. */
(function(root){
 'use strict';
 const E=typeof module==='object'&&module.exports?require('./local-experiment.js'):root.LocalExperiment;
 const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const bindings=new WeakMap();
 const LANGUAGE_REFERENCES=[['eng_Latn','English'],['cym_Latn','Welsh'],['deu_Latn','German'],['fra_Latn','French'],['spa_Latn','Spanish'],['ita_Latn','Italian'],['por_Latn','Portuguese'],['fin_Latn','Finnish']];
 function languageDescriptor(task){
  const registry=typeof module==='object'&&module.exports?require('./output-evaluators.js'):root.OutputEvaluators;
  const descriptor=registry?.describe(task.criterion);if(!descriptor)throw Error('The language comparison is not supported by this view.');return descriptor;
 }
 function languagePage(task,result,id){
  const page=result.languageScore.pages.find(p=>p.page===id),output=result.transformed.find(p=>p.page===id),characters=Array.from(output.text),excerpt=characters.slice(0,120).join('');
  const introduction='<h3>After the method · '+esc(id.toUpperCase())+'</h3><p class="run-text-note">Rune labels, not a translation.'+(characters.length>120?' First 120 characters; inspect the complete text below.':'')+'</p><pre class="run-language-excerpt">'+esc(transliteration(excerpt,task.alphabet,true))+(characters.length>120?'…':'')+'</pre>';
  if(page.status==='insufficient')return introduction+'<h3>Too little text to compare</h3><p>This page has '+page.runes+' runes. This comparison needs at least 40. No language scores were calculated.</p><p>Inspect the output directly, or separately review a longer passage to check.</p>';
  return introduction+'<h3>Compared with rearranged text</h3><p>For each reference, the bar counts how many of 32 rearrangements scored at least as high as this output. Every rearrangement keeps the same runes and length.</p><p class="run-language-caution"><strong>A short bar is not evidence of readable text.</strong> Unreadable outputs can also score above all 32 rearrangements. These rows do not identify the language.</p><ul class="run-language-comparisons" aria-label="Language reference comparisons">'+LANGUAGE_REFERENCES.map(([id,label])=>{const model=page.models.find(m=>m.id===id);if(!model)throw Error('A language reference is missing.');return '<li><div class="run-language-row"><span>'+label+'</span><span>'+model.shuffledAtOrAbove+' of 32</span></div><div class="run-language-track" role="img" aria-label="'+label+': '+model.shuffledAtOrAbove+' of 32 rearrangements scored at least as high as the output"><span style="width:'+(model.shuffledAtOrAbove/32*100)+'%"></span></div></li>';}).join('')+'</ul><p class="run-text-note">References stay in a fixed order. Each compares groups of three runes after the same spelling conversion. Counts describe these 32 rearrangements, not confidence in a language.</p><details class="run-language-values"><summary>Exact comparison values</summary><div class="run-language-table-wrap"><table><thead><tr><th>Reference</th><th>Output score</th><th>Rearranged range</th></tr></thead><tbody>'+LANGUAGE_REFERENCES.map(([id,label])=>{const model=page.models.find(m=>m.id===id);return '<tr><th scope="row">'+label+'</th><td>'+model.total+'</td><td>'+model.shuffledMin+' to '+model.shuffledMax+'</td></tr>';}).join('')+'</tbody></table></div><p class="run-text-note">Scores are model-specific integer totals. Compare each output with its own rearrangements, not raw scores across languages.</p></details>';
 }
 function languageView(task,result){
  const descriptor=languageDescriptor(task),first=task.pages[0].id;
  return '<section class="run-language" data-run-language>'+ (task.pages.length>1?'<label class="run-language-page">Page<select data-run-language-page>'+task.pages.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.id.toUpperCase())+'</option>').join('')+'</select></label>':'')+'<div data-run-language-content>'+languagePage(task,result,first)+'</div><section class="run-language-next"><h3>What to check next</h3><p>'+esc(descriptor.next)+'</p><p>'+esc(descriptor.limit)+'</p></section></section>';
 }
 function bindLanguage(host,task,result){
  const panel=host.querySelector?.('[data-run-language]'),select=panel?.querySelector('[data-run-language-page]'),content=panel?.querySelector('[data-run-language-content]');
  if(!select||!content)return ()=>{};
  const change=()=>{if(task.pages.some(p=>p.id===select.value))content.innerHTML=languagePage(task,result,select.value);};
  select.addEventListener('change',change);return ()=>select.removeEventListener?.('change',change);
 }
 function outputExcerpt(task,result,id){
  const output=result.transformed.find(page=>page.page===id),chars=Array.from(output.text),excerpt=chars.slice(0,120).join('');
  return '<p class="run-text-note">'+esc(id.toUpperCase())+(chars.length>120?' · First 120 characters':'')+'</p><pre class="run-language-excerpt">'+esc(transliteration(excerpt,task.alphabet,true))+(chars.length>120?'…':'')+'</pre>';
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
 function prefixAlignment(task,result,pageId,mode='runes',expected=task.criterion.values){
  const indices=new Map(task.alphabet.map((entry,i)=>[entry.rune,i])),text=result.transformed.find(page=>page.page===pageId).text,observed=Array.from(text).filter(rune=>indices.has(rune)).map(rune=>indices.get(rune));
  const mismatch=expected.findIndex((value,i)=>observed[i]!==value),start=mismatch<0?0:Math.max(0,mismatch-3),end=Math.min(expected.length,start+8),label=value=>value===undefined?'Missing':mode==='latin'?task.alphabet[value].latin:task.alphabet[value].rune;
  const status=mismatch<0?'All '+expected.length+' prefix positions match.':observed[mismatch]===undefined?'The output ends before prefix position '+(mismatch+1)+'.':'First mismatch at prefix position '+(mismatch+1)+'.';
  return '<section class="run-prefix-alignment"><h3>Expected and observed prefix</h3><p class="run-prefix-status">'+esc(pageId.toUpperCase()+': '+status)+'</p><p class="run-text-note">'+'Showing positions '+(start+1)+'–'+end+' of '+expected.length+'. '+'Positions count runes only; separators do not occupy a position.</p><table class="run-prefix-table"><thead><tr><th scope="col">Position</th><th scope="col">Expected</th><th scope="col">Actual</th><th scope="col">Result</th></tr></thead><tbody>'+expected.slice(start,end).map((value,offset)=>{const i=start+offset,missing=observed[i]===undefined,same=value===observed[i];return '<tr class="run-prefix-pair'+(same?'':' is-different')+'"><th scope="row">'+(i+1)+'</th><td class="run-prefix-symbol">'+esc(label(value))+'</td><td'+(missing?'':' class="run-prefix-symbol"')+'>'+esc(label(observed[i]))+'</td><td>'+(same?'Match':missing?'Missing':'Different')+'</td></tr>';}).join('')+'</tbody></table></section>';
 }
 function prefixChart(task,result){
  const matched=result.matches.filter(row=>row.matched).length,total=task.pages.length,notMatched=total-matched;
  return '<figure class="local-run-chart run-prefix-chart"><figcaption>Exact starting-sequence check</figcaption><div class="run-prefix-total" role="img" aria-label="'+matched+' of '+total+' pages matched all '+task.criterion.values.length+' prefix positions; '+notMatched+' did not match."><span class="run-prefix-match" style="width:'+(100*matched/total).toFixed(4)+'%"></span><span class="run-prefix-other" style="width:'+(100*notMatched/total).toFixed(4)+'%"></span></div><dl class="run-prefix-counts"><div><dt>Matched every position</dt><dd>'+matched+' of '+total+' pages</dd></div><div><dt>Did not match</dt><dd>'+notMatched+' of '+total+' pages</dd></div></dl><p class="run-chart-note">The fixed prefix has '+task.criterion.values.length+' rune positions.</p></figure>';
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
 function bindWordSums(host,task,result){
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
  bindings.get(host)?.();
  E.summary(task,result);const snapshot=JSON.parse(JSON.stringify({task,result})),initialPage=options.pageId===undefined?snapshot.task.pages[0].id:options.pageId;if(!snapshot.task.pages.some(p=>p.id===initialPage))throw Error('Choose a page in the original output.');
  const sumsCleanup=task.criterion.kind==='word-prime-sums'?bindWordSums(host,snapshot.task,snapshot.result):task.criterion.kind==='language-score'?bindLanguage(host,snapshot.task,snapshot.result):task.criterion.kind==='measurement'&&task.steps.length?bindOutputPreview(host,snapshot.task,snapshot.result,initialPage):()=>{};
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
  buttons.forEach(button=>listen(button,'click',()=>{const chosen=button.getAttribute('data-run-text-mode');if(['runes','latin'].includes(chosen)){mode=chosen;update();}}));
  update();const cleanup=()=>{listeners.forEach(remove=>remove());sumsCleanup();};bindings.set(host,cleanup);return cleanup;
 }
 function render(task,result){
  const data=E.summary(task,result),max=Math.max(1,...(data.comparison||[]).map(r=>r.value));
  if(task.criterion.kind==='language-score')return '<section class="local-run-result" aria-labelledby="local-run-finding"><h2 id="local-run-finding">Output</h2>'+languageView(task,result)+'<dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
  if(task.criterion.kind==='measurement'&&task.steps.length)return '<section class="local-run-result" aria-labelledby="local-run-finding">'+outputPreview(task,result)+'<dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'<details><summary>Rune counts</summary><p>Computation verified. '+esc(data.finding)+'</p><ul>'+data.comparison.map(row=>'<li>'+esc(row.label+': '+row.value+' of '+row.total+' pairs')+'</li>').join('')+'</ul><p>'+esc(data.limit)+'</p></details></section>';
  return '<section class="local-run-result" aria-labelledby="local-run-finding"><p class="run-state">Computation verified</p><h2 id="local-run-finding">What this run found</h2><p>'+esc(data.finding)+'</p>'+
   (task.criterion.kind==='word-prime-sums'?wordSumsView(task,result):task.criterion.kind==='word-affine-count'?wordPairChart(task,result):task.criterion.kind==='exact-prefix'?prefixChart(task,result):'<figure class="local-run-chart"><figcaption>Repeated neighbouring runes</figcaption><div role="img" aria-label="'+esc(data.comparison.map(r=>r.label+': '+r.value+' of '+r.total+' pairs').join('. '))+'">'+
   data.comparison.map((row,i)=>'<div class="run-bar-row"><span>'+esc(row.label)+'</span><div class="run-bar-track"><span class="run-bar run-bar-'+i+'" style="width:'+(row.value/max*100).toFixed(4)+'%"></span></div><strong>'+row.value+'</strong></div>').join('')+
   '</div><p class="run-chart-note">Counts follow the rune sequence on each page, ignoring spaces and punctuation.</p></figure>')+
   (task.criterion.kind==='word-affine-count'?wordPairExample(task,result):'')+'<p class="run-limit">'+esc(data.limit)+'</p><dl class="run-scope"><div><dt>Pages</dt><dd>'+esc(pageLabel(task.pages))+'</dd></div><div><dt>Runes checked</dt><dd>'+result.metrics.runes.toLocaleString('en-US')+'</dd></div></dl>'+inspector(task,result)+'</section>';
 }
 function renderPrefixComparison(task,result,criterion,pageId){
  if(criterion?.kind!=='exact-prefix'||!Array.isArray(criterion.values)||criterion.values.length<1||criterion.values.length>256||criterion.values.some(v=>!Number.isInteger(v)||v<0||v>28)||!task.pages.some(p=>p.id===pageId)||!result.transformed.some(p=>p.page===pageId))throw Error('Use an explicit opening and an original output page.');
  return prefixAlignment(task,result,pageId,'runes',criterion.values);
 }
 const api={render,bind,pageLabel,renderPrefixComparison};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalRunView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
