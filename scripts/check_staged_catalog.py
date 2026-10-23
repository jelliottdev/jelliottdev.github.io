"""Check catalog hashes against Git's index, including line-ending normalization."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=root, **kwargs)


def verify(root=ROOT, all_files=False):
    catalog = json.loads(git(root, 'show', ':data/catalog.json'))
    changed = set(git(root, 'diff', '--cached', '--name-only', '-z').decode().split('\0'))
    entries = [entry for entry in catalog['files']
               if all_files or entry['path'] in changed]
    if not entries:
        return 0
    names = [entry['path'] for entry in entries]
    if any('\n' in name or '\r' in name for name in names):
        raise ValueError('Catalog paths must not contain line breaks')
    # One Git process reads every indexed blob; repeated `git show` is costly on Windows.
    request = ''.join(':' + name + '\n' for name in names).encode('utf-8')
    data = git(root, 'cat-file', '--batch', input=request)
    cursor = 0
    for entry in entries:
        path = entry['path']
        end = data.index(b'\n', cursor)
        header = data[cursor:end].split()
        assert len(header) == 3 and header[1] == b'blob', f'Missing staged file: {path}'
        size = int(header[2])
        cursor = end + 1
        content = data[cursor:cursor + size]
        cursor += size + 1
        assert size == entry['bytes'], f'Staged size differs: {path}'
        assert hashlib.sha256(content).hexdigest() == entry['sha256'], f'Staged hash differs: {path}'
    return len(entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Check the entire indexed catalog, not only changed paths')
    args = parser.parse_args()
    count = verify(all_files=args.all)
    print(f'PASS: {count} catalogued files match the staged Git bytes')
