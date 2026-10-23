/* Browser-free breakpoint regression: preserve the passage currently being used. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
let onChange;
const focus={id:'focused-control'},target={id:'nested-passage'};
const section=(open,members=[])=>({open,contains:node=>members.includes(node)});
let sections=[];
const context={URLSearchParams,location:{hash:'#/wiki/example?section=nested-passage'},
 window:{matchMedia:()=>({addEventListener(type,fn){assert.equal(type,'change');onChange=fn}})},
 document:{activeElement:focus,querySelectorAll:()=>sections,getElementById:id=>id===target.id?target:null,addEventListener(){}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'..','wiki.js'),'utf8'),context);
sections=[section(true),section(true),section(true,[focus]),section(true,[target])];
onChange({matches:true});
assert.deepEqual(sections.map(s=>s.open),[true,false,true,true],
 'Entering mobile keeps the first section and sections containing current focus or a nested deep-link target open');
sections=[section(false),section(false,[target]),section(true)];context.document.activeElement=null;
onChange({matches:true});
assert.deepEqual(sections.map(s=>s.open),[false,false,false],
 'A deliberately closed section is not reopened by a stale URL target or first-section default');
context.location.hash='#/wiki/example?section=missing';sections=[section(true),section(true)];
onChange({matches:true});assert.deepEqual(sections.map(s=>s.open),[true,false]);
onChange({matches:false});assert(sections.every(s=>s.open),'Returning to desktop retains the expanded article behavior');
sections=[];onChange({matches:true});
console.log('PASS: mobile breakpoint retains active and deep-linked passages, respects closed sections, handles missing targets, and preserves desktop expansion. DOM stubs do not verify rendering.');
