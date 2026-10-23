/* Optional reader data must not replace unchanged, keyboard-focused links. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..');
const page=JSON.parse(fs.readFileSync(path.join(root,'data/pages/lp1-04.json'),'utf8'));
const nodes=new Map(),context={localStorage:{getItem:()=>null},location:{hash:'#/reader/'+page.id},currentPage:page,
 db:{articles:[{id:'reading-'+page.reading.section}],payloads:{records:[]}},esc:String,link:p=>'#/page/'+p.id,partialDataNotice:()=>'',
 document:{activeElement:null,addEventListener(){},getElementById:id=>nodes.get(id),querySelector:()=>null}};
function node(){
 let html='',anchors=[];
 return {writes:0,get innerHTML(){return html},set innerHTML(value){
  html=value;this.writes++;for(const anchor of anchors)anchor.isConnected=false;
  if(anchors.includes(context.document.activeElement))context.document.activeElement=null;
  anchors=[...value.matchAll(/<a href="([^"]+)"/g)].map(([,href])=>({href,isConnected:true,focus(){context.document.activeElement=this}}));
 },get anchors(){return anchors}};
}
context.document.createElement=()=>node();
const reading=node(),payload=node();nodes.set('reader-reading-links',reading);nodes.set('reader-payload-link',payload);
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'access.js'),'utf8'),context);
context.refreshReaderSupplementary();assert.equal(reading.anchors.length,3);reading.anchors[0].focus();
const focusedReading=context.document.activeElement;
context.db.payloads.records=[{page:page.id}];context.refreshReaderSupplementary();
assert.equal(context.document.activeElement,focusedReading,'Payload arrival must not replace an unchanged reading link');
assert.equal(reading.writes,1);assert.equal(payload.anchors.length,1);
payload.anchors[0].focus();const focusedPayload=context.document.activeElement;
for(let n=0;n<4;n++)context.refreshReaderSupplementary();
assert.equal(context.document.activeElement,focusedPayload,'Other optional completions leave the focused payload link intact');
assert.equal(reading.writes,1);assert.equal(payload.writes,1);
context.location.hash='#/reader/lp2-02';context.refreshReaderSupplementary();assert.equal(reading.writes,1,'Stale old-page state cannot refresh the new reader');
context.location.hash='#/research';context.refreshReaderSupplementary();assert.equal(payload.writes,1);
console.log('PASS: initial reading/payload links appear, later optional completions preserve link nodes and focus, stale routes remain untouched. DOM-only, no rendered layout claim.');
