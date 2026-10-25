/* Original transformed outputs for explicit inspection; no target execution or public route activation. */
import {INSPECTION_POLICY,readEvidencePage,verifySnapshot} from './factored-evidence-provider.mjs';
export {LIMITS} from './factored-evidence-provider.mjs';
export const readFactoredInspectionEvidencePage=options=>readEvidencePage(INSPECTION_POLICY,options);
export const verifyFactoredInspectionSnapshot=options=>verifySnapshot(INSPECTION_POLICY,options);
