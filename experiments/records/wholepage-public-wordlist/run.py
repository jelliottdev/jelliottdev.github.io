"""Full-page GP29 Vigenere search over the archived 43-key wordlist."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import time
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
PINS = {x['path']: x['sha256'] for x in PLAN['inputs']}
Q = 26 ** 4


def read(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[rel], rel
    return raw


@njit
def score_one(cipher, key, keylen, phase, sign, symbols, sizes, weights):
    state = 0
    chars = 0
    total = 0.0
    for j in range(len(cipher)):
        value = (cipher[j] + sign * key[(j + phase) % keylen]) % 29
        for k in range(sizes[value]):
            state = (state * 26 + symbols[value, k]) % Q
            chars += 1
            if chars >= 4:
                total += weights[state]
    return total / (chars - 3)


@njit
def grid_scores(pages, page_lengths, keys, key_lengths, phases, signs, symbols, sizes, weights):
    grid = np.empty((len(page_lengths), len(phases)), dtype=np.float64)
    for p in range(len(page_lengths)):
        stream = pages[p, :page_lengths[p]]
        for s in range(len(phases)):
            grid[p, s] = score_one(stream, keys[s], key_lengths[s], phases[s], signs[s], symbols, sizes, weights)
    return grid


@njit
def grid_max(pages, page_lengths, keys, key_lengths, phases, signs, symbols, sizes, weights):
    best = -1e300
    for p in range(len(page_lengths)):
        stream = pages[p, :page_lengths[p]]
        for s in range(len(phases)):
            value = score_one(stream, keys[s], key_lengths[s], phases[s], signs[s], symbols, sizes, weights)
            if value > best:
                best = value
    return best


def setup():
    alphabet = json.loads(read(ROOT / 'data/index.json'))['alphabet']
    alphabet_runes = {v['rune']: i for i, v in enumerate(alphabet)}
    latin = [v['latin'] for v in alphabet]
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, label in enumerate(latin):
        sizes[i] = len(label)
        for j, letter in enumerate(label):
            symbols[i, j] = ord(letter) - 65
    lines = read(ROOT / 'experiments/records/english-scorer-controls/english_quadgrams.txt').decode('ascii').splitlines()
    counts = dict((gram, int(count)) for gram, count in (line.split() for line in lines))
    volume = sum(counts.values())
    floor = math.log10(0.01 / volume)
    weights = np.full(Q, floor, dtype=np.float64)
    portable = {}
    for gram, count in counts.items():
        n = 0
        for letter in gram:
            n = n * 26 + ord(letter) - 65
        weights[n] = portable[gram] = math.log10(count / volume)

    def score(values):
        text = ''.join(latin[x] for x in values)
        return sum(portable.get(text[j:j + 4], floor) for j in range(len(text) - 3)) / (len(text) - 3)

    key_rows = json.loads(read(ROOT / 'experiments/records/public-wordlist-vigenere/plan.json'))['keys']
    source_keys = [(row['id'], tuple(alphabet_runes[c] for c in row['runes'])) for row in key_rows]
    settings = [(name, phase, sign, values) for name, values in source_keys
                for phase in range(len(values)) for sign in (-1, 1)]
    assert len(source_keys) == 43 and sum(len(v) for _, v in source_keys) == 309
    assert len(settings) == PLAN['settings_count'] == 618
    key_array = np.zeros((len(settings), max(len(v) for _, _, _, v in settings)), dtype=np.int64)
    key_lengths = np.array([len(v) for _, _, _, v in settings], dtype=np.int64)
    phases = np.array([phase for _, phase, _, _ in settings], dtype=np.int64)
    signs = np.array([sign for _, _, sign, _ in settings], dtype=np.int64)
    for i, (_, _, _, value) in enumerate(settings):
        key_array[i, :len(value)] = value
    return alphabet_runes, settings, key_array, key_lengths, phases, signs, symbols, sizes, weights, score


def controls(settings, keys, lengths, phases, signs, symbols, sizes, weights, portable):
    rows = []
    for i, (name, key_id) in enumerate(zip(PLAN['control_readings'], PLAN['control_key_ids'])):
        raw = read(ROOT / f'exports/readings/{name}.csv').decode('utf-8-sig')
        plain = [int(row['output_index']) for row in csv.DictReader(raw.splitlines())][:PLAN['control_length']]
        assert len(plain) == PLAN['control_length']
        baseline = portable(plain)
        below = 0
        for rep in range(PLAN['control_replicates']):
            mixed = plain.copy()
            random.Random(PLAN['control_seed'] + i * 1000 + rep).shuffle(mixed)
            below += portable(mixed) < baseline
        planted_index = next(j for j, (id_, phase, sign, _) in enumerate(settings)
                             if id_ == key_id and phase == i % len(settings[j][3]) and sign == -1)
        _, phase, sign, key = settings[planted_index]
        cipher = np.array([(p - sign * key[(j + phase) % len(key)]) % 29 for j, p in enumerate(plain)], dtype=np.int64)
        decoded = [(int(c) + sign * key[(j + phase) % len(key)]) % 29 for j, c in enumerate(cipher)]
        assert decoded == plain
        numeric = score_one(cipher, keys[planted_index], lengths[planted_index], phases[planted_index], signs[planted_index], symbols, sizes, weights)
        assert math.isclose(numeric, baseline, abs_tol=1e-11)
        ranked = sorted(((score_one(cipher, keys[j], lengths[j], phases[j], signs[j], symbols, sizes, weights), j)
                         for j in range(len(settings))), key=lambda item: (-item[0], item[1]))
        rank = next(j + 1 for j, (_, index) in enumerate(ranked) if index == planted_index)
        rows.append({'reading': name, 'source_score': baseline, 'shuffles_below': below,
                     'planted_setting': [key_id, phase, sign], 'planted_true_rank': rank})
    originals = sum(r['source_score'] >= PLAN['threshold'] and r['shuffles_below'] >= 198 for r in rows)
    plants = sum(r['planted_true_rank'] == 1 for r in rows)
    return {'rows': rows, 'good_originals': originals, 'top_rank_plants': plants,
            'passed': originals >= 8 and plants >= 8}


def page_arrays(alphabet_runes):
    streams = []
    for page in PLAN['pages']:
        doc = json.loads(read(ROOT / f'data/pages/{page}.json'))
        values = [alphabet_runes[r] for line in doc['lines'] for r in line['raw'] if r in alphabet_runes]
        assert len(values) == doc['rune_count'] and len(values) >= 66
        streams.append(values)
    assert json.loads(read(ROOT / 'data/pages/lp2-50.json'))['rune_count'] == 0
    assert len(streams) == 55
    lengths = np.array([len(v) for v in streams], dtype=np.int64)
    pages = np.zeros((55, int(max(lengths))), dtype=np.int64)
    for i, values in enumerate(streams):
        pages[i, :len(values)] = values
    return streams, pages, lengths


def produce(controls_only=False, benchmark=False):
    lookup, settings, keys, klens, phases, signs, symbols, sizes, weights, portable = setup()
    gate = controls(settings, keys, klens, phases, signs, symbols, sizes, weights, portable)
    if controls_only:
        return gate, None
    if not gate['passed']:
        raise RuntimeError('Predeclared positive-control gate failed; ciphertext search not run')
    streams, pages, lengths = page_arrays(lookup)
    # A single full-grid timing measures the remaining work before the global null.
    start = time.perf_counter()
    grid = grid_scores(pages, lengths, keys, klens, phases, signs, symbols, sizes, weights)
    print(f'Observed grid seconds: {time.perf_counter() - start:.3f}', flush=True)
    if benchmark:
        return gate, None
    for p, s in ((0, 0), (1, 17), (14, 156), (31, 357), (54, 617)):
        _, phase, sign, key = settings[s]
        decoded = [(c + sign * key[(j + phase) % len(key)]) % 29 for j, c in enumerate(streams[p])]
        assert math.isclose(float(grid[p, s]), portable(decoded), abs_tol=1e-11)
    case_lines = []
    best = None
    threshold_passes = 0
    for p, (page, cipher) in enumerate(zip(PLAN['pages'], streams)):
        for s, (key_id, phase, sign, key) in enumerate(settings):
            score = float(grid[p, s])
            plain = bytes((c + sign * key[(j + phase) % len(key)]) % 29 for j, c in enumerate(cipher))
            row = {'page': page, 'key': key_id, 'phase': phase, 'sign': sign,
                   'runes': len(plain), 'score': score, 'indices_sha256': hashlib.sha256(plain).hexdigest()}
            case_lines.append(json.dumps(row, separators=(',', ':')) + '\n')
            threshold_passes += score >= PLAN['threshold']
            if best is None or score > best['score']:
                best = row
    maxima = []
    for rep in range(PLAN['null_replicates']):
        mixed = np.zeros_like(pages)
        for p, values in enumerate(streams):
            arranged = values.copy()
            random.Random(PLAN['null_seed'] + rep * 1000 + p).shuffle(arranged)
            mixed[p, :len(arranged)] = arranged
        maxima.append(float(grid_max(mixed, lengths, keys, klens, phases, signs, symbols, sizes, weights)))
    at_least = sum(v >= best['score'] for v in maxima)
    lines = ''.join(case_lines)
    result = {'schema': 'liberpedia-wholepage-public-wordlist-v1',
              'plan_sha256': hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest(),
              'control_gate': gate, 'page_count': len(streams), 'setting_count': len(settings),
              'case_count': len(case_lines), 'cases_sha256': hashlib.sha256(lines.encode('utf-8')).hexdigest(),
              'best_case': best, 'threshold_passes': threshold_passes,
              'null_maxima': maxima, 'null_at_least_best': at_least,
              'empirical_global_tail': (1 + at_least) / (len(maxima) + 1)}
    return result, lines


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls-only', action='store_true')
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    value, cases = produce(args.controls_only, args.benchmark)
    if args.controls_only:
        print({k: value[k] for k in ('good_originals', 'top_rank_plants', 'passed')})
    elif args.benchmark:
        print('Benchmark complete; no LP2 scores or null maxima saved')
    else:
        (HERE / 'results.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
        (HERE / 'cases.jsonl').write_text(cases, encoding='utf-8', newline='\n')
        print({k: value[k] for k in ('case_count', 'best_case', 'threshold_passes', 'null_at_least_best', 'empirical_global_tail')})
