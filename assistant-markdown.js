/* Small, escaped Markdown renderer. Only evidence-owned links can become anchors. */
(function(root){
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safe=href=>/^#\/(?:page\/lp[12]-\d{2}|reader\/lp[12]-\d{2}|experiments\/[a-z0-9-]+|spelling|conventions|alphabet|readings|topics|sources)$/.test(href);
  function render(text,sources=[]){
    const inline=(s,depth=0)=>{
      if(depth>3)return esc(s);
      return s.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]\n]+\]\([^)]+\)|\[\d+\])/g).map(part=>{
        if(/^`[^`]+`$/.test(part))return '<code>'+esc(part.slice(1,-1))+'</code>';
        if(/^\*\*[^*]+\*\*$/.test(part))return '<strong>'+inline(part.slice(2,-2),depth+1)+'</strong>';
        if(/^\*[^*]+\*$/.test(part))return '<em>'+inline(part.slice(1,-1),depth+1)+'</em>';
        const citation=part.match(/^\[(\d+)\]$/);
        if(citation){const source=sources[Number(citation[1])-1];if(source&&safe(source.href))return `<a class="answer-citation" href="${esc(source.href)}" title="${esc(source.title)}" aria-label="Source ${citation[1]}: ${esc(source.title)}">${esc(part)}</a>`;}
        const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if(link)return sources.some(s=>s.href===link[2])&&safe(link[2])?`<a href="${esc(link[2])}">${esc(link[1])}</a>`:esc(link[1]);
        return esc(part);
      }).join('');
    };
    const lines=String(text).split('\n'),out=[];
    let paragraph=[],list='',code=null;
    const flush=()=>{if(paragraph.length){out.push('<p>'+inline(paragraph.join(' '))+'</p>');paragraph=[];}};
    const close=()=>{flush();if(list){out.push(`</${list}>`);list='';}};
    const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(s=>s.trim());
    for(let i=0;i<lines.length;i++){
      const line=lines[i];
      if(/^\s*```/.test(line)){close();if(code!==null){out.push('<pre tabindex="0"><code>'+esc(code.join('\n'))+'</code></pre>');code=null;}else code=[];continue;}
      if(code!==null){code.push(line);continue;}
      if(!line.trim()){close();continue;}
      if(line.includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i+1])){
        close();const headers=cells(line);i++;
        let rows='';while(i+1<lines.length&&lines[i+1].includes('|')&&lines[i+1].trim()){
          const row=cells(lines[++i]);rows+='<tr>'+headers.map((_,n)=>'<td>'+inline(row[n]||'')+'</td>').join('')+'</tr>';}
        out.push('<div class="answer-table" role="region" aria-label="Answer comparison table" tabindex="0"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+inline(h)+'</th>').join('')+'</tr></thead><tbody>'+rows+'</tbody></table></div>');continue;
      }
      const heading=line.match(/^(#{1,6})\s+(.+)$/);
      if(heading){close();out.push(`<h3>${inline(heading[2])}</h3>`);continue;}
      const item=line.match(/^\s*(?:([-*])|\d+[.)])\s+(.+)$/);
      if(item){flush();const type=item[1]?'ul':'ol';if(type!==list){close();list=type;out.push(`<${type}>`);}out.push('<li>'+inline(item[2])+'</li>');continue;}
      closeList();
      if(/^>\s?/.test(line)){flush();out.push('<blockquote>'+inline(line.replace(/^>\s?/,''))+'</blockquote>');}else paragraph.push(line);
    }
    function closeList(){if(list){out.push(`</${list}>`);list='';}}
    close();if(code!==null)out.push('<pre tabindex="0"><code>'+esc(code.join('\n'))+'</code></pre>');
    return out.join('');
  }
  const api={render,safe};
  if(typeof module!=='undefined')module.exports=api;else root.AssistantMarkdown=api;
})(globalThis);
