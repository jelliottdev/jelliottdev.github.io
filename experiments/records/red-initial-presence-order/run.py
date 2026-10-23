"""Corrected LP2 large-red-initial page-order control. Standard library only."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import zlib

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TRIALS = 100_000
SEED = 3301
N = 58


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positions(rows, field):
    return tuple(int(row['page'][-2:]) for row in rows if row[field] == '1')


def gap_score(selected):
    gaps = [b - a for a, b in zip(selected, selected[1:])]
    m = len(gaps)
    return m * sum(g * g for g in gaps) - sum(gaps) ** 2


def max_run(selected):
    best = current = 1
    for a, b in zip(selected, selected[1:]):
        current = current + 1 if b == a + 1 else 1
        best = max(best, current)
    return best


def packed_length(selected):
    bits = sum(1 << (63 - p) for p in selected)
    return len(zlib.compress(bits.to_bytes(8, 'big'), level=9))


def count_with_run_at_most(n, k, maximum):
    states = {(0, 0): 1}  # (number selected, current run) -> count
    for _ in range(n):
        following = {}
        for (used, run), count in states.items():
            following[(used, 0)] = following.get((used, 0), 0) + count
            if used < k and run < maximum:
                following[(used + 1, run + 1)] = following.get((used + 1, run + 1), 0) + count
        states = following
    return sum(count for (used, _), count in states.items() if used == k)


def exact_probabilities(selected):
    k = len(selected)
    total = math.comb(N, k)
    span = selected[-1] - selected[0]
    short_span = sum((N - s) * math.comb(s - 1, k - 2)
                     for s in range(k - 1, span + 1))
    run = max_run(selected)
    long_run = total - count_with_run_at_most(N, k, run - 1)
    return {
        'span': span,
        'span_lower_numerator': short_span,
        'max_run': run,
        'max_run_upper_numerator': long_run,
        'denominator': total,
        'span_lower_p': short_span / total,
        'max_run_upper_p': long_run / total,
    }


def monte_carlo(selected, regular, block):
    rng = random.Random(SEED)
    observed_gap = gap_score(selected)
    observed_compressed = packed_length(selected)
    low_gap = high_gap = low_compressed = low_regular = low_block = 0
    regular_gap = gap_score(regular)
    block_gap = gap_score(block)
    compressed_counts = {}
    for _ in range(TRIALS):
        candidate = tuple(sorted(rng.sample(range(N), len(selected))))
        value = gap_score(candidate)
        low_gap += value <= observed_gap
        high_gap += value >= observed_gap
        low_regular += value <= regular_gap
        low_block += value <= block_gap
        size = packed_length(candidate)
        low_compressed += size <= observed_compressed
        compressed_counts[size] = compressed_counts.get(size, 0) + 1
    gap_count = len(selected) - 1
    return {
        'trials': TRIALS,
        'seed': SEED,
        'gap_variance': observed_gap / gap_count ** 2,
        'gap_lower_hits': low_gap,
        'gap_upper_hits': high_gap,
        'gap_lower_p': (low_gap + 1) / (TRIALS + 1),
        'gap_upper_p': (high_gap + 1) / (TRIALS + 1),
        'compressed_bytes': observed_compressed,
        'compressed_lower_hits': low_compressed,
        'compressed_lower_p': (low_compressed + 1) / (TRIALS + 1),
        'compressed_null_counts': {str(k): v for k, v in sorted(compressed_counts.items())},
        'regular_gap_lower_hits': low_regular,
        'regular_gap_lower_p': (low_regular + 1) / (TRIALS + 1),
        'block_gap_lower_hits': low_block,
        'block_gap_lower_p': (low_block + 1) / (TRIALS + 1),
        'zlib_version': zlib.ZLIB_VERSION,
    }


def build():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan['inputs']:
        actual = sha(ROOT / item['path'])
        if actual != item['sha256']:
            raise ValueError(f"Input changed: {item['path']}")
    with (ROOT / 'research/red-initials-audit.csv').open(newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    if len(rows) != N or [row['page'] for row in rows] != [f'LP2-{p:02d}' for p in range(N)]:
        raise ValueError('Expected every LP2 page in printed order')
    selected = positions(rows, 'component_rule')
    source = positions(rows, 'source_total_rule')
    if len(selected) != 13 or len(source) != 15 or set(source) - set(selected) != {7, 53}:
        raise ValueError('Image audit and declared source comparison disagree')
    regular = tuple(round(p * 57 / 12) for p in range(13))
    block = tuple(range(13))
    exact = exact_probabilities(selected)
    simulated = monte_carlo(selected, regular, block)
    tests = [exact['span_lower_p'], exact['max_run_upper_p'],
             simulated['gap_lower_p'], simulated['gap_upper_p'],
             simulated['compressed_lower_p']]
    return {
        'schema': 'liberpedia-red-initial-presence-order-v1',
        'plan_sha256': hashlib.sha256(plan_bytes).hexdigest(),
        'corrected_pages': list(selected),
        'source_total_red_pages': list(source),
        'source_only_pages': [7, 53],
        'observed': {**exact, **simulated},
        'bonferroni_min_p': min(1.0, 5 * min(tests)),
        'controls': {
            'approximately_even_pages': list(regular),
            'even_gap_variance': gap_score(regular) / 12 ** 2,
            'even_gap_lower_p': simulated['regular_gap_lower_p'],
            'even_compressed_bytes': packed_length(regular),
            'consecutive_pages': list(block),
            'block_span_lower_p': exact_probabilities(block)['span_lower_p'],
            'block_max_run_upper_p': exact_probabilities(block)['max_run_upper_p'],
            'block_gap_variance': gap_score(block) / 12 ** 2,
            'block_gap_lower_p': simulated['block_gap_lower_p'],
            'block_compressed_bytes': packed_length(block),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = build()
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if output != (HERE / 'results.json').read_text(encoding='utf-8'):
            raise SystemExit('Saved result does not match the replay')
        print('PASS: corrected page list, exact run/span tails and seeded spacing control')
    else:
        (HERE / 'results.json').write_text(output, encoding='utf-8', newline='\n')
        print(f"Saved {HERE / 'results.json'}")


if __name__ == '__main__':
    main()
