"""Trace only the 22 distinct already observed synthetic failures; no target reads."""
import ast, collections, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTROL = ROOT / 'research/source-intake/numeric-skip-controls-2026-10-24'
sys.path.insert(0, str(CONTROL))
import probe

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    _, _, enc, source, streams = probe.load()
    keys = {(br, name): key for br, name, key in streams}
    readings = json.loads((CONTROL / 'known-readings.json').read_text(encoding='utf8'))
    data = json.loads((CONTROL / 'control-results.json').read_text(encoding='utf8'))
    failures = [r for r in data['rows'] if not r['full_exact']]
    assert len(failures) == 44
    for r in [r for r in failures if r['atbash'] == 0]:
        twin = next(x for x in failures if all(x[k] == r[k] for k in ['branch','name','sign','offset','reading']) and x['atbash'] == 1)
        assert all(twin[k] == r[k] for k in ['seed','skips','decoded_sha256','full_score'])
    tree = ast.parse(Path(source.__file__).read_text(encoding='utf8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'beam')
    instrumented = ast.unparse(node).replace('beams = nxt[:beam_w]', 'audit_step(i, nxt, beam_w)\n        beams = nxt[:beam_w]')
    rows = []
    for r in [r for r in failures if r['atbash'] == 0]:
        plain = readings[r['reading']]
        key = keys[r['branch'], r['name']]
        cipher, skips, used = enc.encipher_keyskip(plain, key[r['offset']:], sign=r['sign'], supp=.83, seed=r['seed'])
        assert skips == r['skips'] and max(skips) <= 3 and used[0] == 0
        for i in range(1, len(plain)):
            for j in range(used[i-1]+1, used[i]):
                assert (plain[i]-r['sign']*key[r['offset']+j]) % 29 == cipher[i-1]
        events = []
        def step(i, candidates, width):
            ranks = [j for j, x in enumerate(candidates) if x[3] == tuple(plain[:i+1])]
            events.append((i, min(ranks, default=None), width))
        env = dict(source.__dict__)
        env['audit_step'] = step
        exec(compile(instrumented, '<source-beam-observer>', 'exec'), env)
        pred = env['beam'](probe.np.array(cipher), probe.np.array(key), r['sign'], r['offset'], len(plain), 200 if r['branch'] == 'numeric' else 300)
        assert hashlib.sha256(bytes(pred)).hexdigest() == r['decoded_sha256']
        assert all(rank is not None and rank < width for _, rank, width in events)
        truth = source.Q.score(enc.idx_to_trans(plain))
        chosen = source.Q.score(enc.idx_to_trans(pred))
        assert chosen > truth
        rows.append({k:r[k] for k in ['branch','name','sign','offset','reading']} | {'true_plaintext_survives_every_truncation':True, 'terminal_truth_zero_based_rank':events[-1][1], 'chosen_minus_truth_cumulative_score':chosen-truth, 'chosen_normalized_score':source.Q.score_norm(enc.idx_to_trans(pred)), 'truth_normalized_score':source.Q.score_norm(enc.idx_to_trans(plain)), 'saved_decoded_hash_matches':True})
    receipt = {'schema':'numeric-skip-control-beam-observer-v1','timing':'Retrospective diagnosis of already observed synthetic failures, saved before artifact-stream target plan. No manuscript read by this script.', 'input_sha256':{str((CONTROL/n).relative_to(ROOT)).replace('\\','/'):sha(CONTROL/n) for n in ['probe.py','control-results.json','known-readings.json','plan-frozen.json']}, 'source_beam_sha256':sha(Path(source.__file__)), 'script_sha256':sha(Path(__file__)), 'observed_failure_cells':44,'distinct_transformed_failure_cases':22,'all_true_readings_survive_to_final_beam':True,'terminal_truth_rank_range_zero_based':[min(x['terminal_truth_zero_based_rank'] for x in rows),max(x['terminal_truth_zero_based_rank'] for x in rows)], 'strictly_higher_cumulative_alternatives':44,'ties':0,'normalized_worse_alternative_cells':2*sum(x['chosen_normalized_score'] < x['truth_normalized_score'] for x in rows),'rows':rows,'interpretation':'All failures select a higher cumulative-score alternative despite the exact reading remaining in beam. Ranking is cumulative; final acceptance is normalized. Atbash twins duplicate transformed inputs. These controls do not calibrate a full-search false-positive rate.'}
    (HERE/'beam-observer-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['rows','input_sha256']},indent=2))
if __name__ == '__main__':
    main()
