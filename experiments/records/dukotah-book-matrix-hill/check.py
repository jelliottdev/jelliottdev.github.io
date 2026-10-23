"""Independent reference for the book-matrix replay; imports no producer code."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / "source"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))


def determinant(a):
    if len(a)==1:
        return a[0][0]%29
    return sum(((-1)**j)*a[0][j]*determinant([row[:j]+row[j+1:] for row in a[1:]])
               for j in range(len(a)))%29


def inverse(a):
    n=len(a)
    d=determinant(a)
    if d==0:
        return None
    cof=[[(-1)**(i+j)*determinant([row[:j]+row[j+1:] for r,row in enumerate(a) if r!=i])
          for j in range(n)] for i in range(n)]
    return [[cof[j][i]*pow(d,-1,29)%29 for j in range(n)] for i in range(n)]


def multiplication(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(a)))%29 for j in range(len(a))]
            for i in range(len(a))]


def transform(indices,a):
    n=len(a)
    return [sum(a[r][c]*indices[i+c] for c in range(n))%29
            for i in range(0,len(indices)-n+1,n) for r in range(n)]


def scorer(path):
    rows=[line.split() for line in path.read_text(encoding="ascii").splitlines()]
    total=sum(int(count) for _,count in rows)
    lookup={quad:math.log10(int(count))-math.log10(total) for quad,count in rows}
    floor=math.log10(.01)-math.log10(total)
    def score(text):
        letters=''.join(c for c in text.upper() if 'A'<=c<='Z')
        return sum(lookup.get(letters[i:i+4],floor) for i in range(len(letters)-3))/(len(letters)-3)
    return score


def main():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert sha(HERE/'plan.json')==result['plan_sha256']
    receipt=json.loads((HERE/'initial-control-receipt.json').read_text(encoding='utf-8'))
    assert sha(HERE/'plan-original.json')==receipt['first_frozen_plan_sha256']==plan['amendment']['original_plan_sha256']
    assert len(receipt['original_plants'])==28
    assert all(v['runes']==84 for k,v in receipt['original_plants'].items() if 'M3' in k)
    assert sha(SRC/'analysis/campaign7/hill5_magic.py')==plan['source_sha256']
    assert sha(SRC/'data/krisyotam_runes.txt')==plan['input_hashes']['source_rune_text_sha256']
    gem=assignment(SRC/'src/lp/gematria.py','GEMATRIA')
    assert len(gem)==29 and [x[0] for x in gem]==list(range(29))
    rune_to_index={row[1]:row[0] for row in gem}
    labels=[row[2] for row in gem]
    source_segments=[s for s in (SRC/'data/krisyotam_runes.txt').read_text(encoding='utf-8').split('%')]
    pages=[[rune_to_index[c] for c in s if c in rune_to_index] for s in source_segments]
    pages=[p for p in pages if p]
    assert len(pages)==57
    targets={}
    for i in range(56):
        if i==50: continue
        name=f'lp2-{i:02}'
        site=json.loads((ROOT/'data/pages'/f'{name}.json').read_text(encoding='utf-8'))
        indices=[rune_to_index[c] for c in site['raw'] if c in rune_to_index]
        source_index=i if i<50 else i-1
        assert indices==pages[source_index]
        targets[name]=indices
    targets['joined']=[x for p in pages[:55] for x in p]
    mats=assignment(SRC/'analysis/campaign7/hill5_magic.py','MATRICES')
    mj=json.dumps(mats,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(mj).hexdigest()==plan['matrix_json_sha256']
    printed=json.loads((ROOT/'data/pages/lp2-15.json').read_text(encoding='utf-8'))['numbers']
    assert mats['M3_4x4'][-1][-1]==820 and printed[-1][-1]==1820
    corrected=[r[:] for r in mats['M3_4x4']];corrected[-1][-1]=1820
    mats['M3_image_cell']=corrected
    cases={(x['group'],x['op'],x['target']):x for x in result['cases']}
    assert len(cases)==len(result['cases'])==1568
    with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8',newline='') as f:
        plain=[int(row['output_index']) for row in csv.DictReader(f)]
    score=scorer(SRC/'data/english_quadgrams.txt')
    all_arms={}
    for group,raw in mats.items():
        base=[[v%29 for v in row] for row in raw]
        bt=[list(row) for row in zip(*base)]
        inv=inverse(base)
        assert inv is not None and multiplication(base,inv)==[[int(i==j) for j in range(len(base))] for i in range(len(base))]
        arm={'M':base,'MT':bt,'Minv':inv,'MTinv':inverse(bt)}
        for op,a in arm.items():
            all_arms[(group,op)]=a
        for op,a in arm.items():
            for name,idx in targets.items():
                out=transform(idx,a)
                text=''.join(labels[i] for i in out)
                row=cases[(group,op,name)]
                assert row['preview']==text[:70]
                assert abs(row['score']-round(score(text),9))<1e-9,(group,op,name)
            pad=(-len(plain))%len(a)
            p=plain+[0]*pad
            recovery=transform(transform(p,inverse(a)),a)
            assert recovery==p and recovery[:len(plain)]==plain
            assert recovery[len(plain):]==[0]*pad
            assert score(''.join(labels[i] for i in recovery[:len(plain)]))>-5
            control=result['planted_controls'][group+'.'+op]
            assert control['recovered_runes']==len(plain)
            assert control['zero_padding_removed']==pad
    archived=json.loads((SRC/'analysis/campaign7/hill5_magic_results.json').read_text(encoding='utf-8'))
    best=max((v for v in cases.values() if v['group']!='M3_image_cell'),key=lambda x:x['score'])
    assert round(best['score'],3)==archived['best_score']
    assert best['target']=='lp2-55' and archived['best']['target']=='p54'
    for block in (4,5):
        profile=result['block_coverage'][str(block)]
        assert profile=={'page_runes':sum(map(len,pages[:55])),
                         'page_tail_runes_dropped':sum(len(p)%block for p in pages[:55]),
                         'pages_with_tail':sum(bool(len(p)%block) for p in pages[:55]),
                         'joined_runes':len(targets['joined']),
                         'joined_tail_runes_dropped':len(targets['joined'])%block}
    n=result['conditional_null'];assert n['trials']==199 and len(n['rows'])==199
    assert n['source_max_ge_observed']==sum(x['source_max']>=result['source_best']['score'] for x in n['rows'])
    assert n['corrected_max_ge_observed']==sum(x['corrected_max']>=result['corrected_best']['score'] for x in n['rows'])
    rng=random.Random(3301)
    sample={0,1,49,99,198}
    for trial in range(199):
        shuffled=[p[:] for p in pages[:55]]
        for page in shuffled:rng.shuffle(page)
        if trial not in sample:continue
        candidate=shuffled+[[v for p in shuffled for v in p]]
        high_source=-999.0;high_corrected=-999.0
        for (group,op),matrix in all_arms.items():
            for stream in candidate:
                out=transform(stream,matrix)
                value=round(score(''.join(labels[i] for i in out)),9)
                if group=='M3_image_cell':high_corrected=max(high_corrected,value)
                else:high_source=max(high_source,value)
        assert abs(high_source-n['rows'][trial]['source_max'])<1e-9
        assert abs(high_corrected-n['rows'][trial]['corrected_max'])<1e-9
    print('PASS 1,568 independent matrix/score cases, five selected null trials, source receipt, site pages and known-reading plants')


if __name__=='__main__':main()
