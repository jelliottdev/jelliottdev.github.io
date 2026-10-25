/* Original output candidates for the pinned language comparison; client independently verifies and evaluates; private foundation, no route activation. */
import {OUTPUT_POLICY,readEvidencePage,verifySnapshot} from './factored-evidence-provider.mjs';
export {LIMITS} from './factored-evidence-provider.mjs';
export const readFactoredOutputEvidencePage=options=>readEvidencePage(OUTPUT_POLICY,options);
export const verifyFactoredOutputSnapshot=options=>verifySnapshot(OUTPUT_POLICY,options);
