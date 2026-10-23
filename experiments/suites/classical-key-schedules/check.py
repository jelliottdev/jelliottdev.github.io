"""Independent page-record and closed-form check of the key-schedule census.

This implementation does not import the producer. It reads page JSON rather
than the producer's text files and reconstructs clocks directly by position.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ABC = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
TO_INDEX = {symbol: pos for pos, symbol in enumerate(ABC)}
IDS = ('rotating-folded-key-openings', 'mixed-alphabet-key-openings',
       'grouped-key-advance-openings')


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def period_of(key, operation):
    n = len(key)
    nominal = n * n if operation.startswith('rotate') else 2 * n - (2 if operation == 'fold-skip-endpoints' else 0)
    generated = tuple(key_symbol(key, operation, 0, 0, j, None) for j in range(nominal))
    for width in range(1, nominal + 1):
        if nominal % width == 0 and all(generated[j] == generated[j % width] for j in range(nominal)):
            return width
    raise AssertionError('period calculation')


def key_symbol(key, operation, phase, offset, j, inverse_mixed):
    n = len(key)
    if operation == 'rotate-left':
        cycle, slot = divmod(j + phase, n)
        return key[(slot + cycle) % n]
    if operation == 'rotate-right':
        cycle, slot = divmod(j + phase, n)
        return key[(slot - cycle) % n]
    if operation == 'fold-repeat-endpoints':
        slot = (j + phase) % (2 * n)
        return key[slot if slot < n else 2 * n - 1 - slot]
    if operation == 'fold-skip-endpoints':
        slot = (j + phase) % (2 * n - 2)
        return key[slot if slot < n else 2 * n - 2 - slot]
    if operation == 'keyword-mixed-GP29':
        return inverse_mixed[key[(j + phase) % n]]
    group = int(operation.rsplit('-', 1)[1])
    return key[(phase + ((j + offset) // group)) % n]


def transform(cipher, key, operation, phase, offset, mixed):
    if mixed is None:
        return tuple((c - key_symbol(key, operation, phase, offset, j, None)) % 29
                     for j, c in enumerate(cipher))
    inv = {symbol: pos for pos, symbol in enumerate(mixed)}
    return tuple(mixed[(inv[c] - key_symbol(key, operation, phase, offset, j, inv)) % 29]
                 for j, c in enumerate(cipher))


def plant(plain, key, operation, phase, offset, mixed):
    if mixed is None:
        return tuple((p + key_symbol(key, operation, phase, offset, j, None)) % 29
                     for j, p in enumerate(plain))
    inv = {symbol: pos for pos, symbol in enumerate(mixed)}
    return tuple(mixed[(inv[p] + key_symbol(key, operation, phase, offset, j, inv)) % 29]
                 for j, p in enumerate(plain))


def configurations(record_id, keys):
    for key_id, key in keys:
        if record_id == IDS[0]:
            for operation in ('rotate-left', 'rotate-right', 'fold-repeat-endpoints', 'fold-skip-endpoints'):
                for phase in range(period_of(key, operation)):
                    yield operation, key_id, key, phase, 0, None
        elif record_id == IDS[1]:
            mixed = []
            for symbol in (*key, *range(29)):
                if symbol not in mixed:
                    mixed.append(symbol)
            assert len(mixed) == 29
            for phase in range(len(key)):
                yield 'keyword-mixed-GP29', key_id, key, phase, 0, tuple(mixed)
        elif record_id == IDS[2]:
            for size in (2, 3, 4, 5):
                for phase in range(len(key)):
                    for offset in range(size):
                        yield f'group-{size}', key_id, key, phase, offset, None
        else:
            raise AssertionError(record_id)


def verify(record_id):
    output_path = ROOT / 'experiments/records' / record_id / 'results.json'
    saved = json.loads(output_path.read_text(encoding='utf-8'))
    manifest_path = HERE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    key_path = ROOT / manifest['source_keys']
    opening_path = ROOT / manifest['opening_vectors']
    assert saved['manifest_sha256'] == file_hash(manifest_path)
    assert saved['key_plan_sha256'] == file_hash(key_path)
    assert saved['opening_plan_sha256'] == file_hash(opening_path)
    key_rows = json.loads(key_path.read_text(encoding='utf-8'))['keys']
    keys = [(item['id'], tuple(TO_INDEX[c] for c in item['runes'])) for item in key_rows]
    openings = [(item['id'], tuple(item['indices']))
                for item in json.loads(opening_path.read_text(encoding='utf-8'))['openings']]
    assert len(keys) == 43 and len(openings) == 9
    pages = []
    for source in saved['sources']:
        text_path = ROOT / source['path']
        assert file_hash(text_path) == source['sha256']
        name = text_path.stem
        page = json.loads((ROOT / 'data/pages' / f'{name}.json').read_text(encoding='utf-8'))
        rune_symbols = [char for row in page['lines'] for char in row['raw'] if char in TO_INDEX]
        assert len(rune_symbols) == source['runes']
        if rune_symbols:
            pages.append((name, tuple(TO_INDEX[x] for x in rune_symbols[:12])))
    assert len(pages) == 55
    rows = {}
    seen_clocks = {}
    hasher = hashlib.sha256()
    total = 0
    exact = 0
    best = 0
    examples = []
    planted = {}
    sample = tuple(TO_INDEX[x] for x in 'ᛗᚩᚢᚾᛏᚪᛁᚾᛗᚩᚢᚾᛏᚪᛁᚾᛗᚩᚢᚾᛏᚪᛁᚾ')
    for operation, key_id, key, phase, offset, mixed in configurations(record_id, keys):
        row = rows.setdefault(operation, {'configurations': 0, 'page_cases': 0,
                                          'comparisons': 0, 'exact_matches': 0,
                                          'max_prefix': 0, 'unique_12_step_clocks': 0})
        row['configurations'] += 1
        total += 1
        seen_clocks.setdefault(operation, set()).add(transform(tuple(range(12)), key, operation, phase, offset, mixed))
        if operation not in planted:
            assert transform(plant(sample, key, operation, phase, offset, mixed), key,
                             operation, phase, offset, mixed) == sample
            planted[operation] = {'key': key_id, 'phase': phase, 'group_offset': offset,
                                  'recovered_runes': len(sample)}
        for page_name, cipher in pages:
            out = transform(cipher, key, operation, phase, offset, mixed)
            hasher.update(f'{operation}\t{key_id}\t{phase}\t{offset}\t{page_name}\t{",".join(str(x) for x in out)}\n'.encode())
            row['page_cases'] += 1
            row['comparisons'] += len(openings)
            for opening_id, target in openings:
                length = next((j for j, (a, b) in enumerate(zip(out, target)) if a != b), 12)
                if length == 12:
                    exact += 1
                    row['exact_matches'] += 1
                row['max_prefix'] = max(row['max_prefix'], length)
                if length > best:
                    best = length
                    examples = []
                if length == best and len(examples) < 5:
                    examples.append({'variant': operation, 'key': key_id, 'phase': phase,
                                     'group_offset': offset, 'page': page_name,
                                     'opening': opening_id})
    for operation, row in rows.items():
        row['unique_12_step_clocks'] = len(seen_clocks[operation])
    assert saved['kind'] == record_id
    assert saved['variants'] == rows
    assert saved['planted_controls'] == planted
    assert saved['configuration_count'] == total
    assert saved['page_cases'] == total * 55
    assert saved['comparison_count'] == total * 55 * 9
    assert saved['exact_matches'] == exact
    assert saved['max_prefix'] == best
    assert saved['max_prefix_examples'] == examples
    assert saved['case_digest_sha256'] == hasher.hexdigest()
    print('PASS', record_id, total, 'settings,', exact, 'exact matches')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record_ids', nargs='*', choices=IDS)
    args = parser.parse_args()
    for ident in args.record_ids or IDS:
        verify(ident)
