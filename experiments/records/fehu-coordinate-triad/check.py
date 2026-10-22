"""Independent line-based recount of the frozen Fehu-coordinate report."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
prime = tuple(item['prime'] for item in alphabet)
symbols = {item['rune'] for item in alphabet}
all_lines = []
for number in range(58):
    page = json.loads((ROOT / 'data/pages' / f'lp2-{number:02d}.json').read_text(encoding='utf-8'))
    all_lines.extend(line['raw'] for line in page['lines'])

sequence = [character for line in all_lines for character in line if character in symbols]
fehu = [ordinal for ordinal, character in enumerate(sequence) if character == '\u16a0']
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert len(sequence) == saved['runes'] == 13136
assert len(fehu) == saved['fehu_count'] == 466
assert fehu[181] == saved['reported_start_rune_index'] == 4949

def independent_sums(one_based):
    first = one_based - 1
    result = []
    for window_number in range(3):
        segment = fehu[first + window_number * 29:first + window_number * 29 + 59]
        origin = fehu[first if window_number < 2 else first + 58]
        total = 0
        for position in segment:
            quotient, remainder = divmod(position - origin, 29)
            coordinate = quotient % 29 if window_number == 1 else remainder
            total += prime[coordinate]
        result.append(total)
    return result

assert saved['reported_sums'] == [3001, 2819, 2579]
assert independent_sums(182) == saved['reported_sums']
assert len(saved['rows']) == 350
for number, row in enumerate(saved['rows'], start=1):
    assert row['start_fehu'] == number
    assert row['sums'] == independent_sums(number)
assert saved['exact_matches'] == [{'start_fehu': 182, 'sums': [3001, 2819, 2579]}]
print('PASS: line-based recount checks all 350 starts and the reported LP2-only coordinate triad')
