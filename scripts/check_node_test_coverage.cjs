'use strict';
// Every script test has an explicit execution policy; this gate never runs browser QA.
const fs=require('node:fs'),path=require('node:path');
const EXCLUSIONS=Object.freeze({
 'scripts/test_article_outline_mobile.cjs':'Manual browser QA: Edge/Playwright mobile article outline against an externally served site; writes screenshots.',
 'scripts/test_catalogue_mobile.cjs':'Manual browser QA: Edge/Playwright catalogue at multiple viewport widths against an externally served site.',
 'scripts/test_choice_explorer.cjs':'Manual browser QA: Edge/Playwright choice explorer against an externally served site.',
 'scripts/test_compact_finite_admission.cjs':'Shared heavy test implementation executed by the four registered test_compact_finite_admission_group_*.cjs shards; standalone execution would duplicate all witnesses.',
 'scripts/test_experiment_archive_mobile.cjs':'Manual browser QA: Edge/Playwright research archive viewport and screenshot checks against an externally served site.',
 'scripts/test_experiment_layout.cjs':'Manual browser QA: Edge/Playwright experiment layout and screenshots against an externally served site.',
 'scripts/test_experiment_progressive.cjs':'Manual browser QA: Edge/Playwright progressive experiment loading against an externally served site.',
 'scripts/test_fibonacci_panel.cjs':'Manual browser QA: Edge/Playwright Fibonacci panel and screenshots against an externally served site.',
 'scripts/test_home_clarity.cjs':'Manual browser QA: Edge/Playwright home and quick-start screenshots against an externally served site.',
 'scripts/test_idea_coverage.cjs':'Legacy old-app UI test requiring repair before CI: line 189 assumes the reader question always appears literally inside experimentArticle; later assertions also require the retired Detailed analysis and sources fold. Do not treat these obsolete presentation assertions as current UI contracts.',
 'scripts/test_interface.cjs':'Manual browser QA: Edge/Playwright broad route/viewport smoke test with an externally served site and browser network stubs.',
 'scripts/test_method_map_mobile.cjs':'Manual browser QA: Edge/Playwright method-map viewport screenshots against an externally served site.',
 'scripts/test_mobile_navigation.cjs':'Manual browser QA: Edge/Playwright mobile navigation against an externally served site.',
 'scripts/test_mobile_sections.cjs':'Manual browser QA: Edge/Playwright mobile menu sections/screenshots against an externally served site.',
 'scripts/test_reader_compact.cjs':'Manual browser QA: Edge/Playwright compact reader/viewer against an externally served site.',
 'scripts/test_reader_continuity.cjs':'Manual browser QA: Edge/Playwright reader continuity against an externally served site.',
 'scripts/test_reader_navigation.cjs':'Manual browser QA: Edge/Playwright reader navigation against an externally served site.',
 'scripts/test_reader_recovery.cjs':'Manual browser QA: Edge/Playwright reader recovery against an externally served site.',
 'scripts/test_rune_font_mobile.cjs':'Manual browser QA: Edge/Playwright rune-font viewport screenshots against an externally served site.',
 'scripts/test_search_filters.cjs':'Manual browser QA: Edge/Playwright search filters/screenshots against an externally served site.',
 'scripts/test_startup_resilience.cjs':'Manual browser QA: Edge/Playwright startup resilience against an externally served site.',
 'scripts/test_switching_choices_render.cjs':'Manual browser QA: Edge/Playwright switching-choice screenshot rendering against an externally served site.',
 'scripts/test_visual_system.cjs':'Manual browser QA: Edge/Playwright visual screenshots across home/navigation/articles against an externally served site.'
});
const TEST=/^(?:scripts\/test_[^/]+|services\/idea-assistant\/test[_-][^/]+)\.(?:cjs|mjs)$/;
function explicitWorkflowTests(text){
 const found=new Set();
 // Only node invocations in YAML run values/block commands count, never comments or prose.
 let block=false,indent=0;
 for(const line of text.split(/\r?\n/)){
  if(!line.trim()||line.trimStart().startsWith('#'))continue;
  const spaces=line.length-line.trimStart().length,run=line.match(/^\s*(?:-\s*)?run:\s*(.*)$/);
  let command=null;
  if(run){block=/^[|>][-+]?\s*$/.test(run[1]);indent=spaces;command=block?null:run[1];}
  else if(block&&spaces>indent)command=line.trim();else block=false;
  if(command){const match=command.match(/^(?:node|nodejs)\s+(?:--[\w-]+\s+)*["']?((?:scripts\/test_[\w.-]+|services\/idea-assistant\/test[_-][\w.-]+)\.(?:cjs|mjs))["']?(?:\s|$)/);if(match)found.add(match[1]);}
 }
 return found;
}
function checkCoverage({files,manifest,workflows=[],exclusions=EXCLUSIONS}){
 const tests=new Set(files.filter(file=>TEST.test(file))),registered=new Set();
 for(const check of manifest.checks||[])for(const arg of check.args||[])if(typeof arg==='string'&&TEST.test(arg))registered.add(arg);
 const explicit=new Set(workflows.flatMap(text=>[...explicitWorkflowTests(text)]));
 for(const [file,reason] of Object.entries(exclusions)){
  if(!tests.has(file))throw Error('Stale Node test exclusion: '+file);
  if(typeof reason!=='string'||reason.trim().length<30)throw Error('Node test exclusion needs a concrete reason: '+file);
  if(registered.has(file)||explicit.has(file))throw Error('Registered Node test must not also be excluded: '+file);
 }
 const missing=[...tests].filter(file=>!registered.has(file)&&!explicit.has(file)&&!Object.hasOwn(exclusions,file)).sort();
 if(missing.length)throw Error('Unregistered Node test scripts:\n'+missing.join('\n'));
 return Object.freeze({tests:tests.size,registered:[...tests].filter(file=>registered.has(file)).length,workflow:[...tests].filter(file=>explicit.has(file)&&!registered.has(file)).length,excluded:Object.keys(exclusions).length});
}
function main(root=path.resolve(__dirname,'..')){
 const files=['scripts','services/idea-assistant'].flatMap(dir=>fs.readdirSync(path.join(root,dir)).map(name=>dir+'/'+name)),workflowDir=path.join(root,'.github/workflows');
 const workflows=fs.readdirSync(workflowDir).filter(name=>/\.ya?ml$/.test(name)).map(name=>fs.readFileSync(path.join(workflowDir,name),'utf8'));
 const result=checkCoverage({files,manifest:JSON.parse(fs.readFileSync(path.join(root,'scripts/node-checks.json'),'utf8')),workflows});
 console.log('PASS Node test registration coverage '+JSON.stringify(result));return result;
}
module.exports={EXCLUSIONS,checkCoverage,explicitWorkflowTests,main};
if(require.main===module)try{main();}catch(error){console.error(error.message);process.exitCode=1;}
