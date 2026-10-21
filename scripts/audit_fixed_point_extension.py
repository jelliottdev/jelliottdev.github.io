"""Check GP totals and the explicitly separate LP2-56 fixed-point extension."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from math import isqrt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def prime(n):return n>=2 and all(n%d for d in range(2,isqrt(n)+1))

def audit():
    base_path=ROOT/'exports/reading-fixed-points.json';base=json.loads(base_path.read_bytes())
    for p,h in base['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(ROOT/'scripts/audit_reading_fixed_points.py')==base['auditor_sha256']
    alphabet=json.loads((ROOT/'data/index.json').read_bytes())['alphabet']
    primes=[n for n in range(2,500) if prime(n)]
    assert [a['prime'] for a in alphabet]==primes[:29]
    runes=[a['rune'] for a in alphabet];gp={a['rune']:a['prime'] for a in alphabet}
    groups={}
    for reason in ['ordinary transformation fixed point','recorded interruption']:
        points=[p for p in base['unchanged_positions'] if p['reason']==reason]
        counts=Counter(p['rune'] for p in points);total=sum(gp[c]*n for c,n in counts.items())
        groups[reason]={'positions':len(points),'gp_sum':total,'sum_is_prime':prime(total),
            'by_rune':[{'rune':c,'count':n,'prime':gp[c],'subtotal':gp[c]*n} for c,n in sorted(counts.items())]}
    control=next(c for c in json.loads((ROOT/'data/evidence/reading-methods.json').read_bytes())['controls'] if c['id']=='lp2-56')
    assert control=={'id':'lp2-56','pages':['lp2-56'],'method':'prime-minus-one','key':[],
        'skip':[56],'start':0,'shift':0,'boundary':'reset'}
    source=[c for c in (ROOT/'text/lp2-56.txt').read_text(encoding='utf-8') if c in runes]
    with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8',newline='') as f:trace=list(csv.DictReader(f))
    assert len(source)==len(trace)==85
    key=0;positions=[]
    for i,(rune,row) in enumerate(zip(source,trace)):
        x=runes.index(rune);skip=i==56;before=key
        assert row['page']=='lp2-56' and int(row['page_rune_ordinal'])==int(row['section_rune_ordinal'])==i
        assert row['input_rune']==rune and int(row['input_index'])==x and row['copied']==str(skip)
        if skip:amount=None;y=x;assert row['subtracted_value']==''
        else:
            amount=primes[key]-1;y=(x-amount)%29;key+=1
            assert int(row['subtracted_value'])==amount
        assert int(row['key_position_before'])==before and int(row['key_position_after'])==key
        assert row['key_slot_before']=='' and int(row['output_index'])==y
        if x==y:positions.append({'ordinal':i,'rune':rune,'index':x,'subtracted_value':amount,
            'key_position_before':before,'key_position_after':key,'interruption':skip})
    extra_skips=sum(p['interruption'] for p in positions)
    return {'baseline_report_sha256':sha(base_path),'baseline_gp_groups':groups,
        'extension':{'page':'lp2-56','runes':len(source),'unchanged':len(positions),
            'ordinary_fixed_points':len(positions)-extra_skips,'recorded_interruptions':extra_skips,'positions':positions},
        'combined':{'runes':sum(s['runes'] for s in base['summaries'])+len(source),
            'unchanged':len(base['unchanged_positions'])+len(positions),
            'ordinary_fixed_points':groups['ordinary transformation fixed point']['positions']+len(positions)-extra_skips,
            'recorded_interruptions':groups['recorded interruption']['positions']+extra_skips},
        'source_sha256':{p:sha(ROOT/p) for p in ['data/index.json','data/evidence/reading-methods.json','text/lp2-56.txt','exports/readings/lp2-56.csv']},
        'auditor_sha256':sha(Path(__file__)),
        'limits':'LP2-56 is an explicitly added known control, not part of the original 464-word object. Counts and GP arithmetic do not define a grille, identify intent, or supply a statistical significance test.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Use a new output path')
    report=audit()
    with a.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'combined':report['combined'],'extension':report['extension']},ensure_ascii=True,indent=2))
