'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{execFileSync}=require('node:child_process');
const {parseNameStatus,classifyChanges,scopeForCheckout,UI_PATHS}=require('./ci_validation_scope.cjs');
const registry=()=>({schema:'liberpedia-experiments-v1',records:[]}),catalog=()=>({schema:'liber-primus-file-catalog-v1',files:[]});
const entry=(name,status='M')=>({status,paths:[name]});let count=0;
function test(name,fn){fn();count++;console.log('PASS '+name);}
test('only exact reviewed UI paths bypass science; all mixed/unknown paths remain full',()=>{
 for(const p of ['app.js','investigate.js','style.css','data/assistant.json','scripts/test_investigate.cjs'])assert.equal(classifyChanges([entry(p)],registry(),catalog()).science,false,p);
 for(const p of ['articles/method-feedback.html','scripts/build_articles.py','scripts/test_experiments.py','experiments/records/x/record.json','data/pages/lp2-15.json','data/experiments.json','images/lp2-15.jpg','text/lp2-15.txt','exports/x.json','research/x.md','reference/x.html','downloads/x.zip','.gitattributes','.github/workflows/validate-experiments.yml','scripts/ci_validation_scope.cjs','scripts/test_ci_validation_scope.cjs','unknown.js','services/idea-assistant/worker.mjs'])assert.equal(classifyChanges([entry('app.js'),entry(p)],registry(),catalog()).science,true,p);
 assert.equal(classifyChanges([],registry(),catalog()).science,true);assert.equal(classifyChanges([entry('app.js','A')],registry(),catalog()).science,false);
});
test('word-sum clarification stays UI-only while execution and declared inputs stay full',()=>{
 const ui=['word-sum-intake.js','scripts/test_word_sum_intake.cjs','scripts/test_word_sum_intake_flow.cjs'];
 assert.equal(classifyChanges(ui.map(p=>entry(p,'A')),registry(),catalog()).science,false);
 for(const dependency of ['local-experiment.js','tools/research_runner.py','services/idea-assistant/prepare-task.mjs',
  'scripts/browser_followups.py','experiments/records/lp2-row-prime-sums/record.json','data/local-run-inputs.json'])
  assert.equal(classifyChanges([...ui.map(p=>entry(p)),entry(dependency)],registry(),catalog()).science,true,dependency);
 for(const name of ui){
  const c=catalog();c.files.push({path:name});assert.equal(classifyChanges([entry(name)],registry(),c).science,true,name);
  const r=registry();r.records.push({reproduction:{inputs:[{path:name}]}});assert.equal(classifyChanges([entry(name)],r,catalog()).science,true,name);
 }
 const workflow=fs.readFileSync(path.join(__dirname,'../.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n');
 for(const script of ['scripts/test_word_sum_intake.cjs','scripts/test_word_sum_intake_flow.cjs']){
  const block=workflow.split(/(?=^      - )/m).find(s=>s.includes('run: node scripts/run_node_checks.cjs\n'));
  const manifest=require('./run_node_checks.cjs').validateManifest(JSON.parse(fs.readFileSync(path.join(__dirname,'node-checks.json'),'utf8')));
  assert(block&&manifest.checks.some(c=>c.args.length===1&&c.args[0]===script),'The reviewed clarification must keep its unconditional Node check: '+script);
  assert(!/^        if:/m.test(block),'Frontend clarification tests cannot be gated by science scope');
 }
});
test('question presentation stays lightweight without exempting evaluation, evidence or declared sources',()=>{
 const ui=['index.html','library.html','library.css','library.js','record-question-view.js','record-question-view.css','scripts/test_record_question_view.cjs','scripts/test_record_question_mount.cjs'];
 assert.equal(classifyChanges(ui.map(p=>entry(p)),registry(),catalog()).science,false);
 for(const file of ['record-question-model.js','record-question-live.js','finite-question-policy.js','local-experiment.js','services/idea-assistant/record-plans.mjs','scripts/public_wordlist_followups.py','experiments/records/lp2-prime-openings/record.json'])
  assert.equal(classifyChanges([...ui.map(p=>entry(p)),entry(file)],registry(),catalog()).science,true,file);
 for(const file of ui){const c=catalog();c.files.push({path:file});assert.equal(classifyChanges([entry(file)],registry(),c).science,true,file);}
 const actualRegistry=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/experiments.json'),'utf8')),actualCatalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/catalog.json'),'utf8'));
 assert.equal(classifyChanges(ui.map(p=>entry(p)),actualRegistry,actualCatalog).science,false);
 const manifest=require('./run_node_checks.cjs').validateManifest(JSON.parse(fs.readFileSync(path.join(__dirname,'node-checks.json'),'utf8')));
 const workflow=fs.readFileSync(path.join(__dirname,'../.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n'),block=workflow.split(/(?=^      - )/m).find(s=>s.includes('run: node scripts/run_node_checks.cjs\n'));
 assert(block&&!/^        if:/m.test(block),'The Node suite remains unconditional');
 for(const script of ui.filter(p=>p.startsWith('scripts/')))assert(manifest.checks.some(item=>item.args.length===1&&item.args[0]===script),script+' still runs in the unconditional Node suite');
});

