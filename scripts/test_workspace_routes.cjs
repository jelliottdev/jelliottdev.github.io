const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const routes=require('../workspace-routes.js');
assert.equal(routes.destination('#/reader/lp2-15?view=text&line=4-8'),'reader.html#lp2-15?view=text&line=4-8');
assert.equal(routes.destination('#/experiments?q=autokey%20LP2-15'),'investigate.html?q=autokey%20LP2-15');
for(const route of ['#/experiments?browse=prime','#/experiments?section=browse-experiments','#/experiments/word-internal-affine-lags','#/research','#/wiki/line-gaps','#/reader/../../bad'])assert.equal(routes.destination(route),null);
for(const route of ['', '#/', '#/overview'])assert.equal(routes.destination(route),'home.html');
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

// Validate actual entry markup, not only the JS modules used by the VM tests.
const checkerHTML=fs.readFileSync(require.resolve('../investigate.html'),'utf8');
const checkerScripts=[...checkerHTML.matchAll(/<script\b([^>]*)>/g)].map(([,attributes])=>{
 const src=attributes.match(/\bsrc="([^"<>\r\n]+)"/);
 assert(src,'Each checker script needs a closed, quoted source attribute: '+attributes);
 assert(!/[<>]/.test(attributes),'A malformed attribute must not consume the next script');
 const filename=src[1].split('?')[0];
 assert(fs.existsSync(require.resolve('../'+filename)),'Entry dependency exists: '+filename);
 return filename;
});
assert.deepEqual(checkerScripts,['claim-specification.js','claim-share.js','claim-research.js','claim-interpretation.js','assistant-search.js','assistant-markdown.js','recorded-comparison.js','investigate.js'],'The formatter and all dependencies must load before the checker');
console.log('PASS: checker entry script attributes, dependency paths and load order.');
