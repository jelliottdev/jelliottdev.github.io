/* Production coordinate arithmetic and DOM lifecycle; no browser or new measurements. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),api=require('../line-gap-view.js');
const fixture={schema:'liberpedia-line-gap-measurements-v1',rows:[{id:'lp2-04-text',page:'lp2-04',label:'LP2-04',rect_xyxy:[400,400,2000,1000],image_path:'images/lp2-04.jpg',width:2400,height:3600,lines:[{top:420,bottom:480},{top:590,bottom:650},{top:725,bottom:785}],gaps:[{from_line:1,to_line:2,top:481,bottom:589,pixels:109},{from_line:2,to_line:3,top:651,bottom:724,pixels:74}],overlay_path:'exports/line-gaps/lp2-04-text.svg'}]};
assert.equal(api.validate(fixture),fixture);const r=fixture.rows[0],svg=api.graphic(r,0,{});
assert(svg.includes('width="2400" height="3600"'));assert(svg.includes('481 V 589'));assert(svg.includes(' 480 H 2000'));assert(svg.includes(' 590 H 2000'));
const box=svg.match(/viewBox="([^"]+)"/)[1].split(' ').map(Number);assert.equal(box[2],625);assert(box[1]<420&&box[1]+box[3]>650);assert(svg.includes('109 original-image pixels'));
assert(!api.graphic(r,0,{guides:false}).includes('<path'));assert(api.graphic(r,0,{overview:true}).includes('viewBox="0 0 2400 3600"'));
assert(api.measurementHtml(r,1).includes('<strong>74 pixels</strong>'));assert(api.measurementHtml(r,0).includes('not screen pixels'));
assert(api.measurementHtml(r,0).includes('Space between lines'));assert(!api.measurementHtml(r,0).includes('Blank'));
assert.equal(api.widestGap({gaps:[{pixels:74},{pixels:110},{pixels:75}]}),1);assert.equal(api.widestGap({gaps:[{pixels:79},{pixels:79}]}),0);
for(const mutate of [d=>d.rows[0].gaps[0].pixels=110,d=>d.rows[0].gaps[0].from_line=0,d=>d.rows[0].image_path='https://bad/image.jpg',d=>d.rows[0].overlay_path='../bad.svg',d=>d.rows[0].lines[1].top=480]){const bad=structuredClone(fixture);mutate(bad);assert.throws(()=>api.validate(bad));}
const actual=path.join(root,'exports/line-gap-measurements.json');if(fs.existsSync(actual)){const data=api.validate(JSON.parse(fs.readFileSync(actual,'utf8')));const first=data.rows.find(r=>r.page==='lp2-04');assert(first.gaps.some(g=>g.pixels===109));assert(first.gaps.some(g=>g.pixels===74));for(const [id,pixels] of [['lp2-04',109],['lp2-35',110],['lp2-57',129],['lp2-15-panel',79]]){const row=data.rows.find(r=>r.id===id);assert.equal(row.gaps[api.widestGap(row)].pixels,pixels);}for(const row of data.rows)for(let i=0;i<row.gaps.length;i++)assert(api.graphic(row,i,{}).includes(row.image_path));}
function harness(){
 const timers=new Map(),c={module:{exports:{}},AbortController,setTimeout(fn,ms){assert.equal(ms,10000);timers.set(1,fn);return 1},clearTimeout(id){timers.delete(id)}};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(root,'line-gap-view.js'),'utf8'),c);
 const node=()=>({textContent:'',innerHTML:'',disabled:false,hidden:false,listeners:{},addEventListener(t,f){this.listeners[t]=f},focus(){doc.activeElement=this},setAttribute(k,v){this[k]=v}}),doc={activeElement:null};
 const status=node(),retry=node(),body=node(),nodes=new Map();retry.hidden=true;body.querySelector=s=>{if(!nodes.has(s))nodes.set(s,node());return nodes.get(s)};body.querySelectorAll=()=>[];
 const mount={isConnected:true,ownerDocument:doc,querySelector:s=>({'[data-gap-status]':status,'[data-gap-retry]':retry,'[data-gap-body]':body}[s])};let current=true;const requests=[];
 const options={isCurrent:()=>current,fetcher:(url,o)=>new Promise((resolve,reject)=>{assert.equal(url,'exports/line-gap-measurements.json');requests.push({resolve,reject,signal:o.signal})})};
 return {api:c.module.exports,mount,options,status,retry,body,nodes,requests,timers,doc,leave(){current=false},respond(data=fixture){requests.at(-1).resolve({ok:true,json:async()=>data})}};
}
(async()=>{
 const h=harness(),strip=h.body.querySelector('[data-gap-pairs]');strip.clientWidth=200;strip.querySelector=()=>({offsetLeft:500,offsetWidth:56});
 const load=h.api.bind(h.mount,h.options);h.respond();await load;assert(h.body.innerHTML.includes('Show whole page'));assert(h.nodes.get('[data-gap-measurement]').innerHTML.includes('109 pixels'));assert.equal(h.nodes.get('[data-gap-prev]').disabled,true);assert.equal(strip.scrollLeft,428,'Only the gap strip scrolls to center the chosen button');assert.equal(h.doc.activeElement,null,'Initial selection never moves focus');
 h.doc.activeElement=h.nodes.get('[data-gap-next]');h.nodes.get('[data-gap-next]').listeners.click();assert(h.nodes.get('[data-gap-measurement]').innerHTML.includes('74 pixels'));assert.equal(h.nodes.get('[data-gap-next]').disabled,true);assert.equal(h.doc.activeElement,h.nodes.get('[data-gap-prev]'),'Reaching an endpoint does not leave focus on a disabled control');
 for(const invalid of [false,true]){const s=harness(),p=s.api.bind(s.mount,s.options);s.leave();if(invalid)s.requests[0].reject(Error());else s.respond();await p;assert.equal(s.body.innerHTML,'');}
 const e=harness(),p=e.api.bind(e.mount,e.options);e.respond({});await p;assert(!e.retry.hidden);e.doc.activeElement=e.retry;const again=e.retry.listeners.click();e.respond();await again;assert(e.retry.hidden);assert.equal(e.doc.activeElement,e.nodes.get('[data-gap-region]'));
 const t=harness(),wait=t.api.bind(t.mount,t.options);[...t.timers.values()][0]();await wait;assert(t.requests[0].signal.aborted);assert(!t.retry.hidden);
 const css=fs.readFileSync(path.join(root,'style.css'),'utf8');assert(css.includes('.line-gap-pairs{position:relative;display:flex;gap:6px;overflow-x:auto'));assert(css.includes('min-height:44px'));assert(css.includes('.line-gap-measurement strong{font-size:28px'));
 console.log('PASS: original-coordinate crop/gap arithmetic, guides, receipt validation, selected-pair controls, bounded load/retry/stale guards. Source/DOM only.');
})().catch(e=>{console.error(e);process.exitCode=1});
