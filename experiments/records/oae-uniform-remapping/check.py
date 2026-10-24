"""Independent full-stream remapping; no producer imports or edge tables."""
from collections import Counter
from itertools import product
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[2]
plan = json.loads((here / 'plan.json').read_bytes())
saved = json.loads((here / 'results.json').read_bytes())
raw = (root / plan['input']['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == plan['input']['sha256']
source = ''.join(c for c in raw.decode('utf-8') if c in plan['alphabet'])
assert len(source) == saved['runes']
assert len(saved['rows']) == 27
for targets, row in zip(product(plan['family'], repeat=3), saved['rows']):
    mapped = source.translate(str.maketrans(dict(zip(plan['family'], targets))))
    counts = Counter(mapped)
    assert row['targets'] == ''.join(targets)
    assert row['adjacent_equal'] == sum(a == b for a, b in zip(mapped, mapped[1:]))
    num = sum(n * (n - 1) for n in counts.values())
    den = len(mapped) * (len(mapped) - 1)
    assert row['collision_numerator'] == num and row['collision_denominator'] == den
    assert row['observed_alphabet'] == len(counts)
    assert row['raw_ioc'] == num / den
    assert row['fixed29_ioc'] == 29 * num / den
    assert row['source_variable_alphabet_ioc'] == len(counts) * num / den
assert saved['plan_sha256'] == hashlib.sha256((here / 'plan.json').read_bytes()).hexdigest()
print('PASS: every full remapped stream reproduces repeats and both IoC normalizations')
