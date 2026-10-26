"""Rebuild exports with different hash seeds in an isolated checkout copy."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REBUILT_COLLECTION_ARCHIVES = (
    'reference-data.zip', 'original-images.zip',
    'transcriptions-and-readings.zip',
)


def rebuilt_archive(name):
    """The first build regenerates these archives, so never copy their old bytes."""
    path = PurePosixPath(name)
    return ((len(path.parts) == 2 and path.parts[0] == 'downloads'
             and path.name in REBUILT_COLLECTION_ARCHIVES)
            or (len(path.parts) == 3 and path.parts[:2] == ('downloads', 'experiments')
                and path.suffix == '.zip'))


def copy_tracked_checkout(source, target):
    """Copy indexed paths using current worktree bytes, without visiting untracked trees.

    Git supplies inventory only: using committed/index blob bytes would hide local
    publication edits. Reject unsupported index states and link escapes before
    copying, and use independent regular files so builds cannot change the source.
    """
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError('The isolated checkout must be separate from its source.')
    top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=source)
    if Path(os.fsdecode(top).strip()).resolve() != source:
        raise ValueError('The source must be the Git checkout root.')
    inventory = subprocess.check_output(['git', 'ls-files', '--cached', '--stage', '-z'], cwd=source)
    selected, seen = [], set()
    for entry in inventory.split(b'\0'):
        if not entry:
            continue
        header, raw_name = entry.split(b'\t', 1)
        mode, _object_id, stage = header.split()
        name = os.fsdecode(raw_name)
        path = PurePosixPath(name)
        if stage != b'0':
            raise ValueError('Resolve the Git index conflict before testing exports: ' + name)
        if (not name or path.is_absolute() or '..' in path.parts or
                '\\' in name or ':' in name or name in seen):
            raise ValueError('Unsafe or duplicate indexed path: ' + name)
        seen.add(name)
        if mode not in (b'100644', b'100755'):
            raise ValueError('Only regular tracked files can be copied: ' + name)
        if rebuilt_archive(name):
            continue
        original, destination = source / name, target / name
        resolved = original.resolve(strict=True)
        if not resolved.is_relative_to(source):
            raise ValueError('Tracked source escapes its checkout: ' + name)
        if not stat.S_ISREG(original.lstat().st_mode):
            raise ValueError('Tracked source is not a regular file: ' + name)
        if not destination.resolve().is_relative_to(target):
            raise ValueError('Tracked destination escapes the isolated checkout: ' + name)
        if destination.exists() or destination.is_symlink():
            raise ValueError('Tracked destination must not already exist: ' + name)
        selected.append((original, destination))
    if not selected:
        raise ValueError('The Git index contains no files to test.')
    for original, destination in selected:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
    return len(selected)


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
    for name in REBUILT_COLLECTION_ARCHIVES:
        (root / 'downloads' / name).unlink(missing_ok=True)
    for archive in (root / 'downloads/experiments').glob('*.zip'):
        assert archive.resolve().is_relative_to(root.resolve())
        archive.unlink()


def main():
    with tempfile.TemporaryDirectory(prefix='liberpedia-export-test-', dir=ROOT.parent) as folder:
        target = Path(folder).resolve()
        assert target.is_relative_to(ROOT.parent.resolve()) and target != ROOT.resolve()
        # No hard links: rebuilding this copy must not overwrite checkout files.
        copy_tracked_checkout(ROOT, target)
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
