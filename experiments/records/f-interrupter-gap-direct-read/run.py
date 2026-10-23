"""Test four literal GP interpretations of every consecutive LP2 F gap."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pages():
    index_raw = (ROOT / 'data/index.json').read_bytes()
    alphabet = json.loads(index_raw)['alphabet']
    lookup = {row['rune']: row for row in alphabet}
    assert len(lookup) == 29 and alphabet[0]['latin'] == 'F'
    pages, hashes = {}, {'data/index.json': sha(index_raw)}
    for n in range(56):
        page = f'lp2-{n:02}'
        rel = f'text/{page}.txt'
        raw = (ROOT / rel).read_bytes()
        text = raw.decode('utf-8')
        unknown = {c for c in text if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        assert not unknown, (page, unknown)
        runes = [c for c in text if c in lookup]
        assert len(runes) == next(entry['rune_count'] for entry in json.loads(index_raw)['pages'] if entry['id'] == page)
        pages[page] = runes
        hashes[rel] = sha(raw)
    return alphabet, pages, hashes


def f_points(pages, f_rune):
    points = []
    global_start = 0
    for page, runes in pages.items():
        for local, rune in enumerate(runes):
            if rune == f_rune:
                points.append({'ordinal': len(points) + 1, 'page': page,
                               'page_rune_index': local, 'global_rune_index': global_start + local})
        global_start += len(runes)
    return points, global_start


def gaps(points, boundary):
    output = []
    for left, right in zip(points, points[1:]):
        if boundary == 'within-page-only' and left['page'] != right['page']:
            continue
        distance = right['global_rune_index'] - left['global_rune_index']
        output.append({'ordinal': len(output) + 1, 'left_f_ordinal': left['ordinal'],
                       'right_f_ordinal': right['ordinal'], 'left_page': left['page'],
                       'right_page': right['page'], 'position_distance': distance,
                       'intervening_runes': distance - 1})
    return output


def map_gaps(gap_list, gap_key, map_key, alphabet):
    by_prime = {row['prime']: row['latin'] for row in alphabet}
    symbols, missing = [], []
    for item in gap_list:
        value = item[gap_key]
        if map_key == 'zero-based-index-0-to-28':
            symbol = alphabet[value]['latin'] if 0 <= value < len(alphabet) else None
        elif map_key == 'exact-GP-prime-value':
            symbol = by_prime.get(value)
        else:
            raise ValueError(map_key)
        symbols.append(symbol)
        if symbol is None:
            missing.append({'gap_ordinal': item['ordinal'], 'left_f_ordinal': item['left_f_ordinal'],
                            'right_f_ordinal': item['right_f_ordinal'], 'value': value})
    return {'gap_count': len(gap_list), 'mapped_count': len(gap_list)-len(missing),
            'unmapped_count': len(missing), 'symbols_in_order': symbols,
            'unmapped': missing, 'complete_direct_reading': ' '.join(symbols) if not missing else None}


def controls(alphabet):
    f = alphabet[0]['rune']
    u = alphabet[1]['rune']
    result = {}
    for name, distances, map_key in [
        ('gp-prime-distances', [2, 3, 5, 7, 11], 'exact-GP-prime-value'),
        ('gp-index-distances', [1, 2, 3, 4, 5], 'zero-based-index-0-to-28'),
    ]:
        positions = [0]
        for distance in distances:
            positions.append(positions[-1] + distance)
        runes = [u] * (positions[-1] + 1)
        for position in positions:
            runes[position] = f
        points, _ = f_points({'synthetic': runes}, f)
        observed = gaps(points, 'global-concatenated-pages')
        assert [g['position_distance'] for g in observed] == distances
        mapped = map_gaps(observed, 'position_distance', map_key, alphabet)
        assert mapped['unmapped_count'] == 0
        assert mapped['symbols_in_order'] == ([row['latin'] for row in alphabet[:5]] if name == 'gp-prime-distances'
                                             else [row['latin'] for row in alphabet[1:6]])
        result[name] = {'f_positions': positions, 'distances': distances,
                        'symbols': mapped['symbols_in_order']}
    outlier = map_gaps([{'ordinal': 1, 'left_f_ordinal': 1, 'right_f_ordinal': 2,
                         'position_distance': 200, 'intervening_runes': 199}],
                       'position_distance', 'exact-GP-prime-value', alphabet)
    assert outlier['unmapped_count'] == 1 and outlier['symbols_in_order'] == [None]
    result['unmapped-outlier'] = {'distance': 200, 'unmapped': True}
    return result


def build():
    plan_raw = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_raw)
    assert plan['schema'] == 'liberpedia-f-interrupter-gap-direct-read-plan-v1'
    alphabet, pages, hashes = read_pages()
    points, rune_count = f_points(pages, alphabet[0]['rune'])
    assert len(points) == 458 and rune_count == 12956
    all_gaps = {boundary: gaps(points, boundary) for boundary in plan['boundary_rules']}
    assert len(all_gaps['global-concatenated-pages']) == 457
    cases = []
    gap_names = {'position-distance': 'position_distance', 'intervening-rune-count': 'intervening_runes'}
    for boundary in plan['boundary_rules']:
        for gap_rule in plan['gap_rules']:
            for map_key in plan['value_maps']:
                cases.append({'boundary': boundary, 'gap_rule': gap_rule, 'value_map': map_key,
                              **map_gaps(all_gaps[boundary], gap_names[gap_rule], map_key, alphabet)})
    return {'schema': 'liberpedia-f-interrupter-gap-direct-read-results-v1',
            'plan_sha256': sha(plan_raw), 'sources_sha256': hashes,
            'runes': rune_count, 'f_count': len(points), 'f_positions': points,
            'gap_vectors': all_gaps, 'cases': cases,
            'complete_case_count': sum(case['complete_direct_reading'] is not None for case in cases),
            'synthetic_controls': controls(alphabet)}


if __name__ == '__main__':
    result = build()
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if sys.argv[1:] == ['--write']:
        (HERE / 'results.json').write_bytes(encoded)
    elif not sys.argv[1:] or sys.argv[1:] == ['--check']:
        assert (HERE / 'results.json').read_bytes() == encoded
    else:
        raise SystemExit('usage: run.py [--write|--check]')
    print(f"{result['f_count']} F positions; {len(result['gap_vectors']['global-concatenated-pages'])} global gaps; "
          f"{result['complete_case_count']} complete direct readings")
