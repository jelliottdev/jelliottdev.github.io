"""Reproduce all candidate streams and controls, then independently check them."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def reproduce(output):
    def call(script,*arguments):
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,arguments)],cwd=ROOT,check=True)
    result=output/'results.json';audit=output/'audit.json';summary=output/'summary.csv'
    call('seed_crib_controls.py','--output',result)
    assert json.loads(result.read_bytes())==json.loads((HERE/'results.json').read_bytes()),'Saved results differ'
    call('check_seed_crib_controls.py',result,'--receipt',audit)
    call('summarize_seed_crib_controls.py',result,audit,'--output',summary)
    assert summary.read_bytes()==(HERE/'summary.csv').read_bytes(),'Saved summary differs'
    from plot import render
    assert render()==(HERE/'prefix-matches.svg').read_text(encoding='utf-8'),'Saved figure differs'
    print('All 8192 streams, 120 result cells, summary and figure verified.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    options=parser.add_mutually_exclusive_group(required=True)
    options.add_argument('--check',action='store_true');options.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix='liberpedia-seeds-') as directory:reproduce(Path(directory))
    else:
        args.output.mkdir(parents=True,exist_ok=False);reproduce(args.output)
