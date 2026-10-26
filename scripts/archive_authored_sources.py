"""Retain exact published finite-source record bytes; never rewrite a record.

--write adds immutable objects and extends the manifest. The default checks all
retained objects and current coverage. CI can pass --baseline-manifest from its
explicit base revision to reject a coordinated manifest-and-object deletion.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/authored-source-archive.json'
PREFIX = 'published-sources/records/'
MAX_SOURCE = 2 * 1024 * 1024
MAX_BYTES = 32 * 1024 * 1024
MAX_ENTRIES = 128


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    return json.loads(data.decode('utf-8'))


def record_identity(data):
    if not data or len(data) > MAX_SOURCE:
        raise ValueError('Source record exceeds its byte bound')
    record = parse(data)
    if not isinstance(record, dict) or not isinstance(record.get('id'), str) or len(record['id']) > 100 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', record['id']) or record.get('status') != 'published':
        raise ValueError('A retained source must be a published record')
    recipes = record.get('browser_followups')
    if not isinstance(recipes, list) or len(recipes) > 8 or not any(isinstance(recipe, dict) and recipe.get('kind') == 'finite-settings' for recipe in recipes):
        raise ValueError('A retained source must contain a finite follow-up')
    return record['id']


def entry(data):
    digest = sha(data)
    return {'recordId': record_identity(data), 'sha256': digest, 'bytes': len(data), 'path': PREFIX + digest + '.json'}


def manifest_entries(value):
    if not isinstance(value, dict) or set(value) != {'schema', 'entries'} or value['schema'] != 'liberpedia-authored-source-archive-v1' or not isinstance(value['entries'], list) or len(value['entries']) > MAX_ENTRIES:
        raise ValueError('Invalid source archive manifest')
    entries = {}
    for item in value['entries']:
        if not isinstance(item, dict) or set(item) != {'recordId', 'sha256', 'bytes', 'path'} or not isinstance(item['sha256'], str) or len(item['sha256']) != 64 or any(c not in '0123456789abcdef' for c in item['sha256']) or item['path'] != PREFIX + item['sha256'] + '.json' or not isinstance(item['bytes'], int) or isinstance(item['bytes'], bool) or not 0 < item['bytes'] <= MAX_SOURCE or item['sha256'] in entries:
            raise ValueError('Invalid or repeated source archive entry')
        entries[item['sha256']] = item
    if sum(item['bytes'] for item in entries.values()) > MAX_BYTES:
        raise ValueError('Source archive exceeds its byte budget; nothing may be evicted')
    return entries


def prepare(root=ROOT, baseline=None):
    root = Path(root)
    path = root / MANIFEST
    old = manifest_entries(parse(path.read_bytes())) if path.exists() else {}
    for item in old.values():
        target = root / item['path']
        if not target.exists() or entry(target.read_bytes()) != item:
            raise ValueError('Retained source bytes are missing or changed: ' + item['path'])
    if baseline is not None:
        previous = manifest_entries(baseline)
        if any(old.get(key) != item for key, item in previous.items()):
            raise ValueError('Retained source entries may not be removed or changed')
    files = {}
    entries = dict(old)
    for source in sorted((root / 'experiments/records').glob('*/record.json')):
        data = source.read_bytes()
        record = parse(data)
        if record.get('status') != 'published' or not any(isinstance(recipe, dict) and recipe.get('kind') == 'finite-settings' for recipe in record.get('browser_followups', [])):
            continue
        item = entry(data)
        if item['recordId'] != source.parent.name:
            raise ValueError('The current record ID differs from its directory')
        target = root / item['path']
        if target.exists() and target.read_bytes() != data:
            raise ValueError('An immutable content-addressed source changed')
        files[item['path']] = data
        entries[item['sha256']] = item
    value = {'schema': 'liberpedia-authored-source-archive-v1', 'entries': sorted(entries.values(), key=lambda item: (item['recordId'], item['sha256']))}
    manifest_entries(value)
    retained = {item['path'] for item in value['entries']}
    for target in (root / PREFIX).glob('*.json'):
        if target.relative_to(root).as_posix() not in retained:
            raise ValueError('An archived source is missing from the retention manifest')
    files[MANIFEST] = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    return files


def build(root=ROOT, write=False, baseline=None):
    root = Path(root)
    files = prepare(root, baseline)
    for name, data in files.items():
        path = root / name
        if write:
            if name != MANIFEST and path.exists():
                if path.read_bytes() != data:
                    raise ValueError('An immutable source may not be overwritten')
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif not path.exists() or path.read_bytes() != data:
            raise ValueError('Source archive is stale: ' + name)
    return parse(files[MANIFEST])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--baseline-manifest', type=Path)
    args = parser.parse_args()
    baseline = parse(args.baseline_manifest.read_bytes()) if args.baseline_manifest else None
    value = build(write=args.write, baseline=baseline)
    print(f"PASS {len(value['entries'])} exact finite-source revisions retained")
