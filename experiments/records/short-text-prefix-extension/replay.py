"""Recompute controls and the bounded extension in temporary output; no installation/network."""
import argparse, importlib.util, json, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def compare(a,b):
    a=dict(a);b=dict(b);a.pop('seconds',None);b.pop('seconds',None)
    assert a==b,'Deterministic JSON differs'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='c01-short-prefix-') as t:
        stage=Path(t)/'reproduction';shutil.copytree(H/'reproduction',stage)
        sys.path.insert(0,str(stage));spec=importlib.util.spec_from_file_location('prefix_run',stage/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        (stage/'controls.json').unlink();m.controls(a.inputs)
        compare(read(stage/'controls.json'),read(H/'reproduction/controls.json'))
        # The historical protocol binds original control timing bytes, not replay timings.
        shutil.copyfile(H/'reproduction/controls.json',stage/'controls.json')
        out=Path(t)/'target';m.target(a.inputs,out)
        compare(read(out/'results.json'),read(H/'results.json'))
        with np.load(out/'alignment-scores.npz') as x,np.load(H/'alignment-scores.npz') as y:
            assert x.files==y.files
            for k in x.files:assert np.array_equal(x[k],y[k]),k
        subprocess.run([sys.executable,str(H/'independent/audit_target.py'),'--run-root',str(stage),'--result-root',str(out),'--inputs-root',str(Path(a.inputs).resolve()),'--check-only'],check=True)
        print('PASS: all controls, separate short-text calls, all40,245 raw/integer scores and deterministic reports; expected files untouched.')
if __name__=='__main__':main()
