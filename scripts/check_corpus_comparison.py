"""Independent expanded-sample/statistics/bisection audit of corpus ranks.

Does not import the producer. Source-byte validation is a separate prerequisite;
this verifies the comparison against the census linked by its audit receipt.
"""
import argparse
from bisect import bisect_left, bisect_right
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def expanded_profile(histogram):
    values = []
    for key, count in histogram.items():
        assert int(key) > 0 and type(count) is int and count > 0
        values.extend([Fraction(int(key))] * count)
    assert len(values) > 1
    quantiles = statistics.quantiles(values, n=4, method='inclusive')
    variance = statistics.variance(values)
    result = {'length_' + str(k): Fraction(values.count(k), len(values)) for k in range(1, 15)}
    result.update(length_15_plus=Fraction(sum(v >= 15 for v in values), len(values)),
                  mean=statistics.mean(values), sample_variance=variance, sample_std=variance,
                  min=min(values), percentile_25=quantiles[0], median=statistics.median(values),
                  percentile_75=quantiles[2], max=max(values))
    return result


def check_rows(rows, profiles, target):
    assert [r['measure'] for r in rows] == list(target)
    for row in rows:
        name = row['measure']
        ordered = sorted(p[name] for p in profiles)
        value = target[name]
        lower, upper = bisect_left(ordered, value), bisect_right(ordered, value)
        expected = {'measure': name, 'comparison_scale': 'variance' if name == 'sample_std' else name,
                    'target_comparison_value': {'numerator': value.numerator, 'denominator': value.denominator},
                    'reference_count': len(ordered), 'below': lower, 'equal': upper - lower,
                    'above': len(ordered) - upper, 'inclusive_left_numerator': upper,
                    'inclusive_right_numerator': len(ordered) - lower}
        assert row == expected, name


def check(census_path, source_receipt_path, comparison_path):
    raw_census, raw_receipt, raw_comparison = [p.read_bytes() for p in
                                              (census_path, source_receipt_path, comparison_path)]
    census, receipt, comparison = map(json.loads, (raw_census, raw_receipt, raw_comparison))
    plan_raw = (ROOT / 'experiments/plans/corpus-prefix-comparison.json').read_bytes()
    plan = json.loads(plan_raw)
    for item in plan['inputs']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256']
    assert comparison['plan_sha256'] == sha(plan_raw)
    assert comparison['census_sha256'] == receipt['report_sha256'] == sha(raw_census)
    assert comparison['source_audit_receipt_sha256'] == sha(raw_receipt)
    assert comparison['script_sha256'] == sha((ROOT / 'scripts/compare_corpus_prefixes.py').read_bytes())
    assert receipt['checker_sha256'] == sha((ROOT / 'scripts/check_corpus_prefixes.py').read_bytes())
    assert census['complete'] is True
    assert census['specification']['revision'] == plan['source_revision']
    assert census['specification']['prefix_tokens'] == comparison['tokens_per_prefix'] == plan['tokens']
    assert comparison['target'] == plan['target']
    rows = census['records']
    assert len(rows) == census['entries'] == receipt['entries_checked'] == 25906
    assert len({r['file'] for r in rows}) == len(rows)
    assert len({r['object_id'] for r in rows}) == receipt['distinct_blobs_checked']
    by_blob, profiles = {}, []
    for row in rows:
        if not row['eligible']:
            continue
        stats = row['statistics']
        assert sum(stats['histogram'].values()) == stats['tokens'] == plan['tokens']
        assert sum(int(k) * v for k, v in stats['histogram'].items()) == stats['counted_units']
        oid = row['object_id']
        if oid not in by_blob:
            by_blob[oid] = (stats, expanded_profile(stats['histogram']))
        assert by_blob[oid][0] == stats
        profiles.append(by_blob[oid][1])
    assert len(profiles) == census['eligible_entries'] == receipt['eligible_entries']
    manuscript = json.loads((ROOT / 'exports/unsolved-word-lengths.json').read_bytes())
    histogram = manuscript[plan['target']]['histogram']
    assert sum(histogram.values()) == plan['tokens']
    target = expanded_profile(histogram)
    assert list(target) == plan['measures']
    assert set(comparison['comparisons']) == set(plan['weighting'])
    check_rows(comparison['comparisons']['eligible path'], profiles, target)
    check_rows(comparison['comparisons']['distinct eligible Git blob'], [p[1] for p in by_blob.values()], target)
    return {'comparison_sha256': sha(raw_comparison), 'census_sha256': sha(raw_census),
            'source_audit_receipt_sha256': sha(raw_receipt),
            'checker_sha256': sha(Path(__file__).read_bytes()),
            'measure_rows_checked': 46, 'eligible_paths': len(profiles), 'eligible_blobs': len(by_blob),
            'method': 'Expanded rational samples; statistics-module moments and quantiles; sorted bisection for exact ties and both inclusive tails. Source-byte audit is a separate prerequisite.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('census', type=Path)
    parser.add_argument('source_receipt', type=Path)
    parser.add_argument('comparison', type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit('Receipt already exists; choose a new path')
    result = check(args.census, args.source_receipt, args.comparison)
    with args.receipt.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(result, indent=2) + '\n')
    print('Verified all 46 comparison rows against the supplied census')
