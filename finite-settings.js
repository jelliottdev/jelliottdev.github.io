/* Explicit finite settings only. Each detached member still needs the fixed-plan compiler. */
(function(root){
 'use strict';
 const node=typeof module==='object'&&module.exports,C=node?require('./claim-specification.js'):root.ClaimSpecification,H=node?require('./claim-share.js'):root.ClaimShare;
 const LIMITS=Object.freeze({programs:1024,cases:4096,pages:75,operations:8,parameters:56,expandedBytes:8*1024*1024});
 const FACTORED_LIMITS=Object.freeze({...LIMITS,cases:76800});
 const NAMES=new Set(['a','b','reset','unit','key','direction','interrupts','offset']);
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(key=>Object.hasOwn(v,key));
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const stable=v=>C.serialize(v),clone=v=>JSON.parse(stable(v));
 function capture(value,depth=0,budget={nodes:0}){
  if(depth>16||++budget.nodes>6000)throw Error('Finite settings exceed the card structure bounds.');
  if(value===null||typeof value==='boolean'||typeof value==='string')return value;
  if(typeof value==='number'&&Number.isFinite(value))return value;
  if(Array.isArray(value)){
   if(Reflect.ownKeys(value).length!==value.length+1)throw Error('Finite settings arrays must contain only dense JSON values.');
   const out=[];for(let i=0;i<value.length;i++){const d=Object.getOwnPropertyDescriptor(value,String(i));if(!d||!Object.hasOwn(d,'value')||!d.enumerable)throw Error('Finite settings arrays must contain only data.');out.push(capture(d.value,depth+1,budget));}return out;
  }
  if(!value||typeof value!=='object'||![Object.prototype,null].includes(Object.getPrototypeOf(value)))throw Error('Finite settings must be JSON data.');
  const out={};for(const key of Reflect.ownKeys(value)){
   if(typeof key!=='string'||['__proto__','prototype','constructor'].includes(key))throw Error('Unsafe finite settings field.');
   const d=Object.getOwnPropertyDescriptor(value,key);if(!Object.hasOwn(d,'value')||!d.enumerable)throw Error('Finite settings fields must contain data.');out[key]=capture(d.value,depth+1,budget);
  }return out;
 }
 function canonical(card){
  const value=capture(card),text=JSON.stringify(value);if(new TextEncoder().encode(text).length>H.MAX_BYTES)throw Error('Finite settings exceed the canonical card byte limit.');
  let binary='';for(const byte of new TextEncoder().encode(text))binary+=String.fromCharCode(byte);
  const imported=H.decode('#idea='+btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')),confirmed=C.confirm(imported.draft,{id:'finite-settings-validation',at:'2000-01-01T00:00:00.000Z'}),normalized=H.cardData(confirmed);
  if(stable(value)!==stable(normalized))throw Error('Finite settings require a canonical confirmed idea card.');return normalized;
 }
 function literal(name,value){
  if(name==='a'||name==='b'){if(!Number.isInteger(value)||value<0||value>28)throw Error('Affine alternatives must be indices from 0 to 28.');}
  else if(name==='offset'){if(!Number.isInteger(value)||value<0||value>28)throw Error('Sequence offsets must be integers from 0 to 28.');}
  else if(name==='reset'||name==='unit'){if(!['page','line','word'].includes(value))throw Error('Boundary alternatives must be page, line or word.');}
  else if(name==='direction'){if(!['subtract','add'].includes(value))throw Error('Arithmetic alternatives must be add or subtract.');}
  else if(name==='key'||name==='interrupts'){
   if(!Array.isArray(value)||!value.length||value.length>(name==='key'?20000:29)||value.some(n=>!Number.isInteger(n)||n<0||n>28))throw Error('Key alternatives must be explicit GP index arrays.');
   if(name==='interrupts'&&value.some((n,i)=>i>0&&n<=value[i-1]))throw Error('Interrupter alternatives must be sorted distinct GP indices.');
  }else throw Error('This finite parameter is not supported.');
  return clone(value);
 }
 function compare(a,b){
  if(typeof a==='number'&&typeof b==='number')return a-b;
  if(Array.isArray(a)&&Array.isArray(b)){for(let i=0;i<Math.min(a.length,b.length);i++){const n=a[i]-b[i];if(n)return n;}return a.length-b.length;}
  const left=stable(a),right=stable(b);return left<right?-1:left>right?1:0;
 }
 const byteLength=value=>new TextEncoder().encode(stable(value)).length;
 function memberCard(card,settings){
  const member=clone(card);member.rules.searchBounds={status:'not_applicable'};for(const setting of settings)member.method.value.operations[setting.operation][setting.name]=clone(setting.value);return canonical(member);
 }
 function parse(input,limits=LIMITS){
  const card=canonical(input),bound=card.rules.searchBounds;
  if(bound.status!=='specified'||!exact(bound.value,['kind','version','parameters'])||bound.value.kind!=='finite-settings'||bound.value.version!==1)throw Error('Declare a version 1 finite-settings search bound.');
  if(card.method.status!=='specified'||!Array.isArray(card.method.value.operations)||!card.method.value.operations.length||card.method.value.operations.length>LIMITS.operations)throw Error('Finite settings need one to eight ordered method operations.');
  if(card.scope.status!=='specified'||!exact(card.scope.value,['pages'])||!Array.isArray(card.scope.value.pages)||!card.scope.value.pages.length||card.scope.value.pages.length>LIMITS.pages)throw Error('Finite settings need exact complete pages.');
  const axes=bound.value.parameters;if(!Array.isArray(axes)||!axes.length||axes.length>LIMITS.parameters)throw Error('Declare a bounded nonempty list of finite parameters.');
  const seen=new Set();let programCount=1;
  const parameters=axes.map(axis=>{
   const referenced=Object.hasOwn(axis||{},'valuesFrom');
   if(!exact(axis,['operation','name',referenced?'valuesFrom':'values'])||!Number.isSafeInteger(axis.operation)||axis.operation<0||axis.operation>=card.method.value.operations.length||!NAMES.has(axis.name)||referenced&&axis.name!=='key')throw Error('A finite parameter must name an existing operation, supported setting and explicit values or a pinned key bank.');
   let alternatives=axis.values;
   if(referenced){
    const ref=axis.valuesFrom;if(!exact(ref,['bankId','bankSha256','start','count'])||typeof ref.bankId!=='string'||typeof ref.bankSha256!=='string'||!Number.isSafeInteger(ref.start)||ref.start<0||!Number.isSafeInteger(ref.count)||ref.count<1||ref.count>LIMITS.programs)throw Error('Use an exact bounded pinned key-bank range.');
    const banks=node?require('./repeating-key-banks.js'):root.RepeatingKeyBanks;if(!banks?.resolve)throw Error('The maintained repeating-key banks are unavailable.');alternatives=banks.resolve(ref);
    if(!Object.isFrozen(alternatives)||!Array.isArray(alternatives)||alternatives.some(value=>!Object.isFrozen(value))||alternatives.length!==ref.count)throw Error('The maintained key-bank resolution changed.');
   }
   if(!Array.isArray(alternatives)||!alternatives.length||alternatives.length>LIMITS.programs)throw Error('A finite parameter needs one to 1024 explicit alternatives.');
   const key=axis.operation+'|'+axis.name;if(seen.has(key))throw Error('A finite parameter is declared more than once.');seen.add(key);
   if(Object.hasOwn(card.method.value.operations[axis.operation],axis.name))throw Error('Finite settings cannot replace a supplied fixed method parameter.');
   const values=alternatives.map(value=>literal(axis.name,value)),identities=new Set(values.map(stable));if(identities.size!==values.length)throw Error('A finite parameter repeats an alternative.');values.sort(compare);
   programCount*=values.length;if(programCount>LIMITS.programs)throw Error('Finite settings exceed 1024 programs; no alternatives were truncated.');return {operation:axis.operation,name:axis.name,values};
  }).sort((a,b)=>a.operation-b.operation||(a.name<b.name?-1:a.name>b.name?1:0));
  const caseCount=programCount*card.scope.value.pages.length;if(caseCount>limits.cases)throw Error('Finite settings exceed '+limits.cases+' program-page cases; no cases were truncated.');
  const declaration={kind:'finite-settings',version:1,parameters,programCount,caseCount};
  // Measure one maximum-size member before allocating a Cartesian expansion.
  // This upper bound includes settings, cards, separators and the declaration.
  const largest=parameters.map(axis=>({operation:axis.operation,name:axis.name,value:axis.values.reduce((a,b)=>byteLength(a)>=byteLength(b)?a:b)})),maxMember={settings:largest,card:memberCard(card,largest)};
  if(byteLength({declaration,variants:[]})+programCount*(byteLength(maxMember)+1)>LIMITS.expandedBytes)throw Error('Finite settings exceed the 8 MiB detached expansion budget; no alternatives were truncated.');
  return {card,declaration};
 }
 function inspect(card){return freeze(parse(card).declaration);}
 function expand(input,limits=LIMITS){
  const {card,declaration}=parse(input,limits),variants=[];
  function visit(index,settings){
   if(index<declaration.parameters.length){const axis=declaration.parameters[index];for(const value of axis.values)visit(index+1,[...settings,{operation:axis.operation,name:axis.name,value}]);return;}
   // Reuse the canonical card boundary, not a parallel operation compiler.
   variants.push({settings:clone(settings),card:memberCard(card,settings)});
  }
  visit(0,[]);return freeze({declaration,variants});
 }
 function member(input,supplied,limits=LIMITS){
  const {card,declaration}=parse(input,limits),assignments=capture(supplied);
  if(!Array.isArray(assignments)||assignments.length!==declaration.parameters.length)throw Error('Select exactly one value for every declared finite parameter.');
  const selected=new Map(),axes=new Map(declaration.parameters.map(axis=>[axis.operation+'|'+axis.name,axis]));
  for(const setting of assignments){
   if(!exact(setting,['operation','name','value'])||!Number.isSafeInteger(setting.operation)||typeof setting.name!=='string')throw Error('A finite member assignment is malformed.');
   const key=setting.operation+'|'+setting.name,axis=axes.get(key);if(!axis||selected.has(key))throw Error('A finite member contains an unknown or repeated assignment.');
   const value=literal(axis.name,setting.value),declared=axis.values.find(candidate=>stable(candidate)===stable(value));if(declared===undefined)throw Error('A finite member value is outside its declared alternatives.');selected.set(key,declared);
  }
  const settings=declaration.parameters.map(axis=>({operation:axis.operation,name:axis.name,value:clone(selected.get(axis.operation+'|'+axis.name))}));
  return freeze({declaration,settings,card:memberCard(card,settings)});
 }
 const factored=Object.freeze({inspect:card=>freeze(parse(card,FACTORED_LIMITS).declaration),expand:card=>expand(card,FACTORED_LIMITS),member:(card,settings)=>member(card,settings,FACTORED_LIMITS),LIMITS:FACTORED_LIMITS});
 const api={inspect,expand:card=>expand(card),member:(card,settings)=>member(card,settings),factored,LIMITS};if(node)module.exports=api;else root.FiniteSettings=api;
})(typeof globalThis!=='undefined'?globalThis:this);
