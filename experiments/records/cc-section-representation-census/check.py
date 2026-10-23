"""Independently count rune streams from per-page JSON and verify the saved census."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
KEYS = ('runes', 'prime_digits', 'index_0_digits', 'index_1_digits')


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    lookup = {row['rune']: (n, row['prime']) for n, row in enumerate(index['alphabet'])}
    page_streams = []
    for n in range(40):
        page = json.loads((ROOT / f'data/pages/lp2-{n:02}.json').read_text(encoding='utf-8'))
        from_json = tuple(c for c in page['raw'] if c in lookup)
        from_text = tuple(c for c in (ROOT / f'text/lp2-{n:02}.txt').read_text(encoding='utf-8') if c in lookup)
        assert from_json == from_text, f'Page {n:02} raw and text disagree'
        assert len(from_json) == page['rune_count']
        page_streams.append(from_json)
    assert len(page_streams) == 40

    def lengths(runes):
        positions = [lookup[c][0] for c in runes]
        primes = [lookup[c][1] for c in runes]
        return {'runes': len(runes),
                'prime_digits': len(''.join(str(v) for v in primes)),
                'index_0_digits': len(''.join(str(v) for v in positions)),
                'index_1_digits': len(''.join(str(v + 1) for v in positions))}

    all_intervals = {}
    for first in range(40):
        stream = ()
        for last in range(first, 40):
            stream += page_streams[last]
            all_intervals[first, last] = lengths(stream)
    assert len(all_intervals) == result['interval_count'] == 820

    for row in result['listed_groups']:
        assert all_intervals[row['first'], row['last']] == {key: row[key] for key in KEYS}
    for key, entry in result['perfect_square_intervals'].items():
        check = [{'first': a, 'last': b, 'length': values[key], 'side': math.isqrt(values[key])}
                 for (a, b), values in all_intervals.items()
                 if values[key] > 0 and math.isqrt(values[key]) ** 2 == values[key]]
        assert check == entry['intervals'] and len(check) == entry['count']
    for entry in result['target_length_recurrence']:
        check = [{'first': a, 'last': b} for (a, b), values in all_intervals.items()
                 if values[entry['representation']] == entry['length']]
        assert check == entry['intervals'] and len(check) == entry['interval_count']

    headerless = (ROOT / 'text/lp2-15.txt').read_text(encoding='utf-8').partition('\n')[2]
    assert lengths(tuple(c for c in headerless if c in lookup))['prime_digits'] == 289
    assert result['conditional_claims'] == {
        'branches_index_1_digits': 2915, 'after_one_extra_printed_digit': 2916,
        'mayfly_runes': 1021, 'after_removing_16_hypothesized_runes': 1005}
    for rel, expected in result['sources_sha256'].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected
    print('PASS: independent page-JSON streams, 820 intervals, four representations and conditional arithmetic')


if __name__ == '__main__':
    main()
