"""Audit a proposed lag-six affine rune relation under declared word boundaries."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MOD = 29
LAG = 6
TARGET = (27, 24)  # -2 modulo 29, intercept 24
TRIALS = 2000
SEED = 330106


def load():
    source = (ROOT / 'data/index.json').read_bytes()
    alphabet = json.loads(source)['alphabet']
    lookup = {entry['rune']: i for i, entry in enumerate(alphabet)}
    assert len(lookup) == MOD
    hashes = {'data/index.json': hashlib.sha256(source).hexdigest()}
    pages = []
    for number in range(56):
        path = f'text/lp2-{number:02d}.txt'
        raw = (ROOT / path).read_bytes()
        text = raw.decode('utf-8')
        unknown = {c for c in text if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unmapped runes in {path}: {unknown!r}')
        # Hyphens and periods mark gaps. Slashes and newlines are layout marks;
        # a word may wrap across them. Preserve each page as its own scope.
        words = [[lookup[c] for c in piece if c in lookup]
                 for piece in re.split(r'[-.]', text)]
        pages.append([word for word in words if word])
        count = sum(map(len, pages[-1]))
        expected = next(p['rune_count'] for p in json.loads(source)['pages']
                        if p['id'] == f'lp2-{number:02d}')
        assert count == expected, path
        hashes[path] = hashlib.sha256(raw).hexdigest()
    return pages, hashes


def pair_matrix(words, lag):
    matrix = [[0] * MOD for _ in range(MOD)]
    opportunities = 0
    for word in words:
        for left, right in zip(word, word[lag:]):
            matrix[left][right] += 1
            opportunities += 1
    return matrix, opportunities


def affine_counts(matrix):
    return [[sum(matrix[c][(a*c+b) % MOD] for c in range(MOD))
             for b in range(MOD)] for a in range(MOD)]


def exact_word_shuffle_mean(words, a, b, lag):
    mean = 0.0
    for word in words:
        n = len(word)
        if n <= lag:
            continue
        counts = Counter(word)
        ordered = sum(counts[c] * (counts.get((a*c+b) % MOD, 0) -
                                 (c == (a*c+b) % MOD)) for c in counts)
        mean += (n-lag) * ordered / (n*(n-1))
    return mean


def summarize(values, observed):
    sorted_values = sorted(values)
    return {'mean': sum(values)/len(values),
            'central_95': [sorted_values[int(.025*len(values))],
                           sorted_values[int(.975*len(values))-1]],
            'at_least_observed': sum(x >= observed for x in values),
            'trials': len(values)}


def report():
    pages, hashes = load()
    words = [w for page in pages for w in page]
    lag_rows = []
    for lag in range(1, 13):
        matrix, opportunities = pair_matrix(words, lag)
        lag_rows.append({'lag': lag, 'opportunities': opportunities,
                         'target_matches': affine_counts(matrix)[TARGET[0]][TARGET[1]],
                         'uniform_expected': opportunities/MOD})
    matrix, opportunities = pair_matrix(words, LAG)
    grid = affine_counts(matrix)
    observed = grid[TARGET[0]][TARGET[1]]
    ranking = sorted(((grid[a][b], a, b) for a in range(MOD) for b in range(MOD)),
                     reverse=True)
    page_counts = []
    crossing = {'opportunities': 0, 'matches': 0}
    for number, page in enumerate(pages):
        page_matrix, page_opportunities = pair_matrix(page, LAG)
        page_matches = affine_counts(page_matrix)[TARGET[0]][TARGET[1]]
        page_counts.append({'page': f'lp2-{number:02d}',
                            'opportunities': page_opportunities,
                            'matches': page_matches})
        stream = [(rune, word_number) for word_number, word in enumerate(page)
                  for rune in word]
        for (left, left_word), (right, right_word) in zip(stream, stream[LAG:]):
            if left_word == right_word:
                continue
            crossing['opportunities'] += 1
            crossing['matches'] += right == (TARGET[0]*left+TARGET[1]) % MOD
    rng = random.Random(SEED)
    target_trials, max_trials = [], []
    for _ in range(TRIALS):
        shuffled = [word.copy() for word in words]
        for word in shuffled:
            rng.shuffle(word)
        trial_matrix, _ = pair_matrix(shuffled, LAG)
        trial_grid = affine_counts(trial_matrix)
        target_trials.append(trial_grid[TARGET[0]][TARGET[1]])
        max_trials.append(max(max(row) for row in trial_grid))
    return {
        'schema': 'liberpedia-word-internal-affine-lags-v1',
        'input_sha256': hashes,
        'scope': 'LP2-00–55; archived 29-rune order; headings included; hyphen and period split words; slash and newline are layout and do not split words; no cross-page pairs.',
        'claim': {'lag': LAG, 'a': TARGET[0], 'b': TARGET[1],
                  'equation': "c' = 24 - 2c (mod 29)"},
        'word_count': len(words), 'rune_count': sum(map(len, words)),
        'lag_profile': lag_rows,
        'target': {'opportunities': opportunities, 'matches': observed,
                   'uniform_expected': opportunities/MOD,
                   'exact_word_shuffle_expected': exact_word_shuffle_mean(words, *TARGET, LAG),
                   'word_shuffle': summarize(target_trials, observed)},
        'crossing_word_gaps': crossing,
        'page_counts': page_counts,
        'affine_family': {'candidate_count': MOD*MOD,
                          'counts_by_a_b': grid,
                          'word_shuffle_expected_by_a_b': [
                              [round(exact_word_shuffle_mean(words, a, b, LAG), 6)
                               for b in range(MOD)] for a in range(MOD)],
                          'target_rank': 1 + sum(count > observed for count, _, _ in ranking),
                          'largest_observed': [{'matches': count, 'a': a, 'b': b}
                                               for count, a, b in ranking[:10]],
                          'shuffle_maximum': summarize(max_trials, observed)},
        'reference': {'trials': TRIALS, 'seed': SEED,
                      'model': 'Shuffle rune order independently inside each visible word, keeping each word length and rune multiset. For the family comparison, score all 841 affine maps at lag six and retain each shuffle’s maximum.',
                      'caution': 'The formula and lag came from a supplied exploratory claim. A lag-six family maximum only adjusts the 841 affine maps at this lag, not all lags, segmentation choices, or other searched models.'}
    }


def figure(data):
    target = data['target']
    family = data['affine_family']['shuffle_maximum']
    values = [
        ('Observed relation', target['matches'], '#255f79'),
        ('Word-shuffle mean', target['word_shuffle']['mean'], '#657c88'),
        ('Best-map shuffle mean', family['mean'], '#8b96a0'),
    ]
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 270" role="img" aria-labelledby="title description">',
             '<title id="title">Lag-six affine matches within LP2 words</title>',
             '<desc id="description">The observed formula has 77 matches. Word shuffles average 44.6 for that formula. The best of all 841 affine formulas in each shuffle averages 65.9.</desc>',
             '<rect width="640" height="270" fill="#fff"/>',
             '<g font-family="system-ui,sans-serif" fill="#27343c">',
             '<text x="18" y="27" font-size="18" font-weight="600">Matches at lag six</text>',
             '<text x="18" y="48" font-size="12">LP2-00–55 · word-internal pairs · 2,000 within-word shuffles</text>']
    for i, (label, value, color) in enumerate(values):
        y = 85 + i*51
        lines += [f'<text x="18" y="{y}" font-size="13">{label}</text>',
                  f'<rect x="222" y="{y-15}" width="{value/80*332:.1f}" height="20" fill="{color}"/>',
                  f'<text x="{min(566, 228+value/80*332):.1f}" y="{y}" font-size="13">{value:.1f}</text>']
    lines += ['<text x="18" y="249" font-size="12">The best-map comparison adjusts 841 formulas at lag six; it does not adjust other lags or word rules.</text>',
              '</g></svg>']
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    visual = figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload, encoding='utf-8', newline='\n')
        (HERE/'comparison.svg').write_text(visual, encoding='utf-8', newline='\n')
    if args.check:
        assert payload == (HERE/'results.json').read_text(encoding='utf-8')
        assert visual == (HERE/'comparison.svg').read_text(encoding='utf-8')
        print('PASS affine-lag audit')
    print(f"{result['target']['matches']} / {result['target']['opportunities']} target matches; "
          f"rank {result['affine_family']['target_rank']} / {result['affine_family']['candidate_count']} affine maps")


if __name__ == '__main__':
    main()
