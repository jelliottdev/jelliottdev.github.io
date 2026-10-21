"""Replay the six-width experiment, independent checker and figures offline."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def reproduce(output):
    result,receipt = output/'results.json',output/'audit.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/lp1_width_selection.py'),'--output',str(result)],check=True,stdout=subprocess.DEVNULL)
    assert json.loads(result.read_bytes()) == json.loads((HERE/'results.json').read_bytes())
    subprocess.run([sys.executable,str(ROOT/'scripts/check_lp1_width_selection.py'),str(result),'--receipt',str(receipt)],check=True)
    assert json.loads(receipt.read_bytes()) == json.loads((HERE/'audit.json').read_bytes())
    from plot import render
    for name,text in render().items():
        assert text == (HERE/name).read_text(encoding='utf-8')
        (output/name).write_text(text,encoding='utf-8',newline='\n')
    print('All observed and shuffled width scores, receipts and figures reproduced.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true')
    group.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix='liberpedia-widths-') as directory:reproduce(Path(directory))
    else:
        args.output.mkdir(parents=True,exist_ok=False)
        reproduce(args.output)
