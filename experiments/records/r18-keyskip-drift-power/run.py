"""Run the pinned R18 F0 gate and full B experiment in an isolated source copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LP = Path('liber-primus')
TIMING = {'elapsed_s', 'sec_per_decode', 'sec'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without_timing(value):
    if isinstance(value, dict):
        return {k: without_timing(v) for k, v in value.items() if k not in TIMING}
    if isinstance(value, list):
        return [without_timing(v) for v in value]
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root', type=Path, required=True,
                    help='Pinned Dukotah/cicada3301 repository root')
    ap.add_argument('--kjv', type=Path,
                    help='Exact KJV input; defaults to SOURCE/liber-primus/data/kjv.txt')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    root = args.source_root.resolve()
    rev = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if rev != plan['source_revision']:
        raise ValueError(f'Source revision mismatch: {rev}')
    kjv = args.kjv.resolve() if args.kjv else root / LP / 'data/kjv.txt'
    if sha(kjv) != plan['external_kjv_sha256']:
        raise ValueError('KJV bytes do not match frozen plan')
    for rel, expected in plan['source_input_sha256'].items():
        if sha(root / LP / rel) != expected:
            raise ValueError(f'Source input mismatch: {rel}')
    if sha(HERE / 'source-output-raw.txt') != plan['original_result_sha256']:
        raise ValueError('Original source result receipt mismatch')
    if sha(HERE / 'source-gate.json') != plan['source_gate_sha256']:
        raise ValueError('Original F0 gate receipt mismatch')

    with tempfile.TemporaryDirectory(prefix='r18-drift-power-') as tmp:
        stage = Path(tmp) / LP
        for rel in plan['source_input_sha256']:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / LP / rel, dest)
        shutil.copyfile(kjv, stage / 'data/kjv.txt')
        folder = stage / 'analysis/round18/L2-filter-leak'
        env = dict(os.environ, PYTHONUTF8='1')
        subprocess.run([sys.executable, str(folder / 'fastbeam.py')],
                       cwd=folder, env=env, check=True)
        gate = json.loads((folder / 'gate_F0.json').read_text(encoding='utf-8'))
        if not gate['pass'] or gate['cases'] != 24 or gate['path_mismatches'] != 0:
            raise AssertionError('F0 blocking gate failed')
        source_gate = json.loads((HERE / 'source-gate.json').read_text(encoding='utf-8'))
        if without_timing(gate) != without_timing(source_gate):
            raise AssertionError('F0 result differs from source receipt')
        subprocess.run([sys.executable, str(folder / 'b_drawcount.py')],
                       cwd=folder, env=env, check=True)
        replayed = json.loads((folder / 'b_drawcount.json').read_text(encoding='utf-8'))
        # Save the exact output outside the temporary tree for publication.
        (HERE / 'replayed-output-raw.txt').write_bytes((folder / 'b_drawcount.json').read_bytes())
    source = json.loads((HERE / 'source-output-raw.txt').read_text(encoding='utf-8'))
    if args.check:
        if without_timing(replayed) != without_timing(source):
            raise AssertionError('A non-timing source result changed')
        print('PASS: F0 parity and all B non-timing results; source checkout unchanged')
    else:
        print(json.dumps({'f0_pass': True,
                          'non_timing_fields_match': without_timing(replayed) == without_timing(source)}, indent=2))


if __name__ == '__main__':
    main()
