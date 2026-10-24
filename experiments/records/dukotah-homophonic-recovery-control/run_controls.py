"""Private recovered-P6 controls only; never loads manuscript rune streams."""
import ast
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = 'source/corpus/H-branch-recovery/recovered/claude_cicada-3301-scope-cigxzi/liber-primus/analysis/campaign15/P6-homophonic.py'
FUNCTIONS = ['clean_english', 'ngram_index', 'build_model', 'score_labels', 'pick_order',
             'freq_bins', 'english_model', 'sa_solve', 'make_synthetic', 'partc_z']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def load_engine():
    receipt = json.loads((HERE / 'source-receipt.json').read_bytes())
    for entry in receipt['files']:
        assert sha((HERE / entry['path']).read_bytes()) == entry['sha256'], entry['path']
    tree = ast.parse((HERE / SOURCE).read_bytes())
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    assert {node.name for node in definitions} == set(FUNCTIONS)
    scope = {'np': np, 'math': math, 'os': os, 're': re, 'N': 29,
             'REPO': str(HERE / 'source/liber-primus')}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), SOURCE, 'exec'), scope)
    letters = scope['clean_english']()
    substrate = np.frombuffer(letters.encode('ascii', 'ignore'), dtype=np.uint8)
    substrate = substrate[(substrate >= 65) & (substrate <= 90)] - 65
    scope['_eng_letters'] = np.tile(substrate, max(1, 300000 // len(substrate)))
    return scope, letters


def summarize_fit(engine, cipher, truth, psi_true, model, k, order, seed):
    original_score = engine['score_labels']
    best_seen = {'score': -math.inf, 'labels': None}

    def observe(labels, classes, table, width):
        score = original_score(labels, classes, table, width)
        if score > best_seen['score']:
            best_seen.update(score=score, labels=labels.copy())
        return score

    engine['score_labels'] = observe
    start = time.perf_counter()
    score, psi = engine['sa_solve'](cipher, k, model, order, 4000, 4, seed=seed)
    elapsed = time.perf_counter() - start
    engine['score_labels'] = original_score
    decoded = psi[cipher]
    confusion = np.zeros((k, k), dtype=np.int64)
    np.add.at(confusion, (truth, decoded), 1)
    # This is the source's non-bijective row-maximum metric, not exact recovery.
    source_mapping = confusion.argmax(axis=1)
    return {'returned_score': score, 'returned_psi': psi.tolist(),
            'returned_decode_exact': bool(np.array_equal(decoded, truth)),
            'returned_raw_position_accuracy': float(np.mean(decoded == truth)),
            'returned_rune_map_accuracy': float(np.mean(psi == psi_true)),
            'source_rowmax_accuracy': float(np.mean(source_mapping[truth] == decoded)),
            'confusion': confusion.tolist(), 'best_evaluated_score': best_seen['score'],
            'best_evaluated_labels': best_seen['labels'].tolist(), 'seconds': elapsed}


def main():
    plan_bytes = (HERE / 'controls-plan-frozen.json').read_bytes()
    plan = json.loads(plan_bytes)
    assert sha(Path(__file__).read_bytes()) == plan['runner_sha256']
    assert sha((HERE / 'source-receipt.json').read_bytes()) == plan['source_receipt_sha256']
    engine, letters = load_engine()
    start_all = time.perf_counter()
    report = {'plan_sha256': sha(plan_bytes), 'source_sha256': sha((HERE / SOURCE).read_bytes()),
              'numpy_version': np.__version__, 'training_letters': len(letters),
              'training_letters_sha256': sha(letters.encode()),
              'tiled_letters': len(engine['_eng_letters']), 'benchmark': [], 'cases': []}
    benchmark_case = plan['cases'][0]
    cipher, truth, psi_true = engine['make_synthetic'](benchmark_case['k'], plan['length'],
                                                     suppress=benchmark_case['suppress'], seed=benchmark_case['seed'])
    order = engine['pick_order'](benchmark_case['k'])
    model = engine['english_model'](benchmark_case['k'], order)
    for _ in range(2):
        start = time.perf_counter()
        engine['sa_solve'](cipher, benchmark_case['k'], model, order, 128, 1, seed=110)
        report['benchmark'].append(time.perf_counter() - start)
    report['projected_seconds'] = max(report['benchmark']) / 128 * plan['projected_full_length_iterations']
    save('benchmark.json', {key: value for key, value in report.items() if key != 'cases'})
    print('Benchmark projection:', round(report['projected_seconds'], 1), 'seconds', flush=True)
    if report['projected_seconds'] > plan['benchmark_gate_seconds']:
        print('Stopped by frozen benchmark gate; no target is authorized.', flush=True)
        return
    for spec in plan['cases']:
        seed, k = spec['seed'], spec['k']
        engine['rng'] = np.random.default_rng(3301 + seed)
        cipher, truth, psi_true = engine['make_synthetic'](k, plan['length'], suppress=spec['suppress'], seed=seed)
        order = engine['pick_order'](k)
        model = engine['english_model'](k, order)
        score = engine['score_labels']
        fitted = summarize_fit(engine, cipher, truth, psi_true, model, k, order, 99 + seed)
        case = {'spec': spec, 'order': order, 'cipher': cipher.tolist(), 'truth': truth.tolist(),
                'true_psi': psi_true.tolist(), 'observed_symbols': len(set(cipher.tolist())),
                'oracle_score': score(truth, k, model, order), 'fit': fitted}
        shuffled = cipher[engine['rng'].permutation(len(cipher))]
        case['source_one_shuffle_score'], _ = engine['sa_solve'](shuffled, k, model, order, 4000, 2, seed=1234 + seed)
        cut = len(cipher) * 7 // 10
        _, train_psi = engine['sa_solve'](cipher[:cut], k, model, order, 4000, 4, seed=777 + seed)
        held = train_psi[cipher[cut:]]
        held_score = score(held, k, model, order)
        held_null = [score(held[engine['rng'].permutation(len(held))], k, model, order) for _ in range(500)]
        case['heldout'] = {'cut': cut, 'psi': train_psi.tolist(), 'score': held_score,
                           'shuffle_scores': held_null,
                           'z': (held_score - float(np.mean(held_null))) / float(np.std(held_null))}
        partc = engine['partc_z'](cipher, k, model, order, 4000, 4, 24, seed=seed)
        case['source_partc'] = {'score': partc[0], 'psi': partc[1].tolist(), 'z': partc[2],
                               'control_max': partc[3], 'control_mean': partc[4], 'control_sd': partc[5],
                               'strict_z_above_3': bool(partc[2] > 3),
                               'strict_above_control_max': bool(partc[0] > partc[3])}
        matched_rng = np.random.default_rng(6600 + seed)
        case['matched_budget_controls'] = []
        for trial in range(8):
            null_cipher = cipher[matched_rng.permutation(len(cipher))]
            null_score, null_psi = engine['sa_solve'](null_cipher, k, model, order, 4000, 4,
                                                     seed=200000 + seed * 100 + trial)
            case['matched_budget_controls'].append({'trial': trial, 'score': null_score,
                                                   'psi': null_psi.tolist(),
                                                   'cipher_sha256': sha(null_cipher.astype('<i8').tobytes())})
        null_scores = [row['score'] for row in case['matched_budget_controls']]
        case['matched_null_at_or_above_fit'] = sum(value >= fitted['returned_score'] for value in null_scores)
        case['source_heldout_strict_z_above_3'] = bool(case['heldout']['z'] > 3)
        report['cases'].append(case)
        save('case-' + str(seed) + '.json', case)
        print('Case', seed, 'raw accuracy', round(fitted['returned_raw_position_accuracy'], 4),
              'source rowmax', round(fitted['source_rowmax_accuracy'], 4),
              'source PartC z', round(partc[2], 3), 'matched nulls >= fit', case['matched_null_at_or_above_fit'], flush=True)
    report['seconds'] = time.perf_counter() - start_all
    save('controls-results.json', report)
    print('Controls complete:', round(report['seconds'], 1), 'seconds. No manuscript scores computed.', flush=True)


if __name__ == '__main__':
    main()
