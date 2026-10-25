/* Look up the opposite word grouping; never create or run a comparison task. */
import Variants from '../../task-variants.js';
import {findEvidence} from './task-evidence.mjs';

export async function boundaryComparison({db,task,inputVersion,discoverEvidence=findEvidence,crypto:cryptoAPI=globalThis.crypto}){
 if(task?.criterion?.kind!=='word-affine-count'||!Variants.inspect(task))return null;
 const companion=await Variants.prepare(task,cryptoAPI);
 try{
  const found=await discoverEvidence({db,task:companion,inputVersion,crypto:cryptoAPI});
  const coverage={...found,requestedTask:companion,inputVersion};
  return {task:companion,coverage,...(found.truncated&&found.remainingPages.length?{coverageUnavailable:true}:{})};
 }catch{return {task:companion,coverageUnavailable:true};}
}
