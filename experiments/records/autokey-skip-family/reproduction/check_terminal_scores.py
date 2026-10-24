"""Pre-target source-string score parity for the separately compiled normalizer."""
import hashlib,json
from pathlib import Path
import numpy as np
import engine as e
from terminal_scores import normalized
H=Path(__file__).resolve().parent
if __name__=='__main__':
    d=json.loads((H/'controls-results.json').read_bytes());count=0;err=0.
    for x in d['domain']:
        paths=e.terminals(x['ciphertext'],x['primer'],x['sign'],450,x['mode'])[0]
        got=normalized(paths);want=np.asarray([e.Q.score_norm(e.text(p)) for p in paths]);count+=len(paths);err=max(err,float(np.max(np.abs(got-want))))
        assert np.array_equal(got,want)
    assert count>0
    r=dict(stage='Synthetic only; no manuscript opened',normalizer_sha256=hashlib.sha256((H/'terminal_scores.py').read_bytes()).hexdigest(),check_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),controls_results_sha256=hashlib.sha256((H/'controls-results.json').read_bytes()).hexdigest(),terminal_paths=count,maximum_absolute_error=err,exact=err==0.,reporting_note='Supersedes an unfrozen one-line draft receipt whose check was accidentally not called and reported zero paths; this script asserts nonempty checked coverage before target.')
    (H/'terminal-score-parity.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print(r)
