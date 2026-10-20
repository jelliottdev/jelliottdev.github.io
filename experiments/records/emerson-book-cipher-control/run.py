"""Replicate the historical Emerson control, including exact PDF extraction.
Requires Python 3.12 and pypdf==6.19.0. No network requests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def run():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Input hash changed: '+item['path'])
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/reproduce_emerson.py'),'--check-pdf'],
                        capture_output=True,encoding='utf-8',timeout=60)
    if proc.returncode:
        raise RuntimeError('Control reconstruction failed: '+proc.stderr)
    result=json.loads(proc.stdout)
    if result['decoded']!=plan['expected']:raise ValueError('Unexpected reconstructed string')
    return {'schema':'liberpedia-emerson-control-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'pdf_paragraphs_verified':50,'coordinate_lookups':sum(':' in r['entry'] for r in result['trace']),
            'literal_characters':sum(':' not in r['entry'] for r in result['trace']),
            'result':result}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--output',type=Path)
    args=parser.parse_args();result=run()
    if args.check:
        if result!=json.loads((HERE/'results.json').read_text(encoding='utf-8')):raise SystemExit('Rerun differs')
        print('PDF paragraphs and complete lookup trace reproduce exactly.')
    else:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('pdf_paragraphs_verified','coordinate_lookups','literal_characters')}))
if __name__=='__main__':main()
