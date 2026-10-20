"""Count equal rune pairs at specified distances within one archived page.

Python standard library only. No wraparound, decoding, or significance test.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

from rune_ngrams import indexed_runes

ROOT = Path(__file__).resolve().parents[1]


def lag_counts(symbols, max_lag):
    n = len(symbols)
    if isinstance(max_lag, bool) or not isinstance(max_lag, int) or not 1 <= max_lag < n:
        raise ValueError('Maximum lag must be an integer from 1 through rune_count - 1')
    return [{'lag': lag, 'matching_pairs': sum(symbols[i] == symbols[i + lag] for i in range(n - lag)),
             'compared_pairs': n - lag} for lag in range(1, max_lag + 1)]


def report(page_id, max_lag):
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    page = next((p for p in index['pages'] if p['id'] == page_id), None)
    if page is None:
        raise ValueError('Unknown page ID; include the release, for example lp2-31')
    source = ROOT / 'text' / (page_id + '.txt')
    raw = source.read_bytes()
    text = raw.decode('utf-8')
    alphabet = [entry['rune'] for entry in index['alphabet']]
    if len(alphabet) != 29 or len(set(alphabet)) != 29:
        raise ValueError('Expected 29 distinct runes')
    unknown = {c for c in text if '\u16a0' <= c <= '\u16ff'} - set(alphabet)
    if unknown:
        raise ValueError('Unknown runes in transcription: ' + ascii(unknown))
    symbols, _ = indexed_runes(text, {rune: i for i, rune in enumerate(alphabet)})
    if len(symbols) != page['rune_count']:
        raise ValueError('Rune count disagrees with page index')
    rows = lag_counts(symbols, max_lag)
    n = len(symbols)
    counts = Counter(symbols)
    expectation = Fraction(sum(c * (c - 1) for c in counts.values()), n * (n - 1))
    for row in rows:
        row['rate_fraction'] = str(Fraction(row['matching_pairs'], row['compared_pairs']))
        row['rate'] = row['matching_pairs'] / row['compared_pairs']
    return {
        'schema': 'liberpedia-rune-lag-matches-v1', 'page': page_id,
        'source': source.relative_to(ROOT).as_posix(), 'source_sha256': hashlib.sha256(raw).hexdigest(),
        'alphabet': alphabet,
        'alphabet_sha256': hashlib.sha256(''.join(alphabet).encode('utf-8')).hexdigest(),
        'alphabet_hash_encoding': 'UTF-8 concatenation of the ordered runes, without separators',
        'scope': 'Archived runes including headings; non-runes removed. Pairs may cross word, line, and paragraph boundaries, never pages. No circular wraparound.',
        'counting': 'At lag d, compare x[i] with x[i+d] for i=0 through n-d-1. Count each forward pair once.',
        'rune_count': n, 'max_lag': max_lag, 'rows': rows,
        'shuffle_expected_rate_fraction': str(expectation),
        'shuffle_model': 'Uniform random rearrangement preserving these symbol counts. This is the expected equality rate at each fixed lag, not a p-value or confidence interval.',
        'interpretation': 'Descriptive counts; a peak is not an established period, key length, or decryption.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('page', type=str.lower)
    parser.add_argument('--max-lag', type=int, default=20)
    parser.add_argument('--output', type=Path, help='Save UTF-8 JSON without overwriting')
    args = parser.parse_args()
    try:
        result = json.dumps(report(args.page, args.max_lag), ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8', newline='') as out:
                out.write(result)
            print('Saved report:', args.output)
        else:
            print(result, end='')
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', newline='')
    main()
