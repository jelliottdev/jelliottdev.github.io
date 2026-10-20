"""Independent endpoint enumeration and sieve, using archived page records."""
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
tokens = []
for number in (49, 50, 51):
    page = f'lp2-{number}'
    raw = json.loads((ROOT / f'data/pages/{page}.json').read_text(encoding='utf-8'))['raw']
    grid_row = 0
    for line in raw.splitlines():
        if re.fullmatch(r'[0-9A-Za-z]{2}(?:-[0-9A-Za-z]{2})+/?', line):
            grid_row += 1
            row = line.removesuffix('/').split('-')
            assert len(row) == 8
            for column, token in enumerate(row, 1):
                tokens.append(dict(page=page, row=grid_row, column=column,
                                   sequence=len(tokens)+1, token=token))
assert len(tokens) == 256
sieve = [True] * 3334
sieve[:2] = [False, False]
for n in range(2, 58):
    if sieve[n]:
        for multiple in range(n*n, len(sieve), n):
            sieve[multiple] = False
hits = {}
total = eligible = 0
for a, b in itertools.permutations(range(256), 2):
    x, y, xx, yy = a % 8, a // 8, b % 8, b // 8
    if max(abs(xx-x), abs(yy-y)) != 3 or (xx-x) % 3 or (yy-y) % 3:
        continue
    dx, dy = (xx-x)//3, (yy-y)//3
    cells = [tokens[(y+i*dy)*8+x+i*dx] for i in range(4)]
    if len({c['page'] for c in cells}) != 1:
        continue
    total += 1
    digits = ''.join(c['token'][0] for c in cells)
    if '4' in digits:
        continue
    eligible += 1
    if sieve[int(digits)]:
        hits[(x,y,dx,dy)] = (digits, cells)
result = json.loads(Path(__file__).with_name('results.json').read_text(encoding='utf-8'))
assert total == result['total_directed_paths'] == 1148
assert eligible == result['eligible_paths'] == 876
assert len(hits) == result['prime_occurrences'] == 151
seen = set()
for h in result['hits']:
    key = (*h['start_xy_zero_based'], *h['step_xy'])
    assert key not in seen
    seen.add(key)
    assert hits[key] == (h['digits'], h['cells'])
    assert h['decimal'] == int(h['digits'])
    assert h['suffixes'] == ''.join(c['token'][1] for c in h['cells'])
    base4 = sum(int(d)*4**(3-i) for i,d in enumerate(h['digits']))
    assert h['base4_value'] == base4
    assert h['base4_value_is_prime'] == sieve[base4]
    assert h['crosses_page'] == (len({c['page'] for c in h['cells']}) > 1)
assert seen == set(hits)
universe = [n for n in range(3334) if sieve[n] and set(str(n)) <= set('0123')]
actual = [int(digits) for digits,cells in hits.values()]
assert result['frequencies'] == [dict(decimal=n, digits=f'{n:04d}', count=actual.count(n)) for n in universe]
assert result['missing_primes'] == [n for n in universe if n not in actual] == [1033,1103,2213,3011,3301]
assert result['distinct_primes'] == len(set(actual)) == 44
assert result['prime_universe_size'] == len(universe) == 49
assert result['rejected_paths_containing_4'] == total-eligible
print('PASS: endpoint-pair enumeration, sieve and original-page coordinates independently agree')
