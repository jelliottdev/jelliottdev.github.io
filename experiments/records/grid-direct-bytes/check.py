"""Replay every saved direct-byte case from the structured page records."""
from collections import Counter
from itertools import product
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
alphabet = plan['digit_alphabet']

def value(token):
    return 60 * alphabet.index(token[0]) + alphabet.index(token[1])

tokens = []
for page, expected in ((49, 10), (50, 13), (51, 9)):
    raw = json.loads((ROOT / f'data/pages/lp2-{page:02}.json').read_text(encoding='utf-8'))['raw']
    rows = [line.rstrip('/').split('-') for line in raw.splitlines()
            if re.fullmatch(r'[A-Za-z0-9]{2}(?:-[A-Za-z0-9]{2}){7}/?', line)]
    assert len(rows) == expected
    tokens.extend(token for row in rows for token in row)
assert len(tokens) == 256
stems = [i for i, token in enumerate(tokens) if token[-1] in 'Il']
assert len(stems) == 10

def checks(data):
    try:
        data.decode('utf-8', 'strict')
        utf8, error = True, None
    except UnicodeDecodeError as exc:
        utf8, error = False, exc.start
    cmf, flg = data[:2]
    return {
        'ASCII': all(v in (9, 10, 13) or 32 <= v <= 126 for v in data),
        'UTF-8': utf8,
        'PNG': data[:8] == bytes.fromhex('89504e470d0a1a0a'),
        'gzip': data[:3] == bytes.fromhex('1f8b08'),
        'ZIP': data[:4] == bytes.fromhex('504b0304'),
        'zlib': cmf % 16 == 8 and cmf // 16 <= 7 and (cmf * 256 + flg) % 31 == 0,
        'utf8_error_at': error,
    }

# Synthetic controls ensure the screen recognizes what its plan says it recognizes.
control = bytes([65] * 256)
assert checks(control)['ASCII'] and checks(control)['UTF-8']
assert checks(bytes.fromhex('89504e470d0a1a0a') + control[8:])['PNG']
assert checks(bytes.fromhex('1f8b08') + control[3:])['gzip']
assert checks(bytes.fromhex('504b0304') + control[4:])['ZIP']
assert checks(bytes.fromhex('7801') + control[2:])['zlib']

cases = {(case['route'], case['mask']): case for case in result['cases']}
assert len(cases) == result['case_count'] == 16 * 1024
totals = Counter()
orders = set()
for axis, outer_reverse, inner_reverse, alternate in product(('rows', 'columns'), (False, True), (False, True), (False, True)):
    route_id = f'{axis}-{int(outer_reverse)}{int(inner_reverse)}{int(alternate)}'
    outer_count, inner_count = (32, 8) if axis == 'rows' else (8, 32)
    order = []
    for step, outer in enumerate(reversed(range(outer_count)) if outer_reverse else range(outer_count)):
        inner = reversed(range(inner_count)) if inner_reverse ^ (alternate and step % 2 == 1) else range(inner_count)
        order.extend((outer * 8 + i) if axis == 'rows' else (i * 8 + outer) for i in inner)
    assert sorted(order) == list(range(256))
    assert tuple(order) not in orders
    orders.add(tuple(order))
    for mask in range(1024):
        candidate = tokens.copy()
        for bit, position in enumerate(stems):
            candidate[position] = candidate[position][0] + ('l' if mask & (1 << bit) else 'I')
        data = bytes(value(candidate[i]) for i in order)
        actual = checks(data)
        saved = cases[(route_id, mask)]
        assert saved['sha256'] == hashlib.sha256(data).hexdigest()
        assert saved['first_8_hex'] == data[:8].hex()
        assert saved['screens'] == {name: actual[name] for name in saved['screens']}
        assert saved['utf8_error_at'] == actual['utf8_error_at']
        totals.update({name: int(actual[name]) for name in saved['screens']})
assert len(orders) == 16
assert {name: totals[name] for name in result['total_screen_counts']} == result['total_screen_counts']
print('Independent page-record replay and synthetic controls pass for all 16,384 cases.')
