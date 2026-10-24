/* Source rows exclude standalone archive separators, never screen wrapping. */
(function(root){
 const isSource=text=>/[^\s\-.,/&$§%]/u.test(text);
 function rows(text){let number=0;return String(text??'').split('\n').map((text,index)=>({text,archive_row:index+1,number:isSource(text)?++number:null}));}
 function labels(raw,alphabet){const map=new Map(alphabet.map(a=>[a.rune,a.latin]));return [...raw].map(c=>map.get(c)||c).join('');}
 function addressable(page,text){const original=rows(page.raw),derived=rows(text);return original.length===derived.length&&original.every((r,i)=>(r.number===null)===(derived[i].number===null));}
 const api={rows,labels,addressable,isSource};if(typeof module!=='undefined')module.exports=api;else root.ReaderSourceRows=api;
})(globalThis);
