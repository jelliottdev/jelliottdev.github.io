/* Local CUA-only QA server. Replaces only inference through createApp injection.
   No production source/data changes and no outbound model request. */
'use strict';
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const qa=`window.__investigateMock=async function(url,options){
 if(!String(url).startsWith('https://'))return fetch(url,options);
 const mode=new URLSearchParams(location.search).get('qa');
 if(mode==='offline')return Response.json({error:'Mock outage'},{status:503});
 if(mode==='empty')return Response.json({answer:null,sources:[],reason:'no-matching-records'});
 if(mode==='delay')await new Promise((resolve,reject)=>{let t=setTimeout(resolve,10000);options.signal.addEventListener('abort',()=>{clearTimeout(t);reject(new DOMException('Canceled','AbortError'));});});
 const registry=await (await fetch('data/experiments.json')).json();
 const request=JSON.parse(options.body),docs=AssistantSearch.experimentDocs(registry.records);
 const selected=AssistantSearch.select(docs,request.query,request.pages).filter(d=>d.kind==='experiment').slice(0,1);
 if(!selected.length)return Response.json({answer:null,sources:[],reason:'no-matching-records'});
 const record=registry.records.find(r=>r.id===selected[0].id);
 if(mode==='changed')selected[0].text+=' changed';
 return Response.json({answer:(record.reader_finding||record.finding)+' [1].\\n\\n'+(record.reader_limit||record.limitations)+' [1].',sources:selected});
};`;
http.createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost');
 if(url.pathname==='/__qa.js'){res.setHeader('Content-Type','text/javascript');res.end(qa);return;}
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
  const types={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'};
  res.setHeader('Content-Type',(types[path.extname(file)]||'application/octet-stream')+'; charset=utf-8');res.end(bytes);
 }catch{res.writeHead(404).end();}
}).listen(4397,'127.0.0.1',()=>console.log('Mock-only investigate QA: http://127.0.0.1:4397/investigate.html'));
