"""Independent finite-witness audit. Never construct a full target transform."""
import bisect
import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAGES = [f'lp2-{n:02d}' for n in range(56) if n != 50]
RECIPE_IDS = ['cumulative-word-reset-warning', 'cumulative-line-reset-warning',
              'row-reversal-atbash-warning', 'word-reversal-atbash-warning']
WARNING = [24,7,24,4,9,21,17,18,20,10,18,1,18,9,3,2,21,0,4,3,19,2,10,15]


def read(path):
    return json.loads((ROOT / path).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(rows, key):
    assert isinstance(rows,list)
    values = [row[key] for row in rows]
    assert len(values) == len(set(values)), ('Duplicate',key)
    return dict(zip(values,rows))


def indices(values, length):
    assert isinstance(values,list) and len(values) == length
    assert all(type(v) is int and 0 <= v < 29 for v in values)


def check():
    raw_plan = (HERE/'plan.json').read_bytes()
    plan = json.loads(raw_plan)
    report = json.loads((HERE/'results.json').read_bytes())
    assert report['schema'] == 'liberpedia-prefix-evidence-gates-v1'
    assert report['plan_sha256'] == sha(raw_plan)
    assert plan['pages'] == PAGES and plan['opening_length'] == 24 and plan['alphabet_size'] == 29
    assert plan['recipes'] == RECIPE_IDS
    pins = unique(plan['inputs'],'path')
    for path,pin in pins.items():
        assert pin['sha256'] == sha((ROOT/path).read_bytes()), ('Changed source',path)
    identities = unique(plan['recipe_identities'],'id')
    assert set(identities) == set(RECIPE_IDS)
    for recipe_id,identity in identities.items():
        parent = read(identity['path'])
        recipes = unique(parent['browser_followups'],'id')
        recipe = recipes[recipe_id]
        projection = {k:recipe[k] for k in ('id','title','card','inputs','control')}
        encoded = json.dumps(projection,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        assert sha(encoded) == identity['sha256']
        card = recipe['card']
        assert card['scope']['value']['pages'] == PAGES
        assert card['rules']['inputVersion']['value'] == 'raw'
        assert card['rules']['representation']['value'] == 'GP29'
        assert card['rules']['evaluation']['value'] == {'kind':'exact-prefix','values':WARNING}
        expected_operations = {
            'cumulative-word-reset-warning':[{'id':'cumulative_difference','reset':'word'}],
            'cumulative-line-reset-warning':[{'id':'cumulative_difference','reset':'line'}],
            'row-reversal-atbash-warning':[{'id':'reverse_runes','unit':'line'},{'id':'affine','a':28,'b':28}],
            'word-reversal-atbash-warning':[{'id':'reverse_runes','unit':'word'},{'id':'affine','a':28,'b':28}],
        }
        actual_operations = [{k:v for k,v in operation.items() if k != 'label'} for operation in card['method']['value']['operations']]
        assert actual_operations == expected_operations[recipe_id]
        assert recipe['inputs']['alphabet_sha256'] == sha(json.dumps([{k:r[k] for k in ('rune','latin','prime')} for r in read('data/index.json')['alphabet']],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
        inputs = unique(recipe['inputs']['pages'],'id')
        assert set(inputs) == set(PAGES)
        for pid,entry in inputs.items():
            assert entry['text_sha256'] == pins[f'text/{pid}.txt']['sha256']
    alphabet = [r['rune'] for r in read('data/index.json')['alphabet']]
    assert len(alphabet) == len(set(alphabet)) == 29
    lookup = dict(zip(alphabet,range(29)))
    with (ROOT/'exports/readings/warning.csv').open(encoding='utf-8',newline='') as stream:
        warning = [int(r['output_index']) for r in csv.DictReader(stream) if r['output_index'].strip()][:24]
    assert warning == WARNING == report['opening_indices']
    raw = {pid:(ROOT/f'text/{pid}.txt').read_bytes().decode('utf-8') for pid in PAGES}
    positions = {pid:[i for i,c in enumerate(text) if c in lookup] for pid,text in raw.items()}
    assert all(positions.values()) and sum(map(len,positions.values())) == 12956
    for text in raw.values():
        assert not {c for c in text if '\u16a0' <= c <= '\u16ff'} - set(alphabet)
    cumulative = read('experiments/records/cumulative-autokey-literal/results.json')
    first = unique(cumulative['first_positions'],'page')
    assert set(first) == set(PAGES) and cumulative['nonempty_pages'] == 55
    for pid in PAGES:
        assert first[pid]['cipher_index'] == lookup[raw[pid][positions[pid][0]]]
        assert cumulative['input_sha256'][f'text/{pid}.txt'] == pins[f'text/{pid}.txt']['sha256']
    eligible = [pid for pid in PAGES if first[pid]['cipher_index'] == WARNING[0]]
    assert eligible == ['lp2-01','lp2-54']
    manifest = read('experiments/suites/feedback-opening-census/manifest.json')
    census_file = 'experiments/suites/feedback-opening-census/cases.json'
    summary = read('experiments/suites/feedback-opening-census/results.json')
    census = unique(read(census_file)['cases'],'id')
    assert manifest['pages'] == PAGES
    assert manifest['modes'] == ['ciphertext','plaintext'] and manifest['lags'] == list(range(1,17))
    assert manifest['primers'] == list(range(29)) and manifest['boundaries'] == ['continuous','word-reset']
    assert len(census) == summary['case_count'] == 1856
    expected_ids = {f'{mode}-lag{lag:02d}-primer{primer:02d}-{boundary}' for mode,lag,primer,boundary in
                    itertools.product(manifest['modes'],manifest['lags'],manifest['primers'],manifest['boundaries'])}
    assert set(census) == expected_ids
    assert summary['cases_sha256'] == sha((ROOT/census_file).read_bytes())
    assert summary['manifest_sha256'] == sha((ROOT/'experiments/suites/feedback-opening-census/manifest.json').read_bytes())
    assert next(c['indices'] for c in manifest['cribs'] if c['id']=='warning') == WARNING[:12]
    source_inputs = unique(summary['input_sha256'],'path')
    for pid in PAGES:
        path = f'text/{pid}.txt'
        assert source_inputs[path]['sha256'] == pins[path]['sha256']
    for suffix in ('continuous','word-reset'):
        case = census[f'ciphertext-lag01-primer00-{suffix}']
        assert (case['mode'],case['lag'],case['primer'],case['boundary']) == ('ciphertext',1,0,suffix)
        assert case['max_prefix_length'] == 1 and case['opening_matches'] == []
        assert all({'page':pid,'opening':'warning'} in case['max_prefix_ties'] for pid in eligible)
    row_data = read('experiments/records/lp2-row-column-routes/results.json')
    word_data = read('experiments/records/lp2-word-reversal/results.json')
    source_pages = {}
    for name,data in [('lp2-row-column-routes',row_data),('lp2-word-reversal',word_data)]:
        assert data['plan_sha256'] == pins[f'experiments/records/{name}/plan.json']['sha256']
        all_pages = unique(data['pages'],'page')
        assert set(all_pages) == set(PAGES+['lp2-50'])
        assert all_pages['lp2-50']['cases'] == []
        source_pages[name] = all_pages
        assert data['case_count'] == (880 if name=='lp2-row-column-routes' else 110)
        for pid in PAGES:
            count = len(positions[pid])
            rows = all_pages[pid]['cases']
            if name=='lp2-row-column-routes':
                labels = [(r['axis'],r['outer_reverse'],r['inner_reverse'],r['alternating']) for r in rows]
                assert set(labels) == set(itertools.product(('row','column'),(False,True),(False,True),(False,True)))
                assert len(labels) == 16
                assert all_pages[pid]['source_sha256'] == pins[f'text/{pid}.txt']['sha256']
                assert row_data['alphabet'] == alphabet
            else:
                assert len(rows) == 2 and {r['boundary_mode'] for r in rows} == {'split-lines','join-lines'}
                assert all_pages[pid]['rune_count'] == count
            for row in rows:
                indices(row['output_indices'],count)
                assert sorted(row['source_ordinals']) == list(range(count))
                assert all(type(n) is int for n in row['source_ordinals'])
    recipe_rows = unique(report['recipes'],'id')
    assert list(recipe_rows) == RECIPE_IDS and report['recipe_count'] == 4
    for rid,recipe in recipe_rows.items():
        page_rows = unique(recipe['pages'],'page')
        assert list(page_rows) == PAGES
        assert recipe['closed_pages'] == 55 and recipe['new_target_decodes'] == 0
        for pid,row in page_rows.items():
            text = raw[pid]; offsets = positions[pid]
            assert row['excluded'] is True
            mismatch = row['first_mismatch_zero_based']
            assert type(mismatch) is int and 0 <= mismatch < 12
            if rid.startswith('cumulative'):
                word = rid.startswith('cumulative-word')
                case_id = 'ciphertext-lag01-primer00-'+('word-reset' if word else 'continuous')
                assert recipe['source_record'] == 'cumulative-autokey-literal' and recipe['proof'] == 'saved-census-before-reset'
                assert row['saved_census_case'] == case_id and row['saved_max_prefix_length'] == 1
                expected_mismatch = 1 if pid in eligible else 0
                assert mismatch == expected_mismatch
                # Independently verify the at-most-two-symbol witness, never full target output.
                prefix = [lookup[text[i]] for i in offsets[:mismatch+1]]
                observed = [prefix[0]]
                if mismatch:
                    between = text[offsets[0]+1:offsets[1]]
                    observed.append(prefix[1] if word and any(c in '-.' for c in between) else (prefix[1]-prefix[0])%29)
                assert observed[:mismatch] == WARNING[:mismatch] and observed[mismatch] != WARNING[mismatch]
                assert row['source_character_offsets'] == offsets[:mismatch+1]
                assert row['source_input_prefix'] == prefix
                assert row['saved_output_prefix'] == [prefix[0]]
                changed_offsets = [i for i,c in enumerate(text) if i > offsets[0] and c not in lookup and
                                   (c not in '-.' if word else c in '\r\n')]
                changed = None
                if changed_offsets:
                    offset = changed_offsets[0]
                    changed = {'character_offset':offset,'rune_offset':bisect.bisect_left(offsets,offset)}
                assert row['first_changed_reset'] == changed
                assert changed is None or mismatch < changed['rune_offset']
            else:
                row_mode = rid.startswith('row')
                name = 'lp2-row-column-routes' if row_mode else 'lp2-word-reversal'
                assert recipe['source_record'] == name and recipe['proof'] == 'inverse-affine-saved-prefix'
                options = source_pages[name][pid]['cases']
                if row_mode:
                    chosen = [c for c in options if (c.get('axis'),c.get('outer_reverse'),c.get('inner_reverse'),c.get('alternating')) == ('row',False,True,False)]
                else:
                    chosen = [c for c in options if c['boundary_mode']=='split-lines']
                assert len(chosen) == 1
                saved = chosen[0]
                required = [28-v for v in WARNING]
                expected_mismatch = next(i for i in range(24) if saved['output_indices'][i] != required[i])
                assert mismatch == expected_mismatch
                take = mismatch+1
                trace = [offsets[i] for i in saved['source_ordinals'][:take]]
                assert row['source_character_offsets'] == trace
                assert row['source_input_prefix'] == row['saved_output_prefix'] == saved['output_indices'][:take]
                assert row['required_preimage_prefix'] == required[:take]
                assert row['first_changed_reset'] is None
                assert [lookup[text[i]] for i in trace] == saved['output_indices'][:take]
                assert [28-v for v in saved['output_indices'][:mismatch]] == WARNING[:mismatch]
                assert 28-saved['output_indices'][mismatch] != WARNING[mismatch]
    assert report['page_recipe_exclusions'] == 220 and report['new_target_decodes'] == 0
    assert report['scope_limit'] == plan['scope_limit']
    expected_controls = {'inverse_affine_known_answer','truncated_prefix_not_excluded','mismatch_before_reset_excluded',
                         'mismatch_at_reset_not_excluded','mismatch_after_reset_not_excluded','unchanged_prefix_excluded'}
    assert set(report['controls']) == expected_controls and all(v is True for v in report['controls'].values())
    print('PASS: independent pins,55page coverage,4recipes/220finite witnesses, source-array shapes and strictreset reasoning; no full target transformation.')


if __name__ == '__main__':
    check()
