"""Finite GP29 one-rune replacement test against fixed page openings."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX = {r: i for i, r in enumerate(ALPHABET)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for row in plan['inputs']:
        assert sha(ROOT / row['path']) == row['sha256'], row['path']
    keys = [(row['id'], row['runes']) for row in json.loads(
        (ROOT / 'experiments/records/public-wordlist-vigenere/plan.json').read_text(encoding='utf-8'))['keys']]
    openings = [(row['id'], tuple(row['indices'])) for row in json.loads(
        (ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))['openings']]
    pages = []
    for number in range(56):
        name = f'lp2-{number:02d}'
        runes = tuple(INDEX[c] for c in (ROOT / f'text/{name}.txt').read_text(encoding='utf-8') if c in INDEX)
        if runes:
            pages.append((name, runes[:12]))
    assert len(keys) == 43 and len(openings) == 9 and len(pages) == 55
    assert all(len(v) == 12 for _, v in openings) and all(len(v) == 12 for _, v in pages)
    return keys, openings, pages


def variants(keys):
    provenance = defaultdict(set)
    names = Counter()
    for source_id, key in keys:
        for position, old in enumerate(key):
            for replacement in ALPHABET:
                if replacement == old:
                    continue
                changed = key[:position] + replacement + key[position + 1:]
                provenance[changed].add(('position', source_id))
                names['position'] += 1
        for old in set(key):
            for replacement in ALPHABET:
                if replacement == old:
                    continue
                changed = key.replace(old, replacement)
                provenance[changed].add(('rune-type', source_id))
                names['rune-type'] += 1
    assert names == {'position': 8652, 'rune-type': 7056}
    assert len(provenance) == 9856
    return provenance, names


def required_clocks(openings, pages):
    lookup = defaultdict(list)
    for page, cipher in pages:
        for opening, plain in openings:
            # Subtractive decoding P=C-K requires K=C-P; additive P=C+K requires K=P-C.
            lookup[tuple((c - p) % 29 for c, p in zip(cipher, plain))].append((page, opening, 'subtract'))
            lookup[tuple((p - c) % 29 for c, p in zip(cipher, plain))].append((page, opening, 'add'))
    return lookup


def run():
    keys, openings, pages = inputs()
    changes, names = variants(keys)
    lookup = required_clocks(openings, pages)
    hits = []
    cycles = Counter()
    mode_cycles = Counter()
    h = hashlib.sha256()
    distinct_clocks = set()
    for key in sorted(changes):
        vector = tuple(INDEX[r] for r in key)
        modes = sorted({mode for mode, _ in changes[key]})
        for phase in range(len(vector)):
            clock = tuple(vector[(phase + j) % len(vector)] for j in range(12))
            h.update(bytes(clock))
            distinct_clocks.add(clock)
            cycles['all'] += 1
            for mode in modes:
                mode_cycles[mode] += 1
            for page, opening, direction in lookup.get(clock, ()):
                hits.append({'key': key, 'phase': phase, 'page': page, 'opening': opening, 'direction': direction,
                             'modes': modes, 'source_keys': sorted({sid for _, sid in changes[key]})})
    assert cycles['all'] == 83328
    return {'schema': 'liberpedia-mutated-dictionary-key-openings-v1',
            'plan_sha256': sha(HERE / 'plan.json'),
            'source_key_count': len(keys), 'named_mutations': dict(sorted(names.items())),
            'unique_mutated_keys': len(changes), 'phase_settings': cycles['all'],
            'unique_12_rune_clocks': len(distinct_clocks),
            'mode_phase_settings': dict(sorted(mode_cycles.items())),
            'page_count': len(pages), 'opening_count': len(openings),
            'nominal_comparisons': cycles['all'] * len(pages) * len(openings) * 2,
            'distinct_required_clocks': len(lookup), 'clock_stream_sha256': h.hexdigest(),
            'exact_matches': hits, 'match_count': len(hits)}


def controls():
    keys, openings, _ = inputs()
    changes, _ = variants(keys)
    only_position = next(k for k, v in sorted(changes.items()) if {m for m, _ in v} == {'position'})
    only_rune_type = next(k for k, v in sorted(changes.items()) if {m for m, _ in v} == {'rune-type'})
    both = next(k for k, v in sorted(changes.items()) if {m for m, _ in v} == {'position', 'rune-type'} and len(k) > 5)
    for key, phase in ((only_position, 2), (only_rune_type, 4), (both, 3)):
        vector = tuple(INDEX[c] for c in key)
        plain = openings[0][1]
        actual = tuple(vector[(j + phase) % len(vector)] for j in range(12))
        for direction in ('subtract', 'add'):
            cipher = tuple((p + k if direction == 'subtract' else p - k) % 29
                           for p, k in zip(plain, actual))
            required = tuple((c - p if direction == 'subtract' else p - c) % 29
                             for c, p in zip(cipher, plain))
            assert required == actual
            assert tuple((c - k if direction == 'subtract' else c + k) % 29
                         for c, k in zip(cipher, actual)) == plain
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    assert controls()
    result = run()
    path = HERE / 'results.json'
    if args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print({k: result[k] for k in ('unique_mutated_keys', 'phase_settings', 'match_count')})
