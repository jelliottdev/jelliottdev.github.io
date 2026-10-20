"""Rebuild exports with different hash seeds in an isolated checkout copy."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    catalog = json.loads((root / 'data/catalog.json').read_text(encoding='utf-8'))
    paths = {f['path'] for f in catalog['files']}
    paths.update(['data/catalog.json', 'downloads/SHA256SUMS.txt',
                  'llms.txt', 'llms-full.txt', 'robots.txt', 'sitemap.xml'])
    return {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in sorted(paths)}


def build(root, seed):
    result = subprocess.run(
        [sys.executable, 'scripts/build_access_exports.py'], cwd=root,
        env={**os.environ, 'PYTHONHASHSEED': str(seed)}, capture_output=True,
        text=True, encoding='utf-8')
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return snapshot(root)


def compare(first, second):
    changed = sorted(p for p in first.keys() | second.keys()
                     if first.get(p) != second.get(p))
    assert not changed, 'Identical inputs changed export bytes: ' + ', '.join(changed)


def remove_copied_archives(root):
    for name in ['reference-data', 'original-images', 'transcriptions-and-readings']:
        (root / 'downloads' / (name + '.zip')).unlink(missing_ok=True)
    for archive in (root / 'downloads/experiments').glob('*.zip'):
        assert archive.resolve().is_relative_to(root.resolve())
        archive.unlink()


def main():
    with tempfile.TemporaryDirectory(prefix='liberpedia-export-test-', dir=ROOT.parent) as folder:
        target = Path(folder).resolve()
        assert target.is_relative_to(ROOT.parent.resolve()) and target != ROOT.resolve()
        # No hard links: rebuilding this copy must not overwrite checkout files.
        shutil.copytree(ROOT, target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        # Repository archives may have been produced on another OS/zlib version.
        # Establish a fresh baseline in this runtime before testing repeatability.
        remove_copied_archives(target)
        first = build(target, 1)
        compare(first, build(target, 2))
        # Also verify a clean archive rebuild, not only the archive reuse path.
        remove_copied_archives(target)
        compare(first, build(target, 3))
    print('PASS: all cataloged bytes and discovery exports match across three hash seeds, '
          'including a clean rebuild of the collection and experiment archives.')


if __name__ == '__main__':
    main()
