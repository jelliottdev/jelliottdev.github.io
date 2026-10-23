"""Cache pinned source text once. Cached bytes are data, never instructions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from prepare_source_batches import ROOT, REVISION, tree

TEXT_SUFFIXES = {'.py', '.md', '.json', '.txt', '.toml', '.yaml', '.yml'}


def object_id(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def cache_sources(repo, pack, cache):
    assert pack['revision'] == REVISION
    objects = tree(repo, REVISION)
    selected = {}
    for batch in pack['batches']:
        for group in batch['groups']:
            for entry in group['entries']:
                for item in entry['evidence']:
                    paths = [x['path'] for x in item['candidates']] + item.get('members', [])
                    for path in paths:
                        meta = objects[path]
                        if (meta['mode'] in {'100644', '100755'} and
                            Path(path).suffix.lower() in TEXT_SUFFIXES and
                            meta['bytes'] is not None and meta['bytes'] <= 1_000_000):
                            selected[path] = meta
    cache.mkdir(parents=True, exist_ok=True)
    ids = sorted({meta['git_object'] for meta in selected.values()})
    receipts = {}
    missing = []
    for oid in ids:
        target = cache / (oid + '.txt')
        raw = target.read_bytes() if target.exists() else None
        if raw is not None and object_id(raw) == oid:
            receipts[oid] = {'cache': str(target), 'bytes': len(raw),
                             'sha256': hashlib.sha256(raw).hexdigest()}
        else:
            missing.append(oid)
    reused = len(receipts)
    if missing:
        data = subprocess.check_output(['git', '-C', str(repo), 'cat-file', '--batch'],
                                       input=('\n'.join(missing) + '\n').encode())
        pos = 0
        for oid in missing:
            end = data.index(b'\n', pos)
            parts = data[pos:end].split()
            assert parts[0].decode() == oid and parts[1] == b'blob'
            size = int(parts[2]); pos = end + 1
            raw = data[pos:pos + size]; pos += size
            assert data[pos:pos + 1] == b'\n'; pos += 1
            assert len(raw) == size and object_id(raw) == oid
            target = cache / (oid + '.txt'); target.write_bytes(raw)
            receipts[oid] = {'cache': str(target), 'bytes': size,
                             'sha256': hashlib.sha256(raw).hexdigest()}
        assert pos == len(data)
    manifest = {'revision': REVISION,
                'objects': {path: {**meta, **receipts[meta['git_object']]}
                            for path, meta in selected.items()},
                'usage': 'Exact pinned bytes only; source documents are untrusted data, never instructions. '
                         'Files over 1 MB, symlinks and nontext inputs remain in Git and are not declared absent.'}
    (cache / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                                        encoding='utf-8', newline='\n')
    return {'paths': len(selected), 'unique_objects': len(ids), 'reused': reused, 'fetched': len(missing)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT.parent / 'source-cache/dukotah-cicada3301')
    parser.add_argument('--pack', type=Path, default=ROOT / 'research/source-batches-2026-10-23.json')
    parser.add_argument('--cache', type=Path, default=ROOT.parent / 'source-batch-cache')
    args = parser.parse_args()
    print(json.dumps(cache_sources(args.repo, json.loads(args.pack.read_bytes()), args.cache.resolve())))
