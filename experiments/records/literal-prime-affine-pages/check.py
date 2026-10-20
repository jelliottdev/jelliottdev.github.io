"""Independent certificate check by direct modulus ranges; no producer import."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
d=json.loads((ROOT/'exports/literal-prime-affine-pages.json').read_bytes())
alphabet=json.loads((ROOT/'data/index.json').read_bytes())['alphabet']
lookup={a['rune']:a['prime'] for a in alphabet}
palette=set(lookup.values())
supports={}
for page in d['pages']:
    raw=(ROOT/f"text/{page['page']}.txt").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==page['sha256']
    # Count each alphabet symbol independently rather than filtering a stream.
    text=raw.decode('utf-8')
    support=sorted(value for rune,value in lookup.items() if text.count(rune)>0)
    assert support==page['support']
    supports[page['page']]=support
assert set(supports)=={f'lp2-{i:02d}' for i in range(56)}
assert d['empty_pages']==[p for p,s in supports.items() if not s]
covered=[]
for case in d['cases']:
    support=case['support']; anchors=set(); survivors=[]; checked=0
    assert case['pages']==[p for p,s in supports.items() if s==support]
    covered+=case['pages']
    for row in case['certificate']:
        u,v,p=row['u'],row['v'],row['witness_input']
        assert u in palette and v in palette and u!=v and p in support
        assert (u,v) not in anchors
        anchors.add((u,v))
        value=u+(p-2)*(v-u)
        assert value==row['unreduced_image'] and value not in palette
        bound=max(abs(value-y) for y in palette)
        moduli=[m for m in range(110,bound+1) if value%m in palette]
        assert moduli==row['candidate_moduli']
        for m in moduli:
            outputs=[(u+(x-2)*(v-u))%m for x in support]
            checked+=1
            if all(y in palette for y in outputs) and len(set(outputs))==len(outputs):
                survivors.append({'a':(v-u)%m,'b':(u-2*(v-u))%m,'m':m,'output':outputs})
    for row in case['integer_maps']:
        a,b=row['a'],row['b'];u,v=2*a+b,3*a+b
        assert (u,v) not in anchors and u!=v
        anchors.add((u,v))
        outputs=[a*p+b for p in support]
        assert outputs==row['output'] and set(outputs)<=palette
    assert anchors=={(u,v) for u in palette for v in palette if u!=v}
    assert survivors==case['survivors'] and checked==case['candidate_maps_tested']
    assert case['integer_maps']==[{'a':1,'b':0,'output':support}]
assert sorted(covered)==sorted(p for p,s in supports.items() if s)
page55=next(c for c in d['cases'] if c['pages']==['lp2-55'])
assert {(r['a'],r['b'],r['m']) for r in page55['survivors']}=={(58,57,114),(102,101,202)}
for r in page55['survivors']:
    assert r['output'][1:]==page55['support'][1:]
    assert r['output'][0] not in page55['support']
print('PASS: 56 page supports, all three complete certificates, and both page-55 exceptions')
