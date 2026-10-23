"""Independent recurrence and whole-grid verification; `--full` repeats 199 nulls."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

H = Path(__file__).resolve().parent
Q = 29


def connection(values):
    """Independent array-form Berlekamp–Massey implementation."""
    n = len(values)
    active = [1] + [0] * n
    previous = [1] + [0] * n
    complexity = 0
    distance = 1
    old_delta = 1
    for t in range(n):
        delta = (values[t] + sum(active[j] * values[t-j]
                    for j in range(1, complexity+1))) % Q
        if not delta:
            distance += 1
            continue
        original = active[:]
        scale = delta * pow(old_delta, Q-2, Q) % Q
        for j in range(n + 1 - distance):
            active[j + distance] = (active[j + distance] - scale * previous[j]) % Q
        if 2 * complexity <= t:
            complexity = t + 1 - complexity
            previous = original
            old_delta = delta
            distance = 1
        else:
            distance += 1
    return active[:complexity+1], complexity


def extend(initial, polynomial, target_length):
    result = initial[:]
    degree = len(polynomial) - 1
    while len(result) < target_length:
        result.append((-sum(polynomial[j] * result[-j]
                      for j in range(1, degree+1))) % Q)
    return result


def key_for(cipher, plain, mode):
    if mode == 'sub':
        return [(a-b) % Q for a,b in zip(cipher,plain)]
    if mode == 'add':
        return [(b-a) % Q for a,b in zip(cipher,plain)]
    return [(a+b) % Q for a,b in zip(cipher,plain)]


def decrypt(cipher, key, mode):
    if mode == 'sub':
        return [(a-b) % Q for a,b in zip(cipher,key)]
    if mode == 'add':
        return [(a+b) % Q for a,b in zip(cipher,key)]
    return [(b-a) % Q for a,b in zip(cipher,key)]


def corrected_page(cipher, plan, pair_weights, triples):
    examined = good = 0
    best = None
    for name, crib in plan['cribs'].items():
        width = len(crib)
        for mode in plan['modes']:
            for offset in range(len(cipher) - width - 128 + 1):
                examined += 1
                key = key_for(cipher[offset:offset+width], crib, mode)
                train = key[:-2]
                polynomial, degree = connection(train)
                if not 2 <= degree <= min(5, len(train)//2):
                    continue
                predicted = extend(train, polynomial, width+128)
                if predicted[len(train):width] != key[-2:]:
                    continue
                good += 1
                out = decrypt(cipher[offset+width:offset+width+128],
                              predicted[width:width+128], mode)
                val = sum(pair_weights.get((a,b),0) for a,b in zip(out,out[1:]))
                val += 5 * sum((a,b,c) in triples for a,b,c in zip(out,out[1:],out[2:]))
                candidate = {'score': val, 'mode': mode, 'crib': name,
                             'pos': offset, 'order': degree, 'continuation': out}
                if best is None or val > best['score']:
                    best = candidate
    return {'windows': examined, 'verified_recurrences': good, 'best': best}


def source_page(cipher, plan, pair_weights, triples):
    examined = good = 0
    best = None
    for name, crib in plan['source_cribs'].items():
        width = len(crib)
        for mode in plan['modes']:
            for offset in range(len(cipher)-width):
                examined += 1
                key = key_for(cipher[offset:offset+width], crib, mode)
                polynomial, degree = connection(key)
                if not 2 <= degree <= width//2:
                    continue
                phase_zero = extend(key[:degree], polynomial, len(cipher))
                out = decrypt(cipher, phase_zero, mode)
                histogram = [0]*Q
                for value in out:
                    histogram[value] += 1
                ioc = Q*sum(f*(f-1) for f in histogram)/(len(out)*(len(out)-1))
                if ioc <= 1.4:
                    continue
                good += 1
                bg = sum(pair_weights.get((a,b),0) for a,b in zip(out,out[1:]))
                tg = sum((a,b,c) in triples for a,b,c in zip(out,out[1:],out[2:]))
                candidate = {'score': ioc+0.01*bg+0.05*tg, 'ioc': ioc,
                             'bigram': bg, 'trigram': tg, 'crib': name,
                             'mode': mode, 'pos': offset, 'order': degree,
                             'sample_80': out[:80]}
                if best is None or candidate['score'] > best['score']:
                    best = candidate
    return {'tested': examined, 'source_ioc_gate_passes': good, 'best': best}


def check(full=False):
    plan = json.loads((H/'plan.json').read_text(encoding='utf-8'))
    inputs_bytes = (H/'inputs.json').read_bytes()
    assert hashlib.sha256(inputs_bytes).hexdigest() == plan['inputs_sha256']
    inputs = json.loads(inputs_bytes)['rows']
    result = json.loads((H/'results.json').read_text(encoding='utf-8'))
    pairs = {tuple(x['pair']): x['weight'] for x in plan['score']['bigrams']}
    triples = {tuple(x) for x in plan['score']['trigrams']}
    for row in inputs:
        pid = row['page_id']
        assert row['source_indices'] == [x for x in row['site_indices'] if x != 11], pid
        assert source_page(row['source_indices'], plan, pairs, triples) == result['source_original'][pid], pid
        if pid.startswith('lp2-'):
            assert corrected_page(row['site_indices'], plan, pairs, triples) == result['corrected'][pid], pid
    top = [(pid,x['best']) for pid,x in result['corrected'].items() if x['best']]
    assert result['observed_global_best_page'] == max(top,key=lambda a:a[1]['score'])[0]
    rng = random.Random(plan['null']['seed'])
    verified = 0
    for trial in range(plan['null']['trials']):
        trial_best = None
        for row in inputs:
            if row['page_id'].startswith('lp1-'):
                continue
            shuffled = row['site_indices'][:]
            rng.shuffle(shuffled)
            if full or trial < 5 or trial >= plan['null']['trials']-5:
                found = corrected_page(shuffled, plan, pairs, triples)['best']
                if found:
                    trial_best = max(trial_best,found['score']) if trial_best is not None else found['score']
        if full or trial < 5 or trial >= plan['null']['trials']-5:
            assert trial_best == result['shared_null_maxima'][trial], trial
            verified += 1
    print(json.dumps({'source_pages_checked':len(inputs),
                      'corrected_pages_checked':len(inputs)-1,
                      'shared_null_trials_checked':verified,
                      'result':'pass'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true')
    check(parser.parse_args().full)
