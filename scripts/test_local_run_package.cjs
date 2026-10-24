'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process'),{webcrypto}=require('node:crypto');
const E=require('../local-experiment.js'),P=require('../local-run-package.js');
const root=path.resolve(__dirname,'..'),runner=fs.readFileSync(path.join(root,'tools/research_runner.py'),'utf8');
const runes=Array.from('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ');
async function main(){
 const task=await E.prepare({title:'Synthetic package control 🧪',alphabet:runes.map((rune,i)=>({rune,latin:'R'+i,prime:i+2})),
  pages:[{id:'lp2-15',text:'ᚠᚢ-ᚦᚩ\r\nᚱᚳ'}],steps:[{op:'reverse',unit:'line'},{op:'affine',a:2,b:1},{op:'cumulative-difference',reset:'line'}],criterion:{kind:'measurement'}},webcrypto);
 const address='https://jelliottdev.github.io/run.html#task='+task.taskId,before=structuredClone(task);
 const bytes=await P.build(task,runner,address);assert(bytes instanceof Uint8Array);assert.deepEqual(task,before);
 assert.deepEqual(await P.build(task,runner,address),bytes,'Identical inputs produce byte-identical ZIPs');
 const changing=structuredClone(task),pending=P.build(changing,runner,address);changing.pages[0].text='Changed during identity verification';assert.deepEqual(await pending,bytes,'Caller changes during hashing cannot alter the packaged task');
 const reordered=Object.fromEntries(Object.entries(task).reverse());assert.deepEqual(await P.build(reordered,runner,address),bytes,'Task key order cannot change archive bytes');
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'local-run-package-'));
 try{
  const archive=path.join(folder,'package.zip');fs.writeFileSync(archive,bytes);fs.writeFileSync(path.join(folder,'expected-task.json'),E.stable(task)+'\n');fs.writeFileSync(path.join(folder,'expected-runner.py'),runner);
  const inspect=String.raw`import json,pathlib,sys,tempfile,zipfile
p=pathlib.Path(sys.argv[1]);z=zipfile.ZipFile(p/'package.zip')
assert z.namelist()==['task.json','research_runner.py','START.txt']
assert z.testzip() is None
for m in z.infolist():
 assert m.compress_type==zipfile.ZIP_STORED and m.date_time==(1980,1,1,0,0,0)
 assert m.flag_bits & 0x800 and not m.is_dir()
 assert pathlib.PurePosixPath(m.filename).name==m.filename
assert z.read('task.json')==(p/'expected-task.json').read_bytes()
assert z.read('research_runner.py')==(p/'expected-runner.py').read_bytes()
assert sys.argv[2] in z.read('START.txt').decode('utf-8')
with tempfile.TemporaryDirectory(prefix='extracted-rune-run-') as directory:
 output=pathlib.Path(directory);z.extractall(output)
 import subprocess
 subprocess.run([sys.executable,'research_runner.py','--task','task.json','--out','results.json'],cwd=output,check=True)
 sys.stdout.buffer.write((output/'results.json').read_bytes())
`;
  const result=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',inspect,folder,address],{encoding:'utf8',maxBuffer:3000000}));
  assert.deepEqual(await E.verify(task,result,webcrypto),E.run(task));
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
 for(const bad of ['https://evil.example/run.html#task='+task.taskId,'https://jelliottdev.github.io.evil.example/run.html#task='+task.taskId,
  'https://user:password@jelliottdev.github.io/run.html#task='+task.taskId,'https://jelliottdev.github.io:444/run.html#task='+task.taskId,
  'https://jelliottdev.github.io/run.html?text=private#task='+task.taskId,'https://jelliottdev.github.io/../run.html#task='+task.taskId,
  'https://jelliottdev.github.io/run.html#task='+'0'.repeat(64),'http://192.168.1.2/run.html#task='+task.taskId,'javascript:alert(1)',null])await assert.rejects(P.build(task,runner,bad));
 for(const origin of ['http://localhost:8765','http://127.0.0.1:8765'])assert(await P.build(task,runner,origin+'/run.html#task='+task.taskId));
 const tampered=structuredClone(task);tampered.pages[0].text+='ᚠ';await assert.rejects(P.build(tampered,runner,address),/changed/);
 await assert.rejects(P.build({...task,unknown:undefined},runner,address),'Unknown fields cannot disappear during JSON snapshotting');
 for(const invalid of ['',null,'x'.repeat(100001),'🧪'.repeat(25001),'\ud800'])await assert.rejects(P.build(task,invalid,address));
 const context={LocalExperiment:E,TextEncoder,URL,crypto:webcrypto};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'local-run-package.js'),'utf8'),context);
 assert.deepEqual(Buffer.from(await context.LocalRunPackage.build(task,runner,address)),Buffer.from(bytes),'Browser UMD and CommonJS produce identical archives');
 console.log('PASS local run package: deterministic STORE/CRC/date/UTF8; exact source/task; safe return addresses; Python extraction/run and shared verification; browser parity.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
