"""Compare ciphertext neighbors of hyphen and within-token LP2 doublets."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = 33012217
TRIALS = 10000
WITHIN = {'contiguous', 'row-wrap only', 'apostrophe/soft wrap'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chi_square(rows, selected):
    """Pearson association over raw neighbor labels, with missing as bin 29."""
    n = len(rows)
    h = len(selected)
    w = n - h
    assert h and w
    total = 0.0
    for field in ('before_index', 'after_index'):
        pooled = Counter((29 if row[field] is None else row[field]) for row in rows)
        hyphen = Counter((29 if rows[i][field] is None else rows[i][field]) for i in selected)
        for label, count in pooled.items():
            observed_h = hyphen[label]
            expected_h = h * count / n
            expected_w = w * count / n
            total += (observed_h - expected_h) ** 2 / expected_h
            total += ((count - observed_h) - expected_w) ** 2 / expected_w
    return total


def quantile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(fraction * len(ordered) + .999999) - 1))]


def describe(rows, group):
    selected = [row for row in rows if row['group'] == group]
    result = {'events': len(selected)}
    for side in ('before', 'after'):
        index = side + '_index'
        delta = side + '_difference'
        values = [row[index] for row in selected if row[index] is not None]
        changes = [row[delta] for row in selected if row[delta] is not None]
        assert len(values) == len(changes)
        result[side] = {
            'available': len(values),
            'missing': len(selected) - len(values),
            'rune_counts': [values.count(i) for i in range(29)],
            'distinct_runes': len(set(values)),
            'circular_distance_total': sum(min(d, 29 - d) for d in changes),
            'mean_circular_distance': sum(min(d, 29 - d) for d in changes) / len(changes)
                                     if changes else None,
        }
    return result


def compute():
    plan = json.loads((HERE / 'boundary-context-plan.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    context_report = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    context = context_report['observed']['events']
    boundaries = json.loads((ROOT / 'experiments/records/doublet-boundaries/results.json').read_text(encoding='utf-8'))['events']
    alphabet_rows = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    alphabet = [item['latin'] for item in alphabet_rows]
    lookup = {item['rune']: i for i, item in enumerate(alphabet_rows)}
    assert len(context) == len(boundaries) == 86 and len(alphabet) == 29
    by_position = {(event['page'], event['rune_index_zero_based'] + 1): event for event in boundaries}
    assert len(by_position) == 86
    rows = []
    streams = {}
    for event in context:
        key = event['page'], event['rune_index']
        boundary = by_position[key]
        symbol = event['ciphertext_index']
        before_delta = event['preceding_difference']
        after_delta = event['following_difference']
        assert before_delta != 0 and after_delta != 0
        before = None if before_delta is None else (symbol - before_delta) % 29
        after = None if after_delta is None else (symbol + after_delta) % 29
        if event['page'] not in streams:
            source_path = 'text/' + event['page'] + '.txt'
            file = ROOT / source_path
            assert sha(file) == context_report['input_sha256'][source_path]
            streams[event['page']] = [lookup[ch] for ch in file.read_text(encoding='utf-8') if ch in lookup]
        stream = streams[event['page']]
        pos = event['rune_index']
        assert stream[pos-1] == stream[pos] == symbol
        assert before == (stream[pos-2] if pos >= 2 else None)
        assert after == (stream[pos+1] if pos+1 < len(stream) else None)
        category = boundary['category']
        group = 'within-token' if category in WITHIN else ('hyphen' if category == 'hyphen' else 'other')
        rows.append({
            'page': event['page'], 'rune_index': event['rune_index'],
            'separator_category': category, 'group': group,
            'repeated_index': symbol, 'repeated_label': alphabet[symbol],
            'before_index': before, 'before_label': None if before is None else alphabet[before],
            'after_index': after, 'after_label': None if after is None else alphabet[after],
            'before_difference': before_delta, 'after_difference': after_delta,
        })
    assert Counter(row['group'] for row in rows) == {'hyphen': 22, 'within-token': 63, 'other': 1}
    eligible = [row for row in rows if row['group'] != 'other']
    observed = frozenset(i for i, row in enumerate(eligible) if row['group'] == 'hyphen')
    score = chi_square(eligible, observed)
    rng = random.Random(SEED)
    global_scores, page_scores = [], []
    by_page = defaultdict(list)
    for i, row in enumerate(eligible):
        by_page[row['page']].append(i)
    page_groups = [(indices, len(set(indices) & observed)) for indices in by_page.values()]
    movable_pages = sum(0 < k < len(indices) for indices, k in page_groups)
    movable_events = sum(len(indices) for indices, k in page_groups if 0 < k < len(indices))
    for _ in range(TRIALS):
        global_labels = frozenset(rng.sample(range(len(eligible)), len(observed)))
        global_scores.append(chi_square(eligible, global_labels))
        page_labels = frozenset(i for indices, k in page_groups for i in rng.sample(indices, k))
        page_scores.append(chi_square(eligible, page_labels))
    def reference(scores):
        at_least = sum(s >= score - 1e-12 for s in scores)
        return {'central_95': [quantile(scores, .025), quantile(scores, .975)],
                'at_least_observed': at_least,
                'inclusive_fraction': (at_least + 1) / (TRIALS + 1)}
    return {
        'schema': 'liberpedia-doublet-boundary-context-v1',
        'plan_sha256': sha(HERE / 'boundary-context-plan.json'),
        'scope': '85 of 86 LP2-00–55 doublets: 22 hyphen-crossing versus 63 within-token; one other-separator event shown separately.',
        'alphabet_labels': alphabet,
        'group_descriptions': {group: describe(rows, group) for group in ('hyphen', 'within-token', 'other')},
        'primary_statistic': {'name': 'sum of before and after raw-rune Pearson 2x30 association chi-squares',
                              'observed': score},
        'controls': {'seed': SEED, 'trials': TRIALS,
                     'global_label_permutation': reference(global_scores),
                     'within_page_label_permutation': reference(page_scores),
                     'within_page_movable_pages': movable_pages,
                     'within_page_movable_events': movable_events,
                     'limitations': 'Exploratory conditional label shuffles. The page-stratified control cannot move labels on one-event or single-category pages; neither control estimates a cipher likelihood.'},
        'events': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = json.dumps(compute(), indent=2, ensure_ascii=False) + '\n'
    path = HERE / 'boundary-context.json'
    if args.write:
        path.write_text(output, encoding='utf-8', newline='\n')
    else:
        assert output == path.read_text(encoding='utf-8')
    data = json.loads(output)
    print(data['primary_statistic'], data['controls'])


if __name__ == '__main__':
    main()
