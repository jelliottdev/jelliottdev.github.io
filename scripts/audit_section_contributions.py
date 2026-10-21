"""Descriptive section contributions to the fixed 16-column LP1 arrangement.

No shuffle, selection, fitted parameter or significance test is performed.
"""
import argparse
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'experiments/records/lp1-word-length-balance/'


def calculate():
    plan = json.loads((ROOT / (BASE + 'plan.json')).read_bytes())
    spec = importlib.util.spec_from_file_location('baseline', ROOT / (BASE + 'run.py'))
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    words, _ = baseline.reconstruct(plan)
    assert words == json.loads((ROOT / (BASE + 'words.json')).read_bytes())
    n, total, k = len(words), sum(w['rune_length'] for w in words), plan['columns']
    assert (n, total, k) == (464, 1796, 16)
    sections = []
    for section in plan['sections']:
        chosen = [w for w in words if w['section'] == section['id']]
        counts = [sum(w['column'] == j + 1 for w in chosen) for j in range(k)]
        sums = [sum(w['rune_length'] for w in chosen if w['column'] == j + 1) for j in range(k)]
        # Global mean reference: n times excess runes, avoiding rounded values.
        excess = [n * s - total * c for s, c in zip(sums, counts)]
        sections.append({'section': section['id'], 'words': len(chosen),
                         'column_counts': counts, 'column_sums': sums,
                         'scaled_excess': excess,
                         'excess_runes': [str(Fraction(x, n)) for x in excess]})
    combined = [sum(s['scaled_excess'][j] for s in sections) for j in range(k)]
    # A second route assigns each word directly from its ordinal, ignoring
    # stored column labels and the section aggregation above.
    direct = [sum(n * w['rune_length'] - total for i, w in enumerate(words) if i % k == j)
              for j in range(k)]
    assert combined == direct
    diagonal = [sum(x*x for x in s['scaled_excess']) for s in sections]
    pairs = []
    for a in range(len(sections)):
        for b in range(a):
            dot = sum(x*y for x, y in zip(sections[a]['scaled_excess'], sections[b]['scaled_excess']))
            # Direct word-pair expansion provides an independent arithmetic check.
            direct_dot = sum((n*x['rune_length']-total)*(n*y['rune_length']-total)
                             for i, x in enumerate(words) if x['section'] == sections[a]['section']
                             for j, y in enumerate(words) if y['section'] == sections[b]['section'] and i % k == j % k)
            assert dot == direct_dot
            pairs.append({'sections': [sections[b]['section'], sections[a]['section']],
                          'twice_dot_in_runes_squared': str(Fraction(2*dot, n*n))})
    energy = sum(x*x for x in combined)
    assert Fraction(energy, n*n) == sum(Fraction(x, n*n) for x in diagonal) + sum(Fraction(p['twice_dot_in_runes_squared']) for p in pairs)
    result = json.loads((ROOT / (BASE + 'results.json')).read_bytes())
    assert Fraction(energy, n*n) == Fraction(result['observed_integer_score'], k*k)
    paths = [BASE + name for name in ['plan.json', 'run.py', 'words.json', 'results.json']]
    paths += list(plan['input_hashes'])
    return {'scope': __doc__, 'words': n, 'runes': total, 'columns': k,
            'reference_mean_runes': str(Fraction(total, n)),
            'sections': sections, 'combined_excess_runes': [str(Fraction(x, n)) for x in combined],
            'section_energies_runes_squared': [str(Fraction(x, n*n)) for x in diagonal],
            'pair_contributions': pairs,
            'sum_section_energies': str(Fraction(sum(diagonal), n*n)),
            'combined_energy': str(Fraction(energy, n*n)),
            'limits': 'Fixed original order and width 16. Global mean reference, not separate section means. Unequal section counts per column are retained. Cross terms describe cancellation or reinforcement, not probability, causation or intent.',
            'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = calculate()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ['sum_section_energies', 'combined_energy', 'pair_contributions']}, indent=2))
