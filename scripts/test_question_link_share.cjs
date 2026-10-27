'use strict';
const assert=require('node:assert/strict'),Share=require('../question-link-share.js');
const proposalId='p_'+'1'.repeat(64),options={proposalId,pageURL:'https://example.test/liberpedia/run.html?old=1#task=previous'},url='https://example.test/liberpedia/run.html#idea='+proposalId;
(async()=>{
 assert.equal(Share.link(options),url);
 assert.equal(Share.link({...options,pageURL:'http://127.0.0.1:8765/run.html'}),'http://127.0.0.1:8765/run.html#idea='+proposalId);
 for(const value of [{...options,proposalId:'unverified draft'},{...options,proposalId:proposalId+'&task=other'},{...options,pageURL:'javascript:alert(1)'},{...options,pageURL:'https://user:secret@example.test/run.html'},{...options,pageURL:'https://example.test/'+ 'a'.repeat(4096)},{...options,verdict:'solved'}])assert.throws(()=>Share.link(value));
 console.log('PASS saved question links retain the application path and reject draft IDs, credentials and non-web destinations');
 const calls=[];assert.deepEqual(await Share.share(options,{navigator:{async share(value){calls.push(value);},clipboard:{writeText(){assert.fail('Native sharing must not also copy');}}}}),{status:'shared',url});assert.deepEqual(calls,[{title:'Liberpedia research question',url}]);
 assert.deepEqual(await Share.share(options,{navigator:{async share(){throw Object.assign(Error('dismissed'),{name:'AbortError'});},clipboard:{writeText(){assert.fail('Cancellation must not copy');}}}}),{status:'cancelled',url});
 console.log('PASS explicit native sharing contains only the saved question link and cancellation has no clipboard side effect');
 const copied=[];assert.deepEqual(await Share.share(options,{navigator:{clipboard:{async writeText(value){copied.push(value);}}}}),{status:'copied',url});assert.deepEqual(copied,[url]);
 assert.deepEqual(await Share.share(options,{navigator:{async share(){throw Error('unsupported');},clipboard:{async writeText(){throw Error('denied');}}}}),{status:'fallback',url});
 assert.deepEqual(await Share.share(options,{navigator:{}}),{status:'fallback',url});
 console.log('PASS clipboard and manual-link fallback never claim a save, result or successful copy after failure');
})().catch(error=>{console.error(error);process.exitCode=1;});
