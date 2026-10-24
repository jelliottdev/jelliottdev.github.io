#!/usr/bin/env node
/* Manual maintainer review. No inference, installation, deployment or publication. */
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join,isAbsolute,extname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const HERE=dirname(fileURLToPath(import.meta.url));
export const STATUSES=Object.freeze(['pending','accepted','duplicate','declined']);
const DECISIONS=STATUSES.filter(s=>s!=='pending');
const ID=/^p_[0-9a-f]{64}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const MAX_BYTES=8*1024*1024;
const sqlString=value=>"'"+String(value).replaceAll("'","''")+"'";

export const HELP=`Manual proposal review (explicit local/remote D1; no AI):
  node services/idea-assistant/review-proposals.mjs list --local|--remote [--limit 20] [--after p_HASH]
       [--status pending|accepted|duplicate|declined|all] [--new-notes]
  node services/idea-assistant/review-proposals.mjs show --local|--remote --id p_HASH
       [--note-limit 200] [--after-note UUID] [--history-limit 100] [--before-review N]
  node services/idea-assistant/review-proposals.mjs export --local|--remote --out FILE [--id p_HASH]
       [--limit 20] [--after p_HASH] [--note-limit 200] [--after-note UUID]
  node services/idea-assistant/review-proposals.mjs decide --local|--remote --id p_HASH
       --status accepted|duplicate|declined --expected-status pending --reason TEXT
       [--record EXISTING_PUBLISHED_RECORD_ID]

All commands accept --wrangler ABSOLUTE_INSTALLED_WRANGLER_JS and --database NAME
(remote: liberpedia-proposals; local: liberpedia-proposals-local).
--config FILE overrides the mode's config; --persist-to DIR is local-only.
LIBERPEDIA_WRANGLER supplies the installed JS path.
No npx/download fallback. --dry-run prints bounded SQL without contacting D1.
list/export default to pending; --status selects a reviewed queue too.
--new-notes selects reviewed cards with later submissions (defaults --status all).
show includes the exact card, submission notes and retained decision history.
IDs are p_ plus the complete 64-hex hash.
Limits: at most 100 cards, 1000 submission notes, 8 MiB serialized output.
Exports never overwrite files. Notes pagination is by UUID, not received time.
Acceptance records a review decision; it never publishes or runs an experiment.
`;

function integer(value,fallback,max,label){
 if(value===undefined)return fallback;
 if(!/^\d+$/.test(String(value))||Number(value)<1||Number(value)>max)throw Error(`${label} must be between 1 and ${max}.`);
 return Number(value);
}
function proposalId(value){if(!ID.test(value||''))throw Error('Use the complete p_ plus 64 lowercase hex proposal ID.');return value;}
export function parseArgs(args){
 const [command,...rest]=args;
 if(!command||command==='--help'||command==='help')return {command:'help'};
 if(!['list','show','export','decide'].includes(command))throw Error('Choose list, show, export or decide. Use --help.');
 const options={command},allowed=new Set(['wrangler','database','dry-run','local','remote','config','persist-to',
  ...(command==='decide'?['id','status','expected-status','reason','record']:
   command==='show'?['id','note-limit','after-note','history-limit','before-review']:
   ['limit','after','id','status','new-notes',...(command==='export'?['out','note-limit','after-note']:[])])]);
 for(let i=0;i<rest.length;i++){
  const flag=rest[i];if(!flag.startsWith('--')||!allowed.has(flag.slice(2)))throw Error('Unknown option: '+flag);
  const key=flag.slice(2);if(Object.hasOwn(options,key))throw Error('Repeated option: '+flag);
  if(['dry-run','local','remote','new-notes'].includes(key)){options[key]=true;continue;}
  if(rest[i+1]===undefined||rest[i+1].startsWith('--'))throw Error('Missing value for '+flag);
  options[key]=rest[++i];
 }
 if(options.local&&options.remote)throw Error('Choose --local or --remote, not both.');
 if(!options.local&&!options.remote&&!options['dry-run'])throw Error('Choose explicit --local or --remote; no database command is run by default.');
 if(options['persist-to']&&!options.local)throw Error('--persist-to is local-only.');
 options.database??=options.local?'liberpedia-proposals-local':'liberpedia-proposals';
 if(!/^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(options.database))throw Error('Invalid database name.');
 if(options.id)proposalId(options.id);
 if(options.after)proposalId(options.after);
 if(options.id&&options.after)throw Error('Choose --id or --after, not both.');
 if(command==='decide'){
  proposalId(options.id);
  if(!DECISIONS.includes(options.status))throw Error('A decision status must be accepted, duplicate or declined.');
  if(!STATUSES.includes(options['expected-status']))throw Error('Supply an explicit known --expected-status.');
  if(typeof options.reason!=='string'||!options.reason.trim()||options.reason.length>2000||options.reason.includes('\0'))throw Error('Supply a nonempty decision reason of at most 2000 characters, without NUL.');
  if(options.record&&!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(options.record))throw Error('Invalid related record ID.');
 }else{
  options.limit=command==='show'?1:integer(options.limit,20,100,'Card limit');
  options.status??=command==='show'||options['new-notes']?'all':'pending';
  if(![...STATUSES,'all'].includes(options.status))throw Error('Unknown review status.');
  if(command==='show'){
   proposalId(options.id);options['history-limit']=integer(options['history-limit'],100,100,'Review-history limit');
   if(options['before-review']!==undefined)options['before-review']=integer(options['before-review'],undefined,Number.MAX_SAFE_INTEGER,'Review-history cursor');
  }
  if(command==='export'||command==='show'){
   if(command==='export'&&!options.out)throw Error('Export requires an explicit --out file.');
   options['note-limit']=integer(options['note-limit'],200,1000,'Submission-note limit');
   if(options['after-note']){options['after-note']=options['after-note'].toLowerCase();if(!UUID.test(options['after-note']))throw Error('Invalid submission UUID cursor.');}
  }
 }
 return options;
}

