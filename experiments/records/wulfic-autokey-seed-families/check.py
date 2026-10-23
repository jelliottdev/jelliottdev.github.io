"""Independently reconstruct saved winners and the complete-search comparisons."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PHASES = ('named_keywords', 'two_rune_seeds', 'three_rune_seeds', 'distinct_p21_deor')


def scalar_decode(cipher, seed, mode):
    plain = []
    lag = len(seed)
    for position, value in enumerate(cipher):
        key = seed[position] if position < lag else (plain[position-lag] if mode.startswith('pt_') else cipher[position-lag])
        if mode.endswith('_sub'):
            output = (value-key) % 29
        elif mode.endswith('_add'):
            output = (value+key) % 29
        else:
            output = (key-value) % 29
        plain.append(output)
    return plain


def scalar_ioc(values):
    count = Counter(values)
    return 29*sum(n*(n-1) for n in count.values())/(len(values)*(len(values)-1))


def check_case(case, pages, gated=True):
    page = pages[str(case['source_page'])]
    assert page['page'] == case['page']
    plain = scalar_decode(page['runes'], case['seed'], case['mode'])
    assert hashlib.sha256(bytes(plain)).hexdigest() == case['decoded_sha256']
    assert abs(scalar_ioc(plain)-case['ioc']) < 1e-12
    if gated:
        assert all(plain[pos] in (10, 24) for pos in page['singletons'])


def main():
    inputs = json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    results = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest() == results['input_sha256']
    assert hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest() == results['plan_sha256']
    assert inputs['source_commit'] == results['source_commit']
    pages = inputs['pages']
    assert set(pages) == {str(page) for page in range(21,55)}
    for old, row in pages.items():
        assert row['page'] == f'lp2-{int(old)-17:02d}' and len(row['runes']) > 1
        assert all(0 <= rune < 29 for rune in row['runes'])
        assert hashlib.sha256((ROOT/row['site_path']).read_bytes()).hexdigest() == row['site_sha256']
    observed = results['observed']
    assert set(observed) == set(PHASES)
    assert [observed[p]['configurations'] for p in PHASES] == [4488,171564,4536354,60]
    assert [observed[p]['hit_count'] for p in PHASES] == [0,0,0,0]
    assert len(results['null']) == results['null_trials'] == 49
    assert [row['trial'] for row in results['null']] == list(range(49))
    for phase in PHASES:
        record = observed[phase]
        rows = record['pages']
        assert len(rows) == 34
        assert sum(x['configurations'] for x in rows) == record['configurations']
        assert sum(x['gate_count'] for x in rows) == record['gate_count']
        assert sum(x['hit_count'] for x in rows) == record['hit_count']
        for row in rows:
            if row['best']:
                check_case(row['best'], pages, phase != 'distinct_p21_deor')
        if record['best']:
            check_case(record['best'], pages, phase != 'distinct_p21_deor')
            assert record['best']['ioc'] == max(row['best']['ioc'] for row in rows if row['best'])
        else:
            assert record['gate_count'] == 0
        null_rows = [trial['phases'][phase] for trial in results['null']]
        assert sum(item['hit_count'] >= record['hit_count'] for item in null_rows) == results['null_ge'][phase]['hit_count']
        reference = record['best']['ioc'] if record['best'] else -1
        assert sum((item['max_ioc'] if item['max_ioc'] is not None else -1) >= reference for item in null_rows) == results['null_ge'][phase]['max_ioc']
    assert results['source_duplicate_crosswalk'] == {
        'p21_identical_keyword_arrays':17, 'p21_repeated_settings':1020,
        'p21_distinct_four_rune_deor_settings':60, 'comprehensive_deor_3_rune_repeats_in_phase3':186}
    print('PASS: 34 source-mapped pages, scalar winners, branch counts and 49 complete-search controls')


if __name__ == '__main__':
    main()
