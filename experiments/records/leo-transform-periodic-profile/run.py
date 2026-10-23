"""Source-bound five-transform periodic diagnostic with a selected-peak control.

Requires numpy and numba; source rune text is provided from a pinned relikd checkout.
"""
import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
RI = {r: i for i, r in enumerate(RUNES)}
BREAKS = set('•⁘⁚⁖⁜')
NAMES = ('p0-2', 'p3-7', 'p8-14', 'p15-22', 'p23-26',
         'p27-32', 'p33-39', 'p40-53', 'p54-55')
INV = np.array([0] + [pow(i, -1, 29) for i in range(1, 29)], dtype=np.int64)


def parse(text):
    return np.array([RI[c] for c in text if c in RI], dtype=np.int64)


def transforms(x):
    a, b = x[:-1], x[1:]
    good = (a != 0) & (b != 0)
    return {
        'raw': x,
        'diff1': (b - a) % 29,
        'sum1': (b + a) % 29,
        'diff2': (x[2:] - x[:-2]) % 29,
        'ratio_nonzero': (b[good] * INV[a[good]]) % 29,
    }


@njit
def scores(x, max_period):
    out = np.zeros(max_period, dtype=np.float64)
    n = len(x)
    for period in range(1, max_period + 1):
        counts = np.zeros((period, 29), dtype=np.int64)
        for i in range(n):
            counts[i % period, x[i]] += 1
        total = 0.0
        for col in range(period):
            size = (n - 1 - col) // period + 1
            pairs = 0
            for symbol in range(29):
                v = counts[col, symbol]
                pairs += v * (v - 1)
            total += 29.0 * pairs / (size * (size - 1))
        out[period - 1] = total / period
    return out


def scan(x, cap):
    max_period = min(cap, len(x) // 6)
    v = scores(x, max_period)
    mu = float(np.mean(v))
    sd = float(np.std(v)) + 1e-9
    z = (v - mu) / sd
    order = np.argsort(-v, kind='stable')[:6]
    return {'length': len(x), 'global_ioc': round(ioc(x), 6),
            'periods': max_period,
            'top': [{'period': int(k + 1), 'ioc': round(float(v[k]), 6),
                     'within_profile_z': round(float(z[k]), 4)} for k in order],
            'best_z': round(float(np.max(z)), 6)}


def ioc(x):
    n = len(x)
    c = np.bincount(x, minlength=29)
    return 29 * int(np.sum(c * (c - 1))) / (n * (n - 1)) if n > 1 else 0.0


def kasiski(x):
    positions = defaultdict(list)
    for i in range(len(x) - 3):
        positions[tuple(map(int, x[i:i+4]))].append(i)
    dist = Counter()
    for ps in positions.values():
        for a, b in zip(ps, ps[1:]):
            dist[b-a] += 1
    fac = Counter()
    for d, c in dist.items():
        for f in range(3, 100):
            if d % f == 0:
                fac[f] += c
    return {'repeated_fourgram_pairs': sum(dist.values()),
            'top_factors': [[f, c] for f, c in fac.most_common(6)]}


def word_edge(text):
    xs = []
    word_id = 0
    active = False
    for ch in text:
        if ch in RI:
            xs.append((RI[ch], word_id))
            active = True
        elif ch in BREAKS:
            if active:
                word_id += 1
            active = False
    within = Counter()
    boundary = Counter()
    for (a, wa), (b, wb) in zip(xs, xs[1:]):
        (within if wa == wb else boundary)[(b - a) % 29] += 1
    return {'within_pairs': sum(within.values()), 'within_equal': within[0],
            'boundary_pairs': sum(boundary.values()), 'boundary_equal': boundary[0]}


def best_scan_z(x):
    top = (-math.inf, None, None)
    for name, y in transforms(x).items():
        v = scores(y, min(300, len(y) // 6))
        z = (v - np.mean(v)) / (np.std(v) + 1e-9)
        i = int(np.argmax(z))
        if float(z[i]) > top[0]:
            top = (float(z[i]), name, i + 1)
    return top


def compute(root, plan):
    root = Path(root)
    texts = {}
    for name in NAMES:
        rel = f'pages/{name}.txt'
        path = root / rel
        if hashlib.sha256(path.read_bytes()).hexdigest() != plan['source_sha256'][rel]:
            raise ValueError('source changed: ' + rel)
        texts[name] = path.read_text(encoding='utf-8')
    xs = {name: parse(texts[name]) for name in NAMES}
    rows = {}
    for name, x in xs.items():
        rows[name] = {tname: {**scan(y, 300), **kasiski(y)}
                      for tname, y in transforms(x).items()}
    allx = np.concatenate([xs[name] for name in NAMES])
    corpus = {tname: scan(y, 600) for tname, y in transforms(allx).items()}
    observed = best_scan_z(xs['p27-32'])
    cfg = plan['selection_control']
    rng = random.Random(cfg['seed'])
    base = xs[cfg['section']].tolist()
    null = []
    for _ in range(cfg['shuffles']):
        v = base[:]
        rng.shuffle(v)
        null.append(best_scan_z(np.array(v, dtype=np.int64))[0])
    exceed = sum(v >= observed[0] for v in null)
    # Strong planted 13-cycle, fixed before real-data control result.
    plant_rng = random.Random(1330)
    key = [plant_rng.randrange(29) for _ in range(13)]
    plant = np.array([key[i % 13] if plant_rng.random() >= 0.10
                      else plant_rng.randrange(29) for i in range(len(base))], dtype=np.int64)
    positive = best_scan_z(plant)
    positive_p13_ioc = float(scores(plant, 13)[12])
    return {'schema': 'leo-transform-profile-v1', 'source_revision': plan['source_revision'],
            'source_rune_lengths': {n: len(xs[n]) for n in NAMES},
            'section_profiles': rows, 'concatenated_profiles': corpus,
            'word_edge': {n: word_edge(texts[n]) for n in NAMES},
            'selected_section_control': {
                'section': cfg['section'], 'observed': {'z': round(observed[0], 6),
                    'transform': observed[1], 'period': observed[2]},
                'shuffles': cfg['shuffles'], 'exceedances': exceed,
                'conditional_p': (1 + exceed) / (1 + cfg['shuffles']),
                'nine_section_bonferroni_bound': min(1.0, 9 * (1 + exceed) / (1 + cfg['shuffles'])),
                'null_max_z': [round(v, 6) for v in null],
                'planted_periodic_control': {'z': round(positive[0], 6),
                    'transform': positive[1], 'period': positive[2],
                    'raw_period13_ioc': round(positive_p13_ioc, 6),
                    'null_maxima_at_least_plant': sum(v >= positive[0] for v in null)}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result = compute(args.source_root, plan)
    p = HERE/'results.json'
    if args.check:
        if result != json.loads(p.read_text(encoding='utf-8')):
            raise SystemExit('results differ')
        print('all source vectors and controls match')
    else:
        p.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        print('wrote', p)


if __name__ == '__main__':
    main()
