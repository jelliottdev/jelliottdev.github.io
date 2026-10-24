/* Local CUA-only QA server. Replaces only inference through createApp injection.
   No production source/data changes and no outbound model request. */
'use strict';
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
// Optional local receipt replay: no provider call and no replacement evidence.
const receipt=process.env.CLAIM_QA_RECEIPT?JSON.parse(fs.readFileSync(path.resolve(process.env.CLAIM_QA_RECEIPT),'utf8')):null;
const qa=`window.__investigateMockCore=async function(url,options){
 const proposalMode=new URLSearchParams(location.search).get('qa');
 if(url==='data/assistant.json')return Response.json({endpoint:'https://mock.example/ask',researchContract:'card-v1',interpretationEndpoint:proposalMode?.startsWith('interpret')?'https://mock.example/interpret':null,proposalEndpoint:proposalMode?.startsWith('intake-')?'https://mock.example/proposals':null});
 if(url==='https://mock.example/interpret'){
  if(proposalMode==='interpret-error')return Response.json({error:'Mock interpretation outage'},{status:503});
  const text=JSON.parse(options.body).text,source=quote=>({start:text.indexOf(quote),quote});
  const known=text==='Try reversing rune order within each row on LP2-15, preserving word boundaries.';
  const candidate={schema:ClaimInterpretation.SCHEMA,outcome:null,steps:[{id:known?'reverse_row_runes':'described_method',familyId:known?'transposition':null,source:source(text),parameters:{}}],scope:known?{pages:['lp2-15'],passage:null,source:source('LP2-15')}:null,rules:known?{wordBoundaries:{status:'specified',value:'preserve',source:source('preserving word boundaries')}}:{}};
  if(proposalMode==='interpret-reset'&&text==='Use Vigenere with key ABC. Reset the key at each word.')candidate.rules.reset={status:'specified',value:'Reset the key at each word.',source:source('Reset the key at each word.')};
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Response.json({candidate,sourceBinding:[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('')});
 }
 if(url==='https://mock.example/proposals'&&proposalMode==='intake-error')return Response.json({error:'Mock-only save unavailable'},{status:503});
 if(url==='https://mock.example/proposals')return Response.json({id:'p_'+'c'.repeat(64),status:'received',receivedAt:new Date().toISOString()});
 if(!String(url).startsWith('https://'))return fetch(url,options);
 const mode=new URLSearchParams(location.search).get('qa');
 if(mode==='receipt'){
  const response=await fetch('/__receipt.json');if(!response.ok)return Response.json({error:'No local QA receipt configured'},{status:503});
  const receipt=await response.json(),sent=ClaimResearch.validate(JSON.parse(options.body)).request.card,expected=ClaimResearch.validate(receipt.request).request.card;
  if(ClaimSpecification.serialize(sent)!==ClaimSpecification.serialize(expected))return Response.json({error:'Local receipt card mismatch'},{status:400});
  return Response.json(receipt.result);
 }
 if(mode==='offline')return Response.json({error:'Mock outage'},{status:503});
 if(mode==='empty')return Response.json({answer:null,sources:[],reason:'no-matching-records'});
 if(mode==='delay')await new Promise((resolve,reject)=>{let t=setTimeout(resolve,10000);options.signal.addEventListener('abort',()=>{clearTimeout(t);reject(new DOMException('Canceled','AbortError'));});});
 const registry=await (await fetch('data/experiments.json')).json();
 const raw=JSON.parse(options.body),request=raw.version===1?ClaimResearch.validate(raw):raw,docs=AssistantSearch.experimentDocs(registry.records);
 if(mode==='recorded'){
  const recorded=request.snapshot&&RecordedComparison.compare({snapshot:request.snapshot,documents:docs});
  return Response.json(recorded||{error:'The local fixture does not match the reviewed operation.'},{status:recorded?200:400});
 }
 const selected=AssistantSearch.select(docs,request.query,request.pages,request.discovery).filter(d=>d.kind==='experiment');
 if(!selected.length)return Response.json({answer:null,sources:[],reason:'no-matching-records'});
 const record=registry.records.find(r=>r.id===selected[0].id);
 if(mode==='changed')selected[0].text+=' changed';
 return Response.json({answer:(record.reader_finding||record.finding)+' [1].\\n\\n'+(record.reader_limit||record.limitations)+' [1].',sources:selected});
};
window.__investigateMock=async function(url,options){
 const response=await window.__investigateMockCore(url,options);
 if(url==='https://mock.example/ask'&&JSON.parse(options.body).version===1){
  const payload=await response.json();return Response.json({...payload,claimBinding:await ClaimResearch.binding(JSON.parse(options.body))},{status:response.status});
 }
 return response;
};`;
http.createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost');
 if(url.pathname==='/__qa.js'){res.setHeader('Content-Type','text/javascript');res.end(qa);return;}
 if(url.pathname==='/__receipt.json'){
  if(!receipt){res.writeHead(404).end();return;}
  res.setHeader('Content-Type','application/json; charset=utf-8');res.end(JSON.stringify(receipt));return;
 }
 if(url.pathname==='/__receipt-card.html'){
  if(!receipt){res.writeHead(404).end();return;}
  const H=require('../claim-share.js'),R=require('../claim-research.js'),href='investigate.html?qa=receipt'+H.encode(R.validate(receipt.request).snapshot);
  res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local receipt replay</title><style>body{font:16px/1.6 Arial;margin:24px}a{display:inline-block;padding:12px}</style><p>Local saved-response replay; no model call. Saved answer and evidence text are replayed unchanged.</p><a href="'+href+'">Review saved-response idea</a>');return;
 }
 if(url.pathname==='/__share-card.html'){
  const C=require('../claim-specification.js'),H=require('../claim-share.js'),known=value=>C.field('specified',value,{kind:'supplied',refs:['local QA fixture']});
  const spec=C.confirm(C.createDraft({source:{text:'Private original wording is excluded from the shared card.'},aim:known({outcomeId:'decipher',detail:'Recover readable text with the two steps below'}),method:known({operations:[{id:'reverse_row_runes',label:'Reverse rune order within rows'},{id:'vigenere',label:'Apply Vigenere with key FIRFUMFERENFE',key:'FIRFUMFERENFE',offset:7}]}),scope:known({pages:['lp2-15','lp2-16','lp2-17'],description:'Only the visible rune text'}),rules:{wordBoundaries:known('preserve'),boundaryMode:known('within_words'),reset:known('Restart on each page')}}),{id:'local-share-qa',at:'2026-10-24T12:00:00Z'});
  res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local card export QA</title><style>body{margin:24px;font:16px Arial;background:#eef1f3}img{display:block;max-width:100%;width:540px;height:auto;margin-top:20px;background:white}a{display:inline-block;padding:12px;background:white}</style><a href="investigate.html'+H.encode(spec)+'">Open shared idea for review</a><p id="status">Rendering card…</p><img id="card" alt="Standardized idea image exported by the production renderer"><script src="claim-specification.js"></script><script src="claim-share.js"></script><script>ClaimShare.renderPNG('+JSON.stringify(spec).replace(/</g,'\\u003c')+').then(blob=>{document.getElementById("card").src=URL.createObjectURL(blob);document.getElementById("status").textContent="Production PNG rendered locally; no native sharing."}).catch(error=>document.getElementById("status").textContent=error.message)</script>');return;
 }
 const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
 if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
 try{
  let bytes=fs.readFileSync(file);
  if(url.pathname==='/investigate.html')bytes=Buffer.from(bytes.toString().replace(/<script src="investigate\.js(?:\?[^"]*)?">/,tag=>'<script src="/__qa.js"></script>'+tag));
  if(url.pathname==='/investigate.js')bytes=Buffer.from(bytes.toString().replace('createApp(root.document);',"createApp(root.document,{fetcher:root.__investigateMock||(()=>Promise.reject(Error('QA mock unavailable; network disabled')))});"));
  const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.woff2':'font/woff2'};
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(bytes);
 }catch{res.writeHead(404).end();}
}).listen(Number(process.env.PORT||4397),'127.0.0.1',()=>console.log('Mock-only investigate QA: http://127.0.0.1:'+(process.env.PORT||4397)+'/investigate.html'));
