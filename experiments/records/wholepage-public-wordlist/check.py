"""Independent case-byte reconstruction and sampled score/null validation."""
import csv
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
PIN = {r['path']: r['sha256'] for r in PLAN['inputs']}


def source(name):
    raw = (ROOT / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN[name]
    return raw


alphabet = json.loads(source('data/index.json'))['alphabet']
rune_to_index = {v['rune']: i for i, v in enumerate(alphabet)}
latin = [v['latin'] for v in alphabet]
model = [line.split() for line in source('experiments/records/english-scorer-controls/english_quadgrams.txt').decode('ascii').splitlines()]
total = sum(int(n) for _, n in model)
floor = math.log10(0.01 / total)
weights = {g: math.log10(int(n) / total) for g, n in model}


def portable_score(indices):
    s = ''.join(latin[v] for v in indices)
    return sum(weights.get(s[i:i + 4], floor) for i in range(len(s) - 3)) / (len(s) - 3)


@njit
def numeric_score(cipher, key, phase, sign, symbol, size, table):
    state, count, total_score = 0, 0, 0.0
    for i in range(len(cipher)):
        value = (cipher[i] + sign * key[(i + phase) % len(key)]) % 29
        for j in range(size[value]):
            state = (state * 26 + symbol[value, j]) % (26 ** 4)
            count += 1
            if count >= 4:
                total_score += table[state]
    return total_score / (count - 3)


def main():
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    raw_cases = (HERE / 'cases.jsonl').read_bytes()
    assert hashlib.sha256(raw_cases).hexdigest() == saved['cases_sha256']
    cases = [json.loads(line) for line in raw_cases.splitlines()]
    assert len(cases) == saved['case_count'] == 33990
    keys = {row['id']: tuple(rune_to_index[r] for r in row['runes'])
            for row in json.loads(source('experiments/records/public-wordlist-vigenere/plan.json'))['keys']}
    streams = {}
    for page in PLAN['pages']:
        data = json.loads(source(f'data/pages/{page}.json'))
        c = tuple(rune_to_index[r] for line in data['lines'] for r in line['raw'] if r in rune_to_index)
        assert len(c) == data['rune_count']
        streams[page] = c
    assert json.loads(source('data/pages/lp2-50.json'))['rune_count'] == 0
    symbol = np.zeros((29, 2), dtype=np.int64)
    size = np.zeros(29, dtype=np.int64)
    for v, letters in enumerate(latin):
        size[v] = len(letters)
        for j, letter in enumerate(letters):
            symbol[v, j] = ord(letter) - 65
    table = np.full(26 ** 4, floor, dtype=np.float64)
    for gram, score in weights.items():
        index = 0
        for c in gram:
            index = index * 26 + ord(c) - 65
        table[index] = score
    setting_labels = [(key_id, phase, sign) for key_id, key in keys.items()
                      for phase in range(len(key)) for sign in (-1, 1)]
    assert len(setting_labels) == saved['setting_count'] == 618
    best = None
    passing = 0
    for index, row in enumerate(cases):
        assert (row['key'], row['phase'], row['sign']) == setting_labels[index % 618]
        assert row['page'] == PLAN['pages'][index // 618]
        key = keys[row['key']]
        cipher = streams[row['page']]
        plain = bytes((c + row['sign'] * key[(j + row['phase']) % len(key)]) % 29
                      for j, c in enumerate(cipher))
        assert row['runes'] == len(plain)
        assert hashlib.sha256(plain).hexdigest() == row['indices_sha256']
        passing += row['score'] >= PLAN['threshold']
        if best is None or row['score'] > best['score']:
            best = row
        if index % 101 == 0:
            assert math.isclose(portable_score(plain), row['score'], abs_tol=1e-11)
    assert best == saved['best_case']
    assert passing == saved['threshold_passes'] == 0
    # Reconstruct separated null replicates with independent parsing and scoring.
    for rep in (0, 99, 198):
        maximum = -math.inf
        for p, page in enumerate(PLAN['pages']):
            cipher = list(streams[page])
            random.Random(PLAN['null_seed'] + rep * 1000 + p).shuffle(cipher)
            values = np.array(cipher, dtype=np.int64)
            for key_id, phase, sign in setting_labels:
                key = np.array(keys[key_id], dtype=np.int64)
                maximum = max(maximum, numeric_score(values, key, phase, sign, symbol, size, table))
        assert math.isclose(maximum, saved['null_maxima'][rep], abs_tol=1e-11)
    assert len(saved['null_maxima']) == 199
    assert saved['null_at_least_best'] == sum(v >= best['score'] for v in saved['null_maxima'])
    assert saved['plan_sha256'] == hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest()
    print('Independent check: all 33,990 output hashes, 337 portable scores, three full-search null maxima')


if __name__ == '__main__':
    main()
