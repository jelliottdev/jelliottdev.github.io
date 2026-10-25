/* Derived-prefix candidates: unchanged original receipts, not new evaluations.
 * The maintained client must independently replay the original output before
 * evaluating the requested prefix. Completion is scoped to this provider scan.
 * No public route activates this versioned policy yet.
 */
import {PREFIX_POLICY,readEvidencePage,verifySnapshot} from './factored-evidence-provider.mjs';
export {LIMITS} from './factored-evidence-provider.mjs';
export const readFactoredPrefixEvidencePage=options=>readEvidencePage(PREFIX_POLICY,options);
export const verifyFactoredPrefixSnapshot=options=>verifySnapshot(PREFIX_POLICY,options);
