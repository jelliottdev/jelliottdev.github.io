"""Audit all candidates using a rotating key iterator and known-reading controls."""
import csv
import itertools
import json
from pathlib import Path
from run import decode
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
lookup={c:i for i,c in enumerate(r['alphabet'])}
keys={k['id']:k['indices'] for k in plan['keys']}
for opening in plan['openings']:
    rows=list(csv.DictReader((ROOT/opening['source']).read_text(encoding='utf-8').splitlines()))
    assert opening['indices']==[int(x['output_index']) for x in rows[:12]]
for name,page in [('welcome','lp1-03'),('second-koan','lp1-14')]:
    cipher=[lookup[c] for c in (ROOT/'text'/(page+'.txt')).read_text(encoding='utf-8') if c in lookup][:12]
    expected=next(o['indices'] for o in plan['openings'] if o['id']==name)
    assert decode(cipher,keys[name],0,-1)==expected
streams={p:[lookup[c] for c in (ROOT/'text'/(p+'.txt')).read_text(encoding='utf-8') if c in lookup] for p in plan['pages']}
seen=set()
for c in r['cases']:
    identity=(c['page'],c['key'],c['phase'],c['sign'])
    assert identity not in seen;seen.add(identity)
    key=keys[c['key']];phase=c['phase']
    cycle=itertools.cycle(key[phase:]+key[:phase]);output=[]
    for rune in streams[c['page']]:
        value=rune+c['sign']*next(cycle)
        while value<0:value+=29
        while value>=29:value-=29
        output.append(value)
    assert output==c['output_indices']
    assert c['matching_openings']==[o['id'] for o in plan['openings'] if output[:12]==o['indices']]
assert len(seen)==2352==r['case_count']
assert r['comparison_count']==len(seen)*len(plan['openings'])
assert r['matching_case_count']==sum(bool(c['matching_openings']) for c in r['cases'])
print('Known opening controls, all 2352 candidate streams and all match decisions pass.')
