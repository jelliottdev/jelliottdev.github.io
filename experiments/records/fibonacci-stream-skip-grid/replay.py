"""Portable controls/target replay in isolation; frozen scientific bytes unchanged."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile

import engine as e


def comparison(path):
    value=json.loads(path.read_text(encoding='utf8'))
    value.pop('elapsed_seconds',None)
    return value


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--controls',action='store_true',help='Repeat all841known-reading source plants in the isolated bundle.')
    parser.add_argument('--parity',action='store_true',help='Also repeat8410native50and120full277synthetic alias comparisons.')
    args=parser.parse_args()
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='fib-skip-portable-') as temporary:
        target=e.Path(temporary)
        copied=target/e.HERE.relative_to(e.ROOT)
        shutil.copytree(e.HERE,copied,ignore=shutil.ignore_patterns('__pycache__'))
        for item in plan['inputs']:
            dest=target/item['path']
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(e.ROOT/item['path'],dest)
        def call(name,*arguments):
            subprocess.run([sys.executable,str(copied/name),*arguments],cwd=target,check=True,capture_output=True,text=True)
        call('prove.py')
        assert (copied/'proof-receipt.json').read_bytes()==(e.HERE/'proof-receipt.json').read_bytes()
        assert (copied/'aliases.json').read_bytes()==(e.HERE/'aliases.json').read_bytes()
        if args.parity:
            call('preflight.py','parity')
            assert comparison(copied/'parity-results.json')==comparison(e.HERE/'parity-results.json')
            shutil.copyfile(e.HERE/'parity-results.json',copied/'parity-results.json')
        if args.controls:
            call('preflight.py','controls')
            assert comparison(copied/'control-results.json')==comparison(e.HERE/'control-results.json')
            # Preserve frozen hash-bound receipts before the target input preflight.
            shutil.copyfile(e.HERE/'control-results.json',copied/'control-results.json')
        call('check_preflight.py')
        assert (copied/'preflight-independent-check.json').read_bytes()==(e.HERE/'preflight-independent-check.json').read_bytes()
        print('PASS isolated proof/plant preflight',flush=True)
        call('run.py')
        for name in ['cases.json','short-paths.bin','source-label-summary.json','source-ordered-hits.json']:
            assert (copied/name).read_bytes()==(e.HERE/name).read_bytes(),name
        assert comparison(copied/'results.json')==comparison(e.HERE/'results.json')
    receipt={'schema':'fibonacci-portable-isolated-replay-v1','source_cache_required':False,
             'finite_proof_and_aliases_identical':True,'all841plants_replayed':args.controls,
             'native8410plus120parity_replayed':args.parity,
             'all92510canonical_cases_and_short_paths_byte_identical':True,
             'expanded_source_labels_hits_and_tie_order_byte_identical':True,
             'report_identical_except_elapsed_time':True,'original_plans_and_outputs_preserved':True}
    e.write(e.HERE/'replay-check.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    main()
