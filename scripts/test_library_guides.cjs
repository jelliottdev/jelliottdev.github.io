/* Scoped guide interactions; synthetic DOM and existing line-gap lifecycle tests. */
'use strict';
const assert=require('node:assert/strict'),G=require('../library-guides.js');
function node(value=''){return {value,hidden:true,textContent:'',listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},setAttribute(k,v){this[k]=v;}}}
(async()=>{
 const fields=['pages','orders','shifts','offsets'].map((id,i)=>Object.assign(node(String(i+2)),{id:'choice-'+id}));
 const controls=node(),fallback=node(),outputs=new Map();
 const figure={querySelector(selector){if(selector==='.choice-explorer-live')return controls;if(selector==='.choice-explorer-static')return fallback;const f=fields.find(f=>'#'+f.id===selector);if(f)return f;if(!outputs.has(selector))outputs.set(selector,node());return outputs.get(selector)}};
 const choice={isConnected:true,querySelector:s=>s==='#choice-explorer'?figure:null};
 await G.bind(choice);assert.equal(controls.hidden,false);assert.equal(fallback.hidden,true);assert.equal(outputs.get('#choice-total').textContent,'120 configurations');
 fields[0].value='10';fields[0].listeners.input();assert.equal(outputs.get('#choice-total').textContent,'600 configurations');assert.equal(outputs.get('#choice-step-offsets').textContent,'600');
 // Real source renderer is delegated, never reimplemented using screen pixels.
 const prior=global.LineGapView,calls=[];global.LineGapView={render:()=>'<measured-source-view>',bind(mount,options){calls.push({mount,options});return Promise.resolve()}};
 const mount={innerHTML:''},article={isConnected:true,querySelector:s=>s==='[data-line-gap-explorer]'?mount:null};
 await G.bind(article,{isCurrent:()=>article.isConnected});assert.equal(mount.innerHTML,'<measured-source-view>');assert.equal(calls.length,1);assert.equal(calls[0].options.isCurrent(),true);
 // A section jump keeps the same article alive; leaving the guide invalidates it.
 assert.equal(calls[0].options.isCurrent(),true);article.isConnected=false;assert.equal(calls[0].options.isCurrent(),false);
 await G.bind(article,{isCurrent:()=>false});assert.equal(calls.length,1);
 if(prior===undefined)delete global.LineGapView;else global.LineGapView=prior;
 console.log('PASS: existing choice arithmetic, scoped line-gap delegation and removed-guide liveness. No targets or services.');
})().catch(e=>{console.error(e);process.exitCode=1});
