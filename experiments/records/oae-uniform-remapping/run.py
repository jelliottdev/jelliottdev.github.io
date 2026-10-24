"""Census every uniform O/A/AE remapping, using exact count tables."""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def calculate():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    raw = (ROOT / plan['input']['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == plan['input']['sha256']
    alphabet, family = plan['alphabet'], plan['family']
    stream = [c for c in raw.decode('utf-8') if c in alphabet]
    counts = Counter(stream)
    edges = Counter(zip(stream, stream[1:]))
    fixed_repeats = sum(n for (a, b), n in edges.items() if a == b and a not in family)
    rows = []
    for targets in product(family, repeat=3):
        mapping = dict(zip(family, targets))
        after = Counter({c: n for c, n in counts.items() if c not in family})
        for c in family:
            after[mapping[c]] += counts[c]
        n = len(stream)
        collision_sum = sum(v * (v - 1) for v in after.values())
        repeats = fixed_repeats + sum(k for (a, b), k in edges.items()
                                      if a in family and b in family and mapping[a] == mapping[b])
        rows.append({'targets': ''.join(targets), 'bijective': len(set(targets)) == 3,
                     'observed_alphabet': len(after), 'adjacent_equal': repeats,
                     'adjacent_pairs': n - 1, 'collision_numerator': collision_sum,
                     'collision_denominator': n * (n - 1),
                     'raw_ioc': collision_sum / (n * (n - 1)),
                     'fixed29_ioc': 29 * collision_sum / (n * (n - 1)),
                     'source_variable_alphabet_ioc': len(after) * collision_sum / (n * (n - 1))})
    baseline = next(r for r in rows if r['targets'] == family)
    assert all(r['adjacent_equal'] == baseline['adjacent_equal']
               and r['collision_numerator'] == baseline['collision_numerator']
               for r in rows if r['bijective'])
    collapsed = [r for r in rows if len(set(r['targets'])) == 1]
    assert all(r['adjacent_equal'] == max(x['adjacent_equal'] for x in rows)
               and r['collision_numerator'] == max(x['collision_numerator'] for x in rows)
               for r in collapsed)
    return {'schema': 'liberpedia-uniform-rune-remapping-v1',
            'plan_sha256': hashlib.sha256(plan_bytes).hexdigest(),
            'input_sha256': plan['input']['sha256'], 'runes': len(stream),
            'family_counts': {c: counts[c] for c in family},
            'family_to_family_adjacent_pairs': sum(k for (a, b), k in edges.items()
                                                  if a in family and b in family),
            'rows': rows, 'baseline': baseline, 'collapsed': collapsed[0]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
        print('PASS: all 27 uniform maps, six permutation controls and exact bounds')
    else:
        (HERE / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: result[k] for k in ['runes', 'family_counts', 'baseline', 'collapsed']}, ensure_ascii=False))
