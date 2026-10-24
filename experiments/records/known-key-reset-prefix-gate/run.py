"""Audit saved uninterrupted outputs; never decode reset variants on target pages."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda value: hashlib.sha256(value).hexdigest()


def first_reset(text, lookup, mode):
    count = 0
    for position, char in enumerate(text):
        if char in lookup:
            count += 1
        elif count and (mode == 'word' or char in '\r\n'):
            return {'rune_offset': count, 'character_offset': position}
    return None


def assess(text, lookup, baseline, opening):
    mismatch = next((j for j in range(min(len(opening), len(baseline)))
                     if baseline[j] != opening[j]), None)
    boundaries = {mode: first_reset(text, lookup, mode) for mode in ('word', 'line')}
    excluded = {mode: mismatch is not None and (boundary is None or mismatch < boundary['rune_offset'])
                for mode, boundary in boundaries.items()}
    return {'rune_count': len(baseline), 'baseline_prefix': baseline[:len(opening)],
            'first_mismatch_zero_based': mismatch, 'first_resets': boundaries, 'excluded': excluded}


def synthetic_controls(alphabet, key, opening):
    lookup = {char: i for i, char in enumerate(alphabet)}
    cases = []
    for mode, separator in [('word', ' '), ('line', '\n')]:
        # The first reset lies between the first and second known runes.
        plain = alphabet[opening[0]] + separator + ''.join(alphabet[v] for v in opening[1:])
        cipher, position = [], 0
        for char in plain:
            if char in lookup:
                cipher.append(alphabet[(lookup[char] + key[position % len(key)]) % 29])
                position += 1
            else:
                cipher.append(char)
                if mode == 'word' or char in '\r\n':
                    position = 0
        for kind in ('positive-after-boundary', 'negative-before-boundary'):
            text = ''.join(cipher)
            if kind.startswith('negative'):
                text = alphabet[(lookup[text[0]] + 1) % 29] + text[1:]
            values = [lookup[ch] for ch in text if ch in lookup]
            baseline = [(v - key[j % len(key)]) % 29 for j, v in enumerate(values)]
            decoded, position = [], 0
            for char in text:
                if char in lookup:
                    decoded.append((lookup[char] - key[position % len(key)]) % 29)
                    position += 1
                elif mode == 'word' or char in '\r\n':
                    position = 0
            audit = assess(text, lookup, baseline, opening)
            assert audit['excluded'][mode] == kind.startswith('negative')
            assert (decoded == opening) == kind.startswith('positive')
            cases.append({'mode': mode, 'kind': kind, 'ciphertext': text,
                          'reset_output_indices': decoded, 'audit': audit})
    return cases


def run():
    raw_plan = (HERE / 'plan.json').read_bytes()
    plan = json.loads(raw_plan)
    for item in plan['inputs']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    parent = json.loads((ROOT / plan['parent_results']).read_bytes())
    parent_plan_bytes = (ROOT / plan['parent_plan']).read_bytes()
    parent_plan = json.loads(parent_plan_bytes)
    assert parent['plan_sha256'] == sha(parent_plan_bytes)
    alphabet = [row['rune'] for row in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']]
    assert parent['alphabet'] == alphabet and len(alphabet) == len(set(alphabet)) == 29
    lookup = {char: i for i, char in enumerate(alphabet)}
    key = next(k['indices'] for k in parent_plan['keys'] if k['id'] == 'second-koan')
    opening = next(o['indices'] for o in parent_plan['openings'] if o['id'] == 'warning')
    assert key == plan['key'] and opening == plan['opening']
    assert len(parent['cases']) == parent['case_count'] == 2352
    rows, empty = [], []
    for page_id in plan['pages']:
        page = json.loads((ROOT / 'data/pages' / (page_id + '.json')).read_bytes())
        text_bytes = (ROOT / 'text' / (page_id + '.txt')).read_bytes()
        assert page['id'] == page_id and page['raw'] == text_bytes.decode('utf-8')
        assert next(i['sha256'] for i in parent['inputs'] if i['path'] == 'text/' + page_id + '.txt') == sha(text_bytes)
        values = [lookup[ch] for ch in page['raw'] if ch in lookup]
        saved = [c for c in parent['cases'] if (c['page'], c['key'], c['phase'], c['sign']) == (page_id, 'second-koan', 0, -1)]
        assert len(saved) == 1
        baseline = [(value - key[j % len(key)]) % 29 for j, value in enumerate(values)]
        assert baseline == saved[0]['output_indices'], page_id
        if not values:
            empty.append(page_id)
            continue
        rows.append({'page': page_id, **assess(page['raw'], lookup, baseline, opening)})
    counts = {mode: {'excluded_pages': [r['page'] for r in rows if r['excluded'][mode]],
                     'not_excluded_pages': [r['page'] for r in rows if not r['excluded'][mode]]}
              for mode in ('word', 'line')}
    return {'schema': 'liberpedia-reset-prefix-gate-v1', 'plan_sha256': sha(raw_plan),
            'baseline_arrays_verified': len(rows), 'baseline_runes_verified': sum(r['rune_count'] for r in rows),
            'empty_pages': empty, 'counts': counts, 'pages': rows,
            'synthetic_controls': synthetic_controls(alphabet, key, opening),
            'new_reset_target_decodes': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_bytes()), 'Saved gate results differ'
        print('PASS: all saved baseline arrays, gates and synthetic controls reproduce; no reset targets decoded.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
