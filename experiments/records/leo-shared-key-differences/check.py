"""Independent scalar spot checks of the pinned source inputs and saved maxima."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'


def at_shift(a,b,shift):
    if shift >= 0:
        pairs=zip(a[shift:],b)
    else:
        pairs=zip(a,b[-shift:])
    differences=[(x-y)%29 for x,y in pairs]
    n=len(differences)
    if n<300:
        raise AssertionError((shift,n))
    counts=Counter(differences)
    ioc=29*sum(v*(v-1) for v in counts.values())/(n*(n-1))
    return (ioc-1)*(n-1)/math.sqrt(56),n


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root',type=Path,required=True)
    ap.add_argument('--source-test-root',type=Path,required=True)
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    main_result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    follow=json.loads((HERE/'followup-results.json').read_text(encoding='utf-8'))
    for rel,field in (('tests5.py','source_test_sha256'),('results/tests5.txt','source_receipt_sha256')):
        assert hashlib.sha256((args.source_test_root/rel).read_bytes()).hexdigest()==plan[field]
    receipt=(args.source_test_root/'results/tests5.txt').read_text(encoding='utf-8')
    assert 'p15-22   p33-39   z=3.3 shift=1598 overlap=305' in receipt
    source_lp=args.source_test_root/'lp.py'
    assert hashlib.sha256(source_lp.read_bytes()).hexdigest()=='b516c817679e035a96e1a4014d16ab2b13e8d8dcbdfe98caf20a51568bd070f5'
    assert 'return math.sqrt(2 * (m - 1)) / (n - 1)' in source_lp.read_text(encoding='utf-8')
    names=plan['sections']
    sections={}
    for name in names:
        rel=f'pages/{name}.txt';path=args.source_root/rel
        assert hashlib.sha256(path.read_bytes()).hexdigest()==plan['section_sha256'][rel]
        sections[name]=[RUNES.index(c) for c in path.read_text(encoding='utf-8') if c in RUNES]
        assert len(sections[name])==main_result['lp2']['section_lengths'][name]
    assert len(main_result['lp2']['all_pair_maxima'])==45
    for row in main_result['lp2']['all_pair_maxima']:
        z,n=at_shift(sections[row['first']],sections[row['second']],row['shift'])
        assert n==row['overlap'] and abs(z-row['z'])<1e-10,row
    cross=[r for r in main_result['lp2']['all_pair_maxima'] if r['first']!=r['second']]
    assert len(cross)==36
    assert follow['observed']==max(cross,key=lambda r:r['z'])
    assert follow['shuffle_exceedances']==sum(v>=follow['observed']['z'] for v in follow['shuffle_maxima'])
    assert main_result['lp2']['shuffle_exceedances']==sum(v>=main_result['lp2']['global_max']['z'] for v in main_result['lp2']['shuffle_maxima'])
    assert abs(follow['exploratory_plus_one_tail']-(follow['shuffle_exceedances']+1)/100)<1e-12
    # The source receipt reports ~3.3 for this exact pair/shift, whereas the
    # pinned current source's SD formula gives 5.676... . An approximate
    # 0.75/sqrt(n) formula is numerically consistent with the printed value;
    # this does not establish which historical formula generated the receipt.
    pair=next(x for x in cross if x['first']=='p15-22' and x['second']=='p33-39')
    assert pair['shift']==1598 and pair['overlap']==305
    ioc=1+pair['z']*math.sqrt(56)/(pair['overlap']-1)
    approximate=(ioc-1)/(0.75/math.sqrt(pair['overlap']))
    assert round(approximate,1)==3.3 and round(pair['z'],1)==5.7
    # A planted shared-key cancellation is exact, independent of a language
    # score: subtracting two ciphertext streams removes the common key.
    p=[(7*i+2)%29 for i in range(1200)]
    q=[(11*i+5)%29 for i in range(1200)]
    key=[(13*i*i+3)%29 for i in range(1200)]
    assert [((p[i]+key[i])-(q[i]+key[i]))%29 for i in range(1200)]==[(p[i]-q[i])%29 for i in range(1200)]
    print('PASS: source receipts, 45 independent winning-window counts, 36-pair follow-up and shared-key cancellation')


if __name__=='__main__':
    main()
