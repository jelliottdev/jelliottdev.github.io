"""Replay long repeated LP2 rune n-grams with sectionwise step-shuffle controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SECTIONS = [(0, 2), (3, 7), (8, 14), (15, 22), (23, 26),
            (27, 32), (33, 39), (40, 53), (54, 55)]
LENGTHS = (5, 6, 7)
TRIALS = 999
SEED = 3301


def repeated(values: list[int], n: int) -> dict[tuple[int, ...], list[int]]:
    positions: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for i in range(len(values) - n + 1):
        positions[tuple(values[i:i+n])].append(i)
    return {gram: locs for gram, locs in positions.items() if len(locs) > 1}


def shuffled_steps(section: list[int], rng: random.Random) -> list[int]:
    steps = [(b-a) % 29 for a, b in zip(section, section[1:])]
    rng.shuffle(steps)
    rebuilt = [section[0]]
    for step in steps:
        rebuilt.append((rebuilt[-1] + step) % 29)
    return rebuilt


def calculate() -> dict:
    idx = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    alphabet = {row['rune']: row['index'] for row in idx['alphabet']}
    labels = {row['index']: row['latin'] for row in idx['alphabet']}
    sections = [[alphabet[c] for page in range(lo, hi+1)
                 for c in (ROOT/f'text/lp2-{page:02}.txt').read_text(encoding='utf-8')
                 if c in alphabet] for lo, hi in SECTIONS]
    stream = [v for section in sections for v in section]
    assert len(stream) == 12956
    observed = {n: repeated(stream, n) for n in LENGTHS}
    rng = random.Random(SEED)
    null_counts = {str(n): [] for n in LENGTHS}
    for _ in range(TRIALS):
        surrogate = [v for section in sections for v in shuffled_steps(section, rng)]
        for n in LENGTHS:
            null_counts[str(n)].append(len(repeated(surrogate, n)))
    counts = {str(n): len(observed[n]) for n in LENGTHS}
    null_hit = {str(n): sum(x >= counts[str(n)] for x in null_counts[str(n)])
                for n in LENGTHS}
    # Seven-gram count is zero, so only the 5/6-gram candidates enter this union.
    any_hit = sum(a >= counts['5'] or b >= counts['6']
                  for a, b in zip(null_counts['5'], null_counts['6']))
    # Strong planted recurrence: copy a 6-gram to a distant position in a
    # control stream. The difference count must increase at least one.
    plant = [v for section in sections for v in shuffled_steps(section, rng)]
    before = len(repeated(plant, 6))
    plant[9000:9006] = plant[1000:1006]
    after = len(repeated(plant, 6))
    assert after > before
    inputs = ['data/index.json'] + [f'text/lp2-{i:02}.txt' for i in range(56)]
    return {'schema': 'liberpedia-repeated-long-ngrams-v1',
            'input_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
            'section_ranges': [list(pair) for pair in SECTIONS], 'runes': len(stream),
            'definition': 'Distinct repeated contiguous rune-index tuples, including overlapping windows and cross-section boundaries in the concatenated corpus.',
            'observed_counts': counts,
            'observed_repeats': {str(n): [{'runes': ''.join(labels[v] for v in gram), 'indices': list(gram), 'positions': locs}
                                          for gram, locs in sorted(observed[n].items(), key=lambda pair: pair[1])]
                                 for n in LENGTHS},
            'null': 'Shuffle all adjacent modular rune differences within each of nine sections; preserve each section first rune, length and exact difference inventory; concatenate and recount.',
            'seed': SEED, 'trials': TRIALS, 'null_counts': null_counts,
            'null_at_least_observed': null_hit,
            'any_5_or_6_at_least_observed': any_hit,
            'planted_6gram': {'before': before, 'after': after, 'copied_from': 1000, 'copied_to': 9000}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    path = HERE/'results.json'
    if args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
        print('repeated-long-ngrams: checked')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print({k: result[k] for k in ('observed_counts', 'null_at_least_observed', 'any_5_or_6_at_least_observed', 'planted_6gram')})


if __name__ == '__main__':
    main()
