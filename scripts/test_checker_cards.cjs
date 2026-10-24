/* Reader-facing card content and primary navigation; no browser/model requests. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),records=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'))).records;
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context={esc};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'experiments.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'assistant-ui.js'),'utf8'),context);
const labels={supported:'Supported within scope','not-supported':'Not supported within scope',inconclusive:'Inconclusive'};
for(const record of records){
 const html=context.experimentSearchResult(record,['lp2-31','lp2-56']);
 const links=[...html.matchAll(/<a href="([^"]+)">([\s\S]*?)<\/a>/g)];
 assert.equal(links.length,1,'One keyboard destination per card: '+record.id);
 assert.equal(links[0][1],'#/experiments/'+record.id);assert.equal(links[0][2],esc(record.title));
 assert(html.includes('<h3><a '),'The meaningful record title is the primary link');
 assert(html.includes(labels[record.outcome]),'The recorded outcome stays visible: '+record.id);
 assert(html.includes(esc(record.reader_finding||record.finding)),'Finding remains complete');
 if(record.reader_limit)assert(html.includes('<strong>Limit:</strong> '+esc(record.reader_limit)));
 for(const page of ['lp2-31','lp2-56'].filter(id=>!record.scope.pages.includes(id)))assert(html.includes(page.toUpperCase()),'Requested scope mismatch remains visible');
}
const fixture={...records[0],id:'card-fixture',title:'Long <img src=x> & title',reader_finding:'Clear <result>',reader_limit:'A narrow <limit>',outcome:'constructor'};
const html=context.experimentSearchResult(fixture);assert(!html.includes('<img'));assert(html.includes('&lt;img src=x&gt;'));
assert(html.includes('Finding not classified'),'Unknown labels cannot expose inherited object properties');
assert(html.includes(esc(fixture.reader_finding)));assert(html.includes(esc(fixture.reader_limit)));
const css=fs.readFileSync(path.join(root,'style.css'),'utf8');
const headingRule=css.match(/\.experiment-result h3 a\{([^}]+)\}/)?.[1]||'';
assert(headingRule.includes('display:block'));assert(headingRule.includes('min-height:44px'));assert(headingRule.includes('overflow-wrap:anywhere'));
// The form's ID selector used to override the action group's 44px rule with 42px.
// Compare the actual competing declarations rather than accepting a lower-priority match.
const actionRules=[...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].flatMap((match,index)=>
 match[1].split(',').map(selector=>({selector:selector.trim(),body:match[2],index}))
).filter(rule=>['#experiment-form button','.idea-actions button'].includes(rule.selector)&&/min-height:/.test(rule.body));
actionRules.sort((a,b)=>Number(b.selector.includes('#'))-Number(a.selector.includes('#'))||b.index-a.index);
assert.equal(actionRules[0].body.match(/min-height:([^;}]*)/)?.[1],'44px','The highest-priority checker action rule must retain the intended touch target');
const indexLinkRule=css.match(/\.idea-index-link a\{([^}]+)\}/)?.[1]||'';
assert(indexLinkRule.includes('display:inline-flex')&&indexLinkRule.includes('min-height:44px'),'The directory link matches the reciprocal research action target');
console.log(`PASS: ${records.length} cards each expose one meaningful record link, visible outcome/finding/curated limit/scope, escaped text and a source-defined 44px wrapping title target. No rendered layout claim.`);
