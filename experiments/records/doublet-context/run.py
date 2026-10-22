"""Conditional context audit around LP2 equal-neighbor rune events."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SEED = 330122
TRIALS = 5000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    raw = (ROOT / 'data/index.json').read_bytes()
    alphabet = json.loads(raw)['alphabet']
    lookup = {row['rune']: i for i, row in enumerate(alphabet)}
    assert len(lookup) == 29 and alphabet[28]['latin'] == 'EA'
    hashes = {'data/index.json': sha(raw)}
    pages = []
    for number in range(56):
        path = f'text/lp2-{number:02d}.txt'
        raw = (ROOT / path).read_bytes()
        source = raw.decode('utf-8')
        unknown = set(c for c in source if '\u16a0' <= c <= '\u16ff') - lookup.keys()
        if unknown:
            raise ValueError(f'Unknown rune in {path}: {unknown!r}')
        pages.append([lookup[c] for c in source if c in lookup])
        hashes[path] = sha(raw)
    return alphabet, pages, hashes


def deltas(page):
    return [(right - left) % 29 for left, right in zip(page, page[1:])]


def reconstruct(start, changes):
    page = [start]
    for change in changes:
        page.append((page[-1] + change) % 29)
    return page


def measure(pages, labels):
    events = []
    symbols = Counter()
    before = Counter()
    after = Counter()
    missing_before = missing_after = neighboring_zero = 0
    for page_number, page in enumerate(pages):
        changes = deltas(page)
        for at, change in enumerate(changes):
            if change:
                continue
            symbol = page[at + 1]
            left = changes[at - 1] if at > 0 else None
            right = changes[at + 1] if at + 1 < len(changes) else None
            if left is None:
                missing_before += 1
            elif left == 0:
                neighboring_zero += 1
            else:
                before[left] += 1
            if right is None:
                missing_after += 1
            elif right == 0:
                neighboring_zero += 1
            else:
                after[right] += 1
            symbols[symbol] += 1
            events.append({'page': f'lp2-{page_number:02d}', 'rune_index': at + 1,
                           'ciphertext_index': symbol, 'ciphertext_label': labels[symbol],
                           'preceding_difference': left, 'following_difference': right})
    symbol_bins = [symbols[i] for i in range(29)]
    before_bins = [before[i] for i in range(1, 29)]
    after_bins = [after[i] for i in range(1, 29)]
    collision_pairs = sum(c * (c - 1) // 2 for c in symbol_bins)
    context_imbalance = sum((a - b) ** 2 / (a + b + 1) for a, b in zip(before_bins, after_bins))
    return {'events': events, 'symbol_counts': symbol_bins,
            'preceding_difference_counts': before_bins,
            'following_difference_counts': after_bins,
            'missing_preceding': missing_before, 'missing_following': missing_after,
            'neighboring_zero_exclusions': neighboring_zero,
            'collision_pairs': collision_pairs, 'context_imbalance': context_imbalance}


def nearest(values, proportion):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(proportion * len(ordered) + .999999) - 1))]


def ranks(values, observed):
    return {'central_95': [nearest(values, .025), nearest(values, .975)],
            'at_least_observed': sum(value >= observed for value in values),
            'at_most_observed': sum(value <= observed for value in values)}


def report():
    alphabet, pages, hashes = inputs()
    labels = [row['latin'] for row in alphabet]
    observed = measure(pages, labels)
    assert len(observed['events']) == 86
    assert sum(max(0, len(page) - 1) for page in pages) == 12901
    page_changes = [deltas(page) for page in pages]
    rng = random.Random(SEED)
    collisions, imbalances = [], []
    average_bins = [0] * 29
    positive_control = False
    for trial in range(TRIALS):
        synthetic = []
        for page, changes in zip(pages, page_changes):
            if not page:
                synthetic.append([])
                continue
            pool = [value for value in changes if value]
            rng.shuffle(pool)
            iterator = iter(pool)
            shuffled = [0 if value == 0 else next(iterator) for value in changes]
            synthetic.append(reconstruct(page[0], shuffled))
        if trial == 0:
            positive_control = all(
                [value == 0 for value in deltas(rebuilt)] == [value == 0 for value in original]
                and Counter(value for value in deltas(rebuilt) if value)
                == Counter(value for value in original if value)
                for rebuilt, original in zip(synthetic, page_changes))
            assert positive_control
        measured = measure(synthetic, labels)
        collisions.append(measured['collision_pairs'])
        imbalances.append(measured['context_imbalance'])
        for i, count in enumerate(measured['symbol_counts']):
            average_bins[i] += count
    return {'schema': 'liberpedia-doublet-context-v1',
            'plan_sha256': sha((HERE / 'plan.txt').read_bytes()),
            'input_sha256': hashes,
            'scope': 'Archived LP2-00--55, headings included; within-page 29-rune streams.',
            'model': 'Fix first ciphertext rune, zero-difference mask and nonzero difference multiset separately for each page; permute nonzero difference order.',
            'within_page_transitions': 12901,
            'observed': observed,
            'reference': {'trials': TRIALS, 'seed': SEED,
                          'collision_pairs': ranks(collisions, observed['collision_pairs']),
                          'context_imbalance': ranks(imbalances, observed['context_imbalance']),
                          'event_symbol_mean_counts': [value / TRIALS for value in average_bins],
                          'positive_control': positive_control,
                          'limits': 'Conditional exploratory rank, not a prospective p-value. The zero mask, page starts and per-page difference histograms are fixed.'}}


def chart(data):
    counts = data['observed']['symbol_counts']
    means = data['reference']['event_symbol_mean_counts']
    ceiling = max(max(counts), max(means)) + 2
    left, top, width, height = 60, 100, 870, 290
    y = lambda value: top + height * (1 - value / ceiling)
    bar = width / 29
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1010" height="490" viewBox="0 0 1010 490" role="img" aria-labelledby="title desc">',
             '<title id="title">Ciphertext symbols at 86 doublet positions</title>',
             '<desc id="desc">Counts for all 29 Gematria Primus indices, with conditional permutation means. These are ciphertext states, not proposed plaintext EA labels.</desc>',
             '<rect width="1010" height="490" fill="#fff"/>',
             '<text x="60" y="40" font-family="Arial,sans-serif" font-size="24" fill="#20242a">Symbols at the 86 doublets</text>',
             '<text x="60" y="68" font-family="Arial,sans-serif" font-size="15" fill="#5c626b">LP2-00–55 · within-page events · GP index 0–28</text>']
    for i, (count, mean) in enumerate(zip(counts, means)):
        x = left + i * bar + 2
        parts.append(f'<rect x="{x:.2f}" y="{y(count):.2f}" width="{bar-5:.2f}" height="{top+height-y(count):.2f}" fill="#315d76"/>')
        parts.append(f'<line x1="{x:.2f}" y1="{y(mean):.2f}" x2="{x+bar-5:.2f}" y2="{y(mean):.2f}" stroke="#a24136" stroke-width="2"/>')
        if i % 2 == 0 or i == 28:
            parts.append(f'<text x="{x+(bar-5)/2:.2f}" y="413" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#49545d">{i}</text>')
    parts += [f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="#64717b"/>',
              '<text x="60" y="450" font-family="Arial,sans-serif" font-size="14" fill="#20242a">Blue: observed event symbols. Red ticks: means of 5,000 within-page conditional permutations.</text>',
              '<text x="60" y="474" font-family="Arial,sans-serif" font-size="13" fill="#5c626b">Individual red ticks are descriptive; they are not per-symbol significance thresholds.</text>',
              '</svg>']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = report()
    output = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    image = chart(data).encode('utf-8')
    if args.write:
        (HERE / 'results.json').write_bytes(output)
        (HERE / 'context.svg').write_bytes(image)
    elif args.check:
        assert (HERE / 'results.json').read_bytes() == output
        assert (HERE / 'context.svg').read_bytes() == image
        print('PASS: fixed-mask context controls and chart reproduce')
    else:
        print(output.decode('utf-8'))


if __name__ == '__main__':
    main()
