/* Preserve public hash links while opening the dedicated workspaces. */
(function(root){
  'use strict';
  function destination(hash){
    const [path,query='']=String(hash||'').replace(/^#/, '').split('?');
    const parts=path.split('/').filter(Boolean);
    const params=new URLSearchParams(query);
    if(params.get('full')==='1')return null;
    if(!parts.length || (parts.length===1&&parts[0]==='overview'))return 'home.html';
    if(parts[0]==='reader' && parts.length<=2){
      const id=parts[1]||'lp1-00';
      if(!/^lp[12]-\d{2}$/.test(id))return null;
      return 'reader.html#'+id+(query?'?'+query:'');
    }
    if(parts[0]==='research'||parts[0]==='research-map'){
      if(parts[0]==='research'){
        if(/^\d+$/.test(params.get('page')||'')){params.set('p',params.get('page'));params.delete('page');}
        if(!params.has('mode'))params.set('mode','list');
      }
      return 'research.html'+(params.size?'#'+params:'');
    }
    if(parts[0]==='wiki'&&parts.length<=2){
      const id=parts[1];if(id&&!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))return null;
      return 'library.html#/'+(id?'guide/'+id:'guides')+(query?'?'+query:'');
    }
    if(parts[0]==='experiments'&&parts.length===2&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(parts[1]))return 'library.html#/experiment/'+parts[1]+(query?'?'+query:'');
    if(parts[0]==='experiments' && parts.length===1 && (params.has('browse') || params.get('section')==='browse-experiments')){
      params.set('q',params.get('browse')||params.get('q')||'');params.delete('browse');params.delete('section');params.set('mode','list');
      if(params.has('page')){params.set('p',params.get('page'));params.delete('page');}
      return 'research.html#'+params;
    }
    if(parts[0]==='experiments' && parts.length===1)return 'investigate.html'+(query?'?'+query:'');
    return null;
  }
  function redirect(){const target=destination(location.hash);if(target){location.replace(target);return true;}return false;}
  const api={destination,redirect};
  if(typeof module!=='undefined')module.exports=api;
  else {root.LiberpediaWorkspaces=api;redirect();}
})(globalThis);
