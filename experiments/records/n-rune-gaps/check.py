"""Independent gap lengths from splitting the rune stream at each N."""
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
target=next(r['rune'] for r in alphabet if r['latin']=='N')
pattern='['+''.join(r['rune'] for r in alphabet)+']'
inverse={r['prime']:r['latin'] for r in alphabet}
for output in result['outputs']:
    chunks=[];locations=[]
    for page in output['pages']:
        raw=(ROOT/f'text/{page}.txt').read_text(encoding='utf-8')
        matches=list(re.finditer(pattern,raw))
        chunks.append(''.join(m.group() for m in matches))
        locations.extend((page,i+1,m.start()) for i,m in enumerate(matches) if m.group()==target)
    stream=''.join(chunks)
    gaps=[len(s) for s in stream.split(target)[1:-1]]
    if output['distance_mode']=='position-distance':gaps=[n+1 for n in gaps]
    assert gaps==[p['distance'] for p in output['pairs']]
    assert output['tokens']==[inverse.get(n,'.') for n in gaps]
    assert output['n_count']==stream.count(target)
    assert output['rune_count']==len(stream)
    for i,pair in enumerate(output['pairs']):
        for key,expected in [('left',locations[i]),('right',locations[i+1])]:
            x=pair[key];assert (x['page'],x['rune_ordinal'],x['source_character_offset'])==expected
        assert pair['crosses_page']==(pair['left']['page']!=pair['right']['page'])
assert len(result['outputs'])==8
print('PASS: split-based distances, all endpoint locations, boundary flags and labels')
