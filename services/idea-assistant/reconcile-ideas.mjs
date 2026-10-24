/* Private, offline owner review. Retrieval is not coverage or novelty. */
import {readFileSync,mkdirSync,writeFileSync,realpathSync,existsSync,unlinkSync,rmdirSync} from 'node:fs';
import {resolve,dirname,join,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import C from '../../claim-specification.js';
import Share from '../../claim-share.js';
import Research from '../../claim-research.js';
import Search from '../../assistant-search.js';
import {compareCards,validateCard} from './idea-relations.mjs';

const ROOT=fileURLToPath(new URL('../../',import.meta.url));
const MAX_INPUT=8*1024*1024,MAX_REGISTRY=64*1024*1024,MAX_OUTPUT=32*1024*1024;
const statuses=new Set(['pending','accepted','duplicate','declined']);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const fail=message=>{throw Error(message);};
const text=(value,max,name)=>typeof value==='string'&&value.length<=max?value:fail('Invalid '+name);
const integer=(value,name)=>Number.isSafeInteger(value)&&value>=0?value:fail('Invalid '+name);
const timestamp=value=>typeof value==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value)&&Number.isFinite(Date.parse(value));
const same=(a,b)=>C.serialize(a)===C.serialize(b);
export function parseArgs(args){
 const options={registry:join(ROOT,'data','experiments.json')};
 if(args.length===0||args.length===1&&args[0]==='--help')return {help:true};
 for(let i=0;i<args.length;i+=2){const key=args[i];if(!['--input','--registry','--out'].includes(key)||i+1>=args.length||options[key.slice(2)]&&key!=='--registry')fail('Use --input FILE --out NEW_PRIVATE_DIRECTORY [--registry FILE]');
  if(key==='--registry'&&options.registryExplicit)fail('Duplicate --registry');options[key.slice(2)]=resolve(args[i+1]);if(key==='--registry')options.registryExplicit=true;}
 if(!options.input||!options.out)fail('Explicit --input and --out are required');return options;
}
export function validateExport(data,publishedIds){
 if(data?.schema!=='liberpedia-proposal-review-export-v1'||!Array.isArray(data.cards)||data.cards.length>100||!Array.isArray(data.submissions)||data.submissions.length>1000)fail('Expected bounded review-proposals export');
 if(data.notes_complete_for_selection!==true||data.next_after_note)fail('Incomplete submission notes: export all selected-card contributions before reconciliation');
 const ids=new Set(),cards=[];
 for(const row of data.cards){
  text(row.card_json,Share.MAX_BYTES,'card_json');const hash=sha(row.card_json);
  if(row.card_hash!==hash||row.id!=='p_'+hash)fail('Card hash/ID mismatch');
  if(ids.has(row.id))fail('Duplicate proposal ID');ids.add(row.id);
  if(!statuses.has(row.status))fail('Unknown review status');
  integer(row.submission_count,'submission_count');
  const card=validateCard(row.card_json);
  if(C.serialize(card)!==row.card_json)fail('Card JSON is not canonical active card data');
  if(!same(card,row.card))fail('Parsed card disagrees with immutable card_json');
  const confirmed=C.confirm(Share.decode(text(row.fragment,Share.MAX_URL,'fragment')).draft,{id:'offline-reconciliation',at:'2000-01-01T00:00:00.000Z'});
  if(!same(card,Share.cardData(confirmed)))fail('Fragment disagrees with immutable card');
  if(row.record_id!=null&&!publishedIds.has(row.record_id))fail('Stale related published-record ID: '+row.record_id);
  cards.push({...row,card});
 }
 const requests=new Set(),counts=new Map(cards.map(row=>[row.id,0]));
 for(const submission of data.submissions){
  if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(submission.request_id)||requests.has(submission.request_id.toLowerCase()))fail('Invalid or duplicate submission request ID');
  requests.add(submission.request_id.toLowerCase());if(!ids.has(submission.proposal_id))fail('Orphan submission');
  text(submission.original_idea,8000,'original_idea');text(submission.note,1200,'note');text(submission.source_url,1500,'source_url');
  if(!timestamp(submission.received_at)||submission.received_day!==submission.received_at.slice(0,10))fail('Invalid submission timestamp/day');
  counts.set(submission.proposal_id,counts.get(submission.proposal_id)+1);
 }
 for(const card of cards)if(counts.get(card.id)!==card.submission_count)fail('Missing submission notes for '+card.id);
 if(data.counts?.selected_cards!==cards.length||data.counts?.selected_submissions!==data.submissions.length)fail('Export selected counts disagree');
 if(integer(data.counts.matching_cards,'matching_cards')<cards.length||integer(data.counts.matching_submissions,'matching_submissions')<data.submissions.length)fail('Export matching counts disagree');
 if(!timestamp(data.read_started_at)||!timestamp(data.read_finished_at)||Date.parse(data.read_started_at)>Date.parse(data.read_finished_at))fail('Invalid export read timestamps');
 return cards;
}
export function reconcile(data,registry,{inputHash,registryHash,generatedAt=new Date().toISOString(),codeHashes={}}={}){
 if(registry?.schema!=='liberpedia-experiments-v1'||!Array.isArray(registry.records))fail('Invalid published registry');
 const ids=new Set();for(const record of registry.records){if(typeof record.id!=='string'||!/^[a-z0-9][a-z0-9-]*$/.test(record.id)||ids.has(record.id))fail('Invalid or duplicate registry record ID');ids.add(record.id);}
 const published=registry.records.filter(r=>r.status==='published'),publishedMap=new Map(published.map(r=>[r.id,r]));
 const cards=validateExport(data,new Set(publishedMap.keys())),docs=Search.experimentDocs(published),groups=[];
 for(const row of cards){
  let group=groups.find(g=>g.card_hash===row.card_hash);
  if(!group){
   const confirmed=C.confirm(Share.decode(row.fragment).draft,{id:'offline-reconciliation',at:'2000-01-01T00:00:00.000Z'});
   // Deliberately exclude original wording, outcome and scope prose from ranking.
   // Ordered method parameters and specified rules remain method-search terms.
   const ready=C.completeness(confirmed).researchReady;
   const pages=row.card.scope.status==='specified'?(row.card.scope.value.pages||[]):[];
   let projection=null;
   if(ready){
    // Use the shared parameter/operand projection, without turning private
    // background, aims, passage prose or unresolved notes into ranking terms.
    // The complete original card remains below for the owner's comparison.
    const ranking=C.confirm(C.createDraft({source:{text:'Offline method-only discovery.',origin:'shared_link'},
     method:confirmed.method,rules:confirmed.rules,
     scope:row.card.scope.status==='specified'?C.field('specified',{pages}):C.field()}),
     {id:'offline-ranking',at:'2000-01-01T00:00:00.000Z'});
    try{projection=Research.prepare(ranking);}
    catch(error){if(!['query-too-long','context-too-long','body-too-long'].includes(error.code))throw error;}
   }
   const query=projection?.query||null;
   const hits=projection?Search.select(docs,query,pages,projection.discovery).filter(d=>d.kind==='experiment'):[];
   group={id:row.id,card_hash:row.card_hash,card_json:row.card_json,card:row.card,fragment:row.fragment,proposals:[],contributions:[],
    retrieval:{query,pages,discovery:projection?.discovery||null,state:!ready?'needs_clarification':!projection?'needs_shorter_method':hits.length?'candidate_records_found':'needs_comparison',basis:'standardized method and rules only; shared per-step hints support discovery; pages break ties; candidates are not exact coverage'},
    candidates:hits.map(hit=>({id:hit.id,citation:'https://jelliottdev.github.io/#/experiments/'+hit.id,record_sha256:sha(C.serialize(publishedMap.get(hit.id))),record:publishedMap.get(hit.id)})),novelty:'not_assessed',coverage:'not_assessed'};
   groups.push(group);
  }
  const {card,card_json,fragment,...metadata}=row;group.proposals.push(metadata);
  group.contributions.push(...data.submissions.filter(s=>s.proposal_id===row.id));
 }
 const relations=[];
 for(let i=0;i<groups.length;i++)for(let j=i+1;j<groups.length;j++)relations.push({left:groups[i].id,right:groups[j].id,...compareCards(groups[i].card,groups[j].card)});
 return {schema:'liberpedia-private-idea-reconciliation-v1',generated_at:generatedAt,
  purpose:'Owner comparison of saved incoming cards; no tasks created, no experiments run, no novelty or coverage determined.',
  snapshot:{input_sha256:inputHash,registry_sha256:registryHash,published_records:published.length,code_sha256:codeHashes,export_read_started_at:data.read_started_at,export_read_finished_at:data.read_finished_at,filter:data.filter,next_after:data.next_after||null,matching_counts:data.counts,note:'Export reads are not transactional. This report covers only the selected complete card ledger; a cursor or higher matching count leaves more cards outside this report.'},
  counts:{saved_incoming_cards:cards.length,exact_card_groups:groups.length,contributions:data.submissions.length,cards_pending_maintainer_review:cards.filter(c=>c.status==='pending').length,pending_tasks_created:0,experiments_executed:0},groups,relations};
}
// All supplied strings are inert text, including Markdown, HTML and remote URLs.
const escape=value=>String(value??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const block=value=>'<pre>'+escape(typeof value==='string'?value:JSON.stringify(value,null,2))+'</pre>';
export function render(report){
 const lines=['# Private incoming-idea comparison','',report.purpose,'',block(report.counts),'', 'Candidate records are leads for comparison, not completed coverage of the incoming idea. No match means **needs comparison**, never “new”. Original wording and source URLs below are private inert text; nothing is fetched.','', '## Snapshot','',block(report.snapshot)];
 for(const group of report.groups){lines.push('', '## Card '+group.id,'',block({retrieval:group.retrieval,novelty:group.novelty,coverage:group.coverage}),'','### Exact standardized card','',block(group.card),'','### Saved card review metadata','',block(group.proposals),'','### Every contribution','',block(group.contributions));
  if(!group.candidates.length)lines.push('','No candidate selected. Owner comparison is still required.');
  for(const candidate of group.candidates)lines.push('','### Published candidate: '+escape(candidate.id),'', '[Open published record]('+candidate.citation+')','', 'Full registry record, including exact scope, exclusions, findings and limits:','',block(candidate.record));
 }
 lines.push('','## Relationships between incoming cards','', 'Deltas run from left to right. These structural comparisons do not assess novelty or research coverage.','',block(report.relations));return lines.join('\n')+'\n';
}
function readJSON(path,limit){const bytes=readFileSync(path);if(bytes.length>limit)fail('Input exceeds byte limit: '+path);return {value:JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),hash:sha(bytes)};}
export function privateOutput(out){
 const absolute=resolve(out);if(existsSync(absolute))fail('Output must be a new private directory');
 const parent=realpathSync(dirname(absolute)),actual=join(parent,absolute.slice(dirname(absolute).length+1));
 const repo=realpathSync(ROOT),rel=relative(repo,actual);
 if(!rel||!rel.startsWith('..'+(process.platform==='win32'?'\\':'/'))&&!isAbsolute(rel))fail('Private output must be outside the public repository');
 return actual;
}
export function run(options){
 const out=privateOutput(options.out),input=readJSON(options.input,MAX_INPUT),registry=readJSON(options.registry,MAX_REGISTRY);
 const codeHashes=Object.fromEntries(['reconcile-ideas.mjs','idea-relations.mjs','../../assistant-search.js','../../claim-share.js','../../claim-specification.js','../../claim-research.js'].map(p=>[p,sha(readFileSync(new URL(p,import.meta.url)))]));
 const report=reconcile(input.value,registry.value,{inputHash:input.hash,registryHash:registry.hash,codeHashes}),json=JSON.stringify(report,null,2)+'\n',markdown=render(report);
 if(Buffer.byteLength(json)+Buffer.byteLength(markdown)>MAX_OUTPUT)fail('Output exceeds bounded report size');
 mkdirSync(out,{mode:0o700});const written=[];
 try{for(const [name,content] of [['queue-review.json',json],['queue-review.md',markdown]]){const path=join(out,name);writeFileSync(path,content,{encoding:'utf8',flag:'wx',mode:0o600});written.push(path);}}
 catch(error){for(const path of written)unlinkSync(path);rmdirSync(out);throw error;}
 return {out,counts:report.counts};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options=parseArgs(process.argv.slice(2));console.log(options.help?'Offline owner review: node services/idea-assistant/reconcile-ideas.mjs --input PRIVATE_EXPORT.json --out NEW_PRIVATE_DIRECTORY [--registry data/experiments.json]':JSON.stringify(run(options),null,2));}
 catch(error){console.error(error.message);process.exitCode=1;}
}
