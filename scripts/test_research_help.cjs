const assert=require('node:assert/strict'),Help=require('../research-help.js'),F=require('../record-followup-view.js'),registry=require('../data/experiments.json');
const records=Object.fromEntries(registry.records.map(r=>[r.id,r])),before=JSON.stringify(records),groups=Help.choices(records),html=Help.render(records);
assert(groups.length>0);assert.equal(JSON.stringify(records),before);
assert(html.includes('No theory or coding needed'));assert(html.includes('may already be complete'));
for(const {record,checks} of groups){assert.deepEqual(checks,F.available(record));assert(html.includes('run.html#record='+record.id+'&amp;followup='+checks[0].id));}
const original=groups.find(g=>g.checks.length>1),elements=new Map(),get=key=>{if(!elements.has(key))elements.set(key,{});return elements.get(key);},index=groups.indexOf(original),element={dataset:{helpCheck:String(index)},querySelector:get};
Help.bind({querySelectorAll:()=>[element]},records);const select=get('select'),last=original.checks.at(-1);select.value=last.id;select.onchange();assert.equal(get('[data-help-question]').textContent,last.question);assert.equal(get('[data-help-review]').href,'run.html#record='+original.record.id+'&followup='+last.id);select.value='unknown';select.onchange();assert.equal(select.value,last.id,'Unknown choices cannot change the source-bound destination');
assert.equal(Help.choices({...records,bogus:{id:'bogus',community:true,browser_followups:original.checks}}).length,groups.length);
assert(Help.render({}).includes('No maintained browser checks'));assert(!Help.render({}).includes('run.html#'));
const altered=structuredClone(records);altered[groups[0].record.id].title='<img src=x onerror=alert(1)>';assert(!Help.render(altered).includes('<img'));assert(Help.render(altered).includes('&lt;img'));
console.log('PASS maintained discovery, exact review links, selection, unavailable work, escaping and immutable source');
