/* Fixed official aggregate for large scopes; never fall back to per-page requests. */
import Inputs from '../../local-input-bundle.js';
export const parseInputBundle=Inputs.parse;
export async function loadInputBundle({fetcher=globalThis.fetch,signal,read}){
 if(signal?.aborted)throw Error('Source loading cancelled.');
 let stop;const aborted=new Promise((_,reject)=>{stop=()=>reject(Error('Source loading cancelled.'));signal?.addEventListener('abort',stop,{once:true});});
 try{
  const response=await Promise.race([Promise.resolve().then(()=>fetcher('https://jelliottdev.github.io/data/local-run-inputs.json',{redirect:'manual',signal})),aborted]);
  if(!response.ok)throw Error('The official input bundle is unavailable.');
  return parseInputBundle(await Promise.race([read(response,2*1024*1024),aborted]));
 }finally{signal?.removeEventListener('abort',stop);}
}
