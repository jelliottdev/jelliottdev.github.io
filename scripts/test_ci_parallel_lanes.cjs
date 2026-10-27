'use strict';
// Structural workflow regression only: no CI dispatch, source computations or writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),{createHash}=require('node:crypto');
const workflow=fs.readFileSync(require('node:path').join(__dirname,'../.github/workflows/validate-experiments.yml'),'utf8').replace(/\r\n/g,'\n');
function jobs(text){text=text.split('jobs:\n')[1];const matches=[...text.matchAll(/^  ([a-z]+):\n/gm)],out={};for(let i=0;i<matches.length;i++)out[matches[i][1]]=text.slice(matches[i].index,matches[i+1]?.index);return out;}
function runs(text){const lines=text.split('\n'),values=[];for(let i=0;i<lines.length;i++){const m=lines[i].match(/^(?:      - run: |        run: )(.*)$/);if(!m)continue;if(m[1]!=='|'){values.push(m[1]);continue;}const body=[];for(const line of lines.slice(i+1)){if(line.trim()&&!line.startsWith('          '))break;body.push(line.slice(10));}values.push(body.join('\n').trimEnd());}return values;}
function check(text){
 const j=jobs(text);assert.deepEqual(Object.keys(j),['scope','node','science','validate']);
 assert(!/^concurrency:/m.test(text),'Whole-workflow cancellation would discard science');
 for(const lane of [j.node,j.science]){assert(lane.includes('    needs: scope\n'));assert(!lane.match(/^    if:/m));assert(!lane.includes('continue-on-error:'));}
 assert(j.node.includes('group: node-${{ github.workflow }}-${{ github.event_name }}-${{ github.event.pull_request.number || github.ref }}'));
 assert(j.node.includes('cancel-in-progress: true'));assert(j.science.includes('group: science-${{ github.workflow }}-${{ github.event_name }}-${{ github.sha }}'));assert(j.science.includes('cancel-in-progress: false'));
 assert(j.node.includes("python-version: '3.12'"),'Node tests retain the Python runtime used by subprocess fixtures');
 assert.deepEqual(runs(j.node),['node scripts/check_node_test_coverage.cjs','node scripts/run_node_checks.cjs']);
 assert(!j.node.includes('        if:'));assert(!j.science.includes('run_node_checks.cjs'));
 assert(j.validate.includes('    if: ${{ always() }}\n'));assert(j.validate.includes('    needs: [scope, node, science]\n'));
 for(const name of ['scope','node','science'])assert(j.validate.includes(name.toUpperCase()+'_RESULT: ${{ needs.'+name+'.result }}'));
 assert.deepEqual(runs(j.validate),['set -euo pipefail\ntest "$SCOPE_RESULT" = success\ntest "$NODE_RESULT" = success\ntest "$SCIENCE_RESULT" = success']);
 // Snapshot all 102 pre-split run bodies (including baseline shell programs).
 // Moving steps must not silently drop, alter or duplicate any scientific check.
 const original=[...runs(j.scope),...runs(j.node),...runs(j.science)].sort();assert.equal(original.length,102);
 assert.equal(createHash('sha256').update(JSON.stringify(original)).digest('hex'),'32d1bbdcea4c73cfdd525bf7d078577cb97d9fc321ed65c52e3cf670fd3063a9');
 return j;
}
check(workflow);
for(const [from,to] of [['cancel-in-progress: false','cancel-in-progress: true'],['    needs: [scope, node, science]','    needs: [node, science]'],['test "$NODE_RESULT" = success','true'],['    if: ${{ always() }}','    if: ${{ success() }}'],['python scripts/test_export_reproducibility.py','python scripts/test_export_reproducibility_removed.py']])assert.throws(()=>check(workflow.replace(from,to)));
console.log('PASS parallel Node/science lanes preserve all 102 original commands and reject canceled/skipped/failed dependencies at the stable validation gate');
