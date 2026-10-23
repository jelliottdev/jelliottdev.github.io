"""Replay the archived keyword-plus-stream grid on verified, current LP2 runes.

The source's archived script is not executed: its old path is broken. This is
an exact-grid reimplementation with a declared whole-search shuffle control.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KEYS = json.loads((HERE / 'keys.json').read_text(encoding='utf-8'))
N_NULL = 49
SEED = 20261023


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primes_through(limit):
    sieve = bytearray(b'\x01') * (limit + 1)
    sieve[:2] = b'\x00\x00'
    for p in range(2, int(limit ** .5) + 1):
        if sieve[p]:
            sieve[p*p:limit+1:p] = b'\x00' * (((limit-p*p)//p)+1)
    return [p for p, good in enumerate(sieve) if good]


def streams(length):
    primes = primes_through(100000)
    names, rows = [], []
    for start in range(50):
        names.append(f'totient_s{start}')
        rows.append([(p-1) % 29 for p in primes[start:start+length]])
        names.append(f'primemod_s{start}')
        rows.append([p % 29 for p in primes[start:start+length]])
    running = 0
    cumulative = []
    for p in primes[:length]:
        running = (running + p - 1) % 29
        cumulative.append(running)
    names.append('cumul_totient'); rows.append(cumulative)
    names.append('linear'); rows.append([i % 29 for i in range(length)])
    fib = [0, 1]
    while len(fib) < length:
        fib.append((fib[-1] + fib[-2]) % 29)
    names.append('fibonacci'); rows.append(fib[:length])
    assert len(names) == len(rows) == 103
    return names, np.array(rows, dtype=np.int16)


def corpus():
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    lookup = {x['rune']: i for i, x in enumerate(alphabet)}
    source = json.loads((HERE / 'source-gp-hashes.json').read_text(encoding='utf-8'))['pages']
    pages, hashes = [], {}
    for p in range(4, 38):
        path = ROOT / f'text/lp2-{p:02d}.txt'
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
        text = path.read_text(encoding='utf-8')
        vals = [lookup[ch] for ch in text if ch in lookup]
        unknown = {ch for ch in text if '\u16a0' <= ch <= '\u16ff' and ch not in lookup}
        assert not unknown, (p, unknown)
        assert vals, p
        seq = ''.join(ch for ch in text if ch in lookup)
        witness = source[f'lp2-{p:02d}']
        assert witness['legacy_page'] == p+17 and witness['runes'] == len(vals)
        assert hashlib.sha256(seq.encode('utf-8')).hexdigest() == witness['source_gp_sha256']
        pages.append((p, np.array(vals, dtype=np.int16)))
    return pages, hashes


def full_key_arrays(max_len):
    names = list(KEYS)
    rows = np.zeros((len(names), max_len), dtype=np.int16)
    for j, name in enumerate(names):
        key = KEYS[name]
        assert key and all(0 <= x < 29 for x in key)
        for i in range(max_len):
            rows[j, i] = key[i % len(key)]
    return names, rows


@njit(cache=False)
def scan_page(cipher, keys, streams_):
    n = len(cipher)
    best = -1.0
    best_row = (-1, -1, -1, -1)
    hits = 0
    for k in range(keys.shape[0]):
        for s in range(streams_.shape[0]):
            for ko in range(2):
                sign_k = -1 if ko == 0 else 1
                for so in range(2):
                    sign_s = -1 if so == 0 else 1
                    counts = np.zeros(29, dtype=np.int32)
                    for i in range(n):
                        x = (cipher[i] + sign_k * keys[k, i] + sign_s * streams_[s, i]) % 29
                        counts[x] += 1
                    pairs = 0
                    for v in range(29):
                        pairs += counts[v] * (counts[v] - 1)
                    score = pairs * 29.0 / (n * (n - 1))
                    if score > 1.4:
                        hits += 1
                    if score > best:
                        best = score
                        best_row = (k, s, ko, so)
    return best, best_row, hits


def scalar_score(cipher, key, stream, ko, so):
    count = [0] * 29
    sk, ss = (-1 if ko == 0 else 1), (-1 if so == 0 else 1)
    for i, c in enumerate(cipher):
        count[(int(c) + sk * int(key[i]) + ss * int(stream[i])) % 29] += 1
    n = len(cipher)
    return 29.0 * sum(f*(f-1) for f in count) / (n*(n-1))


def known_reading_control(key_names, key_rows, stream_names, stream_rows):
    readings = json.loads((ROOT / 'data/evidence/known-readings.json').read_text(encoding='utf-8'))
    reading = next(x for x in readings['controls'] if x['id'] == 'welcome')
    plain = np.array([v for page in reading['decoded_pages'] for v in page['rune_indices']], dtype=np.int16)
    k = key_names.index('CABAL'); s = stream_names.index('totient_s7')
    # For source sub/sub decoding, encryption adds both masks.
    cipher = (plain + key_rows[k, :len(plain)] + stream_rows[s, :len(plain)]) % 29
    recovered = (cipher - key_rows[k, :len(plain)] - stream_rows[s, :len(plain)]) % 29
    assert np.array_equal(recovered, plain)
    score = scalar_score(cipher, key_rows[k], stream_rows[s], 0, 0)
    return {'id': 'welcome', 'runes': len(plain), 'keyword': 'CABAL', 'stream': 'totient_s7',
            'keyword_sign': 'sub', 'stream_sign': 'sub', 'exact_recovery': True,
            'recovered_ioc': score, 'passes_source_screen': score > 1.4}


def execute():
    pages, hashes = corpus()
    longest = max(len(vals) for _, vals in pages)
    key_names, key_rows = full_key_arrays(max(longest, 515))
    stream_names, stream_rows = streams(max(longest, 515))
    control = known_reading_control(key_names, key_rows, stream_names, stream_rows)
    original = []
    for p, cipher in pages:
        score, row, hits = scan_page(cipher, key_rows, stream_rows)
        k, s, ko, so = row
        assert abs(score - scalar_score(cipher, key_rows[k], stream_rows[s], ko, so)) < 1e-12
        original.append({'page': f'lp2-{p:02d}', 'runes': len(cipher), 'best_ioc': score,
                         'best_keyword': key_names[k], 'best_stream': stream_names[s],
                         'best_keyword_sign': ('sub','add')[ko], 'best_stream_sign': ('sub','add')[so],
                         'screen_hits': hits})
    rng = random.Random(SEED)
    null = []
    for trial in range(N_NULL):
        trial_max = -1.0
        trial_hits = 0
        for _, cipher in pages:
            shuffled = list(map(int, cipher))
            rng.shuffle(shuffled)
            best, _, hits = scan_page(np.array(shuffled, dtype=np.int16), key_rows, stream_rows)
            trial_max = max(trial_max, best)
            trial_hits += hits
        null.append({'trial': trial, 'maximum_ioc': trial_max, 'screen_hits': trial_hits})
    best = max(original, key=lambda x: x['best_ioc'])
    total_hits = sum(x['screen_hits'] for x in original)
    result = {
        'schema': 'liberpedia-wulfic-legacy-combined-results-v1',
        'input_sha256': hashes,
        'keys_sha256': sha(HERE/'keys.json'),
        'source_gp_hashes_sha256': sha(HERE/'source-gp-hashes.json'),
        'input_mapping_amendment_sha256': sha(HERE/'input-mapping-amendment.json'),
        'readings_sha256': sha(ROOT/'data/evidence/known-readings.json'),
        'page_count': len(pages), 'source_page_slots': 34,
        'keywords': len(key_names), 'streams': len(stream_names),
        'sign_pairs': 4, 'candidate_count': len(pages)*len(key_names)*len(stream_names)*4,
        'known_reading_control': control,
        'pages': original, 'best': best, 'source_screen_hit_count': total_hits,
        'null_seed': SEED, 'null_trials': N_NULL, 'null': null,
        'global_max_null_ge_observed': sum(x['maximum_ioc'] >= best['best_ioc'] for x in null),
        'hit_count_null_ge_observed': sum(x['screen_hits'] >= total_hits for x in null),
    }
    return result


def main():
    result = execute()
    output = HERE/'results.json'
    if '--check' in sys.argv:
        saved = json.loads(output.read_text(encoding='utf-8'))
        assert result == saved
    else:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('PASS: full source grid, known-reading control and histogram-preserving shuffles')


if __name__ == '__main__':
    main()
