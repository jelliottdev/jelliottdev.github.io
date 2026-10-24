"""Offline function controls for the pinned Round-20 P1 decision, not a pad sweep."""
import argparse, hashlib, importlib.util, itertools, json
from pathlib import Path
H = Path(__file__).resolve().parent
def load():
    manifest = json.loads((H / 'source-manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((H / 'source' / name).read_bytes()).hexdigest() == digest, name
    p = H / 'source/build_surface.py'
    spec = importlib.util.spec_from_file_location('source_surface', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
def main(check=False):
    m = load()
    rows = []
    for size in range(1, 10):
        for regs in itertools.combinations(m.ALL9, size):
            cell = {'survival': {r: {'B': .95, 'median_reduction': 100.0} for r in regs}}
            v, d = m.adjudicate(cell)
            rows.append({'registers': list(regs), 'verdict': v,
                         'claimed_all9_survival_pass': d['all9_survival_pass']})
    controls = []
    for label, bad, reduction in [('complete-pass', None, 100), ('complete-low-CY', 'CY', 100),
                                   ('complete-low-reduction', None, 99)]:
        cell = {'survival': {r: {'B': .89 if r == bad else .95,
                                   'median_reduction': reduction} for r in m.ALL9}}
        v, d = m.adjudicate(cell)
        controls.append({'label': label, 'verdict': v, 'detail': d})
    cells = []
    for c in m.load_cells():
        v, d = m.adjudicate(c); cells.append({**c, 'verdict': v, 'detail': d})
    archived = json.loads((H / 'source/survival_surface.json').read_text())
    assert cells == archived['cells']
    result = {'scope': 'New function-level coverage controls plus saved-pilot adjudication replay. No original survival plants rerun.',
              'subset_rows': rows, 'controls': controls, 'actual_source_cells': cells,
              'source_cell_parity': True, 'incomplete_subsets_marked_PASS': sum(
                  len(r['registers']) < 9 and r['verdict'] == 'PASS' for r in rows),
              'actual_overall': archived['OVERALL_VERDICT'],
              'actual_best_kill_survival': archived['best_min(CY,HALFVOWEL)_at>=100x']}
    if check:
        assert json.loads((H / 'results.json').read_text()) == result
    else:
        (H / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f"PASS: {result['incomplete_subsets_marked_PASS']} incomplete subsets accepted; actual saved-pilot verdict unchanged")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
