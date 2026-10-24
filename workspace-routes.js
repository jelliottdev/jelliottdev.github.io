/* Preserve public hash links while opening the dedicated workspaces. */
(function(root){
  'use strict';
  function destination(hash){
    const [path,query='']=String(hash||'').replace(/^#/, '').split('?');
    const parts=path.split('/').filter(Boolean);
    if(parts[0]==='reader' && parts.length<=2){
      const id=parts[1]||'lp1-00';
      if(!/^lp[12]-\d{2}$/.test(id))return null;
      return 'reader.html#'+id+(query?'?'+query:'');
    }
    if(parts[0]==='experiments' && parts.length===1 && (new URLSearchParams(query).has('browse') || new URLSearchParams(query).get('section')==='browse-experiments'))return null;
    if(parts[0]==='experiments' && parts.length===1)return 'investigate.html'+(query?'?'+query:'');
    return null;
  }
  function redirect(){const target=destination(location.hash);if(target){location.replace(target);return true;}return false;}
  const api={destination,redirect};
  if(typeof module!=='undefined')module.exports=api;
  else {root.LiberpediaWorkspaces=api;redirect();}
})(globalThis);
