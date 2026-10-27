'use strict';
const assert=require('node:assert/strict'),{checkCoverage,explicitWorkflowTests}=require('./check_node_test_coverage.cjs');
const a='scripts/test_registered.cjs',b='scripts/test_workflow.mjs',c='scripts/test_browser.cjs',d='scripts/test_forgotten.cjs';
const input={files:[a,b,c,'scripts/helper.cjs'],manifest:{checks:[{args:[a]}]},workflows:['steps:\n  - run: |\n      node --experimental-sqlite '+b+'\n  - name: node scripts/test_prose.cjs\n# node scripts/test_comment.cjs\n'],exclusions:{[c]:'Manual browser screenshot QA requiring an externally served application and Edge.'}};
assert.deepEqual(checkCoverage(input),{tests:3,registered:1,workflow:1,excluded:1});
assert.throws(()=>checkCoverage({...input,files:[...input.files,d]}),/Unregistered Node test scripts:[\s\S]*test_forgotten/);
assert.deepEqual(checkCoverage({...input,files:[...input.files,d],manifest:{checks:[{args:[a]},{args:['--experimental-sqlite',d]}]}}),{tests:4,registered:2,workflow:1,excluded:1});
assert.throws(()=>checkCoverage({...input,exclusions:{[c]:'manual'}}),/concrete reason/);
assert.throws(()=>checkCoverage({...input,exclusions:{...input.exclusions,[d]:'Manual test requiring an external browser and server.'}}),/Stale/);
assert.throws(()=>checkCoverage({...input,exclusions:{...input.exclusions,[a]:'Manual test requiring an external browser and server.'}}),/also be excluded/);
assert.deepEqual([...explicitWorkflowTests('- run: node scripts/test_direct.cjs\n- name: node scripts/test_prose.cjs\n# node scripts/test_comment.cjs\n')],['scripts/test_direct.cjs']);
assert.throws(()=>checkCoverage({...input,workflows:['# node '+b+'\n- name: node '+b]}),/test_workflow/);
for(const service of ['services/idea-assistant/test_backend.mjs','services/idea-assistant/test-backend.cjs']){
 const withService={...input,files:[...input.files,service]};
 assert.throws(()=>checkCoverage(withService),/Unregistered Node test scripts:[\s\S]*services\/idea-assistant\/test/);
 assert.equal(checkCoverage({...withService,manifest:{checks:[...input.manifest.checks,{args:['--experimental-sqlite',service]}]}}).registered,2);
 assert.equal(checkCoverage({...withService,workflows:[...input.workflows,'- run: node --experimental-sqlite '+service]}).workflow,2);
}
console.log('PASS new unregistered tests fail; manifest and explicit workflow registrations, documented manual exclusions and stale-exclusion guards work');
