"""Independent ordering-key audit and hand-calculated ragged-grid controls."""
import json
from pathlib import Path
from run import route
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
p=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
assert route([[0,1,2],[3,4],[5]],'column',False,False,False)==[0,3,5,1,4,2]
assert route([[0,1,2],[3,4],[5]],'row',False,False,True)==[0,1,2,4,3,5]
lookup={c:i for i,c in enumerate(r['alphabet'])}
count=0
for page in r['pages']:
    positions=[];coordinates={};row_no=0
    for line_no,line in enumerate((ROOT/'text'/(page['page']+'.txt')).read_text(encoding='utf-8').splitlines(),1):
        indices=[lookup[c] for c in line if c in lookup]
        if not indices:continue
        for col,index in enumerate(indices):
            ordinal=len(positions);coordinates[ordinal]=(row_no,col)
            positions.append({'ordinal':ordinal,'line':line_no,'rune_position':col+1,'index':index})
        row_no+=1
    assert positions==page['source_positions']
    if not positions:assert page['cases']==[];continue
    width=max(c for _,c in coordinates.values())+1
    seen=set()
    for case in page['cases']:
        config=(case['axis'],case['outer_reverse'],case['inner_reverse'],case['alternating'])
        assert config not in seen;seen.add(config)
        def order_key(ordinal):
            row,col=coordinates[ordinal]
            outer,inner,size=(row,col,row_no) if case['axis']=='row' else (col,row,width)
            rank=size-1-outer if case['outer_reverse'] else outer
            reverse=case['inner_reverse'] ^ (case['alternating'] and rank%2==1)
            return rank,-inner if reverse else inner
        expected=sorted(coordinates,key=order_key)
        assert expected==case['source_ordinals']
        assert case['output_indices']==[positions[i]['index'] for i in expected]
        assert sorted(expected)==list(range(len(positions)))
        assert case['matching_openings']==[o['id'] for o in p['openings'] if case['output_indices'][:12]==o['indices']]
        count+=1
    assert len(seen)==16
assert count==r['case_count']==880
assert r['matching_case_count']==sum(bool(c['matching_openings']) for page in r['pages'] for c in page['cases'])
print('Hand-calculated controls and all 880 independent ordering-key comparisons pass.')
