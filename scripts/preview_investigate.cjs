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
