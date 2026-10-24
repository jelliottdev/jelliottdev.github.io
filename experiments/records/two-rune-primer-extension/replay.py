"""Reproduce in a new temporary output directory; preserve expected results."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import numpy as np
import numba

HERE=Path(__file__).resolve().parent


def stable(value, filename):
    omitted={'seconds'}
    if filename=='controls.json':omitted|={'benchmark_seconds','projected_target_and_null_seconds'}
    if filename=='results.json':omitted|={'controls_sha256'}
    if filename=='independent-check.json':omitted|={'results_sha256'}
    return {key:item for key,item in value.items() if key not in omitted}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,help='Existing parent for the temporary replay directory')
    args=parser.parse_args()
    plan=json.loads((HERE/'plan-frozen.json').read_bytes())
    assert np.__version__==plan['environment']['numpy'] and numba.__version__==plan['environment']['numba'],'Use recorded dependencies; nothing installed automatically.'
    import quick_verify
    quick_verify.verify()
    manifest=json.loads((HERE/'input-manifest.json').read_bytes())
    stages={x['path'] for x in plan['files']}|{x['path'] for x in manifest['files']}|{'plan-frozen.json','summarize.py'}
    expected={name:(HERE/name).read_bytes() for name in ['controls.json','results.json','scores.npy','independent-check.json','page-maxima.json']}
    with tempfile.TemporaryDirectory(prefix='two-rune-replay-',dir=args.parent) as folder:
        stage=Path(folder)
        for name in sorted(stages):
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((HERE/name).read_bytes())
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        for command in ([sys.executable,str(stage/'run.py'),'controls'],[sys.executable,str(stage/'run.py'),'target'],[sys.executable,str(stage/'check.py')],[sys.executable,str(stage/'summarize.py')]):
            subprocess.run(command,cwd=stage,env=env,check=True)
        assert (stage/'scores.npy').read_bytes()==expected['scores.npy'],'Score bytes differ.'
        for name in ['controls.json','results.json','independent-check.json','page-maxima.json']:
            actual=json.loads((stage/name).read_bytes());wanted=json.loads(expected[name])
            if name=='results.json':
                assert actual['controls_sha256']==hashlib.sha256((stage/'controls.json').read_bytes()).hexdigest()
            if name=='independent-check.json':
                assert actual['results_sha256']==hashlib.sha256((stage/'results.json').read_bytes()).hexdigest()
            assert stable(actual,name)==stable(wanted,name),'Deterministic output differs: '+name
        for name,raw in expected.items():assert (HERE/name).read_bytes()==raw,'Expected bytes changed: '+name
    print('PASS: complete controls, target and49null searches reproduced in isolation; deterministic values and score bytes match; expectations unchanged.')


if __name__=='__main__':main()
