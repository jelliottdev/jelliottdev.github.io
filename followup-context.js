/* Source-authored context only; never a task condition, inference or result. */
(function(root){
 'use strict';
 function valid(value){return typeof value==='string'&&value===value.trim()&&value.length>0&&Array.from(value).length<=500&&!/[<>\[\]`*\\\x00-\x1f\x7f-\x9f\u2028\u2029\ud800-\udfff]/u.test(value);}
 const api={valid};if(typeof module==='object'&&module.exports)module.exports=api;else root.FollowupContext=api;
})(typeof globalThis!=='undefined'?globalThis:this);
