"""Independently recount windows from page JSON using direct rune-value sums."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
values = {a['rune']: a['prime'] for a in alphabet}
saved = json.loads((ROOT / 'exports/wing-tree-windows.json').read_text(encoding='utf-8'))
assert [p['page'] for p in saved['pages']] == [f'lp2-{n}' for n in range(27, 33)]
all_sums = []
for item in saved['pages']:
    raw = json.loads((ROOT / 'data/pages' / (item['page'] + '.json')).read_text(encoding='utf-8'))['raw']
    positions = [i for i, c in enumerate(raw) if c in values]
    runes = [raw[i] for i in positions]
    expected = []
    for end in range(11, len(runes) + 1):
        start = end - 11
        expected.append(dict(start_rune=start + 1, end_rune=end,
                             source_start=positions[start], source_end_inclusive=positions[end - 1],
                             runes=''.join(runes[start:end]),
                             prime_sum=sum(values[c] for c in runes[start:end])))
    assert item['windows'] == expected, item['page']
    sums = [w['prime_sum'] for w in expected]
    assert item['rune_count'] == len(runes)
    assert item['window_count'] == len(sums)
    assert item['window_sum_total'] == sum(sums)
    assert item['hit_counts'] == {str(t): sums.count(t) for t in (563, 569)}
    all_sums.extend(sums)
assert len(all_sums) == saved['window_count'] == 1373
assert sum(all_sums) == saved['window_sum_total'] == 784505
assert saved['hit_counts'] == {str(t): all_sums.count(t) for t in (563, 569)} == {'563': 7, '569': 10}
assert saved['mean_window_sum'] == sum(all_sums) / len(all_sums)
print('PASS: independent page-record reconstruction of all 1373 windows and totals')
