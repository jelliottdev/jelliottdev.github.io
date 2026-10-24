"""Bounded offline source audit; does not run a manuscript search or rebuild an LM."""
import hashlib, importlib.util, json, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT.parent / 'source-cache/dukotah-cicada3301'
PIN = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')

def main():
    p1 = SOURCE / 'liber-primus/analysis/round20/P1'
    dest = HERE / 'source-p1'
    dest.mkdir(exist_ok=True)
    names = ['build_surface.py', 'survival_surface.json', 'PREREG.md', 'RESULTS.md']
    names += [p.name for p in sorted(p1.glob('pilot_*.json'))]
    manifest = {}
    for name in names:
        shutil.copyfile(p1 / name, dest / name)
        manifest[name] = sha(dest / name)
    save(HERE / 'source-manifest.json', {'revision': PIN, 'files': manifest})
    spec = importlib.util.spec_from_file_location('p1_surface', dest / 'build_surface.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    # main writes under its own HERE. Retain source archival JSON and redirect ONLY output dir,
    # while load_cells remains the exact callable on the copied pilot files.
    cells = mod.load_cells()
    actual = []
    for cell in cells:
        verdict, detail = mod.adjudicate(cell)
        actual.append({**cell, 'verdict': verdict, 'detail': detail})
    best = max(min(c['detail']['CY_survival'], c['detail']['EN_HALFVOWEL_survival'])
               for c in actual if c['detail']['reduction_pass'])
    archived = json.loads((dest / 'survival_surface.json').read_text())
    assert actual == archived['cells']
    assert best == archived['best_min(CY,HALFVOWEL)_at>=100x']
    assert not any(c['verdict'] == 'PASS' for c in actual)
    save(HERE / 'fresh-surface-audit.json', {'source_cells': actual,
         'archived_cells_exact_parity': True, 'best_kill_survival': best,
         'overall': 'INFEASIBLE', 'scope': 'Saved-pilot aggregation only; no plant or pad scan replay.'})
    witness = json.loads((SOURCE / 'liber-primus/analysis/round19/I2/out_build.json').read_text())
    candidates = list((ROOT.parent / 'source-cache/corpus-input-probes-20261023').glob('*mabinogion*.txt'))
    candidates += list((ROOT.parent / 'source-cache').glob('i2-welsh-recovery/*.txt'))
    candidates += list((ROOT.parent / 'source-cache/corpus-input-probes-20261023').glob('welsh*.txt'))
    expected = witness['corpora']['EN_MODERN'][1]
    welsh = witness['corpora']['CY'][0]
    probes = [{'path': str(p.relative_to(ROOT.parent)), 'bytes': p.stat().st_size,
               'sha256': sha(p), 'english_match': sha(p) == expected['sha256'],
               'welsh_match': sha(p) == welsh['sha256']} for p in candidates]
    assert any(p['english_match'] for p in probes)
    assert not any(p['welsh_match'] for p in probes)
    save(HERE / 'corpus-recovery.json', {'english_witness': expected, 'welsh_witness': welsh,
         'candidates': probes, 'conclusion': 'Exact English Mabinogion recovered locally; exact Welsh still absent. No replacement corpus used.'})
    print('PASS: exact saved-pilot adjudication parity; English corpus recovered; Welsh remains blocked')

if __name__ == '__main__': main()
