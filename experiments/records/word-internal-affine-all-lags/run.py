"""Compare a full 12-lag, 841-map affine search with shuffled-word controls."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MOD = 29


def load():
    raw = (HERE / 'plan.json').read_bytes()
    plan = json.loads(raw)
    if plan['schema'] != 'liberpedia-affine-all-lags-plan-v1' or plan['lags'] != list(range(1, 13)) or plan['trials'] != 999:
        raise ValueError('Plan differs from this reviewed implementation')
    for item in plan['inputs']:
        if hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f"Input changed: {item['path']}")
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    lookup = {entry['rune']: i for i, entry in enumerate(index['alphabet'])}
    if len(lookup) != MOD:
        raise ValueError('Expected 29 runes')
    words = []
    for page in plan['source_pages']:
        text = (ROOT / 'text' / f'{page}.txt').read_text(encoding='utf-8')
        unknown = {c for c in text if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unmapped runes: {page}')
        words.extend(word for part in re.split(r'[-.]', text)
                     if (word := [lookup[c] for c in part if c in lookup]))
    return plan, hashlib.sha256(raw).hexdigest(), words


def pair_matrix(words, lag):
    matrix = [[0] * MOD for _ in range(MOD)]
    opportunities = 0
    for word in words:
        for i in range(len(word) - lag):
            matrix[word[i]][word[i + lag]] += 1
            opportunities += 1
    return matrix, opportunities


def expected_matrix(words, lag):
    """Exact pair means when rune order is random within each fixed-multiset word."""
    matrix = [[0.0] * MOD for _ in range(MOD)]
    for word in words:
        n = len(word)
        if n <= lag:
            continue
        counts = Counter(word)
        weight = (n - lag) / (n * (n - 1))
        for x, nx in counts.items():
            for y, ny in counts.items():
                matrix[x][y] += weight * nx * (ny - (x == y))
    return matrix


MAPS = [(a, b, tuple((a*x+b) % MOD for x in range(MOD)))
        for a in range(MOD) for b in range(MOD)]


def scan(matrix, expected, lag):
    for a, b, ys in MAPS:
        count = sum(matrix[x][ys[x]] for x in range(MOD))
        mean = sum(expected[x][ys[x]] for x in range(MOD))
        yield ((count - mean) / math.sqrt(mean + 1), lag, a, b, count, mean)


def best(rows):
    return min(rows, key=lambda row: (-row[0], row[1], row[2], row[3]))


def describe(row):
    score, lag, a, b, count, mean = row
    return {'lag': lag, 'a': a, 'b': b, 'matches': count,
            'word_shuffle_mean': round(mean, 6), 'score': round(score, 6)}


def report():
    plan, plan_hash, words = load()
    expected = {lag: expected_matrix(words, lag) for lag in plan['lags']}
    rows, opportunities = [], {}
    for lag in plan['lags']:
        matrix, n = pair_matrix(words, lag)
        opportunities[str(lag)] = n
        rows.extend(scan(matrix, expected[lag], lag))
    selected = best(rows)
    supplied = next(row for row in rows if row[1:4] == (6, 27, 24))
    by_lag = [describe(best(row for row in rows if row[1] == lag)) for lag in plan['lags']]
    rng = random.Random(plan['seed'])
    maxima = []
    for _ in range(plan['trials']):
        shuffled = [word.copy() for word in words]
        for word in shuffled:
            rng.shuffle(word)
        peak = None
        for lag in plan['lags']:
            matrix, _ = pair_matrix(shuffled, lag)
            candidate = best(scan(matrix, expected[lag], lag))
            if peak is None or candidate[0] > peak[0]:
                peak = candidate
        maxima.append(peak[0])
    exceedances = sum(x >= selected[0] for x in maxima)
    supplied_exceedances = sum(x >= supplied[0] for x in maxima)
    sorted_maxima = sorted(maxima)
    p = (exceedances + 1) / (plan['trials'] + 1)
    return {
        'schema': 'liberpedia-affine-all-lags-result-v1', 'plan_sha256': plan_hash,
        'word_count': len(words), 'rune_count': sum(map(len, words)),
        'opportunities_by_lag': opportunities, 'candidate_count': len(rows),
        'selected': describe(selected), 'supplied_lag_six_rule': describe(supplied),
        'supplied_rule_against_full_search': {'exceedances': supplied_exceedances,
                                              'tail_plus_one': (supplied_exceedances + 1) / (plan['trials'] + 1)},
        'selected_by_lag': by_lag,
        'selection_null': {'trials': plan['trials'], 'seed': plan['seed'],
                           'maxima': [round(x, 6) for x in maxima],
                           'median': round(sorted_maxima[len(maxima)//2], 6),
                           'central_95': [round(sorted_maxima[24], 6), round(sorted_maxima[974], 6)],
                           'exceedances': exceedances, 'p_plus_one': p,
                           'below_declared_threshold': p < plan['threshold']},
        'interpretation_limit': 'Adjusts 12 lags and 841 affine maps under one word rule, not earlier choices of segmentation or model family, and does not identify an encryption process.'
    }


def figure(result):
    values = result['selection_null']['maxima']
    observed = result['selected']['score']
    supplied = result['supplied_lag_six_rule']['score']
    low = min(min(values), observed, 0)
    high = max(max(values), observed) * 1.05
    bins = [0] * 24
    for value in values:
        bins[min(23, int((value-low)/(high-low)*24))] += 1
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 290" role="img" aria-labelledby="t d">',
             '<title id="t">Full affine search compared with shuffled words</title>',
             f'<desc id="d">Observed top score {observed:.2f}; {result["selection_null"]["exceedances"]} of 999 shuffled searches reached it.</desc>',
             '<rect width="640" height="290" fill="#fff"/>',
             '<g font-family="system-ui,sans-serif" fill="#26343c">',
             '<text x="28" y="30" font-size="18" font-weight="600">The complete search, repeated on shuffled words</text>',
             '<text x="28" y="52" font-size="12">12 rune distances × 841 rules · 999 shuffled-word searches</text>']
    for i, count in enumerate(bins):
        height = 165 * count / max(bins)
        parts.append(f'<rect x="{44+i*22}" y="{230-height:.1f}" width="19" height="{height:.1f}" fill="#9eabb3"/>')
    marker = 44 + (observed-low)/(high-low)*528
    supplied_marker = 44 + (supplied-low)/(high-low)*528
    parts += [f'<line x1="{marker:.1f}" y1="70" x2="{marker:.1f}" y2="233" stroke="#285e78" stroke-width="3"/>',
              f'<line x1="{supplied_marker:.1f}" y1="112" x2="{supplied_marker:.1f}" y2="233" stroke="#5e737e" stroke-width="2" stroke-dasharray="5 4"/>',
              f'<text x="{min(marker+6,510):.1f}" y="83" font-size="12" font-weight="700" fill="#285e78">Strongest: {observed:.2f}</text>',
              f'<text x="{min(supplied_marker+6,480):.1f}" y="108" font-size="12" fill="#4e6672">Lag-six claim: {supplied:.2f}</text>',
              '<line x1="44" y1="230" x2="572" y2="230" stroke="#60727c"/>',
              f'<text x="44" y="250" font-size="12">{low:.1f}</text>',
              f'<text x="540" y="250" font-size="12">{high:.1f}</text>',
              '<text x="44" y="274" font-size="12">Maximum standardized excess under each complete search</text>',
              '</g></svg>']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    svg = figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload, encoding='utf-8', newline='\n')
        (HERE/'selection-null.svg').write_text(svg, encoding='utf-8', newline='\n')
    if args.check:
        if payload != (HERE/'results.json').read_text(encoding='utf-8') or svg != (HERE/'selection-null.svg').read_text(encoding='utf-8'):
            raise SystemExit('Saved result differs from recomputation')
        print('PASS full lag-and-map selection reproduces')
    print(f"Selected {result['selected']}; {result['selection_null']['exceedances']} / {result['selection_null']['trials']} controls reached it")


if __name__ == '__main__':
    main()
