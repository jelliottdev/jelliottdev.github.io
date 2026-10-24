const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),rows=require('../reader/source-rows.js');global.ReaderSourceRows=rows;const address=require('../reader/reader-address.js');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8')),index=read('data/index.json');
assert.equal(index.pages.length,75);
let sourceCount=0,reviewed=0,readings=0;
for(const meta of index.pages){
 const page=read('data/pages/'+meta.id+'.json');for(const file of ['images/'+meta.id+'.jpg','thumbs/'+meta.id+'.jpg'])assert(fs.existsSync(path.join(root,file)),file);
 const numbered=rows.rows(page.raw).filter(r=>r.number!==null);assert.equal(numbered.length,page.lines.length,meta.id+' addresses must agree with actual source rows');
 numbered.forEach((r,i)=>{assert.equal(r.number,i+1);assert.equal(r.text,page.lines[i].raw)});sourceCount+=numbered.length;
 const labels=rows.labels(page.raw,index.alphabet);assert.equal(labels.split('\n').length,page.raw.split('\n').length);assert(rows.addressable(page,labels));
 if(page.reviewed_text){assert(rows.addressable(page,page.reviewed_text),meta.id+' reviewed row mapping');reviewed++;}
 if(page.reading){assert.equal(typeof page.reading.literal,'string');assert.equal(typeof page.reading.reading,'string');readings++;}
}
const page=read('data/pages/lp2-15.json'),display=rows.rows(page.raw);assert.equal(display[5].number,null);assert.equal(display[6].number,null);assert.equal(display[7].number,6);assert.equal(display[5].text,'&');assert.equal(display[6].text,'$');
for(const input of ['15:4','15:4:2-4','15:4-8','15-17','LP1 7:3']){const t=address.parse(input,'LP2');assert(!t.error);const p=read('data/pages/'+t.release.toLowerCase()+'-'+String(t.pages[0]).padStart(2,'0')+'.json');assert.equal(address.validate(t,index.pages,p),null,input);}
assert(address.parse('15-17:4').error);assert(address.parse('15:4-8:2').error);assert(address.parse('15:0').error);assert(address.validate(address.parse('15:99'),index.pages,page));assert.equal(address.parse('ordinary phrase'),null);
const labels=rows.labels(page.raw,index.alphabet);assert(labels.includes('\n&\n$\n'));assert.equal(page.raw,read('data/pages/lp2-15.json').raw,'Rendering must never mutate the stored copy source');
for(const file of ['reader.html','manuscript-reader.js','manuscript-reader.css','manuscript-compare.js','manuscript-compare.css']){const text=fs.readFileSync(path.join(root,file),'utf8');assert(!text.includes('/archive/'));assert(!text.includes('reader-study'));}
for(const special of ['exports/sources/cicada-2014-sixth-onion/10-page.jpg','fonts/NotoSansRunic-Regular.ttf'])assert(fs.existsSync(path.join(root,special)));
console.log(`PASS: all75 real pages/assets; ${sourceCount} exact source rows, ${reviewed} reviewed row maps, ${readings} literal/contextual versions; separator preservation/address bounds; production-local paths.`);