function pendingWhere(options){
 const status=options.status||'pending';
 if(![...STATUSES,'all'].includes(status))throw Error('Unknown review status.');
 return (status==='all'?'1=1':'p.status = '+sqlString(status))+
  (options['new-notes']?' AND p.reviewed_at IS NOT NULL AND EXISTS (SELECT 1 FROM proposal_submissions s WHERE s.proposal_id=p.id AND s.received_at>p.reviewed_at)':'')+
  (options.id?' AND p.id = '+sqlString(proposalId(options.id)):'')+
  (options.after?' AND p.id > '+sqlString(proposalId(options.after)):'');
}
export function listSQL(options){
 const limit=integer(options.limit,20,100,'Card limit');
 return `SELECT COUNT(*) AS matching_cards,
 (SELECT COUNT(*) FROM proposal_submissions s JOIN proposals p ON p.id=s.proposal_id WHERE ${pendingWhere(options)}) AS matching_submissions
 FROM proposals p WHERE ${pendingWhere(options)};
SELECT p.id,p.card_hash,p.card_json,p.fragment,p.created_at,p.status,
 p.reviewed_at,p.review_reason,p.record_id,
 (SELECT COUNT(*) FROM proposal_submissions s WHERE s.proposal_id=p.id) AS submission_count,
 (SELECT COUNT(*) FROM proposal_submissions s WHERE s.proposal_id=p.id AND (p.reviewed_at IS NULL OR s.received_at>p.reviewed_at)) AS unreviewed_submission_count
 FROM proposals p WHERE ${pendingWhere(options)} ORDER BY p.id LIMIT ${limit+1};\n`;
}
export function notesSQL(ids,options){
 if(!ids.length)return null;
 ids.forEach(proposalId);
 const limit=integer(options['note-limit'],200,1000,'Submission-note limit');
 const cursor=options['after-note'];
 if(cursor&&!UUID.test(cursor))throw Error('Invalid submission UUID cursor.');
 return `SELECT request_id,proposal_id,note,source_url,original_idea,received_at,received_day
 FROM proposal_submissions WHERE proposal_id IN (${ids.map(sqlString).join(',')})`+
  (cursor?' AND request_id > '+sqlString(cursor):'')+` ORDER BY request_id LIMIT ${limit+1};\n`;
}
export function decisionSQL(options,publishedIds,at=new Date().toISOString()){
 proposalId(options.id);
 if(!DECISIONS.includes(options.status)||!STATUSES.includes(options['expected-status']))throw Error('Invalid decision or expected status.');
 if(typeof options.reason!=='string'||!options.reason.trim()||options.reason.length>2000||options.reason.includes('\0'))throw Error('Invalid decision reason.');
 if(!Number.isFinite(Date.parse(at)))throw Error('Invalid review timestamp.');
 if(options.record&&!publishedIds.has(options.record))throw Error('Related record is not in the local published registry: '+options.record);
 // Only these metadata columns may change. SQL quoting is literal SQLite
 // quoting; the complete SQL is one argv value and never passes through a shell.
 const changes=['status='+sqlString(options.status),'reviewed_at='+sqlString(at),'review_reason='+sqlString(options.reason.trim()),
  ...(options.record?['record_id='+sqlString(options.record)]:[])];
 return `UPDATE proposals SET ${changes.join(',')}
 WHERE id=${sqlString(options.id)} AND status=${sqlString(options['expected-status'])}
 RETURNING id,status,reviewed_at,review_reason,record_id;\n`;
}
export function historySQL(id,options){
 proposalId(id);const limit=integer(options['history-limit'],100,100,'Review-history limit');
 const before=options['before-review'];
 if(before!==undefined)integer(before,undefined,Number.MAX_SAFE_INTEGER,'Review-history cursor');
 return `SELECT COUNT(*) AS decision_count FROM proposal_reviews WHERE proposal_id=${sqlString(id)};
SELECT id,proposal_id,changed_at,old_status,new_status,old_reviewed_at,new_reviewed_at,
 old_review_reason,new_review_reason,old_record_id,new_record_id
 FROM proposal_reviews WHERE proposal_id=${sqlString(id)}`+
  (before!==undefined?' AND id < '+before:'')+` ORDER BY id DESC LIMIT ${limit+1};\n`;
}

