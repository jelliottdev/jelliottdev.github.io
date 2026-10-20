"""Independent flat-index sums from the archived page record."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
r=json.loads(Path(__file__).with_name('results.json').read_text())
a=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet'];weights={x['rune']:x['prime'] for x in a}
page=json.loads((ROOT/'data/pages/lp2-32.json').read_text(encoding='utf-8'))
s=[weights[c] for c in page['raw'] if c in weights]
assert len(s)==121 and sum(s)==page['prime_sum']==6045
assert s==[c['prime'] for c in r['cells']]
assert [sum(s[i:i+11]) for i in range(0,121,11)]==r['row_sums']
assert [sum(s[i::11]) for i in range(11)]==r['column_sums']
for window in r['all_5x5_perimeters']:
    start=(window['top_row']-1)*11+window['left_column']-1
    positions=set(range(start,start+5))|set(range(start+44,start+49))|{start+i*11 for i in range(5)}|{start+i*11+4 for i in range(5)}
    assert len(positions)==16
    assert sum(s[i] for i in positions)==window['total']
central={i for i in range(121) if 3<=i//11<=7 and 3<=i%11<=7 and (i//11 in (3,7) or i%11 in (3,7))}
assert central=={c['rune_index'] for c in r['central_perimeter']}
assert sum(s[i] for i in central)==r['central_perimeter_sum']==1136
# Independent check of this archived baseline JPEG's fixed SOF0 header.
b=(ROOT/'images/message-2016.jpg').read_bytes();i=b.index(b'\xff\xc0')
assert b[i+2:i+5]==b'\x00\x11\x08'
assert [int.from_bytes(b[i+7:i+9],'big'),int.from_bytes(b[i+5:i+7],'big')]==r['image_dimensions']==[563,569]
assert len((ROOT/'exports/steganography/message-2016.outguess.bin').read_bytes())==r['payload_bytes']==1136
print('PASS: flat-index perimeter/row/column sums and independent JPEG header check')
