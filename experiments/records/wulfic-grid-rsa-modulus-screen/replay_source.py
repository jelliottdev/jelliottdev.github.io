"""Run only original Stage X1/X3 and compare every preserved row."""
import argparse
import csv
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from run import grid_bytes

HERE = Path(__file__).resolve().parent
HEADER = ('part', 'test', 'reading', 'value', 'reference', 'detail', 'verdict')


def encoded(rows):
    text = io.StringIO(newline='')
    writer = csv.writer(text, delimiter='\t', lineterminator='\n')
    writer.writerow(HEADER)
    writer.writerows(rows)
    return text.getvalue().encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    parser.add_argument('--save', action='store_true', help='Save reproduced component rows locally')
    args = parser.parse_args()
    root = args.source_root.resolve()
    plan = json.loads((HERE / 'plan.json').read_text())
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == plan['source_revision']
    for name, digest in plan['source_sha256'].items():
        original = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=root)
        assert hashlib.sha256(original).hexdigest() == digest, name
        if name.endswith('.py'):
            assert (root / name).read_bytes() == original, 'Working source differs: ' + name
    raw = subprocess.check_output(['git', 'show', 'HEAD:reference/findings/stage_x_other.tsv'], cwd=root)
    table = list(csv.reader(io.StringIO(raw.decode()), delimiter='\t'))
    expected = encoded([row for row in table[1:] if row[0] in ('X1', 'X3')])
    sys.path.insert(0, str(root))
    module = importlib.import_module('tools.run_stage_x')
    grid = np.frombuffer(grid_bytes(), dtype=np.uint8)
    dependency = json.loads((HERE / 'dependency-amendment.json').read_text())
    assert hashlib.sha256((root / dependency['source_corpus']).read_bytes()).hexdigest() == dependency['sha256']
    assert module.keys.grid_bytes(module.load_corpus()) == grid.tolist(), 'Source and site grid bytes differ'
    actual = encoded(module.x1_rows(grid, 100000) + module.x3_rows(grid))
    assert actual == expected, 'Original source component differs from its committed table'
    target = HERE / 'source-x1-x3.tsv'
    if args.save:
        assert not target.exists(), 'Refuse to overwrite a frozen source receipt'
        target.write_bytes(actual)
    else:
        assert target.read_bytes() == actual
    print('PASS: all 7 X1 and 4 X3 rows reproduce byte-for-byte')


if __name__ == '__main__':
    main()