export function invocation(wrangler,sql,database,options={}){
 if(!isAbsolute(wrangler)||!['.js','.mjs','.cjs'].includes(extname(wrangler).toLowerCase()))throw Error('--wrangler must name an absolute installed Wrangler JavaScript entry point.');
 if(!/^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(database))throw Error('Invalid database name.');
 if(!options.local&&!options.remote)throw Error('Choose explicit --local or --remote.');
 if(typeof sql!=='string'||!sql.trim()||sql.includes('\0'))throw Error('Expected nonempty SQL without NUL.');
 const config=options.config?resolve(options.config):join(HERE,options.local?'wrangler.proposals-local.jsonc':'wrangler.jsonc');
 // Remote --file invokes D1 bulk import, whose output is not query rows.
 // --command uses the query API in both modes and preserves SELECT/RETURNING.
 return {command:process.execPath,args:[wrangler,'d1','execute',database,options.local?'--local':'--remote','--json','--command',sql,'--config',config,
  ...(options['persist-to']?['--persist-to',resolve(options['persist-to'])]:[])],shell:false};
}
export function resolveWrangler(options,env=process.env){
 const configured=options.wrangler||env.LIBERPEDIA_WRANGLER;
 const candidates=configured?[configured]:[join(HERE,'node_modules/wrangler/bin/wrangler.js'),resolve(HERE,'../../node_modules/wrangler/bin/wrangler.js')];
 const path=candidates.find(candidate=>isAbsolute(candidate)&&existsSync(candidate));
 if(!path)throw Error('Installed Wrangler not found. Set --wrangler or LIBERPEDIA_WRANGLER to its absolute JS entry; no installer is run.');
 invocation(path,'SELECT 1;',options.database,options);return path;
}
function d1Results(stdout){
 let data;try{data=JSON.parse(stdout);}catch{throw Error('Wrangler did not return JSON. Inspect the CLI configuration and authentication.');}
 if(!Array.isArray(data)||data.some(part=>part.success!==true||!Array.isArray(part.results)))throw Error('D1 returned an unsuccessful or unrecognized result.');
 return data.map(part=>part.results);
}
export function remoteExecutor(options,{spawn=spawnSync}={}){
 const wrangler=resolveWrangler(options);
 return sql=>{
  const call=invocation(wrangler,sql,options.database,options),result=spawn(call.command,call.args,{
   cwd:HERE,encoding:'utf8',shell:false,timeout:60000,maxBuffer:16*1024*1024,
   env:{...process.env,WRANGLER_SEND_METRICS:'false',CI:'true'}});
  if(result.error)throw Error('Wrangler could not complete: '+result.error.message);
  if(result.status!==0)throw Error('Wrangler exited '+result.status+'. No success is claimed; inspect scoped D1 access and retry with the expected status.');
  return d1Results(result.stdout);
 };
}
function cardRow(row){
 proposalId(row.id);
 const hash=createHash('sha256').update(row.card_json,'utf8').digest('hex');
 if(row.card_hash!==hash||row.id!=='p_'+hash)throw Error('Stored card identity/hash mismatch: '+row.id);
 if(!STATUSES.includes(row.status))throw Error('An unknown review status was returned.');
 let card;try{card=JSON.parse(row.card_json);}catch{throw Error('Stored standardized card JSON is invalid: '+row.id);}
 return {...row,card}; // Keep exact immutable card_json alongside readable JSON.
}
function boundedJSON(value){
 const content=JSON.stringify(value,null,2)+'\n';
 if(Buffer.byteLength(content,'utf8')>MAX_BYTES)throw Error('Output exceeds 8 MiB. Use a smaller card/note limit or an exact --id; no data was truncated.');
 return content;
}

