"""Independently recount openings using closed-form alphabet positions."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
index = {row['rune']: i for i, row in enumerate(alphabet)}
assert len(index) == 29 and index['ᚠ'] == 0
for name, expected in result['input_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def independent(cipher, keys, phases, start, sign, policy):
    # The number of earlier non-F symbols fixes the paused alphabet clock.
    active = [(start + (i if policy == 'key-only' else sum(c != 0 for c in cipher[:i]))) % 2
              for i in range(len(cipher))]
    output = []
    for i, (c, a) in enumerate(zip(cipher, active)):
        count = sum(cipher[j] != 0 and active[j] == a for j in range(i))
        offset = keys[a][(phases[a] + count) % len(keys[a])]
        output.append(((c if a == 0 else 28 - c) + sign * offset) % 29)
    return output


pages = []
for name in plan['pages']:
    runes = [index[c] for c in (ROOT / f'text/{name}.txt').read_text(encoding='utf-8') if c in index]
    if runes:
        pages.append((name, runes[:12]))
summary = {p: dict(settings=0, page_cases=0, comparisons=0, exact_matches=0, max_prefix=0)
           for p in ('key-only', 'both')}
census = hashlib.sha256()
for order in (0, 1):
    keys = [row['indices'] for row in plan['keys']][::1 if order == 0 else -1]
    for policy, sign, start in itertools.product(('key-only', 'both'), (-1, 1), (0, 1)):
        for a, b in itertools.product(range(len(keys[0])), range(len(keys[1]))):
            summary[policy]['settings'] += 1
            for page, cipher in pages:
                plain = independent(cipher, keys, (a, b), start, sign, policy)
                census.update(bytes(plain))
                row = summary[policy]
                row['page_cases'] += 1
                for crib in plan['openings']:
                    length = 0
                    for x, y in zip(plain, crib['indices']):
                        if x != y:
                            break
                        length += 1
                    row['comparisons'] += 1
                    row['exact_matches'] += length == 12
                    row['max_prefix'] = max(row['max_prefix'], length)
assert summary == result['by_policy']
assert census.hexdigest() == result['head_census_sha256']
keys = [row['indices'] for row in plan['keys']]
for policy, trace in result['clock_example'].items():
    cipher = [step['cipher'] for step in trace]
    assert independent(cipher, keys, (0, 0), 0, -1, policy) == [step['plain'] for step in trace]
print('PASS: independent state clocks, every page-opening comparison and full output digest')
