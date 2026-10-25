/* Shared strict official aggregate parser. No fetch or source substitution. */
(function(root){'use strict';
const ID=/^(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))$/;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
function parseInputBundle(value){
 if(!exact(value,['schema','alphabet','pages'])||value.schema!=='liberpedia-local-inputs-v1'||!Array.isArray(value.alphabet)||value.alphabet.length!==29||!Array.isArray(value.pages)||value.pages.length!==75)throw Error('The official input bundle is malformed.');
 const runes=new Set();for(const item of value.alphabet){if(!exact(item,['rune','latin','prime'])||typeof item.rune!=='string'||Array.from(item.rune).length!==1||runes.has(item.rune)||typeof item.latin!=='string'||!item.latin||item.latin.length>20||!Number.isInteger(item.prime)||item.prime<2||item.prime>1000)throw Error('The official bundle alphabet is invalid.');runes.add(item.rune);}
 const pages=new Map();for(const page of value.pages){if(!exact(page,['id','raw','reviewed_text'])||!ID.test(page.id)||pages.has(page.id)||typeof page.raw!=='string'||page.raw.length>300000||!(page.reviewed_text===null||typeof page.reviewed_text==='string'&&page.reviewed_text.length<=300000))throw Error('The official bundle page is invalid.');pages.set(page.id,page);}
 return {alphabet:value.alphabet,pages};
}
const api={parse:parseInputBundle};if(typeof module==='object'&&module.exports)module.exports=api;else root.LocalInputBundle=api;
})(typeof globalThis!=='undefined'?globalThis:this);
