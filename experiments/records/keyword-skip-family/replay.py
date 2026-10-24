"""Replay unchanged frozen controls and target into temporary files; compare expected evidence."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
def normalized(value):
    if isinstance(value,dict):return {k:normalized(v) for k,v in value.items() if k not in ('seconds','seconds_per_call','projected_target_screen_seconds')}
    if isinstance(value,list):return [normalized(x) for x in value]
    return value
def main():
    p=argparse.ArgumentParser();p.add_argument('--transcription',required=True);a=p.parse_args();raw=Path(a.transcription).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='5e0003aa7f7dde3b238d17c5f964790dbf6bf9db5edacc4a5ec0bad81c6f4bce'
    subprocess.run([sys.executable,'-B',str(H/'check.py')],check=True)
    with tempfile.TemporaryDirectory(prefix='keyword-skip-replay-') as tmp:
        stage=Path(tmp)/'reproduction';shutil.copytree(H/'reproduction',stage)
        (stage/'source/liber-primus/data/krisyotam_runes.txt').write_bytes(raw)
        original=(stage/'controls-results.json').read_bytes();(stage/'controls-results.json').unlink()
        subprocess.run([sys.executable,'-B',str(stage/'controls.py')],check=True)
        assert normalized(json.loads(original))==normalized(json.loads((stage/'controls-results.json').read_bytes())),'Deterministic control results differ'
        # Restore the frozen timing-bearing receipt required by the target protocol.
        (stage/'controls-results.json').write_bytes(original)
        for name in ('results.json','screen-scores.npy','phase-selections.npy','full-survivors.json'):(stage/name).unlink()
        subprocess.run([sys.executable,'-B',str(stage/'run_target.py')],check=True)
        for name in ('results.json','full-survivors.json'):
            assert normalized(json.loads((stage/name).read_bytes()))==normalized(json.loads((H/'reproduction'/name).read_bytes())),name
        for name in ('screen-scores.npy','phase-selections.npy'):
            assert np.array_equal(np.load(stage/name),np.load(H/'reproduction'/name)),name
        audit=H/'independent/audit_target.py'
        if audit.exists():subprocess.run([sys.executable,'-B',str(audit),'--producer-root',str(stage),'--check-only'],check=True)
        print('PASS: complete synthetic controls and target replay; deterministic results/score arrays unchanged; expected files preserved')
if __name__=='__main__':main()
