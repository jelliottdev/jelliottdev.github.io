/* Strict original-protocol discovery. Legacy wire and cursors remain unchanged. */
import {STRICT_POLICY,readEvidencePage,verifySnapshot} from './factored-evidence-provider.mjs';
export {LIMITS} from './factored-evidence-provider.mjs';
export const readFactoredEvidencePage=options=>readEvidencePage(STRICT_POLICY,options);
export const verifyFactoredSnapshot=options=>verifySnapshot(STRICT_POLICY,options);
