"""Frozen, bounded GP29 key-schedule tests for three distinct proposals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX = {r: i for i, r in enumerate(ALPHABET)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shortest_cycle(values: tuple[int, ...]) -> tuple[int, ...]:
    for size in range(1, len(values) + 1):
        if len(values) % size == 0 and values == values[:size] * (len(values) // size):
            return values[:size]
    raise AssertionError('finite cycle must have a period')


def expanded_cycle(key: tuple[int, ...], variant: str) -> tuple[int, ...]:
    k = len(key)
    if variant == 'rotate-left':
        whole = tuple(v for q in range(k) for v in key[q:] + key[:q])
    elif variant == 'rotate-right':
        whole = tuple(v for q in range(k) for v in key[-q:] + key[:-q])
    elif variant == 'fold-repeat-endpoints':
        whole = key + key[::-1]
    elif variant == 'fold-skip-endpoints':
        whole = key + key[-2:0:-1]
    else:
        raise ValueError(variant)
    return shortest_cycle(whole)


def mixed_alphabet(key: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(dict.fromkeys(key + tuple(range(29))))


def configs(kind: str, keys: list[tuple[str, tuple[int, ...]]]):
    for key_id, key in keys:
        if kind == 'rotating-folded-key-openings':
            for variant in ('rotate-left', 'rotate-right', 'fold-repeat-endpoints', 'fold-skip-endpoints'):
                cycle = expanded_cycle(key, variant)
                for phase in range(len(cycle)):
                    yield variant, key_id, phase, 0, key, cycle, None
        elif kind == 'mixed-alphabet-key-openings':
            mixed = mixed_alphabet(key)
            for phase in range(len(key)):
                yield 'keyword-mixed-GP29', key_id, phase, 0, key, None, mixed
        elif kind == 'grouped-key-advance-openings':
            for group in range(2, 6):
                for phase in range(len(key)):
                    for offset in range(group):
                        yield f'group-{group}', key_id, phase, offset, key, None, None
        else:
            raise ValueError(kind)


def decode_head(cipher: tuple[int, ...], item) -> tuple[int, ...]:
    variant, _, phase, offset, key, cycle, mixed = item
    if mixed is not None:
        inverse = {symbol: i for i, symbol in enumerate(mixed)}
        return tuple(mixed[(inverse[c] - inverse[key[(j + phase) % len(key)]]) % 29]
                     for j, c in enumerate(cipher))
    if cycle is not None:
        return tuple((c - cycle[(j + phase) % len(cycle)]) % 29 for j, c in enumerate(cipher))
    group = int(variant.split('-')[1])
    return tuple((c - key[(phase + (j + offset) // group) % len(key)]) % 29
                 for j, c in enumerate(cipher))


def encode_head(plain: tuple[int, ...], item) -> tuple[int, ...]:
    variant, _, phase, offset, key, cycle, mixed = item
    if mixed is not None:
        inverse = {symbol: i for i, symbol in enumerate(mixed)}
        return tuple(mixed[(inverse[p] + inverse[key[(j + phase) % len(key)]]) % 29]
                     for j, p in enumerate(plain))
    if cycle is not None:
        return tuple((p + cycle[(j + phase) % len(cycle)]) % 29 for j, p in enumerate(plain))
    group = int(variant.split('-')[1])
    return tuple((p + key[(phase + (j + offset) // group) % len(key)]) % 29
                 for j, p in enumerate(plain))


def load_inputs():
    manifest_path = HERE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    kp = ROOT / manifest['source_keys']
    op = ROOT / manifest['opening_vectors']
    assert digest(kp) == manifest['source_keys_sha256']
    assert digest(op) == manifest['opening_vectors_sha256']
    keys = [(row['id'], tuple(INDEX[c] for c in row['runes']))
            for row in json.loads(kp.read_text(encoding='utf-8'))['keys']]
    openings = [(row['id'], tuple(row['indices']))
                for row in json.loads(op.read_text(encoding='utf-8'))['openings']]
    assert len(keys) == 43 and len(openings) == 9
    assert all(len(value) == 12 for _, value in openings)
    pages = []
    sources = []
    for number in range(56):
        path = ROOT / f'text/lp2-{number:02d}.txt'
        runes = tuple(INDEX[c] for c in path.read_text(encoding='utf-8') if c in INDEX)
        sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
                        'runes': len(runes)})
        if runes:
            assert len(runes) >= 12
            pages.append((f'lp2-{number:02d}', runes[:12]))
    assert len(pages) == 55
    return manifest, keys, openings, pages, sources


def run(kind: str) -> dict:
    manifest, keys, openings, pages, sources = load_inputs()
    assert kind in manifest['records']
    details = {}
    case_hash = hashlib.sha256()
    best = 0
    best_examples = []
    all_clock_heads = set()
    total_configs = 0
    total_exact = 0
    comparison_count = 0
    plain = tuple(INDEX[c] for c in 'ᛗᚩᚢᚾᛏᚪᛁᚾᛗᚩᚢᚾᛏᚪᛁᚾᛗᚩᚢᚾᛏᚪᛁᚾ')
    planted_by_variant = {}
    for item in configs(kind, keys):
        variant, key_id, phase, offset, key, cycle, mixed = item
        row = details.setdefault(variant, {'configurations': 0, 'page_cases': 0,
                                           'comparisons': 0, 'exact_matches': 0,
                                           'max_prefix': 0, 'unique_12_step_clocks': 0})
        row['configurations'] += 1
        total_configs += 1
        clock = decode_head(tuple(range(12)), item)
        all_clock_heads.add((variant, clock))
        if variant not in planted_by_variant:
            # A 24-rune planting exercises transitions past every short key/group.
            planted = encode_head(plain, item)
            assert decode_head(planted, item) == plain
            planted_by_variant[variant] = {'key': key_id, 'phase': phase, 'group_offset': offset,
                                           'recovered_runes': len(plain)}
        for page, cipher in pages:
            out = decode_head(cipher, item)
            case_hash.update(f'{variant}\t{key_id}\t{phase}\t{offset}\t{page}\t{",".join(map(str, out))}\n'.encode())
            row['page_cases'] += 1
            row['comparisons'] += len(openings)
            comparison_count += len(openings)
            for opening_id, target in openings:
                prefix = 0
                while prefix < 12 and out[prefix] == target[prefix]:
                    prefix += 1
                if prefix == 12:
                    row['exact_matches'] += 1
                    total_exact += 1
                if prefix > row['max_prefix']:
                    row['max_prefix'] = prefix
                if prefix > best:
                    best = prefix
                    best_examples = []
                if prefix == best and len(best_examples) < 5:
                    best_examples.append({'variant': variant, 'key': key_id,
                                          'phase': phase, 'group_offset': offset,
                                          'page': page, 'opening': opening_id})
    # Count clock equivalence within each named variant, not across distinct operations.
    for variant in details:
        details[variant]['unique_12_step_clocks'] = sum(v == variant for v, _ in all_clock_heads)
    assert total_configs == sum(v['configurations'] for v in details.values())
    assert comparison_count == total_configs * len(pages) * len(openings)
    return {'schema': 'liberpedia-classical-key-schedules-results-v1',
            'kind': kind, 'manifest_sha256': digest(HERE / 'manifest.json'),
            'key_plan_sha256': manifest['source_keys_sha256'],
            'opening_plan_sha256': manifest['opening_vectors_sha256'],
            'sources': sources, 'key_count': len(keys), 'page_count': len(pages),
            'opening_count': len(openings), 'configuration_count': total_configs,
            'page_cases': total_configs * len(pages), 'comparison_count': comparison_count,
            'exact_matches': total_exact, 'max_prefix': best,
            'max_prefix_examples': best_examples, 'variants': details,
            'planted_controls': planted_by_variant, 'case_digest_sha256': case_hash.hexdigest()}
