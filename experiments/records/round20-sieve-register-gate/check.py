"""Independent coverage/specification check; uses no source decision callable."""
import hashlib, json
from pathlib import Path
H = Path(__file__).resolve().parent
ALL9 = {'EN_MODERN','EN_KJV','LP1_REAL','LATIN','OE','DE','CY','EN_HALFVOWEL','EN_NOVOWEL'}
def main():
    man = json.loads((H / 'source-manifest.json').read_text())
    for name, digest in man['files'].items():
        assert hashlib.sha256((H / 'source' / name).read_bytes()).hexdigest() == digest, name
    d = json.loads((H / 'results.json').read_text())
    rows = d['subset_rows']
    assert len(rows) == 2**9 - 1
    subsets = {frozenset(r['registers']) for r in rows}
    assert len(subsets) == len(rows) and all(s <= ALL9 and s for s in subsets)
    # Independent specification: PASS requires measurements for every named register.
    incomplete = [r for r in rows if set(r['registers']) != ALL9]
    assert len(incomplete) == 510 and all(r['verdict'] == 'PASS' for r in incomplete)
    assert all(r['claimed_all9_survival_pass'] for r in rows)
    assert [r['verdict'] for r in d['controls']] == ['PASS','PARTIAL(gate-registers-only)','SHORTFALL']
    raw = json.loads((H / 'source/survival_surface.json').read_text())
    assert d['actual_source_cells'] == raw['cells']
    assert len(raw['cells']) == 4 and raw['OVERALL_VERDICT'] == 'INFEASIBLE'
    # Independently derive the source decision from reported pilot summaries.
    best = 0
    for c in d['actual_source_cells']:
        present = ALL9 & set(c['survival'])
        assert {'CY','EN_HALFVOWEL'} <= present
        if min(c['survival'][r]['median_reduction'] for r in present) >= 100:
            best = max(best, min(c['survival'][r]['B'] for r in ['CY','EN_HALFVOWEL']))
        assert any(c['survival'][r]['B'] < .9 for r in present)
    assert best == d['actual_best_kill_survival'] == 2/3
    assert d['incomplete_subsets_marked_PASS'] == 510
    print('PASS: source hashes, 511 unique subsets, 510 missing-coverage false passes, three comparison controls, four archived cells')
if __name__ == '__main__': main()
