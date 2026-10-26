"""Retain exact published authored-source record bytes; never rewrite a record.

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
HEX = re.compile(r'[a-f0-9]{64}')


def fixed_recipe(recipe):
    """Recognize the maintained fixed declaration, without running its program.

    Retention is not execution or admission. The ordinary publication validator
    still checks official inputs and synthetic results. Here we require its
    closed structure and compiler, rather than mistaking arbitrary metadata
    without a kind field for a fixed follow-up.
    """
    from browser_followups import compile_card, digest, runner
    required = {'id', 'title', 'question', 'scope_change', 'limitation', 'card', 'inputs', 'control'}
    if not isinstance(recipe, dict) or set(recipe) not in (required, required | {'motivation'}):
        return False
    try:
        if not isinstance(recipe['id'], str) or len(recipe['id']) > 100 or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', recipe['id']):
            return False
        for name in ('title', 'question', 'scope_change', 'limitation'):
            value = recipe[name]
            if not isinstance(value, str) or not value.strip() or len(value) > (300 if name == 'title' else 1200):
                return False
        if 'motivation' in recipe:
            value = recipe['motivation']
            if not isinstance(value, str) or value != value.strip() or not 1 <= len(value) <= 500 or re.search(r'[<>\[\]`*\\\x00-\x1f\x7f-\x9f\u2028\u2029\ud800-\udfff]', value):
                return False
        plan = compile_card(recipe['card'])
        pins, control = recipe['inputs'], recipe['control']
        if not isinstance(pins, dict) or set(pins) != {'version', 'alphabet_sha256', 'pages'} or pins['version'] != plan['inputVersion'] or not isinstance(pins['alphabet_sha256'], str) or not HEX.fullmatch(pins['alphabet_sha256']) or not isinstance(pins['pages'], list) or len(pins['pages']) != len(plan['pages']):
            return False
        for pin, identifier in zip(pins['pages'], plan['pages']):
            if not isinstance(pin, dict) or set(pin) != {'id', 'text_sha256'} or pin['id'] != identifier or not isinstance(pin['text_sha256'], str) or not HEX.fullmatch(pin['text_sha256']):
                return False
        if not isinstance(control, dict) or set(control) != {'label', 'task', 'expected_result_sha256'} or not isinstance(control['label'], str) or not control['label'].strip() or len(control['label']) > 300 or 'synthetic' not in control['label'].lower() or not isinstance(control['expected_result_sha256'], str) or not HEX.fullmatch(control['expected_result_sha256']):
            return False
        task = control['task']
        runner.validate(task)
        if 'synthetic' not in task['title'].lower() or task['steps'] != plan['steps'] or digest(task['alphabet']) != pins['alphabet_sha256']:
            return False
        if plan['criterion']['kind'] in ('measurement', 'language-score'):
            if task['criterion']['kind'] != 'exact-prefix':
                return False
            runes = {row['rune'] for row in task['alphabet']}
            if not all(sum(ch in runes for ch in page['text']) == len(task['criterion']['values']) for page in task['pages']):
                return False
        elif task['criterion'] != plan['criterion']:
            return False
        return True
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def authored_recipe(recipe):
    return isinstance(recipe, dict) and (recipe.get('kind') == 'finite-settings' or fixed_recipe(recipe))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    return json.loads(data.decode('utf-8-sig'))


def record_identity(data):
    if not data or len(data) > MAX_SOURCE:
        raise ValueError('Source record exceeds its byte bound')
    record = parse(data)
    if not isinstance(record, dict) or not isinstance(record.get('id'), str) or len(record['id']) > 100 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', record['id']) or record.get('status') != 'published':
        raise ValueError('A retained source must be a published record')
    recipes = record.get('browser_followups')
    if not isinstance(recipes, list) or len(recipes) > 8 or not any(authored_recipe(recipe) for recipe in recipes):
        raise ValueError('A retained source must contain a maintained authored follow-up')
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
        if record.get('status') != 'published' or not any(authored_recipe(recipe) for recipe in record.get('browser_followups', [])):
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
    print(f"PASS {len(value['entries'])} exact authored-source revisions retained")
