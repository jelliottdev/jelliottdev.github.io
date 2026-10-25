const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),Context=require('../followup-context.js'),View=require('../record-followup-view.js');
for(const value of ['A source explanation.','😀'.repeat(500),'Spaces, slashes and line breaks separate words.'])assert(Context.valid(value));
for(const value of [null,[],{},'',1,' leading','trailing ','😀'.repeat(501),'<b>text</b>','[link]','a`b','a*b','a\\b','a\nb','a\u0000b','a\u0085b','a\u2028b','a\u2029b','a\ud800b'])assert(!Context.valid(value),String(value));
const record=JSON.parse(fs.readFileSync(require.resolve('../experiments/records/word-internal-affine-lags/record.json'),'utf8')),before=JSON.stringify(record);assert.equal(View.recipes(record).length,2);for(const motivation of ['',null,'<script>']){const changed=structuredClone(record);changed.browser_followups[0].motivation=motivation;assert.equal(View.recipes(changed).length,1);}assert.equal(JSON.stringify(record),before);
const legacy=structuredClone(record);delete legacy.browser_followups[0].motivation;assert.equal(View.recipes(legacy).length,2);
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync(require.resolve('../followup-context.js'),'utf8'),ctx);ctx.value='😀'.repeat(500);assert.equal(vm.runInContext('FollowupContext.valid(value)',ctx),true);
for(const name of ['run.html','research.html','index.html','library.html']){const html=fs.readFileSync(require.resolve('../'+name),'utf8'),consumer=name==='run.html'?'record-followups.js':'record-followup-view.js';assert(html.indexOf('followup-context.js')<html.indexOf(consumer),'Context must load before its consumer: '+name);assert.equal(html.split('src="followup-context.js').length-1,1);}
console.log('PASS shared context validation, strict source rejection, legacy recipes, Unicode, browser export and loader order');

for(const name of ['index.html','library.html','research.html']){
 const html=fs.readFileSync(require.resolve('../'+name),'utf8');
 const scripts=['claim-specification.js','claim-share.js','finite-settings.js','record-question-model.js','record-followup-view.js'];
 let previous=-1;
 for(const script of scripts){const at=html.indexOf('src="'+script);assert(at>previous,'Finite recipe dependency order: '+name+' '+script);assert.equal(html.split('src="'+script).length-1,1);previous=at;}
}