export async function run(options,{execute,stdout=console.log,now=()=>new Date().toISOString(),write=writeFileSync,read=readFileSync}={}){
 if(options.command==='help'){stdout(HELP);return;}
 let publishedIds=new Set();
 if(options.record){
  const registry=JSON.parse(read(resolve(HERE,'../../data/experiments.json'),'utf8'));
  publishedIds=new Set(registry.records.filter(r=>r.status==='published').map(r=>r.id));
 }
 const sql=options.command==='decide'?decisionSQL(options,publishedIds,now()):listSQL(options);
 if(options['dry-run']){stdout(sql);return;}
 const query=execute||remoteExecutor(options),started=now();
 if(options.command==='decide'){
  const results=await query(sql),rows=results[0];
  if(!Array.isArray(rows)||rows.length!==1||rows[0].id!==options.id||rows[0].status!==options.status)throw Error('No decision confirmed: proposal is missing or its status changed. Refresh the queue; do not retry with a guessed expected status.');
  stdout(boundedJSON({decision:rows[0],experiment_published:false}));return;
 }
 const results=await query(sql);
 if(results.length!==2||results[0].length!==1)throw Error('Unexpected queue response.');
 const raw=results[1],more=raw.length>options.limit,cards=raw.slice(0,options.limit).map(cardRow);
 const base={schema:'liberpedia-proposal-review-export-v1',read_started_at:started,
  counts:{...results[0][0],selected_cards:cards.length,selected_submissions:cards.reduce((sum,c)=>sum+Number(c.submission_count),0)},
  cards,next_after:more?cards.at(-1).id:null,
  filter:{status:options.status,new_notes_only:Boolean(options['new-notes']),after:options.after||null},
  note:'Counts distinguish immutable cards from submissions. Review/export is not experiment execution or publication.'};
 if(options.command==='show'&&!cards.length)throw Error('Proposal ID was not found.');
 if(options.command==='export'||options.command==='show'){
  const querySQL=notesSQL(cards.map(c=>c.id),options),allNotes=querySQL?(await query(querySQL))[0]:[];
  if(!Array.isArray(allNotes))throw Error('Unexpected submission-notes response.');
  const notes=allNotes.slice(0,options['note-limit']);
  const selectedIds=new Set(cards.map(c=>c.id));
  if(notes.some(note=>!UUID.test(note.request_id)||!selectedIds.has(note.proposal_id)))throw Error('Unexpected submission identity in export.');
  base.submissions=notes;base.next_after_note=allNotes.length>notes.length?notes.at(-1).request_id:null;
  base.notes_complete_for_selection=!options['after-note']&&!base.next_after_note;
  base.note_pagination='UUID order; pass --id for one card and --after-note with next_after_note to continue. Metadata and notes are separate bounded reads, not a transactional snapshot.';
 }
 if(options.command==='show'){
  const history=await query(historySQL(options.id,options));
  if(history.length!==2||history[0].length!==1||!Array.isArray(history[1]))throw Error('Unexpected review-history response. Ensure migration 0002 is applied.');
  const rows=history[1].slice(0,options['history-limit']);
  if(rows.some(row=>row.proposal_id!==options.id||!Number.isSafeInteger(row.id)||row.id<1||!STATUSES.includes(row.old_status)||!STATUSES.includes(row.new_status)))throw Error('Unexpected review-history identity or status.');
  base.review_history_count=history[0][0].decision_count;base.review_history=rows;
  base.next_before_review=history[1].length>rows.length?rows.at(-1).id:null;
 }
 base.read_finished_at=now();const content=boundedJSON(base);
 if(options.command==='export'){
  write(resolve(options.out),content,{encoding:'utf8',mode:0o600,flag:'wx'});
  stdout(`Exported ${cards.length} pending cards and ${base.submissions.length} submission notes to ${resolve(options.out)}. Existing files are never overwritten.`);
 }else stdout(content);
}

if(process.argv[1]&&pathToFileURL(resolve(process.argv[1])).href===import.meta.url){
 try{await run(parseArgs(process.argv.slice(2)));}
 catch(error){console.error('Proposal review: '+error.message);process.exitCode=1;}
}
