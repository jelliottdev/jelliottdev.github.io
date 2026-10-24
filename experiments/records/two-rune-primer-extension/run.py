"""Frozen controls, then separately authorized finite target and full-search nulls."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path
import numpy as np
import engine as e

HERE = Path(__file__).resolve().parent


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(value, indent=2) + '\n')


def plan():
    p = json.loads((HERE / 'plan-frozen.json').read_bytes())
    for row in p['files']:
        assert hashlib.sha256((HERE / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
    e.verify_inputs()
    return p


def controls(p):
    model = e.model()
    t0 = time.perf_counter()
    parity = []
    outcomes = []
    for label, plain in e.controls_plaintexts():
        for primer in p['controls']['primers']:
            cipher = e.fb.encipher(plain, e.fb.f_sum, 2, primer, source='pt', sign=-1)
            base = e.zero_decode(np.asarray(cipher, dtype=np.int64))
            scores = e.score_grid(base, *model)
            maximum_difference = 0.0
            exact = True
            for a in range(29):
                for b in range(29):
                    native = e.fb.decode(cipher, e.fb.f_sum, 2, [a,b], source='pt', sign=-1)
                    accelerated = e.shifted_plain(base, a, b).tolist()
                    exact = exact and native == accelerated
                    difference = abs(e.fb.score_norm(native[2:]) - float(scores[a*29+b]))
                    maximum_difference = max(maximum_difference, difference)
            truth_index = primer[0]*29+primer[1]
            truth_score = float(scores[truth_index])
            greater = int(np.sum(scores > truth_score + 1e-12))
            ties = int(np.sum(np.abs(scores-truth_score) <= 1e-12))
            recovered = e.shifted_plain(base, *primer).tolist() == plain
            wrong = np.delete(scores, truth_index)
            outcomes.append({'text':label, 'primer':primer, 'runes':len(plain),
                             'complete_recovery':recovered, 'truth_score':truth_score,
                             'strictly_higher_candidates':greater, 'tied_candidates_including_truth':ties,
                             'best_wrong_score':float(np.max(wrong)),
                             'passes':bool(recovered and greater == 0 and ties == 1 and truth_score >= p['absolute_gate'])})
            parity.append({'text':label,'primer':primer,'pairs':841,'decoded_arrays_exact':exact,
                           'maximum_score_difference':maximum_difference})
            print('Control', label, primer, 'truth', truth_score, 'higher', greater, 'ties', ties, flush=True)
    rng = random.Random(p['benchmark']['seed'])
    synthetic = [rng.randrange(29) for _ in range(p['benchmark']['length'])]
    base = e.zero_decode(np.asarray(synthetic, dtype=np.int64))
    # Warm compilation before repeated steady-state benchmark.
    e.score_grid(base, *model)
    samples = []
    for _ in range(p['benchmark']['repeats']):
        start = time.perf_counter();e.score_grid(base, *model);samples.append(time.perf_counter()-start)
    projection = max(samples) * p['target_runes'] / len(synthetic) * (1+p['null_trials'])
    passed = all(row['passes'] for row in outcomes) and all(row['decoded_arrays_exact'] and row['maximum_score_difference'] <= 1e-12 for row in parity) and projection <= p['benchmark']['max_projected_seconds']
    save('controls.json', {'pass':passed, 'controls':outcomes,'parity':parity,'benchmark_seconds':samples,
                           'projected_target_and_null_seconds':projection,'seconds':time.perf_counter()-t0,
                           'no_target_scoring':True,'plan_sha256':hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest()})
    assert passed, 'Control/parity/benchmark gate failed: no target scan permitted.'


def target(p):
    gate = json.loads((HERE / 'controls.json').read_bytes())
    assert gate['pass'] and gate['no_target_scoring']
    assert gate['plan_sha256'] == hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest()
    model = e.model()
    pages = json.loads((HERE/'pages.json').read_bytes())['pages']
    t0 = time.perf_counter()
    arrays = []
    nulls = []
    digest = hashlib.sha256()
    for trial in range(p['null_trials']+1):
        rng = random.Random(p['null_seed']+trial-1) if trial else None
        matrix = []
        ciphers = []
        for row in pages:
            cipher = list(row['runes'])
            if rng: rng.shuffle(cipher)
            ciphers.append(cipher)
            base = e.zero_decode(np.asarray(cipher,dtype=np.int64))
            matrix.append(e.score_grid(base,*model))
            if not trial:
                for a in range(29):
                    for b in range(29):digest.update(bytes(e.shifted_plain(base,a,b)))
        scores = np.asarray(matrix)
        arrays.append(scores)
        flat = int(np.argmax(scores)); pi, index = divmod(flat,841)
        best = e.witness(ciphers[pi], pages[pi]['page'], index, scores[pi,index])
        if trial: nulls.append({'trial':trial-1,'seed':p['null_seed']+trial-1,'best':best})
        else:
            order = np.argsort(-scores.reshape(-1),kind='stable')[:p['top_witnesses']]
            top = [e.witness(ciphers[int(i)//841], pages[int(i)//841]['page'], int(i)%841, scores.reshape(-1)[i]) for i in order]
            observed = {'best':best,'top':top,'all_decodes_sha256':digest.hexdigest(),
                        'diagonal_best':float(np.max(scores[:,np.arange(29)*30])),
                        'off_diagonal_best':float(np.max(scores[:,[a*29+b for a in range(29) for b in range(29) if a!=b]]))}
        print('Search',trial,'best',best['page'],best['primer'],best['score'],flush=True)
    scores = np.asarray(arrays,dtype='<f8')
    with (HERE/'scores.npy').open('xb') as out:np.save(out,scores,allow_pickle=False)
    largest_null = max(row['best']['score'] for row in nulls)
    hit_bar = max(p['absolute_gate'],largest_null+p['null_margin'])
    hits = np.argwhere(scores[0] >= hit_bar)
    hit_witnesses = [e.witness(pages[int(pi)]['runes'],pages[int(pi)]['page'],int(index),scores[0,pi,index]) for pi,index in hits]
    save('results.json',{'plan_sha256':hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest(),
                         'controls_sha256':hashlib.sha256((HERE/'controls.json').read_bytes()).hexdigest(),
                         'scores_sha256':hashlib.sha256((HERE/'scores.npy').read_bytes()).hexdigest(),
                         'observed':observed,'nulls':nulls,'null_ge_observed':sum(row['best']['score']>=observed['best']['score'] for row in nulls),
                         'hit_bar':hit_bar,'absolute_gate':p['absolute_gate'],'largest_null':largest_null,
                         'gate_hits':hit_witnesses,'pages':len(pages),'runes':sum(len(x['runes']) for x in pages),
                         'target_cases':len(pages)*841,'prior_diagonal_cases':len(pages)*29,'new_off_diagonal_cases':len(pages)*812,
                         'seconds':time.perf_counter()-t0})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['controls','target'])
    args=parser.parse_args();p=plan()
    (controls if args.phase=='controls' else target)(p)
