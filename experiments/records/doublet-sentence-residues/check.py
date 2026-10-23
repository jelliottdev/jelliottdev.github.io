"""Independent event recount and optional upstream punctuation-byte verification."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RANGES=[(0,2),(3,7),(8,14),(15,22),(23,26),(27,32),(33,39),(40,53),(54,55)]
PUBLISHED={2:[39,47],3:[26,23,37],4:[21,24,18,23],5:[13,17,16,25,15],
           6:[11,12,17,15,11,20],7:[10,14,16,7,18,8,13],8:[11,12,12,9,10,12,6,14]}


def punctuation_resets(raw):
    runes=set('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ')
    ordinal=0; pending=False; resets=[]
    for char in raw:
        if char in runes:
            if pending and ordinal>0: resets.append(ordinal)
            pending=False; ordinal+=1
        elif char in '⁘⁜⁖':
            pending=True
    return ordinal,resets


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-pages',type=Path,
        help='Optional checkout of relikd/LiberPrayground/pages at the pinned commit')
    args=ap.parse_args()
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    ann=json.loads((HERE/'sentence-boundaries.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'sentence-boundaries.json').read_bytes()).hexdigest()==data['boundary_sha256']
    assert hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()==data['plan_sha256']
    gp=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    alphabet=set(row['rune'] for row in gp['alphabet'])
    assert [s['rune_count'] for s in ann['sections']]==data['section_lengths']
    section_events=[]; local_events=[]; eligible=[]
    for j,((lo,hi),section) in enumerate(zip(RANGES,ann['sections'])):
        symbols=[r for p in range(lo,hi+1) for r in (ROOT/f'text/lp2-{p:02}.txt').read_text(encoding='utf-8') if r in alphabet]
        assert len(symbols)==section['rune_count']
        resets=set(section['reset_at_rune_indices']); assert len(resets)==len(section['reset_at_rune_indices'])
        origin=0; local=[]
        for i in range(len(symbols)):
            if i in resets: origin=i
            local.append(i-origin)
        events=[i for i in range(1,len(symbols)) if symbols[i]==symbols[i-1]]
        assert events==data['event_ordinals'][j]
        section_events.append(events)
        local_events.extend(local[i] for i in events)
        eligible.append([local[i] for i in range(1,len(symbols))])
        if args.source_pages:
            p=args.source_pages/(section['name']+'.txt')
            assert hashlib.sha256(p.read_bytes()).hexdigest()==section['source_text_sha256']
            assert punctuation_resets(p.read_text(encoding='utf-8'))==(len(symbols),section['reset_at_rune_indices'])
    assert sum(len(v) for v in section_events)==86
    for m,source_counts in PUBLISHED.items():
        counted=[sum(p%m==r for p in local_events) for r in range(m)]
        assert counted==source_counts==data['observed'][str(m)]['counts']
        expected=[sum(len(section_events[j])*sum(p%m==r for p in opportunities)/len(opportunities)
                      for j,opportunities in enumerate(eligible)) for r in range(m)]
        assert all(abs(a-b)<1e-7 for a,b in zip(expected,data['expected'][str(m)]))
    assert len(data['control_maxima'])==data['trials']==5000
    assert data['max_controls_at_least_observed']==sum(v>=data['best_observed'] for v in data['control_maxima'])
    assert data['planted_mod7_score']>max(data['control_maxima'])
    print('PASS: independent 86-event recount, seven source vectors, null accounting, planted control'+
          (' and upstream source bytes' if args.source_pages else ''))


if __name__=='__main__':main()
