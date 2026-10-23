"""Replay sentence-relative doublet residues with fixed-boundary controls."""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RANGES = [(0,2),(3,7),(8,14),(15,22),(23,26),(27,32),(33,39),(40,53),(54,55)]
MODULI = range(2,9)


def table(positions, modulus):
    return [sum(p % modulus == r for section in positions for p in section) for r in range(modulus)]


def score(counts, expected):
    return sum((c-e)**2/e for c,e in zip(counts,expected))/(len(counts)-1)


def build():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    ann = json.loads((HERE/'sentence-boundaries.json').read_text(encoding='utf-8'))
    assert [s['name'] for s in ann['sections']] == ['p0-2','p3-7','p8-14','p15-22','p23-26','p27-32','p33-39','p40-53','p54-55']
    index = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    alphabet = {row['rune']:row['index'] for row in index['alphabet']}
    streams=[]; positions=[]; event_ordinals=[]
    for (lo,hi), section in zip(RANGES,ann['sections']):
        stream=[alphabet[r] for page in range(lo,hi+1)
                for r in (ROOT/f'text/lp2-{page:02}.txt').read_text(encoding='utf-8') if r in alphabet]
        assert len(stream)==section['rune_count']
        reset=set(section['reset_at_rune_indices'])
        assert all(0<i<len(stream) for i in reset)
        local=[]; cursor=0
        for i in range(len(stream)):
            if i in reset: cursor=0
            local.append(cursor)
            cursor+=1
        events=[i for i in range(1,len(stream)) if stream[i]==stream[i-1]]
        streams.append(stream); positions.append(local); event_ordinals.append(events)
    assert [len(v) for v in event_ordinals]==[4,6,9,10,11,13,12,18,3]
    observed_local=[[positions[j][i] for i in events] for j,events in enumerate(event_ordinals)]
    expected={}; observed={}
    for m in MODULI:
        e=[sum(len(events)*sum(positions[j][i]%m==r for i in range(1,len(stream)))/(len(stream)-1)
               for j,(stream,events) in enumerate(zip(streams,event_ordinals))) for r in range(m)]
        counts=table(observed_local,m)
        expected[str(m)]=e
        observed[str(m)]={'counts':counts,'chi_over_df':round(score(counts,e),8)}
    best=max(v['chi_over_df'] for v in observed.values())
    rng=random.Random(plan['scan']['seed'])
    maxima=[]
    for _ in range(plan['scan']['trials']):
        sampled=[[positions[j][i] for i in rng.sample(range(1,len(stream)),len(event_ordinals[j]))]
                 for j,stream in enumerate(streams)]
        maxima.append(round(max(score(table(sampled,m),expected[str(m)]) for m in MODULI),8))
    planted=[]
    for j,stream in enumerate(streams):
        candidates=[positions[j][i] for i in range(1,len(stream)) if positions[j][i]%7==0]
        assert len(candidates)>=len(event_ordinals[j])
        planted.append(candidates[:len(event_ordinals[j])])
    planted_score=round(score(table(planted,7),expected['7']),8)
    paths=['data/index.json']+[f'text/lp2-{i:02}.txt' for i in range(56)]
    return {'schema':'liberpedia-doublet-sentence-residues-v1',
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'boundary_sha256':hashlib.sha256((HERE/'sentence-boundaries.json').read_bytes()).hexdigest(),
            'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
            'section_lengths':[len(s) for s in streams],
            'events_per_section':[len(e) for e in event_ordinals],
            'event_ordinals':event_ordinals,
            'observed':observed,
            'expected':{str(m):[round(v,7) for v in expected[str(m)]] for m in MODULI},
            'best_observed':best,'seed':plan['scan']['seed'],'trials':plan['scan']['trials'],
            'control_maxima':maxima,'max_controls_at_least_observed':sum(v>=best for v in maxima),
            'planted_mod7_score':planted_score}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    output=build(); path=HERE/'results.json'
    if args.check: assert output==json.loads(path.read_text(encoding='utf-8'))
    else: path.write_text(json.dumps(output,indent=2)+chr(10),encoding='utf-8')
    print('sentence residues',output['max_controls_at_least_observed'],'/',output['trials'],'controls at least observed; plant',output['planted_mod7_score'])
