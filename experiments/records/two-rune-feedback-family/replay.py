"""Rerun the complete frozen family in a fresh temporary directory; install nothing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
import numba

HERE=Path(__file__).resolve().parent


def control_values(value):
    """Remove only measured runtime/projection fields, never scientific results."""
    omit={'seconds','benchmark','projected_seconds_50whole_searches','all56_projected_seconds_50whole_searches'}
    if isinstance(value,dict):return {k:control_values(v) for k,v in value.items() if k not in omit}
    if isinstance(value,list):return [control_values(v) for v in value]
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent',type=Path);args=parser.parse_args()
    import quick_verify
    quick_verify.verify()
    protocol=json.loads((HERE/'protocol-frozen.json').read_bytes())
    assert np.__version__==protocol['environment']['numpy'] and numba.__version__==protocol['environment']['numba'],'Use recorded packages; no automatic installation.'
    names={row['path'] for row in protocol['files']}|{row['path'] for row in json.loads((HERE/'source-manifest.json').read_bytes())['files']}|{'protocol-frozen.json'}
    outputs=['observed-effective-scores.npy','null-page-maxima-scores.npy','null-page-maxima-primers.npy','observed-witnesses.json','results.json']
    expected={name:(HERE/name).read_bytes() for name in outputs}
    with tempfile.TemporaryDirectory(prefix='two-rune-family-',dir=args.parent) as folder:
        stage=Path(folder)
        for name in sorted(names):
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((HERE/name).read_bytes())
        # Replay every original prototype control in its original local layout.
        # It has no manuscript transcription; benchmark timings may vary.
        control_stage=stage/'control-replay';control_stage.mkdir()
        control_files={'engine.py','source-manifest.json','known-readings.json'}|{row['path'] for row in json.loads((HERE/'source-manifest.json').read_bytes())['files']}
        for name in control_files:
            target=control_stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((HERE/name).read_bytes())
        for name in ('probe.py','proposal-frozen.json'):(control_stage/name).write_bytes((HERE/'prototype'/name).read_bytes())
        subprocess.run([sys.executable,str(control_stage/'probe.py')],cwd=control_stage,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},check=True)
        actual=json.loads((control_stage/'prototype-results.json').read_bytes())
        wanted=json.loads((HERE/'prototype/prototype-results.json').read_bytes())
        assert control_values(actual)==control_values(wanted),'Known-input control outcomes changed.'
        subprocess.run([sys.executable,str(stage/'run.py')],cwd=stage,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},check=True)
        for name in outputs:
            actual=(stage/name).read_bytes()
            if name=='results.json':
                actual=json.loads(actual);wanted=json.loads(expected[name])
                actual.pop('seconds');wanted.pop('seconds');assert actual==wanted,name
            else:assert actual==expected[name],name
        # Independent checker has its own direct formulas/scorer, never imports engine.
        checker=HERE/'independent/audit_run.py'
        assert checker.exists(),'Independent checker missing; keep bundle intact.'
        subprocess.run([sys.executable,str(checker),'--run-root',str(stage),'--check-only'],check=True)
    for name,data in expected.items():assert (HERE/name).read_bytes()==data,'Expected output overwritten: '+name
    print('PASS: complete family+49whole-search nulls match deterministic outputs and exact numeric bytes; expected files unchanged.')


if __name__=='__main__':main()
