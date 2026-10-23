"""Replay the pinned R18 A program in an isolated temporary source tree.

The source writes a_locus.json beside itself. Staging its exact dependencies in a
temporary directory ensures this command never changes the source checkout.
"""
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable(value):
    return {k: v for k, v in value.items() if k != 'elapsed_s'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True,
                        help='Pinned Dukotah/cicada3301 checkout (repository root)')
    parser.add_argument('--kjv', type=Path, help='Exact recovered kjv.txt; defaults to SOURCE/liber-primus/data/kjv.txt')
    parser.add_argument('--check', action='store_true', help='Compare complete output with the preserved source receipt')
    args = parser.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    imports = json.loads((HERE / 'source-dependencies.json').read_text(encoding='utf-8'))
    root = args.source_root.resolve()
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                       text=True).strip()
    if revision != plan['source_revision']:
        raise ValueError(f'Source checkout revision mismatch: {revision}')
    if imports['source_revision'] != revision:
        raise ValueError('Additional source dependency revision mismatch')
    kjv = args.kjv.resolve() if args.kjv else root / LP / 'data/kjv.txt'
    for rel, expected in plan['source_input_sha256'].items():
        file = root / LP / rel
        if digest(file) != expected:
            raise ValueError(f'Source input hash mismatch: {rel}')
    for rel, expected in imports['sha256'].items():
        if digest(root / LP / rel) != expected:
            raise ValueError(f'Additional source input hash mismatch: {rel}')
    if digest(kjv) != plan['external_kjv_sha256']:
        raise ValueError('KJV source text hash mismatch')
    original = HERE / 'source-output-raw.txt'
    if digest(original) != plan['original_result_sha256']:
        raise ValueError('Preserved original result hash mismatch')

    with tempfile.TemporaryDirectory(prefix='r18-filter-locus-') as tmp:
        staged = Path(tmp) / LP
        needed = list(plan['source_input_sha256']) + list(imports['sha256'])
        for rel in set(needed):
            target = staged / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / LP / rel, target)
        shutil.copyfile(kjv, staged / 'data/kjv.txt')
        script = staged / 'analysis/round18/L2-filter-leak/a_locus.py'
        env = dict(os.environ, PYTHONUTF8='1')
        subprocess.run([sys.executable, str(script), '--reps', '200'],
                       cwd=script.parent, env=env, check=True)
        current = json.loads((script.parent / 'a_locus.json').read_text(encoding='utf-8'))
    source = json.loads(original.read_text(encoding='utf-8'))
    if args.check:
        if stable(current) != stable(source):
            raise AssertionError('A non-timing source result changed')
        print('PASS: every non-timing field matches the pinned source result; source checkout unchanged')
    else:
        print(json.dumps({'non_timing_fields_match': stable(current) == stable(source),
                          'elapsed_s': current['elapsed_s']}, indent=2))


if __name__ == '__main__':
    main()
