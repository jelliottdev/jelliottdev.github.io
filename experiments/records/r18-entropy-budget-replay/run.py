"""Replay the pinned Round 18 C calculation in a temporary source tree."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root', required=True, type=Path)
    ap.add_argument('--kjv', type=Path)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    root = args.source_root.resolve()
    rev = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if rev != plan['source_revision']:
        raise ValueError(f'Source revision mismatch: {rev}')
    kjv = args.kjv.resolve() if args.kjv else root / LP / 'data/kjv.txt'
    if sha(kjv) != plan['external_kjv_sha256']:
        raise ValueError('KJV input hash mismatch')
    for rel, expected in plan['source_input_sha256'].items():
        if sha(root / LP / rel) != expected:
            raise ValueError(f'Source input hash mismatch: {rel}')
    if sha(HERE / 'source-output-raw.txt') != plan['original_result_sha256']:
        raise ValueError('Preserved source output hash mismatch')
    with tempfile.TemporaryDirectory(prefix='r18-entropy-') as tmp:
        stage = Path(tmp) / LP
        for rel in plan['source_input_sha256']:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / LP / rel, dest)
        shutil.copyfile(kjv, stage / 'data/kjv.txt')
        folder = stage / 'analysis/round18/L2-filter-leak'
        env = dict(os.environ, PYTHONUTF8='1')
        subprocess.run([sys.executable, str(folder / 'c_budget.py')],
                       cwd=folder, env=env, check=True)
        output_bytes = (folder / 'c_budget.json').read_bytes()
    (HERE / 'replayed-output-raw.txt').write_bytes(output_bytes)
    replay = json.loads(output_bytes.decode('utf-8'))
    source = json.loads((HERE / 'source-output-raw.txt').read_text(encoding='utf-8'))
    if args.check:
        if source != replay:
            raise AssertionError('Source C output fields differ')
        print('PASS: every source C result field matches; source checkout unchanged')
    else:
        print(json.dumps({'all_fields_match': source == replay}, indent=2))


if __name__ == '__main__':
    main()
