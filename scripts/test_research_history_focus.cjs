/* Classic history entry identity gates record-focus restoration. No browser. */
const assert=require('node:assert/strict'),Index=require('../research-index.js');
const document={activeElement:null};
let key='#/research?q=prime&sort=recent&page=2',nodes=[];
function record(id){return {isConnected:true,getAttribute:name=>name==='href'?'#/experiments/'+id:null,closest(){return this},
 focus(options){this.focusOptions=options;document.activeElement=this}};}
const index={dataset:{get researchState(){return key}},contains:node=>nodes.includes(node),querySelectorAll:()=>nodes};
const main={ownerDocument:document,querySelector:selector=>selector==='.research-index'?index:null,focus(){document.activeElement=this}};
const history={state:{unrelated:'preserved'},replaceState(state){this.state=state}};
main.focus();assert.equal(Index.restoreHistoryFocus(main,history),false,'First visit keeps main focus');
assert.equal(document.activeElement,main);assert.equal(history.state.unrelated,'preserved');const firstEntry=history.state;
nodes=[record('record-a'),record('record-b')];nodes[1].focus({preventScroll:true});Index.remember(main,840);
assert.equal(Index.position(main),840);
// A genuine fragment push clears classic state; a fresh same-URL visit must not restore old focus.
history.state=null;main.focus();assert.equal(Index.restoreHistoryFocus(main,history),false);
assert.equal(document.activeElement,main);assert.notDeepEqual(history.state,firstEntry,'Fresh entry gets a separate token even at the same query URL');
// Returning restores the recognized entry/token, then the still-present result after rerender.
history.state=firstEntry;nodes=[record('record-a'),record('record-b')];main.focus();
assert.equal(Index.restoreHistoryFocus(main,history),true);assert.equal(document.activeElement,nodes[1]);
assert.deepEqual(nodes[1].focusOptions,{preventScroll:true});assert.equal(Index.position(main),840,'Focus restoration never changes the saved viewport');
// Another pagination/filter state must not inherit that result target.
key='#/research?q=prime&sort=recent&page=3';main.focus();assert.equal(Index.restoreHistoryFocus(main,history),false);
assert.equal(document.activeElement,main);
// Filters replace the same entry and preserve its token; saved focus is associated with the new exact state.
key='#/research?q=feedback&type=method';history.replaceState({...history.state,filterState:'kept'});nodes=[record('record-c')];nodes[0].focus({preventScroll:true});Index.remember(main,360);
main.focus();assert.equal(Index.restoreHistoryFocus(main,history),true);assert.equal(document.activeElement,nodes[0]);assert.equal(history.state.filterState,'kept');
// A removed result, disconnected link or non-record focus safely falls back to main.
main.focus();nodes=[];assert.equal(Index.restoreHistoryFocus(main,history),false);assert.equal(document.activeElement,main);
nodes=[record('record-c')];nodes[0].isConnected=false;assert.equal(Index.restoreHistoryFocus(main,history),false);
nodes[0].isConnected=true;document.activeElement={closest:()=>null};Index.remember(main,370);main.focus();
assert.equal(Index.restoreHistoryFocus(main,history),false);assert.equal(Index.position(main),370);
// Unrecognized state from an earlier page session is not assumed to be a known return.
const oldHistory={state:{__liberpediaResearchEntry:'old-session',other:2},replaceState(state){this.state=state}};
assert.equal(Index.restoreHistoryFocus(main,oldHistory),false);assert.equal(oldHistory.state.other,2);
for(const state of ['external-state',[],14])assert.equal(Index.restoreHistoryFocus(main,{state,replaceState(){throw Error('Do not overwrite non-object state')}}),false);
assert.equal(Index.restoreHistoryFocus(main,{state:null,replaceState(){throw Error('History unavailable')}}),false);
console.log('PASS: recognized-entry-only return focus, fresh same-URL fallback, exact filter/pagination state, scroll preservation, missing targets and safe history failures. DOM-only, no rendered claim.');

// Exercise the production route hook, rather than only testing the helper API.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');
const routeDoc={activeElement:null,body:{classList:{toggle(){},remove(){}}},querySelectorAll:()=>[],getElementById:()=>null};
const routeHistory={state:null,replaceState(value){this.state=value}};let showingIndex=false,currentLink;
const query='#/research?q=router-fixture';
const routeIndex={dataset:{researchState:query},contains:node=>node===currentLink,querySelectorAll:()=>currentLink?[currentLink]:[]};
const routeMain={ownerDocument:routeDoc,get innerHTML(){return showingIndex?'Research index':'Record'},
 set innerHTML(value){showingIndex=value==='Research index';},
 querySelector:selector=>selector==='.research-index'?(showingIndex?routeIndex:null):selector==='h1'?{textContent:'Reference'}:null,
 focus(){routeDoc.activeElement=this}};
const routeContext={ResearchIndex:Index,URLSearchParams,db:{},renderId:0,optionalLoads:{},unavailableData:{},
 document:routeDoc,main:routeMain,history:routeHistory,location:{hash:query},esc:String,
 window:{scrollY:620,scrollTo(x,y){this.lastScroll=y}},closeSearchSuggestions(){},setNavigation(){},stopExperimentAI(){},
 researchIndexPage:async()=>{routeMain.innerHTML='Research index';currentLink={isConnected:true,getAttribute:()=> '#/experiments/router-record',closest(){return this},focus(options){this.focusOptions=options;routeDoc.activeElement=this}};},
 experimentsPage:async()=>{routeMain.innerHTML='Record'}};
vm.createContext(routeContext);vm.runInContext(app.slice(app.indexOf('function requireStartupData('),app.indexOf('\nconst optionalStartupData=')),routeContext);
(async()=>{
 await routeContext.route();const entry=routeHistory.state;assert.equal(routeDoc.activeElement,null,'Initial fresh visit does not force result focus');
 currentLink.focus({preventScroll:true});routeContext.location.hash='#/experiments/router-record';routeHistory.state=null;await routeContext.route();
 routeContext.location.hash=query;routeHistory.state=entry;await routeContext.route();
 assert.equal(routeDoc.activeElement,currentLink,'Actual router restores the departed result on a recognized entry return');
 assert.deepEqual(currentLink.focusOptions,{preventScroll:true});assert.equal(routeContext.window.lastScroll,620);
 routeHistory.state=null;await routeContext.route();assert.equal(routeDoc.activeElement,routeMain,'Fresh same-URL route retains main focus');
 console.log('PASS: production router/index handoff restores result focus only for history return and preserves its saved scroll.');
})().catch(error=>{console.error(error);process.exitCode=1});
