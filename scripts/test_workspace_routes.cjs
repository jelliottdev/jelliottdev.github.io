const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const routes=require('../workspace-routes.js');
assert.equal(routes.destination('#/reader/lp2-15?view=text&line=4-8'),'reader.html#lp2-15?view=text&line=4-8');
assert.equal(routes.destination('#/experiments?q=autokey%20LP2-15'),'investigate.html?q=autokey%20LP2-15');
for(const route of ['#/experiments?browse=prime','#/experiments?section=browse-experiments','#/experiments/word-internal-affine-lags','#/research','#/wiki/line-gaps','#/reader/../../bad'])assert.equal(routes.destination(route),null);
const app=fs.readFileSync(require('node:path').join(__dirname,'../app.js'),'utf8');
const slice=app.slice(app.indexOf('function requireStartupData('),app.indexOf('\nconst optionalStartupData='));
let resolveMap,mounts=0;
const context={URLSearchParams,db:{},renderId:0,optionalLoads:{},unavailableData:{},esc:String,
 location:{hash:'#/research-map'},ResearchIndex:require('../research-index.js'),
 head:t=>'<h1>'+t+'</h1>',closeSearchSuggestions(){},setNavigation(){},stopExperimentAI(){},overview:()=>'<h1>Home</h1>',
 window:{scrollY:0,scrollTo(){}},history:{replaceState(){}},
 fetchStartupJson:()=>new Promise(r=>resolveMap=r),WikiResearchMap:{mount(){mounts++;return {destroy(){}}}},
 document:{body:{classList:{toggle(){},remove(){}}},getElementById:()=>null,querySelectorAll:()=>[]},
 main:{innerHTML:'',querySelector:()=>({textContent:'Home'}),focus(){}}};
vm.createContext(context);vm.runInContext(slice,context);
(async()=>{
 const pending=context.route();await new Promise(r=>setImmediate(r));
 context.location.hash='#/overview';await context.route();resolveMap({});await pending;
 assert.equal(mounts,0,'A slow map fetch must not replace a newer route');
 assert.match(context.main.innerHTML,/Home/);
 console.log('PASS: legacy deep links preserve query/record routes; stale map fetch cannot replace a later destination.');
})().catch(e=>{console.error(e);process.exitCode=1});
