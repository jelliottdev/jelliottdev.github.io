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

// Automatic provenance/tool/navigation panels must not reappear below authored prose.
const authored='<p>Measured finding with an <a href="#/experiments/example">inline source</a>.</p>';
context.db={articles:[{id:'example',title:'Example',summary:'Summary',category:'Analysis and reproduction',html:authored,pages:['lp2-04']},{id:'backlink',linked_articles:['example']}],guideCategories:[]};
context.DOMParser=class{parseFromString(){return {body:{children:[],innerHTML:authored},querySelectorAll(){return []}}}};
context.head=()=>'<header>Example</header>';context.esc=String;
context.footer=()=>'<footer>Source snapshot: repeated footer</footer>';
const rendered=vm.runInContext("wikiPage('example')",context);
assert(rendered.includes(authored),'Authored findings and contextual source links remain');
assert(!/article-tools|article-related|Source snapshot|Page tools|Related pages and guides/.test(rendered),'No automatic article-end boilerplate');
console.log('PASS: wiki articles preserve authored sources without automatic related/tool/provenance panels.');
