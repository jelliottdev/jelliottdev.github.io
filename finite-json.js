/* Bounded plain JSON capture without invoking input getters or serialization hooks. */
(function(root){
 'use strict';
 const own=(v,k)=>Object.prototype.hasOwnProperty.call(v,k),native=fn=>Function.prototype.toString.call(fn);
 function objectPrototype(proto){
  if(proto===null||proto===Object.prototype)return true;
  if(Object.getPrototypeOf(proto)!==null)return false;
  const ctor=Object.getOwnPropertyDescriptor(proto,'constructor');
  return ctor&&own(ctor,'value')&&typeof ctor.value==='function'&&native(ctor.value)===native(Object)&&Reflect.ownKeys(proto).every(k=>typeof k==='string')&&JSON.stringify(Object.getOwnPropertyNames(proto).sort())===JSON.stringify(Object.getOwnPropertyNames(Object.prototype).sort());
 }
 function arrayPrototype(proto){
  if(proto===Array.prototype)return true;
  if(!proto||!objectPrototype(Object.getPrototypeOf(proto)))return false;
  const ctor=Object.getOwnPropertyDescriptor(proto,'constructor');
  return ctor&&own(ctor,'value')&&typeof ctor.value==='function'&&native(ctor.value)===native(Array)&&Object.getOwnPropertyDescriptor(ctor.value,'prototype')?.value===proto&&JSON.stringify(Object.getOwnPropertyNames(proto).sort())===JSON.stringify(Object.getOwnPropertyNames(Array.prototype).sort())&&Reflect.ownKeys(proto).filter(k=>typeof k==='symbol').length===Reflect.ownKeys(Array.prototype).filter(k=>typeof k==='symbol').length;
 }
 function capture(value,{maxBytes=8*1024*1024,maxDepth=20,maxNodes=500000}={}){
  if(![maxBytes,maxDepth,maxNodes].every(n=>Number.isSafeInteger(n)&&n>0))throw Error('Invalid finite JSON limits.');
  let bytes=0,nodes=0;const ancestors=new WeakSet(),encoder=new TextEncoder();
  function add(n){bytes+=n;if(bytes>maxBytes)throw Error('Finite JSON exceeds its byte bound.');}
  function string(text){if(text.length>maxBytes)throw Error('Finite JSON exceeds its byte bound.');add(encoder.encode(JSON.stringify(text)).length);return text;}
  function visit(v,depth){
   if(depth>maxDepth||++nodes>maxNodes)throw Error('Finite JSON exceeds its depth or node bound.');
   if(v===null){add(4);return null;}
   if(typeof v==='string')return string(v);
   if(typeof v==='boolean'){add(v?4:5);return v;}
   if(typeof v==='number'&&Number.isFinite(v)){add(JSON.stringify(v).length);return v;}
   if(!v||typeof v!=='object')throw Error('Finite JSON needs ordinary JSON values.');
   if(ancestors.has(v))throw Error('Finite JSON cannot contain cycles.');
   const array=Array.isArray(v),proto=Object.getPrototypeOf(v);if(!(array?arrayPrototype(proto):objectPrototype(proto)))throw Error('Finite JSON needs plain objects and arrays.');
   if(array){const length=Object.getOwnPropertyDescriptor(v,'length');if(!length||!own(length,'value')||!Number.isSafeInteger(length.value)||length.value<0||length.value>maxNodes)throw Error('Finite JSON arrays must be bounded and dense.');}
   const keys=Reflect.ownKeys(v);if(keys.length>maxNodes+1)throw Error('Finite JSON exceeds its node bound.');if(keys.some(k=>typeof k!=='string'))throw Error('Finite JSON cannot contain symbol fields.');
   const fields=new Map();for(const key of keys){const d=Object.getOwnPropertyDescriptor(v,key);if(!d||!own(d,'value')||!d.enumerable&&!(array&&key==='length'))throw Error('Finite JSON fields must be enumerable data.');if(['__proto__','constructor','prototype'].includes(key))throw Error('Finite JSON cannot contain unsafe fields.');fields.set(key,d.value);}
   ancestors.add(v);let result;
   if(array){
    const length=fields.get('length');if(!Number.isSafeInteger(length)||length<0||length>maxNodes||keys.length!==length+1)throw Error('Finite JSON arrays must be bounded and dense.');
    add(2+Math.max(0,length-1));result=[];for(let i=0;i<length;i++){if(!fields.has(String(i)))throw Error('Finite JSON arrays must be dense.');result.push(visit(fields.get(String(i)),depth+1));}
   }else{
    add(2+Math.max(0,keys.length-1));result={};for(const key of keys){string(key);add(1);result[key]=visit(fields.get(key),depth+1);}
   }
   ancestors.delete(v);return result;
  }
  return visit(value,0);
 }
 const api={capture};if(typeof module==='object'&&module.exports)module.exports=api;else root.FiniteJSON=api;
})(typeof globalThis!=='undefined'?globalThis:this);
