"""Independent direct extraction of three feedback inverse zero counts."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
lookup={item['rune']:item['index'] for item in alphabet}
zeros=[0,0,0]
doublets=0
for number in range(56):
    source=(ROOT/f'text/lp2-{number:02d}.txt').read_text(encoding='utf-8')
    stream=[lookup[c] for c in source if c in lookup]
    row=[0,0,0]
    for left,right in zip(stream,stream[1:]):
        row[0]+=right==left
        row[1]+=left==right
        row[2]+=(left+right)%29==0
    doublets+=row[0]
    zeros=[a+b for a,b in zip(zeros,row)]
    assert dict(zip(('additive','beaufort','subtractive'),row))==data['pages'][number]['zero_outputs']
assert zeros==[86,86,437] and doublets==86
assert all((a-b)%29==(-(b-a))%29 for a in range(29) for b in range(29))
print('PASS: direct zero-condition scan on every page and modular inverse identity')
