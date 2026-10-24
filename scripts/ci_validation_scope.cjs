/* A conservative CI shortcut, never a source of scientific coverage claims. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'..');
// Exact reviewed application paths only. New files, backend files, articles,
// generators, scientific inputs and this classifier itself default to full CI.
const UI_PATHS=new Set([
 'access.js','app.js','assistant-markdown.js','assistant-search.js','assistant-ui.js',
 'claim-interpretation.js','claim-research.js','claim-share.js','claim-specification.js',
 'experiment-search.js','experiments.js','grid-stem-view.js','home-intake.css','home.css','home.html','home.js',
 'idea-coverage.js','index.html','investigate.css','investigate.html','investigate.js',
 'line-gap-view.js','manuscript-compare.css','manuscript-compare.js','manuscript-reader.css','manuscript-reader.js',
 'numeric-skip-view.js','prime-lag-view.js','reader.html','research-index.js','research-map.css','research-map.js',
 'research.js','search-engine.js','search-ui.js','spelling.js','style.css','url-marker-view.js','wiki.js','workspace-routes.js',
 'data/assistant.json',
 'scripts/test_home_preview.cjs',
 'scripts/test_assistant.cjs','scripts/test_claim_interpretation.cjs','scripts/test_claim_specification.cjs',
 'scripts/test_claim_share.cjs','scripts/test_claim_research.cjs','scripts/test_claim_discovery.cjs','scripts/test_workspace_routes.cjs',
 'scripts/test_manuscript_reader.cjs','scripts/test_reader_continuous.cjs','scripts/test_manuscript_search.cjs',
 'scripts/test_investigate.cjs','scripts/test_investigate_edit_fidelity.cjs','scripts/test_investigate_share.cjs',
 'scripts/test_investigate_intake_focus.cjs','scripts/test_investigate_card_request.cjs','scripts/test_investigate_interpretation.cjs',
 'scripts/test_proposal_ui.cjs','scripts/test_research_map.cjs','scripts/test_assistant_retrieval.cjs',
 'scripts/test_research_index.cjs','scripts/test_download_pagination.cjs','scripts/test_research_history_focus.cjs',
 'scripts/test_experiment_support_state.cjs','scripts/test_experiment_detail_loading.cjs','scripts/test_experiment_article_links.cjs',
 'scripts/test_checker_copy_state.cjs','scripts/test_checker_loading.cjs','scripts/test_checker_cards.cjs',
 'scripts/test_checker_cache.cjs','scripts/test_checker_payload.cjs','scripts/test_keyboard_focus.cjs',
 'scripts/test_reader_state.cjs','scripts/test_reader_supplementary.cjs','scripts/test_image_dialog_state.cjs',
 'scripts/test_route_image_modal.cjs','scripts/test_download_verification.cjs','scripts/test_wiki_section_focus.cjs',
 'scripts/test_affine_lag_example.cjs','scripts/test_scientific_figure_states.cjs','scripts/test_grid_stem_view.cjs',
 'scripts/test_url_marker_view.cjs','scripts/test_prime_lag_view.cjs','scripts/test_numeric_skip_view.cjs',
 'scripts/test_line_gap_view.cjs','scripts/test_search.cjs','scripts/test_page_links.cjs','scripts/test_guide_index.cjs','scripts/test_article_loading.cjs'
]);
const full=reason=>({science:true,scope:'full',reason});
function parseNameStatus(bytes){
 const text=typeof bytes==='string'?bytes:new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 if(!text)return [];if(!text.endsWith('\0'))throw Error('Git output lacks NUL terminator');
 const tokens=text.slice(0,-1).split('\0'),entries=[];
 for(let i=0;i<tokens.length;){const status=tokens[i++];const count=/^[RC]\d{1,3}$/.test(status)?2:/^[MADTUXB]$/.test(status)?1:0;
  if(!count||i+count>tokens.length)throw Error('Malformed Git name-status output');
  const paths=tokens.slice(i,i+count);i+=count;if(paths.some(p=>!p))throw Error('Empty Git path');entries.push({status,paths});}
 return entries;
}
function declaredPaths(registry,catalog){
 if(registry?.schema!=='liberpedia-experiments-v1'||!Array.isArray(registry.records)||catalog?.schema!=='liber-primus-file-catalog-v1'||!Array.isArray(catalog.files))throw Error('Unknown registry/catalog structure');
 const declared=new Set(),add=p=>{
  if(typeof p!=='string'||!p||p!==p.trim()||p.includes('\0'))throw Error('Invalid declared dependency');
  p=p.replace(/\\/g,'/');if(p.startsWith('/')||/^[a-z][a-z0-9+.-]*:/i.test(p))throw Error('Absolute/unknown dependency semantics');
  const parts=p.split('/');if(parts.includes('..'))throw Error('Parent-relative dependency semantics');
  // Case-insensitive comparison is conservative for checkouts originating on
  // Windows. Every declaration also guards descendants, including directory
  // artifacts without a trailing slash. An explicit '.' guards the whole tree.
  declared.add(parts.filter(part=>part&&part!=='.').join('/').toLowerCase());
 };
 for(const item of catalog.files)add(item.path);
 for(const record of registry.records){if(!record||typeof record!=='object')throw Error('Invalid record');
  if(record.article_path)add(record.article_path);if(record.reproduction?.script)add(record.reproduction.script);
  for(const role of ['inputs','outputs']){const files=record.reproduction?.[role]??[];if(!Array.isArray(files))throw Error('Invalid reproduction dependencies');for(const file of files)add(file.path);}
  const artifacts=record.scope?.artifacts??[];if(!Array.isArray(artifacts))throw Error('Invalid scope artifacts');for(const p of artifacts)add(p);
 }return declared;
}
function classifyChanges(entries,registry,catalog){
 try{
  if(!entries.length)return full('No trustworthy changed paths');
  const declared=declaredPaths(registry,catalog);
  for(const entry of entries){
   if(!['M','A'].includes(entry.status)||entry.paths.length!==1)return full('Deletion, rename, copy or unsupported change status');
   const name=entry.paths[0],dependencyName=name.toLowerCase();
   if([...declared].some(p=>!p||dependencyName===p||dependencyName.startsWith(p+'/')))return full('Changed declared record/catalog dependency: '+name);
   if(!UI_PATHS.has(name))return full('Unclassified path: '+name);
  }
  return {science:false,scope:'ui-only',reason:'Every change is an allowlisted application addition/modification with no declared scientific/catalog dependency'};
 }catch{return full('Cannot validate dependency declarations');}
}
function scopeForCheckout({root=ROOT,eventName,event,git}={}){
 if(!['push','pull_request'].includes(eventName))return full(eventName==='workflow_dispatch'?'Manual full validation':'Unknown event: full validation');
 const base=eventName==='push'?event?.before:event?.pull_request?.base?.sha;
 if(typeof base!=='string'||!/^[a-f0-9]{40}(?:[a-f0-9]{24})?$/i.test(base)||/^0+$/.test(base))return full('Missing/invalid Git baseline');
 const run=git||(args=>execFileSync('git',args,{cwd:root,encoding:null,maxBuffer:16*1024*1024,shell:false}));
 try{
  run(['cat-file','-e',base+'^{commit}']);
  const entries=parseNameStatus(run(['diff','--name-status','-z','--no-renames',base,'HEAD','--']));
  return classifyChanges(entries,JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json'),'utf8')),JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'),'utf8')));
 }catch{return full('Git baseline, NUL diff or dependency files unavailable');}
}
function main(env=process.env){
 let event;try{event=JSON.parse(fs.readFileSync(env.GITHUB_EVENT_PATH,'utf8'));}catch{}
 const result=scopeForCheckout({eventName:env.GITHUB_EVENT_NAME,event});
 if(env.GITHUB_OUTPUT)fs.appendFileSync(env.GITHUB_OUTPUT,'science='+result.science+'\nscope='+result.scope+'\n','utf8');
 console.log(JSON.stringify(result));return result;
}
module.exports={UI_PATHS,parseNameStatus,declaredPaths,classifyChanges,scopeForCheckout,main};
if(require.main===module)main();
