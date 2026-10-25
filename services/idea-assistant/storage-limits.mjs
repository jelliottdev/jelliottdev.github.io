/* Global daily storage ceilings, separate from request/rate and payload limits. */
export const STORAGE_LIMITS=Object.freeze({tasks:5000,results:5000,taskIdeaLinks:10000,preparations:10000});
// Lower-only overrides let boundary tests exercise the same atomic SQL without
// manufacturing thousands of unrelated scientific receipts.
export function storageLimits(overrides={}){
 if(!overrides||typeof overrides!=='object'||Array.isArray(overrides)||![Object.prototype,null].includes(Object.getPrototypeOf(overrides))||Object.getOwnPropertySymbols(overrides).length)throw Error('Invalid storage limits');
 const limits={...STORAGE_LIMITS};
 for(const key of Object.getOwnPropertyNames(overrides)){
  const field=Object.getOwnPropertyDescriptor(overrides,key);
  if(!Object.hasOwn(limits,key)||!field.enumerable||!Object.hasOwn(field,'value')||!Number.isSafeInteger(field.value)||field.value<1||field.value>STORAGE_LIMITS[key])throw Error('Invalid storage limit override');
  limits[key]=field.value;
 }
 return Object.freeze(limits);
}
