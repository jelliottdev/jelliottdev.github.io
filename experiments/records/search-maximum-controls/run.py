"""Reproduce the frozen benchmark; --check compares with the saved result."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'scripts'))
from run_search_maximum_controls import produce

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.check and args.output:parser.error('Choose --check or --output')
    if not args.check and (args.output is None or args.output.exists()):parser.error('Choose a new --output path')
    result=produce()
    if args.check:assert result==json.loads((HERE/'results.json').read_bytes())
    else:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print('All 288 paired searches reproduced')
