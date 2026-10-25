/* Presentation only: callers supply an independently verified finite-search summary. */
(function(root){
 'use strict';
 const mounts=new WeakMap(),esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const text=(v,max)=>typeof v==='string'&&v.trim().length>0&&v.length<=max;
 function href(v){if(!text(v,2000)||/[\u0000-\u0020\\]/.test(v))return false;try{const u=new URL(v,'https://jelliottdev.github.io/');return u.protocol==='https:'&&!u.username&&!u.password&&(v.startsWith('https://')||u.origin==='https://jelliottdev.github.io'&&!v.startsWith('//'));}catch{return false;}}
 function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
 function validate(value){
  if(!value||typeof value!=='object'||Array.isArray(value))throw Error('A finite-search summary is required.');
  const keys=['method','programCount','pageIds','check','coveredCases','totalCases','remainingCases','lookupComplete','answer','finding','limit','sourceLinks'];
  if(Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k)))throw Error('The finite-search summary is incomplete.');
  for(const k of ['method','check','finding','limit'])if(!text(value[k],k==='method'?300:1200))throw Error('Invalid '+k+'.');
  if(!Array.isArray(value.pageIds)||!value.pageIds.length||value.pageIds.length>75||value.pageIds.some(p=>!/^lp[12]-\d{2}$/.test(p))||new Set(value.pageIds).size!==value.pageIds.length)throw Error('Invalid page scope.');
  for(const k of ['programCount','coveredCases','totalCases','remainingCases'])if(!Number.isSafeInteger(value[k])||value[k]<(k==='programCount'||k==='totalCases'?1:0))throw Error('Invalid search count.');
  if(value.totalCases!==value.programCount*value.pageIds.length||value.coveredCases+value.remainingCases!==value.totalCases||typeof value.lookupComplete!=='boolean'||![null,'found','not-found'].includes(value.answer))throw Error('Inconsistent search scope.');
  if(value.answer==='not-found'&&value.remainingCases!==0||value.answer==='found'&&value.coveredCases===0||value.answer===null&&value.remainingCases===0)throw Error('The answer does not match the checked scope.');
  if(!Array.isArray(value.sourceLinks)||value.sourceLinks.length>75||value.sourceLinks.some(s=>!s||Object.keys(s).length!==2||!text(s.label,300)||!href(s.href)))throw Error('Invalid source link.');
  return freeze(JSON.parse(JSON.stringify(value)));
 }
 function validateOutput(value){
  if(!value||typeof value!=='object'||Array.isArray(value))throw Error('A comparison summary is required.');
  const {complete,usableCases,insufficientCases,...common}=value;
  if(Object.hasOwn(common,'answer')||typeof complete!=='boolean'||!Number.isSafeInteger(usableCases)||usableCases<0||!Number.isSafeInteger(insufficientCases)||insufficientCases<0||usableCases+insufficientCases!==value.coveredCases||complete!==(value.remainingCases===0))throw Error('Inconsistent comparison counts.');
  validate({...common,answer:complete?'not-found':null});
  return freeze(JSON.parse(JSON.stringify(value)));
 }
 function validateInspection(value){
  if(!value||typeof value!=='object'||Array.isArray(value))throw Error('An output inspection summary is required.');
  const {complete,runeOutputCases,noRuneCases,...common}=value;
  if(Object.hasOwn(common,'answer')||typeof complete!=='boolean'||!Number.isSafeInteger(runeOutputCases)||runeOutputCases<0||!Number.isSafeInteger(noRuneCases)||noRuneCases<0||runeOutputCases+noRuneCases!==value.coveredCases||complete!==(value.remainingCases===0))throw Error('Inconsistent output inspection counts.');
  validate({...common,answer:complete?'not-found':null});return freeze(JSON.parse(JSON.stringify(value)));
 }
 function pageLabel(ids){const grouped=[];for(let i=0;i<ids.length;i++){let end=i;while(end+1<ids.length&&ids[end+1].slice(0,4)===ids[i].slice(0,4)&&Number(ids[end+1].slice(4))===Number(ids[end].slice(4))+1)end++;grouped.push(ids[i].toUpperCase()+(end>i?'–'+ids[end].slice(4):''));i=end;}return grouped.join(', ');}
 const number=n=>n.toLocaleString('en-US');
 function action(model){return model.answer?'inspect':!model.lookupComplete?'retry':'check';}
 function markup(m,level,busy=false,error='',checkLabel='Continue checking',output=false){
  const kind=output?(m.complete?'inspect':!m.lookupComplete?'retry':'check'):action(m),label=kind==='inspect'?'Inspect output':kind==='retry'?'Retry saved evidence':checkLabel;
  return '<section class="finite-search"><h'+level+'>'+(output==='inspection'?'Inspect these outputs':output?'Compare these outputs':'Does any setting meet this check?')+'</h'+level+'><p class="finite-search-finding" role="status">'+(output==='inspection'?number(m.runeOutputCases)+' outputs ready · '+number(m.noRuneCases)+' without runes · '+number(m.remainingCases)+' unchecked.':output?number(m.usableCases)+' compared · '+number(m.insufficientCases)+' too short · '+number(m.remainingCases)+' unchecked.':esc(m.finding))+'</p><p class="finite-search-limit">'+esc(m.limit)+'</p><dl class="finite-search-summary"><div><dt>Method</dt><dd>'+esc(m.method)+'</dd></div><div><dt>Settings</dt><dd>'+number(m.programCount)+' '+(m.programCount===1?'setting':'settings')+'</dd></div><div><dt>Pages</dt><dd>'+esc(pageLabel(m.pageIds))+'</dd></div><div><dt>Check</dt><dd>'+esc(m.check)+'</dd></div></dl>'+(output?'<p class="finite-search-progress">'+esc(m.finding)+(!m.lookupComplete?' Saved evidence has not been fully checked.':'')+'</p>':!m.answer?'<p class="finite-search-progress">'+number(m.coveredCases)+' of '+number(m.totalCases)+' checks saved and verified.'+(!m.lookupComplete?' Saved evidence has not been fully checked.':'')+'</p>':'')+'<div class="finite-search-actions"><button type="button" data-finite-action="'+kind+'"'+(busy?' disabled aria-busy="true"':'')+'>'+esc(label)+'</button>'+(output&&m.coveredCases&&kind!=='inspect'?'<button type="button" data-finite-work="inspect">Inspect checked output</button>':'')+'</div>'+(error?'<p class="finite-search-error" role="alert">'+esc(error)+'</p>':'')+(m.sourceLinks.length?(m.sourceLinks.length>1?'<details class="finite-search-source-disclosure"><summary>Sources used ('+m.sourceLinks.length+')</summary>':'')+'<ul class="finite-search-sources">'+m.sourceLinks.map(s=>'<li><a href="'+esc(s.href)+'">'+esc(s.label)+'</a></li>').join('')+'</ul>'+(m.sourceLinks.length>1?'</details>':''):'')+'</section>';
 }
 function render(model,{headingLevel=2,checkLabel='Continue checking'}={}){if(!text(checkLabel,80))throw Error('Invalid check action label.');return markup(validate(model),[2,3,4].includes(headingLevel)?headingLevel:2,false,'',checkLabel);}
 function renderOutput(model,{headingLevel=2,checkLabel='Continue comparing'}={}){if(!text(checkLabel,80))throw Error('Invalid check action label.');return markup(validateOutput(model),[2,3,4].includes(headingLevel)?headingLevel:2,false,'',checkLabel,true);}
 function renderInspection(model,{headingLevel=2,checkLabel='Continue checking outputs'}={}){if(!text(checkLabel,80))throw Error('Invalid check action label.');return markup(validateInspection(model),[2,3,4].includes(headingLevel)?headingLevel:2,false,'',checkLabel,'inspection');}
 function mount(host,model,options={}){
  if(!host||typeof host.addEventListener!=='function'||typeof host.removeEventListener!=='function')throw Error('A view host is required.');
  let captured=validate(model);mounts.get(host)?.destroy();let dead=false,generation=0,pending=false,controller=null;
  const level=[2,3,4].includes(options.headingLevel)?options.headingLevel:2;
  function draw(error=''){if(!dead)host.innerHTML=markup(captured,level,pending,error);}
  async function click(event){const button=event.target?.closest?.('[data-finite-action]');if(dead||pending||!button||!host.contains(button))return;const kind=action(captured);if(button.getAttribute('data-finite-action')!==kind)return;
   const callback=options[kind==='inspect'?'onInspect':kind==='retry'?'onRetry':'onCheckRemaining'];if(typeof callback!=='function')return;
   const token=++generation;controller=new AbortController();pending=true;draw();let failure='';
   try{await callback(captured,{signal:controller.signal});}catch(error){if(!dead&&generation===token){failure='This action could not be completed. Please try again.';try{options.onError?.(error);}catch{/* Diagnostic hooks cannot break recovery. */}}}
   finally{if(!dead&&generation===token){pending=false;controller=null;draw(failure);}}
  }
  host.addEventListener('click',click);const handle={update(next){const checked=validate(next);if(dead)return;generation++;controller?.abort();controller=null;pending=false;captured=checked;draw();},destroy(){if(dead)return;dead=true;generation++;controller?.abort();host.removeEventListener('click',click);if(mounts.get(host)===handle)mounts.delete(host);}};
  mounts.set(host,handle);draw();return handle;
 }
 const api={validate,render,validateOutput,renderOutput,validateInspection,renderInspection,mount};if(typeof module==='object'&&module.exports)module.exports=api;else root.FiniteSearchView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
