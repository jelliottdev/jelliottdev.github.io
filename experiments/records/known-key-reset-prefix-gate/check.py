"""Independent positional/equation check; no reset decoding of manuscript targets."""
import bisect
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan_bytes = (HERE / 'plan.json').read_bytes()
plan = json.loads(plan_bytes)
result = json.loads((HERE / 'results.json').read_bytes())
assert result['plan_sha256'] == hashlib.sha256(plan_bytes).hexdigest()
for dependency in plan['inputs']:
    assert hashlib.sha256((ROOT / dependency['path']).read_bytes()).hexdigest() == dependency['sha256']
parent = json.loads((ROOT / plan['parent_results']).read_bytes())
parent_plan_bytes = (ROOT / plan['parent_plan']).read_bytes()
assert parent['plan_sha256'] == hashlib.sha256(parent_plan_bytes).hexdigest()
parent_plan = json.loads(parent_plan_bytes)
key = next(row['indices'] for row in parent_plan['keys'] if row['id'] == 'second-koan')
opening = next(row for row in parent_plan['openings'] if row['id'] == 'warning')
trace = list(csv.DictReader(io.StringIO((ROOT / opening['source']).read_text(encoding='utf-8'))))
assert hashlib.sha256((ROOT / opening['source']).read_bytes()).hexdigest() == opening['sha256']
assert [int(row['output_index']) for row in trace][:12] == opening['indices'] == plan['opening']
assert key == plan['key']
alphabet = [row['rune'] for row in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']]
assert alphabet == parent['alphabet']
lookup = dict(zip(alphabet, range(29)))


def audit(text):
    positions = [i for i, char in enumerate(text) if char in lookup]
    baseline = [(lookup[text[position]] - key[j % len(key)]) % 29 for j, position in enumerate(positions)]
    differences = [j for j, (a, b) in enumerate(zip(baseline, plan['opening'])) if a != b]
    first = differences[0] if differences else None
    boundaries, excluded = {}, {}
    for mode in ('word', 'line'):
        separators = [i for i, char in enumerate(text) if positions and i > positions[0]
                      and char not in lookup and (mode == 'word' or char in '\r\n')]
        character = separators[0] if separators else None
        boundary = {'character_offset': character, 'rune_offset': bisect.bisect_left(positions, character)} if character is not None else None
        boundaries[mode] = boundary
        # A strict comparison is essential: a mismatch AT the first reset can change.
        excluded[mode] = first is not None and (boundary is None or first < boundary['rune_offset'])
    return baseline, {'rune_count': len(positions), 'baseline_prefix': baseline[:12],
                      'first_mismatch_zero_based': first, 'first_resets': boundaries, 'excluded': excluded}


rows, empty = [], []
for page_id in plan['pages']:
    page = json.loads((ROOT / 'data/pages' / (page_id + '.json')).read_bytes())
    raw = (ROOT / 'text' / (page_id + '.txt')).read_bytes()
    assert page['raw'] == raw.decode('utf-8') and page['id'] == page_id
    baseline, evidence = audit(page['raw'])
    saved = [row for row in parent['cases'] if (row['page'], row['key'], row['phase'], row['sign']) == (page_id, 'second-koan', 0, -1)]
    assert len(saved) == 1 and saved[0]['output_indices'] == baseline
    assert next(row['sha256'] for row in parent['inputs'] if row['path'] == 'text/' + page_id + '.txt') == hashlib.sha256(raw).hexdigest()
    if not baseline:
        empty.append(page_id)
    else:
        rows.append({'page': page_id, **evidence})
assert rows == result['pages'] and empty == result['empty_pages'] == ['lp2-50']
assert len(rows) == result['baseline_arrays_verified'] == 55
assert sum(row['rune_count'] for row in rows) == result['baseline_runes_verified'] == 12956
for mode, expected_count in [('word', 54), ('line', 55)]:
    excluded = [row['page'] for row in rows if row['excluded'][mode]]
    eligible = [row['page'] for row in rows if not row['excluded'][mode]]
    assert result['counts'][mode] == {'excluded_pages': excluded, 'not_excluded_pages': eligible}
    assert len(excluded) == expected_count
assert result['counts']['word']['not_excluded_pages'] == ['lp2-54']
assert result['counts']['line']['not_excluded_pages'] == []
assert len(result['synthetic_controls']) == 4
for control in result['synthetic_controls']:
    text, mode = control['ciphertext'], control['mode']
    _, evidence = audit(text)
    assert evidence == control['audit']
    positions = [i for i, char in enumerate(text) if char in lookup]
    separators = [i for i, char in enumerate(text) if char not in lookup and (mode == 'word' or char in '\r\n')]
    decoded = []
    for position in positions:
        last_separator = max((i for i in separators if i < position), default=-1)
        local_ordinal = bisect.bisect_left(positions, position) - bisect.bisect_right(positions, last_separator)
        decoded.append((lookup[text[position]] - key[local_ordinal % len(key)]) % 29)
    assert decoded == control['reset_output_indices']
    positive = control['kind'] == 'positive-after-boundary'
    assert (decoded == plan['opening']) == positive
    assert evidence['excluded'][mode] == (not positive)
    assert evidence['first_mismatch_zero_based'] == (1 if positive else 0)
    assert evidence['first_resets'][mode]['rune_offset'] == 1
assert result['new_reset_target_decodes'] == 0
print('PASS: independent equations verify all55 baseline arrays/12956 runes,54word/55line exclusions, LP2-54 survivor and4 strict-boundary controls. No reset target decoded.')
