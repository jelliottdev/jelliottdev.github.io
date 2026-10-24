/* Shared text-entry contract. URL fragments are not sent in the page request. */
(function(root){
 'use strict';
 const MAX_LENGTH=1500;
 function issue(text){
  if(typeof text!=='string'||!text.trim())return 'Describe an idea first.';
  if(text.length>MAX_LENGTH)return 'The text checker accepts up to 1,500 characters. Shorten the idea to continue.';
  return '';
 }
 function href(text){
  const error=issue(text);if(error)throw Error(error);
  // A new entry URL also avoids an older cached checker that cannot read input fragments.
  return 'investigate.html?v=20261024-input#input='+encodeURIComponent(text);
 }
 function read(location={}){
  const fragment=location.hash||'';
  if(fragment.startsWith('#input=')){
   try{return {text:decodeURIComponent(fragment.slice(7)),error:''};}
   catch{return {text:'',error:'This idea link could not be read. Return to the home page or enter the idea below.'};}
  }
  return {text:new URLSearchParams(location.search||'').get('q')||'',error:''};
 }
 const api={MAX_LENGTH,issue,href,read};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.IdeaInput=api;
})(globalThis);
