"""Exact descriptive ranks from a complete census with its source-audit receipt.

No p-values or language probabilities. Standard deviation is compared through
variance, preserving exact ordering and ties without a floating square root.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'experiments/plans/corpus-prefix-comparison.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def exact_profile(histogram):
    pairs = sorted((int(k), v) for k, v in histogram.items())
    assert pairs and all(k > 0 and type(v) is int and v > 0 for k, v in pairs)
    assert len({k for k, v in pairs}) == len(pairs)
    n = sum(v for k, v in pairs)
    assert n > 1
    total = sum(k * v for k, v in pairs)
    variance = Fraction(n * sum(k * k * v for k, v in pairs) - total * total, n * (n - 1))
    def at(index):
        cumulative = 0
        for length, count in pairs:
            cumulative += count
            if index < cumulative:
                return length
        raise AssertionError('Rank outside histogram')
    def quantile(q):
        position = (n - 1) * q
        low = position.numerator // position.denominator
        weight = position - low
        return at(low) * (1 - weight) + at(min(low + 1, n - 1)) * weight
    counts = dict(pairs)
    values = {'length_' + str(k): Fraction(counts.get(k, 0), n) for k in range(1, 15)}
    values.update(length_15_plus=Fraction(sum(v for k, v in pairs if k >= 15), n),
                  mean=Fraction(total, n), sample_variance=variance,
                  sample_std=variance, min=Fraction(pairs[0][0]),
                  percentile_25=quantile(Fraction(1, 4)), median=quantile(Fraction(1, 2)),
                  percentile_75=quantile(Fraction(3, 4)), max=Fraction(pairs[-1][0]))
    return values


def rank_profiles(profiles, target):
    assert profiles
    result = []
    for measure, value in target.items():
        below = sum(p[measure] < value for p in profiles)
        equal = sum(p[measure] == value for p in profiles)
        above = len(profiles) - below - equal
        result.append({'measure': measure,
                       'comparison_scale': 'variance' if measure == 'sample_std' else measure,
                       'target_comparison_value': {'numerator': value.numerator, 'denominator': value.denominator},
                       'reference_count': len(profiles), 'below': below, 'equal': equal, 'above': above,
                       'inclusive_left_numerator': below + equal,
                       'inclusive_right_numerator': above + equal})
    return result


def compare(report_path, receipt_path):
    plan = json.loads(PLAN.read_bytes())
    for item in plan['inputs']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    raw = report_path.read_bytes()
    report = json.loads(raw)
    receipt = json.loads(receipt_path.read_bytes())
    assert report['complete'] is True and report['entries'] == len(report['records']) == 25906
    assert report['specification']['revision'] == plan['source_revision']
    assert report['specification']['prefix_tokens'] == plan['tokens']
    assert receipt['report_sha256'] == sha(raw) and receipt['entries_checked'] == 25906
    assert receipt['checker_sha256'] == sha((ROOT / 'scripts/check_corpus_prefixes.py').read_bytes())
    rows = report['records']
    assert len({r['file'] for r in rows}) == len(rows)
    assert receipt['distinct_blobs_checked'] == len({r['object_id'] for r in rows})
    eligible = [r for r in rows if r['eligible']]
    assert len(eligible) == report['eligible_entries'] == receipt['eligible_entries']
    manuscript = json.loads((ROOT / 'exports/unsolved-word-lengths.json').read_bytes())
    histogram = manuscript[plan['target']]['histogram']
    assert sum(histogram.values()) == plan['tokens']
    target = exact_profile(histogram)
    assert list(target) == plan['measures']
    profiles, unique, seen = [], [], {}
    for row in eligible:
        stats = row['statistics']
        assert stats['tokens'] == sum(stats['histogram'].values()) == plan['tokens']
        assert stats['counted_units'] == sum(int(k) * v for k, v in stats['histogram'].items())
        oid = row['object_id']
        if oid in seen:
            assert seen[oid][0] == stats
            profile = seen[oid][1]
        else:
            profile = exact_profile(stats['histogram'])
            seen[oid] = (stats, profile)
            unique.append(profile)
        profiles.append(profile)
    return {'status': 'descriptive comparison; independent comparison check still required',
            'plan_sha256': sha(PLAN.read_bytes()), 'census_sha256': sha(raw),
            'source_audit_receipt_sha256': sha(receipt_path.read_bytes()),
            'script_sha256': sha(Path(__file__).read_bytes()),
            'target': plan['target'], 'tokens_per_prefix': plan['tokens'],
            'comparisons': {'eligible path': rank_profiles(profiles, target),
                            'distinct eligible Git blob': rank_profiles(unique, target)},
            'limits': 'Fixed corpus-prefix positions, not calibrated p-values or language probabilities. All 23 measures retained. Standard-deviation comparisons use exact variance; their stored target comparison value is variance, not standard deviation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Output already exists; choose a new path')
    result = compare(args.report, args.receipt)
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(result, indent=2) + '\n')
    print('Wrote all 23 comparisons under both weighting policies; independent comparison check pending')
