"""Trace the reported 729/index arithmetic across LP2-00–02 without word editing."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_results():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    runes = plan['runes']
    assert len(runes) == len(plan['latin_labels']) == len(plan['prime_values']) == 29
    index = {r: i for i, r in enumerate(runes)}
    trace = []
    global_line = 0
    page_counts = []
    for page in range(3):
        name = f'text/lp2-{page:02d}.txt'
        dependency = plan['inputs'][page]
        assert dependency['path'] == name and digest(ROOT / name) == dependency['sha256']
        content = (ROOT / name).read_text(encoding='utf-8')
        page_line = 0
        start = len(trace)
        for line in content.splitlines():
            if not any(c in index for c in line):
                continue
            global_line += 1
            page_line += 1
            for char in line:
                if char not in index:
                    continue
                j = index[char]
                row = {'position': len(trace) + 1, 'page': f'lp2-{page:02d}',
                       'global_line': global_line, 'page_line': page_line,
                       'rune': char, 'prime_value': plan['prime_values'][j], 'index': j}
                if j == 0:
                    row['undefined'] = '729/0'
                else:
                    q, r = divmod(729, j)
                    direction = 1 if 2*r > j else -1 if 2*r < j else 0
                    base = q % 29
                    row.update({'quotient_floor': q, 'remainder': r,
                                'base_index': base, 'base_label': plan['latin_labels'][base],
                                'direction': direction})
                    for label, line_number in [('global', global_line), ('page', page_line)]:
                        raw = base + direction * line_number
                        row[label + '_raw_index'] = raw
                        row[label + '_wrapped_index'] = raw % 29
                        row[label + '_wrapped_label'] = plan['latin_labels'][raw % 29]
                trace.append(row)
        page_counts.append({'page': f'lp2-{page:02d}', 'rune_count': len(trace) - start,
                            'rune_rows': page_line})
    assert [p['rune_count'] for p in page_counts] == [262, 266, 201]
    assert len(trace) == 729 and global_line == 33
    first = trace[:8]
    assert ''.join(row['rune'] for row in first) == 'ᛋᚻᛖᚩᚷᛗᛡᚠ'
    assert [row['prime_value'] for row in first] == plan['source_first_word_claimed_values']
    assert [row['index'] for row in first] == [15, 8, 18, 3, 6, 19, 27, 0]
    nonzero = [row for row in trace if row['index']]
    return {
        'plan_sha256': digest(plan_path),
        'page_counts': page_counts,
        'total_runes': len(trace),
        'total_rune_rows': global_line,
        'zero_index_count': len(trace) - len(nonzero),
        'first_word_source_indices': plan['source_first_word_claimed_indices'],
        'first_word_canonical_indices': [row['index'] for row in first],
        'source_index_mismatch_positions': [i + 1 for i, row in enumerate(first)
                                            if row['index'] != plan['source_first_word_claimed_indices'][i]],
        'global_out_of_range_without_wrap': sum(not 0 <= row['global_raw_index'] < 29 for row in nonzero),
        'page_out_of_range_without_wrap': sum(not 0 <= row['page_raw_index'] < 29 for row in nonzero),
        'page_vs_global_wrapped_differences': sum(row['page_wrapped_index'] != row['global_wrapped_index'] for row in nonzero),
        'direction_counts': dict(sorted(Counter(str(row['direction']) for row in nonzero).items())),
        'trace': trace
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = make_results()
    path = HERE / 'results.json'
    if args.write:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Wrote', path)
    elif args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
        print('PASS: 729-rune index-inversion trace and both line conventions')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
