"""Conditional nonzero-difference check for one EA-stalling key model."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SEED = 33012026
TRIALS = 2000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(fraction * len(ordered) + .999999) - 1))]


def read_inputs():
    index_raw = (ROOT / 'data/index.json').read_bytes()
    alphabet = json.loads(index_raw)['alphabet']
    lookup = {entry['rune']: number for number, entry in enumerate(alphabet)}
    assert len(lookup) == 29 and alphabet[28]['latin'] == 'EA'
    hashes = {'data/index.json': digest(index_raw)}
    streams = []
    for number in range(56):
        path = f'text/lp2-{number:02d}.txt'
        raw = (ROOT / path).read_bytes()
        source = raw.decode('utf-8')
        unknown = {c for c in source if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unknown rune in {path}: {unknown!r}')
        streams.append([lookup[c] for c in source if c in lookup])
        hashes[path] = digest(raw)
    return streams, hashes


def differences(streams):
    return [[(page[i] - page[i-1]) % 29 for i in range(1, len(page))]
            for page in streams]


def measures(pages):
    counts = Counter(value for page in pages for value in page if value)
    n = sum(counts.values())
    expected = n / 28
    chi_square = sum((counts[value] - expected) ** 2 / expected for value in range(1, 29))
    adjacent = [(left, right) for page in pages for left, right in zip(page, page[1:])
                if left and right]
    return {'nonzero_count': n,
            'nonzero_histogram': [counts[value] for value in range(1, 29)],
            'chi_square': chi_square,
            'adjacent_nonzero_pairs': len(adjacent),
            'adjacent_equal_nonzero': sum(left == right for left, right in adjacent),
            'adjacent_equal_expected': len(adjacent) / 28}


def simulate(masks, starts):
    rng = random.Random(SEED)
    chi_values, equal_values = [], []
    positive_control_passed = False
    for trial in range(TRIALS):
        synthetic = [[0 if is_zero else rng.randrange(1, 29) for is_zero in page]
                     for page in masks]
        if trial == 0:
            reconstructed = [[start] + [0] * len(page) for start, page in zip(starts, synthetic)]
            for cipher, page in zip(reconstructed, synthetic):
                for i, delta in enumerate(page, 1):
                    cipher[i] = (cipher[i-1] + delta) % 29
            positive_control_passed = differences(reconstructed) == synthetic
            assert positive_control_passed
        measured = measures(synthetic)
        chi_values.append(measured['chi_square'])
        equal_values.append(measured['adjacent_equal_nonzero'])
    return chi_values, equal_values, positive_control_passed


def report():
    streams, hashes = read_inputs()
    pages = differences(streams)
    observed = measures(pages)
    zeros = sum(value == 0 for page in pages for value in page)
    assert zeros == 86 and sum(map(len, pages)) == 12901
    masks = [[value == 0 for value in page] for page in pages]
    starts = [page[0] if page else 0 for page in streams]
    chi, equal, control = simulate(masks, starts)
    def ranks(values, value):
        return {'central_95': [percentile(values, .025), percentile(values, .975)],
                'at_least_observed': sum(x >= value for x in values),
                'at_most_observed': sum(x <= value for x in values)}
    return {'schema': 'liberpedia-ea-difference-independence-v1',
            'plan_sha256': digest((HERE / 'plan.txt').read_bytes()),
            'input_sha256': hashes,
            'scope': 'Archived LP2-00--55 runes including headings; within-page differences only.',
            'model': 'Conditional on the observed zero-difference mask, independent uniform draws from residues 1--28 at every other within-page transition.',
            'within_page_transitions': 12901, 'zero_differences': zeros,
            'observed': observed,
            'reference': {'trials': TRIALS, 'seed': SEED,
                          'chi_square': ranks(chi, observed['chi_square']),
                          'adjacent_equal_nonzero': ranks(equal, observed['adjacent_equal_nonzero']),
                          'synthetic_cipher_round_trip': control,
                          'selection_note': 'Exploratory diagnostics chosen after the doublet and difference-IoC observations; ranks are conditional and unadjusted for selection.'}}


def figure(result):
    values = result['observed']['nonzero_histogram']
    expected = result['observed']['nonzero_count'] / 28
    ceiling = max(values) + 35
    left, top, width, height = 72, 82, 750, 300
    y = lambda n: top + height * (1 - n / ceiling)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="510" viewBox="0 0 900 510" role="img" aria-labelledby="title desc">',
             '<title id="title">Nonzero ciphertext difference counts, residues 1 to 28</title>',
             '<desc id="desc">Twenty-eight bars compare observed nonzero differences with the equal-count reference implied by independent uniform nonzero keys. This conditional comparison does not identify a cipher.</desc>',
             '<rect width="900" height="510" fill="#fff"/>',
             '<text x="72" y="38" font-family="Arial,sans-serif" font-size="24" fill="#20242a">Nonzero differences</text>',
             '<text x="72" y="61" font-family="Arial,sans-serif" font-size="15" fill="#5c626b">LP2-00–55 · 12,815 nonzero within-page transitions</text>',
             f'<line x1="{left}" y1="{y(expected):.2f}" x2="{left+width}" y2="{y(expected):.2f}" stroke="#9c3034" stroke-width="2"/>',
             f'<text x="{left+width+8}" y="{y(expected)+5:.2f}" font-family="Arial,sans-serif" font-size="13" fill="#9c3034">{expected:.1f}</text>']
    bar_width = width / 28
    for i, value in enumerate(values):
        x = left + i * bar_width + 2
        parts.append(f'<rect x="{x:.2f}" y="{y(value):.2f}" width="{bar_width-4:.2f}" height="{top+height-y(value):.2f}" fill="#315d76"/>')
        if (i + 1) in (1, 4, 8, 12, 16, 20, 24, 28):
            parts.append(f'<text x="{x+bar_width/2-2:.2f}" y="406" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#49545d">{i+1}</text>')
    parts += [f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="#64717b"/>',
              '<text x="72" y="447" font-family="Arial,sans-serif" font-size="14" fill="#20242a">Blue: observed counts by difference residue. Red: equal-count reference.</text>',
              f'<text x="72" y="473" font-family="Arial,sans-serif" font-size="14" fill="#20242a">Adjacent equal nonzero differences: {result["observed"]["adjacent_equal_nonzero"]} of {result["observed"]["adjacent_nonzero_pairs"]} eligible pairs.</text>',
              '</svg>']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    chart = figure(result)
    if args.write:
        (HERE / 'results.json').write_bytes(output.encode('utf-8'))
        (HERE / 'differences.svg').write_bytes(chart.encode('utf-8'))
    elif args.check:
        assert (HERE / 'results.json').read_bytes() == output.encode('utf-8')
        assert (HERE / 'differences.svg').read_bytes() == chart.encode('utf-8')
        print('PASS: observed differences, conditional simulations, positive control and figure reproduce')
    else:
        print(output)


if __name__ == '__main__':
    main()
