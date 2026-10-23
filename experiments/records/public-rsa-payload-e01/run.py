"""Run the pinned Round 18 E-01 source in an isolated temporary checkout."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
SOURCE_RELPATH = 'liber-primus/analysis/round18/L5-payload'


def verify_inputs():
    for row in PLAN['inputs']:
        actual = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
        assert actual == row['sha256'], row['path']


def execute():
    verify_inputs()
    with tempfile.TemporaryDirectory(prefix='liberpedia-e01-') as temp:
        copied = Path(temp) / 'source'
        shutil.copytree(HERE / 'source', copied)
        path = copied / SOURCE_RELPATH / 'e01_extended.py'
        completed = subprocess.run([sys.executable, str(path)], cwd=copied,
                                   capture_output=True, text=True, check=True)
        assert 'CONTROL VERDICT: PASS' in completed.stdout
        actual = json.loads((copied / SOURCE_RELPATH / 'e01_results.json').read_text(encoding='utf-8'))
    expected = json.loads((HERE / 'source-expected.json').read_text(encoding='utf-8'))
    stable = ('moduli', 'payload_variants', 'exponents', 'matchers',
              'tuples_evaluated', 'tuples_skipped', 'hits', 'rows')
    for name in stable:
        assert actual[name] == expected[name], name
    assert actual['control_verdict'] == 'PASS'
    assert all(item['fired'] for item in actual['controls']['positive'].values())
    negative = actual['controls']['negative']
    assert negative['trials'] == 10000
    assert all(value['strict'] == 0 for value in negative['hits'].values())
    assert actual['tuples_evaluated'] == 162 and len(actual['tuples_skipped']) == 12
    return {'schema': 'liberpedia-public-rsa-payload-e01-v1',
            'plan_sha256': hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest(),
            'source_revision': PLAN['source_revision'],
            'source_row_match': True,
            'controls': {'positive_all_fire': True, 'random_trials': negative['trials'],
                         'random_strict_hits': sum(x['strict'] for x in negative['hits'].values())},
            'modulus_bits': [x['bits'] for x in actual['moduli']],
            'payload_variants': actual['payload_variants'], 'exponents': actual['exponents'],
            'matcher_names': actual['matchers'],
            'tuples_evaluated': actual['tuples_evaluated'],
            'invalid_rsa_inputs_skipped': len(actual['tuples_skipped']),
            'structural_hits': actual['hits'],
            'strict_hit_count': sum(x['tier'] == 'strict' for x in actual['rows']),
            'loose_hit_count': sum(x['tier'] == 'loose' for x in actual['rows']),
            'source_rows_sha256': hashlib.sha256(json.dumps(actual['rows'], sort_keys=True,
                                                           separators=(',', ':')).encode()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    value = execute()
    if args.check:
        assert value == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    else:
        (HERE / 'results.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print({k: value[k] for k in ('tuples_evaluated', 'invalid_rsa_inputs_skipped', 'strict_hit_count', 'loose_hit_count')})
