"""Fast saved-receipt validation only: no source imports, corpus reads or scans."""
import json, hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
read=lambda n:json.loads((H/n).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=read('receipt.json')
for row in receipt['files']:
    p=H/row['path'];assert p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
assert sha(H/'inputs-frozen.json')==read('target-plan-frozen.json')['inputs_sha256']
assert sha(H/'independent-controls.json')==read('target-plan-frozen.json')['controls_sha256']
assert sha(H/'positive_control_T0.json')==read('target-plan-frozen.json')['t0_sha256']
assert sha(H/'replay.py')==read('target-plan-frozen.json')['runner_sha256']
assert sha(H/'replay-controls-frozen.py')==read('controls-plan-frozen.json')['runner_sha256']
assert sha(H/'scan_results.json')==read('independent-target-audit.json')['output_sha256']
assert receipt['eligible_texts']==84 and receipt['held_texts']==94
assert receipt['global_witnesses_recounted']==21 and receipt['t0_witnesses_recounted']==6
assert read('independent-controls.json')['independent_offset_counts']==103995
assert [x['count'] for x in receipt['real_patterns']]==[593,1445,664,109,47]
for p in H.glob('*.py'):
    assert b'\r\n' not in p.read_bytes(),p.name
print('PASS:',len(receipt['files']),'file hashes, frozen-plan links, saved counts and LF scripts; no target rerun.')
