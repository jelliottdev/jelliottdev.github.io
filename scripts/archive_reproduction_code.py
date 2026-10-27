"""Retain explicitly pinned maintained implementation bytes, never science files.

Default/--check verifies coverage and every immutable object. --write only adds
exact current versions or reuses already retained versions; it never guesses a
historical version from Git or changes an authored reproduction pin.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'data/maintained-reproduction-code-policy.json'
MANIFEST = 'data/reproduction-code-archive.json'
PREFIX = 'published-sources/code/'
SCHEMA = 'liberpedia-reproduction-code-archive-v1'
MAX_SOURCE = 2 * 1024 * 1024
MAX_BYTES = 32 * 1024 * 1024
MAX_ENTRIES = 512



def sha(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Repeated JSON field')
        value[key] = item
    return value


def parse(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)


def contained(root, name):
    if (not isinstance(name, str) or len(name) > 500
            or not re.fullmatch(r'[A-Za-z0-9_./-]+', name)
            or any(part in ('', '.', '..') for part in name.split('/'))):
        raise ValueError('Unsafe maintained code path')
    target = (root / name).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Maintained code path escapes repository')
    return target


def bounded_read(root, name, limit=MAX_SOURCE):
    target = contained(root, name)
    if target.stat().st_size > limit:
        raise ValueError('Maintained code file exceeds byte bound')
    data = target.read_bytes()
    if not data or len(data) > limit:
        raise ValueError('Maintained code file exceeds byte bound')
    return data


def maintained_path(value):
    """Scope guard only; the checked-in JSON selects actual maintained modules."""
    return (isinstance(value, str) and len(value) <= 300
            and re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\.(?:js|mjs)', value) is not None
            and all(part not in ('', '.', '..') for part in value.split('/'))
            and ('/' not in value or value.startswith(('scripts/', 'services/'))))


def policy(root=ROOT):
    value = parse(bounded_read(Path(root).resolve(), POLICY))
    if (not isinstance(value, dict) or set(value) != {'schema', 'paths'}
            or value['schema'] != 'liberpedia-maintained-reproduction-code-policy-v1'
            or not isinstance(value['paths'], list)
            or not 1 <= len(value['paths']) <= 32
            or any(not maintained_path(path) for path in value['paths'])
            or len(set(value['paths'])) != len(value['paths'])):
        raise ValueError('The maintained code policy must name unique bounded implementation paths')
    return tuple(value['paths'])


def entry(source_path, data):
    if not maintained_path(source_path) or not isinstance(data, bytes) or not 0 < len(data) <= MAX_SOURCE:
        raise ValueError('Invalid maintained code source')
    digest = sha(data)
    return {'sourcePath': source_path, 'sha256': digest, 'bytes': len(data),
            'path': PREFIX + digest + Path(source_path).suffix}


def manifest_entries(value):
    if (not isinstance(value, dict) or set(value) != {'schema', 'entries'}
            or value['schema'] != SCHEMA or not isinstance(value['entries'], list)
            or len(value['entries']) > MAX_ENTRIES):
        raise ValueError('Invalid maintained code archive manifest')
    entries = {}
    for item in value['entries']:
        if (not isinstance(item, dict) or set(item) != {'sourcePath', 'sha256', 'bytes', 'path'}
                or not maintained_path(item['sourcePath'])
                or not isinstance(item['sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', item['sha256'])
                or type(item['bytes']) is not int or not 0 < item['bytes'] <= MAX_SOURCE
                or item['path'] != PREFIX + item['sha256'] + Path(item['sourcePath']).suffix):
            raise ValueError('Invalid maintained code archive association')
        key = (item['sourcePath'], item['sha256'])
        if key in entries:
            raise ValueError('Repeated maintained code archive association')
        entries[key] = item
    objects = {}
    for item in entries.values():
        if item['path'] in objects and objects[item['path']] != item['bytes']:
            raise ValueError('Conflicting maintained code object size')
        objects[item['path']] = item['bytes']
    if sum(objects.values()) > MAX_BYTES:
        raise ValueError('Maintained code archive exceeds total byte budget; no eviction permitted')
    return entries


def read_entry(root, item):
    """Validate one exact sourcePath association and its raw retained bytes."""
    manifest_entries({'schema': SCHEMA, 'entries': [item]})
    data = bounded_read(Path(root).resolve(), item['path'])
    if entry(item['sourcePath'], data) != item:
        raise ValueError('Retained maintained code bytes changed')
    return data


def _pins(record, allowed):
    reproduction = record.get('reproduction', {})
    if not isinstance(reproduction, dict):
        raise ValueError('Invalid reproduction declaration')
    pins = reproduction.get('inputs', [])
    if not isinstance(pins, list):
        raise ValueError('Invalid reproduction input pins')
    selected = {}
    for pin in pins:
        if not isinstance(pin, dict):
            raise ValueError('Invalid reproduction input pin')
        path = pin.get('path')
        if isinstance(path, str) and path in allowed:
            if set(pin) != {'path', 'sha256'} or path in selected:
                raise ValueError('Repeated or malformed maintained code pin')
            selected[path] = pin['sha256']
    script = reproduction.get('script')
    if script in allowed:
        digest = reproduction.get('script_sha256')
        if script in selected and selected[script] != digest:
            raise ValueError('Conflicting maintained script pin')
        selected[script] = digest
    for path, digest in selected.items():
        if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise ValueError('Invalid maintained code SHA-256 pin: ' + path)
    return selected.items()


def prepare(root=ROOT, baseline=None):
    root = Path(root).resolve()
    allowed = policy(root)
    manifest_path = contained(root, MANIFEST)
    old = manifest_entries(parse(bounded_read(root, MANIFEST))) if manifest_path.exists() else {}
    for item in old.values():
        if item['sourcePath'] not in allowed:
            raise ValueError('Retained maintained code paths may not be removed from policy')
        read_entry(root, item)
    if baseline is not None:
        previous = manifest_entries(baseline)
        if any(item['sourcePath'] not in allowed or old.get(key) != item for key, item in previous.items()):
            raise ValueError('Retained maintained code associations may not be removed or changed')
    entries, files = dict(old), {}
    for source in sorted((root / 'experiments/records').glob('*/record.json')):
        name = source.relative_to(root).as_posix()
        record = parse(bounded_read(root, name))
        if not isinstance(record, dict):
            raise ValueError('Invalid canonical record')
        if record.get('status') != 'published':
            continue
        if record.get('id') != source.parent.name:
            raise ValueError('Canonical record ID differs from directory')
        for source_path, digest in _pins(record, allowed):
            key = (source_path, digest)
            if key in entries:
                continue
            try:
                data = bounded_read(root, source_path)
            except FileNotFoundError as error:
                raise ValueError('No exact retained maintained code version: ' + source_path) from error
            if sha(data) != digest:
                raise ValueError('No exact retained maintained code version: ' + source_path)
            item = entry(source_path, data)
            target = contained(root, item['path'])
            if target.exists() and bounded_read(root, item['path']) != data:
                raise ValueError('Immutable maintained code object changed')
            files[item['path']] = data
            entries[key] = item
    value = {'schema': SCHEMA, 'entries': sorted(entries.values(), key=lambda item: (item['sourcePath'], item['sha256']))}
    manifest_entries(value)
    retained = {item['path'] for item in value['entries']}
    archive = contained(root, PREFIX.rstrip('/'))
    if archive.exists():
        for target in archive.iterdir():
            if not target.is_file() or target.relative_to(root).as_posix() not in retained:
                raise ValueError('Maintained code object is missing from retention manifest')
    files[MANIFEST] = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    return files


def build(root=ROOT, write=False, baseline=None):
    root = Path(root).resolve()
    files = prepare(root, baseline)
    # Validate every existing destination before changing any object or index.
    for name, data in files.items():
        path = contained(root, name)
        if name != MANIFEST and path.exists() and path.read_bytes() != data:
            raise ValueError('Immutable maintained code object may not be overwritten')
    for name, data in files.items():
        path = contained(root, name)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path = contained(root, name)
            if name == MANIFEST:
                path.write_bytes(data)
            elif not path.exists():
                with path.open('xb') as stream:
                    stream.write(data)
        elif not path.exists() or path.read_bytes() != data:
            raise ValueError('Maintained code archive is stale: ' + name)
    return parse(files[MANIFEST])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--baseline-manifest', type=Path)
    args = parser.parse_args()
    baseline = parse(args.baseline_manifest.read_bytes()) if args.baseline_manifest else None
    value = build(write=args.write, baseline=baseline)
    print(('WROTE' if args.write else 'CHECKED') + ' ' + str(len(value['entries'])) + ' maintained code associations')
