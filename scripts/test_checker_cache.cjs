/* Cold checker, warm details, malformed artifacts and retry must stay separate. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),full=JSON.parse(fs.readFileSync(path.join(root,'data/experiments.json')));
const fields=['id','status','title','question','summary','tags','record_type','family','variant','scope','outcome','finding','limitations','article','method_topics','reader_finding','reader_limit','reader_test','materials'];
const compact={schema:'liberpedia-checker-records-v1',registry_sha256:'a'.repeat(64),records:full.records.slice(0,2).map(record=>Object.fromEntries(fields.filter(k=>Object.hasOwn(record,k)).map(k=>[k,record[k]])))};
const source=fs.readFileSync(path.join(root,'experiments.js'),'utf8');
const make=()=>{const context={};vm.createContext(context);vm.runInContext(source,context);return context};
const response=data=>({ok:true,json:async()=>data});
(async()=>{
 const context=make(),requests=[];let finish;
 context.fetch=url=>{requests.push(url);return new Promise(resolve=>finish=resolve)};
 const first=context.ensureCheckerRecords(),second=context.ensureCheckerRecords();assert.equal(requests.length,1);
 finish(response(compact));assert.equal(await first,await second);
 assert(vm.runInContext('experimentRecords===undefined',context),'Compact load does not populate full-detail records');
 assert.equal((await context.ensureCheckerRecords())[0].id,compact.records[0].id);assert.equal(requests.length,1,'Checker cache is reused');
 context.fetch=async url=>{requests.push(url);return response(url.startsWith('reference/experiments/')?full.records[0]:full)};
 context.renderId=1;context.main={innerHTML:'',querySelector:()=>null};context.head=()=>'';context.footer=()=>'';context.esc=String;
 for(const name of ['bindRouteIllustration','bindLanguageBlockFigure','bindAffineLagFigure','bindBlockBoundaryFigure','startExperimentSupport'])context[name]=()=>{};
 await context.experimentsPage(full.records[0].id,1);
 assert.equal(requests.at(-1),`reference/experiments/${full.records[0].id}.json`);
 assert(vm.runInContext('experimentRecords===undefined',context),'An individual detail must not fill the complete registry cache');
 const details=await context.ensureExperimentRecords();assert.equal(requests.at(-1),'data/experiments.json');
 assert(context.main.innerHTML.includes('Download experiment ZIP'),'Later detail route renders complete files after fetching the full registry');
 assert(details[0].reproduction&&details[0].sources,'Later detail loader retains complete dependencies');
 assert.equal(await context.ensureCheckerRecords(),details,'Warm complete records take precedence without another compact request');
 assert.equal(requests.length,3);
 const warm=make();warm.complete=full.records;vm.runInContext('experimentRecords=complete',warm);warm.fetch=()=>{throw Error('Unexpected cold load')};
 assert.equal(await warm.ensureCheckerRecords(),full.records);
 const invalid=[{}, {...compact,schema:'old-schema'}, {...compact,registry_sha256:'missing'},
  {...compact,records:[{...compact.records[0],scope:{pages:[]}}]},
  {...compact,records:[{...compact.records[0],article:undefined}]},
  {...compact,records:[{...compact.records[0],limitations:undefined}]},
  {...compact,records:[{...compact.records[0],record_type:{id:'constructor'}}]},
  {...compact,records:[compact.records[0],compact.records[0]]}];
 for(const payload of invalid){
  const test=make();let calls=0;test.fetch=async()=>{calls++;return response(calls===1?payload:compact)};
  await assert.rejects(test.ensureCheckerRecords(),/invalid format/);assert(vm.runInContext('checkerRecords===undefined&&experimentRecords===undefined',test));
  const recovered=await test.ensureCheckerRecords();assert.equal(recovered.length,2);assert.equal(calls,2,'Malformed loads release the promise for retry');
 }
 const validNote={summary:'Saved scores.',reuse:'Compare recorded scores.',limits:'No decoded text.',evidence:['experiments/records/test/results.json']};
 assert(context.validMaterials(validNote));
 for(const materials of [null,{}, {...validNote,summary:''},{...validNote,limits:'x'.repeat(1201)}, {...validNote,evidence:['../private']},{...validNote,evidence:validNote.evidence.concat(validNote.evidence)},{...validNote,runVerified:true}]){
  assert(!context.validCheckerPayload({...compact,records:[{...compact.records[0],materials}]}),'Malformed notes must not become model evidence');
 }
 const missing=make();let calls=0;missing.fetch=async()=>{calls++;return calls===1?{ok:false}:response(compact)};
 await assert.rejects(missing.ensureCheckerRecords(),/could not be loaded/);await missing.ensureCheckerRecords();assert.equal(calls,2);
 console.log('PASS: cold compact shared/cache load, later complete details, warm full reuse, required schema/evidence validation and malformed/missing retry.');
})().catch(error=>{console.error(error);process.exitCode=1});
