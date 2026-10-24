"""One exact L6 A1 source unit, matched to its pinned checkpoint."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT.parent / 'source-cache' / 'dukotah-cicada3301'
SCRIPTS = SOURCE / 'liber-primus/analysis/round18/L6-offset-marsaglia/scripts'
sys.path.insert(0, str(SCRIPTS))
import lib_l6 as X  # noqa: E402

ct = bytes(int(x) for x in X.L.nc.unsolved())
assert len(ct) == 12956 and max(ct) < 29
expected_ct = SOURCE / 'liber-primus/analysis/seed_sweep/ct.bin'
original_read = Path.read_bytes


def source_read(path):
    return ct if path == expected_ct else original_read(path)


Path.read_bytes = source_read
import sweep_offset as S  # noqa: E402

job = S.jobs_for('A1')[0]
start = time.perf_counter()
S._init('A1')
fresh = S._unit_A1(job)
wall = time.perf_counter() - start
path = 'liber-primus/analysis/round18/L6-offset-marsaglia/out/ckpt_A1/0.json'
archived_bytes = subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'HEAD:{path}'])
archived = json.loads(archived_bytes)
if fresh != archived:
    for key in sorted(set(fresh) | set(archived)):
        if fresh.get(key) != archived.get(key):
            print('DIFF', key, 'fresh=', str(fresh.get(key))[:400], 'archived=', str(archived.get(key))[:400])
out = {'schema': 'liberpedia-l6-a1-unit-parity-v1',
       'source_revision': 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1',
       'checkpoint': path,
       'checkpoint_sha256': hashlib.sha256(archived_bytes).hexdigest(),
       'ct_reconstruction_sha256': hashlib.sha256(ct).hexdigest(),
       'unit': 0, 'all_fields_exact': fresh == archived,
       'offsets': fresh['n_offsets'], 'best': fresh['best'], 'elapsed_s': wall}
(HERE / 'pilot-a1.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\n')
print(('PASS' if fresh == archived else 'FAIL'), 'A1 unit 0 checkpoint parity', fresh['n_offsets'], 'offsets', f'{wall:.2f}s')
raise SystemExit(0 if fresh == archived else 1)
