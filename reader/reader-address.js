'use strict';
// Small, explicit grammar. The resolver never guesses which release or row was meant.
const ReaderAddress={
 parse(input,currentRelease='LP2'){
  let text=input.trim().replace(/[–—]/g,'-');
  const natural=/^(?:(LP[12])\s+)?(?:page\s+)?(\d{1,2}(?:\s*-\s*\d{1,2})?)(?:\s*,?\s+lines?\s+(\d+(?:\s*-\s*\d+)?))?(?:\s*,?\s+words?\s+(\d+(?:\s*-\s*\d+)?))?$/i.exec(text);
  if(natural?.[4]&&!natural[3])return {error:'Choose a line before adding a word address.'};
  if(natural)text=[natural[1]||'',natural[2],natural[3]?':'+natural[3]:'',natural[4]?':'+natural[4]:''].join(' ').replace(/\s*:\s*/g,':').trim();
  const match=/^(?:(LP[12])\s*[- ]?\s*)?(\d{1,2}(?:\s*-\s*\d{1,2})?)(?::(\d+(?:\s*-\s*\d+)?))?(?::(\d+(?:\s*-\s*\d+)?))?$/i.exec(text);
  if(!match)return null;
  const range=value=>{const parts=value.split('-').map(x=>Number(x.trim()));return [parts[0],parts[1]??parts[0]]};
  const target={release:(match[1]||currentRelease).toUpperCase(),pages:range(match[2]),lines:match[3]?range(match[3]):null,words:match[4]?range(match[4]):null};
  if(target.pages[0]>target.pages[1]||target.lines&&target.lines[0]>target.lines[1]||target.words&&target.words[0]>target.words[1])return {error:'Write ranges from first to last.'};
  if(target.lines&&target.pages[0]!==target.pages[1])return {error:'Choose one page before adding a line address.'};
  if(target.words&&!target.lines)return {error:'Choose one line before adding a word address.'};
  if(target.words&&target.lines[0]!==target.lines[1])return {error:'Choose one line before adding a word address.'};
  if(target.lines?.[0]===0||target.words?.[0]===0)return {error:'Line and word numbers start at 1.'};
  return target;
 },
 label(target){return [target.release+' '+target.pages.map(x=>String(x).padStart(2,'0')).filter((x,i,a)=>i===0||x!==a[0]).join('–'),target.lines?'line'+(target.lines[0]!==target.lines[1]?'s ':' ')+target.lines.filter((x,i,a)=>i===0||x!==a[0]).join('–'):'',target.words?'word'+(target.words[0]!==target.words[1]?'s ':' ')+target.words.filter((x,i,a)=>i===0||x!==a[0]).join('–'):''].filter(Boolean).join(' · ')},
 short(target){const range=a=>a[0]===a[1]?String(a[0]):a.join('-');return target.release+' '+range(target.pages)+(target.lines?':'+range(target.lines):'')+(target.words?':'+range(target.words):'')},
 words(text){return [...text.matchAll(/[^\s\-.,&$§/%]+/gu)].map(m=>({text:m[0],start:m.index,end:m.index+m[0].length}))},
 validate(target,index,page){
  const pages=index.filter(p=>p.release===target.release&&p.release_index>=target.pages[0]&&p.release_index<=target.pages[1]);
  if(pages.length!==target.pages[1]-target.pages[0]+1)return 'That page range is outside this release.';
  if(target.lines&&page){if(target.lines[1]>ReaderSourceRows.rows(page.raw).filter(r=>r.number!==null).length)return `${page.id.toUpperCase()} has ${ReaderSourceRows.rows(page.raw).filter(r=>r.number!==null).length} source lines.`;if(target.words){const count=this.words(ReaderSourceRows.rows(page.raw).find(r=>r.number===target.lines[0]).text).length;if(target.words[1]>count)return `Line ${target.lines[0]} has ${count} archive words.`}}
  return null;
 }
};

if(typeof module!=="undefined")module.exports=ReaderAddress;else window.ReaderAddress=ReaderAddress;