test('deletions, copies, renames and type changes always preserve full validation',()=>{
 for(const status of ['D','T','U','X','B'])assert.equal(classifyChanges([entry('app.js',status)],registry(),catalog()).science,true);
 for(const status of ['R100','C100'])assert.equal(classifyChanges([{status,paths:['app.js','home.js']}],registry(),catalog()).science,true);
});
test('registry scripts, inputs, outputs, artifacts and catalog dependencies override UI allowlist',()=>{
 for(const make of [()=>({reproduction:{script:'app.js'}}),()=>({reproduction:{inputs:[{path:'app.js'}]}}),()=>({reproduction:{outputs:[{path:'app.js'}]}}),()=>({scope:{artifacts:['app.js']}}),()=>({article_path:'app.js'})]){const r=registry();r.records.push(make());assert.equal(classifyChanges([entry('app.js')],r,catalog()).science,true);}
 const c=catalog();c.files.push({path:'style.css'});assert.equal(classifyChanges([entry('style.css')],registry(),c).science,true);
 for(const [r,c]of [[{},catalog()],[registry(),{}],[{schema:registry().schema,records:[{reproduction:{inputs:[{}]}}]},catalog()]])assert.equal(classifyChanges([entry('app.js')],r,c).science,true);
});
test('declared aliases, Windows separators/case and directories cannot bypass dependency guards',()=>{
 for(const alias of ['./home.js','.\\home.js','HOME.JS','././home.js']){const r=registry();r.records.push({scope:{artifacts:[alias]}});assert.equal(classifyChanges([entry('home.js')],r,catalog()).science,true,alias);}
 for(const directory of ['scripts','scripts/','./scripts/','.\\scripts\\']){const r=registry();r.records.push({scope:{artifacts:[directory]}});assert.equal(classifyChanges([entry('scripts/test_home_preview.cjs')],r,catalog()).science,true,directory);}
 for(const declaration of ['.','./','/home.js','C:\\home.js','https://example.org/home.js','../home.js']){const r=registry();r.records.push({scope:{artifacts:[declaration]}});assert.equal(classifyChanges([entry('home.js')],r,catalog()).science,true,declaration);}
 const c=catalog();c.files.push({path:'.\\home.js'});assert.equal(classifyChanges([entry('home.js')],registry(),c).science,true);
});
test('NUL parsing preserves tabs/newlines/spaces/unicode and both rename paths',()=>{
 const bytes=Buffer.from('M\0odd name\tline\nλ.js\0R100\0app.js\0new\nname.js\0A\0-leading-dash.js\0');const parsed=parseNameStatus(bytes);
 assert.equal(parsed[0].paths[0],'odd name\tline\nλ.js');assert.deepEqual(parsed[1],{status:'R100',paths:['app.js','new\nname.js']});assert.equal(parsed[2].paths[0],'-leading-dash.js');assert.equal(classifyChanges(parsed,registry(),catalog()).science,true);
 for(const value of ['M\0app.js','M\0','R100\0app.js\0','Q\0app.js\0'])assert.throws(()=>parseNameStatus(Buffer.from(value)));
 assert.throws(()=>parseNameStatus(Buffer.from([0xff])));assert.deepEqual(parseNameStatus(Buffer.alloc(0)),[]);
});
test('manual, unknown event, missing/invalid/unavailable baseline fall back without unsafe shell interpolation',()=>{
 for(const eventName of ['workflow_dispatch','schedule','unknown',undefined])assert.equal(scopeForCheckout({eventName,git(){throw Error('Must not run');}}).science,true);
 for(const before of [undefined,'0'.repeat(40),'--bad; command','f'.repeat(39)])assert.equal(scopeForCheckout({eventName:'push',event:{before},git(){throw Error('Must not run');}}).science,true);
 assert.equal(scopeForCheckout({eventName:'push',event:{before:'a'.repeat(40)},git(){throw Error('Shallow checkout lacks parent');}}).science,true);
});
test('actual Git baseline and NUL diff choose UI-only, mixed/deleted files choose full',()=>{
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'liberpedia-ci-scope-'));
 const git=args=>execFileSync('git',args,{cwd:tmp,encoding:null,shell:false,stdio:['ignore','pipe','pipe']});
 try{
  git(['init','-q']);git(['config','user.name','Offline CI scope test']);git(['config','user.email','ci-scope@example.invalid']);git(['config','core.autocrlf','false']);fs.mkdirSync(path.join(tmp,'data'));
  fs.writeFileSync(path.join(tmp,'data/experiments.json'),JSON.stringify(registry()));fs.writeFileSync(path.join(tmp,'data/catalog.json'),JSON.stringify(catalog()));fs.writeFileSync(path.join(tmp,'app.js'),'base\n');git(['add','.']);git(['commit','-qm','base']);const base=git(['rev-parse','HEAD']).toString().trim();
  fs.writeFileSync(path.join(tmp,'app.js'),'changed\n');git(['add','.']);git(['commit','-qm','UI']);
  for(const event of [{eventName:'push',event:{before:base}},{eventName:'pull_request',event:{pull_request:{base:{sha:base}}}}])assert.equal(scopeForCheckout({root:tmp,...event}).science,false);
  const ui=git(['rev-parse','HEAD']).toString().trim();fs.writeFileSync(path.join(tmp,'odd name λ.js'),'unknown\n');git(['add','.']);git(['commit','-qm','unknown path']);assert.equal(scopeForCheckout({root:tmp,eventName:'push',event:{before:ui}}).science,true);
  const unknown=git(['rev-parse','HEAD']).toString().trim();git(['rm','-q','app.js']);git(['commit','-qm','delete UI']);assert.equal(scopeForCheckout({root:tmp,eventName:'push',event:{before:unknown}}).science,true);
  fs.writeFileSync(path.join(tmp,'data/catalog.json'),'{bad');assert.equal(scopeForCheckout({root:tmp,eventName:'push',event:{before:base}}).science,true);
 }finally{
  const actual=fs.realpathSync(tmp),parent=fs.realpathSync(os.tmpdir());assert(actual.startsWith(parent+path.sep)&&path.basename(actual).startsWith('liberpedia-ci-scope-'));fs.rmSync(actual,{recursive:true,force:true});
 }
});
test('operational documentation stays lightweight unless it is a declared research dependency',()=>{
 for(const name of ['docs/community-research-loop.md','services/idea-assistant/README.md']){
  assert.equal(classifyChanges([entry(name)],registry(),catalog()).science,false);
  const r=registry();r.records.push({reproduction:{inputs:[{path:name}]}});
  assert.equal(classifyChanges([entry(name)],r,catalog()).science,true);
 }
 const workflow=fs.readFileSync(path.join(__dirname,'../.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n');
 assert(!/^concurrency:/m.test(workflow),'A branch-wide cancellation must not erase required scientific replay');
 const lane=workflow.split('  validate:\n')[1].split('    steps:\n')[0];
 assert(lane.includes('needs: scope'));
 assert(lane.includes("needs.scope.outputs.science == 'true' && github.sha || github.ref"),'Science runs retain their commit while lightweight work can replace an older lightweight run');
});

test('current reviewed allowlist does not silently include arbitrary future filenames',()=>{assert(!UI_PATHS.has('new-ui.js'));assert(!UI_PATHS.has('scripts/test_new_science.cjs'));assert(!UI_PATHS.has('.github/workflows/validate-experiments.yml'));});
test('actual checked-in registry/catalog allow app-only changes and workflow retains gated science checks',()=>{
 const root=path.resolve(__dirname,'..'),r=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8')),c=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'),'utf8'));
 assert.equal(classifyChanges(['word-sum-intake.js','scripts/test_word_sum_intake.cjs','scripts/test_word_sum_intake_flow.cjs'].map(p=>entry(p)),r,c).science,false);
 assert.equal(classifyChanges([entry('app.js')],r,c).science,false);assert.equal(classifyChanges([entry('home.js'),entry('scripts/test_home_preview.cjs')],r,c).science,false);
 const workflow=fs.readFileSync(path.join(root,'.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n');assert(workflow.includes('  workflow_dispatch:\n'));assert(workflow.includes('  validate:\n'));
 assert(workflow.includes('python scripts/check_experiment_authoring.py --github-event --fetch-base'),'Authoring policy must check the full push/PR, including a shallow baseline fetch');
 const blocks=workflow.split('  validate:\n')[1].split('    steps:\n')[1].split(/(?=^      - )/m).filter(s=>s.startsWith('      - '));
 for(const b of blocks)assert((b.match(/^        if:/gm)||[]).length<=1,'Duplicate workflow condition makes YAML invalid: '+b.split('\n')[0]);
 const python=blocks.findIndex(s=>s.includes('actions/setup-python@'));assert(python>0);assert(!blocks[python].includes('        if:'),'The one Python setup is shared by retention and science checks');
 const archiveTests=blocks.findIndex(b=>b.startsWith('      - name: Test immutable authored source retention\n')),archiveGate=blocks.findIndex(b=>b.startsWith('      - name: Check current and retained authored source revisions\n')),nodeChecks=blocks.findIndex(b=>b.includes('run: node scripts/run_node_checks.cjs'));
 assert(archiveTests>python&&archiveGate>archiveTests&&nodeChecks>archiveGate,'Fast immutable-source checks precede the full Node suite');
 for(const index of [archiveTests,archiveGate])assert(!blocks[index].includes('        if:'),'Immutable-source retention is unconditional');
 assert(blocks[archiveTests].includes('python -m unittest discover -s scripts -p test_archive_authored_sources.py'));assert(blocks[archiveGate].includes('--baseline-manifest "$baseline"'));assert(!blocks[archiveGate].includes('--write'));
 for(const [i,b]of blocks.entries()){if(/run: node\b/.test(b))assert(!b.includes('        if:'),'The reviewed Node checks remain unconditional');if(i!==archiveTests&&(/run: python\b|git diff --exit-code/.test(b)))assert(b.includes("if: steps.scope.outputs.science == 'true'"),'Science gate removed: '+b.split('\n')[0]);}
 for(const command of ['python scripts/test_export_reproducibility.py','python scripts/ci_experiment_bundles.py','python tests/test_bundle_ci_dispatch.py','python scripts/build_experiments.py','python scripts/reproduce_reading.py --check-all','git diff --exit-code --'])assert(workflow.includes(command),'Existing scientific gate missing');
});
console.log('PASS '+count+' conservative CI scope groups; no scientific rebuilds or hosted calls');
