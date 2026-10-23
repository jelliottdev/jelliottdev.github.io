"""Recount supplied matrix lengths and census all contiguous LP2-00..39 intervals."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
KEYS = ('runes', 'prime_digits', 'index_0_digits', 'index_1_digits')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    audit_path = ROOT / plan['source_audit']
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    index_path = ROOT / 'data/index.json'
    alphabet = json.loads(index_path.read_text(encoding='utf-8'))['alphabet']
    lookup = {row['rune']: (i, row['prime']) for i, row in enumerate(alphabet)}
    assert len(lookup) == 29
    sources = {'data/index.json': digest(index_path), plan['source_audit']: digest(audit_path)}
    per_page = []
    for n in range(40):
        relative = f'text/lp2-{n:02}.txt'
        path = ROOT / relative
        raw = path.read_text(encoding='utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        assert not unknown, (relative, unknown)
        runes = [lookup[c] for c in raw if c in lookup]
        per_page.append({
            'runes': len(runes),
            'prime_digits': sum(len(str(prime)) for _, prime in runes),
            'index_0_digits': sum(len(str(i)) for i, _ in runes),
            'index_1_digits': sum(len(str(i + 1)) for i, _ in runes),
        })
        sources[relative] = digest(path)
    assert all(sources[k] == v for k, v in audit['sources_sha256'].items())

    prefixes = {key: [0] for key in KEYS}
    for row in per_page:
        for key in KEYS:
            prefixes[key].append(prefixes[key][-1] + row[key])
    def interval(a, b):
        return {key: prefixes[key][b+1] - prefixes[key][a] for key in KEYS}

    listed = []
    for a, b in plan['listed_groups']:
        lengths = interval(a, b)
        reference = next(row for row in audit['groups'] if row['pages'] == f'lp2-{a:02}–{b:02}')
        assert all(lengths[key] == reference[key] for key in KEYS)
        listed.append({'pages': f'LP2-{a:02}–{b:02}', 'first': a, 'last': b, **lengths})

    intervals = [(a, b, interval(a, b)) for a in range(40) for b in range(a, 40)]
    assert len(intervals) == 820
    squares = {}
    for key in KEYS:
        matching = [{'first': a, 'last': b, 'length': row[key], 'side': math.isqrt(row[key])}
                    for a, b, row in intervals if row[key] > 0 and math.isqrt(row[key])**2 == row[key]]
        squares[key] = {'count': len(matching), 'intervals': matching}

    # Exact-length recurrence is descriptive; no significance model is implied.
    target_cases = [
        ('LP2-00–02', 'runes', 729), ('LP2-03–07', 'prime_digits', 2345),
        ('LP2-08–14', 'runes', 1729), ('LP2-08–14', 'index_1_digits', 2915),
        ('LP2-16–22', 'prime_digits', 3481), ('LP2-23–26', 'runes', 1021),
        ('LP2-27–31', 'runes', 1312), ('LP2-27–31', 'index_0_digits', 2200),
        ('LP2-32–32', 'runes', 121), ('LP2-32–32', 'index_0_digits', 196),
        ('LP2-33–38', 'runes', 1440), ('LP2-33–39', 'runes', 1680),
        ('LP2-39–39', 'runes', 240),
    ]
    recurrence = []
    for label, key, length in target_cases:
        assert next(row for row in listed if row['pages'] == label)[key] == length
        matches = [{'first': a, 'last': b} for a, b, row in intervals if row[key] == length]
        recurrence.append({'pages': label, 'representation': key, 'length': length,
                           'interval_count': len(matches), 'intervals': matches})

    body = (ROOT / 'text/lp2-15.txt').read_text(encoding='utf-8').partition('\n')[2]
    body_runes = [lookup[c] for c in body if c in lookup]
    assert len(body_runes) == audit['lp2_15_body_excluding_header']['runes'] == 150
    assert sum(len(str(p)) for _, p in body_runes) == 289
    return {
        'schema': 'liberpedia-cc-section-representation-census-v1',
        'sources_sha256': sources,
        'page_count': 40,
        'interval_count': len(intervals),
        'listed_groups': listed,
        'page_15_body': {'runes': 150, 'prime_digits': 289, 'square_side': 17},
        'conditional_claims': {'branches_index_1_digits': 2915, 'after_one_extra_printed_digit': 2916,
                               'mayfly_runes': 1021, 'after_removing_16_hypothesized_runes': 1005},
        'perfect_square_intervals': squares,
        'target_length_recurrence': recurrence,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = compute()
    path = HERE / 'results.json'
    if args.check:
        assert json.loads(path.read_text(encoding='utf-8')) == result
        print('PASS: matrix representation census matches all pinned inputs and saved results')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(f'Wrote {path}')
