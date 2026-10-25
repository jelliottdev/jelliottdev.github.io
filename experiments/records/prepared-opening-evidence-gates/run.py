"""Reuse saved prefix evidence; never generate a complete new target decode."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from prefix_evidence_gate import inverse_affine_prefix, first_mismatch, reset_prefix_compatibility


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def controls():
    assert inverse_affine_prefix([24, 7, 24], 28, 28) == [4, 21, 4]
    assert first_mismatch([4, 21, 9], [4, 21, 4]) == 2
    assert first_mismatch([4, 21], [4, 21, 4]) is None
    assert reset_prefix_compatibility(1, 2)
    assert not reset_prefix_compatibility(1, 1)
    assert not reset_prefix_compatibility(2, 1)
    assert not reset_prefix_compatibility(None, 2)
    assert reset_prefix_compatibility(1, None)
    return {'inverse_affine_known_answer': True, 'truncated_prefix_not_excluded': True,
            'mismatch_before_reset_excluded': True, 'mismatch_at_reset_not_excluded': True,
            'mismatch_after_reset_not_excluded': True, 'unchanged_prefix_excluded': True}


def first_changed_reset(raw, lookup, mode):
    count = 0
    for offset, char in enumerate(raw):
        if char in lookup:
            count += 1
        elif count and ((mode == 'word' and char not in '-.') or (mode == 'line' and char in '\r\n')):
            return {'rune_offset': count, 'character_offset': offset}
    return None


def build():
    passed = controls()  # Known-answer and boundary counterexamples precede evidence inspection.
    raw_plan = (HERE / 'plan.json').read_bytes()
    plan = json.loads(raw_plan)
    for item in plan['inputs']:
        assert sha((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    for identity in plan['recipe_identities']:
        record = load(identity['path'])
        recipe = next(f for f in record['browser_followups'] if f['id'] == identity['id'])
        projection = {k: recipe[k] for k in ('id', 'title', 'card', 'inputs', 'control')}
        assert sha(canonical(projection)) == identity['sha256'], identity['id']
    alphabet = load('data/index.json')['alphabet']
    lookup = {row['rune']: n for n, row in enumerate(alphabet)}
    assert len(alphabet) == len(lookup) == plan['alphabet_size'] == 29
    with (ROOT / 'exports/readings/warning.csv').open(encoding='utf-8', newline='') as f:
        warning = [int(row['output_index']) for row in csv.DictReader(f) if row['output_index'].strip()][:24]
    assert len(warning) == 24 and warning[:3] == [24, 7, 24]
    inverse = inverse_affine_prefix(warning, 28, 28)
    cumulative = load('experiments/records/cumulative-autokey-literal/results.json')
    first_positions = {row['page']: row['cipher_index'] for row in cumulative['first_positions']}
    cases = load('experiments/suites/feedback-opening-census/cases.json')
    census = {row['id']: row for row in cases['cases']}
    manifest = load('experiments/suites/feedback-opening-census/manifest.json')
    summary = load('experiments/suites/feedback-opening-census/results.json')
    assert summary['cases_sha256'] == sha((ROOT / 'experiments/suites/feedback-opening-census/cases.json').read_bytes())
    assert summary['manifest_sha256'] == sha((ROOT / 'experiments/suites/feedback-opening-census/manifest.json').read_bytes())
    assert manifest['pages'] == plan['pages']
    frozen = {item['path']: item['sha256'] for item in plan['inputs']}
    for item in summary['input_sha256']:
        if item['path'] in frozen:
            assert item['sha256'] == frozen[item['path']], item['path']
    for page_id in plan['pages']:
        path = 'text/' + page_id + '.txt'
        assert next(i['sha256'] for i in summary['input_sha256'] if i['path'] == path) == frozen[path]
        assert cumulative['input_sha256'][path] == frozen[path]
    assert next(c['indices'] for c in manifest['cribs'] if c['id'] == 'warning') == warning[:12]
    for case_id in ('ciphertext-lag01-primer00-continuous', 'ciphertext-lag01-primer00-word-reset'):
        assert census[case_id]['max_prefix_length'] == 1 and not census[case_id]['opening_matches']
    routes = load('experiments/records/lp2-row-column-routes/results.json')
    words = load('experiments/records/lp2-word-reversal/results.json')
    for name, data in [('lp2-row-column-routes', routes), ('lp2-word-reversal', words)]:
        parent_path = 'experiments/records/' + name + '/plan.json'
        assert data['plan_sha256'] == frozen[parent_path]
        parent_plan = load(parent_path)
        for item in parent_plan.get('inputs', []):
            if item['path'] in frozen:
                assert item['sha256'] == frozen[item['path']]
    route_pages = {p['page']: p for p in routes['pages']}
    word_pages = {p['page']: p for p in words['pages']}
    assert len(plan['pages']) == 55 and set(first_positions) == set(plan['pages'])
    recipes = []
    for recipe_id in plan['recipes']:
        mode = 'word' if recipe_id.startswith('cumulative-word') else 'line'
        source = ('cumulative-autokey-literal' if recipe_id.startswith('cumulative') else
                  'lp2-row-column-routes' if recipe_id.startswith('row') else 'lp2-word-reversal')
        rows = []
        for page_id in plan['pages']:
            raw = (ROOT / ('text/' + page_id + '.txt')).read_bytes().decode('utf-8')
            positions = [(i, lookup[c]) for i, c in enumerate(raw) if c in lookup]
            assert positions
            assert route_pages[page_id]['source_sha256'] == frozen['text/' + page_id + '.txt']
            witness = {'page': page_id}
            if recipe_id.startswith('cumulative'):
                baseline_id = 'ciphertext-lag01-primer00-' + ('word-reset' if mode == 'word' else 'continuous')
                baseline = census[baseline_id]
                assert first_positions[page_id] == positions[0][1]
                # Saved census bounds every page/opening at one matching rune.
                # The first symbol is unchanged by either proposed reset policy.
                mismatch = 0 if positions[0][1] != warning[0] else 1
                if mismatch == 1:
                    assert {'page': page_id, 'opening': 'warning'} in baseline['max_prefix_ties']
                changed = first_changed_reset(raw, lookup, mode)
                changed_at = changed['rune_offset'] if changed else None
                excluded = reset_prefix_compatibility(mismatch, changed_at)
                witness.update({'first_mismatch_zero_based': mismatch,
                    'source_character_offsets': [i for i, _ in positions[:mismatch+1]],
                    'source_input_prefix': [v for _, v in positions[:mismatch+1]],
                    'saved_output_prefix': [first_positions[page_id]],
                    'saved_census_case': baseline_id, 'saved_max_prefix_length': 1,
                    'first_changed_reset': changed, 'excluded': excluded})
            else:
                parent = route_pages[page_id] if recipe_id.startswith('row') else word_pages[page_id]
                selected = [c for c in parent['cases'] if
                    (c.get('axis') == 'row' and c.get('outer_reverse') is False and c.get('inner_reverse') is True and c.get('alternating') is False)
                    or (recipe_id.startswith('word') and c.get('boundary_mode') == 'split-lines')]
                assert len(selected) == 1
                saved = selected[0]
                mismatch = first_mismatch(saved['output_indices'][:24], inverse)
                assert mismatch is not None
                take = mismatch + 1
                if recipe_id.startswith('row'):
                    offsets = [positions[i][0] for i in saved['source_ordinals'][:take]]
                else:
                    offsets = saved['source_character_offsets'][:take]
                assert [lookup[raw[i]] for i in offsets] == saved['output_indices'][:take]
                witness.update({'first_mismatch_zero_based': mismatch,
                    'source_character_offsets': offsets,
                    'source_input_prefix': [lookup[raw[i]] for i in offsets],
                    'saved_output_prefix': saved['output_indices'][:take],
                    'required_preimage_prefix': inverse[:take],
                    'first_changed_reset': None, 'excluded': True})
            assert witness['excluded'], (recipe_id, page_id)
            rows.append(witness)
        recipes.append({'id': recipe_id, 'source_record': source,
                        'proof': 'saved-census-before-reset' if recipe_id.startswith('cumulative') else 'inverse-affine-saved-prefix',
                        'pages': rows, 'closed_pages': len(rows), 'new_target_decodes': 0})
    return {'schema': 'liberpedia-prefix-evidence-gates-v1', 'plan_sha256': sha(raw_plan),
            'controls': passed, 'opening_indices': warning, 'recipes': recipes,
            'recipe_count': len(recipes), 'page_recipe_exclusions': sum(r['closed_pages'] for r in recipes),
            'new_target_decodes': 0, 'scope_limit': plan['scope_limit']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', action='store_true')
    choice.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = build()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
        print('PASS: four fixed-opening exclusions reuse saved evidence; zero new target decodes.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
