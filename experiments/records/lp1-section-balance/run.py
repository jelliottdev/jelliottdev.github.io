"""Reproduce and independently check the section-preserving balance variant."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def reproduce(output):
    result=output/'results.json';receipt=output/'audit.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/lp1_section_balance.py'),'--output',str(result)],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
    assert json.loads(result.read_bytes())==json.loads((HERE/'results.json').read_bytes()),'Saved result differs'
    subprocess.run([sys.executable,str(ROOT/'scripts/check_lp1_section_balance.py'),str(result),'--receipt',str(receipt)],check=True,cwd=ROOT)
    from plot import render
    for name,content in render().items():
        assert content==(HERE/name).read_text(encoding='utf-8'),name
        (output/name).write_text(content,encoding='utf-8',newline='\n')
    print('All 49,999 scores, exact expectation, figures and histogram reproduced. Baseline plot uses preserved baseline results.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix='liberpedia-sections-') as directory:reproduce(Path(directory))
    else:
        args.output.mkdir(parents=True,exist_ok=False);reproduce(args.output)
