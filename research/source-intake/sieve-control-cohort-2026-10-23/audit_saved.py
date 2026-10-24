"""Explicit NEW function-level checks; no original full-source replay claimed."""
import ast, glob, hashlib, json
from pathlib import Path
H = Path(__file__).resolve().parent
S = H.parents[2].parent / 'source-cache/dukotah-cicada3301/liber-primus'

def scoped(path, names, ns):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns

def main():
    out = {'amendment': 'NEW function-level AST isolation of named pure/loader functions; dependencies injected explicitly. No claim of unchanged original full entrypoint replay, survival experiment replay or source closure.'}
    ns = scoped(S/'analysis/round20/P2/nskips_lib.py', ['discrete_tail'], {})
    null = json.loads((S/'analysis/round20/P2/nskips_null.json').read_text())
    cells = []
    for name, tail in null['marginal_null'].items():
        sample = [int(k) for k, count in tail['hist'].items() for _ in range(count)]
        got = ns['discrete_tail'](sample)
        for k in ['n','mean','max','q90','q95','q99','q999']:
            assert got[k] == tail[k], (name,k)
        cells.append({'cell': name,'n':len(sample),'q99':got['q99']})
    out['p2'] = {'marginal_histogram_cells':cells, 'total_saved_wrongkey_counts':sum(c['n'] for c in cells),
                 'plant_function_uses': 'CX.long_plain(L, seed) for every register label; _reg_stream returns None and is not called by plant.',
                 'not_replayed':'Fresh wrong-key or planted beam decodes; existing public-nskips-crossover covers distinct length ladder.'}
    r = json.loads((S/'analysis/round20/R/interaction_b.json').read_text())
    assert r['sC']/r['sT'] == r['screened_fp'] == .025
    assert r['uC']/r['uT'] == r['unscreened_fp'] == 0
    out['redteam'] = {'saved_screened': [r['sC'],r['sT']], 'saved_unscreened':[r['uC'],r['uT']],
                       'saved_ratio_field':r['ratio'], 'ratio_against_text_nominal_1e8':r['screened_fp']/1e-8,
                       'finding':'Raw counts agree with prose 5/200 and 0/200. Saved ratio is 25,000,000 but prose nominal 1e-8 implies 2,500,000; do not quote these as numerically identical.',
                       'not_replayed':'Original screened/unscreened beam populations and full recovery controls.'}
    ns = scoped(S/'analysis/round20/S-RESCOPE/rescope20.py', ['load_survivors'],
                {'json':json,'os':__import__('os'),'B04':str(S/'analysis/round13/B04')})
    rows = ns['load_survivors']()
    stages = {}
    for row in rows: stages[row['_stage']] = stages.get(row['_stage'],0)+1
    assert len(rows) == 250
    rescope = json.loads((S/'analysis/round20/S-RESCOPE/out_rescope.json').read_text())
    proxy = rescope['heldout_proxy_audit']
    assert proxy['realmode_proxy_caught'] + proxy['realmode_proxy_MISSED'] == proxy['n_en_novowel_hallucinations'] == 45
    assert sum(v < .9 for v in proxy['heldout_recoveries_of_hallucinations']) == proxy['realmode_proxy_caught'] == 15
    out['rescope'] = {'loaded_survivors':len(rows),'stages':stages,'saved_proxy_caught':15,'saved_proxy_missed':30,
                       'not_replayed':'487 survivor adjudications, 96 payload reseeds, plants and proxy beam audit. Truthless self-consistency is not measured plaintext recovery.'}
    ns = scoped(S/'analysis/round20/S-MARS/smars_sweep.py', ['held_units'],
                {'json':json,'glob':glob,'os':__import__('os'),'LP':str(S),
                 'L6':str(S/'analysis/round18/L6-offset-marsaglia'),
                 'BUILDERS':['mod29','hi_nibble','lo_nibble','byte_scaled','prime_to_idx','nibbles']})
    held,total,done = ns['held_units']()
    assert (len(held),total,done) == (756,756,0)
    iso = S/'analysis/round18/L6-offset-marsaglia/data/iso'
    out['smars'] = {'local_computed_held':len(held),'grid_total':total,'local_checkpointed':done,'source_reported_held':679,'source_reported_checkpointed':77,'local_iso_exists':iso.exists(),
                     'population_blocker':'77 source checkpoint JSONs are absent locally; original held_units() reconstructs all 756 units, not the source-reported 679. This is missing input, not a changed run result.',
                     'not_replayed':'Physical Marsaglia positive/wrong-key controls and null sweep; no fetch attempted.'}
    (H/'saved-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('PASS: P2 histograms, red-team arithmetic, 250 survivor loader; Marsaglia grid differs because 77 checkpoint inputs are absent')
if __name__ == '__main__': main()
