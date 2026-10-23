"""Replay a pinned shared-running-key diagnostic and calibrate its selected LP2 peak."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX = {r: i for i, r in enumerate(RUNES)}


def load(root, plan):
    root = Path(root)
    sections = {}
    for name in plan['sections']:
        rel = 'pages/' + name + '.txt'
        path = root / rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == plan['section_sha256'][rel], rel
        sections[name] = np.asarray([INDEX[c] for c in path.read_text(encoding='utf-8') if c in INDEX], dtype=np.int16)
    base = root / 'data/baseline-rune-stream.txt'
    assert hashlib.sha256(base.read_bytes()).hexdigest() == plan['baseline_sha256']
    wp = [INDEX[c] for c in base.read_text(encoding='utf-8') if c in INDEX][:plan['synthetic_power']['gp_runes']]
    assert len(wp) == 60000
    return sections, wp


def ioc(values):
    n = len(values)
    counts = np.bincount(values, minlength=29)
    return 29.0 * int(np.sum(counts * (counts - 1))) / (n * (n - 1))


def power(wp, cfg):
    n = cfg['shared_length']; ki = cfg['key_offset']
    key = np.asarray(wp[ki:ki+n], dtype=np.int16)
    a = (np.asarray(wp[:n], dtype=np.int16) + key) % 29
    b = (np.asarray(wp[5000:5000+n], dtype=np.int16) + key) % 29
    true_kappa = float(np.mean(a == b))
    true_diff_ioc = ioc((a - b) % 29)
    rng = random.Random(cfg['random_seed'])
    kappa, diff_ioc = [], []
    null_key = np.asarray(wp[cfg['null_key_offset']:cfg['null_key_offset']+n], dtype=np.int16)
    for _ in range(cfg['null_draws']):
        off = rng.randrange(cfg['null_plain_start_min'], cfg['null_plain_start_max_exclusive'])
        other = (np.asarray(wp[off:off+n], dtype=np.int16) + null_key) % 29
        kappa.append(float(np.mean(a == other)))
        diff_ioc.append(ioc((a - other) % 29))
    return {'true_kappa': true_kappa, 'true_difference_ioc': true_diff_ioc,
            'null_kappa_mean': float(np.mean(kappa)), 'null_kappa_sd': float(np.std(kappa)),
            'null_difference_ioc_mean': float(np.mean(diff_ioc)),
            'null_difference_ioc_sd': float(np.std(diff_ioc)),
            'source_null_draws': len(kappa)}


@njit
def best_pair(a, b, same):
    # Return the maximum source normalized difference IoC over all valid shifts.
    highest = -1e30
    best_shift = 0
    best_n = 0
    for shift in range(-(len(b)-300), len(a)-300):
        if same and shift == 0:
            continue
        if shift >= 0:
            ai = shift; bi = 0
        else:
            ai = 0; bi = -shift
        n = min(len(a)-ai, len(b)-bi)
        if n < 300:
            continue
        counts = np.zeros(29, dtype=np.int64)
        for j in range(n):
            counts[(int(a[ai+j])-int(b[bi+j])) % 29] += 1
        pairs = 0
        for count in counts:
            pairs += count*(count-1)
        val = 29.0*pairs/(n*(n-1))
        z = (val-1.0)*(n-1)/math.sqrt(56.0)
        if z > highest:
            highest = z;best_shift = shift;best_n = n
    return highest,best_shift,best_n


def scan(sections, names):
    rows = []
    for i,name_a in enumerate(names):
        for name_b in names[i:]:
            z,shift,n = best_pair(sections[name_a],sections[name_b],name_a==name_b)
            rows.append({'first':name_a,'second':name_b,'z':float(z),'shift':int(shift),'overlap':int(n)})
    rows.sort(key=lambda r:(-r['z'],r['first'],r['second']))
    return rows


def compute(root,plan):
    sections,wp=load(root,plan)
    names=plan['sections']
    observed=scan(sections,names)
    control=plan['lp2_scan']
    rng=np.random.default_rng(control['selected_control_seed'])
    maxima=[]
    for _ in range(control['selected_control_draws']):
        shuffled={name:rng.permutation(sections[name]) for name in names}
        maxima.append(scan(shuffled,names)[0]['z'])
    top=observed[0]['z']
    return {'schema':'liberpedia-leo-shared-key-differences-results-v1',
            'synthetic_power':power(wp,plan['synthetic_power']),
            'lp2':{'section_lengths':{name:len(sections[name]) for name in names},
                   'pair_count':len(observed),'all_pair_maxima':observed,
                   'global_max':observed[0], 'shuffle_maxima':maxima,
                   'shuffle_exceedances':sum(x>=top for x in maxima),
                   'shuffle_plus_one_tail':(1+sum(x>=top for x in maxima))/(1+len(maxima))}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root',type=Path,required=True)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=compute(args.source_root,plan)
    path=HERE/'results.json'
    if args.check:
        saved=json.loads(path.read_text(encoding='utf-8'))
        assert saved==result
        print('PASS: synthetic control, 45 complete pair/shift scans and 99 shared full-search shuffles')
    else:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'best':result['lp2']['global_max'],'exceedances':result['lp2']['shuffle_exceedances']}))


if __name__=='__main__':
    main()
