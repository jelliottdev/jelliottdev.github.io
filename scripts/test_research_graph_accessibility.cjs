/* Real production renderer, sharing the SVG fixture used by graph interaction tests. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const fixtureSource=fs.readFileSync(require.resolve('./test_research_graph_controller.cjs'),'utf8');
const marker='{const f=fixture(),before=JSON.stringify([...f.c.nodes]);';
const at=fixtureSource.indexOf(marker);assert(at>0,'The maintained graph fixture is available before its test cases');
const sandbox={require};vm.createContext(sandbox);vm.runInContext(fixtureSource.slice(0,at)+'\nglobalThis.graphFixture=fixture;',sandbox);
const fixture=options=>sandbox.graphFixture(options);
function exposed(f){return [...f.groups].filter(([,el])=>el.getAttribute('aria-hidden')!=='true');}
function check(f){
 for(const [id,el]of f.groups){const actionable=el.getAttribute('tabindex')==='0';assert.equal(el.getAttribute('aria-hidden'),String(!actionable),id+' must expose exactly the current keyboard target');assert.equal(el.getAttribute('role')==='button',actionable,id+' must retain its button role');assert.equal(el.group.getAttribute('aria-hidden'),'true','The separately drawn label never creates a duplicate accessible target');}
}
let groups=0;
for(const width of [320,390,768,1440]){
 const f=fixture({width,height:700,real:true,focus:'all-research'});
 assert(f.groups.size>300);assert.equal(exposed(f).length,0,'New DOM nodes start hidden until camera/reveal resolves');
 f.c.fit();check(f);const active=exposed(f);assert(active.length>0&&active.length<10,'Overview exposes the next branches, not the complete archive');for(const [id]of active)assert.equal(f.c.nodes.get(id).parent,'all-research');
 const before=JSON.stringify([...f.c.nodes]);f.c.camera.k=1.2;f.c.applyCamera();check(f);assert.equal(JSON.stringify([...f.c.nodes]),before,'Accessibility updates do not alter navigation ancestry or records');groups++;
}
{
 const f=fixture();f.c.camera.k=1.2;f.c.applyCamera();check(f);const deep=exposed(f).find(([id])=>id.startsWith('leaf'));assert(deep,'Zoomed visible deep label becomes one accessible keyboard target');
 f.c.document.activeElement=deep[1];f.c.camera.k=.5;f.c.applyCamera();check(f);assert.equal(deep[1].getAttribute('aria-hidden'),'true');assert.equal(f.c.document.activeElement,f.c.map,'A hidden deep target releases focus to the graph without scrolling');assert.equal(f.c.map.focusOptions.preventScroll,true);
 const child=f.groups.get('branch');assert.equal(child.getAttribute('aria-hidden'),'false');f.c.document.activeElement=child;f.c.applyCamera();assert.equal(f.c.document.activeElement,child,'A still actionable branch keeps keyboard focus');
 f.c.camera.x=-10000;f.c.applyCamera();check(f);assert.equal(exposed(f).length,0,'Panned-offscreen targets leave both keyboard and accessibility trees');groups++;
}
{
 const f=fixture({width:10,height:10});f.c.applyCamera();check(f);assert.equal(exposed(f).length,0,'An unlaid-out/hidden viewport cannot expose the complete archive');groups++;
}
console.log(groups+' production graph accessibility groups passed: next-level targets only, initial hidden DOM, deep zoom reveal/hide, retained navigation/focus, offscreen and zero-size states.');
