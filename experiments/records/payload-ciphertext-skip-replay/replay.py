"""Replay controls and exact96 payload targets in temporary files; never rewrite expectations."""
import importlib.util,json,shutil,subprocess,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent
def deterministic(value):
    if isinstance(value,dict):return {k:deterministic(v) for k,v in value.items() if k!='seconds'}
    if isinstance(value,list):return [deterministic(x) for x in value]
    return value
def main():
    subprocess.run([sys.executable,'-B',str(H/'check.py')],check=True)
    with tempfile.TemporaryDirectory(prefix='payload-ciphertext-replay-') as tmp:
        stage=Path(tmp)/'reproduction';shutil.copytree(H/'reproduction',stage)
        original=(stage/'controls-results.json').read_bytes();(stage/'controls-results.json').unlink()
        subprocess.run([sys.executable,'-B',str(stage/'controls.py')],check=True)
        assert deterministic(json.loads(original))==deterministic(json.loads((stage/'controls-results.json').read_bytes())),'Deterministic controls differ'
        # Preserve the frozen receipt, including its timing, as required by the target protocol.
        (stage/'controls-results.json').write_bytes(original)
        (stage/'target-results.json').unlink();subprocess.run([sys.executable,'-B',str(stage/'run_target.py')],check=True)
        assert deterministic(json.loads((stage/'target-results.json').read_bytes()))==deterministic(json.loads((H/'reproduction/target-results.json').read_bytes())),'Deterministic target results differ'
        sys.path.insert(0,str(H/'independent'))
        import audit_controls,audit_target
        audit_controls.run(stage);audit_target.run(stage)
        print('PASS: complete144 controls/24 boundaries/96 allocations/96 target beams and independent reconstructions; expected files preserved')
if __name__=='__main__':main()
