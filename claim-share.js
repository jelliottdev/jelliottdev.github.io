/* Bounded standardized-card links and optional native share. No network/storage. */
(function(root){
 'use strict';
 const C=typeof module==='object'&&module.exports?require('./claim-specification.js'):root.ClaimSpecification;
 const VERSION=1,MAX_BYTES=12000,MAX_URL=16000;
 const imageBindings=new WeakMap();
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 function json(value,depth=0){
  if(depth>16)throw Error('Shared fields are nested too deeply');
  if(value===null||typeof value==='boolean'||typeof value==='string')return value;
  if(typeof value==='number'&&Number.isFinite(value))return value;
  if(Array.isArray(value))return value.map(v=>json(v,depth+1));
  if(value&&typeof value==='object'&&(Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null)){
   const out={};for(const [k,v]of Object.entries(value)){
    if(['__proto__','prototype','constructor'].includes(k))throw Error('Unsafe shared field');
    out[k]=json(v,depth+1);
   }return out;
  }throw Error('Shared fields must be JSON');
 }
 function keys(value,allowed){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!allowed.includes(k)))throw Error('Invalid shared fields');}
 function activeField(f){return f.status==='specified'?{status:f.status,value:json(f.value)}:{status:f.status};}
 function cleanOperation(o){const result=json(o);
  // Some opaque steps carry their only active wording in sourceText. Promote
  // that wording to the shared step, rather than copying a second source field.
  if(!result.label&&typeof result.sourceText==='string')result.label=result.sourceText;
  for(const k of ['sourceText','provenance','editHistory'])delete result[k];return result;
 }
 function bytes(s){return new TextEncoder().encode(s);}
 function checkedPayload(p){
  p=json(p);keys(p,['version','outcome','method','scope','rules','unresolved']);
  if(p.version!==VERSION)throw Error('Unsupported shared idea version');
  for(const name of ['outcome','method','scope']){
   keys(p[name],['status','value']);if(!C.STATES.includes(p[name].status)||((p[name].status==='specified')!==own(p[name],'value')))throw Error('Invalid shared field state');
  }
  if(p.outcome.status==='specified'){
   keys(p.outcome.value,['outcomeId','detail']);
   if(![...Object.keys(C.OUTCOMES),'unclassified'].includes(p.outcome.value.outcomeId)||typeof p.outcome.value.detail!=='string')throw Error('Invalid shared outcome');
  }
  if(p.method.status==='specified'){
   keys(p.method.value,['operations']);if(!Array.isArray(p.method.value.operations)||p.method.value.operations.length>64)throw Error('Invalid shared operations');
   for(const o of p.method.value.operations)if(!o||typeof o.id!=='string'||!o.id.trim()||['sourceText','provenance','editHistory'].some(k=>own(o,k)))throw Error('Invalid shared operation');
  }
  keys(p.rules,C.RULES);if(Object.keys(p.rules).length!==C.RULES.length)throw Error('Missing shared rules');
  for(const f of Object.values(p.rules)){keys(f,['status','value']);if(!C.STATES.includes(f.status)||((f.status==='specified')!==own(f,'value')))throw Error('Invalid shared rule');}
  if(!Array.isArray(p.unresolved)||p.unresolved.length>64)throw Error('Invalid shared constraints');
  if(bytes(JSON.stringify(p)).length>MAX_BYTES)throw Error('Shared idea exceeds 12,000 decoded bytes');
  return p;
 }
 function cardData(spec){
  const s=C.validateConfirmed(spec),outcome=activeField(s.aim);
  if(outcome.status==='specified'){const aim=C.normalizeOutcome(s.aim);outcome.value={outcomeId:aim.id,detail:aim.detail};}
  const method=activeField(s.method);if(method.status==='specified')method.value={operations:s.method.value.operations.map(cleanOperation)};
  const rules=Object.fromEntries(C.RULES.map(k=>[k,activeField(s.rules[k])]));
  const unresolved=s.unresolved.map(c=>{const v=json(c);delete v.provenance;return v;});
  return checkedPayload({version:VERSION,outcome,method,scope:activeField(s.scope),rules,unresolved});
 }
 function encode(spec){
  const data=bytes(JSON.stringify(cardData(spec)));let binary='';for(const b of data)binary+=String.fromCharCode(b);
  return '#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 }
 function field(f){return C.field(f.status,f.status==='specified'?f.value:undefined,{kind:'project_context',refs:['shared-link:v1']});}
 const RULE_LABELS={representation:'Representation',wordBoundaries:'Word boundaries',boundaryMode:'Word handling',unmapped:'Unmapped values',inputVersion:'Input version',evaluation:'Evaluation',reset:'Restart rule',initialState:'Initial state',searchBounds:'Search bounds',searchProtocol:'Search protocol',exceptionalCases:'Exceptions'};
 const niceKey=s=>s.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/_/g,' ').replace(/^./,c=>c.toUpperCase());
 const pretty=v=>typeof v==='string'?v:JSON.stringify(v);
 function pageLabel(pages){
  if(!pages.length)return 'No pages selected';const result=[];
  for(let i=0;i<pages.length;i++){
   const start=pages[i];let end=start;
   while(i+1<pages.length&&pages[i+1].slice(0,4)===start.slice(0,4)&&Number(pages[i+1].slice(4))===Number(end.slice(4))+1)end=pages[++i];
   result.push(start.toUpperCase()+(end===start?'':'–'+end.slice(4)));
  }return result.join(', ');
 }
 function sections(p){
  const state=f=>f.status==='specified'?pretty(f.value):niceKey(f.status);
  const title=p.outcome.status==='specified'?(C.OUTCOMES[p.outcome.value.outcomeId]||'Other outcome'):'';
  const aim=p.outcome.status==='specified'?title+(p.outcome.value.detail&&p.outcome.value.detail!==title?' — '+p.outcome.value.detail:''):state(p.outcome);
  const rows=[['Outcome',aim]];
  const methodLabels=C.reviewRows({aim:p.outcome,method:p.method,scope:p.scope,rules:p.rules,unresolved:p.unresolved}).find(row=>row.label==='Method').tags;
  if(p.method.status==='specified')p.method.value.operations.forEach((o,i)=>rows.push(['Step '+(i+1),methodLabels[i].text,
   Object.entries(o).filter(([k])=>!['id','label','declaredFamilyId'].includes(k)&&!(k==='familyId'&&o.id==='family_selection')).map(([k,v])=>niceKey(k)+': '+pretty(v)).join('\n')]));
  else rows.push(['Method',state(p.method)]);
  if(p.scope.status==='specified'){
   const scope=p.scope.value,parts=[];
   if(own(scope,'pages'))parts.push(pageLabel(scope.pages));
   if(own(scope,'description'))parts.push(pretty(scope.description));
   for(const [k,v]of Object.entries(scope))if(!['pages','description'].includes(k))parts.push(niceKey(k)+': '+pretty(v));
   rows.push(['Scope',parts.length?parts.join('\n'):'Explicit empty scope description']);
  }else rows.push(['Scope',state(p.scope)]);
  for(const [k,f]of Object.entries(p.rules))if(f.status!=='unspecified')rows.push([RULE_LABELS[k],
   k==='boundaryMode'&&f.status==='specified'&&own(C.BOUNDARIES,f.value)?C.BOUNDARIES[f.value]:state(f)]);
  if(p.unresolved.length)rows.push(['Unresolved',JSON.stringify(p.unresolved)]);
  const unknown=Object.entries(p.rules).filter(([,f])=>f.status==='unspecified').map(([k])=>k);
  if(unknown.length)rows.push(['Other rules','Not specified']);
  return rows;
 }
 function decode(fragment){
  if(typeof fragment!=='string'||!/^#idea=[A-Za-z0-9_-]+$/.test(fragment)||fragment.length>MAX_URL)throw Error('Invalid shared idea link');
  const token=fragment.slice(6);if(token.length>Math.ceil(MAX_BYTES*4/3)||token.length%4===1)throw Error('Shared idea exceeds size limit');
  let parsed;try{const raw=atob(token.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-token.length%4)%4));
   if(btoa(raw).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')!==token)throw Error();
   const data=Uint8Array.from(raw,c=>c.charCodeAt(0));if(data.length>MAX_BYTES)throw Error();
   parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));
  }catch{throw Error('Malformed shared idea');}
  const p=checkedPayload(parsed),summary='Shared standardized idea (not an executed experiment).\n'+sections(p).map(r=>r.join(': ')).join('\n');
  const draft=C.createDraft({source:{text:summary,origin:'shared_link'},aim:field(p.outcome),method:field(p.method),scope:field(p.scope),rules:Object.fromEntries(Object.entries(p.rules).map(([k,f])=>[k,field(f)])),unresolved:p.unresolved});
  return {draft,acknowledged:{aim:true,scope:true},version:VERSION};
 }
 function link(spec,baseURL){const url=new URL(baseURL);if(!['http:','https:'].includes(url.protocol))throw Error('Sharing needs an HTTP(S) page URL');const entryVersion=url.searchParams.get('v');url.search='';if(entryVersion==='complete-current-20261024')url.searchParams.set('v',entryVersion);url.hash=encode(spec);const result=url.href;if(result.length>MAX_URL)throw Error('Shared URL exceeds 16,000 characters');return result;}
 function wrap(ctx,text,maxWidth){
  const lines=[];
  for(const paragraph of text.split('\n')){
   let line='';
   for(const token of paragraph.match(/\S+|\s+/gu)||[]){
    if(ctx.measureText(line+token).width<=maxWidth){line+=token;continue;}
    if(line.trim()){lines.push(line.trimEnd());line='';}
    if(!token.trim())continue;
    for(const char of token){if(line&&ctx.measureText(line+char).width>maxWidth){lines.push(line);line='';}line+=char;}
   }
   lines.push(line.trimEnd());
  }
  return lines;
 }
 async function renderPNG(spec,{document:doc=root.document,maxHeight=16000}={}){
  const p=cardData(spec);if(!doc?.createElement)throw Error('Image export is unavailable');
  const canvas=doc.createElement('canvas'),ctx=canvas.getContext('2d');if(!ctx)throw Error('Image export is unavailable');
  const width=1080,pad=64,blocks=[];let y=160;
  for(const row of sections(p)){
   ctx.font='26px sans-serif';const labels=wrap(ctx,row[0],width-2*pad);
   ctx.font='34px sans-serif';const body=wrap(ctx,row.slice(1).filter(v=>v&&v!=='{}').join('\n'),width-2*pad);
   blocks.push({y,labels,body});y+=labels.length*34+12+body.length*46+34;
  }
  const height=Math.ceil(y+88);if(!Number.isFinite(maxHeight)||height>maxHeight||height>32760)throw Error('Card is too long for a PNG; share the complete link instead');
  canvas.width=width;canvas.height=height;ctx.fillStyle='#fff';ctx.fillRect(0,0,width,height);
  ctx.fillStyle='#202020';ctx.font='bold 52px Georgia, serif';ctx.fillText('An idea for Liber Primus',pad,92);
  for(const block of blocks){let top=block.y;ctx.fillStyle='#666';ctx.font='26px sans-serif';for(const line of block.labels){ctx.fillText(line,pad,top);top+=34;}top+=12;ctx.fillStyle='#222';ctx.font='34px sans-serif';for(const line of block.body){ctx.fillText(line,pad,top);top+=46;}}
  ctx.fillStyle='#666';ctx.font='24px sans-serif';ctx.fillText('Liberpedia · An idea for Liber Primus',pad,height-42);
  return new Promise((resolve,reject)=>canvas.toBlob(blob=>{
   if(!blob){reject(Error('PNG export failed'));return;}imageBindings.set(blob,JSON.stringify(p));resolve(blob);
  },'image/png'));
 }
 async function share(spec,url,env={}){
  const nav=env.navigator||root.navigator,doc=env.document||root.document,FileType=env.File||root.File;
  const complete=link(spec,url),data={title:'An idea for Liber Primus',text:'Liberpedia · Standardized idea',url:complete};
  let png=null,imageError=null;
  if(env.preparedPNG){
   if(imageBindings.get(env.preparedPNG)===JSON.stringify(cardData(spec)))png=env.preparedPNG;
   else imageError='Prepared image belongs to a different card; sharing the complete link';
  }
  if(typeof nav?.share==='function'){
   if(png&&FileType&&typeof nav.canShare==='function'){
    const file=new FileType([png],'liber-primus-idea.png',{type:'image/png'});
    try{if(nav.canShare({files:[file]}))data.files=[file];}catch{/* Share text/link if file support cannot be established. */}
   }
   try{await nav.share(data);return {status:'shared',url:complete,imageError};}
   catch(error){if(error?.name==='AbortError')return {status:'cancelled',url:complete};return {status:'fallback',url:complete,png,error:error.message||'Native sharing failed',imageError};}
  }
  let status='copied',error;
  try{if(typeof nav?.clipboard?.writeText!=='function')throw Error('Clipboard is unavailable');await nav.clipboard.writeText(complete);}
  catch(failure){status='fallback';error=failure.message||'Copy the link manually';}
  if(!png)try{png=await renderPNG(spec,{document:doc});}catch(failure){imageError=failure.message;}
  return {status,url:complete,png,...(error?{error}:{}),imageError};
 }
 const api={VERSION,MAX_BYTES,MAX_URL,cardData,sections:p=>sections(checkedPayload(p)),encode,decode,link,renderPNG,prepare:renderPNG,share};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ClaimShare=api;
})(typeof globalThis!=='undefined'?globalThis:this);
