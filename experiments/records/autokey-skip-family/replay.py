"""Full replay in temporary directories; expected outputs are never rewritten."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
def deterministic(value):
    if isinstance(value,dict):return {k:deterministic(v) for k,v in value.items() if k not in ('seconds','seconds_per_call','projected_target_seconds')}
    if isinstance(value,list):return [deterministic(x) for x in value]
    return value
def main():
    p=argparse.ArgumentParser();p.add_argument('--transcription',required=True);a=p.parse_args();raw=Path(a.transcription).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='5e0003aa7f7dde3b238d17c5f964790dbf6bf9db5edacc4a5ec0bad81c6f4bce'
    subprocess.run([sys.executable,'-B',str(H/'check.py')],check=True)
    with tempfile.TemporaryDirectory(prefix='autokey-skip-replay-') as tmp:
        stage=Path(tmp)/'reproduction';shutil.copytree(H/'reproduction',stage)
        (stage/'source/liber-primus/data/krisyotam_runes.txt').write_bytes(raw)
        original=(stage/'controls-results.json').read_bytes();(stage/'controls-results.json').unlink()
        subprocess.run([sys.executable,'-B',str(stage/'controls.py')],check=True)
        assert deterministic(json.loads(original))==deterministic(json.loads((stage/'controls-results.json').read_bytes())),'Deterministic controls differ'
        (stage/'controls-results.json').write_bytes(original)
        for name in ('results.json','measurements.npz'):(stage/name).unlink()
        subprocess.run([sys.executable,'-B',str(stage/'run_target.py')],check=True)
        # NPZ compressed-container bytes need not be used as a scientific comparison.
        expected=json.loads((H/'reproduction/results.json').read_bytes());actual=json.loads((stage/'results.json').read_bytes())
        expected.pop('measurements_sha256');actual.pop('measurements_sha256')
        assert deterministic(expected)==deterministic(actual),'Deterministic target results differ'
        with np.load(stage/'measurements.npz') as got,np.load(H/'reproduction/measurements.npz') as wanted:
            assert set(got.files)==set(wanted.files)
            for name in wanted.files:assert np.array_equal(got[name],wanted[name]),name
        subprocess.run([sys.executable,'-B',str(H/'independent/audit_target.py'),'--producer-root',str(stage),'--check-only'],check=True)
        print('PASS: complete controls/9,900-case replay, every measurement/output array and independent audit; expected files preserved')
if __name__=='__main__':main()
