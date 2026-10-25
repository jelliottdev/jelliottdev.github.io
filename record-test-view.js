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
 const api={valid,render,title,intro,blurb,renderIntro};if(typeof module==='object'&&module.exports)module.exports=api;else root.RecordTestView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
