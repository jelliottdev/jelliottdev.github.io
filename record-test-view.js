/* Authored descriptions of a recorded test; never executable plans or inferred methods. */
(function(root){
 'use strict';
 const fields=[['input','Used'],['action','Tried'],['check','Checked']];
 const esc=value=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
 function plain(value,max=320){
  return typeof value==='string'&&value.trim()===value&&value.length>0&&Array.from(value).length<=max
   &&!/[<>\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(value);
 }
 function valid(value){
  if(!value||typeof value!=='object'||Array.isArray(value)||Reflect.ownKeys(value).length!==3)return false;
  return fields.every(([key])=>{const property=Object.getOwnPropertyDescriptor(value,key);return property?.enumerable&&Object.hasOwn(property,'value')&&plain(property.value);});
 }
 // Presentation uses authored text only; never guess a method from source names.
 function own(record,key){const p=record&&Object.getOwnPropertyDescriptor(record,key);return p&&Object.hasOwn(p,'value')?p.value:undefined;}
 function title(record){const value=own(record,'reader_title');return plain(value,110)?value:own(record,'title')||'';}
 function intro(record){const value=own(record,'reader_intro');return plain(value,280)?value:'';}
 function blurb(record){const value=intro(record)||own(record,'reader_question');return plain(value,320)&&value!==title(record)?value:'';}
 function renderIntro(record){const value=intro(record);return value?'<p class="record-intro">'+esc(value)+'</p>':'';}
 function render(record,{headingLevel=2}={}){
  const value=record?.reader_test;if(!valid(value))return '';
  const level=Number.isInteger(headingLevel)&&headingLevel>=2&&headingLevel<=6?headingLevel:2;
  return '<section class="record-test" aria-label="What was tried"><h'+level+'>What was tried</h'+level+'><dl>'+fields.map(([key,label])=>'<div><dt>'+label+'</dt><dd>'+esc(value[key])+'</dd></div>').join('')+'</dl></section>';
 }
 function renderRelated(record){
  const id=own(record,'id');if(typeof id!=='string'||!/^[a-z0-9][a-z0-9-]{0,127}$/.test(id))return '';
  const excerpt=(value,max)=>{if(typeof value!=='string')return '';const text=value.replace(/\s+/gu,' ').trim();const units=Array.from(text);if(units.length<=max)return text;const head=units.slice(0,max).join(''),cut=head.lastIndexOf(' ');return head.slice(0,cut>head.length*.6?cut:head.length)+'…';};
  const test=own(record,'reader_test'),scope=own(record,'scope'),authored=valid(test),action=authored?own(test,'action'):own(scope,'procedure'),check=authored?own(test,'check'):'',checked=authored?action+(check!==action?' '+check:''):action,finding=own(record,'reader_finding')||own(record,'finding'),limit=own(record,'reader_limit')||own(record,'limitations'),lead=excerpt(finding,240),normalized=typeof finding==='string'?finding.replace(/\s+/gu,' ').trim():'';
  const paragraph=(label,value,small=false)=>typeof value==='string'&&value.trim()?'<p'+(small?' class="small"':'')+'><strong>'+label+':</strong> '+esc(value).replace(/\n/g,'<br>')+'</p>':'';
  const detail=(lead!==normalized?paragraph('Full result',finding):'')+paragraph(authored?'What was checked':'What was tried',checked)+paragraph('Limit',limit,true);
  return '<article class="source record-related"><h3><a href="library.html#/experiment/'+esc(id)+'">'+esc(String(title(record)))+'</a></h3>'+(lead?'<p><strong>Result:</strong> '+esc(lead)+'</p>':'')+(detail?'<details><summary>How it was checked and its limits</summary>'+detail+'</details>':'')+'</article>';
 }
 const api={valid,render,title,intro,blurb,renderIntro,renderRelated};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordTestView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
