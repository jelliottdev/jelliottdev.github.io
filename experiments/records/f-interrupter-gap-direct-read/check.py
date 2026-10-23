"""Independently reconstruct every F gap from per-page JSON and verify mapping."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    report = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    by_rune = {entry['rune']: entry for entry in alphabet}
    index_symbols = [entry['latin'] for entry in alphabet]
    prime_symbols = {entry['prime']: entry['latin'] for entry in alphabet}
    f = alphabet[0]['rune']
    length = 0
    points = []
    for n in range(56):
        page = f'lp2-{n:02}'
        original = json.loads((ROOT / f'data/pages/{page}.json').read_text(encoding='utf-8'))['raw']
        text = (ROOT / f'text/{page}.txt').read_text(encoding='utf-8')
        json_runes = [character for character in original if character in by_rune]
        text_runes = [character for character in text if character in by_rune]
        assert json_runes == text_runes
        for local in [i for i, value in enumerate(json_runes) if value == f]:
            points.append({'ordinal': len(points)+1, 'page': page,
                           'page_rune_index': local, 'global_rune_index': length+local})
        length += len(json_runes)
    assert points == report['f_positions'] and len(points) == report['f_count'] == 458
    assert length == report['runes'] == 12956
    for boundary, saved_gaps in report['gap_vectors'].items():
        expected = []
        for left, right in zip(points[:-1], points[1:]):
            if boundary == 'within-page-only' and left['page'] != right['page']:
                continue
            distance = right['global_rune_index']-left['global_rune_index']
            expected.append({'ordinal': len(expected)+1, 'left_f_ordinal': left['ordinal'],
                             'right_f_ordinal': right['ordinal'], 'left_page': left['page'],
                             'right_page': right['page'], 'position_distance': distance,
                             'intervening_runes': distance-1})
        assert expected == saved_gaps
    assert len(report['gap_vectors']['global-concatenated-pages']) == 457
    assert len(report['gap_vectors']['within-page-only']) == 403

    for case in report['cases']:
        gap_field = 'position_distance' if case['gap_rule'] == 'position-distance' else 'intervening_runes'
        symbols = []
        missing = []
        for gap in report['gap_vectors'][case['boundary']]:
            value = gap[gap_field]
            if case['value_map'] == 'zero-based-index-0-to-28':
                symbol = index_symbols[value] if value in range(29) else None
            else:
                assert case['value_map'] == 'exact-GP-prime-value'
                symbol = prime_symbols.get(value)
            symbols.append(symbol)
            if symbol is None:
                missing.append({'gap_ordinal': gap['ordinal'], 'left_f_ordinal': gap['left_f_ordinal'],
                                'right_f_ordinal': gap['right_f_ordinal'], 'value': value})
        assert symbols == case['symbols_in_order']
        assert missing == case['unmapped'] and len(missing) == case['unmapped_count']
        assert len(symbols) - len(missing) == case['mapped_count']
        assert case['complete_direct_reading'] == (' '.join(symbols) if not missing else None)
    assert report['complete_case_count'] == sum(case['unmapped_count'] == 0 for case in report['cases']) == 0

    controls = report['synthetic_controls']
    for name, values, table in [
        ('gp-prime-distances', [2, 3, 5, 7, 11], prime_symbols),
        ('gp-index-distances', [1, 2, 3, 4, 5], dict(enumerate(index_symbols))),
    ]:
        positions = [0]
        for v in values:
            positions.append(positions[-1]+v)
        synthetic = [alphabet[1]['rune']] * (positions[-1]+1)
        for p in positions:
            synthetic[p] = f
        recovered_positions = [i for i, value in enumerate(synthetic) if value == f]
        distances = [b-a for a, b in zip(recovered_positions, recovered_positions[1:])]
        assert distances == values and recovered_positions == controls[name]['f_positions']
        assert [table[v] for v in distances] == controls[name]['symbols']
    assert 200 not in prime_symbols and controls['unmapped-outlier']['unmapped']
    for rel, expected in report['sources_sha256'].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected
    print('PASS: 458 F positions, 457/403 gaps, eight complete mapping vectors and reconstructed controls')


if __name__ == '__main__':
    main()
