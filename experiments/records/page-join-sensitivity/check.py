"""Independent streaming check of page-edge token counts and invariants."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet = {row['rune'] for row in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
pages = [(ROOT/f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8').translate(str.maketrans('', '', '/\r\n')) for n in range(56)]
edges = {n for n in range(55) if pages[n][-1] in alphabet and pages[n+1][0] in alphabet}
assert len(edges) == 32
assert report['candidate_edges'] == [f'LP2-{n:02d}/{n+1:02d}' for n in sorted(edges)]

def scan(separate):
    lengths = []
    current = 0
    for number, page in enumerate(pages):
        if number and (number-1) in separate and current:
            lengths.append(current)
            current = 0
        for char in page:
            if char in alphabet:
                current += 1
            elif char == "'" and current:
                continue
            elif current:
                lengths.append(current)
                current = 0
    if current:
        lengths.append(current)
    return lengths

joined = scan(set())
separated = scan(edges)
for values, label in ((joined, 'all_joined'), (separated, 'all_candidates_separated')):
    saved = report[label]
    assert len(values) == saved['token_count']
    assert max(values) == saved['max_length']
    assert {str(k): v for k, v in sorted(Counter(values).items())} == saved['histogram']
    assert sum(v >= 10 for v in values) == saved['long_tokens_10_plus']
    assert sum(values) == 12956
assert len(separated) - len(joined) == 32
for n, row in zip(sorted(edges), report['single_edge_splits']):
    assert row['edge'] == f'LP2-{n:02d}/{n+1:02d}'
    values = scan({n})
    assert len(values) == row['split_token_count'] == len(joined)+1
    assert max(values) == row['split_max_length']
    assert sum(v >= 10 for v in values) == row['split_long_tokens_10_plus']
print('PASS: independent scanner reproduces 32 edge effects and 12,956-rune invariant')
