"""Independent extraction and control-count spot checks for long rune repeats."""
import json
import random
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[3]
here = Path(__file__).resolve().parent
data = json.loads((here/'results.json').read_text(encoding='utf-8'))
alphabet = {row['rune']: row['index'] for row in json.loads((root/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
blocks = []
for lo, hi in data['section_ranges']:
    chars = ''.join((root/f'text/lp2-{p:02}.txt').read_text(encoding='utf-8') for p in range(lo, hi+1))
    blocks.append([alphabet[c] for c in chars if c in alphabet])
plain = [v for block in blocks for v in block]
assert len(plain) == data['runes'] == 12956

def count(x, n):
    return sum(m > 1 for m in Counter(tuple(x[k:k+n]) for k in range(len(x)-n+1)).values())

for n in (5, 6, 7):
    assert count(plain, n) == data['observed_counts'][str(n)]
    for item in data['observed_repeats'][str(n)]:
        assert all(plain[p:p+n] == item['indices'] for p in item['positions'])

randomizer = random.Random(data['seed'])
for trial in range(12):
    sample = []
    for block in blocks:
        increments = [(block[i]-block[i-1]) % 29 for i in range(1, len(block))]
        randomizer.shuffle(increments)
        reconstructed = [block[0]]
        for delta in increments:
            reconstructed.append((reconstructed[-1]+delta) % 29)
        sample.extend(reconstructed)
    for n in (5, 6, 7):
        assert count(sample, n) == data['null_counts'][str(n)][trial]
assert data['any_5_or_6_at_least_observed'] == sum(
    a >= 6 or b >= 1 for a, b in zip(data['null_counts']['5'], data['null_counts']['6']))
print('repeated-long-ngrams: independent extraction, counts and first 12 controls checked')
