"""Post-observation distinct-section calibration; see followup-plan.json."""
import argparse
import json
from pathlib import Path

import numpy as np

import run

HERE = Path(__file__).resolve().parent


def cross_max(sections, names):
    best = None
    for i, a in enumerate(names):
        for b in names[i+1:]:
            z, shift, n = run.best_pair(sections[a], sections[b], False)
            if best is None or z > best['z']:
                best = {'first': a, 'second': b, 'z': float(z),
                        'shift': int(shift), 'overlap': int(n)}
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root', type=Path, required=True)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    follow = json.loads((HERE/'followup-plan.json').read_text(encoding='utf-8'))
    sections, _ = run.load(args.source_root, plan)
    names = plan['sections']
    observed = cross_max(sections, names)
    rng = np.random.default_rng(follow['seed'])
    controls = []
    for _ in range(follow['draws']):
        shuffled = {name: rng.permutation(sections[name]) for name in names}
        controls.append(cross_max(shuffled, names)['z'])
    hits = sum(z >= observed['z'] for z in controls)
    result = {'schema':'liberpedia-leo-shared-key-cross-section-followup-results-v1',
              'post_observation': True, 'pair_count':36, 'observed':observed,
              'shuffle_maxima':controls, 'shuffle_exceedances':hits,
              'exploratory_plus_one_tail':(hits+1)/(len(controls)+1)}
    path = HERE/'followup-results.json'
    if args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
        print('PASS: 36 distinct pairs and 99 shared full-search controls')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
        print(json.dumps({'observed':observed,'exceedances':hits}))


if __name__=='__main__':
    main()
