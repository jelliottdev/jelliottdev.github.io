"""Reproduce image-row coverage and check it without replacing saved evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def reproduce(output):
    def call(script, *args):
        subprocess.run([sys.executable, str(ROOT/'scripts'/script), *map(str,args)], check=True, cwd=ROOT)
    result = output/'results.json'
    audit = output/'audit.json'
    call('image_row_coverage.py', '--output', result)
    assert json.loads(result.read_bytes()) == json.loads((HERE/'results.json').read_bytes()), 'Saved result differs'
    call('check_image_row_coverage.py', result, '--receipt', audit)
    call('render_image_row_coverage.py', result, audit, '--output', output/'overlays')
    for saved in (HERE/'overlays').glob('*.svg'):
        assert saved.read_bytes() == (output/'overlays'/saved.name).read_bytes(), saved.name
    print('Saved results and all eight overlays reproduced; independent computation passed.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix='liberpedia-rows-') as directory:
            reproduce(Path(directory))
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        reproduce(args.output)
