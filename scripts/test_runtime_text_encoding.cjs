// Human-written browser assets must survive Windows source edits as UTF-8.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const bad=/\u00c3[\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013-\u2022\u2030\u2039\u203a\u20ac\u2122]|\u00c2[\u0080-\u00bf]|\u00e2\u20ac|\ufffd/u;
assert(bad.test('\u00c3\u00a9'));assert(bad.test('\u00c2\u00b7'));assert(bad.test('\u00e2\u20ac\u00a6'));
assert(!bad.test('Cymraeg \u00e9 \u00c3o \u16a0 \u2026 \u00b7'));
let count=0;
for(const name of fs.readdirSync(path.resolve(__dirname,'..'))){
 if(!/\.(?:js|html|css)$/.test(name)||/data|catalog/.test(name))continue;
 const bytes=fs.readFileSync(path.resolve(__dirname,'..',name)),source=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 assert(!bad.test(source),name+': corrupted text encoding; read/write source explicitly as UTF-8');count++;
}
console.log('PASS UTF-8 and visible punctuation in '+count+' handwritten browser assets; archived/generated text excluded.');
