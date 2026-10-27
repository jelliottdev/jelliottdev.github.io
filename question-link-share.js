/* Share an explicitly saved question, without exporting a draft or claiming a result. */
(function(root){
 'use strict';
 const ID=/^p_[a-f0-9]{64}$/;
 function link(options){
  if(!options||typeof options!=='object'||Array.isArray(options)||Object.keys(options).length!==2||!['proposalId','pageURL'].every(key=>Object.hasOwn(options,key))||!ID.test(options.proposalId)||typeof options.pageURL!=='string'||options.pageURL.length>4096)throw Error('Use a saved question and the current page URL.');
  const base=new URL(options.pageURL);
  if(!['http:','https:'].includes(base.protocol)||base.username||base.password)throw Error('Use a web page URL without credentials.');
  const url=new URL('run.html',base);url.hash='idea='+options.proposalId;return url.href;
 }
 async function share(options,env={}){
  const url=link(options),nav=env.navigator||root.navigator;
  if(typeof nav?.share==='function'){
   try{await nav.share({title:'Liberpedia research question',url});return Object.freeze({status:'shared',url});}
   catch(error){if(error?.name==='AbortError')return Object.freeze({status:'cancelled',url});}
  }
  try{if(typeof nav?.clipboard?.writeText!=='function')throw Error('Unavailable');await nav.clipboard.writeText(url);return Object.freeze({status:'copied',url});}
  catch{return Object.freeze({status:'fallback',url});}
 }
 const api=Object.freeze({link,share});if(typeof module==='object'&&module.exports)module.exports=api;else root.QuestionLinkShare=api;
})(typeof globalThis!=='undefined'?globalThis:this);
