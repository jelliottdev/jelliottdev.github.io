"""Check declared bundle bytes and saved gate arithmetic, without repeating searches."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent


def verify():
    record_path=HERE/'record.json'
    if record_path.exists():
        record=json.loads(record_path.read_bytes());prefix='experiments/records/'+record['id']+'/'
        for role in ('inputs','outputs'):
            for row in record['reproduction'][role]:
                assert row['path'].startswith(prefix),row['path']
                raw=(HERE/row['path'][len(prefix):]).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
    r=json.loads((HERE/'results.json').read_bytes());controls=json.loads((HERE/'controls.json').read_bytes())
    assert controls['pass'] and len(controls['controls'])==6
    assert {x['text'] for x in controls['controls']}=={'source-control','warning'}
    assert all(x['complete_recovery'] and x['strictly_higher_candidates']==0 and x['tied_candidates_including_truth']==1 for x in controls['controls'])
    scores=np.load(HERE/'scores.npy',allow_pickle=False)
    assert scores.shape==(50,55,841) and np.isfinite(scores).all()
    assert hashlib.sha256((HERE/'scores.npy').read_bytes()).hexdigest()==r['scores_sha256']
    assert float(np.max(scores[0]))==r['observed']['best']['score']
    assert r['null_ge_observed']==sum(float(np.max(s))>=r['observed']['best']['score'] for s in scores[1:])
    assert r['hit_bar']==max(-5.5,float(np.max(scores[1:]))+.5)
    assert int(np.sum(scores[0]>=r['hit_bar']))==len(r['gate_hits'])
    print('PASS: declared hashes and saved full-grid gate arithmetic; no searches run.')


if __name__=='__main__':verify()
