/* Actual router regression: changing destinations dismisses an old image modal. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),source=fs.readFileSync(path.join(root,'app.js'),'utf8');
const start=source.indexOf('function requireStartupData('),end=source.indexOf('\nconst optionalStartupData=',start);
const events=[],dialog={open:true,close(){events.push('close');this.open=false}};
const context={URLSearchParams,db:{},renderId:1,optionalLoads:{},unavailableData:{},esc:String,
 location:{hash:'#/overview'},ResearchIndex:require('../research-index.js'),
 head:title=>'<h1>'+title+'</h1>',closeSearchSuggestions(){},setNavigation(){},stopExperimentAI(){},overview:()=>'<h1>New destination</h1>',
 window:{scrollY:0,scrollTo(){}},
 document:{body:{classList:{toggle(){},remove(){}}},getElementById:id=>id==='image-dialog'?dialog:null,querySelectorAll:()=>[]},
 main:{innerHTML:'',querySelector:()=>({textContent:'New destination'}),focus(){events.push('focus')}}};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
(async()=>{
 await context.route();assert.equal(dialog.open,false,'Navigation must not leave the old manuscript image over the new destination');
 assert.equal(events[0],'close');assert.equal(events.at(-1),'focus','The new route receives focus after the old modal closes');
 events.length=0;context.location.hash='#/missing';await context.route();assert(!events.includes('close'),'An already closed modal is left alone');
 assert(context.main.innerHTML.includes('Page not found'));
 console.log('PASS: actual router dismisses stale modal before rendering/focusing new destination; closed modal is untouched.');
})().catch(error=>{console.error(error);process.exitCode=1});
