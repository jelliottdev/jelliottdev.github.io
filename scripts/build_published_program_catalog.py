"""Combine maintained program indexes without rewriting historical providers."""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'liberpedia-published-program-source-index-v1'
PROVIDERS = ('data/published-program-source-index.json', 'data/published-panel-program-source-index.json')
MAX_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 1024


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def merge(providers):
    entries, identities, paths = [], set(), set()
    for provider in providers:
        if not isinstance(provider, dict) or set(provider) != {'schema', 'entries'} or provider['schema'] != SCHEMA or not isinstance(provider['entries'], list):
            raise ValueError('Invalid program index provider')
        for entry in provider['entries']:
            if not isinstance(entry, dict) or any(not isinstance(entry.get(k), str) for k in ('recordId', 'revision', 'caseId', 'path')):
                raise ValueError('Invalid program pointer identity')
            key = (entry['recordId'], entry['revision'], entry['caseId'])
            if key in identities or entry['path'] in paths:
                raise ValueError('Program providers overlap; existing evidence cannot be replaced')
            identities.add(key)
            paths.add(entry['path'])
            entries.append(copy.deepcopy(entry))
            if len(entries) > MAX_ENTRIES:
                raise ValueError('Program catalog exceeds its entry bound')
    value = {'schema': SCHEMA, 'entries': entries}
    if len(stable(value).encode('utf-8')) > MAX_BYTES:
        raise ValueError('Program catalog exceeds its byte bound')
    return value


def prepare(root=ROOT):
    root = Path(root)
    value = merge([json.loads((root / name).read_bytes()) for name in PROVIDERS])
    content = stable(value)
    return {'data/published-program-source-catalog.json': content + '\n',
            'published-program-source-catalog-data.js': "/* Generated maintained program catalog; providers remain immutable. */\n(function(root){'use strict';const data=" + content + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedProgramSourceCatalogData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"}


def build(root=ROOT, write=False):
    root = Path(root)
    files = prepare(root)
    for name, text in files.items():
        path, data = root / name, text.encode('utf-8')
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif not path.exists() or path.read_bytes() != data:
            raise ValueError('Program catalog is stale: ' + name)
    return json.loads(files['data/published-program-source-catalog.json'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    value = build(write=args.write)
    print('PASS ' + str(len(value['entries'])) + ' maintained program pointers; provider bytes unchanged')
