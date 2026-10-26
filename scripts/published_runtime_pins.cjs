'use strict';
/* Historical source identity is explicit. No Git/network fallback and no execution. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const ROOT=path.resolve(__dirname,'..'),PINS=Object.freeze({
 'scripts/published_known_key_projection.py':Object.freeze({sha256:'824029e9b72d0eeaf84890ad5f966c101472c47d5ff47e9d0cf7f0eba1b95aea',extension:'.py'}),
 'tools/research_runner.py':Object.freeze({sha256:'be73adac90d9b7cf7ee8a7b2f11bdd1d7a61974e84b21a5566ca97f37a1d0c61',extension:'.py'}),
 'local-experiment.js':Object.freeze({sha256:'b2f38df4184a36f1462cfea120c1d121dde05babdb29e30f97442d8528b762c2',extension:'.js'})
});
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function retainedPath(source){const pin=Object.hasOwn(PINS,source)&&PINS[source];assert(pin,'Unknown historical runtime source identity');return 'published-sources/runtime/'+pin.sha256+pin.extension;}
function verifySourcePin(pin,{root=ROOT,readFile=fs.readFileSync}={}){
 assert(pin&&typeof pin==='object'&&!Array.isArray(pin)&&Object.keys(pin).length===2&&typeof pin.path==='string'&&typeof pin.sha256==='string'&&/^[a-f0-9]{64}$/.test(pin.sha256),'Invalid source pin');
 assert(/^[a-zA-Z0-9_./-]+$/.test(pin.path)&&!pin.path.startsWith('/')&&!pin.path.split('/').some(p=>!p||p==='.'||p==='..'),'Invalid source path');
 if(Object.hasOwn(PINS,pin.path)){
  assert.equal(pin.sha256,PINS[pin.path].sha256,'Historical source hash does not match its recorded identity: '+pin.path);
  const file=retainedPath(pin.path),bytes=readFile(path.resolve(root,file));assert.equal(hash(bytes),pin.sha256,'Retained historical source changed: '+pin.path);return Object.freeze({sourcePath:pin.path,retainedPath:file,sha256:pin.sha256});
 }
 const bytes=readFile(path.resolve(root,pin.path));assert(hash(bytes)===pin.sha256||hash(bytes.toString('utf8').replace(/\r\n/g,'\n'))===pin.sha256,'Source pin changed: '+pin.path);return Object.freeze({sourcePath:pin.path,sha256:pin.sha256});
}
function verifySourcePins(pins,options){assert(Array.isArray(pins),'Declare source pins');const names=new Set();for(const pin of pins){assert(!names.has(pin?.path),'Duplicate source pin');names.add(pin?.path);verifySourcePin(pin,options);}for(const source of Object.keys(PINS))assert(names.has(source),'Missing historical source identity: '+source);return true;}
module.exports={PINS,retainedPath,verifySourcePin,verifySourcePins};
