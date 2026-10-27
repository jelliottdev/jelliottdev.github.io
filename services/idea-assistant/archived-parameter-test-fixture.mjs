/* Shared private SQLite fixture for archived source creation and discovery tests. */
import {DatabaseSync} from 'node:sqlite';
import {createHash} from 'node:crypto';
import {applyMigrations} from './sqlite-test-migrations.mjs';
import C from '../../claim-specification.js';
import E from '../../local-experiment.js';
const at='2026-10-26T00:00:00.000Z',origin='https://jelliottdev.github.io',sha=v=>createHash('sha256').update(typeof v==='string'?v:E.stable(v)).digest('hex');
export function fixture(){const sql=new DatabaseSync(':memory:');applyMigrations(sql);let rates=0,rateAllowed=true;const db={prepare(text){return {bind(...args){return {text,args,async first(){return sql.prepare(text).get(...args)||null;},async all(){return {results:sql.prepare(text).all(...args)};},async run(){return sql.prepare(text).run(...args);}};}};},async batch(items){sql.exec('BEGIN');try{const results=items.map(x=>({success:true,meta:{changes:Number(sql.prepare(x.text).run(...x.args).changes)}}));sql.exec('COMMIT');return results;}catch(e){sql.exec('ROLLBACK');throw e;}}};const env={SITE_ORIGIN:origin,PROPOSALS:db,TASK_LIMIT:{async limit(){rates++;return {success:rateAllowed};}}};
 function publish(c,visible=true){const json=C.serialize(c),id='p_'+sha(json);sql.prepare('INSERT OR IGNORE INTO proposals(id,card_hash,card_json,fragment,created_at) VALUES(?,?,?,?,?)').run(id,id.slice(2),json,'unused',at);if(visible)sql.prepare('INSERT OR IGNORE INTO research_ideas VALUES(?,?,?)').run(id,at,at.slice(0,10));return id;}
 return {sql,db,env,publish,rates:()=>rates,deny:()=>rateAllowed=false,close:()=>sql.close()};}
export const counts=f=>Object.fromEntries(['proposals','proposal_submissions','research_ideas','question_derivations','question_derivation_submissions','local_tasks','local_task_results','prepared_plans'].map(t=>[t,Number(f.sql.prepare('SELECT COUNT(*) n FROM '+t).get().n)]));
